"""
Communication Analytics Models
Handles real-time metrics tracking, user engagement analysis, and financial impact measurement
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, ForeignKey, Enum, Float, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import enum
from ..models.base import Base


class MetricType(enum.Enum):
    """Types of communication metrics"""
    DELIVERY_RATE = "delivery_rate"
    OPEN_RATE = "open_rate"
    CLICK_RATE = "click_rate"
    RESPONSE_RATE = "response_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    COST_PER_ENGAGEMENT = "cost_per_engagement"
    CONVERSION_RATE = "conversion_rate"
    RETENTION_RATE = "retention_rate"


class ChannelType(enum.Enum):
    """Communication channels for analytics"""
    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class UserSegment(enum.Enum):
    """User segments for analysis"""
    NEW_USER = "new_user"
    ENGAGED = "engaged"
    AT_RISK = "at_risk"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    INACTIVE = "inactive"


class FinancialOutcome(enum.Enum):
    """Financial outcomes to track"""
    LATE_FEE_AVOIDED = "late_fee_avoided"
    BILL_PAID_ON_TIME = "bill_paid_on_time"
    SAVINGS_GOAL_ACHIEVED = "savings_goal_achieved"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    CAREER_ADVANCEMENT = "career_advancement"
    BUDGET_IMPROVED = "budget_improved"
    EMERGENCY_FUND_BUILT = "emergency_fund_built"


class CommunicationMetrics(Base):
    """Real-time communication metrics tracking"""
    __tablename__ = 'communication_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_type = Column(String(50))     # "low_balance", "weekly_checkin"
    channel = Column(String(10))          # "sms" or "email"
    status = Column(String(20))           # "sent", "delivered", "failed"
    cost = Column(Float)                  # Cost in dollars
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    action_taken = Column(String(100))    # "viewed_forecast", "updated_budget"
    
    # Relationships
    user = relationship("User", back_populates="communication_metrics")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_comm_metrics_user_id', 'user_id'),
        Index('idx_comm_metrics_message_type', 'message_type'),
        Index('idx_comm_metrics_channel', 'channel'),
        Index('idx_comm_metrics_status', 'status'),
        Index('idx_comm_metrics_sent_at', 'sent_at'),
    )


class UserEngagementMetrics(Base):
    """Detailed user engagement analysis"""
    __tablename__ = 'user_engagement_metrics'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Engagement metrics
    total_messages_received = Column(Integer, default=0)
    total_messages_engaged = Column(Integer, default=0)
    total_messages_ignored = Column(Integer, default=0)
    
    # Channel-specific engagement
    sms_engagement_count = Column(Integer, default=0)
    email_engagement_count = Column(Integer, default=0)
    push_engagement_count = Column(Integer, default=0)
    in_app_engagement_count = Column(Integer, default=0)
    
    # Time-based engagement patterns
    engagement_by_hour = Column(JSON, nullable=True)  # {hour: engagement_count}
    engagement_by_day = Column(JSON, nullable=True)  # {day: engagement_count}
    engagement_by_month = Column(JSON, nullable=True)  # {month: engagement_count}
    
    # Message type effectiveness
    alert_type_engagement = Column(JSON, nullable=True)  # {alert_type: {engaged, total, rate}}
    
    # Response time analysis
    avg_response_time_minutes = Column(Float, default=0.0)
    response_time_distribution = Column(JSON, nullable=True)  # {time_range: count}
    
    # Engagement trends
    engagement_trend = Column(String(20), default="stable")  # increasing, decreasing, stable
    engagement_score = Column(Float, default=0.0)  # 0-100 scale
    
    # Frequency analysis
    optimal_frequency = Column(String(20), nullable=True)  # daily, weekly, monthly
    current_frequency = Column(String(20), nullable=True)
    frequency_effectiveness = Column(Float, default=0.0)  # 0-100 scale
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="engagement_metrics")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_engagement_user_id', 'user_id'),
        Index('idx_user_engagement_score', 'engagement_score'),
        Index('idx_user_engagement_trend', 'engagement_trend'),
    )


# Backward-compatible alias expected by some services/tests
# The service imports UserEngagementAnalytics; maintain alias to avoid import errors
UserEngagementAnalytics = UserEngagementMetrics

class ChannelEffectiveness(Base):
    """SMS vs Email performance comparison and optimization"""
    __tablename__ = 'channel_effectiveness'
    
    id = Column(String(36), primary_key=True)
    
    # Channel identification
    channel = Column(Enum(ChannelType), nullable=False)
    alert_type = Column(String(50), nullable=True)
    user_segment = Column(Enum(UserSegment), nullable=True)
    
    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    
    # Performance metrics
    messages_sent = Column(Integer, default=0)
    messages_delivered = Column(Integer, default=0)
    messages_opened = Column(Integer, default=0)
    messages_clicked = Column(Integer, default=0)
    messages_responded = Column(Integer, default=0)
    messages_converted = Column(Integer, default=0)
    
    # Calculated rates
    delivery_rate = Column(Float, default=0.0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    response_rate = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    
    # Cost analysis
    total_cost = Column(Numeric(10, 4), default=0.0)
    cost_per_message = Column(Numeric(10, 4), default=0.0)
    cost_per_engagement = Column(Numeric(10, 4), default=0.0)
    cost_per_conversion = Column(Numeric(10, 4), default=0.0)
    
    # ROI metrics
    revenue_generated = Column(Numeric(12, 2), default=0.0)
    roi_percentage = Column(Float, default=0.0)
    profit_margin = Column(Float, default=0.0)
    
    # User behavior
    avg_response_time_minutes = Column(Float, default=0.0)
    opt_out_rate = Column(Float, default=0.0)
    re_engagement_rate = Column(Float, default=0.0)
    
    # Comparative metrics
    vs_other_channels = Column(JSON, nullable=True)  # Performance comparison
    market_benchmark = Column(Float, default=0.0)  # Industry standard
    performance_score = Column(Float, default=0.0)  # 0-100 scale
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_channel_effectiveness_date_channel', 'date', 'channel'),
        Index('idx_channel_effectiveness_alert_type', 'alert_type'),
        Index('idx_channel_effectiveness_user_segment', 'user_segment'),
        Index('idx_channel_effectiveness_performance', 'performance_score'),
    )


class FinancialImpactMetrics(Base):
    """Financial outcome correlation with communication engagement"""
    __tablename__ = 'financial_impact_metrics'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Financial outcomes
    outcome_type = Column(Enum(FinancialOutcome), nullable=False)
    outcome_value = Column(Numeric(12, 2), nullable=True)  # Dollar amount
    outcome_date = Column(DateTime, nullable=False)
    
    # Communication correlation
    communication_channel = Column(Enum(ChannelType), nullable=True)
    alert_type = Column(String(50), nullable=True)
    message_id = Column(String(100), nullable=True)
    
    # Time correlation
    days_since_last_communication = Column(Integer, nullable=True)
    communication_frequency_before_outcome = Column(String(20), nullable=True)
    
    # Engagement correlation
    user_engaged_with_communication = Column(Boolean, default=False)
    engagement_level = Column(String(20), nullable=True)  # low, medium, high
    
    # Attribution
    attributed_to_communication = Column(Boolean, default=False)
    attribution_confidence = Column(Float, default=0.0)  # 0-100 scale
    attribution_reason = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="financial_impact_metrics")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_financial_impact_user_id', 'user_id'),
        Index('idx_financial_impact_outcome_type', 'outcome_type'),
        Index('idx_financial_impact_outcome_date', 'outcome_date'),
        Index('idx_financial_impact_attribution', 'attributed_to_communication'),
    )


class CostTracking(Base):
    """Budget monitoring and cost analysis for communications"""
    __tablename__ = 'cost_tracking'
    
    id = Column(String(36), primary_key=True)
    
    # Cost identification
    channel = Column(Enum(ChannelType), nullable=False)
    alert_type = Column(String(50), nullable=True)
    user_segment = Column(Enum(UserSegment), nullable=True)
    
    # Time period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    
    # Cost breakdown
    sms_cost = Column(Numeric(10, 4), default=0.0)
    email_cost = Column(Numeric(10, 4), default=0.0)
    push_cost = Column(Numeric(10, 4), default=0.0)
    in_app_cost = Column(Numeric(10, 4), default=0.0)
    
    # Service provider costs
    twilio_cost = Column(Numeric(10, 4), default=0.0)
    resend_cost = Column(Numeric(10, 4), default=0.0)
    other_provider_cost = Column(Numeric(10, 4), default=0.0)
    
    # Infrastructure costs
    server_cost = Column(Numeric(10, 4), default=0.0)
    storage_cost = Column(Numeric(10, 4), default=0.0)
    bandwidth_cost = Column(Numeric(10, 4), default=0.0)
    
    # Operational costs
    development_cost = Column(Numeric(10, 4), default=0.0)
    maintenance_cost = Column(Numeric(10, 4), default=0.0)
    support_cost = Column(Numeric(10, 4), default=0.0)
    
    # Total costs
    total_cost = Column(Numeric(12, 4), default=0.0)
    total_messages = Column(Integer, default=0)
    cost_per_message = Column(Numeric(10, 4), default=0.0)
    
    # Budget tracking
    budget_allocation = Column(Numeric(12, 4), default=0.0)
    budget_utilization = Column(Float, default=0.0)  # percentage
    budget_variance = Column(Numeric(12, 4), default=0.0)
    
    # Cost efficiency
    cost_per_engagement = Column(Numeric(10, 4), default=0.0)
    cost_per_conversion = Column(Numeric(10, 4), default=0.0)
    cost_efficiency_score = Column(Float, default=0.0)  # 0-100 scale
    
    # Cost trends
    cost_trend = Column(String(20), default="stable")  # increasing, decreasing, stable
    cost_forecast = Column(Numeric(12, 4), default=0.0)
    
    # Alerts and thresholds
    cost_threshold_exceeded = Column(Boolean, default=False)
    budget_alert_triggered = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_cost_tracking_date_channel', 'date', 'channel'),
        Index('idx_cost_tracking_total_cost', 'total_cost'),
        Index('idx_cost_tracking_budget_utilization', 'budget_utilization'),
        Index('idx_cost_tracking_cost_efficiency', 'cost_efficiency_score'),
    )


class ABTestResults(Base):
    """A/B testing results for communication optimization"""
    __tablename__ = 'ab_test_results'
    
    id = Column(String(36), primary_key=True)
    
    # Test identification
    test_name = Column(String(100), nullable=False)
    test_variant = Column(String(50), nullable=False)  # A, B, C, etc.
    test_type = Column(String(50), nullable=False)  # content, timing, frequency, channel
    
    # Test parameters
    target_audience = Column(JSON, nullable=True)  # {segment, criteria}
    test_duration_days = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # Sample sizes
    total_users = Column(Integer, default=0)
    total_messages_sent = Column(Integer, default=0)
    total_engagements = Column(Integer, default=0)
    
    # Performance metrics
    delivery_rate = Column(Float, default=0.0)
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    response_rate = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    
    # Financial impact
    total_revenue_impact = Column(Numeric(12, 2), default=0.0)
    cost_per_conversion = Column(Numeric(10, 4), default=0.0)
    roi = Column(Float, default=0.0)  # Return on investment percentage
    
    # Statistical significance
    confidence_level = Column(Float, default=0.0)  # 0-100 scale
    p_value = Column(Float, default=0.0)
    is_statistically_significant = Column(Boolean, default=False)
    
    # Test status
    is_winner = Column(Boolean, default=False)
    test_status = Column(String(20), default="running")  # running, completed, paused
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_ab_test_results_test_name', 'test_name'),
        Index('idx_ab_test_results_test_status', 'test_status'),
        Index('idx_ab_test_results_is_winner', 'is_winner'),
    )


class CommunicationQueueStatus(Base):
    """Real-time communication queue monitoring"""
    __tablename__ = 'communication_queue_status'
    
    id = Column(String(36), primary_key=True)
    
    # Queue identification
    queue_name = Column(String(50), nullable=False)  # sms_critical, email_reports, etc.
    channel = Column(Enum(ChannelType), nullable=False)
    
    # Queue metrics
    queue_depth = Column(Integer, default=0)
    messages_processed = Column(Integer, default=0)
    messages_failed = Column(Integer, default=0)
    messages_pending = Column(Integer, default=0)
    
    # Performance metrics
    avg_processing_time_seconds = Column(Float, default=0.0)
    max_processing_time_seconds = Column(Float, default=0.0)
    throughput_messages_per_minute = Column(Float, default=0.0)
    
    # Error tracking
    error_rate = Column(Float, default=0.0)  # percentage
    last_error_message = Column(Text, nullable=True)
    last_error_time = Column(DateTime, nullable=True)
    
    # Health status
    is_healthy = Column(Boolean, default=True)
    health_score = Column(Float, default=100.0)  # 0-100 scale
    last_health_check = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_queue_status_queue_name', 'queue_name'),
        Index('idx_queue_status_channel', 'channel'),
        Index('idx_queue_status_health', 'is_healthy'),
    )


class AnalyticsAlert(Base):
    """Alert system for analytics anomalies and thresholds"""
    __tablename__ = 'analytics_alerts'
    
    id = Column(String(36), primary_key=True)
    
    # Alert identification
    alert_type = Column(String(50), nullable=False)  # low_delivery_rate, high_opt_out, cost_threshold
    alert_severity = Column(String(20), nullable=False)  # low, medium, high, critical
    alert_status = Column(String(20), default="active")  # active, acknowledged, resolved
    
    # Alert conditions
    metric_name = Column(String(50), nullable=False)
    threshold_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    comparison_operator = Column(String(10), nullable=False)  # <, >, <=, >=, ==
    
    # Context
    channel = Column(Enum(ChannelType), nullable=True)
    alert_type_filter = Column(String(50), nullable=True)
    user_segment = Column(Enum(UserSegment), nullable=True)
    time_period = Column(String(20), nullable=True)  # last_hour, last_day, last_week
    
    # Alert details
    alert_message = Column(Text, nullable=False)
    alert_description = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    
    # Notification
    notified_users = Column(JSON, nullable=True)  # List of user IDs notified
    notification_sent_at = Column(DateTime, nullable=True)
    
    # Resolution
    resolved_by = Column(String(36), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_analytics_alerts_alert_type', 'alert_type'),
        Index('idx_analytics_alerts_severity', 'alert_severity'),
        Index('idx_analytics_alerts_status', 'alert_status'),
        Index('idx_analytics_alerts_created_at', 'created_at'),
    )


class AnalyticsReport(Base):
    """Automated analytics reports"""
    __tablename__ = 'analytics_reports'
    
    id = Column(String(36), primary_key=True)
    
    # Report identification
    report_type = Column(String(50), nullable=False)  # weekly_performance, monthly_engagement, quarterly_impact
    report_period = Column(String(20), nullable=False)  # weekly, monthly, quarterly, yearly
    report_date = Column(DateTime, nullable=False)
    
    # Report scope
    channels_included = Column(JSON, nullable=True)  # List of channels
    user_segments_included = Column(JSON, nullable=True)  # List of segments
    alert_types_included = Column(JSON, nullable=True)  # List of alert types
    
    # Report metrics
    total_messages_sent = Column(Integer, default=0)
    total_engagements = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    total_revenue_impact = Column(Numeric(12, 2), default=0.0)
    total_cost = Column(Numeric(10, 4), default=0.0)
    
    # Performance summary
    avg_delivery_rate = Column(Float, default=0.0)
    avg_engagement_rate = Column(Float, default=0.0)
    avg_conversion_rate = Column(Float, default=0.0)
    avg_cost_per_engagement = Column(Numeric(10, 4), default=0.0)
    overall_roi = Column(Float, default=0.0)
    
    # Key insights
    top_performing_channel = Column(String(20), nullable=True)
    top_performing_alert_type = Column(String(50), nullable=True)
    most_engaged_segment = Column(String(20), nullable=True)
    key_insights = Column(JSON, nullable=True)  # List of insights
    
    # Report content
    report_data = Column(JSON, nullable=True)  # Full report data
    report_url = Column(String(500), nullable=True)  # Link to generated report
    
    # Distribution
    recipients = Column(JSON, nullable=True)  # List of recipient emails
    sent_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(36), nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_analytics_reports_report_type', 'report_type'),
        Index('idx_analytics_reports_report_date', 'report_date'),
        Index('idx_analytics_reports_period', 'report_period'),
    )


class UserSegmentPerformance(Base):
    """Performance metrics by user segment"""
    __tablename__ = 'user_segment_performance'
    
    id = Column(String(36), primary_key=True)
    
    # Segment identification
    user_segment = Column(Enum(UserSegment), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    
    # Segment metrics
    total_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    churned_users = Column(Integer, default=0)
    
    # Communication metrics
    messages_sent = Column(Integer, default=0)
    messages_delivered = Column(Integer, default=0)
    messages_engaged = Column(Integer, default=0)
    
    # Engagement rates
    delivery_rate = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    retention_rate = Column(Float, default=0.0)
    
    # Financial metrics
    avg_revenue_per_user = Column(Numeric(10, 2), default=0.0)
    total_revenue = Column(Numeric(12, 2), default=0.0)
    conversion_rate = Column(Float, default=0.0)
    
    # Channel performance
    channel_performance = Column(JSON, nullable=True)  # {channel: {metrics}}
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_segment_performance_segment_date', 'user_segment', 'date'),
        Index('idx_user_segment_performance_engagement_rate', 'engagement_rate'),
        Index('idx_user_segment_performance_retention_rate', 'retention_rate'),
    ) 