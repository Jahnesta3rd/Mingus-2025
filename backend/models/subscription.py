"""
Subscription models for MINGUS subscription management
Handles Stripe integration, billing, and subscription lifecycle
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .base import Base


class SubscriptionStatus(enum.Enum):
    """Subscription status enumeration"""
    ACTIVE = "active"  # paying subscription
    PAST_DUE = "past_due"  # payment failed, grace period
    CANCELED = "canceled"  # user canceled subscription
    UNPAID = "unpaid"  # payment failed, access suspended
    TRIAL = "trial"


class PaymentStatus(enum.Enum):
    """Payment status enumeration"""
    SUCCEEDED = "succeeded"
    PENDING = "pending"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    DISPUTED = "disputed"


class BillingCycle(enum.Enum):
    """Billing cycle enumeration"""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class TaxCalculationMethod(enum.Enum):
    """Tax calculation method enumeration"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    EXEMPT = "exempt"


class RefundStatus(enum.Enum):
    """Refund status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class AuditEventType(enum.Enum):
    """Audit event type enumeration"""
    # Subscription events
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    SUBSCRIPTION_REACTIVATED = "subscription_reactivated"
    SUBSCRIPTION_TIER_CHANGED = "subscription_tier_changed"
    SUBSCRIPTION_BILLING_CHANGED = "subscription_billing_changed"
    
    # Payment events
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REFUNDED = "payment_refunded"
    PAYMENT_DISPUTED = "payment_disputed"
    PAYMENT_METHOD_ADDED = "payment_method_added"
    PAYMENT_METHOD_REMOVED = "payment_method_removed"
    PAYMENT_METHOD_UPDATED = "payment_method_updated"
    
    # Feature usage events
    FEATURE_USED = "feature_used"
    FEATURE_LIMIT_REACHED = "feature_limit_reached"
    FEATURE_ACCESS_DENIED = "feature_access_denied"
    USAGE_RESET = "usage_reset"
    
    # Compliance events
    TAX_CALCULATION = "tax_calculation"
    COMPLIANCE_CHECK = "compliance_check"
    DATA_EXPORT = "data_export"
    PRIVACY_REQUEST = "privacy_request"
    GDPR_REQUEST = "gdpr_request"
    
    # System events
    SYSTEM_MAINTENANCE = "system_maintenance"
    SECURITY_EVENT = "security_event"
    ERROR_OCCURRED = "error_occurred"


class AuditSeverity(enum.Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PricingTierType(enum.Enum):
    """Pricing tier types"""
    BUDGET = "budget"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"


class Customer(Base):
    """Links MINGUS users to Stripe customers"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    stripe_customer_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    phone = Column(String(50))
    address = Column(JSON)  # Store address as JSON
    tax_exempt = Column(String(50), default='none')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="customer")
    subscriptions = relationship("Subscription", back_populates="customer")
    payment_methods = relationship("PaymentMethod", back_populates="customer")
    billing_history = relationship("BillingHistory", back_populates="customer")
    billing_disputes = relationship("BillingDispute", back_populates="customer")
    
    def __repr__(self):
        return f'<Customer {self.stripe_customer_id}>'
    
    def to_dict(self):
        """Convert customer to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stripe_customer_id': self.stripe_customer_id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'tax_exempt': self.tax_exempt,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PricingTier(Base):
    """Defines the three tier structure for MINGUS subscriptions"""
    __tablename__ = 'pricing_tiers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tier_type = Column(Enum(PricingTierType), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    monthly_price = Column(Float, nullable=False)
    yearly_price = Column(Float, nullable=False)
    stripe_price_id_monthly = Column(String(255), unique=True)
    stripe_price_id_yearly = Column(String(255), unique=True)
    
    # Feature limits
    max_health_checkins_per_month = Column(Integer, default=4)
    max_financial_reports_per_month = Column(Integer, default=2)
    max_ai_insights_per_month = Column(Integer, default=0)
    max_projects = Column(Integer, default=1)
    max_team_members = Column(Integer, default=1)
    max_storage_gb = Column(Integer, default=1)
    max_api_calls_per_month = Column(Integer, default=1000)
    advanced_analytics = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    custom_integrations = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="pricing_tier")
    
    def __repr__(self):
        return f'<PricingTier {self.tier_type.value}>'
    
    def to_dict(self):
        """Convert pricing tier to dictionary"""
        return {
            'id': self.id,
            'tier_type': self.tier_type.value,
            'name': self.name,
            'description': self.description,
            'monthly_price': self.monthly_price,
            'yearly_price': self.yearly_price,
            'stripe_price_id_monthly': self.stripe_price_id_monthly,
            'stripe_price_id_yearly': self.stripe_price_id_yearly,
            'max_health_checkins_per_month': self.max_health_checkins_per_month,
            'max_financial_reports_per_month': self.max_financial_reports_per_month,
            'max_ai_insights_per_month': self.max_ai_insights_per_month,
            'max_projects': self.max_projects,
            'max_team_members': self.max_team_members,
            'max_storage_gb': self.max_storage_gb,
            'max_api_calls_per_month': self.max_api_calls_per_month,
            'advanced_analytics': self.advanced_analytics,
            'priority_support': self.priority_support,
            'custom_integrations': self.custom_integrations,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Subscription(Base):
    """Tracks subscription lifecycle"""
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    pricing_tier_id = Column(Integer, ForeignKey('pricing_tiers.id'), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True, nullable=False, index=True)
    
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.TRIAL)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime)
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    
    # Billing details
    billing_cycle = Column(Enum(BillingCycle), nullable=False, default=BillingCycle.MONTHLY)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    
    # Proration and billing features
    proration_behavior = Column(String(50), default='create_prorations')  # Stripe proration behavior
    proration_date = Column(DateTime)
    next_billing_date = Column(DateTime)
    
    # Tax and compliance
    tax_percent = Column(Float, default=0.0)
    tax_calculation_method = Column(Enum(TaxCalculationMethod), default=TaxCalculationMethod.AUTOMATIC)
    tax_exempt = Column(String(50), default='none')
    tax_identification_number = Column(String(255))
    
    # Usage-based billing
    usage_type = Column(String(50), default='licensed')  # 'licensed' or 'metered'
    usage_aggregation = Column(String(50), default='sum')  # 'sum', 'last_during_period', 'last_ever', 'max'
    
    # Metadata (avoid reserved attribute name 'metadata')
    extra_metadata = Column('metadata', JSON)  # Store additional Stripe metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    pricing_tier = relationship("PricingTier", back_populates="subscriptions")
    usage = relationship("SubscriptionUsage", back_populates="subscription")
    
    def __repr__(self):
        return f'<Subscription {self.stripe_subscription_id}>'
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'pricing_tier_id': self.pricing_tier_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'status': self.status.value,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'billing_cycle': self.billing_cycle,
            'amount': self.amount,
            'currency': self.currency,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PaymentMethod(Base):
    """Stores payment method details"""
    __tablename__ = 'payment_methods'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    stripe_payment_method_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Payment method details
    type = Column(String(50), nullable=False)  # 'card', 'bank_account', etc.
    brand = Column(String(50))  # 'visa', 'mastercard', etc.
    last4 = Column(String(4))
    exp_month = Column(Integer)
    exp_year = Column(Integer)
    country = Column(String(2))
    fingerprint = Column(String(255))
    
    # Billing details
    billing_details = Column(JSON)  # Store billing address, name, etc.
    
    # Status
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="payment_methods")
    
    def __repr__(self):
        return f'<PaymentMethod {self.stripe_payment_method_id}>'
    
    def to_dict(self):
        """Convert payment method to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'stripe_payment_method_id': self.stripe_payment_method_id,
            'type': self.type,
            'brand': self.brand,
            'last4': self.last4,
            'exp_month': self.exp_month,
            'exp_year': self.exp_year,
            'country': self.country,
            'fingerprint': self.fingerprint,
            'billing_details': self.billing_details,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BillingHistory(Base):
    """Transaction and invoice tracking"""
    __tablename__ = 'billing_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    
    # Stripe references
    stripe_invoice_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_payment_intent_id = Column(String(255), index=True)
    
    # Invoice details
    invoice_number = Column(String(255))
    amount_due = Column(Float, nullable=False)
    amount_paid = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    
    # Status
    status = Column(Enum(PaymentStatus), nullable=False)
    paid = Column(Boolean, default=False)
    
    # Dates
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    paid_date = Column(DateTime)
    
    # Description and metadata
    description = Column(Text)
    extra_metadata = Column('metadata', JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="billing_history")
    billing_disputes = relationship("BillingDispute", back_populates="invoice")
    
    def __repr__(self):
        return f'<BillingHistory {self.stripe_invoice_id}>'
    
    def to_dict(self):
        """Convert billing history to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'subscription_id': self.subscription_id,
            'stripe_invoice_id': self.stripe_invoice_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'invoice_number': self.invoice_number,
            'amount_due': self.amount_due,
            'amount_paid': self.amount_paid,
            'currency': self.currency,
            'status': self.status.value,
            'paid': self.paid,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'description': self.description,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SubscriptionUsage(Base):
    """Tracks feature usage against limits"""
    __tablename__ = 'subscription_usage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    
    # Usage tracking
    usage_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Feature usage counts
    projects_created = Column(Integer, default=0)
    team_members_added = Column(Integer, default=0)
    storage_used_mb = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    
    # Additional usage metrics
    login_count = Column(Integer, default=0)
    feature_usage = Column(JSON)  # Store feature-specific usage data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="usage")
    
    def __repr__(self):
        return f'<SubscriptionUsage {self.subscription_id} - {self.usage_date}>'
    
    def to_dict(self):
        """Convert subscription usage to dictionary"""
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'usage_date': self.usage_date.isoformat() if self.usage_date else None,
            'projects_created': self.projects_created,
            'team_members_added': self.team_members_added,
            'storage_used_mb': self.storage_used_mb,
            'api_calls_made': self.api_calls_made,
            'login_count': self.login_count,
            'feature_usage': self.feature_usage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class FeatureUsage(Base):
    """Tracks feature usage against tier-specific limits"""
    __tablename__ = 'feature_usage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    
    # Usage period
    usage_month = Column(Integer, nullable=False)  # 1-12
    usage_year = Column(Integer, nullable=False)
    
    # Feature usage counts
    health_checkins_used = Column(Integer, default=0)
    financial_reports_used = Column(Integer, default=0)
    ai_insights_used = Column(Integer, default=0)
    projects_created = Column(Integer, default=0)
    team_members_added = Column(Integer, default=0)
    storage_used_mb = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    
    # Usage tracking
    last_usage_date = Column(DateTime, default=datetime.utcnow)
    is_reset = Column(Boolean, default=False)  # Track if monthly reset has been applied
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON)  # Store additional usage data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscription = relationship("Subscription")
    
    def __repr__(self):
        return f'<FeatureUsage {self.subscription_id} - {self.usage_month}/{self.usage_year}>'
    
    def to_dict(self):
        """Convert feature usage to dictionary"""
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'usage_month': self.usage_month,
            'usage_year': self.usage_year,
            'health_checkins_used': self.health_checkins_used,
            'financial_reports_used': self.financial_reports_used,
            'ai_insights_used': self.ai_insights_used,
            'projects_created': self.projects_created,
            'team_members_added': self.team_members_added,
            'storage_used_mb': self.storage_used_mb,
            'api_calls_made': self.api_calls_made,
            'last_usage_date': self.last_usage_date.isoformat() if self.last_usage_date else None,
            'is_reset': self.is_reset,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_usage_percentage(self, feature_name, tier_limits):
        """Calculate usage percentage for a specific feature"""
        current_usage = getattr(self, f'{feature_name}_used', 0)
        tier_limit = getattr(tier_limits, f'max_{feature_name}_per_month', 0)
        
        if tier_limit == -1:  # Unlimited
            return 0.0
        elif tier_limit == 0:
            return 100.0 if current_usage > 0 else 0.0
        
        return min(100.0, (current_usage / tier_limit) * 100)
    
    def is_feature_available(self, feature_name, tier_limits):
        """Check if a feature is available based on current usage and tier limits"""
        current_usage = getattr(self, f'{feature_name}_used', 0)
        tier_limit = getattr(tier_limits, f'max_{feature_name}_per_month', 0)
        
        if tier_limit == -1:  # Unlimited
            return True
        elif tier_limit == 0:  # Not available
            return False
        
        return current_usage < tier_limit


class TaxCalculation(Base):
    """Tax calculation and compliance tracking"""
    __tablename__ = 'tax_calculations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    invoice_id = Column(Integer, ForeignKey('billing_history.id'))
    
    # Tax details
    tax_rate = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    taxable_amount = Column(Float, nullable=False, default=0.0)
    tax_jurisdiction = Column(String(255))
    tax_registration_number = Column(String(255))
    
    # Calculation method
    calculation_method = Column(Enum(TaxCalculationMethod), default=TaxCalculationMethod.AUTOMATIC)
    is_exempt = Column(Boolean, default=False)
    exemption_reason = Column(String(255))
    
    # Stripe integration
    stripe_tax_calculation_id = Column(String(255), unique=True)
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer")
    subscription = relationship("Subscription")
    invoice = relationship("BillingHistory")
    
    def __repr__(self):
        return f'<TaxCalculation {self.id} - {self.tax_amount}>'
    
    def to_dict(self):
        """Convert tax calculation to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'subscription_id': self.subscription_id,
            'invoice_id': self.invoice_id,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'taxable_amount': self.taxable_amount,
            'tax_jurisdiction': self.tax_jurisdiction,
            'tax_registration_number': self.tax_registration_number,
            'calculation_method': self.calculation_method.value if self.calculation_method else None,
            'is_exempt': self.is_exempt,
            'exemption_reason': self.exemption_reason,
            'stripe_tax_calculation_id': self.stripe_tax_calculation_id,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Refund(Base):
    """Refund management and tracking"""
    __tablename__ = 'refunds'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('billing_history.id'), nullable=False)
    
    # Refund details
    stripe_refund_id = Column(String(255), unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    reason = Column(String(255))  # 'duplicate', 'fraudulent', 'requested_by_customer'
    status = Column(Enum(RefundStatus), nullable=False, default=RefundStatus.PENDING)
    
    # Processing details
    processing_fee = Column(Float, default=0.0)
    failure_reason = Column(String(255))
    failure_balance_transaction = Column(String(255))
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer")
    invoice = relationship("BillingHistory")
    
    def __repr__(self):
        return f'<Refund {self.stripe_refund_id} - {self.amount}>'
    
    def to_dict(self):
        """Convert refund to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'invoice_id': self.invoice_id,
            'stripe_refund_id': self.stripe_refund_id,
            'amount': self.amount,
            'currency': self.currency,
            'reason': self.reason,
            'status': self.status.value if self.status else None,
            'processing_fee': self.processing_fee,
            'failure_reason': self.failure_reason,
            'failure_balance_transaction': self.failure_balance_transaction,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Credit(Base):
    """Credit management for customer accounts"""
    __tablename__ = 'credits'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Credit details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    credit_type = Column(String(50), nullable=False)  # 'refund', 'promotional', 'adjustment', 'overpayment'
    description = Column(Text)
    
    # Usage tracking
    original_amount = Column(Float, nullable=False)
    remaining_amount = Column(Float, nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime)
    
    # Stripe integration
    stripe_credit_note_id = Column(String(255), unique=True)
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer")
    
    def __repr__(self):
        return f'<Credit {self.id} - {self.amount} {self.currency}>'
    
    def to_dict(self):
        """Convert credit to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'amount': self.amount,
            'currency': self.currency,
            'credit_type': self.credit_type,
            'description': self.description,
            'original_amount': self.original_amount,
            'remaining_amount': self.remaining_amount,
            'is_used': self.is_used,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'stripe_credit_note_id': self.stripe_credit_note_id,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ProrationCalculation(Base):
    """Automatic proration calculations for subscription changes"""
    __tablename__ = 'proration_calculations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'), nullable=False)
    
    # Proration details
    proration_date = Column(DateTime, nullable=False)
    old_amount = Column(Float, nullable=False)
    new_amount = Column(Float, nullable=False)
    proration_amount = Column(Float, nullable=False)
    currency = Column(String(3), default='USD')
    
    # Calculation method
    calculation_method = Column(String(50), default='exact_day')  # 'exact_day', 'exact_time', 'exact_month'
    proration_behavior = Column(String(50), default='create_prorations')
    
    # Usage tracking
    usage_until_proration = Column(Float, default=0.0)
    usage_after_proration = Column(Float, default=0.0)
    
    # Stripe integration
    stripe_proration_id = Column(String(255), unique=True)
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscription = relationship("Subscription")
    
    def __repr__(self):
        return f'<ProrationCalculation {self.id} - {self.proration_amount}>'
    
    def to_dict(self):
        """Convert proration calculation to dictionary"""
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'proration_date': self.proration_date.isoformat() if self.proration_date else None,
            'old_amount': self.old_amount,
            'new_amount': self.new_amount,
            'proration_amount': self.proration_amount,
            'currency': self.currency,
            'calculation_method': self.calculation_method,
            'proration_behavior': self.proration_behavior,
            'usage_until_proration': self.usage_until_proration,
            'usage_after_proration': self.usage_after_proration,
            'stripe_proration_id': self.stripe_proration_id,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AuditLog(Base):
    """Comprehensive audit trail for all subscription and billing events"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event identification
    event_type = Column(Enum(AuditEventType), nullable=False)
    severity = Column(Enum(AuditSeverity), nullable=False, default=AuditSeverity.INFO)
    event_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # User and session context
    user_id = Column(Integer, ForeignKey('users.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    session_id = Column(String(255))
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    
    # Related entities
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    invoice_id = Column(Integer, ForeignKey('billing_history.id'))
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'))
    feature_usage_id = Column(Integer, ForeignKey('feature_usage.id'))
    
    # Event details
    event_description = Column(Text, nullable=False)
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    changed_fields = Column(JSON)  # List of changed fields
    
    # Compliance and security
    compliance_impact = Column(Boolean, default=False)
    security_impact = Column(Boolean, default=False)
    data_classification = Column(String(50), default='internal')  # internal, confidential, restricted
    
    # External references
    stripe_event_id = Column(String(255))
    external_reference = Column(String(255))
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    customer = relationship("Customer")
    subscription = relationship("Subscription")
    invoice = relationship("BillingHistory")
    payment_method = relationship("PaymentMethod")
    feature_usage = relationship("FeatureUsage")
    
    def __repr__(self):
        return f'<AuditLog {self.event_type.value} - {self.event_timestamp}>'
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type.value if self.event_type else None,
            'severity': self.severity.value if self.severity else None,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'user_id': self.user_id,
            'customer_id': self.customer_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'subscription_id': self.subscription_id,
            'invoice_id': self.invoice_id,
            'payment_method_id': self.payment_method_id,
            'feature_usage_id': self.feature_usage_id,
            'event_description': self.event_description,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'changed_fields': self.changed_fields,
            'compliance_impact': self.compliance_impact,
            'security_impact': self.security_impact,
            'data_classification': self.data_classification,
            'stripe_event_id': self.stripe_event_id,
            'external_reference': self.external_reference,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ComplianceRecord(Base):
    """Compliance tracking and reporting"""
    __tablename__ = 'compliance_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Compliance details
    compliance_type = Column(String(100), nullable=False)  # GDPR, SOX, PCI, etc.
    requirement_id = Column(String(255))
    requirement_description = Column(Text)
    
    # Entity context
    customer_id = Column(Integer, ForeignKey('customers.id'))
    subscription_id = Column(Integer, ForeignKey('subscriptions.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Compliance status
    status = Column(String(50), nullable=False, default='pending')  # pending, compliant, non_compliant, exempt
    compliance_date = Column(DateTime)
    next_review_date = Column(DateTime)
    
    # Evidence and documentation
    evidence_description = Column(Text)
    evidence_files = Column(JSON)  # List of file references
    auditor_notes = Column(Text)
    
    # Risk assessment
    risk_level = Column(String(20), default='low')  # low, medium, high, critical
    risk_description = Column(Text)
    mitigation_actions = Column(JSON)
    
    # External references
    external_audit_id = Column(String(255))
    regulatory_reference = Column(String(255))
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer")
    subscription = relationship("Subscription")
    user = relationship("User")
    
    def __repr__(self):
        return f'<ComplianceRecord {self.compliance_type} - {self.status}>'
    
    def to_dict(self):
        """Convert compliance record to dictionary"""
        return {
            'id': self.id,
            'compliance_type': self.compliance_type,
            'requirement_id': self.requirement_id,
            'requirement_description': self.requirement_description,
            'customer_id': self.customer_id,
            'subscription_id': self.subscription_id,
            'user_id': self.user_id,
            'status': self.status,
            'compliance_date': self.compliance_date.isoformat() if self.compliance_date else None,
            'next_review_date': self.next_review_date.isoformat() if self.next_review_date else None,
            'evidence_description': self.evidence_description,
            'evidence_files': self.evidence_files,
            'auditor_notes': self.auditor_notes,
            'risk_level': self.risk_level,
            'risk_description': self.risk_description,
            'mitigation_actions': self.mitigation_actions,
            'external_audit_id': self.external_audit_id,
            'regulatory_reference': self.regulatory_reference,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SecurityEvent(Base):
    """Security event tracking and monitoring"""
    __tablename__ = 'security_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event identification
    event_type = Column(String(100), nullable=False)  # login_failure, suspicious_activity, data_breach, etc.
    severity = Column(Enum(AuditSeverity), nullable=False, default=AuditSeverity.INFO)
    event_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # User and session context
    user_id = Column(Integer, ForeignKey('users.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    session_id = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(Text)
    location_data = Column(JSON)  # Geographic location, ISP, etc.
    
    # Security details
    threat_level = Column(String(20), default='low')  # low, medium, high, critical
    attack_vector = Column(String(100))  # SQL injection, XSS, brute force, etc.
    indicators = Column(JSON)  # Security indicators and patterns
    response_actions = Column(JSON)  # Actions taken in response
    
    # Investigation
    investigation_status = Column(String(50), default='open')  # open, investigating, resolved, closed
    investigator_id = Column(Integer, ForeignKey('users.id'))
    investigation_notes = Column(Text)
    resolution_date = Column(DateTime)
    
    # External references
    security_tool_id = Column(String(255))
    external_threat_id = Column(String(255))
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    customer = relationship("Customer")
    investigator = relationship("User", foreign_keys=[investigator_id])
    
    def __repr__(self):
        return f'<SecurityEvent {self.event_type} - {self.severity.value}>'
    
    def to_dict(self):
        """Convert security event to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'severity': self.severity.value if self.severity else None,
            'event_timestamp': self.event_timestamp.isoformat() if self.event_timestamp else None,
            'user_id': self.user_id,
            'customer_id': self.customer_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'location_data': self.location_data,
            'threat_level': self.threat_level,
            'attack_vector': self.attack_vector,
            'indicators': self.indicators,
            'response_actions': self.response_actions,
            'investigation_status': self.investigation_status,
            'investigator_id': self.investigator_id,
            'investigation_notes': self.investigation_notes,
            'resolution_date': self.resolution_date.isoformat() if self.resolution_date else None,
            'security_tool_id': self.security_tool_id,
            'external_threat_id': self.external_threat_id,
            'metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ============================================================================
