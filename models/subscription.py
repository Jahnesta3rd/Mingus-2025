"""
MINGUS Application - Subscription Models
========================================

SQLAlchemy models for subscription and billing system.

Models:
- SubscriptionPlan: Tiered subscription plans with features
- Subscription: User subscription management with Stripe integration
- FeatureAccess: Feature access control with usage limits
- BillingHistory: Complete billing transaction history

Author: MINGUS Development Team
Date: January 2025
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Numeric, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from . import Base


class SubscriptionPlan(Base):
    """Tiered subscription plans with features and limits."""
    
    __tablename__ = 'subscription_plans'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Plan information
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    billing_cycle = Column(String(20), nullable=False)  # monthly, yearly
    
    # Features and limits
    features = Column(JSONB, nullable=False)
    limits = Column(JSONB)  # usage limits for features
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")
    
    # Validation
    @validates('name')
    def validate_name(self, key, name):
        """Validate plan name."""
        if not name or len(name.strip()) == 0:
            raise ValueError("Plan name cannot be empty")
        return name.strip()
    
    @validates('price')
    def validate_price(self, key, price):
        """Validate plan price."""
        if price <= 0:
            raise ValueError("Plan price must be positive")
        return price
    
    @validates('billing_cycle')
    def validate_billing_cycle(self, key, cycle):
        """Validate billing cycle."""
        valid_cycles = ['monthly', 'yearly']
        if cycle not in valid_cycles:
            raise ValueError(f"Billing cycle must be one of: {valid_cycles}")
        return cycle
    
    @validates('features')
    def validate_features(self, key, features):
        """Validate features JSON."""
        if not isinstance(features, dict):
            raise ValueError("Features must be a dictionary")
        return features
    
    # Methods
    def get_feature_limit(self, feature_name):
        """Get usage limit for a specific feature."""
        if not self.limits:
            return None
        return self.limits.get(f'{feature_name}_per_month')
    
    def has_feature(self, feature_name):
        """Check if plan includes a specific feature."""
        if not self.features:
            return False
        return self.features.get(feature_name, False)
    
    def to_dict(self):
        """Convert plan to dictionary."""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'price': float(self.price) if self.price else None,
            'billing_cycle': self.billing_cycle,
            'features': self.features,
            'limits': self.limits,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<SubscriptionPlan(id={self.id}, name='{self.name}', price={self.price})>"


class Subscription(Base):
    """User subscription management with Stripe integration."""
    
    __tablename__ = 'subscriptions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('subscription_plans.id'), nullable=False)
    
    # Stripe integration
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    stripe_customer_id = Column(String(255))
    
    # Subscription status
    status = Column(String(50), nullable=False, index=True)  # active, canceled, past_due, unpaid
    
    # Billing periods
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True))
    
    # Trial information
    trial_start = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    billing_history = relationship("BillingHistory", back_populates="subscription", cascade="all, delete-orphan")
    
    # Validation
    @validates('status')
    def validate_status(self, key, status):
        """Validate subscription status."""
        valid_statuses = ['active', 'canceled', 'past_due', 'unpaid', 'trialing']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    # Properties
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        return self.status == 'active' or self.status == 'trialing'
    
    @property
    def is_trial(self):
        """Check if subscription is in trial period."""
        if not self.trial_end:
            return False
        return datetime.now(timezone.utc) <= self.trial_end
    
    @property
    def days_until_renewal(self):
        """Calculate days until next renewal."""
        if not self.current_period_end:
            return None
        delta = self.current_period_end - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    # Methods
    def cancel(self, at_period_end=True):
        """Cancel subscription."""
        if at_period_end:
            self.cancel_at_period_end = True
        else:
            self.status = 'canceled'
            self.canceled_at = datetime.now(timezone.utc)
    
    def reactivate(self):
        """Reactivate canceled subscription."""
        if self.status == 'canceled':
            self.status = 'active'
            self.cancel_at_period_end = False
            self.canceled_at = None
    
    def to_dict(self):
        """Convert subscription to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'plan_id': str(self.plan_id),
            'stripe_subscription_id': self.stripe_subscription_id,
            'stripe_customer_id': self.stripe_customer_id,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'is_active': self.is_active,
            'is_trial': self.is_trial,
            'days_until_renewal': self.days_until_renewal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status='{self.status}')>"


