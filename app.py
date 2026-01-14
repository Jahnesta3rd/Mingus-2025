#!/usr/bin/env python3
"""
Mingus Personal Finance App - Main Application
Integrated Flask application with all API endpoints and security features
"""

import os
import sys
from flask import Flask, jsonify, request, g, render_template
from functools import wraps
import time
import threading
from datetime import datetime
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import API blueprints
from backend.api.auth_endpoints import auth_api
from backend.api.assessment_endpoints import assessment_api
from backend.api.meme_endpoints import meme_api
from backend.api.user_preferences_endpoints import user_preferences_api
from backend.api.profile_endpoints import profile_api
from backend.api.quick_setup_endpoints import quick_setup_api
from backend.api.resume_endpoints import resume_api
from backend.api.job_matching_endpoints import job_matching_api
from backend.api.three_tier_endpoints import three_tier_api
from backend.api.recommendation_engine_endpoints import recommendation_engine_api
from backend.api.referral_gated_endpoints import referral_gated_api
from backend.api.unified_risk_analytics_api import risk_analytics_api
from backend.api.vehicle_endpoints import vehicle_api
from backend.api.vehicle_management_api import vehicle_management_api
try:
    from backend.api.vehicle_setup_endpoints import vehicle_setup_api
except ImportError:
    vehicle_setup_api = None
    # Logger will be defined later, just skip for now
    pass
from backend.api.vehicle_expense_endpoints import vehicle_expense_api
from backend.api.enhanced_vehicle_expense_endpoints import enhanced_vehicle_api
from backend.api.weekly_checkin_endpoints import weekly_checkin_api
from backend.api.career_vehicle_optimization_api import career_vehicle_api
from backend.api.housing_endpoints import housing_api

# Import security middleware
from backend.middleware.security import SecurityMiddleware

# Import CORS logging middleware
from backend.middleware.cors_logging import setup_cors_logging

# Import SQLAlchemy models and database
from backend.models.database import init_database

# Import Redis session and cache configuration
from backend.config.session_config import init_redis_session
import redis
from backend.services.query_cache_manager import QueryCacheManager

# Import system monitoring
from backend.monitoring.system_monitor import SystemResourceMonitor

# Import error monitoring
from backend.monitoring.error_monitor import (
    get_error_monitor,
    ErrorSeverity,
    ErrorCategory
)

# Import dashboard API
from backend.api.dashboard_endpoints import dashboard_api, init_dashboard

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration from environment variables
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'your-secret-key-change-this'),
    CSRF_SECRET_KEY=os.environ.get('CSRF_SECRET_KEY', 'your-csrf-secret-key'),
    ENCRYPTION_KEY=os.environ.get('ENCRYPTION_KEY', 'your-encryption-key'),
    RATE_LIMIT_PER_MINUTE=int(os.environ.get('RATE_LIMIT_PER_MINUTE', '100')),
    DB_ENCRYPTION_ENABLED=os.environ.get('DB_ENCRYPTION_ENABLED', 'true').lower() == 'true',
    LOG_SENSITIVE_DATA=os.environ.get('LOG_SENSITIVE_DATA', 'false').lower() == 'true',
    # Performance optimizations
    MAX_CONTENT_LENGTH=int(os.environ.get('MAX_CONTENT_LENGTH', '16777216')),  # 16MB
    SEND_FILE_MAX_AGE_DEFAULT=int(os.environ.get('SEND_FILE_MAX_AGE_DEFAULT', '31536000')),  # 1 year
    PERMANENT_SESSION_LIFETIME=int(os.environ.get('PERMANENT_SESSION_LIFETIME', '86400')),  # 24 hours
    # Database connection pool settings
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '3600')),
        'pool_pre_ping': os.environ.get('DB_POOL_PRE_PING', 'true').lower() == 'true'
    }
)

# Configure CORS for all endpoints including new assessment endpoints
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000').split(',')
CORS_METHODS = os.environ.get('CORS_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',')
CORS_HEADERS = os.environ.get('CORS_HEADERS', 'Content-Type,Authorization,X-CSRF-Token,X-Requested-With').split(',')

# Determine if we're in development mode
is_development = os.environ.get('FLASK_ENV', 'development') == 'development'

# Configure CORS
# In development, be more permissive for testing and load testing
if is_development:
    # Development: Allow all origins for testing (including requests without Origin header)
    CORS(app, 
         resources={r"/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             "allow_headers": "*",  # Allow all headers in development
             "supports_credentials": False,
             "expose_headers": "*"
         }},
         send_wildcard=True,
         allow_headers="*")  # Explicitly allow all headers
