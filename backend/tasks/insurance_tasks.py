#!/usr/bin/env python3
"""Celery tasks for Health Insurance Advisor plan parsing."""

from __future__ import annotations

import os
import sys

from celery import Celery
from celery.utils.log import get_task_logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

celery_logger = get_task_logger(__name__)


def make_celery(app=None):
    """Create and configure Celery app for HIA tasks."""
    celery = Celery(
        app.import_name if app else "mingus_hia_tasks",
        broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/2"),
        backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        include=["backend.tasks.insurance_tasks"],
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
            "hia.*": {"queue": "hia_queue"},
        },
        task_default_queue="hia_queue",
    )
    return celery


celery_app = make_celery()


@celery_app.task(name="hia.parse_plan")
def parse_insurance_plan(plan_id: int):
    """Parse an uploaded insurance plan document (stub until HIA-03)."""
    celery_logger.info("[HIA] parse_insurance_plan called for plan_id=%s", plan_id)
    # HIA-03 will implement parse_insurance_document_with_llm here
    return {"plan_id": plan_id, "status": "stub"}
