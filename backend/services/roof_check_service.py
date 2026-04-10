#!/usr/bin/env python3
"""Roof Check — 12-question housing assessment for Life Ledger (roof module)."""

from __future__ import annotations

from typing import Any

ROOF_CHECK_QUESTIONS: list[dict[str, Any]] = [
    {
        "id": 1,
        "prompt": "Housing type",
        "options": [
            {"label": "Own with equity growing", "value": 3},
            {"label": "Rent strategically — saving the difference", "value": 2},
            {"label": "Own but underwater/flat", "value": 1},
            {"label": "Rent with nothing to show", "value": 0},
        ],
    },
    {
        "id": 2,
        "prompt": "Rent/mortgage to income ratio",
        "options": [
            {"label": "Under 25%", "value": 3},
            {"label": "25-30%", "value": 2},
            {"label": "30-40%", "value": 1},
            {"label": "Over 40%", "value": 0},
        ],
    },
    {
        "id": 3,
        "prompt": "Housing stability",
        "options": [
            {"label": "Owned or long-term stable lease", "value": 3},
            {"label": "Annual lease, renews easily", "value": 2},
            {"label": "Month-to-month or uncertain", "value": 1},
            {"label": "At risk of displacement", "value": 0},
        ],
    },
    {
        "id": 4,
        "prompt": "Location vs. opportunity",
        "options": [
            {"label": "Close to work, low commute cost", "value": 3},
            {"label": "Manageable commute", "value": 2},
            {"label": "Long commute, significant cost", "value": 1},
            {"label": "Location limits job opportunities", "value": 0},
        ],
    },
    {
        "id": 5,
        "prompt": "Building equity",
        "options": [
            {"label": "Yes, paying down mortgage", "value": 3},
            {"label": "Renting but investing the difference", "value": 2},
            {"label": "Renting, not investing difference", "value": 1},
            {"label": "No equity building at all", "value": 0},
        ],
    },
    {
        "id": 6,
        "prompt": "Housing cost trend",
        "options": [
            {"label": "Locked in stable rate", "value": 3},
            {"label": "Modest increases, manageable", "value": 2},
            {"label": "Significant rent increases yearly", "value": 1},
            {"label": "Uncontrollable, at landlord mercy", "value": 0},
        ],
    },
    {
        "id": 7,
        "prompt": "Emergency housing fund",
        "options": [
            {"label": "3+ months housing costs saved", "value": 3},
            {"label": "1-2 months saved", "value": 2},
            {"label": "Less than 1 month", "value": 1},
            {"label": "No housing emergency fund", "value": 0},
        ],
    },
    {
        "id": 8,
        "prompt": "Roommate situation",
        "options": [
            {"label": "Strategic roommates, significantly lowers cost", "value": 3},
            {"label": "Solo but within means", "value": 2},
            {"label": "Solo and stretched", "value": 1},
            {"label": "Paying for others or being subsidized chaotically", "value": 0},
        ],
    },
    {
        "id": 9,
        "prompt": "Space vs. cost",
        "options": [
            {"label": "Right-sized for needs and budget", "value": 3},
            {"label": "Slightly over/under but manageable", "value": 2},
            {"label": "Significantly over-housed, overpaying", "value": 1},
            {"label": "Under-housed, poor living conditions", "value": 0},
        ],
    },
    {
        "id": 10,
        "prompt": "Path to ownership",
        "options": [
            {"label": "Actively on path — saving, building credit", "value": 3},
            {"label": "Thinking about it but no concrete plan", "value": 2},
            {"label": "Not a priority right now", "value": 1},
            {"label": "Feels completely out of reach", "value": 0},
        ],
    },
    {
        "id": 11,
        "prompt": "Property tax/insurance awareness",
        "options": [
            {"label": "Fully understand all housing costs", "value": 3},
            {"label": "Know the basics", "value": 2},
            {"label": "Vague awareness", "value": 1},
            {"label": "No idea what total costs are", "value": 0},
        ],
    },
    {
        "id": 12,
        "prompt": "Housing decision basis",
        "options": [
            {"label": "Strategic — aligned with financial goals", "value": 3},
            {"label": "Practical — best I could find", "value": 2},
            {"label": "Emotional — fell in love with it", "value": 1},
            {"label": "Reactive — took what was available", "value": 0},
        ],
    },
]


def normalize_roof_check_answers(raw: dict[str, Any]) -> dict[str, int]:
    """Validate JSON answers: keys '1'..'12', values integers 0–3."""
    if not isinstance(raw, dict):
        raise ValueError("answers must be an object")
    out: dict[str, int] = {}
    for i in range(1, 13):
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


def calculate_roof_score(answers: dict[str, int]) -> int:
    """Sum values / (12 * 3) * 100, rounded to int."""
    if len(answers) != 12:
        raise ValueError("answers must contain exactly 12 entries")
    total = sum(answers.values())
    raw = (total / (12 * 3)) * 100.0
    return int(round(raw))


def calculate_housing_wealth_gap(answers: dict[str, int], score: int) -> dict[str, Any]:
    """
    Estimated annual wealth difference vs. an optimized housing situation.
    ten_year_gap is a tiered illustrative total reflecting growth on the annual gap.
    """
    if len(answers) != 12:
        raise ValueError("answers must contain exactly 12 entries")
    if score >= 75:
        return {
            "annual_wealth_gap": 0,
            "verdict": "Equity Builder",
            "ten_year_gap": 0,
        }
    if score >= 55:
        return {
            "annual_wealth_gap": 4800,
            "verdict": "Stability Zone",
            "ten_year_gap": 72000,
        }
    if score >= 35:
        return {
            "annual_wealth_gap": 12000,
            "verdict": "House Neutral",
            "ten_year_gap": 180000,
        }
    return {
        "annual_wealth_gap": 24000,
        "verdict": "House Poor",
        "ten_year_gap": 360000,
    }
