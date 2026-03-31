#!/usr/bin/env python3
"""Celery tasks for transactional email (beta invites, etc.)."""

from __future__ import annotations

import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

from backend.celery import celery
from backend.services.email_service import EmailService

BETA_INVITE_SUBJECT = "You're invited to the Mingus Beta"


def _template_dir() -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "templates", "emails")
    )


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
