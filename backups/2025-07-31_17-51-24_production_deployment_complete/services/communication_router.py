import logging
import json
import redis
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from celery import Celery, current_task
from celery.utils.log import get_task_logger
import os

# Import existing services
from .twilio_sms_service import twilio_sms_service, SMSPriority
from .resend_email_service import resend_email_service

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Message types for routing decisions"""
    # SMS-optimized messages
    FINANCIAL_ALERT = "financial_alert"
    PAYMENT_REMINDER = "payment_reminder"
    QUICK_CHECKIN = "quick_checkin"
    SECURITY_ALERT = "security_alert"
    LOW_BALANCE_WARNING = "low_balance_warning"
    PAYMENT_FAILURE = "payment_failure"
    
    # Email-optimized messages
    MONTHLY_REPORT = "monthly_report"
    CAREER_INSIGHTS = "career_insights"
    EDUCATIONAL_CONTENT = "educational_content"
    DETAILED_ANALYSIS = "detailed_analysis"
    FINANCIAL_EDUCATION = "financial_education"
    COMMUNITY_EVENT = "community_event"
    INVESTMENT_OPPORTUNITY = "investment_opportunity"

class UrgencyLevel(Enum):
    """Message urgency levels"""
    CRITICAL = "critical"      # SMS immediately
    HIGH = "high"             # SMS within 1 hour
    MEDIUM = "medium"         # SMS daily batch
    LOW = "low"               # Email weekly

class UserEngagementLevel(Enum):
    """User engagement levels"""
    HIGH = "high"             # More emails, fewer SMS
    MEDIUM = "medium"         # Balanced approach
    LOW = "low"               # More SMS for re-engagement
    AT_RISK = "at_risk"       # Critical SMS only

class CommunicationChannel(Enum):
    """Communication channels"""
    SMS = "sms"
    EMAIL = "email"
    BOTH = "both"
    NONE = "none"

@dataclass
class UserProfile:
    """User profile for communication routing"""
    user_id: str
    email: str
    phone_number: Optional[str] = None
    engagement_level: UserEngagementLevel = UserEngagementLevel.MEDIUM
    income_range: str = "40k-60k"  # 40k-60k, 60k-80k, 80k-100k
    age_range: str = "25-35"       # 25-35, 35-45, 45+
    cultural_preferences: Dict[str, Any] = field(default_factory=dict)
    communication_preferences: Dict[str, Any] = field(default_factory=dict)
    last_activity: Optional[datetime] = None
    sms_opted_in: bool = False
    email_opted_in: bool = True

@dataclass
class CommunicationMessage:
    """Communication message for routing"""
    message_id: str
    user_id: str
    message_type: MessageType
    urgency_level: UrgencyLevel
    content: Dict[str, Any]
    template_name: Optional[str] = None
    template_vars: Dict[str, Any] = field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    max_retries: int = 3
    retry_delay: int = 300  # 5 minutes
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class RoutingDecision:
    """Routing decision for a message"""
    channel: CommunicationChannel
    priority: str
    delay_seconds: int = 0
    batch_key: Optional[str] = None
    fallback_channel: Optional[CommunicationChannel] = None
    reasoning: str = ""

class CommunicationRouter:
    """Intelligent communication channel router for MINGUS"""
    
    def __init__(self):
        # Redis configuration
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        
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
        
        # Message type to channel mapping
        self.message_type_routing = {
            # SMS-optimized messages
            MessageType.FINANCIAL_ALERT: CommunicationChannel.SMS,
            MessageType.PAYMENT_REMINDER: CommunicationChannel.SMS,
            MessageType.QUICK_CHECKIN: CommunicationChannel.SMS,
            MessageType.SECURITY_ALERT: CommunicationChannel.SMS,
            MessageType.LOW_BALANCE_WARNING: CommunicationChannel.SMS,
            MessageType.PAYMENT_FAILURE: CommunicationChannel.SMS,
            
            # Email-optimized messages
            MessageType.MONTHLY_REPORT: CommunicationChannel.EMAIL,
            MessageType.CAREER_INSIGHTS: CommunicationChannel.EMAIL,
            MessageType.EDUCATIONAL_CONTENT: CommunicationChannel.EMAIL,
            MessageType.DETAILED_ANALYSIS: CommunicationChannel.EMAIL,
            MessageType.FINANCIAL_EDUCATION: CommunicationChannel.EMAIL,
            MessageType.COMMUNITY_EVENT: CommunicationChannel.EMAIL,
            MessageType.INVESTMENT_OPPORTUNITY: CommunicationChannel.EMAIL,
        }
        
        # Urgency level to delay mapping
        self.urgency_delays = {
            UrgencyLevel.CRITICAL: 0,      # Immediate
            UrgencyLevel.HIGH: 3600,       # 1 hour
            UrgencyLevel.MEDIUM: 86400,    # 24 hours (daily batch)
            UrgencyLevel.LOW: 604800,      # 1 week
        }
        
        # Cultural personalization for African American professionals
        self.cultural_context = {
            'age_25_35': {
                'career_focus': 'career_advancement',
                'financial_goals': ['home_ownership', 'student_loan_payoff', 'emergency_fund'],
                'communication_style': 'direct_and_supportive',
                'community_emphasis': True,
                'representation_matters': True
            },
            'income_40k_60k': {
                'financial_priorities': ['budgeting', 'debt_management', 'savings'],
                'investment_approach': 'conservative',
                'education_focus': 'basic_financial_literacy'
            },
            'income_60k_80k': {
                'financial_priorities': ['investing', 'retirement_planning', 'wealth_building'],
                'investment_approach': 'moderate',
                'education_focus': 'advanced_financial_strategies'
            },
            'income_80k_100k': {
                'financial_priorities': ['wealth_preservation', 'tax_optimization', 'legacy_planning'],
                'investment_approach': 'aggressive',
                'education_focus': 'sophisticated_investment_strategies'
            }
        }
    
    def route_message(self, message: CommunicationMessage, user_profile: UserProfile) -> RoutingDecision:
        """
        Route a message to the appropriate communication channel
        
        Args:
            message: Communication message
            user_profile: User profile for routing decisions
        
        Returns:
            Routing decision with channel and timing
        """
        try:
            # Base routing by message type
            base_channel = self.message_type_routing.get(message.message_type, CommunicationChannel.EMAIL)
            
            # Adjust based on user engagement level
            engagement_adjusted_channel = self._adjust_for_engagement(base_channel, user_profile.engagement_level)
            
            # Adjust based on urgency level
            urgency_adjusted_channel = self._adjust_for_urgency(engagement_adjusted_channel, message.urgency_level)
            
            # Apply cultural personalization
            culturally_adjusted_channel = self._apply_cultural_personalization(
                urgency_adjusted_channel, user_profile, message
            )
            
            # Check user preferences and opt-in status
            final_channel = self._check_user_preferences(culturally_adjusted_channel, user_profile)
            
            # Determine delay and batching
            delay_seconds = self._calculate_delay(message.urgency_level, user_profile)
            batch_key = self._get_batch_key(message, user_profile)
            
            # Determine fallback channel
            fallback_channel = self._determine_fallback_channel(final_channel, message.urgency_level)
            
            # Generate reasoning
            reasoning = self._generate_routing_reasoning(
                message, user_profile, final_channel, delay_seconds
            )
            
            return RoutingDecision(
                channel=final_channel,
                priority=self._get_priority(message.urgency_level),
                delay_seconds=delay_seconds,
                batch_key=batch_key,
                fallback_channel=fallback_channel,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error routing message: {e}")
            # Default to email for safety
            return RoutingDecision(
                channel=CommunicationChannel.EMAIL,
                priority="medium",
                reasoning=f"Error in routing: {str(e)}"
            )
    
    def _adjust_for_engagement(self, base_channel: CommunicationChannel, 
                              engagement_level: UserEngagementLevel) -> CommunicationChannel:
        """Adjust channel based on user engagement level"""
        if engagement_level == UserEngagementLevel.HIGH:
            # High engagement users: prefer email for detailed content
            if base_channel == CommunicationChannel.SMS:
                return CommunicationChannel.EMAIL
            return base_channel
            
        elif engagement_level == UserEngagementLevel.LOW:
            # Low engagement users: prefer SMS for re-engagement
            if base_channel == CommunicationChannel.EMAIL:
                return CommunicationChannel.SMS
            return base_channel
            
        elif engagement_level == UserEngagementLevel.AT_RISK:
            # At-risk users: SMS only for critical messages
            return CommunicationChannel.SMS
            
        else:  # MEDIUM engagement
            return base_channel
    
    def _adjust_for_urgency(self, channel: CommunicationChannel, 
                           urgency_level: UrgencyLevel) -> CommunicationChannel:
        """Adjust channel based on urgency level"""
        if urgency_level == UrgencyLevel.CRITICAL:
            return CommunicationChannel.SMS
        elif urgency_level == UrgencyLevel.HIGH:
            return CommunicationChannel.SMS
        elif urgency_level == UrgencyLevel.MEDIUM:
            return channel  # Keep original decision
        else:  # LOW urgency
            return CommunicationChannel.EMAIL
    
    def _apply_cultural_personalization(self, channel: CommunicationChannel, 
                                      user_profile: UserProfile, 
                                      message: CommunicationMessage) -> CommunicationChannel:
        """Apply cultural personalization for African American professionals"""
        try:
            # Get cultural context based on age and income
            age_context = self.cultural_context.get(f'age_{user_profile.age_range.replace("-", "_")}', {})
            income_context = self.cultural_context.get(f'income_{user_profile.income_range.replace("-", "_")}', {})
            
            # Community-focused messages: prefer SMS for immediate connection
            if message.message_type in [MessageType.COMMUNITY_EVENT, MessageType.QUICK_CHECKIN]:
                if age_context.get('community_emphasis'):
                    return CommunicationChannel.SMS
            
            # Career insights: prefer email for detailed content
            if message.message_type == MessageType.CAREER_INSIGHTS:
                if age_context.get('career_focus') == 'career_advancement':
                    return CommunicationChannel.EMAIL
            
            # Financial education: adjust based on income level
            if message.message_type == MessageType.FINANCIAL_EDUCATION:
                education_focus = income_context.get('education_focus', 'basic_financial_literacy')
                if education_focus in ['advanced_financial_strategies', 'sophisticated_investment_strategies']:
                    return CommunicationChannel.EMAIL
                else:
                    return CommunicationChannel.SMS
            
            # Investment opportunities: prefer email for detailed analysis
            if message.message_type == MessageType.INVESTMENT_OPPORTUNITY:
                return CommunicationChannel.EMAIL
            
            return channel
            
        except Exception as e:
            logger.error(f"Error applying cultural personalization: {e}")
            return channel
    
    def _check_user_preferences(self, channel: CommunicationChannel, 
                               user_profile: UserProfile) -> CommunicationChannel:
        """Check user preferences and opt-in status"""
        # Check opt-in status
        if channel == CommunicationChannel.SMS and not user_profile.sms_opted_in:
            return CommunicationChannel.EMAIL
        if channel == CommunicationChannel.EMAIL and not user_profile.email_opted_in:
            return CommunicationChannel.SMS
        
        # Check user preferences
        user_prefs = user_profile.communication_preferences
        
        if channel == CommunicationChannel.SMS and user_prefs.get('prefer_email', False):
            return CommunicationChannel.EMAIL
        if channel == CommunicationChannel.EMAIL and user_prefs.get('prefer_sms', False):
            return CommunicationChannel.SMS
        
        return channel
    
    def _calculate_delay(self, urgency_level: UrgencyLevel, 
                        user_profile: UserProfile) -> int:
        """Calculate delay based on urgency level and user profile"""
        base_delay = self.urgency_delays.get(urgency_level, 0)
        
        # Adjust for user engagement level
        if user_profile.engagement_level == UserEngagementLevel.HIGH:
            base_delay = max(0, base_delay - 3600)  # Reduce delay by 1 hour
        elif user_profile.engagement_level == UserEngagementLevel.LOW:
            base_delay = min(base_delay + 3600, 86400)  # Increase delay by 1 hour, max 24h
        
        return base_delay
    
    def _get_batch_key(self, message: CommunicationMessage, 
                      user_profile: UserProfile) -> Optional[str]:
        """Get batch key for message batching"""
        if message.urgency_level in [UrgencyLevel.MEDIUM, UrgencyLevel.LOW]:
            # Batch by user engagement level and message type
            return f"batch:{user_profile.engagement_level.value}:{message.message_type.value}"
        return None
    
    def _determine_fallback_channel(self, primary_channel: CommunicationChannel, 
                                   urgency_level: UrgencyLevel) -> Optional[CommunicationChannel]:
        """Determine fallback channel for delivery failures"""
        if primary_channel == CommunicationChannel.SMS:
            if urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
                return CommunicationChannel.EMAIL
        elif primary_channel == CommunicationChannel.EMAIL:
            if urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
                return CommunicationChannel.SMS
        
        return None
    
    def _get_priority(self, urgency_level: UrgencyLevel) -> str:
        """Get priority string for task queue"""
        priority_map = {
            UrgencyLevel.CRITICAL: "critical",
            UrgencyLevel.HIGH: "high",
            UrgencyLevel.MEDIUM: "medium",
            UrgencyLevel.LOW: "low"
        }
        return priority_map.get(urgency_level, "medium")
    
    def _generate_routing_reasoning(self, message: CommunicationMessage, 
                                  user_profile: UserProfile, 
                                  channel: CommunicationChannel, 
                                  delay_seconds: int) -> str:
        """Generate reasoning for routing decision"""
        reasons = []
        
        # Message type reasoning
        if message.message_type in [MessageType.FINANCIAL_ALERT, MessageType.SECURITY_ALERT]:
            reasons.append("SMS for immediate financial/security alerts")
        elif message.message_type in [MessageType.MONTHLY_REPORT, MessageType.DETAILED_ANALYSIS]:
            reasons.append("Email for detailed content")
        
        # Engagement level reasoning
        if user_profile.engagement_level == UserEngagementLevel.HIGH:
            reasons.append("High engagement user - prefer detailed content")
        elif user_profile.engagement_level == UserEngagementLevel.LOW:
            reasons.append("Low engagement user - SMS for re-engagement")
        
        # Urgency reasoning
        if message.urgency_level == UrgencyLevel.CRITICAL:
            reasons.append("Critical urgency - immediate SMS")
        elif message.urgency_level == UrgencyLevel.LOW:
            reasons.append("Low urgency - email delivery")
        
        # Cultural reasoning
        if user_profile.age_range == "25-35":
            reasons.append("Young professional - community-focused approach")
        
        # Delay reasoning
        if delay_seconds > 0:
            delay_hours = delay_seconds // 3600
            if delay_hours > 0:
                reasons.append(f"Batched delivery in {delay_hours} hours")
        
        return "; ".join(reasons)
    
    def get_user_engagement_level(self, user_id: str) -> UserEngagementLevel:
        """Get user engagement level from Redis analytics"""
        if not self.redis_client:
            return UserEngagementLevel.MEDIUM
        
        try:
            # Get engagement metrics
            last_activity = self.redis_client.get(f"user_activity:{user_id}")
            email_opens = int(self.redis_client.get(f"email_opens:{user_id}") or 0)
            sms_responses = int(self.redis_client.get(f"sms_responses:{user_id}") or 0)
            app_logins = int(self.redis_client.get(f"app_logins:{user_id}") or 0)
            
            # Calculate engagement score
            engagement_score = 0
            
            if last_activity:
                last_activity_dt = datetime.fromisoformat(last_activity)
                days_since_activity = (datetime.utcnow() - last_activity_dt).days
                if days_since_activity <= 1:
                    engagement_score += 30
                elif days_since_activity <= 7:
                    engagement_score += 20
                elif days_since_activity <= 30:
                    engagement_score += 10
            
            engagement_score += min(email_opens * 5, 30)
            engagement_score += min(sms_responses * 10, 30)
            engagement_score += min(app_logins * 2, 20)
            
            # Determine engagement level
            if engagement_score >= 80:
                return UserEngagementLevel.HIGH
            elif engagement_score >= 50:
                return UserEngagementLevel.MEDIUM
            elif engagement_score >= 20:
                return UserEngagementLevel.LOW
            else:
                return UserEngagementLevel.AT_RISK
                
        except Exception as e:
            logger.error(f"Error getting user engagement level: {e}")
            return UserEngagementLevel.MEDIUM
    
    def update_user_activity(self, user_id: str, activity_type: str):
        """Update user activity tracking"""
        if not self.redis_client:
            return
        
        try:
            current_time = datetime.utcnow().isoformat()
            
            # Update last activity
            self.redis_client.set(f"user_activity:{user_id}", current_time)
            
            # Update activity counters
            if activity_type == "email_open":
                self.redis_client.incr(f"email_opens:{user_id}")
            elif activity_type == "sms_response":
                self.redis_client.incr(f"sms_responses:{user_id}")
            elif activity_type == "app_login":
                self.redis_client.incr(f"app_logins:{user_id}")
            
            # Set expiration for counters (90 days)
            self.redis_client.expire(f"email_opens:{user_id}", 86400 * 90)
            self.redis_client.expire(f"sms_responses:{user_id}", 86400 * 90)
            self.redis_client.expire(f"app_logins:{user_id}", 86400 * 90)
            
        except Exception as e:
            logger.error(f"Error updating user activity: {e}")

# Create singleton instance
communication_router = CommunicationRouter() 