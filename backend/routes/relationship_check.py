#!/usr/bin/env python3
"""In-app Relationship Check: writes vibe_person_assessments without a VibeCheckupsLead."""

from __future__ import annotations

import uuid
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from backend.auth.decorators import require_auth, require_csrf
from backend.middleware.limiter_ext import limiter
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vibe_tracker import VibePersonAssessment, VibeTrackedPerson

relationship_check_bp = Blueprint("relationship_check", __name__)

EMOTIONAL_QUESTIONS = frozenset({"emotional_availability", "conflict_style", "shared_values"})
FINANCIAL_QUESTIONS = frozenset({"income_transparency", "wiggle_room"})
EXPECTED_ANSWER_KEYS = EMOTIONAL_QUESTIONS | FINANCIAL_QUESTIONS


def _user_for_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _parse_json() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return uuid.UUID(str(value).strip())
    except (ValueError, TypeError, AttributeError):
        return None


def _verdict_from_avg(avg_score: float) -> tuple[str, str]:
    if avg_score >= 80:
        return "Strong", "💚"
    if avg_score >= 60:
        return "Healthy", "🌱"
    if avg_score >= 40:
        return "Mixed", "⚖️"
    if avg_score >= 20:
        return "Strained", "⚠️"
    return "Critical", "🚩"


def _validate_answers(raw: object) -> dict[str, int] | None:
    if not isinstance(raw, dict):
        return None
    out: dict[str, int] = {}
    for key in EXPECTED_ANSWER_KEYS:
        if key not in raw:
            return None
        val = raw[key]
        if not isinstance(val, int) or isinstance(val, bool):
            return None
        if val < 0 or val > 3:
            return None
        out[key] = val
    return out


@relationship_check_bp.route("/assessment", methods=["POST"])
@require_auth
@require_csrf
@limiter.limit("20 per minute")
def create_assessment():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    body = _parse_json()
    person_id = _parse_uuid(body.get("tracked_person_id"))
    if person_id is None:
        return jsonify({"error": "tracked_person_id must be a valid UUID"}), 400

    person = db.session.get(VibeTrackedPerson, person_id)
    if person is None:
        return jsonify({"error": "Person not found"}), 404
    if person.user_id != user.id:
        return jsonify({"error": "Forbidden"}), 403
    if person.is_archived:
        return jsonify({"error": "Person not found"}), 404

    answers = _validate_answers(body.get("answers"))
    if answers is None:
        return jsonify(
            {
                "error": "answers must include all five question keys with integer values 0–3",
            }
        ), 400

    emotional_raw = sum(answers[q] for q in EMOTIONAL_QUESTIONS)
    financial_raw = sum(answers[q] for q in FINANCIAL_QUESTIONS)
    emotional_score = int(round(emotional_raw * (100 / 9)))
    financial_score = int(round(financial_raw * (100 / 6)))
    avg_score = (emotional_score + financial_score) / 2
    verdict_label, verdict_emoji = _verdict_from_avg(avg_score)

    now = datetime.utcnow()
    assessment = VibePersonAssessment(
        tracked_person_id=person.id,
        lead_id=None,
        emotional_score=emotional_score,
        financial_score=financial_score,
        verdict_label=verdict_label,
        verdict_emoji=verdict_emoji,
        annual_projection=0,
        answers_snapshot={
            "source": "relationship_check",
            "answers": answers,
            "scored_at": now.isoformat(),
        },
        completed_at=now,
    )
    db.session.add(assessment)
    person.last_assessed_at = now
    person.assessment_count = (person.assessment_count or 0) + 1
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "assessment_id": str(assessment.id),
            "scores": {
                "emotional_score": emotional_score,
                "financial_score": financial_score,
                "verdict_label": verdict_label,
                "verdict_emoji": verdict_emoji,
            },
        }
    ), 200
