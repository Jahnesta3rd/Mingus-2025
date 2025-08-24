"""
Environment Configuration for MINGUS Application
Manages environment variables and provides validation for PostgreSQL configuration
"""

import os
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from urllib.parse import urlparse
from config.secure_config import get_secure_config

@dataclass
class DatabaseConfig:
    """Database configuration validation and management"""
    
    # Connection settings
    host: str
    port: int
    database: str
    username: str
    password: str
    
    # SSL settings
    ssl_mode: str
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None
    ssl_crl: Optional[str] = None
    
    # Pool settings
    pool_size: int = 20
    pool_recycle: int = 3600
    pool_timeout: int = 30
    max_overflow: int = 30
    
    # Performance settings
    statement_timeout: int = 30000
    idle_timeout: int = 60000
    lock_timeout: int = 10000
    
    @classmethod
    def from_url(cls, database_url: str) -> 'DatabaseConfig':
        """Create DatabaseConfig from database URL"""
        parsed = urlparse(database_url)
        
        # Extract SSL parameters from query string
        ssl_params = {}
        if parsed.query:
            query_params = dict(item.split('=') for item in parsed.query.split('&'))
            ssl_params = {
                'ssl_mode': query_params.get('sslmode', 'prefer'),
                'ssl_cert': query_params.get('sslcert'),
                'ssl_key': query_params.get('sslkey'),
                'ssl_ca': query_params.get('sslca'),
                'ssl_crl': query_params.get('sslcrl'),
            }
        
        return cls(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/') or 'mingus_production',
            username=parsed.username or 'mingus_user',
            password=parsed.password or '',
            **ssl_params
        )
    
    def to_url(self) -> str:
        """Convert DatabaseConfig back to URL"""
        ssl_params = []
        if self.ssl_mode:
            ssl_params.append(f'sslmode={self.ssl_mode}')
        if self.ssl_cert:
            ssl_params.append(f'sslcert={self.ssl_cert}')
        if self.ssl_key:
            ssl_params.append(f'sslkey={self.ssl_key}')
        if self.ssl_ca:
            ssl_params.append(f'sslca={self.ssl_ca}')
        if self.ssl_crl:
            ssl_params.append(f'sslcrl={self.ssl_crl}')
        
        query_string = '&'.join(ssl_params) if ssl_params else ''
        
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}{'?' + query_string if query_string else ''}"
    
    def validate(self) -> List[str]:
        """Validate database configuration"""
        errors = []
        
        # Validate required fields
        if not self.host:
            errors.append("Database host is required")
        if not self.database:
            errors.append("Database name is required")
        if not self.username:
            errors.append("Database username is required")
        
        # Validate port range
        if not (1 <= self.port <= 65535):
            errors.append("Database port must be between 1 and 65535")
        
        # Validate pool settings
        if self.pool_size < 1:
            errors.append("Pool size must be at least 1")
        if self.pool_recycle < 0:
            errors.append("Pool recycle must be non-negative")
        if self.pool_timeout < 0:
            errors.append("Pool timeout must be non-negative")
        if self.max_overflow < 0:
            errors.append("Max overflow must be non-negative")
        
        # Validate timeout settings
        if self.statement_timeout < 0:
            errors.append("Statement timeout must be non-negative")
        if self.idle_timeout < 0:
            errors.append("Idle timeout must be non-negative")
        if self.lock_timeout < 0:
            errors.append("Lock timeout must be non-negative")
        
        # Validate SSL mode
        valid_ssl_modes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']
        if self.ssl_mode not in valid_ssl_modes:
            errors.append(f"SSL mode must be one of: {', '.join(valid_ssl_modes)}")
        
        return errors


