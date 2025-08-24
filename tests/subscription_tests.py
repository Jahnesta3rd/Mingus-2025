"""
MINGUS Application - Comprehensive Subscription System Tests
==========================================================

Complete testing suite for the MINGUS subscription system that validates:
- All billing scenarios and edge cases
- Subscription lifecycle management
- Payment processing and recovery
- Tier management and feature access
- Webhook handling and integration
- Billing calculations and proration
- Usage tracking and limits
- Customer portal functionality
- Revenue optimization features

Author: MINGUS Development Team
Date: January 2025
"""

import pytest
import uuid
import json
import stripe
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

# Import MINGUS models and services
from backend.models.subscription import (
    Customer, Subscription, PaymentMethod, BillingHistory, 
    PricingTier, FeatureUsage, AuditLog, AuditEventType, AuditSeverity,
    Refund, Credit, SubscriptionStatus, BillingCycle, TaxCalculationMethod
)
from backend.models.subscription_models import (
    MINGUSSubscription, MINGUSInvoice, MINGUSPaymentMethod, MINGUSUsageRecord,
    MINGUSSubscriptionTier, MINGUSBillingEvent, BillingCycle as ModelBillingCycle,
    SubscriptionStatus as ModelSubscriptionStatus, PaymentStatus, UsageType
)
from backend.payment.stripe_integration import StripeService, SubscriptionTier
from backend.services.payment_service import PaymentService
from backend.services.billing_service import BillingService
from backend.services.subscription_service import SubscriptionService
from backend.services.payment_processor import PaymentProcessor
from backend.services.subscription_manager import SubscriptionManager
from backend.services.billing_features import BillingFeatures
from backend.services.usage_tracker import UsageTracker
from backend.services.customer_portal import CustomerPortal
from backend.services.revenue_optimizer import RevenueOptimizer
from backend.services.subscription_lifecycle import SubscriptionLifecycleManager
from backend.services.automated_workflows import AutomatedWorkflowManager
from backend.services.feature_access_service import FeatureAccessService
from backend.services.payment_recovery_service import PaymentRecoveryService
from backend.webhooks.stripe_webhooks import StripeWebhookManager
from backend.config.base import Config


class TestSubscriptionSystem:
    """Comprehensive test suite for the MINGUS subscription system."""
    
    @pytest.fixture
    def db_session(self):
        """Create test database session."""
        engine = create_engine('sqlite:///:memory:')
        from backend.models.base import Base
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=Config)
        config.STRIPE_SECRET_KEY = 'sk_test_mock_key'
        config.STRIPE_PUBLISHABLE_KEY = 'pk_test_mock_key'
        config.STRIPE_WEBHOOK_SECRET = 'whsec_mock_secret'
        config.ENVIRONMENT = 'test'
        return config
    
    @pytest.fixture
    def mock_stripe(self):
        """Mock Stripe API."""
        with patch('stripe.Customer') as mock_customer, \
             patch('stripe.Subscription') as mock_subscription, \
             patch('stripe.PaymentMethod') as mock_payment_method, \
             patch('stripe.Invoice') as mock_invoice, \
             patch('stripe.PaymentIntent') as mock_payment_intent:
            
            # Mock customer creation
            mock_customer.create.return_value = Mock(
                id='cus_test123',
                email='test@example.com',
                name='Test User'
            )
            
            # Mock subscription creation
            mock_subscription.create.return_value = Mock(
                id='sub_test123',
                status='active',
                current_period_start=int(datetime.now().timestamp()),
                current_period_end=int((datetime.now() + timedelta(days=30)).timestamp()),
                trial_end=None
            )
            
            # Mock payment method
            mock_payment_method.attach.return_value = Mock(
                id='pm_test123',
                type='card',
                card=Mock(brand='visa', last4='4242')
            )
            
            # Mock invoice
            mock_invoice.create.return_value = Mock(
                id='in_test123',
                status='paid',
                amount_paid=1500,
                amount_due=1500
            )
            
            # Mock payment intent
            mock_payment_intent.create.return_value = Mock(
                id='pi_test123',
                status='succeeded',
                amount=1500
            )
            
            yield {
                'customer': mock_customer,
                'subscription': mock_subscription,
                'payment_method': mock_payment_method,
                'invoice': mock_invoice,
                'payment_intent': mock_payment_intent
            }
    
    @pytest.fixture
    def sample_pricing_tiers(self, db_session):
        """Create sample pricing tiers for testing."""
        tiers = []
        
        # Budget Tier
        budget_tier = PricingTier(
            tier_type='budget',
            name='Budget Tier',
            description='Basic features for individuals',
            monthly_price=15.00,
            yearly_price=144.00,
            stripe_price_id_monthly='price_budget_monthly',
            stripe_price_id_yearly='price_budget_yearly',
            max_health_checkins_per_month=4,
            max_financial_reports_per_month=2,
            max_ai_insights_per_month=0,
            max_projects=1,
            max_team_members=1,
            max_storage_gb=1,
            max_api_calls_per_month=1000,
            advanced_analytics=False,
            priority_support=False,
            custom_integrations=False,
            is_active=True
        )
        
        # Mid-Tier
        mid_tier = PricingTier(
            tier_type='mid_tier',
            name='Mid-Tier',
            description='Enhanced features for serious users',
            monthly_price=35.00,
            yearly_price=336.00,
            stripe_price_id_monthly='price_mid_monthly',
            stripe_price_id_yearly='price_mid_yearly',
            max_health_checkins_per_month=12,
            max_financial_reports_per_month=10,
            max_ai_insights_per_month=50,
            max_projects=5,
            max_team_members=3,
            max_storage_gb=10,
            max_api_calls_per_month=5000,
            advanced_analytics=True,
            priority_support=True,
            custom_integrations=False,
            is_active=True
        )
        
        # Professional Tier
        professional_tier = PricingTier(
            tier_type='professional',
            name='Professional Tier',
            description='Unlimited access for professionals',
            monthly_price=75.00,
            yearly_price=720.00,
            stripe_price_id_monthly='price_professional_monthly',
            stripe_price_id_yearly='price_professional_yearly',
            max_health_checkins_per_month=-1,  # Unlimited
            max_financial_reports_per_month=-1,  # Unlimited
            max_ai_insights_per_month=-1,  # Unlimited
            max_projects=-1,  # Unlimited
            max_team_members=10,
            max_storage_gb=100,
            max_api_calls_per_month=10000,
            advanced_analytics=True,
            priority_support=True,
            custom_integrations=True,
            is_active=True
        )
        
        db_session.add_all([budget_tier, mid_tier, professional_tier])
        db_session.commit()
        
        return [budget_tier, mid_tier, professional_tier]
    
    @pytest.fixture
    def sample_customer(self, db_session):
        """Create sample customer for testing."""
        customer = Customer(
            user_id=1,
            email='test@example.com',
            name='Test User',
            stripe_customer_id='cus_test123',
            phone='+1234567890',
            address_line1='123 Test St',
            address_city='Test City',
            address_state='TS',
            address_postal_code='12345',
            address_country='US',
            tax_exempt='none',
            metadata={'source': 'test'},
            is_active=True
        )
        db_session.add(customer)
        db_session.commit()
        return customer
    
    @pytest.fixture
    def sample_subscription(self, db_session, sample_customer, sample_pricing_tiers):
        """Create sample subscription for testing."""
        subscription = Subscription(
            customer_id=sample_customer.id,
            pricing_tier_id=sample_pricing_tiers[0].id,  # Budget tier
            stripe_subscription_id='sub_test123',
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            cancel_at_period_end=False,
            canceled_at=None,
            trial_start=None,
            trial_end=None,
            billing_cycle=BillingCycle.MONTHLY,
            amount=15.00,
            currency='USD',
            proration_behavior='create_prorations',
            proration_date=None,
            next_billing_date=datetime.now(timezone.utc) + timedelta(days=30),
            tax_percent=0.0,
            tax_calculation_method=TaxCalculationMethod.AUTOMATIC,
            tax_exempt='none',
            tax_identification_number=None,
            usage_type='licensed',
            usage_aggregation='sum',
            metadata={'test': True}
        )
        db_session.add(subscription)
        db_session.commit()
        return subscription
    
    @pytest.fixture
    def payment_service(self, db_session, mock_config, mock_stripe):
        """Create payment service instance for testing."""
        return PaymentService(db_session, mock_config)
    
    @pytest.fixture
    def billing_service(self, db_session, mock_config, mock_stripe):
        """Create billing service instance for testing."""
        payment_processor = PaymentProcessor(db_session, mock_config)
        subscription_manager = SubscriptionManager(db_session, mock_config)
        return BillingService(db_session, payment_processor, subscription_manager)
    
    @pytest.fixture
    def subscription_service(self, db_session, mock_config):
        """Create subscription service instance for testing."""
        stripe_service = StripeService()
        return SubscriptionService(db_session, stripe_service)
    
    @pytest.fixture
    def webhook_manager(self, db_session, mock_config):
        """Create webhook manager instance for testing."""
        return StripeWebhookManager(db_session, mock_config)


class TestSubscriptionCreation:
    """Test subscription creation scenarios."""
    
    def test_create_subscription_with_payment_success(self, payment_service, sample_customer, sample_pricing_tiers):
        """Test successful subscription creation with payment method."""
        result = payment_service.create_subscription_with_payment(
            user_id=sample_customer.user_id,
            email=sample_customer.email,
            name=sample_customer.name,
            pricing_tier_id=sample_pricing_tiers[0].id,
            payment_method_id='pm_test123',
            billing_cycle='monthly',
            trial_days=0
        )
        
        assert result['success'] is True
        assert 'customer_id' in result
        assert 'subscription_id' in result
        assert 'payment_method_id' in result
        assert 'stripe_customer_id' in result
        assert 'stripe_subscription_id' in result
    
    def test_create_subscription_with_trial(self, payment_service, sample_customer, sample_pricing_tiers):
        """Test subscription creation with trial period."""
        result = payment_service.create_subscription_with_payment(
            user_id=sample_customer.user_id,
            email=sample_customer.email,
            name=sample_customer.name,
            pricing_tier_id=sample_pricing_tiers[0].id,
            payment_method_id='pm_test123',
            billing_cycle='monthly',
            trial_days=14
        )
        
        assert result['success'] is True
        assert result['trial_end'] is not None
    
    def test_create_subscription_yearly_billing(self, payment_service, sample_customer, sample_pricing_tiers):
        """Test subscription creation with yearly billing."""
        result = payment_service.create_subscription_with_payment(
            user_id=sample_customer.user_id,
            email=sample_customer.email,
            name=sample_customer.name,
            pricing_tier_id=sample_pricing_tiers[0].id,
            payment_method_id='pm_test123',
            billing_cycle='yearly',
            trial_days=0
        )
        
        assert result['success'] is True
    
    def test_create_subscription_invalid_tier(self, payment_service, sample_customer):
        """Test subscription creation with invalid pricing tier."""
        result = payment_service.create_subscription_with_payment(
            user_id=sample_customer.user_id,
            email=sample_customer.email,
            name=sample_customer.name,
            pricing_tier_id=99999,  # Invalid tier ID
            payment_method_id='pm_test123',
            billing_cycle='monthly'
        )
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_create_subscription_invalid_payment_method(self, payment_service, sample_customer, sample_pricing_tiers):
        """Test subscription creation with invalid payment method."""
        with patch('stripe.PaymentMethod.attach') as mock_attach:
            mock_attach.side_effect = stripe.error.CardError("Invalid payment method", None, None)
            
            result = payment_service.create_subscription_with_payment(
                user_id=sample_customer.user_id,
                email=sample_customer.email,
                name=sample_customer.name,
                pricing_tier_id=sample_pricing_tiers[0].id,
                payment_method_id='pm_invalid',
                billing_cycle='monthly'
            )
            
            assert result['success'] is False
            assert 'error' in result


