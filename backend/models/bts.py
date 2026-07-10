#!/usr/bin/env python3
"""Back-to-school session and purchase-plan models (BTS1 / BTS2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from .database import db


class BackToSchoolSession(db.Model):
    """Planning session created by BTS1 (date + cash forecast tiers)."""

    __tablename__ = "back_to_school_sessions"

    session_id = db.Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    user_id = db.Column(db.String(255), nullable=False, index=True)
    bts_date = db.Column(db.Date, nullable=False)
    tier1_date = db.Column(db.Date, nullable=False)
    tier2_date = db.Column(db.Date, nullable=False)
    tier3_date = db.Column(db.Date, nullable=False)
    tier1_balance = db.Column(db.Numeric(12, 2), nullable=False)
    tier2_balance = db.Column(db.Numeric(12, 2), nullable=False)
    tier3_balance = db.Column(db.Numeric(12, 2), nullable=False)
    child_name = db.Column(db.String(255), nullable=True)
    child_age = db.Column(db.Integer, nullable=True)
    child_gender = db.Column(db.String(50), nullable=True)
    shortfall = db.Column(db.Numeric(12, 2), nullable=False, default=0, server_default="0")
    estimated_budget = db.Column(db.Numeric(12, 2), nullable=True)
    # Denormalized Tier 2 budget including side-job earnings (BTS7)
    tier2_budget_with_earnings = db.Column(db.Numeric(12, 2), nullable=True)
    # BTS8 — Tier 2 reminder notification state
    tier1_purchased_at = db.Column(db.DateTime, nullable=True)
    tier2_reminder_sent = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.text("false")
    )
    tier2_reminder_sent_at = db.Column(db.DateTime, nullable=True)
    tier2_reminder_dismissed = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.text("false")
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=db.text("NOW()"),
    )

    purchase_plan = db.relationship(
        "BackToSchoolPurchasePlan",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    recommendations = db.relationship(
        "BackToSchoolRecommendation",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "sessionId": str(self.session_id),
            "userId": self.user_id,
            "btsDate": self.bts_date.isoformat() if self.bts_date else None,
            "tier1Date": self.tier1_date.isoformat() if self.tier1_date else None,
            "tier2Date": self.tier2_date.isoformat() if self.tier2_date else None,
            "tier3Date": self.tier3_date.isoformat() if self.tier3_date else None,
            "tier1Balance": float(self.tier1_balance) if self.tier1_balance is not None else 0.0,
            "tier2Balance": float(self.tier2_balance) if self.tier2_balance is not None else 0.0,
            "tier3Balance": float(self.tier3_balance) if self.tier3_balance is not None else 0.0,
            "childName": self.child_name,
            "childAge": self.child_age,
            "childGender": self.child_gender,
            "shortfall": float(self.shortfall) if self.shortfall is not None else 0.0,
            "estimatedBudget": (
                float(self.estimated_budget) if self.estimated_budget is not None else None
            ),
            "tier2BudgetWithEarnings": (
                float(self.tier2_budget_with_earnings)
                if self.tier2_budget_with_earnings is not None
                else None
            ),
            "tier1PurchasedAt": (
                self.tier1_purchased_at.isoformat() if self.tier1_purchased_at else None
            ),
            "tier2ReminderSent": bool(self.tier2_reminder_sent),
            "tier2ReminderSentAt": (
                self.tier2_reminder_sent_at.isoformat()
                if self.tier2_reminder_sent_at
                else None
            ),
            "tier2ReminderDismissed": bool(self.tier2_reminder_dismissed),
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class BackToSchoolPurchasePlan(db.Model):
    """Claude-generated 3-tier purchase plan (BTS2)."""

    __tablename__ = "back_to_school_purchase_plans"

    plan_id = db.Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=db.text("gen_random_uuid()"),
    )
    session_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("back_to_school_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user_id = db.Column(db.String(255), nullable=False, index=True)
    plan_data = db.Column(JSONB, nullable=False)
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

    session = db.relationship("BackToSchoolSession", back_populates="purchase_plan")

    def to_dict(self) -> dict:
        return {
            "planId": str(self.plan_id),
            "sessionId": str(self.session_id),
            "userId": self.user_id,
            "planData": self.plan_data,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class BackToSchoolRecommendation(db.Model):
    """BTS5 product recommendations audit trail (per session + tier)."""

    __tablename__ = "back_to_school_recommendations"
    __table_args__ = (
        db.UniqueConstraint(
            "session_id",
            "tier",
            name="uq_bts_recommendation_session_tier",
        ),
    )

    recommendation_id = db.Column(
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
    tier = db.Column(db.String(20), nullable=False)
    recommendation_data = db.Column(JSONB, nullable=False)
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

    session = db.relationship("BackToSchoolSession", back_populates="recommendations")

    def to_dict(self) -> dict:
        return {
            "recommendationId": str(self.recommendation_id),
            "sessionId": str(self.session_id),
            "userId": self.user_id,
            "tier": self.tier,
            "recommendationData": self.recommendation_data,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
