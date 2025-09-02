"""
Backup Monitoring and Alerting System
Comprehensive monitoring, alerting, and compliance reporting for backup operations
"""

import os
import sys
import logging
import json
import time
import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import schedule
import threading
import requests
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary
import psutil
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
BACKUP_SUCCESS_COUNTER = Counter('backup_success_total', 'Total successful backups', ['backup_type'])
BACKUP_FAILURE_COUNTER = Counter('backup_failure_total', 'Total failed backups', ['backup_type'])
BACKUP_DURATION_HISTOGRAM = Histogram('backup_duration_seconds', 'Backup duration in seconds', ['backup_type'])
BACKUP_SIZE_GAUGE = Gauge('backup_size_bytes', 'Backup size in bytes', ['backup_type'])
RECOVERY_SUCCESS_COUNTER = Counter('recovery_success_total', 'Total successful recoveries', ['recovery_type'])
RECOVERY_FAILURE_COUNTER = Counter('recovery_failure_total', 'Total failed recoveries', ['recovery_type'])
RECOVERY_DURATION_HISTOGRAM = Histogram('recovery_duration_seconds', 'Recovery duration in seconds', ['recovery_type'])
STORAGE_USAGE_GAUGE = Gauge('storage_usage_bytes', 'Storage usage in bytes', ['storage_type'])
BACKUP_VERIFICATION_COUNTER = Counter('backup_verification_total', 'Total backup verifications', ['status'])

@dataclass
class MonitoringConfig:
    """Configuration for backup monitoring"""
    prometheus_enabled: bool
    prometheus_port: int
    email_alerts_enabled: bool
    email_smtp_server: str
    email_smtp_port: int
    email_username: str
    email_password: str
    email_from: str
    email_to: List[str]
    slack_webhook_url: str
    alert_thresholds: Dict[str, int]
    compliance_reporting: bool
    compliance_retention_days: int
    health_check_interval: int  # seconds
    storage_monitoring: bool
    performance_monitoring: bool

@dataclass
class BackupAlert:
    """Backup alert information"""
    alert_id: str
    timestamp: datetime.datetime
    alert_type: str  # backup_failure, storage_full, verification_failed, etc.
    severity: str  # critical, warning, info
    message: str
    backup_id: Optional[str]
    recovery_id: Optional[str]
    status: str  # active, resolved, acknowledged
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime.datetime]

@dataclass
class ComplianceReport:
    """Compliance report data"""
    report_id: str
    timestamp: datetime.datetime
    report_period: str  # daily, weekly, monthly
    backup_success_rate: float
    recovery_success_rate: float
    verification_success_rate: float
    storage_utilization: float
    rto_achievement: float
    rpo_achievement: float
    encryption_compliance: bool
    retention_compliance: bool
    audit_trail_complete: bool
    compliance_score: float

@dataclass
class SystemHealth:
    """System health metrics"""
    timestamp: datetime.datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    backup_processes: int
    recovery_processes: int
    storage_available: int
    storage_total: int

