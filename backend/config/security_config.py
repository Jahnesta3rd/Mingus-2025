#!/usr/bin/env python3
"""
Security Configuration for MINGUS Assessment System
Centralized configuration for enhanced authentication and security features
"""

import os
from typing import Dict, Any, List

class SecurityConfig:
    """Security configuration settings"""
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 1
    JWT_REFRESH_EXPIRATION_DAYS = 7
    JWT_ISSUER = 'mingus-app'
    JWT_AUDIENCE = 'mingus-users'
    JWT_REQUIRE_IP_VALIDATION = True
    JWT_REQUIRE_USER_AGENT_VALIDATION = True
    JWT_TOKEN_ROTATION_ENABLED = True
    JWT_TOKEN_ROTATION_THRESHOLD_HOURS = 12
    
    # Brute Force Protection Configuration
    BRUTE_FORCE_MAX_LOGIN_ATTEMPTS = 5
    BRUTE_FORCE_LOGIN_LOCKOUT_DURATION = 300  # 5 minutes
    BRUTE_FORCE_LOGIN_WINDOW_SIZE = 900  # 15 minutes
    
    BRUTE_FORCE_MAX_ASSESSMENT_ATTEMPTS = 10
    BRUTE_FORCE_ASSESSMENT_LOCKOUT_DURATION = 600  # 10 minutes
    BRUTE_FORCE_ASSESSMENT_WINDOW_SIZE = 3600  # 1 hour
    
    BRUTE_FORCE_MAX_PASSWORD_RESET_ATTEMPTS = 3
    BRUTE_FORCE_PASSWORD_RESET_LOCKOUT_DURATION = 1800  # 30 minutes
    BRUTE_FORCE_PASSWORD_RESET_WINDOW_SIZE = 3600  # 1 hour
    
    BRUTE_FORCE_PROGRESSIVE_LOCKOUT_ENABLED = True
    BRUTE_FORCE_PROGRESSIVE_MULTIPLIER = 2.0
    BRUTE_FORCE_MAX_LOCKOUT_DURATION = 86400  # 24 hours
    
    BRUTE_FORCE_REQUIRE_CAPTCHA_AFTER = 3
    BRUTE_FORCE_REQUIRE_EMAIL_VERIFICATION_AFTER = 10
    BRUTE_FORCE_SUSPICIOUS_ACTIVITY_THRESHOLD = 20
    
    # Session Configuration
    SESSION_TIMEOUT = 3600  # 1 hour
    SESSION_REFRESH_THRESHOLD = 300  # 5 minutes
    SESSION_REMEMBER_ME_DURATION = 604800  # 7 days
    SESSION_REQUIRE_IP_VALIDATION = True
    SESSION_REQUIRE_USER_AGENT_VALIDATION = True
    SESSION_FIXATION_PROTECTION = True
    SESSION_SECURE_COOKIES = True
    SESSION_REGENERATION_INTERVAL = 3600  # 1 hour
    SESSION_MAX_CONCURRENT_SESSIONS = 3
    SESSION_MAX_SESSIONS_PER_USER = 10
    
    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    REDIS_DB_JWT = int(os.getenv('REDIS_DB_JWT', 0))
    REDIS_DB_BRUTE_FORCE = int(os.getenv('REDIS_DB_BRUTE_FORCE', 1))
    REDIS_DB_SESSIONS = int(os.getenv('REDIS_DB_SESSIONS', 2))
    
    # Security Features
    SECURITY_ENABLED = True
    MFA_ENABLED = os.getenv('MFA_ENABLED', 'false').lower() == 'true'
    MFA_REQUIRED_FOR_FINANCIAL_ACTIONS = True
    SUSPICIOUS_ACTIVITY_DETECTION = True
    PASSWORD_BREACH_DETECTION = True
    ACTIVITY_LOGGING = True
    
    # Logging Configuration
    SECURITY_LOG_RETENTION_DAYS = 90
    SECURITY_LOG_LEVEL = 'INFO'
    SECURITY_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # IP Whitelist (for trusted networks)
    IP_WHITELIST = [
        '127.0.0.1',
        '::1',
        # Add your trusted IP addresses here
    ]
    
    # User Whitelist (for admin accounts)
    USER_WHITELIST = [
        # Add admin user IDs here
    ]
    
    # Sensitive Actions (require additional security)
    SENSITIVE_ACTIONS = [
        'login',
        'logout',
        'password_change',
        'profile_update',
        'financial_data_access',
        'subscription_change',
        'mfa_setup',
        'account_lockout',
        'suspicious_activity',
        'breach_detection',
        'assessment_submission',
        'assessment_modification'
    ]
    
    # Rate Limiting Configuration
    RATE_LIMIT_LOGIN_ATTEMPTS_PER_MINUTE = 5
    RATE_LIMIT_PASSWORD_RESET_ATTEMPTS_PER_HOUR = 3
    RATE_LIMIT_MFA_ATTEMPTS_PER_MINUTE = 3
    RATE_LIMIT_REGISTRATION_ATTEMPTS_PER_HOUR = 3
    RATE_LIMIT_API_REQUESTS_PER_MINUTE = 100
    RATE_LIMIT_BURST_LIMIT = 20
    RATE_LIMIT_WINDOW_SIZE = 60  # seconds
    
    @classmethod
    def get_jwt_config(cls) -> Dict[str, Any]:
        """Get JWT configuration"""
        return {
            'secret_key': cls.JWT_SECRET_KEY,
            'algorithm': cls.JWT_ALGORITHM,
            'expiration_hours': cls.JWT_EXPIRATION_HOURS,
            'refresh_expiration_days': cls.JWT_REFRESH_EXPIRATION_DAYS,
            'issuer': cls.JWT_ISSUER,
            'audience': cls.JWT_AUDIENCE,
            'require_ip_validation': cls.JWT_REQUIRE_IP_VALIDATION,
            'require_user_agent_validation': cls.JWT_REQUIRE_USER_AGENT_VALIDATION,
            'token_rotation_enabled': cls.JWT_TOKEN_ROTATION_ENABLED,
            'token_rotation_threshold_hours': cls.JWT_TOKEN_ROTATION_THRESHOLD_HOURS
        }
    
    @classmethod
    def get_brute_force_config(cls) -> Dict[str, Any]:
        """Get brute force protection configuration"""
        return {
            'max_login_attempts': cls.BRUTE_FORCE_MAX_LOGIN_ATTEMPTS,
            'login_lockout_duration': cls.BRUTE_FORCE_LOGIN_LOCKOUT_DURATION,
            'login_window_size': cls.BRUTE_FORCE_LOGIN_WINDOW_SIZE,
            'max_assessment_attempts': cls.BRUTE_FORCE_MAX_ASSESSMENT_ATTEMPTS,
            'assessment_lockout_duration': cls.BRUTE_FORCE_ASSESSMENT_LOCKOUT_DURATION,
            'assessment_window_size': cls.BRUTE_FORCE_ASSESSMENT_WINDOW_SIZE,
            'max_password_reset_attempts': cls.BRUTE_FORCE_MAX_PASSWORD_RESET_ATTEMPTS,
            'password_reset_lockout_duration': cls.BRUTE_FORCE_PASSWORD_RESET_LOCKOUT_DURATION,
            'password_reset_window_size': cls.BRUTE_FORCE_PASSWORD_RESET_WINDOW_SIZE,
            'progressive_lockout_enabled': cls.BRUTE_FORCE_PROGRESSIVE_LOCKOUT_ENABLED,
            'progressive_multiplier': cls.BRUTE_FORCE_PROGRESSIVE_MULTIPLIER,
            'max_lockout_duration': cls.BRUTE_FORCE_MAX_LOCKOUT_DURATION,
            'require_captcha_after': cls.BRUTE_FORCE_REQUIRE_CAPTCHA_AFTER,
            'require_email_verification_after': cls.BRUTE_FORCE_REQUIRE_EMAIL_VERIFICATION_AFTER,
            'suspicious_activity_threshold': cls.BRUTE_FORCE_SUSPICIOUS_ACTIVITY_THRESHOLD,
            'redis_host': cls.REDIS_HOST,
            'redis_port': cls.REDIS_PORT,
            'redis_db': cls.REDIS_DB_BRUTE_FORCE,
            'redis_password': cls.REDIS_PASSWORD,
            'ip_whitelist': cls.IP_WHITELIST,
            'user_whitelist': cls.USER_WHITELIST
        }
    
    @classmethod
    def get_session_config(cls) -> Dict[str, Any]:
        """Get session configuration"""
        return {
            'session_timeout': cls.SESSION_TIMEOUT,
            'session_refresh_threshold': cls.SESSION_REFRESH_THRESHOLD,
            'remember_me_duration': cls.SESSION_REMEMBER_ME_DURATION,
            'require_ip_validation': cls.SESSION_REQUIRE_IP_VALIDATION,
            'require_user_agent_validation': cls.SESSION_REQUIRE_USER_AGENT_VALIDATION,
            'session_fixation_protection': cls.SESSION_FIXATION_PROTECTION,
            'secure_session_cookies': cls.SESSION_SECURE_COOKIES,
            'session_regeneration_interval': cls.SESSION_REGENERATION_INTERVAL,
            'max_concurrent_sessions': cls.SESSION_MAX_CONCURRENT_SESSIONS,
            'max_sessions_per_user': cls.SESSION_MAX_SESSIONS_PER_USER,
            'redis_host': cls.REDIS_HOST,
            'redis_port': cls.REDIS_PORT,
            'redis_db': cls.REDIS_DB_SESSIONS,
            'redis_password': cls.REDIS_PASSWORD,
            'track_session_activity': cls.ACTIVITY_LOGGING,
            'log_session_events': cls.ACTIVITY_LOGGING
        }
    
    @classmethod
    def get_rate_limit_config(cls) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return {
            'login_attempts_per_minute': cls.RATE_LIMIT_LOGIN_ATTEMPTS_PER_MINUTE,
            'password_reset_attempts_per_hour': cls.RATE_LIMIT_PASSWORD_RESET_ATTEMPTS_PER_HOUR,
            'mfa_attempts_per_minute': cls.RATE_LIMIT_MFA_ATTEMPTS_PER_MINUTE,
            'registration_attempts_per_hour': cls.RATE_LIMIT_REGISTRATION_ATTEMPTS_PER_HOUR,
            'api_requests_per_minute': cls.RATE_LIMIT_API_REQUESTS_PER_MINUTE,
            'burst_limit': cls.RATE_LIMIT_BURST_LIMIT,
            'window_size': cls.RATE_LIMIT_WINDOW_SIZE
        }
    
    @classmethod
    def get_security_features(cls) -> Dict[str, Any]:
        """Get security features configuration"""
        return {
            'security_enabled': cls.SECURITY_ENABLED,
            'mfa_enabled': cls.MFA_ENABLED,
            'mfa_required_for_financial_actions': cls.MFA_REQUIRED_FOR_FINANCIAL_ACTIONS,
            'suspicious_activity_detection': cls.SUSPICIOUS_ACTIVITY_DETECTION,
            'password_breach_detection': cls.PASSWORD_BREACH_DETECTION,
            'activity_logging': cls.ACTIVITY_LOGGING,
            'sensitive_actions': cls.SENSITIVE_ACTIONS
        }
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'log_retention_days': cls.SECURITY_LOG_RETENTION_DAYS,
            'log_level': cls.SECURITY_LOG_LEVEL,
            'log_format': cls.SECURITY_LOG_FORMAT
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate security configuration"""
        issues = []
        
        # Check JWT secret
        if cls.JWT_SECRET_KEY == 'your-super-secret-jwt-key-change-in-production':
            issues.append("JWT_SECRET_KEY should be changed in production")
        
        # Check Redis configuration
        if not cls.REDIS_HOST:
            issues.append("REDIS_HOST is required")
        
        # Check timeout values
        if cls.SESSION_TIMEOUT < 300:
            issues.append("SESSION_TIMEOUT should be at least 5 minutes")
        
        if cls.BRUTE_FORCE_LOGIN_LOCKOUT_DURATION < 60:
            issues.append("BRUTE_FORCE_LOGIN_LOCKOUT_DURATION should be at least 60 seconds")
        
        # Check attempt limits
        if cls.BRUTE_FORCE_MAX_LOGIN_ATTEMPTS < 1:
            issues.append("BRUTE_FORCE_MAX_LOGIN_ATTEMPTS must be at least 1")
        
        if cls.BRUTE_FORCE_MAX_ASSESSMENT_ATTEMPTS < 1:
            issues.append("BRUTE_FORCE_MAX_ASSESSMENT_ATTEMPTS must be at least 1")
        
        return issues

# Environment-specific configurations
class DevelopmentSecurityConfig(SecurityConfig):
    """Development environment security configuration"""
    JWT_SECRET_KEY = 'dev-secret-key-change-in-production'
    REDIS_HOST = 'localhost'
    MFA_ENABLED = False
    SUSPICIOUS_ACTIVITY_DETECTION = False
    PASSWORD_BREACH_DETECTION = False
    ACTIVITY_LOGGING = True

class ProductionSecurityConfig(SecurityConfig):
    """Production environment security configuration"""
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    MFA_ENABLED = True
    SUSPICIOUS_ACTIVITY_DETECTION = True
    PASSWORD_BREACH_DETECTION = True
    ACTIVITY_LOGGING = True
    SESSION_SECURE_COOKIES = True

class TestingSecurityConfig(SecurityConfig):
    """Testing environment security configuration"""
    JWT_SECRET_KEY = 'test-secret-key'
    REDIS_HOST = 'localhost'
    MFA_ENABLED = False
    SUSPICIOUS_ACTIVITY_DETECTION = False
    PASSWORD_BREACH_DETECTION = False
    ACTIVITY_LOGGING = False
    BRUTE_FORCE_MAX_LOGIN_ATTEMPTS = 100  # Higher limit for testing

def get_security_config(environment: str = None) -> SecurityConfig:
    """Get security configuration for the specified environment"""
    if not environment:
        environment = os.getenv('FLASK_ENV', 'development')
    
    configs = {
        'development': DevelopmentSecurityConfig,
        'production': ProductionSecurityConfig,
        'testing': TestingSecurityConfig
    }
    
    return configs.get(environment, SecurityConfig)
