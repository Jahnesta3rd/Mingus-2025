#!/usr/bin/env python3
"""
Daily Outlook API for Mingus Application

REST API endpoints for the Daily Outlook feature with proper authentication,
validation, and tier restrictions.

Endpoints:
- GET /api/daily-outlook - Get today's outlook for current user
- GET /api/daily-outlook/history - Get outlook history with pagination
- POST /api/daily-outlook/action-completed - Mark action as completed
- POST /api/daily-outlook/rating - Submit user rating
- GET /api/daily-outlook/streak - Get current streak information
- POST /api/relationship-status - Update relationship status
"""

import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from backend.models.database import db
from backend.models.user_models import User
from backend.models.daily_outlook import (
    DailyOutlook, UserRelationshipStatus, RelationshipStatus
)
from backend.auth.decorators import require_auth, require_csrf, get_current_user_id
from backend.utils.validation import APIValidator
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier, FeatureFlag
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
from typing import Dict, Any, List, Optional
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import func, and_, or_, desc, asc
from werkzeug.exceptions import BadRequest, NotFound, Forbidden, Unauthorized

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
daily_outlook_api = Blueprint('daily_outlook_api', __name__, url_prefix='/api/daily-outlook')

# Initialize services
validator = APIValidator()
feature_service = FeatureFlagService()

# ============================================================================
# MARSHMALLOW SCHEMAS FOR VALIDATION
# ============================================================================

class ActionCompletedSchema(Schema):
    """Schema for action completion validation"""
    action_id = fields.String(required=True, validate=validate.Length(min=1, max=100))
    completion_status = fields.Boolean(required=True)
    completion_notes = fields.String(validate=validate.Length(max=500))

class RatingSchema(Schema):
    """Schema for user rating validation"""
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    feedback = fields.String(validate=validate.Length(max=1000))

class RelationshipStatusSchema(Schema):
    """Schema for relationship status update validation"""
    status = fields.String(required=True, validate=validate.OneOf([status.value for status in RelationshipStatus]))
    satisfaction_score = fields.Integer(required=True, validate=validate.Range(min=1, max=10))
    financial_impact_score = fields.Integer(required=True, validate=validate.Range(min=1, max=10))

class HistoryQuerySchema(Schema):
    """Schema for history query parameters validation"""
    start_date = fields.Date(load_default=None)
    end_date = fields.Date(load_default=None)
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_user_tier_access(user_id: int, required_tier: FeatureTier) -> bool:
    """Check if user has access to a specific tier feature"""
    try:
        user_tier = feature_service.get_user_tier(user_id)
        tier_hierarchy = {
            FeatureTier.BUDGET: 1,
            FeatureTier.BUDGET_CAREER_VEHICLE: 2,
            FeatureTier.MID_TIER: 3,
            FeatureTier.PROFESSIONAL: 4
        }
        
        user_level = tier_hierarchy.get(user_tier, 0)
        required_level = tier_hierarchy.get(required_tier, 999)
        
        return user_level >= required_level
    except Exception as e:
        logger.error(f"Error checking tier access for user {user_id}: {e}")
        return False

def validate_request_data(schema_class, data: Dict[str, Any]) -> tuple[bool, List[str], Dict[str, Any]]:
    """Validate request data using Marshmallow schema"""
    try:
        schema = schema_class()
        validated_data = schema.load(data)
        return True, [], validated_data
    except ValidationError as e:
        errors = []
        for field, messages in e.messages.items():
            if isinstance(messages, list):
                errors.extend([f"{field}: {msg}" for msg in messages])
            else:
                errors.append(f"{field}: {messages}")
        return False, errors, {}
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, [f"Validation failed: {str(e)}"], {}

