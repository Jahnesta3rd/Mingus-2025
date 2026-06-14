#!/usr/bin/env python3
"""Per-user debt snapshot for the Debt Reduction Analyzer."""

from datetime import datetime

from sqlalchemy import Numeric

from .database import db


class DebtProfile(db.Model):
    """One row per user; stores revolving, installment, student, and BNPL debt."""

    __tablename__ = "debt_profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Section 1: Credit Cards & Store Cards
    revolving_balance = db.Column(Numeric(12, 2), nullable=True)
    revolving_apr = db.Column(Numeric(5, 2), nullable=True)
    revolving_min_payment = db.Column(Numeric(10, 2), nullable=True)
    revolving_apr_unknown = db.Column(db.Boolean, nullable=False, default=False)

    # Section 2: Loans (Auto, Personal, Medical)
    installment_balance = db.Column(Numeric(12, 2), nullable=True)
    installment_apr = db.Column(Numeric(5, 2), nullable=True)
    installment_payment = db.Column(Numeric(10, 2), nullable=True)

    # Section 3: Federal Student Loans
    federal_student_balance = db.Column(Numeric(12, 2), nullable=True)
    federal_student_payment = db.Column(Numeric(10, 2), nullable=True)
    on_idr_plan = db.Column(db.Boolean, nullable=False, default=False)
    pursuing_pslf = db.Column(db.Boolean, nullable=False, default=False)

    # Section 4: Private Student Loans
    private_student_balance = db.Column(Numeric(12, 2), nullable=True)
    private_student_apr = db.Column(Numeric(5, 2), nullable=True)

    # Section 5: Buy Now Pay Later
    bnpl_balance = db.Column(Numeric(12, 2), nullable=True)
    bnpl_monthly_payment = db.Column(Numeric(10, 2), nullable=True)
    bnpl_active_plans = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship("User", backref=db.backref("debt_profile", uselist=False))

    def __repr__(self) -> str:
        return f"<DebtProfile id={self.id} user_id={self.user_id}>"
