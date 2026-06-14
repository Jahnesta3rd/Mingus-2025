#!/usr/bin/env python3
"""Health Insurance Advisor plan upload and management API."""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from backend.api.profile_endpoints import get_db_connection
from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.models import hia_usage_profile_mixin  # noqa: F401 — ensure HIA columns
from backend.models.database import db
from backend.models.financial_setup import RecurringExpense
from backend.models.health_insurance_plan import HealthInsurancePlan
from backend.models.health_insurance_recommendation import HealthInsuranceRecommendation
from backend.models.transaction_schedule import IncomeStream
from backend.models.user_models import User
from backend.services.insurance_recommendation_service import (
    RecommendationGenerationError,
    generate_insurance_recommendation,
)

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

_MONTHLY_INCOME_MULTIPLIERS: dict[str, float] = {
    "weekly": 52 / 12,
    "biweekly": 26 / 12,
    "semimonthly": 2.0,
    "monthly": 1.0,
    "quarterly": 1 / 3,
    "annual": 1 / 12,
}

_USAGE_BODY_TO_COLUMN: dict[str, str] = {
    "coverage_type": "hia_coverage_type",
    "primary_care_visits": "hia_primary_care_visits",
    "specialist_visits": "hia_specialist_visits",
    "er_visits": "hia_er_visits",
    "planned_procedure": "hia_planned_procedure",
    "takes_rx": "hia_takes_rx",
    "rx_type": "hia_rx_type",
}


def _parse_json_object(raw: Any) -> dict:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return dict(parsed) if isinstance(parsed, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}


def _coerce_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return bool(value)


def _stream_to_monthly(amount: Decimal | float, frequency: str) -> float:
    freq = (frequency or "monthly").strip().lower()
    multiplier = _MONTHLY_INCOME_MULTIPLIERS.get(freq, 1.0)
    return float(amount) * multiplier


def _compute_gross_monthly_income(user_id: int) -> float | None:
    streams = IncomeStream.query.filter_by(user_id=user_id, is_active=True).all()
    if not streams:
        return None
    return round(sum(_stream_to_monthly(s.amount, s.frequency) for s in streams), 2)


def _build_prefill_banner(
    gross_monthly_income: float | None,
    emergency_fund: float | None,
) -> str | None:
    parts: list[str] = []
    if gross_monthly_income is not None:
        parts.append(f"${gross_monthly_income:,.0f}/month income")
    if emergency_fund is not None:
        parts.append(f"${emergency_fund:,.0f} emergency fund")
    if not parts:
        return None
    return f"Using your profile: {' · '.join(parts)}"


def _load_usage_profile_row(user_id: int) -> dict[str, Any] | None:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  up.hia_coverage_type,
                  up.hia_primary_care_visits,
                  up.hia_specialist_visits,
                  up.hia_er_visits,
                  up.hia_planned_procedure,
                  up.hia_takes_rx,
                  up.hia_rx_type,
                  up.hia_last_updated,
                  up.financial_info,
                  up.personal_info
                FROM user_profiles up
                JOIN users u ON u.email = up.email
                WHERE u.id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def _usage_profile_response(user: User) -> dict[str, Any]:
    row = _load_usage_profile_row(user.id)

    usage = {
        "coverage_type": None,
        "primary_care_visits": None,
        "specialist_visits": None,
        "er_visits": None,
        "planned_procedure": None,
        "takes_rx": None,
        "rx_type": None,
        "last_updated": None,
    }
    emergency_fund = None
    household_size = None

    if row:
        usage = {
            "coverage_type": row.get("hia_coverage_type"),
            "primary_care_visits": row.get("hia_primary_care_visits"),
            "specialist_visits": row.get("hia_specialist_visits"),
            "er_visits": row.get("hia_er_visits"),
            "planned_procedure": row.get("hia_planned_procedure"),
            "takes_rx": row.get("hia_takes_rx"),
            "rx_type": row.get("hia_rx_type"),
            "last_updated": (
                row["hia_last_updated"].isoformat()
                if row.get("hia_last_updated")
                else None
            ),
        }
        financial_info = _parse_json_object(row.get("financial_info"))
        personal_info = _parse_json_object(row.get("personal_info"))
        emergency_fund = _coerce_float(financial_info.get("emergency_fund"))
        household_size = _coerce_int(
            personal_info.get("household_size") or personal_info.get("householdSize")
        )

    gross_monthly_income = _compute_gross_monthly_income(user.id)

    return {
        "usage": usage,
        "financial_context": {
            "gross_monthly_income": gross_monthly_income,
            "emergency_fund": emergency_fund,
            "household_size": household_size,
        },
        "prefill_banner": _build_prefill_banner(gross_monthly_income, emergency_fund),
    }


