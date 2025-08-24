"""
Audit Trail Service for MINGUS
==============================

Comprehensive audit trail system for tracking webhook events, processing steps, and system actions:
- Event processing audit trails
- User action tracking
- System operation logging
- Compliance reporting
- Performance analysis
- Security monitoring

Author: MINGUS Development Team
Date: January 2025
"""

import logging
import time
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid
import threading

from ..config.base import Config

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types"""
    WEBHOOK_RECEIVED = "webhook_received"
    WEBHOOK_PROCESSED = "webhook_processed"
    WEBHOOK_FAILED = "webhook_failed"
    USER_ACTION = "user_action"
    SYSTEM_ACTION = "system_action"
    SECURITY_EVENT = "security_event"
    PERFORMANCE_EVENT = "performance_event"
    BUSINESS_LOGIC = "business_logic"
    PAYMENT_RECOVERY = "payment_recovery"
    FEATURE_ACCESS = "feature_access"
    NOTIFICATION_SENT = "notification_sent"


class AuditSeverity(Enum):
    """Audit event severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """Audit event categories"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"
    COMPLIANCE = "compliance"
    OPERATIONS = "operations"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    category: AuditCategory
    timestamp: datetime
    source: str
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    webhook_event_id: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    processing_time_ms: Optional[float] = None
    success: Optional[bool] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class AuditTrail:
    """Audit trail data structure"""
    trail_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    events: List[AuditEvent] = None
    summary: Dict[str, Any] = None
    metadata: Dict[str, Any] = None


@dataclass
class AuditQuery:
    """Audit query parameters"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_types: Optional[List[AuditEventType]] = None
    severities: Optional[List[AuditSeverity]] = None
    categories: Optional[List[AuditCategory]] = None
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    source: Optional[str] = None
    limit: int = 1000
    offset: int = 0


