"""
MINGUS Application - PCI Compliance Middleware
==============================================

Flask middleware for PCI DSS compliance checking, request/response sanitization,
and automatic PCI violation detection and logging.

Features:
- Request/response sanitization for card data
- Automatic PCI violation detection
- Compliance checking middleware
- Security header enforcement
- Audit logging for compliance events

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import os
import re
import json
import logging
import hashlib
import hmac
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from flask import (
    request, response, g, current_app, abort, make_response,
    jsonify, session, has_request_context
)
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden
from werkzeug.middleware.proxy_fix import ProxyFix

from ..payment.pci_compliance import (
    get_pci_validator, PCIComplianceValidator, CardDataValidator
)
from .audit_logging import AuditLogger
from .payment_audit import PaymentAuditLogger

# Configure logging
logger = logging.getLogger(__name__)


class ViolationSeverity(Enum):
    """PCI violation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationType(Enum):
    """PCI violation types."""
    CARD_DATA_EXPOSURE = "card_data_exposure"
    INSECURE_TRANSMISSION = "insecure_transmission"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    COMPLIANCE_CHECK_FAILED = "compliance_check_failed"
    SECURITY_HEADER_MISSING = "security_header_missing"
    SENSITIVE_DATA_LOGGING = "sensitive_data_logging"


@dataclass
class PCIViolation:
    """PCI compliance violation record."""
    violation_id: str
    violation_type: ViolationType
    severity: ViolationSeverity
    description: str
    request_path: str
    request_method: str
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    mitigated: bool = False
    mitigation_action: Optional[str] = None


