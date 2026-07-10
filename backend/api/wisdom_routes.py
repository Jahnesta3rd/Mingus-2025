#!/usr/bin/env python3
"""Wisdom Call API: weekly script, projections, engagement, and stats."""

from __future__ import annotations

import json
import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from backend.auth.decorators import get_current_user_db_id, require_auth, require_csrf
from backend.models.checkin import WeeklyCheckin
from backend.models.database import db
from backend.models.in_app_notification import InAppNotification
from backend.services.wisdom_call_service import (
    WisdomCallService,
    _friendly_date_str,
    _milestone_projected_line,
    _milestone_shortfall_message,
)

logger = logging.getLogger(__name__)

wisdom_bp = Blueprint("wisdom", __name__, url_prefix="/api/wisdom")

# Back-compat alias used by older imports.
wisdom_call_bp = wisdom_bp

_svc = WisdomCallService()
_LAST_BATCH_REDIS_KEY = "mingus:wisdom_call:last_batch"
_ADMIN_KEY_ENV = ("WISDOM_ADMIN_KEY", "ADMIN_API_KEY", "MINGUS_ADMIN_KEY")


def _parse_week(week: str | int) -> int | None:
    try:
        value = int(week)
    except (TypeError, ValueError):
        return None
    if value < 1 or value > 53:
        return None
    return value


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat() + ("Z" if dt.tzinfo is None else "")


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _friendly_date_full(value: Any) -> str | None:
    raw = str(value)[:10] if value is not None else ""
    try:
        d = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return _friendly_date_str(value)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def _projection_message(milestone: dict[str, Any]) -> str:
    status = (milestone.get("status") or "").strip().lower()
    shortfall = _milestone_shortfall_message(milestone)
    if status == "behind" and shortfall:
        return shortfall
    line = _milestone_projected_line(milestone)
    if line:
        # Soften email-style line into API message tone.
        if line.startswith("Projected: "):
            rest = line[len("Projected: ") :]
            if status in ("on_track", "ahead"):
                return f"You'll hit your goal by {rest.split(' (')[0]}"
            return line
        return line
    name = milestone.get("name") or "your goal"
    return f"Keep going on {name}."


def _serialize_financial_projection(m: dict[str, Any]) -> dict[str, Any]:
    current = _coerce_float(m.get("current_balance", m.get("current")))
    target = _coerce_float(m.get("target_amount", m.get("target")))
    status = (m.get("status") or "no_data").strip().lower()
    projected_date = m.get("projected_date")
    target_date = m.get("target_date")
    weekly_need = _coerce_float(m.get("weekly_need"))

    progress_pct = None
    if current is not None and target is not None and target > 0:
        progress_pct = round(max(0.0, min(100.0, (current / target) * 100.0)), 1)

    shortfall_message = None
    if status == "behind" and weekly_need and weekly_need > 0:
        short_target = _friendly_date_full(target_date) or "your target date"
        try:
            d = datetime.strptime(str(target_date)[:10], "%Y-%m-%d").date()
            short_target = f"{d.strftime('%b')} {d.day}"
        except (TypeError, ValueError):
            pass
        shortfall_message = f"Need ${weekly_need:,.0f}/week more to hit {short_target} target"

    return {
        "name": m.get("name") or "Milestone",
        "current_balance": current,
        "target_amount": target,
        "target_date": target_date,
        "projected_date": projected_date,
        "status": status,
        "message": _projection_message(m),
        # UI helpers (backward compatible with WisdomCallPage)
        "current": current,
        "target": target,
        "progress_pct": progress_pct,
        "projected_date_label": _friendly_date_full(projected_date),
        "target_date_label": _friendly_date_full(target_date),
        "weekly_need": weekly_need,
        "shortfall": m.get("shortfall"),
        "shortfall_message": shortfall_message,
        "weekly_saving_rate": m.get("weekly_saving_rate"),
    }


def _admin_key_configured() -> str | None:
    for key in _ADMIN_KEY_ENV:
        value = (os.environ.get(key) or "").strip()
        if value:
            return value
    return None


def _admin_key_valid(provided: str | None) -> bool:
    expected = _admin_key_configured()
    if not expected or not provided:
        return False
    return provided.strip() == expected


