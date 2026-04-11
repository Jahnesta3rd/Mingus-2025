#!/usr/bin/env python3
"""Celery: evaluate vibe/financial alerts after roster assessments."""

from __future__ import annotations

import uuid

from loguru import logger

from backend.celery import celery
from backend.models.database import db
from backend.services.vibe_financial_alert_service import check_for_alerts as run_alert_check


@celery.task(name="check_vibe_financial_alerts")
def check_for_alerts(user_id: int, person_id: str) -> None:
    """Run alert rules for one tracked person; persists UserAlert rows when triggered."""
    try:
        pid = uuid.UUID(str(person_id))
    except (ValueError, TypeError):
        logger.warning(
            "check_vibe_financial_alerts: invalid person_id={!r} user_id={}",
            person_id,
            user_id,
        )
        return

    try:
        from app import app as flask_app

        with flask_app.app_context():
            try:
                run_alert_check(user_id, pid)
            except Exception:
                db.session.rollback()
                raise
    except Exception:
        logger.exception(
            "check_vibe_financial_alerts failed user_id={} person_id={!r}",
            user_id,
            person_id,
        )
