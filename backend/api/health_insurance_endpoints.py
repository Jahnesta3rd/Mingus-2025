#!/usr/bin/env python3
"""Health Insurance Advisor plan upload and management API."""

from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.models.database import db
from backend.models.health_insurance_plan import HealthInsurancePlan
from backend.models.user_models import User

logger = logging.getLogger(__name__)

health_insurance_bp = Blueprint(
    "health_insurance", __name__, url_prefix="/api/benefits"
)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
UPLOAD_ROOT = "/var/www/mingus/uploads/insurance"

_MANUAL_FIELDS = (
    "plan_name",
    "plan_type",
    "insurer_name",
    "plan_year",
    "monthly_premium_employee",
    "monthly_premium_employee_spouse",
    "monthly_premium_family",
    "annual_deductible_individual",
    "annual_deductible_family",
    "out_of_pocket_max_individual",
    "out_of_pocket_max_family",
    "coinsurance_pct",
    "copay_primary_care",
    "copay_specialist",
    "copay_er",
    "rx_tier1",
    "rx_tier2",
    "rx_tier3",
    "rx_tier4",
    "has_hsa_eligible",
    "employer_hsa_contribution",
    "in_network_only",
)


def _resolve_user() -> User | None:
    uid = get_current_user_db_id()
    if uid is None:
        return None
    return User.query.get(uid)


