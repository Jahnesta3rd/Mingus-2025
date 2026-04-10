#!/usr/bin/env python3
"""
Financial Setup API – recurring expenses and user income (onboarding / weekly context).
"""

import json
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request, g
from flask_cors import cross_origin
from loguru import logger
from sqlalchemy import text

from backend.auth.decorators import require_auth, require_csrf
from backend.models.database import db
from backend.models.financial_setup import RecurringExpense, UserIncome
from backend.models.user_models import User

financial_setup_bp = Blueprint(
    "financial_setup",
    __name__,
    url_prefix="/api/financial-setup",
)

ALLOWED_INCOME_FREQ = frozenset({"monthly", "biweekly", "weekly", "annual"})
ALLOWED_EXPENSE_FREQ = frozenset({"monthly", "weekly", "biweekly", "annual"})
# DB CHECK on recurring_expenses.category — canonical values
ALLOWED_DB_EXPENSE_CATEGORIES = frozenset(
    {
        "housing",
        "transportation",
        "insurance",
        "debt",
        "subscription",
        "utilities",
        "other",
        "relationship",
    }
)
# Legacy API aliases → canonical DB value
_EXPENSE_CATEGORY_ALIASES = {
    "transport": "transportation",
    "food": "other",
    "subscriptions": "subscription",
    "healthcare": "insurance",
    "childcare": "other",
    "debt_payment": "debt",
}


def _normalize_expense_category(cat: str) -> str | None:
    c = (cat or "").strip().lower()
    if c in ALLOWED_DB_EXPENSE_CATEGORIES:
        return c
    return _EXPENSE_CATEGORY_ALIASES.get(c)


def _current_user_row() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _to_decimal_amount(v) -> Decimal | None:
    try:
        if isinstance(v, bool):
            return None
        d = Decimal(str(v))
        return d
    except (InvalidOperation, TypeError, ValueError):
        return None


def _num(v, *, allow_none=False):
    if v is None and allow_none:
        return None
    if isinstance(v, bool):
        raise ValueError("invalid numeric")
    try:
        return float(v)
    except (TypeError, ValueError):
        raise ValueError("invalid numeric")


@financial_setup_bp.route("/", methods=["GET", "OPTIONS"])
@cross_origin()
@require_auth
def get_setup():
    """Placeholder: return empty financial setup data."""
    if request.method == "OPTIONS":
        return jsonify({}), 200
    return jsonify({"success": True, "income": None, "recurring_expenses": []}), 200


@financial_setup_bp.route("/income", methods=["GET", "POST", "OPTIONS"])
@cross_origin()
@require_auth
@require_csrf
def financial_setup_income():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user = _current_user_row()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if request.method == "GET":
        rows = (
            UserIncome.query.filter_by(user_id=user.id, is_active=True)
            .order_by(UserIncome.created_at.asc())
            .all()
        )
        out = []
        for r in rows:
            out.append(
                {
                    "id": str(r.id),
                    "source_name": r.source_name,
                    "amount": float(r.amount),
                    "frequency": r.frequency,
                    "pay_day": r.pay_day,
                    "is_active": r.is_active,
                }
            )
        return jsonify({"income": out}), 200

    # POST
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400
    sources = data.get("sources")
    if not isinstance(sources, list):
        return jsonify({"error": "sources must be an array"}), 400

    for item in sources:
        if not isinstance(item, dict):
            return jsonify({"error": "each source must be an object"}), 400
        sn = (item.get("source_name") or "").strip()
        if not sn:
            return jsonify({"error": "source_name is required and must be non-empty"}), 400
        freq = (item.get("frequency") or "").lower()
        if freq not in ALLOWED_INCOME_FREQ:
            return jsonify({"error": f"invalid frequency: {freq!r}"}), 400
        amt = _to_decimal_amount(item.get("amount"))
        if amt is None or amt <= 0:
            return jsonify({"error": "amount must be a number > 0"}), 400
        pd = item.get("pay_day")
        if pd is not None:
            try:
                pd = int(pd)
            except (TypeError, ValueError):
                return jsonify({"error": "pay_day must be an integer or null"}), 400
            if pd < 1 or pd > 31:
                return jsonify({"error": "pay_day must be between 1 and 31"}), 400
        else:
            pd = None

    try:
        for row in UserIncome.query.filter_by(user_id=user.id).all():
            row.is_active = False
        for item in sources:
            sn = (item.get("source_name") or "").strip()
            freq = (item.get("frequency") or "").lower()
            amt = _to_decimal_amount(item.get("amount"))
            pd = item.get("pay_day")
            if pd is not None:
                pd = int(pd)
            db.session.add(
                UserIncome(
                    user_id=user.id,
                    source_name=sn,
                    amount=amt,
                    frequency=freq,
                    pay_day=pd,
                    is_active=True,
                )
            )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("financial_setup_income POST failed for user {}: {}", user.id, e)
        return jsonify({"error": "Internal server error"}), 500

    return jsonify({"success": True, "sources_saved": len(sources)}), 200


