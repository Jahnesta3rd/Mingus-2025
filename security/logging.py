"""
MINGUS Security Logging and Monitoring System
Comprehensive security event tracking and monitoring
"""

import logging
import json
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import hashlib
import uuid
from collections import defaultdict, deque
import sqlite3
import os
from pathlib import Path
import requests
from urllib.parse import urlparse
import ipaddress
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Types of security events"""
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOGOUT = "auth_logout"
    AUTH_SESSION_EXPIRED = "auth_session_expired"
    AUTH_SESSION_HIJACKED = "auth_session_hijacked"
    AUTH_MFA_SUCCESS = "auth_mfa_success"
    AUTH_MFA_FAILURE = "auth_mfa_failure"
    AUTH_PASSWORD_CHANGE = "auth_password_change"
    AUTH_PASSWORD_RESET = "auth_password_reset"
    AUTH_ACCOUNT_LOCKED = "auth_account_locked"
    AUTH_ACCOUNT_UNLOCKED = "auth_account_unlocked"
    
    AUTHORIZATION_FAILURE = "authorization_failure"
    AUTHORIZATION_GRANTED = "authorization_granted"
    AUTHORIZATION_REVOKED = "authorization_revoked"
    AUTHORIZATION_ESCALATION = "authorization_escalation"
    
    INPUT_VALIDATION_VIOLATION = "input_validation_violation"
    INPUT_SANITIZATION = "input_sanitization"
    INPUT_REJECTED = "input_rejected"
    
    RATE_LIMITING_TRIGGER = "rate_limiting_trigger"
    RATE_LIMITING_BLOCKED = "rate_limiting_blocked"
    RATE_LIMITING_RESET = "rate_limiting_reset"
    
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    COMMAND_INJECTION_ATTEMPT = "command_injection_attempt"
    
    FILE_UPLOAD_ATTEMPT = "file_upload_attempt"
    FILE_UPLOAD_REJECTED = "file_upload_rejected"
    FILE_UPLOAD_MALICIOUS = "file_upload_malicious"
    
    API_ACCESS = "api_access"
    API_ACCESS_DENIED = "api_access_denied"
    API_RATE_LIMITED = "api_rate_limited"
    API_SIGNATURE_INVALID = "api_signature_invalid"
    
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_FAILURE = "payment_failure"
    PAYMENT_FRAUD_DETECTED = "payment_fraud_detected"
    
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    
    ADMIN_ACTION = "admin_action"
    ADMIN_ACCESS = "admin_access"
    ADMIN_ESCALATION = "admin_escalation"
    
    SYSTEM_CONFIGURATION_CHANGE = "system_configuration_change"
    SECURITY_CONFIGURATION_CHANGE = "security_configuration_change"
    
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    THREAT_DETECTED = "threat_detected"
    INCIDENT_REPORTED = "incident_reported"

class SecurityEventSeverity(Enum):
    """Security event severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class SecurityEventStatus(Enum):
    """Security event status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    timestamp: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_method: Optional[str] = None
    request_url: Optional[str] = None
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    
    # Event-specific data
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Security context
    threat_level: Optional[str] = None
    risk_score: Optional[float] = None
    indicators: List[str] = field(default_factory=list)
    
    # Status and tracking
    status: SecurityEventStatus = SecurityEventStatus.DETECTED
    investigation_notes: List[str] = field(default_factory=list)
    remediation_actions: List[str] = field(default_factory=list)
    
    # Compliance and audit
    compliance_tags: List[str] = field(default_factory=list)
    audit_trail: List[str] = field(default_factory=list)
    
    # Metadata
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['status'] = self.status.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    title: str
    description: str
    severity: SecurityEventSeverity
    timestamp: str
    event_ids: List[str] = field(default_factory=list)
    threat_indicators: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    status: str = "active"
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None

class SecurityEventLogger:
    """Comprehensive security event logger"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_file = config.get('log_file', '/var/log/mingus/security.log')
        self.db_file = config.get('db_file', '/var/lib/mingus/security_events.db')
        self.max_events = config.get('max_events', 100000)
        self.retention_days = config.get('retention_days', 90)
        self.enable_real_time_monitoring = config.get('enable_real_time_monitoring', True)
        self.enable_alerting = config.get('enable_alerting', True)
        self.enable_behavior_analysis = config.get('enable_behavior_analysis', True)
        self.enable_anomaly_detection = config.get('enable_anomaly_detection', True)
        
        # Initialize components
        self._setup_logging()
        self._setup_database()
        self._setup_monitoring()
        
        # Initialize behavior detector
        if self.enable_behavior_analysis:
            self.behavior_detector = SuspiciousBehaviorDetector(config)
        else:
            self.behavior_detector = None
        
        # Initialize real-time security monitor
        if self.enable_anomaly_detection:
            self.real_time_monitor = RealTimeSecurityMonitor(config)
        else:
            self.real_time_monitor = None
        
        # Event tracking
        self.event_counters = defaultdict(int)
        self.recent_events = deque(maxlen=1000)
        self.suspicious_ips = set()
        self.blocked_ips = set()
        
        # Threading
        self.lock = threading.Lock()
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        
        if self.enable_real_time_monitoring:
            self._start_monitoring()
    
    def _setup_logging(self):
        """Setup file logging"""
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Configure formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
    
    def _setup_database(self):
        """Setup SQLite database for event storage"""
        db_dir = os.path.dirname(self.db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Security events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                request_method TEXT,
                request_url TEXT,
                request_headers TEXT,
                request_body TEXT,
                response_status INTEGER,
                response_body TEXT,
                details TEXT,
                threat_level TEXT,
                risk_score REAL,
                indicators TEXT,
                status TEXT NOT NULL,
                investigation_notes TEXT,
                remediation_actions TEXT,
                compliance_tags TEXT,
                audit_trail TEXT,
                source TEXT,
                correlation_id TEXT,
                parent_event_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Security alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_alerts (
                alert_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                severity TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_ids TEXT,
                threat_indicators TEXT,
                recommended_actions TEXT,
                status TEXT NOT NULL,
                acknowledged_by TEXT,
                acknowledged_at TEXT,
                resolved_by TEXT,
                resolved_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Event counters table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_counters (
                event_type TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Suspicious IPs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suspicious_ips (
                ip_address TEXT PRIMARY KEY,
                threat_level TEXT NOT NULL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_count INTEGER DEFAULT 1,
                blocked BOOLEAN DEFAULT FALSE
            )
        ''')
        
        self.conn.commit()
    
    def _setup_monitoring(self):
        """Setup real-time monitoring"""
        self.alert_rules = {
            'high_failure_rate': {
                'threshold': 5,
                'window': 300,  # 5 minutes
                'event_types': [SecurityEventType.AUTH_FAILURE],
                'action': 'block_ip'
            },
            'suspicious_activity': {
                'threshold': 10,
                'window': 600,  # 10 minutes
                'event_types': [SecurityEventType.SUSPICIOUS_ACTIVITY],
                'action': 'alert'
            },
            'critical_violations': {
                'threshold': 1,
                'window': 60,  # 1 minute
                'event_types': [SecurityEventType.SQL_INJECTION_ATTEMPT, SecurityEventType.XSS_ATTEMPT],
                'action': 'immediate_block'
            }
        }
    
    def log_event(self, event: SecurityEvent) -> str:
        """Log a security event"""
        with self.lock:
            try:
                # Generate event ID if not provided
                if not event.event_id:
                    event.event_id = str(uuid.uuid4())
                
                # Add timestamp if not provided
                if not event.timestamp:
                    event.timestamp = datetime.utcnow().isoformat()
                
                # Calculate risk score if not provided
                if event.risk_score is None:
                    event.risk_score = self._calculate_risk_score(event)
                
                # Analyze user behavior if enabled
                if self.enable_behavior_analysis and self.behavior_detector:
                    behavior_analysis = self.behavior_detector.analyze_user_behavior(event)
                    
                    if behavior_analysis['suspicious']:
                        # Update event with behavior analysis
                        event.indicators.extend([pattern['description'] for pattern in behavior_analysis['patterns_detected']])
                        event.risk_score = max(event.risk_score, behavior_analysis['risk_score'])
                        event.details['behavior_analysis'] = behavior_analysis
                        
                        # Log suspicious behavior event
                        self._log_suspicious_behavior(event, behavior_analysis)
                
                # Process real-time monitoring if enabled
                if self.enable_anomaly_detection and self.real_time_monitor:
                    real_time_alerts = self.real_time_monitor.process_security_event(event)
                    
                    if real_time_alerts:
                        # Update event with real-time alerts
                        event.details['real_time_alerts'] = real_time_alerts
                        event.indicators.extend([alert['description'] for alert in real_time_alerts])
                        
                        # Update risk score based on alerts
                        max_alert_severity = max([alert.get('severity', 'low') for alert in real_time_alerts])
                        severity_weights = {'critical': 10.0, 'high': 7.0, 'medium': 4.0, 'low': 1.0}
                        alert_risk_score = severity_weights.get(max_alert_severity, 1.0)
                        event.risk_score = max(event.risk_score, alert_risk_score)
                
                # Store in database
                self._store_event(event)
                
                # Update counters
                self._update_counters(event)
                
                # Add to recent events
                self.recent_events.append(event)
                
                # Check for suspicious activity
                self._check_suspicious_activity(event)
                
                # Log to file
                logger.info(f"Security Event: {event.event_type.value} - {event.severity.value} - {event.event_id}")
                
                # Real-time monitoring
                if self.enable_real_time_monitoring:
                    self._process_real_time_event(event)
                
                return event.event_id
                
            except Exception as e:
                logger.error(f"Error logging security event: {e}")
                return None
    
    def _store_event(self, event: SecurityEvent):
        """Store event in database"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_events (
                event_id, event_type, severity, timestamp, user_id, session_id,
                ip_address, user_agent, request_method, request_url, request_headers,
                request_body, response_status, response_body, details, threat_level,
                risk_score, indicators, status, investigation_notes, remediation_actions,
                compliance_tags, audit_trail, source, correlation_id, parent_event_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id, event.event_type.value, event.severity.value,
            event.timestamp, event.user_id, event.session_id, event.ip_address,
            event.user_agent, event.request_method, event.request_url,
            json.dumps(event.request_headers) if event.request_headers else None,
            event.request_body, event.response_status, event.response_body,
            json.dumps(event.details), event.threat_level, event.risk_score,
            json.dumps(event.indicators), event.status.value,
            json.dumps(event.investigation_notes), json.dumps(event.remediation_actions),
            json.dumps(event.compliance_tags), json.dumps(event.audit_trail),
            event.source, event.correlation_id, event.parent_event_id
        ))
        
        self.conn.commit()
    
    def _update_counters(self, event: SecurityEvent):
        """Update event counters"""
        self.event_counters[event.event_type.value] += 1
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO event_counters (event_type, count, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (event.event_type.value, self.event_counters[event.event_type.value]))
        
        self.conn.commit()
    
    def _calculate_risk_score(self, event: SecurityEvent) -> float:
        """Calculate risk score for event"""
        base_score = {
            SecurityEventSeverity.CRITICAL: 10.0,
            SecurityEventSeverity.HIGH: 7.0,
            SecurityEventSeverity.MEDIUM: 4.0,
            SecurityEventSeverity.LOW: 1.0,
            SecurityEventSeverity.INFO: 0.5
        }.get(event.severity, 1.0)
        
        # Adjust based on event type
        type_multipliers = {
            SecurityEventType.SQL_INJECTION_ATTEMPT: 2.0,
            SecurityEventType.XSS_ATTEMPT: 1.8,
            SecurityEventType.AUTH_FAILURE: 1.5,
            SecurityEventType.RATE_LIMITING_TRIGGER: 1.2,
            SecurityEventType.SUSPICIOUS_ACTIVITY: 1.3
        }
        
        multiplier = type_multipliers.get(event.event_type, 1.0)
        
        # Adjust based on IP reputation
        if event.ip_address and event.ip_address in self.suspicious_ips:
            multiplier *= 1.5
        
        return min(10.0, base_score * multiplier)
    
    def _check_suspicious_activity(self, event: SecurityEvent):
        """Check for suspicious activity patterns"""
        if not event.ip_address:
            return
        
        # Check for high-risk event types
        high_risk_events = [
            SecurityEventType.SQL_INJECTION_ATTEMPT,
            SecurityEventType.XSS_ATTEMPT,
            SecurityEventType.COMMAND_INJECTION_ATTEMPT,
            SecurityEventType.PATH_TRAVERSAL_ATTEMPT
        ]
        
        if event.event_type in high_risk_events:
            self.suspicious_ips.add(event.ip_address)
            self._update_suspicious_ip(event.ip_address, "high")
        
        # Check for rapid authentication failures
        if event.event_type == SecurityEventType.AUTH_FAILURE:
            recent_failures = self._count_recent_events(
                event.ip_address, SecurityEventType.AUTH_FAILURE, 300
            )
            if recent_failures >= 5:
                self.suspicious_ips.add(event.ip_address)
                self._update_suspicious_ip(event.ip_address, "medium")
    
    def _update_suspicious_ip(self, ip_address: str, threat_level: str):
        """Update suspicious IP tracking"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO suspicious_ips 
            (ip_address, threat_level, last_seen, event_count)
            VALUES (?, ?, CURRENT_TIMESTAMP, 
                   COALESCE((SELECT event_count + 1 FROM suspicious_ips WHERE ip_address = ?), 1))
        ''', (ip_address, threat_level, ip_address))
        
        self.conn.commit()
    
    def _count_recent_events(self, ip_address: str, event_type: SecurityEventType, 
                           window_seconds: int) -> int:
        """Count recent events for an IP"""
        cursor = self.conn.cursor()
        
        cutoff_time = (datetime.utcnow() - timedelta(seconds=window_seconds)).isoformat()
        
        cursor.execute('''
            SELECT COUNT(*) FROM security_events 
            WHERE ip_address = ? AND event_type = ? AND timestamp > ?
        ''', (ip_address, event_type.value, cutoff_time))
        
        return cursor.fetchone()[0]
    
    def _process_real_time_event(self, event: SecurityEvent):
        """Process event for real-time monitoring"""
        # Check alert rules
        for rule_name, rule in self.alert_rules.items():
            if event.event_type in rule['event_types']:
                recent_count = self._count_recent_events(
                    event.ip_address or "unknown",
                    event.event_type,
                    rule['window']
                )
                
                if recent_count >= rule['threshold']:
                    self._trigger_alert(rule_name, event, recent_count)
    
    def _trigger_alert(self, rule_name: str, event: SecurityEvent, count: int):
        """Trigger security alert"""
        alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            title=f"Security Alert: {rule_name.replace('_', ' ').title()}",
            description=f"Detected {count} {event.event_type.value} events from {event.ip_address or 'unknown IP'}",
            severity=event.severity,
            timestamp=datetime.utcnow().isoformat(),
            event_ids=[event.event_id],
            threat_indicators=[f"High frequency of {event.event_type.value}"],
            recommended_actions=["Investigate source IP", "Review security logs", "Consider blocking IP"]
        )
        
        self._store_alert(alert)
        
        if self.enable_alerting:
            self._send_alert_notification(alert)
    
    def _store_alert(self, alert: SecurityAlert):
        """Store alert in database"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_alerts (
                alert_id, title, description, severity, timestamp, event_ids,
                threat_indicators, recommended_actions, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert.alert_id, alert.title, alert.description, alert.severity.value,
            alert.timestamp, json.dumps(alert.event_ids), json.dumps(alert.threat_indicators),
            json.dumps(alert.recommended_actions), alert.status
        ))
        
        self.conn.commit()
    
    def _send_alert_notification(self, alert: SecurityAlert):
        """Send alert notification"""
        # This would integrate with notification systems (email, Slack, etc.)
        logger.warning(f"SECURITY ALERT: {alert.title} - {alert.description}")
    
    def _start_monitoring(self):
        """Start real-time monitoring thread"""
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def _monitoring_loop(self):
        """Real-time monitoring loop"""
        while not self.shutdown_event.is_set():
            try:
                # Periodic checks
                self._check_anomalies()
                self._cleanup_old_events()
                
                # Sleep for monitoring interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    def _check_anomalies(self):
        """Check for security anomalies"""
        # Check for unusual patterns
        # This would implement more sophisticated anomaly detection
        pass
    
    def _cleanup_old_events(self):
        """Clean up old events based on retention policy"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM security_events WHERE timestamp < ?
        ''', (cutoff_date.isoformat(),))
        
        self.conn.commit()
    
    def get_events(self, filters: Dict[str, Any] = None, limit: int = 100) -> List[SecurityEvent]:
        """Get security events with optional filtering"""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []
        
        if filters:
            if 'event_type' in filters:
                query += " AND event_type = ?"
                params.append(filters['event_type'])
            
            if 'severity' in filters:
                query += " AND severity = ?"
                params.append(filters['severity'])
            
            if 'ip_address' in filters:
                query += " AND ip_address = ?"
                params.append(filters['ip_address'])
            
            if 'user_id' in filters:
                query += " AND user_id = ?"
                params.append(filters['user_id'])
            
            if 'start_time' in filters:
                query += " AND timestamp >= ?"
                params.append(filters['start_time'])
            
            if 'end_time' in filters:
                query += " AND timestamp <= ?"
                params.append(filters['end_time'])
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            event = self._row_to_event(row)
            events.append(event)
        
        return events
    
    def _row_to_event(self, row) -> SecurityEvent:
        """Convert database row to SecurityEvent"""
        return SecurityEvent(
            event_id=row['event_id'],
            event_type=SecurityEventType(row['event_type']),
            severity=SecurityEventSeverity(row['severity']),
            timestamp=row['timestamp'],
            user_id=row['user_id'],
            session_id=row['session_id'],
            ip_address=row['ip_address'],
            user_agent=row['user_agent'],
            request_method=row['request_method'],
            request_url=row['request_url'],
            request_headers=json.loads(row['request_headers']) if row['request_headers'] else None,
            request_body=row['request_body'],
            response_status=row['response_status'],
            response_body=row['response_body'],
            details=json.loads(row['details']) if row['details'] else {},
            threat_level=row['threat_level'],
            risk_score=row['risk_score'],
            indicators=json.loads(row['indicators']) if row['indicators'] else [],
            status=SecurityEventStatus(row['status']),
            investigation_notes=json.loads(row['investigation_notes']) if row['investigation_notes'] else [],
            remediation_actions=json.loads(row['remediation_actions']) if row['remediation_actions'] else [],
            compliance_tags=json.loads(row['compliance_tags']) if row['compliance_tags'] else [],
            audit_trail=json.loads(row['audit_trail']) if row['audit_trail'] else [],
            source=row['source'],
            correlation_id=row['correlation_id'],
            parent_event_id=row['parent_event_id']
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get security event statistics"""
        cursor = self.conn.cursor()
        
        # Event counts by type
        cursor.execute('''
            SELECT event_type, COUNT(*) as count 
            FROM security_events 
            GROUP BY event_type
        ''')
        event_counts = dict(cursor.fetchall())
        
        # Event counts by severity
        cursor.execute('''
            SELECT severity, COUNT(*) as count 
            FROM security_events 
            GROUP BY severity
        ''')
        severity_counts = dict(cursor.fetchall())
        
        # Recent activity (last 24 hours)
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM security_events WHERE timestamp > ?
        ''', (yesterday,))
        recent_count = cursor.fetchone()[0]
        
        # Suspicious IPs
        cursor.execute('''
            SELECT COUNT(*) FROM suspicious_ips WHERE blocked = TRUE
        ''')
        blocked_ips = cursor.fetchone()[0]
        
        return {
            'event_counts': event_counts,
            'severity_counts': severity_counts,
            'recent_activity_24h': recent_count,
            'blocked_ips': blocked_ips,
            'total_events': sum(event_counts.values())
        }
    
    def shutdown(self):
        """Shutdown the security logger"""
        self.shutdown_event.set()
        if self.monitoring_thread:
            self.monitoring_thread.join()
        self.conn.close()

    def _log_suspicious_behavior(self, original_event: SecurityEvent, behavior_analysis: Dict[str, Any]):
        """Log suspicious behavior as a separate event"""
        suspicious_event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            severity=SecurityEventSeverity.HIGH if behavior_analysis['risk_score'] > 7.0 else SecurityEventSeverity.MEDIUM,
            timestamp=datetime.utcnow().isoformat(),
            user_id=original_event.user_id,
            session_id=original_event.session_id,
            ip_address=original_event.ip_address,
            user_agent=original_event.user_agent,
            details={
                'original_event_id': original_event.event_id,
                'original_event_type': original_event.event_type.value,
                'behavior_analysis': behavior_analysis,
                'patterns_detected': len(behavior_analysis['patterns_detected']),
                'risk_score': behavior_analysis['risk_score']
            },
            threat_level='high' if behavior_analysis['risk_score'] > 7.0 else 'medium',
            risk_score=behavior_analysis['risk_score'],
            indicators=behavior_analysis['patterns_detected'],
            source='behavior_analysis_system',
            correlation_id=original_event.event_id
        )
        
        # Store suspicious behavior event
        self._store_event(suspicious_event)
        
        # Log to file
        logger.warning(f"Suspicious Behavior Detected: User {original_event.user_id} - Risk Score: {behavior_analysis['risk_score']}")
    
    def get_user_behavior_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user behavior profile"""
        if not self.behavior_detector:
            return {}
        
        return self.behavior_detector.user_profiles.get(user_id, {})
    
    def get_suspicious_users(self) -> List[Dict[str, Any]]:
        """Get list of suspicious users with their profiles"""
        if not self.behavior_detector:
            return []
        
        suspicious_users = []
        for user_id, profile in self.behavior_detector.user_profiles.items():
            if user_id in self.behavior_detector.suspicious_users:
                suspicious_users.append({
                    'user_id': user_id,
                    'profile': profile,
                    'risk_score': self._calculate_user_risk_score(user_id)
                })
        
        return suspicious_users
    
    def _calculate_user_risk_score(self, user_id: str) -> float:
        """Calculate overall risk score for a user"""
        if not self.behavior_detector or user_id not in self.behavior_detector.user_profiles:
            return 0.0
        
        profile = self.behavior_detector.user_profiles[user_id]
        
        # Calculate risk based on various factors
        risk_factors = {
            'financial_access_count': 0.1,
            'payment_transactions': 0.1,
            'admin_actions': 0.2,
            'config_changes': 0.3,
            'policy_violations': 0.4,
            'ip_count': 0.2,
            'session_count': 0.2
        }
        
        total_risk = 0.0
        
        for factor, weight in risk_factors.items():
            if factor == 'ip_count':
                value = len(profile.get('ip_addresses', set()))
            elif factor == 'session_count':
                value = len(profile.get('sessions', set()))
            else:
                value = profile.get(factor, 0)
            
            total_risk += value * weight
        
        return min(10.0, total_risk)

    def get_real_time_alerts(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get real-time security alerts"""
        if not self.real_time_monitor:
            return []
        
        if active_only:
            return list(self.real_time_monitor.active_alerts.values())
        else:
            return self.real_time_monitor.alert_history
    
    def get_anomaly_detection_stats(self) -> Dict[str, Any]:
        """Get anomaly detection statistics"""
        if not self.real_time_monitor:
            return {}
        
        stats = {
            'active_alerts': len(self.real_time_monitor.active_alerts),
            'total_alerts': len(self.real_time_monitor.alert_history),
            'failed_login_clusters': len(self.real_time_monitor.failed_login_clusters),
            'anomaly_detectors': {}
        }
        
        # Get stats from each anomaly detector
        for detector_name, detector in self.real_time_monitor.anomaly_detectors.items():
            if hasattr(detector, 'user_profiles'):
                stats['anomaly_detectors'][detector_name] = {
                    'profiles_count': len(detector.user_profiles)
                }
        
        return stats
    
    def get_failed_login_clusters(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get failed login clusters"""
        if not self.real_time_monitor:
            return {}
        
        return dict(self.real_time_monitor.failed_login_clusters)
    
    def get_user_anomaly_profile(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user anomaly profile"""
        if not self.real_time_monitor:
            return {}
        
        profile = {}
        
        # Get profiles from each anomaly detector
        for detector_name, detector in self.real_time_monitor.anomaly_detectors.items():
            if hasattr(detector, 'user_profiles') and user_id in detector.user_profiles:
                profile[detector_name] = detector.user_profiles[user_id]
            elif hasattr(detector, 'user_financial_profiles') and user_id in detector.user_financial_profiles:
                profile[detector_name] = detector.user_financial_profiles[user_id]
            elif hasattr(detector, 'user_temporal_profiles') and user_id in detector.user_temporal_profiles:
                profile[detector_name] = detector.user_temporal_profiles[user_id]
        
        return profile

# Convenience functions for common security events
def log_auth_attempt(logger: SecurityEventLogger, user_id: str, success: bool, 
                    ip_address: str, user_agent: str, details: Dict[str, Any] = None) -> str:
    """Log authentication attempt"""
    event_type = SecurityEventType.AUTH_SUCCESS if success else SecurityEventType.AUTH_FAILURE
    severity = SecurityEventSeverity.INFO if success else SecurityEventSeverity.MEDIUM
    
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        severity=severity,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
        source="authentication_system"
    )
    
    return logger.log_event(event)

