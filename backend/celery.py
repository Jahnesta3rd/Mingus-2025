#!/usr/bin/env python3
"""Celery application for Mingus background tasks.

Run worker (includes beta invite emails):
  celery -A backend.celery worker --loglevel=info
"""
import os

from celery import Celery

celery = Celery(
    "mingus",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/2"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=["backend.tasks.email_tasks"],
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
)

# Alias for tooling that expects `app`
app = celery