def _get_owned_plan(plan_id: int, user_id: int) -> HealthInsurancePlan | None:
    return HealthInsurancePlan.query.filter_by(id=plan_id, user_id=user_id).first()


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _clean_plan_name(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = re.sub(r"[_\-]+", " ", stem).strip()
    return cleaned[:200] or "Insurance Plan"


def _plan_summary(plan: HealthInsurancePlan) -> dict[str, Any]:
    return {
        "plan_id": plan.id,
        "plan_name": plan.plan_name,
        "plan_type": plan.plan_type,
        "insurer_name": plan.insurer_name,
        "parse_status": plan.parse_status,
        "parsed_at": plan.parsed_at.isoformat() if plan.parsed_at else None,
        "monthly_premium_employee": _to_float(plan.monthly_premium_employee),
        "annual_deductible_individual": _to_float(plan.annual_deductible_individual),
        "out_of_pocket_max_individual": _to_float(plan.out_of_pocket_max_individual),
        "has_hsa_eligible": bool(plan.has_hsa_eligible),
    }


def _upload_response(plan: HealthInsurancePlan, filename: str) -> dict[str, Any]:
    return {
        "plan_id": plan.id,
        "filename": filename,
        "parse_status": plan.parse_status,
    }


def _collect_upload_files():
    files = request.files.getlist("files")
    if not files:
        files = request.files.getlist("file")
    if not files:
        files = list(request.files.values())
    return [f for f in files if f and f.filename]


def _apply_manual_fields(plan: HealthInsurancePlan, data: dict[str, Any]) -> None:
    for field in _MANUAL_FIELDS:
        if field not in data:
            continue
        value = data[field]
        if field == "has_hsa_eligible":
            plan.has_hsa_eligible = bool(value)
        elif field == "in_network_only":
            plan.in_network_only = None if value is None else bool(value)
        elif field == "plan_year" or field == "coinsurance_pct":
            plan.__setattr__(field, None if value is None else int(value))
        elif field in {
            "monthly_premium_employee",
            "monthly_premium_employee_spouse",
            "monthly_premium_family",
            "annual_deductible_individual",
            "annual_deductible_family",
            "out_of_pocket_max_individual",
            "out_of_pocket_max_family",
            "copay_primary_care",
            "copay_specialist",
            "copay_er",
            "rx_tier1",
            "rx_tier2",
            "rx_tier3",
            "rx_tier4",
            "employer_hsa_contribution",
        }:
            plan.__setattr__(field, None if value is None else value)
        else:
            plan.__setattr__(field, value)
    plan.parse_status = "manual"
    plan.updated_at = datetime.utcnow()


@health_insurance_bp.route("/insurance-plans/upload", methods=["POST"])
@require_auth
def upload_insurance_plans():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    upload_files = _collect_upload_files()
    if not upload_files:
        return jsonify({"error": "No files uploaded"}), 400

    from backend.tasks.insurance_tasks import parse_insurance_plan

    results: list[dict[str, Any]] = []
    for upload_file in upload_files:
        original_filename = secure_filename(upload_file.filename) or upload_file.filename
        extension = Path(original_filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            return jsonify(
                {
                    "error": "invalid_file_type",
                    "message": "Allowed file types: .pdf, .docx",
                    "filename": original_filename,
                }
            ), 400

        upload_batch_id = str(uuid.uuid4())
        dest_dir = os.path.join(UPLOAD_ROOT, str(user.id), upload_batch_id)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, original_filename)
        upload_file.save(dest_path)

        plan = HealthInsurancePlan(
            user_id=user.id,
            upload_batch_id=upload_batch_id,
            plan_name=_clean_plan_name(original_filename),
            raw_document_path=dest_path,
            parse_status="pending",
        )
        db.session.add(plan)
        db.session.commit()

        try:
            parse_insurance_plan.delay(plan.id)
        except Exception:
            logger.exception("Failed to queue parse_insurance_plan for plan_id=%s", plan.id)

        results.append(_upload_response(plan, original_filename))

    if len(results) == 1:
        return jsonify(results[0]), 201
    return jsonify(results), 201


@health_insurance_bp.route("/insurance-plans", methods=["GET"])
@require_auth
def list_insurance_plans():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    plans = (
        HealthInsurancePlan.query.filter_by(user_id=user.id)
        .order_by(HealthInsurancePlan.created_at.desc())
        .all()
    )
    return jsonify([_plan_summary(plan) for plan in plans])


@health_insurance_bp.route("/insurance-plans/<int:plan_id>/status", methods=["GET"])
@require_auth
def get_insurance_plan_status(plan_id: int):
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    plan = _get_owned_plan(plan_id, user.id)
    if plan is None:
        return jsonify({"error": "Plan not found"}), 404

    return jsonify(
        {
            "plan_id": plan.id,
            "parse_status": plan.parse_status,
            "parsed_at": plan.parsed_at.isoformat() if plan.parsed_at else None,
        }
    )


@health_insurance_bp.route("/insurance-plans/<int:plan_id>", methods=["DELETE"])
@require_auth
def delete_insurance_plan(plan_id: int):
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    plan = _get_owned_plan(plan_id, user.id)
    if plan is None:
        return jsonify({"error": "Plan not found"}), 404

    file_path = plan.raw_document_path
    db.session.delete(plan)
    db.session.commit()

    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except OSError:
            logger.warning("Failed to delete insurance plan file: %s", file_path)

    return jsonify({"deleted": True})


@health_insurance_bp.route("/insurance-plans/manual-create", methods=["POST"])
@require_auth
def manual_create_insurance_plan():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    plan_name = (data.get("plan_name") or "").strip()
    if not plan_name:
        return jsonify({"error": "plan_name is required"}), 400

    plan = HealthInsurancePlan(
        user_id=user.id,
        plan_name=plan_name[:200],
        parse_status="manual",
    )
    _apply_manual_fields(plan, data)
    db.session.add(plan)
    db.session.commit()

    return jsonify(_plan_summary(plan)), 201


@health_insurance_bp.route("/insurance-plans/<int:plan_id>/manual", methods=["PUT"])
@require_auth
def manual_update_insurance_plan(plan_id: int):
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    plan = _get_owned_plan(plan_id, user.id)
    if plan is None:
        return jsonify({"error": "Plan not found"}), 404

    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "Request body required"}), 400

    _apply_manual_fields(plan, data)
    db.session.commit()

    return jsonify(_plan_summary(plan))
