"""
MINGUS Celery Tasks for SMS and Email Communications
Handles all asynchronous communication tasks with proper prioritization and error handling
"""

import os
import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal

# Celery imports
from celery import Celery, current_task
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError

# External service imports
import redis
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioException
import resend
from sqlalchemy import and_, or_, func, desc, extract

# Database imports
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# MINGUS imports
from ..database import get_db_session
from ..models.user import User
from ..models.communication_preferences import (
    CommunicationPreferences, ConsentRecord, CommunicationDeliveryLog,
    AlertType, CommunicationChannel, ConsentStatus
)
from ..models.communication_analytics import (
    CommunicationMetrics, UserEngagementAnalytics, FinancialImpactMetrics,
    MetricType, ChannelType
)
from ..models.behavioral_triggers import TriggerEvent
from ..services.communication_preference_service import CommunicationPreferenceService
from ..services.communication_analytics_service import CommunicationAnalyticsService

# Configure logging
logger = get_task_logger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Celery app
celery_app = Celery('mingus_celery_tasks')
celery_app.config_from_object('celeryconfig')

# Initialize external services
try:
    # Twilio configuration
    twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if twilio_account_sid and twilio_auth_token:
        twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)
    else:
        twilio_client = None
        logger.warning("Twilio credentials not configured")
        
    # Resend configuration
    resend_api_key = os.getenv('RESEND_API_KEY')
    if resend_api_key:
        try:
            resend.api_key = resend_api_key
            resend_client = resend
        except Exception:
            resend_client = None
            logger.warning("Failed to configure Resend client")
    else:
        resend_client = None
        logger.warning("Resend API key not configured")
        
    # Redis configuration
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.from_url(redis_url)
    
except Exception as e:
    logger.error(f"Failed to initialize external services: {e}")
    twilio_client = None
    resend_client = None
    redis_client = None

# Initialize services
communication_preference_service = CommunicationPreferenceService()
communication_analytics_service = CommunicationAnalyticsService()

# Cost tracking constants
SMS_COST_PER_MESSAGE = Decimal('0.0075')  # $0.0075 per SMS
EMAIL_COST_PER_MESSAGE = Decimal('0.0001')  # $0.0001 per email

# Rate limiting constants
RATE_LIMITS = {
    'critical_financial': {'sms': '10/m', 'email': '5/m'},
    'payment_reminder': {'sms': '20/m', 'email': '10/m'},
    'weekly_checkin': {'sms': '50/m', 'email': '25/m'},
    'milestone_reminder': {'sms': '30/m', 'email': '15/m'},
    'monthly_report': {'sms': '0/m', 'email': '10/m'},
    'career_insights': {'sms': '0/m', 'email': '20/m'},
    'educational_content': {'sms': '0/m', 'email': '30/m'},
    'onboarding_sequence': {'sms': '100/m', 'email': '50/m'}
}


def validate_user_preferences(user_id: str, channel: CommunicationChannel, 
                            alert_type: AlertType) -> Tuple[bool, str]:
    """
    Validate if user has consented to receive communications
    
    Args:
        user_id: User ID
        channel: Communication channel (SMS/EMAIL)
        alert_type: Type of alert
        
    Returns:
        Tuple of (can_send, reason)
    """
    try:
        db = get_db_session()
        
        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Check communication preferences
        preferences = db.query(CommunicationPreferences).filter(
            CommunicationPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            return False, "No communication preferences found"
        
        # Check channel-specific consent
        if channel == CommunicationChannel.SMS:
            if not preferences.sms_enabled:
                return False, "SMS communications disabled"
            
            # Check TCPA compliance
            consent = db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.user_id == user_id,
                    ConsentRecord.consent_type == 'sms',
                    ConsentRecord.consent_status == ConsentStatus.GRANTED
                )
            ).first()
            
            if not consent:
                return False, "SMS consent not granted"
                
        elif channel == CommunicationChannel.EMAIL:
            if not preferences.email_enabled:
                return False, "Email communications disabled"
            
            # Check GDPR compliance
            consent = db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.user_id == user_id,
                    ConsentRecord.consent_type == 'email',
                    ConsentRecord.consent_status == ConsentStatus.GRANTED
                )
            ).first()
            
            if not consent:
                return False, "Email consent not granted"
        
        # Check alert type preferences
        alert_pref = db.query(AlertTypePreference).filter(
            and_(
                AlertTypePreference.user_id == user_id,
                AlertTypePreference.alert_type == alert_type
            )
        ).first()
        
        if alert_pref and not alert_pref.enabled:
            return False, f"Alert type {alert_type.value} disabled"
        
        return True, "Valid"
        
    except Exception as e:
        logger.error(f"Error validating user preferences: {e}")
        return False, f"Validation error: {str(e)}"
    finally:
        db.close()


