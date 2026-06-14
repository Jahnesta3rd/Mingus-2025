#!/usr/bin/env python3
"""New Parent checklist financial impact routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.auth.decorators import current_user, require_auth
from backend.models.financial_setup import RecurringExpense
from backend.models.user_models import User
from backend.services.parent_checklist_impact_service import (
    SOURCE,
    apply_checklist_item_impact,
)

parent_checklist_bp = Blueprint(
    "parent_checklist",
    __name__,
    url_prefix="/api/user/checklist",
)


@parent_checklist_bp.route("/apply-impact", methods=["POST"])
@require_auth
def apply_impact():
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    if not item_id or not isinstance(item_id, str) or not item_id.strip():
        return jsonify({"error": "item_id required"}), 400

    amount_override = data.get("amount_override")
    if amount_override is not None:
        try:
            amount_override = float(amount_override)
        except (TypeError, ValueError):
            amount_override = None

    result = apply_checklist_item_impact(user.id, item_id.strip(), amount_override)
    return jsonify(result), 200


@parent_checklist_bp.route("/impact-summary", methods=["GET"])
@require_auth
def impact_summary():
    user: User | None = current_user
    if user is None:
        return jsonify({"error": "User not found"}), 404

    rows = (
        RecurringExpense.query.filter_by(user_id=user.id, source=SOURCE)
        .order_by(RecurringExpense.created_at.asc())
        .all()
    )
    items = [
        {
            "name": row.name,
            "amount": float(row.amount),
            "frequency": row.frequency,
            "category": row.category,
        }
        for row in rows
    ]
    monthly_total = sum(item["amount"] for item in items)
    return jsonify(
        {
            "items": items,
            "monthly_total": monthly_total,
            "annual_total": monthly_total * 12,
        }
    ), 200