class EnvironmentManager:
    """Manages environment variables and configuration using secure configuration management"""
    
    def __init__(self):
        """Initialize environment manager with secure config manager"""
        self.secure_config = get_secure_config()
        self.database_config = None
    
    def load_database_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables"""
        database_url = self.secure_config.get('DATABASE_URL')
        
        if database_url:
            # Parse from URL
            self.database_config = DatabaseConfig.from_url(database_url)
        else:
            # Load individual components
            self.database_config = DatabaseConfig(
                host=self.secure_config.get('DB_HOST', 'localhost'),
                port=int(self.secure_config.get('DB_PORT', '5432')),
                database=self.secure_config.get('DB_NAME', 'mingus_production'),
                username=self.secure_config.get('DB_USER', 'mingus_user'),
                password=self.secure_config.get('DB_PASSWORD', ''),
                ssl_mode=self.secure_config.get('DB_SSL_MODE', 'prefer'),
                ssl_cert=self.secure_config.get('DB_SSL_CERT'),
                ssl_key=self.secure_config.get('DB_SSL_KEY'),
                ssl_ca=self.secure_config.get('DB_SSL_CA'),
                ssl_crl=self.secure_config.get('DB_SSL_CRL'),
                pool_size=int(self.secure_config.get('DB_POOL_SIZE', '20')),
                pool_recycle=int(self.secure_config.get('DB_POOL_RECYCLE', '3600')),
                pool_timeout=int(self.secure_config.get('DB_POOL_TIMEOUT', '30')),
                max_overflow=int(self.secure_config.get('DB_MAX_OVERFLOW', '30')),
                statement_timeout=int(self.secure_config.get('DB_STATEMENT_TIMEOUT', '30000')),
                idle_timeout=int(self.secure_config.get('DB_IDLE_TIMEOUT', '60000')),
                lock_timeout=int(self.secure_config.get('DB_LOCK_TIMEOUT', '10000'))
            )
        
        return self.database_config
    
    def validate_environment(self) -> List[str]:
        """Validate all environment variables and configuration"""
        errors = []
        
        # Validate database configuration
        if not self.database_config:
            self.load_database_config()
        
        db_errors = self.database_config.validate()
        errors.extend(db_errors)
        
        # Validate required environment variables
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'SUPABASE_URL',
            'SUPABASE_KEY'
        ]
        
        for var in required_vars:
            if not self.secure_config.get(var):
                errors.append(f"Required environment variable {var} is missing")
        
        # Validate Redis URL
        redis_url = self.secure_config.get('REDIS_URL')
        if redis_url:
            redis_error = self._validate_redis_url(redis_url)
            if redis_error:
                errors.append(redis_error)
        
        # Validate mail server
        mail_server = self.secure_config.get('MAIL_SERVER')
        if mail_server:
            mail_error = self._validate_mail_server(mail_server)
            if mail_error:
                errors.append(mail_error)
        
        # Validate Supabase URL
        supabase_url = self.secure_config.get('SUPABASE_URL')
        if supabase_url:
            supabase_error = self._validate_supabase_url(supabase_url)
            if supabase_error:
                errors.append(supabase_error)
        
        # Validate Stripe configuration
        stripe_env = self.secure_config.get('STRIPE_ENVIRONMENT', 'test')
        if stripe_env == 'test':
            if not self.secure_config.get('STRIPE_TEST_SECRET_KEY'):
                errors.append("STRIPE_TEST_SECRET_KEY is required for test environment")
        elif stripe_env == 'live':
            if not self.secure_config.get('STRIPE_LIVE_SECRET_KEY'):
                errors.append("STRIPE_LIVE_SECRET_KEY is required for live environment")
        
        # Validate Plaid configuration
        plaid_env = self.secure_config.get('PLAID_ENVIRONMENT', 'sandbox')
        if plaid_env == 'sandbox':
            if not self.secure_config.get('PLAID_SANDBOX_CLIENT_ID'):
                errors.append("PLAID_SANDBOX_CLIENT_ID is required for sandbox environment")
            if not self.secure_config.get('PLAID_SANDBOX_SECRET'):
                errors.append("PLAID_SANDBOX_SECRET is required for sandbox environment")
        elif plaid_env == 'production':
            if not self.secure_config.get('PLAID_PRODUCTION_CLIENT_ID'):
                errors.append("PLAID_PRODUCTION_CLIENT_ID is required for production environment")
            if not self.secure_config.get('PLAID_PRODUCTION_SECRET'):
                errors.append("PLAID_PRODUCTION_SECRET is required for production environment")
        
        return errors
    
    def _validate_redis_url(self, url: str) -> Optional[str]:
        """Validate Redis URL format"""
        if not url.startswith(('redis://', 'rediss://')):
            return "Redis URL must start with redis:// or rediss://"
        return None
    
    def _validate_mail_server(self, server: str) -> Optional[str]:
        """Validate mail server format"""
        if not re.match(r'^[a-zA-Z0-9.-]+$', server):
            return "Mail server must be a valid hostname"
        return None
    
    def _validate_supabase_url(self, url: str) -> Optional[str]:
        """Validate Supabase URL format"""
        if not url.startswith('https://'):
            return "Supabase URL must use HTTPS"
        if not 'supabase.co' in url:
            return "Supabase URL must contain supabase.co domain"
        return None
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get summary of environment configuration"""
        if not self.database_config:
            self.load_database_config()
        
        return {
            'environment': self.secure_config.get('FLASK_ENV', 'production'),
            'debug': self.secure_config.get('DEBUG', 'false').lower() == 'true',
            'testing': self.secure_config.get('TESTING', 'false').lower() == 'true',
            'database': {
                'host': self.database_config.host,
                'port': self.database_config.port,
                'database': self.database_config.database,
                'username': self.database_config.username,
                'ssl_mode': self.database_config.ssl_mode,
                'pool_size': self.database_config.pool_size
            },
            'redis': {
                'url': self.secure_config.get('REDIS_URL', 'Not configured'),
                'configured': bool(self.secure_config.get('REDIS_URL'))
            },
            'supabase': {
                'url': self.secure_config.get('SUPABASE_URL', 'Not configured'),
                'configured': bool(self.secure_config.get('SUPABASE_URL'))
            },
            'stripe': {
                'environment': self.secure_config.get('STRIPE_ENVIRONMENT', 'test'),
                'configured': bool(self.secure_config.get('STRIPE_TEST_SECRET_KEY') or self.secure_config.get('STRIPE_LIVE_SECRET_KEY'))
            },
            'plaid': {
                'environment': self.secure_config.get('PLAID_ENVIRONMENT', 'sandbox'),
                'configured': bool(self.secure_config.get('PLAID_SANDBOX_CLIENT_ID') or self.secure_config.get('PLAID_PRODUCTION_CLIENT_ID'))
            },
            'email': {
                'provider': self.secure_config.get('EMAIL_PROVIDER', 'Not configured'),
                'configured': bool(self.secure_config.get('RESEND_API_KEY') or self.secure_config.get('MAIL_SERVER'))
            },
            'sms': {
                'provider': 'Twilio' if self.secure_config.get('TWILIO_ACCOUNT_SID') else 'Not configured',
                'configured': bool(self.secure_config.get('TWILIO_ACCOUNT_SID'))
            }
        }
    
    def print_environment_summary(self):
        """Print formatted environment summary"""
        summary = self.get_environment_summary()
        
        print("=" * 60)
        print("MINGUS APPLICATION - ENVIRONMENT SUMMARY")
        print("=" * 60)
        
        print(f"Environment: {summary['environment'].upper()}")
        print(f"Debug Mode: {'Yes' if summary['debug'] else 'No'}")
        print(f"Testing Mode: {'Yes' if summary['testing'] else 'No'}")
        print()
        
        print("DATABASE CONFIGURATION:")
        print(f"  Host: {summary['database']['host']}")
        print(f"  Port: {summary['database']['port']}")
        print(f"  Database: {summary['database']['database']}")
        print(f"  Username: {summary['database']['username']}")
        print(f"  SSL Mode: {summary['database']['ssl_mode']}")
        print(f"  Pool Size: {summary['database']['pool_size']}")
        print()
        
        print("EXTERNAL SERVICES:")
        print(f"  Redis: {'Configured' if summary['redis']['configured'] else 'Not configured'}")
        print(f"  Supabase: {'Configured' if summary['supabase']['configured'] else 'Not configured'}")
        print(f"  Stripe: {summary['stripe']['environment'].title()} ({'Configured' if summary['stripe']['configured'] else 'Not configured'})")
        print(f"  Plaid: {summary['plaid']['environment'].title()} ({'Configured' if summary['plaid']['configured'] else 'Not configured'})")
        print(f"  Email: {summary['email']['provider']}")
        print(f"  SMS: {summary['sms']['provider']}")
        print()
        
        # Check for validation errors
        errors = self.validate_environment()
        if errors:
            print("VALIDATION ERRORS:")
            for error in errors:
                print(f"  ❌ {error}")
            print()
        else:
            print("✅ All environment variables are valid!")
            print()
        
        print("=" * 60)


