#!/usr/bin/env python3
"""Quick Spend Logger entries for daily discretionary purchases."""

from datetime import datetime

from sqlalchemy import Index, Numeric

from .database import db


class QuickSpendEntry(db.Model):
    __tablename__ = "quick_spend_entries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Timestamps
    logged_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False
    )
    date = db.Column(db.Date, nullable=False, index=True)

    # Required — the three fields the FAB always captures
    amount = db.Column(Numeric(10, 2), nullable=False)
    spend_vibe = db.Column(db.String(50), nullable=False)
    vibe_signal = db.Column(db.String(50), nullable=False)

    # Merchant — one of merchant_id or custom_merchant_name will be set
    merchant_id = db.Column(db.String(50), nullable=True)
    merchant_name = db.Column(db.String(100), nullable=True)
    merchant_group = db.Column(db.String(60), nullable=True)

    # Optional enrichment
    notes = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


Index(
    "ix_quick_spend_user_date",
    QuickSpendEntry.user_id,
    QuickSpendEntry.date,
)
