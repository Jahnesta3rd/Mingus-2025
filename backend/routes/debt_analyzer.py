#!/usr/bin/env python3
"""Debt Reduction Analyzer API."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy.dialects.postgresql import insert

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.models.database import db
from backend.models.debt_profile import DebtProfile
from backend.models.user_models import User

debt_analyzer_bp = Blueprint(
    "debt_analyzer", __name__, url_prefix="/api/debt-analyzer"
)

_PROFILE_FIELDS = (
    "revolving_balance",
    "revolving_apr",
    "revolving_min_payment",
    "revolving_apr_unknown",
    "installment_balance",
    "installment_apr",
    "installment_payment",
    "federal_student_balance",
    "federal_student_payment",
    "on_idr_plan",
    "pursuing_pslf",
    "private_student_balance",
    "private_student_apr",
    "bnpl_balance",
    "bnpl_monthly_payment",
    "bnpl_active_plans",
)

_SIM_CAP_MONTHS = 600


def _resolve_user() -> User | None:
    uid = get_current_user_db_id()
    if uid is None:
        return None
    return User.query.get(uid)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _profile_to_dict(row: DebtProfile) -> dict[str, Any]:
    return {
        "has_profile": True,
        "id": row.id,
        "user_id": row.user_id,
        "revolving_balance": _to_float(row.revolving_balance),
        "revolving_apr": _to_float(row.revolving_apr),
        "revolving_min_payment": _to_float(row.revolving_min_payment),
        "revolving_apr_unknown": bool(row.revolving_apr_unknown),
        "installment_balance": _to_float(row.installment_balance),
        "installment_apr": _to_float(row.installment_apr),
        "installment_payment": _to_float(row.installment_payment),
        "federal_student_balance": _to_float(row.federal_student_balance),
        "federal_student_payment": _to_float(row.federal_student_payment),
        "on_idr_plan": bool(row.on_idr_plan),
        "pursuing_pslf": bool(row.pursuing_pslf),
        "private_student_balance": _to_float(row.private_student_balance),
        "private_student_apr": _to_float(row.private_student_apr),
        "bnpl_balance": _to_float(row.bnpl_balance),
        "bnpl_monthly_payment": _to_float(row.bnpl_monthly_payment),
        "bnpl_active_plans": row.bnpl_active_plans,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _build_debt_list(profile: DebtProfile) -> list[dict[str, Any]]:
    debts: list[dict[str, Any]] = []

    bnpl_balance = _to_float(profile.bnpl_balance) or 0.0
    if bnpl_balance > 0:
        debts.append(
            {
                "name": "Buy Now Pay Later",
                "balance": bnpl_balance,
                "apr": 0.0,
                "min_payment": _to_float(profile.bnpl_monthly_payment) or 0.0,
                "priority_zero": True,
            }
        )

    private_balance = _to_float(profile.private_student_balance) or 0.0
    if private_balance > 0:
        debts.append(
            {
                "name": "Private Student Loans",
                "balance": private_balance,
                "apr": _to_float(profile.private_student_apr) or 7.0,
                "min_payment": private_balance * 0.02,
                "priority_zero": False,
            }
        )

    revolving_balance = _to_float(profile.revolving_balance) or 0.0
    if revolving_balance > 0:
        revolving_apr = (
            22.0
            if profile.revolving_apr_unknown
            else (_to_float(profile.revolving_apr) or 22.0)
        )
        debts.append(
            {
                "name": "Credit Cards & Store Cards",
                "balance": revolving_balance,
                "apr": revolving_apr,
                "min_payment": _to_float(profile.revolving_min_payment)
                or revolving_balance * 0.02,
                "priority_zero": False,
            }
        )

    installment_balance = _to_float(profile.installment_balance) or 0.0
    if installment_balance > 0:
        debts.append(
            {
                "name": "Auto & Personal Loans",
                "balance": installment_balance,
                "apr": _to_float(profile.installment_apr) or 6.0,
                "min_payment": _to_float(profile.installment_payment) or 0.0,
                "priority_zero": False,
            }
        )

    return debts


def _federal_block(profile: DebtProfile) -> dict[str, Any]:
    pursuing_pslf = bool(profile.pursuing_pslf)
    on_idr_plan = bool(profile.on_idr_plan)
    if pursuing_pslf:
        recommendation = (
            "You are pursuing PSLF — do not aggressively pay down "
            "federal loans. Make minimum IDR payments only."
        )
    elif on_idr_plan:
        recommendation = (
            "Federal loans qualify for income-driven repayment. "
            "Consider IDR before accelerating payoff."
        )
    else:
        recommendation = (
            "Federal loans may qualify for income-driven repayment "
            "or forgiveness programs."
        )

    return {
        "balance": _to_float(profile.federal_student_balance) or 0.0,
        "monthly_payment": _to_float(profile.federal_student_payment) or 0.0,
        "on_idr_plan": on_idr_plan,
        "pursuing_pslf": pursuing_pslf,
        "recommendation": recommendation,
    }


def _extra_targets(
    debts: list[dict[str, Any]], strategy: str, month: int
) -> list[dict[str, Any]]:
    active = [d for d in debts if d["balance"] > 0.005]
    if not active:
        return []

    priority_zero = [d for d in active if d.get("priority_zero")]
    regular = [d for d in active if not d.get("priority_zero")]

    ordered: list[dict[str, Any]] = []
    if priority_zero:
        ordered.extend(sorted(priority_zero, key=lambda d: d["balance"]))

    use_snowball = strategy == "snowball" or (
        strategy == "hybrid" and month <= 3
    )
    if regular:
        if use_snowball:
            ordered.extend(sorted(regular, key=lambda d: d["balance"]))
        else:
            ordered.extend(sorted(regular, key=lambda d: d["apr"], reverse=True))

    return ordered


def _simulate_strategy(
    debts: list[dict[str, Any]],
    monthly_budget: float,
    strategy: str,
    *,
    minimum_only: bool = False,
) -> dict[str, Any]:
    working = deepcopy(debts)
    payoff_order: list[str] = []
    monthly_schedule: list[dict[str, Any]] = []
    total_interest = 0.0
    payoff_months = 0

    for month in range(1, _SIM_CAP_MONTHS + 1):
        if not any(d["balance"] > 0.005 for d in working):
            break

        month_interest = 0.0
        for debt in working:
            if debt["balance"] <= 0.005:
                continue
            interest = debt["balance"] * (debt["apr"] / 100.0 / 12.0)
            debt["balance"] += interest
            month_interest += interest
            total_interest += interest

        remaining = monthly_budget
        for debt in working:
            if debt["balance"] <= 0.005 or remaining <= 0:
                continue
            payment = min(debt["min_payment"], debt["balance"], remaining)
            if payment > 0:
                debt["balance"] -= payment
                remaining -= payment

        if not minimum_only and remaining > 0:
            for debt in _extra_targets(working, strategy, month):
                if remaining <= 0:
                    break
                if debt["balance"] <= 0.005:
                    continue
                payment = min(debt["balance"], remaining)
                debt["balance"] -= payment
                remaining -= payment

        for debt in working:
            if debt["balance"] <= 0.005:
                debt["balance"] = 0.0
                if debt["name"] not in payoff_order:
                    payoff_order.append(debt["name"])

        remaining_total = sum(d["balance"] for d in working)
        monthly_schedule.append(
            {
                "month": month,
                "remaining_total": round(remaining_total, 2),
                "interest_paid": round(month_interest, 2),
            }
        )
        payoff_months = month

        if remaining_total <= 0.005:
            break

    return {
        "payoff_months": payoff_months,
        "total_interest": round(total_interest, 2),
        "payoff_order": payoff_order,
        "monthly_schedule": monthly_schedule,
    }


def _pick_recommended_strategy(
    avalanche: dict[str, Any], snowball: dict[str, Any]
) -> str:
    interest_saved = snowball["total_interest"] - avalanche["total_interest"]
    months_saved = avalanche["payoff_months"] - snowball["payoff_months"]

    if interest_saved >= 500:
        return "avalanche"
    if months_saved >= 6:
        return "snowball"
    return "hybrid"


@debt_analyzer_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    row = DebtProfile.query.filter_by(user_id=user.id).first()
    if row is None:
        return jsonify({"has_profile": False}), 200
    return jsonify(_profile_to_dict(row)), 200


@debt_analyzer_bp.route("/profile", methods=["POST"])
@require_auth
def upsert_profile():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    body = request.get_json(silent=True) or {}
    updates = {field: body[field] for field in _PROFILE_FIELDS if field in body}
    now = datetime.utcnow()

    insert_values: dict[str, Any] = {"user_id": user.id, "created_at": now, "updated_at": now}
    insert_values.update(updates)

    update_values = {key: insert_values[key] for key in updates}
    update_values["updated_at"] = now

    stmt = insert(DebtProfile.__table__).values(**insert_values)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_debt_profiles_user_id",
        set_=update_values,
    )
    db.session.execute(stmt)
    db.session.commit()

    row = DebtProfile.query.filter_by(user_id=user.id).first()
    profile = _profile_to_dict(row) if row else {"has_profile": False}
    return jsonify({"success": True, "profile": profile}), 200


@debt_analyzer_bp.route("/calculate", methods=["POST"])
@require_auth
def calculate():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    profile = DebtProfile.query.filter_by(user_id=user.id).first()
    if profile is None:
        return (
            jsonify(
                {
                    "error": "no_profile",
                    "message": "Complete your debt profile first",
                }
            ),
            400,
        )

    body = request.get_json(silent=True) or {}
    monthly_payment = body.get("monthly_payment")
    if monthly_payment is None:
        return jsonify({"error": "monthly_payment required"}), 400

    try:
        monthly_payment = float(monthly_payment)
        extra_payment = float(body.get("extra_payment") or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid payment amounts"}), 400

    total_budget = monthly_payment + extra_payment
    debts = _build_debt_list(profile)
    federal = _federal_block(profile)

    analyzer_debt = sum(d["balance"] for d in debts)
    federal_balance = federal["balance"]
    total_debt = analyzer_debt + federal_balance

    avalanche = _simulate_strategy(debts, total_budget, "avalanche")
    snowball = _simulate_strategy(debts, total_budget, "snowball")
    hybrid = _simulate_strategy(debts, total_budget, "hybrid")
    minimum_only = _simulate_strategy(debts, total_budget, "avalanche", minimum_only=True)

    best_interest = min(
        avalanche["total_interest"],
        snowball["total_interest"],
        hybrid["total_interest"],
    )
    interest_savings_vs_minimum = round(
        minimum_only["total_interest"] - best_interest, 2
    )

    return jsonify(
        {
            "total_debt": round(total_debt, 2),
            "analyzer_debt": round(analyzer_debt, 2),
            "monthly_payment": round(total_budget, 2),
            "strategies": {
                "avalanche": avalanche,
                "snowball": snowball,
                "hybrid": hybrid,
            },
            "federal_student_loans": federal,
            "bnpl_flagged": (_to_float(profile.bnpl_balance) or 0.0) > 0,
            "recommended_strategy": _pick_recommended_strategy(avalanche, snowball),
            "interest_savings_vs_minimum": interest_savings_vs_minimum,
            "partial_data": bool(profile.revolving_apr_unknown),
        }
    ), 200
