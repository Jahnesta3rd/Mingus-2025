"""
Rate Limiting Monitoring and Alerting System
Comprehensive monitoring for rate limiting with cultural sensitivity
"""

import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import redis
from flask import current_app, g

logger = logging.getLogger(__name__)

@dataclass
class RateLimitEvent:
    """Rate limit event data"""
    timestamp: float
    identifier: str
    endpoint_type: str
    requests_made: int
    limit: int
    limited: bool
    ip_address: str
    user_id: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    path: Optional[str]
    cultural_context: Dict[str, Any]

@dataclass
class RateLimitAlert:
    """Rate limit alert data"""
    alert_id: str
    timestamp: float
    alert_type: str  # threshold, violation, suspicious
    severity: str    # low, medium, high, critical
    message: str
    data: Dict[str, Any]
    endpoint_type: str
    identifier: str
    cultural_context: Dict[str, Any]

class RateLimitMonitor:
    """Monitor rate limiting activity and generate alerts"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.alerts: deque = deque(maxlen=1000)   # Keep last 1k alerts
        self.metrics: Dict[str, Any] = defaultdict(int)
        self.last_alert_time: Dict[str, float] = {}
        self.alert_cooldown = 300  # 5 minutes between alerts
        
        # Thresholds for alerts
        self.thresholds = {
            'warning': 0.7,      # 70% of limit
            'alert': 0.8,        # 80% of limit
            'critical': 0.95     # 95% of limit
        }
        
        # Suspicious activity patterns
        self.suspicious_patterns = {
            'rapid_requests': {'threshold': 10, 'window': 60},  # 10 requests in 1 minute
            'multiple_endpoints': {'threshold': 5, 'window': 300},  # 5 different endpoints in 5 minutes
            'failed_auth': {'threshold': 3, 'window': 300},  # 3 failed auth attempts in 5 minutes
        }
    
    def record_event(self, event: RateLimitEvent) -> None:
        """Record a rate limit event"""
        try:
            # Store event in memory
            self.events.append(event)
            
            # Store event in Redis if available
            if self.redis_client:
                self._store_event_redis(event)
            
            # Update metrics
            self._update_metrics(event)
            
            # Check for alerts
            self._check_alerts(event)
            
            # Check for suspicious activity
            self._check_suspicious_activity(event)
            
        except Exception as e:
            logger.error(f"Error recording rate limit event: {e}")
    
    def _store_event_redis(self, event: RateLimitEvent) -> None:
        """Store event in Redis for persistence"""
        try:
            event_key = f"rate_limit_event:{event.timestamp}:{event.identifier}"
            event_data = asdict(event)
            event_data['timestamp'] = event.timestamp
            
            # Store event with expiration (24 hours)
            self.redis_client.setex(
                event_key, 
                86400, 
                json.dumps(event_data)
            )
            
            # Add to sorted set for time-based queries
            self.redis_client.zadd(
                'rate_limit_events',
                {event_key: event.timestamp}
            )
            
            # Clean up old events (older than 24 hours)
            cutoff_time = time.time() - 86400
            old_events = self.redis_client.zrangebyscore(
                'rate_limit_events', 0, cutoff_time
            )
            if old_events:
                self.redis_client.zrem('rate_limit_events', *old_events)
                for old_event in old_events:
                    self.redis_client.delete(old_event)
                    
        except Exception as e:
            logger.error(f"Error storing event in Redis: {e}")
    
    def _update_metrics(self, event: RateLimitEvent) -> None:
        """Update monitoring metrics"""
        try:
            # Increment counters
            self.metrics['total_requests'] += 1
            self.metrics[f'endpoint_{event.endpoint_type}_requests'] += 1
            
            if event.limited:
                self.metrics['total_rate_limited'] += 1
                self.metrics[f'endpoint_{event.endpoint_type}_limited'] += 1
            
            # Update hourly counters
            hour_key = f"hour_{int(event.timestamp // 3600)}"
            self.metrics[f'{hour_key}_requests'] += 1
            if event.limited:
                self.metrics[f'{hour_key}_limited'] += 1
            
            # Update identifier counters
            self.metrics[f'identifier_{event.identifier}_requests'] += 1
            if event.limited:
                self.metrics[f'identifier_{event.identifier}_limited'] += 1
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def _check_alerts(self, event: RateLimitEvent) -> None:
        """Check if event should trigger alerts"""
        try:
            # Calculate usage percentage
            usage_percentage = event.requests_made / event.limit
            
            # Check thresholds
            for threshold_name, threshold_value in self.thresholds.items():
                if usage_percentage >= threshold_value:
                    self._trigger_threshold_alert(event, threshold_name, usage_percentage)
            
            # Check if rate limit was exceeded
            if event.limited:
                self._trigger_violation_alert(event)
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _trigger_threshold_alert(self, event: RateLimitEvent, threshold_name: str, usage_percentage: float) -> None:
        """Trigger a threshold-based alert"""
        try:
            alert_key = f"{event.identifier}:{event.endpoint_type}:{threshold_name}"
            current_time = time.time()
            
            # Check cooldown
            if alert_key in self.last_alert_time:
                if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                    return
            
            # Create alert
            alert = RateLimitAlert(
                alert_id=f"{alert_key}_{int(current_time)}",
                timestamp=current_time,
                alert_type="threshold",
                severity=self._get_threshold_severity(threshold_name),
                message=f"Rate limit threshold {threshold_name} reached: {usage_percentage:.1%}",
                data={
                    'usage_percentage': usage_percentage,
                    'requests_made': event.requests_made,
                    'limit': event.limit,
                    'threshold': threshold_name
                },
                endpoint_type=event.endpoint_type,
                identifier=event.identifier,
                cultural_context=event.cultural_context
            )
            
            # Store alert
            self.alerts.append(alert)
            self.last_alert_time[alert_key] = current_time
            
            # Log alert
            self._log_alert(alert)
            
            # Send alert to external systems if configured
            self._send_external_alert(alert)
            
        except Exception as e:
            logger.error(f"Error triggering threshold alert: {e}")
    
    def _trigger_violation_alert(self, event: RateLimitEvent) -> None:
        """Trigger a rate limit violation alert"""
        try:
            alert_key = f"{event.identifier}:{event.endpoint_type}:violation"
            current_time = time.time()
            
            # Check cooldown
            if alert_key in self.last_alert_time:
                if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                    return
            
            # Create alert
            alert = RateLimitAlert(
                alert_id=f"{alert_key}_{int(current_time)}",
                timestamp=current_time,
                alert_type="violation",
                severity="high",
                message=f"Rate limit exceeded for {event.endpoint_type}",
                data={
                    'requests_made': event.requests_made,
                    'limit': event.limit,
                    'endpoint': event.endpoint,
                    'method': event.method,
                    'path': event.path
                },
                endpoint_type=event.endpoint_type,
                identifier=event.identifier,
                cultural_context=event.cultural_context
            )
            
            # Store alert
            self.alerts.append(alert)
            self.last_alert_time[alert_key] = current_time
            
            # Log alert
            self._log_alert(alert)
            
            # Send alert to external systems
            self._send_external_alert(alert)
            
        except Exception as e:
            logger.error(f"Error triggering violation alert: {e}")
    
    def _check_suspicious_activity(self, event: RateLimitEvent) -> None:
        """Check for suspicious activity patterns"""
        try:
            current_time = time.time()
            
            # Check rapid requests pattern
            if self._is_rapid_requests(event):
                self._trigger_suspicious_alert(event, "rapid_requests")
            
            # Check multiple endpoints pattern
            if self._is_multiple_endpoints(event):
                self._trigger_suspicious_alert(event, "multiple_endpoints")
            
            # Check failed auth pattern
            if self._is_failed_auth(event):
                self._trigger_suspicious_alert(event, "failed_auth")
                
        except Exception as e:
            logger.error(f"Error checking suspicious activity: {e}")
    
    def _is_rapid_requests(self, event: RateLimitEvent) -> bool:
        """Check if identifier is making rapid requests"""
        try:
            # Count requests in the last minute
            cutoff_time = time.time() - 60
            recent_events = [
                e for e in self.events 
                if e.identifier == event.identifier and e.timestamp >= cutoff_time
            ]
            
            return len(recent_events) >= self.suspicious_patterns['rapid_requests']['threshold']
            
        except Exception as e:
            logger.error(f"Error checking rapid requests: {e}")
            return False
    
    def _is_multiple_endpoints(self, event: RateLimitEvent) -> bool:
        """Check if identifier is hitting multiple endpoints rapidly"""
        try:
            # Count unique endpoints in the last 5 minutes
            cutoff_time = time.time() - 300
            recent_events = [
                e for e in self.events 
                if e.identifier == event.identifier and e.timestamp >= cutoff_time
            ]
            
            unique_endpoints = set(e.endpoint_type for e in recent_events)
            return len(unique_endpoints) >= self.suspicious_patterns['multiple_endpoints']['threshold']
            
        except Exception as e:
            logger.error(f"Error checking multiple endpoints: {e}")
            return False
    
    def _is_failed_auth(self, event: RateLimitEvent) -> bool:
        """Check if there are multiple failed auth attempts"""
        try:
            # Count failed auth attempts in the last 5 minutes
            cutoff_time = time.time() - 300
            recent_auth_events = [
                e for e in self.events 
                if e.endpoint_type in ['login', 'password_reset'] and e.timestamp >= cutoff_time
            ]
            
            return len(recent_auth_events) >= self.suspicious_patterns['failed_auth']['threshold']
            
        except Exception as e:
            logger.error(f"Error checking failed auth: {e}")
            return False
    
    def _trigger_suspicious_alert(self, event: RateLimitEvent, pattern: str) -> None:
        """Trigger a suspicious activity alert"""
        try:
            alert_key = f"{event.identifier}:suspicious:{pattern}"
            current_time = time.time()
            
            # Check cooldown
            if alert_key in self.last_alert_time:
                if current_time - self.last_alert_time[alert_key] < self.alert_cooldown:
                    return
            
            # Create alert
            alert = RateLimitAlert(
                alert_id=f"{alert_key}_{int(current_time)}",
                timestamp=current_time,
                alert_type="suspicious",
                severity="medium",
                message=f"Suspicious activity detected: {pattern}",
                data={
                    'pattern': pattern,
                    'identifier': event.identifier,
                    'endpoint_type': event.endpoint_type,
                    'ip_address': event.ip_address
                },
                endpoint_type=event.endpoint_type,
                identifier=event.identifier,
                cultural_context=event.cultural_context
            )
            
            # Store alert
            self.alerts.append(alert)
            self.last_alert_time[alert_key] = current_time
            
            # Log alert
            self._log_alert(alert)
            
            # Send alert to external systems
            self._send_external_alert(alert)
            
        except Exception as e:
            logger.error(f"Error triggering suspicious alert: {e}")
    
    def _get_threshold_severity(self, threshold_name: str) -> str:
        """Get severity level for threshold"""
        severity_map = {
            'warning': 'low',
            'alert': 'medium',
            'critical': 'high'
        }
        return severity_map.get(threshold_name, 'medium')
    
    def _log_alert(self, alert: RateLimitAlert) -> None:
        """Log alert to monitoring system"""
        try:
            from backend.monitoring.logging_config import log_security_event
            
            log_security_event("rate_limit_alert", {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "endpoint_type": alert.endpoint_type,
                "identifier": alert.identifier,
                "cultural_context": alert.cultural_context,
                "data": alert.data
            }, alert.data.get('user_id'), alert.data.get('ip_address'))
            
        except Exception as e:
            logger.error(f"Error logging alert: {e}")
    
    def _send_external_alert(self, alert: RateLimitAlert) -> None:
        """Send alert to external monitoring systems"""
        try:
            # Check if external alerting is enabled
            if not current_app.config.get('RATE_LIMIT_EXTERNAL_ALERTS', False):
                return
            
            # Send to configured channels
            channels = current_app.config.get('RATE_LIMIT_ALERT_CHANNELS', [])
            
            for channel in channels:
                if channel == 'email':
                    self._send_email_alert(alert)
                elif channel == 'slack':
                    self._send_slack_alert(alert)
                elif channel == 'webhook':
                    self._send_webhook_alert(alert)
                    
        except Exception as e:
            logger.error(f"Error sending external alert: {e}")
    
    def _send_email_alert(self, alert: RateLimitAlert) -> None:
        """Send email alert"""
        try:
            # Implementation would depend on your email service
            logger.info(f"Email alert sent: {alert.message}")
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _send_slack_alert(self, alert: RateLimitAlert) -> None:
        """Send Slack alert"""
        try:
            # Implementation would depend on your Slack integration
            logger.info(f"Slack alert sent: {alert.message}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _send_webhook_alert(self, alert: RateLimitAlert) -> None:
        """Send webhook alert"""
        try:
            # Implementation would depend on your webhook configuration
            logger.info(f"Webhook alert sent: {alert.message}")
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current monitoring metrics"""
        try:
            metrics = dict(self.metrics)
            
            # Add calculated metrics
            if metrics.get('total_requests', 0) > 0:
                metrics['rate_limit_percentage'] = (
                    metrics.get('total_rate_limited', 0) / metrics['total_requests']
                ) * 100
            
            # Add recent activity
            metrics['recent_events'] = len(self.events)
            metrics['recent_alerts'] = len(self.alerts)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
    
    def get_alerts(self, hours: int = 24) -> List[RateLimitAlert]:
        """Get alerts from the last N hours"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            return [
                alert for alert in self.alerts 
                if alert.timestamp >= cutoff_time
            ]
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    def get_events(self, hours: int = 24) -> List[RateLimitEvent]:
        """Get events from the last N hours"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            return [
                event for event in self.events 
                if event.timestamp >= cutoff_time
            ]
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []

