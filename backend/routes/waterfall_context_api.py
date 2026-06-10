#!/usr/bin/env python3
"""
Waterfall + Money Fluency context assembly (#171).

GET /api/waterfall/context — single structured object from latest check-in state.
"""

from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Any

from flask import Blueprint, jsonify
from sqlalchemy import desc

from backend.auth.decorators import get_current_user_db_id, require_auth
from backend.services.correlation_engine_service import (
    compute_spending_deltas,
    has_transaction_weeks_history,
    weekly_actual_spend,
    weekly_baseline_before,
)
from backend.models.life_ledger import LifeLedgerProfile
from backend.models.user_models import User
from backend.models.vibe_tracker import VibeTrackedPerson
from backend.models.wellness import WeeklyCheckin

waterfall_context_bp = Blueprint("waterfall_context", __name__, url_prefix="/api/waterfall")

# Relationship direction values (spec + implemented checkup schema).
_REL_POSITIVE = frozenset({"definitely_yes", "mostly_yes", "improving", "stable"})
_REL_WATCH = frozenset({"not_really", "unsure", "declining", "uncertain"})

# Source fields counted toward data_completeness (non-null raw inputs).
_COMPLETENESS_FIELDS = (
    "housing_unexpected_cost",
    "housing_cost_changed",
    "mood_stress_triggered_purchase",
    "spending_intentionality_rating",
    "vehicle_decision_horizon",
    "housing_lease_end_horizon",
    "housing_down_payment_status",
    "housing_tenure",
    "body_work_impact",
    "body_ongoing_health_cost",
    "spirit_financially_anxious",
    "relationship_direction",
)


def _safe_getattr(obj: Any, attr: str, default: Any = None) -> Any:
    try:
        return getattr(obj, attr, default)
    except Exception:
        return default


def _resolve_user() -> User | None:
    uid = get_current_user_db_id()
    if uid is None:
        return None
    return User.query.get(uid)


def _derive_user_tier(user: User) -> str:
    if bool(getattr(user, "is_beta", False)) or (user.tier or "").strip().lower() == "professional":
        return "professional"
    if (user.tier or "").strip().lower() == "mid_tier":
        return "mid_tier"
    return "budget"


def _read_profile(user_id: int) -> LifeLedgerProfile | None:
    try:
        return LifeLedgerProfile.query.filter_by(user_id=user_id).first()
    except Exception:
        return None


def _read_recent_weekly_checkins(user_id: int, limit: int = 4) -> list[WeeklyCheckin]:
    try:
        return (
            WeeklyCheckin.query.filter_by(user_id=user_id)
            .order_by(desc(WeeklyCheckin.week_ending_date))
            .limit(limit)
            .all()
        )
    except Exception:
        return []


def _fixed_bills_pressure(profile: LifeLedgerProfile | None) -> str:
    try:
        if profile is None:
            return "normal"
        unexpected = _safe_getattr(profile, "housing_unexpected_cost")
        cost_changed = _safe_getattr(profile, "housing_cost_changed")
        if unexpected is True:
            return "elevated"
        if cost_changed == "increased":
            return "elevated"
        return "normal"
    except Exception:
        return "normal"


def _discretionary_risk(profile: LifeLedgerProfile | None) -> str:
    try:
        if profile is None:
            return "normal"
        trigger = _safe_getattr(profile, "mood_stress_triggered_purchase")
        if trigger == "yes":
            return "high"
        if trigger in ("not_sure", "unsure"):
            return "watch"
        return "normal"
    except Exception:
        return "normal"


def _surplus_trajectory(profile: LifeLedgerProfile | None) -> str:
    try:
        if profile is None:
            return "watch"
        rating = _safe_getattr(profile, "spending_intentionality_rating")
        if rating is None:
            return "watch"
        if rating >= 4:
            return "positive"
        if rating <= 2:
            return "at_risk"
        return "watch"
    except Exception:
        return "watch"


def _vehicle_decision(profile: LifeLedgerProfile | None) -> str | None:
    try:
        if profile is None:
            return None
        horizon = _safe_getattr(profile, "vehicle_decision_horizon")
        if horizon is None:
            return None
        if horizon == "keeping_years":
            return "keeping"
        if horizon == "unsure":
            return "unsure"
        if horizon in ("considering_replace", "actively_shopping"):
            return "selling"
        return None
    except Exception:
        return None