def log_authorization_failure(logger: SecurityEventLogger, user_id: str, resource: str,
                            ip_address: str, user_agent: str, details: Dict[str, Any] = None) -> str:
    """Log authorization failure"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.AUTHORIZATION_FAILURE,
        severity=SecurityEventSeverity.HIGH,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'resource': resource,
            **(details or {})
        },
        source="authorization_system"
    )
    
    return logger.log_event(event)

def log_input_validation_violation(logger: SecurityEventLogger, input_data: str, 
                                 violation_type: str, ip_address: str, 
                                 user_agent: str, details: Dict[str, Any] = None) -> str:
    """Log input validation violation"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.INPUT_VALIDATION_VIOLATION,
        severity=SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'input_data': input_data[:100],  # Truncate for security
            'violation_type': violation_type,
            **(details or {})
        },
        source="input_validation_system"
    )
    
    return logger.log_event(event)

def log_rate_limiting_trigger(logger: SecurityEventLogger, ip_address: str, 
                            endpoint: str, limit_type: str, details: Dict[str, Any] = None) -> str:
    """Log rate limiting trigger"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.RATE_LIMITING_TRIGGER,
        severity=SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        ip_address=ip_address,
        details={
            'endpoint': endpoint,
            'limit_type': limit_type,
            **(details or {})
        },
        source="rate_limiting_system"
    )
    
    return logger.log_event(event)

# Flask integration
def integrate_with_flask(app, security_logger: SecurityEventLogger):
    """Integrate security logging with Flask app"""
    
    @app.before_request
    def log_request_start():
        """Log request start"""
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())
    
    @app.after_request
    def log_request_end(response):
        """Log request end"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Log security-relevant events
            if response.status_code == 401:
                log_auth_attempt(
                    security_logger,
                    user_id=request.args.get('user_id'),
                    success=False,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    details={'endpoint': request.endpoint, 'method': request.method}
                )
            elif response.status_code == 403:
                log_authorization_failure(
                    security_logger,
                    user_id=request.args.get('user_id'),
                    resource=request.endpoint,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    details={'endpoint': request.endpoint, 'method': request.method}
                )
            elif response.status_code == 429:
                log_rate_limiting_trigger(
                    security_logger,
                    ip_address=request.remote_addr,
                    endpoint=request.endpoint,
                    limit_type="request_rate",
                    details={'method': request.method}
                )
        
        return response
    
    @app.errorhandler(400)
    def log_bad_request(error):
        """Log bad request (potential input validation violation)"""
        log_input_validation_violation(
            security_logger,
            input_data=str(request.get_data()),
            violation_type="bad_request",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            details={'endpoint': request.endpoint, 'method': request.method}
        )
        return error

