#!/usr/bin/env python3
"""
Gamification API for Mingus Application

REST API endpoints for the gamification and streak tracking system.
Handles streak data, achievements, milestones, challenges, and recovery options.

Endpoints:
- GET /api/gamification/streak - Get user streak data
- GET /api/gamification/achievements - Get user achievements
- GET /api/gamification/milestones - Get milestone information
- GET /api/gamification/challenges - Get weekly challenges
- GET /api/gamification/leaderboard - Get leaderboard data
- POST /api/gamification/recovery - Process recovery actions
- POST /api/gamification/challenges/join - Join a challenge
- POST /api/gamification/achievements/claim - Claim an achievement
"""

import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from backend.models.database import db
from backend.models.user_models import User
from backend.models.gamification_models import *
from backend.auth.decorators import require_auth, require_csrf, get_current_user_id
from backend.utils.validation import APIValidator
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
from backend.services.gamification_service import GamificationService
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
gamification_api = Blueprint('gamification_api', __name__, url_prefix='/api/gamification')

# Initialize services
validator = APIValidator()
feature_service = FeatureFlagService()
gamification_service = GamificationService()

# ============================================================================
# MARSHMALLOW SCHEMAS FOR VALIDATION
# ============================================================================

class RecoveryActionSchema(Schema):
    """Schema for recovery action validation"""
    recovery_type = fields.String(required=True, validate=validate.OneOf([t.value for t in RecoveryType]))
    action = fields.String(required=True, validate=validate.Length(min=1, max=100))

class ChallengeJoinSchema(Schema):
    """Schema for challenge join validation"""
    challenge_id = fields.String(required=True, validate=validate.Length(min=1, max=100))

class AchievementClaimSchema(Schema):
    """Schema for achievement claim validation"""
    achievement_id = fields.String(required=True, validate=validate.Length(min=1, max=100))

class LeaderboardQuerySchema(Schema):
    """Schema for leaderboard query validation"""
    category = fields.String(validate=validate.OneOf(['streak', 'achievements', 'engagement']))
    limit = fields.Integer(validate=validate.Range(min=1, max=100))
    period = fields.String(validate=validate.OneOf(['week', 'month', 'year', 'all']))

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

# ============================================================================
# API ENDPOINTS
# ============================================================================

@gamification_api.route('/streak', methods=['GET'])
@cross_origin()
@require_auth
def get_streak_data():
    """
    Get comprehensive streak data for current user
    
    Returns streak information, milestones, achievements, recovery options,
    and weekly challenges.
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to gamification features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Gamification features are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get complete gamification data
        gamification_data = gamification_service.get_complete_gamification_data(user_id)
        
        if not gamification_data:
            return jsonify({
                'error': 'No data available',
                'message': 'Unable to retrieve gamification data'
            }), 404
        
        return jsonify({
            'success': True,
            'data': gamification_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting streak data for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve streak data'
        }), 500

@gamification_api.route('/achievements', methods=['GET'])
@cross_origin()
@require_auth
def get_achievements():
    """
    Get user achievements
    
    Returns all achievements with unlock status and progress.
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to gamification features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Gamification features are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get user achievements
        achievements = gamification_service.get_achievements(user_id)
        
        return jsonify({
            'success': True,
            'achievements': [
                {
                    'id': a.id,
                    'name': a.name,
                    'description': a.description,
                    'icon': a.icon,
                    'color': a.color,
                    'points': a.points,
                    'unlocked': a.unlocked,
                    'unlocked_date': a.unlocked_date.isoformat() if a.unlocked_date else None,
                    'category': a.category.value
                } for a in achievements
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting achievements for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve achievements'
        }), 500

@gamification_api.route('/milestones', methods=['GET'])
@cross_origin()
@require_auth
def get_milestones():
    """
    Get milestone information for user
    
    Returns milestones with progress and achievement status.
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to gamification features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Gamification features are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get user streak data
        streak_data = gamification_service.calculate_streak(user_id)
        
        # Get milestones
        milestones = gamification_service.get_milestones(user_id, streak_data)
        
        return jsonify({
            'success': True,
            'milestones': [
                {
                    'id': m.id,
                    'name': m.name,
                    'days_required': m.days_required,
                    'description': m.description,
                    'reward': m.reward,
                    'icon': m.icon,
                    'color': m.color,
                    'achieved': m.achieved,
                    'achieved_date': m.achieved_date.isoformat() if m.achieved_date else None,
                    'progress_percentage': m.progress_percentage
                } for m in milestones
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting milestones for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve milestones'
        }), 500

@gamification_api.route('/challenges', methods=['GET'])
@cross_origin()
@require_auth
def get_weekly_challenges():
    """
    Get current weekly challenges
    
    Returns available weekly challenges with progress.
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to gamification features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET_CAREER_VEHICLE):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Weekly challenges are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget_career_vehicle'
            }), 403
        
        # Get weekly challenges
        challenges = gamification_service.get_weekly_challenges(user_id)
        
        return jsonify({
            'success': True,
            'challenges': [
                {
                    'id': c.id,
                    'title': c.title,
                    'description': c.description,
                    'target': c.target,
                    'current_progress': c.current_progress,
                    'reward': c.reward,
                    'deadline': c.deadline.isoformat(),
                    'category': c.category.value,
                    'difficulty': c.difficulty.value
                } for c in challenges
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting weekly challenges for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve weekly challenges'
        }), 500

@gamification_api.route('/leaderboard', methods=['GET'])
@cross_origin()
@require_auth
def get_leaderboard():
    """
    Get leaderboard data
    
    Query parameters:
    - category: Leaderboard category (streak, achievements, engagement)
    - limit: Number of entries to return (default: 10, max: 100)
    - period: Time period (week, month, year, all)
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to gamification features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Gamification features are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get query parameters
        category = request.args.get('category', 'streak')
        limit = request.args.get('limit', 10, type=int)
        period = request.args.get('period', 'week')
        
        # Validate parameters
        if limit < 1 or limit > 100:
            return jsonify({
                'error': 'Invalid limit',
                'message': 'Limit must be between 1 and 100'
            }), 400
        
        if category not in ['streak', 'achievements', 'engagement']:
            return jsonify({
                'error': 'Invalid category',
                'message': 'Category must be one of: streak, achievements, engagement'
            }), 400
        
        # Get leaderboard data
        leaderboard_data = gamification_service.get_leaderboard(category, limit)
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard_data,
            'category': category,
            'period': period,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting leaderboard for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve leaderboard data'
        }), 500

@gamification_api.route('/recovery', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def process_recovery():
    """
    Process streak recovery action
    
    Request body:
    {
        "recovery_type": "restart|catch_up|grace_period|streak_freeze",
        "action": "action_identifier"
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
        is_valid, errors, validated_data = validate_request_data(RecoveryActionSchema, data)
        if not is_valid:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Invalid request data',
                'details': errors
            }), 400
        
        # Check if user has access to recovery features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Recovery features are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Process recovery action
        success = gamification_service.process_gamification_action(
            user_id, 
            'recovery', 
            validated_data
        )
        
        if not success:
            return jsonify({
                'error': 'Recovery failed',
                'message': 'Failed to process recovery action'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Recovery action processed successfully',
            'recovery_type': validated_data['recovery_type'],
            'action': validated_data['action']
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing recovery for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to process recovery action'
        }), 500

