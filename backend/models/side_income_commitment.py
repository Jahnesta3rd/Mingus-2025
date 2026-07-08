#!/usr/bin/env python3
"""Side income commitment tracking for ICC → DF1 handoff."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class UserSideIncomeCommitment(db.Model):
    __tablename__ = "user_side_income_commitment"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    icc_assessment_id = db.Column(PG_UUID(as_uuid=True), nullable=True)
    person_id = db.Column(PG_UUID(as_uuid=True), nullable=True)
    selected_job = db.Column(db.String(150), nullable=False)
    df1_job_type = db.Column(db.String(20), nullable=True)
    target_monthly_income = db.Column(db.Numeric(8, 2), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="selected")
    df1_first_income_date = db.Column(db.DateTime, nullable=True)
    df1_monthly_income_actual = db.Column(db.Numeric(8, 2), nullable=True)
    independence_timeline_original_months = db.Column(db.Integer, nullable=True)
    independence_timeline_with_income_months = db.Column(db.Integer, nullable=True)
    gap_coverage_pct_at_selection = db.Column(db.Numeric(5, 2), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = db.relationship("User", backref="side_income_commitments")

    def __repr__(self) -> str:
        return (
            f"<UserSideIncomeCommitment user_id={self.user_id!r} "
            f"job={self.selected_job!r} status={self.status!r}>"
        )
