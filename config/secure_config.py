"""
Secure Configuration Management System for MINGUS Application
Provides centralized, secure configuration management with validation, encryption, and audit logging.
"""

import os
import secrets
import hashlib
import json
import base64
import logging
import warnings
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for configuration values"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ConfigValidationError(Exception):
    """Exception raised for configuration validation errors"""
    pass

class SecretRotationError(Exception):
    """Exception raised for secret rotation errors"""
    pass

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    encryption_enabled: bool = True
    audit_logging_enabled: bool = True
    validation_enabled: bool = True
    secret_rotation_enabled: bool = True
    weak_secret_detection: bool = True
    startup_warnings_enabled: bool = True

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

class SecureConfigManager:
    """Secure configuration manager with validation, encryption, and audit logging"""
    
    def __init__(self, config_file: Optional[str] = None, security_config: Optional[SecurityConfig] = None):
        """Initialize secure configuration manager"""
        self.config_file = config_file
        self.security_config = security_config or SecurityConfig()
        self.config_cache: Dict[str, Any] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self.validation_rules = self._setup_validation_rules()
        self.encryption_key = None
        self.fernet = None
        
        # Initialize encryption if enabled
        if self.security_config.encryption_enabled:
            self._initialize_encryption()
        
        # Load configuration
        self._load_configuration()
        
        # Validate configuration
        if self.security_config.validation_enabled:
            self._validate_configuration()
        
        # Check for startup warnings
        if self.security_config.startup_warnings_enabled:
            self._check_startup_warnings()
    
    def _initialize_encryption(self):
        """Initialize encryption for sensitive configuration values"""
        try:
            config_key = os.getenv('CONFIG_ENCRYPTION_KEY')
            if not config_key:
                # Generate a new encryption key for development
                config_key = self._generate_secure_key(32)
                warnings.warn(
                    f"CONFIG_ENCRYPTION_KEY not found. Generated new key: {config_key[:16]}... "
                    "Set this environment variable for consistent encryption."
                )
            
            # Derive encryption key using PBKDF2
            salt = b'mingus_config_salt'  # In production, use a random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(config_key.encode()))
            self.encryption_key = key
            self.fernet = Fernet(key)
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            self.security_config.encryption_enabled = False
    
    def _generate_secure_key(self, length: int = 32) -> str:
        """Generate a secure random key"""
        return secrets.token_urlsafe(length)
    
    def _setup_validation_rules(self) -> Dict[str, ValidationRule]:
        """Setup comprehensive validation rules for all configuration keys"""
        return {
            # Critical security keys
            'SECRET_KEY': ValidationRule(
                required=True,
                security_level=SecurityLevel.CRITICAL,
                min_length=32,
                description="Flask secret key for session encryption",
                warning_message="Missing SECRET_KEY - sessions will be insecure"
            ),
            'FIELD_ENCRYPTION_KEY': ValidationRule(
                required=True,
                security_level=SecurityLevel.CRITICAL,
                min_length=32,
                description="Key for encrypting sensitive database fields",
                warning_message="Missing FIELD_ENCRYPTION_KEY - sensitive data will be unencrypted"
            ),
            'DJANGO_SECRET_KEY': ValidationRule(
                required=True,
                security_level=SecurityLevel.CRITICAL,
                min_length=50,
                description="Django secret key for compatibility",
                warning_message="Missing DJANGO_SECRET_KEY - Django compatibility may be affected"
            ),
            
            # Database configuration
            'DATABASE_URL': ValidationRule(
                required=True,
                security_level=SecurityLevel.HIGH,
                pattern=r'^postgresql://.*$',
                description="PostgreSQL database connection URL",
                warning_message="Missing DATABASE_URL - application cannot connect to database"
            ),
            
            # External service credentials
            'SUPABASE_URL': ValidationRule(
                required=True,
                security_level=SecurityLevel.HIGH,
                pattern=r'^https://.*\.supabase\.co$',
                description="Supabase project URL",
                warning_message="Missing SUPABASE_URL - authentication and database features disabled"
            ),
            'SUPABASE_KEY': ValidationRule(
                required=True,
                security_level=SecurityLevel.CRITICAL,
                pattern=r'^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$',
                description="Supabase anonymous key",
                warning_message="Missing SUPABASE_KEY - authentication and database features disabled"
            ),
            'SUPABASE_SERVICE_ROLE_KEY': ValidationRule(
                required=False,
                security_level=SecurityLevel.CRITICAL,
                pattern=r'^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$',
                description="Supabase service role key for admin operations",
                warning_message="Missing SUPABASE_SERVICE_ROLE_KEY - admin operations disabled"
            ),
            
            # Payment processing
            'STRIPE_TEST_SECRET_KEY': ValidationRule(
                required=False,
                security_level=SecurityLevel.CRITICAL,
                pattern=r'^sk_test_[A-Za-z0-9]{24}$',
                description="Stripe test secret key",
                warning_message="Missing STRIPE_TEST_SECRET_KEY - payment processing disabled in test mode"
            ),
            'STRIPE_LIVE_SECRET_KEY': ValidationRule(
                required=False,
                security_level=SecurityLevel.CRITICAL,
                pattern=r'^sk_live_[A-Za-z0-9]{24}$',
                description="Stripe live secret key",
                warning_message="Missing STRIPE_LIVE_SECRET_KEY - payment processing disabled in live mode"
            ),
            
            # Financial data
            'PLAID_SANDBOX_CLIENT_ID': ValidationRule(
                required=False,
                security_level=SecurityLevel.HIGH,
                pattern=r'^[A-Za-z0-9]{24}$',
                description="Plaid sandbox client ID",
                warning_message="Missing PLAID_SANDBOX_CLIENT_ID - financial data features disabled in sandbox"
            ),
            'PLAID_SANDBOX_SECRET': ValidationRule(
                required=False,
                security_level=SecurityLevel.CRITICAL,
                pattern=r'^[A-Za-z0-9]{30}$',
                description="Plaid sandbox secret",
                warning_message="Missing PLAID_SANDBOX_SECRET - financial data features disabled in sandbox"
            ),
            'PLAID_PRODUCTION_CLIENT_ID': ValidationRule(
                required=False,
                security_level=SecurityLevel.HIGH,
                pattern=r'^[A-Za-z0-9]{24}$',
                description="Plaid production client ID",
                warning_message="Missing PLAID_PRODUCTION_CLIENT_ID - financial data features disabled in production"
            ),
            'PLAID_PRODUCTION_SECRET': ValidationRule(
                required=False,
                security_level=SecurityLevel.CRITICAL,
                pattern=r'^[A-Za-z0-9]{30}$',
                description="Plaid production secret",
                warning_message="Missing PLAID_PRODUCTION_SECRET - financial data features disabled in production"
            ),
            
            # Communication services
            'TWILIO_ACCOUNT_SID': ValidationRule(
                required=False,
                security_level=SecurityLevel.HIGH,
                pattern=r'^AC[A-Za-z0-9]{32}$',
                description="Twilio account SID for SMS",
                warning_message="Missing TWILIO_ACCOUNT_SID - SMS features disabled"
            ),
            'TWILIO_AUTH_TOKEN': ValidationRule(
                required=False,
                security_level=SecurityLevel.CRITICAL,
                pattern=r'^[A-Za-z0-9]{32}$',
                description="Twilio auth token for SMS",
                warning_message="Missing TWILIO_AUTH_TOKEN - SMS features disabled"
            ),
            'RESEND_API_KEY': ValidationRule(
                required=False,
                security_level=SecurityLevel.CRITICAL,
                pattern=r'^re_[A-Za-z0-9]{40}$',
                description="Resend API key for email",
                warning_message="Missing RESEND_API_KEY - email features disabled"
            ),
            
            # Redis configuration
            'REDIS_URL': ValidationRule(
                required=False,
                security_level=SecurityLevel.MEDIUM,
                pattern=r'^redis://.*$',
                description="Redis connection URL for caching and sessions",
                warning_message="Missing REDIS_URL - using in-memory storage (not recommended for production)"
            ),
            
            # Environment-specific settings
            'FLASK_ENV': ValidationRule(
                required=False,
                security_level=SecurityLevel.LOW,
                allowed_values=['development', 'testing', 'production'],
                description="Flask environment setting",
                warning_message="FLASK_ENV not set - defaulting to production"
            ),
            'DEBUG': ValidationRule(
                required=False,
                security_level=SecurityLevel.LOW,
                allowed_values=['true', 'false'],
                description="Debug mode setting",
                warning_message="DEBUG not set - defaulting to false"
            ),
            
            # Optional but recommended settings
            'CONFIG_ENCRYPTION_KEY': ValidationRule(
                required=False,
                security_level=SecurityLevel.HIGH,
                min_length=32,
                description="Key for encrypting configuration values",
                warning_message="CONFIG_ENCRYPTION_KEY not set - configuration encryption disabled"
            ),
            'AUDIT_LOG_ENABLED': ValidationRule(
                required=False,
                security_level=SecurityLevel.MEDIUM,
                allowed_values=['true', 'false'],
                description="Enable audit logging for configuration access",
                warning_message="AUDIT_LOG_ENABLED not set - audit logging disabled"
            ),
        }
    
    def _load_configuration(self):
        """Load configuration from environment variables and optional file"""
        # Load from environment variables
        for key in self.validation_rules:
            value = os.getenv(key)
            if value is not None:
                self.config_cache[key] = value
        
        # Load from config file if specified
        if self.config_file and Path(self.config_file).exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(self.config_file)
                
                # Reload from environment after loading .env file
                for key in self.validation_rules:
                    value = os.getenv(key)
                    if value is not None:
                        self.config_cache[key] = value
                        
            except ImportError:
                logger.warning("python-dotenv not installed, skipping .env file loading")
            except Exception as e:
                logger.error(f"Failed to load configuration file {self.config_file}: {e}")
    
    def _validate_configuration(self):
        """Validate all configuration values against defined rules"""
        errors = []
        warnings_list = []
        
        for key, rule in self.validation_rules.items():
            value = self.config_cache.get(key)
            
            # Check if required
            if rule.required and not value:
                errors.append(f"Configuration '{key}' is required but not set")
                continue
            
            # Skip validation if value is not set and not required
            if not value:
                continue
            
            # Validate pattern
            if rule.pattern and not re.match(rule.pattern, value):
                errors.append(f"Configuration '{key}' does not match required pattern")
            
            # Validate length
            if rule.min_length and len(value) < rule.min_length:
                errors.append(f"Configuration '{key}' must be at least {rule.min_length} characters")
            
            if rule.max_length and len(value) > rule.max_length:
                errors.append(f"Configuration '{key}' must be at most {rule.max_length} characters")
            
            # Validate allowed values
            if rule.allowed_values and value not in rule.allowed_values:
                errors.append(f"Configuration '{key}' must be one of: {', '.join(rule.allowed_values)}")
            
            # Custom validation
            if rule.custom_validator:
                try:
                    if not rule.custom_validator(value):
                        errors.append(f"Configuration '{key}' failed custom validation")
                except Exception as e:
                    errors.append(f"Configuration '{key}' custom validation error: {e}")
            
            # Check for weak secrets
            if self.security_config.weak_secret_detection and self._is_weak_secret(value):
                warnings_list.append(f"Configuration '{key}' appears to be a weak secret")
        
        if errors:
            raise ConfigValidationError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        if warnings_list:
            for warning in warnings_list:
                logger.warning(warning)
    
    def _is_weak_secret(self, value: str) -> bool:
        """Check if a secret value is weak"""
        weak_patterns = [
            r'^dev-',
            r'^test-',
            r'^password$',
            r'^secret$',
            r'^key$',
            r'^123456',
            r'^admin',
            r'^default',
            r'^changeme',
            r'^temp',
            r'^demo',
        ]
        
        value_lower = value.lower()
        for pattern in weak_patterns:
            if re.search(pattern, value_lower):
                return True
        
        # Check for low entropy
        if len(set(value)) < len(value) * 0.3:
            return True
        
        return False
    
    def _check_startup_warnings(self):
        """Check for startup warnings and display them"""
        warnings_list = []
        
        for key, rule in self.validation_rules.items():
            if not self.config_cache.get(key) and rule.warning_message:
                warnings_list.append(f"{key}: {rule.warning_message}")
        
        if warnings_list:
            logger.warning("=== STARTUP WARNINGS ===")
            for warning in warnings_list:
                logger.warning(f"⚠️  {warning}")
            logger.warning("=== END STARTUP WARNINGS ===")
    
    def get(self, key: str, default: Any = None, decrypt: bool = False) -> Any:
        """Get configuration value with optional decryption"""
        value = self.config_cache.get(key, default)
        
        # Log access for audit
        if self.security_config.audit_logging_enabled:
            self._log_access(key, 'get')
        
        # Decrypt if requested and encryption is enabled
        if decrypt and value and self.fernet:
            try:
                if isinstance(value, str) and value.startswith('encrypted:'):
                    encrypted_value = value[10:]  # Remove 'encrypted:' prefix
                    decrypted_bytes = self.fernet.decrypt(encrypted_value.encode())
                    return decrypted_bytes.decode()
            except Exception as e:
                logger.error(f"Failed to decrypt value for {key}: {e}")
        
        return value
    
    def set(self, key: str, value: Any, encrypt: bool = False) -> None:
        """Set configuration value with optional encryption"""
        # Validate the value
        if key in self.validation_rules:
            rule = self.validation_rules[key]
            if rule.pattern and not re.match(rule.pattern, str(value)):
                raise ConfigValidationError(f"Value for {key} does not match required pattern")
        
        # Encrypt if requested and encryption is enabled
        if encrypt and self.fernet:
            try:
                encrypted_bytes = self.fernet.encrypt(str(value).encode())
                value = f"encrypted:{encrypted_bytes.decode()}"
            except Exception as e:
                logger.error(f"Failed to encrypt value for {key}: {e}")
        
        self.config_cache[key] = value
        
        # Log change for audit
        if self.security_config.audit_logging_enabled:
            self._log_access(key, 'set')
    
    def _log_access(self, key: str, action: str):
        """Log configuration access for audit purposes"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'key': key,
            'action': action,
            'security_level': self.validation_rules.get(key, ValidationRule()).security_level.value
        }
        self.audit_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
    
    def rotate_secret(self, key: str) -> str:
        """Rotate a secret configuration value"""
        if not self.security_config.secret_rotation_enabled:
            raise SecretRotationError("Secret rotation is disabled")
        
        # Generate new secret based on key type
        if 'SECRET_KEY' in key:
            new_secret = self._generate_secure_key(32)
        elif 'ENCRYPTION_KEY' in key:
            new_secret = self._generate_secure_key(32)
        elif 'DJANGO_SECRET_KEY' in key:
            new_secret = self._generate_secure_key(50)
        else:
            new_secret = self._generate_secure_key(32)
        
        # Set the new secret
        self.set(key, new_secret, encrypt=True)
        
        logger.info(f"Rotated secret for {key}")
        return new_secret
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get configuration audit log"""
        return self.audit_log.copy()
    
    def export_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration (redacting secrets by default)"""
        exported = {}
        
        for key, value in self.config_cache.items():
            if include_secrets:
                exported[key] = value
            else:
                # Redact sensitive values
                if self.validation_rules.get(key, ValidationRule()).security_level in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]:
                    exported[key] = f"***REDACTED*** ({len(str(value))} chars)"
                else:
                    exported[key] = value
        
        return exported
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate the current environment configuration"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_critical': [],
            'missing_high': [],
            'missing_medium': [],
            'missing_low': [],
            'weak_secrets': [],
            'recommendations': []
        }
        
        for key, rule in self.validation_rules.items():
            value = self.config_cache.get(key)
            
            if not value:
                if rule.required:
                    results['errors'].append(f"Required configuration '{key}' is missing")
                    results['valid'] = False
                else:
                    if rule.security_level == SecurityLevel.CRITICAL:
                        results['missing_critical'].append(key)
                    elif rule.security_level == SecurityLevel.HIGH:
                        results['missing_high'].append(key)
                    elif rule.security_level == SecurityLevel.MEDIUM:
                        results['missing_medium'].append(key)
                    else:
                        results['missing_low'].append(key)
            else:
                # Validate existing values
                if rule.pattern and not re.match(rule.pattern, value):
                    results['errors'].append(f"Configuration '{key}' does not match required pattern")
                    results['valid'] = False
                
                if self._is_weak_secret(value):
                    results['weak_secrets'].append(key)
        
        # Generate recommendations
        if results['missing_critical']:
            results['recommendations'].append("Set critical missing configurations for security")
        if results['missing_high']:
            results['recommendations'].append("Set high-priority missing configurations for full functionality")
        if results['weak_secrets']:
            results['recommendations'].append("Rotate weak secrets for better security")
        
        return results


# Global instance for easy access
_secure_config = None

def get_secure_config() -> SecureConfigManager:
    """Get the global secure configuration instance"""
    global _secure_config
    if _secure_config is None:
        _secure_config = SecureConfigManager()
    return _secure_config

def get_secret_key() -> str:
    """Get the Flask secret key"""
    config = get_secure_config()
    return config.get('SECRET_KEY', '')

def get_database_url() -> str:
    """Get the database URL"""
    config = get_secure_config()
    return config.get('DATABASE_URL', '')

def is_production() -> bool:
    """Check if running in production environment"""
    config = get_secure_config()
    return config.get('FLASK_ENV', 'production') == 'production'

def is_development() -> bool:
    """Check if running in development environment"""
    config = get_secure_config()
    return config.get('FLASK_ENV', 'production') == 'development'

def is_testing() -> bool:
    """Check if running in testing environment"""
    config = get_secure_config()
    return config.get('FLASK_ENV', 'production') == 'testing'


def validate_config():
    """
    Simple validation function that checks for required environment variables.
    This provides a basic validation check similar to the simple approach.
    
    Raises:
        ValueError: If any required environment variables are missing
    """
    required_vars = ['SECRET_KEY', 'DATABASE_URL', 'SUPABASE_KEY']
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    
    # Additional validation using the secure config manager if available
    try:
        secure_config = get_secure_config()
        secure_config._validate_configuration()
    except Exception as e:
        logger.warning(f"Advanced validation failed: {e}")
        # Don't raise here as we've already validated the basic required vars 