def _coerce_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_user() -> User | None:
    uid = get_current_user_db_id()
    if uid is None:
        return None
    return User.query.get(uid)


def _tier_is_budget(user: User) -> bool:
    return (user.tier or "budget").strip().lower() == "budget"


def _tier_is_professional(user: User) -> bool:
    return (user.tier or "").strip().lower() == "professional"


def _get_recommendation_row(user_id: int) -> HealthInsuranceRecommendation | None:
    return HealthInsuranceRecommendation.query.filter_by(user_id=user_id).first()


def _strip_recommendation_for_budget(
    recommendation_json: dict[str, Any],
) -> dict[str, Any]:
    comparisons = recommendation_json.get("plan_comparisons") or []
    return {
        "plan_comparisons": [
            {
                "plan_name": item.get("plan_name"),
                "estimated_annual_cost": item.get("estimated_annual_cost"),
                "deductible": item.get("deductible"),
                "oop_max": item.get("oop_max"),
            }
            for item in comparisons
        ]
    }


def _recommendation_response(rec: HealthInsuranceRecommendation, user: User) -> dict[str, Any]:
    recommendation_json = rec.recommendation_json or {}
    tier_locked = _tier_is_budget(user)

    payload: dict[str, Any] = {
        "recommendation": (
            _strip_recommendation_for_budget(recommendation_json)
            if tier_locked
            else recommendation_json
        ),
        "tier_locked": tier_locked,
        "recommended_plan_id": rec.recommended_plan_id,
        "expected_annual_cost_recommended": _to_float(
            rec.expected_annual_cost_recommended
        ),
        "expected_annual_cost_runner_up": _to_float(
            rec.expected_annual_cost_runner_up
        ),
        "hsa_recommended": rec.hsa_recommended,
        "hsa_annual_benefit": _to_float(rec.hsa_annual_benefit),
        "generated_at": rec.generated_at.isoformat() if rec.generated_at else None,
        "expires_at": rec.expires_at.isoformat() if rec.expires_at else None,
    }
    if tier_locked:
        payload["upgrade_prompt"] = (
            "Upgrade to Mid-tier to see your personalized recommendation and risk analysis."
        )
    return payload


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
            if isinstance(value, str):
                plan.has_hsa_eligible = value.lower() in ("true", "1", "yes")
            else:
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


@health_insurance_bp.route("/insurance-plans/usage-profile", methods=["GET"])
@require_auth
def get_usage_profile():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify(_usage_profile_response(user))


@health_insurance_bp.route("/insurance-plans/usage-profile", methods=["POST"])
@require_auth
def save_usage_profile():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    set_clauses: list[str] = []
    params: list[Any] = []

    for body_field, column in _USAGE_BODY_TO_COLUMN.items():
        if body_field not in data:
            continue
        value = data[body_field]
        if body_field in {"primary_care_visits", "specialist_visits", "er_visits"}:
            value = _coerce_int(value)
        elif body_field in {"planned_procedure", "takes_rx"}:
            value = _coerce_bool(value)
        elif body_field == "coverage_type" and value is not None:
            value = str(value)[:20]
        elif body_field == "rx_type" and value is not None:
            value = str(value)[:20]
        set_clauses.append(f"{column} = %s")
        params.append(value)

    set_clauses.append("hia_last_updated = NOW()")
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if set_clauses:
                params.append(user.id)
                cur.execute(
                    f"""
                    UPDATE user_profiles up
                    SET {", ".join(set_clauses)}
                    FROM users u
                    WHERE up.email = u.email AND u.id = %s
                    """,
                    params,
                )
                if cur.rowcount == 0:
                    cur.execute(
                        """
                        INSERT INTO user_profiles (
                            email,
                            personal_info,
                            financial_info,
                            monthly_expenses,
                            important_dates,
                            health_wellness,
                            goals,
                            hia_coverage_type,
                            hia_primary_care_visits,
                            hia_specialist_visits,
                            hia_er_visits,
                            hia_planned_procedure,
                            hia_takes_rx,
                            hia_rx_type,
                            hia_last_updated,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            %s, '{}', '{}', '{}', '{}', '{}', '{}',
                            %s, %s, %s, %s, %s, %s, %s, NOW(),
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        """,
                        (
                            user.email,
                            data.get("coverage_type"),
                            _coerce_int(data.get("primary_care_visits")),
                            _coerce_int(data.get("specialist_visits")),
                            _coerce_int(data.get("er_visits")),
                            _coerce_bool(data.get("planned_procedure")),
                            _coerce_bool(data.get("takes_rx")),
                            data.get("rx_type"),
                        ),
                    )
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Failed to save HIA usage profile for user_id=%s", user.id)
        return jsonify({"error": "Failed to save usage profile"}), 500
    finally:
        conn.close()

    return jsonify({"saved": True})


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


