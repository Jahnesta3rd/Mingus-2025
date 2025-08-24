"""
Manual Transaction Models for MINGUS Budget Tier

This module provides data models for manual transaction entry functionality
available to Budget tier users who cannot link bank accounts.
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint, JSON,
    Numeric, SmallInteger, BigInteger, Date
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from backend.models.base import Base

logger = logging.getLogger(__name__)


class TransactionEntryType(Enum):
    """Manual transaction entry types"""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"


class ExpenseCategory(Enum):
    """Basic expense categories for Budget tier"""
    FOOD_DINING = "food_dining"
    TRANSPORTATION = "transportation"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    UTILITIES = "utilities"
    HOUSING = "housing"
    INSURANCE = "insurance"
    EDUCATION = "education"
    TRAVEL = "travel"
    SUBSCRIPTIONS = "subscriptions"
    PERSONAL_CARE = "personal_care"
    GIFTS = "gifts"
    CHARITY = "charity"
    OTHER = "other"


class RecurringFrequency(Enum):
    """Recurring transaction frequencies"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ManualTransaction(Base):
    """Manual transaction model for Budget tier users"""
    
    __tablename__ = 'manual_transactions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Transaction information
    name = Column(String(500), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    entry_type = Column(String(50), nullable=False)  # income, expense, transfer, refund
    category = Column(String(50), nullable=False)
    
    # Transaction details
    date = Column(Date, nullable=False, index=True)
    description = Column(Text, nullable=True)
    merchant_name = Column(String(255), nullable=True)
    
    # Tags and metadata
    tags = Column(JSONB, nullable=True)  # Array of tag strings
    metadata = Column(JSONB, nullable=True)  # Additional transaction metadata
    
    # Recurring transaction information
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_frequency = Column(String(50), nullable=True)
    recurring_start_date = Column(Date, nullable=True)
    recurring_end_date = Column(Date, nullable=True)
    parent_transaction_id = Column(UUID(as_uuid=True), ForeignKey('manual_transactions.id'), nullable=True)
    
    # Status and timing
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="manual_transactions")
    parent_transaction = relationship("ManualTransaction", remote_side=[id], back_populates="recurring_transactions")
    recurring_transactions = relationship("ManualTransaction", back_populates="parent_transaction")
    
    # Indexes
    __table_args__ = (
        Index('idx_manual_transactions_user_date', 'user_id', 'date'),
        Index('idx_manual_transactions_type_category', 'entry_type', 'category'),
        Index('idx_manual_transactions_recurring', 'is_recurring', 'recurring_frequency'),
        Index('idx_manual_transactions_active', 'is_active'),
        CheckConstraint('amount > 0', name='check_positive_amount'),
    )
    
    @validates('entry_type')
    def validate_entry_type(self, key, value):
        """Validate transaction entry type"""
        valid_types = [t.value for t in TransactionEntryType]
        if value not in valid_types:
            raise ValueError(f"Invalid entry type: {value}")
        return value
    
    @validates('category')
    def validate_category(self, key, value):
        """Validate expense category"""
        valid_categories = [c.value for c in ExpenseCategory]
        if value not in valid_categories:
            raise ValueError(f"Invalid category: {value}")
        return value
    
    @validates('amount')
    def validate_amount(self, key, value):
        """Validate transaction amount"""
        if not isinstance(value, (int, float, Decimal)):
            raise ValueError("Amount must be a number")
        if value <= 0:
            raise ValueError("Amount must be greater than 0")
        return Decimal(str(value))
    
    @validates('date')
    def validate_date(self, key, value):
        """Validate transaction date"""
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'amount': float(self.amount),
            'entry_type': self.entry_type,
            'category': self.category,
            'date': self.date.isoformat() if self.date else None,
            'description': self.description,
            'merchant_name': self.merchant_name,
            'tags': self.tags or [],
            'is_recurring': self.is_recurring,
            'recurring_frequency': self.recurring_frequency,
            'recurring_start_date': self.recurring_start_date.isoformat() if self.recurring_start_date else None,
            'recurring_end_date': self.recurring_end_date.isoformat() if self.recurring_end_date else None,
            'parent_transaction_id': str(self.parent_transaction_id) if self.parent_transaction_id else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ManualTransaction {self.name} ({self.amount}) for user {self.user_id}>'


