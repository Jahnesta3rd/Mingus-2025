"""
MINGUS Application - Comprehensive Audit Logger
===============================================

Advanced audit logging system for financial compliance and security monitoring.
Provides comprehensive tracking of all financial transactions, user activities,
and security events with minimal performance impact.

Features:
- Real-time and background audit logging
- Financial transaction tracking with full context
- User activity logging with IP and session tracking
- Security event detection and logging
- Structured JSON logging format
- Performance-optimized logging
- Integration with existing security systems

Author: MINGUS Development Team
Date: January 2025
License: Proprietary - MINGUS Financial Services
"""

import os
import json
import logging
import uuid
import hashlib
import hmac
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import traceback
from contextlib import contextmanager

from flask import current_app, request, g, session
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.audit import (
    AuditLog, FinancialTransactionAudit, UserActivityAudit,
    SecurityEventAudit, ComplianceReport
)
from ..database import get_db_session
from ..tasks.audit_tasks import log_audit_event_async

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types for comprehensive tracking"""
    # Financial Events
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REFUNDED = "payment_refunded"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    INVOICE_GENERATED = "invoice_generated"
    INVOICE_PAID = "invoice_paid"
    
    # User Activity Events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    PREFERENCES_UPDATE = "preferences_update"
    
    # Data Access Events
    DATA_VIEWED = "data_viewed"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    
    # Security Events
    LOGIN_ATTEMPT = "login_attempt"
    FAILED_LOGIN = "failed_login"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    IP_BLOCKED = "ip_blocked"
    SESSION_EXPIRED = "session_expired"
    
    # Compliance Events
    GDPR_CONSENT_GIVEN = "gdpr_consent_given"
    GDPR_CONSENT_WITHDRAWN = "gdpr_consent_withdrawn"
    DATA_RETENTION_POLICY = "data_retention_policy"
    COMPLIANCE_REPORT_GENERATED = "compliance_report_generated"
    AUDIT_TRAIL_EXPORTED = "audit_trail_exported"


class AuditSeverity(Enum):
    """Audit severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class AuditCategory(Enum):
    """Audit categories for organization"""
    FINANCIAL = "financial"
    USER_ACTIVITY = "user_activity"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    SYSTEM = "system"
    DATA_ACCESS = "data_access"
    PAYMENT = "payment"
    SUBSCRIPTION = "subscription"


