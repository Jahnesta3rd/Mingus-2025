#!/usr/bin/env python3
"""
Checkup hub partial-write endpoints (#170).

Mind-mood and spirit-calm fields upsert into WeeklyCheckin for the current week.
Extended fields not yet on the ORM model are stored in wins JSON under _checkup_hub.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from flask import Blueprint, jsonify, request
from marshmallow import Schema, ValidationError, fields, validate

from backend.auth.decorators import require_auth, get_current_user_id
from backend.models.database import db
from backend.models.user_models import User
from backend.models.wellness import WeeklyCheckin
from backend.services.wellness_score_service import WellnessScoreCalculator

checkups_hub_bp = Blueprint("checkups_hub", __name__, url_prefix="/api/checkups")


def _resolve_user_id() -> int:
    uid = get_current_user_id()
    if uid is None:
        raise ValueError("Authentication required")
    if isinstance(uid, int):
        return uid
    user = User.query.filter_by(user_id=str(uid)).first()
    if user is None:
        user = User.query.get(uid)
    if user is None:
        raise ValueError("User not found")
    return user.id


def _week_ending_today():
    return WellnessScoreCalculator.get_week_ending_date(datetime.utcnow().date())


def _load_hub_meta(checkin: WeeklyCheckin | None) -> dict[str, Any]:
    if checkin is None or not checkin.wins:
        return {}
    try:
        parsed = json.loads(checkin.wins)
        if isinstance(parsed, dict):
            hub = parsed.get("_checkup_hub")
            if isinstance(hub, dict):
                return hub
    except (json.JSONDecodeError, TypeError):
        pass
    return {}


def _merge_hub_meta(checkin: WeeklyCheckin, patch: dict[str, Any]) -> None:
    base: dict[str, Any] = {}
    if checkin.wins:
        try:
            parsed = json.loads(checkin.wins)
            if isinstance(parsed, dict):
                base = parsed
        except (json.JSONDecodeError, TypeError):
            base = {"_legacy_wins": checkin.wins}
    hub = base.get("_checkup_hub")
    if not isinstance(hub, dict):
        hub = {}
    hub.update(patch)
    base["_checkup_hub"] = hub
    checkin.wins = json.dumps(base)


def _get_or_create_weekly(user_id: int, week_ending) -> WeeklyCheckin:
    row = WeeklyCheckin.query.filter_by(
        user_id=user_id, week_ending_date=week_ending
    ).first()
    if row is None:
        row = WeeklyCheckin(user_id=user_id, week_ending_date=week_ending)
        db.session.add(row)
        db.session.flush()
    return row


class MindMoodSchema(Schema):
    mood_rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    stress_level = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    mood_stress_triggered_purchase = fields.String(
        required=True, validate=validate.OneOf(["yes", "no", "unsure"])
    )
    mood_avoided_finances = fields.Boolean(required=True)
    mood_coping_methods = fields.List(fields.String(), required=True)
    spending_intentionality_rating = fields.Integer(
        required=True, validate=validate.Range(min=1, max=5)
    )


class SpiritCalmSchema(Schema):
    practice_felt_grounding = fields.Boolean(required=True)
    meditation_minutes_total = fields.Integer(
        required=True, validate=validate.Range(min=0, max=999)
    )


@checkups_hub_bp.route("/mind-mood", methods=["POST"])
@require_auth
def submit_mind_mood():
    """Partial upsert of mind/mood fields into WeeklyCheckin for the current week."""
    if not request.is_json:
        return jsonify({"error": "JSON body required"}), 400
    try:
        data = MindMoodSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation error", "messages": e.messages}), 400

    try:
        user_id = _resolve_user_id()
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    week_ending = _week_ending_today()
    checkin = _get_or_create_weekly(user_id, week_ending)

    checkin.overall_mood = data["mood_rating"]
    checkin.stress_level = data["stress_level"]
    checkin.spending_control = data["spending_intentionality_rating"]

    _merge_hub_meta(
        checkin,
        {
            "mood_stress_triggered_purchase": data["mood_stress_triggered_purchase"],
            "mood_avoided_finances": data["mood_avoided_finances"],
            "mood_coping_methods": data["mood_coping_methods"],
            "mood_rating": data["mood_rating"],
            "spending_intentionality_rating": data["spending_intentionality_rating"],
        },
    )

    if checkin.completed_at is None:
        checkin.completed_at = datetime.utcnow()

    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "week_ending_date": week_ending.isoformat(),
            "completed_at": checkin.completed_at.isoformat() if checkin.completed_at else None,
        }
    )


@checkups_hub_bp.route("/spirit-calm", methods=["POST"])
@require_auth
def submit_spirit_calm():
    """Upsert spirit supplement fields into WeeklyCheckin for the current week."""
    if not request.is_json:
        return jsonify({"error": "JSON body required"}), 400
    try:
        data = SpiritCalmSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation error", "messages": e.messages}), 400

    try:
        user_id = _resolve_user_id()
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    week_ending = _week_ending_today()
    checkin = _get_or_create_weekly(user_id, week_ending)

    checkin.meditation_minutes = data["meditation_minutes_total"]
    _merge_hub_meta(
        checkin,
        {
            "practice_felt_grounding": data["practice_felt_grounding"],
            "meditation_minutes_total": data["meditation_minutes_total"],
        },
    )

    if checkin.completed_at is None:
        checkin.completed_at = datetime.utcnow()

    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "week_ending_date": week_ending.isoformat(),
            "meditation_minutes_total": data["meditation_minutes_total"],
            "practice_felt_grounding": data["practice_felt_grounding"],
        }
    )
