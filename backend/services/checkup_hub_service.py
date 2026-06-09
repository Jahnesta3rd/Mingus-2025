#!/usr/bin/env python3
"""Score helpers and profile field writers for dashboard checkup hub (#170)."""

from __future__ import annotations

import json
from typing import Any

from backend.models.life_ledger import LifeLedgerProfile

_WORK_IMPACT_PENALTY = {
    "none": 0,
    "minor": 5,
    "moderate": 15,
    "major": 25,
    "severe": 35,
}


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def compute_body_score_from_checkup(
    energy_rating: int,
    work_impact: str,
    ongoing_health_cost: bool,
) -> int:
    base = energy_rating * 20
    base -= _WORK_IMPACT_PENALTY.get(work_impact, 10)
    if ongoing_health_cost:
        base -= 10
    return _clamp_score(base)


def compute_roof_score_from_checkup(
    stability_rating: int,
    unexpected_cost: bool,
    cost_changed: str,
) -> int:
    base = stability_rating * 20
    if unexpected_cost:
        base -= 15
    if cost_changed == "increased":
        base -= 10
    elif cost_changed == "decreased":
        base += 5
    return _clamp_score(base)


def compute_vehicle_score_from_checkup(
    satisfaction: int,
    maintenance_confidence: int,
    reliability: int,
    value_perception: int,
    recent_concern: bool,
) -> int:
    avg = (satisfaction + maintenance_confidence + reliability + value_perception) / 4.0
    base = int(round(avg * 20))
    if recent_concern:
        base -= 10
    return _clamp_score(base)


def serialize_coping_methods(methods: list[str]) -> str:
    return json.dumps(methods)


def apply_body_checkup(profile: LifeLedgerProfile, data: dict[str, Any]) -> int:
    profile.body_energy_rating = data["body_energy_rating"]
    profile.body_work_impact = data["body_work_impact"]
    profile.body_ongoing_health_cost = data["body_ongoing_health_cost"]
    score = compute_body_score_from_checkup(
        data["body_energy_rating"],
        data["body_work_impact"],
        data["body_ongoing_health_cost"],
    )
    profile.body_score = score
    return score


def apply_mind_mood_checkup(profile: LifeLedgerProfile, data: dict[str, Any]) -> None:
    profile.mood_stress_triggered_purchase = data["mood_stress_triggered_purchase"]
    profile.mood_avoided_finances = data["mood_avoided_finances"]
    profile.mood_coping_methods = serialize_coping_methods(data["mood_coping_methods"])
    profile.spending_intentionality_rating = data["spending_intentionality_rating"]


def apply_spirit_calm_checkup(profile: LifeLedgerProfile, data: dict[str, Any]) -> None:
    profile.practice_had_moments = data["practice_had_moments"]
    profile.practice_affected_finances = data["practice_affected_finances"]
    profile.spirit_financially_anxious = data["spirit_financially_anxious"]


def apply_housing_checkup(profile: LifeLedgerProfile, data: dict[str, Any]) -> int:
    profile.housing_stability_rating = data["housing_stability_rating"]
    profile.housing_tenure = data["housing_tenure"]
    profile.housing_lease_end_horizon = data.get("housing_lease_end_horizon")
    profile.housing_cost_changed = data["housing_cost_changed"]
    profile.housing_down_payment_status = data.get("housing_down_payment_status")
    profile.housing_unexpected_cost = data["housing_unexpected_cost"]
    profile.housing_unexpected_cost_amount = data.get("housing_unexpected_cost_amount")
    score = compute_roof_score_from_checkup(
        data["housing_stability_rating"],
        data["housing_unexpected_cost"],
        data["housing_cost_changed"],
    )
    profile.roof_score = score
    return score


def apply_vehicle_checkup(profile: LifeLedgerProfile, data: dict[str, Any]) -> int:
    profile.vehicle_satisfaction_rating = data["vehicle_satisfaction_rating"]
    profile.vehicle_maintenance_confidence = data["vehicle_maintenance_confidence"]
    profile.vehicle_recent_concern = data["vehicle_recent_concern"]
    profile.vehicle_concern_description = data.get("vehicle_concern_description")
    profile.vehicle_weekly_miles = data["vehicle_weekly_miles"]
    profile.vehicle_last_service_horizon = data["vehicle_last_service_horizon"]
    profile.vehicle_insurance_known = data["vehicle_insurance_known"]
    profile.vehicle_insurance_premium = data.get("vehicle_insurance_premium")
    profile.vehicle_insurance_last_shopped = data.get("vehicle_insurance_last_shopped")
    profile.vehicle_decision_horizon = data["vehicle_decision_horizon"]
    profile.vehicle_reliability_rating = data["vehicle_reliability_rating"]
    profile.vehicle_value_perception = data["vehicle_value_perception"]
    score = compute_vehicle_score_from_checkup(
        data["vehicle_satisfaction_rating"],
        data["vehicle_maintenance_confidence"],
        data["vehicle_reliability_rating"],
        data["vehicle_value_perception"],
        data["vehicle_recent_concern"],
    )
    profile.vehicle_score = score
    return score


def apply_relationships_checkup(profile: LifeLedgerProfile, data: dict[str, Any]) -> None:
    profile.relationship_friction_type = data["relationship_friction_type"]
    profile.relationship_spending_this_week = data["relationship_spending_this_week"]
    profile.relationship_spending_amount = data.get("relationship_spending_amount")
    profile.relationship_spending_type = data.get("relationship_spending_type")
    profile.relationship_direction = data["relationship_direction"]
    profile.relationship_cost_awareness = data["relationship_cost_awareness"]
    profile.relationship_future_intention = data["relationship_future_intention"]