def calculate_streak_count(user_id: int, current_date: date) -> int:
    """Calculate user's current streak count"""
    try:
        # Get the most recent outlook before today
        yesterday = current_date - timedelta(days=1)
        recent_outlook = DailyOutlook.query.filter(
            and_(
                DailyOutlook.user_id == user_id,
                DailyOutlook.date < current_date
            )
        ).order_by(desc(DailyOutlook.date)).first()
        
        if not recent_outlook:
            return 0
        
        # Count consecutive days with outlooks
        streak_count = 0
        check_date = recent_outlook.date
        
        while True:
            outlook = DailyOutlook.query.filter(
                and_(
                    DailyOutlook.user_id == user_id,
                    DailyOutlook.date == check_date
                )
            ).first()
            
            if not outlook:
                break
                
            streak_count += 1
            check_date -= timedelta(days=1)
            
            # Prevent infinite loop
            if streak_count > 365:
                break
        
        return streak_count
    except Exception as e:
        logger.error(f"Error calculating streak for user {user_id}: {e}")
        return 0

def update_user_relationship_status(user_id: int, status: str, satisfaction_score: int, financial_impact_score: int) -> bool:
    """Update user's relationship status"""
    try:
        # Get or create relationship status record
        relationship_status = UserRelationshipStatus.query.filter_by(user_id=user_id).first()
        
        if not relationship_status:
            relationship_status = UserRelationshipStatus(
                user_id=user_id,
                status=RelationshipStatus(status),
                satisfaction_score=satisfaction_score,
                financial_impact_score=financial_impact_score
            )
            db.session.add(relationship_status)
        else:
            relationship_status.status = RelationshipStatus(status)
            relationship_status.satisfaction_score = satisfaction_score
            relationship_status.financial_impact_score = financial_impact_score
            relationship_status.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating relationship status for user {user_id}: {e}")
        db.session.rollback()
        return False

# ============================================================================
# API ENDPOINTS
# ============================================================================

