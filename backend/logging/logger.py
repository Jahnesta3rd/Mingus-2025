"""
Structured logging configuration for the Mingus financial application.
Provides JSON-formatted logging with rotation, privacy protection, and comprehensive monitoring.
"""

import os
import sys
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Third-party imports
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    print("Warning: structlog not available, falling back to standard logging")

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    print("Warning: sentry_sdk not available, error tracking will be limited")


class PrivacyAwareJSONFormatter(logging.Formatter):
    """JSON formatter that automatically redacts sensitive information."""
    
    # Fields that should always be redacted
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'key', 'api_key', 'private_key',
        'credit_card', 'ssn', 'social_security', 'account_number',
        'routing_number', 'pin', 'cvv', 'expiry', 'cvv2', 'cvc',
        'card_number', 'cardholder_name', 'billing_address',
        'mother_maiden_name', 'security_question', 'security_answer'
    }
    
    # Patterns that indicate sensitive data
    SENSITIVE_PATTERNS = [
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{9}\b',  # 9-digit numbers (potential SSN)
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{10,11}\b',  # Phone numbers
    ]
    
    def __init__(self, include_timestamp: bool = True, 
                 include_level: bool = True, 
                 include_logger: bool = True,
                 include_module: bool = True,
                 include_function: bool = True,
                 include_line: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_module = include_module
        self.include_function = include_function
        self.include_line = include_line
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with privacy protection."""
        
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self._sanitize_message(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'extra_fields'):
            log_entry.update(self._sanitize_dict(record.extra_fields))
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else 'Unknown',
                'message': str(record.exc_info[1]) if record.exc_info[1] else 'Unknown error',
                'traceback': self._sanitize_traceback(record.exc_info[2])
            }
        
        # Add request context if available
        try:
            from flask import request, g
            if request:
                log_entry['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', 'Unknown'),
                    'user_id': getattr(g, 'user_id', None),
                    'session_id': getattr(g, 'session_id', None),
                    'request_id': getattr(g, 'request_id', None)
                }
        except (ImportError, RuntimeError):
            pass  # Not in Flask context
        
        # Remove None values and empty strings
        log_entry = {k: v for k, v in log_entry.items() if v is not None and v != ''}
        
        return json.dumps(log_entry, default=str)
    
    def _sanitize_message(self, message: str) -> str:
        """Sanitize log message for sensitive information."""
        import re
        
        # Replace sensitive patterns
        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, '[REDACTED]', message)
        
        return message
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary for sensitive information."""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            # Check if key contains sensitive information
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_message(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _sanitize_traceback(self, traceback_obj) -> str:
        """Sanitize traceback for sensitive information."""
        if not traceback_obj:
            return ""
        
        import traceback
        tb_lines = traceback.format_tb(traceback_obj)
        sanitized_lines = []
        
        for line in tb_lines:
            sanitized_line = self._sanitize_message(line)
            sanitized_lines.append(sanitized_line)
        
        return ''.join(sanitized_lines)


class MingusLogger:
    """Main logging configuration for the Mingus application."""
    
    def __init__(self, app_name: str = "mingus", 
                 log_level: str = "INFO",
                 log_dir: str = "logs",
                 max_log_size: int = 100 * 1024 * 1024,  # 100MB
                 backup_count: int = 10,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_sentry: bool = False,
                 sentry_dsn: str = None):
        
        self.app_name = app_name
        self.log_level = getattr(logging, log_level.upper())
        self.log_dir = Path(log_dir)
        self.max_log_size = max_log_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_sentry = enable_sentry
        self.sentry_dsn = sentry_dsn
        
        # Create log directory if it doesn't exist
        if self.enable_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize Sentry if enabled
        if self.enable_sentry and self.sentry_dsn and SENTRY_AVAILABLE:
            self._setup_sentry()
    
    def _setup_logging(self):
        """Configure the logging system."""
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        json_formatter = PrivacyAwareJSONFormatter()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File handlers for different log types
        if self.enable_file:
            self._setup_file_handlers(root_logger, json_formatter)
        
        # Set specific logger levels
        self._configure_logger_levels()
        
        # Log initialization
        logger = logging.getLogger(__name__)
        logger.info("Logging system initialized", extra={
            'extra_fields': {
                'app_name': self.app_name,
                'log_level': logging.getLevelName(self.log_level),
                'log_dir': str(self.log_dir),
                'console_enabled': self.enable_console,
                'file_enabled': self.enable_file,
                'sentry_enabled': self.enable_sentry
            }
        })
    
    def _setup_file_handlers(self, root_logger: logging.Logger, formatter: logging.Formatter):
        """Setup file handlers for different log types."""
        
        # Main application log
        app_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}.log",
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        app_handler.setLevel(self.log_level)
        app_handler.setFormatter(formatter)
        root_logger.addHandler(app_handler)
        
        # Error log
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_errors.log",
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        # Security log
        security_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_security.log",
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(formatter)
        root_logger.addHandler(security_handler)
        
        # Financial transaction log
        financial_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_financial.log",
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        financial_handler.setLevel(logging.INFO)
        financial_handler.setFormatter(formatter)
        root_logger.addHandler(financial_handler)
        
        # Performance log
        performance_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.app_name}_performance.log",
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(formatter)
        root_logger.addHandler(performance_handler)
    
    def _configure_logger_levels(self):
        """Configure specific logger levels for different components."""
        
        # Set noisy loggers to higher levels
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('boto3').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        logging.getLogger('celery').setLevel(logging.INFO)
        logging.getLogger('redis').setLevel(logging.WARNING)
        
        # Set our loggers to appropriate levels
        logging.getLogger('mingus').setLevel(logging.DEBUG)
        logging.getLogger('mingus.security').setLevel(logging.INFO)
        logging.getLogger('mingus.financial').setLevel(logging.INFO)
        logging.getLogger('mingus.performance').setLevel(logging.INFO)
    
    def _setup_sentry(self):
        """Initialize Sentry for error tracking."""
        if not SENTRY_AVAILABLE:
            return
        
        try:
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                integrations=[
                    FlaskIntegration(),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    CeleryIntegration(),
                ],
                environment=os.getenv('FLASK_ENV', 'development'),
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                # Set a uniform sample rate for all transactions
                traces_sampler=lambda context: 0.1,
                # Filter out health check endpoints
                before_send=lambda event, hint: None if self._is_health_check(event) else event,
            )
            
            logger = logging.getLogger(__name__)
            logger.info("Sentry integration initialized successfully")
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize Sentry: {e}")
    
    def _is_health_check(self, event) -> bool:
        """Check if event is from a health check endpoint."""
        if 'request' in event:
            url = event['request'].get('url', '')
            return any(health_endpoint in url for health_endpoint in ['/health', '/status', '/ping'])
        return False


