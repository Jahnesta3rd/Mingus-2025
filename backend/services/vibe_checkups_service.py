#!/usr/bin/env python3
"""Scoring, verdict copy, and 12-month projection for Vibe Checkups."""

from __future__ import annotations

import math
import re
from typing import Any

# Emotional quiz keys — use the "value" component from each answer.
EMOTIONAL_KEYS = (
    "emotional_availability",
    "conflict_style",
    "shared_values",
    "apology_language",
    "accountability",
    "therapy_growth",
    "past_relationship_patterns",
    "boundary_setting",
    "jealousy_insecurity",
    "long_term_compatibility",
)

# Financial quiz keys — use the "financial" component from each answer.
FINANCIAL_KEYS = (
    "income_transparency",
    "spending_style",
    "debt_situation",
    "savings_habits",
    "check_splitting",
    "financial_emergency",
    "investment_awareness",
    "social_pressure_spending",
    "housing_situation",
    "family_financial_dynamics",
)

TIER_BASE = (
    {"dining": 800, "activities": 600, "gifts": 400, "travel": 500, "misc": 300},
    {"dining": 500, "activities": 350, "gifts": 250, "travel": 300, "misc": 150},
    {"dining": 300, "activities": 200, "gifts": 150, "travel": 200, "misc": 100},
    {"dining": 200, "activities": 150, "gifts": 100, "travel": 150, "misc": 80},
)

SEASONAL_MULTIPLIERS = (
    1.3,
    1.0,
    1.4,
    1.1,
    1.2,
    1.5,
    1.1,
    0.9,
    1.2,
    1.3,
    1.6,
    1.8,
)

_MONTH_EVENTS = (
    "New year reset: extra dates and resolutions spending.",
    "Valentine buildup: dining and small gifts ramp up.",
    "Spring outings: activities and weekend trips.",
    "Tax-adjacent stress: comfort spending and misc.",
    "Wedding season starts: gifts and travel deposits.",
    "Summer social peak: trips, dining, and activities.",
    "Mid-year check-ins: subscriptions and lifestyle creep.",
    "Back-to-social routine: local events and dining.",
    "Birthday clusters: gifts and group activities.",
    "Holiday planning begins: travel bookings and gifts.",
    "Thanksgiving + Friendsgiving: hosting and travel.",
    "Year-end splurge: gifts, travel, and celebrations.",
)


def _coerce_answer_components(entry: Any) -> tuple[int | None, int | None]:
    """Return (value, financial) from a stored answer (dict or plain int)."""
    if entry is None:
        return None, None
    if isinstance(entry, dict):
        v = entry.get("value")
        f = entry.get("financial")
        try:
            vi = int(v) if v is not None else None
        except (TypeError, ValueError):
            vi = None
        try:
            fi = int(f) if f is not None else None
        except (TypeError, ValueError):
            fi = None
        return vi, fi
    if isinstance(entry, bool):
        return None, None
    try:
        return int(entry), None
    except (TypeError, ValueError):
        return None, None


def calculate_scores(answers: dict) -> dict[str, int]:
    """
    Emotional score from sum(value) / (10 * 3) * 100.
    Financial score from sum(financial) / (10 * 3) * 100.
    Missing keys count as 0 in the numerator; denominator is fixed per category.
    """
    if not isinstance(answers, dict):
        answers = {}

    e_sum = 0
    for key in EMOTIONAL_KEYS:
        v, _ = _coerce_answer_components(answers.get(key))
        if v is not None and v >= 0:
            e_sum += min(v, 3)

    f_sum = 0
    for key in FINANCIAL_KEYS:
        _, fn = _coerce_answer_components(answers.get(key))
        if fn is not None and fn >= 0:
            f_sum += min(fn, 3)

    denom_e = len(EMOTIONAL_KEYS) * 3
    denom_f = len(FINANCIAL_KEYS) * 3
    emotional_score = int(round((e_sum / denom_e) * 100)) if denom_e else 0
    financial_score = int(round((f_sum / denom_f) * 100)) if denom_f else 0
    return {
        "emotional_score": max(0, min(100, emotional_score)),
        "financial_score": max(0, min(100, financial_score)),
    }


def get_verdict(overall_score: float, max_score: float = 100.0) -> dict[str, str]:
    """Map overall score (0..max_score) to label, emoji, description, and color."""
    if max_score <= 0:
        pct = 0.0
    else:
        pct = (overall_score / max_score) * 100.0

    if pct >= 80:
        return {
            "label": "Green Flag Royalty",
            "emoji": "🌿",
            "description": "You two look aligned on habits, money talk, and emotional safety. Keep nurturing the patterns that work.",
            "color": "green",
        }
    if pct >= 65:
        return {
            "label": "Promising",
            "emoji": "✨",
            "description": "Solid foundation with a few edges to smooth. Small, consistent conversations will compound fast.",
            "color": "teal",
        }
    if pct >= 50:
        return {
            "label": "Mixed Bag",
            "emoji": "🎭",
            "description": "Some strengths and some friction points. Worth naming the gaps before they become defaults.",
            "color": "amber",
        }
    if pct >= 30:
        return {
            "label": "Red Flag Parade",
            "emoji": "🚩",
            "description": "Several signals suggest misalignment on money or emotional safety. Pause big joint moves until patterns change.",
            "color": "orange",
        }
    return {
        "label": "Run. Just Run.",
        "emoji": "🏃",
        "description": "The combo of answers points to high risk for resentment and money conflict. Protect yourself first.",
        "color": "red",
    }


def _spending_tier_from_answers(answers: dict) -> int:
    """
    Derive tier index 0..3 (0 = highest baseline spend) from
    date_expectations, spending_style, and lifestyle_inflation.
    """
    keys = ("date_expectations", "spending_style", "lifestyle_inflation")
    vals: list[float] = []
    for key in keys:
        raw = answers.get(key)
        v, f = _coerce_answer_components(raw)
        # Prefer explicit value; else financial; else skip
        component = v if v is not None else f
        if component is not None and component >= 0:
            vals.append(float(min(component, 3)))

    if not vals:
        return 2

    avg = sum(vals) / len(vals)
    if avg >= 2.34:
        return 0
    if avg >= 1.67:
        return 1
    if avg >= 1.0:
        return 2
    return 3


def build_projection(answers: dict) -> list[dict[str, Any]]:
    """
    Twelve monthly dicts: month, event, monthly_cost, cumulative_cost.
    Base category totals scaled by spending tier and monthly seasonal multiplier.
    """
    if not isinstance(answers, dict):
        answers = {}

    tier = _spending_tier_from_answers(answers)
    tier = max(0, min(3, tier))
    base = TIER_BASE[tier]
    base_monthly = sum(base.values())

    out: list[dict[str, Any]] = []
    cumulative = 0
    for i in range(12):
        mult = SEASONAL_MULTIPLIERS[i]
        monthly = int(math.ceil(base_monthly * mult))
        cumulative += monthly
        out.append(
            {
                "month": i + 1,
                "event": _MONTH_EVENTS[i],
                "monthly_cost": monthly,
                "cumulative_cost": cumulative,
            }
        )
    return out


_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


def is_valid_email(email: str) -> bool:
    if not email or len(email) > 255:
        return False
    return bool(_EMAIL_RE.match(email.strip()))


def sanitize_optional_str(
    value: Any,
    *,
    max_length: int = 255,
    allow_empty: bool = True,
) -> str | None:
    """Trim and clip optional string fields; drop control characters."""
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = "".join(ch for ch in value.strip() if ch == "\t" or ord(ch) >= 32)
    if not cleaned and not allow_empty:
        return None
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned or None
