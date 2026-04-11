#!/usr/bin/env python3
"""Celery application for Mingus background tasks.

Run worker (includes beta invite emails):
  celery -A backend.celery worker --loglevel=info
"""
import os

from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "mingus",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/2"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=[
        "backend.tasks.email_tasks",
        "backend.tasks.vibe_checkups_emails",
        "backend.tasks.life_correlation_tasks",
        "backend.tasks.spirit_tasks",
        "backend.tasks.spirit_reminder",
        "backend.tasks.vibe_financial_alert_tasks",
    ],
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

celery.conf.beat_schedule = {
    **(celery.conf.beat_schedule or {}),
    "spirit-practice-reminders": {
        "task": "backend.tasks.spirit_reminder.send_spirit_reminders",
        "schedule": crontab(minute="*/15"),
    },
}

# Alias for tooling that expects `app`
app = celery
