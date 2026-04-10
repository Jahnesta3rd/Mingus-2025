#!/usr/bin/env python3
"""Vehicle Health — 10-question assessment for Life Ledger (vehicle module)."""

from __future__ import annotations

import secrets
import string
from datetime import datetime
from typing import Any

from backend.models.database import db
from backend.models.vehicle_models import Vehicle

# Each option value is 0–3 (best first in UI).
VEHICLE_CHECK_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": 1,
        "prompt": "Vehicle age",
        "options": [
            {"label": "Under 3 years", "value": 3},
            {"label": "3–7 years", "value": 2},
            {"label": "7–12 years", "value": 1},
            {"label": "Over 12 years", "value": 0},
        ],
    },
    {
        "id": 2,
        "prompt": "Mileage",
        "options": [
            {"label": "Under 30k miles", "value": 3},
            {"label": "30k–80k", "value": 2},
            {"label": "80k–150k", "value": 1},
            {"label": "Over 150k", "value": 0},
        ],
    },
    {
        "id": 3,
        "prompt": "Maintenance history",
        "options": [
            {"label": "Always on schedule, documented", "value": 3},
            {"label": "Mostly kept up", "value": 2},
            {"label": "Behind on some items", "value": 1},
            {"label": "Rarely maintained", "value": 0},
        ],
    },
    {
        "id": 4,
        "prompt": "Current known issues",
        "options": [
            {"label": "None", "value": 3},
            {"label": "1 minor issue", "value": 2},
            {"label": "Multiple minor or 1 major", "value": 1},
            {"label": "Multiple major issues", "value": 0},
        ],
    },
    {
        "id": 5,
        "prompt": "Reliability in last 12 months",
        "options": [
            {"label": "Zero unexpected breakdowns", "value": 3},
            {"label": "1 minor breakdown", "value": 2},
            {"label": "2–3 breakdowns", "value": 1},
            {"label": "4+ or stranded", "value": 0},
        ],
    },
    {
        "id": 6,
        "prompt": "Insurance situation",
        "options": [
            {"label": "Fully covered, comprehensive", "value": 3},
            {"label": "Liability + some coverage", "value": 2},
            {"label": "Minimum liability only", "value": 1},
            {"label": "Uninsured or lapsed", "value": 0},
        ],
    },
    {
        "id": 7,
        "prompt": "Vehicle use",
        "options": [
            {"label": "Low mileage, mostly local", "value": 3},
            {"label": "Moderate commute", "value": 2},
            {"label": "High mileage commuter", "value": 1},
            {"label": "Commercial or extreme use", "value": 0},
        ],
    },
    {
        "id": 8,
        "prompt": "Fuel efficiency",
        "options": [
            {"label": "Hybrid or EV", "value": 3},
            {"label": "Good MPG (30+)", "value": 2},
            {"label": "Average MPG (20–30)", "value": 1},
            {"label": "Poor MPG (under 20)", "value": 0},
        ],
    },
    {
        "id": 9,
        "prompt": "Emergency fund for car",
        "options": [
            {"label": "3+ months car costs saved", "value": 3},
            {"label": "1–2 months saved", "value": 2},
            {"label": "Less than 1 month", "value": 1},
            {"label": "Nothing saved", "value": 0},
        ],
    },
    {
        "id": 10,
        "prompt": "Plan for this vehicle",
        "options": [
            {"label": "Keeping 3+ more years", "value": 3},
            {"label": "Keeping 1–2 more years", "value": 2},
            {"label": "Replacing soon but no plan", "value": 1},
            {"label": "No idea, taking it day by day", "value": 0},
        ],
    },
]

# Per-question risk copy for weaker answers (used to pick 2–3 lowest-scoring areas).
_RISK_BY_Q_VALUE: dict[str, dict[int, str]] = {
    "1": {
        0: "Older vehicle (12+ years) — higher failure and repair probability",
        1: "Mid-life vehicle (7–12 years) — watch for wear-related costs",
        2: "Vehicle is 3–7 years — stay ahead of scheduled maintenance",
    },
    "2": {
        0: "High mileage — major service due soon",
        1: "Elevated mileage — budget for upcoming major services",
        2: "Moderate mileage — keep up with interval services",
    },
    "3": {
        0: "No maintenance history — unknown failure risk",
        1: "Maintenance backlog — catch-up reduces surprise repairs",
        2: "Some maintenance gaps — document and close them",
    },
    "4": {
        0: "Multiple known issues need immediate attention",
        1: "Known issues present — address before they cascade",
        2: "Minor issue on the books — fix early to avoid compound cost",
    },
    "5": {
        0: "Frequent breakdowns — budgeting and backup transport matter",
        1: "Multiple breakdowns — reliability risk to cash flow",
        2: "Recent breakdown — investigate root cause",
    },
    "6": {
        0: "No or lapsed insurance — legal and financial exposure",
        1: "Thin coverage — a serious incident could be expensive",
        2: "Coverage gaps — review limits vs. vehicle value",
    },
    "7": {
        0: "Heavy or commercial use accelerates wear and operating cost",
        1: "High annual miles — faster wear and higher upkeep",
        2: "Regular commuting — plan for tires, brakes, and fluids",
    },
    "8": {
        0: "Poor fuel economy — fuel spend is a steady drain",
        1: "Average MPG — efficiency upgrades or driving habits can help",
        2: "Fuel costs add up — track miles and budget fuel",
    },
    "9": {
        0: "No car emergency fund — repairs may hit cash flow hard",
        1: "Thin car savings — one repair can disrupt the month",
        2: "Limited car cushion — build toward 1–2 months of ownership cost",
    },
    "10": {
        0: "No replacement plan — surprise costs or rushed buying risk",
        1: "Uncertain timeline — start a simple replace-or-repair rule",
        2: "Near-term change possible — align savings with next step",
    },
}


