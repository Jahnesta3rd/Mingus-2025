#!/usr/bin/env python3
"""
CORS Failure Logging Middleware

Logs CORS-related requests, failures, and security events for monitoring and debugging.
"""

import os
import logging
import logging.handlers
from datetime import datetime
from flask import request, g
from typing import Optional, Dict, Any
import json

# Create dedicated CORS logger
cors_logger = logging.getLogger('mingus.cors')
cors_logger.setLevel(logging.INFO)

# Prevent duplicate handlers
if not cors_logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # CORS-specific log file
    cors_log_file = os.path.join(log_dir, 'cors.log')
    
    # File handler with rotation (10MB, 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        cors_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    
    # Detailed formatter for CORS logs
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    cors_logger.addHandler(file_handler)
    
    # Console handler for important CORS events
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
    console_formatter = logging.Formatter(
        '%(asctime)s - [CORS] %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    cors_logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    cors_logger.propagate = False


class CORSLoggingMiddleware:
    """Middleware to log CORS-related requests and failures"""
    
    def __init__(self, app=None, allowed_origins: Optional[list] = None):
        """
        Initialize CORS logging middleware
        
        Args:
            app: Flask application instance
            allowed_origins: List of allowed CORS origins
        """
        self.allowed_origins = allowed_origins or []
        self.app = app
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        # Store allowed origins from app config
        cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
        self.allowed_origins = [origin.strip() for origin in cors_origins if origin.strip()]
        
        # Register before_request and after_request hooks
        app.before_request(self._log_cors_request)
        app.after_request(self._log_cors_response)
        
        cors_logger.info(f"CORS logging middleware initialized with {len(self.allowed_origins)} allowed origins")
    
    def _log_cors_request(self):
        """Log CORS-related request information"""
        origin = request.headers.get('Origin')
        method = request.method
        path = request.path
        
        # Store CORS info in Flask g for use in after_request
        g.cors_info = {
            'origin': origin,
            'method': method,
            'path': path,
            'request_headers': dict(request.headers),
            'timestamp': datetime.utcnow().isoformat(),
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Log preflight requests (OPTIONS)
        if method == 'OPTIONS' and origin:
            requested_method = request.headers.get('Access-Control-Request-Method', 'N/A')
            requested_headers = request.headers.get('Access-Control-Request-Headers', 'N/A')
            
            cors_logger.info(
                f"CORS Preflight Request - Origin: {origin}, "
                f"Path: {path}, Method: {requested_method}, "
                f"Headers: {requested_headers}, IP: {request.remote_addr}"
            )
    
    def _log_cors_response(self, response):
        """Log CORS-related response information"""
        if not hasattr(g, 'cors_info'):
            return response
        
        origin = g.cors_info.get('origin')
        method = g.cors_info.get('method')
        path = g.cors_info.get('path')
        
        # Get CORS headers from response
        acao = response.headers.get('Access-Control-Allow-Origin')
        acac = response.headers.get('Access-Control-Allow-Credentials')
        acam = response.headers.get('Access-Control-Allow-Methods')
        acah = response.headers.get('Access-Control-Allow-Headers')
        aceh = response.headers.get('Access-Control-Expose-Headers')
        
        # Determine if CORS request was allowed or blocked
        is_allowed = origin in self.allowed_origins if origin else None
        is_blocked = origin is not None and origin not in self.allowed_origins
        
        # Build log entry
        log_data = {
            'timestamp': g.cors_info.get('timestamp'),
            'origin': origin,
            'method': method,
            'path': path,
            'status_code': response.status_code,
            'remote_addr': g.cors_info.get('remote_addr'),
            'user_agent': g.cors_info.get('user_agent'),
            'cors_headers': {
                'Access-Control-Allow-Origin': acao,
                'Access-Control-Allow-Credentials': acac,
                'Access-Control-Allow-Methods': acam,
                'Access-Control-Allow-Headers': acah,
                'Access-Control-Expose-Headers': aceh
            },
            'allowed_origin': is_allowed,
            'blocked': is_blocked
        }
        
        # Log based on CORS status
        if is_blocked:
            # Unauthorized origin - SECURITY EVENT
            cors_logger.warning(
                f"CORS BLOCKED - Unauthorized origin: {origin}, "
                f"Path: {path}, Method: {method}, "
                f"IP: {g.cors_info.get('remote_addr')}, "
                f"Status: {response.status_code}"
            )
            cors_logger.debug(f"CORS Block Details: {json.dumps(log_data, indent=2)}")
            
        elif origin and method == 'OPTIONS':
            # Preflight request
            if acao:
                cors_logger.info(
                    f"CORS Preflight ALLOWED - Origin: {origin}, "
                    f"Path: {path}, Status: {response.status_code}"
                )
            else:
                cors_logger.warning(
                    f"CORS Preflight MISSING HEADERS - Origin: {origin}, "
                    f"Path: {path}, Status: {response.status_code}"
                )
                cors_logger.debug(f"CORS Preflight Details: {json.dumps(log_data, indent=2)}")
                
        elif origin and acao:
            # Actual CORS request with origin
            if acao == origin:
                cors_logger.debug(
                    f"CORS Request ALLOWED - Origin: {origin}, "
                    f"Path: {path}, Method: {method}, Status: {response.status_code}"
                )
            elif acao == '*':
                cors_logger.warning(
                    f"CORS Request with WILDCARD - Origin: {origin}, "
                    f"Path: {path}, Method: {method}, "
                    f"Warning: Using wildcard with credentials may be insecure"
                )
            else:
                cors_logger.warning(
                    f"CORS Request ORIGIN MISMATCH - Requested: {origin}, "
                    f"Allowed: {acao}, Path: {path}, Method: {method}"
                )
                cors_logger.debug(f"CORS Mismatch Details: {json.dumps(log_data, indent=2)}")
        
        # Log missing CORS headers for cross-origin requests
        if origin and origin not in self.allowed_origins:
            if not acao:
                cors_logger.error(
                    f"CORS ERROR - Missing Access-Control-Allow-Origin header "
                    f"for origin: {origin}, Path: {path}, Method: {method}"
                )
        
        return response
    
    @staticmethod
    def log_cors_failure(origin: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Static method to log CORS failures from anywhere in the application
        
        Args:
            origin: The origin that was blocked
            reason: Reason for the failure
            details: Additional details about the failure
        """
        log_message = f"CORS FAILURE - Origin: {origin}, Reason: {reason}"
        
        if details:
            log_message += f", Details: {json.dumps(details, indent=2)}"
        
        cors_logger.error(log_message)
    
    @staticmethod
    def log_cors_success(origin: str, path: str, method: str):
        """
        Static method to log successful CORS requests
        
        Args:
            origin: The origin that was allowed
            path: Request path
            method: HTTP method
        """
        cors_logger.debug(f"CORS SUCCESS - Origin: {origin}, Path: {path}, Method: {method}")


def setup_cors_logging(app, allowed_origins: Optional[list] = None):
    """
    Convenience function to set up CORS logging for a Flask app
    
    Args:
        app: Flask application instance
        allowed_origins: List of allowed CORS origins (optional)
    
    Returns:
        CORSLoggingMiddleware instance
    """
    middleware = CORSLoggingMiddleware(app, allowed_origins)
    return middleware
