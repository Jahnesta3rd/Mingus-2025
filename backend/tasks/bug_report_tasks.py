#!/usr/bin/env python3
"""Celery tasks: bug report notification emails."""

from __future__ import annotations

import os

from celery.exceptions import Retry
from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

from backend.celery import celery
from backend.tasks.email_tasks import send_email


def _emails_template_dir() -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "templates", "emails")
    )


def _render_template(name: str, **kwargs) -> str:
    env = Environment(
        loader=FileSystemLoader(_emails_template_dir()),
        autoescape=select_autoescape(["html", "xml"]),
    )
    return env.get_template(name).render(**kwargs)


def _retry_countdown(task) -> int:
    return 60 * (2 ** task.request.retries)


@celery.task(name="send_bug_report_admin_email", bind=True, max_retries=3)
def send_bug_report_admin_email(self, report_id: int) -> dict | None:
    from app import app as flask_app
    from backend.models.bug_report import BugReport
    from backend.models.database import db

    try:
        with flask_app.app_context():
            report = db.session.get(BugReport, report_id)
            if not report:
                logger.error("send_bug_report_admin_email: missing BugReport id={}", report_id)
                return {"ok": False, "error": "not_found"}

            ticket_number = report.ticket_number
            user_name = report.user_name
            user_email_addr = report.user_email
            ctx = {
                "ticket_number": ticket_number,
                "user_name": user_name,
                "user_email": user_email_addr,
                "user_tier": report.user_tier,
                "account_age_days": report.account_age_days,
                "is_beta": report.is_beta,
                "current_route": report.current_route or "—",
                "browser_info": report.browser_info or "—",
                "balance_status": report.balance_status or "—",
                "last_feature": report.last_feature or "—",
                "description": report.description,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if report.created_at
                else "—",
            }
            html = _render_template("bug_report_admin.html", **ctx)

        to_addr = os.environ.get("BUG_REPORT_TO", "").strip()
        from_addr = os.environ.get("BUG_REPORT_FROM", "").strip()
        if not to_addr or not from_addr:
            logger.error(
                "send_bug_report_admin_email: BUG_REPORT_TO / BUG_REPORT_FROM not set"
            )
            return {"ok": False, "error": "missing_env"}

        subject = f"[{ticket_number}] Bug Report from {user_name}"
        try:
            ok = send_email(
                to=to_addr,
                subject=subject,
                html_body=html,
                mail_from=from_addr,
                reply_to=user_email_addr,
            )
        except Exception as exc:
            logger.exception(
                "send_bug_report_admin_email: send exception report_id={}", report_id
            )
            if self.request.retries >= self.max_retries:
                return {"ok": False, "error": str(exc)}
            raise self.retry(exc=exc, countdown=_retry_countdown(self))

        if ok:
            logger.info("send_bug_report_admin_email: sent report_id={}", report_id)
            return {"ok": True}

        logger.warning(
            "send_bug_report_admin_email: send returned false report_id={}", report_id
        )
        if self.request.retries >= self.max_retries:
            return {"ok": False, "error": "send_failed"}
        raise self.retry(
            exc=RuntimeError("send_email returned False"),
            countdown=_retry_countdown(self),
        )
    except Retry:
        raise
    except Exception:
        logger.exception("send_bug_report_admin_email: unexpected report_id={}", report_id)
        return {"ok": False, "error": "unexpected"}


@celery.task(name="send_bug_report_user_email", bind=True, max_retries=3)
def send_bug_report_user_email(self, report_id: int) -> dict | None:
    from app import app as flask_app
    from backend.models.bug_report import BugReport
    from backend.models.database import db

    try:
        with flask_app.app_context():
            report = db.session.get(BugReport, report_id)
            if not report:
                logger.error("send_bug_report_user_email: missing BugReport id={}", report_id)
                return {"ok": False, "error": "not_found"}

            ticket_number = report.ticket_number
            user_name = report.user_name
            user_email_addr = report.user_email
            description = report.description
            html = _render_template(
                "bug_report_user.html",
                ticket_number=ticket_number,
                user_name=user_name,
                description=description,
            )

        from_addr = os.environ.get("BUG_REPORT_FROM", "").strip()
        reply_admin = os.environ.get("BUG_REPORT_TO", "").strip()
        if not from_addr or not reply_admin:
            logger.error(
                "send_bug_report_user_email: BUG_REPORT_FROM / BUG_REPORT_TO not set"
            )
            return {"ok": False, "error": "missing_env"}

        subject = f"We got your report — {ticket_number}"
        try:
            ok = send_email(
                to=user_email_addr,
                subject=subject,
                html_body=html,
                mail_from=from_addr,
                reply_to=reply_admin,
            )
        except Exception as exc:
            logger.exception(
                "send_bug_report_user_email: send exception report_id={}", report_id
            )
            if self.request.retries >= self.max_retries:
                return {"ok": False, "error": str(exc)}
            raise self.retry(exc=exc, countdown=_retry_countdown(self))

        if ok:
            logger.info("send_bug_report_user_email: sent report_id={}", report_id)
            return {"ok": True}

        logger.warning(
            "send_bug_report_user_email: send returned false report_id={}", report_id
        )
        if self.request.retries >= self.max_retries:
            return {"ok": False, "error": "send_failed"}
        raise self.retry(
            exc=RuntimeError("send_email returned False"),
            countdown=_retry_countdown(self),
        )
    except Retry:
        raise
    except Exception:
        logger.exception("send_bug_report_user_email: unexpected report_id={}", report_id)
        return {"ok": False, "error": "unexpected"}
