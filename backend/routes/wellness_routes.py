#!/usr/bin/env python3
"""
Public /api/wellness HTTP surface.

Delegates to view functions in ``backend.api.wellness_checkin_api`` (unchanged module).
Adds: empty-data 200 responses where the legacy handlers returned 404, response shaping
for the dashboard TypeScript types, and a single registration point so we do not mount
``wellness_checkin_bp`` twice (duplicate URL rules).

Imports ``backend.api.wellness_checkin_api`` lazily on first use so importing this
blueprint alone does not pull the API module during app wiring; the first wellness
request still loads ``backend.api`` (which expects ``DATABASE_URL`` in this codebase).
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Callable

from flask import Blueprint, Response, jsonify

from backend.auth.decorators import require_auth
from backend.services.wellness_score_service import WellnessScoreCalculator

logger = logging.getLogger(__name__)

wellness_public_bp = Blueprint(
    "wellness_public",
    __name__,
    url_prefix="/api/wellness",
)

_wca_mod: Any = None


def _wca():
    """Lazy import of wellness_checkin_api (avoids backend.api package init at import time)."""
    global _wca_mod
    if _wca_mod is None:
        import backend.api.wellness_checkin_api as m

        _wca_mod = m
    return _wca_mod


def _rv_parts(rv: Any) -> tuple[Any, int]:
    if isinstance(rv, tuple):
        if len(rv) == 2:
            return rv[0], int(rv[1])
        if len(rv) == 3:
            return rv[0], int(rv[2])
    return rv, 200


def _as_dict(response_obj: Any) -> dict[str, Any]:
    if isinstance(response_obj, Response):
        data = response_obj.get_json(silent=True)
        return data if isinstance(data, dict) else {}
    if isinstance(response_obj, dict):
        return response_obj
    return {}


def _json_error(message: str, code: str = "internal_error", status: int = 500):
    return jsonify({"error": code, "message": message}), status


def _empty_scores_payload() -> dict[str, Any]:
    we = WellnessScoreCalculator.get_week_ending_date(date.today())
    return {
        "week_ending_date": we.isoformat(),
        "physical_score": None,
        "mental_score": None,
        "relational_score": None,
        "financial_feeling_score": None,
        "overall_wellness_score": None,
        "physical_change": None,
        "mental_change": None,
        "relational_change": None,
        "overall_change": None,
    }


def _empty_current_week_payload() -> dict[str, Any]:
    we = WellnessScoreCalculator.get_week_ending_date(date.today())
    return {
        "week_ending_date": we.isoformat(),
        "completed": False,
    }


def _strip_streak_to_frontend_shape(data: dict[str, Any]) -> dict[str, Any]:
    """WellnessStreakResponse: four fields only."""
    return {
        "current_streak": int(data.get("current_streak") or 0),
        "longest_streak": int(data.get("longest_streak") or 0),
        "last_checkin_date": data.get("last_checkin_date"),
        "total_checkins": int(data.get("total_checkins") or 0),
    }


def _passthrough(fn_name: str) -> Callable[..., Any]:
    def _view(*args: Any, **kwargs: Any) -> Any:
        return getattr(_wca(), fn_name)(*args, **kwargs)

    _view.__name__ = fn_name
    return _view


# --- Adapted endpoints (404 → 200, shape tweaks) ---


@wellness_public_bp.route("/scores/latest", methods=["GET"])
@require_auth
def scores_latest_adapter():
    try:
        body, status = _rv_parts(_wca().get_latest_scores())
        if status == 404:
            return jsonify(_empty_scores_payload()), 200
        if status != 200:
            return body, status
        data = _as_dict(body)
        data.pop("calculated_at", None)
        return jsonify(data), 200
    except Exception as e:
        logger.exception("wellness scores/latest: %s", e)
        return _json_error(str(e))


@wellness_public_bp.route("/insights", methods=["GET"])
@require_auth
def insights_adapter():
    try:
        body, status = _rv_parts(_wca().get_insights())
        if status == 404:
            return jsonify({"insights": [], "weeks_of_data": 0}), 200
        if status != 200:
            return body, status
        return body, status
    except Exception as e:
        logger.exception("wellness insights: %s", e)
        return _json_error(str(e))


@wellness_public_bp.route("/streak", methods=["GET"])
@require_auth
def streak_adapter():
    try:
        body, status = _rv_parts(_wca().get_streak())
        if status != 200:
            return body, status
        data = _as_dict(body)
        return jsonify(_strip_streak_to_frontend_shape(data)), 200
    except Exception as e:
        logger.exception("wellness streak: %s", e)
        return _json_error(str(e))


@wellness_public_bp.route("/checkin/current-week", methods=["GET"])
@require_auth
def current_week_checkin_adapter():
    try:
        body, status = _rv_parts(_wca().get_current_week_checkin())
        if status == 404:
            return jsonify(_empty_current_week_payload()), 200
        if status != 200:
            return body, status
        return body, status
    except Exception as e:
        logger.exception("wellness checkin/current-week: %s", e)
        return _json_error(str(e))


@wellness_public_bp.route("/checkin", methods=["POST"])
@require_auth
def submit_checkin_adapter():
    try:
        body, status = _rv_parts(_wca().submit_checkin())
        return body, status
    except Exception as e:
        logger.exception("wellness checkin POST: %s", e)
        return _json_error(str(e))


@wellness_public_bp.route("/weekly-checkin/questions", methods=["GET"])
@require_auth
def weekly_checkin_questions_adapter():
    try:
        body, status = _rv_parts(_wca().get_weekly_checkin_questions())
        return body, status
    except Exception as e:
        logger.exception("wellness weekly-checkin/questions: %s", e)
        return _json_error(str(e))


@wellness_public_bp.route("/weekly-checkin", methods=["POST"])
@require_auth
def weekly_checkin_submit_adapter():
    try:
        body, status = _rv_parts(_wca().submit_weekly_checkin_unified())
        return body, status
    except Exception as e:
        logger.exception("wellness weekly-checkin POST: %s", e)
        return _json_error(str(e))


# --- Passthrough routes (same handlers as wellness_checkin_api) ---

wellness_public_bp.add_url_rule(
    "/checkin/history",
    endpoint="checkin_history",
    view_func=_passthrough("get_checkin_history"),
    methods=["GET"],
)
wellness_public_bp.add_url_rule(
    "/scores/history",
    endpoint="scores_history",
    view_func=_passthrough("get_scores_history"),
    methods=["GET"],
)
wellness_public_bp.add_url_rule(
    "/spending/history",
    endpoint="spending_history",
    view_func=_passthrough("get_spending_history"),
    methods=["GET"],
)
wellness_public_bp.add_url_rule(
    "/spending/baselines",
    endpoint="spending_baselines",
    view_func=_passthrough("get_spending_baselines"),
    methods=["GET"],
)
wellness_public_bp.add_url_rule(
    "/correlations",
    endpoint="correlations",
    view_func=_passthrough("get_correlations"),
    methods=["GET"],
)
wellness_public_bp.add_url_rule(
    "/correlations/refresh",
    endpoint="correlations_refresh",
    view_func=_passthrough("refresh_correlations"),
    methods=["POST"],
)
wellness_public_bp.add_url_rule(
    "/parenting-costs",
    endpoint="parenting_costs",
    view_func=_passthrough("get_parenting_costs"),
    methods=["GET"],
)
wellness_public_bp.add_url_rule(
    "/achievements",
    endpoint="achievements",
    view_func=_passthrough("get_achievements"),
    methods=["GET"],
)
wellness_public_bp.add_url_rule(
    "/summary",
    endpoint="summary",
    view_func=_passthrough("get_summary"),
    methods=["GET"],
)
