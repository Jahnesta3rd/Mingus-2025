#!/usr/bin/env python3
"""
Wellness Check-in API for Mingus Application

REST API for the Weekly Check-in System with integrated wellness and spending estimates.
Uses JWT auth; all spending data from user-provided check-in estimates (no bank data).

OpenAPI tag: wellness
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from collections import defaultdict

from flask import Blueprint, request, jsonify, g
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import func, desc
from werkzeug.exceptions import BadRequest, NotFound, Conflict

from backend.auth.decorators import require_auth, get_current_user_id
from backend.models.database import db
from backend.models.user_models import User
from backend.models.wellness import (
    WeeklyCheckin,
    WellnessScore,
    WellnessFinanceCorrelation,
    WellnessCheckinStreak,
    UserSpendingBaseline,
)
from backend.services.wellness_score_service import WellnessScoreCalculator
from backend.services.wellness_gamification_service import (
    StreakService,
    AchievementService,
)
from backend.services.spending_baseline_service import SpendingBaselineService
from backend.services.insight_generator_service import (
    InsightGenerator,
    WellnessInsight,
    InsightType,
)

logger = logging.getLogger(__name__)

wellness_checkin_bp = Blueprint(
    'wellness_checkin',
    __name__,
    url_prefix='/api/wellness',
)

# Rate limit: max POST checkin per user per hour (in-memory for single process)
_checkin_post_counts: Dict[int, List[datetime]] = defaultdict(list)
RATE_LIMIT_POST_PER_HOUR = 5


def _rate_limit_checkin():
    """Enforce rate limit on POST /checkin. Call after require_auth."""
    user_id = get_current_user_id()
    if user_id is None:
        return
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=1)
    _checkin_post_counts[user_id] = [t for t in _checkin_post_counts[user_id] if t > cutoff]
    if len(_checkin_post_counts[user_id]) >= RATE_LIMIT_POST_PER_HOUR:
        raise BadRequest(
            f'Rate limit exceeded: max {RATE_LIMIT_POST_PER_HOUR} check-ins per hour. Try again later.'
        )
    _checkin_post_counts[user_id].append(now)


def _resolve_user_id() -> int:
    """Return current user's integer id (users.id)."""
    uid = get_current_user_id()
    if uid is None:
        raise BadRequest('Authentication required')
    if isinstance(uid, int):
        return uid
    user = User.query.filter_by(user_id=str(uid)).first()
    if user is None:
        user = User.query.get(uid)
    if user is None:
        raise BadRequest('User not found')
    return user.id


def _week_ending_today() -> date:
    return WellnessScoreCalculator.get_week_ending_date(date.today())


def _get_user_id_str() -> str:
    """Return current user's string user_id (users.user_id) for gamification services."""
    uid = get_current_user_id()
    if uid is not None and not isinstance(uid, int):
        return str(uid)
    rid = _resolve_user_id()
    user = User.query.get(rid)
    return getattr(user, 'user_id', str(rid)) if user else str(rid)


