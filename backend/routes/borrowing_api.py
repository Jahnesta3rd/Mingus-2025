#!/usr/bin/env python3
"""Borrowing scenarios API — analysis-only with hard safety rules."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.services.borrowing_scenarios_service import BorrowingScenarios

logger = logging.getLogger(__name__)

borrowing_bp = Blueprint("borrowing", __name__, url_prefix="/api/borrowing")

_VALID_REASONS = frozenset(
    {
        "bridge_startup",
        "relationship_unsafe",
        "accelerate_timeline",
        "emergency_move",
        "general",
    }
)


def _parse_non_negative_float(value, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


@borrowing_bp.route("/analyze", methods=["POST"])
@require_auth
def analyze():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    try:
        amount_needed = _parse_non_negative_float(body.get("amount_needed"), "amount_needed")
        monthly_income = _parse_non_negative_float(body.get("monthly_income"), "monthly_income")
        side_income = _parse_non_negative_float(body.get("side_income", 0), "side_income")
        borrowing_reason = str(body.get("borrowing_reason") or "bridge_startup").strip().lower()
        if borrowing_reason not in _VALID_REASONS:
            raise ValueError(
                f"borrowing_reason must be one of: {', '.join(sorted(_VALID_REASONS))}"
            )
        relationship_unsafe = bool(body.get("relationship_unsafe"))
        income_stable = bool(body.get("income_stable", True))
        accelerate_timeline = bool(body.get("accelerate_timeline")) or borrowing_reason == "accelerate_timeline"
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400

    service = BorrowingScenarios()
    try:
        payload = service.analyze_borrowing_options(
            user_id,
            amount_needed,
            monthly_income,
            side_income,
            borrowing_reason=borrowing_reason,
            relationship_unsafe=relationship_unsafe,
            income_stable=income_stable,
            accelerate_timeline=accelerate_timeline,
        )
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception("borrowing analyze failed user_id=%s", user_id)
        return jsonify({"error": "analysis_failed", "message": str(exc)}), 500

    return jsonify(payload), 200
