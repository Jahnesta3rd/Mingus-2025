#!/usr/bin/env python3
"""Home Purchase Readiness Score — current computed score per user (HPRS)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from .database import db


class HprsScore(db.Model):
    """Latest HPRS snapshot for a user; upserted on each recompute."""

    __tablename__ = "hprs_scores"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_hprs_scores_user_id"),
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_hprs_scores_overall_score",
        ),
        CheckConstraint(
            "down_payment_score IS NULL OR (down_payment_score >= 0 AND down_payment_score <= 100)",
            name="ck_hprs_scores_down_payment_score",
        ),
        CheckConstraint(
            "credit_score IS NULL OR (credit_score >= 0 AND credit_score <= 100)",
            name="ck_hprs_scores_credit_score",
        ),
        CheckConstraint(
            "dti_score IS NULL OR (dti_score >= 0 AND dti_score <= 100)",
            name="ck_hprs_scores_dti_score",
        ),
        CheckConstraint(
            "savings_rate_score IS NULL OR (savings_rate_score >= 0 AND savings_rate_score <= 100)",
            name="ck_hprs_scores_savings_rate_score",
        ),
        CheckConstraint(
            "income_stability_score IS NULL OR (income_stability_score >= 0 AND income_stability_score <= 100)",
            name="ck_hprs_scores_income_stability_score",
        ),
        Index("ix_hprs_scores_user_id", "user_id"),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    overall_score = db.Column(db.Integer, nullable=False)
    readiness_tier = db.Column(db.String(20), nullable=False)
    down_payment_score = db.Column(db.Integer, nullable=True)
    credit_score = db.Column(db.Integer, nullable=True)
    dti_score = db.Column(db.Integer, nullable=True)
    savings_rate_score = db.Column(db.Integer, nullable=True)
    income_stability_score = db.Column(db.Integer, nullable=True)
    target_price = db.Column(db.Float, nullable=True)
    target_timeline_months = db.Column(db.Integer, nullable=True)
    down_payment_saved = db.Column(db.Float, nullable=True)
    down_payment_needed = db.Column(db.Float, nullable=True)
    inputs_snapshot = db.Column(JSONB, nullable=True)
    career_risk_score = db.Column(db.Integer, nullable=True)
    career_risk_band = db.Column(db.String(20), nullable=True)
    career_modifier = db.Column(db.Integer, nullable=False, default=0)
    vehicle_risk_score = db.Column(db.Integer, nullable=True)
    vehicle_risk_band = db.Column(db.String(20), nullable=True)
    vehicle_modifier = db.Column(db.Integer, nullable=False, default=0)
    combined_modifier = db.Column(db.Integer, nullable=False, default=0)
    market_score = db.Column(db.Integer, nullable=True)
    computed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = db.relationship("User", backref=db.backref("hprs_score_row", uselist=False))
    plans = db.relationship(
        "HprsPlan",
        back_populates="score",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<HprsScore user_id={self.user_id!r} overall={self.overall_score!r} "
            f"tier={self.readiness_tier!r}>"
        )
