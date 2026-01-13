#!/usr/bin/env python3
"""
Error Monitoring and Logging System
Comprehensive error tracking, logging, and alerting
"""

import os
import sys
import json
import logging
import logging.handlers
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum
import threading

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    DATABASE = "database"
    NETWORK = "network"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"
    UNKNOWN = "unknown"

@dataclass
class ErrorLog:
    """Error log entry"""
    timestamp: datetime
    severity: str
    category: str
    error_type: str
    error_message: str
    stack_trace: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: Optional[str] = None
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    request_ip: Optional[str] = None
    request_user_agent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class ErrorMonitor:
    """
    Comprehensive error monitoring and logging system
    
    Features:
    - Structured error logging
    - Error categorization and severity
    - Error aggregation and statistics
    - Alert generation
    - Integration with external services (Sentry)
    - Error history and search
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        enable_sentry: bool = False,
        sentry_dsn: Optional[str] = None,
        max_error_history: int = 10000
    ):
        """
        Initialize error monitor
        
        Args:
            log_dir: Directory for log files
            enable_sentry: Enable Sentry integration
            sentry_dsn: Sentry DSN (required if enable_sentry=True)
            max_error_history: Maximum number of errors to keep in memory
        """
        self.log_dir = log_dir
        self.enable_sentry = enable_sentry
        self.sentry_dsn = sentry_dsn
        self.max_error_history = max_error_history
        
        # Create logs directory
        os.makedirs(log_dir, exist_ok=True)
        
        # Error storage
        self.error_history = deque(maxlen=max_error_history)
        self.error_stats = {
            'total': 0,
            'by_severity': {severity.value: 0 for severity in ErrorSeverity},
            'by_category': {category.value: 0 for category in ErrorCategory},
            'by_hour': {},
            'recent_errors': []
        }
        
        # Alert thresholds (from environment or defaults)
        self.alert_thresholds = {
            'critical_per_hour': int(os.environ.get('ERROR_ALERT_CRITICAL_PER_HOUR', '10')),
            'high_per_hour': int(os.environ.get('ERROR_ALERT_HIGH_PER_HOUR', '50')),
            'total_per_hour': int(os.environ.get('ERROR_ALERT_TOTAL_PER_HOUR', '200'))
        }
        
        # Active alerts
        self.active_alerts = []
        
        # Initialize logging
        self._setup_logging()
        
        # Initialize Sentry if enabled
        if self.enable_sentry:
            self._setup_sentry()
    
    def _setup_logging(self):
        """Set up structured logging"""
        # Application logger
        self.app_logger = logging.getLogger('mingus.app')
        self.app_logger.setLevel(logging.INFO)
        
        # Error logger
        self.error_logger = logging.getLogger('mingus.errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        json_formatter = logging.Formatter(
            '%(message)s'  # JSON will be in message
        )
        
        # Application log file (all levels)
        app_log_file = os.path.join(self.log_dir, 'app.log')
        app_file_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        app_file_handler.setLevel(logging.INFO)
        app_file_handler.setFormatter(detailed_formatter)
        self.app_logger.addHandler(app_file_handler)
        
        # Error log file (errors only)
        error_log_file = os.path.join(self.log_dir, 'errors.log')
        error_file_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=20,  # Keep more error logs
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        self.error_logger.addHandler(error_file_handler)
        
        # JSON error log (for log aggregation)
        json_error_log_file = os.path.join(self.log_dir, 'errors.json.log')
        json_file_handler = logging.handlers.RotatingFileHandler(
            json_error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=20,
            encoding='utf-8'
        )
        json_file_handler.setLevel(logging.ERROR)
        json_file_handler.setFormatter(json_formatter)
        self.error_logger.addHandler(json_file_handler)
        
        # Console handler (for development)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(detailed_formatter)
        self.app_logger.addHandler(console_handler)
        
        # Suppress noisy loggers
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
    
    def _setup_sentry(self):
        """Initialize Sentry for error tracking"""
        if not self.sentry_dsn:
            logger.warning("Sentry enabled but DSN not provided")
            self.enable_sentry = False
            return
        
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                integrations=[
                    FlaskIntegration(),
                    SqlalchemyIntegration(),
                    LoggingIntegration(
                        level=logging.INFO,
                        event_level=logging.ERROR
                    )
                ],
                traces_sample_rate=0.1,  # 10% of transactions
                environment=os.environ.get('FLASK_ENV', 'production'),
                release=os.environ.get('APP_VERSION', '1.0.0'),
                before_send=self._sentry_before_send,
                max_breadcrumbs=50
            )
            logger.info("Sentry initialized successfully")
        except ImportError:
            logger.warning("sentry-sdk not installed. Install with: pip install sentry-sdk")
            self.enable_sentry = False
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            self.enable_sentry = False
    
    def _sentry_before_send(self, event, hint):
        """Filter events before sending to Sentry"""
        # Don't send low severity errors
        if 'level' in event:
            if event['level'] == 'info' or event['level'] == 'warning':
                return None
        
        # Add custom context
        event.setdefault('tags', {})['component'] = 'mingus-backend'
        
        return event
    
    def log_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_method: Optional[str] = None,
        request_path: Optional[str] = None,
        request_ip: Optional[str] = None,
        request_user_agent: Optional[str] = None
    ) -> ErrorLog:
        """
        Log an error with full context
        
        Args:
            error: Exception object
            severity: Error severity level
            category: Error category
            context: Additional context dictionary
            user_id: User ID (if available)
            session_id: Session ID (if available)
            endpoint: API endpoint where error occurred
            request_method: HTTP method
            request_path: Request path
            request_ip: Client IP address
            request_user_agent: User agent string
            
        Returns:
            ErrorLog object
        """
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        # Create error log entry
        error_log = ErrorLog(
            timestamp=datetime.now(),
            severity=severity.value,
            category=category.value,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            user_id=user_id,
            session_id=session_id,
            endpoint=endpoint,
            request_method=request_method,
            request_path=request_path,
            request_ip=request_ip,
            request_user_agent=request_user_agent,
            context=context or {}
        )
        
        # Store in history
        self.error_history.append(error_log)
        
        # Update statistics
        self._update_stats(error_log)
        
        # Log to file
        self._log_to_file(error_log)
        
        # Send to Sentry if enabled
        if self.enable_sentry:
            self._send_to_sentry(error_log, error)
        
        # Check for alerts
        self._check_alerts()
        
        return error_log
    
    def _update_stats(self, error_log: ErrorLog):
        """Update error statistics"""
        self.error_stats['total'] += 1
        self.error_stats['by_severity'][error_log.severity] += 1
        self.error_stats['by_category'][error_log.category] += 1
        
        # Update hourly stats
        hour_key = error_log.timestamp.strftime('%Y-%m-%d %H:00')
        if hour_key not in self.error_stats['by_hour']:
            self.error_stats['by_hour'][hour_key] = 0
        self.error_stats['by_hour'][hour_key] += 1
        
        # Update recent errors (last 100)
        self.error_stats['recent_errors'].append({
            'timestamp': error_log.timestamp.isoformat(),
            'severity': error_log.severity,
            'category': error_log.category,
            'error_type': error_log.error_type,
            'error_message': error_log.error_message[:200],  # Truncate long messages
            'endpoint': error_log.endpoint
        })
        if len(self.error_stats['recent_errors']) > 100:
            self.error_stats['recent_errors'].pop(0)
    
    def _log_to_file(self, error_log: ErrorLog):
        """Log error to file"""
        # Standard log format
        log_message = (
            f"ERROR | {error_log.error_type} | {error_log.severity.upper()} | "
            f"{error_log.category} | {error_log.error_message}"
        )
        if error_log.endpoint:
            log_message += f" | Endpoint: {error_log.endpoint}"
        if error_log.user_id:
            log_message += f" | User: {error_log.user_id}"
        
        self.error_logger.error(log_message, exc_info=False)
        
        # JSON format for log aggregation
        json_log = {
            'timestamp': error_log.timestamp.isoformat(),
            'severity': error_log.severity,
            'category': error_log.category,
            'error_type': error_log.error_type,
            'error_message': error_log.error_message,
            'stack_trace': error_log.stack_trace,
            'user_id': error_log.user_id,
            'session_id': error_log.session_id,
            'endpoint': error_log.endpoint,
            'request_method': error_log.request_method,
            'request_path': error_log.request_path,
            'request_ip': error_log.request_ip,
            'context': error_log.context
        }
        
        # Log JSON to separate file
        json_logger = logging.getLogger('mingus.errors.json')
        json_logger.error(json.dumps(json_log))
    
    def _send_to_sentry(self, error_log: ErrorLog, error: Exception):
        """Send error to Sentry"""
        try:
            import sentry_sdk
            
            with sentry_sdk.push_scope() as scope:
                # Set severity
                if error_log.severity == 'critical':
                    scope.level = 'fatal'
                elif error_log.severity == 'high':
                    scope.level = 'error'
                elif error_log.severity == 'medium':
                    scope.level = 'warning'
                else:
                    scope.level = 'info'
                
                # Add tags
                scope.set_tag('category', error_log.category)
                scope.set_tag('error_type', error_log.error_type)
                if error_log.endpoint:
                    scope.set_tag('endpoint', error_log.endpoint)
                
                # Add context
                scope.set_context('request', {
                    'method': error_log.request_method,
                    'path': error_log.request_path,
                    'ip': error_log.request_ip,
                    'user_agent': error_log.request_user_agent
                })
                
                if error_log.user_id:
                    scope.set_user({'id': error_log.user_id})
                
                if error_log.context:
                    scope.set_context('custom', error_log.context)
                
                # Capture exception
                sentry_sdk.capture_exception(error)
        except Exception as e:
            logger.debug(f"Error sending to Sentry: {e}")
    
    def _check_alerts(self):
        """Check for error rate alerts"""
        # Count errors in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_errors = [
            e for e in self.error_history
            if e.timestamp >= one_hour_ago
        ]
        
        critical_count = sum(1 for e in recent_errors if e.severity == 'critical')
        high_count = sum(1 for e in recent_errors if e.severity == 'high')
        total_count = len(recent_errors)
        
        # Check thresholds
        if critical_count >= self.alert_thresholds['critical_per_hour']:
            self._create_alert(
                'critical_errors',
                f"High critical error rate: {critical_count} critical errors in the last hour",
                'critical'
            )
        
        if high_count >= self.alert_thresholds['high_per_hour']:
            self._create_alert(
                'high_errors',
                f"High error rate: {high_count} high-severity errors in the last hour",
                'warning'
            )
        
        if total_count >= self.alert_thresholds['total_per_hour']:
            self._create_alert(
                'total_errors',
                f"Very high error rate: {total_count} total errors in the last hour",
                'warning'
            )
    
    def _create_alert(self, alert_type: str, message: str, level: str):
        """Create an alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if alert already exists
        existing = [a for a in self.active_alerts if a['type'] == alert_type]
        if not existing:
            self.active_alerts.append(alert)
            logger.warning(f"ALERT [{level.upper()}]: {message}")
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff]
        
        return {
            'total': len(recent_errors),
            'by_severity': {
                severity.value: sum(1 for e in recent_errors if e.severity == severity.value)
                for severity in ErrorSeverity
            },
            'by_category': {
                category.value: sum(1 for e in recent_errors if e.category == category.value)
                for category in ErrorCategory
            },
            'recent_errors': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'severity': e.severity,
                    'category': e.category,
                    'error_type': e.error_type,
                    'error_message': e.error_message[:200],
                    'endpoint': e.endpoint
                }
                for e in recent_errors[-50:]  # Last 50 errors
            ],
            'alerts': self.active_alerts
        }
    
    def get_errors(
        self,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get filtered error list"""
        errors = list(self.error_history)
        
        if severity:
            errors = [e for e in errors if e.severity == severity]
        
        if category:
            errors = [e for e in errors if e.category == category]
        
        # Sort by timestamp (newest first)
        errors.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [asdict(e) for e in errors[:limit]]
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Automatically categorize error based on type and message"""
        error_type = type(error).__name__.lower()
        error_message = str(error).lower()
        
        # Database errors (check both type and message)
        db_keywords = ['sql', 'database', 'db', 'query', 'connection pool', 'transaction']
        if any(db in error_type for db in db_keywords) or \
           any(db in error_message for db in db_keywords):
            return ErrorCategory.DATABASE
        
        # Network errors
        net_keywords = ['connection', 'timeout', 'network', 'http', 'request', 'socket']
        if any(net in error_type for net in net_keywords) or \
           any(net in error_message for net in net_keywords):
            return ErrorCategory.NETWORK
        
        # Validation errors
        val_keywords = ['validation', 'value', 'invalid', 'required', 'format', 'type']
        if any(val in error_type for val in val_keywords) or \
           any(val in error_message for val in val_keywords):
            return ErrorCategory.VALIDATION
        
        # Authentication errors
        auth_keywords = ['authentication', 'unauthorized', 'login', 'token', 'credential']
        if any(auth in error_type for auth in auth_keywords) or \
           any(auth in error_message for auth in auth_keywords):
            return ErrorCategory.AUTHENTICATION
        
        # Authorization errors
        authz_keywords = ['authorization', 'forbidden', 'permission', 'access', 'denied']
        if any(authz in error_type for authz in authz_keywords) or \
           any(authz in error_message for authz in authz_keywords):
            return ErrorCategory.AUTHORIZATION
        
        # External API errors
        api_keywords = ['api', 'external', 'third-party', 'service', 'endpoint']
        if any(api in error_message for api in api_keywords):
            return ErrorCategory.EXTERNAL_API
        
        return ErrorCategory.UNKNOWN
    
    def determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Automatically determine error severity"""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Critical: System failures, data corruption
        if any(crit in error_message for crit in ['corrupt', 'data loss', 'system failure', 'critical']):
            return ErrorSeverity.CRITICAL
        
        # High: Database errors, external API failures
        if category == ErrorCategory.DATABASE or category == ErrorCategory.EXTERNAL_API:
            return ErrorSeverity.HIGH
        
        # Medium: Validation, authentication (default)
        if category in [ErrorCategory.VALIDATION, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.MEDIUM
        
        # Low: Business logic, expected errors
        if category == ErrorCategory.BUSINESS_LOGIC:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM

# Global error monitor instance
_error_monitor: Optional[ErrorMonitor] = None

def get_error_monitor() -> ErrorMonitor:
    """Get or create global error monitor instance"""
    global _error_monitor
    if _error_monitor is None:
        _error_monitor = ErrorMonitor(
            log_dir=os.environ.get('LOG_DIR', 'logs'),
            enable_sentry=os.environ.get('ENABLE_SENTRY', 'false').lower() == 'true',
            sentry_dsn=os.environ.get('SENTRY_DSN'),
            max_error_history=int(os.environ.get('MAX_ERROR_HISTORY', '10000'))
        )
    return _error_monitor
