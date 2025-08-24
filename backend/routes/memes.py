"""
Meme Splash Page API Routes
Handles meme display, user interactions, and preferences management.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from typing import Dict, Any
import json

from ..services.meme_service import MemeService
from ..models.meme_models import Meme, UserMemeHistory, UserMemePreferences
from ..database import get_db

memes_bp = Blueprint('memes', __name__, url_prefix='/api/memes')


@memes_bp.route('/daily', methods=['GET'])
@login_required
def get_daily_meme():
    """Get today's themed meme for the current user based on day of week"""
    try:
        db: Session = get_db()
        meme_service = MemeService(db)
        
        # Get today's themed meme for the user
        memes = meme_service.get_todays_meme_for_user(current_user.id, limit=1)
        
        if not memes:
            return jsonify({
                'success': False,
                'message': 'No memes available for you right now',
                'data': None
            }), 404
        
        meme = memes[0]
        
        # Get today's day and category for context
        from datetime import datetime
        today = datetime.utcnow()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_of_week = today.weekday()
        day_name = day_names[day_of_week]
        
        # Record the view
        meme_service.record_user_interaction(
            user_id=current_user.id,
            meme_id=meme.id,
            interaction_type='view',
            session_id=request.args.get('session_id'),
            source_page=request.args.get('source_page', 'daily_meme'),
            device_type=request.args.get('device_type'),
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': f'{day_name}\'s themed meme retrieved successfully',
            'data': {
                **meme.to_dict(),
                'day_of_week': day_name,
                'category_theme': meme.category
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting daily meme: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve daily meme',
            'error': str(e)
        }), 500


