#!/usr/bin/env python3
"""Per-user Spirit & Finance practice reminder preferences."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.schema import Identity

from .database import db

DEFAULT_REMINDER_DAYS = "mon,tue,wed,thu,fri,sat,sun"


class SpiritNotificationPrefs(db.Model):
    """One row per user: daily practice reminder schedule and nudge toggles."""

    __tablename__ = "spirit_notification_prefs"

    id = db.Column(db.Integer, Identity(always=False), primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reminders_enabled = db.Column(db.Boolean, nullable=False, default=True)
    reminder_hour = db.Column(db.Integer, nullable=False, default=8)
    reminder_timezone = db.Column(db.String(50), nullable=False, default="America/New_York")
    reminder_days = db.Column(db.String(50), nullable=False, default=DEFAULT_REMINDER_DAYS)
    streak_nudge_enabled = db.Column(db.Boolean, nullable=False, default=True)
    last_reminder_sent = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = db.relationship("User", backref=db.backref("spirit_notification_prefs", uselist=False))

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_spirit_notification_prefs_user_id"),
        Index("ix_spirit_notification_prefs_reminders_enabled", "reminders_enabled"),
    )

    def to_api_dict(self) -> dict:
        return {
            "reminders_enabled": bool(self.reminders_enabled),
            "reminder_hour": int(self.reminder_hour),
            "reminder_timezone": self.reminder_timezone,
            "reminder_days": self.reminder_days,
            "streak_nudge_enabled": bool(self.streak_nudge_enabled),
            "last_reminder_sent": self.last_reminder_sent.isoformat() + "Z"
            if self.last_reminder_sent
            else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
        }