@gamification_api.route('/challenges/join', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def join_challenge():
    """
    Join a weekly challenge
    
    Request body:
    {
        "challenge_id": "challenge_identifier"
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
        is_valid, errors, validated_data = validate_request_data(ChallengeJoinSchema, data)
        if not is_valid:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Invalid request data',
                'details': errors
            }), 400
        
        # Check if user has access to challenge features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET_CAREER_VEHICLE):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Weekly challenges are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget_career_vehicle'
            }), 403
        
        # Join challenge
        success = gamification_service.process_gamification_action(
            user_id, 
            'challenge', 
            validated_data
        )
        
        if not success:
            return jsonify({
                'error': 'Join failed',
                'message': 'Failed to join challenge'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Successfully joined challenge',
            'challenge_id': validated_data['challenge_id']
        }), 200
        
    except Exception as e:
        logger.error(f"Error joining challenge for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to join challenge'
        }), 500

@gamification_api.route('/achievements/claim', methods=['POST'])
@cross_origin()
@require_auth
@require_csrf
def claim_achievement():
    """
    Claim an achievement
    
    Request body:
    {
        "achievement_id": "achievement_identifier"
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
        is_valid, errors, validated_data = validate_request_data(AchievementClaimSchema, data)
        if not is_valid:
            return jsonify({
                'error': 'Validation failed',
                'message': 'Invalid request data',
                'details': errors
            }), 400
        
        # Check if user has access to achievement features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Achievement features are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Claim achievement
        success = gamification_service.process_gamification_action(
            user_id, 
            'achievement_claim', 
            validated_data
        )
        
        if not success:
            return jsonify({
                'error': 'Claim failed',
                'message': 'Failed to claim achievement'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Achievement claimed successfully',
            'achievement_id': validated_data['achievement_id']
        }), 200
        
    except Exception as e:
        logger.error(f"Error claiming achievement for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to claim achievement'
        }), 500

@gamification_api.route('/analytics', methods=['GET'])
@cross_origin()
@require_auth
def get_engagement_analytics():
    """
    Get engagement analytics for user
    
    Returns comprehensive analytics including engagement score,
    consistency rating, and improvement trends.
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to analytics features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET_CAREER_VEHICLE):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Analytics features are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget_career_vehicle'
            }), 403
        
        # Get engagement analytics
        analytics = gamification_service.get_engagement_analytics(user_id)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve analytics'
        }), 500

@gamification_api.route('/tier-rewards', methods=['GET'])
@cross_origin()
@require_auth
def get_tier_rewards():
    """
    Get tier-specific rewards for user
    
    Returns rewards available based on user's current tier.
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has access to gamification features
        if not check_user_tier_access(user_id, FeatureTier.BUDGET):
            return jsonify({
                'error': 'Feature not available',
                'message': 'Gamification features are not available in your current tier.',
                'upgrade_required': True,
                'required_tier': 'budget'
            }), 403
        
        # Get tier rewards
        tier_rewards = gamification_service.get_tier_rewards(user_id)
        
        return jsonify({
            'success': True,
            'tier_rewards': tier_rewards
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting tier rewards for user {user_id}: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve tier rewards'
        }), 500
