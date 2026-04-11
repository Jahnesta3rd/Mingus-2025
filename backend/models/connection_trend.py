#!/usr/bin/env python3
"""
Connection Trend: behavioral observation check-ins per roster person (fade scale).
"""

import uuid
from datetime import datetime

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class ConnectionTrendAssessment(db.Model):
    """One Connection Trend assessment snapshot for a tracked person."""

    __tablename__ = "connection_trend_assessments"
    __table_args__ = (
        Index(
            "ix_connection_trend_assessments_user_person_assessed_at",
            "user_id",
            "person_id",
            "assessed_at",
        ),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # users.id is Integer in this codebase (see VibeTrackedPerson).
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    person_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_tracked_people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assessed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    q1_response_pattern = db.Column(db.SmallInteger, nullable=True)
    q2_initiative = db.Column(db.SmallInteger, nullable=True)
    q3_followthrough = db.Column(db.SmallInteger, nullable=True)
    q4_future_talk = db.Column(db.SmallInteger, nullable=True)
    q5_social_visibility = db.Column(db.SmallInteger, nullable=True)
    q6_reciprocity = db.Column(db.SmallInteger, nullable=True)
    q7_gut_signal = db.Column(db.SmallInteger, nullable=True)

    raw_score = db.Column(db.SmallInteger, nullable=True)
    normalized_score = db.Column(db.SmallInteger, nullable=True)
    fade_tier = db.Column(db.String(20), nullable=True)
    pattern_type = db.Column(db.String(30), nullable=True)

    def __repr__(self):
        return (
            f"<ConnectionTrendAssessment id={self.id!r} "
            f"person_id={self.person_id!r} user_id={self.user_id!r}>"
        )
