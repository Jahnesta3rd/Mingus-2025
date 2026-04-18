#!/usr/bin/env python3
"""Per-user career snapshot from modular onboarding (Guided Canvas)."""

from datetime import datetime

from sqlalchemy import CheckConstraint

from .database import db


class CareerProfile(db.Model):
    """One row per user; primary key is user_id."""

    __tablename__ = "career_profile"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    current_role = db.Column(db.String(100), nullable=True)
    industry = db.Column(db.String(100), nullable=True)
    years_experience = db.Column(db.Integer, nullable=True)
    satisfaction = db.Column(db.Integer, nullable=True)
    open_to_move = db.Column(db.Boolean, nullable=False, default=False)
    target_comp = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship("User", backref=db.backref("career_profile_row", uselist=False))

    __table_args__ = (
        CheckConstraint(
            "years_experience IS NULL OR (years_experience >= 0 AND years_experience <= 60)",
            name="ck_career_profile_years_experience",
        ),
        CheckConstraint(
            "satisfaction IS NULL OR (satisfaction >= 1 AND satisfaction <= 5)",
            name="ck_career_profile_satisfaction",
        ),
    )

    def __repr__(self) -> str:
        return f"<CareerProfile user_id={self.user_id} role={self.current_role!r}>"
