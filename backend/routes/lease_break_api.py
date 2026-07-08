#!/usr/bin/env python3
"""Lease break analysis API."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.services.lease_break_service import LeaseBreakAnalyzer

logger = logging.getLogger(__name__)

lease_break_bp = Blueprint("lease_break", __name__, url_prefix="/api/lease-break")


def _parse_positive_int(value, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer") from exc
    if parsed <= 0:
        raise ValueError(f"{field} must be a positive integer")
    return parsed


def _parse_positive_float(value, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive number") from exc
    if parsed <= 0:
        raise ValueError(f"{field} must be a positive number")
    return parsed


@lease_break_bp.route("/analyze", methods=["POST"])
@require_auth
def analyze():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    try:
        months_remaining = _parse_positive_int(body.get("months_remaining"), "months_remaining")
        monthly_rent = _parse_positive_float(body.get("monthly_rent"), "monthly_rent")
        break_fee_raw = body.get("break_fee_percent", 1.5)
        break_fee_percent = float(break_fee_raw)
        if break_fee_percent < 0:
            raise ValueError("break_fee_percent must be non-negative")
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400

    analyzer = LeaseBreakAnalyzer()
    try:
        payload = analyzer.analyze_break_cost(
            user_id,
            months_remaining,
            monthly_rent,
            break_fee_percent=break_fee_percent,
        )
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception("lease break analyze failed user_id=%s", user_id)
        return jsonify({"error": "analysis_failed", "message": str(exc)}), 500

    return jsonify(payload), 200
