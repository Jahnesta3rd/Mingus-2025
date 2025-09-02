"""
Performance Monitoring Configuration
Environment-specific configurations for development and production
"""

import os
from typing import Dict, Any

class MonitoringConfig:
    """Base monitoring configuration class"""
    
    # Performance thresholds (in milliseconds)
    PERFORMANCE_THRESHOLDS = {
        'slow_query_threshold_ms': 1000,      # 1 second
        'slow_api_threshold_ms': 2000,        # 2 seconds
        'slow_redis_threshold_ms': 100,       # 100ms
        'slow_celery_threshold_ms': 5000,     # 5 seconds
        'memory_usage_max_percent': 85,
        'cpu_usage_max_percent': 80,
        'disk_usage_max_percent': 90,
    }
    
    # Metrics storage limits
    MAX_METRICS_PER_TYPE = 10000
    METRICS_RETENTION_DAYS = 30
    
    # Monitoring intervals (in seconds)
    SYSTEM_MONITORING_INTERVAL = 60      # 1 minute
    DATABASE_MONITORING_INTERVAL = 30    # 30 seconds
    REDIS_MONITORING_INTERVAL = 30       # 30 seconds
    CLEANUP_INTERVAL = 3600              # 1 hour
    
    # Feature flags
    ENABLE_SQL_LOGGING = True
    ENABLE_REDIS_LOGGING = True
    ENABLE_CELERY_LOGGING = True
    ENABLE_WEB_VITALS = True
    ENABLE_DATABASE_CONNECTION_MONITORING = True
    ENABLE_REDIS_CONNECTION_MONITORING = True

class DevelopmentConfig(MonitoringConfig):
    """Development environment configuration"""
    
    # More verbose logging in development
    ENABLE_SQL_LOGGING = True
    ENABLE_REDIS_LOGGING = True
    ENABLE_CELERY_LOGGING = True
    ENABLE_WEB_VITALS = True
    
    # Lower thresholds for development testing
    PERFORMANCE_THRESHOLDS = {
        'slow_query_threshold_ms': 500,       # 500ms
        'slow_api_threshold_ms': 1000,        # 1 second
        'slow_redis_threshold_ms': 50,        # 50ms
        'slow_celery_threshold_ms': 2000,     # 2 seconds
        'memory_usage_max_percent': 90,
        'cpu_usage_max_percent': 90,
        'disk_usage_max_percent': 95,
    }
    
    # Shorter retention for development
    METRICS_RETENTION_DAYS = 7
    MAX_METRICS_PER_TYPE = 5000
    
    # More frequent monitoring in development
    SYSTEM_MONITORING_INTERVAL = 30      # 30 seconds
    DATABASE_MONITORING_INTERVAL = 15    # 15 seconds
    REDIS_MONITORING_INTERVAL = 15       # 15 seconds

class ProductionConfig(MonitoringConfig):
    """Production environment configuration"""
    
    # Conservative thresholds for production
    PERFORMANCE_THRESHOLDS = {
        'slow_query_threshold_ms': 2000,      # 2 seconds
        'slow_api_threshold_ms': 5000,        # 5 seconds
        'slow_redis_threshold_ms': 200,       # 200ms
        'slow_celery_threshold_ms': 10000,    # 10 seconds
        'memory_usage_max_percent': 80,
        'cpu_usage_max_percent': 75,
        'disk_usage_max_percent': 85,
    }
    
    # Longer retention for production analysis
    METRICS_RETENTION_DAYS = 90
    MAX_METRICS_PER_TYPE = 50000
    
    # Less frequent monitoring to reduce overhead
    SYSTEM_MONITORING_INTERVAL = 120     # 2 minutes
    DATABASE_MONITORING_INTERVAL = 60    # 1 minute
    REDIS_MONITORING_INTERVAL = 60       # 1 minute
    CLEANUP_INTERVAL = 7200              # 2 hours

class TestingConfig(MonitoringConfig):
    """Testing environment configuration"""
    
    # Minimal monitoring for testing
    ENABLE_SQL_LOGGING = False
    ENABLE_REDIS_LOGGING = False
    ENABLE_CELERY_LOGGING = False
    ENABLE_WEB_VITALS = False
    
    # Very low thresholds for testing
    PERFORMANCE_THRESHOLDS = {
        'slow_query_threshold_ms': 100,       # 100ms
        'slow_api_threshold_ms': 200,         # 200ms
        'slow_redis_threshold_ms': 10,        # 10ms
        'slow_celery_threshold_ms': 500,      # 500ms
        'memory_usage_max_percent': 95,
        'cpu_usage_max_percent': 95,
        'disk_usage_max_percent': 98,
    }
    
    # Minimal retention for testing
    METRICS_RETENTION_DAYS = 1
    MAX_METRICS_PER_TYPE = 1000
    
    # Very frequent monitoring for testing
    SYSTEM_MONITORING_INTERVAL = 10      # 10 seconds
    DATABASE_MONITORING_INTERVAL = 5     # 5 seconds
    REDIS_MONITORING_INTERVAL = 5        # 5 seconds
    CLEANUP_INTERVAL = 300               # 5 minutes

