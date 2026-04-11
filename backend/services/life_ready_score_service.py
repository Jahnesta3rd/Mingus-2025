#!/usr/bin/env python3
"""Life Ready Score: weighted composite of vibe, body, wellness, finances, and cash-flow stability."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text

from backend.models.database import db
from backend.models.financial_setup import RecurringExpense
from backend.models.life_correlation import LifeScoreSnapshot
from backend.models.life_ledger import LifeLedgerProfile
from backend.models.transaction_schedule import IncomeStream, ScheduledExpense
from backend.models.user_models import User
from backend.models.wellness import WeeklyCheckin, WellnessScore

logger = logging.getLogger(__name__)

_W_VIBE = 0.30
_W_BODY = 0.20
_W_WELLNESS = 0.15
_W_FIN = 0.25
_W_STAB = 0.10

_NEUTRAL = 50
_TREND_EPS = 3


def _clamp_0_100(x: float) -> int:
    return int(max(0, min(100, round(x))))


def _coerce_float(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _normalize_wellness_score(raw: float | None) -> float | None:
    """Accept 0–10 or 0–100 scale; return 0–100."""
    if raw is None:
        return None
    v = float(raw)
    if v <= 10.5:
        return max(0.0, min(100.0, v * 10.0))
    return max(0.0, min(100.0, v))


def _wellness_input_for_user(user_id: int) -> float | None:
    """Prefer WellnessScore for the latest check-in week; else average 1–10 fields on latest WeeklyCheckin."""
    latest = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .order_by(WeeklyCheckin.week_ending_date.desc())
        .first()
    )
    if latest is None:
        return None
    ws = WellnessScore.query.filter_by(
        user_id=user_id, week_ending_date=latest.week_ending_date
    ).first()
    if ws is not None and ws.overall_wellness_score is not None:
        return _normalize_wellness_score(_coerce_float(ws.overall_wellness_score))
    vals: list[int] = []
    for attr in (
        "overall_mood",
        "sleep_quality",
        "relationship_satisfaction",
    ):
        n = getattr(latest, attr, None)
        if n is not None:
            vals.append(int(n))
    if not vals:
        return None
    return _normalize_wellness_score(sum(vals) / len(vals))


def _financial_health_from_profile(user_id: int) -> float | None:
    """Savings rate as percentage 0–100: (income − expenses) / income × 100."""
    user = db.session.get(User, user_id)
    if user is None:
        return None
    email = (user.email or "").strip().lower()
    if not email:
        return None
    try:
        row = db.session.execute(
            text("SELECT financial_info FROM user_profiles WHERE email = :email"),
            {"email": email},
        ).fetchone()
    except Exception as e:
        logger.warning("life_ready financial_info load failed user_id=%s: %s", user_id, e)
        return None
    raw = row[0] if row else None
    if not raw:
        return None
    try:
        fi = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError):
        return None
    if not isinstance(fi, dict):
        return None
    monthly_income = _coerce_float(
        fi.get("monthlyTakehome") or fi.get("monthlyIncome")
    )
    if monthly_income is None or monthly_income <= 0:
        return None
    me = fi.get("monthlyExpenses")
    if not isinstance(me, dict):
        me = {}
    total_expenses = sum(
        float(me.get(k, 0) or 0)
        for k in (
            "rent",
            "carPayment",
            "insurance",
            "groceries",
            "utilities",
            "studentLoanPayment",
            "creditCardMinimum",
        )
    )
    savings_rate = (monthly_income - total_expenses) / monthly_income
    return max(0.0, min(100.0, savings_rate * 100.0))


def _stability_score(user_id: int) -> float:
    has_income = (
        IncomeStream.query.filter_by(user_id=user_id, is_active=True).first() is not None
    )
    has_recurring_expense = (
        RecurringExpense.query.filter_by(user_id=user_id, is_active=True).first()
        is not None
    )
    has_scheduled_expense = (
        ScheduledExpense.query.filter_by(user_id=user_id, is_active=True).first()
        is not None
    )
    has_expense = has_recurring_expense or has_scheduled_expense
    return 100.0 if (has_income and has_expense) else 10.0


def _component_or_neutral(x: float | None) -> float:
    return float(_NEUTRAL) if x is None else float(x)


def _weighted_total(
    vibe: float, body: float, wellness: float, financial: float, stability: float
) -> int:
    total = (
        vibe * _W_VIBE
        + body * _W_BODY
        + wellness * _W_WELLNESS
        + financial * _W_FIN
        + stability * _W_STAB
    )
    return _clamp_0_100(total)


def _financial_from_snapshot_rate(rate: float | None) -> float:
    if rate is None:
        return float(_NEUTRAL)
    r = float(rate)
    if r <= 1.0:
        return max(0.0, min(100.0, r * 100.0))
    return max(0.0, min(100.0, r))


def _score_from_snapshot(snap: LifeScoreSnapshot) -> int:
    """Approximate prior Life Ready Score using stored snapshot fields; stability unknown → neutral."""
    vibe = _component_or_neutral(
        _coerce_float(snap.best_vibe_combined_score)
    )
    body = _component_or_neutral(_coerce_float(snap.body_score))
    w_raw = _coerce_float(snap.avg_wellness_score)
    wellness = _component_or_neutral(
        _normalize_wellness_score(w_raw) if w_raw is not None else None
    )
    financial = _financial_from_snapshot_rate(_coerce_float(snap.monthly_savings_rate))
    stability = float(_NEUTRAL)
    return _weighted_total(vibe, body, wellness, financial, stability)


def _trend_vs_snapshot(user_id: int, current: int) -> str:
    last = (
        LifeScoreSnapshot.query.filter_by(user_id=user_id)
        .order_by(LifeScoreSnapshot.snapshot_date.desc())
        .first()
    )
    if last is None:
        return "stable"
    previous = _score_from_snapshot(last)
    delta = current - previous
    if delta >= _TREND_EPS:
        return "improving"
    if delta <= -_TREND_EPS:
        return "declining"
    return "stable"


def _headline(
    vibe: float, body: float, wellness: float, financial: float, stability: float
) -> str:
    raw = {
        "vibe": vibe,
        "body": body,
        "wellness": wellness,
        "financial": financial,
        "stability": stability,
    }
    lo = min(raw, key=raw.get)
    hi = max(raw, key=raw.get)
    spread = raw[hi] - raw[lo]
    if lo == "financial" and raw["financial"] < 55:
        return "Your financial foundation is the area with the most room to grow."
    if spread < 12:
        return "You're balanced across all areas. Keep the momentum."
    if hi == "vibe":
        return "Your relationship energy is your strongest asset right now."
    if hi == "body":
        return "Your physical readiness is leading the way right now."
    if hi == "wellness":
        return "Your weekly wellness habits are carrying your overall readiness."
    if hi == "financial":
        return "Your savings picture is the strongest pillar of your readiness right now."
    if hi == "stability":
        return "Having income and expenses mapped out is anchoring your readiness."
    return "You're balanced across all areas. Keep the momentum."


def compute_life_ready_score(user_id: int) -> dict[str, Any]:
    """
    Composite 0–100 score with breakdown, trend vs latest LifeScoreSnapshot, and headline.
    Missing inputs use neutral 50.
    """
    profile = LifeLedgerProfile.query.filter_by(user_id=user_id).first()
    vibe_raw = _coerce_float(profile.vibe_score) if profile else None
    body_raw = _coerce_float(profile.body_score) if profile else None

    vibe = _component_or_neutral(vibe_raw)
    body = _component_or_neutral(body_raw)
    wellness = _component_or_neutral(_wellness_input_for_user(user_id))
    financial = _component_or_neutral(_financial_health_from_profile(user_id))
    stability = _stability_score(user_id)

    life_ready_score = _weighted_total(vibe, body, wellness, financial, stability)
    trend = _trend_vs_snapshot(user_id, life_ready_score)
    headline = _headline(vibe, body, wellness, financial, stability)

    return {
        "life_ready_score": life_ready_score,
        "components": {
            "vibe": {"score": int(round(vibe)), "weight": _W_VIBE},
            "body": {"score": int(round(body)), "weight": _W_BODY},
            "wellness": {"score": int(round(wellness)), "weight": _W_WELLNESS},
            "financial": {"score": int(round(financial)), "weight": _W_FIN},
            "stability": {"score": int(round(stability)), "weight": _W_STAB},
        },
        "trend": trend,
        "headline": headline,
    }
