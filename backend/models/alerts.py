#!/usr/bin/env python3
"""In-app financial / vibe alerts for dashboard surfaces."""

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class UserAlert(db.Model):
    """User-scoped alert row (unread until read_at is set)."""

    __tablename__ = "user_alerts"
    __table_args__ = (db.Index("ix_user_alerts_user_id_read_at", "user_id", "read_at"),)

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    action_label = db.Column(db.String(100), nullable=False)
    action_route = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)
    dismissed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<UserAlert id={self.id!r} user_id={self.user_id!r} type={self.alert_type!r}>"
