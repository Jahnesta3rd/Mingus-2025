"""
Subscription Tier Models

This module defines the SQLAlchemy ORM models for subscription tier features
including custom categories, category rules, merchant analysis, cash flow forecasts,
and AI categorization results.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.models.base import Base


class CustomCategory(Base):
    """Model for storing custom categories"""
    
    __tablename__ = 'custom_categories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    category_name = Column(String(100), nullable=False, index=True)
    parent_category = Column(String(100), nullable=True, index=True)
    color = Column(String(7), nullable=False, default='#000000')  # Hex color
    icon = Column(String(50), nullable=False, default='default')
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rules = relationship("CategoryRule", back_populates="category", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_custom_categories_user_active', 'user_id', 'is_active'),
        Index('idx_custom_categories_name_user', 'category_name', 'user_id'),
    )


class CategoryRule(Base):
    """Model for storing custom category rules"""
    
    __tablename__ = 'category_rules'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(String(255), nullable=False, unique=True, index=True)
    category_id = Column(String(255), ForeignKey('custom_categories.category_id'), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    category_name = Column(String(100), nullable=False, index=True)
    rule_type = Column(String(50), nullable=False, index=True)  # merchant_name, amount_range, etc.
    rule_conditions = Column(JSON, nullable=False)  # Rule conditions as JSON
    priority = Column(Integer, nullable=False, default=1, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("CustomCategory", back_populates="rules")
    
    # Indexes
    __table_args__ = (
        Index('idx_category_rules_user_active', 'user_id', 'is_active'),
        Index('idx_category_rules_type_priority', 'rule_type', 'priority'),
        Index('idx_category_rules_category_user', 'category_id', 'user_id'),
    )


class MerchantAnalysis(Base):
    """Model for storing detailed merchant analysis"""
    
    __tablename__ = 'merchant_analyses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    merchant_name = Column(String(255), nullable=False, index=True)
    standardized_name = Column(String(255), nullable=False, index=True)
    merchant_type = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True, index=True)
    
    # Transaction analysis
    total_transactions = Column(Integer, nullable=False, default=0)
    total_amount = Column(Float, nullable=False, default=0.0)
    average_amount = Column(Float, nullable=False, default=0.0)
    first_transaction = Column(DateTime, nullable=False)
    last_transaction = Column(DateTime, nullable=False)
    
    # Spending patterns
    spending_frequency = Column(Float, nullable=False, default=0.0)
    spending_consistency = Column(Float, nullable=False, default=0.0)
    seasonal_patterns = Column(JSON, nullable=True)
    
    # Merchant insights
    merchant_score = Column(Float, nullable=False, default=0.0, index=True)
    risk_level = Column(String(20), nullable=False, default='low', index=True)
    fraud_indicators = Column(JSON, nullable=True)
    
    # Business intelligence
    business_type = Column(String(100), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_merchant_analyses_user_merchant', 'user_id', 'merchant_name'),
        Index('idx_merchant_analyses_score_risk', 'merchant_score', 'risk_level'),
        Index('idx_merchant_analyses_type_category', 'merchant_type', 'category'),
        Index('idx_merchant_analyses_updated', 'updated_at', 'user_id'),
    )


class CashFlowForecast(Base):
    """Model for storing cash flow forecasts"""
    
    __tablename__ = 'cash_flow_forecasts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forecast_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    forecast_period = Column(Integer, nullable=False, index=True)  # months
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    
    # Forecast data
    monthly_forecasts = Column(JSON, nullable=False)
    confidence_intervals = Column(JSON, nullable=True)
    
    # Income forecasting
    projected_income = Column(Float, nullable=False, default=0.0)
    income_growth_rate = Column(Float, nullable=False, default=0.0)
    income_volatility = Column(Float, nullable=False, default=0.0)
    
    # Expense forecasting
    projected_expenses = Column(Float, nullable=False, default=0.0)
    expense_growth_rate = Column(Float, nullable=False, default=0.0)
    expense_volatility = Column(Float, nullable=False, default=0.0)
    
    # Cash flow projections
    projected_cash_flow = Column(Float, nullable=False, default=0.0)
    cash_flow_trend = Column(String(20), nullable=False, default='stable', index=True)
    break_even_date = Column(DateTime, nullable=True)
    
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
        Index('idx_cash_flow_forecasts_user_period', 'user_id', 'forecast_period'),
        Index('idx_cash_flow_forecasts_trend_accuracy', 'cash_flow_trend', 'accuracy_score'),
        Index('idx_cash_flow_forecasts_updated', 'last_updated', 'user_id'),
        Index('idx_cash_flow_forecasts_date_range', 'start_date', 'end_date'),
    )


class AICategorizationResult(Base):
    """Model for storing AI categorization results"""
    
    __tablename__ = 'ai_categorization_results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    original_category = Column(String(100), nullable=False, index=True)
    ai_category = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False, default=0.0, index=True)
    categorization_method = Column(String(50), nullable=False, index=True)
    reasoning = Column(Text, nullable=True)
    alternatives = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_ai_categorization_user_transaction', 'user_id', 'transaction_id'),
        Index('idx_ai_categorization_confidence', 'confidence_score', 'created_at'),
        Index('idx_ai_categorization_method', 'categorization_method', 'created_at'),
        Index('idx_ai_categorization_original_ai', 'original_category', 'ai_category'),
    )


class SubscriptionTier(Base):
    """Model for storing user subscription tier information"""
    
    __tablename__ = 'subscription_tiers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    tier_type = Column(String(50), nullable=False, index=True)  # budget, mid_tier, professional
    tier_name = Column(String(100), nullable=False)
    tier_description = Column(Text, nullable=True)
    
    # Feature access
    features = Column(JSON, nullable=False)  # Dictionary of feature access
    limits = Column(JSON, nullable=False)  # Dictionary of feature limits
    
    # Subscription details
    subscription_id = Column(String(255), nullable=True, index=True)
    billing_cycle = Column(String(20), nullable=True)  # monthly, yearly
    next_billing_date = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    trial_end_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_subscription_tiers_type_active', 'tier_type', 'is_active'),
        Index('idx_subscription_tiers_billing', 'next_billing_date', 'is_active'),
        Index('idx_subscription_tiers_trial', 'trial_end_date', 'is_active'),
    )


class FeatureUsage(Base):
    """Model for tracking feature usage by users"""
    
    __tablename__ = 'feature_usage'
    
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
        Index('idx_feature_usage_user_feature', 'user_id', 'feature_type'),
        Index('idx_feature_usage_period', 'period_start', 'period_end'),
        Index('idx_feature_usage_last_used', 'last_used', 'user_id'),
    )


class TierUpgrade(Base):
    """Model for tracking tier upgrade history"""
    
    __tablename__ = 'tier_upgrades'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, nullable=False, index=True)
    from_tier = Column(String(50), nullable=False, index=True)
    to_tier = Column(String(50), nullable=False, index=True)
    upgrade_reason = Column(String(255), nullable=True)
    
    # Upgrade details
    upgrade_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    effective_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Billing information
    billing_amount = Column(Float, nullable=True)
    billing_currency = Column(String(3), nullable=True, default='USD')
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_tier_upgrades_user_date', 'user_id', 'upgrade_date'),
        Index('idx_tier_upgrades_from_to', 'from_tier', 'to_tier'),
        Index('idx_tier_upgrades_active', 'is_active', 'user_id'),
    ) 