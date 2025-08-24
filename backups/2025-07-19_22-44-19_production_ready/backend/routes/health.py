"""
Health-related routes for the Mingus application
"""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from backend.models import UserHealthCheckin, User
from backend.middleware.auth import require_auth, get_current_user_id
from functools import wraps
import traceback
import logging

logger = logging.getLogger(__name__)

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api/health')

# Custom exception classes
class ValidationError(Exception):
    pass

class AuthenticationError(Exception):
    pass

class DatabaseError(Exception):
    pass

class PermissionError(Exception):
    pass

def handle_api_errors(f):
    """Decorator to handle API errors consistently"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'type': 'validation_error'
            }), 400
        except AuthenticationError as e:
            logger.warning(f"Auth error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'type': 'auth_error'
            }), 401
        except PermissionError as e:
            logger.warning(f"Permission error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': 'Insufficient permissions',
                'type': 'permission_error'
            }), 403
        except DatabaseError as e:
            logger.error(f"Database error in {f.__name__}: {e}")
            return jsonify({
                'success': False,
                'error': 'Database operation failed',
                'type': 'database_error'
            }), 500
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'type': 'server_error'
            }), 500
    return decorated_function

@health_bp.route('/demo', methods=['GET'])
def demo_checkin_form():
    """
    Demo health check-in form (no authentication required for testing)
    """
    try:
        return render_template('health_checkin.html', last_checkin=None)
    except Exception as e:
        logger.error(f"Error rendering demo health check-in form: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/checkin', methods=['GET'])
@require_auth
def checkin_form():
    """
    Render the health check-in form
    """
    try:
        # Get the current user from session
        user_id = request.session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get the last check-in for this user
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return jsonify({'error': 'Database not configured'}), 500
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            last_checkin = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .first()
            
            return render_template('health_checkin.html', 
                                last_checkin=last_checkin.checkin_date if last_checkin else None)
    
    except Exception as e:
        logger.error(f"Error rendering health check-in form: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/checkin', methods=['POST'])
@require_auth
def submit_health_checkin():
    """Submit health check-in data"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Track performance metrics
        from backend.monitoring.performance_monitoring import performance_monitor
        from backend.optimization.cache_manager import cache_manager
        
        with performance_monitor.api_timer('/api/health/checkin', 'POST', user_id):
            # Cache user health data
            cache_key = f"health_data_{user_id}"
            cache_manager.set(cache_key, data, ttl=3600)
            
            # Submit health data
            result = current_app.health_service.submit_health_checkin(user_id, data)
            
            # Track user engagement
            from backend.analytics.business_intelligence import business_intelligence
            business_intelligence.track_user_engagement(
                user_id, 
                session.get('session_id', 'unknown'),
                'health_checkin',
                usage_time=1.0
            )
        
        return jsonify({
            'success': True,
            'message': 'Health check-in submitted successfully',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Health check-in error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/checkin/latest', methods=['GET'])
@require_auth
def get_latest_checkin():
    """
    Get user's most recent check-in data
    """
    try:
        # Get the current user from session
        user_id = request.session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get latest check-in from database
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return jsonify({'error': 'Database not configured'}), 500
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            latest_checkin = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .first()
            
            if not latest_checkin:
                return jsonify({
                    'message': 'No check-ins found',
                    'checkin': None
                }), 200
            
            # Convert to JSON-serializable format
            checkin_data = {
                'id': latest_checkin.id,
                'checkin_date': latest_checkin.checkin_date.isoformat(),
                'physical_activity_minutes': latest_checkin.physical_activity_minutes,
                'physical_activity_level': latest_checkin.physical_activity_level,
                'relationships_rating': latest_checkin.relationships_rating,
                'relationships_notes': latest_checkin.relationships_notes,
                'mindfulness_minutes': latest_checkin.mindfulness_minutes,
                'mindfulness_type': latest_checkin.mindfulness_type,
                'stress_level': latest_checkin.stress_level,
                'energy_level': latest_checkin.energy_level,
                'mood_rating': latest_checkin.mood_rating,
                'created_at': latest_checkin.created_at.isoformat()
            }
            
            return jsonify({
                'checkin': checkin_data
            }), 200
    
    except Exception as e:
        logger.error(f"Error fetching latest check-in: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/checkin/history', methods=['GET'])
@require_auth
def get_checkin_history():
    """
    Get user's check-in history (last 12 weeks)
    """
    try:
        # Get the current user from session
        user_id = request.session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get query parameters
        weeks = request.args.get('weeks', 12, type=int)
        
        # Validate parameters
        if weeks < 1 or weeks > 52:
            return jsonify({'error': 'Weeks must be between 1 and 52'}), 400
        
        # Calculate date range (last N weeks)
        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Get check-ins from database
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return jsonify({'error': 'Database not configured'}), 500
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            checkins = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .filter(UserHealthCheckin.checkin_date >= start_date)\
                .filter(UserHealthCheckin.checkin_date <= end_date)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .all()
            
            # Convert to JSON-serializable format
            checkin_data = []
            for checkin in checkins:
                checkin_data.append({
                    'id': checkin.id,
                    'checkin_date': checkin.checkin_date.isoformat(),
                    'physical_activity_minutes': checkin.physical_activity_minutes,
                    'physical_activity_level': checkin.physical_activity_level,
                    'relationships_rating': checkin.relationships_rating,
                    'relationships_notes': checkin.relationships_notes,
                    'mindfulness_minutes': checkin.mindfulness_minutes,
                    'mindfulness_type': checkin.mindfulness_type,
                    'stress_level': checkin.stress_level,
                    'energy_level': checkin.energy_level,
                    'mood_rating': checkin.mood_rating,
                    'created_at': checkin.created_at.isoformat()
                })
            
            return jsonify({
                'checkins': checkin_data,
                'total': len(checkin_data),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'weeks': weeks
                }
            }), 200
    
    except Exception as e:
        logger.error(f"Error fetching check-in history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/status', methods=['GET'])
@require_auth
def get_checkin_status():
    """
    Check if user has completed this week's check-in
    """
    try:
        # Get the current user from session
        user_id = request.session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Calculate current week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday of current week
        week_end = week_start + timedelta(days=6)  # Sunday of current week
        
        # Check for existing check-in this week
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return jsonify({'error': 'Database not configured'}), 500
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            this_week_checkin = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .filter(UserHealthCheckin.checkin_date >= week_start)\
                .filter(UserHealthCheckin.checkin_date <= week_end)\
                .first()
            
            # Get last check-in for additional context
            last_checkin = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .first()
            
            status_data = {
                'current_week': {
                    'start_date': week_start.isoformat(),
                    'end_date': week_end.isoformat(),
                    'completed': this_week_checkin is not None
                },
                'last_checkin': None,
                'streak_weeks': 0
            }
            
            if this_week_checkin:
                status_data['current_week']['checkin_date'] = this_week_checkin.checkin_date.isoformat()
            
            if last_checkin:
                status_data['last_checkin'] = {
                    'date': last_checkin.checkin_date.isoformat(),
                    'days_ago': (today - last_checkin.checkin_date).days
                }
            
            # Calculate streak (consecutive weeks with check-ins)
            if last_checkin:
                streak_count = 0
                current_date = last_checkin.checkin_date
                
                while True:
                    week_start_check = current_date - timedelta(days=current_date.weekday())
                    week_end_check = week_start_check + timedelta(days=6)
                    
                    # Check if there's a check-in in this week
                    week_checkin = db.query(UserHealthCheckin)\
                        .filter(UserHealthCheckin.user_id == user_id)\
                        .filter(UserHealthCheckin.checkin_date >= week_start_check)\
                        .filter(UserHealthCheckin.checkin_date <= week_end_check)\
                        .first()
                    
                    if week_checkin:
                        streak_count += 1
                        current_date = week_start_check - timedelta(days=1)  # Previous week
                    else:
                        break
                
                status_data['streak_weeks'] = streak_count
            
            return jsonify(status_data), 200
    
    except Exception as e:
        logger.error(f"Error checking check-in status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/checkins', methods=['GET'])
@require_auth
def get_checkins():
    """
    Get user's health check-ins (paginated)
    """
    try:
        # Get the current user from session
        user_id = request.session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate parameters
        if limit < 1 or limit > 100:
            return jsonify({'error': 'Limit must be between 1 and 100'}), 400
        
        if offset < 0:
            return jsonify({'error': 'Offset must be non-negative'}), 400
        
        # Get check-ins from database
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return jsonify({'error': 'Database not configured'}), 500
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            checkins = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .offset(offset)\
                .limit(limit)\
                .all()
            
            # Convert to JSON-serializable format
            checkin_data = []
            for checkin in checkins:
                checkin_data.append({
                    'id': checkin.id,
                    'checkin_date': checkin.checkin_date.isoformat(),
                    'physical_activity_minutes': checkin.physical_activity_minutes,
                    'physical_activity_level': checkin.physical_activity_level,
                    'relationships_rating': checkin.relationships_rating,
                    'relationships_notes': checkin.relationships_notes,
                    'mindfulness_minutes': checkin.mindfulness_minutes,
                    'mindfulness_type': checkin.mindfulness_type,
                    'stress_level': checkin.stress_level,
                    'energy_level': checkin.energy_level,
                    'mood_rating': checkin.mood_rating,
                    'created_at': checkin.created_at.isoformat()
                })
            
            return jsonify({
                'checkins': checkin_data,
                'total': len(checkin_data),
                'limit': limit,
                'offset': offset
            }), 200
    
    except Exception as e:
        logger.error(f"Error fetching health check-ins: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/stats', methods=['GET'])
@require_auth
def get_health_stats():
    """
    Get user's health statistics
    """
    try:
        # Get the current user from session
        user_id = request.session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        
        if days < 1 or days > 365:
            return jsonify({'error': 'Days must be between 1 and 365'}), 400
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get check-ins from database
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return jsonify({'error': 'Database not configured'}), 500
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            checkins = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .filter(UserHealthCheckin.checkin_date >= start_date)\
                .filter(UserHealthCheckin.checkin_date <= end_date)\
                .all()
            
            if not checkins:
                return jsonify({
                    'message': 'No check-ins found for the specified period',
                    'stats': {}
                }), 200
            
            # Calculate statistics
            total_checkins = len(checkins)
            
            # Average ratings
            avg_relationships = sum(c.relationships_rating for c in checkins) / total_checkins
            avg_stress = sum(c.stress_level for c in checkins) / total_checkins
            avg_energy = sum(c.energy_level for c in checkins) / total_checkins
            avg_mood = sum(c.mood_rating for c in checkins) / total_checkins
            
            # Activity statistics
            total_activity_minutes = sum(c.physical_activity_minutes or 0 for c in checkins)
            avg_activity_minutes = total_activity_minutes / total_checkins
            
            total_mindfulness_minutes = sum(c.mindfulness_minutes or 0 for c in checkins)
            avg_mindfulness_minutes = total_mindfulness_minutes / total_checkins
            
            # Activity level distribution
            activity_levels = {}
            for checkin in checkins:
                if checkin.physical_activity_level:
                    activity_levels[checkin.physical_activity_level] = \
                        activity_levels.get(checkin.physical_activity_level, 0) + 1
            
            # Mindfulness type distribution
            mindfulness_types = {}
            for checkin in checkins:
                if checkin.mindfulness_type:
                    mindfulness_types[checkin.mindfulness_type] = \
                        mindfulness_types.get(checkin.mindfulness_type, 0) + 1
            
            stats = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'total_checkins': total_checkins,
                'averages': {
                    'relationships_rating': round(avg_relationships, 1),
                    'stress_level': round(avg_stress, 1),
                    'energy_level': round(avg_energy, 1),
                    'mood_rating': round(avg_mood, 1),
                    'physical_activity_minutes': round(avg_activity_minutes, 1),
                    'mindfulness_minutes': round(avg_mindfulness_minutes, 1)
                },
                'totals': {
                    'physical_activity_minutes': total_activity_minutes,
                    'mindfulness_minutes': total_mindfulness_minutes
                },
                'distributions': {
                    'activity_levels': activity_levels,
                    'mindfulness_types': mindfulness_types
                }
            }
            
            return jsonify({'stats': stats}), 200
    
    except Exception as e:
        logger.error(f"Error calculating health stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# --- Health Onboarding Routes ---

@health_bp.route('/onboarding', methods=['GET'])
def health_onboarding():
    """Render the health-finance onboarding flow"""
    return render_template('health_onboarding.html')

@health_bp.route('/onboarding/complete', methods=['POST'])
@require_auth
@handle_api_errors
def complete_health_onboarding():
    """Handle onboarding completion and save user preferences"""
    user_id = get_current_user_id()
    if not user_id:
        raise AuthenticationError("User not authenticated")
    
    data = request.get_json()
    
    # Validate input
    if not data:
        raise ValidationError("Request body is required")
    
    if 'goals' not in data:
        raise ValidationError("Goals are required")
    
    # Prevent duplicate completion
    if user_completed_health_onboarding(user_id):
        return jsonify({
            'success': True,
            'message': 'Onboarding already completed',
            'redirect': '/api/health/dashboard'
        })
    
    # Save onboarding data
    save_onboarding_completion(user_id, data)
    
    return jsonify({
        'success': True,
        'message': 'Onboarding completed successfully',
        'redirect': '/api/health/dashboard'
    })

@health_bp.route('/onboarding/status', methods=['GET'])
def onboarding_status():
    """Check if user has completed health onboarding"""
    # This would check against user's profile or onboarding_progress table
    # For now, return mock status
    return jsonify({
        'completed': False,
        'current_step': 1,
        'total_steps': 4
    })

@health_bp.route('/summary', methods=['GET'])
@require_auth
def get_health_summary():
    """
    Get a comprehensive health summary for the current user
    """
    try:
        # Get the current user from session
        user_id = request.session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        # Get database session
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return jsonify({'error': 'Database not configured'}), 500
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            # Get user's check-ins from the last 30 days
            thirty_days_ago = date.today() - timedelta(days=30)
            
            recent_checkins = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .filter(UserHealthCheckin.checkin_date >= thirty_days_ago)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .all()
            
            if not recent_checkins:
                return jsonify({
                    'message': 'No health data available',
                    'summary': {
                        'total_checkins': 0,
                        'last_checkin': None,
                        'average_ratings': {},
                        'trends': {}
                    }
                }), 200
            
            # Calculate summary statistics
            total_checkins = len(recent_checkins)
            latest_checkin = recent_checkins[0]
            
            # Calculate average ratings
            avg_relationships = sum(c.relationships_rating for c in recent_checkins) / total_checkins
            avg_stress = sum(c.stress_level for c in recent_checkins) / total_checkins
            avg_energy = sum(c.energy_level for c in recent_checkins) / total_checkins
            avg_mood = sum(c.mood_rating for c in recent_checkins) / total_checkins
            
            # Calculate total activity minutes
            total_activity = sum(c.physical_activity_minutes or 0 for c in recent_checkins)
            total_mindfulness = sum(c.mindfulness_minutes or 0 for c in recent_checkins)
            
            # Determine trends (comparing first half vs second half of the period)
            mid_point = len(recent_checkins) // 2
            if mid_point > 0:
                first_half = recent_checkins[mid_point:]
                second_half = recent_checkins[:mid_point]
                
                first_avg_mood = sum(c.mood_rating for c in first_half) / len(first_half)
                second_avg_mood = sum(c.mood_rating for c in second_half) / len(second_half)
                
                mood_trend = 'improving' if second_avg_mood > first_avg_mood else 'declining' if second_avg_mood < first_avg_mood else 'stable'
            else:
                mood_trend = 'insufficient_data'
            
            # Generate insights
            insights = []
            if avg_stress > 7:
                insights.append("Your stress levels are elevated. Consider mindfulness practices.")
            if avg_energy < 5:
                insights.append("Your energy levels are low. Focus on sleep and physical activity.")
            if total_activity < 150:  # Less than 2.5 hours per week
                insights.append("You could benefit from more physical activity.")
            if total_mindfulness < 60:  # Less than 1 hour per week
                insights.append("Consider adding more mindfulness practices to your routine.")
            
            summary = {
                'total_checkins': total_checkins,
                'last_checkin': latest_checkin.checkin_date.isoformat(),
                'period_days': 30,
                'average_ratings': {
                    'relationships': round(avg_relationships, 1),
                    'stress': round(avg_stress, 1),
                    'energy': round(avg_energy, 1),
                    'mood': round(avg_mood, 1)
                },
                'total_activity': {
                    'physical_minutes': total_activity,
                    'mindfulness_minutes': total_mindfulness
                },
                'trends': {
                    'mood': mood_trend
                },
                'insights': insights,
                'recommendations': [
                    "Continue tracking your health metrics regularly",
                    "Aim for at least 150 minutes of physical activity per week",
                    "Practice mindfulness for at least 10 minutes daily"
                ]
            }
            
            return jsonify({
                'message': 'Health summary retrieved successfully',
                'summary': summary
            }), 200
    
    except Exception as e:
        logger.error(f"Error getting health summary: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/dashboard', methods=['GET'])
@require_auth
def health_dashboard():
    """Health dashboard page after onboarding completion"""
    try:
        user_id = get_current_user_id()
        
        # Check if user completed onboarding
        if not user_completed_health_onboarding(user_id):
            return redirect('/api/health/onboarding')
        
        # Get user's health data
        health_data = get_user_health_summary(user_id)
        goals = get_user_health_goals(user_id)
        
        return render_template('health_dashboard.html', 
                             health_data=health_data,
                             goals=goals)
    except Exception as e:
        logger.error(f"Error in health dashboard: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/main_app', methods=['GET'])
@require_auth
def health_main_app():
    """Main health application interface"""
    try:
        user_id = get_current_user_id()
        
        # Redirect to onboarding if not completed
        if not user_completed_health_onboarding(user_id):
            return redirect('/api/health/onboarding')
        
        # Get comprehensive health data
        user_profile = get_user_health_profile(user_id)
        recent_checkins = get_recent_health_checkins(user_id)
        insights = get_health_finance_insights(user_id)
        
        return render_template('health_main_app.html',
                             profile=user_profile,
                             checkins=recent_checkins,
                             insights=insights)
    except Exception as e:
        logger.error(f"Error in health main app: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@health_bp.route('/api/checkin', methods=['POST'])
@require_auth
def health_checkin():
    """Submit a health check-in"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sleep_hours', 'exercise_minutes', 'stress_level', 'energy_level']
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required health metrics'
            }), 400
        
        # Save health check-in
        checkin_id = save_health_checkin(user_id, data)
        
        # Generate insights if enough data
        insights = generate_health_insights(user_id)
        
        return jsonify({
            'success': True,
            'checkin_id': checkin_id,
            'insights': insights
        })
        
    except Exception as e:
        logger.error(f"Error in health checkin: {e}")
        return jsonify({'error': 'Failed to save health check-in'}), 500

# Helper functions
def user_completed_health_onboarding(user_id):
    """Check if user has completed health onboarding"""
    try:
        # Query your database for onboarding completion
        # For now, return True as placeholder
        # This should check against your onboarding_progress table
        return True
    except Exception as e:
        logger.error(f"Error checking onboarding completion: {e}")
        return False

def get_user_health_summary(user_id):
    """Get user's health data summary"""
    try:
        # Get database session
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return {}
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            # Get total check-ins
            total_checkins = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .count()
            
            # Get recent check-ins for averages
            recent_checkins = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .limit(10)\
                .all()
            
            if not recent_checkins:
                return {
                    'total_checkins': 0,
                    'avg_sleep': 0,
                    'avg_exercise': 0,
                    'current_streak': 0
                }
            
            # Calculate averages
            avg_sleep = sum(c.sleep_hours or 0 for c in recent_checkins) / len(recent_checkins)
            avg_exercise = sum(c.physical_activity_minutes or 0 for c in recent_checkins) / len(recent_checkins)
            
            # Calculate current streak (consecutive weeks with check-ins)
            current_streak = 0
            current_date = date.today()
            
            for i in range(52):  # Check up to 52 weeks back
                week_start = current_date - timedelta(days=current_date.weekday() + (i * 7))
                week_end = week_start + timedelta(days=6)
                
                checkin_in_week = db.query(UserHealthCheckin)\
                    .filter(UserHealthCheckin.user_id == user_id)\
                    .filter(UserHealthCheckin.checkin_date >= week_start)\
                    .filter(UserHealthCheckin.checkin_date <= week_end)\
                    .first()
                
                if checkin_in_week:
                    current_streak += 1
                else:
                    break
            
            return {
                'total_checkins': total_checkins,
                'avg_sleep': round(avg_sleep, 1),
                'avg_exercise': round(avg_exercise, 1),
                'current_streak': current_streak
            }
    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        return {
            'total_checkins': 0,
            'avg_sleep': 0,
            'avg_exercise': 0,
            'current_streak': 0
        }

def get_user_health_goals(user_id):
    """Get user's health goals from onboarding"""
    try:
        # This should query your onboarding_responses or user_profile table
        # For now, return empty list as placeholder
        return []
    except Exception as e:
        logger.error(f"Error getting health goals: {e}")
        return []

def get_user_health_profile(user_id):
    """Get comprehensive user health profile"""
    try:
        # This should query your user profile and health data
        # For now, return empty dict as placeholder
        return {}
    except Exception as e:
        logger.error(f"Error getting health profile: {e}")
        return {}

def get_recent_health_checkins(user_id):
    """Get recent health check-ins"""
    try:
        # Get database session
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return []
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            recent_checkins = db.query(UserHealthCheckin)\
                .filter(UserHealthCheckin.user_id == user_id)\
                .order_by(UserHealthCheckin.checkin_date.desc())\
                .limit(10)\
                .all()
            
            return [
                {
                    'id': c.id,
                    'date': c.checkin_date.isoformat(),
                    'stress_level': c.stress_level,
                    'energy_level': c.energy_level,
                    'mood_rating': c.mood_rating,
                    'physical_activity_minutes': c.physical_activity_minutes,
                    'mindfulness_minutes': c.mindfulness_minutes
                }
                for c in recent_checkins
            ]
    except Exception as e:
        logger.error(f"Error getting recent check-ins: {e}")
        return []

def get_health_finance_insights(user_id):
    """Get health-finance correlation insights"""
    try:
        # This should analyze health data and correlate with financial data
        # For now, return empty list as placeholder
        return []
    except Exception as e:
        logger.error(f"Error getting health-finance insights: {e}")
        return []

def save_health_checkin(user_id, data):
    """Save health check-in to database"""
    try:
        # Get database session
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            return None
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            # Create new check-in record
            checkin = UserHealthCheckin(
                user_id=user_id,
                checkin_date=date.today(),
                sleep_hours=data.get('sleep_hours'),
                physical_activity_minutes=data.get('exercise_minutes'),
                stress_level=data.get('stress_level'),
                energy_level=data.get('energy_level'),
                mood_rating=data.get('mood_rating', 5),
                relationships_rating=data.get('relationships_rating', 5),
                mindfulness_minutes=data.get('mindfulness_minutes', 0)
            )
            
            db.add(checkin)
            db.commit()
            
            return checkin.id
    except Exception as e:
        logger.error(f"Error saving health check-in: {e}")
        return None

def generate_health_insights(user_id):
    """Generate insights based on health data"""
    try:
        # This should analyze health data and generate personalized insights
        # For now, return empty list as placeholder
        return []
    except Exception as e:
        logger.error(f"Error generating health insights: {e}")
        return []

def save_onboarding_completion(user_id, data):
    """Save onboarding completion data to database"""
    try:
        # Get database session
        engine = current_app.config.get('DATABASE_ENGINE')
        if not engine:
            raise DatabaseError("Database not configured")
        
        SessionLocal = current_app.config.get('DATABASE_SESSION')
        with SessionLocal() as db:
            # Save goals and preferences to user profile or onboarding table
            # This is a placeholder - implement based on your database schema
            
            # For now, just log the completion
            logger.info(f"Onboarding completed for user {user_id} with goals: {data.get('goals', [])}")
            
            # You would typically save to a table like:
            # - user_onboarding_progress
            # - user_health_preferences
            # - user_goals
            
            return True
    except Exception as e:
        logger.error(f"Error saving onboarding completion: {e}")
        raise DatabaseError(f"Failed to save onboarding data: {str(e)}")
