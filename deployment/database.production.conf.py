"""
Production Database Configuration for MINGUS Application
Optimized for high-performance PostgreSQL with proper connection management
"""

import os
import ssl
from urllib.parse import urlparse

# =====================================================
# DATABASE CONNECTION CONFIGURATION
# =====================================================

# Primary database URL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production')

# Parse database URL for connection parameters
db_url_parts = urlparse(DATABASE_URL)

# =====================================================
# SQLALCHEMY ENGINE OPTIONS
# =====================================================

# Connection pooling - production optimized
SQLALCHEMY_ENGINE_OPTIONS = {
    # Pool configuration
    'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
    'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),  # 1 hour
    'pool_pre_ping': True,
    'pool_reset_on_return': 'commit',
    'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 30)),
    'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
    
    # Connection configuration
    'echo': os.environ.get('DB_ECHO', 'false').lower() == 'true',
    'echo_pool': os.environ.get('DB_ECHO_POOL', 'false').lower() == 'true',
    
    # SSL configuration for production
    'connect_args': {
        'sslmode': 'require',
        'ssl_cert': os.environ.get('DB_SSL_CERT'),
        'ssl_key': os.environ.get('DB_SSL_KEY'),
        'ssl_ca': os.environ.get('DB_SSL_CA'),
        'application_name': 'mingus_production',
        'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', 10)),
        'options': '-c statement_timeout=300000 -c idle_in_transaction_session_timeout=300000'
    }
}

# =====================================================
# DATABASE PERFORMANCE SETTINGS
# =====================================================

# Statement timeout (5 minutes)
DB_STATEMENT_TIMEOUT = int(os.environ.get('DB_STATEMENT_TIMEOUT', 300000))  # milliseconds

# Idle transaction timeout (5 minutes)
DB_IDLE_IN_TRANSACTION_TIMEOUT = int(os.environ.get('DB_IDLE_IN_TRANSACTION_TIMEOUT', 300000))  # milliseconds

# Lock timeout (30 seconds)
DB_LOCK_TIMEOUT = int(os.environ.get('DB_LOCK_TIMEOUT', 30000))  # milliseconds

# Deadlock timeout (1 second)
DB_DEADLOCK_TIMEOUT = int(os.environ.get('DB_DEADLOCK_TIMEOUT', 1000))  # milliseconds

# =====================================================
# CONNECTION POOL OPTIMIZATION
# =====================================================

# Pool size calculation based on workers
def calculate_pool_size():
    """Calculate optimal pool size based on Gunicorn workers"""
    gunicorn_workers = int(os.environ.get('GUNICORN_WORKERS', 4))
    base_pool_size = int(os.environ.get('DB_POOL_SIZE', 20))
    
    # Ensure minimum pool size per worker
    min_pool_per_worker = 5
    calculated_pool_size = max(base_pool_size, gunicorn_workers * min_pool_per_worker)
    
    # Cap at reasonable maximum
    max_pool_size = 100
    return min(calculated_pool_size, max_pool_size)

# Update pool size if not explicitly set
if not os.environ.get('DB_POOL_SIZE'):
    SQLALCHEMY_ENGINE_OPTIONS['pool_size'] = calculate_pool_size()

# =====================================================
# SSL/TLS CONFIGURATION
# =====================================================

# SSL context for database connections
def create_ssl_context():
    """Create SSL context for database connections"""
    ssl_context = ssl.create_default_context()
    
    # SSL certificate verification
    if os.environ.get('DB_SSL_CA'):
        ssl_context.load_verify_locations(os.environ.get('DB_SSL_CA'))
    
    # Client certificate (if required)
    if os.environ.get('DB_SSL_CERT') and os.environ.get('DB_SSL_KEY'):
        ssl_context.load_cert_chain(
            certfile=os.environ.get('DB_SSL_CERT'),
            keyfile=os.environ.get('DB_SSL_KEY')
        )
    
    # SSL verification mode
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = True
    
    return ssl_context

# Add SSL context to connection args if SSL is enabled
if os.environ.get('DB_SSL_ENABLED', 'true').lower() == 'true':
    try:
        ssl_context = create_ssl_context()
        SQLALCHEMY_ENGINE_OPTIONS['connect_args']['sslmode'] = 'require'
        SQLALCHEMY_ENGINE_OPTIONS['connect_args']['ssl_context'] = ssl_context
    except Exception as e:
        # Fallback to basic SSL if context creation fails
        SQLALCHEMY_ENGINE_OPTIONS['connect_args']['sslmode'] = 'require'

# =====================================================
# DATABASE MONITORING AND METRICS
# =====================================================

