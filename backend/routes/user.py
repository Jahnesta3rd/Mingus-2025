#!/usr/bin/env python3
"""
User routes: agreement acceptance audit trail (JWT required).
"""

from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request
from flask_cors import cross_origin
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from backend.auth.decorators import get_current_jwt_user, jwt_required
from backend.models.agreement_acceptance import AgreementAcceptance
from backend.models.database import db

ALLOWED_AGREEMENT_VERSIONS = frozenset({"September2025"})
CURRENT_TERMS_VERSION = "September2025"

user_bp = Blueprint("user_agreement", __name__, url_prefix="/api/user")


def _parse_agreed_at(raw):
    """Return naive UTC datetime; raises ValueError if invalid."""
    if raw is None or raw == "":
        return datetime.utcnow()
    s = str(raw).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _accepted_at_iso(dt: datetime) -> str:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.isoformat() + "Z"


@user_bp.route("/agreement-acceptance", methods=["POST", "OPTIONS"])
@cross_origin()
@jwt_required
def post_agreement_acceptance():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(
            {"success": False, "error": "Missing required field: agreementVersion"}
        ), 400

    if "agreementVersion" not in data or data["agreementVersion"] is None:
        return jsonify(
            {"success": False, "error": "Missing required field: agreementVersion"}
        ), 400

    agreement_version = data["agreementVersion"]
    if not isinstance(agreement_version, str) or not agreement_version.strip():
        return jsonify(
            {"success": False, "error": "Missing required field: agreementVersion"}
        ), 400

    agreement_version = agreement_version.strip()
    if agreement_version not in ALLOWED_AGREEMENT_VERSIONS:
        return jsonify(
            {
                "success": False,
                "error": f"Invalid agreementVersion; allowed: {sorted(ALLOWED_AGREEMENT_VERSIONS)}",
            }
        ), 400

    cu = get_current_jwt_user()
    if cu is None:
        return jsonify(
            {
                "success": False,
                "error": "User record not found for authenticated session",
            }
        ), 400

    user_id = cu.id
    if user_id is None:
        return jsonify(
            {"success": False, "error": "Invalid user session"}
        ), 400

    agreed_raw = data.get("agreedAt")
    try:
        if agreed_raw is None or agreed_raw == "":
            accepted_at = datetime.utcnow()
        else:
            accepted_at = _parse_agreed_at(agreed_raw)
    except (ValueError, TypeError):
        return jsonify(
            {"success": False, "error": "Invalid agreedAt timestamp; use ISO-8601"}
        ), 400

    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent", "Unknown")

    acceptance = AgreementAcceptance(
        user_id=user_id,
        agreement_version=agreement_version,
        accepted_at=accepted_at,
        ip_address=ip_address,
        user_agent=user_agent,
        agreement_hash=None,
    )

    try:
        db.session.add(acceptance)
        db.session.commit()
    except SQLAlchemyError:
        logger.exception(
            "Failed to persist agreement acceptance user_id={} version={}",
            user_id,
            agreement_version,
        )
        db.session.rollback()
        return jsonify(
            {"success": False, "error": "Failed to save agreement acceptance"}
        ), 500
    except Exception:
        logger.exception(
            "Unexpected error saving agreement acceptance user_id={} version={}",
            user_id,
            agreement_version,
        )
        db.session.rollback()
        return jsonify(
            {"success": False, "error": "Failed to save agreement acceptance"}
        ), 500

    accepted_iso = _accepted_at_iso(accepted_at)
    logger.info(
        "Agreement accepted user_id={} agreement_version={} accepted_at={} ip={} user_agent={}",
        user_id,
        agreement_version,
        accepted_iso,
        ip_address,
        user_agent[:200] if user_agent else "",
    )

    return jsonify(
        {
            "success": True,
            "message": "Agreement accepted",
            "acceptedAt": accepted_iso,
            "agreementVersion": agreement_version,
        }
    ), 201


@user_bp.route("/terms-status", methods=["GET", "OPTIONS"])
@cross_origin()
@jwt_required
def get_terms_status():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    cu = get_current_jwt_user()
    if cu is None:
        return jsonify(
            {
                "success": False,
                "error": "User record not found for authenticated session",
            }
        ), 400

    user_id = cu.id
    if user_id is None:
        return jsonify({"success": False, "error": "Invalid user session"}), 400

    try:
        latest = (
            AgreementAcceptance.query.filter_by(
                user_id=user_id,
                agreement_version=CURRENT_TERMS_VERSION,
            )
            .order_by(AgreementAcceptance.accepted_at.desc())
            .limit(1)
            .first()
        )
    except SQLAlchemyError:
        logger.exception(
            "DB error loading terms status user_id={}",
            user_id,
        )
        return jsonify({"error": "Failed to load terms status"}), 500
    except Exception:
        logger.exception(
            "Unexpected error loading terms status user_id={}",
            user_id,
        )
        return jsonify({"error": "Failed to load terms status"}), 500

    if latest is None:
        return jsonify(
            {
                "accepted": False,
                "acceptedVersion": None,
                "currentVersion": CURRENT_TERMS_VERSION,
                "acceptedAt": None,
            }
        ), 200

    return jsonify(
        {
            "accepted": True,
            "acceptedVersion": latest.agreement_version,
            "currentVersion": CURRENT_TERMS_VERSION,
            "acceptedAt": _accepted_at_iso(latest.accepted_at),
        }
    ), 200


@user_bp.route("/test-auth", methods=["GET", "OPTIONS"])
@cross_origin()
@jwt_required
def test_auth():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    cu = get_current_jwt_user()
    return jsonify(
        {
            "success": True,
            "current_user_id_claim": getattr(g, "current_user_id", None),
            "current_user_email": getattr(g, "current_user_email", None),
            "user": cu.to_dict() if cu else None,
        }
    ), 200
