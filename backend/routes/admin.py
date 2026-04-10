#!/usr/bin/env python3
"""Admin-only API routes (aggregate metrics)."""

from __future__ import annotations

import math
from datetime import date, timedelta

from flask import Blueprint, g, jsonify
from loguru import logger
from sqlalchemy import and_, func

from backend.auth.decorators import require_auth
from backend.models.database import db
from backend.models.spirit_checkin import (
    SpiritCheckin,
    SpiritCheckinStreak,
    SpiritFinanceCorrelation,
)
from backend.models.user_models import User

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

_PRACTICE_TYPES = ("prayer", "meditation", "gratitude", "affirmation")


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


@admin_bp.route("/spirit-metrics", methods=["GET"])
@require_auth
def spirit_metrics():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin_user(user):
        return _admin_forbidden()

    try:
        cutoff_date = date.today() - timedelta(days=30)

        total_checkins_all_time = db.session.query(func.count(SpiritCheckin.id)).scalar() or 0

        checkins_last_30_days = (
            db.session.query(func.count(SpiritCheckin.id))
            .filter(SpiritCheckin.checked_in_date >= cutoff_date)
            .scalar()
            or 0
        )

        active_users_last_30_days = (
            db.session.query(func.count(func.distinct(SpiritCheckin.user_id)))
            .filter(SpiritCheckin.checked_in_date >= cutoff_date)
            .scalar()
            or 0
        )

        active_subq = (
            db.session.query(SpiritCheckin.user_id)
            .filter(SpiritCheckin.checked_in_date >= cutoff_date)
            .distinct()
            .subquery()
        )
        avg_streak_row = (
            db.session.query(func.avg(SpiritCheckinStreak.current_streak))
            .join(active_subq, SpiritCheckinStreak.user_id == active_subq.c.user_id)
            .scalar()
        )
        avg_streak_active_users = float(avg_streak_row) if avg_streak_row is not None else 0.0

        avg_score_row = db.session.query(func.avg(SpiritCheckin.practice_score)).scalar()
        avg_practice_score = float(avg_score_row) if avg_score_row is not None else 0.0

        breakdown_rows = (
            db.session.query(SpiritCheckin.practice_type, func.count(SpiritCheckin.id))
            .group_by(SpiritCheckin.practice_type)
            .all()
        )
        practice_type_breakdown = {k: 0 for k in _PRACTICE_TYPES}
        for ptype, cnt in breakdown_rows:
            if ptype in practice_type_breakdown:
                practice_type_breakdown[ptype] = int(cnt)

        sfc = SpiritFinanceCorrelation
        latest_subq = (
            db.session.query(
                sfc.user_id,
                func.max(sfc.computed_at).label("max_computed"),
            )
            .group_by(sfc.user_id)
            .subquery()
        )
        latest_corrs = (
            db.session.query(sfc)
            .join(
                latest_subq,
                and_(
                    sfc.user_id == latest_subq.c.user_id,
                    sfc.computed_at == latest_subq.c.max_computed,
                ),
            )
            .all()
        )

        savings_vals = [
            float(r.corr_practice_savings)
            for r in latest_corrs
            if r.corr_practice_savings is not None and not math.isnan(r.corr_practice_savings)
        ]
        stress_vals = [
            float(r.corr_practice_stress)
            for r in latest_corrs
            if r.corr_practice_stress is not None and not math.isnan(r.corr_practice_stress)
        ]

        avg_corr_practice_savings = (
            sum(savings_vals) / len(savings_vals) if savings_vals else 0.0
        )
        avg_corr_practice_stress = sum(stress_vals) / len(stress_vals) if stress_vals else 0.0

        if savings_vals:
            positive = sum(1 for v in savings_vals if v > 0.3)
            pct_users_with_positive_savings_corr = 100.0 * positive / len(savings_vals)
        else:
            pct_users_with_positive_savings_corr = 0.0

        payload = {
            "total_checkins_all_time": int(total_checkins_all_time),
            "checkins_last_30_days": int(checkins_last_30_days),
            "active_users_last_30_days": int(active_users_last_30_days),
            "avg_streak_active_users": round(avg_streak_active_users, 4),
            "avg_practice_score": round(avg_practice_score, 4),
            "practice_type_breakdown": practice_type_breakdown,
            "avg_corr_practice_savings": round(avg_corr_practice_savings, 4),
            "avg_corr_practice_stress": round(avg_corr_practice_stress, 4),
            "pct_users_with_positive_savings_corr": round(pct_users_with_positive_savings_corr, 4),
        }
        return jsonify(payload)

    except Exception as e:
        logger.error(f"spirit-metrics admin endpoint failed: {e}")
        return jsonify({"error": "Failed to load spirit metrics"}), 500
