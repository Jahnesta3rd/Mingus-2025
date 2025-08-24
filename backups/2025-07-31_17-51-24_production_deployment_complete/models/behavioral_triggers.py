"""
Behavioral Trigger Models
Handles intelligent trigger detection and contextual communication initiation
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, ForeignKey, Enum, Float, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum
from ..models.base import Base


class TriggerType(enum.Enum):
    """Types of behavioral triggers"""
    FINANCIAL_BEHAVIOR = "financial_behavior"
    HEALTH_WELLNESS = "health_wellness"
    CAREER_ADVANCEMENT = "career_advancement"
    LIFE_EVENT = "life_event"
    ENGAGEMENT = "engagement"
    PREDICTIVE = "predictive"


class TriggerCategory(enum.Enum):
    """Specific trigger categories"""
    # Financial behavior triggers
    SPENDING_SPIKE = "spending_spike"
    INCOME_DROP = "income_drop"
    SAVINGS_STALL = "savings_stall"
    MILESTONE_REACHED = "milestone_reached"
    
    # Health/wellness triggers
    LOW_EXERCISE_HIGH_SPENDING = "low_exercise_high_spending"
    HIGH_STRESS_FINANCIAL = "high_stress_financial"
    RELATIONSHIP_CHANGE = "relationship_change"
    
    # Career triggers
    JOB_OPPORTUNITY = "job_opportunity"
    SKILL_GAP = "skill_gap"
    SALARY_BELOW_MARKET = "salary_below_market"
    
    # Life event triggers
    BIRTHDAY_APPROACHING = "birthday_approaching"
    LEASE_RENEWAL = "lease_renewal"
    STUDENT_LOAN_GRACE_ENDING = "student_loan_grace_ending"
    
    # Engagement triggers
    APP_USAGE_DECLINE = "app_usage_decline"
    FEATURE_UNUSED = "feature_unused"
    PREMIUM_UPGRADE_OPPORTUNITY = "premium_upgrade_opportunity"


class TriggerStatus(enum.Enum):
    """Trigger status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    TESTING = "testing"


