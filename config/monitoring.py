#!/usr/bin/env python3
"""
Monitoring and Logging Configuration for Mingus Meme Splash Page
Handles application logging, error tracking, and performance monitoring
"""

import os
import logging
import logging.handlers
from datetime import datetime
import json
import time
from functools import wraps
from typing import Dict, Any, Optional
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import newrelic.agent

class MonitoringConfig:
    def __init__(self):
        self.log_level = os.environ.get('LOG_LEVEL', 'INFO')
        self.log_file = os.environ.get('LOG_FILE', 'logs/mingus-meme-app.log')
        self.sentry_dsn = os.environ.get('SENTRY_DSN')
        self.new_relic_key = os.environ.get('NEW_RELIC_LICENSE_KEY')
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize error tracking
        self._setup_sentry()
        
        # Initialize performance monitoring
        self._setup_new_relic()
    
    def _setup_logging(self):
        """Configure application logging"""
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Application-specific logger
        self.logger = logging.getLogger('mingus.meme')
        
        # Disable some noisy loggers
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('boto3').setLevel(logging.WARNING)
        logging.getLogger('botocore').setLevel(logging.WARNING)
    
    def _setup_sentry(self):
        """Initialize Sentry for error tracking"""
        if self.sentry_dsn:
            try:
                sentry_sdk.init(
                    dsn=self.sentry_dsn,
                    integrations=[
                        FlaskIntegration(),
                        SqlalchemyIntegration(),
                    ],
                    traces_sample_rate=0.1,  # 10% of transactions
                    environment=os.environ.get('FLASK_ENV', 'production'),
                    release=os.environ.get('APP_VERSION', '1.0.0'),
                    before_send=self._sentry_before_send
                )
                self.logger.info("Sentry initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Sentry: {e}")
        else:
            self.logger.warning("Sentry DSN not configured")
    
    def _setup_new_relic(self):
        """Initialize New Relic for performance monitoring"""
        if self.new_relic_key:
            try:
                newrelic.agent.initialize('newrelic.ini')
                self.logger.info("New Relic initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize New Relic: {e}")
        else:
            self.logger.warning("New Relic license key not configured")
    
    def _sentry_before_send(self, event, hint):
        """Filter events before sending to Sentry"""
        # Don't send 404 errors
        if 'exc_info' in hint:
            exc_type, exc_value, tb = hint['exc_info']
            if hasattr(exc_value, 'code') and exc_value.code == 404:
                return None
        
        # Add custom context
        event.setdefault('tags', {})['component'] = 'meme-splash'
        
        return event
    
    def log_request(self, request, response, duration):
        """Log HTTP request details"""
        log_data = {
            'method': request.method,
            'url': request.url,
            'status_code': response.status_code,
            'duration_ms': duration * 1000,
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'user_id': request.headers.get('X-User-ID'),
            'session_id': request.headers.get('X-Session-ID')
        }
        
        # Log to file
        self.logger.info(f"Request: {json.dumps(log_data)}")
        
        # Send to Sentry if error
        if response.status_code >= 400:
            sentry_sdk.capture_message(
                f"HTTP {response.status_code}: {request.method} {request.url}",
                level='error',
                extra=log_data
            )
    
    def log_meme_interaction(self, meme_id: int, action: str, user_id: Optional[str] = None, **kwargs):
        """Log meme interaction for analytics"""
        log_data = {
            'event_type': 'meme_interaction',
            'meme_id': meme_id,
            'action': action,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        self.logger.info(f"Meme interaction: {json.dumps(log_data)}")
        
        # Send to analytics service if configured
        if os.environ.get('MIXPANEL_TOKEN'):
            self._send_to_mixpanel(log_data)
    
    def log_performance_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Log performance metrics"""
        log_data = {
            'event_type': 'performance_metric',
            'metric_name': metric_name,
            'value': value,
            'timestamp': datetime.utcnow().isoformat(),
            'tags': tags or {}
        }
        
        self.logger.info(f"Performance metric: {json.dumps(log_data)}")
        
        # Send to New Relic if available
        if self.new_relic_key:
            try:
                newrelic.agent.record_custom_metric(f"Custom/{metric_name}", value)
            except Exception as e:
                self.logger.error(f"Failed to send metric to New Relic: {e}")
    
    def _send_to_mixpanel(self, data: Dict[str, Any]):
        """Send analytics data to Mixpanel"""
        try:
            import requests
            
            # This is a simplified implementation
            # In production, you'd use the official Mixpanel library
            mixpanel_token = os.environ.get('MIXPANEL_TOKEN')
            if mixpanel_token:
                # Implementation would go here
                pass
        except Exception as e:
            self.logger.error(f"Failed to send to Mixpanel: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status"""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': os.environ.get('APP_VERSION', '1.0.0'),
            'environment': os.environ.get('FLASK_ENV', 'production'),
            'sentry_configured': bool(self.sentry_dsn),
            'new_relic_configured': bool(self.new_relic_key),
            'log_level': self.log_level
        }

def performance_monitor(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log performance
            monitoring.log_performance_metric(
                f"function.{func.__name__}.duration",
                duration,
                {'function': func.__name__}
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            monitoring.log_performance_metric(
                f"function.{func.__name__}.error",
                1,
                {'function': func.__name__, 'error': str(e)}
            )
            
            raise
    return wrapper

def log_errors(func):
    """Decorator to log function errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            monitoring.logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            sentry_sdk.capture_exception(e)
            raise
    return wrapper

# Global monitoring instance
monitoring = MonitoringConfig()
