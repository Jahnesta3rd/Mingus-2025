#!/usr/bin/env python3
"""
Enhanced Authentication Middleware for MINGUS Assessment System
Integrates secure JWT validation, brute force protection, and session security
"""

import logging
from functools import wraps
from flask import request, jsonify, current_app, g, session
from typing import Optional, Dict, Any

# Import security components
from backend.security.secure_jwt_manager import get_jwt_manager
from backend.security.brute_force_protection import get_brute_force_protection
from backend.security.secure_session_manager import get_session_manager

logger = logging.getLogger(__name__)

def require_auth(f):
    """Enhanced authentication decorator with security features"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Get security components
            jwt_manager = get_jwt_manager()
            brute_force_protection = get_brute_force_protection()
            session_manager = get_session_manager()
            
            # Check for JWT token first (preferred method)
            auth_header = request.headers.get('Authorization')
            token = None
            session_id = None
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]
                
                # Validate JWT token with enhanced security
                jwt_result = jwt_manager.validate_secure_token(token)
                
                if jwt_result.get('valid'):
                    payload = jwt_result['payload']
                    user_id = payload.get('sub')
                    
                    # Check for token rotation
                    if jwt_result.get('rotation_needed'):
                        # Create new token
                        new_token = jwt_manager.refresh_token(token)
                        if new_token:
                            # Add new token to response headers
                            g.new_token = new_token
                    
                    # Set user context
                    g.current_user_id = user_id
                    g.auth_method = 'jwt'
                    g.token_payload = payload
                    
                    logger.debug(f"JWT authentication successful for user {user_id}")
                    return f(*args, **kwargs)
                else:
                    logger.warning(f"JWT validation failed: {jwt_result.get('reason')}")
            
            # Check for session-based authentication
            session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')
            
            if session_id:
                session_result = session_manager.validate_session(session_id)
                
                if session_result.get('valid'):
                    session_data = session_result['session']
                    user_id = session_data.user_id
                    
                    # Set user context
                    g.current_user_id = user_id
                    g.auth_method = 'session'
                    g.session_data = session_data
                    
                    logger.debug(f"Session authentication successful for user {user_id}")
                    return f(*args, **kwargs)
                else:
                    logger.warning(f"Session validation failed: {session_result.get('reason')}")
            
            # No valid authentication found
            logger.error("No valid authentication found")
            return jsonify({"error": "Authentication required"}), 401
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 401
    
    return decorated

def require_assessment_auth(f):
    """Enhanced authentication decorator specifically for assessment endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # First, require basic authentication
            auth_result = require_auth(lambda: None)()
            if hasattr(auth_result, 'status_code') and auth_result.status_code == 401:
                return auth_result
            
            # Get security components
            brute_force_protection = get_brute_force_protection()
            
            # Get assessment ID from request
            assessment_id = request.args.get('assessment_id') or \
                          request.json.get('assessment_id') if request.is_json else None
            
            if not assessment_id:
                return jsonify({"error": "Assessment ID required"}), 400
            
            # Check assessment submission protection
            user_id = g.current_user_id
            protection_result = brute_force_protection.check_assessment_submission_protection(
                user_id, assessment_id
            )
            
            if not protection_result.get('allowed'):
                return jsonify({
                    "error": "Assessment submission temporarily blocked",
                    "reason": protection_result.get('reason'),
                    "retry_after": protection_result.get('retry_after')
                }), 429
            
            # Set assessment context
            g.assessment_id = assessment_id
            g.assessment_attempts = protection_result.get('attempts', 0)
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Assessment authentication error: {str(e)}")
            return jsonify({"error": "Assessment authentication failed"}), 401
    
    return decorated