# Global monitor instance
_rate_limit_monitor = None

def get_rate_limit_monitor() -> RateLimitMonitor:
    """Get global rate limit monitor instance"""
    global _rate_limit_monitor
    if _rate_limit_monitor is None:
        # Try to get Redis client from app context
        redis_client = None
        try:
            if hasattr(current_app, 'redis_client'):
                redis_client = current_app.redis_client
            elif hasattr(current_app, 'extensions') and 'redis' in current_app.extensions:
                redis_client = current_app.extensions['redis']
        except RuntimeError:
            pass  # Outside app context
        
        _rate_limit_monitor = RateLimitMonitor(redis_client)
    return _rate_limit_monitor

def record_rate_limit_event(event_data: Dict[str, Any]) -> None:
    """Record a rate limit event"""
    try:
        monitor = get_rate_limit_monitor()
        
        event = RateLimitEvent(
            timestamp=event_data.get('timestamp', time.time()),
            identifier=event_data.get('identifier', 'unknown'),
            endpoint_type=event_data.get('endpoint_type', 'unknown'),
            requests_made=event_data.get('requests_made', 0),
            limit=event_data.get('limit', 0),
            limited=event_data.get('limited', False),
            ip_address=event_data.get('ip_address', 'unknown'),
            user_id=event_data.get('user_id'),
            user_agent=event_data.get('user_agent'),
            endpoint=event_data.get('endpoint'),
            method=event_data.get('method'),
            path=event_data.get('path'),
            cultural_context=event_data.get('cultural_context', {})
        )
        
        monitor.record_event(event)
        
    except Exception as e:
        logger.error(f"Error recording rate limit event: {e}")
