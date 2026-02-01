#!/usr/bin/env python3
"""
Spending Baseline Service for Mingus Application

Calculates and updates user spending baselines from weekly check-in estimates.
Used to detect anomalies and power insights like "Your shopping this week is 2x your average."
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc

from backend.models.database import db
from backend.models.wellness import WeeklyCheckin, UserSpendingBaseline


# Minimum weeks required for meaningful baselines
MIN_WEEKS_FOR_BASELINE = 3
# Rolling window: use last N weeks to avoid old data skewing (8–12 weeks)
BASELINE_ROLLING_WEEKS = 12

# Category keys in check-in dict (as from API / DB)
CATEGORY_KEYS = [
    'groceries_estimate',
    'dining_estimate',
    'entertainment_estimate',
    'shopping_estimate',
    'transport_estimate',
    'utilities_estimate',
    'other_estimate',
]
VARIABLE_KEYS = CATEGORY_KEYS.copy()
IMPULSE_KEY = 'impulse_spending'
STRESS_KEY = 'stress_spending'

# Baseline dict keys (avg_*)
BASELINE_AVG_KEYS = [
    'avg_groceries',
    'avg_dining',
    'avg_entertainment',
    'avg_shopping',
    'avg_transport',
    'avg_utilities',
    'avg_other',
    'avg_total_variable',
    'avg_impulse',
    'avg_stress',
]

# Map check-in key -> baseline key for compare_to_baseline
CHECKIN_TO_BASELINE = {
    'groceries_estimate': 'avg_groceries',
    'dining_estimate': 'avg_dining',
    'entertainment_estimate': 'avg_entertainment',
    'shopping_estimate': 'avg_shopping',
    'transport_estimate': 'avg_transport',
    'utilities_estimate': 'avg_utilities',
    'other_estimate': 'avg_other',
    'impulse_spending': 'avg_impulse',
    'stress_spending': 'avg_stress',
}


def _safe_float(value: Any) -> Optional[float]:
    """Convert value to float; return None if invalid or None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_average(values: List[float]) -> Optional[float]:
    """
    Calculate average, excluding None values.
    Return None if no valid values.
    """
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return sum(valid) / len(valid)


def _calculate_percent_change(current: float, baseline: float) -> float:
    """
    Return percentage change: ((current - baseline) / baseline) * 100.
    Handle zero baseline: return 0.0 if baseline == 0.
    """
    if baseline == 0:
        return 0.0
    return ((current - baseline) / baseline) * 100.0


def _get_status(percent_change: float) -> str:
    """
    Categorize the change into status buckets.
    percent_change = ((current - baseline) / baseline) * 100.
    much_lower (<-50%), lower (-50 to -20%), normal (-20 to 20%), higher (20-50%), much_higher (>50%)
    """
    if percent_change < -50:
        return 'much_lower'
    if percent_change < -20:
        return 'lower'
    if percent_change < 20:
        return 'normal'
    if percent_change <= 50:
        return 'higher'
    return 'much_higher'


