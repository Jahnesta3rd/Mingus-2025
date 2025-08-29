"""
Security Integration Middleware
Comprehensive security middleware combining rate limiting and API validation
"""

import logging
import time
from functools import wraps
from typing import Dict, Any, Optional, List
from flask import request, jsonify, g, current_app

from .rate_limiter import rate_limited, get_rate_limiter, add_rate_limit_headers
from .api_validation import validate_api_request, get_api_validator

logger = logging.getLogger(__name__)

def secure_endpoint(endpoint_type: str, 
                   custom_rate_limits: Optional[Dict] = None,
                   max_request_size: Optional[int] = None,
                   allowed_content_types: Optional[List[str]] = None,
                   required_headers: Optional[List[str]] = None):
    """
    Comprehensive security decorator combining rate limiting and API validation
    
    Args:
        endpoint_type: Rate limit endpoint type
        custom_rate_limits: Custom rate limits to override defaults
        max_request_size: Maximum request size in bytes
        allowed_content_types: List of allowed content types
        required_headers: List of required headers
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Apply API validation first
                validator = get_api_validator()
                
                # Override configuration if provided
                if max_request_size is not None:
                    validator.max_request_size = max_request_size
                if allowed_content_types is not None:
                    validator.allowed_content_types = allowed_content_types
                if required_headers is not None:
                    validator.required_headers = required_headers
                
                validation_result = validator.validate_request()
                
                if not validation_result["valid"]:
                    # Log security event
                    try:
                        from backend.monitoring.logging_config import log_security_event
                        log_security_event("api_validation_failure", {
                            "reason": validation_result["reason"],
                            "endpoint": request.endpoint,
                            "method": request.method,
                            "path": request.path,
                            "ip_address": request.remote_addr,
                            "user_agent": request.headers.get('User-Agent'),
                            "content_type": request.content_type,
                            "content_length": request.content_length
                        }, g.get('user_id'), request.remote_addr)
                    except Exception as e:
                        logger.error(f"Error logging API validation failure: {e}")
                    
                    return jsonify({
                        "error": "Invalid request",
                        "message": "Request validation failed",
                        "details": validation_result["reason"]
                    }), validation_result["code"]
                
                # Apply rate limiting
                rate_limiter = get_rate_limiter()
                
                # Override default limits if provided
                if custom_rate_limits:
                    rate_limiter.default_limits[endpoint_type] = custom_rate_limits
                
                identifier = rate_limiter.get_identifier(request)
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests for {endpoint_type}",
                        "retry_after": int(limit_info['window_remaining'])
                    })
                    response.status_code = 429
                    response.headers['Retry-After'] = str(int(limit_info['window_remaining']))
                    response.headers['X-RateLimit-Limit'] = str(limit_info['limit'])
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = str(int(time.time() + limit_info['window_remaining']))
                    
                    return response
                
                # Sanitize request data
                if request.is_json:
                    request._json = validator.sanitize_input(request.get_json())
                elif request.form:
                    request.form = validator.sanitize_input(request.form.to_dict())
                
                # Add rate limit info to context for headers
                g.rate_limit_info = limit_info
                
                # Execute the endpoint function
                response = f(*args, **kwargs)
                
                # Add rate limit headers to response
                if isinstance(response, tuple):
                    response_obj, status_code = response
                    response_obj = add_rate_limit_headers(response_obj)
                    return response_obj, status_code
                else:
                    return add_rate_limit_headers(response)
                
            except Exception as e:
                logger.error(f"Security integration error: {e}")
                # Allow request if security checks fail
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Pre-configured security decorators for common endpoint types
def secure_assessment_endpoint():
    """Secure decorator for assessment endpoints"""
    return secure_endpoint(
        endpoint_type='assessment_submit',
        custom_rate_limits={'requests': 3, 'window': 300},
        max_request_size=512 * 1024,  # 512KB
        allowed_content_types=['application/json']
    )

def secure_assessment_view_endpoint():
    """Secure decorator for assessment view endpoints"""
    return secure_endpoint(
        endpoint_type='assessment_view',
        custom_rate_limits={'requests': 20, 'window': 300},
        max_request_size=256 * 1024,  # 256KB
        allowed_content_types=['application/json']
    )

def secure_auth_endpoint():
    """Secure decorator for authentication endpoints"""
    return secure_endpoint(
        endpoint_type='auth',
        custom_rate_limits={'requests': 10, 'window': 300},
        max_request_size=256 * 1024,  # 256KB
        allowed_content_types=['application/json', 'application/x-www-form-urlencoded']
    )

def secure_financial_endpoint():
    """Secure decorator for financial endpoints"""
    return secure_endpoint(
        endpoint_type='financial',
        custom_rate_limits={'requests': 50, 'window': 3600},
        max_request_size=1024 * 1024,  # 1MB
        allowed_content_types=['application/json']
    )

def secure_meme_endpoint():
    """Secure decorator for meme endpoints"""
    return secure_endpoint(
        endpoint_type='meme_upload',
        custom_rate_limits={'requests': 10, 'window': 3600},
        max_request_size=10 * 1024 * 1024,  # 10MB
        allowed_content_types=['multipart/form-data', 'application/json']
    )

def secure_analytics_endpoint():
    """Secure decorator for analytics endpoints"""
    return secure_endpoint(
        endpoint_type='analytics',
        custom_rate_limits={'requests': 30, 'window': 3600},
        max_request_size=512 * 1024,  # 512KB
        allowed_content_types=['application/json']
    )

def secure_webhook_endpoint():
    """Secure decorator for webhook endpoints"""
    return secure_endpoint(
        endpoint_type='webhook',
        custom_rate_limits={'requests': 100, 'window': 3600},
        max_request_size=1024 * 1024,  # 1MB
        allowed_content_types=['application/json']
    )

def secure_admin_endpoint():
    """Secure decorator for admin endpoints"""
    return secure_endpoint(
        endpoint_type='admin',
        custom_rate_limits={'requests': 200, 'window': 3600},
        max_request_size=1024 * 1024,  # 1MB
        allowed_content_types=['application/json']
    )

# Security middleware for Flask application
class SecurityMiddleware:
    """Flask middleware for comprehensive security"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Register error handlers
        app.register_error_handler(429, self.handle_rate_limit_exceeded)
        app.register_error_handler(413, self.handle_request_too_large)
        app.register_error_handler(415, self.handle_unsupported_media_type)
        app.register_error_handler(400, self.handle_bad_request)
    
    def before_request(self):
        """Security checks before request processing"""
        try:
            # Basic API validation for all requests
            validator = get_api_validator()
            validation_result = validator.validate_request()
            
            if not validation_result["valid"]:
                # Log security event
                try:
                    from backend.monitoring.logging_config import log_security_event
                    log_security_event("api_validation_failure", {
                        "reason": validation_result["reason"],
                        "endpoint": request.endpoint,
                        "method": request.method,
                        "path": request.path,
                        "ip_address": request.remote_addr,
                        "user_agent": request.headers.get('User-Agent'),
                        "content_type": request.content_type,
                        "content_length": request.content_length
                    }, g.get('user_id'), request.remote_addr)
                except Exception as e:
                    logger.error(f"Error logging API validation failure: {e}")
                
                # Return error response
                response = jsonify({
                    "error": "Invalid request",
                    "message": "Request validation failed",
                    "details": validation_result["reason"]
                })
                response.status_code = validation_result["code"]
                return response
            
            # Sanitize request data
            if request.is_json:
                request._json = validator.sanitize_input(request.get_json())
            elif request.form:
                request.form = validator.sanitize_input(request.form.to_dict())
                
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
    
    def after_request(self, response):
        """Add security headers to response"""
        try:
            # Add rate limit headers if available
            response = add_rate_limit_headers(response)
            
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            
        except Exception as e:
            logger.error(f"Error adding security headers: {e}")
        
        return response
    
    def handle_rate_limit_exceeded(self, error):
        """Handle rate limit exceeded errors"""
        return jsonify({
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later."
        }), 429
    
    def handle_request_too_large(self, error):
        """Handle request too large errors"""
        return jsonify({
            "error": "Request too large",
            "message": "The request size exceeds the allowed limit."
        }), 413
    
    def handle_unsupported_media_type(self, error):
        """Handle unsupported media type errors"""
        return jsonify({
            "error": "Unsupported media type",
            "message": "The request content type is not supported."
        }), 415
    
    def handle_bad_request(self, error):
        """Handle bad request errors"""
        return jsonify({
            "error": "Bad request",
            "message": "The request could not be processed."
        }), 400

