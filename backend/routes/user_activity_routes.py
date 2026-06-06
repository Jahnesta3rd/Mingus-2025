#!/usr/bin/env python3
"""Public /api/user/activity HTTP surface for dashboard recent activity."""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify

from backend.auth.decorators import get_current_jwt_user, require_auth

logger = logging.getLogger(__name__)

user_activity_public_bp = Blueprint(
    "user_activity_public",
    __name__,
    url_prefix="/api/user/activity",
)

_uas_mod: Any = None


def _user_activity_service():
    """Lazy import of aggregator (mirrors gamification_public lazy-import style)."""
    global _uas_mod
    if _uas_mod is None:
        import backend.services.user_activity_service as m

        _uas_mod = m
    return _uas_mod


@user_activity_public_bp.route("/recent", methods=["GET"])
@require_auth
def recent_activity():
    """GET /api/user/activity/recent — {activities: [...]} (no success/data wrapper)."""
    try:
        user = get_current_jwt_user()
        if not user:
            return jsonify({"activities": []}), 200

        svc = _user_activity_service()
        activities = svc.get_recent_activity(int(user.id), limit=20)
        return jsonify({"activities": activities}), 200
    except Exception as e:
        logger.exception("user activity recent: %s", e)
        return jsonify(
            {
                "error": "server_error",
                "message": "Unable to load recent activity.",
            }
        ), 500
