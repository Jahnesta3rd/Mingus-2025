#!/usr/bin/env python3
"""Independence cost assessment history."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .database import db


class IndependenceCostAssessment(db.Model):
    __tablename__ = "independence_cost_assessments"

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = db.Column(
        PG_UUID(as_uuid=True),
        db.ForeignKey("vibe_tracked_people.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    zip_code = db.Column(db.String(5), nullable=True)
    city_name = db.Column(db.String(100), nullable=True)
    market_rent_1br = db.Column(db.Numeric(8, 2), nullable=True)
    estimated_housing = db.Column(db.Numeric(8, 2), nullable=False)
    estimated_utilities = db.Column(db.Numeric(8, 2), nullable=False)
    estimated_food = db.Column(db.Numeric(8, 2), nullable=False)
    estimated_transportation = db.Column(db.Numeric(8, 2), nullable=False)
    estimated_phone_internet = db.Column(db.Numeric(8, 2), nullable=False)
    estimated_other = db.Column(db.Numeric(8, 2), nullable=False)
    total_monthly_solo = db.Column(db.Numeric(8, 2), nullable=False)
    total_startup_cost = db.Column(db.Numeric(10, 2), nullable=True)
    current_housing_contribution = db.Column(db.Numeric(8, 2), nullable=True)
    monthly_independence_gap = db.Column(db.Numeric(8, 2), nullable=True)
    months_to_save_startup = db.Column(db.Numeric(8, 2), nullable=True)
    partner_emotional_score_current = db.Column(db.Integer, nullable=True)
    partner_emotional_trend = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<IndependenceCostAssessment user_id={self.user_id!r} person_id={self.person_id!r}>"
