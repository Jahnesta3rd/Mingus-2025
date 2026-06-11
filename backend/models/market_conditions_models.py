#!/usr/bin/env python3
"""Models for market conditions caching and seeded OES wage data (#165)."""

from datetime import datetime

from .database import db


class OesWageData(db.Model):
    """Seeded BLS OES wage percentiles by career field and MSA."""

    __tablename__ = "oes_wage_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bls_career_field = db.Column(db.String(100), nullable=False, index=True)
    msa_code = db.Column(db.String(20), nullable=False, index=True)
    msa_name = db.Column(db.String(100), nullable=False)
    pct_10 = db.Column(db.Integer, nullable=False)
    pct_25 = db.Column(db.Integer, nullable=False)
    pct_50 = db.Column(db.Integer, nullable=False)
    pct_75 = db.Column(db.Integer, nullable=False)
    pct_90 = db.Column(db.Integer, nullable=False)
    source_year = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "bls_career_field",
            "msa_code",
            name="uq_oes_wage_data_field_msa",
        ),
    )


class MarketDataCache(db.Model):
    """TTL cache for national/regional market indicator fetches."""

    __tablename__ = "market_data_cache"

    key = db.Column(db.String(200), primary_key=True)
    value = db.Column(db.JSON, nullable=False)
    fetched_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
