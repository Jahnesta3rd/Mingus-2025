import requests
import smtplib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from dataclasses import dataclass
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import time

class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertChannel(Enum):
    """Alert notification channels"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"

class IncidentStatus(Enum):
    """Security incident status"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IncidentSeverity(Enum):
    """Security incident severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AlertConfig:
    """Alert configuration"""
    email_enabled: bool = True
    sms_enabled: bool = True
    slack_enabled: bool = False
    webhook_enabled: bool = False
    pagerduty_enabled: bool = False
    
    # Email configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    alert_email_recipients: List[str] = None
    
    # SMS configuration
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    alert_sms_recipients: List[str] = None
    
    # Slack configuration
    slack_webhook_url: str = ""
    slack_channel: str = "#security-alerts"
    
    # Webhook configuration
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = None
    
    # PagerDuty configuration
    pagerduty_api_key: str = ""
    pagerduty_service_id: str = ""

@dataclass
class DigitalOceanConfig:
    """Digital Ocean monitoring configuration"""
    api_token: str = ""
    droplet_ids: List[str] = None
    monitoring_enabled: bool = True
    metrics_interval: int = 300  # 5 minutes
    alert_thresholds: Dict[str, float] = None

@dataclass
class LogAggregationConfig:
    """Log aggregation configuration"""
    enabled: bool = True
    log_sources: List[str] = None
    aggregation_interval: int = 60  # 1 minute
    retention_days: int = 30
    analysis_enabled: bool = True
    anomaly_detection: bool = True

@dataclass
class IncidentResponseConfig:
    """Security incident response configuration"""
    enabled: bool = True
    auto_escalation: bool = True
    escalation_threshold: int = 3  # alerts
    response_team: List[str] = None
    playbooks: Dict[str, str] = None
    notification_channels: List[AlertChannel] = None

class DigitalOceanMonitor:
    """Digital Ocean monitoring integration"""
    
    def __init__(self, config: DigitalOceanConfig):
        self.config = config
        self.base_url = "https://api.digitalocean.com/v2"
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json"
        }
        self.metrics_cache = {}
        self.last_check = None
    
    def get_droplet_metrics(self, droplet_id: str) -> Dict[str, Any]:
        """Get metrics for a specific droplet"""
        try:
            url = f"{self.base_url}/monitoring/metrics/droplet/{droplet_id}"
            params = {
                "start": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "end": datetime.utcnow().isoformat(),
                "host_id": droplet_id
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            logging.error(f"Error getting Digital Ocean metrics: {e}")
            return {}
    
    def get_all_droplets(self) -> List[Dict[str, Any]]:
        """Get all droplets"""
        try:
            url = f"{self.base_url}/droplets"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json().get("droplets", [])
        
        except Exception as e:
            logging.error(f"Error getting Digital Ocean droplets: {e}")
            return []
    
    def check_metrics_thresholds(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check metrics against configured thresholds"""
        alerts = []
        
        if not self.config.alert_thresholds:
            return alerts
        
        for metric_name, threshold in self.config.alert_thresholds.items():
            if metric_name in metrics:
                current_value = metrics[metric_name]
                if current_value > threshold:
                    alerts.append({
                        "metric": metric_name,
                        "current_value": current_value,
                        "threshold": threshold,
                        "severity": "high" if current_value > threshold * 1.5 else "medium"
                    })
        
        return alerts
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health from Digital Ocean"""
        try:
            health_data = {
                "droplets": [],
                "total_alerts": 0,
                "overall_status": "healthy"
            }
            
            droplets = self.get_all_droplets()
            
            for droplet in droplets:
                droplet_id = droplet["id"]
                metrics = self.get_droplet_metrics(droplet_id)
                alerts = self.check_metrics_thresholds(metrics)
                
                droplet_health = {
                    "id": droplet_id,
                    "name": droplet["name"],
                    "status": droplet["status"],
                    "metrics": metrics,
                    "alerts": alerts,
                    "health_score": self._calculate_health_score(metrics, alerts)
                }
                
                health_data["droplets"].append(droplet_health)
                health_data["total_alerts"] += len(alerts)
            
            # Determine overall status
            if health_data["total_alerts"] > 5:
                health_data["overall_status"] = "critical"
            elif health_data["total_alerts"] > 2:
                health_data["overall_status"] = "warning"
            
            return health_data
        
        except Exception as e:
            logging.error(f"Error getting Digital Ocean system health: {e}")
            return {"overall_status": "error", "error": str(e)}

class AlertManager:
    """Comprehensive alert management system"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
        self.alert_queue = queue.Queue()
        self.alert_history = []
        self.alert_workers = []
        self.start_alert_workers()
    
    def start_alert_workers(self):
        """Start background alert processing workers"""
        for i in range(3):  # 3 worker threads
            worker = threading.Thread(target=self._alert_worker, daemon=True)
            worker.start()
            self.alert_workers.append(worker)
    
    def _alert_worker(self):
        """Background worker for processing alerts"""
        while True:
            try:
                alert = self.alert_queue.get(timeout=1)
                self._process_alert(alert)
                self.alert_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error in alert worker: {e}")
    
    def send_alert(self, priority: AlertPriority, message: str, 
                   details: Dict[str, Any] = None, channels: List[AlertChannel] = None):
        """Send alert through configured channels"""
        alert = {
            "id": f"alert_{int(time.time())}_{hash(message) % 10000}",
            "timestamp": datetime.utcnow().isoformat(),
            "priority": priority.value,
            "message": message,
            "details": details or {},
            "channels": channels or [AlertChannel.EMAIL, AlertChannel.SMS]
        }
        
        self.alert_queue.put(alert)
        self.alert_history.append(alert)
        
        # Keep only last 1000 alerts
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process individual alert"""
        for channel in alert["channels"]:
            try:
                if channel == AlertChannel.EMAIL and self.config.email_enabled:
                    self._send_email_alert(alert)
                elif channel == AlertChannel.SMS and self.config.sms_enabled:
                    self._send_sms_alert(alert)
                elif channel == AlertChannel.SLACK and self.config.slack_enabled:
                    self._send_slack_alert(alert)
                elif channel == AlertChannel.WEBHOOK and self.config.webhook_enabled:
                    self._send_webhook_alert(alert)
                elif channel == AlertChannel.PAGERDUTY and self.config.pagerduty_enabled:
                    self._send_pagerduty_alert(alert)
            except Exception as e:
                logging.error(f"Error sending alert via {channel.value}: {e}")
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert"""
        if not self.config.alert_email_recipients:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username
            msg['To'] = ", ".join(self.config.alert_email_recipients)
            msg['Subject'] = f"[{alert['priority'].upper()}] MINGUS Security Alert"
            
            body = f"""
            Security Alert - {alert['priority'].upper()}
            
            Message: {alert['message']}
            Time: {alert['timestamp']}
            Alert ID: {alert['id']}
            
            Details:
            {json.dumps(alert['details'], indent=2)}
            
            ---
            MINGUS Security System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
        
        except Exception as e:
            logging.error(f"Error sending email alert: {e}")
    
    def _send_sms_alert(self, alert: Dict[str, Any]):
        """Send SMS alert via Twilio"""
        if not self.config.alert_sms_recipients:
            return
        
        try:
            from twilio.rest import Client
            
            client = Client(self.config.twilio_account_sid, self.config.twilio_auth_token)
            
            message = f"[{alert['priority'].upper()}] {alert['message']}"
            
            for phone_number in self.config.alert_sms_recipients:
                client.messages.create(
                    body=message,
                    from_=self.config.twilio_phone_number,
                    to=phone_number
                )
        
        except Exception as e:
            logging.error(f"Error sending SMS alert: {e}")
    
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Send Slack alert"""
        try:
            payload = {
                "channel": self.config.slack_channel,
                "text": f"🚨 *Security Alert - {alert['priority'].upper()}*\n{alert['message']}",
                "attachments": [
                    {
                        "fields": [
                            {"title": "Time", "value": alert['timestamp'], "short": True},
                            {"title": "Alert ID", "value": alert['id'], "short": True},
                            {"title": "Details", "value": json.dumps(alert['details'], indent=2), "short": False}
                        ]
                    }
                ]
            }
            
            requests.post(self.config.slack_webhook_url, json=payload)
        
        except Exception as e:
            logging.error(f"Error sending Slack alert: {e}")
    
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Send webhook alert"""
        try:
            headers = self.config.webhook_headers or {}
            payload = {
                "alert": alert,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "mingus_security"
            }
            
            requests.post(self.config.webhook_url, json=payload, headers=headers)
        
        except Exception as e:
            logging.error(f"Error sending webhook alert: {e}")
    
    def _send_pagerduty_alert(self, alert: Dict[str, Any]):
        """Send PagerDuty alert"""
        try:
            payload = {
                "routing_key": self.config.pagerduty_api_key,
                "event_action": "trigger",
                "payload": {
                    "summary": f"Security Alert: {alert['message']}",
                    "severity": alert['priority'],
                    "source": "mingus_security",
                    "custom_details": alert['details']
                }
            }
            
            requests.post("https://events.pagerduty.com/v2/enqueue", json=payload)
        
        except Exception as e:
            logging.error(f"Error sending PagerDuty alert: {e}")
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history"""
        return self.alert_history[-limit:]
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        if not self.alert_history:
            return {"total_alerts": 0, "by_priority": {}, "by_channel": {}}
        
        by_priority = {}
        by_channel = {}
        
        for alert in self.alert_history:
            priority = alert['priority']
            by_priority[priority] = by_priority.get(priority, 0) + 1
            
            for channel in alert.get('channels', []):
                channel_name = channel.value if isinstance(channel, AlertChannel) else channel
                by_channel[channel_name] = by_channel.get(channel_name, 0) + 1
        
        return {
            "total_alerts": len(self.alert_history),
            "by_priority": by_priority,
            "by_channel": by_channel
        }

