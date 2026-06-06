#!/usr/bin/env python3
"""Life Ready Score: weighted composite across ledger, wellness, finances, and cash-flow stability.

Eight nominal components (Financial, Roof, Career, Vibe, Vehicle, Body, Wellness, Stability);
Career is inactive until a metric exists — its weight is excluded and active weights renormalize to 1.0.
"""

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

# Nominal Whole-Life weights (8 slots). Career is inactive: excluded from ``_ACTIVE_WEIGHT_SUM``.
_NOMINAL_WEIGHTS: dict[str, float] = {
    "financial": 0.20,
    "roof": 0.20,
    "career": 0.14,
    "vibe": 0.12,
    "vehicle": 0.12,
    "body": 0.08,
    "wellness": 0.08,
    "stability": 0.06,
}
_ACTIVE_COMPONENT_KEYS: tuple[str, ...] = (
    "financial",
    "roof",
    "vibe",
    "vehicle",
    "body",
    "wellness",
    "stability",
)
_ACTIVE_WEIGHT_SUM = sum(_NOMINAL_WEIGHTS[k] for k in _ACTIVE_COMPONENT_KEYS)

_NEUTRAL = 50
_TREND_EPS = 3
_MIN_PILLARS_FOR_SCORE = 3
_PILLARS_TOTAL = 4


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


def _financial_health_from_profile(user_id: str) -> float | None:
    """Savings rate as percentage 0–100: (income − expenses) / income × 100."""
    user = db.session.query(User).filter_by(user_id=user_id).first()
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


def _stability_has_income_and_expense(user_id: int) -> bool:
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
    return bool(has_income and has_expense)


def _stability_score(user_id: int) -> float:
    return 100.0 if _stability_has_income_and_expense(user_id) else 10.0


def _assessment_results_meaningful(raw: Any) -> bool:
    """True when user_profiles.assessment_results has usable content (not NULL / empty)."""
    if raw is None:
        return False
    if isinstance(raw, str):
        s = raw.strip()
        if not s or s == "{}":
            return False
        try:
            parsed: Any = json.loads(s)
        except (TypeError, ValueError):
            return False
    elif isinstance(raw, (dict, list)):
        parsed = raw
    else:
        return False
    if isinstance(parsed, dict):
        return len(parsed) > 0
    if isinstance(parsed, list):
        return len(parsed) > 0
    return False


def _user_profile_assessment_raw(email: str) -> Any | None:
    if not email:
        return None
    try:
        row = db.session.execute(
            text(
                "SELECT assessment_results FROM user_profiles WHERE email = :email"
            ),
            {"email": email},
        ).fetchone()
    except Exception as e:
        logger.warning("life_ready assessment_results load failed email=%s: %s", email, e)
        return None
    return row[0] if row else None


def _vibe_body_pillar_meaningful(
    profile: LifeLedgerProfile | None, assessment_raw: Any
) -> bool:
    """Pillar 1: any ledger assessment (vibe/body/roof/vehicle) or synced assessment_results."""
    if _assessment_results_meaningful(assessment_raw):
        return True
    if profile is None:
        return False
    return (
        profile.vibe_score is not None
        or profile.body_score is not None
        or profile.roof_score is not None
        or profile.vehicle_score is not None
    )


def _wellness_pillar_meaningful(user_id: int) -> bool:
    """Pillar 2: any check-in or stored wellness score row."""
    return (
        WeeklyCheckin.query.filter_by(user_id=user_id).first() is not None
        or WellnessScore.query.filter_by(user_id=user_id).first() is not None
    )


def _stability_pillar_meaningful(user_id: int) -> bool:
    """Pillar 4: only when both active income and expense mapping exist (not the 10 fallback)."""
    return _stability_has_income_and_expense(user_id)


def _components_payload(
    *,
    financial: float,
    roof: float,
    vibe: float,
    vehicle: float,
    body: float,
    wellness: float,
    stability: float,
) -> dict[str, Any]:
    """Response order matches product naming; career is the inactive socket (no score, not in blend)."""

    def _active_slot(key: str, score: float) -> dict[str, Any]:
        return {
            "score": int(round(score)),
            "weight": _NOMINAL_WEIGHTS[key],
            "active": True,
        }

    return {
        "financial": _active_slot("financial", financial),
        "roof": _active_slot("roof", roof),
        "career": {
            "score": None,
            "weight": _NOMINAL_WEIGHTS["career"],
            "active": False,
        },
        "vibe": _active_slot("vibe", vibe),
        "vehicle": _active_slot("vehicle", vehicle),
        "body": _active_slot("body", body),
        "wellness": _active_slot("wellness", wellness),
        "stability": _active_slot("stability", stability),
    }


def _insufficient_score_payload(
    components: dict[str, Any], pillars_complete: int
) -> dict[str, Any]:
    return {
        "life_ready_score": None,
        "has_sufficient_data": False,
        "pillars_complete": pillars_complete,
        "pillars_total": _PILLARS_TOTAL,
        "components": components,
        "trend": None,
        "headline": None,
    }


def _sufficient_score_payload(
    life_ready_score: int,
    components: dict[str, Any],
    trend: str,
    headline: str,
    pillars_complete: int,
) -> dict[str, Any]:
    return {
        "life_ready_score": life_ready_score,
        "has_sufficient_data": True,
        "pillars_complete": pillars_complete,
        "pillars_total": _PILLARS_TOTAL,
        "components": components,
        "trend": trend,
        "headline": headline,
    }