def track_communication_cost(user_id: str, channel: CommunicationChannel, 
                           message_type: str, success: bool) -> None:
    """
    Track communication costs for billing and analytics
    
    Args:
        user_id: User ID
        channel: Communication channel
        message_type: Type of message sent
        success: Whether delivery was successful
    """
    try:
        cost = SMS_COST_PER_MESSAGE if channel == CommunicationChannel.SMS else EMAIL_COST_PER_MESSAGE
        
        # Store cost in Redis for real-time tracking
        cost_key = f"communication_cost:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
        redis_client.hincrby(cost_key, channel.value, int(cost * 10000))  # Store as integer cents
        
        # Log cost for analytics
        logger.info(f"Communication cost tracked - User: {user_id}, Channel: {channel.value}, "
                   f"Type: {message_type}, Cost: ${cost}, Success: {success}")
        
    except Exception as e:
        logger.error(f"Error tracking communication cost: {e}")


def log_delivery_status(user_id: str, channel: CommunicationChannel, message_type: str,
                       message_id: str, status: str, error_message: str = None) -> None:
    """
    Log delivery status to database
    
    Args:
        user_id: User ID
        channel: Communication channel
        message_type: Type of message
        message_id: External service message ID
        status: Delivery status
        error_message: Error message if failed
    """
    try:
        db = get_db_session()
        
        delivery_log = CommunicationDeliveryLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            channel=channel,
            alert_type=message_type,
            message_id=message_id,
            delivery_status=status,
            error_message=error_message,
            sent_at=datetime.utcnow()
        )
        
        db.add(delivery_log)
        db.commit()
        
        logger.info(f"Delivery status logged - User: {user_id}, Channel: {channel.value}, "
                   f"Status: {status}, Message ID: {message_id}")
        
    except Exception as e:
        logger.error(f"Error logging delivery status: {e}")
        db.rollback()
    finally:
        db.close()


def handle_failed_delivery(user_id: str, channel: CommunicationChannel, 
                          message_type: str, error_message: str) -> None:
    """
    Handle failed message delivery with fallback logic
    
    Args:
        user_id: User ID
        channel: Communication channel
        message_type: Type of message
        error_message: Error message
    """
    try:
        logger.warning(f"Failed delivery - User: {user_id}, Channel: {channel.value}, "
                      f"Type: {message_type}, Error: {error_message}")
        
        # Log failure
        log_delivery_status(user_id, channel, message_type, None, 'failed', error_message)
        
        # Try fallback channel if available
        if channel == CommunicationChannel.SMS:
            # Try email as fallback
            logger.info(f"Attempting email fallback for user {user_id}")
            # This would trigger an email task
            
        elif channel == CommunicationChannel.EMAIL:
            # Try SMS as fallback for critical messages
            if message_type in ['critical_financial', 'payment_reminder']:
                logger.info(f"Attempting SMS fallback for user {user_id}")
                # This would trigger an SMS task
        
        # Update analytics
        communication_analytics_service.track_delivery_metrics({
            'user_id': user_id,
            'channel': channel,
            'alert_type': message_type,
            'delivery_status': 'failed',
            'error_message': error_message
        })
        
    except Exception as e:
        logger.error(f"Error handling failed delivery: {e}")


