#!/usr/bin/env python3
"""Celery tasks: persist daily life score snapshots for correlation tooling."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from loguru import logger
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.celery import celery
from backend.models.database import db
from backend.models.life_correlation import LifeScoreSnapshot
from backend.models.user_models import User
from backend.models.vibe_checkups import VibeCheckupsLead
from backend.models.vibe_tracker import VibePersonAssessment, VibeTrackedPerson
from backend.models.wellness import WeeklyCheckin
from backend.services import life_ledger_service as lls


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _relationship_monthly_from_lead(lead: VibeCheckupsLead | None) -> int | None:
    if lead is None:
        return None
    pd = lead.projection_data
    if isinstance(pd, list) and len(pd) > 0:
        first = pd[0]
        if isinstance(first, dict) and first.get("monthly_cost") is not None:
            try:
                return int(first["monthly_cost"])
            except (TypeError, ValueError):
                pass
    try:
        return int(round(lead.total_annual_projection / 12))
    except (TypeError, ValueError, ZeroDivisionError):
        return None


@celery.task(name="record_life_snapshot")
def record_life_snapshot(user_id: str, trigger: str) -> None:
    """Gather cross-domain signals and upsert one snapshot row for this user for today (UTC)."""
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        logger.error("record_life_snapshot: invalid user_id={!r}", user_id)
        return

    try:
        from app import app as flask_app

        with flask_app.app_context():
            try:
                _record_life_snapshot_impl(uid, trigger)
            except Exception:
                db.session.rollback()
                raise
    except Exception:
        logger.exception(
            "record_life_snapshot failed user_id={} trigger={!r}", uid, trigger
        )


def _record_life_snapshot_impl(uid: int, trigger: str) -> None:
    profile = lls.get_or_create_profile(uid)

    snap_date = _utc_today()

    checkins = (
        WeeklyCheckin.query.filter_by(user_id=uid)
        .order_by(WeeklyCheckin.week_ending_date.desc())
        .limit(4)
        .all()
    )
    moods = [c.overall_mood for c in checkins if c.overall_mood is not None]
    stresses = [c.stress_level for c in checkins if c.stress_level is not None]
    avg_wellness = sum(moods) / len(moods) if moods else None
    avg_stress = sum(stresses) / len(stresses) if stresses else None

    cutoff = datetime.utcnow() - timedelta(days=90)
    vibe_base = (
        db.session.query(
            func.max(VibePersonAssessment.emotional_score).label("max_e"),
            func.max(VibePersonAssessment.financial_score).label("max_f"),
            func.max(
                (
                    VibePersonAssessment.emotional_score
                    + VibePersonAssessment.financial_score
                )
                / 2.0
            ).label("max_c"),
        )
        .join(
            VibeTrackedPerson,
            VibeTrackedPerson.id == VibePersonAssessment.tracked_person_id,
        )
        .filter(
            VibeTrackedPerson.user_id == uid,
            VibePersonAssessment.completed_at >= cutoff,
        )
        .one()
    )
    max_e = vibe_base.max_e
    max_f = vibe_base.max_f
    max_c_raw = vibe_base.max_c
    best_combined = int(round(max_c_raw)) if max_c_raw is not None else None

    active_n = (
        VibeTrackedPerson.query.filter_by(user_id=uid, is_archived=False)
        .with_entities(func.count())
        .scalar()
    )
    active_n = int(active_n or 0)

    user = db.session.get(User, uid)
    lead = None
    if user and (user.email or "").strip():
        em = (user.email or "").strip().lower()
        lead = (
            VibeCheckupsLead.query.filter(func.lower(VibeCheckupsLead.email) == em)
            .order_by(VibeCheckupsLead.created_at.desc())
            .first()
        )
    rel_monthly = _relationship_monthly_from_lead(lead)

    monthly_savings_rate = None
    net_worth_estimate = None

    tbl = LifeScoreSnapshot.__table__
    values = {
        "id": uuid4(),
        "user_id": uid,
        "snapshot_date": snap_date,
        "trigger": trigger[:50] if trigger else "unknown",
        "body_score": profile.body_score,
        "roof_score": profile.roof_score,
        "vehicle_score": profile.vehicle_score,
        "life_ledger_score": profile.life_ledger_score,
        "best_vibe_emotional_score": max_e,
        "best_vibe_financial_score": max_f,
        "best_vibe_combined_score": best_combined,
        "active_tracked_people_count": active_n,
        "monthly_savings_rate": monthly_savings_rate,
        "net_worth_estimate": net_worth_estimate,
        "relationship_monthly_cost": rel_monthly,
        "avg_wellness_score": avg_wellness,
        "avg_stress_level": avg_stress,
        "created_at": datetime.utcnow(),
    }

    ins = pg_insert(tbl).values(**values)
    ins = ins.on_conflict_do_update(
        index_elements=[tbl.c.user_id, tbl.c.snapshot_date],
        set_={
            "trigger": ins.excluded.trigger,
            "body_score": ins.excluded.body_score,
            "roof_score": ins.excluded.roof_score,
            "vehicle_score": ins.excluded.vehicle_score,
            "life_ledger_score": ins.excluded.life_ledger_score,
            "best_vibe_emotional_score": ins.excluded.best_vibe_emotional_score,
            "best_vibe_financial_score": ins.excluded.best_vibe_financial_score,
            "best_vibe_combined_score": ins.excluded.best_vibe_combined_score,
            "active_tracked_people_count": ins.excluded.active_tracked_people_count,
            "monthly_savings_rate": ins.excluded.monthly_savings_rate,
            "net_worth_estimate": ins.excluded.net_worth_estimate,
            "relationship_monthly_cost": ins.excluded.relationship_monthly_cost,
            "avg_wellness_score": ins.excluded.avg_wellness_score,
            "avg_stress_level": ins.excluded.avg_stress_level,
        },
    )
    db.session.execute(ins)
    db.session.commit()

    try:
        import os

        import redis

        _r = redis.Redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            socket_timeout=2,
        )
        _r.delete(f"life_correlation:{uid}")
    except Exception:
        pass
