"""
MINGUS Application - Subscription Data Models
============================================

Comprehensive SQLAlchemy models for subscription management that integrate
with Stripe and PostgreSQL database.

Author: MINGUS Development Team
Date: January 2025
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey,
    Numeric, Enum, Index, UniqueConstraint, CheckConstraint, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from typing import Optional, Dict, Any, List
import uuid

from .base import Base
from ..payment.stripe_integration import SubscriptionTier


class BillingCycle(PyEnum):
    """Billing cycle enumeration."""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKLY = "weekly"
    DAILY = "daily"


class SubscriptionStatus(PyEnum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIAL = "trial"
    EXPIRED = "expired"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class PaymentStatus(PyEnum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"


class UsageType(PyEnum):
    """Usage tracking type enumeration."""
    ANALYTICS_REPORTS = "analytics_reports"
    DATA_EXPORTS = "data_exports"
    SUPPORT_REQUESTS = "support_requests"
    AI_INSIGHTS = "ai_insights"
    API_REQUESTS = "api_requests"
    GOALS = "goals"
    INVESTMENT_ACCOUNTS = "investment_accounts"
    CUSTOM_CATEGORIES = "custom_categories"
    TEAM_MEMBERS = "team_members"


class MINGUSSubscription(Base):
    """MINGUS subscription model that integrates with Stripe."""
    
    __tablename__ = 'mingus_subscriptions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    user = relationship("User", back_populates="subscriptions")
    
    # Stripe integration
    stripe_subscription_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=False)
    
    # Subscription details
    tier = Column(Enum(SubscriptionTier), nullable=False)
    billing_cycle = Column(Enum(BillingCycle), nullable=False)
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.INCOMPLETE)
    
    # Pricing information
    amount = Column(Numeric(10, 2), nullable=False)  # Amount in cents
    currency = Column(String(3), nullable=False, default='usd')
    discount_amount = Column(Numeric(10, 2), nullable=True)  # Discount amount in cents
    discount_percentage = Column(Integer, nullable=True)  # Discount percentage
    
    # Billing dates
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage limits and tracking
    usage_limits = Column(JSON, nullable=False, default=dict)
    current_usage = Column(JSON, nullable=False, default=dict)
    
    # Metadata (avoid reserved attribute name 'metadata')
    extra_metadata = Column('metadata', JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    invoices = relationship("MINGUSInvoice", back_populates="subscription", cascade="all, delete-orphan")
    usage_records = relationship("MINGUSUsageRecord", back_populates="subscription", cascade="all, delete-orphan")
    payment_methods = relationship("MINGUSPaymentMethod", back_populates="subscription", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_subscription_user_status', 'user_id', 'status'),
        Index('idx_subscription_stripe_customer', 'stripe_customer_id'),
        Index('idx_subscription_tier_billing', 'tier', 'billing_cycle'),
        Index('idx_subscription_period_end', 'current_period_end'),
        UniqueConstraint('user_id', 'stripe_subscription_id', name='uq_user_stripe_subscription'),
        {'extend_existing': True},
    )
    
    @validates('amount')
    def validate_amount(self, key, value):
        """Validate subscription amount."""
        if value <= 0:
            raise ValueError("Subscription amount must be positive")
        return value
    
    @validates('currency')
    def validate_currency(self, key, value):
        """Validate currency code."""
        if value not in ['usd', 'eur', 'gbp', 'cad', 'aud']:
            raise ValueError("Unsupported currency")
        return value.lower()
    
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
    
    def is_trial(self) -> bool:
        """Check if subscription is in trial period."""
        if not self.trial_end:
            return False
        return datetime.utcnow() < self.trial_end
    
    def days_until_renewal(self) -> int:
        """Calculate days until next renewal."""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)
    
    def get_usage_percentage(self, usage_type: UsageType) -> float:
        """Get usage percentage for a specific type."""
        limit = self.usage_limits.get(usage_type.value, 0)
        current = self.current_usage.get(usage_type.value, 0)
        
        if limit == 0:
            return 0.0
        if limit == -1:  # Unlimited
            return 0.0
        
        return min(100.0, (current / limit) * 100)
    
    def can_use_feature(self, usage_type: UsageType, amount: int = 1) -> bool:
        """Check if user can use a feature based on limits."""
        limit = self.usage_limits.get(usage_type.value, 0)
        current = self.current_usage.get(usage_type.value, 0)
        
        if limit == -1:  # Unlimited
            return True
        
        return current + amount <= limit
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'stripe_subscription_id': self.stripe_subscription_id,
            'stripe_customer_id': self.stripe_customer_id,
            'stripe_price_id': self.stripe_price_id,
            'tier': self.tier.value,
            'billing_cycle': self.billing_cycle.value,
            'status': self.status.value,
            'amount': float(self.amount),
            'currency': self.currency,
            'discount_amount': float(self.discount_amount) if self.discount_amount else None,
            'discount_percentage': self.discount_percentage,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'usage_limits': self.usage_limits,
            'current_usage': self.current_usage,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active(),
            'is_trial': self.is_trial(),
            'days_until_renewal': self.days_until_renewal()
        }


class MINGUSInvoice(Base):
    """MINGUS invoice model that integrates with Stripe invoices."""
    
    __tablename__ = 'mingus_invoices'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('mingus_subscriptions.id'), nullable=False, index=True)
    subscription = relationship("MINGUSSubscription", back_populates="invoices")
    
    # Stripe integration
    stripe_invoice_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    
    # Invoice details
    invoice_number = Column(String(255), nullable=False, unique=True)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False)  # Amount before tax/discounts
    tax = Column(Numeric(10, 2), nullable=False, default=0)
    discount = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False)  # Final amount
    amount_paid = Column(Numeric(10, 2), nullable=False, default=0)
    amount_remaining = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default='usd')
    
    # Billing dates
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Invoice items
    items = Column(JSON, nullable=False, default=list)
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_invoice_subscription_status', 'subscription_id', 'status'),
        Index('idx_invoice_due_date', 'due_date'),
        Index('idx_invoice_payment_intent', 'stripe_payment_intent_id'),
        {'extend_existing': True},
    )
    
    @validates('total')
    def validate_total(self, key, value):
        """Validate invoice total."""
        if value < 0:
            raise ValueError("Invoice total cannot be negative")
        return value
    
    def is_paid(self) -> bool:
        """Check if invoice is paid."""
        return self.status in [PaymentStatus.SUCCEEDED, PaymentStatus.PARTIALLY_REFUNDED]
    
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if not self.due_date or self.is_paid():
            return False
        return datetime.utcnow() > self.due_date
    
    def get_payment_percentage(self) -> float:
        """Get payment percentage."""
        if self.total == 0:
            return 100.0
        return min(100.0, (float(self.amount_paid) / float(self.total)) * 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice to dictionary."""
        return {
            'id': str(self.id),
            'subscription_id': str(self.subscription_id),
            'stripe_invoice_id': self.stripe_invoice_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'invoice_number': self.invoice_number,
            'status': self.status.value,
            'subtotal': float(self.subtotal),
            'tax': float(self.tax),
            'discount': float(self.discount),
            'total': float(self.total),
            'amount_paid': float(self.amount_paid),
            'amount_remaining': float(self.amount_remaining),
            'currency': self.currency,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'items': self.items,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_paid': self.is_paid(),
            'is_overdue': self.is_overdue(),
            'payment_percentage': self.get_payment_percentage()
        }