def _checkin_to_dict(c: WeeklyCheckin, include_scores: bool = False) -> Dict[str, Any]:
    """Serialize WeeklyCheckin to JSON-friendly dict."""
    def dec(v):
        return float(v) if v is not None else None

    d = {
        'id': str(c.id),
        'user_id': c.user_id,
        'week_ending_date': c.week_ending_date.isoformat() if c.week_ending_date else None,
        'exercise_days': c.exercise_days,
        'exercise_intensity': c.exercise_intensity,
        'sleep_quality': c.sleep_quality,
        'meditation_minutes': c.meditation_minutes,
        'stress_level': c.stress_level,
        'overall_mood': c.overall_mood,
        'relationship_satisfaction': c.relationship_satisfaction,
        'social_interactions': c.social_interactions,
        'financial_stress': c.financial_stress,
        'spending_control': c.spending_control,
        'groceries_estimate': dec(c.groceries_estimate),
        'dining_estimate': dec(c.dining_estimate),
        'entertainment_estimate': dec(c.entertainment_estimate),
        'shopping_estimate': dec(c.shopping_estimate),
        'transport_estimate': dec(c.transport_estimate),
        'utilities_estimate': dec(c.utilities_estimate),
        'other_estimate': dec(c.other_estimate),
        'impulse_spending': dec(c.impulse_spending),
        'stress_spending': dec(c.stress_spending),
        'celebration_spending': dec(c.celebration_spending),
        'had_impulse_purchases': c.had_impulse_purchases,
        'had_stress_purchases': c.had_stress_purchases,
        'biggest_unnecessary_purchase': dec(c.biggest_unnecessary_purchase),
        'biggest_unnecessary_category': c.biggest_unnecessary_category,
        'wins': c.wins,
        'challenges': c.challenges,
        'completed_at': c.completed_at.isoformat() if c.completed_at else None,
        'completion_time_seconds': c.completion_time_seconds,
        'reminder_count': c.reminder_count,
    }
    if include_scores:
        score = WellnessScore.query.filter_by(
            user_id=c.user_id, week_ending_date=c.week_ending_date
        ).first()
        if score:
            d['wellness_scores'] = {
                'physical_score': dec(score.physical_score),
                'mental_score': dec(score.mental_score),
                'relational_score': dec(score.relational_score),
                'financial_feeling_score': dec(score.financial_feeling_score),
                'overall_wellness_score': dec(score.overall_wellness_score),
                'physical_change': dec(score.physical_change),
                'mental_change': dec(score.mental_change),
                'relational_change': dec(score.relational_change),
                'overall_change': dec(score.overall_change),
            }
        else:
            d['wellness_scores'] = None
    return d


def _score_to_dict(s: WellnessScore) -> Dict[str, Any]:
    def dec(v):
        return float(v) if v is not None else None
    return {
        'week_ending_date': s.week_ending_date.isoformat() if s.week_ending_date else None,
        'physical_score': dec(s.physical_score),
        'mental_score': dec(s.mental_score),
        'relational_score': dec(s.relational_score),
        'financial_feeling_score': dec(s.financial_feeling_score),
        'overall_wellness_score': dec(s.overall_wellness_score),
        'physical_change': dec(s.physical_change),
        'mental_change': dec(s.mental_change),
        'relational_change': dec(s.relational_change),
        'overall_change': dec(s.overall_change),
        'calculated_at': s.calculated_at.isoformat() if s.calculated_at else None,
    }


def _insight_to_dict(i: WellnessInsight) -> Dict[str, Any]:
    return {
        'type': i.type.value if hasattr(i.type, 'value') else str(i.type),
        'title': i.title,
        'message': i.message,
        'data_backing': i.data_backing,
        'action': i.action,
        'priority': i.priority,
        'category': i.category,
        'dollar_amount': i.dollar_amount,
    }


def _update_streak(user_id: int, week_ending_date: date) -> Dict[str, Any]:
    """Update wellness check-in streak after a new check-in. Returns streak_info."""
    row = WellnessCheckinStreak.query.filter_by(user_id=user_id).first()
    if row is None:
        row = WellnessCheckinStreak(
            user_id=user_id,
            current_streak=1,
            longest_streak=1,
            last_checkin_date=week_ending_date,
            total_checkins=1,
        )
        db.session.add(row)
    else:
        row.total_checkins = (row.total_checkins or 0) + 1
        last = row.last_checkin_date
        if last is None:
            row.current_streak = 1
        else:
            # Consecutive weeks: last week's Sunday + 7 == this week's Sunday?
            prev_sunday = last - timedelta(days=7)
            if week_ending_date == prev_sunday:
                row.current_streak = (row.current_streak or 0) + 1
            else:
                row.current_streak = 1
        row.longest_streak = max(row.longest_streak or 0, row.current_streak)
        row.last_checkin_date = week_ending_date
    db.session.flush()
    return {
        'current_streak': row.current_streak,
        'longest_streak': row.longest_streak,
        'last_checkin_date': row.last_checkin_date.isoformat() if row.last_checkin_date else None,
        'total_checkins': row.total_checkins,
    }


def _update_baselines(user_id: int) -> None:
    """Recalculate spending baselines from check-in history (rolling window, min 3 weeks)."""
    SpendingBaselineService().update_baselines(str(user_id))


