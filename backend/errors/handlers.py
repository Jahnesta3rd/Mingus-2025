"""
Global error handlers for the Mingus financial application.
Provides centralized error handling with security-conscious responses and comprehensive logging.
"""

import traceback
import sys
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from flask import Flask, request, jsonify, current_app, g
from werkzeug.exceptions import HTTPException, BadRequest, Unauthorized, Forbidden, NotFound, InternalServerError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from redis.exceptions import RedisError
from celery.exceptions import CeleryError

from .exceptions import (
    MingusBaseException, AuthenticationError, AuthorizationError, 
    FinancialDataError, PaymentError, DatabaseError, APIError,
    BackgroundTaskError, SecurityError, ExternalServiceError
)
from ..logging.logger import get_logger


logger = get_logger(__name__)


class ErrorHandler:
    """Centralized error handling for the Mingus application."""
    
    def __init__(self, app: Flask):
        self.app = app
        self.setup_error_handlers()
    
    def setup_error_handlers(self):
        """Register all error handlers with the Flask app."""
        
        # Register custom exception handlers
        self.app.register_error_handler(MingusBaseException, self.handle_mingus_exception)
        
        # Register HTTP exception handlers
        self.app.register_error_handler(400, self.handle_bad_request)
        self.app.register_error_handler(401, self.handle_unauthorized)
        self.app.register_error_handler(403, self.handle_forbidden)
        self.app.register_error_handler(404, self.handle_not_found)
        self.app.register_error_handler(429, self.handle_rate_limit)
        self.app.register_error_handler(500, self.handle_internal_server_error)
        
        # Register database error handlers
        self.app.register_error_handler(SQLAlchemyError, self.handle_database_error)
        self.app.register_error_handler(IntegrityError, self.handle_integrity_error)
        self.app.register_error_handler(OperationalError, self.handle_operational_error)
        
        # Register external service error handlers
        self.app.register_error_handler(RedisError, self.handle_redis_error)
        self.app.register_error_handler(CeleryError, self.handle_celery_error)
        
        # Register generic exception handler (catch-all)
        self.app.register_error_handler(Exception, self.handle_generic_exception)
    
    def _sanitize_error_context(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from error context."""
        sanitized = context.copy()
        
        # Remove sensitive fields
        sensitive_fields = [
            'password', 'token', 'secret', 'key', 'api_key', 'private_key',
            'credit_card', 'ssn', 'social_security', 'account_number',
            'routing_number', 'pin', 'cvv', 'expiry'
        ]
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '[REDACTED]'
        
        # Remove request body if it might contain sensitive data
        if 'request_body' in sanitized:
            sanitized['request_body'] = '[REDACTED]'
        
        # Remove headers that might contain sensitive information
        if 'headers' in sanitized:
            headers = sanitized['headers'].copy()
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                if header in headers:
                    headers[header] = '[REDACTED]'
            sanitized['headers'] = headers
        
        return sanitized
    
    def _log_error(self, error: Exception, context: Dict[str, Any], 
                   error_type: str = "UNKNOWN", user_id: Optional[str] = None):
        """Log error with comprehensive context."""
        
        # Get request information
        request_info = {
            'method': request.method,
            'url': request.url,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'referrer': request.headers.get('Referer', 'Unknown'),
            'user_id': user_id or getattr(g, 'user_id', None),
            'session_id': getattr(g, 'session_id', None),
            'request_id': getattr(g, 'request_id', None)
        }
        
        # Create comprehensive error log
        error_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type,
            'error_class': error.__class__.__name__,
            'error_message': str(error),
            'error_traceback': traceback.format_exc(),
            'request_info': request_info,
            'error_context': self._sanitize_error_context(error, context),
            'environment': current_app.config.get('FLASK_ENV', 'unknown')
        }
        
        # Log based on error severity
        if isinstance(error, (AuthenticationError, AuthorizationError, SecurityError)):
            logger.warning("Security-related error occurred", extra=error_log)
        elif isinstance(error, (FinancialDataError, PaymentError)):
            logger.error("Financial data error occurred", extra=error_log)
        elif isinstance(error, (DatabaseError, ExternalServiceError)):
            logger.error("System error occurred", extra=error_log)
        else:
            logger.error("Unexpected error occurred", extra=error_log)
    
    def _create_error_response(self, error: Exception, status_code: int = 500,
                             user_message: str = None, error_id: str = None) -> Tuple[Dict[str, Any], int]:
        """Create a standardized error response."""
        
        # Generate error ID if not provided
        if not error_id:
            import uuid
            error_id = str(uuid.uuid4())[:8]
        
        # Determine user-friendly message
        if user_message:
            message = user_message
        elif hasattr(error, 'user_message'):
            message = error.user_message
        else:
            message = self._get_default_user_message(status_code)
        
        # Create response
        response = {
            "error": {
                "type": "error",
                "code": getattr(error, 'error_code', f"HTTP_{status_code}"),
                "message": message,
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(g, 'request_id', None)
            }
        }
        
        # Add additional context for development
        if current_app.config.get('FLASK_ENV') == 'development':
            response["error"]["debug"] = {
                "error_class": error.__class__.__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc().split('\n')[-5:]  # Last 5 lines
            }
        
        return response, status_code
    
    def _get_default_user_message(self, status_code: int) -> str:
        """Get default user-friendly message for HTTP status codes."""
        messages = {
            400: "Your request contains invalid information. Please check and try again.",
            401: "Please log in to continue.",
            403: "You don't have permission to perform this action.",
            404: "The requested resource was not found.",
            429: "You've made too many requests. Please wait a moment and try again.",
            500: "We're experiencing technical difficulties. Please try again later.",
            502: "We're experiencing issues with our services. Please try again later.",
            503: "We're temporarily unavailable. Please try again later."
        }
        return messages.get(status_code, "An unexpected error occurred. Please try again.")
    
    def handle_mingus_exception(self, error: MingusBaseException) -> Tuple[Dict[str, Any], int]:
        """Handle custom Mingus exceptions."""
        context = {
            'error_code': error.error_code,
            'context': error.context,
            'timestamp': error.timestamp.isoformat()
        }
        
        self._log_error(error, context, "MINGUS_EXCEPTION", 
                       getattr(g, 'user_id', None))
        
        # Determine appropriate status code
        status_code = self._get_status_code_for_error(error)
        
        return self._create_error_response(
            error, status_code, error.user_message, error.error_id
        )
    
    def _get_status_code_for_error(self, error: MingusBaseException) -> int:
        """Determine appropriate HTTP status code for Mingus exceptions."""
        if isinstance(error, (AuthenticationError, SessionExpiredError)):
            return 401
        elif isinstance(error, (AuthorizationError, CSRFError)):
            return 403
        elif isinstance(error, (InvalidFinancialDataError, DataValidationError, InvalidRequestError)):
            return 400
        elif isinstance(error, (InsufficientFundsError, TransactionLimitExceededError)):
            return 422
        elif isinstance(error, RateLimitExceededError):
            return 429
        elif isinstance(error, (DatabaseError, ExternalServiceError, BackgroundTaskError)):
            return 503
        else:
            return 500
    
    def handle_bad_request(self, error: BadRequest) -> Tuple[Dict[str, Any], int]:
        """Handle 400 Bad Request errors."""
        context = {'request_data': request.get_data(as_text=True)}
        self._log_error(error, context, "BAD_REQUEST", getattr(g, 'user_id', None))
        return self._create_error_response(error, 400)
    
    def handle_unauthorized(self, error: Unauthorized) -> Tuple[Dict[str, Any], int]:
        """Handle 401 Unauthorized errors."""
        context = {'auth_header': request.headers.get('Authorization', 'Not provided')}
        self._log_error(error, context, "UNAUTHORIZED", getattr(g, 'user_id', None))
        return self._create_error_response(error, 401)
    
    def handle_forbidden(self, error: Forbidden) -> Tuple[Dict[str, Any], int]:
        """Handle 403 Forbidden errors."""
        context = {'requested_resource': request.url}
        self._log_error(error, context, "FORBIDDEN", getattr(g, 'user_id', None))
        return self._create_error_response(error, 403)
    
    def handle_not_found(self, error: NotFound) -> Tuple[Dict[str, Any], int]:
        """Handle 404 Not Found errors."""
        context = {'requested_resource': request.url}
        self._log_error(error, context, "NOT_FOUND", getattr(g, 'user_id', None))
        return self._create_error_response(error, 404)
    
    def handle_rate_limit(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """Handle 429 Rate Limit errors."""
        context = {'rate_limit_info': 'Rate limit exceeded'}
        self._log_error(error, context, "RATE_LIMIT", getattr(g, 'user_id', None))
        return self._create_error_response(error, 429)
    
    def handle_internal_server_error(self, error: InternalServerError) -> Tuple[Dict[str, Any], int]:
        """Handle 500 Internal Server Error."""
        context = {'error_type': 'internal_server_error'}
        self._log_error(error, context, "INTERNAL_SERVER_ERROR", getattr(g, 'user_id', None))
        return self._create_error_response(error, 500)
    
    def handle_database_error(self, error: SQLAlchemyError) -> Tuple[Dict[str, Any], int]:
        """Handle database-related errors."""
        context = {
            'database_operation': 'database_operation',
            'sql_error': str(error)
        }
        self._log_error(error, context, "DATABASE_ERROR", getattr(g, 'user_id', None))
        return self._create_error_response(error, 503)
    
    def handle_integrity_error(self, error: IntegrityError) -> Tuple[Dict[str, Any], int]:
        """Handle database integrity errors."""
        context = {
            'database_operation': 'integrity_check',
            'constraint': getattr(error, 'orig', None)
        }
        self._log_error(error, context, "INTEGRITY_ERROR", getattr(g, 'user_id', None))
        return self._create_error_response(error, 400)
    
    def handle_operational_error(self, error: OperationalError) -> Tuple[Dict[str, Any], int]:
        """Handle database operational errors."""
        context = {
            'database_operation': 'operational',
            'connection_info': 'database_connection'
        }
        self._log_error(error, context, "OPERATIONAL_ERROR", getattr(g, 'user_id', None))
        return self._create_error_response(error, 503)
    
    def handle_redis_error(self, error: RedisError) -> Tuple[Dict[str, Any], int]:
        """Handle Redis connection errors."""
        context = {'service': 'redis', 'operation': 'cache_operation'}
        self._log_error(error, context, "REDIS_ERROR", getattr(g, 'user_id', None))
        return self._create_error_response(error, 503)
    
    def handle_celery_error(self, error: CeleryError) -> Tuple[Dict[str, Any], int]:
        """Handle Celery background task errors."""
        context = {'service': 'celery', 'operation': 'background_task'}
        self._log_error(error, context, "CELERY_ERROR", getattr(g, 'user_id', None))
        return self._create_error_response(error, 503)
    
    def handle_generic_exception(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """Handle any unhandled exceptions."""
        context = {
            'error_type': 'unhandled_exception',
            'error_class': error.__class__.__name__
        }
        self._log_error(error, context, "GENERIC_EXCEPTION", getattr(g, 'user_id', None))
        return self._create_error_response(error, 500)


def init_error_handlers(app: Flask):
    """Initialize error handlers for the Flask application."""
    error_handler = ErrorHandler(app)
    logger.info("Error handlers initialized successfully")
    return error_handler


def handle_validation_error(validation_errors: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Handle data validation errors with detailed feedback."""
    from .exceptions import DataValidationError
    
    error = DataValidationError(
        message="Data validation failed",
        validation_errors=list(validation_errors.keys())
    )
    
    # Create detailed validation error response
    response = {
        "error": {
            "type": "validation_error",
            "code": "DATA_VALIDATION_ERROR",
            "message": "Please check your information and try again",
            "error_id": error.error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "validation_errors": validation_errors,
            "request_id": getattr(g, 'request_id', None)
        }
    }
    
    return response, 400


def handle_rate_limit_exceeded(limit_type: str, retry_after: int = None) -> Tuple[Dict[str, Any], int]:
    """Handle rate limiting with proper headers."""
    from .exceptions import RateLimitExceededError
    
    error = RateLimitExceededError(limit_type, retry_after)
    
    response, status_code = error.to_dict(), 429
    
    # Add rate limit headers
    if retry_after:
        response['headers'] = {
            'Retry-After': str(retry_after),
            'X-RateLimit-Reset': str(retry_after)
        }
    
    return response, status_code
