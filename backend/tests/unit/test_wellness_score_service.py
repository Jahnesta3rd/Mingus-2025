"""
Unit Tests for Wellness Score Calculator Service

Tests include:
- Edge cases (all zeros, all max values)
- Normal calculations for physical, mental, relational, financial_feeling
- Week-over-week changes
- Invalid input handling (out-of-range, wrong types)
- get_week_ending_date helper
"""

import unittest
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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
):
    """Build a checkin dict with defaults; override as needed."""
    d = {
        'exercise_days': exercise_days,
        'sleep_quality': sleep_quality,
        'meditation_minutes': meditation_minutes,
        'stress_level': stress_level,
        'overall_mood': overall_mood,
        'relationship_satisfaction': relationship_satisfaction,
        'social_interactions': social_interactions,
        'financial_stress': financial_stress,
        'spending_control': spending_control,
    }
    if exercise_intensity is not None:
        d['exercise_intensity'] = exercise_intensity
    return d


class TestGetWeekEndingDate(unittest.TestCase):
    """Tests for get_week_ending_date helper."""

    def test_sunday_returns_same_date(self):
        # Sunday 2 Feb 2025
        d = date(2025, 2, 2)
        self.assertEqual(WellnessScoreCalculator.get_week_ending_date(d), d)

    def test_monday_returns_next_sunday(self):
        # Monday 27 Jan 2025 -> Sunday 2 Feb 2025
        d = date(2025, 1, 27)
        expected = date(2025, 2, 2)
        self.assertEqual(WellnessScoreCalculator.get_week_ending_date(d), expected)

    def test_saturday_returns_next_day_sunday(self):
        d = date(2025, 2, 1)  # Saturday
        expected = date(2025, 2, 2)  # Sunday
        self.assertEqual(WellnessScoreCalculator.get_week_ending_date(d), expected)


class TestPhysicalScore(unittest.TestCase):
    """Tests for calculate_physical_score."""

    def setUp(self):
        self.calc = WellnessScoreCalculator()

    def test_all_zeros(self):
        checkin = _full_checkin(exercise_days=0, sleep_quality=1)
        checkin.pop('exercise_intensity', None)
        score = self.calc.calculate_physical_score(checkin)
        # 0/7*40 + 0 + (0/9)*40 = 0
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_all_max(self):
        checkin = _full_checkin(
            exercise_days=7,
            exercise_intensity='intense',
            sleep_quality=10,
        )
        score = self.calc.calculate_physical_score(checkin)
        # 40 + 20 + 40 = 100
        self.assertAlmostEqual(score, 100.0, places=5)

    def test_normal_values(self):
        checkin = _full_checkin(
            exercise_days=3,
            exercise_intensity='moderate',
            sleep_quality=7,
        )
        score = self.calc.calculate_physical_score(checkin)
        # (3/7)*40 + 15 + ((7-1)/9)*40 ≈ 17.14 + 15 + 26.67 ≈ 58.81
        expected = (3 / 7) * 40 + 15 + (6 / 9) * 40
        self.assertAlmostEqual(score, expected, places=5)

    def test_exercise_days_only_no_intensity(self):
        checkin = _full_checkin(exercise_days=7, sleep_quality=10)
        checkin.pop('exercise_intensity', None)
        score = self.calc.calculate_physical_score(checkin)
        # 40 + 0 + 40 = 80
        self.assertAlmostEqual(score, 80.0, places=5)

    def test_exercise_days_out_of_range_high(self):
        checkin = _full_checkin(exercise_days=8, sleep_quality=5)
        with self.assertRaises(ValueError) as ctx:
            self.calc.calculate_physical_score(checkin)
        self.assertIn('exercise_days', str(ctx.exception))

    def test_sleep_quality_out_of_range(self):
        checkin = _full_checkin(exercise_days=0, sleep_quality=11)
        with self.assertRaises(ValueError) as ctx:
            self.calc.calculate_physical_score(checkin)
        self.assertIn('sleep_quality', str(ctx.exception))

    def test_invalid_exercise_intensity(self):
        checkin = _full_checkin(
            exercise_days=3,
            exercise_intensity='super',
            sleep_quality=5,
        )
        with self.assertRaises(ValueError) as ctx:
            self.calc.calculate_physical_score(checkin)
        self.assertIn('exercise_intensity', str(ctx.exception))