else:
    # Production: Only allow configured origins
    CORS(app, 
         origins=CORS_ORIGINS,
         methods=CORS_METHODS,
         allow_headers=CORS_HEADERS,
         supports_credentials=True,
         expose_headers=['X-CSRF-Token'])

# Set up CORS failure logging
cors_logging_middleware = setup_cors_logging(app, allowed_origins=CORS_ORIGINS)
logger.info(f"CORS logging enabled - monitoring {len(CORS_ORIGINS)} allowed origins")

# Initialize Redis-based session storage
# This will automatically fall back to filesystem if Redis is unavailable
try:
    init_redis_session(app)
    logger.info("Redis session storage initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize Redis sessions (will continue without Redis): {e}")
    # Continue without Redis - app will use filesystem sessions

# Initialize Redis query cache manager
try:
    redis_cache_url = os.environ.get('REDIS_CACHE_URL', 'redis://localhost:6379/1')
    redis_password = os.environ.get('REDIS_PASSWORD')
    
    # Add password to URL if provided
    if redis_password and '@' not in redis_cache_url:
        if '://:' in redis_cache_url:
            redis_cache_url = redis_cache_url.replace('://:', f'://:{redis_password}@')
        elif 'redis://' in redis_cache_url:
            redis_cache_url = redis_cache_url.replace('redis://', f'redis://:{redis_password}@')
    
    redis_cache_client = redis.from_url(
        redis_cache_url,
        decode_responses=True,
        socket_timeout=2,  # Shorter timeout
        socket_connect_timeout=2,  # Shorter timeout
        retry_on_timeout=False,  # Don't retry on timeout
        health_check_interval=30
    )
    
    # Test connection with short timeout and error handling
    try:
        redis_cache_client.ping()
    except Exception as ping_error:
        raise ConnectionError(f"Redis ping failed: {ping_error}")
    
    # Initialize query cache manager
    app.query_cache_manager = QueryCacheManager(redis_cache_client, default_ttl=300)
    logger.info("Redis query cache manager initialized successfully")
except (redis.ConnectionError, redis.TimeoutError, OSError, ConnectionError, Exception) as e:
    logger.warning(f"Failed to initialize Redis query cache (will continue without caching): {e}")
    # Set to None so code can check if cache is available
    app.query_cache_manager = None
    # Continue without caching - app will work fine

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[f"{app.config['RATE_LIMIT_PER_MINUTE']} per minute"],
    storage_uri=os.environ.get('RATE_LIMIT_STORAGE_URL', 'memory://'),
    headers_enabled=True  # Enable rate limit headers (X-RateLimit-*)
)

# Register API blueprints
app.register_blueprint(auth_api)
app.register_blueprint(assessment_api)
app.register_blueprint(meme_api)
app.register_blueprint(user_preferences_api)
app.register_blueprint(profile_api)
app.register_blueprint(quick_setup_api)
app.register_blueprint(resume_api)
app.register_blueprint(job_matching_api)
app.register_blueprint(three_tier_api)
app.register_blueprint(recommendation_engine_api)
app.register_blueprint(referral_gated_api)
app.register_blueprint(risk_analytics_api)
app.register_blueprint(vehicle_api)
app.register_blueprint(vehicle_management_api)
if vehicle_setup_api:
    app.register_blueprint(vehicle_setup_api)
app.register_blueprint(vehicle_expense_api)
app.register_blueprint(enhanced_vehicle_api)
app.register_blueprint(weekly_checkin_api)
app.register_blueprint(career_vehicle_api)
app.register_blueprint(housing_api)

# Import and register gas price API
from backend.api.gas_price_endpoints import gas_price_api
app.register_blueprint(gas_price_api)

# Import and register Professional tier APIs
from backend.api.professional_tier_api import professional_tier_api
from backend.api.business_integrations_api import business_integrations_api
from backend.api.subscription_management_api import subscription_management_api
from backend.api.tax_adjacent_api import tax_adjacent_api
app.register_blueprint(professional_tier_api)
app.register_blueprint(business_integrations_api)
app.register_blueprint(subscription_management_api)
app.register_blueprint(tax_adjacent_api)

# Import and register External API for Optimal Living Location feature
from backend.api.external_api_endpoints import external_api
app.register_blueprint(external_api)

# Import and register Optimal Location API for housing features
from backend.api.optimal_location_api import optimal_location_api
app.register_blueprint(optimal_location_api)

