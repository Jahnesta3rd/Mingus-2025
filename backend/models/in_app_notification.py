#!/usr/bin/env python3
"""Simple in-app notification rows for product messages (e.g. spirit reminders)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index
from sqlalchemy.schema import Identity

from .database import db


class InAppNotification(db.Model):
    __tablename__ = "in_app_notifications"

    id = db.Column(db.Integer, Identity(always=False), primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("in_app_notifications", lazy="dynamic"))

    __table_args__ = (Index("ix_in_app_notifications_user_created", "user_id", "created_at"),)