@daily_outlook_api.route('/', methods=['GET'])
@cross_origin()
@require_auth
def get_todays_outlook():
    """
    Get today's outlook for current user
    
    Returns complete daily outlook data, updates view timestamp, and increments streak if consecutive day
    """
    try:
        user_id = get_current_user_id()
        today = date.today()
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Daily Outlook feature is not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get today's outlook
        outlook = DailyOutlook.query.filter(
            and_(
                DailyOutlook.user_id == user_id,
                DailyOutlook.date == today
            )
        ).first()
        
        if not outlook:
            return jsonify({
                'error': 'No outlook available',
                'message': 'No daily outlook available for today. Please check back later.',
                'date': today.isoformat()
            }), 404
        
        # Update view timestamp
        outlook.viewed_at = datetime.utcnow()
        
        # Calculate and update streak count
        streak_count = calculate_streak_count(user_id, today)
        outlook.streak_count = streak_count
        
        db.session.commit()
        
        # Return outlook data
        return jsonify({
            'success': True,
            'outlook': outlook.to_dict(),
            'streak_info': {
                'current_streak': streak_count,
                'viewed_at': outlook.viewed_at.isoformat() if outlook.viewed_at else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting today's outlook for user {user_id}: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve today\'s outlook'
        }), 500

@daily_outlook_api.route('/history', methods=['GET'])
@cross_origin()
@require_auth
def get_outlook_history():
    """
    Get outlook history with optional date range and pagination
    
    Query parameters:
    - start_date: Start date for filtering (YYYY-MM-DD)
    - end_date: End date for filtering (YYYY-MM-DD)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Daily Outlook feature is not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Validate query parameters
        query_params = {
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'page': request.args.get('page', 1, type=int),
            'per_page': request.args.get('per_page', 20, type=int)
        }
        
        # Convert date strings to date objects
        if query_params['start_date']:
            try:
                query_params['start_date'] = datetime.strptime(query_params['start_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': 'Invalid date format',
                    'message': 'start_date must be in YYYY-MM-DD format'
                }), 400
        
        if query_params['end_date']:
            try:
                query_params['end_date'] = datetime.strptime(query_params['end_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': 'Invalid date format',
                    'message': 'end_date must be in YYYY-MM-DD format'
                }), 400
        
        # Validate pagination parameters
        if query_params['page'] < 1:
            return jsonify({
                'error': 'Invalid page number',
                'message': 'Page number must be greater than 0'
            }), 400
        
        if query_params['per_page'] < 1 or query_params['per_page'] > 100:
            return jsonify({
                'error': 'Invalid per_page value',
                'message': 'per_page must be between 1 and 100'
            }), 400
        
        # Build query
        query = DailyOutlook.query.filter(DailyOutlook.user_id == user_id)
        
        if query_params['start_date']:
            query = query.filter(DailyOutlook.date >= query_params['start_date'])
        
        if query_params['end_date']:
            query = query.filter(DailyOutlook.date <= query_params['end_date'])
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        outlooks = query.order_by(desc(DailyOutlook.date)).paginate(
            page=query_params['page'],
            per_page=query_params['per_page'],
            error_out=False
        )
        
        # Calculate engagement metrics
        engagement_metrics = {
            'total_outlooks': total_count,
            'average_rating': 0,
            'completion_rate': 0,
            'streak_high_score': 0
        }
        
        if total_count > 0:
            # Calculate average rating
            avg_rating = db.session.query(func.avg(DailyOutlook.user_rating)).filter(
                and_(
                    DailyOutlook.user_id == user_id,
                    DailyOutlook.user_rating.isnot(None)
                )
            ).scalar()
            engagement_metrics['average_rating'] = round(float(avg_rating or 0), 2)
            
            # Calculate completion rate (simplified - based on actions completed)
            completed_outlooks = query.filter(
                DailyOutlook.actions_completed.isnot(None)
            ).count()
            engagement_metrics['completion_rate'] = round((completed_outlooks / total_count) * 100, 2)
            
            # Get highest streak
            max_streak = db.session.query(func.max(DailyOutlook.streak_count)).filter(
                DailyOutlook.user_id == user_id
            ).scalar()
            engagement_metrics['streak_high_score'] = max_streak or 0
        
        return jsonify({
            'success': True,
            'outlooks': [outlook.to_dict() for outlook in outlooks.items],
            'pagination': {
                'page': query_params['page'],
                'per_page': query_params['per_page'],
                'total_count': total_count,
                'total_pages': outlooks.pages,
                'has_next': outlooks.has_next,
                'has_prev': outlooks.has_prev
            },
            'engagement_metrics': engagement_metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting outlook history for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve outlook history'
        }), 500

@daily_outlook_api.route('/action-completed', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def mark_action_completed():
    """
    Mark action as completed
    
    Request body:
    {
        "action_id": "string",
        "completion_status": true,
        "completion_notes": "optional notes"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body is required'
            }), 400
        
        # Validate request data
        is_valid, errors, validated_data = validate_request_data(ActionCompletedSchema, data)
        if not is_valid:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Invalid request data',
                'details': errors
            }), 400
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Daily Outlook feature is not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get today's outlook
        today = date.today()
        outlook = DailyOutlook.query.filter(
            and_(
                DailyOutlook.user_id == user_id,
                DailyOutlook.date == today
            )
        ).first()
        
        if not outlook:
            return jsonify({
                'error': 'No outlook available',
                'message': 'No daily outlook available for today'
            }), 404
        
        # Update actions completed
        actions_completed = outlook.actions_completed or {}
        actions_completed[validated_data['action_id']] = {
            'completed': validated_data['completion_status'],
            'completed_at': datetime.utcnow().isoformat(),
            'notes': validated_data.get('completion_notes', '')
        }
        
        outlook.actions_completed = actions_completed
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Action completion status updated',
            'action_id': validated_data['action_id'],
            'completion_status': validated_data['completion_status']
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating action completion for user {user_id}: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to update action completion status'
        }), 500

