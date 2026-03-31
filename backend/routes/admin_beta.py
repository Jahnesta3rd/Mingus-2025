#!/usr/bin/env python3
"""Beta admin dashboard API: aggregates beta codes, users, telemetry, and feedback."""

from __future__ import annotations

import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from backend.auth.decorators import require_auth
from backend.models.beta_code import BetaCode
from backend.models.beta_invite_log import BetaInviteLog
from backend.models.database import db
from backend.models.feedback import FeatureRating, NPSSurvey
from backend.models.user_models import User
from backend.services.business_intelligence_log import _db_path as _bi_db_path
from backend.services.beta_invite_service import BetaInviteService

admin_beta_bp = Blueprint("admin_beta", __name__, url_prefix="/api/admin/beta")


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


def _bi_connect():
    path = _bi_db_path()
    if not os.path.isfile(path):
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _cutoff_iso(*, days: int | None = None, hours: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    if days is not None:
        cut = now - timedelta(days=days)
    else:
        cut = now - timedelta(hours=hours or 0)
    return cut.isoformat()


@admin_beta_bp.route("/overview", methods=["GET"])
@require_auth
def overview():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin_user(user):
        return _admin_forbidden()

    total_codes = BetaCode.query.count()
    redeemed = BetaCode.query.filter_by(status="redeemed").count()
    available = BetaCode.query.filter_by(status="available").count()
    redemption_rate = (redeemed / total_codes) if total_codes else 0.0

    total_beta = User.query.filter_by(is_beta=True).count()

    beta_uuid_set = {
        row[0]
        for row in db.session.query(User.user_id).filter(User.is_beta.is_(True)).all()
    }

    conn = _bi_connect()
    total_events = 0
    unique_tracked = 0
    top_features: list[dict] = []
    active_7d = 0
    active_24h = 0

    if conn:
        try:
            cur = conn.execute("SELECT COUNT(*) FROM feature_events")
            total_events = cur.fetchone()[0] or 0

            cur = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM feature_events WHERE user_id IS NOT NULL"
            )
            unique_tracked = cur.fetchone()[0] or 0

            cur = conn.execute(
                """
                SELECT feature_name, COUNT(*) AS c
                FROM feature_events
                WHERE feature_name IS NOT NULL AND feature_name != ''
                GROUP BY feature_name
                ORDER BY c DESC
                LIMIT 5
                """
            )
            top_features = [{"name": r["feature_name"], "count": r["c"]} for r in cur]

            cut7 = _cutoff_iso(days=7)
            cur = conn.execute(
                """
                SELECT DISTINCT user_id FROM feature_events
                WHERE user_id IS NOT NULL AND user_id != '' AND timestamp >= ?
                """,
                (cut7,),
            )
            active_7d = sum(1 for r in cur if r[0] in beta_uuid_set)

            cut24 = _cutoff_iso(hours=24)
            cur = conn.execute(
                """
                SELECT DISTINCT user_id FROM feature_events
                WHERE user_id IS NOT NULL AND user_id != '' AND timestamp >= ?
                """,
                (cut24,),
            )
            active_24h = sum(1 for r in cur if r[0] in beta_uuid_set)
        finally:
            conn.close()

    ratings_total = FeatureRating.query.count()
    up_count = FeatureRating.query.filter_by(rating="up").count()
    down_count = FeatureRating.query.filter_by(rating="down").count()
    denom = up_count + down_count
    thumbs_up_pct = (100.0 * up_count / denom) if denom else None

    nps_submitted = NPSSurvey.query.count()
    avg_nps = db.session.query(func.avg(NPSSurvey.score)).scalar()
    avg_nps_score = float(avg_nps) if avg_nps is not None else None

    return (
        jsonify(
            {
                "codes": {
                    "total": total_codes,
                    "redeemed": redeemed,
                    "available": available,
                    "redemption_rate": redemption_rate,
                },
                "beta_invites": {
                    "sent": BetaInviteLog.query.filter_by(status="sent").count(),
                    "queued": BetaInviteLog.query.filter_by(status="queued").count(),
                    "failed": BetaInviteLog.query.filter_by(status="failed").count(),
                },
                "users": {
                    "total_beta": total_beta,
                    "active_last_7_days": active_7d,
                    "active_last_24_hours": active_24h,
                },
                "feature_events": {
                    "total_events": total_events,
                    "unique_users_tracked": unique_tracked,
                    "top_features": top_features,
                },
                "feedback": {
                    "ratings_submitted": ratings_total,
                    "nps_submitted": nps_submitted,
                    "avg_nps_score": avg_nps_score,
                    "thumbs_up_pct": thumbs_up_pct,
                },
            }
        ),
        200,
    )


