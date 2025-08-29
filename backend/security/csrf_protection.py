"""
CSRF Protection System
Provides comprehensive CSRF token generation, validation, and protection for assessment endpoints
"""

import secrets
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import session, request, jsonify, current_app, g
from functools import wraps
from loguru import logger

class CSRFProtection:
    """CSRF protection system with secure token generation and validation"""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_lifetime = 3600  # 1 hour
        self.max_tokens_per_session = 10
    
    def generate_csrf_token(self, session_id: str = None) -> str:
        """
        Generate a secure CSRF token with session binding and timestamp
        
        Args:
            session_id: Session identifier (defaults to current session)
            
        Returns:
            Secure CSRF token string
        """
        if not session_id:
            session_id = session.get('session_id', secrets.token_urlsafe(32))
        
        timestamp = str(int(time.time()))
        token_data = f"{session_id}:{timestamp}"
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Return token in format: session_id:timestamp:signature
        return f"{token_data}:{signature}"
    
    def validate_csrf_token(self, token: str, session_id: str = None) -> bool:
        """
        Validate a CSRF token for authenticity and freshness
        
        Args:
            token: CSRF token to validate
            session_id: Session identifier to check against
            
        Returns:
            True if token is valid, False otherwise
        """
        if not token:
            return False
        
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False
            
            token_session_id, timestamp, signature = parts
            
            # Check session ID binding
            current_session_id = session_id or session.get('session_id')
            if token_session_id != current_session_id:
                logger.warning(f"CSRF token session mismatch: expected {current_session_id}, got {token_session_id}")
                return False
            
            # Check timestamp freshness
            token_time = int(timestamp)
            current_time = int(time.time())
            
            if current_time - token_time > self.token_lifetime:
                logger.warning(f"CSRF token expired: age {current_time - token_time}s, max {self.token_lifetime}s")
                return False
            
            # Verify HMAC signature
            token_data = f"{token_session_id}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"CSRF token validation error: {e}")
            return False
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens from session storage"""
        if 'csrf_tokens' not in session:
            return
        
        current_time = int(time.time())
        valid_tokens = {}
        
        for token_id, token_data in session['csrf_tokens'].items():
            if current_time - token_data.get('created_at', 0) <= self.token_lifetime:
                valid_tokens[token_id] = token_data
        
        session['csrf_tokens'] = valid_tokens
    
    def get_session_token_count(self) -> int:
        """Get the number of active tokens for current session"""
        return len(session.get('csrf_tokens', {}))
    
    def _generate_signature(self, token_data: str) -> str:
        """Generate HMAC signature for token data"""
        return hmac.new(
            self.secret_key.encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()

def log_security_event(event_type: str, user_id: str, details: Dict[str, Any]):
    """Log security events for monitoring and analysis"""
    event_data = {
        'event_type': event_type,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'endpoint': request.endpoint,
        'method': request.method,
        'details': details
    }
    
    logger.warning(f"Security event: {event_type} - User: {user_id} - Details: {details}")
    
    # Store in security audit log if available
    if hasattr(current_app, 'security_audit_log'):
        current_app.security_audit_log.log_event(event_data)

def require_csrf_token(f):
    """
    CSRF protection decorator for assessment endpoints
    
    Validates CSRF token from headers or form data
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF validation for GET requests
        if request.method == 'GET':
            return f(*args, **kwargs)
        
        # Get CSRF protection instance
        csrf_protection = CSRFProtection(current_app.config['SECRET_KEY'])
        
        # Extract token from headers or form data
        token = (
            request.headers.get('X-CSRFToken') or 
            request.headers.get('X-CSRF-Token') or
            request.form.get('csrf_token') or
            request.get_json().get('csrf_token') if request.is_json else None
        )
        
        if not token:
            log_security_event(
                "csrf_token_missing", 
                session.get('user_id', 'anonymous'),
                {"endpoint": request.endpoint, "method": request.method}
            )
            return jsonify({
                "error": "CSRF token required",
                "message": "Security token is required for this operation"
            }), 403
        
        # Validate token
        if not csrf_protection.validate_csrf_token(token):
            log_security_event(
                "csrf_token_invalid", 
                session.get('user_id', 'anonymous'),
                {
                    "endpoint": request.endpoint, 
                    "method": request.method,
                    "token_preview": token[:10] + "..." if len(token) > 10 else "invalid"
                }
            )
            return jsonify({
                "error": "Invalid CSRF token",
                "message": "Security token is invalid or expired"
            }), 403
        
        # Log successful validation
        logger.info(f"CSRF token validated successfully for endpoint: {request.endpoint}")
        
        return f(*args, **kwargs)
    
    return decorated_function

def generate_csrf_token_endpoint():
    """Endpoint to generate CSRF tokens for frontend use"""
    csrf_protection = CSRFProtection(current_app.config['SECRET_KEY'])
    
    # Clean up expired tokens
    csrf_protection.cleanup_expired_tokens()
    
    # Check token limit
    if csrf_protection.get_session_token_count() >= csrf_protection.max_tokens_per_session:
        return jsonify({
            "error": "Token limit exceeded",
            "message": "Maximum number of active tokens reached"
        }), 429
    
    # Generate new token
    token = csrf_protection.generate_csrf_token()
    
    # Store token metadata in session
    if 'csrf_tokens' not in session:
        session['csrf_tokens'] = {}
    
    token_id = secrets.token_urlsafe(16)
    session['csrf_tokens'][token_id] = {
        'token': token,
        'created_at': int(time.time()),
        'endpoint': request.endpoint
    }
    
    return jsonify({
        "csrf_token": token,
        "expires_in": csrf_protection.token_lifetime,
        "token_id": token_id
    })

def validate_assessment_csrf(f):
    """
    Specialized CSRF decorator for assessment submission endpoints
    
    Includes additional validation for assessment-specific security requirements
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Apply standard CSRF protection
        csrf_result = require_csrf_token(f)(*args, **kwargs)
        
        # If CSRF validation failed, return the error
        if isinstance(csrf_result, tuple) and len(csrf_result) == 2:
            response, status_code = csrf_result
            if status_code != 200:
                return response, status_code
        
        # Additional assessment-specific security checks
        assessment_type = kwargs.get('assessment_type')
        if assessment_type:
            # Validate assessment type format
            if not re.match(r'^[a-zA-Z0-9_-]+$', assessment_type):
                log_security_event(
                    "invalid_assessment_type",
                    session.get('user_id', 'anonymous'),
                    {"assessment_type": assessment_type}
                )
                return jsonify({
                    "error": "Invalid assessment type",
                    "message": "Assessment type contains invalid characters"
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

# Import regex for assessment type validation
import re
