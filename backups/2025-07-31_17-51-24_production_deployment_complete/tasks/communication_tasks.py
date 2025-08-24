import logging
import json
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from celery import Celery, current_task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import os

# Import existing services
from ..services.communication_router import communication_router, CommunicationMessage, MessageType, UrgencyLevel
from ..services.twilio_sms_service import twilio_sms_service
from ..services.resend_email_service import resend_email_service
from ..models.financial_alerts import FinancialAlert, UserFinancialContext, AlertDeliveryLog
from ..database import get_db_session

logger = get_task_logger(__name__)

# Initialize Celery app
celery_app = Celery('communication_tasks')
celery_app.config_from_object('celeryconfig')

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def route_and_send_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route and send a communication message
    
    Args:
        message_data: Message data including user_id, message_type, content, etc.
    
    Returns:
        Dict with delivery results
    """
    try:
        # Get database session
        db = get_db_session()
        
        # Create communication message
        message = CommunicationMessage(
            message_id=message_data.get('message_id', str(uuid.uuid4())),
            user_id=message_data['user_id'],
            message_type=MessageType(message_data['message_type']),
            urgency_level=UrgencyLevel(message_data['urgency_level']),
            content=message_data['content'],
            template_name=message_data.get('template_name'),
            template_vars=message_data.get('template_vars', {}),
            scheduled_at=datetime.fromisoformat(message_data['scheduled_at']) if message_data.get('scheduled_at') else None
        )
        
        # Get user profile (simplified - would typically query database)
        user_profile = _get_user_profile(db, message.user_id)
        
        # Route the message
        routing_decision = communication_router.route_message(message, user_profile)
        
        # Send based on routing decision
        if routing_decision.channel.value == 'sms':
            return _send_sms_message(message, user_profile, routing_decision)
        elif routing_decision.channel.value == 'email':
            return _send_email_message(message, user_profile, routing_decision)
        elif routing_decision.channel.value == 'both':
            # Send both SMS and email
            sms_result = _send_sms_message(message, user_profile, routing_decision)
            email_result = _send_email_message(message, user_profile, routing_decision)
            
            return {
                'success': sms_result.get('success') or email_result.get('success'),
                'sms_result': sms_result,
                'email_result': email_result,
                'routing_reasoning': routing_decision.reasoning
            }
        else:
            return {
                'success': False,
                'error': f'No communication channel selected: {routing_decision.reasoning}'
            }
            
    except Exception as exc:
        logger.error(f"Error in route_and_send_message: {exc}")
        self.retry(countdown=60 * (2 ** self.request.retries))
        return {
            'success': False,
            'error': str(exc)
        }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_financial_alert(self, alert_id: str) -> Dict[str, Any]:
    """
    Send a financial alert
    
    Args:
        alert_id: Financial alert ID
    
    Returns:
        Dict with delivery results
    """
    try:
        # Get database session
        db = get_db_session()
        
        # Get the alert
        alert = db.query(FinancialAlert).filter(FinancialAlert.id == alert_id).first()
        if not alert:
            return {
                'success': False,
                'error': f'Alert {alert_id} not found'
            }
        
        # Get user profile
        user_profile = _get_user_profile(db, alert.user_id)
        
        # Create communication message
        message = CommunicationMessage(
            message_id=str(alert.id),
            user_id=str(alert.user_id),
            message_type=_map_alert_type_to_message_type(alert.alert_type),
            urgency_level=UrgencyLevel(alert.urgency_level),
            content={
                'title': alert.title,
                'message': alert.message,
                'sms_message': alert.sms_message,
                'email_subject': alert.email_subject,
                'email_content': alert.email_content
            },
            template_name=alert.alert_type,
            template_vars=alert.metadata or {}
        )
        
        # Route and send
        routing_decision = communication_router.route_message(message, user_profile)
        
        # Send based on communication channel
        if alert.communication_channel == 'sms':
            result = _send_sms_message(message, user_profile, routing_decision)
        elif alert.communication_channel == 'email':
            result = _send_email_message(message, user_profile, routing_decision)
        elif alert.communication_channel == 'both':
            sms_result = _send_sms_message(message, user_profile, routing_decision)
            email_result = _send_email_message(message, user_profile, routing_decision)
            result = {
                'success': sms_result.get('success') or email_result.get('success'),
                'sms_result': sms_result,
                'email_result': email_result
            }
        else:
            result = {
                'success': False,
                'error': f'Unknown communication channel: {alert.communication_channel}'
            }
        
        # Update alert status
        if result.get('success'):
            alert.status = 'sent'
            alert.sent_at = datetime.utcnow()
        else:
            alert.status = 'failed'
        
        db.commit()
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in send_financial_alert: {exc}")
        self.retry(countdown=60 * (2 ** self.request.retries))
        return {
            'success': False,
            'error': str(exc)
        }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_batch_messages(self, batch_key: str) -> Dict[str, Any]:
    """
    Send batch messages for non-urgent communications
    
    Args:
        batch_key: Batch key for grouping messages
    
    Returns:
        Dict with batch delivery results
    """
    try:
        # Get database session
        db = get_db_session()
        
        # Get pending messages for this batch
        pending_alerts = db.query(FinancialAlert).filter(
            and_(
                FinancialAlert.status == 'pending',
                FinancialAlert.urgency_level.in_(['medium', 'low']),
                FinancialAlert.created_at <= datetime.utcnow() - timedelta(hours=1)  # Wait at least 1 hour
            )
        ).limit(50).all()  # Process up to 50 messages per batch
        
        results = []
        for alert in pending_alerts:
            result = send_financial_alert.delay(str(alert.id))
            results.append({
                'alert_id': str(alert.id),
                'task_id': result.id
            })
        
        return {
            'success': True,
            'batch_key': batch_key,
            'messages_processed': len(results),
            'results': results
        }
        
    except Exception as exc:
        logger.error(f"Error in send_batch_messages: {exc}")
        self.retry(countdown=60 * (2 ** self.request.retries))
        return {
            'success': False,
            'error': str(exc)
        }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def handle_delivery_fallback(self, original_message_id: str, fallback_channel: str) -> Dict[str, Any]:
    """
    Handle delivery fallback when primary channel fails
    
    Args:
        original_message_id: Original message ID
        fallback_channel: Fallback channel (sms or email)
    
    Returns:
        Dict with fallback delivery results
    """
    try:
        # Get database session
        db = get_db_session()
        
        # Get the original alert
        alert = db.query(FinancialAlert).filter(FinancialAlert.id == original_message_id).first()
        if not alert:
            return {
                'success': False,
                'error': f'Alert {original_message_id} not found'
            }
        
        # Get user profile
        user_profile = _get_user_profile(db, alert.user_id)
        
        # Create fallback message
        message = CommunicationMessage(
            message_id=f"{alert.id}_fallback",
            user_id=str(alert.user_id),
            message_type=_map_alert_type_to_message_type(alert.alert_type),
            urgency_level=UrgencyLevel(alert.urgency_level),
            content={
                'title': f"URGENT: {alert.title}",
                'message': f"Previous delivery failed. {alert.message}",
                'sms_message': f"URGENT: {alert.sms_message}" if alert.sms_message else None,
                'email_subject': f"URGENT: {alert.email_subject}" if alert.email_subject else None,
                'email_content': f"<p><strong>Previous delivery failed.</strong></p>{alert.email_content}" if alert.email_content else None
            },
            template_name=f"{alert.alert_type}_fallback",
            template_vars=alert.metadata or {}
        )
        
        # Send via fallback channel
        if fallback_channel == 'sms':
            result = _send_sms_message(message, user_profile, None)
        elif fallback_channel == 'email':
            result = _send_email_message(message, user_profile, None)
        else:
            result = {
                'success': False,
                'error': f'Unknown fallback channel: {fallback_channel}'
            }
        
        # Log fallback attempt
        if result.get('success'):
            log_entry = AlertDeliveryLog(
                alert_id=alert.id,
                delivery_method=fallback_channel,
                delivery_status='sent',
                message_id=result.get('message_sid') or result.get('email_id'),
                sent_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in handle_delivery_fallback: {exc}")
        self.retry(countdown=60 * (2 ** self.request.retries))
        return {
            'success': False,
            'error': str(exc)
        }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def check_delivery_status(self, message_id: str, delivery_method: str) -> Dict[str, Any]:
    """
    Check delivery status and handle follow-ups
    
    Args:
        message_id: Message ID to check
        delivery_method: Delivery method (sms or email)
    
    Returns:
        Dict with delivery status
    """
    try:
        if delivery_method == 'sms':
            # Check SMS delivery status via Twilio
            result = twilio_sms_service.track_delivery_status(message_id)
            
            if result.get('success'):
                status = result.get('status')
                
                # Handle failed deliveries
                if status in ['failed', 'undelivered']:
                    # Trigger fallback to email
                    handle_delivery_fallback.delay(message_id, 'email')
                
                # Handle delivered but no response
                elif status == 'delivered':
                    # Check if user responded within 24 hours
                    # This would typically check for user activity
                    pass
                
                return result
            else:
                return result
        else:
            # Email delivery status would be handled by Resend webhooks
            return {
                'success': True,
                'status': 'email_delivery_status_handled_by_webhook'
            }
            
    except Exception as exc:
        logger.error(f"Error in check_delivery_status: {exc}")
        self.retry(countdown=60 * (2 ** self.request.retries))
        return {
            'success': False,
            'error': str(exc)
        }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_follow_up_email(self, user_id: str, original_message_id: str) -> Dict[str, Any]:
    """
    Send follow-up email when SMS gets no response in 24 hours
    
    Args:
        user_id: User ID
        original_message_id: Original message ID
    
    Returns:
        Dict with follow-up delivery results
    """
    try:
        # Get database session
        db = get_db_session()
        
        # Get the original alert
        alert = db.query(FinancialAlert).filter(FinancialAlert.id == original_message_id).first()
        if not alert:
            return {
                'success': False,
                'error': f'Alert {original_message_id} not found'
            }
        
        # Get user profile
        user_profile = _get_user_profile(db, alert.user_id)
        
        # Create follow-up message
        follow_up_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>📱 Follow-up: {alert.title}</h2>
            
            <p>We sent you an SMS alert yesterday but haven't heard back. Here's the important information:</p>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Alert Details</h3>
                <p><strong>Type:</strong> {alert.alert_type.replace('_', ' ').title()}</p>
                <p><strong>Urgency:</strong> {alert.urgency_level.title()}</p>
                <p><strong>Message:</strong> {alert.message}</p>
            </div>
            
            <p><strong>What you can do:</strong></p>
            <ul>
                <li>Review your financial situation</li>
                <li>Take action if needed</li>
                <li>Contact support if you need help</li>
                <li>Update your preferences if you prefer email over SMS</li>
            </ul>
            
            <p>We're here to support your financial wellness journey!</p>
            
            <p>Best regards,<br>The MINGUS Team</p>
        </div>
        """
        
        # Send follow-up email
        result = resend_email_service.send_email(
            to_email=user_profile.email,
            subject=f"Follow-up: {alert.title}",
            html_content=follow_up_content
        )
        
        # Log follow-up attempt
        if result.get('success'):
            log_entry = AlertDeliveryLog(
                alert_id=alert.id,
                delivery_method='email',
                delivery_status='sent',
                message_id=result.get('email_id'),
                sent_at=datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in send_follow_up_email: {exc}")
        self.retry(countdown=60 * (2 ** self.request.retries))
        return {
            'success': False,
            'error': str(exc)
        }

def _send_sms_message(message: CommunicationMessage, user_profile, routing_decision) -> Dict[str, Any]:
    """Send SMS message"""
    try:
        sms_content = message.content.get('sms_message') or message.content.get('message')
        
        result = twilio_sms_service.send_sms(
            phone_number=user_profile.phone_number,
            message=sms_content,
            priority_level=getattr(twilio_sms_service.SMSPriority, message.urgency_level.value.upper()),
            template_name=message.template_name,
            template_vars=message.template_vars,
            user_id=message.user_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def _send_email_message(message: CommunicationMessage, user_profile, routing_decision) -> Dict[str, Any]:
    """Send email message"""
    try:
        email_subject = message.content.get('email_subject') or message.content.get('title', 'MINGUS Alert')
        email_content = message.content.get('email_content') or message.content.get('message', '')
        
        result = resend_email_service.send_email(
            to_email=user_profile.email,
            subject=email_subject,
            html_content=email_content
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def _get_user_profile(db: Session, user_id: str):
    """Get user profile for communication routing"""
    try:
        # Get user financial context
        context = db.query(UserFinancialContext).filter(
            UserFinancialContext.user_id == user_id
        ).first()
        
        # Get user engagement level
        engagement_level = communication_router.get_user_engagement_level(user_id)
        
        # Create user profile (simplified)
        from ..services.communication_router import UserProfile, UserEngagementLevel
        
        return UserProfile(
            user_id=user_id,
            email="user@example.com",  # Would get from user table
            phone_number=context.phone_number if context else None,
            engagement_level=UserEngagementLevel(engagement_level.value),
            income_range=context.income_range if context else "40k-60k",
            age_range=context.age_range if context else "25-35",
            sms_opted_in=True,  # Would check from user preferences
            email_opted_in=True
        )
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        # Return default profile
        from ..services.communication_router import UserProfile, UserEngagementLevel
        
        return UserProfile(
            user_id=user_id,
            email="user@example.com",
            engagement_level=UserEngagementLevel.MEDIUM,
            sms_opted_in=True,
            email_opted_in=True
        )

def _map_alert_type_to_message_type(alert_type: str) -> MessageType:
    """Map alert type to message type"""
    mapping = {
        'cash_flow': MessageType.FINANCIAL_ALERT,
        'bill_payment': MessageType.PAYMENT_REMINDER,
        'subscription': MessageType.PAYMENT_REMINDER,
        'spending_pattern': MessageType.DETAILED_ANALYSIS,
        'budget_exceeded': MessageType.FINANCIAL_ALERT,
        'emergency_fund': MessageType.FINANCIAL_ALERT
    }
    
    return mapping.get(alert_type, MessageType.FINANCIAL_ALERT) 