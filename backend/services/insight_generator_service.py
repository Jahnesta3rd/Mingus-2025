#!/usr/bin/env python3
"""
Insight Generator Service for Mingus Application

Produces actionable wellness-finance insights from check-in data.
Uses WellnessScoreCalculator and correlation results (WellnessFinanceCorrelator when available).
All spending data comes from weekly check-in estimates (no external bank data).
Target audience: African American professionals ages 25-35.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional

# CorrelationResult: interface expected from WellnessFinanceCorrelator (or stub when not yet built)
try:
    from backend.services.correlation_engine_service import CorrelationResult
except ImportError:
    @dataclass
    class CorrelationResult:
        """Stub for correlation result when correlation engine not yet installed."""
        correlation: float
        strength: str  # 'weak', 'moderate', 'strong'
        direction: str  # 'positive', 'negative', 'none'
        data_points: int
        confidence: str  # 'low', 'medium', 'high'
        insight: str
        dollar_impact: Optional[float] = None


class InsightType(Enum):
    CORRELATION = "correlation"
    TREND = "trend"
    ANOMALY = "anomaly"
    ACHIEVEMENT = "achievement"
    RECOMMENDATION = "recommendation"
    SPENDING_PATTERN = "spending_pattern"


@dataclass
class WellnessInsight:
    type: InsightType
    title: str
    message: str
    data_backing: str
    action: str
    priority: int  # 1-5, 1 = highest
    category: str  # 'physical', 'mental', 'relational', 'financial', 'spending'
    dollar_amount: Optional[float] = None


# Spending estimate keys (from weekly_checkins)
SPENDING_KEYS = [
    'groceries_estimate', 'dining_estimate', 'entertainment_estimate',
    'shopping_estimate', 'transport_estimate', 'utilities_estimate', 'other_estimate',
]
TAGGED_SPENDING_KEYS = ['impulse_spending', 'stress_spending', 'celebration_spending']


def _safe_float(val: Any) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _total_spending(checkin: Dict[str, Any]) -> float:
    total = 0.0
    for k in SPENDING_KEYS + TAGGED_SPENDING_KEYS:
        total += _safe_float(checkin.get(k))
    return total


def compare_to_baseline(current_value: float, baseline: float) -> str:
    """
    Compare current spending to user's baseline (average).

    Returns:
        'much_lower'  if current < 50% of baseline
        'lower'       if 50% <= current < 80%
        'normal'      if 80% <= current <= 120%
        'higher'      if 120% < current <= 150%
        'much_higher' if current > 150% of baseline
    """
    if baseline is None or baseline <= 0:
        return 'normal'
    ratio = current_value / baseline
    if ratio < 0.5:
        return 'much_lower'
    if ratio < 0.8:
        return 'lower'
    if ratio <= 1.2:
        return 'normal'
    if ratio <= 1.5:
        return 'higher'
    return 'much_higher'


class InsightGenerator:
    """
    Generates personalized wellness-finance insights from check-in data and correlations.
    Tone: supportive, never judgmental; use "your data shows"; suggest, don't demand.
    """

    def __init__(self):
        pass

    def generate_weekly_insights(
        self,
        current_checkin: Dict[str, Any],
        previous_checkins: List[Dict[str, Any]],
        correlations: Dict[str, CorrelationResult],
        spending_baselines: Dict[str, float],
    ) -> List[WellnessInsight]:
        """
        Generate a prioritized list of insights (top 5).
        Combines correlation, trend, spending pattern, anomaly, achievement, and recommendation insights.
        """
        insights: List[WellnessInsight] = []
        insights.extend(self._correlation_insights(correlations))
        insights.extend(self._trend_insights(current_checkin, previous_checkins))
        insights.extend(
            self._spending_pattern_insights(
                current_checkin, previous_checkins, spending_baselines
            )
        )
        insights.extend(self._anomaly_insights(current_checkin))
        insights.extend(self._achievement_insights(current_checkin, previous_checkins))
        insights.extend(self._recommendation_insights(current_checkin, correlations))

        insights.sort(key=lambda x: (x.priority, x.title))
        return insights[:5]

    def _correlation_insights(
        self, correlations: Dict[str, CorrelationResult]
    ) -> List[WellnessInsight]:
        """Only include correlations with medium+ confidence and moderate+ strength."""
        insights = []
        name_to_category = {
            'stress_impulse': 'financial',
            'stress_vs_impulse_spending': 'financial',
            'exercise_spending_control': 'physical',
            'sleep_dining': 'physical',
            'mood_entertainment': 'mental',
            'mood_shopping': 'mental',
            'meditation_impulse': 'mental',
            'relationship_discretionary': 'relational',
        }
        name_to_title = {
            'stress_impulse': '🔗 Stress & Spending Link',
            'stress_vs_impulse_spending': '🔗 Stress & Spending Link',
            'exercise_spending_control': '🔗 Exercise & Control',
            'sleep_dining': '🔗 Sleep & Dining',
            'mood_entertainment': '🔗 Mood & Entertainment',
            'mood_shopping': '🔗 Mood & Shopping',
            'meditation_impulse': '🔗 Meditation & Impulse',
            'relationship_discretionary': '🔗 Relationships & Spending',
        }
        for name, result in correlations.items():
            if result.confidence not in ('medium', 'high'):
                continue
            if result.strength not in ('moderate', 'strong'):
                continue
            priority = 2 if result.strength == 'strong' else 3
            category = name_to_category.get(name, 'financial')
            title = name_to_title.get(name, '🔗 Pattern Found')
            dollar = getattr(result, 'dollar_impact', None) or getattr(
                result, 'dollar_amount', None
            )
            msg = result.insight
            if not msg:
                msg = f"Your data shows a {result.strength} link (based on {result.data_points} weeks)."
            action = (
                "Keep tracking to see how small changes in wellness affect your spending."
            )
            if result.direction == 'positive' and 'stress' in name.lower():
                action = "Consider a 24-hour pause on non-essentials when stress is high."
            insight = WellnessInsight(
                type=InsightType.CORRELATION,
                title=title,
                message=msg,
                data_backing=f"Based on {result.data_points} weeks of your data",
                action=action,
                priority=priority,
                category=category,
                dollar_amount=dollar,
            )
            insights.append(insight)
        return insights

    def _trend_insights(
        self,
        current_checkin: Dict[str, Any],
        previous_checkins: List[Dict[str, Any]],
    ) -> List[WellnessInsight]:
        """Detect 3+ week trends in exercise, stress, meditation, mood, impulse/total spending."""
        insights = []
        if len(previous_checkins) < 2:
            return insights

        # Build sequences: current first, then 2+ previous (newest first)
        def seq(key: str, as_float: bool = False):
            getter = _safe_float if as_float else (lambda x: x if x is not None else 0)
            out = [getter(current_checkin.get(key))]
            for c in previous_checkins[:3]:
                out.append(getter(c.get(key)))
            return out

        # Improving: exercise_days up over 3+ weeks (current >= prev1 >= prev2)
        exercise_seq = seq('exercise_days')
        if len(exercise_seq) >= 3 and all(exercise_seq[i] >= exercise_seq[i + 1] for i in range(len(exercise_seq) - 1)) and exercise_seq[0] > exercise_seq[-1]:
            insights.append(WellnessInsight(
                type=InsightType.TREND,
                title='📈 Exercise Momentum',
                message="Your data shows exercise days increasing over the last 3+ weeks. Keep it up!",
                data_backing=f"Trend: {exercise_seq[-1]} → {exercise_seq[0]} days",
                action="Consistency builds habit. Even small increases help.",
                priority=2,
                category='physical',
            ))

        stress_seq = seq('stress_level')
        if len(stress_seq) >= 3 and all(stress_seq[i] <= stress_seq[i + 1] for i in range(len(stress_seq) - 1)) and stress_seq[0] < stress_seq[-1]:
            insights.append(WellnessInsight(
                type=InsightType.TREND,
                title='📉 Stress Trending Down',
                message="Your stress level has decreased over 3+ weeks. Nice progress!",
                data_backing=f"Trend: {stress_seq[-1]} → {stress_seq[0]}/10",
                action="Whatever you're doing is working. Keep it up.",
                priority=2,
                category='mental',
            ))

        impulse_seq = seq('impulse_spending', as_float=True)
        if len(impulse_seq) >= 3 and all(impulse_seq[i] >= impulse_seq[i + 1] for i in range(len(impulse_seq) - 1)) and impulse_seq[0] > impulse_seq[-1]:
            insights.append(WellnessInsight(
                type=InsightType.TREND,
                title='📈 Impulse Trend',
                message=f"Your impulse spending has increased for 3 weeks: ${impulse_seq[-1]:.0f} → ${impulse_seq[0]:.0f}.",
                data_backing="Week-over-week impulse spending",
                action="Notice what’s driving the increase. A small pause before buying can help.",
                priority=3,
                category='spending',
                dollar_amount=impulse_seq[0],
            ))

        # Positive: stress spending $0 for 3+ weeks
        stress_spend_seq = seq('stress_spending', as_float=True)
        if len(stress_spend_seq) >= 3 and all(s == 0 for s in stress_spend_seq):
            insights.append(WellnessInsight(
                type=InsightType.TREND,
                title='📉 Great Progress',
                message="Your stress spending has been $0 for 3+ weeks straight!",
                data_backing="No stress-driven purchases in recent weeks",
                action="Celebrate this win. You’re building a healthier pattern.",
                priority=2,
                category='spending',
            ))

        return insights

    def _spending_pattern_insights(
        self,
        current_checkin: Dict[str, Any],
        previous_checkins: List[Dict[str, Any]],
        baselines: Dict[str, float],
    ) -> List[WellnessInsight]:
        """Compare current week spending to user's averages; flag above/below normal and impulse/stress."""
        insights = []
        total_current = _total_spending(current_checkin)
        avg_total = baselines.get('avg_total_variable') or baselines.get('avg_total')
        if avg_total and avg_total > 0:
            comparison = compare_to_baseline(total_current, avg_total)
            if comparison == 'much_higher' or comparison == 'higher':
                pct = (total_current / avg_total - 1) * 100
                insights.append(WellnessInsight(
                    type=InsightType.SPENDING_PATTERN,
                    title='📊 Spending This Week',
                    message=f"Your total spending this week (${total_current:.0f}) is {pct:.0f}% above your usual ${avg_total:.0f} average. Your data shows this; no judgment.",
                    data_backing=f"Current: ${total_current:.0f} vs average ${avg_total:.0f}",
                    action="Review what drove the increase. Awareness is the first step.",
                    priority=3,
                    category='spending',
                    dollar_amount=total_current,
                ))
            elif comparison == 'much_lower' or comparison == 'lower':
                pct = (1 - total_current / avg_total) * 100
                insights.append(WellnessInsight(
                    type=InsightType.SPENDING_PATTERN,
                    title='💚 Spending Win',
                    message=f"Your total spending this week is {pct:.0f}% below your average. Nice control!",
                    data_backing=f"Current: ${total_current:.0f} vs average ${avg_total:.0f}",
                    action="Keep doing what’s working.",
                    priority=2,
                    category='spending',
                    dollar_amount=total_current,
                ))

        shopping_current = _safe_float(current_checkin.get('shopping_estimate'))
        avg_shopping = baselines.get('avg_shopping')
        if avg_shopping and avg_shopping > 0 and shopping_current > 0:
            ratio = shopping_current / avg_shopping
            if ratio >= 1.5:
                insights.append(WellnessInsight(
                    type=InsightType.SPENDING_PATTERN,
                    title='📊 Shopping Spike',
                    message=f"Your shopping this week (${shopping_current:.0f}) is {ratio:.1f}x your usual ${avg_shopping:.0f} average.",
                    data_backing=f"Current: ${shopping_current:.0f} vs average ${avg_shopping:.0f}",
                    action="Notice what triggered the extra shopping. No judgment—just awareness.",
                    priority=3,
                    category='spending',
                    dollar_amount=shopping_current,
                ))

        impulse_current = _safe_float(current_checkin.get('impulse_spending'))
        avg_impulse = baselines.get('avg_impulse')
        if avg_impulse and avg_impulse > 0 and impulse_current > avg_impulse * 1.5:
            insights.append(WellnessInsight(
                type=InsightType.SPENDING_PATTERN,
                title='📊 Impulse Above Usual',
                message=f"Your impulse spending this week (${impulse_current:.0f}) is above your usual ${avg_impulse:.0f} average.",
                data_backing=f"Current: ${impulse_current:.0f} vs average ${avg_impulse:.0f}",
                action="Consider a 24-hour pause before non-essential purchases.",
                priority=3,
                category='spending',
                dollar_amount=impulse_current,
            ))

        return insights

    def _anomaly_insights(self, current_checkin: Dict[str, Any]) -> List[WellnessInsight]:
        """Flag unusual patterns in the current check-in (real-time alerts)."""
        insights = []
        stress = _safe_float(current_checkin.get('stress_level'))
        impulse = _safe_float(current_checkin.get('impulse_spending'))
        mood = _safe_float(current_checkin.get('overall_mood'))
        shopping = _safe_float(current_checkin.get('shopping_estimate'))
        entertainment = _safe_float(current_checkin.get('entertainment_estimate'))
        sleep = _safe_float(current_checkin.get('sleep_quality'))
        dining = _safe_float(current_checkin.get('dining_estimate'))

        if stress >= 7 and impulse > 0:
            insights.append(WellnessInsight(
                type=InsightType.ANOMALY,
                title='⚡ Stress Spending Alert',
                message=f"You reported high stress ({int(stress)}/10) and ${impulse:.0f} in impulse purchases. These often go together. Your data shows the link.",
                data_backing=f"Stress: {int(stress)}/10, Impulse: ${impulse:.0f}",
                action="Consider waiting 24 hours on non-essentials. You’ve got this.",
                priority=1,
                category='financial',
                dollar_amount=impulse,
            ))

        if mood <= 4 and (shopping > 50 or entertainment > 50):
            total = shopping + entertainment
            insights.append(WellnessInsight(
                type=InsightType.ANOMALY,
                title='⚡ Mood & Spending',
                message=f"Low mood this week ({int(mood)}/10) with ${total:.0f} in shopping/entertainment. Sometimes we spend to feel better.",
                data_backing=f"Mood: {int(mood)}/10, Discretionary: ${total:.0f}",
                action="Check in with yourself before the next purchase. A short walk or call can help too.",
                priority=1,
                category='mental',
                dollar_amount=total,
            ))

        if sleep is not None and sleep <= 4 and dining > 50:
            insights.append(WellnessInsight(
                type=InsightType.ANOMALY,
                title='⚡ Sleep & Dining',
                message=f"Sleep quality was low ({int(sleep)}/10) and dining out is ${dining:.0f}. Poor sleep often leads to more convenience spending.",
                data_backing=f"Sleep: {int(sleep)}/10, Dining: ${dining:.0f}",
                action="Prioritizing rest might naturally lower dining spend. Small step: one extra home meal.",
                priority=2,
                category='physical',
                dollar_amount=dining,
            ))

        return insights

    def _achievement_insights(
        self,
        current_checkin: Dict[str, Any],
        previous_checkins: List[Dict[str, Any]],
    ) -> List[WellnessInsight]:
        """Celebrate milestones: $0 impulse, no stress spending streak, lowest spending, 5+ exercise days."""
        insights = []
        impulse = _safe_float(current_checkin.get('impulse_spending'))
        stress_spend = _safe_float(current_checkin.get('stress_spending'))
        exercise_days = current_checkin.get('exercise_days')
        if exercise_days is not None:
            exercise_days = int(exercise_days)

        if impulse == 0 and previous_checkins:
            had_impulse_before = any(
                _safe_float(c.get('impulse_spending')) > 0 for c in previous_checkins
            )
            if had_impulse_before:
                insights.append(WellnessInsight(
                    type=InsightType.ACHIEVEMENT,
                    title='🏆 Zero Impulse Week',
                    message="This is your first week reporting $0 in impulse spending. Your data shows real progress!",
                    data_backing="Impulse spending: $0 this week",
                    action="Celebrate this win. Keep the same awareness next week.",
                    priority=2,
                    category='spending',
                ))

        if len(previous_checkins) >= 2:
            stress_seq = [_safe_float(current_checkin.get('stress_spending'))] + [
                _safe_float(c.get('stress_spending')) for c in previous_checkins[:3]
            ]
            if all(s == 0 for s in stress_seq):
                insights.append(WellnessInsight(
                    type=InsightType.ACHIEVEMENT,
                    title='🏆 No Stress Spending Streak',
                    message="You’ve had no stress-driven spending for 3+ weeks. That’s a big deal!",
                    data_backing="Stress spending: $0 for 3+ weeks",
                    action="Keep using whatever coping works—you’re building a lasting pattern.",
                    priority=2,
                    category='spending',
                ))

        if exercise_days is not None and exercise_days >= 5:
            prev_max = max(
                (int(c.get('exercise_days') or 0) for c in previous_checkins),
                default=0,
            )
            if prev_max < 5:
                insights.append(WellnessInsight(
                    type=InsightType.ACHIEVEMENT,
                    title='🏆 Fitness Five',
                    message=f"You hit {exercise_days} exercise days this week—your best yet!",
                    data_backing=f"Exercise days: {exercise_days} (previous best: {prev_max})",
                    action="Consistency beats perfection. Keep it up!",
                    priority=2,
                    category='physical',
                ))

        total_current = _total_spending(current_checkin)
        if previous_checkins and total_current > 0:
            prev_totals = [_total_spending(c) for c in previous_checkins if _total_spending(c) > 0]
            if prev_totals and total_current <= min(prev_totals):
                insights.append(WellnessInsight(
                    type=InsightType.ACHIEVEMENT,
                    title='🏆 Lowest Spending Week',
                    message="Your total spending this week is the lowest in your recent history. Nice control!",
                    data_backing=f"This week: ${total_current:.0f} vs previous weeks",
                    action="Notice what helped—routine, planning, or mood. Double down next week.",
                    priority=2,
                    category='spending',
                    dollar_amount=total_current,
                ))

        return insights

    def _recommendation_insights(
        self,
        current_checkin: Dict[str, Any],
        correlations: Dict[str, CorrelationResult],
    ) -> List[WellnessInsight]:
        """Actionable recommendations from current state + patterns."""
        insights = []
        stress = _safe_float(current_checkin.get('stress_level'))

        stress_corr = correlations.get('stress_impulse') or correlations.get(
            'stress_vs_impulse_spending'
        )
        if stress_corr and stress_corr.strength in ('moderate', 'strong') and stress_corr.confidence in ('medium', 'high'):
            if stress >= 6:
                insights.append(WellnessInsight(
                    type=InsightType.RECOMMENDATION,
                    title='🛡️ Spending Shield',
                    message="Your pattern shows stress leads to more impulse buys. Stress is high this week—consider a 24-hour pause on non-essentials.",
                    data_backing=f"Stress: {int(stress)}/10. Your data: {(getattr(stress_corr, 'insight', None) or '')[:80]}",
                    action="Wait 24 hours before any non-essential purchase. You’ve got this.",
                    priority=1,
                    category='financial',
                ))

        return insights