class MINGUSPaymentMethod(Base):
    """MINGUS payment method model that integrates with Stripe payment methods."""
    
    __tablename__ = 'mingus_payment_methods'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('mingus_subscriptions.id'), nullable=False, index=True)
    subscription = relationship("MINGUSSubscription", back_populates="payment_methods")
    
    # Stripe integration
    stripe_payment_method_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Payment method details
    type = Column(String(50), nullable=False)  # card, bank_account, etc.
    brand = Column(String(50), nullable=True)  # visa, mastercard, etc.
    last4 = Column(String(4), nullable=True)
    exp_month = Column(Integer, nullable=True)
    exp_year = Column(Integer, nullable=True)
    country = Column(String(2), nullable=True)
    
    # Billing details
    billing_details = Column(JSON, nullable=True)
    
    # Status
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_method_subscription', 'subscription_id', 'is_default'),
        Index('idx_payment_method_type', 'type'),
        Index('idx_payment_method_active', 'is_active'),
        {'extend_existing': True},
    )
    
    def is_expired(self) -> bool:
        """Check if payment method is expired."""
        if not self.exp_month or not self.exp_year:
            return False
        
        now = datetime.utcnow()
        return now.year > self.exp_year or (now.year == self.exp_year and now.month > self.exp_month)
    
    def get_display_name(self) -> str:
        """Get display name for payment method."""
        if self.type == 'card':
            brand = self.brand or 'Card'
            return f"{brand.title()} •••• {self.last4}"
        elif self.type == 'bank_account':
            return f"Bank Account •••• {self.last4}"
        else:
            return f"{self.type.title()} •••• {self.last4}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payment method to dictionary."""
        return {
            'id': str(self.id),
            'subscription_id': str(self.subscription_id),
            'stripe_payment_method_id': self.stripe_payment_method_id,
            'type': self.type,
            'brand': self.brand,
            'last4': self.last4,
            'exp_month': self.exp_month,
            'exp_year': self.exp_year,
            'country': self.country,
            'billing_details': self.billing_details,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_expired': self.is_expired(),
            'display_name': self.get_display_name()
        }


