#!/usr/bin/env python3
"""
Test version of the Daily Outlook API without authentication decorators.

This module provides the same business logic as the production API
but without the @require_auth decorators that cause issues in testing.
"""

from backend.services.daily_outlook_service import DailyOutlookService
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
from backend.models.daily_outlook import DailyOutlook, UserRelationshipStatus
from backend.models.user_models import User
from backend.models.database import db
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

# Create test blueprint
test_daily_outlook_api = Blueprint('test_daily_outlook_api', __name__)

# Initialize services
daily_outlook_service = DailyOutlookService()
feature_flag_service = FeatureFlagService()


def get_current_user_id():
    """Mock function to get current user ID for testing"""
    # This will be mocked in tests
    return 1


def check_user_tier_access(user_id, required_tier):
    """Mock function to check user tier access for testing"""
    # This will be mocked in tests
    return True


@test_daily_outlook_api.route('/api/daily-outlook/', methods=['GET'])
def get_daily_outlook():
    """Get today's daily outlook for the current user"""
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'success': False,
                'error': 'Insufficient tier access for daily outlook feature'
            }), 403
        
        # Get today's outlook
        today = date.today()
        outlook = DailyOutlook.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        if not outlook:
            return jsonify({
                'success': False,
                'error': 'No daily outlook found for today'
            }), 404
        
        # Get streak information
        streak_count = daily_outlook_service.calculate_streak_count(user_id, today)
        
        return jsonify({
            'success': True,
            'outlook': outlook.to_dict(),
            'streak_info': {
                'current_streak': streak_count,
                'last_updated': outlook.updated_at.isoformat() if hasattr(outlook, 'updated_at') and outlook.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting daily outlook: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@test_daily_outlook_api.route('/api/daily-outlook/history', methods=['GET'])
def get_daily_outlook_history():
    """Get daily outlook history for the current user"""
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'success': False,
                'error': 'Insufficient tier access for daily outlook feature'
            }), 403
        
        # Get query parameters
        limit = request.args.get('limit', 30, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get outlook history
        outlooks = DailyOutlook.query.filter_by(user_id=user_id)\
            .order_by(DailyOutlook.date.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return jsonify({
            'success': True,
            'outlooks': [outlook.to_dict() for outlook in outlooks],
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': DailyOutlook.query.filter_by(user_id=user_id).count()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting daily outlook history: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@test_daily_outlook_api.route('/api/daily-outlook/action-completed', methods=['POST'])
def mark_action_completed():
    """Mark a daily outlook action as completed"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or 'action_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Action ID is required'
            }), 400
        
        action_id = data['action_id']
        completion_notes = data.get('completion_notes', '')
        
        # Get today's outlook
        today = date.today()
        outlook = DailyOutlook.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        if not outlook:
            return jsonify({
                'success': False,
                'error': 'No daily outlook found for today'
            }), 404
        
        # Update the outlook with completed action
        outlook.actions_completed = outlook.actions_completed or []
        if action_id not in outlook.actions_completed:
            outlook.actions_completed.append(action_id)
        
        # Note: completion_notes could be stored in a separate field if needed
        
        outlook.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Action marked as completed',
            'outlook': outlook.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error marking action as completed: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@test_daily_outlook_api.route('/api/daily-outlook/rating', methods=['POST'])
def submit_daily_rating():
    """Submit daily outlook rating"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or 'rating' not in data:
            return jsonify({
                'success': False,
                'error': 'Rating is required'
            }), 400
        
        rating = data['rating']
        if not isinstance(rating, (int, float)) or rating < 1 or rating > 10:
            return jsonify({
                'success': False,
                'error': 'Rating must be a number between 1 and 10'
            }), 400
        
        # Get today's outlook
        today = date.today()
        outlook = DailyOutlook.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        if not outlook:
            return jsonify({
                'success': False,
                'error': 'No daily outlook found for today'
            }), 404
        
        # Update the outlook with rating
        outlook.user_rating = rating
        outlook.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rating submitted successfully',
            'outlook': outlook.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error submitting daily rating: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@test_daily_outlook_api.route('/api/daily-outlook/streak', methods=['GET'])
def get_streak_info():
    """Get streak information for the current user"""
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'success': False,
                'error': 'Insufficient tier access for daily outlook feature'
            }), 403
        
        # Get streak information
        today = date.today()
        streak_count = daily_outlook_service.calculate_streak_count(user_id, today)
        
        # Get longest streak
        outlooks = DailyOutlook.query.filter_by(user_id=user_id)\
            .order_by(DailyOutlook.date.desc())\
            .all()
        
        longest_streak = 0
        current_streak = 0
        last_date = None
        
        for outlook in outlooks:
            if last_date is None:
                last_date = outlook.date
                current_streak = 1
            elif (last_date - outlook.date).days == 1:
                current_streak += 1
                last_date = outlook.date
            else:
                longest_streak = max(longest_streak, current_streak)
                current_streak = 1
                last_date = outlook.date
        
        longest_streak = max(longest_streak, current_streak)
        
        return jsonify({
            'success': True,
            'streak_info': {
                'current_streak': streak_count,
                'longest_streak': longest_streak,
                'total_outlooks': len(outlooks)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting streak info: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@test_daily_outlook_api.route('/api/relationship-status', methods=['GET'])
def get_relationship_status():
    """Get current relationship status for the user"""
    try:
        user_id = get_current_user_id()
        
        # Get relationship status
        relationship_status = UserRelationshipStatus.query.filter_by(user_id=user_id).first()
        
        if not relationship_status:
            return jsonify({
                'success': True,
                'relationship_status': None,
                'message': 'No relationship status set'
            })
        
        return jsonify({
            'success': True,
            'relationship_status': {
                'status': relationship_status.status.value,
                'satisfaction_score': relationship_status.satisfaction_score,
                'financial_impact_score': relationship_status.financial_impact_score,
                'last_updated': relationship_status.updated_at.isoformat() if relationship_status.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting relationship status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@test_daily_outlook_api.route('/api/relationship-status', methods=['POST'])
def update_relationship_status():
    """Update relationship status for the user"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request data is required'
            }), 400
        
        required_fields = ['status', 'satisfaction_score', 'financial_impact_score']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        status = data['status']
        satisfaction_score = data['satisfaction_score']
        financial_impact_score = data['financial_impact_score']
        
        # Validate scores
        if not isinstance(satisfaction_score, int) or satisfaction_score < 1 or satisfaction_score > 10:
            return jsonify({
                'success': False,
                'error': 'Satisfaction score must be an integer between 1 and 10'
            }), 400
        
        if not isinstance(financial_impact_score, int) or financial_impact_score < 1 or financial_impact_score > 10:
            return jsonify({
                'success': False,
                'error': 'Financial impact score must be an integer between 1 and 10'
            }), 400
        
        # Update relationship status
        success = daily_outlook_service.update_user_relationship_status(
            user_id, status, satisfaction_score, financial_impact_score
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to update relationship status'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Relationship status updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating relationship status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@test_daily_outlook_api.route('/api/v2/daily-outlook/<int:user_id>', methods=['GET'])
def get_daily_outlook_v2(user_id):
    """Get daily outlook for a specific user (v2 API)"""
    try:
        # Check if user has access to daily outlook feature
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'success': False,
                'error': 'Insufficient tier access for daily outlook feature'
            }), 403
        
        # Get today's outlook
        today = date.today()
        outlook = DailyOutlook.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        if not outlook:
            return jsonify({
                'success': False,
                'error': 'No daily outlook found for today'
            }), 404
        
        # Get streak information
        streak_count = daily_outlook_service.calculate_streak_count(user_id, today)
        
        return jsonify({
            'success': True,
            'outlook': outlook.to_dict(),
            'streak_info': {
                'current_streak': streak_count,
                'last_updated': outlook.updated_at.isoformat() if hasattr(outlook, 'updated_at') and outlook.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting daily outlook v2: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
