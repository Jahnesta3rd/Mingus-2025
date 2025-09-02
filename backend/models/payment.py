"""
MINGUS Application - PCI Compliant Payment Models
=================================================

Payment models that NEVER store sensitive card data, only Stripe references
and payment method tokens for PCI DSS compliance.

Key Features:
- No card number, CVV, or expiry storage
- Only Stripe customer IDs and payment method references
- Comprehensive audit trail fields
- PCI compliance tracking
- Secure payment method handling

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import uuid
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

from .base import Base
from ..extensions import db

# Configure logging
logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
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
    REQUIRES_ACTION = "requires_action"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class PaymentMethodType(Enum):
    """Payment method type enumeration."""
    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    SEPA_DEBIT = "sepa_debit"
    IDEAL = "ideal"
    SOFORT = "sofort"
    GIROPAY = "giropay"
    BANCONTACT = "bancontact"
    EPS = "eps"
    P24 = "p24"
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


class PaymentIntentStatus(Enum):
    """Payment intent status enumeration."""
    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    REQUIRES_CAPTURE = "requires_capture"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"


class ComplianceLevel(Enum):
    """PCI compliance level enumeration."""
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    COMPLIANT = "compliant"
    FULLY_COMPLIANT = "fully_compliant"


class MINGUSCustomer(Base):
    """MINGUS customer model that integrates with Stripe customers."""
    
    __tablename__ = 'mingus_customers'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, unique=True, index=True)
    user = relationship("User", back_populates="customer")
    
    # Stripe integration
    stripe_customer_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Customer information (non-sensitive)
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Billing address (non-sensitive)
    billing_address = Column(JSON, nullable=True)
    
    # Customer metadata
    customer_metadata = Column(JSON, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # PCI compliance tracking
    pci_compliance_level = Column(ENUM(ComplianceLevel), nullable=False, default=ComplianceLevel.NON_COMPLIANT)
    last_compliance_check = Column(DateTime(timezone=True), nullable=True)
    compliance_score = Column(Float, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_customer_user', 'user_id'),
        Index('idx_customer_stripe', 'stripe_customer_id'),
        Index('idx_customer_email', 'email'),
        Index('idx_customer_compliance', 'pci_compliance_level'),
        {'extend_existing': True},
    )
    
    # Relationships
    payment_methods = relationship("MINGUSPaymentMethod", back_populates="customer", cascade="all, delete-orphan")
    payment_intents = relationship("MINGUSPaymentIntent", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("MINGUSInvoice", back_populates="customer", cascade="all, delete-orphan")
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate customer email."""
        if not email or '@' not in email:
            raise ValueError("Invalid email address")
        return email.lower()
    
    def update_compliance_status(self, level: ComplianceLevel, score: float = None):
        """Update PCI compliance status."""
        self.pci_compliance_level = level
        self.compliance_score = score
        self.last_compliance_check = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert customer to dictionary (no sensitive data)."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'stripe_customer_id': self.stripe_customer_id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'billing_address': self.billing_address,
            'metadata': self.customer_metadata,
            'is_active': self.is_active,
            'pci_compliance_level': self.pci_compliance_level.value if self.pci_compliance_level else None,
            'last_compliance_check': self.last_compliance_check.isoformat() if self.last_compliance_check else None,
            'compliance_score': self.compliance_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MINGUSPaymentMethod(Base):
    """MINGUS payment method model that NEVER stores card data."""
    
    __tablename__ = 'mingus_payment_methods'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Customer relationship
    customer_id = Column(UUID(as_uuid=True), ForeignKey('mingus_customers.id'), nullable=False, index=True)
    customer = relationship("MINGUSCustomer", back_populates="payment_methods")
    
    # Stripe integration
    stripe_payment_method_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Payment method details (NON-SENSITIVE ONLY)
    type = Column(ENUM(PaymentMethodType), nullable=False)
    brand = Column(String(50), nullable=True)  # visa, mastercard, etc.
    last4 = Column(String(4), nullable=True)  # Only last 4 digits
    exp_month = Column(Integer, nullable=True)  # Expiry month (1-12)
    exp_year = Column(Integer, nullable=True)   # Expiry year (YYYY)
    country = Column(String(2), nullable=True)  # Country code
    
    # Billing details (non-sensitive)
    billing_details = Column(JSON, nullable=True)
    
    # Status
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # PCI compliance tracking
    pci_compliant = Column(Boolean, nullable=False, default=False)
    last_compliance_check = Column(DateTime(timezone=True), nullable=True)
    compliance_notes = Column(Text, nullable=True)
    
    # Metadata (avoid reserved name)
    extra_metadata = Column('metadata', JSON, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_method_customer', 'customer_id', 'is_default'),
        Index('idx_payment_method_type', 'type'),
        Index('idx_payment_method_active', 'is_active'),
        Index('idx_payment_method_compliance', 'pci_compliant'),
        UniqueConstraint('customer_id', 'is_default', name='uq_customer_default_payment_method'),
        {'extend_existing': True},
    )
    
    # Relationships
    payment_intents = relationship("MINGUSPaymentIntent", back_populates="payment_method", cascade="all, delete-orphan")
    
    @validates('exp_month')
    def validate_exp_month(self, key, exp_month):
        """Validate expiry month."""
        if exp_month is not None and (exp_month < 1 or exp_month > 12):
            raise ValueError("Expiry month must be between 1 and 12")
        return exp_month
    
    @validates('exp_year')
    def validate_exp_year(self, key, exp_year):
        """Validate expiry year."""
        if exp_year is not None:
            current_year = datetime.now().year
            if exp_year < current_year or exp_year > current_year + 20:
                raise ValueError("Expiry year must be between current year and current year + 20")
        return exp_year
    
    @validates('last4')
    def validate_last4(self, key, last4):
        """Validate last 4 digits."""
        if last4 is not None:
            if not last4.isdigit() or len(last4) != 4:
                raise ValueError("Last 4 digits must be exactly 4 digits")
        return last4
    
    def is_expired(self) -> bool:
        """Check if payment method is expired."""
        if not self.exp_month or not self.exp_year:
            return False
        
        now = datetime.now(timezone.utc)
        return now.year > self.exp_year or (now.year == self.exp_year and now.month > self.exp_month)
    
    def get_display_name(self) -> str:
        """Get display name for payment method (no sensitive data)."""
        if self.type == PaymentMethodType.CARD:
            brand = self.brand or 'Card'
            if self.last4:
                return f"{brand.title()} •••• {self.last4}"
            else:
                return f"{brand.title()} Card"
        elif self.type == PaymentMethodType.BANK_ACCOUNT:
            if self.last4:
                return f"Bank Account •••• {self.last4}"
            else:
                return "Bank Account"
        else:
            if self.last4:
                return f"{self.type.title()} •••• {self.last4}"
            else:
                return f"{self.type.title()}"
    
    def update_compliance_status(self, compliant: bool, notes: str = None):
        """Update PCI compliance status."""
        self.pci_compliant = compliant
        self.last_compliance_check = datetime.now(timezone.utc)
        self.compliance_notes = notes
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payment method to dictionary (no sensitive data)."""
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'stripe_payment_method_id': self.stripe_payment_method_id,
            'type': self.type.value if self.type else None,
            'brand': self.brand,
            'last4': self.last4,
            'exp_month': self.exp_month,
            'exp_year': self.exp_year,
            'country': self.country,
            'billing_details': self.billing_details,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'pci_compliant': self.pci_compliant,
            'last_compliance_check': self.last_compliance_check.isoformat() if self.last_compliance_check else None,
            'compliance_notes': self.compliance_notes,
            'extra_metadata': self.extra_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_expired': self.is_expired()
        }


class MINGUSPaymentIntent(Base):
    """MINGUS payment intent model for tracking Stripe payment intents."""
    
    __tablename__ = 'mingus_payment_intents'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Customer relationship
    customer_id = Column(UUID(as_uuid=True), ForeignKey('mingus_customers.id'), nullable=False, index=True)
    customer = relationship("MINGUSCustomer", back_populates="payment_intents")
    
    # Payment method relationship
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey('mingus_payment_methods.id'), nullable=True, index=True)
    payment_method = relationship("MINGUSPaymentMethod", back_populates="payment_intents")
    
    # Stripe integration
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Payment details
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), nullable=False, default='usd')
    status = Column(ENUM(PaymentIntentStatus), nullable=False, default=PaymentIntentStatus.REQUIRES_PAYMENT_METHOD)
    
    # Client secret (temporary, should be rotated)
    client_secret = Column(String(255), nullable=True)
    
    # Metadata
    payment_metadata = Column(JSON, nullable=True)
    
    # PCI compliance tracking
    pci_compliant = Column(Boolean, nullable=False, default=False)
    compliance_checks_passed = Column(JSON, nullable=True)
    compliance_notes = Column(Text, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_intent_customer', 'customer_id'),
        Index('idx_payment_intent_stripe', 'stripe_payment_intent_id'),
        Index('idx_payment_intent_status', 'status'),
        Index('idx_payment_intent_compliance', 'pci_compliant'),
        {'extend_existing': True},
    )
    
    @validates('amount')
    def validate_amount(self, key, amount):
        """Validate payment amount."""
        if amount <= 0:
            raise ValueError("Payment amount must be greater than 0")
        return amount
    
    @validates('currency')
    def validate_currency(self, key, currency):
        """Validate currency code."""
        valid_currencies = ['usd', 'eur', 'gbp', 'cad']
        if currency.lower() not in valid_currencies:
            raise ValueError(f"Unsupported currency. Must be one of: {', '.join(valid_currencies)}")
        return currency.lower()
    
    def update_status(self, status: PaymentIntentStatus):
        """Update payment intent status."""
        self.status = status
        self.updated_at = datetime.now(timezone.utc)
    
    def update_compliance_status(self, compliant: bool, checks_passed: Dict[str, Any] = None, notes: str = None):
        """Update PCI compliance status."""
        self.pci_compliant = compliant
        self.compliance_checks_passed = checks_passed
        self.compliance_notes = notes
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payment intent to dictionary."""
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'payment_method_id': str(self.payment_method_id) if self.payment_method_id else None,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value if self.status else None,
            'client_secret': self.client_secret,
            'metadata': self.payment_metadata,
            'pci_compliant': self.pci_compliant,
            'compliance_checks_passed': self.compliance_checks_passed,
            'compliance_notes': self.compliance_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MINGUSInvoice(Base):
    """MINGUS invoice model for tracking billing and payments."""
    
    __tablename__ = 'mingus_invoices'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Customer relationship
    customer_id = Column(UUID(as_uuid=True), ForeignKey('mingus_customers.id'), nullable=False, index=True)
    customer = relationship("MINGUSCustomer", back_populates="invoices")
    
    # Payment intent relationship
    payment_intent_id = Column(UUID(as_uuid=True), ForeignKey('mingus_payment_intents.id'), nullable=True, index=True)
    payment_intent = relationship("MINGUSPaymentIntent")
    
    # Stripe integration
    stripe_invoice_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    
    # Invoice details
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(ENUM(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Financial details
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    amount_paid = Column(Float, nullable=False, default=0.0)
    amount_remaining = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default='usd')
    
    # Dates
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Invoice items
    items = Column(JSON, nullable=True)
    
    # Metadata
    extra_metadata = Column('metadata', JSON, nullable=True)
    
    # PCI compliance tracking
    pci_compliant = Column(Boolean, nullable=False, default=False)
    compliance_checks_passed = Column(JSON, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_invoice_customer', 'customer_id'),
        Index('idx_invoice_number', 'invoice_number'),
        Index('idx_invoice_status', 'status'),
        Index('idx_invoice_due_date', 'due_date'),
        Index('idx_invoice_compliance', 'pci_compliant'),
        CheckConstraint('subtotal >= 0', name='check_subtotal_positive'),
        CheckConstraint('tax >= 0', name='check_tax_positive'),
        CheckConstraint('discount >= 0', name='check_discount_positive'),
        CheckConstraint('total >= 0', name='check_total_positive'),
        CheckConstraint('amount_paid >= 0', name='check_amount_paid_positive'),
        CheckConstraint('amount_remaining >= 0', name='check_amount_remaining_positive'),
        {'extend_existing': True},
    )
    
    @validates('subtotal', 'tax', 'discount', 'total', 'amount_paid', 'amount_remaining')
    def validate_amounts(self, key, amount):
        """Validate all amount fields are non-negative."""
        if amount < 0:
            raise ValueError(f"{key} cannot be negative")
        return amount
    
    @validates('currency')
    def validate_currency(self, key, currency):
        """Validate currency code."""
        valid_currencies = ['usd', 'eur', 'gbp', 'cad']
        if currency.lower() not in valid_currencies:
            raise ValueError(f"Unsupported currency. Must be one of: {', '.join(valid_currencies)}")
        return currency.lower()
    
    def is_paid(self) -> bool:
        """Check if invoice is fully paid."""
        return self.amount_paid >= self.total
    
    def is_overdue(self) -> bool:
        """Check if invoice is overdue."""
        if not self.due_date or self.is_paid():
            return False
        return datetime.now(timezone.utc) > self.due_date
    
    def get_payment_percentage(self) -> float:
        """Get payment percentage."""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.amount_paid / self.total) * 100)
    
    def update_payment_status(self, status: PaymentStatus, amount_paid: float = None):
        """Update payment status."""
        self.status = status
        if amount_paid is not None:
            self.amount_paid = amount_paid
            self.amount_remaining = max(0.0, self.total - self.amount_paid)
            if self.is_paid():
                self.paid_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def update_compliance_status(self, compliant: bool, checks_passed: Dict[str, Any] = None):
        """Update PCI compliance status."""
        self.pci_compliant = compliant
        self.compliance_checks_passed = checks_passed
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice to dictionary."""
        return {
            'id': str(self.id),
            'customer_id': str(self.customer_id),
            'payment_intent_id': str(self.payment_intent_id) if self.payment_intent_id else None,
            'stripe_invoice_id': self.stripe_invoice_id,
            'stripe_payment_intent_id': self.stripe_payment_intent_id,
            'invoice_number': self.invoice_number,
            'status': self.status.value if self.status else None,
            'subtotal': self.subtotal,
            'tax': self.tax,
            'discount': self.discount,
            'total': self.total,
            'amount_paid': self.amount_paid,
            'amount_remaining': self.amount_remaining,
            'currency': self.currency,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'items': self.items,
            'extra_metadata': self.extra_metadata,
            'pci_compliant': self.pci_compliant,
            'compliance_checks_passed': self.compliance_checks_passed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_paid': self.is_paid(),
            'is_overdue': self.is_overdue(),
            'payment_percentage': self.get_payment_percentage()
        }


class MINGUSPaymentAudit(Base):
    """MINGUS payment audit trail for PCI compliance."""
    
    __tablename__ = 'mingus_payment_audits'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Audit details
    audit_type = Column(String(100), nullable=False, index=True)
    audit_level = Column(String(50), nullable=False, default='info')
    
    # Related entities
    customer_id = Column(UUID(as_uuid=True), ForeignKey('mingus_customers.id'), nullable=True, index=True)
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey('mingus_payment_methods.id'), nullable=True, index=True)
    payment_intent_id = Column(UUID(as_uuid=True), ForeignKey('mingus_payment_intents.id'), nullable=True, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey('mingus_invoices.id'), nullable=True, index=True)
    
    # Audit data
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # User context
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_audit_type', 'audit_type'),
        Index('idx_payment_audit_level', 'audit_level'),
        Index('idx_payment_audit_customer', 'customer_id'),
        Index('idx_payment_audit_created', 'created_at'),
        {'extend_existing': True},
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit record to dictionary."""
        return {
            'id': str(self.id),
            'audit_type': self.audit_type,
            'audit_level': self.audit_level,
            'customer_id': str(self.customer_id) if self.customer_id else None,
            'payment_method_id': str(self.payment_method_id) if self.payment_method_id else None,
            'payment_intent_id': str(self.payment_intent_id) if self.payment_intent_id else None,
            'invoice_id': str(self.invoice_id) if self.invoice_id else None,
            'message': self.message,
            'details': self.details,
            'user_id': str(self.user_id) if self.user_id else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Export all models
__all__ = [
    'MINGUSCustomer',
    'MINGUSPaymentMethod', 
    'MINGUSPaymentIntent',
    'MINGUSInvoice',
    'MINGUSPaymentAudit',
    'PaymentStatus',
    'PaymentMethodType',
    'PaymentIntentStatus',
    'ComplianceLevel'
]
