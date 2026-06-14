#!/usr/bin/env python3
"""Cached Health Insurance Advisor recommendation for a user."""

from datetime import datetime

from sqlalchemy import Numeric

from .database import db


class HealthInsuranceRecommendation(db.Model):
    """One active recommendation row per user from the HIA engine."""

    __tablename__ = "health_insurance_recommendations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    generated_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    expires_at = db.Column(db.DateTime, nullable=False)
    recommended_plan_id = db.Column(
        db.Integer,
        db.ForeignKey("health_insurance_plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    runner_up_plan_id = db.Column(
        db.Integer,
        db.ForeignKey("health_insurance_plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    accepted_plan_id = db.Column(
        db.Integer,
        db.ForeignKey("health_insurance_plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    recommendation_json = db.Column(db.JSON, nullable=False)
    expected_annual_cost_recommended = db.Column(Numeric(10, 2), nullable=True)
    expected_annual_cost_runner_up = db.Column(Numeric(10, 2), nullable=True)
    hsa_recommended = db.Column(db.Boolean, nullable=True)
    hsa_annual_benefit = db.Column(Numeric(10, 2), nullable=True)
    risk_flags_json = db.Column(db.JSON, nullable=True)
    benchmark_context_json = db.Column(db.JSON, nullable=True)
    model_version = db.Column(db.String(50), nullable=False, default="claude-sonnet-4-6")
    input_snapshot_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship(
        "User", backref=db.backref("health_insurance_recommendation", uselist=False)
    )
    recommended_plan = db.relationship(
        "HealthInsurancePlan",
        foreign_keys=[recommended_plan_id],
        backref=db.backref("recommendations_as_recommended", lazy="dynamic"),
    )
    runner_up_plan = db.relationship(
        "HealthInsurancePlan",
        foreign_keys=[runner_up_plan_id],
        backref=db.backref("recommendations_as_runner_up", lazy="dynamic"),
    )
    accepted_plan = db.relationship(
        "HealthInsurancePlan",
        foreign_keys=[accepted_plan_id],
        backref=db.backref("recommendations_as_accepted", lazy="dynamic"),
    )

    def __repr__(self) -> str:
        return f"<HealthInsuranceRecommendation id={self.id} user_id={self.user_id}>"
