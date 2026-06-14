#!/usr/bin/env python3
"""Apply financial impact from New Parent checklist items to recurring expenses."""

from __future__ import annotations

from decimal import Decimal

from backend.models.database import db
from backend.models.financial_setup import RecurringExpense
from backend.models.transaction_schedule import IncomeStream
from backend.models.user_models import User
from backend.services.market_conditions_service import resolve_user_msa

SOURCE = "parent_checklist"

MSA_CHILDCARE_MONTHLY = {
    "41860": 3200,  # San Francisco
    "35620": 2800,  # New York
    "14460": 2500,  # Boston
    "42660": 2400,  # Seattle
    "47900": 2300,  # Washington DC
    "31080": 2200,  # Los Angeles
    "16980": 2000,  # Chicago
    "25540": 2000,  # Hartford
    "37980": 1900,  # Philadelphia
    "19740": 1900,  # Denver
    "12580": 1900,  # Baltimore
    "38900": 1900,  # Portland OR
    "33100": 1700,  # Miami
    "12420": 1700,  # Austin
    "40900": 1800,  # Sacramento
    "12060": 1600,  # Atlanta
    "39580": 1600,  # Raleigh
    "34980": 1500,  # Nashville
    "19100": 1500,  # Dallas
    "19820": 1500,  # Detroit
    "26420": 1400,  # Houston
    "38060": 1400,  # Phoenix
    "16740": 1400,  # Charlotte
    "41180": 1400,  # St. Louis
    "40060": 1400,  # Richmond
    "45300": 1300,  # Tampa
    "18140": 1300,  # Columbus
    "26900": 1300,  # Indianapolis
    "29820": 1300,  # Las Vegas
    "38300": 1300,  # Pittsburgh
    "17140": 1300,  # Cincinnati
    "47260": 1300,  # Virginia Beach
    "31140": 1200,  # Louisville
    "35380": 1200,  # New Orleans
    "41700": 1100,  # San Antonio
    "32820": 1000,  # Memphis
    "36420": 1000,  # Oklahoma City
    "13820": 900,   # Birmingham
}
CHILDCARE_NATIONAL_DEFAULT = 1800

_DEFAULT_CHECKLIST_DEFAULTS: dict[str, object] = {
    "childcare_default": CHILDCARE_NATIONAL_DEFAULT,
    "childcare_metro": "National average",
    "childcare_is_localized": False,
    "contribution_529": 200,
    "gross_monthly": 0,
    "income_source": "default",
}

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


def _income_to_monthly(amount: float, frequency: str) -> float:
    freq = (frequency or "monthly").strip().lower()
    if freq == "monthly":
        return amount
    if freq == "biweekly":
        return amount * 26 / 12
    if freq == "weekly":
        return amount * 52 / 12
    if freq == "annual":
        return amount / 12
    return 0.0


def get_checklist_defaults(user_id: int) -> dict:
    try:
        user = db.session.get(User, user_id)
        if user is None:
            return dict(_DEFAULT_CHECKLIST_DEFAULTS)

        msa_code, msa_name = resolve_user_msa(user)
        childcare_default = MSA_CHILDCARE_MONTHLY.get(
            msa_code or "",
            CHILDCARE_NATIONAL_DEFAULT,
        )

        streams = IncomeStream.query.filter_by(user_id=user.id, is_active=True).all()
        gross_monthly = sum(
            _income_to_monthly(float(stream.amount), stream.frequency)
            for stream in streams
        )

        if gross_monthly == 0:
            contribution_529 = 100
            income_source = "default"
        else:
            contribution_529 = max(
                100,
                min(500, round(gross_monthly * 0.015 / 25) * 25),
            )
            income_source = "income_streams"

        return {
            "childcare_default": childcare_default,
            "childcare_metro": msa_name or "National average",
            "childcare_is_localized": msa_code is not None,
            "contribution_529": contribution_529,
            "gross_monthly": round(gross_monthly, 2),
            "income_source": income_source,
        }
    except Exception:
        return dict(_DEFAULT_CHECKLIST_DEFAULTS)


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
