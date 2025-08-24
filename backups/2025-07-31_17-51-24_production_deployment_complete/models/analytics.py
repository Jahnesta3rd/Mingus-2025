"""
Analytics Models for Transaction Processing

This module defines the SQLAlchemy models for storing transaction analysis results,
spending insights, budget alerts, and other analytics data.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.models.base import Base


class TransactionInsight(Base):
    """Model for storing transaction analysis insights"""
    
    __tablename__ = 'transaction_insights'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    account_id = Column(String(255), nullable=False, index=True)
    
    # Analysis results
    category = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    transaction_type = Column(String(50), nullable=False, index=True)
    merchant_name = Column(String(255), nullable=True)
    
    # Flags
    is_recurring = Column(Boolean, default=False, index=True)
    is_subscription = Column(Boolean, default=False, index=True)
    is_anomaly = Column(Boolean, default=False, index=True)
    
    # Risk and scoring
    risk_score = Column(Float, default=0.0)
    fraud_score = Column(Float, default=0.0)
    
    # Additional data
    insights = Column(Text, nullable=True)  # JSON string of insights
    tags = Column(Text, nullable=True)  # JSON string of tags
    metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_insights_user_date', 'user_id', 'created_at'),
        Index('idx_transaction_insights_category', 'category', 'created_at'),
        Index('idx_transaction_insights_type', 'transaction_type', 'created_at'),
        Index('idx_transaction_insights_recurring', 'is_recurring', 'created_at'),
        Index('idx_transaction_insights_subscription', 'is_subscription', 'created_at'),
    )


class SpendingCategory(Base):
    """Model for storing spending category analysis"""
    
    __tablename__ = 'spending_categories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    category_name = Column(String(100), nullable=False, index=True)
    
    # Spending statistics
    total_amount = Column(Float, nullable=False, default=0.0)
    transaction_count = Column(Integer, nullable=False, default=0)
    average_amount = Column(Float, nullable=False, default=0.0)
    
    # Trend analysis
    trend_direction = Column(String(20), nullable=True)  # 'increasing', 'decreasing', 'stable'
    percentage_change = Column(Float, nullable=True)
    trend_period = Column(String(20), nullable=True)  # 'week', 'month', 'quarter', 'year'
    
    # Budget information
    budget_limit = Column(Float, nullable=True)
    budget_used = Column(Float, nullable=True, default=0.0)
    budget_percentage = Column(Float, nullable=True)
    
    # Analysis period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Recommendations
    recommendations = Column(Text, nullable=True)  # JSON string of recommendations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_spending_categories_user_period', 'user_id', 'period_start', 'period_end'),
        Index('idx_spending_categories_category_period', 'category_name', 'period_start', 'period_end'),
        Index('idx_spending_categories_budget', 'user_id', 'budget_percentage'),
    )


class BudgetAlert(Base):
    """Model for storing budget alerts and notifications"""
    
    __tablename__ = 'budget_alerts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    category_name = Column(String(100), nullable=False, index=True)
    
    # Alert details
    alert_type = Column(String(50), nullable=False)  # 'warning', 'critical', 'over_budget'
    alert_level = Column(String(20), nullable=False)  # 'low', 'medium', 'high'
    
    # Spending information
    current_spending = Column(Float, nullable=False)
    budget_limit = Column(Float, nullable=False)
    percentage_used = Column(Float, nullable=False)
    
    # Time information
    days_remaining = Column(Integer, nullable=True)
    alert_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_dismissed = Column(Boolean, default=False, index=True)
    dismissed_at = Column(DateTime, nullable=True)
    dismissed_by = Column(Integer, nullable=True)
    
    # Recommendations
    recommendations = Column(Text, nullable=True)  # JSON string of recommendations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_budget_alerts_user_active', 'user_id', 'is_active'),
        Index('idx_budget_alerts_category_active', 'category_name', 'is_active'),
        Index('idx_budget_alerts_level_date', 'alert_level', 'alert_date'),
        Index('idx_budget_alerts_percentage', 'percentage_used', 'alert_date'),
    )


class SpendingPattern(Base):
    """Model for storing spending pattern analysis"""
    
    __tablename__ = 'spending_patterns'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly', 'seasonal'
    
    # Pattern details
    category_name = Column(String(100), nullable=True, index=True)
    merchant_name = Column(String(255), nullable=True, index=True)
    
    # Pattern characteristics
    frequency = Column(Integer, nullable=False)  # Number of occurrences
    average_amount = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Timing information
    day_of_week = Column(Integer, nullable=True)  # 0-6 (Monday-Sunday)
    day_of_month = Column(Integer, nullable=True)  # 1-31
    month_of_year = Column(Integer, nullable=True)  # 1-12
    hour_of_day = Column(Integer, nullable=True)  # 0-23
    
    # Confidence and reliability
    confidence_score = Column(Float, nullable=False, default=0.0)
    reliability_score = Column(Float, nullable=False, default=0.0)
    
    # Pattern metadata
    first_occurrence = Column(DateTime, nullable=False)
    last_occurrence = Column(DateTime, nullable=False)
    next_predicted = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_recurring = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_spending_patterns_user_type', 'user_id', 'pattern_type'),
        Index('idx_spending_patterns_category', 'category_name', 'is_active'),
        Index('idx_spending_patterns_recurring', 'is_recurring', 'is_active'),
        Index('idx_spending_patterns_timing', 'day_of_week', 'hour_of_day'),
    )


class AnomalyDetection(Base):
    """Model for storing anomaly detection results"""
    
    __tablename__ = 'anomaly_detections'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    transaction_id = Column(String(255), nullable=False, index=True)
    
    # Anomaly details
    anomaly_type = Column(String(50), nullable=False)  # 'amount', 'merchant', 'timing', 'location'
    severity = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    confidence = Column(Float, nullable=False, default=0.0)
    
    # Anomaly characteristics
    expected_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=False)
    deviation_percentage = Column(Float, nullable=True)
    
    # Context information
    category_name = Column(String(100), nullable=True, index=True)
    merchant_name = Column(String(255), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    
    # Analysis details
    detection_method = Column(String(50), nullable=False)  # 'statistical', 'ml', 'rule_based'
    algorithm_version = Column(String(20), nullable=True)
    
    # Status
    is_confirmed = Column(Boolean, default=False, index=True)
    is_false_positive = Column(Boolean, default=False, index=True)
    user_feedback = Column(String(50), nullable=True)  # 'confirmed', 'false_positive', 'ignored'
    
    # Timestamps
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_anomaly_detections_user_severity', 'user_id', 'severity'),
        Index('idx_anomaly_detections_type_severity', 'anomaly_type', 'severity'),
        Index('idx_anomaly_detections_confirmed', 'is_confirmed', 'detected_at'),
        Index('idx_anomaly_detections_feedback', 'user_feedback', 'detected_at'),
    )


class SubscriptionAnalysis(Base):
    """Model for storing subscription analysis results"""
    
    __tablename__ = 'subscription_analyses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Subscription details
    merchant_name = Column(String(255), nullable=False, index=True)
    subscription_name = Column(String(255), nullable=True)
    
    # Financial information
    monthly_cost = Column(Float, nullable=False)
    annual_cost = Column(Float, nullable=False)
    total_spent = Column(Float, nullable=False, default=0.0)
    
    # Usage information
    transaction_count = Column(Integer, nullable=False, default=0)
    first_transaction = Column(DateTime, nullable=False)
    last_transaction = Column(DateTime, nullable=False)
    next_expected = Column(DateTime, nullable=True)
    
    # Subscription characteristics
    billing_cycle = Column(String(20), nullable=True)  # 'monthly', 'quarterly', 'annual'
    category = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Analysis results
    usage_score = Column(Float, nullable=True)  # How much value user gets
    cost_score = Column(Float, nullable=True)  # Cost-effectiveness
    recommendation = Column(String(50), nullable=True)  # 'keep', 'cancel', 'downgrade', 'upgrade'
    
    # User feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    user_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_subscription_analyses_user_active', 'user_id', 'is_active'),
        Index('idx_subscription_analyses_merchant', 'merchant_name', 'is_active'),
        Index('idx_subscription_analyses_cost', 'monthly_cost', 'is_active'),
        Index('idx_subscription_analyses_recommendation', 'recommendation', 'is_active'),
    )


class FinancialInsight(Base):
    """Model for storing general financial insights"""
    
    __tablename__ = 'financial_insights'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Insight details
    insight_type = Column(String(50), nullable=False, index=True)  # 'savings', 'spending', 'income', 'trend'
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Insight data
    data = Column(JSON, nullable=True)  # Structured data for the insight
    metrics = Column(JSON, nullable=True)  # Key metrics and calculations
    
    # Impact and priority
    impact_score = Column(Float, nullable=False, default=0.0)  # 0-1 scale
    priority = Column(String(20), nullable=False, default='medium')  # 'low', 'medium', 'high', 'critical'
    
    # Actionability
    is_actionable = Column(Boolean, default=True, index=True)
    action_type = Column(String(50), nullable=True)  # 'review', 'change', 'optimize', 'monitor'
    action_description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_dismissed = Column(Boolean, default=False, index=True)
    dismissed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_financial_insights_user_type', 'user_id', 'insight_type'),
        Index('idx_financial_insights_priority', 'priority', 'impact_score'),
        Index('idx_financial_insights_actionable', 'is_actionable', 'is_active'),
        Index('idx_financial_insights_generated', 'generated_at', 'is_active'),
    )


class AnalyticsReport(Base):
    """Model for storing analytics reports"""
    
    __tablename__ = 'analytics_reports'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Report details
    report_type = Column(String(50), nullable=False)  # 'spending', 'income', 'budget', 'trends', 'comprehensive'
    report_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Report period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Report data
    data = Column(JSON, nullable=False)  # Complete report data
    summary = Column(JSON, nullable=True)  # Executive summary
    charts = Column(JSON, nullable=True)  # Chart configurations
    
    # Report status
    status = Column(String(20), nullable=False, default='generated')  # 'generated', 'delivered', 'viewed'
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    viewed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_analytics_reports_user_type', 'user_id', 'report_type'),
        Index('idx_analytics_reports_period', 'period_start', 'period_end'),
        Index('idx_analytics_reports_status', 'status', 'generated_at'),
    ) 