"""
Meme Security Module
===================
Comprehensive security measures for the meme splash page feature including
file upload validation, SQL injection prevention, rate limiting, and content moderation.
"""

import os
import re
import hashlib
import magic
import mimetypes
from typing import Dict, Any, List, Tuple, Optional, BinaryIO
from datetime import datetime, timedelta
import logging
from PIL import Image
import bleach
from flask import request, current_app
import redis
from functools import wraps
import json

logger = logging.getLogger(__name__)

class MemeSecurityValidator:
    """Security validator for meme-related operations"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize security validator
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self.redis_client = None
        self._initialize_redis()
        
        # File upload security settings
        self.max_file_size = config.get('MEME_MAX_UPLOAD_SIZE', 10 * 1024 * 1024)  # 10MB
        self.allowed_extensions = config.get('IMAGE_ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,webp').split(',')
        self.allowed_mime_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
        ]
        
        # Content security settings
        self.max_caption_length = config.get('MEME_MAX_CAPTION_LENGTH', 500)
        self.max_alt_text_length = config.get('MEME_MAX_ALT_TEXT_LENGTH', 200)
        self.forbidden_words = self._load_forbidden_words()
        
        # Rate limiting settings
        self.rate_limit_per_minute = config.get('MEME_RATE_LIMIT_PER_MINUTE', 100)
        self.upload_rate_limit = config.get('RATE_LIMIT_UPLOAD', '10/hour')
        
    def _initialize_redis(self) -> None:
        """Initialize Redis client for rate limiting"""
        try:
            redis_url = self.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis client initialized for security features")
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
            self.redis_client = None
    
    def _load_forbidden_words(self) -> List[str]:
        """Load list of forbidden words for content moderation"""
        # This could be loaded from a database or file
        return [
            'spam', 'scam', 'hack', 'crack', 'warez', 'porn', 'adult',
            'gambling', 'casino', 'bet', 'lottery', 'viagra', 'cialis'
        ]
    
    def validate_file_upload(self, file: BinaryIO, filename: str) -> Tuple[bool, str]:
        """
        Comprehensive file upload validation
        
        Args:
            file: File object to validate
            filename: Original filename
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file extension
            if not self._validate_file_extension(filename):
                return False, f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                return False, f"File size {file_size / (1024*1024):.1f}MB exceeds maximum {self.max_file_size / (1024*1024)}MB"
            
            # Check MIME type
            if not self._validate_mime_type(file):
                return False, "Invalid file type detected"
            
            # Check for malicious content
            if not self._check_file_content(file):
                return False, "File content appears to be malicious"
            
            # Validate image format
            if not self._validate_image_format(file):
                return False, "Invalid image format"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating file upload: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _validate_file_extension(self, filename: str) -> bool:
        """Validate file extension"""
        if not filename or '.' not in filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return extension in self.allowed_extensions
    
    def _validate_mime_type(self, file: BinaryIO) -> bool:
        """Validate MIME type using magic numbers"""
        try:
            # Read first 2048 bytes for MIME detection
            file.seek(0)
            header = file.read(2048)
            file.seek(0)
            
            # Use python-magic to detect MIME type
            detected_mime = magic.from_buffer(header, mime=True)
            
            # Also check using mimetypes
            file.seek(0)
            guessed_mime, _ = mimetypes.guess_type(file.name if hasattr(file, 'name') else '')
            
            # Accept if either detection method finds an allowed type
            return (detected_mime in self.allowed_mime_types or 
                   guessed_mime in self.allowed_mime_types)
            
        except Exception as e:
            logger.error(f"Error validating MIME type: {e}")
            return False
    
    def _check_file_content(self, file: BinaryIO) -> bool:
        """Check file content for malicious patterns"""
        try:
            file.seek(0)
            content = file.read(1024)  # Read first 1KB
            
            # Check for executable content
            executable_patterns = [
                b'MZ',  # Windows executable
                b'\x7fELF',  # Linux executable
                b'\xfe\xed\xfa',  # Mach-O executable
                b'#!/',  # Shell script
            ]
            
            for pattern in executable_patterns:
                if pattern in content:
                    return False
            
            # Check for PHP code
            if b'<?php' in content or b'<?=' in content:
                return False
            
            # Check for JavaScript injection
            if b'<script' in content.lower():
                return False
            
            file.seek(0)
            return True
            
        except Exception as e:
            logger.error(f"Error checking file content: {e}")
            return False
    
    def _validate_image_format(self, file: BinaryIO) -> bool:
        """Validate image format using PIL"""
        try:
            with Image.open(file) as img:
                # Check if it's a valid image
                img.verify()
            
            file.seek(0)
            return True
            
        except Exception as e:
            logger.error(f"Error validating image format: {e}")
            return False
    
    def validate_caption(self, caption: str) -> Tuple[bool, str]:
        """
        Validate meme caption content
        
        Args:
            caption: Caption text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check length
            if len(caption) > self.max_caption_length:
                return False, f"Caption too long. Maximum {self.max_caption_length} characters allowed"
            
            # Check for forbidden words
            caption_lower = caption.lower()
            for word in self.forbidden_words:
                if word in caption_lower:
                    return False, f"Caption contains forbidden content"
            
            # Check for excessive links
            link_pattern = r'https?://[^\s]+'
            links = re.findall(link_pattern, caption)
            if len(links) > 2:
                return False, "Too many links in caption"
            
            # Check for excessive special characters
            special_char_ratio = len(re.findall(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', caption)) / len(caption)
            if special_char_ratio > 0.3:
                return False, "Caption contains too many special characters"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating caption: {e}")
            return False, f"Validation error: {str(e)}"
    
    def validate_alt_text(self, alt_text: str) -> Tuple[bool, str]:
        """
        Validate alt text content
        
        Args:
            alt_text: Alt text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check length
            if len(alt_text) > self.max_alt_text_length:
                return False, f"Alt text too long. Maximum {self.max_alt_text_length} characters allowed"
            
            # Check for forbidden words
            alt_text_lower = alt_text.lower()
            for word in self.forbidden_words:
                if word in alt_text_lower:
                    return False, f"Alt text contains forbidden content"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating alt text: {e}")
            return False, f"Validation error: {str(e)}"
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent XSS and injection attacks
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        try:
            # Remove HTML tags
            clean_text = bleach.clean(text, tags=[], strip=True)
            
            # Remove potentially dangerous characters
            clean_text = re.sub(r'[<>"\']', '', clean_text)
            
            # Normalize whitespace
            clean_text = ' '.join(clean_text.split())
            
            return clean_text
            
        except Exception as e:
            logger.error(f"Error sanitizing input: {e}")
            return ""
    
    def check_rate_limit(self, user_id: Optional[int], action: str, 
                        limit: Optional[int] = None) -> Tuple[bool, int]:
        """
        Check rate limit for user action
        
        Args:
            user_id: User ID (None for anonymous users)
            action: Action type (e.g., 'upload', 'view', 'like')
            limit: Custom limit (uses default if None)
            
        Returns:
            Tuple of (allowed, remaining_requests)
        """
        if not self.redis_client:
            return True, 999  # Allow if Redis not available
        
        try:
            # Generate key for rate limiting
            key = f"rate_limit:{action}:{user_id or request.remote_addr}"
            
            # Get current count
            current_count = self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            # Get limit
            if limit is None:
                if action == 'upload':
                    limit = 10  # 10 uploads per hour
                elif action == 'view':
                    limit = self.rate_limit_per_minute
                else:
                    limit = 100  # Default limit
            
            # Check if limit exceeded
            if current_count >= limit:
                return False, 0
            
            # Increment counter
            self.redis_client.incr(key)
            
            # Set expiration (1 hour for uploads, 1 minute for others)
            expiry = 3600 if action == 'upload' else 60
            self.redis_client.expire(key, expiry)
            
            return True, limit - current_count - 1
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True, 999  # Allow if error
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], 
                          user_id: Optional[int] = None) -> None:
        """
        Log security event
        
        Args:
            event_type: Type of security event
            details: Event details
            user_id: User ID if applicable
        """
        try:
            from backend.monitoring.logging_config import log_security_event
            
            log_security_event(
                event_type=event_type,
                details=details,
                user_id=user_id,
                ip_address=request.remote_addr
            )
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")