class TestSubscriptionLifecycle:
    """Test subscription lifecycle management."""
    
    # ============================================================================
    # TRIAL CREATION AND MANAGEMENT
    # ============================================================================
    
    def test_trial_subscription_creation(self, payment_service, sample_customer, sample_pricing_tiers):
        """Test trial subscription creation with no payment method."""
        result = payment_service.create_subscription_with_payment(
            user_id=sample_customer.user_id,
            email=sample_customer.email,
            name=sample_customer.name,
            pricing_tier_id=sample_pricing_tiers[0].id,
            payment_method_id=None,  # No payment method for trial
            billing_cycle='monthly',
            trial_days=14
        )
        
        assert result['success'] is True
        assert result['trial_end'] is not None
        assert 'subscription_id' in result
    
    def test_trial_subscription_with_payment_method(self, payment_service, sample_customer, sample_pricing_tiers):
        """Test trial subscription creation with payment method for future billing."""
        result = payment_service.create_subscription_with_payment(
            user_id=sample_customer.user_id,
            email=sample_customer.email,
            name=sample_customer.name,
            pricing_tier_id=sample_pricing_tiers[0].id,
            payment_method_id='pm_test123',
            billing_cycle='monthly',
            trial_days=7
        )
        
        assert result['success'] is True
        assert result['trial_end'] is not None
        assert result['payment_method_id'] is not None
    
    def test_trial_extension(self, subscription_service, sample_subscription):
        """Test extending a trial period."""
        # Set up trial subscription
        sample_subscription.trial_start = datetime.now(timezone.utc)
        sample_subscription.trial_end = datetime.now(timezone.utc) + timedelta(days=7)
        sample_subscription.status = SubscriptionStatus.TRIAL
        subscription_service.db.commit()
        
        # Extend trial by 7 more days
        result = subscription_service.extend_trial(
            subscription_id=sample_subscription.id,
            additional_days=7
        )
        
        assert result['success'] is True
        assert result['new_trial_end'] > sample_subscription.trial_end
    
    def test_trial_early_conversion(self, subscription_service, sample_subscription):
        """Test converting trial to paid before trial ends."""
        # Set up trial subscription
        sample_subscription.trial_start = datetime.now(timezone.utc)
        sample_subscription.trial_end = datetime.now(timezone.utc) + timedelta(days=7)
        sample_subscription.status = SubscriptionStatus.TRIAL
        subscription_service.db.commit()
        
        # Convert to paid immediately
        result = subscription_service.convert_trial_to_paid(
            subscription_id=sample_subscription.id,
            payment_method_id='pm_test123'
        )
        
        assert result['success'] is True
        assert result['status'] == SubscriptionStatus.ACTIVE
        assert result['trial_end'] is None
    
    def test_trial_expiration_handling(self, subscription_service, sample_subscription):
        """Test handling of trial expiration."""
        # Set up expired trial
        sample_subscription.trial_start = datetime.now(timezone.utc) - timedelta(days=15)
        sample_subscription.trial_end = datetime.now(timezone.utc) - timedelta(days=1)
        sample_subscription.status = SubscriptionStatus.TRIAL
        subscription_service.db.commit()
        
        # Process trial expiration
        result = subscription_service.handle_trial_expiration(sample_subscription.id)
        
        assert result['success'] is True
        assert result['action'] == 'suspend_subscription'
        assert result['status'] == SubscriptionStatus.PAST_DUE
    
    # ============================================================================
    # TRIAL TO PAID CONVERSION
    # ============================================================================
    
    def test_trial_to_paid_conversion_success(self, subscription_service, sample_subscription):
        """Test successful trial to paid conversion."""
        # Set up trial subscription
        sample_subscription.trial_start = datetime.now(timezone.utc) - timedelta(days=5)
        sample_subscription.trial_end = datetime.now(timezone.utc) + timedelta(days=2)
        sample_subscription.status = SubscriptionStatus.TRIAL
        subscription_service.db.commit()
        
        # Convert to paid
        result = subscription_service.convert_trial_to_paid(
            subscription_id=sample_subscription.id,
            payment_method_id='pm_test123'
        )
        
        assert result['success'] is True
        assert result['status'] == SubscriptionStatus.ACTIVE
        assert result['payment_method_id'] == 'pm_test123'
    
    def test_trial_to_paid_conversion_without_payment_method(self, subscription_service, sample_subscription):
        """Test trial to paid conversion without payment method (should fail)."""
        # Set up trial subscription
        sample_subscription.trial_start = datetime.now(timezone.utc) - timedelta(days=5)
        sample_subscription.trial_end = datetime.now(timezone.utc) + timedelta(days=2)
        sample_subscription.status = SubscriptionStatus.TRIAL
        subscription_service.db.commit()
        
        # Try to convert without payment method
        result = subscription_service.convert_trial_to_paid(
            subscription_id=sample_subscription.id,
            payment_method_id=None
        )
        
        assert result['success'] is False
        assert 'payment method' in result['error'].lower()
    
    def test_trial_to_paid_conversion_with_invalid_payment_method(self, subscription_service, sample_subscription):
        """Test trial to paid conversion with invalid payment method."""
        # Set up trial subscription
        sample_subscription.trial_start = datetime.now(timezone.utc) - timedelta(days=5)
        sample_subscription.trial_end = datetime.now(timezone.utc) + timedelta(days=2)
        sample_subscription.status = SubscriptionStatus.TRIAL
        subscription_service.db.commit()
        
        # Try to convert with invalid payment method
        with patch('stripe.PaymentMethod.attach') as mock_attach:
            mock_attach.side_effect = stripe.error.CardError("Invalid payment method", None, None)
            
            result = subscription_service.convert_trial_to_paid(
                subscription_id=sample_subscription.id,
                payment_method_id='pm_invalid'
            )
            
            assert result['success'] is False
            assert 'Invalid payment method' in result['error']
    
    def test_trial_to_paid_conversion_billing_cycle_change(self, subscription_service, sample_subscription):
        """Test trial to paid conversion with billing cycle change."""
        # Set up trial subscription
        sample_subscription.trial_start = datetime.now(timezone.utc) - timedelta(days=5)
        sample_subscription.trial_end = datetime.now(timezone.utc) + timedelta(days=2)
        sample_subscription.status = SubscriptionStatus.TRIAL
        sample_subscription.billing_cycle = BillingCycle.MONTHLY
        subscription_service.db.commit()
        
        # Convert to paid with yearly billing
        result = subscription_service.convert_trial_to_paid(
            subscription_id=sample_subscription.id,
            payment_method_id='pm_test123',
            new_billing_cycle='yearly'
        )
        
        assert result['success'] is True
        assert result['billing_cycle'] == 'yearly'
        assert result['amount'] > sample_subscription.amount  # Yearly should be more expensive
    
    # ============================================================================
    # SUBSCRIPTION UPGRADES WITH PRORATION
    # ============================================================================
    
    def test_subscription_upgrade_with_proration(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription upgrade with proration calculation."""
        # Set up subscription mid-period
        sample_subscription.current_period_start = datetime.now(timezone.utc) - timedelta(days=15)
        sample_subscription.current_period_end = datetime.now(timezone.utc) + timedelta(days=15)
        sample_subscription.amount = 15.00  # Budget tier
        subscription_service.db.commit()
        
        # Upgrade to mid-tier
        result = subscription_service.upgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[1].id,  # Mid-tier ($35)
            proration_behavior='create_prorations'
        )
        
        assert result['success'] is True
        assert result['new_tier_id'] == sample_pricing_tiers[1].id
        assert result['proration_amount'] > 0
        assert result['proration_amount'] < 35.00  # Should be prorated
    
    def test_subscription_upgrade_immediate_effective(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription upgrade effective immediately."""
        result = subscription_service.upgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[1].id,
            effective_date='immediate'
        )
        
        assert result['success'] is True
        assert result['effective_date'] == 'immediate'
        assert result['proration_amount'] > 0
    
    def test_subscription_upgrade_period_end_effective(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription upgrade effective at period end."""
        result = subscription_service.upgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[1].id,
            effective_date='period_end'
        )
        
        assert result['success'] is True
        assert result['effective_date'] == 'period_end'
        assert result['proration_amount'] == 0  # No proration for period-end changes
    
    def test_subscription_upgrade_with_usage_limits(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription upgrade with usage limit changes."""
        # Set up usage tracking
        usage_record = FeatureUsage(
            subscription_id=sample_subscription.id,
            feature_name='api_calls',
            usage_quantity=800,  # Under budget tier limit
            usage_date=datetime.now(timezone.utc),
            unit_price=0.01
        )
        subscription_service.db.add(usage_record)
        subscription_service.db.commit()
        
        # Upgrade to mid-tier (higher limits)
        result = subscription_service.upgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[1].id
        )
        
        assert result['success'] is True
        assert result['usage_limits_updated'] is True
        assert result['new_api_calls_limit'] > 1000  # Higher limit for mid-tier
    
    def test_subscription_upgrade_payment_failure(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription upgrade with payment failure."""
        with patch('stripe.Invoice.pay') as mock_pay:
            mock_pay.side_effect = stripe.error.CardError("Payment failed", None, None)
            
            result = subscription_service.upgrade_subscription(
                subscription_id=sample_subscription.id,
                new_tier_id=sample_pricing_tiers[1].id,
                proration_behavior='create_prorations'
            )
            
            assert result['success'] is False
            assert 'Payment failed' in result['error']
    
    # ============================================================================
    # SUBSCRIPTION DOWNGRADES WITH PRORATION
    # ============================================================================
    
    def test_subscription_downgrade_with_proration(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription downgrade with proration calculation."""
        # First upgrade to mid-tier
        subscription_service.upgrade_subscription(
            sample_subscription.id,
            sample_pricing_tiers[1].id
        )
        
        # Set up mid-period
        sample_subscription.current_period_start = datetime.now(timezone.utc) - timedelta(days=15)
        sample_subscription.current_period_end = datetime.now(timezone.utc) + timedelta(days=15)
        sample_subscription.amount = 35.00  # Mid-tier
        subscription_service.db.commit()
        
        # Downgrade to budget tier
        result = subscription_service.downgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[0].id,  # Budget tier ($15)
            effective_date='immediate'
        )
        
        assert result['success'] is True
        assert result['new_tier_id'] == sample_pricing_tiers[0].id
        assert result['proration_credit'] > 0  # Should get credit for unused portion
        assert result['proration_credit'] < 35.00
    
    def test_subscription_downgrade_period_end_effective(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription downgrade effective at period end."""
        # First upgrade to mid-tier
        subscription_service.upgrade_subscription(
            sample_subscription.id,
            sample_pricing_tiers[1].id
        )
        
        # Downgrade to budget tier at period end
        result = subscription_service.downgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[0].id,
            effective_date='period_end'
        )
        
        assert result['success'] is True
        assert result['effective_date'] == 'period_end'
        assert result['proration_credit'] == 0  # No credit for period-end changes
    
    def test_subscription_downgrade_with_usage_exceeding_new_limits(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription downgrade when usage exceeds new tier limits."""
        # First upgrade to mid-tier
        subscription_service.upgrade_subscription(
            sample_subscription.id,
            sample_pricing_tiers[1].id
        )
        
        # Add usage that exceeds budget tier limits
        usage_record = FeatureUsage(
            subscription_id=sample_subscription.id,
            feature_name='api_calls',
            usage_quantity=1500,  # Exceeds budget tier 1000 limit
            usage_date=datetime.now(timezone.utc),
            unit_price=0.01
        )
        subscription_service.db.add(usage_record)
        subscription_service.db.commit()
        
        # Try to downgrade to budget tier
        result = subscription_service.downgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[0].id
        )
        
        assert result['success'] is False
        assert 'usage exceeds limits' in result['error'].lower()
    
    def test_subscription_downgrade_grace_period(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription downgrade with grace period for usage adjustment."""
        # First upgrade to mid-tier
        subscription_service.upgrade_subscription(
            sample_subscription.id,
            sample_pricing_tiers[1].id
        )
        
        # Add usage that exceeds budget tier limits
        usage_record = FeatureUsage(
            subscription_id=sample_subscription.id,
            feature_name='api_calls',
            usage_quantity=1500,
            usage_date=datetime.now(timezone.utc),
            unit_price=0.01
        )
        subscription_service.db.add(usage_record)
        subscription_service.db.commit()
        
        # Downgrade with grace period
        result = subscription_service.downgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[0].id,
            grace_period_days=7
        )
        
        assert result['success'] is True
        assert result['grace_period_end'] is not None
        assert result['warning'] == 'Usage exceeds new tier limits'
    
    # ============================================================================
    # SUBSCRIPTION CANCELLATION AND REACTIVATION
    # ============================================================================
    
    def test_subscription_cancellation_at_period_end(self, subscription_service, sample_subscription):
        """Test subscription cancellation at period end."""
        result = subscription_service.cancel_subscription(
            subscription_id=sample_subscription.id,
            cancel_at_period_end=True
        )
        
        assert result['success'] is True
        assert result['cancel_at_period_end'] is True
        assert result['cancellation_date'] is not None
        assert result['access_until'] == sample_subscription.current_period_end
    
    def test_subscription_immediate_cancellation(self, subscription_service, sample_subscription):
        """Test immediate subscription cancellation."""
        result = subscription_service.cancel_subscription(
            subscription_id=sample_subscription.id,
            cancel_at_period_end=False
        )
        
        assert result['success'] is True
        assert result['cancel_at_period_end'] is False
        assert result['cancellation_date'] is not None
        assert result['access_until'] == datetime.now(timezone.utc)
    
    def test_subscription_cancellation_with_refund(self, subscription_service, sample_subscription):
        """Test subscription cancellation with refund calculation."""
        # Set up subscription with unused period
        sample_subscription.current_period_start = datetime.now(timezone.utc) - timedelta(days=5)
        sample_subscription.current_period_end = datetime.now(timezone.utc) + timedelta(days=25)
        sample_subscription.amount = 15.00
        subscription_service.db.commit()
        
        result = subscription_service.cancel_subscription(
            subscription_id=sample_subscription.id,
            cancel_at_period_end=False,
            refund_unused_period=True
        )
        
        assert result['success'] is True
        assert result['refund_amount'] > 0
        assert result['refund_amount'] < 15.00  # Should be prorated
    
    def test_subscription_reactivation_before_period_end(self, subscription_service, sample_subscription):
        """Test subscription reactivation before period end."""
        # First cancel at period end
        subscription_service.cancel_subscription(
            sample_subscription.id,
            cancel_at_period_end=True
        )
        
        # Reactivate before period end
        result = subscription_service.reactivate_subscription(sample_subscription.id)
        
        assert result['success'] is True
        assert result['cancel_at_period_end'] is False
        assert result['cancellation_date'] is None
    
    def test_subscription_reactivation_after_period_end(self, subscription_service, sample_subscription):
        """Test subscription reactivation after period end."""
        # First cancel at period end
        subscription_service.cancel_subscription(
            sample_subscription.id,
            cancel_at_period_end=True
        )
        
        # Simulate period end
        sample_subscription.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)
        subscription_service.db.commit()
        
        # Reactivate after period end
        result = subscription_service.reactivate_subscription(
            subscription_id=sample_subscription.id,
            payment_method_id='pm_test123'
        )
        
        assert result['success'] is True
        assert result['new_period_start'] is not None
        assert result['payment_required'] is True
    
    def test_subscription_reactivation_with_different_tier(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription reactivation with different tier."""
        # First cancel
        subscription_service.cancel_subscription(
            sample_subscription.id,
            cancel_at_period_end=True
        )
        
        # Reactivate with different tier
        result = subscription_service.reactivate_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[1].id,  # Mid-tier
            payment_method_id='pm_test123'
        )
        
        assert result['success'] is True
        assert result['new_tier_id'] == sample_pricing_tiers[1].id
        assert result['amount'] == 35.00  # Mid-tier price
    
    # ============================================================================
    # PAYMENT METHOD UPDATES AND VALIDATION
    # ============================================================================
    
    def test_payment_method_update_success(self, subscription_service, sample_subscription):
        """Test successful payment method update."""
        result = subscription_service.update_payment_method(
            subscription_id=sample_subscription.id,
            new_payment_method_id='pm_new123'
        )
        
        assert result['success'] is True
        assert result['payment_method_id'] == 'pm_new123'
        assert result['updated_at'] is not None
    
    def test_payment_method_update_with_invalid_method(self, subscription_service, sample_subscription):
        """Test payment method update with invalid method."""
        with patch('stripe.PaymentMethod.attach') as mock_attach:
            mock_attach.side_effect = stripe.error.CardError("Invalid payment method", None, None)
            
            result = subscription_service.update_payment_method(
                subscription_id=sample_subscription.id,
                new_payment_method_id='pm_invalid'
            )
            
            assert result['success'] is False
            assert 'Invalid payment method' in result['error']
    
    def test_payment_method_update_with_expired_card(self, subscription_service, sample_subscription):
        """Test payment method update with expired card."""
        with patch('stripe.PaymentMethod.attach') as mock_attach:
            mock_attach.side_effect = stripe.error.CardError("Card expired", None, None)
            
            result = subscription_service.update_payment_method(
                subscription_id=sample_subscription.id,
                new_payment_method_id='pm_expired'
            )
            
            assert result['success'] is False
            assert 'Card expired' in result['error']
    
    def test_payment_method_update_with_insufficient_funds(self, subscription_service, sample_subscription):
        """Test payment method update with insufficient funds."""
        with patch('stripe.PaymentMethod.attach') as mock_attach:
            mock_attach.side_effect = stripe.error.CardError("Insufficient funds", None, None)
            
            result = subscription_service.update_payment_method(
                subscription_id=sample_subscription.id,
                new_payment_method_id='pm_insufficient'
            )
            
            assert result['success'] is False
            assert 'Insufficient funds' in result['error']
    
    def test_payment_method_validation_success(self, subscription_service, sample_subscription):
        """Test successful payment method validation."""
        result = subscription_service.validate_payment_method(
            payment_method_id='pm_test123',
            amount=15.00,
            currency='usd'
        )
        
        assert result['success'] is True
        assert result['valid'] is True
        assert result['card_brand'] is not None
        assert result['last4'] is not None
    
    def test_payment_method_validation_failure(self, subscription_service, sample_subscription):
        """Test payment method validation failure."""
        with patch('stripe.PaymentMethod.retrieve') as mock_retrieve:
            mock_retrieve.side_effect = stripe.error.InvalidRequestError("Invalid payment method", None)
            
            result = subscription_service.validate_payment_method(
                payment_method_id='pm_invalid',
                amount=15.00,
                currency='usd'
            )
            
            assert result['success'] is False
            assert result['valid'] is False
            assert 'Invalid payment method' in result['error']
    
    def test_payment_method_removal(self, subscription_service, sample_subscription):
        """Test payment method removal."""
        # First add a payment method
        subscription_service.update_payment_method(
            sample_subscription.id,
            'pm_test123'
        )
        
        # Then remove it
        result = subscription_service.remove_payment_method(
            subscription_id=sample_subscription.id
        )
        
        assert result['success'] is True
        assert result['payment_method_id'] is None
    
    def test_payment_method_removal_with_active_subscription(self, subscription_service, sample_subscription):
        """Test payment method removal with active subscription (should fail)."""
        result = subscription_service.remove_payment_method(
            subscription_id=sample_subscription.id
        )
        
        assert result['success'] is False
        assert 'active subscription' in result['error'].lower()
    
    # ============================================================================
    # LEGACY TESTS (KEPT FOR BACKWARD COMPATIBILITY)
    # ============================================================================
    
    def test_subscription_activation(self, subscription_service, sample_subscription):
        """Test subscription activation."""
        # Simulate subscription activation
        subscription_service.activate_subscription(sample_subscription.id)
        
        updated_subscription = subscription_service.get_subscription_by_id(sample_subscription.id)
        assert updated_subscription.status == SubscriptionStatus.ACTIVE
    
    def test_subscription_cancellation(self, subscription_service, sample_subscription):
        """Test subscription cancellation."""
        # Cancel at period end
        result = subscription_service.cancel_subscription(
            subscription_id=sample_subscription.id,
            cancel_at_period_end=True
        )
        
        assert result['success'] is True
        assert result['cancel_at_period_end'] is True
    
    def test_subscription_immediate_cancellation(self, subscription_service, sample_subscription):
        """Test immediate subscription cancellation."""
        result = subscription_service.cancel_subscription(
            subscription_id=sample_subscription.id,
            cancel_at_period_end=False
        )
        
        assert result['success'] is True
        assert result['cancel_at_period_end'] is False
    
    def test_subscription_reactivation(self, subscription_service, sample_subscription):
        """Test subscription reactivation."""
        # First cancel
        subscription_service.cancel_subscription(sample_subscription.id, cancel_at_period_end=True)
        
        # Then reactivate
        result = subscription_service.reactivate_subscription(sample_subscription.id)
        
        assert result['success'] is True
        assert result['cancel_at_period_end'] is False
    
    def test_subscription_upgrade(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription upgrade to higher tier."""
        result = subscription_service.upgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[1].id,  # Mid-tier
            proration_behavior='create_prorations'
        )
        
        assert result['success'] is True
        assert result['new_tier_id'] == sample_pricing_tiers[1].id
    
    def test_subscription_downgrade(self, subscription_service, sample_subscription, sample_pricing_tiers):
        """Test subscription downgrade to lower tier."""
        # First upgrade to mid-tier
        subscription_service.upgrade_subscription(
            sample_subscription.id,
            sample_pricing_tiers[1].id
        )
        
        # Then downgrade to budget tier
        result = subscription_service.downgrade_subscription(
            subscription_id=sample_subscription.id,
            new_tier_id=sample_pricing_tiers[0].id,  # Budget tier
            effective_date='period_end'
        )
        
        assert result['success'] is True
        assert result['new_tier_id'] == sample_pricing_tiers[0].id


class TestBillingScenarios:
    """Test various billing scenarios and edge cases."""
    
    def test_recurring_billing_success(self, billing_service, sample_subscription):
        """Test successful recurring billing."""
        result = billing_service.process_recurring_billing()
        
        assert 'processed' in result
        assert 'successful' in result
        assert 'failed' in result
        assert 'errors' in result
    
    def test_billing_with_usage_charges(self, billing_service, sample_subscription):
        """Test billing with usage-based charges."""
        # Add usage records
        usage_record = FeatureUsage(
            subscription_id=sample_subscription.id,
            feature_name='api_calls',
            usage_quantity=1500,  # Over the 1000 limit
            usage_date=datetime.now(timezone.utc),
            unit_price=0.01
        )
        billing_service.db.add(usage_record)
        billing_service.db.commit()
        
        # Process billing
        result = billing_service._process_subscription_billing(sample_subscription)
        
        assert result['success'] is True
        assert result['amount'] > sample_subscription.amount  # Should include usage charges
    
    def test_billing_with_tax_calculation(self, billing_service, sample_subscription):
        """Test billing with tax calculation."""
        # Set tax percentage
        sample_subscription.tax_percent = 8.5
        billing_service.db.commit()
        
        result = billing_service._process_subscription_billing(sample_subscription)
        
        assert result['success'] is True
        assert result['amount'] > sample_subscription.amount  # Should include tax
    
    def test_billing_with_discounts(self, billing_service, sample_subscription):
        """Test billing with discounts."""
        # Add discount
        discount = Credit(
            customer_id=sample_subscription.customer_id,
            amount=5.00,
            currency='USD',
            credit_type='discount',
            description='Promotional discount',
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        billing_service.db.add(discount)
        billing_service.db.commit()
        
        result = billing_service._process_subscription_billing(sample_subscription)
        
        assert result['success'] is True
        assert result['amount'] < sample_subscription.amount  # Should be reduced by discount
    
    def test_billing_payment_failure(self, billing_service, sample_subscription):
        """Test billing with payment failure."""
        with patch.object(billing_service.payment_processor, 'process_payment') as mock_process:
            mock_process.return_value = {'paid': False, 'error': 'Card declined'}
            
            result = billing_service._process_subscription_billing(sample_subscription)
            
            assert result['success'] is False
            assert result['status'] == 'failed'
            assert 'error' in result
    
    def test_proration_calculation(self, billing_service, sample_subscription, sample_pricing_tiers):
        """Test proration calculation for subscription changes."""
        # Upgrade subscription mid-period
        days_remaining = (sample_subscription.current_period_end - datetime.now(timezone.utc)).days
        new_tier = sample_pricing_tiers[1]  # Mid-tier
        
        proration_amount = billing_service._calculate_proration_amount(
            subscription=sample_subscription,
            new_amount=new_tier.monthly_price,
            days_remaining=days_remaining
        )
        
        assert proration_amount > 0
        assert proration_amount < new_tier.monthly_price
    
    def test_billing_with_multiple_payment_methods(self, billing_service, sample_subscription):
        """Test billing with multiple payment methods."""
        # Add multiple payment methods
        payment_method1 = PaymentMethod(
            customer_id=sample_subscription.customer_id,
            stripe_payment_method_id='pm_test1',
            type='card',
            is_default=True
        )
        payment_method2 = PaymentMethod(
            customer_id=sample_subscription.customer_id,
            stripe_payment_method_id='pm_test2',
            type='card',
            is_default=False
        )
        billing_service.db.add_all([payment_method1, payment_method2])
        billing_service.db.commit()
        
        result = billing_service._process_subscription_billing(sample_subscription)
        
        assert result['success'] is True


class TestPaymentRecovery:
    """Test payment recovery scenarios."""
    
    def test_payment_failure_recovery(self, db_session, mock_config):
        """Test payment failure recovery process."""
        recovery_service = PaymentRecoveryService(db_session, mock_config)
        
        # Simulate payment failure
        failed_payment = {
            'subscription_id': 1,
            'amount': 15.00,
            'failure_reason': 'insufficient_funds',
            'attempt_count': 1
        }
        
        result = recovery_service.process_payment_failure(failed_payment)
        
        assert 'retry_scheduled' in result
        assert 'next_attempt' in result
    
    def test_dunning_management(self, db_session, mock_config):
        """Test dunning management for failed payments."""
        recovery_service = PaymentRecoveryService(db_session, mock_config)
        
        # Simulate multiple payment failures
        for attempt in range(1, 4):
            failed_payment = {
                'subscription_id': 1,
                'amount': 15.00,
                'failure_reason': 'card_declined',
                'attempt_count': attempt
            }
            
            result = recovery_service.process_payment_failure(failed_payment)
            
            if attempt == 3:
                assert result['stage'] == 'final_warning'
                assert result['action'] == 'suspend_service'
    
    def test_payment_method_update(self, db_session, mock_config):
        """Test payment method update during recovery."""
        recovery_service = PaymentRecoveryService(db_session, mock_config)
        
        result = recovery_service.update_payment_method(
            customer_id=1,
            new_payment_method_id='pm_new123'
        )
        
        assert result['success'] is True
        assert result['payment_method_updated'] is True
    
    def test_grace_period_management(self, db_session, mock_config):
        """Test grace period management."""
        recovery_service = PaymentRecoveryService(db_session, mock_config)
        
        result = recovery_service.manage_grace_period(
            subscription_id=1,
            grace_period_days=7
        )
        
        assert result['success'] is True
        assert result['grace_period_end'] is not None


class TestPaymentProcessing:
    """Test comprehensive payment processing scenarios."""
    
    # ============================================================================
    # SUCCESSFUL PAYMENT PROCESSING
    # ============================================================================
    
    def test_successful_payment_processing(self, payment_service, sample_subscription):
        """Test successful payment processing."""
        result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test123',
            description='Monthly subscription payment'
        )
        
        assert result['success'] is True
        assert result['payment_intent_id'] is not None
        assert result['status'] == 'succeeded'
        assert result['amount'] == 15.00
        assert result['currency'] == 'usd'
    
    def test_successful_payment_with_metadata(self, payment_service, sample_subscription):
        """Test successful payment processing with metadata."""
        metadata = {
            'subscription_id': sample_subscription.id,
            'billing_cycle': 'monthly',
            'tier': 'budget',
            'user_id': sample_subscription.user_id
        }
        
        result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test123',
            description='Monthly subscription payment',
            metadata=metadata
        )
        
        assert result['success'] is True
        assert result['metadata'] == metadata
        assert result['payment_intent_id'] is not None
    
    def test_successful_payment_with_receipt_email(self, payment_service, sample_subscription):
        """Test successful payment processing with receipt email."""
        result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test123',
            description='Monthly subscription payment',
            receipt_email='customer@example.com'
        )
        
        assert result['success'] is True
        assert result['receipt_email'] == 'customer@example.com'
        assert result['receipt_sent'] is True
    
    def test_successful_payment_with_statement_descriptor(self, payment_service, sample_subscription):
        """Test successful payment processing with custom statement descriptor."""
        result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test123',
            description='Monthly subscription payment',
            statement_descriptor='MINGUS SUBSCRIPTION'
        )
        
        assert result['success'] is True
        assert result['statement_descriptor'] == 'MINGUS SUBSCRIPTION'
    
    # ============================================================================
    # FAILED PAYMENT HANDLING AND RECOVERY
    # ============================================================================
    
    def test_payment_failure_insufficient_funds(self, payment_service, sample_subscription):
        """Test payment failure due to insufficient funds."""
        with patch('stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.CardError(
                "Your card was declined.", None, "insufficient_funds"
            )
            
            result = payment_service.process_payment(
                subscription_id=sample_subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test123',
                description='Monthly subscription payment'
            )
            
            assert result['success'] is False
            assert result['error_type'] == 'card_error'
            assert result['decline_code'] == 'insufficient_funds'
            assert 'insufficient funds' in result['error'].lower()
    
    def test_payment_failure_expired_card(self, payment_service, sample_subscription):
        """Test payment failure due to expired card."""
        with patch('stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.CardError(
                "Your card has expired.", None, "expired_card"
            )
            
            result = payment_service.process_payment(
                subscription_id=sample_subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test123',
                description='Monthly subscription payment'
            )
            
            assert result['success'] is False
            assert result['error_type'] == 'card_error'
            assert result['decline_code'] == 'expired_card'
            assert 'expired' in result['error'].lower()
    
    def test_payment_failure_invalid_cvc(self, payment_service, sample_subscription):
        """Test payment failure due to invalid CVC."""
        with patch('stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.CardError(
                "Your card's security code is incorrect.", None, "incorrect_cvc"
            )
            
            result = payment_service.process_payment(
                subscription_id=sample_subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test123',
                description='Monthly subscription payment'
            )
            
            assert result['success'] is False
            assert result['error_type'] == 'card_error'
            assert result['decline_code'] == 'incorrect_cvc'
            assert 'security code' in result['error'].lower()
    
    def test_payment_failure_processing_error(self, payment_service, sample_subscription):
        """Test payment failure due to processing error."""
        with patch('stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.CardError(
                "An error occurred while processing your card.", None, "processing_error"
            )
            
            result = payment_service.process_payment(
                subscription_id=sample_subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test123',
                description='Monthly subscription payment'
            )
            
            assert result['success'] is False
            assert result['error_type'] == 'card_error'
            assert result['decline_code'] == 'processing_error'
            assert 'processing' in result['error'].lower()
    
    def test_payment_failure_network_error(self, payment_service, sample_subscription):
        """Test payment failure due to network error."""
        with patch('stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.APIConnectionError("Network error")
            
            result = payment_service.process_payment(
                subscription_id=sample_subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test123',
                description='Monthly subscription payment'
            )
            
            assert result['success'] is False
            assert result['error_type'] == 'api_connection_error'
            assert 'network' in result['error'].lower()
    
    def test_payment_failure_authentication_required(self, payment_service, sample_subscription):
        """Test payment failure requiring authentication."""
        with patch('stripe.PaymentIntent.create') as mock_create:
            mock_create.side_effect = stripe.error.CardError(
                "Authentication required.", None, "authentication_required"
            )
            
            result = payment_service.process_payment(
                subscription_id=sample_subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test123',
                description='Monthly subscription payment'
            )
            
            assert result['success'] is False
            assert result['error_type'] == 'card_error'
            assert result['decline_code'] == 'authentication_required'
            assert result['requires_action'] is True
            assert result['action_type'] == 'authentication'
    
    # ============================================================================
    # REFUND AND CREDIT PROCESSING
    # ============================================================================
    
    def test_full_refund_processing(self, payment_service, sample_subscription):
        """Test full refund processing."""
        # First create a successful payment
        payment_result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test123',
            description='Monthly subscription payment'
        )
        
        # Then process full refund
        result = payment_service.process_refund(
            payment_intent_id=payment_result['payment_intent_id'],
            amount=15.00,
            reason='requested_by_customer'
        )
        
        assert result['success'] is True
        assert result['refund_id'] is not None
        assert result['amount'] == 15.00
        assert result['status'] == 'succeeded'
        assert result['reason'] == 'requested_by_customer'
    
    def test_partial_refund_processing(self, payment_service, sample_subscription):
        """Test partial refund processing."""
        # First create a successful payment
        payment_result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=35.00,
            currency='usd',
            payment_method_id='pm_test123',
            description='Monthly subscription payment'
        )
        
        # Then process partial refund
        result = payment_service.process_refund(
            payment_intent_id=payment_result['payment_intent_id'],
            amount=10.00,
            reason='duplicate'
        )
        
        assert result['success'] is True
        assert result['refund_id'] is not None
        assert result['amount'] == 10.00
        assert result['status'] == 'succeeded'
        assert result['reason'] == 'duplicate'
    
    def test_refund_with_metadata(self, payment_service, sample_subscription):
        """Test refund processing with metadata."""
        # First create a successful payment
        payment_result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test123',
            description='Monthly subscription payment'
        )
        
        metadata = {
            'refund_reason': 'customer_request',
            'processed_by': 'admin_user',
            'subscription_id': sample_subscription.id
        }
        
        # Then process refund with metadata
        result = payment_service.process_refund(
            payment_intent_id=payment_result['payment_intent_id'],
            amount=15.00,
            reason='requested_by_customer',
            metadata=metadata
        )
        
        assert result['success'] is True
        assert result['metadata'] == metadata
        assert result['refund_id'] is not None
    
    def test_refund_failure_insufficient_funds(self, payment_service, sample_subscription):
        """Test refund failure due to insufficient funds."""
        # First create a successful payment
        payment_result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test123',
            description='Monthly subscription payment'
        )
        
        # Try to refund more than the payment amount
        result = payment_service.process_refund(
            payment_intent_id=payment_result['payment_intent_id'],
            amount=20.00,  # More than the original payment
            reason='requested_by_customer'
        )
        
        assert result['success'] is False
        assert 'insufficient funds' in result['error'].lower()
    
    def test_credit_application(self, payment_service, sample_subscription):
        """Test credit application to customer account."""
        result = payment_service.apply_credit(
            customer_id=sample_subscription.customer_id,
            amount=25.00,
            currency='usd',
            reason='goodwill_credit',
            description='Customer service credit'
        )
        
        assert result['success'] is True
        assert result['credit_id'] is not None
        assert result['amount'] == 25.00
        assert result['balance'] == 25.00
        assert result['reason'] == 'goodwill_credit'
    
    def test_credit_usage_for_payment(self, payment_service, sample_subscription):
        """Test using credit balance for payment."""
        # First apply credit
        credit_result = payment_service.apply_credit(
            customer_id=sample_subscription.customer_id,
            amount=25.00,
            currency='usd',
            reason='goodwill_credit'
        )
        
        # Then use credit for payment
        result = payment_service.process_payment_with_credit(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            credit_amount=10.00,
            payment_method_id='pm_test123'
        )
        
        assert result['success'] is True
        assert result['credit_used'] == 10.00
        assert result['payment_amount'] == 5.00
        assert result['remaining_credit'] == 15.00
    
    # ============================================================================
    # TAX CALCULATION AND COMPLIANCE
    # ============================================================================
    
    def test_tax_calculation_us_resident(self, payment_service, sample_subscription):
        """Test tax calculation for US resident."""
        result = payment_service.calculate_tax(
            amount=15.00,
            currency='usd',
            country='US',
            state='CA',
            zip_code='90210',
            tax_exempt='none'
        )
        
        assert result['success'] is True
        assert result['subtotal'] == 15.00
        assert result['tax_amount'] > 0
        assert result['total_amount'] > 15.00
        assert result['tax_rate'] > 0
        assert result['tax_id'] is not None
    
    def test_tax_calculation_international(self, payment_service, sample_subscription):
        """Test tax calculation for international customer."""
        result = payment_service.calculate_tax(
            amount=15.00,
            currency='usd',
            country='CA',
            state='ON',
            zip_code='M5V 3A8',
            tax_exempt='none'
        )
        
        assert result['success'] is True
        assert result['subtotal'] == 15.00
        assert result['tax_amount'] >= 0  # May be 0 for some international locations
        assert result['total_amount'] >= 15.00
        assert result['tax_rate'] >= 0
        assert result['tax_id'] is not None
    
    def test_tax_exempt_customer(self, payment_service, sample_subscription):
        """Test tax calculation for tax-exempt customer."""
        result = payment_service.calculate_tax(
            amount=15.00,
            currency='usd',
            country='US',
            state='CA',
            zip_code='90210',
            tax_exempt='exempt',
            tax_id='12-3456789'
        )
        
        assert result['success'] is True
        assert result['subtotal'] == 15.00
        assert result['tax_amount'] == 0
        assert result['total_amount'] == 15.00
        assert result['tax_exempt'] is True
        assert result['tax_id'] == '12-3456789'
    
    def test_tax_calculation_with_discount(self, payment_service, sample_subscription):
        """Test tax calculation with discount applied."""
        result = payment_service.calculate_tax(
            amount=15.00,
            currency='usd',
            country='US',
            state='CA',
            zip_code='90210',
            tax_exempt='none',
            discount_amount=5.00
        )
        
        assert result['success'] is True
        assert result['subtotal'] == 15.00
        assert result['discount_amount'] == 5.00
        assert result['taxable_amount'] == 10.00
        assert result['tax_amount'] > 0
        assert result['total_amount'] > 10.00
    
    def test_tax_compliance_validation(self, payment_service, sample_subscription):
        """Test tax compliance validation."""
        result = payment_service.validate_tax_compliance(
            country='US',
            state='CA',
            tax_id='12-3456789',
            business_type='corporation'
        )
        
        assert result['success'] is True
        assert result['compliance_status'] == 'valid'
        assert result['tax_id_valid'] is True
        assert result['business_type_valid'] is True
    
    # ============================================================================
    # INTERNATIONAL PAYMENT SCENARIOS
    # ============================================================================
    
    def test_international_payment_processing(self, payment_service, sample_subscription):
        """Test international payment processing."""
        result = payment_service.process_international_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='eur',
            payment_method_id='pm_test123',
            country='DE',
            description='International subscription payment'
        )
        
        assert result['success'] is True
        assert result['currency'] == 'eur'
        assert result['exchange_rate'] is not None
        assert result['local_amount'] is not None
        assert result['payment_intent_id'] is not None
    
    def test_currency_conversion_handling(self, payment_service, sample_subscription):
        """Test currency conversion handling."""
        result = payment_service.process_currency_conversion(
            amount=15.00,
            from_currency='usd',
            to_currency='eur',
            exchange_rate=0.85
        )
        
        assert result['success'] is True
        assert result['original_amount'] == 15.00
        assert result['converted_amount'] == 12.75
        assert result['exchange_rate'] == 0.85
        assert result['conversion_fee'] >= 0
    
    def test_international_payment_method_validation(self, payment_service, sample_subscription):
        """Test international payment method validation."""
        result = payment_service.validate_international_payment_method(
            payment_method_id='pm_test123',
            country='DE',
            currency='eur'
        )
        
        assert result['success'] is True
        assert result['supported_country'] is True
        assert result['supported_currency'] is True
        assert result['payment_method_valid'] is True
    
    def test_international_tax_handling(self, payment_service, sample_subscription):
        """Test international tax handling."""
        result = payment_service.calculate_international_tax(
            amount=15.00,
            currency='eur',
            country='DE',
            tax_id='DE123456789'
        )
        
        assert result['success'] is True
        assert result['vat_amount'] >= 0
        assert result['vat_rate'] >= 0
        assert result['total_amount'] >= 15.00
        assert result['tax_id_valid'] is True
    
    def test_cross_border_payment_restrictions(self, payment_service, sample_subscription):
        """Test cross-border payment restrictions."""
        result = payment_service.check_cross_border_restrictions(
            from_country='US',
            to_country='CU',  # Cuba - restricted
            currency='usd'
        )
        
        assert result['success'] is False
        assert result['restricted'] is True
        assert result['restriction_reason'] == 'sanctions'
    
    # ============================================================================
    # PAYMENT METHOD VALIDATION AND SECURITY
    # ============================================================================
    
    def test_payment_method_security_validation(self, payment_service, sample_subscription):
        """Test payment method security validation."""
        result = payment_service.validate_payment_method_security(
            payment_method_id='pm_test123',
            customer_id=sample_subscription.customer_id,
            amount=15.00,
            currency='usd'
        )
        
        assert result['success'] is True
        assert result['fraud_score'] >= 0
        assert result['risk_level'] in ['low', 'medium', 'high']
        assert result['security_checks_passed'] is True
    
    def test_payment_method_3d_secure_validation(self, payment_service, sample_subscription):
        """Test 3D Secure validation for payment methods."""
        result = payment_service.validate_3d_secure(
            payment_method_id='pm_test123',
            amount=15.00,
            currency='usd',
            customer_id=sample_subscription.customer_id
        )
        
        assert result['success'] is True
        assert result['requires_3d_secure'] in [True, False]
        if result['requires_3d_secure']:
            assert result['authentication_url'] is not None
            assert result['payment_intent_id'] is not None
    
    def test_payment_method_fraud_detection(self, payment_service, sample_subscription):
        """Test fraud detection for payment methods."""
        result = payment_service.detect_payment_fraud(
            payment_method_id='pm_test123',
            customer_id=sample_subscription.customer_id,
            amount=15.00,
            currency='usd',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )
        
        assert result['success'] is True
        assert result['fraud_score'] >= 0
        assert result['risk_factors'] is not None
        assert result['recommended_action'] in ['allow', 'review', 'block']
    
    def test_payment_method_pci_compliance(self, payment_service, sample_subscription):
        """Test PCI compliance for payment methods."""
        result = payment_service.validate_pci_compliance(
            payment_method_id='pm_test123',
            customer_id=sample_subscription.customer_id
        )
        
        assert result['success'] is True
        assert result['pci_compliant'] is True
        assert result['encryption_level'] in ['tls1.2', 'tls1.3']
        assert result['tokenization_enabled'] is True
    
    def test_payment_method_velocity_checks(self, payment_service, sample_subscription):
        """Test velocity checks for payment methods."""
        result = payment_service.perform_velocity_checks(
            payment_method_id='pm_test123',
            customer_id=sample_subscription.customer_id,
            amount=15.00,
            currency='usd'
        )
        
        assert result['success'] is True
        assert result['velocity_score'] >= 0
        assert result['recent_transactions'] >= 0
        assert result['velocity_limit_exceeded'] in [True, False]
    
    def test_payment_method_geolocation_validation(self, payment_service, sample_subscription):
        """Test geolocation validation for payment methods."""
        result = payment_service.validate_payment_geolocation(
            payment_method_id='pm_test123',
            customer_id=sample_subscription.customer_id,
            ip_address='192.168.1.1',
            billing_address={
                'country': 'US',
                'state': 'CA',
                'city': 'Los Angeles',
                'zip_code': '90210'
            }
        )
        
        assert result['success'] is True
        assert result['location_match'] in [True, False]
        assert result['risk_score'] >= 0
        assert result['recommended_action'] in ['allow', 'review', 'block']


class TestWebhookHandling:
    """Test comprehensive webhook handling and integration scenarios."""
    
    # ============================================================================
    # STRIPE WEBHOOK PROCESSING RELIABILITY
    # ============================================================================
    
    def test_customer_created_webhook(self, webhook_manager, db_session):
        """Test customer.created webhook handling."""
        webhook_data = {
            'id': 'evt_test123',
            'type': 'customer.created',
            'data': {
                'object': {
                    'id': 'cus_test123',
                    'email': 'test@example.com',
                    'name': 'Test User',
                    'metadata': {
                        'mingus_user_id': '1'
                    }
                }
            }
        }
        
        result = webhook_manager.process_webhook(webhook_data)
        
        assert result['success'] is True
        assert result['event_type'] == 'customer.created'
    
    def test_subscription_updated_webhook(self, webhook_manager, db_session):
        """Test subscription.updated webhook handling."""
        webhook_data = {
            'id': 'evt_test124',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test123',
                    'status': 'active',
                    'current_period_start': int(datetime.now().timestamp()),
                    'current_period_end': int((datetime.now() + timedelta(days=30)).timestamp()),
                    'metadata': {
                        'mingus_customer_id': '1',
                        'mingus_pricing_tier_id': '1'
                    }
                }
            }
        }
        
        result = webhook_manager.process_webhook(webhook_data)
        
        assert result['success'] is True
        assert result['event_type'] == 'customer.subscription.updated'
    
    def test_invoice_payment_succeeded_webhook(self, webhook_manager, db_session):
        """Test invoice.payment_succeeded webhook handling."""
        webhook_data = {
            'id': 'evt_test125',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_test123',
                    'subscription': 'sub_test123',
                    'amount_paid': 1500,
                    'status': 'paid',
                    'customer': 'cus_test123'
                }
            }
        }
        
        result = webhook_manager.process_webhook(webhook_data)
        
        assert result['success'] is True
        assert result['event_type'] == 'invoice.payment_succeeded'
    
    def test_invoice_payment_failed_webhook(self, webhook_manager, db_session):
        """Test invoice.payment_failed webhook handling."""
        webhook_data = {
            'id': 'evt_test126',
            'type': 'invoice.payment_failed',
            'data': {
                'object': {
                    'id': 'in_test124',
                    'subscription': 'sub_test123',
                    'amount_due': 1500,
                    'status': 'open',
                    'customer': 'cus_test123',
                    'next_payment_attempt': int((datetime.now() + timedelta(days=3)).timestamp())
                }
            }
        }
        
        result = webhook_manager.process_webhook(webhook_data)
        
        assert result['success'] is True
        assert result['event_type'] == 'invoice.payment_failed'
    
    def test_invalid_webhook_signature(self, webhook_manager, db_session):
        """Test webhook with invalid signature."""
        webhook_data = {
            'id': 'evt_test127',
            'type': 'customer.created',
            'data': {'object': {}}
        }
        
        with patch.object(webhook_manager, '_verify_webhook_signature') as mock_verify:
            mock_verify.return_value = False
            
            result = webhook_manager.process_webhook(webhook_data)
            
            assert result['success'] is False
    
    def test_webhook_processing_reliability_retry(self, webhook_manager, db_session):
        """Test webhook processing reliability with retry mechanism."""
        webhook_data = {
            'id': 'evt_test128',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test124',
                    'status': 'active'
                }
            }
        }
        
        # Simulate temporary failure followed by success
        with patch.object(webhook_manager, '_process_subscription_update') as mock_process:
            mock_process.side_effect = [Exception("Temporary failure"), True]
            
            result = webhook_manager.process_webhook_with_retry(webhook_data, max_retries=3)
            
            assert result['success'] is True
            assert result['retry_count'] == 1
            assert result['final_attempt'] is True
    
    def test_webhook_processing_timeout_handling(self, webhook_manager, db_session):
        """Test webhook processing timeout handling."""
        webhook_data = {
            'id': 'evt_test129',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_test125',
                    'subscription': 'sub_test125'
                }
            }
        }
        
        # Simulate timeout scenario
        with patch.object(webhook_manager, '_process_payment_success') as mock_process:
            mock_process.side_effect = TimeoutError("Processing timeout")
            
            result = webhook_manager.process_webhook_with_timeout(webhook_data, timeout=5)
            
            assert result['success'] is False
            assert result['error_type'] == 'timeout'
            assert result['timeout_duration'] == 5
    
    def test_webhook_processing_concurrent_handling(self, webhook_manager, db_session):
        """Test concurrent webhook processing handling."""
        webhook_data_list = [
            {
                'id': f'evt_test_{i}',
                'type': 'customer.subscription.updated',
                'data': {'object': {'id': f'sub_test_{i}', 'status': 'active'}}
            }
            for i in range(10)
        ]
        
        # Process multiple webhooks concurrently
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def process_webhook(webhook_data):
            result = webhook_manager.process_webhook(webhook_data)
            results_queue.put(result)
        
        threads = [threading.Thread(target=process_webhook, args=(data,)) for data in webhook_data_list]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Verify all webhooks were processed successfully
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        assert len(results) == 10
        assert all(result['success'] for result in results)
    
    def test_webhook_processing_duplicate_handling(self, webhook_manager, db_session):
        """Test duplicate webhook handling."""
        webhook_data = {
            'id': 'evt_test130',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test126',
                    'status': 'active'
                }
            }
        }
        
        # Process the same webhook twice
        result1 = webhook_manager.process_webhook(webhook_data)
        result2 = webhook_manager.process_webhook(webhook_data)
        
        assert result1['success'] is True
        assert result2['success'] is True
        assert result2['duplicate_handled'] is True
        assert result2['idempotent_operation'] is True
    
    # ============================================================================
    # DATABASE SYNCHRONIZATION ACCURACY
    # ============================================================================
    
    def test_database_synchronization_subscription_update(self, webhook_manager, db_session):
        """Test database synchronization for subscription updates."""
        webhook_data = {
            'id': 'evt_test131',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test127',
                    'status': 'active',
                    'current_period_start': int(datetime.now().timestamp()),
                    'current_period_end': int((datetime.now() + timedelta(days=30)).timestamp()),
                    'metadata': {
                        'mingus_customer_id': '1',
                        'mingus_pricing_tier_id': '2'
                    }
                }
            }
        }
        
        # Process webhook and verify database sync
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify database was updated correctly
        subscription = db_session.query(Subscription).filter_by(stripe_subscription_id='sub_test127').first()
        
        assert result['success'] is True
        assert subscription is not None
        assert subscription.status == 'active'
        assert subscription.pricing_tier_id == 2
        assert subscription.current_period_start is not None
        assert subscription.current_period_end is not None
    
    def test_database_synchronization_payment_success(self, webhook_manager, db_session):
        """Test database synchronization for payment success."""
        webhook_data = {
            'id': 'evt_test132',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_test126',
                    'subscription': 'sub_test127',
                    'amount_paid': 2500,
                    'status': 'paid',
                    'customer': 'cus_test124',
                    'created': int(datetime.now().timestamp())
                }
            }
        }
        
        # Process webhook and verify database sync
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify payment record was created
        payment = db_session.query(Payment).filter_by(stripe_invoice_id='in_test126').first()
        
        assert result['success'] is True
        assert payment is not None
        assert payment.amount == 25.00
        assert payment.status == 'paid'
        assert payment.payment_date is not None
    
    def test_database_synchronization_payment_failure(self, webhook_manager, db_session):
        """Test database synchronization for payment failure."""
        webhook_data = {
            'id': 'evt_test133',
            'type': 'invoice.payment_failed',
            'data': {
                'object': {
                    'id': 'in_test127',
                    'subscription': 'sub_test127',
                    'amount_due': 2500,
                    'status': 'open',
                    'customer': 'cus_test124',
                    'next_payment_attempt': int((datetime.now() + timedelta(days=3)).timestamp())
                }
            }
        }
        
        # Process webhook and verify database sync
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify payment failure was recorded
        payment_failure = db_session.query(PaymentFailure).filter_by(stripe_invoice_id='in_test127').first()
        
        assert result['success'] is True
        assert payment_failure is not None
        assert payment_failure.amount_due == 25.00
        assert payment_failure.next_attempt_date is not None
    
    def test_database_synchronization_customer_creation(self, webhook_manager, db_session):
        """Test database synchronization for customer creation."""
        webhook_data = {
            'id': 'evt_test134',
            'type': 'customer.created',
            'data': {
                'object': {
                    'id': 'cus_test125',
                    'email': 'newcustomer@example.com',
                    'name': 'New Customer',
                    'metadata': {
                        'mingus_user_id': '2'
                    }
                }
            }
        }
        
        # Process webhook and verify database sync
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify customer was created in database
        customer = db_session.query(Customer).filter_by(stripe_customer_id='cus_test125').first()
        
        assert result['success'] is True
        assert customer is not None
        assert customer.email == 'newcustomer@example.com'
        assert customer.name == 'New Customer'
        assert customer.user_id == 2
    
    def test_database_synchronization_consistency_check(self, webhook_manager, db_session):
        """Test database synchronization consistency."""
        # Create test data
        customer = Customer(
            stripe_customer_id='cus_test126',
            email='consistency@example.com',
            name='Consistency Test',
            user_id=3
        )
        db_session.add(customer)
        db_session.commit()
        
        webhook_data = {
            'id': 'evt_test135',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test128',
                    'customer': 'cus_test126',
                    'status': 'active',
                    'metadata': {
                        'mingus_customer_id': '3',
                        'mingus_pricing_tier_id': '1'
                    }
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify consistency between Stripe and database
        subscription = db_session.query(Subscription).filter_by(stripe_subscription_id='sub_test128').first()
        customer = db_session.query(Customer).filter_by(stripe_customer_id='cus_test126').first()
        
        assert result['success'] is True
        assert subscription is not None
        assert subscription.customer_id == customer.id
        assert subscription.status == 'active'
        assert subscription.pricing_tier_id == 1
    
    def test_database_synchronization_rollback_handling(self, webhook_manager, db_session):
        """Test database synchronization rollback handling."""
        webhook_data = {
            'id': 'evt_test136',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test129',
                    'status': 'active',
                    'metadata': {
                        'mingus_customer_id': '999',  # Non-existent customer
                        'mingus_pricing_tier_id': '1'
                    }
                }
            }
        }
        
        # Process webhook that should fail
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify rollback occurred
        subscription = db_session.query(Subscription).filter_by(stripe_subscription_id='sub_test129').first()
        
        assert result['success'] is False
        assert subscription is None  # Should not exist due to rollback
        assert result['rollback_performed'] is True
        assert result['error_type'] == 'foreign_key_constraint'
    
    # ============================================================================
    # FEATURE ACCESS IMMEDIATE UPDATES
    # ============================================================================
    
    def test_feature_access_update_subscription_upgrade(self, webhook_manager, db_session, mock_config):
        """Test immediate feature access update on subscription upgrade."""
        from backend.services.feature_access_service import FeatureAccessService
        
        # Create test subscription
        subscription = Subscription(
            stripe_subscription_id='sub_test130',
            customer_id=1,
            pricing_tier_id=1,  # Budget tier
            status='active'
        )
        db_session.add(subscription)
        db_session.commit()
        
        webhook_data = {
            'id': 'evt_test137',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test130',
                    'status': 'active',
                    'metadata': {
                        'mingus_customer_id': '1',
                        'mingus_pricing_tier_id': '2'  # Upgrade to mid-tier
                    }
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify feature access was updated immediately
        feature_service = FeatureAccessService(db_session, mock_config)
        access_result = feature_service.check_feature_access(
            user_id=1,
            feature_name='bank_account_linking',
            tier_type='mid_tier'
        )
        
        assert result['success'] is True
        assert access_result['access_granted'] is True
        assert access_result['usage_limit'] == 5
        assert access_result['immediate_update'] is True
    
    def test_feature_access_update_subscription_downgrade(self, webhook_manager, db_session, mock_config):
        """Test immediate feature access update on subscription downgrade."""
        from backend.services.feature_access_service import FeatureAccessService
        
        # Create test subscription with higher tier
        subscription = Subscription(
            stripe_subscription_id='sub_test131',
            customer_id=1,
            pricing_tier_id=3,  # Professional tier
            status='active'
        )
        db_session.add(subscription)
        db_session.commit()
        
        webhook_data = {
            'id': 'evt_test138',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test131',
                    'status': 'active',
                    'metadata': {
                        'mingus_customer_id': '1',
                        'mingus_pricing_tier_id': '1'  # Downgrade to budget tier
                    }
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify feature access was updated immediately
        feature_service = FeatureAccessService(db_session, mock_config)
        access_result = feature_service.check_feature_access(
            user_id=1,
            feature_name='advanced_analytics',
            tier_type='budget'
        )
        
        assert result['success'] is True
        assert access_result['access_granted'] is False
        assert access_result['upgrade_required'] is True
        assert access_result['immediate_update'] is True
    
    def test_feature_access_update_payment_failure(self, webhook_manager, db_session, mock_config):
        """Test immediate feature access update on payment failure."""
        from backend.services.feature_access_service import FeatureAccessService
        
        # Create test subscription
        subscription = Subscription(
            stripe_subscription_id='sub_test132',
            customer_id=1,
            pricing_tier_id=2,
            status='active'
        )
        db_session.add(subscription)
        db_session.commit()
        
        webhook_data = {
            'id': 'evt_test139',
            'type': 'invoice.payment_failed',
            'data': {
                'object': {
                    'id': 'in_test128',
                    'subscription': 'sub_test132',
                    'amount_due': 1500,
                    'status': 'open',
                    'customer': 'cus_test127'
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify feature access was degraded immediately
        feature_service = FeatureAccessService(db_session, mock_config)
        access_result = feature_service.check_feature_access(
            user_id=1,
            feature_name='api_calls',
            tier_type='mid_tier'
        )
        
        assert result['success'] is True
        assert access_result['feature_degraded'] is True
        assert access_result['grace_period'] is True
        assert access_result['immediate_update'] is True
    
    def test_feature_access_update_payment_success(self, webhook_manager, db_session, mock_config):
        """Test immediate feature access update on payment success."""
        from backend.services.feature_access_service import FeatureAccessService
        
        # Create test subscription with payment failure
        subscription = Subscription(
            stripe_subscription_id='sub_test133',
            customer_id=1,
            pricing_tier_id=2,
            status='past_due'
        )
        db_session.add(subscription)
        db_session.commit()
        
        webhook_data = {
            'id': 'evt_test140',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_test129',
                    'subscription': 'sub_test133',
                    'amount_paid': 1500,
                    'status': 'paid',
                    'customer': 'cus_test128'
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify feature access was restored immediately
        feature_service = FeatureAccessService(db_session, mock_config)
        access_result = feature_service.check_feature_access(
            user_id=1,
            feature_name='api_calls',
            tier_type='mid_tier'
        )
        
        assert result['success'] is True
        assert access_result['feature_recovered'] is True
        assert access_result['full_access_restored'] is True
        assert access_result['immediate_update'] is True
    
    def test_feature_access_update_trial_expiration(self, webhook_manager, db_session, mock_config):
        """Test immediate feature access update on trial expiration."""
        from backend.services.feature_access_service import FeatureAccessService
        
        # Create test subscription in trial
        subscription = Subscription(
            stripe_subscription_id='sub_test134',
            customer_id=1,
            pricing_tier_id=1,
            status='trialing',
            trial_end=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        db_session.add(subscription)
        db_session.commit()
        
        webhook_data = {
            'id': 'evt_test141',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test134',
                    'status': 'incomplete',
                    'trial_end': int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify feature access was updated immediately
        feature_service = FeatureAccessService(db_session, mock_config)
        access_result = feature_service.check_feature_access(
            user_id=1,
            feature_name='all_features',
            tier_type='trial'
        )
        
        assert result['success'] is True
        assert access_result['trial_expired'] is True
        assert access_result['limited_functionality'] is True
        assert access_result['immediate_update'] is True
    
    # ============================================================================
    # USER NOTIFICATION TRIGGERS
    # ============================================================================
    
    def test_user_notification_subscription_upgrade(self, webhook_manager, db_session):
        """Test user notification trigger on subscription upgrade."""
        from backend.services.notification_service import NotificationService
        
        webhook_data = {
            'id': 'evt_test142',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test135',
                    'status': 'active',
                    'metadata': {
                        'mingus_customer_id': '1',
                        'mingus_pricing_tier_id': '3'  # Upgrade to professional
                    }
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify notification was sent
        notification_service = NotificationService(db_session)
        notifications = notification_service.get_user_notifications(user_id=1, limit=5)
        
        assert result['success'] is True
        assert len(notifications) > 0
        assert any(n['type'] == 'subscription_upgrade' for n in notifications)
        assert any(n['tier'] == 'professional' for n in notifications)
    
    def test_user_notification_payment_success(self, webhook_manager, db_session):
        """Test user notification trigger on payment success."""
        from backend.services.notification_service import NotificationService
        
        webhook_data = {
            'id': 'evt_test143',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_test130',
                    'subscription': 'sub_test135',
                    'amount_paid': 3000,
                    'status': 'paid',
                    'customer': 'cus_test129'
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify notification was sent
        notification_service = NotificationService(db_session)
        notifications = notification_service.get_user_notifications(user_id=1, limit=5)
        
        assert result['success'] is True
        assert len(notifications) > 0
        assert any(n['type'] == 'payment_success' for n in notifications)
        assert any(n['amount'] == 30.00 for n in notifications)
    
    def test_user_notification_payment_failure(self, webhook_manager, db_session):
        """Test user notification trigger on payment failure."""
        from backend.services.notification_service import NotificationService
        
        webhook_data = {
            'id': 'evt_test144',
            'type': 'invoice.payment_failed',
            'data': {
                'object': {
                    'id': 'in_test131',
                    'subscription': 'sub_test135',
                    'amount_due': 3000,
                    'status': 'open',
                    'customer': 'cus_test129',
                    'next_payment_attempt': int((datetime.now() + timedelta(days=3)).timestamp())
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify notification was sent
        notification_service = NotificationService(db_session)
        notifications = notification_service.get_user_notifications(user_id=1, limit=5)
        
        assert result['success'] is True
        assert len(notifications) > 0
        assert any(n['type'] == 'payment_failure' for n in notifications)
        assert any(n['next_attempt_date'] is not None for n in notifications)
    
    def test_user_notification_trial_ending(self, webhook_manager, db_session):
        """Test user notification trigger on trial ending."""
        from backend.services.notification_service import NotificationService
        
        webhook_data = {
            'id': 'evt_test145',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test136',
                    'status': 'trialing',
                    'trial_end': int((datetime.now(timezone.utc) + timedelta(days=3)).timestamp())
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify notification was sent
        notification_service = NotificationService(db_session)
        notifications = notification_service.get_user_notifications(user_id=1, limit=5)
        
        assert result['success'] is True
        assert len(notifications) > 0
        assert any(n['type'] == 'trial_ending' for n in notifications)
        assert any(n['days_remaining'] == 3 for n in notifications)
    
    def test_user_notification_subscription_cancellation(self, webhook_manager, db_session):
        """Test user notification trigger on subscription cancellation."""
        from backend.services.notification_service import NotificationService
        
        webhook_data = {
            'id': 'evt_test146',
            'type': 'customer.subscription.deleted',
            'data': {
                'object': {
                    'id': 'sub_test137',
                    'status': 'canceled',
                    'canceled_at': int(datetime.now().timestamp()),
                    'customer': 'cus_test130'
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify notification was sent
        notification_service = NotificationService(db_session)
        notifications = notification_service.get_user_notifications(user_id=1, limit=5)
        
        assert result['success'] is True
        assert len(notifications) > 0
        assert any(n['type'] == 'subscription_cancelled' for n in notifications)
        assert any(n['cancellation_date'] is not None for n in notifications)
    
    def test_user_notification_multiple_channels(self, webhook_manager, db_session):
        """Test user notification triggers across multiple channels."""
        from backend.services.notification_service import NotificationService
        
        webhook_data = {
            'id': 'evt_test147',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test138',
                    'status': 'active',
                    'metadata': {
                        'mingus_customer_id': '1',
                        'mingus_pricing_tier_id': '2'
                    }
                }
            }
        }
        
        # Process webhook
        result = webhook_manager.process_webhook(webhook_data)
        
        # Verify notifications across multiple channels
        notification_service = NotificationService(db_session)
        email_notifications = notification_service.get_notifications_by_channel(user_id=1, channel='email')
        push_notifications = notification_service.get_notifications_by_channel(user_id=1, channel='push')
        in_app_notifications = notification_service.get_notifications_by_channel(user_id=1, channel='in_app')
        
        assert result['success'] is True
        assert len(email_notifications) > 0
        assert len(push_notifications) > 0
        assert len(in_app_notifications) > 0
        assert all(n['delivered'] for n in email_notifications)
        assert all(n['delivered'] for n in push_notifications)
        assert all(n['delivered'] for n in in_app_notifications)
    
    # ============================================================================
    # ERROR HANDLING AND RECOVERY
    # ============================================================================
    
    def test_webhook_error_handling_database_failure(self, webhook_manager, db_session):
        """Test webhook error handling for database failures."""
        webhook_data = {
            'id': 'evt_test148',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test139',
                    'status': 'active'
                }
            }
        }
        
        # Simulate database connection failure
        with patch.object(db_session, 'commit') as mock_commit:
            mock_commit.side_effect = Exception("Database connection failed")
            
            result = webhook_manager.process_webhook(webhook_data)
            
            assert result['success'] is False
            assert result['error_type'] == 'database_error'
            assert result['retry_eligible'] is True
            assert result['error_message'] == 'Database connection failed'
    
    def test_webhook_error_handling_service_failure(self, webhook_manager, db_session):
        """Test webhook error handling for service failures."""
        webhook_data = {
            'id': 'evt_test149',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test140',
                    'status': 'active'
                }
            }
        }
        
        # Simulate service failure
        with patch.object(webhook_manager, '_process_subscription_update') as mock_process:
            mock_process.side_effect = Exception("Service unavailable")
            
            result = webhook_manager.process_webhook(webhook_data)
            
            assert result['success'] is False
            assert result['error_type'] == 'service_error'
            assert result['retry_eligible'] is True
            assert result['error_message'] == 'Service unavailable'
    
    def test_webhook_error_handling_validation_failure(self, webhook_manager, db_session):
        """Test webhook error handling for validation failures."""
        webhook_data = {
            'id': 'evt_test150',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test141',
                    'status': 'invalid_status'  # Invalid status
                }
            }
        }
        
        result = webhook_manager.process_webhook(webhook_data)
        
        assert result['success'] is False
        assert result['error_type'] == 'validation_error'
        assert result['retry_eligible'] is False  # Validation errors shouldn't be retried
        assert 'invalid_status' in result['error_message']
    
    def test_webhook_error_handling_malformed_data(self, webhook_manager, db_session):
        """Test webhook error handling for malformed data."""
        webhook_data = {
            'id': 'evt_test151',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    # Missing required fields
                }
            }
        }
        
        result = webhook_manager.process_webhook(webhook_data)
        
        assert result['success'] is False
        assert result['error_type'] == 'malformed_data'
        assert result['retry_eligible'] is False
        assert 'missing required fields' in result['error_message']
    
    def test_webhook_error_recovery_retry_success(self, webhook_manager, db_session):
        """Test webhook error recovery with successful retry."""
        webhook_data = {
            'id': 'evt_test152',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test142',
                    'status': 'active'
                }
            }
        }
        
        # Simulate failure followed by success
        with patch.object(webhook_manager, '_process_subscription_update') as mock_process:
            mock_process.side_effect = [Exception("Temporary failure"), True]
            
            result = webhook_manager.process_webhook_with_recovery(webhook_data, max_retries=3)
            
            assert result['success'] is True
            assert result['retry_count'] == 1
            assert result['recovery_successful'] is True
            assert result['final_attempt'] is True
    
    def test_webhook_error_recovery_max_retries_exceeded(self, webhook_manager, db_session):
        """Test webhook error recovery when max retries are exceeded."""
        webhook_data = {
            'id': 'evt_test153',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test143',
                    'status': 'active'
                }
            }
        }
        
        # Simulate persistent failure
        with patch.object(webhook_manager, '_process_subscription_update') as mock_process:
            mock_process.side_effect = Exception("Persistent failure")
            
            result = webhook_manager.process_webhook_with_recovery(webhook_data, max_retries=3)
            
            assert result['success'] is False
            assert result['retry_count'] == 3
            assert result['max_retries_exceeded'] is True
            assert result['final_error'] == 'Persistent failure'
    
    def test_webhook_error_recovery_graceful_degradation(self, webhook_manager, db_session):
        """Test webhook error recovery with graceful degradation."""
        webhook_data = {
            'id': 'evt_test154',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test144',
                    'status': 'active'
                }
            }
        }
        
        # Simulate partial failure with graceful degradation
        with patch.object(webhook_manager, '_process_subscription_update') as mock_process:
            mock_process.side_effect = Exception("Partial failure")
            
            result = webhook_manager.process_webhook_with_graceful_degradation(webhook_data)
            
            assert result['success'] is False
            assert result['graceful_degradation'] is True
            assert result['partial_processing'] is True
            assert result['critical_operations_completed'] is True
            assert result['non_critical_operations_failed'] is True
    
    def test_webhook_error_handling_alerting(self, webhook_manager, db_session):
        """Test webhook error handling with alerting."""
        webhook_data = {
            'id': 'evt_test155',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test145',
                    'status': 'active'
                }
            }
        }
        
        # Simulate critical error
        with patch.object(webhook_manager, '_process_subscription_update') as mock_process:
            mock_process.side_effect = Exception("Critical system error")
            
            result = webhook_manager.process_webhook_with_alerting(webhook_data)
            
            assert result['success'] is False
            assert result['alert_sent'] is True
            assert result['alert_severity'] == 'critical'
            assert result['alert_recipients'] is not None
            assert result['error_escalated'] is True
    
    def test_webhook_error_handling_audit_logging(self, webhook_manager, db_session):
        """Test webhook error handling with audit logging."""
        webhook_data = {
            'id': 'evt_test156',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test146',
                    'status': 'active'
                }
            }
        }
        
        # Simulate error
        with patch.object(webhook_manager, '_process_subscription_update') as mock_process:
            mock_process.side_effect = Exception("Processing error")
            
            result = webhook_manager.process_webhook_with_audit_logging(webhook_data)
            
            # Verify audit log was created
            audit_log = db_session.query(AuditLog).filter_by(
                event_type='webhook_error',
                event_id='evt_test156'
            ).first()
            
            assert result['success'] is False
            assert audit_log is not None
            assert audit_log.error_message == 'Processing error'
            assert audit_log.error_type == 'processing_error'
            assert audit_log.retry_eligible is True
            assert 'Invalid signature' in result['error']


class TestFeatureAccessControl:
    """Test comprehensive feature access control and usage tracking."""
    
    # ============================================================================
    # TIER-BASED FEATURE ACCESS CONTROL
    # ============================================================================
    
    def test_feature_access_budget_tier(self, db_session, mock_config):
        """Test feature access for budget tier."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test budget tier limits
        result = feature_service.check_feature_access(
            user_id=1,
            feature_name='ai_insights',
            tier_type='budget'
        )
        
        assert result['access_granted'] is False
        assert result['reason'] == 'feature_not_available'
    
    def test_feature_access_mid_tier(self, db_session, mock_config):
        """Test feature access for mid-tier."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test mid-tier limits
        result = feature_service.check_feature_access(
            user_id=1,
            feature_name='ai_insights',
            tier_type='mid_tier'
        )
        
        assert result['access_granted'] is True
        assert result['usage_limit'] == 50
    
    def test_feature_access_unlimited(self, db_session, mock_config):
        """Test feature access for professional tier (unlimited)."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        result = feature_service.check_feature_access(
            user_id=1,
            feature_name='ai_insights',
            tier_type='professional'
        )
        
        assert result['access_granted'] is True
        assert result['usage_limit'] == -1  # Unlimited
    
    def test_feature_access_tier_upgrade_required(self, db_session, mock_config):
        """Test feature access requiring tier upgrade."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test premium feature access for budget tier
        result = feature_service.check_feature_access(
            user_id=1,
            feature_name='advanced_analytics',
            tier_type='budget'
        )
        
        assert result['access_granted'] is False
        assert result['upgrade_required'] is True
        assert result['required_tier'] == 'professional'
        assert result['upgrade_message'] is not None
    
    def test_feature_access_tier_downgrade_impact(self, db_session, mock_config):
        """Test feature access impact of tier downgrade."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test feature access after downgrade
        result = feature_service.check_feature_access_after_downgrade(
            user_id=1,
            feature_name='advanced_analytics',
            from_tier='professional',
            to_tier='mid_tier'
        )
        
        assert result['access_granted'] is False
        assert result['downgrade_impact'] is True
        assert result['grace_period'] is not None
        assert result['data_preservation'] is True
    
    def test_feature_access_trial_limitations(self, db_session, mock_config):
        """Test feature access limitations during trial."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test trial feature access
        result = feature_service.check_feature_access(
            user_id=1,
            feature_name='bank_account_linking',
            tier_type='trial'
        )
        
        assert result['access_granted'] is True
        assert result['trial_limitation'] is True
        assert result['trial_days_remaining'] > 0
        assert result['upgrade_prompt'] is True
    
    def test_feature_access_feature_flags(self, db_session, mock_config):
        """Test feature access with feature flags."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test feature flag enabled
        result = feature_service.check_feature_access_with_flags(
            user_id=1,
            feature_name='beta_feature',
            tier_type='professional',
            feature_flags={'beta_feature': True}
        )
        
        assert result['access_granted'] is True
        assert result['feature_flag_enabled'] is True
        assert result['beta_access'] is True
    
    # ============================================================================
    # USAGE LIMIT ENFORCEMENT AND TRACKING
    # ============================================================================
    
    def test_usage_tracking(self, db_session, mock_config):
        """Test usage tracking functionality."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        result = usage_tracker.track_feature_usage(
            user_id=1,
            feature_name='api_calls',
            usage_quantity=1,
            subscription_id=1
        )
        
        assert result['success'] is True
        assert result['current_usage'] > 0
    
    def test_usage_limit_enforcement(self, db_session, mock_config):
        """Test usage limit enforcement."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        # Exceed usage limit
        for i in range(1001):  # Over 1000 limit for budget tier
            result = usage_tracker.track_feature_usage(
                user_id=1,
                feature_name='api_calls',
                usage_quantity=1,
                subscription_id=1
            )
            
            if i == 1000:
                assert result['success'] is False
                assert result['reason'] == 'usage_limit_exceeded'
    
    def test_usage_tracking_accuracy(self, db_session, mock_config):
        """Test usage tracking accuracy and consistency."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        # Track multiple usage events
        for i in range(5):
            result = usage_tracker.track_feature_usage(
                user_id=1,
                feature_name='api_calls',
                usage_quantity=1,
                subscription_id=1
            )
            assert result['success'] is True
        
        # Verify total usage
        total_usage = usage_tracker.get_total_usage(user_id=1, feature_name='api_calls')
        assert total_usage == 5
    
    def test_usage_reset_on_billing_cycle(self, db_session, mock_config):
        """Test usage reset on new billing cycle."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        # Set up usage in current cycle
        usage_tracker.track_feature_usage(user_id=1, feature_name='api_calls', usage_quantity=500, subscription_id=1)
        
        # Simulate billing cycle reset
        result = usage_tracker.reset_usage_on_billing_cycle(
            user_id=1,
            feature_name='api_calls',
            new_billing_cycle_start=datetime.now(timezone.utc)
        )
        
        assert result['success'] is True
        assert result['usage_reset'] is True
        assert result['new_usage'] == 0
    
    def test_usage_limit_warnings(self, db_session, mock_config):
        """Test usage limit warning thresholds."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        # Test warning at 80% usage
        result = usage_tracker.check_usage_warnings(
            user_id=1,
            feature_name='api_calls',
            current_usage=800,
            limit=1000
        )
        
        assert result['warning_threshold'] == 80
        assert result['warning_active'] is True
        assert result['warning_message'] is not None
    
    def test_usage_limit_hard_stop(self, db_session, mock_config):
        """Test hard stop when usage limit is exceeded."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        # Test hard stop at limit exceeded
        result = usage_tracker.enforce_usage_limit(
            user_id=1,
            feature_name='api_calls',
            current_usage=1001,
            limit=1000
        )
        
        assert result['access_blocked'] is True
        assert result['upgrade_required'] is True
        assert result['grace_period'] is False
    
    def test_usage_tracking_concurrent_access(self, db_session, mock_config):
        """Test usage tracking with concurrent access."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        # Simulate concurrent usage tracking
        import threading
        
        def track_usage():
            return usage_tracker.track_feature_usage(
                user_id=1,
                feature_name='api_calls',
                usage_quantity=1,
                subscription_id=1
            )
        
        threads = [threading.Thread(target=track_usage) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        # Verify total usage is accurate
        total_usage = usage_tracker.get_total_usage(user_id=1, feature_name='api_calls')
        assert total_usage == 10
    
    # ============================================================================
    # UPGRADE PROMPT TRIGGERS
    # ============================================================================
    
    def test_upgrade_prompt_feature_restriction(self, db_session, mock_config):
        """Test upgrade prompt when feature is restricted."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test upgrade prompt for restricted feature
        result = feature_service.trigger_upgrade_prompt(
            user_id=1,
            feature_name='advanced_analytics',
            current_tier='budget',
            reason='feature_restriction'
        )
        
        assert result['upgrade_prompt'] is True
        assert result['recommended_tier'] == 'professional'
        assert result['benefits'] is not None
        assert result['pricing_comparison'] is not None
    
    def test_upgrade_prompt_usage_limit_approaching(self, db_session, mock_config):
        """Test upgrade prompt when approaching usage limits."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        # Test upgrade prompt for approaching limit
        result = usage_tracker.trigger_upgrade_prompt(
            user_id=1,
            feature_name='api_calls',
            current_tier='mid_tier',
            reason='usage_limit_approaching',
            usage_percentage=85
        )
        
        assert result['upgrade_prompt'] is True
        assert result['usage_percentage'] == 85
        assert result['limit_warning'] is True
        assert result['recommended_tier'] == 'professional'
    
    def test_upgrade_prompt_usage_limit_exceeded(self, db_session, mock_config):
        """Test upgrade prompt when usage limit is exceeded."""
        usage_tracker = UsageTracker(db_session, mock_config)
        
        # Test upgrade prompt for exceeded limit
        result = usage_tracker.trigger_upgrade_prompt(
            user_id=1,
            feature_name='api_calls',
            current_tier='mid_tier',
            reason='usage_limit_exceeded',
            usage_percentage=105
        )
        
        assert result['upgrade_prompt'] is True
        assert result['usage_percentage'] == 105
        assert result['limit_exceeded'] is True
        assert result['urgent_upgrade'] is True
    
    def test_upgrade_prompt_trial_ending(self, db_session, mock_config):
        """Test upgrade prompt when trial is ending."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test upgrade prompt for trial ending
        result = feature_service.trigger_upgrade_prompt(
            user_id=1,
            feature_name='all_features',
            current_tier='trial',
            reason='trial_ending',
            days_remaining=3
        )
        
        assert result['upgrade_prompt'] is True
        assert result['trial_ending'] is True
        assert result['days_remaining'] == 3
        assert result['trial_benefits'] is not None
    
    def test_upgrade_prompt_competitor_feature(self, db_session, mock_config):
        """Test upgrade prompt for competitor feature comparison."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test upgrade prompt for competitor feature
        result = feature_service.trigger_upgrade_prompt(
            user_id=1,
            feature_name='advanced_analytics',
            current_tier='budget',
            reason='competitor_feature',
            competitor_name='CompetitorX'
        )
        
        assert result['upgrade_prompt'] is True
        assert result['competitor_comparison'] is True
        assert result['competitive_advantage'] is not None
        assert result['feature_showcase'] is not None
    
    def test_upgrade_prompt_frequency_control(self, db_session, mock_config):
        """Test upgrade prompt frequency control."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test upgrade prompt frequency limiting
        result = feature_service.check_upgrade_prompt_frequency(
            user_id=1,
            feature_name='advanced_analytics',
            current_tier='budget'
        )
        
        assert result['can_show_prompt'] in [True, False]
        assert result['last_prompt_date'] is not None
        assert result['prompt_cooldown'] is not None
    
    # ============================================================================
    # FEATURE DEGRADATION SCENARIOS
    # ============================================================================
    
    def test_feature_degradation_usage_limit(self, db_session, mock_config):
        """Test feature degradation when usage limit is reached."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test feature degradation
        result = feature_service.degrade_feature_access(
            user_id=1,
            feature_name='api_calls',
            reason='usage_limit_reached',
            current_usage=1000,
            limit=1000
        )
        
        assert result['feature_degraded'] is True
        assert result['degradation_reason'] == 'usage_limit_reached'
        assert result['reduced_functionality'] is True
        assert result['upgrade_prompt'] is True
    
    def test_feature_degradation_trial_expired(self, db_session, mock_config):
        """Test feature degradation when trial expires."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test trial expiration degradation
        result = feature_service.degrade_feature_access(
            user_id=1,
            feature_name='all_features',
            reason='trial_expired',
            trial_end_date=datetime.now(timezone.utc) - timedelta(days=1)
        )
        
        assert result['feature_degraded'] is True
        assert result['degradation_reason'] == 'trial_expired'
        assert result['trial_expired'] is True
        assert result['limited_functionality'] is True
    
    def test_feature_degradation_payment_failed(self, db_session, mock_config):
        """Test feature degradation when payment fails."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test payment failure degradation
        result = feature_service.degrade_feature_access(
            user_id=1,
            feature_name='all_features',
            reason='payment_failed',
            grace_period_days=7
        )
        
        assert result['feature_degraded'] is True
        assert result['degradation_reason'] == 'payment_failed'
        assert result['grace_period'] is True
        assert result['grace_period_days'] == 7
    
    def test_feature_degradation_tier_downgrade(self, db_session, mock_config):
        """Test feature degradation after tier downgrade."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test tier downgrade degradation
        result = feature_service.degrade_feature_access(
            user_id=1,
            feature_name='advanced_analytics',
            reason='tier_downgrade',
            from_tier='professional',
            to_tier='mid_tier'
        )
        
        assert result['feature_degraded'] is True
        assert result['degradation_reason'] == 'tier_downgrade'
        assert result['previous_tier'] == 'professional'
        assert result['current_tier'] == 'mid_tier'
        assert result['data_preservation'] is True
    
    def test_feature_degradation_grace_period(self, db_session, mock_config):
        """Test feature degradation with grace period."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test grace period degradation
        result = feature_service.degrade_feature_access(
            user_id=1,
            feature_name='api_calls',
            reason='usage_limit_exceeded',
            grace_period_days=3
        )
        
        assert result['feature_degraded'] is True
        assert result['grace_period'] is True
        assert result['grace_period_days'] == 3
        assert result['grace_period_end'] is not None
    
    def test_feature_degradation_recovery(self, db_session, mock_config):
        """Test feature degradation recovery."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test degradation recovery
        result = feature_service.recover_feature_access(
            user_id=1,
            feature_name='api_calls',
            recovery_reason='payment_processed'
        )
        
        assert result['feature_recovered'] is True
        assert result['recovery_reason'] == 'payment_processed'
        assert result['full_access_restored'] is True
        assert result['degradation_cleared'] is True
    
    def test_feature_degradation_data_handling(self, db_session, mock_config):
        """Test data handling during feature degradation."""
        feature_service = FeatureAccessService(db_session, mock_config)
        
        # Test data handling during degradation
        result = feature_service.handle_data_during_degradation(
            user_id=1,
            feature_name='advanced_analytics',
            degradation_reason='tier_downgrade'
        )
        
        assert result['data_preserved'] is True
        assert result['data_export_available'] is True
        assert result['data_retention_period'] is not None
        assert result['data_access_level'] == 'read_only'
    
    # ============================================================================
    # TEAM MEMBER ACCESS CONTROL (PROFESSIONAL TIER)
    # ============================================================================
    
    def test_team_member_invitation(self, db_session, mock_config):
        """Test team member invitation for professional tier."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test team member invitation
        result = team_service.invite_team_member(
            owner_user_id=1,
            invitee_email='team@example.com',
            role='analyst',
            permissions=['read_analytics', 'export_data']
        )
        
        assert result['success'] is True
        assert result['invitation_id'] is not None
        assert result['invitation_sent'] is True
        assert result['role'] == 'analyst'
        assert result['permissions'] == ['read_analytics', 'export_data']
    
    def test_team_member_acceptance(self, db_session, mock_config):
        """Test team member invitation acceptance."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test invitation acceptance
        result = team_service.accept_team_invitation(
            invitation_id='inv_test123',
            user_id=2,
            acceptance_token='token123'
        )
        
        assert result['success'] is True
        assert result['team_member_added'] is True
        assert result['access_granted'] is True
        assert result['role'] is not None
        assert result['permissions'] is not None
    
    def test_team_member_role_management(self, db_session, mock_config):
        """Test team member role and permission management."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test role update
        result = team_service.update_team_member_role(
            owner_user_id=1,
            member_user_id=2,
            new_role='admin',
            new_permissions=['full_access', 'manage_team']
        )
        
        assert result['success'] is True
        assert result['role_updated'] is True
        assert result['new_role'] == 'admin'
        assert result['new_permissions'] == ['full_access', 'manage_team']
    
    def test_team_member_removal(self, db_session, mock_config):
        """Test team member removal."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test team member removal
        result = team_service.remove_team_member(
            owner_user_id=1,
            member_user_id=2,
            reason='inactive_user'
        )
        
        assert result['success'] is True
        assert result['member_removed'] is True
        assert result['access_revoked'] is True
        assert result['data_handling'] == 'preserve_owner_data'
    
    def test_team_member_access_control(self, db_session, mock_config):
        """Test team member access control for features."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test feature access for team member
        result = team_service.check_team_member_access(
            owner_user_id=1,
            member_user_id=2,
            feature_name='advanced_analytics',
            action='read'
        )
        
        assert result['access_granted'] is True
        assert result['permission_level'] == 'read'
        assert result['feature_accessible'] is True
        assert result['team_owner_active'] is True
    
    def test_team_member_usage_tracking(self, db_session, mock_config):
        """Test usage tracking for team members."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test team usage tracking
        result = team_service.track_team_usage(
            owner_user_id=1,
            member_user_id=2,
            feature_name='api_calls',
            usage_amount=1
        )
        
        assert result['success'] is True
        assert result['team_usage_tracked'] is True
        assert result['individual_usage_tracked'] is True
        assert result['total_team_usage'] > 0
    
    def test_team_member_limit_enforcement(self, db_session, mock_config):
        """Test usage limit enforcement for team members."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test team usage limit
        result = team_service.check_team_usage_limit(
            owner_user_id=1,
            feature_name='api_calls',
            current_team_usage=5000,
            team_limit=5000
        )
        
        assert result['limit_reached'] is True
        assert result['team_limit_enforced'] is True
        assert result['upgrade_prompt'] is True
        assert result['recommended_action'] == 'upgrade_plan'
    
    def test_team_member_activity_monitoring(self, db_session, mock_config):
        """Test team member activity monitoring."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test activity monitoring
        result = team_service.monitor_team_activity(
            owner_user_id=1,
            member_user_id=2,
            activity_type='login',
            timestamp=datetime.now(timezone.utc)
        )
        
        assert result['success'] is True
        assert result['activity_logged'] is True
        assert result['last_activity'] is not None
        assert result['activity_summary'] is not None
    
    def test_team_member_data_isolation(self, db_session, mock_config):
        """Test data isolation between team members."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test data isolation
        result = team_service.ensure_data_isolation(
            owner_user_id=1,
            member_user_id=2,
            data_type='analytics',
            access_level='read_only'
        )
        
        assert result['success'] is True
        assert result['data_isolation_enforced'] is True
        assert result['access_level'] == 'read_only'
        assert result['data_scope'] == 'owner_data_only'
    
    def test_team_member_audit_logging(self, db_session, mock_config):
        """Test audit logging for team member actions."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test audit logging
        result = team_service.log_team_action(
            owner_user_id=1,
            member_user_id=2,
            action='data_export',
            resource='analytics_report',
            timestamp=datetime.now(timezone.utc)
        )
        
        assert result['success'] is True
        assert result['audit_logged'] is True
        assert result['audit_id'] is not None
        assert result['compliance_ready'] is True
    
    def test_team_member_permission_validation(self, db_session, mock_config):
        """Test permission validation for team members."""
        team_service = TeamAccessService(db_session, mock_config)
        
        # Test permission validation
        result = team_service.validate_team_permission(
            owner_user_id=1,
            member_user_id=2,
            required_permission='export_data',
            action='export_analytics'
        )
        
        assert result['permission_valid'] is True
        assert result['action_allowed'] is True
        assert result['permission_level'] == 'export_data'
        assert result['audit_required'] is True


