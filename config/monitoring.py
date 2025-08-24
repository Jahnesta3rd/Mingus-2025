"""
Monitoring and Metrics Configuration
"""
import os

class MonitoringConfig:
    """Configuration for monitoring and metrics"""
    
    # Prometheus Configuration
    PROMETHEUS_ENABLED = os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true'
    PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', '9090'))
    PROMETHEUS_PATH = os.getenv('PROMETHEUS_PATH', '/metrics')
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT = int(os.getenv('HEALTH_CHECK_TIMEOUT', '30'))
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))
    
    # Alerting Configuration
    ALERTING_ENABLED = os.getenv('ALERTING_ENABLED', 'false').lower() == 'true'
    ALERT_WEBHOOK_URL = os.getenv('ALERT_WEBHOOK_URL', '')
    ALERT_SLACK_WEBHOOK = os.getenv('ALERT_SLACK_WEBHOOK', '')
    
    # Thresholds for Alerting
    HEALTH_CHECK_FAILURE_THRESHOLD = int(os.getenv('HEALTH_CHECK_FAILURE_THRESHOLD', '3'))
    RESPONSE_TIME_THRESHOLD_MS = int(os.getenv('RESPONSE_TIME_THRESHOLD_MS', '5000'))
    MEMORY_USAGE_THRESHOLD_PERCENT = int(os.getenv('MEMORY_USAGE_THRESHOLD_PERCENT', '90'))
    CPU_USAGE_THRESHOLD_PERCENT = int(os.getenv('CPU_USAGE_THRESHOLD_PERCENT', '80'))
    DISK_USAGE_THRESHOLD_PERCENT = int(os.getenv('DISK_USAGE_THRESHOLD_PERCENT', '85'))
    
    # Database Connection Pool Thresholds
    DB_POOL_UTILIZATION_THRESHOLD = float(os.getenv('DB_POOL_UTILIZATION_THRESHOLD', '0.8'))
    DB_CONNECTION_TIMEOUT_THRESHOLD_MS = int(os.getenv('DB_CONNECTION_TIMEOUT_THRESHOLD_MS', '1000'))
    
    # Redis Thresholds
    REDIS_MEMORY_THRESHOLD_PERCENT = int(os.getenv('REDIS_MEMORY_THRESHOLD_PERCENT', '80'))
    REDIS_CONNECTION_TIMEOUT_THRESHOLD_MS = int(os.getenv('REDIS_CONNECTION_TIMEOUT_THRESHOLD_MS', '500'))
    
    # External API Thresholds
    EXTERNAL_API_TIMEOUT_THRESHOLD_MS = int(os.getenv('EXTERNAL_API_TIMEOUT_THRESHOLD_MS', '3000'))
    EXTERNAL_API_FAILURE_THRESHOLD = int(os.getenv('EXTERNAL_API_FAILURE_THRESHOLD', '2'))
    
    # Metrics Retention
    METRICS_RETENTION_HOURS = int(os.getenv('METRICS_RETENTION_HOURS', '24'))
    
    # Logging Configuration
    METRICS_LOGGING_ENABLED = os.getenv('METRICS_LOGGING_ENABLED', 'true').lower() == 'true'
    METRICS_LOG_LEVEL = os.getenv('METRICS_LOG_LEVEL', 'INFO') 