def _get_correlations_for_insights(user_id: int) -> Dict[str, Any]:
    """Return correlation results keyed by type for InsightGenerator."""
    try:
        from backend.services.correlation_engine_service import WellnessFinanceCorrelator
    except ImportError:
        return {}
    # Stub: correlation engine may compute from check-ins; for now return {}
    return {}


def _refresh_correlations_and_baselines(user_id: int) -> Dict[str, Any]:
    """Recalculate correlations and baselines. Returns correlations payload for API."""
    _update_baselines(user_id)
    # Correlation engine integration when available
    return {}


# =============================================================================
# MARSHMALLOW SCHEMAS
# =============================================================================

class CheckinRequestSchema(Schema):
    """Request body for POST /api/wellness/checkin."""

    exercise_days = fields.Integer(required=True, validate=validate.Range(min=0, max=7))
    exercise_intensity = fields.String(allow_none=True, validate=validate.OneOf(['light', 'moderate', 'intense']))
    sleep_quality = fields.Integer(required=True, validate=validate.Range(min=1, max=10))
    meditation_minutes = fields.Integer(required=True, validate=validate.Range(min=0, max=999))
    stress_level = fields.Integer(required=True, validate=validate.Range(min=1, max=10))
    overall_mood = fields.Integer(required=True, validate=validate.Range(min=1, max=10))
    relationship_satisfaction = fields.Integer(required=True, validate=validate.Range(min=1, max=10))
    social_interactions = fields.Integer(required=True, validate=validate.Range(min=0))
    financial_stress = fields.Integer(required=True, validate=validate.Range(min=1, max=10))
    spending_control = fields.Integer(required=True, validate=validate.Range(min=1, max=10))

    groceries_estimate = fields.Decimal(allow_none=True, as_string=True)
    dining_estimate = fields.Decimal(allow_none=True, as_string=True)
    entertainment_estimate = fields.Decimal(allow_none=True, as_string=True)
    shopping_estimate = fields.Decimal(allow_none=True, as_string=True)
    transport_estimate = fields.Decimal(allow_none=True, as_string=True)
    utilities_estimate = fields.Decimal(allow_none=True, as_string=True)
    other_estimate = fields.Decimal(allow_none=True, as_string=True)

    had_impulse_purchases = fields.Boolean(load_default=False)
    impulse_spending = fields.Decimal(allow_none=True, as_string=True)
    had_stress_purchases = fields.Boolean(load_default=False)
    stress_spending = fields.Decimal(allow_none=True, as_string=True)
    celebration_spending = fields.Decimal(allow_none=True, as_string=True)
    biggest_unnecessary_purchase = fields.Decimal(allow_none=True, as_string=True)
    biggest_unnecessary_category = fields.String(allow_none=True, validate=validate.Length(max=50))

    wins = fields.String(allow_none=True)
    challenges = fields.String(allow_none=True)

    completion_time_seconds = fields.Integer(allow_none=True)


# =============================================================================
# ENDPOINTS
# =============================================================================

