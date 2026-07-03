#!/usr/bin/env python3
"""Celery tasks for transactional email (beta invites, etc.)."""

from __future__ import annotations

import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

from backend.celery import celery
from backend.services.email_service import EmailService, send_email as service_send_email

BETA_INVITE_SUBJECT = "You're invited to the Mingus Beta"

LEAD_MAGNET_ASSESSMENT_LABELS = {
    "ai_risk": "AI Risk",
    "income_comparison": "Income Comparison",
    "layoff_risk": "Layoff Risk",
    "cuffing_season": "Cuffing Season",
    "ai-risk": "AI Replacement Risk",
    "income-comparison": "Income Comparison",
    "layoff-risk": "Layoff Risk",
    "cuffing-season": "Cuffing Season",
}


def _retry_countdown_seconds(retries: int) -> int:
    """Exponential backoff: 60s, 120s, 240s, …"""
    return (2 ** retries) * 60


def _assessment_label(assessment_type: str) -> str:
    return LEAD_MAGNET_ASSESSMENT_LABELS.get(
        assessment_type,
        assessment_type.replace("_", " ").replace("-", " ").title(),
    )


def _render_lead_magnet_results_html(
    assessment_type: str,
    results_data: dict,
) -> str:
    env = Environment(
        loader=FileSystemLoader(_template_dir()),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("lead_magnet_results.html")
    return tpl.render(
        assessment_type=assessment_type,
        assessment_label=_assessment_label(assessment_type),
        results_data=results_data or {},
    )


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
    mail_from: str | None = None,
    reply_to: str | None = None,
) -> bool:
    """Transactional send via :class:`EmailService` (used by Celery tasks)."""
    svc = EmailService()
    return svc.send_email(
        to=to,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        mail_from=mail_from,
        reply_to=reply_to,
    )


def _template_dir() -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "templates", "emails")
    )


