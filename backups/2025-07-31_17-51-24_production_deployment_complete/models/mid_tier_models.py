"""
Mid-Tier Models

This module defines the SQLAlchemy ORM models for Mid-tier subscription features
including standard categorization results, spending insights, 6-month cash flow forecasts,
and savings goals.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.models.base import Base


class StandardCategorizationResult(Base):
    """Model for storing standard categorization results"""
    
    __tablename__ = 'standard_categorization_results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    original_category = Column(String(100), nullable=False, index=True)
    suggested_category = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False, default=0.0, index=True)
    categorization_method = Column(String(50), nullable=False, index=True)
    reasoning = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_standard_categorization_user_transaction', 'user_id', 'transaction_id'),
        Index('idx_standard_categorization_confidence', 'confidence_score', 'created_at'),
        Index('idx_standard_categorization_method', 'categorization_method', 'created_at'),
        Index('idx_standard_categorization_original_suggested', 'original_category', 'suggested_category'),
    )


class SpendingInsight(Base):
    """Model for storing basic spending insights"""
    
    __tablename__ = 'spending_insights'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    insight_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    insight_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    data = Column(JSON, nullable=False)
    impact_score = Column(Float, nullable=False, default=0.0, index=True)
    priority = Column(String(20), nullable=False, default='medium', index=True)
    is_actionable = Column(Boolean, default=True, index=True)
    action_description = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_dismissed = Column(Boolean, default=False, index=True)
    dismissed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_spending_insights_user_type', 'user_id', 'insight_type'),
        Index('idx_spending_insights_priority_impact', 'priority', 'impact_score'),
        Index('idx_spending_insights_actionable_active', 'is_actionable', 'is_active'),
        Index('idx_spending_insights_created', 'created_at', 'user_id'),
    )


class SavingsGoal(Base):
    """Model for storing savings goals"""
    
    __tablename__ = 'savings_goals'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    goal_name = Column(String(255), nullable=False, index=True)
    goal_type = Column(String(50), nullable=False, index=True)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, nullable=False, default=0.0)
    target_date = Column(DateTime, nullable=False, index=True)
    monthly_target = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default='not_started', index=True)
    progress_percentage = Column(Float, nullable=False, default=0.0, index=True)
    
    # Goal details
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True, default='#4ECDC4')  # Hex color
    icon = Column(String(50), nullable=True, default='target')
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_savings_goals_user_status', 'user_id', 'status'),
        Index('idx_savings_goals_type_status', 'goal_type', 'status'),
        Index('idx_savings_goals_progress', 'progress_percentage', 'user_id'),
        Index('idx_savings_goals_target_date', 'target_date', 'user_id'),
    )


class SavingsGoalProgress(Base):
    """Model for tracking savings goal progress history"""
    
    __tablename__ = 'savings_goal_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(String(255), ForeignKey('savings_goals.goal_id'), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    previous_amount = Column(Float, nullable=False)
    new_amount = Column(Float, nullable=False)
    amount_change = Column(Float, nullable=False)
    progress_percentage = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, index=True)
    
    # Update details
    update_reason = Column(String(255), nullable=True)
    update_source = Column(String(50), nullable=True)  # manual, automatic, transaction
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    goal = relationship("SavingsGoal")
    
    # Indexes
    __table_args__ = (
        Index('idx_savings_goal_progress_goal_date', 'goal_id', 'created_at'),
        Index('idx_savings_goal_progress_user_date', 'user_id', 'created_at'),
        Index('idx_savings_goal_progress_status', 'status', 'created_at'),
    )


class CashFlowForecast6Month(Base):
    """Model for storing 6-month cash flow forecasts"""
    
    __tablename__ = 'cash_flow_forecasts_6month'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forecast_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    forecast_period = Column(Integer, nullable=False, default=6, index=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    
    # Monthly forecasts
    monthly_forecasts = Column(JSON, nullable=False)
    
    # Summary data
    projected_income = Column(Float, nullable=False, default=0.0)
    projected_expenses = Column(Float, nullable=False, default=0.0)
    projected_cash_flow = Column(Float, nullable=False, default=0.0)
    cash_flow_trend = Column(String(20), nullable=False, default='stable', index=True)
    
    # Model information
    model_version = Column(String(20), nullable=False, default='1.0')
    accuracy_score = Column(Float, nullable=False, default=0.0, index=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_cash_flow_forecasts_6month_user_date', 'user_id', 'created_at'),
        Index('idx_cash_flow_forecasts_6month_trend', 'cash_flow_trend', 'accuracy_score'),
        Index('idx_cash_flow_forecasts_6month_period', 'forecast_period', 'user_id'),
    )


class MidTierFeatureUsage(Base):
    """Model for tracking Mid-tier feature usage"""
    
    __tablename__ = 'mid_tier_feature_usage'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    feature_type = Column(String(50), nullable=False, index=True)
    usage_count = Column(Integer, nullable=False, default=0)
    last_used = Column(DateTime, nullable=True)
    
    # Usage period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)
    
    # Usage details
    usage_data = Column(JSON, nullable=True)  # Additional usage statistics
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_mid_tier_feature_usage_user_feature', 'user_id', 'feature_type'),
        Index('idx_mid_tier_feature_usage_period', 'period_start', 'period_end'),
        Index('idx_mid_tier_feature_usage_last_used', 'last_used', 'user_id'),
    )


class MidTierInsightPreference(Base):
    """Model for storing user preferences for Mid-tier insights"""
    
    __tablename__ = 'mid_tier_insight_preferences'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # Insight preferences
    insight_types_enabled = Column(JSON, nullable=False, default=list)  # List of enabled insight types
    insight_frequency = Column(String(20), nullable=False, default='weekly')  # daily, weekly, monthly
    max_insights_per_period = Column(Integer, nullable=False, default=10)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    in_app_notifications = Column(Boolean, default=True)
    
    # Filter preferences
    min_impact_score = Column(Float, nullable=False, default=0.3)
    priority_filter = Column(JSON, nullable=True)  # List of priority levels to show
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_mid_tier_insight_preferences_user', 'user_id'),
    )


class MidTierGoalTemplate(Base):
    """Model for storing savings goal templates"""
    
    __tablename__ = 'mid_tier_goal_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(String(255), nullable=False, unique=True, index=True)
    goal_type = Column(String(50), nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template defaults
    default_target_amount = Column(Float, nullable=True)
    default_duration_months = Column(Integer, nullable=True)
    default_monthly_target = Column(Float, nullable=True)
    
    # Template metadata
    category = Column(String(100), nullable=True, index=True)
    difficulty_level = Column(String(20), nullable=True, index=True)  # easy, medium, hard
    estimated_impact = Column(String(20), nullable=True)  # low, medium, high
    
    # Template details
    tips = Column(JSON, nullable=True)  # List of tips for achieving the goal
    milestones = Column(JSON, nullable=True)  # List of milestone amounts and descriptions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_mid_tier_goal_templates_type', 'goal_type', 'difficulty_level'),
        Index('idx_mid_tier_goal_templates_category', 'category', 'estimated_impact'),
    ) 