# Create default security logger instance
def create_security_logger(config: Dict[str, Any] = None) -> SecurityEventLogger:
    """Create security logger with default configuration"""
    if config is None:
        config = {
            'log_file': '/var/log/mingus/security.log',
            'db_file': '/var/lib/mingus/security_events.db',
            'max_events': 100000,
            'retention_days': 90,
            'enable_real_time_monitoring': True,
            'enable_alerting': True,
            'enable_behavior_analysis': True
        }
    
    return SecurityEventLogger(config) 

class SuspiciousBehaviorDetector:
    """Detector for suspicious user behavior patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.behavior_patterns = self._load_behavior_patterns()
        self.user_profiles = defaultdict(dict)
        self.suspicious_users = set()
        self.behavior_thresholds = config.get('behavior_thresholds', {
            'financial_data_access': {
                'unusual_hours': {'start': 22, 'end': 6},  # 10 PM to 6 AM
                'max_daily_access': 50,
                'max_concurrent_sessions': 3,
                'unusual_locations': True
            },
            'payment_processing': {
                'max_daily_transactions': 20,
                'max_transaction_amount': 10000,
                'unusual_payment_methods': True,
                'rapid_transactions': {'count': 5, 'window': 300}  # 5 transactions in 5 minutes
            },
            'admin_actions': {
                'max_daily_actions': 100,
                'sensitive_operations': ['user_deletion', 'permission_grant', 'system_config'],
                'unusual_admin_activity': True
            },
            'configuration_changes': {
                'max_daily_changes': 10,
                'sensitive_configs': ['security_settings', 'encryption_keys', 'access_controls'],
                'unauthorized_changes': True
            },
            'security_policy_violations': {
                'max_violations_per_day': 5,
                'critical_violations': ['data_export', 'admin_escalation', 'bypass_security'],
                'policy_bypass_attempts': True
            }
        })
    
    def analyze_user_behavior(self, event: SecurityEvent) -> Dict[str, Any]:
        """Analyze user behavior for suspicious patterns"""
        analysis = {
            'suspicious': False,
            'risk_score': 0.0,
            'patterns_detected': [],
            'recommendations': []
        }
        
        if not event.user_id:
            return analysis
        
        # Update user profile
        self._update_user_profile(event)
        
        # Check for suspicious patterns
        patterns = []
        
        # Financial data access analysis
        if event.event_type in [SecurityEventType.DATA_ACCESS, SecurityEventType.DATA_MODIFICATION]:
            financial_patterns = self._analyze_financial_data_access(event)
            patterns.extend(financial_patterns)
        
        # Payment processing analysis
        if event.event_type in [SecurityEventType.PAYMENT_PROCESSING, SecurityEventType.PAYMENT_FAILURE]:
            payment_patterns = self._analyze_payment_processing(event)
            patterns.extend(payment_patterns)
        
        # Admin actions analysis
        if event.event_type in [SecurityEventType.ADMIN_ACTION, SecurityEventType.ADMIN_ACCESS]:
            admin_patterns = self._analyze_admin_actions(event)
            patterns.extend(admin_patterns)
        
        # Configuration changes analysis
        if event.event_type in [SecurityEventType.SYSTEM_CONFIGURATION_CHANGE, SecurityEventType.SECURITY_CONFIGURATION_CHANGE]:
            config_patterns = self._analyze_configuration_changes(event)
            patterns.extend(config_patterns)
        
        # Security policy violations analysis
        if event.event_type in [SecurityEventType.AUTHORIZATION_FAILURE, SecurityEventType.SUSPICIOUS_ACTIVITY]:
            policy_patterns = self._analyze_security_policy_violations(event)
            patterns.extend(policy_patterns)
        
        # Calculate overall risk score
        if patterns:
            analysis['suspicious'] = True
            analysis['patterns_detected'] = patterns
            analysis['risk_score'] = self._calculate_behavior_risk_score(patterns)
            analysis['recommendations'] = self._generate_behavior_recommendations(patterns)
        
        return analysis
    
    def _update_user_profile(self, event: SecurityEvent):
        """Update user behavior profile"""
        user_id = event.user_id
        if not user_id:
            return
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'first_seen': event.timestamp,
                'last_seen': event.timestamp,
                'event_count': 0,
                'event_types': defaultdict(int),
                'session_patterns': defaultdict(int),
                'activity_hours': defaultdict(int),
                'ip_addresses': set(),
                'user_agents': set()
            }
        
        profile = self.user_profiles[user_id]
        profile['last_seen'] = event.timestamp
        profile['event_count'] += 1
        profile['event_types'][event.event_type.value] += 1
        
        if event.ip_address:
            profile['ip_addresses'].add(event.ip_address)
        if event.user_agent:
            profile['user_agents'].add(event.user_agent)
        
        # Update temporal patterns
        event_time = datetime.fromisoformat(event.timestamp)
        profile['activity_hours'][event_time.hour] += 1
    
    def _analyze_financial_data_access(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Analyze suspicious financial data access patterns"""
        patterns = []
        user_id = event.user_id
        profile = self.user_profiles.get(user_id, {})
        
        # Check for unusual access hours
        event_time = datetime.fromisoformat(event.timestamp)
        hour = event_time.hour
        unusual_hours = self.behavior_thresholds['financial_data_access']['unusual_hours']
        
        if hour >= unusual_hours['start'] or hour <= unusual_hours['end']:
            patterns.append({
                'type': 'unusual_hours_access',
                'severity': 'medium',
                'description': f'Financial data accessed during unusual hours ({hour}:00)',
                'details': {'hour': hour, 'threshold': unusual_hours}
            })
        
        # Check for excessive daily access
        daily_access = profile.get('financial_access_count', 0)
        max_daily = self.behavior_thresholds['financial_data_access']['max_daily_access']
        
        if daily_access > max_daily:
            patterns.append({
                'type': 'excessive_financial_access',
                'severity': 'high',
                'description': f'Excessive financial data access: {daily_access} times today',
                'details': {'count': daily_access, 'threshold': max_daily}
            })
        
        # Check for multiple IP addresses
        ip_count = len(profile.get('ip_addresses', set()))
        if ip_count > 3:
            patterns.append({
                'type': 'multiple_ip_access',
                'severity': 'medium',
                'description': f'Financial data accessed from {ip_count} different IP addresses',
                'details': {'ip_count': ip_count, 'ips': list(profile.get('ip_addresses', set()))}
            })
        
        # Check for concurrent sessions
        session_count = len(profile.get('sessions', set()))
        max_sessions = self.behavior_thresholds['financial_data_access']['max_concurrent_sessions']
        
        if session_count > max_sessions:
            patterns.append({
                'type': 'concurrent_sessions',
                'severity': 'high',
                'description': f'Multiple concurrent sessions accessing financial data: {session_count}',
                'details': {'session_count': session_count, 'threshold': max_sessions}
            })
        
        return patterns
    
    def _analyze_payment_processing(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Analyze suspicious payment processing patterns"""
        patterns = []
        user_id = event.user_id
        profile = self.user_profiles.get(user_id, {})
        
        # Check for excessive daily transactions
        daily_transactions = profile.get('payment_transactions', 0)
        max_daily = self.behavior_thresholds['payment_processing']['max_daily_transactions']
        
        if daily_transactions > max_daily:
            patterns.append({
                'type': 'excessive_payment_transactions',
                'severity': 'high',
                'description': f'Excessive payment transactions: {daily_transactions} today',
                'details': {'count': daily_transactions, 'threshold': max_daily}
            })
        
        # Check for large transaction amounts
        if event.details and 'amount' in event.details:
            amount = float(event.details['amount'])
            max_amount = self.behavior_thresholds['payment_processing']['max_transaction_amount']
            
            if amount > max_amount:
                patterns.append({
                    'type': 'large_transaction_amount',
                    'severity': 'high',
                    'description': f'Large transaction amount: ${amount:,.2f}',
                    'details': {'amount': amount, 'threshold': max_amount}
                })
        
        # Check for rapid transactions
        rapid_config = self.behavior_thresholds['payment_processing']['rapid_transactions']
        recent_transactions = self._count_recent_events(user_id, SecurityEventType.PAYMENT_PROCESSING, rapid_config['window'])
        
        if recent_transactions >= rapid_config['count']:
            patterns.append({
                'type': 'rapid_payment_transactions',
                'severity': 'critical',
                'description': f'Rapid payment transactions: {recent_transactions} in {rapid_config["window"]} seconds',
                'details': {'count': recent_transactions, 'window': rapid_config['window']}
            })
        
        # Check for unusual payment methods
        if event.details and 'payment_method' in event.details:
            payment_method = event.details['payment_method']
            unusual_methods = ['cryptocurrency', 'prepaid_card', 'gift_card']
            
            if payment_method.lower() in unusual_methods:
                patterns.append({
                    'type': 'unusual_payment_method',
                    'severity': 'medium',
                    'description': f'Unusual payment method used: {payment_method}',
                    'details': {'payment_method': payment_method}
                })
        
        return patterns
    
    def _analyze_admin_actions(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Analyze suspicious admin action patterns"""
        patterns = []
        user_id = event.user_id
        profile = self.user_profiles.get(user_id, {})
        
        # Check for excessive daily admin actions
        daily_actions = profile.get('admin_actions', 0)
        max_daily = self.behavior_thresholds['admin_actions']['max_daily_actions']
        
        if daily_actions > max_daily:
            patterns.append({
                'type': 'excessive_admin_actions',
                'severity': 'high',
                'description': f'Excessive admin actions: {daily_actions} today',
                'details': {'count': daily_actions, 'threshold': max_daily}
            })
        
        # Check for sensitive operations
        sensitive_ops = self.behavior_thresholds['admin_actions']['sensitive_operations']
        if event.details and 'operation' in event.details:
            operation = event.details['operation']
            
            if operation in sensitive_ops:
                patterns.append({
                    'type': 'sensitive_admin_operation',
                    'severity': 'critical',
                    'description': f'Sensitive admin operation: {operation}',
                    'details': {'operation': operation, 'sensitive_operations': sensitive_ops}
                })
        
        # Check for unusual admin activity hours
        event_time = datetime.fromisoformat(event.timestamp)
        hour = event_time.hour
        
        if hour >= 22 or hour <= 6:  # Late night admin activity
            patterns.append({
                'type': 'unusual_admin_hours',
                'severity': 'medium',
                'description': f'Admin action during unusual hours ({hour}:00)',
                'details': {'hour': hour}
            })
        
        return patterns
    
    def _analyze_configuration_changes(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Analyze suspicious configuration change patterns"""
        patterns = []
        user_id = event.user_id
        profile = self.user_profiles.get(user_id, {})
        
        # Check for excessive daily configuration changes
        daily_changes = profile.get('config_changes', 0)
        max_daily = self.behavior_thresholds['configuration_changes']['max_daily_changes']
        
        if daily_changes > max_daily:
            patterns.append({
                'type': 'excessive_config_changes',
                'severity': 'high',
                'description': f'Excessive configuration changes: {daily_changes} today',
                'details': {'count': daily_changes, 'threshold': max_daily}
            })
        
        # Check for sensitive configuration changes
        sensitive_configs = self.behavior_thresholds['configuration_changes']['sensitive_configs']
        if event.details and 'config_type' in event.details:
            config_type = event.details['config_type']
            
            if config_type in sensitive_configs:
                patterns.append({
                    'type': 'sensitive_config_change',
                    'severity': 'critical',
                    'description': f'Sensitive configuration change: {config_type}',
                    'details': {'config_type': config_type, 'sensitive_configs': sensitive_configs}
                })
        
        # Check for unauthorized configuration changes
        if event.details and 'authorized' in event.details:
            if not event.details['authorized']:
                patterns.append({
                    'type': 'unauthorized_config_change',
                    'severity': 'critical',
                    'description': 'Unauthorized configuration change attempted',
                    'details': {'config_type': event.details.get('config_type', 'unknown')}
                })
        
        return patterns
    
    def _analyze_security_policy_violations(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Analyze security policy violation patterns"""
        patterns = []
        user_id = event.user_id
        profile = self.user_profiles.get(user_id, {})
        
        # Check for excessive daily policy violations
        daily_violations = profile.get('policy_violations', 0)
        max_daily = self.behavior_thresholds['security_policy_violations']['max_violations_per_day']
        
        if daily_violations > max_daily:
            patterns.append({
                'type': 'excessive_policy_violations',
                'severity': 'high',
                'description': f'Excessive policy violations: {daily_violations} today',
                'details': {'count': daily_violations, 'threshold': max_daily}
            })
        
        # Check for critical policy violations
        critical_violations = self.behavior_thresholds['security_policy_violations']['critical_violations']
        if event.details and 'violation_type' in event.details:
            violation_type = event.details['violation_type']
            
            if violation_type in critical_violations:
                patterns.append({
                    'type': 'critical_policy_violation',
                    'severity': 'critical',
                    'description': f'Critical policy violation: {violation_type}',
                    'details': {'violation_type': violation_type, 'critical_violations': critical_violations}
                })
        
        # Check for policy bypass attempts
        if event.details and 'bypass_attempt' in event.details:
            if event.details['bypass_attempt']:
                patterns.append({
                    'type': 'policy_bypass_attempt',
                    'severity': 'critical',
                    'description': 'Security policy bypass attempt detected',
                    'details': {'method': event.details.get('bypass_method', 'unknown')}
                })
        
        return patterns
    
    def _count_recent_events(self, user_id: str, event_type: SecurityEventType, window_seconds: int) -> int:
        """Count recent events for a user"""
        if user_id not in self.user_profiles:
            return 0
        
        profile = self.user_profiles[user_id]
        cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        # This would typically query the database for recent events
        # For now, we'll use a simplified approach
        return profile.get('event_count', 0)  # Simplified implementation
    
    def _calculate_behavior_risk_score(self, patterns: List[Dict[str, Any]]) -> float:
        """Calculate risk score based on behavior patterns"""
        severity_weights = {
            'critical': 10.0,
            'high': 7.0,
            'medium': 4.0,
            'low': 1.0
        }
        
        total_score = 0
        for pattern in patterns:
            severity = pattern.get('severity', 'medium')
            weight = severity_weights.get(severity, 1.0)
            total_score += weight
        
        return min(10.0, total_score)
    
    def _generate_behavior_recommendations(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on behavior patterns"""
        recommendations = []
        
        for pattern in patterns:
            pattern_type = pattern.get('type', '')
            
            if 'unusual_hours' in pattern_type:
                recommendations.append("Review user access patterns and consider implementing time-based access controls")
            elif 'excessive' in pattern_type:
                recommendations.append("Implement stricter rate limiting and access controls")
            elif 'sensitive' in pattern_type:
                recommendations.append("Require additional authentication for sensitive operations")
            elif 'unauthorized' in pattern_type:
                recommendations.append("Investigate unauthorized access attempts and strengthen authorization controls")
            elif 'policy_violation' in pattern_type:
                recommendations.append("Review and enforce security policies more strictly")
            elif 'bypass' in pattern_type:
                recommendations.append("Investigate policy bypass attempts and strengthen security controls")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _load_behavior_patterns(self) -> Dict[str, Any]:
        """Load behavior pattern definitions"""
        return {
            'financial_data_access': {
                'description': 'Suspicious patterns in financial data access',
                'indicators': [
                    'unusual_access_hours',
                    'excessive_daily_access',
                    'multiple_ip_addresses',
                    'concurrent_sessions'
                ]
            },
            'payment_processing': {
                'description': 'Suspicious patterns in payment processing',
                'indicators': [
                    'excessive_transactions',
                    'large_amounts',
                    'rapid_transactions',
                    'unusual_payment_methods'
                ]
            },
            'admin_actions': {
                'description': 'Suspicious patterns in administrative actions',
                'indicators': [
                    'excessive_admin_actions',
                    'sensitive_operations',
                    'unusual_hours'
                ]
            },
            'configuration_changes': {
                'description': 'Suspicious patterns in configuration changes',
                'indicators': [
                    'excessive_changes',
                    'sensitive_configs',
                    'unauthorized_changes'
                ]
            },
            'security_policy_violations': {
                'description': 'Suspicious patterns in security policy violations',
                'indicators': [
                    'excessive_violations',
                    'critical_violations',
                    'bypass_attempts'
                ]
            }
        } 

# Convenience functions for suspicious behavior logging
def log_financial_data_access(logger: SecurityEventLogger, user_id: str, data_type: str,
                            access_method: str, ip_address: str, user_agent: str,
                            details: Dict[str, Any] = None) -> str:
    """Log financial data access event"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.DATA_ACCESS,
        severity=SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'data_type': data_type,
            'access_method': access_method,
            **(details or {})
        },
        source="financial_data_system"
    )
    
    return logger.log_event(event)

def log_payment_processing(logger: SecurityEventLogger, user_id: str, amount: float,
                          payment_method: str, transaction_id: str, ip_address: str,
                          user_agent: str, details: Dict[str, Any] = None) -> str:
    """Log payment processing event"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.PAYMENT_PROCESSING,
        severity=SecurityEventSeverity.HIGH,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'amount': amount,
            'payment_method': payment_method,
            'transaction_id': transaction_id,
            **(details or {})
        },
        source="payment_processing_system"
    )
    
    return logger.log_event(event)

def log_admin_action(logger: SecurityEventLogger, user_id: str, operation: str,
                    target_resource: str, ip_address: str, user_agent: str,
                    details: Dict[str, Any] = None) -> str:
    """Log admin action event"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.ADMIN_ACTION,
        severity=SecurityEventSeverity.HIGH,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'operation': operation,
            'target_resource': target_resource,
            **(details or {})
        },
        source="admin_system"
    )
    
    return logger.log_event(event)

