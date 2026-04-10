#!/usr/bin/env python3
"""Celery tasks for Spirit & Finance correlation refresh."""

from __future__ import annotations

from loguru import logger

from backend.celery import celery
from backend.services.spirit_correlation import SpiritCorrelationEngine


@celery.task(name="refresh_spirit_correlation")
def refresh_spirit_correlation(user_id: int) -> None:
    try:
        from app import app as flask_app

        with flask_app.app_context():
            engine = SpiritCorrelationEngine()
            engine.refresh_correlation(int(user_id))
    except Exception as e:
        logger.error(f"refresh_spirit_correlation failed for user {user_id}: {e}")