def generate_personalized_content(user_id: str, template: str, 
                                personalization_data: Dict[str, Any]) -> str:
    """
    Generate personalized message content
    
    Args:
        user_id: User ID
        template: Message template
        personalization_data: Data for personalization
        
    Returns:
        Personalized message content
    """
    try:
        db = get_db_session()
        
        # Get user data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return template
        
        # Replace placeholders with actual data
        content = template
        
        # User-specific replacements
        content = content.replace('{user_name}', user.full_name or 'there')
        content = content.replace('{user_first_name}', user.full_name.split()[0] if user.full_name else 'there')
        
        # Data-specific replacements
        for key, value in personalization_data.items():
            placeholder = f'{{{key}}}'
            if placeholder in content:
                content = content.replace(placeholder, str(value))
        
        return content
        
    except Exception as e:
        logger.error(f"Error generating personalized content: {e}")
        return template
    finally:
        db.close()


# ============================================================================
# SMS TASKS - HIGH PRIORITY
# ============================================================================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, 
                autoretry_for=(Exception,), retry_backoff=True)
def send_critical_financial_alert(self, user_id: str, alert_data: Dict[str, Any]) -> bool:
    """
    Send critical financial alerts (Priority 1)
    
    Args:
        user_id: User ID
        alert_data: Alert data including message and urgency
        
    Returns:
        Success status
    """
    try:
        # Validate user preferences
        can_send, reason = validate_user_preferences(
            user_id, CommunicationChannel.SMS, AlertType.CRITICAL_FINANCIAL
        )
        
        if not can_send:
            logger.info(f"Skipping critical alert for user {user_id}: {reason}")
            return False
        
        # Generate personalized message
        template = alert_data.get('template', 'Critical: {message}')
        message = generate_personalized_content(user_id, template, alert_data)
        
        # Get user phone number
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.phone_number:
            raise ValueError(f"No phone number found for user {user_id}")
        
        # Send SMS via Twilio
        if not twilio_client:
            raise Exception("Twilio client not configured")
        
        message_obj = twilio_client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=user.phone_number
        )
        
        # Track success
        track_communication_cost(user_id, CommunicationChannel.SMS, 'critical_financial', True)
        log_delivery_status(user_id, CommunicationChannel.SMS, 'critical_financial', 
                          message_obj.sid, 'delivered')
        
        # Update analytics
        communication_analytics_service.track_delivery_metrics({
            'user_id': user_id,
            'channel': CommunicationChannel.SMS,
            'alert_type': 'critical_financial',
            'delivery_status': 'delivered',
            'message_id': message_obj.sid
        })
        
        logger.info(f"Critical financial alert sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending critical financial alert to user {user_id}: {e}")
        handle_failed_delivery(user_id, CommunicationChannel.SMS, 'critical_financial', str(e))
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return False
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300,
                autoretry_for=(Exception,), retry_backoff=True)
