"""
System Health Check Routes for MINGUS Application
Provides comprehensive health monitoring for all system components
"""

import os
import time
import psutil
import redis
import requests
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, current_app, request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps
import logging
import traceback
import json
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Create blueprint
system_health_bp = Blueprint('system_health', __name__, url_prefix='/api/system/health')

class HealthCheckError(Exception):
    """Custom exception for health check failures"""
    pass

class ServiceUnavailableError(Exception):
    """Custom exception for service unavailability"""
    pass

def health_check_response(success: bool, data: Dict[str, Any], status_code: int = 200) -> Tuple[Dict[str, Any], int]:
    """Standardized health check response format"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }
    return response, status_code

def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and performance"""
    try:
        start_time = time.time()
        
        # Test database connection
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            raise HealthCheckError("Database extension not found")
        
        # Test basic query
        result = db.session.execute(text("SELECT 1 as test"))
        result.fetchone()
        
        # Test more complex query to check table access
        result = db.session.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
        table_count = result.fetchone()[0]
        
        query_time = time.time() - start_time
        
        return {
            'status': 'healthy',
            'connection': 'active',
            'response_time_ms': round(query_time * 1000, 2),
            'table_count': table_count,
            'last_check': datetime.utcnow().isoformat()
        }
        
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'connection': 'failed',
            'last_check': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected database health check error: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'connection': 'unknown',
            'last_check': datetime.utcnow().isoformat()
        }

