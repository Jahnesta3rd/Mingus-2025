"""
Webhook Configuration
Configuration settings for webhook handlers and external service integrations
"""

import os
from typing import Dict, Any
from config.secure_config import get_secure_config


class WebhookConfig:
    """Configuration for webhook handlers using secure configuration management"""
    
    def __init__(self):
        """Initialize webhook configuration with secure config manager"""
        self.secure_config = get_secure_config()
        self._load_webhook_config()
    
    def _load_webhook_config(self):
        """Load webhook-specific configuration"""
        # Twilio Configuration
        self.TWILIO_AUTH_TOKEN = self.secure_config.get('TWILIO_AUTH_TOKEN', '')
        self.TWILIO_ACCOUNT_SID = self.secure_config.get('TWILIO_ACCOUNT_SID', '')
        self.TWILIO_PHONE_NUMBER = self.secure_config.get('TWILIO_PHONE_NUMBER', '')
        
        # Resend Configuration
        self.RESEND_API_KEY = self.secure_config.get('RESEND_API_KEY', '')
        self.RESEND_WEBHOOK_SECRET = self.secure_config.get('RESEND_WEBHOOK_SECRET', '')
        self.RESEND_FROM_EMAIL = self.secure_config.get('RESEND_FROM_EMAIL', 'noreply@mingus.com')
        
        # Webhook Security
        self.WEBHOOK_TIMEOUT = int(self.secure_config.get('WEBHOOK_TIMEOUT', '30'))  # seconds
        self.WEBHOOK_MAX_RETRIES = int(self.secure_config.get('WEBHOOK_MAX_RETRIES', '3'))
        
        # Rate Limiting
        self.WEBHOOK_RATE_LIMIT = self.secure_config.get('WEBHOOK_RATE_LIMIT', '100/hour')
        
        # Logging
        self.WEBHOOK_LOG_LEVEL = self.secure_config.get('WEBHOOK_LOG_LEVEL', 'INFO')
        self.WEBHOOK_LOG_FORMAT = self.secure_config.get('WEBHOOK_LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Message ID Mapping
        # How to map external service IDs to our internal message IDs
        self.MESSAGE_ID_MAPPING_STRATEGY = self.secure_config.get('MESSAGE_ID_MAPPING_STRATEGY', 'database')
        
        # Supported mapping strategies:
        # - 'database': Store external ID in database
        # - 'embedded': Embed our ID in external service metadata
        # - 'timestamp': Use timestamp-based matching
        
        # Database mapping table (if using database strategy)
        self.MESSAGE_MAPPING_TABLE = self.secure_config.get('MESSAGE_MAPPING_TABLE', 'message_external_ids')
        
        # Timestamp matching window (if using timestamp strategy)
        self.TIMESTAMP_MATCHING_WINDOW = int(self.secure_config.get('TIMESTAMP_MATCHING_WINDOW', '3600'))  # seconds
        
        # Webhook endpoints
        self.TWILIO_WEBHOOK_URL = self.secure_config.get('TWILIO_WEBHOOK_URL', '/webhooks/twilio')
        self.RESEND_WEBHOOK_URL = self.secure_config.get('RESEND_WEBHOOK_URL', '/webhooks/resend')
        
        # Error handling
        self.WEBHOOK_ERROR_NOTIFICATION_EMAIL = self.secure_config.get('WEBHOOK_ERROR_NOTIFICATION_EMAIL', '')
        self.WEBHOOK_ERROR_NOTIFICATION_SLACK = self.secure_config.get('WEBHOOK_ERROR_NOTIFICATION_SLACK', '')
        
        # Monitoring
        self.WEBHOOK_METRICS_ENABLED = self.secure_config.get('WEBHOOK_METRICS_ENABLED', 'true').lower() == 'true'
        self.WEBHOOK_METRICS_RETENTION_DAYS = int(self.secure_config.get('WEBHOOK_METRICS_RETENTION_DAYS', '30'))
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate webhook configuration
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required Twilio settings
        if not self.TWILIO_AUTH_TOKEN:
            validation_results['errors'].append('TWILIO_AUTH_TOKEN is required for SMS webhooks')
            validation_results['valid'] = False
        
        if not self.TWILIO_ACCOUNT_SID:
            validation_results['warnings'].append('TWILIO_ACCOUNT_SID is recommended for SMS functionality')
        
        # Check required Resend settings
        if not self.RESEND_WEBHOOK_SECRET:
            validation_results['errors'].append('RESEND_WEBHOOK_SECRET is required for email webhooks')
            validation_results['valid'] = False
        
        if not self.RESEND_API_KEY:
            validation_results['warnings'].append('RESEND_API_KEY is recommended for email functionality')
        
        # Check webhook URLs
        if not self.TWILIO_WEBHOOK_URL.startswith('/'):
            validation_results['errors'].append('TWILIO_WEBHOOK_URL must start with /')
            validation_results['valid'] = False
        
        if not self.RESEND_WEBHOOK_URL.startswith('/'):
            validation_results['errors'].append('RESEND_WEBHOOK_URL must start with /')
            validation_results['valid'] = False
        
        # Check mapping strategy
        valid_strategies = ['database', 'embedded', 'timestamp']
        if self.MESSAGE_ID_MAPPING_STRATEGY not in valid_strategies:
            validation_results['errors'].append(f'MESSAGE_ID_MAPPING_STRATEGY must be one of: {valid_strategies}')
            validation_results['valid'] = False
        
        return validation_results
    
    def get_webhook_urls(self) -> Dict[str, str]:
        """
        Get webhook URLs for external services
        
        Returns:
            Dictionary with webhook URLs
        """
        base_url = self.secure_config.get('WEBHOOK_BASE_URL', 'https://api.mingus.com')
        
        return {
            'twilio': f"{base_url}{self.TWILIO_WEBHOOK_URL}",
            'resend': f"{base_url}{self.RESEND_WEBHOOK_URL}",
            'health': f"{base_url}/webhooks/health"
        }
    
    def is_development(self) -> bool:
        """
        Check if running in development mode
        
        Returns:
            True if in development mode
        """
        return self.secure_config.get('FLASK_ENV', 'production') == 'development'
    
    def should_verify_signatures(self) -> bool:
        """
        Check if webhook signatures should be verified
        
        Returns:
            True if signatures should be verified
        """
        # Always verify in production, optional in development
        if self.is_development():
            return self.secure_config.get('VERIFY_WEBHOOK_SIGNATURES', 'true').lower() == 'true'
        return True


# Global instance for easy access
_webhook_config = None

def get_webhook_config() -> WebhookConfig:
    """Get the global webhook configuration instance"""
    global _webhook_config
    if _webhook_config is None:
        _webhook_config = WebhookConfig()
    return _webhook_config 