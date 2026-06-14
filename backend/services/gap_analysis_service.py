#!/usr/bin/env python3
"""Rent vs. Buy gap analysis — ideal buyer profile vs. current user situation."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

from backend.models.database import db
from backend.models.gap_analysis import GapAnalysisResult
from backend.models.housing_profile import HousingProfile
from backend.services.hprs_input_service import get_hprs_inputs

logger = logging.getLogger(__name__)

_SEVERITY_ON_TRACK = "on_track"
_SEVERITY_STRETCHED = "stretched"
_SEVERITY_BLOCKED = "blocked"


def _income_severity(gap: float, required: float) -> str:
    if gap <= 0:
        return _SEVERITY_ON_TRACK
    if gap <= required * 0.20:
        return _SEVERITY_STRETCHED
    return _SEVERITY_BLOCKED


def _savings_rate_severity(gap: float, required: float) -> str:
    if gap <= 0:
        return _SEVERITY_ON_TRACK
    if gap <= required * 0.30:
        return _SEVERITY_STRETCHED
    return _SEVERITY_BLOCKED


def _down_payment_severity(gap: float, target: float) -> str:
    if gap <= 0:
        return _SEVERITY_ON_TRACK
    if gap <= target * 0.40:
        return _SEVERITY_STRETCHED
    return _SEVERITY_BLOCKED


def _dti_severity(gap: float) -> str:
    if gap <= 0:
        return _SEVERITY_ON_TRACK
    if gap <= 0.08:
        return _SEVERITY_STRETCHED
    return _SEVERITY_BLOCKED


def _credit_severity(gap: int | None) -> str | None:
    if gap is None:
        return None
    if gap <= 0:
        return _SEVERITY_ON_TRACK
    if gap <= 80:
        return _SEVERITY_STRETCHED
    return _SEVERITY_BLOCKED


def _monthly_pi(loan_amount: float, interest_rate: float, loan_term_years: int) -> float:
    r = interest_rate / 12
    n = loan_term_years * 12
    if r == 0:
        return loan_amount / n
    factor = (1 + r) ** n
    return loan_amount * r * factor / (factor - 1)


def compute_gap_analysis(
    user_id: int,
    home_price: float,
    down_payment_pct: float,
    interest_rate: float,
    loan_term_years: int,
    timeline_months: int,
) -> dict[str, Any]:
    """Compute gap dimensions, persist a snapshot, and return the analysis payload."""
    try:
        loan_amount = home_price * (1 - down_payment_pct)
        monthly_pi = _monthly_pi(loan_amount, interest_rate, loan_term_years)
        monthly_tax = home_price * 0.011 / 12
        monthly_insurance = home_price * 0.005 / 12
        monthly_piti = monthly_pi + monthly_tax + monthly_insurance
        target_down_payment = home_price * down_payment_pct
        required_gross_income = monthly_piti / 0.28
        required_monthly_savings = target_down_payment / timeline_months

        hprs_inputs = get_hprs_inputs(user_id)
        gross_monthly_income = hprs_inputs.get("gross_monthly_income")
        total_monthly_obligations = hprs_inputs.get("total_monthly_obligations")
        credit_score = hprs_inputs.get("credit_score")

        current_monthly_savings = 0.0
        if (
            gross_monthly_income is not None
            and total_monthly_obligations is not None
        ):
            surplus = gross_monthly_income - total_monthly_obligations
            if surplus > 0:
                current_monthly_savings = float(surplus)

        housing = HousingProfile.query.filter_by(user_id=user_id).first()
        if housing and housing.down_payment_saved is not None:
            current_savings_balance = float(housing.down_payment_saved)
        else:
            saved = hprs_inputs.get("down_payment_saved")
            current_savings_balance = float(saved) if saved is not None else 0.0

        current_back_end_dti = float(hprs_inputs.get("current_dti") or 0)

        income_for_gap = float(gross_monthly_income or 0)
        gap_income = required_gross_income - income_for_gap
        income_severity = _income_severity(gap_income, required_gross_income)

        gap_savings_rate = required_monthly_savings - current_monthly_savings
        savings_severity = _savings_rate_severity(
            gap_savings_rate, required_monthly_savings
        )

        gap_down_payment = target_down_payment - current_savings_balance
        down_payment_severity = _down_payment_severity(
            gap_down_payment, target_down_payment
        )

        gap_dti = current_back_end_dti - 0.36
        dti_severity = _dti_severity(gap_dti)

        gap_credit: int | None
        if credit_score is None:
            gap_credit = None
            credit_severity = None
        else:
            gap_credit = 740 - int(credit_score)
            credit_severity = _credit_severity(gap_credit)

        partial_data = gross_monthly_income is None or credit_score is None

        severities = [
            income_severity,
            savings_severity,
            down_payment_severity,
            dti_severity,
        ]
        if credit_severity is not None:
            severities.append(credit_severity)

        any_blocked = _SEVERITY_BLOCKED in severities
        any_stretched = _SEVERITY_STRETCHED in severities
        all_on_track = (
            not partial_data
            and all(s == _SEVERITY_ON_TRACK for s in severities)
        )

        row = GapAnalysisResult(
            user_id=user_id,
            home_price=Decimal(str(round(home_price, 2))),
            down_payment_pct=Decimal(str(round(down_payment_pct, 2))),
            interest_rate=Decimal(str(round(interest_rate, 3))),
            loan_term_years=loan_term_years,
            timeline_months=timeline_months,
            gap_income=Decimal(str(round(gap_income, 2))),
            gap_savings_rate=Decimal(str(round(gap_savings_rate, 2))),
            gap_down_payment=Decimal(str(round(gap_down_payment, 2))),
            gap_dti=Decimal(str(round(gap_dti, 4))),
            gap_credit=gap_credit,
            income_severity=income_severity,
            savings_severity=savings_severity,
            down_payment_severity=down_payment_severity,
            dti_severity=dti_severity,
            credit_severity=credit_severity,
            required_gross_income=Decimal(str(round(required_gross_income, 2))),
            required_monthly_savings=Decimal(str(round(required_monthly_savings, 2))),
            target_down_payment=Decimal(str(round(target_down_payment, 2))),
            monthly_piti=Decimal(str(round(monthly_piti, 2))),
        )
        db.session.add(row)
        db.session.commit()

        return {
            "gap_analysis_id": row.id,
            "home_price": round(home_price, 2),
            "monthly_piti": round(monthly_piti, 2),
            "target_down_payment": round(target_down_payment, 2),
            "required_gross_income": round(required_gross_income, 2),
            "required_monthly_savings": round(required_monthly_savings, 2),
            "current": {
                "gross_monthly_income": (
                    round(float(gross_monthly_income), 2)
                    if gross_monthly_income is not None
                    else None
                ),
                "current_monthly_savings": round(current_monthly_savings, 2),
                "current_savings_balance": round(current_savings_balance, 2),
                "credit_score": credit_score,
                "back_end_dti": round(current_back_end_dti, 4),
            },
            "gaps": {
                "income": {
                    "gap": round(gap_income, 2),
                    "severity": income_severity,
                },
                "savings_rate": {
                    "gap": round(gap_savings_rate, 2),
                    "severity": savings_severity,
                },
                "down_payment": {
                    "gap": round(gap_down_payment, 2),
                    "severity": down_payment_severity,
                },
                "dti": {
                    "gap": round(gap_dti, 4),
                    "severity": dti_severity,
                },
                "credit": {
                    "gap": gap_credit,
                    "severity": credit_severity,
                },
            },
            "any_blocked": any_blocked,
            "any_stretched": any_stretched,
            "all_on_track": all_on_track,
            "partial_data": partial_data,
        }
    except Exception:
        logger.warning(
            "gap analysis computation failed for user_id=%s",
            user_id,
            exc_info=True,
        )
        db.session.rollback()
        return {"error": "computation_failed"}
