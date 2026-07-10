#!/usr/bin/env python3
"""Wisdom call context: wellness metrics, spending signals, and script inputs."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta
from typing import Any

import anthropic
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import desc

from backend.models.career_profile import CareerProfile
from backend.models.checkin import WeeklyCheckin
from backend.models.database import db
from backend.models.debt_profile import DebtProfile
from backend.models.housing_profile import HousingProfile
from backend.models.in_app_notification import InAppNotification
from backend.models.job_posting import JobPosting
from backend.models.life_correlation import LifeScoreSnapshot
from backend.models.todo import Todo
from backend.models.user_models import User
from backend.models.user_profile import UserProfile
from backend.models.vibe_tracker import VibePersonAssessment, VibePersonTrend, VibeTrackedPerson
from backend.models.wellness import UserSpendingBaseline
from backend.services.cash_forecast_service import _iter_normalized_important_events
from backend.services.email_service import EmailService
from backend.services.hprs_input_service import get_hprs_inputs
from backend.services.market_conditions_service import get_market_conditions
from backend.utils.user_profile_context import resolve_current_salary

logger = logging.getLogger(__name__)

_WISDOM_CALL_MODEL = "claude-opus-4-6"
_WISDOM_CALL_MAX_TOKENS = 1400
_WISDOM_CALL_TEMPERATURE = 0.7
_WISDOM_CALL_MAX_RETRIES = 3


class WisdomCallScriptError(Exception):
    """Raised when wisdom-call script generation fails after retries."""


# Progress at or above this % counts as on_track when no explicit flag is set.
_ON_TRACK_PROGRESS_PCT = 70.0
# Default down-payment assumption for housing buy goals.
_DEFAULT_DOWN_PAYMENT_PCT = 0.20
# Upcoming events window for wisdom-call context.
_UPCOMING_EVENTS_DAYS = 60
# Financial projection lookback + display caps.
_PROJECTION_LOOKBACK_WEEKS = 8
_MAX_MILESTONES = 4
_WEEKS_PER_MONTH = 4.333
# Status thresholds vs target date (days_difference = projected - target).
_AHEAD_DAYS = -30
_BEHIND_DAYS = 7
_PARTNER_TYPES = frozenset(
    {
        "partner",
        "spouse",
        "significant_other",
        "boyfriend",
        "girlfriend",
        "fiancé",
        "fiance",
        "fiancée",
        "fiancee",
        "husband",
        "wife",
    }
)
_FAMILY_TYPES = frozenset(
    {
        "family",
        "parent",
        "mother",
        "father",
        "sibling",
        "brother",
        "sister",
        "child",
        "kid",
        "kids",
        "son",
        "daughter",
        "relative",
    }
)
_FAMILY_CARD_TYPES = frozenset({"family", "kids"})
_RELATIONSHIP_RATING_KEYS = (
    "relationship_temperature",
    "primary_partner_rating",
    "financial_communication_with_partner",
    "parenting_stress",
    "relationship_satisfaction",
    "social_interactions",
)

_TREND_EPS = 0.5

# Spike: current >= 1.5x baseline (or prior week when no baseline).
_SPIKE_RATIO = 1.5
# Mild elevation: current >= 1.2x baseline.
_ELEVATED_RATIO = 1.2

_CATEGORY_KEYS = (
    "groceries_estimate",
    "dining_estimate",
    "entertainment_estimate",
    "shopping_estimate",
    "transport_estimate",
    "utilities_estimate",
    "other_estimate",
)
_TAGGED_KEYS = ("impulse_spending", "stress_spending", "celebration_spending")
_CHECKIN_TO_BASELINE = {
    "groceries_estimate": "avg_groceries",
    "dining_estimate": "avg_dining",
    "entertainment_estimate": "avg_entertainment",
    "shopping_estimate": "avg_shopping",
    "transport_estimate": "avg_transport",
    "utilities_estimate": "avg_utilities",
    "other_estimate": "avg_other",
    "impulse_spending": "avg_impulse",
    "stress_spending": "avg_stress",
}

# Metrics where a higher value is better (for interpretive trend labels).
_HIGHER_IS_BETTER = frozenset(
    {
        "mood_rating",
        "activity_frequency",
        "avg_sleep_hours",
        "body_score",
        "rest_quality",
        "overall_mood",
        "sleep_quality",
        "relationship_temperature",
        "primary_partner_rating",
        "financial_communication_with_partner",
        "relationship_satisfaction",
        "social_interactions",
    }
)

# Metrics where a lower value is better.
_LOWER_IS_BETTER = frozenset({"stress_level", "financial_stress", "parenting_stress"})


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _raw_direction(current: float | None, previous: float | None) -> str:
    """Week-over-week direction of the raw metric: up / down / flat / unknown."""
    if current is None or previous is None:
        return "unknown"
    delta = current - previous
    if delta > _TREND_EPS:
        return "up"
    if delta < -_TREND_EPS:
        return "down"
    return "flat"


def _interpretive_trend(metric: str, direction: str) -> str:
    """Map raw direction to improving / declining / stable for script language."""
    if direction in ("unknown", "flat"):
        return "stable" if direction == "flat" else "unknown"
    if metric in _LOWER_IS_BETTER:
        return "improving" if direction == "down" else "declining"
    if metric in _HIGHER_IS_BETTER:
        return "improving" if direction == "up" else "declining"
    # Neutral metrics: report raw direction only via interpretive labels.
    if direction == "up":
        return "increasing"
    if direction == "down":
        return "decreasing"
    return "stable"


class WisdomCallService:
    """Builds personalized wisdom-call context from weekly check-ins."""

    def _get_wellness_data(self, user_id: int, lookback_weeks: int = 4) -> dict[str, Any]:
        """
        Return current wellness metrics with week-over-week trends.

        Pulls the latest WeeklyCheckin plus the prior week for deltas. Uses up to
        ``lookback_weeks`` rows for multi-week averages when present.
        """
        checkins = (
            WeeklyCheckin.query.filter_by(user_id=user_id)
            .order_by(desc(WeeklyCheckin.week_ending_date))
            .limit(max(2, lookback_weeks))
            .all()
        )

        if not checkins:
            return {
                "has_data": False,
                "week_number": None,
                "year": None,
                "week_ending_date": None,
                "metrics": {},
                "averages": {},
            }

        current = checkins[0]
        previous = checkins[1] if len(checkins) > 1 else None

        metric_keys = (
            "mood_rating",
            "stress_level",
            "activity_frequency",
            "avg_sleep_hours",
            "body_score",
            "rest_quality",
            "overall_mood",
            "sleep_hours",
            "sleep_quality",
            "meditation_minutes",
            "meditation_minutes_total",
            "financial_stress",
            "relationship_temperature",
            "spiritual_connection_rating",
        )

        metrics: dict[str, Any] = {}
        for key in metric_keys:
            current_val = _coerce_float(getattr(current, key, None))
            previous_val = (
                _coerce_float(getattr(previous, key, None)) if previous is not None else None
            )
            direction = _raw_direction(current_val, previous_val)
            metrics[key] = {
                "value": current_val,
                "previous": previous_val,
                "delta": (
                    round(current_val - previous_val, 2)
                    if current_val is not None and previous_val is not None
                    else None
                ),
                "direction": direction,
                "trend": _interpretive_trend(key, direction),
            }

        averages: dict[str, float | None] = {}
        for key in ("mood_rating", "stress_level", "activity_frequency", "avg_sleep_hours"):
            vals = [
                v
                for v in (_coerce_float(getattr(c, key, None)) for c in checkins)
                if v is not None
            ]
            averages[key] = round(sum(vals) / len(vals), 2) if vals else None

        return {
            "has_data": True,
            "week_number": current.week_number,
            "year": current.year,
            "week_ending_date": (
                current.week_ending_date.isoformat() if current.week_ending_date else None
            ),
            "checkins_used": len(checkins),
            "metrics": metrics,
            "averages": averages,
        }

    def _get_spending_signals(self, user_id: int, lookback_weeks: int = 8) -> dict[str, Any]:
        """
        Calculate spending delta vs baseline, category spikes, and recurring patterns.

        Prefers ``spending_delta_from_baseline`` / ``unusual_spending_detected`` on the
        latest check-in when set; otherwise derives signals from estimates and
        ``UserSpendingBaseline`` (falling back to prior-week averages).
        """
        checkins = (
            WeeklyCheckin.query.filter_by(user_id=user_id)
            .order_by(desc(WeeklyCheckin.week_ending_date))
            .limit(max(2, lookback_weeks))
            .all()
        )

        empty = {
            "has_data": False,
            "delta": None,
            "spikes": [],
            "patterns": [],
            "unusual_spending_detected": False,
            "categories": {},
            "tagged": {},
        }
        if not checkins:
            return empty

        current = checkins[0]
        previous = checkins[1] if len(checkins) > 1 else None
        history = checkins[1:]  # older weeks, newest-first

        current_total = _checkin_variable_total(current)
        baseline_row = UserSpendingBaseline.query.filter_by(user_id=user_id).first()
        baseline_avg = _coerce_float(
            getattr(baseline_row, "avg_total_variable", None) if baseline_row else None
        )
        if baseline_avg is None:
            hist_totals = [
                t for t in (_checkin_variable_total(c) for c in history) if t is not None
            ]
            baseline_avg = (
                round(sum(hist_totals) / len(hist_totals), 2) if hist_totals else None
            )

        stored_delta = _coerce_float(getattr(current, "spending_delta_from_baseline", None))
        if stored_delta is not None:
            delta_amount = round(stored_delta, 2)
            delta_pct = (
                round((stored_delta / baseline_avg) * 100.0, 1)
                if baseline_avg and baseline_avg > 0
                else None
            )
        elif current_total is not None and baseline_avg is not None:
            delta_amount = round(current_total - baseline_avg, 2)
            delta_pct = (
                round((delta_amount / baseline_avg) * 100.0, 1) if baseline_avg > 0 else None
            )
        else:
            prev_total = _checkin_variable_total(previous) if previous else None
            if current_total is not None and prev_total is not None:
                delta_amount = round(current_total - prev_total, 2)
                delta_pct = (
                    round((delta_amount / prev_total) * 100.0, 1) if prev_total > 0 else None
                )
            else:
                delta_amount = None
                delta_pct = None

        unusual = bool(getattr(current, "unusual_spending_detected", False))
        if not unusual and delta_pct is not None and abs(delta_pct) >= 50:
            unusual = True

        categories = _category_comparisons(current, previous, baseline_row)
        tagged = _tagged_comparisons(current, previous, baseline_row)
        spikes = _detect_spikes(categories, tagged)
        if spikes:
            unusual = True

        patterns = _detect_patterns(current, checkins, categories, tagged, delta_pct)

        return {
            "has_data": True,
            "week_number": current.week_number,
            "week_ending_date": (
                current.week_ending_date.isoformat() if current.week_ending_date else None
            ),
            "delta": {
                "amount": delta_amount,
                "percent": delta_pct,
                "current_total": current_total,
                "baseline_avg": baseline_avg,
                "direction": (
                    "up"
                    if delta_amount is not None and delta_amount > _TREND_EPS
                    else (
                        "down"
                        if delta_amount is not None and delta_amount < -_TREND_EPS
                        else "flat"
                        if delta_amount is not None
                        else "unknown"
                    )
                ),
            },
            "spikes": spikes,
            "patterns": patterns,
            "unusual_spending_detected": unusual,
            "categories": categories,
            "tagged": tagged,
            "flags": {
                "had_impulse_purchases": bool(getattr(current, "had_impulse_purchases", False)),
                "had_stress_purchases": bool(getattr(current, "had_stress_purchases", False)),
                "social_spending_unplanned": getattr(current, "social_spending_unplanned", None),
                "unexpected_kid_spending": getattr(current, "unexpected_kid_spending", None),
            },
        }

    def _get_todos_data(self, user_id: int, week_number: int | None = None) -> dict[str, Any]:
        """
        Count todos, break down by domain, and list overdue open items.

        Open statuses: pending, in_progress (and any status other than completed/cancelled/done).
        Overdue: open todo with due_date before today.
        """
        todos = (
            Todo.query.filter_by(user_id=user_id)
            .order_by(Todo.created_at.desc())
            .all()
        )

        if not todos:
            return {
                "has_data": False,
                "counts": {
                    "total": 0,
                    "open": 0,
                    "completed": 0,
                    "cancelled": 0,
                    "overdue": 0,
                },
                "by_domain": {},
                "by_status": {},
                "by_priority": {},
                "overdue": [],
                "open": [],
                "this_week": [],
            }

        today = date.today()
        completed_statuses = frozenset({"completed", "done"})
        cancelled_statuses = frozenset({"cancelled", "canceled"})

        by_domain: dict[str, dict[str, int]] = {}
        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        overdue_items: list[dict[str, Any]] = []
        open_items: list[dict[str, Any]] = []
        this_week_items: list[dict[str, Any]] = []

        open_count = 0
        completed_count = 0
        cancelled_count = 0

        for todo in todos:
            status = (todo.status or "pending").strip().lower()
            priority = (todo.priority or "medium").strip().lower()
            domain = (todo.domain or "unspecified").strip().lower()

            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1

            domain_bucket = by_domain.setdefault(
                domain,
                {"total": 0, "open": 0, "completed": 0, "overdue": 0},
            )
            domain_bucket["total"] += 1

            is_completed = status in completed_statuses
            is_cancelled = status in cancelled_statuses
            is_open = not is_completed and not is_cancelled

            if is_completed:
                completed_count += 1
                domain_bucket["completed"] += 1
            elif is_cancelled:
                cancelled_count += 1
            else:
                open_count += 1
                domain_bucket["open"] += 1

            payload = _todo_to_dict(todo, today=today, is_open=is_open)

            if is_open:
                open_items.append(payload)
                if payload["is_overdue"]:
                    overdue_items.append(payload)
                    domain_bucket["overdue"] += 1

            if week_number is not None and todo.week_created == week_number:
                this_week_items.append(payload)
            elif week_number is None and todo.week_created == today.isocalendar().week:
                this_week_items.append(payload)

        overdue_items.sort(key=lambda t: (t.get("due_date") or "9999-99-99", t.get("priority") or ""))
        open_items.sort(
            key=lambda t: (
                0 if t.get("is_overdue") else 1,
                t.get("due_date") or "9999-99-99",
                {"high": 0, "medium": 1, "low": 2}.get(t.get("priority") or "medium", 1),
            )
        )

        return {
            "has_data": True,
            "counts": {
                "total": len(todos),
                "open": open_count,
                "completed": completed_count,
                "cancelled": cancelled_count,
                "overdue": len(overdue_items),
            },
            "by_domain": by_domain,
            "by_status": by_status,
            "by_priority": by_priority,
            "overdue": overdue_items,
            "open": open_items,
            "this_week": this_week_items,
        }

    def _get_goals_data(self, user_id: int, lookback_weeks: int = 4) -> dict[str, Any]:
        """
        Track goal progress %, on_track flags, and recent wins.

        Sources: ``User.primary_financial_goal``, ``UserProfile.goals`` JSON,
        ``HousingProfile`` buy-goal savings, and ``WeeklyCheckin.wins``.
        """
        user = User.query.get(user_id)
        profile = None
        if user and user.email:
            profile = UserProfile.query.filter_by(email=user.email).first()
        housing = HousingProfile.query.filter_by(user_id=user_id).first()

        goals: list[dict[str, Any]] = []

        primary = (user.primary_financial_goal or "").strip() if user else ""
        if primary:
            goals.append(
                _normalize_goal(
                    {
                        "id": "primary_financial_goal",
                        "title": primary,
                        "domain": "financial",
                        "source": "user.primary_financial_goal",
                    }
                )
            )

        for raw in _parse_profile_goals(profile.goals if profile else None):
            goals.append(_normalize_goal({**raw, "source": raw.get("source") or "user_profile.goals"}))

        housing_goal = _housing_buy_goal(housing)
        if housing_goal is not None:
            # Prefer housing progress over a duplicate primary label when both exist.
            goals.append(housing_goal)

        # Deduplicate by title (case-insensitive), keeping the richest progress data.
        goals = _dedupe_goals(goals)

        wins = _collect_wins(user_id, lookback_weeks)

        tracked = [g for g in goals if g.get("progress_pct") is not None]
        on_track_goals = [g for g in goals if g.get("on_track") is True]
        off_track_goals = [g for g in goals if g.get("on_track") is False]
        avg_progress = (
            round(sum(g["progress_pct"] for g in tracked) / len(tracked), 1)
            if tracked
            else None
        )
        overall_on_track = (
            None
            if not goals
            else (
                all(g.get("on_track") is True for g in goals if g.get("on_track") is not None)
                if any(g.get("on_track") is not None for g in goals)
                else None
            )
        )

        has_data = bool(goals or wins)
        return {
            "has_data": has_data,
            "primary_financial_goal": primary or None,
            "goals": goals,
            "counts": {
                "total": len(goals),
                "with_progress": len(tracked),
                "on_track": len(on_track_goals),
                "off_track": len(off_track_goals),
                "wins": len(wins),
            },
            "average_progress_pct": avg_progress,
            "on_track": overall_on_track,
            "wins": wins,
        }

    def _get_relationships_data(
        self,
        user_id: int,
        lookback_weeks: int = 4,
        upcoming_days: int = _UPCOMING_EVENTS_DAYS,
    ) -> dict[str, Any]:
        """
        Track relationship health ratings, week-over-week changes, partner/family
        connections, and upcoming significant events.
        """
        checkins = (
            WeeklyCheckin.query.filter_by(user_id=user_id)
            .order_by(desc(WeeklyCheckin.week_ending_date))
            .limit(max(2, lookback_weeks))
            .all()
        )
        current = checkins[0] if checkins else None
        previous = checkins[1] if len(checkins) > 1 else None

        ratings = _relationship_ratings(current, previous)
        changes = _relationship_changes(current, previous, ratings)

        people = (
            VibeTrackedPerson.query.filter_by(user_id=user_id, is_archived=False)
            .order_by(VibeTrackedPerson.nickname.asc())
            .all()
        )
        connections = [_connection_summary(p) for p in people]
        partner = _select_partner(connections, current)
        family = [
            c
            for c in connections
            if c.get("is_family") and not c.get("is_partner")
        ]

        events = _upcoming_relationship_events(user_id, upcoming_days)

        health_vals = [
            ratings[k]["value"]
            for k in (
                "relationship_temperature",
                "primary_partner_rating",
                "relationship_satisfaction",
            )
            if k in ratings and ratings[k].get("value") is not None
        ]
        # parenting_stress is inverted for health (lower is better)
        parenting = ratings.get("parenting_stress", {}).get("value")
        if parenting is not None:
            health_vals.append(max(1.0, 11.0 - parenting))

        overall_health = (
            round(sum(health_vals) / len(health_vals), 1) if health_vals else None
        )
        if partner and partner.get("emotional_score") is not None:
            # Blend check-in health with partner vibe emotional score (0-100 → ~1-10).
            vibe_as_10 = float(partner["emotional_score"]) / 10.0
            if overall_health is None:
                overall_health = round(vibe_as_10, 1)
            else:
                overall_health = round((overall_health * 0.6) + (vibe_as_10 * 0.4), 1)

        has_data = bool(checkins or people or events)
        return {
            "has_data": has_data,
            "overall_health": overall_health,
            "ratings": ratings,
            "changes": changes,
            "partner": partner,
            "family": family,
            "connections": connections,
            "events": events,
            "counts": {
                "connections": len(connections),
                "family": len(family),
                "upcoming_events": len(events),
                "ratings_present": sum(
                    1 for r in ratings.values() if r.get("value") is not None
                ),
                "improving": sum(1 for c in changes.get("metrics", []) if c.get("trend") == "improving"),
                "declining": sum(1 for c in changes.get("metrics", []) if c.get("trend") == "declining"),
            },
            "flags": {
                "has_partner": partner is not None,
                "meaningful_time_with_people": (
                    getattr(current, "meaningful_time_with_people", None)
                    if current
                    else None
                ),
                "financial_convo_with_partner": (
                    getattr(current, "financial_convo_with_partner", None)
                    if current
                    else None
                ),
                "partner_spending_unplanned": (
                    getattr(current, "partner_spending_unplanned", None)
                    if current
                    else None
                ),
            },
        }

    def _get_career_data(self, user_id: int, opportunity_limit: int = 5) -> dict[str, Any]:
        """
        Return career income, market percentile, compensation gaps, and opportunities.

        Sources: ``CareerProfile``, HPRS income inputs, BLS/OES market percentiles,
        and active ``JobPosting`` rows in the user's field.
        """
        user = User.query.get(user_id)
        career = CareerProfile.query.filter_by(user_id=user_id).first()
        hprs = get_hprs_inputs(user_id)

        annual_income = resolve_current_salary(user, career) if user else None
        monthly_income = _coerce_float(hprs.get("gross_monthly_income"))
        if monthly_income is None and annual_income is not None:
            monthly_income = round(annual_income / 12.0, 2)

        target_comp = _coerce_float(getattr(career, "target_comp", None) if career else None)
        # target_comp on CareerProfile is often a stretch/target; don't treat it as
        # current income when resolve_current_salary already fell back to it.
        income = {
            "annual": annual_income,
            "monthly": monthly_income,
            "target_comp": target_comp,
            "income_type": hprs.get("income_type"),
        }

        personal = None
        personal_note = None
        if user is not None:
            try:
                market = get_market_conditions(user)
                personal = market.get("personal")
                personal_note = (market.get("meta") or {}).get("personal_note")
            except Exception:
                personal = None
                personal_note = None

        percentile = None
        if personal and personal.get("percentile") is not None:
            percentile = int(personal["percentile"])
        elif hprs.get("income_percentile") is not None:
            try:
                percentile = int(hprs["income_percentile"])
            except (TypeError, ValueError):
                percentile = None

        percentile_payload = {
            "value": percentile,
            "above_median": personal.get("above_median") if personal else None,
            "field_label": (
                personal.get("field_label")
                if personal
                else (career.bls_career_field if career else None)
            ),
            "msa_name": personal.get("msa_name") if personal else None,
            "bands": (
                {
                    "pct_10": personal.get("pct_10"),
                    "pct_25": personal.get("pct_25"),
                    "pct_50": personal.get("pct_50"),
                    "pct_75": personal.get("pct_75"),
                    "pct_90": personal.get("pct_90"),
                }
                if personal
                else None
            ),
            "wage_growth_yoy": personal.get("wage_growth_yoy") if personal else None,
            "source_year": personal.get("source_year") if personal else None,
            "note": personal_note,
        }

        gaps = _career_gaps(
            annual_income=annual_income,
            target_comp=target_comp,
            personal=personal,
        )
        opportunities = _career_opportunities(
            career=career,
            annual_income=annual_income,
            personal=personal,
            gaps=gaps,
            limit=opportunity_limit,
        )

        profile = None
        if career is not None:
            profile = {
                "current_role": career.current_role,
                "occupation_key": career.occupation_key,
                "industry": career.industry,
                "bls_career_field": career.bls_career_field,
                "years_experience": career.years_experience,
                "satisfaction": career.satisfaction,
                "open_to_move": bool(career.open_to_move),
                "seniority_level": career.seniority_level,
                "is_management": career.is_management,
                "employer_name": career.employer_name_text,
            }

        has_data = bool(
            career is not None
            or annual_income is not None
            or monthly_income is not None
            or percentile is not None
            or opportunities
        )
        return {
            "has_data": has_data,
            "profile": profile,
            "income": income,
            "percentile": percentile_payload,
            "gaps": gaps,
            "opportunities": opportunities,
            "counts": {
                "gaps": len(gaps),
                "opportunities": len(opportunities),
                "job_matches": sum(
                    1 for o in opportunities if o.get("type") == "job_posting"
                ),
            },
            "flags": {
                "open_to_move": bool(career.open_to_move) if career else False,
                "below_median": (
                    personal.get("above_median") is False if personal else None
                ),
                "has_target_gap": any(g.get("id") == "target_comp_gap" for g in gaps),
                "low_satisfaction": (
                    career.satisfaction is not None and career.satisfaction <= 2
                    if career
                    else False
                ),
            },
        }

    def _get_financial_projections(
        self,
        user_id: int,
        week_number: int | None = None,
    ) -> dict[str, Any]:
        """
        Project when the user will hit financial milestones at their current rate.

        Uses active goals (profile, housing down payment, debt payoff) and an
        8-week historical saving/payment rate. Compares projected hit date to
        each goal's target date (on_track / ahead / behind).
        """
        del week_number  # reserved for week-scoped goal filtering
        today = date.today()
        weekly_rate = _estimate_weekly_saving_rate(user_id)
        debt_weekly_rate = _estimate_weekly_debt_paydown_rate(user_id)

        raw_milestones = _collect_projection_milestones(user_id)
        projected: list[dict[str, Any]] = []
        for milestone in raw_milestones:
            rate = (
                debt_weekly_rate
                if milestone.get("kind") == "debt_payoff"
                else weekly_rate
            )
            projected.append(
                _project_milestone(milestone, weekly_rate=rate, today=today)
            )

        # Prefer actionable milestones with dates/rates; cap to top 3–4.
        projected.sort(
            key=lambda m: (
                0 if m.get("status") == "behind" else 1,
                0 if m.get("status") != "no_data" else 1,
                m.get("days_difference") is None,
                abs(m.get("days_difference") or 0),
            )
        )
        milestones = projected[:_MAX_MILESTONES]

        on_track_n = sum(1 for m in milestones if m.get("status") == "on_track")
        ahead_n = sum(1 for m in milestones if m.get("status") == "ahead")
        behind_n = sum(1 for m in milestones if m.get("status") == "behind")
        no_data_n = sum(1 for m in milestones if m.get("status") == "no_data")

        parts: list[str] = []
        if on_track_n:
            parts.append(f"on track for {on_track_n} goal{'s' if on_track_n != 1 else ''}")
        if ahead_n:
            parts.append(f"ahead on {ahead_n} goal{'s' if ahead_n != 1 else ''}")
        if behind_n:
            parts.append(f"behind on {behind_n} goal{'s' if behind_n != 1 else ''}")
        if no_data_n and not parts:
            parts.append("not enough savings history to project yet")
        summary = (
            ", ".join(parts).capitalize()
            if parts
            else "No active financial milestones to project"
        )

        return {
            "has_data": bool(milestones),
            "weekly_saving_rate": weekly_rate,
            "weekly_debt_paydown_rate": debt_weekly_rate,
            "milestones": milestones,
            "total_projection_summary": summary,
            "counts": {
                "total": len(milestones),
                "on_track": on_track_n,
                "ahead": ahead_n,
                "behind": behind_n,
                "no_data": no_data_n,
            },
        }

    def aggregate_user_context(
        self,
        user_id: int,
        week_number: int | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate wellness, spending, todos, goals, relationships, career, and
        financial projections into one wisdom-call context payload.
        """
        if week_number is None:
            week_number = int(date.today().isocalendar().week)

        return {
            "user_id": user_id,
            "week_number": week_number,
            "wellness": self._get_wellness_data(user_id),
            "todos": self._get_todos_data(user_id, week_number),
            "spending": self._get_spending_signals(user_id),
            "goals": self._get_goals_data(user_id),
            "relationships": self._get_relationships_data(user_id),
            "career": self._get_career_data(user_id),
            "financial_projections": self._get_financial_projections(
                user_id, week_number
            ),
        }

    def _build_system_prompt(self, user_profile: dict[str, Any] | None = None) -> str:
        """
        Build the wisdom-call system prompt: advisor persona + projection guidance.

        ``user_profile`` may include first_name, primary_financial_goal, tier,
        and other light personalization fields from the caller.
        """
        profile = user_profile or {}
        first_name = (
            (profile.get("first_name") or profile.get("name") or "").strip() or "friend"
        )
        goal = (
            (profile.get("primary_financial_goal") or profile.get("goal") or "").strip()
            or "build financial stability"
        )
        tier = (profile.get("tier") or profile.get("user_tier") or "").strip() or "member"

        return f"""You are Mingus Wisdom — a warm, direct personal finance and life advisor for Black professionals.
You speak like a trusted coach: supportive, never judgmental, specific with numbers and dates, and always actionable.
Address the user as {first_name} when natural. Their primary focus is: {goal}. Membership tier: {tier}.

VOICE & STYLE
- Conversational spoken script (this may be read aloud as a weekly wisdom call).
- Short paragraphs. Concrete dollars, dates, and weekly actions — not vague encouragement.
- Celebrate wins. Name patterns without shaming. Suggest, don't demand.
- Cover the whole life picture when data is present: wellness, spending, goals, relationships, career, and todos.
- Prefer 1–3 clear next steps over a long lecture.

FINANCIAL PROJECTIONS (when projection data is provided)
When you receive financial_projections / milestone data:
- Reference milestone projections with specific dates and dollar amounts.
- Use motivational language for on-track and ahead goals.
- Create urgency for behind-track goals — clear, calm, and concrete (not fear-based).
- Give a concrete weekly (and daily when helpful) action for shortfalls.
- Tie the ask to the user's current weekly saving rate when available.

Examples of the tone to match:
- On track / ahead: "You'll hit your $5K emergency fund by March 15. That's only 6 weeks away. If you can keep saving $150/week, you'll have it."
- Behind: "Your down payment target is Dec 31, but at current rate, you'll hit it April 1. You need to save $100 more per week."

When a milestone is close, lean into motivational framing (e.g. "Only $1,200 away").
When status is no_data, do not invent a projected date — ask for consistency or note missing history.

BOUNDARIES
- Observational and practical only — no clinical diagnoses, no legal advice, no guaranteed investment returns.
- Do not invent balances, rates, or dates that are not in the provided context.
- If a section has no data, skip it gracefully rather than fabricating detail.
""".strip()

    def _build_context_message(
        self,
        user_context: dict[str, Any],
        user_name: str,
        week_number: int,
    ) -> str:
        """
        Format aggregated data into a structured user message for Claude.

        Ordered brief: wellness → todos → spending → projections → goals →
        relationships → career. Safe against missing/partial aggregator payloads.
        """
        wellness = user_context.get("wellness") or {}
        spending = user_context.get("spending") or {}
        todos = user_context.get("todos") or {}
        goals = user_context.get("goals") or {}
        relationships = user_context.get("relationships") or {}
        career = user_context.get("career") or {}
        projections = user_context.get("financial_projections") or {}

        name = (user_name or "friend").strip() or "friend"

        sections = [
            f"Write a personalized wisdom call script for {name}, Week {week_number}.",
            "",
            _format_wellness_section(wellness),
            "",
            _format_todos_section(todos),
            "",
            _format_spending_section(spending),
            "",
            _format_projections_section(projections),
            "",
            _format_goals_section(goals),
            "",
            _format_relationships_section(relationships),
            "",
            _format_career_section(career),
            "",
            "Now write the wisdom call script following the guidelines in your system prompt.",
        ]
        return "\n".join(sections).strip() + "\n"

    def generate_script(
        self,
        context: dict[str, Any],
        user_profile: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a wisdom-call script via Claude Opus 4.6.

        Uses ``_build_system_prompt`` + ``_build_context_message`` from the
        aggregated context. Retries on rate limits with exponential backoff.
        """
        if not isinstance(context, dict):
            raise WisdomCallScriptError("context must be an aggregated user context dict")

        profile = user_profile or {}
        user_name = (
            (profile.get("first_name") or profile.get("name") or "").strip()
            or "friend"
        )
        week_number = context.get("week_number")
        if week_number is None:
            week_number = int(date.today().isocalendar().week)

        system_prompt = self._build_system_prompt(profile)
        user_message = self._build_context_message(
            context,
            user_name=user_name,
            week_number=int(week_number),
        )

        last_error: Exception | None = None
        for attempt in range(_WISDOM_CALL_MAX_RETRIES):
            try:
                client = anthropic.Anthropic()
                response = client.messages.create(
                    model=_WISDOM_CALL_MODEL,
                    max_tokens=_WISDOM_CALL_MAX_TOKENS,
                    temperature=_WISDOM_CALL_TEMPERATURE,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                block = response.content[0] if response.content else None
                text = (getattr(block, "text", None) or "").strip()
                if not text:
                    raise WisdomCallScriptError("Claude returned an empty wisdom-call script")

                projections = context.get("financial_projections") or {}
                if projections.get("milestones"):
                    text = self._enhance_script_with_projections(text, projections)

                is_valid, errors = self._validate_script(text, context)
                if not is_valid:
                    logger.warning(
                        "wisdom_call script validation issues: %s",
                        errors,
                    )
                elif errors:
                    logger.info(
                        "wisdom_call script soft validation notes: %s",
                        errors,
                    )
                return text
            except anthropic.RateLimitError as exc:
                last_error = exc
                wait_s = _rate_limit_wait_seconds(exc, attempt)
                logger.warning(
                    "wisdom_call generate_script rate-limited (attempt %s/%s); sleeping %.1fs",
                    attempt + 1,
                    _WISDOM_CALL_MAX_RETRIES,
                    wait_s,
                )
                time.sleep(wait_s)
            except anthropic.APIStatusError as exc:
                last_error = exc
                status = getattr(exc, "status_code", None)
                # Retry transient 5xx / overloaded responses.
                if status in {429, 500, 502, 503, 529} and attempt < _WISDOM_CALL_MAX_RETRIES - 1:
                    wait_s = min(2 ** attempt, 30)
                    logger.warning(
                        "wisdom_call generate_script API status %s (attempt %s/%s); sleeping %ss",
                        status,
                        attempt + 1,
                        _WISDOM_CALL_MAX_RETRIES,
                        wait_s,
                    )
                    time.sleep(wait_s)
                    continue
                logger.exception("wisdom_call generate_script API status error")
                raise WisdomCallScriptError(
                    f"Wisdom call generation failed (status={status})"
                ) from exc
            except anthropic.APIConnectionError as exc:
                last_error = exc
                if attempt < _WISDOM_CALL_MAX_RETRIES - 1:
                    wait_s = min(2 ** attempt, 20)
                    logger.warning(
                        "wisdom_call generate_script connection error (attempt %s/%s); sleeping %ss",
                        attempt + 1,
                        _WISDOM_CALL_MAX_RETRIES,
                        wait_s,
                    )
                    time.sleep(wait_s)
                    continue
                logger.exception("wisdom_call generate_script connection failed")
                raise WisdomCallScriptError(
                    "Wisdom call generation failed: connection error"
                ) from exc
            except WisdomCallScriptError:
                raise
            except Exception as exc:
                logger.exception("wisdom_call generate_script unexpected error")
                raise WisdomCallScriptError(
                    "Wisdom call generation failed unexpectedly"
                ) from exc

        logger.error(
            "wisdom_call generate_script exhausted retries: %s",
            last_error,
        )
        raise WisdomCallScriptError(
            "Wisdom call generation failed after rate-limit retries"
        ) from last_error

    async def create_wisdom_call(
        self,
        user_id: int,
        week_number: int,
    ) -> WeeklyCheckin | None:
        """
        Orchestrate wisdom-call creation and storage for a user/week.

        1. Idempotent: return existing check-in if ``wisdom_call_script`` is set
        2. Load user profile + aggregate context
        3. Call ``generate_script()``
        4. Persist to ``WeeklyCheckin.wisdom_call_script``
        5. Set ``wisdom_call_sent_at`` (``wisdom_call_audio_url`` stays NULL until Phase 5)
        6. Return the check-in row

        Returns ``None`` when the user or weekly check-in is missing, or when
        script generation / persistence fails.
        """
        checkin = (
            WeeklyCheckin.query.filter_by(user_id=user_id, week_number=week_number)
            .first()
        )
        if checkin is None:
            logger.warning(
                "create_wisdom_call: no WeeklyCheckin for user_id=%s week_number=%s",
                user_id,
                week_number,
            )
            return None

        if (checkin.wisdom_call_script or "").strip():
            logger.info(
                "create_wisdom_call: existing script for user_id=%s week_number=%s; skipping",
                user_id,
                week_number,
            )
            return checkin

        user = User.query.get(user_id)
        if user is None:
            logger.warning("create_wisdom_call: user_id=%s not found", user_id)
            return None

        user_profile = self._load_user_profile_for_script(user)
        context = self.aggregate_user_context(user_id, week_number)

        try:
            script = await asyncio.to_thread(
                self.generate_script,
                context,
                user_profile,
            )
        except WisdomCallScriptError:
            logger.exception(
                "create_wisdom_call: script generation failed user_id=%s week_number=%s",
                user_id,
                week_number,
            )
            return None

        if not (script or "").strip():
            logger.error(
                "create_wisdom_call: empty script for user_id=%s week_number=%s",
                user_id,
                week_number,
            )
            return None

        checkin.wisdom_call_script = script.strip()
        checkin.wisdom_call_sent_at = datetime.utcnow()
        # Phase 5 owns audio; leave URL unset here.
        checkin.wisdom_call_audio_url = None

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception(
                "create_wisdom_call: failed to persist user_id=%s week_number=%s",
                user_id,
                week_number,
            )
            return None

        logger.info(
            "create_wisdom_call: saved script for user_id=%s week_number=%s (%s chars)",
            user_id,
            week_number,
            len(checkin.wisdom_call_script or ""),
        )
        return checkin

    @staticmethod
    def _load_user_profile_for_script(user: User) -> dict[str, Any]:
        """Light personalization fields for ``generate_script`` / system prompt."""
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": user.first_name,
            "primary_financial_goal": user.primary_financial_goal,
            "tier": user.tier,
            "email": user.email,
        }

    async def deliver_wisdom_call(
        self,
        user_id: int,
        week_number: int,
    ) -> dict[str, Any]:
        """
        Deliver a stored wisdom-call script via in-app notification + email.

        Intended to be invoked by a Monday 9 AM scheduler. No audio (Phase 5)
        and no SMS — in-app + email only.

        Returns a delivery status dict::

            {"success": True, "in_app": "sent", "email": "sent", "delivered_at": "..."}
        """
        delivered_at = datetime.utcnow()
        delivered_at_iso = delivered_at.isoformat() + "Z"

        def _status(
            *,
            success: bool,
            in_app: str,
            email: str,
            error: str | None = None,
        ) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "success": success,
                "in_app": in_app,
                "email": email,
                "delivered_at": delivered_at_iso if success else None,
            }
            if error:
                payload["error"] = error
            return payload

        checkin = (
            WeeklyCheckin.query.filter_by(user_id=user_id, week_number=week_number)
            .first()
        )
        if checkin is None:
            logger.warning(
                "deliver_wisdom_call: no WeeklyCheckin for user_id=%s week_number=%s",
                user_id,
                week_number,
            )
            return _status(
                success=False,
                in_app="skipped",
                email="skipped",
                error="no_checkin",
            )

        script = (checkin.wisdom_call_script or "").strip()
        if not script:
            logger.warning(
                "deliver_wisdom_call: no script for user_id=%s week_number=%s",
                user_id,
                week_number,
            )
            return _status(
                success=False,
                in_app="skipped",
                email="skipped",
                error="no_script",
            )

        user = User.query.get(user_id)
        if user is None:
            logger.warning("deliver_wisdom_call: user_id=%s not found", user_id)
            return _status(
                success=False,
                in_app="skipped",
                email="skipped",
                error="no_user",
            )

        projections = self._get_financial_projections(user_id, week_number)
        milestones = [
            m for m in (projections.get("milestones") or []) if isinstance(m, dict)
        ]

        in_app_status = await asyncio.to_thread(
            self._deliver_wisdom_in_app,
            user_id,
            week_number,
            script,
        )
        logger.info(
            "deliver_wisdom_call: in_app=%s user_id=%s week_number=%s",
            in_app_status,
            user_id,
            week_number,
        )

        email_status = await asyncio.to_thread(
            self._deliver_wisdom_email,
            user,
            week_number,
            script,
            milestones,
        )
        logger.info(
            "deliver_wisdom_call: email=%s user_id=%s week_number=%s",
            email_status,
            user_id,
            week_number,
        )

        success = in_app_status == "sent" or email_status == "sent"
        if success:
            # Mark as sent to the user when at least one channel succeeds.
            checkin.wisdom_call_sent_at = delivered_at
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                logger.exception(
                    "deliver_wisdom_call: failed to update sent_at user_id=%s week_number=%s",
                    user_id,
                    week_number,
                )

        return _status(
            success=success,
            in_app=in_app_status,
            email=email_status,
            error=None if success else "delivery_failed",
        )

    def _deliver_wisdom_in_app(
        self,
        user_id: int,
        week_number: int,
        script: str,
    ) -> str:
        """Create an in-app notification. Returns ``sent`` or ``failed``."""
        preview = " ".join(script.split())
        if len(preview) > 220:
            preview = preview[:217].rstrip() + "..."

        try:
            note = InAppNotification(
                user_id=user_id,
                title=f"Your Week {week_number} Wisdom Call is ready",
                body=preview,
                category="wisdom_call",
            )
            db.session.add(note)
            db.session.commit()
            return "sent"
        except Exception:
            db.session.rollback()
            logger.exception(
                "deliver_wisdom_call: in-app notification failed user_id=%s week_number=%s",
                user_id,
                week_number,
            )
            return "failed"

    def _deliver_wisdom_email(
        self,
        user: User,
        week_number: int,
        script: str,
        milestones: list[dict[str, Any]],
    ) -> str:
        """Email the script + milestone snapshot. Returns sent/failed/skipped."""
        to_email = (user.email or "").strip()
        if not to_email:
            logger.warning(
                "deliver_wisdom_call: no email for user_id=%s; skipping email",
                user.id,
            )
            return "skipped"

        first_name = (user.first_name or "").strip() or (
            to_email.split("@")[0] if to_email else "there"
        )
        dashboard_url = _wisdom_call_dashboard_url(week_number)
        milestone_rows = _milestone_email_rows(milestones[:3])
        email_ctx = {
            "user_name": first_name,
            "week_number": week_number,
            "script": script,
            "milestones": milestone_rows,
            "dashboard_url": dashboard_url,
        }
        html_body = _render_wisdom_call_email(email_ctx)
        text_body = _render_wisdom_call_text_email(email_ctx)

        try:
            ok = EmailService().send_email(
                to=to_email,
                subject=f"Your Mingus Wisdom Call — Week {week_number}",
                html_body=html_body,
                text_body=text_body,
            )
        except Exception:
            logger.exception(
                "deliver_wisdom_call: email exception user_id=%s week_number=%s",
                user.id,
                week_number,
            )
            return "failed"

        if not ok:
            logger.warning(
                "deliver_wisdom_call: email service returned False user_id=%s week_number=%s",
                user.id,
                week_number,
            )
            return "failed"
        return "sent"

    def _validate_script(
        self,
        script: str,
        context: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        Quality-gate a generated wisdom-call script.

        Returns ``(is_valid, errors)``. Hard failures set ``is_valid=False``;
        soft warnings are included in ``errors`` but do not alone invalidate.
        Callers should log and decide whether to use, regenerate, or fall back.
        """
        hard: list[str] = []
        soft: list[str] = []
        text = (script or "").strip()
        lower = text.lower()
        words = re.findall(r"[A-Za-z']+", text)
        word_count = len(words)

        # --- HARD FAIL ---
        if word_count < 200:
            hard.append(f"word_count_too_low:{word_count}")
        elif word_count > 2000:
            hard.append(f"word_count_too_high:{word_count}")

        if not re.search(r"\byou\b", lower):
            hard.append("missing_user_addressing")

        known_numbers, known_dates = _collect_context_facts(context)
        invented = _find_invented_facts(text, known_numbers, known_dates)
        hard.extend(invented)

        # --- Projection checks (hard when milestones exist) ---
        projections = context.get("financial_projections") or {}
        milestones = [
            m
            for m in (projections.get("milestones") or [])
            if isinstance(m, dict) and m.get("status") not in (None, "no_data")
        ]
        if milestones:
            mentioned = [
                m
                for m in milestones
                if (m.get("name") or "").lower() in lower
                or _milestone_alias_mentioned(m, lower)
            ]
            if not mentioned:
                hard.append("projections_not_referenced")
            else:
                # At least one milestone projection mentioned with a specific date.
                date_ok = False
                for m in mentioned:
                    for key in ("projected_date", "target_date"):
                        raw = m.get(key)
                        if raw and _date_mentioned_in_script(str(raw), text):
                            date_ok = True
                            break
                    if date_ok:
                        break
                # Also accept any ISO / Month Day style date near projection language.
                if not date_ok and not _script_has_specific_date(text):
                    hard.append("projections_missing_specific_dates")
                elif not date_ok:
                    soft.append("projection_dates_not_tied_to_milestone")

            contradictions = _find_projection_contradictions(text, milestones)
            hard.extend(contradictions)

        # --- SOFT WARN ---
        generic_phrases = (
            "keep up the good work",
            "stay positive",
            "you've got this",
            "things will get better",
            "hang in there",
        )
        if any(p in lower for p in generic_phrases) and word_count < 400:
            soft.append("generic_tone")

        section_flags = {
            "wellness": bool((context.get("wellness") or {}).get("has_data")),
            "spending": bool((context.get("spending") or {}).get("has_data")),
            "todos": bool((context.get("todos") or {}).get("has_data")),
            "goals": bool((context.get("goals") or {}).get("has_data")),
            "relationships": bool((context.get("relationships") or {}).get("has_data")),
            "career": bool((context.get("career") or {}).get("has_data")),
        }
        section_keywords = {
            "wellness": ("mood", "stress", "sleep", "wellness"),
            "spending": ("spend", "spending", "baseline", "impulse"),
            "todos": ("task", "todo", "to-do", "overdue"),
            "goals": ("goal", "win", "progress"),
            "relationships": ("partner", "relationship", "family"),
            "career": ("career", "job", "income", "salary", "role"),
        }
        for section, has_data in section_flags.items():
            if not has_data:
                continue
            if not any(k in lower for k in section_keywords[section]):
                soft.append(f"missing_data_source:{section}")

        temporal_cues = (
            "this week",
            "last week",
            "week ",
            "today",
            "tomorrow",
            "by ",
            "days",
            "month",
        )
        if not any(cue in lower for cue in temporal_cues):
            soft.append("weak_temporal_context")

        errors = [f"HARD:{e}" for e in hard] + [f"SOFT:{e}" for e in soft]
        is_valid = len(hard) == 0
        return is_valid, errors

    def _enhance_script_with_projections(
        self,
        script: str,
        projections: dict[str, Any] | list[dict[str, Any]] | None,
    ) -> str:
        """
        Make financial projections in the script more vivid and concrete.

        Accepts the full ``financial_projections`` payload (preferred) or a bare
        milestones list. Called before validation so the script includes specific
        dates, rates, and shortfall actions.
        """
        if not script:
            return ""

        milestones, default_weekly_rate = _normalize_projections_arg(projections)
        if not milestones:
            return script

        enhanced = script
        today = date.today()

        for milestone in milestones:
            name = (milestone.get("name") or "").strip()
            if not name:
                continue
            status = (milestone.get("status") or "").strip().lower()
            if status in ("", "no_data"):
                continue

            # Skip if already has concrete projection language for this milestone.
            if _milestone_already_concrete(enhanced, milestone):
                continue

            vivid = _build_vivid_projection_sentence(
                milestone,
                default_weekly_rate=default_weekly_rate,
                today=today,
            )
            if not vivid:
                continue

            enhanced2 = _inject_vivid_projection(enhanced, name, status, vivid)
            enhanced = enhanced2

        return enhanced


def _wisdom_call_app_url() -> str:
    return os.environ.get("PUBLIC_APP_URL", "https://mingusapp.com").rstrip("/")


def _wisdom_call_dashboard_url(week_number: int) -> str:
    return f"{_wisdom_call_app_url()}/dashboard/wisdom/{int(week_number)}"


def _wisdom_email_template_dir() -> str:
    return os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "templates", "email")
    )