def require_secure_auth(f):
    """Enhanced authentication decorator with additional security checks"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # First, require basic authentication
            auth_result = require_auth(lambda: None)()
            if hasattr(auth_result, 'status_code') and auth_result.status_code == 401:
                return auth_result
            
            # Get security components
            jwt_manager = get_jwt_manager()
            brute_force_protection = get_brute_force_protection()
            
            user_id = g.current_user_id
            
            # Check for suspicious activity
            suspicious_activity = brute_force_protection.get_suspicious_activity(hours=1)
            user_suspicious = [event for event in suspicious_activity 
                             if event.get('identifier') == user_id]
            
            if user_suspicious:
                logger.warning(f"Suspicious activity detected for user {user_id}")
                return jsonify({
                    "error": "Suspicious activity detected",
                    "message": "Please contact support for assistance"
                }), 403
            
            # Additional security checks can be added here
            # For example, check if user's account is flagged, etc.
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Secure authentication error: {str(e)}")
            return jsonify({"error": "Secure authentication failed"}), 401
    
    return decorated

def get_current_user_id() -> Optional[str]:
    """Get the current user ID from authentication context"""
    try:
        if hasattr(g, 'current_user_id'):
            return g.current_user_id
        
        # Fallback to session
        return session.get('user_id')
        
    except Exception as e:
        logger.error(f"Error getting current user ID: {str(e)}")
        return None

def get_current_user_info() -> Optional[Dict[str, Any]]:
    """Get current user information from authentication context"""
    try:
        user_info = {}
        
        if hasattr(g, 'current_user_id'):
            user_info['user_id'] = g.current_user_id
            user_info['auth_method'] = getattr(g, 'auth_method', 'unknown')
            
            if hasattr(g, 'token_payload'):
                user_info['token_payload'] = g.token_payload
            
            if hasattr(g, 'session_data'):
                user_info['session_data'] = g.session_data
        
        return user_info if user_info else None
        
    except Exception as e:
        logger.error(f"Error getting current user info: {str(e)}")
        return None

def logout_user():
    """Enhanced logout function with security cleanup"""
    try:
        jwt_manager = get_jwt_manager()
        session_manager = get_session_manager()
        
        # Get current authentication info
        user_info = get_current_user_info()
        if not user_info:
            return
        
        user_id = user_info.get('user_id')
        
        # Revoke JWT token if present
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
            jwt_manager.revoke_token(token)
        
        # Revoke session if present
        session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')
        if session_id:
            session_manager.revoke_session(session_id, user_id)
        
        # Clear session data
        session.clear()
        
        # Clear Flask context
        if hasattr(g, 'current_user_id'):
            del g.current_user_id
        if hasattr(g, 'auth_method'):
            del g.auth_method
        if hasattr(g, 'token_payload'):
            del g.token_payload
        if hasattr(g, 'session_data'):
            del g.session_data
        
        logger.info(f"User {user_id} logged out successfully")
        
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")

def create_auth_response(user_id: str, remember_me: bool = False) -> Dict[str, Any]:
    """Create enhanced authentication response with security features"""
    try:
        jwt_manager = get_jwt_manager()
        session_manager = get_session_manager()
        brute_force_protection = get_brute_force_protection()
        
        # Create secure JWT token
        token = jwt_manager.create_secure_token(user_id)
        
        # Create secure session
        session_id = session_manager.create_secure_session(user_id, token, remember_me)
        
        # Record successful login
        brute_force_protection.record_successful_attempt(user_id, 'login')
        
        # Get user info (implement based on your user model)
        user_info = get_user_info(user_id)
        
        response_data = {
            'success': True,
            'token': token,
            'session_id': session_id,
            'user': user_info,
            'auth_method': 'jwt_session'
        }
        
        # Add token info
        token_info = jwt_manager.get_token_info(token)
        if token_info:
            response_data['token_info'] = {
                'expires_at': token_info['expires_at'].isoformat(),
                'issued_at': token_info['issued_at'].isoformat()
            }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error creating auth response: {str(e)}")
        raise

def get_user_info(user_id: str) -> Dict[str, Any]:
    """Get user information (implement based on your user model)"""
    # This is a placeholder - implement with your actual user database
    # Example implementation:
    """
    from your_models import User
    
    user = User.query.get(user_id)
    if user:
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role
        }
    return None
    """
    return {
        'id': user_id,
        'email': f'user_{user_id}@example.com',
        'first_name': 'User',
        'last_name': user_id
    }

def validate_auth_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate authentication request data"""
    errors = []
    
    # Validate email
    email = request_data.get('email', '').strip()
    if not email:
        errors.append("Email is required")
    elif not is_valid_email(email):
        errors.append("Invalid email format")
    
    # Validate password
    password = request_data.get('password', '')
    if not password:
        errors.append("Password is required")
    elif len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def handle_auth_error(error_type: str, details: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle authentication errors with appropriate responses"""
    error_responses = {
        'invalid_credentials': {
            'error': 'Invalid credentials',
            'message': 'Email or password is incorrect'
        },
        'account_locked': {
            'error': 'Account temporarily locked',
            'message': 'Too many failed login attempts'
        },
        'rate_limited': {
            'error': 'Rate limit exceeded',
            'message': 'Too many requests, please try again later'
        },
        'token_expired': {
            'error': 'Token expired',
            'message': 'Please log in again'
        },
        'session_expired': {
            'error': 'Session expired',
            'message': 'Please log in again'
        },
        'suspicious_activity': {
            'error': 'Suspicious activity detected',
            'message': 'Please contact support for assistance'
        }
    }
    
    response = error_responses.get(error_type, {
        'error': 'Authentication error',
        'message': 'An error occurred during authentication'
    })
    
    if details:
        response.update(details)
    
    return response