def send_payment_reminder(self, user_id: str, payment_data: Dict[str, Any]) -> bool:
    """
    Send payment reminders (Priority 2)
    
    Args:
        user_id: User ID
        payment_data: Payment reminder data
        
    Returns:
        Success status
    """
    try:
        # Validate user preferences
        can_send, reason = validate_user_preferences(
            user_id, CommunicationChannel.SMS, AlertType.BILL_REMINDERS
        )
        
        if not can_send:
            logger.info(f"Skipping payment reminder for user {user_id}: {reason}")
            return False
        
        # Generate personalized message
        template = payment_data.get('template', 'Reminder: {bill_name} due {due_date} - ${amount}')
        message = generate_personalized_content(user_id, template, payment_data)
        
        # Get user phone number
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.phone_number:
            raise ValueError(f"No phone number found for user {user_id}")
        
        # Send SMS via Twilio
        if not twilio_client:
            raise Exception("Twilio client not configured")
        
        message_obj = twilio_client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=user.phone_number
        )
        
        # Track success
        track_communication_cost(user_id, CommunicationChannel.SMS, 'payment_reminder', True)
        log_delivery_status(user_id, CommunicationChannel.SMS, 'payment_reminder', 
                          message_obj.sid, 'delivered')
        
        logger.info(f"Payment reminder sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending payment reminder to user {user_id}: {e}")
        handle_failed_delivery(user_id, CommunicationChannel.SMS, 'payment_reminder', str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return False
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=600)
def send_weekly_checkin(self, user_id: str, checkin_data: Dict[str, Any]) -> bool:
    """
    Send weekly wellness checkins (Priority 3)
    
    Args:
        user_id: User ID
        checkin_data: Checkin data
        
    Returns:
        Success status
    """
    try:
        # Validate user preferences
        can_send, reason = validate_user_preferences(
            user_id, CommunicationChannel.SMS, AlertType.DAILY_CHECKIN
        )
        
        if not can_send:
            logger.info(f"Skipping weekly checkin for user {user_id}: {reason}")
            return False
        
        # Generate personalized message
        template = checkin_data.get('template', 'Weekly check-in: {message}')
        message = generate_personalized_content(user_id, template, checkin_data)
        
        # Get user phone number
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.phone_number:
            raise ValueError(f"No phone number found for user {user_id}")
        
        # Send SMS via Twilio
        if not twilio_client:
            raise Exception("Twilio client not configured")
        
        message_obj = twilio_client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=user.phone_number
        )
        
        # Track success
        track_communication_cost(user_id, CommunicationChannel.SMS, 'weekly_checkin', True)
        log_delivery_status(user_id, CommunicationChannel.SMS, 'weekly_checkin', 
                          message_obj.sid, 'delivered')
        
        logger.info(f"Weekly checkin sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending weekly checkin to user {user_id}: {e}")
        handle_failed_delivery(user_id, CommunicationChannel.SMS, 'weekly_checkin', str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=600 * (2 ** self.request.retries))
        
        return False
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1, default_retry_delay=900)
def send_milestone_reminder(self, user_id: str, milestone_data: Dict[str, Any]) -> bool:
    """
    Send milestone reminders (Priority 4)
    
    Args:
        user_id: User ID
        milestone_data: Milestone data
        
    Returns:
        Success status
    """
    try:
        # Validate user preferences
        can_send, reason = validate_user_preferences(
            user_id, CommunicationChannel.SMS, AlertType.BUDGET_ALERTS
        )
        
        if not can_send:
            logger.info(f"Skipping milestone reminder for user {user_id}: {reason}")
            return False
        
        # Generate personalized message
        template = milestone_data.get('template', '🎉 {milestone_name} achieved! {message}')
        message = generate_personalized_content(user_id, template, milestone_data)
        
        # Get user phone number
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.phone_number:
            raise ValueError(f"No phone number found for user {user_id}")
        
        # Send SMS via Twilio
        if not twilio_client:
            raise Exception("Twilio client not configured")
        
        message_obj = twilio_client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=user.phone_number
        )
        
        # Track success
        track_communication_cost(user_id, CommunicationChannel.SMS, 'milestone_reminder', True)
        log_delivery_status(user_id, CommunicationChannel.SMS, 'milestone_reminder', 
                          message_obj.sid, 'delivered')
        
        logger.info(f"Milestone reminder sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending milestone reminder to user {user_id}: {e}")
        handle_failed_delivery(user_id, CommunicationChannel.SMS, 'milestone_reminder', str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=900 * (2 ** self.request.retries))
        
        return False
    finally:
        db.close()


# ============================================================================
# EMAIL TASKS - LOWER PRIORITY
# ============================================================================

