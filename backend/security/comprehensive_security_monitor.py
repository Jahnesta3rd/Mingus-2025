"""
Comprehensive Security Monitoring System for Assessment System
Includes security event logging, anomaly detection, and automated alerting
"""

import json
import logging
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import request, g
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Security event types"""
    AUTH_FAILURE = "auth_failure"
    AUTH_SUCCESS = "auth_success"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ASSESSMENT_ANOMALY = "assessment_anomaly"
    DATA_ACCESS_VIOLATION = "data_access_violation"
    SESSION_HIJACKING = "session_hijacking"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"

class SecuritySeverity(Enum):
    """Security severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    timestamp: datetime
    event_type: SecurityEventType
    user_identifier: str
    severity: SecuritySeverity
    ip_address: str
    user_agent: str
    endpoint: str
    method: str
    details: Dict[str, Any]

class SecurityMonitor:
    """Comprehensive security monitoring system"""
    
    def __init__(self, db_session: Session, redis_client: redis.Redis = None):
        self.db_session = db_session
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=0)
        self.setup_security_logger()
        self.setup_alert_thresholds()
        
    def setup_security_logger(self):
        """Setup dedicated security logger"""
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.INFO)
        
        # File handler for security events - use relative path for testing
        import os
        log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'security_events.log')
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.security_logger.addHandler(handler)
        
    def setup_alert_thresholds(self):
        """Setup alert thresholds for different security events"""
        self.alert_thresholds = {
            'failed_logins': {'count': 5, 'window': 300},  # 5 in 5 minutes
            'injection_attempts': {'count': 3, 'window': 300},  # 3 in 5 minutes
            'rate_limit_violations': {'count': 10, 'window': 600},  # 10 in 10 minutes
            'assessment_anomalies': {'count': 2, 'window': 3600},  # 2 in 1 hour
            'suspicious_activities': {'count': 5, 'window': 1800}  # 5 in 30 minutes
        }
        
    def log_security_event(self, event_type: SecurityEventType, user_identifier: str, 
                          details: Dict[str, Any], severity: SecuritySeverity = SecuritySeverity.INFO) -> SecurityEvent:
        """Log a security event with comprehensive details"""
        
        event_data = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            user_identifier=user_identifier,
            severity=severity,
            ip_address=request.remote_addr if request else 'unknown',
            user_agent=request.headers.get('User-Agent') if request else 'unknown',
            endpoint=request.endpoint if request else 'unknown',
            method=request.method if request else 'unknown',
            details=details
        )
        
        # Log the event
        log_message = json.dumps(asdict(event_data))
        if severity == SecuritySeverity.CRITICAL:
            self.security_logger.critical(log_message)
        elif severity == SecuritySeverity.WARNING:
            self.security_logger.warning(log_message)
        else:
            self.security_logger.info(log_message)
        
        # Store in database
        self._store_security_event(event_data)
        
        # Check if alert should be triggered
        self._check_alert_thresholds(event_type, event_data)
        
        return event_data
    
    def _store_security_event(self, event: SecurityEvent):
        """Store security event in database"""
        try:
            query = text("""
                INSERT INTO security_events 
                (timestamp, event_type, user_identifier, severity, ip_address, 
                 user_agent, endpoint, method, details, created_at)
                VALUES (:timestamp, :event_type, :user_identifier, :severity, :ip_address,
                        :user_agent, :endpoint, :method, :details, :created_at)
            """)
            
            self.db_session.execute(query, {
                'timestamp': event.timestamp,
                'event_type': event.event_type.value,
                'user_identifier': event.user_identifier,
                'severity': event.severity.value,
                'ip_address': event.ip_address,
                'user_agent': event.user_agent,
                'endpoint': event.endpoint,
                'method': event.method,
                'details': json.dumps(event.details),
                'created_at': datetime.utcnow()
            })
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error storing security event: {e}")
            self.db_session.rollback()
    
    def _check_alert_thresholds(self, event_type: SecurityEventType, event_data: SecurityEvent):
        """Check if alert thresholds have been exceeded"""
        
        # Map event types to threshold categories
        threshold_mapping = {
            SecurityEventType.AUTH_FAILURE: 'failed_logins',
            SecurityEventType.SQL_INJECTION_ATTEMPT: 'injection_attempts',
            SecurityEventType.XSS_ATTEMPT: 'injection_attempts',
            SecurityEventType.RATE_LIMIT_EXCEEDED: 'rate_limit_violations',
            SecurityEventType.ASSESSMENT_ANOMALY: 'assessment_anomalies',
            SecurityEventType.SUSPICIOUS_ACTIVITY: 'suspicious_activities'
        }
        
        threshold_key = threshold_mapping.get(event_type)
        if not threshold_key:
            return
        
        threshold = self.alert_thresholds[threshold_key]
        
        # Count recent events of this type
        recent_count = self._count_recent_events(event_type, threshold['window'])
        
        if recent_count >= threshold['count']:
            self._trigger_security_alert(event_type, event_data, recent_count)
    
    def _count_recent_events(self, event_type: SecurityEventType, window_seconds: int) -> int:
        """Count recent events of a specific type"""
        try:
            # Use Redis for fast counting
            key = f"security_events:{event_type.value}:{int(time.time() // window_seconds)}"
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Error counting recent events: {e}")
            return 0
    
    def _trigger_security_alert(self, event_type: SecurityEventType, event_data: SecurityEvent, count: int):
        """Trigger a security alert"""
        alert_data = {
            'alert_type': 'SECURITY_THRESHOLD_EXCEEDED',
            'event_type': event_type.value,
            'count': count,
            'timeframe': self.alert_thresholds.get(event_type.value, {}).get('window', 300),
            'latest_event': asdict(event_data)
        }
        
        # Send alert email
        self._send_security_alert_email(alert_data)
        
        # Log the alert
        self.security_logger.critical(f"SECURITY ALERT: {json.dumps(alert_data)}")
        
        # Store alert in database
        self._store_security_alert(alert_data)
    
    def _store_security_alert(self, alert_data: Dict[str, Any]):
        """Store security alert in database"""
        try:
            query = text("""
                INSERT INTO security_alerts 
                (alert_type, event_type, count, timeframe, alert_details, created_at)
                VALUES (:alert_type, :event_type, :count, :timeframe, :alert_details, :created_at)
            """)
            
            self.db_session.execute(query, {
                'alert_type': alert_data['alert_type'],
                'event_type': alert_data['event_type'],
                'count': alert_data['count'],
                'timeframe': alert_data['timeframe'],
                'alert_details': json.dumps(alert_data),
                'created_at': datetime.utcnow()
            })
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error storing security alert: {e}")
            self.db_session.rollback()
    
    def _send_security_alert_email(self, alert_data: Dict[str, Any]):
        """Send security alert email"""
        try:
            # Create alerter instance
            alerter = SecurityAlerter(
                smtp_host='smtp.gmail.com',
                smtp_port=587,
                username='security@mingus.com',
                password='your_app_password'
            )
            
            # Send the alert
            alerter.send_security_alert_email(alert_data)
            
        except Exception as e:
            logger.error(f"Error sending security alert email: {e}")

