"""
Financial CSRF Protection System
Comprehensive CSRF protection for all financial endpoints in MINGUS application

This module provides:
1. Secure CSRF token generation and validation
2. Financial endpoint protection decorators
3. Token rotation and session management
4. Security event logging and monitoring
5. Integration with Flask-WTF for enhanced protection
"""

import secrets
import hmac
import hashlib
import time
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from flask import Flask, session, request, jsonify, current_app, g, abort
from flask_wtf import CSRFProtect
from loguru import logger

class FinancialCSRFProtection:
    """Advanced CSRF protection system for financial operations"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.csrf_protect = None
        self.token_lifetime = 1800  # 30 minutes for financial operations
        self.max_tokens_per_session = 5
        self.required_endpoints = [
            # Income/Expense endpoints
            '/api/v1/financial/transactions',
            '/api/financial/transactions',
            '/api/financial/income',
            '/api/financial/expenses',
            
            # Subscription management
            '/api/payment/subscriptions',
            '/api/payment/subscriptions/',
            '/api/payment/subscriptions/me',
            '/api/payment/subscriptions/tiers',
            
            # Payment processing
            '/api/payment/payment-intents',
            '/api/payment/payment-methods',
            '/api/payment/customers',
            '/api/payment/invoices',
            
            # Financial goals and planning
            '/api/financial/goals',
            '/api/financial-goals',
            '/api/financial/questionnaire',
            '/api/financial/planning',
            
            # Weekly check-ins
            '/api/health/checkin',
            '/api/health/checkin/',
            
            # Financial profile updates
            '/api/financial/profile',
            '/api/financial/profile/',
            '/api/onboarding/financial-profile',
            
            # Billing and subscription changes
            '/api/payment/billing',
            '/api/payment/upgrade',
            '/api/payment/downgrade',
            '/api/payment/cancel',
            
            # Financial compliance
            '/api/financial/payment/process',
            '/api/financial/records/store',
            '/api/financial/breach/report',
            
            # Financial analysis
            '/api/financial-analysis/spending-patterns',
            '/api/financial/analytics',
            '/api/financial/export'
        ]
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize CSRF protection with Flask application"""
        self.app = app
        
        # Configure Flask-WTF CSRF protection
        app.config.setdefault('WTF_CSRF_ENABLED', True)
        app.config.setdefault('WTF_CSRF_TIME_LIMIT', self.token_lifetime)
        app.config.setdefault('WTF_CSRF_SSL_STRICT', True)
        app.config.setdefault('WTF_CSRF_HEADERS', ['X-CSRFToken', 'X-CSRF-Token'])
        
        # Initialize Flask-WTF CSRF protection
        self.csrf_protect = CSRFProtect(app)
        
        # Set up CSRF error handler using Flask error handler
        @app.errorhandler(400)
        def csrf_error(error):
            if hasattr(error, 'description') and 'CSRF' in error.description:
                logger.warning(f"CSRF validation failed: {error.description}")
                return jsonify({
                    'error': 'CSRF validation failed',
                    'message': 'Security token is invalid or expired. Please refresh the page and try again.',
                    'code': 'CSRF_ERROR'
                }), 400
            return error
        
        logger.info("🔒 Financial CSRF protection initialized successfully")
    
    def generate_financial_csrf_token(self, session_id: str = None) -> str:
        """
        Generate a secure CSRF token specifically for financial operations
        
        Args:
            session_id: Session identifier (defaults to current session)
            
        Returns:
            Secure CSRF token string
        """
        if not session_id:
            session_id = session.get('session_id', secrets.token_urlsafe(32))
        
        timestamp = str(int(time.time()))
        token_data = f"financial:{session_id}:{timestamp}"
        
        # Create HMAC signature with financial-specific salt
        signature = hmac.new(
            (current_app.config['SECRET_KEY'] + 'financial').encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Return token in format: financial:session_id:timestamp:signature
        return f"{token_data}:{signature}"
    
    def validate_financial_csrf_token(self, token: str, session_id: str = None) -> bool:
        """
        Validate a financial CSRF token for authenticity and freshness
        
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
            if len(parts) != 4 or parts[0] != 'financial':
                return False
            
            _, token_session_id, timestamp, signature = parts
            
            # Check session ID binding
            current_session_id = session_id or session.get('session_id')
            if token_session_id != current_session_id:
                logger.warning(f"Financial CSRF token session mismatch: expected {current_session_id}, got {token_session_id}")
                return False
            
            # Check timestamp freshness
            token_time = int(timestamp)
            current_time = int(time.time())
            
            if current_time - token_time > self.token_lifetime:
                logger.warning(f"Financial CSRF token expired: age {current_time - token_time}s, max {self.token_lifetime}s")
                return False
            
            # Verify HMAC signature
            token_data = f"financial:{token_session_id}:{timestamp}"
            expected_signature = hmac.new(
                (current_app.config['SECRET_KEY'] + 'financial').encode(),
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Financial CSRF token validation error: {e}")
            return False
    
    def cleanup_expired_tokens(self):
        """Clean up expired financial tokens from session storage"""
        if 'financial_csrf_tokens' not in session:
            return
        
        current_time = int(time.time())
        valid_tokens = {}
        
        for token_id, token_data in session['financial_csrf_tokens'].items():
            if current_time - token_data.get('created_at', 0) <= self.token_lifetime:
                valid_tokens[token_id] = token_data
        
        session['financial_csrf_tokens'] = valid_tokens
    
    def get_session_token_count(self) -> int:
        """Get the number of active financial tokens for current session"""
        return len(session.get('financial_csrf_tokens', {}))
    
    def log_financial_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log financial security events for monitoring and analysis"""
        event_data = {
            'event_type': f'financial_{event_type}',
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'endpoint': request.endpoint,
            'method': request.method,
            'financial_operation': True,
            'details': details
        }
        
        logger.warning(f"Financial security event: {event_type} - User: {user_id} - Details: {details}")
        
        # Store in security audit log if available
        if hasattr(current_app, 'security_audit_log'):
            current_app.security_audit_log.log_event(event_data)

def require_financial_csrf(f: Callable) -> Callable:
    """
    CSRF protection decorator for financial endpoints
    
    Validates CSRF token from headers or form data for all financial operations
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF validation for GET requests
        if request.method == 'GET':
            return f(*args, **kwargs)
        
        # Check if this is a financial endpoint
        endpoint_path = request.path
        is_financial_endpoint = any(
            endpoint_path.startswith(required) for required in FinancialCSRFProtection.required_endpoints
        )
        
        if not is_financial_endpoint:
            return f(*args, **kwargs)
        
        # Get CSRF protection instance
        csrf_protection = FinancialCSRFProtection()
        
        # Extract token from headers or form data
        token = (
            request.headers.get('X-CSRFToken') or 
            request.headers.get('X-CSRF-Token') or
            request.form.get('csrf_token') or
            request.get_json().get('csrf_token') if request.is_json else None
        )
        
        if not token:
            csrf_protection.log_financial_security_event(
                "csrf_token_missing", 
                session.get('user_id', 'anonymous'),
                {"endpoint": request.endpoint, "method": request.method, "path": endpoint_path}
            )
            return jsonify({
                "error": "CSRF token required",
                "message": "Security token is required for financial operations",
                "code": "FINANCIAL_CSRF_REQUIRED"
            }), 403
        
        # Validate token
        if not csrf_protection.validate_financial_csrf_token(token):
            csrf_protection.log_financial_security_event(
                "csrf_token_invalid", 
                session.get('user_id', 'anonymous'),
                {
                    "endpoint": request.endpoint, 
                    "method": request.method,
                    "path": endpoint_path,
                    "token_preview": token[:10] + "..." if len(token) > 10 else "invalid"
                }
            )
            return jsonify({
                "error": "Invalid CSRF token",
                "message": "Security token is invalid or expired for financial operation",
                "code": "FINANCIAL_CSRF_INVALID"
            }), 403
        
        # Log successful validation
        logger.info(f"Financial CSRF token validated successfully for endpoint: {request.endpoint}")
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_payment_csrf(f: Callable) -> Callable:
    """
    Enhanced CSRF protection decorator for payment processing endpoints
    
    Includes additional validation for payment-specific security requirements
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Apply standard financial CSRF protection
        csrf_result = require_financial_csrf(f)(*args, **kwargs)
        
        # If CSRF validation failed, return the error
        if isinstance(csrf_result, tuple) and len(csrf_result) == 2:
            response, status_code = csrf_result
            if status_code != 200:
                return response, status_code
        
        # Additional payment-specific security checks
        payment_amount = request.get_json().get('amount') if request.is_json else None
        if payment_amount:
            # Validate payment amount format
            try:
                amount = float(payment_amount)
                if amount <= 0 or amount > 1000000:  # $1M limit
                    logger.warning(f"Invalid payment amount: {amount}")
                    return jsonify({
                        "error": "Invalid payment amount",
                        "message": "Payment amount must be between $0.01 and $1,000,000"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "error": "Invalid payment amount format",
                    "message": "Payment amount must be a valid number"
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_subscription_csrf(f: Callable) -> Callable:
    """
    Enhanced CSRF protection decorator for subscription management endpoints
    
    Includes additional validation for subscription-specific security requirements
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Apply standard financial CSRF protection
        csrf_result = require_financial_csrf(f)(*args, **kwargs)
        
        # If CSRF validation failed, return the error
        if isinstance(csrf_result, tuple) and len(csrf_result) == 2:
            response, status_code = csrf_result
            if status_code != 200:
                return response, status_code
        
        # Additional subscription-specific security checks
        subscription_tier = request.get_json().get('tier') if request.is_json else None
        if subscription_tier:
            # Validate subscription tier format
            valid_tiers = ['budget', 'mid_tier', 'professional']
            if subscription_tier not in valid_tiers:
                logger.warning(f"Invalid subscription tier: {subscription_tier}")
                return jsonify({
                    "error": "Invalid subscription tier",
                    "message": f"Subscription tier must be one of: {', '.join(valid_tiers)}"
                }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function

def generate_financial_csrf_token_endpoint():
    """Endpoint to generate financial CSRF tokens for frontend use"""
    csrf_protection = FinancialCSRFProtection()
    
    # Clean up expired tokens
    csrf_protection.cleanup_expired_tokens()
    
    # Check token limit
    if csrf_protection.get_session_token_count() >= csrf_protection.max_tokens_per_session:
        return jsonify({
            "error": "Token limit exceeded",
            "message": "Maximum number of active financial tokens reached"
        }), 429
    
    # Generate new token
    token = csrf_protection.generate_financial_csrf_token()
    
    # Store token metadata in session
    if 'financial_csrf_tokens' not in session:
        session['financial_csrf_tokens'] = {}
    
    token_id = secrets.token_urlsafe(16)
    session['financial_csrf_tokens'][token_id] = {
        'token': token,
        'created_at': int(time.time()),
        'endpoint': request.endpoint
    }
    
    return jsonify({
        "csrf_token": token,
        "expires_in": csrf_protection.token_lifetime,
        "token_id": token_id,
        "type": "financial"
    })

# Global CSRF protection instance
financial_csrf = FinancialCSRFProtection()

def init_financial_csrf_protection(app: Flask):
    """Initialize financial CSRF protection with Flask application"""
    financial_csrf.init_app(app)
    
    # Register CSRF token generation endpoint
    app.add_url_rule(
        '/api/financial/csrf-token',
        'generate_financial_csrf_token',
        generate_financial_csrf_token_endpoint,
        methods=['GET']
    )
    
    logger.info("🔒 Financial CSRF protection system initialized")
    return financial_csrf
