#!/usr/bin/env python3
"""Beta code validation (public), redemption (authenticated), and admin status."""
from datetime import datetime

from flask import Blueprint, jsonify, request, g

from backend.auth.decorators import require_auth
from backend.middleware.limiter_ext import limiter
from backend.models.beta_code import BetaCode
from backend.models.database import db
from backend.models.user_models import User
from backend.services.business_intelligence_log import log_event

beta_bp = Blueprint("beta", __name__, url_prefix="/api/beta")


def _user_for_jwt():
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _is_admin_user(user: User) -> bool:
    if not user:
        return False
    if getattr(user, "is_admin", False):
        return True
    role = (getattr(user, "role", None) or "").lower()
    return role == "admin"


def _tier_unset_for_beta(user: User) -> bool:
    t = user.tier
    if t is None or t == "":
        return True
    return t == "budget"


@beta_bp.route("/validate", methods=["POST"])
@limiter.limit("10 per minute")
def validate_beta_code():
    """Pre-registration: check code exists and is not redeemed (does not consume)."""
    data = request.get_json(silent=True) or {}
    code_str = (data.get("code") or "").strip()
    if not code_str:
        return jsonify({"valid": False, "error": "Code required"}), 400

    record = BetaCode.query.filter_by(code=code_str).first()
    if not record:
        return jsonify({"valid": False, "error": "Code not found"}), 404
    if record.status == "redeemed":
        return jsonify({"valid": False, "error": "Code already used"}), 409

    return jsonify(
        {
            "valid": True,
            "message": "Beta code accepted",
            "tier": "professional",
        }
    ), 200


@beta_bp.route("/redeem", methods=["POST"])
@require_auth
def redeem_beta_code():
    """Register professional tier from an available beta code (no Stripe)."""
    data = request.get_json(silent=True) or {}
    code_str = (data.get("code") or "").strip()
    if not code_str:
        return jsonify({"success": False, "error": "Code required"}), 400

    user = _user_for_jwt()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    if user.is_beta:
        return jsonify(
            {"success": False, "error": "Beta access already activated for this account"}
        ), 409

    if not _tier_unset_for_beta(user):
        return jsonify(
            {
                "success": False,
                "error": "Beta codes are only for accounts without a paid tier upgrade",
            }
        ), 403

    record = BetaCode.query.filter_by(code=code_str).first()
    if not record:
        return jsonify({"success": False, "error": "Code not found"}), 404
    if record.status == "redeemed":
        return jsonify({"success": False, "error": "Code already used"}), 409

    now = datetime.utcnow()
    record.status = "redeemed"
    record.redeemed_at = now
    record.redeemed_by_user_id = user.id

    user.tier = "professional"
    user.is_beta = True
    user.beta_batch = record.batch

    db.session.commit()

    log_event(
        "beta_code_redeemed",
        user_id=user.id,
        code=record.code,
        batch=record.batch,
    )

    return jsonify(
        {
            "success": True,
            "tier": "professional",
            "message": "Welcome to Mingus Beta! You have full Professional access.",
        }
    ), 200


@beta_bp.route("/status", methods=["GET"])
@require_auth
def beta_status():
    """Admin-only aggregate beta code statistics."""
    user = _user_for_jwt()
    if not user or not _is_admin_user(user):
        return jsonify({"error": "Admin access required"}), 403

    rows = BetaCode.query.order_by(BetaCode.id).all()
    total = len(rows)
    available = sum(1 for r in rows if r.status == "available")
    redeemed = sum(1 for r in rows if r.status == "redeemed")

    by_batch = {}
    for r in rows:
        key = r.batch or ""
        if key not in by_batch:
            by_batch[key] = {"total": 0, "redeemed": 0}
        by_batch[key]["total"] += 1
        if r.status == "redeemed":
            by_batch[key]["redeemed"] += 1

    codes = [
        {
            "code": r.code,
            "status": r.status,
            "batch": r.batch,
            "redeemed_at": r.redeemed_at.isoformat() if r.redeemed_at else None,
            "redeemed_by_user_id": r.redeemed_by_user_id,
        }
        for r in rows
    ]

    return jsonify(
        {
            "total": total,
            "available": available,
            "redeemed": redeemed,
            "by_batch": by_batch,
            "codes": codes,
        }
    ), 200
