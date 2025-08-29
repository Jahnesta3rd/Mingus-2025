"""
MINGUS Assessment Security System
Comprehensive input validation and injection prevention for assessment endpoints
"""

import re
import json
import logging
import bleach
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps
from flask import request, jsonify, current_app
from markupsafe import Markup
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class SecurityValidator:
    """Enhanced security validator for assessment endpoints"""
    
    def __init__(self):
        # SQL injection patterns
        self.sql_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b)",
            r"(\b(exec|execute)\b\s+(sp_|xp_|procedure|function))",
            r"(--\s|#\s|/\*|\*/|--\s*$|--\s*;)",
            r"(\b(or|and)\b\s*['\"]?\w*['\"]?\s*[=<>])",
            r"(\b(char|ascii|substring|length)\b\s*\([^)]*\))",
            r"(waitfor\s+delay|benchmark\s*\()",
            r"(\b(declare|cast|convert)\b)",
            r"(\b(xp_cmdshell|sp_executesql)\b)",
            r"(\b(backup|restore|attach|detach)\b\s+(database|table|file))",
            r"(\b(grant|revoke|deny)\b)",
            r"(\b(union|select|insert|update|delete|drop|create|alter)\b.*\b(or|and)\b)",
            r"(\b(or|and)\b.*\b(union|select|insert|update|delete|drop|create|alter)\b)"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"(<script[^>]*>.*?</script>)",
            r"(<script[^>]*>)",
            r"(javascript:.*)",
            r"(on\w+\s*=)",
            r"(<iframe[^>]*>)",
            r"(<object[^>]*>)",
            r"(<embed[^>]*>)",
            r"(<link[^>]*>)",
            r"(<meta[^>]*>)",
            r"(<form[^>]*>)",
            r"(<input[^>]*>)",
            r"(<textarea[^>]*>)",
            r"(<select[^>]*>)",
            r"(<button[^>]*>)",
            r"(<a[^>]*href\s*=\s*[\"']javascript:)",
            r"(<img[^>]*on\w+\s*=)",
            r"(<svg[^>]*on\w+\s*=)",
            r"(<math[^>]*on\w+\s*=)",
            r"(<link[^>]*on\w+\s*=)",
            r"(<body[^>]*on\w+\s*=)",
            r"(<div[^>]*on\w+\s*=)"
        ]
        
        # Command injection patterns
        self.cmd_patterns = [
            r"(\b(cat|ls|pwd|whoami|id|uname)\b)",
            r"(\b(rm|del|mkdir|touch|chmod)\b)",
            r"(\b(wget|curl|nc|telnet|ssh)\b)",
            r"(\b(python|perl|ruby|php|bash|sh)\b)",
            r"(&&|\|\||`|\$\()",  # Removed semicolon to avoid SQL conflicts
            r"(\b(sudo|su|sudoers)\b)",
            r"(\b(kill|ps|top|htop)\b)",
            r"(\b(netstat|ifconfig|ipconfig)\b)",
            r"(\b(ping|traceroute|nslookup)\b)",
            r"(\b(find|grep|sed|awk)\b)",
            r"(\b(tar|zip|unzip|gzip|gunzip)\b)",
            r"(\b(docker|kubectl|helm)\b)"
        ]
        
        # NoSQL injection patterns
        self.nosql_patterns = [
            r"(\$where\s*:)",
            r"(\$ne\s*:)",
            r"(\$gt\s*:)",
            r"(\$lt\s*:)",
            r"(\$regex\s*:)",
            r"(\$exists\s*:)",
            r"(\$in\s*:)",
            r"(\$nin\s*:)",
            r"(\$or\s*:)",
            r"(\$and\s*:)",
            r"(\$not\s*:)",
            r"(\$nor\s*:)",
            r"(\"\$where\")",
            r"(\"\$ne\")",
            r"(\"\$gt\")",
            r"(\"\$lt\")",
            r"(\"\$regex\")",
            r"(\"\$exists\")",
            r"(\"\$in\")",
            r"(\"\$nin\")",
            r"(\"\$or\")",
            r"(\"\$and\")",
            r"(\"\$not\")",
            r"(\"\$nor\")"
        ]
        
        # Path traversal patterns (more specific to avoid command injection conflicts)
        self.path_patterns = [
            r"(\.\./|\.\.\\)",
            r"(^/etc/passwd$|^/etc/shadow$)",  # Only exact matches
            r"(c:\\windows\\system32)",
            r"(^/proc/|^/sys/)",  # Only at start of string
            r"(^/dev/|^/tmp/)",   # Only at start of string
            r"(~/.ssh/|~/.bashrc)",
            r"(^/var/log/|^/var/www/)",  # Only at start of string
            r"(^/home/|^/root/)",        # Only at start of string
            r"(~/.ssh/id_rsa)",
            r"(~/.ssh/id_dsa)",
            r"(~/.ssh/known_hosts)"
        ]
        
        # Compile patterns for efficiency
        self.sql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.sql_patterns]
        self.xss_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.xss_patterns]
        self.cmd_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.cmd_patterns]
        self.nosql_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.nosql_patterns]
        self.path_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.path_patterns]
    
    def validate_input(self, input_string: str, field_name: str = "input") -> Dict[str, Any]:
        """Validate input string for security threats"""
        if not isinstance(input_string, str):
            return {"valid": False, "reason": f"{field_name} must be a string", "field": field_name}
        
        # Length validation
        if len(input_string) > 10000:  # Reasonable limit for assessment inputs
            return {"valid": False, "reason": f"{field_name} is too long (max 10,000 characters)", "field": field_name}
        
        if len(input_string.strip()) == 0:
            return {"valid": False, "reason": f"{field_name} cannot be empty", "field": field_name}
        
        input_lower = input_string.lower()
        
        # Check XSS patterns first (more specific)
        for i, pattern in enumerate(self.xss_regex):
            if pattern.search(input_lower):
                self._log_security_event("xss_attempt", field_name, self.xss_patterns[i])
                return {
                    "valid": False, 
                    "reason": f"Invalid input detected in {field_name}", 
                    "field": field_name,
                    "attack_type": "xss"
                }
        
        # Check path traversal patterns (before command injection to avoid false positives)
        for i, pattern in enumerate(self.path_regex):
            if pattern.search(input_lower):
                self._log_security_event("path_traversal_attempt", field_name, self.path_patterns[i])
                return {
                    "valid": False, 
                    "reason": f"Invalid input detected in {field_name}", 
                    "field": field_name,
                    "attack_type": "path_traversal"
                }
        
        # Check command injection patterns (before SQL to avoid false positives)
        for i, pattern in enumerate(self.cmd_regex):
            if pattern.search(input_lower):
                self._log_security_event("command_injection_attempt", field_name, self.cmd_patterns[i])
                return {
                    "valid": False, 
                    "reason": f"Invalid input detected in {field_name}", 
                    "field": field_name,
                    "attack_type": "command_injection"
                }
        
        # Check SQL injection patterns
        for i, pattern in enumerate(self.sql_regex):
            if pattern.search(input_lower):
                self._log_security_event("sql_injection_attempt", field_name, self.sql_patterns[i])
                return {
                    "valid": False, 
                    "reason": f"Invalid input detected in {field_name}", 
                    "field": field_name,
                    "attack_type": "sql_injection"
                }
        
        # Check NoSQL injection patterns
        for i, pattern in enumerate(self.nosql_regex):
            if pattern.search(input_lower):
                self._log_security_event("nosql_injection_attempt", field_name, self.nosql_patterns[i])
                return {
                    "valid": False, 
                    "reason": f"Invalid input detected in {field_name}", 
                    "field": field_name,
                    "attack_type": "nosql_injection"
                }
        
        return {"valid": True, "field": field_name}
    
    def validate_assessment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate assessment submission data"""
        if not isinstance(data, dict):
            return {"valid": False, "reason": "Assessment data must be a dictionary"}
        
        validation_errors = []
        sanitized_data = {}
        
        # Validate responses object
        responses = data.get('responses', {})
        if not isinstance(responses, dict):
            return {"valid": False, "reason": "Responses must be a dictionary"}
        
        # Validate each response field
        for field_name, field_value in responses.items():
            if isinstance(field_value, str):
                validation = self.validate_input(field_value, field_name)
                if not validation["valid"]:
                    validation_errors.append(validation)
                else:
                    sanitized_data[field_name] = self.sanitize_html_input(field_value)
            elif isinstance(field_value, list):
                # Handle checkbox/multiple choice responses
                if not all(isinstance(item, str) for item in field_value):
                    validation_errors.append({
                        "valid": False,
                        "reason": f"All items in {field_name} must be strings",
                        "field": field_name
                    })
                else:
                    sanitized_list = []
                    for item in field_value:
                        validation = self.validate_input(item, f"{field_name}_item")
                        if not validation["valid"]:
                            validation_errors.append(validation)
                        else:
                            sanitized_list.append(self.sanitize_html_input(item))
                    sanitized_data[field_name] = sanitized_list
            elif isinstance(field_value, (int, float)):
                # Validate numeric responses
                if field_value < 0 or field_value > 1000000:  # Reasonable range for assessment scores
                    validation_errors.append({
                        "valid": False,
                        "reason": f"Value for {field_name} is out of valid range",
                        "field": field_name
                    })
                else:
                    sanitized_data[field_name] = field_value
            else:
                validation_errors.append({
                    "valid": False,
                    "reason": f"Invalid data type for {field_name}",
                    "field": field_name
                })
        
        # Validate optional fields
        optional_fields = ['email', 'first_name', 'last_name', 'location', 'job_title', 'industry']
        for field in optional_fields:
            if field in data:
                field_value = data[field]
                if isinstance(field_value, str):
                    validation = self.validate_input(field_value, field)
                    if not validation["valid"]:
                        validation_errors.append(validation)
                    else:
                        sanitized_data[field] = self.sanitize_html_input(field_value)
        
        # Validate email format if provided
        if 'email' in sanitized_data:
            email_validation = self.validate_email(sanitized_data['email'])
            if not email_validation["valid"]:
                validation_errors.append(email_validation)
        
        if validation_errors:
            return {
                "valid": False,
                "errors": validation_errors,
                "reason": "Multiple validation errors found"
            }
        
        return {
            "valid": True,
            "sanitized_data": sanitized_data
        }
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """Validate email format"""
        if not email or not isinstance(email, str):
            return {
                "valid": False,
                "reason": "Email must be a non-empty string",
                "field": "email"
            }
        
        # Basic email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return {
                "valid": False,
                "reason": "Invalid email format",
                "field": "email"
            }
        
        # Additional checks for common email issues
        if '..' in email.split('@')[0]:  # Consecutive dots in local part
            return {
                "valid": False,
                "reason": "Invalid email format",
                "field": "email"
            }
        
        if len(email.split('@')) > 1 and '..' in email.split('@')[1]:  # Consecutive dots in domain part
            return {
                "valid": False,
                "reason": "Invalid email format",
                "field": "email"
            }
        
        if email.startswith('.') or email.endswith('.'):
            return {
                "valid": False,
                "reason": "Invalid email format",
                "field": "email"
            }
        
        return {"valid": True, "field": "email"}
    
    def detect_sql_injection(self, input_string: str) -> bool:
        """Detect SQL injection attempts in input string"""
        if not isinstance(input_string, str):
            return False
        
        input_lower = input_string.lower()
        
        # Check SQL injection patterns
        for pattern in self.sql_regex:
            if pattern.search(input_lower):
                return True
        
        return False
    
    def detect_xss_attack(self, input_string: str) -> bool:
        """Detect XSS attack attempts in input string"""
        if not isinstance(input_string, str):
            return False
        
        input_lower = input_string.lower()
        
        # Check XSS patterns
        for pattern in self.xss_regex:
            if pattern.search(input_lower):
                return True
        
        return False
    
    def detect_command_injection(self, input_string: str) -> bool:
        """Detect command injection attempts in input string"""
        if not isinstance(input_string, str):
            return False
        
        input_lower = input_string.lower()
        
        # Check command injection patterns
        for pattern in self.cmd_regex:
            if pattern.search(input_lower):
                return True
        
        return False
    
    def sanitize_html_input(self, input_string: str) -> str:
        """Sanitize HTML input to prevent XSS"""
        # Allow only safe HTML tags and attributes
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}
        
        cleaned = bleach.clean(input_string, tags=allowed_tags, attributes=allowed_attributes)
        return Markup(cleaned)
    
    def _log_security_event(self, event_type: str, field_name: str, pattern: str):
        """Log security events for monitoring"""
        security_event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "field_name": field_name,
            "pattern": pattern,
            "ip_address": request.remote_addr if request else "unknown",
            "user_agent": request.headers.get('User-Agent', 'unknown') if request else "unknown",
            "user_id": getattr(request, 'user', {}).get('id', 'anonymous') if request else "unknown"
        }
        
        logger.warning(f"Security event detected: {json.dumps(security_event)}")
        
        # Store in security events table if available
        try:
            if hasattr(current_app, 'db'):
                from backend.models.security_models import SecurityEvent
                security_event_record = SecurityEvent(
                    id=security_event["event_id"],
                    event_type=event_type,
                    field_name=field_name,
                    pattern=pattern,
                    ip_address=security_event["ip_address"],
                    user_agent=security_event["user_agent"],
                    user_id=security_event["user_id"],
                    timestamp=datetime.utcnow()
                )
                current_app.db.session.add(security_event_record)
                current_app.db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log security event to database: {e}")

# Security decorator for assessment endpoints
def validate_assessment_input(f):
    """Decorator to validate assessment input data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        validator = SecurityValidator()
        
        # Validate JSON payload
        if request.is_json:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON data"}), 400
            
            # Validate assessment data
            validation_result = validator.validate_assessment_data(data)
            if not validation_result["valid"]:
                # Log security event
                if "errors" in validation_result:
                    for error in validation_result["errors"]:
                        if "attack_type" in error:
                            validator._log_security_event(
                                f"{error['attack_type']}_attempt", 
                                error.get("field", "unknown"),
                                "validation_failure"
                            )
                
                return jsonify({
                    "error": "Invalid input detected",
                    "message": "Please check your input and try again"
                }), 400
            
            # Replace request data with sanitized data
            request.validated_data = validation_result["sanitized_data"]
        
        return f(*args, **kwargs)
    return decorated_function

