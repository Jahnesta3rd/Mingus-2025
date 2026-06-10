#!/usr/bin/env python3
"""Plaid bank connection API (#177)."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.models.database import db
from backend.models.transaction import Transaction
from backend.models.user_models import User
from backend.services.plaid_service import plaid_service
from backend.tasks.plaid_tasks import sync_user_transactions_background

plaid_bp = Blueprint("plaid", __name__, url_prefix="/api/plaid")


def _resolve_user() -> User | None:
    uid = get_current_user_db_id()
    if uid is None:
        return None
    return User.query.get(uid)


@plaid_bp.route("/link-token", methods=["GET"])
@require_auth
def get_link_token():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if plaid_service is None:
        return jsonify({"error": "plaid_unavailable"}), 503
    try:
        token = plaid_service.create_link_token(user.id)
        return jsonify({"link_token": token}), 200
    except Exception:
        return jsonify({"error": "plaid_unavailable"}), 503


@plaid_bp.route("/exchange-token", methods=["POST"])
@require_auth
def exchange_token():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404
    if plaid_service is None:
        return jsonify({"error": "exchange_failed"}), 400

    body = request.get_json(silent=True) or {}
    public_token = (body.get("public_token") or "").strip()
    if not public_token:
        return jsonify({"error": "exchange_failed"}), 400

    try:
        result = plaid_service.exchange_public_token(public_token)
        connected_at = datetime.utcnow()
        user.plaid_access_token = result["access_token"]
        user.plaid_item_id = result["item_id"]
        user.plaid_connected_at = connected_at
        db.session.commit()
        sync_user_transactions_background(user.id)
        return jsonify({
            "success": True,
            "connected_at": connected_at.isoformat(),
        }), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "exchange_failed"}), 400


@plaid_bp.route("/status", methods=["GET"])
@require_auth
def plaid_status():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    connected = bool(user.plaid_access_token)
    transaction_count = 0
    if connected:
        try:
            transaction_count = Transaction.query.filter_by(user_id=user.id).count()
        except Exception:
            transaction_count = 0

    return jsonify({
        "connected": connected,
        "connected_at": user.plaid_connected_at.isoformat() if user.plaid_connected_at else None,
        "transaction_count": transaction_count,
    }), 200


@plaid_bp.route("/disconnect", methods=["DELETE"])
@require_auth
def disconnect_plaid():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    try:
        user.plaid_access_token = None
        user.plaid_item_id = None
        user.plaid_connected_at = None
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"error": "disconnect_failed"}), 500