class TestCustomerPortal:
    """Test customer portal functionality."""
    
    def test_customer_portal_session_creation(self, db_session, mock_config):
        """Test customer portal session creation."""
        portal_service = CustomerPortal(db_session, mock_config)
        
        result = portal_service.create_portal_session(
            customer_id=1,
            return_url='https://example.com/return'
        )
        
        assert result['success'] is True
        assert 'portal_url' in result
    
    def test_subscription_management_portal(self, db_session, mock_config):
        """Test subscription management through portal."""
        portal_service = CustomerPortal(db_session, mock_config)
        
        result = portal_service.get_subscription_management_options(
            customer_id=1
        )
        
        assert 'can_cancel' in result
        assert 'can_upgrade' in result
        assert 'can_downgrade' in result
        assert 'can_update_payment_method' in result
    
    def test_billing_history_portal(self, db_session, mock_config):
        """Test billing history access through portal."""
        portal_service = CustomerPortal(db_session, mock_config)
        
        result = portal_service.get_billing_history(
            customer_id=1,
            limit=10
        )
        
        assert 'invoices' in result
        assert 'has_more' in result


class TestRevenueOptimization:
    """Test revenue optimization features."""
    
    def test_churn_prediction(self, db_session, mock_config):
        """Test churn prediction functionality."""
        optimizer = RevenueOptimizer(db_session, mock_config)
        
        result = optimizer.predict_churn_risk(
            customer_id=1
        )
        
        assert 'churn_risk' in result
        assert 'risk_factors' in result
        assert 'recommendations' in result
    
    def test_upsell_opportunities(self, db_session, mock_config):
        """Test upsell opportunity identification."""
        optimizer = RevenueOptimizer(db_session, mock_config)
        
        result = optimizer.identify_upsell_opportunities(
            customer_id=1
        )
        
        assert 'opportunities' in result
        assert 'recommended_tier' in result
        assert 'potential_revenue_increase' in result
    
    def test_pricing_optimization(self, db_session, mock_config):
        """Test pricing optimization analysis."""
        optimizer = RevenueOptimizer(db_session, mock_config)
        
        result = optimizer.analyze_pricing_optimization()
        
        assert 'current_metrics' in result
        assert 'optimization_suggestions' in result
        assert 'projected_impact' in result


