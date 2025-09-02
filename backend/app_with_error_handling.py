"""
Updated Flask application with comprehensive error handling, logging, and monitoring.
This file demonstrates how to integrate all the error handling components.
"""

import os
import sys
import time
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, g, current_app
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

# Load environment variables
load_dotenv()

# Import our error handling and logging components
from errors.exceptions import (
    MingusBaseException, AuthenticationError, AuthorizationError,
    FinancialDataError, PaymentError, DatabaseError, APIError,
    BackgroundTaskError, SecurityError, ExternalServiceError,
    InvalidFinancialDataError, InsufficientFundsError, RateLimitExceededError
)
from errors.handlers import init_error_handlers, handle_validation_error, handle_rate_limit_exceeded
from logging.logger import init_logging, get_logger, log_financial_transaction, log_security_event, log_performance_metric
from monitoring.error_tracking import init_monitoring, get_monitoring, ErrorSeverity
from logging.formatters import get_formatter_for_environment

# Import existing components
try:
    from src.utils.cashflow_calculator import calculate_daily_cashflow
except ImportError:
    print("Warning: cashflow_calculator not available")

try:
    from models.articles import (
        Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
        ArticleRecommendation, ArticleAnalytics
    )
except ImportError:
    print("Warning: article models not available")


def create_app(config_name: str = None) -> Flask:
    """Application factory with comprehensive error handling and monitoring."""
    
    app = Flask(__name__)
    
    # Basic Flask configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')
    
    # Initialize logging system
    try:
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_dir = os.getenv('LOG_DIR', 'logs')
        enable_sentry = os.getenv('ENABLE_SENTRY', 'false').lower() == 'true'
        sentry_dsn = os.getenv('SENTRY_DSN')
        
        logging_system = init_logging(
            app_name="mingus",
            log_level=log_level,
            log_dir=log_dir,
            enable_sentry=enable_sentry,
            sentry_dsn=sentry_dsn
        )
        print("✅ Logging system initialized successfully")
        
    except Exception as e:
        print(f"⚠️  Logging system initialization failed: {e}")
        print("🔓 Continuing without advanced logging")
    
    # Initialize error handling
    try:
        error_handler = init_error_handlers(app)
        print("✅ Error handlers initialized successfully")
        
    except Exception as e:
        print(f"⚠️  Error handler initialization failed: {e}")
        print("🔓 Continuing without error handlers")
    
    # Initialize monitoring system
    try:
        monitoring = init_monitoring("mingus")
        print("✅ Monitoring system initialized successfully")
        
    except Exception as e:
        print(f"⚠️  Monitoring system initialization failed: {e}")
        print("🔓 Continuing without monitoring")
    
    # Initialize Flask extensions
    try:
        from extensions import init_extensions
        init_extensions(app)
        print("✅ Flask extensions initialized")
    except Exception as e:
        print(f"⚠️  Flask extensions initialization failed: {e}")
    
    # SSL Configuration - only import and initialize in production
    if app.config['FLASK_ENV'] == 'production':
        try:
            from middleware.ssl_middleware import init_ssl_middleware
            from config.ssl_config import SSLSecurity
            
            # Production SSL settings
            app.config['SESSION_COOKIE_SECURE'] = True
            app.config['SESSION_COOKIE_HTTPONLY'] = True
            app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
            app.config['SESSION_COOKIE_MAX_AGE'] = 1800  # 30 minutes for financial app
            
            # Initialize SSL middleware
            ssl_middleware = init_ssl_middleware(app)
            ssl_security = SSLSecurity(app)
            print("🔒 SSL Security middleware initialized for production")
        except Exception as e:
            print(f"⚠️  SSL middleware initialization failed: {e}")
            print("🔓 Continuing without SSL middleware")
    else:
        # Development settings
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['SESSION_COOKIE_MAX_AGE'] = 3600
        print("🔓 Development mode - SSL disabled")
    
    # Request context middleware
    @app.before_request
    def before_request():
        """Set up request context for logging and monitoring."""
        # Generate unique request ID
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = time.time()
        
        # Set user context if available
        try:
            # This would typically come from your authentication system
            g.user_id = request.headers.get('X-User-ID')
            g.session_id = request.headers.get('X-Session-ID')
        except Exception:
            g.user_id = None
            g.session_id = None
        
        # Log request start
        logger = get_logger('mingus.requests')
        logger.info("Request started", extra={
            'extra_fields': {
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'user_id': g.user_id,
                'session_id': g.session_id,
                'request_id': g.request_id
            }
        })
    
    @app.after_request
    def after_request(response):
        """Log request completion and record performance metrics."""
        # Calculate response time
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            
            # Record performance metric
            try:
                monitoring = get_monitoring()
                monitoring.record_performance_metric(
                    'response_time',
                    response_time,
                    'seconds',
                    tags={'method': request.method, 'endpoint': request.endpoint},
                    metadata={'status_code': response.status_code}
                )
            except Exception:
                pass  # Monitoring not available
            
            # Log request completion
            logger = get_logger('mingus.requests')
            logger.info("Request completed", extra={
                'extra_fields': {
                    'method': request.method,
                    'url': request.url,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'user_id': getattr(g, 'user_id', None),
                    'request_id': getattr(g, 'request_id', None)
                }
            })
        
        return response
    
    # Rate limiting decorator
    def rate_limit(limit_type: str, max_requests: int, window_seconds: int):
        """Rate limiting decorator for API endpoints."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    # Simple in-memory rate limiting (use Redis in production)
                    client_ip = request.remote_addr
                    key = f"rate_limit:{limit_type}:{client_ip}"
                    
                    # Check if rate limit exceeded
                    current_time = time.time()
                    window_start = current_time - window_seconds
                    
                    # This is a simplified implementation
                    # In production, use Redis or a proper rate limiting library
                    if hasattr(g, 'rate_limit_data'):
                        if key in g.rate_limit_data:
                            requests = g.rate_limit_data[key]
                            # Remove old requests
                            requests = [req_time for req_time in requests if req_time > window_start]
                            
                            if len(requests) >= max_requests:
                                retry_after = int(window_seconds - (current_time - requests[0]))
                                return handle_rate_limit_exceeded(limit_type, retry_after)
                            
                            requests.append(current_time)
                            g.rate_limit_data[key] = requests
                        else:
                            g.rate_limit_data[key] = [current_time]
                    else:
                        g.rate_limit_data = {key: [current_time]}
                    
                    return f(*args, **kwargs)
                    
                except Exception as e:
                    logger = get_logger('mingus.rate_limiting')
                    logger.error(f"Rate limiting error: {e}")
                    return f(*args, **kwargs)  # Continue without rate limiting on error
            
            return decorated_function
        return decorator
    
    # Routes with error handling and monitoring
    @app.route('/')
    def index():
        """Serve the main accessibility demo page."""
        try:
            return app.send_static_file('accessibility_demo.html')
        except Exception as e:
            logger = get_logger('mingus.routes')
            logger.error(f"Error serving index page: {e}")
            return jsonify({"error": "Failed to serve page"}), 500
    
    @app.route('/health')
    def health_check():
        """Comprehensive health check endpoint."""
        try:
            # Get monitoring health status
            monitoring = get_monitoring()
            health_status = monitoring.get_health_status()
            
            return jsonify(health_status), 200
            
        except Exception as e:
            logger = get_logger('mingus.health')
            logger.error(f"Health check failed: {e}")
            
            # Fallback health response
            return jsonify({
                "status": "unknown",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check failed"
            }), 500
    
    @app.route('/status')
    def status():
        """Detailed application status endpoint."""
        try:
            monitoring = get_monitoring()
            
            status_data = {
                "application": "Mingus Financial Application",
                "version": "1.0.0",
                "environment": app.config['FLASK_ENV'],
                "timestamp": datetime.utcnow().isoformat(),
                "health": monitoring.get_health_status(),
                "services": {
                    "database": "operational",  # Add actual health checks
                    "redis": "operational",
                    "celery": "operational"
                }
            }
            
            return jsonify(status_data), 200
            
        except Exception as e:
            logger = get_logger('mingus.status')
            logger.error(f"Status check failed: {e}")
            return jsonify({"error": "Status check failed"}), 500
    
    @app.route('/forecast', methods=['POST'])
    @rate_limit("forecast", 10, 60)  # 10 requests per minute
    def generate_forecast():
        """Generate cashflow forecast with comprehensive error handling."""
        start_time = time.time()
        
        try:
            # Validate request data
            data = request.get_json()
            if not data:
                raise InvalidFinancialDataError("No data provided")
            
            # Validate required fields
            required_fields = ['user_id', 'initial_balance']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise InvalidFinancialDataError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Extract and validate parameters
            user_id = data['user_id']
            initial_balance = data['initial_balance']
            start_date = data.get('start_date')
            
            # Validate initial balance
            try:
                initial_balance = float(initial_balance)
                if initial_balance < 0:
                    raise InvalidFinancialDataError("Initial balance cannot be negative")
            except (ValueError, TypeError):
                raise InvalidFinancialDataError("Initial balance must be a valid number")
            
            # Generate forecast
            forecast_results = calculate_daily_cashflow(
                user_id=user_id,
                initial_balance=initial_balance,
                start_date=start_date
            )
            
            # Log successful financial transaction
            try:
                log_financial_transaction(
                    transaction_type="forecast_generation",
                    amount=initial_balance,
                    user_id=user_id,
                    status="success"
                )
            except Exception:
                pass  # Logging not critical
            
            # Record performance metric
            try:
                monitoring = get_monitoring()
                response_time = time.time() - start_time
                monitoring.record_performance_metric(
                    'forecast_generation_time',
                    response_time,
                    'seconds',
                    tags={'user_id': user_id, 'initial_balance': str(initial_balance)}
                )
            except Exception:
                pass  # Monitoring not critical
            
            return jsonify({
                "status": "success",
                "data": forecast_results,
                "request_id": getattr(g, 'request_id', None)
            }), 200
            
        except InvalidFinancialDataError as e:
            # Log validation error
            try:
                logger = get_logger('mingus.financial')
                logger.warning(f"Financial data validation failed: {e.message}", extra={
                    'extra_fields': {
                        'user_id': data.get('user_id') if data else None,
                        'error_type': 'validation_error',
                        'missing_fields': missing_fields if 'missing_fields' in locals() else []
                    }
                })
            except Exception:
                pass
            
            # Record error in monitoring
            try:
                monitoring = get_monitoring()
                monitoring.record_error(
                    error_type="validation_error",
                    error_class="InvalidFinancialDataError",
                    error_message=str(e),
                    severity=ErrorSeverity.MEDIUM,
                    user_id=data.get('user_id') if data else None,
                    ip_address=request.remote_addr,
                    context={'endpoint': 'forecast', 'data': data}
                )
            except Exception:
                pass
            
            return jsonify(e.to_dict()), 400
            
        except Exception as e:
            # Log unexpected error
            try:
                logger = get_logger('mingus.financial')
                logger.error(f"Unexpected error in forecast generation: {e}", extra={
                    'extra_fields': {
                        'user_id': data.get('user_id') if data else None,
                        'error_type': 'unexpected_error',
                        'traceback': str(e)
                    }
                })
            except Exception:
                pass
            
            # Record error in monitoring
            try:
                monitoring = get_monitoring()
                monitoring.record_error(
                    error_type="unexpected_error",
                    error_class=e.__class__.__name__,
                    error_message=str(e),
                    severity=ErrorSeverity.HIGH,
                    user_id=data.get('user_id') if data else None,
                    ip_address=request.remote_addr,
                    context={'endpoint': 'forecast', 'data': data}
                )
            except Exception:
                pass
            
            return jsonify({
                "error": {
                    "type": "error",
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred while generating your forecast",
                    "error_id": str(uuid.uuid4())[:8],
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": getattr(g, 'request_id', None)
                }
            }), 500
    
    @app.route('/metrics')
    def metrics():
        """Application metrics endpoint for monitoring."""
        try:
            monitoring = get_monitoring()
            
            metrics_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "error_summary": monitoring.error_tracker.get_error_summary(3600),  # Last hour
                "performance_metrics": {
                    "response_time_avg": monitoring.performance_monitor.get_metric_average('response_time', 300),
                    "forecast_generation_avg": monitoring.performance_monitor.get_metric_average('forecast_generation_time', 300)
                },
                "system_metrics": monitoring.performance_monitor.get_system_metrics(),
                "active_alerts": len(monitoring.alert_manager.get_active_alerts())
            }
            
            return jsonify(metrics_data), 200
            
        except Exception as e:
            logger = get_logger('mingus.metrics')
            logger.error(f"Metrics endpoint failed: {e}")
            return jsonify({"error": "Failed to retrieve metrics"}), 500
    
    # Error handlers for specific error types
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle request entity too large errors."""
        return jsonify({
            "error": {
                "type": "error",
                "code": "REQUEST_TOO_LARGE",
                "message": "The request data is too large to process",
                "error_id": str(uuid.uuid4())[:8],
                "timestamp": datetime.utcnow().isoformat()
            }
        }), 413
    
    @app.errorhandler(415)
    def unsupported_media_type(error):
        """Handle unsupported media type errors."""
        return jsonify({
            "error": {
                "type": "error",
                "code": "UNSUPPORTED_MEDIA_TYPE",
                "message": "The request content type is not supported",
                "error_id": str(uuid.uuid4())[:8],
                "timestamp": datetime.utcnow().isoformat()
            }
        }), 415
    
    # Log application startup
    try:
        logger = get_logger('mingus.startup')
        logger.info("Mingus application started successfully", extra={
            'extra_fields': {
                'environment': app.config['FLASK_ENV'],
                'version': '1.0.0',
                'features': ['error_handling', 'logging', 'monitoring', 'rate_limiting']
            }
        })
    except Exception:
        pass
    
    return app


# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = app.config['FLASK_ENV'] == 'development'
    
    # Print environment check
    print("\nEnvironment variables:")
    print(f"FLASK_ENV: {app.config['FLASK_ENV']}")
    print(f"LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
    print(f"LOG_DIR: {os.getenv('LOG_DIR', 'logs')}")
    print(f"ENABLE_SENTRY: {os.getenv('ENABLE_SENTRY', 'false')}")
    print(f"PORT: {port}")
    print(f"DEBUG: {debug}")
    print()
    
    app.run(host='0.0.0.0', port=port, debug=debug)
