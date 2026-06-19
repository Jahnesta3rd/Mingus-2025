#!/usr/bin/env python3
"""Admin PMF dashboard API: user growth and product-market fit signals."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify
from sqlalchemy import func, inspect

from backend.auth.decorators import require_auth
from backend.models.database import db
from backend.models.feedback import NPSSurvey, SeanEllisSurvey
from backend.models.user_models import User

admin_pmf_bp = Blueprint("admin_pmf", __name__, url_prefix="/api/admin/pmf")
admin_sean_ellis_bp = Blueprint("admin_sean_ellis", __name__, url_prefix="/api/admin/sean-ellis")


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
    try:
        total = db.session.query(SeanEllisSurvey).count()
        if total < 5:
            return None
        vd = (
            db.session.query(SeanEllisSurvey)
            .filter_by(response="very_disappointed")
            .count()
        )
        return round((vd / total) * 100, 1)
    except Exception:
        return None


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


@admin_sean_ellis_bp.route("/results", methods=["GET"])
@require_auth
def sean_ellis_results():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin_user(user):
        return _admin_forbidden()

    total = db.session.query(SeanEllisSurvey).count()
    very_disappointed = (
        db.session.query(SeanEllisSurvey).filter_by(response="very_disappointed").count()
    )
    somewhat_disappointed = (
        db.session.query(SeanEllisSurvey)
        .filter_by(response="somewhat_disappointed")
        .count()
    )
    not_disappointed = (
        db.session.query(SeanEllisSurvey).filter_by(response="not_disappointed").count()
    )
    no_longer_use = (
        db.session.query(SeanEllisSurvey).filter_by(response="no_longer_use").count()
    )
    very_disappointed_pct = (
        round((very_disappointed / total) * 100, 1) if total >= 5 else None
    )

    return (
        jsonify(
            {
                "total_responses": total,
                "very_disappointed": very_disappointed,
                "somewhat_disappointed": somewhat_disappointed,
                "not_disappointed": not_disappointed,
                "no_longer_use": no_longer_use,
                "very_disappointed_pct": very_disappointed_pct,
            }
        ),
        200,
    )
