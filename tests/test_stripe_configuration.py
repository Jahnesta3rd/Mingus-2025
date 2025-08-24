"""
MINGUS Application - Stripe Configuration Tests
==============================================

Tests for the Stripe configuration system.

Author: MINGUS Development Team
Date: January 2025
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from backend.config.stripe import (
    StripeConfig, StripeErrorHandler, StripeWebhookConfig,
    get_stripe_config, get_stripe_error_handler, get_stripe_webhook_config,
    validate_stripe_environment, get_stripe_environment_info
)


class TestStripeConfig:
    """Test cases for StripeConfig."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear any existing environment variables
        self.original_env = os.environ.copy()
        
        # Test environment variables
        os.environ['STRIPE_ENVIRONMENT'] = 'test'
        os.environ['STRIPE_TEST_SECRET_KEY'] = 'sk_test_test_key'
        os.environ['STRIPE_TEST_PUBLISHABLE_KEY'] = 'pk_test_test_key'
        os.environ['STRIPE_TEST_WEBHOOK_SECRET'] = 'whsec_test_secret'
        os.environ['STRIPE_TEST_WEBHOOK_ENDPOINT'] = 'https://test.example.com/webhook'
        os.environ['STRIPE_TEST_BUDGET_MONTHLY_PRICE_ID'] = 'price_test_budget_monthly'
        os.environ['STRIPE_TEST_BUDGET_YEARLY_PRICE_ID'] = 'price_test_budget_yearly'
        os.environ['STRIPE_TEST_MID_TIER_MONTHLY_PRICE_ID'] = 'price_test_mid_monthly'
        os.environ['STRIPE_TEST_MID_TIER_YEARLY_PRICE_ID'] = 'price_test_mid_yearly'
        os.environ['STRIPE_TEST_PROFESSIONAL_MONTHLY_PRICE_ID'] = 'price_test_pro_monthly'
        os.environ['STRIPE_TEST_PROFESSIONAL_YEARLY_PRICE_ID'] = 'price_test_pro_yearly'
        os.environ['STRIPE_TEST_CURRENCY'] = 'usd'
        os.environ['STRIPE_TEST_TRIAL_DAYS'] = '7'
        os.environ['STRIPE_TEST_GRACE_PERIOD_DAYS'] = '3'
        os.environ['STRIPE_TEST_LOG_LEVEL'] = 'DEBUG'
        os.environ['STRIPE_TEST_DEBUG'] = 'true'
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_test_environment_config(self):
        """Test test environment configuration loading."""
        config = StripeConfig('test')
        
        assert config.environment == 'test'
        assert config.is_test_mode is True
        assert config.is_live_mode is False
        assert config.api_key == 'sk_test_test_key'
        assert config.publishable_key == 'pk_test_test_key'
        assert config.webhook_secret == 'whsec_test_secret'
        assert config.webhook_endpoint == 'https://test.example.com/webhook'
        assert config.currency == 'usd'
        assert config.trial_days == 7
        assert config.grace_period_days == 3
        assert config.log_level == 'DEBUG'
        assert config.enable_debug is True
    
    def test_live_environment_config(self):
        """Test live environment configuration loading."""
        # Set up live environment variables
        os.environ['STRIPE_ENVIRONMENT'] = 'live'
        os.environ['STRIPE_LIVE_SECRET_KEY'] = 'sk_live_live_key'
        os.environ['STRIPE_LIVE_PUBLISHABLE_KEY'] = 'pk_live_live_key'
        os.environ['STRIPE_LIVE_WEBHOOK_SECRET'] = 'whsec_live_secret'
        os.environ['STRIPE_LIVE_WEBHOOK_ENDPOINT'] = 'https://live.example.com/webhook'
        os.environ['STRIPE_LIVE_BUDGET_MONTHLY_PRICE_ID'] = 'price_live_budget_monthly'
        os.environ['STRIPE_LIVE_CURRENCY'] = 'usd'
        os.environ['STRIPE_LIVE_TRIAL_DAYS'] = '7'
        os.environ['STRIPE_LIVE_GRACE_PERIOD_DAYS'] = '3'
        os.environ['STRIPE_LIVE_LOG_LEVEL'] = 'INFO'
        os.environ['STRIPE_LIVE_DEBUG'] = 'false'
        
        config = StripeConfig('live')
        
        assert config.environment == 'live'
        assert config.is_test_mode is False
        assert config.is_live_mode is True
        assert config.api_key == 'sk_live_live_key'
        assert config.publishable_key == 'pk_live_live_key'
        assert config.webhook_secret == 'whsec_live_secret'
        assert config.webhook_endpoint == 'https://live.example.com/webhook'
        assert config.currency == 'usd'
        assert config.trial_days == 7
        assert config.grace_period_days == 3
        assert config.log_level == 'INFO'
        assert config.enable_debug is False
    
    def test_invalid_environment(self):
        """Test invalid environment configuration."""
        with pytest.raises(ValueError, match="Environment must be 'test' or 'live'"):
            StripeConfig('invalid')
    
    def test_default_environment(self):
        """Test default environment configuration."""
        # Remove STRIPE_ENVIRONMENT to test default
        os.environ.pop('STRIPE_ENVIRONMENT', None)
        
        config = StripeConfig()
        
        assert config.environment == 'test'
        assert config.is_test_mode is True
    
    def test_is_configured_property(self):
        """Test is_configured property."""
        config = StripeConfig('test')
        
        # Should be configured with all required keys
        assert config.is_configured is True
        
        # Remove required key
        config.api_key = None
        assert config.is_configured is False
    
    def test_missing_configuration_property(self):
        """Test missing_configuration property."""
        config = StripeConfig('test')
        
        # Should have no missing configuration
        assert config.missing_configuration == []
        
        # Remove required keys
        config.api_key = None
        config.publishable_key = None
        
        missing = config.missing_configuration
        assert 'STRIPE_TEST_SECRET_KEY' in missing
        assert 'STRIPE_TEST_PUBLISHABLE_KEY' in missing
        assert len(missing) == 2
    
    def test_get_price_id(self):
        """Test get_price_id method."""
        config = StripeConfig('test')
        
        # Test existing price IDs
        assert config.get_price_id('budget', 'monthly') == 'price_test_budget_monthly'
        assert config.get_price_id('budget', 'yearly') == 'price_test_budget_yearly'
        assert config.get_price_id('mid_tier', 'monthly') == 'price_test_mid_monthly'
        assert config.get_price_id('professional', 'yearly') == 'price_test_pro_yearly'
        
        # Test non-existent price ID
        assert config.get_price_id('invalid', 'monthly') is None
    
    def test_validate_configuration(self):
        """Test validate_configuration method."""
        config = StripeConfig('test')
        
        validation = config.validate_configuration()
        
        assert validation['environment'] == 'test'
        assert validation['is_configured'] is True
        assert validation['missing_configuration'] == []
        assert 'budget_monthly' in validation['price_ids_configured']
        assert validation['price_ids_configured']['budget_monthly'] is True
        assert validation['warnings'] == []
    
    def test_validate_configuration_with_missing_items(self):
        """Test validate_configuration with missing items."""
        config = StripeConfig('test')
        
        # Remove some price IDs
        config.price_ids['budget_monthly'] = None
        config.webhook_endpoint = 'https://your-test-domain.com/api/payment/webhooks/stripe'
        
        validation = config.validate_configuration()
        
        assert validation['is_configured'] is True
        assert validation['price_ids_configured']['budget_monthly'] is False
        assert 'Missing price ID for budget monthly plan' in validation['warnings']
        assert 'Webhook endpoint not properly configured' in validation['warnings']
    
    def test_to_dict(self):
        """Test to_dict method."""
        config = StripeConfig('test')
        
        config_dict = config.to_dict()
        
        assert config_dict['environment'] == 'test'
        assert config_dict['is_test_mode'] is True
        assert config_dict['is_live_mode'] is False
        assert config_dict['currency'] == 'usd'
        assert config_dict['trial_days'] == 7
        assert config_dict['grace_period_days'] == 3
        assert config_dict['log_level'] == 'DEBUG'
        assert config_dict['enable_debug'] is True
        assert config_dict['webhook_endpoint'] == 'https://test.example.com/webhook'
        assert config_dict['is_configured'] is True
        assert config_dict['missing_configuration'] == []
        
        # Check that sensitive data is not included
        assert 'api_key' not in config_dict
        assert 'webhook_secret' not in config_dict


