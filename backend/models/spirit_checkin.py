#!/usr/bin/env python3
"""
Spirit & Finance daily check-in models: practice logging, streaks, and finance correlations.
"""

from datetime import datetime

from sqlalchemy import Index, UniqueConstraint, CheckConstraint

from .database import db


class SpiritCheckin(db.Model):
    """One spiritual practice check-in per user per calendar day."""

    __tablename__ = "spirit_checkins"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    checked_in_date = db.Column(db.Date, nullable=False)
    practice_type = db.Column(db.String(20), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    feeling_before = db.Column(db.Integer, nullable=True)
    feeling_after = db.Column(db.Integer, nullable=False)
    intention_text = db.Column(db.Text, nullable=True)
    practice_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("spirit_checkins", lazy="dynamic"))

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "checked_in_date",
            name="uq_spirit_checkins_user_checked_in_date",
        ),
        Index("ix_spirit_checkins_user_id_checked_in_date", "user_id", "checked_in_date"),
        CheckConstraint(
            "practice_type IN ('prayer', 'meditation', 'gratitude', 'affirmation')",
            name="ck_spirit_checkins_practice_type",
        ),
        CheckConstraint(
            "duration_minutes IN (5, 10, 15, 20, 30)",
            name="ck_spirit_checkins_duration_minutes",
        ),
        CheckConstraint(
            "feeling_before IS NULL OR (feeling_before >= 1 AND feeling_before <= 5)",
            name="ck_spirit_checkins_feeling_before",
        ),
        CheckConstraint(
            "feeling_after >= 1 AND feeling_after <= 5",
            name="ck_spirit_checkins_feeling_after",
        ),
    )

    @staticmethod
    def compute_score(practice_type: str, duration_minutes: int, feeling_after: int) -> float:
        type_weight = {
            "prayer": 1.4,
            "meditation": 1.3,
            "gratitude": 1.1,
            "affirmation": 1.0,
        }
        duration_multiplier = {5: 0.6, 10: 0.8, 15: 1.0, 20: 1.2, 30: 1.5}
        tw = type_weight[practice_type]
        dm = duration_multiplier[duration_minutes]
        feeling_lift = (feeling_after / 5.0) * 1.5
        return round(tw * dm * feeling_lift * 10, 2)

    def __repr__(self):
        return (
            f"<SpiritCheckin id={self.id} user_id={self.user_id} "
            f"date={self.checked_in_date!r} type={self.practice_type!r}>"
        )


class SpiritCheckinStreak(db.Model):
    """Aggregated streak and totals for spirit check-ins (one row per user)."""

    __tablename__ = "spirit_checkin_streaks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    current_streak = db.Column(db.Integer, nullable=False, default=0)
    longest_streak = db.Column(db.Integer, nullable=False, default=0)
    last_checkin_date = db.Column(db.Date, nullable=True)
    total_checkins = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship("User", backref=db.backref("spirit_checkin_streak", uselist=False))

    def __repr__(self):
        return (
            f"<SpiritCheckinStreak user_id={self.user_id} "
            f"current={self.current_streak} longest={self.longest_streak}>"
        )


class SpiritFinanceCorrelation(db.Model):
    """Computed rolling-window correlations between practice scores and finance signals."""

    __tablename__ = "spirit_finance_correlations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    computed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    weeks_analyzed = db.Column(db.Integer, nullable=False, default=8)
    corr_practice_savings = db.Column(db.Float, nullable=True)
    corr_practice_impulse = db.Column(db.Float, nullable=True)
    corr_practice_stress = db.Column(db.Float, nullable=True)
    corr_practice_bills_ontime = db.Column(db.Float, nullable=True)
    avg_practice_score_high_weeks = db.Column(db.Float, nullable=True)
    avg_impulse_miss_days = db.Column(db.Float, nullable=True)
    avg_impulse_checkin_days = db.Column(db.Float, nullable=True)
    insight_summary = db.Column(db.Text, nullable=True)

    user = db.relationship("User", backref=db.backref("spirit_finance_correlations", lazy="dynamic"))

    __table_args__ = (
        Index("ix_spirit_finance_correlations_user_id_computed_at", "user_id", "computed_at"),
    )

    def __repr__(self):
        return (
            f"<SpiritFinanceCorrelation id={self.id} user_id={self.user_id} "
            f"computed_at={self.computed_at!r} weeks={self.weeks_analyzed}>"
        )
