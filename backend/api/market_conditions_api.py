#!/usr/bin/env python3
"""Market conditions API (#165)."""

from __future__ import annotations

import logging

from flask import Blueprint, g, jsonify, request
from flask_cors import cross_origin

from backend.auth.decorators import require_auth
from backend.models.user_models import User
from backend.services.market_conditions_service import get_market_conditions

logger = logging.getLogger(__name__)

market_conditions_api = Blueprint("market_conditions_api", __name__)


@market_conditions_api.route("/api/market-conditions", methods=["GET", "OPTIONS"])
@cross_origin()
@require_auth
def market_conditions():
    """Return national, regional, and personal market conditions for the current user."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user = User.query.filter_by(user_id=str(g.current_user_id)).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        payload = get_market_conditions(user)
    except Exception as exc:
        logger.exception("market-conditions failed for user %s: %s", g.current_user_id, exc)
        return jsonify({"error": "Unable to load market conditions"}), 500

    return jsonify(payload), 200
