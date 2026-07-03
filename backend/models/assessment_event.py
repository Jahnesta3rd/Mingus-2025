#!/usr/bin/env python3
"""Funnel analytics events for lead-magnet assessments."""

from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from .database import db


class AssessmentEvent(db.Model):
    __tablename__ = "assessment_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assessment_id = db.Column(db.Integer, nullable=False, index=True)
    email_hash = db.Column(db.String(255), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    token = db.Column(db.String(255), nullable=True)
    event_metadata = db.Column("metadata", JSONB, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(
        self,
        assessment_id,
        email_hash,
        event_type,
        token=None,
        metadata=None,
    ):
        self.assessment_id = assessment_id
        self.email_hash = email_hash
        self.event_type = event_type
        self.token = token
        self.event_metadata = metadata or {}
