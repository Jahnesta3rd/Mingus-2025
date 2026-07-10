#!/usr/bin/env python3
"""
Mingus Application - Weekly Check-in Wellness Models
SQLAlchemy models for the Weekly Check-in System with integrated spending estimates.

WeeklyCheckin lives in backend.models.checkin; re-exported here for compatibility.
"""

import uuid
from datetime import datetime

from sqlalchemy import Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db
from .checkin import (  # noqa: F401 — re-export
    WeeklyCheckin,
    EXERCISE_INTENSITY_VALUES,
    CONFIDENCE_LEVEL_VALUES,
)


# =============================================================================
# WELLNESS_SCORES TABLE
# =============================================================================

class WellnessScore(db.Model):
    """Computed weekly wellness scores from check-in data."""
    __tablename__ = 'wellness_scores'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    week_ending_date = db.Column(db.Date, nullable=False, index=True)
    checkin_id = db.Column(PG_UUID(as_uuid=True), db.ForeignKey('weekly_checkins.id', ondelete='CASCADE'), nullable=True, index=True)

    physical_score = db.Column(db.Numeric(5, 2), nullable=True)
    mental_score = db.Column(db.Numeric(5, 2), nullable=True)
    relational_score = db.Column(db.Numeric(5, 2), nullable=True)
    financial_feeling_score = db.Column(db.Numeric(5, 2), nullable=True)
    overall_wellness_score = db.Column(db.Numeric(5, 2), nullable=True)

    physical_change = db.Column(db.Numeric(5, 2), nullable=True)
    mental_change = db.Column(db.Numeric(5, 2), nullable=True)
    relational_change = db.Column(db.Numeric(5, 2), nullable=True)
    overall_change = db.Column(db.Numeric(5, 2), nullable=True)

    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='wellness_scores')

    __table_args__ = (
        UniqueConstraint('user_id', 'week_ending_date', name='uq_wellness_scores_user_week'),
        Index('idx_wellness_scores_user_id', 'user_id'),
        Index('idx_wellness_scores_week_ending_date', 'week_ending_date'),
        Index('idx_wellness_scores_user_week', 'user_id', 'week_ending_date'),
    )

    def __repr__(self):
        return f'<WellnessScore {self.id}: user={self.user_id} week={self.week_ending_date}>'


# =============================================================================
# WELLNESS_FINANCE_CORRELATIONS TABLE
# =============================================================================

class WellnessFinanceCorrelation(db.Model):
    """Correlation analysis results between wellness and spending."""
    __tablename__ = 'wellness_finance_correlations'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    weeks_analyzed = db.Column(db.Integer, nullable=True)

    stress_vs_impulse_spending = db.Column(db.Numeric(4, 3), nullable=True)
    stress_vs_total_spending = db.Column(db.Numeric(4, 3), nullable=True)
    exercise_vs_spending_control = db.Column(db.Numeric(4, 3), nullable=True)
    sleep_vs_dining_spending = db.Column(db.Numeric(4, 3), nullable=True)
    mood_vs_entertainment_spending = db.Column(db.Numeric(4, 3), nullable=True)
    mood_vs_shopping_spending = db.Column(db.Numeric(4, 3), nullable=True)
    meditation_vs_impulse_spending = db.Column(db.Numeric(4, 3), nullable=True)
    relationship_vs_discretionary_spending = db.Column(db.Numeric(4, 3), nullable=True)

    data_points = db.Column(db.Integer, nullable=True)
    confidence_level = db.Column(db.String(10), nullable=True)  # low, medium, high
    strongest_correlation_type = db.Column(db.String(50), nullable=True)
    strongest_correlation_value = db.Column(db.Numeric(4, 3), nullable=True)

    calculated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='wellness_finance_correlations')

    __table_args__ = (
        Index('idx_wellness_finance_corr_user_id', 'user_id'),
        Index('idx_wellness_finance_corr_dates', 'start_date', 'end_date'),
        CheckConstraint('confidence_level IS NULL OR confidence_level IN (\'low\', \'medium\', \'high\')', name='ck_wellness_finance_corr_confidence'),
    )

    def __repr__(self):
        return f'<WellnessFinanceCorrelation {self.id}: user={self.user_id}>'