class TestStripeErrorHandler:
    """Test cases for StripeErrorHandler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = StripeConfig('test')
        self.error_handler = StripeErrorHandler(self.config)
    
    def test_init(self):
        """Test error handler initialization."""
        assert self.error_handler.config == self.config
        assert self.error_handler.logger is not None
    
    def test_log_error(self):
        """Test error logging."""
        error = Exception("Test error")
        context = {'operation': 'test', 'user_id': '123'}
        
        # Should not raise an exception
        self.error_handler.log_error(error, context)
    
    def test_log_payment_event(self):
        """Test payment event logging."""
        event_type = 'payment_intent.succeeded'
        event_data = {
            'id': 'pi_test_123',
            'amount': 1500,
            'currency': 'usd',
            'status': 'succeeded',
            'customer': 'cus_test_123',
            'created': 1640995200
        }
        
        # Should not raise an exception
        self.error_handler.log_payment_event(event_type, event_data)
    
    def test_log_subscription_event(self):
        """Test subscription event logging."""
        event_type = 'customer.subscription.created'
        subscription_data = {
            'id': 'sub_test_123',
            'customer': 'cus_test_123',
            'status': 'active',
            'current_period_start': 1640995200,
            'current_period_end': 1643673600,
            'cancel_at_period_end': False
        }
        
        # Should not raise an exception
        self.error_handler.log_subscription_event(event_type, subscription_data)


class TestStripeWebhookConfig:
    """Test cases for StripeWebhookConfig."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = StripeConfig('test')
        self.webhook_config = StripeWebhookConfig(self.config)
    
    def test_init(self):
        """Test webhook config initialization."""
        assert self.webhook_config.config == self.config
        assert len(self.webhook_config.supported_events) > 0
        assert 'customer.subscription.created' in self.webhook_config.supported_events
        assert 'invoice.payment_succeeded' in self.webhook_config.supported_events
    
    def test_is_supported_event(self):
        """Test supported event checking."""
        assert self.webhook_config.is_supported_event('customer.subscription.created') is True
        assert self.webhook_config.is_supported_event('invoice.payment_succeeded') is True
        assert self.webhook_config.is_supported_event('unsupported.event') is False
    
    def test_get_webhook_url(self):
        """Test webhook URL retrieval."""
        url = self.webhook_config.get_webhook_url()
        assert url == 'https://test.example.com/webhook'
    
    @patch('backend.config.stripe.stripe')
    def test_validate_webhook_signature_success(self, mock_stripe):
        """Test successful webhook signature validation."""
        payload = b'{"type": "test.event", "data": {"object": {}}}'
        signature = 'whsec_test_signature'
        
        # Mock successful validation
        mock_stripe.Webhook.construct_event.return_value = {'type': 'test.event'}
        
        result = self.webhook_config.validate_webhook_signature(payload, signature)
        assert result is True
    
    @patch('backend.config.stripe.stripe')
    def test_validate_webhook_signature_failure(self, mock_stripe):
        """Test failed webhook signature validation."""
        payload = b'{"type": "test.event", "data": {"object": {}}}'
        signature = 'invalid_signature'
        
        # Mock failed validation
        mock_stripe.Webhook.construct_event.side_effect = Exception("Invalid signature")
        
        result = self.webhook_config.validate_webhook_signature(payload, signature)
        assert result is False