def get_monitoring_config(environment: str = None) -> Dict[str, Any]:
    """Get monitoring configuration for specified environment"""
    if environment is None:
        environment = os.getenv('FLASK_ENV', 'development')
    
    if environment == 'production':
        config_class = ProductionConfig
    elif environment == 'testing':
        config_class = TestingConfig
    else:
        config_class = DevelopmentConfig
    
    config = config_class()
    
    return {
        'performance_thresholds': config.PERFORMANCE_THRESHOLDS,
        'max_metrics_per_type': config.MAX_METRICS_PER_TYPE,
        'cleanup_interval_seconds': config.CLEANUP_INTERVAL,
        'system_monitoring_interval': config.SYSTEM_MONITORING_INTERVAL,
        'database_monitoring_interval': config.DATABASE_MONITORING_INTERVAL,
        'redis_monitoring_interval': config.REDIS_MONITORING_INTERVAL,
        'metrics_retention_days': config.METRICS_RETENTION_DAYS,
        'enable_sql_logging': config.ENABLE_SQL_LOGGING,
        'enable_redis_logging': config.ENABLE_REDIS_LOGGING,
        'enable_celery_logging': config.ENABLE_CELERY_LOGGING,
        'enable_web_vitals': config.ENABLE_WEB_VITALS,
        'enable_database_connection_monitoring': config.ENABLE_DATABASE_CONNECTION_MONITORING,
        'enable_redis_connection_monitoring': config.ENABLE_REDIS_CONNECTION_MONITORING,
        'environment': environment
    }

# Database connection monitoring configuration
DATABASE_MONITORING_CONFIG = {
    'postgresql': {
        'connection_pool_monitoring': True,
        'query_timeout_threshold': 30,  # seconds
        'connection_timeout_threshold': 5,  # seconds
        'max_connections_threshold': 100,
        'idle_connections_threshold': 10,
        'slow_query_logging': True,
        'query_plan_analysis': True,
        'table_size_monitoring': True,
        'index_usage_monitoring': True,
    },
    'redis': {
        'connection_pool_monitoring': True,
        'memory_usage_monitoring': True,
        'hit_rate_monitoring': True,
        'slow_operation_logging': True,
        'connection_timeout_threshold': 1,  # seconds
        'max_connections_threshold': 50,
        'idle_connections_threshold': 5,
    }
}

# Alerting configuration
ALERTING_CONFIG = {
    'email_alerts': {
        'enabled': False,
        'smtp_server': os.getenv('SMTP_SERVER'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'smtp_username': os.getenv('SMTP_USERNAME'),
        'smtp_password': os.getenv('SMTP_PASSWORD'),
        'from_email': os.getenv('ALERT_FROM_EMAIL'),
        'to_emails': os.getenv('ALERT_TO_EMAILS', '').split(','),
    },
    'slack_alerts': {
        'enabled': False,
        'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
        'channel': os.getenv('SLACK_CHANNEL', '#monitoring'),
    },
    'webhook_alerts': {
        'enabled': False,
        'webhook_url': os.getenv('WEBHOOK_URL'),
        'headers': {
            'Authorization': f"Bearer {os.getenv('WEBHOOK_TOKEN')}",
            'Content-Type': 'application/json'
        }
    },
    'alert_thresholds': {
        'critical_cpu_percent': 95,
        'critical_memory_percent': 95,
        'critical_disk_percent': 95,
        'critical_error_rate': 10,  # percentage
        'warning_cpu_percent': 80,
        'warning_memory_percent': 80,
        'warning_disk_percent': 80,
        'warning_error_rate': 5,  # percentage
    }
}

# Prometheus metrics configuration
PROMETHEUS_CONFIG = {
    'enabled': os.getenv('PROMETHEUS_ENABLED', 'false').lower() == 'true',
    'port': int(os.getenv('PROMETHEUS_PORT', 9090)),
    'metrics_path': '/metrics',
    'collect_default_metrics': True,
    'custom_metrics': {
        'flask_requests_total': True,
        'flask_request_duration_seconds': True,
        'database_queries_total': True,
        'database_query_duration_seconds': True,
        'redis_operations_total': True,
        'redis_operation_duration_seconds': True,
        'celery_tasks_total': True,
        'celery_task_duration_seconds': True,
        'system_cpu_percent': True,
        'system_memory_percent': True,
        'system_disk_percent': True,
    }
}

# Logging configuration
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_logging': {
        'enabled': True,
        'filename': 'performance_monitoring.log',
        'max_bytes': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
    },
    'syslog': {
        'enabled': False,
        'host': os.getenv('SYSLOG_HOST'),
        'port': int(os.getenv('SYSLOG_PORT', 514)),
        'facility': 'local0',
    }
}

# Development-specific overrides
if os.getenv('FLASK_ENV') == 'development':
    # Enable more verbose logging
    LOGGING_CONFIG['level'] = 'DEBUG'
    
    # Enable all monitoring features
    DATABASE_MONITORING_CONFIG['postgresql']['query_plan_analysis'] = True
    DATABASE_MONITORING_CONFIG['postgresql']['table_size_monitoring'] = True
    
    # Enable alerting for development
    ALERTING_CONFIG['email_alerts']['enabled'] = True
    ALERTING_CONFIG['slack_alerts']['enabled'] = True

# Production-specific overrides
if os.getenv('FLASK_ENV') == 'production':
    # Disable verbose logging in production
    LOGGING_CONFIG['level'] = 'WARNING'
    
    # Enable production alerting
    ALERTING_CONFIG['email_alerts']['enabled'] = True
    ALERTING_CONFIG['slack_alerts']['enabled'] = True
    
    # Enable Prometheus metrics
    PROMETHEUS_CONFIG['enabled'] = True
    
    # More conservative database monitoring
    DATABASE_MONITORING_CONFIG['postgresql']['query_plan_analysis'] = False
    DATABASE_MONITORING_CONFIG['postgresql']['table_size_monitoring'] = False
