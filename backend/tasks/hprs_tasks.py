#!/usr/bin/env python3
"""Celery tasks for HPRS latent candidate detection and plan generation."""

from __future__ import annotations

import os
import sys
from datetime import datetime

from celery import Celery
from celery.utils.log import get_task_logger
from sqlalchemy import and_, or_

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models.database import db
from backend.models.housing_profile import HousingProfile
from backend.models.hprs_latent_candidate import HprsLatentCandidate
from backend.models.user_models import User
from backend.services.hprs_service import (
    _build_latent_nudge,
    _deliver_nudge,
    evaluate_latent_candidate,
    generate_hprs_plan,
)

celery_logger = get_task_logger(__name__)


def make_celery(app=None):
    """Create and configure Celery app for HPRS tasks."""
    celery = Celery(
        app.import_name if app else "mingus_hprs_tasks",
        broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/2"),
        backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        include=["backend.tasks.hprs_tasks"],
    )
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        task_soft_time_limit=240,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_routes={
            "hprs.*": {"queue": "hprs_queue"},
        },
        task_default_queue="hprs_queue",
    )
    return celery


celery_app = make_celery()


def _eligible_latent_user_ids() -> list[int]:
    now = datetime.utcnow()
    rows = (
        db.session.query(User.id)
        .outerjoin(HousingProfile, User.id == HousingProfile.user_id)
        .outerjoin(HprsLatentCandidate, User.id == HprsLatentCandidate.user_id)
        .filter(
            or_(
                HousingProfile.user_id.is_(None),
                HousingProfile.has_buy_goal.is_(False),
            )
        )
        .filter(
            or_(
                HprsLatentCandidate.id.is_(None),
                and_(
                    HprsLatentCandidate.status.notin_(["activated", "opted_out"]),
                    or_(
                        HprsLatentCandidate.status != "snoozed",
                        HprsLatentCandidate.snoozed_until.is_(None),
                        HprsLatentCandidate.snoozed_until <= now,
                    ),
                ),
            )
        )
        .all()
    )
    return [row[0] for row in rows]


@celery_app.task(name="hprs.check_latent_candidates")
def check_latent_hprs_candidates():
    """Evaluate latent readiness thresholds for users without a buy goal."""
    from app import app as flask_app

    evaluated = 0
    nudges_queued = 0
    errors = 0

    with flask_app.app_context():
        user_ids = _eligible_latent_user_ids()
        celery_logger.info("check_latent_hprs_candidates: evaluating %s users", len(user_ids))

        for user_id in user_ids:
            try:
                result = evaluate_latent_candidate(user_id, db.session)
                evaluated += 1
                if not result.get("threshold_met"):
                    continue
                nudge_type = result.get("nudge_type")
                if not nudge_type:
                    continue
                generate_latent_nudge_task.delay(
                    user_id,
                    nudge_type,
                    result.get("threshold_data") or {},
                )
                nudges_queued += 1
            except Exception:
                errors += 1
                celery_logger.exception(
                    "check_latent_hprs_candidates failed for user_id=%s",
                    user_id,
                )

    summary = {
        "evaluated": evaluated,
        "nudges_queued": nudges_queued,
        "errors": errors,
    }
    celery_logger.info("check_latent_hprs_candidates complete: %s", summary)
    return summary


@celery_app.task(name="hprs.generate_latent_nudge")
def generate_latent_nudge_task(user_id: int, nudge_type: str, threshold_data: dict):
    """Build and deliver a latent HPRS nudge for one user."""
    from app import app as flask_app

    try:
        with flask_app.app_context():
            nudge_text = _build_latent_nudge(nudge_type, threshold_data or {})
            _deliver_nudge(user_id, nudge_type, nudge_text)
        return {"ok": True, "user_id": user_id, "nudge_type": nudge_type}
    except Exception as exc:
        celery_logger.exception(
            "generate_latent_nudge_task failed user_id=%s nudge_type=%s",
            user_id,
            nudge_type,
        )
        return {"ok": False, "user_id": user_id, "error": str(exc)}


@celery_app.task(name="hprs.generate_plan")
def generate_hprs_plan_task(user_id: int):
    """Generate and persist a full HPRS plan for one user."""
    from app import app as flask_app

    try:
        with flask_app.app_context():
            generate_hprs_plan(user_id)
        return {"ok": True, "user_id": user_id}
    except Exception as exc:
        celery_logger.exception("generate_hprs_plan_task failed user_id=%s", user_id)
        return {"ok": False, "user_id": user_id, "error": str(exc)}