class MINGUSUsageRecord(Base):
    """MINGUS usage tracking model for subscription features."""
    
    __tablename__ = 'mingus_usage_records'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('mingus_subscriptions.id'), nullable=False, index=True)
    subscription = relationship("MINGUSSubscription", back_populates="usage_records")
    
    # Usage details
    usage_type = Column(Enum(UsageType), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)
    
    # Usage period
    usage_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_subscription_type', 'subscription_id', 'usage_type'),
        Index('idx_usage_date', 'usage_date'),
        Index('idx_usage_type_date', 'usage_type', 'usage_date'),
        {'extend_existing': True},
    )
    
    @validates('quantity')
    def validate_quantity(self, key, value):
        """Validate usage quantity."""
        if value <= 0:
            raise ValueError("Usage quantity must be positive")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert usage record to dictionary."""
        return {
            'id': str(self.id),
            'subscription_id': str(self.subscription_id),
            'usage_type': self.usage_type.value,
            'quantity': self.quantity,
            'description': self.description,
            'usage_date': self.usage_date.isoformat() if self.usage_date else None,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class MINGUSSubscriptionTier(Base):
    """MINGUS subscription tier configuration model."""
    
    __tablename__ = 'mingus_subscription_tiers'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tier details
    tier = Column(Enum(SubscriptionTier), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing
    monthly_price = Column(Numeric(10, 2), nullable=False)  # Price in cents
    yearly_price = Column(Numeric(10, 2), nullable=False)  # Price in cents
    currency = Column(String(3), nullable=False, default='usd')
    
    # Stripe integration
    stripe_monthly_price_id = Column(String(255), nullable=True)
    stripe_yearly_price_id = Column(String(255), nullable=True)
    
    # Features and limits
    features = Column(JSON, nullable=False, default=dict)
    limits = Column(JSON, nullable=False, default=dict)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_featured = Column(Boolean, nullable=False, default=False)
    
    # Sort order
    sort_order = Column(Integer, nullable=False, default=0)
    
    # Metadata (avoid reserved attribute name 'metadata')
    extra_metadata = Column('metadata', JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_tier_active', 'is_active'),
        Index('idx_tier_sort', 'sort_order'),
        Index('idx_tier_featured', 'is_featured'),
        {'extend_existing': True},
    )
    
    @validates('monthly_price', 'yearly_price')
    def validate_price(self, key, value):
        """Validate tier prices."""
        if value < 0:
            raise ValueError("Price cannot be negative")
        return value
    
    def get_price(self, billing_cycle: BillingCycle) -> float:
        """Get price for specific billing cycle."""
        if billing_cycle == BillingCycle.MONTHLY:
            return float(self.monthly_price)
        elif billing_cycle == BillingCycle.YEARLY:
            return float(self.yearly_price)
        else:
            return float(self.monthly_price)  # Default to monthly
    
    def get_stripe_price_id(self, billing_cycle: BillingCycle) -> Optional[str]:
        """Get Stripe price ID for specific billing cycle."""
        if billing_cycle == BillingCycle.MONTHLY:
            return self.stripe_monthly_price_id
        elif billing_cycle == BillingCycle.YEARLY:
            return self.stripe_yearly_price_id
        else:
            return self.stripe_monthly_price_id
    
    def get_yearly_discount_percentage(self) -> float:
        """Calculate yearly discount percentage."""
        if self.monthly_price == 0:
            return 0.0
        
        yearly_monthly_cost = float(self.monthly_price) * 12
        yearly_cost = float(self.yearly_price)
        
        if yearly_monthly_cost == 0:
            return 0.0
        
        discount = ((yearly_monthly_cost - yearly_cost) / yearly_monthly_cost) * 100
        return max(0.0, discount)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription tier to dictionary."""
        return {
            'id': str(self.id),
            'tier': self.tier.value,
            'name': self.name,
            'description': self.description,
            'monthly_price': float(self.monthly_price),
            'yearly_price': float(self.yearly_price),
            'currency': self.currency,
            'stripe_monthly_price_id': self.stripe_monthly_price_id,
            'stripe_yearly_price_id': self.stripe_yearly_price_id,
            'features': self.features,
            'limits': self.limits,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'sort_order': self.sort_order,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'yearly_discount_percentage': self.get_yearly_discount_percentage()
        }


