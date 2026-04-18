#!/usr/bin/env python3
"""Persisted modular onboarding progress (per-user, one row)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.ext.hybrid import hybrid_property

from backend.constants.onboarding import MODULE_ORDER
from backend.models.database import db


class OnboardingProgress(db.Model):
    """Tracks which onboarding modules are done or skipped for resume across sessions."""

    __tablename__ = "onboarding_progress"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    completed_modules = db.Column(db.JSON, nullable=False, default=list)
    skipped_modules = db.Column(db.JSON, nullable=False, default=list)
    current_module = db.Column(db.String(64), nullable=False, default="income")
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_activity_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @hybrid_property
    def is_complete(self) -> bool:
        """True when every module id is in completed and/or skipped (same rule as completed_at)."""
        seen = set(self.completed_modules or []) | set(self.skipped_modules or [])
        return seen.issuperset(set(MODULE_ORDER))

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "completed_modules": list(self.completed_modules or []),
            "skipped_modules": list(self.skipped_modules or []),
            "current_module": self.current_module,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_activity_at": self.last_activity_at.isoformat()
            if self.last_activity_at
            else None,
            "is_complete": self.is_complete,
        }

    def __repr__(self) -> str:
        return f"<OnboardingProgress user_id={self.user_id} complete={self.is_complete}>"