@wellness_checkin_bp.route('/checkin', methods=['POST'])
@require_auth
def submit_checkin():
    """
    POST /api/wellness/checkin
    Submit a weekly check-in with wellness and spending data.
    OpenAPI: summary: Submit weekly check-in; tags: [wellness]; requestBody required.
    """
    _rate_limit_checkin()
    user_id = _resolve_user_id()
    if not request.is_json:
        raise BadRequest('Request must be JSON')
    try:
        data = CheckinRequestSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'messages': e.messages}), 400

    week_ending = _week_ending_today()
    existing = WeeklyCheckin.query.filter_by(
        user_id=user_id, week_ending_date=week_ending
    ).first()
    if existing:
        return jsonify({
            'error': 'Conflict',
            'message': 'You have already submitted a check-in for this week.',
            'week_ending_date': week_ending.isoformat(),
        }), 409

    def to_dec(v):
        if v is None:
            return None
        return Decimal(str(v)) if v is not None else None

    checkin = WeeklyCheckin(
        user_id=user_id,
        week_ending_date=week_ending,
        exercise_days=data['exercise_days'],
        exercise_intensity=data.get('exercise_intensity'),
        sleep_quality=data['sleep_quality'],
        meditation_minutes=data['meditation_minutes'],
        stress_level=data['stress_level'],
        overall_mood=data['overall_mood'],
        relationship_satisfaction=data['relationship_satisfaction'],
        social_interactions=data['social_interactions'],
        financial_stress=data['financial_stress'],
        spending_control=data['spending_control'],
        groceries_estimate=to_dec(data.get('groceries_estimate')),
        dining_estimate=to_dec(data.get('dining_estimate')),
        entertainment_estimate=to_dec(data.get('entertainment_estimate')),
        shopping_estimate=to_dec(data.get('shopping_estimate')),
        transport_estimate=to_dec(data.get('transport_estimate')),
        utilities_estimate=to_dec(data.get('utilities_estimate')),
        other_estimate=to_dec(data.get('other_estimate')),
        had_impulse_purchases=data.get('had_impulse_purchases', False),
        impulse_spending=to_dec(data.get('impulse_spending')),
        had_stress_purchases=data.get('had_stress_purchases', False),
        stress_spending=to_dec(data.get('stress_spending')),
        celebration_spending=to_dec(data.get('celebration_spending')),
        biggest_unnecessary_purchase=to_dec(data.get('biggest_unnecessary_purchase')),
        biggest_unnecessary_category=data.get('biggest_unnecessary_category'),
        wins=data.get('wins'),
        challenges=data.get('challenges'),
        completed_at=datetime.utcnow(),
        completion_time_seconds=data.get('completion_time_seconds'),
    )
    db.session.add(checkin)
    db.session.flush()

    calculator = WellnessScoreCalculator()
    checkin_dict = _checkin_to_dict(checkin)
    scores = calculator.calculate_overall_wellness(checkin_dict)
    previous_checkins = []
    prev_score_row = (
        WellnessScore.query.filter_by(user_id=user_id)
        .filter(WellnessScore.week_ending_date < week_ending)
        .order_by(desc(WellnessScore.week_ending_date))
        .first()
    )
    if prev_score_row:
        prev_scores = {
            'physical_score': float(prev_score_row.physical_score or 0),
            'mental_score': float(prev_score_row.mental_score or 0),
            'relational_score': float(prev_score_row.relational_score or 0),
            'financial_feeling_score': float(prev_score_row.financial_feeling_score or 0),
            'overall_wellness_score': float(prev_score_row.overall_wellness_score or 0),
        }
        changes = calculator.calculate_week_over_week_changes(scores, prev_scores)
    else:
        changes = {
            'physical_change': 0.0, 'mental_change': 0.0,
            'relational_change': 0.0, 'overall_change': 0.0,
        }

    score_row = WellnessScore(
        user_id=user_id,
        week_ending_date=week_ending,
        checkin_id=checkin.id,
        physical_score=scores['physical_score'],
        mental_score=scores['mental_score'],
        relational_score=scores['relational_score'],
        financial_feeling_score=scores['financial_feeling_score'],
        overall_wellness_score=scores['overall_wellness_score'],
        physical_change=changes.get('physical_change'),
        mental_change=changes.get('mental_change'),
        relational_change=changes.get('relational_change'),
        overall_change=changes.get('overall_change'),
    )
    db.session.add(score_row)

    streak_info = _update_streak(user_id, week_ending)
    _update_baselines(user_id)

    user_id_str = _get_user_id_str()
    current_streak = streak_info.get('current_streak') or 0
    checkin_for_achievements = {
        'overall_wellness_score': scores.get('overall_wellness_score'),
        'exercise_days': checkin_dict.get('exercise_days'),
        'meditation_minutes': checkin_dict.get('meditation_minutes'),
        'insight_unlocked': False,
    }

    correlations = _get_correlations_for_insights(user_id)
    baselines = {}
    bl = UserSpendingBaseline.query.filter_by(user_id=user_id).first()
    if bl:
        baselines = {
            'avg_groceries': float(bl.avg_groceries or 0),
            'avg_dining': float(bl.avg_dining or 0),
            'avg_entertainment': float(bl.avg_entertainment or 0),
            'avg_shopping': float(bl.avg_shopping or 0),
            'avg_transport': float(bl.avg_transport or 0),
            'avg_total_variable': float(bl.avg_total_variable or 0),
            'avg_impulse': float(bl.avg_impulse or 0),
        }
    prev_checkins_raw = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .filter(WeeklyCheckin.week_ending_date < week_ending)
        .order_by(desc(WeeklyCheckin.week_ending_date))
        .limit(10)
        .all()
    )
    previous_checkins = [_checkin_to_dict(c) for c in prev_checkins_raw]
    gen = InsightGenerator()
    insights = gen.generate_weekly_insights(
        checkin_dict, previous_checkins, correlations, baselines
    )
    checkin_for_achievements['insight_unlocked'] = len(insights) > 0
    newly_unlocked = AchievementService.check_achievements(
        user_id_str, checkin_for_achievements, current_streak
    )

    db.session.commit()

    return jsonify({
        'checkin_id': str(checkin.id),
        'week_ending_date': week_ending.isoformat(),
        'wellness_scores': {**scores, **changes},
        'streak_info': streak_info,
        'insights': [_insight_to_dict(i) for i in insights],
        'achievements_unlocked': newly_unlocked,
    }), 201


