#!/usr/bin/env python3
"""
Wellness–Finance Correlation Engine for Mingus Application

Computes Pearson correlations between wellness metrics and spending from weekly check-ins.
Used by InsightGenerator for correlation-based insights.
"""

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Any, Optional

from sqlalchemy import func

logger = logging.getLogger(__name__)

_SPENDING_DELTA_UNAVAILABLE: Dict[str, Any] = {
    "available": False,
    "total_this_week": None,
    "baseline_avg": None,
    "delta_amount": None,
    "delta_pct": None,
    "by_category": None,
}


@dataclass
class CorrelationResult:
    """Result of a single correlation analysis."""
    correlation: float
    strength: str  # 'weak', 'moderate', 'strong'
    direction: str  # 'positive', 'negative', 'none'
    data_points: int
    confidence: str  # 'low', 'medium', 'high'
    insight: str
    dollar_impact: Optional[float] = None


def pearson_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """
    Compute Pearson correlation coefficient between two equal-length sequences.
    Returns None if insufficient data (< 2 points) or zero variance in either series.
    """
    n = len(x)
    if n != len(y) or n < 2:
        return None
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(xi * xi for xi in x)
    sum_yy = sum(yi * yi for yi in y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    num = n * sum_xy - sum_x * sum_y
    den_x = n * sum_xx - sum_x * sum_x
    den_y = n * sum_yy - sum_y * sum_y
    if den_x <= 0 or den_y <= 0:
        return None
    import math
    den = math.sqrt(den_x * den_y)
    if den == 0:
        return None
    return num / den


def correlation_strength(r: float) -> str:
    """Map |r| to strength: weak, moderate, strong."""
    if r is None:
        return 'weak'
    abs_r = abs(r)
    if abs_r >= 0.6:
        return 'strong'
    if abs_r >= 0.3:
        return 'moderate'
    return 'weak'


def correlation_direction(r: float) -> str:
    """Map r to direction: positive, negative, none."""
    if r is None:
        return 'none'
    if r > 0.1:
        return 'positive'
    if r < -0.1:
        return 'negative'
    return 'none'


def confidence_level(data_points: int, strength: str) -> str:
    """Assign confidence based on sample size and strength."""
    if data_points >= 8 and strength in ('moderate', 'strong'):
        return 'high'
    if data_points >= 4:
        return 'medium'
    return 'low'


class WellnessFinanceCorrelator:
    """
    Computes wellness–finance correlations from weekly check-in history.
    Requires at least 4 weeks of data for meaningful results.
    """

    PAIRS = [
        ('stress_level', 'impulse_spending', 'stress_vs_impulse_spending', 'Stress & impulse spending'),
        ('stress_level', 'total_spending', 'stress_vs_total_spending', 'Stress & total spending'),
        ('exercise_days', 'spending_control', 'exercise_vs_spending_control', 'Exercise & spending control'),
        ('sleep_quality', 'dining_estimate', 'sleep_vs_dining_spending', 'Sleep & dining'),
        ('overall_mood', 'entertainment_estimate', 'mood_vs_entertainment_spending', 'Mood & entertainment'),
        ('overall_mood', 'shopping_estimate', 'mood_vs_shopping_spending', 'Mood & shopping'),
        ('meditation_minutes', 'impulse_spending', 'meditation_vs_impulse_spending', 'Meditation & impulse'),
        ('relationship_satisfaction', 'discretionary_spending', 'relationship_vs_discretionary_spending', 'Relationships & discretionary'),
    ]

    def __init__(self, min_weeks: int = 4):
        self.min_weeks = min_weeks

    def _get_series(
        self, checkins: List[Dict[str, Any]], key: str, as_float: bool = True
    ) -> List[float]:
        out = []
        for c in checkins:
            v = c.get(key)
            if v is None:
                continue
            try:
                out.append(float(v))
            except (TypeError, ValueError):
                continue
        return out

    def _total_spending(self, checkin: Dict[str, Any]) -> float:
        keys = [
            'groceries_estimate', 'dining_estimate', 'entertainment_estimate',
            'shopping_estimate', 'transport_estimate', 'utilities_estimate', 'other_estimate',
        ]
        total = 0.0
        for k in keys:
            v = checkin.get(k)
            if v is not None:
                try:
                    total += float(v)
                except (TypeError, ValueError):
                    pass
        return total

    def _discretionary_series(self, checkins: List[Dict[str, Any]]) -> List[float]:
        return [self._total_spending(c) for c in checkins]

    def _y_value(self, checkin: Dict[str, Any], y_key: str) -> Optional[float]:
        if y_key == 'total_spending':
            return self._total_spending(checkin)
        if y_key == 'discretionary_spending':
            return self._total_spending(checkin)
        v = checkin.get(y_key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def compute_correlations(
        self, checkins: List[Dict[str, Any]]
    ) -> Dict[str, CorrelationResult]:
        """
        Compute all wellness–finance correlations. Returns dict keyed by correlation type.
        Returns empty dict if fewer than min_weeks check-ins.
        """
        if len(checkins) < self.min_weeks:
            return {}

        results = {}
        for x_key, y_key, result_key, label in self.PAIRS:
            x_series = []
            y_series = []
            for c in checkins:
                x_val = c.get(x_key)
                y_val = self._y_value(c, y_key)
                if x_val is None or y_val is None:
                    continue
                try:
                    x_series.append(float(x_val))
                    y_series.append(y_val)
                except (TypeError, ValueError):
                    continue
            if len(x_series) < self.min_weeks or len(x_series) != len(y_series):
                continue
            r = pearson_correlation(x_series, y_series)
            if r is None:
                continue
            strength = correlation_strength(r)
            direction = correlation_direction(r)
            conf = confidence_level(len(x_series), strength)
            insight = f"Based on {len(x_series)} weeks: {label} show a {strength} {direction} relationship."
            dollar_impact = sum(y_series) / len(y_series) if y_series else None
            results[result_key] = CorrelationResult(
                correlation=round(r, 4),
                strength=strength,
                direction=direction,
                data_points=len(x_series),
                confidence=conf,
                insight=insight,
                dollar_impact=dollar_impact,
            )
        return results


def _monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _weekly_debit_total(user_id: int, week_start: date, week_end: date) -> float:
    from backend.models.database import db
    from backend.models.transaction import Transaction

    try:
        total = (
            db.session.query(func.coalesce(func.sum(Transaction.amount), 0.0))
            .filter(
                Transaction.user_id == user_id,
                Transaction.is_debit.is_(True),
                Transaction.date >= week_start,
                Transaction.date <= week_end,
            )
            .scalar()
        )
        return float(total or 0.0)
    except Exception:
        return 0.0


def _weekly_debit_by_category(user_id: int, week_start: date, week_end: date) -> Dict[str, float]:
    from backend.models.database import db
    from backend.models.transaction import Transaction

    try:
        rows = (
            db.session.query(Transaction.category, func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.is_debit.is_(True),
                Transaction.date >= week_start,
                Transaction.date <= week_end,
                Transaction.category.isnot(None),
            )
            .group_by(Transaction.category)
            .all()
        )
        return {str(cat): float(total or 0.0) for cat, total in rows if cat}
    except Exception:
        return {}


def _complete_week_totals(user_id: int, this_week_start: date, weeks_back: int) -> List[float]:
    totals: List[float] = []
    for i in range(1, weeks_back + 1):
        ws = this_week_start - timedelta(weeks=i)
        we = ws + timedelta(days=6)
        totals.append(_weekly_debit_total(user_id, ws, we))
    return totals


def compute_spending_deltas(user_id: int) -> Dict[str, Any]:
    """
    Compare this week's measured debit spend to an 8-week complete-week baseline.
    Returns unavailable payload when no transactions exist or on error.
    """
    from backend.models.transaction import Transaction

    try:
        txn_count = Transaction.query.filter_by(user_id=user_id).count()
        if txn_count == 0:
            return dict(_SPENDING_DELTA_UNAVAILABLE)

        today = date.today()
        this_week_start = _monday_of_week(today)
        this_week_end = today
        total_this_week = _weekly_debit_total(user_id, this_week_start, this_week_end)

        complete_totals = _complete_week_totals(user_id, this_week_start, 8)
        weeks_with_data = sum(1 for t in complete_totals if t > 0)

        if weeks_with_data < 2:
            return {
                "available": True,
                "total_this_week": round(total_this_week, 2),
                "baseline_avg": None,
                "delta_amount": None,
                "delta_pct": None,
                "by_category": None,
            }

        baseline_avg = sum(complete_totals) / len(complete_totals)
        delta_amount = total_this_week - baseline_avg
        delta_pct = (delta_amount / baseline_avg * 100.0) if baseline_avg > 0 else None
        by_category = _weekly_debit_by_category(user_id, this_week_start, this_week_end)

        return {
            "available": True,
            "total_this_week": round(total_this_week, 2),
            "baseline_avg": round(baseline_avg, 2),
            "delta_amount": round(delta_amount, 2),
            "delta_pct": round(delta_pct, 2) if delta_pct is not None else None,
            "by_category": by_category or None,
        }
    except Exception:
        logger.exception("compute_spending_deltas failed user_id=%s", user_id)
        return dict(_SPENDING_DELTA_UNAVAILABLE)


def weekly_actual_spend(user_id: int, week_start: date) -> float:
    """Debit spend for one ISO week (Mon–Sun)."""
    return _weekly_debit_total(user_id, week_start, week_start + timedelta(days=6))


def weekly_baseline_before(user_id: int, week_start: date, weeks: int = 8) -> float | None:
    """Average weekly debit spend for `weeks` complete weeks before `week_start`."""
    totals = []
    for i in range(1, weeks + 1):
        ws = week_start - timedelta(weeks=i)
        we = ws + timedelta(days=6)
        totals.append(_weekly_debit_total(user_id, ws, we))
    if not totals:
        return None
    return sum(totals) / len(totals)


def has_transaction_weeks_history(user_id: int, min_weeks: int = 4) -> bool:
    from backend.models.transaction import Transaction

    try:
        earliest = (
            Transaction.query.filter_by(user_id=user_id)
            .order_by(Transaction.date.asc())
            .with_entities(Transaction.date)
            .first()
        )
        if earliest is None or earliest[0] is None:
            return False
        days_span = (date.today() - earliest[0]).days
        return days_span >= (min_weeks * 7)
    except Exception:
        return False