class SecurityAlerter:
    """Email alerting system for security events"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.alert_recipients = ['security@mingus.com', 'admin@mingus.com']
    
    def send_security_alert_email(self, alert_data: Dict[str, Any]):
        """Send security alert email"""
        subject = f"MINGUS Security Alert - {alert_data['event_type']}"
        
        body = f"""
        SECURITY ALERT TRIGGERED
        
        Event Type: {alert_data['event_type']}
        Count: {alert_data['count']} events
        Timeframe: {alert_data['timeframe']} seconds
        
        Latest Event Details:
        - Timestamp: {alert_data['latest_event']['timestamp']}
        - IP Address: {alert_data['latest_event']['ip_address']}
        - User Agent: {alert_data['latest_event']['user_agent']}
        - Endpoint: {alert_data['latest_event']['endpoint']}
        - User Identifier: {alert_data['latest_event']['user_identifier']}
        
        Please investigate immediately.
        """
        
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            for recipient in self.alert_recipients:
                msg['To'] = recipient
                server.send_message(msg)
                del msg['To']
            
            server.quit()
            logger.info(f"Security alert email sent for {alert_data['event_type']}")
            
        except Exception as e:
            logger.error(f"Failed to send security alert email: {str(e)}")

class AnomalyDetector:
    """Anomaly detection for assessment system"""
    
    def __init__(self):
        self.baseline_window = 7  # days
        self.anomaly_threshold = 2.5  # standard deviations
    
    def detect_assessment_anomalies(self, user_id: str, assessment_data: Dict) -> List[Dict]:
        """Detect anomalies in assessment submissions"""
        anomalies = []
        
        # Check completion time anomaly
        completion_time = assessment_data.get('completion_time', 0)
        avg_completion_time = self._get_average_completion_time(assessment_data['type'])
        
        if completion_time < avg_completion_time * 0.1:  # Suspiciously fast
            anomalies.append({
                'type': 'suspiciously_fast_completion',
                'value': completion_time,
                'expected_range': f"{avg_completion_time * 0.5}-{avg_completion_time * 2}",
                'severity': 'HIGH'
            })
        
        # Check answer pattern anomalies
        answers = assessment_data.get('responses', {})
        if self._has_suspicious_answer_pattern(answers):
            anomalies.append({
                'type': 'suspicious_answer_pattern',
                'details': 'Repetitive or random answer pattern detected',
                'severity': 'MEDIUM'
            })
        
        # Check for unusual score patterns
        score = assessment_data.get('score', 0)
        if self._is_unusual_score(assessment_data['type'], score):
            anomalies.append({
                'type': 'unusual_score',
                'value': score,
                'details': 'Score significantly different from typical range',
                'severity': 'MEDIUM'
            })
        
        return anomalies
    
    def _get_average_completion_time(self, assessment_type: str) -> float:
        """Get average completion time for assessment type"""
        # Query database for average completion times
        average_times = {
            'ai_job_risk': 240,      # 4 minutes
            'relationship_impact': 300,  # 5 minutes
            'tax_impact': 180,       # 3 minutes
            'income_comparison': 210  # 3.5 minutes
        }
        return average_times.get(assessment_type, 240)
    
    def _has_suspicious_answer_pattern(self, answers: Dict) -> bool:
        """Check for suspicious answer patterns"""
        values = list(answers.values())
        
        # Check for all identical answers
        if len(set(str(v) for v in values)) == 1:
            return True
        
        # Check for sequential patterns
        numeric_values = [v for v in values if isinstance(v, (int, float))]
        if len(numeric_values) >= 5:
            differences = [numeric_values[i+1] - numeric_values[i] 
                         for i in range(len(numeric_values)-1)]
            if len(set(differences)) == 1 and differences[0] != 0:
                return True
        
        # Check for alternating patterns
        if len(values) >= 4:
            alternating = all(values[i] == values[i+2] for i in range(len(values)-2))
            if alternating:
                return True
        
        return False
    
    def _is_unusual_score(self, assessment_type: str, score: float) -> bool:
        """Check if score is unusual for assessment type"""
        # Define typical score ranges for each assessment type
        score_ranges = {
            'ai_job_risk': (20, 80),      # 20-80% risk
            'relationship_impact': (10, 90),  # 10-90% impact
            'tax_impact': (15, 85),       # 15-85% impact
            'income_comparison': (25, 75)  # 25-75% comparison
        }
        
        min_score, max_score = score_ranges.get(assessment_type, (0, 100))
        return score < min_score or score > max_score

class SecurityMonitoringMiddleware:
    """Middleware for integrating security monitoring with Flask routes"""
    
    def __init__(self, security_monitor: SecurityMonitor, anomaly_detector: AnomalyDetector):
        self.security_monitor = security_monitor
        self.anomaly_detector = anomaly_detector
    
    def monitor_assessment_submission(self, user_id: str, assessment_data: Dict):
        """Monitor assessment submission for security issues"""
        
        # Check for anomalies
        anomalies = self.anomaly_detector.detect_assessment_anomalies(user_id, assessment_data)
        
        if anomalies:
            # Log security event for anomalies
            self.security_monitor.log_security_event(
                event_type=SecurityEventType.ASSESSMENT_ANOMALY,
                user_identifier=user_id,
                details={
                    'assessment_type': assessment_data['type'],
                    'anomalies': anomalies,
                    'completion_time': assessment_data.get('completion_time'),
                    'score': assessment_data.get('score')
                },
                severity=SecuritySeverity.WARNING
            )
        
        # Check for suspicious patterns in responses
        responses = assessment_data.get('responses', {})
        if self._detect_suspicious_patterns(responses):
            self.security_monitor.log_security_event(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_identifier=user_id,
                details={
                    'assessment_type': assessment_data['type'],
                    'suspicious_pattern': 'detected',
                    'response_count': len(responses)
                },
                severity=SecuritySeverity.WARNING
            )
    
    def _detect_suspicious_patterns(self, responses: Dict) -> bool:
        """Detect suspicious patterns in assessment responses"""
        
        # Check for injection attempts in text responses
        suspicious_patterns = [
            '<script', 'javascript:', 'onload=', 'onerror=',
            'union select', 'drop table', 'exec ', 'eval(',
            'document.cookie', 'window.location'
        ]
        
        for response in responses.values():
            if isinstance(response, str):
                response_lower = response.lower()
                for pattern in suspicious_patterns:
                    if pattern in response_lower:
                        return True
        
        return False
    
    def monitor_authentication(self, user_id: str, success: bool, details: Dict):
        """Monitor authentication attempts"""
        
        if not success:
            self.security_monitor.log_security_event(
                event_type=SecurityEventType.AUTH_FAILURE,
                user_identifier=user_id,
                details=details,
                severity=SecuritySeverity.WARNING
            )
        else:
            self.security_monitor.log_security_event(
                event_type=SecurityEventType.AUTH_SUCCESS,
                user_identifier=user_id,
                details=details,
                severity=SecuritySeverity.INFO
            )
    
    def monitor_rate_limit_violation(self, user_id: str, endpoint: str, details: Dict):
        """Monitor rate limit violations"""
        
        self.security_monitor.log_security_event(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            user_identifier=user_id,
            details={
                'endpoint': endpoint,
                **details
            },
            severity=SecuritySeverity.WARNING
        )
