"""
Security Middleware
Provides security headers, input validation, and audit logging for financial data
"""

import re
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import request, g, current_app, jsonify
from loguru import logger
from functools import wraps

class SecurityMiddleware:
    """Security middleware for financial profile endpoints"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.errorhandler(400)(self.handle_validation_error)
        app.errorhandler(413)(self.handle_payload_too_large)
        
        # Register security decorators
        app.jinja_env.globals['security_headers'] = self.get_security_headers
        
        logger.info("Security middleware initialized")
    
    def before_request(self):
        """Process requests before handling"""
        # Generate request ID for tracking
        g.request_id = str(uuid.uuid4())
        
        # Log request details
        self.log_request()
        
        # Validate financial data if applicable
        if self.is_financial_endpoint():
            self.validate_financial_input()
        
        # Check rate limiting
        self.check_rate_limit()
    
    def after_request(self, response):
        """Process responses after handling"""
        # Add security headers
        self.add_security_headers(response)
        
        # Log response details
        self.log_response(response)
        
        # Add request ID to response headers
        response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
        
        return response
    
    def add_security_headers(self, response):
        """Add comprehensive security headers to response"""
        headers = current_app.config.get('SECURITY_HEADERS', {})
        
        for header, value in headers.items():
            response.headers[header] = value
        
        # Additional dynamic headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HTTPS enforcement
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response
    
    def validate_financial_input(self):
        """Validate financial data input with reasonable limits"""
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return
        
        try:
            data = request.get_json() or {}
            limits = current_app.config.get('FINANCIAL_VALIDATION_LIMITS', {})
            
            validation_errors = []
            
            # Validate income amounts
            if 'monthly_income' in data:
                income = self.parse_amount(data['monthly_income'])
                if income is not None:
                    if income < limits.get('min_amount', 0):
                        validation_errors.append(f"Monthly income must be at least ${limits.get('min_amount', 0):,.2f}")
                    if income > limits.get('max_monthly_income', 1000000):
                        validation_errors.append(f"Monthly income cannot exceed ${limits.get('max_monthly_income', 1000000):,.2f}")
            
            # Validate savings amounts
            if 'current_savings' in data:
                savings = self.parse_amount(data['current_savings'])
                if savings is not None and savings < limits.get('min_amount', 0):
                    validation_errors.append(f"Current savings must be at least ${limits.get('min_amount', 0):,.2f}")
            
            # Validate debt amounts
            if 'current_debt' in data:
                debt = self.parse_amount(data['current_debt'])
                if debt is not None:
                    if debt < limits.get('min_amount', 0):
                        validation_errors.append(f"Current debt must be at least ${limits.get('min_amount', 0):,.2f}")
                    if debt > limits.get('max_debt_amount', 5000000):
                        validation_errors.append(f"Current debt cannot exceed ${limits.get('max_debt_amount', 5000000):,.2f}")
            
            # Validate savings goals
            if 'savings_goal' in data:
                goal = self.parse_amount(data['savings_goal'])
                if goal is not None:
                    if goal < limits.get('min_amount', 0):
                        validation_errors.append(f"Savings goal must be at least ${limits.get('min_amount', 0):,.2f}")
                    if goal > limits.get('max_savings_goal', 10000000):
                        validation_errors.append(f"Savings goal cannot exceed ${limits.get('max_savings_goal', 10000000):,.2f}")
            
            # Validate frequency options
            if 'income_frequency' in data:
                frequency = data['income_frequency']
                valid_frequencies = limits.get('max_frequency_options', [])
                if frequency not in valid_frequencies:
                    validation_errors.append(f"Income frequency must be one of: {', '.join(valid_frequencies)}")
            
            # Validate income sources array
            if 'income_sources' in data and isinstance(data['income_sources'], list):
                for i, source in enumerate(data['income_sources']):
                    if 'amount' in source:
                        amount = self.parse_amount(source['amount'])
                        if amount is not None:
                            if amount < limits.get('min_amount', 0):
                                validation_errors.append(f"Income source {i+1} amount must be at least ${limits.get('min_amount', 0):,.2f}")
                            if amount > limits.get('max_income_per_source', 1000000):
                                validation_errors.append(f"Income source {i+1} amount cannot exceed ${limits.get('max_income_per_source', 1000000):,.2f}")
            
            # If validation errors exist, return 400
            if validation_errors:
                self.log_validation_error(validation_errors)
                return jsonify({
                    'error': 'Validation failed',
                    'details': validation_errors,
                    'request_id': g.get('request_id')
                }), 400
                
        except Exception as e:
            logger.error(f"Financial validation error: {str(e)}")
            return jsonify({
                'error': 'Invalid request format',
                'request_id': g.get('request_id')
            }), 400
    
    def parse_amount(self, value) -> Optional[float]:
        """Parse and validate amount values"""
        if value is None:
            return None
        
        try:
            # Remove currency symbols and commas
            if isinstance(value, str):
                value = re.sub(r'[$,]', '', value.strip())
            
            amount = float(value)
            return amount if amount >= 0 else None
        except (ValueError, TypeError):
            return None
    
    def is_financial_endpoint(self) -> bool:
        """Check if current endpoint handles financial data"""
        financial_patterns = [
            r'/api/financial-profile',
            r'/api/onboarding/financial',
            r'/api/income',
            r'/api/savings',
            r'/api/debt'
        ]
        
        path = request.path.lower()
        return any(re.search(pattern, path) for pattern in financial_patterns)
    
    def check_rate_limit(self):
        """Check rate limiting for financial endpoints"""
        if not self.is_financial_endpoint():
            return
        
        # Simple rate limiting - in production, use Redis or similar
        client_ip = request.remote_addr
        current_time = datetime.now()
        
        # This is a basic implementation - consider using Flask-Limiter for production
        if hasattr(g, 'rate_limit_data'):
            last_request = g.rate_limit_data.get('last_request')
            request_count = g.rate_limit_data.get('count', 0)
            
            if last_request and (current_time - last_request).seconds < 60:
                if request_count > 10:  # 10 requests per minute for financial endpoints
                    logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                    return jsonify({
                        'error': 'Rate limit exceeded. Please try again later.',
                        'request_id': g.get('request_id')
                    }), 429
                g.rate_limit_data['count'] = request_count + 1
            else:
                g.rate_limit_data = {
                    'last_request': current_time,
                    'count': 1
                }
        else:
            g.rate_limit_data = {
                'last_request': current_time,
                'count': 1
            }
    
    def log_request(self):
        """Log request details for audit"""
        if not current_app.config.get('AUDIT_LOG_ENABLED', True):
            return
        
        audit_data = {
            'request_id': g.get('request_id'),
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'user_id': getattr(g, 'user_id', None),
            'session_id': request.cookies.get('session'),
            'is_financial': self.is_financial_endpoint()
        }
        
        logger.info(f"Request audit: {json.dumps(audit_data)}")
    
    def log_response(self, response):
        """Log response details for audit"""
        if not current_app.config.get('AUDIT_LOG_ENABLED', True):
            return
        
        audit_data = {
            'request_id': g.get('request_id'),
            'timestamp': datetime.now().isoformat(),
            'status_code': response.status_code,
            'response_size': len(response.get_data()),
            'is_financial': self.is_financial_endpoint()
        }
        
        logger.info(f"Response audit: {json.dumps(audit_data)}")
    
    def log_validation_error(self, errors: List[str]):
        """Log validation errors for audit"""
        audit_data = {
            'request_id': g.get('request_id'),
            'timestamp': datetime.now().isoformat(),
            'validation_errors': errors,
            'ip_address': request.remote_addr,
            'user_id': getattr(g, 'user_id', None)
        }
        
        logger.warning(f"Validation error audit: {json.dumps(audit_data)}")
    
    def handle_validation_error(self, error):
        """Handle validation errors"""
        return jsonify({
            'error': 'Bad request',
            'message': 'Invalid input data',
            'request_id': g.get('request_id')
        }), 400
    
    def handle_payload_too_large(self, error):
        """Handle payload too large errors"""
        return jsonify({
            'error': 'Payload too large',
            'message': 'Request body exceeds maximum allowed size',
            'request_id': g.get('request_id')
        }), 413
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for templates"""
        return current_app.config.get('SECURITY_HEADERS', {})

# Security decorators
def require_https(f):
    """Decorator to require HTTPS"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not current_app.debug:
            return jsonify({'error': 'HTTPS required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def validate_financial_data(f):
    """Decorator to validate financial data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Validation is handled by middleware
        return f(*args, **kwargs)
    return decorated_function

def audit_financial_access(f):
    """Decorator to audit financial data access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Audit logging is handled by middleware
        return f(*args, **kwargs)
    return decorated_function 