@celery_app.task(bind=True, max_retries=2, default_retry_delay=1800)
def send_monthly_report(self, user_id: str, report_data: Dict[str, Any]) -> bool:
    """
    Send monthly financial reports (Priority 5)
    
    Args:
        user_id: User ID
        report_data: Report data
        
    Returns:
        Success status
    """
    try:
        # Validate user preferences
        can_send, reason = validate_user_preferences(
            user_id, CommunicationChannel.EMAIL, AlertType.MONTHLY_ANALYSIS
        )
        
        if not can_send:
            logger.info(f"Skipping monthly report for user {user_id}: {reason}")
            return False
        
        # Get user email
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            raise ValueError(f"No email found for user {user_id}")
        
        # Generate email content
        subject = report_data.get('subject', 'Your Monthly Financial Report')
        html_content = report_data.get('html_content', '<p>Your monthly report is ready!</p>')
        
        # Send email via Resend
        if not resend_client:
            raise Exception("Resend client not configured")
        
        response = resend_client.Emails.send({
            "from": "MINGUS <noreply@mingus.com>",
            "to": [user.email],
            "subject": subject,
            "html": html_content
        })
        
        # Track success
        track_communication_cost(user_id, CommunicationChannel.EMAIL, 'monthly_report', True)
        log_delivery_status(user_id, CommunicationChannel.EMAIL, 'monthly_report', 
                          response.id, 'delivered')
        
        logger.info(f"Monthly report sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending monthly report to user {user_id}: {e}")
        handle_failed_delivery(user_id, CommunicationChannel.EMAIL, 'monthly_report', str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=1800 * (2 ** self.request.retries))
        
        return False
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=1800)
def send_career_insights(self, user_id: str, career_data: Dict[str, Any]) -> bool:
    """
    Send career insights (Priority 6)
    
    Args:
        user_id: User ID
        career_data: Career data
        
    Returns:
        Success status
    """
    try:
        # Validate user preferences
        can_send, reason = validate_user_preferences(
            user_id, CommunicationChannel.EMAIL, AlertType.CAREER_INSIGHTS
        )
        
        if not can_send:
            logger.info(f"Skipping career insights for user {user_id}: {reason}")
            return False
        
        # Get user email
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            raise ValueError(f"No email found for user {user_id}")
        
        # Generate email content
        subject = career_data.get('subject', 'Career Opportunities for You')
        html_content = career_data.get('html_content', '<p>New career insights available!</p>')
        
        # Send email via Resend
        if not resend_client:
            raise Exception("Resend client not configured")
        
        response = resend_client.Emails.send({
            "from": "MINGUS <noreply@mingus.com>",
            "to": [user.email],
            "subject": subject,
            "html": html_content
        })
        
        # Track success
        track_communication_cost(user_id, CommunicationChannel.EMAIL, 'career_insights', True)
        log_delivery_status(user_id, CommunicationChannel.EMAIL, 'career_insights', 
                          response.id, 'delivered')
        
        logger.info(f"Career insights sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending career insights to user {user_id}: {e}")
        handle_failed_delivery(user_id, CommunicationChannel.EMAIL, 'career_insights', str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=1800 * (2 ** self.request.retries))
        
        return False
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=1800)
def send_educational_content(self, user_id: str, education_data: Dict[str, Any]) -> bool:
    """
    Send educational content (Priority 7)
    
    Args:
        user_id: User ID
        education_data: Education data
        
    Returns:
        Success status
    """
    try:
        # Validate user preferences
        can_send, reason = validate_user_preferences(
            user_id, CommunicationChannel.EMAIL, AlertType.MARKETING_CONTENT
        )
        
        if not can_send:
            logger.info(f"Skipping educational content for user {user_id}: {reason}")
            return False
        
        # Get user email
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            raise ValueError(f"No email found for user {user_id}")
        
        # Generate email content
        subject = education_data.get('subject', 'Financial Education: {topic}')
        html_content = education_data.get('html_content', '<p>New educational content available!</p>')
        
        # Send email via Resend
        if not resend_client:
            raise Exception("Resend client not configured")
        
        response = resend_client.Emails.send({
            "from": "MINGUS <noreply@mingus.com>",
            "to": [user.email],
            "subject": subject,
            "html": html_content
        })
        
        # Track success
        track_communication_cost(user_id, CommunicationChannel.EMAIL, 'educational_content', True)
        log_delivery_status(user_id, CommunicationChannel.EMAIL, 'educational_content', 
                          response.id, 'delivered')
        
        logger.info(f"Educational content sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending educational content to user {user_id}: {e}")
        handle_failed_delivery(user_id, CommunicationChannel.EMAIL, 'educational_content', str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=1800 * (2 ** self.request.retries))
        
        return False
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=900)
def send_onboarding_sequence(self, user_id: str, onboarding_data: Dict[str, Any]) -> bool:
    """
    Send onboarding sequence emails (Priority 8)
    
    Args:
        user_id: User ID
        onboarding_data: Onboarding data
        
    Returns:
        Success status
    """
    try:
        # Validate user preferences
        can_send, reason = validate_user_preferences(
            user_id, CommunicationChannel.EMAIL, AlertType.MARKETING_CONTENT
        )
        
        if not can_send:
            logger.info(f"Skipping onboarding sequence for user {user_id}: {reason}")
            return False
        
        # Get user email
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.email:
            raise ValueError(f"No email found for user {user_id}")
        
        # Generate email content
        subject = onboarding_data.get('subject', 'Welcome to MINGUS!')
        html_content = onboarding_data.get('html_content', '<p>Welcome to MINGUS!</p>')
        
        # Send email via Resend
        if not resend_client:
            raise Exception("Resend client not configured")
        
        response = resend_client.emails.send({
            "from": "MINGUS <noreply@mingus.com>",
            "to": [user.email],
            "subject": subject,
            "html": html_content
        })
        
        # Track success
        track_communication_cost(user_id, CommunicationChannel.EMAIL, 'onboarding_sequence', True)
        log_delivery_status(user_id, CommunicationChannel.EMAIL, 'onboarding_sequence', 
                          response.id, 'delivered')
        
        logger.info(f"Onboarding sequence sent to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending onboarding sequence to user {user_id}: {e}")
        handle_failed_delivery(user_id, CommunicationChannel.EMAIL, 'onboarding_sequence', str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=900 * (2 ** self.request.retries))
        
        return False
    finally:
        db.close()


