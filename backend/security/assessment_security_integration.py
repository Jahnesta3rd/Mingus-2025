"""
Assessment Security Integration
Integrates comprehensive security monitoring with assessment system
"""

import logging
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, jsonify, current_app, g
from sqlalchemy.orm import Session

from backend.security.comprehensive_security_monitor import (
    SecurityMonitor, 
    SecurityEventType, 
    SecuritySeverity,
    AnomalyDetector,
    SecurityMonitoringMiddleware
)
from backend.security.assessment_security import SecurityValidator

logger = logging.getLogger(__name__)

def init_assessment_security(app, db_session=None, redis_client=None):
    """Initialize assessment security integration with Flask app"""
    try:
        # Create security integration instance
        security_integration = AssessmentSecurityIntegration(db_session, redis_client)
        
        # Register security middleware
        app.security_integration = security_integration
        
        # Add security headers middleware
        from backend.security.security_headers import SecurityHeaders
        security_headers = SecurityHeaders()
        app.after_request(security_headers.add_security_headers)
        
        # Add CSRF protection
        from backend.security.csrf_protection import CSRFProtection
        secret_key = app.config.get('SECRET_KEY', 'default-secret-key-for-testing')
        csrf_protection = CSRFProtection(secret_key)
        # Note: CSRF protection is applied via decorators on specific endpoints
        # rather than globally via before_request to avoid conflicts
        
        logger.info("Assessment security integration initialized successfully")
        return security_integration
        
    except Exception as e:
        logger.error(f"Failed to initialize assessment security: {e}")
        raise

