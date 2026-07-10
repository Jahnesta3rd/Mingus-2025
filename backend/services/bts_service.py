#!/usr/bin/env python3
"""Back-to-school planning: date setup, cash forecast tiers, and shortfall jobs."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from backend.services.cash_forecast_service import (
    classify_status,
    generate_daily_forecast,
)
from backend.models.bts import BackToSchoolSession
from backend.models.database import db

logger = logging.getLogger(__name__)


def _today() -> date:
    """Indirection so tests can freeze 'today' without replacing datetime.date."""
    return date.today()


# Estimated total BTS spend by child age band (essentials + supplies + extras).
_AGE_BUDGETS: list[tuple[int, int, float]] = [
    (0, 5, 200.0),
    (6, 8, 280.0),
    (9, 11, 350.0),
    (12, 14, 420.0),
    (15, 18, 500.0),
]
_DEFAULT_BUDGET = 300.0

# Static gig catalog used when tier-1 cash is short of estimated BTS needs.
_SECOND_JOB_CATALOG: list[dict[str, Any]] = [
    {
        "jobId": "doordash",
        "title": "DoorDash Driver",
        "hourlyRate": 15.0,
        "hoursPerWeek": 10,
        "startupCost": "0",
        "rampUpDays": 3,
    },
    {
        "jobId": "instacart",
        "title": "Instacart Shopper",
        "hourlyRate": 16.0,
        "hoursPerWeek": 8,
        "startupCost": "0",
        "rampUpDays": 2,
    },
    {
        "jobId": "tutoring",
        "title": "After-School Tutor",
        "hourlyRate": 25.0,
        "hoursPerWeek": 6,
        "startupCost": "0",
        "rampUpDays": 5,
    },
    {
        "jobId": "rideshare",
        "title": "Rideshare Driver",
        "hourlyRate": 18.0,
        "hoursPerWeek": 12,
        "startupCost": "50",
        "rampUpDays": 4,
    },
]


def _iso(d: date) -> str:
    return d.isoformat()


def _money(value: float | Decimal | int | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)


def estimate_bts_budget(child_age: int | None) -> float:
    """Return estimated total BTS spend for a child age."""
    if child_age is None:
        return _DEFAULT_BUDGET
    try:
        age = int(child_age)
    except (TypeError, ValueError):
        return _DEFAULT_BUDGET
    for lo, hi, budget in _AGE_BUDGETS:
        if lo <= age <= hi:
            return budget
    if age > 18:
        return 500.0
    return _DEFAULT_BUDGET


def compute_tier_dates(bts_date: date) -> dict[str, date]:
    """Tier 1 = BTS-14, Tier 2 = BTS-7, Tier 3 = BTS."""
    return {
        "tier1": bts_date - timedelta(days=14),
        "tier2": bts_date - timedelta(days=7),
        "tier3": bts_date,
    }


class BTSService:
    """
    Orchestrates back-to-school planning:
    1. Get BTS date from user
    2. Derive tier purchase dates (BTS-14 / BTS-7 / BTS)
    3. Query cash forecast balances on those dates
    4. Compute shortfall vs estimated BTS budget
    5. Recommend second jobs when cash is short
    6. Return a planning session payload for the UI
    """

    def __init__(self) -> None:
        # In-memory cache kept for backward-compatible get_session lookups.
        self._sessions: dict[str, dict[str, Any]] = {}

    def setup_bts_session(
        self,
        userId: str,
        btsDate: date,
        childName: str | None = None,
        childAge: int | None = None,
        childGender: str | None = None,
    ) -> dict[str, Any]:
        if not userId or not str(userId).strip():
            raise ValueError("userId is required")
        if not isinstance(btsDate, date) or isinstance(btsDate, datetime):
            raise ValueError("btsDate must be a date")

        today = _today()
        if btsDate < today:
            raise ValueError("btsDate must be today or in the future")

        tiers = compute_tier_dates(btsDate)
        balances = self._balances_for_tiers(str(userId).strip(), tiers)
        estimated_needed = estimate_bts_budget(childAge)
        tier1_balance = balances["tier1"]["forecastedBalance"]
        shortfall = _money(max(0.0, estimated_needed - tier1_balance))

        recommended_jobs: list[dict[str, Any]] = []
        if shortfall > 0:
            recommended_jobs = self._recommend_second_jobs(
                shortfall=shortfall,
                today=today,
                earn_by=tiers["tier2"],
            )

        session_row = BackToSchoolSession(
            user_id=str(userId).strip(),
            bts_date=btsDate,
            tier1_date=tiers["tier1"],
            tier2_date=tiers["tier2"],
            tier3_date=tiers["tier3"],
            tier1_balance=tier1_balance,
            tier2_balance=balances["tier2"]["forecastedBalance"],
            tier3_balance=balances["tier3"]["forecastedBalance"],
            child_name=childName,
            child_age=childAge,
            child_gender=childGender,
            shortfall=shortfall,
            estimated_budget=estimated_needed,
        )
        db.session.add(session_row)
        db.session.commit()

        session_id = str(session_row.session_id)
        days_until = (btsDate - today).days

        result: dict[str, Any] = {
            "sessionId": session_id,
            "btsDate": _iso(btsDate),
            "tier1Date": _iso(tiers["tier1"]),
            "tier2Date": _iso(tiers["tier2"]),
            "tier3Date": _iso(tiers["tier3"]),
            "availableBalances": balances,
            "daysUntilSchool": days_until,
            "shortfall": shortfall,
            "estimatedBudget": estimated_needed,
            "recommendedSecondJobs": recommended_jobs,
            "child": {
                "name": childName,
                "age": childAge,
                "gender": childGender,
            },
        }

        self._sessions[session_id] = {
            **result,
            "userId": str(userId).strip(),
            "createdAt": datetime.utcnow().isoformat() + "Z",
        }
        return result

    def get_forecast_timeline(self, user_id: str, bts_date: date) -> dict[str, Any]:
        """
        Cash forecast for the 3-week BTS planning window.

        Returns balances at today, tier1 (BTS-14), tier2 (BTS-7), and tier3 (BTS).
        """
        if not user_id or not str(user_id).strip():
            raise ValueError("user_id is required")
        if not isinstance(bts_date, date) or isinstance(bts_date, datetime):
            raise ValueError("bts_date must be a date")

        today = _today()
        tiers = compute_tier_dates(bts_date)
        points = {
            "today": today,
            "tier1": tiers["tier1"],
            "tier2": tiers["tier2"],
            "tier3": tiers["tier3"],
        }

        daily = self._daily_through(str(user_id).strip(), bts_date)
        by_date = {row["date"]: row for row in daily}

        timeline: list[dict[str, Any]] = []
        for key, d0 in points.items():
            row = by_date.get(_iso(d0))
            if row:
                balance = _money(row.get("closing_balance"))
                status = str(row.get("balance_status") or classify_status(Decimal(str(balance))))
            else:
                # Date before today or outside forecast window — use nearest available.
                balance, status = self._nearest_balance(daily, d0)

            label = {
                "today": "Today",
                "tier1": "Tier 1 — Essentials",
                "tier2": "Tier 2 — Supplies",
                "tier3": "Tier 3 — School start",
            }[key]

            timeline.append(
                {
                    "key": key,
                    "label": label,
                    "date": _iso(d0),
                    "forecastedBalance": balance,
                    "status": status,
                    "daysFromToday": (d0 - today).days,
                }
            )

        return {
            "userId": str(user_id).strip(),
            "btsDate": _iso(bts_date),
            "tier1Date": _iso(tiers["tier1"]),
            "tier2Date": _iso(tiers["tier2"]),
            "tier3Date": _iso(tiers["tier3"]),
            "timeline": timeline,
            "daysUntilSchool": (bts_date - today).days,
        }

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        cached = self._sessions.get(session_id)
        if cached:
            return cached
        try:
            sid = uuid.UUID(str(session_id).strip())
        except ValueError:
            return None
        row = BackToSchoolSession.query.filter_by(session_id=sid).first()
        return row.to_dict() if row else None

    def _daily_through(self, user_id: str, end_date: date) -> list[dict[str, Any]]:
        today = _today()
        days = max(1, (end_date - today).days + 1)
        # Pad a few days past BTS in case of timezone edge cases.
        days = max(days, 1) + 3
        try:
            return generate_daily_forecast(user_id, days=days)
        except Exception as exc:
            logger.exception("BTS cash forecast failed for user_id=%s: %s", user_id, exc)
            return []

    def _balances_for_tiers(
        self, user_id: str, tiers: dict[str, date]
    ) -> dict[str, dict[str, Any]]:
        end = max(tiers.values())
        daily = self._daily_through(user_id, end)
        by_date = {row["date"]: row for row in daily}

        out: dict[str, dict[str, Any]] = {}
        for key, d0 in tiers.items():
            row = by_date.get(_iso(d0))
            if row:
                balance = _money(row.get("closing_balance"))
                status = str(row.get("balance_status") or classify_status(Decimal(str(balance))))
            else:
                balance, status = self._nearest_balance(daily, d0)
            out[key] = {
                "date": _iso(d0),
                "forecastedBalance": balance,
                "status": status,
            }
        return out

    @staticmethod
    def _nearest_balance(
        daily: list[dict[str, Any]], target: date
    ) -> tuple[float, str]:
        if not daily:
            return 0.0, "danger"
        target_s = _iso(target)
        # Prefer exact, else last day on/before target, else first day after.
        before = [r for r in daily if r["date"] <= target_s]
        if before:
            row = before[-1]
        else:
            row = daily[0]
        balance = _money(row.get("closing_balance"))
        status = str(row.get("balance_status") or classify_status(Decimal(str(balance))))
        return balance, status

    def _recommend_second_jobs(
        self,
        *,
        shortfall: float,
        today: date,
        earn_by: date,
    ) -> list[dict[str, Any]]:
        """Rank gig options by how much they can earn before the tier-2 date."""
        recommendations: list[dict[str, Any]] = []
        for job in _SECOND_JOB_CATALOG:
            ramp = int(job["rampUpDays"])
            start = today + timedelta(days=ramp)
            if start > earn_by:
                continue
            earning_days = max(0, (earn_by - start).days)
            weeks = earning_days / 7.0
            weekly = float(job["hourlyRate"]) * float(job["hoursPerWeek"])
            potential = _money(weekly * weeks)
            if potential <= 0:
                continue
            recommendations.append(
                {
                    "jobId": job["jobId"],
                    "title": job["title"],
                    "hourlyRate": job["hourlyRate"],
                    "hoursPerWeek": job["hoursPerWeek"],
                    "weeklyIncome": _money(weekly),
                    "startupCost": job["startupCost"],
                    "rampUpDays": ramp,
                    "couldEarnBy": _iso(earn_by),
                    "potentialEarnings": potential,
                    "coversShortfall": potential >= shortfall,
                }
            )

        recommendations.sort(key=lambda j: j["potentialEarnings"], reverse=True)
        return recommendations[:3]
