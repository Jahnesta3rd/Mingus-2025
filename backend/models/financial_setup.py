#!/usr/bin/env python3
"""
Mingus Application - Financial Setup Models
SQLAlchemy models for recurring expenses and user income (weekly check-in context).
"""

import uuid
from datetime import datetime

from sqlalchemy import Index, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from .database import db


# =============================================================================
# RECURRING_EXPENSES TABLE
# =============================================================================

class RecurringExpense(db.Model):
    """User's fixed monthly expenses (set up once)."""
    __tablename__ = 'recurring_expenses'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # housing, transportation, insurance, debt, subscription, utilities, other
    due_day = db.Column(db.Integer, nullable=True)  # 1-31
    frequency = db.Column(db.String(20), nullable=False)  # monthly, biweekly, weekly, quarterly, annual
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='recurring_expenses')

    __table_args__ = (
        Index('idx_recurring_expenses_user_id', 'user_id'),
        Index('idx_recurring_expenses_user_active', 'user_id', 'is_active'),
        CheckConstraint(
            "category IN ('housing', 'transportation', 'insurance', 'debt', 'subscription', 'utilities', 'other')",
            name='ck_recurring_expenses_category'
        ),
        CheckConstraint(
            "frequency IN ('monthly', 'biweekly', 'weekly', 'quarterly', 'annual')",
            name='ck_recurring_expenses_frequency'
        ),
        CheckConstraint('due_day IS NULL OR (due_day >= 1 AND due_day <= 31)', name='ck_recurring_expenses_due_day'),
        CheckConstraint('amount >= 0', name='ck_recurring_expenses_amount_non_negative'),
    )

    def __repr__(self):
        return f'<RecurringExpense {self.id}: {self.name} {self.amount}>'


# =============================================================================
# USER_INCOME TABLE
# =============================================================================

class UserIncome(db.Model):
    """User's income sources."""
    __tablename__ = 'user_income'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    source_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # monthly, biweekly, weekly, annual
    pay_day = db.Column(db.Integer, nullable=True)  # day of month for monthly, or 1/15 for biweekly
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='user_income_sources')

    __table_args__ = (
        Index('idx_user_income_user_id', 'user_id'),
        Index('idx_user_income_user_active', 'user_id', 'is_active'),
        CheckConstraint(
            "frequency IN ('monthly', 'biweekly', 'weekly', 'annual')",
            name='ck_user_income_frequency'
        ),
        CheckConstraint('pay_day IS NULL OR (pay_day >= 1 AND pay_day <= 31)', name='ck_user_income_pay_day'),
        CheckConstraint('amount >= 0', name='ck_user_income_amount_non_negative'),
    )

    def __repr__(self):
        return f'<UserIncome {self.id}: {self.source_name} {self.amount}>'