@admin_beta_bp.route("/feedback-insights", methods=["GET"])
@require_auth
def feedback_insights():
    """NPS segments, would-pay, and top most_valuable_feature values (dashboard section 4)."""
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin_user(user):
        return _admin_forbidden()

    detractors = NPSSurvey.query.filter(NPSSurvey.score <= 6).count()
    passives = NPSSurvey.query.filter(
        NPSSurvey.score >= 7, NPSSurvey.score <= 8
    ).count()
    promoters = NPSSurvey.query.filter(NPSSurvey.score >= 9).count()

    would_yes = NPSSurvey.query.filter_by(would_pay="yes").count()
    would_maybe = NPSSurvey.query.filter_by(would_pay="maybe").count()
    would_no = NPSSurvey.query.filter_by(would_pay="no").count()

    mvf_rows = (
        db.session.query(NPSSurvey.most_valuable_feature, func.count().label("c"))
        .filter(
            NPSSurvey.most_valuable_feature.isnot(None),
            NPSSurvey.most_valuable_feature != "",
        )
        .group_by(NPSSurvey.most_valuable_feature)
        .order_by(func.count().desc())
        .limit(3)
        .all()
    )
    top_valuable_features = [
        {"name": name, "count": int(c)} for name, c in mvf_rows if name
    ]

    return (
        jsonify(
            {
                "nps_breakdown": {
                    "detractors": detractors,
                    "passives": passives,
                    "promoters": promoters,
                },
                "would_pay": {"yes": would_yes, "maybe": would_maybe, "no": would_no},
                "top_valuable_features": top_valuable_features,
            }
        ),
        200,
    )


@admin_beta_bp.route("/users", methods=["GET"])
@require_auth
def beta_users():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin_user(user):
        return _admin_forbidden()

    beta_users_list = User.query.filter_by(is_beta=True).order_by(User.created_at.desc()).all()
    if not beta_users_list:
        return jsonify([]), 200

    uuid_list = [u.user_id for u in beta_users_list]
    int_ids = [u.id for u in beta_users_list]

    events_by_uuid: dict[str, tuple[int, str | None]] = {}
    top_feature_by_uuid: dict[str, str | None] = {}

    conn = _bi_connect()
    feat_counts_by_uuid: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    if conn and uuid_list:
        try:
            chunk_size = 400
            for i in range(0, len(uuid_list), chunk_size):
                chunk = uuid_list[i : i + chunk_size]
                placeholders = ",".join("?" * len(chunk))
                q = f"""
                    SELECT user_id, COUNT(*) AS cnt, MAX(timestamp) AS last_ts
                    FROM feature_events
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id
                """
                for row in conn.execute(q, chunk):
                    events_by_uuid[row["user_id"]] = (row["cnt"], row["last_ts"])

                q2 = f"""
                    SELECT user_id, feature_name, COUNT(*) AS cnt
                    FROM feature_events
                    WHERE user_id IN ({placeholders})
                    GROUP BY user_id, feature_name
                """
                for row in conn.execute(q2, chunk):
                    feat_counts_by_uuid[row["user_id"]][row["feature_name"]] += row["cnt"]
            for uid, feat_map in feat_counts_by_uuid.items():
                if feat_map:
                    top_feature_by_uuid[uid] = max(feat_map, key=lambda k: feat_map[k])
        finally:
            conn.close()

    nps_by_int_id = {
        row.user_id: row.score
        for row in NPSSurvey.query.filter(NPSSurvey.user_id.in_(int_ids)).all()
    }

    out = []
    for u in beta_users_list:
        ev = events_by_uuid.get(u.user_id, (0, None))
        out.append(
            {
                "user_id": u.id,
                "email": u.email or "",
                "first_name": (u.first_name or "") or "",
                "created_at": u.created_at.isoformat() if u.created_at else "",
                "beta_batch": (u.beta_batch or "") or "",
                "events_count": ev[0],
                "last_active": ev[1],
                "nps_score": nps_by_int_id.get(u.id),
                "top_feature": top_feature_by_uuid.get(u.user_id),
            }
        )

    return jsonify(out), 200


