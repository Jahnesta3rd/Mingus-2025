#!/usr/bin/env python3
"""8-K Item 2.05 layoff disclosure events tied to employers."""

from datetime import datetime

from sqlalchemy import Index, Numeric

from .database import db


class LayoffEvent(db.Model):
    """8-K Item 2.05 layoff disclosure tied to an employer."""

    __tablename__ = "layoff_events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employer_id = db.Column(
        db.Integer,
        db.ForeignKey("employers.id", ondelete="CASCADE"),
        nullable=False,
    )
    filing_date = db.Column(db.Date, nullable=False)
    accession_number = db.Column(db.String(25), nullable=False)
    item_number = db.Column(db.String(10), nullable=False, default="2.05")
    affected_count = db.Column(db.Integer, nullable=True)
    confidence = db.Column(Numeric(4, 3), nullable=False)
    raw_excerpt = db.Column(db.Text, nullable=True)
    source = db.Column(
        db.String(20),
        nullable=False,
        server_default="8k_filing",
    )
    # Valid values: '8k_filing' | 'warn_act'
    review_state = db.Column(
        db.String(20),
        nullable=True,
        default=None,
    )
    # Valid values: None (confirmed/auto) | 'needs_review' | 'confirmed' | 'rejected'
    expires_at = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    employer = db.relationship("Employer", back_populates="layoff_events")

    __table_args__ = (
        Index(
            "ix_layoff_events_employer_filing_date",
            "employer_id",
            "filing_date",
            postgresql_ops={"filing_date": "DESC"},
        ),
        Index("ix_layoff_events_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<LayoffEvent id={self.id} employer_id={self.employer_id} "
            f"filing_date={self.filing_date}>"
        )
