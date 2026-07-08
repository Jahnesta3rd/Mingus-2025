#!/usr/bin/env python3
"""Expense audit API — 90-day spending analysis."""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, jsonify, request

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.services.expense_audit_service import ExpenseAuditAnalyzer

logger = logging.getLogger(__name__)

expense_audit_bp = Blueprint("expense_audit", __name__, url_prefix="/api/expense-audit")


def _parse_uuid(value, field: str) -> UUID:
    if not value:
        raise ValueError(f"{field} is required")
    try:
        return UUID(str(value).strip())
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"{field} must be a valid UUID") from exc


@expense_audit_bp.route("/analyze", methods=["POST"])
@require_auth
def analyze():
    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    body = request.get_json(silent=True) or {}
    days_lookback = int(body.get("days_lookback") or 90)
    if days_lookback <= 0:
        return jsonify({"error": "invalid_input", "message": "days_lookback must be positive"}), 400

    analyzer = ExpenseAuditAnalyzer()
    try:
        payload = analyzer.analyze_expenses(user_id, days_lookback=days_lookback)
    except ValueError as exc:
        return jsonify({"error": "invalid_input", "message": str(exc)}), 400
    except Exception as exc:
        logger.exception("expense audit analyze failed user_id=%s", user_id)
        return jsonify({"error": "analysis_failed", "message": str(exc)}), 500

    return jsonify(payload), 200
