"""
MINGUS Application - Audit Middleware
=====================================

Flask middleware for automatic audit logging of all requests and responses.
Provides comprehensive request/response audit trail capture with minimal
performance impact on user operations.

Features:
- Automatic request/response logging
- User context and IP tracking
- Performance impact minimization
- Configurable logging levels
- Integration with existing security systems
- Request correlation and tracing

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import os
import time
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable
from functools import wraps

from flask import (
    Flask, request, response, g, session, current_app,
    has_request_context, abort, jsonify
)
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from .audit_logger import (
    AuditLogger, AuditEventType, AuditCategory, 
    AuditSeverity, AuditContext
)

logger = logging.getLogger(__name__)


class AuditMiddleware:
    """
    Flask middleware for comprehensive request/response audit logging.
    
    Automatically logs all incoming requests and outgoing responses
    with detailed context information for compliance and security monitoring.
    """
    
    def __init__(self, app: Flask = None, audit_logger: AuditLogger = None):
        self.app = app
        self.audit_logger = audit_logger or AuditLogger()
        self.enable_request_logging = True
        self.enable_response_logging = True
        self.enable_performance_logging = True
        self.enable_error_logging = True
        self.sensitive_endpoints = set()
        self.excluded_endpoints = set()
        self.sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'x-stripe-signature', 'x-webhook-signature'
        }
        self.sensitive_params = {
            'password', 'token', 'secret', 'key', 'api_key',
            'access_token', 'refresh_token', 'stripe_token'
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the audit middleware with Flask app"""
        self.app = app
        
        # Load configuration
        self.enable_request_logging = app.config.get('AUDIT_REQUEST_LOGGING', True)
        self.enable_response_logging = app.config.get('AUDIT_RESPONSE_LOGGING', True)
        self.enable_performance_logging = app.config.get('AUDIT_PERFORMANCE_LOGGING', True)
        self.enable_error_logging = app.config.get('AUDIT_ERROR_LOGGING', True)
        
        # Load sensitive endpoints from config
        self.sensitive_endpoints = set(app.config.get('AUDIT_SENSITIVE_ENDPOINTS', []))
        self.excluded_endpoints = set(app.config.get('AUDIT_EXCLUDED_ENDPOINTS', []))
        
        # Load sensitive headers and parameters
        self.sensitive_headers = set(app.config.get('AUDIT_SENSITIVE_HEADERS', self.sensitive_headers))
        self.sensitive_params = set(app.config.get('AUDIT_SENSITIVE_PARAMS', self.sensitive_params))
        
        # Register middleware
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)
        
        # Register error handlers
        app.register_error_handler(Exception, self._handle_exception)
        app.register_error_handler(HTTPException, self._handle_http_exception)
        
        # Initialize audit logger with app
        self.audit_logger.init_app(app)
        
        logger.info("Audit middleware initialized successfully")
    
    def _before_request(self):
        """Log incoming request details"""
        if not self.enable_request_logging:
            return
        
        try:
            # Generate request ID for correlation
            request_id = str(uuid.uuid4())
            g.request_id = request_id
            g.request_start_time = time.time()
            
            # Skip logging for excluded endpoints
            if request.endpoint in self.excluded_endpoints:
                return
            
            # Extract request context
            context = self._extract_request_context()
            
            # Determine if this is a sensitive endpoint
            is_sensitive = (
                request.endpoint in self.sensitive_endpoints or
                any(sensitive in request.path.lower() for sensitive in ['login', 'auth', 'payment', 'stripe'])
            )
            
            # Prepare request data (sanitized)
            request_data = self._sanitize_request_data(is_sensitive)
            
            # Log request
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                category=AuditCategory.DATA_ACCESS,
                severity=AuditSeverity.INFO,
                description=f"Request received: {request.method} {request.path}",
                context=context,
                data={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.path,
                    'endpoint': request.endpoint,
                    'query_params': request_data.get('query_params', {}),
                    'headers': request_data.get('headers', {}),
                    'body_size': len(request.get_data()) if request.get_data() else 0,
                    'content_type': request.content_type,
                    'is_sensitive': is_sensitive,
                    'user_authenticated': bool(getattr(g, 'user_id', None)),
                    'session_active': bool(session.get('user_id')),
                    'correlation_id': request.headers.get('X-Correlation-ID'),
                    'user_agent': request.headers.get('User-Agent'),
                    'referrer': request.headers.get('Referer'),
                    'origin': request.headers.get('Origin')
                },
                user_id=getattr(g, 'user_id', None)
            )
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
            # Don't fail the request due to audit logging errors
    
    def _after_request(self, response):
        """Log response details"""
        if not self.enable_response_logging:
            return response
        
        try:
            # Skip logging for excluded endpoints
            if request.endpoint in self.excluded_endpoints:
                return response
            
            # Calculate request duration
            request_duration = 0
            if hasattr(g, 'request_start_time'):
                request_duration = (time.time() - g.request_start_time) * 1000  # Convert to milliseconds
            
            # Extract response context
            context = self._extract_request_context()
            
            # Prepare response data
            response_data = {
                'request_id': getattr(g, 'request_id', None),
                'status_code': response.status_code,
                'status_description': response.status,
                'response_size': len(response.get_data()) if response.get_data() else 0,
                'content_type': response.content_type,
                'request_duration_ms': round(request_duration, 2),
                'headers': dict(response.headers),
                'cookies_set': len(response.headers.getlist('Set-Cookie')),
                'cache_headers': {
                    'cache_control': response.headers.get('Cache-Control'),
                    'etag': response.headers.get('ETag'),
                    'last_modified': response.headers.get('Last-Modified')
                }
            }
            
            # Determine severity based on status code
            if response.status_code >= 500:
                severity = AuditSeverity.ERROR
            elif response.status_code >= 400:
                severity = AuditSeverity.WARNING
            else:
                severity = AuditSeverity.INFO
            
            # Log response
            self.audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                category=AuditCategory.DATA_ACCESS,
                severity=severity,
                description=f"Response sent: {response.status_code} {response.status}",
                context=context,
                data=response_data,
                user_id=getattr(g, 'user_id', None)
            )
            
            # Add audit headers to response
            if hasattr(g, 'request_id'):
                response.headers['X-Request-ID'] = g.request_id
            if hasattr(g, 'audit_correlation_id'):
                response.headers['X-Audit-Correlation-ID'] = g.audit_correlation_id
            
        except Exception as e:
            logger.error(f"Failed to log response: {e}")
            # Don't fail the response due to audit logging errors
        
        return response
    
    def _teardown_request(self, exception=None):
        """Handle request teardown and cleanup"""
        try:
            # Log any unhandled exceptions
            if exception and self.enable_error_logging:
                context = self._extract_request_context()
                
                self.audit_logger.log_event(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    category=AuditCategory.SECURITY,
                    severity=AuditSeverity.ERROR,
                    description=f"Unhandled exception: {type(exception).__name__}: {str(exception)}",
                    context=context,
                    data={
                        'request_id': getattr(g, 'request_id', None),
                        'exception_type': type(exception).__name__,
                        'exception_message': str(exception),
                        'exception_traceback': self._get_traceback(exception),
                        'request_path': request.path if request else None,
                        'request_method': request.method if request else None,
                        'user_id': getattr(g, 'user_id', None)
                    },
                    user_id=getattr(g, 'user_id', None)
                )
            
            # Clean up request context
            if hasattr(g, 'request_start_time'):
                del g.request_start_time
            if hasattr(g, 'request_id'):
                del g.request_id
            if hasattr(g, 'audit_correlation_id'):
                del g.audit_correlation_id
                
        except Exception as e:
            logger.error(f"Failed to handle request teardown: {e}")
    
    def _handle_exception(self, exception):
        """Handle general exceptions"""
        if not self.enable_error_logging:
            return self._default_error_response(exception)
        
        try:
            context = self._extract_request_context()
            
            # Log the exception
            self.audit_logger.log_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                category=AuditCategory.SECURITY,
                severity=AuditSeverity.CRITICAL,
                description=f"Application exception: {type(exception).__name__}: {str(exception)}",
                context=context,
                data={
                    'request_id': getattr(g, 'request_id', None),
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception),
                    'exception_traceback': self._get_traceback(exception),
                    'request_path': request.path if request else None,
                    'request_method': request.method if request else None,
                    'user_id': getattr(g, 'user_id', None),
                    'stack_trace': self._get_stack_trace()
                },
                user_id=getattr(g, 'user_id', None)
            )
            
        except Exception as e:
            logger.error(f"Failed to log exception: {e}")
        
        return self._default_error_response(exception)
    
    def _handle_http_exception(self, exception):
        """Handle HTTP exceptions"""
        if not self.enable_error_logging:
            return self._default_http_error_response(exception)
        
        try:
            context = self._extract_request_context()
            
            # Determine severity based on status code
            if exception.code >= 500:
                severity = AuditSeverity.ERROR
            elif exception.code >= 400:
                severity = AuditSeverity.WARNING
            else:
                severity = AuditSeverity.INFO
            
            # Log the HTTP exception
            self.audit_logger.log_event(
                event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                category=AuditCategory.SECURITY,
                severity=severity,
                description=f"HTTP exception: {exception.code} {exception.name}",
                context=context,
                data={
                    'request_id': getattr(g, 'request_id', None),
                    'status_code': exception.code,
                    'status_name': exception.name,
                    'description': exception.description,
                    'request_path': request.path if request else None,
                    'request_method': request.method if request else None,
                    'user_id': getattr(g, 'user_id', None),
                    'referrer': request.headers.get('Referer') if request else None,
                    'user_agent': request.headers.get('User-Agent') if request else None
                },
                user_id=getattr(g, 'user_id', None)
            )
            
        except Exception as e:
            logger.error(f"Failed to log HTTP exception: {e}")
        
        return self._default_http_error_response(exception)
    
    def _extract_request_context(self) -> AuditContext:
        """Extract comprehensive request context"""
        try:
            return AuditContext(
                user_id=getattr(g, 'user_id', None) or 
                        session.get('user_id') if session else None,
                session_id=session.get('session_id') if session else None,
                ip_address=self._get_client_ip(),
                user_agent=request.headers.get('User-Agent') if request else None,
                request_id=getattr(g, 'request_id', None),
                correlation_id=request.headers.get('X-Correlation-ID') if request else None,
                source=request.endpoint if request else None,
                metadata={
                    'method': request.method if request else None,
                    'url': request.url if request else None,
                    'base_url': request.base_url if request else None,
                    'host': request.host if request else None,
                    'scheme': request.scheme if request else None,
                    'remote_addr': request.remote_addr if request else None,
                    'forwarded_for': request.headers.get('X-Forwarded-For') if request else None,
                    'real_ip': request.headers.get('X-Real-IP') if request else None,
                    'content_length': request.content_length if request else None,
                    'mimetype': request.mimetype if request else None,
                    'accept_languages': request.accept_languages.best if request.accept_languages else None,
                    'accept_mimetypes': request.accept_mimetypes.best if request.accept_mimetypes else None
                } if request else None
            )
        except Exception as e:
            logger.warning(f"Failed to extract request context: {e}")
            return AuditContext()
    
    def _get_client_ip(self) -> str:
        """Get the real client IP address considering proxies"""
        try:
            if request:
                # Check for forwarded headers
                forwarded_for = request.headers.get('X-Forwarded-For')
                if forwarded_for:
                    # Take the first IP in the chain
                    return forwarded_for.split(',')[0].strip()
                
                real_ip = request.headers.get('X-Real-IP')
                if real_ip:
                    return real_ip
                
                # Fallback to remote address
                return request.remote_addr or 'unknown'
        except Exception:
            pass
        return 'unknown'
    
    def _sanitize_request_data(self, is_sensitive: bool) -> Dict[str, Any]:
        """Sanitize request data for logging"""
        try:
            if not request:
                return {}
            
            # Sanitize headers
            headers = dict(request.headers)
            if is_sensitive:
                for header in self.sensitive_headers:
                    if header.lower() in headers:
                        headers[header.lower()] = '[REDACTED]'
            
            # Sanitize query parameters
            query_params = dict(request.args)
            if is_sensitive:
                for param in self.sensitive_params:
                    if param in query_params:
                        query_params[param] = '[REDACTED]'
            
            # Sanitize form data
            form_data = {}
            if request.form:
                form_data = dict(request.form)
                if is_sensitive:
                    for param in self.sensitive_params:
                        if param in form_data:
                            form_data[param] = '[REDACTED]'
            
            # Sanitize JSON data
            json_data = {}
            if request.is_json:
                try:
                    json_data = request.get_json() or {}
                    if is_sensitive:
                        json_data = self._sanitize_json_data(json_data)
                except Exception:
                    json_data = {'error': 'Failed to parse JSON'}
            
            return {
                'headers': headers,
                'query_params': query_params,
                'form_data': form_data,
                'json_data': json_data,
                'files': list(request.files.keys()) if request.files else [],
                'cookies': list(request.cookies.keys()) if request.cookies else []
            }
            
        except Exception as e:
            logger.warning(f"Failed to sanitize request data: {e}")
            return {'error': str(e)}
    
    def _sanitize_json_data(self, data: Any, depth: int = 0) -> Any:
        """Recursively sanitize JSON data"""
        if depth > 10:  # Prevent infinite recursion
            return '[MAX_DEPTH_EXCEEDED]'
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.sensitive_params):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self._sanitize_json_data(value, depth + 1)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_json_data(item, depth + 1) for item in data]
        else:
            return data
    
    def _get_traceback(self, exception) -> str:
        """Get formatted traceback for exception"""
        try:
            import traceback
            return ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        except Exception:
            return str(exception)
    
    def _get_stack_trace(self) -> str:
        """Get current stack trace"""
        try:
            import traceback
            return ''.join(traceback.format_stack())
        except Exception:
            return 'Stack trace unavailable'
    
    def _default_error_response(self, exception) -> tuple:
        """Default error response for unhandled exceptions"""
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'request_id': getattr(g, 'request_id', None)
        }), 500
    
    def _default_http_error_response(self, exception) -> tuple:
        """Default error response for HTTP exceptions"""
        return jsonify({
            'error': exception.name,
            'message': exception.description,
            'status_code': exception.code,
            'request_id': getattr(g, 'request_id', None)
        }), exception.code


