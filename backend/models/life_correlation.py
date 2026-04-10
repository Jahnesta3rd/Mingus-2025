#!/usr/bin/env python3
"""Point-in-time life scores for correlation (ledger, vibe, wellness, projections)."""

import uuid
from datetime import datetime

from sqlalchemy import Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class LifeScoreSnapshot(db.Model):
    """One row per user per calendar day (upserted); captures module and cross-domain signals."""

    __tablename__ = "life_score_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "snapshot_date",
            name="uq_life_score_snapshots_user_id_snapshot_date",
        ),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_date = db.Column(Date, nullable=False)
    trigger = db.Column(db.String(50), nullable=False)

    body_score = db.Column(db.Integer, nullable=True)
    roof_score = db.Column(db.Integer, nullable=True)
    vehicle_score = db.Column(db.Integer, nullable=True)
    life_ledger_score = db.Column(db.Integer, nullable=True)

    best_vibe_emotional_score = db.Column(db.Integer, nullable=True)
    best_vibe_financial_score = db.Column(db.Integer, nullable=True)
    best_vibe_combined_score = db.Column(db.Integer, nullable=True)
    active_tracked_people_count = db.Column(db.Integer, nullable=True)

    monthly_savings_rate = db.Column(db.Float, nullable=True)
    net_worth_estimate = db.Column(db.Integer, nullable=True)
    relationship_monthly_cost = db.Column(db.Integer, nullable=True)

    avg_wellness_score = db.Column(db.Float, nullable=True)
    avg_stress_level = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<LifeScoreSnapshot user_id={self.user_id!r} date={self.snapshot_date!r}>"