@daily_outlook_api.route('/rating', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def submit_rating():
    """
    Submit user rating for today's outlook
    
    Request body:
    {
        "rating": 1-5,
        "feedback": "optional feedback"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body is required'
            }), 400
        
        # Validate request data
        is_valid, errors, validated_data = validate_request_data(RatingSchema, data)
        if not is_valid:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Invalid request data',
                'details': errors
            }), 400
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Daily Outlook feature is not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get today's outlook
        today = date.today()
        outlook = DailyOutlook.query.filter(
            and_(
                DailyOutlook.user_id == user_id,
                DailyOutlook.date == today
            )
        ).first()
        
        if not outlook:
            return jsonify({
                'error': 'No outlook available',
                'message': 'No daily outlook available for today'
            }), 404
        
        # Update rating
        outlook.user_rating = validated_data['rating']
        
        # Store feedback in a separate field or extend the model as needed
        # For now, we'll store it in the surprise_element field as a placeholder
        if validated_data.get('feedback'):
            outlook.surprise_element = validated_data['feedback']
        
        db.session.commit()
        
        # Check if this triggers A/B testing flags (simplified implementation)
        ab_test_flags = {}
        if validated_data['rating'] >= 4:
            ab_test_flags['high_rating_user'] = True
        elif validated_data['rating'] <= 2:
            ab_test_flags['low_rating_user'] = True
        
        return jsonify({
            'success': True,
            'message': 'Rating submitted successfully',
            'rating': validated_data['rating'],
            'ab_test_flags': ab_test_flags
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting rating for user {user_id}: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to submit rating'
        }), 500

@daily_outlook_api.route('/streak', methods=['GET'])
@cross_origin()
@require_auth
def get_streak_info():
    """
    Get current streak information including milestones and rewards
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Daily Outlook feature is not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get current streak
        current_streak = calculate_streak_count(user_id, date.today())
        
        # Get highest streak ever achieved
        max_streak = db.session.query(func.max(DailyOutlook.streak_count)).filter(
            DailyOutlook.user_id == user_id
        ).scalar() or 0
        
        # Define milestones and rewards
        milestones = [
            {'days': 3, 'name': 'Getting Started', 'reward': 'Unlock personalized insights'},
            {'days': 7, 'name': 'Week Warrior', 'reward': 'Advanced progress tracking'},
            {'days': 14, 'name': 'Two Week Champion', 'reward': 'Priority support access'},
            {'days': 30, 'name': 'Monthly Master', 'reward': 'Exclusive content access'},
            {'days': 60, 'name': 'Consistency King', 'reward': 'Premium feature preview'},
            {'days': 100, 'name': 'Century Club', 'reward': 'VIP status upgrade'}
        ]
        
        # Find next milestone
        next_milestone = None
        for milestone in milestones:
            if current_streak < milestone['days']:
                next_milestone = milestone
                break
        
        # Find achieved milestones
        achieved_milestones = [m for m in milestones if current_streak >= m['days']]
        
        # Streak recovery options (simplified)
        recovery_options = []
        if current_streak == 0:
            recovery_options = [
                {
                    'type': 'restart',
                    'description': 'Start fresh with a new streak',
                    'action': 'begin_new_streak'
                }
            ]
        elif current_streak < 7:
            recovery_options = [
                {
                    'type': 'catch_up',
                    'description': 'Complete missed days to maintain streak',
                    'action': 'complete_missed_days'
                }
            ]
        
        return jsonify({
            'success': True,
            'streak_info': {
                'current_streak': current_streak,
                'highest_streak': max_streak,
                'next_milestone': next_milestone,
                'achieved_milestones': achieved_milestones,
                'recovery_options': recovery_options
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting streak info for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve streak information'
        }), 500

# ============================================================================
# RELATIONSHIP STATUS ENDPOINT (separate from daily-outlook prefix)
# ============================================================================

@daily_outlook_api.route('/relationship-status', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def update_relationship_status():
    """
    Update relationship status
    
    Request body:
    {
        "status": "single_career_focused|single_looking|dating|early_relationship|committed|engaged|married|complicated",
        "satisfaction_score": 1-10,
        "financial_impact_score": 1-10
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body is required'
            }), 400
        
        # Validate request data
        is_valid, errors, validated_data = validate_request_data(RelationshipStatusSchema, data)
        if not is_valid:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Invalid request data',
                'details': errors
            }), 400
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Daily Outlook feature is not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Update relationship status
        success = update_user_relationship_status(
            user_id,
            validated_data['status'],
            validated_data['satisfaction_score'],
            validated_data['financial_impact_score']
        )
        
        if not success:
            return jsonify({
                'error': 'Update failed',
                'message': 'Failed to update relationship status'
            }), 500
        
        # Get updated relationship status
        relationship_status = UserRelationshipStatus.query.filter_by(user_id=user_id).first()
        
        return jsonify({
            'success': True,
            'message': 'Relationship status updated successfully',
            'relationship_status': relationship_status.to_dict() if relationship_status else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating relationship status for user {user_id}: {e}")
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to update relationship status'
        }), 500
