#!/usr/bin/env python3
"""VIN Advisor API: book value, repair exposure, verdict, and replacement suggestions."""

from __future__ import annotations

from flask import Blueprint, jsonify

from backend.auth.decorators import require_auth
from backend.models.database import db
from loguru import logger

vin_advisor_bp = Blueprint("vin_advisor", __name__, url_prefix="/api")


@vin_advisor_bp.route("/vin-advisor/<int:user_id>", methods=["GET"])
@require_auth
def get_vin_advisor(user_id: int):
    logger.info(f"vin_advisor requested for user_id={user_id}")
    try:
        from backend.services.vin_advisor_service import analyze_vehicle

        result = analyze_vehicle(user_id, db.session)
        if result is None:
            return (
                jsonify(
                    {
                        "error": "no_vehicle",
                        "message": "No vehicle found for this user.",
                    }
                ),
                404,
            )
        import dataclasses

        logger.info(f"vin_advisor verdict={result.verdict} for user_id={user_id}")
        return jsonify({"status": "ok", "data": dataclasses.asdict(result)}), 200
    except Exception as e:
        logger.error(f"vin_advisor failed for user_id={user_id}: {e}")
        return jsonify({"error": "advisor_error", "message": str(e)}), 500