class FeatureAccess(Base):
    """Feature access control with usage limits and tracking."""
    
    __tablename__ = 'feature_access'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Feature information
    feature_name = Column(String(100), nullable=False, index=True)
    is_enabled = Column(Boolean, default=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    usage_limit = Column(Integer)  # None for unlimited
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="feature_access")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'feature_name', name='uq_user_feature'),
    )
    
    # Validation
    @validates('usage_count')
    def validate_usage_count(self, key, count):
        """Validate usage count."""
        if count < 0:
            raise ValueError("Usage count cannot be negative")
        return count
    
    @validates('usage_limit')
    def validate_usage_limit(self, key, limit):
        """Validate usage limit."""
        if limit is not None and limit < 0:
            raise ValueError("Usage limit cannot be negative")
        return limit
    
    # Properties
    @property
    def is_unlimited(self):
        """Check if feature has unlimited usage."""
        return self.usage_limit is None
    
    @property
    def usage_remaining(self):
        """Calculate remaining usage."""
        if self.is_unlimited:
            return None
        if self.usage_limit is None:
            return None
        return max(0, self.usage_limit - self.usage_count)
    
    @property
    def is_expired(self):
        """Check if feature access has expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def can_use(self):
        """Check if user can use this feature."""
        if not self.is_enabled:
            return False
        if self.is_expired:
            return False
        if not self.is_unlimited and self.usage_remaining == 0:
            return False
        return True
    
    # Methods
    def increment_usage(self):
        """Increment usage count."""
        if not self.can_use:
            raise ValueError("Cannot use feature - access denied")
        
        self.usage_count += 1
        self.last_used_at = datetime.now(timezone.utc)
    
    def reset_usage(self):
        """Reset usage count to zero."""
        self.usage_count = 0
    
    def set_usage_limit(self, limit):
        """Set usage limit."""
        self.usage_limit = limit
    
    def to_dict(self):
        """Convert feature access to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'feature_name': self.feature_name,
            'is_enabled': self.is_enabled,
            'usage_count': self.usage_count,
            'usage_limit': self.usage_limit,
            'usage_remaining': self.usage_remaining,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_unlimited': self.is_unlimited,
            'is_expired': self.is_expired,
            'can_use': self.can_use,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<FeatureAccess(id={self.id}, user_id={self.user_id}, feature='{self.feature_name}', usage={self.usage_count})>"


class BillingHistory(Base):
    """Complete billing transaction history."""
    
    __tablename__ = 'billing_history'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'))
    
    # Stripe integration
    stripe_invoice_id = Column(String(255), unique=True, index=True)
    
    # Billing information
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='USD')
    status = Column(String(50), nullable=False)  # paid, unpaid, void, pending
    
    # Dates
    billing_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    
    # Additional information
    description = Column(Text)
    extra_metadata = Column('metadata', JSONB)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    subscription = relationship("Subscription", back_populates="billing_history")
    
    # Validation
    @validates('amount')
    def validate_amount(self, key, amount):
        """Validate billing amount."""
        if amount <= 0:
            raise ValueError("Billing amount must be positive")
        return amount
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate billing status."""
        valid_statuses = ['paid', 'unpaid', 'void', 'pending', 'failed']
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return status
    
    @validates('currency')
    def validate_currency(self, key, currency):
        """Validate currency code."""
        if len(currency) != 3:
            raise ValueError("Currency must be a 3-letter code")
        return currency.upper()
    
    # Properties
    @property
    def is_paid(self):
        """Check if invoice is paid."""
        return self.status == 'paid'
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        if not self.due_date or self.is_paid:
            return False
        return datetime.now(timezone.utc) > self.due_date
    
    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        delta = datetime.now(timezone.utc) - self.due_date
        return delta.days
    
    # Methods
    def mark_as_paid(self, paid_at=None):
        """Mark invoice as paid."""
        self.status = 'paid'
        self.paid_at = paid_at or datetime.now(timezone.utc)
    
    def mark_as_failed(self):
        """Mark invoice as failed."""
        self.status = 'failed'
    
    def to_dict(self):
        """Convert billing history to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'subscription_id': str(self.subscription_id) if self.subscription_id else None,
            'stripe_invoice_id': self.stripe_invoice_id,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'status': self.status,
            'billing_date': self.billing_date.isoformat() if self.billing_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'description': self.description,
            'metadata': self.extra_metadata,
            'is_paid': self.is_paid,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<BillingHistory(id={self.id}, user_id={self.user_id}, amount={self.amount}, status='{self.status}')>" 