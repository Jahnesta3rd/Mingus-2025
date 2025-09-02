"""
Middleware for automatic error logging and request monitoring in the Mingus application.
Provides comprehensive request/response logging, error tracking, and performance monitoring.
"""

import time
import uuid
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps

from flask import Flask, request, g, current_app, Response
from werkzeug.exceptions import HTTPException

from ..logging.logger import get_logger, log_security_event, log_performance_metric
from ..monitoring.error_tracking import get_monitoring, ErrorSeverity
from ..errors.exceptions import MingusBaseException


class ErrorLoggingMiddleware:
    """Middleware for comprehensive error logging and request monitoring."""
    
    def __init__(self, app: Flask):
        self.app = app
        self.logger = get_logger('mingus.middleware')
        
        # Register middleware functions
        self._register_middleware()
    
    def _register_middleware(self):
        """Register all middleware functions with the Flask app."""
        
        # Request logging middleware
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)
        
        # Error handling middleware
        self.app.errorhandler(Exception)(self._handle_exception)
        
        # Register with teardown context
        self.app.teardown_appcontext(self._teardown_app_context)
        self.app.teardown_request(self._teardown_request)
    
    def _before_request(self):
        """Set up request context and start timing."""
        # Generate unique request ID
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = time.time()
        g.request_logged = False
        
        # Set user context if available
        try:
            g.user_id = request.headers.get('X-User-ID')
            g.session_id = request.headers.get('X-Session-ID')
        except Exception:
            g.user_id = None
            g.session_id = None
        
        # Log request start
        self._log_request_start()
        
        # Record request start metric
        self._record_request_metric('request_started')
    
    def _after_request(self, response: Response) -> Response:
        """Log request completion and record performance metrics."""
        try:
            # Calculate response time
            if hasattr(g, 'start_time'):
                response_time = time.time() - g.start_time
                
                # Log request completion
                self._log_request_completion(response, response_time)
                
                # Record performance metrics
                self._record_performance_metrics(response, response_time)
                
                # Check for security concerns
                self._check_security_concerns(response)
            
        except Exception as e:
            self.logger.error(f"Error in after_request middleware: {e}")
        
        return response
    
    def _handle_exception(self, exception: Exception):
        """Handle unhandled exceptions with comprehensive logging."""
        try:
            # Get request context
            request_context = self._get_request_context()
            
            # Log the exception
            self._log_exception(exception, request_context)
            
            # Record error in monitoring system
            self._record_error_in_monitoring(exception, request_context)
            
            # Check if this is a security-related exception
            if self._is_security_exception(exception):
                self._log_security_event(exception, request_context)
            
            # Return appropriate error response
            if isinstance(exception, HTTPException):
                return self._create_http_error_response(exception)
            elif isinstance(exception, MingusBaseException):
                return exception.to_dict(), self._get_status_code_for_exception(exception)
            else:
                return self._create_generic_error_response(exception)
                
        except Exception as e:
            self.logger.error(f"Error in exception handler: {e}")
            # Fallback to generic error response
            return self._create_generic_error_response(exception)
    
    def _teardown_app_context(self, exception: Optional[Exception]):
        """Clean up application context."""
        if exception:
            self.logger.error(f"Application context error: {exception}")
    
    def _teardown_request(self, exception: Optional[Exception]):
        """Clean up request context."""
        if exception:
            self._log_exception(exception, self._get_request_context())
    
    def _log_request_start(self):
        """Log the start of a request."""
        try:
            request_data = {
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'referrer': request.headers.get('Referer', 'Unknown'),
                'user_id': getattr(g, 'user_id', None),
                'session_id': getattr(g, 'session_id', None),
                'request_id': getattr(g, 'request_id', None),
                'content_type': request.content_type,
                'content_length': request.content_length,
                'headers': self._sanitize_headers(request.headers)
            }
            
            self.logger.info("Request started", extra={
                'extra_fields': request_data
            })
            
            g.request_logged = True
            
        except Exception as e:
            self.logger.error(f"Failed to log request start: {e}")
    
    def _log_request_completion(self, response: Response, response_time: float):
        """Log the completion of a request."""
        try:
            response_data = {
                'method': request.method,
                'url': request.url,
                'status_code': response.status_code,
                'response_time': response_time,
                'response_size': len(response.get_data()),
                'user_id': getattr(g, 'user_id', None),
                'request_id': getattr(g, 'request_id', None),
                'content_type': response.content_type
            }
            
            # Log at appropriate level based on status code
            if response.status_code >= 500:
                self.logger.error("Request completed with server error", extra={
                    'extra_fields': response_data
                })
            elif response.status_code >= 400:
                self.logger.warning("Request completed with client error", extra={
                    'extra_fields': response_data
                })
            else:
                self.logger.info("Request completed successfully", extra={
                    'extra_fields': response_data
                })
                
        except Exception as e:
            self.logger.error(f"Failed to log request completion: {e}")
    
    def _log_exception(self, exception: Exception, context: Dict[str, Any]):
        """Log an exception with comprehensive context."""
        try:
            exception_data = {
                'exception_type': exception.__class__.__name__,
                'exception_message': str(exception),
                'traceback': traceback.format_exc(),
                'request_context': context,
                'user_id': getattr(g, 'user_id', None),
                'request_id': getattr(g, 'request_id', None),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Log based on exception type
            if isinstance(exception, HTTPException):
                self.logger.warning(f"HTTP exception: {exception}", extra={
                    'extra_fields': exception_data
                })
            elif isinstance(exception, MingusBaseException):
                self.logger.error(f"Mingus exception: {exception}", extra={
                    'extra_fields': exception_data
                })
            else:
                self.logger.error(f"Unexpected exception: {exception}", extra={
                    'extra_fields': exception_data
                })
                
        except Exception as e:
            self.logger.error(f"Failed to log exception: {e}")
    
    def _record_error_in_monitoring(self, exception: Exception, context: Dict[str, Any]):
        """Record error in the monitoring system."""
        try:
            monitoring = get_monitoring()
            
            # Determine error severity
            if isinstance(exception, HTTPException):
                severity = ErrorSeverity.LOW if exception.code < 500 else ErrorSeverity.HIGH
            elif isinstance(exception, MingusBaseException):
                severity = ErrorSeverity.MEDIUM  # Default for custom exceptions
            else:
                severity = ErrorSeverity.HIGH
            
            # Record the error
            monitoring.record_error(
                error_type=exception.__class__.__name__,
                error_class=exception.__class__.__name__,
                error_message=str(exception),
                severity=severity,
                user_id=context.get('user_id'),
                request_id=context.get('request_id'),
                ip_address=context.get('remote_addr'),
                user_agent=context.get('user_agent'),
                context={
                    'endpoint': context.get('endpoint'),
                    'method': context.get('method'),
                    'url': context.get('url')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to record error in monitoring: {e}")
    
    def _record_performance_metrics(self, response: Response, response_time: float):
        """Record performance metrics for the request."""
        try:
            # Record response time
            log_performance_metric(
                'response_time',
                response_time,
                'seconds',
                tags={
                    'method': request.method,
                    'endpoint': request.endpoint,
                    'status_code': str(response.status_code)
                },
                metadata={
                    'url': request.url,
                    'user_id': getattr(g, 'user_id', None),
                    'request_id': getattr(g, 'request_id', None)
                }
            )
            
            # Record request size
            if request.content_length:
                log_performance_metric(
                    'request_size',
                    request.content_length,
                    'bytes',
                    tags={'method': request.method, 'endpoint': request.endpoint}
                )
            
            # Record response size
            response_size = len(response.get_data())
            log_performance_metric(
                'response_size',
                response_size,
                'bytes',
                tags={'method': request.method, 'endpoint': request.endpoint}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to record performance metrics: {e}")
    
    def _record_request_metric(self, metric_name: str):
        """Record a request-related metric."""
        try:
            monitoring = get_monitoring()
            monitoring.record_performance_metric(
                metric_name,
                1,
                'count',
                tags={
                    'method': request.method,
                    'endpoint': request.endpoint
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to record request metric: {e}")
    
    def _check_security_concerns(self, response: Response):
        """Check for potential security concerns in the request/response."""
        try:
            security_concerns = []
            
            # Check for suspicious user agents
            user_agent = request.headers.get('User-Agent', '')
            if any(suspicious in user_agent.lower() for suspicious in ['bot', 'crawler', 'scraper']):
                security_concerns.append('suspicious_user_agent')
            
            # Check for unusual request patterns
            if request.content_length and request.content_length > 10 * 1024 * 1024:  # 10MB
                security_concerns.append('large_request_size')
            
            # Check for suspicious headers
            suspicious_headers = ['x-forwarded-for', 'x-real-ip', 'x-client-ip']
            for header in suspicious_headers:
                if header in request.headers:
                    security_concerns.append(f'suspicious_header_{header}')
            
            # Log security concerns
            if security_concerns:
                log_security_event(
                    event_type='security_concern',
                    user_id=getattr(g, 'user_id', None),
                    ip_address=request.remote_addr,
                    concerns=security_concerns,
                    request_url=request.url,
                    user_agent=user_agent
                )
                
        except Exception as e:
            self.logger.error(f"Failed to check security concerns: {e}")
    
    def _is_security_exception(self, exception: Exception) -> bool:
        """Check if an exception is security-related."""
        security_exception_types = [
            'AuthenticationError', 'AuthorizationError', 'CSRFError',
            'SecurityError', 'SessionExpiredError'
        ]
        
        return any(sec_type in exception.__class__.__name__ 
                  for sec_type in security_exception_types)
    
    def _log_security_event(self, exception: Exception, context: Dict[str, Any]):
        """Log a security-related event."""
        try:
            log_security_event(
                event_type='security_exception',
                user_id=context.get('user_id'),
                ip_address=context.get('remote_addr'),
                exception_type=exception.__class__.__name__,
                exception_message=str(exception),
                request_url=context.get('url'),
                user_agent=context.get('user_agent')
            )
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Get comprehensive request context."""
        try:
            return {
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'user_id': getattr(g, 'user_id', None),
                'session_id': getattr(g, 'session_id', None),
                'request_id': getattr(g, 'request_id', None),
                'endpoint': request.endpoint,
                'headers': self._sanitize_headers(request.headers),
                'args': dict(request.args),
                'form': dict(request.form) if request.form else {},
                'json': request.get_json(silent=True)
            }
        except Exception as e:
            self.logger.error(f"Failed to get request context: {e}")
            return {}
    
    def _sanitize_headers(self, headers) -> Dict[str, str]:
        """Sanitize headers to remove sensitive information."""
        sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token',
            'x-csrf-token', 'x-session-id'
        }
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _create_http_error_response(self, exception: HTTPException):
        """Create a response for HTTP exceptions."""
        from flask import jsonify
        
        return jsonify({
            "error": {
                "type": "http_error",
                "code": exception.code,
                "message": exception.description,
                "error_id": str(uuid.uuid4())[:8],
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(g, 'request_id', None)
            }
        }), exception.code
    
    def _create_generic_error_response(self, exception: Exception):
        """Create a generic error response."""
        from flask import jsonify
        
        return jsonify({
            "error": {
                "type": "error",
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "error_id": str(uuid.uuid4())[:8],
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(g, 'request_id', None)
            }
        }), 500
    
    def _get_status_code_for_exception(self, exception: MingusBaseException) -> int:
        """Get appropriate HTTP status code for Mingus exceptions."""
        # This would typically be handled by the error handlers
        # Default to 500 for unexpected cases
        return 500


def init_error_logging_middleware(app: Flask) -> ErrorLoggingMiddleware:
    """Initialize error logging middleware for the Flask application."""
    middleware = ErrorLoggingMiddleware(app)
    
    logger = get_logger('mingus.middleware')
    logger.info("Error logging middleware initialized successfully")
    
    return middleware


# Decorator for manual error logging
def log_errors(f: Callable) -> Callable:
    """Decorator to automatically log errors in a function."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger = get_logger('mingus.decorators')
            logger.error(f"Error in {f.__name__}: {e}", extra={
                'extra_fields': {
                    'function': f.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs),
                    'exception_type': e.__class__.__name__,
                    'exception_message': str(e),
                    'traceback': traceback.format_exc()
                }
            })
            raise
    
    return decorated_function


# Context manager for error logging
class ErrorLoggingContext:
    """Context manager for logging errors in a specific context."""
    
    def __init__(self, context_name: str, **context_data):
        self.context_name = context_name
        self.context_data = context_data
        self.logger = get_logger('mingus.context')
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Entering context: {self.context_name}", extra={
            'extra_fields': {
                'context_name': self.context_name,
                'context_data': self.context_data,
                'action': 'enter'
            }
        })
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is not None:
            # Exception occurred
            self.logger.error(f"Exception in context: {self.context_name}", extra={
                'extra_fields': {
                    'context_name': self.context_name,
                    'context_data': self.context_data,
                    'exception_type': exc_type.__name__ if exc_type else None,
                    'exception_message': str(exc_val) if exc_val else None,
                    'duration': duration,
                    'action': 'exit_with_error'
                }
            })
        else:
            # Normal exit
            self.logger.info(f"Exiting context: {self.context_name}", extra={
                'extra_fields': {
                    'context_name': self.context_name,
                    'context_data': self.context_data,
                    'duration': duration,
                    'action': 'exit_success'
                }
            })
        
        # Don't suppress the exception
        return False