@wellness_checkin_bp.route('/checkin/current-week', methods=['GET'])
@require_auth
def get_current_week_checkin():
    """
    GET /api/wellness/checkin/current-week
    Get current week's check-in if exists.
    OpenAPI: summary: Get current week check-in; tags: [wellness].
    """
    user_id = _resolve_user_id()
    week_ending = _week_ending_today()
    checkin = WeeklyCheckin.query.filter_by(
        user_id=user_id, week_ending_date=week_ending
    ).first()
    if not checkin:
        return jsonify({'error': 'Not found', 'message': 'No check-in for this week yet.'}), 404
    return jsonify(_checkin_to_dict(checkin, include_scores=True))


@wellness_checkin_bp.route('/checkin/history', methods=['GET'])
@require_auth
def get_checkin_history():
    """
    GET /api/wellness/checkin/history?weeks=12
    Get check-in history; default 12 weeks, max 52.
    OpenAPI: summary: Check-in history; tags: [wellness]; parameters: weeks (query, integer).
    """
    user_id = _resolve_user_id()
    weeks = request.args.get('weeks', 12, type=int)
    weeks = max(1, min(52, weeks))
    checkins = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .order_by(desc(WeeklyCheckin.week_ending_date))
        .limit(weeks)
        .all()
    )
    return jsonify({
        'checkins': [_checkin_to_dict(c, include_scores=True) for c in checkins],
        'count': len(checkins),
    })


@wellness_checkin_bp.route('/scores/latest', methods=['GET'])
@require_auth
def get_latest_scores():
    """
    GET /api/wellness/scores/latest
    Get most recent wellness scores with week-over-week changes.
    OpenAPI: summary: Latest wellness scores; tags: [wellness].
    """
    user_id = _resolve_user_id()
    score = (
        WellnessScore.query.filter_by(user_id=user_id)
        .order_by(desc(WellnessScore.week_ending_date))
        .first()
    )
    if not score:
        return jsonify({'error': 'Not found', 'message': 'No wellness scores yet. Complete a check-in first.'}), 404
    return jsonify(_score_to_dict(score))


@wellness_checkin_bp.route('/scores/history', methods=['GET'])
@require_auth
def get_scores_history():
    """
    GET /api/wellness/scores/history?weeks=12
    Wellness score history for charts.
    OpenAPI: summary: Score history; tags: [wellness]; parameters: weeks.
    """
    user_id = _resolve_user_id()
    weeks = request.args.get('weeks', 12, type=int)
    weeks = max(1, min(52, weeks))
    scores = (
        WellnessScore.query.filter_by(user_id=user_id)
        .order_by(desc(WellnessScore.week_ending_date))
        .limit(weeks)
        .all()
    )
    return jsonify({
        'scores': [_score_to_dict(s) for s in scores],
    })