# =============================================================================
# USER_STREAKS TABLE (weekly check-in consistency)
# =============================================================================

class WellnessCheckinStreak(db.Model):
    """Track weekly check-in consistency (streaks). Table: weekly_checkin_streaks to avoid conflict with gamification user_streaks."""
    __tablename__ = 'weekly_checkin_streaks'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    current_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_streak = db.Column(db.Integer, default=0, nullable=False)
    last_checkin_date = db.Column(db.Date, nullable=True)
    total_checkins = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='wellness_checkin_streak')

    __table_args__ = (
        UniqueConstraint('user_id', name='uq_weekly_checkin_streaks_user_id'),
        Index('idx_weekly_checkin_streaks_user_id', 'user_id'),
        CheckConstraint('current_streak >= 0', name='ck_weekly_checkin_streaks_current_streak'),
        CheckConstraint('longest_streak >= 0', name='ck_weekly_checkin_streaks_longest_streak'),
        CheckConstraint('total_checkins >= 0', name='ck_weekly_checkin_streaks_total_checkins'),
    )

    def __repr__(self):
        return f'<WellnessCheckinStreak user={self.user_id} current={self.current_streak}>'


# =============================================================================
# USER_SPENDING_BASELINES TABLE
# =============================================================================

class UserSpendingBaseline(db.Model):
    """Computed average spending for 'more/less than usual' comparisons."""
    __tablename__ = 'user_spending_baselines'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    avg_groceries = db.Column(db.Numeric(10, 2), nullable=True)
    avg_dining = db.Column(db.Numeric(10, 2), nullable=True)
    avg_entertainment = db.Column(db.Numeric(10, 2), nullable=True)
    avg_shopping = db.Column(db.Numeric(10, 2), nullable=True)
    avg_transport = db.Column(db.Numeric(10, 2), nullable=True)
    avg_total_variable = db.Column(db.Numeric(10, 2), nullable=True)
    avg_impulse = db.Column(db.Numeric(10, 2), nullable=True)

    weeks_of_data = db.Column(db.Integer, nullable=True)
    last_calculated = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', back_populates='spending_baseline')

    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_spending_baselines_user_id'),
        Index('idx_user_spending_baselines_user_id', 'user_id'),
    )

    def __repr__(self):
        return f'<UserSpendingBaseline user={self.user_id}>'


# =============================================================================
# USER_ACHIEVEMENTS TABLE (wellness check-in gamification)
# =============================================================================

class UserAchievement(db.Model):
    """Unlocked wellness check-in achievements per user."""
    __tablename__ = 'user_achievements'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    achievement_key = db.Column(db.String(50), nullable=False, index=True)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('wellness_achievements', lazy='dynamic', cascade='all, delete-orphan'))

    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_key', name='uq_user_achievements_user_key'),
        Index('idx_user_achievements_user_id', 'user_id'),
        Index('idx_user_achievements_key', 'achievement_key'),
    )

    def __repr__(self):
        return f'<UserAchievement user={self.user_id} key={self.achievement_key}>'


# =============================================================================
# CHECKIN_QUESTION_LOG TABLE (#176)
# =============================================================================

class CheckinQuestionLog(db.Model):
    """Tracks which rotating check-in questions were shown/answered per user/week."""
    __tablename__ = 'checkin_question_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    question_id = db.Column(db.String(20), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('checkin_question_logs', lazy='dynamic'))

    __table_args__ = (
        UniqueConstraint(
            'user_id', 'question_id', 'week_number', 'year',
            name='uq_checkin_question_log_user_q_week',
        ),
        Index('idx_checkin_question_log_user_question', 'user_id', 'question_id'),
        Index('idx_checkin_question_log_user_week_year', 'user_id', 'week_number', 'year'),
    )

    def __repr__(self):
        return f'<CheckinQuestionLog user={self.user_id} q={self.question_id} w={self.year}-W{self.week_number}>'
