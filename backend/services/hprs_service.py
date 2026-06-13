#!/usr/bin/env python3
"""HPRS orchestrator — runs pillar scoring and risk modifiers into one result."""

from __future__ import annotations

import logging
from typing import Any

from backend.models.hprs_score import HprsScore
from backend.services.hprs_career_risk_service import derive_career_risk
from backend.services.hprs_score_service import compute_hprs_score
from backend.services.hprs_vehicle_risk_service import derive_vehicle_risk

logger = logging.getLogger(__name__)

_PILLAR_WEIGHTS = {
    "down_payment": 0.30,
    "dti": 0.25,
    "credit": 0.20,
    "income": 0.10,
    "reserves": 0.10,
}


def _iso_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _assemble_result(
    row: HprsScore,
    career_result: dict[str, Any],
    vehicle_result: dict[str, Any],
) -> dict[str, Any]:
    inputs_snapshot = row.inputs_snapshot if isinstance(row.inputs_snapshot, dict) else {}
    partial_data = inputs_snapshot.get("partial_data")
    if partial_data is None:
        partial_data = bool(inputs_snapshot.get("partial_data", False))

    return {
        "overall_score": int(row.overall_score),
        "readiness_tier": row.readiness_tier,
        "partial_data": bool(partial_data),
        "computed_at": _iso_timestamp(row.computed_at),
        "pillars": {
            "down_payment": {
                "score": int(row.down_payment_score or 0),
                "weight": _PILLAR_WEIGHTS["down_payment"],
            },
            "dti": {
                "score": int(row.dti_score or 0),
                "weight": _PILLAR_WEIGHTS["dti"],
            },
            "credit": {
                "score": int(row.credit_score or 0),
                "weight": _PILLAR_WEIGHTS["credit"],
            },
            "income": {
                "score": int(row.income_stability_score or 0),
                "weight": _PILLAR_WEIGHTS["income"],
            },
            "reserves": {
                "score": int(row.savings_rate_score or 0),
                "weight": _PILLAR_WEIGHTS["reserves"],
            },
        },
        "career_risk": {
            "score": row.career_risk_score,
            "band": row.career_risk_band,
            "modifier": int(row.career_modifier or 0),
            "active_layoff": bool(career_result.get("active_layoff", False)),
        },
        "vehicle_risk": {
            "score": row.vehicle_risk_score,
            "band": row.vehicle_risk_band,
            "modifier": int(row.vehicle_modifier or 0),
            "verdict": vehicle_result.get("verdict"),
            "annual_repair_exposure": vehicle_result.get("annual_repair_exposure"),
        },
        "combined_modifier": int(row.combined_modifier or 0),
        "target_price": row.target_price,
        "target_timeline_months": row.target_timeline_months,
        "down_payment_saved": row.down_payment_saved,
        "down_payment_needed": row.down_payment_needed,
        "inputs_snapshot": inputs_snapshot,
    }


def compute_full_hprs(user_id: int) -> dict:
    """Run pillar scoring, career risk, and vehicle risk; return assembled HPRS dict."""
    career_result: dict[str, Any] = {}
    vehicle_result: dict[str, Any] = {}

    try:
        compute_hprs_score(user_id)
    except Exception:
        logger.warning(
            "compute_full_hprs: compute_hprs_score failed for user_id=%s",
            user_id,
            exc_info=True,
        )
        return {"error": "score_computation_failed"}

    try:
        career_result = derive_career_risk(user_id)
    except Exception:
        logger.warning(
            "compute_full_hprs: derive_career_risk failed for user_id=%s",
            user_id,
            exc_info=True,
        )

    try:
        vehicle_result = derive_vehicle_risk(user_id)
    except Exception:
        logger.warning(
            "compute_full_hprs: derive_vehicle_risk failed for user_id=%s",
            user_id,
            exc_info=True,
        )

    row = HprsScore.query.filter_by(user_id=user_id).first()
    if row is None:
        logger.warning(
            "compute_full_hprs: hprs_scores row missing after pipeline for user_id=%s",
            user_id,
        )
        return {"error": "score_computation_failed"}

    return _assemble_result(row, career_result, vehicle_result)
