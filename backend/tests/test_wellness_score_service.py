"""
Comprehensive tests for Wellness Score Calculator Service.

Uses pytest and parametrize. Covers:
- All score calculations with edge cases (0, max, typical)
- Week-over-week change calculations
- Input validation errors
"""

import pytest
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.wellness_score_service import (
    WellnessScoreCalculator,
    DEFAULT_WEIGHTS,
    EXERCISE_INTENSITY_POINTS,
)


def _full_checkin(
    exercise_days=0,
    exercise_intensity=None,
    sleep_quality=5,
    meditation_minutes=0,
    stress_level=5,
    overall_mood=5,
    relationship_satisfaction=5,
    social_interactions=5,
    financial_stress=5,
    spending_control=5,
    **kwargs,
):
    d = {
        "exercise_days": exercise_days,
        "sleep_quality": sleep_quality,
        "meditation_minutes": meditation_minutes,
        "stress_level": stress_level,
        "overall_mood": overall_mood,
        "relationship_satisfaction": relationship_satisfaction,
        "social_interactions": social_interactions,
        "financial_stress": financial_stress,
        "spending_control": spending_control,
    }
    if exercise_intensity is not None:
        d["exercise_intensity"] = exercise_intensity
    d.update(kwargs)
    return d


# ---- get_week_ending_date ----

@pytest.mark.parametrize("d,expected", [
    (date(2025, 2, 2), date(2025, 2, 2)),   # Sunday
    (date(2025, 1, 27), date(2025, 2, 2)),  # Monday
    (date(2025, 2, 1), date(2025, 2, 2)),   # Saturday
    (date(2025, 1, 15), date(2025, 1, 19)), # Wed -> Sunday
])
def test_get_week_ending_date(d, expected):
    assert WellnessScoreCalculator.get_week_ending_date(d) == expected


# ---- Physical score: 0, max, typical ----

@pytest.mark.parametrize("checkin,expected", [
    (_full_checkin(exercise_days=0, sleep_quality=1), 0.0),
    (_full_checkin(exercise_days=7, exercise_intensity="intense", sleep_quality=10), 100.0),
    (_full_checkin(exercise_days=3, exercise_intensity="moderate", sleep_quality=7),
     (3/7)*40 + 15 + (6/9)*40),
    (_full_checkin(exercise_days=7, sleep_quality=10), 80.0),  # no intensity
])
def test_calculate_physical_score_values(checkin, expected):
    calc = WellnessScoreCalculator()
    result = calc.calculate_physical_score(checkin)
    assert abs(result - expected) < 0.01


@pytest.mark.parametrize("checkin,err_key", [
    (_full_checkin(exercise_days=8, sleep_quality=5), "exercise_days"),
    (_full_checkin(exercise_days=0, sleep_quality=11), "sleep_quality"),
    (_full_checkin(exercise_days=3, exercise_intensity="super", sleep_quality=5), "exercise_intensity"),
    (_full_checkin(exercise_days=-1, sleep_quality=5), "exercise_days"),
])
def test_physical_score_validation_errors(checkin, err_key):
    calc = WellnessScoreCalculator()
    with pytest.raises(ValueError) as exc_info:
        calc.calculate_physical_score(checkin)
    assert err_key in str(exc_info.value)


# ---- Mental score ----

@pytest.mark.parametrize("checkin,expected", [
    (_full_checkin(meditation_minutes=0, stress_level=10, overall_mood=1), 0.0),
    (_full_checkin(meditation_minutes=60, stress_level=1, overall_mood=10), 100.0),
    (_full_checkin(meditation_minutes=120, stress_level=1, overall_mood=10), 100.0),  # cap 60
])
def test_calculate_mental_score_values(checkin, expected):
    calc = WellnessScoreCalculator()
    assert abs(calc.calculate_mental_score(checkin) - expected) < 0.01


def test_mental_stress_inverted():
    calc = WellnessScoreCalculator()
    low = calc.calculate_mental_score(_full_checkin(meditation_minutes=0, stress_level=1, overall_mood=5))
    high = calc.calculate_mental_score(_full_checkin(meditation_minutes=0, stress_level=10, overall_mood=5))
    assert low > high


# ---- Relational score ----

@pytest.mark.parametrize("checkin,expected", [
    (_full_checkin(relationship_satisfaction=1, social_interactions=0), 0.0),
    (_full_checkin(relationship_satisfaction=10, social_interactions=10), 100.0),
    (_full_checkin(relationship_satisfaction=10, social_interactions=20), 100.0),  # cap 10
])
def test_calculate_relational_score_values(checkin, expected):
    calc = WellnessScoreCalculator()
    assert abs(calc.calculate_relational_score(checkin) - expected) < 0.01


