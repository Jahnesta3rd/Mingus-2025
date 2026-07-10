#!/usr/bin/env python3
"""
Mingus Application - Weekly Check-in Model
SQLAlchemy model for weekly wellness, spending signals, and wisdom calls.
"""

import uuid

from sqlalchemy import Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


# =============================================================================
# ENUMS (stored as VARCHAR with CHECK in migration for portability)
# =============================================================================

EXERCISE_INTENSITY_VALUES = ('light', 'moderate', 'intense')
CONFIDENCE_LEVEL_VALUES = ('low', 'medium', 'high')


class WeeklyCheckin(db.Model):
    """
    Core weekly check-in: wellness self-report, spending signals, and wisdom call.

    One record per user per week_number.
    wisdom_call_audio_url remains NULL until Phase 5 (audio generation).
    """

    __tablename__ = 'weekly_checkins'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    week_ending_date = db.Column(db.Date, nullable=False, index=True)
    week_number = db.Column(db.Integer, nullable=True, index=True)
    year = db.Column(db.Integer, nullable=True, index=True)

    # --- PHYSICAL WELLNESS ---
    exercise_days = db.Column(db.Integer, nullable=True)  # 0-7
    exercise_intensity = db.Column(db.String(10), nullable=True)  # light, moderate, intense
    sleep_quality = db.Column(db.Integer, nullable=True)  # 1-10
    sleep_hours = db.Column(db.Float, nullable=True)

    # --- MENTAL WELLNESS ---
    meditation_minutes = db.Column(db.Integer, nullable=True)  # 0-999
    stress_level = db.Column(db.Integer, nullable=True)  # 1-10
    overall_mood = db.Column(db.Integer, nullable=True)  # 1-10

    # --- RELATIONAL WELLNESS ---
    relationship_satisfaction = db.Column(db.Integer, nullable=True)  # 1-10
    social_interactions = db.Column(db.Integer, nullable=True)  # 0+

    # --- FINANCIAL FEELINGS ---
    financial_stress = db.Column(db.Integer, nullable=True)  # 1-10
    spending_control = db.Column(db.Integer, nullable=True)  # 1-10

    # --- WEEKLY SPENDING ESTIMATES ---
    groceries_estimate = db.Column(db.Numeric(10, 2), nullable=True)
    dining_estimate = db.Column(db.Numeric(10, 2), nullable=True)
    entertainment_estimate = db.Column(db.Numeric(10, 2), nullable=True)
    shopping_estimate = db.Column(db.Numeric(10, 2), nullable=True)
    transport_estimate = db.Column(db.Numeric(10, 2), nullable=True)
    utilities_estimate = db.Column(db.Numeric(10, 2), nullable=True)
    other_estimate = db.Column(db.Numeric(10, 2), nullable=True)

    # --- TAGGED SPENDING ---
    impulse_spending = db.Column(db.Numeric(10, 2), nullable=True)
    stress_spending = db.Column(db.Numeric(10, 2), nullable=True)
    celebration_spending = db.Column(db.Numeric(10, 2), nullable=True)
    had_impulse_purchases = db.Column(db.Boolean, default=False, nullable=False)
    had_stress_purchases = db.Column(db.Boolean, default=False, nullable=False)
    biggest_unnecessary_purchase = db.Column(db.Numeric(10, 2), nullable=True)
    biggest_unnecessary_category = db.Column(db.String(50), nullable=True)

    # --- REFLECTION ---
    wins = db.Column(db.Text, nullable=True)
    challenges = db.Column(db.Text, nullable=True)

    # --- UNIFIED WEEKLY CHECK-IN (#176) — wellness self-state ---
    mood_rating = db.Column(db.Integer, nullable=True)
    activity_frequency = db.Column(db.Integer, nullable=True)
    body_score = db.Column(db.Integer, nullable=True)
    avg_sleep_hours = db.Column(db.Float, nullable=True)
    rest_quality = db.Column(db.Integer, nullable=True)
    # Relationships
    relationship_temperature = db.Column(db.Integer, nullable=True)
    meaningful_time_with_people = db.Column(db.Boolean, nullable=True)
    primary_partner_rating = db.Column(db.Integer, nullable=True)
    financial_convo_with_partner = db.Column(db.Boolean, nullable=True)
    financial_communication_with_partner = db.Column(db.Integer, nullable=True)
    parenting_stress = db.Column(db.Integer, nullable=True)
    unexpected_kid_spending = db.Column(db.Boolean, nullable=True)
    unexpected_kid_amount = db.Column(db.Float, nullable=True)
    # Practice & Spirit
    meditation_minutes_total = db.Column(db.Integer, nullable=True)
    practice_felt_grounding = db.Column(db.Boolean, nullable=True)
    felt_spiritual_connection = db.Column(db.Boolean, nullable=True)
    spiritual_connection_rating = db.Column(db.Integer, nullable=True)
    # Money & Spending (self-report)
    spending_discipline_rating = db.Column(db.Integer, nullable=True)
    discretionary_spending = db.Column(db.Numeric(10, 2), nullable=True)
    social_spending_unplanned = db.Column(db.Boolean, nullable=True)
    social_spending_amount = db.Column(db.Numeric(10, 2), nullable=True)
    partner_spending_unplanned = db.Column(db.Boolean, nullable=True)
    partner_spending_amount = db.Column(db.Numeric(10, 2), nullable=True)
    kids_spending_total = db.Column(db.Numeric(10, 2), nullable=True)
    kids_spending_unplanned = db.Column(db.Numeric(10, 2), nullable=True)
    financial_reflection = db.Column(db.Text, nullable=True)
    spending_trigger_description = db.Column(db.Text, nullable=True)
    weekly_reflection_change = db.Column(db.Text, nullable=True)

    # --- FINANCIAL SIGNALS (baseline comparison) ---
    spending_delta_from_baseline = db.Column(db.Float, nullable=True)
    unusual_spending_detected = db.Column(db.Boolean, default=False, nullable=False)

    # --- WISDOM CALL ---
    # wisdom_call_audio_url stays NULL until Phase 5 (audio generation).
    wisdom_call_script = db.Column(db.Text, nullable=True)
    wisdom_call_audio_url = db.Column(db.String(512), nullable=True)
    wisdom_call_sent_at = db.Column(db.DateTime, nullable=True)
    wisdom_call_listened_at = db.Column(db.DateTime, nullable=True)

    # --- METADATA ---
    completed_at = db.Column(db.DateTime, nullable=True)
    completion_time_seconds = db.Column(db.Integer, nullable=True)
    reminder_count = db.Column(db.Integer, default=0, nullable=False)

    # Relationships (backref on User: weekly_checkins)
    user = db.relationship('User', back_populates='weekly_checkins')
    wellness_scores = db.relationship(
        'WellnessScore',
        backref='checkin',
        lazy='dynamic',
        foreign_keys='WellnessScore.checkin_id',
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'week_number', name='uq_weekly_checkins_user_week_number'),
        UniqueConstraint('user_id', 'week_ending_date', name='uq_weekly_checkins_user_week'),
        Index('idx_weekly_checkins_user_id', 'user_id'),
        Index('idx_weekly_checkins_week_number', 'week_number'),
        Index('idx_weekly_checkins_week_ending_date', 'week_ending_date'),
        Index('idx_weekly_checkins_user_week', 'user_id', 'week_ending_date'),
        CheckConstraint(
            'exercise_days IS NULL OR (exercise_days >= 0 AND exercise_days <= 7)',
            name='ck_weekly_checkins_exercise_days',
        ),
        CheckConstraint(
            "exercise_intensity IS NULL OR exercise_intensity IN ('light', 'moderate', 'intense')",
            name='ck_weekly_checkins_exercise_intensity',
        ),
        CheckConstraint(
            'sleep_quality IS NULL OR (sleep_quality >= 1 AND sleep_quality <= 10)',
            name='ck_weekly_checkins_sleep_quality',
        ),
        CheckConstraint(
            'meditation_minutes IS NULL OR (meditation_minutes >= 0 AND meditation_minutes <= 999)',
            name='ck_weekly_checkins_meditation_minutes',
        ),
        CheckConstraint(
            'stress_level IS NULL OR (stress_level >= 1 AND stress_level <= 10)',
            name='ck_weekly_checkins_stress_level',
        ),
        CheckConstraint(
            'overall_mood IS NULL OR (overall_mood >= 1 AND overall_mood <= 10)',
            name='ck_weekly_checkins_overall_mood',
        ),
        CheckConstraint(
            'relationship_satisfaction IS NULL OR (relationship_satisfaction >= 1 AND relationship_satisfaction <= 10)',
            name='ck_weekly_checkins_relationship_satisfaction',
        ),
        CheckConstraint(
            'social_interactions IS NULL OR social_interactions >= 0',
            name='ck_weekly_checkins_social_interactions',
        ),
        CheckConstraint(
            'financial_stress IS NULL OR (financial_stress >= 1 AND financial_stress <= 10)',
            name='ck_weekly_checkins_financial_stress',
        ),
        CheckConstraint(
            'spending_control IS NULL OR (spending_control >= 1 AND spending_control <= 10)',
            name='ck_weekly_checkins_spending_control',
        ),
    )

    def __repr__(self):
        return (
            f'<WeeklyCheckin {self.id}: user={self.user_id} '
            f'week_number={self.week_number} week={self.week_ending_date}>'
        )
