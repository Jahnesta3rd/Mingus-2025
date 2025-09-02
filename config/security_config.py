"""
Centralized Security Configuration Management System
Provides unified configuration for all security systems across environments
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import re
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class SecurityLevel(Enum):
    """Security levels for configuration values"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors"""
    pass

class SecurityPolicyViolation(Exception):
    """Exception raised for security policy violations"""
    pass

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    name: str
    description: str
    enabled: bool = True
    severity: SecurityLevel = SecurityLevel.MEDIUM
    rules: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)

@dataclass
class ValidationRule:
    """Validation rule for configuration values"""
    required: bool = False
    security_level: SecurityLevel = SecurityLevel.LOW
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[str]] = None
    custom_validator: Optional[callable] = None
    description: str = ""
    warning_message: str = ""

@dataclass
class SecurityConfig:
    """Base security configuration"""
    environment: Environment = Environment.DEVELOPMENT
    encryption_enabled: bool = True
    audit_logging_enabled: bool = True
    validation_enabled: bool = True
    secret_rotation_enabled: bool = True
    weak_secret_detection: bool = True
    startup_warnings_enabled: bool = True
    security_headers_enabled: bool = True
    rate_limiting_enabled: bool = True
    csrf_protection_enabled: bool = True
    session_security_enabled: bool = True

