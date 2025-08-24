"""
Meme Splash Page API Routes
Flask API endpoints for the meme splash page feature in the Mingus personal finance app.
"""

from flask import Blueprint, request, jsonify, session, current_app
from flask_cors import cross_origin
from functools import wraps
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
import time
from datetime import datetime, timedelta
import json

from ..services.meme_service import MemeService
from ..models.meme_models import UserMemePreferences, UserMemeHistory
from ..models.user import User

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
meme_bp = Blueprint('meme', __name__, url_prefix='/api')

# Simple in-memory rate limiting (in production, use Redis)
_rate_limit_store = {}
_rate_limit_cleanup_time = time.time()

def get_db_session() -> Session:
    """Get database session"""
    return current_app.db.session

def require_auth():
    """Decorator to require authentication"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return wrapper
    return decorator

def get_user_id() -> Optional[int]:
    """Get current user ID from session"""
    return session.get('user_id')

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            global _rate_limit_store, _rate_limit_cleanup_time
            
            # Clean up old entries every 5 minutes
            current_time = time.time()
            if current_time - _rate_limit_cleanup_time > 300:
                _rate_limit_store = {k: v for k, v in _rate_limit_store.items() 
                                   if current_time - v['timestamp'] < window_seconds}
                _rate_limit_cleanup_time = current_time
            
            # Get client identifier (IP + user_id if authenticated)
            user_id = get_user_id()
            client_id = f"{request.remote_addr}_{user_id or 'anonymous'}"
            
            # Check rate limit
            if client_id in _rate_limit_store:
                client_data = _rate_limit_store[client_id]
                if current_time - client_data['timestamp'] < window_seconds:
                    if client_data['count'] >= max_requests:
                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'retry_after': int(window_seconds - (current_time - client_data['timestamp'])),
                            'limit': max_requests
                        }), 429
                    client_data['count'] += 1
                else:
                    _rate_limit_store[client_id] = {
                        'count': 1,
                        'timestamp': current_time
                    }
            else:
                _rate_limit_store[client_id] = {
                    'count': 1,
                    'timestamp': current_time
                }
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_json_input(required_fields):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Error Handlers
@meme_bp.errorhandler(404)
def meme_not_found(error):
    return jsonify({'error': 'Meme not found'}), 404

@meme_bp.errorhandler(403)
def access_denied(error):
    return jsonify({'error': 'Access denied'}), 403

@meme_bp.errorhandler(429)
def rate_limited(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429

@meme_bp.errorhandler(500)
def internal_error(error):
    db_session = get_db_session()
    db_session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# API Endpoints

@meme_bp.route('/user-meme/<int:user_id>', methods=['GET'])
@cross_origin()
@require_auth()
@rate_limit(max_requests=50, window_seconds=60)
def get_user_meme(user_id):
    """
    GET /api/user-meme/<user_id>
    Returns personalized meme for user
    """
    try:
        # Verify user is requesting their own meme or is admin
        current_user_id = get_user_id()
        if current_user_id != user_id:
            # Check if user is admin (you can implement admin check here)
            return jsonify({'error': 'Unauthorized access'}), 403
        
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        # Check if user exists
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"User {user_id} not found")
            return jsonify({'error': 'User not found'}), 404
        
        # Get personalized meme for user
        meme = meme_service.select_best_meme_for_user(user_id)
        
        if not meme:
            logger.info(f"No meme available for user {user_id}")
            return jsonify({
                'message': 'No meme available at this time',
                'meme': None,
                'next_available': None
            }), 200
        
        # Record the view interaction
        meme_service.record_user_interaction(
            user_id=user_id,
            meme_id=meme['id'],
            interaction_type='view',
            session_id=request.headers.get('X-Session-ID'),
            source_page='meme_splash',
            device_type=request.headers.get('User-Agent', '').split('/')[0] if request.headers.get('User-Agent') else None,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        logger.info(f"Meme {meme['id']} served to user {user_id}")
        
        return jsonify({
            'success': True,
            'meme': {
                'id': meme['id'],
                'image_url': meme['image'],
                'caption': meme['caption'],
                'category': meme['category'],
                'alt_text': meme['alt_text'],
                'tags': meme['tags']
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting meme for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve meme'}), 500

@meme_bp.route('/meme-analytics', methods=['POST'])
@cross_origin()
@require_auth()
@rate_limit(max_requests=100, window_seconds=60)
@validate_json_input(['meme_id', 'interaction_type'])
def track_meme_analytics():
    """
    POST /api/meme-analytics
    Tracks user interactions with memes
    """
    try:
        data = request.get_json()
        user_id = get_user_id()
        
        # Validate interaction type
        valid_interactions = ['viewed', 'skipped', 'continued', 'liked', 'shared', 'reported']
        interaction_type = data['interaction_type']
        if interaction_type not in valid_interactions:
            return jsonify({
                'error': f'Invalid interaction type. Must be one of: {", ".join(valid_interactions)}'
            }), 400
        
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        # Map frontend interaction types to backend types
        interaction_mapping = {
            'viewed': 'view',
            'skipped': 'skip',
            'continued': 'view',
            'liked': 'like',
            'shared': 'share',
            'reported': 'report'
        }
        
        backend_interaction_type = interaction_mapping.get(interaction_type, 'view')
        
        # Record the interaction
        history = meme_service.record_user_interaction(
            user_id=user_id,
            meme_id=data['meme_id'],
            interaction_type=backend_interaction_type,
            time_spent=data.get('time_spent_seconds', 0),
            session_id=request.headers.get('X-Session-ID'),
            source_page=data.get('source_page', 'meme_splash'),
            device_type=request.headers.get('User-Agent', '').split('/')[0] if request.headers.get('User-Agent') else None,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        logger.info(f"Recorded {interaction_type} interaction for user {user_id} with meme {data['meme_id']}")
        
        return jsonify({
            'success': True,
            'message': f'{interaction_type.capitalize()} interaction recorded',
            'interaction_id': history.id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error tracking meme analytics: {str(e)}")
        return jsonify({'error': 'Failed to track analytics'}), 500

@meme_bp.route('/user-meme-preferences/<int:user_id>', methods=['GET'])
@cross_origin()
@require_auth()
@rate_limit(max_requests=30, window_seconds=60)
def get_user_meme_preferences(user_id):
    """
    GET /api/user-meme-preferences/<user_id>
    Returns user's meme preferences and analytics
    """
    try:
        # Verify user is requesting their own preferences or is admin
        current_user_id = get_user_id()
        if current_user_id != user_id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        # Check if user exists
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user preferences
        preferences = meme_service.get_user_preferences(user_id)
        if not preferences:
            # Create default preferences
            preferences = meme_service.create_user_preferences(user_id, {
                'memes_enabled': True,
                'preferred_categories': [],
                'frequency_setting': 'daily'
            })
        
        # Get user statistics
        stats = meme_service.get_user_meme_stats(user_id)
        
        # Calculate engagement metrics
        total_interactions = stats.get('total_interactions', 0)
        interactions_by_type = stats.get('interactions_by_type', {})
        
        skip_count = interactions_by_type.get('skip', 0)
        view_count = interactions_by_type.get('view', 0)
        like_count = interactions_by_type.get('like', 0)
        
        skip_rate = (skip_count / total_interactions * 100) if total_interactions > 0 else 0
        engagement_rate = (like_count / view_count * 100) if view_count > 0 else 0
        
        logger.info(f"Retrieved preferences for user {user_id}")
        
        return jsonify({
            'success': True,
            'preferences': {
                'memes_enabled': preferences.memes_enabled,
                'preferred_categories': preferences.preferred_categories_list,
                'frequency_setting': preferences.frequency_setting,
                'custom_frequency_days': preferences.custom_frequency_days,
                'last_meme_shown_at': preferences.last_meme_shown_at.isoformat() if preferences.last_meme_shown_at else None,
                'opt_out_reason': preferences.opt_out_reason,
                'opt_out_date': preferences.opt_out_date.isoformat() if preferences.opt_out_date else None
            },
            'analytics': {
                'total_interactions': total_interactions,
                'interactions_by_type': interactions_by_type,
                'favorite_categories': stats.get('favorite_categories', []),
                'skip_rate': round(skip_rate, 2),
                'engagement_rate': round(engagement_rate, 2),
                'last_updated': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting preferences for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve preferences'}), 500

@meme_bp.route('/user-meme-preferences/<int:user_id>', methods=['PUT'])
@cross_origin()
@require_auth()
@rate_limit(max_requests=20, window_seconds=60)
@validate_json_input([])  # No required fields, all are optional
def update_user_meme_preferences(user_id):
    """
    PUT /api/user-meme-preferences/<user_id>
    Updates user's meme preferences
    """
    try:
        # Verify user is updating their own preferences or is admin
        current_user_id = get_user_id()
        if current_user_id != user_id:
            return jsonify({'error': 'Unauthorized access'}), 403
        
        data = request.get_json()
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        # Check if user exists
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate input data
        if 'memes_enabled' in data and not isinstance(data['memes_enabled'], bool):
            return jsonify({'error': 'memes_enabled must be a boolean'}), 400
        
        if 'preferred_categories' in data:
            if not isinstance(data['preferred_categories'], list):
                return jsonify({'error': 'preferred_categories must be a list'}), 400
            
            valid_categories = [
                'monday_career', 'tuesday_health', 'wednesday_home', 
                'thursday_relationships', 'friday_entertainment', 
                'saturday_kids', 'sunday_faith'
            ]
            
            for category in data['preferred_categories']:
                if category not in valid_categories:
                    return jsonify({
                        'error': f'Invalid category: {category}. Must be one of: {", ".join(valid_categories)}'
                    }), 400
        
        if 'frequency_setting' in data:
            valid_frequencies = ['daily', 'weekly', 'disabled', 'custom']
            if data['frequency_setting'] not in valid_frequencies:
                return jsonify({
                    'error': f'Invalid frequency_setting. Must be one of: {", ".join(valid_frequencies)}'
                }), 400
        
        if 'custom_frequency_days' in data:
            if not isinstance(data['custom_frequency_days'], int) or data['custom_frequency_days'] < 1 or data['custom_frequency_days'] > 30:
                return jsonify({'error': 'custom_frequency_days must be an integer between 1 and 30'}), 400
        
        # Update preferences
        updated_preferences = meme_service.update_user_preferences(user_id, data)
        
        logger.info(f"Updated preferences for user {user_id}: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Preferences updated successfully',
            'preferences': {
                'memes_enabled': updated_preferences.memes_enabled,
                'preferred_categories': updated_preferences.preferred_categories_list,
                'frequency_setting': updated_preferences.frequency_setting,
                'custom_frequency_days': updated_preferences.custom_frequency_days,
                'last_meme_shown_at': updated_preferences.last_meme_shown_at.isoformat() if updated_preferences.last_meme_shown_at else None,
                'opt_out_reason': updated_preferences.opt_out_reason,
                'opt_out_date': updated_preferences.opt_out_date.isoformat() if updated_preferences.opt_out_date else None
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating preferences for user {user_id}: {str(e)}")
        return jsonify({'error': 'Failed to update preferences'}), 500

# Health check endpoint
@meme_bp.route('/meme-health', methods=['GET'])
@cross_origin()
def meme_health_check():
    """
    GET /api/meme-health
    Health check endpoint for meme service
    """
    try:
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        # Check if we can access the database
        from ..models.meme_models import Meme
        total_memes = db_session.query(Meme).count()
        
        return jsonify({
            'status': 'healthy',
            'service': 'meme-api',
            'database': 'connected',
            'total_memes': total_memes,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'meme-api',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Optional: Admin endpoints for meme management
@meme_bp.route('/admin/memes', methods=['GET'])
@cross_origin()
@require_auth()
@rate_limit(max_requests=30, window_seconds=60)
def get_all_memes():
    """
    GET /api/admin/memes
    Admin endpoint to get all memes (for management purposes)
    """
    try:
        # TODO: Add admin role check here
        user_id = get_user_id()
        
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        # Get query parameters
        category = request.args.get('category')
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 memes
        offset = int(request.args.get('offset', 0))
        
        # Get memes
        if category:
            memes = meme_service.get_active_memes_by_category(category, limit)
        else:
            memes = meme_service.get_all_active_memes(limit)
        
        # Apply offset
        memes = memes[offset:offset + limit]
        
        return jsonify({
            'success': True,
            'memes': [meme.to_dict() for meme in memes],
            'total_count': len(memes),
            'limit': limit,
            'offset': offset,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting all memes: {str(e)}")
        return jsonify({'error': 'Failed to retrieve memes'}), 500

@meme_bp.route('/admin/meme-analytics', methods=['GET'])
@cross_origin()
@require_auth()
@rate_limit(max_requests=20, window_seconds=60)
def get_meme_analytics():
    """
    GET /api/admin/meme-analytics
    Admin endpoint to get overall meme analytics
    """
    try:
        # TODO: Add admin role check here
        
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        analytics = meme_service.get_meme_analytics()
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting meme analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500