# Performance monitoring settings
DB_PERFORMANCE_MONITORING = {
    'enabled': os.environ.get('DB_PERFORMANCE_MONITORING', 'true').lower() == 'true',
    'slow_query_threshold': int(os.environ.get('DB_SLOW_QUERY_THRESHOLD', 1000)),  # milliseconds
    'log_slow_queries': os.environ.get('DB_LOG_SLOW_QUERIES', 'true').lower() == 'true',
    'track_connection_usage': os.environ.get('DB_TRACK_CONNECTION_USAGE', 'true').lower() == 'true',
    'metrics_interval': int(os.environ.get('DB_METRICS_INTERVAL', 60))  # seconds
}

# =====================================================
# DATABASE MAINTENANCE SETTINGS
# =====================================================

# Maintenance configuration
DB_MAINTENANCE = {
    'auto_vacuum': os.environ.get('DB_AUTO_VACUUM', 'true').lower() == 'true',
    'auto_analyze': os.environ.get('DB_AUTO_ANALYZE', 'true').lower() == 'true',
    'vacuum_threshold': int(os.environ.get('DB_VACUUM_THRESHOLD', 50)),
    'analyze_threshold': int(os.environ.get('DB_ANALYZE_THRESHOLD', 10)),
    'maintenance_window_start': os.environ.get('DB_MAINTENANCE_WINDOW_START', '02:00'),
    'maintenance_window_end': os.environ.get('DB_MAINTENANCE_WINDOW_END', '04:00')
}

# =====================================================
# BACKUP CONFIGURATION
# =====================================================

# Backup settings
DB_BACKUP_CONFIG = {
    'enabled': os.environ.get('DB_BACKUP_ENABLED', 'true').lower() == 'true',
    'backup_interval': int(os.environ.get('DB_BACKUP_INTERVAL', 86400)),  # 24 hours
    'backup_retention_days': int(os.environ.get('DB_BACKUP_RETENTION_DAYS', 30)),
    'backup_compression': os.environ.get('DB_BACKUP_COMPRESSION', 'gzip'),
    'backup_directory': os.environ.get('DB_BACKUP_DIRECTORY', '/app/backups/database'),
    'pg_dump_options': os.environ.get('DB_PG_DUMP_OPTIONS', '--verbose --clean --no-owner --no-privileges')
}

# =====================================================
# SECURITY CONFIGURATION
# =====================================================

# Security settings
DB_SECURITY_CONFIG = {
    'row_level_security': os.environ.get('DB_ROW_LEVEL_SECURITY', 'true').lower() == 'true',
    'encryption_at_rest': os.environ.get('DB_ENCRYPTION_AT_REST', 'true').lower() == 'true',
    'connection_encryption': os.environ.get('DB_CONNECTION_ENCRYPTION', 'true').lower() == 'true',
    'audit_logging': os.environ.get('DB_AUDIT_LOGGING', 'true').lower() == 'true',
    'max_connections_per_user': int(os.environ.get('DB_MAX_CONNECTIONS_PER_USER', 10))
}

# =====================================================
# READ REPLICA CONFIGURATION
# =====================================================

# Read replica settings (for scaling)
READ_REPLICA_URL = os.environ.get('READ_REPLICA_URL')
READ_REPLICA_POOL_SIZE = int(os.environ.get('READ_REPLICA_POOL_SIZE', 10))
READ_REPLICA_MAX_OVERFLOW = int(os.environ.get('READ_REPLICA_MAX_OVERFLOW', 20))

# Read replica engine options
if READ_REPLICA_URL:
    READ_REPLICA_ENGINE_OPTIONS = {
        'pool_size': READ_REPLICA_POOL_SIZE,
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'pool_reset_on_return': 'commit',
        'max_overflow': READ_REPLICA_MAX_OVERFLOW,
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'echo': False,
        'connect_args': {
            'sslmode': 'require',
            'application_name': 'mingus_read_replica',
            'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', 10)),
            'options': '-c statement_timeout=300000'
        }
    }
else:
    READ_REPLICA_ENGINE_OPTIONS = None

# =====================================================
# CONNECTION HEALTH CHECKS
# =====================================================

# Health check configuration
DB_HEALTH_CHECK = {
    'enabled': os.environ.get('DB_HEALTH_CHECK_ENABLED', 'true').lower() == 'true',
    'interval': int(os.environ.get('DB_HEALTH_CHECK_INTERVAL', 30)),  # seconds
    'timeout': int(os.environ.get('DB_HEALTH_CHECK_TIMEOUT', 5)),  # seconds
    'max_retries': int(os.environ.get('DB_HEALTH_CHECK_MAX_RETRIES', 3)),
    'query': 'SELECT 1'  # Simple health check query
}

# =====================================================
# QUERY OPTIMIZATION
# =====================================================

