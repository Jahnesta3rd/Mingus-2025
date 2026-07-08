#!/usr/bin/env python3
"""Relationship milestone monthly check-in records."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from .database import db


class RelationshipMilestoneCheckin(db.Model):
    __tablename__ = "relationship_milestone_checkins"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    vibe_trend = db.Column(db.String(20), nullable=False)
    feels_safe = db.Column(db.String(10), nullable=False)
    needs_to_leave_sooner = db.Column(db.Boolean, nullable=False, default=False)
    on_track_savings = db.Column(db.Boolean, nullable=False, default=False)
    prefer_leave_now = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False)
    emergency_flags = db.Column(JSONB, nullable=True)
    next_steps = db.Column(JSONB, nullable=True)
    resources_provided = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __repr__(self) -> str:
        return (
            f"<RelationshipMilestoneCheckin user_id={self.user_id!r} "
            f"person_id={self.person_id!r} status={self.status!r}>"
        )