@memes_bp.route('/category/<category>', methods=['GET'])
@login_required
def get_memes_by_category(category: str):
    """Get memes by category"""
    try:
        db: Session = get_db()
        meme_service = MemeService(db)
        
        # Validate category
        valid_categories = ['monday_career', 'tuesday_health', 'wednesday_home', 'thursday_relationships', 'friday_entertainment', 'saturday_kids', 'sunday_faith']
        if category not in valid_categories:
            return jsonify({
                'success': False,
                'message': f'Invalid category. Must be one of: {", ".join(valid_categories)}'
            }), 400
        
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 memes
        memes = meme_service.get_active_memes_by_category(category, limit=limit)
        
        return jsonify({
            'success': True,
            'message': f'Memes for category "{category}" retrieved successfully',
            'data': {
                'category': category,
                'memes': [meme.to_dict() for meme in memes],
                'count': len(memes)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting memes by category: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve memes by category',
            'error': str(e)
        }), 500


@memes_bp.route('/<meme_id>/interact', methods=['POST'])
@login_required
def interact_with_meme(meme_id: str):
    """Record user interaction with a meme (like, share, skip, report)"""
    try:
        data = request.get_json()
        interaction_type = data.get('interaction_type', 'view')
        time_spent = data.get('time_spent_seconds', 0)
        
        # Validate interaction type
        valid_interactions = ['view', 'like', 'share', 'skip', 'report']
        if interaction_type not in valid_interactions:
            return jsonify({
                'success': False,
                'message': f'Invalid interaction type. Must be one of: {", ".join(valid_interactions)}'
            }), 400
        
        db: Session = get_db()
        meme_service = MemeService(db)
        
        # Verify meme exists
        meme = meme_service.get_meme_by_id(meme_id)
        if not meme:
            return jsonify({
                'success': False,
                'message': 'Meme not found'
            }), 404
        
        # Record the interaction
        history = meme_service.record_user_interaction(
            user_id=current_user.id,
            meme_id=meme_id,
            interaction_type=interaction_type,
            time_spent=time_spent,
            session_id=data.get('session_id'),
            source_page=data.get('source_page'),
            device_type=data.get('device_type'),
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'message': f'Interaction recorded successfully',
            'data': {
                'interaction_id': history.id,
                'interaction_type': interaction_type,
                'meme_id': meme_id,
                'updated_metrics': {
                    'view_count': meme.view_count,
                    'like_count': meme.like_count,
                    'share_count': meme.share_count,
                    'engagement_score': meme.engagement_score
                }
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error recording meme interaction: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to record interaction',
            'error': str(e)
        }), 500


@memes_bp.route('/preferences', methods=['GET'])
@login_required
def get_user_preferences():
    """Get user's meme preferences"""
    try:
        db: Session = get_db()
        meme_service = MemeService(db)
        
        prefs = meme_service.get_user_preferences(current_user.id)
        
        if not prefs:
            # Create default preferences
            prefs = meme_service.create_user_preferences(current_user.id, {
                'memes_enabled': True,
                'preferred_categories': ['monday_career', 'tuesday_health', 'wednesday_home', 'thursday_relationships', 'friday_entertainment', 'saturday_kids', 'sunday_faith'],
                'frequency_setting': 'daily'
            })
        
        return jsonify({
            'success': True,
            'message': 'User preferences retrieved successfully',
            'data': prefs.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user preferences: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve user preferences',
            'error': str(e)
        }), 500


@memes_bp.route('/preferences', methods=['PUT'])
@login_required
def update_user_preferences():
    """Update user's meme preferences"""
    try:
        data = request.get_json()
        
        # Validate data
        if 'memes_enabled' in data and not isinstance(data['memes_enabled'], bool):
            return jsonify({
                'success': False,
                'message': 'memes_enabled must be a boolean'
            }), 400
        
        if 'frequency_setting' in data:
            valid_frequencies = ['daily', 'weekly', 'disabled', 'custom']
            if data['frequency_setting'] not in valid_frequencies:
                return jsonify({
                    'success': False,
                    'message': f'frequency_setting must be one of: {", ".join(valid_frequencies)}'
                }), 400
        
        if 'preferred_categories' in data:
            valid_categories = ['monday_career', 'tuesday_health', 'wednesday_home', 'thursday_relationships', 'friday_entertainment', 'saturday_kids', 'sunday_faith']
            if not all(cat in valid_categories for cat in data['preferred_categories']):
                return jsonify({
                    'success': False,
                    'message': f'preferred_categories must contain only: {", ".join(valid_categories)}'
                }), 400
        
        db: Session = get_db()
        meme_service = MemeService(db)
        
        prefs = meme_service.update_user_preferences(current_user.id, data)
        
        return jsonify({
            'success': True,
            'message': 'User preferences updated successfully',
            'data': prefs.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error updating user preferences: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to update user preferences',
            'error': str(e)
        }), 500


@memes_bp.route('/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get user's meme interaction statistics"""
    try:
        db: Session = get_db()
        meme_service = MemeService(db)
        
        stats = meme_service.get_user_meme_stats(current_user.id)
        
        return jsonify({
            'success': True,
            'message': 'User stats retrieved successfully',
            'data': stats
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve user stats',
            'error': str(e)
        }), 500


@memes_bp.route('/analytics', methods=['GET'])
@login_required
def get_meme_analytics():
    """Get overall meme analytics (admin only)"""
    try:
        # Check if user is admin (you may need to implement this based on your auth system)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        db: Session = get_db()
        meme_service = MemeService(db)
        
        analytics = meme_service.get_meme_analytics()
        
        return jsonify({
            'success': True,
            'message': 'Meme analytics retrieved successfully',
            'data': analytics
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting meme analytics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve meme analytics',
            'error': str(e)
        }), 500


@memes_bp.route('/seed', methods=['POST'])
@login_required
def seed_sample_memes():
    """Seed the database with sample memes (admin only)"""
    try:
        # Check if user is admin
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        db: Session = get_db()
        meme_service = MemeService(db)
        
        meme_service.seed_sample_memes()
        
        return jsonify({
            'success': True,
            'message': 'Sample memes seeded successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error seeding sample memes: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to seed sample memes',
            'error': str(e)
        }), 500


@memes_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get available meme categories"""
    categories = [
        {
            'id': 'monday_career',
            'name': 'Monday - Career & Business',
            'description': 'Career news, business skills, professional development, and workplace financial wisdom'
        },
        {
            'id': 'tuesday_health',
            'name': 'Tuesday - Health & Wellness',
            'description': 'Health spending, wellness investments, medical savings, and fitness financial planning'
        },
        {
            'id': 'wednesday_home',
            'name': 'Wednesday - Home & Transportation',
            'description': 'Housing costs, home improvement, transportation expenses, and property investment'
        },
        {
            'id': 'thursday_relationships',
            'name': 'Thursday - Relationships & Family',
            'description': 'Family finances, relationship money talks, shared goals, and partnership budgeting'
        },
        {
            'id': 'friday_entertainment',
            'name': 'Friday - Entertainment & Fun',
            'description': 'Weekend planning, entertainment budgets, social spending, and leisure activities'
        },
        {
            'id': 'saturday_kids',
            'name': 'Saturday - Kids & Education',
            'description': 'Children\'s education, college savings, kids\' activities, and family financial education'
        },
        {
            'id': 'sunday_faith',
            'name': 'Sunday - Faith & Reflection',
            'description': 'Spiritual financial wisdom, gratitude, reflection, and faith-based money management'
        }
    ]
    
    return jsonify({
        'success': True,
        'message': 'Categories retrieved successfully',
        'data': categories
    }), 200


@memes_bp.route('/today', methods=['GET'])
def get_todays_category():
    """Get today's meme category and theme information"""
    from datetime import datetime
    
    today = datetime.utcnow()
    day_of_week = today.weekday()  # Monday = 0, Sunday = 6
    
    day_categories = {
        0: {
            'id': 'monday_career',
            'name': 'Monday - Career & Business',
            'description': 'Career news, business skills, professional development, and workplace financial wisdom',
            'day_name': 'Monday',
            'theme': 'Career & Business'
        },
        1: {
            'id': 'tuesday_health',
            'name': 'Tuesday - Health & Wellness',
            'description': 'Health spending, wellness investments, medical savings, and fitness financial planning',
            'day_name': 'Tuesday',
            'theme': 'Health & Wellness'
        },
        2: {
            'id': 'wednesday_home',
            'name': 'Wednesday - Home & Transportation',
            'description': 'Housing costs, home improvement, transportation expenses, and property investment',
            'day_name': 'Wednesday',
            'theme': 'Home & Transportation'
        },
        3: {
            'id': 'thursday_relationships',
            'name': 'Thursday - Relationships & Family',
            'description': 'Family finances, relationship money talks, shared goals, and partnership budgeting',
            'day_name': 'Thursday',
            'theme': 'Relationships & Family'
        },
        4: {
            'id': 'friday_entertainment',
            'name': 'Friday - Entertainment & Fun',
            'description': 'Weekend planning, entertainment budgets, social spending, and leisure activities',
            'day_name': 'Friday',
            'theme': 'Entertainment & Fun'
        },
        5: {
            'id': 'saturday_kids',
            'name': 'Saturday - Kids & Education',
            'description': 'Children\'s education, college savings, kids\' activities, and family financial education',
            'day_name': 'Saturday',
            'theme': 'Kids & Education'
        },
        6: {
            'id': 'sunday_faith',
            'name': 'Sunday - Faith & Reflection',
            'description': 'Spiritual financial wisdom, gratitude, reflection, and faith-based money management',
            'day_name': 'Sunday',
            'theme': 'Faith & Reflection'
        }
    }
    
    todays_info = day_categories.get(day_of_week, day_categories[0])
    
    return jsonify({
        'success': True,
        'message': f"Today is {todays_info['day_name']} - {todays_info['theme']}",
        'data': {
            **todays_info,
            'date': today.strftime('%Y-%m-%d'),
            'day_of_week_number': day_of_week
        }
    }), 200


@memes_bp.route('/opt-out', methods=['POST'])
@login_required
def opt_out_memes():
    """Streamlined opt-out endpoint for disabling daily memes"""
    try:
        data = request.get_json() or {}
        opt_out_reason = data.get('reason', 'user_requested')
        
        db: Session = get_db()
        meme_service = MemeService(db)
        
        # Update user preferences to disable memes
        prefs = meme_service.update_user_preferences(current_user.id, {
            'memes_enabled': False,
            'opt_out_reason': opt_out_reason
        })
        
        # Track opt-out analytics
        try:
            from ..services.analytics_service import AnalyticsService
            analytics_service = AnalyticsService(db)
            analytics_service.track_event(
                user_id=current_user.id,
                event_type='meme_opt_out',
                event_data={
                    'reason': opt_out_reason,
                    'source': data.get('source', 'splash_page'),
                    'user_agent': request.headers.get('User-Agent'),
                    'ip_address': request.remote_addr
                }
            )
        except Exception as analytics_error:
            # Log but don't fail the opt-out if analytics fails
            current_app.logger.warning(f"Analytics tracking failed for meme opt-out: {analytics_error}")
        
        return jsonify({
            'success': True,
            'message': 'Daily memes have been turned off. You can re-enable them anytime in Settings.',
            'data': {
                'memes_enabled': False,
                'opt_out_date': prefs.opt_out_date.isoformat() if prefs.opt_out_date else None,
                'redirect_url': '/dashboard'  # Direct redirect to dashboard
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error during meme opt-out: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to turn off daily memes. Please try again.',
            'error': str(e)
        }), 500


@memes_bp.route('/opt-in', methods=['POST'])
@login_required
def opt_in_memes():
    """Re-enable memes with optional category customization"""
    try:
        data = request.get_json() or {}
        preferred_categories = data.get('preferred_categories', [])
        
        db: Session = get_db()
        meme_service = MemeService(db)
        
        # Update user preferences to enable memes
        update_data = {
            'memes_enabled': True,
            'opt_out_reason': None,
            'opt_out_date': None
        }
        
        # Add category preferences if provided
        if preferred_categories:
            valid_categories = ['monday_career', 'tuesday_health', 'wednesday_home', 'thursday_relationships', 'friday_entertainment', 'saturday_kids', 'sunday_faith']
            if all(cat in valid_categories for cat in preferred_categories):
                update_data['preferred_categories'] = preferred_categories
        
        prefs = meme_service.update_user_preferences(current_user.id, update_data)
        
        # Track opt-in analytics
        try:
            from ..services.analytics_service import AnalyticsService
            analytics_service = AnalyticsService(db)
            analytics_service.track_event(
                user_id=current_user.id,
                event_type='meme_opt_in',
                event_data={
                    'source': data.get('source', 'settings'),
                    'categories_selected': preferred_categories,
                    'user_agent': request.headers.get('User-Agent'),
                    'ip_address': request.remote_addr
                }
            )
        except Exception as analytics_error:
            # Log but don't fail the opt-in if analytics fails
            current_app.logger.warning(f"Analytics tracking failed for meme opt-in: {analytics_error}")
        
        return jsonify({
            'success': True,
            'message': 'Daily memes have been re-enabled successfully!',
            'data': prefs.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error during meme opt-in: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to re-enable daily memes. Please try again.',
            'error': str(e)
        }), 500


@memes_bp.route('/preview', methods=['GET'])
@login_required
def preview_memes():
    """Get sample memes for preview (used in re-enable flow)"""
    try:
        db: Session = get_db()
        meme_service = MemeService(db)
        
        # Get one meme from each category for preview
        categories = ['monday_career', 'tuesday_health', 'wednesday_home', 'thursday_relationships', 'friday_entertainment', 'saturday_kids', 'sunday_faith']
        preview_memes = []
        
        for category in categories:
            memes = meme_service.get_active_memes_by_category(category, limit=1)
            if memes:
                preview_memes.append(memes[0].to_dict())
        
        return jsonify({
            'success': True,
            'message': 'Preview memes retrieved successfully',
            'data': {
                'preview_memes': preview_memes,
                'categories': categories
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting preview memes: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve preview memes',
            'error': str(e)
        }), 500