class TransactionTemplate(Base):
    """Transaction templates for quick entry"""
    
    __tablename__ = 'transaction_templates'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Template information
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    entry_type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    
    # Template details
    description = Column(Text, nullable=True)
    merchant_name = Column(String(255), nullable=True)
    tags = Column(JSONB, nullable=True)
    
    # Usage tracking
    use_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status and timing
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="transaction_templates")
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_templates_user', 'user_id'),
        Index('idx_transaction_templates_active', 'is_active'),
        CheckConstraint('amount > 0', name='check_template_positive_amount'),
    )
    
    @validates('entry_type')
    def validate_entry_type(self, key, value):
        """Validate transaction entry type"""
        valid_types = [t.value for t in TransactionEntryType]
        if value not in valid_types:
            raise ValueError(f"Invalid entry type: {value}")
        return value
    
    @validates('category')
    def validate_category(self, key, value):
        """Validate expense category"""
        valid_categories = [c.value for c in ExpenseCategory]
        if value not in valid_categories:
            raise ValueError(f"Invalid category: {value}")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'amount': float(self.amount),
            'entry_type': self.entry_type,
            'category': self.category,
            'description': self.description,
            'merchant_name': self.merchant_name,
            'tags': self.tags or [],
            'use_count': self.use_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<TransactionTemplate {self.name} ({self.amount}) for user {self.user_id}>'


