#!/usr/bin/env python3
"""Company screen API — run multi-layer employer screens and manage questions (CS4)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

from backend.auth.decorators import get_current_jwt_user, jwt_required
from backend.models.company_screen import CompanyScreen, CompanyScreenQuestion
from backend.models.database import db
from backend.services.company_screen_service import CompanyScreenService
from backend.services.module_access_service import has_module

logger = logging.getLogger(__name__)

company_screen_bp = Blueprint(
    "company_screen",
    __name__,
    url_prefix="/api/company-screen",
)


def _first_of_next_month_iso() -> str:
    now = datetime.utcnow()
    if now.month == 12:
        resets = datetime(now.year + 1, 1, 1)
    else:
        resets = datetime(now.year, now.month + 1, 1)
    return resets.isoformat()


def _load_user():
    user = get_current_jwt_user()
    if user is None:
        return None, (jsonify({"error": "NOT_FOUND", "message": "User not found"}), 404)
    return user, None


@company_screen_bp.route("/run", methods=["POST", "OPTIONS"])
@cross_origin()
@jwt_required
def run_company_screen():
    """Run a new company screen for the authenticated user."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user, error_response = _load_user()
    if error_response:
        return error_response

    data = request.get_json(silent=True) or {}
    employer_name = (data.get("employer_name") or "").strip()
    employer_cik = data.get("employer_cik")
    if employer_cik is not None:
        employer_cik = str(employer_cik).strip() or None

    if not employer_name:
        return jsonify(
            {
                "error": "VALIDATION",
                "message": "employer_name is required",
            }
        ), 400

    if len(employer_name) > 200:
        return jsonify(
            {
                "error": "VALIDATION",
                "message": "employer_name must be at most 200 characters",
            }
        ), 400

    tier = (user.tier or "budget").strip().lower()
    career_pro_access = has_module(user.id, "career_pro")
    unlimited_tiers = frozenset({"professional", "family_life_stage"})

    if not career_pro_access and tier not in unlimited_tiers:
        return jsonify(
            {
                "error": "TIER_GATE",
                "message": "Upgrade to Career Pro to screen companies before interviews.",
                "upgrade_url": "/settings/billing",
            }
        ), 403

    service = CompanyScreenService()
    if career_pro_access and tier not in unlimited_tiers:
        used = service.get_screens_used_this_cycle(user.id, db.session)
        if used >= 10:
            return jsonify(
                {
                    "error": "SCREEN_LIMIT",
                    "message": f"You have used {used} of 10 company screens this month.",
                    "resets_on": _first_of_next_month_iso(),
                }
            ), 429

    try:
        result = service.run_screen(
            user.id,
            employer_name,
            employer_cik,
            db.session,
        )
        return jsonify(result), 200
    except Exception as exc:
        logger.exception("run_company_screen failed for user_id=%s", user.id)
        db.session.rollback()
        return jsonify(
            {
                "error": "INTERNAL",
                "message": str(exc),
            }
        ), 500


@company_screen_bp.route("/<uuid:screen_id>", methods=["GET", "OPTIONS"])
@cross_origin()
@jwt_required
def get_company_screen(screen_id: uuid.UUID):
    """Return a single company screen owned by the current user."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user, error_response = _load_user()
    if error_response:
        return error_response

    screen = (
        db.session.query(CompanyScreen)
        .filter(
            CompanyScreen.id == screen_id,
            CompanyScreen.user_id == user.id,
        )
        .first()
    )
    if screen is None:
        return jsonify(
            {"error": "NOT_FOUND", "message": "Screen not found"}
        ), 404

    service = CompanyScreenService()
    return jsonify(service._serialize_screen(screen)), 200


@company_screen_bp.route("/history", methods=["GET", "OPTIONS"])
@cross_origin()
@jwt_required
def company_screen_history():
    """Return recent company screens for the current user."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user, error_response = _load_user()
    if error_response:
        return error_response

    screens = (
        db.session.query(CompanyScreen)
        .filter(CompanyScreen.user_id == user.id)
        .order_by(CompanyScreen.created_at.desc())
        .limit(20)
        .all()
    )

    service = CompanyScreenService()
    serialized = [service._serialize_screen(screen) for screen in screens]
    return jsonify({"screens": serialized, "total": len(serialized)}), 200


@company_screen_bp.route(
    "/questions/<uuid:question_id>/dismiss",
    methods=["PATCH", "OPTIONS"],
)
@cross_origin()
@jwt_required
def dismiss_company_screen_question(question_id: uuid.UUID):
    """Mark a question as dismissed."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user, error_response = _load_user()
    if error_response:
        return error_response

    question = (
        db.session.query(CompanyScreenQuestion)
        .join(CompanyScreen)
        .filter(
            CompanyScreenQuestion.id == question_id,
            CompanyScreen.user_id == user.id,
        )
        .first()
    )
    if question is None:
        return jsonify(
            {"error": "NOT_FOUND", "message": "Screen not found"}
        ), 404

    question.dismissed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"dismissed": True, "question_id": str(question_id)}), 200


@company_screen_bp.route(
    "/questions/<uuid:question_id>/copy",
    methods=["PATCH", "OPTIONS"],
)
@cross_origin()
@jwt_required
def copy_company_screen_question(question_id: uuid.UUID):
    """Mark a question as copied."""
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user, error_response = _load_user()
    if error_response:
        return error_response

    question = (
        db.session.query(CompanyScreenQuestion)
        .join(CompanyScreen)
        .filter(
            CompanyScreenQuestion.id == question_id,
            CompanyScreen.user_id == user.id,
        )
        .first()
    )
    if question is None:
        return jsonify(
            {"error": "NOT_FOUND", "message": "Screen not found"}
        ), 404

    question.copied_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"copied": True, "question_id": str(question_id)}), 200