# BILLING DISPUTE MODELS
# ============================================================================

class BillingDispute(Base):
    """Billing dispute management and tracking"""
    __tablename__ = 'billing_disputes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    invoice_id = Column(Integer, ForeignKey('billing_history.id'), nullable=False)
    
    # Dispute details
    dispute_type = Column(String(50), nullable=False)  # 'chargeback', 'refund_request', 'billing_error', 'service_issue'
    dispute_reason = Column(Text, nullable=False)
    dispute_amount = Column(Float, nullable=False)
    original_amount = Column(Float, nullable=False)
    
    # Status tracking
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'under_review', 'resolved', 'closed'
    contact_preference = Column(String(20), default='email')  # 'email', 'phone', 'portal'
    
    # Supporting information
    supporting_documents = Column(JSON)  # List of document URLs
    resolution_notes = Column(Text)
    resolution_amount = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", back_populates="billing_disputes")
    invoice = relationship("BillingHistory", back_populates="billing_disputes")
    comments = relationship("DisputeComment", back_populates="dispute", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BillingDispute(id={self.id}, customer_id={self.customer_id}, status='{self.status}')>"
    
    def to_dict(self):
        """Convert billing dispute to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'invoice_id': self.invoice_id,
            'dispute_type': self.dispute_type,
            'dispute_reason': self.dispute_reason,
            'dispute_amount': self.dispute_amount,
            'original_amount': self.original_amount,
            'status': self.status,
            'contact_preference': self.contact_preference,
            'supporting_documents': self.supporting_documents,
            'resolution_notes': self.resolution_notes,
            'resolution_amount': self.resolution_amount,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class DisputeComment(Base):
    """Comments and communication for billing disputes"""
    __tablename__ = 'dispute_comments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dispute_id = Column(Integer, ForeignKey('billing_disputes.id'), nullable=False)
    
    # Comment details
    comment = Column(Text, nullable=False)
    is_customer_comment = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dispute = relationship("BillingDispute", back_populates="comments")
    
    def __repr__(self):
        return f"<DisputeComment(id={self.id}, dispute_id={self.dispute_id}, is_customer={self.is_customer_comment})>"
    
    def to_dict(self):
        """Convert dispute comment to dictionary"""
        return {
            'id': self.id,
            'dispute_id': self.dispute_id,
            'comment': self.comment,
            'is_customer_comment': self.is_customer_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 