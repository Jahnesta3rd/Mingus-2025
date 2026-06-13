#!/usr/bin/env python3
"""Read-only aggregation of onboarding data for Home Purchase Readiness Score (HPRS)."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from backend.models.career_profile import CareerProfile
from backend.models.financial_setup import RecurringExpense
from backend.models.housing_profile import HousingProfile
from backend.models.transaction_schedule import IncomeStream
from backend.models.user_models import User
from backend.models.database import db
from backend.services.bls_oes_service import get_national_wage_percentiles
from backend.utils.user_profile_context import (
    extract_zip_from_text,
    resolve_current_salary,
)

_MONTHLY_EXPENSE_MULTIPLIERS: dict[str, float] = {
    "weekly": 52 / 12,
    "biweekly": 26 / 12,
    "monthly": 1.0,
    "quarterly": 1 / 3,
    "annual": 1 / 12,
}

_MONTHLY_INCOME_MULTIPLIERS: dict[str, float] = {
    "weekly": 52 / 12,
    "biweekly": 26 / 12,
    "semimonthly": 2.0,
    "monthly": 1.0,
    "quarterly": 1 / 3,
    "annual": 1 / 12,
}

_W2_STREAM_TYPES = frozenset({"earned", "w2"})
_1099_STREAM_TYPES = frozenset({"gig", "1099", "rental", "self_employed"})

_DEBT_CATEGORIES = frozenset({"debt"})
_RENT_CATEGORIES = frozenset({"housing", "rent"})


def _parse_json_object(raw: Any) -> dict:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}


def _coerce_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1", "y"}:
            return True
        if normalized in {"false", "no", "0", "n"}:
            return False
    return None


def _to_monthly_amount(amount: Decimal | float, frequency: str, *, table: str) -> float:
    multipliers = _MONTHLY_INCOME_MULTIPLIERS if table == "income" else _MONTHLY_EXPENSE_MULTIPLIERS
    freq = (frequency or "monthly").strip().lower()
    multiplier = multipliers.get(freq, 1.0)
    return float(amount) * multiplier


def _normalize_stream_income_type(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in _W2_STREAM_TYPES:
        return "w2"
    if value in _1099_STREAM_TYPES:
        return "1099"
    return "unknown"


def _dominant_income_type(streams: list[IncomeStream]) -> str:
    if not streams:
        return "unknown"
    normalized = {_normalize_stream_income_type(s.income_type) for s in streams}
    normalized.discard("unknown")
    if not normalized:
        return "unknown"
    if "w2" in normalized and "1099" in normalized:
        return "mixed"
    if len(normalized) == 1:
        return next(iter(normalized))
    return "mixed"


def _load_user_profile_json(user: User) -> tuple[dict, dict, dict]:
    personal_info: dict = {}
    financial_info: dict = {}
    goals: dict = {}
    email = (user.email or "").strip().lower()
    if not email:
        return personal_info, financial_info, goals
    try:
        row = db.session.execute(
            text(
                "SELECT personal_info, financial_info, goals "
                "FROM user_profiles WHERE email = :email LIMIT 1"
            ),
            {"email": email},
        ).fetchone()
    except Exception:
        return personal_info, financial_info, goals
    if not row:
        return personal_info, financial_info, goals
    personal_info = _parse_json_object(row[0])
    financial_info = _parse_json_object(row[1])
    goals = _parse_json_object(row[2])
    return personal_info, financial_info, goals


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _resolve_credit_score(financial_info: dict, personal_info: dict, goals: dict) -> int | None:
    for source in (financial_info, personal_info, goals):
        score = _coerce_int(
            _first_present(
                source.get("credit_score"),
                source.get("creditScore"),
            )
        )
        if score is not None:
            return score
    return None


def _resolve_household_size(personal_info: dict, goals: dict) -> int | None:
    for source in (personal_info, goals):
        size = _coerce_int(
            _first_present(
                source.get("household_size"),
                source.get("householdSize"),
            )
        )
        if size is not None:
            return size
    return None


def _resolve_has_co_borrower(personal_info: dict, goals: dict) -> bool | None:
    for source in (personal_info, goals):
        value = _first_present(
            source.get("has_co_borrower"),
            source.get("hasCoBorrower"),
            source.get("co_borrower"),
            source.get("coBorrower"),
        )
        coerced = _coerce_bool(value)
        if coerced is not None:
            return coerced
    return None


def _resolve_down_payment_target_pct(
    goals: dict,
    personal_info: dict,
    financial_info: dict,
) -> float:
    for source in (goals, personal_info, financial_info):
        pct = _coerce_float(
            _first_present(
                source.get("down_payment_target_pct"),
                source.get("downPaymentTargetPct"),
                source.get("down_payment_percent"),
                source.get("downPaymentPercent"),
            )
        )
        if pct is not None:
            return pct
    return 20.0


def _resolve_target_zip(
    housing: HousingProfile | None,
    personal_info: dict,
    goals: dict,
) -> str | None:
    for source in (goals, personal_info):
        raw = _first_present(source.get("target_zip"), source.get("targetZip"))
        if raw:
            zip_code = extract_zip_from_text(str(raw))
            if zip_code:
                return zip_code
        zip_code = extract_zip_from_text(str(source.get("zip_code") or source.get("zipCode") or ""))
        if zip_code:
            return zip_code
    if housing and housing.zip_or_city:
        zip_code = extract_zip_from_text(housing.zip_or_city)
        if zip_code:
            return zip_code
    return None


def _compute_percentile_bracket(current_salary: int, percentiles: dict) -> int | None:
    p10 = percentiles.get("p10")
    p25 = percentiles.get("p25")
    p50 = percentiles.get("p50")
    p75 = percentiles.get("p75")
    p90 = percentiles.get("p90")
    if None in (p10, p25, p50, p75, p90):
        return None
    salary = float(current_salary)
    if salary < p10:
        return 0
    if salary < p25:
        return 10
    if salary < p50:
        return 25
    if salary < p75:
        return 50
    if salary < p90:
        return 75
    return 90


def _resolve_income_percentile(user: User, career: CareerProfile | None) -> int | None:
    if not career or not career.bls_career_field:
        return None
    current_salary = resolve_current_salary(user, career)
    if current_salary is None:
        return None
    wage_data = get_national_wage_percentiles(career.bls_career_field)
    percentiles = {
        key: wage_data[key]
        for key in ("p10", "p25", "p50", "p75", "p90")
        if key in wage_data
    }
    return _compute_percentile_bracket(current_salary, percentiles)


def _is_debt_expense(expense: RecurringExpense) -> bool:
    category = (expense.category or "").strip().lower()
    if category in _DEBT_CATEGORIES:
        return True
    name = (expense.name or "").strip().lower()
    return any(token in name for token in ("loan", "credit card", "credit_card", "mortgage"))


def _is_rent_expense(expense: RecurringExpense) -> bool:
    category = (expense.category or "").strip().lower()
    return category in _RENT_CATEGORIES


def get_hprs_inputs(user_id: int) -> dict:
    """Aggregate HPRS input fields for a user; never raises on missing data."""
    empty: dict[str, Any] = {
        "gross_monthly_income": None,
        "income_type": "unknown",
        "employment_tenure_months": None,
        "total_monthly_debt": None,
        "monthly_rent": None,
        "total_monthly_obligations": None,
        "target_price": None,
        "target_timeline_months": None,
        "down_payment_saved": None,
        "down_payment_target_pct": 20.0,
        "target_zip": None,
        "credit_score": None,
        "household_size": None,
        "has_co_borrower": None,
        "income_percentile": None,
        "employer_type": None,
        "down_payment_needed": None,
        "down_payment_gap": None,
        "current_dti": None,
        "partial_data": True,
    }

    try:
        user = db.session.get(User, user_id)
        if not user:
            return empty

        streams = (
            IncomeStream.query.filter_by(user_id=user.id, is_active=True)
            .order_by(IncomeStream.amount.desc())
            .all()
        )
        expenses = RecurringExpense.query.filter_by(user_id=user.id, is_active=True).all()
        housing = HousingProfile.query.filter_by(user_id=user.id).first()
        career = CareerProfile.query.filter_by(user_id=user.id).first()
        personal_info, financial_info, goals = _load_user_profile_json(user)

        gross_monthly_income = None
        if streams:
            gross_monthly_income = round(
                sum(
                    _to_monthly_amount(s.amount, s.frequency, table="income")
                    for s in streams
                ),
                2,
            )

        income_type = _dominant_income_type(streams)

        employment_tenure_months = None
        if streams:
            top_stream = streams[0]
            employment_tenure_months = _coerce_int(
                getattr(top_stream, "employment_tenure_months", None)
            )
            if employment_tenure_months is None:
                employment_tenure_months = _coerce_int(
                    getattr(top_stream, "tenure_months", None)
                )

        total_monthly_debt = None
        debt_total = sum(
            _to_monthly_amount(e.amount, e.frequency, table="expense")
            for e in expenses
            if _is_debt_expense(e)
        )
        if expenses:
            total_monthly_debt = round(debt_total, 2)

        monthly_rent = None
        rent_from_expenses = sum(
            _to_monthly_amount(e.amount, e.frequency, table="expense")
            for e in expenses
            if _is_rent_expense(e)
        )
        if rent_from_expenses > 0:
            monthly_rent = round(rent_from_expenses, 2)
        elif housing and housing.housing_type == "rent":
            monthly_rent = round(float(housing.monthly_cost), 2)

        total_monthly_obligations = None
        if expenses:
            total_monthly_obligations = round(
                sum(
                    _to_monthly_amount(e.amount, e.frequency, table="expense")
                    for e in expenses
                ),
                2,
            )

        target_price = _coerce_float(housing.target_price) if housing else None
        target_timeline_months = (
            _coerce_int(housing.target_timeline_months) if housing else None
        )
        down_payment_saved = None
        if housing and housing.down_payment_saved is not None:
            down_payment_saved = round(float(housing.down_payment_saved), 2)

        down_payment_target_pct = _resolve_down_payment_target_pct(
            goals, personal_info, financial_info
        )
        target_zip = _resolve_target_zip(housing, personal_info, goals)

        credit_score = _resolve_credit_score(financial_info, personal_info, goals)
        household_size = _resolve_household_size(personal_info, goals)
        has_co_borrower = _resolve_has_co_borrower(personal_info, goals)

        income_percentile = _resolve_income_percentile(user, career)
        employer_type = (career.employer_type if career else None) or None

        down_payment_needed = None
        if target_price is not None:
            down_payment_needed = round(
                target_price * (down_payment_target_pct / 100.0),
                2,
            )

        down_payment_gap = None
        if down_payment_needed is not None and down_payment_saved is not None:
            down_payment_gap = round(down_payment_needed - down_payment_saved, 2)

        current_dti = None
        if (
            gross_monthly_income is not None
            and gross_monthly_income > 0
            and total_monthly_debt is not None
        ):
            current_dti = round(total_monthly_debt / gross_monthly_income, 4)

        partial_data = any(
            value is None
            for value in (
                gross_monthly_income,
                target_price,
                down_payment_saved,
                credit_score,
            )
        )

        return {
            "gross_monthly_income": gross_monthly_income,
            "income_type": income_type,
            "employment_tenure_months": employment_tenure_months,
            "total_monthly_debt": total_monthly_debt,
            "monthly_rent": monthly_rent,
            "total_monthly_obligations": total_monthly_obligations,
            "target_price": target_price,
            "target_timeline_months": target_timeline_months,
            "down_payment_saved": down_payment_saved,
            "down_payment_target_pct": down_payment_target_pct,
            "target_zip": target_zip,
            "credit_score": credit_score,
            "household_size": household_size,
            "has_co_borrower": has_co_borrower,
            "income_percentile": income_percentile,
            "employer_type": employer_type,
            "down_payment_needed": down_payment_needed,
            "down_payment_gap": down_payment_gap,
            "current_dti": current_dti,
            "partial_data": partial_data,
        }
    except Exception:
        return empty
