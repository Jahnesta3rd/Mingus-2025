#!/usr/bin/env python3
"""Rent vs. Buy gap analysis results and cached homeownership action plans."""

from datetime import datetime

from sqlalchemy import Numeric

from .database import db


class GapAnalysisResult(db.Model):
    """Snapshot of gap dimensions and LLM-generated action plan for a user."""

    __tablename__ = "gap_analysis_results"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Calculator inputs (snapshot)
    home_price = db.Column(Numeric(12, 2), nullable=False)
    down_payment_pct = db.Column(Numeric(5, 2), nullable=False)
    interest_rate = db.Column(Numeric(5, 3), nullable=False)
    loan_term_years = db.Column(db.Integer, nullable=False)
    timeline_months = db.Column(db.Integer, nullable=False)

    # Gap dimensions (5)
    gap_income = db.Column(Numeric(12, 2), nullable=True)
    gap_savings_rate = db.Column(Numeric(12, 2), nullable=True)
    gap_down_payment = db.Column(Numeric(12, 2), nullable=True)
    gap_dti = db.Column(Numeric(7, 4), nullable=True)
    gap_credit = db.Column(db.Integer, nullable=True)

    # Severity per dimension
    income_severity = db.Column(db.String(20), nullable=True)
    savings_severity = db.Column(db.String(20), nullable=True)
    down_payment_severity = db.Column(db.String(20), nullable=True)
    dti_severity = db.Column(db.String(20), nullable=True)
    credit_severity = db.Column(db.String(20), nullable=True)

    # Ideal profile computed values
    required_gross_income = db.Column(Numeric(12, 2), nullable=True)
    required_monthly_savings = db.Column(Numeric(10, 2), nullable=True)
    target_down_payment = db.Column(Numeric(12, 2), nullable=True)
    monthly_piti = db.Column(Numeric(10, 2), nullable=True)

    # LLM action plan (cached)
    action_plan_json = db.Column(db.JSON, nullable=True)
    plan_generated_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship(
        "User", backref=db.backref("gap_analysis_results", lazy="dynamic")
    )

    def __repr__(self) -> str:
        return f"<GapAnalysisResult id={self.id} user_id={self.user_id}>"
