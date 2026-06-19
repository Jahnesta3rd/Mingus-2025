#!/usr/bin/env python3
"""Celery tasks: lead magnet assessment results emails."""

from __future__ import annotations

import hashlib
import os

import psycopg2
import psycopg2.extras
from loguru import logger

from backend.celery import celery
from backend.services.email_service import EmailService

LEAD_MAGNET_REPLY_TO = "johnnie@mingusapp.com"


def _get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def _is_duplicate_submission(email: str, assessment_type: str) -> bool:
    """True if the same email + assessment_type was submitted within the last 24 hours."""
    email_hash = hashlib.sha256(email.encode()).hexdigest()
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM assessments
                WHERE email = %s
                  AND assessment_type = %s
                  AND completed_at > NOW() - INTERVAL '24 hours'
                """,
                (email_hash, assessment_type),
            )
            row = cur.fetchone()
            return bool(row and row["cnt"] > 1)
    finally:
        conn.close()


@celery.task(name="send_lead_magnet_results", bind=True, max_retries=3)
def send_lead_magnet_results(
    self,
    email: str,
    first_name: str,
    assessment_type: str,
    results: dict,
    recommendations: list,
) -> dict:
    """Queue assessment results email with retries and exponential backoff."""
    if _is_duplicate_submission(email, assessment_type):
        logger.info(
            "Duplicate suppressed: {} assessment={}",
            email,
            assessment_type,
        )
        return {"ok": True, "suppressed": True}

    try:
        ok = EmailService().send_assessment_results(
            email=email,
            first_name=first_name,
            assessment_type=assessment_type,
            results=results,
            recommendations=recommendations,
            reply_to=LEAD_MAGNET_REPLY_TO,
        )
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            logger.error(
                "Lead magnet email failed after retries: {} assessment={}: {}",
                email,
                assessment_type,
                exc,
            )
            return {"ok": False}
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown) from exc

    if ok:
        logger.info("Lead magnet email sent: {} assessment={}", email, assessment_type)
        return {"ok": True}

    if self.request.retries >= self.max_retries:
        logger.error(
            "Lead magnet email failed after retries: {} assessment={}",
            email,
            assessment_type,
        )
        return {"ok": False}

    countdown = 60 * (2 ** self.request.retries)
    raise self.retry(
        exc=RuntimeError("send_assessment_results returned False"),
        countdown=countdown,
    )
