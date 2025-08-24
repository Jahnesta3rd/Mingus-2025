"""
Enhanced Alerting System
Advanced multi-channel alerting with email, SMS, Slack, Discord, Teams, and webhook support
"""

import os
import json
import time
import smtplib
import requests
import threading
import queue
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from loguru import logger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import sqlite3
import hashlib
import uuid

from ..services.resend_email_service import resend_email_service

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
    DISCORD = "discord"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    OPSGENIE = "opsgenie"
    TELEGRAM = "telegram"

@dataclass
class AlertTemplate:
    """Alert template configuration"""
    name: str
    subject: str
    body_template: str
    html_template: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    channels: List[AlertChannel] = field(default_factory=lambda: [AlertChannel.EMAIL])

@dataclass
class AlertConfig:
    """Enhanced alert configuration"""
    # Email configuration
    email_enabled: bool = True
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = "alerts@mingus.com"
    to_emails: List[str] = field(default_factory=list)
    
    # SMS configuration (Twilio)
    sms_enabled: bool = True
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    to_phone_numbers: List[str] = field(default_factory=list)
    
    # Slack configuration
    slack_enabled: bool = True
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    slack_username: str = "Mingus Alerts"
    slack_icon_emoji: str = ":warning:"
    
    # Discord configuration
    discord_enabled: bool = True
    discord_webhook_url: str = ""
    discord_username: str = "Mingus Alerts"
    discord_avatar_url: str = ""
    
    # Microsoft Teams configuration
    teams_enabled: bool = True
    teams_webhook_url: str = ""
    teams_title: str = "Mingus Security Alert"
    
    # Webhook configuration
    webhook_enabled: bool = True
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)
    webhook_timeout: int = 30
    
    # PagerDuty configuration
    pagerduty_enabled: bool = True
    pagerduty_api_key: str = ""
    pagerduty_service_id: str = ""
    
    # OpsGenie configuration
    opsgenie_enabled: bool = True
    opsgenie_api_key: str = ""
    opsgenie_team: str = ""
    
    # Telegram configuration
    telegram_enabled: bool = True
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # General configuration
    alert_retention_days: int = 30
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    rate_limit_per_minute: int = 10
    enable_delivery_tracking: bool = True

