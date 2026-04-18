#!/usr/bin/env python3
"""Per-user housing snapshot from modular onboarding (Guided Canvas)."""

from datetime import datetime

from sqlalchemy import CheckConstraint

from .database import db


class HousingProfile(db.Model):
    """One row per user; primary key is user_id."""

    __tablename__ = "housing_profile"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    housing_type = db.Column(db.String(10), nullable=False)
    monthly_cost = db.Column(db.Float, nullable=False)
    zip_or_city = db.Column(db.String(100), nullable=False)
    split_share_pct = db.Column(db.Float, nullable=True)
    has_buy_goal = db.Column(db.Boolean, nullable=False, default=False)
    target_price = db.Column(db.Float, nullable=True)
    target_timeline_months = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship("User", backref=db.backref("housing_profile_row", uselist=False))

    __table_args__ = (
        CheckConstraint(
            "housing_type IN ('rent','own')",
            name="ck_housing_profile_housing_type",
        ),
        CheckConstraint("monthly_cost >= 0", name="ck_housing_profile_monthly_cost"),
        CheckConstraint(
            "split_share_pct IS NULL OR (split_share_pct >= 0 AND split_share_pct <= 100)",
            name="ck_housing_profile_split_share_pct",
        ),
    )

    def __repr__(self) -> str:
        return f"<HousingProfile user_id={self.user_id} type={self.housing_type!r}>"
