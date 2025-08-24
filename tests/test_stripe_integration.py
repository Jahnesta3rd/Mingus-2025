"""
MINGUS Application - Stripe Integration Tests
============================================

Tests for the Stripe integration functionality.

Author: MINGUS Development Team
Date: January 2025
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from backend.payment.stripe_integration import StripeService, SubscriptionTier
from backend.payment.payment_models import PaymentStatus, SubscriptionStatus


class TestStripeService:
    """Test cases for StripeService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock environment variables
        os.environ['STRIPE_SECRET_KEY'] = 'sk_test_mock_key'
        os.environ['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_mock_key'
        os.environ['STRIPE_WEBHOOK_SECRET'] = 'whsec_mock_secret'
        
        # Mock Stripe API
        self.stripe_patcher = patch('backend.payment.stripe_integration.stripe')
        self.mock_stripe = self.stripe_patcher.start()
        
        # Initialize service
        self.stripe_service = StripeService()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.stripe_patcher.stop()
    
    def test_init_with_api_key(self):
        """Test StripeService initialization with API key."""
        service = StripeService(api_key='test_key')
        assert service.api_key == 'test_key'
    
    def test_init_without_api_key(self):
        """Test StripeService initialization without API key."""
        with pytest.raises(ValueError, match="Stripe API key is required"):
            os.environ.pop('STRIPE_SECRET_KEY', None)
            StripeService()
    
    def test_get_publishable_key(self):
        """Test getting publishable key."""
        key = self.stripe_service.get_publishable_key()
        assert key == 'pk_test_mock_key'
    
    def test_get_publishable_key_missing(self):
        """Test getting publishable key when not configured."""
        self.stripe_service.publishable_key = None
        with pytest.raises(ValueError, match="Stripe publishable key not configured"):
            self.stripe_service.get_publishable_key()
    
    def test_create_customer_success(self):
        """Test successful customer creation."""
        # Mock Stripe customer response
        mock_customer = Mock()
        mock_customer.id = 'cus_test123'
        mock_customer.email = 'test@example.com'
        mock_customer.name = 'Test User'
        mock_customer.phone = '+1234567890'
        mock_customer.address = None
        mock_customer.created = 1640995200  # 2022-01-01 00:00:00 UTC
        mock_customer.metadata = {'user_id': 'test_uuid'}
        
        self.mock_stripe.Customer.create.return_value = mock_customer
        
        # Test customer creation
        customer = self.stripe_service.create_customer(
            email='test@example.com',
            name='Test User',
            phone='+1234567890',
            metadata={'user_id': 'test_uuid'}
        )
        
        # Verify customer creation
        assert customer.id == 'cus_test123'
        assert customer.email == 'test@example.com'
        assert customer.name == 'Test User'
        assert customer.phone == '+1234567890'
        assert customer.created_at == datetime(2022, 1, 1, tzinfo=timezone.utc)
        assert customer.metadata == {'user_id': 'test_uuid'}
        
        # Verify Stripe API call
        self.mock_stripe.Customer.create.assert_called_once()
    
    def test_create_customer_stripe_error(self):
        """Test customer creation with Stripe error."""
        self.mock_stripe.Customer.create.side_effect = Exception("Stripe error")
        
        with pytest.raises(Exception, match="Stripe error"):
            self.stripe_service.create_customer(email='test@example.com')
    
    def test_get_customer_success(self):
        """Test successful customer retrieval."""
        # Mock Stripe customer response
        mock_customer = Mock()
        mock_customer.id = 'cus_test123'
        mock_customer.email = 'test@example.com'
        mock_customer.name = 'Test User'
        mock_customer.phone = '+1234567890'
        mock_customer.address = None
        mock_customer.created = 1640995200
        mock_customer.metadata = {}
        
        self.mock_stripe.Customer.retrieve.return_value = mock_customer
        
        # Test customer retrieval
        customer = self.stripe_service.get_customer('cus_test123')
        
        # Verify customer retrieval
        assert customer.id == 'cus_test123'
        assert customer.email == 'test@example.com'
        
        # Verify Stripe API call
        self.mock_stripe.Customer.retrieve.assert_called_once_with('cus_test123')
    
    def test_create_payment_intent_success(self):
        """Test successful payment intent creation."""
        # Mock Stripe payment intent response
        mock_intent = Mock()
        mock_intent.id = 'pi_test123'
        mock_intent.amount = 1500
        mock_intent.currency = 'usd'
        mock_intent.status = 'requires_payment_method'
        mock_intent.client_secret = 'pi_test123_secret_abc'
        mock_intent.created = 1640995200
        mock_intent.metadata = {'user_id': 'test_uuid'}
        mock_intent.description = 'Test payment'
        mock_intent.receipt_email = None
        
        self.mock_stripe.PaymentIntent.create.return_value = mock_intent
        
        # Test payment intent creation
        payment_intent = self.stripe_service.create_payment_intent(
            amount=1500,
            currency='usd',
            customer_id='cus_test123',
            description='Test payment',
            metadata={'user_id': 'test_uuid'}
        )
        
        # Verify payment intent creation
        assert payment_intent.id == 'pi_test123'
        assert payment_intent.amount == 1500
        assert payment_intent.currency == 'usd'
        assert payment_intent.status == PaymentStatus.REQUIRES_PAYMENT_METHOD
        assert payment_intent.client_secret == 'pi_test123_secret_abc'
        assert payment_intent.description == 'Test payment'
        assert payment_intent.metadata == {'user_id': 'test_uuid'}
        
        # Verify Stripe API call
        self.mock_stripe.PaymentIntent.create.assert_called_once()
    
    def test_create_subscription_success(self):
        """Test successful subscription creation."""
        # Mock Stripe subscription response
        mock_subscription = Mock()
        mock_subscription.id = 'sub_test123'
        mock_subscription.customer = 'cus_test123'
        mock_subscription.status = 'active'
        mock_subscription.current_period_start = 1640995200
        mock_subscription.current_period_end = 1643673600
        mock_subscription.cancel_at_period_end = False
        mock_subscription.created = 1640995200
        mock_subscription.trial_start = None
        mock_subscription.trial_end = None
        mock_subscription.canceled_at = None
        mock_subscription.metadata = {'tier': 'budget'}
        
        self.mock_stripe.Subscription.create.return_value = mock_subscription
        
        # Test subscription creation
        subscription = self.stripe_service.create_subscription(
            customer_id='cus_test123',
            tier=SubscriptionTier.BUDGET,
            billing_cycle='monthly',
            trial_days=7,
            metadata={'tier': 'budget'}
        )
        
        # Verify subscription creation
        assert subscription.id == 'sub_test123'
        assert subscription.customer_id == 'cus_test123'
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.cancel_at_period_end is False
        assert subscription.metadata == {'tier': 'budget'}
        
        # Verify Stripe API call
        self.mock_stripe.Subscription.create.assert_called_once()
    
    def test_get_subscription_tier_info(self):
        """Test getting subscription tier information."""
        tier_info = self.stripe_service.get_subscription_tier_info(SubscriptionTier.BUDGET)
        
        assert tier_info.name == "Budget Tier"
        assert tier_info.price_monthly == 1500
        assert tier_info.price_yearly == 14400
        assert tier_info.features['basic_analytics'] is True
        assert tier_info.limits['analytics_reports_per_month'] == 5
    
    def test_get_all_tiers(self):
        """Test getting all subscription tiers."""
        tiers = self.stripe_service.get_all_tiers()
        
        assert len(tiers) == 3
        assert SubscriptionTier.BUDGET in tiers
        assert SubscriptionTier.MID_TIER in tiers
        assert SubscriptionTier.PROFESSIONAL in tiers
        
        # Verify tier details
        budget_tier = tiers[SubscriptionTier.BUDGET]
        assert budget_tier.name == "Budget Tier"
        assert budget_tier.price_monthly == 1500
        
        mid_tier = tiers[SubscriptionTier.MID_TIER]
        assert mid_tier.name == "Mid-Tier"
        assert mid_tier.price_monthly == 3500
        
        professional_tier = tiers[SubscriptionTier.PROFESSIONAL]
        assert professional_tier.name == "Professional Tier"
        assert professional_tier.price_monthly == 7500
    
    def test_subscription_tier_features(self):
        """Test subscription tier features and limits."""
        # Test Budget Tier
        budget_tier = self.stripe_service.get_subscription_tier_info(SubscriptionTier.BUDGET)
        assert budget_tier.features['basic_analytics'] is True
        assert budget_tier.features['advanced_ai_insights'] is False
        assert budget_tier.limits['analytics_reports_per_month'] == 5
        assert budget_tier.limits['goals_per_account'] == 3
        
        # Test Mid-Tier
        mid_tier = self.stripe_service.get_subscription_tier_info(SubscriptionTier.MID_TIER)
        assert mid_tier.features['basic_analytics'] is True
        assert mid_tier.features['advanced_ai_insights'] is True
        assert mid_tier.features['career_risk_management'] is True
        assert mid_tier.limits['analytics_reports_per_month'] == 20
        assert mid_tier.limits['ai_insights_per_month'] == 50
        
        # Test Professional Tier
        professional_tier = self.stripe_service.get_subscription_tier_info(SubscriptionTier.PROFESSIONAL)
        assert professional_tier.features['unlimited_access'] is True
        assert professional_tier.features['dedicated_account_manager'] is True
        assert professional_tier.features['team_management'] is True
        assert professional_tier.limits['analytics_reports_per_month'] == -1  # Unlimited
        assert professional_tier.limits['team_members'] == 10
    
    def test_subscription_tier_pricing(self):
        """Test subscription tier pricing."""
        # Test Budget Tier pricing
        budget_tier = self.stripe_service.get_subscription_tier_info(SubscriptionTier.BUDGET)
        assert budget_tier.price_monthly == 1500  # $15.00
        assert budget_tier.price_yearly == 14400  # $144.00 (20% discount)
        
        # Test Mid-Tier pricing
        mid_tier = self.stripe_service.get_subscription_tier_info(SubscriptionTier.MID_TIER)
        assert mid_tier.price_monthly == 3500  # $35.00
        assert mid_tier.price_yearly == 33600  # $336.00 (20% discount)
        
        # Test Professional Tier pricing
        professional_tier = self.stripe_service.get_subscription_tier_info(SubscriptionTier.PROFESSIONAL)
        assert professional_tier.price_monthly == 7500  # $75.00
        assert professional_tier.price_yearly == 72000  # $720.00 (20% discount)
    
    def test_handle_webhook_success(self):
        """Test successful webhook handling."""
        # Mock webhook event
        mock_event = {
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_test123',
                    'customer': 'cus_test123',
                    'status': 'active'
                }
            }
        }
        
        self.mock_stripe.Webhook.construct_event.return_value = mock_event
        
        # Test webhook handling
        payload = b'{"type": "customer.subscription.created"}'
        signature = 'whsec_test_signature'
        
        event = self.stripe_service.handle_webhook(payload, signature)
        
        # Verify webhook handling
        assert event == mock_event
        self.mock_stripe.Webhook.construct_event.assert_called_once_with(
            payload, signature, self.stripe_service.webhook_secret
        )
    
    def test_handle_webhook_missing_secret(self):
        """Test webhook handling without webhook secret."""
        self.stripe_service.webhook_secret = None
        
        payload = b'{"type": "customer.subscription.created"}'
        signature = 'whsec_test_signature'
        
        with pytest.raises(ValueError, match="Webhook secret not configured"):
            self.stripe_service.handle_webhook(payload, signature)
    
    def test_handle_webhook_signature_verification_failed(self):
        """Test webhook handling with signature verification failure."""
        self.mock_stripe.Webhook.construct_event.side_effect = Exception("Invalid signature")
        
        payload = b'{"type": "customer.subscription.created"}'
        signature = 'whsec_test_signature'
        
        with pytest.raises(Exception, match="Invalid signature"):
            self.stripe_service.handle_webhook(payload, signature)


