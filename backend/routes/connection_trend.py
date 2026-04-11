#!/usr/bin/env python3
"""Connection Trend API: observation questions, assessments, history."""

from __future__ import annotations

import uuid
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from backend.auth.decorators import require_auth, require_csrf
from backend.middleware.limiter_ext import limiter
from backend.models.connection_trend import ConnectionTrendAssessment
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vibe_tracker import VibeTrackedPerson
from backend.services.connection_trend_service import (
    compute_fade_tier,
    compute_pattern_type,
    get_pattern_insight,
)

connection_trend_bp = Blueprint("connection_trend", __name__)

_STATIC_QUESTIONS = [
    {
        "id": "q1",
        "key": "q1_response_pattern",
        "text": (
            "When you reach out, how quickly are they getting back to you?"
        ),
        "answers": [
            "Faster or more engaged than before",
            "About the same",
            "Slower or less often",
        ],
    },
    {
        "id": "q2",
        "key": "q2_initiative",
        "text": "Who's been making plans or suggesting things to do lately?",
        "answers": [
            "Mostly them, or it's pretty balanced",
            "It varies — hard to say",
            "Mostly me",
        ],
    },
    {
        "id": "q3",
        "key": "q3_followthrough",
        "text": "When plans are made, do they happen?",
        "answers": [
            "Yes, reliably",
            "Sometimes — a few cancellations",
            "Plans have been falling through more than usual",
        ],
    },
    {
        "id": "q4",
        "key": "q4_future_talk",
        "text": (
            "Are they talking about things you two might do together down the road?"
        ),
        "answers": [
            "Yes — making future references or plans",
            "Not really, but it feels normal for them",
            "Less than before — conversations feel more present-only",
        ],
    },
    {
        "id": "q5",
        "key": "q5_social_visibility",
        "text": (
            "Have you met or been around their people — friends, family, coworkers?"
        ),
        "answers": [
            "Yes, or it feels like it's moving naturally",
            "Not yet, but it's still early",
            (
                "I've been around them but haven't been introduced, "
                "or it's been avoided"
            ),
        ],
    },
    {
        "id": "q6",
        "key": "q6_reciprocity",
        "text": "How does the effort feel — who's putting more in right now?",
        "answers": [
            "It feels mutual",
            "Slightly uneven but not a concern",
            "I'm clearly putting in more right now",
        ],
    },
    {
        "id": "q7",
        "key": "q7_gut_signal",
        "text": (
            "Does something feel off that you haven't been able to name yet?"
        ),
        "answers": [
            "No — things feel solid",
            "Maybe — I've had a thought or two",
            "Yes — something feels different",
        ],
    },
]

_Q_KEYS = [f"q{i}" for i in range(1, 8)]


def _user_for_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _parse_json() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _person_for_user(person_id: uuid.UUID, user: User) -> VibeTrackedPerson | None:
    p = db.session.get(VibeTrackedPerson, person_id)
    if not p or p.user_id != user.id:
        return None
    return p


def _assessment_dict(row: ConnectionTrendAssessment) -> dict:
    insight = get_pattern_insight(row.pattern_type, row.fade_tier)
    return {
        "id": str(row.id),
        "user_id": row.user_id,
        "person_id": str(row.person_id),
        "assessed_at": row.assessed_at.isoformat() + "Z"
        if row.assessed_at
        else None,
        "q1_response_pattern": row.q1_response_pattern,
        "q2_initiative": row.q2_initiative,
        "q3_followthrough": row.q3_followthrough,
        "q4_future_talk": row.q4_future_talk,
        "q5_social_visibility": row.q5_social_visibility,
        "q6_reciprocity": row.q6_reciprocity,
        "q7_gut_signal": row.q7_gut_signal,
        "raw_score": row.raw_score,
        "normalized_score": row.normalized_score,
        "fade_tier": row.fade_tier,
        "pattern_type": row.pattern_type,
        "pattern_insight": insight,
    }


@connection_trend_bp.route("/questions", methods=["GET"])
@require_auth
def get_questions():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"questions": _STATIC_QUESTIONS})


@connection_trend_bp.route("/people/<uuid:person_id>/assess", methods=["POST"])
@require_auth
@require_csrf
@limiter.limit("30 per minute")
def post_assess(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    person = _person_for_user(person_id, user)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    body = _parse_json()
    values: list[int] = []
    for k in _Q_KEYS:
        if k not in body:
            return jsonify({"error": f"{k} is required (0, 1, or 2)"}), 400
        v = body.get(k)
        if isinstance(v, bool) or not isinstance(v, int):
            return jsonify({"error": f"{k} must be an integer 0–2"}), 400
        if v not in (0, 1, 2):
            return jsonify({"error": f"{k} must be 0, 1, or 2"}), 400
        values.append(v)

    raw_score = sum(values)
    normalized_score = int(round(raw_score / 14.0 * 100.0))
    fade_tier = compute_fade_tier(normalized_score)
    pattern_type = compute_pattern_type(*values)

    row = ConnectionTrendAssessment(
        user_id=user.id,
        person_id=person.id,
        assessed_at=datetime.utcnow(),
        q1_response_pattern=values[0],
        q2_initiative=values[1],
        q3_followthrough=values[2],
        q4_future_talk=values[3],
        q5_social_visibility=values[4],
        q6_reciprocity=values[5],
        q7_gut_signal=values[6],
        raw_score=raw_score,
        normalized_score=normalized_score,
        fade_tier=fade_tier,
        pattern_type=pattern_type,
    )
    db.session.add(row)
    db.session.commit()

    return jsonify({"assessment": _assessment_dict(row)}), 201


@connection_trend_bp.route("/people/<uuid:person_id>/history", methods=["GET"])
@require_auth
def get_history(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    person = _person_for_user(person_id, user)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    rows = (
        ConnectionTrendAssessment.query.filter_by(
            user_id=user.id,
            person_id=person.id,
        )
        .order_by(ConnectionTrendAssessment.assessed_at.desc())
        .all()
    )
    return jsonify({"assessments": [_assessment_dict(r) for r in rows]})


@connection_trend_bp.route("/people/<uuid:person_id>/latest", methods=["GET"])
@require_auth
def get_latest(person_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    person = _person_for_user(person_id, user)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    row = (
        ConnectionTrendAssessment.query.filter_by(
            user_id=user.id,
            person_id=person.id,
        )
        .order_by(ConnectionTrendAssessment.assessed_at.desc())
        .first()
    )
    if not row:
        return jsonify({"assessment": None})
    return jsonify({"assessment": _assessment_dict(row)})
