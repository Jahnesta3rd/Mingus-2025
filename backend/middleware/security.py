from flask import Flask, request, jsonify, make_response
from functools import wraps
import time
import hashlib
import hmac
import os
from datetime import datetime, timedelta

class SecurityMiddleware:
    def __init__(self, app: Flask = None):
        self.app = app
        self.rate_limits = {}
        self.max_requests = 100  # per minute
        self.window_size = 60  # seconds
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        # Rate limiting
        client_ip = request.remote_addr
        current_time = time.time()
        
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []
        
        # Clean old requests
        self.rate_limits[client_ip] = [
            req_time for req_time in self.rate_limits[client_ip]
            if current_time - req_time < self.window_size
        ]
        
        # Check rate limit
        if len(self.rate_limits[client_ip]) >= self.max_requests:
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # Add current request
        self.rate_limits[client_ip].append(current_time)
        
        # CSRF protection
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            csrf_token = request.headers.get('X-CSRF-Token')
            if not self.validate_csrf_token(csrf_token):
                return jsonify({'error': 'Invalid CSRF token'}), 403
    
    def after_request(self, response):
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response
    
    def validate_csrf_token(self, token: str) -> bool:
        if not token:
            return False
        
        # For testing purposes, accept 'test-token'
        if token == 'test-token':
            return True
        
        # In production, implement proper CSRF token validation
        # This is a simplified example
        expected_token = os.environ.get('CSRF_SECRET_KEY', 'default-secret')
        return hmac.compare_digest(token, expected_token)

def require_csrf(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token:
            return jsonify({'error': 'CSRF token required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        # Implement proper JWT validation here
        if not validate_jwt_token(token):
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def validate_jwt_token(token: str) -> bool:
    # Implement JWT validation logic
    # This is a placeholder
    return True