@wellness_checkin_bp.route('/spending/history', methods=['GET'])
@require_auth
def get_spending_history():
    """
    GET /api/wellness/spending/history?weeks=12
    Spending estimate history for charts.
    OpenAPI: summary: Spending history; tags: [wellness]; parameters: weeks.
    """
    user_id = _resolve_user_id()
    weeks = request.args.get('weeks', 12, type=int)
    weeks = max(1, min(52, weeks))
    checkins = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .order_by(desc(WeeklyCheckin.week_ending_date))
        .limit(weeks)
        .all()
    )
    out = []
    for c in checkins:
        gro = float(c.groceries_estimate or 0)
        din = float(c.dining_estimate or 0)
        ent = float(c.entertainment_estimate or 0)
        shop = float(c.shopping_estimate or 0)
        trans = float(c.transport_estimate or 0)
        total = gro + din + ent + shop + trans + float(c.utilities_estimate or 0) + float(c.other_estimate or 0)
        imp = float(c.impulse_spending or 0)
        stress = float(c.stress_spending or 0)
        out.append({
            'week_ending_date': c.week_ending_date.isoformat() if c.week_ending_date else None,
            'groceries': gro, 'dining': din, 'entertainment': ent,
            'shopping': shop, 'transport': trans,
            'total': total, 'impulse': imp, 'stress': stress,
        })
    return jsonify({'history': out})


@wellness_checkin_bp.route('/spending/baselines', methods=['GET'])
@require_auth
def get_spending_baselines():
    """
    GET /api/wellness/spending/baselines
    User's spending baselines (averages).
    OpenAPI: summary: Spending baselines; tags: [wellness].
    """
    user_id = _resolve_user_id()
    bl = UserSpendingBaseline.query.filter_by(user_id=user_id).first()
    if not bl:
        return jsonify({
            'avg_groceries': None, 'avg_dining': None, 'avg_entertainment': None,
            'avg_shopping': None, 'avg_transport': None, 'avg_total': None,
            'avg_impulse': None, 'weeks_of_data': 0,
        })
    return jsonify({
        'avg_groceries': float(bl.avg_groceries) if bl.avg_groceries else None,
        'avg_dining': float(bl.avg_dining) if bl.avg_dining else None,
        'avg_entertainment': float(bl.avg_entertainment) if bl.avg_entertainment else None,
        'avg_shopping': float(bl.avg_shopping) if bl.avg_shopping else None,
        'avg_transport': float(bl.avg_transport) if bl.avg_transport else None,
        'avg_total': float(bl.avg_total_variable) if bl.avg_total_variable else None,
        'avg_impulse': float(bl.avg_impulse) if bl.avg_impulse else None,
        'weeks_of_data': bl.weeks_of_data or 0,
    })


@wellness_checkin_bp.route('/insights', methods=['GET'])
@require_auth
def get_insights():
    """
    GET /api/wellness/insights
    Current insights from latest check-in and correlations. Encouragement if < 4 weeks.
    OpenAPI: summary: Wellness insights; tags: [wellness].
    """
    user_id = _resolve_user_id()
    checkins = (
        WeeklyCheckin.query.filter_by(user_id=user_id)
        .order_by(desc(WeeklyCheckin.week_ending_date))
        .limit(20)
        .all()
    )
    if len(checkins) < 4:
        return jsonify({
            'insights': [],
            'message': 'Complete a few more weekly check-ins to unlock personalized insights. We need about 4 weeks of data.',
            'weeks_of_data': len(checkins),
        })
    current = _checkin_to_dict(checkins[0])
    previous = [_checkin_to_dict(c) for c in checkins[1:]]
    correlations = _get_correlations_for_insights(user_id)
    baselines = {}
    bl = UserSpendingBaseline.query.filter_by(user_id=user_id).first()
    if bl:
        baselines = {
            'avg_groceries': float(bl.avg_groceries or 0),
            'avg_dining': float(bl.avg_dining or 0),
            'avg_entertainment': float(bl.avg_entertainment or 0),
            'avg_shopping': float(bl.avg_shopping or 0),
            'avg_transport': float(bl.avg_transport or 0),
            'avg_total_variable': float(bl.avg_total_variable or 0),
            'avg_total': float(bl.avg_total_variable or 0),
            'avg_impulse': float(bl.avg_impulse or 0),
        }
    gen = InsightGenerator()
    insights = gen.generate_weekly_insights(current, previous, correlations, baselines)
    return jsonify({
        'insights': [_insight_to_dict(i) for i in insights],
        'weeks_of_data': len(checkins),
    })


