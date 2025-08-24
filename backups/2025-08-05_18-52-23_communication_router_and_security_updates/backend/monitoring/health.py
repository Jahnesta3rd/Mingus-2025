"""
Health Monitoring Module
Provides health check routes and monitoring functionality for the Flask application
"""

from flask import Flask, jsonify, current_app
from datetime import datetime
import time
import os
import requests
from typing import Dict, Any, Optional
from loguru import logger

def create_health_routes(app: Flask) -> None:
    """Create health check routes for the Flask application"""
    
    @app.route('/health')
    def health_check():
        """Basic application health endpoint for load balancers and monitoring"""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'mingus-api',
            'version': getattr(current_app, 'version', '1.0.0')
        }
    
    @app.route('/health/detailed')
    def detailed_health():
        """Detailed health endpoint with comprehensive system checks"""
        start_time = time.time()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'mingus-api',
            'version': getattr(current_app, 'version', '1.0.0'),
            'response_time_ms': 0,
            'checks': {}
        }
        
        # Database health check
        db_status = check_database_health()
        health_data['checks']['database'] = db_status
        
        # Redis health check
        redis_status = check_redis_health()
        health_data['checks']['redis'] = redis_status
        
        # External services health check
        external_status = check_external_services_health()
        health_data['checks']['external_services'] = external_status
        
        # System resources health check
        system_status = check_system_resources()
        health_data['checks']['system'] = system_status
        
        # Calculate response time
        health_data['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Determine overall status
        all_checks = [db_status['status'], redis_status['status'], 
                     external_status['status'], system_status['status']]
        
        if all(status == 'healthy' for status in all_checks):
            health_data['status'] = 'healthy'
            return health_data, 200
        elif any(status == 'unhealthy' for status in all_checks):
            health_data['status'] = 'unhealthy'
            return health_data, 503
        else:
            health_data['status'] = 'degraded'
            return health_data, 200
    
    @app.route('/health/readiness')
    def readiness_check():
        """Readiness probe for Kubernetes and container orchestration"""
        checks = {
            'database': check_database_health(),
            'redis': check_redis_health()
        }
        
        ready = all(check['status'] == 'healthy' for check in checks.values())
        
        return {
            'ready': ready,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }, 200 if ready else 503
    
    @app.route('/health/liveness')
    def liveness_check():
        """Liveness probe for Kubernetes and container orchestration"""
        return {
            'alive': True,
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': get_uptime_seconds()
        }
    
    @app.route('/health/startup')
    def startup_check():
        """Startup probe for Kubernetes and container orchestration"""
        checks = {
            'database': check_database_health(),
            'redis': check_redis_health(),
            'system': check_system_resources()
        }
        
        startup_complete = all(check['status'] == 'healthy' for check in checks.values())
        
        return {
            'startup_complete': startup_complete,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': checks
        }, 200 if startup_complete else 503

def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and health"""
    try:
        from sqlalchemy import text
        from sqlalchemy.exc import SQLAlchemyError
        
        db = current_app.extensions.get('sqlalchemy')
        if not db:
            return {
                'status': 'unhealthy',
                'error': 'Database extension not found',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        # Test basic connectivity
        result = db.session.execute(text("SELECT 1 as test"))
        result.fetchone()
        
        # Test more complex query
        result = db.session.execute(text("SELECT COUNT(*) as table_count FROM information_schema.tables"))
        table_count = result.fetchone()[0]
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            'status': 'healthy',
            'response_time_ms': response_time,
            'table_count': table_count,
            'error': None
        }
        
    except SQLAlchemyError as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': f'Unexpected error: {str(e)}',
            'response_time_ms': None
        }

def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity and health"""
    try:
        import redis
        
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        
        start_time = time.time()
        
        redis_client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            socket_connect_timeout=2,
            socket_timeout=2
        )
        
        # Test basic connectivity
        redis_client.ping()
        
        # Test basic operations
        test_key = f"health_check_{int(time.time())}"
        redis_client.set(test_key, "test_value", ex=60)
        value = redis_client.get(test_key)
        redis_client.delete(test_key)
        
        if value != b"test_value":
            raise Exception("Redis read/write test failed")
        
        # Get Redis info
        info = redis_client.info()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            'status': 'healthy',
            'response_time_ms': response_time,
            'memory_usage_bytes': info.get('used_memory', 0),
            'connected_clients': info.get('connected_clients', 0),
            'error': None
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_external_services_health() -> Dict[str, Any]:
    """Check external services health"""
    services = {}
    
    # Check Supabase
    supabase_status = check_supabase_health()
    services['supabase'] = supabase_status
    
    # Check Stripe
    stripe_status = check_stripe_health()
    services['stripe'] = stripe_status
    
    # Check Twilio
    twilio_status = check_twilio_health()
    services['twilio'] = twilio_status
    
    # Check Resend
    resend_status = check_resend_health()
    services['resend'] = resend_status
    
    # Determine overall status
    healthy_services = sum(1 for s in services.values() if s['status'] == 'healthy')
    total_services = len(services)
    
    if healthy_services == total_services:
        overall_status = 'healthy'
    elif healthy_services == 0:
        overall_status = 'unhealthy'
    else:
        overall_status = 'degraded'
    
    return {
        'status': overall_status,
        'services': services,
        'summary': {
            'healthy_services': healthy_services,
            'total_services': total_services
        }
    }

