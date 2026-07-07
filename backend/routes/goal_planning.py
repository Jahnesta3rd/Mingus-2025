#!/usr/bin/env python3
"""Goal planning API — server-side analysis with secure Claude access."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from backend.auth.decorators import require_auth, require_csrf
from backend.services.goal_planning_service import (
    GoalPlanningServiceError,
    run_goal_planning_analyze,
)

logger = logging.getLogger(__name__)

goal_planning_bp = Blueprint(
    "goal_planning", __name__, url_prefix="/api/goal-planning"
)


@goal_planning_bp.route("/analyze", methods=["POST"])
@require_auth
@require_csrf
def analyze_goal_planning():
    """Analyze a financial goal and return recommendations + enrichment."""

    body = request.get_json(silent=True) or {}
    goal = body.get("goal")
    user_profile = body.get("userProfile")

    try:
        result = run_goal_planning_analyze(goal, user_profile)
    except GoalPlanningServiceError as exc:
        return jsonify({"error": "analysis_failed", "message": str(exc)}), 400
    except Exception:
        logger.exception("Unexpected goal planning analysis failure")
        return jsonify({
            "error": "analysis_failed",
            "message": "Unable to analyze goal. Please try again.",
        }), 500

    return jsonify(result), 200
