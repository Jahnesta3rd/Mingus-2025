#!/usr/bin/env python3
"""User alerts API: unread list and mark-read."""

from __future__ import annotations

import uuid
from datetime import datetime

from flask import Blueprint, g, jsonify

from backend.auth.decorators import require_auth, require_csrf
from backend.models.alerts import UserAlert
from backend.models.database import db
from backend.models.user_models import User

alerts_bp = Blueprint("alerts", __name__)


def _user_for_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _alert_json(row: UserAlert) -> dict:
    return {
        "id": str(row.id),
        "type": row.alert_type,
        "severity": row.severity,
        "message": row.message,
        "action_label": row.action_label,
        "action_route": row.action_route,
    }


@alerts_bp.route("/unread", methods=["GET"])
@require_auth
def list_unread():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    limit = 50
    tier = (user.tier or "budget").strip().lower()
    if tier == "budget":
        limit = 1

    rows = (
        UserAlert.query.filter(
            UserAlert.user_id == user.id,
            UserAlert.read_at.is_(None),
        )
        .order_by(UserAlert.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"alerts": [_alert_json(r) for r in rows]})


@alerts_bp.route("/<uuid:alert_id>/read", methods=["PATCH"])
@require_auth
@require_csrf
def mark_read(alert_id: uuid.UUID):
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404

    row = db.session.get(UserAlert, alert_id)
    if not row or row.user_id != user.id:
        return jsonify({"error": "Not found"}), 404

    now = datetime.utcnow()
    row.read_at = now
    row.dismissed_at = now
    db.session.commit()
    return jsonify({"ok": True})