class AuditDecorator:
    """
    Decorator for automatic audit logging of specific endpoints.
    
    Provides fine-grained control over what gets logged and how
    for specific routes and functions.
    """
    
    def __init__(self, audit_logger: AuditLogger = None):
        self.audit_logger = audit_logger or AuditLogger()
    
    def __call__(self, event_type: AuditEventType, category: AuditCategory, 
                 severity: AuditSeverity = AuditSeverity.INFO, 
                 description: Optional[str] = None,
                 log_request: bool = True,
                 log_response: bool = True,
                 log_performance: bool = True):
        """
        Create audit decorator for function/route logging.
        
        Args:
            event_type: Type of audit event
            category: Category of the event
            severity: Severity level
            description: Event description
            log_request: Whether to log request details
            log_response: Whether to log response details
            log_performance: Whether to log performance metrics
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                request_id = str(uuid.uuid4())
                
                try:
                    # Log function entry
                    if log_request:
                        self._log_function_entry(func, event_type, category, severity, 
                                              description, request_id, *args, **kwargs)
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Log function completion
                    if log_response:
                        duration = (time.time() - start_time) * 1000
                        self._log_function_completion(func, event_type, category, severity,
                                                   description, request_id, duration, result)
                    
                    return result
                    
                except Exception as e:
                    # Log function failure
                    duration = (time.time() - start_time) * 1000
                    self._log_function_failure(func, event_type, category, severity,
                                            description, request_id, duration, e)
                    raise
            
            return wrapper
        return decorator
    
    def _log_function_entry(self, func, event_type, category, severity, description, 
                           request_id, *args, **kwargs):
        """Log function entry"""
        try:
            func_name = description or func.__name__
            self.audit_logger.log_event(
                event_type=event_type,
                category=category,
                severity=severity,
                description=f"Function called: {func_name}",
                data={
                    'request_id': request_id,
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys()) if kwargs else [],
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log function entry: {e}")
    
    def _log_function_completion(self, func, event_type, category, severity, 
                                description, request_id, duration, result):
        """Log function completion"""
        try:
            func_name = description or func.__name__
            self.audit_logger.log_event(
                event_type=event_type,
                category=category,
                severity=AuditSeverity.INFO,
                description=f"Function completed: {func_name}",
                data={
                    'request_id': request_id,
                    'function_name': func.__name__,
                    'duration_ms': round(duration, 2),
                    'status': 'success',
                    'result_type': type(result).__name__,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log function completion: {e}")
    
    def _log_function_failure(self, func, event_type, category, severity, 
                             description, request_id, duration, exception):
        """Log function failure"""
        try:
            func_name = description or func.__name__
            self.audit_logger.log_event(
                event_type=event_type,
                category=category,
                severity=AuditSeverity.ERROR,
                description=f"Function failed: {func_name}",
                data={
                    'request_id': request_id,
                    'function_name': func.__name__,
                    'duration_ms': round(duration, 2),
                    'status': 'failure',
                    'exception_type': type(exception).__name__,
                    'exception_message': str(exception),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log function failure: {e}")


# Global instances
audit_middleware = AuditMiddleware()
audit_decorator = AuditDecorator()

# Convenience functions
def init_audit_middleware(app: Flask, audit_logger: AuditLogger = None):
    """Initialize audit middleware for Flask app"""
    return AuditMiddleware(app, audit_logger)

def audit_route(event_type: AuditEventType, category: AuditCategory, 
                severity: AuditSeverity = AuditSeverity.INFO,
                description: Optional[str] = None):
    """Decorator for auditing specific routes"""
    return audit_decorator(event_type, category, severity, description)

def audit_function(event_type: AuditEventType, category: AuditCategory,
                  severity: AuditSeverity = AuditSeverity.INFO,
                  description: Optional[str] = None):
    """Decorator for auditing specific functions"""
    return audit_decorator(event_type, category, severity, description)
