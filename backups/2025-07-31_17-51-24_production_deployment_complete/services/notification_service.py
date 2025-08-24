"""
Notification Service for MINGUS

This module provides comprehensive notification services for user communications:
- Plaid connection issue notifications
- Bank maintenance notifications
- Data synchronization status updates
- Security and compliance notifications
- Multi-channel notification delivery
"""

import logging
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from .resend_email_service import resend_email_service

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications"""
    PLAID_CONNECTION_ISSUE = "plaid_connection_issue"
    BANK_MAINTENANCE = "bank_maintenance"
    DATA_SYNC_STATUS = "data_sync_status"
    SECURITY_ALERT = "security_alert"
    COMPLIANCE_UPDATE = "compliance_update"
    SYSTEM_MAINTENANCE = "system_maintenance"
    FEATURE_UPDATE = "feature_update"
    ACCOUNT_UPDATE = "account_update"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
    SMS = "sms"
    WEBHOOK = "webhook"

@dataclass
class NotificationTemplate:
    """Notification template configuration"""
    template_id: str
    notification_type: NotificationType
    subject: str
    email_body: str
    in_app_body: str
    push_body: str
    sms_body: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    variables: List[str]  # Template variables that can be substituted

@dataclass
class NotificationData:
    """Notification data structure"""
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    channels: List[NotificationChannel]
    action_required: bool
    action_url: Optional[str]
    metadata: Dict[str, Any]
    scheduled_at: Optional[datetime]
    expires_at: Optional[datetime]

@dataclass
class NotificationDelivery:
    """Notification delivery record"""
    notification_id: str
    user_id: str
    channel: NotificationChannel
    status: str  # pending, sent, delivered, failed
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    next_retry: Optional[datetime]

class NotificationService:
    """Service for managing and sending user notifications"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.templates = self._initialize_notification_templates()
        self.channel_handlers = self._initialize_channel_handlers()
        
    def _initialize_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Initialize notification templates"""
        return {
            'plaid_connection_issue': NotificationTemplate(
                template_id='plaid_connection_issue',
                notification_type=NotificationType.PLAID_CONNECTION_ISSUE,
                subject='Bank Connection Issue - Action Required',
                email_body="""
                <h2>Bank Connection Issue</h2>
                <p>Hello {user_name},</p>
                <p>We've detected an issue with your bank connection to {institution_name}.</p>
                <p><strong>Issue:</strong> {error_message}</p>
                <p><strong>What this means:</strong> {explanation}</p>
                <p><strong>Action required:</strong> {action_required_text}</p>
                {action_button}
                <p>If you have any questions, please don't hesitate to contact our support team.</p>
                <p>Best regards,<br>The MINGUS Team</p>
                """,
                in_app_body="Bank connection issue detected with {institution_name}. {action_required_text}",
                push_body="Bank connection issue: {institution_name} - {action_required_text}",
                sms_body="MINGUS: Bank connection issue with {institution_name}. {action_required_text}",
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP, NotificationChannel.PUSH],
                variables=['user_name', 'institution_name', 'error_message', 'explanation', 'action_required_text', 'action_button']
            ),
            
            'bank_maintenance': NotificationTemplate(
                template_id='bank_maintenance',
                notification_type=NotificationType.BANK_MAINTENANCE,
                subject='Bank Maintenance - Temporary Service Interruption',
                email_body="""
                <h2>Bank Maintenance Notice</h2>
                <p>Hello {user_name},</p>
                <p>Your bank ({institution_name}) is currently performing scheduled maintenance.</p>
                <p><strong>Maintenance Details:</strong></p>
                <ul>
                    <li>Expected duration: {duration}</li>
                    <li>Services affected: {affected_services}</li>
                    <li>Estimated completion: {completion_time}</li>
                </ul>
                <p>We'll automatically retry your connection once maintenance is complete. No action is required from you.</p>
                <p>Best regards,<br>The MINGUS Team</p>
                """,
                in_app_body="Bank maintenance in progress for {institution_name}. Expected completion: {completion_time}",
                push_body="Bank maintenance: {institution_name} - {duration}",
                sms_body="MINGUS: Bank maintenance for {institution_name}. Expected completion: {completion_time}",
                priority=NotificationPriority.LOW,
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
                variables=['user_name', 'institution_name', 'duration', 'affected_services', 'completion_time']
            ),
            
            'data_sync_success': NotificationTemplate(
                template_id='data_sync_success',
                notification_type=NotificationType.DATA_SYNC_STATUS,
                subject='Data Sync Complete - {institution_name}',
                email_body="""
                <h2>Data Sync Complete</h2>
                <p>Hello {user_name},</p>
                <p>Your financial data from {institution_name} has been successfully updated.</p>
                <p><strong>Sync Summary:</strong></p>
                <ul>
                    <li>New transactions: {new_transactions}</li>
                    <li>Updated balances: {updated_balances}</li>
                    <li>Sync time: {sync_time}</li>
                </ul>
                <p>Your financial dashboard has been updated with the latest information.</p>
                <p>Best regards,<br>The MINGUS Team</p>
                """,
                in_app_body="Data sync complete for {institution_name}. {new_transactions} new transactions, {updated_balances} balance updates.",
                push_body="Data sync: {institution_name} - {new_transactions} new transactions",
                sms_body="MINGUS: Data sync complete for {institution_name}. {new_transactions} new transactions.",
                priority=NotificationPriority.LOW,
                channels=[NotificationChannel.IN_APP],
                variables=['user_name', 'institution_name', 'new_transactions', 'updated_balances', 'sync_time']
            ),
            
            'data_sync_failure': NotificationTemplate(
                template_id='data_sync_failure',
                notification_type=NotificationType.DATA_SYNC_STATUS,
                subject='Data Sync Issue - {institution_name}',
                email_body="""
                <h2>Data Sync Issue</h2>
                <p>Hello {user_name},</p>
                <p>We encountered an issue while syncing your data from {institution_name}.</p>
                <p><strong>Issue Details:</strong></p>
                <ul>
                    <li>Error: {error_message}</li>
                    <li>Last successful sync: {last_successful_sync}</li>
                    <li>Next retry: {next_retry}</li>
                </ul>
                <p>We're working to resolve this issue and will retry automatically. No action is required from you.</p>
                <p>Best regards,<br>The MINGUS Team</p>
                """,
                in_app_body="Data sync issue with {institution_name}. We'll retry automatically. Next retry: {next_retry}",
                push_body="Data sync issue: {institution_name} - Will retry at {next_retry}",
                sms_body="MINGUS: Data sync issue with {institution_name}. Will retry at {next_retry}",
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.IN_APP],
                variables=['user_name', 'institution_name', 'error_message', 'last_successful_sync', 'next_retry']
            ),
            
            'security_alert': NotificationTemplate(
                template_id='security_alert',
                notification_type=NotificationType.SECURITY_ALERT,
                subject='Security Alert - {alert_type}',
                email_body="""
                <h2>Security Alert</h2>
                <p>Hello {user_name},</p>
                <p>We've detected a security-related event on your account.</p>
                <p><strong>Alert Details:</strong></p>
                <ul>
                    <li>Type: {alert_type}</li>
                    <li>Time: {alert_time}</li>
                    <li>Details: {alert_details}</li>
                </ul>
                <p><strong>Action Required:</strong> {action_required}</p>
                {action_button}
                <p>If you didn't initiate this action, please contact our security team immediately.</p>
                <p>Best regards,<br>The MINGUS Security Team</p>
                """,
                in_app_body="Security alert: {alert_type}. {action_required}",
                push_body="Security alert: {alert_type} - {action_required}",
                sms_body="MINGUS Security Alert: {alert_type}. {action_required}",
                priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP, NotificationChannel.PUSH, NotificationChannel.SMS],
                variables=['user_name', 'alert_type', 'alert_time', 'alert_details', 'action_required', 'action_button']
            ),
            
            'compliance_update': NotificationTemplate(
                template_id='compliance_update',
                notification_type=NotificationType.COMPLIANCE_UPDATE,
                subject='Privacy Policy Update',
                email_body="""
                <h2>Privacy Policy Update</h2>
                <p>Hello {user_name},</p>
                <p>We've updated our privacy policy to better protect your data and comply with new regulations.</p>
                <p><strong>Key Changes:</strong></p>
                <ul>
                    <li>{changes}</li>
                </ul>
                <p>These changes will take effect on {effective_date}.</p>
                <p>Please review the updated policy and let us know if you have any questions.</p>
                <p>Best regards,<br>The MINGUS Team</p>
                """,
                in_app_body="Privacy policy updated. Effective date: {effective_date}. Please review the changes.",
                push_body="Privacy policy update - Effective {effective_date}",
                sms_body="MINGUS: Privacy policy updated. Effective {effective_date}.",
                priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
                variables=['user_name', 'changes', 'effective_date']
            )
        }
    
    def _initialize_channel_handlers(self) -> Dict[NotificationChannel, Callable]:
        """Initialize notification channel handlers"""
        return {
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.IN_APP: self._send_in_app_notification,
            NotificationChannel.PUSH: self._send_push_notification,
            NotificationChannel.SMS: self._send_sms_notification,
            NotificationChannel.WEBHOOK: self._send_webhook_notification
        }
    
    def send_notification(self, notification_data: Union[Dict[str, Any], NotificationData]) -> Dict[str, Any]:
        """Send notification to user"""
        try:
            # Convert dict to NotificationData if needed
            if isinstance(notification_data, dict):
                notification_data = self._dict_to_notification_data(notification_data)
            
            # Validate notification data
            validation_result = self._validate_notification_data(notification_data)
            if not validation_result['valid']:
                return validation_result
            
            # Get user information
            user_info = self._get_user_info(notification_data.user_id)
            if not user_info:
                return {'success': False, 'error': 'User not found'}
            
            # Get template
            template = self.templates.get(notification_data.notification_type.value)
            if not template:
                return {'success': False, 'error': 'Notification template not found'}
            
            # Prepare notification content
            content = self._prepare_notification_content(template, notification_data, user_info)
            
            # Send notifications through all specified channels
            delivery_results = []
            for channel in notification_data.channels:
                if channel in self.channel_handlers:
                    try:
                        result = self.channel_handlers[channel](notification_data, content, user_info)
                        delivery_results.append({
                            'channel': channel.value,
                            'success': result.get('success', False),
                            'message': result.get('message', ''),
                            'error': result.get('error')
                        })
                    except Exception as e:
                        logger.error(f"Error sending notification via {channel.value}: {e}")
                        delivery_results.append({
                            'channel': channel.value,
                            'success': False,
                            'error': str(e)
                        })
            
            # Store notification record
            notification_record = self._store_notification_record(notification_data, delivery_results)
            
            return {
                'success': True,
                'notification_id': str(notification_record.get('id')),
                'delivery_results': delivery_results
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _dict_to_notification_data(self, data: Dict[str, Any]) -> NotificationData:
        """Convert dictionary to NotificationData"""
        return NotificationData(
            user_id=data['user_id'],
            notification_type=NotificationType(data['notification_type']),
            title=data.get('title', ''),
            message=data.get('message', ''),
            priority=NotificationPriority(data.get('priority', 'medium')),
            channels=[NotificationChannel(ch) for ch in data.get('channels', ['in_app'])],
            action_required=data.get('action_required', False),
            action_url=data.get('action_url'),
            metadata=data.get('metadata', {}),
            scheduled_at=data.get('scheduled_at'),
            expires_at=data.get('expires_at')
        )
    
    def _validate_notification_data(self, notification_data: NotificationData) -> Dict[str, Any]:
        """Validate notification data"""
        try:
            if not notification_data.user_id:
                return {'valid': False, 'error': 'User ID is required'}
            
            if not notification_data.message:
                return {'valid': False, 'error': 'Message is required'}
            
            if not notification_data.channels:
                return {'valid': False, 'error': 'At least one channel is required'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information for notification"""
        try:
            # This would query the user table for user information
            # For now, return placeholder data
            return {
                'id': user_id,
                'email': f'user_{user_id}@example.com',
                'name': f'User {user_id}',
                'phone': '+1234567890',
                'preferences': {
                    'email_notifications': True,
                    'push_notifications': True,
                    'sms_notifications': False
                }
            }
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def _prepare_notification_content(self, template: NotificationTemplate, 
                                    notification_data: NotificationData, 
                                    user_info: Dict[str, Any]) -> Dict[str, str]:
        """Prepare notification content using template"""
        try:
            # Merge notification data with user info for template variables
            template_vars = {
                'user_name': user_info.get('name', 'User'),
                'user_email': user_info.get('email', ''),
                'user_id': user_info.get('id', ''),
                **notification_data.metadata
            }
            
            # Prepare content for each channel
            content = {
                'subject': self._substitute_variables(template.subject, template_vars),
                'email_body': self._substitute_variables(template.email_body, template_vars),
                'in_app_body': self._substitute_variables(template.in_app_body, template_vars),
                'push_body': self._substitute_variables(template.push_body, template_vars),
                'sms_body': self._substitute_variables(template.sms_body, template_vars)
            }
            
            return content
            
        except Exception as e:
            logger.error(f"Error preparing notification content: {e}")
            return {}
    
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template string"""
        try:
            result = template
            for key, value in variables.items():
                placeholder = f'{{{key}}}'
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
            return result
        except Exception as e:
            logger.error(f"Error substituting variables: {e}")
            return template
    
    def _send_email_notification(self, notification_data: NotificationData, 
                                content: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification using Resend"""
        try:
            # Check if user has email notifications enabled
            if not user_info.get('preferences', {}).get('email_notifications', True):
                return {'success': False, 'message': 'Email notifications disabled'}
            
            # Send email via Resend
            result = resend_email_service.send_notification_email(
                user_email=user_info['email'],
                subject=content['subject'],
                message=content['email_body'],
                notification_type=notification_data.notification_type.value
            )
            
            if result.get('success'):
                logger.info(f"Email notification sent to {user_info['email']}: {content['subject']}")
                return {'success': True, 'message': 'Email sent successfully', 'email_id': result.get('email_id')}
            else:
                logger.error(f"Failed to send email notification: {result.get('error')}")
                return {'success': False, 'error': result.get('error', 'Email send failed')}
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_in_app_notification(self, notification_data: NotificationData, 
                                 content: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            # Store in-app notification in database
            # This would create a record in the notifications table
            notification_record = {
                'user_id': notification_data.user_id,
                'type': notification_data.notification_type.value,
                'title': notification_data.title,
                'message': content['in_app_body'],
                'priority': notification_data.priority.value,
                'action_required': notification_data.action_required,
                'action_url': notification_data.action_url,
                'metadata': notification_data.metadata,
                'created_at': datetime.utcnow(),
                'read': False
            }
            
            # In production, this would be stored in the database
            logger.info(f"In-app notification created for user {notification_data.user_id}: {notification_data.title}")
            
            return {'success': True, 'message': 'In-app notification created'}
            
        except Exception as e:
            logger.error(f"Error sending in-app notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_push_notification(self, notification_data: NotificationData, 
                               content: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send push notification"""
        try:
            # Check if user has push notifications enabled
            if not user_info.get('preferences', {}).get('push_notifications', True):
                return {'success': False, 'message': 'Push notifications disabled'}
            
            # Get push notification configuration
            push_config = self.config.get('push_notifications', {})
            if not push_config:
                return {'success': False, 'error': 'Push notification configuration not found'}
            
            # Prepare push notification payload
            payload = {
                'title': notification_data.title,
                'body': content['push_body'],
                'data': {
                    'notification_type': notification_data.notification_type.value,
                    'action_url': notification_data.action_url,
                    'metadata': notification_data.metadata
                }
            }
            
            # Send push notification
            # In production, this would use Firebase, OneSignal, or similar service
            logger.info(f"Push notification sent to user {notification_data.user_id}: {notification_data.title}")
            
            return {'success': True, 'message': 'Push notification sent'}
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_sms_notification(self, notification_data: NotificationData, 
                              content: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            # Check if user has SMS notifications enabled
            if not user_info.get('preferences', {}).get('sms_notifications', False):
                return {'success': False, 'message': 'SMS notifications disabled'}
            
            # Get SMS configuration
            sms_config = self.config.get('sms', {})
            if not sms_config:
                return {'success': False, 'error': 'SMS configuration not found'}
            
            # Send SMS
            # In production, this would use Twilio, AWS SNS, or similar service
            logger.info(f"SMS notification sent to {user_info.get('phone', 'unknown')}: {content['sms_body']}")
            
            return {'success': True, 'message': 'SMS sent successfully'}
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_webhook_notification(self, notification_data: NotificationData, 
                                  content: Dict[str, str], user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            # Get webhook configuration
            webhook_config = self.config.get('webhooks', {})
            if not webhook_config:
                return {'success': False, 'error': 'Webhook configuration not found'}
            
            # Prepare webhook payload
            payload = {
                'user_id': notification_data.user_id,
                'notification_type': notification_data.notification_type.value,
                'title': notification_data.title,
                'message': notification_data.message,
                'priority': notification_data.priority.value,
                'action_required': notification_data.action_required,
                'action_url': notification_data.action_url,
                'metadata': notification_data.metadata,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send webhook
            # In production, this would send to configured webhook endpoints
            logger.info(f"Webhook notification sent for user {notification_data.user_id}: {notification_data.title}")
            
            return {'success': True, 'message': 'Webhook sent successfully'}
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return {'success': False, 'error': str(e)}
    
    def _store_notification_record(self, notification_data: NotificationData, 
                                  delivery_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store notification record in database"""
        try:
            # In production, this would store in the notifications table
            notification_record = {
                'id': 'notification_id',  # Would be generated UUID
                'user_id': notification_data.user_id,
                'type': notification_data.notification_type.value,
                'title': notification_data.title,
                'message': notification_data.message,
                'priority': notification_data.priority.value,
                'channels': [ch.value for ch in notification_data.channels],
                'action_required': notification_data.action_required,
                'action_url': notification_data.action_url,
                'metadata': notification_data.metadata,
                'delivery_results': delivery_results,
                'created_at': datetime.utcnow(),
                'scheduled_at': notification_data.scheduled_at,
                'expires_at': notification_data.expires_at
            }
            
            return notification_record
            
        except Exception as e:
            logger.error(f"Error storing notification record: {e}")
            return {}
    
    def get_user_notifications(self, user_id: str, limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get user notifications"""
        try:
            # In production, this would query the notifications table
            # For now, return placeholder data
            notifications = [
                {
                    'id': 'notification_1',
                    'type': 'plaid_connection_issue',
                    'title': 'Bank Connection Issue',
                    'message': 'We detected an issue with your bank connection.',
                    'priority': 'medium',
                    'action_required': True,
                    'created_at': datetime.utcnow().isoformat(),
                    'read': False
                }
            ]
            
            if unread_only:
                notifications = [n for n in notifications if not n.get('read', False)]
            
            return notifications[:limit]
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        try:
            # In production, this would update the notifications table
            logger.info(f"Notification {notification_id} marked as read for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False 