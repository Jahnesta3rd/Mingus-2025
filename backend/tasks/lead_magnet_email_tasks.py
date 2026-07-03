#!/usr/bin/env python3
"""Celery tasks: lead magnet assessment results emails."""

from __future__ import annotations

import hashlib
import json
import os

import psycopg2
import psycopg2.extras
from loguru import logger

from backend.celery import celery
from backend.services.assessment_analytics_service import log_assessment_event
from backend.services.email_service import EmailService

LEAD_MAGNET_REPLY_TO = "johnnie@mingusapp.com"


def _minimal_task_app():
    from pathlib import Path

    from dotenv import load_dotenv
    from flask import Flask

    from backend.models.database import init_database

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    backend_env = root / "backend" / ".env"
    if backend_env.is_file():
        load_dotenv(backend_env, override=True)

    import backend.models  # noqa: F401

    app = Flask(__name__)
    init_database(app)
    return app


def _get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn


def _is_duplicate_submission(email: str, assessment_type: str) -> bool:
    """True if the same email + assessment_type was submitted within the last 24 hours."""
    email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
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


def _log_email_sent(assessment_id: int | None, email: str, *, is_resend: bool = False) -> None:
    if not assessment_id:
        return
    app = _minimal_task_app()
    with app.app_context():
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()
        log_assessment_event(
            assessment_id,
            email_hash,
            "email_sent",
            metadata={"mailer": "resend" if is_resend else "initial", "status": "success"},
        )


@celery.task(name="send_lead_magnet_results", bind=True, max_retries=3)
def send_lead_magnet_results(
    self,
    email: str,
    first_name: str,
    assessment_type: str,
    results: dict,
    recommendations: list,
    assessment_id: int | None = None,
    token: str | None = None,
    is_resend: bool = False,
) -> dict:
    """Queue assessment results email with retries and exponential backoff."""
    if not is_resend and _is_duplicate_submission(email, assessment_type):
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
            assessment_id=assessment_id,
            token=token,
            is_resend=is_resend,
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
        _log_email_sent(assessment_id, email, is_resend=is_resend)
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


@celery.task(name="resend_lead_magnet_link", bind=True, max_retries=3)
def resend_lead_magnet_link(
    self,
    assessment_id: int,
    email: str,
    token: str,
) -> dict:
    """Resend results link email with a fresh token."""
    conn = _get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.first_name, a.assessment_type,
                       lr.score, lr.risk_level, lr.recommendations
                FROM assessments a
                LEFT JOIN lead_magnet_results lr ON a.id = lr.assessment_id
                WHERE a.id = %s
                """,
                (assessment_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return {"ok": False, "error": "not_found"}

    recs_raw = row.get("recommendations")
    if isinstance(recs_raw, str):
        try:
            recommendations = json.loads(recs_raw)
        except (TypeError, ValueError):
            recommendations = []
    elif isinstance(recs_raw, list):
        recommendations = recs_raw
    else:
        recommendations = []

    results = {
        "score": row.get("score", 0),
        "risk_level": row.get("risk_level", "Unknown"),
        "recommendations": recommendations,
    }

    try:
        ok = EmailService().send_assessment_results(
            email=email,
            first_name=row.get("first_name") or "there",
            assessment_type=row["assessment_type"],
            results=results,
            recommendations=recommendations,
            reply_to=LEAD_MAGNET_REPLY_TO,
            assessment_id=assessment_id,
            token=token,
            is_resend=True,
        )
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            return {"ok": False}
        raise self.retry(exc=exc, countdown=60) from exc

    if ok:
        _log_email_sent(assessment_id, email, is_resend=True)
        return {"ok": True}

    if self.request.retries >= self.max_retries:
        return {"ok": False}
    raise self.retry(exc=RuntimeError("send failed"), countdown=60)
