"""
Environment Configuration for MINGUS Application
Manages environment variables and provides validation for PostgreSQL configuration
"""

import os
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from urllib.parse import urlparse

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
    """Manages environment variables and configuration validation"""
    
    def __init__(self):
        self.environment = os.environ.get('FLASK_ENV', 'production')
        self.database_config = None
        self.validation_errors = []
    
    def load_database_config(self) -> DatabaseConfig:
        """Load and validate database configuration from environment"""
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            # Fallback to individual environment variables
            self.database_config = DatabaseConfig(
                host=os.environ.get('DB_HOST', 'localhost'),
                port=int(os.environ.get('DB_PORT', '5432')),
                database=os.environ.get('DB_NAME', 'mingus_production'),
                username=os.environ.get('DB_USER', 'mingus_user'),
                password=os.environ.get('DB_PASSWORD', 'mingus_password'),
                ssl_mode=os.environ.get('DB_SSL_MODE', 'prefer'),
                ssl_cert=os.environ.get('DB_SSL_CERT'),
                ssl_key=os.environ.get('DB_SSL_KEY'),
                ssl_ca=os.environ.get('DB_SSL_CA'),
                ssl_crl=os.environ.get('DB_SSL_CRL'),
                pool_size=int(os.environ.get('DB_POOL_SIZE', '20')),
                pool_recycle=int(os.environ.get('DB_POOL_RECYCLE', '3600')),
                pool_timeout=int(os.environ.get('DB_POOL_TIMEOUT', '30')),
                max_overflow=int(os.environ.get('DB_MAX_OVERFLOW', '30')),
                statement_timeout=int(os.environ.get('DB_STATEMENT_TIMEOUT', '30000')),
                idle_timeout=int(os.environ.get('DB_IDLE_TIMEOUT', '60000')),
                lock_timeout=int(os.environ.get('DB_LOCK_TIMEOUT', '10000')),
            )
        else:
            self.database_config = DatabaseConfig.from_url(database_url)
            
            # Override with individual environment variables if provided
            if os.environ.get('DB_POOL_SIZE'):
                self.database_config.pool_size = int(os.environ.get('DB_POOL_SIZE'))
            if os.environ.get('DB_POOL_RECYCLE'):
                self.database_config.pool_recycle = int(os.environ.get('DB_POOL_RECYCLE'))
            if os.environ.get('DB_POOL_TIMEOUT'):
                self.database_config.pool_timeout = int(os.environ.get('DB_POOL_TIMEOUT'))
            if os.environ.get('DB_MAX_OVERFLOW'):
                self.database_config.max_overflow = int(os.environ.get('DB_MAX_OVERFLOW'))
            if os.environ.get('DB_STATEMENT_TIMEOUT'):
                self.database_config.statement_timeout = int(os.environ.get('DB_STATEMENT_TIMEOUT'))
            if os.environ.get('DB_IDLE_TIMEOUT'):
                self.database_config.idle_timeout = int(os.environ.get('DB_IDLE_TIMEOUT'))
            if os.environ.get('DB_LOCK_TIMEOUT'):
                self.database_config.lock_timeout = int(os.environ.get('DB_LOCK_TIMEOUT'))
        
        return self.database_config
    
    def validate_environment(self) -> List[str]:
        """Validate all environment variables"""
        errors = []
        
        # Validate database configuration
        if self.database_config:
            db_errors = self.database_config.validate()
            errors.extend(db_errors)
        
        # Validate required environment variables
        required_vars = [
            'SECRET_KEY',
            'FLASK_ENV'
        ]
        
        for var in required_vars:
            if not os.environ.get(var):
                errors.append(f"Required environment variable {var} is not set")
        
        # Validate optional environment variables
        optional_vars = {
            'REDIS_URL': self._validate_redis_url,
            'MAIL_SERVER': self._validate_mail_server,
            'SUPABASE_URL': self._validate_supabase_url,
        }
        
        for var, validator in optional_vars.items():
            value = os.environ.get(var)
            if value:
                validation_error = validator(value)
                if validation_error:
                    errors.append(validation_error)
        
        # Validate numeric environment variables
        numeric_vars = {
            'PORT': (1, 65535),
            'DB_POOL_SIZE': (1, 100),
            'DB_MAX_OVERFLOW': (0, 100),
            'DB_STATEMENT_TIMEOUT': (1000, 300000),
            'DB_IDLE_TIMEOUT': (1000, 300000),
            'DB_LOCK_TIMEOUT': (1000, 60000),
        }
        
        for var, (min_val, max_val) in numeric_vars.items():
            value = os.environ.get(var)
            if value:
                try:
                    num_value = int(value)
                    if not (min_val <= num_value <= max_val):
                        errors.append(f"{var} must be between {min_val} and {max_val}")
                except ValueError:
                    errors.append(f"{var} must be a valid integer")
        
        # Validate boolean environment variables
        boolean_vars = [
            'DEBUG', 'TESTING', 'DB_ENABLE_QUERY_LOGGING', 'DB_BACKUP_ENABLED',
            'DB_ENABLE_ROW_LEVEL_SECURITY', 'DB_ENABLE_AUDIT_LOGGING',
            'SECURE_SSL_REDIRECT', 'WTF_CSRF_ENABLED'
        ]
        
        for var in boolean_vars:
            value = os.environ.get(var)
            if value and value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                errors.append(f"{var} must be a valid boolean value (true/false, 1/0, yes/no)")
        
        self.validation_errors = errors
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
        if 'supabase.co' not in url:
            return "Supabase URL must contain supabase.co"
        return None
    
    def get_environment_summary(self) -> Dict[str, Any]:
        """Get a summary of the current environment configuration"""
        return {
            'environment': self.environment,
            'database': {
                'host': self.database_config.host if self.database_config else None,
                'port': self.database_config.port if self.database_config else None,
                'database': self.database_config.database if self.database_config else None,
                'username': self.database_config.username if self.database_config else None,
                'ssl_mode': self.database_config.ssl_mode if self.database_config else None,
                'pool_size': self.database_config.pool_size if self.database_config else None,
            },
            'validation_errors': self.validation_errors,
            'environment_variables': {
                'FLASK_ENV': os.environ.get('FLASK_ENV'),
                'SECRET_KEY': '***' if os.environ.get('SECRET_KEY') else None,
                'DATABASE_URL': '***' if os.environ.get('DATABASE_URL') else None,
                'REDIS_URL': '***' if os.environ.get('REDIS_URL') else None,
                'SUPABASE_URL': os.environ.get('SUPABASE_URL'),
                'MAIL_SERVER': os.environ.get('MAIL_SERVER'),
                'PORT': os.environ.get('PORT'),
                'DEBUG': os.environ.get('DEBUG'),
                'TESTING': os.environ.get('TESTING'),
            }
        }
    
    def print_environment_summary(self):
        """Print environment configuration summary"""
        summary = self.get_environment_summary()
        
        print("=" * 60)
        print("🔧 MINGUS ENVIRONMENT CONFIGURATION")
        print("=" * 60)
        
        print(f"\n🌍 Environment: {summary['environment']}")
        
        if summary['database']:
            print(f"\n🗄️  Database Configuration:")
            for key, value in summary['database'].items():
                if value is not None:
                    print(f"   {key}: {value}")
        
        if summary['validation_errors']:
            print(f"\n❌ Validation Errors:")
            for error in summary['validation_errors']:
                print(f"   - {error}")
        else:
            print(f"\n✅ Environment validation passed")
        
        print(f"\n🔑 Environment Variables:")
        for key, value in summary['environment_variables'].items():
            if value is not None:
                print(f"   {key}: {value}")
        
        print("=" * 60)


