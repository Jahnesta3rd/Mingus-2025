#!/usr/bin/env python3
"""
Public /api/daily-outlook HTTP surface.

Adapts legacy ``daily_outlook_api`` shapes to the dashboard ``DailyOutlookData`` JSON
contract without modifying ``backend/api/daily_outlook_api.py`` or outlook services.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, desc, func

from backend.auth.decorators import get_current_jwt_user, require_auth
from backend.models.database import db
from backend.models.daily_outlook import DailyOutlook

logger = logging.getLogger(__name__)

daily_outlook_public_bp = Blueprint(
    "daily_outlook_public",
    __name__,
    url_prefix="/api/daily-outlook",
)

_MILESTONE_DAYS = (3, 7, 14, 30, 60, 100)
_CONTENT_SVC: Any = None

_DEFAULT_EMPTY_TOMORROW_TEASER: dict[str, Any] = {
    "title": "Tomorrow's outlook will appear here",
    "description": "Complete today's check-in to unlock a preview of tomorrow.",
    "excitement_level": 0,
}


def _content_service() -> Any:
    global _CONTENT_SVC
    if _CONTENT_SVC is None:
        from backend.services.daily_outlook_content_service import DailyOutlookContentService

        _CONTENT_SVC = DailyOutlookContentService()
    return _CONTENT_SVC


def _calculate_streak_count(internal_user_id: int, current_date: date) -> int:
    """Consecutive outlook days ending before current_date (same logic as legacy API)."""
    try:
        recent_outlook = DailyOutlook.query.filter(
            and_(
                DailyOutlook.user_id == internal_user_id,
                DailyOutlook.date < current_date,
            )
        ).order_by(desc(DailyOutlook.date)).first()

        if not recent_outlook:
            return 0

        streak_count = 0
        check_date = recent_outlook.date

        while True:
            outlook = DailyOutlook.query.filter(
                and_(
                    DailyOutlook.user_id == internal_user_id,
                    DailyOutlook.date == check_date,
                )
            ).first()
            if not outlook:
                break
            streak_count += 1
            check_date -= timedelta(days=1)
            if streak_count > 365:
                break
        return streak_count
    except Exception as e:
        logger.error("streak calc user %s: %s", internal_user_id, e)
        return 0


def _normalize_user_tier(raw: Optional[str]) -> str:
    allowed = ("budget", "budget_career_vehicle", "mid_tier", "professional")
    if not raw:
        return "budget"
    key = str(raw).strip().lower()
    if key in allowed:
        return key
    return "budget"


def _next_milestone_days(current_streak: int) -> int:
    for m in _MILESTONE_DAYS:
        if current_streak < m:
            return m
    return int(current_streak) + 3


def _streak_payload(internal_user_id: int, current_streak: int) -> dict[str, Any]:
    longest = (
        db.session.query(func.max(DailyOutlook.streak_count))
        .filter(DailyOutlook.user_id == internal_user_id)
        .scalar()
    )
    longest_val = int(longest or 0)
    longest_val = max(longest_val, current_streak)
    next_m = _next_milestone_days(current_streak)
    progress = int(min(100, round(100 * current_streak / next_m))) if next_m else 100
    milestone_reached = current_streak > 0 and current_streak in _MILESTONE_DAYS
    return {
        "current_streak": current_streak,
        "longest_streak": longest_val,
        "milestone_reached": milestone_reached,
        "next_milestone": next_m,
        "progress_percentage": progress,
    }


def _balance_block(outlook: DailyOutlook, internal_user_id: int, today: date) -> dict[str, Any]:
    value = int(outlook.balance_score or 0)
    prev_row = DailyOutlook.query.filter(
        and_(
            DailyOutlook.user_id == internal_user_id,
            DailyOutlook.date == today - timedelta(days=1),
        )
    ).first()
    if prev_row is None:
        return {
            "value": value,
            "trend": "stable",
            "change_percentage": 0.0,
            "previous_value": value,
        }
    prev_val = int(prev_row.balance_score or 0)
    diff = value - prev_val
    if diff > 0:
        trend = "up"
    elif diff < 0:
        trend = "down"
    else:
        trend = "stable"
    pct = (100.0 * diff / prev_val) if prev_val else 0.0
    return {
        "value": value,
        "trend": trend,
        "change_percentage": round(float(pct), 2),
        "previous_value": prev_val,
    }


def _primary_insight_block(text: Optional[str]) -> dict[str, Any]:
    body = (text or "").strip() or "Welcome! Your financial journey starts with a single step."
    return {
        "title": "Today's insight",
        "message": body,
        "type": "neutral",
        "icon": "💡",
    }


def _encouragement_block(text: Optional[str]) -> dict[str, Any]:
    raw = (text or "").strip() or "You've got this! Every step forward is progress."
    emoji = "✨"
    if raw and ord(raw[0]) > 127:
        emoji = raw[0]
        raw = raw[1:].lstrip()
    return {"text": raw, "type": "motivational", "emoji": emoji}


def _difficulty_to_priority(difficulty: Optional[str]) -> str:
    d = (difficulty or "medium").lower()
    if d == "easy":
        return "low"
    if d == "hard":
        return "high"
    return "medium"


def _serialize_quick_actions(
    raw: Any,
    actions_completed: Optional[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions_completed = actions_completed or {}
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        qid = str(item.get("id") or item.get("action_id") or f"quick_{idx}")
        title = str(item.get("title") or item.get("action") or "Action")
        desc = str(item.get("description") or "")
        rec = actions_completed.get(qid) or {}
        completed = bool(rec.get("completed", False))
        priority = item.get("priority")
        if priority not in ("high", "medium", "low"):
            priority = _difficulty_to_priority(item.get("difficulty"))
        est = item.get("estimated_time", "5 minutes")
        out.append(
            {
                "id": qid,
                "title": title,
                "description": desc,
                "completed": completed,
                "priority": priority,
                "estimated_time": str(est),
            }
        )
    return out


def _teaser_from_string(teaser: str) -> dict[str, Any]:
    s = (teaser or "").strip() or "Tomorrow: More insights to help you on your financial journey."
    if ":" in s:
        title, rest = s.split(":", 1)
        title = title.strip()[:120] or "Tomorrow"
        description = rest.strip() or s
    else:
        title = "Tomorrow"
        description = s
    excitement = min(5, max(1, len(description) // 45 + 1))
    return {"title": title, "description": description, "excitement_level": excitement}


def _build_tomorrow_teaser_for_user(
    internal_user_id: int, external_user_id: str, streak_for_teaser: int
) -> dict[str, Any]:
    try:
        from backend.services.daily_outlook_content_service import UserData
        from backend.services.feature_flag_service import FeatureFlagService

        fs = FeatureFlagService()
        tier = fs.get_user_tier(str(external_user_id))
        ud = UserData(
            user_id=internal_user_id,
            tier=tier,
            location="Unknown",
            relationship_status="single",
            financial_score=50.0,
            wellness_score=50.0,
            relationship_score=50.0,
            career_score=50.0,
            streak_count=streak_for_teaser,
            recent_activity={},
            spending_patterns={},
            goals={},
            assessment_results={},
        )
        teaser_str = _content_service().build_tomorrow_teaser(ud)
        return _teaser_from_string(teaser_str)
    except Exception as e:
        logger.warning("tomorrow teaser fallback: %s", e)
        return _teaser_from_string(
            "Tomorrow: More insights to help you on your financial journey."
        )


def _empty_defaults(user_display_name: str, user_tier: str) -> dict[str, Any]:
    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "user_name": user_display_name,
        "current_time": now,
        "balance_score": {
            "value": 0,
            "trend": "stable",
            "change_percentage": 0.0,
            "previous_value": 0,
        },
        "primary_insight": {
            "title": "Get started",
            "message": "Complete your first check-in to unlock your personalized daily outlook.",
            "type": "neutral",
            "icon": "👋",
        },
        "quick_actions": [],
        "encouragement_message": {
            "text": "We're glad you're here. Small steps lead to big change.",
            "type": "reminder",
            "emoji": "🌱",
        },
        "streak_data": {
            "current_streak": 0,
            "longest_streak": 0,
            "milestone_reached": False,
            "next_milestone": 3,
            "progress_percentage": 0,
        },
        "tomorrow_teaser": dict(_DEFAULT_EMPTY_TOMORROW_TEASER),
        "user_tier": user_tier,
    }


def _compose_full_payload(
    user_row: Any,
    outlook: DailyOutlook,
    *,
    touch_view: bool,
) -> dict[str, Any]:
    today = date.today()
    internal_id = int(user_row.id)
    streak = _calculate_streak_count(internal_id, today)
    if touch_view:
        outlook.viewed_at = datetime.utcnow()
        outlook.streak_count = streak
        db.session.commit()

    display = (
        (user_row.first_name or "").strip()
        or (user_row.email or "there").split("@", 1)[0]
        or "there"
    )
    tier = _normalize_user_tier(getattr(user_row, "tier", None))

    balance = _balance_block(outlook, internal_id, today)
    primary = _primary_insight_block(outlook.primary_insight)
    encouragement = _encouragement_block(outlook.encouragement_message)
    quick = _serialize_quick_actions(outlook.quick_actions, outlook.actions_completed)
    streak_data = _streak_payload(internal_id, streak)
    teaser = _build_tomorrow_teaser_for_user(internal_id, str(user_row.user_id), streak)

    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return {
        "user_name": display,
        "current_time": now,
        "balance_score": balance,
        "primary_insight": primary,
        "quick_actions": quick,
        "encouragement_message": encouragement,
        "streak_data": streak_data,
        "tomorrow_teaser": teaser,
        "user_tier": tier,
    }


@daily_outlook_public_bp.route("/", methods=["GET"], strict_slashes=False)
@require_auth
def get_daily_outlook():
    user = get_current_jwt_user()
    if not user:
        return jsonify({"error": "Authentication required", "message": "User not found"}), 401

    today = date.today()
    display = (
        (user.first_name or "").strip()
        or (user.email or "there").split("@", 1)[0]
        or "there"
    )
    tier = _normalize_user_tier(getattr(user, "tier", None))

    outlook = DailyOutlook.query.filter(
        and_(DailyOutlook.user_id == user.id, DailyOutlook.date == today)
    ).first()

    if not outlook:
        return jsonify(_empty_defaults(display, tier)), 200

    try:
        return jsonify(_compose_full_payload(user, outlook, touch_view=True)), 200
    except Exception as e:
        logger.exception("daily outlook GET: %s", e)
        db.session.rollback()
        return jsonify({"error": "server_error", "message": "Failed to load daily outlook"}), 500


@daily_outlook_public_bp.route("/tomorrow", methods=["GET"], strict_slashes=False)
@require_auth
def get_tomorrow_teaser():
    user = get_current_jwt_user()
    if not user:
        return jsonify({"error": "Authentication required", "message": "User not found"}), 401

    today = date.today()
    display = (
        (user.first_name or "").strip()
        or (user.email or "there").split("@", 1)[0]
        or "there"
    )
    tier = _normalize_user_tier(getattr(user, "tier", None))
    streak = _calculate_streak_count(int(user.id), today)

    outlook = DailyOutlook.query.filter(
        and_(DailyOutlook.user_id == user.id, DailyOutlook.date == today)
    ).first()

    base = _empty_defaults(display, tier)
    if outlook:
        base["tomorrow_teaser"] = _build_tomorrow_teaser_for_user(
            int(user.id), str(user.user_id), streak
        )
    base["current_time"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    return jsonify(base), 200


@daily_outlook_public_bp.route("/actions", methods=["POST"], strict_slashes=False)
@require_auth
def post_action():
    user = get_current_jwt_user()
    if not user:
        return jsonify({"error": "Authentication required", "message": "User not found"}), 401

    data = request.get_json(silent=True) or {}
    action_id = data.get("action_id")
    if action_id is None or not isinstance(action_id, str) or not action_id.strip():
        return jsonify({"error": "validation_error", "message": "action_id is required"}), 400
    if "completed" not in data or not isinstance(data["completed"], bool):
        return jsonify({"error": "validation_error", "message": "completed boolean is required"}), 400

    today = date.today()
    outlook = DailyOutlook.query.filter(
        and_(DailyOutlook.user_id == user.id, DailyOutlook.date == today)
    ).first()
    if not outlook:
        return jsonify({"success": True, "message": "No outlook for today"}), 200

    actions_completed = dict(outlook.actions_completed or {})
    actions_completed[action_id.strip()] = {
        "completed": data["completed"],
        "completed_at": datetime.utcnow().isoformat(),
        "notes": "",
    }
    outlook.actions_completed = actions_completed
    db.session.commit()

    quick = _serialize_quick_actions(outlook.quick_actions, outlook.actions_completed)
    updated = next((q for q in quick if q["id"] == action_id.strip()), None)
    if updated:
        return jsonify(updated), 200
    return jsonify({"success": True, "action_id": action_id.strip(), "completed": data["completed"]}), 200


@daily_outlook_public_bp.route("/rating", methods=["POST"], strict_slashes=False)
@require_auth
def post_rating():
    user = get_current_jwt_user()
    if not user:
        return jsonify({"error": "Authentication required", "message": "User not found"}), 401

    data = request.get_json(silent=True) or {}
    rating = data.get("rating")
    try:
        rating_int = int(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "validation_error", "message": "rating must be an integer 1–5"}), 400
    if rating_int < 1 or rating_int > 5:
        return jsonify({"error": "validation_error", "message": "rating must be between 1 and 5"}), 400

    today = date.today()
    outlook = DailyOutlook.query.filter(
        and_(DailyOutlook.user_id == user.id, DailyOutlook.date == today)
    ).first()
    if not outlook:
        return jsonify({"success": True, "message": "No outlook for today"}), 200

    outlook.user_rating = rating_int
    db.session.commit()

    ab_test_flags: dict[str, Any] = {}
    if rating_int >= 4:
        ab_test_flags["high_rating_user"] = True
    elif rating_int <= 2:
        ab_test_flags["low_rating_user"] = True

    return (
        jsonify(
            {
                "success": True,
                "message": "Rating submitted successfully",
                "rating": rating_int,
                "ab_test_flags": ab_test_flags,
            }
        ),
        200,
    )

