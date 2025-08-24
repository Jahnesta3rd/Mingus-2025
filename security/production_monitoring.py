"""
Production Monitoring System
Comprehensive monitoring with security focus for production environments
"""

import os
import sys
import json
import time
import ssl
import socket
import requests
import subprocess
import threading
import schedule
import hashlib
import smtplib
import ssl as ssl_lib
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import psutil
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
import schedule
import asyncio
import aiohttp
from cryptography import x509
from cryptography.hazmat.backends import default_backend

class MonitoringType(Enum):
    """Types of monitoring"""
    SECURITY_EVENT = "security_event"
    PERFORMANCE = "performance"
    UPTIME = "uptime"
    SSL_CERTIFICATE = "ssl_certificate"
    SECURITY_SCAN = "security_scan"

class AlertLevel(Enum):
    """Alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """Alert channels"""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"

@dataclass
class MonitoringEvent:
    """Monitoring event structure"""
    event_id: str
    event_type: MonitoringType
    alert_level: AlertLevel
    timestamp: datetime
    source: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

@dataclass
class AlertConfig:
    """Alert configuration"""
    email_enabled: bool = True
    email_recipients: List[str] = field(default_factory=list)
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    slack_enabled: bool = True
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    sms_enabled: bool = False
    sms_provider: str = "twilio"
    sms_recipients: List[str] = field(default_factory=list)
    
    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)
    
    pagerduty_enabled: bool = False
    pagerduty_api_key: str = ""
    pagerduty_service_id: str = ""

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enabled: bool = True
    check_interval: int = 60  # seconds
    alert_config: AlertConfig = field(default_factory=AlertConfig)
    
    # Security event monitoring
    security_events_enabled: bool = True
    security_event_threshold: int = 10  # events per minute
    
    # Performance monitoring
    performance_enabled: bool = True
    cpu_threshold: float = 80.0  # percentage
    memory_threshold: float = 85.0  # percentage
    disk_threshold: float = 90.0  # percentage
    response_time_threshold: float = 2000.0  # milliseconds
    
    # Uptime monitoring
    uptime_enabled: bool = True
    uptime_endpoints: List[str] = field(default_factory=list)
    uptime_check_interval: int = 30  # seconds
    
    # SSL certificate monitoring
    ssl_enabled: bool = True
    ssl_domains: List[str] = field(default_factory=list)
    ssl_warning_days: int = 30
    ssl_critical_days: int = 7
    
    # Security scan monitoring
    security_scan_enabled: bool = True
    security_scan_schedule: str = "0 2 * * *"  # Daily at 2 AM
    security_scan_tools: List[str] = field(default_factory=list)

class ProductionMonitor:
    """Production monitoring system"""
    
    def __init__(self, config: MonitoringConfig, base_path: str = "/var/lib/mingus/monitoring"):
        self.config = config
        self.base_path = base_path
        self.events = []
        self.monitoring_thread = None
        self.running = False
        self.alert_manager = AlertManager(config.alert_config)
        
        # Initialize monitoring database
        self._init_monitoring_database()
        
        # Load monitoring configuration
        self._load_monitoring_config()
        
        # Initialize monitoring components
        self.security_monitor = SecurityEventMonitor(config, self.alert_manager)
        self.performance_monitor = PerformanceMonitor(config, self.alert_manager)
        self.uptime_monitor = UptimeMonitor(config, self.alert_manager)
        self.ssl_monitor = SSLCertificateMonitor(config, self.alert_manager)
        self.security_scanner = SecurityScanner(config, self.alert_manager)
    
    def _init_monitoring_database(self):
        """Initialize monitoring database"""
        try:
            os.makedirs(self.base_path, exist_ok=True)
            
            db_path = os.path.join(self.base_path, "monitoring.db")
            with sqlite3.connect(db_path) as conn:
                # Events table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS monitoring_events (
                        event_id TEXT PRIMARY KEY,
                        event_type TEXT NOT NULL,
                        alert_level TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        source TEXT NOT NULL,
                        message TEXT NOT NULL,
                        details TEXT,
                        resolved INTEGER DEFAULT 0,
                        resolved_at TEXT,
                        acknowledged INTEGER DEFAULT 0,
                        acknowledged_by TEXT,
                        acknowledged_at TEXT
                    )
                """)
                
                # Performance metrics table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_percent REAL,
                        memory_percent REAL,
                        disk_percent REAL,
                        response_time REAL,
                        active_connections INTEGER
                    )
                """)
                
                # Uptime checks table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS uptime_checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        endpoint TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        status_code INTEGER,
                        response_time REAL,
                        status TEXT NOT NULL
                    )
                """)
                
                # SSL certificate checks table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ssl_checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        domain TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        expiry_date TEXT,
                        days_until_expiry INTEGER,
                        status TEXT NOT NULL
                    )
                """)
                
                # Security scan results table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS security_scan_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scan_type TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        vulnerabilities_found INTEGER,
                        severity_level TEXT,
                        details TEXT,
                        status TEXT NOT NULL
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON monitoring_events(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON monitoring_events(event_type)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_level ON monitoring_events(alert_level)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_uptime_endpoint ON uptime_checks(endpoint)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_ssl_domain ON ssl_checks(domain)")
                
        except Exception as e:
            logger.error(f"Error initializing monitoring database: {e}")
    
    def _load_monitoring_config(self):
        """Load monitoring configuration"""
        config_path = os.path.join(self.base_path, "monitoring_config.yml")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
                # Update configuration with loaded data
                if 'alert_config' in config_data:
                    self.config.alert_config = AlertConfig(**config_data['alert_config'])
                
                if 'uptime_endpoints' in config_data:
                    self.config.uptime_endpoints = config_data['uptime_endpoints']
                
                if 'ssl_domains' in config_data:
                    self.config.ssl_domains = config_data['ssl_domains']
                
                if 'security_scan_tools' in config_data:
                    self.config.security_scan_tools = config_data['security_scan_tools']
    
    def start_monitoring(self):
        """Start monitoring system"""
        if self.running:
            logger.warning("Monitoring system is already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Start individual monitors
        if self.config.security_events_enabled:
            self.security_monitor.start()
        
        if self.config.performance_enabled:
            self.performance_monitor.start()
        
        if self.config.uptime_enabled:
            self.uptime_monitor.start()
        
        if self.config.ssl_enabled:
            self.ssl_monitor.start()
        
        if self.config.security_scan_enabled:
            self.security_scanner.start()
        
        logger.info("Production monitoring system started")
    
    def stop_monitoring(self):
        """Stop monitoring system"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop individual monitors
        self.security_monitor.stop()
        self.performance_monitor.stop()
        self.uptime_monitor.stop()
        self.ssl_monitor.stop()
        self.security_scanner.stop()
        
        logger.info("Production monitoring system stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Run scheduled tasks
                schedule.run_pending()
                
                # Store events in database
                self._store_events()
                
                # Clean up old data
                self._cleanup_old_data()
                
                time.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _store_events(self):
        """Store events in database"""
        try:
            db_path = os.path.join(self.base_path, "monitoring.db")
            with sqlite3.connect(db_path) as conn:
                for event in self.events:
                    conn.execute("""
                        INSERT OR REPLACE INTO monitoring_events 
                        (event_id, event_type, alert_level, timestamp, source, message, details,
                         resolved, resolved_at, acknowledged, acknowledged_by, acknowledged_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        event.event_id,
                        event.event_type.value,
                        event.alert_level.value,
                        event.timestamp.isoformat(),
                        event.source,
                        event.message,
                        json.dumps(event.details),
                        1 if event.resolved else 0,
                        event.resolved_at.isoformat() if event.resolved_at else None,
                        1 if event.acknowledged else 0,
                        event.acknowledged_by,
                        event.acknowledged_at.isoformat() if event.acknowledged_at else None
                    ))
                
                self.events.clear()
                
        except Exception as e:
            logger.error(f"Error storing events: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        try:
            db_path = os.path.join(self.base_path, "monitoring.db")
            with sqlite3.connect(db_path) as conn:
                # Clean up events older than 30 days
                cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
                conn.execute("DELETE FROM monitoring_events WHERE timestamp < ?", (cutoff_date,))
                
                # Clean up performance metrics older than 7 days
                cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
                conn.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_date,))
                
                # Clean up uptime checks older than 7 days
                conn.execute("DELETE FROM uptime_checks WHERE timestamp < ?", (cutoff_date,))
                
                # Clean up SSL checks older than 7 days
                conn.execute("DELETE FROM ssl_checks WHERE timestamp < ?", (cutoff_date,))
                
                # Clean up security scan results older than 30 days
                cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
                conn.execute("DELETE FROM security_scan_results WHERE timestamp < ?", (cutoff_date,))
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get monitoring system status"""
        return {
            "running": self.running,
            "security_events_enabled": self.config.security_events_enabled,
            "performance_enabled": self.config.performance_enabled,
            "uptime_enabled": self.config.uptime_enabled,
            "ssl_enabled": self.config.ssl_enabled,
            "security_scan_enabled": self.config.security_scan_enabled,
            "check_interval": self.config.check_interval,
            "total_events": len(self.events)
        }
    
    def get_recent_events(self, hours: int = 24) -> List[MonitoringEvent]:
        """Get recent monitoring events"""
        try:
            db_path = os.path.join(self.base_path, "monitoring.db")
            with sqlite3.connect(db_path) as conn:
                cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
                
                cursor = conn.execute("""
                    SELECT event_id, event_type, alert_level, timestamp, source, message, details,
                           resolved, resolved_at, acknowledged, acknowledged_by, acknowledged_at
                    FROM monitoring_events 
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
                
                events = []
                for row in cursor.fetchall():
                    event = MonitoringEvent(
                        event_id=row[0],
                        event_type=MonitoringType(row[1]),
                        alert_level=AlertLevel(row[2]),
                        timestamp=datetime.fromisoformat(row[3]),
                        source=row[4],
                        message=row[5],
                        details=json.loads(row[6]) if row[6] else {},
                        resolved=bool(row[7]),
                        resolved_at=datetime.fromisoformat(row[8]) if row[8] else None,
                        acknowledged=bool(row[9]),
                        acknowledged_by=row[10],
                        acknowledged_at=datetime.fromisoformat(row[11]) if row[11] else None
                    )
                    events.append(event)
                
                return events
                
        except Exception as e:
            logger.error(f"Error getting recent events: {e}")
            return []

class SecurityEventMonitor:
    """Security event monitoring"""
    
    def __init__(self, config: MonitoringConfig, alert_manager):
        self.config = config
        self.alert_manager = alert_manager
        self.running = False
        self.event_count = 0
        self.last_reset = datetime.utcnow()
    
    def start(self):
        """Start security event monitoring"""
        self.running = True
        logger.info("Security event monitoring started")
    
    def stop(self):
        """Stop security event monitoring"""
        self.running = False
        logger.info("Security event monitoring stopped")
    
    def record_security_event(self, event_type: str, severity: str, message: str, details: Dict[str, Any] = None):
        """Record a security event"""
        if not self.running:
            return
        
        self.event_count += 1
        
        # Check if we need to reset the counter
        if datetime.utcnow() - self.last_reset > timedelta(minutes=1):
            self.event_count = 1
            self.last_reset = datetime.utcnow()
        
        # Check threshold
        if self.event_count >= self.config.security_event_threshold:
            alert_level = AlertLevel.CRITICAL if self.event_count > self.config.security_event_threshold * 2 else AlertLevel.WARNING
            
            self.alert_manager.send_alert(
                alert_level,
                f"High security event rate: {self.event_count} events per minute",
                {
                    "event_type": event_type,
                    "severity": severity,
                    "message": message,
                    "details": details or {},
                    "event_count": self.event_count
                }
            )
        
        logger.warning(f"Security event: {event_type} - {message}")

class PerformanceMonitor:
    """Performance monitoring with security focus"""
    
    def __init__(self, config: MonitoringConfig, alert_manager):
        self.config = config
        self.alert_manager = alert_manager
        self.running = False
        self.monitoring_thread = None
    
    def start(self):
        """Start performance monitoring"""
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop(self):
        """Stop performance monitoring"""
        self.running = False
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Performance monitoring loop"""
        while self.running:
            try:
                self._check_performance()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(60)
    
    def _check_performance(self):
        """Check system performance"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.config.cpu_threshold:
                self.alert_manager.send_alert(
                    AlertLevel.WARNING,
                    f"High CPU usage: {cpu_percent}%",
                    {"cpu_percent": cpu_percent, "threshold": self.config.cpu_threshold}
                )
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.config.memory_threshold:
                self.alert_manager.send_alert(
                    AlertLevel.WARNING,
                    f"High memory usage: {memory.percent}%",
                    {"memory_percent": memory.percent, "threshold": self.config.memory_threshold}
                )
            
            # Disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > self.config.disk_threshold:
                self.alert_manager.send_alert(
                    AlertLevel.WARNING,
                    f"High disk usage: {disk.percent}%",
                    {"disk_percent": disk.percent, "threshold": self.config.disk_threshold}
                )
            
            # Network connections (security focus)
            connections = psutil.net_connections()
            suspicious_connections = []
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    # Check for suspicious ports
                    if conn.raddr and conn.raddr.port in [22, 23, 3389, 5900]:
                        suspicious_connections.append({
                            "local": f"{conn.laddr.ip}:{conn.laddr.port}",
                            "remote": f"{conn.raddr.ip}:{conn.raddr.port}",
                            "status": conn.status
                        })
            
            if suspicious_connections:
                self.alert_manager.send_alert(
                    AlertLevel.WARNING,
                    f"Suspicious network connections detected: {len(suspicious_connections)}",
                    {"suspicious_connections": suspicious_connections}
                )
            
            # Store metrics
            self._store_performance_metrics(cpu_percent, memory.percent, disk.percent)
            
        except Exception as e:
            logger.error(f"Error checking performance: {e}")
    
    def _store_performance_metrics(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Store performance metrics"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), "..", "monitoring.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_metrics 
                    (timestamp, cpu_percent, memory_percent, disk_percent)
                    VALUES (?, ?, ?, ?)
                """, (
                    datetime.utcnow().isoformat(),
                    cpu_percent,
                    memory_percent,
                    disk_percent
                ))
        except Exception as e:
            logger.error(f"Error storing performance metrics: {e}")

class UptimeMonitor:
    """Uptime monitoring"""
    
    def __init__(self, config: MonitoringConfig, alert_manager):
        self.config = config
        self.alert_manager = alert_manager
        self.running = False
        self.monitoring_thread = None
    
    def start(self):
        """Start uptime monitoring"""
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Uptime monitoring started")
    
    def stop(self):
        """Stop uptime monitoring"""
        self.running = False
        logger.info("Uptime monitoring stopped")
    
    def _monitoring_loop(self):
        """Uptime monitoring loop"""
        while self.running:
            try:
                self._check_uptime()
                time.sleep(self.config.uptime_check_interval)
            except Exception as e:
                logger.error(f"Error in uptime monitoring: {e}")
                time.sleep(60)
    
    def _check_uptime(self):
        """Check uptime for configured endpoints"""
        for endpoint in self.config.uptime_endpoints:
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=10, verify=True)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code >= 400:
                    self.alert_manager.send_alert(
                        AlertLevel.CRITICAL,
                        f"Endpoint {endpoint} returned status {response.status_code}",
                        {
                            "endpoint": endpoint,
                            "status_code": response.status_code,
                            "response_time": response_time
                        }
                    )
                
                # Check response time
                if response_time > self.config.response_time_threshold:
                    self.alert_manager.send_alert(
                        AlertLevel.WARNING,
                        f"Slow response time for {endpoint}: {response_time}ms",
                        {
                            "endpoint": endpoint,
                            "response_time": response_time,
                            "threshold": self.config.response_time_threshold
                        }
                    )
                
                # Store uptime check
                self._store_uptime_check(endpoint, response.status_code, response_time, "success")
                
            except requests.exceptions.RequestException as e:
                self.alert_manager.send_alert(
                    AlertLevel.CRITICAL,
                    f"Endpoint {endpoint} is down: {e}",
                    {"endpoint": endpoint, "error": str(e)}
                )
                self._store_uptime_check(endpoint, None, None, "failed")
            
            except Exception as e:
                logger.error(f"Error checking uptime for {endpoint}: {e}")
    
    def _store_uptime_check(self, endpoint: str, status_code: Optional[int], response_time: Optional[float], status: str):
        """Store uptime check result"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), "..", "monitoring.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT INTO uptime_checks 
                    (endpoint, timestamp, status_code, response_time, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    endpoint,
                    datetime.utcnow().isoformat(),
                    status_code,
                    response_time,
                    status
                ))
        except Exception as e:
            logger.error(f"Error storing uptime check: {e}")

class SSLCertificateMonitor:
    """SSL certificate monitoring"""
    
    def __init__(self, config: MonitoringConfig, alert_manager):
        self.config = config
        self.alert_manager = alert_manager
        self.running = False
        self.monitoring_thread = None
    
    def start(self):
        """Start SSL certificate monitoring"""
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("SSL certificate monitoring started")
    
    def stop(self):
        """Stop SSL certificate monitoring"""
        self.running = False
        logger.info("SSL certificate monitoring stopped")
    
    def _monitoring_loop(self):
        """SSL certificate monitoring loop"""
        while self.running:
            try:
                self._check_ssl_certificates()
                time.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in SSL certificate monitoring: {e}")
                time.sleep(3600)
    
    def _check_ssl_certificates(self):
        """Check SSL certificates for configured domains"""
        for domain in self.config.ssl_domains:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        
                        if not cert:
                            self.alert_manager.send_alert(
                                AlertLevel.CRITICAL,
                                f"No SSL certificate found for {domain}",
                                {"domain": domain}
                            )
                            continue
                        
                        # Parse expiry date
                        not_after = cert['notAfter']
                        expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        days_until_expiry = (expiry_date - datetime.utcnow()).days
                        
                        # Check expiry
                        if days_until_expiry < 0:
                            self.alert_manager.send_alert(
                                AlertLevel.CRITICAL,
                                f"SSL certificate for {domain} has expired",
                                {"domain": domain, "expiry_date": expiry_date.isoformat()}
                            )
                        elif days_until_expiry < self.config.ssl_critical_days:
                            self.alert_manager.send_alert(
                                AlertLevel.CRITICAL,
                                f"SSL certificate for {domain} expires in {days_until_expiry} days",
                                {"domain": domain, "days_until_expiry": days_until_expiry}
                            )
                        elif days_until_expiry < self.config.ssl_warning_days:
                            self.alert_manager.send_alert(
                                AlertLevel.WARNING,
                                f"SSL certificate for {domain} expires in {days_until_expiry} days",
                                {"domain": domain, "days_until_expiry": days_until_expiry}
                            )
                        
                        # Store SSL check
                        self._store_ssl_check(domain, expiry_date, days_until_expiry, "valid")
                
            except Exception as e:
                self.alert_manager.send_alert(
                    AlertLevel.CRITICAL,
                    f"SSL certificate check failed for {domain}: {e}",
                    {"domain": domain, "error": str(e)}
                )
                self._store_ssl_check(domain, None, None, "failed")
    
    def _store_ssl_check(self, domain: str, expiry_date: Optional[datetime], days_until_expiry: Optional[int], status: str):
        """Store SSL certificate check result"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), "..", "monitoring.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT INTO ssl_checks 
                    (domain, timestamp, expiry_date, days_until_expiry, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    domain,
                    datetime.utcnow().isoformat(),
                    expiry_date.isoformat() if expiry_date else None,
                    days_until_expiry,
                    status
                ))
        except Exception as e:
            logger.error(f"Error storing SSL check: {e}")