@admin_beta_bp.route("/features", methods=["GET"])
@require_auth
def feature_engagement():
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin_user(user):
        return _admin_forbidden()

    conn = _bi_connect()
    views_by_feature: dict[str, int] = defaultdict(int)
    uniques_by_feature: dict[str, set[str]] = defaultdict(set)

    if conn:
        try:
            cur = conn.execute(
                """
                SELECT feature_name, user_id
                FROM feature_events
                WHERE event_type = 'view'
                  AND feature_name IS NOT NULL
                  AND feature_name != ''
                """
            )
            for row in cur:
                fn = row["feature_name"]
                views_by_feature[fn] += 1
                uid = row["user_id"]
                if uid:
                    uniques_by_feature[fn].add(uid)
        finally:
            conn.close()

    rating_stats = (
        db.session.query(
            FeatureRating.feature_name,
            FeatureRating.rating,
            func.count().label("c"),
        )
        .group_by(FeatureRating.feature_name, FeatureRating.rating)
        .all()
    )
    up_down: dict[str, dict[str, int]] = defaultdict(lambda: {"up": 0, "down": 0})
    for fname, rating, c in rating_stats:
        if rating in ("up", "down"):
            up_down[fname][rating] = int(c)

    feature_names = set(views_by_feature.keys()) | set(up_down.keys())
    rows = []
    for fname in feature_names:
        vu = views_by_feature.get(fname, 0)
        uu = len(uniques_by_feature.get(fname, set()))
        ud = up_down[fname]
        upc, dnc = ud["up"], ud["down"]
        total_r = upc + dnc
        if total_r > 0:
            avg_rating = (upc * 5.0 + dnc * 1.0) / total_r
        else:
            avg_rating = None
        rows.append(
            {
                "feature_name": fname,
                "total_views": vu,
                "unique_users": uu,
                "avg_rating": avg_rating,
                "thumbs_up": upc,
                "thumbs_down": dnc,
            }
        )

    rows.sort(key=lambda r: r["total_views"], reverse=True)
    return jsonify(rows), 200


@admin_beta_bp.route("/send-wave", methods=["POST"])
@require_auth
def send_wave():
    """Queue beta invites from JSON payload; optionally dispatch Celery sends."""
    user = _user_for_jwt()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if not _is_admin_user(user):
        return _admin_forbidden()

    body = request.get_json(silent=True) or {}
    wave_label = (body.get("wave_label") or "").strip()
    recipients = body.get("recipients")
    beta_url = (body.get("beta_url") or "https://mingusapp.com/beta").strip()
    dry_run = bool(body.get("dry_run"))

    if not wave_label:
        return jsonify({"error": "wave_label is required"}), 400
    if not isinstance(recipients, list):
        return jsonify({"error": "recipients must be a list"}), 400

    svc = BetaInviteService()
    prep = svc.prepare_wave(wave_label, recipients, dry_run=dry_run)
    skipped = len(prep["skipped"])
    dispatched = 0

    if not dry_run:
        send = svc.send_wave(wave_label, beta_url)
        dispatched = send["dispatched"]

    return (
        jsonify(
            {
                "dispatched": dispatched,
                "skipped": skipped,
                "wave": wave_label,
                "dry_run": dry_run,
            }
        ),
        200,
    )