class PCIMiddleware:
    """PCI DSS compliance middleware for Flask applications."""
    
    def __init__(self, app=None):
        """Initialize PCI compliance middleware."""
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.pci_validator = get_pci_validator()
        self.audit_logger = AuditLogger()
        self.payment_audit_logger = PaymentAuditLogger()
        
        # PCI compliance settings
        self.enforce_compliance = True
        self.block_violations = True
        self.log_violations = True
        self.require_https = True
        
        # Sensitive data patterns
        self.sensitive_patterns = {
            'card_number': [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 16-digit cards
                r'\b\d{4}[-\s]?\d{6}[-\s]?\d{5}\b',  # 15-digit cards (Amex)
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,4}\b',  # 13-19 digit cards
            ],
            'cvv': [
                r'\b\d{3,4}\b',  # 3-4 digit CVV
            ],
            'expiry': [
                r'\b(0[1-9]|1[0-2])/([0-9]{2}|[0-9]{4})\b',  # MM/YY or MM/YYYY
                r'\b(0[1-9]|1[0-2])-([0-9]{2}|[0-9]{4})\b',  # MM-YY or MM-YYYY
            ],
            'ssn': [
                r'\b\d{3}-\d{2}-\d{4}\b',  # XXX-XX-XXXX
                r'\b\d{9}\b',  # XXXXXXXXX
            ],
            'bank_account': [
                r'\b\d{8,17}\b',  # 8-17 digit bank account numbers
            ]
        }
        
        # PCI protected routes
        self.pci_protected_routes = [
            '/api/payments',
            '/api/subscriptions',
            '/api/billing',
            '/api/webhooks/stripe',
            '/checkout',
            '/billing',
            '/subscription'
        ]
        
        # Excluded routes (health checks, etc.)
        self.excluded_routes = [
            '/health',
            '/status',
            '/metrics',
            '/ping'
        ]
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        
        # Load PCI compliance settings
        self.enforce_compliance = app.config.get('ENFORCE_PCI_COMPLIANCE', True)
        self.block_violations = app.config.get('BLOCK_PCI_VIOLATIONS', True)
        self.log_violations = app.config.get('LOG_PCI_VIOLATIONS', True)
        self.require_https = app.config.get('REQUIRE_HTTPS', True)
        
        # Register middleware
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
        
        # Register error handlers
        app.register_error_handler(400, self.handle_bad_request)
        app.register_error_handler(401, self.handle_unauthorized)
        app.register_error_handler(403, self.handle_forbidden)
        app.register_error_handler(500, self.handle_internal_error)
        
        self.logger.info("PCI compliance middleware initialized")
    
    def before_request(self):
        """Process request before handling."""
        try:
            # Skip middleware for excluded routes
            if self._is_excluded_route(request.path):
                return None
            
            # Set request start time for performance monitoring
            g.request_start_time = datetime.now()
            
            # Check HTTPS requirement
            if self.require_https and not request.is_secure:
                if request.path in self.pci_protected_routes:
                    self._log_violation(
                        ViolationType.INSECURE_TRANSMISSION,
                        ViolationSeverity.HIGH,
                        f"HTTPS required for PCI protected route: {request.path}",
                        request.path,
                        request.method
                    )
                    if self.block_violations:
                        abort(403, description="HTTPS required for this endpoint")
            
            # Check for sensitive data in request
            if self._contains_sensitive_data(request):
                self._log_violation(
                    ViolationType.CARD_DATA_EXPOSURE,
                    ViolationSeverity.CRITICAL,
                    "Sensitive data detected in request",
                    request.path,
                    request.method
                )
                if self.block_violations:
                    abort(400, description="Sensitive data not allowed in request")
            
            # Validate PCI compliance for protected routes
            if self._is_pci_protected_route(request.path):
                compliance_result = self._check_route_compliance(request)
                if not compliance_result['compliant']:
                    self._log_violation(
                        ViolationType.COMPLIANCE_CHECK_FAILED,
                        ViolationSeverity.HIGH,
                        f"PCI compliance check failed: {compliance_result['reason']}",
                        request.path,
                        request.method
                    )
                    if self.block_violations:
                        abort(403, description="PCI compliance check failed")
            
            # Log request for audit trail
            self._log_request_audit(request)
            
        except Exception as e:
            self.logger.error(f"PCI middleware before_request error: {e}")
            # Don't block the request on middleware errors
    
    def after_request(self, response):
        """Process response after handling."""
        try:
            # Skip middleware for excluded routes
            if self._is_excluded_route(request.path):
                return response
            
            # Add security headers
            response = self._add_security_headers(response)
            
            # Check for sensitive data in response
            if self._contains_sensitive_data_in_response(response):
                self._log_violation(
                    ViolationType.CARD_DATA_EXPOSURE,
                    ViolationSeverity.CRITICAL,
                    "Sensitive data detected in response",
                    request.path,
                    request.method
                )
                # Don't block the response, but log the violation
            
            # Log response for audit trail
            self._log_response_audit(request, response)
            
            # Calculate request duration
            if hasattr(g, 'request_start_time'):
                duration = datetime.now() - g.request_start_time
                response.headers['X-Request-Duration'] = str(duration.total_seconds())
            
        except Exception as e:
            self.logger.error(f"PCI middleware after_request error: {e}")
        
        return response
    
    def teardown_request(self, exception=None):
        """Clean up after request handling."""
        try:
            # Log any exceptions that occurred
            if exception:
                self._log_violation(
                    ViolationType.UNAUTHORIZED_ACCESS,
                    ViolationSeverity.MEDIUM,
                    f"Request exception: {str(exception)}",
                    request.path if has_request_context() else "unknown",
                    request.method if has_request_context() else "unknown"
                )
            
            # Clean up request context
            if hasattr(g, 'request_start_time'):
                del g.request_start_time
                
        except Exception as e:
            self.logger.error(f"PCI middleware teardown_request error: {e}")
    
    def _is_excluded_route(self, path: str) -> bool:
        """Check if route is excluded from PCI middleware."""
        return any(path.startswith(excluded) for excluded in self.excluded_routes)
    
    def _is_pci_protected_route(self, path: str) -> bool:
        """Check if route requires PCI compliance."""
        return any(path.startswith(protected) for protected in self.pci_protected_routes)
    
    def _contains_sensitive_data(self, request) -> bool:
        """Check if request contains sensitive data."""
        try:
            # Check request body
            if request.is_json:
                body_data = request.get_json(silent=True)
                if body_data and self._scan_for_sensitive_data(body_data):
                    return True
            
            # Check form data
            if request.form:
                form_data = dict(request.form)
                if self._scan_for_sensitive_data(form_data):
                    return True
            
            # Check query parameters
            if request.args:
                query_data = dict(request.args)
                if self._scan_for_sensitive_data(query_data):
                    return True
            
            # Check headers (excluding standard headers)
            headers_to_check = {
                'X-Card-Number', 'X-CVV', 'X-Expiry', 'X-SSN',
                'X-Bank-Account', 'X-Payment-Data'
            }
            
            for header in headers_to_check:
                if header in request.headers:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking for sensitive data: {e}")
            return False
    
    def _contains_sensitive_data_in_response(self, response) -> bool:
        """Check if response contains sensitive data."""
        try:
            # Check response content
            if response.content_type and 'json' in response.content_type:
                try:
                    response_data = json.loads(response.get_data(as_text=True))
                    if self._scan_for_sensitive_data(response_data):
                        return True
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass
            
            # Check response headers
            headers_to_check = {
                'X-Card-Number', 'X-CVV', 'X-Expiry', 'X-SSN',
                'X-Bank-Account', 'X-Payment-Data'
            }
            
            for header in headers_to_check:
                if header in response.headers:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking response for sensitive data: {e}")
            return False
    
    def _scan_for_sensitive_data(self, data: Any) -> bool:
        """Recursively scan data for sensitive information."""
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    # Check key names for sensitive indicators
                    if self._is_sensitive_key(key):
                        return True
                    
                    # Recursively check values
                    if self._scan_for_sensitive_data(value):
                        return True
            
            elif isinstance(data, list):
                for item in data:
                    if self._scan_for_sensitive_data(item):
                        return True
            
            elif isinstance(data, str):
                # Check for sensitive data patterns
                for pattern_type, patterns in self.sensitive_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, data, re.IGNORECASE):
                            return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error scanning for sensitive data: {e}")
            return False
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name indicates sensitive data."""
        sensitive_key_patterns = [
            r'card.*number', r'cc.*number', r'credit.*card',
            r'cvv', r'cvc', r'security.*code',
            r'expiry', r'expiration', r'exp',
            r'ssn', r'social.*security',
            r'bank.*account', r'account.*number',
            r'payment.*data', r'billing.*info'
        ]
        
        key_lower = key.lower()
        return any(re.search(pattern, key_lower) for pattern in sensitive_key_patterns)
    
    def _check_route_compliance(self, request) -> Dict[str, Any]:
        """Check PCI compliance for a specific route."""
        try:
            # Basic compliance checks
            compliance_checks = {
                'https_enforced': request.is_secure,
                'authentication_required': self._requires_authentication(request),
                'rate_limited': self._is_rate_limited(request),
                'audit_logged': True  # Always true if we reach this point
            }
            
            # Check if all required checks pass
            all_passed = all(compliance_checks.values())
            
            if not all_passed:
                failed_checks = [
                    key for key, value in compliance_checks.items() 
                    if not value
                ]
                reason = f"Failed compliance checks: {', '.join(failed_checks)}"
            else:
                reason = "All compliance checks passed"
            
            return {
                'compliant': all_passed,
                'reason': reason,
                'checks': compliance_checks
            }
            
        except Exception as e:
            self.logger.error(f"Error checking route compliance: {e}")
            return {
                'compliant': False,
                'reason': f"Compliance check error: {str(e)}",
                'checks': {}
            }
    
    def _requires_authentication(self, request) -> bool:
        """Check if route requires authentication."""
        # Check if user is authenticated
        if hasattr(request, 'user') and request.user:
            return True
        
        # Check session for authentication
        if session.get('user_id'):
            return True
        
        # Check for authentication headers
        auth_headers = ['Authorization', 'X-API-Key', 'X-Auth-Token']
        if any(header in request.headers for header in auth_headers):
            return True
        
        return False
    
    def _is_rate_limited(self, request) -> bool:
        """Check if request is within rate limits."""
        # This would integrate with your rate limiting system
        # For now, return True (no rate limiting implemented)
        return True
    
    def _add_security_headers(self, response) -> response:
        """Add security headers to response."""
        try:
            # PCI DSS required security headers
            security_headers = {
                'X-Frame-Options': 'DENY',
                'X-Content-Type-Options': 'nosniff',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'X-PCI-Compliance': 'enabled'
            }
            
            # Add headers to response
            for header, value in security_headers.items():
                if header not in response.headers:
                    response.headers[header] = value
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error adding security headers: {e}")
            return response
    
    def _log_violation(
        self,
        violation_type: ViolationType,
        severity: ViolationSeverity,
        description: str,
        request_path: str,
        request_method: str
    ):
        """Log a PCI compliance violation."""
        try:
            if not self.log_violations:
                return
            
            # Generate violation ID
            violation_id = self._generate_violation_id()
            
            # Get user information
            user_id = None
            if hasattr(request, 'user') and request.user:
                user_id = str(request.user.id)
            elif session.get('user_id'):
                user_id = str(session['user_id'])
            
            # Create violation record
            violation = PCIViolation(
                violation_id=violation_id,
                violation_type=violation_type,
                severity=severity,
                description=description,
                request_path=request_path,
                request_method=request_method,
                user_id=user_id,
                ip_address=request.remote_addr if has_request_context() else 'unknown',
                user_agent=request.headers.get('User-Agent', 'unknown') if has_request_context() else 'unknown',
                timestamp=datetime.now(),
                details={
                    'headers': dict(request.headers) if has_request_context() else {},
                    'query_params': dict(request.args) if has_request_context() else {},
                    'form_data': dict(request.form) if has_request_context() else {},
                    'json_data': request.get_json(silent=True) if has_request_context() else None
                }
            )
            
            # Log to audit system
            self.audit_logger.log_pci_violation(
                violation_id,
                violation_type.value,
                severity.value,
                description,
                request_path,
                request_method,
                user_id,
                violation.ip_address
            )
            
            # Log to payment audit system if payment-related
            if 'payment' in request_path.lower() or 'billing' in request_path.lower():
                self.payment_audit_logger.log_pci_violation(
                    violation_id,
                    violation_type.value,
                    severity.value,
                    description,
                    request_path,
                    request_method,
                    user_id
                )
            
            # Log to application logger
            log_message = (
                f"PCI VIOLATION [{severity.value.upper()}] {violation_type.value}: "
                f"{description} - {request_method} {request_path} - "
                f"User: {user_id}, IP: {violation.ip_address}"
            )
            
            if severity == ViolationSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif severity == ViolationSeverity.HIGH:
                self.logger.error(log_message)
            elif severity == ViolationSeverity.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            # Store violation for reporting
            self._store_violation(violation)
            
        except Exception as e:
            self.logger.error(f"Error logging PCI violation: {e}")
    
    def _generate_violation_id(self) -> str:
        """Generate unique violation ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        random_suffix = os.urandom(4).hex()
        return f"pci_violation_{timestamp}_{random_suffix}"
    
    def _store_violation(self, violation: PCIViolation):
        """Store violation for reporting and analysis."""
        try:
            # This would typically store to database
            # For now, just log to memory (not recommended for production)
            if not hasattr(self, '_violations'):
                self._violations = []
            
            self._violations.append(violation)
            
            # Keep only last 1000 violations in memory
            if len(self._violations) > 1000:
                self._violations = self._violations[-1000:]
                
        except Exception as e:
            self.logger.error(f"Error storing violation: {e}")
    
    def _log_request_audit(self, request):
        """Log request for audit trail."""
        try:
            # Basic request logging
            audit_data = {
                'timestamp': datetime.now().isoformat(),
                'method': request.method,
                'path': request.path,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'content_type': request.content_type,
                'content_length': request.content_length,
                'headers': dict(request.headers),
                'query_params': dict(request.args)
            }
            
            # Add user information if available
            if hasattr(request, 'user') and request.user:
                audit_data['user_id'] = str(request.user.id)
                audit_data['user_email'] = getattr(request.user, 'email', None)
            elif session.get('user_id'):
                audit_data['user_id'] = str(session['user_id'])
            
            # Log to audit system
            self.audit_logger.log_request(
                request.method,
                request.path,
                audit_data['user_id'] if 'user_id' in audit_data else None,
                audit_data['ip_address']
            )
            
        except Exception as e:
            self.logger.error(f"Error logging request audit: {e}")
    
    def _log_response_audit(self, request, response):
        """Log response for audit trail."""
        try:
            # Basic response logging
            audit_data = {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'content_type': response.content_type,
                'content_length': response.content_length,
                'headers': dict(response.headers)
            }
            
            # Add user information if available
            user_id = None
            if hasattr(request, 'user') and request.user:
                user_id = str(request.user.id)
            elif session.get('user_id'):
                user_id = str(session['user_id'])
            
            # Log to audit system
            self.audit_logger.log_response(
                request.method,
                request.path,
                response.status_code,
                user_id,
                request.remote_addr
            )
            
        except Exception as e:
            self.logger.error(f"Error logging response audit: {e}")
    
    def get_violations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[ViolationSeverity] = None,
        violation_type: Optional[ViolationType] = None
    ) -> List[PCIViolation]:
        """Get stored violations with optional filtering."""
        try:
            if not hasattr(self, '_violations'):
                return []
            
            violations = self._violations.copy()
            
            # Filter by date range
            if start_date:
                violations = [v for v in violations if v.timestamp >= start_date]
            if end_date:
                violations = [v for v in violations if v.timestamp <= end_date]
            
            # Filter by severity
            if severity:
                violations = [v for v in violations if v.severity == severity]
            
            # Filter by violation type
            if violation_type:
                violations = [v for v in violations if v.violation_type == violation_type]
            
            # Sort by timestamp (newest first)
            violations.sort(key=lambda x: x.timestamp, reverse=True)
            
            return violations
            
        except Exception as e:
            self.logger.error(f"Error getting violations: {e}")
            return []
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get PCI compliance report."""
        try:
            # Get violations from last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            violations = self.get_violations(start_date, end_date)
            
            # Calculate statistics
            total_violations = len(violations)
            critical_violations = len([v for v in violations if v.severity == ViolationSeverity.CRITICAL])
            high_violations = len([v for v in violations if v.severity == ViolationSeverity.HIGH])
            medium_violations = len([v for v in violations if v.severity == ViolationSeverity.MEDIUM])
            low_violations = len([v for v in violations if v.severity == ViolationSeverity.LOW])
            
            # Group by violation type
            violations_by_type = {}
            for violation in violations:
                violation_type = violation.violation_type.value
                if violation_type not in violations_by_type:
                    violations_by_type[violation_type] = 0
                violations_by_type[violation_type] += 1
            
            # Calculate compliance score
            if total_violations == 0:
                compliance_score = 100.0
            else:
                # Weight violations by severity
                weighted_violations = (
                    critical_violations * 10 +
                    high_violations * 5 +
                    medium_violations * 2 +
                    low_violations * 1
                )
                compliance_score = max(0.0, 100.0 - (weighted_violations * 2))
            
            return {
                'compliance_score': round(compliance_score, 2),
                'total_violations': total_violations,
                'critical_violations': critical_violations,
                'high_violations': high_violations,
                'medium_violations': medium_violations,
                'low_violations': low_violations,
                'violations_by_type': violations_by_type,
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    # Error handlers
    def handle_bad_request(self, error):
        """Handle 400 Bad Request errors."""
        self._log_violation(
            ViolationType.UNAUTHORIZED_ACCESS,
            ViolationSeverity.MEDIUM,
            f"Bad request: {error.description}",
            request.path if has_request_context() else "unknown",
            request.method if has_request_context() else "unknown"
        )
        
        return jsonify({
            'error': 'Bad Request',
            'message': error.description,
            'status_code': 400
        }), 400
    
    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors."""
        self._log_violation(
            ViolationType.UNAUTHORIZED_ACCESS,
            ViolationSeverity.HIGH,
            f"Unauthorized access: {error.description}",
            request.path if has_request_context() else "unknown",
            request.method if has_request_context() else "unknown"
        )
        
        return jsonify({
            'error': 'Unauthorized',
            'message': error.description,
            'status_code': 401
        }), 401
    
    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors."""
        self._log_violation(
            ViolationType.UNAUTHORIZED_ACCESS,
            ViolationSeverity.HIGH,
            f"Forbidden access: {error.description}",
            request.path if has_request_context() else "unknown",
            request.method if has_request_context() else "unknown"
        )
        
        return jsonify({
            'error': 'Forbidden',
            'message': error.description,
            'status_code': 403
        }), 403
    
    def handle_internal_error(self, error):
        """Handle 500 Internal Server Error."""
        self._log_violation(
            ViolationType.COMPLIANCE_CHECK_FAILED,
            ViolationSeverity.MEDIUM,
            f"Internal server error: {error.description}",
            request.path if has_request_context() else "unknown",
            request.method if has_request_context() else "unknown"
        )
        
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred',
            'status_code': 500
        }), 500


# Global PCI middleware instance
pci_middleware = PCIMiddleware()


def get_pci_middleware() -> PCIMiddleware:
    """Get the global PCI middleware instance."""
    return pci_middleware


def init_pci_middleware(app):
    """Initialize PCI middleware with Flask app."""
    pci_middleware.init_app(app)
    app.logger.info("PCI compliance middleware initialized")