# Parameterized query enforcement
class SecureAssessmentDB:
    """Secure database operations for assessments"""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def create_user_assessment(self, user_id: str, assessment_id: str, responses: dict):
        """Create user assessment using parameterized queries"""
        from sqlalchemy import text
        
        query = text("""
            INSERT INTO user_assessments (id, user_id, assessment_id, responses_json, created_at, is_complete)
            VALUES (:id, :user_id, :assessment_id, :responses, NOW(), :is_complete)
        """)
        
        return self.db_session.execute(query, {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'assessment_id': assessment_id, 
            'responses': json.dumps(responses),
            'is_complete': True
        })
    
    def get_assessment_by_type(self, assessment_type: str):
        """Get assessment by type using parameterized query"""
        from sqlalchemy import text
        
        query = text("""
            SELECT * FROM assessments 
            WHERE type = :assessment_type AND is_active = :is_active
        """)
        
        return self.db_session.execute(query, {
            'assessment_type': assessment_type,
            'is_active': True
        }).fetchone()
    
    def get_user_assessment_count(self, user_id: str, assessment_id: str):
        """Get user assessment count using parameterized query"""
        from sqlalchemy import text
        
        query = text("""
            SELECT COUNT(*) as count FROM user_assessments 
            WHERE user_id = :user_id AND assessment_id = :assessment_id
        """)
        
        result = self.db_session.execute(query, {
            'user_id': user_id,
            'assessment_id': assessment_id
        }).fetchone()
        
        return result.count if result else 0