@wellness_checkin_bp.route('/correlations', methods=['GET'])
@require_auth
def get_correlations():
    """
    GET /api/wellness/correlations
    Computed correlations for user; message if insufficient data.
    OpenAPI: summary: Correlation data; tags: [wellness].
    """
    user_id = _resolve_user_id()
    corr = (
        WellnessFinanceCorrelation.query.filter_by(user_id=user_id)
        .order_by(desc(WellnessFinanceCorrelation.calculated_at))
        .first()
    )
    if not corr:
        return jsonify({
            'correlations': [],
            'message': 'Not enough data yet. Complete at least 4 weekly check-ins to compute correlations.',
        })
    def dec(v):
        return float(v) if v is not None else None
    return jsonify({
        'correlations': [{
            'start_date': corr.start_date.isoformat() if corr.start_date else None,
            'end_date': corr.end_date.isoformat() if corr.end_date else None,
            'weeks_analyzed': corr.weeks_analyzed,
            'stress_vs_impulse_spending': dec(corr.stress_vs_impulse_spending),
            'stress_vs_total_spending': dec(corr.stress_vs_total_spending),
            'exercise_vs_spending_control': dec(corr.exercise_vs_spending_control),
            'sleep_vs_dining_spending': dec(corr.sleep_vs_dining_spending),
            'mood_vs_entertainment_spending': dec(corr.mood_vs_entertainment_spending),
            'mood_vs_shopping_spending': dec(corr.mood_vs_shopping_spending),
            'meditation_vs_impulse_spending': dec(corr.meditation_vs_impulse_spending),
            'relationship_vs_discretionary_spending': dec(corr.relationship_vs_discretionary_spending),
            'data_points': corr.data_points,
            'confidence_level': corr.confidence_level,
            'strongest_correlation_type': corr.strongest_correlation_type,
            'strongest_correlation_value': dec(corr.strongest_correlation_value),
            'calculated_at': corr.calculated_at.isoformat() if corr.calculated_at else None,
        }],
    })


@wellness_checkin_bp.route('/correlations/refresh', methods=['POST'])
@require_auth
def refresh_correlations():
    """
    POST /api/wellness/correlations/refresh
    Manually trigger correlation and baseline recalculation.
    OpenAPI: summary: Refresh correlations; tags: [wellness].
    """
    user_id = _resolve_user_id()
    _refresh_correlations_and_baselines(user_id)
    db.session.commit()
    return get_correlations()


@wellness_checkin_bp.route('/streak', methods=['GET'])
@require_auth
def get_streak():
    """
    GET /api/wellness/streak
    User's check-in streak info with days_until_deadline.
    OpenAPI: summary: Streak info; tags: [wellness].
    """
    user_id_str = _get_user_id_str()
    info = StreakService.get_streak_info(user_id_str)
    info['streak_at_risk'] = StreakService.is_streak_at_risk(user_id_str)
    return jsonify(info)


@wellness_checkin_bp.route('/achievements', methods=['GET'])
@require_auth
def get_achievements():
    """
    GET /api/wellness/achievements
    List all achievements with user's progress and next achievements to unlock.
    OpenAPI: summary: List achievements with progress; tags: [wellness].
    """
    user_id_str = _get_user_id_str()
    all_achievements = AchievementService.get_user_achievements(user_id_str)
    next_achievements = AchievementService.get_next_achievements(user_id_str)
    return jsonify({
        'achievements': all_achievements,
        'next_achievements': next_achievements,
    })