class SpendingBaselineService:
    """
    Calculate and update user spending baselines from weekly check-ins.
    Uses rolling window (last N weeks) and enforces minimum data requirement.
    """

    def __init__(
        self,
        rolling_weeks: int = BASELINE_ROLLING_WEEKS,
        min_weeks: int = MIN_WEEKS_FOR_BASELINE,
    ):
        self.rolling_weeks = rolling_weeks
        self.min_weeks = min_weeks

    def _checkin_to_spending_dict(self, checkin: Any) -> Dict[str, Optional[float]]:
        """Convert a check-in (model or dict) to a flat spending dict."""
        out: Dict[str, Optional[float]] = {}
        for key in CATEGORY_KEYS + [IMPULSE_KEY, STRESS_KEY]:
            if hasattr(checkin, key):
                v = getattr(checkin, key, None)
            else:
                v = checkin.get(key) if isinstance(checkin, dict) else None
            out[key] = _safe_float(v)
        return out

    def calculate_baselines(self, user_id: str, checkins: List[dict]) -> dict:
        """
        Calculate average spending for each category across all check-ins.
        Only include check-ins where the category was reported (not null).
        Uses per-category counts for averages (not global n).
        """
        n = len(checkins)
        # Collect values per key (only where reported)
        values: Dict[str, List[float]] = {k: [] for k in CATEGORY_KEYS + [IMPULSE_KEY, STRESS_KEY]}
        for c in checkins:
            row = self._checkin_to_spending_dict(c)
            for key, v in row.items():
                if v is not None and v >= 0:
                    values[key].append(v)

        avg_groceries = _safe_average(values['groceries_estimate'])
        avg_dining = _safe_average(values['dining_estimate'])
        avg_entertainment = _safe_average(values['entertainment_estimate'])
        avg_shopping = _safe_average(values['shopping_estimate'])
        avg_transport = _safe_average(values['transport_estimate'])
        avg_utilities = _safe_average(values['utilities_estimate'])
        avg_other = _safe_average(values['other_estimate'])

        # Total variable: sum of category averages when we have them; or average of per-checkin totals
        per_checkin_totals: List[float] = []
        for c in checkins:
            row = self._checkin_to_spending_dict(c)
            total = sum(_safe_float(row[k]) or 0 for k in CATEGORY_KEYS)
            if any(row.get(k) is not None for k in CATEGORY_KEYS):
                per_checkin_totals.append(total)
        avg_total_variable = _safe_average(per_checkin_totals) if per_checkin_totals else None

        avg_impulse = _safe_average(values['impulse_spending'])
        avg_stress = _safe_average(values['stress_spending'])

        return {
            'avg_groceries': avg_groceries,
            'avg_dining': avg_dining,
            'avg_entertainment': avg_entertainment,
            'avg_shopping': avg_shopping,
            'avg_transport': avg_transport,
            'avg_utilities': avg_utilities,
            'avg_other': avg_other,
            'avg_total_variable': avg_total_variable,
            'avg_impulse': avg_impulse,
            'avg_stress': avg_stress,
            'weeks_of_data': n,
        }

    def update_baselines(self, user_id: str) -> dict:
        """
        Fetch check-ins for user (rolling window), recalculate baselines,
        save to user_spending_baselines table. Return updated baselines dict.
        """
        uid = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        checkins_query = (
            WeeklyCheckin.query.filter_by(user_id=uid)
            .order_by(desc(WeeklyCheckin.week_ending_date))
            .limit(self.rolling_weeks)
            .all()
        )
        checkins = [self._checkin_to_spending_dict(c) for c in checkins_query]
        if len(checkins) < self.min_weeks:
            # Insufficient data: return special status (don't overwrite existing baseline with partial data)
            existing = UserSpendingBaseline.query.filter_by(user_id=uid).first()
            if existing:
                return self.get_baselines(user_id) or {}
            return {
                'avg_groceries': None,
                'avg_dining': None,
                'avg_entertainment': None,
                'avg_shopping': None,
                'avg_transport': None,
                'avg_utilities': None,
                'avg_other': None,
                'avg_total_variable': None,
                'avg_impulse': None,
                'avg_stress': None,
                'weeks_of_data': len(checkins),
                'insufficient_data': True,
            }

        baselines = self.calculate_baselines(user_id, checkins)
        baselines['insufficient_data'] = False

        row = UserSpendingBaseline.query.filter_by(user_id=uid).first()
        if row is None:
            row = UserSpendingBaseline(user_id=uid)
            db.session.add(row)

        # Persist only columns that exist on the model
        row.avg_groceries = baselines.get('avg_groceries')
        row.avg_dining = baselines.get('avg_dining')
        row.avg_entertainment = baselines.get('avg_entertainment')
        row.avg_shopping = baselines.get('avg_shopping')
        row.avg_transport = baselines.get('avg_transport')
        row.avg_total_variable = baselines.get('avg_total_variable')
        row.avg_impulse = baselines.get('avg_impulse')
        row.weeks_of_data = baselines.get('weeks_of_data')
        row.last_calculated = datetime.now(timezone.utc)
        # Model may not have avg_utilities, avg_other, avg_stress; skip if not present
        if hasattr(row, 'avg_utilities'):
            row.avg_utilities = baselines.get('avg_utilities')
        if hasattr(row, 'avg_other'):
            row.avg_other = baselines.get('avg_other')
        if hasattr(row, 'avg_stress'):
            row.avg_stress = baselines.get('avg_stress')

        db.session.commit()
        return baselines

    def get_baselines(self, user_id: str) -> Optional[dict]:
        """
        Get current baselines from database.
        Return None if no baselines exist yet.
        """
        uid = int(user_id) if isinstance(user_id, str) and user_id.isdigit() else user_id
        row = UserSpendingBaseline.query.filter_by(user_id=uid).first()
        if row is None:
            return None
        out = {
            'avg_groceries': float(row.avg_groceries) if row.avg_groceries is not None else None,
            'avg_dining': float(row.avg_dining) if row.avg_dining is not None else None,
            'avg_entertainment': float(row.avg_entertainment) if row.avg_entertainment is not None else None,
            'avg_shopping': float(row.avg_shopping) if row.avg_shopping is not None else None,
            'avg_transport': float(row.avg_transport) if row.avg_transport is not None else None,
            'avg_utilities': float(row.avg_utilities) if getattr(row, 'avg_utilities', None) is not None else None,
            'avg_other': float(row.avg_other) if getattr(row, 'avg_other', None) is not None else None,
            'avg_total_variable': float(row.avg_total_variable) if row.avg_total_variable is not None else None,
            'avg_impulse': float(row.avg_impulse) if row.avg_impulse is not None else None,
            'avg_stress': float(row.avg_stress) if getattr(row, 'avg_stress', None) is not None else None,
            'weeks_of_data': row.weeks_of_data,
        }
        return out

    def compare_to_baseline(self, user_id: str, current_checkin: dict) -> dict:
        """
        Compare current week's spending to baselines.
        Returns per-category and total/impulse/stress with current, baseline, difference, percent_change, status.
        Returns special status for insufficient data if baselines don't exist or weeks_of_data < min_weeks.
        """
        baselines = self.get_baselines(user_id)
        if baselines is None or baselines.get('weeks_of_data', 0) < self.min_weeks:
            return {'insufficient_data': True, 'message': 'Not enough baseline data (need at least %d weeks).' % self.min_weeks}

        result: Dict[str, Any] = {'insufficient_data': False}
        spending = self._checkin_to_spending_dict(current_checkin)

        # Categories
        for checkin_key, baseline_key in CHECKIN_TO_BASELINE.items():
            if baseline_key == 'avg_total_variable':
                continue
            current_val = spending.get(checkin_key)
            baseline_val = baselines.get(baseline_key)
            if current_val is None and baseline_val is None:
                continue
            current_val = current_val if current_val is not None else 0.0
            baseline_val = baseline_val if baseline_val is not None else 0.0
            diff = current_val - baseline_val
            pct = _calculate_percent_change(current_val, baseline_val)
            status = _get_status(pct)
            # Result key: groceries_estimate -> groceries, impulse_spending -> impulse
            key_name = checkin_key.replace('_estimate', '').replace('_spending', '') or 'other'
            result[key_name] = {
                'current': round(current_val, 2),
                'baseline': round(baseline_val, 2),
                'difference': round(diff, 2),
                'percent_change': round(pct, 1),
                'status': status,
            }

        # Total variable
        current_total = sum(_safe_float(spending.get(k)) or 0 for k in CATEGORY_KEYS)
        baseline_total = baselines.get('avg_total_variable') or 0.0
        diff_total = current_total - baseline_total
        pct_total = _calculate_percent_change(current_total, baseline_total)
        status_total = _get_status(pct_total)
        result['total'] = {
            'current': round(current_total, 2),
            'baseline': round(baseline_total, 2),
            'difference': round(diff_total, 2),
            'percent_change': round(pct_total, 1),
            'status': status_total,
        }

        return result
