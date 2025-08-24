"""
MINGUS Application - Stripe Integration
======================================

Comprehensive Stripe integration for the MINGUS personal finance application.

Features:
- Three subscription tiers (Budget, Mid-Tier, Professional)
- Payment processing and subscription management
- Webhook handling for real-time updates
- Customer management and billing
- Security and compliance features

Author: MINGUS Development Team
Date: January 2025
"""

import os
import logging
import stripe
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from .payment_models import (
    PaymentStatus, SubscriptionStatus, PaymentError, PaymentIntent,
    Customer, Subscription, Invoice, PaymentMethod, PaymentMethodType
)
from ..config.stripe import get_stripe_config, get_stripe_error_handler, get_stripe_webhook_config
from ..security.stripe_security import get_stripe_security_manager

# Configure logging
logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """MINGUS subscription tiers."""
    BUDGET = "budget"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"


@dataclass
class TierFeatures:
    """Subscription tier features and limits."""
    name: str
    price_monthly: int  # Price in cents
    price_yearly: int   # Price in cents (with discount)
    features: Dict[str, Any]
    limits: Dict[str, Any]
    description: str
    stripe_price_id_monthly: Optional[str] = None
    stripe_price_id_yearly: Optional[str] = None


class StripeService:
    """Comprehensive Stripe integration service for MINGUS."""
    
    # MINGUS Subscription Tiers Configuration
    SUBSCRIPTION_TIERS = {
        SubscriptionTier.BUDGET: TierFeatures(
            name="Budget Tier",
            price_monthly=1500,  # $15.00
            price_yearly=14400,  # $144.00 (20% discount)
            description="Perfect for individuals getting started with personal finance management",
            features={
                "basic_analytics": True,
                "goal_setting": True,
                "email_support": True,
                "basic_reports": True,
                "mobile_app": True,
                "data_export": True,
                "basic_notifications": True
            },
            limits={
                "analytics_reports_per_month": 5,
                "goals_per_account": 3,
                "data_export_per_month": 2,
                "support_requests_per_month": 3,
                "transaction_history_months": 12
            }
        ),
        SubscriptionTier.MID_TIER: TierFeatures(
            name="Mid-Tier",
            price_monthly=3500,  # $35.00
            price_yearly=33600,  # $336.00 (20% discount)
            description="Advanced features for serious personal finance management",
            features={
                "basic_analytics": True,
                "goal_setting": True,
                "email_support": True,
                "basic_reports": True,
                "mobile_app": True,
                "data_export": True,
                "basic_notifications": True,
                "advanced_ai_insights": True,
                "career_risk_management": True,
                "priority_support": True,
                "advanced_reports": True,
                "custom_categories": True,
                "investment_tracking": True,
                "debt_optimization": True,
                "tax_planning": True
            },
            limits={
                "analytics_reports_per_month": 20,
                "goals_per_account": 10,
                "data_export_per_month": 10,
                "support_requests_per_month": 10,
                "transaction_history_months": 36,
                "ai_insights_per_month": 50,
                "investment_accounts": 5,
                "custom_categories": 20
            }
        ),
        SubscriptionTier.PROFESSIONAL: TierFeatures(
            name="Professional Tier",
            price_monthly=7500,  # $75.00
            price_yearly=72000,  # $720.00 (20% discount)
            description="Unlimited access with dedicated support for professionals",
            features={
                "basic_analytics": True,
                "goal_setting": True,
                "email_support": True,
                "basic_reports": True,
                "mobile_app": True,
                "data_export": True,
                "basic_notifications": True,
                "advanced_ai_insights": True,
                "career_risk_management": True,
                "priority_support": True,
                "advanced_reports": True,
                "custom_categories": True,
                "investment_tracking": True,
                "debt_optimization": True,
                "tax_planning": True,
                "unlimited_access": True,
                "dedicated_account_manager": True,
                "team_management": True,
                "white_label_reports": True,
                "api_access": True,
                "custom_integrations": True,
                "priority_feature_requests": True,
                "phone_support": True,
                "onboarding_call": True
            },
            limits={
                "analytics_reports_per_month": -1,  # Unlimited
                "goals_per_account": -1,  # Unlimited
                "data_export_per_month": -1,  # Unlimited
                "support_requests_per_month": -1,  # Unlimited
                "transaction_history_months": -1,  # Unlimited
                "ai_insights_per_month": -1,  # Unlimited
                "investment_accounts": -1,  # Unlimited
                "custom_categories": -1,  # Unlimited
                "team_members": 10,
                "api_requests_per_month": 10000
            }
        )
    }
    
    def __init__(self, api_key: Optional[str] = None, webhook_secret: Optional[str] = None):
        """
        Initialize Stripe service.
        
        Args:
            api_key: Stripe API key (defaults to environment variable)
            webhook_secret: Stripe webhook secret (defaults to environment variable)
        """
        # Get configuration
        self.config = get_stripe_config()
        self.error_handler = get_stripe_error_handler()
        self.webhook_config = get_stripe_webhook_config()
        self.security_manager = get_stripe_security_manager()
        
        # Use provided keys or fall back to configuration
        self.api_key = api_key or self.config.api_key
        self.webhook_secret = webhook_secret or self.config.webhook_secret
        self.publishable_key = self.config.publishable_key
        
        if not self.api_key:
            missing_config = self.config.missing_configuration
            raise ValueError(f"Stripe API key is required. Missing: {missing_config}")
        
        # Initialize Stripe
        stripe.api_key = self.api_key
        
        # Set up logging based on configuration
        if self.config.enable_debug:
            stripe.log = self.config.log_level.lower()
        else:
            stripe.log = 'warning'
        
        # Log initialization
        self.error_handler.logger.info(
            f"Stripe service initialized for {self.config.environment} environment"
        )
        
        # Validate configuration
        validation = self.config.validate_configuration()
        if not validation['is_configured']:
            self.error_handler.logger.warning(
                f"Stripe configuration incomplete: {validation['missing_configuration']}"
            )
    
    def get_publishable_key(self) -> str:
        """Get Stripe publishable key for client-side integration."""
        if not self.publishable_key:
            raise ValueError("Stripe publishable key not configured")
        return self.publishable_key
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get Stripe environment information."""
        return self.config.to_dict()
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate Stripe configuration."""
        return self.config.validate_configuration()
    
    def create_customer(self, email: str, name: Optional[str] = None, 
                       phone: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                       user_id: str = '', source_ip: str = '', user_agent: str = '', 
                       request_id: str = '') -> Customer:
        """
        Create a new Stripe customer with enhanced security.
        
        Args:
            email: Customer email address
            name: Customer name (optional)
            phone: Customer phone number (optional)
            metadata: Additional metadata (optional)
            user_id: User identifier for security tracking
            source_ip: Source IP address for security validation
            user_agent: User agent string for logging
            request_id: Request identifier for tracking
            
        Returns:
            Customer object
            
        Raises:
            stripe.error.StripeError: If customer creation fails
        """
        try:
            # Security validation
            if user_id and source_ip:
                success, message, security_info = self.security_manager.process_api_request(
                    'customer', user_id, {'email': email, 'name': name, 'phone': phone},
                    source_ip, user_agent, request_id
                )
                if not success:
                    raise stripe.error.StripeError(f"Security validation failed: {message}")
            
            customer_data = {
                'email': email,
                'metadata': metadata or {}
            }
            
            if name:
                customer_data['name'] = name
            if phone:
                customer_data['phone'] = phone
            
            stripe_customer = stripe.Customer.create(**customer_data)
            
            customer = Customer(
                id=stripe_customer.id,
                email=stripe_customer.email,
                name=stripe_customer.name,
                phone=stripe_customer.phone,
                address=stripe_customer.address.to_dict() if stripe_customer.address else None,
                created_at=datetime.fromtimestamp(stripe_customer.created, tz=timezone.utc),
                metadata=stripe_customer.metadata
            )
            
            self.error_handler.logger.info(f"Created Stripe customer: {customer.id}")
            return customer
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'create_customer',
                'email': email,
                'name': name
            })
            raise
    
    def get_customer(self, customer_id: str) -> Customer:
        """
        Retrieve a Stripe customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            Customer object
            
        Raises:
            stripe.error.StripeError: If customer retrieval fails
        """
        try:
            stripe_customer = stripe.Customer.retrieve(customer_id)
            
            customer = Customer(
                id=stripe_customer.id,
                email=stripe_customer.email,
                name=stripe_customer.name,
                phone=stripe_customer.phone,
                address=stripe_customer.address.to_dict() if stripe_customer.address else None,
                created_at=datetime.fromtimestamp(stripe_customer.created, tz=timezone.utc),
                metadata=stripe_customer.metadata
            )
            
            return customer
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'get_customer',
                'customer_id': customer_id
            })
            raise
    
    def update_customer(self, customer_id: str, **kwargs) -> Customer:
        """
        Update a Stripe customer.
        
        Args:
            customer_id: Stripe customer ID
            **kwargs: Fields to update
            
        Returns:
            Updated Customer object
            
        Raises:
            stripe.error.StripeError: If customer update fails
        """
        try:
            stripe_customer = stripe.Customer.modify(customer_id, **kwargs)
            
            customer = Customer(
                id=stripe_customer.id,
                email=stripe_customer.email,
                name=stripe_customer.name,
                phone=stripe_customer.phone,
                address=stripe_customer.address.to_dict() if stripe_customer.address else None,
                created_at=datetime.fromtimestamp(stripe_customer.created, tz=timezone.utc),
                metadata=stripe_customer.metadata
            )
            
            self.error_handler.logger.info(f"Updated Stripe customer: {customer_id}")
            return customer
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'update_customer',
                'customer_id': customer_id,
                'update_fields': list(kwargs.keys())
            })
            raise
    
    def create_payment_intent(self, amount: int, currency: str = 'usd', 
                            customer_id: Optional[str] = None,
                            description: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> PaymentIntent:
        """
        Create a payment intent for one-time payments.
        
        Args:
            amount: Amount in cents
            currency: Currency code (default: 'usd')
            customer_id: Stripe customer ID
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            PaymentIntent object
            
        Raises:
            stripe.error.StripeError: If payment intent creation fails
        """
        try:
            intent_data = {
                'amount': amount,
                'currency': currency,
                'metadata': metadata or {}
            }
            
            if customer_id:
                intent_data['customer'] = customer_id
            if description:
                intent_data['description'] = description
            
            stripe_intent = stripe.PaymentIntent.create(**intent_data)
            
            payment_intent = PaymentIntent(
                id=stripe_intent.id,
                amount=stripe_intent.amount,
                currency=stripe_intent.currency,
                status=PaymentStatus(stripe_intent.status),
                client_secret=stripe_intent.client_secret,
                created_at=datetime.fromtimestamp(stripe_intent.created, tz=timezone.utc),
                metadata=stripe_intent.metadata,
                description=stripe_intent.description,
                receipt_email=stripe_intent.receipt_email
            )
            
            self.error_handler.logger.info(f"Created payment intent: {payment_intent.id}")
            return payment_intent
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'create_payment_intent',
                'amount': amount,
                'currency': currency,
                'customer_id': customer_id
            })
            raise
    
    def create_subscription(self, customer_id: str, tier: SubscriptionTier, 
                          billing_cycle: str = 'monthly',
                          trial_days: Optional[int] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> Subscription:
        """
        Create a subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID
            tier: Subscription tier
            billing_cycle: 'monthly' or 'yearly'
            trial_days: Number of trial days
            metadata: Additional metadata
            
        Returns:
            Subscription object
            
        Raises:
            stripe.error.StripeError: If subscription creation fails
        """
        try:
            tier_config = self.SUBSCRIPTION_TIERS[tier]
            
            # Get price ID from configuration
            price_id = self.config.get_price_id(tier.value, billing_cycle)
            
            if not price_id:
                raise ValueError(f"Price ID not configured for {tier.value} {billing_cycle} plan")
            
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'metadata': metadata or {}
            }
            
            if trial_days:
                subscription_data['trial_period_days'] = trial_days
            
            stripe_subscription = stripe.Subscription.create(**subscription_data)
            
            subscription = Subscription(
                id=stripe_subscription.id,
                customer_id=stripe_subscription.customer,
                status=SubscriptionStatus(stripe_subscription.status),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc),
                cancel_at_period_end=stripe_subscription.cancel_at_period_end,
                created_at=datetime.fromtimestamp(stripe_subscription.created, tz=timezone.utc),
                trial_start=datetime.fromtimestamp(stripe_subscription.trial_start, tz=timezone.utc) if stripe_subscription.trial_start else None,
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end, tz=timezone.utc) if stripe_subscription.trial_end else None,
                canceled_at=datetime.fromtimestamp(stripe_subscription.canceled_at, tz=timezone.utc) if stripe_subscription.canceled_at else None,
                metadata=stripe_subscription.metadata
            )
            
            self.error_handler.logger.info(f"Created subscription: {subscription.id} for customer: {customer_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'create_subscription',
                'customer_id': customer_id,
                'tier': tier.value,
                'billing_cycle': billing_cycle,
                'trial_days': trial_days
            })
            raise
    
    def get_subscription(self, subscription_id: str) -> Subscription:
        """
        Retrieve a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            
        Returns:
            Subscription object
            
        Raises:
            stripe.error.StripeError: If subscription retrieval fails
        """
        try:
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            
            subscription = Subscription(
                id=stripe_subscription.id,
                customer_id=stripe_subscription.customer,
                status=SubscriptionStatus(stripe_subscription.status),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc),
                cancel_at_period_end=stripe_subscription.cancel_at_period_end,
                created_at=datetime.fromtimestamp(stripe_subscription.created, tz=timezone.utc),
                trial_start=datetime.fromtimestamp(stripe_subscription.trial_start, tz=timezone.utc) if stripe_subscription.trial_start else None,
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end, tz=timezone.utc) if stripe_subscription.trial_end else None,
                canceled_at=datetime.fromtimestamp(stripe_subscription.canceled_at, tz=timezone.utc) if stripe_subscription.canceled_at else None,
                metadata=stripe_subscription.metadata
            )
            
            return subscription
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'get_subscription',
                'subscription_id': subscription_id
            })
            raise
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Subscription:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            at_period_end: Whether to cancel at period end
            
        Returns:
            Updated Subscription object
            
        Raises:
            stripe.error.StripeError: If subscription cancellation fails
        """
        try:
            if at_period_end:
                stripe_subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                stripe_subscription = stripe.Subscription.cancel(subscription_id)
            
            subscription = Subscription(
                id=stripe_subscription.id,
                customer_id=stripe_subscription.customer,
                status=SubscriptionStatus(stripe_subscription.status),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc),
                cancel_at_period_end=stripe_subscription.cancel_at_period_end,
                created_at=datetime.fromtimestamp(stripe_subscription.created, tz=timezone.utc),
                trial_start=datetime.fromtimestamp(stripe_subscription.trial_start, tz=timezone.utc) if stripe_subscription.trial_start else None,
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end, tz=timezone.utc) if stripe_subscription.trial_end else None,
                canceled_at=datetime.fromtimestamp(stripe_subscription.canceled_at, tz=timezone.utc) if stripe_subscription.canceled_at else None,
                metadata=stripe_subscription.metadata
            )
            
            self.error_handler.logger.info(f"Cancelled subscription: {subscription_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'cancel_subscription',
                'subscription_id': subscription_id,
                'at_period_end': at_period_end
            })
            raise
    
    def update_subscription(self, subscription_id: str, tier: SubscriptionTier,
                          billing_cycle: str = 'monthly') -> Subscription:
        """
        Update subscription to a different tier.
        
        Args:
            subscription_id: Stripe subscription ID
            tier: New subscription tier
            billing_cycle: 'monthly' or 'yearly'
            
        Returns:
            Updated Subscription object
            
        Raises:
            stripe.error.StripeError: If subscription update fails
        """
        try:
            # Get price ID from configuration
            price_id = self.config.get_price_id(tier.value, billing_cycle)
            
            if not price_id:
                raise ValueError(f"Price ID not configured for {tier.value} {billing_cycle} plan")
            
            # Get current subscription
            current_subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Update subscription with new price
            stripe_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': current_subscription['items']['data'][0].id,
                    'price': price_id,
                }],
                proration_behavior='create_prorations'
            )
            
            subscription = Subscription(
                id=stripe_subscription.id,
                customer_id=stripe_subscription.customer,
                status=SubscriptionStatus(stripe_subscription.status),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc),
                cancel_at_period_end=stripe_subscription.cancel_at_period_end,
                created_at=datetime.fromtimestamp(stripe_subscription.created, tz=timezone.utc),
                trial_start=datetime.fromtimestamp(stripe_subscription.trial_start, tz=timezone.utc) if stripe_subscription.trial_start else None,
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end, tz=timezone.utc) if stripe_subscription.trial_end else None,
                canceled_at=datetime.fromtimestamp(stripe_subscription.canceled_at, tz=timezone.utc) if stripe_subscription.canceled_at else None,
                metadata=stripe_subscription.metadata
            )
            
            self.error_handler.logger.info(f"Updated subscription: {subscription_id} to {tier.value}")
            return subscription
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'update_subscription',
                'subscription_id': subscription_id,
                'tier': tier.value,
                'billing_cycle': billing_cycle
            })
            raise
    
    def get_customer_subscriptions(self, customer_id: str) -> List[Subscription]:
        """
        Get all subscriptions for a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            List of Subscription objects
            
        Raises:
            stripe.error.StripeError: If subscription retrieval fails
        """
        try:
            subscriptions = stripe.Subscription.list(customer=customer_id)
            
            subscription_list = []
            for stripe_subscription in subscriptions.data:
                subscription = Subscription(
                    id=stripe_subscription.id,
                    customer_id=stripe_subscription.customer,
                    status=SubscriptionStatus(stripe_subscription.status),
                    current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc),
                    current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc),
                    cancel_at_period_end=stripe_subscription.cancel_at_period_end,
                    created_at=datetime.fromtimestamp(stripe_subscription.created, tz=timezone.utc),
                    trial_start=datetime.fromtimestamp(stripe_subscription.trial_start, tz=timezone.utc) if stripe_subscription.trial_start else None,
                    trial_end=datetime.fromtimestamp(stripe_subscription.trial_end, tz=timezone.utc) if stripe_subscription.trial_end else None,
                    canceled_at=datetime.fromtimestamp(stripe_subscription.canceled_at, tz=timezone.utc) if stripe_subscription.canceled_at else None,
                    metadata=stripe_subscription.metadata
                )
                subscription_list.append(subscription)
            
            return subscription_list
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'get_customer_subscriptions',
                'customer_id': customer_id
            })
            raise
    
    def get_invoice(self, invoice_id: str) -> Invoice:
        """
        Retrieve an invoice.
        
        Args:
            invoice_id: Stripe invoice ID
            
        Returns:
            Invoice object
            
        Raises:
            stripe.error.StripeError: If invoice retrieval fails
        """
        try:
            stripe_invoice = stripe.Invoice.retrieve(invoice_id)
            
            invoice = Invoice(
                id=stripe_invoice.id,
                customer_id=stripe_invoice.customer,
                subscription_id=stripe_invoice.subscription,
                amount_due=stripe_invoice.amount_due,
                amount_paid=stripe_invoice.amount_paid,
                currency=stripe_invoice.currency,
                status=stripe_invoice.status,
                billing_reason=stripe_invoice.billing_reason,
                created_at=datetime.fromtimestamp(stripe_invoice.created, tz=timezone.utc),
                due_date=datetime.fromtimestamp(stripe_invoice.due_date, tz=timezone.utc) if stripe_invoice.due_date else None,
                paid_at=datetime.fromtimestamp(stripe_invoice.status_transitions.paid_at, tz=timezone.utc) if hasattr(stripe_invoice.status_transitions, 'paid_at') and stripe_invoice.status_transitions.paid_at else None,
                description=stripe_invoice.description,
                metadata=stripe_invoice.metadata
            )
            
            return invoice
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'get_invoice',
                'invoice_id': invoice_id
            })
            raise
    
    def get_customer_invoices(self, customer_id: str, limit: int = 10) -> List[Invoice]:
        """
        Get invoices for a customer.
        
        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return
            
        Returns:
            List of Invoice objects
            
        Raises:
            stripe.error.StripeError: If invoice retrieval fails
        """
        try:
            invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
            
            invoice_list = []
            for stripe_invoice in invoices.data:
                invoice = Invoice(
                    id=stripe_invoice.id,
                    customer_id=stripe_invoice.customer,
                    subscription_id=stripe_invoice.subscription,
                    amount_due=stripe_invoice.amount_due,
                    amount_paid=stripe_invoice.amount_paid,
                    currency=stripe_invoice.currency,
                    status=stripe_invoice.status,
                    billing_reason=stripe_invoice.billing_reason,
                    created_at=datetime.fromtimestamp(stripe_invoice.created, tz=timezone.utc),
                    due_date=datetime.fromtimestamp(stripe_invoice.due_date, tz=timezone.utc) if stripe_invoice.due_date else None,
                    paid_at=datetime.fromtimestamp(stripe_invoice.status_transitions.paid_at, tz=timezone.utc) if hasattr(stripe_invoice.status_transitions, 'paid_at') and stripe_invoice.status_transitions.paid_at else None,
                    description=stripe_invoice.description,
                    metadata=stripe_invoice.metadata
                )
                invoice_list.append(invoice)
            
            return invoice_list
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'get_customer_invoices',
                'customer_id': customer_id,
                'limit': limit
            })
            raise
    
    def get_payment_methods(self, customer_id: str) -> List[PaymentMethod]:
        """
        Get payment methods for a customer.
        
        Args:
            customer_id: Stripe customer ID
            
        Returns:
            List of PaymentMethod objects
            
        Raises:
            stripe.error.StripeError: If payment method retrieval fails
        """
        try:
            payment_methods = stripe.PaymentMethod.list(customer=customer_id, type='card')
            
            method_list = []
            for stripe_method in payment_methods.data:
                method = PaymentMethod(
                    id=stripe_method.id,
                    customer_id=stripe_method.customer,
                    type=PaymentMethodType(stripe_method.type),
                    card_brand=stripe_method.card.brand if stripe_method.card else None,
                    card_last4=stripe_method.card.last4 if stripe_method.card else None,
                    card_exp_month=stripe_method.card.exp_month if stripe_method.card else None,
                    card_exp_year=stripe_method.card.exp_year if stripe_method.card else None,
                    billing_details=stripe_method.billing_details.to_dict() if stripe_method.billing_details else None,
                    created_at=datetime.fromtimestamp(stripe_method.created, tz=timezone.utc),
                    metadata=stripe_method.metadata
                )
                method_list.append(method)
            
            return method_list
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'get_payment_methods',
                'customer_id': customer_id
            })
            raise
    
    def attach_payment_method(self, customer_id: str, payment_method_id: str) -> PaymentMethod:
        """
        Attach a payment method to a customer.
        
        Args:
            customer_id: Stripe customer ID
            payment_method_id: Stripe payment method ID
            
        Returns:
            PaymentMethod object
            
        Raises:
            stripe.error.StripeError: If payment method attachment fails
        """
        try:
            stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            
            # Retrieve the attached payment method
            stripe_method = stripe.PaymentMethod.retrieve(payment_method_id)
            
            method = PaymentMethod(
                id=stripe_method.id,
                customer_id=stripe_method.customer,
                type=PaymentMethodType(stripe_method.type),
                card_brand=stripe_method.card.brand if stripe_method.card else None,
                card_last4=stripe_method.card.last4 if stripe_method.card else None,
                card_exp_month=stripe_method.card.exp_month if stripe_method.card else None,
                card_exp_year=stripe_method.card.exp_year if stripe_method.card else None,
                billing_details=stripe_method.billing_details.to_dict() if stripe_method.billing_details else None,
                created_at=datetime.fromtimestamp(stripe_method.created, tz=timezone.utc),
                metadata=stripe_method.metadata
            )
            
            self.error_handler.logger.info(f"Attached payment method {payment_method_id} to customer {customer_id}")
            return method
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'attach_payment_method',
                'payment_method_id': payment_method_id,
                'customer_id': customer_id
            })
            raise
    
    def detach_payment_method(self, payment_method_id: str) -> bool:
        """
        Detach a payment method from a customer.
        
        Args:
            payment_method_id: Stripe payment method ID
            
        Returns:
            True if successful
            
        Raises:
            stripe.error.StripeError: If payment method detachment fails
        """
        try:
            stripe.PaymentMethod.detach(payment_method_id)
            self.error_handler.logger.info(f"Detached payment method: {payment_method_id}")
            return True
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'detach_payment_method',
                'payment_method_id': payment_method_id
            })
            raise
    
    def get_subscription_tier_info(self, tier: SubscriptionTier) -> TierFeatures:
        """
        Get information about a subscription tier.
        
        Args:
            tier: Subscription tier
            
        Returns:
            TierFeatures object
        """
        return self.SUBSCRIPTION_TIERS[tier]
    
    def get_all_tiers(self) -> Dict[SubscriptionTier, TierFeatures]:
        """
        Get all subscription tiers.
        
        Returns:
            Dictionary of all subscription tiers
        """
        return self.SUBSCRIPTION_TIERS.copy()
    
    def calculate_proration(self, subscription_id: str, new_price_id: str, 
                          proration_date: Optional[int] = None) -> Dict[str, Any]:
        """
        Calculate proration for subscription changes.
        
        Args:
            subscription_id: Stripe subscription ID
            new_price_id: New price ID
            proration_date: Proration date (Unix timestamp)
            
        Returns:
            Proration calculation
            
        Raises:
            stripe.error.StripeError: If proration calculation fails
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            proration_data = {
                'subscription': subscription_id,
                'subscription_items': [{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price_id,
                }]
            }
            
            if proration_date:
                proration_data['proration_date'] = proration_date
            
            proration = stripe.Invoice.upcoming(**proration_data)
            
            return {
                'total': proration.total,
                'subtotal': proration.subtotal,
                'tax': proration.tax,
                'lines': [line.to_dict() for line in proration.lines.data]
            }
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'calculate_proration',
                'subscription_id': subscription_id,
                'new_price_id': new_price_id,
                'proration_date': proration_date
            })
            raise
    
    def create_refund(self, payment_intent_id: str, amount: Optional[int] = None,
                     reason: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a refund for a payment.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Refund amount in cents (None for full refund)
            reason: Refund reason
            metadata: Additional metadata
            
        Returns:
            Refund information
            
        Raises:
            stripe.error.StripeError: If refund creation fails
        """
        try:
            refund_data = {
                'payment_intent': payment_intent_id,
                'metadata': metadata or {}
            }
            
            if amount:
                refund_data['amount'] = amount
            if reason:
                refund_data['reason'] = reason
            
            refund = stripe.Refund.create(**refund_data)
            
            self.error_handler.logger.info(f"Created refund: {refund.id} for payment intent: {payment_intent_id}")
            return refund.to_dict()
            
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'create_refund',
                'payment_intent_id': payment_intent_id,
                'amount': amount,
                'reason': reason
            })
            raise
    
    def handle_webhook(self, payload: bytes, signature: str, source_ip: str = '', 
                      user_agent: str = '', request_id: str = '', timestamp: str = None) -> Dict[str, Any]:
        """
        Handle Stripe webhook events with enhanced security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            source_ip: Source IP address for security validation
            user_agent: User agent string for logging
            request_id: Request identifier for tracking
            timestamp: Webhook timestamp for replay protection
            
        Returns:
            Webhook event data
            
        Raises:
            stripe.error.SignatureVerificationError: If signature verification fails
            stripe.error.StripeError: If webhook processing fails
        """
        try:
            if not self.webhook_secret:
                raise ValueError("Webhook secret not configured")
            
            # Enhanced webhook security validation
            is_valid, error_message = self.security_manager.validate_webhook_request(
                payload, signature, source_ip, timestamp, user_agent, request_id
            )
            
            if not is_valid:
                raise stripe.error.SignatureVerificationError(error_message, signature)
            
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            # Check if event is supported
            if not self.webhook_config.is_supported_event(event['type']):
                self.error_handler.logger.warning(f"Unsupported webhook event: {event['type']}")
                return event
            
            self.error_handler.logger.info(f"Received webhook event: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'customer.subscription.created':
                self._handle_subscription_created(event['data']['object'])
            elif event['type'] == 'customer.subscription.updated':
                self._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                self._handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                self._handle_invoice_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                self._handle_invoice_payment_failed(event['data']['object'])
            elif event['type'] == 'payment_intent.succeeded':
                self._handle_payment_intent_succeeded(event['data']['object'])
            elif event['type'] == 'payment_intent.payment_failed':
                self._handle_payment_intent_failed(event['data']['object'])
            
            return event
            
        except stripe.error.SignatureVerificationError as e:
            self.error_handler.log_error(e, {
                'operation': 'webhook_signature_verification',
                'signature': signature[:20] + '...' if signature else None,
                'source_ip': source_ip,
                'request_id': request_id
            })
            raise
        except stripe.error.StripeError as e:
            self.error_handler.log_error(e, {
                'operation': 'webhook_processing',
                'payload_size': len(payload),
                'source_ip': source_ip,
                'request_id': request_id
            })
            raise
    
    def _handle_subscription_created(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription created webhook."""
        self.error_handler.log_subscription_event('created', subscription_data)
        # Add your business logic here
    
    def _handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription updated webhook."""
        self.error_handler.log_subscription_event('updated', subscription_data)
        # Add your business logic here
    
    def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription deleted webhook."""
        self.error_handler.log_subscription_event('deleted', subscription_data)
        # Add your business logic here
    
    def _handle_invoice_payment_succeeded(self, invoice_data: Dict[str, Any]) -> None:
        """Handle invoice payment succeeded webhook."""
        self.error_handler.log_payment_event('invoice_payment_succeeded', invoice_data)
        # Add your business logic here
    
    def _handle_invoice_payment_failed(self, invoice_data: Dict[str, Any]) -> None:
        """Handle invoice payment failed webhook."""
        self.error_handler.log_payment_event('invoice_payment_failed', invoice_data)
        # Add your business logic here
    
    def _handle_payment_intent_succeeded(self, payment_intent_data: Dict[str, Any]) -> None:
        """Handle payment intent succeeded webhook."""
        self.error_handler.log_payment_event('payment_intent_succeeded', payment_intent_data)
        # Add your business logic here
    
    def _handle_payment_intent_failed(self, payment_intent_data: Dict[str, Any]) -> None:
        """Handle payment intent failed webhook."""
        self.error_handler.log_payment_event('payment_intent_failed', payment_intent_data)
        # Add your business logic here 