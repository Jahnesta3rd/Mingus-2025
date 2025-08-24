"""
Communication Preferences and Consent Management Models
Handles user communication preferences, TCPA compliance, and GDPR compliance
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, ForeignKey, Enum, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum
from ..models.base import Base


class CommunicationChannel(enum.Enum):
    """Communication channels available"""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class AlertType(enum.Enum):
    """Types of alerts and communications"""
    CRITICAL_FINANCIAL = "critical_financial"
    DAILY_CHECKIN = "daily_checkin"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_ANALYSIS = "monthly_analysis"
    CAREER_INSIGHTS = "career_insights"
    WELLNESS_TIPS = "wellness_tips"
    BILL_REMINDERS = "bill_reminders"
    BUDGET_ALERTS = "budget_alerts"
    SPENDING_PATTERNS = "spending_patterns"
    EMERGENCY_FUND = "emergency_fund"
    SUBSCRIPTION_UPDATES = "subscription_updates"
    MARKETING_CONTENT = "marketing_content"


class FrequencyType(enum.Enum):
    """Communication frequency options"""
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    NEVER = "never"


class ConsentStatus(enum.Enum):
    """Consent status for communications"""
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"


class UserSegment(enum.Enum):
    """User segments for default preferences"""
    NEW_USER = "new_user"
    PREMIUM_SUBSCRIBER = "premium_subscriber"
    AT_RISK_USER = "at_risk_user"
    HIGH_ENGAGEMENT = "high_engagement"
    INACTIVE = "inactive"


class CommunicationPreferences(Base):
    """User communication preferences"""
    __tablename__ = 'communication_preferences'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Channel preferences for different alert types
    sms_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=False)
    in_app_enabled = Column(Boolean, default=True)
    
    # User preference fields as requested
    preferred_sms_time = Column(Time, default=datetime.strptime("09:00", "%H:%M").time())
    preferred_email_day = Column(Integer, default=1)  # 0=Monday, 1=Tuesday, etc.
    alert_types_sms = Column(JSON, default=lambda: {
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
    })
    alert_types_email = Column(JSON, default=lambda: {
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
    })
    frequency_preference = Column(Enum(FrequencyType), default=FrequencyType.WEEKLY)
    
    # Frequency preferences for different alert types
    critical_frequency = Column(Enum(FrequencyType), default=FrequencyType.IMMEDIATE)
    daily_frequency = Column(Enum(FrequencyType), default=FrequencyType.DAILY)
    weekly_frequency = Column(Enum(FrequencyType), default=FrequencyType.WEEKLY)
    monthly_frequency = Column(Enum(FrequencyType), default=FrequencyType.MONTHLY)
    
    # Content type preferences
    financial_alerts_enabled = Column(Boolean, default=True)
    career_content_enabled = Column(Boolean, default=True)
    wellness_content_enabled = Column(Boolean, default=True)
    marketing_content_enabled = Column(Boolean, default=False)
    
    # Delivery timing preferences
    preferred_email_time = Column(Time, default=datetime.strptime("18:00", "%H:%M").time())
    timezone = Column(String(50), default="UTC")
    
    # User segment for default preferences
    user_segment = Column(Enum(UserSegment), default=UserSegment.NEW_USER)
    
    # Smart defaults based on user profile
    auto_adjust_frequency = Column(Boolean, default=True)
    engagement_based_optimization = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="communication_preferences")
    consent_records = relationship("ConsentRecord", back_populates="preferences")
    delivery_logs = relationship("CommunicationDeliveryLog", back_populates="preferences")


class SMSConsent(Base):
    """TCPA-compliant SMS consent tracking"""
    __tablename__ = 'sms_consent'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Phone number verification
    phone_number = Column(String(20), nullable=False)
    phone_verified = Column(Boolean, default=False)
    verification_code = Column(String(10), nullable=True)
    verification_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # TCPA compliance fields
    consent_granted = Column(Boolean, default=False)
    consent_granted_at = Column(DateTime(timezone=True), nullable=True)
    consent_source = Column(String(100), nullable=False)  # 'web_form', 'mobile_app', 'api', 'sms_reply'
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Opt-out tracking
    opted_out = Column(Boolean, default=False)
    opted_out_at = Column(DateTime(timezone=True), nullable=True)
    opt_out_reason = Column(String(200), nullable=True)
    opt_out_method = Column(String(50), nullable=True)  # 'sms_stop', 'web_form', 'api'
    
    # Re-engagement
    re_engaged = Column(Boolean, default=False)
    re_engaged_at = Column(DateTime(timezone=True), nullable=True)
    re_engagement_method = Column(String(50), nullable=True)
    
    # Compliance tracking
    last_message_sent_at = Column(DateTime(timezone=True), nullable=True)
    messages_sent_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sms_consent")


class ConsentRecord(Base):
    """TCPA and GDPR consent tracking"""
    __tablename__ = 'consent_records'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    preferences_id = Column(String(36), ForeignKey('communication_preferences.id'), nullable=False)
    
    # Consent details
    consent_type = Column(String(50), nullable=False)  # 'sms', 'email', 'marketing'
    consent_status = Column(Enum(ConsentStatus), default=ConsentStatus.PENDING)
    
    # TCPA compliance fields
    phone_number = Column(String(20), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    consent_source = Column(String(100), nullable=False)  # 'web_form', 'mobile_app', 'api'
    
    # GDPR compliance fields
    legal_basis = Column(String(50), nullable=True)  # 'consent', 'legitimate_interest', 'contract'
    purpose = Column(Text, nullable=True)
    data_retention_period = Column(Integer, nullable=True)  # days
    
    # Consent lifecycle
    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verification
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_method = Column(String(50), nullable=True)  # 'sms_code', 'email_link', 'manual'
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="consent_records")
    preferences = relationship("CommunicationPreferences", back_populates="consent_records")


class AlertTypePreference(Base):
    """Granular preferences for specific alert types"""
    __tablename__ = 'alert_type_preferences'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    preferences_id = Column(String(36), ForeignKey('communication_preferences.id'), nullable=False)
    
    # Alert type and channel preferences
    alert_type = Column(Enum(AlertType), nullable=False)
    sms_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=False)
    in_app_enabled = Column(Boolean, default=True)
    
    # Frequency for this specific alert type
    frequency = Column(Enum(FrequencyType), nullable=False)
    
    # Priority and timing
    priority = Column(Integer, default=5)  # 1-10 scale
    preferred_time = Column(Time, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="alert_type_preferences")
    preferences = relationship("CommunicationPreferences")


class DeliveryLog(Base):
    """Log of all communication deliveries for compliance and analytics"""
    __tablename__ = 'delivery_logs'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    preferences_id = Column(String(36), ForeignKey('communication_preferences.id'), nullable=False)
    
    # Delivery details
    alert_type = Column(Enum(AlertType), nullable=False)
    channel = Column(Enum(CommunicationChannel), nullable=False)
    message_id = Column(String(100), nullable=True)  # External service message ID
    
    # Content and timing
    subject = Column(Text, nullable=True)
    content_preview = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Delivery status
    status = Column(String(50), default="pending")  # pending, sent, delivered, failed, bounced
    error_message = Column(Text, nullable=True)
    
    # User engagement
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Compliance tracking
    consent_verified = Column(Boolean, default=False)
    compliance_checks_passed = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="delivery_logs")
    preferences = relationship("CommunicationPreferences", back_populates="delivery_logs")


class OptOutHistory(Base):
    """Track opt-outs for compliance and re-engagement"""
    __tablename__ = 'opt_out_history'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Opt-out details
    channel = Column(Enum(CommunicationChannel), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=True)  # null means all types
    reason = Column(String(200), nullable=True)
    
    # Opt-out method
    method = Column(String(50), nullable=False)  # 'sms_stop', 'email_unsubscribe', 'web_form', 'api'
    source = Column(String(100), nullable=True)  # 'sms', 'email', 'web', 'mobile_app'
    
    # Timing
    opted_out_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # for temporary opt-outs
    
    # Re-engagement
    re_engaged_at = Column(DateTime(timezone=True), nullable=True)
    re_engagement_method = Column(String(50), nullable=True)
    
    # Compliance tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="opt_out_history")


class UserEngagementMetrics(Base):
    """Track user engagement for preference optimization"""
    __tablename__ = 'user_engagement_metrics'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Engagement metrics
    total_messages_sent = Column(Integer, default=0)
    total_messages_opened = Column(Integer, default=0)
    total_messages_clicked = Column(Integer, default=0)
    total_messages_responded = Column(Integer, default=0)
    
    # Channel-specific metrics
    sms_engagement_rate = Column(Integer, default=0)  # percentage
    email_engagement_rate = Column(Integer, default=0)  # percentage
    push_engagement_rate = Column(Integer, default=0)  # percentage
    
    # Alert type engagement
    alert_type_engagement = Column(JSON, nullable=True)  # {alert_type: engagement_rate}
    
    # Timing preferences
    optimal_send_times = Column(JSON, nullable=True)  # {day_of_week: {hour: engagement_rate}}
    
    # Frequency optimization
    current_frequency = Column(String(50), default="weekly")
    recommended_frequency = Column(String(50), nullable=True)
    frequency_adjustment_reason = Column(Text, nullable=True)
    
    # Last engagement
    last_engagement_at = Column(DateTime(timezone=True), nullable=True)
    engagement_trend = Column(String(20), default="stable")  # increasing, decreasing, stable
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="engagement_metrics")


class CommunicationPolicy(Base):
    """System-wide communication policies and rules"""
    __tablename__ = 'communication_policies'
    
    id = Column(String(36), primary_key=True)
    
    # Policy details
    policy_name = Column(String(100), nullable=False)
    policy_type = Column(String(50), nullable=False)  # 'default', 'tier_based', 'region_based'
    
    # Target criteria
    user_tier = Column(String(50), nullable=True)  # 'free', 'premium', 'enterprise'
    region = Column(String(50), nullable=True)
    user_segment = Column(Enum(UserSegment), nullable=True)
    
    # Policy rules
    default_channel = Column(Enum(CommunicationChannel), default=CommunicationChannel.EMAIL)
    default_frequency = Column(Enum(FrequencyType), default=FrequencyType.WEEKLY)
    max_messages_per_day = Column(Integer, default=5)
    max_messages_per_week = Column(Integer, default=20)
    
    # Content restrictions
    allowed_alert_types = Column(JSON, nullable=True)  # list of allowed alert types
    marketing_content_allowed = Column(Boolean, default=False)
    
    # Compliance settings
    require_double_optin = Column(Boolean, default=True)
    consent_retention_days = Column(Integer, default=2555)  # 7 years
    auto_optout_inactive_days = Column(Integer, default=365)  # 1 year
    
    # Timing restrictions
    quiet_hours_start = Column(String(5), default="22:00")  # HH:MM format
    quiet_hours_end = Column(String(5), default="08:00")  # HH:MM format
    timezone_aware = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=5)  # 1-10 scale for policy precedence
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True) 