def log_configuration_change(logger: SecurityEventLogger, user_id: str, config_type: str,
                           change_description: str, authorized: bool, ip_address: str,
                           user_agent: str, details: Dict[str, Any] = None) -> str:
    """Log configuration change event"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.SYSTEM_CONFIGURATION_CHANGE,
        severity=SecurityEventSeverity.HIGH if not authorized else SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'config_type': config_type,
            'change_description': change_description,
            'authorized': authorized,
            **(details or {})
        },
        source="configuration_management_system"
    )
    
    return logger.log_event(event)

def log_security_policy_violation(logger: SecurityEventLogger, user_id: str, violation_type: str,
                                 policy_name: str, bypass_attempt: bool, ip_address: str,
                                 user_agent: str, details: Dict[str, Any] = None) -> str:
    """Log security policy violation event"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        severity=SecurityEventSeverity.HIGH if bypass_attempt else SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'violation_type': violation_type,
            'policy_name': policy_name,
            'bypass_attempt': bypass_attempt,
            **(details or {})
        },
        source="security_policy_system"
    )
    
    return logger.log_event(event) 

class RealTimeSecurityMonitor:
    """Real-time security monitoring and alerting system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_thresholds = config.get('alert_thresholds', {
            'failed_login_cluster': {'count': 5, 'window': 300},  # 5 failed logins in 5 minutes
            'unusual_financial_pattern': {'amount_threshold': 5000, 'frequency_threshold': 3},
            'suspicious_api_usage': {'rate_limit_exceeded': 10, 'unusual_endpoints': 5},
            'geographic_anomaly': {'distance_threshold': 1000},  # 1000 km
            'time_based_anomaly': {'unusual_hours': {'start': 22, 'end': 6}}
        })
        
        self.active_alerts = {}
        self.alert_history = []
        self.anomaly_detectors = {
            'user_behavior': UserBehaviorAnomalyDetector(config),
            'financial_patterns': FinancialPatternAnomalyDetector(config),
            'api_usage': APIUsageAnomalyDetector(config),
            'geographic': GeographicAnomalyDetector(config),
            'temporal': TemporalAnomalyDetector(config)
        }
        
        self.failed_login_clusters = defaultdict(list)
        self.user_sessions = defaultdict(dict)
        self.geographic_profiles = defaultdict(dict)
        self.api_usage_profiles = defaultdict(dict)
        
        # Start monitoring threads
        self._start_monitoring_threads()
    
    def process_security_event(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Process security event and generate real-time alerts"""
        alerts = []
        
        # Check for failed login clustering
        if event.event_type == SecurityEventType.AUTH_FAILURE:
            login_alerts = self._check_failed_login_clustering(event)
            alerts.extend(login_alerts)
        
        # Check for unusual financial patterns
        if event.event_type in [SecurityEventType.PAYMENT_PROCESSING, SecurityEventType.DATA_ACCESS]:
            financial_alerts = self._check_unusual_financial_patterns(event)
            alerts.extend(financial_alerts)
        
        # Check for suspicious API usage
        if event.event_type in [SecurityEventType.API_ACCESS, SecurityEventType.RATE_LIMITING_TRIGGER]:
            api_alerts = self._check_suspicious_api_usage(event)
            alerts.extend(api_alerts)
        
        # Check for geographic anomalies
        if event.ip_address:
            geo_alerts = self._check_geographic_anomalies(event)
            alerts.extend(geo_alerts)
        
        # Check for time-based anomalies
        time_alerts = self._check_time_based_anomalies(event)
        alerts.extend(time_alerts)
        
        # Generate real-time alerts
        for alert in alerts:
            self._generate_real_time_alert(alert)
        
        return alerts
    
    def _check_failed_login_clustering(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for failed login attempt clustering"""
        alerts = []
        ip_address = event.ip_address
        user_id = event.details.get('username', 'unknown') if event.details else 'unknown'
        
        if not ip_address:
            return alerts
        
        # Add to failed login cluster
        cluster_key = f"{ip_address}_{user_id}"
        self.failed_login_clusters[cluster_key].append({
            'timestamp': event.timestamp,
            'event_id': event.event_id,
            'user_agent': event.user_agent
        })
        
        # Check for clustering threshold
        recent_failures = [
            failure for failure in self.failed_login_clusters[cluster_key]
            if (datetime.fromisoformat(event.timestamp) - 
                datetime.fromisoformat(failure['timestamp'])).total_seconds() <= 
                self.alert_thresholds['failed_login_cluster']['window']
        ]
        
        if len(recent_failures) >= self.alert_thresholds['failed_login_cluster']['count']:
            alerts.append({
                'type': 'failed_login_cluster',
                'severity': 'high',
                'description': f'Failed login cluster detected: {len(recent_failures)} failed attempts from {ip_address}',
                'details': {
                    'ip_address': ip_address,
                    'username': user_id,
                    'failure_count': len(recent_failures),
                    'time_window': self.alert_thresholds['failed_login_cluster']['window'],
                    'recent_failures': recent_failures
                },
                'recommendations': [
                    'Block IP address temporarily',
                    'Investigate potential brute force attack',
                    'Enable additional authentication measures'
                ]
            })
        
        return alerts
    
    def _check_unusual_financial_patterns(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for unusual financial transaction patterns"""
        anomalies = []
        user_id = event.user_id
        
        if not user_id:
            return anomalies
        
        # Use financial pattern anomaly detector
        financial_detector = self.anomaly_detectors['financial_patterns']
        anomalies.extend(financial_detector.detect_anomalies(event))
        
        return anomalies
    
    def _check_suspicious_api_usage(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for suspicious API usage patterns"""
        anomalies = []
        user_id = event.user_id
        ip_address = event.ip_address
        
        if not user_id or not ip_address:
            return anomalies
        
        # Use API usage anomaly detector
        api_detector = self.anomaly_detectors['api_usage']
        anomalies.extend(api_detector.detect_anomalies(event))
        
        return anomalies
    
    def _check_geographic_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for geographic access anomalies"""
        anomalies = []
        user_id = event.user_id
        ip_address = event.ip_address
        
        if not user_id or not ip_address:
            return anomalies
        
        # Use geographic anomaly detector
        geo_detector = self.anomaly_detectors['geographic']
        anomalies.extend(geo_detector.detect_anomalies(event))
        
        return anomalies
    
    def _check_time_based_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for time-based access pattern anomalies"""
        anomalies = []
        user_id = event.user_id
        
        if not user_id:
            return anomalies
        
        # Use temporal anomaly detector
        temporal_detector = self.anomaly_detectors['temporal']
        anomalies.extend(temporal_detector.detect_anomalies(event))
        
        return anomalies
    
    def _generate_real_time_alert(self, alert: Dict[str, Any]):
        """Generate and send real-time security alert"""
        alert_id = str(uuid.uuid4())
        alert['alert_id'] = alert_id
        alert['timestamp'] = datetime.utcnow().isoformat()
        alert['status'] = 'active'
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Log alert
        logger.warning(f"SECURITY ALERT: {alert['type']} - {alert['severity']} - {alert['description']}")
        
        # Send real-time notification (implement based on your notification system)
        self._send_alert_notification(alert)
    
    def _send_alert_notification(self, alert: Dict[str, Any]):
        """Send real-time alert notification"""
        # Implementation depends on your notification system
        # Examples: Email, SMS, Slack, Webhook, etc.
        pass
    
    def _start_monitoring_threads(self):
        """Start background monitoring threads"""
        # Start alert cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_old_alerts, daemon=True)
        cleanup_thread.start()
        
        # Start failed login cleanup thread
        login_cleanup_thread = threading.Thread(target=self._cleanup_failed_logins, daemon=True)
        login_cleanup_thread.start()
    
    def _cleanup_old_alerts(self):
        """Clean up old alerts"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_alerts = []
                
                for alert_id, alert in self.active_alerts.items():
                    alert_time = datetime.fromisoformat(alert['timestamp'])
                    if (current_time - alert_time).total_seconds() > 3600:  # 1 hour
                        expired_alerts.append(alert_id)
                
                for alert_id in expired_alerts:
                    del self.active_alerts[alert_id]
                
                time.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in alert cleanup: {e}")
                time.sleep(60)
    
    def _cleanup_failed_logins(self):
        """Clean up old failed login attempts"""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_clusters = []
                
                for cluster_key, failures in self.failed_login_clusters.items():
                    # Remove failures older than 1 hour
                    recent_failures = [
                        failure for failure in failures
                        if (current_time - datetime.fromisoformat(failure['timestamp'])).total_seconds() <= 3600
                    ]
                    
                    if recent_failures:
                        self.failed_login_clusters[cluster_key] = recent_failures
                    else:
                        expired_clusters.append(cluster_key)
                
                for cluster_key in expired_clusters:
                    del self.failed_login_clusters[cluster_key]
                
                time.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in failed login cleanup: {e}")
                time.sleep(60)

class UserBehaviorAnomalyDetector:
    """Detector for user behavior anomalies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_profiles = defaultdict(dict)
        self.behavior_baselines = defaultdict(dict)
    
    def detect_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Detect user behavior anomalies"""
        anomalies = []
        user_id = event.user_id
        
        if not user_id:
            return anomalies
        
        # Update user profile
        self._update_user_profile(event)
        
        # Check for behavioral anomalies
        anomalies.extend(self._check_behavioral_anomalies(event))
        
        return anomalies
    
    def _update_user_profile(self, event: SecurityEvent):
        """Update user behavior profile"""
        user_id = event.user_id
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                'first_seen': event.timestamp,
                'last_seen': event.timestamp,
                'event_count': 0,
                'event_types': defaultdict(int),
                'session_patterns': defaultdict(int),
                'activity_hours': defaultdict(int),
                'ip_addresses': set(),
                'user_agents': set()
            }
        
        profile = self.user_profiles[user_id]
        profile['last_seen'] = event.timestamp
        profile['event_count'] += 1
        profile['event_types'][event.event_type.value] += 1
        
        if event.ip_address:
            profile['ip_addresses'].add(event.ip_address)
        if event.user_agent:
            profile['user_agents'].add(event.user_agent)
        
        # Update temporal patterns
        event_time = datetime.fromisoformat(event.timestamp)
        profile['activity_hours'][event_time.hour] += 1
    
    def _check_behavioral_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for behavioral anomalies"""
        anomalies = []
        user_id = event.user_id
        profile = self.user_profiles.get(user_id, {})
        
        # Check for unusual activity hours
        event_time = datetime.fromisoformat(event.timestamp)
        hour = event_time.hour
        
        if profile.get('activity_hours'):
            # Calculate normal activity hours
            total_activity = sum(profile['activity_hours'].values())
            hour_percentage = profile['activity_hours'].get(hour, 0) / total_activity
            
            if hour_percentage < 0.05:  # Less than 5% of activity at this hour
                anomalies.append({
                    'type': 'unusual_activity_hour',
                    'severity': 'medium',
                    'description': f'Unusual activity hour detected: {hour}:00',
                    'details': {
                        'hour': hour,
                        'activity_percentage': hour_percentage,
                        'total_activity': total_activity
                    },
                    'recommendations': [
                        'Verify user identity',
                        'Check for account compromise',
                        'Enable additional authentication'
                    ]
                })
        
        # Check for unusual event types
        event_type_count = profile.get('event_types', {}).get(event.event_type.value, 0)
        total_events = profile.get('event_count', 0)
        
        if total_events > 10:  # Only check after sufficient history
            event_type_percentage = event_type_count / total_events
            
            if event_type_percentage < 0.1:  # Less than 10% of events are this type
                anomalies.append({
                    'type': 'unusual_event_type',
                    'severity': 'low',
                    'description': f'Unusual event type detected: {event.event_type.value}',
                    'details': {
                        'event_type': event.event_type.value,
                        'event_percentage': event_type_percentage,
                        'total_events': total_events
                    },
                    'recommendations': [
                        'Monitor for additional unusual activity',
                        'Review user permissions'
                    ]
                })
        
        return anomalies

class FinancialPatternAnomalyDetector:
    """Detector for unusual financial transaction patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_financial_profiles = defaultdict(dict)
        self.transaction_patterns = defaultdict(list)
    
    def detect_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Detect unusual financial patterns"""
        anomalies = []
        user_id = event.user_id
        
        if not user_id:
            return anomalies
        
        # Update financial profile
        self._update_financial_profile(event)
        
        # Check for financial anomalies
        anomalies.extend(self._check_financial_anomalies(event))
        
        return anomalies
    
    def _update_financial_profile(self, event: SecurityEvent):
        """Update user financial profile"""
        user_id = event.user_id
        
        if user_id not in self.user_financial_profiles:
            self.user_financial_profiles[user_id] = {
                'total_transactions': 0,
                'total_amount': 0.0,
                'average_amount': 0.0,
                'max_amount': 0.0,
                'transaction_frequency': defaultdict(int),
                'amount_distribution': defaultdict(int),
                'payment_methods': set(),
                'merchants': set(),
                'transaction_times': []
            }
        
        profile = self.user_financial_profiles[user_id]
        
        if event.event_type == SecurityEventType.PAYMENT_PROCESSING:
            amount = float(event.details.get('amount', 0)) if event.details else 0
            
            profile['total_transactions'] += 1
            profile['total_amount'] += amount
            profile['average_amount'] = profile['total_amount'] / profile['total_transactions']
            profile['max_amount'] = max(profile['max_amount'], amount)
            
            # Update amount distribution
            amount_range = self._get_amount_range(amount)
            profile['amount_distribution'][amount_range] += 1
            
            # Update payment methods
            if event.details and 'payment_method' in event.details:
                profile['payment_methods'].add(event.details['payment_method'])
            
            # Update merchants
            if event.details and 'merchant_id' in event.details:
                profile['merchants'].add(event.details['merchant_id'])
            
            # Update transaction times
            profile['transaction_times'].append(event.timestamp)
            
            # Keep only recent transactions (last 100)
            if len(profile['transaction_times']) > 100:
                profile['transaction_times'] = profile['transaction_times'][-100:]
    
    def _check_financial_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for financial anomalies"""
        anomalies = []
        user_id = event.user_id
        profile = self.user_financial_profiles.get(user_id, {})
        
        if event.event_type == SecurityEventType.PAYMENT_PROCESSING and event.details:
            amount = float(event.details.get('amount', 0))
            
            # Check for unusually large amounts
            if profile.get('average_amount', 0) > 0:
                amount_ratio = amount / profile['average_amount']
                
                if amount_ratio > 5:  # 5x the average amount
                    anomalies.append({
                        'type': 'unusually_large_amount',
                        'severity': 'high',
                        'description': f'Unusually large transaction amount: ${amount:,.2f}',
                        'details': {
                            'amount': amount,
                            'average_amount': profile['average_amount'],
                            'amount_ratio': amount_ratio
                        },
                        'recommendations': [
                            'Verify transaction legitimacy',
                            'Contact user for confirmation',
                            'Enable additional fraud checks'
                        ]
                    })
            
            # Check for unusual payment methods
            payment_method = event.details.get('payment_method', '')
            if payment_method and payment_method not in profile.get('payment_methods', set()):
                anomalies.append({
                    'type': 'unusual_payment_method',
                    'severity': 'medium',
                    'description': f'Unusual payment method used: {payment_method}',
                    'details': {
                        'payment_method': payment_method,
                        'previous_methods': list(profile.get('payment_methods', set()))
                    },
                    'recommendations': [
                        'Verify payment method ownership',
                        'Enable additional verification'
                    ]
                })
            
            # Check for rapid transactions
            recent_transactions = self._get_recent_transactions(user_id, 300)  # 5 minutes
            if len(recent_transactions) >= 3:
                anomalies.append({
                    'type': 'rapid_transactions',
                    'severity': 'high',
                    'description': f'Rapid transactions detected: {len(recent_transactions)} in 5 minutes',
                    'details': {
                        'transaction_count': len(recent_transactions),
                        'time_window': 300
                    },
                    'recommendations': [
                        'Investigate for potential fraud',
                        'Enable transaction delays',
                        'Contact user for verification'
                    ]
                })
        
        return anomalies
    
    def _get_amount_range(self, amount: float) -> str:
        """Get amount range category"""
        if amount < 100:
            return '0-100'
        elif amount < 500:
            return '100-500'
        elif amount < 1000:
            return '500-1000'
        elif amount < 5000:
            return '1000-5000'
        else:
            return '5000+'
    
    def _get_recent_transactions(self, user_id: str, window_seconds: int) -> List[str]:
        """Get recent transactions within time window"""
        profile = self.user_financial_profiles.get(user_id, {})
        transaction_times = profile.get('transaction_times', [])
        
        current_time = datetime.utcnow()
        recent_transactions = []
        
        for timestamp in transaction_times:
            transaction_time = datetime.fromisoformat(timestamp)
            if (current_time - transaction_time).total_seconds() <= window_seconds:
                recent_transactions.append(timestamp)
        
        return recent_transactions

class APIUsageAnomalyDetector:
    """Detector for suspicious API usage patterns"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_usage_profiles = defaultdict(dict)
        self.endpoint_patterns = defaultdict(list)
        self.rate_limit_violations = defaultdict(list)
    
    def detect_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Detect suspicious API usage patterns"""
        anomalies = []
        user_id = event.user_id
        ip_address = event.ip_address
        
        if not user_id or not ip_address:
            return anomalies
        
        # Update API usage profile
        self._update_api_profile(event)
        
        # Check for API anomalies
        anomalies.extend(self._check_api_anomalies(event))
        
        return anomalies
    
    def _update_api_profile(self, event: SecurityEvent):
        """Update API usage profile"""
        user_id = event.user_id
        ip_address = event.ip_address
        
        profile_key = f"{user_id}_{ip_address}"
        
        if profile_key not in self.api_usage_profiles:
            self.api_usage_profiles[profile_key] = {
                'total_requests': 0,
                'endpoint_usage': defaultdict(int),
                'request_methods': defaultdict(int),
                'response_codes': defaultdict(int),
                'request_times': [],
                'rate_limit_violations': 0,
                'unusual_endpoints': set()
            }
        
        profile = self.api_usage_profiles[profile_key]
        profile['total_requests'] += 1
        
        # Update endpoint usage
        if event.request_url:
            endpoint = self._extract_endpoint(event.request_url)
            profile['endpoint_usage'][endpoint] += 1
        
        # Update request methods
        if event.request_method:
            profile['request_methods'][event.request_method] += 1
        
        # Update response codes
        if event.response_status:
            profile['response_codes'][event.response_status] += 1
        
        # Update request times
        profile['request_times'].append(event.timestamp)
        
        # Keep only recent requests (last 1000)
        if len(profile['request_times']) > 1000:
            profile['request_times'] = profile['request_times'][-1000:]
        
        # Track rate limit violations
        if event.event_type == SecurityEventType.RATE_LIMITING_TRIGGER:
            profile['rate_limit_violations'] += 1
    
    def _check_api_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for API usage anomalies"""
        anomalies = []
        user_id = event.user_id
        ip_address = event.ip_address
        profile_key = f"{user_id}_{ip_address}"
        profile = self.api_usage_profiles.get(profile_key, {})
        
        # Check for excessive rate limit violations
        if profile.get('rate_limit_violations', 0) >= 5:
            anomalies.append({
                'type': 'excessive_rate_limit_violations',
                'severity': 'high',
                'description': f'Excessive rate limit violations: {profile["rate_limit_violations"]}',
                'details': {
                    'violation_count': profile['rate_limit_violations'],
                    'user_id': user_id,
                    'ip_address': ip_address
                },
                'recommendations': [
                    'Temporarily block IP address',
                    'Investigate for potential abuse',
                    'Review rate limiting configuration'
                ]
            })
        
        # Check for unusual endpoints
        if event.request_url:
            endpoint = self._extract_endpoint(event.request_url)
            total_requests = profile.get('total_requests', 0)
            endpoint_usage = profile.get('endpoint_usage', {}).get(endpoint, 0)
            
            if total_requests > 10 and endpoint_usage / total_requests < 0.05:
                # Endpoint used less than 5% of the time
                anomalies.append({
                    'type': 'unusual_endpoint_usage',
                    'severity': 'medium',
                    'description': f'Unusual endpoint usage: {endpoint}',
                    'details': {
                        'endpoint': endpoint,
                        'usage_percentage': endpoint_usage / total_requests,
                        'total_requests': total_requests
                    },
                    'recommendations': [
                        'Monitor for additional unusual activity',
                        'Review user permissions for this endpoint'
                    ]
                })
        
        # Check for rapid API requests
        recent_requests = self._get_recent_requests(profile_key, 60)  # 1 minute
        if len(recent_requests) >= 20:
            anomalies.append({
                'type': 'rapid_api_requests',
                'severity': 'medium',
                'description': f'Rapid API requests: {len(recent_requests)} in 1 minute',
                'details': {
                    'request_count': len(recent_requests),
                    'time_window': 60
                },
                'recommendations': [
                    'Check for automated requests',
                    'Review API usage patterns',
                    'Consider implementing request throttling'
                ]
            })
        
        return anomalies
    
    def _extract_endpoint(self, url: str) -> str:
        """Extract endpoint from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.path
        except:
            return url
    
    def _get_recent_requests(self, profile_key: str, window_seconds: int) -> List[str]:
        """Get recent requests within time window"""
        profile = self.api_usage_profiles.get(profile_key, {})
        request_times = profile.get('request_times', [])
        
        current_time = datetime.utcnow()
        recent_requests = []
        
        for timestamp in request_times:
            request_time = datetime.fromisoformat(timestamp)
            if (current_time - request_time).total_seconds() <= window_seconds:
                recent_requests.append(timestamp)
        
        return recent_requests

class GeographicAnomalyDetector:
    """Detector for geographic access anomalies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_locations = defaultdict(list)
        self.location_profiles = defaultdict(dict)
        self.distance_threshold = config.get('distance_threshold', 1000)  # 1000 km
    
    def detect_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Detect geographic anomalies"""
        anomalies = []
        user_id = event.user_id
        ip_address = event.ip_address
        
        if not user_id or not ip_address:
            return anomalies
        
        # Get location from IP address
        location = self._get_location_from_ip(ip_address)
        
        if location:
            # Update location profile
            self._update_location_profile(user_id, location, event.timestamp)
            
            # Check for geographic anomalies
            anomalies.extend(self._check_geographic_anomalies(user_id, location))
        
        return anomalies
    
    def _get_location_from_ip(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get location information from IP address"""
        # This is a simplified implementation
        # In production, you would use a geolocation service like MaxMind, IP2Location, etc.
        
        # Mock location data for demonstration
        mock_locations = {
            '192.168.1.100': {'city': 'New York', 'country': 'US', 'lat': 40.7128, 'lon': -74.0060},
            '192.168.1.101': {'city': 'Los Angeles', 'country': 'US', 'lat': 34.0522, 'lon': -118.2437},
            '10.0.0.1': {'city': 'London', 'country': 'GB', 'lat': 51.5074, 'lon': -0.1278}
        }
        
        return mock_locations.get(ip_address, {
            'city': 'Unknown',
            'country': 'Unknown',
            'lat': 0.0,
            'lon': 0.0
        })
    
    def _update_location_profile(self, user_id: str, location: Dict[str, Any], timestamp: str):
        """Update user location profile"""
        if user_id not in self.user_locations:
            self.user_locations[user_id] = []
        
        self.user_locations[user_id].append({
            'location': location,
            'timestamp': timestamp
        })
        
        # Keep only recent locations (last 50)
        if len(self.user_locations[user_id]) > 50:
            self.user_locations[user_id] = self.user_locations[user_id][-50:]
    
    def _check_geographic_anomalies(self, user_id: str, current_location: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for geographic anomalies"""
        anomalies = []
        user_locations = self.user_locations.get(user_id, [])
        
        if len(user_locations) < 2:
            return anomalies
        
        # Get previous location
        previous_location = user_locations[-2]['location']
        
        # Calculate distance between locations
        distance = self._calculate_distance(
            previous_location['lat'], previous_location['lon'],
            current_location['lat'], current_location['lon']
        )
        
        # Check if distance exceeds threshold
        if distance > self.distance_threshold:
            # Calculate time difference
            current_time = datetime.fromisoformat(user_locations[-1]['timestamp'])
            previous_time = datetime.fromisoformat(user_locations[-2]['timestamp'])
            time_diff = (current_time - previous_time).total_seconds() / 3600  # hours
            
            # Check if travel time is unrealistic
            if time_diff < distance / 1000:  # Assuming 1000 km/h as reasonable travel speed
                anomalies.append({
                    'type': 'unrealistic_travel',
                    'severity': 'high',
                    'description': f'Unrealistic travel detected: {distance:.0f} km in {time_diff:.1f} hours',
                    'details': {
                        'distance_km': distance,
                        'time_hours': time_diff,
                        'previous_location': previous_location,
                        'current_location': current_location,
                        'travel_speed_kmh': distance / time_diff
                    },
                    'recommendations': [
                        'Verify user identity',
                        'Check for account compromise',
                        'Enable additional authentication',
                        'Investigate potential VPN usage'
                    ]
                })
        
        # Check for unusual country access
        if current_location['country'] != previous_location['country']:
            anomalies.append({
                'type': 'country_change',
                'severity': 'medium',
                'description': f'Access from different country: {previous_location["country"]} to {current_location["country"]}',
                'details': {
                    'previous_country': previous_location['country'],
                    'current_country': current_location['country'],
                    'previous_city': previous_location['city'],
                    'current_city': current_location['city']
                },
                'recommendations': [
                    'Verify travel plans',
                    'Enable additional verification',
                    'Monitor for additional unusual activity'
                ]
            })
        
        return anomalies
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        import math
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

class TemporalAnomalyDetector:
    """Detector for time-based access pattern anomalies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_temporal_profiles = defaultdict(dict)
        self.time_patterns = defaultdict(dict)
        self.unusual_hours = config.get('unusual_hours', {'start': 22, 'end': 6})
    
    def detect_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Detect time-based anomalies"""
        anomalies = []
        user_id = event.user_id
        
        if not user_id:
            return anomalies
        
        # Update temporal profile
        self._update_temporal_profile(event)
        
        # Check for temporal anomalies
        anomalies.extend(self._check_temporal_anomalies(event))
        
        return anomalies
    
    def _update_temporal_profile(self, event: SecurityEvent):
        """Update user temporal profile"""
        user_id = event.user_id
        event_time = datetime.fromisoformat(event.timestamp)
        
        if user_id not in self.user_temporal_profiles:
            self.user_temporal_profiles[user_id] = {
                'hourly_activity': defaultdict(int),
                'daily_activity': defaultdict(int),
                'weekly_activity': defaultdict(int),
                'monthly_activity': defaultdict(int),
                'activity_patterns': [],
                'last_activity': None
            }
        
        profile = self.user_temporal_profiles[user_id]
        
        # Update hourly activity
        hour = event_time.hour
        profile['hourly_activity'][hour] += 1
        
        # Update daily activity
        day = event_time.strftime('%A')  # Monday, Tuesday, etc.
        profile['daily_activity'][day] += 1
        
        # Update weekly activity
        week = event_time.strftime('%Y-%W')  # Year-Week
        profile['weekly_activity'][week] += 1
        
        # Update monthly activity
        month = event_time.strftime('%Y-%m')  # Year-Month
        profile['monthly_activity'][month] += 1
        
        # Update activity patterns
        profile['activity_patterns'].append({
            'timestamp': event.timestamp,
            'hour': hour,
            'day': day,
            'event_type': event.event_type.value
        })
        
        # Keep only recent patterns (last 1000)
        if len(profile['activity_patterns']) > 1000:
            profile['activity_patterns'] = profile['activity_patterns'][-1000:]
        
        profile['last_activity'] = event.timestamp
    
    def _check_temporal_anomalies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Check for temporal anomalies"""
        anomalies = []
        user_id = event.user_id
        profile = self.user_temporal_profiles.get(user_id, {})
        event_time = datetime.fromisoformat(event.timestamp)
        
        # Check for unusual hours
        hour = event_time.hour
        if hour >= self.unusual_hours['start'] or hour <= self.unusual_hours['end']:
            # Check if this is unusual for this user
            total_activity = sum(profile.get('hourly_activity', {}).values())
            hour_activity = profile.get('hourly_activity', {}).get(hour, 0)
            
            if total_activity > 10:  # Only check after sufficient history
                hour_percentage = hour_activity / total_activity
                
                if hour_percentage < 0.1:  # Less than 10% of activity at this hour
                    anomalies.append({
                        'type': 'unusual_activity_hour',
                        'severity': 'medium',
                        'description': f'Unusual activity hour: {hour}:00',
                        'details': {
                            'hour': hour,
                            'activity_percentage': hour_percentage,
                            'total_activity': total_activity,
                            'hour_activity': hour_activity
                        },
                        'recommendations': [
                            'Verify user identity',
                            'Check for account compromise',
                            'Enable additional authentication'
                        ]
                    })
        
        # Check for unusual days
        day = event_time.strftime('%A')
        total_activity = sum(profile.get('daily_activity', {}).values())
        day_activity = profile.get('daily_activity', {}).get(day, 0)
        
        if total_activity > 20:  # Only check after sufficient history
            day_percentage = day_activity / total_activity
            
            if day_percentage < 0.05:  # Less than 5% of activity on this day
                anomalies.append({
                    'type': 'unusual_activity_day',
                    'severity': 'low',
                    'description': f'Unusual activity day: {day}',
                    'details': {
                        'day': day,
                        'activity_percentage': day_percentage,
                        'total_activity': total_activity,
                        'day_activity': day_activity
                    },
                    'recommendations': [
                        'Monitor for additional unusual activity',
                        'Review user schedule patterns'
                    ]
                })
        
        # Check for long inactivity periods
        if profile.get('last_activity'):
            last_activity = datetime.fromisoformat(profile['last_activity'])
            inactivity_hours = (event_time - last_activity).total_seconds() / 3600
            
            if inactivity_hours > 168:  # More than 1 week
                anomalies.append({
                    'type': 'long_inactivity_period',
                    'severity': 'low',
                    'description': f'Long inactivity period: {inactivity_hours:.1f} hours',
                    'details': {
                        'inactivity_hours': inactivity_hours,
                        'last_activity': profile['last_activity'],
                        'current_activity': event.timestamp
                    },
                    'recommendations': [
                        'Welcome user back',
                        'Review account security',
                        'Check for any missed notifications'
                    ]
                })
        
        return anomalies 

# Convenience functions for monitoring features
def log_failed_login_attempt(logger: SecurityEventLogger, username: str, ip_address: str,
                           user_agent: str, failure_reason: str, details: Dict[str, Any] = None) -> str:
    """Log failed login attempt with clustering detection"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.AUTH_FAILURE,
        severity=SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        user_id=username,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'username': username,
            'failure_reason': failure_reason,
            **(details or {})
        },
        source="authentication_system"
    )
    
    return logger.log_event(event)

