#!/usr/bin/env python3
"""
Unified Security Configuration for MINGUS Assessment System
Centralized configuration for JWT authentication and security features
"""

import os
from typing import Dict, Any, List
from datetime import timedelta

class UnifiedSecurityConfig:
    """Unified security configuration settings"""
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800))  # 7 days
    JWT_TOKEN_ROTATION_THRESHOLD = int(os.getenv('JWT_TOKEN_ROTATION_THRESHOLD', 300))  # 5 minutes
    
    # JWT Claims Configuration
    JWT_ISSUER = 'mingus-app'
    JWT_AUDIENCE = 'mingus-users'
    JWT_REQUIRE_IP_VALIDATION = os.getenv('JWT_REQUIRE_IP_VALIDATION', 'false').lower() == 'true'
    JWT_REQUIRE_USER_AGENT_VALIDATION = os.getenv('JWT_REQUIRE_USER_AGENT_VALIDATION', 'false').lower() == 'true'
    
    # Session Management Configuration
    MAX_CONCURRENT_SESSIONS = int(os.getenv('MAX_CONCURRENT_SESSIONS', 3))
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', 3600))  # 1 hour
    SESSION_REFRESH_THRESHOLD = int(os.getenv('SESSION_REFRESH_THRESHOLD', 300))  # 5 minutes
    SESSION_REMEMBER_ME_DURATION = int(os.getenv('SESSION_REMEMBER_ME_DURATION', 604800))  # 7 days
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '100/hour')
    RATE_LIMIT_LOGIN = os.getenv('RATE_LIMIT_LOGIN', '10/minute')
    RATE_LIMIT_REGISTER = os.getenv('RATE_LIMIT_REGISTER', '5/minute')
    RATE_LIMIT_PASSWORD_RESET = os.getenv('RATE_LIMIT_PASSWORD_RESET', '3/minute')
    
    # Brute Force Protection Configuration
    BRUTE_FORCE_PROTECTION_ENABLED = os.getenv('BRUTE_FORCE_PROTECTION_ENABLED', 'true').lower() == 'true'
    BRUTE_FORCE_MAX_LOGIN_ATTEMPTS = int(os.getenv('BRUTE_FORCE_MAX_LOGIN_ATTEMPTS', 5))
    BRUTE_FORCE_LOGIN_LOCKOUT_DURATION = int(os.getenv('BRUTE_FORCE_LOGIN_LOCKOUT_DURATION', 300))  # 5 minutes
    BRUTE_FORCE_LOGIN_WINDOW_SIZE = int(os.getenv('BRUTE_FORCE_LOGIN_WINDOW_SIZE', 900))  # 15 minutes
    
    BRUTE_FORCE_MAX_ASSESSMENT_ATTEMPTS = int(os.getenv('BRUTE_FORCE_MAX_ASSESSMENT_ATTEMPTS', 10))
    BRUTE_FORCE_ASSESSMENT_LOCKOUT_DURATION = int(os.getenv('BRUTE_FORCE_ASSESSMENT_LOCKOUT_DURATION', 600))  # 10 minutes
    BRUTE_FORCE_ASSESSMENT_WINDOW_SIZE = int(os.getenv('BRUTE_FORCE_ASSESSMENT_WINDOW_SIZE', 3600))  # 1 hour
    
    BRUTE_FORCE_MAX_PASSWORD_RESET_ATTEMPTS = int(os.getenv('BRUTE_FORCE_MAX_PASSWORD_RESET_ATTEMPTS', 3))
    BRUTE_FORCE_PASSWORD_RESET_LOCKOUT_DURATION = int(os.getenv('BRUTE_FORCE_PASSWORD_RESET_LOCKOUT_DURATION', 1800))  # 30 minutes
    BRUTE_FORCE_PASSWORD_RESET_WINDOW_SIZE = int(os.getenv('BRUTE_FORCE_PASSWORD_RESET_WINDOW_SIZE', 3600))  # 1 hour
    
    # Progressive Lockout Configuration
    BRUTE_FORCE_PROGRESSIVE_LOCKOUT_ENABLED = os.getenv('BRUTE_FORCE_PROGRESSIVE_LOCKOUT_ENABLED', 'true').lower() == 'true'
    BRUTE_FORCE_PROGRESSIVE_MULTIPLIER = float(os.getenv('BRUTE_FORCE_PROGRESSIVE_MULTIPLIER', 2.0))
    BRUTE_FORCE_MAX_LOCKOUT_DURATION = int(os.getenv('BRUTE_FORCE_MAX_LOCKOUT_DURATION', 86400))  # 24 hours
    
    # Security Features Configuration
    BRUTE_FORCE_REQUIRE_CAPTCHA_AFTER = int(os.getenv('BRUTE_FORCE_REQUIRE_CAPTCHA_AFTER', 3))
    BRUTE_FORCE_REQUIRE_EMAIL_VERIFICATION_AFTER = int(os.getenv('BRUTE_FORCE_REQUIRE_EMAIL_VERIFICATION_AFTER', 10))
    BRUTE_FORCE_SUSPICIOUS_ACTIVITY_THRESHOLD = int(os.getenv('BRUTE_FORCE_SUSPICIOUS_ACTIVITY_THRESHOLD', 20))
    
    # Password Security Configuration
    PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_REQUIRE_UPPERCASE = os.getenv('PASSWORD_REQUIRE_UPPERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_LOWERCASE = os.getenv('PASSWORD_REQUIRE_LOWERCASE', 'true').lower() == 'true'
    PASSWORD_REQUIRE_NUMBERS = os.getenv('PASSWORD_REQUIRE_NUMBERS', 'true').lower() == 'true'
    PASSWORD_REQUIRE_SPECIAL_CHARS = os.getenv('PASSWORD_REQUIRE_SPECIAL_CHARS', 'true').lower() == 'true'
    PASSWORD_HISTORY_SIZE = int(os.getenv('PASSWORD_HISTORY_SIZE', 5))
    
    # Token Security Configuration
    TOKEN_BLACKLIST_ENABLED = os.getenv('TOKEN_BLACKLIST_ENABLED', 'true').lower() == 'true'
    TOKEN_BLACKLIST_CLEANUP_INTERVAL = int(os.getenv('TOKEN_BLACKLIST_CLEANUP_INTERVAL', 3600))  # 1 hour
    TOKEN_BLACKLIST_MAX_SIZE = int(os.getenv('TOKEN_BLACKLIST_MAX_SIZE', 10000))
    
    # Subscription Tier Configuration
    SUBSCRIPTION_TIERS = {
        'free': {
            'name': 'Free',
            'max_assessments_per_month': 3,
            'max_storage_mb': 100,
            'features': ['basic_assessments', 'email_support']
        },
        'basic': {
            'name': 'Basic',
            'max_assessments_per_month': 20,
            'max_storage_mb': 500,
            'features': ['basic_assessments', 'priority_support', 'export_reports']
        },
        'premium': {
            'name': 'Premium',
            'max_assessments_per_month': 100,
            'max_storage_mb': 2000,
            'features': ['advanced_assessments', 'priority_support', 'export_reports', 'api_access']
        },
        'enterprise': {
            'name': 'Enterprise',
            'max_assessments_per_month': -1,  # Unlimited
            'max_storage_mb': -1,  # Unlimited
            'features': ['all_features', 'dedicated_support', 'custom_integrations', 'white_label']
        }
    }
    
    # Security Headers Configuration
    SECURITY_HEADERS = {
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }
    
    # CORS Configuration
    CORS_ENABLED = os.getenv('CORS_ENABLED', 'true').lower() == 'true'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,https://yourdomain.com').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-Requested-With']
    CORS_EXPOSE_HEADERS = ['X-New-Token']
    CORS_SUPPORTS_CREDENTIALS = True
    
    # Redis Configuration (for session storage and rate limiting)
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_SSL = os.getenv('REDIS_SSL', 'false').lower() == 'true'
    
    # Logging Configuration
    SECURITY_LOGGING_ENABLED = os.getenv('SECURITY_LOGGING_ENABLED', 'true').lower() == 'true'
    SECURITY_LOG_LEVEL = os.getenv('SECURITY_LOG_LEVEL', 'INFO')
    SECURITY_LOG_FILE = os.getenv('SECURITY_LOG_FILE', 'logs/security.log')
    
    # Monitoring Configuration
    SECURITY_MONITORING_ENABLED = os.getenv('SECURITY_MONITORING_ENABLED', 'true').lower() == 'true'
    SECURITY_ALERT_EMAIL = os.getenv('SECURITY_ALERT_EMAIL', 'security@yourdomain.com')
    SECURITY_ALERT_WEBHOOK = os.getenv('SECURITY_ALERT_WEBHOOK', None)
    
    # Development/Testing Configuration
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    TESTING_MODE = os.getenv('TESTING_MODE', 'false').lower() == 'true'
    
    @classmethod
    def get_jwt_config(cls) -> Dict[str, Any]:
        """Get JWT configuration"""
        return {
            'secret_key': cls.JWT_SECRET_KEY,
            'algorithm': cls.JWT_ALGORITHM,
            'access_token_expires': cls.JWT_ACCESS_TOKEN_EXPIRES,
            'refresh_token_expires': cls.JWT_REFRESH_TOKEN_EXPIRES,
            'token_rotation_threshold': cls.JWT_TOKEN_ROTATION_THRESHOLD,
            'issuer': cls.JWT_ISSUER,
            'audience': cls.JWT_AUDIENCE,
            'require_ip_validation': cls.JWT_REQUIRE_IP_VALIDATION,
            'require_user_agent_validation': cls.JWT_REQUIRE_USER_AGENT_VALIDATION
        }
    
    @classmethod
    def get_session_config(cls) -> Dict[str, Any]:
        """Get session configuration"""
        return {
            'max_concurrent_sessions': cls.MAX_CONCURRENT_SESSIONS,
            'session_timeout': cls.SESSION_TIMEOUT,
            'session_refresh_threshold': cls.SESSION_REFRESH_THRESHOLD,
            'session_remember_me_duration': cls.SESSION_REMEMBER_ME_DURATION
        }
    
    @classmethod
    def get_rate_limit_config(cls) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return {
            'enabled': cls.RATE_LIMIT_ENABLED,
            'default': cls.RATE_LIMIT_DEFAULT,
            'login': cls.RATE_LIMIT_LOGIN,
            'register': cls.RATE_LIMIT_REGISTER,
            'password_reset': cls.RATE_LIMIT_PASSWORD_RESET
        }
    
    @classmethod
    def get_brute_force_config(cls) -> Dict[str, Any]:
        """Get brute force protection configuration"""
        return {
            'enabled': cls.BRUTE_FORCE_PROTECTION_ENABLED,
            'login': {
                'max_attempts': cls.BRUTE_FORCE_MAX_LOGIN_ATTEMPTS,
                'lockout_duration': cls.BRUTE_FORCE_LOGIN_LOCKOUT_DURATION,
                'window_size': cls.BRUTE_FORCE_LOGIN_WINDOW_SIZE
            },
            'assessment': {
                'max_attempts': cls.BRUTE_FORCE_MAX_ASSESSMENT_ATTEMPTS,
                'lockout_duration': cls.BRUTE_FORCE_ASSESSMENT_LOCKOUT_DURATION,
                'window_size': cls.BRUTE_FORCE_ASSESSMENT_WINDOW_SIZE
            },
            'password_reset': {
                'max_attempts': cls.BRUTE_FORCE_MAX_PASSWORD_RESET_ATTEMPTS,
                'lockout_duration': cls.BRUTE_FORCE_PASSWORD_RESET_LOCKOUT_DURATION,
                'window_size': cls.BRUTE_FORCE_PASSWORD_RESET_WINDOW_SIZE
            },
            'progressive_lockout': {
                'enabled': cls.BRUTE_FORCE_PROGRESSIVE_LOCKOUT_ENABLED,
                'multiplier': cls.BRUTE_FORCE_PROGRESSIVE_MULTIPLIER,
                'max_duration': cls.BRUTE_FORCE_MAX_LOCKOUT_DURATION
            },
            'security_features': {
                'require_captcha_after': cls.BRUTE_FORCE_REQUIRE_CAPTCHA_AFTER,
                'require_email_verification_after': cls.BRUTE_FORCE_REQUIRE_EMAIL_VERIFICATION_AFTER,
                'suspicious_activity_threshold': cls.BRUTE_FORCE_SUSPICIOUS_ACTIVITY_THRESHOLD
            }
        }
    
    @classmethod
    def get_password_config(cls) -> Dict[str, Any]:
        """Get password security configuration"""
        return {
            'min_length': cls.PASSWORD_MIN_LENGTH,
            'require_uppercase': cls.PASSWORD_REQUIRE_UPPERCASE,
            'require_lowercase': cls.PASSWORD_REQUIRE_LOWERCASE,
            'require_numbers': cls.PASSWORD_REQUIRE_NUMBERS,
            'require_special_chars': cls.PASSWORD_REQUIRE_SPECIAL_CHARS,
            'history_size': cls.PASSWORD_HISTORY_SIZE
        }
    
    @classmethod
    def get_subscription_tier_config(cls, tier: str) -> Dict[str, Any]:
        """Get subscription tier configuration"""
        return cls.SUBSCRIPTION_TIERS.get(tier, cls.SUBSCRIPTION_TIERS['free'])
    
    @classmethod
    def get_all_subscription_tiers(cls) -> Dict[str, Any]:
        """Get all subscription tier configurations"""
        return cls.SUBSCRIPTION_TIERS
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return any errors"""
        errors = []
        
        # Validate JWT secret key
        if cls.JWT_SECRET_KEY == 'your-super-secret-jwt-key-change-in-production':
            errors.append('JWT_SECRET_KEY must be changed from default value')
        
        # Validate token expiry times
        if cls.JWT_ACCESS_TOKEN_EXPIRES <= 0:
            errors.append('JWT_ACCESS_TOKEN_EXPIRES must be positive')
        
        if cls.JWT_REFRESH_TOKEN_EXPIRES <= cls.JWT_ACCESS_TOKEN_EXPIRES:
            errors.append('JWT_REFRESH_TOKEN_EXPIRES must be greater than JWT_ACCESS_TOKEN_EXPIRES')
        
        # Validate rate limiting
        if cls.RATE_LIMIT_ENABLED and not cls.RATE_LIMIT_DEFAULT:
            errors.append('RATE_LIMIT_DEFAULT must be set when rate limiting is enabled')
        
        # Validate brute force protection
        if cls.BRUTE_FORCE_PROTECTION_ENABLED:
            if cls.BRUTE_FORCE_MAX_LOGIN_ATTEMPTS <= 0:
                errors.append('BRUTE_FORCE_MAX_LOGIN_ATTEMPTS must be positive')
            
            if cls.BRUTE_FORCE_LOGIN_LOCKOUT_DURATION <= 0:
                errors.append('BRUTE_FORCE_LOGIN_LOCKOUT_DURATION must be positive')
        
        # Validate session configuration
        if cls.MAX_CONCURRENT_SESSIONS <= 0:
            errors.append('MAX_CONCURRENT_SESSIONS must be positive')
        
        if cls.SESSION_TIMEOUT <= 0:
            errors.append('SESSION_TIMEOUT must be positive')
        
        return errors
    
    @classmethod
    def get_environment_variables(cls) -> Dict[str, str]:
        """Get list of required environment variables"""
        return {
            'JWT_SECRET_KEY': 'Secret key for JWT token signing (required)',
            'JWT_ACCESS_TOKEN_EXPIRES': 'Access token expiry time in seconds (default: 3600)',
            'JWT_REFRESH_TOKEN_EXPIRES': 'Refresh token expiry time in seconds (default: 604800)',
            'MAX_CONCURRENT_SESSIONS': 'Maximum concurrent sessions per user (default: 3)',
            'RATE_LIMIT_ENABLED': 'Enable rate limiting (default: true)',
            'BRUTE_FORCE_PROTECTION_ENABLED': 'Enable brute force protection (default: true)',
            'REDIS_ENABLED': 'Enable Redis for session storage (default: false)',
            'REDIS_HOST': 'Redis host (default: localhost)',
            'REDIS_PORT': 'Redis port (default: 6379)',
            'CORS_ORIGINS': 'Comma-separated list of allowed CORS origins',
            'SECURITY_ALERT_EMAIL': 'Email for security alerts',
            'DEBUG_MODE': 'Enable debug mode (default: false)'
        }
