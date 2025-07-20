"""
Request logging for Flask application using built-in hooks
"""

import time
import logging
from flask import request, g
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_request_logging(app):
    """
    Set up request logging using Flask's built-in hooks
    instead of WSGI middleware to avoid request context issues
    """
    
    @app.before_request
    def log_request_start():
        """Log when request starts and store start time"""
        g.start_time = time.time()
        logger.info(f"REQUEST START: {request.method} {request.path}")
        
        # Log request headers if needed (optional)
        if app.debug:
            logger.debug(f"Headers: {dict(request.headers)}")
    
    @app.after_request
    def log_request_end(response):
        """Log when request ends with response info"""
        duration = time.time() - g.start_time if hasattr(g, 'start_time') else 0
        
        logger.info(
            f"REQUEST END: {request.method} {request.path} "
            f"- Status: {response.status_code} "
            f"- Duration: {duration:.3f}s"
        )
        
        return response
    
    @app.errorhandler(500)
    def log_server_error(error):
        """Log 500 errors with more detail"""
        duration = time.time() - g.start_time if hasattr(g, 'start_time') else 0
        
        logger.error(
            f"SERVER ERROR: {request.method} {request.path} "
            f"- Error: {str(error)} "
            f"- Duration: {duration:.3f}s"
        )
        
        return "Internal Server Error", 500

# Legacy compatibility - keeping the old function names for any existing imports
def RequestLogger(app):
    """Legacy function for backward compatibility"""
    setup_request_logging(app)
    return app

def log_response(response):
    """Legacy function for backward compatibility"""
    return response 