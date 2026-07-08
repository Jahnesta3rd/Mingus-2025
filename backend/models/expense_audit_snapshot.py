#!/usr/bin/env python3
"""Expense audit snapshot records."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from .database import db


class ExpenseAuditSnapshot(db.Model):
    __tablename__ = "expense_audit_snapshots"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    days_lookback = db.Column(db.Integer, nullable=False, default=90)
    total_monthly_spending = db.Column(db.Numeric(8, 2), nullable=False)
    spending_by_category = db.Column(JSONB, nullable=False)
    tier_recommendations = db.Column(JSONB, nullable=False)
    combined_savings = db.Column(JSONB, nullable=False)
    replacement_activities = db.Column(JSONB, nullable=True)
    selected_tiers = db.Column(db.String(10), nullable=True)
    total_savings_selected = db.Column(db.Numeric(8, 2), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return f"<ExpenseAuditSnapshot user_id={self.user_id!r} total={self.total_monthly_spending!r}>"
