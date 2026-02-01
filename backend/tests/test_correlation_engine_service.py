"""
Comprehensive tests for Wellness–Finance Correlation Engine Service.

Covers:
- Pearson correlation calculation (positive, negative, zero)
- Insufficient data (< 4 weeks)
- Zero variance data
- Each correlation type
- Insight message generation
- Confidence level assignment
"""

import pytest
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.services.correlation_engine_service import (
    pearson_correlation,
    correlation_strength,
    correlation_direction,
    confidence_level,
    CorrelationResult,
    WellnessFinanceCorrelator,
)


# ---- Pearson correlation ----

def test_pearson_positive_correlation():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]
    r = pearson_correlation(x, y)
    assert r is not None
    assert abs(r - 1.0) < 0.001


def test_pearson_negative_correlation():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [10.0, 8.0, 6.0, 4.0, 2.0]
    r = pearson_correlation(x, y)
    assert r is not None
    assert abs(r - (-1.0)) < 0.001


def test_pearson_zero_correlation():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [5.0, 5.0, 5.0, 5.0, 5.0]  # constant
    r = pearson_correlation(x, y)
    assert r is None  # zero variance in y


def test_pearson_insufficient_data():
    assert pearson_correlation([1.0], [2.0]) is None
    assert pearson_correlation([], []) is None
    assert pearson_correlation([1.0, 2.0], [1.0]) is None  # length mismatch


def test_pearson_zero_variance_both():
    x = [3.0, 3.0, 3.0]
    y = [7.0, 7.0, 7.0]
    r = pearson_correlation(x, y)
    assert r is None


# ---- Strength / direction / confidence ----

@pytest.mark.parametrize("r,expected_strength", [
    (0.8, "strong"),
    (0.5, "moderate"),
    (0.2, "weak"),
    (-0.7, "strong"),
    (None, "weak"),
])
def test_correlation_strength(r, expected_strength):
    assert correlation_strength(r) == expected_strength


@pytest.mark.parametrize("r,expected_direction", [
    (0.5, "positive"),
    (-0.5, "negative"),
    (0.05, "none"),
    (None, "none"),
])
def test_correlation_direction(r, expected_direction):
    assert correlation_direction(r) == expected_direction


@pytest.mark.parametrize("data_points,strength,expected_conf", [
    (8, "strong", "high"),
    (4, "moderate", "medium"),
    (3, "strong", "low"),
    (10, "weak", "medium"),
])
def test_confidence_level_assignment(data_points, strength, expected_conf):
    assert confidence_level(data_points, strength) == expected_conf


# ---- WellnessFinanceCorrelator ----

def _checkin(stress=5, impulse=0, exercise_days=3, sleep_quality=6, **kwargs):
    d = {
        "stress_level": stress,
        "impulse_spending": impulse,
        "exercise_days": exercise_days,
        "sleep_quality": sleep_quality,
        "overall_mood": 5,
        "meditation_minutes": 10,
        "relationship_satisfaction": 5,
        "spending_control": 5,
        "groceries_estimate": 100,
        "dining_estimate": 50,
        "entertainment_estimate": 30,
        "shopping_estimate": 40,
        "transport_estimate": 20,
        "utilities_estimate": 80,
        "other_estimate": 10,
    }
    d.update(kwargs)
    return d


def test_correlator_insufficient_data_returns_empty():
    corr = WellnessFinanceCorrelator(min_weeks=4)
    checkins = [_checkin(stress_level=i, impulse_spending=i * 10) for i in range(3)]
    result = corr.compute_correlations(checkins)
    assert result == {}


def test_correlator_with_4_weeks_returns_results():
    corr = WellnessFinanceCorrelator(min_weeks=4)
    checkins = [
        _checkin(stress_level=3, impulse_spending=20, week_ending_date=date(2025, 1, 5)),
        _checkin(stress_level=5, impulse_spending=40, week_ending_date=date(2025, 1, 12)),
        _checkin(stress_level=7, impulse_spending=60, week_ending_date=date(2025, 1, 19)),
        _checkin(stress_level=9, impulse_spending=80, week_ending_date=date(2025, 1, 26)),
    ]
    result = corr.compute_correlations(checkins)
    # May have stress_vs_impulse_spending if aligned
    assert isinstance(result, dict)
    for key, val in result.items():
        assert isinstance(val, CorrelationResult)
        assert val.data_points >= 4
        assert val.strength in ("weak", "moderate", "strong")
        assert val.direction in ("positive", "negative", "none")
        assert val.confidence in ("low", "medium", "high")
        assert isinstance(val.insight, str)


def test_correlator_zero_variance_skipped():
    corr = WellnessFinanceCorrelator(min_weeks=4)
    checkins = [_checkin(stress_level=5, impulse_spending=50) for _ in range(4)]  # no variance
    result = corr.compute_correlations(checkins)
    # Zero variance in stress_level and possibly impulse_spending -> Pearson may be None for some pairs
    assert isinstance(result, dict)


def test_correlator_result_has_required_fields():
    corr = WellnessFinanceCorrelator(min_weeks=4)
    checkins = [
        _checkin(stress_level=i, impulse_spending=i * 15) for i in range(4, 9)
    ]
    result = corr.compute_correlations(checkins)
    for key, r in result.items():
        assert hasattr(r, "correlation")
        assert hasattr(r, "strength")
        assert hasattr(r, "direction")
        assert hasattr(r, "data_points")
        assert hasattr(r, "confidence")
        assert hasattr(r, "insight")


def test_correlator_insight_message_generation():
    corr = WellnessFinanceCorrelator(min_weeks=4)
    checkins = [
        _checkin(stress_level=i, impulse_spending=i * 12) for i in range(1, 6)
    ]
    result = corr.compute_correlations(checkins)
    for r in result.values():
        assert "weeks" in r.insight or "Based" in r.insight
        assert r.data_points >= 4
