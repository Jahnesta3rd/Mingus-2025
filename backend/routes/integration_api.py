#!/usr/bin/env python3
"""ICC ↔ DF1 integration endpoints."""

from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.services.side_income_integration_service import (
    IntegrationError,
    SideIncomeIntegrationService,
    _parse_uuid,
)
from backend.services.expense_audit_service import ExpenseAuditAnalyzer

logger = logging.getLogger(__name__)

integration_bp = Blueprint("integration", __name__, url_prefix="/api/integration")


def _parse_positive_float(value, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise IntegrationError(f"{field} must be a number", status_code=400, error="invalid_input") from None
    if parsed <= 0:
        raise IntegrationError(f"{field} must be positive", status_code=400, error="invalid_input")
    return parsed


def _parse_datetime(value) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    raw = str(value).strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise IntegrationError(
            "income_date must be a valid ISO datetime",
            status_code=400,
            error="invalid_input",
        ) from exc


@integration_bp.route("/icc-to-df1-handoff", methods=["POST"])
@require_auth
def icc_to_df1_handoff():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    try:
        icc_assessment_id = _parse_uuid(body.get("icc_assessment_id"), "icc_assessment_id")
        person_id = _parse_uuid(body.get("person_id"), "person_id")
        selected_job = body.get("selected_job")
        df1_job_type = body.get("df1_job_type")
        target_monthly_income = _parse_positive_float(
            body.get("target_monthly_income"),
            "target_monthly_income",
        )
        gap_coverage_pct = float(body.get("gap_coverage_pct") or 0)
        payload = SideIncomeIntegrationService().create_icc_to_df1_handoff(
            user_id=user_id,
            icc_assessment_id=icc_assessment_id,
            person_id=person_id,
            selected_job=selected_job,
            df1_job_type=df1_job_type,
            target_monthly_income=target_monthly_income,
            gap_coverage_pct=gap_coverage_pct,
        )
    except IntegrationError as exc:
        return jsonify({"error": exc.error, "message": exc.message}), exc.status_code
    except Exception as exc:
        logger.exception("ICC to DF1 handoff failed for user_id=%s: %s", user_id, exc)
        return (
            jsonify(
                {
                    "error": "handoff_failed",
                    "message": "Could not create side income commitment.",
                }
            ),
            500,
        )

    return jsonify(payload), 200


@integration_bp.route("/df1-to-icc-milestone", methods=["POST"])
def df1_to_icc_milestone():
    """Record DF1 income milestones; auth optional for internal service calls."""
    user_id = get_current_user_db_id()

    body = request.get_json(silent=True) or {}
    try:
        commitment_id = _parse_uuid(body.get("commitment_id"), "commitment_id")
        milestone_type = str(body.get("milestone_type") or "").strip()
        income_amount = float(body.get("income_amount"))
        income_date = _parse_datetime(body.get("income_date"))
        payload = SideIncomeIntegrationService().record_df1_milestone(
            commitment_id=commitment_id,
            milestone_type=milestone_type,
            income_amount=income_amount,
            income_date=income_date,
            user_id=user_id,
        )
    except IntegrationError as exc:
        return jsonify({"error": exc.error, "message": exc.message}), exc.status_code
    except (TypeError, ValueError):
        return jsonify({"error": "invalid_input", "message": "Invalid request body"}), 400
    except Exception as exc:
        logger.exception("DF1 milestone update failed: %s", exc)
        return (
            jsonify(
                {
                    "error": "milestone_failed",
                    "message": "Could not update side income commitment.",
                }
            ),
            500,
        )

    return jsonify(payload), 200


@integration_bp.route("/expense-audit-to-icc-dashboard", methods=["POST"])
@require_auth
def expense_audit_to_icc_dashboard():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    try:
        icc_assessment_id = _parse_uuid(body.get("icc_assessment_id"), "icc_assessment_id")
        selected_tiers = body.get("selected_tiers") or []
        if not isinstance(selected_tiers, list):
            raise IntegrationError(
                "selected_tiers must be an array",
                status_code=400,
                error="invalid_input",
            )
        snapshot_id = body.get("snapshot_id")
        parsed_snapshot = (
            _parse_uuid(snapshot_id, "snapshot_id") if snapshot_id else None
        )
        payload = ExpenseAuditAnalyzer().apply_tiers_to_icc(
            user_id=user_id,
            icc_assessment_id=icc_assessment_id,
            selected_tiers=selected_tiers,
            snapshot_id=parsed_snapshot,
        )
    except IntegrationError as exc:
        return jsonify({"error": exc.error, "message": exc.message}), exc.status_code
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400
    except LookupError as exc:
        return jsonify({"error": "not_found", "message": str(exc)}), 404
    except Exception as exc:
        logger.exception("expense audit ICC integration failed user_id=%s", user_id)
        return (
            jsonify(
                {
                    "error": "integration_failed",
                    "message": "Could not apply expense cuts to ICC.",
                }
            ),
            500,
        )

    return jsonify(payload), 200
