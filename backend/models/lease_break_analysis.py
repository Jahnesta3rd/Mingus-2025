#!/usr/bin/env python3
"""Lease break analysis records."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class LeaseBreakAnalysis(db.Model):
    __tablename__ = "lease_break_analyses"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    months_remaining = db.Column(db.Integer, nullable=False)
    monthly_rent = db.Column(db.Numeric(8, 2), nullable=False)
    break_fee_percent = db.Column(db.Numeric(3, 1), nullable=False, default=1.5)
    scenario_a_cost = db.Column(db.Numeric(10, 2), nullable=False)
    scenario_b_cost = db.Column(db.Numeric(10, 2), nullable=False)
    recommendation = db.Column(db.String(50), nullable=False)
    savings = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return (
            f"<LeaseBreakAnalysis user_id={self.user_id!r} "
            f"recommendation={self.recommendation!r}>"
        )