# Global instance for easy access
_env_manager = None

def get_environment_manager() -> EnvironmentManager:
    """Get the global environment manager instance"""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvironmentManager()
    return _env_manager

def create_env_file(environment: str, output_file: str = '.env'):
    """Create environment file template"""
    env_manager = get_environment_manager()
    
    # This would be implemented to create a .env file template
    # For now, we'll just print a message
    print(f"Environment file creation for {environment} would be implemented here")
    print(f"Output file: {output_file}")

def validate_and_load_environment() -> EnvironmentManager:
    """Validate and load environment configuration"""
    env_manager = get_environment_manager()
    errors = env_manager.validate_environment()
    
    if errors:
        print("Environment validation failed:")
        for error in errors:
            print(f"  ❌ {error}")
        raise ValueError("Environment validation failed")
    
    return env_manager

def get_database_url() -> str:
    """Get database URL from environment"""
    env_manager = get_environment_manager()
    if not env_manager.database_config:
        env_manager.load_database_config()
    return env_manager.database_config.to_url()

def get_redis_url() -> Optional[str]:
    """Get Redis URL from environment"""
    env_manager = get_environment_manager()
    return env_manager.secure_config.get('REDIS_URL')

def get_secret_key() -> str:
    """Get secret key from environment"""
    env_manager = get_environment_manager()
    return env_manager.secure_config.get('SECRET_KEY', '')

def is_production() -> bool:
    """Check if running in production environment"""
    env_manager = get_environment_manager()
    return env_manager.secure_config.get('FLASK_ENV', 'production') == 'production'

def is_development() -> bool:
    """Check if running in development environment"""
    env_manager = get_environment_manager()
    return env_manager.secure_config.get('FLASK_ENV', 'production') == 'development'

def is_testing() -> bool:
    """Check if running in testing environment"""
    env_manager = get_environment_manager()
    return env_manager.secure_config.get('TESTING', 'false').lower() == 'true' 