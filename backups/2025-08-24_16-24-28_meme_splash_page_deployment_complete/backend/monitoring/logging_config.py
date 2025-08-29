"""
Logging Configuration
====================
Comprehensive logging setup for the MINGUS application with structured logging,
monitoring, and error tracking for the meme splash page feature.
"""

import os
import sys
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Dict, Any, Optional
import structlog
from structlog.stdlib import LoggerFactory
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        """Format log record as structured JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': record.process,
            'thread_id': record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)

class MemeFeatureLogger:
    """Specialized logger for meme feature events"""
    
    def __init__(self, logger_name: str = 'meme_feature'):
        self.logger = logging.getLogger(logger_name)
        self.struct_logger = structlog.get_logger(logger_name)
    
    def log_meme_view(self, user_id: int, meme_id: str, category: str, 
                     view_duration: Optional[int] = None, **kwargs):
        """Log meme view event"""
        self.struct_logger.info(
            "meme_viewed",
            user_id=user_id,
            meme_id=meme_id,
            category=category,
            view_duration=view_duration,
            event_type="meme_view",
            **kwargs
        )
    
    def log_meme_interaction(self, user_id: int, meme_id: str, interaction_type: str, **kwargs):
        """Log meme interaction event"""
        self.struct_logger.info(
            "meme_interaction",
            user_id=user_id,
            meme_id=meme_id,
            interaction_type=interaction_type,
            event_type="meme_interaction",
            **kwargs
        )
    
    def log_meme_upload(self, user_id: int, meme_id: str, category: str, 
                       file_size: int, **kwargs):
        """Log meme upload event"""
        self.struct_logger.info(
            "meme_uploaded",
            user_id=user_id,
            meme_id=meme_id,
            category=category,
            file_size=file_size,
            event_type="meme_upload",
            **kwargs
        )
    
    def log_meme_error(self, error_type: str, error_message: str, 
                      user_id: Optional[int] = None, meme_id: Optional[str] = None, **kwargs):
        """Log meme-related error"""
        self.struct_logger.error(
            "meme_error",
            error_type=error_type,
            error_message=error_message,
            user_id=user_id,
            meme_id=meme_id,
            event_type="meme_error",
            **kwargs
        )

def setup_logging(config: Dict[str, Any]) -> None:
    """
    Setup comprehensive logging configuration
    
    Args:
        config: Application configuration dictionary
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Get log level from config
    log_level = getattr(logging, config.get('LOG_LEVEL', 'INFO').upper())
    log_format = config.get('LOG_FORMAT', 'json')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if log_format == 'json':
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(console_handler)
    
    # File handler for application logs
    log_dir = config.get('LOG_DIR', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    app_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(app_handler)
    
    # Error log handler
    error_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)
    
    # Meme feature specific handler
    meme_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'meme_feature.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    meme_handler.setLevel(log_level)
    meme_handler.setFormatter(StructuredFormatter())
    
    meme_logger = logging.getLogger('meme_feature')
    meme_logger.addHandler(meme_handler)
    meme_logger.setLevel(log_level)
    
    # Security log handler
    security_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'security.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(StructuredFormatter())
    
    security_logger = logging.getLogger('security')
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.WARNING)
    
    # Performance log handler
    perf_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'performance.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    perf_handler.setLevel(log_level)
    perf_handler.setFormatter(StructuredFormatter())
    
    perf_logger = logging.getLogger('performance')
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(log_level)

def setup_sentry(config: Dict[str, Any]) -> None:
    """
    Setup Sentry error tracking
    
    Args:
        config: Application configuration dictionary
    """
    sentry_dsn = config.get('SENTRY_DSN')
    if not sentry_dsn:
        return
    
    # Configure Sentry integrations
    integrations = [
        FlaskIntegration(),
        SqlalchemyIntegration(),
        RedisIntegration(),
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
    ]
    
    # Initialize Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=integrations,
        traces_sample_rate=config.get('SENTRY_TRACES_SAMPLE_RATE', 0.1),
        profiles_sample_rate=config.get('SENTRY_PROFILES_SAMPLE_RATE', 0.1),
        environment=config.get('FLASK_ENV', 'development'),
        release=config.get('APP_VERSION', '1.0.0'),
        before_send=before_sentry_send
    )