class AuditTrailService:
    """Comprehensive audit trail service"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Audit configuration
        self.audit_config = {
            'enabled': True,
            'retention_days': 365,
            'batch_size': 100,
            'flush_interval': 60,  # seconds
            'compression_enabled': True,
            'encryption_enabled': True,
            'real_time_logging': True,
            'performance_tracking': True,
            'security_monitoring': True,
            'compliance_reporting': True
        }
        
        # Audit event buffer
        self.event_buffer = []
        self.buffer_lock = threading.Lock()
        
        # Performance tracking
        self.performance_metrics = {
            'events_logged': 0,
            'events_flushed': 0,
            'buffer_size': 0,
            'processing_time_avg': 0.0
        }
        
        # Initialize audit tables
        self._initialize_audit_tables()
    
    def log_webhook_event(
        self,
        webhook_event_id: str,
        event_type: str,
        source: str,
        request_data: Dict[str, Any],
        processing_result: Dict[str, Any],
        processing_time_ms: float,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log webhook event processing"""
        try:
            # Determine audit event type
            if success:
                audit_event_type = AuditEventType.WEBHOOK_PROCESSED
                severity = AuditSeverity.INFO
            else:
                audit_event_type = AuditEventType.WEBHOOK_FAILED
                severity = AuditSeverity.ERROR
            
            # Create audit event
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=audit_event_type,
                severity=severity,
                category=AuditCategory.BUSINESS,
                timestamp=datetime.now(timezone.utc),
                source=source,
                webhook_event_id=webhook_event_id,
                description=f"Webhook {event_type} processing",
                details={
                    'webhook_type': event_type,
                    'request_data': self._sanitize_data(request_data),
                    'processing_result': self._sanitize_data(processing_result),
                    'processing_time_ms': processing_time_ms,
                    'success': success
                },
                metadata=metadata or {},
                processing_time_ms=processing_time_ms,
                success=success,
                error_message=error_message
            )
            
            # Log the event
            event_id = self._log_audit_event(audit_event)
            
            # Update performance metrics
            self._update_performance_metrics(processing_time_ms)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error logging webhook event: {e}")
            return None
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        description: str,
        details: Dict[str, Any],
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Log user action"""
        try:
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACTION,
                severity=AuditSeverity.INFO,
                category=AuditCategory.SECURITY,
                timestamp=datetime.now(timezone.utc),
                source="user_action",
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                description=description,
                details=self._sanitize_data(details),
                metadata={
                    'action': action,
                    'user_agent': user_agent
                },
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            
            return self._log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(f"Error logging user action: {e}")
            return None
    
    def log_system_action(
        self,
        action: str,
        description: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.INFO,
        category: AuditCategory = AuditCategory.SYSTEM,
        source: str = "system",
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Log system action"""
        try:
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.SYSTEM_ACTION,
                severity=severity,
                category=category,
                timestamp=datetime.now(timezone.utc),
                source=source,
                description=description,
                details=self._sanitize_data(details),
                metadata={'action': action},
                success=success,
                error_message=error_message
            )
            
            return self._log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(f"Error logging system action: {e}")
            return None
    
    def log_security_event(
        self,
        event_type: str,
        description: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.WARNING,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        threat_level: str = "low"
    ) -> str:
        """Log security event"""
        try:
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.SECURITY_EVENT,
                severity=severity,
                category=AuditCategory.SECURITY,
                timestamp=datetime.now(timezone.utc),
                source="security_monitor",
                user_id=user_id,
                description=description,
                details=self._sanitize_data(details),
                metadata={
                    'security_event_type': event_type,
                    'threat_level': threat_level
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return self._log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
            return None
    
    def log_performance_event(
        self,
        operation: str,
        duration_ms: float,
        details: Dict[str, Any],
        threshold_ms: Optional[float] = None,
        source: str = "performance_monitor"
    ) -> str:
        """Log performance event"""
        try:
            # Determine severity based on duration
            if threshold_ms and duration_ms > threshold_ms * 2:
                severity = AuditSeverity.ERROR
            elif threshold_ms and duration_ms > threshold_ms:
                severity = AuditSeverity.WARNING
            else:
                severity = AuditSeverity.INFO
            
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.PERFORMANCE_EVENT,
                severity=severity,
                category=AuditCategory.PERFORMANCE,
                timestamp=datetime.now(timezone.utc),
                source=source,
                description=f"Performance event: {operation}",
                details=self._sanitize_data(details),
                metadata={
                    'operation': operation,
                    'threshold_ms': threshold_ms
                },
                processing_time_ms=duration_ms
            )
            
            return self._log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(f"Error logging performance event: {e}")
            return None
    
    def log_business_logic_event(
        self,
        operation: str,
        description: str,
        details: Dict[str, Any],
        customer_id: Optional[str] = None,
        user_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Log business logic event"""
        try:
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.BUSINESS_LOGIC,
                severity=AuditSeverity.INFO,
                category=AuditCategory.BUSINESS,
                timestamp=datetime.now(timezone.utc),
                source="business_logic",
                customer_id=customer_id,
                user_id=user_id,
                description=description,
                details=self._sanitize_data(details),
                metadata={'operation': operation},
                success=success,
                error_message=error_message
            )
            
            return self._log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(f"Error logging business logic event: {e}")
            return None
    
    def log_payment_recovery_event(
        self,
        customer_id: str,
        recovery_action: str,
        details: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Log payment recovery event"""
        try:
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.PAYMENT_RECOVERY,
                severity=AuditSeverity.INFO,
                category=AuditCategory.BUSINESS,
                timestamp=datetime.now(timezone.utc),
                source="payment_recovery",
                customer_id=customer_id,
                description=f"Payment recovery: {recovery_action}",
                details=self._sanitize_data(details),
                metadata={'recovery_action': recovery_action},
                success=success,
                error_message=error_message
            )
            
            return self._log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(f"Error logging payment recovery event: {e}")
            return None
    
    def log_feature_access_event(
        self,
        user_id: str,
        feature: str,
        action: str,
        details: Dict[str, Any],
        success: bool = True
    ) -> str:
        """Log feature access event"""
        try:
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.FEATURE_ACCESS,
                severity=AuditSeverity.INFO,
                category=AuditCategory.SECURITY,
                timestamp=datetime.now(timezone.utc),
                source="feature_access",
                user_id=user_id,
                description=f"Feature access: {feature} - {action}",
                details=self._sanitize_data(details),
                metadata={
                    'feature': feature,
                    'action': action
                },
                success=success
            )
            
            return self._log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(f"Error logging feature access event: {e}")
            return None
    
    def log_notification_event(
        self,
        notification_type: str,
        recipient: str,
        details: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Log notification event"""
        try:
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.NOTIFICATION_SENT,
                severity=AuditSeverity.INFO,
                category=AuditCategory.BUSINESS,
                timestamp=datetime.now(timezone.utc),
                source="notification_service",
                description=f"Notification sent: {notification_type}",
                details=self._sanitize_data(details),
                metadata={
                    'notification_type': notification_type,
                    'recipient': recipient
                },
                success=success,
                error_message=error_message
            )
            
            return self._log_audit_event(audit_event)
            
        except Exception as e:
            logger.error(f"Error logging notification event: {e}")
            return None
    
    def query_audit_events(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events based on criteria"""
        try:
            # Build query conditions
            conditions = []
            params = {}
            
            if query.start_time:
                conditions.append("timestamp >= :start_time")
                params['start_time'] = query.start_time
            
            if query.end_time:
                conditions.append("timestamp <= :end_time")
                params['end_time'] = query.end_time
            
            if query.event_types:
                conditions.append("event_type IN :event_types")
                params['event_types'] = [et.value for et in query.event_types]
            
            if query.severities:
                conditions.append("severity IN :severities")
                params['severities'] = [s.value for s in query.severities]
            
            if query.categories:
                conditions.append("category IN :categories")
                params['categories'] = [c.value for c in query.categories]
            
            if query.user_id:
                conditions.append("user_id = :user_id")
                params['user_id'] = query.user_id
            
            if query.customer_id:
                conditions.append("customer_id = :customer_id")
                params['customer_id'] = query.customer_id
            
            if query.source:
                conditions.append("source = :source")
                params['source'] = query.source
            
            # Build SQL query
            sql = """
                SELECT * FROM audit_events
                WHERE 1=1
            """
            
            if conditions:
                sql += " AND " + " AND ".join(conditions)
            
            sql += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params['limit'] = query.limit
            params['offset'] = query.offset
            
            # Execute query
            result = self.db.execute(sql, params)
            events = []
            
            for row in result:
                event = AuditEvent(
                    event_id=row['event_id'],
                    event_type=AuditEventType(row['event_type']),
                    severity=AuditSeverity(row['severity']),
                    category=AuditCategory(row['category']),
                    timestamp=row['timestamp'],
                    source=row['source'],
                    user_id=row['user_id'],
                    customer_id=row['customer_id'],
                    session_id=row['session_id'],
                    request_id=row['request_id'],
                    webhook_event_id=row['webhook_event_id'],
                    description=row['description'],
                    details=json.loads(row['details']) if row['details'] else {},
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent'],
                    processing_time_ms=row['processing_time_ms'],
                    success=row['success'],
                    error_message=row['error_message'],
                    stack_trace=row['stack_trace']
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error querying audit events: {e}")
            return []
    
    def generate_audit_report(
        self,
        start_time: datetime,
        end_time: datetime,
        report_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate audit report"""
        try:
            query = AuditQuery(
                start_time=start_time,
                end_time=end_time,
                limit=10000
            )
            
            events = self.query_audit_events(query)
            
            # Generate report based on type
            if report_type == "comprehensive":
                return self._generate_comprehensive_report(events, start_time, end_time)
            elif report_type == "security":
                return self._generate_security_report(events, start_time, end_time)
            elif report_type == "performance":
                return self._generate_performance_report(events, start_time, end_time)
            elif report_type == "business":
                return self._generate_business_report(events, start_time, end_time)
            else:
                return self._generate_summary_report(events, start_time, end_time)
                
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_audit_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get audit statistics for the specified period"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days)
            
            query = AuditQuery(
                start_time=start_time,
                end_time=end_time,
                limit=100000
            )
            
            events = self.query_audit_events(query)
            
            # Calculate statistics
            total_events = len(events)
            events_by_type = {}
            events_by_severity = {}
            events_by_category = {}
            events_by_source = {}
            
            for event in events:
                # By type
                event_type = event.event_type.value
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
                
                # By severity
                severity = event.severity.value
                events_by_severity[severity] = events_by_severity.get(severity, 0) + 1
                
                # By category
                category = event.category.value
                events_by_category[category] = events_by_category.get(category, 0) + 1
                
                # By source
                source = event.source
                events_by_source[source] = events_by_source.get(source, 0) + 1
            
            return {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'days': days
                },
                'total_events': total_events,
                'events_by_type': events_by_type,
                'events_by_severity': events_by_severity,
                'events_by_category': events_by_category,
                'events_by_source': events_by_source,
                'daily_average': total_events / days if days > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {}
    
    # Private methods
    
    def _log_audit_event(self, audit_event: AuditEvent) -> str:
        """Log audit event to buffer and database"""
        try:
            # Add to buffer
            with self.buffer_lock:
                self.event_buffer.append(audit_event)
                self.performance_metrics['events_logged'] += 1
                self.performance_metrics['buffer_size'] = len(self.event_buffer)
            
            # Flush buffer if it's full
            if len(self.event_buffer) >= self.audit_config['batch_size']:
                self._flush_buffer()
            
            # Real-time logging if enabled
            if self.audit_config['real_time_logging']:
                self._log_to_console(audit_event)
            
            return audit_event.event_id
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            return None
    
    def _flush_buffer(self):
        """Flush audit event buffer to database"""
        try:
            with self.buffer_lock:
                if not self.event_buffer:
                    return
                
                events_to_flush = self.event_buffer.copy()
                self.event_buffer.clear()
                self.performance_metrics['buffer_size'] = 0
            
            # Insert events into database
            for event in events_to_flush:
                self._insert_audit_event(event)
            
            self.performance_metrics['events_flushed'] += len(events_to_flush)
            
        except Exception as e:
            logger.error(f"Error flushing audit buffer: {e}")
    
    def _insert_audit_event(self, audit_event: AuditEvent):
        """Insert audit event into database"""
        try:
            sql = """
                INSERT INTO audit_events (
                    event_id, event_type, severity, category, timestamp, source,
                    user_id, customer_id, session_id, request_id, webhook_event_id,
                    description, details, metadata, ip_address, user_agent,
                    processing_time_ms, success, error_message, stack_trace
                ) VALUES (
                    :event_id, :event_type, :severity, :category, :timestamp, :source,
                    :user_id, :customer_id, :session_id, :request_id, :webhook_event_id,
                    :description, :details, :metadata, :ip_address, :user_agent,
                    :processing_time_ms, :success, :error_message, :stack_trace
                )
            """
            
            params = {
                'event_id': audit_event.event_id,
                'event_type': audit_event.event_type.value,
                'severity': audit_event.severity.value,
                'category': audit_event.category.value,
                'timestamp': audit_event.timestamp,
                'source': audit_event.source,
                'user_id': audit_event.user_id,
                'customer_id': audit_event.customer_id,
                'session_id': audit_event.session_id,
                'request_id': audit_event.request_id,
                'webhook_event_id': audit_event.webhook_event_id,
                'description': audit_event.description,
                'details': json.dumps(audit_event.details) if audit_event.details else None,
                'metadata': json.dumps(audit_event.metadata) if audit_event.metadata else None,
                'ip_address': audit_event.ip_address,
                'user_agent': audit_event.user_agent,
                'processing_time_ms': audit_event.processing_time_ms,
                'success': audit_event.success,
                'error_message': audit_event.error_message,
                'stack_trace': audit_event.stack_trace
            }
            
            self.db.execute(sql, params)
            
        except Exception as e:
            logger.error(f"Error inserting audit event: {e}")
    
    def _initialize_audit_tables(self):
        """Initialize audit tables"""
        try:
            # Create audit_events table
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id VARCHAR(36) PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    category VARCHAR(20) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                    source VARCHAR(100) NOT NULL,
                    user_id VARCHAR(36),
                    customer_id VARCHAR(36),
                    session_id VARCHAR(100),
                    request_id VARCHAR(100),
                    webhook_event_id VARCHAR(100),
                    description TEXT,
                    details JSONB,
                    metadata JSONB,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    processing_time_ms FLOAT,
                    success BOOLEAN,
                    error_message TEXT,
                    stack_trace TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """
            
            self.db.execute(create_table_sql)
            
            # Create indexes
            index_sqls = [
                "CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_audit_events_event_type ON audit_events(event_type)",
                "CREATE INDEX IF NOT EXISTS idx_audit_events_severity ON audit_events(severity)",
                "CREATE INDEX IF NOT EXISTS idx_audit_events_category ON audit_events(category)",
                "CREATE INDEX IF NOT EXISTS idx_audit_events_user_id ON audit_events(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_events_customer_id ON audit_events(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_events_source ON audit_events(source)",
                "CREATE INDEX IF NOT EXISTS idx_audit_events_webhook_event_id ON audit_events(webhook_event_id)"
            ]
            
            for index_sql in index_sqls:
                self.db.execute(index_sql)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error initializing audit tables: {e}")
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data for audit logging"""
        try:
            if not data:
                return {}
            
            sanitized = data.copy()
            
            # Remove sensitive fields
            sensitive_fields = [
                'password', 'token', 'secret', 'key', 'api_key',
                'authorization', 'cookie', 'session', 'credit_card',
                'ssn', 'social_security', 'bank_account'
            ]
            
            for field in sensitive_fields:
                if field in sanitized:
                    sanitized[field] = '[REDACTED]'
            
            # Sanitize nested dictionaries
            for key, value in sanitized.items():
                if isinstance(value, dict):
                    sanitized[key] = self._sanitize_data(value)
                elif isinstance(value, list):
                    sanitized[key] = [
                        self._sanitize_data(item) if isinstance(item, dict) else item
                        for item in value
                    ]
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing data: {e}")
            return {'error': 'Data sanitization failed'}
    
    def _log_to_console(self, audit_event: AuditEvent):
        """Log audit event to console for real-time monitoring"""
        try:
            log_message = f"[AUDIT] {audit_event.event_type.value} - {audit_event.severity.value} - {audit_event.description}"
            
            if audit_event.severity == AuditSeverity.ERROR:
                logger.error(log_message)
            elif audit_event.severity == AuditSeverity.WARNING:
                logger.warning(log_message)
            elif audit_event.severity == AuditSeverity.INFO:
                logger.info(log_message)
            else:
                logger.debug(log_message)
                
        except Exception as e:
            logger.error(f"Error logging to console: {e}")
    
    def _update_performance_metrics(self, processing_time_ms: float):
        """Update performance metrics"""
        try:
            # Update average processing time
            current_avg = self.performance_metrics['processing_time_avg']
            total_events = self.performance_metrics['events_logged']
            
            if total_events > 0:
                new_avg = ((current_avg * (total_events - 1)) + processing_time_ms) / total_events
                self.performance_metrics['processing_time_avg'] = new_avg
            else:
                self.performance_metrics['processing_time_avg'] = processing_time_ms
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _generate_comprehensive_report(self, events: List[AuditEvent], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        try:
            # Calculate statistics
            total_events = len(events)
            events_by_type = {}
            events_by_severity = {}
            events_by_category = {}
            
            for event in events:
                # By type
                event_type = event.event_type.value
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
                
                # By severity
                severity = event.severity.value
                events_by_severity[severity] = events_by_severity.get(severity, 0) + 1
                
                # By category
                category = event.category.value
                events_by_category[category] = events_by_category.get(category, 0) + 1
            
            return {
                'report_type': 'comprehensive',
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'summary': {
                    'total_events': total_events,
                    'events_by_type': events_by_type,
                    'events_by_severity': events_by_severity,
                    'events_by_category': events_by_category
                },
                'events': [asdict(event) for event in events[:100]]  # Limit to 100 events
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {}
    
    def _generate_security_report(self, events: List[AuditEvent], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate security audit report"""
        try:
            security_events = [
                event for event in events
                if event.category == AuditCategory.SECURITY
            ]
            
            return {
                'report_type': 'security',
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'summary': {
                    'total_security_events': len(security_events),
                    'critical_events': len([e for e in security_events if e.severity == AuditSeverity.CRITICAL]),
                    'error_events': len([e for e in security_events if e.severity == AuditSeverity.ERROR]),
                    'warning_events': len([e for e in security_events if e.severity == AuditSeverity.WARNING])
                },
                'events': [asdict(event) for event in security_events[:50]]
            }
            
        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {}
    
    def _generate_performance_report(self, events: List[AuditEvent], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate performance audit report"""
        try:
            performance_events = [
                event for event in events
                if event.category == AuditCategory.PERFORMANCE
            ]
            
            # Calculate performance statistics
            processing_times = [
                event.processing_time_ms for event in performance_events
                if event.processing_time_ms is not None
            ]
            
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            max_processing_time = max(processing_times) if processing_times else 0
            min_processing_time = min(processing_times) if processing_times else 0
            
            return {
                'report_type': 'performance',
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'summary': {
                    'total_performance_events': len(performance_events),
                    'avg_processing_time_ms': avg_processing_time,
                    'max_processing_time_ms': max_processing_time,
                    'min_processing_time_ms': min_processing_time,
                    'slow_operations': len([e for e in performance_events if e.severity in [AuditSeverity.WARNING, AuditSeverity.ERROR]])
                },
                'events': [asdict(event) for event in performance_events[:50]]
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {}
    
    def _generate_business_report(self, events: List[AuditEvent], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate business audit report"""
        try:
            business_events = [
                event for event in events
                if event.category == AuditCategory.BUSINESS
            ]
            
            return {
                'report_type': 'business',
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'summary': {
                    'total_business_events': len(business_events),
                    'webhook_events': len([e for e in business_events if e.event_type == AuditEventType.WEBHOOK_PROCESSED]),
                    'failed_webhooks': len([e for e in business_events if e.event_type == AuditEventType.WEBHOOK_FAILED]),
                    'payment_recovery_events': len([e for e in business_events if e.event_type == AuditEventType.PAYMENT_RECOVERY]),
                    'notifications_sent': len([e for e in business_events if e.event_type == AuditEventType.NOTIFICATION_SENT])
                },
                'events': [asdict(event) for event in business_events[:50]]
            }
            
        except Exception as e:
            logger.error(f"Error generating business report: {e}")
            return {}
    
    def _generate_summary_report(self, events: List[AuditEvent], start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate summary audit report"""
        try:
            return {
                'report_type': 'summary',
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'summary': {
                    'total_events': len(events),
                    'events_by_category': {
                        category.value: len([e for e in events if e.category == category])
                        for category in AuditCategory
                    },
                    'events_by_severity': {
                        severity.value: len([e for e in events if e.severity == severity])
                        for severity in AuditSeverity
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            return {} 