# Rate limiting for assessment endpoints
def rate_limit_assessment(limit: int = 10, window: int = 3600):
    """Rate limiting decorator for assessment endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user identifier
            user_id = getattr(request, 'user', {}).get('id', 'anonymous')
            ip_address = request.remote_addr
            
            # Create cache key
            cache_key = f"assessment_rate_limit:{user_id}:{ip_address}:{f.__name__}"
            
            # Check rate limit (in production, use Redis)
            current_count = getattr(current_app, '_assessment_rate_limit_cache', {}).get(cache_key, 0)
            if current_count >= limit:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {limit} assessment requests per {window//3600} hour(s)',
                    'retry_after': window
                }), 429
            
            # Increment counter
            if not hasattr(current_app, '_assessment_rate_limit_cache'):
                current_app._assessment_rate_limit_cache = {}
            current_app._assessment_rate_limit_cache[cache_key] = current_count + 1
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# HTML sanitization for assessment content
def sanitize_assessment_content(content: str) -> str:
    """Sanitize assessment content to prevent XSS"""
    # Allow only safe HTML tags for assessment content
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    allowed_attributes = {'class': []}
    
    cleaned = bleach.clean(content, tags=allowed_tags, attributes=allowed_attributes)
    return Markup(cleaned)

# Security headers for assessment endpoints
def add_assessment_security_headers(response):
    """Add security headers specific to assessment endpoints"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response
