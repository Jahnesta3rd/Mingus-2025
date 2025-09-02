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

def init_security(app):
    """Initialize security components for the Flask application"""
    security_middleware = SecurityMiddleware()
    security_middleware.init_app(app)
    
    # Initialize CSP middleware
    from backend.middleware.csp_middleware import init_csp
    csp_middleware = init_csp(app)
    
    # Return security components for potential use
    return {
        'middleware': security_middleware,
        'csp_middleware': csp_middleware,
        'decorators': {
            'require_https': require_https,
            'validate_financial_data': validate_financial_data,
            'audit_financial_access': audit_financial_access
        }
    }

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
            
            # Validate expense amounts
            if 'monthly_expenses' in data:
                expenses = self.parse_amount(data['monthly_expenses'])
                if expenses is not None:
                    if expenses < limits.get('min_amount', 0):
                        validation_errors.append(f"Monthly expenses must be at least ${limits.get('min_amount', 0):,.2f}")
                    if expenses > limits.get('max_monthly_expenses', 500000):
                        validation_errors.append(f"Monthly expenses cannot exceed ${limits.get('max_monthly_expenses', 500000):,.2f}")
            
            # Validate account numbers (basic format check)
            if 'account_number' in data:
                account_num = str(data['account_number']).strip()
                if not re.match(r'^\d{8,17}$', account_num):
                    validation_errors.append("Account number must be 8-17 digits")
            
            # Validate routing numbers
            if 'routing_number' in data:
                routing_num = str(data['routing_number']).strip()
                if not re.match(r'^\d{9}$', routing_num):
                    validation_errors.append("Routing number must be exactly 9 digits")
            
            # Validate SSN (basic format check)
            if 'ssn' in data:
                ssn = str(data['ssn']).replace('-', '').replace(' ', '')
                if not re.match(r'^\d{9}$', ssn):
                    validation_errors.append("SSN must be exactly 9 digits")
            
            # Validate email addresses
            if 'email' in data:
                email = str(data['email']).strip()
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    validation_errors.append("Invalid email format")
            
            # Validate phone numbers
            if 'phone' in data:
                phone = str(data['phone']).replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
                if not re.match(r'^\d{10,11}$', phone):
                    validation_errors.append("Phone number must be 10-11 digits")
            
            # If validation errors found, return 400 response
            if validation_errors:
                self.log_validation_error(validation_errors)
                return jsonify({
                    'error': 'Validation failed',
                    'validation_errors': validation_errors,
                    'request_id': g.get('request_id', 'unknown')
                }), 400
                
        except Exception as e:
            logger.error(f"Error during financial validation: {str(e)}")
            return jsonify({
                'error': 'Validation error',
                'message': 'An error occurred during validation',
                'request_id': g.get('request_id', 'unknown')
            }), 400
    
    def parse_amount(self, value) -> Optional[float]:
        """Parse amount value, handling various formats"""
        if value is None:
            return None
        
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.-]', '', str(value))
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def is_financial_endpoint(self) -> bool:
        """Check if current endpoint handles financial data"""
        financial_paths = [
            '/api/financial-profile',
            '/api/income',
            '/api/expenses',
            '/api/bank-account',
            '/api/plaid'
        ]
        
        return any(request.path.startswith(path) for path in financial_paths)
    
    def check_rate_limit(self):
        """Basic rate limiting check"""
        # This is a simplified rate limiting implementation
        # In production, use Redis or a dedicated rate limiting library
        client_ip = request.remote_addr
        current_time = datetime.utcnow()
        
        # Store rate limit data in app context (simplified)
        if not hasattr(current_app, 'rate_limit_data'):
            current_app.rate_limit_data = {}
        
        if client_ip not in current_app.rate_limit_data:
            current_app.rate_limit_data[client_ip] = {
                'requests': 1,
                'window_start': current_time
            }
        else:
            # Reset window if more than 1 minute has passed
            time_diff = (current_time - current_app.rate_limit_data[client_ip]['window_start']).total_seconds()
            if time_diff > 60:
                current_app.rate_limit_data[client_ip] = {
                    'requests': 1,
                    'window_start': current_time
                }
            else:
                current_app.rate_limit_data[client_ip]['requests'] += 1
                
                # Check if limit exceeded (100 requests per minute)
                if current_app.rate_limit_data[client_ip]['requests'] > 100:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': 'Too many requests',
                        'request_id': g.get('request_id', 'unknown')
                    }), 429
    
    def log_request(self):
        """Log request details for security monitoring"""
        logger.info(f"Request: {request.method} {request.path} | IP: {request.remote_addr} | ID: {g.get('request_id', 'unknown')}")
        
        # Log sensitive endpoints
        if self.is_financial_endpoint():
            logger.warning(f"Financial data access: {request.method} {request.path} | IP: {request.remote_addr}")
    
    def log_response(self, response):
        """Log response details for security monitoring"""
        logger.info(f"Response: {response.status_code} | ID: {g.get('request_id', 'unknown')}")
    
    def log_validation_error(self, errors: List[str]):
        """Log validation errors for security monitoring"""
        logger.warning(f"Validation errors: {errors} | IP: {request.remote_addr} | ID: {g.get('request_id', 'unknown')}")
    
    def handle_validation_error(self, error):
        """Handle validation errors"""
        return jsonify({
            'error': 'Validation error',
            'message': 'Invalid request data',
            'request_id': g.get('request_id', 'unknown')
        }), 400
    
    def handle_payload_too_large(self, error):
        """Handle payload too large errors"""
        return jsonify({
            'error': 'Payload too large',
            'message': 'Request payload exceeds maximum allowed size',
            'request_id': g.get('request_id', 'unknown')
        }), 413
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for templates"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block'
        }

def require_https(f):
    """Decorator to require HTTPS"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only require HTTPS in production
        if not request.is_secure and current_app.config.get('ENV') == 'production':
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