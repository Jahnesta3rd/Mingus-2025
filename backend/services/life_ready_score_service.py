#!/usr/bin/env python3
"""Life Ready Score: weighted composite across ledger, wellness, finances, and cash-flow stability.

Eight nominal components (Financial, Roof, Career, Vibe, Vehicle, Body, Wellness, Stability);
all eight are active; nominal weights sum to 1.0.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text

from backend.models.career_profile import CareerProfile
from backend.models.database import db
from backend.models.employer import Employer, EmployerHealthSnapshot, LayoffEvent
from backend.models.financial_setup import RecurringExpense
from backend.models.life_correlation import LifeScoreSnapshot
from backend.models.life_ledger import LifeLedgerProfile
from backend.models.transaction_schedule import IncomeStream, ScheduledExpense
from backend.models.user_models import User
from backend.models.wellness import WeeklyCheckin, WellnessScore
from backend.services.employer_health_scoring import get_latest_snapshot

logger = logging.getLogger(__name__)

# Nominal Whole-Life weights (8 slots); sum to 1.0.
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
    "career",
    "vibe",
    "vehicle",
    "body",
    "wellness",
    "stability",
)
_ACTIVE_WEIGHT_SUM = sum(_NOMINAL_WEIGHTS[k] for k in _ACTIVE_COMPONENT_KEYS)

_SATISFACTION_TO_CAREER_SCORE: dict[int, float] = {
    1: 20.0,
    2: 35.0,
    3: 50.0,
    4: 65.0,
    5: 80.0,
}

_NEUTRAL = 50
_EDGAR_STALE_DAYS = 14
_LAYOFF_EVENT_WINDOW_DAYS = 90
_EDGAR_STRESSED_THRESHOLD = 35
_INCOME_WATCH_PERCENTILE = 25
_TREND_EPS = 3
_MIN_PILLARS_FOR_SCORE = 3
_PILLARS_TOTAL = 4
_ALERT_SEVERITY_ORDER = {"high": 0, "moderate": 1, "watch": 2}


@dataclass
class LifeAlert:
    domain: str
    severity: str
    headline: str
    detail: str
    action_label: str
    action_target: str


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


def _snapshot_refreshed_at_utc(refreshed_at: datetime) -> datetime:
    if refreshed_at.tzinfo is None:
        return refreshed_at.replace(tzinfo=timezone.utc)
    return refreshed_at.astimezone(timezone.utc)


def _employer_health_snapshot_fresh(snapshot: Any) -> bool:
    """True when employer health snapshot score is within the stale window."""
    if snapshot is None or snapshot.score is None or snapshot.refreshed_at is None:
        return False
    refreshed = _snapshot_refreshed_at_utc(snapshot.refreshed_at)
    age = datetime.now(timezone.utc) - refreshed
    return age <= timedelta(days=_EDGAR_STALE_DAYS)


def _employer_snapshot_for_cik(cik: str) -> Any | None:
    cik_padded = cik.zfill(10)
    employer = db.session.query(Employer).filter_by(cik=cik_padded).first()
    if employer is None:
        return None
    return get_latest_snapshot(employer.id, db_session=db.session)


def _get_career_component_score(user_id: int) -> float:
    """Career slot: fresh employer health when CIK resolved, else satisfaction (no CIK), else neutral."""
    cp = CareerProfile.query.filter_by(user_id=user_id).first()
    if cp is None:
        return float(_NEUTRAL)

    cik = (cp.employer_cik or "").strip()
    edgar_attempted = bool(cik)
    if cik:
        snapshot = _employer_snapshot_for_cik(cik)
        if _employer_health_snapshot_fresh(snapshot):
            try:
                return max(0.0, min(100.0, float(snapshot.score)))
            except (TypeError, ValueError):
                logger.warning(
                    "life_ready invalid employer health score user_id=%s cik=%s",
                    user_id,
                    cik.zfill(10),
                )
        if edgar_attempted:
            return float(_NEUTRAL)

    if cp.satisfaction is not None:
        return _SATISFACTION_TO_CAREER_SCORE.get(int(cp.satisfaction), float(_NEUTRAL))

    return float(_NEUTRAL)


def _career_has_real_signal(user_id: int) -> bool:
    cp = CareerProfile.query.filter_by(user_id=user_id).first()
    if cp is None:
        return False
    cik = (cp.employer_cik or "").strip()
    if cik:
        snapshot = _employer_snapshot_for_cik(cik)
        return _employer_health_snapshot_fresh(snapshot)
    if cp.satisfaction is not None:
        return True
    return False


def _format_alert_date(filing_date: date) -> str:
    """Human-readable date without platform-specific strftime flags."""
    return f"{filing_date.strftime('%B')} {filing_date.day}, {filing_date.strftime('%Y')}"


def _layoff_source_label(event: LayoffEvent) -> str:
    source = getattr(event, "source", "8k_filing")
    if source == "8k_filing":
        return "8-K SEC filing"
    return "state WARN Act notice"


def _life_alerts_to_dicts(alerts: list[LifeAlert]) -> list[dict[str, str]]:
    return [
        {
            "domain": a.domain,
            "severity": a.severity,
            "headline": a.headline,
            "detail": a.detail,
            "action_label": a.action_label,
            "action_target": a.action_target,
        }
        for a in alerts
    ]


def _get_life_alerts(user_id: int) -> list[LifeAlert]:
    alerts: list[LifeAlert] = []
    cp = CareerProfile.query.filter_by(user_id=user_id).first()
    if cp is None:
        return alerts

    cik = (cp.employer_cik or "").strip()
    employer = (
        db.session.query(Employer).filter_by(cik=cik.zfill(10)).first()
        if cik
        else None
    )

    if employer is not None:
        cutoff_date = (
            datetime.now(timezone.utc) - timedelta(days=_LAYOFF_EVENT_WINDOW_DAYS)
        ).date()
        event = (
            db.session.query(LayoffEvent)
            .filter(
                LayoffEvent.employer_id == employer.id,
                LayoffEvent.filing_date >= cutoff_date,
                LayoffEvent.review_state != "needs_review",
            )
            .order_by(LayoffEvent.filing_date.desc())
            .first()
        )
        if event is not None:
            alerts.append(
                LifeAlert(
                    domain="career",
                    severity="high",
                    headline="Layoff risk detected",
                    detail=(
                        f"Your employer filed a workforce reduction "
                        f"{_layoff_source_label(event)} "
                        f"on {_format_alert_date(event.filing_date)}. "
                        "This does not affect your Life Score, but may affect "
                        "your financial plan."
                    ),
                    action_label="Review Career Risk",
                    action_target="career_risk",
                )
            )

    if cik and employer is not None and not any(a.severity == "high" for a in alerts):
        snap = (
            db.session.query(EmployerHealthSnapshot)
            .filter_by(employer_id=employer.id)
            .order_by(EmployerHealthSnapshot.fiscal_period_end.desc())
            .first()
        )
        if snap is not None and snap.score is not None and snap.refreshed_at is not None:
            refreshed = _snapshot_refreshed_at_utc(snap.refreshed_at)
            age = datetime.now(timezone.utc) - refreshed
            score_val = _coerce_float(snap.score)
            if (
                age <= timedelta(days=_EDGAR_STALE_DAYS)
                and score_val is not None
                and score_val < _EDGAR_STRESSED_THRESHOLD
            ):
                alerts.append(
                    LifeAlert(
                        domain="career",
                        severity="moderate",
                        headline="Employer financial stress",
                        detail=(
                            f"Your employer's financial health score is "
                            f"{int(round(score_val))}/100, which is in the stressed "
                            "range based on recent SEC filings."
                        ),
                        action_label="See Employer Health",
                        action_target="career_risk",
                    )
                )

    income_pct = getattr(cp, "income_percentile", None)
    if (
        income_pct is not None
        and income_pct < _INCOME_WATCH_PERCENTILE
        and not any(a.domain == "career" for a in alerts)
    ):
        alerts.append(
            LifeAlert(
                domain="career",
                severity="watch",
                headline="Income below peer average",
                detail=(
                    f"Your income is in the {int(income_pct)}th percentile "
                    "for your role and location. A salary review may improve "
                    "your financial position."
                ),
                action_label="See Income Benchmarks",
                action_target="career_risk",
            )
        )

    alerts.sort(key=lambda a: _ALERT_SEVERITY_ORDER.get(a.severity, 9))
    return alerts


def _with_life_alerts(payload: dict[str, Any], user_id: int | None) -> dict[str, Any]:
    alerts = _get_life_alerts(user_id) if user_id is not None else []
    payload["life_alerts"] = _life_alerts_to_dicts(alerts)
    return payload


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
    career: float,
    vibe: float,
    vehicle: float,
    body: float,
    wellness: float,
    stability: float,
) -> dict[str, Any]:
    """Response order matches product naming; all eight slots are active."""

    def _active_slot(key: str, score: float) -> dict[str, Any]:
        return {
            "score": int(round(score)),
            "weight": _NOMINAL_WEIGHTS[key],
            "active": True,
        }

    return {
        "financial": _active_slot("financial", financial),
        "roof": _active_slot("roof", roof),
        "career": _active_slot("career", career),
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
    user_id: int,
    *,
    financial: float,
    roof: float,
    career: float,
    vibe: float,
    vehicle: float,
    body: float,
    wellness: float,
    stability: float,
) -> int:
    """Weighted mean over active components; redistributes career weight when no real signal."""
    scores = {
        "financial": financial,
        "roof": roof,
        "career": career,
        "vibe": vibe,
        "vehicle": vehicle,
        "body": body,
        "wellness": wellness,
        "stability": stability,
    }
    weights = dict(_NOMINAL_WEIGHTS)
    if not _career_has_real_signal(user_id):
        career_w = weights.pop("career", 0.0)
        active = {k: v for k, v in weights.items() if k in scores}
        total_active = sum(active.values())
        if total_active > 0:
            for k in active:
                weights[k] += career_w * (active[k] / total_active)
    blended = sum(scores[k] * weights[k] for k in weights if k in scores)
    return _clamp_0_100(blended)


def _persist_snapshot_career_score(user_id: int, career: float) -> None:
    """Write career sub-score onto today's snapshot row when one already exists."""
    snap_date = datetime.now(timezone.utc).date()
    snap = LifeScoreSnapshot.query.filter_by(
        user_id=user_id, snapshot_date=snap_date
    ).first()
    if snap is None:
        return
    snap.career_score = career
    try:
        db.session.commit()
    except Exception as e:
        logger.warning(
            "life_ready career_score snapshot persist failed user_id=%s: %s",
            user_id,
            e,
        )
        db.session.rollback()


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
    stored_career = _coerce_float(getattr(snap, "career_score", None))
    career = float(stored_career) if stored_career is not None else float(_NEUTRAL)
    return _weighted_total(
        snap.user_id,
        financial=financial,
        roof=roof,
        career=career,
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
    career: float,
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
        "career": career,
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
    if hi == "career":
        return "Your career readiness is your strongest pillar right now."
    if hi == "stability":
        return "Having income and expenses mapped out is anchoring your readiness."
    return "You're balanced across all areas. Keep the momentum."


def compute_life_ready_score(user_id: str) -> dict[str, Any]:
    """
    Composite 0–100 score with breakdown, trend vs latest LifeScoreSnapshot, and headline.
    Missing inputs for *active* components use neutral 50. Career uses employer health,
    satisfaction map, or neutral 50.

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
        return _with_life_alerts(
            _insufficient_score_payload(
                _components_payload(
                    financial=n,
                    roof=n,
                    career=n,
                    vibe=n,
                    vehicle=n,
                    body=n,
                    wellness=n,
                    stability=n,
                ),
                0,
            ),
            None,
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
    career = _get_career_component_score(uid)

    components = _components_payload(
        financial=financial,
        roof=roof,
        career=career,
        vibe=vibe,
        vehicle=vehicle,
        body=body,
        wellness=wellness,
        stability=stability,
    )

    if pillars_complete < _MIN_PILLARS_FOR_SCORE:
        return _with_life_alerts(
            _insufficient_score_payload(components, pillars_complete),
            uid,
        )

    _persist_snapshot_career_score(uid, career)

    life_ready_score = _weighted_total(
        uid,
        financial=financial,
        roof=roof,
        career=career,
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
        career=career,
        vibe=vibe,
        vehicle=vehicle,
        body=body,
        wellness=wellness,
        stability=stability,
    )

    return _with_life_alerts(
        _sufficient_score_payload(
            life_ready_score, components, trend, headline, pillars_complete
        ),
        uid,
    )
