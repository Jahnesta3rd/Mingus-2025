#!/usr/bin/env python3
"""
Enhanced Authentication Middleware
Provides authentication decorators with email verification integration
"""

from functools import wraps
from flask import request, jsonify, session, current_app, g
from loguru import logger
from typing import Optional, Callable, Any
import re

def login_required(f: Callable) -> Callable:
    """
    Decorator to require user authentication
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function with authentication check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if user is authenticated via session
            user_id = session.get('user_id')
            
            if not user_id:
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Get user from database to verify session validity
            user = current_app.user_service.get_user_by_id(user_id)
            if not user:
                # Clear invalid session
                session.clear()
                return jsonify({
                    'error': 'Invalid session',
                    'code': 'INVALID_SESSION'
                }), 401
            
            # Store user in Flask g for access in route handlers
            g.current_user = user
            g.user_id = user_id
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return jsonify({
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR'
            }), 500
    
    return decorated_function

def email_verification_required(f: Callable) -> Callable:
    """
    Decorator to require email verification
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function with email verification check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # First check authentication
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Get user from database
            user = current_app.user_service.get_user_by_id(user_id)
            if not user:
                session.clear()
                return jsonify({
                    'error': 'Invalid session',
                    'code': 'INVALID_SESSION'
                }), 401
            
            # Check if email is verified
            if not user.get('email_verified'):
                return jsonify({
                    'error': 'Email verification required',
                    'code': 'EMAIL_VERIFICATION_REQUIRED',
                    'message': 'Please verify your email address to access this feature'
                }), 403
            
            # Store user in Flask g
            g.current_user = user
            g.user_id = user_id
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Email verification check error: {e}")
            return jsonify({
                'error': 'Verification check failed',
                'code': 'VERIFICATION_ERROR'
            }), 500
    
    return decorated_function

def optional_auth(f: Callable) -> Callable:
    """
    Decorator for optional authentication (user can be authenticated or not)
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function with optional user context
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = session.get('user_id')
            
            if user_id:
                # User is authenticated, get user data
                user = current_app.user_service.get_user_by_id(user_id)
                if user:
                    g.current_user = user
                    g.user_id = user_id
                    g.is_authenticated = True
                else:
                    # Clear invalid session
                    session.clear()
                    g.is_authenticated = False
            else:
                g.is_authenticated = False
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Optional auth error: {e}")
            g.is_authenticated = False
            return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f: Callable) -> Callable:
    """
    Decorator to require admin privileges
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function with admin check
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # First check authentication
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Get user from database
            user = current_app.user_service.get_user_by_id(user_id)
            if not user:
                session.clear()
                return jsonify({
                    'error': 'Invalid session',
                    'code': 'INVALID_SESSION'
                }), 401
            
            # Check if user is admin
            if not user.get('is_admin'):
                return jsonify({
                    'error': 'Admin privileges required',
                    'code': 'ADMIN_REQUIRED'
                }), 403
            
            # Store user in Flask g
            g.current_user = user
            g.user_id = user_id
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Admin check error: {e}")
            return jsonify({
                'error': 'Admin check failed',
                'code': 'ADMIN_CHECK_ERROR'
            }), 500
    
    return decorated_function

