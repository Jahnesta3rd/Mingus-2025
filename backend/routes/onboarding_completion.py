from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional

from backend.models.user import User
from backend.models.user_goals import UserGoals
from backend.models.user_preferences import UserPreferences
from backend.models.reminder_schedule import ReminderSchedule
from backend.database import get_db_session
from backend.services.health_reminder_service import HealthReminderService
from backend.services.email_service import EmailService

logger = logging.getLogger(__name__)

onboarding_completion_bp = Blueprint('onboarding_completion', __name__)

@onboarding_completion_bp.route('/page', methods=['GET'])
@login_required
def onboarding_completion_page():
    """Serve the onboarding completion page."""
    return render_template('onboarding_completion.html')

@onboarding_completion_bp.route('/data/<user_id>', methods=['GET'])
@login_required
def get_completion_data(user_id: str):
    """Get completion data for onboarding celebration screen."""
    try:
        # Verify user access
        if str(current_user.id) != user_id:
            return jsonify({'error': 'Unauthorized access'}), 403

        # Get user data
        db_session = get_db_session()
        user = db_session.query(User).filter(User.id == current_user.id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get goals count
        goals_count = db_session.query(UserGoals).filter(
            UserGoals.user_id == current_user.id
        ).count()

        # Calculate profile completion percentage
        profile_fields = ['name', 'email', 'phone', 'date_of_birth', 'employment_status']
        completed_fields = sum(1 for field in profile_fields if getattr(user, field, None))
        profile_completion = int((completed_fields / len(profile_fields)) * 100)

        # Get community stats (mock data for now)
        community_stats = {
            'total_members': 15420,
            'active_this_week': 8234,
            'average_savings': 247
        }

        # Check if mobile app is available
        mobile_app_available = True  # This could be dynamic based on platform

        # Get first check-in date if scheduled
        first_checkin = db_session.query(ReminderSchedule).filter(
            ReminderSchedule.user_id == current_user.id,
            ReminderSchedule.reminder_type == 'first_checkin'
        ).first()

        completion_data = {
            'user_name': user.name or 'User',
            'goals_count': goals_count,
            'profile_completion': profile_completion,
            'first_checkin_date': first_checkin.scheduled_date.isoformat() if first_checkin else None,
            'mobile_app_available': mobile_app_available,
            'community_stats': community_stats
        }

        return jsonify(completion_data)

    except Exception as e:
        logger.error(f"Error getting completion data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_completion_bp.route('/schedule-checkin', methods=['POST'])
@login_required
def schedule_first_checkin():
    """Schedule the user's first weekly check-in reminder."""
    try:
        db_session = get_db_session()
        data = request.get_json()
        user_id = data.get('user_id')
        preferences = data.get('preferences', {})

        # Verify user access
        if str(current_user.id) != str(user_id):
            return jsonify({'error': 'Unauthorized access'}), 403

        # Calculate first check-in date based on preferences
        frequency = preferences.get('frequency', 'weekly')
        day = preferences.get('day', 'wednesday')
        time = preferences.get('time', '10:00')

        # Map day names to numbers (0=Monday, 6=Sunday)
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        target_day = day_map.get(day.lower(), 2)  # Default to Wednesday

        # Calculate next occurrence of the target day
        today = datetime.now()
        days_ahead = target_day - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        next_checkin_date = today + timedelta(days=days_ahead)

        # Set the time
        hour, minute = map(int, time.split(':'))
        next_checkin_date = next_checkin_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Create or update reminder schedule
        existing_schedule = db_session.query(ReminderSchedule).filter(
            ReminderSchedule.user_id == current_user.id,
            ReminderSchedule.reminder_type == 'first_checkin'
        ).first()

        if existing_schedule:
            existing_schedule.scheduled_date = next_checkin_date
            existing_schedule.frequency = frequency
            existing_schedule.preferences = preferences
        else:
            new_schedule = ReminderSchedule(
                user_id=current_user.id,
                reminder_type='first_checkin',
                scheduled_date=next_checkin_date,
                frequency=frequency,
                preferences=preferences,
                enabled=preferences.get('enabled', True)
            )
            db_session.add(new_schedule)

        # Save user preferences
        user_prefs = db_session.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()

        if user_prefs:
            user_prefs.reminder_preferences = preferences
        else:
            new_prefs = UserPreferences(
                user_id=current_user.id,
                reminder_preferences=preferences
            )
            db_session.add(new_prefs)

        db_session.commit()

        # Send confirmation email if enabled
        if preferences.get('email', True):
            try:
                email_service = EmailService()
                email_service.send_checkin_confirmation(
                    user_email=current_user.email,
                    user_name=current_user.name,
                    scheduled_date=next_checkin_date,
                    frequency=frequency
                )
            except Exception as e:
                logger.error(f"Failed to send confirmation email: {e}")

        return jsonify({
            'success': True,
            'scheduled_date': next_checkin_date.isoformat(),
            'message': 'First check-in scheduled successfully'
        })

    except Exception as e:
        logger.error(f"Error scheduling first check-in: {e}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_completion_bp.route('/preferences', methods=['POST'])
@login_required
def save_engagement_preferences():
    """Save user engagement preferences."""
    try:
        db_session = get_db_session()
        data = request.get_json()
        user_id = data.get('user_id')
        preferences = data.get('preferences', {})

        # Verify user access
        if str(current_user.id) != str(user_id):
            return jsonify({'error': 'Unauthorized access'}), 403

        # Save or update user preferences
        user_prefs = db_session.query(UserPreferences).filter(
            UserPreferences.user_id == current_user.id
        ).first()

        if user_prefs:
            user_prefs.reminder_preferences = preferences
            user_prefs.updated_at = datetime.utcnow()
        else:
            new_prefs = UserPreferences(
                user_id=current_user.id,
                reminder_preferences=preferences
            )
            db_session.add(new_prefs)

        db_session.commit()

        return jsonify({
            'success': True,
            'message': 'Preferences saved successfully'
        })

    except Exception as e:
        logger.error(f"Error saving preferences: {e}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_completion_bp.route('/complete', methods=['POST'])
@login_required
def mark_onboarding_complete():
    """Mark onboarding as complete and trigger welcome sequence."""
    try:
        db_session = get_db_session()
        data = request.get_json()
        user_id = data.get('user_id')
        completed_at = data.get('completed_at')

        # Verify user access
        if str(current_user.id) != str(user_id):
            return jsonify({'error': 'Unauthorized access'}), 403

        # Update user onboarding status
        user = db_session.query(User).filter(User.id == current_user.id).first()
        if user:
            user.onboarding_completed = True
            user.onboarding_completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            user.updated_at = datetime.utcnow()

        db_session.commit()

        # Send welcome email
        try:
            email_service = EmailService()
            email_service.send_welcome_email(
                user_email=current_user.email,
                user_name=current_user.name
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")

        # Create first achievement
        try:
            from backend.models.user_achievements import UserAchievements
            first_achievement = UserAchievements(
                user_id=current_user.id,
                achievement_type='onboarding_complete',
                title='Welcome to Mingus!',
                description='You\'ve successfully completed your onboarding setup',
                points_awarded=100
            )
            db_session.add(first_achievement)
            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to create first achievement: {e}")

        return jsonify({
            'success': True,
            'message': 'Onboarding marked as complete'
        })

    except Exception as e:
        logger.error(f"Error marking onboarding complete: {e}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_completion_bp.route('/mobile-app', methods=['GET'])
@login_required
def get_mobile_app_info():
    """Get mobile app download information."""
    try:
        # Detect user platform
        user_agent = request.headers.get('User-Agent', '').lower()
        
        mobile_app_info = {
            'ios_url': 'https://apps.apple.com/app/mingus-financial-wellness',
            'android_url': 'https://play.google.com/store/apps/details?id=com.mingus.app',
            'qr_code_url': '/static/images/mobile-app-qr.png',
            'available': True,
            'platform': 'web'
        }

        if 'iphone' in user_agent or 'ipad' in user_agent:
            mobile_app_info['platform'] = 'ios'
        elif 'android' in user_agent:
            mobile_app_info['platform'] = 'android'

        return jsonify(mobile_app_info)

    except Exception as e:
        logger.error(f"Error getting mobile app info: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_completion_bp.route('/community-stats', methods=['GET'])
@login_required
def get_community_stats():
    """Get community statistics for engagement motivation."""
    try:
        db_session = get_db_session()
        # Get real community stats from database
        total_users = db_session.query(User).count()
        active_users = db_session.query(User).filter(
            User.last_login >= datetime.utcnow() - timedelta(days=7)
        ).count()

        # Calculate average savings (mock data for now)
        average_savings = 247

        # Get new members today
        new_members_today = db_session.query(User).filter(
            User.created_at >= datetime.utcnow().date()
        ).count()

        community_stats = {
            'total_members': total_users,
            'active_this_week': active_users,
            'average_savings': average_savings,
            'new_members_today': new_members_today,
            'top_achievement': 'Emergency fund goal reached by 73% of members this month'
        }

        return jsonify(community_stats)

    except Exception as e:
        logger.error(f"Error getting community stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_completion_bp.route('/welcome-email', methods=['POST'])
@login_required
def send_welcome_email():
    """Send welcome email to new user."""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        # Verify user access
        if str(current_user.id) != str(user_id):
            return jsonify({'error': 'Unauthorized access'}), 403

        # Send welcome email
        email_service = EmailService()
        success = email_service.send_welcome_email(
            user_email=current_user.email,
            user_name=current_user.name
        )

        return jsonify({
            'success': success,
            'message': 'Welcome email sent successfully' if success else 'Failed to send welcome email'
        })

    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@onboarding_completion_bp.route('/create-reminder', methods=['POST'])
@login_required
def create_first_checkin_reminder():
    """Create the first check-in reminder."""
    try:
        db_session = get_db_session()
        data = request.get_json()
        user_id = data.get('user_id')
        scheduled_date = data.get('scheduled_date')
        reminder_type = data.get('reminder_type', 'first_checkin')

        # Verify user access
        if str(current_user.id) != str(user_id):
            return jsonify({'error': 'Unauthorized access'}), 403

        # Parse scheduled date
        scheduled_datetime = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))

        # Create reminder schedule
        reminder_schedule = ReminderSchedule(
            user_id=current_user.id,
            reminder_type=reminder_type,
            scheduled_date=scheduled_datetime,
            frequency='weekly',
            enabled=True
        )

        db_session.add(reminder_schedule)
        db_session.commit()

        return jsonify({
            'success': True,
            'message': 'Reminder created successfully',
            'scheduled_date': scheduled_datetime.isoformat()
        })

    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500 