class SecurityScanner:
    """Security scan scheduling and monitoring"""
    
    def __init__(self, config: MonitoringConfig, alert_manager):
        self.config = config
        self.alert_manager = alert_manager
        self.running = False
    
    def start(self):
        """Start security scanner"""
        self.running = True
        
        # Schedule security scans
        schedule.every().day.at("02:00").do(self._run_security_scan)
        
        logger.info("Security scanner started")
    
    def stop(self):
        """Stop security scanner"""
        self.running = False
        logger.info("Security scanner stopped")
    
    def _run_security_scan(self):
        """Run security scan"""
        if not self.running:
            return
        
        logger.info("Starting scheduled security scan")
        
        try:
            # Run different security scan tools
            for tool in self.config.security_scan_tools:
                self._run_scan_tool(tool)
            
            logger.info("Security scan completed")
            
        except Exception as e:
            logger.error(f"Error running security scan: {e}")
            self.alert_manager.send_alert(
                AlertLevel.WARNING,
                f"Security scan failed: {e}",
                {"error": str(e)}
            )
    
    def _run_scan_tool(self, tool: str):
        """Run specific security scan tool"""
        try:
            if tool == "nmap":
                self._run_nmap_scan()
            elif tool == "nuclei":
                self._run_nuclei_scan()
            elif tool == "zap":
                self._run_zap_scan()
            else:
                logger.warning(f"Unknown security scan tool: {tool}")
                
        except Exception as e:
            logger.error(f"Error running {tool} scan: {e}")
    
    def _run_nmap_scan(self):
        """Run Nmap security scan"""
        try:
            # Run Nmap scan for common vulnerabilities
            result = subprocess.run([
                "nmap", "-sV", "--script=vuln", "localhost"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Parse results for vulnerabilities
                vulnerabilities = self._parse_nmap_results(result.stdout)
                
                if vulnerabilities:
                    self.alert_manager.send_alert(
                        AlertLevel.WARNING,
                        f"Nmap scan found {len(vulnerabilities)} potential vulnerabilities",
                        {"vulnerabilities": vulnerabilities}
                    )
                
                # Store scan results
                self._store_scan_result("nmap", len(vulnerabilities), "completed")
            else:
                logger.error(f"Nmap scan failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error running Nmap scan: {e}")
    
    def _run_nuclei_scan(self):
        """Run Nuclei security scan"""
        try:
            # Run Nuclei scan for web vulnerabilities
            result = subprocess.run([
                "nuclei", "-u", "https://localhost", "-silent"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Parse results for vulnerabilities
                vulnerabilities = self._parse_nuclei_results(result.stdout)
                
                if vulnerabilities:
                    self.alert_manager.send_alert(
                        AlertLevel.WARNING,
                        f"Nuclei scan found {len(vulnerabilities)} web vulnerabilities",
                        {"vulnerabilities": vulnerabilities}
                    )
                
                # Store scan results
                self._store_scan_result("nuclei", len(vulnerabilities), "completed")
            else:
                logger.error(f"Nuclei scan failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error running Nuclei scan: {e}")
    
    def _run_zap_scan(self):
        """Run OWASP ZAP security scan"""
        try:
            # Run ZAP baseline scan
            result = subprocess.run([
                "zap-baseline.py", "-t", "https://localhost"
            ], capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                # Parse results for vulnerabilities
                vulnerabilities = self._parse_zap_results(result.stdout)
                
                if vulnerabilities:
                    self.alert_manager.send_alert(
                        AlertLevel.WARNING,
                        f"ZAP scan found {len(vulnerabilities)} web vulnerabilities",
                        {"vulnerabilities": vulnerabilities}
                    )
                
                # Store scan results
                self._store_scan_result("zap", len(vulnerabilities), "completed")
            else:
                logger.error(f"ZAP scan failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error running ZAP scan: {e}")
    
    def _parse_nmap_results(self, output: str) -> List[Dict[str, Any]]:
        """Parse Nmap scan results"""
        vulnerabilities = []
        lines = output.split('\n')
        
        for line in lines:
            if 'VULNERABLE' in line or 'CVE' in line:
                vulnerabilities.append({
                    "type": "nmap",
                    "description": line.strip(),
                    "severity": "medium"
                })
        
        return vulnerabilities
    
    def _parse_nuclei_results(self, output: str) -> List[Dict[str, Any]]:
        """Parse Nuclei scan results"""
        vulnerabilities = []
        lines = output.split('\n')
        
        for line in lines:
            if line.strip():
                vulnerabilities.append({
                    "type": "nuclei",
                    "description": line.strip(),
                    "severity": "medium"
                })
        
        return vulnerabilities
    
    def _parse_zap_results(self, output: str) -> List[Dict[str, Any]]:
        """Parse ZAP scan results"""
        vulnerabilities = []
        lines = output.split('\n')
        
        for line in lines:
            if 'FAIL' in line or 'WARN' in line:
                vulnerabilities.append({
                    "type": "zap",
                    "description": line.strip(),
                    "severity": "medium"
                })
        
        return vulnerabilities
    
    def _store_scan_result(self, scan_type: str, vulnerabilities_found: int, status: str):
        """Store security scan result"""
        try:
            db_path = os.path.join(os.path.dirname(__file__), "..", "monitoring.db")
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    INSERT INTO security_scan_results 
                    (scan_type, timestamp, vulnerabilities_found, status)
                    VALUES (?, ?, ?, ?)
                """, (
                    scan_type,
                    datetime.utcnow().isoformat(),
                    vulnerabilities_found,
                    status
                ))
        except Exception as e:
            logger.error(f"Error storing scan result: {e}")

class AlertManager:
    """Alert management system"""
    
    def __init__(self, alert_config: AlertConfig):
        self.config = alert_config
    
    def send_alert(self, level: AlertLevel, message: str, details: Dict[str, Any] = None):
        """Send alert through configured channels"""
        try:
            if self.config.email_enabled:
                self._send_email_alert(level, message, details)
            
            if self.config.slack_enabled:
                self._send_slack_alert(level, message, details)
            
            if self.config.sms_enabled:
                self._send_sms_alert(level, message, details)
            
            if self.config.webhook_enabled:
                self._send_webhook_alert(level, message, details)
            
            if self.config.pagerduty_enabled:
                self._send_pagerduty_alert(level, message, details)
            
            logger.info(f"Alert sent: {level.value} - {message}")
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _send_email_alert(self, level: AlertLevel, message: str, details: Dict[str, Any] = None):
        """Send email alert"""
        try:
            if not self.config.email_recipients:
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username
            msg['To'] = ', '.join(self.config.email_recipients)
            msg['Subject'] = f"[{level.value.upper()}] MINGUS Security Alert"
            
            body = f"""
            Security Alert: {message}
            
            Level: {level.value}
            Time: {datetime.utcnow().isoformat()}
            
            Details:
            {json.dumps(details, indent=2) if details else 'No additional details'}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _send_slack_alert(self, level: AlertLevel, message: str, details: Dict[str, Any] = None):
        """Send Slack alert"""
        try:
            if not self.config.slack_webhook_url:
                return
            
            payload = {
                "channel": self.config.slack_channel,
                "text": f"[{level.value.upper()}] {message}",
                "attachments": [
                    {
                        "fields": [
                            {
                                "title": "Level",
                                "value": level.value,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": datetime.utcnow().isoformat(),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            if details:
                payload["attachments"][0]["fields"].append({
                    "title": "Details",
                    "value": json.dumps(details, indent=2),
                    "short": False
                })
            
            response = requests.post(self.config.slack_webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _send_sms_alert(self, level: AlertLevel, message: str, details: Dict[str, Any] = None):
        """Send SMS alert"""
        try:
            if not self.config.sms_recipients:
                return
            
            # Implementation depends on SMS provider
            # This is a placeholder for Twilio or similar service
            logger.info(f"SMS alert would be sent: {level.value} - {message}")
            
        except Exception as e:
            logger.error(f"Error sending SMS alert: {e}")
    
    def _send_webhook_alert(self, level: AlertLevel, message: str, details: Dict[str, Any] = None):
        """Send webhook alert"""
        try:
            if not self.config.webhook_url:
                return
            
            payload = {
                "level": level.value,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "details": details or {}
            }
            
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                headers=self.config.webhook_headers,
                timeout=10
            )
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    def _send_pagerduty_alert(self, level: AlertLevel, message: str, details: Dict[str, Any] = None):
        """Send PagerDuty alert"""
        try:
            if not self.config.pagerduty_api_key or not self.config.pagerduty_service_id:
                return
            
            # Implementation for PagerDuty API
            # This is a placeholder for PagerDuty integration
            logger.info(f"PagerDuty alert would be sent: {level.value} - {message}")
            
        except Exception as e:
            logger.error(f"Error sending PagerDuty alert: {e}")

# Global monitoring instance
_production_monitor = None

def get_production_monitor(config: MonitoringConfig = None, base_path: str = "/var/lib/mingus/monitoring") -> ProductionMonitor:
    """Get global production monitor instance"""
    global _production_monitor
    
    if _production_monitor is None:
        if config is None:
            config = MonitoringConfig()
        _production_monitor = ProductionMonitor(config, base_path)
    
    return _production_monitor

def start_production_monitoring(config: MonitoringConfig = None, base_path: str = "/var/lib/mingus/monitoring"):
    """Start production monitoring"""
    monitor = get_production_monitor(config, base_path)
    monitor.start_monitoring()

def stop_production_monitoring():
    """Stop production monitoring"""
    global _production_monitor
    if _production_monitor:
        _production_monitor.stop_monitoring()
        _production_monitor = None 