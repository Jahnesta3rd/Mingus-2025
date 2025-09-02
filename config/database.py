"""
Database Configuration for Mingus Financial Application
Optimized settings for different environments with production-grade connection pooling
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Base database configuration"""
    # Connection settings
    host: str
    port: int
    database: str
    username: str
    password: str
    
    # Connection pooling settings
    pool_size: int
    max_overflow: int
    pool_recycle: int
    pool_timeout: int
    pool_pre_ping: bool
    
    # SSL settings
    ssl_mode: str
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None
    
    # Performance settings
    statement_timeout: int = 30000  # 30 seconds
    idle_in_transaction_timeout: int = 60000  # 60 seconds
    connect_timeout: int = 10
    command_timeout: int = 30
    
    # Keepalive settings
    keepalives_idle: int = 60
    keepalives_interval: int = 10
    keepalives_count: int = 5
    
    # Monitoring settings
    health_check_interval: int = 300  # 5 minutes
    critical_check_interval: int = 60  # 1 minute
    consistency_check_interval: int = 3600  # 1 hour
    
    # Thresholds
    slow_query_threshold: float = 1.0  # 1 second
    connection_leak_threshold: int = 5
    error_rate_critical: float = 0.1  # 10%
    error_rate_warning: float = 0.05  # 5%
    
    @property
    def connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        ssl_params = []
        if self.ssl_mode != 'disable':
            ssl_params.append(f"sslmode={self.ssl_mode}")
            if self.ssl_cert:
                ssl_params.append(f"sslcert={self.ssl_cert}")
            if self.ssl_key:
                ssl_params.append(f"sslkey={self.ssl_key}")
            if self.ssl_ca:
                ssl_params.append(f"sslrootcert={self.ssl_ca}")
        
        ssl_string = "&".join(ssl_params) if ssl_params else ""
        
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
            f"{'?' + ssl_string if ssl_string else ''}"
        )
    
    def get_pool_settings(self, pool_name: str = 'main') -> Dict[str, Any]:
        """Get pool-specific settings"""
        base_settings = {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_recycle': self.pool_recycle,
            'pool_timeout': self.pool_timeout,
            'pool_pre_ping': self.pool_pre_ping,
            'connect_args': {
                'application_name': f'mingus_financial_{pool_name}',
                'options': (
                    f'-c timezone=utc '
                    f'-c statement_timeout={self.statement_timeout} '
                    f'-c idle_in_transaction_session_timeout={self.idle_in_transaction_timeout}'
                ),
                'connect_timeout': self.connect_timeout,
                'command_timeout': self.command_timeout,
                'sslmode': self.ssl_mode,
                'keepalives_idle': self.keepalives_idle,
                'keepalives_interval': self.keepalives_interval,
                'keepalives_count': self.keepalives_count
            }
        }
        
        # Pool-specific overrides
        if pool_name == 'celery':
            base_settings['pool_size'] = max(10, self.pool_size // 2)
            base_settings['max_overflow'] = max(20, self.max_overflow // 2)
            base_settings['pool_recycle'] = min(1800, self.pool_recycle // 2)
        
        elif pool_name == 'analytics':
            base_settings['pool_size'] = max(5, self.pool_size // 4)
            base_settings['max_overflow'] = max(10, self.max_overflow // 4)
            base_settings['pool_recycle'] = self.pool_recycle * 2
            base_settings['pool_timeout'] = self.pool_timeout * 2
        
        elif pool_name == 'financial':
            base_settings['pool_size'] = max(20, self.pool_size // 2)
            base_settings['max_overflow'] = max(40, self.max_overflow // 2)
            base_settings['pool_timeout'] = min(15, self.pool_timeout // 2)
        
        return base_settings


class DevelopmentDatabaseConfig(DatabaseConfig):
    """Development environment database configuration"""
    
    def __init__(self):
        super().__init__(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'mingus_dev'),
            username=os.getenv('DB_USER', 'mingus_user'),
            password=os.getenv('DB_PASSWORD', 'mingus_password'),
            
            # Development pool settings
            pool_size=int(os.getenv('DB_POOL_SIZE', '20')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '30')),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
            pool_pre_ping=True,
            
            # Development SSL settings
            ssl_mode=os.getenv('DB_SSL_MODE', 'prefer'),
            
            # Development monitoring (more frequent for debugging)
            health_check_interval=int(os.getenv('DB_HEALTH_CHECK_INTERVAL', '120')),
            critical_check_interval=int(os.getenv('DB_CRITICAL_CHECK_INTERVAL', '30')),
            consistency_check_interval=int(os.getenv('DB_CONSISTENCY_CHECK_INTERVAL', '1800')),
            
            # Development thresholds (more lenient)
            slow_query_threshold=float(os.getenv('DB_SLOW_QUERY_THRESHOLD', '2.0')),
            connection_leak_threshold=int(os.getenv('DB_CONNECTION_LEAK_THRESHOLD', '10')),
            error_rate_critical=float(os.getenv('DB_ERROR_RATE_CRITICAL', '0.15')),
            error_rate_warning=float(os.getenv('DB_ERROR_RATE_WARNING', '0.08'))
        )


class ProductionDatabaseConfig(DatabaseConfig):
    """Production environment database configuration for 1,000+ concurrent users"""
    
    def __init__(self):
        super().__init__(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'mingus_prod'),
            username=os.getenv('DB_USER', 'mingus_user'),
            password=os.getenv('DB_PASSWORD', 'mingus_password'),
            
            # Production pool settings - optimized for high concurrency
            pool_size=int(os.getenv('DB_POOL_SIZE', '50')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '100')),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
            pool_pre_ping=True,
            
            # Production SSL settings
            ssl_mode=os.getenv('DB_SSL_MODE', 'require'),
            ssl_cert=os.getenv('DB_SSL_CERT'),
            ssl_key=os.getenv('DB_SSL_KEY'),
            ssl_ca=os.getenv('DB_SSL_CA'),
            
            # Production monitoring (less frequent to reduce overhead)
            health_check_interval=int(os.getenv('DB_HEALTH_CHECK_INTERVAL', '300')),
            critical_check_interval=int(os.getenv('DB_CRITICAL_CHECK_INTERVAL', '60')),
            consistency_check_interval=int(os.getenv('DB_CONSISTENCY_CHECK_INTERVAL', '3600')),
            
            # Production thresholds (strict for financial data)
            slow_query_threshold=float(os.getenv('DB_SLOW_QUERY_THRESHOLD', '1.0')),
            connection_leak_threshold=int(os.getenv('DB_CONNECTION_LEAK_THRESHOLD', '5')),
            error_rate_critical=float(os.getenv('DB_ERROR_RATE_CRITICAL', '0.05')),
            error_rate_warning=float(os.getenv('DB_ERROR_RATE_WARNING', '0.02')),
            
            # Production performance settings
            statement_timeout=int(os.getenv('DB_STATEMENT_TIMEOUT', '30000')),
            idle_in_transaction_timeout=int(os.getenv('DB_IDLE_IN_TRANSACTION_TIMEOUT', '60000')),
            connect_timeout=int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
            command_timeout=int(os.getenv('DB_COMMAND_TIMEOUT', '30'))
        )


class TestingDatabaseConfig(DatabaseConfig):
    """Testing environment database configuration"""
    
    def __init__(self):
        super().__init__(
            host=os.getenv('TEST_DB_HOST', 'localhost'),
            port=int(os.getenv('TEST_DB_PORT', '5432')),
            database=os.getenv('TEST_DB_NAME', 'mingus_test'),
            username=os.getenv('TEST_DB_USER', 'mingus_test_user'),
            password=os.getenv('TEST_DB_PASSWORD', 'mingus_test_password'),
            
            # Testing pool settings (minimal for tests)
            pool_size=int(os.getenv('TEST_DB_POOL_SIZE', '5')),
            max_overflow=int(os.getenv('TEST_DB_MAX_OVERFLOW', '10')),
            pool_recycle=int(os.getenv('TEST_DB_POOL_RECYCLE', '1800')),
            pool_timeout=int(os.getenv('TEST_DB_POOL_TIMEOUT', '10')),
            pool_pre_ping=True,
            
            # Testing SSL settings
            ssl_mode=os.getenv('TEST_DB_SSL_MODE', 'prefer'),
            
            # Testing monitoring (very frequent for debugging)
            health_check_interval=int(os.getenv('TEST_DB_HEALTH_CHECK_INTERVAL', '60')),
            critical_check_interval=int(os.getenv('TEST_DB_CRITICAL_CHECK_INTERVAL', '15')),
            consistency_check_interval=int(os.getenv('TEST_DB_CONSISTENCY_CHECK_INTERVAL', '900')),
            
            # Testing thresholds (very lenient)
            slow_query_threshold=float(os.getenv('TEST_DB_SLOW_QUERY_THRESHOLD', '5.0')),
            connection_leak_threshold=int(os.getenv('TEST_DB_CONNECTION_LEAK_THRESHOLD', '20')),
            error_rate_critical=float(os.getenv('TEST_DB_ERROR_RATE_CRITICAL', '0.25')),
            error_rate_warning=float(os.getenv('TEST_DB_ERROR_RATE_WARNING', '0.15'))
        )


class StagingDatabaseConfig(DatabaseConfig):
    """Staging environment database configuration"""
    
    def __init__(self):
        super().__init__(
            host=os.getenv('STAGING_DB_HOST', 'localhost'),
            port=int(os.getenv('STAGING_DB_PORT', '5432')),
            database=os.getenv('STAGING_DB_NAME', 'mingus_staging'),
            username=os.getenv('STAGING_DB_USER', 'mingus_user'),
            password=os.getenv('STAGING_DB_PASSWORD', 'mingus_password'),
            
            # Staging pool settings (similar to production but smaller)
            pool_size=int(os.getenv('STAGING_DB_POOL_SIZE', '30')),
            max_overflow=int(os.getenv('STAGING_DB_MAX_OVERFLOW', '60')),
            pool_recycle=int(os.getenv('STAGING_DB_POOL_RECYCLE', '3600')),
            pool_timeout=int(os.getenv('STAGING_DB_POOL_TIMEOUT', '30')),
            pool_pre_ping=True,
            
            # Staging SSL settings
            ssl_mode=os.getenv('STAGING_DB_SSL_MODE', 'require'),
            
            # Staging monitoring (similar to production)
            health_check_interval=int(os.getenv('STAGING_DB_HEALTH_CHECK_INTERVAL', '300')),
            critical_check_interval=int(os.getenv('STAGING_DB_CRITICAL_CHECK_INTERVAL', '60')),
            consistency_check_interval=int(os.getenv('STAGING_DB_CONSISTENCY_CHECK_INTERVAL', '3600')),
            
            # Staging thresholds (similar to production)
            slow_query_threshold=float(os.getenv('STAGING_DB_SLOW_QUERY_THRESHOLD', '1.0')),
            connection_leak_threshold=int(os.getenv('STAGING_DB_CONNECTION_LEAK_THRESHOLD', '5')),
            error_rate_critical=float(os.getenv('STAGING_DB_ERROR_RATE_CRITICAL', '0.05')),
            error_rate_warning=float(os.getenv('STAGING_DB_ERROR_RATE_WARNING', '0.02'))
        )


def get_database_config(environment: str = None) -> DatabaseConfig:
    """Get database configuration for the specified environment"""
    if not environment:
        environment = os.getenv('FLASK_ENV', 'development')
    
    environment = environment.lower()
    
    if environment == 'production':
        return ProductionDatabaseConfig()
    elif environment == 'staging':
        return StagingDatabaseConfig()
    elif environment == 'testing':
        return TestingDatabaseConfig()
    else:
        return DevelopmentDatabaseConfig()


def get_environment_variables(environment: str = None) -> Dict[str, str]:
    """Get environment variables for database configuration"""
    config = get_database_config(environment)
    
    env_vars = {
        'DATABASE_URL': config.connection_string,
        'DB_HOST': config.host,
        'DB_PORT': str(config.port),
        'DB_NAME': config.database,
        'DB_USER': config.username,
        'DB_PASSWORD': config.password,
        
        # Connection pooling
        'DB_POOL_SIZE': str(config.pool_size),
        'DB_MAX_OVERFLOW': str(config.max_overflow),
        'DB_POOL_RECYCLE': str(config.pool_recycle),
        'DB_POOL_TIMEOUT': str(config.pool_timeout),
        'DB_POOL_PRE_PING': str(config.pool_pre_ping).lower(),
        
        # SSL settings
        'DB_SSL_MODE': config.ssl_mode,
        'DB_SSL_CERT': config.ssl_cert or '',
        'DB_SSL_KEY': config.ssl_key or '',
        'DB_SSL_CA': config.ssl_ca or '',
        
        # Performance settings
        'DB_STATEMENT_TIMEOUT': str(config.statement_timeout),
        'DB_IDLE_IN_TRANSACTION_TIMEOUT': str(config.idle_in_transaction_timeout),
        'DB_CONNECT_TIMEOUT': str(config.connect_timeout),
        'DB_COMMAND_TIMEOUT': str(config.command_timeout),
        
        # Keepalive settings
        'DB_KEEPALIVES_IDLE': str(config.keepalives_idle),
        'DB_KEEPALIVES_INTERVAL': str(config.keepalives_interval),
        'DB_KEEPALIVES_COUNT': str(config.keepalives_count),
        
        # Monitoring settings
        'DB_HEALTH_CHECK_INTERVAL': str(config.health_check_interval),
        'DB_CRITICAL_CHECK_INTERVAL': str(config.critical_check_interval),
        'DB_CONSISTENCY_CHECK_INTERVAL': str(config.consistency_check_interval),
        
        # Thresholds
        'DB_SLOW_QUERY_THRESHOLD': str(config.slow_query_threshold),
        'DB_CONNECTION_LEAK_THRESHOLD': str(config.connection_leak_threshold),
        'DB_ERROR_RATE_CRITICAL': str(config.error_rate_critical),
        'DB_ERROR_RATE_WARNING': str(config.error_rate_warning),
        
        # Pool-specific settings
        'CELERY_DB_POOL_SIZE': str(max(10, config.pool_size // 2)),
        'CELERY_DB_MAX_OVERFLOW': str(max(20, config.max_overflow // 2)),
        'CELERY_DB_POOL_RECYCLE': str(min(1800, config.pool_recycle // 2)),
        'CELERY_DB_POOL_TIMEOUT': str(config.pool_timeout),
        
        'ANALYTICS_DB_POOL_SIZE': str(max(5, config.pool_size // 4)),
        'ANALYTICS_DB_MAX_OVERFLOW': str(max(10, config.max_overflow // 4)),
        'ANALYTICS_DB_POOL_RECYCLE': str(config.pool_recycle * 2),
        'ANALYTICS_DB_POOL_TIMEOUT': str(config.pool_timeout * 2),
        
        'FINANCIAL_DB_POOL_SIZE': str(max(20, config.pool_size // 2)),
        'FINANCIAL_DB_MAX_OVERFLOW': str(max(40, config.max_overflow // 2)),
        'FINANCIAL_DB_POOL_RECYCLE': str(config.pool_recycle // 2),
        'FINANCIAL_DB_POOL_TIMEOUT': str(min(15, config.pool_timeout // 2)),
    }
    
    # Add read replica configuration if available
    read_replicas = os.getenv('DB_READ_REPLICAS', '')
    if read_replicas:
        env_vars['DB_READ_REPLICAS'] = read_replicas
        
        # Parse replica weights
        replica_urls = read_replicas.split(',')
        for i, url in enumerate(replica_urls):
            if url.strip():
                weight = os.getenv(f'DB_REPLICA_{i+1}_WEIGHT', '1')
                env_vars[f'DB_REPLICA_{i+1}_WEIGHT'] = weight
    
    return env_vars


def validate_database_config(config: DatabaseConfig) -> bool:
    """Validate database configuration"""
    errors = []
    
    # Check required fields
    if not config.host:
        errors.append("Database host is required")
    if not config.database:
        errors.append("Database name is required")
    if not config.username:
        errors.append("Database username is required")
    if not config.password:
        errors.append("Database password is required")
    
    # Check port range
    if not (1 <= config.port <= 65535):
        errors.append("Database port must be between 1 and 65535")
    
    # Check pool settings
    if config.pool_size < 1:
        errors.append("Pool size must be at least 1")
    if config.max_overflow < 0:
        errors.append("Max overflow must be non-negative")
    if config.pool_recycle < 0:
        errors.append("Pool recycle must be non-negative")
    if config.pool_timeout < 1:
        errors.append("Pool timeout must be at least 1 second")
    
    # Check timeouts
    if config.statement_timeout < 1000:
        errors.append("Statement timeout must be at least 1000ms")
    if config.idle_in_transaction_timeout < 1000:
        errors.append("Idle in transaction timeout must be at least 1000ms")
    
    # Check thresholds
    if not (0 < config.error_rate_critical < 1):
        errors.append("Error rate critical must be between 0 and 1")
    if not (0 < config.error_rate_warning < 1):
        errors.append("Error rate warning must be between 0 and 1")
    if config.error_rate_warning >= config.error_rate_critical:
        errors.append("Error rate warning must be less than error rate critical")
    
    if errors:
        raise ValueError(f"Database configuration validation failed: {'; '.join(errors)}")
    
    return True


# Export main classes and functions
__all__ = [
    'DatabaseConfig',
    'DevelopmentDatabaseConfig',
    'ProductionDatabaseConfig',
    'TestingDatabaseConfig',
    'StagingDatabaseConfig',
    'get_database_config',
    'get_environment_variables',
    'validate_database_config'
]
