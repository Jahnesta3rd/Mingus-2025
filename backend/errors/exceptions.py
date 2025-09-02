"""
Custom exception classes for the Mingus financial application.
Provides structured error handling for different types of financial and system errors.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime


class MingusBaseException(Exception):
    """Base exception class for all Mingus application errors."""
    
    def __init__(self, message: str, error_code: str = None, 
                 user_message: str = None, context: Dict[str, Any] = None,
                 timestamp: datetime = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.user_message = user_message or "An unexpected error occurred. Please try again."
        self.context = context or {}
        self.timestamp = timestamp or datetime.utcnow()
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Generate a unique error ID for tracking."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "type": self.__class__.__name__,
                "code": self.error_code,
                "message": self.user_message,
                "error_id": self.error_id,
                "timestamp": self.timestamp.isoformat()
            }
        }
    
    def __str__(self):
        return f"{self.__class__.__name__}: {self.message} (ID: {self.error_id})"


# Authentication and Authorization Errors
class AuthenticationError(MingusBaseException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", 
                 user_message: str = "Please log in to continue"):
        super().__init__(message, "AUTH_FAILED", user_message)


class AuthorizationError(MingusBaseException):
    """Raised when user lacks permission for requested action."""
    
    def __init__(self, message: str = "Insufficient permissions", 
                 user_message: str = "You don't have permission to perform this action"):
        super().__init__(message, "INSUFFICIENT_PERMISSIONS", user_message)


class SessionExpiredError(MingusBaseException):
    """Raised when user session has expired."""
    
    def __init__(self, message: str = "Session expired", 
                 user_message: str = "Your session has expired. Please log in again"):
        super().__init__(message, "SESSION_EXPIRED", user_message)


# Financial Data Errors
class FinancialDataError(MingusBaseException):
    """Base class for financial data related errors."""
    
    def __init__(self, message: str, error_code: str, 
                 user_message: str = "There was an issue with your financial data"):
        super().__init__(message, error_code, user_message)


class InvalidFinancialDataError(FinancialDataError):
    """Raised when financial data is invalid or malformed."""
    
    def __init__(self, message: str = "Invalid financial data", 
                 field: str = None, value: Any = None):
        user_message = "Please check your financial information and try again"
        if field:
            user_message = f"Please check your {field} information and try again"
        
        context = {"field": field, "value": value}
        super().__init__(message, "INVALID_FINANCIAL_DATA", user_message, context)


class InsufficientFundsError(FinancialDataError):
    """Raised when user has insufficient funds for a transaction."""
    
    def __init__(self, required_amount: float, available_amount: float):
        message = f"Insufficient funds: required {required_amount}, available {available_amount}"
        user_message = "You don't have sufficient funds for this transaction"
        context = {
            "required_amount": required_amount,
            "available_amount": available_amount
        }
        super().__init__(message, "INSUFFICIENT_FUNDS", user_message, context)


class TransactionLimitExceededError(FinancialDataError):
    """Raised when transaction limit is exceeded."""
    
    def __init__(self, limit_type: str, limit_amount: float, attempted_amount: float):
        message = f"Transaction limit exceeded: {limit_type} limit {limit_amount}, attempted {attempted_amount}"
        user_message = f"Transaction amount exceeds your {limit_type} limit"
        context = {
            "limit_type": limit_type,
            "limit_amount": limit_amount,
            "attempted_amount": attempted_amount
        }
        super().__init__(message, "TRANSACTION_LIMIT_EXCEEDED", user_message, context)


# Payment Processing Errors
class PaymentError(MingusBaseException):
    """Base class for payment processing errors."""
    
    def __init__(self, message: str, error_code: str, 
                 user_message: str = "There was an issue processing your payment"):
        super().__init__(message, error_code, user_message)


class StripePaymentError(PaymentError):
    """Raised when Stripe payment processing fails."""
    
    def __init__(self, stripe_error: str, payment_intent_id: str = None):
        message = f"Stripe payment error: {stripe_error}"
        user_message = "Payment processing failed. Please check your payment information."
        context = {
            "stripe_error": stripe_error,
            "payment_intent_id": payment_intent_id
        }
        super().__init__(message, "STRIPE_PAYMENT_ERROR", user_message, context)


class PaymentMethodError(PaymentError):
    """Raised when payment method is invalid or expired."""
    
    def __init__(self, payment_method_type: str, reason: str):
        message = f"Payment method error: {payment_method_type} - {reason}"
        user_message = "Your payment method needs to be updated. Please add a new payment method."
        context = {
            "payment_method_type": payment_method_type,
            "reason": reason
        }
        super().__init__(message, "PAYMENT_METHOD_ERROR", user_message, context)


# Database and Data Errors
class DatabaseError(MingusBaseException):
    """Base class for database related errors."""
    
    def __init__(self, message: str, error_code: str, 
                 user_message: str = "There was an issue accessing your data"):
        super().__init__(message, error_code, user_message)


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message, "DB_CONNECTION_ERROR", 
                        "We're experiencing technical difficulties. Please try again later.")


class TransactionError(DatabaseError):
    """Raised when database transaction fails."""
    
    def __init__(self, message: str = "Database transaction failed", 
                 operation: str = None):
        user_message = "We couldn't complete your request. Please try again."
        context = {"operation": operation}
        super().__init__(message, "DB_TRANSACTION_ERROR", user_message, context)


class DataValidationError(MingusBaseException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, 
                 validation_errors: List[str] = None):
        user_message = "Please check your information and try again"
        if field:
            user_message = f"Please check your {field} and try again"
        
        context = {
            "field": field,
            "validation_errors": validation_errors or []
        }
        super().__init__(message, "DATA_VALIDATION_ERROR", user_message, context)


# API and Rate Limiting Errors
class APIError(MingusBaseException):
    """Base class for API related errors."""
    
    def __init__(self, message: str, error_code: str, 
                 user_message: str = "There was an issue with your request"):
        super().__init__(message, error_code, user_message)


class RateLimitExceededError(APIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, limit_type: str, retry_after: int = None):
        message = f"Rate limit exceeded: {limit_type}"
        user_message = "You've made too many requests. Please wait a moment and try again."
        context = {
            "limit_type": limit_type,
            "retry_after": retry_after
        }
        super().__init__(message, "RATE_LIMIT_EXCEEDED", user_message, context)


class InvalidRequestError(APIError):
    """Raised when API request is invalid."""
    
    def __init__(self, message: str, field: str = None):
        user_message = "Your request contains invalid information. Please check and try again."
        context = {"field": field}
        super().__init__(message, "INVALID_REQUEST", user_message, context)


# Background Task Errors
class BackgroundTaskError(MingusBaseException):
    """Base class for background task errors."""
    
    def __init__(self, message: str, error_code: str, 
                 user_message: str = "A background process failed. Please try again"):
        super().__init__(message, error_code, user_message)


class CeleryTaskError(BackgroundTaskError):
    """Raised when Celery background task fails."""
    
    def __init__(self, task_name: str, error_details: str):
        message = f"Celery task failed: {task_name} - {error_details}"
        user_message = "We're processing your request. You'll receive a notification when it's complete."
        context = {
            "task_name": task_name,
            "error_details": error_details
        }
        super().__init__(message, "CELERY_TASK_ERROR", user_message, context)


class QueueError(BackgroundTaskError):
    """Raised when task queue operations fail."""
    
    def __init__(self, operation: str, queue_name: str):
        message = f"Queue operation failed: {operation} on {queue_name}"
        user_message = "We're experiencing high demand. Please try again in a few minutes."
        context = {
            "operation": operation,
            "queue_name": queue_name
        }
        super().__init__(message, "QUEUE_ERROR", user_message, context)


# Security and Privacy Errors
class SecurityError(MingusBaseException):
    """Base class for security related errors."""
    
    def __init__(self, message: str, error_code: str, 
                 user_message: str = "A security check failed. Please try again"):
        super().__init__(message, error_code, user_message)


class CSRFError(SecurityError):
    """Raised when CSRF token validation fails."""
    
    def __init__(self, message: str = "CSRF token validation failed"):
        super().__init__(message, "CSRF_ERROR", 
                        "Security validation failed. Please refresh the page and try again.")


class DataPrivacyError(SecurityError):
    """Raised when data privacy requirements are violated."""
    
    def __init__(self, message: str, data_type: str = None):
        user_message = "We couldn't process your request due to privacy restrictions."
        context = {"data_type": data_type}
        super().__init__(message, "DATA_PRIVACY_ERROR", user_message, context)


# External Service Errors
class ExternalServiceError(MingusBaseException):
    """Base class for external service errors."""
    
    def __init__(self, message: str, error_code: str, service_name: str,
                 user_message: str = "We're experiencing issues with an external service"):
        context = {"service_name": service_name}
        super().__init__(message, error_code, user_message, context)


class RedisConnectionError(ExternalServiceError):
    """Raised when Redis connection fails."""
    
    def __init__(self, message: str = "Redis connection failed"):
        super().__init__(message, "REDIS_CONNECTION_ERROR", "Redis",
                        "We're experiencing technical difficulties. Please try again later.")


# Cultural and Accessibility Errors
class CulturalContextError(MingusBaseException):
    """Raised when cultural context requirements are not met."""
    
    def __init__(self, message: str, cultural_context: str):
        user_message = "We couldn't process your request due to missing cultural context information."
        context = {"cultural_context": cultural_context}
        super().__init__(message, "CULTURAL_CONTEXT_ERROR", user_message, context)


class AccessibilityError(MingusBaseException):
    """Raised when accessibility requirements are not met."""
    
    def __init__(self, message: str, accessibility_feature: str):
        user_message = "We couldn't provide the requested accessibility feature."
        context = {"accessibility_feature": accessibility_feature}
        super().__init__(message, "ACCESSIBILITY_ERROR", user_message, context)