def _component_or_neutral(x: float | None) -> float:
    return float(_NEUTRAL) if x is None else float(x)


def _weighted_total(
    *,
    financial: float,
    roof: float,
    vibe: float,
    vehicle: float,
    body: float,
    wellness: float,
    stability: float,
) -> int:
    """Weighted mean over active components only; nominal weights renormalize (inactive career omitted)."""
    scores = {
        "financial": financial,
        "roof": roof,
        "vibe": vibe,
        "vehicle": vehicle,
        "body": body,
        "wellness": wellness,
        "stability": stability,
    }
    blended = sum(
        scores[k] * _NOMINAL_WEIGHTS[k] for k in _ACTIVE_COMPONENT_KEYS
    ) / float(_ACTIVE_WEIGHT_SUM)
    return _clamp_0_100(blended)


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
    roof = _component_or_neutral(_coerce_float(snap.roof_score))
    vehicle = _component_or_neutral(_coerce_float(snap.vehicle_score))
    w_raw = _coerce_float(snap.avg_wellness_score)
    wellness = _component_or_neutral(
        _normalize_wellness_score(w_raw) if w_raw is not None else None
    )
    financial = _financial_from_snapshot_rate(_coerce_float(snap.monthly_savings_rate))
    stability = float(_NEUTRAL)
    return _weighted_total(
        financial=financial,
        roof=roof,
        vibe=vibe,
        vehicle=vehicle,
        body=body,
        wellness=wellness,
        stability=stability,
    )


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
    *,
    financial: float,
    roof: float,
    vibe: float,
    vehicle: float,
    body: float,
    wellness: float,
    stability: float,
) -> str:
    raw = {
        "vibe": vibe,
        "body": body,
        "roof": roof,
        "vehicle": vehicle,
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
    if hi == "roof":
        return "Your housing readiness is leading the way right now."
    if hi == "vehicle":
        return "Your vehicle readiness is leading the way right now."
    if hi == "wellness":
        return "Your weekly wellness habits are carrying your overall readiness."
    if hi == "financial":
        return "Your savings picture is the strongest pillar of your readiness right now."
    if hi == "stability":
        return "Having income and expenses mapped out is anchoring your readiness."
    return "You're balanced across all areas. Keep the momentum."


def compute_life_ready_score(user_id: str) -> dict[str, Any]:
    """
    Composite 0–100 score with breakdown, trend vs latest LifeScoreSnapshot, and headline.
    Missing inputs for *active* components use neutral 50. Career is inactive and never filled.

    When fewer than ``_MIN_PILLARS_FOR_SCORE`` of four pillars (ledger assessments including
    vibe/body/roof/vehicle + synced assessments, wellness, financial, stability) have real
    data, returns ``life_ready_score`` null and ``has_sufficient_data`` false instead of a
    neutral-blended number.

    Args:
        user_id: External user identifier (``User.user_id``, UUID string from JWT).
    """
    user = db.session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        n = float(_NEUTRAL)
        return _insufficient_score_payload(
            _components_payload(
                financial=n,
                roof=n,
                vibe=n,
                vehicle=n,
                body=n,
                wellness=n,
                stability=n,
            ),
            0,
        )

    uid = user.id
    ext_user_id = user.user_id
    email = (user.email or "").strip().lower()

    profile = LifeLedgerProfile.query.filter_by(user_id=uid).first()
    assessment_raw = _user_profile_assessment_raw(email)

    ledger_pillar = _vibe_body_pillar_meaningful(profile, assessment_raw)
    wellness_pillar = _wellness_pillar_meaningful(uid)
    financial_pillar = _financial_health_from_profile(ext_user_id) is not None
    stability_pillar = _stability_pillar_meaningful(uid)

    pillars_complete = sum(
        (ledger_pillar, wellness_pillar, financial_pillar, stability_pillar)
    )

    vibe_raw = _coerce_float(profile.vibe_score) if profile else None
    body_raw = _coerce_float(profile.body_score) if profile else None
    roof_raw = _coerce_float(profile.roof_score) if profile else None
    vehicle_raw = _coerce_float(profile.vehicle_score) if profile else None

    vibe = _component_or_neutral(vibe_raw)
    body = _component_or_neutral(body_raw)
    roof = _component_or_neutral(roof_raw)
    vehicle = _component_or_neutral(vehicle_raw)
    wellness = _component_or_neutral(_wellness_input_for_user(uid))
    financial = _component_or_neutral(_financial_health_from_profile(ext_user_id))
    stability = _stability_score(uid)

    components = _components_payload(
        financial=financial,
        roof=roof,
        vibe=vibe,
        vehicle=vehicle,
        body=body,
        wellness=wellness,
        stability=stability,
    )

    if pillars_complete < _MIN_PILLARS_FOR_SCORE:
        return _insufficient_score_payload(components, pillars_complete)

    life_ready_score = _weighted_total(
        financial=financial,
        roof=roof,
        vibe=vibe,
        vehicle=vehicle,
        body=body,
        wellness=wellness,
        stability=stability,
    )
    trend = _trend_vs_snapshot(uid, life_ready_score)
    headline = _headline(
        financial=financial,
        roof=roof,
        vibe=vibe,
        vehicle=vehicle,
        body=body,
        wellness=wellness,
        stability=stability,
    )

    return _sufficient_score_payload(
        life_ready_score, components, trend, headline, pillars_complete
    )