class TestMentalScore(unittest.TestCase):
    """Tests for calculate_mental_score."""

    def setUp(self):
        self.calc = WellnessScoreCalculator()

    def test_all_zeros(self):
        checkin = _full_checkin(
            meditation_minutes=0,
            stress_level=10,  # high stress = 0 points
            overall_mood=1,
        )
        score = self.calc.calculate_mental_score(checkin)
        # 0 + 0 + 0 = 0
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_all_max(self):
        checkin = _full_checkin(
            meditation_minutes=60,
            stress_level=1,  # low stress
            overall_mood=10,
        )
        score = self.calc.calculate_mental_score(checkin)
        # 30 + 35 + 35 = 100
        self.assertAlmostEqual(score, 100.0, places=5)

    def test_meditation_capped_at_60(self):
        checkin = _full_checkin(
            meditation_minutes=120,
            stress_level=1,
            overall_mood=10,
        )
        score = self.calc.calculate_mental_score(checkin)
        # Still 30 for meditation (cap at 60 min)
        self.assertAlmostEqual(score, 100.0, places=5)

    def test_stress_inverted(self):
        # Low stress (1) should give high stress_points
        checkin_low = _full_checkin(meditation_minutes=0, stress_level=1, overall_mood=5)
        score_low = self.calc.calculate_mental_score(checkin_low)
        checkin_high = _full_checkin(meditation_minutes=0, stress_level=10, overall_mood=5)
        score_high = self.calc.calculate_mental_score(checkin_high)
        self.assertGreater(score_low, score_high)

    def test_stress_level_out_of_range(self):
        checkin = _full_checkin(stress_level=0)
        with self.assertRaises(ValueError) as ctx:
            self.calc.calculate_mental_score(checkin)
        self.assertIn('stress_level', str(ctx.exception))


class TestRelationalScore(unittest.TestCase):
    """Tests for calculate_relational_score."""

    def setUp(self):
        self.calc = WellnessScoreCalculator()

    def test_all_min(self):
        checkin = _full_checkin(
            relationship_satisfaction=1,
            social_interactions=0,
        )
        score = self.calc.calculate_relational_score(checkin)
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_all_max(self):
        checkin = _full_checkin(
            relationship_satisfaction=10,
            social_interactions=10,
        )
        score = self.calc.calculate_relational_score(checkin)
        # 60 + 40 = 100
        self.assertAlmostEqual(score, 100.0, places=5)

    def test_social_interactions_capped_at_10(self):
        checkin = _full_checkin(
            relationship_satisfaction=10,
            social_interactions=20,
        )
        score = self.calc.calculate_relational_score(checkin)
        self.assertAlmostEqual(score, 100.0, places=5)

    def test_social_interactions_negative_raises(self):
        checkin = _full_checkin(relationship_satisfaction=5, social_interactions=-1)
        with self.assertRaises(ValueError) as ctx:
            self.calc.calculate_relational_score(checkin)
        self.assertIn('social_interactions', str(ctx.exception))


class TestFinancialFeelingScore(unittest.TestCase):
    """Tests for calculate_financial_feeling_score."""

    def setUp(self):
        self.calc = WellnessScoreCalculator()

    def test_all_min(self):
        checkin = _full_checkin(financial_stress=10, spending_control=1)
        score = self.calc.calculate_financial_feeling_score(checkin)
        # 0 + 0 = 0
        self.assertAlmostEqual(score, 0.0, places=5)

    def test_all_max(self):
        checkin = _full_checkin(financial_stress=1, spending_control=10)
        score = self.calc.calculate_financial_feeling_score(checkin)
        # 50 + 50 = 100
        self.assertAlmostEqual(score, 100.0, places=5)

    def test_financial_stress_out_of_range(self):
        checkin = _full_checkin(financial_stress=11, spending_control=5)
        with self.assertRaises(ValueError) as ctx:
            self.calc.calculate_financial_feeling_score(checkin)
        self.assertIn('financial_stress', str(ctx.exception))


