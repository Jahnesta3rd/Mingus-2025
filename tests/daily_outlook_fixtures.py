"""Shared helpers for daily outlook pytest suites."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.models.daily_outlook import DailyOutlook
from backend.models.database import db


def seed_today_outlook(user_id: int) -> DailyOutlook:
    """Create today's outlook so POST endpoints can reach validation/business logic."""
    outlook = DailyOutlook(
        user_id=user_id,
        date=date.today(),
        balance_score=75,
        financial_weight=Decimal("0.30"),
        wellness_weight=Decimal("0.25"),
        relationship_weight=Decimal("0.25"),
        career_weight=Decimal("0.20"),
        quick_actions=[{"id": "test", "title": "Test", "description": "Test action"}],
        streak_count=1,
    )
    db.session.add(outlook)
    db.session.commit()
    return outlook
