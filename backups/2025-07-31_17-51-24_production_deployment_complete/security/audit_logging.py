"""
Audit Logging System

This module provides comprehensive audit logging for banking compliance,
including structured logging, data retention, and compliance reporting.
"""

import logging
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import hmac
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.security.banking_compliance import AuditEventType, ComplianceLevel

logger = logging.getLogger(__name__)


class LogSeverity(Enum):
    """Log severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogCategory(Enum):
    """Log categories for banking operations"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    BANKING_OPERATIONS = "banking_operations"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    SYSTEM = "system"


@dataclass
class AuditLogRecord:
    """Audit log record structure"""
    log_id: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    event_type: AuditEventType
    event_category: LogCategory
    severity: LogSeverity
    description: str
    resource_type: str
    resource_id: Optional[str]
    ip_address: str
    user_agent: str
    request_method: Optional[str]
    request_path: Optional[str]
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    compliance_level: ComplianceLevel = ComplianceLevel.INTERNAL
    data_classification: str = "confidential"
    retention_days: int = 2555  # 7 years default
    hash_signature: Optional[str] = None


@dataclass
class AuditLogQuery:
    """Audit log query parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    event_type: Optional[AuditEventType] = None
    event_category: Optional[LogCategory] = None
    severity: Optional[LogSeverity] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    compliance_level: Optional[ComplianceLevel] = None
    limit: int = 1000
    offset: int = 0


@dataclass
class ComplianceReport:
    """Compliance report structure"""
    report_id: str
    report_type: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_events: int
    events_by_category: Dict[str, int]
    events_by_severity: Dict[str, int]
    compliance_score: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    status: str


class AuditLoggingService:
    """Comprehensive audit logging service for banking compliance"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        
        # Initialize audit log storage (in production, this would be a dedicated table)
        self.audit_logs: List[AuditLogRecord] = []
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup structured logging configuration"""
        try:
            # Create structured formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Create file handler for audit logs
            audit_handler = logging.FileHandler('logs/audit.log')
            audit_handler.setLevel(logging.INFO)
            audit_handler.setFormatter(formatter)
            
            # Add handler to audit logger
            audit_logger = logging.getLogger('audit')
            audit_logger.addHandler(audit_handler)
            audit_logger.setLevel(logging.INFO)
            
        except Exception as e:
            self.logger.error(f"Error setting up logging: {e}")
    
    def log_event(self, event_type: AuditEventType, event_category: LogCategory,
                  severity: LogSeverity, description: str, resource_type: str,
                  user_id: Optional[str] = None, resource_id: Optional[str] = None,
                  ip_address: str = None, user_agent: str = None,
                  request_method: str = None, request_path: str = None,
                  request_headers: Dict[str, str] = None, request_body: str = None,
                  response_status: int = None, response_body: str = None,
                  metadata: Dict[str, Any] = None, compliance_level: ComplianceLevel = None) -> str:
        """Log an audit event"""
        try:
            # Generate unique log ID
            log_id = f"audit_{int(time.time())}_{self._generate_random_suffix()}"
            
            # Create audit log record
            audit_record = AuditLogRecord(
                log_id=log_id,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                session_id=self._get_session_id(),
                event_type=event_type,
                event_category=event_category,
                severity=severity,
                description=description,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address or "unknown",
                user_agent=user_agent or "unknown",
                request_method=request_method,
                request_path=request_path,
                request_headers=request_headers or {},
                request_body=self._sanitize_request_body(request_body),
                response_status=response_status,
                response_body=self._sanitize_response_body(response_body),
                metadata=metadata or {},
                compliance_level=compliance_level or ComplianceLevel.INTERNAL,
                retention_days=self._get_retention_days(event_type),
                hash_signature=self._generate_hash_signature(log_id, description)
            )
            
            # Store audit record
            self._store_audit_record(audit_record)
            
            # Log to structured logger
            self._log_to_structured_logger(audit_record)
            
            # Log to console for debugging
            self.logger.info(f"AUDIT: {event_type.value} - {description} - User: {user_id} - IP: {ip_address}")
            
            return log_id
            
        except Exception as e:
            self.logger.error(f"Error logging audit event: {e}")
            return None
    
    def _generate_random_suffix(self) -> str:
        """Generate random suffix for log ID"""
        import secrets
        return secrets.token_hex(4)
    
    def _get_session_id(self) -> Optional[str]:
        """Get current session ID"""
        try:
            # In a real implementation, this would get the session ID from Flask session
            return None
        except Exception:
            return None
    
    def _sanitize_request_body(self, body: str) -> Optional[str]:
        """Sanitize request body for logging"""
        try:
            if not body:
                return None
            
            # Remove sensitive fields from request body
            sensitive_fields = ['password', 'access_token', 'refresh_token', 'account_number', 'routing_number']
            
            try:
                data = json.loads(body)
                sanitized_data = self._remove_sensitive_fields(data, sensitive_fields)
                return json.dumps(sanitized_data)
            except json.JSONDecodeError:
                # If not JSON, return truncated string
                return body[:100] + "..." if len(body) > 100 else body
                
        except Exception as e:
            self.logger.error(f"Error sanitizing request body: {e}")
            return None
    
    def _sanitize_response_body(self, body: str) -> Optional[str]:
        """Sanitize response body for logging"""
        try:
            if not body:
                return None
            
            # Remove sensitive fields from response body
            sensitive_fields = ['access_token', 'refresh_token', 'account_number', 'routing_number', 'balance']
            
            try:
                data = json.loads(body)
                sanitized_data = self._remove_sensitive_fields(data, sensitive_fields)
                return json.dumps(sanitized_data)
            except json.JSONDecodeError:
                # If not JSON, return truncated string
                return body[:100] + "..." if len(body) > 100 else body
                
        except Exception as e:
            self.logger.error(f"Error sanitizing response body: {e}")
            return None
    
    def _remove_sensitive_fields(self, data: Any, sensitive_fields: List[str]) -> Any:
        """Recursively remove sensitive fields from data"""
        try:
            if isinstance(data, dict):
                sanitized = {}
                for key, value in data.items():
                    if key.lower() in [field.lower() for field in sensitive_fields]:
                        sanitized[key] = "***REDACTED***"
                    else:
                        sanitized[key] = self._remove_sensitive_fields(value, sensitive_fields)
                return sanitized
            elif isinstance(data, list):
                return [self._remove_sensitive_fields(item, sensitive_fields) for item in data]
            else:
                return data
                
        except Exception as e:
            self.logger.error(f"Error removing sensitive fields: {e}")
            return data
    
    def _get_retention_days(self, event_type: AuditEventType) -> int:
        """Get retention days for event type"""
        retention_map = {
            AuditEventType.DATA_ACCESS: 2555,  # 7 years
            AuditEventType.DATA_MODIFICATION: 2555,  # 7 years
            AuditEventType.AUTHENTICATION: 2555,  # 7 years
            AuditEventType.AUTHORIZATION: 2555,  # 7 years
            AuditEventType.ENCRYPTION: 1825,  # 5 years
            AuditEventType.DECRYPTION: 1825,  # 5 years
            AuditEventType.DATA_EXPORT: 2555,  # 7 years
            AuditEventType.DATA_DELETION: 2555,  # 7 years
            AuditEventType.COMPLIANCE_CHECK: 1825,  # 5 years
            AuditEventType.SECURITY_INCIDENT: 3650,  # 10 years
        }
        return retention_map.get(event_type, 2555)  # Default 7 years
    
    def _generate_hash_signature(self, log_id: str, description: str) -> str:
        """Generate hash signature for log integrity"""
        try:
            # Create signature from log ID and description
            message = f"{log_id}:{description}:{int(time.time())}"
            secret = "audit_log_secret"  # In production, use secure secret
            
            signature = hmac.new(
                secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            self.logger.error(f"Error generating hash signature: {e}")
            return None
    
    def _store_audit_record(self, record: AuditLogRecord):
        """Store audit record in database"""
        try:
            # In production, this would store in a dedicated audit_logs table
            self.audit_logs.append(record)
            
            # Keep only recent logs in memory (for demo purposes)
            if len(self.audit_logs) > 10000:
                self.audit_logs = self.audit_logs[-5000:]
                
        except Exception as e:
            self.logger.error(f"Error storing audit record: {e}")
    
    def _log_to_structured_logger(self, record: AuditLogRecord):
        """Log to structured logger"""
        try:
            audit_logger = logging.getLogger('audit')
            
            # Create structured log message
            log_data = {
                'log_id': record.log_id,
                'timestamp': record.timestamp.isoformat(),
                'user_id': record.user_id,
                'event_type': record.event_type.value,
                'event_category': record.event_category.value,
                'severity': record.severity.value,
                'description': record.description,
                'resource_type': record.resource_type,
                'resource_id': record.resource_id,
                'ip_address': record.ip_address,
                'user_agent': record.user_agent,
                'request_method': record.request_method,
                'request_path': record.request_path,
                'compliance_level': record.compliance_level.value,
                'hash_signature': record.hash_signature
            }
            
            # Log based on severity
            if record.severity == LogSeverity.CRITICAL:
                audit_logger.critical(json.dumps(log_data))
            elif record.severity == LogSeverity.ERROR:
                audit_logger.error(json.dumps(log_data))
            elif record.severity == LogSeverity.WARNING:
                audit_logger.warning(json.dumps(log_data))
            else:
                audit_logger.info(json.dumps(log_data))
                
        except Exception as e:
            self.logger.error(f"Error logging to structured logger: {e}")
    
    def query_audit_logs(self, query: AuditLogQuery) -> List[AuditLogRecord]:
        """Query audit logs based on criteria"""
        try:
            logs = self.audit_logs.copy()
            
            # Apply filters
            if query.start_date:
                logs = [log for log in logs if log.timestamp >= query.start_date]
            
            if query.end_date:
                logs = [log for log in logs if log.timestamp <= query.end_date]
            
            if query.user_id:
                logs = [log for log in logs if log.user_id == query.user_id]
            
            if query.event_type:
                logs = [log for log in logs if log.event_type == query.event_type]
            
            if query.event_category:
                logs = [log for log in logs if log.event_category == query.event_category]
            
            if query.severity:
                logs = [log for log in logs if log.severity == query.severity]
            
            if query.resource_type:
                logs = [log for log in logs if log.resource_type == query.resource_type]
            
            if query.resource_id:
                logs = [log for log in logs if log.resource_id == query.resource_id]
            
            if query.ip_address:
                logs = [log for log in logs if log.ip_address == query.ip_address]
            
            if query.compliance_level:
                logs = [log for log in logs if log.compliance_level == query.compliance_level]
            
            # Sort by timestamp (newest first)
            logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            start = query.offset
            end = start + query.limit
            logs = logs[start:end]
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Error querying audit logs: {e}")
            return []
    
    def generate_compliance_report(self, report_type: str, period_start: datetime,
                                 period_end: datetime) -> ComplianceReport:
        """Generate compliance report for specified period"""
        try:
            # Query logs for the period
            query = AuditLogQuery(
                start_date=period_start,
                end_date=period_end
            )
            logs = self.query_audit_logs(query)
            
            # Calculate statistics
            total_events = len(logs)
            
            events_by_category = {}
            events_by_severity = {}
            
            for log in logs:
                # Count by category
                category = log.event_category.value
                events_by_category[category] = events_by_category.get(category, 0) + 1
                
                # Count by severity
                severity = log.severity.value
                events_by_severity[severity] = events_by_severity.get(severity, 0) + 1
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(logs)
            
            # Generate findings
            findings = self._generate_findings(logs)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(findings, compliance_score)
            
            # Determine status
            if compliance_score >= 95:
                status = 'compliant'
            elif compliance_score >= 80:
                status = 'review_required'
            else:
                status = 'non_compliant'
            
            return ComplianceReport(
                report_id=f"compliance_{int(time.time())}",
                report_type=report_type,
                generated_at=datetime.utcnow(),
                period_start=period_start,
                period_end=period_end,
                total_events=total_events,
                events_by_category=events_by_category,
                events_by_severity=events_by_severity,
                compliance_score=compliance_score,
                findings=findings,
                recommendations=recommendations,
                status=status
            )
            
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {e}")
            raise
    
    def _calculate_compliance_score(self, logs: List[AuditLogRecord]) -> float:
        """Calculate compliance score based on audit logs"""
        try:
            if not logs:
                return 100.0
            
            total_events = len(logs)
            critical_events = len([log for log in logs if log.severity == LogSeverity.CRITICAL])
            error_events = len([log for log in logs if log.severity == LogSeverity.ERROR])
            warning_events = len([log for log in logs if log.severity == LogSeverity.WARNING])
            
            # Calculate score (critical events have highest weight)
            score = 100.0
            score -= (critical_events * 10)  # -10 points per critical event
            score -= (error_events * 5)      # -5 points per error event
            score -= (warning_events * 1)    # -1 point per warning event
            
            return max(0.0, score)
            
        except Exception as e:
            self.logger.error(f"Error calculating compliance score: {e}")
            return 0.0
    
    def _generate_findings(self, logs: List[AuditLogRecord]) -> List[Dict[str, Any]]:
        """Generate findings from audit logs"""
        try:
            findings = []
            
            # Check for critical security events
            critical_events = [log for log in logs if log.severity == LogSeverity.CRITICAL]
            if critical_events:
                findings.append({
                    'type': 'critical_security_events',
                    'count': len(critical_events),
                    'description': f"Found {len(critical_events)} critical security events",
                    'severity': 'high',
                    'events': [log.log_id for log in critical_events[:5]]  # First 5
                })
            
            # Check for unauthorized access attempts
            auth_events = [log for log in logs if log.event_type == AuditEventType.AUTHORIZATION]
            failed_auth = [log for log in auth_events if 'unauthorized' in log.description.lower()]
            if failed_auth:
                findings.append({
                    'type': 'unauthorized_access_attempts',
                    'count': len(failed_auth),
                    'description': f"Found {len(failed_auth)} unauthorized access attempts",
                    'severity': 'medium',
                    'events': [log.log_id for log in failed_auth[:5]]
                })
            
            # Check for data access patterns
            data_access_events = [log for log in logs if log.event_type == AuditEventType.DATA_ACCESS]
            if len(data_access_events) > 1000:  # High volume of data access
                findings.append({
                    'type': 'high_data_access_volume',
                    'count': len(data_access_events),
                    'description': f"High volume of data access events: {len(data_access_events)}",
                    'severity': 'medium',
                    'events': [log.log_id for log in data_access_events[:5]]
                })
            
            return findings
            
        except Exception as e:
            self.logger.error(f"Error generating findings: {e}")
            return []
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]], compliance_score: float) -> List[str]:
        """Generate recommendations based on findings and compliance score"""
        try:
            recommendations = []
            
            if compliance_score < 90:
                recommendations.append("Implement additional security monitoring and alerting")
            
            if compliance_score < 80:
                recommendations.append("Conduct comprehensive security audit and review")
            
            for finding in findings:
                if finding['severity'] == 'high':
                    recommendations.append(f"Immediate action required: {finding['description']}")
                elif finding['severity'] == 'medium':
                    recommendations.append(f"Review and address: {finding['description']}")
            
            if not recommendations:
                recommendations.append("Current compliance level is acceptable")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    def cleanup_expired_logs(self) -> int:
        """Clean up expired audit logs based on retention policies"""
        try:
            current_time = datetime.utcnow()
            expired_logs = []
            
            for log in self.audit_logs:
                expiration_date = log.timestamp + timedelta(days=log.retention_days)
                if current_time > expiration_date:
                    expired_logs.append(log)
            
            # Remove expired logs
            for log in expired_logs:
                self.audit_logs.remove(log)
            
            self.logger.info(f"Cleaned up {len(expired_logs)} expired audit logs")
            return len(expired_logs)
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired logs: {e}")
            return 0
    
    def export_audit_logs(self, query: AuditLogQuery, format: str = 'json') -> str:
        """Export audit logs in specified format"""
        try:
            logs = self.query_audit_logs(query)
            
            if format.lower() == 'json':
                # Convert to JSON
                log_data = []
                for log in logs:
                    log_dict = asdict(log)
                    log_dict['timestamp'] = log.timestamp.isoformat()
                    log_data.append(log_dict)
                
                return json.dumps(log_data, indent=2)
            
            elif format.lower() == 'csv':
                # Convert to CSV
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    'log_id', 'timestamp', 'user_id', 'event_type', 'event_category',
                    'severity', 'description', 'resource_type', 'resource_id',
                    'ip_address', 'user_agent', 'compliance_level'
                ])
                
                # Write data
                for log in logs:
                    writer.writerow([
                        log.log_id, log.timestamp.isoformat(), log.user_id,
                        log.event_type.value, log.event_category.value,
                        log.severity.value, log.description, log.resource_type,
                        log.resource_id, log.ip_address, log.user_agent,
                        log.compliance_level.value
                    ])
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting audit logs: {e}")
            raise
    
    def get_audit_statistics(self, period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Get audit statistics for specified period"""
        try:
            query = AuditLogQuery(start_date=period_start, end_date=period_end)
            logs = self.query_audit_logs(query)
            
            # Calculate statistics
            total_events = len(logs)
            unique_users = len(set(log.user_id for log in logs if log.user_id))
            unique_ips = len(set(log.ip_address for log in logs))
            
            # Events by type
            events_by_type = {}
            for log in logs:
                event_type = log.event_type.value
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            
            # Events by severity
            events_by_severity = {}
            for log in logs:
                severity = log.severity.value
                events_by_severity[severity] = events_by_severity.get(severity, 0) + 1
            
            # Top resources accessed
            resource_access = {}
            for log in logs:
                if log.resource_type:
                    resource_access[log.resource_type] = resource_access.get(log.resource_type, 0) + 1
            
            return {
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'total_events': total_events,
                'unique_users': unique_users,
                'unique_ips': unique_ips,
                'events_by_type': events_by_type,
                'events_by_severity': events_by_severity,
                'top_resources': dict(sorted(resource_access.items(), key=lambda x: x[1], reverse=True)[:10])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting audit statistics: {e}")
            return {} 