class TestCalculateOverallWellness(unittest.TestCase):
    """Tests for calculate_overall_wellness."""

    def setUp(self):
        self.calc = WellnessScoreCalculator()

    def test_returns_all_scores_rounded(self):
        checkin = _full_checkin(
            exercise_days=5,
            exercise_intensity='moderate',
            sleep_quality=7,
            meditation_minutes=30,
            stress_level=4,
            overall_mood=7,
            relationship_satisfaction=8,
            social_interactions=6,
            financial_stress=3,
            spending_control=7,
        )
        result = self.calc.calculate_overall_wellness(checkin)
        self.assertIn('physical_score', result)
        self.assertIn('mental_score', result)
        self.assertIn('relational_score', result)
        self.assertIn('financial_feeling_score', result)
        self.assertIn('overall_wellness_score', result)
        for k, v in result.items():
            self.assertIsInstance(v, (int, float))
            self.assertEqual(round(v, 2), v)

    def test_custom_weights(self):
        checkin = _full_checkin(
            exercise_days=7,
            exercise_intensity='intense',
            sleep_quality=10,
            meditation_minutes=60,
            stress_level=1,
            overall_mood=10,
            relationship_satisfaction=10,
            social_interactions=10,
            financial_stress=1,
            spending_control=10,
        )
        # All 100s; weights should still apply to overall
        result = self.calc.calculate_overall_wellness(checkin)
        self.assertAlmostEqual(result['overall_wellness_score'], 100.0, places=2)
        result_custom = self.calc.calculate_overall_wellness(
            checkin,
            weights={'physical': 0.5, 'mental': 0.5, 'relational': 0, 'financial_feeling': 0},
        )
        self.assertAlmostEqual(result_custom['overall_wellness_score'], 100.0, places=2)


class TestWeekOverWeekChanges(unittest.TestCase):
    """Tests for calculate_week_over_week_changes."""

    def setUp(self):
        self.calc = WellnessScoreCalculator()

    def test_positive_changes(self):
        current = {
            'physical_score': 70,
            'mental_score': 80,
            'relational_score': 60,
            'overall_wellness_score': 68,
        }
        previous = {
            'physical_score': 60,
            'mental_score': 70,
            'relational_score': 50,
            'overall_wellness_score': 58,
        }
        changes = self.calc.calculate_week_over_week_changes(current, previous)
        self.assertEqual(changes['physical_change'], 10.0)
        self.assertEqual(changes['mental_change'], 10.0)
        self.assertEqual(changes['relational_change'], 10.0)
        self.assertEqual(changes['overall_change'], 10.0)

    def test_negative_changes(self):
        current = {'physical_score': 50, 'mental_score': 50, 'relational_score': 50, 'overall_wellness_score': 50}
        previous = {'physical_score': 70, 'mental_score': 70, 'relational_score': 70, 'overall_wellness_score': 70}
        changes = self.calc.calculate_week_over_week_changes(current, previous)
        self.assertEqual(changes['physical_change'], -20.0)
        self.assertEqual(changes['overall_change'], -20.0)

    def test_no_previous_uses_zero(self):
        current = {'physical_score': 80, 'mental_score': 80, 'relational_score': 80, 'overall_wellness_score': 80}
        previous = {}
        changes = self.calc.calculate_week_over_week_changes(current, previous)
        self.assertEqual(changes['physical_change'], 80.0)
        self.assertEqual(changes['overall_change'], 80.0)

    def test_returns_rounded_two_decimals(self):
        current = {'physical_score': 70.5, 'mental_score': 70.5, 'relational_score': 70.5, 'overall_wellness_score': 70.5}
        previous = {'physical_score': 70.123, 'mental_score': 70.123, 'relational_score': 70.123, 'overall_wellness_score': 70.123}
        changes = self.calc.calculate_week_over_week_changes(current, previous)
        for v in changes.values():
            self.assertEqual(round(v, 2), v)


class TestInvalidInputHandling(unittest.TestCase):
    """Tests for invalid input (wrong types, missing keys)."""

    def setUp(self):
        self.calc = WellnessScoreCalculator()

    def test_exercise_days_non_numeric(self):
        checkin = _full_checkin()
        checkin['exercise_days'] = 'five'
        with self.assertRaises(ValueError) as ctx:
            self.calc.calculate_physical_score(checkin)
        self.assertIn('integer', str(ctx.exception).lower())

    def test_missing_sleep_quality(self):
        checkin = _full_checkin()
        del checkin['sleep_quality']
        with self.assertRaises(ValueError):
            self.calc.calculate_physical_score(checkin)

    def test_missing_meditation_minutes(self):
        checkin = _full_checkin()
        del checkin['meditation_minutes']
        with self.assertRaises(ValueError):
            self.calc.calculate_mental_score(checkin)

    def test_missing_social_interactions(self):
        checkin = _full_checkin()
        del checkin['social_interactions']
        with self.assertRaises(ValueError):
            self.calc.calculate_relational_score(checkin)


if __name__ == '__main__':
    unittest.main()
