#!/usr/bin/env python3
"""Append-only HPRS score history for trend tracking."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class HprsScoreHistory(db.Model):
    """Point-in-time HPRS row written on each compute (audit + trend charts)."""

    __tablename__ = "hprs_score_history"
    __table_args__ = (
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_hprs_score_history_overall_score",
        ),
        Index(
            "ix_hprs_score_history_user_id_recorded_at",
            "user_id",
            "recorded_at",
        ),
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
    trigger = db.Column(db.String(50), nullable=False)
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship(
        "User",
        backref=db.backref("hprs_score_history_rows", lazy="dynamic"),
    )

    def __repr__(self) -> str:
        return (
            f"<HprsScoreHistory user_id={self.user_id!r} overall={self.overall_score!r} "
            f"trigger={self.trigger!r} recorded_at={self.recorded_at!r}>"
        )
