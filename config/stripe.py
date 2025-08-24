"""
MINGUS Application - Stripe Configuration
========================================

Comprehensive Stripe configuration for development and production environments.

Features:
- Environment-specific API keys
- Webhook endpoint configuration
- Test mode and live mode handling
- Error handling and logging configuration
- Security settings

Author: MINGUS Development Team
Date: January 2025
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from .secure_config import get_secure_config


class StripeEnvironment(Enum):
    """Stripe environment enumeration."""
    TEST = "test"
    LIVE = "live"


class StripeConfig:
    """Comprehensive Stripe configuration management using secure configuration."""
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize Stripe configuration.
        
        Args:
            environment: Environment to use ('test' or 'live'). 
                        Defaults to environment variable STRIPE_ENVIRONMENT
        """
        self.secure_config = get_secure_config()
        self.environment = environment or self.secure_config.get('STRIPE_ENVIRONMENT', 'test')
        
        if self.environment not in ['test', 'live']:
            raise ValueError("Environment must be 'test' or 'live'")
        
        self.is_test_mode = self.environment == 'test'
        self.is_live_mode = self.environment == 'live'
        
        # Load configuration based on environment
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration based on current environment."""
        if self.is_test_mode:
            self._load_test_configuration()
        else:
            self._load_live_configuration()
    
    def _load_test_configuration(self):
        """Load test environment configuration using secure config manager."""
        self.api_key = self.secure_config.get('STRIPE_TEST_SECRET_KEY')
        self.publishable_key = self.secure_config.get('STRIPE_TEST_PUBLISHABLE_KEY')
        self.webhook_secret = self.secure_config.get('STRIPE_TEST_WEBHOOK_SECRET')
        
        # Test webhook endpoint
        self.webhook_endpoint = self.secure_config.get(
            'STRIPE_TEST_WEBHOOK_ENDPOINT',
            'https://your-test-domain.com/api/payment/webhooks/stripe'
        )
        
        # Test price IDs
        self.price_ids = {
            'budget_monthly': self.secure_config.get('STRIPE_TEST_BUDGET_MONTHLY_PRICE_ID'),
            'budget_yearly': self.secure_config.get('STRIPE_TEST_BUDGET_YEARLY_PRICE_ID'),
            'mid_tier_monthly': self.secure_config.get('STRIPE_TEST_MID_TIER_MONTHLY_PRICE_ID'),
            'mid_tier_yearly': self.secure_config.get('STRIPE_TEST_MID_TIER_YEARLY_PRICE_ID'),
            'professional_monthly': self.secure_config.get('STRIPE_TEST_PROFESSIONAL_MONTHLY_PRICE_ID'),
            'professional_yearly': self.secure_config.get('STRIPE_TEST_PROFESSIONAL_YEARLY_PRICE_ID'),
        }
        
        # Test-specific settings
        self.currency = self.secure_config.get('STRIPE_TEST_CURRENCY', 'usd')
        self.trial_days = int(self.secure_config.get('STRIPE_TEST_TRIAL_DAYS', '7'))
        self.grace_period_days = int(self.secure_config.get('STRIPE_TEST_GRACE_PERIOD_DAYS', '3'))
        
        # Test logging
        self.log_level = self.secure_config.get('STRIPE_TEST_LOG_LEVEL', 'DEBUG')
        self.enable_debug = self.secure_config.get('STRIPE_TEST_DEBUG', 'true').lower() == 'true'
        
    def _load_live_configuration(self):
        """Load live environment configuration using secure config manager."""
        self.api_key = self.secure_config.get('STRIPE_LIVE_SECRET_KEY')
        self.publishable_key = self.secure_config.get('STRIPE_LIVE_PUBLISHABLE_KEY')
        self.webhook_secret = self.secure_config.get('STRIPE_LIVE_WEBHOOK_SECRET')
        
        # Live webhook endpoint
        self.webhook_endpoint = self.secure_config.get(
            'STRIPE_LIVE_WEBHOOK_ENDPOINT',
            'https://your-live-domain.com/api/payment/webhooks/stripe'
        )
        
        # Live price IDs
        self.price_ids = {
            'budget_monthly': self.secure_config.get('STRIPE_LIVE_BUDGET_MONTHLY_PRICE_ID'),
            'budget_yearly': self.secure_config.get('STRIPE_LIVE_BUDGET_YEARLY_PRICE_ID'),
            'mid_tier_monthly': self.secure_config.get('STRIPE_LIVE_MID_TIER_MONTHLY_PRICE_ID'),
            'mid_tier_yearly': self.secure_config.get('STRIPE_LIVE_MID_TIER_YEARLY_PRICE_ID'),
            'professional_monthly': self.secure_config.get('STRIPE_LIVE_PROFESSIONAL_MONTHLY_PRICE_ID'),
            'professional_yearly': self.secure_config.get('STRIPE_LIVE_PROFESSIONAL_YEARLY_PRICE_ID'),
        }
        
        # Live-specific settings
        self.currency = self.secure_config.get('STRIPE_LIVE_CURRENCY', 'usd')
        self.trial_days = int(self.secure_config.get('STRIPE_LIVE_TRIAL_DAYS', '7'))
        self.grace_period_days = int(self.secure_config.get('STRIPE_LIVE_GRACE_PERIOD_DAYS', '3'))
        
        # Live logging
        self.log_level = self.secure_config.get('STRIPE_LIVE_LOG_LEVEL', 'INFO')
        self.enable_debug = self.secure_config.get('STRIPE_LIVE_DEBUG', 'false').lower() == 'true'
    
    @property
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return bool(
            self.api_key and 
            self.publishable_key and 
            self.webhook_secret
        )
    
    @property
    def missing_configuration(self) -> list:
        """Get list of missing configuration items."""
        missing = []
        
        if not self.api_key:
            missing.append(f'STRIPE_{self.environment.upper()}_SECRET_KEY')
        
        if not self.publishable_key:
            missing.append(f'STRIPE_{self.environment.upper()}_PUBLISHABLE_KEY')
        
        if not self.webhook_secret:
            missing.append(f'STRIPE_{self.environment.upper()}_WEBHOOK_SECRET')
        
        return missing
    
    def get_price_id(self, tier: str, billing_cycle: str) -> Optional[str]:
        """
        Get price ID for a specific tier and billing cycle.
        
        Args:
            tier: Subscription tier ('budget', 'mid_tier', 'professional')
            billing_cycle: Billing cycle ('monthly', 'yearly')
            
        Returns:
            Price ID or None if not configured
        """
        key = f'{tier}_{billing_cycle}'
        return self.price_ids.get(key)
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the current configuration.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'environment': self.environment,
            'is_configured': self.is_configured,
            'missing_configuration': self.missing_configuration,
            'price_ids_configured': {},
            'warnings': []
        }
        
        # Check price IDs
        for tier in ['budget', 'mid_tier', 'professional']:
            for cycle in ['monthly', 'yearly']:
                price_id = self.get_price_id(tier, cycle)
                validation['price_ids_configured'][f'{tier}_{cycle}'] = bool(price_id)
                
                if not price_id:
                    validation['warnings'].append(
                        f'Missing price ID for {tier} {cycle} plan'
                    )
        
        # Check webhook endpoint
        if not self.webhook_endpoint or 'your-domain' in self.webhook_endpoint:
            validation['warnings'].append(
                'Webhook endpoint not properly configured'
            )
        
        return validation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'environment': self.environment,
            'is_test_mode': self.is_test_mode,
            'is_live_mode': self.is_live_mode,
            'currency': self.currency,
            'trial_days': self.trial_days,
            'grace_period_days': self.grace_period_days,
            'log_level': self.log_level,
            'enable_debug': self.enable_debug,
            'webhook_endpoint': self.webhook_endpoint,
            'price_ids_configured': {
                key: bool(value) for key, value in self.price_ids.items()
            },
            'is_configured': self.is_configured,
            'missing_configuration': self.missing_configuration
        }
    
    def rotate_api_key(self) -> str:
        """
        Rotate the current API key.
        
        Returns:
            New API key
        """
        if self.is_test_mode:
            return self.secure_config.rotate_secret('STRIPE_TEST_SECRET_KEY')
        else:
            return self.secure_config.rotate_secret('STRIPE_LIVE_SECRET_KEY')
    
    def rotate_webhook_secret(self) -> str:
        """
        Rotate the webhook secret.
        
        Returns:
            New webhook secret
        """
        if self.is_test_mode:
            return self.secure_config.rotate_secret('STRIPE_TEST_WEBHOOK_SECRET')
        else:
            return self.secure_config.rotate_secret('STRIPE_LIVE_WEBHOOK_SECRET')


class StripeErrorHandler:
    """Stripe error handling and logging configuration."""
    
    def __init__(self, config: StripeConfig):
        """
        Initialize error handler.
        
        Args:
            config: Stripe configuration
        """
        self.config = config
        self.logger = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        import logging
        
        # Create logger
        self.logger = logging.getLogger('stripe')
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create file handler
        log_file = f'logs/stripe_{self.config.environment}.log'
        os.makedirs('logs', exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, self.config.log_level.upper()))
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.config.log_level.upper()))
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Set Stripe debug mode
        if self.config.enable_debug:
            import stripe
            stripe.log = self.config.log_level.lower()
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """
        Log Stripe error with context.
        
        Args:
            error: Exception that occurred
            context: Additional context information
        """
        if not self.logger:
            return
        
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'environment': self.config.environment,
            'context': context or {}
        }
        
        self.logger.error(f"Stripe Error: {error_info}")
    
    def log_payment_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Log payment event.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        if not self.logger:
            return
        
        log_data = {
            'event_type': event_type,
            'environment': self.config.environment,
            'timestamp': event_data.get('created'),
            'customer_id': event_data.get('customer'),
            'subscription_id': event_data.get('subscription'),
            'amount': event_data.get('amount'),
            'currency': event_data.get('currency'),
            'status': event_data.get('status')
        }
        
        self.logger.info(f"Payment Event: {log_data}")
    
    def log_subscription_event(self, event_type: str, subscription_data: Dict[str, Any]):
        """
        Log subscription event.
        
        Args:
            event_type: Type of event
            subscription_data: Subscription data
        """
        if not self.logger:
            return
        
        log_data = {
            'event_type': event_type,
            'environment': self.config.environment,
            'subscription_id': subscription_data.get('id'),
            'customer_id': subscription_data.get('customer'),
            'status': subscription_data.get('status'),
            'current_period_start': subscription_data.get('current_period_start'),
            'current_period_end': subscription_data.get('current_period_end'),
            'cancel_at_period_end': subscription_data.get('cancel_at_period_end')
        }
        
        self.logger.info(f"Subscription Event: {log_data}")


class StripeWebhookConfig:
    """Webhook configuration and validation."""
    
    def __init__(self, config: StripeConfig):
        """
        Initialize webhook configuration.
        
        Args:
            config: Stripe configuration
        """
        self.config = config
        self.supported_events = [
            'customer.subscription.created',
            'customer.subscription.updated',
            'customer.subscription.deleted',
            'invoice.payment_succeeded',
            'invoice.payment_failed',
            'payment_intent.succeeded',
            'payment_intent.payment_failed',
            'customer.created',
            'customer.updated',
            'customer.deleted',
            'payment_method.attached',
            'payment_method.detached',
            'invoice.created',
            'invoice.finalized',
            'invoice.payment_action_required'
        ]
    
    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            
        Returns:
            True if signature is valid
        """
        try:
            import stripe
            stripe.Webhook.construct_event(
                payload, 
                signature, 
                self.config.webhook_secret
            )
            return True
        except Exception:
            return False
    
    def is_supported_event(self, event_type: str) -> bool:
        """
        Check if event type is supported.
        
        Args:
            event_type: Event type to check
            
        Returns:
            True if event is supported
        """
        return event_type in self.supported_events
    
    def get_webhook_url(self) -> str:
        """
        Get webhook URL for current environment.
        
        Returns:
            Webhook URL
        """
        return self.config.webhook_endpoint