class TestGlobalFunctions:
    """Test cases for global configuration functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Clear global instances
        import backend.config.stripe as stripe_config_module
        stripe_config_module.stripe_config = None
        stripe_config_module.stripe_error_handler = None
        stripe_config_module.stripe_webhook_config = None
        
        # Set up test environment
        os.environ['STRIPE_ENVIRONMENT'] = 'test'
        os.environ['STRIPE_TEST_SECRET_KEY'] = 'sk_test_test_key'
        os.environ['STRIPE_TEST_PUBLISHABLE_KEY'] = 'pk_test_test_key'
        os.environ['STRIPE_TEST_WEBHOOK_SECRET'] = 'whsec_test_secret'
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clear global instances
        import backend.config.stripe as stripe_config_module
        stripe_config_module.stripe_config = None
        stripe_config_module.stripe_error_handler = None
        stripe_config_module.stripe_webhook_config = None
    
    def test_get_stripe_config(self):
        """Test get_stripe_config function."""
        config = get_stripe_config()
        
        assert config.environment == 'test'
        assert config.is_test_mode is True
        assert config.api_key == 'sk_test_test_key'
        
        # Should return the same instance
        config2 = get_stripe_config()
        assert config is config2
    
    def test_get_stripe_error_handler(self):
        """Test get_stripe_error_handler function."""
        error_handler = get_stripe_error_handler()
        
        assert error_handler.config.environment == 'test'
        assert error_handler.logger is not None
        
        # Should return the same instance
        error_handler2 = get_stripe_error_handler()
        assert error_handler is error_handler2
    
    def test_get_stripe_webhook_config(self):
        """Test get_stripe_webhook_config function."""
        webhook_config = get_stripe_webhook_config()
        
        assert webhook_config.config.environment == 'test'
        assert len(webhook_config.supported_events) > 0
        
        # Should return the same instance
        webhook_config2 = get_stripe_webhook_config()
        assert webhook_config is webhook_config2
    
    def test_validate_stripe_environment(self):
        """Test validate_stripe_environment function."""
        validation = validate_stripe_environment()
        
        assert validation['environment'] == 'test'
        assert validation['is_configured'] is True
        assert validation['missing_configuration'] == []
    
    def test_get_stripe_environment_info(self):
        """Test get_stripe_environment_info function."""
        info = get_stripe_environment_info()
        
        assert info['environment'] == 'test'
        assert info['is_test_mode'] is True
        assert info['is_live_mode'] is False
        assert info['is_configured'] is True


class TestConfigurationIntegration:
    """Integration tests for configuration system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Set up complete test environment
        os.environ['STRIPE_ENVIRONMENT'] = 'test'
        os.environ['STRIPE_TEST_SECRET_KEY'] = 'sk_test_integration_key'
        os.environ['STRIPE_TEST_PUBLISHABLE_KEY'] = 'pk_test_integration_key'
        os.environ['STRIPE_TEST_WEBHOOK_SECRET'] = 'whsec_integration_secret'
        os.environ['STRIPE_TEST_WEBHOOK_ENDPOINT'] = 'https://integration.example.com/webhook'
        os.environ['STRIPE_TEST_BUDGET_MONTHLY_PRICE_ID'] = 'price_integration_budget_monthly'
        os.environ['STRIPE_TEST_BUDGET_YEARLY_PRICE_ID'] = 'price_integration_budget_yearly'
        os.environ['STRIPE_TEST_MID_TIER_MONTHLY_PRICE_ID'] = 'price_integration_mid_monthly'
        os.environ['STRIPE_TEST_MID_TIER_YEARLY_PRICE_ID'] = 'price_integration_mid_yearly'
        os.environ['STRIPE_TEST_PROFESSIONAL_MONTHLY_PRICE_ID'] = 'price_integration_pro_monthly'
        os.environ['STRIPE_TEST_PROFESSIONAL_YEARLY_PRICE_ID'] = 'price_integration_pro_yearly'
        os.environ['STRIPE_TEST_CURRENCY'] = 'usd'
        os.environ['STRIPE_TEST_TRIAL_DAYS'] = '7'
        os.environ['STRIPE_TEST_GRACE_PERIOD_DAYS'] = '3'
        os.environ['STRIPE_TEST_LOG_LEVEL'] = 'DEBUG'
        os.environ['STRIPE_TEST_DEBUG'] = 'true'
    
    def test_complete_configuration_validation(self):
        """Test complete configuration validation."""
        validation = validate_stripe_environment()
        
        assert validation['is_configured'] is True
        assert validation['missing_configuration'] == []
        assert validation['warnings'] == []
        
        # Check all price IDs are configured
        price_ids = validation['price_ids_configured']
        assert price_ids['budget_monthly'] is True
        assert price_ids['budget_yearly'] is True
        assert price_ids['mid_tier_monthly'] is True
        assert price_ids['mid_tier_yearly'] is True
        assert price_ids['professional_monthly'] is True
        assert price_ids['professional_yearly'] is True
    
    def test_configuration_with_missing_items(self):
        """Test configuration validation with missing items."""
        # Remove some configuration
        os.environ.pop('STRIPE_TEST_BUDGET_MONTHLY_PRICE_ID', None)
        os.environ.pop('STRIPE_TEST_WEBHOOK_SECRET', None)
        
        validation = validate_stripe_environment()
        
        assert validation['is_configured'] is False
        assert 'STRIPE_TEST_WEBHOOK_SECRET' in validation['missing_configuration']
        assert 'Missing price ID for budget monthly plan' in validation['warnings']
    
    def test_environment_switching(self):
        """Test switching between environments."""
        # Test environment
        config_test = StripeConfig('test')
        assert config_test.environment == 'test'
        assert config_test.is_test_mode is True
        
        # Set up live environment
        os.environ['STRIPE_LIVE_SECRET_KEY'] = 'sk_live_switch_key'
        os.environ['STRIPE_LIVE_PUBLISHABLE_KEY'] = 'pk_live_switch_key'
        os.environ['STRIPE_LIVE_WEBHOOK_SECRET'] = 'whsec_switch_secret'
        
        # Live environment
        config_live = StripeConfig('live')
        assert config_live.environment == 'live'
        assert config_live.is_live_mode is True
        assert config_live.api_key == 'sk_live_switch_key'


if __name__ == '__main__':
    pytest.main([__file__]) 