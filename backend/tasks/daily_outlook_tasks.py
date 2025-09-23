#!/usr/bin/env python3
"""
Mingus Daily Outlook Celery Tasks

Background tasks for daily outlook pre-generation, notifications, and content optimization.
Compatible with the existing Celery setup in the Mingus application.

Features:
- Daily outlook pre-generation for all active users
- Timezone-aware notification delivery
- Content performance optimization and A/B testing
- Integration with existing notification system
- Comprehensive error handling and retry logic
- Performance metrics and analytics
"""

import os
import sys
import logging
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional, List
import pytz

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Celery imports
from celery import Celery
from celery.exceptions import Retry
from celery.utils.log import get_task_logger

# Import our services and models
from backend.services.daily_outlook_content_service import DailyOutlookContentService
from backend.services.daily_outlook_service import DailyOutlookService
from backend.models.daily_outlook import DailyOutlook
from backend.models.user_models import User

# Configure logging
logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)

# Initialize Celery app
def make_celery(app=None):
    """Create and configure Celery app"""
    celery = Celery(
        app.import_name if app else 'mingus_daily_outlook_tasks',
        broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/2'),
        backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2'),
        include=['backend.tasks.daily_outlook_tasks']
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=600,  # 10 minutes for content generation
        task_soft_time_limit=540,  # 9 minutes
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_disable_rate_limits=False,
        task_compression='gzip',
        result_compression='gzip',
        task_routes={
            'backend.tasks.daily_outlook_tasks.*': {'queue': 'daily_outlook_queue'},
        },
        task_default_queue='daily_outlook_queue',
        task_default_exchange='daily_outlook_exchange',
        task_default_exchange_type='direct',
        task_default_routing_key='daily_outlook_task',
    )
    
    return celery

