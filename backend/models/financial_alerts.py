from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import uuid

Base = declarative_base()

class FinancialAlert(Base):
    """Financial alert tracking and management"""
    
    __tablename__ = 'financial_alerts'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User identification
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Alert information
    alert_type = Column(String(50), nullable=False, index=True)  # cash_flow, bill_payment, subscription, spending_pattern, budget_exceeded
    alert_subtype = Column(String(50), nullable=True)  # negative_balance, upcoming_bill, unusual_spending, etc.
    urgency_level = Column(String(20), nullable=False, index=True)  # critical, high, medium, low
    
    # Financial context
    trigger_amount = Column(Float, nullable=True)  # Amount that triggered the alert
    current_balance = Column(Float, nullable=True)  # Current account balance
    projected_balance = Column(Float, nullable=True)  # Projected balance at trigger date
    due_date = Column(DateTime(timezone=True), nullable=True)  # For bill/subscription alerts
    days_until_negative = Column(Integer, nullable=True)  # Days until negative balance
    
    # Alert content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    sms_message = Column(Text, nullable=True)  # SMS-specific message
    email_subject = Column(String(200), nullable=True)
    email_content = Column(Text, nullable=True)
    
    # Communication tracking
    communication_channel = Column(String(20), nullable=False)  # sms, email, both
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Alert status
    status = Column(String(20), nullable=False, default='pending')  # pending, sent, delivered, read, responded, resolved, dismissed
    resolution_action = Column(String(50), nullable=True)  # user_action, system_resolved, dismissed
    
    # Metadata
    metadata = Column(JSONB, nullable=True)  # Additional context data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="financial_alerts")
    
    # Indexes
    __table_args__ = (
        Index('idx_financial_alerts_user_status', 'user_id', 'status'),
        Index('idx_financial_alerts_urgency_created', 'urgency_level', 'created_at'),
        Index('idx_financial_alerts_type_status', 'alert_type', 'status'),
        Index('idx_financial_alerts_due_date', 'due_date'),
    )
    
    def __repr__(self):
        return f'<FinancialAlert {self.alert_type}:{self.urgency_level} for user {self.user_id}>'

class UserFinancialContext(Base):
    """User financial context and preferences for alert personalization"""
    
    __tablename__ = 'user_financial_contexts'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User identification
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True)
    
    # Income information
    primary_income_source = Column(String(50), nullable=True)  # full_time, part_time, gig_work, business, investment
    secondary_income_sources = Column(JSONB, nullable=True)  # Array of additional income sources
    monthly_income = Column(Float, nullable=True)
    income_frequency = Column(String(20), nullable=True)  # weekly, bi_weekly, monthly, irregular
    
    # Financial obligations
    student_loan_payment = Column(Float, nullable=True)
    student_loan_due_date = Column(Integer, nullable=True)  # Day of month
    family_obligations = Column(Float, nullable=True)  # Monthly family support
    rent_mortgage = Column(Float, nullable=True)
    rent_mortgage_due_date = Column(Integer, nullable=True)  # Day of month
    
    # Emergency fund and savings
    emergency_fund_balance = Column(Float, nullable=True)
    emergency_fund_target = Column(Float, nullable=True)
    savings_balance = Column(Float, nullable=True)
    
    # Spending categories and budgets
    spending_categories = Column(JSONB, nullable=True)  # Category budgets and preferences
    regional_cost_of_living = Column(String(50), nullable=True)  # atlanta, houston, dc_metro, etc.
    
    # Financial goals
    primary_financial_goal = Column(String(100), nullable=True)
    secondary_goals = Column(JSONB, nullable=True)  # Array of additional goals
    
    # Alert preferences
    alert_preferences = Column(JSONB, nullable=True)  # User's alert preferences
    optimal_engagement_time = Column(String(20), nullable=True)  # morning, afternoon, evening, night
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="financial_context")
    
    def __repr__(self):
        return f'<UserFinancialContext for user {self.user_id}>'