def log_unusual_financial_transaction(logger: SecurityEventLogger, user_id: str, amount: float,
                                    payment_method: str, transaction_id: str, ip_address: str,
                                    user_agent: str, details: Dict[str, Any] = None) -> str:
    """Log unusual financial transaction with pattern detection"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.PAYMENT_PROCESSING,
        severity=SecurityEventSeverity.HIGH,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'amount': amount,
            'payment_method': payment_method,
            'transaction_id': transaction_id,
            'unusual_pattern': True,
            **(details or {})
        },
        source="payment_processing_system"
    )
    
    return logger.log_event(event)

def log_suspicious_api_usage(logger: SecurityEventLogger, user_id: str, endpoint: str,
                           request_method: str, ip_address: str, user_agent: str,
                           response_status: int, details: Dict[str, Any] = None) -> str:
    """Log suspicious API usage with pattern detection"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.API_ACCESS,
        severity=SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_url=endpoint,
        response_status=response_status,
        details={
            'endpoint': endpoint,
            'suspicious_usage': True,
            **(details or {})
        },
        source="api_gateway"
    )
    
    return logger.log_event(event)

def log_geographic_anomaly(logger: SecurityEventLogger, user_id: str, ip_address: str,
                          previous_location: Dict[str, Any], current_location: Dict[str, Any],
                          user_agent: str, details: Dict[str, Any] = None) -> str:
    """Log geographic anomaly with location tracking"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        severity=SecurityEventSeverity.HIGH,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'anomaly_type': 'geographic',
            'previous_location': previous_location,
            'current_location': current_location,
            **(details or {})
        },
        source="geographic_monitoring_system"
    )
    
    return logger.log_event(event)

def log_time_based_anomaly(logger: SecurityEventLogger, user_id: str, ip_address: str,
                          user_agent: str, unusual_time: str, details: Dict[str, Any] = None) -> str:
    """Log time-based anomaly with temporal pattern detection"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        severity=SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={
            'anomaly_type': 'temporal',
            'unusual_time': unusual_time,
            **(details or {})
        },
        source="temporal_monitoring_system"
    )
    
    return logger.log_event(event)

def log_rate_limit_violation(logger: SecurityEventLogger, user_id: str, ip_address: str,
                           endpoint: str, limit_type: str, user_agent: str,
                           details: Dict[str, Any] = None) -> str:
    """Log rate limit violation with API usage pattern detection"""
    event = SecurityEvent(
        event_id=str(uuid.uuid4()),
        event_type=SecurityEventType.RATE_LIMITING_TRIGGER,
        severity=SecurityEventSeverity.MEDIUM,
        timestamp=datetime.utcnow().isoformat(),
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_url=endpoint,
        details={
            'endpoint': endpoint,
            'limit_type': limit_type,
            'violation': True,
            **(details or {})
        },
        source="rate_limiting_system"
    )
    
    return logger.log_event(event)