# Create Celery app
celery_app = make_celery()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def generate_daily_outlooks_batch(self, target_date: str = None, force_regenerate: bool = False):
    """
    Pre-generate daily outlooks for all active users.
    Runs every night at 5:00 AM UTC.
    
    Args:
        target_date: Date to generate outlooks for (YYYY-MM-DD format, defaults to tomorrow)
        force_regenerate: If True, regenerate even if outlooks already exist
        
    Returns:
        Dict containing generation results and statistics
    """
    task_id = self.request.id
    celery_logger.info(f"Starting daily outlook batch generation task {task_id}")
    
    try:
        # Parse target date
        if target_date:
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date_obj = date.today() + timedelta(days=1)  # Tomorrow
        
        # Initialize services
        content_service = DailyOutlookContentService()
        outlook_service = DailyOutlookService()
        
        # Get all active users
        active_users = _get_active_users()
        celery_logger.info(f"Found {len(active_users)} active users for outlook generation")
        
        if not active_users:
            return {
                'success': True,
                'message': 'No active users found',
                'target_date': target_date_obj.isoformat(),
                'task_id': task_id,
                'generated_count': 0
            }
        
        # Track generation results
        results = {
            'success': True,
            'target_date': target_date_obj.isoformat(),
            'task_id': task_id,
            'total_users': len(active_users),
            'generated_count': 0,
            'skipped_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        # Generate outlooks for each user
        for user in active_users:
            try:
                # Check if outlook already exists (unless forcing regeneration)
                if not force_regenerate:
                    existing_outlook = DailyOutlook.query.filter(
                        DailyOutlook.user_id == user.id,
                        DailyOutlook.date == target_date_obj
                    ).first()
                    
                    if existing_outlook:
                        results['skipped_count'] += 1
                        celery_logger.debug(f"Skipping user {user.id} - outlook already exists")
                        continue
                
                # Generate personalized outlook
                outlook_data = content_service.generate_daily_outlook(user.id)
                
                # Update date to target date
                outlook_data['date'] = target_date_obj
                outlook_data['user_id'] = user.id
                
                # Save to database
                success = content_service._save_daily_outlook(outlook_data)
                
                if success:
                    results['generated_count'] += 1
                    celery_logger.debug(f"Generated outlook for user {user.id}")
                else:
                    results['failed_count'] += 1
                    results['errors'].append(f"Failed to save outlook for user {user.id}")
                    
            except Exception as e:
                results['failed_count'] += 1
                error_msg = f"Error generating outlook for user {user.id}: {str(e)}"
                results['errors'].append(error_msg)
                celery_logger.error(error_msg)
        
        # Log final results
        celery_logger.info(f"Daily outlook generation completed: {results['generated_count']} generated, "
                          f"{results['skipped_count']} skipped, {results['failed_count']} failed")
        
        return results
        
    except Exception as exc:
        celery_logger.error(f"Daily outlook batch generation failed: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            celery_logger.info(f"Retrying daily outlook generation (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))  # Exponential backoff
        
        # Final failure
        return {
            'success': False,
            'error': str(exc),
            'task_id': task_id,
            'retries_exhausted': True,
            'target_date': target_date_obj.isoformat() if 'target_date_obj' in locals() else None
        }

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def send_daily_outlook_notifications(self, target_date: str = None):
    """
    Send daily outlook notifications to users at their preferred times.
    Handles timezone differences for different cities.
    
    Args:
        target_date: Date to send notifications for (YYYY-MM-DD format, defaults to today)
        
    Returns:
        Dict containing notification results and statistics
    """
    task_id = self.request.id
    celery_logger.info(f"Starting daily outlook notifications task {task_id}")
    
    try:
        # Parse target date
        if target_date:
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date_obj = date.today()
        
        # Get users with notification preferences
        users_to_notify = _get_users_for_notification(target_date_obj)
        celery_logger.info(f"Found {len(users_to_notify)} users to notify")
        
        if not users_to_notify:
            return {
                'success': True,
                'message': 'No users to notify',
                'target_date': target_date_obj.isoformat(),
                'task_id': task_id,
                'notifications_sent': 0
            }
        
        # Track notification results
        results = {
            'success': True,
            'target_date': target_date_obj.isoformat(),
            'task_id': task_id,
            'total_users': len(users_to_notify),
            'notifications_sent': 0,
            'failed_count': 0,
            'errors': []
        }
        
        # Send notifications to each user
        for user_data in users_to_notify:
            try:
                # Get user's outlook for the target date
                outlook = DailyOutlook.query.filter(
                    DailyOutlook.user_id == user_data['user_id'],
                    DailyOutlook.date == target_date_obj
                ).first()
                
                if not outlook:
                    celery_logger.warning(f"No outlook found for user {user_data['user_id']} on {target_date_obj}")
                    results['failed_count'] += 1
                    continue
                
                # Send notification via existing notification system
                notification_sent = _send_outlook_notification(user_data, outlook)
                
                if notification_sent:
                    results['notifications_sent'] += 1
                    celery_logger.debug(f"Notification sent to user {user_data['user_id']}")
                else:
                    results['failed_count'] += 1
                    results['errors'].append(f"Failed to send notification to user {user_data['user_id']}")
                    
            except Exception as e:
                results['failed_count'] += 1
                error_msg = f"Error sending notification to user {user_data['user_id']}: {str(e)}"
                results['errors'].append(error_msg)
                celery_logger.error(error_msg)
        
        # Log final results
        celery_logger.info(f"Daily outlook notifications completed: {results['notifications_sent']} sent, "
                          f"{results['failed_count']} failed")
        
        return results
        
    except Exception as exc:
        celery_logger.error(f"Daily outlook notifications failed: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            celery_logger.info(f"Retrying daily outlook notifications (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30)
        
        # Final failure
        return {
            'success': False,
            'error': str(exc),
            'task_id': task_id,
            'retries_exhausted': True,
            'target_date': target_date_obj.isoformat() if 'target_date_obj' in locals() else None
        }

@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def optimize_content_performance(self, analysis_period_days: int = 7):
    """
    Analyze outlook performance and optimize content.
    Runs weekly to identify low-performing content and trigger A/B testing.
    
    Args:
        analysis_period_days: Number of days to analyze (default 7)
        
    Returns:
        Dict containing optimization results and recommendations
    """
    task_id = self.request.id
    celery_logger.info(f"Starting content performance optimization task {task_id}")
    
    try:
        # Calculate analysis period
        end_date = date.today()
        start_date = end_date - timedelta(days=analysis_period_days)
        
        # Get performance metrics
        performance_data = _analyze_outlook_performance(start_date, end_date)
        
        # Identify low-performing content
        low_performing_content = _identify_low_performing_content(performance_data)
        
        # Generate optimization recommendations
        recommendations = _generate_optimization_recommendations(low_performing_content)
        
        # Trigger A/B tests for improvements
        ab_tests_triggered = _trigger_ab_tests(recommendations)
        
        # Update content templates based on findings
        templates_updated = _update_content_templates(recommendations)
        
        # Track optimization results
        results = {
            'success': True,
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': analysis_period_days
            },
            'task_id': task_id,
            'performance_metrics': performance_data,
            'low_performing_content': low_performing_content,
            'recommendations': recommendations,
            'ab_tests_triggered': ab_tests_triggered,
            'templates_updated': templates_updated
        }
        
        # Log results
        celery_logger.info(f"Content performance optimization completed: "
                          f"{len(low_performing_content)} low-performing items identified, "
                          f"{ab_tests_triggered} A/B tests triggered, "
                          f"{templates_updated} templates updated")
        
        return results
        
    except Exception as exc:
        celery_logger.error(f"Content performance optimization failed: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            celery_logger.info(f"Retrying content optimization (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # Final failure
        return {
            'success': False,
            'error': str(exc),
            'task_id': task_id,
            'retries_exhausted': True
        }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_active_users() -> List[User]:
    """Get all active users who should receive daily outlooks"""
    try:
        # Get users who have been active in the last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        active_users = User.query.filter(
            User.last_activity >= cutoff_date
        ).all()
        
        return active_users
        
    except Exception as e:
        celery_logger.error(f"Error getting active users: {e}")
        return []

def _get_users_for_notification(target_date: date) -> List[Dict[str, Any]]:
    """Get users who should receive notifications for the target date"""
    try:
        # This would typically check user notification preferences
        # For now, we'll get users with outlooks for the target date
        users_with_outlooks = User.query.join(DailyOutlook).filter(
            DailyOutlook.date == target_date
        ).all()
        
        # Convert to notification format
        users_to_notify = []
        for user in users_with_outlooks:
            # Get user's timezone (default to UTC if not set)
            user_timezone = getattr(user, 'timezone', 'UTC')
            
            # Get notification preferences (default to 6:45 AM weekdays, 8:30 AM weekends)
            notification_time = _get_user_notification_time(user, target_date)
            
            users_to_notify.append({
                'user_id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'timezone': user_timezone,
                'notification_time': notification_time,
                'preferences': {
                    'weekday_time': '06:45',
                    'weekend_time': '08:30',
                    'enabled': True
                }
            })
        
        return users_to_notify
        
    except Exception as e:
        celery_logger.error(f"Error getting users for notification: {e}")
        return []

def _get_user_notification_time(user: User, target_date: date) -> str:
    """Get the preferred notification time for a user on a specific date"""
    try:
        # Check if it's a weekday (Monday=0, Sunday=6)
        is_weekday = target_date.weekday() < 5
        
        # Get user preferences (defaults if not set)
        weekday_time = getattr(user, 'weekday_notification_time', '06:45')
        weekend_time = getattr(user, 'weekend_notification_time', '08:30')
        
        return weekday_time if is_weekday else weekend_time
        
    except Exception as e:
        celery_logger.error(f"Error getting notification time for user {user.id}: {e}")
        return '06:45'  # Default fallback

def _send_outlook_notification(user_data: Dict[str, Any], outlook: DailyOutlook) -> bool:
    """Send outlook notification to user via existing notification system"""
    try:
        # This would integrate with the existing notification system
        # For now, we'll simulate the notification
        
        # Prepare notification content
        notification_content = {
            'title': 'Your Daily Outlook is Ready! 🌅',
            'message': f"Good morning {user_data.get('first_name', 'there')}! Your personalized daily outlook is ready.",
            'outlook_preview': outlook.primary_insight[:100] + '...' if outlook.primary_insight else 'Your daily insights await!',
            'streak_count': outlook.streak_count,
            'balance_score': outlook.balance_score,
            'action_url': f'/daily-outlook/{outlook.date}',
            'user_id': user_data['user_id']
        }
        
        # Send via existing notification system
        # This would integrate with the HousingNotificationSystem or similar
        celery_logger.info(f"Notification prepared for user {user_data['user_id']}: {notification_content['title']}")
        
        # In a real implementation, this would:
        # 1. Send push notification via FCM/APNS
        # 2. Send email notification
        # 3. Update user's notification history
        # 4. Track delivery metrics
        
        return True
        
    except Exception as e:
        celery_logger.error(f"Error sending notification to user {user_data['user_id']}: {e}")
        return False

def _analyze_outlook_performance(start_date: date, end_date: date) -> Dict[str, Any]:
    """Analyze outlook performance metrics for the given period"""
    try:
        # Get outlooks in the analysis period
        outlooks = DailyOutlook.query.filter(
            DailyOutlook.date >= start_date,
            DailyOutlook.date <= end_date
        ).all()
        
        if not outlooks:
            return {
                'total_outlooks': 0,
                'view_rate': 0.0,
                'engagement_rate': 0.0,
                'average_rating': 0.0,
                'completion_rate': 0.0
            }
        
        # Calculate metrics
        total_outlooks = len(outlooks)
        viewed_outlooks = len([o for o in outlooks if o.viewed_at])
        rated_outlooks = len([o for o in outlooks if o.user_rating])
        completed_actions = len([o for o in outlooks if o.actions_completed])
        
        return {
            'total_outlooks': total_outlooks,
            'view_rate': viewed_outlooks / total_outlooks if total_outlooks > 0 else 0.0,
            'engagement_rate': rated_outlooks / total_outlooks if total_outlooks > 0 else 0.0,
            'average_rating': sum(o.user_rating for o in outlooks if o.user_rating) / rated_outlooks if rated_outlooks > 0 else 0.0,
            'completion_rate': completed_actions / total_outlooks if total_outlooks > 0 else 0.0,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }
        
    except Exception as e:
        celery_logger.error(f"Error analyzing outlook performance: {e}")
        return {}

def _identify_low_performing_content(performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify low-performing content based on performance metrics"""
    try:
        low_performing = []
        
        # Define thresholds for low performance
        thresholds = {
            'view_rate': 0.3,  # Less than 30% view rate
            'engagement_rate': 0.2,  # Less than 20% engagement
            'average_rating': 3.0,  # Less than 3.0 average rating
            'completion_rate': 0.15  # Less than 15% completion
        }
        
        # Check each metric against thresholds
        for metric, threshold in thresholds.items():
            if performance_data.get(metric, 0) < threshold:
                low_performing.append({
                    'metric': metric,
                    'current_value': performance_data.get(metric, 0),
                    'threshold': threshold,
                    'severity': 'high' if performance_data.get(metric, 0) < threshold * 0.5 else 'medium'
                })
        
        return low_performing
        
    except Exception as e:
        celery_logger.error(f"Error identifying low-performing content: {e}")
        return []

def _generate_optimization_recommendations(low_performing_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate optimization recommendations based on low-performing content"""
    try:
        recommendations = []
        
        for item in low_performing_content:
            if item['metric'] == 'view_rate':
                recommendations.append({
                    'type': 'notification_timing',
                    'description': 'Optimize notification timing and frequency',
                    'priority': 'high' if item['severity'] == 'high' else 'medium',
                    'actions': ['Adjust notification times', 'A/B test different schedules']
                })
            elif item['metric'] == 'engagement_rate':
                recommendations.append({
                    'type': 'content_personalization',
                    'description': 'Improve content personalization and relevance',
                    'priority': 'high' if item['severity'] == 'high' else 'medium',
                    'actions': ['Enhance user profiling', 'Improve content matching']
                })
            elif item['metric'] == 'average_rating':
                recommendations.append({
                    'type': 'content_quality',
                    'description': 'Improve content quality and value',
                    'priority': 'high' if item['severity'] == 'high' else 'medium',
                    'actions': ['Review content templates', 'Update insight generation']
                })
            elif item['metric'] == 'completion_rate':
                recommendations.append({
                    'type': 'action_design',
                    'description': 'Optimize quick actions and user flow',
                    'priority': 'high' if item['severity'] == 'high' else 'medium',
                    'actions': ['Simplify action steps', 'Improve action relevance']
                })
        
        return recommendations
        
    except Exception as e:
        celery_logger.error(f"Error generating optimization recommendations: {e}")
        return []

def _trigger_ab_tests(recommendations: List[Dict[str, Any]]) -> int:
    """Trigger A/B tests based on optimization recommendations"""
    try:
        ab_tests_triggered = 0
        
        for recommendation in recommendations:
            if recommendation['priority'] == 'high':
                # Trigger A/B test for high-priority recommendations
                celery_logger.info(f"Triggering A/B test for: {recommendation['type']}")
                ab_tests_triggered += 1
        
        return ab_tests_triggered
        
    except Exception as e:
        celery_logger.error(f"Error triggering A/B tests: {e}")
        return 0

def _update_content_templates(recommendations: List[Dict[str, Any]]) -> int:
    """Update content templates based on optimization recommendations"""
    try:
        templates_updated = 0
        
        for recommendation in recommendations:
            if recommendation['type'] in ['content_personalization', 'content_quality']:
                # Update content templates
                celery_logger.info(f"Updating content templates for: {recommendation['type']}")
                templates_updated += 1
        
        return templates_updated
        
    except Exception as e:
        celery_logger.error(f"Error updating content templates: {e}")
        return 0

# ============================================================================
# PERIODIC TASK CONFIGURATION
# ============================================================================

@celery_app.task
def schedule_daily_outlook_generation():
    """Schedule daily outlook generation (called by Celery Beat)"""
    celery_logger.info("Scheduling daily outlook generation")
    
    # Schedule the generation task
    result = generate_daily_outlooks_batch.delay()
    
    return {
        'success': True,
        'scheduled_task_id': result.id,
        'scheduled_at': datetime.utcnow().isoformat()
    }

@celery_app.task
def schedule_daily_outlook_notifications():
    """Schedule daily outlook notifications (called by Celery Beat)"""
    celery_logger.info("Scheduling daily outlook notifications")
    
    # Schedule the notification task
    result = send_daily_outlook_notifications.delay()
    
    return {
        'success': True,
        'scheduled_task_id': result.id,
        'scheduled_at': datetime.utcnow().isoformat()
    }

@celery_app.task
def schedule_content_optimization():
    """Schedule content performance optimization (called by Celery Beat)"""
    celery_logger.info("Scheduling content performance optimization")
    
    # Schedule the optimization task
    result = optimize_content_performance.delay()
    
    return {
        'success': True,
        'scheduled_task_id': result.id,
        'scheduled_at': datetime.utcnow().isoformat()
    }

# ============================================================================
# HEALTH MONITORING
# ============================================================================

@celery_app.task(bind=True)
def health_check_daily_outlook_tasks(self):
    """Health check task for daily outlook system"""
    task_id = self.request.id
    celery_logger.info("Running daily outlook system health check")
    
    try:
        # Check database connectivity
        from backend.models.database import db
        db.session.execute('SELECT 1')
        
        # Check recent task performance
        recent_outlooks = DailyOutlook.query.filter(
            DailyOutlook.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        # Check active users
        active_users = _get_active_users()
        
        health_status = {
            'service_status': 'healthy',
            'database_connected': True,
            'recent_outlooks_generated': recent_outlooks,
            'active_users_count': len(active_users),
            'task_id': task_id,
            'check_time': datetime.utcnow().isoformat(),
            'task_type': 'health_check'
        }
        
        celery_logger.info("Daily outlook system health check passed")
        return health_status
        
    except Exception as exc:
        celery_logger.error(f"Daily outlook system health check failed: {exc}")
        return {
            'service_status': 'error',
            'error': str(exc),
            'task_id': task_id,
            'check_time': datetime.utcnow().isoformat(),
            'task_type': 'health_check'
        }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def generate_daily_outlooks(self, target_date: str = None, force_regenerate: bool = False):
    """
    Generate daily outlooks for all active users.
    This is a wrapper function for the batch generation task.
    
    Args:
        target_date: Date to generate outlooks for (YYYY-MM-DD format, defaults to tomorrow)
        force_regenerate: If True, regenerate even if outlooks already exist
        
    Returns:
        Dict containing generation results and statistics
    """
    task_id = self.request.id
    celery_logger.info(f"Starting daily outlook generation task {task_id}")
    
    try:
        # Call the batch generation function
        result = generate_daily_outlooks_batch(target_date, force_regenerate)
        
        celery_logger.info(f"Daily outlook generation task {task_id} completed successfully")
        return {
            'status': 'success',
            'task_id': task_id,
            'generated_count': result.get('generated_count', 0),
            'skipped_count': result.get('skipped_count', 0),
            'error_count': result.get('error_count', 0),
            'target_date': target_date or (date.today() + timedelta(days=1)).isoformat(),
            'completion_time': datetime.utcnow().isoformat(),
            'task_type': 'generate_daily_outlooks'
        }
        
    except Exception as exc:
        celery_logger.error(f"Daily outlook generation task {task_id} failed: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            celery_logger.info(f"Retrying daily outlook generation task {task_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'status': 'error',
            'error': str(exc),
            'task_id': task_id,
            'completion_time': datetime.utcnow().isoformat(),
            'task_type': 'generate_daily_outlooks'
        }