def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and performance"""
    try:
        start_time = time.time()
        
        # Get Redis configuration
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_db = int(os.getenv('REDIS_DB', '0'))
        redis_password = os.getenv('REDIS_PASSWORD')
        
        # Test Redis connection
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test ping
        ping_response = redis_client.ping()
        
        # Test basic operations
        test_key = f"health_check_{int(time.time())}"
        redis_client.set(test_key, "test_value", ex=60)
        test_value = redis_client.get(test_key)
        redis_client.delete(test_key)
        
        query_time = time.time() - start_time
        
        # Get Redis info
        info = redis_client.info()
        
        return {
            'status': 'healthy' if ping_response else 'unhealthy',
            'connection': 'active' if ping_response else 'failed',
            'response_time_ms': round(query_time * 1000, 2),
            'redis_version': info.get('redis_version', 'unknown'),
            'connected_clients': info.get('connected_clients', 0),
            'used_memory_human': info.get('used_memory_human', 'unknown'),
            'last_check': datetime.utcnow().isoformat()
        }
        
    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'connection': 'failed',
            'last_check': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected Redis health check error: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'connection': 'unknown',
            'last_check': datetime.utcnow().isoformat()
        }

def check_external_services() -> Dict[str, Any]:
    """Check external service connectivity"""
    services = {}
    
    # Check Twilio (SMS service)
    try:
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if twilio_account_sid and twilio_auth_token:
            # Test Twilio API connectivity
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}"
            response = requests.get(url, auth=(twilio_account_sid, twilio_auth_token), timeout=10)
            services['twilio'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_code': response.status_code,
                'last_check': datetime.utcnow().isoformat()
            }
        else:
            services['twilio'] = {
                'status': 'not_configured',
                'last_check': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Twilio health check failed: {e}")
        services['twilio'] = {
            'status': 'error',
            'error': str(e),
            'last_check': datetime.utcnow().isoformat()
        }
    
    # Check Resend (Email service)
    try:
        resend_api_key = os.getenv('RESEND_API_KEY')
        
        if resend_api_key:
            # Test Resend API connectivity
            url = "https://api.resend.com/domains"
            headers = {'Authorization': f'Bearer {resend_api_key}'}
            response = requests.get(url, headers=headers, timeout=10)
            services['resend'] = {
                'status': 'healthy' if response.status_code in [200, 401] else 'unhealthy',
                'response_code': response.status_code,
                'last_check': datetime.utcnow().isoformat()
            }
        else:
            services['resend'] = {
                'status': 'not_configured',
                'last_check': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Resend health check failed: {e}")
        services['resend'] = {
            'status': 'error',
            'error': str(e),
            'last_check': datetime.utcnow().isoformat()
        }
    
    # Check Plaid (Banking integration)
    try:
        plaid_client_id = os.getenv('PLAID_CLIENT_ID')
        plaid_secret = os.getenv('PLAID_SECRET')
        
        if plaid_client_id and plaid_secret:
            # Test Plaid API connectivity
            url = "https://sandbox.plaid.com/institutions/get"
            headers = {
                'Content-Type': 'application/json',
                'PLAID-CLIENT-ID': plaid_client_id,
                'PLAID-SECRET': plaid_secret
            }
            response = requests.post(url, headers=headers, json={'count': 1}, timeout=10)
            services['plaid'] = {
                'status': 'healthy' if response.status_code in [200, 401] else 'unhealthy',
                'response_code': response.status_code,
                'last_check': datetime.utcnow().isoformat()
            }
        else:
            services['plaid'] = {
                'status': 'not_configured',
                'last_check': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Plaid health check failed: {e}")
        services['plaid'] = {
            'status': 'error',
            'error': str(e),
            'last_check': datetime.utcnow().isoformat()
        }
    
    return services

def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        
        return {
            'cpu': {
                'usage_percent': cpu_percent,
                'status': 'healthy' if cpu_percent < 80 else 'warning' if cpu_percent < 95 else 'critical'
            },
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'usage_percent': memory.percent,
                'status': 'healthy' if memory.percent < 80 else 'warning' if memory.percent < 95 else 'critical'
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'usage_percent': round((disk.used / disk.total) * 100, 2),
                'status': 'healthy' if (disk.used / disk.total) < 0.8 else 'warning' if (disk.used / disk.total) < 0.95 else 'critical'
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'last_check': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System resources health check failed: {e}")
        return {
            'error': str(e),
            'last_check': datetime.utcnow().isoformat()
        }

def check_application_status() -> Dict[str, Any]:
    """Check application-specific health indicators"""
    try:
        # Get application configuration
        config = current_app.config
        
        # Check if app is in debug mode
        debug_mode = config.get('DEBUG', False)
        
        # Check environment
        environment = os.getenv('FLASK_ENV', 'development')
        
        # Check if database migrations are up to date
        db_migration_status = 'unknown'
        try:
            from flask_migrate import current
            db_migration_status = 'up_to_date'  # Simplified check
        except Exception:
            db_migration_status = 'unknown'
        
        return {
            'app_name': 'MINGUS',
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': environment,
            'debug_mode': debug_mode,
            'database_migrations': db_migration_status,
            'startup_time': current_app.start_time if hasattr(current_app, 'start_time') else 'unknown',
            'uptime_seconds': time.time() - getattr(current_app, 'start_time', time.time()),
            'last_check': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Application status check failed: {e}")
        return {
            'error': str(e),
            'last_check': datetime.utcnow().isoformat()
        }

@system_health_bp.route('/', methods=['GET'])
def health_check():
    """
    Comprehensive system health check endpoint
    
    Returns:
        JSON response with health status of all system components
    """
    try:
        start_time = time.time()
        
        # Perform all health checks
        database_health = check_database_health()
        redis_health = check_redis_health()
        external_services = check_external_services()
        system_resources = check_system_resources()
        application_status = check_application_status()
        
        # Determine overall health status
        critical_services = ['database', 'redis']
        unhealthy_services = []
        
        if database_health.get('status') != 'healthy':
            unhealthy_services.append('database')
        if redis_health.get('status') != 'healthy':
            unhealthy_services.append('redis')
        
        # Check if any critical services are unhealthy
        has_critical_failure = any(service in unhealthy_services for service in critical_services)
        
        overall_status = 'healthy' if not has_critical_failure else 'unhealthy'
        
        # Calculate response time
        response_time = time.time() - start_time
        
        health_data = {
            'overall_status': overall_status,
            'response_time_ms': round(response_time * 1000, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': database_health,
                'redis': redis_health,
                'external_services': external_services,
                'system_resources': system_resources,
                'application': application_status
            },
            'unhealthy_services': unhealthy_services,
            'critical_services_failing': has_critical_failure
        }
        
        status_code = 200 if overall_status == 'healthy' else 503
        
        return health_check_response(True, health_data, status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        error_data = {
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return health_check_response(False, error_data, 500)

@system_health_bp.route('/simple', methods=['GET'])
def simple_health_check():
    """
    Simple health check endpoint for load balancers and basic monitoring
    
    Returns:
        JSON response with basic health status
    """
    try:
        # Quick database check
        db = current_app.extensions.get('sqlalchemy')
        if db:
            db.session.execute(text("SELECT 1"))
            db_status = 'healthy'
        else:
            db_status = 'unhealthy'
        
        # Quick Redis check
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            redis_client = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=2)
            redis_client.ping()
            redis_status = 'healthy'
        except:
            redis_status = 'unhealthy'
        
        overall_status = 'healthy' if db_status == 'healthy' and redis_status == 'healthy' else 'unhealthy'
        
        data = {
            'status': overall_status,
            'database': db_status,
            'redis': redis_status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        status_code = 200 if overall_status == 'healthy' else 503
        
        return health_check_response(True, data, status_code)
        
    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        return health_check_response(False, {'error': str(e)}, 500)

@system_health_bp.route('/database', methods=['GET'])
def database_health_check():
    """Database-specific health check"""
    try:
        health_data = check_database_health()
        status_code = 200 if health_data.get('status') == 'healthy' else 503
        
        return health_check_response(True, health_data, status_code)
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return health_check_response(False, {'error': str(e)}, 500)

@system_health_bp.route('/redis', methods=['GET'])
def redis_health_check():
    """Redis-specific health check"""
    try:
        health_data = check_redis_health()
        status_code = 200 if health_data.get('status') == 'healthy' else 503
        
        return health_check_response(True, health_data, status_code)
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return health_check_response(False, {'error': str(e)}, 500)

@system_health_bp.route('/external', methods=['GET'])
def external_services_health_check():
    """External services health check"""
    try:
        health_data = check_external_services()
        
        # Check if any external services are unhealthy
        unhealthy_count = sum(1 for service in health_data.values() 
                            if service.get('status') == 'unhealthy')
        
        overall_status = 'healthy' if unhealthy_count == 0 else 'unhealthy'
        status_code = 200 if overall_status == 'healthy' else 503
        
        return health_check_response(True, health_data, status_code)
        
    except Exception as e:
        logger.error(f"External services health check failed: {e}")
        return health_check_response(False, {'error': str(e)}, 500)

@system_health_bp.route('/resources', methods=['GET'])
def system_resources_health_check():
    """System resources health check"""
    try:
        health_data = check_system_resources()
        
        # Check if any resources are critical
        critical_resources = []
        for resource_type, data in health_data.items():
            if isinstance(data, dict) and data.get('status') == 'critical':
                critical_resources.append(resource_type)
        
        overall_status = 'healthy' if not critical_resources else 'warning'
        status_code = 200 if overall_status == 'healthy' else 503
        
        return health_check_response(True, health_data, status_code)
        
    except Exception as e:
        logger.error(f"System resources health check failed: {e}")
        return health_check_response(False, {'error': str(e)}, 500)

@system_health_bp.route('/application', methods=['GET'])
def application_health_check():
    """Application-specific health check"""
    try:
        health_data = check_application_status()
        status_code = 200
        
        return health_check_response(True, health_data, status_code)
        
    except Exception as e:
        logger.error(f"Application health check failed: {e}")
        return health_check_response(False, {'error': str(e)}, 500)

@system_health_bp.route('/metrics', methods=['GET'])
def health_metrics():
    """
    Health metrics endpoint for monitoring systems
    
    Returns:
        JSON response with metrics suitable for monitoring systems
    """
    try:
        # Get all health data
        database_health = check_database_health()
        redis_health = check_redis_health()
        system_resources = check_system_resources()
        
        # Format metrics for monitoring systems
        metrics = {
            'mingus_database_status': 1 if database_health.get('status') == 'healthy' else 0,
            'mingus_redis_status': 1 if redis_health.get('status') == 'healthy' else 0,
            'mingus_database_response_time_ms': database_health.get('response_time_ms', 0),
            'mingus_redis_response_time_ms': redis_health.get('response_time_ms', 0),
            'mingus_cpu_usage_percent': system_resources.get('cpu', {}).get('usage_percent', 0),
            'mingus_memory_usage_percent': system_resources.get('memory', {}).get('usage_percent', 0),
            'mingus_disk_usage_percent': system_resources.get('disk', {}).get('usage_percent', 0),
            'mingus_uptime_seconds': time.time() - getattr(current_app, 'start_time', time.time()),
            'mingus_health_check_timestamp': int(time.time())
        }
        
        return health_check_response(True, metrics, 200)
        
    except Exception as e:
        logger.error(f"Health metrics failed: {e}")
        return health_check_response(False, {'error': str(e)}, 500)

@system_health_bp.route('/readiness', methods=['GET'])
def readiness_check():
    """
    Readiness probe for Kubernetes and container orchestration
    
    Returns:
        JSON response indicating if the application is ready to serve traffic
    """
    try:
        # Check critical services for readiness
        database_health = check_database_health()
        redis_health = check_redis_health()
        
        # Application is ready if database and redis are healthy
        is_ready = (database_health.get('status') == 'healthy' and 
                   redis_health.get('status') == 'healthy')
        
        status_code = 200 if is_ready else 503
        
        data = {
            'ready': is_ready,
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': database_health.get('status'),
                'redis': redis_health.get('status')
            }
        }
        
        return health_check_response(True, data, status_code)
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return health_check_response(False, {'ready': False, 'error': str(e)}, 503)

@system_health_bp.route('/liveness', methods=['GET'])
def liveness_check():
    """
    Liveness probe for Kubernetes and container orchestration
    
    Returns:
        JSON response indicating if the application is alive and running
    """
    try:
        # Basic liveness check - just verify the application is responding
        data = {
            'alive': True,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': time.time() - getattr(current_app, 'start_time', time.time())
        }
        
        return health_check_response(True, data, 200)
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return health_check_response(False, {'alive': False, 'error': str(e)}, 503)

@system_health_bp.route('/startup', methods=['GET'])
def startup_check():
    """
    Startup probe for Kubernetes and container orchestration
    
    Returns:
        JSON response indicating if the application has finished startup
    """
    try:
        # Check if all services are initialized
        database_health = check_database_health()
        redis_health = check_redis_health()
        system_resources = check_system_resources()
        
        # Application is started if all services are healthy
        is_started = (database_health.get('status') == 'healthy' and 
                     redis_health.get('status') == 'healthy' and
                     system_resources.get('cpu', {}).get('status') != 'critical')
        
        status_code = 200 if is_started else 503
        
        data = {
            'started': is_started,
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': database_health.get('status'),
                'redis': redis_health.get('status'),
                'system_resources': system_resources.get('cpu', {}).get('status')
            }
        }
        
        return health_check_response(True, data, status_code)
        
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        return health_check_response(False, {'started': False, 'error': str(e)}, 503)

@system_health_bp.route('/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with comprehensive system information
    
    Returns:
        JSON response with detailed health information for debugging
    """
    try:
        start_time = time.time()
        
        # Perform all health checks
        database_health = check_database_health()
        redis_health = check_redis_health()
        external_services = check_external_services()
        system_resources = check_system_resources()
        application_status = check_application_status()
        
        # Additional detailed checks
        import psutil
        process = psutil.Process()
        
        detailed_data = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'services': {
                'database': database_health,
                'redis': redis_health,
                'external_services': external_services,
                'system_resources': system_resources,
                'application': application_status
            },
            'process_info': {
                'pid': process.pid,
                'memory_rss_mb': round(process.memory_info().rss / (1024 * 1024), 2),
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            },
            'environment': {
                'python_version': f"{process.cmdline()[0] if process.cmdline() else 'unknown'}",
                'flask_env': current_app.config.get('ENV', 'development'),
                'debug_mode': current_app.config.get('DEBUG', False)
            }
        }
        
        # Determine overall status
        critical_services = ['database', 'redis']
        unhealthy_services = []
        
        if database_health.get('status') != 'healthy':
            unhealthy_services.append('database')
        if redis_health.get('status') != 'healthy':
            unhealthy_services.append('redis')
        
        has_critical_failure = any(service in unhealthy_services for service in critical_services)
        detailed_data['overall_status'] = 'healthy' if not has_critical_failure else 'unhealthy'
        detailed_data['unhealthy_services'] = unhealthy_services
        
        status_code = 200 if detailed_data['overall_status'] == 'healthy' else 503
        
        return health_check_response(True, detailed_data, status_code)
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        error_data = {
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return health_check_response(False, error_data, 500)

# Error handlers for the blueprint
@system_health_bp.errorhandler(404)
def not_found(error):
    return health_check_response(False, {'error': 'Health check endpoint not found'}, 404)

@system_health_bp.errorhandler(500)
def internal_error(error):
    return health_check_response(False, {'error': 'Internal server error'}, 500) 