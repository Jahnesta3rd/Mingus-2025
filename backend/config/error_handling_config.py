"""
Configuration for error handling, logging, and monitoring in the Mingus application.
Centralizes all settings for easy management across environments.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class LoggingConfig:
    """Configuration for the logging system."""
    
    # Basic logging settings
    app_name: str = "mingus"
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    # Log file settings
    max_log_size: int = 100 * 1024 * 1024  # 100MB
    backup_count: int = 10
    
    # Output settings
    enable_console: bool = True
    enable_file: bool = True
    enable_sentry: bool = False
    
    # Sentry configuration
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1
    sentry_profiles_sample_rate: float = 0.1
    
    # Log formatting
    json_format: bool = True
    include_timestamp: bool = True
    include_level: bool = True
    include_logger: bool = True
    include_module: bool = True
    include_function: bool = True
    include_line: bool = True
    include_process: bool = True
    include_thread: bool = True
    
    # Privacy and security
    redact_sensitive_data: bool = True
    sensitive_fields: set = field(default_factory=lambda: {
        'password', 'token', 'secret', 'key', 'api_key', 'private_key',
        'credit_card', 'ssn', 'social_security', 'account_number',
        'routing_number', 'pin', 'cvv', 'expiry', 'cvv2', 'cvc',
        'card_number', 'cardholder_name', 'billing_address'
    })
    
    def __post_init__(self):
        """Set environment-specific defaults."""
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            self.log_level = "WARNING"
            self.enable_console = False
            self.enable_file = True
            self.enable_sentry = True
            self.json_format = True
            self.include_module = False
            self.include_function = False
            self.include_line = False
            self.include_process = False
            self.include_thread = False
        elif env == 'staging':
            self.log_level = "INFO"
            self.enable_console = True
            self.enable_file = True
            self.enable_sentry = True
            self.json_format = True
            self.include_line = False
            self.include_process = False
            self.include_thread = False
        else:  # development
            self.log_level = "DEBUG"
            self.enable_console = True
            self.enable_file = True
            self.enable_sentry = False
            self.json_format = False
            self.include_module = True
            self.include_function = True
            self.include_line = True
            self.include_process = True
            self.include_thread = True


@dataclass
class ErrorHandlingConfig:
    """Configuration for error handling."""
    
    # Error response settings
    include_error_id: bool = True
    include_timestamp: bool = True
    include_request_id: bool = True
    
    # Development mode settings
    include_debug_info: bool = False
    include_traceback: bool = False
    include_error_class: bool = False
    
    # Security settings
    sanitize_error_context: bool = True
    redact_sensitive_data: bool = True
    
    # User message settings
    user_friendly_messages: bool = True
    cultural_appropriateness: bool = True
    
    # Error categorization
    categorize_errors: bool = True
    severity_levels: bool = True
    
    def __post_init__(self):
        """Set environment-specific defaults."""
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            self.include_debug_info = False
            self.include_traceback = False
            self.include_error_class = False
        elif env == 'staging':
            self.include_debug_info = False
            self.include_traceback = False
            self.include_error_class = True
        else:  # development
            self.include_debug_info = True
            self.include_traceback = True
            self.include_error_class = True


@dataclass
class MonitoringConfig:
    """Configuration for monitoring and alerting."""
    
    # Basic monitoring settings
    enabled: bool = True
    app_name: str = "mingus"
    
    # Error tracking
    track_errors: bool = True
    error_window_size: int = 3600  # 1 hour
    max_error_events: int = 10000
    
    # Performance monitoring
    track_performance: bool = True
    performance_window_size: int = 300  # 5 minutes
    max_performance_metrics: int = 10000
    
    # System monitoring
    track_system_metrics: bool = True
    system_metrics_interval: int = 30  # seconds
    
    # Alerting
    enable_alerts: bool = True
    alert_check_interval: int = 30  # seconds
    
    # Alert thresholds
    error_rate_threshold: float = 0.1  # 10% error rate
    memory_usage_threshold: float = 80.0  # 80% memory usage
    cpu_usage_threshold: float = 80.0  # 80% CPU usage
    disk_usage_threshold: float = 90.0  # 90% disk usage
    response_time_threshold: float = 2.0  # 2 seconds
    
    # Redis integration
    use_redis: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Health check settings
    health_check_enabled: bool = True
    health_check_interval: int = 60  # seconds
    health_check_timeout: int = 30  # seconds
    
    def __post_init__(self):
        """Set environment-specific defaults."""
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            self.enabled = True
            self.track_errors = True
            self.track_performance = True
            self.track_system_metrics = True
            self.enable_alerts = True
            self.use_redis = True
        elif env == 'staging':
            self.enabled = True
            self.track_errors = True
            self.track_performance = True
            self.track_system_metrics = True
            self.enable_alerts = True
            self.use_redis = True
        else:  # development
            self.enabled = True
            self.track_errors = True
            self.track_performance = True
            self.track_system_metrics = False
            self.enable_alerts = False
            self.use_redis = False


@dataclass
class SecurityConfig:
    """Configuration for security-related error handling."""
    
    # Authentication and authorization
    log_auth_failures: bool = True
    log_auth_successes: bool = False
    log_permission_denied: bool = True
    
    # Financial data security
    log_financial_access: bool = True
    log_financial_modifications: bool = True
    log_payment_attempts: bool = True
    
    # Session security
    log_session_events: bool = True
    log_session_timeouts: bool = True
    log_session_hijacking_attempts: bool = True
    
    # API security
    log_api_abuse: bool = True
    log_rate_limit_violations: bool = True
    log_suspicious_requests: bool = True
    
    # Data privacy
    gdpr_compliance: bool = True
    pii_protection: bool = True
    data_retention_policy: bool = True
    
    # Threat detection
    enable_threat_detection: bool = True
    suspicious_ip_threshold: int = 10
    suspicious_user_agent_threshold: int = 5
    
    def __post_init__(self):
        """Set environment-specific defaults."""
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            self.log_auth_successes = False
            self.enable_threat_detection = True
        else:
            self.log_auth_successes = True
            self.enable_threat_detection = False


@dataclass
class RateLimitingConfig:
    """Configuration for rate limiting and API protection."""
    
    # Basic rate limiting
    enabled: bool = True
    default_limit: int = 100  # requests per window
    default_window: int = 3600  # 1 hour
    
    # Endpoint-specific limits
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        'forecast': {'limit': 10, 'window': 60},  # 10 requests per minute
        'payment': {'limit': 5, 'window': 300},   # 5 requests per 5 minutes
        'login': {'limit': 3, 'window': 300},     # 3 attempts per 5 minutes
        'health': {'limit': 1000, 'window': 60},  # 1000 requests per minute
    })
    
    # Storage backend
    storage_backend: str = "memory"  # memory, redis, database
    
    # Response headers
    include_retry_after: bool = True
    include_rate_limit_headers: bool = True
    
    # Blocking behavior
    block_exceeded_requests: bool = True
    return_429_status: bool = True
    
    def __post_init__(self):
        """Set environment-specific defaults."""
        env = os.getenv('FLASK_ENV', 'development').lower()
        
        if env == 'production':
            self.enabled = True
            self.storage_backend = "redis"
            self.block_exceeded_requests = True
        else:
            self.enabled = True
            self.storage_backend = "memory"
            self.block_exceeded_requests = False


@dataclass
class CulturalConfig:
    """Configuration for culturally appropriate error messages."""
    
    # Target audience
    target_culture: str = "african_american_professional"
    primary_language: str = "en"
    
    # Message tone
    message_tone: str = "professional_encouraging"
    use_cultural_references: bool = True
    avoid_stereotypes: bool = True
    
    # Financial terminology
    use_accessible_language: bool = True
    explain_financial_terms: bool = True
    provide_educational_context: bool = True
    
    # Support and guidance
    offer_support: bool = True
    provide_resources: bool = True
    encourage_questions: bool = True
    
    # Cultural sensitivity
    respect_cultural_values: bool = True
    acknowledge_historical_context: bool = True
    promote_financial_empowerment: bool = True


@dataclass
class AccessibilityConfig:
    """Configuration for accessibility in error messages."""
    
    # Screen reader support
    screen_reader_friendly: bool = True
    clear_error_descriptions: bool = True
    provide_actionable_guidance: bool = True
    
    # Visual accessibility
    high_contrast_support: bool = True
    clear_typography: bool = True
    consistent_layout: bool = True
    
    # Cognitive accessibility
    simple_language: bool = True
    step_by_step_guidance: bool = True
    avoid_technical_jargon: bool = True
    
    # Mobile accessibility
    mobile_friendly: bool = True
    touch_target_sizing: bool = True
    responsive_design: bool = True


class ErrorHandlingConfiguration:
    """Main configuration class that combines all configurations."""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv('FLASK_ENV', 'development')
        
        # Initialize all configuration sections
        self.logging = LoggingConfig()
        self.error_handling = ErrorHandlingConfig()
        self.monitoring = MonitoringConfig()
        self.security = SecurityConfig()
        self.rate_limiting = RateLimitingConfig()
        self.cultural = CulturalConfig()
        self.accessibility = AccessibilityConfig()
        
        # Load environment-specific overrides
        self._load_environment_overrides()
    
    def _load_environment_overrides(self):
        """Load environment-specific configuration overrides."""
        env = self.environment.lower()
        
        if env == 'production':
            self._load_production_overrides()
        elif env == 'staging':
            self._load_staging_overrides()
        else:
            self._load_development_overrides()
    
    def _load_production_overrides(self):
        """Load production-specific configuration overrides."""
        # Production overrides
        self.logging.enable_sentry = True
        self.logging.sentry_dsn = os.getenv('SENTRY_DSN')
        self.logging.log_level = "WARNING"
        
        self.monitoring.enabled = True
        self.monitoring.use_redis = True
        self.monitoring.enable_alerts = True
        
        self.security.enable_threat_detection = True
        self.rate_limiting.enabled = True
        self.rate_limiting.storage_backend = "redis"
    
    def _load_staging_overrides(self):
        """Load staging-specific configuration overrides."""
        # Staging overrides
        self.logging.enable_sentry = True
        self.logging.sentry_dsn = os.getenv('SENTRY_DSN')
        self.logging.log_level = "INFO"
        
        self.monitoring.enabled = True
        self.monitoring.use_redis = True
        self.monitoring.enable_alerts = True
        
        self.security.enable_threat_detection = True
        self.rate_limiting.enabled = True
        self.rate_limiting.storage_backend = "redis"
    
    def _load_development_overrides(self):
        """Load development-specific configuration overrides."""
        # Development overrides
        self.logging.enable_sentry = False
        self.logging.log_level = "DEBUG"
        
        self.monitoring.enabled = True
        self.monitoring.use_redis = False
        self.monitoring.enable_alerts = False
        
        self.security.enable_threat_detection = False
        self.rate_limiting.enabled = True
        self.rate_limiting.storage_backend = "memory"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for easy serialization."""
        return {
            'environment': self.environment,
            'logging': self.logging.__dict__,
            'error_handling': self.error_handling.__dict__,
            'monitoring': self.monitoring.__dict__,
            'security': self.security.__dict__,
            'rate_limiting': self.rate_limiting.__dict__,
            'cultural': self.cultural.__dict__,
            'accessibility': self.accessibility.__dict__
        }
    
    def validate(self) -> bool:
        """Validate the configuration for consistency."""
        try:
            # Basic validation
            if not self.logging.app_name:
                return False
            
            if self.logging.enable_sentry and not self.logging.sentry_dsn:
                return False
            
            if self.monitoring.use_redis and not self.monitoring.redis_host:
                return False
            
            return True
            
        except Exception:
            return False


# Global configuration instance
_config_instance = None


def get_config(environment: str = None) -> ErrorHandlingConfiguration:
    """Get the global configuration instance."""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ErrorHandlingConfiguration(environment)
    
    return _config_instance


def reload_config(environment: str = None) -> ErrorHandlingConfiguration:
    """Reload the configuration with new environment settings."""
    global _config_instance
    
    _config_instance = ErrorHandlingConfiguration(environment)
    return _config_instance