class BackupMonitoringManager:
    """Comprehensive backup monitoring and alerting system"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.alerts: List[BackupAlert] = []
        self.compliance_reports: List[ComplianceReport] = []
        self.health_metrics: List[SystemHealth] = []
        self._setup_prometheus()
        self._setup_monitoring_directories()
        
    def _setup_prometheus(self):
        """Initialize Prometheus metrics server"""
        if self.config.prometheus_enabled:
            try:
                start_http_server(self.config.prometheus_port)
                logger.info(f"Prometheus metrics server started on port {self.config.prometheus_port}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")
                
    def _setup_monitoring_directories(self):
        """Create monitoring directory structure"""
        monitoring_dir = Path("monitoring")
        monitoring_dir.mkdir(exist_ok=True)
        
        (monitoring_dir / "alerts").mkdir(exist_ok=True)
        (monitoring_dir / "reports").mkdir(exist_ok=True)
        (monitoring_dir / "health").mkdir(exist_ok=True)
        (monitoring_dir / "logs").mkdir(exist_ok=True)
        
    def _generate_alert_id(self) -> str:
        """Generate unique alert identifier"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"alert_{timestamp}_{random_suffix}"
        
    def _generate_report_id(self) -> str:
        """Generate unique report identifier"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = os.urandom(4).hex()
        return f"report_{timestamp}_{random_suffix}"
        
    def record_backup_success(self, backup_type: str, duration: float, size: int):
        """Record successful backup metrics"""
        BACKUP_SUCCESS_COUNTER.labels(backup_type=backup_type).inc()
        BACKUP_DURATION_HISTOGRAM.labels(backup_type=backup_type).observe(duration)
        BACKUP_SIZE_GAUGE.labels(backup_type=backup_type).set(size)
        
        logger.info(f"Backup success recorded: {backup_type}, duration: {duration}s, size: {size} bytes")
        
    def record_backup_failure(self, backup_type: str, error_message: str):
        """Record failed backup metrics"""
        BACKUP_FAILURE_COUNTER.labels(backup_type=backup_type).inc()
        
        # Create alert for backup failure
        self.create_alert(
            alert_type="backup_failure",
            severity="critical",
            message=f"Backup failure for {backup_type}: {error_message}",
            backup_id=None
        )
        
        logger.error(f"Backup failure recorded: {backup_type}, error: {error_message}")
        
    def record_recovery_success(self, recovery_type: str, duration: float):
        """Record successful recovery metrics"""
        RECOVERY_SUCCESS_COUNTER.labels(recovery_type=recovery_type).inc()
        RECOVERY_DURATION_HISTOGRAM.labels(recovery_type=recovery_type).observe(duration)
        
        logger.info(f"Recovery success recorded: {recovery_type}, duration: {duration}s")
        
    def record_recovery_failure(self, recovery_type: str, error_message: str):
        """Record failed recovery metrics"""
        RECOVERY_FAILURE_COUNTER.labels(recovery_type=recovery_type).inc()
        
        # Create alert for recovery failure
        self.create_alert(
            alert_type="recovery_failure",
            severity="critical",
            message=f"Recovery failure for {recovery_type}: {error_message}",
            recovery_id=None
        )
        
        logger.error(f"Recovery failure recorded: {recovery_type}, error: {error_message}")
        
    def record_backup_verification(self, status: str):
        """Record backup verification metrics"""
        BACKUP_VERIFICATION_COUNTER.labels(status=status).inc()
        
        if status == "failed":
            self.create_alert(
                alert_type="verification_failed",
                severity="warning",
                message="Backup verification failed",
                backup_id=None
            )
            
        logger.info(f"Backup verification recorded: {status}")
        
    def create_alert(self, alert_type: str, severity: str, message: str, 
                    backup_id: Optional[str] = None, recovery_id: Optional[str] = None):
        """Create and send backup alert"""
        alert = BackupAlert(
            alert_id=self._generate_alert_id(),
            timestamp=datetime.datetime.now(),
            alert_type=alert_type,
            severity=severity,
            message=message,
            backup_id=backup_id,
            recovery_id=recovery_id,
            status="active",
            acknowledged_by=None,
            acknowledged_at=None
        )
        
        self.alerts.append(alert)
        self._save_alert(alert)
        
        # Send alert notifications
        self._send_email_alert(alert)
        self._send_slack_alert(alert)
        
        logger.info(f"Alert created: {alert.alert_id} - {alert_type}")
        
    def _send_email_alert(self, alert: BackupAlert):
        """Send email alert"""
        if not self.config.email_alerts_enabled:
            return
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = ', '.join(self.config.email_to)
            msg['Subject'] = f"Backup Alert: {alert.alert_type.upper()} - {alert.severity.upper()}"
            
            body = f"""
Backup System Alert

Alert ID: {alert.alert_id}
Timestamp: {alert.timestamp}
Type: {alert.alert_type}
Severity: {alert.severity}
Message: {alert.message}

