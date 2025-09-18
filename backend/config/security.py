"""
Security configuration for the Mingus application
"""

import os
import secrets
from datetime import timedelta

class SecurityConfig:
    """Security configuration settings"""
    
    # CSRF Protection
    CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY', secrets.token_hex(32))
    CSRF_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '100'))
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Data Encryption
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', secrets.token_hex(32))
    HASH_ALGORITHM = 'sha256'
    SALT_ROUNDS = 12
    
    # Session Security
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # CORS Settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_HEADERS = ['Content-Type', 'Authorization', 'X-CSRF-Token']
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    }
    
    # Input Validation
    MAX_EMAIL_LENGTH = 254
    MAX_NAME_LENGTH = 100
    MAX_PHONE_LENGTH = 15
    MAX_ANSWER_LENGTH = 1000
    MAX_ANSWERS_SIZE = 10000  # bytes
    
    # Database Security
    DB_ENCRYPTION_ENABLED = os.environ.get('DB_ENCRYPTION_ENABLED', 'True').lower() == 'true'
    DB_CONNECTION_TIMEOUT = 30
    DB_MAX_CONNECTIONS = 20
    
    # Logging Security
    LOG_SENSITIVE_DATA = os.environ.get('LOG_SENSITIVE_DATA', 'False').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Assessment Security
    ASSESSMENT_MAX_ATTEMPTS = 3
    ASSESSMENT_COOLDOWN = 300  # 5 minutes
    ASSESSMENT_DATA_RETENTION_DAYS = 365
    
    @classmethod
    def get_csrf_token(cls):
        """Generate a new CSRF token"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def validate_csrf_token(cls, token):
        """Validate CSRF token"""
        if not token:
            return False
        
        # In production, implement proper session-based CSRF validation
        # This is a simplified example
        return len(token) >= 32
    
    @classmethod
    def get_rate_limit_key(cls, client_ip):
        """Get rate limit key for client IP"""
        return f"rate_limit:{client_ip}"
    
    @classmethod
    def is_development(cls):
        """Check if running in development mode"""
        return os.environ.get('FLASK_ENV', 'production') == 'development'
    
    @classmethod
    def is_production(cls):
        """Check if running in production mode"""
        return os.environ.get('FLASK_ENV', 'production') == 'production'
