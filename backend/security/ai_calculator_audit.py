"""
AI Calculator Audit Logging System

Comprehensive audit logging for AI Calculator operations including:
- Assessment submissions and modifications
- Data access and retrieval
- GDPR compliance activities
- Security events and suspicious behavior
- Data retention and deletion activities
- User consent management
- Rate limiting violations
- Vulnerability monitoring
"""

import logging
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from backend.security.audit_logging import AuditLoggingService, AuditEventType, LogCategory, LogSeverity

logger = logging.getLogger(__name__)


class AICalculatorAuditEventType(Enum):
    """AI Calculator specific audit event types"""
    ASSESSMENT_SUBMITTED = "assessment_submitted"
    ASSESSMENT_ACCESSED = "assessment_accessed"
    ASSESSMENT_MODIFIED = "assessment_modified"
    ASSESSMENT_DELETED = "assessment_deleted"
    
    GDPR_CONSENT_GRANTED = "gdpr_consent_granted"
    GDPR_CONSENT_WITHDRAWN = "gdpr_consent_withdrawn"
    GDPR_DATA_EXPORT = "gdpr_data_export"
    GDPR_DATA_DELETION = "gdpr_data_deletion"
    GDPR_ACCESS_REQUEST = "gdpr_access_request"
    
    SECURITY_RATE_LIMIT_EXCEEDED = "security_rate_limit_exceeded"
    SECURITY_SUSPICIOUS_BEHAVIOR = "security_suspicious_behavior"
    SECURITY_INPUT_VALIDATION_FAILED = "security_input_validation_failed"
    SECURITY_CSRF_VIOLATION = "security_csrf_violation"
    SECURITY_SQL_INJECTION_ATTEMPT = "security_sql_injection_attempt"
    SECURITY_XSS_ATTEMPT = "security_xss_attempt"
    
    DATA_RETENTION_CLEANUP = "data_retention_cleanup"
    DATA_ENCRYPTION = "data_encryption"
    DATA_DECRYPTION = "data_decryption"
    
    ANONYMOUS_ASSESSMENT = "anonymous_assessment"
    CONVERSION_TRACKED = "conversion_tracked"
    EMAIL_SENT = "email_sent"
    ANALYTICS_TRACKED = "analytics_tracked"


