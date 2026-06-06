#!/usr/bin/env python3
"""
Public /api/gamification HTTP surface (Milestones).

Delegates to ``backend.api.gamification_api`` tier check and ``gamification_service`` on
that module (same singleton as the legacy blueprint). Uses internal ``users.id`` for
streak/milestone DB queries; external ``users.user_id`` for tier checks and userId query
comparison.

Imports ``backend.api.gamification_api`` lazily on first request (see wellness_routes).
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_jwt_user, require_auth

logger = logging.getLogger(__name__)

gamification_public_bp = Blueprint(
    "gamification_public",
    __name__,
    url_prefix="/api/gamification",
)

# Frontend SpendingMilestonesWidget — fixed thresholds only.
_FRONTEND_MILESTONE_DAYS: tuple[int, ...] = (3, 7, 14, 30, 60, 100)

_ga_mod: Any = None


def _ga():
    global _ga_mod
    if _ga_mod is None:
        import backend.api.gamification_api as m

        _ga_mod = m
    return _ga_mod


def _empty_milestones_payload() -> dict[str, Any]:
    return {
        "current_streak": 0,
        "next_milestone": 3,
        "milestones": [],
        "achievements": [],
    }


def _next_milestone_days(current_streak: int) -> int:
    for d in _FRONTEND_MILESTONE_DAYS:
        if current_streak < d:
            return d
    return _FRONTEND_MILESTONE_DAYS[-1]


def _json_error(message: str, code: str, status: int):
    return jsonify({"error": code, "message": message}), status


@gamification_public_bp.route("/milestones", methods=["GET"])
@require_auth
def milestones_adapter():
    """
    GET /api/gamification/milestones

    Query ``userId`` is optional; if present it must match the authenticated user
    (external ``user_id`` or internal numeric ``id``).
    """
    try:
        user = get_current_jwt_user()
        if not user:
            return jsonify(_empty_milestones_payload()), 200

        uid_int = int(user.id)
        uid_ext = str(user.user_id).strip() if getattr(user, "user_id", None) else str(uid_int)

        raw_q = request.args.get("userId") or request.args.get("userid")
        if raw_q is not None and str(raw_q).strip() != "":
            qn = str(raw_q).strip()
            if qn not in {uid_ext, str(uid_int)}:
                return _json_error(
                    "userId does not match authenticated user",
                    "forbidden",
                    403,
                )

        ga = _ga()
        if not ga.check_user_tier_access(uid_ext, ga.FeatureTier.BUDGET):
            return jsonify(
                {
                    "error": "Feature not available",
                    "message": "Gamification features are not available in your current tier.",
                    "upgrade_required": True,
                    "required_tier": "budget",
                }
            ), 403

        streak_data = ga.gamification_service.calculate_streak(uid_int)
        milestones = ga.gamification_service.get_milestones(uid_int, streak_data)
        achievements_objs = ga.gamification_service.get_achievements(uid_int)
        achievements = [a.id for a in achievements_objs if getattr(a, "unlocked", False)]

        by_days = {m.days_required: m for m in milestones}
        shaped_milestones = []
        for d in _FRONTEND_MILESTONE_DAYS:
            m = by_days.get(d)
            if m is None:
                shaped_milestones.append(
                    {"days": d, "achieved": False, "achieved_date": None}
                )
            else:
                ad = m.achieved_date.isoformat() if m.achieved_date else None
                shaped_milestones.append(
                    {"days": d, "achieved": bool(m.achieved), "achieved_date": ad}
                )

        current_streak = int(getattr(streak_data, "current_streak", 0) or 0)
        payload = {
            "current_streak": current_streak,
            "next_milestone": _next_milestone_days(current_streak),
            "milestones": shaped_milestones,
            "achievements": achievements,
        }
        return jsonify(payload), 200
    except Exception as e:
        logger.exception("gamification milestones: %s", e)
        return jsonify(_empty_milestones_payload()), 200