class TestSubscriptionTier:
    """Test cases for SubscriptionTier enum."""
    
    def test_subscription_tier_values(self):
        """Test subscription tier enum values."""
        assert SubscriptionTier.BUDGET.value == "budget"
        assert SubscriptionTier.MID_TIER.value == "mid_tier"
        assert SubscriptionTier.PROFESSIONAL.value == "professional"
    
    def test_subscription_tier_from_string(self):
        """Test creating subscription tier from string."""
        assert SubscriptionTier("budget") == SubscriptionTier.BUDGET
        assert SubscriptionTier("mid_tier") == SubscriptionTier.MID_TIER
        assert SubscriptionTier("professional") == SubscriptionTier.PROFESSIONAL
    
    def test_subscription_tier_invalid_value(self):
        """Test creating subscription tier with invalid value."""
        with pytest.raises(ValueError):
            SubscriptionTier("invalid_tier")


class TestPaymentModels:
    """Test cases for payment models."""
    
    def test_payment_status_enum(self):
        """Test PaymentStatus enum values."""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.SUCCEEDED.value == "succeeded"
        assert PaymentStatus.FAILED.value == "failed"
    
    def test_subscription_status_enum(self):
        """Test SubscriptionStatus enum values."""
        assert SubscriptionStatus.ACTIVE.value == "active"
        assert SubscriptionStatus.CANCELED.value == "canceled"
        assert SubscriptionStatus.PAST_DUE.value == "past_due"
    
    def test_payment_error_to_dict(self):
        """Test PaymentError to_dict method."""
        from backend.payment.payment_models import PaymentError
        
        error = PaymentError(
            code="card_declined",
            message="Your card was declined",
            type="card_error",
            decline_code="insufficient_funds",
            param="number",
            request_id="req_test123",
            timestamp=datetime(2022, 1, 1, tzinfo=timezone.utc)
        )
        
        error_dict = error.to_dict()
        
        assert error_dict['code'] == "card_declined"
        assert error_dict['message'] == "Your card was declined"
        assert error_dict['type'] == "card_error"
        assert error_dict['decline_code'] == "insufficient_funds"
        assert error_dict['param'] == "number"
        assert error_dict['request_id'] == "req_test123"
        assert error_dict['timestamp'] == "2022-01-01T00:00:00+00:00"


if __name__ == '__main__':
    pytest.main([__file__]) 