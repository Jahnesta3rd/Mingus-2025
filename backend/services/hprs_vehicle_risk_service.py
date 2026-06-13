#!/usr/bin/env python3
"""Vehicle risk derivation for HPRS from vehicle profile and analytics."""

from __future__ import annotations

from datetime import date
from typing import Any

from backend.models.database import db
from backend.models.hprs_score import HprsScore
from backend.models.vehicle_models import Vehicle
from backend.services.vehicle_analytics_service import VehicleAnalyticsService
from backend.services.vin_advisor_service import analyze_vehicle

_PILLAR_WEIGHTS = {
    "down_payment": 0.30,
    "dti": 0.25,
    "credit": 0.20,
    "income_stability": 0.10,
    "savings_rate": 0.10,
}

_BAND_MODIFIERS = {
    "STABLE": 0,
    "WATCH": -2,
    "ELEVATED": -5,
    "CRITICAL": -10,
}

_NO_VEHICLE = {
    "vehicle_risk_score": 0,
    "vehicle_risk_band": "STABLE",
    "vehicle_modifier": 0,
    "data_source": "no_vehicle",
    "annual_repair_exposure": None,
    "replacement_cost_est": None,
    "verdict": None,
}


def _clamp_0_100(value: int | float) -> int:
    return int(max(0, min(100, round(value))))


def _modifier_for_band(band: str) -> int:
    return _BAND_MODIFIERS.get(band, 0)


def _risk_band(score: int) -> str:
    if score <= 20:
        return "STABLE"
    if score <= 45:
        return "WATCH"
    if score <= 70:
        return "ELEVATED"
    return "CRITICAL"


def _get_primary_vehicle(user_id: int) -> Vehicle | None:
    return (
        db.session.query(Vehicle)
        .filter(Vehicle.user_id == user_id)
        .order_by(Vehicle.id.asc())
        .first()
    )


def _base_mileage_age_score(vehicle_age: int, mileage: int) -> int:
    scores: list[int] = []
    if vehicle_age <= 3 and mileage < 36000:
        scores.append(10)
    if 4 <= vehicle_age <= 6 or 36000 <= mileage < 75000:
        scores.append(25)
    if 7 <= vehicle_age <= 10 or 75000 <= mileage < 120000:
        scores.append(45)
    if 11 <= vehicle_age <= 14 or 120000 <= mileage < 150000:
        scores.append(65)
    if vehicle_age > 14 or mileage > 150000:
        scores.append(80)
    return max(scores) if scores else 0


def _apply_modifiers(
    base_score: int,
    verdict: str | None,
    annual_repair_exposure: float | None,
) -> int:
    score = base_score
    if verdict == "replace":
        score += 15
    elif verdict == "monitor":
        score += 5

    if annual_repair_exposure is not None:
        exposure = float(annual_repair_exposure)
        if exposure > 3000:
            score += 10
        elif exposure > 1500:
            score += 5

    return _clamp_0_100(score)


def _replacement_cost_est(
    book_value: int,
    annual_salary: int,
) -> float | None:
    if book_value <= 0:
        return None
    value_budget = book_value * 2.5
    if annual_salary > 0:
        salary_budget = annual_salary * 0.25
        return float(min(salary_budget, value_budget))
    return float(value_budget)


def _load_vin_advisor(user_id: int) -> dict[str, Any] | None:
    try:
        result = analyze_vehicle(user_id, db.session)
    except Exception:
        db.session.rollback()
        return None
    if result is None:
        return None
    return {
        "verdict": result.verdict,
        "annual_repair_exposure": float(result.annual_repair_exposure),
        "replacement_cost_est": _replacement_cost_est(
            result.book_value,
            result.annual_salary,
        ),
    }


def _load_vehicle_analytics(user_id: int, vehicle: Vehicle) -> dict[str, Any]:
    try:
        service = VehicleAnalyticsService()
        vehicles = [vehicle]
        cost_analysis = service._get_cost_per_mile_analysis(user_id, vehicles)  # noqa: SLF001
        peer_data = service._get_peer_comparison_data(user_id, vehicles)  # noqa: SLF001
        return {
            "cost_per_mile": cost_analysis.get("current"),
            "peer_percentile": peer_data.get("percentile"),
        }
    except Exception:
        db.session.rollback()
        return {}


def _recompute_overall_score(row: HprsScore, vehicle_modifier: int) -> int:
    career_modifier = int(row.career_modifier or 0)
    weighted = (
        int(row.down_payment_score or 0) * _PILLAR_WEIGHTS["down_payment"]
        + int(row.dti_score or 0) * _PILLAR_WEIGHTS["dti"]
        + int(row.credit_score or 0) * _PILLAR_WEIGHTS["credit"]
        + int(row.income_stability_score or 0) * _PILLAR_WEIGHTS["income_stability"]
        + int(row.savings_rate_score or 0) * _PILLAR_WEIGHTS["savings_rate"]
        + career_modifier
        + vehicle_modifier
    )
    return _clamp_0_100(weighted)


def _update_hprs_score_row(user_id: int, result: dict[str, Any]) -> None:
    row = HprsScore.query.filter_by(user_id=user_id).first()
    if row is None:
        return

    vehicle_modifier = int(result["vehicle_modifier"])
    career_modifier = int(row.career_modifier or 0)

    row.vehicle_risk_score = result["vehicle_risk_score"]
    row.vehicle_risk_band = result["vehicle_risk_band"]
    row.vehicle_modifier = vehicle_modifier
    row.combined_modifier = career_modifier + vehicle_modifier
    row.overall_score = _recompute_overall_score(row, vehicle_modifier)
    db.session.commit()


def derive_vehicle_risk(user_id: int) -> dict:
    """Derive vehicle risk from profile/analytics and update hprs_scores."""
    try:
        vehicle = _get_primary_vehicle(user_id)
        if vehicle is None:
            result = dict(_NO_VEHICLE)
            _update_hprs_score_row(user_id, result)
            return result

        ref_year = date.today().year
        vehicle_age = max(0, ref_year - int(vehicle.year))
        mileage = int(vehicle.current_mileage or 0)

        vin_advisor = _load_vin_advisor(user_id)
        analytics = _load_vehicle_analytics(user_id, vehicle)

        verdict = vin_advisor.get("verdict") if vin_advisor else None
        annual_repair_exposure = (
            vin_advisor.get("annual_repair_exposure") if vin_advisor else None
        )
        replacement_cost_est = (
            vin_advisor.get("replacement_cost_est") if vin_advisor else None
        )

        base_score = _base_mileage_age_score(vehicle_age, mileage)
        vehicle_risk_score = _apply_modifiers(
            base_score,
            verdict,
            annual_repair_exposure,
        )
        band = _risk_band(vehicle_risk_score)
        data_source = "vin_advisor" if vin_advisor else "mileage_age"

        result = {
            "vehicle_risk_score": vehicle_risk_score,
            "vehicle_risk_band": band,
            "vehicle_modifier": _modifier_for_band(band),
            "data_source": data_source,
            "annual_repair_exposure": annual_repair_exposure,
            "replacement_cost_est": replacement_cost_est,
            "verdict": verdict,
        }
        _update_hprs_score_row(user_id, result)
        return result
    except Exception:
        db.session.rollback()
        result = dict(_NO_VEHICLE)
        _update_hprs_score_row(user_id, result)
        return result
