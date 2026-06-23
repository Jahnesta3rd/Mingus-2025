#!/usr/bin/env python3
"""Home Purchase Readiness Score API."""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import Any

from flask import Blueprint, current_app, jsonify
from sqlalchemy import or_

from backend.auth.decorators import current_user, require_auth
from backend.models.database import db
from backend.models.hprs_latent_candidate import HprsLatentCandidate
from backend.models.hprs_plan import HprsPlan
from backend.models.hprs_score import HprsScore
from backend.models.user_models import User
from backend.services.hprs_service import compute_full_hprs, generate_hprs_plan
from backend.services.hprs_career_risk_service import get_commitment_pipeline_context

logger = logging.getLogger(__name__)

hprs_bp = Blueprint("hprs", __name__, url_prefix="/api/housing")

_SCORE_STALE_DAYS = 7
_PLAN_STALE_DAYS = 30

_PILLAR_WEIGHTS = {
    "down_payment": 0.30,
    "dti": 0.25,
    "credit": 0.20,
    "income": 0.10,
    "reserves": 0.10,
}

_plan_generation_lock = threading.Lock()
_plan_generation_users: set[int] = set()


def _tier_is_budget(user: User) -> bool:
    return (user.tier or "budget").strip().lower() == "budget"


def _iso_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _score_result_from_row(row: HprsScore) -> dict[str, Any]:
    inputs_snapshot = row.inputs_snapshot if isinstance(row.inputs_snapshot, dict) else {}
    partial_data = inputs_snapshot.get("partial_data")
    if partial_data is None:
        partial_data = bool(inputs_snapshot.get("partial_data", False))

    commitment_context = get_commitment_pipeline_context(row.user_id, db.session)

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
            "active_layoff": False,
            "pipeline_credit": int(commitment_context.get("pipeline_credit") or 0),
            "commitment_type": commitment_context.get("commitment_type"),
        },
        "vehicle_risk": {
            "score": row.vehicle_risk_score,
            "band": row.vehicle_risk_band,
            "modifier": int(row.vehicle_modifier or 0),
            "verdict": None,
            "annual_repair_exposure": None,
        },
        "combined_modifier": int(row.combined_modifier or 0),
    }


def _plan_from_row(plan_row: HprsPlan | None) -> dict[str, Any] | None:
    if plan_row is None:
        return None

    steps = plan_row.action_steps
    if isinstance(steps, dict):
        plan = dict(steps)
        if not plan.get("summary") and plan_row.plan_summary:
            plan["summary"] = plan_row.plan_summary
        return plan

    return {
        "summary": plan_row.plan_summary or "",
        "score_band": "",
        "plan_phases": steps if isinstance(steps, list) else [],
        "monthly_actions": [],
        "quick_wins": [],
        "watch_flags": [],
        "projected_score": 0,
        "mortgage_estimate": {"monthly_piti": None, "front_end_dti": None},
    }


def _apply_tier_gating(plan: dict[str, Any] | None, user: User) -> dict[str, Any] | None:
    if plan is None:
        return None
    if not _tier_is_budget(user):
        return plan
    return {
        "summary": plan.get("summary"),
        "score_band": plan.get("score_band"),
    }


def _score_is_stale(row: HprsScore | None, now: datetime) -> bool:
    if row is None:
        return True
    return (now - row.computed_at) > timedelta(days=_SCORE_STALE_DAYS)


def _plan_is_stale(plan_row: HprsPlan | None, now: datetime) -> bool:
    if plan_row is None:
        return True
    return (now - plan_row.generated_at) > timedelta(days=_PLAN_STALE_DAYS)


def _start_plan_generation(app, user_id: int) -> bool:
    with _plan_generation_lock:
        if user_id in _plan_generation_users:
            return False
        _plan_generation_users.add(user_id)

    def _worker() -> None:
        try:
            with app.app_context():
                generate_hprs_plan(user_id)
        except Exception:
            logger.warning(
                "hprs readiness-score: background plan generation failed for user_id=%s",
                user_id,
                exc_info=True,
            )
        finally:
            with _plan_generation_lock:
                _plan_generation_users.discard(user_id)

    threading.Thread(target=_worker, daemon=True).start()
    return True


@hprs_bp.route("/readiness-score", methods=["GET"])
@require_auth
def get_readiness_score():
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    user_id = user.id
    now = datetime.utcnow()

    score_row = HprsScore.query.filter_by(user_id=user_id).first()
    if _score_is_stale(score_row, now):
        score_result = compute_full_hprs(user_id)
        if score_result.get("error"):
            return jsonify({"error": score_result["error"]}), 500
        score_row = HprsScore.query.filter_by(user_id=user_id).first()
    else:
        score_result = _score_result_from_row(score_row)

    plan_row = (
        HprsPlan.query.filter_by(user_id=user_id, is_active=True)
        .order_by(HprsPlan.generated_at.desc())
        .first()
    )

    plan_loading = False
    if _plan_is_stale(plan_row, now):
        started = _start_plan_generation(current_app._get_current_object(), user_id)
        if started or user_id in _plan_generation_users:
            plan_loading = True

    plan_body = _apply_tier_gating(_plan_from_row(plan_row), user)
    score_band = (plan_body or {}).get("score_band")

    if plan_row is not None:
        generated_at = _iso_timestamp(plan_row.generated_at)
        expires_at = _iso_timestamp(plan_row.generated_at + timedelta(days=_PLAN_STALE_DAYS))
    else:
        generated_at = score_result.get("computed_at")
        expires_at = None

    response_dict = {
        "score": score_result["overall_score"],
        "score_band": score_band,
        "readiness_tier": score_result["readiness_tier"],
        "overall_score": score_result["overall_score"],
        "partial_data": score_result["partial_data"],
        "pillars": score_result["pillars"],
        "career_risk": score_result["career_risk"],
        "vehicle_risk": score_result["vehicle_risk"],
        "combined_modifier": score_result["combined_modifier"],
        "plan": plan_body,
        "plan_loading": plan_loading,
        "generated_at": generated_at,
        "expires_at": expires_at,
    }

    # HPRS-13: surface latent nudge if one is pending
    latent_candidate = db.session.query(HprsLatentCandidate).filter(
        HprsLatentCandidate.user_id == user.id,
        HprsLatentCandidate.status == "nudged",
        HprsLatentCandidate.nudge_text.isnot(None),
        or_(
            HprsLatentCandidate.snoozed_until.is_(None),
            HprsLatentCandidate.snoozed_until < datetime.utcnow(),
        ),
    ).first()

    response_dict["latent_nudge"] = (
        {"body": latent_candidate.nudge_text} if latent_candidate else None
    )

    return jsonify(response_dict), 200