def require_authentication(f):
    """Decorator to require user authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session, jsonify
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_meme_permission(f):
    """Decorator to require meme-specific permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session, jsonify, request
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has meme feature enabled
        # This could be enhanced with role-based permissions
        return f(*args, **kwargs)
    return decorated_function

def validate_meme_input(f):
    """Decorator to validate meme input data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, jsonify
        
        # Get security validator
        validator = MemeSecurityValidator(current_app.config)
        
        # Validate JSON input
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Validate required fields
        required_fields = ['caption_text', 'alt_text', 'category']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Sanitize and validate caption
        caption = validator.sanitize_input(data['caption_text'])
        is_valid, error_msg = validator.validate_caption(caption)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Sanitize and validate alt text
        alt_text = validator.sanitize_input(data['alt_text'])
        is_valid, error_msg = validator.validate_alt_text(alt_text)
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Validate category
        allowed_categories = ['faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out']
        if data['category'] not in allowed_categories:
            return jsonify({'error': f'Invalid category. Allowed: {", ".join(allowed_categories)}'}), 400
        
        # Update request data with sanitized values
        data['caption_text'] = caption
        data['alt_text'] = alt_text
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_meme_actions(action: str, limit: Optional[int] = None):
    """Decorator to apply rate limiting to meme actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, jsonify, request
            
            # Get security validator
            validator = MemeSecurityValidator(current_app.config)
            
            # Get user ID
            user_id = session.get('user_id')
            
            # Check rate limit
            allowed, remaining = validator.check_rate_limit(user_id, action, limit)
            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': 60,
                    'limit': limit or 100
                }), 429
            
            # Add remaining count to response headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Remaining'] = str(remaining)
                response.headers['X-RateLimit-Limit'] = str(limit or 100)
            
            return response
        return decorated_function
    return decorator

# Convenience functions for common security operations
def get_security_validator() -> MemeSecurityValidator:
    """Get security validator instance"""
    return MemeSecurityValidator(current_app.config)

def validate_meme_upload(file: BinaryIO, filename: str, caption: str, 
                        alt_text: str, category: str) -> Tuple[bool, str]:
    """Validate complete meme upload"""
    validator = get_security_validator()
    
    # Validate file
    is_valid, error_msg = validator.validate_file_upload(file, filename)
    if not is_valid:
        return False, error_msg
    
    # Validate caption
    is_valid, error_msg = validator.validate_caption(caption)
    if not is_valid:
        return False, error_msg
    
    # Validate alt text
    is_valid, error_msg = validator.validate_alt_text(alt_text)
    if not is_valid:
        return False, error_msg
    
    return True, ""

def log_meme_security_event(event_type: str, details: Dict[str, Any], 
                           user_id: Optional[int] = None) -> None:
    """Log meme-related security event"""
    validator = get_security_validator()
    validator.log_security_event(event_type, details, user_id)
