#!/usr/bin/env python3
"""Relationship intelligence API — ephemeral LLM narratives (tier-gated)."""

from __future__ import annotations

import uuid

from flask import Blueprint, g, jsonify, request

from backend.auth.decorators import require_auth
from backend.models.user_models import User
from backend.models.vibe_tracker import VibeTrackedPerson
from backend.services.relationship_intelligence_service import (
    generate_cost_narrative,
    generate_relationship_narrative,
    generate_roster_insight,
    generate_stay_or_go,
)

rel_intel_api = Blueprint(
    "rel_intel_api",
    __name__,
    url_prefix="/api/relationship-intelligence",
)


def _current_user() -> tuple[User | None, tuple]:
    user = User.query.filter_by(user_id=str(g.current_user_id)).first()
    if not user:
        return None, (jsonify({"error": "User not found"}), 404)
    return user, None


def _tier_is_budget(user: User) -> bool:
    return (user.tier or "budget").strip().lower() == "budget"


def _person_for_user(user: User, person_id: str) -> VibeTrackedPerson | None:
    try:
        pid = uuid.UUID(str(person_id).strip())
    except (ValueError, TypeError, AttributeError):
        return None
    return VibeTrackedPerson.query.filter_by(id=pid, user_id=user.id).first()


@rel_intel_api.route("/narrative", methods=["POST"])
@require_auth
def post_narrative():
    user, err = _current_user()
    if err:
        return err

    if _tier_is_budget(user):
        return (
            jsonify(
                {
                    "error": "forbidden",
                    "message": "Relationship intelligence is available on Mid-tier and above.",
                }
            ),
            403,
        )

    body = request.get_json(silent=True) or {}
    person_id = body.get("person_id")
    if not person_id or not isinstance(person_id, str):
        return jsonify({"error": "person_id is required"}), 400

    person_id = person_id.strip()
    person = _person_for_user(user, person_id)
    if not person:
        return jsonify({"error": "Person not found"}), 404

    if person.llm_opt_out:
        return jsonify({"person_id": person_id, "opted_out": True}), 200

    ext_user_id = str(user.user_id)
    narrative = generate_relationship_narrative(ext_user_id, person_id)
    stay_or_go = generate_stay_or_go(ext_user_id, person_id)
    cost = generate_cost_narrative(ext_user_id, person_id)

    response: dict = {"person_id": person_id}
    if narrative:
        response["narrative"] = narrative["narrative"]
    if stay_or_go:
        response["stay_or_go"] = {
            "direction": stay_or_go["direction"],
            "explanation": stay_or_go["explanation"],
        }
    if cost:
        response["cost_narrative"] = cost["cost_narrative"]

    return jsonify(response), 200


@rel_intel_api.route("/roster-insight", methods=["POST"])
@require_auth
def post_roster_insight():
    user, err = _current_user()
    if err:
        return err

    if _tier_is_budget(user):
        return (
            jsonify(
                {
                    "error": "forbidden",
                    "message": "Relationship intelligence is available on Mid-tier and above.",
                }
            ),
            403,
        )

    result = generate_roster_insight(str(user.user_id))
    if not result:
        return jsonify({"insufficient_data": True}), 200

    return (
        jsonify(
            {
                "insight": result["insight"],
                "person_count": result["person_count"],
            }
        ),
        200,
    )
