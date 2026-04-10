#!/usr/bin/env python3
"""Spirit & Finance API: daily check-ins, streaks, correlations, calendar."""

from __future__ import annotations

import calendar
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

from flask import Blueprint, jsonify, request
import pytz
from sqlalchemy import desc

from backend.auth.decorators import current_user, require_auth, require_csrf
from backend.models.database import db
from backend.models.spirit_checkin import (
    SpiritCheckin,
    SpiritCheckinStreak,
    SpiritFinanceCorrelation,
)
from backend.models.spirit_prefs import SpiritNotificationPrefs, DEFAULT_REMINDER_DAYS
from backend.services.spirit_correlation import SpiritCorrelationEngine
from backend.tasks.life_correlation_tasks import record_life_snapshot
from backend.tasks.spirit_tasks import refresh_spirit_correlation

spirit_finance_bp = Blueprint("spirit_finance", __name__)

_TIER_PROFESSIONAL = "professional"
_TIER_MID = "mid_tier"
_TIER_BUDGET = "budget"

_VALID_PRACTICE = frozenset({"prayer", "meditation", "gratitude", "affirmation"})
_VALID_DURATION = frozenset({5, 10, 15, 20, 30})

_REMINDER_DAY_ORDER = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_REMINDER_DAY_SET = frozenset(_REMINDER_DAY_ORDER)
_TIMEZONE_SET = getattr(pytz, "all_timezones_set", frozenset(pytz.all_timezones))


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _parse_json() -> dict[str, Any]:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _checkin_dict(c: SpiritCheckin) -> dict[str, Any]:
    return {
        "id": c.id,
        "user_id": c.user_id,
        "checked_in_date": c.checked_in_date.isoformat(),
        "practice_type": c.practice_type,
        "duration_minutes": c.duration_minutes,
        "feeling_before": c.feeling_before,
        "feeling_after": c.feeling_after,
        "intention_text": c.intention_text,
        "practice_score": float(c.practice_score),
        "created_at": c.created_at.isoformat() + "Z" if c.created_at else None,
    }


def _streak_dict(s: SpiritCheckinStreak | None) -> dict[str, Any]:
    if not s:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "total_checkins": 0,
            "last_checkin_date": None,
        }
    return {
        "current_streak": s.current_streak,
        "longest_streak": s.longest_streak,
        "total_checkins": s.total_checkins,
        "last_checkin_date": s.last_checkin_date.isoformat()
        if s.last_checkin_date
        else None,
    }


def _parse_insight_summary(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data if x is not None]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return []


def _correlation_core_dict(row: SpiritFinanceCorrelation) -> dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "computed_at": row.computed_at.isoformat() + "Z" if row.computed_at else None,
        "weeks_analyzed": row.weeks_analyzed,
        "corr_practice_savings": row.corr_practice_savings,
        "corr_practice_impulse": row.corr_practice_impulse,
        "corr_practice_stress": row.corr_practice_stress,
        "corr_practice_bills_ontime": row.corr_practice_bills_ontime,
        "avg_practice_score_high_weeks": row.avg_practice_score_high_weeks,
        "avg_impulse_miss_days": row.avg_impulse_miss_days,
        "avg_impulse_checkin_days": row.avg_impulse_checkin_days,
        "insight_summary": _parse_insight_summary(row.insight_summary),
    }


def _spirit_prefs_defaults() -> dict[str, Any]:
    return {
        "reminders_enabled": True,
        "reminder_hour": 8,
        "reminder_timezone": "America/New_York",
        "reminder_days": DEFAULT_REMINDER_DAYS,
        "streak_nudge_enabled": True,
        "last_reminder_sent": None,
        "updated_at": None,
    }


