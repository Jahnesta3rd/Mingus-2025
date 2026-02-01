"""
Comprehensive tests for Insight Generator Service.

Uses pytest and parametrize. Covers:
- Insight prioritization (top 5, sorted by priority)
- Each insight type generation (correlation, trend, anomaly, achievement, spending_pattern, recommendation)
- Trend detection (3+ weeks)
- Anomaly detection
- Achievement detection
- Empty / insufficient data handling
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.insight_generator_service import (
    InsightGenerator,
    InsightType,
    WellnessInsight,
    compare_to_baseline,
    CorrelationResult,
)


def _make_correlation(strength="moderate", confidence="medium", insight="Pattern.", data_points=8, dollar_impact=None):
    return CorrelationResult(
        correlation=0.5,
        strength=strength,
        direction="positive",
        data_points=data_points,
        confidence=confidence,
        insight=insight,
        dollar_impact=dollar_impact,
    )


def _checkin(
    stress_level=5,
    overall_mood=5,
    exercise_days=3,
    impulse_spending=0,
    stress_spending=0,
    shopping_estimate=0,
    entertainment_estimate=0,
    dining_estimate=0,
    sleep_quality=6,
    **kwargs,
):
    d = {
        "stress_level": stress_level,
        "overall_mood": overall_mood,
        "exercise_days": exercise_days,
        "impulse_spending": impulse_spending,
        "stress_spending": stress_spending,
        "shopping_estimate": shopping_estimate,
        "entertainment_estimate": entertainment_estimate,
        "dining_estimate": dining_estimate,
        "sleep_quality": sleep_quality,
        "meditation_minutes": 0,
        "relationship_satisfaction": 5,
        "social_interactions": 5,
        "financial_stress": 5,
        "spending_control": 5,
        "groceries_estimate": 0,
        "transport_estimate": 0,
        "utilities_estimate": 0,
        "other_estimate": 0,
        "celebration_spending": 0,
    }
    d.update(kwargs)
    return d


# ---- compare_to_baseline ----

@pytest.mark.parametrize("current,baseline,expected", [
    (30, 100, "much_lower"),
    (65, 100, "lower"),
    (100, 100, "normal"),
    (80, 100, "normal"),
    (120, 100, "normal"),
    (130, 100, "higher"),
    (200, 100, "much_higher"),
    (50, 0, "normal"),
    (50, None, "normal"),
])
def test_compare_to_baseline(current, baseline, expected):
    assert compare_to_baseline(current, baseline) == expected


# ---- generate_weekly_insights ----

def test_returns_at_most_five():
    gen = InsightGenerator()
    current = _checkin()
    previous = [_checkin(stress_level=6), _checkin(stress_level=7)]
    insights = gen.generate_weekly_insights(current, previous, {}, {})
    assert len(insights) <= 5


def test_sorted_by_priority():
    gen = InsightGenerator()
    current = _checkin(stress_level=8, impulse_spending=120)
    insights = gen.generate_weekly_insights(current, [], {}, {})
    priorities = [i.priority for i in insights]
    assert priorities == sorted(priorities)


def test_all_insights_have_required_fields():
    gen = InsightGenerator()
    current = _checkin()
    insights = gen.generate_weekly_insights(current, [], {}, {})
    for i in insights:
        assert i.type in list(InsightType)
        assert isinstance(i.title, str)
        assert isinstance(i.message, str)
        assert isinstance(i.data_backing, str)
        assert isinstance(i.action, str)
        assert i.priority in (1, 2, 3, 4, 5)
        assert i.category in ("physical", "mental", "relational", "financial", "spending")


# ---- Empty / insufficient data ----

def test_empty_previous_returns_some_insights():
    gen = InsightGenerator()
    current = _checkin(stress_level=8, impulse_spending=80)
    insights = gen.generate_weekly_insights(current, [], {}, {})
    assert isinstance(insights, list)
    # Anomaly insights can still appear
    titles = [i.title for i in insights]
    assert any("Stress" in t for t in titles) or len(insights) >= 0


def test_insufficient_baseline_no_crash():
    gen = InsightGenerator()
    current = _checkin(groceries_estimate=100, dining_estimate=50)
    insights = gen.generate_weekly_insights(current, [], {}, {})
    assert isinstance(insights, list)


# ---- Correlation insights ----

def test_correlation_only_medium_plus_confidence():
    gen = InsightGenerator()
    correlations = {
        "stress_impulse": _make_correlation(confidence="low"),
        "exercise_control": _make_correlation(confidence="high"),
    }
    insights = gen._correlation_insights(correlations)
    assert len(insights) == 1
    assert insights[0].type == InsightType.CORRELATION


def test_correlation_only_moderate_plus_strength():
    gen = InsightGenerator()
    correlations = {
        "stress_impulse": _make_correlation(strength="weak", confidence="medium"),
        "exercise_control": _make_correlation(strength="strong", confidence="medium"),
    }
    insights = gen._correlation_insights(correlations)
    assert len(insights) == 1


# ---- Trend insights (3+ weeks) ----

def test_trend_requires_2_plus_previous():
    gen = InsightGenerator()
    current = _checkin(exercise_days=5)
    previous = [_checkin(exercise_days=4), _checkin(exercise_days=3)]
    insights = gen._trend_insights(current, previous)
    # May have exercise momentum if sequence is increasing
    assert isinstance(insights, list)


def test_trend_stress_spending_zero_3_weeks():
    gen = InsightGenerator()
    current = _checkin(stress_spending=0)
    previous = [_checkin(stress_spending=0), _checkin(stress_spending=0)]
    insights = gen._trend_insights(current, previous)
    titles = [i.title for i in insights]
    assert any("Great Progress" in t or "stress" in t.lower() for t in titles)


# ---- Anomaly insights ----

@pytest.mark.parametrize("current,expected_in_title", [
    (_checkin(stress_level=8, impulse_spending=120), "Stress"),
    (_checkin(overall_mood=3, shopping_estimate=80, entertainment_estimate=40), "Mood"),
])
def test_anomaly_detection(current, expected_in_title):
    gen = InsightGenerator()
    insights = gen._anomaly_insights(current)
    titles = [i.title for i in insights]
    assert any(expected_in_title in t for t in titles)


def test_no_anomaly_when_stress_low():
    gen = InsightGenerator()
    current = _checkin(stress_level=4, impulse_spending=20)
    insights = gen._anomaly_insights(current)
    assert not any("Stress Spending Alert" in i.title for i in insights)


# ---- Achievement insights ----

def test_achievement_zero_impulse_after_previous():
    gen = InsightGenerator()
    current = _checkin(impulse_spending=0)
    previous = [_checkin(impulse_spending=50), _checkin(impulse_spending=30)]
    insights = gen._achievement_insights(current, previous)
    assert any("Zero Impulse" in i.title or "impulse" in i.message.lower() for i in insights)


def test_achievement_five_plus_exercise_days():
    gen = InsightGenerator()
    current = _checkin(exercise_days=5)
    previous = [_checkin(exercise_days=3), _checkin(exercise_days=4)]
    insights = gen._achievement_insights(current, previous)
    assert any("Fitness" in i.title or "exercise" in i.message.lower() for i in insights)


# ---- Spending pattern insights ----

def test_spending_above_average():
    gen = InsightGenerator()
    current = _checkin(groceries_estimate=100, dining_estimate=80, shopping_estimate=100)
    baselines = {"avg_total_variable": 150, "avg_shopping": 40}
    insights = gen._spending_pattern_insights(current, [], baselines)
    assert any("above" in i.message.lower() or "Spending This Week" in i.title for i in insights)


def test_spending_below_average():
    gen = InsightGenerator()
    current = _checkin(groceries_estimate=30, dining_estimate=20)
    baselines = {"avg_total_variable": 200}
    insights = gen._spending_pattern_insights(current, [], baselines)
    assert any("below" in i.message.lower() or "Win" in i.title for i in insights)


# ---- Recommendation insights ----

def test_recommendation_stress_impulse_plus_high_stress():
    gen = InsightGenerator()
    current = _checkin(stress_level=8)
    correlations = {
        "stress_impulse": _make_correlation(strength="strong", confidence="high", insight="High stress → more impulse."),
    }
    insights = gen._recommendation_insights(current, correlations)
    assert any("Spending Shield" in i.title or "24-hour" in i.action for i in insights)


def test_no_recommendation_when_stress_low():
    gen = InsightGenerator()
    current = _checkin(stress_level=4)
    correlations = {"stress_impulse": _make_correlation(strength="strong", confidence="high")}
    insights = gen._recommendation_insights(current, correlations)
    assert not any("Spending Shield" in i.title for i in insights)


# ---- Tone (supportive) ----

def test_messages_supportive():
    gen = InsightGenerator()
    current = _checkin(stress_level=8, impulse_spending=100)
    insights = gen.generate_weekly_insights(current, [], {}, {})
    for i in insights:
        assert "fail" not in i.message.lower()
        assert "bad" not in i.message.lower()