def _redis_client():
    try:
        import redis

        url = os.environ.get("CELERY_BROKER_URL") or os.environ.get(
            "REDIS_URL", "redis://localhost:6379/2"
        )
        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def store_wisdom_batch_result(results: dict[str, Any]) -> None:
    """Persist last scheduler run for the stats endpoint."""
    payload = {
        **results,
        "stored_at": datetime.utcnow().isoformat() + "Z",
    }
    client = _redis_client()
    if client is None:
        logger.warning("wisdom stats: redis unavailable; last batch not stored")
        return
    try:
        client.set(_LAST_BATCH_REDIS_KEY, json.dumps(payload), ex=60 * 60 * 24 * 90)
    except Exception:
        logger.exception("wisdom stats: failed to store last batch result")


def load_wisdom_batch_result() -> dict[str, Any] | None:
    client = _redis_client()
    if client is None:
        return None
    try:
        raw = client.get(_LAST_BATCH_REDIS_KEY)
        if not raw:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        logger.exception("wisdom stats: failed to load last batch result")
        return None


def _user_engagement_stats(user_id: int) -> dict[str, Any]:
    rows = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .filter(WeeklyCheckin.wisdom_call_script.isnot(None))
        .filter(WeeklyCheckin.wisdom_call_script != "")
        .order_by(WeeklyCheckin.week_number.desc())
        .limit(16)
        .all()
    )
    sent = [r for r in rows if r.wisdom_call_sent_at is not None]
    read = [r for r in sent if r.wisdom_call_listened_at is not None]
    sent_n = len(sent)
    read_n = len(read)
    read_rate = round(read_n / sent_n, 4) if sent_n else 0.0

    # Trend: compare read rate of newest 4 sent weeks vs prior 4.
    recent = sent[:4]
    prior = sent[4:8]
    recent_rate = (
        sum(1 for r in recent if r.wisdom_call_listened_at) / len(recent)
        if recent
        else None
    )
    prior_rate = (
        sum(1 for r in prior if r.wisdom_call_listened_at) / len(prior) if prior else None
    )
    if recent_rate is None:
        engagement_trend = "unknown"
    elif prior_rate is None:
        engagement_trend = "stable"
    elif recent_rate - prior_rate >= 0.15:
        engagement_trend = "improving"
    elif prior_rate - recent_rate >= 0.15:
        engagement_trend = "declining"
    else:
        engagement_trend = "stable"

    last_read_row = next((r for r in sent if r.wisdom_call_listened_at), None)
    return {
        "user_id": user_id,
        "read_rate": read_rate,
        "engagement_trend": engagement_trend,
        "last_read": _iso(last_read_row.wisdom_call_listened_at) if last_read_row else None,
        "sent_count": sent_n,
        "read_count": read_n,
        "weeks_sampled": len(rows),
    }


def _weekly_delivery_trends(weeks: int = 8) -> list[dict[str, Any]]:
    """Aggregate sent/read counts by week_number for recent wisdom calls."""
    cutoff = datetime.utcnow() - timedelta(days=weeks * 7 + 7)
    rows = (
        db.session.query(
            WeeklyCheckin.week_number,
            func.count(WeeklyCheckin.id),
            func.count(WeeklyCheckin.wisdom_call_sent_at),
            func.count(WeeklyCheckin.wisdom_call_listened_at),
        )
        .filter(WeeklyCheckin.wisdom_call_script.isnot(None))
        .filter(WeeklyCheckin.wisdom_call_script != "")
        .filter(
            (WeeklyCheckin.wisdom_call_sent_at >= cutoff)
            | (WeeklyCheckin.completed_at >= cutoff)
            | (WeeklyCheckin.wisdom_call_sent_at.is_(None))
        )
        .group_by(WeeklyCheckin.week_number)
        .order_by(WeeklyCheckin.week_number.desc())
        .limit(weeks)
        .all()
    )
    trends = []
    for week_number, scripts, sent, read in rows:
        if week_number is None:
            continue
        trends.append(
            {
                "week": int(week_number),
                "scripts": int(scripts or 0),
                "sent": int(sent or 0),
                "read": int(read or 0),
                "delivery_rate": round((sent or 0) / scripts, 4) if scripts else 0.0,
                "read_rate": round((read or 0) / sent, 4) if sent else 0.0,
            }
        )
    return trends


