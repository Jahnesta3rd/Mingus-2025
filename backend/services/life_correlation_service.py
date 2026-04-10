#!/usr/bin/env python3
"""Life Correlation Engine: pattern detection over LifeScoreSnapshot time series (observational, not statistical)."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from typing import Any

import redis
from loguru import logger

from backend.models.life_correlation import LifeScoreSnapshot

_redis = redis.Redis.from_url(
    os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
    socket_timeout=3,
)

_CACHE_TTL = 21600
_CACHE_KEY_PREFIX = "life_correlation:"


def _cache_key(user_id: int) -> str:
    return f"{_CACHE_KEY_PREFIX}{user_id}"


def get_snapshots(user_id: int, days: int = 180) -> list[LifeScoreSnapshot]:
    """Return snapshots for user within the window, oldest first."""
    cutoff = date.today() - timedelta(days=days)
    return (
        LifeScoreSnapshot.query.filter(
            LifeScoreSnapshot.user_id == user_id,
            LifeScoreSnapshot.snapshot_date >= cutoff,
        )
        .order_by(LifeScoreSnapshot.snapshot_date.asc())
        .all()
    )


def _num_delta(first: int | float | None, last: int | float | None) -> float | None:
    if first is None or last is None:
        return None
    try:
        return float(last) - float(first)
    except (TypeError, ValueError):
        return None


def _annual_relationship_cost(snap: LifeScoreSnapshot) -> float | None:
    m = snap.relationship_monthly_cost
    if m is None:
        return None
    try:
        return float(m) * 12.0
    except (TypeError, ValueError):
        return None


def compute_score_deltas(snapshots: list[LifeScoreSnapshot]) -> dict[str, float | None]:
    """Change from first to latest snapshot per metric. Positive = improvement, except relationship_cost_delta = annual $ increase."""
    if not snapshots:
        return {
            "body_delta": None,
            "roof_delta": None,
            "vehicle_delta": None,
            "vibe_emotional_delta": None,
            "vibe_financial_delta": None,
            "savings_rate_delta": None,
            "wellness_delta": None,
            "relationship_cost_delta": None,
        }

    first, last = snapshots[0], snapshots[-1]
    a0, a1 = _annual_relationship_cost(first), _annual_relationship_cost(last)
    rel_delta = None if a0 is None or a1 is None else a1 - a0

    return {
        "body_delta": _num_delta(first.body_score, last.body_score),
        "roof_delta": _num_delta(first.roof_score, last.roof_score),
        "vehicle_delta": _num_delta(first.vehicle_score, last.vehicle_score),
        "vibe_emotional_delta": _num_delta(
            first.best_vibe_emotional_score, last.best_vibe_emotional_score
        ),
        "vibe_financial_delta": _num_delta(
            first.best_vibe_financial_score, last.best_vibe_financial_score
        ),
        "savings_rate_delta": _num_delta(
            first.monthly_savings_rate, last.monthly_savings_rate
        ),
        "wellness_delta": _num_delta(first.avg_wellness_score, last.avg_wellness_score),
        "relationship_cost_delta": rel_delta,
    }


def _months_span(snapshots: list[LifeScoreSnapshot]) -> int:
    if len(snapshots) < 2:
        return 0
    d0, d1 = snapshots[0].snapshot_date, snapshots[-1].snapshot_date
    return max(1, int(round((d1 - d0).days / 30.0)))


def _strength_from_delta(abs_delta: float) -> str:
    if abs_delta > 15:
        return "strong"
    if abs_delta >= 8:
        return "moderate"
    if abs_delta >= 3:
        return "mild"
    return "mild"


def detect_correlations(snapshots: list[LifeScoreSnapshot]) -> list[dict[str, Any]]:
    """Observational patterns only — not claims of statistical significance."""
    correlations: list[dict[str, Any]] = []
    if len(snapshots) < 3:
        return correlations

    deltas = compute_score_deltas(snapshots)
    n_months = _months_span(snapshots)

    def add(
        type_: str,
        primary_delta: float | None,
        description: str,
        insight_message: str,
    ) -> None:
        if primary_delta is None:
            mag = 0.0
        else:
            mag = abs(float(primary_delta))
        correlations.append(
            {
                "type": type_,
                "strength": _strength_from_delta(mag),
                "description": description,
                "insight_message": insight_message,
            }
        )

    bd = deltas.get("body_delta")
    ved = deltas.get("vibe_emotional_delta")
    srd = deltas.get("savings_rate_delta")
    vfd = deltas.get("vibe_financial_delta")
    rcd = deltas.get("relationship_cost_delta")
    wd = deltas.get("wellness_delta")
    first, last = snapshots[0], snapshots[-1]
    lld = _num_delta(first.life_ledger_score, last.life_ledger_score)
    vcd = _num_delta(first.best_vibe_combined_score, last.best_vibe_combined_score)

    if bd is not None and ved is not None and bd > 8 and ved > 5:
        add(
            "FITNESS_VIBE_POSITIVE",
            max(bd, ved),
            "Body score and emotional compatibility scores both moved up over this period.",
            f"As your body score improved by {bd:.0f} points over the last {n_months} months, "
            f"the emotional compatibility in your checkups also rose by {ved:.0f} points. "
            "You may be showing up differently — or attracting differently.",
        )

    if bd is not None and ved is not None and bd < -5 and ved < 0:
        add(
            "FITNESS_VIBE_OPPORTUNITY",
            max(abs(bd), abs(ved)),
            "Body and emotional vibe scores have both declined recently.",
            "Your body score and vibe scores have both dipped recently. "
            "Physical wellbeing and relationship energy tend to move together. "
            "Small wins in the gym often show up in how you carry yourself.",
        )

    if srd is not None and vfd is not None and srd > 0.05 and vfd > 8:
        add(
            "FINANCIAL_VIBE_POSITIVE",
            max(srd * 100, vfd),
            "Savings rate and financial compatibility scores increased together.",
            "Your savings rate has improved and your financial compatibility scores in recent checkups are higher. "
            "You may be gravitating toward people who share your financial values as your own clarity grows.",
        )

    if rcd is not None and rcd > 3000:
        add(
            "FINANCIAL_VIBE_OPPORTUNITY",
            rcd,
            "Estimated annual relationship costs are higher than at the start of this window.",
            f"Your estimated relationship costs have increased by ${rcd:,.0f}/year "
            "across your recent checkups. This may reflect choices worth examining — "
            "or simply that you're dating at a higher lifestyle level.",
        )

    if wd is not None and ved is not None and wd > 8 and ved > 8:
        add(
            "WELLNESS_VIBE_POSITIVE",
            max(wd, ved),
            "Wellness and emotional compatibility scores improved in parallel.",
            "Your wellness scores and emotional compatibility ratings have both improved over this period. "
            "Emotional availability tends to follow physical and mental wellbeing.",
        )

    if lld is not None and vcd is not None and lld > 10 and vcd > 8:
        add(
            "OVERALL_UPWARD",
            max(lld, vcd),
            "Life ledger and combined vibe scores suggest broad upward movement.",
            f"Across the board, you're in a stronger position than you were {n_months} months ago — "
            "physically, financially, and in your checkup scores. "
            "This is what growth looks like in the data.",
        )

    if srd is not None and rcd is not None and srd < -0.05 and rcd > 2000:
        add(
            "FINANCIAL_SAVINGS_RELATIONSHIP_DRAG",
            max(abs(srd) * 100, rcd),
            "Savings rate fell while relationship costs rose in the snapshot window.",
            "Your savings rate has dropped while relationship costs increased. "
            "The Vibe Checkups financial projection exists for exactly this moment. "
            "It may be worth a fresh look at the numbers.",
        )

    return correlations


def _default_headline() -> str:
    return "Keep tracking — patterns emerge with time."


def _build_summary_payload(user_id: int) -> dict[str, Any]:
    snapshots = get_snapshots(user_id, days=180)
    count = len(snapshots)
    if count >= 2:
        dr = (snapshots[-1].snapshot_date - snapshots[0].snapshot_date).days
    else:
        dr = 0

    deltas = compute_score_deltas(snapshots)
    has_sufficient = count >= 3
    correlations = detect_correlations(snapshots) if has_sufficient else []

    if correlations:
        headline = correlations[0]["insight_message"]
    elif has_sufficient:
        headline = (
            "We looked across your snapshots; no strong preset patterns jumped out this time. "
            "Keep logging — new stretches of data often tell a clearer story."
        )
    else:
        headline = _default_headline()

    return {
        "snapshots_count": count,
        "date_range_days": dr,
        "deltas": deltas,
        "correlations": correlations,
        "has_sufficient_data": has_sufficient,
        "headline_insight": headline,
    }


def generate_correlation_summary(user_id: int) -> dict[str, Any]:
    """Full summary for a user; cached 6h in Redis (best-effort)."""
    key = _cache_key(user_id)
    try:
        raw = _redis.get(key)
        if raw is not None:
            return json.loads(raw)
    except Exception as e:
        logger.warning("life_correlation cache read failed: {}", e)

    result = _build_summary_payload(user_id)

    try:
        _redis.setex(key, _CACHE_TTL, json.dumps(result))
    except Exception as e:
        logger.warning("life_correlation cache write failed: {}", e)

    return result


def snapshot_to_dict(s: LifeScoreSnapshot) -> dict[str, Any]:
    """JSON-serializable row for API responses."""
    return {
        "id": str(s.id),
        "user_id": s.user_id,
        "snapshot_date": s.snapshot_date.isoformat()
        if s.snapshot_date
        else None,
        "trigger": s.trigger,
        "body_score": s.body_score,
        "roof_score": s.roof_score,
        "vehicle_score": s.vehicle_score,
        "life_ledger_score": s.life_ledger_score,
        "best_vibe_emotional_score": s.best_vibe_emotional_score,
        "best_vibe_financial_score": s.best_vibe_financial_score,
        "best_vibe_combined_score": s.best_vibe_combined_score,
        "active_tracked_people_count": s.active_tracked_people_count,
        "monthly_savings_rate": s.monthly_savings_rate,
        "net_worth_estimate": s.net_worth_estimate,
        "relationship_monthly_cost": s.relationship_monthly_cost,
        "avg_wellness_score": s.avg_wellness_score,
        "avg_stress_level": s.avg_stress_level,
        "created_at": s.created_at.isoformat() + "Z" if s.created_at else None,
    }
