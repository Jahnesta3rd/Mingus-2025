"""
Request logging middleware
"""

import time
import json
from datetime import datetime
from flask import request, g
from loguru import logger
from backend.monitoring.performance_monitoring import performance_monitor
from backend.monitoring.alerting import alerting_system

class RequestLoggerMiddleware:
    """Request logging middleware"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # Get request start time
        start_time = time.time()
        
        # Get request info from environ (safe way)
        method = environ.get('REQUEST_METHOD', 'UNKNOWN')
        path = environ.get('PATH_INFO', '/')
        
        # Log request start
        logger.info(f"REQUEST START: {method} {path}")
        
        # Process request
        response = self.app(environ, start_response)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Get status code from response
        status_code = 200
        if isinstance(response, (list, tuple)) and len(response) > 1:
            status_code = response[1]
        
        # Update performance metrics (only if monitoring is available)
        try:
            with performance_monitor.api_timer(path, method):
                # Track API performance
                user_id = None
                if hasattr(g, 'user_id'):
                    user_id = g.user_id
                
                performance_monitor.update_metric('api_response_time', response_time, {
                    'endpoint': path,
                    'method': method,
                    'status_code': status_code
                })
                
                # Check for performance alerts
                if response_time > 2.0:  # Alert if response time > 2 seconds
                    alerting_system.update_metric('api_response_time', response_time)
        except Exception as e:
            logger.warning(f"Performance monitoring error: {str(e)}")
        
        # Log request end
        logger.info(f"REQUEST END: {method} {path} - Status: {status_code} - Duration: {response_time:.3f}s")
        
        return response

def setup_request_logging(app):
    """Setup request logging middleware for Flask app"""
    try:
        # Wrap the app with request logging middleware
        app.wsgi_app = RequestLoggerMiddleware(app.wsgi_app)
        logger.info("Request logging middleware setup successfully")
    except Exception as e:
        logger.error(f"Failed to setup request logging: {str(e)}")

def log_response(response):
    """Legacy function for backward compatibility"""
    return response 