def _top_milestones(sample_limit: int = 80) -> list[dict[str, Any]]:
    """Sample recent recipients and aggregate projection statuses by milestone name."""
    recipients = (
        WeeklyCheckin.query.filter(WeeklyCheckin.wisdom_call_script.isnot(None))
        .filter(WeeklyCheckin.wisdom_call_script != "")
        .filter(WeeklyCheckin.wisdom_call_sent_at.isnot(None))
        .order_by(WeeklyCheckin.wisdom_call_sent_at.desc())
        .limit(sample_limit)
        .all()
    )
    tallies: dict[str, dict[str, int]] = defaultdict(
        lambda: {"on_track": 0, "ahead": 0, "behind": 0, "no_data": 0, "total": 0}
    )
    for row in recipients:
        try:
            projections = _svc._get_financial_projections(row.user_id, row.week_number)
        except Exception:
            logger.exception(
                "wisdom stats: projection sample failed user_id=%s week=%s",
                row.user_id,
                row.week_number,
            )
            continue
        for m in projections.get("milestones") or []:
            if not isinstance(m, dict):
                continue
            name = (m.get("name") or "Milestone").strip() or "Milestone"
            status = (m.get("status") or "no_data").strip().lower()
            if status not in tallies[name]:
                status = "no_data"
            tallies[name][status] += 1
            tallies[name]["total"] += 1

    ranked = sorted(tallies.items(), key=lambda kv: kv[1]["total"], reverse=True)
    return [{"name": name, **counts} for name, counts in ranked[:8]]


def _system_stats() -> dict[str, Any]:
    script_q = WeeklyCheckin.query.filter(
        WeeklyCheckin.wisdom_call_script.isnot(None),
        WeeklyCheckin.wisdom_call_script != "",
    )
    scripts = script_q.count()
    sent = script_q.filter(WeeklyCheckin.wisdom_call_sent_at.isnot(None)).count()
    read = script_q.filter(WeeklyCheckin.wisdom_call_listened_at.isnot(None)).count()

    in_app = InAppNotification.query.filter_by(category="wisdom_call").count()
    # Email is part of deliver_wisdom_call; approximate via sent_at (channel success).
    email_sent = sent
    delivery_rate = round(sent / scripts, 4) if scripts else 0.0
    email_rate = round(email_sent / scripts, 4) if scripts else 0.0
    read_rate = round(read / sent, 4) if sent else 0.0

    last_batch = load_wisdom_batch_result() or {}
    failed = int(last_batch.get("failed") or 0)
    total = int(last_batch.get("total") or 0)
    skipped = int(last_batch.get("skipped") or 0)
    attempted = max(total - skipped, 0)
    failure_rate = (
        float(last_batch["failure_rate"])
        if last_batch.get("failure_rate") is not None
        else (round(failed / attempted, 4) if attempted else 0.0)
    )

    return {
        "delivery_rate": delivery_rate,
        "email_rate": email_rate,
        "read_rate": read_rate,
        "failure_rate": failure_rate,
        "counts": {
            "scripts": scripts,
            "sent": sent,
            "read": read,
            "in_app_notifications": in_app,
            "email_approx": email_sent,
        },
        "top_milestones": _top_milestones(),
        "weekly_trends": _weekly_delivery_trends(),
        "last_task_run": {
            "status": (
                "ok"
                if last_batch and failure_rate <= 0.10
                else "degraded"
                if last_batch
                else "unknown"
            ),
            "ran_at": last_batch.get("ran_at") or last_batch.get("stored_at"),
            "week_number": last_batch.get("week_number"),
            "total": last_batch.get("total"),
            "generated": last_batch.get("generated"),
            "delivered": last_batch.get("delivered"),
            "failed": last_batch.get("failed"),
            "skipped": last_batch.get("skipped"),
            "failure_rate": failure_rate,
        },
    }


