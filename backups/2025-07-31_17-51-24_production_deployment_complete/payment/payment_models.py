"""
MINGUS Application - Payment Models
==================================

Payment-related models, enums, and error classes for the MINGUS payment system.

Author: MINGUS Development Team
Date: January 2025
"""

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


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


class SubscriptionStatus(Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class BillingCycle(Enum):
    """Billing cycle enumeration."""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKLY = "weekly"
    DAILY = "daily"


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


@dataclass
class PaymentError:
    """Payment error information."""
    code: str
    message: str
    type: str
    decline_code: Optional[str] = None
    param: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            'code': self.code,
            'message': self.message,
            'type': self.type,
            'decline_code': self.decline_code,
            'param': self.param,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


@dataclass
class PaymentIntent:
    """Payment intent information."""
    id: str
    amount: int  # Amount in cents
    currency: str
    status: PaymentStatus
    client_secret: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    receipt_email: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payment intent to dictionary."""
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value,
            'client_secret': self.client_secret,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
            'description': self.description,
            'receipt_email': self.receipt_email
        }


@dataclass
class Customer:
    """Customer information."""
    id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert customer to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata
        }


@dataclass
class Subscription:
    """Subscription information."""
    id: str
    customer_id: str
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'status': self.status.value,
            'current_period_start': self.current_period_start.isoformat(),
            'current_period_end': self.current_period_end.isoformat(),
            'cancel_at_period_end': self.cancel_at_period_end,
            'created_at': self.created_at.isoformat(),
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'metadata': self.metadata
        }


@dataclass
class Invoice:
    """Invoice information."""
    id: str
    customer_id: str
    subscription_id: Optional[str]
    amount_due: int  # Amount in cents
    amount_paid: int  # Amount in cents
    currency: str
    status: str
    billing_reason: str
    created_at: datetime
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'subscription_id': self.subscription_id,
            'amount_due': self.amount_due,
            'amount_paid': self.amount_paid,
            'currency': self.currency,
            'status': self.status,
            'billing_reason': self.billing_reason,
            'created_at': self.created_at.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'description': self.description,
            'metadata': self.metadata
        }


@dataclass
class PaymentMethod:
    """Payment method information."""
    id: str
    customer_id: str
    type: PaymentMethodType
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    card_exp_month: Optional[int] = None
    card_exp_year: Optional[int] = None
    billing_details: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payment method to dictionary."""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'type': self.type.value,
            'card_brand': self.card_brand,
            'card_last4': self.card_last4,
            'card_exp_month': self.card_exp_month,
            'card_exp_year': self.card_exp_year,
            'billing_details': self.billing_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata
        } 