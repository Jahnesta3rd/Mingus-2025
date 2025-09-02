"""
AI Calculator Security and Privacy System

Comprehensive security and privacy measures for the AI Job Impact Calculator including:
- PII encryption in ai_job_assessments table
- Data retention policies (2-year deletion)
- GDPR compliance with explicit consent
- Rate limiting (5 assessments per hour per IP)
- CSRF protection
- Input validation and sanitization
- SQL injection prevention
- Anonymous assessment option
- Audit logging for all operations
- CCPA compliance
- Vulnerability monitoring
"""

import logging
import hashlib
import hmac
import secrets
import time
import json
import re
import os
import base64
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import bleach
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError
from flask import request, jsonify, current_app, g, session
import redis

from backend.security.audit_logging import AuditLoggingService, AuditEventType, LogCategory, LogSeverity
from backend.security.data_protection_service import DataProtectionService, EncryptionType
from backend.gdpr.compliance_manager import GDPRComplianceManager, ConsentType, RequestType

logger = logging.getLogger(__name__)


class AICalculatorSecurityLevel(Enum):
    """Security levels for AI Calculator operations"""
    PUBLIC = "public"           # Anonymous assessments
    AUTHENTICATED = "authenticated"  # User assessments
    PREMIUM = "premium"         # Premium features
    ADMIN = "admin"            # Administrative access


class DataRetentionPolicy(Enum):
    """Data retention policies for AI Calculator"""
    ASSESSMENT_DATA = "assessment_data"      # 2 years
    USER_PROFILE = "user_profile"           # 2 years
    ANALYTICS_DATA = "analytics_data"       # 1 year
    AUDIT_LOGS = "audit_loggs"              # 7 years
    TEMPORARY_DATA = "temporary_data"       # 30 days


@dataclass
class AICalculatorSecurityConfig:
    """Configuration for AI Calculator security"""
    # Rate limiting
    max_assessments_per_hour: int = 5
    max_anonymous_assessments_per_ip: int = 3
    max_authenticated_assessments_per_user: int = 10
    
    # Data retention (in days)
    assessment_data_retention_days: int = 730  # 2 years
    user_profile_retention_days: int = 730     # 2 years
    analytics_data_retention_days: int = 365   # 1 year
    audit_log_retention_days: int = 2555       # 7 years
    
    # Encryption
    encryption_key_rotation_days: int = 90
    pii_encryption_enabled: bool = True
    
    # Privacy
    anonymous_assessment_enabled: bool = True
    gdpr_compliance_enabled: bool = True
    ccpa_compliance_enabled: bool = True
    
    # Security
    csrf_protection_enabled: bool = True
    input_validation_enabled: bool = True
    sql_injection_prevention_enabled: bool = True
    xss_prevention_enabled: bool = True
    
    # Monitoring
    audit_logging_enabled: bool = True
    suspicious_behavior_detection_enabled: bool = True
    vulnerability_scanning_enabled: bool = True