class LogAggregator:
    """Log aggregation and analysis system"""
    
    def __init__(self, config: LogAggregationConfig):
        self.config = config
        self.db_path = "/var/lib/mingus/log_aggregation.db"
        self.analysis_queue = queue.Queue()
        self.analysis_workers = []
        self._init_database()
        self.start_analysis_workers()
    
    def _init_database(self):
        """Initialize log aggregation database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregated_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS log_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    findings TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON aggregated_logs(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_source ON aggregated_logs(source)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_level ON aggregated_logs(level)
            """)
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error initializing log aggregation database: {e}")
    
    def start_analysis_workers(self):
        """Start background log analysis workers"""
        for i in range(2):  # 2 analysis worker threads
            worker = threading.Thread(target=self._analysis_worker, daemon=True)
            worker.start()
            self.analysis_workers.append(worker)
    
    def _analysis_worker(self):
        """Background worker for log analysis"""
        while True:
            try:
                log_batch = self.analysis_queue.get(timeout=1)
                self._analyze_logs(log_batch)
                self.analysis_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error in log analysis worker: {e}")
    
    def aggregate_logs(self, logs: List[Dict[str, Any]]):
        """Aggregate logs from various sources"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for log in logs:
                cursor.execute("""
                    INSERT INTO aggregated_logs (timestamp, source, level, message, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    log.get('timestamp', datetime.utcnow().isoformat()),
                    log.get('source', 'unknown'),
                    log.get('level', 'info'),
                    log.get('message', ''),
                    json.dumps(log.get('metadata', {}))
                ))
            
            conn.commit()
            conn.close()
            
            # Queue for analysis
            self.analysis_queue.put(logs)
        
        except Exception as e:
            logging.error(f"Error aggregating logs: {e}")
    
    def _analyze_logs(self, logs: List[Dict[str, Any]]):
        """Analyze aggregated logs for patterns and anomalies"""
        try:
            findings = []
            
            # Pattern analysis
            patterns = self._detect_patterns(logs)
            findings.extend(patterns)
            
            # Anomaly detection
            if self.config.anomaly_detection:
                anomalies = self._detect_anomalies(logs)
                findings.extend(anomalies)
            
            # Security analysis
            security_issues = self._detect_security_issues(logs)
            findings.extend(security_issues)
            
            # Store analysis results
            if findings:
                self._store_analysis_findings(findings)
        
        except Exception as e:
            logging.error(f"Error analyzing logs: {e}")
    
    def _detect_patterns(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect patterns in logs"""
        findings = []
        
        # Error rate analysis
        error_logs = [log for log in logs if log.get('level') in ['error', 'critical']]
        if len(error_logs) > len(logs) * 0.1:  # More than 10% errors
            findings.append({
                "type": "high_error_rate",
                "severity": "high",
                "description": f"High error rate detected: {len(error_logs)} errors out of {len(logs)} logs",
                "details": {"error_count": len(error_logs), "total_logs": len(logs)}
            })
        
        # Repeated error patterns
        error_messages = [log.get('message', '') for log in error_logs]
        message_counts = {}
        for message in error_messages:
            message_counts[message] = message_counts.get(message, 0) + 1
        
        for message, count in message_counts.items():
            if count > 5:  # Same error more than 5 times
                findings.append({
                    "type": "repeated_error",
                    "severity": "medium",
                    "description": f"Repeated error detected: '{message}' occurred {count} times",
                    "details": {"message": message, "count": count}
                })
        
        return findings
    
    def _detect_anomalies(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in logs"""
        findings = []
        
        # Unusual activity patterns
        timestamps = [log.get('timestamp') for log in logs if log.get('timestamp')]
        if timestamps:
            # Check for unusual time patterns
            hour_counts = {}
            for timestamp in timestamps:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = dt.hour
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                except:
                    continue
            
            # Detect unusual hours (outside business hours)
            unusual_hours = [hour for hour, count in hour_counts.items() 
                           if hour < 6 or hour > 22 and count > 10]
            
            if unusual_hours:
                findings.append({
                    "type": "unusual_activity_hours",
                    "severity": "medium",
                    "description": f"Unusual activity detected during hours: {unusual_hours}",
                    "details": {"unusual_hours": unusual_hours, "hour_counts": hour_counts}
                })
        
        return findings
    
    def _detect_security_issues(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect security-related issues in logs"""
        findings = []
        
        security_keywords = [
            'unauthorized', 'forbidden', 'authentication failed', 'login failed',
            'sql injection', 'xss', 'csrf', 'brute force', 'ddos', 'malware',
            'suspicious', 'anomaly', 'breach', 'compromise'
        ]
        
        for log in logs:
            message = log.get('message', '').lower()
            for keyword in security_keywords:
                if keyword in message:
                    findings.append({
                        "type": "security_keyword_detected",
                        "severity": "high",
                        "description": f"Security keyword '{keyword}' detected in logs",
                        "details": {
                            "keyword": keyword,
                            "message": log.get('message'),
                            "source": log.get('source'),
                            "timestamp": log.get('timestamp')
                        }
                    })
        
        return findings
    
    def _store_analysis_findings(self, findings: List[Dict[str, Any]]):
        """Store analysis findings in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for finding in findings:
                cursor.execute("""
                    INSERT INTO log_analysis (timestamp, analysis_type, findings, severity)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(),
                    finding['type'],
                    json.dumps(finding),
                    finding['severity']
                ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error storing analysis findings: {e}")
    
    def get_log_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get log statistics for the specified time period"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            
            # Total logs
            cursor.execute("""
                SELECT COUNT(*) FROM aggregated_logs WHERE timestamp >= ?
            """, (since,))
            total_logs = cursor.fetchone()[0]
            
            # Logs by level
            cursor.execute("""
                SELECT level, COUNT(*) FROM aggregated_logs 
                WHERE timestamp >= ? GROUP BY level
            """, (since,))
            logs_by_level = dict(cursor.fetchall())
            
            # Logs by source
            cursor.execute("""
                SELECT source, COUNT(*) FROM aggregated_logs 
                WHERE timestamp >= ? GROUP BY source
            """, (since,))
            logs_by_source = dict(cursor.fetchall())
            
            # Recent analysis findings
            cursor.execute("""
                SELECT analysis_type, severity, COUNT(*) FROM log_analysis 
                WHERE timestamp >= ? GROUP BY analysis_type, severity
            """, (since,))
            analysis_findings = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_logs": total_logs,
                "logs_by_level": logs_by_level,
                "logs_by_source": logs_by_source,
                "analysis_findings": analysis_findings,
                "time_period_hours": hours
            }
        
        except Exception as e:
            logging.error(f"Error getting log statistics: {e}")
            return {}

class SecurityIncidentManager:
    """Security incident response workflow management"""
    
    def __init__(self, config: IncidentResponseConfig):
        self.config = config
        self.db_path = "/var/lib/mingus/incidents.db"
        self.incidents = {}
        self.escalation_queue = queue.Queue()
        self.response_workers = []
        self._init_database()
        self.start_response_workers()
    
    def _init_database(self):
        """Initialize incident response database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_incidents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    assigned_to TEXT,
                    playbook TEXT,
                    timeline TEXT,
                    resolution TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incident_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    metadata TEXT
                )
            """)
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error initializing incident database: {e}")
    
    def start_response_workers(self):
        """Start incident response workers"""
        for i in range(2):  # 2 response worker threads
            worker = threading.Thread(target=self._response_worker, daemon=True)
            worker.start()
            self.response_workers.append(worker)
    
    def _response_worker(self):
        """Background worker for incident response"""
        while True:
            try:
                incident = self.escalation_queue.get(timeout=1)
                self._handle_incident_escalation(incident)
                self.escalation_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error in incident response worker: {e}")
    
    def create_incident(self, title: str, description: str, severity: IncidentSeverity,
                       source_alert: Dict[str, Any] = None) -> str:
        """Create a new security incident"""
        try:
            incident_id = f"incident_{int(time.time())}_{hash(title) % 10000}"
            
            incident = {
                "id": incident_id,
                "title": title,
                "description": description,
                "severity": severity.value,
                "status": IncidentStatus.OPEN.value,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "assigned_to": None,
                "playbook": self._get_playbook(severity),
                "timeline": [],
                "resolution": None,
                "source_alert": source_alert
            }
            
            # Store in database
            self._store_incident(incident)
            
            # Add to memory cache
            self.incidents[incident_id] = incident
            
            # Add initial event
            self.add_incident_event(incident_id, "incident_created", 
                                   f"Incident created with severity: {severity.value}")
            
            # Check for auto-escalation
            if self.config.auto_escalation:
                self._check_escalation(incident)
            
            return incident_id
        
        except Exception as e:
            logging.error(f"Error creating incident: {e}")
            return None
    
    def _get_playbook(self, severity: IncidentSeverity) -> str:
        """Get appropriate playbook for incident severity"""
        playbooks = self.config.playbooks or {}
        
        if severity == IncidentSeverity.CRITICAL:
            return playbooks.get("critical", "default_critical_playbook")
        elif severity == IncidentSeverity.HIGH:
            return playbooks.get("high", "default_high_playbook")
        elif severity == IncidentSeverity.MEDIUM:
            return playbooks.get("medium", "default_medium_playbook")
        else:
            return playbooks.get("low", "default_low_playbook")
    
    def _store_incident(self, incident: Dict[str, Any]):
        """Store incident in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO security_incidents 
                (id, title, description, severity, status, created_at, updated_at, 
                 assigned_to, playbook, timeline, resolution)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident["id"],
                incident["title"],
                incident["description"],
                incident["severity"],
                incident["status"],
                incident["created_at"],
                incident["updated_at"],
                incident["assigned_to"],
                incident["playbook"],
                json.dumps(incident["timeline"]),
                incident["resolution"]
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error storing incident: {e}")
    
    def add_incident_event(self, incident_id: str, event_type: str, description: str,
                          user_id: str = None, metadata: Dict[str, Any] = None):
        """Add event to incident timeline"""
        try:
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "description": description,
                "user_id": user_id,
                "metadata": metadata or {}
            }
            
            # Add to incident timeline
            if incident_id in self.incidents:
                self.incidents[incident_id]["timeline"].append(event)
                self.incidents[incident_id]["updated_at"] = event["timestamp"]
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO incident_events 
                (incident_id, event_type, description, timestamp, user_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                incident_id,
                event_type,
                description,
                event["timestamp"],
                user_id,
                json.dumps(metadata or {})
            ))
            
            # Update incident
            cursor.execute("""
                UPDATE security_incidents SET updated_at = ? WHERE id = ?
            """, (event["timestamp"], incident_id))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logging.error(f"Error adding incident event: {e}")
    
    def update_incident_status(self, incident_id: str, status: IncidentStatus,
                              user_id: str = None, resolution: str = None):
        """Update incident status"""
        try:
            if incident_id not in self.incidents:
                return False
            
            old_status = self.incidents[incident_id]["status"]
            self.incidents[incident_id]["status"] = status.value
            self.incidents[incident_id]["updated_at"] = datetime.utcnow().isoformat()
            
            if resolution:
                self.incidents[incident_id]["resolution"] = resolution
            
            # Add status change event
            self.add_incident_event(
                incident_id,
                "status_changed",
                f"Status changed from {old_status} to {status.value}",
                user_id
            )
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE security_incidents 
                SET status = ?, updated_at = ?, resolution = ?
                WHERE id = ?
            """, (status.value, self.incidents[incident_id]["updated_at"], 
                  resolution, incident_id))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            logging.error(f"Error updating incident status: {e}")
            return False
    
    def assign_incident(self, incident_id: str, assigned_to: str, user_id: str = None):
        """Assign incident to team member"""
        try:
            if incident_id not in self.incidents:
                return False
            
            self.incidents[incident_id]["assigned_to"] = assigned_to
            self.incidents[incident_id]["updated_at"] = datetime.utcnow().isoformat()
            
            # Add assignment event
            self.add_incident_event(
                incident_id,
                "assigned",
                f"Incident assigned to {assigned_to}",
                user_id
            )
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE security_incidents 
                SET assigned_to = ?, updated_at = ?
                WHERE id = ?
            """, (assigned_to, self.incidents[incident_id]["updated_at"], incident_id))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            logging.error(f"Error assigning incident: {e}")
            return False
    
    def _check_escalation(self, incident: Dict[str, Any]):
        """Check if incident needs escalation"""
        try:
            # Count recent incidents of same severity
            recent_incidents = [
                inc for inc in self.incidents.values()
                if inc["severity"] == incident["severity"] and
                inc["status"] in [IncidentStatus.OPEN.value, IncidentStatus.INVESTIGATING.value] and
                (datetime.utcnow() - datetime.fromisoformat(inc["created_at"])).total_seconds() < 3600  # 1 hour
            ]
            
            if len(recent_incidents) >= self.config.escalation_threshold:
                self.escalation_queue.put(incident)
        
        except Exception as e:
            logging.error(f"Error checking escalation: {e}")
    
    def _handle_incident_escalation(self, incident: Dict[str, Any]):
        """Handle incident escalation"""
        try:
            # Add escalation event
            self.add_incident_event(
                incident["id"],
                "escalated",
                f"Incident escalated due to threshold ({self.config.escalation_threshold} incidents in 1 hour)"
            )
            
            # Update status to investigating
            self.update_incident_status(incident["id"], IncidentStatus.INVESTIGATING)
            
            # Send notifications
            if self.config.notification_channels:
                # This would integrate with the AlertManager
                pass
        
        except Exception as e:
            logging.error(f"Error handling incident escalation: {e}")
    
    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get incident by ID"""
        return self.incidents.get(incident_id)
    
    def get_active_incidents(self) -> List[Dict[str, Any]]:
        """Get all active incidents"""
        return [
            incident for incident in self.incidents.values()
            if incident["status"] in [IncidentStatus.OPEN.value, IncidentStatus.INVESTIGATING.value]
        ]
    
    def get_incident_statistics(self) -> Dict[str, Any]:
        """Get incident statistics"""
        if not self.incidents:
            return {"total_incidents": 0, "by_severity": {}, "by_status": {}}
        
        by_severity = {}
        by_status = {}
        
        for incident in self.incidents.values():
            severity = incident["severity"]
            status = incident["status"]
            
            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_incidents": len(self.incidents),
            "by_severity": by_severity,
            "by_status": by_status,
            "active_incidents": len(self.get_active_incidents())
        }

class SecurityIntegrations:
    """Main integration orchestrator"""
    
    def __init__(self, alert_config: AlertConfig = None, 
                 digital_ocean_config: DigitalOceanConfig = None,
                 log_config: LogAggregationConfig = None,
                 incident_config: IncidentResponseConfig = None):
        
        self.alert_manager = AlertManager(alert_config or AlertConfig())
        self.digital_ocean_monitor = DigitalOceanMonitor(digital_ocean_config or DigitalOceanConfig())
        self.log_aggregator = LogAggregator(log_config or LogAggregationConfig())
        self.incident_manager = SecurityIncidentManager(incident_config or IncidentResponseConfig())
    
    def process_security_event(self, event: Dict[str, Any]):
        """Process security event through all integrations"""
        try:
            # Log aggregation
            self.log_aggregator.aggregate_logs([event])
            
            # Check for critical events that need alerts
            if event.get('severity') in ['critical', 'high']:
                self.alert_manager.send_alert(
                    AlertPriority.HIGH if event.get('severity') == 'high' else AlertPriority.CRITICAL,
                    f"Security Event: {event.get('event_type', 'Unknown')}",
                    event
                )
            
            # Check for incident creation
            if event.get('severity') == 'critical':
                self.incident_manager.create_incident(
                    f"Critical Security Event: {event.get('event_type', 'Unknown')}",
                    event.get('message', 'Critical security event detected'),
                    IncidentSeverity.CRITICAL,
                    event
                )
        
        except Exception as e:
            logging.error(f"Error processing security event: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations"""
        return {
            "alert_manager": {
                "enabled": True,
                "stats": self.alert_manager.get_alert_stats()
            },
            "digital_ocean_monitor": {
                "enabled": self.digital_ocean_monitor.config.monitoring_enabled,
                "health": self.digital_ocean_monitor.get_system_health()
            },
            "log_aggregator": {
                "enabled": self.log_aggregator.config.enabled,
                "stats": self.log_aggregator.get_log_statistics()
            },
            "incident_manager": {
                "enabled": self.incident_manager.config.enabled,
                "stats": self.incident_manager.get_incident_statistics()
            }
        }

# Utility functions for easy integration
def create_security_integrations(alert_config: AlertConfig = None,
                                digital_ocean_config: DigitalOceanConfig = None,
                                log_config: LogAggregationConfig = None,
                                incident_config: IncidentResponseConfig = None) -> SecurityIntegrations:
    """Create security integrations instance"""
    return SecurityIntegrations(alert_config, digital_ocean_config, log_config, incident_config)

def send_security_alert(integrations: SecurityIntegrations, priority: AlertPriority, 
                       message: str, details: Dict[str, Any] = None):
    """Send security alert through integrations"""
    integrations.alert_manager.send_alert(priority, message, details)

def create_security_incident(integrations: SecurityIntegrations, title: str, 
                           description: str, severity: IncidentSeverity) -> str:
    """Create security incident through integrations"""
    return integrations.incident_manager.create_incident(title, description, severity)

def get_digital_ocean_health(integrations: SecurityIntegrations) -> Dict[str, Any]:
    """Get Digital Ocean system health"""
    return integrations.digital_ocean_monitor.get_system_health()

def get_log_analysis(integrations: SecurityIntegrations, hours: int = 24) -> Dict[str, Any]:
    """Get log analysis results"""
    return integrations.log_aggregator.get_log_statistics(hours) 