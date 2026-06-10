#!/usr/bin/env python3
"""Plaid-synced bank transactions for measured spending correlation."""

from datetime import datetime

from sqlalchemy import Index

from .database import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    plaid_transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    merchant = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    subcategory = db.Column(db.String(100), nullable=True)
    date = db.Column(db.Date, nullable=False, index=True)
    is_debit = db.Column(db.Boolean, nullable=False)
    account_id = db.Column(db.String(100), nullable=True)
    pending = db.Column(db.Boolean, default=False)
    user_tagged_stress_spending = db.Column(db.Boolean, nullable=True)
    user_tagged_relationship_spending = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('transactions', lazy='dynamic', cascade='all, delete-orphan'))

    __table_args__ = (
        Index('idx_transactions_user_date', 'user_id', 'date'),
    )

    def __repr__(self):
        return f'<Transaction {self.plaid_transaction_id} user={self.user_id}>'