def _normalize_reminder_days(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        parts = [str(x).strip().lower() for x in raw if x is not None and str(x).strip()]
    elif isinstance(raw, str):
        parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    else:
        return None
    if not parts:
        return None
    for p in parts:
        if p not in _REMINDER_DAY_SET:
            return None
    return ",".join(d for d in _REMINDER_DAY_ORDER if d in parts)


def _static_recommendations() -> list[dict[str, str]]:
    return [
        {
            "icon": "sunrise",
            "title": "Morning anchor",
            "body": "Block 10 minutes after waking for prayer or meditation before you open email or money apps.",
        },
        {
            "icon": "cart",
            "title": "Plan purchases after practice",
            "body": "Schedule discretionary buys right after a check-in so you decide with a calmer baseline.",
        },
        {
            "icon": "calendar",
            "title": "21-day challenge",
            "body": "Commit to one short daily practice for three weeks and review spending stress once a week.",
        },
        {
            "icon": "users",
            "title": "Partner check-in",
            "body": "Share your streak goal with someone you trust for gentle accountability.",
        },
    ]


@spirit_finance_bp.route("/checkin", methods=["POST"])
@require_auth
@require_csrf
def submit_checkin():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    body = _parse_json()
    practice_type = body.get("practice_type")
    duration_minutes = body.get("duration_minutes")
    feeling_after = body.get("feeling_after")
    feeling_before = body.get("feeling_before")
    intention_text = body.get("intention_text")

    if practice_type not in _VALID_PRACTICE:
        return jsonify({"error": "invalid_practice_type"}), 400
    try:
        duration_minutes = int(duration_minutes)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid_duration_minutes"}), 400
    if duration_minutes not in _VALID_DURATION:
        return jsonify({"error": "invalid_duration_minutes"}), 400
    try:
        feeling_after = int(feeling_after)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid_feeling_after"}), 400
    if feeling_after not in (1, 2, 3, 4, 5):
        return jsonify({"error": "invalid_feeling_after"}), 400

    if feeling_before is not None:
        try:
            feeling_before = int(feeling_before)
        except (TypeError, ValueError):
            return jsonify({"error": "invalid_feeling_before"}), 400
        if feeling_before not in (1, 2, 3, 4, 5):
            return jsonify({"error": "invalid_feeling_before"}), 400

    today = _utc_today()
    existing = SpiritCheckin.query.filter_by(
        user_id=user.id, checked_in_date=today
    ).first()
    if existing:
        return (
            jsonify(
                {
                    "error": "already_checked_in",
                    "message": "You have already logged today.",
                }
            ),
            409,
        )

    score = SpiritCheckin.compute_score(practice_type, duration_minutes, feeling_after)
    checkin = SpiritCheckin(
        user_id=user.id,
        checked_in_date=today,
        practice_type=practice_type,
        duration_minutes=duration_minutes,
        feeling_before=feeling_before,
        feeling_after=feeling_after,
        intention_text=intention_text,
        practice_score=score,
    )
    db.session.add(checkin)

    streak = SpiritCheckinStreak.query.filter_by(user_id=user.id).first()
    if not streak:
        streak = SpiritCheckinStreak(
            user_id=user.id,
            current_streak=0,
            longest_streak=0,
            total_checkins=0,
        )
        db.session.add(streak)

    last = streak.last_checkin_date
    if last == today - timedelta(days=1):
        streak.current_streak = (streak.current_streak or 0) + 1
    else:
        streak.current_streak = 1
    if streak.current_streak > (streak.longest_streak or 0):
        streak.longest_streak = streak.current_streak
    streak.total_checkins = (streak.total_checkins or 0) + 1
    streak.last_checkin_date = today

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "save_failed"}), 500

    refresh_spirit_correlation.delay(user.id)
    record_life_snapshot.delay(str(user.id), "spirit_checkin")

    return (
        jsonify(
            {
                "checkin": _checkin_dict(checkin),
                "streak": _streak_dict(streak),
                "practice_score": score,
            }
        ),
        201,
    )


@spirit_finance_bp.route("/checkin/today", methods=["GET"])
@require_auth
def checkin_today():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    today = _utc_today()
    c = SpiritCheckin.query.filter_by(user_id=user.id, checked_in_date=today).first()
    if c:
        return jsonify({"checked_in": True, "checkin": _checkin_dict(c)})
    return jsonify({"checked_in": False})