def _try_authenticate_request() -> int | None:
    """Soft-auth: set g from JWT if present; return internal users.id or None."""
    from flask import g

    import jwt as pyjwt

    from backend.auth.decorators import JWT_ALGORITHM, JWT_SECRET_KEY, _is_testing_mode

    if _is_testing_mode():
        from backend.auth.decorators import _apply_test_auth_context

        _apply_test_auth_context()
        return get_current_user_db_id()

    token = request.cookies.get("mingus_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    if not token:
        return None
    try:
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        g.current_user_id = payload.get("user_id")
        g.current_user_email = payload.get("email")
        return get_current_user_db_id()
    except Exception:
        return None


@wisdom_bp.route("/stats", methods=["GET"])
def get_wisdom_call_stats():
    """
    Monitoring + engagement stats.

    Query params:
      - user_id (optional): per-user read rate / trend (requires auth or admin_key)
      - admin_key (optional): unlocks system delivery metrics + last task run
    """
    user_id_param = request.args.get("user_id", type=int)
    admin_key = request.args.get("admin_key") or request.headers.get("X-Admin-Key")
    is_admin = _admin_key_valid(admin_key)

    payload: dict[str, Any] = {}

    if admin_key is not None:
        if not is_admin:
            return jsonify({"error": "Invalid or missing admin_key"}), 403
        payload["system"] = _system_stats()

    # User stats when requested explicitly, or when no admin system block was asked.
    include_user = user_id_param is not None or admin_key is None
    if include_user:
        authed_id = _try_authenticate_request()
        if is_admin and user_id_param is not None:
            target_id = int(user_id_param)
        elif authed_id is not None:
            if user_id_param is not None and int(user_id_param) != int(authed_id):
                return jsonify({"error": "Forbidden"}), 403
            target_id = int(authed_id)
        else:
            if "system" in payload:
                return jsonify(payload)
            return jsonify({"error": "Authentication required"}), 401
        payload["user"] = _user_engagement_stats(target_id)

    return jsonify(payload)


@wisdom_bp.route("/<week>", methods=["GET"])
@require_auth
def get_wisdom_call(week: str):
    """Return wisdom-call script + financial projections for a week."""
    week_number = _parse_week(week)
    if week_number is None:
        return jsonify({"error": "Invalid week number"}), 400

    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    checkin = (
        WeeklyCheckin.query.filter_by(user_id=user_id, week_number=week_number).first()
    )
    if checkin is None or not (checkin.wisdom_call_script or "").strip():
        return jsonify({"error": "Wisdom call not found for this week"}), 404

    projections = _svc._get_financial_projections(user_id, week_number)
    financial_projections = [
        _serialize_financial_projection(m)
        for m in (projections.get("milestones") or [])
        if isinstance(m, dict)
    ]

    return jsonify(
        {
            "week": week_number,
            "script": checkin.wisdom_call_script,
            "audio_url": checkin.wisdom_call_audio_url,  # NULL until Phase 5
            "format": "text" if not checkin.wisdom_call_audio_url else "audio",
            "sent_at": _iso(checkin.wisdom_call_sent_at),
            "listened_at": _iso(checkin.wisdom_call_listened_at),
            "financial_projections": financial_projections,
            # Backward-compatible aliases for existing UI clients.
            "week_number": week_number,
            "milestones": financial_projections,
            "projections_summary": projections.get("total_projection_summary"),
            "weekly_saving_rate": projections.get("weekly_saving_rate"),
        }
    )


@wisdom_bp.route("/<week>/read", methods=["POST"])
@require_auth
@require_csrf
def mark_wisdom_call_read(week: str):
    """Track engagement: mark the week's wisdom call as read/listened."""
    week_number = _parse_week(week)
    if week_number is None:
        return jsonify({"error": "Invalid week number"}), 400

    user_id = get_current_user_db_id()
    if user_id is None:
        return jsonify({"error": "Authentication required"}), 401

    checkin = (
        WeeklyCheckin.query.filter_by(user_id=user_id, week_number=week_number).first()
    )
    if checkin is None or not (checkin.wisdom_call_script or "").strip():
        return jsonify({"error": "Wisdom call not found for this week"}), 404

    if checkin.wisdom_call_listened_at is None:
        checkin.wisdom_call_listened_at = datetime.utcnow()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"error": "Failed to record engagement"}), 500

    return jsonify(
        {
            "success": True,
            "week": week_number,
            "week_number": week_number,
            "listened_at": _iso(checkin.wisdom_call_listened_at),
        }
    )