# Initialize SQLAlchemy database
init_database(app)

# Initialize security middleware
# Note: Security middleware will skip public endpoints like /health and /api/status
# Register security middleware AFTER CORS to ensure security headers are set after CORS headers
security_middleware = SecurityMiddleware()
security_middleware.init_app(app)

# Initialize system resource monitoring
monitoring_interval = int(os.environ.get('MONITORING_INTERVAL', '10'))
enable_prometheus = os.environ.get('ENABLE_PROMETHEUS', 'false').lower() == 'true'
prometheus_port = int(os.environ.get('PROMETHEUS_PORT', '9090'))

system_monitor = SystemResourceMonitor(
    monitoring_interval=monitoring_interval,
    enable_prometheus=enable_prometheus,
    prometheus_port=prometheus_port,
    alert_thresholds={
        'cpu_percent': float(os.environ.get('ALERT_CPU_THRESHOLD', '80.0')),
        'memory_percent': float(os.environ.get('ALERT_MEMORY_THRESHOLD', '85.0')),
        'disk_percent': float(os.environ.get('ALERT_DISK_THRESHOLD', '90.0')),
        'error_rate': float(os.environ.get('ALERT_ERROR_RATE_THRESHOLD', '5.0')),
        'response_time_ms': float(os.environ.get('ALERT_RESPONSE_TIME_THRESHOLD', '1000.0')),
        'cache_hit_rate': float(os.environ.get('ALERT_CACHE_HIT_RATE_THRESHOLD', '0.70'))
    }
)
system_monitor.start()
logger.info("System resource monitoring initialized")

# Initialize error monitoring
error_monitor = get_error_monitor()
logger.info("Error monitoring initialized")

# Initialize dashboard API
init_dashboard(system_monitor, error_monitor)
app.register_blueprint(dashboard_api)
logger.info("Dashboard API initialized")

# Set up cache metrics integration (if cache manager is available)
if hasattr(app, 'query_cache_manager') and app.query_cache_manager:
    def update_cache_metrics():
        """Update cache metrics in system monitor"""
        try:
            stats = app.query_cache_manager.get_stats()
            system_monitor.update_cache_metrics(
                hits=stats.get('hits', 0),
                misses=stats.get('misses', 0)
            )
        except Exception as e:
            logger.debug(f"Error updating cache metrics: {e}")
    
    # Schedule cache metrics update (every 30 seconds)
    def cache_metrics_loop():
        while True:
            try:
                update_cache_metrics()
                time.sleep(30)
            except Exception as e:
                logger.debug(f"Error in cache metrics loop: {e}")
                time.sleep(30)
    
    cache_metrics_thread = threading.Thread(target=cache_metrics_loop, daemon=True)
    cache_metrics_thread.start()
    logger.info("Cache metrics integration enabled")

# Request tracking middleware
@app.before_request
def track_request_start():
    """Track request start time"""
    g.request_start_time = time.time()

@app.after_request
def track_request_end(response):
    """Track request metrics and log errors"""
    if hasattr(g, 'request_start_time'):
        duration = time.time() - g.request_start_time
        system_monitor.track_request(
            method=request.method,
            endpoint=request.endpoint or request.path,
            status_code=response.status_code,
            duration=duration
        )
        
        # Log errors (4xx and 5xx)
        if response.status_code >= 400:
            try:
                error_data = response.get_json() if response.is_json else {}
                error_message = error_data.get('error', f'HTTP {response.status_code}')
                
                # Determine category based on status code
                if response.status_code == 401:
                    category = ErrorCategory.AUTHENTICATION
                elif response.status_code == 403:
                    category = ErrorCategory.AUTHORIZATION
                elif response.status_code == 404:
                    category = ErrorCategory.UNKNOWN  # Don't log 404s as errors
                    return response
                elif response.status_code == 422:
                    category = ErrorCategory.VALIDATION
                elif response.status_code >= 500:
                    category = ErrorCategory.SYSTEM
                else:
                    category = ErrorCategory.UNKNOWN
                
                # Determine severity
                if response.status_code >= 500:
                    severity = ErrorSeverity.HIGH
                elif response.status_code >= 400:
                    severity = ErrorSeverity.MEDIUM
                else:
                    severity = ErrorSeverity.LOW
                
                # Create a simple exception for logging
                class HTTPError(Exception):
                    pass
                
                http_error = HTTPError(error_message)
                http_error.status_code = response.status_code
                
                error_monitor.log_error(
                    error=http_error,
                    severity=severity,
                    category=category,
                    endpoint=request.endpoint or request.path,
                    request_method=request.method,
                    request_path=request.path,
                    request_ip=request.remote_addr,
                    request_user_agent=request.headers.get('User-Agent'),
                    context={'status_code': response.status_code, 'response_data': error_data}
                )
            except Exception as e:
                logger.debug(f"Error logging HTTP error: {e}")
    
    return response

