#!/usr/bin/env python3
"""Per-user health insurance plan records for the Health Insurance Advisor."""

from datetime import datetime

from sqlalchemy import Numeric

from .database import db


class HealthInsurancePlan(db.Model):
    """Uploaded or manually entered health plan details for a user."""

    __tablename__ = "health_insurance_plans"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    upload_batch_id = db.Column(db.String(36), nullable=True)
    plan_name = db.Column(db.String(200), nullable=False)
    plan_type = db.Column(db.String(20), nullable=True)
    insurer_name = db.Column(db.String(200), nullable=True)
    plan_year = db.Column(db.Integer, nullable=True)
    monthly_premium_employee = db.Column(Numeric(10, 2), nullable=True)
    monthly_premium_employee_spouse = db.Column(Numeric(10, 2), nullable=True)
    monthly_premium_family = db.Column(Numeric(10, 2), nullable=True)
    annual_deductible_individual = db.Column(Numeric(10, 2), nullable=True)
    annual_deductible_family = db.Column(Numeric(10, 2), nullable=True)
    out_of_pocket_max_individual = db.Column(Numeric(10, 2), nullable=True)
    out_of_pocket_max_family = db.Column(Numeric(10, 2), nullable=True)
    coinsurance_pct = db.Column(db.Integer, nullable=True)
    copay_primary_care = db.Column(Numeric(10, 2), nullable=True)
    copay_specialist = db.Column(Numeric(10, 2), nullable=True)
    copay_er = db.Column(Numeric(10, 2), nullable=True)
    rx_tier1 = db.Column(Numeric(10, 2), nullable=True)
    rx_tier2 = db.Column(Numeric(10, 2), nullable=True)
    rx_tier3 = db.Column(Numeric(10, 2), nullable=True)
    rx_tier4 = db.Column(Numeric(10, 2), nullable=True)
    has_hsa_eligible = db.Column(db.Boolean, nullable=False, default=False)
    employer_hsa_contribution = db.Column(Numeric(10, 2), nullable=True)
    in_network_only = db.Column(db.Boolean, nullable=True)
    raw_document_path = db.Column(db.String(500), nullable=True)
    parse_status = db.Column(db.String(20), nullable=False, default="pending")
    parsed_json = db.Column(db.JSON, nullable=True)
    parsed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship(
        "User", backref=db.backref("health_insurance_plans", lazy="dynamic")
    )

    def __repr__(self) -> str:
        return f"<HealthInsurancePlan id={self.id} user_id={self.user_id}>"
