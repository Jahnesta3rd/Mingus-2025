#!/usr/bin/env python3
"""Life Ledger profile and insights API."""

from __future__ import annotations

import uuid
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from backend.auth.decorators import require_auth
from backend.models.database import db
from backend.models.life_ledger import LifeLedgerInsight, LifeLedgerModuleAnswer
from backend.models.user_models import User
from backend.services import life_ledger_service as lls
from backend.services import body_check_service as bcs
from backend.services import roof_check_service as rcs
from backend.services import vehicle_check_service as vcs
from backend.tasks.life_correlation_tasks import record_life_snapshot

life_ledger_bp = Blueprint("life_ledger", __name__)

_MODULES = frozenset({"vibe", "body", "roof", "vehicle"})
_SCORE_ATTR = {
    "vibe": "vibe_score",
    "body": "body_score",
    "roof": "roof_score",
    "vehicle": "vehicle_score",
}
_PROJECTION_ATTR = {
    "vibe": "vibe_annual_projection",
    "body": "body_health_cost_projection",
    "roof": "roof_housing_wealth_gap",
    "vehicle": "vehicle_annual_maintenance",
}


def _user_from_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


@life_ledger_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    profile = lls.get_or_create_profile(user.id)
    db.session.flush()
    insights = lls.sync_insights_for_user(user.id, profile)
    db.session.commit()
    return jsonify(lls.profile_to_dict(profile, insights))


@life_ledger_bp.route("/profile", methods=["POST"])
@require_auth
def update_profile():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    module = data.get("module")
    if module not in _MODULES:
        return jsonify({"error": "module must be one of: vibe, body, roof, vehicle"}), 400

    score = data.get("score")
    if not isinstance(score, int) or score < 0 or score > 100:
        return jsonify({"error": "score must be an integer 0–100"}), 400

    profile = lls.get_or_create_profile(user.id)
    setattr(profile, _SCORE_ATTR[module], score)

    if "projection" in data and data["projection"] is not None:
        proj = data["projection"]
        if not isinstance(proj, int):
            return jsonify({"error": "projection must be an integer"}), 400
        setattr(profile, _PROJECTION_ATTR[module], proj)

    answers = data.get("answers")
    if answers is not None:
        if not isinstance(answers, dict):
            return jsonify({"error": "answers must be an object"}), 400
        row = LifeLedgerModuleAnswer(
            user_id=user.id,
            module=module,
            answers=answers,
            completed_at=datetime.utcnow(),
            score=score,
        )
        db.session.add(row)

    profile.life_ledger_score = lls.compute_life_ledger_score(profile)
    db.session.flush()
    insights = lls.sync_insights_for_user(user.id, profile)
    db.session.commit()
    record_life_snapshot.delay(str(user.id), "profile_update")
    return jsonify(lls.profile_to_dict(profile, insights))


@life_ledger_bp.route("/body-check/submit", methods=["POST"])
@require_auth
def submit_body_check():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    raw_answers = data.get("answers")
    if not isinstance(raw_answers, dict):
        return jsonify({"error": "answers object required"}), 400

    try:
        answers = bcs.normalize_body_check_answers(raw_answers)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    body_score = bcs.calculate_body_score(answers)
    health_cost_projection = bcs.calculate_health_cost_projection(body_score)
    productivity_impact = bcs.calculate_productivity_impact(body_score)

    profile = lls.get_or_create_profile(user.id)
    profile.body_score = body_score
    profile.body_health_cost_projection = health_cost_projection
    profile.life_ledger_score = lls.compute_life_ledger_score(profile)

    row = LifeLedgerModuleAnswer(
        user_id=user.id,
        module="body",
        answers=answers,
        completed_at=datetime.utcnow(),
        score=body_score,
    )
    db.session.add(row)

    db.session.flush()
    insights = lls.sync_insights_for_user(user.id, profile)
    db.session.commit()
    record_life_snapshot.delay(str(user.id), "body_update")

    return jsonify(
        {
            "body_score": body_score,
            "health_cost_projection": health_cost_projection,
            "productivity_impact": productivity_impact,
            "insights": insights,
        }
    )


@life_ledger_bp.route("/roof-check/submit", methods=["POST"])
@require_auth
def submit_roof_check():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    raw_answers = data.get("answers")
    if not isinstance(raw_answers, dict):
        return jsonify({"error": "answers object required"}), 400

    try:
        answers = rcs.normalize_roof_check_answers(raw_answers)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    roof_score = rcs.calculate_roof_score(answers)
    housing_wealth_gap = rcs.calculate_housing_wealth_gap(answers, roof_score)
    annual_gap = int(housing_wealth_gap["annual_wealth_gap"])

    profile = lls.get_or_create_profile(user.id)
    profile.roof_score = roof_score
    profile.roof_housing_wealth_gap = annual_gap
    profile.life_ledger_score = lls.compute_life_ledger_score(profile)

    row = LifeLedgerModuleAnswer(
        user_id=user.id,
        module="roof",
        answers=answers,
        completed_at=datetime.utcnow(),
        score=roof_score,
    )
    db.session.add(row)

    db.session.flush()
    insights = lls.sync_insights_for_user(user.id, profile)
    db.session.commit()
    record_life_snapshot.delay(str(user.id), "roof_update")

    return jsonify(
        {
            "roof_score": roof_score,
            "housing_wealth_gap": housing_wealth_gap,
            "verdict": housing_wealth_gap["verdict"],
            "insights": insights,
        }
    )


@life_ledger_bp.route("/vehicle-check/submit", methods=["POST"])
@require_auth
def submit_vehicle_check():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    raw_answers = data.get("answers")
    if not isinstance(raw_answers, dict):
        return jsonify({"error": "answers object required"}), 400

    try:
        answers = vcs.normalize_vehicle_check_answers(raw_answers)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    vehicle_score = vcs.calculate_vehicle_score(answers)
    annual_maintenance = vcs.calculate_annual_maintenance(answers, vehicle_score)
    annual_cost = int(annual_maintenance["annual_cost"])

    profile = lls.get_or_create_profile(user.id)
    profile.vehicle_score = vehicle_score
    profile.vehicle_annual_maintenance = annual_cost
    profile.life_ledger_score = lls.compute_life_ledger_score(profile)

    row = LifeLedgerModuleAnswer(
        user_id=user.id,
        module="vehicle",
        answers=answers,
        completed_at=datetime.utcnow(),
        score=vehicle_score,
    )
    db.session.add(row)

    vcs.ensure_placeholder_vehicle_from_assessment(user.id, answers, annual_cost)

    db.session.flush()
    insights = lls.sync_insights_for_user(user.id, profile)
    db.session.commit()
    record_life_snapshot.delay(str(user.id), "vehicle_update")

    return jsonify(
        {
            "vehicle_score": vehicle_score,
            "annual_maintenance": annual_maintenance,
            "risk_level": annual_maintenance["risk_level"],
            "top_risks": annual_maintenance["top_risks"],
            "insights": insights,
        }
    )


@life_ledger_bp.route("/dismiss-insight/<uuid:insight_id>", methods=["POST"])
@require_auth
def dismiss_insight(insight_id: uuid.UUID):
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    row = LifeLedgerInsight.query.filter_by(id=insight_id, user_id=user.id).first()
    if not row:
        return jsonify({"error": "Insight not found"}), 404
    row.dismissed = True
    db.session.commit()
    return jsonify({"ok": True})
