"""
Plaid Configuration for MINGUS

This module provides comprehensive configuration management for Plaid integration
across different environments (Development/Sandbox and Production) with webhook support.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class PlaidEnvironment(Enum):
    """Plaid environment types"""
    SANDBOX = "sandbox"
    DEVELOPMENT = "development"
    PRODUCTION = "production"

@dataclass
class PlaidWebhookConfig:
    """Webhook configuration for Plaid"""
    webhook_url: str
    webhook_secret: Optional[str] = None
    webhook_events: list = None
    
    def __post_init__(self):
        if self.webhook_events is None:
            self.webhook_events = [
                'TRANSACTIONS_INITIAL_UPDATE',
                'TRANSACTIONS_HISTORICAL_UPDATE',
                'TRANSACTIONS_DEFAULT_UPDATE',
                'TRANSACTIONS_REMOVED',
                'ITEM_LOGIN_REQUIRED',
                'ITEM_ERROR',
                'ACCOUNT_UPDATED',
                'ACCOUNT_AVAILABLE_BALANCE_UPDATED'
            ]

@dataclass
class PlaidConfig:
    """Complete Plaid configuration"""
    # Environment
    environment: PlaidEnvironment
    
    # API Credentials
    client_id: str
    secret: str
    
    # Webhook Configuration
    webhook: PlaidWebhookConfig
    
    # Link Configuration
    redirect_uri: Optional[str] = None
    update_mode: str = "background"
    country_codes: list = None
    language: str = "en"
    
    # Security
    access_token_encryption_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    enable_metrics: bool = True
    
    # Performance
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        if self.country_codes is None:
            self.country_codes = ["US"]
        
        # Validate required fields
        if not self.client_id or not self.secret:
            raise ValueError("Plaid client_id and secret are required")
        
        if not self.webhook.webhook_url:
            raise ValueError("Webhook URL is required")

class PlaidConfigManager:
    """Manages Plaid configuration across different environments"""
    
    def __init__(self):
        self.configs = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load configurations for all environments"""
        
        # Development/Sandbox Configuration
        self.configs[PlaidEnvironment.SANDBOX] = PlaidConfig(
            environment=PlaidEnvironment.SANDBOX,
            client_id=os.getenv('PLAID_SANDBOX_CLIENT_ID', ''),
            secret=os.getenv('PLAID_SANDBOX_SECRET', ''),
            webhook=PlaidWebhookConfig(
                webhook_url=os.getenv('PLAID_SANDBOX_WEBHOOK_URL', 'https://your-dev-domain.com/api/plaid/webhook'),
                webhook_secret=os.getenv('PLAID_SANDBOX_WEBHOOK_SECRET'),
                webhook_events=[
                    'TRANSACTIONS_INITIAL_UPDATE',
                    'TRANSACTIONS_HISTORICAL_UPDATE',
                    'TRANSACTIONS_DEFAULT_UPDATE',
                    'TRANSACTIONS_REMOVED',
                    'ITEM_LOGIN_REQUIRED',
                    'ITEM_ERROR'
                ]
            ),
            redirect_uri=os.getenv('PLAID_SANDBOX_REDIRECT_URI', 'https://your-dev-domain.com/plaid/callback'),
            update_mode="background",
            country_codes=["US"],
            language="en",
            access_token_encryption_key=os.getenv('PLAID_SANDBOX_ENCRYPTION_KEY'),
            log_level="DEBUG",
            enable_metrics=True,
            request_timeout=30,
            max_retries=3,
            retry_delay=1.0
        )
        
        # Production Configuration
        self.configs[PlaidEnvironment.PRODUCTION] = PlaidConfig(
            environment=PlaidEnvironment.PRODUCTION,
            client_id=os.getenv('PLAID_PRODUCTION_CLIENT_ID', ''),
            secret=os.getenv('PLAID_PRODUCTION_SECRET', ''),
            webhook=PlaidWebhookConfig(
                webhook_url=os.getenv('PLAID_PRODUCTION_WEBHOOK_URL', 'https://your-prod-domain.com/api/plaid/webhook'),
                webhook_secret=os.getenv('PLAID_PRODUCTION_WEBHOOK_SECRET'),
                webhook_events=[
                    'TRANSACTIONS_INITIAL_UPDATE',
                    'TRANSACTIONS_HISTORICAL_UPDATE',
                    'TRANSACTIONS_DEFAULT_UPDATE',
                    'TRANSACTIONS_REMOVED',
                    'ITEM_LOGIN_REQUIRED',
                    'ITEM_ERROR',
                    'ACCOUNT_UPDATED',
                    'ACCOUNT_AVAILABLE_BALANCE_UPDATED'
                ]
            ),
            redirect_uri=os.getenv('PLAID_PRODUCTION_REDIRECT_URI', 'https://your-prod-domain.com/plaid/callback'),
            update_mode="background",
            country_codes=["US"],
            language="en",
            access_token_encryption_key=os.getenv('PLAID_PRODUCTION_ENCRYPTION_KEY'),
            log_level="INFO",
            enable_metrics=True,
            request_timeout=30,
            max_retries=3,
            retry_delay=1.0
        )
    
    def get_config(self, environment: PlaidEnvironment) -> PlaidConfig:
        """Get configuration for specified environment"""
        if environment not in self.configs:
            raise ValueError(f"Configuration not found for environment: {environment}")
        
        return self.configs[environment]
    
    def get_current_config(self) -> PlaidConfig:
        """Get configuration for current environment"""
        env_str = os.getenv('PLAID_ENV', 'sandbox').lower()
        
        if env_str in ['sandbox', 'development']:
            return self.get_config(PlaidEnvironment.SANDBOX)
        elif env_str == 'production':
            return self.get_config(PlaidEnvironment.PRODUCTION)
        else:
            raise ValueError(f"Invalid Plaid environment: {env_str}")
    
    def validate_config(self, config: PlaidConfig) -> bool:
        """Validate configuration"""
        try:
            # Check required fields
            if not config.client_id or not config.secret:
                logger.error("Plaid client_id and secret are required")
                return False
            
            if not config.webhook.webhook_url:
                logger.error("Webhook URL is required")
                return False
            
            # Validate webhook URL format
            if not config.webhook.webhook_url.startswith(('http://', 'https://')):
                logger.error("Webhook URL must be a valid HTTP/HTTPS URL")
                return False
            
            # Production-specific validations
            if config.environment == PlaidEnvironment.PRODUCTION:
                if not config.webhook.webhook_url.startswith('https://'):
                    logger.error("Production webhook URL must use HTTPS")
                    return False
                
                if not config.access_token_encryption_key:
                    logger.warning("Access token encryption key is recommended for production")
            
            logger.info(f"Plaid configuration validated for environment: {config.environment.value}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def get_webhook_config(self, environment: PlaidEnvironment) -> PlaidWebhookConfig:
        """Get webhook configuration for specified environment"""
        config = self.get_config(environment)
        return config.webhook

# Global configuration manager instance
plaid_config_manager = PlaidConfigManager()

def get_plaid_config(environment: Optional[PlaidEnvironment] = None) -> PlaidConfig:
    """Get Plaid configuration for specified or current environment"""
    if environment:
        return plaid_config_manager.get_config(environment)
    else:
        return plaid_config_manager.get_current_config()

def validate_plaid_config(environment: Optional[PlaidEnvironment] = None) -> bool:
    """Validate Plaid configuration"""
    config = get_plaid_config(environment)
    return plaid_config_manager.validate_config(config) 