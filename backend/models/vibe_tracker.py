#!/usr/bin/env python3
"""
Vibe Tracker: user-labeled tracked people, repeated assessments, and trend summaries.

Nickname is a user-assigned label only; stored data is the account owner's own responses.
"""

import uuid
from datetime import datetime

from sqlalchemy import Index, UniqueConstraint, false as sa_false
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class VibeTrackedPerson(db.Model):
    """A labeled entry the user tracks over time (not a third-party profile)."""

    __tablename__ = "vibe_tracked_people"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "nickname",
            name="uq_vibe_tracked_people_user_id_nickname",
        ),
        Index("ix_vibe_tracked_people_user_id_is_archived", "user_id", "is_archived"),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nickname = db.Column(db.String(30), nullable=False)
    card_type = db.Column(
        db.String(20),
        nullable=False,
        default="person",
    )
    emoji = db.Column(db.String(8), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_assessed_at = db.Column(db.DateTime, nullable=True)
    is_archived = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=sa_false(),
    )
    archived_at = db.Column(db.DateTime, nullable=True)
    assessment_count = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<VibeTrackedPerson id={self.id!r} nickname={self.nickname!r} user_id={self.user_id!r}>"


class VibePersonAssessment(db.Model):
    """One completed assessment snapshot for a tracked person."""

    __tablename__ = "vibe_person_assessments"
    __table_args__ = (
        Index(
            "ix_vibe_person_assessments_tracked_person_completed_at",
            "tracked_person_id",
            "completed_at",
        ),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracked_person_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_tracked_people.id", ondelete="CASCADE"),
        nullable=False,
    )
    lead_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_checkups_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    emotional_score = db.Column(db.Integer, nullable=False)
    financial_score = db.Column(db.Integer, nullable=False)
    verdict_label = db.Column(db.String(100), nullable=False)
    verdict_emoji = db.Column(db.String(8), nullable=True)
    annual_projection = db.Column(db.Integer, nullable=False)
    answers_snapshot = db.Column(db.JSON, nullable=False, default=dict)
    completed_at = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<VibePersonAssessment id={self.id!r} tracked_person_id={self.tracked_person_id!r}>"


class VibePersonTrend(db.Model):
    """Aggregated trend and stay/go signal for one tracked person (one row per person)."""

    __tablename__ = "vibe_person_trends"
    __table_args__ = (
        UniqueConstraint(
            "tracked_person_id",
            name="uq_vibe_person_trends_tracked_person_id",
        ),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracked_person_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_tracked_people.id", ondelete="CASCADE"),
        nullable=False,
    )
    trend_direction = db.Column(db.String(20), nullable=False)
    emotional_delta = db.Column(db.Integer, nullable=True)
    financial_delta = db.Column(db.Integer, nullable=True)
    projection_delta = db.Column(db.Integer, nullable=True)
    assessment_count = db.Column(db.Integer, nullable=False, default=0)
    last_computed_at = db.Column(db.DateTime, nullable=False)
    stay_or_go_signal = db.Column(db.String(20), nullable=True)
    stay_or_go_confidence = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<VibePersonTrend id={self.id!r} tracked_person_id={self.tracked_person_id!r} direction={self.trend_direction!r}>"