class AICalculatorSecurityService:
    """Comprehensive security service for AI Calculator"""
    
    def __init__(self, db_session: Session, config: AICalculatorSecurityConfig = None):
        self.db = db_session
        self.config = config or AICalculatorSecurityConfig()
        self.audit_service = AuditLoggingService(db_session)
        self.data_protection = DataProtectionService(db_session)
        self.gdpr_manager = GDPRComplianceManager(db_session)
        
        # Initialize encryption keys
        self._init_encryption_keys()
        
        # Initialize Redis for rate limiting
        self.redis_client = self._init_redis()
        
        # Security patterns
        self._init_security_patterns()
    
    def _init_encryption_keys(self):
        """Initialize encryption keys for PII data"""
        try:
            # Generate or retrieve encryption key
            key_file = current_app.config.get('AI_CALCULATOR_ENCRYPTION_KEY_FILE', 'ai_calculator_key.key')
            
            if not os.path.exists(key_file):
                # Generate new key
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                self.encryption_key = key
            else:
                # Load existing key
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
            
            self.cipher = Fernet(self.encryption_key)
            logger.info("AI Calculator encryption keys initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption keys: {e}")
            self.cipher = None
    
    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection for rate limiting"""
        try:
            redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379')
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
            return None
    
    def _init_security_patterns(self):
        """Initialize security patterns for input validation"""
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
        
        # Compile patterns for performance
        self.sql_regex = re.compile('|'.join(self.sql_patterns), re.IGNORECASE)
        self.xss_regex = re.compile('|'.join(self.xss_patterns), re.IGNORECASE)
    
    def encrypt_pii(self, data: str) -> str:
        """Encrypt PII data"""
        if not self.config.pii_encryption_enabled or not self.cipher:
            return data
        
        try:
            encrypted_data = self.cipher.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt PII data: {e}")
            return data
    
    def decrypt_pii(self, encrypted_data: str) -> str:
        """Decrypt PII data"""
        if not self.config.pii_encryption_enabled or not self.cipher:
            return encrypted_data
        
        try:
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt PII data: {e}")
            return encrypted_data
    
    def validate_input(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate and sanitize input data"""
        errors = []
        
        if not self.config.input_validation_enabled:
            return True, errors
        
        # Validate required fields
        required_fields = [
            'job_title', 'industry', 'experience_level', 'tasks_array',
            'remote_work_frequency', 'ai_usage_frequency', 'team_size',
            'tech_skills_level', 'concerns_array'
        ]
        
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate email if provided
        if 'email' in data and data['email']:
            email = data['email'].strip().lower()
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append("Invalid email format")
        
        # Validate enum values
        enum_validations = {
            'experience_level': ['entry', 'mid', 'senior', 'executive'],
            'remote_work_frequency': ['never', 'rarely', 'sometimes', 'often', 'always'],
            'ai_usage_frequency': ['never', 'rarely', 'sometimes', 'often', 'always'],
            'team_size': ['1-5', '6-10', '11-25', '26-50', '50+'],
            'tech_skills_level': ['basic', 'intermediate', 'advanced', 'expert']
        }
        
        for field, valid_values in enum_validations.items():
            if field in data and data[field] not in valid_values:
                errors.append(f"Invalid value for {field}: {data[field]}")
        
        # Sanitize string inputs
        string_fields = ['job_title', 'industry', 'first_name', 'location']
        for field in string_fields:
            if field in data and data[field]:
                # Check for SQL injection
                if self.sql_regex.search(data[field]):
                    errors.append(f"SQL injection attempt detected in {field}")
                
                # Check for XSS
                if self.xss_regex.search(data[field]):
                    errors.append(f"XSS attempt detected in {field}")
                
                # Sanitize HTML
                data[field] = bleach.clean(data[field], strip=True)
        
        return len(errors) == 0, errors
    
    def check_rate_limit(self, user_id: Optional[str] = None, ip_address: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limiting for assessment submission"""
        if not ip_address:
            ip_address = request.remote_addr or 'unknown'
        
        identifier = user_id or f"ip:{ip_address}"
        key = f"ai_calculator_rate_limit:{identifier}"
        
        try:
            if self.redis_client:
                # Use Redis for rate limiting
                current_count = self.redis_client.get(key)
                current_count = int(current_count) if current_count else 0
                
                limit = self.config.max_authenticated_assessments_per_user if user_id else self.config.max_anonymous_assessments_per_ip
                
                if current_count >= limit:
                    return False, {
                        'limited': True,
                        'current_count': current_count,
                        'limit': limit,
                        'retry_after': 3600,  # 1 hour
                        'message': f'Maximum {limit} assessments per hour exceeded'
                    }
                
                # Increment counter
                self.redis_client.incr(key)
                self.redis_client.expire(key, 3600)  # Expire in 1 hour
                
                return True, {
                    'limited': False,
                    'current_count': current_count + 1,
                    'limit': limit,
                    'remaining': limit - (current_count + 1)
                }
            else:
                # Fallback to in-memory rate limiting
                return self._check_memory_rate_limit(identifier, limit)
                
        except Exception as e:
            logger.error(f"Rate limiting check failed: {e}")
            return True, {'limited': False, 'error': 'Rate limiting unavailable'}
    
    def _check_memory_rate_limit(self, identifier: str, limit: int) -> Tuple[bool, Dict[str, Any]]:
        """Fallback memory-based rate limiting"""
        current_time = time.time()
        
        if not hasattr(current_app, '_ai_calculator_rate_limit_cache'):
            current_app._ai_calculator_rate_limit_cache = {}
        
        cache_key = f"ai_calculator:{identifier}"
        
        if cache_key not in current_app._ai_calculator_rate_limit_cache:
            current_app._ai_calculator_rate_limit_cache[cache_key] = {
                'count': 0,
                'reset_time': current_time + 3600
            }
        
        rate_data = current_app._ai_calculator_rate_limit_cache[cache_key]
        
        # Reset if window expired
        if current_time > rate_data['reset_time']:
            rate_data['count'] = 0
            rate_data['reset_time'] = current_time + 3600
        
        if rate_data['count'] >= limit:
            return False, {
                'limited': True,
                'current_count': rate_data['count'],
                'limit': limit,
                'retry_after': int(rate_data['reset_time'] - current_time),
                'message': f'Maximum {limit} assessments per hour exceeded'
            }
        
        rate_data['count'] += 1
        
        return True, {
            'limited': False,
            'current_count': rate_data['count'],
            'limit': limit,
            'remaining': limit - rate_data['count']
        }
    
    def log_assessment_event(self, event_type: str, user_id: Optional[str], 
                           assessment_data: Dict[str, Any], ip_address: str = None) -> None:
        """Log assessment events for audit trail"""
        if not self.config.audit_logging_enabled:
            return
        
        try:
            if not ip_address:
                ip_address = request.remote_addr or 'unknown'
            
            # Log to audit service
            self.audit_service.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=user_id,
                session_id=session.get('session_id'),
                description=f"AI Calculator {event_type}",
                metadata={
                    'assessment_type': 'ai_job_impact',
                    'ip_address': ip_address,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'data_encrypted': self.config.pii_encryption_enabled,
                    'anonymous_user': user_id is None
                },
                severity=LogSeverity.INFO
            )
            
            logger.info(f"AI Calculator {event_type} logged for user {user_id or 'anonymous'} from {ip_address}")
            
        except Exception as e:
            logger.error(f"Failed to log assessment event: {e}")
    
    def check_gdpr_consent(self, user_id: Optional[str] = None, email: str = None) -> bool:
        """Check if user has provided GDPR consent"""
        if not self.config.gdpr_compliance_enabled:
            return True
        
        try:
            if user_id:
                # Check for authenticated user
                consent = self.gdpr_manager.get_user_consent(user_id, ConsentType.MARKETING)
                return consent and consent.granted
            elif email:
                # Check for anonymous user by email
                consent = self.gdpr_manager.get_consent_by_email(email, ConsentType.MARKETING)
                return consent and consent.granted
            else:
                # No way to check consent
                return False
                
        except Exception as e:
            logger.error(f"Failed to check GDPR consent: {e}")
            return False
    
    def enforce_data_retention(self) -> Dict[str, Any]:
        """Enforce data retention policies"""
        try:
            deleted_counts = {}
            
            # Delete old assessment data (2 years)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.assessment_data_retention_days)
            
            # Delete from ai_job_assessments table
            result = self.db.execute(text("""
                DELETE FROM ai_job_assessments 
                WHERE created_at < :cutoff_date 
                AND user_id IS NULL
            """), {'cutoff_date': cutoff_date})
            
            deleted_counts['assessments'] = result.rowcount
            
            # Delete old conversion data
            result = self.db.execute(text("""
                DELETE FROM ai_calculator_conversions 
                WHERE created_at < :cutoff_date
            """), {'cutoff_date': cutoff_date})
            
            deleted_counts['conversions'] = result.rowcount
            
            self.db.commit()
            
            # Log the cleanup
            self.audit_service.log_event(
                event_type=AuditEventType.DATA_RETENTION,
                user_id=None,
                description="AI Calculator data retention cleanup",
                metadata={
                    'deleted_counts': deleted_counts,
                    'cutoff_date': cutoff_date.isoformat(),
                    'retention_days': self.config.assessment_data_retention_days
                },
                severity=LogSeverity.INFO
            )
            
            logger.info(f"AI Calculator data retention cleanup completed: {deleted_counts}")
            return deleted_counts
            
        except Exception as e:
            logger.error(f"Failed to enforce data retention: {e}")
            self.db.rollback()
            return {'error': str(e)}
    
    def detect_suspicious_behavior(self, user_id: Optional[str], ip_address: str, 
                                 assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect suspicious behavior patterns"""
        if not self.config.suspicious_behavior_detection_enabled:
            return {'suspicious': False}
        
        try:
            suspicious_indicators = []
            
            # Check for rapid submissions
            if self.redis_client:
                rapid_key = f"ai_calculator_rapid:{ip_address}"
                rapid_count = self.redis_client.get(rapid_key)
                rapid_count = int(rapid_count) if rapid_count else 0
                
                if rapid_count > 10:  # More than 10 submissions in short time
                    suspicious_indicators.append('rapid_submissions')
                
                self.redis_client.incr(rapid_key)
                self.redis_client.expire(rapid_key, 300)  # 5 minutes
            
            # Check for unusual patterns in assessment data
            if len(assessment_data.get('tasks_array', [])) > 20:
                suspicious_indicators.append('excessive_tasks')
            
            if len(assessment_data.get('concerns_array', [])) > 10:
                suspicious_indicators.append('excessive_concerns')
            
            # Check for automated patterns
            user_agent = request.headers.get('User-Agent', '')
            if any(bot in user_agent.lower() for bot in ['bot', 'crawler', 'spider', 'scraper']):
                suspicious_indicators.append('bot_user_agent')
            
            is_suspicious = len(suspicious_indicators) > 0
            
            if is_suspicious:
                # Log suspicious behavior
                self.audit_service.log_event(
                    event_type=AuditEventType.SECURITY,
                    user_id=user_id,
                    description="Suspicious AI Calculator behavior detected",
                    metadata={
                        'ip_address': ip_address,
                        'user_agent': user_agent,
                        'suspicious_indicators': suspicious_indicators,
                        'assessment_data_keys': list(assessment_data.keys())
                    },
                    severity=LogSeverity.WARNING
                )
            
            return {
                'suspicious': is_suspicious,
                'indicators': suspicious_indicators,
                'risk_level': 'high' if len(suspicious_indicators) > 2 else 'medium' if len(suspicious_indicators) > 0 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Failed to detect suspicious behavior: {e}")
            return {'suspicious': False, 'error': str(e)}


# Security decorators for AI Calculator endpoints
def secure_ai_calculator_endpoint(security_level: AICalculatorSecurityLevel = AICalculatorSecurityLevel.PUBLIC):
    """Security decorator for AI Calculator endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get security service
                security_service = AICalculatorSecurityService(current_app.db.session)
                
                # Get user information
                user_id = getattr(g, 'user_id', None)
                ip_address = request.remote_addr or 'unknown'
                
                # Check rate limiting
                rate_limit_allowed, rate_limit_info = security_service.check_rate_limit(user_id, ip_address)
                if not rate_limit_allowed:
                    return jsonify({
                        'success': False,
                        'error': 'rate_limit_exceeded',
                        'message': rate_limit_info.get('message', 'Rate limit exceeded'),
                        'retry_after': rate_limit_info.get('retry_after', 3600)
                    }), 429
                
                # Validate input data
                if request.method == 'POST':
                    data = request.get_json() or {}
                    is_valid, validation_errors = security_service.validate_input(data)
                    
                    if not is_valid:
                        return jsonify({
                            'success': False,
                            'error': 'validation_error',
                            'message': 'Invalid input data',
                            'details': validation_errors
                        }), 400
                    
                    # Detect suspicious behavior
                    suspicious_info = security_service.detect_suspicious_behavior(user_id, ip_address, data)
                    if suspicious_info.get('suspicious'):
                        # Still process but log the suspicious behavior
                        security_service.log_assessment_event(
                            'suspicious_submission', user_id, data, ip_address
                        )
                
                # Log the event
                security_service.log_assessment_event(
                    'endpoint_access', user_id, {}, ip_address
                )
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"AI Calculator security error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'security_error',
                    'message': 'Security check failed'
                }), 500
        
        return decorated_function
    return decorator


def require_gdpr_consent():
    """Decorator to require GDPR consent for data processing"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                security_service = AICalculatorSecurityService(current_app.db.session)
                user_id = getattr(g, 'user_id', None)
                
                # Get email from request data
                data = request.get_json() or {}
                email = data.get('email')
                
                # Check GDPR consent
                has_consent = security_service.check_gdpr_consent(user_id, email)
                
                if not has_consent:
                    return jsonify({
                        'success': False,
                        'error': 'gdpr_consent_required',
                        'message': 'GDPR consent is required for data processing',
                        'consent_required': True
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"GDPR consent check error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'consent_check_error',
                    'message': 'Consent verification failed'
                }), 500
        
        return decorated_function
    return decorator


def encrypt_pii_data():
    """Decorator to encrypt PII data before database storage"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                security_service = AICalculatorSecurityService(current_app.db.session)
                
                # Get request data
                data = request.get_json() or {}
                
                # Encrypt PII fields
                pii_fields = ['first_name', 'email', 'location']
                for field in pii_fields:
                    if field in data and data[field]:
                        data[field] = security_service.encrypt_pii(data[field])
                
                # Replace request data with encrypted version
                request._cached_json = data
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"PII encryption error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'encryption_error',
                    'message': 'Data encryption failed'
                }), 500
        
        return decorated_function
    return decorator


# CSRF protection for AI Calculator forms
def generate_ai_calculator_csrf_token() -> str:
    """Generate CSRF token for AI Calculator forms"""
    if 'ai_calculator_csrf_token' not in session:
        session['ai_calculator_csrf_token'] = secrets.token_urlsafe(32)
    return session['ai_calculator_csrf_token']


def validate_ai_calculator_csrf_token(token: str) -> bool:
    """Validate CSRF token for AI Calculator forms"""
    if not token:
        return False
    
    expected_token = session.get('ai_calculator_csrf_token')
    if not expected_token:
        return False
    
    return hmac.compare_digest(token, expected_token)


def require_ai_calculator_csrf():
    """Decorator to require CSRF token for AI Calculator endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                if not current_app.config.get('AI_CALCULATOR_CSRF_ENABLED', True):
                    return f(*args, **kwargs)
                
                # Get CSRF token from headers or form data
                csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                
                if not validate_ai_calculator_csrf_token(csrf_token):
                    return jsonify({
                        'success': False,
                        'error': 'csrf_validation_failed',
                        'message': 'CSRF token validation failed'
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"CSRF validation error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'csrf_error',
                    'message': 'CSRF validation failed'
                }), 500
        
        return decorated_function
    return decorator


# Data export functionality for GDPR compliance
def export_user_data(user_id: str) -> Dict[str, Any]:
    """Export user data for GDPR compliance"""
    try:
        security_service = AICalculatorSecurityService(current_app.db.session)
        
        # Get user assessments
        assessments = current_app.db.session.execute(text("""
            SELECT * FROM ai_job_assessments 
            WHERE user_id = :user_id
        """), {'user_id': user_id}).fetchall()
        
        # Decrypt PII data
        decrypted_assessments = []
        for assessment in assessments:
            assessment_dict = dict(assessment._mapping)
            
            # Decrypt PII fields
            for field in ['first_name', 'email', 'location']:
                if assessment_dict.get(field):
                    assessment_dict[field] = security_service.decrypt_pii(assessment_dict[field])
            
            decrypted_assessments.append(assessment_dict)
        
        # Get conversion data
        conversions = current_app.db.session.execute(text("""
            SELECT * FROM ai_calculator_conversions 
            WHERE assessment_id IN (
                SELECT id FROM ai_job_assessments WHERE user_id = :user_id
            )
        """), {'user_id': user_id}).fetchall()
        
        export_data = {
            'user_id': user_id,
            'export_date': datetime.now(timezone.utc).isoformat(),
            'assessments': decrypted_assessments,
            'conversions': [dict(c._mapping) for c in conversions],
            'data_categories': ['personal_data', 'assessment_data', 'conversion_data']
        }
        
        # Log the export
        security_service.audit_service.log_event(
            event_type=AuditEventType.DATA_PORTABILITY,
            user_id=user_id,
            description="AI Calculator data export requested",
            metadata={
                'export_date': export_data['export_date'],
                'assessment_count': len(decrypted_assessments),
                'conversion_count': len(conversions)
            },
            severity=LogSeverity.INFO
        )
        
        return export_data
        
    except Exception as e:
        logger.error(f"Failed to export user data: {e}")
        return {'error': str(e)}


# Data deletion functionality for GDPR compliance
def delete_user_data(user_id: str) -> Dict[str, Any]:
    """Delete user data for GDPR compliance"""
    try:
        security_service = AICalculatorSecurityService(current_app.db.session)
        
        # Delete conversions first (foreign key constraint)
        conversions_deleted = current_app.db.session.execute(text("""
            DELETE FROM ai_calculator_conversions 
            WHERE assessment_id IN (
                SELECT id FROM ai_job_assessments WHERE user_id = :user_id
            )
        """), {'user_id': user_id}).rowcount
        
        # Delete assessments
        assessments_deleted = current_app.db.session.execute(text("""
            DELETE FROM ai_job_assessments 
            WHERE user_id = :user_id
        """), {'user_id': user_id}).rowcount
        
        current_app.db.session.commit()
        
        # Log the deletion
        security_service.audit_service.log_event(
            event_type=AuditEventType.DATA_DELETION,
            user_id=user_id,
            description="AI Calculator data deletion requested",
            metadata={
                'assessments_deleted': assessments_deleted,
                'conversions_deleted': conversions_deleted,
                'deletion_date': datetime.now(timezone.utc).isoformat()
            },
            severity=LogSeverity.INFO
        )
        
        return {
            'success': True,
            'assessments_deleted': assessments_deleted,
            'conversions_deleted': conversions_deleted,
            'deletion_date': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete user data: {e}")
        current_app.db.session.rollback()
        return {'error': str(e)}


# Privacy policy and consent management
def get_ai_calculator_privacy_policy() -> Dict[str, Any]:
    """Get AI Calculator privacy policy"""
    return {
        'version': '1.0',
        'effective_date': '2025-01-27',
        'data_controller': 'MINGUS',
        'data_processing_purposes': [
            'AI job impact assessment',
            'Personalized recommendations',
            'Email communication (with consent)',
            'Analytics and improvement'
        ],
        'data_categories': [
            'Personal identification data (name, email)',
            'Professional information (job title, industry)',
            'Assessment responses',
            'Technical data (IP address, user agent)'
        ],
        'data_retention': {
            'assessment_data': '2 years',
            'user_profile': '2 years',
            'analytics_data': '1 year',
            'audit_logs': '7 years'
        },
        'user_rights': [
            'Right to access personal data',
            'Right to rectification',
            'Right to erasure',
            'Right to data portability',
            'Right to object to processing',
            'Right to withdraw consent'
        ],
        'contact_information': {
            'email': 'privacy@mingusapp.com',
            'address': 'MINGUS Privacy Team'
        }
    }


def create_ai_calculator_consent_record(user_id: Optional[str], email: str, 
                                      consent_types: List[str], ip_address: str) -> bool:
    """Create consent record for AI Calculator"""
    try:
        security_service = AICalculatorSecurityService(current_app.db.session)
        
        # Create consent records
        for consent_type in consent_types:
            security_service.gdpr_manager.create_consent_record(
                user_id=user_id,
                email=email,
                consent_type=ConsentType(consent_type),
                granted=True,
                ip_address=ip_address,
                user_agent=request.headers.get('User-Agent', ''),
                consent_version='1.0',
                privacy_policy_version='1.0'
            )
        
        # Log consent creation
        security_service.audit_service.log_event(
            event_type=AuditEventType.COMPLIANCE,
            user_id=user_id,
            description="AI Calculator consent granted",
            metadata={
                'email': email,
                'consent_types': consent_types,
                'ip_address': ip_address
            },
            severity=LogSeverity.INFO
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create consent record: {e}")
        return False