def _lease_renewal_imminent(profile: LifeLedgerProfile | None) -> bool:
    try:
        if profile is None:
            return False
        horizon = _safe_getattr(profile, "housing_lease_end_horizon")
        return horizon in ("within_3_months", "under_3mo")
    except Exception:
        return False


def _down_payment_status(profile: LifeLedgerProfile | None) -> str | None:
    try:
        if profile is None:
            return None
        tenure = _safe_getattr(profile, "housing_tenure")
        if tenure == "own":
            raw = _safe_getattr(profile, "housing_down_payment_status")
            if raw is None:
                return "owner"
            mapping = {
                "on_track": "on_track",
                "ready": "on_track",
                "started": "behind",
                "not_saving": "not_started",
                "behind": "behind",
                "not_started": "not_started",
            }
            return mapping.get(raw, "owner")
        if tenure == "rent":
            return None
        raw = _safe_getattr(profile, "housing_down_payment_status")
        if raw is None:
            return None
        mapping = {
            "on_track": "on_track",
            "ready": "on_track",
            "started": "behind",
            "not_saving": "not_started",
            "behind": "behind",
            "not_started": "not_started",
        }
        return mapping.get(raw)
    except Exception:
        return None


def _body_work_impact(profile: LifeLedgerProfile | None) -> bool | None:
    try:
        if profile is None:
            return None
        raw = _safe_getattr(profile, "body_work_impact")
        if raw is None:
            return None
        if raw in ("yes", "somewhat", "minor", "moderate", "major", "severe"):
            return raw != "none"
        return False
    except Exception:
        return None


def _body_ongoing_health_cost(profile: LifeLedgerProfile | None) -> bool | None:
    try:
        if profile is None:
            return None
        val = _safe_getattr(profile, "body_ongoing_health_cost")
        return val if isinstance(val, bool) else None
    except Exception:
        return None


def _financially_anxious(profile: LifeLedgerProfile | None) -> bool | None:
    try:
        if profile is None:
            return None
        raw = _safe_getattr(profile, "spirit_financially_anxious")
        if raw is None:
            return None
        return raw in ("yes", "a_little", "unsure")
    except Exception:
        return None


def _relationship_direction_values(user_id: int, profile: LifeLedgerProfile | None) -> list[str]:
    """Best-effort last-4 directions; profile holds the latest hub check-in."""
    values: list[str] = []
    try:
        _ = (
            VibeTrackedPerson.query.filter_by(user_id=user_id, is_archived=False)
            .order_by(desc(VibeTrackedPerson.assessment_count), desc(VibeTrackedPerson.last_assessed_at))
            .limit(1)
            .first()
        )
    except Exception:
        pass

    try:
        if profile is not None:
            direction = _safe_getattr(profile, "relationship_direction")
            if direction:
                values.append(str(direction))
    except Exception:
        pass

    return values[:4]


def _relationship_direction_signal(user_id: int, profile: LifeLedgerProfile | None) -> str | None:
    try:
        directions = _relationship_direction_values(user_id, profile)
        if not directions:
            return None

        positive_count = sum(1 for d in directions if d in _REL_POSITIVE)
        watch_count = sum(1 for d in directions if d in _REL_WATCH)

        if positive_count >= 3:
            return "positive"
        if watch_count >= 2:
            return "watch"

        if len(directions) == 1:
            only = directions[0]
            if only == "improving":
                return "positive"
            if only in ("declining", "uncertain"):
                return "watch"
            return "neutral"

        if positive_count > watch_count:
            return "positive" if positive_count >= 2 else "neutral"
        if watch_count > positive_count:
            return "watch"
        return "neutral"
    except Exception:
        return None


