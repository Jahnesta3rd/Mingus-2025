"""
Rate Limiting Decorators for Financial Application
Comprehensive decorators for different rate limiting strategies
"""

import time
import logging
from functools import wraps
from typing import Dict, Any, Optional, Union, Callable
from flask import request, jsonify, g, current_app, Response
from .rate_limiter import get_rate_limiter, add_rate_limit_headers

logger = logging.getLogger(__name__)

def rate_limit(endpoint_type: str, custom_limits: Optional[Dict] = None):
    """
    Main rate limiting decorator
    
    Args:
        endpoint_type: Rate limit endpoint type
        custom_limits: Custom limits to override defaults
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                rate_limiter = get_rate_limiter()
                
                # Override default limits if provided
                if custom_limits:
                    rate_limiter.rate_limits[endpoint_type] = custom_limits
                
                identifier = rate_limiter.get_identifier(request)
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info.get('retry_after', 0)),
                        "endpoint": endpoint_type
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
                    return response
                
                # Store rate limit info for response headers
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_by_user(endpoint_type: str, custom_limits: Optional[Dict] = None):
    """
    Rate limiting decorator for authenticated users only
    
    Args:
        endpoint_type: Rate limit endpoint type
        custom_limits: Custom limits to override defaults
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check if user is authenticated
                user_id = g.get('user_id')
                if not user_id:
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'User authentication required for rate limiting'
                    }), 401
                
                rate_limiter = get_rate_limiter()
                
                # Override default limits if provided
                if custom_limits:
                    rate_limiter.rate_limits[endpoint_type] = custom_limits
                
                identifier = f"user:{user_id}"
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info.get('retry_after', 0)),
                        "endpoint": endpoint_type
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
                    return response
                
                # Store rate limit info for response headers
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"User rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_by_ip(endpoint_type: str, custom_limits: Optional[Dict] = None):
    """
    Rate limiting decorator based on IP address only
    
    Args:
        endpoint_type: Rate limit endpoint type
        custom_limits: Custom limits to override defaults
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                rate_limiter = get_rate_limiter()
                ip_address = rate_limiter._get_client_ip(request)
                identifier = f"ip:{ip_address}"
                
                # Override default limits if provided
                if custom_limits:
                    rate_limiter.rate_limits[endpoint_type] = custom_limits
                
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info.get('retry_after', 0)),
                        "endpoint": endpoint_type
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
                    return response
                
                # Store rate limit info for response headers
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"IP rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_financial(endpoint_type: str = 'financial_api'):
    """
    Rate limiting decorator specifically for financial endpoints
    
    Args:
        endpoint_type: Financial rate limit type
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                rate_limiter = get_rate_limiter()
                
                # Use user ID if authenticated, otherwise IP
                user_id = g.get('user_id')
                if user_id:
                    identifier = f"user:{user_id}"
                else:
                    ip_address = rate_limiter._get_client_ip(request)
                    identifier = f"ip:{ip_address}"
                
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Financial API rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info.get('retry_after', 0)),
                        "endpoint": endpoint_type,
                        "note": "Financial data access is rate limited for security"
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
                    return response
                
                # Store rate limit info for response headers
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Financial rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_payment(endpoint_type: str = 'payment'):
    """
    Rate limiting decorator specifically for payment endpoints
    
    Args:
        endpoint_type: Payment rate limit type
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                rate_limiter = get_rate_limiter()
                
                # Payment endpoints require authentication
                user_id = g.get('user_id')
                if not user_id:
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'User authentication required for payment operations'
                    }), 401
                
                identifier = f"user:{user_id}"
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Payment rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info.get('retry_after', 0)),
                        "endpoint": endpoint_type,
                        "note": "Payment operations are rate limited for security"
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
                    return response
                
                # Store rate limit info for response headers
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Payment rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_auth(endpoint_type: str):
    """
    Rate limiting decorator for authentication endpoints
    
    Args:
        endpoint_type: Authentication rate limit type (login, register, password_reset)
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                rate_limiter = get_rate_limiter()
                
                # Auth endpoints use IP-based rate limiting
                ip_address = rate_limiter._get_client_ip(request)
                identifier = f"ip:{ip_address}"
                
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Authentication rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info.get('retry_after', 0)),
                        "endpoint": endpoint_type,
                        "note": "Authentication attempts are rate limited for security"
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
                    return response
                
                # Store rate limit info for response headers
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Auth rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_assessment(endpoint_type: str):
    """
    Rate limiting decorator for assessment and onboarding endpoints
    
    Args:
        endpoint_type: Assessment rate limit type
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                rate_limiter = get_rate_limiter()
                
                # Use user ID if authenticated, otherwise IP
                user_id = g.get('user_id')
                if user_id:
                    identifier = f"user:{user_id}"
                else:
                    ip_address = rate_limiter._get_client_ip(request)
                    identifier = f"ip:{ip_address}"
                
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Assessment rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info.get('retry_after', 0)),
                        "endpoint": endpoint_type,
                        "note": "Assessment submissions are rate limited to ensure quality"
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
                    return response
                
                # Store rate limit info for response headers
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Assessment rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def rate_limit_webhook(endpoint_type: str = 'stripe_webhook'):
    """
    Rate limiting decorator for webhook endpoints
    
    Args:
        endpoint_type: Webhook rate limit type
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                rate_limiter = get_rate_limiter()
                
                # Webhook endpoints use IP-based rate limiting
                ip_address = rate_limiter._get_client_ip(request)
                identifier = f"ip:{ip_address}"
                
                limit_info = rate_limiter.is_rate_limited(identifier, endpoint_type)
                
                if limit_info['limited']:
                    rate_limiter.log_rate_limit_violation(identifier, endpoint_type, limit_info)
                    
                    response = jsonify({
                        "error": "Webhook rate limit exceeded",
                        "message": rate_limiter.get_rate_limit_message(endpoint_type),
                        "retry_after": int(limit_info.get('retry_after', 0)),
                        "endpoint": endpoint_type,
                        "note": "Webhook requests are rate limited to prevent abuse"
                    })
                    response.status_code = 429
                    response = add_rate_limit_headers(response, limit_info)
                    
                    return response
                
                # Store rate limit info for response headers
                g.rate_limit_info = limit_info
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Webhook rate limiting error: {e}")
                # Allow request if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def add_rate_limit_headers_to_response(response: Response) -> Response:
    """
    Add rate limit headers to response if available
    
    Args:
        response: Flask response object
        
    Returns:
        Response with rate limit headers
    """
    try:
        if hasattr(g, 'rate_limit_info'):
            limit_info = g.rate_limit_info
            response = add_rate_limit_headers(response, limit_info)
    except Exception as e:
        logger.error(f"Error adding rate limit headers to response: {e}")
    
    return response

# Convenience decorators for common use cases
login_rate_limit = rate_limit_auth('login')
register_rate_limit = rate_limit_auth('register')
password_reset_rate_limit = rate_limit_auth('password_reset')
financial_rate_limit = rate_limit_financial('financial_api')
payment_rate_limit = rate_limit_payment('payment')
assessment_submit_rate_limit = rate_limit_assessment('assessment_submit')
assessment_view_rate_limit = rate_limit_assessment('assessment_view')
webhook_rate_limit = rate_limit_webhook('stripe_webhook')