@dataclass
class AuditContext:
    """Context information for audit events"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FinancialTransactionData:
    """Financial transaction specific data"""
    transaction_id: str
    amount: int  # Amount in cents
    currency: str
    payment_method: str
    stripe_payment_intent_id: Optional[str] = None
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None
    invoice_id: Optional[str] = None
    status: str = "pending"
    failure_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditLogger:
    """
    Comprehensive audit logger for MINGUS financial application.
    
    Provides real-time and background logging capabilities with minimal
    performance impact on user operations.
    """
    
    def __init__(self, app=None, db_session: Optional[Session] = None):
        self.app = app
        self.db_session = db_session
        self.enable_async_logging = True
        self.enable_real_time_logging = True
        self.batch_size = 100
        self.retention_days = 2555  # 7 years for financial compliance
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the audit logger with Flask app"""
        self.app = app
        self.enable_async_logging = app.config.get('AUDIT_ASYNC_LOGGING', True)
        self.enable_real_time_logging = app.config.get('AUDIT_REAL_TIME_LOGGING', True)
        self.batch_size = app.config.get('AUDIT_BATCH_SIZE', 100)
        self.retention_days = app.config.get('AUDIT_RETENTION_DAYS', 2555)
        
        # Register cleanup task
        if hasattr(app, 'extensions') and 'celery' in app.extensions:
            self._schedule_cleanup_task()
    
    def _get_request_context(self) -> AuditContext:
        """Extract context information from current request"""
        try:
            return AuditContext(
                user_id=getattr(g, 'user_id', None) or 
                        getattr(session, 'user_id', None),
                session_id=session.get('session_id') if session else None,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get('User-Agent') if request else None,
                request_id=getattr(g, 'request_id', None),
                correlation_id=request.headers.get('X-Correlation-ID') if request else None,
                source=request.endpoint if request else None,
                metadata={
                    'method': request.method if request else None,
                    'url': request.url if request else None,
                    'headers': dict(request.headers) if request else None
                } if request else None
            )
        except Exception as e:
            logger.warning(f"Failed to extract request context: {e}")
            return AuditContext()
    
    def _generate_audit_id(self) -> str:
        """Generate unique audit ID"""
        return str(uuid.uuid4())
    
    def _calculate_hash(self, data: str) -> str:
        """Calculate SHA-256 hash of audit data for integrity"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format timestamp in ISO format with timezone"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    
    def log_event(
        self,
        event_type: AuditEventType,
        category: AuditCategory,
        severity: AuditSeverity,
        description: str,
        context: Optional[AuditContext] = None,
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        async_logging: bool = None
    ) -> str:
        """
        Log an audit event with comprehensive context.
        
        Args:
            event_type: Type of audit event
            category: Category of the event
            severity: Severity level
            description: Human-readable description
            context: Additional context information
            data: Event-specific data
            user_id: User ID (overrides context user_id)
            async_logging: Whether to use async logging (defaults to instance setting)
        
        Returns:
            Audit log ID
        """
        try:
            # Use provided user_id or extract from context
            if user_id is None and context:
                user_id = context.user_id
            
            # Extract context from request if not provided
            if context is None:
                context = self._get_request_context()
                if user_id is None:
                    user_id = context.user_id
            
            # Generate audit ID
            audit_id = self._generate_audit_id()
            
            # Prepare audit record
            audit_record = {
                'audit_id': audit_id,
                'timestamp': self._format_timestamp(datetime.now(timezone.utc)),
                'event_type': event_type.value,
                'category': category.value,
                'severity': severity.value,
                'description': description,
                'user_id': user_id,
                'session_id': context.session_id if context else None,
                'ip_address': context.ip_address if context else None,
                'user_agent': context.user_agent if context else None,
                'request_id': context.request_id if context else None,
                'correlation_id': context.correlation_id if context else None,
                'source': context.source if context else None,
                'data': data or {},
                'metadata': context.metadata if context else {},
                'hash': None  # Will be calculated after JSON serialization
            }
            
            # Calculate integrity hash
            json_data = json.dumps(audit_record, sort_keys=True, default=str)
            audit_record['hash'] = self._calculate_hash(json_data)
            
            # Determine logging method
            if async_logging is None:
                async_logging = self.enable_async_logging
            
            if async_logging and self.enable_async_logging:
                # Use background task for logging
                self._log_async(audit_record)
            else:
                # Use real-time logging
                self._log_sync(audit_record)
            
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Fallback to basic logging
            logger.error(f"AUDIT_FAILURE: {event_type.value} - {description} - {e}")
            return str(uuid.uuid4())
    
    def _log_sync(self, audit_record: Dict[str, Any]):
        """Synchronous logging to database"""
        try:
            if self.db_session:
                # Create audit log record
                audit_log = AuditLog(
                    audit_id=audit_record['audit_id'],
                    timestamp=datetime.fromisoformat(audit_record['timestamp']),
                    event_type=audit_record['event_type'],
                    category=audit_record['category'],
                    severity=audit_record['severity'],
                    description=audit_record['description'],
                    user_id=audit_record['user_id'],
                    session_id=audit_record['session_id'],
                    ip_address=audit_record['ip_address'],
                    user_agent=audit_record['user_agent'],
                    request_id=audit_record['request_id'],
                    correlation_id=audit_record['correlation_id'],
                    source=audit_record['source'],
                    data=audit_record['data'],
                    metadata=audit_record['metadata'],
                    hash=audit_record['hash']
                )
                
                self.db_session.add(audit_log)
                self.db_session.commit()
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in sync audit logging: {e}")
            self.db_session.rollback()
        except Exception as e:
            logger.error(f"Unexpected error in sync audit logging: {e}")
    
    def _log_async(self, audit_record: Dict[str, Any]):
        """Asynchronous logging using Celery task"""
        try:
            if hasattr(current_app, 'extensions') and 'celery' in current_app.extensions:
                log_audit_event_async.delay(audit_record)
            else:
                # Fallback to sync logging if Celery not available
                self._log_sync(audit_record)
        except Exception as e:
            logger.error(f"Failed to queue async audit log: {e}")
            # Fallback to sync logging
            self._log_sync(audit_record)
    
    def log_financial_transaction(
        self,
        transaction_data: FinancialTransactionData,
        context: Optional[AuditContext] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Log financial transaction with comprehensive details.
        
        Args:
            transaction_data: Financial transaction information
            context: Additional context
            user_id: User ID
        
        Returns:
            Audit log ID
        """
        # Determine event type based on status
        if transaction_data.status == "succeeded":
            event_type = AuditEventType.PAYMENT_COMPLETED
            severity = AuditSeverity.INFO
        elif transaction_data.status == "failed":
            event_type = AuditEventType.PAYMENT_FAILED
            severity = AuditSeverity.ERROR
        elif transaction_data.status == "refunded":
            event_type = AuditEventType.PAYMENT_REFUNDED
            severity = AuditSeverity.INFO
        else:
            event_type = AuditEventType.PAYMENT_INITIATED
            severity = AuditSeverity.INFO
        
        # Prepare financial data
        financial_data = {
            'transaction_id': transaction_data.transaction_id,
            'amount': transaction_data.amount,
            'currency': transaction_data.currency,
            'payment_method': transaction_data.payment_method,
            'stripe_payment_intent_id': transaction_data.stripe_payment_intent_id,
            'customer_id': transaction_data.customer_id,
            'subscription_id': transaction_data.subscription_id,
            'invoice_id': transaction_data.invoice_id,
            'status': transaction_data.status,
            'failure_reason': transaction_data.failure_reason,
            'metadata': transaction_data.metadata or {}
        }
        
        description = f"Financial transaction {transaction_data.status}: {transaction_data.amount} {transaction_data.currency}"
        if transaction_data.failure_reason:
            description += f" - {transaction_data.failure_reason}"
        
        return self.log_event(
            event_type=event_type,
            category=AuditCategory.FINANCIAL,
            severity=severity,
            description=description,
            context=context,
            data=financial_data,
            user_id=user_id
        )
    
    def log_user_activity(
        self,
        activity_type: AuditEventType,
        description: str,
        user_id: str,
        data: Optional[Dict[str, Any]] = None,
        context: Optional[AuditContext] = None
    ) -> str:
        """
        Log user activity with context.
        
        Args:
            activity_type: Type of user activity
            description: Activity description
            user_id: User ID
            data: Activity-specific data
            context: Additional context
        
        Returns:
            Audit log ID
        """
        return self.log_event(
            event_type=activity_type,
            category=AuditCategory.USER_ACTIVITY,
            severity=AuditSeverity.INFO,
            description=description,
            context=context,
            data=data or {},
            user_id=user_id
        )
    
    def log_security_event(
        self,
        event_type: AuditEventType,
        description: str,
        severity: AuditSeverity = AuditSeverity.SECURITY,
        context: Optional[AuditContext] = None,
        data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Log security event with appropriate severity.
        
        Args:
            event_type: Type of security event
            description: Event description
            severity: Security severity level
            context: Additional context
            data: Event-specific data
            user_id: User ID
        
        Returns:
            Audit log ID
        """
        return self.log_event(
            event_type=event_type,
            category=AuditCategory.SECURITY,
            severity=severity,
            description=description,
            context=context,
            data=data or {},
            user_id=user_id
        )
    
    def log_compliance_event(
        self,
        event_type: AuditEventType,
        description: str,
        data: Optional[Dict[str, Any]] = None,
        context: Optional[AuditContext] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Log compliance-related event.
        
        Args:
            event_type: Type of compliance event
            description: Event description
            data: Compliance data
            context: Additional context
            user_id: User ID
        
        Returns:
            Audit log ID
        """
        return self.log_event(
            event_type=event_type,
            category=AuditCategory.COMPLIANCE,
            severity=AuditSeverity.COMPLIANCE,
            description=description,
            context=context,
            data=data or {},
            user_id=user_id
        )
    
    def _schedule_cleanup_task(self):
        """Schedule cleanup task for old audit logs"""
        try:
            if hasattr(current_app, 'extensions') and 'celery' in current_app.extensions:
                from ..tasks.audit_tasks import cleanup_old_audit_logs
                # Schedule daily cleanup
                cleanup_old_audit_logs.apply_async(countdown=86400)  # 24 hours
        except Exception as e:
            logger.warning(f"Failed to schedule audit cleanup task: {e}")
    
    def get_audit_summary(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        categories: Optional[List[AuditCategory]] = None
    ) -> Dict[str, Any]:
        """
        Get audit summary for reporting and analysis.
        
        Args:
            user_id: Filter by user ID
            start_date: Start date for filtering
            end_date: End date for filtering
            event_types: Filter by event types
            categories: Filter by categories
        
        Returns:
            Audit summary statistics
        """
        try:
            if not self.db_session:
                return {"error": "No database session available"}
            
            # Build query filters
            filters = []
            if user_id:
                filters.append(AuditLog.user_id == user_id)
            if start_date:
                filters.append(AuditLog.timestamp >= start_date)
            if end_date:
                filters.append(AuditLog.timestamp <= end_date)
            if event_types:
                filters.append(AuditLog.event_type.in_([et.value for et in event_types]))
            if categories:
                filters.append(AuditLog.category.in_([cat.value for cat in categories]))
            
            # Get counts by category
            category_counts = {}
            for category in AuditCategory:
                count = self.db_session.query(AuditLog).filter(
                    *filters,
                    AuditLog.category == category.value
                ).count()
                category_counts[category.value] = count
            
            # Get counts by severity
            severity_counts = {}
            for severity in AuditSeverity:
                count = self.db_session.query(AuditLog).filter(
                    *filters,
                    AuditLog.severity == severity.value
                ).count()
                severity_counts[severity.value] = count
            
            return {
                "total_events": sum(category_counts.values()),
                "category_counts": category_counts,
                "severity_counts": severity_counts,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                },
                "filters_applied": {
                    "user_id": user_id,
                    "event_types": [et.value for et in event_types] if event_types else None,
                    "categories": [cat.value for cat in categories] if categories else None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit summary: {e}")
            return {"error": str(e)}
    
    def verify_audit_integrity(self, audit_id: str) -> bool:
        """
        Verify the integrity of an audit log entry.
        
        Args:
            audit_id: Audit log ID to verify
        
        Returns:
            True if integrity is verified, False otherwise
        """
        try:
            if not self.db_session:
                return False
            
            audit_log = self.db_session.query(AuditLog).filter(
                AuditLog.audit_id == audit_id
            ).first()
            
            if not audit_log:
                return False
            
            # Recalculate hash
            audit_data = asdict(audit_log)
            audit_data.pop('hash', None)  # Remove existing hash
            json_data = json.dumps(audit_data, sort_keys=True, default=str)
            calculated_hash = self._calculate_hash(json_data)
            
            return calculated_hash == audit_log.hash
            
        except Exception as e:
            logger.error(f"Failed to verify audit integrity: {e}")
            return False


# Global audit logger instance
audit_logger = AuditLogger()

# Decorator for automatic audit logging
def audit_log(
    event_type: AuditEventType,
    category: AuditCategory,
    severity: AuditSeverity = AuditSeverity.INFO,
    description: Optional[str] = None,
    data_extractor: Optional[callable] = None
):
    """
    Decorator for automatic audit logging of function calls.
    
    Args:
        event_type: Type of audit event
        category: Category of the event
        severity: Severity level
        description: Event description (can use function name if None)
        data_extractor: Function to extract additional data from function args/kwargs
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Extract user_id from function arguments or context
                user_id = None
                if 'user_id' in kwargs:
                    user_id = kwargs['user_id']
                elif args and hasattr(args[0], 'user_id'):
                    user_id = args[0].user_id
                
                # Extract additional data if extractor provided
                data = None
                if data_extractor:
                    try:
                        data = data_extractor(*args, **kwargs)
                    except Exception as e:
                        logger.warning(f"Data extraction failed: {e}")
                
                # Log function entry
                func_name = description or func.__name__
                audit_logger.log_event(
                    event_type=event_type,
                    category=category,
                    severity=severity,
                    description=f"Function called: {func_name}",
                    data=data,
                    user_id=user_id
                )
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Log successful completion
                audit_logger.log_event(
                    event_type=event_type,
                    category=category,
                    severity=AuditSeverity.INFO,
                    description=f"Function completed: {func_name}",
                    data=data,
                    user_id=user_id
                )
                
                return result
                
            except Exception as e:
                # Log function failure
                func_name = description or func.__name__
                audit_logger.log_event(
                    event_type=event_type,
                    category=category,
                    severity=AuditSeverity.ERROR,
                    description=f"Function failed: {func_name} - {str(e)}",
                    data=data,
                    user_id=user_id
                )
                raise
        
        return wrapper
    return decorator


# Context manager for audit logging
@contextmanager
def audit_context(
    event_type: AuditEventType,
    category: AuditCategory,
    description: str,
    user_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None
):
    """
    Context manager for audit logging of code blocks.
    
    Args:
        event_type: Type of audit event
        category: Category of the event
        description: Event description
        user_id: User ID
        data: Additional data
    """
    audit_id = None
    try:
        # Log entry
        audit_id = audit_logger.log_event(
            event_type=event_type,
            category=category,
            severity=AuditSeverity.INFO,
            description=f"Started: {description}",
            data=data,
            user_id=user_id
        )
        
        yield audit_id
        
        # Log successful completion
        audit_logger.log_event(
            event_type=event_type,
            category=category,
            severity=AuditSeverity.INFO,
            description=f"Completed: {description}",
            data=data,
            user_id=user_id
        )
        
    except Exception as e:
        # Log failure
        if audit_id:
            audit_logger.log_event(
                event_type=event_type,
                category=category,
                severity=AuditSeverity.ERROR,
                description=f"Failed: {description} - {str(e)}",
                data=data,
                user_id=user_id
            )
        raise