def check_supabase_health() -> Dict[str, Any]:
    """Check Supabase connectivity"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            return {
                'status': 'not_configured',
                'error': 'Supabase credentials not configured',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}'
        }
        
        response = requests.get(
            f"{supabase_url}/rest/v1/",
            headers=headers,
            timeout=5
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code in [200, 401]:
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'error': None
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_stripe_health() -> Dict[str, Any]:
    """Check Stripe connectivity"""
    try:
        stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
        
        if not stripe_secret_key:
            return {
                'status': 'not_configured',
                'error': 'Stripe credentials not configured',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        headers = {
            'Authorization': f'Bearer {stripe_secret_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.get(
            'https://api.stripe.com/v1/account',
            headers=headers,
            timeout=5
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'error': None
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_twilio_health() -> Dict[str, Any]:
    """Check Twilio connectivity"""
    try:
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not twilio_account_sid or not twilio_auth_token:
            return {
                'status': 'not_configured',
                'error': 'Twilio credentials not configured',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        import base64
        auth_string = f"{twilio_account_sid}:{twilio_auth_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.get(
            f'https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}.json',
            headers=headers,
            timeout=5
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'error': None
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_resend_health() -> Dict[str, Any]:
    """Check Resend connectivity"""
    try:
        resend_api_key = os.getenv('RESEND_API_KEY')
        
        if not resend_api_key:
            return {
                'status': 'not_configured',
                'error': 'Resend credentials not configured',
                'response_time_ms': None
            }
        
        start_time = time.time()
        
        headers = {
            'Authorization': f'Bearer {resend_api_key}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            'https://api.resend.com/domains',
            headers=headers,
            timeout=5
        )
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        if response.status_code in [200, 401]:
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'error': None
            }
        else:
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time,
                'error': f'HTTP {response.status_code}'
            }
            
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_ms': None
        }

def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage"""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Process info
        process = psutil.Process()
        
        return {
            'status': 'healthy',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_percent': round((disk.used / disk.total) * 100, 2),
            'disk_available_gb': round(disk.free / (1024**3), 2),
            'process_memory_mb': round(process.memory_info().rss / (1024**2), 2),
            'process_threads': process.num_threads(),
            'error': None
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

def get_uptime_seconds() -> float:
    """Get application uptime in seconds"""
    try:
        import psutil
        process = psutil.Process()
        return time.time() - process.create_time()
    except:
        return 0.0 