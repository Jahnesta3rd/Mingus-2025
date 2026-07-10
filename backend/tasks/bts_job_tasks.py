#!/usr/bin/env python3
"""Celery tasks: BTS job earnings sync + Tier 2 reminder notifications."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from backend.celery import celery


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


@celery.task(name="bts.sync_job_earnings", bind=True, max_retries=1)
def sync_job_earnings(self):
    """
    Every 5 minutes: sync earnings from DF1 for all active BTS job commitments.
    """
    app = _minimal_task_app()
    with app.app_context():
        from backend.models.job_commitment import JobCommitment
        from backend.services.bts_job_integration_service import (
            bts_job_integration_service,
        )

        active = JobCommitment.query.filter_by(status="active").all()
        results = []
        for commitment in active:
            result = bts_job_integration_service.sync_earnings_from_df1(
                user_id=commitment.user_id,
                job_id=commitment.job_id,
            )
            results.append(
                {
                    "commitmentId": str(commitment.commitment_id),
                    "sessionId": str(commitment.session_id),
                    **result,
                }
            )

        logger.info(
            "BTS job earnings sync complete: {} active, results={}",
            len(active),
            results,
        )
        return {"synced": len(results), "results": results}


@celery.task(name="bts.send_tier2_reminders", bind=True, max_retries=3)
def send_tier2_reminders(self):
    """
    Daily at 9 AM UTC: mark sessions ready for Tier 2 reminder banner.

    Condition: tier1_purchased_at + 7 days <= now AND reminder not yet sent.
    """
    app = _minimal_task_app()
    with app.app_context():
        from backend.models.bts import BackToSchoolSession
        from backend.models.database import db

        try:
            cutoff = datetime.utcnow() - timedelta(days=7)
            sessions = BackToSchoolSession.query.filter(
                BackToSchoolSession.tier1_purchased_at.isnot(None),
                BackToSchoolSession.tier1_purchased_at <= cutoff,
                BackToSchoolSession.tier2_reminder_sent.is_(False),
            ).all()

            notified = 0
            emailed = 0
            errors = []

            for session in sessions:
                try:
                    session.tier2_reminder_sent = True
                    session.tier2_reminder_sent_at = datetime.utcnow()
                    db.session.commit()
                    notified += 1

                    try:
                        send_tier2_reminder_email.delay(
                            str(session.user_id), str(session.session_id)
                        )
                        emailed += 1
                    except Exception as mail_exc:
                        logger.warning(
                            "Could not queue Tier 2 reminder email for {}: {}",
                            session.session_id,
                            mail_exc,
                        )
                except Exception as exc:
                    db.session.rollback()
                    msg = f"{session.session_id}: {exc}"
                    errors.append(msg)
                    logger.error("Failed to mark Tier 2 reminder: {}", msg)

            logger.info(
                "Tier 2 reminders: notified={}, emailed_queued={}, errors={}",
                notified,
                emailed,
                len(errors),
            )
            return {
                "status": "success",
                "notified": notified,
                "emailedQueued": emailed,
                "errors": errors,
            }
        except Exception as exc:
            logger.exception("Tier 2 reminder task failed: {}", exc)
            raise self.retry(exc=exc, countdown=300)


@celery.task(name="bts.send_tier2_reminder_email", bind=True, max_retries=2)
def send_tier2_reminder_email(self, user_id: str, session_id: str):
    """Optional email notification when Tier 2 reminder is activated."""
    app = _minimal_task_app()
    with app.app_context():
        import uuid as uuid_mod

        from backend.models.bts import BackToSchoolSession
        from backend.models.job_commitment import JobCommitment
        from backend.models.user_models import User
        from backend.services.email_service import EmailService

        try:
            session_uuid = uuid_mod.UUID(str(session_id))
            session = BackToSchoolSession.query.filter_by(
                session_id=session_uuid
            ).first()
            user = User.query.filter_by(user_id=str(user_id)).first()
            if not session or not user or not user.email:
                return {"status": "skipped", "reason": "missing user or session"}

            commitment = JobCommitment.query.filter_by(
                session_id=session_uuid
            ).first()

            first_name = getattr(user, "first_name", None) or "there"
            earnings = float(commitment.actual_earnings) if commitment else 0.0
            job_title = commitment.job_title if commitment else None
            budget = (
                float(session.tier2_budget_with_earnings)
                if session.tier2_budget_with_earnings is not None
                else float(session.tier2_balance or 0)
            )
            plan_url = f"https://mingusapp.com/bts/{session_id}/plan"

            earnings_line = (
                f"<p>You've earned <strong>${earnings:.2f}</strong>"
                f"{f' from {job_title}' if job_title else ''}.</p>"
                if earnings > 0
                else ""
            )
            html = f"""
            <div style="font-family: Georgia, serif; max-width: 560px; margin: 0 auto;">
              <h1 style="color: #583fbc;">Tier 2 shopping is open</h1>
              <p>Hi {first_name},</p>
              <p>It's time for your Tier 2 back-to-school purchases.</p>
              {earnings_line}
              <p>Your available Tier 2 budget is about <strong>${budget:.2f}</strong>.</p>
              <p><a href="{plan_url}" style="color: #583fbc; font-weight: 600;">
                Open your shopping plan
              </a></p>
              <p style="color: #5c5c7a; font-size: 13px;">— Mingus</p>
            </div>
            """

            ok = EmailService().send_email(
                to=user.email,
                subject="Tier 2 shopping is ready",
                html_body=html,
            )
            return {
                "status": "sent" if ok else "failed",
                "userId": str(user_id),
                "sessionId": str(session_id),
            }
        except Exception as exc:
            logger.exception("Tier 2 reminder email failed: {}", exc)
            raise self.retry(exc=exc, countdown=120)
