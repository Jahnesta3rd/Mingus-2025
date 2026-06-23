#!/usr/bin/env python3
"""Company screen scoring: layered employer risk assessment and jargon cache."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from .database import db


def _company_screen_expires_at() -> datetime:
    return datetime.utcnow() + timedelta(days=7)


def _jargon_cache_expires_at() -> datetime:
    return datetime.utcnow() + timedelta(days=14)


class CompanyScreen(db.Model):
    """Multi-layer company risk screen for a user (public or private employer)."""

    __tablename__ = "company_screens"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employer_cik = db.Column(db.String(20), nullable=True)
    employer_name_text = db.Column(db.String(200), nullable=False)
    composite_score = db.Column(db.Integer, nullable=True)
    composite_band = db.Column(db.String(20), nullable=True)
    layer1_score = db.Column(db.Integer, nullable=True)
    layer1_status = db.Column(db.String(20), nullable=False, default="pending")
    layer2_score = db.Column(db.Integer, nullable=True)
    layer2_status = db.Column(db.String(20), nullable=False, default="pending")
    layer3_band = db.Column(db.String(30), nullable=True)
    layer3_status = db.Column(db.String(20), nullable=False, default="pending")
    layoff_event_detected = db.Column(db.Boolean, nullable=False, default=False)
    layoff_event_date = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False, default=_company_screen_expires_at)
    screens_used_this_cycle = db.Column(db.Integer, nullable=False, default=1)

    user = db.relationship("User", backref=db.backref("company_screens", lazy="dynamic"))
    questions = db.relationship(
        "CompanyScreenQuestion",
        back_populates="screen",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<CompanyScreen id={self.id!r} user_id={self.user_id!r} "
            f"employer={self.employer_name_text!r}>"
        )


class CompanyScreenQuestion(db.Model):
    """Follow-up question surfaced during or after a company screen."""

    __tablename__ = "company_screen_questions"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    screen_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("company_screens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text = db.Column(db.Text, nullable=False)
    flag_source = db.Column(db.String(50), nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    dismissed_at = db.Column(db.DateTime, nullable=True)
    copied_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    screen = db.relationship("CompanyScreen", back_populates="questions")

    def __repr__(self) -> str:
        return (
            f"<CompanyScreenQuestion id={self.id!r} screen_id={self.screen_id!r} "
            f"flag_source={self.flag_source!r}>"
        )


class CompanyJargonCache(db.Model):
    """Cached jargon analysis for employer text content (14-day TTL)."""

    __tablename__ = "company_jargon_cache"
    __table_args__ = (
        UniqueConstraint(
            "employer_name_hash",
            "raw_text_hash",
            name="uq_company_jargon_cache_name_text_hash",
        ),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employer_cik = db.Column(db.String(20), nullable=True)
    employer_name_hash = db.Column(db.String(64), nullable=False)
    raw_text_hash = db.Column(db.String(64), nullable=False)
    jargon_score = db.Column(db.Integer, nullable=False)
    jargon_density_pct = db.Column(db.Float, nullable=True)
    top_jargon_phrases = db.Column(JSONB, nullable=True)
    scored_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False, default=_jargon_cache_expires_at)

    def __repr__(self) -> str:
        return (
            f"<CompanyJargonCache id={self.id!r} "
            f"employer_name_hash={self.employer_name_hash!r}>"
        )