class CashFlowForecast(Base):
    """Cash flow forecast model for Budget tier users"""
    
    __tablename__ = 'cash_flow_forecasts'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Forecast information
    forecast_start_date = Column(Date, nullable=False)
    forecast_end_date = Column(Date, nullable=False)
    opening_balance = Column(Numeric(15, 2), nullable=False)
    projected_income = Column(Numeric(15, 2), nullable=False)
    projected_expenses = Column(Numeric(15, 2), nullable=False)
    closing_balance = Column(Numeric(15, 2), nullable=False)
    
    # Forecast details
    daily_balances = Column(JSONB, nullable=True)  # Array of daily balance objects
    risk_dates = Column(JSONB, nullable=True)  # Array of risk date strings
    recommendations = Column(JSONB, nullable=True)  # Array of recommendation strings
    confidence_score = Column(Float, nullable=False, default=0.0)
    
    # Forecast metadata
    assumptions = Column(JSONB, nullable=True)  # Forecast assumptions
    data_quality_score = Column(Float, nullable=True)  # Quality of input data
    last_transaction_date = Column(Date, nullable=True)  # Date of last transaction used
    
    # Status and timing
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="cash_flow_forecasts")
    
    # Indexes
    __table_args__ = (
        Index('idx_cash_flow_forecasts_user', 'user_id'),
        Index('idx_cash_flow_forecasts_dates', 'forecast_start_date', 'forecast_end_date'),
        Index('idx_cash_flow_forecasts_active', 'is_active'),
    )
    
    @validates('confidence_score')
    def validate_confidence_score(self, key, value):
        """Validate confidence score"""
        if not isinstance(value, (int, float)):
            raise ValueError("Confidence score must be a number")
        if value < 0 or value > 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return float(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert forecast to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'forecast_start_date': self.forecast_start_date.isoformat() if self.forecast_start_date else None,
            'forecast_end_date': self.forecast_end_date.isoformat() if self.forecast_end_date else None,
            'opening_balance': float(self.opening_balance),
            'projected_income': float(self.projected_income),
            'projected_expenses': float(self.projected_expenses),
            'closing_balance': float(self.closing_balance),
            'daily_balances': self.daily_balances or [],
            'risk_dates': self.risk_dates or [],
            'recommendations': self.recommendations or [],
            'confidence_score': self.confidence_score,
            'assumptions': self.assumptions or {},
            'data_quality_score': self.data_quality_score,
            'last_transaction_date': self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<CashFlowForecast {self.forecast_start_date} to {self.forecast_end_date} for user {self.user_id}>'


class BudgetTierUsage(Base):
    """Usage tracking for Budget tier features"""
    
    __tablename__ = 'budget_tier_usage'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Usage period
    usage_month = Column(Integer, nullable=False)  # 1-12
    usage_year = Column(Integer, nullable=False)
    
    # Feature usage counts
    manual_transactions_used = Column(Integer, default=0, nullable=False)
    cash_flow_forecasts_used = Column(Integer, default=0, nullable=False)
    expense_reports_used = Column(Integer, default=0, nullable=False)
    
    # Usage limits
    manual_transactions_limit = Column(Integer, default=100, nullable=False)
    cash_flow_forecasts_limit = Column(Integer, default=2, nullable=False)
    expense_reports_limit = Column(Integer, default=5, nullable=False)
    
    # Usage tracking
    last_usage_date = Column(DateTime(timezone=True), nullable=True)
    is_reset = Column(Boolean, default=False, nullable=False)  # Track if monthly reset has been applied
    
    # Metadata
    metadata = Column(JSONB, nullable=True)  # Additional usage data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="budget_tier_usage")
    
    # Indexes
    __table_args__ = (
        Index('idx_budget_tier_usage_user_period', 'user_id', 'usage_month', 'usage_year'),
        Index('idx_budget_tier_usage_period', 'usage_month', 'usage_year'),
        UniqueConstraint('user_id', 'usage_month', 'usage_year', name='uq_user_monthly_usage'),
    )
    
    def get_usage_percentage(self, feature_name: str) -> float:
        """Get usage percentage for a specific feature"""
        if feature_name == 'manual_transactions':
            return (self.manual_transactions_used / self.manual_transactions_limit * 100) if self.manual_transactions_limit > 0 else 0
        elif feature_name == 'cash_flow_forecasts':
            return (self.cash_flow_forecasts_used / self.cash_flow_forecasts_limit * 100) if self.cash_flow_forecasts_limit > 0 else 0
        elif feature_name == 'expense_reports':
            return (self.expense_reports_used / self.expense_reports_limit * 100) if self.expense_reports_limit > 0 else 0
        return 0
    
    def is_feature_available(self, feature_name: str) -> bool:
        """Check if a feature is available (not at limit)"""
        if feature_name == 'manual_transactions':
            return self.manual_transactions_used < self.manual_transactions_limit
        elif feature_name == 'cash_flow_forecasts':
            return self.cash_flow_forecasts_used < self.cash_flow_forecasts_limit
        elif feature_name == 'expense_reports':
            return self.expense_reports_used < self.expense_reports_limit
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert usage to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'usage_month': self.usage_month,
            'usage_year': self.usage_year,
            'manual_transactions': {
                'used': self.manual_transactions_used,
                'limit': self.manual_transactions_limit,
                'remaining': self.manual_transactions_limit - self.manual_transactions_used,
                'percentage': self.get_usage_percentage('manual_transactions')
            },
            'cash_flow_forecasts': {
                'used': self.cash_flow_forecasts_used,
                'limit': self.cash_flow_forecasts_limit,
                'remaining': self.cash_flow_forecasts_limit - self.cash_flow_forecasts_used,
                'percentage': self.get_usage_percentage('cash_flow_forecasts')
            },
            'expense_reports': {
                'used': self.expense_reports_used,
                'limit': self.expense_reports_limit,
                'remaining': self.expense_reports_limit - self.expense_reports_used,
                'percentage': self.get_usage_percentage('expense_reports')
            },
            'last_usage_date': self.last_usage_date.isoformat() if self.last_usage_date else None,
            'is_reset': self.is_reset,
            'metadata': self.metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<BudgetTierUsage {self.usage_month}/{self.usage_year} for user {self.user_id}>' 