def test_relational_social_negative_raises():
    calc = WellnessScoreCalculator()
    with pytest.raises(ValueError) as exc_info:
        calc.calculate_relational_score(_full_checkin(relationship_satisfaction=5, social_interactions=-1))
    assert "social_interactions" in str(exc_info.value)


# ---- Financial feeling score ----

@pytest.mark.parametrize("checkin,expected", [
    (_full_checkin(financial_stress=10, spending_control=1), 0.0),
    (_full_checkin(financial_stress=1, spending_control=10), 100.0),
])
def test_calculate_financial_feeling_score_values(checkin, expected):
    calc = WellnessScoreCalculator()
    assert abs(calc.calculate_financial_feeling_score(checkin) - expected) < 0.01


# ---- Overall wellness ----

def test_calculate_overall_wellness_returns_all_keys():
    calc = WellnessScoreCalculator()
    checkin = _full_checkin(
        exercise_days=5, exercise_intensity="moderate", sleep_quality=7,
        meditation_minutes=30, stress_level=4, overall_mood=7,
        relationship_satisfaction=8, social_interactions=6,
        financial_stress=3, spending_control=7,
    )
    result = calc.calculate_overall_wellness(checkin)
    for key in ("physical_score", "mental_score", "relational_score", "financial_feeling_score", "overall_wellness_score"):
        assert key in result
        assert result[key] == round(result[key], 2)


def test_calculate_overall_wellness_all_100():
    calc = WellnessScoreCalculator()
    checkin = _full_checkin(
        exercise_days=7, exercise_intensity="intense", sleep_quality=10,
        meditation_minutes=60, stress_level=1, overall_mood=10,
        relationship_satisfaction=10, social_interactions=10,
        financial_stress=1, spending_control=10,
    )
    result = calc.calculate_overall_wellness(checkin)
    assert result["overall_wellness_score"] == 100.0


# ---- Week-over-week changes ----

@pytest.mark.parametrize("current,previous,expected_changes", [
    (
        {"physical_score": 70, "mental_score": 80, "relational_score": 60, "overall_wellness_score": 68},
        {"physical_score": 60, "mental_score": 70, "relational_score": 50, "overall_wellness_score": 58},
        {"physical_change": 10.0, "mental_change": 10.0, "relational_change": 10.0, "overall_change": 10.0},
    ),
    (
        {"physical_score": 50, "mental_score": 50, "relational_score": 50, "overall_wellness_score": 50},
        {"physical_score": 70, "mental_score": 70, "relational_score": 70, "overall_wellness_score": 70},
        {"physical_change": -20.0, "mental_change": -20.0, "relational_change": -20.0, "overall_change": -20.0},
    ),
    (
        {"physical_score": 80, "mental_score": 80, "relational_score": 80, "overall_wellness_score": 80},
        {},
        {"physical_change": 80.0, "mental_change": 80.0, "relational_change": 80.0, "overall_change": 80.0},
    ),
])
def test_calculate_week_over_week_changes(current, previous, expected_changes):
    calc = WellnessScoreCalculator()
    result = calc.calculate_week_over_week_changes(current, previous)
    for k, v in expected_changes.items():
        assert result[k] == v


def test_week_over_week_returns_rounded_two_decimals():
    calc = WellnessScoreCalculator()
    current = {"physical_score": 70.556, "mental_score": 70.556, "relational_score": 70.556, "overall_wellness_score": 70.556}
    previous = {"physical_score": 70.123, "mental_score": 70.123, "relational_score": 70.123, "overall_wellness_score": 70.123}
    result = calc.calculate_week_over_week_changes(current, previous)
    for v in result.values():
        assert v == round(v, 2)


# ---- Input validation (wrong types / missing) ----

@pytest.mark.parametrize("checkin,method", [
    ({**_full_checkin(), "exercise_days": "five"}, "calculate_physical_score"),
    ({**_full_checkin(), "sleep_quality": None}, "calculate_physical_score"),
    ({**_full_checkin(), "meditation_minutes": None}, "calculate_mental_score"),
    ({**_full_checkin(), "social_interactions": None}, "calculate_relational_score"),
])
def test_invalid_input_raises(checkin, method):
    calc = WellnessScoreCalculator()
    with pytest.raises(ValueError):
        getattr(calc, method)(checkin)


def test_missing_sleep_quality_raises():
    calc = WellnessScoreCalculator()
    c = _full_checkin()
    del c["sleep_quality"]
    with pytest.raises(ValueError):
        calc.calculate_physical_score(c)