# Global configuration instances
stripe_config = None
stripe_error_handler = None
stripe_webhook_config = None


def get_stripe_config() -> StripeConfig:
    """Get global Stripe configuration instance."""
    global stripe_config
    if stripe_config is None:
        stripe_config = StripeConfig()
    return stripe_config


def get_stripe_error_handler() -> StripeErrorHandler:
    """Get global Stripe error handler instance."""
    global stripe_error_handler
    if stripe_error_handler is None:
        config = get_stripe_config()
        stripe_error_handler = StripeErrorHandler(config)
    return stripe_error_handler


def get_stripe_webhook_config() -> StripeWebhookConfig:
    """Get global Stripe webhook configuration instance."""
    global stripe_webhook_config
    if stripe_webhook_config is None:
        config = get_stripe_config()
        stripe_webhook_config = StripeWebhookConfig(config)
    return stripe_webhook_config


def validate_stripe_environment() -> Dict[str, Any]:
    """
    Validate Stripe environment configuration.
    
    Returns:
        Validation results
    """
    config = get_stripe_config()
    return config.validate_configuration()


def get_stripe_environment_info() -> Dict[str, Any]:
    """
    Get Stripe environment information.
    
    Returns:
        Environment information
    """
    config = get_stripe_config()
    return config.to_dict()


def rotate_stripe_secrets() -> Dict[str, str]:
    """
    Rotate all Stripe secrets.
    
    Returns:
        Dictionary with new secrets
    """
    config = get_stripe_config()
    new_secrets = {}
    
    # Rotate API key
    new_secrets['api_key'] = config.rotate_api_key()
    
    # Rotate webhook secret
    new_secrets['webhook_secret'] = config.rotate_webhook_secret()
    
    return new_secrets 