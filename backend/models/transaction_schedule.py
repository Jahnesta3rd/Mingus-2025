#!/usr/bin/env python3
"""
Transaction schedule models for cash-forecast style income and recurring expenses.

Mingus ``users.id`` is integer; foreign keys use Integer to match.
"""

import uuid
from datetime import datetime

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class IncomeStream(db.Model):
    """Take-home income on a fixed cadence (next pay date drives forecasting)."""

    __tablename__ = "income_streams"
    __table_args__ = (
        Index("ix_income_streams_user_id_is_active", "user_id", "is_active"),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    next_date = db.Column(db.Date, nullable=False)
    income_type = db.Column(db.String(30), nullable=False, default="earned")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<IncomeStream {self.id}: {self.label}>"


class ScheduledExpense(db.Model):
    """Recurring cash outflow on a schedule (distinct from financial_setup.RecurringExpense)."""

    __tablename__ = "schedule_recurring_expenses"
    __mapper_args__ = {
        "polymorphic_identity": "scheduled_expense",
    }
    __table_args__ = (
        Index("ix_schedule_recurring_expenses_user_id_is_active", "user_id", "is_active"),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    due_day = db.Column(db.Integer, nullable=False)
    next_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ScheduledExpense {self.id}: {self.label}>"
