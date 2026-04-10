#!/usr/bin/env python3
"""Life Ready Score API: single composite readiness endpoint."""

from __future__ import annotations

from flask import Blueprint, g, jsonify

from backend.auth.decorators import require_auth
from backend.models.user_models import User
from backend.services.life_ready_score_service import compute_life_ready_score

life_ready_score_bp = Blueprint("life_ready_score", __name__)


def _user_from_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


@life_ready_score_bp.route("/api/life-ready-score", methods=["GET"])
@require_auth
def get_life_ready_score():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(compute_life_ready_score(user.id))
