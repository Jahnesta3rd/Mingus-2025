"""
Banking Security Middleware

This module provides security middleware for handling banking data requests,
including request validation, rate limiting, IP filtering, and security headers.
"""

import logging
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
import re
from functools import wraps
from flask import request, Response, g, current_app
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, TooManyRequests
import redis
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.security.banking_compliance import BankingComplianceService, AuditEventType
from backend.models.user_models import User
from backend.models.bank_account_models import BankAccount

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different endpoints"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    window_size: int = 60  # seconds


@dataclass
class SecurityHeaders:
    """Security headers configuration"""
    content_security_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    x_xss_protection: str = "1; mode=block"
    strict_transport_security: str = "max-age=31536000; includeSubDomains"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"


class BankingSecurityMiddleware:
    """Security middleware for banking data handling"""
    
    def __init__(self, db_session: Session, compliance_service: BankingComplianceService):
        self.db = db_session
        self.compliance_service = compliance_service
        self.rate_limit_config = RateLimitConfig()
        self.security_headers = SecurityHeaders()
        
        # Initialize Redis for rate limiting (if available)
        try:
            self.redis_client = redis.Redis(
                host=current_app.config.get('REDIS_HOST', 'localhost'),
                port=current_app.config.get('REDIS_PORT', 6379),
                db=current_app.config.get('REDIS_DB', 0),
                decode_responses=True
            )
            self.redis_available = True
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
            self.redis_available = False
            self.rate_limit_cache = {}
    
    def require_security_level(self, security_level: SecurityLevel):
        """Decorator to require specific security level"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Validate security level
                if not self._validate_security_level(security_level):
                    raise Forbidden("Insufficient security level")
                
                # Apply security checks
                self._apply_security_checks(security_level)
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def _validate_security_level(self, required_level: SecurityLevel) -> bool:
        """Validate if current request meets security level requirements"""
        try:
            # Get user's security level (in real implementation, this would be based on user permissions)
            user_security_level = self._get_user_security_level()
            
            # Security level hierarchy
            level_hierarchy = {
                SecurityLevel.LOW: 1,
                SecurityLevel.MEDIUM: 2,
                SecurityLevel.HIGH: 3,
                SecurityLevel.CRITICAL: 4
            }
            
            return level_hierarchy.get(user_security_level, 0) >= level_hierarchy.get(required_level, 0)
            
        except Exception as e:
            logger.error(f"Error validating security level: {e}")
            return False
    
    def _get_user_security_level(self) -> SecurityLevel:
        """Get user's security level based on authentication and permissions"""
        try:
            # In a real implementation, this would check user roles, MFA status, etc.
            if hasattr(g, 'user') and g.user:
                # Check if user has MFA enabled
                if hasattr(g.user, 'mfa_enabled') and g.user.mfa_enabled:
                    return SecurityLevel.HIGH
                else:
                    return SecurityLevel.MEDIUM
            else:
                return SecurityLevel.LOW
                
        except Exception as e:
            logger.error(f"Error getting user security level: {e}")
            return SecurityLevel.LOW
    
    def _apply_security_checks(self, security_level: SecurityLevel):
        """Apply security checks based on level"""
        try:
            # Rate limiting
            if not self._check_rate_limit():
                raise TooManyRequests("Rate limit exceeded")
            
            # IP filtering
            if not self._check_ip_whitelist():
                raise Forbidden("IP not in whitelist")
            
            # Request validation
            if not self._validate_request():
                raise BadRequest("Invalid request")
            
            # Additional checks for higher security levels
            if security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                if not self._check_session_validity():
                    raise Unauthorized("Invalid session")
                
                if not self._check_request_signature():
                    raise Unauthorized("Invalid request signature")
            
            # Critical level checks
            if security_level == SecurityLevel.CRITICAL:
                if not self._check_encryption_headers():
                    raise BadRequest("Encryption headers required")
                
                if not self._check_audit_trail():
                    raise Forbidden("Audit trail required")
                    
        except Exception as e:
            logger.error(f"Error applying security checks: {e}")
            raise
    
    def _check_rate_limit(self) -> bool:
        """Check rate limiting for current request"""
        try:
            if not self.rate_limit_config:
                return True
            
            # Get client identifier
            client_id = self._get_client_identifier()
            
            # Check minute limit
            minute_key = f"rate_limit:{client_id}:minute:{int(time.time() // 60)}"
            if not self._check_rate_limit_window(minute_key, self.rate_limit_config.requests_per_minute):
                return False
            
            # Check hour limit
            hour_key = f"rate_limit:{client_id}:hour:{int(time.time() // 3600)}"
            if not self._check_rate_limit_window(hour_key, self.rate_limit_config.requests_per_hour):
                return False
            
            # Check day limit
            day_key = f"rate_limit:{client_id}:day:{int(time.time() // 86400)}"
            if not self._check_rate_limit_window(day_key, self.rate_limit_config.requests_per_day):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow request if rate limiting fails
    
    def _check_rate_limit_window(self, key: str, limit: int) -> bool:
        """Check rate limit for a specific time window"""
        try:
            if self.redis_available:
                current_count = self.redis_client.get(key)
                if current_count and int(current_count) >= limit:
                    return False
                
                # Increment counter
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, 60)  # Expire in 60 seconds
                pipe.execute()
            else:
                # Fallback to in-memory cache
                current_time = time.time()
                if key not in self.rate_limit_cache:
                    self.rate_limit_cache[key] = {'count': 0, 'reset_time': current_time + 60}
                
                window_data = self.rate_limit_cache[key]
                if current_time > window_data['reset_time']:
                    window_data['count'] = 0
                    window_data['reset_time'] = current_time + 60
                
                if window_data['count'] >= limit:
                    return False
                
                window_data['count'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit window: {e}")
            return True
    
    def _get_client_identifier(self) -> str:
        """Get unique client identifier for rate limiting"""
        try:
            # Use IP address and user ID if available
            ip_address = request.remote_addr or 'unknown'
            user_id = getattr(g, 'user_id', None) or 'anonymous'
            
            return f"{ip_address}:{user_id}"
            
        except Exception as e:
            logger.error(f"Error getting client identifier: {e}")
            return 'unknown'
    
    def _check_ip_whitelist(self) -> bool:
        """Check if IP is in whitelist"""
        try:
            # Get IP whitelist from configuration
            ip_whitelist = current_app.config.get('IP_WHITELIST', [])
            
            if not ip_whitelist:
                return True  # No whitelist configured
            
            client_ip = request.remote_addr
            return client_ip in ip_whitelist
            
        except Exception as e:
            logger.error(f"Error checking IP whitelist: {e}")
            return True
    
    def _validate_request(self) -> bool:
        """Validate request format and content"""
        try:
            # Check request method
            if request.method not in ['GET', 'POST', 'PUT', 'DELETE']:
                return False
            
            # Check content type for POST/PUT requests
            if request.method in ['POST', 'PUT']:
                content_type = request.headers.get('Content-Type', '')
                if not content_type.startswith('application/json'):
                    return False
            
            # Validate JSON for POST/PUT requests
            if request.method in ['POST', 'PUT'] and request.is_json:
                try:
                    json.loads(request.get_data(as_text=True))
                except json.JSONDecodeError:
                    return False
            
            # Check for required headers
            required_headers = ['User-Agent']
            for header in required_headers:
                if not request.headers.get(header):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating request: {e}")
            return False
    
    def _check_session_validity(self) -> bool:
        """Check if user session is valid"""
        try:
            if not hasattr(g, 'user') or not g.user:
                return False
            
            # Check session timeout
            session_timeout = current_app.config.get('SESSION_TIMEOUT_MINUTES', 30)
            if hasattr(g.user, 'last_activity'):
                time_diff = datetime.utcnow() - g.user.last_activity
                if time_diff.total_seconds() > (session_timeout * 60):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking session validity: {e}")
            return False
    
    def _check_request_signature(self) -> bool:
        """Check request signature for high-security endpoints"""
        try:
            # Get signature from headers
            signature = request.headers.get('X-Request-Signature')
            timestamp = request.headers.get('X-Request-Timestamp')
            
            if not signature or not timestamp:
                return False
            
            # Validate timestamp (within 5 minutes)
            try:
                timestamp_int = int(timestamp)
                current_time = int(time.time())
                if abs(current_time - timestamp_int) > 300:  # 5 minutes
                    return False
            except ValueError:
                return False
            
            # Verify signature
            secret = current_app.config.get('REQUEST_SIGNATURE_SECRET')
            if not secret:
                return False
            
            # Create expected signature
            message = f"{timestamp}:{request.path}:{request.get_data(as_text=True)}"
            expected_signature = hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error checking request signature: {e}")
            return False
    
    def _check_encryption_headers(self) -> bool:
        """Check for encryption headers in critical requests"""
        try:
            # Check for encryption headers
            encryption_header = request.headers.get('X-Encryption-Algorithm')
            if not encryption_header:
                return False
            
            # Validate encryption algorithm
            valid_algorithms = ['AES-256-GCM', 'AES-256-CBC']
            if encryption_header not in valid_algorithms:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking encryption headers: {e}")
            return False
    
    def _check_audit_trail(self) -> bool:
        """Check if audit trail is properly configured"""
        try:
            # Check if audit logging is enabled
            audit_enabled = current_app.config.get('AUDIT_LOGGING_ENABLED', True)
            if not audit_enabled:
                return False
            
            # Check if user has audit permissions
            if hasattr(g, 'user') and g.user:
                # In real implementation, check user's audit permissions
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking audit trail: {e}")
            return False
    
    def add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        try:
            # Content Security Policy
            response.headers['Content-Security-Policy'] = self.security_headers.content_security_policy
            
            # X-Frame-Options
            response.headers['X-Frame-Options'] = self.security_headers.x_frame_options
            
            # X-Content-Type-Options
            response.headers['X-Content-Type-Options'] = self.security_headers.x_content_type_options
            
            # X-XSS-Protection
            response.headers['X-XSS-Protection'] = self.security_headers.x_xss_protection
            
            # Strict-Transport-Security
            response.headers['Strict-Transport-Security'] = self.security_headers.strict_transport_security
            
            # Referrer-Policy
            response.headers['Referrer-Policy'] = self.security_headers.referrer_policy
            
            # Permissions-Policy
            response.headers['Permissions-Policy'] = self.security_headers.permissions_policy
            
            # Additional banking-specific headers
            response.headers['X-Banking-Security'] = 'enabled'
            response.headers['X-Content-Encryption'] = 'AES-256-GCM'
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding security headers: {e}")
            return response
    
    def validate_banking_request(self, user_id: str, bank_account_id: str = None) -> bool:
        """Validate banking-specific request requirements"""
        try:
            # Check if user is authenticated
            if not user_id:
                return False
            
            # Check if user exists and is active
            user = self.db.query(User).filter(
                and_(
                    User.id == user_id,
                    User.is_active == True
                )
            ).first()
            
            if not user:
                return False
            
            # If bank account ID is provided, validate access
            if bank_account_id:
                return self.compliance_service.validate_bank_data_access(
                    user_id=user_id,
                    bank_account_id=bank_account_id,
                    access_type='api_request',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating banking request: {e}")
            return False
    
    def sanitize_banking_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize banking data in response"""
        try:
            return self.compliance_service.sanitize_bank_data(data)
        except Exception as e:
            logger.error(f"Error sanitizing banking response: {e}")
            return data
    
    def log_banking_access(self, user_id: str, resource_type: str, resource_id: str = None, 
                          access_type: str = 'read'):
        """Log banking data access for audit"""
        try:
            self.compliance_service._log_audit_event(
                user_id=user_id,
                event_type=AuditEventType.DATA_ACCESS,
                event_description=f"{access_type} access to {resource_type}",
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                metadata={'access_type': access_type, 'method': request.method}
            )
        except Exception as e:
            logger.error(f"Error logging banking access: {e}")
    
    def validate_plaid_webhook(self, body: str, signature: str, timestamp: str) -> bool:
        """Validate Plaid webhook authenticity"""
        try:
            return self.compliance_service.verify_plaid_webhook_signature(
                body=body,
                signature=signature,
                timestamp=timestamp
            )
        except Exception as e:
            logger.error(f"Error validating Plaid webhook: {e}")
            return False
    
    def encrypt_sensitive_response(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Encrypt sensitive data in response"""
        try:
            encrypted_data = data.copy()
            
            # Encrypt sensitive fields
            if data_type in ['bank_account', 'transaction', 'balance']:
                sensitive_fields = ['account_number', 'routing_number', 'access_token']
                
                for field in sensitive_fields:
                    if field in encrypted_data:
                        encrypted_data[field] = self.compliance_service.encrypt_sensitive_data(
                            str(encrypted_data[field]), field
                        )
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Error encrypting sensitive response: {e}")
            return data
    
    def get_security_context(self) -> Dict[str, Any]:
        """Get current security context"""
        try:
            return {
                'user_id': getattr(g, 'user_id', None),
                'security_level': self._get_user_security_level().value,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'request_method': request.method,
                'request_path': request.path,
                'timestamp': datetime.utcnow().isoformat(),
                'rate_limit_status': self._get_rate_limit_status()
            }
        except Exception as e:
            logger.error(f"Error getting security context: {e}")
            return {}
    
    def _get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            client_id = self._get_client_identifier()
            
            if self.redis_available:
                minute_key = f"rate_limit:{client_id}:minute:{int(time.time() // 60)}"
                hour_key = f"rate_limit:{client_id}:hour:{int(time.time() // 3600)}"
                
                minute_count = int(self.redis_client.get(minute_key) or 0)
                hour_count = int(self.redis_client.get(hour_key) or 0)
            else:
                minute_count = 0
                hour_count = 0
            
            return {
                'minute_requests': minute_count,
                'hour_requests': hour_count,
                'minute_limit': self.rate_limit_config.requests_per_minute,
                'hour_limit': self.rate_limit_config.requests_per_hour
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {} 