@spirit_finance_bp.route("/history", methods=["GET"])
@require_auth
def checkin_history():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        weeks = int(request.args.get("weeks", "8"))
    except (TypeError, ValueError):
        weeks = 8
    weeks = max(1, min(weeks, 52))

    try:
        page = int(request.args.get("page", "1"))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", "20"))
    except (TypeError, ValueError):
        per_page = 20
    page = max(1, page)
    per_page = max(1, min(per_page, 100))

    windows = SpiritCorrelationEngine.week_windows(weeks, _utc_today())
    start_date = windows[0][1]

    q = SpiritCheckin.query.filter(
        SpiritCheckin.user_id == user.id,
        SpiritCheckin.checked_in_date >= start_date,
    )
    total = q.count()
    rows = (
        q.order_by(desc(SpiritCheckin.checked_in_date))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    streak = SpiritCheckinStreak.query.filter_by(user_id=user.id).first()
    return jsonify(
        {
            "checkins": [_checkin_dict(c) for c in rows],
            "total": total,
            "streak": _streak_dict(streak),
        }
    )


@spirit_finance_bp.route("/correlation", methods=["GET"])
@require_auth
def get_correlation():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    tier = (user.tier or _TIER_BUDGET).strip().lower()
    engine = SpiritCorrelationEngine()
    row = engine.latest_correlation(user.id)
    if not row:
        row = engine.refresh_correlation(user.id)
    if not row:
        return jsonify({"error": "correlation_unavailable"}), 503

    insights = _parse_insight_summary(row.insight_summary)

    if tier == _TIER_MID:
        return jsonify(
            {
                "corr_practice_savings": row.corr_practice_savings,
                "corr_practice_stress": row.corr_practice_stress,
                "corr_practice_impulse": row.corr_practice_impulse,
                "corr_practice_bills_ontime": row.corr_practice_bills_ontime,
                "insight_summary": insights,
            }
        )

    if tier == _TIER_PROFESSIONAL:
        practice_weeks = engine.get_weekly_practice_scores(user.id, weeks=8)
        fin_weeks = engine.get_weekly_financial_data(user.id, weeks=8)
        by_fin = {f["week_label"]: f for f in fin_weeks}
        weekly_data: list[dict[str, Any]] = []
        for p in practice_weeks:
            label = p["week_label"]
            frow = by_fin.get(label, {})
            weekly_data.append(
                {
                    "week_label": label,
                    "practice_score": p["practice_score"],
                    "checkin_count": p["checkin_count"],
                    "savings_rate": frow.get("savings_rate"),
                    "impulse_spend": frow.get("impulse_spend"),
                    "stress_index": frow.get("stress_index"),
                    "bills_ontime": frow.get("bills_ontime"),
                }
            )

        full = _correlation_core_dict(row)
        full["weekly_data"] = weekly_data
        return jsonify(full)

    return jsonify(
        {
            "corr_practice_savings": row.corr_practice_savings,
            "corr_practice_stress": row.corr_practice_stress,
            "insight_summary": insights,
        }
    )


@spirit_finance_bp.route("/streak", methods=["GET"])
@require_auth
def get_streak():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    streak = SpiritCheckinStreak.query.filter_by(user_id=user.id).first()
    d = _streak_dict(streak)
    return jsonify(d)


@spirit_finance_bp.route("/calendar", methods=["GET"])
@require_auth
def spirit_calendar():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    month_s = request.args.get("month") or ""
    try:
        y_str, m_str = month_s.split("-", 1)
        y = int(y_str)
        m = int(m_str)
        if m < 1 or m > 12:
            raise ValueError
    except (ValueError, AttributeError):
        return jsonify({"error": "invalid_month", "expected": "YYYY-MM"}), 400

    today = _utc_today()
    _, last_day = calendar.monthrange(y, m)
    start_d = date(y, m, 1)
    end_d = date(y, m, last_day)

    checkins = SpiritCheckin.query.filter(
        SpiritCheckin.user_id == user.id,
        SpiritCheckin.checked_in_date >= start_d,
        SpiritCheckin.checked_in_date <= end_d,
    ).all()
    done_dates = {c.checked_in_date for c in checkins}

    days_out: list[dict[str, str]] = []
    d = start_d
    while d <= end_d:
        if d > today:
            status = "future"
        elif d in done_dates:
            status = "done"
        elif d == today:
            status = "no_data"
        else:
            status = "missed"
        days_out.append({"date": d.isoformat(), "status": status})
        d += timedelta(days=1)

    return jsonify({"days": days_out})


@spirit_finance_bp.route("/prefs", methods=["GET"])
@require_auth
def spirit_prefs_get():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    row = SpiritNotificationPrefs.query.filter_by(user_id=user.id).first()
    if not row:
        return jsonify(_spirit_prefs_defaults())
    return jsonify(row.to_api_dict())


@spirit_finance_bp.route("/prefs", methods=["PUT"])
@require_auth
@require_csrf
def spirit_prefs_put():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    body = _parse_json()
    row = SpiritNotificationPrefs.query.filter_by(user_id=user.id).first()
    if row:
        base = {
            "reminders_enabled": bool(row.reminders_enabled),
            "reminder_hour": int(row.reminder_hour),
            "reminder_timezone": row.reminder_timezone,
            "reminder_days": row.reminder_days,
            "streak_nudge_enabled": bool(row.streak_nudge_enabled),
        }
    else:
        d = _spirit_prefs_defaults()
        base = {
            "reminders_enabled": d["reminders_enabled"],
            "reminder_hour": d["reminder_hour"],
            "reminder_timezone": d["reminder_timezone"],
            "reminder_days": d["reminder_days"],
            "streak_nudge_enabled": d["streak_nudge_enabled"],
        }

    if "reminders_enabled" in body:
        base["reminders_enabled"] = bool(body["reminders_enabled"])
    if "reminder_hour" in body:
        try:
            h = int(body["reminder_hour"])
        except (TypeError, ValueError):
            return jsonify({"error": "invalid_reminder_hour"}), 400
        if h < 0 or h > 23:
            return jsonify({"error": "invalid_reminder_hour"}), 400
        base["reminder_hour"] = h
    if "reminder_timezone" in body:
        tz = str(body["reminder_timezone"] or "").strip()
        if tz not in _TIMEZONE_SET:
            return jsonify({"error": "invalid_reminder_timezone"}), 400
        base["reminder_timezone"] = tz
    if "reminder_days" in body:
        norm = _normalize_reminder_days(body["reminder_days"])
        if norm is None:
            return jsonify({"error": "invalid_reminder_days"}), 400
        base["reminder_days"] = norm
    if "streak_nudge_enabled" in body:
        base["streak_nudge_enabled"] = bool(body["streak_nudge_enabled"])

    if row:
        row.reminders_enabled = base["reminders_enabled"]
        row.reminder_hour = base["reminder_hour"]
        row.reminder_timezone = base["reminder_timezone"]
        row.reminder_days = base["reminder_days"]
        row.streak_nudge_enabled = base["streak_nudge_enabled"]
    else:
        row = SpiritNotificationPrefs(
            user_id=user.id,
            reminders_enabled=base["reminders_enabled"],
            reminder_hour=base["reminder_hour"],
            reminder_timezone=base["reminder_timezone"],
            reminder_days=base["reminder_days"],
            streak_nudge_enabled=base["streak_nudge_enabled"],
        )
        db.session.add(row)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"error": "save_failed"}), 500

    return jsonify(row.to_api_dict())


@spirit_finance_bp.route("/insights", methods=["GET"])
@require_auth
def spirit_insights():
    user = current_user
    if not user:
        return jsonify({"error": "User not found"}), 404

    row = (
        SpiritFinanceCorrelation.query.filter_by(user_id=user.id)
        .order_by(SpiritFinanceCorrelation.computed_at.desc())
        .first()
    )
    insights = _parse_insight_summary(row.insight_summary) if row else []
    return jsonify(
        {
            "insights": insights,
            "recommendations": _static_recommendations(),
        }
    )
