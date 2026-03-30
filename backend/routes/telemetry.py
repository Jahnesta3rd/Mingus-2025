#!/usr/bin/env python3
"""Feature usage telemetry API (JWT). Events are queued to Celery for SQLite insert."""

import logging

from flask import Blueprint, g, jsonify, request

from backend.auth.decorators import require_auth
from backend.models.user_models import User
from backend.services.telemetry_service import TRACKED_FEATURES

logger = logging.getLogger(__name__)

telemetry_bp = Blueprint("telemetry", __name__, url_prefix="/api/telemetry")

_VALID_EVENT_TYPES = frozenset({"view", "click", "export", "search"})


def _user_for_jwt():
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


@telemetry_bp.route("/event", methods=["POST"])
@require_auth
def post_telemetry_event():
    data = request.get_json(silent=True) or {}
    event_type = (data.get("event_type") or "").strip()
    feature_name = (data.get("feature_name") or "").strip()
    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return jsonify({"error": "metadata must be an object"}), 400

    if feature_name not in TRACKED_FEATURES:
        return jsonify({"error": "Unknown or untracked feature_name"}), 400
    if event_type not in _VALID_EVENT_TYPES:
        return jsonify({"error": 'event_type must be one of: view, click, export, search'}), 400

    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id = str(user.user_id)
    user_tier = (user.tier or "")[:50] if user.tier else None

    try:
        from backend.tasks.telemetry_tasks import log_telemetry_event

        log_telemetry_event.delay(user_id, event_type, feature_name, metadata, user_tier)
    except Exception as exc:
        logger.warning("Failed to enqueue telemetry event: %s", exc)

    return jsonify({"accepted": True}), 202
