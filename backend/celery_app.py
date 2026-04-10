#!/usr/bin/env python3
"""Celery app entrypoint alias (some scripts expect ``backend.celery_app``)."""

from backend.celery import app, celery

__all__ = ["app", "celery"]
