"""
Webhook Configuration
Configuration settings for webhook handlers and external service integrations
"""

import os
from typing import Dict, Any


class WebhookConfig:
    """Configuration for webhook handlers"""
    
    # Twilio Configuration
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
    
    # Resend Configuration
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
    RESEND_WEBHOOK_SECRET = os.environ.get('RESEND_WEBHOOK_SECRET', '')
    RESEND_FROM_EMAIL = os.environ.get('RESEND_FROM_EMAIL', 'noreply@mingus.com')
    
    # Webhook Security
    WEBHOOK_TIMEOUT = int(os.environ.get('WEBHOOK_TIMEOUT', '30'))  # seconds
    WEBHOOK_MAX_RETRIES = int(os.environ.get('WEBHOOK_MAX_RETRIES', '3'))
    
    # Rate Limiting
    WEBHOOK_RATE_LIMIT = os.environ.get('WEBHOOK_RATE_LIMIT', '100/hour')
    
    # Logging
    WEBHOOK_LOG_LEVEL = os.environ.get('WEBHOOK_LOG_LEVEL', 'INFO')
    WEBHOOK_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Message ID Mapping
    # How to map external service IDs to our internal message IDs
    MESSAGE_ID_MAPPING_STRATEGY = os.environ.get('MESSAGE_ID_MAPPING_STRATEGY', 'database')
    
    # Supported mapping strategies:
    # - 'database': Store external ID in database
    # - 'embedded': Embed our ID in external service metadata
    # - 'timestamp': Use timestamp-based matching
    
    # Database mapping table (if using database strategy)
    MESSAGE_MAPPING_TABLE = 'message_external_ids'
    
    # Timestamp matching window (if using timestamp strategy)
    TIMESTAMP_MATCHING_WINDOW = int(os.environ.get('TIMESTAMP_MATCHING_WINDOW', '3600'))  # seconds
    
    # Webhook endpoints
    TWILIO_WEBHOOK_URL = os.environ.get('TWILIO_WEBHOOK_URL', '/webhooks/twilio')
    RESEND_WEBHOOK_URL = os.environ.get('RESEND_WEBHOOK_URL', '/webhooks/resend')
    
    # Error handling
    WEBHOOK_ERROR_NOTIFICATION_EMAIL = os.environ.get('WEBHOOK_ERROR_NOTIFICATION_EMAIL', '')
    WEBHOOK_ERROR_NOTIFICATION_SLACK = os.environ.get('WEBHOOK_ERROR_NOTIFICATION_SLACK', '')
    
    # Monitoring
    WEBHOOK_METRICS_ENABLED = os.environ.get('WEBHOOK_METRICS_ENABLED', 'true').lower() == 'true'
    WEBHOOK_METRICS_RETENTION_DAYS = int(os.environ.get('WEBHOOK_METRICS_RETENTION_DAYS', '30'))
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
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
        if not cls.TWILIO_AUTH_TOKEN:
            validation_results['errors'].append('TWILIO_AUTH_TOKEN is required for SMS webhooks')
            validation_results['valid'] = False
        
        if not cls.TWILIO_ACCOUNT_SID:
            validation_results['warnings'].append('TWILIO_ACCOUNT_SID is recommended for SMS functionality')
        
        # Check required Resend settings
        if not cls.RESEND_WEBHOOK_SECRET:
            validation_results['errors'].append('RESEND_WEBHOOK_SECRET is required for email webhooks')
            validation_results['valid'] = False
        
        if not cls.RESEND_API_KEY:
            validation_results['warnings'].append('RESEND_API_KEY is recommended for email functionality')
        
        # Check webhook URLs
        if not cls.TWILIO_WEBHOOK_URL.startswith('/'):
            validation_results['errors'].append('TWILIO_WEBHOOK_URL must start with /')
            validation_results['valid'] = False
        
        if not cls.RESEND_WEBHOOK_URL.startswith('/'):
            validation_results['errors'].append('RESEND_WEBHOOK_URL must start with /')
            validation_results['valid'] = False
        
        # Check mapping strategy
        valid_strategies = ['database', 'embedded', 'timestamp']
        if cls.MESSAGE_ID_MAPPING_STRATEGY not in valid_strategies:
            validation_results['errors'].append(f'MESSAGE_ID_MAPPING_STRATEGY must be one of: {valid_strategies}')
            validation_results['valid'] = False
        
        return validation_results
    
    @classmethod
    def get_webhook_urls(cls) -> Dict[str, str]:
        """
        Get webhook URLs for external services
        
        Returns:
            Dictionary with webhook URLs
        """
        base_url = os.environ.get('WEBHOOK_BASE_URL', 'https://api.mingus.com')
        
        return {
            'twilio': f"{base_url}{cls.TWILIO_WEBHOOK_URL}",
            'resend': f"{base_url}{cls.RESEND_WEBHOOK_URL}",
            'health': f"{base_url}/webhooks/health"
        }
    
    @classmethod
    def is_development(cls) -> bool:
        """
        Check if running in development mode
        
        Returns:
            True if in development mode
        """
        return os.environ.get('FLASK_ENV', 'production') == 'development'
    
    @classmethod
    def should_verify_signatures(cls) -> bool:
        """
        Check if webhook signatures should be verified
        
        Returns:
            True if signatures should be verified
        """
        # Always verify in production, optional in development
        if cls.is_development():
            return os.environ.get('VERIFY_WEBHOOK_SIGNATURES', 'true').lower() == 'true'
        return True 