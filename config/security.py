#!/usr/bin/env python3
"""
Security Configuration for Mingus Meme Splash Page
Handles file validation, SQL injection prevention, and rate limiting
"""

import os
import re
import hashlib
import hmac
from functools import wraps
from flask import request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class SecurityConfig:
    def __init__(self):
        self.redis_url = os.environ.get('RATE_LIMIT_STORAGE_URL', 'redis://localhost:6379/1')
        self.secret_key = os.environ.get('SECRET_KEY', 'default-secret-key')
        
        # Initialize rate limiter
        self.limiter = self._setup_rate_limiter()
        
        # Security settings
        self.max_file_size = int(os.environ.get('MAX_FILE_SIZE', 5242880))  # 5MB
        self.allowed_extensions = set(os.environ.get('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif,webp').split(','))
        self.cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
    
    def _setup_rate_limiter(self):
        """Initialize Flask-Limiter"""
        try:
            redis_client = redis.from_url(self.redis_url)
            redis_client.ping()  # Test connection
            
            return Limiter(
                app=current_app,
                key_func=get_remote_address,
                storage_uri=self.redis_url,
                default_limits=["1000 per hour", "100 per minute"]
            )
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
            return Limiter(
                app=current_app,
                key_func=get_remote_address,
                default_limits=["1000 per hour", "100 per minute"]
            )
    
    def validate_file_upload(self, file) -> dict:
        """Validate uploaded file for security"""
        if not file or not file.filename:
            return {'valid': False, 'error': 'No file provided'}
        
        # Check file extension
        if not self._is_allowed_file(file.filename):
            return {'valid': False, 'error': 'File type not allowed'}
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > self.max_file_size:
            return {'valid': False, 'error': 'File too large'}
        
        # Check for malicious content
        if not self._is_safe_file_content(file):
            return {'valid': False, 'error': 'File content not safe'}
        
        return {'valid': True}
    
    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _is_safe_file_content(self, file) -> bool:
        """Check if file content is safe"""
        try:
            # Read first 1KB to check for malicious content
            file.seek(0)
            content = file.read(1024)
            file.seek(0)  # Reset
            
            # Check for executable signatures
            dangerous_signatures = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'data:text/html',
                b'<?php',
                b'#!/bin/',
                b'MZ'  # PE executable
            ]
            
            for signature in dangerous_signatures:
                if signature in content.lower():
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking file content: {e}")
            return False
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent XSS"""
        if not text:
            return text
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Escape special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        return text
    
    def validate_sql_input(self, value) -> bool:
        """Validate input to prevent SQL injection"""
        if not isinstance(value, str):
            return True
        
        # Check for common SQL injection patterns
        dangerous_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'--',
            r'/\*',
            r'\*/',
            r'xp_',
            r'sp_'
        ]
        
        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, value_lower):
                return False
        
        return True
    
    def generate_csrf_token(self, user_id: str = None) -> str:
        """Generate CSRF token"""
        data = f"{user_id or 'anonymous'}:{request.remote_addr}"
        return hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def validate_csrf_token(self, token: str, user_id: str = None) -> bool:
        """Validate CSRF token"""
        expected_token = self.generate_csrf_token(user_id)
        return hmac.compare_digest(token, expected_token)
    
    def check_cors_origin(self, origin: str) -> bool:
        """Check if origin is allowed for CORS"""
        if not self.cors_origins or not self.cors_origins[0]:
            return True  # Allow all if not configured
        
        return origin in self.cors_origins

# Security decorators
def require_csrf_token(f):
    """Decorator to require CSRF token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            user_id = request.headers.get('X-User-ID')
            
            if not token or not security.validate_csrf_token(token, user_id):
                return jsonify({'error': 'Invalid CSRF token'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def validate_input(f):
    """Decorator to validate and sanitize input"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Sanitize form data
        if request.form:
            for key, value in request.form.items():
                if isinstance(value, str):
                    request.form[key] = security.sanitize_input(value)
        
        # Sanitize JSON data
        if request.is_json:
            data = request.get_json()
            if data:
                sanitized_data = {}
                for key, value in data.items():
                    if isinstance(value, str):
                        sanitized_data[key] = security.sanitize_input(value)
                    else:
                        sanitized_data[key] = value
                request._cached_json = sanitized_data
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_by_user(f):
    """Decorator for user-specific rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID')
        if user_id:
            # Apply stricter limits for authenticated users
            if not security.limiter.test_request(f"user:{user_id}"):
                return jsonify({'error': 'Rate limit exceeded'}), 429
        
        return f(*args, **kwargs)
    return decorated_function

# Global security instance
security = SecurityConfig()
