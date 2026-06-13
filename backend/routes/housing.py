#!/usr/bin/env python3
"""Housing HPRS action endpoints — plan queue, nudge activation, snooze."""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import jsonify

from backend.auth.decorators import current_user, require_auth
from backend.models.database import db
from backend.models.housing_profile import HousingProfile
from backend.models.user_models import User
from backend.routes.hprs import hprs_bp
from backend.tasks.hprs_tasks import generate_hprs_plan_task


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
