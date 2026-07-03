#!/usr/bin/env python3
"""Helpers for logging assessment funnel events."""

from __future__ import annotations

import logging

from backend.models.assessment_event import AssessmentEvent
from backend.models.database import db

logger = logging.getLogger(__name__)


def log_assessment_event(
    assessment_id: int,
    email_hash: str,
    event_type: str,
    *,
    token: str | None = None,
    metadata: dict | None = None,
) -> AssessmentEvent | None:
    """Persist a funnel event; failures are logged and do not raise."""
    try:
        event = AssessmentEvent(
            assessment_id=assessment_id,
            email_hash=email_hash,
            event_type=event_type,
            token=token,
            metadata=metadata,
        )
        db.session.add(event)
        db.session.commit()
        return event
    except Exception as exc:
        db.session.rollback()
        logger.warning(
            "Failed to log assessment event %s for assessment %s: %s",
            event_type,
            assessment_id,
            exc,
        )
        return None
