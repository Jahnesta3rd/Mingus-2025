# backend/logging_config.py
"""
MINGUS Article Library - Logging Configuration
=============================================
Structured logging configuration for the article library system
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import structlog
from pythonjsonlogger import jsonlogger
from flask import Flask, request, g, has_request_context

# Custom formatter for structured logging
class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add request context if available
        if has_request_context():
            log_record['request_id'] = getattr(g, 'request_id', None)
            log_record['user_id'] = getattr(g, 'user_id', None)
            log_record['endpoint'] = request.endpoint
            log_record['method'] = request.method
            log_record['path'] = request.path
            log_record['ip'] = request.remote_addr
            log_record['user_agent'] = request.headers.get('User-Agent')
        
        # Add service information
        log_record['service'] = 'mingus-article-library'
        log_record['version'] = os.getenv('APP_VERSION', '1.0.0')
        log_record['environment'] = os.getenv('FLASK_ENV', 'development')

# Custom processor for adding request context
def add_request_context(logger, method_name, event_dict):
    """Add request context to log entries"""
    if has_request_context():
        event_dict['request_id'] = getattr(g, 'request_id', None)
        event_dict['user_id'] = getattr(g, 'user_id', None)
        event_dict['endpoint'] = request.endpoint
        event_dict['method'] = request.method
        event_dict['path'] = request.path
    return event_dict

# Custom processor for adding performance metrics
def add_performance_metrics(logger, method_name, event_dict):
    """Add performance metrics to log entries"""
    if has_request_context() and hasattr(g, 'start_time'):
        duration = (datetime.utcnow() - g.start_time).total_seconds()
        event_dict['duration_ms'] = round(duration * 1000, 2)
    return event_dict

# Custom processor for sanitizing sensitive data
def sanitize_sensitive_data(logger, method_name, event_dict):
    """Sanitize sensitive data from log entries"""
    sensitive_fields = ['password', 'token', 'api_key', 'secret']
    
    for field in sensitive_fields:
        if field in event_dict:
            event_dict[field] = '***REDACTED***'
    
    return event_dict

def setup_structlog():
    """Configure structlog for structured logging"""
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        add_request_context,
        add_performance_metrics,
        sanitize_sensitive_data,
        structlog.processors.JSONRenderer()
    ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def setup_flask_logging(app: Flask):
    """Configure Flask application logging"""
    
    # Configure Flask app logger
    app.logger.handlers.clear()
    
    # Create structured formatter
    formatter = StructuredFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Console handler for development
    if app.config.get('FLASK_ENV') == 'development':
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.DEBUG)
    
    # File handler for production
    if app.config.get('FLASK_ENV') == 'production':
        # Ensure logs directory exists
        logs_dir = os.path.join(app.root_path, '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Application logs
        app_handler = logging.FileHandler(
            os.path.join(logs_dir, 'app.log')
        )
        app_handler.setFormatter(formatter)
        app.logger.addHandler(app_handler)
        app.logger.setLevel(logging.INFO)
        
        # Error logs
        error_handler = logging.FileHandler(
            os.path.join(logs_dir, 'error.log')
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        app.logger.addHandler(error_handler)

def setup_component_logging():
    """Configure logging for specific components"""
    
    # Article search service - DEBUG level for detailed search queries
    logging.getLogger('backend.services.article_search').setLevel(logging.DEBUG)
    
    # AI classifier service - INFO level for classification results
    logging.getLogger('backend.services.ai_classifier').setLevel(logging.INFO)
    
    # Recommendation engine - INFO level for recommendation generation
    logging.getLogger('backend.services.article_recommendations').setLevel(logging.INFO)
    
    # Analytics service - INFO level for analytics events
    logging.getLogger('backend.services.analytics').setLevel(logging.INFO)
    
    # Cache service - DEBUG level for cache operations
    logging.getLogger('backend.services.cache_service').setLevel(logging.DEBUG)
    
    # Email processing - INFO level for email operations
    logging.getLogger('backend.services.email_processor').setLevel(logging.INFO)
    
    # Database operations - WARNING level (only show issues)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Celery tasks - INFO level for task execution
    logging.getLogger('celery').setLevel(logging.INFO)
    
    # Redis operations - WARNING level (only show issues)
    logging.getLogger('redis').setLevel(logging.WARNING)
    
    # External API calls - INFO level
    logging.getLogger('urllib3').setLevel(logging.INFO)
    logging.getLogger('requests').setLevel(logging.INFO)

def setup_logging_config():
    """Setup comprehensive logging configuration"""
    
    # Get log level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configure structlog
    setup_structlog()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create structured formatter
    formatter = StructuredFormatter(
        fmt='%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Setup component-specific logging
    setup_component_logging()

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)

def log_request_start():
    """Log the start of a request"""
    if has_request_context():
        g.start_time = datetime.utcnow()
        logger = get_logger('request')
        logger.info(
            "Request started",
            method=request.method,
            path=request.path,
            user_agent=request.headers.get('User-Agent'),
            ip=request.remote_addr
        )

def log_request_end(response):
    """Log the end of a request"""
    if has_request_context():
        duration = (datetime.utcnow() - g.start_time).total_seconds()
        logger = get_logger('request')
        logger.info(
            "Request completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )
    return response

def log_error(error, context: Optional[Dict[str, Any]] = None):
    """Log an error with context"""
    logger = get_logger('error')
    error_context = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': getattr(error, '__traceback__', None)
    }
    
    if context:
        error_context.update(context)
    
    logger.error("Error occurred", **error_context)

def log_performance_metric(metric_name: str, value: float, unit: str = 'ms', context: Optional[Dict[str, Any]] = None):
    """Log a performance metric"""
    logger = get_logger('performance')
    metric_data = {
        'metric_name': metric_name,
        'value': value,
        'unit': unit
    }
    
    if context:
        metric_data.update(context)
    
    logger.info("Performance metric", **metric_data)

def log_user_action(action: str, user_id: int, context: Optional[Dict[str, Any]] = None):
    """Log a user action"""
    logger = get_logger('user_action')
    action_data = {
        'action': action,
        'user_id': user_id
    }
    
    if context:
        action_data.update(context)
    
    logger.info("User action", **action_data)

def log_article_event(event_type: str, article_id: int, context: Optional[Dict[str, Any]] = None):
    """Log an article-related event"""
    logger = get_logger('article_event')
    event_data = {
        'event_type': event_type,
        'article_id': article_id
    }
    
    if context:
        event_data.update(context)
    
    logger.info("Article event", **event_data)

def log_ai_classification(article_id: int, classification_result: Dict[str, Any], processing_time: float):
    """Log AI classification results"""
    logger = get_logger('ai_classification')
    logger.info(
        "AI classification completed",
        article_id=article_id,
        phase=classification_result.get('phase'),
        difficulty=classification_result.get('difficulty'),
        cultural_relevance_score=classification_result.get('cultural_relevance_score'),
        quality_score=classification_result.get('quality_score'),
        processing_time_ms=round(processing_time * 1000, 2)
    )

def log_search_query(query: str, filters: Dict[str, Any], result_count: int, processing_time: float):
    """Log search query execution"""
    logger = get_logger('search')
    logger.info(
        "Search query executed",
        query=query,
        filters=filters,
        result_count=result_count,
        processing_time_ms=round(processing_time * 1000, 2)
    )

def log_recommendation_generation(user_id: int, recommendation_count: int, processing_time: float):
    """Log recommendation generation"""
    logger = get_logger('recommendations')
    logger.info(
        "Recommendations generated",
        user_id=user_id,
        recommendation_count=recommendation_count,
        processing_time_ms=round(processing_time * 1000, 2)
    )

def log_cache_operation(operation: str, key: str, hit: bool, processing_time: float):
    """Log cache operations"""
    logger = get_logger('cache')
    logger.debug(
        "Cache operation",
        operation=operation,
        key=key,
        hit=hit,
        processing_time_ms=round(processing_time * 1000, 2)
    )

def log_database_operation(operation: str, table: str, processing_time: float, row_count: int = None):
    """Log database operations"""
    logger = get_logger('database')
    log_data = {
        'operation': operation,
        'table': table,
        'processing_time_ms': round(processing_time * 1000, 2)
    }
    
    if row_count is not None:
        log_data['row_count'] = row_count
    
    logger.debug("Database operation", **log_data)

def log_celery_task(task_name: str, task_id: str, status: str, processing_time: float = None):
    """Log Celery task execution"""
    logger = get_logger('celery')
    task_data = {
        'task_name': task_name,
        'task_id': task_id,
        'status': status
    }
    
    if processing_time is not None:
        task_data['processing_time_ms'] = round(processing_time * 1000, 2)
    
    logger.info("Celery task", **task_data)

def log_external_api_call(service: str, endpoint: str, method: str, status_code: int, processing_time: float):
    """Log external API calls"""
    logger = get_logger('external_api')
    logger.info(
        "External API call",
        service=service,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        processing_time_ms=round(processing_time * 1000, 2)
    )

# Convenience function for quick setup
def setup_logging(app: Flask = None):
    """Setup logging for the application"""
    setup_logging_config()
    
    if app:
        setup_flask_logging(app)
    
    # Log startup
    logger = get_logger('startup')
    logger.info(
        "Logging system initialized",
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
        environment=os.getenv('FLASK_ENV', 'development'),
        service='mingus-article-library'
    )

if __name__ == '__main__':
    # Test logging configuration
    setup_logging()
    
    logger = get_logger('test')
    logger.info("Logging test", test_field="test_value")
    logger.error("Error test", error_details="test error")
    
    print("Logging configuration test completed")
