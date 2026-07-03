#!/usr/bin/env python3
"""Admin API: assessment funnel conversion metrics."""

from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, g, jsonify
from sqlalchemy import case, func

from backend.auth.decorators import require_auth
from backend.models.assessment_event import AssessmentEvent
from backend.models.database import db
from backend.models.user_models import User

admin_assessment_analytics_bp = Blueprint(
    "admin_assessment_analytics",
    __name__,
    url_prefix="/api/admin",
)


def _user_for_jwt() -> User | None:
    ext = getattr(g, "current_user_id", None)
    if ext is None:
        return None
    return User.query.filter_by(user_id=str(ext)).first()


def _require_admin():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not getattr(user, "is_admin", False) and (getattr(user, "role", None) or "").lower() != "admin":
        return jsonify({"error": "Admin access required"}), 403
    return None


def _count_events(event_type: str, since: datetime) -> int:
    return (
        AssessmentEvent.query.filter(
            AssessmentEvent.event_type == event_type,
            AssessmentEvent.created_at > since,
        ).count()
    )


@admin_assessment_analytics_bp.route("/assessment-funnel", methods=["GET"])
@require_auth
def get_assessment_funnel():
    """Funnel metrics for the last 30 days."""
    denied = _require_admin()
    if denied:
        return denied

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    submitted = _count_events("submitted", thirty_days_ago)
    email_sent = _count_events("email_sent", thirty_days_ago)
    results_viewed = _count_events("results_viewed", thirty_days_ago)
    signup_completed = _count_events("signup_completed", thirty_days_ago)

    return jsonify(
        {
            "period": "last_30_days",
            "funnel": {
                "submitted": submitted,
                "email_sent": email_sent,
                "results_viewed": results_viewed,
                "signup_completed": signup_completed,
            },
            "conversion_rates": {
                "submitted_to_email_sent": (email_sent / submitted * 100) if submitted else 0,
                "email_sent_to_results_viewed": (results_viewed / email_sent * 100) if email_sent else 0,
                "results_viewed_to_signup": (signup_completed / results_viewed * 100) if results_viewed else 0,
                "overall_submitted_to_signup": (signup_completed / submitted * 100) if submitted else 0,
            },
        }
    ), 200


@admin_assessment_analytics_bp.route("/assessment-funnel/by-type", methods=["GET"])
@require_auth
def get_funnel_by_assessment_type():
    """Funnel metrics grouped by assessment type."""
    denied = _require_admin()
    if denied:
        return denied

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    rows = (
        db.session.query(
            AssessmentEvent.assessment_id,
            func.sum(case((AssessmentEvent.event_type == "submitted", 1), else_=0)).label("submitted"),
            func.sum(case((AssessmentEvent.event_type == "results_viewed", 1), else_=0)).label("viewed"),
            func.sum(case((AssessmentEvent.event_type == "signup_completed", 1), else_=0)).label("signups"),
        )
        .filter(AssessmentEvent.created_at > thirty_days_ago)
        .group_by(AssessmentEvent.assessment_id)
        .all()
    )

    import os
    import psycopg2
    import psycopg2.extras

    by_type: dict[str, dict[str, int]] = {}
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    try:
        cursor = conn.cursor()
        for row in rows:
            cursor.execute(
                "SELECT assessment_type FROM assessments WHERE id = %s",
                (row.assessment_id,),
            )
            atype_row = cursor.fetchone()
            atype = atype_row["assessment_type"] if atype_row else "unknown"
            bucket = by_type.setdefault(atype, {"submitted": 0, "viewed": 0, "signups": 0})
            bucket["submitted"] += int(row.submitted or 0)
            bucket["viewed"] += int(row.viewed or 0)
            bucket["signups"] += int(row.signups or 0)
    finally:
        conn.close()

    return jsonify({"by_type": by_type}), 200