class AssessmentSecurityIntegration:
    """Integrates security monitoring with assessment system"""
    
    def __init__(self, db_session: Session, redis_client=None):
        self.db_session = db_session
        self.security_monitor = SecurityMonitor(db_session, redis_client)
        self.anomaly_detector = AnomalyDetector()
        self.security_middleware = SecurityMonitoringMiddleware(
            self.security_monitor, 
            self.anomaly_detector
        )
        self.security_validator = SecurityValidator()
    
    def secure_assessment_endpoint(self, f):
        """Decorator to secure assessment endpoints with comprehensive monitoring"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get user identifier
                user_id = self._get_user_identifier()
                
                # Validate input for security threats
                validation_result = self._validate_assessment_input(request)
                
                if not validation_result['valid']:
                    # Log security event for validation failure
                    self.security_monitor.log_security_event(
                        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                        user_identifier=user_id,
                        details={
                            'validation_errors': validation_result['errors'],
                            'endpoint': request.endpoint,
                            'method': request.method,
                            'ip_address': request.remote_addr
                        },
                        severity=SecuritySeverity.WARNING
                    )
                    
                    return jsonify({
                        'error': 'Invalid input detected',
                        'details': validation_result['errors']
                    }), 400
                
                # Monitor assessment submission
                if request.method == 'POST' and 'assessment_data' in request.json:
                    self.security_middleware.monitor_assessment_submission(
                        user_id, 
                        request.json['assessment_data']
                    )
                
                # Execute the original function
                result = f(*args, **kwargs)
                
                # Log successful assessment completion
                if request.method == 'POST' and 'assessment_data' in request.json:
                    self._log_assessment_completion(user_id, request.json['assessment_data'])
                
                return result
                
            except Exception as e:
                logger.error(f"Error in secure assessment endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        return decorated_function
    
    def secure_authentication_endpoint(self, f):
        """Decorator to secure authentication endpoints with monitoring"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = self._get_user_identifier()
                
                # Execute the original function
                result = f(*args, **kwargs)
                
                # Monitor authentication result
                success = self._determine_auth_success(result)
                self.security_middleware.monitor_authentication(
                    user_id,
                    success,
                    {
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'ip_address': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent')
                    }
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in secure authentication endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        return decorated_function
    
    def secure_rate_limited_endpoint(self, f):
        """Decorator to secure rate-limited endpoints with monitoring"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = self._get_user_identifier()
                
                # Execute the original function
                result = f(*args, **kwargs)
                
                # Check if rate limit was exceeded (status code 429)
                if hasattr(result, 'status_code') and result.status_code == 429:
                    self.security_middleware.monitor_rate_limit_violation(
                        user_id,
                        request.endpoint,
                        {
                            'ip_address': request.remote_addr,
                            'user_agent': request.headers.get('User-Agent'),
                            'request_count': self._get_request_count(user_id, request.endpoint)
                        }
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in secure rate-limited endpoint: {e}")
                return jsonify({'error': 'Internal server error'}), 500
        
        return decorated_function
    
    def _get_user_identifier(self) -> str:
        """Get user identifier from request context"""
        # Try to get from JWT token
        if hasattr(g, 'user_id') and g.user_id:
            return str(g.user_id)
        
        # Try to get from session
        if hasattr(g, 'session') and g.session:
            return str(g.session.get('user_id', 'anonymous'))
        
        # Try to get from request parameters
        if request.args.get('user_id'):
            return request.args.get('user_id')
        
        # Try to get from JSON body
        if request.json and request.json.get('user_id'):
            return request.json.get('user_id')
        
        # Fallback to IP address
        return request.remote_addr or 'unknown'
    
    def _validate_assessment_input(self, request) -> Dict[str, Any]:
        """Validate assessment input for security threats"""
        errors = []
        
        try:
            # Validate JSON data
            if request.json:
                for key, value in request.json.items():
                    if isinstance(value, str):
                        # Check for SQL injection
                        if self.security_validator.detect_sql_injection(value):
                            errors.append(f"SQL injection attempt detected in {key}")
                        
                        # Check for XSS
                        if self.security_validator.detect_xss_attack(value):
                            errors.append(f"XSS attempt detected in {key}")
                        
                        # Check for command injection
                        if self.security_validator.detect_command_injection(value):
                            errors.append(f"Command injection attempt detected in {key}")
            
            # Validate URL parameters
            for key, value in request.args.items():
                if isinstance(value, str):
                    if self.security_validator.detect_sql_injection(value):
                        errors.append(f"SQL injection attempt detected in URL parameter {key}")
                    
                    if self.security_validator.detect_xss_attack(value):
                        errors.append(f"XSS attempt detected in URL parameter {key}")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error validating assessment input: {e}")
            return {
                'valid': False,
                'errors': ['Input validation error']
            }
    
    def _determine_auth_success(self, result) -> bool:
        """Determine if authentication was successful based on result"""
        try:
            # Check if result is a tuple (response, status_code)
            if isinstance(result, tuple) and len(result) == 2:
                response, status_code = result
                return status_code == 200
            
            # Check if result has status_code attribute
            if hasattr(result, 'status_code'):
                return result.status_code == 200
            
            # Check if result is a dict with success field
            if isinstance(result, dict):
                return result.get('success', False)
            
            return False
            
        except Exception as e:
            logger.error(f"Error determining auth success: {e}")
            return False
    
    def _get_request_count(self, user_id: str, endpoint: str) -> int:
        """Get request count for rate limiting monitoring"""
        try:
            # This would typically query Redis or database for request count
            # For now, return a placeholder
            return 1
        except Exception as e:
            logger.error(f"Error getting request count: {e}")
            return 0
    
    def _log_assessment_completion(self, user_id: str, assessment_data: Dict):
        """Log successful assessment completion"""
        try:
            self.security_monitor.log_security_event(
                event_type=SecurityEventType.ASSESSMENT_ANOMALY,
                user_identifier=user_id,
                details={
                    'assessment_type': assessment_data.get('type'),
                    'completion_time': assessment_data.get('completion_time'),
                    'score': assessment_data.get('score'),
                    'response_count': len(assessment_data.get('responses', {}))
                },
                severity=SecuritySeverity.INFO
            )
        except Exception as e:
            logger.error(f"Error logging assessment completion: {e}")

class SecurityIntegrationManager:
    """Manages security integration across the application"""
    
    def __init__(self, db_session: Session, redis_client=None):
        self.db_session = db_session
        self.redis_client = redis_client
        self.assessment_integration = AssessmentSecurityIntegration(db_session, redis_client)
    
    def setup_security_monitoring(self, app):
        """Setup security monitoring for the Flask application"""
        
        # Register security monitoring with app context
        @app.before_request
        def before_request_security():
            """Security monitoring before each request"""
            try:
                # Log all requests for security analysis
                self._log_request_for_security()
                
                # Check for suspicious patterns in request
                self._check_request_suspicious_patterns()
                
            except Exception as e:
                logger.error(f"Error in before_request_security: {e}")
        
        @app.after_request
        def after_request_security(response):
            """Security monitoring after each request"""
            try:
                # Log response for security analysis
                self._log_response_for_security(response)
                
            except Exception as e:
                logger.error(f"Error in after_request_security: {e}")
            
            return response
    
    def _log_request_for_security(self):
        """Log request details for security analysis"""
        try:
            user_id = self._get_user_identifier()
            
            # Log request details
            self.assessment_integration.security_monitor.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_identifier=user_id,
                details={
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent'),
                    'content_length': request.content_length,
                    'content_type': request.content_type
                },
                severity=SecuritySeverity.INFO
            )
        except Exception as e:
            logger.error(f"Error logging request for security: {e}")
    
    def _check_request_suspicious_patterns(self):
        """Check for suspicious patterns in request"""
        try:
            user_id = self._get_user_identifier()
            
            # Check for suspicious headers
            suspicious_headers = [
                'X-Forwarded-For', 'X-Real-IP', 'X-Client-IP',
                'CF-Connecting-IP', 'True-Client-IP'
            ]
            
            for header in suspicious_headers:
                if header in request.headers:
                    self.assessment_integration.security_monitor.log_security_event(
                        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                        user_identifier=user_id,
                        details={
                            'suspicious_header': header,
                            'header_value': request.headers[header],
                            'endpoint': request.endpoint
                        },
                        severity=SecuritySeverity.WARNING
                    )
            
            # Check for suspicious user agents
            user_agent = request.headers.get('User-Agent', '')
            suspicious_user_agents = [
                'bot', 'crawler', 'spider', 'scraper',
                'curl', 'wget', 'python-requests'
            ]
            
            for suspicious_ua in suspicious_user_agents:
                if suspicious_ua.lower() in user_agent.lower():
                    self.assessment_integration.security_monitor.log_security_event(
                        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                        user_identifier=user_id,
                        details={
                            'suspicious_user_agent': user_agent,
                            'endpoint': request.endpoint
                        },
                        severity=SecuritySeverity.WARNING
                    )
                    break
                    
        except Exception as e:
            logger.error(f"Error checking suspicious patterns: {e}")
    
    def _log_response_for_security(self, response):
        """Log response details for security analysis"""
        try:
            user_id = self._get_user_identifier()
            
            # Log response details
            self.assessment_integration.security_monitor.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_identifier=user_id,
                details={
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'status_code': response.status_code,
                    'content_length': response.content_length,
                    'content_type': response.content_type
                },
                severity=SecuritySeverity.INFO
            )
        except Exception as e:
            logger.error(f"Error logging response for security: {e}")
    
    def _get_user_identifier(self) -> str:
        """Get user identifier from request context"""
        # Try to get from JWT token
        if hasattr(g, 'user_id') and g.user_id:
            return str(g.user_id)
        
        # Try to get from session
        if hasattr(g, 'session') and g.session:
            return str(g.session.get('user_id', 'anonymous'))
        
        # Fallback to IP address
        return request.remote_addr or 'unknown'
