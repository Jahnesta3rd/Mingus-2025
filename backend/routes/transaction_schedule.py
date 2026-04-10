#!/usr/bin/env python3
"""API for scheduled income streams and recurring expenses (cash forecast inputs)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from backend.auth.decorators import require_auth
from backend.models.database import db
from backend.models.transaction_schedule import IncomeStream, ScheduledExpense
from backend.models.user_models import User

transaction_schedule_bp = Blueprint("transaction_schedule", __name__)

_FREQUENCIES = frozenset({"weekly", "biweekly", "semimonthly", "monthly"})
_INCOME_TYPES = frozenset(
    {"earned", "child_support", "alimony", "gig", "rental", "other"}
)
_EXPENSE_CATEGORIES = frozenset(
    {
        "housing",
        "transportation",
        "debt",
        "utilities",
        "subscription",
        "family_support",
        "child_support",
        "alimony",
        "caregiving",
        "other",
    }
)


def _user_from_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _parse_json() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _parse_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if len(s) >= 10:
            s = s[:10]
        try:
            return date.fromisoformat(s)
        except ValueError:
            return None
    return None


def _parse_amount(value) -> Decimal | None:
    if value is None:
        return None
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if d < 0:
        return None
    return d.quantize(Decimal("0.01"))


def _income_dict(row: IncomeStream) -> dict:
    return {
        "id": str(row.id),
        "user_id": row.user_id,
        "label": row.label,
        "amount": str(row.amount),
        "frequency": row.frequency,
        "next_date": row.next_date.isoformat() if row.next_date else None,
        "income_type": row.income_type,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() + "Z" if row.created_at else None,
    }


def _expense_dict(row: ScheduledExpense) -> dict:
    return {
        "id": str(row.id),
        "user_id": row.user_id,
        "label": row.label,
        "amount": str(row.amount),
        "category": row.category,
        "frequency": row.frequency,
        "due_day": row.due_day,
        "next_date": row.next_date.isoformat() if row.next_date else None,
        "is_active": row.is_active,
        "created_at": row.created_at.isoformat() + "Z" if row.created_at else None,
    }


def _income_for_user(income_id: uuid.UUID, user: User) -> IncomeStream | None:
    row = db.session.get(IncomeStream, income_id)
    if not row or row.user_id != user.id:
        return None
    return row


def _expense_for_user(expense_id: uuid.UUID, user: User) -> ScheduledExpense | None:
    row = db.session.get(ScheduledExpense, expense_id)
    if not row or row.user_id != user.id:
        return None
    return row


@transaction_schedule_bp.route("/income", methods=["GET"])
@require_auth
def list_income():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    rows = (
        IncomeStream.query.filter_by(user_id=user.id, is_active=True)
        .order_by(IncomeStream.created_at.asc())
        .all()
    )
    return jsonify({"income": [_income_dict(r) for r in rows]})


@transaction_schedule_bp.route("/income", methods=["POST"])
@require_auth
def create_income():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    body = _parse_json()
    label = body.get("label")
    if not isinstance(label, str) or not label.strip():
        return jsonify({"error": "label is required (non-empty string)"}), 400
    label = label.strip()[:100]
    amount = _parse_amount(body.get("amount"))
    if amount is None:
        return jsonify({"error": "amount is required (non-negative number)"}), 400
    frequency = body.get("frequency")
    if not isinstance(frequency, str) or frequency not in _FREQUENCIES:
        return jsonify(
            {
                "error": "frequency must be one of: weekly, biweekly, semimonthly, monthly"
            }
        ), 400
    next_d = _parse_date(body.get("next_date"))
    if next_d is None:
        return jsonify({"error": "next_date is required (ISO date)"}), 400
    income_type = body.get("income_type", "earned")
    if not isinstance(income_type, str) or income_type not in _INCOME_TYPES:
        return jsonify(
            {
                "error": "income_type must be one of: earned, child_support, alimony, gig, rental, other"
            }
        ), 400

    row = IncomeStream(
        user_id=user.id,
        label=label,
        amount=amount,
        frequency=frequency,
        next_date=next_d,
        income_type=income_type,
        is_active=True,
    )
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Could not create income stream"}), 409
    return jsonify(_income_dict(row)), 201


@transaction_schedule_bp.route("/income/<uuid:income_id>", methods=["PUT"])
@require_auth
def update_income(income_id: uuid.UUID):
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    row = _income_for_user(income_id, user)
    if not row:
        return jsonify({"error": "Income stream not found"}), 404
    body = _parse_json()
    if "label" in body:
        label = body.get("label")
        if not isinstance(label, str) or not label.strip():
            return jsonify({"error": "label must be a non-empty string"}), 400
        row.label = label.strip()[:100]
    if "amount" in body:
        amount = _parse_amount(body.get("amount"))
        if amount is None:
            return jsonify({"error": "amount must be a non-negative number"}), 400
        row.amount = amount
    if "frequency" in body:
        frequency = body.get("frequency")
        if not isinstance(frequency, str) or frequency not in _FREQUENCIES:
            return jsonify(
                {
                    "error": "frequency must be one of: weekly, biweekly, semimonthly, monthly"
                }
            ), 400
        row.frequency = frequency
    if "next_date" in body:
        next_d = _parse_date(body.get("next_date"))
        if next_d is None:
            return jsonify({"error": "next_date must be an ISO date"}), 400
        row.next_date = next_d
    if "income_type" in body:
        income_type = body.get("income_type")
        if not isinstance(income_type, str) or income_type not in _INCOME_TYPES:
            return jsonify(
                {
                    "error": "income_type must be one of: earned, child_support, alimony, gig, rental, other"
                }
            ), 400
        row.income_type = income_type
    if "is_active" in body:
        active = body.get("is_active")
        if not isinstance(active, bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        row.is_active = active
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Could not update income stream"}), 409
    return jsonify(_income_dict(row))


@transaction_schedule_bp.route("/income/<uuid:income_id>", methods=["DELETE"])
@require_auth
def delete_income(income_id: uuid.UUID):
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    row = _income_for_user(income_id, user)
    if not row:
        return jsonify({"error": "Income stream not found"}), 404
    row.is_active = False
    db.session.commit()
    return jsonify({"ok": True, "id": str(row.id)})


@transaction_schedule_bp.route("/expenses", methods=["GET"])
@require_auth
def list_expenses():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    rows = (
        ScheduledExpense.query.filter_by(user_id=user.id, is_active=True)
        .order_by(ScheduledExpense.created_at.asc())
        .all()
    )
    return jsonify({"expenses": [_expense_dict(r) for r in rows]})


@transaction_schedule_bp.route("/expenses", methods=["POST"])
@require_auth
def create_expense():
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    body = _parse_json()
    label = body.get("label")
    if not isinstance(label, str) or not label.strip():
        return jsonify({"error": "label is required (non-empty string)"}), 400
    label = label.strip()[:100]
    amount = _parse_amount(body.get("amount"))
    if amount is None:
        return jsonify({"error": "amount is required (non-negative number)"}), 400
    category = body.get("category")
    if not isinstance(category, str) or category not in _EXPENSE_CATEGORIES:
        return jsonify(
            {
                "error": "category must be one of: housing, transportation, debt, utilities, subscription, family_support, child_support, alimony, caregiving, other"
            }
        ), 400
    frequency = body.get("frequency")
    if not isinstance(frequency, str) or frequency not in _FREQUENCIES:
        return jsonify(
            {
                "error": "frequency must be one of: weekly, biweekly, semimonthly, monthly"
            }
        ), 400
    due_day = body.get("due_day")
    if not isinstance(due_day, int) or due_day < 1 or due_day > 31:
        return jsonify({"error": "due_day must be an integer 1–31"}), 400
    next_d = _parse_date(body.get("next_date"))
    if next_d is None:
        return jsonify({"error": "next_date is required (ISO date)"}), 400

    row = ScheduledExpense(
        user_id=user.id,
        label=label,
        amount=amount,
        category=category,
        frequency=frequency,
        due_day=due_day,
        next_date=next_d,
        is_active=True,
    )
    db.session.add(row)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Could not create recurring expense"}), 409
    return jsonify(_expense_dict(row)), 201


@transaction_schedule_bp.route("/expenses/<uuid:expense_id>", methods=["PUT"])
@require_auth
def update_expense(expense_id: uuid.UUID):
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    row = _expense_for_user(expense_id, user)
    if not row:
        return jsonify({"error": "Recurring expense not found"}), 404
    body = _parse_json()
    if "label" in body:
        label = body.get("label")
        if not isinstance(label, str) or not label.strip():
            return jsonify({"error": "label must be a non-empty string"}), 400
        row.label = label.strip()[:100]
    if "amount" in body:
        amount = _parse_amount(body.get("amount"))
        if amount is None:
            return jsonify({"error": "amount must be a non-negative number"}), 400
        row.amount = amount
    if "category" in body:
        category = body.get("category")
        if not isinstance(category, str) or category not in _EXPENSE_CATEGORIES:
            return jsonify(
                {
                    "error": "category must be one of: housing, transportation, debt, utilities, subscription, family_support, child_support, alimony, caregiving, other"
                }
            ), 400
        row.category = category
    if "frequency" in body:
        frequency = body.get("frequency")
        if not isinstance(frequency, str) or frequency not in _FREQUENCIES:
            return jsonify(
                {
                    "error": "frequency must be one of: weekly, biweekly, semimonthly, monthly"
                }
            ), 400
        row.frequency = frequency
    if "due_day" in body:
        due_day = body.get("due_day")
        if not isinstance(due_day, int) or due_day < 1 or due_day > 31:
            return jsonify({"error": "due_day must be an integer 1–31"}), 400
        row.due_day = due_day
    if "next_date" in body:
        next_d = _parse_date(body.get("next_date"))
        if next_d is None:
            return jsonify({"error": "next_date must be an ISO date"}), 400
        row.next_date = next_d
    if "is_active" in body:
        active = body.get("is_active")
        if not isinstance(active, bool):
            return jsonify({"error": "is_active must be a boolean"}), 400
        row.is_active = active
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Could not update recurring expense"}), 409
    return jsonify(_expense_dict(row))


@transaction_schedule_bp.route("/expenses/<uuid:expense_id>", methods=["DELETE"])
@require_auth
def delete_expense(expense_id: uuid.UUID):
    user = _user_from_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    row = _expense_for_user(expense_id, user)
    if not row:
        return jsonify({"error": "Recurring expense not found"}), 404
    row.is_active = False
    db.session.commit()
    return jsonify({"ok": True, "id": str(row.id)})
