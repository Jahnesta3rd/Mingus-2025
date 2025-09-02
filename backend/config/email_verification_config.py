"""
Email Verification System Configuration
Comprehensive configuration management for the MINGUS email verification system

This module provides environment-specific configuration for:
- Token generation and validation
- Rate limiting and security
- Email templates and delivery
- Integration with existing services
"""

import os
import secrets
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class EmailVerificationConfig:
    """Configuration class for email verification system"""
    
    # ============================================================================
    # TOKEN SECURITY CONFIGURATION
    # ============================================================================
    
    # Secret key for HMAC token generation (CRITICAL: Must be cryptographically secure)
    # This should be a 64+ character random string, different for each environment
    EMAIL_VERIFICATION_SECRET: str
    
    # Token length in bytes (64 = 512 bits, cryptographically secure)
    EMAIL_VERIFICATION_TOKEN_LENGTH: int = 64
    
    # Token expiration time in hours
    # Development: 24 hours, Production: 24 hours, Staging: 12 hours
    EMAIL_VERIFICATION_EXPIRY_HOURS: int = 24
    
    # Maximum token age before requiring regeneration (in hours)
    EMAIL_VERIFICATION_MAX_TOKEN_AGE_HOURS: int = 48
    
    # ============================================================================
    # RATE LIMITING CONFIGURATION
    # ============================================================================
    
    # Maximum verification attempts per hour per IP address
    # Prevents brute force attacks on verification tokens
    EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR: int = 10
    
    # Maximum verification attempts per hour per user
    # Additional protection for authenticated users
    EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_USER_HOUR: int = 5
    
    # Maximum resend attempts per day per user
    # Prevents email spam and abuse
    EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS_PER_DAY: int = 5
    
    # Cooldown period between resend attempts (in hours)
    # Prevents rapid-fire resend requests
    EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS: int = 1
    
    # Maximum failed verification attempts before account lockout
    # Protects against brute force attacks
    EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS: int = 5
    
    # Account lockout duration after max failed attempts (in hours)
    # Temporary lockout to prevent continued attacks
    EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS: int = 1
    
    # ============================================================================
    # EMAIL CONFIGURATION
    # ============================================================================
    
    # Email service configuration (inherits from existing Resend setup)
    EMAIL_SERVICE_PROVIDER: str = "resend"
    
    # Email template directory path
    EMAIL_TEMPLATE_DIR: str = "backend/templates"
    
    # Default sender email address
    EMAIL_DEFAULT_FROM: str = "noreply@mingus.app"
    
    # Reply-to email address for support
    EMAIL_REPLY_TO: str = "support@mingus.app"
    
    # Email subject line prefix
    EMAIL_SUBJECT_PREFIX: str = "Mingus - "
    
    # Maximum email size in bytes (for template validation)
    EMAIL_MAX_SIZE_BYTES: int = 1024 * 1024  # 1MB
    
    # ============================================================================
    # REMINDER SYSTEM CONFIGURATION
    # ============================================================================
    
    # Enable automatic reminder system
    EMAIL_VERIFICATION_ENABLE_REMINDERS: bool = True
    
    # Reminder schedule in days after signup
    # Format: comma-separated list of days
    EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS: str = "3,7,14"
    
    # Maximum reminders per user
    EMAIL_VERIFICATION_MAX_REMINDERS_PER_USER: int = 3
    
    # Reminder email template names
    EMAIL_VERIFICATION_REMINDER_TEMPLATES: Dict[str, str] = None
    
    # ============================================================================
    # AUDIT AND MONITORING CONFIGURATION
    # ============================================================================
    
    # Enable comprehensive audit logging
    EMAIL_VERIFICATION_ENABLE_AUDIT_LOGGING: bool = True
    
    # Audit log retention period in days
    EMAIL_VERIFICATION_AUDIT_LOG_RETENTION_DAYS: int = 90
    
    # Enable performance monitoring
    EMAIL_VERIFICATION_ENABLE_MONITORING: bool = True
    
    # Metrics collection interval in minutes
    EMAIL_VERIFICATION_METRICS_INTERVAL_MINUTES: int = 15
    
    # ============================================================================
    # INTEGRATION CONFIGURATION
    # ============================================================================
    
    # Frontend URL for verification links
    # Must be HTTPS in production
    FRONTEND_URL: str
    
    # API base URL for verification endpoints
    API_BASE_URL: str
    
    # Redis configuration for rate limiting
    REDIS_URL: str
    
    # Database connection string (inherits from existing config)
    DATABASE_URL: str
    
    # Celery broker URL for background tasks
    CELERY_BROKER_URL: str
    
    # ============================================================================
    # SECURITY ADVANCED CONFIGURATION
    # ============================================================================
    
    # Enable IP address tracking for security
    EMAIL_VERIFICATION_TRACK_IP_ADDRESSES: bool = True
    
    # Enable User-Agent tracking for security
    EMAIL_VERIFICATION_TRACK_USER_AGENTS: bool = True
    
    # Enable geolocation tracking (if available)
    EMAIL_VERIFICATION_TRACK_GEO_LOCATION: bool = False
    
    # Maximum concurrent verification sessions per user
    EMAIL_VERIFICATION_MAX_CONCURRENT_SESSIONS: int = 3
    
    # Session timeout in hours
    EMAIL_VERIFICATION_SESSION_TIMEOUT_HOURS: int = 24
    
    # ============================================================================
    # DEVELOPMENT AND TESTING CONFIGURATION
    # ============================================================================
    
    # Enable debug mode (development only)
    EMAIL_VERIFICATION_DEBUG: bool = False
    
    # Enable test mode for automated testing
    EMAIL_VERIFICATION_TEST_MODE: bool = False
    
    # Test email override (development only)
    EMAIL_VERIFICATION_TEST_EMAIL: Optional[str] = None
    
    # Mock email service for testing
    EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_configuration()
        self._setup_reminder_templates()
    
    def _validate_configuration(self):
        """Validate configuration values for security and correctness"""
        errors = []
        
        # Validate token security
        if len(self.EMAIL_VERIFICATION_SECRET) < 32:
            errors.append("EMAIL_VERIFICATION_SECRET must be at least 32 characters long")
        
        if self.EMAIL_VERIFICATION_TOKEN_LENGTH < 32:
            errors.append("EMAIL_VERIFICATION_TOKEN_LENGTH must be at least 32 bytes")
        
        # Validate rate limiting
        if self.EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR < 1:
            errors.append("EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR must be at least 1")
        
        if self.EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS < 1:
            errors.append("EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS must be at least 1")
        
        # Validate email configuration
        if not self.FRONTEND_URL.startswith(('http://', 'https://')):
            errors.append("FRONTEND_URL must be a valid HTTP/HTTPS URL")
        
        if self.EMAIL_VERIFICATION_DEBUG and self.EMAIL_VERIFICATION_DEBUG != 'development':
            errors.append("EMAIL_VERIFICATION_DEBUG should only be enabled in development")
        
        # Validate reminder schedule
        try:
            reminder_days = [int(d.strip()) for d in self.EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS.split(',')]
            if not all(1 <= day <= 30 for day in reminder_days):
                errors.append("Reminder schedule days must be between 1 and 30")
        except ValueError:
            errors.append("Reminder schedule must be comma-separated integers")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _setup_reminder_templates(self):
        """Setup reminder email template configuration"""
        if self.EMAIL_VERIFICATION_REMINDER_TEMPLATES is None:
            self.EMAIL_VERIFICATION_REMINDER_TEMPLATES = {
                'first': 'verification_reminder.html',
                'second': 'verification_reminder.html',
                'final': 'verification_reminder.html'
            }
    
    def get_reminder_schedule_days(self) -> list:
        """Get reminder schedule as list of integers"""
        return [int(d.strip()) for d in self.EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS.split(',')]
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv('FLASK_ENV') == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return os.getenv('FLASK_ENV') == 'development'
    
    def is_staging(self) -> bool:
        """Check if running in staging environment"""
        return os.getenv('FLASK_ENV') == 'staging'
    
    def get_token_expiry_timedelta(self) -> timedelta:
        """Get token expiry as timedelta"""
        return timedelta(hours=self.EMAIL_VERIFICATION_EXPIRY_HOURS)
    
    def get_lockout_timedelta(self) -> timedelta:
        """Get lockout duration as timedelta"""
        return timedelta(hours=self.EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS)
    
    def get_resend_cooldown_timedelta(self) -> timedelta:
        """Get resend cooldown as timedelta"""
        return timedelta(hours=self.EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS)

