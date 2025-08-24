"""
Prometheus metrics for health checks and application monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from flask import Response
import time
from functools import wraps

# Health check metrics
HEALTH_CHECK_DURATION = Histogram(
    'health_check_duration_seconds',
    'Time spent performing health checks',
    ['endpoint', 'component']
)

HEALTH_CHECK_FAILURES = Counter(
    'health_check_failures_total',
    'Total number of health check failures',
    ['endpoint', 'component', 'error_type']
)

HEALTH_CHECK_STATUS = Gauge(
    'health_check_status',
    'Current status of health checks (1=healthy, 0=unhealthy)',
    ['endpoint', 'component']
)

# Application metrics
APP_REQUEST_DURATION = Histogram(
    'app_request_duration_seconds',
    'Time spent processing requests',
    ['method', 'endpoint', 'status']
)

APP_REQUEST_COUNT = Counter(
    'app_request_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

# System metrics
SYSTEM_MEMORY_USAGE = Gauge(
    'system_memory_bytes',
    'Current memory usage in bytes',
    ['type']
)

SYSTEM_CPU_USAGE = Gauge(
    'system_cpu_percent',
    'Current CPU usage percentage'
)

SYSTEM_DISK_USAGE = Gauge(
    'system_disk_bytes',
    'Current disk usage in bytes',
    ['mount_point']
)

# Database metrics
DB_CONNECTION_POOL_SIZE = Gauge(
    'db_connection_pool_size',
    'Current database connection pool size',
    ['pool_type']
)

DB_CONNECTION_POOL_USED = Gauge(
    'db_connection_pool_used',
    'Number of database connections currently in use',
    ['pool_type']
)

# Redis metrics
REDIS_MEMORY_USAGE = Gauge(
    'redis_memory_bytes',
    'Current Redis memory usage in bytes'
)

REDIS_CONNECTED_CLIENTS = Gauge(
    'redis_connected_clients',
    'Number of clients connected to Redis'
)

def health_check_timer(endpoint, component):
    """Decorator to measure health check response times"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                HEALTH_CHECK_DURATION.labels(endpoint=endpoint, component=component).observe(duration)
                HEALTH_CHECK_STATUS.labels(endpoint=endpoint, component=component).set(1)
                return result
            except Exception as e:
                duration = time.time() - start_time
                HEALTH_CHECK_DURATION.labels(endpoint=endpoint, component=component).observe(duration)
                HEALTH_CHECK_STATUS.labels(endpoint=endpoint, component=component).set(0)
                HEALTH_CHECK_FAILURES.labels(
                    endpoint=endpoint, 
                    component=component, 
                    error_type=type(e).__name__
                ).inc()
                raise
        return wrapper
    return decorator

def record_health_check_failure(endpoint, component, error_type):
    """Record a health check failure"""
    HEALTH_CHECK_FAILURES.labels(
        endpoint=endpoint,
        component=component,
        error_type=error_type
    ).inc()
    HEALTH_CHECK_STATUS.labels(endpoint=endpoint, component=component).set(0)
    
    # Send alert if configured
    try:
        from .services.alerting_service import alerting_service
        alerting_service.alert_health_check_failure(endpoint, component, error_type)
    except Exception as e:
        print(f"Error sending alert: {e}")

def record_health_check_success(endpoint, component):
    """Record a successful health check"""
    HEALTH_CHECK_STATUS.labels(endpoint=endpoint, component=component).set(1)

def update_system_metrics():
    """Update system resource metrics"""
    try:
        import psutil
        
        # Memory metrics
        memory = psutil.virtual_memory()
        SYSTEM_MEMORY_USAGE.labels(type='total').set(memory.total)
        SYSTEM_MEMORY_USAGE.labels(type='available').set(memory.available)
        SYSTEM_MEMORY_USAGE.labels(type='used').set(memory.used)
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        SYSTEM_CPU_USAGE.set(cpu_percent)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        SYSTEM_DISK_USAGE.labels(mount_point='/').set(disk.used)
        
    except Exception as e:
        # Log error but don't fail
        print(f"Error updating system metrics: {e}")

def update_database_metrics(db):
    """Update database connection pool metrics"""
    try:
        if hasattr(db, 'engine') and hasattr(db.engine, 'pool'):
            pool = db.engine.pool
            DB_CONNECTION_POOL_SIZE.labels(pool_type='main').set(pool.size())
            DB_CONNECTION_POOL_USED.labels(pool_type='main').set(pool.checkedout())
    except Exception as e:
        print(f"Error updating database metrics: {e}")

def update_redis_metrics(redis_client):
    """Update Redis metrics"""
    try:
        info = redis_client.info()
        REDIS_MEMORY_USAGE.set(info.get('used_memory', 0))
        REDIS_CONNECTED_CLIENTS.set(info.get('connected_clients', 0))
    except Exception as e:
        print(f"Error updating Redis metrics: {e}")

def get_metrics():
    """Generate Prometheus metrics response"""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

def create_metrics_endpoint(app):
    """Create metrics endpoint for Prometheus scraping"""
    @app.route('/metrics')
    def metrics():
        """Prometheus metrics endpoint"""
        return get_metrics() 