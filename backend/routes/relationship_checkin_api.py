#!/usr/bin/env python3
"""Relationship milestone monthly check-in API."""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.services.relationship_milestone_service import RelationshipMilestoneChecker

logger = logging.getLogger(__name__)

relationship_checkin_bp = Blueprint(
    "relationship_checkin",
    __name__,
    url_prefix="/api/relationship-checkin",
)


def _parse_person_id(raw: str | None) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(str(raw).strip())
    except (TypeError, ValueError, AttributeError):
        return None


@relationship_checkin_bp.route("/assess", methods=["POST"])
@require_auth
def assess():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    person_id = _parse_person_id(body.get("person_id"))
    if person_id is None:
        return jsonify({"error": "invalid_input", "message": "person_id is required"}), 400

    responses = {
        "vibe_trend": body.get("vibe_trend"),
        "feels_safe": body.get("feels_safe"),
        "needs_to_leave_sooner": body.get("needs_to_leave_sooner"),
        "on_track_savings": body.get("on_track_savings"),
        "prefer_leave_now": body.get("prefer_leave_now"),
        "emergency_signals": body.get("emergency_signals"),
    }

    checker = RelationshipMilestoneChecker()
    try:
        payload = checker.monthly_readiness_check(user_id, person_id, responses)
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": "not_found", "message": str(exc)}), 404
    except Exception as exc:
        logger.exception("relationship checkin assess failed user_id=%s", user_id)
        return jsonify({"error": "assessment_failed", "message": str(exc)}), 500

    return jsonify(payload), 200


@relationship_checkin_bp.route("/quarterly-reassessment", methods=["GET"])
@require_auth
def quarterly_reassessment():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    person_id = _parse_person_id(request.args.get("person_id"))
    if person_id is None:
        return jsonify({"error": "invalid_input", "message": "person_id is required"}), 400

    checker = RelationshipMilestoneChecker()
    try:
        payload = checker.quarterly_reassessment(user_id, person_id)
    except LookupError as exc:
        return jsonify({"error": "not_found", "message": str(exc)}), 404
    except Exception as exc:
        logger.exception(
            "quarterly reassessment failed user_id=%s person_id=%s",
            user_id,
            person_id,
        )
        return jsonify({"error": "reassessment_failed", "message": str(exc)}), 500

    return jsonify(payload), 200
