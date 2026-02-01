#!/usr/bin/env python3
"""
Wellness Score Calculator Service for Mingus Application

Stateless service that computes wellness scores from weekly check-in data.
All calculations use only user-provided data (no external APIs).
"""

from datetime import date, timedelta
from typing import Dict, Any, Optional


# Default weights for overall wellness (must sum to 1.0)
DEFAULT_WEIGHTS = {
    'physical': 0.30,
    'mental': 0.30,
    'relational': 0.20,
    'financial_feeling': 0.20,
}

EXERCISE_INTENSITY_POINTS = {
    'light': 10,
    'moderate': 15,
    'intense': 20,
}


class WellnessScoreCalculator:
    """
    Stateless calculator for wellness scores from check-in data.
    All scores are on a 0-100 scale.
    """

    @staticmethod
    def get_week_ending_date(d: date) -> date:
        """
        Return the Sunday (week-ending date) for the week containing the given date.
        Uses US convention: week runs Monday–Sunday, so Sunday is the last day.

        Args:
            d: Any date in the week.

        Returns:
            The Sunday of that week. If d is already Sunday, returns d.
        """
        # Python: weekday() 0=Monday, 6=Sunday
        days_until_sunday = (6 - d.weekday()) % 7
        return d + timedelta(days=days_until_sunday)

    @staticmethod
    def _validate_optional_int(value: Any, min_val: int, max_val: int, name: str) -> Optional[int]:
        """Coerce and validate an optional int in range; None remains None."""
        if value is None:
            return None
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be an integer, got {type(value).__name__}")
        if not (min_val <= v <= max_val):
            raise ValueError(f"{name} must be between {min_val} and {max_val}, got {v}")
        return v

    @staticmethod
    def _validate_required_int(value: Any, min_val: int, max_val: int, name: str) -> int:
        """Validate required int in range."""
        if value is None:
            raise ValueError(f"{name} is required")
        return WellnessScoreCalculator._validate_optional_int(value, min_val, max_val, name)

    def calculate_physical_score(self, checkin: Dict[str, Any]) -> float:
        """
        Physical wellness score (0-100) from exercise and sleep.

        Formula:
        - Exercise days (0-7) → 0-40 points: (exercise_days / 7) * 40
        - Exercise intensity → 0-20 points: light=10, moderate=15, intense=20
          (only counted if exercise_days > 0)
        - Sleep quality (1-10) → 0-40 points: ((sleep_quality - 1) / 9) * 40

        Args:
            checkin: Dict with exercise_days, exercise_intensity (optional), sleep_quality.

        Returns:
            Score from 0 to 100.

        Raises:
            ValueError: If any value is out of range.
        """
        exercise_days = self._validate_required_int(
            checkin.get('exercise_days'), 0, 7, 'exercise_days'
        )
        sleep_quality = self._validate_required_int(
            checkin.get('sleep_quality'), 1, 10, 'sleep_quality'
        )

        # Exercise days → 0-40
        exercise_points = (exercise_days / 7) * 40

        # Intensity → 0-20 only if exercised
        intensity_points = 0
        if exercise_days > 0:
            raw = checkin.get('exercise_intensity')
            if raw is not None:
                intensity_str = str(raw).strip().lower()
                if intensity_str not in EXERCISE_INTENSITY_POINTS:
                    raise ValueError(
                        f"exercise_intensity must be one of "
                        f"{list(EXERCISE_INTENSITY_POINTS.keys())}, got {raw!r}"
                    )
                intensity_points = EXERCISE_INTENSITY_POINTS[intensity_str]

        # Sleep quality (1-10) → 0-40
        sleep_points = ((sleep_quality - 1) / 9) * 40

        total = exercise_points + intensity_points + sleep_points
        return min(100.0, total)

    def calculate_mental_score(self, checkin: Dict[str, Any]) -> float:
        """
        Mental wellness score (0-100) from meditation, stress, and mood.

        Formula:
        - Meditation minutes → 0-30 points: min(meditation_minutes, 60) / 60 * 30 (cap at 60 min)
        - Stress level (inverted; 1=low, 10=high) → 0-35: ((10 - stress_level) / 9) * 35
        - Overall mood (1-10) → 0-35: ((overall_mood - 1) / 9) * 35

        Args:
            checkin: Dict with meditation_minutes, stress_level, overall_mood.

        Returns:
            Score from 0 to 100.

        Raises:
            ValueError: If any value is out of range.
        """
        meditation_minutes = self._validate_required_int(
            checkin.get('meditation_minutes'), 0, 999, 'meditation_minutes'
        )
        stress_level = self._validate_required_int(
            checkin.get('stress_level'), 1, 10, 'stress_level'
        )
        overall_mood = self._validate_required_int(
            checkin.get('overall_mood'), 1, 10, 'overall_mood'
        )

        # Meditation: cap at 60 min → 0-30
        meditation_points = (min(meditation_minutes, 60) / 60) * 30

        # Stress inverted: low stress = high points. (11 - stress_level - 1) / 9 * 35 = (10 - stress_level) / 9 * 35
        stress_points = ((10 - stress_level) / 9) * 35

        # Mood (1-10) → 0-35
        mood_points = ((overall_mood - 1) / 9) * 35

        total = meditation_points + stress_points + mood_points
        return min(100.0, total)

    def calculate_relational_score(self, checkin: Dict[str, Any]) -> float:
        """
        Relational wellness score (0-100) from relationships and social interactions.

        Formula:
        - Relationship satisfaction (1-10) → 0-60: ((relationship_satisfaction - 1) / 9) * 60
        - Social interactions → 0-40: min(social_interactions, 10) / 10 * 40 (cap at 10)

        Args:
            checkin: Dict with relationship_satisfaction, social_interactions.

        Returns:
            Score from 0 to 100.

        Raises:
            ValueError: If any value is out of range.
        """
        relationship_satisfaction = self._validate_required_int(
            checkin.get('relationship_satisfaction'), 1, 10, 'relationship_satisfaction'
        )
        social_raw = checkin.get('social_interactions')
        if social_raw is None:
            raise ValueError("social_interactions is required")
        try:
            social_interactions = int(social_raw)
        except (TypeError, ValueError):
            raise ValueError(
                f"social_interactions must be an integer, got {type(social_raw).__name__}"
            )
        if social_interactions < 0:
            raise ValueError(
                f"social_interactions must be >= 0, got {social_interactions}"
            )

        # Relationship (1-10) → 0-60
        relationship_points = ((relationship_satisfaction - 1) / 9) * 60

        # Social interactions, cap at 10 → 0-40
        social_points = (min(social_interactions, 10) / 10) * 40

        total = relationship_points + social_points
        return min(100.0, total)

    def calculate_financial_feeling_score(self, checkin: Dict[str, Any]) -> float:
        """
        Financial feeling score (0-100) from stress and control.

        Formula:
        - Financial stress (inverted; 1=low, 10=high) → 0-50: ((10 - financial_stress) / 9) * 50
        - Spending control (1-10) → 0-50: ((spending_control - 1) / 9) * 50

        Args:
            checkin: Dict with financial_stress, spending_control.

        Returns:
            Score from 0 to 100.

        Raises:
            ValueError: If any value is out of range.
        """
        financial_stress = self._validate_required_int(
            checkin.get('financial_stress'), 1, 10, 'financial_stress'
        )
        spending_control = self._validate_required_int(
            checkin.get('spending_control'), 1, 10, 'spending_control'
        )

        # Financial stress inverted → 0-50
        stress_points = ((10 - financial_stress) / 9) * 50

        # Spending control → 0-50
        control_points = ((spending_control - 1) / 9) * 50

        total = stress_points + control_points
        return min(100.0, total)

    def calculate_overall_wellness(
        self,
        checkin: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, float]:
        """
        Compute all component scores and weighted overall wellness score.

        Default weights: physical=0.30, mental=0.30, relational=0.20, financial_feeling=0.20.

        Args:
            checkin: Full check-in dict with all required fields for each component.
            weights: Optional dict with keys physical, mental, relational, financial_feeling
                     (should sum to 1.0).

        Returns:
            Dict with physical_score, mental_score, relational_score, financial_feeling_score,
            overall_wellness_score (all rounded to 2 decimal places).

        Raises:
            ValueError: If any check-in value is out of range.
        """
        w = weights if weights is not None else DEFAULT_WEIGHTS.copy()

        physical = self.calculate_physical_score(checkin)
        mental = self.calculate_mental_score(checkin)
        relational = self.calculate_relational_score(checkin)
        financial_feeling = self.calculate_financial_feeling_score(checkin)

        overall = (
            physical * w.get('physical', DEFAULT_WEIGHTS['physical'])
            + mental * w.get('mental', DEFAULT_WEIGHTS['mental'])
            + relational * w.get('relational', DEFAULT_WEIGHTS['relational'])
            + financial_feeling * w.get('financial_feeling', DEFAULT_WEIGHTS['financial_feeling'])
        )

        return {
            'physical_score': round(physical, 2),
            'mental_score': round(mental, 2),
            'relational_score': round(relational, 2),
            'financial_feeling_score': round(financial_feeling, 2),
            'overall_wellness_score': round(min(100.0, overall), 2),
        }

    def calculate_week_over_week_changes(
        self,
        current_scores: Dict[str, float],
        previous_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Compute week-over-week change for each component and overall.

        Change = current - previous (positive = improvement).

        Args:
            current_scores: Dict with physical_score, mental_score, relational_score,
                            financial_feeling_score, overall_wellness_score.
            previous_scores: Same keys as current_scores.

        Returns:
            Dict with physical_change, mental_change, relational_change, overall_change
            (all rounded to 2 decimal places). financial_feeling_change is omitted to match
            the requirement of physical_change, mental_change, relational_change, overall_change.
        """
        keys_and_result = [
            ('physical_score', 'physical_change'),
            ('mental_score', 'mental_change'),
            ('relational_score', 'relational_change'),
            ('overall_wellness_score', 'overall_change'),
        ]
        result = {}
        for score_key, change_key in keys_and_result:
            curr = current_scores.get(score_key, 0) or 0
            prev = previous_scores.get(score_key, 0) or 0
            result[change_key] = round(curr - prev, 2)
        return result
