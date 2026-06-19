#!/usr/bin/env python3
"""Admin PMF dashboard API: user growth and product-market fit signals."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify
from sqlalchemy import func, inspect, text

from backend.auth.decorators import require_auth
from backend.models.database import db
from backend.models.feedback import NPSSurvey
from backend.models.user_models import User

admin_pmf_bp = Blueprint("admin_pmf", __name__, url_prefix="/api/admin/pmf")


def _user_for_jwt():
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _is_admin_user(user: User | None) -> bool:
    if not user:
        return False
    if getattr(user, "is_admin", False):
        return True
    role = (getattr(user, "role", None) or "").lower()
    return role == "admin"


def _admin_forbidden():
    return jsonify({"error": "Admin access required"}), 403


def _table_exists(table_name: str) -> bool:
    return inspect(db.engine).has_table(table_name)


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    cols = {c["name"] for c in inspect(db.engine).get_columns(table_name)}
    return column_name in cols


def _count_users_since(days: int) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return User.query.filter(User.created_at >= cutoff).count()


def _organic_signups() -> int | None:
    if not _column_exists("users", "acquisition_source"):
        return None
    return User.query.filter(User.acquisition_source.isnot(None)).count()


def _paid_signups() -> int | None:
    if not _column_exists("users", "tier"):
        return None
    return User.query.filter(User.tier != "budget").count()


def _avg_nps() -> float | None:
    avg = db.session.query(func.avg(NPSSurvey.score)).scalar()
    if avg is None:
        return None
    return round(float(avg), 1)


def _very_disappointed_pct() -> float | None:
    if not _table_exists("sean_ellis_survey"):
        return None
    if not _column_exists("sean_ellis_survey", "response"):
        return None
    total = db.session.execute(
        text("SELECT COUNT(*) FROM sean_ellis_survey")
    ).scalar()
    if not total:
        return None
    very_disappointed = db.session.execute(
        text(
            "SELECT COUNT(*) FROM sean_ellis_survey "
            "WHERE response = 'very_disappointed'"
        )
    ).scalar()
    return round(100.0 * float(very_disappointed) / float(total), 1)


@admin_pmf_bp.route("/overview", methods=["GET"])
@require_auth
def overview():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin_user(user):
        return _admin_forbidden()

    total_users = User.query.count()

    return (
        jsonify(
            {
                "total_users": total_users,
                "users_last_7_days": _count_users_since(7),
                "users_last_30_days": _count_users_since(30),
                "organic_signups": _organic_signups(),
                "paid_signups": _paid_signups(),
                "avg_nps": _avg_nps(),
                "very_disappointed_pct": _very_disappointed_pct(),
            }
        ),
        200,
    )