def _wisdom_email_env(*, autoescape: bool) -> Environment:
    return Environment(
        loader=FileSystemLoader(_wisdom_email_template_dir()),
        autoescape=select_autoescape(["html", "xml"]) if autoescape else False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _render_wisdom_call_email(ctx: dict[str, Any]) -> str:
    return _wisdom_email_env(autoescape=True).get_template("wisdom_call.html").render(
        **ctx
    )


def _render_wisdom_call_text_email(ctx: dict[str, Any]) -> str:
    return (
        _wisdom_email_env(autoescape=False)
        .get_template("wisdom_call_text_email.html")
        .render(**ctx)
        .strip()
        + "\n"
    )


def _email_money_label(value: Any) -> str:
    amount = _coerce_float(value)
    if amount is None:
        return "—"
    return f"${amount:,.0f}"


def _friendly_date_with_year(value: Any) -> str | None:
    d = _parse_iso_date(value)
    if d is None:
        return None
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def _weeks_away_label(projected_date: Any, today: date | None = None) -> str | None:
    p_d = _parse_iso_date(projected_date)
    if p_d is None:
        return None
    today = today or date.today()
    days = (p_d - today).days
    if days < 0:
        return None
    weeks = max(0, int(round(days / 7)))
    if weeks == 0:
        return "this week"
    if weeks == 1:
        return "1 week away"
    return f"{weeks} weeks away"


def _milestone_projected_line(
    milestone: dict[str, Any],
    *,
    today: date | None = None,
) -> str:
    status = (milestone.get("status") or "").strip().lower()
    projected = _friendly_date_with_year(
        _milestone_field(milestone, "projected_date")
    )
    target = _friendly_date_with_year(_milestone_field(milestone, "target_date"))
    weeks_away = _weeks_away_label(
        _milestone_field(milestone, "projected_date"), today=today
    )

    if not projected:
        if status == "on_track":
            return "On track! ✓"
        if status == "ahead":
            return "Ahead of schedule 🎯"
        if status == "behind":
            return "Behind target — needs focus"
        return "Projection coming soon"

    if status in ("on_track", "ahead"):
        suffix = f" ({weeks_away}!)" if weeks_away else ""
        mark = " ✓" if status == "on_track" else " 🎯"
        return f"Projected: {projected}{suffix}{mark}"

    if status == "behind":
        if target:
            return f"Projected: {projected} (Behind target of {target})"
        return f"Projected: {projected} (Behind target)"

    return f"Projected: {projected}"


def _milestone_shortfall_message(milestone: dict[str, Any]) -> str | None:
    status = (milestone.get("status") or "").strip().lower()
    if status != "behind":
        return None
    weekly_need = _coerce_float(_milestone_field(milestone, "weekly_need"))
    if not weekly_need or weekly_need <= 0:
        return None
    target = _friendly_date_with_year(_milestone_field(milestone, "target_date"))
    if target:
        # Prefer short month form for the shortfall line.
        d = _parse_iso_date(_milestone_field(milestone, "target_date"))
        short = f"{d.strftime('%b')} {d.day}, {d.year}" if d else target
        return f"Need to save ${weekly_need:,.0f}/week extra to hit {short}"
    return f"Need to save ${weekly_need:,.0f}/week extra"


def _milestone_email_rows(milestones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build scannable milestone rows for HTML + text wisdom-call emails."""
    today = date.today()
    status_meta = {
        "on_track": ("On Track ✓", "#15803d", "#dcfce7"),
        "ahead": ("Ahead 🎯", "#15803d", "#dcfce7"),
        "behind": ("Behind ⚠️", "#a16207", "#fef9c3"),
        "no_data": ("Needs data", "#64748b", "#f1f5f9"),
    }
    rows: list[dict[str, Any]] = []
    for m in milestones:
        if not isinstance(m, dict):
            continue
        name = (m.get("name") or "Milestone").strip() or "Milestone"
        status = (m.get("status") or "").strip().lower() or "no_data"
        status_label, status_color, status_bg = status_meta.get(
            status, ("Update", "#64748b", "#f1f5f9")
        )
        current = _milestone_field(m, "current_balance", "current")
        target = _milestone_field(m, "target_amount", "target")
        current_f = _coerce_float(current)
        target_f = _coerce_float(target)
        progress_text = None
        if current_f is not None and target_f is not None and target_f > 0:
            pct = max(0.0, min(100.0, (current_f / target_f) * 100.0))
            progress_text = f"{pct:.0f}% to target"

        rows.append(
            {
                "name": name,
                "status": status,
                "status_label": status_label,
                "status_color": status_color,
                "status_bg": status_bg,
                "current_label": _email_money_label(current),
                "target_label": _email_money_label(target),
                "progress_text": progress_text,
                "projected_line": _milestone_projected_line(m, today=today),
                "shortfall_message": _milestone_shortfall_message(m),
                # Keep summary for any older callers.
                "summary": _milestone_email_summary(m),
            }
        )
    return rows


def _milestone_email_summary(milestone: dict[str, Any]) -> str:
    target = _milestone_field(milestone, "target_amount", "target")
    current = _milestone_field(milestone, "current_balance", "current")
    projected = _friendly_date_with_year(
        _milestone_field(milestone, "projected_date")
    )
    target_date = _friendly_date_with_year(_milestone_field(milestone, "target_date"))
    weekly_need = _coerce_float(_milestone_field(milestone, "weekly_need"))
    status = (milestone.get("status") or "").strip().lower()

    parts: list[str] = []
    if target is not None:
        try:
            parts.append(f"Target ${float(target):,.0f}")
        except (TypeError, ValueError):
            pass
    if current is not None:
        try:
            parts.append(f"now at ${float(current):,.0f}")
        except (TypeError, ValueError):
            pass
    if target_date:
        parts.append(f"goal date {target_date}")
    if projected:
        verb = "projected" if status != "behind" else "currently projected"
        parts.append(f"{verb} {projected}")
    if status == "behind" and weekly_need and weekly_need > 0:
        parts.append(f"need ${weekly_need:,.0f} more per week")

    return " · ".join(parts) if parts else "Progress update available in the app."


def _normalize_projections_arg(
    projections: dict[str, Any] | list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], float | None]:
    if projections is None:
        return [], None
    if isinstance(projections, list):
        return [m for m in projections if isinstance(m, dict)], None
    if not isinstance(projections, dict):
        return [], None
    milestones = [
        m for m in (projections.get("milestones") or []) if isinstance(m, dict)
    ]
    rate = _coerce_float(projections.get("weekly_saving_rate"))
    return milestones, rate


def _milestone_field(milestone: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in milestone and milestone.get(key) is not None:
            return milestone.get(key)
    return None


def _milestone_already_concrete(script: str, milestone: dict[str, Any]) -> bool:
    """True if script already cites projected/target date near this milestone."""
    lower = script.lower()
    name = (milestone.get("name") or "").lower()
    if name not in lower and not _milestone_alias_mentioned(milestone, lower):
        return False
    for key in ("projected_date", "target_date"):
        raw = milestone.get(key)
        if raw and _date_mentioned_in_script(str(raw), script):
            return True
    # Concrete rate / shortfall language already present.
    if re.search(r"\$\d[\d,]*/\s*week", script, flags=re.IGNORECASE):
        if name in lower or _milestone_alias_mentioned(milestone, lower):
            return True
    return False


def _build_vivid_projection_sentence(
    milestone: dict[str, Any],
    *,
    default_weekly_rate: float | None,
    today: date,
) -> str:
    name = (milestone.get("name") or "Your goal").strip()
    status = (milestone.get("status") or "").strip().lower()
    target_amount = _coerce_float(
        _milestone_field(milestone, "target_amount", "target")
    )
    current = _coerce_float(
        _milestone_field(milestone, "current_balance", "current")
    )
    target_date = _milestone_field(milestone, "target_date")
    projected_date = _milestone_field(milestone, "projected_date")
    weekly_need = _coerce_float(milestone.get("weekly_need"))
    shortfall = _coerce_float(
        _milestone_field(milestone, "shortfall_amount", "shortfall")
    )
    weekly_rate = _coerce_float(
        _milestone_field(milestone, "weekly_saving_rate", "weekly_rate")
    )
    if weekly_rate is None:
        weekly_rate = default_weekly_rate

    target_friendly = _friendly_date_str(target_date)
    projected_friendly = _friendly_date_str(projected_date)
    projected_month_year = _friendly_month_year(projected_date)
    amount_label = (
        f"${target_amount:,.0f}" if target_amount is not None else "your goal"
    )

    if status == "behind":
        late_bit = ""
        t_d = _parse_iso_date(target_date)
        p_d = _parse_iso_date(projected_date)
        if t_d and p_d and p_d > t_d:
            # Approximate months late for copy.
            months_late = max(1, int(round((p_d - t_d).days / 30.44)))
            late_bit = f"—{months_late} month{'s' if months_late != 1 else ''} late"

        parts = [
            f"Your {name.lower()} target is {amount_label}"
            + (f" by {target_friendly}" if target_friendly else "")
            + "."
        ]
        if current is not None:
            parts.append(f"Right now, you're at ${current:,.0f}.")
        if projected_friendly or projected_month_year:
            hit = projected_month_year or projected_friendly
            parts.append(
                f"At your current savings rate, you won't hit it until {hit}"
                + (f"{late_bit}." if late_bit else ".")
            )
        if weekly_need and weekly_need > 0:
            parts.append(
                f"To make your deadline, you need to save ${weekly_need:,.0f} more per week."
            )
            parts.append("That's doable, but it requires focus.")
        elif shortfall and shortfall > 0:
            parts.append(
                f"You need about ${shortfall:,.0f} more to finish on time."
            )
        return " ".join(parts)

    if status in ("on_track", "ahead"):
        weeks_away = None
        p_d = _parse_iso_date(projected_date)
        if p_d:
            days_until = (p_d - today).days
            if days_until >= 0:
                weeks_away = max(0, int(round(days_until / 7)))

        rate_bit = (
            f"At your current rate of ${weekly_rate:,.0f}/week, "
            if weekly_rate and weekly_rate > 0
            else "At your current rate, "
        )
        hit_bit = (
            f"you'll hit your {amount_label} goal by {projected_friendly}."
            if projected_friendly
            else f"you'll hit your {amount_label} goal."
        )
        close_bit = ""
        if weeks_away is not None:
            if weeks_away == 0:
                close_bit = " That's this week."
            elif weeks_away == 1:
                close_bit = " That's just 1 week away."
            else:
                close_bit = f" That's just {weeks_away} weeks away."

        if status == "ahead":
            t_d = _parse_iso_date(target_date)
            if t_d and p_d and (t_d - p_d).days > 0:
                close_bit = (
                    f" That's {(t_d - p_d).days} days early — keep the momentum going."
                )

        return f"{rate_bit}{hit_bit}{close_bit}".strip()

    message = (milestone.get("message") or "").strip()
    return message


def _friendly_month_year(value: Any) -> str | None:
    d = _parse_iso_date(value)
    if d is None:
        return None
    return f"{d.strftime('%B')} {d.year}"


def _inject_vivid_projection(
    script: str,
    name: str,
    status: str,
    vivid: str,
) -> str:
    """
    Inject vivid projection copy near the first milestone mention.

    - behind: replace the mentioning sentence with the vivid paragraph
    - on_track/ahead: append vivid sentence after the mentioning sentence
    - if not mentioned: append a short projection paragraph at the end
    """
    # Sentence split (keep delimiters).
    parts = re.split(r"(?<=[.!?])\s+", script.strip())
    name_l = name.lower()
    mention_idx = None
    for i, sentence in enumerate(parts):
        s_l = sentence.lower()
        if name_l in s_l or _milestone_alias_mentioned({"name": name}, s_l):
            mention_idx = i
            break

    if mention_idx is None:
        # No mention yet — append a concrete projection block before validation.
        joiner = "" if script.rstrip().endswith((".", "!", "?")) else "."
        return f"{script.rstrip()}{joiner} {vivid}".strip()

    if status == "behind":
        parts[mention_idx] = vivid
        return " ".join(p.strip() for p in parts if p.strip())

    # on_track / ahead: keep original sentence, append concrete follow-up.
    original = parts[mention_idx].rstrip()
    if not original.endswith((".", "!", "?")):
        original += "."
    # Avoid duplicating if vivid already glued somehow.
    if vivid.lower() in original.lower():
        return script
    parts[mention_idx] = f"{original} {vivid}"
    return " ".join(p.strip() for p in parts if p.strip())


def _parse_iso_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _friendly_date_str(value: Any) -> str | None:
    d = _parse_iso_date(value)
    if d is None:
        return None
    return f"{d.strftime('%B')} {d.day}"


def _collect_context_facts(
    context: dict[str, Any],
) -> tuple[set[str], set[str]]:
    """Collect normalized number/date tokens present in the aggregated context."""
    numbers: set[str] = set()
    dates: set[str] = set()

    def walk(obj: Any) -> None:
        if obj is None:
            return
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
            return
        if isinstance(obj, (list, tuple)):
            for v in obj:
                walk(v)
            return
        if isinstance(obj, bool):
            return
        if isinstance(obj, (int, float)):
            numbers.add(_normalize_number_token(obj))
            return
        if isinstance(obj, (date, datetime)):
            d = obj.date() if isinstance(obj, datetime) else obj
            dates.add(d.isoformat())
            dates.add(_friendly_date_str(d) or "")
            return
        s = str(obj)
        for m in re.findall(r"\d{4}-\d{2}-\d{2}", s):
            dates.add(m)
            dates.add(_friendly_date_str(m) or "")
        for m in re.findall(r"\$?\d[\d,]*(?:\.\d+)?", s):
            numbers.add(_normalize_number_token(m))

    walk(context)
    dates.discard("")
    numbers.discard("")
    return numbers, dates


def _normalize_number_token(value: Any) -> str:
    s = str(value).replace("$", "").replace(",", "").strip()
    try:
        f = float(s)
        if abs(f - round(f)) < 1e-9:
            return str(int(round(f)))
        return f"{f:.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return s


def _find_invented_facts(
    script: str,
    known_numbers: set[str],
    known_dates: set[str],
) -> list[str]:
    """
    Flag script dates/amounts that do not appear in context.

    Conservative: only hard-fail on ISO dates and $-prefixed amounts with no
    nearby known match. Bare integers are ignored (too many false positives).
    """
    issues: list[str] = []
    known_dates_l = {d.lower() for d in known_dates if d}
    known_nums = set(known_numbers)

    for iso in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", script):
        if iso not in known_dates and iso.lower() not in known_dates_l:
            issues.append(f"invented_date:{iso}")

    # Month Day / Month Day, Year
    for mon, day in re.findall(
        r"\b(January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+(\d{1,2})\b",
        script,
        flags=re.IGNORECASE,
    ):
        friendly = f"{mon.capitalize()} {int(day)}"
        if friendly.lower() not in known_dates_l and not any(
            friendly.lower() in kd for kd in known_dates_l
        ):
            # Allow if any known date shares month+day.
            matched = False
            for kd in known_dates:
                d = _parse_iso_date(kd)
                if d and d.strftime("%B").lower() == mon.lower() and d.day == int(day):
                    matched = True
                    break
            if not matched:
                issues.append(f"invented_date:{friendly}")

    for raw in re.findall(r"\$\d[\d,]*(?:\.\d+)?", script):
        token = _normalize_number_token(raw)
        if token and token not in known_nums:
            # Allow K-style rounding of known thousands.
            try:
                val = float(token)
            except ValueError:
                issues.append(f"invented_amount:{raw}")
                continue
            nearby = False
            for kn in known_nums:
                try:
                    known_v = float(kn)
                except ValueError:
                    continue
                if known_v <= 0:
                    continue
                if abs(known_v - val) <= max(1.0, known_v * 0.02):
                    nearby = True
                    break
                # $5K style vs 5000
                if abs(known_v / 1000.0 - val) < 0.05 or abs(val / 1000.0 - known_v) < 0.05:
                    nearby = True
                    break
            if not nearby:
                issues.append(f"invented_amount:{raw}")

    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for item in issues:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _milestone_alias_mentioned(milestone: dict[str, Any], lower_script: str) -> bool:
    name = (milestone.get("name") or "").lower()
    aliases = {
        "emergency fund": ("emergency fund", "ef", "rainy day"),
        "down payment": ("down payment", "home purchase", "house fund"),
        "debt payoff": ("debt payoff", "debt-free", "pay off debt", "debt free"),
    }
    for key, words in aliases.items():
        if key in name and any(w in lower_script for w in words):
            return True
    return False


def _date_mentioned_in_script(raw_date: str, script: str) -> bool:
    d = _parse_iso_date(raw_date)
    if d is None:
        return False
    lower = script.lower()
    if d.isoformat() in script:
        return True
    friendly = _friendly_date_str(d)
    if friendly and friendly.lower() in lower:
        return True
    # "March 15th"
    ordinal = f"{d.strftime('%B').lower()} {d.day}"
    if ordinal in lower:
        return True
    if f"{ordinal}th" in lower or f"{ordinal}st" in lower or f"{ordinal}nd" in lower or f"{ordinal}rd" in lower:
        return True
    return False


def _script_has_specific_date(script: str) -> bool:
    if re.search(r"\b\d{4}-\d{2}-\d{2}\b", script):
        return True
    return bool(
        re.search(
            r"\b(January|February|March|April|May|June|July|August|September|"
            r"October|November|December)\s+\d{1,2}(st|nd|rd|th)?\b",
            script,
            flags=re.IGNORECASE,
        )
    )


def _find_projection_contradictions(
    script: str,
    milestones: list[dict[str, Any]],
) -> list[str]:
    """Detect 'hit target / on track' language conflicting with behind milestones."""
    lower = script.lower()
    issues: list[str] = []
    hit_phrases = (
        "you'll hit",
        "you will hit",
        "on track",
        "right on track",
        "crushing it",
        "ahead of schedule",
        "ahead of your",
    )
    behind_phrases = (
        "behind",
        "falling behind",
        "won't hit",
        "will not hit",
        "off track",
        "late",
        "need to save",
        "need an extra",
    )

    for m in milestones:
        name = (m.get("name") or "").strip()
        status = (m.get("status") or "").lower()
        if not name:
            continue
        # Window: sentences mentioning the milestone (or whole script if short name hit).
        if name.lower() not in lower and not _milestone_alias_mentioned(m, lower):
            continue

        # Extract rough local context around the name.
        idx = lower.find(name.lower())
        if idx < 0:
            # alias path — use full script
            window = lower
        else:
            start = max(0, idx - 160)
            end = min(len(lower), idx + len(name) + 220)
            window = lower[start:end]

        if status == "behind":
            if any(p in window for p in hit_phrases) and not any(
                p in window for p in behind_phrases
            ):
                issues.append(f"projection_contradiction:{name}:behind_vs_on_track_language")
        elif status in ("ahead", "on_track"):
            if any(p in window for p in ("falling behind", "won't hit", "off track")) and not any(
                p in window for p in ("on track", "ahead", "crushing", "you'll hit", "you will hit")
            ):
                issues.append(f"projection_contradiction:{name}:{status}_vs_behind_language")

    return issues


def _rate_limit_wait_seconds(exc: Exception, attempt: int) -> float:
    """Prefer Retry-After when present; otherwise exponential backoff."""
    headers = getattr(exc, "headers", None) or {}
    retry_after = None
    if isinstance(headers, dict):
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
    else:
        try:
            retry_after = headers.get("retry-after")  # type: ignore[attr-defined]
        except Exception:
            retry_after = None
    if retry_after is not None:
        try:
            return max(1.0, float(retry_after))
        except (TypeError, ValueError):
            pass
    return float(min(2 ** attempt, 30))


def _metric_line(metrics: dict[str, Any], key: str, *, label: str, suffix: str = "") -> str:
    info = (metrics or {}).get(key) or {}
    value = info.get("value")
    previous = info.get("previous")
    trend = info.get("trend") or "unknown"
    value_s = f"{value}{suffix}" if value is not None else "N/A"
    prev_s = f"{previous}{suffix}" if previous is not None else "N/A"
    return f"{label}: {value_s} (last week: {prev_s}, trend: {trend})"


def _format_wellness_section(wellness: dict[str, Any]) -> str:
    if not wellness.get("has_data"):
        return "EMOTIONAL STATE\nNo wellness check-in data this week."

    metrics = wellness.get("metrics") or {}
    averages = wellness.get("averages") or {}
    mood = (metrics.get("mood_rating") or {}).get("value")
    stress = (metrics.get("stress_level") or {}).get("value")
    if mood is not None and stress is not None:
        if mood >= 7 and stress <= 4:
            vibe = "strong"
        elif mood <= 4 or stress >= 7:
            vibe = "strained"
        else:
            vibe = "baseline"
    else:
        vibe = "baseline"

    sleep = (metrics.get("avg_sleep_hours") or metrics.get("sleep_hours") or {}).get("value")
    activity = (metrics.get("activity_frequency") or {}).get("value")
    lines = [
        "EMOTIONAL STATE",
        _metric_line(metrics, "mood_rating", label="Mood", suffix="/10"),
        _metric_line(metrics, "stress_level", label="Stress", suffix="/10"),
        f"Sleep: {sleep if sleep is not None else 'N/A'} hrs/night",
        f"Activity: {activity if activity is not None else 'N/A'} times/week",
        f"Overall vibe: {vibe}",
    ]
    if averages:
        avg_bits = [
            f"{k}={v}" for k, v in averages.items() if v is not None
        ]
        if avg_bits:
            lines.append(f"Recent averages: {', '.join(avg_bits)}")
    return "\n".join(lines)


def _format_todos_section(todos: dict[str, Any]) -> str:
    counts = todos.get("counts") or {}
    total = int(counts.get("total") or 0)
    completed = int(counts.get("completed") or 0)
    overdue = int(counts.get("overdue") or 0)
    open_n = int(counts.get("open") or 0)
    pct = (completed / total * 100.0) if total > 0 else 0.0

    domain_lines: list[str] = []
    for domain, data in (todos.get("by_domain") or {}).items():
        if not isinstance(data, dict):
            continue
        domain_lines.append(
            f"  {domain}: {data.get('completed', 0)}/{data.get('total', 0)} done"
            f" ({data.get('overdue', 0)} overdue)"
        )

    lines = [
        "TASK PROGRESS",
        f"Completed: {completed}/{total} ({pct:.0f}%)",
        f"Open: {open_n} | Overdue: {overdue}",
    ]
    if domain_lines:
        lines.append("By domain:")
        lines.extend(domain_lines)
    elif not todos.get("has_data"):
        lines.append("No todos recorded.")
    return "\n".join(lines)


def _format_spending_section(spending: dict[str, Any]) -> str:
    if not spending.get("has_data"):
        return "SPENDING PATTERNS\nNo spending signal data this week."

    delta = spending.get("delta") or {}
    pct = delta.get("percent")
    amount = delta.get("amount")
    pct_s = f"{pct:+.1f}%" if pct is not None else "N/A"
    amount_s = f"${amount:+,.0f}" if amount is not None else "N/A"
    unusual = bool(spending.get("unusual_spending_detected"))
    patterns = spending.get("patterns") or []
    pattern_labels = [
        (p.get("label") or p.get("id") or str(p))
        for p in patterns
        if isinstance(p, dict)
    ]
    spikes = spending.get("spikes") or []
    spike_names = [
        (s.get("name") or s.get("category") or "")
        for s in spikes[:2]
        if isinstance(s, dict)
    ]

    lines = [
        "SPENDING PATTERNS",
        f"This week vs baseline: {pct_s}",
        f"Amount: {amount_s}",
        f"Status: {'SPIKE - unusual spending detected' if unusual else 'Normal'}",
        f"Patterns detected: {', '.join(pattern_labels) if pattern_labels else 'None'}",
        f"Top spike categories: {', '.join(n for n in spike_names if n) or 'None'}",
    ]
    return "\n".join(lines)


def _format_projections_section(projections: dict[str, Any]) -> str:
    milestones = projections.get("milestones") or []
    lines = ["FINANCIAL MILESTONES & PROJECTIONS"]
    if not milestones:
        lines.append("No projection data.")
    else:
        for m in milestones:
            if not isinstance(m, dict):
                continue
            name = m.get("name") or "Milestone"
            current = m.get("current_balance")
            target = m.get("target_amount")
            status = (m.get("status") or "unknown").upper()
            current_s = f"${current:,.0f}" if current is not None else "N/A"
            target_s = f"${target:,.0f}" if target is not None else "N/A"
            lines.append(f"  • {name}: {current_s}/{target_s} ({status})")
            lines.append(
                f"    Target: {m.get('target_date') or 'N/A'} | "
                f"Projected: {m.get('projected_date') or 'N/A'}"
            )
            if m.get("weekly_saving_rate") is not None:
                lines.append(f"    Weekly rate: ${m['weekly_saving_rate']:,.0f}")
            if m.get("weekly_need"):
                lines.append(
                    f"    Extra needed: ${m['weekly_need']:,.0f}/week "
                    f"(shortfall ${m.get('shortfall_amount') or 0:,.0f})"
                )
            if m.get("motivational"):
                lines.append(f"    Motivational: {m['motivational']}")
            if m.get("message"):
                lines.append(f"    {m['message']}")
    lines.append(
        f"Summary: {projections.get('total_projection_summary') or 'No projection data'}"
    )
    return "\n".join(lines)


def _format_goals_section(goals: dict[str, Any]) -> str:
    wins_raw = goals.get("wins") or []
    win_texts: list[str] = []
    for w in wins_raw:
        if isinstance(w, dict):
            text = (w.get("text") or "").strip()
            if text:
                win_texts.append(text)
        elif w:
            win_texts.append(str(w))
    wins_s = "; ".join(win_texts[:5]) if win_texts else "No recent wins recorded"

    progress = goals.get("average_progress_pct")
    progress_s = f"{progress:.0f}%" if progress is not None else "N/A"
    on_track = goals.get("on_track")
    if on_track is True:
        status = "On track overall"
    elif on_track is False:
        status = "Some goals need attention"
    else:
        status = "Goal status unclear / incomplete data"

    goal_lines: list[str] = []
    for g in (goals.get("goals") or [])[:4]:
        if not isinstance(g, dict):
            continue
        title = g.get("title") or "Goal"
        pct = g.get("progress_pct")
        pct_s = f"{pct:.0f}%" if pct is not None else "N/A"
        track = g.get("on_track")
        track_s = (
            "on_track" if track is True else "off_track" if track is False else "unknown"
        )
        goal_lines.append(f"  • {title}: {pct_s} ({track_s})")

    lines = [
        "GOALS & WINS",
        f"Recent wins: {wins_s}",
        f"Overall progress: {progress_s}",
        f"Status: {status}",
    ]
    if goal_lines:
        lines.append("Active goals:")
        lines.extend(goal_lines)
    return "\n".join(lines)


def _format_relationships_section(relationships: dict[str, Any]) -> str:
    if not relationships.get("has_data"):
        return "RELATIONSHIPS\nNo relationship data available."

    health = relationships.get("overall_health")
    health_s = f"{health:.1f}/10" if health is not None else "N/A"
    partner = relationships.get("partner") or {}
    partner_name = partner.get("nickname") or partner.get("name") or "No partner data"
    partner_rating = (
        partner.get("checkin_rating")
        or partner.get("emotional_score")
        or partner.get("rating")
    )
    if partner_rating is not None and float(partner_rating) > 10:
        partner_rating_s = f"{float(partner_rating):.0f}/100 vibe"
    elif partner_rating is not None:
        partner_rating_s = f"{float(partner_rating):.0f}/10"
    else:
        partner_rating_s = "N/A"

    counts = relationships.get("counts") or {}
    connections = counts.get("connections") or counts.get("total_connections") or 0
    family_n = counts.get("family") or 0
    events_n = counts.get("upcoming_events") or 0

    summary = (relationships.get("changes") or {}).get("summary") or {}
    improving = summary.get("improving") or []
    declining = summary.get("declining") or []

    event_bits: list[str] = []
    for ev in (relationships.get("events") or [])[:3]:
        if isinstance(ev, dict) and ev.get("name"):
            event_bits.append(
                f"{ev.get('name')} in {ev.get('days_until', '?')}d"
            )

    lines = [
        "RELATIONSHIPS",
        f"Overall health: {health_s}",
        f"Partner: {partner_name} ({partner_rating_s})",
        f"Family: {family_n} | Close connections: {connections}",
        f"Improving: {', '.join(improving) if improving else 'None'}",
        f"Declining: {', '.join(declining) if declining else 'None'}",
    ]
    if event_bits:
        lines.append(f"Upcoming events: {', '.join(event_bits)} ({events_n} total)")
    return "\n".join(lines)


def _format_career_section(career: dict[str, Any]) -> str:
    if not career.get("has_data"):
        return "CAREER\nNo career data available."

    profile = career.get("profile") or {}
    # Support both our shape (profile.current_role string) and nested current_role dict.
    current_role = career.get("current_role")
    if isinstance(current_role, dict):
        role_title = current_role.get("title") or "Unknown"
        company = current_role.get("company") or "Unknown"
    else:
        role_title = profile.get("current_role") or current_role or "Unknown"
        company = profile.get("employer_name") or "Unknown"

    income = career.get("income") or {}
    annual = income.get("annual")
    annual_s = f"${annual:,.0f}/year" if annual is not None else "N/A"

    percentile = career.get("percentile") or {}
    pct_val = percentile.get("value")
    pct_s = f"{pct_val}th percentile" if pct_val is not None else "N/A"
    above = percentile.get("above_median")
    median_s = (
        "above median" if above is True else "below median" if above is False else "median unknown"
    )

    gaps = career.get("gaps") or []
    gap0 = gaps[0] if gaps and isinstance(gaps[0], dict) else {}
    gap_amount = gap0.get("amount") or gap0.get("gap")
    gap_label = gap0.get("label") or "Income gap"
    gap_s = f"${gap_amount:+,.0f}" if gap_amount is not None else "N/A"

    opps = career.get("opportunities") or []
    if isinstance(opps, dict):
        signals = opps.get("signals") or []
        opp_labels = [str(s) for s in signals]
    else:
        opp_labels = [
            (o.get("label") or o.get("id") or str(o))
            for o in opps
            if isinstance(o, dict)
        ][:5]

    lines = [
        "CAREER",
        f"Role: {role_title}",
        f"Company: {company}",
        f"Income: {annual_s}",
        f"Market position: {pct_s} ({median_s})",
        f"{gap_label}: {gap_s}",
        f"Opportunities: {', '.join(opp_labels) if opp_labels else 'None flagged'}",
    ]
    return "\n".join(lines)


def _estimate_weekly_saving_rate(user_id: int) -> float | None:
    """Average weekly savings from snapshots, HPRS surplus, or check-in underspend."""
    snapshots = (
        LifeScoreSnapshot.query.filter(
            LifeScoreSnapshot.user_id == user_id,
            LifeScoreSnapshot.monthly_savings_rate.isnot(None),
        )
        .order_by(LifeScoreSnapshot.snapshot_date.desc())
        .limit(_PROJECTION_LOOKBACK_WEEKS)
        .all()
    )
    rates = [
        _coerce_float(s.monthly_savings_rate)
        for s in snapshots
        if _coerce_float(s.monthly_savings_rate) is not None
    ]
    if rates:
        monthly_avg = sum(rates) / len(rates)
        if monthly_avg > 0:
            return round(monthly_avg / _WEEKS_PER_MONTH, 2)

    hprs = get_hprs_inputs(user_id)
    income = _coerce_float(hprs.get("gross_monthly_income"))
    obligations = _coerce_float(hprs.get("total_monthly_obligations"))
    if income is not None and obligations is not None:
        surplus = income - obligations
        if surplus > 0:
            return round(surplus / _WEEKS_PER_MONTH, 2)

    # Last 8 check-ins: treat spend below baseline as implied weekly savings.
    checkins = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .order_by(desc(WeeklyCheckin.week_ending_date))
        .limit(_PROJECTION_LOOKBACK_WEEKS)
        .all()
    )
    baseline = UserSpendingBaseline.query.filter_by(user_id=user_id).first()
    baseline_total = _coerce_float(
        getattr(baseline, "avg_total_variable", None) if baseline else None
    )
    implied: list[float] = []
    for c in checkins:
        stored = _coerce_float(getattr(c, "spending_delta_from_baseline", None))
        if stored is not None:
            # Negative delta = underspend = savings.
            if stored < 0:
                implied.append(-stored)
            continue
        total = _checkin_variable_total(c)
        if total is not None and baseline_total is not None and baseline_total > total:
            implied.append(baseline_total - total)
    if implied:
        return round(sum(implied) / len(implied), 2)

    return None


def _estimate_weekly_debt_paydown_rate(user_id: int) -> float | None:
    debt = DebtProfile.query.filter_by(user_id=user_id).first()
    if debt is None:
        return None
    monthly = 0.0
    for attr in (
        "revolving_min_payment",
        "installment_payment",
        "federal_student_payment",
        "bnpl_monthly_payment",
    ):
        val = _coerce_float(getattr(debt, attr, None))
        if val is not None and val > 0:
            monthly += val
    # Private student loans: approximate min as 1.5% of balance / month when APR known.
    private_bal = _coerce_float(getattr(debt, "private_student_balance", None))
    if private_bal and private_bal > 0:
        monthly += private_bal * 0.015
    if monthly <= 0:
        return None
    return round(monthly / _WEEKS_PER_MONTH, 2)


def _collect_projection_milestones(user_id: int) -> list[dict[str, Any]]:
    """Active financial milestones with current/target/date for projection."""
    today = date.today()
    milestones: list[dict[str, Any]] = []

    user = User.query.get(user_id)
    profile = None
    if user and user.email:
        profile = UserProfile.query.filter_by(email=user.email).first()

    for raw in _parse_profile_goals(profile.goals if profile else None):
        normalized = _normalize_goal(raw)
        current = normalized.get("current_amount")
        target = normalized.get("target_amount")
        if target is None or target <= 0:
            continue
        if current is None:
            current = 0.0
        target_date = _goal_target_date(raw, normalized, today)
        milestones.append(
            {
                "name": normalized.get("title") or "Financial goal",
                "kind": "savings",
                "current_balance": float(current),
                "target_amount": float(target),
                "target_date": target_date,
            }
        )

    housing = HousingProfile.query.filter_by(user_id=user_id).first()
    housing_goal = _housing_buy_goal(housing)
    if housing_goal and housing_goal.get("target_amount"):
        timeline = housing_goal.get("timeline_months")
        target_date = None
        if timeline:
            target_date = today + timedelta(days=int(round(float(timeline) * 30.44)))
        milestones.append(
            {
                "name": housing_goal.get("title") or "Down Payment",
                "kind": "savings",
                "current_balance": float(housing_goal.get("current_amount") or 0),
                "target_amount": float(housing_goal["target_amount"]),
                "target_date": target_date,
            }
        )

    debt = DebtProfile.query.filter_by(user_id=user_id).first()
    if debt is not None:
        total_debt = 0.0
        for attr in (
            "revolving_balance",
            "installment_balance",
            "federal_student_balance",
            "private_student_balance",
            "bnpl_balance",
        ):
            val = _coerce_float(getattr(debt, attr, None))
            if val is not None and val > 0:
                total_debt += val
        if total_debt > 0:
            # Debt payoff: current_balance is remaining debt; target is $0.
            milestones.append(
                {
                    "name": "Debt Payoff",
                    "kind": "debt_payoff",
                    "current_balance": round(total_debt, 2),
                    "target_amount": 0.0,
                    "target_date": today + timedelta(days=365),
                }
            )

    # Deduplicate by name.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for m in milestones:
        key = (m.get("name") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(m)
    return unique


def _goal_target_date(
    raw: dict[str, Any],
    normalized: dict[str, Any],
    today: date,
) -> date | None:
    for key in ("target_date", "due_date", "deadline"):
        raw_d = raw.get(key)
        if not raw_d:
            continue
        try:
            return date.fromisoformat(str(raw_d)[:10])
        except ValueError:
            continue
    timeline = normalized.get("timeline_months")
    if timeline is not None and timeline > 0:
        return today + timedelta(days=int(round(float(timeline) * 30.44)))
    return None


def _project_milestone(
    milestone: dict[str, Any],
    *,
    weekly_rate: float | None,
    today: date,
) -> dict[str, Any]:
    name = milestone.get("name") or "Goal"
    current = float(milestone.get("current_balance") or 0)
    target = float(milestone.get("target_amount") or 0)
    target_date = milestone.get("target_date")
    kind = milestone.get("kind") or "savings"

    # Debt payoff: remaining = current balance down to 0.
    if kind == "debt_payoff":
        remaining = max(0.0, current - target)
    else:
        remaining = max(0.0, target - current)

    remaining_rounded = round(remaining, 2)
    motivational = None
    if 0 < remaining_rounded <= max(1000.0, target * 0.25 if target else 1000.0):
        motivational = f"Only ${remaining_rounded:,.0f} away!"

    base = {
        "name": name,
        "kind": kind,
        "current_balance": round(current, 2),
        "target_amount": round(target, 2),
        "target_date": target_date.isoformat() if isinstance(target_date, date) else None,
        "weekly_saving_rate": weekly_rate,
        "projected_date": None,
        "status": "no_data",
        "days_difference": None,
        "shortfall_amount": 0,
        "weekly_need": None,
        "message": "Not enough savings history to project this milestone yet.",
        "remaining": remaining_rounded,
        "motivational": motivational,
    }

    if remaining_rounded <= 0:
        base.update(
            {
                "status": "ahead",
                "days_difference": 0,
                "projected_date": today.isoformat(),
                "message": f"You've already hit {name} — nice work!",
                "motivational": "Milestone reached!",
            }
        )
        return base

    if weekly_rate is None or weekly_rate <= 0:
        return base

    weeks_needed = remaining_rounded / weekly_rate
    projected_date = today + timedelta(days=int(round(weeks_needed * 7)))
    base["projected_date"] = projected_date.isoformat()

    if target_date is None:
        amt_label = _money_label(target if kind != "debt_payoff" else remaining_rounded)
        base.update(
            {
                "status": "on_track",
                "message": (
                    f"At ${weekly_rate:,.0f}/week, you'll hit {amt_label} "
                    f"by {_format_friendly_date(projected_date)}."
                ),
            }
        )
        if motivational:
            base["message"] = f"{motivational} {base['message']}"
        return base

    days_difference = (projected_date - target_date).days
    base["days_difference"] = days_difference

    if days_difference <= _AHEAD_DAYS:
        status = "ahead"
    elif days_difference > _BEHIND_DAYS:
        status = "behind"
    else:
        status = "on_track"
    base["status"] = status

    target_label = _money_label(target if kind != "debt_payoff" else 0)
    if kind == "debt_payoff":
        target_label = "$0 debt"

    if status == "ahead":
        early = abs(days_difference)
        base["message"] = (
            f"You'll hit {target_label} by {_format_friendly_date(projected_date)} "
            f"(target: {_format_friendly_date(target_date)}) — {early} days early!"
        )
    elif status == "on_track":
        base["message"] = (
            f"You'll hit {target_label} by {_format_friendly_date(projected_date)} "
            f"(target: {_format_friendly_date(target_date)})."
        )
    else:
        weeks_left = max(1, int(round((target_date - today).days / 7)))
        amount_by_target = weekly_rate * weeks_left
        shortfall = max(0.0, round(remaining_rounded - amount_by_target, 2))
        weekly_need = round(shortfall / weeks_left, 2) if shortfall > 0 else 0.0
        base["shortfall_amount"] = shortfall
        base["weekly_need"] = weekly_need if weekly_need > 0 else None
        late = days_difference
        msg = (
            f"At current rate, you'll hit {target_label} by "
            f"{_format_friendly_date(projected_date)} "
            f"(target: {_format_friendly_date(target_date)}) — {late} days late."
        )
        if shortfall > 0 and weekly_need:
            msg += (
                f" Need ${weekly_need:,.0f}/week extra. "
                f"You need to save ${shortfall:,.0f} more to hit your goal on time "
                f"(${weekly_need:,.0f}/week for the next {weeks_left} weeks)."
            )
        base["message"] = msg

    if motivational and status != "behind":
        base["message"] = f"{motivational} {base['message']}"

    return base


def _money_label(amount: float) -> str:
    if amount >= 1000 and abs(amount - round(amount / 1000) * 1000) < 1:
        return f"${amount/1000:.0f}K"
    return f"${amount:,.0f}"


def _format_friendly_date(d: date) -> str:
    return f"{d.strftime('%B')} {d.day}"


def _career_gaps(
    *,
    annual_income: int | float | None,
    target_comp: float | None,
    personal: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    current = _coerce_float(annual_income)

    if current is not None and target_comp is not None and target_comp > 0:
        # Avoid a fake gap when resolve_current_salary fell back to target_comp.
        if abs(current - target_comp) > 1:
            amount = round(target_comp - current, 2)
            pct = round((amount / current) * 100.0, 1) if current > 0 else None
            if amount > 0:
                gaps.append(
                    {
                        "id": "target_comp_gap",
                        "label": "Gap to target compensation",
                        "current": current,
                        "target": target_comp,
                        "amount": amount,
                        "percent": pct,
                        "severity": "stretched" if pct is not None and pct <= 20 else "blocked",
                    }
                )

    if current is not None and personal:
        median = _coerce_float(personal.get("pct_50"))
        if median is not None and median > 0 and current < median:
            amount = round(median - current, 2)
            pct = round((amount / median) * 100.0, 1)
            gaps.append(
                {
                    "id": "median_gap",
                    "label": "Below field median",
                    "current": current,
                    "target": median,
                    "amount": amount,
                    "percent": pct,
                    "severity": "stretched" if pct <= 15 else "blocked",
                }
            )

        p75 = _coerce_float(personal.get("pct_75"))
        if p75 is not None and p75 > 0 and current < p75:
            amount = round(p75 - current, 2)
            pct = round((amount / p75) * 100.0, 1)
            # Only surface p75 gap when already at/above median (next rung).
            if median is not None and current >= median:
                gaps.append(
                    {
                        "id": "p75_gap",
                        "label": "Gap to 75th percentile",
                        "current": current,
                        "target": p75,
                        "amount": amount,
                        "percent": pct,
                        "severity": "on_track" if pct <= 10 else "stretched",
                    }
                )

    return gaps


def _career_opportunities(
    *,
    career: CareerProfile | None,
    annual_income: int | float | None,
    personal: dict[str, Any] | None,
    gaps: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []

    if career and career.open_to_move:
        opportunities.append(
            {
                "id": "open_to_move",
                "type": "signal",
                "label": "Open to a move",
                "detail": "Profile marked open to relocating or changing roles.",
                "priority": "high",
            }
        )

    if career and career.satisfaction is not None and career.satisfaction <= 2:
        opportunities.append(
            {
                "id": "low_satisfaction",
                "type": "signal",
                "label": "Low role satisfaction",
                "detail": f"Satisfaction rated {career.satisfaction}/5 — explore advancement or a change.",
                "priority": "high",
            }
        )

    if personal and personal.get("above_median") is False:
        opportunities.append(
            {
                "id": "raise_or_switch",
                "type": "signal",
                "label": "Compensation below field median",
                "detail": "Market data suggests room for a raise, promotion, or role switch.",
                "priority": "medium",
            }
        )

    if any(g.get("id") == "target_comp_gap" for g in gaps):
        gap = next(g for g in gaps if g.get("id") == "target_comp_gap")
        detail = f"About ${gap['amount']:,.0f}"
        if gap.get("percent") is not None:
            detail += f" ({gap['percent']}%)"
        detail += " to reach your target comp."
        opportunities.append(
            {
                "id": "close_target_gap",
                "type": "signal",
                "label": "Close target compensation gap",
                "detail": detail,
                "priority": "medium",
                "amount": gap.get("amount"),
            }
        )

    # Curated job postings that pay above current income in the same field.
    field = None
    if career is not None:
        field = career.bls_career_field or career.industry
    current = _coerce_float(annual_income) or 0.0
    if field:
        query = JobPosting.query.filter_by(is_active=True, career_field=field)
        if current > 0:
            query = query.filter(JobPosting.salary_min > int(current * 0.95))
        jobs = (
            query.order_by(JobPosting.salary_max.desc())
            .limit(max(1, limit))
            .all()
        )
        for job in jobs:
            mid = (int(job.salary_min) + int(job.salary_max)) / 2.0
            lift = round(mid - current, 2) if current > 0 else None
            opportunities.append(
                {
                    "id": f"job_{job.id}",
                    "type": "job_posting",
                    "label": f"{job.title} at {job.company}",
                    "detail": (
                        f"{job.city}, {job.state} · "
                        f"${job.salary_min:,}–${job.salary_max:,}"
                        + (f" · +${lift:,.0f} vs current" if lift and lift > 0 else "")
                    ),
                    "priority": "medium",
                    "salary_min": job.salary_min,
                    "salary_max": job.salary_max,
                    "city": job.city,
                    "state": job.state,
                    "url": job.url,
                    "advancement_trajectory": job.advancement_trajectory,
                }
            )

    # De-dupe by id, keep order, cap.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for opp in opportunities:
        oid = str(opp.get("id"))
        if oid in seen:
            continue
        seen.add(oid)
        unique.append(opp)
        if len(unique) >= max(1, limit) + 3:  # allow a few signal + job mix
            break
    return unique[: max(limit + 3, limit)]


def _relationship_ratings(
    current: WeeklyCheckin | None,
    previous: WeeklyCheckin | None,
) -> dict[str, dict[str, Any]]:
    ratings: dict[str, dict[str, Any]] = {}
    if current is None:
        return ratings
    for key in _RELATIONSHIP_RATING_KEYS:
        current_val = _coerce_float(getattr(current, key, None))
        previous_val = (
            _coerce_float(getattr(previous, key, None)) if previous is not None else None
        )
        direction = _raw_direction(current_val, previous_val)
        ratings[key] = {
            "value": current_val,
            "previous": previous_val,
            "delta": (
                round(current_val - previous_val, 2)
                if current_val is not None and previous_val is not None
                else None
            ),
            "direction": direction,
            "trend": _interpretive_trend(key, direction),
        }
    return ratings


def _relationship_changes(
    current: WeeklyCheckin | None,
    previous: WeeklyCheckin | None,
    ratings: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    metric_changes = [
        {
            "metric": key,
            "delta": info.get("delta"),
            "direction": info.get("direction"),
            "trend": info.get("trend"),
            "value": info.get("value"),
            "previous": info.get("previous"),
        }
        for key, info in ratings.items()
        if info.get("delta") is not None
    ]
    meaningful_current = (
        getattr(current, "meaningful_time_with_people", None) if current else None
    )
    meaningful_previous = (
        getattr(previous, "meaningful_time_with_people", None) if previous else None
    )
    return {
        "metrics": metric_changes,
        "meaningful_time_with_people": {
            "current": meaningful_current,
            "previous": meaningful_previous,
            "changed": (
                meaningful_current != meaningful_previous
                if meaningful_current is not None and meaningful_previous is not None
                else None
            ),
        },
        "summary": {
            "improving": [m["metric"] for m in metric_changes if m["trend"] == "improving"],
            "declining": [m["metric"] for m in metric_changes if m["trend"] == "declining"],
            "stable": [m["metric"] for m in metric_changes if m["trend"] == "stable"],
        },
    }


def _connection_summary(person: VibeTrackedPerson) -> dict[str, Any]:
    rel_type = (person.relationship_type or "").strip().lower()
    card_type = (person.card_type or "person").strip().lower()
    is_partner = rel_type in _PARTNER_TYPES
    is_family = card_type in _FAMILY_CARD_TYPES or rel_type in _FAMILY_TYPES

    latest = (
        VibePersonAssessment.query.filter_by(tracked_person_id=person.id)
        .order_by(VibePersonAssessment.completed_at.desc())
        .first()
    )
    trend = VibePersonTrend.query.filter_by(tracked_person_id=person.id).first()

    emotional = int(latest.emotional_score) if latest else None
    financial = int(latest.financial_score) if latest else None
    prev_assessment = None
    if latest:
        prev_assessment = (
            VibePersonAssessment.query.filter(
                VibePersonAssessment.tracked_person_id == person.id,
                VibePersonAssessment.completed_at < latest.completed_at,
            )
            .order_by(VibePersonAssessment.completed_at.desc())
            .first()
        )

    emotional_change = None
    financial_change = None
    if latest and prev_assessment:
        emotional_change = int(latest.emotional_score) - int(prev_assessment.emotional_score)
        financial_change = int(latest.financial_score) - int(prev_assessment.financial_score)

    return {
        "id": str(person.id),
        "nickname": person.nickname,
        "relationship_type": person.relationship_type,
        "card_type": person.card_type,
        "is_partner": is_partner,
        "is_family": is_family,
        "estimated_monthly_cost": _coerce_float(person.estimated_monthly_cost),
        "emotional_score": emotional,
        "financial_score": financial,
        "emotional_change": emotional_change,
        "financial_change": financial_change,
        "verdict_label": latest.verdict_label if latest else None,
        "trend_direction": trend.trend_direction if trend else None,
        "emotional_delta": trend.emotional_delta if trend else emotional_change,
        "financial_delta": trend.financial_delta if trend else financial_change,
        "stay_or_go_signal": trend.stay_or_go_signal if trend else None,
        "last_assessed_at": (
            person.last_assessed_at.isoformat() if person.last_assessed_at else None
        ),
        "assessment_count": person.assessment_count or 0,
    }


def _select_partner(
    connections: list[dict[str, Any]],
    current: WeeklyCheckin | None,
) -> dict[str, Any] | None:
    partners = [c for c in connections if c.get("is_partner")]
    partner = partners[0] if partners else None
    # If no typed partner, use highest emotional-score person card as soft partner signal
    # only when check-in has primary_partner_rating.
    if partner is None and current is not None:
        partner_rating = _coerce_float(getattr(current, "primary_partner_rating", None))
        if partner_rating is not None:
            person_cards = [
                c
                for c in connections
                if (c.get("card_type") or "person") == "person" and not c.get("is_family")
            ]
            if person_cards:
                partner = max(
                    person_cards,
                    key=lambda c: (
                        c.get("emotional_score") is not None,
                        c.get("emotional_score") or 0,
                        c.get("assessment_count") or 0,
                    ),
                )
                partner = {**partner, "is_partner": True, "inferred": True}

    if partner is None:
        return None

    out = dict(partner)
    if current is not None:
        out["checkin_rating"] = _coerce_float(getattr(current, "primary_partner_rating", None))
        out["financial_convo_with_partner"] = getattr(
            current, "financial_convo_with_partner", None
        )
        out["financial_communication_rating"] = _coerce_float(
            getattr(current, "financial_communication_with_partner", None)
        )
        out["partner_spending_unplanned"] = getattr(
            current, "partner_spending_unplanned", None
        )
        out["partner_spending_amount"] = _coerce_float(
            getattr(current, "partner_spending_amount", None)
        )
    return out


def _upcoming_relationship_events(user_id: int, upcoming_days: int) -> list[dict[str, Any]]:
    user = User.query.get(user_id)
    if not user or not user.email:
        return []
    profile = UserProfile.query.filter_by(email=user.email).first()
    if not profile or not profile.important_dates:
        return []
    try:
        important = json.loads(profile.important_dates)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(important, dict):
        return []

    today = date.today()
    end = today + timedelta(days=max(1, upcoming_days))
    events: list[dict[str, Any]] = []
    for ev in _iter_normalized_important_events(important):
        raw_d = ev.get("date")
        if not raw_d:
            continue
        try:
            ev_date = date.fromisoformat(str(raw_d)[:10])
        except ValueError:
            continue
        if ev_date < today or ev_date > end:
            continue
        events.append(
            {
                "name": ev.get("name"),
                "date": ev_date.isoformat(),
                "days_until": (ev_date - today).days,
                "cost": _coerce_float(ev.get("cost")) or 0.0,
                "person_nickname": ev.get("person_nickname") or None,
                "emoji": ev.get("emoji"),
                "significant": True,
            }
        )
    events.sort(key=lambda e: e.get("date") or "9999-99-99")
    return events


def _parse_profile_goals(raw: str | None) -> list[dict[str, Any]]:
    if not raw or not str(raw).strip():
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        # Free-text goals blob — treat as a single untitled goal description.
        text = str(raw).strip()
        return [{"title": text[:255], "description": text, "source": "user_profile.goals_text"}]

    if isinstance(data, list):
        return [g for g in data if isinstance(g, dict)]
    if isinstance(data, dict):
        nested = data.get("goals")
        if isinstance(nested, list):
            return [g for g in nested if isinstance(g, dict)]
        if data.get("title") or data.get("name") or data.get("type"):
            return [data]
    return []


def _housing_buy_goal(housing: HousingProfile | None) -> dict[str, Any] | None:
    if housing is None or not housing.has_buy_goal:
        return None
    target_price = _coerce_float(housing.target_price)
    saved = _coerce_float(housing.down_payment_saved) or 0.0
    target_down = (
        round(target_price * _DEFAULT_DOWN_PAYMENT_PCT, 2) if target_price and target_price > 0 else None
    )
    progress_pct = _progress_pct(saved, target_down)
    timeline = housing.target_timeline_months
    on_track = _infer_on_track(progress_pct, timeline_months=timeline)
    return {
        "id": "housing_buy_goal",
        "title": "Home purchase down payment",
        "domain": "housing",
        "source": "housing_profile",
        "current_amount": saved,
        "target_amount": target_down,
        "target_price": target_price,
        "timeline_months": timeline,
        "progress_pct": progress_pct,
        "on_track": on_track,
    }


def _normalize_goal(raw: dict[str, Any]) -> dict[str, Any]:
    title = (
        raw.get("title")
        or raw.get("name")
        or raw.get("type")
        or raw.get("goal")
        or "Untitled goal"
    )
    current = _coerce_float(
        raw.get("current_amount")
        or raw.get("current")
        or raw.get("saved")
        or raw.get("current_savings")
    )
    target = _coerce_float(
        raw.get("target_amount")
        or raw.get("target")
        or raw.get("goal_amount")
        or raw.get("amount")
    )
    progress_pct = _coerce_float(
        raw.get("progress_pct")
        or raw.get("progress_percentage")
        or raw.get("progress")
    )
    if progress_pct is None:
        progress_pct = _progress_pct(current, target)
    elif progress_pct > 1 and progress_pct <= 100:
        progress_pct = round(progress_pct, 1)
    elif 0 <= progress_pct <= 1:
        progress_pct = round(progress_pct * 100.0, 1)

    on_track = raw.get("on_track")
    if isinstance(on_track, str):
        on_track = on_track.strip().lower() in {"true", "1", "yes", "on_track"}
    elif on_track is not None:
        on_track = bool(on_track)
    else:
        on_track = _infer_on_track(
            progress_pct,
            timeline_months=_coerce_float(raw.get("timeline_months") or raw.get("timeline")),
        )

    return {
        "id": raw.get("id") or raw.get("goal_id"),
        "title": str(title)[:255],
        "description": raw.get("description"),
        "domain": raw.get("domain") or raw.get("category") or "financial",
        "source": raw.get("source"),
        "current_amount": current,
        "target_amount": target,
        "timeline_months": _coerce_float(raw.get("timeline_months") or raw.get("timeline")),
        "progress_pct": progress_pct,
        "on_track": on_track,
    }


def _progress_pct(current: float | None, target: float | None) -> float | None:
    if current is None or target is None or target <= 0:
        return None
    return round(min(100.0, max(0.0, (current / target) * 100.0)), 1)


def _infer_on_track(
    progress_pct: float | None,
    *,
    timeline_months: float | None = None,
) -> bool | None:
    if progress_pct is None:
        return None
    if progress_pct >= _ON_TRACK_PROGRESS_PCT:
        return True
    # With a long timeline and low progress, still unknown rather than off-track.
    if timeline_months is not None and timeline_months >= 12 and progress_pct >= 25:
        return True
    if progress_pct < 30:
        return False
    return None


def _dedupe_goals(goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for goal in goals:
        key = (goal.get("title") or "").strip().lower()
        if not key:
            continue
        if key not in best:
            best[key] = goal
            order.append(key)
            continue
        existing = best[key]
        existing_score = (existing.get("progress_pct") is not None) + (
            existing.get("target_amount") is not None
        )
        new_score = (goal.get("progress_pct") is not None) + (goal.get("target_amount") is not None)
        if new_score > existing_score:
            best[key] = goal
    return [best[k] for k in order]


def _collect_wins(user_id: int, lookback_weeks: int) -> list[dict[str, Any]]:
    checkins = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .order_by(desc(WeeklyCheckin.week_ending_date))
        .limit(max(1, lookback_weeks))
        .all()
    )
    wins: list[dict[str, Any]] = []
    for c in checkins:
        text = (c.wins or "").strip() if c.wins else ""
        reflection = (
            (c.weekly_reflection_change or "").strip()
            if getattr(c, "weekly_reflection_change", None)
            else ""
        )
        if text:
            wins.append(
                {
                    "week_number": c.week_number,
                    "week_ending_date": (
                        c.week_ending_date.isoformat() if c.week_ending_date else None
                    ),
                    "text": text,
                    "source": "wins",
                }
            )
        if reflection and reflection.lower() != text.lower():
            wins.append(
                {
                    "week_number": c.week_number,
                    "week_ending_date": (
                        c.week_ending_date.isoformat() if c.week_ending_date else None
                    ),
                    "text": reflection,
                    "source": "weekly_reflection_change",
                }
            )
    return wins


def _todo_to_dict(todo: Todo, *, today: date, is_open: bool) -> dict[str, Any]:
    due = todo.due_date
    is_overdue = bool(is_open and due is not None and due < today)
    days_overdue = (today - due).days if is_overdue and due is not None else 0
    return {
        "id": todo.id,
        "title": todo.title,
        "description": todo.description,
        "status": todo.status,
        "priority": todo.priority,
        "domain": todo.domain,
        "week_created": todo.week_created,
        "due_date": due.isoformat() if due else None,
        "created_at": todo.created_at.isoformat() if todo.created_at else None,
        "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
        "is_overdue": is_overdue,
        "days_overdue": days_overdue,
    }


def _checkin_variable_total(checkin: WeeklyCheckin) -> float | None:
    vals = [_coerce_float(getattr(checkin, k, None)) for k in _CATEGORY_KEYS]
    present = [v for v in vals if v is not None]
    if not present:
        disc = _coerce_float(getattr(checkin, "discretionary_spending", None))
        return disc
    return round(sum(present), 2)


def _baseline_for(baseline_row: UserSpendingBaseline | None, checkin_key: str) -> float | None:
    if baseline_row is None:
        return None
    attr = _CHECKIN_TO_BASELINE.get(checkin_key)
    if not attr:
        return None
    return _coerce_float(getattr(baseline_row, attr, None))


def _compare_amount(
    current_val: float | None,
    previous_val: float | None,
    baseline_val: float | None,
) -> dict[str, Any]:
    reference = baseline_val if baseline_val is not None else previous_val
    delta = (
        round(current_val - reference, 2)
        if current_val is not None and reference is not None
        else None
    )
    ratio = (
        round(current_val / reference, 2)
        if current_val is not None and reference is not None and reference > 0
        else None
    )
    pct = (
        round(((current_val - reference) / reference) * 100.0, 1)
        if current_val is not None and reference is not None and reference > 0
        else None
    )
    return {
        "current": current_val,
        "previous": previous_val,
        "baseline": baseline_val,
        "delta": delta,
        "percent_change": pct,
        "ratio": ratio,
        "is_spike": bool(ratio is not None and ratio >= _SPIKE_RATIO and (current_val or 0) > 0),
        "is_elevated": bool(
            ratio is not None and ratio >= _ELEVATED_RATIO and (current_val or 0) > 0
        ),
    }


def _category_comparisons(
    current: WeeklyCheckin,
    previous: WeeklyCheckin | None,
    baseline_row: UserSpendingBaseline | None,
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key in _CATEGORY_KEYS:
        short = key.replace("_estimate", "")
        out[short] = _compare_amount(
            _coerce_float(getattr(current, key, None)),
            _coerce_float(getattr(previous, key, None)) if previous else None,
            _baseline_for(baseline_row, key),
        )
    return out


def _tagged_comparisons(
    current: WeeklyCheckin,
    previous: WeeklyCheckin | None,
    baseline_row: UserSpendingBaseline | None,
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for key in _TAGGED_KEYS:
        short = key.replace("_spending", "")
        out[short] = _compare_amount(
            _coerce_float(getattr(current, key, None)),
            _coerce_float(getattr(previous, key, None)) if previous else None,
            _baseline_for(baseline_row, key),
        )
    return out


def _detect_spikes(
    categories: dict[str, dict[str, Any]],
    tagged: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    spikes: list[dict[str, Any]] = []
    for group, items in (("category", categories), ("tagged", tagged)):
        for name, info in items.items():
            if not info.get("is_spike"):
                continue
            spikes.append(
                {
                    "type": group,
                    "name": name,
                    "current": info.get("current"),
                    "baseline": info.get("baseline"),
                    "previous": info.get("previous"),
                    "ratio": info.get("ratio"),
                    "percent_change": info.get("percent_change"),
                }
            )
    spikes.sort(key=lambda s: s.get("ratio") or 0, reverse=True)
    return spikes


def _detect_patterns(
    current: WeeklyCheckin,
    checkins: list[WeeklyCheckin],
    categories: dict[str, dict[str, Any]],
    tagged: dict[str, dict[str, Any]],
    delta_pct: float | None,
) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []

    stress_level = _coerce_float(getattr(current, "stress_level", None))
    stress_spend = tagged.get("stress", {}).get("current")
    if (
        stress_level is not None
        and stress_level >= 7
        and stress_spend is not None
        and stress_spend > 0
    ):
        patterns.append(
            {
                "id": "stress_spend_link",
                "label": "Stress-linked spending",
                "detail": (
                    f"Stress {int(stress_level)}/10 with ${stress_spend:.0f} "
                    "tagged as stress spending this week."
                ),
            }
        )

    impulse_streak = 0
    for c in checkins:
        impulse = _coerce_float(getattr(c, "impulse_spending", None)) or 0.0
        had_impulse = bool(getattr(c, "had_impulse_purchases", False)) or impulse > 0
        if had_impulse:
            impulse_streak += 1
        else:
            break
    if impulse_streak >= 3:
        patterns.append(
            {
                "id": "impulse_streak",
                "label": "Impulse spending streak",
                "detail": f"Impulse purchases in {impulse_streak} consecutive weeks.",
            }
        )

    elevated_weeks = 0
    for c in checkins[:4]:
        total = _checkin_variable_total(c)
        # Compare each week to the mean of the other lookback weeks when possible.
        others = [
            t
            for t in (_checkin_variable_total(x) for x in checkins if x is not c)
            if t is not None
        ]
        if total is None or not others:
            continue
        mean_others = sum(others) / len(others)
        if mean_others > 0 and total >= mean_others * _ELEVATED_RATIO:
            elevated_weeks += 1
    if elevated_weeks >= 3:
        patterns.append(
            {
                "id": "elevated_spend_run",
                "label": "Elevated spending run",
                "detail": (
                    f"Spending ran ≥20% above peer-week average in "
                    f"{elevated_weeks} of the last {min(4, len(checkins))} weeks."
                ),
            }
        )

    if delta_pct is not None and delta_pct >= 50:
        patterns.append(
            {
                "id": "large_positive_delta",
                "label": "Large spend increase vs baseline",
                "detail": f"Total variable spend is {delta_pct:.0f}% above baseline.",
            }
        )
    elif delta_pct is not None and delta_pct <= -30:
        patterns.append(
            {
                "id": "large_negative_delta",
                "label": "Spending well below baseline",
                "detail": f"Total variable spend is {abs(delta_pct):.0f}% below baseline.",
            }
        )

    shopping = categories.get("shopping", {})
    entertainment = categories.get("entertainment", {})
    mood = _coerce_float(getattr(current, "mood_rating", None)) or _coerce_float(
        getattr(current, "overall_mood", None)
    )
    disc_spike = (shopping.get("is_spike") or entertainment.get("is_spike")) and mood is not None and mood <= 4
    if disc_spike:
        patterns.append(
            {
                "id": "low_mood_discretionary_spike",
                "label": "Low mood + discretionary spike",
                "detail": (
                    f"Mood {int(mood)}/10 with a spike in shopping and/or entertainment."
                ),
            }
        )

    if getattr(current, "social_spending_unplanned", None) is True:
        amt = _coerce_float(getattr(current, "social_spending_amount", None))
        patterns.append(
            {
                "id": "unplanned_social_spend",
                "label": "Unplanned social spending",
                "detail": (
                    f"Unplanned social spend"
                    + (f" of ${amt:.0f}." if amt is not None else ".")
                ),
            }
        )

    if getattr(current, "unexpected_kid_spending", None) is True:
        amt = _coerce_float(getattr(current, "unexpected_kid_amount", None))
        patterns.append(
            {
                "id": "unexpected_kid_spend",
                "label": "Unexpected kid-related spending",
                "detail": (
                    f"Unexpected kid spend"
                    + (f" of ${amt:.0f}." if amt is not None else ".")
                ),
            }
        )

    biggest = _coerce_float(getattr(current, "biggest_unnecessary_purchase", None))
    if biggest is not None and biggest > 0:
        cat = getattr(current, "biggest_unnecessary_category", None) or "uncategorized"
        patterns.append(
            {
                "id": "biggest_unnecessary_purchase",
                "label": "Notable unnecessary purchase",
                "detail": f"${biggest:.0f} in {cat}.",
            }
        )

    return patterns