# ============================================================================
# MONITORING AND ANALYTICS TASKS
# ============================================================================

@celery_app.task(bind=True, max_retries=1, default_retry_delay=300)
def monitor_queue_depth(self) -> Dict[str, Any]:
    """
    Monitor Celery queue depths and alert if thresholds exceeded
    """
    try:
        queue_stats = {}
        
        # Get queue depths from Redis
        for queue_name in ['sms_critical', 'sms_daily', 'email_reports', 'email_education']:
            depth = redis_client.llen(f'celery:{queue_name}')
            queue_stats[queue_name] = depth
            
            # Alert if queue depth is too high
            if depth > 1000:  # Threshold for critical queues
                logger.warning(f"High queue depth detected: {queue_name} has {depth} tasks")
        
        logger.info(f"Queue monitoring completed: {queue_stats}")
        return queue_stats
        
    except Exception as e:
        logger.error(f"Error monitoring queue depth: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300)
        return {}


@celery_app.task(bind=True, max_retries=1, default_retry_delay=600)
def track_delivery_rates(self) -> Dict[str, Any]:
    """
    Track delivery rates and update analytics
    """
    try:
        # Get delivery statistics from database
        db = get_db_session()
        
        # Calculate delivery rates for last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        total_sent = db.query(CommunicationDeliveryLog).filter(
            CommunicationDeliveryLog.sent_at >= yesterday
        ).count()
        
        total_delivered = db.query(CommunicationDeliveryLog).filter(
            and_(
                CommunicationDeliveryLog.sent_at >= yesterday,
                CommunicationDeliveryLog.delivery_status == 'delivered'
            )
        ).count()
        
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        
        # Update analytics
        communication_analytics_service.update_queue_status({
            'delivery_rate_24h': delivery_rate,
            'total_sent_24h': total_sent,
            'total_delivered_24h': total_delivered
        })
        
        logger.info(f"Delivery rate tracking completed: {delivery_rate:.2f}%")
        return {'delivery_rate': delivery_rate, 'total_sent': total_sent}
        
    except Exception as e:
        logger.error(f"Error tracking delivery rates: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=600)
        return {}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1, default_retry_delay=1800)
