"""
Security Monitoring and Alerting Service
Detects and responds to suspicious verification activities
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import text
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    user_id: Optional[str]
    ip_address: str
    phone_number: Optional[str]
    risk_score: float
    timestamp: datetime
    details: Dict[str, Any]

class SecurityMonitor:
    """Monitors verification activities for suspicious behavior"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        
        # Alert thresholds
        self.alert_thresholds = {
            'high_risk_score': 0.8,
            'rapid_attempts': 10,  # attempts per minute
            'multiple_failures': 5,  # consecutive failures
            'suspicious_ip_activity': 20,  # events per hour
            'sim_swap_indicators': 3,  # phone changes per day
        }
        
        # Alert configuration
        self.alert_config = {
            'email_enabled': True,
            'email_recipients': ['security@mingus.com'],
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_username': 'your_email@gmail.com',
            'smtp_password': 'your_app_password',
        }
    
    def check_suspicious_activities(self) -> List[SecurityAlert]:
        """
        Check for suspicious activities and generate alerts
        
        Returns:
            List of security alerts
        """
        alerts = []
        
        try:
            # Check for high-risk activities
            alerts.extend(self._check_high_risk_activities())
            
            # Check for rapid attempts
            alerts.extend(self._check_rapid_attempts())
            
            # Check for multiple failures
            alerts.extend(self._check_multiple_failures())
            
            # Check for suspicious IP activity
            alerts.extend(self._check_suspicious_ip_activity())
            
            # Check for SIM swap indicators
            alerts.extend(self._check_sim_swap_indicators())
            
            # Process and send alerts
            for alert in alerts:
                self._process_alert(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking suspicious activities: {e}")
            return []
    
    def _check_high_risk_activities(self) -> List[SecurityAlert]:
        """Check for activities with high risk scores"""
        alerts = []
        
        try:
            query = text("""
                SELECT user_id, ip_address, phone_number, event_type, risk_score, created_at
                FROM verification_audit_log 
                WHERE risk_score > :threshold
                AND created_at >= :since_time
                ORDER BY created_at DESC
            """)
            
            since_time = datetime.utcnow() - timedelta(hours=1)
            
            results = self.db_session.execute(query, {
                'threshold': self.alert_thresholds['high_risk_score'],
                'since_time': since_time
            }).fetchall()
            
            for result in results:
                alert = SecurityAlert(
                    alert_type='high_risk_activity',
                    severity='high' if result.risk_score > 0.9 else 'medium',
                    title=f'High Risk Verification Activity',
                    description=f'User {result.user_id} had {result.event_type} with risk score {result.risk_score:.2f}',
                    user_id=result.user_id,
                    ip_address=result.ip_address,
                    phone_number=result.phone_number,
                    risk_score=result.risk_score,
                    timestamp=result.created_at,
                    details={
                        'event_type': result.event_type,
                        'risk_score': result.risk_score
                    }
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking high risk activities: {e}")
            return []
    
    def _check_rapid_attempts(self) -> List[SecurityAlert]:
        """Check for rapid verification attempts"""
        alerts = []
        
        try:
            query = text("""
                SELECT user_id, ip_address, phone_number, COUNT(*) as attempt_count
                FROM verification_audit_log 
                WHERE event_type IN ('send_code', 'verify_code')
                AND created_at >= :since_time
                GROUP BY user_id, ip_address
                HAVING COUNT(*) > :threshold
            """)
            
            since_time = datetime.utcnow() - timedelta(minutes=1)
            
            results = self.db_session.execute(query, {
                'since_time': since_time,
                'threshold': self.alert_thresholds['rapid_attempts']
            }).fetchall()
            
            for result in results:
                alert = SecurityAlert(
                    alert_type='rapid_attempts',
                    severity='high',
                    title=f'Rapid Verification Attempts',
                    description=f'User {result.user_id} made {result.attempt_count} attempts in 1 minute',
                    user_id=result.user_id,
                    ip_address=result.ip_address,
                    phone_number=result.phone_number,
                    risk_score=0.8,
                    timestamp=datetime.utcnow(),
                    details={
                        'attempt_count': result.attempt_count,
                        'time_window': '1 minute'
                    }
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking rapid attempts: {e}")
            return []
    
    def _check_multiple_failures(self) -> List[SecurityAlert]:
        """Check for multiple consecutive failures"""
        alerts = []
        
        try:
            query = text("""
                SELECT user_id, ip_address, phone_number, COUNT(*) as failure_count
                FROM verification_audit_log 
                WHERE event_type = 'verify_failed'
                AND created_at >= :since_time
                GROUP BY user_id, ip_address
                HAVING COUNT(*) >= :threshold
            """)
            
            since_time = datetime.utcnow() - timedelta(hours=1)
            
            results = self.db_session.execute(query, {
                'since_time': since_time,
                'threshold': self.alert_thresholds['multiple_failures']
            }).fetchall()
            
            for result in results:
                alert = SecurityAlert(
                    alert_type='multiple_failures',
                    severity='medium',
                    title=f'Multiple Verification Failures',
                    description=f'User {result.user_id} had {result.failure_count} failed attempts',
                    user_id=result.user_id,
                    ip_address=result.ip_address,
                    phone_number=result.phone_number,
                    risk_score=0.6,
                    timestamp=datetime.utcnow(),
                    details={
                        'failure_count': result.failure_count,
                        'time_window': '1 hour'
                    }
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking multiple failures: {e}")
            return []
    
    def _check_suspicious_ip_activity(self) -> List[SecurityAlert]:
        """Check for suspicious IP address activity"""
        alerts = []
        
        try:
            query = text("""
                SELECT ip_address, COUNT(*) as event_count,
                       COUNT(DISTINCT user_id) as unique_users,
                       COUNT(CASE WHEN event_type = 'verify_failed' THEN 1 END) as failed_attempts
                FROM verification_audit_log 
                WHERE created_at >= :since_time
                GROUP BY ip_address
                HAVING COUNT(*) > :threshold OR COUNT(DISTINCT user_id) > 5
            """)
            
            since_time = datetime.utcnow() - timedelta(hours=1)
            
            results = self.db_session.execute(query, {
                'since_time': since_time,
                'threshold': self.alert_thresholds['suspicious_ip_activity']
            }).fetchall()
            
            for result in results:
                alert = SecurityAlert(
                    alert_type='suspicious_ip',
                    severity='high',
                    title=f'Suspicious IP Activity',
                    description=f'IP {result.ip_address} had {result.event_count} events from {result.unique_users} users',
                    user_id=None,
                    ip_address=result.ip_address,
                    phone_number=None,
                    risk_score=0.9,
                    timestamp=datetime.utcnow(),
                    details={
                        'event_count': result.event_count,
                        'unique_users': result.unique_users,
                        'failed_attempts': result.failed_attempts
                    }
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking suspicious IP activity: {e}")
            return []
    
    def _check_sim_swap_indicators(self) -> List[SecurityAlert]:
        """Check for potential SIM swap indicators"""
        alerts = []
        
        try:
            query = text("""
                SELECT user_id, COUNT(DISTINCT phone_number) as phone_changes
                FROM phone_verification 
                WHERE created_at >= :since_time
                GROUP BY user_id
                HAVING COUNT(DISTINCT phone_number) >= :threshold
            """)
            
            since_time = datetime.utcnow() - timedelta(days=1)
            
            results = self.db_session.execute(query, {
                'since_time': since_time,
                'threshold': self.alert_thresholds['sim_swap_indicators']
            }).fetchall()
            
            for result in results:
                alert = SecurityAlert(
                    alert_type='sim_swap_indicator',
                    severity='critical',
                    title=f'Potential SIM Swap Attack',
                    description=f'User {result.user_id} changed phone {result.phone_changes} times in 24 hours',
                    user_id=result.user_id,
                    ip_address='unknown',
                    phone_number=None,
                    risk_score=0.95,
                    timestamp=datetime.utcnow(),
                    details={
                        'phone_changes': result.phone_changes,
                        'time_window': '24 hours'
                    }
                )
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking SIM swap indicators: {e}")
            return []
    
    def _process_alert(self, alert: SecurityAlert) -> None:
        """Process a security alert"""
        try:
            # Log the alert
            logger.warning(f"SECURITY ALERT: {alert.alert_type} - {alert.title} - {alert.description}")
            
            # Store alert in database
            self._store_alert(alert)
            
            # Send email notification for high/critical alerts
            if alert.severity in ['high', 'critical'] and self.alert_config['email_enabled']:
                self._send_alert_email(alert)
            
            # Take automated actions based on alert type
            self._take_automated_action(alert)
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    def _store_alert(self, alert: SecurityAlert) -> None:
        """Store alert in database"""
        try:
            query = text("""
                INSERT INTO security_alerts 
                (alert_type, severity, title, description, user_id, ip_address, 
                 phone_number, risk_score, alert_details, created_at)
                VALUES (:alert_type, :severity, :title, :description, :user_id, :ip_address,
                        :phone_number, :risk_score, :alert_details, :created_at)
            """)
            
            self.db_session.execute(query, {
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'description': alert.description,
                'user_id': alert.user_id,
                'ip_address': alert.ip_address,
                'phone_number': alert.phone_number,
                'risk_score': alert.risk_score,
                'alert_details': json.dumps(alert.details),
                'created_at': alert.timestamp
            })
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
            self.db_session.rollback()
    
    def _send_alert_email(self, alert: SecurityAlert) -> None:
        """Send alert email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.alert_config['smtp_username']
            msg['To'] = ', '.join(self.alert_config['email_recipients'])
            msg['Subject'] = f"SECURITY ALERT: {alert.title}"
            
            body = f"""
            Security Alert Detected
            
            Type: {alert.alert_type}
            Severity: {alert.severity.upper()}
            Title: {alert.title}
            Description: {alert.description}
            
            Details:
            - User ID: {alert.user_id or 'N/A'}
            - IP Address: {alert.ip_address}
            - Phone Number: {alert.phone_number or 'N/A'}
            - Risk Score: {alert.risk_score:.2f}
            - Timestamp: {alert.timestamp.isoformat()}
            
            Additional Details: {json.dumps(alert.details, indent=2)}
            
            Please investigate this activity immediately.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.alert_config['smtp_server'], self.alert_config['smtp_port'])
            server.starttls()
            server.login(self.alert_config['smtp_username'], self.alert_config['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alert email sent for {alert.alert_type}")
            
        except Exception as e:
            logger.error(f"Error sending alert email: {e}")
    
    def _take_automated_action(self, alert: SecurityAlert) -> None:
        """Take automated action based on alert type"""
        try:
            if alert.alert_type == 'suspicious_ip':
                # Block suspicious IP temporarily
                self._block_ip_temporarily(alert.ip_address)
            
            elif alert.alert_type == 'sim_swap_indicator':
                # Require additional verification for user
                self._require_additional_verification(alert.user_id)
            
            elif alert.alert_type == 'rapid_attempts':
                # Increase rate limiting for user/IP
                self._increase_rate_limiting(alert.user_id, alert.ip_address)
            
        except Exception as e:
            logger.error(f"Error taking automated action: {e}")
    
    def _block_ip_temporarily(self, ip_address: str) -> None:
        """Temporarily block an IP address"""
        try:
            # Add to blocked IPs table
            query = text("""
                INSERT OR REPLACE INTO blocked_ips 
                (ip_address, reason, blocked_until, created_at)
                VALUES (:ip_address, :reason, :blocked_until, :created_at)
            """)
            
            blocked_until = datetime.utcnow() + timedelta(hours=24)
            
            self.db_session.execute(query, {
                'ip_address': ip_address,
                'reason': 'suspicious_activity',
                'blocked_until': blocked_until,
                'created_at': datetime.utcnow()
            })
            
            self.db_session.commit()
            logger.info(f"IP {ip_address} blocked until {blocked_until}")
            
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
            self.db_session.rollback()
    
    def _require_additional_verification(self, user_id: str) -> None:
        """Require additional verification for user"""
        try:
            # Mark user for additional verification
            query = text("""
                UPDATE users 
                SET requires_additional_verification = true,
                    additional_verification_reason = 'sim_swap_suspicion',
                    updated_at = NOW()
                WHERE id = :user_id
            """)
            
            self.db_session.execute(query, {'user_id': user_id})
            self.db_session.commit()
            
            logger.info(f"User {user_id} marked for additional verification")
            
        except Exception as e:
            logger.error(f"Error requiring additional verification: {e}")
            self.db_session.rollback()
    
    def _increase_rate_limiting(self, user_id: str, ip_address: str) -> None:
        """Increase rate limiting for user/IP"""
        try:
            # This would update rate limiting configuration
            # For now, just log the action
            logger.info(f"Increased rate limiting for user {user_id} and IP {ip_address}")
            
        except Exception as e:
            logger.error(f"Error increasing rate limiting: {e}")
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get data for security dashboard"""
        try:
            # Get recent alerts
            alerts_query = text("""
                SELECT alert_type, severity, COUNT(*) as count
                FROM security_alerts 
                WHERE created_at >= :since_time
                GROUP BY alert_type, severity
            """)
            
            since_time = datetime.utcnow() - timedelta(days=7)
            
            alerts_result = self.db_session.execute(alerts_query, {
                'since_time': since_time
            }).fetchall()
            
            # Get suspicious IPs
            suspicious_ips_query = text("""
                SELECT * FROM suspicious_ips 
                ORDER BY avg_risk_score DESC 
                LIMIT 10
            """)
            
            suspicious_ips_result = self.db_session.execute(suspicious_ips_query).fetchall()
            
            # Get high-risk activities
            high_risk_query = text("""
                SELECT user_id, ip_address, event_type, risk_score, created_at
                FROM verification_audit_log 
                WHERE risk_score > 0.7
                AND created_at >= :since_time
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            
            high_risk_result = self.db_session.execute(high_risk_query, {
                'since_time': since_time
            }).fetchall()
            
            return {
                'alerts_summary': [
                    {
                        'alert_type': row.alert_type,
                        'severity': row.severity,
                        'count': row.count
                    }
                    for row in alerts_result
                ],
                'suspicious_ips': [
                    {
                        'ip_address': row.ip_address,
                        'total_events': row.total_events,
                        'failed_attempts': row.failed_attempts,
                        'avg_risk_score': float(row.avg_risk_score) if row.avg_risk_score else 0.0,
                        'last_activity': row.last_activity.isoformat() if row.last_activity else None
                    }
                    for row in suspicious_ips_result
                ],
                'high_risk_activities': [
                    {
                        'user_id': row.user_id,
                        'ip_address': row.ip_address,
                        'event_type': row.event_type,
                        'risk_score': float(row.risk_score) if row.risk_score else 0.0,
                        'created_at': row.created_at.isoformat() if row.created_at else None
                    }
                    for row in high_risk_result
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting security dashboard data: {e}")
            return {} 