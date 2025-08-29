"""
API Request Validation Middleware
Comprehensive API request validation with security checks and input sanitization
"""

import re
import logging
from functools import wraps
from typing import Dict, Any, List, Optional
from flask import request, jsonify, g
import html
import json

logger = logging.getLogger(__name__)

class APIValidator:
    """Advanced API request validator with comprehensive security checks"""
    
    def __init__(self):
        self.max_request_size = 1024 * 1024  # 1MB
        self.allowed_content_types = ['application/json', 'application/x-www-form-urlencoded']
        self.required_headers = ['User-Agent', 'Accept']
        self.suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"data:text/html",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"onmouseover=",
            r"eval\(",
            r"document\.cookie",
            r"window\.location",
            r"alert\(",
            r"confirm\(",
            r"prompt\(",
            r"\.\.\/",
            r"\.\.\\",
            r"\/etc\/passwd",
            r"\/proc\/",
            r"\/sys\/",
            r"union\s+select",
            r"drop\s+table",
            r"insert\s+into",
            r"delete\s+from",
            r"update\s+set",
            r"exec\(",
            r"system\(",
            r"shell_exec",
            r"passthru",
            r"`.*`",
            r"\$\{.*\}",
            r"\\x[0-9a-fA-F]{2}",
            r"\\u[0-9a-fA-F]{4}",
            r"\\0",
            r"null\s+byte",
            r"\\x00",
            r"\\u0000"
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    def validate_request(self) -> Dict[str, Any]:
        """
        Validate incoming API request for security and compliance
        
        Returns:
            Dictionary with validation result
        """
        try:
            # Check request size
            if request.content_length and request.content_length > self.max_request_size:
                return {"valid": False, "reason": "Request too large", "code": 413}
            
            # Check content type
            if request.content_type and request.content_type not in self.allowed_content_types:
                return {"valid": False, "reason": "Unsupported content type", "code": 415}
            
            # Check required headers
            for header in self.required_headers:
                if not request.headers.get(header):
                    return {"valid": False, "reason": f"Missing required header: {header}", "code": 400}
            
            # Check for suspicious patterns in headers
            for header_name, header_value in request.headers:
                if self._contains_suspicious_patterns(header_value):
                    return {"valid": False, "reason": "Suspicious header content", "code": 400}
            
            # Check request body for suspicious patterns
            if request.data:
                body_content = request.data.decode('utf-8', errors='ignore')
                if self._contains_suspicious_patterns(body_content):
                    return {"valid": False, "reason": "Suspicious request body content", "code": 400}
            
            # Check JSON payload if present
            if request.is_json:
                json_data = request.get_json()
                if json_data and self._contains_suspicious_patterns_in_json(json_data):
                    return {"valid": False, "reason": "Suspicious JSON content", "code": 400}
            
            # Check form data if present
            if request.form:
                for field_name, field_value in request.form.items():
                    if self._contains_suspicious_patterns(field_value):
                        return {"valid": False, "reason": f"Suspicious form field: {field_name}", "code": 400}
            
            # Check query parameters
            for param_name, param_value in request.args.items():
                if self._contains_suspicious_patterns(param_value):
                    return {"valid": False, "reason": f"Suspicious query parameter: {param_name}", "code": 400}
            
            return {"valid": True}
            
        except Exception as e:
            logger.error(f"API validation error: {e}")
            return {"valid": False, "reason": "Validation error", "code": 500}
    
    def _contains_suspicious_patterns(self, value: str) -> bool:
        """Check if value contains suspicious patterns"""
        if not isinstance(value, str):
            return False
        
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                return True
        return False
    
    def _contains_suspicious_patterns_in_json(self, data: Any) -> bool:
        """Recursively check JSON data for suspicious patterns"""
        if isinstance(data, str):
            return self._contains_suspicious_patterns(data)
        elif isinstance(data, dict):
            for key, value in data.items():
                if self._contains_suspicious_patterns(str(key)) or self._contains_suspicious_patterns_in_json(value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._contains_suspicious_patterns_in_json(item):
                    return True
        return False
    
    def sanitize_input(self, value: Any) -> Any:
        """Sanitize input to prevent XSS and injection attacks"""
        if isinstance(value, str):
            # HTML escape to prevent XSS
            value = html.escape(value)
            # Remove null bytes
            value = value.replace('\x00', '')
            # Remove control characters except newlines and tabs
            value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        elif isinstance(value, dict):
            return {self.sanitize_input(k): self.sanitize_input(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.sanitize_input(item) for item in value]
        
        return value

# Global API validator instance
_api_validator = None

def get_api_validator() -> APIValidator:
    """Get global API validator instance"""
    global _api_validator
    if _api_validator is None:
        _api_validator = APIValidator()
    return _api_validator

def validate_api_request(f):
    """
    API validation decorator
    
    Validates incoming requests for security and compliance
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            validator = get_api_validator()
            validation_result = validator.validate_request()
            
            if not validation_result["valid"]:
                # Log security event
                try:
                    from backend.monitoring.logging_config import log_security_event
                    log_security_event("api_validation_failure", {
                        "reason": validation_result["reason"],
                        "endpoint": request.endpoint,
                        "method": request.method,
                        "path": request.path,
                        "ip_address": request.remote_addr,
                        "user_agent": request.headers.get('User-Agent'),
                        "content_type": request.content_type,
                        "content_length": request.content_length
                    }, g.get('user_id'), request.remote_addr)
                except Exception as e:
                    logger.error(f"Error logging API validation failure: {e}")
                
                return jsonify({
                    "error": "Invalid request",
                    "message": "Request validation failed",
                    "details": validation_result["reason"]
                }), validation_result["code"]
            
            # Sanitize request data
            if request.is_json:
                request._json = validator.sanitize_input(request.get_json())
            elif request.form:
                request.form = validator.sanitize_input(request.form.to_dict())
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"API validation error: {str(e)}")
            return jsonify({
                "error": "Validation error",
                "message": "An error occurred during request validation"
            }), 500
    
    return decorated_function

def validate_api_request_with_custom_config(max_size: Optional[int] = None, 
                                           allowed_types: Optional[List[str]] = None,
                                           required_headers: Optional[List[str]] = None):
    """
    API validation decorator with custom configuration
    
    Args:
        max_size: Maximum request size in bytes
        allowed_types: List of allowed content types
        required_headers: List of required headers
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                validator = get_api_validator()
                
                # Override configuration if provided
                if max_size is not None:
                    validator.max_request_size = max_size
                if allowed_types is not None:
                    validator.allowed_content_types = allowed_types
                if required_headers is not None:
                    validator.required_headers = required_headers
                
                validation_result = validator.validate_request()
                
                if not validation_result["valid"]:
                    # Log security event
                    try:
                        from backend.monitoring.logging_config import log_security_event
                        log_security_event("api_validation_failure", {
                            "reason": validation_result["reason"],
                            "endpoint": request.endpoint,
                            "method": request.method,
                            "path": request.path,
                            "ip_address": request.remote_addr,
                            "user_agent": request.headers.get('User-Agent'),
                            "content_type": request.content_type,
                            "content_length": request.content_length
                        }, g.get('user_id'), request.remote_addr)
                    except Exception as e:
                        logger.error(f"Error logging API validation failure: {e}")
                    
                    return jsonify({
                        "error": "Invalid request",
                        "message": "Request validation failed",
                        "details": validation_result["reason"]
                    }), validation_result["code"]
                
                # Sanitize request data
                if request.is_json:
                    request._json = validator.sanitize_input(request.get_json())
                elif request.form:
                    request.form = validator.sanitize_input(request.form.to_dict())
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"API validation error: {str(e)}")
                return jsonify({
                    "error": "Validation error",
                    "message": "An error occurred during request validation"
                }), 500
        
        return decorated_function
    return decorator

# Convenience decorators for common validation scenarios
def validate_json_request(max_size: Optional[int] = None):
    """Validate JSON API requests"""
    return validate_api_request_with_custom_config(
        max_size=max_size,
        allowed_types=['application/json']
    )

def validate_form_request(max_size: Optional[int] = None):
    """Validate form-encoded API requests"""
    return validate_api_request_with_custom_config(
        max_size=max_size,
        allowed_types=['application/x-www-form-urlencoded']
    )

def validate_file_upload(max_size: int = 10 * 1024 * 1024):  # 10MB default
    """Validate file upload requests"""
    return validate_api_request_with_custom_config(
        max_size=max_size,
        allowed_types=['multipart/form-data', 'application/octet-stream']
    )

# Security event logging helper
def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[str] = None, ip_address: Optional[str] = None):
    """Log security events for monitoring"""
    try:
        from backend.monitoring.logging_config import log_security_event as log_event
        log_event(event_type, details, user_id, ip_address)
    except Exception as e:
        logger.error(f"Error logging security event: {e}")
