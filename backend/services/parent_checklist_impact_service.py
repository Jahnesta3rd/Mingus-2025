#!/usr/bin/env python3
"""Apply financial impact from New Parent checklist items to recurring expenses."""

from __future__ import annotations

from decimal import Decimal

from backend.models.database import db
from backend.models.financial_setup import RecurringExpense

SOURCE = "parent_checklist"

RECURRING_IMPACTS: dict[str, dict[str, object]] = {
    "open_529": {
        "name": "529 college savings",
        "category": "other",
        "default_amount": 200.00,
        "frequency": "monthly",
    },
    "life_insurance_will": {
        "name": "Life insurance premium",
        "category": "insurance",
        "default_amount": 50.00,
        "frequency": "monthly",
    },
    "short_term_disability": {
        "name": "Short-term disability",
        "category": "insurance",
        "default_amount": 30.00,
        "frequency": "monthly",
    },
    "childcare_waitlist": {
        "name": "Childcare",
        "category": "childcare",
        "default_amount": 1800.00,
        "frequency": "monthly",
    },
}

ONE_TIME_IMPACTS: dict[str, dict[str, object]] = {
    "baby_emergency_fund": {
        "name": "Baby emergency fund",
        "default_amount": 1500.00,
    },
    "out_of_pocket_double": {
        "name": "Out-of-pocket max (×2)",
        "default_amount": 4000.00,
    },
}

INFORMATIONAL_ITEM_IDS = frozenset(
    {
        "health_insurance_window",
        "trump_account",
        "beneficiary_update",
        "year_end_deductible",
        "w4_update",
        "leave_income",
    }
)


def _informational_none(item_id: str) -> dict:
    return {
        "applied": False,
        "reason": "informational",
        "impact_type": "none",
        "amount": None,
        "name": item_id,
    }


def _error_result(item_id: str) -> dict:
    return {
        "applied": False,
        "reason": "error",
        "impact_type": "none",
        "amount": None,
        "name": item_id,
    }


def apply_checklist_item_impact(
    user_id: int,
    item_id: str,
    amount_override: float | None = None,
) -> dict:
    if item_id in INFORMATIONAL_ITEM_IDS:
        return _informational_none(item_id)

    if item_id in ONE_TIME_IMPACTS:
        meta = ONE_TIME_IMPACTS[item_id]
        return {
            "applied": False,
            "reason": "informational",
            "impact_type": "one_time",
            "amount": float(meta["default_amount"]),
            "name": str(meta["name"]),
        }

    if item_id not in RECURRING_IMPACTS:
        return _informational_none(item_id)

    meta = RECURRING_IMPACTS[item_id]
    name = str(meta["name"])
    category = str(meta["category"])
    frequency = str(meta["frequency"])
    default_amount = float(meta["default_amount"])

    try:
        existing = RecurringExpense.query.filter_by(
            user_id=user_id,
            source=SOURCE,
            name=name,
        ).first()
        if existing is not None:
            return {
                "applied": False,
                "reason": "already_applied",
                "impact_type": "recurring",
                "amount": float(existing.amount),
                "name": name,
            }

        amount_used = default_amount if amount_override is None else float(amount_override)
        row = RecurringExpense(
            user_id=user_id,
            name=name,
            amount=Decimal(str(amount_used)),
            category=category,
            due_day=None,
            frequency=frequency,
            is_active=True,
            source=SOURCE,
        )
        db.session.add(row)
        db.session.commit()
        return {
            "applied": True,
            "impact_type": "recurring",
            "amount": amount_used,
            "name": name,
            "frequency": frequency,
        }
    except Exception:
        db.session.rollback()
        return _error_result(item_id)