@financial_setup_bp.route("/expenses", methods=["GET", "POST", "OPTIONS"])
@cross_origin()
@require_auth
@require_csrf
def financial_setup_expenses():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user = _current_user_row()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if request.method == "GET":
        rows = (
            RecurringExpense.query.filter_by(user_id=user.id, is_active=True)
            .order_by(RecurringExpense.created_at.asc())
            .all()
        )
        out = []
        for r in rows:
            out.append(
                {
                    "id": str(r.id),
                    "name": r.name,
                    "amount": float(r.amount),
                    "category": r.category,
                    "frequency": r.frequency,
                    "due_day": r.due_day,
                }
            )
        return jsonify({"expenses": out}), 200

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400
    expenses = data.get("expenses")
    if not isinstance(expenses, list):
        return jsonify({"error": "expenses must be an array"}), 400

    for item in expenses:
        if not isinstance(item, dict):
            return jsonify({"error": "each expense must be an object"}), 400
        name = (item.get("name") or "").strip()
        if not name:
            return jsonify({"error": "name is required and must be non-empty"}), 400
        cat_raw = item.get("category") or ""
        db_cat = _normalize_expense_category(str(cat_raw))
        if db_cat is None:
            return jsonify({"error": f"invalid category: {cat_raw!r}"}), 400
        freq = (item.get("frequency") or "").lower()
        if freq not in ALLOWED_EXPENSE_FREQ:
            return jsonify({"error": f"invalid frequency: {freq!r}"}), 400
        amt = _to_decimal_amount(item.get("amount"))
        if amt is None or amt <= 0:
            return jsonify({"error": "amount must be a number > 0"}), 400
        dd = item.get("due_day")
        if dd is not None:
            try:
                dd = int(dd)
            except (TypeError, ValueError):
                return jsonify({"error": "due_day must be an integer or null"}), 400
            if dd < 1 or dd > 31:
                return jsonify({"error": "due_day must be between 1 and 31"}), 400
        else:
            dd = None

    try:
        for row in RecurringExpense.query.filter_by(user_id=user.id).all():
            row.is_active = False
        for item in expenses:
            name = (item.get("name") or "").strip()
            cat_raw = item.get("category") or ""
            db_cat = _normalize_expense_category(str(cat_raw))
            if db_cat is None:
                raise ValueError(f"invalid category: {cat_raw!r}")
            freq = (item.get("frequency") or "").lower()
            amt = _to_decimal_amount(item.get("amount"))
            dd = item.get("due_day")
            if dd is not None:
                dd = int(dd)
            db.session.add(
                RecurringExpense(
                    user_id=user.id,
                    name=name,
                    amount=amt,
                    category=db_cat,
                    frequency=freq,
                    due_day=dd,
                    is_active=True,
                    source=None,
                )
            )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("financial_setup_expenses POST failed for user {}: {}", user.id, e)
        return jsonify({"error": "Internal server error"}), 500

    return jsonify({"success": True, "expenses_saved": len(expenses)}), 200


def _merge_financial_position(prev: dict, body: dict) -> dict:
    """Merge only keys present in body; validate each."""
    merged = dict(prev)
    if "emergency_fund" in body:
        v = _num(body["emergency_fund"])
        if v < 0:
            raise ValueError("emergency_fund must be >= 0")
        merged["emergency_fund"] = v
    if "credit_score" in body:
        v = _num(body["credit_score"])
        if v < 300 or v > 850:
            raise ValueError("credit_score must be between 300 and 850")
        merged["credit_score"] = v
    if "total_debt" in body:
        merged["total_debt"] = _num(body["total_debt"])
    if "savings_balance" in body:
        merged["savings_balance"] = _num(body["savings_balance"])
    if "net_worth" in body and body["net_worth"] is not None:
        merged["net_worth"] = _num(body["net_worth"])
    elif "net_worth" in body:
        merged["net_worth"] = None
    return merged


@financial_setup_bp.route("/position", methods=["GET", "POST", "OPTIONS"])
@cross_origin()
@require_auth
@require_csrf
def financial_setup_position():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    user = _current_user_row()
    if not user:
        return jsonify({"error": "User not found"}), 404

    email = (user.email or "").strip().lower()
    if not email:
        return jsonify({"error": "User email missing"}), 400

    keys = ("emergency_fund", "credit_score", "total_debt", "savings_balance", "net_worth")

    if request.method == "GET":
        try:
            row = db.session.execute(
                text("SELECT financial_info FROM user_profiles WHERE email = :email"),
                {"email": email},
            ).fetchone()
            fi = {}
            if row and row[0]:
                try:
                    fi = json.loads(row[0])
                    if not isinstance(fi, dict):
                        fi = {}
                except (TypeError, ValueError):
                    fi = {}
            payload = {k: fi.get(k) for k in keys}
            return jsonify(payload), 200
        except Exception as e:
            logger.error("financial_setup_position GET failed for {}: {}", email, e)
            return jsonify({"error": "Internal server error"}), 500

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    try:
        row = db.session.execute(
            text("SELECT financial_info FROM user_profiles WHERE email = :email"),
            {"email": email},
        ).fetchone()
        prev = {}
        if row and row[0]:
            try:
                prev = json.loads(row[0])
                if not isinstance(prev, dict):
                    prev = {}
            except (TypeError, ValueError):
                prev = {}
        merged = _merge_financial_position(prev, data)
        fi_json = json.dumps(merged)
        upd = db.session.execute(
            text(
                "UPDATE user_profiles SET financial_info = :fi, "
                "updated_at = CURRENT_TIMESTAMP WHERE email = :email"
            ),
            {"fi": fi_json, "email": email},
        )
        if upd.rowcount == 0:
            db.session.execute(
                text(
                    "INSERT INTO user_profiles (email, first_name, personal_info, "
                    "financial_info, monthly_expenses, important_dates, health_wellness, "
                    "goals, created_at, updated_at) "
                    "VALUES (:email, NULL, '{}', :fi, '{}', '{}', '{}', '{}', "
                    "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {"email": email, "fi": fi_json},
            )
        db.session.commit()
    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error("financial_setup_position POST failed for {}: {}", email, e)
        return jsonify({"error": "Internal server error"}), 500

    return jsonify({"success": True}), 200
