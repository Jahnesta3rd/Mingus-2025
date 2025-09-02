#!/usr/bin/env python3
"""
Payment Audit Logging System for PCI DSS Compliance
Comprehensive audit logging for all payment-related activities
"""

import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from functools import wraps

from flask import request, session, g, current_app
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Payment audit event types"""
    PAYMENT_INTENT_CREATED = "payment_intent_created"
    PAYMENT_INTENT_CONFIRMED = "payment_intent_confirmed"
    PAYMENT_INTENT_FAILED = "payment_intent_failed"
    PAYMENT_INTENT_CANCELLED = "payment_intent_cancelled"
    PAYMENT_METHOD_ATTACHED = "payment_method_attached"
    PAYMENT_METHOD_DETACHED = "payment_method_detached"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    INVOICE_PAID = "invoice_paid"
    INVOICE_PAYMENT_FAILED = "invoice_payment_failed"
    REFUND_CREATED = "refund_created"
    CHARGE_DISPUTED = "charge_disputed"
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    ACCESS_ATTEMPT = "access_attempt"
    DATA_EXPORT = "data_export"
    DATA_DELETION = "data_deletion"

class AuditSeverity(Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PaymentAuditEvent:
    """Payment audit event data structure"""
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    user_agent: Optional[str]
    payment_intent_id: Optional[str]
    customer_id: Optional[str]
    subscription_id: Optional[str]
    amount: Optional[float]
    currency: Optional[str]
    success: bool
    error_message: Optional[str]
    metadata: Dict[str, Any]
    severity: AuditSeverity
    hash_signature: str
    source: str = "mingus_payment_system"

class PaymentAuditLogger:
    """Comprehensive payment audit logging for PCI DSS compliance"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or current_app.config.get('DATABASE_URL')
        self.engine = None
        self.SessionLocal = None
        self.secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
        self.siem_enabled = current_app.config.get('SIEM_ENABLED', False)
        self.siem_endpoint = current_app.config.get('SIEM_ENDPOINT')
        
        # Initialize database connection
        self._init_database()
        
        # Initialize audit tables
        self._create_audit_tables()
        
        logger.info("Payment audit logger initialized")
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Payment audit database connection established")
        except Exception as e:
            logger.error(f"Failed to initialize payment audit database: {e}")
            raise
    
    def _create_audit_tables(self):
        """Create audit logging tables"""
        try:
            with self.engine.connect() as conn:
                # Create payment audit log table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS payment_audit_log (
                        id SERIAL PRIMARY KEY,
                        event_id VARCHAR(255) UNIQUE NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        user_id VARCHAR(255),
                        session_id VARCHAR(255),
                        ip_address INET NOT NULL,
                        user_agent TEXT,
                        payment_intent_id VARCHAR(255),
                        customer_id VARCHAR(255),
                        subscription_id VARCHAR(255),
                        amount DECIMAL(10,2),
                        currency VARCHAR(3),
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        metadata JSONB,
                        severity VARCHAR(20) NOT NULL,
                        hash_signature VARCHAR(255) NOT NULL,
                        source VARCHAR(100) DEFAULT 'mingus_payment_system',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                
                # Create indexes for performance
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_payment_audit_timestamp 
                    ON payment_audit_log(timestamp)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_payment_audit_user_id 
                    ON payment_audit_log(user_id)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_payment_audit_event_type 
                    ON payment_audit_log(event_type)
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_payment_audit_payment_intent 
                    ON payment_audit_log(payment_intent_id)
                """))
                
                # Create audit log integrity table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_log_integrity (
                        id SERIAL PRIMARY KEY,
                        audit_date DATE NOT NULL,
                        total_events INTEGER NOT NULL,
                        hash_signature VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        UNIQUE(audit_date)
                    )
                """))
                
                conn.commit()
                logger.info("Payment audit tables created successfully")
                
        except Exception as e:
            logger.error(f"Failed to create payment audit tables: {e}")
            raise
    
    def log_payment_event(self, event_type: AuditEventType, user_id: Optional[str] = None,
                         payment_data: Dict[str, Any] = None, success: bool = True,
                         error_message: Optional[str] = None, severity: AuditSeverity = AuditSeverity.MEDIUM) -> str:
        """
        Log payment-related event for PCI DSS compliance
        
        Args:
            event_type: Type of payment event
            user_id: User ID associated with the event
            payment_data: Payment-related data
            success: Whether the operation was successful
            error_message: Error message if operation failed
            severity: Severity level of the event
            
        Returns:
            Event ID of the logged event
        """
        try:
            # Generate unique event ID
            event_id = self._generate_event_id()
            
            # Extract payment data
            payment_intent_id = payment_data.get('payment_intent_id') if payment_data else None
            customer_id = payment_data.get('customer_id') if payment_data else None
            subscription_id = payment_data.get('subscription_id') if payment_data else None
            amount = payment_data.get('amount') if payment_data else None
            currency = payment_data.get('currency') if payment_data else None
            
            # Create audit event
            audit_event = PaymentAuditEvent(
                event_id=event_id,
                timestamp=datetime.utcnow(),
                event_type=event_type,
                user_id=user_id,
                session_id=session.get('session_id') if session else None,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                payment_intent_id=payment_intent_id,
                customer_id=customer_id,
                subscription_id=subscription_id,
                amount=amount,
                currency=currency,
                success=success,
                error_message=error_message,
                metadata=payment_data or {},
                severity=severity,
                hash_signature=self._generate_hash_signature(event_id, payment_data)
            )
            
            # Store in database
            self._store_audit_event(audit_event)
            
            # Send to SIEM if enabled
            if self.siem_enabled:
                self._send_to_siem(audit_event)
            
            # Log to application logs
            logger.info(f"Payment audit event logged: {event_type.value} - {event_id}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to log payment audit event: {e}")
            # Don't raise exception to avoid breaking payment flow
            return None
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = int(time.time() * 1000)
        random_component = hashlib.md5(f"{timestamp}{self.secret_key}".encode()).hexdigest()[:8]
        return f"pay_audit_{timestamp}_{random_component}"
    
    def _generate_hash_signature(self, event_id: str, data: Dict[str, Any]) -> str:
        """Generate hash signature for audit log integrity"""
        data_string = json.dumps(data, sort_keys=True) if data else ""
        message = f"{event_id}:{data_string}:{self.secret_key}"
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _store_audit_event(self, audit_event: PaymentAuditEvent):
        """Store audit event in database"""
        try:
            with self.SessionLocal() as db_session:
                db_session.execute(text("""
                    INSERT INTO payment_audit_log (
                        event_id, timestamp, event_type, user_id, session_id,
                        ip_address, user_agent, payment_intent_id, customer_id,
                        subscription_id, amount, currency, success, error_message,
                        metadata, severity, hash_signature, source
                    ) VALUES (
                        :event_id, :timestamp, :event_type, :user_id, :session_id,
                        :ip_address, :user_agent, :payment_intent_id, :customer_id,
                        :subscription_id, :amount, :currency, :success, :error_message,
                        :metadata, :severity, :hash_signature, :source
                    )
                """), {
                    'event_id': audit_event.event_id,
                    'timestamp': audit_event.timestamp,
                    'event_type': audit_event.event_type.value,
                    'user_id': audit_event.user_id,
                    'session_id': audit_event.session_id,
                    'ip_address': audit_event.ip_address,
                    'user_agent': audit_event.user_agent,
                    'payment_intent_id': audit_event.payment_intent_id,
                    'customer_id': audit_event.customer_id,
                    'subscription_id': audit_event.subscription_id,
                    'amount': audit_event.amount,
                    'currency': audit_event.currency,
                    'success': audit_event.success,
                    'error_message': audit_event.error_message,
                    'metadata': json.dumps(audit_event.metadata),
                    'severity': audit_event.severity.value,
                    'hash_signature': audit_event.hash_signature,
                    'source': audit_event.source
                })
                db_session.commit()
                
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
            raise
    
    def _send_to_siem(self, audit_event: PaymentAuditEvent):
        """Send audit event to SIEM system"""
        try:
            if not self.siem_endpoint:
                return
            
            # Prepare SIEM payload
            siem_payload = {
                'event_type': 'payment_audit',
                'timestamp': audit_event.timestamp.isoformat(),
                'source': 'mingus_payment_system',
                'severity': audit_event.severity.value,
                'data': asdict(audit_event)
            }
            
            # Send to SIEM (implement based on your SIEM system)
            # Example: requests.post(self.siem_endpoint, json=siem_payload)
            logger.debug(f"SIEM payload prepared: {siem_payload}")
            
        except Exception as e:
            logger.error(f"Failed to send to SIEM: {e}")
    
    def get_audit_events(self, user_id: Optional[str] = None, 
                        event_type: Optional[AuditEventType] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve audit events with filtering"""
        try:
            query = """
                SELECT * FROM payment_audit_log 
                WHERE 1=1
            """
            params = {}
            
            if user_id:
                query += " AND user_id = :user_id"
                params['user_id'] = user_id
            
            if event_type:
                query += " AND event_type = :event_type"
                params['event_type'] = event_type.value
            
            if start_date:
                query += " AND timestamp >= :start_date"
                params['start_date'] = start_date
            
            if end_date:
                query += " AND timestamp <= :end_date"
                params['end_date'] = end_date
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params['limit'] = limit
            
            with self.SessionLocal() as db_session:
                result = db_session.execute(text(query), params)
                events = []
                for row in result:
                    event_dict = dict(row._mapping)
                    # Parse JSON metadata
                    if event_dict.get('metadata'):
                        event_dict['metadata'] = json.loads(event_dict['metadata'])
                    events.append(event_dict)
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to retrieve audit events: {e}")
            return []
    
    def verify_audit_log_integrity(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Verify audit log integrity for compliance"""
        try:
            with self.SessionLocal() as db_session:
                # Get events in date range
                result = db_session.execute(text("""
                    SELECT event_id, hash_signature, metadata 
                    FROM payment_audit_log 
                    WHERE timestamp BETWEEN :start_date AND :end_date
                    ORDER BY timestamp
                """), {
                    'start_date': start_date,
                    'end_date': end_date
                })
                
                events = list(result)
                total_events = len(events)
                
                # Verify hash signatures
                integrity_verified = True
                failed_verifications = []
                
                for event in events:
                    expected_hash = self._generate_hash_signature(
                        event.event_id, 
                        json.loads(event.metadata) if event.metadata else {}
                    )
                    
                    if event.hash_signature != expected_hash:
                        integrity_verified = False
                        failed_verifications.append({
                            'event_id': event.event_id,
                            'expected_hash': expected_hash,
                            'actual_hash': event.hash_signature
                        })
                
                # Generate integrity hash for the period
                period_data = f"{start_date}:{end_date}:{total_events}"
                period_hash = hmac.new(
                    self.secret_key.encode(),
                    period_data.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                return {
                    'start_date': start_date,
                    'end_date': end_date,
                    'total_events': total_events,
                    'integrity_verified': integrity_verified,
                    'failed_verifications': failed_verifications,
                    'period_hash': period_hash
                }
                
        except Exception as e:
            logger.error(f"Failed to verify audit log integrity: {e}")
            return {
                'error': str(e),
                'integrity_verified': False
            }
    
    def cleanup_old_audit_logs(self, retention_days: int = 2555):  # 7 years for PCI DSS
        """Clean up old audit logs while maintaining compliance"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            with self.SessionLocal() as db_session:
                # Archive old logs before deletion (optional)
                # self._archive_old_logs(cutoff_date)
                
                # Delete old logs
                result = db_session.execute(text("""
                    DELETE FROM payment_audit_log 
                    WHERE timestamp < :cutoff_date
                """), {
                    'cutoff_date': cutoff_date
                })
                
                deleted_count = result.rowcount
                db_session.commit()
                
                logger.info(f"Cleaned up {deleted_count} old audit log entries")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")
            return 0

# Global audit logger instance
_payment_audit_logger = None

def get_payment_audit_logger() -> PaymentAuditLogger:
    """Get global payment audit logger instance"""
    global _payment_audit_logger
    if _payment_audit_logger is None:
        _payment_audit_logger = PaymentAuditLogger()
    return _payment_audit_logger

# Decorator for automatic payment event logging
def log_payment_event(event_type: AuditEventType, severity: AuditSeverity = AuditSeverity.MEDIUM):
    """Decorator to automatically log payment events"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            audit_logger = get_payment_audit_logger()
            user_id = g.get('current_user_id') if g else None
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Log successful event
                audit_logger.log_payment_event(
                    event_type=event_type,
                    user_id=user_id,
                    payment_data=kwargs,
                    success=True,
                    severity=severity
                )
                
                return result
                
            except Exception as e:
                # Log failed event
                audit_logger.log_payment_event(
                    event_type=event_type,
                    user_id=user_id,
                    payment_data=kwargs,
                    success=False,
                    error_message=str(e),
                    severity=severity
                )
                raise
        
        return wrapper
    return decorator
