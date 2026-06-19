#!/usr/bin/env python3
"""GET /api/expenses/summary/<user_email> — spending aggregation for Snapshot card."""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal

from flask import Blueprint, current_app, jsonify
from sqlalchemy import func, or_
from sqlalchemy.exc import OperationalError, ProgrammingError

from backend.models.database import db
from backend.models.financial_setup import RecurringExpense
from backend.models.quick_spend import QuickSpendEntry
from backend.models.transaction_schedule import IncomeStream
from backend.models.user_models import User

logger = logging.getLogger(__name__)

expenses_summary_bp = Blueprint(
    "expenses_summary",
    __name__,
    url_prefix="/api/expenses",
)


def _round_money(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return round(float(value), 2)
    return round(float(value), 2)


def _resolve_user_id(user_email: str) -> int | None:
    user = User.query.filter(
        func.lower(User.email) == user_email.strip().lower()
    ).first()
    if not user:
        return None
    return int(user.id)


def _income_monthly(user_id: int) -> float:
    rows = (
        IncomeStream.query.filter(
            IncomeStream.user_id == user_id,
            or_(IncomeStream.is_active.is_(True), IncomeStream.is_active.is_(None)),
        )
        .with_entities(func.coalesce(func.sum(IncomeStream.amount), 0))
        .scalar()
    )
    return _round_money(rows)


def _recurring_by_category(user_id: int) -> dict[str, float]:
    grouped: dict[str, float] = {}
    rows = (
        db.session.query(
            RecurringExpense.category,
            func.coalesce(func.sum(RecurringExpense.amount), 0),
        )
        .filter(RecurringExpense.user_id == user_id)
        .group_by(RecurringExpense.category)
        .all()
    )
    for category, total in rows:
        key = (category or "other").strip() or "other"
        grouped[key] = _round_money(total)
    return grouped


def _quick_spend_by_merchant_group(user_id: int) -> dict[str, float]:
    today = date.today()
    month_start = today.replace(day=1)
    grouped: dict[str, float] = {}
    try:
        rows = (
            db.session.query(
                QuickSpendEntry.merchant_group,
                func.coalesce(func.sum(QuickSpendEntry.amount), 0),
            )
            .filter(
                QuickSpendEntry.user_id == user_id,
                QuickSpendEntry.date >= month_start,
                QuickSpendEntry.date <= today,
            )
            .group_by(QuickSpendEntry.merchant_group)
            .all()
        )
    except (OperationalError, ProgrammingError):
        db.session.rollback()
        return {}

    for merchant_group, total in rows:
        key = (merchant_group or "other").strip() or "other"
        grouped[key] = _round_money(total)
    return grouped


def _merge_categories(
    recurring: dict[str, float], quick_spend: dict[str, float]
) -> dict[str, float]:
    merged = dict(recurring)
    for key, amount in quick_spend.items():
        merged[key] = _round_money(merged.get(key, 0.0) + amount)
    return merged


@expenses_summary_bp.route("/summary/<user_email>", methods=["GET"])
def get_expenses_summary(user_email: str):
    """Aggregate recurring expenses and current-month quick spend by category."""
    try:
        user_id = _resolve_user_id(user_email)
        if user_id is None:
            return jsonify({"error": "User not found"}), 404

        income_monthly = _income_monthly(user_id)
        recurring = _recurring_by_category(user_id)
        quick_spend = _quick_spend_by_merchant_group(user_id)
        merged = _merge_categories(recurring, quick_spend)

        categories = [
            {"name": name, "amount": amount}
            for name, amount in sorted(
                merged.items(), key=lambda item: item[1], reverse=True
            )
        ]

        return jsonify({"income_monthly": income_monthly, "categories": categories}), 200
    except Exception:
        current_app.logger.error("expenses summary failed for %s", user_email, exc_info=True)
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
