#!/usr/bin/env python3
"""Quick Spend Logger API — POST/GET quick-log endpoints."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func

from backend.auth.decorators import get_current_jwt_user, require_auth
from backend.models.database import db
from backend.models.quick_spend import QuickSpendEntry

logger = logging.getLogger(__name__)

quick_spend_bp = Blueprint(
    "quick_spend",
    __name__,
    url_prefix="/api/expenses",
)

MAX_SINGLE_ENTRY = 10000.0


def _money(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return round(float(value), 2)
    return round(float(value), 2)


def _parse_amount(raw) -> float | None:
    if raw is None:
        return None
    try:
        amount = float(raw)
    except (TypeError, ValueError):
        return None
    if amount <= 0:
        return None
    return amount


def _non_empty_str(raw) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def _serialize_entry(entry: QuickSpendEntry) -> dict:
    return {
        "id": entry.id,
        "amount": _money(entry.amount),
        "spend_vibe": entry.spend_vibe,
        "vibe_signal": entry.vibe_signal,
        "merchant_name": entry.merchant_name,
        "merchant_group": entry.merchant_group,
        "merchant_id": entry.merchant_id,
        "logged_at": entry.logged_at.isoformat() if entry.logged_at else None,
    }


def _current_user_or_401():
    user = get_current_jwt_user()
    if not user:
        return None, (jsonify({"error": "Authentication required"}), 401)
    return user, None


@quick_spend_bp.route("/quick-log", methods=["POST"])
@require_auth
def post_quick_log():
    """POST /api/expenses/quick-log — create a quick spend entry."""
    user, err = _current_user_or_401()
    if err:
        return err

    data = request.get_json(silent=True) or {}

    amount = _parse_amount(data.get("amount"))
    if amount is None:
        return jsonify({"error": "amount must be greater than 0"}), 400
    if amount > MAX_SINGLE_ENTRY:
        return jsonify({"error": "amount exceeds maximum single entry"}), 400

    spend_vibe = _non_empty_str(data.get("spend_vibe"))
    if not spend_vibe:
        return jsonify({"error": "spend_vibe is required"}), 400

    vibe_signal = _non_empty_str(data.get("vibe_signal"))
    if not vibe_signal:
        return jsonify({"error": "vibe_signal is required"}), 400

    entry_date = date.today()
    raw_date = data.get("date")
    if raw_date is not None:
        try:
            entry_date = date.fromisoformat(str(raw_date).strip())
        except ValueError:
            return jsonify({"error": "date must be ISO YYYY-MM-DD"}), 400

    try:
        entry = QuickSpendEntry(
            user_id=int(user.id),
            date=entry_date,
            amount=Decimal(str(round(amount, 2))),
            spend_vibe=spend_vibe,
            vibe_signal=vibe_signal,
            merchant_id=_non_empty_str(data.get("merchant_id")),
            merchant_name=_non_empty_str(data.get("merchant_name")),
            merchant_group=_non_empty_str(data.get("merchant_group")),
            logged_at=datetime.utcnow(),
        )
        db.session.add(entry)
        db.session.commit()

        try:
            from backend.services.life_correlation_service import (
                _cache_key,
                _redis,
            )

            _redis.delete(_cache_key(int(user.id)))
        except Exception as e:
            current_app.logger.warning(
                f"quick_spend: cache invalidation failed: {e}"
            )

        try:
            from backend.tasks.plaid_tasks import recompute_daily_balance

            recompute_daily_balance.delay(int(user.id), str(entry.date))
        except Exception as exc:
            logger.warning(
                "recompute_daily_balance dispatch failed user_id=%s: %s",
                user.id,
                exc,
            )

        return (
            jsonify(
                {
                    "id": entry.id,
                    "date": str(entry.date),
                    "amount": _money(entry.amount),
                    "spend_vibe": entry.spend_vibe,
                    "vibe_signal": entry.vibe_signal,
                    "merchant_name": entry.merchant_name,
                    "merchant_group": entry.merchant_group,
                    "logged_at": entry.logged_at.isoformat(),
                }
            ),
            201,
        )
    except Exception:
        logger.exception("post_quick_log failed user_id=%s", user.id)
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500


@quick_spend_bp.route("/quick-log/today", methods=["GET"])
@require_auth
def get_quick_log_today():
    """GET /api/expenses/quick-log/today — entries for the current UTC date."""
    user, err = _current_user_or_401()
    if err:
        return err

    today = date.today()
    try:
        entries = (
            QuickSpendEntry.query.filter_by(user_id=int(user.id), date=today)
            .order_by(QuickSpendEntry.logged_at.desc())
            .all()
        )
        serialized = [_serialize_entry(entry) for entry in entries]
        total = round(sum(item["amount"] for item in serialized), 2)

        return (
            jsonify(
                {
                    "date": today.isoformat(),
                    "entries": serialized,
                    "total": total,
                    "count": len(serialized),
                }
            ),
            200,
        )
    except Exception:
        logger.exception("get_quick_log_today failed user_id=%s", user.id)
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500


@quick_spend_bp.route("/quick-log/summary", methods=["GET"])
@require_auth
def get_quick_log_summary():
    """GET /api/expenses/quick-log/summary — aggregate spend by signal and vibe."""
    user, err = _current_user_or_401()
    if err:
        return err

    days = request.args.get("days", 30, type=int)
    if days < 1:
        days = 1
    if days > 90:
        days = 90

    today = date.today()
    start_date = today - timedelta(days=days)

    try:
        base_filter = (
            QuickSpendEntry.user_id == int(user.id),
            QuickSpendEntry.date >= start_date,
            QuickSpendEntry.date <= today,
        )

        signal_rows = (
            db.session.query(
                QuickSpendEntry.vibe_signal,
                func.coalesce(func.sum(QuickSpendEntry.amount), 0),
            )
            .filter(*base_filter)
            .group_by(QuickSpendEntry.vibe_signal)
            .all()
        )
        vibe_rows = (
            db.session.query(
                QuickSpendEntry.spend_vibe,
                func.coalesce(func.sum(QuickSpendEntry.amount), 0),
            )
            .filter(*base_filter)
            .group_by(QuickSpendEntry.spend_vibe)
            .all()
        )

        by_signal = {
            str(signal): _money(total)
            for signal, total in signal_rows
            if signal
        }
        by_vibe = {
            str(vibe): _money(total)
            for vibe, total in vibe_rows
            if vibe
        }
        total = round(sum(by_signal.values()), 2)

        return (
            jsonify(
                {
                    "period_days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": today.isoformat(),
                    "total": total,
                    "by_signal": by_signal,
                    "by_vibe": by_vibe,
                }
            ),
            200,
        )
    except Exception:
        logger.exception("get_quick_log_summary failed user_id=%s", user.id)
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
