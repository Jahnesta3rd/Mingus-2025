#!/usr/bin/env python3
"""Life Ledger composite score, per-module answers, and dashboard insights."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, false as sa_false
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class LifeLedgerProfile(db.Model):
    """One row per user: module scores, composite score, and projection fields."""

    __tablename__ = "life_ledger_profiles"
    __table_args__ = (
        CheckConstraint(
            "vibe_score IS NULL OR (vibe_score >= 0 AND vibe_score <= 100)",
            name="ck_life_ledger_profiles_vibe_score",
        ),
        CheckConstraint(
            "body_score IS NULL OR (body_score >= 0 AND body_score <= 100)",
            name="ck_life_ledger_profiles_body_score",
        ),
        CheckConstraint(
            "roof_score IS NULL OR (roof_score >= 0 AND roof_score <= 100)",
            name="ck_life_ledger_profiles_roof_score",
        ),
        CheckConstraint(
            "vehicle_score IS NULL OR (vehicle_score >= 0 AND vehicle_score <= 100)",
            name="ck_life_ledger_profiles_vehicle_score",
        ),
        CheckConstraint(
            "life_ledger_score IS NULL OR (life_ledger_score >= 0 AND life_ledger_score <= 100)",
            name="ck_life_ledger_profiles_life_ledger_score",
        ),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    vibe_score = db.Column(db.Integer, nullable=True)
    body_score = db.Column(db.Integer, nullable=True)
    roof_score = db.Column(db.Integer, nullable=True)
    vehicle_score = db.Column(db.Integer, nullable=True)
    life_ledger_score = db.Column(db.Integer, nullable=True)

    vibe_lead_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_checkups_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    vibe_annual_projection = db.Column(db.Integer, nullable=True)
    body_health_cost_projection = db.Column(db.Integer, nullable=True)
    roof_housing_wealth_gap = db.Column(db.Integer, nullable=True)
    vehicle_annual_maintenance = db.Column(db.Integer, nullable=True)

    # Dashboard checkup hub fields (#170) — all nullable
    body_energy_rating = db.Column(db.Integer, nullable=True)
    body_work_impact = db.Column(db.String(20), nullable=True)
    body_ongoing_health_cost = db.Column(db.Boolean, nullable=True)

    mood_stress_triggered_purchase = db.Column(db.String(10), nullable=True)
    mood_avoided_finances = db.Column(db.Boolean, nullable=True)
    mood_coping_methods = db.Column(db.Text, nullable=True)
    spending_intentionality_rating = db.Column(db.Integer, nullable=True)

    practice_had_moments = db.Column(db.Boolean, nullable=True)
    practice_affected_finances = db.Column(db.String(20), nullable=True)
    spirit_financially_anxious = db.Column(db.String(10), nullable=True)

    housing_stability_rating = db.Column(db.Integer, nullable=True)
    housing_tenure = db.Column(db.String(10), nullable=True)
    housing_lease_end_horizon = db.Column(db.String(20), nullable=True)
    housing_cost_changed = db.Column(db.String(15), nullable=True)
    housing_down_payment_status = db.Column(db.String(20), nullable=True)
    housing_unexpected_cost = db.Column(db.Boolean, nullable=True)
    housing_unexpected_cost_amount = db.Column(db.Float, nullable=True)

    vehicle_satisfaction_rating = db.Column(db.Integer, nullable=True)
    vehicle_maintenance_confidence = db.Column(db.Integer, nullable=True)
    vehicle_recent_concern = db.Column(db.Boolean, nullable=True)
    vehicle_concern_description = db.Column(db.Text, nullable=True)
    vehicle_weekly_miles = db.Column(db.Integer, nullable=True)
    vehicle_last_service_horizon = db.Column(db.String(15), nullable=True)
    vehicle_insurance_known = db.Column(db.Boolean, nullable=True)
    vehicle_insurance_premium = db.Column(db.Float, nullable=True)
    vehicle_insurance_last_shopped = db.Column(db.String(15), nullable=True)
    vehicle_decision_horizon = db.Column(db.String(25), nullable=True)
    vehicle_reliability_rating = db.Column(db.Integer, nullable=True)
    vehicle_value_perception = db.Column(db.Integer, nullable=True)

    relationship_friction_type = db.Column(db.String(20), nullable=True)
    relationship_spending_this_week = db.Column(db.Boolean, nullable=True)
    relationship_spending_amount = db.Column(db.Float, nullable=True)
    relationship_spending_type = db.Column(db.String(20), nullable=True)
    relationship_direction = db.Column(db.String(20), nullable=True)
    relationship_cost_awareness = db.Column(db.String(20), nullable=True)
    relationship_future_intention = db.Column(db.String(20), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class LifeLedgerModuleAnswer(db.Model):
    """Raw quiz-style answers per module."""

    __tablename__ = "life_ledger_module_answers"
    __table_args__ = (Index("ix_life_ledger_module_answers_user_id", "user_id"),)

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    module = db.Column(db.String(32), nullable=False)
    answers = db.Column(db.JSON, nullable=False, default=dict)
    completed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=False)


class LifeLedgerInsight(db.Model):
    """Personalized dashboard insights; may be dismissed by the user."""

    __tablename__ = "life_ledger_insights"
    __table_args__ = (
        Index("ix_life_ledger_insights_user_id", "user_id"),
        Index(
            "ix_life_ledger_insights_user_module_type",
            "user_id",
            "module",
            "insight_type",
        ),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    module = db.Column(db.String(32), nullable=False)
    insight_type = db.Column(db.String(64), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action_url = db.Column(db.String(512), nullable=True)
    dismissed = db.Column(
        db.Boolean, nullable=False, default=False, server_default=sa_false()
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
