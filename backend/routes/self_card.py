#!/usr/bin/env python3
"""Self Card API: internal body / mind / sleep / stress-spend snapshot for the roster."""

from __future__ import annotations

from flask import Blueprint, g, jsonify

from backend.auth.decorators import require_auth
from backend.models.user_models import User
from backend.services import self_card_service as scs

self_card_bp = Blueprint("self_card", __name__)


def _user_from_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


@self_card_bp.route("/self-card", methods=["GET"])
@require_auth
def get_self_card():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(scs.get_self_card_data(user.id))
