#!/usr/bin/env python3
"""Self Card: body, mind, sleep, and stress-spending signals for the roster Self row."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal
from typing import Any

from backend.models.life_correlation import LifeScoreSnapshot
from backend.models.life_ledger import LifeLedgerProfile
from backend.models.wellness import WeeklyCheckin


_TREND_EPS = 0.5


def _clamp_0_100(x: float) -> int:
    return int(max(0, min(100, round(x))))


def _coerce_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, Decimal):
        return float(x)
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _trend_direction(current: float | None, previous: float | None) -> str:
    if current is None or previous is None:
        return "flat"
    delta = current - previous
    if delta > _TREND_EPS:
        return "up"
    if delta < -_TREND_EPS:
        return "down"
    return "flat"


def _mind_score_for_window(checkins: list[WeeklyCheckin]) -> float | None:
    """Same formula as spec for up to four rows (newest-first order not required here)."""
    if not checkins:
        return None
    stress_vals = [
        int(c.stress_level)
        for c in checkins
        if c.stress_level is not None and 1 <= int(c.stress_level) <= 10
    ]
    if stress_vals:
        avg_stress = sum(stress_vals) / len(stress_vals)
    else:
        avg_stress = 5.0
    avg_stress_inverted = (10.0 - avg_stress) * 10.0
    mindful_count = sum(
        1 for c in checkins if (c.meditation_minutes or 0) > 0
    )
    mindfulness_consistency = (mindful_count / 4.0) * 100.0
    raw = avg_stress_inverted * 0.6 + mindfulness_consistency * 0.4
    return float(_clamp_0_100(raw))


def _ordered_recent_checkins(user_id: int, limit: int) -> list[WeeklyCheckin]:
    return (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .order_by(WeeklyCheckin.week_ending_date.desc())
        .limit(limit)
        .all()
    )


def _body_trend(user_id: int, current_body: int | None) -> str:
    if current_body is None:
        return "flat"
    last_snap = (
        LifeScoreSnapshot.query.filter(
            LifeScoreSnapshot.user_id == user_id,
            LifeScoreSnapshot.body_score.isnot(None),
        )
        .order_by(LifeScoreSnapshot.snapshot_date.desc())
        .first()
    )
    if last_snap is None or last_snap.body_score is None:
        return "flat"
    return _trend_direction(float(current_body), float(last_snap.body_score))


def _sleep_avg_and_trend(recent_desc: list[WeeklyCheckin]) -> tuple[float | None, str]:
    """recent_desc: up to four checkins, newest first (week_ending_date desc)."""
    if not recent_desc:
        return None, "flat"
    hours_all = [_coerce_float(c.sleep_hours) for c in recent_desc]
    present = [h for h in hours_all if h is not None]
    sleep_avg = sum(present) / len(present) if present else None

    if len(recent_desc) < 4:
        return sleep_avg, "flat"

    last_four_asc = list(reversed(recent_desc))
    prev_two = last_four_asc[:2]
    last_two = last_four_asc[2:]
    pvals = [_coerce_float(c.sleep_hours) for c in prev_two]
    lvals = [_coerce_float(c.sleep_hours) for c in last_two]
    pavg = (
        sum(x for x in pvals if x is not None) / len([x for x in pvals if x is not None])
        if any(x is not None for x in pvals)
        else None
    )
    lavg = (
        sum(x for x in lvals if x is not None) / len([x for x in lvals if x is not None])
        if any(x is not None for x in lvals)
        else None
    )
    trend = _trend_direction(lavg, pavg)
    return sleep_avg, trend


def _mindfulness_days_this_month(user_id: int, today: date) -> int:
    start = date(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    end = date(today.year, today.month, last_day)
    rows = (
        WeeklyCheckin.query.filter(
            WeeklyCheckin.user_id == user_id,
            WeeklyCheckin.week_ending_date >= start,
            WeeklyCheckin.week_ending_date <= end,
            WeeklyCheckin.meditation_minutes > 0,
        )
        .all()
    )
    return len(rows)


def _mindfulness_streak(user_id: int) -> int:
    rows = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .order_by(WeeklyCheckin.week_ending_date.desc())
        .all()
    )
    streak = 0
    for c in rows:
        if (c.meditation_minutes or 0) > 0:
            streak += 1
        else:
            break
    return streak


def _stress_spend_current_month(user_id: int, today: date) -> float | None:
    start = date(today.year, today.month, 1)
    _, last_day = monthrange(today.year, today.month)
    end = date(today.year, today.month, last_day)
    rows = (
        WeeklyCheckin.query.filter(
            WeeklyCheckin.user_id == user_id,
            WeeklyCheckin.week_ending_date >= start,
            WeeklyCheckin.week_ending_date <= end,
        )
        .all()
    )
    if not rows:
        return None
    total = Decimal("0")
    any_val = False
    for c in rows:
        if c.stress_spending is not None:
            any_val = True
            total += Decimal(str(c.stress_spending))
    if not any_val:
        return None
    return round(float(total), 2)


def get_self_card_data(user_id: int) -> dict[str, Any]:
    today = date.today()
    profile = LifeLedgerProfile.query.filter_by(user_id=user_id).first()
    body_score = profile.body_score if profile else None

    recent8 = _ordered_recent_checkins(user_id, 8)
    recent4 = recent8[:4]
    prev4 = recent8[4:8]

    mind_score_val = _mind_score_for_window(recent4)
    mind_score = _clamp_0_100(mind_score_val) if mind_score_val is not None else None

    mind_trend = "flat"
    if len(recent8) >= 5 and prev4:
        prev_mind = _mind_score_for_window(prev4)
        if mind_score_val is not None and prev_mind is not None:
            mind_trend = _trend_direction(mind_score_val, prev_mind)

    body_trend = _body_trend(user_id, body_score)

    sleep_avg, sleep_trend = _sleep_avg_and_trend(recent4)

    mindfulness_days = _mindfulness_days_this_month(user_id, today)
    mindfulness_streak = _mindfulness_streak(user_id)

    stress_spend_monthly = _stress_spend_current_month(user_id, today)

    spending_shield_savings: float | None = None
    if (
        stress_spend_monthly is not None
        and mindfulness_streak >= 2
        and stress_spend_monthly > 0
    ):
        raw_est = stress_spend_monthly * (mindfulness_streak * 0.15)
        spending_shield_savings = round(min(raw_est, stress_spend_monthly), 2)

    body_f = float(body_score) if body_score is not None else 50.0
    mind_f = float(mind_score) if mind_score is not None else 50.0
    if sleep_avg is not None and sleep_avg >= 7:
        sleep_component = 100.0
    elif sleep_avg is not None:
        sleep_component = (sleep_avg / 7.0) * 100.0
    else:
        sleep_component = 50.0
    self_score = _clamp_0_100(
        body_f * 0.40 + mind_f * 0.40 + sleep_component * 0.20
    )

    return {
        "body_score": body_score,
        "body_trend": body_trend,
        "mind_score": mind_score,
        "mind_trend": mind_trend,
        "sleep_avg": round(sleep_avg, 2) if sleep_avg is not None else None,
        "sleep_trend": sleep_trend,
        "mindfulness_days_this_month": mindfulness_days,
        "mindfulness_streak": mindfulness_streak,
        "stress_spend_monthly": stress_spend_monthly,
        "spending_shield_savings": spending_shield_savings,
        "self_score": self_score,
    }