# Environment variable templates for different deployment scenarios
ENVIRONMENT_TEMPLATES = {
    'development': {
        'FLASK_ENV': 'development',
        'DEBUG': 'true',
        'TESTING': 'false',
        'DATABASE_URL': 'postgresql://mingus_dev:mingus_dev_password@localhost:5432/mingus_development',
        'DB_POOL_SIZE': '5',
        'DB_MAX_OVERFLOW': '10',
        'DB_ENABLE_QUERY_LOGGING': 'true',
        'DB_ECHO': 'true',
        'SECURE_SSL_REDIRECT': 'false',
        'SESSION_COOKIE_SECURE': 'false',
        'WTF_CSRF_ENABLED': 'false',
    },
    
    'testing': {
        'FLASK_ENV': 'testing',
        'DEBUG': 'false',
        'TESTING': 'true',
        'DATABASE_URL': 'postgresql://mingus_test:mingus_test_password@localhost:5432/mingus_testing',
        'DB_POOL_SIZE': '1',
        'DB_MAX_OVERFLOW': '0',
        'DB_ENABLE_QUERY_LOGGING': 'false',
        'DB_ECHO': 'false',
        'SECURE_SSL_REDIRECT': 'false',
        'SESSION_COOKIE_SECURE': 'false',
        'WTF_CSRF_ENABLED': 'false',
        'RATELIMIT_ENABLED': 'false',
    },
    
    'production': {
        'FLASK_ENV': 'production',
        'DEBUG': 'false',
        'TESTING': 'false',
        'DATABASE_URL': 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production',
        'DB_POOL_SIZE': '20',
        'DB_MAX_OVERFLOW': '30',
        'DB_ENABLE_QUERY_LOGGING': 'false',
        'DB_ECHO': 'false',
        'SECURE_SSL_REDIRECT': 'true',
        'SESSION_COOKIE_SECURE': 'true',
        'WTF_CSRF_ENABLED': 'true',
        'RATELIMIT_ENABLED': 'true',
    },
    
    'digitalocean': {
        'FLASK_ENV': 'production',
        'DEBUG': 'false',
        'TESTING': 'false',
        'DATABASE_URL': 'postgresql://doadmin:password@db-postgresql-nyc1-12345.db.ondigitalocean.com:25060/mingus_production?sslmode=require',
        'DB_POOL_SIZE': '20',
        'DB_MAX_OVERFLOW': '30',
        'DB_ENABLE_QUERY_LOGGING': 'false',
        'DB_ECHO': 'false',
        'SECURE_SSL_REDIRECT': 'true',
        'SESSION_COOKIE_SECURE': 'true',
        'WTF_CSRF_ENABLED': 'true',
        'RATELIMIT_ENABLED': 'true',
        'REDIS_URL': 'redis://localhost:6379/0',
    }
}