class MINGUSBillingEvent(Base):
    """MINGUS billing event log for audit and tracking."""
    
    __tablename__ = 'mingus_billing_events'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('mingus_subscriptions.id'), nullable=True, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('mingus_invoices.id'), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False)  # subscription.created, payment.succeeded, etc.
    event_source = Column(String(50), nullable=False, default='stripe')  # stripe, manual, system
    
    # Event data
    event_data = Column(JSON, nullable=False, default=dict)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # Stripe integration
    stripe_event_id = Column(String(255), nullable=True, index=True)
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON, nullable=True)
    
    # Timestamps
    event_timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_billing_event_type', 'event_type'),
        Index('idx_billing_event_timestamp', 'event_timestamp'),
        Index('idx_billing_event_user', 'user_id', 'event_timestamp'),
        Index('idx_billing_event_stripe', 'stripe_event_id'),
        {'extend_existing': True},
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert billing event to dictionary."""
        return {
            'id': str(self.id),
            'subscription_id': str(self.subscription_id) if self.subscription_id else None,
            'invoice_id': str(self.invoice_id) if self.invoice_id else None,
            'event_type': self.event_type,
            'event_source': self.event_source,
            'event_data': self.event_data,
            'previous_state': self.previous_state,
            'new_state': self.new_state,
            'user_id': str(self.user_id) if self.user_id else None,
            'stripe_event_id': self.stripe_event_id,
            'metadata': self.extra_metadata,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 

# Aliases expected by tests
Subscription = MINGUSSubscription
BillingEvent = MINGUSBillingEvent