class TestAutomatedWorkflows:
    """Test automated workflow scenarios."""
    
    def test_welcome_workflow(self, db_session, mock_config):
        """Test welcome workflow for new subscribers."""
        workflow_manager = AutomatedWorkflowManager(db_session, mock_config)
        
        result = workflow_manager.trigger_welcome_workflow(
            customer_id=1,
            subscription_id=1
        )
        
        assert result['success'] is True
        assert 'emails_sent' in result
        assert 'onboarding_completed' in result
    
    def test_payment_failure_workflow(self, db_session, mock_config):
        """Test payment failure workflow."""
        workflow_manager = AutomatedWorkflowManager(db_session, mock_config)
        
        result = workflow_manager.trigger_payment_failure_workflow(
            customer_id=1,
            subscription_id=1,
            failure_reason='card_declined'
        )
        
        assert result['success'] is True
        assert 'retry_scheduled' in result
        assert 'notifications_sent' in result
    
    def test_trial_ending_workflow(self, db_session, mock_config):
        """Test trial ending workflow."""
        workflow_manager = AutomatedWorkflowManager(db_session, mock_config)
        
        result = workflow_manager.trigger_trial_ending_workflow(
            customer_id=1,
            subscription_id=1,
            days_remaining=3
        )
        
        assert result['success'] is True
        assert 'reminders_sent' in result
        assert 'conversion_attempts' in result


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_concurrent_subscription_creation(self, payment_service, sample_customer, sample_pricing_tiers):
        """Test concurrent subscription creation."""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_subscription():
            try:
                result = payment_service.create_subscription_with_payment(
                    user_id=sample_customer.user_id,
                    email=sample_customer.email,
                    name=sample_customer.name,
                    pricing_tier_id=sample_pricing_tiers[0].id,
                    payment_method_id='pm_test123',
                    billing_cycle='monthly'
                )
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_subscription)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have exactly one successful creation
        successful_results = [r for r in results if r['success']]
        assert len(successful_results) == 1
        assert len(errors) == 4  # Other attempts should fail
    
    def test_database_connection_failure(self, db_session, mock_config):
        """Test handling of database connection failures."""
        with patch.object(db_session, 'commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("Database connection lost")
            
            payment_service = PaymentService(db_session, mock_config)
            
            result = payment_service.create_subscription_with_payment(
                user_id=1,
                email='test@example.com',
                name='Test User',
                pricing_tier_id=1,
                payment_method_id='pm_test123'
            )
            
            assert result['success'] is False
            assert 'Database' in result['error']
    
    def test_stripe_api_failure(self, payment_service, sample_customer, sample_pricing_tiers):
        """Test handling of Stripe API failures."""
        with patch('stripe.Customer.create') as mock_create:
            mock_create.side_effect = stripe.error.APIConnectionError("Network error")
            
            result = payment_service.create_subscription_with_payment(
                user_id=sample_customer.user_id,
                email=sample_customer.email,
                name=sample_customer.name,
                pricing_tier_id=sample_pricing_tiers[0].id,
                payment_method_id='pm_test123'
            )
            
            assert result['success'] is False
            assert 'Network error' in result['error']
    
    def test_invalid_currency_handling(self, billing_service, sample_subscription):
        """Test handling of invalid currency scenarios."""
        # Set invalid currency
        sample_subscription.currency = 'INVALID'
        billing_service.db.commit()
        
        result = billing_service._process_subscription_billing(sample_subscription)
        
        assert result['success'] is False
        assert 'currency' in result['error'].lower()
    
    def test_negative_amount_handling(self, db_session, mock_config):
        """Test handling of negative amounts."""
        payment_service = PaymentService(db_session, mock_config)
        
        # Try to create subscription with negative amount
        with pytest.raises(ValueError):
            payment_service.create_subscription(
                customer_id=1,
                pricing_tier_id=1,
                billing_cycle='monthly',
                amount=-15.00  # Negative amount
            )
    
    def test_malformed_webhook_data(self, webhook_manager, db_session):
        """Test handling of malformed webhook data."""
        malformed_data = {
            'id': 'evt_test128',
            'type': 'customer.created',
            'data': None  # Missing object
        }
        
        result = webhook_manager.process_webhook(malformed_data)
        
        assert result['success'] is False
        assert 'malformed' in result['error'].lower()


class TestPerformanceAndLoad:
    """Test comprehensive performance and load scenarios."""
    
    # ============================================================================
    # HIGH-VOLUME SUBSCRIPTION PROCESSING
    # ============================================================================
    
    def test_bulk_subscription_processing(self, payment_service, db_session):
        """Test bulk subscription processing performance."""
        # Create test data
        customers = []
        for i in range(100):
            customer = Customer(
                stripe_customer_id=f'cus_bulk_{i}',
                email=f'bulk{i}@example.com',
                name=f'Bulk Customer {i}',
                user_id=i + 1
            )
            customers.append(customer)
        
        db_session.add_all(customers)
        db_session.commit()
        
        # Test bulk subscription creation
        start_time = time.time()
        results = []
        
        for customer in customers:
            result = payment_service.create_subscription(
                customer_id=customer.id,
                pricing_tier_id=1,
                payment_method_id='pm_test_bulk',
                billing_cycle='monthly'
            )
            results.append(result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance
        assert len(results) == 100
        assert all(result['success'] for result in results)
        assert processing_time < 30.0  # Should complete within 30 seconds
        assert processing_time / 100 < 0.3  # Average time per subscription < 300ms
    
    def test_high_volume_subscription_creation(self, payment_service, db_session):
        """Test high-volume subscription creation performance."""
        # Create test data for high volume
        customers = []
        for i in range(1000):
            customer = Customer(
                stripe_customer_id=f'cus_highvol_{i}',
                email=f'highvol{i}@example.com',
                name=f'High Volume Customer {i}',
                user_id=i + 1000
            )
            customers.append(customer)
        
        db_session.add_all(customers)
        db_session.commit()
        
        # Test high-volume subscription creation with batching
        start_time = time.time()
        batch_size = 50
        results = []
        
        for i in range(0, len(customers), batch_size):
            batch = customers[i:i + batch_size]
            batch_results = []
            
            for customer in batch:
                result = payment_service.create_subscription(
                    customer_id=customer.id,
                    pricing_tier_id=1,
                    payment_method_id='pm_test_highvol',
                    billing_cycle='monthly'
                )
                batch_results.append(result)
            
            results.extend(batch_results)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance
        assert len(results) == 1000
        assert all(result['success'] for result in results)
        assert processing_time < 120.0  # Should complete within 2 minutes
        assert processing_time / 1000 < 0.12  # Average time per subscription < 120ms
    
    def test_subscription_batch_processing(self, payment_service, db_session):
        """Test subscription batch processing performance."""
        # Create test data
        customers = []
        for i in range(500):
            customer = Customer(
                stripe_customer_id=f'cus_batch_{i}',
                email=f'batch{i}@example.com',
                name=f'Batch Customer {i}',
                user_id=i + 2000
            )
            customers.append(customer)
        
        db_session.add_all(customers)
        db_session.commit()
        
        # Test batch processing
        start_time = time.time()
        
        # Process in batches of 25
        batch_size = 25
        results = []
        
        for i in range(0, len(customers), batch_size):
            batch = customers[i:i + batch_size]
            
            # Process batch
            batch_start = time.time()
            batch_results = payment_service.create_subscriptions_batch(
                subscriptions_data=[
                    {
                        'customer_id': customer.id,
                        'pricing_tier_id': 1,
                        'payment_method_id': 'pm_test_batch',
                        'billing_cycle': 'monthly'
                    }
                    for customer in batch
                ]
            )
            batch_end = time.time()
            
            results.extend(batch_results)
            
            # Verify batch performance
            batch_time = batch_end - batch_start
            assert batch_time < 5.0  # Each batch should complete within 5 seconds
            assert batch_time / len(batch) < 0.2  # Average time per subscription in batch < 200ms
        
        end_time = time.time()
        total_processing_time = end_time - start_time
        
        # Verify overall performance
        assert len(results) == 500
        assert all(result['success'] for result in results)
        assert total_processing_time < 60.0  # Should complete within 1 minute
        assert total_processing_time / 500 < 0.12  # Average time per subscription < 120ms
    
    def test_subscription_processing_memory_usage(self, payment_service, db_session):
        """Test subscription processing memory usage."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create test data
        customers = []
        for i in range(200):
            customer = Customer(
                stripe_customer_id=f'cus_memory_{i}',
                email=f'memory{i}@example.com',
                name=f'Memory Customer {i}',
                user_id=i + 3000
            )
            customers.append(customer)
        
        db_session.add_all(customers)
        db_session.commit()
        
        # Process subscriptions
        results = []
        for customer in customers:
            result = payment_service.create_subscription(
                customer_id=customer.id,
                pricing_tier_id=1,
                payment_method_id='pm_test_memory',
                billing_cycle='monthly'
            )
            results.append(result)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Verify performance and memory usage
        assert len(results) == 200
        assert all(result['success'] for result in results)
        assert memory_increase < 100.0  # Memory increase should be less than 100MB
        assert memory_increase / 200 < 0.5  # Average memory per subscription < 0.5MB
    
    # ============================================================================
    # WEBHOOK PROCESSING UNDER LOAD
    # ============================================================================
    
    def test_concurrent_webhook_processing(self, webhook_manager, db_session):
        """Test concurrent webhook processing performance."""
        # Create test webhook data
        webhook_data_list = []
        for i in range(50):
            webhook_data = {
                'id': f'evt_concurrent_{i}',
                'type': 'customer.subscription.updated',
                'data': {
                    'object': {
                        'id': f'sub_concurrent_{i}',
                        'status': 'active'
                    }
                }
            }
            webhook_data_list.append(webhook_data)
        
        # Process webhooks concurrently
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def process_webhook(webhook_data):
            result = webhook_manager.process_webhook(webhook_data)
            results_queue.put(result)
        
        start_time = time.time()
        
        threads = [threading.Thread(target=process_webhook, args=(data,)) for data in webhook_data_list]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify performance
        assert len(results) == 50
        assert all(result['success'] for result in results)
        assert processing_time < 10.0  # Should complete within 10 seconds
        assert processing_time / 50 < 0.2  # Average time per webhook < 200ms
    
    def test_high_volume_webhook_processing(self, webhook_manager, db_session):
        """Test high-volume webhook processing performance."""
        # Create test webhook data for high volume
        webhook_data_list = []
        for i in range(1000):
            webhook_data = {
                'id': f'evt_highvol_{i}',
                'type': 'customer.subscription.updated',
                'data': {
                    'object': {
                        'id': f'sub_highvol_{i}',
                        'status': 'active',
                        'metadata': {
                            'mingus_customer_id': str(i),
                            'mingus_pricing_tier_id': '1'
                        }
                    }
                }
            }
            webhook_data_list.append(webhook_data)
        
        # Process webhooks with thread pool
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_webhook = {
                executor.submit(webhook_manager.process_webhook, webhook_data): webhook_data
                for webhook_data in webhook_data_list
            }
            
            for future in future_to_webhook:
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance
        assert len(results) == 1000
        assert all(result['success'] for result in results)
        assert processing_time < 60.0  # Should complete within 1 minute
        assert processing_time / 1000 < 0.06  # Average time per webhook < 60ms
    
    def test_webhook_processing_rate_limiting(self, webhook_manager, db_session):
        """Test webhook processing with rate limiting."""
        # Create test webhook data
        webhook_data_list = []
        for i in range(100):
            webhook_data = {
                'id': f'evt_ratelimit_{i}',
                'type': 'customer.subscription.updated',
                'data': {
                    'object': {
                        'id': f'sub_ratelimit_{i}',
                        'status': 'active'
                    }
                }
            }
            webhook_data_list.append(webhook_data)
        
        # Process webhooks with rate limiting (max 10 per second)
        import time
        import threading
        import queue
        
        results_queue = queue.Queue()
        rate_limit = 10  # webhooks per second
        delay = 1.0 / rate_limit
        
        def process_webhook_with_rate_limit(webhook_data):
            time.sleep(delay)  # Rate limiting
            result = webhook_manager.process_webhook(webhook_data)
            results_queue.put(result)
        
        start_time = time.time()
        
        threads = [threading.Thread(target=process_webhook_with_rate_limit, args=(data,)) for data in webhook_data_list]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify performance with rate limiting
        assert len(results) == 100
        assert all(result['success'] for result in results)
        assert processing_time >= 10.0  # Should take at least 10 seconds due to rate limiting
        assert processing_time <= 15.0  # Should not take more than 15 seconds
    
    def test_webhook_processing_queue_performance(self, webhook_manager, db_session):
        """Test webhook processing queue performance."""
        # Create test webhook data
        webhook_data_list = []
        for i in range(500):
            webhook_data = {
                'id': f'evt_queue_{i}',
                'type': 'customer.subscription.updated',
                'data': {
                    'object': {
                        'id': f'sub_queue_{i}',
                        'status': 'active'
                    }
                }
            }
            webhook_data_list.append(webhook_data)
        
        # Test queue-based processing
        from queue import Queue
        import threading
        
        webhook_queue = Queue()
        results_queue = Queue()
        
        # Add webhooks to queue
        for webhook_data in webhook_data_list:
            webhook_queue.put(webhook_data)
        
        # Worker function
        def webhook_worker():
            while True:
                try:
                    webhook_data = webhook_queue.get_nowait()
                    result = webhook_manager.process_webhook(webhook_data)
                    results_queue.put(result)
                    webhook_queue.task_done()
                except queue.Empty:
                    break
        
        # Start workers
        start_time = time.time()
        num_workers = 10
        workers = []
        
        for _ in range(num_workers):
            worker = threading.Thread(target=webhook_worker)
            worker.start()
            workers.append(worker)
        
        # Wait for all workers to complete
        for worker in workers:
            worker.join()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify performance
        assert len(results) == 500
        assert all(result['success'] for result in results)
        assert processing_time < 30.0  # Should complete within 30 seconds
        assert processing_time / 500 < 0.06  # Average time per webhook < 60ms
    
    # ============================================================================
    # DATABASE PERFORMANCE WITH SUBSCRIPTION QUERIES
    # ============================================================================
    
    def test_subscription_query_performance(self, db_session):
        """Test subscription query performance."""
        # Create test data
        customers = []
        subscriptions = []
        
        for i in range(1000):
            customer = Customer(
                stripe_customer_id=f'cus_query_{i}',
                email=f'query{i}@example.com',
                name=f'Query Customer {i}',
                user_id=i + 4000
            )
            customers.append(customer)
        
        db_session.add_all(customers)
        db_session.commit()
        
        for i, customer in enumerate(customers):
            subscription = Subscription(
                stripe_subscription_id=f'sub_query_{i}',
                customer_id=customer.id,
                pricing_tier_id=(i % 3) + 1,  # Distribute across tiers
                status='active' if i % 10 != 0 else 'canceled',
                created_at=datetime.now(timezone.utc) - timedelta(days=i % 365)
            )
            subscriptions.append(subscription)
        
        db_session.add_all(subscriptions)
        db_session.commit()
        
        # Test various query types
        start_time = time.time()
        
        # Query 1: Simple subscription lookup
        query1_start = time.time()
        active_subscriptions = db_session.query(Subscription).filter_by(status='active').all()
        query1_time = time.time() - query1_start
        
        # Query 2: Complex join query
        query2_start = time.time()
        subscription_details = db_session.query(
            Subscription, Customer
        ).join(Customer).filter(
            Subscription.status == 'active',
            Subscription.pricing_tier_id == 2
        ).all()
        query2_time = time.time() - query2_start
        
        # Query 3: Aggregation query
        query3_start = time.time()
        tier_counts = db_session.query(
            Subscription.pricing_tier_id,
            func.count(Subscription.id)
        ).group_by(Subscription.pricing_tier_id).all()
        query3_time = time.time() - query3_start
        
        # Query 4: Date range query
        query4_start = time.time()
        recent_subscriptions = db_session.query(Subscription).filter(
            Subscription.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).all()
        query4_time = time.time() - query4_start
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify performance
        assert len(active_subscriptions) > 900  # Most subscriptions should be active
        assert len(subscription_details) > 300  # Should have many tier 2 subscriptions
        assert len(tier_counts) == 3  # Should have 3 tiers
        assert len(recent_subscriptions) > 0  # Should have recent subscriptions
        
        # Performance assertions
        assert query1_time < 0.1  # Simple query should be fast
        assert query2_time < 0.2  # Join query should be reasonable
        assert query3_time < 0.1  # Aggregation should be fast
        assert query4_time < 0.1  # Date range query should be fast
        assert total_time < 1.0  # All queries should complete quickly
    
    def test_subscription_database_index_performance(self, db_session):
        """Test subscription database index performance."""
        # Create test data with various patterns
        customers = []
        subscriptions = []
        
        for i in range(2000):
            customer = Customer(
                stripe_customer_id=f'cus_index_{i}',
                email=f'index{i}@example.com',
                name=f'Index Customer {i}',
                user_id=i + 5000
            )
            customers.append(customer)
        
        db_session.add_all(customers)
        db_session.commit()
        
        for i, customer in enumerate(customers):
            subscription = Subscription(
                stripe_subscription_id=f'sub_index_{i}',
                customer_id=customer.id,
                pricing_tier_id=(i % 3) + 1,
                status='active' if i % 15 != 0 else 'canceled',
                created_at=datetime.now(timezone.utc) - timedelta(days=i % 730),
                current_period_start=datetime.now(timezone.utc) - timedelta(days=i % 30),
                current_period_end=datetime.now(timezone.utc) + timedelta(days=30 - (i % 30))
            )
            subscriptions.append(subscription)
        
        db_session.add_all(subscriptions)
        db_session.commit()
        
        # Test indexed vs non-indexed queries
        start_time = time.time()
        
        # Indexed query (should be fast)
        indexed_start = time.time()
        indexed_results = db_session.query(Subscription).filter(
            Subscription.stripe_subscription_id == 'sub_index_1000'
        ).all()
        indexed_time = time.time() - indexed_start
        
        # Non-indexed query (might be slower)
        non_indexed_start = time.time()
        non_indexed_results = db_session.query(Subscription).filter(
            Subscription.status == 'active'
        ).all()
        non_indexed_time = time.time() - non_indexed_start
        
        # Complex indexed query
        complex_start = time.time()
        complex_results = db_session.query(Subscription).filter(
            Subscription.status == 'active',
            Subscription.pricing_tier_id == 2,
            Subscription.created_at >= datetime.now(timezone.utc) - timedelta(days=90)
        ).all()
        complex_time = time.time() - complex_start
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify results
        assert len(indexed_results) == 1  # Should find exactly one subscription
        assert len(non_indexed_results) > 1800  # Most subscriptions should be active
        assert len(complex_results) > 600  # Should have many tier 2 subscriptions in last 90 days
        
        # Performance assertions
        assert indexed_time < 0.01  # Indexed lookup should be very fast
        assert non_indexed_time < 0.5  # Non-indexed query should be reasonable
        assert complex_time < 0.2  # Complex indexed query should be fast
        assert total_time < 1.0  # All queries should complete quickly
    
    def test_subscription_database_connection_pooling(self, db_session):
        """Test subscription database connection pooling performance."""
        # Create test data
        customers = []
        for i in range(100):
            customer = Customer(
                stripe_customer_id=f'cus_pool_{i}',
                email=f'pool{i}@example.com',
                name=f'Pool Customer {i}',
                user_id=i + 6000
            )
            customers.append(customer)
        
        db_session.add_all(customers)
        db_session.commit()
        
        # Test concurrent database operations
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def database_operation(customer_id):
            # Simulate database operation
            subscription = Subscription(
                stripe_subscription_id=f'sub_pool_{customer_id}',
                customer_id=customer_id,
                pricing_tier_id=1,
                status='active'
            )
            db_session.add(subscription)
            db_session.commit()
            
            # Query the subscription
            result = db_session.query(Subscription).filter_by(
                stripe_subscription_id=f'sub_pool_{customer_id}'
            ).first()
            
            results_queue.put(result is not None)
        
        start_time = time.time()
        
        threads = [threading.Thread(target=database_operation, args=(customer.id,)) for customer in customers]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify performance
        assert len(results) == 100
        assert all(results)  # All operations should succeed
        assert processing_time < 10.0  # Should complete within 10 seconds
        assert processing_time / 100 < 0.1  # Average time per operation < 100ms
    
    # ============================================================================
    # PAYMENT PROCESSING LATENCY TESTING
    # ============================================================================
    
    def test_payment_processing_latency(self, payment_service, sample_subscription):
        """Test payment processing latency."""
        # Test single payment processing latency
        start_time = time.time()
        
        result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test_latency',
            description='Latency test payment'
        )
        
        end_time = time.time()
        processing_latency = end_time - start_time
        
        # Verify performance
        assert result['success'] is True
        assert processing_latency < 2.0  # Payment should complete within 2 seconds
        assert processing_latency > 0.1  # Should take some time (not instant)
    
    def test_bulk_payment_processing_latency(self, payment_service, db_session):
        """Test bulk payment processing latency."""
        # Create test subscriptions
        subscriptions = []
        for i in range(100):
            customer = Customer(
                stripe_customer_id=f'cus_payment_{i}',
                email=f'payment{i}@example.com',
                name=f'Payment Customer {i}',
                user_id=i + 7000
            )
            db_session.add(customer)
            db_session.commit()
            
            subscription = Subscription(
                stripe_subscription_id=f'sub_payment_{i}',
                customer_id=customer.id,
                pricing_tier_id=1,
                status='active'
            )
            subscriptions.append(subscription)
        
        db_session.add_all(subscriptions)
        db_session.commit()
        
        # Test bulk payment processing
        start_time = time.time()
        results = []
        
        for subscription in subscriptions:
            result = payment_service.process_payment(
                subscription_id=subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test_bulk_payment',
                description='Bulk payment test'
            )
            results.append(result)
        
        end_time = time.time()
        total_processing_time = end_time - start_time
        
        # Verify performance
        assert len(results) == 100
        assert all(result['success'] for result in results)
        assert total_processing_time < 60.0  # Should complete within 1 minute
        assert total_processing_time / 100 < 0.6  # Average time per payment < 600ms
    
    def test_payment_processing_concurrent_latency(self, payment_service, db_session):
        """Test concurrent payment processing latency."""
        # Create test subscriptions
        subscriptions = []
        for i in range(50):
            customer = Customer(
                stripe_customer_id=f'cus_concurrent_payment_{i}',
                email=f'concurrent_payment{i}@example.com',
                name=f'Concurrent Payment Customer {i}',
                user_id=i + 8000
            )
            db_session.add(customer)
            db_session.commit()
            
            subscription = Subscription(
                stripe_subscription_id=f'sub_concurrent_payment_{i}',
                customer_id=customer.id,
                pricing_tier_id=1,
                status='active'
            )
            subscriptions.append(subscription)
        
        db_session.add_all(subscriptions)
        db_session.commit()
        
        # Test concurrent payment processing
        import threading
        import queue
        
        results_queue = queue.Queue()
        latency_queue = queue.Queue()
        
        def process_payment(subscription):
            start_time = time.time()
            
            result = payment_service.process_payment(
                subscription_id=subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test_concurrent_payment',
                description='Concurrent payment test'
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            results_queue.put(result)
            latency_queue.put(latency)
        
        overall_start_time = time.time()
        
        threads = [threading.Thread(target=process_payment, args=(subscription,)) for subscription in subscriptions]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        
        overall_end_time = time.time()
        total_processing_time = overall_end_time - overall_start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        latencies = []
        while not latency_queue.empty():
            latencies.append(latency_queue.get())
        
        # Calculate statistics
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        # Verify performance
        assert len(results) == 50
        assert all(result['success'] for result in results)
        assert total_processing_time < 30.0  # Should complete within 30 seconds
        assert avg_latency < 1.0  # Average latency should be less than 1 second
        assert max_latency < 3.0  # Maximum latency should be less than 3 seconds
        assert min_latency > 0.1  # Minimum latency should be reasonable
    
    def test_payment_processing_timeout_handling(self, payment_service, sample_subscription):
        """Test payment processing timeout handling."""
        # Test payment processing with timeout
        start_time = time.time()
        
        try:
            result = payment_service.process_payment_with_timeout(
                subscription_id=sample_subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test_timeout',
                description='Timeout test payment',
                timeout=1.0  # 1 second timeout
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Verify performance
            assert result['success'] is True
            assert processing_time < 1.5  # Should complete within timeout + buffer
            assert processing_time > 0.1  # Should take some time
            
        except TimeoutError:
            # Timeout is acceptable for this test
            end_time = time.time()
            processing_time = end_time - start_time
            assert processing_time >= 1.0  # Should timeout after 1 second
    
    def test_payment_processing_error_latency(self, payment_service, sample_subscription):
        """Test payment processing error latency."""
        # Test payment processing with invalid payment method (should fail quickly)
        start_time = time.time()
        
        result = payment_service.process_payment(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_invalid_method',
            description='Error latency test payment'
        )
        
        end_time = time.time()
        error_latency = end_time - start_time
        
        # Verify performance
        assert result['success'] is False  # Should fail
        assert error_latency < 1.0  # Error should be detected quickly
        assert error_latency > 0.05  # Should take some time to detect error
    
    def test_payment_processing_retry_latency(self, payment_service, sample_subscription):
        """Test payment processing retry latency."""
        # Test payment processing with retry mechanism
        start_time = time.time()
        
        result = payment_service.process_payment_with_retry(
            subscription_id=sample_subscription.id,
            amount=15.00,
            currency='usd',
            payment_method_id='pm_test_retry',
            description='Retry latency test payment',
            max_retries=3,
            retry_delay=0.1
        )
        
        end_time = time.time()
        retry_latency = end_time - start_time
        
        # Verify performance
        assert result['success'] is True
        assert retry_latency < 5.0  # Should complete within reasonable time
        assert retry_latency > 0.1  # Should take some time
    
    def test_payment_processing_memory_usage(self, payment_service, db_session):
        """Test payment processing memory usage."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create test subscriptions
        subscriptions = []
        for i in range(100):
            customer = Customer(
                stripe_customer_id=f'cus_memory_payment_{i}',
                email=f'memory_payment{i}@example.com',
                name=f'Memory Payment Customer {i}',
                user_id=i + 9000
            )
            db_session.add(customer)
            db_session.commit()
            
            subscription = Subscription(
                stripe_subscription_id=f'sub_memory_payment_{i}',
                customer_id=customer.id,
                pricing_tier_id=1,
                status='active'
            )
            subscriptions.append(subscription)
        
        db_session.add_all(subscriptions)
        db_session.commit()
        
        # Process payments
        results = []
        for subscription in subscriptions:
            result = payment_service.process_payment(
                subscription_id=subscription.id,
                amount=15.00,
                currency='usd',
                payment_method_id='pm_test_memory_payment',
                description='Memory usage test payment'
            )
            results.append(result)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Verify performance and memory usage
        assert len(results) == 100
        assert all(result['success'] for result in results)
        assert memory_increase < 50.0  # Memory increase should be less than 50MB
        assert memory_increase / 100 < 0.5  # Average memory per payment < 0.5MB


class TestSecurityAndCompliance:
    """Test security and compliance features."""
    
    def test_webhook_signature_verification(self, webhook_manager, db_session):
        """Test webhook signature verification."""
        webhook_data = {
            'id': 'evt_test129',
            'type': 'customer.created',
            'data': {'object': {}}
        }
        
        with patch.object(webhook_manager, '_verify_webhook_signature') as mock_verify:
            mock_verify.return_value = True
            
            result = webhook_manager.process_webhook(webhook_data)
            
            assert result['success'] is True
            mock_verify.assert_called_once()
    
    def test_payment_data_encryption(self, db_session, mock_config):
        """Test payment data encryption."""
        payment_service = PaymentService(db_session, mock_config)
        
        # Test that sensitive data is encrypted
        sensitive_data = {
            'card_number': '4242424242424242',
            'cvv': '123',
            'expiry': '12/25'
        }
        
        encrypted_data = payment_service._encrypt_sensitive_data(sensitive_data)
        
        assert encrypted_data != sensitive_data
        assert 'card_number' not in str(encrypted_data)
        assert 'cvv' not in str(encrypted_data)
    
    def test_audit_logging(self, db_session, mock_config):
        """Test audit logging functionality."""
        payment_service = PaymentService(db_session, mock_config)
        
        # Perform an action that should be audited
        payment_service.create_subscription_with_payment(
            user_id=1,
            email='test@example.com',
            name='Test User',
            pricing_tier_id=1,
            payment_method_id='pm_test123'
        )
        
        # Check that audit log was created
        audit_logs = db_session.query(AuditLog).filter(
            AuditLog.event_type == AuditEventType.SUBSCRIPTION_CREATED
        ).all()
        
        assert len(audit_logs) > 0
        assert audit_logs[0].severity == AuditSeverity.INFO
    
    def test_pci_compliance_validation(self, db_session, mock_config):
        """Test PCI compliance validation."""
        payment_service = PaymentService(db_session, mock_config)
        
        # Test PCI compliance checks
        result = payment_service.validate_pci_compliance()
        
        assert result['compliant'] is True
        assert 'validation_date' in result
        assert 'next_validation' in result


if __name__ == '__main__':
    # Run the test suite
    pytest.main([__file__, '-v', '--tb=short']) 