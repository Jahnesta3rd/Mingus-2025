#!/usr/bin/env python3
"""
Financial Setup API – recurring expenses and user income (weekly check-in context).
"""

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

from backend.auth.decorators import require_auth

financial_setup_bp = Blueprint(
    "financial_setup",
    __name__,
    url_prefix="/api/financial-setup",
)


@financial_setup_bp.route("/", methods=["GET", "OPTIONS"])
@cross_origin()
@require_auth
def get_setup():
    """Placeholder: return empty financial setup data."""
    if request.method == "OPTIONS":
        return jsonify({}), 200
    return jsonify({"success": True, "income": None, "recurring_expenses": []}), 200
