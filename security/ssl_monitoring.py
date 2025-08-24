#!/usr/bin/env python3
"""
MINGUS SSL Monitoring and Health Check System
Comprehensive SSL/TLS monitoring for financial wellness application
"""

import os
import ssl
import socket
import hashlib
import json
import logging
import requests
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

@dataclass
class SSLHealthCheck:
    """SSL health check configuration"""
    domain: str
    port: int = 443
    timeout: int = 10
    check_interval: int = 300  # 5 minutes
    alert_threshold: int = 30  # days until expiry
    enabled: bool = True

@dataclass
class SSLMonitoringConfig:
    """SSL monitoring configuration"""
    enabled: bool = True
    check_interval: int = 300  # 5 minutes
    alert_enabled: bool = True
    email_alerts: bool = True
    webhook_alerts: bool = False
    slack_alerts: bool = False
    
    # Email configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    
    # Webhook configuration
    webhook_url: Optional[str] = None
    
    # Slack configuration
    slack_webhook_url: Optional[str] = None
    
    # Health checks
    health_checks: List[SSLHealthCheck] = field(default_factory=list)

class SSLMonitor:
    """Comprehensive SSL monitoring system"""
    
    def __init__(self, config: SSLMonitoringConfig):
        self.config = config
        self.health_status = {}
        self.alert_history = []
        self.monitoring_thread = None
        self.running = False
        
        logger.info("SSL monitoring system initialized")
    
    def start_monitoring(self):
        """Start SSL monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("SSL monitoring is already running")
            return
        
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("SSL monitoring started")
    
    def stop_monitoring(self):
        """Stop SSL monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("SSL monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._run_health_checks()
                time.sleep(self.config.check_interval)
            except Exception as e:
                logger.error(f"SSL monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _run_health_checks(self):
        """Run all SSL health checks"""
        for health_check in self.config.health_checks:
            if not health_check.enabled:
                continue
            
            try:
                result = self._check_ssl_health(health_check)
                self.health_status[health_check.domain] = result
                
                # Check for alerts
                if result['alert_required']:
                    self._send_alert(health_check, result)
                
                logger.debug(f"SSL health check for {health_check.domain}: {result['status']}")
                
            except Exception as e:
                logger.error(f"SSL health check error for {health_check.domain}: {e}")
                self.health_status[health_check.domain] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
    
    def _check_ssl_health(self, health_check: SSLHealthCheck) -> Dict[str, Any]:
        """Check SSL health for a specific domain"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            # Connect to server
            with socket.create_connection((health_check.domain, health_check.port), 
                                        timeout=health_check.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=health_check.domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse certificate dates
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    
                    # Calculate days until expiration
                    days_until_expiry = (not_after - datetime.utcnow()).days
                    
                    # Check certificate validity
                    is_valid = days_until_expiry > 0
                    expires_soon = days_until_expiry <= health_check.alert_threshold
                    
                    # Get cipher information
                    cipher = ssock.cipher()
                    cipher_suite = cipher[0] if cipher else None
                    cipher_version = cipher[1] if cipher else None
                    
                    # Check TLS version
                    tls_version = ssock.version()
                    
                    # Determine status
                    if not is_valid:
                        status = 'expired'
                    elif expires_soon:
                        status = 'expires_soon'
                    else:
                        status = 'healthy'
                    
                    # Check if alert is required
                    alert_required = not is_valid or expires_soon
                    
                    return {
                        'domain': health_check.domain,
                        'port': health_check.port,
                        'status': status,
                        'timestamp': datetime.utcnow().isoformat(),
                        'certificate': {
                            'subject': dict(x[0] for x in cert['subject']),
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'not_before': not_before.isoformat(),
                            'not_after': not_after.isoformat(),
                            'days_until_expiry': days_until_expiry,
                            'serial_number': cert.get('serialNumber'),
                            'version': cert.get('version'),
                            'san': cert.get('subjectAltName', [])
                        },
                        'ssl_info': {
                            'tls_version': tls_version,
                            'cipher_suite': cipher_suite,
                            'cipher_version': cipher_version,
                            'key_size': cipher[2] if cipher else None
                        },
                        'is_valid': is_valid,
                        'expires_soon': expires_soon,
                        'alert_required': alert_required,
                        'alert_threshold': health_check.alert_threshold
                    }
                    
        except ssl.SSLError as e:
            return {
                'domain': health_check.domain,
                'port': health_check.port,
                'status': 'ssl_error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': f"SSL error: {e}",
                'is_valid': False,
                'alert_required': True
            }
        except socket.timeout:
            return {
                'domain': health_check.domain,
                'port': health_check.port,
                'status': 'timeout',
                'timestamp': datetime.utcnow().isoformat(),
                'error': 'Connection timeout',
                'is_valid': False,
                'alert_required': True
            }
        except Exception as e:
            return {
                'domain': health_check.domain,
                'port': health_check.port,
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'is_valid': False,
                'alert_required': True
            }
    
    def _send_alert(self, health_check: SSLHealthCheck, result: Dict[str, Any]):
        """Send SSL alert"""
        alert_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'domain': health_check.domain,
            'status': result['status'],
            'details': result
        }
        
        # Store alert in history
        self.alert_history.append(alert_data)
        
        # Keep only last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
        
        # Send alerts via configured channels
        if self.config.email_alerts:
            self._send_email_alert(alert_data)
        
        if self.config.webhook_alerts:
            self._send_webhook_alert(alert_data)
        
        if self.config.slack_alerts:
            self._send_slack_alert(alert_data)
        
        logger.warning(f"SSL alert sent for {health_check.domain}: {result['status']}")
    
    def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert"""
        try:
            if not all([self.config.smtp_username, self.config.smtp_password, 
                       self.config.from_email, self.config.to_email]):
                logger.warning("Email alert configuration incomplete")
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.config.from_email
            msg['To'] = self.config.to_email
            msg['Subject'] = f"SSL Alert: {alert_data['domain']} - {alert_data['status']}"
            
            body = f"""
            SSL Certificate Alert
            
            Domain: {alert_data['domain']}
            Status: {alert_data['status']}
            Time: {alert_data['timestamp']}
            
            Details:
            {json.dumps(alert_data['details'], indent=2)}
            
            This is an automated alert from the MINGUS SSL monitoring system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent for {alert_data['domain']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """Send webhook alert"""
        try:
            if not self.config.webhook_url:
                return
            
            response = requests.post(
                self.config.webhook_url,
                json=alert_data,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent for {alert_data['domain']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Send Slack alert"""
        try:
            if not self.config.slack_webhook_url:
                return
            
            # Determine color based on status
            color = '#ff0000' if alert_data['status'] in ['expired', 'ssl_error'] else '#ffa500'
            
            payload = {
                'attachments': [{
                    'color': color,
                    'title': f"SSL Alert: {alert_data['domain']}",
                    'text': f"Status: {alert_data['status']}",
                    'fields': [
                        {
                            'title': 'Domain',
                            'value': alert_data['domain'],
                            'short': True
                        },
                        {
                            'title': 'Status',
                            'value': alert_data['status'],
                            'short': True
                        },
                        {
                            'title': 'Time',
                            'value': alert_data['timestamp'],
                            'short': True
                        }
                    ],
                    'footer': 'MINGUS SSL Monitor'
                }]
            }
            
            response = requests.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Slack alert sent for {alert_data['domain']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def get_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive SSL health report"""
        total_checks = len(self.config.health_checks)
        enabled_checks = sum(1 for check in self.config.health_checks if check.enabled)
        
        status_counts = {}
        for result in self.health_status.values():
            status = result.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        healthy_count = status_counts.get('healthy', 0)
        alert_count = sum(1 for result in self.health_status.values() 
                         if result.get('alert_required', False))
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_checks': total_checks,
                'enabled_checks': enabled_checks,
                'healthy_count': healthy_count,
                'alert_count': alert_count,
                'health_percentage': (healthy_count / enabled_checks * 100) if enabled_checks > 0 else 0
            },
            'status_breakdown': status_counts,
            'health_status': self.health_status,
            'recent_alerts': self.alert_history[-10:] if self.alert_history else [],
            'monitoring_active': self.running
        }
    
    def add_health_check(self, domain: str, port: int = 443, 
                        alert_threshold: int = 30, enabled: bool = True):
        """Add a new SSL health check"""
        health_check = SSLHealthCheck(
            domain=domain,
            port=port,
            alert_threshold=alert_threshold,
            enabled=enabled
        )
        self.config.health_checks.append(health_check)
        logger.info(f"Added SSL health check for {domain}:{port}")
    
    def remove_health_check(self, domain: str, port: int = 443):
        """Remove an SSL health check"""
        self.config.health_checks = [
            check for check in self.config.health_checks
            if not (check.domain == domain and check.port == port)
        ]
        logger.info(f"Removed SSL health check for {domain}:{port}")
    
    def test_ssl_connection(self, domain: str, port: int = 443) -> Dict[str, Any]:
        """Test SSL connection for a specific domain"""
        health_check = SSLHealthCheck(domain=domain, port=port)
        return self._check_ssl_health(health_check)

def create_ssl_monitoring_config(
    domains: List[str],
    email_config: Optional[Dict[str, str]] = None,
    webhook_url: Optional[str] = None,
    slack_webhook_url: Optional[str] = None
) -> SSLMonitoringConfig:
    """Create SSL monitoring configuration"""
    config = SSLMonitoringConfig(
        enabled=True,
        check_interval=300,  # 5 minutes
        alert_enabled=True,
        email_alerts=bool(email_config),
        webhook_alerts=bool(webhook_url),
        slack_alerts=bool(slack_webhook_url)
    )
    
    # Set email configuration
    if email_config:
        config.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
        config.smtp_port = int(email_config.get('smtp_port', '587'))
        config.smtp_username = email_config.get('username')
        config.smtp_password = email_config.get('password')
        config.from_email = email_config.get('from_email')
        config.to_email = email_config.get('to_email')
    
    # Set webhook configuration
    if webhook_url:
        config.webhook_url = webhook_url
    
    # Set Slack configuration
    if slack_webhook_url:
        config.slack_webhook_url = slack_webhook_url
    
    # Add health checks for domains
    for domain in domains:
        config.health_checks.append(SSLHealthCheck(
            domain=domain,
            port=443,
            alert_threshold=30,
            enabled=True
        ))
    
    return config

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SSL Monitoring System')
    parser.add_argument('--domains', nargs='+', required=True, help='Domains to monitor')
    parser.add_argument('--check-interval', type=int, default=300, help='Check interval in seconds')
    parser.add_argument('--alert-threshold', type=int, default=30, help='Days until expiry to alert')
    parser.add_argument('--email', help='Email for alerts')
    parser.add_argument('--webhook', help='Webhook URL for alerts')
    parser.add_argument('--slack', help='Slack webhook URL for alerts')
    parser.add_argument('--test', help='Test SSL connection for specific domain')
    parser.add_argument('--report', action='store_true', help='Generate health report')
    
    args = parser.parse_args()
    
    if args.test:
        # Test SSL connection
        monitor = SSLMonitor(SSLMonitoringConfig())
        result = monitor.test_ssl_connection(args.test)
        print(json.dumps(result, indent=2))
        return
    
    # Create monitoring configuration
    email_config = None
    if args.email:
        email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': os.getenv('SMTP_PORT', '587'),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL'),
            'to_email': args.email
        }
    
    config = create_ssl_monitoring_config(
        domains=args.domains,
        email_config=email_config,
        webhook_url=args.webhook,
        slack_webhook_url=args.slack
    )
    
    # Create and start monitor
    monitor = SSLMonitor(config)
    
    if args.report:
        # Generate report
        report = monitor.get_health_report()
        print(json.dumps(report, indent=2))
    else:
        # Start monitoring
        monitor.start_monitoring()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("SSL monitoring stopped")

if __name__ == "__main__":
    main() 