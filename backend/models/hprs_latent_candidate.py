#!/usr/bin/env python3
"""Latent HPRS candidate tracking — users without buy goal who meet readiness thresholds."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Index, UniqueConstraint

from .database import db


class HprsLatentCandidate(db.Model):
    """One row per user evaluated for latent home-purchase readiness nudges."""

    __tablename__ = "hprs_latent_candidates"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_hprs_latent_candidates_user_id"),
        Index("ix_hprs_latent_candidates_user_id", "user_id"),
        Index("ix_hprs_latent_candidates_status", "status"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    first_evaluated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    last_evaluated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    threshold_met_at = db.Column(db.DateTime, nullable=True)
    nudge_sent_at = db.Column(db.DateTime, nullable=True)
    nudge_type = db.Column(db.String(20), nullable=True)
    nudge_text = db.Column(db.Text, nullable=True)
    user_engaged_at = db.Column(db.DateTime, nullable=True)
    snoozed_until = db.Column(db.DateTime, nullable=True)
    activated_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="monitoring")

    user = db.relationship(
        "User",
        backref=db.backref("hprs_latent_candidate_row", uselist=False),
    )

    def __repr__(self) -> str:
        return (
            f"<HprsLatentCandidate user_id={self.user_id!r} status={self.status!r} "
            f"nudge_type={self.nudge_type!r}>"
        )
