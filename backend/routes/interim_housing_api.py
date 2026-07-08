#!/usr/bin/env python3
"""Interim housing scenario API — roommate, family, and sublet alternatives."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.services.interim_housing_service import InterimHousingAnalyzer

logger = logging.getLogger(__name__)

interim_housing_bp = Blueprint(
    "interim_housing",
    __name__,
    url_prefix="/api/interim-housing",
)


def _parse_optional_float(value: str | None, field: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


@interim_housing_bp.route("/scenarios", methods=["GET"])
@require_auth
def scenarios():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    zip_code = (request.args.get("zip_code") or "").strip() or None
    try:
        startup_cost_needed = _parse_optional_float(
            request.args.get("startup_cost_needed"),
            "startup_cost_needed",
        )
        monthly_gap = _parse_optional_float(request.args.get("monthly_gap"), "monthly_gap")
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400

    analyzer = InterimHousingAnalyzer()
    try:
        payload = analyzer.analyze_interim_options(
            user_id,
            zip_code or "",
            startup_cost_needed,
            monthly_gap,
        )
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception("interim housing scenarios failed user_id=%s", user_id)
        return jsonify({"error": "analysis_failed", "message": str(exc)}), 500

    return jsonify(payload), 200
