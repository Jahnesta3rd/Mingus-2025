#!/usr/bin/env python3
"""Phased independence timeline API — tiered move-out planning."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.models.independence_cost_assessment import IndependenceCostAssessment
from backend.services.phased_independence_service import PhasedIndependencePlanner

logger = logging.getLogger(__name__)

phased_independence_bp = Blueprint(
    "phased_independence",
    __name__,
    url_prefix="/api/phased-independence",
)


def _parse_float(value: str | None, field: str, default: float | None = None) -> float:
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"{field} is required")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc
    if parsed < 0:
        raise ValueError(f"{field} must be non-negative")
    return parsed


@phased_independence_bp.route("/timeline", methods=["GET"])
@require_auth
def timeline():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    try:
        total_gap = _parse_float(request.args.get("total_gap"), "total_gap")
        monthly_savings = _parse_float(
            request.args.get("monthly_savings"),
            "monthly_savings",
            default=0.0,
        )
        startup_full_raw = request.args.get("startup_cost_full")
        startup_cost_full = (
            _parse_float(startup_full_raw, "startup_cost_full")
            if startup_full_raw not in (None, "")
            else None
        )
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400

    if startup_cost_full is None:
        latest = (
            IndependenceCostAssessment.query.filter_by(user_id=user_id)
            .order_by(IndependenceCostAssessment.created_at.desc())
            .first()
        )
        if latest and latest.total_startup_cost is not None:
            startup_cost_full = float(latest.total_startup_cost)
        if total_gap == 0 and latest and latest.monthly_independence_gap is not None:
            total_gap = float(latest.monthly_independence_gap)

    planner = PhasedIndependencePlanner()
    try:
        payload = planner.build_timeline_payload(
            total_monthly_gap=total_gap,
            monthly_savings=monthly_savings,
            startup_cost_full=startup_cost_full,
        )
        selected_key = (request.args.get("scenario_key") or payload["default_scenario_key"]).strip()
        payload["contingency_scenarios"] = planner.contingency_scenarios(
            selected_key,
            total_gap,
            monthly_savings,
        )
        payload["selected_scenario_key"] = selected_key
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception("phased independence timeline failed user_id=%s", user_id)
        return jsonify({"error": "analysis_failed", "message": str(exc)}), 500

    return jsonify(payload), 200
