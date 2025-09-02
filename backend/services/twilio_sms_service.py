import logging
import os
import re
import json
import redis
import requests
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import phonenumbers
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from twilio.http.http_client import TwilioHttpClient

# Import existing services
from .resend_email_service import resend_email_service

logger = logging.getLogger(__name__)

class SMSPriority(Enum):
    """SMS priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class SMSStatus(Enum):
    """SMS delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNDELIVERED = "undelivered"
    OPTED_OUT = "opted_out"

@dataclass
class SMSTemplate:
    """SMS template configuration"""
    name: str
    message_template: str
    priority: SMSPriority
    max_retries: int = 3
    retry_delay: int = 300  # 5 minutes
    variables: List[str] = field(default_factory=list)
    cost_per_message: float = 0.0075  # Twilio US pricing
    ttl_hours: int = 24  # Template validity

@dataclass
class SMSRateLimit:
    """Rate limiting configuration"""
    regular_limit: int = 100  # SMS per minute for regular alerts
    critical_limit: int = 500  # SMS per minute for critical alerts
    window_seconds: int = 60
    burst_limit: int = 10  # Max burst for immediate sending

class TwilioSMSService:
    """Comprehensive Twilio SMS service for MINGUS financial app"""
    
    def __init__(self):
        # Twilio configuration
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Redis configuration for rate limiting and tracking
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        
        # Initialize Twilio client
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not configured")
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # Rate limiting configuration
        self.rate_limits = SMSRateLimit()
        
        # Initialize SMS templates
        self._init_sms_templates()
        
        # TCPA compliance settings
        self.tcpa_compliance = {
            'opt_in_required': True,
            'opt_out_keywords': ['STOP', 'CANCEL', 'UNSUBSCRIBE', 'QUIT', 'END'],
            'help_keywords': ['HELP', 'SUPPORT', 'INFO', 'ASSIST'],
            'opt_in_keywords': ['START', 'YES', 'SUBSCRIBE', 'JOIN'],
            'support_phone': os.getenv('MINGUS_SUPPORT_PHONE', '+1-800-MINGUS-1'),
            'support_email': os.getenv('MINGUS_SUPPORT_EMAIL', 'support@mingusapp.com')
        }
        
        # Cost tracking
        self.cost_tracking = {
            'total_cost': 0.0,
            'cost_by_template': {},
            'cost_by_month': {},
            'cost_by_user': {}
        }
    
    def _init_sms_templates(self):
        """Initialize SMS templates for financial alerts"""
        self.sms_templates = {
            'low_balance_warning': SMSTemplate(
                name='low_balance_warning',
                message_template="⚠️ MINGUS Alert: Your account balance is ${balance}. Consider transferring funds to avoid overdraft fees. Reply HELP for assistance.",
                priority=SMSPriority.URGENT,
                max_retries=3,
                variables=['balance'],
                cost_per_message=0.0075
            ),
            'payment_failure_alert': SMSTemplate(
                name='payment_failure_alert',
                message_template="🚨 CRITICAL: Your MINGUS payment of ${amount} failed. Update payment method immediately to avoid account suspension. Call {support_phone} for help.",
                priority=SMSPriority.CRITICAL,
                max_retries=5,
                variables=['amount'],
                cost_per_message=0.0075
            ),
            'bill_due_reminder': SMSTemplate(
                name='bill_due_reminder',
                message_template="📅 MINGUS Reminder: Your bill of ${amount} is due on {due_date}. Set up autopay to never miss a payment. Reply HELP for support.",
                priority=SMSPriority.MEDIUM,
                max_retries=2,
                variables=['amount', 'due_date'],
                cost_per_message=0.0075
            ),
            'weekly_checkin': SMSTemplate(
                name='weekly_checkin',
                message_template="💡 MINGUS Weekly Check-in: How's your financial wellness journey? Reply with your stress level (1-10) for personalized insights.",
                priority=SMSPriority.LOW,
                max_retries=1,
                variables=[],
                cost_per_message=0.0075
            ),
            'investment_opportunity': SMSTemplate(
                name='investment_opportunity',
                message_template="📈 MINGUS Opportunity: New investment option available for African American professionals. Learn more at mingusapp.com/investments",
                priority=SMSPriority.MEDIUM,
                max_retries=2,
                variables=[],
                cost_per_message=0.0075
            ),
            'financial_education': SMSTemplate(
                name='financial_education',
                message_template="🎓 MINGUS Education: {topic} - Build wealth while maintaining healthy relationships. Read more: mingusapp.com/learn",
                priority=SMSPriority.LOW,
                max_retries=1,
                variables=['topic'],
                cost_per_message=0.0075
            ),
            'community_event': SMSTemplate(
                name='community_event',
                message_template="🤝 MINGUS Community: Join our {event_type} event for African American professionals. Register: mingusapp.com/events",
                priority=SMSPriority.MEDIUM,
                max_retries=2,
                variables=['event_type'],
                cost_per_message=0.0075
            )
        }
    
    def send_sms(self, phone_number: str, message: str, priority_level: SMSPriority = SMSPriority.MEDIUM, 
                 template_name: str = None, template_vars: Dict[str, Any] = None, 
                 user_id: str = None) -> Dict[str, Any]:
        """
        Send SMS message with rate limiting and tracking
        
        Args:
            phone_number: Recipient phone number
            message: SMS message content
            priority_level: Message priority
            template_name: Optional template name
            template_vars: Template variables
            user_id: Optional user ID for tracking
        
        Returns:
            Dict with success status and message SID
        """
        try:
            # Validate phone number
            if not self.validate_phone_number(phone_number):
                return {
                    'success': False,
                    'error': 'Invalid phone number format',
                    'phone_number': phone_number
                }
            
            # Check TCPA compliance
            if not self._check_tcpa_compliance(phone_number, user_id):
                return {
                    'success': False,
                    'error': 'TCPA compliance check failed - user not opted in',
                    'phone_number': phone_number
                }
            
            # Check rate limiting
            if not self._check_rate_limit(priority_level):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'priority': priority_level.value
                }
            
            # Format message with template if provided
            if template_name and template_name in self.sms_templates:
                template = self.sms_templates[template_name]
                message = self._format_template_message(template, template_vars or {})
                priority_level = template.priority
            
            # Send SMS via Twilio
            if not self.client:
                return {
                    'success': False,
                    'error': 'Twilio client not configured'
                }
            
            # Create message
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=phone_number
            )
            
            # Track delivery
            message_data = {
                'message_sid': twilio_message.sid,
                'phone_number': phone_number,
                'message': message,
                'priority': priority_level.value,
                'template_name': template_name,
                'template_vars': template_vars,
                'user_id': user_id,
                'status': SMSStatus.SENT.value,
                'sent_at': datetime.utcnow().isoformat(),
                'cost': self._calculate_message_cost(template_name, priority_level)
            }
            
            self._track_delivery_status(message_data)
            self._update_cost_tracking(message_data)
            
            logger.info(f"SMS sent successfully: {twilio_message.sid} to {phone_number}")
            
            return {
                'success': True,
                'message_sid': twilio_message.sid,
                'status': 'sent',
                'cost': message_data['cost']
            }
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS: {e}")
            return {
                'success': False,
                'error': f'Twilio error: {str(e)}',
                'phone_number': phone_number
            }
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            
            # Email fallback for critical alerts
            if priority_level in [SMSPriority.CRITICAL, SMSPriority.URGENT]:
                self._send_email_fallback(phone_number, message, priority_level, user_id)
            
            return {
                'success': False,
                'error': str(e),
                'phone_number': phone_number
            }
    
    def track_delivery_status(self, message_sid: str) -> Dict[str, Any]:
        """
        Track SMS delivery status
        
        Args:
            message_sid: Twilio message SID
        
        Returns:
            Dict with delivery status and details
        """
        try:
            if not self.client:
                return {
                    'success': False,
                    'error': 'Twilio client not configured'
                }
            
            # Get message status from Twilio
            message = self.client.messages(message_sid).fetch()
            
            # Update tracking in Redis
            tracking_key = f"sms_tracking:{message_sid}"
            if self.redis_client:
                tracking_data = {
                    'status': message.status,
                    'error_code': message.error_code,
                    'error_message': message.error_message,
                    'updated_at': datetime.utcnow().isoformat()
                }
                self.redis_client.hset(tracking_key, mapping=tracking_data)
                self.redis_client.expire(tracking_key, 86400 * 30)  # 30 days
            
            return {
                'success': True,
                'message_sid': message_sid,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent.isoformat() if message.date_sent else None,
                'date_updated': message.date_updated.isoformat() if message.date_updated else None
            }
            
        except TwilioException as e:
            logger.error(f"Error tracking delivery status: {e}")
            return {
                'success': False,
                'error': f'Twilio error: {str(e)}',
                'message_sid': message_sid
            }
    
    def handle_opt_out_responses(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle SMS opt-out responses
        
        Args:
            webhook_data: Twilio webhook data
        
        Returns:
            Dict with processing result
        """
        try:
            from_number = webhook_data.get('From')
            body = webhook_data.get('Body', '').strip().upper()
            
            if not from_number:
                return {
                    'success': False,
                    'error': 'No from number provided'
                }
            
            # Check for opt-out keywords
            if body in self.tcpa_compliance['opt_out_keywords']:
                return self._process_opt_out(from_number, body)
            
            # Check for help keywords
            elif body in self.tcpa_compliance['help_keywords']:
                return self._process_help_request(from_number, body)
            
            # Check for opt-in keywords
            elif body in self.tcpa_compliance['opt_in_keywords']:
                return self._process_opt_in(from_number, body)
            
            # Handle weekly check-in responses
            elif self._is_weekly_checkin_response(body):
                return self._process_weekly_checkin(from_number, body)
            
            else:
                return self._process_unknown_response(from_number, body)
                
        except Exception as e:
            logger.error(f"Error handling opt-out response: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format and country
        
        Args:
            phone_number: Phone number to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(phone_number, None)
            
            # Check if valid
            if not phonenumbers.is_valid_number(parsed_number):
                return False
            
            # Check if it's a mobile number (optional)
            number_type = phonenumbers.number_type(parsed_number)
            if number_type not in [phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE]:
                logger.warning(f"Phone number may not be mobile: {phone_number}")
            
            # Format to E.164
            formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            
            # Check if it matches the original (after formatting)
            return formatted_number == phone_number
            
        except Exception as e:
            logger.error(f"Error validating phone number {phone_number}: {e}")
            return False
    
    def _check_rate_limit(self, priority: SMSPriority) -> bool:
        """Check if rate limit allows sending SMS"""
        if not self.redis_client:
            return True  # No Redis, skip rate limiting
        
        try:
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(seconds=self.rate_limits.window_seconds)
            
            # Determine limit based on priority
            if priority in [SMSPriority.CRITICAL, SMSPriority.URGENT]:
                limit = self.rate_limits.critical_limit
            else:
                limit = self.rate_limits.regular_limit
            
            # Count messages in current window
            rate_key = f"sms_rate_limit:{current_time.strftime('%Y%m%d%H%M')}"
            current_count = self.redis_client.get(rate_key)
            
            if current_count and int(current_count) >= limit:
                logger.warning(f"Rate limit exceeded: {current_count}/{limit}")
                return False
            
            # Increment counter
            self.redis_client.incr(rate_key)
            self.redis_client.expire(rate_key, self.rate_limits.window_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow sending if rate limiting fails
    
    def _check_identifier_rate_limit(self, identifier: str, limit_type: str = 'general') -> bool:
        """Check rate limit for specific identifier and type"""
        if not self.redis_client:
            return True  # No Redis, skip rate limiting
        
        try:
            current_time = datetime.utcnow()
            
            # Different rate limits for different types
            if limit_type == '2fa':
                # 2FA SMS: max 3 per hour per phone number
                window_seconds = 3600  # 1 hour
                max_attempts = 3
                rate_key = f"sms_2fa_rate_limit:{identifier}:{current_time.strftime('%Y%m%d%H')}"
            else:
                # General SMS: use existing logic
                window_seconds = self.rate_limits.window_seconds
                max_attempts = self.rate_limits.regular_limit
                rate_key = f"sms_rate_limit:{identifier}:{current_time.strftime('%Y%m%d%H%M')}"
            
            # Count attempts in current window
            current_count = self.redis_client.get(rate_key)
            
            if current_count and int(current_count) >= max_attempts:
                logger.warning(f"Rate limit exceeded for {limit_type}: {current_count}/{max_attempts}")
                return False
            
            # Increment counter
            self.redis_client.incr(rate_key)
            self.redis_client.expire(rate_key, window_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {limit_type}: {e}")
            return True  # Allow sending if rate limiting fails
    
    def _check_tcpa_compliance(self, phone_number: str, user_id: str = None) -> bool:
        """Check TCPA compliance for SMS sending"""
        if not self.redis_client:
            return True  # No Redis, skip compliance check
        
        try:
            # Check if user has opted in
            opt_in_key = f"sms_opt_in:{phone_number}"
            if user_id:
                opt_in_key = f"sms_opt_in:{user_id}"
            
            opt_in_status = self.redis_client.get(opt_in_key)
            
            if not opt_in_status or opt_in_status != 'opted_in':
                logger.warning(f"TCPA compliance check failed for {phone_number}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking TCPA compliance: {e}")
            return False
    
    def _track_delivery_status(self, message_data: Dict[str, Any]):
        """Track SMS delivery status in Redis"""
        if not self.redis_client:
            return
        
        try:
            tracking_key = f"sms_tracking:{message_data['message_sid']}"
            self.redis_client.hset(tracking_key, mapping=message_data)
            self.redis_client.expire(tracking_key, 86400 * 30)  # 30 days
            
            # Add to user's SMS history
            if message_data.get('user_id'):
                user_key = f"sms_history:{message_data['user_id']}"
                self.redis_client.lpush(user_key, json.dumps(message_data))
                self.redis_client.ltrim(user_key, 0, 99)  # Keep last 100 messages
                self.redis_client.expire(user_key, 86400 * 90)  # 90 days
            
        except Exception as e:
            logger.error(f"Error tracking delivery status: {e}")
    
    def _update_cost_tracking(self, message_data: Dict[str, Any]):
        """Update cost tracking metrics"""
        if not self.redis_client:
            return
        
        try:
            cost = message_data.get('cost', 0)
            template_name = message_data.get('template_name', 'custom')
            user_id = message_data.get('user_id')
            current_month = datetime.utcnow().strftime('%Y-%m')
            
            # Update total cost
            self.redis_client.incrbyfloat('sms_total_cost', cost)
            
            # Update cost by template
            template_key = f"sms_cost_template:{template_name}"
            self.redis_client.incrbyfloat(template_key, cost)
            
            # Update cost by month
            month_key = f"sms_cost_month:{current_month}"
            self.redis_client.incrbyfloat(month_key, cost)
            
            # Update cost by user
            if user_id:
                user_key = f"sms_cost_user:{user_id}"
                self.redis_client.incrbyfloat(user_key, cost)
            
        except Exception as e:
            logger.error(f"Error updating cost tracking: {e}")
    
    def _format_template_message(self, template: SMSTemplate, variables: Dict[str, Any]) -> str:
        """Format template message with variables"""
        message = template.message_template
        
        # Replace template variables
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if placeholder in message:
                message = message.replace(placeholder, str(var_value))
        
        # Replace support phone
        message = message.replace('{support_phone}', self.tcpa_compliance['support_phone'])
        
        return message
    
    def _calculate_message_cost(self, template_name: str = None, priority: SMSPriority = SMSPriority.MEDIUM) -> float:
        """Calculate message cost based on template and priority"""
        if template_name and template_name in self.sms_templates:
            return self.sms_templates[template_name].cost_per_message
        
        # Default cost based on priority
        cost_map = {
            SMSPriority.LOW: 0.0075,
            SMSPriority.MEDIUM: 0.0075,
            SMSPriority.HIGH: 0.0075,
            SMSPriority.URGENT: 0.0075,
            SMSPriority.CRITICAL: 0.0075
        }
        
        return cost_map.get(priority, 0.0075)
    
    def _send_email_fallback(self, phone_number: str, message: str, priority: SMSPriority, user_id: str = None):
        """Send email fallback for critical SMS failures"""
        try:
            # Get user email from database (simplified)
            user_email = self._get_user_email(user_id) if user_id else None
            
            if user_email:
                subject = f"URGENT: SMS Delivery Failed - {priority.value.upper()} Alert"
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #d32f2f;">🚨 SMS Delivery Failed</h2>
                    <p><strong>Phone Number:</strong> {phone_number}</p>
                    <p><strong>Priority:</strong> {priority.value.upper()}</p>
                    <p><strong>Message:</strong></p>
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                        {message}
                    </div>
                    <p><em>This is an automated fallback notification. Please contact support if you need assistance.</em></p>
                </div>
                """
                
                resend_email_service.send_email(
                    to_email=user_email,
                    subject=subject,
                    html_content=html_content
                )
                
                logger.info(f"Email fallback sent for failed SMS to {phone_number}")
            
        except Exception as e:
            logger.error(f"Error sending email fallback: {e}")
    
    def _process_opt_out(self, phone_number: str, keyword: str) -> Dict[str, Any]:
        """Process opt-out request"""
        try:
            if self.redis_client:
                # Mark as opted out
                self.redis_client.set(f"sms_opt_in:{phone_number}", "opted_out", ex=86400 * 365)  # 1 year
            
            # Send confirmation message
            confirmation = f"You have been unsubscribed from MINGUS SMS alerts. Reply START to resubscribe. For support, call {self.tcpa_compliance['support_phone']}."
            
            return {
                'success': True,
                'action': 'opted_out',
                'phone_number': phone_number,
                'confirmation_message': confirmation
            }
            
        except Exception as e:
            logger.error(f"Error processing opt-out: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_help_request(self, phone_number: str, keyword: str) -> Dict[str, Any]:
        """Process help request"""
        help_message = f"Need help? Call {self.tcpa_compliance['support_phone']} or email {self.tcpa_compliance['support_email']}. Reply STOP to unsubscribe."
        
        return {
            'success': True,
            'action': 'help_requested',
            'phone_number': phone_number,
            'help_message': help_message
        }
    
    def _process_opt_in(self, phone_number: str, keyword: str) -> Dict[str, Any]:
        """Process opt-in request"""
        try:
            if self.redis_client:
                # Mark as opted in
                self.redis_client.set(f"sms_opt_in:{phone_number}", "opted_in", ex=86400 * 365)  # 1 year
            
            welcome_message = "Welcome to MINGUS SMS alerts! You'll receive important financial updates and wellness check-ins. Reply STOP to unsubscribe anytime."
            
            return {
                'success': True,
                'action': 'opted_in',
                'phone_number': phone_number,
                'welcome_message': welcome_message
            }
            
        except Exception as e:
            logger.error(f"Error processing opt-in: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_weekly_checkin_response(self, body: str) -> bool:
        """Check if response is a weekly check-in"""
        try:
            # Check if it's a number 1-10
            stress_level = int(body)
            return 1 <= stress_level <= 10
        except ValueError:
            return False
    
    def _process_weekly_checkin(self, phone_number: str, stress_level: str) -> Dict[str, Any]:
        """Process weekly check-in response"""
        level = int(stress_level)
        
        if level <= 3:
            response = "Great! Your financial wellness is on track. Keep up the good work! 💪"
        elif level <= 6:
            response = "Thanks for checking in. Consider reviewing your budget or reaching out to our community for support. 🤝"
        else:
            response = f"We're here to help! Call {self.tcpa_compliance['support_phone']} for personalized financial guidance. You're not alone. ❤️"
        
        return {
            'success': True,
            'action': 'weekly_checkin',
            'phone_number': phone_number,
            'stress_level': level,
            'response_message': response
        }
    
    def _process_unknown_response(self, phone_number: str, body: str) -> Dict[str, Any]:
        """Process unknown response"""
        help_message = f"Thanks for your message! For support, call {self.tcpa_compliance['support_phone']} or reply HELP. Reply STOP to unsubscribe."
        
        return {
            'success': True,
            'action': 'unknown_response',
            'phone_number': phone_number,
            'help_message': help_message
        }
    
    def _get_user_email(self, user_id: str) -> Optional[str]:
        """Get user email from database (placeholder)"""
        # This would typically query the database
        # For now, return None
        return None
    
    def send_2fa_code(self, phone_number: str, code: str, user_name: str) -> Dict[str, Any]:
        """Send 2FA verification code via SMS"""
        try:
            # Check rate limiting
            if not self._check_identifier_rate_limit(phone_number, '2fa'):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded for 2FA SMS'
                }
            
            # Format message for 2FA
            message = f"Your MINGUS verification code is: {code}. This code expires in 10 minutes. Don't share this code with anyone."
            
            # Send SMS with high priority
            result = self._send_sms(phone_number, message, SMSPriority.HIGH)
            
            if result['success']:
                # Track 2FA SMS cost
                if self.redis_client:
                    self.redis_client.incrbyfloat('sms_total_cost', 0.0075)  # Twilio US pricing
                    self.redis_client.incr('sms_2fa_count')
                
                logger.info(f"2FA SMS sent to {phone_number} for user {user_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending 2FA SMS to {phone_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_sms_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get SMS statistics"""
        if not self.redis_client:
            return {'error': 'Redis not available'}
        
        try:
            stats = {
                'total_sent': 0,
                'total_delivered': 0,
                'total_failed': 0,
                'total_cost': 0.0,
                'by_template': {},
                'by_priority': {},
                'by_month': {},
                '2fa_count': 0
            }
            
            # Get total cost
            total_cost = self.redis_client.get('sms_total_cost')
            if total_cost:
                stats['total_cost'] = float(total_cost)
            
            # Get template costs
            for template_name in self.sms_templates.keys():
                template_cost = self.redis_client.get(f"sms_cost_template:{template_name}")
                if template_cost:
                    stats['by_template'][template_name] = float(template_cost)
            
            # Get 2FA SMS count
            if self.redis_client:
                stats['2fa_count'] = int(self.redis_client.get('sms_2fa_count') or 0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting SMS statistics: {e}")
            return {'error': str(e)}

# Create singleton instance
twilio_sms_service = TwilioSMSService() 