# Global logger instance
_mingus_logger = None


def init_logging(app_name: str = "mingus", **kwargs) -> MingusLogger:
    """Initialize the logging system."""
    global _mingus_logger
    
    if _mingus_logger is None:
        _mingus_logger = MingusLogger(app_name, **kwargs)
    
    return _mingus_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def get_app_logger() -> logging.Logger:
    """Get the main application logger."""
    return logging.getLogger('mingus')


def get_security_logger() -> logging.Logger:
    """Get the security-specific logger."""
    return logging.getLogger('mingus.security')


def get_financial_logger() -> logging.Logger:
    """Get the financial transaction logger."""
    return logging.getLogger('mingus.financial')


def get_performance_logger() -> logging.Logger:
    """Get the performance monitoring logger."""
    return logging.getLogger('mingus.performance')


def log_financial_transaction(transaction_type: str, amount: float, 
                            user_id: str, status: str, **kwargs):
    """Log a financial transaction with privacy protection."""
    logger = get_financial_logger()
    
    # Sanitize sensitive information
    sanitized_kwargs = {}
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in ['card', 'account', 'routing', 'ssn']):
            sanitized_kwargs[key] = '[REDACTED]'
        else:
            sanitized_kwargs[key] = value
    
    logger.info("Financial transaction", extra={
        'extra_fields': {
            'transaction_type': transaction_type,
            'amount': amount,
            'user_id': user_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            **sanitized_kwargs
        }
    })


def log_security_event(event_type: str, user_id: str = None, 
                      ip_address: str = None, **kwargs):
    """Log a security-related event."""
    logger = get_security_logger()
    
    logger.warning("Security event", extra={
        'extra_fields': {
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
    })


def log_performance_metric(metric_name: str, value: float, 
                          unit: str = None, **kwargs):
    """Log a performance metric."""
    logger = get_performance_logger()
    
    logger.info("Performance metric", extra={
        'extra_fields': {
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
    })