def load_email_verification_config() -> EmailVerificationConfig:
    """
    Load email verification configuration from environment variables
    
    Returns:
        EmailVerificationConfig: Configured instance
        
    Raises:
        ValueError: If required configuration is missing or invalid
    """
    
    # Get environment
    env = os.getenv('FLASK_ENV', 'development')
    
    # Load configuration based on environment
    if env == 'production':
        return _load_production_config()
    elif env == 'staging':
        return _load_staging_config()
    else:
        return _load_development_config()

def _load_production_config() -> EmailVerificationConfig:
    """Load production configuration with strict security settings"""
    
    # Validate required production variables
    required_vars = [
        'EMAIL_VERIFICATION_SECRET',
        'FRONTEND_URL',
        'API_BASE_URL',
        'REDIS_URL',
        'DATABASE_URL',
        'CELERY_BROKER_URL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required production environment variables: {missing_vars}")
    
    # Production configuration with enhanced security
    return EmailVerificationConfig(
        # Token security (production: maximum security)
        EMAIL_VERIFICATION_SECRET=os.getenv('EMAIL_VERIFICATION_SECRET'),
        EMAIL_VERIFICATION_TOKEN_LENGTH=64,
        EMAIL_VERIFICATION_EXPIRY_HOURS=24,
        EMAIL_VERIFICATION_MAX_TOKEN_AGE_HOURS=48,
        
        # Rate limiting (production: strict limits)
        EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR=5,
        EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_USER_HOUR=3,
        EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS_PER_DAY=3,
        EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS=2,
        EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS=3,
        EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS=2,
        
        # Email configuration
        EMAIL_DEFAULT_FROM=os.getenv('EMAIL_DEFAULT_FROM', 'noreply@mingus.app'),
        EMAIL_REPLY_TO=os.getenv('EMAIL_REPLY_TO', 'support@mingus.app'),
        EMAIL_SUBJECT_PREFIX="Mingus - ",
        
        # Reminder system (production: conservative)
        EMAIL_VERIFICATION_ENABLE_REMINDERS=True,
        EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS="7,14",
        EMAIL_VERIFICATION_MAX_REMINDERS_PER_USER=2,
        
        # Audit and monitoring (production: comprehensive)
        EMAIL_VERIFICATION_ENABLE_AUDIT_LOGGING=True,
        EMAIL_VERIFICATION_AUDIT_LOG_RETENTION_DAYS=365,
        EMAIL_VERIFICATION_ENABLE_MONITORING=True,
        EMAIL_VERIFICATION_METRICS_INTERVAL_MINUTES=5,
        
        # Integration
        FRONTEND_URL=os.getenv('FRONTEND_URL'),
        API_BASE_URL=os.getenv('API_BASE_URL'),
        REDIS_URL=os.getenv('REDIS_URL'),
        DATABASE_URL=os.getenv('DATABASE_URL'),
        CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL'),
        
        # Security (production: maximum tracking)
        EMAIL_VERIFICATION_TRACK_IP_ADDRESSES=True,
        EMAIL_VERIFICATION_TRACK_USER_AGENTS=True,
        EMAIL_VERIFICATION_TRACK_GEO_LOCATION=True,
        EMAIL_VERIFICATION_MAX_CONCURRENT_SESSIONS=2,
        EMAIL_VERIFICATION_SESSION_TIMEOUT_HOURS=12,
        
        # Development settings (production: disabled)
        EMAIL_VERIFICATION_DEBUG=False,
        EMAIL_VERIFICATION_TEST_MODE=False,
        EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE=False
    )

def _load_staging_config() -> EmailVerificationConfig:
    """Load staging configuration with moderate security settings"""
    
    # Staging configuration (similar to production but with some debugging)
    return EmailVerificationConfig(
        # Token security (staging: high security)
        EMAIL_VERIFICATION_SECRET=os.getenv('EMAIL_VERIFICATION_SECRET', _generate_dev_secret()),
        EMAIL_VERIFICATION_TOKEN_LENGTH=64,
        EMAIL_VERIFICATION_EXPIRY_HOURS=12,  # Shorter for testing
        EMAIL_VERIFICATION_MAX_TOKEN_AGE_HOURS=24,
        
        # Rate limiting (staging: moderate limits)
        EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR=10,
        EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_USER_HOUR=5,
        EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS_PER_DAY=5,
        EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS=1,
        EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS=5,
        EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS=1,
        
        # Email configuration
        EMAIL_DEFAULT_FROM=os.getenv('EMAIL_DEFAULT_FROM', 'noreply@staging.mingus.app'),
        EMAIL_REPLY_TO=os.getenv('EMAIL_REPLY_TO', 'support@staging.mingus.app'),
        EMAIL_SUBJECT_PREFIX="[STAGING] Mingus - ",
        
        # Reminder system (staging: full testing)
        EMAIL_VERIFICATION_ENABLE_REMINDERS=True,
        EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS="1,3,7",  # Faster for testing
        EMAIL_VERIFICATION_MAX_REMINDERS_PER_USER=3,
        
        # Audit and monitoring (staging: comprehensive)
        EMAIL_VERIFICATION_ENABLE_AUDIT_LOGGING=True,
        EMAIL_VERIFICATION_AUDIT_LOG_RETENTION_DAYS=30,
        EMAIL_VERIFICATION_ENABLE_MONITORING=True,
        EMAIL_VERIFICATION_METRICS_INTERVAL_MINUTES=10,
        
        # Integration
        FRONTEND_URL=os.getenv('FRONTEND_URL', 'https://staging.mingus.app'),
        API_BASE_URL=os.getenv('API_BASE_URL', 'https://api.staging.mingus.app'),
        REDIS_URL=os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        DATABASE_URL=os.getenv('DATABASE_URL', 'postgresql://localhost:5432/mingus_staging'),
        CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/2'),
        
        # Security (staging: moderate tracking)
        EMAIL_VERIFICATION_TRACK_IP_ADDRESSES=True,
        EMAIL_VERIFICATION_TRACK_USER_AGENTS=True,
        EMAIL_VERIFICATION_TRACK_GEO_LOCATION=False,
        EMAIL_VERIFICATION_MAX_CONCURRENT_SESSIONS=3,
        EMAIL_VERIFICATION_SESSION_TIMEOUT_HOURS=24,
        
        # Development settings (staging: some debugging)
        EMAIL_VERIFICATION_DEBUG=False,
        EMAIL_VERIFICATION_TEST_MODE=False,
        EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE=False
    )

def _load_development_config() -> EmailVerificationConfig:
    """Load development configuration with relaxed security for testing"""
    
    # Development configuration (relaxed security for testing)
    return EmailVerificationConfig(
        # Token security (development: adequate security)
        EMAIL_VERIFICATION_SECRET=os.getenv('EMAIL_VERIFICATION_SECRET', _generate_dev_secret()),
        EMAIL_VERIFICATION_TOKEN_LENGTH=32,  # Shorter for development
        EMAIL_VERIFICATION_EXPIRY_HOURS=24,
        EMAIL_VERIFICATION_MAX_TOKEN_AGE_HOURS=48,
        
        # Rate limiting (development: relaxed limits)
        EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_HOUR=50,
        EMAIL_VERIFICATION_MAX_ATTEMPTS_PER_USER_HOUR=20,
        EMAIL_VERIFICATION_MAX_RESEND_ATTEMPTS_PER_DAY=10,
        EMAIL_VERIFICATION_RESEND_COOLDOWN_HOURS=0,  # No cooldown in development
        EMAIL_VERIFICATION_MAX_FAILED_ATTEMPTS=10,
        EMAIL_VERIFICATION_LOCKOUT_DURATION_HOURS=0,  # No lockout in development
        
        # Email configuration
        EMAIL_DEFAULT_FROM=os.getenv('EMAIL_DEFAULT_FROM', 'dev@localhost'),
        EMAIL_REPLY_TO=os.getenv('EMAIL_REPLY_TO', 'dev@localhost'),
        EMAIL_SUBJECT_PREFIX="[DEV] Mingus - ",
        
        # Reminder system (development: fast testing)
        EMAIL_VERIFICATION_ENABLE_REMINDERS=True,
        EMAIL_VERIFICATION_REMINDER_SCHEDULE_DAYS="0,1,2",  # Very fast for testing
        EMAIL_VERIFICATION_MAX_REMINDERS_PER_USER=5,
        
        # Audit and monitoring (development: basic)
        EMAIL_VERIFICATION_ENABLE_AUDIT_LOGGING=True,
        EMAIL_VERIFICATION_AUDIT_LOG_RETENTION_DAYS=7,
        EMAIL_VERIFICATION_ENABLE_MONITORING=False,
        EMAIL_VERIFICATION_METRICS_INTERVAL_MINUTES=60,
        
        # Integration
        FRONTEND_URL=os.getenv('FRONTEND_URL', 'http://localhost:3000'),
        API_BASE_URL=os.getenv('API_BASE_URL', 'http://localhost:5000'),
        REDIS_URL=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        DATABASE_URL=os.getenv('DATABASE_URL', 'postgresql://localhost:5432/mingus_dev'),
        CELERY_BROKER_URL=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
        
        # Security (development: minimal tracking)
        EMAIL_VERIFICATION_TRACK_IP_ADDRESSES=False,
        EMAIL_VERIFICATION_TRACK_USER_AGENTS=False,
        EMAIL_VERIFICATION_TRACK_GEO_LOCATION=False,
        EMAIL_VERIFICATION_MAX_CONCURRENT_SESSIONS=10,
        EMAIL_VERIFICATION_SESSION_TIMEOUT_HOURS=48,
        
        # Development settings (development: enabled)
        EMAIL_VERIFICATION_DEBUG=True,
        EMAIL_VERIFICATION_TEST_MODE=True,
        EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE=os.getenv('EMAIL_VERIFICATION_MOCK_EMAIL_SERVICE', 'true').lower() == 'true',
        EMAIL_VERIFICATION_TEST_EMAIL=os.getenv('EMAIL_VERIFICATION_TEST_EMAIL')
    )

def _generate_dev_secret() -> str:
    """Generate a secure secret for development environments"""
    return secrets.token_urlsafe(64)

def validate_environment_setup() -> Dict[str, Any]:
    """
    Validate that all required environment variables are set
    
    Returns:
        Dict[str, Any]: Validation results with status and details
    """
    
    validation_results = {
        'status': 'PASS',
        'errors': [],
        'warnings': [],
        'environment': os.getenv('FLASK_ENV', 'development'),
        'checks': {}
    }
    
    try:
        # Try to load configuration
        config = load_email_verification_config()
        validation_results['checks']['configuration_loading'] = 'PASS'
        
        # Validate critical security settings
        if len(config.EMAIL_VERIFICATION_SECRET) < 32:
            validation_results['errors'].append("EMAIL_VERIFICATION_SECRET is too short")
            validation_results['status'] = 'FAIL'
        
        if config.EMAIL_VERIFICATION_TOKEN_LENGTH < 32:
            validation_results['warnings'].append("Token length is below recommended security level")
        
        # Validate email service integration
        if not config.EMAIL_DEFAULT_FROM:
            validation_results['warnings'].append("EMAIL_DEFAULT_FROM not set")
        
        # Validate frontend URL
        if not config.FRONTEND_URL.startswith(('http://', 'https://')):
            validation_results['errors'].append("Invalid FRONTEND_URL format")
            validation_results['status'] = 'FAIL'
        
        # Production-specific validations
        if config.is_production():
            if not config.FRONTEND_URL.startswith('https://'):
                validation_results['errors'].append("Production FRONTEND_URL must use HTTPS")
                validation_results['status'] = 'FAIL'
            
            if config.EMAIL_VERIFICATION_DEBUG:
                validation_results['errors'].append("Debug mode should not be enabled in production")
                validation_results['status'] = 'FAIL'
        
        validation_results['checks']['security_validation'] = 'PASS'
        
    except Exception as e:
        validation_results['errors'].append(f"Configuration validation failed: {str(e)}")
        validation_results['status'] = 'FAIL'
        validation_results['checks']['configuration_loading'] = 'FAIL'
    
    return validation_results

# Global configuration instance
email_verification_config = None

def get_config() -> EmailVerificationConfig:
    """Get the global email verification configuration instance"""
    global email_verification_config
    
    if email_verification_config is None:
        email_verification_config = load_email_verification_config()
    
    return email_verification_config

def reload_config():
    """Reload configuration from environment variables"""
    global email_verification_config
    email_verification_config = None
    return get_config()
