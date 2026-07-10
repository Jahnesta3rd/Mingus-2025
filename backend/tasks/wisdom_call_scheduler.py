#!/usr/bin/env python3
"""Celery Beat: generate + deliver weekly wisdom calls every Monday 9 AM UTC."""

from __future__ import annotations

import asyncio
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from backend.celery import celery


_FAILURE_RATE_ALERT_THRESHOLD = 0.10
_ACTIVE_USER_DAYS = 30


def _minimal_task_app():
    """Lightweight Flask app + DB for workers (avoids root ``app.py`` imports)."""
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


def _target_week_number(today: date | None = None) -> int:
    """
    ISO week the Monday 9 AM job covers.

    On Monday morning the new ISO week has already started; wisdom calls are for
    the week that just ended (Sunday).
    """
    today = today or datetime.now(timezone.utc).date()
    prior = today - timedelta(days=1)
    return int(prior.isocalendar().week)


def _get_active_users():
    """Users active in the last 30 days with an email address."""
    from backend.models.user_models import User

    cutoff = datetime.utcnow() - timedelta(days=_ACTIVE_USER_DAYS)
    return (
        User.query.filter(
            User.last_activity >= cutoff,
            User.email.isnot(None),
            User.email != "",
        )
        .order_by(User.id.asc())
        .all()
    )


def _alert_high_failure_rate(results: dict[str, Any], failure_rate: float) -> None:
    """Log a critical alert (and email ops if configured) when failures exceed 10%."""
    message = (
        "Wisdom call weekly batch failure rate "
        f"{failure_rate:.1%} exceeds {_FAILURE_RATE_ALERT_THRESHOLD:.0%} threshold. "
        f"total={results.get('total')} generated={results.get('generated')} "
        f"delivered={results.get('delivered')} failed={results.get('failed')} "
        f"skipped={results.get('skipped')} week={results.get('week_number')}"
    )
    logger.critical(message)

    ops_email = (os.environ.get("WISDOM_CALL_ALERT_EMAIL") or os.environ.get("OPS_ALERT_EMAIL") or "").strip()
    if not ops_email:
        return

    try:
        from backend.services.email_service import EmailService

        EmailService().send_email(
            to=ops_email,
            subject="[Mingus] Wisdom call batch failure rate alert",
            html_body=f"<p>{message}</p>",
            text_body=message,
        )
    except Exception:
        logger.exception("Failed to send wisdom-call failure-rate alert email")


async def _process_user(
    svc,
    user_id: int,
    week_number: int,
) -> str:
    """
    Create then deliver one user's wisdom call.

    Returns one of: ``generated_delivered``, ``generated_failed``, ``failed``, ``skipped``.
    """
    from backend.models.checkin import WeeklyCheckin

    checkin = (
        WeeklyCheckin.query.filter_by(user_id=user_id, week_number=week_number).first()
    )
    if checkin is None:
        return "skipped"

    row = await svc.create_wisdom_call(user_id, week_number)
    if row is None or not (row.wisdom_call_script or "").strip():
        return "failed"

    delivery = await svc.deliver_wisdom_call(user_id, week_number)
    if isinstance(delivery, dict) and delivery.get("success"):
        return "generated_delivered"
    return "generated_failed"


def run_weekly_wisdom_batch(week_number: int | None = None) -> dict[str, Any]:
    """
    Generate and deliver wisdom calls for active users.

    Returns ``{"total", "generated", "delivered", "failed", ...}``.
    """
    from backend.services.wisdom_call_service import WisdomCallService

    week = week_number if week_number is not None else _target_week_number()
    svc = WisdomCallService()
    users = _get_active_users()

    results: dict[str, Any] = {
        "total": len(users),
        "generated": 0,
        "delivered": 0,
        "failed": 0,
        "skipped": 0,
        "week_number": week,
        "ran_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    logger.info(
        "wisdom_call batch start: users={} week_number={}",
        results["total"],
        week,
    )

    for user in users:
        try:
            outcome = asyncio.run(_process_user(svc, user.id, week))
        except Exception:
            logger.exception(
                "wisdom_call batch user failed user_id={} week_number={}",
                user.id,
                week,
            )
            results["failed"] += 1
            continue

        if outcome == "skipped":
            results["skipped"] += 1
        elif outcome == "generated_delivered":
            results["generated"] += 1
            results["delivered"] += 1
        elif outcome == "generated_failed":
            results["generated"] += 1
            results["failed"] += 1
        else:
            results["failed"] += 1

    attempted = results["total"] - results["skipped"]
    failure_rate = (results["failed"] / attempted) if attempted > 0 else 0.0
    results["failure_rate"] = round(failure_rate, 4)

    logger.info(
        "wisdom_call batch done: total={} generated={} delivered={} failed={} "
        "skipped={} failure_rate={:.1%} week={}",
        results["total"],
        results["generated"],
        results["delivered"],
        results["failed"],
        results["skipped"],
        failure_rate,
        week,
    )

    if attempted > 0 and failure_rate > _FAILURE_RATE_ALERT_THRESHOLD:
        _alert_high_failure_rate(results, failure_rate)

    try:
        from backend.api.wisdom_routes import store_wisdom_batch_result

        store_wisdom_batch_result(results)
    except Exception:
        logger.exception("wisdom_call batch: failed to persist last-run stats")

    return {
        "total": results["total"],
        "generated": results["generated"],
        "delivered": results["delivered"],
        "failed": results["failed"],
        "skipped": results["skipped"],
        "failure_rate": results["failure_rate"],
        "week_number": results["week_number"],
        "ran_at": results["ran_at"],
    }


@celery.task(
    name="backend.tasks.wisdom_call_scheduler.generate_and_send_weekly_wisdom",
    bind=True,
    ignore_result=False,
    soft_time_limit=3600,
    time_limit=3900,
)
def generate_and_send_weekly_wisdom(self, week_number: int | None = None) -> dict:
    """
    Monday 9 AM UTC: create + deliver wisdom calls for active users.

    Returns:
        ``{"total": N, "generated": X, "delivered": Y, "failed": Z}``
    """
    task_id = getattr(getattr(self, "request", None), "id", None)
    logger.info("generate_and_send_weekly_wisdom start task_id={}", task_id)

    flask_app = _minimal_task_app()
    with flask_app.app_context():
        results = run_weekly_wisdom_batch(week_number=week_number)

    # Public contract requested by the scheduler prompt.
    return {
        "total": results["total"],
        "generated": results["generated"],
        "delivered": results["delivered"],
        "failed": results["failed"],
    }


if __name__ == "__main__":
    _app = _minimal_task_app()
    with _app.app_context():
        print(run_weekly_wisdom_batch())
