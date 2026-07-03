#!/usr/bin/env python3
"""Celery tasks: assessment follow-up emails for non-converters."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from backend.celery import celery
from backend.models.assessment_event import AssessmentEvent
from backend.models.assessment_token import AssessmentToken
from backend.models.database import db
from backend.services.assessment_analytics_service import log_assessment_event
from backend.services.email_service import ASSESSMENT_LABELS, EmailService

LEAD_MAGNET_REPLY_TO = "johnnie@mingusapp.com"


def _minimal_task_app():
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


def _fetch_assessment_context(assessment_id: int) -> dict | None:
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id, a.email_plain, a.first_name, a.assessment_type,
                       lr.score, lr.risk_level
                FROM assessments a
                LEFT JOIN lead_magnet_results lr ON a.id = lr.assessment_id
                WHERE a.id = %s
                """,
                (assessment_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def _insight_for_score(assessment_type: str, score: int | None, risk_level: str | None) -> str:
    label = ASSESSMENT_LABELS.get(assessment_type, assessment_type)
    if score is not None and score >= 67:
        return f"Your {label} score suggests meaningful risk — and there are concrete steps you can take this week."
    if score is not None and score < 33:
        return f"Your {label} results look solid — the right next move is building on that momentum."
    level = risk_level or "your current level"
    return f"Your results put you at {level} — most people in your position benefit from a personalized action plan."


@celery.task(name="send_assessment_followup", bind=True, max_retries=2)
def send_assessment_followup_email(
    self,
    assessment_id: int,
    email: str,
    token: str,
) -> dict:
    """Day-3 follow-up for users who viewed results but have not signed up."""
    app = _minimal_task_app()
    with app.app_context():
        token_obj = AssessmentToken.query.filter_by(
            assessment_id=assessment_id, token=token
        ).first()
        if token_obj and token_obj.is_used:
            return {"ok": True, "skipped": "converted"}

        ctx = _fetch_assessment_context(assessment_id)
        if not ctx or not email:
            return {"ok": False, "error": "missing_context"}

        first_name = (ctx.get("first_name") or "there").strip() or "there"
        assessment_type = ctx.get("assessment_type") or "assessment"
        label = ASSESSMENT_LABELS.get(assessment_type, assessment_type)
        insight = _insight_for_score(
            assessment_type, ctx.get("score"), ctx.get("risk_level")
        )
        public_base = os.environ.get("PUBLIC_APP_URL", "https://mingusapp.com").rstrip("/")
        results_link = (
            f"{public_base}/api/assessments/{assessment_id}/track-click?token={token}"
        )

        html = f"""
<!DOCTYPE html>
<html><body style="font-family:sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:24px">
  <h2 style="color:#5B2D8E">Hey {first_name},</h2>
  <p>We noticed you checked out your {label} results a few days ago.</p>
  <p><strong>Here's the thing:</strong> {insight}</p>
  <p>The best part? Your personalized action plan is still waiting. Most people who see their results take action.</p>
  <p style="text-align:center;margin:30px 0">
    <a href="{results_link}"
       style="background:#5B2D8E;color:#fff;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold">
      View Your Results Again
    </a>
  </p>
  <p>Or, if you're ready to go deeper:</p>
  <p><a href="{public_base}/register?from=assessment&assessment_id={assessment_id}&token={token}">
    Create your free account</a> to unlock your personalized action plan.</p>
  <p>Questions? Reply to this email — we're here to help.</p>
  <p>— Mingus Team</p>
</body></html>"""

        ok = EmailService().send_email(
            to=email,
            subject="Your assessment results are waiting — and you're not alone",
            html_body=html,
            reply_to=LEAD_MAGNET_REPLY_TO,
        )
        if not ok and self.request.retries < self.max_retries:
            raise self.retry(countdown=120)

        if ok:
            log_assessment_event(
                assessment_id,
                hashlib.sha256(email.lower().encode()).hexdigest(),
                "followup_day3_sent",
                token=token,
            )
        return {"ok": ok}


@celery.task(name="send_assessment_final_followup", bind=True, max_retries=2)
def send_assessment_final_followup_email(
    self,
    assessment_id: int,
    email: str,
    token: str,
) -> dict:
    """Day-7 final follow-up with urgency and discount code."""
    app = _minimal_task_app()
    with app.app_context():
        token_obj = AssessmentToken.query.filter_by(
            assessment_id=assessment_id, token=token
        ).first()
        if token_obj and token_obj.is_used:
            return {"ok": True, "skipped": "converted"}

        ctx = _fetch_assessment_context(assessment_id)
        if not ctx or not email:
            return {"ok": False, "error": "missing_context"}

        assessment_type = ctx.get("assessment_type") or "assessment"
        label = ASSESSMENT_LABELS.get(assessment_type, assessment_type)
        expiry = (
            token_obj.expires_at.strftime("%B %d, %Y")
            if token_obj and token_obj.expires_at
            else "soon"
        )
        public_base = os.environ.get("PUBLIC_APP_URL", "https://mingusapp.com").rstrip("/")
        results_link = (
            f"{public_base}/api/assessments/{assessment_id}/track-click?token={token}"
        )

        html = f"""
<!DOCTYPE html>
<html><body style="font-family:sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:24px">
  <h2 style="color:#5B2D8E">Last chance: Your results expire soon</h2>
  <p>You reviewed your {label} results last week. They're still valid until <strong>{expiry}</strong>.</p>
  <p>Here's what people typically do next:</p>
  <ul>
    <li>Create an account to save results and get ongoing guidance</li>
    <li>Build a personalized action plan based on their score</li>
    <li>Track progress over time</li>
  </ul>
  <div style="text-align:center;margin:30px 0;padding:20px;background:#FFF3CD;border-radius:6px">
    <p style="margin:0 0 10px"><strong>Special offer for you:</strong></p>
    <p style="margin:0;font-size:18px;color:#5B2D8E">30% off your first month</p>
    <p style="margin:10px 0 0;font-size:12px;color:#666">Use code: ASSESSMENT30</p>
  </div>
  <p style="text-align:center">
    <a href="{public_base}/register?from=assessment&promo=ASSESSMENT30&assessment_id={assessment_id}&token={token}"
       style="display:inline-block;background:#5B2D8E;color:#fff;padding:12px 24px;text-decoration:none;border-radius:6px;font-weight:bold">
      Claim Your Discount
    </a>
  </p>
  <p style="margin-top:20px;font-size:12px;color:#666;text-align:center">
    <a href="{results_link}">
      View results without signing up
    </a>
  </p>
</body></html>"""

        ok = EmailService().send_email(
            to=email,
            subject=f"Last chance: Your {label} results expire soon",
            html_body=html,
            reply_to=LEAD_MAGNET_REPLY_TO,
        )
        if not ok and self.request.retries < self.max_retries:
            raise self.retry(countdown=120)

        if ok:
            log_assessment_event(
                assessment_id,
                hashlib.sha256(email.lower().encode()).hexdigest(),
                "followup_day7_sent",
                token=token,
            )
        return {"ok": ok}


@celery.task(name="scan_assessment_followups")
def scan_assessment_followups() -> dict:
    """Hourly scan: queue day-3 and day-7 follow-ups for non-converters."""
    app = _minimal_task_app()
    queued = {"day3": 0, "day7": 0}

    with app.app_context():
        now = datetime.utcnow()

        for days, event_sent, task_fn in (
            (3, "followup_day3_sent", send_assessment_followup_email),
            (7, "followup_day7_sent", send_assessment_final_followup_email),
        ):
            window_start = now - timedelta(days=days, hours=1)
            window_end = now - timedelta(days=days)

            candidates = (
                AssessmentEvent.query.filter(
                    AssessmentEvent.event_type == "results_viewed",
                    AssessmentEvent.created_at <= window_end,
                    AssessmentEvent.created_at > window_start,
                )
                .all()
            )

            for event in candidates:
                already = AssessmentEvent.query.filter_by(
                    assessment_id=event.assessment_id,
                    email_hash=event.email_hash,
                    event_type=event_sent,
                ).first()
                if already:
                    continue

                token_obj = AssessmentToken.query.filter_by(
                    assessment_id=event.assessment_id,
                    token=event.token,
                ).first()
                if not token_obj:
                    token_obj = (
                        AssessmentToken.query.filter_by(
                            assessment_id=event.assessment_id
                        )
                        .order_by(AssessmentToken.created_at.desc())
                        .first()
                    )
                if not token_obj or token_obj.is_used:
                    continue

                ctx = _fetch_assessment_context(event.assessment_id)
                email = (ctx or {}).get("email_plain")
                if not email:
                    log = (
                        AssessmentEvent.query.filter_by(
                            assessment_id=event.assessment_id,
                            event_type="submitted",
                        )
                        .order_by(AssessmentEvent.created_at.desc())
                        .first()
                    )
                    email = (log.event_metadata or {}).get("email") if log else None
                if not email:
                    logger.info(
                        "Skipping follow-up — no email for assessment {}",
                        event.assessment_id,
                    )
                    continue

                task_fn.delay(event.assessment_id, email, token_obj.token)
                queued["day3" if days == 3 else "day7"] += 1

    logger.info("Assessment follow-up scan queued: {}", queued)
    return queued
