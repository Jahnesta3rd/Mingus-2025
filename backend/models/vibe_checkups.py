#!/usr/bin/env python3
"""
Vibe Checkups lead funnel: anonymous quiz sessions, captured leads, and funnel analytics.
"""

import uuid
from datetime import datetime

from sqlalchemy import Index, false as sa_false, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


# Documented event_type values for VibeCheckupsFunnelEvent.event_type
VIBE_CHECKUPS_EVENT_TYPES = (
    "quiz_started",
    "quiz_completed",
    "email_gate_shown",
    "email_captured",
    "projection_unlocked",
    "share_card_generated",
    "mingus_cta_clicked",
    "mingus_converted",
)


class VibeCheckupsSession(db.Model):
    """Anonymous quiz progress for the Vibe Checkups funnel."""

    __tablename__ = "vibe_checkups_sessions"
    __table_args__ = (
        Index(
            "ix_vibe_checkups_sessions_utm_source_utm_medium",
            "utm_source",
            "utm_medium",
        ),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    answers = db.Column(db.JSON, nullable=False, default=lambda: {})
    current_question = db.Column(db.Integer, nullable=False, default=0)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    utm_source = db.Column(db.String(255), nullable=True)
    utm_medium = db.Column(db.String(255), nullable=True)
    utm_campaign = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<VibeCheckupsSession id={self.id!r} token={self.session_token!r}>"


class VibeCheckupsLead(db.Model):
    """Email capture plus scores and projection payload for a completed checkup."""

    __tablename__ = "vibe_checkups_leads"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_checkups_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email = db.Column(db.String(255), nullable=False, index=True)
    emotional_score = db.Column(db.Integer, nullable=False)
    financial_score = db.Column(db.Integer, nullable=False)
    verdict_label = db.Column(db.String(255), nullable=False)
    verdict_emoji = db.Column(
        db.String(16), nullable=False, server_default=text("''")
    )
    total_annual_projection = db.Column(db.Integer, nullable=False)
    projection_data = db.Column(db.JSON, nullable=False)
    unlocked_projection = db.Column(db.Boolean, nullable=False, default=False)
    unlock_paid = db.Column(db.Boolean, nullable=False, default=False)
    unlock_amount_cents = db.Column(db.Integer, nullable=True)
    mingus_signup_clicked = db.Column(db.Boolean, nullable=False, default=False)
    mingus_converted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    email_sequence_started = db.Column(db.Boolean, nullable=False, default=False)
    email_opt_out = db.Column(
        db.Boolean, nullable=False, server_default=sa_false()
    )

    def __repr__(self):
        return f"<VibeCheckupsLead id={self.id!r} email={self.email!r}>"


class VibeCheckupsFunnelEvent(db.Model):
    """Analytics and conversion events along the Vibe Checkups funnel."""

    __tablename__ = "vibe_checkups_funnel_events"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_checkups_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    lead_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_checkups_leads.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type = db.Column(db.String(64), nullable=False, index=True)
    event_data = db.Column(db.JSON, nullable=True)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    utm_source = db.Column(db.String(255), nullable=True)
    utm_medium = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<VibeCheckupsFunnelEvent id={self.id!r} type={self.event_type!r}>"