class EnhancedAlertManager:
    """Enhanced alert management system with multiple channels"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
        self.alert_queue = queue.Queue()
        self.alert_history = deque(maxlen=10000)
        self.alert_workers = []
        self.templates = {}
        self.delivery_tracking = {}
        self.rate_limit_tracker = defaultdict(lambda: deque(maxlen=60))
        
        self._init_database()
        self._load_default_templates()
        self.start_alert_workers()
    
    def _init_database(self):
        """Initialize alert database"""
        try:
            db_path = "/var/lib/mingus/alerts.db"
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        priority TEXT NOT NULL,
                        message TEXT NOT NULL,
                        details TEXT,
                        channels TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        sent_at TEXT,
                        status TEXT DEFAULT 'pending',
                        retry_count INTEGER DEFAULT 0,
                        delivery_status TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alert_templates (
                        name TEXT PRIMARY KEY,
                        subject TEXT NOT NULL,
                        body_template TEXT NOT NULL,
                        html_template TEXT,
                        variables TEXT,
                        channels TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS delivery_tracking (
                        alert_id TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        sent_at TEXT NOT NULL,
                        status TEXT NOT NULL,
                        response TEXT,
                        retry_count INTEGER DEFAULT 0,
                        PRIMARY KEY (alert_id, channel)
                    )
                """)
        
        except Exception as e:
            logger.error(f"Error initializing alert database: {e}")
    
    def _load_default_templates(self):
        """Load default alert templates"""
        default_templates = {
            "security_alert": AlertTemplate(
                name="security_alert",
                subject="🚨 Security Alert: {event_type}",
                body_template="""
Security Alert Detected

Event Type: {event_type}
Severity: {severity}
Timestamp: {timestamp}
User: {user_id}
IP Address: {ip_address}
Details: {details}

Please review this alert immediately.

Best regards,
Mingus Security Team
                """,
                html_template="""
<html>
<body>
<h2 style="color: #d32f2f;">🚨 Security Alert Detected</h2>
<p><strong>Event Type:</strong> {event_type}</p>
<p><strong>Severity:</strong> <span style="color: {severity_color};">{severity}</span></p>
<p><strong>Timestamp:</strong> {timestamp}</p>
<p><strong>User:</strong> {user_id}</p>
<p><strong>IP Address:</strong> {ip_address}</p>
<p><strong>Details:</strong> {details}</p>
<hr>
<p><em>Please review this alert immediately.</em></p>
<p>Best regards,<br>Mingus Security Team</p>
</body>
</html>
                """,
                variables=["event_type", "severity", "timestamp", "user_id", "ip_address", "details"],
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.SMS]
            ),
            "performance_alert": AlertTemplate(
                name="performance_alert",
                subject="⚠️ Performance Alert: {metric_name}",
                body_template="""
Performance Alert

Metric: {metric_name}
Current Value: {current_value}
Threshold: {threshold}
Resource: {resource_name}
Timestamp: {timestamp}

This metric has exceeded the configured threshold.

Best regards,
Mingus Monitoring Team
                """,
                variables=["metric_name", "current_value", "threshold", "resource_name", "timestamp"],
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            "system_alert": AlertTemplate(
                name="system_alert",
                subject="🔧 System Alert: {system_name}",
                body_template="""
System Alert

System: {system_name}
Status: {status}
Issue: {issue}
Timestamp: {timestamp}
Impact: {impact}

Please investigate this system issue.

Best regards,
Mingus Operations Team
                """,
                variables=["system_name", "status", "issue", "timestamp", "impact"],
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.SMS]
            )
        }
        
        for template in default_templates.values():
            self.add_template(template)
    
    def add_template(self, template: AlertTemplate):
        """Add alert template"""
        self.templates[template.name] = template
        
        # Store in database
        try:
            with sqlite3.connect("/var/lib/mingus/alerts.db") as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO alert_templates 
                    (name, subject, body_template, html_template, variables, channels)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    template.name,
                    template.subject,
                    template.body_template,
                    template.html_template,
                    json.dumps(template.variables),
                    json.dumps([ch.value for ch in template.channels])
                ))
        except Exception as e:
            logger.error(f"Error storing template: {e}")
    
    def start_alert_workers(self):
        """Start background alert processing workers"""
        for i in range(5):  # 5 worker threads
            worker = threading.Thread(target=self._alert_worker, daemon=True, name=f"alert_worker_{i}")
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
                logger.error(f"Error in alert worker: {e}")
    
    def send_alert(self, priority: AlertPriority, message: str, 
                   details: Dict[str, Any] = None, channels: List[AlertChannel] = None,
                   template_name: str = None, template_vars: Dict[str, Any] = None):
        """Send alert through configured channels"""
        
        alert_id = str(uuid.uuid4())
        alert = {
            "id": alert_id,
            "priority": priority.value,
            "message": message,
            "details": details or {},
            "channels": channels or [AlertChannel.EMAIL],
            "template_name": template_name,
            "template_vars": template_vars or {},
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        # Check rate limiting
        if not self._check_rate_limit(priority):
            logger.warning(f"Rate limit exceeded for priority {priority.value}")
            return alert_id
        
        self.alert_queue.put(alert)
        self.alert_history.append(alert)
        
        # Store in database
        self._store_alert(alert)
        
        return alert_id
    
    def _check_rate_limit(self, priority: AlertPriority) -> bool:
        """Check rate limiting for alerts"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Clean old entries
        while (self.rate_limit_tracker[priority.value] and 
               self.rate_limit_tracker[priority.value][0] < minute_ago):
            self.rate_limit_tracker[priority.value].popleft()
        
        # Check if we're under the limit
        if len(self.rate_limit_tracker[priority.value]) >= self.config.rate_limit_per_minute:
            return False
        
        self.rate_limit_tracker[priority.value].append(current_time)
        return True
    
    def _process_alert(self, alert: Dict[str, Any]):
        """Process individual alert"""
        try:
            # Use template if specified
            if alert.get("template_name"):
                alert = self._apply_template(alert)
            
            # Send to each channel
            for channel in alert["channels"]:
                self._send_to_channel(alert, channel)
            
            # Update status
            alert["status"] = "sent"
            alert["sent_at"] = datetime.utcnow().isoformat()
            self._update_alert_status(alert["id"], "sent")
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            alert["status"] = "failed"
            self._update_alert_status(alert["id"], "failed", str(e))
    
    def _apply_template(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Apply template to alert"""
        template_name = alert["template_name"]
        template_vars = alert["template_vars"]
        
        if template_name not in self.templates:
            logger.warning(f"Template {template_name} not found")
            return alert
        
        template = self.templates[template_name]
        
        # Apply variables to templates
        subject = template.subject.format(**template_vars)
        body = template.body_template.format(**template_vars)
        html_body = template.html_template.format(**template_vars) if template.html_template else None
        
        # Add severity color for HTML
        if html_body and "severity_color" not in template_vars:
            severity = template_vars.get("severity", "medium")
            severity_colors = {
                "critical": "#d32f2f",
                "high": "#f57c00",
                "medium": "#fbc02d",
                "low": "#388e3c"
            }
            template_vars["severity_color"] = severity_colors.get(severity, "#757575")
            html_body = template.html_template.format(**template_vars)
        
        alert["subject"] = subject
        alert["body"] = body
        alert["html_body"] = html_body
        alert["channels"] = template.channels
        
        return alert
    
    def _send_to_channel(self, alert: Dict[str, Any], channel: AlertChannel):
        """Send alert to specific channel"""
        try:
            if channel == AlertChannel.EMAIL:
                self._send_email_alert(alert)
            elif channel == AlertChannel.SMS:
                self._send_sms_alert(alert)
            elif channel == AlertChannel.SLACK:
                self._send_slack_alert(alert)
            elif channel == AlertChannel.DISCORD:
                self._send_discord_alert(alert)
            elif channel == AlertChannel.TEAMS:
                self._send_teams_alert(alert)
            elif channel == AlertChannel.WEBHOOK:
                self._send_webhook_alert(alert)
            elif channel == AlertChannel.PAGERDUTY:
                self._send_pagerduty_alert(alert)
            elif channel == AlertChannel.OPSGENIE:
                self._send_opsgenie_alert(alert)
            elif channel == AlertChannel.TELEGRAM:
                self._send_telegram_alert(alert)
            
            # Track delivery
            if self.config.enable_delivery_tracking:
                self._track_delivery(alert["id"], channel, "sent")
        
        except Exception as e:
            logger.error(f"Error sending alert to {channel.value}: {e}")
            if self.config.enable_delivery_tracking:
                self._track_delivery(alert["id"], channel, "failed", str(e))
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert using Resend"""
        if not self.config.email_enabled:
            return
        
        try:
            # Send email via Resend
            result = resend_email_service.send_notification_email(
                user_email=', '.join(self.config.to_emails),
                subject=alert.get("subject", alert["message"]),
                message=alert.get("body", alert["message"]),
                notification_type='alert'
            )
            
            if result.get('success'):
                logger.info(f"Email alert sent: {alert['id']}")
            else:
                logger.error(f"Failed to send email alert: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            raise
    
    def _send_sms_alert(self, alert: Dict[str, Any]):
        """Send SMS alert via Twilio"""
        if not self.config.sms_enabled:
            return
        
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.config.twilio_account_sid}/Messages.json"
            
            for phone_number in self.config.to_phone_numbers:
                data = {
                    'From': self.config.twilio_phone_number,
                    'To': phone_number,
                    'Body': f"{alert.get('subject', 'Alert')}: {alert.get('body', alert['message'])}"
                }
                
                response = requests.post(url, data=data, auth=(self.config.twilio_account_sid, self.config.twilio_auth_token))
                response.raise_for_status()
            
            logger.info(f"SMS alert sent: {alert['id']}")
        
        except Exception as e:
            logger.error(f"Error sending SMS alert: {e}")
            raise
    
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Send Slack alert"""
        if not self.config.slack_enabled:
            return
        
        try:
            # Determine color based on priority
            priority_colors = {
                "critical": "#d32f2f",
                "high": "#f57c00",
                "medium": "#fbc02d",
                "low": "#388e3c"
            }
            
            color = priority_colors.get(alert["priority"], "#757575")
            
            payload = {
                "channel": self.config.slack_channel,
                "username": self.config.slack_username,
                "icon_emoji": self.config.slack_icon_emoji,
                "attachments": [{
                    "color": color,
                    "title": alert.get("subject", "Alert"),
                    "text": alert.get("body", alert["message"]),
                    "fields": [
                        {
                            "title": "Priority",
                            "value": alert["priority"].upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert["created_at"],
                            "short": True
                        }
                    ],
                    "footer": "Mingus Security System"
                }]
            }
            
            response = requests.post(self.config.slack_webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Slack alert sent: {alert['id']}")
        
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            raise
    
    def _send_discord_alert(self, alert: Dict[str, Any]):
        """Send Discord alert"""
        if not self.config.discord_enabled:
            return
        
        try:
            # Determine color based on priority
            priority_colors = {
                "critical": 0xd32f2f,
                "high": 0xf57c00,
                "medium": 0xfbc02d,
                "low": 0x388e3c
            }
            
            color = priority_colors.get(alert["priority"], 0x757575)
            
            payload = {
                "username": self.config.discord_username,
                "avatar_url": self.config.discord_avatar_url,
                "embeds": [{
                    "title": alert.get("subject", "Alert"),
                    "description": alert.get("body", alert["message"]),
                    "color": color,
                    "fields": [
                        {
                            "name": "Priority",
                            "value": alert["priority"].upper(),
                            "inline": True
                        },
                        {
                            "name": "Time",
                            "value": alert["created_at"],
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": "Mingus Security System"
                    }
                }]
            }
            
            response = requests.post(self.config.discord_webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Discord alert sent: {alert['id']}")
        
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
            raise
    
    def _send_teams_alert(self, alert: Dict[str, Any]):
        """Send Microsoft Teams alert"""
        if not self.config.teams_enabled:
            return
        
        try:
            # Determine color based on priority
            priority_colors = {
                "critical": "#d32f2f",
                "high": "#f57c00",
                "medium": "#fbc02d",
                "low": "#388e3c"
            }
            
            color = priority_colors.get(alert["priority"], "#757575")
            
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color,
                "summary": alert.get("subject", "Alert"),
                "sections": [{
                    "activityTitle": alert.get("subject", "Alert"),
                    "activitySubtitle": f"Priority: {alert['priority'].upper()}",
                    "text": alert.get("body", alert["message"]),
                    "facts": [
                        {
                            "name": "Priority",
                            "value": alert["priority"].upper()
                        },
                        {
                            "name": "Time",
                            "value": alert["created_at"]
                        }
                    ]
                }]
            }
            
            response = requests.post(self.config.teams_webhook_url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Teams alert sent: {alert['id']}")
        
        except Exception as e:
            logger.error(f"Error sending Teams alert: {e}")
            raise
    
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Send webhook alert"""
        if not self.config.webhook_enabled:
            return
        
        try:
            payload = {
                "alert_id": alert["id"],
                "priority": alert["priority"],
                "message": alert.get("body", alert["message"]),
                "subject": alert.get("subject", "Alert"),
                "details": alert["details"],
                "timestamp": alert["created_at"],
                "source": "mingus_security"
            }
            
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                headers=self.config.webhook_headers,
                timeout=self.config.webhook_timeout
            )
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent: {alert['id']}")
        
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
            raise
    
    def _send_pagerduty_alert(self, alert: Dict[str, Any]):
        """Send PagerDuty alert"""
        if not self.config.pagerduty_enabled:
            return
        
        try:
            # Map priority to PagerDuty severity
            severity_map = {
                "critical": "critical",
                "high": "error",
                "medium": "warning",
                "low": "info"
            }
            
            payload = {
                "routing_key": self.config.pagerduty_api_key,
                "event_action": "trigger",
                "payload": {
                    "summary": alert.get("subject", "Alert"),
                    "severity": severity_map.get(alert["priority"], "warning"),
                    "source": "mingus_security",
                    "custom_details": {
                        "message": alert.get("body", alert["message"]),
                        "details": alert["details"],
                        "alert_id": alert["id"]
                    }
                }
            }
            
            response = requests.post("https://events.pagerduty.com/v2/enqueue", json=payload)
            response.raise_for_status()
            
            logger.info(f"PagerDuty alert sent: {alert['id']}")
        
        except Exception as e:
            logger.error(f"Error sending PagerDuty alert: {e}")
            raise
    
    def _send_opsgenie_alert(self, alert: Dict[str, Any]):
        """Send OpsGenie alert"""
        if not self.config.opsgenie_enabled:
            return
        
        try:
            # Map priority to OpsGenie priority
            priority_map = {
                "critical": "P1",
                "high": "P2",
                "medium": "P3",
                "low": "P4"
            }
            
            payload = {
                "message": alert.get("subject", "Alert"),
                "description": alert.get("body", alert["message"]),
                "priority": priority_map.get(alert["priority"], "P3"),
                "tags": ["mingus", "security", alert["priority"]],
                "details": {
                    "alert_id": alert["id"],
                    "details": json.dumps(alert["details"])
                }
            }
            
            if self.config.opsgenie_team:
                payload["teams"] = [{"name": self.config.opsgenie_team}]
            
            headers = {
                "Authorization": f"GenieKey {self.config.opsgenie_api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post("https://api.opsgenie.com/v2/alerts", json=payload, headers=headers)
            response.raise_for_status()
            
            logger.info(f"OpsGenie alert sent: {alert['id']}")
        
        except Exception as e:
            logger.error(f"Error sending OpsGenie alert: {e}")
            raise
    
    def _send_telegram_alert(self, alert: Dict[str, Any]):
        """Send Telegram alert"""
        if not self.config.telegram_enabled:
            return
        
        try:
            message = f"🚨 *{alert.get('subject', 'Alert')}*\n\n"
            message += f"*Priority:* {alert['priority'].upper()}\n"
            message += f"*Time:* {alert['created_at']}\n\n"
            message += alert.get("body", alert["message"])
            
            url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.config.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            logger.info(f"Telegram alert sent: {alert['id']}")
        
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
            raise
    
    def _track_delivery(self, alert_id: str, channel: AlertChannel, status: str, response: str = None):
        """Track alert delivery status"""
        try:
            with sqlite3.connect("/var/lib/mingus/alerts.db") as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO delivery_tracking 
                    (alert_id, channel, sent_at, status, response)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    alert_id,
                    channel.value,
                    datetime.utcnow().isoformat(),
                    status,
                    response
                ))
        except Exception as e:
            logger.error(f"Error tracking delivery: {e}")
    
    def _store_alert(self, alert: Dict[str, Any]):
        """Store alert in database"""
        try:
            with sqlite3.connect("/var/lib/mingus/alerts.db") as conn:
                conn.execute("""
                    INSERT INTO alerts 
                    (id, priority, message, details, channels, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert["id"],
                    alert["priority"],
                    alert["message"],
                    json.dumps(alert["details"]),
                    json.dumps([ch.value for ch in alert["channels"]]),
                    alert["created_at"],
                    alert["status"]
                ))
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    def _update_alert_status(self, alert_id: str, status: str, error: str = None):
        """Update alert status in database"""
        try:
            with sqlite3.connect("/var/lib/mingus/alerts.db") as conn:
                conn.execute("""
                    UPDATE alerts 
                    SET status = ?, sent_at = ?
                    WHERE id = ?
                """, (
                    status,
                    datetime.utcnow().isoformat() if status == "sent" else None,
                    alert_id
                ))
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")
    
    def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            with sqlite3.connect("/var/lib/mingus/alerts.db") as conn:
                # Total alerts
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM alerts 
                    WHERE created_at >= ?
                """, (cutoff_time.isoformat(),))
                total_alerts = cursor.fetchone()[0]
                
                # Alerts by priority
                cursor = conn.execute("""
                    SELECT priority, COUNT(*) FROM alerts 
                    WHERE created_at >= ?
                    GROUP BY priority
                """, (cutoff_time.isoformat(),))
                by_priority = dict(cursor.fetchall())
                
                # Alerts by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) FROM alerts 
                    WHERE created_at >= ?
                    GROUP BY status
                """, (cutoff_time.isoformat(),))
                by_status = dict(cursor.fetchall())
                
                # Delivery statistics
                cursor = conn.execute("""
                    SELECT channel, status, COUNT(*) FROM delivery_tracking 
                    WHERE sent_at >= ?
                    GROUP BY channel, status
                """, (cutoff_time.isoformat(),))
                delivery_stats = {}
                for row in cursor.fetchall():
                    channel, status, count = row
                    if channel not in delivery_stats:
                        delivery_stats[channel] = {}
                    delivery_stats[channel][status] = count
            
            return {
                "total_alerts": total_alerts,
                "by_priority": by_priority,
                "by_status": by_status,
                "delivery_stats": delivery_stats,
                "hours": hours
            }
        
        except Exception as e:
            logger.error(f"Error getting alert stats: {e}")
            return {"error": str(e)}
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            with sqlite3.connect("/var/lib/mingus/alerts.db") as conn:
                cursor = conn.execute("""
                    SELECT id, priority, message, details, channels, created_at, status, sent_at
                    FROM alerts 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                alerts = []
                for row in cursor.fetchall():
                    alert = {
                        "id": row[0],
                        "priority": row[1],
                        "message": row[2],
                        "details": json.loads(row[3]) if row[3] else {},
                        "channels": json.loads(row[4]) if row[4] else [],
                        "created_at": row[5],
                        "status": row[6],
                        "sent_at": row[7]
                    }
                    alerts.append(alert)
                
                return alerts
        
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []

# Factory function for creating alert configuration
def create_alert_config() -> AlertConfig:
    """Create alert configuration from environment variables"""
    return AlertConfig(
        # Email configuration
        email_enabled=os.getenv('ALERT_EMAIL_ENABLED', 'true').lower() == 'true',
        smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        smtp_port=int(os.getenv('SMTP_PORT', '587')),
        smtp_username=os.getenv('SMTP_USERNAME', ''),
        smtp_password=os.getenv('SMTP_PASSWORD', ''),
        smtp_use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
        from_email=os.getenv('ALERT_FROM_EMAIL', 'alerts@mingus.com'),
        to_emails=os.getenv('ALERT_TO_EMAILS', '').split(',') if os.getenv('ALERT_TO_EMAILS') else [],
        
        # SMS configuration
        sms_enabled=os.getenv('ALERT_SMS_ENABLED', 'true').lower() == 'true',
        twilio_account_sid=os.getenv('TWILIO_ACCOUNT_SID', ''),
        twilio_auth_token=os.getenv('TWILIO_AUTH_TOKEN', ''),
        twilio_phone_number=os.getenv('TWILIO_PHONE_NUMBER', ''),
        to_phone_numbers=os.getenv('ALERT_TO_PHONES', '').split(',') if os.getenv('ALERT_TO_PHONES') else [],
        
        # Slack configuration
        slack_enabled=os.getenv('ALERT_SLACK_ENABLED', 'true').lower() == 'true',
        slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL', ''),
        slack_channel=os.getenv('SLACK_CHANNEL', '#alerts'),
        slack_username=os.getenv('SLACK_USERNAME', 'Mingus Alerts'),
        slack_icon_emoji=os.getenv('SLACK_ICON_EMOJI', ':warning:'),
        
        # Discord configuration
        discord_enabled=os.getenv('ALERT_DISCORD_ENABLED', 'true').lower() == 'true',
        discord_webhook_url=os.getenv('DISCORD_WEBHOOK_URL', ''),
        discord_username=os.getenv('DISCORD_USERNAME', 'Mingus Alerts'),
        discord_avatar_url=os.getenv('DISCORD_AVATAR_URL', ''),
        
        # Teams configuration
        teams_enabled=os.getenv('ALERT_TEAMS_ENABLED', 'true').lower() == 'true',
        teams_webhook_url=os.getenv('TEAMS_WEBHOOK_URL', ''),
        teams_title=os.getenv('TEAMS_TITLE', 'Mingus Security Alert'),
        
        # Webhook configuration
        webhook_enabled=os.getenv('ALERT_WEBHOOK_ENABLED', 'true').lower() == 'true',
        webhook_url=os.getenv('WEBHOOK_URL', ''),
        webhook_headers=json.loads(os.getenv('WEBHOOK_HEADERS', '{}')),
        webhook_timeout=int(os.getenv('WEBHOOK_TIMEOUT', '30')),
        
        # PagerDuty configuration
        pagerduty_enabled=os.getenv('ALERT_PAGERDUTY_ENABLED', 'true').lower() == 'true',
        pagerduty_api_key=os.getenv('PAGERDUTY_API_KEY', ''),
        pagerduty_service_id=os.getenv('PAGERDUTY_SERVICE_ID', ''),
        
        # OpsGenie configuration
        opsgenie_enabled=os.getenv('ALERT_OPSGENIE_ENABLED', 'true').lower() == 'true',
        opsgenie_api_key=os.getenv('OPSGENIE_API_KEY', ''),
        opsgenie_team=os.getenv('OPSGENIE_TEAM', ''),
        
        # Telegram configuration
        telegram_enabled=os.getenv('ALERT_TELEGRAM_ENABLED', 'true').lower() == 'true',
        telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
        telegram_chat_id=os.getenv('TELEGRAM_CHAT_ID', ''),
        
        # General configuration
        alert_retention_days=int(os.getenv('ALERT_RETENTION_DAYS', '30')),
        max_retries=int(os.getenv('ALERT_MAX_RETRIES', '3')),
        retry_delay=int(os.getenv('ALERT_RETRY_DELAY', '60')),
        rate_limit_per_minute=int(os.getenv('ALERT_RATE_LIMIT_PER_MINUTE', '10')),
        enable_delivery_tracking=os.getenv('ALERT_DELIVERY_TRACKING', 'true').lower() == 'true'
    )

# Global alert manager instance
_alert_manager = None

def get_alert_manager() -> EnhancedAlertManager:
    """Get global alert manager instance"""
    global _alert_manager
    
    if _alert_manager is None:
        config = create_alert_config()
        _alert_manager = EnhancedAlertManager(config)
    
    return _alert_manager 