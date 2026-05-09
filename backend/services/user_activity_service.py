#!/usr/bin/env python3
"""Aggregate recent user dashboard activity from existing event tables (throwaway adapter)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import desc

from backend.models.connection_trend import ConnectionTrendAssessment
from backend.models.life_ledger import LifeLedgerModuleAnswer
from backend.models.wellness import WeeklyCheckin

_LIFE_MODULES = frozenset({"body", "roof", "vehicle"})
_MODULE_LABEL = {
    "body": "Body check",
    "roof": "Roof check",
    "vehicle": "Vehicle check",
}


def _effective_ts(dt: datetime | None, fallback_day: date | None) -> datetime:
    if dt is not None:
        return dt
    if fallback_day is not None:
        return datetime.combine(fallback_day, datetime.min.time())
    return datetime.utcnow()


def _ts_iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        return ts.isoformat() + "Z"
    return ts.isoformat()


def get_recent_activity(user_id_int: int, limit: int = 20) -> list[dict[str, Any]]:
    """
    Compose recent activity items from existing event tables. Each item maps to:
      { id, type, title, description, timestamp, status, metadata? }

    Sources to compose from (in priority order; skip any that don't have data):
      - WeeklyCheckin entries → type="wellness_checkin"
      - ConnectionTrendAssessment entries → type="vibe_assessment"
      - life_ledger module submissions (body_check, roof_check, vehicle_check) → type="life_check"

    Sort by timestamp desc. Limit to `limit` items total across all sources.
    Return [] if no activity exists.
    """
    if limit < 1:
        return []

    cap = limit

    checkins = (
        WeeklyCheckin.query.filter_by(user_id=user_id_int)
        .order_by(
            desc(WeeklyCheckin.completed_at),
            desc(WeeklyCheckin.week_ending_date),
        )
        .limit(cap)
        .all()
    )

    assessments = (
        ConnectionTrendAssessment.query.filter_by(user_id=user_id_int)
        .order_by(desc(ConnectionTrendAssessment.assessed_at))
        .limit(cap)
        .all()
    )

    ledger_rows = (
        LifeLedgerModuleAnswer.query.filter(
            LifeLedgerModuleAnswer.user_id == user_id_int,
            LifeLedgerModuleAnswer.module.in_(_LIFE_MODULES),
        )
        .order_by(desc(LifeLedgerModuleAnswer.completed_at))
        .limit(cap)
        .all()
    )

    keyed: list[tuple[datetime, dict[str, Any]]] = []

    for c in checkins:
        ts = _effective_ts(c.completed_at, c.week_ending_date)
        completed = c.completed_at is not None
        keyed.append(
            (
                ts,
                {
                    "id": str(c.id),
                    "type": "wellness_checkin",
                    "title": "Weekly wellness check-in",
                    "description": f"Week ending {c.week_ending_date.isoformat()}",
                    "timestamp": _ts_iso(ts),
                    "status": "completed" if completed else "pending",
                    "metadata": {"week_ending_date": c.week_ending_date.isoformat()},
                },
            )
        )

    for a in assessments:
        ts = a.assessed_at
        keyed.append(
            (
                ts,
                {
                    "id": str(a.id),
                    "type": "vibe_assessment",
                    "title": "Connection trend assessment",
                    "description": "Recorded a vibe assessment for someone you track.",
                    "timestamp": _ts_iso(ts),
                    "status": "completed",
                    "metadata": {"person_id": str(a.person_id)},
                },
            )
        )

    for row in ledger_rows:
        label = _MODULE_LABEL.get(row.module, "Life check")
        meta_module = f"{row.module}_check" if row.module in _LIFE_MODULES else row.module
        ts = row.completed_at
        keyed.append(
            (
                ts,
                {
                    "id": str(row.id),
                    "type": "life_check",
                    "title": label,
                    "description": f"{label} submitted (score {row.score}).",
                    "timestamp": _ts_iso(ts),
                    "status": "completed",
                    "metadata": {"module": meta_module, "score": row.score},
                },
            )
        )

    keyed.sort(key=lambda t: t[0], reverse=True)
    return [item for _, item in keyed[:limit]]
