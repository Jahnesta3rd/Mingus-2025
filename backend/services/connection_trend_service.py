#!/usr/bin/env python3
"""Connection Trend: fade tiers, behavioral patterns, insights, trend direction."""

from __future__ import annotations

_INSIGHT_CLOSING = " Based on your responses. Trust your instincts."


def compute_fade_tier(normalized_score: int) -> str:
    """Map 0–100 normalized score to Fade Scale tier labels."""
    n = int(normalized_score)
    if 0 <= n <= 15:
        return "locked_in"
    if 16 <= n <= 30:
        return "breadcrumbing"
    if 31 <= n <= 50:
        return "orbiting"
    if 51 <= n <= 68:
        return "fading"
    if 69 <= n <= 84:
        return "dipping"
    return "cloaking"


def compute_pattern_type(
    q1: int,
    q2: int,
    q3: int,
    q4: int,
    q5: int,
    q6: int,
    q7: int,
) -> str | None:
    """
    First matching rule wins. submarine/zombie are set outside this function.
    """
    if q2 == 2 and q1 <= 1 and q7 <= 1:
        return "breadcrumber"
    if q1 == 2 and q2 == 2 and q3 == 2:
        return "classic_fade"
    if q5 == 2 and q4 == 2 and q1 <= 1:
        return "orbiter"
    if q7 == 2 and q6 == 2 and q3 <= 1 and q4 <= 1:
        return "casper"
    return None


def get_pattern_insight(pattern_type: str | None, fade_tier: str | None) -> dict:
    """
    Display copy for the assessment card.

    fade_tier is accepted for API stability and future tier-conditioned copy.
    Returns insight_message and financial_note (either may be None).
    """
    assert fade_tier is None or isinstance(fade_tier, str)

    if not pattern_type:
        return {"insight_message": None, "financial_note": None}

    templates: dict[str, tuple[str, str | None]] = {
        "breadcrumber": (
            "They respond when you reach out but rarely initiate. That imbalance "
            "tends to be expensive — emotionally and financially.",
            "One-sided relationships often sustain spending without forward movement.",
        ),
        "classic_fade": (
            "Response time, follow-through, and who's making plans have all shifted. "
            "This is what a fade looks like before it's named.",
            "Review upcoming costs linked to this person in your forecast.",
        ),
        "orbiter": (
            "You're in their orbit — visible, considered, but not centered. "
            "That position rarely moves on its own.",
            "Orbiter patterns often sustain mid-level spending indefinitely without "
            "milestone progression.",
        ),
        "casper": (
            "Everything looks fine on paper but something feels off — and you noticed. "
            "Trust what you're sensing.",
            None,
        ),
    }

    pair = templates.get(pattern_type)
    if not pair:
        return {"insight_message": None, "financial_note": None}

    insight_body, financial = pair
    insight_message = insight_body + _INSIGHT_CLOSING
    return {"insight_message": insight_message, "financial_note": financial}


def _normalized_score_from_assessment(a: object) -> int | None:
    if a is None:
        return None
    v = getattr(a, "normalized_score", None)
    if v is not None:
        return int(v) if isinstance(v, (int, float)) else None
    if isinstance(a, dict):
        raw = a.get("normalized_score")
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
    return None


def compute_trend_direction(assessments: list) -> str:
    """
    assessments: oldest first. Higher normalized_score = more strain on the scale.
    """
    if len(assessments) < 2:
        return "too_early"
    prev = _normalized_score_from_assessment(assessments[-2])
    latest = _normalized_score_from_assessment(assessments[-1])
    if prev is None or latest is None:
        return "too_early"
    diff = latest - prev
    if diff > 8:
        return "declining"
    if diff < -8:
        return "improving"
    return "stable"
