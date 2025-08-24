"""
Communication Preference Management Service
Handles user communication preferences, consent management, and compliance
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import pytz
import re
import json

from ..models.communication_preferences import (
    CommunicationPreferences, SMSConsent, ConsentRecord, AlertTypePreference,
    DeliveryLog, OptOutHistory, UserEngagementMetrics, CommunicationPolicy,
    CommunicationChannel, AlertType, FrequencyType, ConsentStatus, UserSegment
)
from ..models.user import User
from ..database import get_db_session

logger = logging.getLogger(__name__)


class CommunicationPreferenceService:
    """Service for managing user communication preferences and consent"""
    
    def __init__(self, db_session: Optional[Session] = None):
        if db_session is not None:
            self.db = db_session
        else:
            try:
                self.db = get_db_session()
            except Exception:
                self.db = None  # type: ignore
    
    def get_user_communication_prefs(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user communication preferences
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user preferences or None if not found
        """
        try:
            preferences = self.db.query(CommunicationPreferences).filter(
                CommunicationPreferences.user_id == user_id
            ).first()
            
            if not preferences:
                return None
            
            return {
                'id': preferences.id,
                'user_id': preferences.user_id,
                'sms_enabled': preferences.sms_enabled,
                'email_enabled': preferences.email_enabled,
                'push_enabled': preferences.push_enabled,
                'in_app_enabled': preferences.in_app_enabled,
                'preferred_sms_time': preferences.preferred_sms_time.strftime('%H:%M') if preferences.preferred_sms_time else None,
                'preferred_email_day': preferences.preferred_email_day,
                'alert_types_sms': preferences.alert_types_sms,
                'alert_types_email': preferences.alert_types_email,
                'frequency_preference': preferences.frequency_preference.value if preferences.frequency_preference else None,
                'financial_alerts_enabled': preferences.financial_alerts_enabled,
                'career_content_enabled': preferences.career_content_enabled,
                'wellness_content_enabled': preferences.wellness_content_enabled,
                'marketing_content_enabled': preferences.marketing_content_enabled,
                'preferred_email_time': preferences.preferred_email_time.strftime('%H:%M') if preferences.preferred_email_time else None,
                'timezone': preferences.timezone,
                'user_segment': preferences.user_segment.value if preferences.user_segment else None,
                'auto_adjust_frequency': preferences.auto_adjust_frequency,
                'engagement_based_optimization': preferences.engagement_based_optimization,
                'created_at': preferences.created_at.isoformat() if preferences.created_at else None,
                'updated_at': preferences.updated_at.isoformat() if preferences.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting user communication preferences: {e}")
            return None
    
    def update_user_preferences(self, user_id: int, preferences_dict: Dict[str, Any]) -> bool:
        """
        Update user communication preferences
        
        Args:
            user_id: User ID
            preferences_dict: Dictionary with preference updates
            
        Returns:
            Success status
        """
        try:
            preferences = self.db.query(CommunicationPreferences).filter(
                CommunicationPreferences.user_id == user_id
            ).first()
            
            if not preferences:
                # Create new preferences with defaults
                preferences = self._create_default_preferences(user_id)
            
            # Update fields
            for key, value in preferences_dict.items():
                if hasattr(preferences, key):
                    if key in ['preferred_sms_time', 'preferred_email_time'] and value:
                        # Convert string time to time object
                        if isinstance(value, str):
                            time_obj = datetime.strptime(value, '%H:%M').time()
                            setattr(preferences, key, time_obj)
                        else:
                            setattr(preferences, key, value)
                    elif key == 'user_segment' and value:
                        setattr(preferences, key, UserSegment(value))
                    elif key == 'frequency_preference' and value:
                        setattr(preferences, key, FrequencyType(value))
                    else:
                        setattr(preferences, key, value)
            
            preferences.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Updated communication preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            self.db.rollback()
            return False
    
    def check_consent_for_message_type(self, user_id: int, message_type: str, channel: CommunicationChannel) -> Tuple[bool, str]:
        """
        Check if user has consented to receive a specific message type on a specific channel
        
        Args:
            user_id: User ID
            message_type: Type of message (alert type)
            channel: Communication channel
            
        Returns:
            Tuple of (can_send, reason)
        """
        try:
            # Check if user exists
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found"
            
            # Get communication preferences
            preferences = self.db.query(CommunicationPreferences).filter(
                CommunicationPreferences.user_id == user_id
            ).first()
            
            if not preferences:
                return False, "No communication preferences found"
            
            # Check channel-specific consent
            if channel == CommunicationChannel.SMS:
                if not preferences.sms_enabled:
                    return False, "SMS communications disabled"
                
                # Check SMS consent
                sms_consent = self.db.query(SMSConsent).filter(
                    and_(
                        SMSConsent.user_id == user_id,
                        SMSConsent.consent_granted == True,
                        SMSConsent.opted_out == False
                    )
                ).first()
                
                if not sms_consent:
                    return False, "SMS consent not granted"
                
                # Check alert type preference
                if preferences.alert_types_sms and message_type in preferences.alert_types_sms:
                    if not preferences.alert_types_sms[message_type]:
                        return False, f"SMS alerts for {message_type} disabled"
                
            elif channel == CommunicationChannel.EMAIL:
                if not preferences.email_enabled:
                    return False, "Email communications disabled"
                
                # Check email consent
                email_consent = self.db.query(ConsentRecord).filter(
                    and_(
                        ConsentRecord.user_id == user_id,
                        ConsentRecord.consent_type == 'email',
                        ConsentRecord.consent_status == ConsentStatus.GRANTED
                    )
                ).first()
                
                if not email_consent:
                    return False, "Email consent not granted"
                
                # Check alert type preference
                if preferences.alert_types_email and message_type in preferences.alert_types_email:
                    if not preferences.alert_types_email[message_type]:
                        return False, f"Email alerts for {message_type} disabled"
            
            # Check opt-out history
            recent_optout = self.db.query(OptOutHistory).filter(
                and_(
                    OptOutHistory.user_id == user_id,
                    OptOutHistory.channel == channel,
                    or_(
                        OptOutHistory.alert_type == AlertType(message_type),
                        OptOutHistory.alert_type.is_(None)  # Global opt-out
                    ),
                    OptOutHistory.opted_out_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).first()
            
            if recent_optout:
                return False, f"User opted out of {channel.value} communications"
            
            return True, "Consent verified"
            
        except Exception as e:
            logger.error(f"Error checking consent: {e}")
            return False, f"Error checking consent: {str(e)}"
    
    def handle_opt_out_request(self, user_id: int, channel: CommunicationChannel, message_type: Optional[str] = None, reason: Optional[str] = None) -> bool:
        """
        Handle user opt-out request
        
        Args:
            user_id: User ID
            channel: Communication channel
            message_type: Specific message type (optional)
            reason: Opt-out reason (optional)
            
        Returns:
            Success status
        """
        try:
            # Create opt-out record
            opt_out = OptOutHistory(
                id=str(uuid.uuid4()),
                user_id=user_id,
                channel=channel,
                alert_type=AlertType(message_type) if message_type else None,
                reason=reason,
                method='api',
                source='api'
            )
            
            self.db.add(opt_out)
            
            # Update preferences if needed
            preferences = self.db.query(CommunicationPreferences).filter(
                CommunicationPreferences.user_id == user_id
            ).first()
            
            if preferences:
                if channel == CommunicationChannel.SMS:
                    preferences.sms_enabled = False
                    if message_type and preferences.alert_types_sms:
                        preferences.alert_types_sms[message_type] = False
                elif channel == CommunicationChannel.EMAIL:
                    preferences.email_enabled = False
                    if message_type and preferences.alert_types_email:
                        preferences.alert_types_email[message_type] = False
                
                preferences.updated_at = datetime.utcnow()
            
            # Update SMS consent if applicable
            if channel == CommunicationChannel.SMS:
                sms_consent = self.db.query(SMSConsent).filter(
                    SMSConsent.user_id == user_id
                ).first()
                
                if sms_consent:
                    sms_consent.opted_out = True
                    sms_consent.opted_out_at = datetime.utcnow()
                    sms_consent.opt_out_reason = reason
                    sms_consent.opt_out_method = 'api'
            
            self.db.commit()
            
            logger.info(f"User {user_id} opted out of {channel.value} communications")
            return True
            
        except Exception as e:
            logger.error(f"Error handling opt-out request: {e}")
            self.db.rollback()
            return False
    
    def get_optimal_send_time(self, user_id: int, channel: CommunicationChannel) -> Optional[datetime]:
        """
        Get optimal send time for user based on preferences and engagement
        
        Args:
            user_id: User ID
            channel: Communication channel
            
        Returns:
            Optimal send time or None
        """
        try:
            preferences = self.db.query(CommunicationPreferences).filter(
                CommunicationPreferences.user_id == user_id
            ).first()
            
            if not preferences:
                return None
            
            # Get user's timezone
            user_tz = pytz.timezone(preferences.timezone or 'UTC')
            now = datetime.now(user_tz)
            
            if channel == CommunicationChannel.SMS:
                # Use preferred SMS time
                if preferences.preferred_sms_time:
                    optimal_time = now.replace(
                        hour=preferences.preferred_sms_time.hour,
                        minute=preferences.preferred_sms_time.minute,
                        second=0,
                        microsecond=0
                    )
                    
                    # If optimal time has passed today, schedule for tomorrow
                    if optimal_time <= now:
                        optimal_time += timedelta(days=1)
                    
                    return optimal_time
                    
            elif channel == CommunicationChannel.EMAIL:
                # Use preferred email day and time
                if preferences.preferred_email_time:
                    # Calculate days until preferred day
                    current_day = now.weekday()
                    preferred_day = preferences.preferred_email_day
                    
                    days_ahead = preferred_day - current_day
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    
                    optimal_time = now.replace(
                        hour=preferences.preferred_email_time.hour,
                        minute=preferences.preferred_email_time.minute,
                        second=0,
                        microsecond=0
                    ) + timedelta(days=days_ahead)
                    
                    return optimal_time
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting optimal send time: {e}")
            return None
    
    def create_user_preferences(self, user_id: int, user_segment: UserSegment = UserSegment.NEW_USER) -> CommunicationPreferences:
        """
        Create default communication preferences for a new user
        
        Args:
            user_id: User ID
            user_segment: User segment for default preferences
            
        Returns:
            Created preferences object
        """
        try:
            # Get smart defaults based on user segment
            defaults = self._get_smart_defaults(user_segment)
            
            preferences = CommunicationPreferences(
                id=str(uuid.uuid4()),
                user_id=user_id,
                user_segment=user_segment,
                **defaults
            )
            
            self.db.add(preferences)
            
            # Create default alert type preferences
            self._create_default_alert_preferences(user_id, preferences.id, user_segment)
            
            # Create engagement metrics
            self._create_engagement_metrics(user_id)
            
            self.db.commit()
            
            logger.info(f"Created communication preferences for user {user_id}")
            return preferences
            
        except Exception as e:
            logger.error(f"Error creating user preferences: {e}")
            self.db.rollback()
            raise
    
    def grant_sms_consent(self, user_id: int, phone_number: str, consent_source: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> SMSConsent:
        """
        Grant SMS consent for TCPA compliance
        
        Args:
            user_id: User ID
            phone_number: Phone number
            consent_source: Source of consent
            ip_address: IP address (optional)
            user_agent: User agent (optional)
            
        Returns:
            SMS consent object
        """
        try:
            # Validate phone number format
            if not self._validate_phone_number(phone_number):
                raise ValueError("Invalid phone number format")
            
            # Create or update SMS consent
            sms_consent = self.db.query(SMSConsent).filter(
                SMSConsent.user_id == user_id
            ).first()
            
            if sms_consent:
                # Update existing consent
                sms_consent.phone_number = phone_number
                sms_consent.consent_granted = True
                sms_consent.consent_granted_at = datetime.utcnow()
                sms_consent.consent_source = consent_source
                sms_consent.ip_address = ip_address
                sms_consent.user_agent = user_agent
                sms_consent.opted_out = False
                sms_consent.opted_out_at = None
                sms_consent.opt_out_reason = None
                sms_consent.opt_out_method = None
            else:
                # Create new consent
                sms_consent = SMSConsent(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    phone_number=phone_number,
                    consent_granted=True,
                    consent_granted_at=datetime.utcnow(),
                    consent_source=consent_source,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                self.db.add(sms_consent)
            
            # Update user's phone number if needed
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and not user.phone_number:
                user.phone_number = phone_number
            
            self.db.commit()
            
            logger.info(f"Granted SMS consent for user {user_id}")
            return sms_consent
            
        except Exception as e:
            logger.error(f"Error granting SMS consent: {e}")
            self.db.rollback()
            raise
    
    def verify_phone_number(self, user_id: int, verification_code: str) -> bool:
        """
        Verify phone number with SMS code
        
        Args:
            user_id: User ID
            verification_code: Verification code
            
        Returns:
            Success status
        """
        try:
            sms_consent = self.db.query(SMSConsent).filter(
                and_(
                    SMSConsent.user_id == user_id,
                    SMSConsent.verification_code == verification_code,
                    SMSConsent.verification_expires_at > datetime.utcnow()
                )
            ).first()
            
            if sms_consent:
                sms_consent.phone_verified = True
                sms_consent.verified_at = datetime.utcnow()
                sms_consent.verification_code = None
                sms_consent.verification_expires_at = None
                
                self.db.commit()
                
                logger.info(f"Phone number verified for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying phone number: {e}")
            self.db.rollback()
            return False
    
    def log_delivery(self, user_id: int, alert_type: AlertType, channel: CommunicationChannel, 
                    message_id: Optional[str] = None, status: str = "sent") -> DeliveryLog:
        """
        Log communication delivery
        
        Args:
            user_id: User ID
            alert_type: Type of alert
            channel: Communication channel
            message_id: External service message ID
            status: Delivery status
            
        Returns:
            Delivery log object
        """
        try:
            preferences = self.db.query(CommunicationPreferences).filter(
                CommunicationPreferences.user_id == user_id
            ).first()
            
            delivery_log = DeliveryLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                preferences_id=preferences.id if preferences else None,
                alert_type=alert_type,
                channel=channel,
                message_id=message_id,
                status=status,
                sent_at=datetime.utcnow()
            )
            
            self.db.add(delivery_log)
            self.db.commit()
            
            logger.info(f"Logged delivery for user {user_id}, {alert_type.value}, {channel.value}")
            return delivery_log
            
        except Exception as e:
            logger.error(f"Error logging delivery: {e}")
            self.db.rollback()
            raise
    
    def get_user_engagement_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get user engagement summary
        
        Args:
            user_id: User ID
            
        Returns:
            Engagement summary dictionary
        """
        try:
            metrics = self.db.query(UserEngagementMetrics).filter(
                UserEngagementMetrics.user_id == user_id
            ).first()
            
            if not metrics:
                return {}
            
            return {
                'total_messages_sent': metrics.total_messages_sent,
                'total_messages_opened': metrics.total_messages_opened,
                'total_messages_clicked': metrics.total_messages_clicked,
                'total_messages_responded': metrics.total_messages_responded,
                'sms_engagement_rate': metrics.sms_engagement_rate,
                'email_engagement_rate': metrics.email_engagement_rate,
                'push_engagement_rate': metrics.push_engagement_rate,
                'alert_type_engagement': metrics.alert_type_engagement,
                'optimal_send_times': metrics.optimal_send_times,
                'current_frequency': metrics.current_frequency,
                'recommended_frequency': metrics.recommended_frequency,
                'last_engagement_at': metrics.last_engagement_at.isoformat() if metrics.last_engagement_at else None,
                'engagement_trend': metrics.engagement_trend
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement summary: {e}")
            return {}
    
    def get_compliance_report(self, user_id: int) -> Dict[str, Any]:
        """
        Get compliance report for user
        
        Args:
            user_id: User ID
            
        Returns:
            Compliance report dictionary
        """
        try:
            # Get SMS consent
            sms_consent = self.db.query(SMSConsent).filter(
                SMSConsent.user_id == user_id
            ).first()
            
            # Get email consent
            email_consent = self.db.query(ConsentRecord).filter(
                and_(
                    ConsentRecord.user_id == user_id,
                    ConsentRecord.consent_type == 'email'
                )
            ).first()
            
            # Get opt-out history
            opt_outs = self.db.query(OptOutHistory).filter(
                OptOutHistory.user_id == user_id
            ).all()
            
            # Get delivery logs
            delivery_logs = self.db.query(DeliveryLog).filter(
                DeliveryLog.user_id == user_id
            ).order_by(DeliveryLog.created_at.desc()).limit(10).all()
            
            return {
                'sms_consent': {
                    'granted': sms_consent.consent_granted if sms_consent else False,
                    'granted_at': sms_consent.consent_granted_at.isoformat() if sms_consent and sms_consent.consent_granted_at else None,
                    'phone_verified': sms_consent.phone_verified if sms_consent else False,
                    'opted_out': sms_consent.opted_out if sms_consent else False,
                    'opted_out_at': sms_consent.opted_out_at.isoformat() if sms_consent and sms_consent.opted_out_at else None
                },
                'email_consent': {
                    'status': email_consent.consent_status.value if email_consent else None,
                    'granted_at': email_consent.granted_at.isoformat() if email_consent and email_consent.granted_at else None,
                    'revoked_at': email_consent.revoked_at.isoformat() if email_consent and email_consent.revoked_at else None
                },
                'opt_outs': [
                    {
                        'channel': opt_out.channel.value,
                        'alert_type': opt_out.alert_type.value if opt_out.alert_type else 'all',
                        'opted_out_at': opt_out.opted_out_at.isoformat(),
                        'reason': opt_out.reason
                    }
                    for opt_out in opt_outs
                ],
                'recent_deliveries': [
                    {
                        'alert_type': log.alert_type.value,
                        'channel': log.channel.value,
                        'status': log.status,
                        'sent_at': log.sent_at.isoformat() if log.sent_at else None
                    }
                    for log in delivery_logs
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting compliance report: {e}")
            return {}
    
    def _create_default_preferences(self, user_id: int) -> CommunicationPreferences:
        """Create default preferences object"""
        return CommunicationPreferences(
            id=str(uuid.uuid4()),
            user_id=user_id,
            sms_enabled=True,
            email_enabled=True,
            push_enabled=False,
            in_app_enabled=True,
            preferred_sms_time=time(9, 0),  # 9:00 AM
            preferred_email_day=1,  # Tuesday
            alert_types_sms={
                "critical_financial": True,
                "bill_reminders": True,
                "budget_alerts": True,
                "emergency_fund": True,
                "daily_checkin": False,
                "weekly_report": False,
                "monthly_analysis": False,
                "career_insights": False,
                "wellness_tips": False,
                "spending_patterns": False,
                "subscription_updates": False,
                "marketing_content": False
            },
            alert_types_email={
                "critical_financial": True,
                "bill_reminders": True,
                "budget_alerts": True,
                "emergency_fund": True,
                "daily_checkin": True,
                "weekly_report": True,
                "monthly_analysis": True,
                "career_insights": True,
                "wellness_tips": True,
                "spending_patterns": True,
                "subscription_updates": True,
                "marketing_content": False
            },
            frequency_preference=FrequencyType.WEEKLY,
            financial_alerts_enabled=True,
            career_content_enabled=True,
            wellness_content_enabled=True,
            marketing_content_enabled=False,
            preferred_email_time=time(18, 0),  # 6:00 PM
            timezone="UTC",
            user_segment=UserSegment.NEW_USER,
            auto_adjust_frequency=True,
            engagement_based_optimization=True
        )
    
    def _get_smart_defaults(self, user_segment: UserSegment) -> Dict[str, Any]:
        """Get smart defaults based on user segment"""
        defaults = {
            UserSegment.NEW_USER: {
                'sms_enabled': True,
                'email_enabled': True,
                'alert_types_sms': {
                    "critical_financial": True,
                    "bill_reminders": True,
                    "budget_alerts": True,
                    "emergency_fund": True,
                    "daily_checkin": False,
                    "weekly_report": False,
                    "monthly_analysis": False,
                    "career_insights": False,
                    "wellness_tips": False,
                    "spending_patterns": False,
                    "subscription_updates": False,
                    "marketing_content": False
                },
                'alert_types_email': {
                    "critical_financial": True,
                    "bill_reminders": True,
                    "budget_alerts": True,
                    "emergency_fund": True,
                    "daily_checkin": True,
                    "weekly_report": True,
                    "monthly_analysis": True,
                    "career_insights": True,
                    "wellness_tips": True,
                    "spending_patterns": True,
                    "subscription_updates": True,
                    "marketing_content": False
                },
                'frequency_preference': FrequencyType.WEEKLY
            },
            UserSegment.PREMIUM_SUBSCRIBER: {
                'sms_enabled': True,
                'email_enabled': True,
                'alert_types_sms': {
                    "critical_financial": True,
                    "bill_reminders": True,
                    "budget_alerts": True,
                    "emergency_fund": True,
                    "daily_checkin": True,
                    "weekly_report": True,
                    "monthly_analysis": True,
                    "career_insights": True,
                    "wellness_tips": True,
                    "spending_patterns": True,
                    "subscription_updates": True,
                    "marketing_content": True
                },
                'alert_types_email': {
                    "critical_financial": True,
                    "bill_reminders": True,
                    "budget_alerts": True,
                    "emergency_fund": True,
                    "daily_checkin": True,
                    "weekly_report": True,
                    "monthly_analysis": True,
                    "career_insights": True,
                    "wellness_tips": True,
                    "spending_patterns": True,
                    "subscription_updates": True,
                    "marketing_content": True
                },
                'frequency_preference': FrequencyType.DAILY
            },
            UserSegment.AT_RISK_USER: {
                'sms_enabled': True,
                'email_enabled': False,
                'alert_types_sms': {
                    "critical_financial": True,
                    "bill_reminders": True,
                    "budget_alerts": True,
                    "emergency_fund": True,
                    "daily_checkin": True,
                    "weekly_report": False,
                    "monthly_analysis": False,
                    "career_insights": False,
                    "wellness_tips": False,
                    "spending_patterns": False,
                    "subscription_updates": False,
                    "marketing_content": False
                },
                'alert_types_email': {
                    "critical_financial": False,
                    "bill_reminders": False,
                    "budget_alerts": False,
                    "emergency_fund": False,
                    "daily_checkin": False,
                    "weekly_report": False,
                    "monthly_analysis": False,
                    "career_insights": False,
                    "wellness_tips": False,
                    "spending_patterns": False,
                    "subscription_updates": False,
                    "marketing_content": False
                },
                'frequency_preference': FrequencyType.DAILY
            },
            UserSegment.HIGH_ENGAGEMENT: {
                'sms_enabled': True,
                'email_enabled': True,
                'alert_types_sms': {
                    "critical_financial": True,
                    "bill_reminders": True,
                    "budget_alerts": True,
                    "emergency_fund": True,
                    "daily_checkin": True,
                    "weekly_report": True,
                    "monthly_analysis": True,
                    "career_insights": True,
                    "wellness_tips": True,
                    "spending_patterns": True,
                    "subscription_updates": True,
                    "marketing_content": True
                },
                'alert_types_email': {
                    "critical_financial": True,
                    "bill_reminders": True,
                    "budget_alerts": True,
                    "emergency_fund": True,
                    "daily_checkin": True,
                    "weekly_report": True,
                    "monthly_analysis": True,
                    "career_insights": True,
                    "wellness_tips": True,
                    "spending_patterns": True,
                    "subscription_updates": True,
                    "marketing_content": True
                },
                'frequency_preference': FrequencyType.DAILY
            }
        }
        
        return defaults.get(user_segment, defaults[UserSegment.NEW_USER])
    
    def _create_default_alert_preferences(self, user_id: int, preferences_id: str, user_segment: UserSegment) -> None:
        """Create default alert type preferences"""
        alert_types = [
            AlertType.CRITICAL_FINANCIAL,
            AlertType.DAILY_CHECKIN,
            AlertType.WEEKLY_REPORT,
            AlertType.MONTHLY_ANALYSIS,
            AlertType.CAREER_INSIGHTS,
            AlertType.WELLNESS_TIPS,
            AlertType.BILL_REMINDERS,
            AlertType.BUDGET_ALERTS,
            AlertType.SPENDING_PATTERNS,
            AlertType.EMERGENCY_FUND,
            AlertType.SUBSCRIPTION_UPDATES,
            AlertType.MARKETING_CONTENT
        ]
        
        for alert_type in alert_types:
            preference = AlertTypePreference(
                id=str(uuid.uuid4()),
                user_id=user_id,
                preferences_id=preferences_id,
                alert_type=alert_type,
                sms_enabled=True,
                email_enabled=True,
                push_enabled=False,
                in_app_enabled=True,
                frequency=FrequencyType.WEEKLY,
                priority=5
            )
            self.db.add(preference)
    
    def _create_engagement_metrics(self, user_id: int) -> None:
        """Create engagement metrics for user"""
        metrics = UserEngagementMetrics(
            id=str(uuid.uuid4()),
            user_id=user_id,
            total_messages_sent=0,
            total_messages_opened=0,
            total_messages_clicked=0,
            total_messages_responded=0,
            sms_engagement_rate=0,
            email_engagement_rate=0,
            push_engagement_rate=0,
            alert_type_engagement={},
            optimal_send_times={},
            current_frequency="weekly",
            engagement_trend="stable"
        )
        self.db.add(metrics)
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        # Basic US phone number validation
        pattern = r'^\+?1?\d{10,15}$'
        return bool(re.match(pattern, phone_number))


# Global service instance (optional)
try:
    communication_preference_service = CommunicationPreferenceService()
except Exception:
    communication_preference_service = None