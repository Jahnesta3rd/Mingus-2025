#!/usr/bin/env python3
"""LLM-generated Home Purchase Readiness action plan (HPRS)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from .database import db


class HprsPlan(db.Model):
    """Personalized HPRS improvement plan; multiple rows per user, one marked active."""

    __tablename__ = "hprs_plans"
    __table_args__ = (
        Index("ix_hprs_plans_user_id_is_active", "user_id", "is_active"),
    )

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("hprs_scores.id", ondelete="SET NULL"),
        nullable=True,
    )
    plan_summary = db.Column(db.Text, nullable=True)
    action_steps = db.Column(JSONB, nullable=False, default=list)
    focus_pillar = db.Column(db.String(30), nullable=True)
    generated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    llm_model = db.Column(db.String(80), nullable=True)

    user = db.relationship("User", backref=db.backref("hprs_plans", lazy="dynamic"))
    score = db.relationship("HprsScore", back_populates="plans")

    def __repr__(self) -> str:
        return (
            f"<HprsPlan user_id={self.user_id!r} active={self.is_active!r} "
            f"generated_at={self.generated_at!r}>"
        )
