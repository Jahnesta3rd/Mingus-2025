#!/usr/bin/env python3
"""90-day expense audit with tier-based cut recommendations."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func

from backend.models.database import db
from backend.models.expense_audit_snapshot import ExpenseAuditSnapshot
from backend.models.financial_setup import RecurringExpense
from backend.models.independence_cost_assessment import IndependenceCostAssessment
from backend.models.quick_spend import QuickSpendEntry
from backend.models.transaction import Transaction

AUDIT_CATEGORIES = (
    "Groceries",
    "Dining",
    "Subscriptions",
    "Transport",
    "Entertainment",
    "Shopping",
    "Other",
)

_CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Groceries", ("grocery", "groceries", "supermarket", "whole foods", "trader", "costco", "walmart", "kroger")),
    ("Dining", ("restaurant", "dining", "coffee", "cafe", "doordash", "uber eats", "grubhub", "starbucks", "mcdonald")),
    ("Subscriptions", ("subscription", "netflix", "spotify", "hulu", "disney", "apple.com/bill", "amazon prime", "gym")),
    ("Transport", ("uber", "lyft", "gas", "fuel", "parking", "transit", "metro", "shell", "chevron")),
    ("Entertainment", ("entertainment", "movie", "concert", "game", "steam", "ticket", "bar", "brewery")),
    ("Shopping", ("amazon", "target", "shopping", "retail", "clothing", "apparel", "best buy")),
]

_REPLACEMENT_ACTIVITIES: dict[str, list[str]] = {
    "Dining": [
        "Meal prep Sundays with pantry staples",
        "Host potluck dinners instead of restaurants",
        "Library + free community events for social time",
    ],
    "Entertainment": [
        "Free museum days and local park events",
        "Streaming rotation (one service at a time)",
        "Hiking or walking meetups",
    ],
    "Subscriptions": [
        "Rotate streaming — cancel after finishing a series",
        "Use library apps (Libby, Hoopla) for books/audio",
        "Free workout videos instead of gym apps",
    ],
    "Shopping": [
        "30-day wishlist rule before non-essentials",
        "Buy-nothing groups and clothing swaps",
        "Thrift / resale for wardrobe refresh",
    ],
}

_TIER_MONTHLY_SAVINGS = {"A": 120.0, "B": 250.0, "C": 150.0}


def _round2(value: float) -> float:
    return round(float(value), 2)


def _normalize_text(*parts: str | None) -> str:
    return " ".join(p.strip().lower() for p in parts if p).strip()


def _categorize_transaction(
    *,
    merchant: str | None,
    category: str | None,
    subcategory: str | None,
) -> str:
    haystack = _normalize_text(merchant, category, subcategory)
    for label, keywords in _CATEGORY_RULES:
        if any(keyword in haystack for keyword in keywords):
            return label
    if category:
        cat = category.strip().lower()
        if "food" in cat or "grocery" in cat:
            return "Groceries"
        if "restaurant" in cat or "dining" in cat:
            return "Dining"
        if "subscription" in cat or "service" in cat:
            return "Subscriptions"
        if "travel" in cat or "transport" in cat:
            return "Transport"
        if "entertainment" in cat or "recreation" in cat:
            return "Entertainment"
        if "shop" in cat:
            return "Shopping"
    return "Other"


def _merchant_group_to_category(group: str | None) -> str:
    mapping = {
        "groceries": "Groceries",
        "dining": "Dining",
        "subscriptions": "Subscriptions",
        "transport": "Transport",
        "entertainment": "Entertainment",
        "shopping": "Shopping",
    }
    key = (group or "").strip().lower()
    return mapping.get(key, "Other")


class ExpenseAuditAnalyzer:
    """Analyze spending and produce ICC-ready tier cut recommendations."""

    def _fetch_transactions(self, user_id: int, start_date: date) -> list[dict[str, Any]]:
        rows = (
            Transaction.query.filter(
                Transaction.user_id == user_id,
                Transaction.date >= start_date,
                Transaction.is_debit.is_(True),
                Transaction.pending.is_(False),
            )
            .order_by(Transaction.date.desc())
            .all()
        )
        return [
            {
                "amount": abs(float(row.amount or 0)),
                "category": _categorize_transaction(
                    merchant=row.merchant,
                    category=row.category,
                    subcategory=row.subcategory,
                ),
                "merchant": row.merchant or "Unknown",
                "source": "plaid",
            }
            for row in rows
            if abs(float(row.amount or 0)) > 0
        ]

    def _fetch_quick_spend(self, user_id: int, start_date: date) -> list[dict[str, Any]]:
        rows = (
            QuickSpendEntry.query.filter(
                QuickSpendEntry.user_id == user_id,
                QuickSpendEntry.date >= start_date,
            )
            .all()
        )
        return [
            {
                "amount": abs(float(row.amount or 0)),
                "category": _merchant_group_to_category(row.merchant_group),
                "merchant": row.merchant_name or row.merchant_group or "Quick spend",
                "source": "quick_spend",
            }
            for row in rows
            if abs(float(row.amount or 0)) > 0
        ]

    def _fetch_recurring_subscriptions(self, user_id: int) -> list[dict[str, Any]]:
        rows = RecurringExpense.query.filter(
            RecurringExpense.user_id == user_id,
            RecurringExpense.is_active.is_(True),
        ).all()
        items: list[dict[str, Any]] = []
        for row in rows:
            category = (row.category or "").strip().lower()
            if category not in {"subscription", "subscriptions", "entertainment", "other"}:
                continue
            items.append(
                {
                    "amount": abs(float(row.amount or 0)),
                    "category": "Subscriptions",
                    "merchant": row.name or "Recurring subscription",
                    "source": "recurring",
                }
            )
        return items

    def _aggregate_by_category(
        self,
        entries: list[dict[str, Any]],
        *,
        days_lookback: int,
    ) -> dict[str, float]:
        totals: dict[str, float] = {cat: 0.0 for cat in AUDIT_CATEGORIES}
        for entry in entries:
            cat = entry.get("category") or "Other"
            if cat not in totals:
                cat = "Other"
            totals[cat] += float(entry.get("amount") or 0)

        months = max(days_lookback / 30.0, 1.0)
        return {cat: _round2(amount / months) for cat, amount in totals.items()}

    def _identify_leaks(
        self,
        entries: list[dict[str, Any]],
        monthly_by_category: dict[str, float],
    ) -> list[dict[str, Any]]:
        leaks: list[dict[str, Any]] = []
        subscription_merchants: dict[str, float] = defaultdict(float)
        dining_merchants: dict[str, float] = defaultdict(float)

        for entry in entries:
            merchant = str(entry.get("merchant") or "Unknown")
            amount = float(entry.get("amount") or 0)
            if entry.get("category") == "Subscriptions":
                subscription_merchants[merchant] += amount
            if entry.get("category") == "Dining":
                dining_merchants[merchant] += amount

        for merchant, total in sorted(subscription_merchants.items(), key=lambda x: -x[1])[:5]:
            leaks.append(
                {
                    "type": "forgotten_subscription",
                    "merchant": merchant,
                    "monthly_est": _round2(total / 3),
                    "note": "Recurring charge detected — confirm you still use this",
                }
            )

        if monthly_by_category.get("Dining", 0) >= 200:
            top_dining = max(dining_merchants.items(), key=lambda x: x[1], default=None)
            if top_dining:
                leaks.append(
                    {
                        "type": "daily_habit",
                        "merchant": top_dining[0],
                        "monthly_est": _round2(top_dining[1] / 3),
                        "note": "Frequent dining spend — small daily purchases add up",
                    }
                )

        if monthly_by_category.get("Shopping", 0) >= 150:
            leaks.append(
                {
                    "type": "impulse_spending",
                    "category": "Shopping",
                    "monthly_est": monthly_by_category["Shopping"],
                    "note": "Discretionary shopping is elevated vs. other categories",
                }
            )

        return leaks

    def _build_tier_recommendations(
        self,
        monthly_by_category: dict[str, float],
        leaks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        dining = monthly_by_category.get("Dining", 0)
        subscriptions = monthly_by_category.get("Subscriptions", 0)
        entertainment = monthly_by_category.get("Entertainment", 0)
        shopping = monthly_by_category.get("Shopping", 0)

        tier_a_cuts = [
            {
                "label": "Cancel unused subscriptions",
                "monthly_savings": _round2(min(60, subscriptions * 0.5)),
                "example": "Netflix / unused apps",
            },
            {
                "label": "Reduce dining out 2x/week",
                "monthly_savings": _round2(min(60, dining * 0.2)),
                "example": "Coffee + lunch swaps",
            },
        ]
        tier_b_cuts = [
            {
                "label": "Meal plan + grocery focus",
                "monthly_savings": _round2(min(90, dining * 0.35)),
                "example": "Batch cook 4 dinners/week",
            },
            {
                "label": "Cut entertainment subscriptions/events",
                "monthly_savings": _round2(min(80, entertainment * 0.4)),
                "example": "One streaming service + free events",
            },
            {
                "label": "Shopping pause (non-essentials)",
                "monthly_savings": _round2(min(80, shopping * 0.3)),
                "example": "30-day wishlist rule",
            },
        ]
        tier_c_cuts = [
            {
                "label": "Restrictive dining + transport cap",
                "monthly_savings": _round2(min(75, (dining + monthly_by_category.get("Transport", 0)) * 0.25)),
                "example": "Essential trips only",
            },
            {
                "label": "Minimal discretionary budget",
                "monthly_savings": _round2(min(75, (entertainment + shopping) * 0.5)),
                "example": "High burnout risk — review monthly",
            },
        ]

        if leaks:
            first_sub = next((l for l in leaks if l["type"] == "forgotten_subscription"), None)
            if first_sub and tier_a_cuts:
                tier_a_cuts[0]["example"] = f"Cancel {first_sub['merchant']} (~${first_sub['monthly_est']}/mo)"

        return {
            "A": {
                "monthly_savings": _TIER_MONTHLY_SAVINGS["A"],
                "difficulty": "easy",
                "sustainability": "green",
                "cuts": tier_a_cuts,
                "summary": "Low-friction cuts: subscriptions + dining tweaks",
            },
            "B": {
                "monthly_savings": _TIER_MONTHLY_SAVINGS["B"],
                "difficulty": "medium",
                "sustainability": "yellow",
                "cuts": tier_b_cuts,
                "summary": "Meal planning, less entertainment, mindful shopping",
            },
            "C": {
                "monthly_savings": _TIER_MONTHLY_SAVINGS["C"],
                "difficulty": "hard",
                "sustainability": "red",
                "cuts": tier_c_cuts,
                "summary": "Restrictive plan — monitor burnout risk",
            },
        }

    def _combined_savings(self) -> dict[str, float]:
        a = _TIER_MONTHLY_SAVINGS["A"]
        b = _TIER_MONTHLY_SAVINGS["B"]
        c = _TIER_MONTHLY_SAVINGS["C"]
        return {
            "A": a,
            "B": b,
            "C": c,
            "A+B": _round2(a + b),
            "A+B+C": _round2(a + b + c),
        }

    def analyze_expenses(self, user_id: int, days_lookback: int = 90) -> dict[str, Any]:
        if days_lookback <= 0:
            raise ValueError("days_lookback must be positive")

        start_date = date.today() - timedelta(days=days_lookback)
        plaid_entries = self._fetch_transactions(user_id, start_date)
        quick_entries = self._fetch_quick_spend(user_id, start_date)
        recurring_entries = self._fetch_recurring_subscriptions(user_id)
        all_entries = plaid_entries + quick_entries + recurring_entries

        monthly_by_category = self._aggregate_by_category(
            all_entries,
            days_lookback=days_lookback,
        )
        total_monthly = _round2(sum(monthly_by_category.values()))
        leaks = self._identify_leaks(all_entries, monthly_by_category)
        tier_recommendations = self._build_tier_recommendations(monthly_by_category, leaks)
        combined_savings = self._combined_savings()

        replacement_activities = [
            {"category": cat, "ideas": ideas}
            for cat, ideas in _REPLACEMENT_ACTIVITIES.items()
            if monthly_by_category.get(cat, 0) > 50
        ]

        snapshot = ExpenseAuditSnapshot(
            user_id=user_id,
            days_lookback=days_lookback,
            total_monthly_spending=total_monthly,
            spending_by_category=monthly_by_category,
            tier_recommendations=tier_recommendations,
            combined_savings=combined_savings,
            replacement_activities=replacement_activities,
        )
        db.session.add(snapshot)
        db.session.commit()

        return {
            "snapshot_id": str(snapshot.id),
            "days_lookback": days_lookback,
            "spending_by_category": monthly_by_category,
            "total_monthly": total_monthly,
            "spending_leaks": leaks,
            "tier_recommendations": tier_recommendations,
            "combined_savings": combined_savings,
            "replacement_activities": replacement_activities,
            "data_sources": {
                "plaid_transactions": len(plaid_entries),
                "quick_spend_entries": len(quick_entries),
                "recurring_subscriptions": len(recurring_entries),
            },
        }

    def apply_tiers_to_icc(
        self,
        *,
        user_id: int,
        icc_assessment_id: UUID,
        selected_tiers: list[str],
        snapshot_id: UUID | None = None,
    ) -> dict[str, Any]:
        normalized = [t.strip().upper() for t in selected_tiers if str(t).strip()]
        valid = {"A", "B", "C"}
        if not normalized or any(t not in valid for t in normalized):
            raise ValueError("selected_tiers must contain A, B, and/or C")

        if snapshot_id is not None:
            snapshot = ExpenseAuditSnapshot.query.filter_by(
                id=snapshot_id,
                user_id=user_id,
            ).first()
        else:
            snapshot = (
                ExpenseAuditSnapshot.query.filter_by(user_id=user_id)
                .order_by(ExpenseAuditSnapshot.created_at.desc())
                .first()
            )
        if snapshot is None:
            raise LookupError("No expense audit snapshot found")

        combined = snapshot.combined_savings or {}
        if "A" in normalized and "B" in normalized and "C" in normalized:
            tier_key = "A+B+C"
        elif "A" in normalized and "B" in normalized:
            tier_key = "A+B"
        elif "A" in normalized:
            tier_key = "A"
        elif "B" in normalized:
            tier_key = "B"
        elif "C" in normalized:
            tier_key = "C"
        else:
            tier_key = "A"

        total_savings = float(combined.get(tier_key) or 0)
        snapshot.selected_tiers = "+".join(sorted(set(normalized), key=lambda x: "ABC".index(x)))
        snapshot.total_savings_selected = _round2(total_savings)
        snapshot.updated_at = datetime.utcnow()

        assessment = IndependenceCostAssessment.query.filter_by(
            id=icc_assessment_id,
            user_id=user_id,
        ).first()
        if assessment is None:
            raise LookupError("ICC assessment not found")

        original_gap = float(assessment.monthly_independence_gap or 0)
        startup_cost = float(assessment.total_startup_cost or 0)
        new_gap = _round2(max(0.0, original_gap - total_savings))

        original_timeline = (
            int(math.ceil(float(assessment.months_to_save_startup)))
            if assessment.months_to_save_startup
            else None
        )
        new_timeline = (
            int(math.ceil(startup_cost / new_gap))
            if new_gap > 0 and startup_cost > 0
            else 0
        )

        db.session.commit()

        return {
            "success": True,
            "snapshot_id": str(snapshot.id),
            "selected_tiers": snapshot.selected_tiers,
            "total_monthly_savings": _round2(total_savings),
            "original_monthly_gap": _round2(original_gap),
            "new_gap_after_cuts": new_gap,
            "original_timeline_months": original_timeline,
            "new_timeline_months": new_timeline,
            "waterfall_link": "/dashboard/waterfall",
        }
