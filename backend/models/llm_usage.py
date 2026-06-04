#!/usr/bin/env python3
"""LLM API usage logging for cost tracking and observability."""

from datetime import datetime

from .database import db


class LlmUsage(db.Model):
    """One row per LLM or classification call."""

    __tablename__ = "llm_usage"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    feature = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    input_tokens = db.Column(db.Integer, nullable=False)
    output_tokens = db.Column(db.Integer, nullable=False)
    total_tokens = db.Column(db.Integer, nullable=False)
    cost_usd = db.Column(db.Numeric(10, 6), nullable=False)
    classification_source = db.Column(db.String(20), nullable=True)
    result_field = db.Column(db.String(100), nullable=True)
    confidence = db.Column(db.Numeric(3, 2), nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("llm_usage_rows", lazy="dynamic"))

    def __repr__(self) -> str:
        return f"<LlmUsage id={self.id} feature={self.feature!r} model={self.model!r}>"