def before_sentry_send(event, hint):
    """Filter sensitive data before sending to Sentry"""
    # Remove sensitive information
    if 'request' in event:
        if 'headers' in event['request']:
            # Remove sensitive headers
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                if header in event['request']['headers']:
                    event['request']['headers'][header] = '[REDACTED]'
        
        if 'data' in event['request']:
            # Remove sensitive data
            if isinstance(event['request']['data'], dict):
                sensitive_fields = ['password', 'token', 'secret', 'key']
                for field in sensitive_fields:
                    if field in event['request']['data']:
                        event['request']['data'][field] = '[REDACTED]'
    
    return event

def setup_performance_monitoring(config: Dict[str, Any]) -> None:
    """
    Setup performance monitoring
    
    Args:
        config: Application configuration dictionary
    """
    if not config.get('ENABLE_METRICS', False):
        return
    
    try:
        from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
        from flask import Response
        
        # Define metrics
        meme_views_total = Counter(
            'meme_views_total',
            'Total number of meme views',
            ['category', 'user_type']
        )
        
        meme_interactions_total = Counter(
            'meme_interactions_total',
            'Total number of meme interactions',
            ['interaction_type', 'category']
        )
        
        meme_upload_duration = Histogram(
            'meme_upload_duration_seconds',
            'Time spent uploading memes',
            ['category']
        )
        
        meme_response_time = Histogram(
            'meme_api_response_time_seconds',
            'API response time for meme endpoints',
            ['endpoint', 'method']
        )
        
        active_memes = Gauge(
            'active_memes_total',
            'Total number of active memes',
            ['category']
        )
        
        # Store metrics in config for access in routes
        config['metrics'] = {
            'meme_views_total': meme_views_total,
            'meme_interactions_total': meme_interactions_total,
            'meme_upload_duration': meme_upload_duration,
            'meme_response_time': meme_response_time,
            'active_memes': active_memes
        }
        
        logger = logging.getLogger('performance')
        logger.info("Performance monitoring enabled")
        
    except ImportError:
        logger = logging.getLogger('performance')
        logger.warning("Prometheus client not available, performance monitoring disabled")

def log_request_metrics(request, response, duration: float, config: Dict[str, Any]) -> None:
    """
    Log request metrics for monitoring
    
    Args:
        request: Flask request object
        response: Flask response object
        duration: Request duration in seconds
        config: Application configuration dictionary
    """
    if not config.get('ENABLE_METRICS', False):
        return
    
    try:
        metrics = config.get('metrics', {})
        response_time_metric = metrics.get('meme_response_time')
        
        if response_time_metric and 'meme' in request.endpoint:
            response_time_metric.labels(
                endpoint=request.endpoint,
                method=request.method
            ).observe(duration)
        
        # Log to performance log
        perf_logger = logging.getLogger('performance')
        perf_logger.info(
            "request_processed",
            endpoint=request.endpoint,
            method=request.method,
            status_code=response.status_code,
            duration=duration,
            user_agent=request.headers.get('User-Agent', ''),
            ip_address=request.remote_addr
        )
        
    except Exception as e:
        logger = logging.getLogger('performance')
        logger.error(f"Error logging request metrics: {e}")

def log_security_event(event_type: str, details: Dict[str, Any], 
                      user_id: Optional[int] = None, ip_address: Optional[str] = None) -> None:
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        details: Event details
        user_id: User ID if applicable
        ip_address: IP address if applicable
    """
    security_logger = logging.getLogger('security')
    security_logger.warning(
        "security_event",
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        **details
    )

def get_meme_logger() -> MemeFeatureLogger:
    """Get the meme feature logger instance"""
    return MemeFeatureLogger()

# Convenience functions for common logging patterns
def log_meme_view(user_id: int, meme_id: str, category: str, **kwargs):
    """Log a meme view event"""
    logger = get_meme_logger()
    logger.log_meme_view(user_id, meme_id, category, **kwargs)

def log_meme_interaction(user_id: int, meme_id: str, interaction_type: str, **kwargs):
    """Log a meme interaction event"""
    logger = get_meme_logger()
    logger.log_meme_interaction(user_id, meme_id, interaction_type, **kwargs)

def log_meme_upload(user_id: int, meme_id: str, category: str, file_size: int, **kwargs):
    """Log a meme upload event"""
    logger = get_meme_logger()
    logger.log_meme_upload(user_id, meme_id, category, file_size, **kwargs)

def log_meme_error(error_type: str, error_message: str, **kwargs):
    """Log a meme-related error"""
    logger = get_meme_logger()
    logger.log_meme_error(error_type, error_message, **kwargs)
