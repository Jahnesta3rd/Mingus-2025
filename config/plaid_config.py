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
from config.secure_config import get_secure_config

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
    """Manages Plaid configuration across different environments using secure configuration management"""
    
    def __init__(self):
        self.secure_config = get_secure_config()
        self.configs = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load configurations for all environments using secure config manager"""
        
        # Development/Sandbox Configuration
        self.configs[PlaidEnvironment.SANDBOX] = PlaidConfig(
            environment=PlaidEnvironment.SANDBOX,
            client_id=self.secure_config.get('PLAID_SANDBOX_CLIENT_ID', ''),
            secret=self.secure_config.get('PLAID_SANDBOX_SECRET', ''),
            webhook=PlaidWebhookConfig(
                webhook_url=self.secure_config.get('PLAID_SANDBOX_WEBHOOK_URL', 'https://your-dev-domain.com/api/plaid/webhook'),
                webhook_secret=self.secure_config.get('PLAID_SANDBOX_WEBHOOK_SECRET', ''),
            ),
            redirect_uri=self.secure_config.get('PLAID_SANDBOX_REDIRECT_URI', 'https://your-dev-domain.com/plaid/link'),
            access_token_encryption_key=self.secure_config.get('PLAID_ACCESS_TOKEN_ENCRYPTION_KEY', ''),
            log_level=self.secure_config.get('PLAID_LOG_LEVEL', 'DEBUG'),
            enable_metrics=self.secure_config.get('PLAID_ENABLE_METRICS', 'true').lower() == 'true',
            request_timeout=int(self.secure_config.get('PLAID_REQUEST_TIMEOUT', '30')),
            max_retries=int(self.secure_config.get('PLAID_MAX_RETRIES', '3')),
            retry_delay=float(self.secure_config.get('PLAID_RETRY_DELAY', '1.0'))
        )
        
        # Development Configuration
        self.configs[PlaidEnvironment.DEVELOPMENT] = PlaidConfig(
            environment=PlaidEnvironment.DEVELOPMENT,
            client_id=self.secure_config.get('PLAID_DEVELOPMENT_CLIENT_ID', ''),
            secret=self.secure_config.get('PLAID_DEVELOPMENT_SECRET', ''),
            webhook=PlaidWebhookConfig(
                webhook_url=self.secure_config.get('PLAID_DEVELOPMENT_WEBHOOK_URL', 'https://your-dev-domain.com/api/plaid/webhook'),
                webhook_secret=self.secure_config.get('PLAID_DEVELOPMENT_WEBHOOK_SECRET', ''),
            ),
            redirect_uri=self.secure_config.get('PLAID_DEVELOPMENT_REDIRECT_URI', 'https://your-dev-domain.com/plaid/link'),
            access_token_encryption_key=self.secure_config.get('PLAID_ACCESS_TOKEN_ENCRYPTION_KEY', ''),
            log_level=self.secure_config.get('PLAID_LOG_LEVEL', 'DEBUG'),
            enable_metrics=self.secure_config.get('PLAID_ENABLE_METRICS', 'true').lower() == 'true',
            request_timeout=int(self.secure_config.get('PLAID_REQUEST_TIMEOUT', '30')),
            max_retries=int(self.secure_config.get('PLAID_MAX_RETRIES', '3')),
            retry_delay=float(self.secure_config.get('PLAID_RETRY_DELAY', '1.0'))
        )
        
        # Production Configuration
        self.configs[PlaidEnvironment.PRODUCTION] = PlaidConfig(
            environment=PlaidEnvironment.PRODUCTION,
            client_id=self.secure_config.get('PLAID_PRODUCTION_CLIENT_ID', ''),
            secret=self.secure_config.get('PLAID_PRODUCTION_SECRET', ''),
            webhook=PlaidWebhookConfig(
                webhook_url=self.secure_config.get('PLAID_PRODUCTION_WEBHOOK_URL', 'https://your-production-domain.com/api/plaid/webhook'),
                webhook_secret=self.secure_config.get('PLAID_PRODUCTION_WEBHOOK_SECRET', ''),
            ),
            redirect_uri=self.secure_config.get('PLAID_PRODUCTION_REDIRECT_URI', 'https://your-production-domain.com/plaid/link'),
            access_token_encryption_key=self.secure_config.get('PLAID_ACCESS_TOKEN_ENCRYPTION_KEY', ''),
            log_level=self.secure_config.get('PLAID_LOG_LEVEL', 'INFO'),
            enable_metrics=self.secure_config.get('PLAID_ENABLE_METRICS', 'true').lower() == 'true',
            request_timeout=int(self.secure_config.get('PLAID_REQUEST_TIMEOUT', '30')),
            max_retries=int(self.secure_config.get('PLAID_MAX_RETRIES', '3')),
            retry_delay=float(self.secure_config.get('PLAID_RETRY_DELAY', '1.0'))
        )
    
    def get_config(self, environment: PlaidEnvironment) -> PlaidConfig:
        """Get configuration for specific environment"""
        if environment not in self.configs:
            raise ValueError(f"Configuration not found for environment: {environment}")
        return self.configs[environment]
    
    def get_current_config(self) -> PlaidConfig:
        """Get configuration for current environment"""
        current_env = self.secure_config.get('PLAID_ENVIRONMENT', 'sandbox').lower()
        
        if current_env == 'sandbox':
            return self.get_config(PlaidEnvironment.SANDBOX)
        elif current_env == 'development':
            return self.get_config(PlaidEnvironment.DEVELOPMENT)
        elif current_env == 'production':
            return self.get_config(PlaidEnvironment.PRODUCTION)
        else:
            logger.warning(f"Unknown Plaid environment: {current_env}, defaulting to sandbox")
            return self.get_config(PlaidEnvironment.SANDBOX)
    
    def validate_config(self, config: PlaidConfig) -> bool:
        """Validate Plaid configuration"""
        try:
            # Check required fields
            if not config.client_id:
                logger.error("Plaid client_id is missing")
                return False
            
            if not config.secret:
                logger.error("Plaid secret is missing")
                return False
            
            if not config.webhook.webhook_url:
                logger.error("Plaid webhook URL is missing")
                return False
            
            # Validate webhook URL format
            if not config.webhook.webhook_url.startswith(('http://', 'https://')):
                logger.error("Plaid webhook URL must start with http:// or https://")
                return False
            
            # Validate redirect URI if provided
            if config.redirect_uri and not config.redirect_uri.startswith(('http://', 'https://')):
                logger.error("Plaid redirect URI must start with http:// or https://")
                return False
            
            # Validate timeout and retry settings
            if config.request_timeout <= 0:
                logger.error("Plaid request timeout must be positive")
                return False
            
            if config.max_retries < 0:
                logger.error("Plaid max retries must be non-negative")
                return False
            
            if config.retry_delay < 0:
                logger.error("Plaid retry delay must be non-negative")
                return False
            
            logger.info(f"Plaid configuration for {config.environment.value} is valid")
            return True
            
        except Exception as e:
            logger.error(f"Error validating Plaid configuration: {e}")
            return False
    
    def get_webhook_config(self, environment: PlaidEnvironment) -> PlaidWebhookConfig:
        """Get webhook configuration for specific environment"""
        config = self.get_config(environment)
        return config.webhook


# Global instance for easy access
_plaid_config_manager = None

def get_plaid_config(environment: Optional[PlaidEnvironment] = None) -> PlaidConfig:
    """Get Plaid configuration for specified or current environment"""
    global _plaid_config_manager
    if _plaid_config_manager is None:
        _plaid_config_manager = PlaidConfigManager()
    
    if environment:
        return _plaid_config_manager.get_config(environment)
    else:
        return _plaid_config_manager.get_current_config()

def validate_plaid_config(environment: Optional[PlaidEnvironment] = None) -> bool:
    """Validate Plaid configuration for specified or current environment"""
    config = get_plaid_config(environment)
    return _plaid_config_manager.validate_config(config) 