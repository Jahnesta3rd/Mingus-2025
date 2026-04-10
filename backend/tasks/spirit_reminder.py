#!/usr/bin/env python3
"""Celery task: daily Spirit & Finance practice reminder emails + in-app notifications."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytz
from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

from backend.celery import celery
from backend.models.database import db
from backend.models.in_app_notification import InAppNotification
from backend.models.spirit_checkin import SpiritCheckin, SpiritCheckinStreak
from backend.models.spirit_prefs import SpiritNotificationPrefs
from backend.models.user_models import User
from backend.services.email_service import EmailService

_REMINDER_DAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

_PRACTICE_QUOTES = (
    "Small practices, repeated, change how you meet the day.",
    "Stillness before spending is its own kind of wealth.",
    "One honest check-in is enough to steer the whole afternoon.",
    "Your attention is the first account you balance.",
    "Show up for five minutes; the streak will carry the rest.",
)


def _template_dir() -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "templates", "email")
    )


def _render_spirit_reminder_html(ctx: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(_template_dir()),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("spirit_reminder.html")
    return tpl.render(**ctx)


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _local_date(utc_dt: datetime, tz_name: str) -> date:
    tz = pytz.timezone(tz_name)
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(tz).date()


def _minimal_task_app():
    """Lightweight Flask app + DB for workers and ``python -m`` (avoids root ``app.py`` imports)."""
    from pathlib import Path

    from dotenv import load_dotenv
    from flask import Flask

    from backend.models.database import init_database

    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")
    backend_env = root / "backend" / ".env"
    if backend_env.is_file():
        load_dotenv(backend_env, override=True)

    import backend.models  # noqa: F401 — register metadata

    app = Flask(__name__)
    init_database(app)
    return app


def _pick_quote(user_id: int, d: date) -> str:
    idx = (int(user_id) + d.year * 400 + d.month * 31 + d.day) % len(_PRACTICE_QUOTES)
    return _PRACTICE_QUOTES[idx]


def _should_send_now(pref: SpiritNotificationPrefs, now_utc: datetime) -> bool:
    tz = pytz.timezone(pref.reminder_timezone)
    local_now = now_utc.astimezone(tz)
    if local_now.hour != int(pref.reminder_hour):
        return False
    day_key = _REMINDER_DAY_KEYS[local_now.weekday()]
    allowed = {p.strip().lower() for p in (pref.reminder_days or "").split(",") if p.strip()}
    return day_key in allowed


def run_spirit_reminder_batch() -> tuple[int, int]:
    """Returns (sent_count, skipped_count)."""
    sent = 0
    skipped = 0
    now_utc = datetime.now(timezone.utc)
    prefs = SpiritNotificationPrefs.query.filter_by(reminders_enabled=True).all()

    public_base = os.environ.get("PUBLIC_APP_URL", "https://mingusapp.com").rstrip("/")
    checkin_url = f"{public_base}/dashboard/spirit"
    prefs_url = f"{public_base}/settings"

    for pref in prefs:
        try:
            if not _should_send_now(pref, now_utc):
                skipped += 1
                continue

            user = db.session.get(User, pref.user_id)
            if not user or not (user.email or "").strip():
                logger.warning("Spirit reminder skip: no user or email user_id={}", pref.user_id)
                skipped += 1
                continue

            utc_today = _utc_today()
            if SpiritCheckin.query.filter_by(
                user_id=user.id, checked_in_date=utc_today
            ).first():
                skipped += 1
                continue

            if pref.last_reminder_sent:
                lr = pref.last_reminder_sent
                if lr.tzinfo is None:
                    lr = lr.replace(tzinfo=timezone.utc)
                if _local_date(lr, pref.reminder_timezone) == _local_date(
                    now_utc, pref.reminder_timezone
                ):
                    skipped += 1
                    continue

            streak_row = SpiritCheckinStreak.query.filter_by(user_id=user.id).first()
            current_streak = int(streak_row.current_streak or 0) if streak_row else 0

            fn = (user.first_name or "").strip() or (
                user.email.split("@")[0] if user.email else "there"
            )
            practice_quote = _pick_quote(user.id, _local_date(now_utc, pref.reminder_timezone))
            streak_at_risk = bool(
                pref.streak_nudge_enabled
                and current_streak > 0
                and streak_row
                and streak_row.last_checkin_date == utc_today - timedelta(days=1)
            )

            html_body = _render_spirit_reminder_html(
                {
                    "user_name": fn,
                    "streak": current_streak,
                    "practice_quote": practice_quote,
                    "checkin_url": checkin_url,
                    "prefs_url": prefs_url,
                    "streak_at_risk": streak_at_risk,
                }
            )

            ok = EmailService().send_email(
                to=user.email.strip(),
                subject="Your Mingus practice reminder",
                html_body=html_body,
            )
            if not ok:
                logger.warning("Spirit reminder email not sent (service returned False) user_id={}", user.id)
                skipped += 1
                continue

            note = InAppNotification(
                user_id=user.id,
                title="Spirit practice reminder",
                body="Take a moment for today’s check-in on Spirit & Finance.",
                category="spirit_reminder",
            )
            db.session.add(note)
            pref.last_reminder_sent = datetime.utcnow()
            db.session.add(pref)
            db.session.commit()
            sent += 1
        except Exception as e:
            logger.exception("Spirit reminder failed for pref user_id={}: {}", pref.user_id, e)
            db.session.rollback()
            skipped += 1

    logger.info("Spirit reminders sent: {}, skipped: {}", sent, skipped)
    return sent, skipped


@celery.task(name="backend.tasks.spirit_reminder.send_spirit_reminders")
def send_spirit_reminders() -> None:
    flask_app = _minimal_task_app()
    with flask_app.app_context():
        run_spirit_reminder_batch()


if __name__ == "__main__":
    _app = _minimal_task_app()
    with _app.app_context():
        run_spirit_reminder_batch()
