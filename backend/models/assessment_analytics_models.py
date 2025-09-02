"""
Assessment Analytics Models

Comprehensive analytics tracking for assessment system and landing page:
- User journey tracking
- Conversion funnel analysis
- Performance monitoring
- Lead quality scoring
- Real-time metrics
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, DECIMAL, JSON, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid
from enum import Enum

from .base import Base

# =====================================================
# ENUM DEFINITIONS
# =====================================================

class AnalyticsEventType(str, Enum):
    """Analytics event types for assessment system"""
    ASSESSMENT_LANDING_VIEWED = 'assessment_landing_viewed'
    ASSESSMENT_STARTED = 'assessment_started'
    ASSESSMENT_QUESTION_ANSWERED = 'assessment_question_answered'
    ASSESSMENT_COMPLETED = 'assessment_completed'
    EMAIL_CAPTURED = 'email_captured'
    CONVERSION_MODAL_OPENED = 'conversion_modal_opened'
    PAYMENT_INITIATED = 'payment_initiated'
    SOCIAL_PROOF_INTERACTION = 'social_proof_interaction'
    ASSESSMENT_ABANDONED = 'assessment_abandoned'
    ASSESSMENT_RESUMED = 'assessment_resumed'
    ASSESSMENT_SHARED = 'assessment_shared'
    LEAD_QUALIFIED = 'lead_qualified'

class ConversionStage(str, Enum):
    """Conversion funnel stages"""
    LANDING_VIEW = 'landing_view'
    ASSESSMENT_START = 'assessment_start'
    ASSESSMENT_COMPLETE = 'assessment_complete'
    EMAIL_CAPTURE = 'email_capture'
    CONVERSION_MODAL = 'conversion_modal'
    PAYMENT_ATTEMPT = 'payment_attempt'
    PAYMENT_SUCCESS = 'payment_success'

class LeadQualityScore(str, Enum):
    """Lead quality scoring levels"""
    HOT = 'hot'
    WARM = 'warm'
    COLD = 'cold'
    UNQUALIFIED = 'unqualified'

# =====================================================
# CORE ANALYTICS MODELS
# =====================================================

class AssessmentAnalyticsEvent(Base):
    """Core analytics events for assessment system"""
    __tablename__ = 'assessment_analytics_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey('assessments.id', ondelete='SET NULL'), nullable=True, index=True)
    assessment_type = Column(String(50), nullable=True, index=True)
    
    # Event metadata
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    properties = Column(JSONB, default={})  # Event-specific properties
    source = Column(String(50), default='web')  # web, mobile, api
    user_agent = Column(Text)
    ip_address = Column(INET)
    referrer = Column(String(500))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    utm_term = Column(String(100))
    utm_content = Column(String(100))
    
    # Device and location data
    device_type = Column(String(50))  # desktop, mobile, tablet
    browser = Column(String(100))
    os = Column(String(100))
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    
    # Performance metrics
    page_load_time = Column(Float)  # milliseconds
    time_on_page = Column(Float)  # seconds
    
    # Relationships
    user = relationship("User", back_populates="assessment_analytics_events")
    assessment = relationship("Assessment", back_populates="analytics_events")
    
    def __repr__(self):
        return f'<AssessmentAnalyticsEvent {self.event_type}:{self.session_id}:{self.timestamp}>'

class AssessmentSession(Base):
    """User session tracking for assessment system"""
    __tablename__ = 'assessment_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Session metadata
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Session properties
    assessment_type = Column(String(50), nullable=True, index=True)
    completed_assessment = Column(Boolean, default=False)
    email_captured = Column(Boolean, default=False)
    conversion_attempted = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    
    # Traffic source
    referrer = Column(String(500))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    
    # Device and location
    device_type = Column(String(50))
    browser = Column(String(100))
    os = Column(String(100))
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    
    # Relationships
    user = relationship("User", back_populates="assessment_sessions")
    events = relationship("AssessmentAnalyticsEvent", back_populates="session")
    
    def __repr__(self):
        return f'<AssessmentSession {self.session_id}:{self.assessment_type}:{self.started_at}>'

class ConversionFunnel(Base):
    """Conversion funnel tracking and analysis"""
    __tablename__ = 'conversion_funnels'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, index=True)
    assessment_type = Column(String(50), nullable=False, index=True)
    
    # Funnel stages
    landing_viewed_at = Column(DateTime(timezone=True), nullable=True)
    assessment_started_at = Column(DateTime(timezone=True), nullable=True)
    assessment_completed_at = Column(DateTime(timezone=True), nullable=True)
    email_captured_at = Column(DateTime(timezone=True), nullable=True)
    conversion_modal_opened_at = Column(DateTime(timezone=True), nullable=True)
    payment_attempted_at = Column(DateTime(timezone=True), nullable=True)
    payment_successful_at = Column(DateTime(timezone=True), nullable=True)
    
    # Time intervals (in seconds)
    time_to_start = Column(Integer, nullable=True)
    time_to_complete = Column(Integer, nullable=True)
    time_to_email_capture = Column(Integer, nullable=True)
    time_to_conversion_attempt = Column(Integer, nullable=True)
    time_to_payment_success = Column(Integer, nullable=True)
    
    # Conversion metrics
    current_stage = Column(String(50), nullable=False, index=True)
    dropped_off_at = Column(String(50), nullable=True)
    conversion_value = Column(DECIMAL(10, 2), nullable=True)
    
    # Lead quality
    lead_quality_score = Column(String(20), nullable=True, index=True)
    risk_level = Column(String(20), nullable=True)
    assessment_score = Column(Integer, nullable=True)
    
    # Traffic source
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<ConversionFunnel {self.session_id}:{self.current_stage}:{self.assessment_type}>'

class LeadQualityMetrics(Base):
    """Lead quality scoring and segmentation"""
    __tablename__ = 'lead_quality_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    assessment_type = Column(String(50), nullable=False, index=True)
    
    # Assessment results
    assessment_score = Column(Integer, nullable=True)
    risk_level = Column(String(20), nullable=True)
    completion_time_seconds = Column(Integer, nullable=True)
    
    # Lead quality indicators
    lead_quality_score = Column(String(20), nullable=False, index=True)
    conversion_probability = Column(Float, nullable=True)  # 0.0 to 1.0
    engagement_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Behavioral signals
    questions_answered = Column(Integer, nullable=True)
    time_spent_on_assessment = Column(Integer, nullable=True)  # seconds
    assessment_abandoned = Column(Boolean, default=False)
    assessment_resumed = Column(Boolean, default=False)
    assessment_shared = Column(Boolean, default=False)
    
    # Conversion behavior
    email_captured = Column(Boolean, default=False)
    conversion_modal_opened = Column(Boolean, default=False)
    payment_attempted = Column(Boolean, default=False)
    converted = Column(Boolean, default=False)
    
    # Demographics (if available)
    age_group = Column(String(20), nullable=True)
    income_level = Column(String(20), nullable=True)
    education_level = Column(String(20), nullable=True)
    job_title = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    
    # Traffic source
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="lead_quality_metrics")
    
    def __repr__(self):
        return f'<LeadQualityMetrics {self.session_id}:{self.lead_quality_score}:{self.assessment_type}>'

class RealTimeMetrics(Base):
    """Real-time metrics for dashboard and social proof"""
    __tablename__ = 'real_time_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String(50), nullable=False, index=True)
    assessment_type = Column(String(50), nullable=True, index=True)
    
    # Metric values
    value = Column(Integer, default=0)
    previous_value = Column(Integer, default=0)
    change_percentage = Column(Float, nullable=True)
    
    # Time tracking
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Additional context
    metric_metadata = Column(JSONB, default={})
    
    def __repr__(self):
        return f'<RealTimeMetrics {self.metric_type}:{self.value}:{self.period_start}>'

class PerformanceMetrics(Base):
    """Performance monitoring and optimization metrics"""
    __tablename__ = 'performance_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_type = Column(String(50), nullable=False, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # Performance data
    page_load_time = Column(Float, nullable=True)  # milliseconds
    api_response_time = Column(Float, nullable=True)  # milliseconds
    database_query_time = Column(Float, nullable=True)  # milliseconds
    error_rate = Column(Float, nullable=True)  # percentage
    
    # Device and browser info
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    
    # Location data
    country = Column(String(2), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Error details
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    def __repr__(self):
        return f'<PerformanceMetrics {self.metric_type}:{self.timestamp}>'

class GeographicAnalytics(Base):
    """Geographic distribution and performance analytics"""
    __tablename__ = 'geographic_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country = Column(String(2), nullable=False, index=True)
    region = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    assessment_type = Column(String(50), nullable=True, index=True)
    
    # Geographic metrics
    total_sessions = Column(Integer, default=0)
    completed_assessments = Column(Integer, default=0)
    conversion_rate = Column(Float, nullable=True)
    average_score = Column(Float, nullable=True)
    average_completion_time = Column(Float, nullable=True)
    
    # Performance metrics
    average_page_load_time = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    
    # Date tracking
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    def __repr__(self):
        return f'<GeographicAnalytics {self.country}:{self.region}:{self.date}>'

# =====================================================
# INDEXES FOR PERFORMANCE
# =====================================================

# AssessmentAnalyticsEvent indexes
from sqlalchemy import Index
AssessmentAnalyticsEvent.__table__.append_constraint(
    Index('idx_assessment_analytics_session_event', 'session_id', 'event_type', 'timestamp')
)
AssessmentAnalyticsEvent.__table__.append_constraint(
    Index('idx_assessment_analytics_user_timestamp', 'user_id', 'timestamp')
)
AssessmentAnalyticsEvent.__table__.append_constraint(
    Index('idx_assessment_analytics_assessment_timestamp', 'assessment_type', 'timestamp')
)

# AssessmentSession indexes
AssessmentSession.__table__.append_constraint(
    Index('idx_assessment_session_user_started', 'user_id', 'started_at')
)
AssessmentSession.__table__.append_constraint(
    Index('idx_assessment_session_type_completed', 'assessment_type', 'completed_assessment')
)

# ConversionFunnel indexes
ConversionFunnel.__table__.append_constraint(
    Index('idx_conversion_funnel_session_stage', 'session_id', 'current_stage')
)
ConversionFunnel.__table__.append_constraint(
    Index('idx_conversion_funnel_type_stage', 'assessment_type', 'current_stage')
)

# LeadQualityMetrics indexes
LeadQualityMetrics.__table__.append_constraint(
    Index('idx_lead_quality_session_score', 'session_id', 'lead_quality_score')
)
LeadQualityMetrics.__table__.append_constraint(
    Index('idx_lead_quality_type_score', 'assessment_type', 'lead_quality_score')
)

# RealTimeMetrics indexes
RealTimeMetrics.__table__.append_constraint(
    Index('idx_real_time_metrics_type_period', 'metric_type', 'period_start')
)

# PerformanceMetrics indexes
PerformanceMetrics.__table__.append_constraint(
    Index('idx_performance_metrics_type_timestamp', 'metric_type', 'timestamp')
)

# GeographicAnalytics indexes
GeographicAnalytics.__table__.append_constraint(
    Index('idx_geographic_analytics_location_date', 'country', 'region', 'date')
)