def _normalize_discipline_value(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return None
    if v > 10:
        return v / 10.0
    return v


def _stress_spend_from_checkins(checkins: list[WeeklyCheckin]) -> bool:
    try:
        if len(checkins) < 3:
            return False

        hits = 0
        for row in checkins[:4]:
            stress = _safe_getattr(row, "stress_level")
            if stress is None or stress < 7:
                continue

            discipline_raw = _safe_getattr(row, "spending_discipline_rating")
            control_raw = _safe_getattr(row, "spending_control")
            if discipline_raw is None:
                discipline_raw = control_raw

            discipline_norm = _normalize_discipline_value(discipline_raw)
            control_low = False
            if control_raw is not None:
                try:
                    control_low = float(control_raw) <= 40
                except (TypeError, ValueError):
                    control_low = False

            discipline_low = discipline_norm is not None and discipline_norm <= 4
            if discipline_low or control_low:
                hits += 1

        return hits >= 2
    except Exception:
        return False


def _monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _stress_spend_from_transactions(user_id: int, checkins: list[WeeklyCheckin]) -> bool:
    try:
        if not has_transaction_weeks_history(user_id, min_weeks=4):
            return False

        today = date.today()
        this_week_start = _monday_of_week(today)
        hits = 0

        for i in range(4):
            week_start = this_week_start - timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)

            stress = None
            for row in checkins:
                week_ending = _safe_getattr(row, "week_ending_date")
                if week_ending is not None and week_start <= week_ending <= week_end:
                    stress = _safe_getattr(row, "stress_level")
                    break

            if stress is None or stress < 7:
                continue

            actual_spend = weekly_actual_spend(user_id, week_start)
            baseline = weekly_baseline_before(user_id, week_start, weeks=8)
            if baseline is not None and baseline > 0 and actual_spend > baseline * 1.2:
                hits += 1

        return hits >= 2
    except Exception:
        return False


def _stress_spend_pattern_detected(user_id: int, checkins: list[WeeklyCheckin]) -> bool:
    try:
        from backend.models.transaction import Transaction

        if Transaction.query.filter_by(user_id=user_id).count() > 0:
            txn_result = _stress_spend_from_transactions(user_id, checkins)
            if has_transaction_weeks_history(user_id, min_weeks=4):
                return txn_result
        return _stress_spend_from_checkins(checkins)
    except Exception:
        return _stress_spend_from_checkins(checkins)


def _source_value(profile: LifeLedgerProfile | None, field: str) -> Any:
    if profile is None:
        return None
    return _safe_getattr(profile, field)


def _data_completeness(profile: LifeLedgerProfile | None) -> float:
    try:
        if profile is None:
            return 0.0
        present = sum(1 for f in _COMPLETENESS_FIELDS if _source_value(profile, f) is not None)
        return round(present / len(_COMPLETENESS_FIELDS), 2)
    except Exception:
        return 0.0


def _last_updated(profile: LifeLedgerProfile | None, checkins: list[WeeklyCheckin]) -> str:
    candidates: list[datetime] = []
    try:
        if profile is not None:
            updated = _safe_getattr(profile, "updated_at")
            if isinstance(updated, datetime):
                candidates.append(updated)
    except Exception:
        pass

    for row in checkins:
        try:
            completed = _safe_getattr(row, "completed_at")
            if isinstance(completed, datetime):
                candidates.append(completed)
        except Exception:
            continue

    if candidates:
        return max(candidates).isoformat()
    return datetime.utcnow().isoformat()


def build_waterfall_context(user: User) -> dict[str, Any]:
    profile = _read_profile(user.id)
    checkins = _read_recent_weekly_checkins(user.id, limit=4)

    return {
        "fixed_bills_pressure": _fixed_bills_pressure(profile),
        "discretionary_risk": _discretionary_risk(profile),
        "surplus_trajectory": _surplus_trajectory(profile),
        "vehicle_decision": _vehicle_decision(profile),
        "lease_renewal_imminent": _lease_renewal_imminent(profile),
        "down_payment_status": _down_payment_status(profile),
        "body_work_impact": _body_work_impact(profile),
        "body_ongoing_health_cost": _body_ongoing_health_cost(profile),
        "financially_anxious": _financially_anxious(profile),
        "relationship_direction_signal": _relationship_direction_signal(user.id, profile),
        "stress_spend_pattern_detected": _stress_spend_pattern_detected(user.id, checkins),
        "actual_spending_delta": compute_spending_deltas(user.id),
        "user_tier": _derive_user_tier(user),
        "data_completeness": _data_completeness(profile),
        "last_updated": _last_updated(profile, checkins),
    }


@waterfall_context_bp.route("/context", methods=["GET"])
@require_auth
def get_waterfall_context():
    user = _resolve_user()
    if user is None:
        return jsonify({"error": "User not found"}), 404

    try:
        payload = build_waterfall_context(user)
    except Exception:
        return jsonify({"error": "Unable to build waterfall context"}), 500

    return jsonify(payload), 200