Backup ID: {alert.backup_id or 'N/A'}
Recovery ID: {alert.recovery_id or 'N/A'}

This is an automated alert from the backup monitoring system.
            """.strip()
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.config.email_smtp_server, self.config.email_smtp_port, context=context) as server:
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(msg)
                
            logger.info(f"Email alert sent: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            
    def _send_slack_alert(self, alert: BackupAlert):
        """Send Slack alert"""
        if not self.config.slack_webhook_url:
            return
            
        try:
            # Prepare Slack message
            color = {
                "critical": "#FF0000",
                "warning": "#FFA500",
                "info": "#0000FF"
            }.get(alert.severity, "#808080")
            
            slack_message = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Backup Alert: {alert.alert_type}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Alert ID",
                                "value": alert.alert_id,
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(
                self.config.slack_webhook_url,
                json=slack_message,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent: {alert.alert_id}")
            else:
                logger.error(f"Slack alert failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            
    def _save_alert(self, alert: BackupAlert):
        """Save alert to file"""
        alert_path = Path("monitoring/alerts") / f"{alert.alert_id}.json"
        
        with open(alert_path, 'w') as f:
            json.dump(asdict(alert), f, default=str, indent=2)
            
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.status = "acknowledged"
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.datetime.now()
                
                # Update saved alert
                self._save_alert(alert)
                
                logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                break
                
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.status = "resolved"
                
                # Update saved alert
                self._save_alert(alert)
                
                logger.info(f"Alert resolved: {alert_id}")
                break
                
    def collect_system_health(self) -> SystemHealth:
        """Collect system health metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv
            }
            
            # Process counts
            backup_processes = len([p for p in psutil.process_iter(['name']) 
                                 if 'backup' in p.info['name'].lower()])
            recovery_processes = len([p for p in psutil.process_iter(['name']) 
                                   if 'recovery' in p.info['name'].lower()])
            
            # Storage metrics
            storage_available = disk.free
            storage_total = disk.total
            
            health = SystemHealth(
                timestamp=datetime.datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                backup_processes=backup_processes,
                recovery_processes=recovery_processes,
                storage_available=storage_available,
                storage_total=storage_total
            )
            
            self.health_metrics.append(health)
            
            # Update Prometheus metrics
            STORAGE_USAGE_GAUGE.labels(storage_type="available").set(storage_available)
            STORAGE_USAGE_GAUGE.labels(storage_type="total").set(storage_total)
            
            # Check thresholds and create alerts
            self._check_health_thresholds(health)
            
            return health
            
        except Exception as e:
            logger.error(f"Failed to collect system health: {e}")
            return None
            
    def _check_health_thresholds(self, health: SystemHealth):
        """Check health metrics against thresholds and create alerts if needed"""
        thresholds = self.config.alert_thresholds
        
        # CPU usage threshold
        if health.cpu_usage > thresholds.get('cpu_usage', 80):
            self.create_alert(
                alert_type="high_cpu_usage",
                severity="warning",
                message=f"High CPU usage: {health.cpu_usage}%"
            )
            
        # Memory usage threshold
        if health.memory_usage > thresholds.get('memory_usage', 85):
            self.create_alert(
                alert_type="high_memory_usage",
                severity="warning",
                message=f"High memory usage: {health.memory_usage}%"
            )
            
        # Disk usage threshold
        if health.disk_usage > thresholds.get('disk_usage', 90):
            self.create_alert(
                alert_type="high_disk_usage",
                severity="critical",
                message=f"High disk usage: {health.disk_usage}%"
            )
            
        # Storage available threshold
        storage_available_gb = health.storage_available / (1024**3)
        if storage_available_gb < thresholds.get('storage_available_gb', 10):
            self.create_alert(
                alert_type="low_storage_available",
                severity="critical",
                message=f"Low storage available: {storage_available_gb:.2f} GB"
            )
            
    def generate_compliance_report(self, report_period: str = "daily") -> ComplianceReport:
        """Generate compliance report for specified period"""
        try:
            # Calculate time range
            end_time = datetime.datetime.now()
            if report_period == "daily":
                start_time = end_time - datetime.timedelta(days=1)
            elif report_period == "weekly":
                start_time = end_time - datetime.timedelta(weeks=1)
            elif report_period == "monthly":
                start_time = end_time - datetime.timedelta(days=30)
            else:
                start_time = end_time - datetime.timedelta(days=1)
                
            # Filter metrics for period
            period_alerts = [a for a in self.alerts if start_time <= a.timestamp <= end_time]
            period_health = [h for h in self.health_metrics if start_time <= h.timestamp <= end_time]
            
            # Calculate metrics
            total_backups = len([a for a in period_alerts if a.alert_type == "backup_success"])
            failed_backups = len([a for a in period_alerts if a.alert_type == "backup_failure"])
            backup_success_rate = (total_backups / (total_backups + failed_backups)) * 100 if (total_backups + failed_backups) > 0 else 100
            
            total_recoveries = len([a for a in period_alerts if a.alert_type == "recovery_success"])
            failed_recoveries = len([a for a in period_alerts if a.alert_type == "recovery_failure"])
            recovery_success_rate = (total_recoveries / (total_recoveries + failed_recoveries)) * 100 if (total_recoveries + failed_recoveries) > 0 else 100
            
            total_verifications = len([a for a in period_alerts if a.alert_type == "verification_success"])
            failed_verifications = len([a for a in period_alerts if a.alert_type == "verification_failed"])
            verification_success_rate = (total_verifications / (total_verifications + failed_verifications)) * 100 if (total_verifications + failed_verifications) > 0 else 100
            
            # Storage utilization
            if period_health:
                avg_storage_utilization = sum(h.disk_usage for h in period_health) / len(period_health)
            else:
                avg_storage_utilization = 0
                
            # RTO and RPO achievement (simplified calculation)
            rto_achievement = 95.0  # Placeholder - should be calculated from actual metrics
            rpo_achievement = 98.0  # Placeholder - should be calculated from actual metrics
            
            # Compliance checks
            encryption_compliance = True  # Placeholder - should check actual encryption status
            retention_compliance = True   # Placeholder - should check actual retention policies
            audit_trail_complete = True   # Placeholder - should check actual audit logs
            
            # Calculate compliance score
            compliance_score = (
                backup_success_rate * 0.3 +
                recovery_success_rate * 0.3 +
                verification_success_rate * 0.2 +
                (100 - avg_storage_utilization) * 0.1 +
                (encryption_compliance and retention_compliance and audit_trail_complete) * 100 * 0.1
            )
            
            report = ComplianceReport(
                report_id=self._generate_report_id(),
                timestamp=datetime.datetime.now(),
                report_period=report_period,
                backup_success_rate=backup_success_rate,
                recovery_success_rate=recovery_success_rate,
                verification_success_rate=verification_success_rate,
                storage_utilization=avg_storage_utilization,
                rto_achievement=rto_achievement,
                rpo_achievement=rpo_achievement,
                encryption_compliance=encryption_compliance,
                retention_compliance=retention_compliance,
                audit_trail_complete=audit_trail_complete,
                compliance_score=compliance_score
            )
            
            self.compliance_reports.append(report)
            self._save_compliance_report(report)
            
            logger.info(f"Compliance report generated: {report.report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return None
            
    def _save_compliance_report(self, report: ComplianceReport):
        """Save compliance report to file"""
        report_path = Path("monitoring/reports") / f"{report.report_id}.json"
        
        with open(report_path, 'w') as f:
            json.dump(asdict(report), f, default=str, indent=2)
            
    def get_active_alerts(self) -> List[BackupAlert]:
        """Get all active alerts"""
        return [a for a in self.alerts if a.status == "active"]
        
    def get_alerts_by_severity(self, severity: str) -> List[BackupAlert]:
        """Get alerts by severity level"""
        return [a for a in self.alerts if a.severity == severity]
        
    def get_alerts_by_type(self, alert_type: str) -> List[BackupAlert]:
        """Get alerts by type"""
        return [a for a in self.alerts if a.alert_type == alert_type]
        
    def get_latest_health_metrics(self, count: int = 10) -> List[SystemHealth]:
        """Get latest health metrics"""
        return sorted(self.health_metrics, key=lambda x: x.timestamp, reverse=True)[:count]
        
    def get_compliance_reports(self, report_period: Optional[str] = None) -> List[ComplianceReport]:
        """Get compliance reports, optionally filtered by period"""
        if report_period:
            return [r for r in self.compliance_reports if r.report_period == report_period]
        return self.compliance_reports
        
    def start_monitoring(self):
        """Start continuous monitoring"""
        logger.info("Starting backup monitoring system")
        
        # Start health monitoring
        def health_monitor():
            while True:
                try:
                    self.collect_system_health()
                    time.sleep(self.config.health_check_interval)
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(60)
                    
        health_thread = threading.Thread(target=health_monitor, daemon=True)
        health_thread.start()
        
        # Schedule compliance reporting
        schedule.every().day.at("06:00").do(self.generate_compliance_report, "daily")
        schedule.every().sunday.at("07:00").do(self.generate_compliance_report, "weekly")
        schedule.every().month.at("01:00").do(self.generate_compliance_report, "monthly")
        
        # Start scheduler
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Backup monitoring system started")
        
    def stop_monitoring(self):
        """Stop monitoring system"""
        logger.info("Stopping backup monitoring system")
        # Cleanup and shutdown logic here


def create_monitoring_config_from_env() -> MonitoringConfig:
    """Create monitoring configuration from environment variables"""
    return MonitoringConfig(
        prometheus_enabled=os.getenv('PROMETHEUS_ENABLED', 'true').lower() == 'true',
        prometheus_port=int(os.getenv('PROMETHEUS_PORT', '9090')),
        email_alerts_enabled=os.getenv('EMAIL_ALERTS_ENABLED', 'false').lower() == 'true',
        email_smtp_server=os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
        email_smtp_port=int(os.getenv('EMAIL_SMTP_PORT', '465')),
        email_username=os.getenv('EMAIL_USERNAME', ''),
        email_password=os.getenv('EMAIL_PASSWORD', ''),
        email_from=os.getenv('EMAIL_FROM', ''),
        email_to=os.getenv('EMAIL_TO', '').split(','),
        slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL', ''),
        alert_thresholds={
            'cpu_usage': int(os.getenv('ALERT_CPU_THRESHOLD', '80')),
            'memory_usage': int(os.getenv('ALERT_MEMORY_THRESHOLD', '85')),
            'disk_usage': int(os.getenv('ALERT_DISK_THRESHOLD', '90')),
            'storage_available_gb': int(os.getenv('ALERT_STORAGE_THRESHOLD', '10'))
        },
        compliance_reporting=os.getenv('COMPLIANCE_REPORTING', 'true').lower() == 'true',
        compliance_retention_days=int(os.getenv('COMPLIANCE_RETENTION_DAYS', '365')),
        health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '300')),  # 5 minutes
        storage_monitoring=os.getenv('STORAGE_MONITORING', 'true').lower() == 'true',
        performance_monitoring=os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
    )


if __name__ == "__main__":
    # Example usage
    config = create_monitoring_config_from_env()
    monitoring_manager = BackupMonitoringManager(config)
    
    # Start monitoring
    monitoring_manager.start_monitoring()
    
    # Example metrics recording
    monitoring_manager.record_backup_success("database", 120.5, 1024000)
    monitoring_manager.record_backup_success("redis", 45.2, 512000)
    
    # Generate compliance report
    report = monitoring_manager.generate_compliance_report("daily")
    print(f"Compliance report generated: {report.compliance_score}%")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Monitoring system stopped")