class SecurityConfigurationManager:
    """Centralized security configuration manager"""
    
    def __init__(self, environment: str = None):
        """Initialize security configuration manager"""
        self.environment = Environment(environment or os.getenv('FLASK_ENV', 'development'))
        self.config_cache: Dict[str, Any] = {}
        self.validation_rules = self._setup_validation_rules()
        self.security_policies = self._setup_security_policies()
        
        # Load environment-specific configuration
        self._load_environment_config()
        
        # Validate configuration
        if self.config.get('validation_enabled', True):
            self._validate_configuration()
        
        # Check for startup warnings
        if self.config.get('startup_warnings_enabled', True):
            self._check_startup_warnings()
    
    def _setup_validation_rules(self) -> Dict[str, ValidationRule]:
        """Setup validation rules for configuration values"""
        return {
            'SECRET_KEY': ValidationRule(
                required=True,
                security_level=SecurityLevel.CRITICAL,
                min_length=32,
                pattern=r'^[A-Za-z0-9\-_+/=]{32,}$',
                description="Application secret key for session encryption",
                warning_message="Weak secret key detected"
            ),
            'DATABASE_URL': ValidationRule(
                required=True,
                security_level=SecurityLevel.HIGH,
                pattern=r'^[a-z]+://[^:]+:[^@]+@[^:]+:\d+/\w+$',
                description="Database connection string",
                warning_message="Insecure database connection detected"
            ),
            'JWT_SECRET_KEY': ValidationRule(
                required=True,
                security_level=SecurityLevel.CRITICAL,
                min_length=32,
                pattern=r'^[A-Za-z0-9\-_+/=]{32,}$',
                description="JWT token signing key",
                warning_message="Weak JWT secret key detected"
            ),
            'ENCRYPTION_KEY': ValidationRule(
                required=True,
                security_level=SecurityLevel.CRITICAL,
                min_length=32,
                pattern=r'^[A-Za-z0-9\-_+/=]{32,}$',
                description="Data encryption key",
                warning_message="Weak encryption key detected"
            ),
            'CORS_ORIGINS': ValidationRule(
                required=False,
                security_level=SecurityLevel.MEDIUM,
                custom_validator=self._validate_cors_origins,
                description="Allowed CORS origins",
                warning_message="Overly permissive CORS configuration detected"
            ),
            'SESSION_COOKIE_SECURE': ValidationRule(
                required=False,
                security_level=SecurityLevel.MEDIUM,
                allowed_values=['true', 'false'],
                description="Secure session cookies",
                warning_message="Insecure session cookies in production"
            ),
            'SESSION_COOKIE_HTTPONLY': ValidationRule(
                required=False,
                security_level=SecurityLevel.MEDIUM,
                allowed_values=['true', 'false'],
                description="HTTP-only session cookies",
                warning_message="Session cookies accessible via JavaScript"
            )
        }
    
    def _setup_security_policies(self) -> List[SecurityPolicy]:
        """Setup security policies"""
        return [
            SecurityPolicy(
                name="Production Security",
                description="Enhanced security requirements for production environment",
                enabled=self.environment == Environment.PRODUCTION,
                severity=SecurityLevel.CRITICAL,
                rules=[
                    "All secrets must be at least 32 characters",
                    "HTTPS must be enabled",
                    "Secure cookies must be enabled",
                    "Audit logging must be enabled",
                    "Rate limiting must be enabled"
                ]
            ),
            SecurityPolicy(
                name="Development Security",
                description="Security requirements for development environment",
                enabled=self.environment == Environment.DEVELOPMENT,
                severity=SecurityLevel.MEDIUM,
                rules=[
                    "Basic validation enabled",
                    "Warnings for weak configurations",
                    "Local development overrides allowed"
                ]
            ),
            SecurityPolicy(
                name="Testing Security",
                description="Security requirements for testing environment",
                enabled=self.environment == Environment.TESTING,
                severity=SecurityLevel.LOW,
                rules=[
                    "Minimal validation",
                    "Test-specific configurations allowed",
                    "Mock security components enabled"
                ]
            )
        ]
    
    def _load_environment_config(self):
        """Load environment-specific configuration"""
        config_file = f"config/{self.environment.value}.py"
        
        try:
            if Path(config_file).exists():
                # Import environment-specific config
                import importlib.util
                spec = importlib.util.spec_from_file_location("env_config", config_file)
                env_config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(env_config)
                
                # Get config class
                config_class = getattr(env_config, f"{self.environment.value.capitalize()}Config", None)
                if config_class:
                    self.config = {key: getattr(config_class, key) for key in dir(config_class) 
                                 if not key.startswith('_') and key.isupper()}
                else:
                    self.config = {}
            else:
                self.config = {}
                
        except Exception as e:
            logger.warning(f"Failed to load environment config from {config_file}: {e}")
            self.config = {}
        
        # Load environment variables
        self._load_environment_variables()
        
        # Set defaults
        self._set_defaults()
    
    def _load_environment_variables(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'SECRET_KEY': 'SECRET_KEY',
            'DATABASE_URL': 'DATABASE_URL',
            'JWT_SECRET_KEY': 'JWT_SECRET_KEY',
            'ENCRYPTION_KEY': 'ENCRYPTION_KEY',
            'CORS_ORIGINS': 'CORS_ORIGINS',
            'SESSION_COOKIE_SECURE': 'SESSION_COOKIE_SECURE',
            'SESSION_COOKIE_HTTPONLY': 'SESSION_COOKIE_HTTPONLY',
            'RATE_LIMIT_ENABLED': 'RATE_LIMIT_ENABLED',
            'CSRF_ENABLED': 'CSRF_ENABLED',
            'AUDIT_LOGGING_ENABLED': 'AUDIT_LOGGING_ENABLED'
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self.config[config_key] = value
    
    def _set_defaults(self):
        """Set default configuration values"""
        defaults = {
            'ENVIRONMENT': self.environment.value,
            'DEBUG': self.environment in [Environment.DEVELOPMENT, Environment.TESTING],
            'TESTING': self.environment == Environment.TESTING,
            'SECRET_KEY': self._generate_default_secret_key(),
            'SESSION_COOKIE_SECURE': self.environment == Environment.PRODUCTION,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
            'RATE_LIMIT_ENABLED': True,
            'CSRF_ENABLED': True,
            'AUDIT_LOGGING_ENABLED': True,
            'SECURITY_HEADERS_ENABLED': True,
            'CORS_ORIGINS': self._get_default_cors_origins(),
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
            'UPLOAD_FOLDER': 'uploads',
            'ALLOWED_EXTENSIONS': {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'},
            'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
            'PASSWORD_MIN_LENGTH': 12,
            'PASSWORD_REQUIRE_UPPERCASE': True,
            'PASSWORD_REQUIRE_LOWERCASE': True,
            'PASSWORD_REQUIRE_DIGITS': True,
            'PASSWORD_REQUIRE_SPECIAL': True,
            'LOGIN_MAX_ATTEMPTS': 5,
            'LOGIN_LOCKOUT_DURATION': 900,  # 15 minutes
            'SESSION_TIMEOUT': 3600,  # 1 hour
            'IDLE_TIMEOUT': 1800,  # 30 minutes
            'MFA_REQUIRED': self.environment == Environment.PRODUCTION,
            'MFA_METHODS': ['totp', 'sms', 'email'],
            'API_RATE_LIMIT': '100 per minute',
            'WEB_RATE_LIMIT': '1000 per minute',
            'LOGIN_RATE_LIMIT': '5 per 15 minutes',
            'REGISTRATION_RATE_LIMIT': '3 per hour',
            'PASSWORD_RESET_RATE_LIMIT': '3 per hour',
            'EMAIL_VERIFICATION_RATE_LIMIT': '5 per hour',
            'SMS_VERIFICATION_RATE_LIMIT': '3 per hour',
            'MAX_SESSIONS_PER_USER': 5,
            'SESSION_ABSOLUTE_TIMEOUT': 86400,  # 24 hours
            'REMEMBER_ME_DURATION': 2592000,  # 30 days
            'SECURE_HEADERS': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': self._get_default_csp(),
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
            }
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _generate_default_secret_key(self) -> str:
        """Generate a default secret key for development/testing"""
        import secrets
        return secrets.token_urlsafe(32)
    
    def _get_default_cors_origins(self) -> List[str]:
        """Get default CORS origins based on environment"""
        if self.environment == Environment.PRODUCTION:
            return ['https://yourdomain.com', 'https://www.yourdomain.com']
        elif self.environment == Environment.STAGING:
            return ['https://staging.yourdomain.com']
        else:
            return ['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:5000']
    
    def _get_default_csp(self) -> str:
        """Get default Content Security Policy"""
        if self.environment == Environment.PRODUCTION:
            return ("default-src 'self'; "
                   "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com; "
                   "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                   "font-src 'self' https://fonts.gstatic.com; "
                   "img-src 'self' data: https:; "
                   "connect-src 'self' https://api.stripe.com; "
                   "frame-src https://js.stripe.com;")
        else:
            return ("default-src 'self'; "
                   "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                   "style-src 'self' 'unsafe-inline'; "
                   "img-src 'self' data:;")
    
    def _validate_cors_origins(self, value: Any) -> bool:
        """Custom validator for CORS origins"""
        if isinstance(value, str):
            origins = [origin.strip() for origin in value.split(',')]
        elif isinstance(value, list):
            origins = value
        else:
            return False
        
        for origin in origins:
            if not re.match(r'^https?://[^/]+$', origin):
                return False
        return True
    
    def _validate_configuration(self):
        """Validate configuration against rules"""
        violations = []
        warnings = []
        
        for key, rule in self.validation_rules.items():
            if key in self.config:
                value = self.config[key]
                
                # Check required fields
                if rule.required and not value:
                    violations.append(f"Required field '{key}' is missing or empty")
                    continue
                
                # Check pattern
                if rule.pattern and not re.match(rule.pattern, str(value)):
                    violations.append(f"Field '{key}' does not match required pattern")
                
                # Check length constraints
                if rule.min_length and len(str(value)) < rule.min_length:
                    violations.append(f"Field '{key}' is too short (min: {rule.min_length})")
                
                if rule.max_length and len(str(value)) > rule.max_length:
                    violations.append(f"Field '{key}' is too long (max: {rule.max_length})")
                
                # Check allowed values
                if rule.allowed_values and str(value).lower() not in [v.lower() for v in rule.allowed_values]:
                    violations.append(f"Field '{key}' has invalid value '{value}'")
                
                # Check custom validator
                if rule.custom_validator and not rule.custom_validator(value):
                    violations.append(f"Field '{key}' failed custom validation")
                
                # Check security level warnings
                if rule.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                    if self._is_weak_value(value):
                        warnings.append(f"{rule.warning_message} for field '{key}'")
        
        # Check security policies
        for policy in self.security_policies:
            if policy.enabled:
                policy_violations = self._check_policy_compliance(policy)
                violations.extend(policy_violations)
        
        # Report violations and warnings
        if violations:
            logger.error("Configuration validation violations:")
            for violation in violations:
                logger.error(f"  - {violation}")
            raise ConfigValidationError(f"Configuration validation failed: {len(violations)} violations")
        
        if warnings:
            logger.warning("Configuration warnings:")
            for warning in warnings:
                logger.warning(f"  - {warning}")
    
    def _is_weak_value(self, value: Any) -> bool:
        """Check if a configuration value is weak"""
        if not value:
            return False
        
        str_value = str(value)
        
        # Check for common weak patterns
        weak_patterns = [
            r'^test$',
            r'^password$',
            r'^secret$',
            r'^key$',
            r'^123',
            r'^admin$',
            r'^root$',
            r'^default$',
            r'^changeme$',
            r'^temp$'
        ]
        
        for pattern in weak_patterns:
            if re.match(pattern, str_value.lower()):
                return True
        
        # Check for short values
        if len(str_value) < 16:
            return True
        
        return False
    
    def _check_policy_compliance(self, policy: SecurityPolicy) -> List[str]:
        """Check compliance with security policy"""
        violations = []
        
        for rule in policy.rules:
            if "HTTPS must be enabled" in rule and self.environment == Environment.PRODUCTION:
                if not self.config.get('SESSION_COOKIE_SECURE', False):
                    violations.append(f"Policy violation: {rule}")
            
            elif "Secure cookies must be enabled" in rule and self.environment == Environment.PRODUCTION:
                if not self.config.get('SESSION_COOKIE_SECURE', False):
                    violations.append(f"Policy violation: {rule}")
            
            elif "Audit logging must be enabled" in rule and self.environment == Environment.PRODUCTION:
                if not self.config.get('AUDIT_LOGGING_ENABLED', False):
                    violations.append(f"Policy violation: {rule}")
        
        return violations
    
    def _check_startup_warnings(self):
        """Check for startup warnings"""
        warnings_list = []
        
        # Check for development patterns in production
        if self.environment == Environment.PRODUCTION:
            if self.config.get('DEBUG', False):
                warnings_list.append("DEBUG mode is enabled in production")
            
            if not self.config.get('SESSION_COOKIE_SECURE', False):
                warnings_list.append("Secure cookies are disabled in production")
            
            if not self.config.get('AUDIT_LOGGING_ENABLED', False):
                warnings_list.append("Audit logging is disabled in production")
        
        # Check for weak secrets
        for key, rule in self.validation_rules.items():
            if key in self.config and rule.security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                if self._is_weak_value(self.config[key]):
                    warnings_list.append(f"Weak value detected for {key}")
        
        # Report warnings
        if warnings_list:
            logger.warning("Security startup warnings:")
            for warning in warnings_list:
                logger.warning(f"  - {warning}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config.copy()
    
    def update(self, key: str, value: Any):
        """Update configuration value"""
        if key in self.validation_rules:
            rule = self.validation_rules[key]
            if rule.custom_validator and not rule.custom_validator(value):
                raise ConfigValidationError(f"Invalid value for {key}")
        
        self.config[key] = value
        logger.info(f"Updated configuration: {key} = {value}")
    
    def validate_security_policy(self, policy_name: str) -> bool:
        """Validate against specific security policy"""
        for policy in self.security_policies:
            if policy.name == policy_name:
                violations = self._check_policy_compliance(policy)
                return len(violations) == 0
        return False
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration (optionally excluding secrets)"""
        export_config = self.config.copy()
        
        if not include_secrets:
            secret_keys = ['SECRET_KEY', 'JWT_SECRET_KEY', 'ENCRYPTION_KEY', 'DATABASE_URL']
            for key in secret_keys:
                if key in export_config:
                    export_config[key] = '***REDACTED***'
        
        return export_config
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security configuration summary"""
        return {
            'environment': self.environment.value,
            'policies_enabled': [p.name for p in self.security_policies if p.enabled],
            'validation_enabled': self.config.get('validation_enabled', False),
            'audit_logging_enabled': self.config.get('audit_logging_enabled', False),
            'encryption_enabled': self.config.get('encryption_enabled', False),
            'rate_limiting_enabled': self.config.get('rate_limiting_enabled', False),
            'csrf_protection_enabled': self.config.get('csrf_protection_enabled', False),
            'session_security_enabled': self.config.get('session_security_enabled', False),
            'security_headers_enabled': self.config.get('security_headers_enabled', False),
            'mfa_required': self.config.get('MFA_REQUIRED', False),
            'password_policy': {
                'min_length': self.config.get('PASSWORD_MIN_LENGTH', 8),
                'require_uppercase': self.config.get('PASSWORD_REQUIRE_UPPERCASE', False),
                'require_lowercase': self.config.get('PASSWORD_REQUIRE_LOWERCASE', False),
                'require_digits': self.config.get('PASSWORD_REQUIRE_DIGITS', False),
                'require_special': self.config.get('PASSWORD_REQUIRE_SPECIAL', False)
            },
            'rate_limits': {
                'api': self.config.get('API_RATE_LIMIT', '100 per minute'),
                'web': self.config.get('WEB_RATE_LIMIT', '1000 per minute'),
                'login': self.config.get('LOGIN_RATE_LIMIT', '5 per 15 minutes')
            }
        }

# Global instance (lazy initialization)
security_config = None

def get_security_config() -> SecurityConfigurationManager:
    """Get global security configuration instance"""
    global security_config
    if security_config is None:
        security_config = SecurityConfigurationManager()
    return security_config

def init_security_config(environment: str = None) -> SecurityConfigurationManager:
    """Initialize security configuration"""
    global security_config
    security_config = SecurityConfigurationManager(environment)
    return security_config
