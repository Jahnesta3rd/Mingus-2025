"""
Alerting Service for Health Check Monitoring
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
import os

class AlertingService:
    """Service for sending alerts when health checks fail or thresholds are exceeded"""
    
    def __init__(self):
        self.alerting_enabled = os.getenv('ALERTING_ENABLED', 'false').lower() == 'true'
        self.webhook_url = os.getenv('ALERT_WEBHOOK_URL', '')
        self.slack_webhook = os.getenv('ALERT_SLACK_WEBHOOK', '')
        self.failure_threshold = int(os.getenv('HEALTH_CHECK_FAILURE_THRESHOLD', '3'))
        self.response_time_threshold = int(os.getenv('RESPONSE_TIME_THRESHOLD_MS', '5000'))
        
        # Track failures for threshold-based alerting
        self.failure_counts = {}
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between alerts for the same issue
        
    def should_alert(self, component: str, error_type: str) -> bool:
        """Determine if an alert should be sent based on thresholds and cooldown"""
        if not self.alerting_enabled:
            return False
            
        key = f"{component}:{error_type}"
        current_time = time.time()
        
        # Check cooldown
        if key in self.last_alert_time:
            if current_time - self.last_alert_time[key] < self.alert_cooldown:
                return False
        
        # Check failure threshold
        if key not in self.failure_counts:
            self.failure_counts[key] = 0
        
        self.failure_counts[key] += 1
        
        if self.failure_counts[key] >= self.failure_threshold:
            self.last_alert_time[key] = current_time
            return True
            
        return False
    
    def reset_failure_count(self, component: str, error_type: str):
        """Reset failure count when component recovers"""
        key = f"{component}:{error_type}"
        if key in self.failure_counts:
            self.failure_counts[key] = 0
    
    def send_alert(self, title: str, message: str, severity: str = "warning", 
                   component: str = "unknown", error_type: str = "unknown") -> bool:
        """Send an alert via configured channels"""
        if not self.alerting_enabled:
            return False
            
        alert_data = {
            "title": title,
            "message": message,
            "severity": severity,
            "component": component,
            "error_type": error_type,
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.getenv('FLASK_ENV', 'development')
        }
        
        success = True
        
        # Send to webhook if configured
        if self.webhook_url:
            try:
                response = requests.post(
                    self.webhook_url,
                    json=alert_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                if response.status_code not in [200, 201, 202]:
                    logger.error(f"Failed to send webhook alert: {response.status_code}")
                    success = False
            except Exception as e:
                logger.error(f"Error sending webhook alert: {e}")
                success = False
        
        # Send to Slack if configured
        if self.slack_webhook:
            try:
                slack_message = self._format_slack_message(alert_data)
                response = requests.post(
                    self.slack_webhook,
                    json=slack_message,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                if response.status_code != 200:
                    logger.error(f"Failed to send Slack alert: {response.status_code}")
                    success = False
            except Exception as e:
                logger.error(f"Error sending Slack alert: {e}")
                success = False
        
        if success:
            logger.info(f"Alert sent successfully: {title}")
        
        return success
    
    def _format_slack_message(self, alert_data: Dict) -> Dict:
        """Format alert data for Slack webhook"""
        color_map = {
            "critical": "#ff0000",
            "error": "#ff6b6b", 
            "warning": "#ffa500",
            "info": "#4CAF50"
        }
        
        color = color_map.get(alert_data['severity'], "#808080")
        
        return {
            "attachments": [{
                "color": color,
                "title": alert_data['title'],
                "text": alert_data['message'],
                "fields": [
                    {
                        "title": "Component",
                        "value": alert_data['component'],
                        "short": True
                    },
                    {
                        "title": "Error Type", 
                        "value": alert_data['error_type'],
                        "short": True
                    },
                    {
                        "title": "Environment",
                        "value": alert_data['environment'],
                        "short": True
                    },
                    {
                        "title": "Timestamp",
                        "value": alert_data['timestamp'],
                        "short": True
                    }
                ],
                "footer": "Mingus Health Check Monitor"
            }]
        }
    
    def alert_health_check_failure(self, endpoint: str, component: str, error_type: str, 
                                  response_time_ms: Optional[float] = None) -> bool:
        """Send alert for health check failure"""
        if not self.should_alert(component, error_type):
            return False
            
        title = f"Health Check Failure: {component}"
        message = f"Health check for {component} failed on endpoint {endpoint}. Error type: {error_type}"
        
        if response_time_ms:
            message += f" Response time: {response_time_ms}ms"
            
        if response_time_ms and response_time_ms > self.response_time_threshold:
            message += f" (exceeds threshold of {self.response_time_threshold}ms)"
        
        severity = "critical" if component in ["database", "redis"] else "warning"
        
        return self.send_alert(title, message, severity, component, error_type)
    
    def alert_threshold_exceeded(self, metric: str, value: float, threshold: float, 
                                component: str = "system") -> bool:
        """Send alert for threshold exceeded"""
        title = f"Threshold Exceeded: {metric}"
        message = f"{metric} value {value} exceeds threshold {threshold} for {component}"
        
        severity = "warning"
        if metric in ["memory_usage", "disk_usage"] and value > 95:
            severity = "critical"
        elif metric in ["cpu_usage"] and value > 90:
            severity = "critical"
        
        return self.send_alert(title, message, severity, component, "threshold_exceeded")
    
    def alert_service_recovery(self, component: str, error_type: str) -> bool:
        """Send alert when service recovers"""
        title = f"Service Recovery: {component}"
        message = f"{component} has recovered from {error_type} error"
        
        # Reset failure count
        self.reset_failure_count(component, error_type)
        
        return self.send_alert(title, message, "info", component, "recovery")

# Global alerting service instance
alerting_service = AlertingService() 