class AICalculatorAuditSeverity(Enum):
    """AI Calculator specific audit severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"


@dataclass
class AICalculatorAuditRecord:
    """AI Calculator audit record structure"""
    audit_id: str
    timestamp: datetime
    event_type: AICalculatorAuditEventType
    severity: AICalculatorAuditSeverity
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: str
    user_agent: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    assessment_id: Optional[str] = None
    data_encrypted: bool = False
    anonymous_user: bool = False
    gdpr_compliant: bool = True
    security_incident: bool = False


class AICalculatorAuditService:
    """Comprehensive audit service for AI Calculator"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.base_audit_service = AuditLoggingService(db_session)
        
        # Initialize audit table if not exists
        self._init_audit_table()
    
    def _init_audit_table(self):
        """Initialize AI Calculator audit table"""
        try:
            # Create AI Calculator specific audit table
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_calculator_audit_logs (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    audit_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    event_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    user_id UUID,
                    session_id VARCHAR(255),
                    ip_address VARCHAR(45) NOT NULL,
                    user_agent TEXT,
                    description TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    assessment_id UUID,
                    data_encrypted BOOLEAN DEFAULT FALSE,
                    anonymous_user BOOLEAN DEFAULT FALSE,
                    gdpr_compliant BOOLEAN DEFAULT TRUE,
                    security_incident BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            
            # Create indexes for performance
            self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_calculator_audit_timestamp 
                ON ai_calculator_audit_logs(timestamp)
            """))
            
            self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_calculator_audit_event_type 
                ON ai_calculator_audit_logs(event_type)
            """))
            
            self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_calculator_audit_user_id 
                ON ai_calculator_audit_logs(user_id)
            """))
            
            self.db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_ai_calculator_audit_security_incident 
                ON ai_calculator_audit_logs(security_incident)
            """))
            
            self.db.commit()
            logger.info("AI Calculator audit table initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI Calculator audit table: {e}")
            self.db.rollback()
    
    def log_event(self, event_type: AICalculatorAuditEventType, user_id: Optional[str],
                  description: str, metadata: Dict[str, Any] = None, 
                  severity: AICalculatorAuditSeverity = AICalculatorAuditSeverity.INFO,
                  assessment_id: Optional[str] = None, ip_address: str = None,
                  user_agent: str = None, session_id: str = None,
                  data_encrypted: bool = False, anonymous_user: bool = False,
                  gdpr_compliant: bool = True, security_incident: bool = False) -> bool:
        """Log AI Calculator audit event"""
        try:
            import uuid
            
            audit_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc)
            
            # Get request information if not provided
            if not ip_address:
                from flask import request
                ip_address = request.remote_addr or 'unknown'
            
            if not user_agent:
                from flask import request
                user_agent = request.headers.get('User-Agent', 'unknown')
            
            if not session_id:
                from flask import session
                session_id = session.get('session_id')
            
            # Create audit record
            audit_record = AICalculatorAuditRecord(
                audit_id=audit_id,
                timestamp=timestamp,
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                description=description,
                metadata=metadata or {},
                assessment_id=assessment_id,
                data_encrypted=data_encrypted,
                anonymous_user=anonymous_user,
                gdpr_compliant=gdpr_compliant,
                security_incident=security_incident
            )
            
            # Insert into database
            self.db.execute(text("""
                INSERT INTO ai_calculator_audit_logs (
                    audit_id, timestamp, event_type, severity, user_id, session_id,
                    ip_address, user_agent, description, metadata, assessment_id,
                    data_encrypted, anonymous_user, gdpr_compliant, security_incident
                ) VALUES (
                    :audit_id, :timestamp, :event_type, :severity, :user_id, :session_id,
                    :ip_address, :user_agent, :description, :metadata, :assessment_id,
                    :data_encrypted, :anonymous_user, :gdpr_compliant, :security_incident
                )
            """), {
                'audit_id': audit_record.audit_id,
                'timestamp': audit_record.timestamp,
                'event_type': audit_record.event_type.value,
                'severity': audit_record.severity.value,
                'user_id': audit_record.user_id,
                'session_id': audit_record.session_id,
                'ip_address': audit_record.ip_address,
                'user_agent': audit_record.user_agent,
                'description': audit_record.description,
                'metadata': json.dumps(audit_record.metadata),
                'assessment_id': audit_record.assessment_id,
                'data_encrypted': audit_record.data_encrypted,
                'anonymous_user': audit_record.anonymous_user,
                'gdpr_compliant': audit_record.gdpr_compliant,
                'security_incident': audit_record.security_incident
            })
            
            self.db.commit()
            
            # Also log to base audit service for integration
            self.base_audit_service.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=user_id,
                session_id=session_id,
                description=f"AI Calculator: {description}",
                metadata={
                    'ai_calculator_event_type': event_type.value,
                    'assessment_id': assessment_id,
                    'data_encrypted': data_encrypted,
                    'anonymous_user': anonymous_user,
                    'gdpr_compliant': gdpr_compliant,
                    'security_incident': security_incident,
                    **metadata or {}
                },
                severity=LogSeverity.INFO if severity == AICalculatorAuditSeverity.INFO else LogSeverity.WARNING
            )
            
            logger.info(f"AI Calculator audit event logged: {event_type.value} - {description}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log AI Calculator audit event: {e}")
            self.db.rollback()
            return False
    
    def log_assessment_submission(self, user_id: Optional[str], assessment_id: str,
                                 assessment_data: Dict[str, Any], ip_address: str = None,
                                 user_agent: str = None, anonymous_user: bool = False,
                                 data_encrypted: bool = True) -> bool:
        """Log assessment submission event"""
        return self.log_event(
            event_type=AICalculatorAuditEventType.ASSESSMENT_SUBMITTED,
            user_id=user_id,
            description=f"Assessment submitted: {assessment_id}",
            metadata={
                'assessment_id': assessment_id,
                'assessment_type': assessment_data.get('assessment_type', 'ai_job_risk'),
                'job_title': assessment_data.get('job_title'),
                'industry': assessment_data.get('industry'),
                'experience_level': assessment_data.get('experience_level'),
                'has_email': bool(assessment_data.get('email')),
                'has_location': bool(assessment_data.get('location'))
            },
            assessment_id=assessment_id,
            ip_address=ip_address,
            user_agent=user_agent,
            anonymous_user=anonymous_user,
            data_encrypted=data_encrypted,
            gdpr_compliant=not anonymous_user
        )
    
    def log_assessment_access(self, user_id: Optional[str], assessment_id: str,
                            ip_address: str = None, user_agent: str = None,
                            authorized: bool = True) -> bool:
        """Log assessment access event"""
        return self.log_event(
            event_type=AICalculatorAuditEventType.ASSESSMENT_ACCESSED,
            user_id=user_id,
            description=f"Assessment accessed: {assessment_id} (Authorized: {authorized})",
            metadata={
                'assessment_id': assessment_id,
                'authorized': authorized
            },
            assessment_id=assessment_id,
            ip_address=ip_address,
            user_agent=user_agent,
            security_incident=not authorized
        )
    
    def log_gdpr_consent(self, user_id: Optional[str], email: str, consent_types: List[str],
                        granted: bool, ip_address: str = None, user_agent: str = None) -> bool:
        """Log GDPR consent event"""
        event_type = (AICalculatorAuditEventType.GDPR_CONSENT_GRANTED if granted 
                     else AICalculatorAuditEventType.GDPR_CONSENT_WITHDRAWN)
        
        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            description=f"GDPR consent {'granted' if granted else 'withdrawn'}: {', '.join(consent_types)}",
            metadata={
                'email': email,
                'consent_types': consent_types,
                'granted': granted
            },
            ip_address=ip_address,
            user_agent=user_agent,
            gdpr_compliant=True
        )
    
    def log_gdpr_data_export(self, user_id: str, ip_address: str = None,
                            user_agent: str = None) -> bool:
        """Log GDPR data export event"""
        return self.log_event(
            event_type=AICalculatorAuditEventType.GDPR_DATA_EXPORT,
            user_id=user_id,
            description=f"GDPR data export requested for user: {user_id}",
            metadata={
                'user_id': user_id,
                'export_type': 'full_data_export'
            },
            ip_address=ip_address,
            user_agent=user_agent,
            gdpr_compliant=True
        )
    
    def log_gdpr_data_deletion(self, user_id: str, ip_address: str = None,
                              user_agent: str = None) -> bool:
        """Log GDPR data deletion event"""
        return self.log_event(
            event_type=AICalculatorAuditEventType.GDPR_DATA_DELETION,
            user_id=user_id,
            description=f"GDPR data deletion requested for user: {user_id}",
            metadata={
                'user_id': user_id,
                'deletion_type': 'full_data_deletion'
            },
            ip_address=ip_address,
            user_agent=user_agent,
            gdpr_compliant=True
        )
    
    def log_security_incident(self, event_type: AICalculatorAuditEventType,
                            user_id: Optional[str], description: str,
                            metadata: Dict[str, Any] = None, ip_address: str = None,
                            user_agent: str = None) -> bool:
        """Log security incident"""
        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            description=description,
            metadata=metadata or {},
            severity=AICalculatorAuditSeverity.SECURITY,
            ip_address=ip_address,
            user_agent=user_agent,
            security_incident=True
        )
    
    def log_rate_limit_violation(self, user_id: Optional[str], ip_address: str,
                                limit_type: str, current_count: int, limit: int,
                                user_agent: str = None) -> bool:
        """Log rate limit violation"""
        return self.log_security_incident(
            event_type=AICalculatorAuditEventType.SECURITY_RATE_LIMIT_EXCEEDED,
            user_id=user_id,
            description=f"Rate limit exceeded: {limit_type} ({current_count}/{limit})",
            metadata={
                'limit_type': limit_type,
                'current_count': current_count,
                'limit': limit,
                'ip_address': ip_address
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_suspicious_behavior(self, user_id: Optional[str], ip_address: str,
                               indicators: List[str], assessment_data: Dict[str, Any],
                               user_agent: str = None) -> bool:
        """Log suspicious behavior detection"""
        return self.log_security_incident(
            event_type=AICalculatorAuditEventType.SECURITY_SUSPICIOUS_BEHAVIOR,
            user_id=user_id,
            description=f"Suspicious behavior detected: {', '.join(indicators)}",
            metadata={
                'suspicious_indicators': indicators,
                'assessment_data_keys': list(assessment_data.keys()),
                'ip_address': ip_address
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_input_validation_failure(self, user_id: Optional[str], ip_address: str,
                                   validation_errors: List[str], input_data: Dict[str, Any],
                                   user_agent: str = None) -> bool:
        """Log input validation failure"""
        return self.log_security_incident(
            event_type=AICalculatorAuditEventType.SECURITY_INPUT_VALIDATION_FAILED,
            user_id=user_id,
            description=f"Input validation failed: {', '.join(validation_errors)}",
            metadata={
                'validation_errors': validation_errors,
                'input_data_keys': list(input_data.keys()),
                'ip_address': ip_address
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def log_data_retention_cleanup(self, deleted_counts: Dict[str, int],
                                 cutoff_date: datetime) -> bool:
        """Log data retention cleanup"""
        return self.log_event(
            event_type=AICalculatorAuditEventType.DATA_RETENTION_CLEANUP,
            user_id=None,
            description=f"Data retention cleanup completed: {deleted_counts}",
            metadata={
                'deleted_counts': deleted_counts,
                'cutoff_date': cutoff_date.isoformat()
            },
            severity=AICalculatorAuditSeverity.INFO
        )
    
    def get_audit_logs(self, user_id: Optional[str] = None, 
                      event_type: Optional[AICalculatorAuditEventType] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      security_incidents_only: bool = False,
                      limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering"""
        try:
            query = """
                SELECT * FROM ai_calculator_audit_logs 
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
            
            if security_incidents_only:
                query += " AND security_incident = TRUE"
            
            query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
            params['limit'] = limit
            params['offset'] = offset
            
            result = self.db.execute(text(query), params)
            logs = []
            
            for row in result:
                log_dict = dict(row._mapping)
                # Parse metadata JSON
                if log_dict.get('metadata'):
                    log_dict['metadata'] = json.loads(log_dict['metadata'])
                logs.append(log_dict)
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []
    
    def get_security_incidents(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get security incidents from the last N days"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            result = self.db.execute(text("""
                SELECT * FROM ai_calculator_audit_logs 
                WHERE security_incident = TRUE 
                AND timestamp >= :start_date
                ORDER BY timestamp DESC
            """), {'start_date': start_date})
            
            incidents = []
            for row in result:
                incident_dict = dict(row._mapping)
                if incident_dict.get('metadata'):
                    incident_dict['metadata'] = json.loads(incident_dict['metadata'])
                incidents.append(incident_dict)
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to retrieve security incidents: {e}")
            return []
    
    def get_gdpr_activity_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get GDPR activity summary"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            result = self.db.execute(text("""
                SELECT 
                    event_type,
                    COUNT(*) as count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM ai_calculator_audit_logs 
                WHERE event_type IN ('gdpr_consent_granted', 'gdpr_consent_withdrawn', 
                                   'gdpr_data_export', 'gdpr_data_deletion')
                AND timestamp >= :start_date
                GROUP BY event_type
            """), {'start_date': start_date})
            
            summary = {
                'consent_granted': 0,
                'consent_withdrawn': 0,
                'data_exports': 0,
                'data_deletions': 0,
                'unique_users_consent': 0,
                'unique_users_export': 0,
                'unique_users_deletion': 0
            }
            
            for row in result:
                event_type = row.event_type
                count = row.count
                unique_users = row.unique_users
                
                if event_type == 'gdpr_consent_granted':
                    summary['consent_granted'] = count
                    summary['unique_users_consent'] = max(summary['unique_users_consent'], unique_users)
                elif event_type == 'gdpr_consent_withdrawn':
                    summary['consent_withdrawn'] = count
                elif event_type == 'gdpr_data_export':
                    summary['data_exports'] = count
                    summary['unique_users_export'] = unique_users
                elif event_type == 'gdpr_data_deletion':
                    summary['data_deletions'] = count
                    summary['unique_users_deletion'] = unique_users
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get GDPR activity summary: {e}")
            return {}
    
    def get_assessment_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get assessment analytics from audit logs"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            result = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_submissions,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(CASE WHEN anonymous_user = TRUE THEN 1 END) as anonymous_submissions,
                    COUNT(CASE WHEN data_encrypted = TRUE THEN 1 END) as encrypted_submissions,
                    COUNT(CASE WHEN gdpr_compliant = TRUE THEN 1 END) as gdpr_compliant_submissions
                FROM ai_calculator_audit_logs 
                WHERE event_type = 'assessment_submitted'
                AND timestamp >= :start_date
            """), {'start_date': start_date})
            
            row = result.fetchone()
            if row:
                return {
                    'total_submissions': row.total_submissions,
                    'unique_users': row.unique_users,
                    'anonymous_submissions': row.anonymous_submissions,
                    'encrypted_submissions': row.encrypted_submissions,
                    'gdpr_compliant_submissions': row.gdpr_compliant_submissions,
                    'compliance_rate': (row.gdpr_compliant_submissions / row.total_submissions * 100) if row.total_submissions > 0 else 0,
                    'encryption_rate': (row.encrypted_submissions / row.total_submissions * 100) if row.total_submissions > 0 else 0
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get assessment analytics: {e}")
            return {}


# Convenience functions for common audit operations
def log_assessment_submission(user_id: Optional[str], assessment_id: str,
                            assessment_data: Dict[str, Any], **kwargs) -> bool:
    """Log assessment submission"""
    audit_service = AICalculatorAuditService(current_app.db.session)
    return audit_service.log_assessment_submission(user_id, assessment_id, assessment_data, **kwargs)


def log_security_incident(event_type: AICalculatorAuditEventType, user_id: Optional[str],
                         description: str, **kwargs) -> bool:
    """Log security incident"""
    audit_service = AICalculatorAuditService(current_app.db.session)
    return audit_service.log_security_incident(event_type, user_id, description, **kwargs)


def log_gdpr_activity(user_id: Optional[str], activity_type: str, **kwargs) -> bool:
    """Log GDPR activity"""
    audit_service = AICalculatorAuditService(current_app.db.session)
    
    if activity_type == 'consent_granted':
        return audit_service.log_gdpr_consent(user_id, granted=True, **kwargs)
    elif activity_type == 'consent_withdrawn':
        return audit_service.log_gdpr_consent(user_id, granted=False, **kwargs)
    elif activity_type == 'data_export':
        return audit_service.log_gdpr_data_export(user_id, **kwargs)
    elif activity_type == 'data_deletion':
        return audit_service.log_gdpr_data_deletion(user_id, **kwargs)
    
    return False
