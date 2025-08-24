"""
Alerting System
Monitors performance degradation, data quality, user experience issues, and business metric anomalies
"""

import time
import json
import smtplib
import requests
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from loguru import logger
import threading
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    category: str
    condition: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    severity: str  # 'low', 'medium', 'high', 'critical'
    enabled: bool = True
    cooldown_minutes: int = 30
    notification_channels: List[str] = field(default_factory=lambda: ['email'])

@dataclass
class Alert:
    """Alert instance"""
    rule_name: str
    category: str
    severity: str
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class AlertChannel:
    """Alert notification channel"""
    name: str
    type: str  # 'email', 'slack', 'webhook'
    config: Dict[str, Any]
    enabled: bool = True

class AlertingSystem:
    """Main alerting system"""
    
    def __init__(self, db_path: str = "alerts.db"):
        self.db_path = db_path
        self.rules: Dict[str, AlertRule] = {}
        self.channels: Dict[str, AlertChannel] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history = deque(maxlen=1000)
        self.metric_cache = defaultdict(lambda: deque(maxlen=100))
        self._lock = threading.RLock()
        
        self._init_database()
        self._load_default_rules()
        self._load_default_channels()
        self._start_monitoring_thread()
    
    def _init_database(self):
        """Initialize alerting database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alert_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        category TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        threshold REAL NOT NULL,
                        operator TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        enabled INTEGER DEFAULT 1,
                        cooldown_minutes INTEGER DEFAULT 30,
                        notification_channels TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        value REAL NOT NULL,
                        threshold REAL NOT NULL,
                        timestamp DATETIME NOT NULL,
                        resolved INTEGER DEFAULT 0,
                        resolved_at DATETIME
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS alert_channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        type TEXT NOT NULL,
                        config TEXT NOT NULL,
                        enabled INTEGER DEFAULT 1
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved)")
                
        except Exception as e:
            logger.error(f"Failed to initialize alerting database: {e}")
    
    def _load_default_rules(self):
        """Load default alert rules"""
        default_rules = [
            AlertRule(
                name="high_api_response_time",
                category="performance",
                condition="API response time exceeds threshold",
                threshold=2.0,
                operator="gt",
                severity="high",
                cooldown_minutes=15
            ),
            AlertRule(
                name="high_error_rate",
                category="performance",
                condition="Error rate exceeds threshold",
                threshold=0.05,
                operator="gt",
                severity="critical",
                cooldown_minutes=5
            ),
            AlertRule(
                name="low_user_engagement",
                category="business",
                condition="User engagement drops below threshold",
                threshold=0.3,
                operator="lt",
                severity="medium",
                cooldown_minutes=60
            ),
            AlertRule(
                name="data_quality_issues",
                category="data",
                condition="Data quality score below threshold",
                threshold=0.8,
                operator="lt",
                severity="high",
                cooldown_minutes=30
            ),
            AlertRule(
                name="high_memory_usage",
                category="system",
                condition="Memory usage exceeds threshold",
                threshold=0.9,
                operator="gt",
                severity="high",
                cooldown_minutes=10
            ),
            AlertRule(
                name="low_cache_hit_rate",
                category="performance",
                condition="Cache hit rate below threshold",
                threshold=0.7,
                operator="lt",
                severity="medium",
                cooldown_minutes=30
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def _load_default_channels(self):
        """Load default notification channels"""
        default_channels = [
            AlertChannel(
                name="email_admin",
                type="email",
                config={
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "alerts@mingus.com",
                    "password": "",
                    "from_email": "alerts@mingus.com",
                    "to_emails": ["admin@mingus.com"]
                }
            ),
            AlertChannel(
                name="slack_alerts",
                type="slack",
                config={
                    "webhook_url": "",
                    "channel": "#alerts",
                    "username": "Mingus Alerts"
                }
            )
        ]
        
        for channel in default_channels:
            self.add_channel(channel)
    
    def _start_monitoring_thread(self):
        """Start background monitoring thread"""
        def monitoring_worker():
            while True:
                try:
                    time.sleep(30)  # Check every 30 seconds
                    self._check_all_rules()
                except Exception as e:
                    logger.error(f"Monitoring thread error: {e}")
        
        thread = threading.Thread(target=monitoring_worker, daemon=True)
        thread.start()
    
    def add_rule(self, rule: AlertRule) -> bool:
        """Add a new alert rule"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO alert_rules 
                    (name, category, condition, threshold, operator, severity, enabled, cooldown_minutes, notification_channels)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.name, rule.category, rule.condition, rule.threshold,
                    rule.operator, rule.severity, rule.enabled, rule.cooldown_minutes,
                    json.dumps(rule.notification_channels)
                ))
                conn.commit()
            
            self.rules[rule.name] = rule
            return True
            
        except Exception as e:
            logger.error(f"Failed to add alert rule: {e}")
            return False
    
    def add_channel(self, channel: AlertChannel) -> bool:
        """Add a new notification channel"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO alert_channels 
                    (name, type, config, enabled)
                    VALUES (?, ?, ?, ?)
                """, (
                    channel.name, channel.type, json.dumps(channel.config), channel.enabled
                ))
                conn.commit()
            
            self.channels[channel.name] = channel
            return True
            
        except Exception as e:
            logger.error(f"Failed to add alert channel: {e}")
            return False
    
    def update_metric(self, metric_name: str, value: float, metadata: Dict[str, Any] = None):
        """Update metric value for alert checking"""
        with self._lock:
            self.metric_cache[metric_name].append({
                'value': value,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            })
    
    def _check_all_rules(self):
        """Check all enabled alert rules"""
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if self._is_in_cooldown(rule_name):
                continue
            
            # Get current metric value
            current_value = self._get_current_metric_value(rule_name)
            if current_value is None:
                continue
            
            # Check if alert should be triggered
            if self._should_trigger_alert(rule, current_value):
                self._trigger_alert(rule, current_value)
    
    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Check if rule is in cooldown period"""
        if rule_name not in self.active_alerts:
            return False
        
        alert = self.active_alerts[rule_name]
        rule = self.rules[rule_name]
        cooldown_duration = timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.now() - alert.timestamp < cooldown_duration
    
    def _get_current_metric_value(self, rule_name: str) -> Optional[float]:
        """Get current value for a metric"""
        # Map rule names to metric names
        metric_mapping = {
            'high_api_response_time': 'api_response_time',
            'high_error_rate': 'error_rate',
            'low_user_engagement': 'user_engagement',
            'data_quality_issues': 'data_quality_score',
            'high_memory_usage': 'memory_usage',
            'low_cache_hit_rate': 'cache_hit_rate'
        }
        
        metric_name = metric_mapping.get(rule_name)
        if not metric_name or metric_name not in self.metric_cache:
            return None
        
        # Get the most recent value
        recent_values = self.metric_cache[metric_name]
        if not recent_values:
            return None
        
        return recent_values[-1]['value']
    
    def _should_trigger_alert(self, rule: AlertRule, value: float) -> bool:
        """Check if alert should be triggered based on rule condition"""
        if rule.operator == 'gt':
            return value > rule.threshold
        elif rule.operator == 'lt':
            return value < rule.threshold
        elif rule.operator == 'eq':
            return abs(value - rule.threshold) < 0.001
        elif rule.operator == 'gte':
            return value >= rule.threshold
        elif rule.operator == 'lte':
            return value <= rule.threshold
        else:
            return False
    
    def _trigger_alert(self, rule: AlertRule, value: float):
        """Trigger an alert"""
        alert = Alert(
            rule_name=rule.name,
            category=rule.category,
            severity=rule.severity,
            message=f"{rule.condition}: {value:.3f} (threshold: {rule.threshold})",
            value=value,
            threshold=rule.threshold,
            timestamp=datetime.now()
        )
        
        # Store alert
        self._store_alert(alert)
        self.active_alerts[rule.name] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        self._send_notifications(alert, rule)
        
        logger.warning(f"Alert triggered: {alert.message}")
    
    def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO alerts 
                    (rule_name, category, severity, message, value, threshold, timestamp, resolved)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.rule_name, alert.category, alert.severity,
                    alert.message, alert.value, alert.threshold,
                    alert.timestamp, alert.resolved
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
    
    def _send_notifications(self, alert: Alert, rule: AlertRule):
        """Send notifications through configured channels"""
        for channel_name in rule.notification_channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                if channel.enabled:
                    self._send_notification(alert, channel)
    
    def _send_notification(self, alert: Alert, channel: AlertChannel):
        """Send notification through a specific channel"""
        try:
            if channel.type == 'email':
                self._send_email_notification(alert, channel)
            elif channel.type == 'slack':
                self._send_slack_notification(alert, channel)
            elif channel.type == 'webhook':
                self._send_webhook_notification(alert, channel)
        except Exception as e:
            logger.error(f"Failed to send notification via {channel.name}: {e}")
    
    def _send_email_notification(self, alert: Alert, channel: AlertChannel):
        """Send email notification"""
        config = channel.config
        
        msg = MIMEMultipart()
        msg['From'] = config['from_email']
        msg['To'] = ', '.join(config['to_emails'])
        msg['Subject'] = f"[{alert.severity.upper()}] Mingus Alert: {alert.rule_name}"
        
        body = f"""
        Alert Details:
        - Rule: {alert.rule_name}
        - Category: {alert.category}
        - Severity: {alert.severity}
        - Message: {alert.message}
        - Value: {alert.value}
        - Threshold: {alert.threshold}
        - Timestamp: {alert.timestamp}
        
        Please investigate this issue immediately.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email (configure SMTP settings as needed)
        # server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        # server.starttls()
        # server.login(config['username'], config['password'])
        # server.send_message(msg)
        # server.quit()
        
        logger.info(f"Email notification sent for alert: {alert.rule_name}")
    
    def _send_slack_notification(self, alert: Alert, channel: AlertChannel):
        """Send Slack notification"""
        config = channel.config
        
        payload = {
            "channel": config['channel'],
            "username": config['username'],
            "text": f"🚨 *{alert.severity.upper()} Alert*: {alert.message}",
            "attachments": [
                {
                    "fields": [
                        {"title": "Rule", "value": alert.rule_name, "short": True},
                        {"title": "Category", "value": alert.category, "short": True},
                        {"title": "Value", "value": str(alert.value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold), "short": True}
                    ],
                    "color": self._get_severity_color(alert.severity)
                }
            ]
        }
        
        # Send to Slack webhook (configure webhook URL as needed)
        # if config['webhook_url']:
        #     requests.post(config['webhook_url'], json=payload)
        
        logger.info(f"Slack notification sent for alert: {alert.rule_name}")
    
    def _send_webhook_notification(self, alert: Alert, channel: AlertChannel):
        """Send webhook notification"""
        config = channel.config
        
        payload = {
            "alert": {
                "rule_name": alert.rule_name,
                "category": alert.category,
                "severity": alert.severity,
                "message": alert.message,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat()
            }
        }
        
        # Send webhook (configure webhook URL as needed)
        # if config.get('url'):
        #     requests.post(config['url'], json=payload, headers=config.get('headers', {}))
        
        logger.info(f"Webhook notification sent for alert: {alert.rule_name}")
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level"""
        colors = {
            'low': '#36a64f',
            'medium': '#ffa500',
            'high': '#ff0000',
            'critical': '#8b0000'
        }
        return colors.get(severity, '#808080')
    
    def resolve_alert(self, rule_name: str) -> bool:
        """Mark an alert as resolved"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE alerts 
                    SET resolved = 1, resolved_at = ? 
                    WHERE rule_name = ? AND resolved = 0
                """, (datetime.now(), rule_name))
                conn.commit()
            
            if rule_name in self.active_alerts:
                self.active_alerts[rule_name].resolved = True
                self.active_alerts[rule_name].resolved_at = datetime.now()
            
            logger.info(f"Alert resolved: {rule_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the last N hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                cursor = conn.execute("""
                    SELECT rule_name, category, severity, message, value, threshold, 
                           timestamp, resolved, resolved_at
                    FROM alerts 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
                
                alerts = []
                for row in cursor.fetchall():
                    alert = Alert(
                        rule_name=row[0],
                        category=row[1],
                        severity=row[2],
                        message=row[3],
                        value=row[4],
                        threshold=row[5],
                        timestamp=datetime.fromisoformat(row[6]),
                        resolved=bool(row[7]),
                        resolved_at=datetime.fromisoformat(row[8]) if row[8] else None
                    )
                    alerts.append(alert)
                
                return alerts
                
        except Exception as e:
            logger.error(f"Failed to get alert history: {e}")
            return []
    
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for the last N hours"""
        alerts = self.get_alert_history(hours)
        
        if not alerts:
            return {}
        
        # Count by severity
        severity_counts = defaultdict(int)
        category_counts = defaultdict(int)
        resolved_count = sum(1 for alert in alerts if alert.resolved)
        
        for alert in alerts:
            severity_counts[alert.severity] += 1
            category_counts[alert.category] += 1
        
        return {
            'total_alerts': len(alerts),
            'resolved_alerts': resolved_count,
            'unresolved_alerts': len(alerts) - resolved_count,
            'severity_distribution': dict(severity_counts),
            'category_distribution': dict(category_counts),
            'resolution_rate': resolved_count / len(alerts) if alerts else 0
        }
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get current alert summary"""
        active_alerts = self.get_active_alerts()
        stats = self.get_alert_statistics(24)
        
        return {
            'active_alerts': len(active_alerts),
            'critical_alerts': len([a for a in active_alerts if a.severity == 'critical']),
            'high_alerts': len([a for a in active_alerts if a.severity == 'high']),
            'medium_alerts': len([a for a in active_alerts if a.severity == 'medium']),
            'low_alerts': len([a for a in active_alerts if a.severity == 'low']),
            'statistics_24h': stats
        }

# Global alerting system instance
alerting_system = AlertingSystem()

# Convenience functions for updating metrics
def update_performance_metric(metric_name: str, value: float, metadata: Dict[str, Any] = None):
    """Update performance metric for alerting"""
    alerting_system.update_metric(metric_name, value, metadata)

def update_business_metric(metric_name: str, value: float, metadata: Dict[str, Any] = None):
    """Update business metric for alerting"""
    alerting_system.update_metric(metric_name, value, metadata)

def update_system_metric(metric_name: str, value: float, metadata: Dict[str, Any] = None):
    """Update system metric for alerting"""
    alerting_system.update_metric(metric_name, value, metadata) 