# CORS logging is already initialized above with setup_cors_logging()

# Health check endpoint (bypasses all middleware)
# Note: This endpoint must be exempt from rate limiting
@app.route('/health', methods=['GET', 'OPTIONS'])
@limiter.exempt  # Exempt from rate limiting
def health_check():
    """Health check endpoint for monitoring - public endpoint, no auth required"""
    # Handle OPTIONS for CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', '*')
        return response
    
    # Get system health from monitor
    health_status = system_monitor.get_health_status()
    
    return jsonify({
        'status': health_status.get('status', 'healthy'),
        'timestamp': os.environ.get('TIMESTAMP', 'unknown'),
        'version': '1.0.0',
        'services': {
            'database': 'connected',
            'sqlalchemy_models': 'active',
            'redis_sessions': 'active' if app.config.get('SESSION_TYPE') == 'redis' else 'inactive',
            'query_cache': 'active' if hasattr(app, 'query_cache_manager') and app.query_cache_manager else 'inactive',
            'vehicle_management': 'active',
            'vehicle_management_api': 'active',
            'assessment_api': 'active',
            'meme_api': 'active',
            'user_preferences_api': 'active',
            'job_matching_api': 'active',
            'three_tier_api': 'active',
            'recommendation_engine_api': 'active',
            'risk_analytics_api': 'active',
            'monitoring': 'active'
        },
        'monitoring': health_status
    })