# Query optimization settings
DB_QUERY_OPTIMIZATION = {
    'enable_query_cache': os.environ.get('DB_ENABLE_QUERY_CACHE', 'true').lower() == 'true',
    'query_cache_ttl': int(os.environ.get('DB_QUERY_CACHE_TTL', 300)),  # 5 minutes
    'max_query_time': int(os.environ.get('DB_MAX_QUERY_TIME', 300)),  # 5 minutes
    'enable_query_logging': os.environ.get('DB_ENABLE_QUERY_LOGGING', 'false').lower() == 'true',
    'log_slow_queries': os.environ.get('DB_LOG_SLOW_QUERIES', 'true').lower() == 'true',
    'slow_query_threshold': int(os.environ.get('DB_SLOW_QUERY_THRESHOLD', 1000))  # milliseconds
}

# =====================================================
# PRODUCTION-SPECIFIC OVERRIDES
# =====================================================

# Production-specific settings
if os.environ.get('FLASK_ENV') == 'production':
    # Increase pool size for production
    SQLALCHEMY_ENGINE_OPTIONS['pool_size'] = max(
        SQLALCHEMY_ENGINE_OPTIONS['pool_size'], 
        20
    )
    
    # Increase max overflow for production
    SQLALCHEMY_ENGINE_OPTIONS['max_overflow'] = max(
        SQLALCHEMY_ENGINE_OPTIONS['max_overflow'], 
        30
    )
    
    # Enable connection encryption
    SQLALCHEMY_ENGINE_OPTIONS['connect_args']['sslmode'] = 'require'
    
    # Increase timeouts for production
    SQLALCHEMY_ENGINE_OPTIONS['connect_args']['options'] = (
        '-c statement_timeout=600000 '  # 10 minutes
        '-c idle_in_transaction_session_timeout=600000 '  # 10 minutes
        '-c lock_timeout=60000 '  # 1 minute
        '-c deadlock_timeout=1000'  # 1 second
    )

# =====================================================
# CONFIGURATION VALIDATION
# =====================================================

# Validate configuration
def validate_database_config():
    """Validate database configuration settings"""
    errors = []
    
    # Validate pool size
    if SQLALCHEMY_ENGINE_OPTIONS['pool_size'] < 1:
        errors.append("DB_POOL_SIZE must be at least 1")
    
    # Validate max overflow
    if SQLALCHEMY_ENGINE_OPTIONS['max_overflow'] < 0:
        errors.append("DB_MAX_OVERFLOW must be non-negative")
    
    # Validate timeouts
    if DB_STATEMENT_TIMEOUT < 1000:
        errors.append("DB_STATEMENT_TIMEOUT must be at least 1000ms")
    
    if DB_IDLE_IN_TRANSACTION_TIMEOUT < 1000:
        errors.append("DB_IDLE_IN_TRANSACTION_TIMEOUT must be at least 1000ms")
    
    return errors

# =====================================================
# CONFIGURATION EXPORT
# =====================================================

# Export configuration for use in application
DATABASE_CONFIG = {
    'url': DATABASE_URL,
    'engine_options': SQLALCHEMY_ENGINE_OPTIONS,
    'read_replica_url': READ_REPLICA_URL,
    'read_replica_engine_options': READ_REPLICA_ENGINE_OPTIONS,
    'performance_monitoring': DB_PERFORMANCE_MONITORING,
    'maintenance': DB_MAINTENANCE,
    'backup': DB_BACKUP_CONFIG,
    'security': DB_SECURITY_CONFIG,
    'health_check': DB_HEALTH_CHECK,
    'query_optimization': DB_QUERY_OPTIMIZATION,
    'timeouts': {
        'statement_timeout': DB_STATEMENT_TIMEOUT,
        'idle_in_transaction_timeout': DB_IDLE_IN_TRANSACTION_TIMEOUT,
        'lock_timeout': DB_LOCK_TIMEOUT,
        'deadlock_timeout': DB_DEADLOCK_TIMEOUT
    }
}

# =====================================================
# LOGGING CONFIGURATION
# =====================================================

# Log final configuration
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_database_config():
    """Log database configuration for debugging"""
    logger.info("=" * 60)
    logger.info("MINGUS PRODUCTION DATABASE CONFIGURATION")
    logger.info("=" * 60)
    logger.info(f"Database URL: {DATABASE_URL}")
    logger.info(f"Pool Size: {SQLALCHEMY_ENGINE_OPTIONS['pool_size']}")
    logger.info(f"Max Overflow: {SQLALCHEMY_ENGINE_OPTIONS['max_overflow']}")
    logger.info(f"Pool Recycle: {SQLALCHEMY_ENGINE_OPTIONS['pool_recycle']}s")
    logger.info(f"Statement Timeout: {DB_STATEMENT_TIMEOUT}ms")
    logger.info(f"SSL Mode: {SQLALCHEMY_ENGINE_OPTIONS['connect_args'].get('sslmode', 'disabled')}")
    logger.info(f"Read Replica: {'Enabled' if READ_REPLICA_URL else 'Disabled'}")
    logger.info("=" * 60)

# Log configuration if this module is imported
if __name__ != '__main__':
    log_database_config() 