def create_env_file(environment: str, output_file: str = '.env'):
    """Create a .env file with the specified environment template"""
    if environment not in ENVIRONMENT_TEMPLATES:
        raise ValueError(f"Unknown environment: {environment}. Available: {list(ENVIRONMENT_TEMPLATES.keys())}")
    
    template = ENVIRONMENT_TEMPLATES[environment]
    
    with open(output_file, 'w') as f:
        f.write(f"# MINGUS Application - {environment.upper()} Environment\n")
        f.write(f"# Generated automatically - Update with your actual values\n\n")
        
        for key, value in template.items():
            f.write(f"{key}={value}\n")
        
        f.write("\n# Additional required variables (update with your values):\n")
        f.write("SECRET_KEY=your-secret-key-change-in-production\n")
        f.write("SUPABASE_URL=https://your-project.supabase.co\n")
        f.write("SUPABASE_KEY=your-supabase-anon-key\n")
        f.write("SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key\n")
        f.write("MAIL_USERNAME=your-email@example.com\n")
        f.write("MAIL_PASSWORD=your-email-password\n")
        f.write("MAIL_DEFAULT_SENDER=noreply@yourdomain.com\n")
    
    print(f"✅ Created {output_file} with {environment} environment template")
    print(f"⚠️  Please update the file with your actual values before deployment")


def validate_and_load_environment() -> EnvironmentManager:
    """Validate and load environment configuration"""
    env_manager = EnvironmentManager()
    env_manager.load_database_config()
    
    errors = env_manager.validate_environment()
    
    if errors:
        print("❌ Environment validation failed:")
        for error in errors:
            print(f"   - {error}")
        print("\n💡 Use create_env_file() to generate a proper .env file")
        raise ValueError("Environment validation failed")
    
    return env_manager


# Convenience functions for common operations
def get_database_url() -> str:
    """Get the database URL from environment"""
    env_manager = EnvironmentManager()
    db_config = env_manager.load_database_config()
    return db_config.to_url()


def get_redis_url() -> Optional[str]:
    """Get the Redis URL from environment"""
    return os.environ.get('REDIS_URL')


def get_secret_key() -> str:
    """Get the secret key from environment"""
    return os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'


def is_production() -> bool:
    """Check if running in production environment"""
    return os.environ.get('FLASK_ENV') == 'production'


def is_development() -> bool:
    """Check if running in development environment"""
    return os.environ.get('FLASK_ENV') == 'development'


def is_testing() -> bool:
    """Check if running in testing environment"""
    return os.environ.get('FLASK_ENV') == 'testing' or os.environ.get('TESTING') == 'true' 