# API status endpoint (public endpoint)
@app.route('/api/status', methods=['GET', 'OPTIONS'])
def api_status():
    """API status endpoint - public endpoint, no auth required"""
    # Handle OPTIONS for CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', '*')
        return response
    
    return jsonify({
        'status': 'operational',
        'endpoints': {
            'assessments': {
                'submit': '/api/assessments',
                'results': '/api/assessments/<id>/results',
                'analytics': '/api/assessments/analytics'
            },
            'memes': {
                'get_meme': '/api/user-meme',
                'analytics': '/api/meme-analytics',
                'stats': '/api/meme-stats'
            },
            'user_preferences': {
                'get': '/api/user-preferences',
                'update': '/api/user-preferences'
            },
            'job_matching': {
                'search': '/api/job-matching/search',
                'msa_targeting': '/api/job-matching/msa-targeting',
                'remote_detection': '/api/job-matching/remote-detection'
            },
            'three_tier_recommendations': {
                'recommendations': '/api/three-tier/recommendations',
                'tier_specific': '/api/three-tier/tier/{tier_name}',
                'job_analysis': '/api/three-tier/job/{job_id}/analysis',
                'tiers_summary': '/api/three-tier/tiers/summary',
                'skills_gap': '/api/three-tier/skills/gap-analysis'
            },
            'recommendation_engine': {
                'process_resume': '/api/recommendations/process-resume',
                'status': '/api/recommendations/status/{session_id}',
                'analytics': '/api/recommendations/analytics',
                'performance': '/api/recommendations/performance',
                'health': '/api/recommendations/health',
                'cache_clear': '/api/recommendations/cache/clear',
                'session_results': '/api/recommendations/sessions/{session_id}/results'
            },
            'referral_gated': {
                'career_preview': '/career-preview',
                'refer_friend': '/refer-friend',
                'referral_status': '/referral-status/{referral_code}',
                'career_advancement': '/career-advancement',
                'feature_access': '/api/feature-access/job-recommendations',
                'upload_resume': '/upload-resume',
                'location_preferences': '/set-location-preferences',
                'process_recommendations': '/process-recommendations',
                'referral_progress': '/referral-progress',
                'validate_zipcode': '/validate-zipcode',
                'location_recommendations': '/location-recommendations'
            },
            'risk_analytics': {
                'assess_and_track': '/api/risk/assess-and-track',
                'dashboard': '/api/risk/dashboard/{user_id}',
                'trigger_recommendations': '/api/risk/trigger-recommendations',
                'effectiveness': '/api/risk/analytics/effectiveness',
                'track_outcome': '/api/risk/outcome/track',
                'monitor_status': '/api/risk/monitor/status',
                'trigger_alert': '/api/risk/alert/trigger',
                'live_trends': '/api/risk/trends/live',
                'active_predictions': '/api/risk/predictions/active',
                'active_experiments': '/api/risk/experiments/active',
                'assign_experiment': '/api/risk/experiments/assign',
                'track_experiment_outcome': '/api/risk/experiments/outcome',
                'admin_analytics': '/api/risk/analytics/admin/comprehensive',
                'health': '/api/risk/health'
            },
            'vehicle_management': {
                'create_vehicle': '/api/vehicle',
                'get_vehicles': '/api/vehicle',
                'get_vehicle': '/api/vehicle/{id}',
                'update_vehicle': '/api/vehicle/{id}',
                'delete_vehicle': '/api/vehicle/{id}',
                'maintenance_predictions': '/api/vehicle/{id}/maintenance-predictions',
                'commute_analysis': '/api/vehicle/{id}/commute-analysis',
                'forecast_impact': '/api/vehicle/{id}/forecast-impact',
                'vin_lookup': '/api/vehicle/vin-lookup',
                'health': '/api/vehicle/health'
            },
            'weekly_checkin': {
                'submit': '/api/weekly-checkin',
                'latest': '/api/weekly-checkin/latest',
                'history': '/api/weekly-checkin/history',
                'analytics': '/api/weekly-checkin/analytics'
            },
            'career_vehicle_optimization': {
                'job_cost_analysis': '/api/career-vehicle/job-cost-analysis',
                'commute_impact_analysis': '/api/career-vehicle/commute-impact-analysis',
                'career_move_planning': '/api/career-vehicle/career-move-planning',
                'budget_optimization': '/api/career-vehicle/budget-optimization',
                'feature_access': '/api/career-vehicle/feature-access'
            },
        'professional_tier': {
            'fleet_management': '/api/professional/fleet',
            'mileage_tracking': '/api/professional/mileage',
            'fleet_analytics': '/api/professional/analytics/fleet',
            'roi_analysis': '/api/professional/roi-analysis',
            'health': '/api/professional/health'
        },
        'tax_adjacent': {
            'expense_tracking': '/api/professional/expenses',
            'mileage_logging': '/api/professional/mileage',
            'maintenance_records': '/api/professional/maintenance',
            'educational_content': '/api/professional/education',
            'expense_reports': '/api/professional/reports/expense',
            'health': '/api/professional/tax-adjacent/health'
        },
            'business_integrations': {
                'quickbooks_connect': '/api/professional/integrations/quickbooks/connect',
                'quickbooks_sync': '/api/professional/integrations/quickbooks/sync',
                'credit_card_connect': '/api/professional/integrations/credit-card/connect',
                'credit_card_categorize': '/api/professional/integrations/credit-card/categorize',
                'hr_connect': '/api/professional/integrations/hr/connect',
                'hr_employee_vehicles': '/api/professional/integrations/hr/employee-vehicles',
                'insurance_connect': '/api/professional/integrations/insurance/connect',
                'insurance_policies': '/api/professional/integrations/insurance/policies',
                'integration_status': '/api/professional/integrations/status',
                'health': '/api/professional/integrations/health'
            },
            'subscription_management': {
                'plans': '/api/subscription/plans',
                'current': '/api/subscription/current',
                'upgrade': '/api/subscription/upgrade',
                'cancel': '/api/subscription/cancel',
                'feature_access': '/api/subscription/feature-access',
                'usage': '/api/subscription/usage',
                'billing_history': '/api/subscription/billing-history',
                'health': '/api/subscription/health'
            },
            'external_apis': {
                'rental_listings': '/api/external/rentals/{zip_code}',
                'home_listings': '/api/external/homes/{zip_code}',
                'route_distance': '/api/external/route/distance',
                'cached_route': '/api/external/route/cached',
                'service_status': '/api/external/status',
                'cache_clear': '/api/external/cache/clear',
                'cache_stats': '/api/external/cache/stats'
            }
        },
        'security': {
            'csrf_protection': 'enabled',
            'rate_limiting': 'enabled',
            'input_validation': 'enabled',
            'data_encryption': app.config['DB_ENCRYPTION_ENABLED']
        },
        'performance': {
            'redis_sessions': 'enabled' if app.config.get('SESSION_TYPE') == 'redis' else 'disabled',
            'query_caching': 'enabled' if hasattr(app, 'query_cache_manager') and app.query_cache_manager else 'disabled',
            'cache_stats': app.query_cache_manager.get_stats() if hasattr(app, 'query_cache_manager') and app.query_cache_manager else None
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found',
        'status_code': 404
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit exceeded errors"""
    # Get retry-after from error if available, default to 60 seconds
    retry_after = getattr(error, 'retry_after', 60)
    
    response = jsonify({
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please try again later.',
        'status_code': 429,
        'retry_after': retry_after
    })
    
    # Add Retry-After header
    response.headers['Retry-After'] = str(retry_after)
    
    return response, 429

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    # Log to error monitor
    try:
        error_monitor.log_error(
            error=error,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            endpoint=request.endpoint or request.path if request else None,
            request_method=request.method if request else None,
            request_path=request.path if request else None,
            request_ip=request.remote_addr if request else None,
            request_user_agent=request.headers.get('User-Agent') if request else None
        )
    except Exception as e:
        logger.error(f"Error logging to error monitor: {e}")
    
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    # Log to error monitor
    try:
        category = error_monitor.categorize_error(e)
        severity = error_monitor.determine_severity(e, category)
        
        error_monitor.log_error(
            error=e,
            severity=severity,
            category=category,
            endpoint=request.endpoint or request.path if request else None,
            request_method=request.method if request else None,
            request_path=request.path if request else None,
            request_ip=request.remote_addr if request else None,
            request_user_agent=request.headers.get('User-Agent') if request else None
        )
    except Exception as log_error:
        logger.error(f"Error logging exception: {log_error}")
    
    # Return appropriate response
    if hasattr(e, 'code') and e.code == 404:
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    # For other exceptions, return 500
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred',
        'status_code': 500
    }), 500

# Application startup
def initialize_app():
    """Initialize application on first request"""
    logger.info("Initializing Mingus Personal Finance App...")
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('database_backups', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    
    # Initialize assessment database
    try:
        from backend.api.assessment_endpoints import init_assessment_db
        init_assessment_db()
        logger.info("Assessment database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize assessment database: {e}")
    
    logger.info("Application initialization complete")

# Metrics endpoints
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get detailed system and application metrics"""
    return jsonify(system_monitor.get_metrics())

@app.route('/api/metrics/health', methods=['GET'])
def get_health_metrics():
    """Get system health status"""
    return jsonify(system_monitor.get_health_status())

@app.route('/api/metrics/recommendations', methods=['GET'])
def get_recommendations():
    """Get performance recommendations"""
    return jsonify({
        'recommendations': system_monitor.get_recommendations(),
        'timestamp': time.time()
    })

# Dashboard route
@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Monitoring dashboard page"""
    return render_template('monitoring_dashboard.html')

# Error monitoring endpoints
@app.route('/api/errors/stats', methods=['GET'])
def get_error_stats():
    """Get error statistics"""
    hours = int(request.args.get('hours', 24))
    return jsonify(error_monitor.get_error_stats(hours=hours))

@app.route('/api/errors', methods=['GET'])
def get_errors():
    """Get error list with optional filtering"""
    severity = request.args.get('severity')
    category = request.args.get('category')
    limit = int(request.args.get('limit', 100))
    
    errors = error_monitor.get_errors(
        severity=severity,
        category=category,
        limit=limit
    )
    
    return jsonify({
        'errors': errors,
        'count': len(errors),
        'filters': {
            'severity': severity,
            'category': category,
            'limit': limit
        }
    })

@app.route('/api/errors/health', methods=['GET'])
def get_error_health():
    """Get error monitoring health status"""
    stats = error_monitor.get_error_stats(hours=1)
    
    # Determine health status
    critical_count = stats['by_severity'].get('critical', 0)
    high_count = stats['by_severity'].get('high', 0)
    total_count = stats['total']
    
    if critical_count > 0:
        status = 'critical'
    elif high_count > 10:
        status = 'degraded'
    elif total_count > 50:
        status = 'warning'
    else:
        status = 'healthy'
    
    return jsonify({
        'status': status,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Initialize application
    initialize_app()
    
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    # Use 5001 if 5000 is occupied (common on macOS due to AirPlay)
    default_port = 5001 if os.path.exists('/System/Library/CoreServices/AirPlayXPCHelper') else 5000
    port = int(os.environ.get('FLASK_PORT', str(default_port)))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting Mingus Personal Finance App on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"CORS origins: {CORS_ORIGINS}")
    logger.info(f"Rate limit: {app.config['RATE_LIMIT_PER_MINUTE']} per minute")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
