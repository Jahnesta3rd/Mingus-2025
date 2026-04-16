#!/usr/bin/env python3
"""Bug reports submitted from the app (admin triage + user confirmation emails)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from .database import db


class BugReport(db.Model):
    __tablename__ = "bug_reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_number = db.Column(db.String(12), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_email = db.Column(db.String(255), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_tier = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=False)
    current_route = db.Column(db.String(255), nullable=True)
    browser_info = db.Column(db.String(255), nullable=True)
    balance_status = db.Column(db.String(20), nullable=True)
    last_feature = db.Column(db.String(100), nullable=True)
    onboarding_complete = db.Column(db.Boolean, default=False, nullable=False)
    account_age_days = db.Column(db.Integer, nullable=True)
    is_beta = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default="open", nullable=False)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    resolved_at = db.Column(db.DateTime, nullable=True)

    ALLOWED_STATUS = frozenset({"open", "in_progress", "resolved", "wont_fix"})

    @classmethod
    def next_ticket_number(cls) -> str:
        m = db.session.query(func.max(cls.id)).scalar()
        n = (m or 0) + 1
        return f"MNG-{n:04d}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "user_name": self.user_name,
            "user_tier": self.user_tier,
            "description": self.description,
            "current_route": self.current_route,
            "browser_info": self.browser_info,
            "balance_status": self.balance_status,
            "last_feature": self.last_feature,
            "onboarding_complete": self.onboarding_complete,
            "account_age_days": self.account_age_days,
            "is_beta": self.is_beta,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
