#!/usr/bin/env python3
"""ICC side income recommendation API."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.services.side_income_accelerator import SideIncomeAccelerator

logger = logging.getLogger(__name__)

side_income_bp = Blueprint(
    "side_income",
    __name__,
    url_prefix="/api/independence-cost",
)


def _parse_positive_float(value, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be a number") from None
    if parsed <= 0:
        raise ValueError(f"{field} must be positive")
    return parsed


def _parse_positive_int(value, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be an integer") from None
    if parsed <= 0:
        raise ValueError(f"{field} must be positive")
    return parsed


@side_income_bp.route("/side-income-recommendations", methods=["POST"])
@require_auth
def side_income_recommendations():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    try:
        monthly_gap = _parse_positive_float(body.get("monthly_gap"), "monthly_gap")
        hours_per_week_available = _parse_positive_int(
            body.get("hours_per_week_available"),
            "hours_per_week_available",
        )
        startup_cost_needed = _parse_positive_float(
            body.get("startup_cost_needed"),
            "startup_cost_needed",
        )
        timeline_months = _parse_positive_int(body.get("timeline_months"), "timeline_months")
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400

    accelerator = SideIncomeAccelerator()
    try:
        payload = accelerator.get_side_income_recommendations(
            user_id,
            monthly_gap=monthly_gap,
            hours_per_week_available=hours_per_week_available,
            startup_cost_needed=startup_cost_needed,
            timeline_months=timeline_months,
        )
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception(
            "side income recommendations failed for user_id=%s: %s",
            user_id,
            exc,
        )
        return (
            jsonify(
                {
                    "error": "recommendation_failed",
                    "message": "Could not generate side income recommendations.",
                }
            ),
            500,
        )

    return jsonify(payload), 200