def normalize_vehicle_check_answers(raw: dict[str, Any]) -> dict[str, int]:
    """Validate JSON answers: keys '1'..'10', values integers 0–3."""
    if not isinstance(raw, dict):
        raise ValueError("answers must be an object")
    out: dict[str, int] = {}
    for i in range(1, 11):
        key = str(i)
        if key not in raw:
            raise ValueError(f"Missing answer for question {i}")
        v = raw[key]
        if type(v) is not int:
            raise ValueError(f"Answer for question {i} must be an integer 0–3")
        if v < 0 or v > 3:
            raise ValueError(f"Answer for question {i} must be between 0 and 3")
        out[key] = v
    return out


def calculate_vehicle_score(answers: dict[str, int]) -> int:
    """Sum values / (10 * 3) * 100, rounded to int."""
    if len(answers) != 10:
        raise ValueError("answers must contain exactly 10 entries")
    total = sum(answers.values())
    return int(round((total / (10 * 3)) * 100.0))


def build_top_risks(answers: dict[str, int]) -> list[str]:
    """2–3 strings for the weakest answers (lowest numeric scores first)."""
    ranked: list[tuple[int, int, str]] = []
    for i in range(1, 11):
        k = str(i)
        v = answers[k]
        by_v = _RISK_BY_Q_VALUE.get(k, {})
        msg = by_v.get(v)
        if msg is None and v < 3:
            msg = "This area scored below ideal — worth a closer look"
        if msg:
            ranked.append((v, i, msg))
    ranked.sort(key=lambda t: (t[0], t[1]))
    out: list[str] = []
    seen: set[str] = set()
    for _, _, msg in ranked:
        if msg in seen:
            continue
        seen.add(msg)
        out.append(msg)
        if len(out) >= 3:
            break
    return out


def calculate_annual_maintenance(answers: dict[str, int], score: int) -> dict[str, Any]:
    """Annual maintenance estimate, risk band, and top risks from answers."""
    if score >= 75:
        tier = {"annual_cost": 800, "risk_level": "Low"}
    elif score >= 55:
        tier = {"annual_cost": 1800, "risk_level": "Moderate"}
    elif score >= 35:
        tier = {"annual_cost": 3600, "risk_level": "High"}
    else:
        tier = {"annual_cost": 6000, "risk_level": "Critical"}
    top_risks = build_top_risks(answers)
    return {**tier, "top_risks": top_risks}


_VIN_ALPHABET = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"


def _placeholder_vin(user_id: int) -> str:
    """17-char placeholder VIN unique per call (retry on collision)."""
    uid_part = min(max(user_id, 0), 99999)
    prefix = f"MNG{uid_part:05d}"
    return prefix + "".join(secrets.choice(_VIN_ALPHABET) for _ in range(9))


def ensure_placeholder_vehicle_from_assessment(
    user_id: int,
    answers: dict[str, int],
    estimated_annual_cost: int,
) -> Vehicle | None:
    """
    If the user has no Vehicle row, create a baseline record from assessment answers.
    """
    existing = Vehicle.query.filter_by(user_id=user_id).first()
    if existing is not None:
        return None

    current_year = datetime.utcnow().year
    age_a = answers.get("1", 2)
    age_delta = {3: 3, 2: 7, 1: 10, 0: 14}.get(age_a, 10)
    year = current_year - age_delta

    mileage_a = answers.get("2", 2)
    current_mileage = {3: 25_000, 2: 55_000, 1: 115_000, 0: 175_000}.get(mileage_a, 55_000)

    use_a = answers.get("7", 2)
    monthly_miles = {3: 500, 2: 1_000, 1: 1_500, 0: 2_000}.get(use_a, 1_000)

    vin = _placeholder_vin(user_id)
    for _ in range(8):
        if Vehicle.query.filter_by(vin=vin).first() is None:
            break
        vin = _placeholder_vin(user_id)
    else:
        vin = _placeholder_vin(user_id)

    vehicle = Vehicle(
        user_id=user_id,
        vin=vin,
        year=year,
        make="Unknown",
        model="Primary vehicle",
        trim=None,
        current_mileage=current_mileage,
        monthly_miles=monthly_miles,
        user_zipcode="00000",
        assigned_msa=None,
        notes="Created from Vehicle Health assessment",
        estimated_annual_cost=estimated_annual_cost,
    )
    db.session.add(vehicle)
    return vehicle
