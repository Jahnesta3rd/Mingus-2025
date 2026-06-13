#!/usr/bin/env python3
"""Deterministic Home Purchase Readiness Score computation and persistence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert

from backend.models.database import db
from backend.models.hprs_score import HprsScore
from backend.models.hprs_score_history import HprsScoreHistory
from backend.services.hprs_input_service import get_hprs_inputs

_PILLAR_WEIGHTS = {
    "down_payment": 0.30,
    "dti": 0.25,
    "credit": 0.20,
    "income_stability": 0.10,
    "savings_rate": 0.10,
}


def _clamp_0_100(value: int | float) -> int:
    return int(max(0, min(100, round(value))))


def _readiness_tier(score: int) -> str:
    if score <= 39:
        return "not_ready"
    if score <= 54:
        return "building"
    if score <= 69:
        return "approaching"
    if score <= 84:
        return "ready"
    return "strong"


def _score_down_payment(
    down_payment_saved: float | None,
    down_payment_needed: float | None,
) -> int:
    if not down_payment_needed or down_payment_needed <= 0:
        return 0
    saved = float(down_payment_saved or 0)
    pct_saved = saved / down_payment_needed
    if pct_saved >= 1.0:
        return 100
    return _clamp_0_100(pct_saved * 99)


def _score_dti(current_dti: float | None) -> int:
    if current_dti is None:
        return 0
    dti = float(current_dti)
    if dti <= 0.28:
        return 100
    if dti <= 0.36:
        return 75
    if dti <= 0.43:
        return 50
    if dti <= 0.50:
        return 25
    return 0


def _score_credit(fico: int | None) -> int:
    if fico is None:
        return 0
    score = int(fico)
    if score >= 740:
        return 100
    if score >= 700:
        return 80
    if score >= 660:
        return 60
    if score >= 620:
        return 40
    return 0


def _score_income_stability(
    employer_type: str | None,
    employment_tenure_months: int | None,
) -> int:
    et = (employer_type or "").strip().lower()
    if et in {"w2", "federal"}:
        base = 100
    elif et in {"state_local", "nonprofit"}:
        base = 75
    elif et == "1099":
        base = 50
    elif et == "self_employed":
        base = 25
    else:
        base = 50

    if employment_tenure_months is not None:
        tenure = int(employment_tenure_months)
        if tenure >= 24:
            base += 10
        elif tenure < 6:
            base -= 10

    return _clamp_0_100(base)


def _score_savings_rate(
    gross_monthly_income: float | None,
    total_monthly_obligations: float | None,
    down_payment_saved: float | None,
) -> int:
    if gross_monthly_income is None or total_monthly_obligations is None:
        return 0
    surplus = float(gross_monthly_income) - float(total_monthly_obligations)
    if surplus <= 0:
        return 0
    saved = float(down_payment_saved or 0)
    reserve_months = saved / surplus
    if reserve_months >= 6:
        return 100
    if reserve_months >= 3:
        return 75
    if reserve_months >= 1:
        return 50
    if reserve_months > 0:
        return 25
    return 0


def _assemble_overall_score(
    d1: int,
    d2: int,
    d3: int,
    d4: int,
    d5: int,
    combined_modifier: int = 0,
) -> int:
    weighted = (
        d1 * _PILLAR_WEIGHTS["down_payment"]
        + d2 * _PILLAR_WEIGHTS["dti"]
        + d3 * _PILLAR_WEIGHTS["credit"]
        + d4 * _PILLAR_WEIGHTS["income_stability"]
        + d5 * _PILLAR_WEIGHTS["savings_rate"]
    )
    return _clamp_0_100(int(weighted) + combined_modifier)


def _score_payload(user_id: int, inputs: dict[str, Any]) -> dict[str, Any]:
    d1 = _score_down_payment(
        inputs.get("down_payment_saved"),
        inputs.get("down_payment_needed"),
    )
    d2 = _score_dti(inputs.get("current_dti"))
    d3 = _score_credit(inputs.get("credit_score"))
    d4 = _score_income_stability(
        inputs.get("employer_type"),
        inputs.get("employment_tenure_months"),
    )
    d5 = _score_savings_rate(
        inputs.get("gross_monthly_income"),
        inputs.get("total_monthly_obligations"),
        inputs.get("down_payment_saved"),
    )

    career_modifier = 0
    vehicle_modifier = 0
    combined_modifier = career_modifier + vehicle_modifier
    overall_score = _assemble_overall_score(d1, d2, d3, d4, d5, combined_modifier)
    tier = _readiness_tier(overall_score)
    now = datetime.utcnow()

    return {
        "user_id": user_id,
        "overall_score": overall_score,
        "readiness_tier": tier,
        "down_payment_score": d1,
        "dti_score": d2,
        "credit_score": d3,
        "income_stability_score": d4,
        "savings_rate_score": d5,
        "target_price": inputs.get("target_price"),
        "target_timeline_months": inputs.get("target_timeline_months"),
        "down_payment_saved": inputs.get("down_payment_saved"),
        "down_payment_needed": inputs.get("down_payment_needed"),
        "inputs_snapshot": inputs,
        "career_risk_score": None,
        "career_risk_band": None,
        "career_modifier": career_modifier,
        "vehicle_risk_score": None,
        "vehicle_risk_band": None,
        "vehicle_modifier": vehicle_modifier,
        "combined_modifier": combined_modifier,
        "market_score": None,
        "computed_at": now,
        "updated_at": now,
        "partial_data": inputs.get("partial_data"),
    }


def _upsert_hprs_score(payload: dict[str, Any]) -> None:
    now = payload["computed_at"]
    insert_values = {
        "user_id": payload["user_id"],
        "overall_score": payload["overall_score"],
        "readiness_tier": payload["readiness_tier"],
        "down_payment_score": payload["down_payment_score"],
        "credit_score": payload["credit_score"],
        "dti_score": payload["dti_score"],
        "savings_rate_score": payload["savings_rate_score"],
        "income_stability_score": payload["income_stability_score"],
        "target_price": payload["target_price"],
        "target_timeline_months": payload["target_timeline_months"],
        "down_payment_saved": payload["down_payment_saved"],
        "down_payment_needed": payload["down_payment_needed"],
        "inputs_snapshot": payload["inputs_snapshot"],
        "career_risk_score": payload["career_risk_score"],
        "career_risk_band": payload["career_risk_band"],
        "career_modifier": payload["career_modifier"],
        "vehicle_risk_score": payload["vehicle_risk_score"],
        "vehicle_risk_band": payload["vehicle_risk_band"],
        "vehicle_modifier": payload["vehicle_modifier"],
        "combined_modifier": payload["combined_modifier"],
        "market_score": payload["market_score"],
        "computed_at": now,
        "created_at": now,
        "updated_at": now,
    }
    update_values = {
        key: insert_values[key]
        for key in insert_values
        if key not in {"user_id", "created_at"}
    }
    update_values["updated_at"] = now

    stmt = insert(HprsScore.__table__).values(**insert_values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_hprs_scores_user_id",
        set_=update_values,
    )
    db.session.execute(stmt)


def _append_score_history(payload: dict[str, Any]) -> None:
    db.session.add(
        HprsScoreHistory(
            user_id=payload["user_id"],
            overall_score=payload["overall_score"],
            readiness_tier=payload["readiness_tier"],
            down_payment_score=payload["down_payment_score"],
            credit_score=payload["credit_score"],
            dti_score=payload["dti_score"],
            savings_rate_score=payload["savings_rate_score"],
            income_stability_score=payload["income_stability_score"],
            trigger="manual",
            recorded_at=payload["computed_at"],
        )
    )


def compute_hprs_score(user_id: int) -> dict:
    """Compute pillar scores, upsert hprs_scores, append history; return score dict."""
    inputs = get_hprs_inputs(user_id)
    payload = _score_payload(user_id, inputs)
    _upsert_hprs_score(payload)
    _append_score_history(payload)
    db.session.commit()
    return payload
