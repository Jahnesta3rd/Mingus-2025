#!/usr/bin/env python3
"""Evaluate and persist financial/vibe alerts after checkups or Connection Trend saves."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from backend.models.alerts import UserAlert
from backend.models.connection_trend import ConnectionTrendAssessment
from backend.models.database import db
from backend.models.user_models import User
from backend.models.vibe_tracker import VibePersonAssessment, VibeTrackedPerson
from backend.services.cash_forecast_service import build_forecast_for_user
from backend.services.life_correlation_service import compute_score_deltas, get_snapshots


def _combined_score(assessment: VibePersonAssessment) -> int:
    return int(
        round((assessment.emotional_score + assessment.financial_score) / 2.0)
    )


def _format_money_monthly(value: float) -> str:
    v = float(value)
    if abs(v - round(v)) < 0.01:
        return f"${int(round(v))}/mo"
    return f"${v:,.0f}/mo"


def _monthly_cost_for_person_forecast(
    user_id: int, person_nickname: str
) -> float | None:
    nick = (person_nickname or "").strip().lower()
    if not nick:
        return None
    try:
        _daily, _summaries, breakdown = build_forecast_for_user(user_id, days=90)
    except Exception:
        return None
    if not breakdown:
        return None
    for row in breakdown:
        rn = (row.get("nickname") or "").strip().lower()
        if rn == nick:
            try:
                return float(row.get("monthly_cost") or 0)
            except (TypeError, ValueError):
                return None
    return None


def _thirty_day_linked_cost_for_nickname(user_id: int, nickname: str) -> float:
    """Sum important-date costs linked to nickname within the next 30 days."""
    from backend.routes import vibe_tracker as vtr

    user = db.session.get(User, user_id)
    if not user:
        return 0.0
    email = (user.email or "").strip().lower()
    if not email:
        return 0.0
    _bal, important = vtr._load_profile_balance_and_dates(email)
    if not isinstance(important, dict):
        important = {}
    nick = (nickname or "").strip()
    if not nick:
        return 0.0
    today = date.today()
    horizon_end = today + timedelta(days=30)
    total = 0.0
    for ev in vtr._iter_normalized_important_events(important):
        pn = (ev.get("person_nickname") or "").strip()
        if pn != nick:
            continue
        try:
            evd = date.fromisoformat(str(ev["date"])[:10])
        except ValueError:
            continue
        if evd < today:
            continue
        if evd > horizon_end:
            continue
        try:
            total += float(ev.get("cost") or 0)
        except (TypeError, ValueError):
            pass
    return total


def check_for_alerts(user_id: int, person_id: uuid.UUID) -> list[dict]:
    """
    After a new Vibe Checkup or Connection Trend assessment, evaluate alert rules,
    insert UserAlert rows, and return serialized alert payloads (with id).
    """
    person = db.session.get(VibeTrackedPerson, person_id)
    if not person or person.user_id != user_id:
        return []

    to_persist: list[dict] = []

    # --- ALERT 1: vibe score drop (needs previous assessment) ---
    assessments = (
        VibePersonAssessment.query.filter_by(tracked_person_id=person_id)
        .order_by(
            VibePersonAssessment.completed_at.desc(),
            VibePersonAssessment.id.desc(),
        )
        .limit(2)
        .all()
    )
    if len(assessments) >= 2:
        latest_a, prev_a = assessments[0], assessments[1]
        c_latest = _combined_score(latest_a)
        c_prev = _combined_score(prev_a)
        if c_latest < c_prev - 10:
            delta = c_prev - c_latest
            monthly = _monthly_cost_for_person_forecast(user_id, person.nickname)
            if monthly is None:
                monthly_str = "$0/mo"
            else:
                monthly_str = _format_money_monthly(monthly)
            to_persist.append(
                {
                    "type": "vibe_score_drop",
                    "severity": "info",
                    "nickname": person.nickname,
                    "message": (
                        f"Your vibe score for {person.nickname} has dropped {delta} points. "
                        f"Their estimated costs in your forecast are {monthly_str}."
                    ),
                    "action_label": "Review forecast",
                    "action_route": "/dashboard/forecast",
                }
            )

    # --- ALERT 2: Connection Trend warning tiers ---
    ct = (
        ConnectionTrendAssessment.query.filter_by(
            user_id=user_id,
            person_id=person_id,
        )
        .order_by(ConnectionTrendAssessment.assessed_at.desc())
        .first()
    )
    if ct and (ct.fade_tier or "") in ("fading", "dipping", "cloaking"):
        upcoming = _thirty_day_linked_cost_for_nickname(user_id, person.nickname)
        if upcoming > 0:
            to_persist.append(
                {
                    "type": "connection_trend_warning",
                    "severity": "warning",
                    "nickname": person.nickname,
                    "message": (
                        f"The pattern with {person.nickname} shows some distance forming. "
                        "You have upcoming costs linked to them in the next 30 days."
                    ),
                    "action_label": "See what's coming up",
                    "action_route": "/dashboard/roster",
                }
            )

    # --- ALERT 3: savings vs relationship cost (same gate as Life Correlation Engine) ---
    snapshots = get_snapshots(user_id, days=180)
    deltas = compute_score_deltas(snapshots)
    srd = deltas.get("savings_rate_delta")
    rcd = deltas.get("relationship_cost_delta")
    if (
        len(snapshots) >= 3
        and srd is not None
        and rcd is not None
        and srd < -0.05
        and rcd > 2000
    ):
        to_persist.append(
            {
                "type": "savings_drag",
                "severity": "warning",
                "nickname": None,
                "message": (
                    "Your savings rate has dropped while your relationship costs have increased. "
                    "The forecast has details."
                ),
                "action_label": "View forecast",
                "action_route": "/dashboard/forecast",
            }
        )

    created: list[dict] = []
    now = datetime.utcnow()
    for item in to_persist:
        row = UserAlert(
            user_id=user_id,
            alert_type=item["type"],
            severity=item["severity"],
            message=item["message"],
            action_label=item["action_label"],
            action_route=item["action_route"],
            created_at=now,
        )
        db.session.add(row)
        db.session.flush()
        created.append(
            {
                "id": str(row.id),
                "type": row.alert_type,
                "severity": row.severity,
                "nickname": item.get("nickname"),
                "message": row.message,
                "action_label": row.action_label,
                "action_route": row.action_route,
            }
        )

    if created:
        db.session.commit()

    return created
