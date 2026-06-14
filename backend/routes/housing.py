#!/usr/bin/env python3
"""Housing HPRS action endpoints — plan queue, nudge activation, snooze."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from flask import jsonify, request

from backend.auth.decorators import current_user, require_auth
from backend.models.database import db
from backend.models.gap_analysis import GapAnalysisResult
from backend.models.housing_profile import HousingProfile
from backend.models.hprs_latent_candidate import HprsLatentCandidate
from backend.models.user_models import User
from backend.routes.hprs import hprs_bp
from backend.services.action_plan_service import (
    ActionPlanGenerationError,
    generate_action_plan,
)
from backend.services.gap_analysis_service import compute_gap_analysis
from backend.tasks.hprs_tasks import generate_hprs_plan_task

_VALID_LOAN_TERMS = {10, 15, 20, 30}


def _to_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _gap_analysis_row_to_dict(row: GapAnalysisResult) -> dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "home_price": _to_float(row.home_price),
        "down_payment_pct": _to_float(row.down_payment_pct),
        "interest_rate": _to_float(row.interest_rate),
        "loan_term_years": row.loan_term_years,
        "timeline_months": row.timeline_months,
        "gap_income": _to_float(row.gap_income),
        "gap_savings_rate": _to_float(row.gap_savings_rate),
        "gap_down_payment": _to_float(row.gap_down_payment),
        "gap_dti": _to_float(row.gap_dti),
        "gap_credit": row.gap_credit,
        "income_severity": row.income_severity,
        "savings_severity": row.savings_severity,
        "down_payment_severity": row.down_payment_severity,
        "dti_severity": row.dti_severity,
        "credit_severity": row.credit_severity,
        "required_gross_income": _to_float(row.required_gross_income),
        "required_monthly_savings": _to_float(row.required_monthly_savings),
        "target_down_payment": _to_float(row.target_down_payment),
        "monthly_piti": _to_float(row.monthly_piti),
        "action_plan_json": row.action_plan_json,
        "plan_generated_at": (
            row.plan_generated_at.isoformat() if row.plan_generated_at else None
        ),
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
    }


def _validate_gap_analysis_payload(data: dict[str, Any]) -> str | None:
    home_price = data.get("home_price")
    down_payment_pct = data.get("down_payment_pct")
    interest_rate = data.get("interest_rate")
    loan_term_years = data.get("loan_term_years")
    timeline_months = data.get("timeline_months")

    try:
        home_price_f = float(home_price)
        down_payment_pct_f = float(down_payment_pct)
        interest_rate_f = float(interest_rate)
        loan_term_years_i = int(loan_term_years)
        timeline_months_i = int(timeline_months)
    except (TypeError, ValueError):
        return "all fields must be numeric"

    if home_price_f <= 0:
        return "home_price must be greater than 0"
    if not (0 < down_payment_pct_f <= 1):
        return "down_payment_pct must be between 0 and 1"
    if not (0 < interest_rate_f < 1):
        return "interest_rate must be between 0 and 1"
    if loan_term_years_i not in _VALID_LOAN_TERMS:
        return "loan_term_years must be one of 10, 15, 20, 30"
    if not (12 <= timeline_months_i <= 360):
        return "timeline_months must be between 12 and 360"
    return None


@hprs_bp.route("/gap-analysis", methods=["POST"])
@require_auth
def create_gap_analysis():
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    validation_error = _validate_gap_analysis_payload(data)
    if validation_error:
        return jsonify({"error": "validation_error", "message": validation_error}), 400

    result = compute_gap_analysis(
        user_id=user.id,
        home_price=float(data["home_price"]),
        down_payment_pct=float(data["down_payment_pct"]),
        interest_rate=float(data["interest_rate"]),
        loan_term_years=int(data["loan_term_years"]),
        timeline_months=int(data["timeline_months"]),
    )
    return jsonify(result), 200


@hprs_bp.route("/gap-analysis/<int:gap_analysis_id>", methods=["GET"])
@require_auth
def get_gap_analysis(gap_analysis_id: int):
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    row = GapAnalysisResult.query.get(gap_analysis_id)
    if row is None or row.user_id != user.id:
        return jsonify({"error": "not_found"}), 404

    return jsonify(_gap_analysis_row_to_dict(row)), 200


@hprs_bp.route("/action-plan", methods=["POST"])
@require_auth
def create_action_plan():
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    gap_analysis_id = data.get("gap_analysis_id")
    if gap_analysis_id is None:
        return jsonify({"error": "validation_error", "message": "gap_analysis_id is required"}), 400

    try:
        gap_analysis_id_int = int(gap_analysis_id)
    except (TypeError, ValueError):
        return jsonify({"error": "validation_error", "message": "gap_analysis_id must be an integer"}), 400

    row = GapAnalysisResult.query.get(gap_analysis_id_int)
    if row is None or row.user_id != user.id:
        return jsonify({"error": "not_found"}), 404

    now = datetime.utcnow()
    if (
        row.action_plan_json is not None
        and row.expires_at is not None
        and row.expires_at > now
    ):
        return jsonify({"plan": row.action_plan_json, "cached": True}), 200

    try:
        plan_json = generate_action_plan(gap_analysis_id_int, user.id)
    except ValueError:
        return jsonify({"error": "not_found"}), 404
    except ActionPlanGenerationError:
        return jsonify({"error": "Plan generation failed. Try again in a moment."}), 500

    return jsonify({"plan": plan_json, "cached": False}), 200


@hprs_bp.route("/hprs/queue-generation", methods=["POST"])
@require_auth
def queue_hprs_generation():
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    profile = HousingProfile.query.filter_by(user_id=user.id).first()
    if profile is None or not profile.has_buy_goal:
        return jsonify({"error": "buy_goal_required"}), 400

    generate_hprs_plan_task.delay(user.id)
    return jsonify({"queued": True}), 202


@hprs_bp.route("/hprs/activate-from-nudge", methods=["POST"])
@require_auth
def activate_from_nudge():
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    now = datetime.utcnow()
    profile = HousingProfile.query.filter_by(user_id=user.id).first()
    if profile is None:
        profile = HousingProfile(
            user_id=user.id,
            housing_type="rent",
            monthly_cost=0.0,
            zip_or_city="",
        )
        db.session.add(profile)

    profile.has_buy_goal = True
    if profile.target_timeline_months is None:
        profile.target_timeline_months = 24

    candidate = HprsLatentCandidate.query.filter_by(user_id=user.id).first()
    if candidate is None:
        candidate = HprsLatentCandidate(user_id=user.id, first_evaluated_at=now)
        db.session.add(candidate)

    candidate.status = "activated"
    candidate.user_engaged_at = now
    candidate.activated_at = now
    candidate.last_evaluated_at = now

    db.session.commit()
    generate_hprs_plan_task.delay(user.id)
    return jsonify({"activated": True, "plan_queued": True}), 200


@hprs_bp.route("/hprs/snooze-nudge", methods=["POST"])
@require_auth
def snooze_nudge():
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    now = datetime.utcnow()
    until = now + timedelta(days=90)

    candidate = HprsLatentCandidate.query.filter_by(user_id=user.id).first()
    if candidate is None:
        candidate = HprsLatentCandidate(user_id=user.id, first_evaluated_at=now)
        db.session.add(candidate)

    candidate.snoozed_until = until
    candidate.status = "snoozed"
    candidate.last_evaluated_at = now
    db.session.commit()

    return jsonify({"snoozed": True, "until": until.isoformat()}), 200