class AlertRule(Base):
    """Configurable alert rules and thresholds"""
    
    __tablename__ = 'alert_rules'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    rule_name = Column(String(100), nullable=False, unique=True)
    rule_type = Column(String(50), nullable=False, index=True)  # cash_flow, bill_payment, subscription, spending_pattern, budget
    
    # Trigger conditions
    trigger_conditions = Column(JSONB, nullable=False)  # Conditions that trigger the alert
    threshold_values = Column(JSONB, nullable=True)  # Threshold values for triggers
    
    # Alert configuration
    urgency_level = Column(String(20), nullable=False)
    communication_channel = Column(String(20), nullable=False)
    message_template = Column(Text, nullable=False)
    sms_template = Column(Text, nullable=True)
    email_subject_template = Column(String(200), nullable=True)
    email_content_template = Column(Text, nullable=True)
    
    # Timing configuration
    advance_notice_days = Column(Integer, nullable=True)  # Days in advance to send alert
    retry_configuration = Column(JSONB, nullable=True)  # Retry logic for failed deliveries
    
    # Rule status
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # Rule priority for processing
    
    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_alert_rules_type_active', 'rule_type', 'is_active'),
        Index('idx_alert_rules_priority', 'priority'),
    )
    
    def __repr__(self):
        return f'<AlertRule {self.rule_name}:{self.rule_type}>'

class CashFlowForecast(Base):
    """Cash flow forecasting for alert detection"""
    
    __tablename__ = 'cash_flow_forecasts'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User identification
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Forecast information
    forecast_date = Column(DateTime(timezone=True), nullable=False, index=True)
    projected_balance = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Income and expenses
    projected_income = Column(Float, nullable=True)
    projected_expenses = Column(Float, nullable=True)
    known_transactions = Column(JSONB, nullable=True)  # Known upcoming transactions
    
    # Risk indicators
    risk_level = Column(String(20), nullable=True)  # low, medium, high, critical
    days_until_negative = Column(Integer, nullable=True)
    negative_balance_amount = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="cash_flow_forecasts")
    
    # Indexes
    __table_args__ = (
        Index('idx_cash_flow_forecasts_user_date', 'user_id', 'forecast_date'),
        Index('idx_cash_flow_forecasts_risk_level', 'risk_level'),
    )
    
    def __repr__(self):
        return f'<CashFlowForecast {self.forecast_date} for user {self.user_id}>'

class SpendingPattern(Base):
    """User spending pattern analysis for unusual spending detection"""
    
    __tablename__ = 'spending_patterns'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User identification
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Pattern information
    category = Column(String(50), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False)  # daily, weekly, monthly, seasonal
    
    # Statistical data
    average_amount = Column(Float, nullable=False)
    standard_deviation = Column(Float, nullable=True)
    frequency = Column(Float, nullable=True)  # Transactions per time period
    last_transaction_date = Column(DateTime(timezone=True), nullable=True)
    
    # Anomaly detection
    is_anomaly = Column(Boolean, default=False, nullable=False)
    anomaly_score = Column(Float, nullable=True)  # 0.0 to 1.0
    anomaly_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="spending_patterns")
    
    # Indexes
    __table_args__ = (
        Index('idx_spending_patterns_user_category', 'user_id', 'category'),
        Index('idx_spending_patterns_anomaly', 'is_anomaly', 'anomaly_score'),
    )
    
    def __repr__(self):
        return f'<SpendingPattern {self.category} for user {self.user_id}>'

class AlertDeliveryLog(Base):
    """Log of alert deliveries and responses"""
    
    __tablename__ = 'alert_delivery_logs'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert reference
    alert_id = Column(UUID(as_uuid=True), ForeignKey('financial_alerts.id'), nullable=False, index=True)
    
    # Delivery information
    delivery_method = Column(String(20), nullable=False)  # sms, email, push
    delivery_status = Column(String(20), nullable=False)  # sent, delivered, failed, bounced
    message_id = Column(String(100), nullable=True)  # External service message ID
    
    # Response tracking
    response_received = Column(Boolean, default=False, nullable=False)
    response_content = Column(Text, nullable=True)
    response_time = Column(DateTime(timezone=True), nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    alert = relationship("FinancialAlert", back_populates="delivery_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_alert_delivery_logs_alert_status', 'alert_id', 'delivery_status'),
        Index('idx_alert_delivery_logs_sent_at', 'sent_at'),
    )
    
    def __repr__(self):
        return f'<AlertDeliveryLog {self.delivery_method}:{self.delivery_status} for alert {self.alert_id}>'

# Add relationships to existing User model (placeholder)
# These would be added to the existing User model
"""
class User(Base):
    # ... existing fields ...
    
    # Financial alert relationships
    financial_alerts = relationship("FinancialAlert", back_populates="user")
    financial_context = relationship("UserFinancialContext", back_populates="user", uselist=False)
    cash_flow_forecasts = relationship("CashFlowForecast", back_populates="user")
    spending_patterns = relationship("SpendingPattern", back_populates="user")
"""

# Add relationship to FinancialAlert
FinancialAlert.delivery_logs = relationship("AlertDeliveryLog", back_populates="alert") 