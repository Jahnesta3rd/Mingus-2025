#!/usr/bin/env python3
"""Per-user career commitment classification and review tracking."""

from datetime import datetime

from sqlalchemy import Index, UniqueConstraint

from .database import db


class CareerCommitmentProfile(db.Model):
    """One row per user; stores commitment type, signals, and review stage."""

    __tablename__ = "career_commitment_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_career_commitment_profiles_user_id"),
        Index("ix_career_commitment_profiles_user_id", "user_id"),
        Index(
            "ix_career_commitment_profiles_user_id_review_stage",
            "user_id",
            "review_stage",
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    commitment_type = db.Column(db.String(20), nullable=True)
    commitment_score = db.Column(db.Integer, nullable=True)
    skill_development_frequency = db.Column(db.Integer, nullable=True)
    field_research_done = db.Column(db.Boolean, nullable=True)
    real_world_signal = db.Column(db.Boolean, nullable=True)
    pivot_intent = db.Column(db.String(30), nullable=True)
    classified_at = db.Column(db.DateTime, nullable=True)
    last_reviewed_at = db.Column(db.DateTime, nullable=True)
    review_stage = db.Column(db.String(20), nullable=True, default="initial")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True,
    )

    user = db.relationship(
        "User",
        backref=db.backref("career_commitment_profile", uselist=False),
    )

    def __repr__(self) -> str:
        return (
            f"<CareerCommitmentProfile id={self.id} user_id={self.user_id} "
            f"commitment_type={self.commitment_type!r} review_stage={self.review_stage!r}>"
        )
