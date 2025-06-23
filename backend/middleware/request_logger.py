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

class RequestLogger:
    """Request logging middleware"""
    
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        # Get request start time
        start_time = time.time()
        
        # Create Flask request context
        with self.app.request_context(environ):
            # Log request start
            logger.info(f"REQUEST START: {request.method} {request.path}")
            
            # Track API performance
            user_id = None
            if hasattr(g, 'user_id'):
                user_id = g.user_id
            
            with performance_monitor.api_timer(request.path, request.method, user_id):
                # Process request
                response = self.app(environ, start_response)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # Update performance metrics
                performance_monitor.update_metric('api_response_time', response_time, {
                    'endpoint': request.path,
                    'method': request.method,
                    'status_code': response[1] if len(response) > 1 else 200
                })
                
                # Check for performance alerts
                if response_time > 2.0:  # Alert if response time > 2 seconds
                    alerting_system.update_metric('api_response_time', response_time)
                
                # Log request end
                logger.info(f"REQUEST END: {request.method} {request.path} - Status: {response[1] if len(response) > 1 else 200} - Duration: {response_time:.3f}s")
                
                return response

# Legacy compatibility - keeping the old function names for any existing imports
def RequestLogger(app):
    """Legacy function for backward compatibility"""
    return RequestLogger(app)

def log_response(response):
    """Legacy function for backward compatibility"""
    return response 