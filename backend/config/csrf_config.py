"""
CSRF Protection Configuration
Configuration settings for financial CSRF protection system
"""

import os
from typing import List, Dict, Any

class CSRFConfig:
    """Configuration class for CSRF protection settings"""
    
    # Token settings
    TOKEN_LIFETIME = int(os.getenv('CSRF_TOKEN_LIFETIME', 1800))  # 30 minutes
    MAX_TOKENS_PER_SESSION = int(os.getenv('CSRF_MAX_TOKENS_PER_SESSION', 5))
    
    # Security settings
    SECURE_COOKIES = os.getenv('CSRF_SECURE_COOKIES', 'true').lower() == 'true'
    HTTPONLY_COOKIES = os.getenv('CSRF_HTTPONLY_COOKIES', 'true').lower() == 'true'
    SAME_SITE_COOKIES = os.getenv('CSRF_SAME_SITE_COOKIES', 'Strict')
    
    # Flask-WTF settings
    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'true').lower() == 'true'
    WTF_CSRF_TIME_LIMIT = int(os.getenv('WTF_CSRF_TIME_LIMIT', TOKEN_LIFETIME))
    WTF_CSRF_SSL_STRICT = os.getenv('WTF_CSRF_SSL_STRICT', 'true').lower() == 'true'
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']
    
    # Financial endpoint patterns that require CSRF protection
    FINANCIAL_ENDPOINTS = [
        # Income/Expense endpoints
        '/api/v1/financial/transactions',
        '/api/financial/transactions',
        '/api/financial/income',
        '/api/financial/expenses',
        
        # Subscription management
        '/api/payment/subscriptions',
        '/api/payment/subscriptions/',
        '/api/payment/subscriptions/me',
        '/api/payment/subscriptions/tiers',
        
        # Payment processing
        '/api/payment/payment-intents',
        '/api/payment/payment-methods',
        '/api/payment/customers',
        '/api/payment/invoices',
        
        # Financial goals and planning
        '/api/financial/goals',
        '/api/financial-goals',
        '/api/financial/questionnaire',
        '/api/financial/planning',
        
        # Weekly check-ins
        '/api/health/checkin',
        '/api/health/checkin/',
        
        # Financial profile updates
        '/api/financial/profile',
        '/api/financial/profile/',
        '/api/onboarding/financial-profile',
        
        # Billing and subscription changes
        '/api/payment/billing',
        '/api/payment/upgrade',
        '/api/payment/downgrade',
        '/api/payment/cancel',
        
        # Financial compliance
        '/api/financial/payment/process',
        '/api/financial/records/store',
        '/api/financial/breach/report',
        
        # Financial analysis
        '/api/financial-analysis/spending-patterns',
        '/api/financial/analytics',
        '/api/financial/export'
    ]
    
    # Payment-specific validation rules
    PAYMENT_VALIDATION = {
        'max_amount': float(os.getenv('CSRF_MAX_PAYMENT_AMOUNT', 1000000)),  # $1M
        'min_amount': float(os.getenv('CSRF_MIN_PAYMENT_AMOUNT', 0.01)),    # $0.01
        'allowed_currencies': ['usd', 'eur', 'gbp', 'cad', 'aud'],
        'required_fields': ['amount', 'currency', 'description']
    }
    
    # Subscription tier validation
    SUBSCRIPTION_TIERS = [
        'budget',
        'mid_tier', 
        'professional'
    ]
    
    # Security event logging
    LOG_CSRF_EVENTS = os.getenv('LOG_CSRF_EVENTS', 'true').lower() == 'true'
    CSRF_LOG_LEVEL = os.getenv('CSRF_LOG_LEVEL', 'WARNING')
    
    # Rate limiting for CSRF token generation
    CSRF_TOKEN_RATE_LIMIT = {
        'max_requests': int(os.getenv('CSRF_TOKEN_RATE_LIMIT_MAX', 10)),
        'window': int(os.getenv('CSRF_TOKEN_RATE_LIMIT_WINDOW', 3600))  # 1 hour
    }
    
    # Error messages
    ERROR_MESSAGES = {
        'token_missing': {
            'error': 'CSRF token required',
            'message': 'Security token is required for financial operations',
            'code': 'FINANCIAL_CSRF_REQUIRED'
        },
        'token_invalid': {
            'error': 'Invalid CSRF token',
            'message': 'Security token is invalid or expired for financial operation',
            'code': 'FINANCIAL_CSRF_INVALID'
        },
        'token_expired': {
            'error': 'CSRF token expired',
            'message': 'Security token has expired. Please refresh the page and try again.',
            'code': 'FINANCIAL_CSRF_EXPIRED'
        },
        'rate_limit_exceeded': {
            'error': 'Token limit exceeded',
            'message': 'Maximum number of active financial tokens reached',
            'code': 'FINANCIAL_CSRF_RATE_LIMIT'
        }
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get complete configuration as dictionary"""
        return {
            'token_lifetime': cls.TOKEN_LIFETIME,
            'max_tokens_per_session': cls.MAX_TOKENS_PER_SESSION,
            'secure_cookies': cls.SECURE_COOKIES,
            'httponly_cookies': cls.HTTPONLY_COOKIES,
            'same_site_cookies': cls.SAME_SITE_COOKIES,
            'wtf_csrf_enabled': cls.WTF_CSRF_ENABLED,
            'wtf_csrf_time_limit': cls.WTF_CSRF_TIME_LIMIT,
            'wtf_csrf_ssl_strict': cls.WTF_CSRF_SSL_STRICT,
            'wtf_csrf_headers': cls.WTF_CSRF_HEADERS,
            'financial_endpoints': cls.FINANCIAL_ENDPOINTS,
            'payment_validation': cls.PAYMENT_VALIDATION,
            'subscription_tiers': cls.SUBSCRIPTION_TIERS,
            'log_csrf_events': cls.LOG_CSRF_EVENTS,
            'csrf_log_level': cls.CSRF_LOG_LEVEL,
            'csrf_token_rate_limit': cls.CSRF_TOKEN_RATE_LIMIT,
            'error_messages': cls.ERROR_MESSAGES
        }
    
    @classmethod
    def is_financial_endpoint(cls, path: str) -> bool:
        """Check if a path requires financial CSRF protection"""
        return any(path.startswith(endpoint) for endpoint in cls.FINANCIAL_ENDPOINTS)
    
    @classmethod
    def validate_payment_amount(cls, amount: float) -> bool:
        """Validate payment amount"""
        return cls.PAYMENT_VALIDATION['min_amount'] <= amount <= cls.PAYMENT_VALIDATION['max_amount']
    
    @classmethod
    def validate_subscription_tier(cls, tier: str) -> bool:
        """Validate subscription tier"""
        return tier in cls.SUBSCRIPTION_TIERS