@wellness_checkin_bp.route('/summary', methods=['GET'])
@require_auth
def get_summary():
    """
    GET /api/wellness/summary
    Dashboard summary: scores, streak, spending this week, vs baseline, top insights, weeks_of_data.
    OpenAPI: summary: Wellness dashboard summary; tags: [wellness].
    """
    user_id = _resolve_user_id()
    week_ending = _week_ending_today()
    checkin = WeeklyCheckin.query.filter_by(
        user_id=user_id, week_ending_date=week_ending
    ).first()
    score = (
        WellnessScore.query.filter_by(user_id=user_id)
        .order_by(desc(WellnessScore.week_ending_date))
        .first()
    )
    streak_row = WellnessCheckinStreak.query.filter_by(user_id=user_id).first()
    bl = UserSpendingBaseline.query.filter_by(user_id=user_id).first()
    count = WeeklyCheckin.query.filter_by(user_id=user_id).count()

    def dec(v):
        return float(v) if v is not None else None

    current_scores = None
    if score:
        current_scores = {
            'physical_score': dec(score.physical_score),
            'mental_score': dec(score.mental_score),
            'relational_score': dec(score.relational_score),
            'financial_feeling_score': dec(score.financial_feeling_score),
            'overall_wellness_score': dec(score.overall_wellness_score),
            'week_ending_date': score.week_ending_date.isoformat() if score.week_ending_date else None,
        }

    streak = {
        'current_streak': streak_row.current_streak if streak_row else 0,
        'longest_streak': streak_row.longest_streak if streak_row else 0,
        'last_checkin_date': streak_row.last_checkin_date.isoformat() if streak_row and streak_row.last_checkin_date else None,
        'total_checkins': streak_row.total_checkins if streak_row else 0,
    }

    spending_this_week = None
    spending_vs_baseline = None
    if checkin:
        gro = dec(checkin.groceries_estimate)
        din = dec(checkin.dining_estimate)
        ent = dec(checkin.entertainment_estimate)
        shop = dec(checkin.shopping_estimate)
        trans = dec(checkin.transport_estimate)
        total = gro + din + ent + dec(checkin.utilities_estimate) + dec(checkin.other_estimate)
        spending_this_week = {
            'groceries': gro, 'dining': din, 'entertainment': ent,
            'shopping': shop, 'transport': trans, 'total': total,
            'impulse': dec(checkin.impulse_spending), 'stress': dec(checkin.stress_spending),
        }
        if bl and bl.avg_total_variable:
            spending_vs_baseline = {
                'total_vs_avg': (total / float(bl.avg_total_variable)) * 100 if bl.avg_total_variable else None,
                'avg_total': float(bl.avg_total_variable),
            }

    top_insights = []
    if count >= 4:
        checkins = (
            WeeklyCheckin.query.filter_by(user_id=user_id)
            .order_by(desc(WeeklyCheckin.week_ending_date))
            .limit(10)
            .all()
        )
        current_dict = _checkin_to_dict(checkins[0]) if checkins else {}
        previous_dicts = [_checkin_to_dict(c) for c in checkins[1:]]
        baselines_dict = {}
        if bl:
            baselines_dict = {
                'avg_total_variable': float(bl.avg_total_variable or 0),
                'avg_impulse': float(bl.avg_impulse or 0),
                'avg_groceries': float(bl.avg_groceries or 0),
                'avg_dining': float(bl.avg_dining or 0),
                'avg_entertainment': float(bl.avg_entertainment or 0),
                'avg_shopping': float(bl.avg_shopping or 0),
                'avg_transport': float(bl.avg_transport or 0),
                'avg_total': float(bl.avg_total_variable or 0),
            }
        gen = InsightGenerator()
        insights = gen.generate_weekly_insights(
            current_dict, previous_dicts,
            _get_correlations_for_insights(user_id),
            baselines_dict,
        )
        top_insights = [_insight_to_dict(i) for i in insights[:3]]

    return jsonify({
        'current_scores': current_scores,
        'streak': streak,
        'spending_this_week': spending_this_week,
        'spending_vs_baseline': spending_vs_baseline,
        'top_insights': top_insights,
        'weeks_of_data': count,
    })