def rate_limit_by_user(f: Callable) -> Callable:
    """
    Decorator for rate limiting by authenticated user
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function with rate limiting
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = session.get('user_id')
            if not user_id:
                # Fall back to IP-based rate limiting
                return f(*args, **kwargs)
            
            # Import rate limiting service
            from ..services.rate_limit_service import RateLimitService
            rate_limit_service = RateLimitService()
            
            # Check user-specific rate limit
            if not rate_limit_service.check_user_limit(user_id, f.__name__):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'code': 'RATE_LIMIT_EXCEEDED',
                    'message': 'Too many requests. Please try again later.'
                }), 429
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue without rate limiting if service fails
            return f(*args, **kwargs)
    
    return decorated_function

def validate_email_verification_status(f: Callable) -> Callable:
    """
    Decorator to validate email verification status and provide context
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function with verification status context
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user_id = session.get('user_id')
            
            if user_id:
                # Get user and verification status
                user = current_app.user_service.get_user_by_id(user_id)
                if user:
                    g.current_user = user
                    g.user_id = user_id
                    g.email_verified = user.get('email_verified', False)
                    
                    # Get verification details if not verified
                    if not g.email_verified:
                        try:
                            from ..services.email_verification_service import EmailVerificationService
                            verification_service = EmailVerificationService()
                            
                            # Check if verification is pending
                            pending_verification = verification_service.get_pending_verification(user_id)
                            if pending_verification:
                                g.pending_verification = {
                                    'id': pending_verification.id,
                                    'expires_at': pending_verification.expires_at.isoformat() if pending_verification.expires_at else None,
                                    'verification_type': pending_verification.verification_type
                                }
                        except Exception as e:
                            logger.warning(f"Could not get verification details: {e}")
                            g.pending_verification = None
                else:
                    g.email_verified = False
                    g.pending_verification = None
            else:
                g.email_verified = False
                g.pending_verification = None
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Email verification status check error: {e}")
            g.email_verified = False
            g.pending_verification = None
            return f(*args, **kwargs)
    
    return decorated_function

def csrf_protected(f: Callable) -> Callable:
    """
    Decorator for CSRF protection
    
    Args:
        f: Function to decorate
        
    Returns:
        Decorated function with CSRF protection
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Skip CSRF check for GET requests
            if request.method == 'GET':
                return f(*args, **kwargs)
            
            # Get CSRF token from headers
            csrf_token = request.headers.get('X-CSRF-Token')
            if not csrf_token:
                return jsonify({
                    'error': 'CSRF token required',
                    'code': 'CSRF_TOKEN_REQUIRED'
                }), 400
            
            # Validate CSRF token
            if not validate_csrf_token(csrf_token):
                return jsonify({
                    'error': 'Invalid CSRF token',
                    'code': 'INVALID_CSRF_TOKEN'
                }), 400
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"CSRF protection error: {e}")
            return jsonify({
                'error': 'CSRF protection failed',
                'code': 'CSRF_ERROR'
            }), 500
    
    return decorated_function

def validate_csrf_token(token: str) -> bool:
    """
    Validate CSRF token
    
    Args:
        token: CSRF token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        # Get session CSRF token
        session_token = session.get('csrf_token')
        if not session_token:
            return False
        
        # Compare tokens (constant-time comparison)
        if len(token) != len(session_token):
            return False
        
        result = 0
        for x, y in zip(token, session_token):
            result |= ord(x) ^ ord(y)
        
        return result == 0
        
    except Exception as e:
        logger.error(f"CSRF token validation error: {e}")
        return False

def generate_csrf_token() -> str:
    """
    Generate a new CSRF token
    
    Returns:
        New CSRF token
    """
    import secrets
    token = secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return token

def get_current_user() -> Optional[dict]:
    """
    Get current authenticated user from Flask g
    
    Returns:
        Current user dict or None if not authenticated
    """
    return getattr(g, 'current_user', None)

def get_user_id() -> Optional[str]:
    """
    Get current user ID from Flask g
    
    Returns:
        Current user ID or None if not authenticated
    """
    return getattr(g, 'user_id', None)

def is_authenticated() -> bool:
    """
    Check if user is authenticated
    
    Returns:
        True if authenticated, False otherwise
    """
    return getattr(g, 'is_authenticated', False)

def is_email_verified() -> bool:
    """
    Check if current user's email is verified
    
    Returns:
        True if email is verified, False otherwise
    """
    return getattr(g, 'email_verified', False)

def get_pending_verification() -> Optional[dict]:
    """
    Get pending email verification details
    
    Returns:
        Pending verification dict or None
    """
    return getattr(g, 'pending_verification', None)