class TriggerPriority(enum.Enum):
    """Trigger priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BehavioralTrigger(Base):
    """Behavioral trigger definitions"""
    __tablename__ = 'behavioral_triggers'
    
    id = Column(String(36), primary_key=True)
    
    # Trigger identification
    trigger_name = Column(String(100), nullable=False)
    trigger_type = Column(Enum(TriggerType), nullable=False)
    trigger_category = Column(Enum(TriggerCategory), nullable=False)
    
    # Trigger configuration
    trigger_conditions = Column(JSON, nullable=False)  # Complex conditions for trigger detection
    trigger_thresholds = Column(JSON, nullable=True)  # Threshold values for triggers
    trigger_frequency = Column(String(20), default="once")  # once, daily, weekly, monthly
    
    # Communication configuration
    sms_template = Column(String(200), nullable=True)
    email_template = Column(String(200), nullable=True)
    communication_delay_minutes = Column(Integer, default=0)  # Delay before sending
    
    # Priority and status
    priority = Column(Enum(TriggerPriority), default=TriggerPriority.MEDIUM)
    status = Column(Enum(TriggerStatus), default=TriggerStatus.ACTIVE)
    
    # Targeting
    target_user_segments = Column(JSON, nullable=True)  # List of user segments
    target_user_tiers = Column(JSON, nullable=True)  # List of user tiers
    exclusion_conditions = Column(JSON, nullable=True)  # Conditions to exclude users
    
    # Machine learning configuration
    ml_model_enabled = Column(Boolean, default=False)
    ml_model_name = Column(String(100), nullable=True)
    ml_confidence_threshold = Column(Float, default=0.7)  # Minimum confidence for ML triggers
    
    # Effectiveness tracking
    success_rate = Column(Float, default=0.0)  # Historical success rate
    engagement_rate = Column(Float, default=0.0)  # Historical engagement rate
    conversion_rate = Column(Float, default=0.0)  # Historical conversion rate
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(36), nullable=True)
    
    # Relationships
    trigger_events = relationship("TriggerEvent", back_populates="trigger")
    trigger_effectiveness = relationship("TriggerEffectiveness", back_populates="trigger")


class TriggerEvent(Base):
    """Individual trigger events that have been fired"""
    __tablename__ = 'trigger_events'
    
    id = Column(String(36), primary_key=True)
    trigger_id = Column(String(36), ForeignKey('behavioral_triggers.id'), nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # 'triggered', 'sent', 'engaged', 'converted'
    event_data = Column(JSON, nullable=True)  # Data that caused the trigger
    
    # Trigger detection
    detection_method = Column(String(50), nullable=False)  # 'rule_based', 'ml_model', 'hybrid'
    confidence_score = Column(Float, default=1.0)  # ML confidence score
    trigger_conditions_met = Column(JSON, nullable=True)  # Which conditions were met
    
    # Communication details
    sms_sent = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    sms_message_id = Column(String(100), nullable=True)
    email_message_id = Column(String(100), nullable=True)
    
    # User response
    user_engaged = Column(Boolean, default=False)
    engagement_type = Column(String(50), nullable=True)  # 'sms_click', 'email_open', 'email_click', 'app_action'
    engagement_time_minutes = Column(Integer, nullable=True)  # Time to engagement
    
    # Conversion tracking
    conversion_achieved = Column(Boolean, default=False)
    conversion_type = Column(String(50), nullable=True)  # 'goal_set', 'action_taken', 'purchase', 'upgrade'
    conversion_value = Column(Numeric(10, 2), nullable=True)  # Dollar value of conversion
    
    # Timing
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    engaged_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    trigger = relationship("BehavioralTrigger", back_populates="trigger_events")
    user = relationship("User", back_populates="trigger_events")


class TriggerEffectiveness(Base):
    """Effectiveness tracking for triggers"""
    __tablename__ = 'trigger_effectiveness'
    
    id = Column(String(36), primary_key=True)
    trigger_id = Column(String(36), ForeignKey('behavioral_triggers.id'), nullable=False)
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    
    # Effectiveness metrics
    total_triggers = Column(Integer, default=0)
    total_sent = Column(Integer, default=0)
    total_engaged = Column(Integer, default=0)
    total_converted = Column(Integer, default=0)
    
    # Rates
    send_rate = Column(Float, default=0.0)  # percentage of triggers that were sent
    engagement_rate = Column(Float, default=0.0)  # percentage of sent that were engaged
    conversion_rate = Column(Float, default=0.0)  # percentage of engaged that converted
    
    # Financial impact
    total_conversion_value = Column(Numeric(12, 2), default=0.0)
    avg_conversion_value = Column(Numeric(10, 2), default=0.0)
    roi = Column(Float, default=0.0)  # Return on investment
    
    # Cost metrics
    total_cost = Column(Numeric(10, 4), default=0.0)
    cost_per_trigger = Column(Numeric(10, 4), default=0.0)
    cost_per_conversion = Column(Numeric(10, 4), default=0.0)
    
    # User segment breakdown
    segment_breakdown = Column(JSON, nullable=True)  # {segment: {metrics}}
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    trigger = relationship("BehavioralTrigger", back_populates="trigger_effectiveness")


class UserBehaviorPattern(Base):
    """User behavior patterns for trigger detection"""
    __tablename__ = 'user_behavior_patterns'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    
    # Pattern identification
    pattern_type = Column(String(50), nullable=False)  # 'spending', 'income', 'savings', 'health', 'career'
    pattern_name = Column(String(100), nullable=False)  # 'weekly_spending_cycle', 'monthly_income_pattern'
    
    # Pattern data
    pattern_data = Column(JSON, nullable=False)  # Historical pattern data
    pattern_confidence = Column(Float, default=0.0)  # Confidence in pattern detection
    pattern_last_updated = Column(DateTime, nullable=False)
    
    # Pattern characteristics
    baseline_value = Column(Float, nullable=True)  # Baseline for comparison
    variance_threshold = Column(Float, nullable=True)  # Threshold for anomaly detection
    trend_direction = Column(String(20), nullable=True)  # 'increasing', 'decreasing', 'stable'
    
    # Usage tracking
    times_used_for_triggers = Column(Integer, default=0)
    last_used_for_trigger = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="behavior_patterns")


class MLModel(Base):
    """Machine learning models for trigger prediction"""
    __tablename__ = 'ml_models'
    
    id = Column(String(36), primary_key=True)
    
    # Model identification
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # 'classification', 'regression', 'clustering'
    model_version = Column(String(20), nullable=False)
    
    # Model configuration
    model_config = Column(JSON, nullable=False)  # Model hyperparameters and configuration
    feature_columns = Column(JSON, nullable=False)  # List of input features
    target_column = Column(String(50), nullable=False)  # Target variable
    
    # Model performance
    accuracy_score = Column(Float, default=0.0)
    precision_score = Column(Float, default=0.0)
    recall_score = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    
    # Training information
    training_data_size = Column(Integer, default=0)
    training_date = Column(DateTime, nullable=False)
    training_duration_minutes = Column(Integer, nullable=True)
    
    # Model status
    is_active = Column(Boolean, default=False)
    is_production = Column(Boolean, default=False)
    
    # Model artifacts
    model_file_path = Column(String(500), nullable=True)  # Path to saved model
    model_metadata = Column(JSON, nullable=True)  # Additional model metadata
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(36), nullable=True)


class TriggerTemplate(Base):
    """Communication templates for triggers"""
    __tablename__ = 'trigger_templates'
    
    id = Column(String(36), primary_key=True)
    
    # Template identification
    template_name = Column(String(100), nullable=False)
    template_type = Column(String(20), nullable=False)  # 'sms', 'email', 'push'
    trigger_category = Column(Enum(TriggerCategory), nullable=False)
    
    # Template content
    subject_line = Column(String(200), nullable=True)  # For emails
    message_content = Column(Text, nullable=False)
    personalization_variables = Column(JSON, nullable=True)  # Available variables for personalization
    
    # Template configuration
    character_limit = Column(Integer, nullable=True)  # For SMS
    call_to_action = Column(String(100), nullable=True)
    urgency_level = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # A/B testing
    is_ab_test_enabled = Column(Boolean, default=False)
    ab_test_variants = Column(JSON, nullable=True)  # Different versions for testing
    
    # Effectiveness
    avg_engagement_rate = Column(Float, default=0.0)
    avg_conversion_rate = Column(Float, default=0.0)
    total_uses = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Default template for category
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(36), nullable=True)


class TriggerSchedule(Base):
    """Scheduling configuration for triggers"""
    __tablename__ = 'trigger_schedules'
    
    id = Column(String(36), primary_key=True)
    trigger_id = Column(String(36), ForeignKey('behavioral_triggers.id'), nullable=False)
    
    # Schedule configuration
    schedule_type = Column(String(20), nullable=False)  # 'immediate', 'delayed', 'recurring', 'optimal_time'
    delay_minutes = Column(Integer, default=0)  # Delay before sending
    
    # Time-based scheduling
    optimal_hours = Column(JSON, nullable=True)  # [9, 10, 11, 18, 19, 20] - preferred hours
    optimal_days = Column(JSON, nullable=True)  # [0, 1, 2, 3, 4, 5, 6] - preferred days (0=Monday)
    timezone_aware = Column(Boolean, default=True)
    
    # Frequency limits
    max_triggers_per_day = Column(Integer, default=3)
    max_triggers_per_week = Column(Integer, default=10)
    max_triggers_per_month = Column(Integer, default=30)
    
    # Cooldown periods
    cooldown_hours = Column(Integer, default=24)  # Hours between same trigger
    cooldown_days = Column(Integer, default=7)  # Days between same trigger category
    
    # User-specific scheduling
    respect_user_preferences = Column(Boolean, default=True)  # Respect user's preferred times
    adaptive_scheduling = Column(Boolean, default=True)  # Learn from user engagement patterns
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    trigger = relationship("BehavioralTrigger") 