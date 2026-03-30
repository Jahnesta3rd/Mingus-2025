#!/usr/bin/env python3
"""Celery tasks for async feature telemetry writes."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from celery import Celery

from backend.services.telemetry_service import TelemetryService


def make_celery(app=None):
    celery = Celery(
        app.import_name if app else "mingus_telemetry_tasks",
        broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/2"),
        backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
        include=["backend.tasks.telemetry_tasks"],
    )
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=120,
        task_soft_time_limit=90,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_routes={"log_telemetry_event": {"queue": "telemetry_queue"}},
        task_default_queue="telemetry_queue",
    )
    return celery


celery_app = make_celery()


@celery_app.task(name="log_telemetry_event")
def log_telemetry_event(user_id, event_type, feature_name, metadata, user_tier):
    TelemetryService.log_event(
        user_id, event_type, feature_name, metadata=metadata, user_tier=user_tier
    )
