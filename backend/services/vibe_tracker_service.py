#!/usr/bin/env python3
"""Vibe Tracker: trend computation and tier limits for tracked people."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import case, func

from backend.models.database import db
from backend.models.vibe_checkups import VibeCheckupsLead
from backend.models.vibe_tracker import (
    VibePersonAssessment,
    VibePersonTrend,
    VibeTrackedPerson,
)


def _normalize_tier(tier: str | None) -> str:
    t = (tier or "budget").strip().lower()
    return t


def check_person_limit(user_id: int, tier: str | None) -> bool:
    """
    Budget: no tracking (False).
    Mid-tier: True if fewer than 3 active (non-archived) people.
    Professional: always True.
    """
    t = _normalize_tier(tier)
    if t == "budget":
        return False
    if t == "professional":
        return True
    if t == "mid_tier":
        n = (
            VibeTrackedPerson.query.filter_by(user_id=user_id, is_archived=False)
            .with_entities(func.count())
            .scalar()
        )
        return (n or 0) < 3
    return False


def serialize_lead_for_snapshot(lead: VibeCheckupsLead) -> dict[str, Any]:
    """Full lead row as JSON-serializable dict for answers_snapshot."""

    def conv(v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, uuid.UUID):
            return str(v)
        if isinstance(v, datetime):
            return v.isoformat() + "Z"
        if isinstance(v, (bytes, bytearray)):
            return v.decode("utf-8", errors="replace")
        return v

    return {c.name: conv(getattr(lead, c.name)) for c in lead.__table__.columns}


def assessment_from_lead(lead: VibeCheckupsLead) -> VibePersonAssessment:
    vl = (lead.verdict_label or "").strip()
    if not vl:
        vl = "Unknown"
    elif len(vl) > 100:
        vl = vl[:100]
    ve = (lead.verdict_emoji or "").strip()
    return VibePersonAssessment(
        lead_id=lead.id,
        emotional_score=lead.emotional_score,
        financial_score=lead.financial_score,
        verdict_label=vl,
        verdict_emoji=ve[:8] if ve else None,
        annual_projection=lead.total_annual_projection,
        answers_snapshot=serialize_lead_for_snapshot(lead),
        completed_at=lead.created_at,
    )


def compute_trend(person_id: uuid.UUID) -> VibePersonTrend:
    """
    Recompute and upsert VibePersonTrend for this tracked person.
    Assessments ordered by completed_at ASC; first = earliest, latest = most recent.
    """
    assessments = (
        VibePersonAssessment.query.filter_by(tracked_person_id=person_id)
        .order_by(VibePersonAssessment.completed_at.asc(), VibePersonAssessment.id.asc())
        .all()
    )
    n = len(assessments)
    now = datetime.utcnow()

    trend = VibePersonTrend.query.filter_by(tracked_person_id=person_id).first()
    if not trend:
        trend = VibePersonTrend(tracked_person_id=person_id)
        db.session.add(trend)

    if n < 2:
        trend.trend_direction = "insufficient_data"
        trend.emotional_delta = None
        trend.financial_delta = None
        trend.projection_delta = None
        trend.assessment_count = n
        trend.last_computed_at = now
        trend.stay_or_go_signal = "too_early"
        trend.stay_or_go_confidence = None
        return trend

    first = assessments[0]
    latest = assessments[-1]
    emotional_delta = latest.emotional_score - first.emotional_score
    financial_delta = latest.financial_score - first.financial_score
    projection_delta = latest.annual_projection - first.annual_projection
    combined_delta = (emotional_delta + financial_delta) / 2.0

    if combined_delta > 5:
        direction = "improving"
    elif combined_delta < -5:
        direction = "declining"
    else:
        direction = "stable"

    trend.trend_direction = direction
    trend.emotional_delta = emotional_delta
    trend.financial_delta = financial_delta
    trend.projection_delta = projection_delta
    trend.assessment_count = n
    trend.last_computed_at = now

    le = latest.emotional_score
    lf = latest.financial_score

    if le >= 70 and lf >= 70:
        trend.stay_or_go_signal = "stay"
        trend.stay_or_go_confidence = 0.85
    elif le < 40 or lf < 40:
        trend.stay_or_go_signal = "go"
        trend.stay_or_go_confidence = 0.80
    elif direction == "declining" and n >= 3:
        trend.stay_or_go_signal = "go"
        trend.stay_or_go_confidence = 0.65
    elif direction == "improving" and n >= 3:
        trend.stay_or_go_signal = "stay"
        trend.stay_or_go_confidence = 0.70
    else:
        trend.stay_or_go_signal = "neutral"
        trend.stay_or_go_confidence = 0.5

    return trend


def latest_assessment_for_person(person_id: uuid.UUID) -> VibePersonAssessment | None:
    return (
        VibePersonAssessment.query.filter_by(tracked_person_id=person_id)
        .order_by(
            VibePersonAssessment.completed_at.desc(),
            VibePersonAssessment.id.desc(),
        )
        .first()
    )


def list_people_order_clause():
    """Non-null last_assessed_at first (desc), then nulls last."""
    return (
        case((VibeTrackedPerson.last_assessed_at.is_(None), 1), else_=0),
        VibeTrackedPerson.last_assessed_at.desc(),
    )