def _task_flask_app():
    """Flask app for Celery task DB access; reuses the bound app when available."""
    from flask import Flask

    from backend.models.database import db

    if getattr(db, "app", None) is not None:
        return db.app

    app = Flask("email_tasks")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def _render_beta_invite_html(
    first_name: str,
    beta_code: str,
    beta_url: str,
    unsubscribe_url: str,
) -> str:
    env = Environment(
        loader=FileSystemLoader(_template_dir()),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("beta_invite.html")
    return tpl.render(
        first_name=first_name,
        beta_code=beta_code,
        beta_url=beta_url,
        unsubscribe_url=unsubscribe_url,
    )


def _mark_log_failed(flask_app, log_id: int) -> None:
    from backend.models.beta_invite_log import BetaInviteLog
    from backend.models.database import db

    with flask_app.app_context():
        row = db.session.get(BetaInviteLog, log_id)
        if row:
            row.status = "failed"
            db.session.commit()
            logger.error(
                "send_beta_invite_email: marked failed log_id={} email={}",
                log_id,
                row.email,
            )


@celery.task(name="send_beta_invite_email", bind=True, max_retries=3)
def send_beta_invite_email(self, log_id: int, beta_url: str) -> dict:
    """Send one beta invite email from a beta_invite_log row; retry with backoff on failure."""
    from datetime import datetime, timezone

    from app import app as flask_app
    from backend.models.beta_invite_log import BetaInviteLog
    from backend.models.database import db

    with flask_app.app_context():
        log = db.session.get(BetaInviteLog, log_id)
        if not log:
            logger.error("send_beta_invite_email: no beta_invite_log id={}", log_id)
            return {"ok": False, "error": "log_not_found"}

        to_email = (log.email or "").strip()
        code = (log.code or "").strip()
        fn = (log.first_name or "").strip() or (
            to_email.split("@")[0] if to_email else "there"
        )
        unsubscribe_url = os.environ.get(
            "BETA_INVITE_UNSUBSCRIBE_URL", "https://mingusapp.com/preferences/email"
        )
        html_body = _render_beta_invite_html(
            first_name=fn,
            beta_code=code,
            beta_url=beta_url,
            unsubscribe_url=unsubscribe_url,
        )

    email_svc = EmailService()
    try:
        ok = email_svc.send_email(
            to=to_email,
            subject=BETA_INVITE_SUBJECT,
            html_body=html_body,
        )
    except Exception as exc:
        logger.exception(
            "send_beta_invite_email: exception log_id={} email={}",
            log_id,
            to_email,
        )
        if self.request.retries >= self.max_retries:
            _mark_log_failed(flask_app, log_id)
            raise
        raise self.retry(exc=exc, countdown=(2 ** self.request.retries) * 60)

    if ok:
        with flask_app.app_context():
            row = db.session.get(BetaInviteLog, log_id)
            if row:
                row.status = "sent"
                row.sent_at = datetime.now(timezone.utc)
                db.session.commit()
        logger.info(
            "send_beta_invite_email: sent log_id={} email={}", log_id, to_email
        )
        return {"ok": True}

    logger.warning(
        "send_beta_invite_email: send returned false log_id={} email={}",
        log_id,
        to_email,
    )
    if self.request.retries >= self.max_retries:
        _mark_log_failed(flask_app, log_id)
        return {"ok": False, "error": "send_failed"}
    raise self.retry(
        exc=RuntimeError("send_email returned False"),
        countdown=(2 ** self.request.retries) * 60,
    )


@celery.task(name="send_lead_magnet_email", bind=True, max_retries=3)
def send_lead_magnet_email(
    self,
    log_id: int,
    recipient_email: str,
    assessment_type: str,
    results_data: dict,
) -> dict:
    """Send lead magnet results email; track status in lead_magnet_email_log."""
    from datetime import datetime, timezone

    from backend.models.database import db
    from backend.models.lead_magnet_email_log import LeadMagnetEmailLog

    flask_app = _task_flask_app()

    attempt = self.request.retries + 1
    logger.debug(
        "send_lead_magnet_email attempt={} log_id={} email={} assessment={}",
        attempt,
        log_id,
        recipient_email,
        assessment_type,
    )

    with flask_app.app_context():
        log = db.session.get(LeadMagnetEmailLog, log_id)
        if not log:
            logger.error("send_lead_magnet_email: no log id={}", log_id)
            return {"ok": False, "error": "log_not_found"}

    label = _assessment_label(assessment_type)
    subject = f"Your {label} Results"
    html_body = _render_lead_magnet_results_html(assessment_type, results_data)

    try:
        ok = service_send_email(
            to=recipient_email,
            subject=subject,
            html_body=html_body,
        )
        if not ok:
            raise RuntimeError("send_email returned False")
    except Exception as exc:
        logger.debug(
            "send_lead_magnet_email failed attempt={} log_id={}: {}",
            attempt,
            log_id,
            exc,
        )
        with flask_app.app_context():
            row = db.session.get(LeadMagnetEmailLog, log_id)
            if row:
                row.last_error = str(exc)
                if self.request.retries < self.max_retries:
                    row.retry_count = self.request.retries + 1
                db.session.commit()

        if self.request.retries >= self.max_retries:
            with flask_app.app_context():
                row = db.session.get(LeadMagnetEmailLog, log_id)
                if row:
                    row.status = "failed"
                    row.retry_count = self.max_retries
                    db.session.commit()
            logger.error(
                "send_lead_magnet_email: failed after retries log_id={} email={}",
                log_id,
                recipient_email,
            )
            return {"ok": False, "error": str(exc)}

        countdown = _retry_countdown_seconds(self.request.retries)
        logger.debug(
            "send_lead_magnet_email: retrying log_id={} in {}s (retry {})",
            log_id,
            countdown,
            self.request.retries + 1,
        )
        raise self.retry(exc=exc, countdown=countdown) from exc

    with flask_app.app_context():
        row = db.session.get(LeadMagnetEmailLog, log_id)
        if row:
            row.status = "sent"
            row.sent_at = datetime.now(timezone.utc)
            db.session.commit()

    logger.info(
        "send_lead_magnet_email: sent log_id={} email={} assessment={}",
        log_id,
        recipient_email,
        assessment_type,
    )
    return {"ok": True}
