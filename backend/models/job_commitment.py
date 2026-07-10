#!/usr/bin/env python3
"""BTS job commitment model (BTS7 — side-job earnings → Tier 2 budget)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class JobCommitment(db.Model):
    """Links a side job to a BTS session for Tier 2 budget boost."""

    __tablename__ = "bts_job_commitments"

    commitment_id = db.Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    session_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("back_to_school_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(db.String(255), nullable=False, index=True)

    job_id = db.Column(db.String(255), nullable=False)
    job_title = db.Column(db.String(255), nullable=False)

    tier2_date = db.Column(db.Date, nullable=False)
    tier2_base_budget = db.Column(db.Numeric(10, 2), nullable=False)

    target_earnings = db.Column(db.Numeric(10, 2), nullable=False)
    actual_earnings = db.Column(
        db.Numeric(10, 2), nullable=False, default=0, server_default="0"
    )
    tier2_budget_with_earnings = db.Column(
        db.Numeric(10, 2), nullable=False, default=0, server_default="0"
    )

    # active | complete
    status = db.Column(
        db.String(50), nullable=False, default="active", server_default="active"
    )

    last_sync_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.text("NOW()"),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=db.text("NOW()"),
    )

    def to_dict(self) -> dict:
        actual = float(self.actual_earnings or 0)
        target = float(self.target_earnings or 0)
        progress = min((actual / target * 100) if target > 0 else 0.0, 100.0)
        return {
            "commitmentId": str(self.commitment_id),
            "sessionId": str(self.session_id),
            "userId": self.user_id,
            "jobId": self.job_id,
            "jobTitle": self.job_title,
            "tier2Date": self.tier2_date.isoformat() if self.tier2_date else None,
            "tier2BaseBudget": float(self.tier2_base_budget or 0),
            "targetEarnings": target,
            "actualEarnings": actual,
            "tier2BudgetWithEarnings": float(self.tier2_budget_with_earnings or 0),
            "progressPercent": round(progress, 1),
            "status": self.status,
            "lastSyncAt": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
