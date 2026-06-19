#!/usr/bin/env python3
"""Celery tasks: sync Plaid transactions after bank connection."""

from __future__ import annotations

import logging

from loguru import logger

from backend.celery import celery
from backend.models.database import db
from backend.models.transaction import Transaction
from backend.models.user_models import User
from backend.services.plaid_service import plaid_service

_log = logging.getLogger(__name__)


def _upsert_transactions(user_id: int, access_token: str) -> int:
    if plaid_service is None:
        return 0

    rows = plaid_service.get_transactions(access_token, days_back=30)
    upserted = 0
    for row in rows:
        existing = Transaction.query.filter_by(
            plaid_transaction_id=row["plaid_transaction_id"]
        ).first()
        if existing is not None:
            existing.amount = row["amount"]
            existing.merchant = row.get("merchant")
            existing.category = row.get("category")
            existing.subcategory = row.get("subcategory")
            existing.date = row["date"]
            existing.is_debit = row["is_debit"]
            existing.account_id = row.get("account_id")
            existing.pending = row.get("pending", False)
        else:
            db.session.add(
                Transaction(
                    user_id=user_id,
                    plaid_transaction_id=row["plaid_transaction_id"],
                    amount=row["amount"],
                    merchant=row.get("merchant"),
                    category=row.get("category"),
                    subcategory=row.get("subcategory"),
                    date=row["date"],
                    is_debit=row["is_debit"],
                    account_id=row.get("account_id"),
                    pending=row.get("pending", False),
                )
            )
        upserted += 1
    db.session.commit()
    return upserted


def _sync_transactions_worker(user_id: int) -> None:
    user = User.query.get(user_id)
    if user is None or not user.plaid_access_token:
        return
    try:
        _upsert_transactions(user_id, user.plaid_access_token)
    except Exception:
        db.session.rollback()
        logger.exception("sync_user_transactions failed user_id=%s", user_id)
        raise


@celery.task(name="sync_user_transactions")
def sync_user_transactions(user_id: int) -> None:
    """Fetch last 30 days of Plaid transactions and upsert into Transaction table."""
    try:
        from backend.tasks.spirit_reminder import _minimal_task_app; flask_app = _minimal_task_app()

        with flask_app.app_context():
            try:
                _sync_transactions_worker(user_id)
            except Exception:
                db.session.rollback()
                raise
    except Exception:
        logger.exception("sync_user_transactions task failed user_id=%s", user_id)


def sync_user_transactions_background(user_id: int) -> None:
    """Enqueue Celery sync; falls back to daemon thread if broker unavailable."""
    try:
        sync_user_transactions.delay(user_id)
    except Exception:
        _log.warning("Celery unavailable for sync_user_transactions; using thread user_id=%s", user_id)
        import threading

        def _run() -> None:
            try:
                from app import app as flask_app

                with flask_app.app_context():
                    _sync_transactions_worker(user_id)
            except Exception:
                logger.exception("background thread sync failed user_id=%s", user_id)

        threading.Thread(target=_run, daemon=True).start()


@celery.task(
    name="recompute_daily_balance",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
)
def recompute_daily_balance(self, user_id: int, date_str: str):
    """
    Sums all quick_spend_entries for user on date_str.
    Looks up that date in daily_cashflow (if the table exists).
    Subtracts quick spend total from closing_balance for that day.
    Writes updated value back.

    If daily_cashflow table does not exist or has no row for
    this date: log info and return without error.
    This task is additive — it never blocks the save operation.
    """
    try:
        from backend.tasks.spirit_reminder import _minimal_task_app

        flask_app = _minimal_task_app()
        with flask_app.app_context():
            try:
                _recompute_daily_balance_impl(user_id, date_str)
            except Exception:
                db.session.rollback()
                raise
    except Exception as exc:
        logger.exception("recompute_daily_balance failed user_id=%s date=%s", user_id, date_str)
        raise self.retry(exc=exc)


def _recompute_daily_balance_impl(user_id: int, date_str: str) -> None:
    from datetime import date as date_type

    from flask import current_app
    from sqlalchemy import text
    from sqlalchemy.exc import OperationalError, ProgrammingError

    from backend.models.quick_spend import QuickSpendEntry

    target_date = date_type.fromisoformat(date_str)

    entries = QuickSpendEntry.query.filter(
        QuickSpendEntry.user_id == user_id,
        QuickSpendEntry.date == target_date,
    ).all()

    quick_spend_total = sum(float(e.amount) for e in entries)

    try:
        row = db.session.execute(
            text(
                """
                SELECT id, closing_balance
                FROM daily_cashflow
                WHERE user_id = :uid AND date = :dt
                LIMIT 1
                """
            ),
            {"uid": user_id, "dt": target_date},
        ).fetchone()
    except (OperationalError, ProgrammingError):
        db.session.rollback()
        current_app.logger.info(
            "recompute_daily_balance: daily_cashflow unavailable for "
            "user %s on %s — skipping",
            user_id,
            date_str,
        )
        return

    if row is None:
        current_app.logger.info(
            "recompute_daily_balance: no daily_cashflow row "
            "for user %s on %s — skipping",
            user_id,
            date_str,
        )
        return

    db.session.execute(
        text(
            """
            UPDATE daily_cashflow
            SET closing_balance = opening_balance - :spent
            WHERE id = :row_id
            """
        ),
        {"spent": quick_spend_total, "row_id": row.id},
    )
    db.session.commit()

    current_app.logger.info(
        "recompute_daily_balance: user %s date %s quick_spend_total=%s applied",
        user_id,
        date_str,
        quick_spend_total,
    )