# Security configuration
SECURITY_CONFIG = {
    'assessment': {
        'submit': {
            'rate_limit': {'requests': 3, 'window': 300},
            'max_size': 512 * 1024,
            'content_types': ['application/json']
        },
        'view': {
            'rate_limit': {'requests': 20, 'window': 300},
            'max_size': 256 * 1024,
            'content_types': ['application/json']
        }
    },
    'auth': {
        'login': {
            'rate_limit': {'requests': 10, 'window': 300},
            'max_size': 256 * 1024,
            'content_types': ['application/json', 'application/x-www-form-urlencoded']
        },
        'register': {
            'rate_limit': {'requests': 5, 'window': 300},
            'max_size': 256 * 1024,
            'content_types': ['application/json', 'application/x-www-form-urlencoded']
        }
    },
    'financial': {
        'general': {
            'rate_limit': {'requests': 50, 'window': 3600},
            'max_size': 1024 * 1024,
            'content_types': ['application/json']
        }
    },
    'meme': {
        'upload': {
            'rate_limit': {'requests': 10, 'window': 3600},
            'max_size': 10 * 1024 * 1024,
            'content_types': ['multipart/form-data', 'application/json']
        },
        'view': {
            'rate_limit': {'requests': 100, 'window': 3600},
            'max_size': 256 * 1024,
            'content_types': ['application/json']
        }
    }
}

def get_security_config(category: str, endpoint: str) -> Dict[str, Any]:
    """Get security configuration for specific endpoint"""
    return SECURITY_CONFIG.get(category, {}).get(endpoint, {})

def secure_endpoint_with_config(category: str, endpoint: str):
    """Secure decorator using configuration"""
    config = get_security_config(category, endpoint)
    
    return secure_endpoint(
        endpoint_type=f"{category}_{endpoint}",
        custom_rate_limits=config.get('rate_limit'),
        max_request_size=config.get('max_size'),
        allowed_content_types=config.get('content_types')
    )