@health_insurance_bp.route("/insurance-recommendation/generate", methods=["POST"])
@require_auth
def generate_insurance_recommendation_endpoint():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    now = datetime.utcnow()
    cached_row = _get_recommendation_row(user.id)
    if (
        cached_row is not None
        and cached_row.expires_at is not None
        and cached_row.expires_at > now
    ):
        return jsonify(
            {
                "recommendation": cached_row.recommendation_json,
                "cached": True,
                "expires_at": cached_row.expires_at.isoformat(),
            }
        )

    try:
        result = generate_insurance_recommendation(user.id)
    except RecommendationGenerationError as exc:
        return jsonify({"error": str(exc)}), 400

    result["cached"] = False
    return jsonify(result)


@health_insurance_bp.route("/insurance-recommendation", methods=["GET"])
@require_auth
def get_insurance_recommendation():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    rec = _get_recommendation_row(user.id)
    if rec is None:
        return jsonify({"status": "not_generated"})

    return jsonify(_recommendation_response(rec, user))


@health_insurance_bp.route("/insurance-plans/accept", methods=["POST"])
@require_auth
def accept_insurance_plan():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    if not _tier_is_professional(user):
        return jsonify(
            {
                "error": "forbidden",
                "upgrade_prompt": (
                    "Upgrade to Professional to accept a plan and add it to your budget."
                ),
            }
        ), 403

    data = request.get_json(silent=True) or {}
    plan_id = data.get("plan_id")
    if plan_id is None:
        return jsonify({"error": "plan_id is required"}), 400

    try:
        plan_id = int(plan_id)
    except (TypeError, ValueError):
        return jsonify({"error": "plan_id must be an integer"}), 400

    plan = _get_owned_plan(plan_id, user.id)
    if plan is None:
        return jsonify({"error": "Plan not found"}), 404

    monthly_amount = _to_float(plan.monthly_premium_employee)
    if monthly_amount is None:
        return jsonify({"error": "Plan has no monthly premium amount"}), 400

    expense = RecurringExpense(
        user_id=user.id,
        name=f"Health insurance — {plan.plan_name}"[:100],
        amount=plan.monthly_premium_employee,
        category="insurance",
        frequency="monthly",
        is_active=True,
        source="health_insurance_advisor",
    )
    db.session.add(expense)

    rec = _get_recommendation_row(user.id)
    if rec is not None:
        rec.accepted_plan_id = plan.id

    db.session.commit()

    return jsonify(
        {
            "accepted": True,
            "monthly_amount": monthly_amount,
            "plan_name": plan.plan_name,
            "message": (
                f"Added ${monthly_amount:,.0f}/month to your budget. "
                "Update your waterfall to see the impact."
            ),
        }
    )


@health_insurance_bp.route("/insurance-enrollment-reminder", methods=["GET"])
@require_auth
def insurance_enrollment_reminder():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    current_month = datetime.utcnow().month
    if current_month not in (10, 11, 12):
        return jsonify({"show_reminder": False})

    rec = _get_recommendation_row(user.id)
    if rec is not None and rec.generated_at is not None:
        cutoff = datetime.utcnow() - timedelta(days=30)
        if rec.generated_at > cutoff:
            return jsonify({"show_reminder": False})

    return jsonify(
        {
            "show_reminder": True,
            "message": (
                "Open enrollment is here — compare your health "
                "plan options in 5 minutes."
            ),
            "action_url": "/dashboard/benefits/insurance",
        }
    )
