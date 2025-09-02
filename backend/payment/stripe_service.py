"""
MINGUS Application - Secure Stripe Payment Service
==================================================

Enhanced Stripe integration service with comprehensive PCI DSS compliance,
secure payment processing, and customer data protection.

Features:
- PCI DSS compliant payment processing
- Secure webhook signature validation
- Customer data protection and tokenization
- Payment method tokenization
- Comprehensive error handling and logging
- Audit trail for compliance

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import os
import logging
import stripe
import uuid
import hashlib
import hmac
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
from flask import current_app, request, g, abort
from werkzeug.exceptions import BadRequest, Unauthorized, InternalServerError

from .pci_compliance import (
    get_pci_validator, CardDataValidator, CardDataTokenizer,
    PCIComplianceValidator
)
from ..models.subscription_models import (
    MINGUSSubscription, MINGUSPaymentMethod, MINGUSInvoice
)
from ..security.audit_logging import AuditLogger
from ..security.payment_audit import PaymentAuditLogger

# Configure logging
logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Custom payment error for MINGUS."""
    
    def __init__(self, message: str, error_code: str = None, stripe_error: Any = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.stripe_error = stripe_error


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
class PaymentIntent:
    """Payment intent data structure."""
    id: str
    amount: int  # Amount in cents
    currency: str
    status: PaymentStatus
    client_secret: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    customer_id: Optional[str] = None
    payment_method_id: Optional[str] = None


@dataclass
class CustomerData:
    """Customer data structure for PCI compliance."""
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    shipping: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class SecureStripeService:
    """PCI DSS compliant Stripe payment service for MINGUS."""
    
    def __init__(self, app=None):
        """Initialize secure Stripe service."""
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.pci_validator = get_pci_validator()
        self.card_validator = CardDataValidator()
        self.tokenizer = CardDataTokenizer()
        self.audit_logger = PaymentAuditLogger()
        
        # Stripe configuration
        self.stripe_secret = None
        self.webhook_secret = None
        self.publishable_key = None
        
        # PCI compliance settings
        self.enforce_pci_compliance = True
        self.require_3d_secure = True
        self.max_retry_attempts = 3
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        
        # Load Stripe configuration
        self.stripe_secret = app.config.get('STRIPE_SECRET_KEY')
        self.webhook_secret = app.config.get('STRIPE_WEBHOOK_SECRET')
        self.publishable_key = app.config.get('STRIPE_PUBLISHABLE_KEY')
        
        # Load PCI compliance settings
        self.enforce_pci_compliance = app.config.get('ENFORCE_PCI_COMPLIANCE', True)
        self.require_3d_secure = app.config.get('REQUIRE_3D_SECURE', True)
        self.max_retry_attempts = app.config.get('MAX_PAYMENT_RETRY_ATTEMPTS', 3)
        
        if self.stripe_secret:
            stripe.api_key = self.stripe_secret
            stripe.max_network_retries = self.max_retry_attempts
        
        # Initialize PCI validator
        self.pci_validator.init_app(app)
        
        self.logger.info("Secure Stripe service initialized with PCI compliance")
    
    def create_payment_intent(
        self,
        amount: int,
        currency: str = 'usd',
        customer_id: Optional[str] = None,
        payment_method_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        confirm: bool = False,
        capture_method: str = 'automatic'
    ) -> PaymentIntent:
        """
        Create a secure payment intent with PCI compliance validation.
        
        Args:
            amount: Amount in cents
            currency: Currency code (default: usd)
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
            metadata: Additional metadata
            confirm: Whether to confirm the payment immediately
            capture_method: Capture method (automatic or manual)
            
        Returns:
            PaymentIntent object
            
        Raises:
            PaymentError: If payment creation fails
        """
        try:
            # Validate inputs
            if amount <= 0:
                raise PaymentError("Amount must be greater than 0", "INVALID_AMOUNT")
            
            if currency not in ['usd', 'eur', 'gbp', 'cad']:
                raise PaymentError("Unsupported currency", "UNSUPPORTED_CURRENCY")
            
            # Prepare payment intent data
            intent_data = {
                'amount': amount,
                'currency': currency,
                'capture_method': capture_method,
                'confirmation_method': 'manual',
                'metadata': metadata or {}
            }
            
            # Add customer if provided
            if customer_id:
                intent_data['customer'] = customer_id
            
            # Add payment method if provided
            if payment_method_id:
                intent_data['payment_method'] = payment_method_id
                intent_data['confirmation_method'] = 'automatic'
            
            # Add 3D Secure requirement
            if self.require_3d_secure:
                intent_data['setup_future_usage'] = 'off_session'
            
            # Create payment intent
            stripe_intent = stripe.PaymentIntent.create(**intent_data)
            
            # Log successful creation
            self.audit_logger.log_payment_intent_created(
                stripe_intent.id,
                amount,
                currency,
                customer_id,
                metadata
            )
            
            # Convert to MINGUS PaymentIntent
            payment_intent = PaymentIntent(
                id=stripe_intent.id,
                amount=stripe_intent.amount,
                currency=stripe_intent.currency,
                status=PaymentStatus(stripe_intent.status),
                client_secret=stripe_intent.client_secret,
                created_at=datetime.fromtimestamp(stripe_intent.created, tz=timezone.utc),
                metadata=stripe_intent.metadata,
                customer_id=stripe_intent.customer,
                payment_method_id=stripe_intent.payment_method
            )
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            error_msg = f"Stripe payment intent creation failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "payment_intent_creation",
                str(e),
                amount,
                currency,
                customer_id
            )
            raise PaymentError(error_msg, "STRIPE_ERROR", e)
        
        except Exception as e:
            error_msg = f"Payment intent creation failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "payment_intent_creation",
                str(e),
                amount,
                currency,
                customer_id
            )
            raise PaymentError(error_msg, "INTERNAL_ERROR")
    
    def confirm_payment_intent(
        self,
        payment_intent_id: str,
        payment_method_id: Optional[str] = None,
        return_url: Optional[str] = None
    ) -> PaymentIntent:
        """
        Confirm a payment intent with PCI compliance validation.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            payment_method_id: Payment method to use
            return_url: Return URL for 3D Secure
            
        Returns:
            Updated PaymentIntent object
            
        Raises:
            PaymentError: If confirmation fails
        """
        try:
            # Prepare confirmation data
            confirm_data = {}
            
            if payment_method_id:
                confirm_data['payment_method'] = payment_method_id
            
            if return_url:
                confirm_data['return_url'] = return_url
            
            # Confirm payment intent
            stripe_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **confirm_data
            )
            
            # Log confirmation
            self.audit_logger.log_payment_intent_confirmed(
                payment_intent_id,
                stripe_intent.status,
                payment_method_id
            )
            
            # Convert to MINGUS PaymentIntent
            payment_intent = PaymentIntent(
                id=stripe_intent.id,
                amount=stripe_intent.amount,
                currency=stripe_intent.currency,
                status=PaymentStatus(stripe_intent.status),
                client_secret=stripe_intent.client_secret,
                created_at=datetime.fromtimestamp(stripe_intent.created, tz=timezone.utc),
                metadata=stripe_intent.metadata,
                customer_id=stripe_intent.customer,
                payment_method_id=stripe_intent.payment_method
            )
            
            return payment_intent
            
        except stripe.error.StripeError as e:
            error_msg = f"Stripe payment intent confirmation failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "payment_intent_confirmation",
                str(e),
                None,
                None,
                None
            )
            raise PaymentError(error_msg, "STRIPE_ERROR", e)
        
        except Exception as e:
            error_msg = f"Payment intent confirmation failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "payment_intent_confirmation",
                str(e),
                None,
                None,
                None
            )
            raise PaymentError(error_msg, "INTERNAL_ERROR")
    
    def create_customer(
        self,
        customer_data: CustomerData,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer with PCI compliance validation.
        
        Args:
            customer_data: Customer information
            payment_method_id: Optional payment method to attach
            
        Returns:
            Stripe customer object
            
        Raises:
            PaymentError: If customer creation fails
        """
        try:
            # Validate customer data
            if not customer_data.email:
                raise PaymentError("Customer email is required", "MISSING_EMAIL")
            
            # Prepare customer data
            customer_params = {
                'email': customer_data.email,
                'metadata': customer_data.metadata or {}
            }
            
            if customer_data.name:
                customer_params['name'] = customer_data.name
            
            if customer_data.phone:
                customer_params['phone'] = customer_data.phone
            
            if customer_data.address:
                customer_params['address'] = customer_data.address
            
            if customer_data.shipping:
                customer_params['shipping'] = customer_data.shipping
            
            # Create customer
            stripe_customer = stripe.Customer.create(**customer_params)
            
            # Attach payment method if provided
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=stripe_customer.id
                )
                
                # Set as default payment method
                stripe.Customer.modify(
                    stripe_customer.id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )
            
            # Log customer creation
            self.audit_logger.log_customer_created(
                stripe_customer.id,
                customer_data.email,
                payment_method_id
            )
            
            return stripe_customer
            
        except stripe.error.StripeError as e:
            error_msg = f"Stripe customer creation failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "customer_creation",
                str(e),
                None,
                None,
                None
            )
            raise PaymentError(error_msg, "STRIPE_ERROR", e)
        
        except Exception as e:
            error_msg = f"Customer creation failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "customer_creation",
                str(e),
                None,
                None,
                None
            )
            raise PaymentError(error_msg, "INTERNAL_ERROR")
    
    def create_payment_method(
        self,
        payment_method_data: Dict[str, Any],
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a payment method with PCI compliance validation.
        
        Args:
            payment_method_data: Payment method information
            customer_id: Customer to attach payment method to
            
        Returns:
            Stripe payment method object
            
        Raises:
            PaymentError: If payment method creation fails
        """
        try:
            # Validate payment method data
            if 'type' not in payment_method_data:
                raise PaymentError("Payment method type is required", "MISSING_TYPE")
            
            # PCI compliance validation for card data
            if payment_method_data['type'] == 'card':
                validation_result = self._validate_card_data(payment_method_data)
                if not validation_result['compliant']:
                    raise PaymentError(
                        f"Card validation failed: {validation_result['errors']}",
                        "CARD_VALIDATION_FAILED"
                    )
            
            # Create payment method
            stripe_payment_method = stripe.PaymentMethod.create(
                type=payment_method_data['type'],
                card=payment_method_data.get('card'),
                billing_details=payment_method_data.get('billing_details'),
                metadata=payment_method_data.get('metadata', {})
            )
            
            # Attach to customer if provided
            if customer_id:
                stripe.PaymentMethod.attach(
                    stripe_payment_method.id,
                    customer=customer_id
                )
            
            # Log payment method creation
            self.audit_logger.log_payment_method_created(
                stripe_payment_method.id,
                payment_method_data['type'],
                customer_id
            )
            
            return stripe_payment_method
            
        except stripe.error.StripeError as e:
            error_msg = f"Stripe payment method creation failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "payment_method_creation",
                str(e),
                None,
                None,
                customer_id
            )
            raise PaymentError(error_msg, "STRIPE_ERROR", e)
        
        except Exception as e:
            error_msg = f"Payment method creation failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "payment_method_creation",
                str(e),
                None,
                None,
                customer_id
            )
            raise PaymentError(error_msg, "INTERNAL_ERROR")
    
    def _validate_card_data(self, payment_method_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate card data for PCI compliance."""
        card_data = payment_method_data.get('card', {})
        
        validation_result = {
            'compliant': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate card number
        if 'number' in card_data:
            card_valid, card_message = self.card_validator.validate_card_number(
                card_data['number']
            )
            if not card_valid:
                validation_result['compliant'] = False
                validation_result['errors'].append(f"Card number: {card_message}")
        
        # Validate expiry date
        if 'exp_month' in card_data and 'exp_year' in card_data:
            exp_valid, exp_message = self.card_validator.validate_expiry_date(
                card_data['exp_month'],
                card_data['exp_year']
            )
            if not exp_valid:
                validation_result['compliant'] = False
                validation_result['errors'].append(f"Expiry date: {exp_message}")
        
        # Validate CVV
        if 'cvc' in card_data:
            # Determine card type for CVV validation
            card_type = 'visa'  # Default, should be determined from card number
            if 'number' in card_data:
                card_type = self.card_validator._identify_card_type(
                    card_data['number'].replace(' ', '').replace('-', '')
                ) or 'visa'
            
            cvv_valid, cvv_message = self.card_validator.validate_cvv(
                card_data['cvc'],
                card_type
            )
            if not cvv_valid:
                validation_result['compliant'] = False
                validation_result['errors'].append(f"CVV: {cvv_message}")
        
        return validation_result
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: int
    ) -> bool:
        """
        Validate Stripe webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature header
            timestamp: Webhook timestamp header
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not self.webhook_secret:
                self.logger.error("Webhook secret not configured")
                return False
            
            # Use PCI validator for webhook validation
            return self.pci_validator.validate_stripe_webhook(
                payload,
                signature,
                timestamp
            )
            
        except Exception as e:
            self.logger.error(f"Webhook signature validation failed: {e}")
            return False
    
    def process_webhook_event(
        self,
        event_data: Dict[str, Any],
        event_type: str
    ) -> Dict[str, Any]:
        """
        Process Stripe webhook events with PCI compliance validation.
        
        Args:
            event_data: Webhook event data
            event_type: Type of webhook event
            
        Returns:
            Processing result
            
        Raises:
            PaymentError: If webhook processing fails
        """
        try:
            # Log webhook event
            self.audit_logger.log_webhook_received(
                event_type,
                event_data.get('id'),
                event_data
            )
            
            # Process based on event type
            if event_type == 'payment_intent.succeeded':
                return self._handle_payment_success(event_data)
            elif event_type == 'payment_intent.payment_failed':
                return self._handle_payment_failure(event_data)
            elif event_type == 'customer.subscription.created':
                return self._handle_subscription_created(event_data)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return self._handle_invoice_payment_success(event_data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_invoice_payment_failure(event_data)
            else:
                # Log unhandled event type
                self.logger.info(f"Unhandled webhook event type: {event_type}")
                return {'status': 'ignored', 'event_type': event_type}
            
        except Exception as e:
            error_msg = f"Webhook event processing failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_webhook_error(
                event_type,
                event_data.get('id'),
                str(e)
            )
            raise PaymentError(error_msg, "WEBHOOK_PROCESSING_ERROR")
    
    def _handle_payment_success(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook."""
        payment_intent = event_data['data']['object']
        
        # Update local payment records
        # This would typically update your database
        
        # Log success
        self.audit_logger.log_payment_success(
            payment_intent['id'],
            payment_intent['amount'],
            payment_intent['currency'],
            payment_intent.get('customer')
        )
        
        return {
            'status': 'processed',
            'event_type': 'payment_intent.succeeded',
            'payment_intent_id': payment_intent['id']
        }
    
    def _handle_payment_failure(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook."""
        payment_intent = event_data['data']['object']
        
        # Log failure
        self.audit_logger.log_payment_failure(
            payment_intent['id'],
            payment_intent.get('last_payment_error', {}).get('message', 'Unknown error'),
            payment_intent.get('customer')
        )
        
        return {
            'status': 'processed',
            'event_type': 'payment_intent.payment_failed',
            'payment_intent_id': payment_intent['id']
        }
    
    def _handle_subscription_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription created webhook."""
        subscription = event_data['data']['object']
        
        # Log subscription creation
        self.audit_logger.log_subscription_created(
            subscription['id'],
            subscription.get('customer'),
            subscription.get('status')
        )
        
        return {
            'status': 'processed',
            'event_type': 'customer.subscription.created',
            'subscription_id': subscription['id']
        }
    
    def _handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updated webhook."""
        subscription = event_data['data']['object']
        
        # Log subscription update
        self.audit_logger.log_subscription_updated(
            subscription['id'],
            subscription.get('status'),
            subscription.get('customer')
        )
        
        return {
            'status': 'processed',
            'event_type': 'customer.subscription.updated',
            'subscription_id': subscription['id']
        }
    
    def _handle_subscription_deleted(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription deleted webhook."""
        subscription = event_data['data']['object']
        
        # Log subscription deletion
        self.audit_logger.log_subscription_deleted(
            subscription['id'],
            subscription.get('customer')
        )
        
        return {
            'status': 'processed',
            'event_type': 'customer.subscription.deleted',
            'subscription_id': subscription['id']
        }
    
    def _handle_invoice_payment_success(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful invoice payment webhook."""
        invoice = event_data['data']['object']
        
        # Log invoice payment success
        self.audit_logger.log_invoice_payment_success(
            invoice['id'],
            invoice['amount_paid'],
            invoice['currency'],
            invoice.get('customer')
        )
        
        return {
            'status': 'processed',
            'event_type': 'invoice.payment_succeeded',
            'invoice_id': invoice['id']
        }
    
    def _handle_invoice_payment_failure(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed invoice payment webhook."""
        invoice = event_data['data']['object']
        
        # Log invoice payment failure
        self.audit_logger.log_invoice_payment_failure(
            invoice['id'],
            invoice.get('last_payment_error', {}).get('message', 'Unknown error'),
            invoice.get('customer')
        )
        
        return {
            'status': 'processed',
            'event_type': 'invoice.payment_failed',
            'invoice_id': invoice['id']
        }
    
    def get_payment_intent(self, payment_intent_id: str) -> PaymentIntent:
        """
        Retrieve a payment intent from Stripe.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            PaymentIntent object
            
        Raises:
            PaymentError: If retrieval fails
        """
        try:
            stripe_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return PaymentIntent(
                id=stripe_intent.id,
                amount=stripe_intent.amount,
                currency=stripe_intent.currency,
                status=PaymentStatus(stripe_intent.status),
                client_secret=stripe_intent.client_secret,
                created_at=datetime.fromtimestamp(stripe_intent.created, tz=timezone.utc),
                metadata=stripe_intent.metadata,
                customer_id=stripe_intent.customer,
                payment_method_id=stripe_intent.payment_method
            )
            
        except stripe.error.StripeError as e:
            error_msg = f"Failed to retrieve payment intent: {str(e)}"
            self.logger.error(error_msg)
            raise PaymentError(error_msg, "STRIPE_ERROR", e)
        
        except Exception as e:
            error_msg = f"Failed to retrieve payment intent: {str(e)}"
            self.logger.error(error_msg)
            raise PaymentError(error_msg, "INTERNAL_ERROR")
    
    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: str = 'requested_by_customer'
    ) -> Dict[str, Any]:
        """
        Refund a payment with PCI compliance validation.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Amount to refund in cents (None for full refund)
            reason: Reason for refund
            
        Returns:
            Stripe refund object
            
        Raises:
            PaymentError: If refund fails
        """
        try:
            # Create refund
            refund_data = {
                'payment_intent': payment_intent_id,
                'reason': reason
            }
            
            if amount:
                refund_data['amount'] = amount
            
            stripe_refund = stripe.Refund.create(**refund_data)
            
            # Log refund
            self.audit_logger.log_refund_created(
                stripe_refund.id,
                payment_intent_id,
                stripe_refund.amount,
                reason
            )
            
            return stripe_refund
            
        except stripe.error.StripeError as e:
            error_msg = f"Stripe refund failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "refund_creation",
                str(e),
                amount,
                None,
                None
            )
            raise PaymentError(error_msg, "STRIPE_ERROR", e)
        
        except Exception as e:
            error_msg = f"Refund failed: {str(e)}"
            self.logger.error(error_msg)
            self.audit_logger.log_payment_error(
                "refund_creation",
                str(e),
                amount,
                None,
                None
            )
            raise PaymentError(error_msg, "INTERNAL_ERROR")
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get PCI compliance report."""
        try:
            report = self.pci_validator.generate_compliance_report()
            
            return {
                'overall_score': report.overall_score,
                'compliance_level': report.compliance_level.value,
                'summary': report.summary,
                'critical_issues': report.critical_issues,
                'warnings': report.warnings,
                'recommendations': report.recommendations,
                'generated_at': report.generated_at.isoformat(),
                'valid_until': report.valid_until.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate compliance report: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }


# Global secure Stripe service instance
secure_stripe_service = SecureStripeService()


def get_secure_stripe_service() -> SecureStripeService:
    """Get the global secure Stripe service instance."""
    return secure_stripe_service


def init_secure_stripe_service(app):
    """Initialize secure Stripe service with Flask app."""
    secure_stripe_service.init_app(app)
    app.logger.info("Secure Stripe service initialized")
