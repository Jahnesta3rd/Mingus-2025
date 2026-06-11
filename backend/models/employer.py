#!/usr/bin/env python3
"""SEC EDGAR employer registry, health snapshots, and layoff events (CR9a)."""

from datetime import datetime

from sqlalchemy import Index, Numeric

from .database import db


class Employer(db.Model):
    """Public company identified by SEC CIK."""

    __tablename__ = "employers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cik = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    ticker = db.Column(db.String(10), nullable=True)
    sic_code = db.Column(db.String(4), nullable=True)
    sic_desc = db.Column(db.String(100), nullable=True)
    exchange = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    health_snapshots = db.relationship(
        "EmployerHealthSnapshot",
        back_populates="employer",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    layoff_events = db.relationship(
        "LayoffEvent",
        back_populates="employer",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Employer id={self.id} cik={self.cik!r} name={self.name!r}>"


class EmployerHealthSnapshot(db.Model):
    """Point-in-time employer financial health score and components."""

    __tablename__ = "employer_health_snapshots"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employer_id = db.Column(
        db.Integer,
        db.ForeignKey("employers.id", ondelete="CASCADE"),
        nullable=False,
    )
    score = db.Column(Numeric(5, 2), nullable=True)
    revenue_delta_score = db.Column(Numeric(5, 2), nullable=True)
    margin_score = db.Column(Numeric(5, 2), nullable=True)
    fcf_score = db.Column(Numeric(5, 2), nullable=True)
    runway_score = db.Column(Numeric(5, 2), nullable=True)
    leverage_score = db.Column(Numeric(5, 2), nullable=True)
    revenue_ttm = db.Column(Numeric(20, 2), nullable=True)
    operating_margin = db.Column(Numeric(8, 4), nullable=True)
    free_cash_flow = db.Column(Numeric(20, 2), nullable=True)
    cash_and_equiv = db.Column(Numeric(20, 2), nullable=True)
    total_debt = db.Column(Numeric(20, 2), nullable=True)
    fiscal_period_end = db.Column(db.Date, nullable=True)
    filing_accession = db.Column(db.String(25), nullable=True)
    data_source = db.Column(db.String(20), nullable=False, default="sec_edgar")
    is_stale = db.Column(db.Boolean, nullable=False, default=False)
    refreshed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    employer = db.relationship("Employer", back_populates="health_snapshots")

    __table_args__ = (
        Index(
            "ix_employer_health_snapshots_employer_refreshed",
            "employer_id",
            "refreshed_at",
            postgresql_ops={"refreshed_at": "DESC"},
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EmployerHealthSnapshot id={self.id} employer_id={self.employer_id} "
            f"score={self.score}>"
        )


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
    review_state = db.Column(db.String(20), nullable=False, default="auto")
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
