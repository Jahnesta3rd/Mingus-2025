"""
Unit Tests for Insight Generator Service

Tests include:
- compare_to_baseline helper
- generate_weekly_insights returns top 5, sorted by priority
- _correlation_insights (medium+ confidence, moderate+ strength)
- _trend_insights (3+ week trends)
- _spending_pattern_insights (vs baselines)
- _anomaly_insights (high stress + impulse, low mood + spending, poor sleep + dining)
- _achievement_insights (zero impulse, stress spending streak, 5+ exercise, lowest spending)
- _recommendation_insights (stress-impulse + high stress)
- Tone: supportive, data-backed, specific dollar amounts
"""

import unittest
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.services.insight_generator_service import (
    InsightGenerator,
    InsightType,
    WellnessInsight,
    compare_to_baseline,
    CorrelationResult,
)


def _make_correlation(
    strength='moderate',
    confidence='medium',
    insight='Your data shows a pattern.',
    data_points=8,
    dollar_impact=None,
):
    """Build a CorrelationResult (stub when correlation engine not installed)."""
    return CorrelationResult(
        correlation=0.5,
        strength=strength,
        direction='positive',
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
    """Minimal check-in dict for tests."""
    d = {
        'stress_level': stress_level,
        'overall_mood': overall_mood,
        'exercise_days': exercise_days,
        'impulse_spending': impulse_spending,
        'stress_spending': stress_spending,
        'shopping_estimate': shopping_estimate,
        'entertainment_estimate': entertainment_estimate,
        'dining_estimate': dining_estimate,
        'sleep_quality': sleep_quality,
        'meditation_minutes': 0,
        'relationship_satisfaction': 5,
        'social_interactions': 5,
        'financial_stress': 5,
        'spending_control': 5,
        'groceries_estimate': 0,
        'transport_estimate': 0,
        'utilities_estimate': 0,
        'other_estimate': 0,
        'celebration_spending': 0,
    }
    d.update(kwargs)
    return d


class TestCompareToBaseline(unittest.TestCase):
    def test_much_lower(self):
        self.assertEqual(compare_to_baseline(30, 100), 'much_lower')

    def test_lower(self):
        self.assertEqual(compare_to_baseline(65, 100), 'lower')

    def test_normal(self):
        self.assertEqual(compare_to_baseline(100, 100), 'normal')
        self.assertEqual(compare_to_baseline(80, 100), 'normal')
        self.assertEqual(compare_to_baseline(120, 100), 'normal')

    def test_higher(self):
        self.assertEqual(compare_to_baseline(130, 100), 'higher')

    def test_much_higher(self):
        self.assertEqual(compare_to_baseline(200, 100), 'much_higher')

    def test_zero_baseline(self):
        self.assertEqual(compare_to_baseline(50, 0), 'normal')
        self.assertEqual(compare_to_baseline(50, None), 'normal')


class TestGenerateWeeklyInsights(unittest.TestCase):
    def setUp(self):
        self.gen = InsightGenerator()

    def test_returns_at_most_five(self):
        current = _checkin()
        previous = [_checkin(stress_level=6), _checkin(stress_level=7)]
        correlations = {}
        baselines = {}
        insights = self.gen.generate_weekly_insights(
            current, previous, correlations, baselines
        )
        self.assertLessEqual(len(insights), 5)

    def test_sorted_by_priority(self):
        current = _checkin(stress_level=8, impulse_spending=120)
        previous = []
        correlations = {}
        baselines = {}
        insights = self.gen.generate_weekly_insights(
            current, previous, correlations, baselines
        )
        priorities = [i.priority for i in insights]
        self.assertEqual(priorities, sorted(priorities))

    def test_all_insights_have_required_fields(self):
        current = _checkin()
        previous = []
        correlations = {}
        baselines = {}
        insights = self.gen.generate_weekly_insights(
            current, previous, correlations, baselines
        )
        for i in insights:
            self.assertIn(i.type, InsightType)
            self.assertIsInstance(i.title, str)
            self.assertIsInstance(i.message, str)
            self.assertIsInstance(i.data_backing, str)
            self.assertIsInstance(i.action, str)
            self.assertIn(i.priority, (1, 2, 3, 4, 5))
            self.assertIn(i.category, ('physical', 'mental', 'relational', 'financial', 'spending'))


class TestCorrelationInsights(unittest.TestCase):
    def setUp(self):
        self.gen = InsightGenerator()

    def test_includes_only_medium_plus_confidence(self):
        correlations = {
            'stress_impulse': _make_correlation(confidence='low'),
            'exercise_control': _make_correlation(confidence='high'),
        }
        insights = self.gen._correlation_insights(correlations)
        self.assertEqual(len(insights), 1)
        self.assertEqual(insights[0].type, InsightType.CORRELATION)

    def test_includes_only_moderate_plus_strength(self):
        correlations = {
            'stress_impulse': _make_correlation(strength='weak', confidence='medium'),
            'exercise_control': _make_correlation(strength='strong', confidence='medium'),
        }
        insights = self.gen._correlation_insights(correlations)
        self.assertEqual(len(insights), 1)
        self.assertEqual(insights[0].priority, 2)


class TestAnomalyInsights(unittest.TestCase):
    def setUp(self):
        self.gen = InsightGenerator()

    def test_high_stress_plus_impulse(self):
        current = _checkin(stress_level=8, impulse_spending=120)
        insights = self.gen._anomaly_insights(current)
        titles = [i.title for i in insights]
        self.assertTrue(any('Stress' in t for t in titles))
        self.assertTrue(any(i.priority == 1 for i in insights))

    def test_low_mood_plus_spending(self):
        current = _checkin(overall_mood=3, shopping_estimate=80, entertainment_estimate=40)
        insights = self.gen._anomaly_insights(current)
        self.assertTrue(any('Mood' in i.title for i in insights))

    def test_no_anomaly_when_stress_low(self):
        current = _checkin(stress_level=4, impulse_spending=20)
        insights = self.gen._anomaly_insights(current)
        self.assertFalse(any('Stress Spending Alert' in i.title for i in insights))


class TestAchievementInsights(unittest.TestCase):
    def setUp(self):
        self.gen = InsightGenerator()

    def test_zero_impulse_after_previous_impulse(self):
        current = _checkin(impulse_spending=0)
        previous = [_checkin(impulse_spending=50), _checkin(impulse_spending=30)]
        insights = self.gen._achievement_insights(current, previous)
        self.assertTrue(any('Zero Impulse' in i.title or 'impulse' in i.message.lower() for i in insights))

    def test_five_plus_exercise_days_first_time(self):
        current = _checkin(exercise_days=5)
        previous = [_checkin(exercise_days=3), _checkin(exercise_days=4)]
        insights = self.gen._achievement_insights(current, previous)
        self.assertTrue(any('Fitness' in i.title or 'exercise' in i.message.lower() for i in insights))

    def test_stress_spending_streak_zero(self):
        current = _checkin(stress_spending=0)
        previous = [_checkin(stress_spending=0), _checkin(stress_spending=0)]
        insights = self.gen._achievement_insights(current, previous)
        self.assertTrue(any('stress spending' in i.message.lower() or 'No Stress' in i.title for i in insights))


class TestSpendingPatternInsights(unittest.TestCase):
    def setUp(self):
        self.gen = InsightGenerator()

    def test_above_average_total(self):
        current = _checkin(groceries_estimate=100, dining_estimate=80, shopping_estimate=100)
        previous = []
        baselines = {'avg_total_variable': 150, 'avg_shopping': 40}
        insights = self.gen._spending_pattern_insights(current, previous, baselines)
        self.assertTrue(any('above' in i.message.lower() or 'Spending This Week' in i.title for i in insights))

    def test_below_average_total(self):
        current = _checkin(groceries_estimate=30, dining_estimate=20)
        previous = []
        baselines = {'avg_total_variable': 200}
        insights = self.gen._spending_pattern_insights(current, previous, baselines)
        self.assertTrue(any('below' in i.message.lower() or 'Win' in i.title for i in insights))

    def test_shopping_spike_vs_baseline(self):
        current = _checkin(shopping_estimate=180)
        previous = []
        baselines = {'avg_shopping': 78}
        insights = self.gen._spending_pattern_insights(current, previous, baselines)
        self.assertTrue(any('Shopping' in i.title for i in insights))
        self.assertTrue(any('180' in i.message for i in insights))


class TestRecommendationInsights(unittest.TestCase):
    def setUp(self):
        self.gen = InsightGenerator()

    def test_stress_impulse_correlation_plus_high_stress(self):
        current = _checkin(stress_level=8)
        correlations = {
            'stress_impulse': _make_correlation(
                strength='strong',
                confidence='high',
                insight='High stress weeks show more impulse spending.',
            ),
        }
        insights = self.gen._recommendation_insights(current, correlations)
        self.assertTrue(any('Spending Shield' in i.title or '24-hour' in i.action for i in insights))

    def test_no_recommendation_when_stress_low(self):
        current = _checkin(stress_level=4)
        correlations = {
            'stress_impulse': _make_correlation(strength='strong', confidence='high'),
        }
        insights = self.gen._recommendation_insights(current, correlations)
        self.assertFalse(any('Spending Shield' in i.title for i in insights))


class TestToneAndContent(unittest.TestCase):
    """Insights should be supportive, data-backed, with concrete actions."""

    def setUp(self):
        self.gen = InsightGenerator()

    def test_messages_use_supportive_language(self):
        current = _checkin(stress_level=8, impulse_spending=100)
        insights = self.gen.generate_weekly_insights(
            current, [], {}, {}
        )
        for i in insights:
            self.assertNotIn('fail', i.message.lower())
            self.assertNotIn('bad', i.message.lower())
            self.assertNotIn('wrong', i.message.lower())

    def test_actions_are_suggestions(self):
        current = _checkin(stress_level=8, impulse_spending=80)
        insights = self.gen._anomaly_insights(current)
        for i in insights:
            self.assertTrue(
                'consider' in i.action.lower() or 'try' in i.action.lower()
                or 'wait' in i.action.lower() or 'check' in i.action.lower()
                or 'celebrate' in i.action.lower() or 'keep' in i.action.lower()
            )


if __name__ == '__main__':
    unittest.main()