def analyze_user_engagement(self) -> Dict[str, Any]:
    """
    Analyze user engagement patterns
    """
    try:
        # Get engagement data from database
        db = get_db_session()
        
        # Analyze engagement by time of day
        engagement_by_hour = {}
        for hour in range(24):
            count = db.query(CommunicationDeliveryLog).filter(
                and_(
                    extract('hour', CommunicationDeliveryLog.sent_at) == hour,
                    CommunicationDeliveryLog.user_engaged == True
                )
            ).count()
            engagement_by_hour[hour] = count
        
        # Update analytics
        communication_analytics_service.update_user_engagement_analytics({
            'engagement_by_hour': engagement_by_hour
        })
        
        logger.info(f"User engagement analysis completed")
        return {'engagement_by_hour': engagement_by_hour}
        
    except Exception as e:
        logger.error(f"Error analyzing user engagement: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=1800)
        return {}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def process_failed_messages(self) -> Dict[str, Any]:
    """
    Process failed messages and attempt retry or fallback
    """
    try:
        db = get_db_session()
        
        # Get failed messages from last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        failed_messages = db.query(CommunicationDeliveryLog).filter(
            and_(
                CommunicationDeliveryLog.sent_at >= one_hour_ago,
                CommunicationDeliveryLog.delivery_status == 'failed'
            )
        ).all()
        
        processed_count = 0
        for message in failed_messages:
            try:
                # Attempt retry or fallback based on message type
                if message.channel == CommunicationChannel.SMS:
                    # Retry SMS or fallback to email
                    if message.alert_type in ['critical_financial', 'payment_reminder']:
                        # Retry SMS for critical messages
                        send_critical_financial_alert.delay(message.user_id, {
                            'template': 'Retry: {message}',
                            'message': 'Previous message failed to deliver'
                        })
                else:
                    # Retry email
                    send_monthly_report.delay(message.user_id, {
                        'subject': 'Retry: Previous message failed',
                        'html_content': '<p>Previous message failed to deliver</p>'
                    })
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing failed message {message.id}: {e}")
        
        logger.info(f"Processed {processed_count} failed messages")
        return {'processed_count': processed_count}
        
    except Exception as e:
        logger.error(f"Error processing failed messages: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300)
        return {}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1, default_retry_delay=3600)
def optimize_send_timing(self) -> Dict[str, Any]:
    """
    Optimize send timing based on user engagement patterns
    """
    try:
        # Analyze optimal send times based on engagement data
        db = get_db_session()
        
        # Get user engagement patterns
        engagement_patterns = db.query(UserEngagementAnalytics).all()
        
        optimizations = {}
        for pattern in engagement_patterns:
            if pattern.engagement_by_hour:
                # Find best engagement hours
                best_hours = sorted(
                    pattern.engagement_by_hour.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]
                
                optimizations[pattern.user_id] = {
                    'best_hours': [int(hour) for hour, _ in best_hours],
                    'engagement_rates': [rate for _, rate in best_hours]
                }
        
        # Store optimizations in Redis for quick access
        for user_id, optimization in optimizations.items():
            redis_client.setex(
                f"optimal_send_time:{user_id}",
                86400,  # 24 hours
                json.dumps(optimization)
            )
        
        logger.info(f"Send timing optimization completed for {len(optimizations)} users")
        return {'optimized_users': len(optimizations)}
        
    except Exception as e:
        logger.error(f"Error optimizing send timing: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=3600)
        return {}
    finally:
        db.close()


# ============================================================================
# TASK ALIASES FOR BACKWARD COMPATIBILITY
# ============================================================================

# Alias tasks for celeryconfig.py compatibility
send_sms_critical = send_critical_financial_alert
send_sms_daily = send_weekly_checkin
send_email_reports = send_monthly_report
send_email_education = send_educational_content 