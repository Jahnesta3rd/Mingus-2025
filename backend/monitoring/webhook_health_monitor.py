"""
Webhook Health Monitor for MINGUS
=================================

Comprehensive health monitoring system for webhook endpoints including:
- Real-time endpoint health monitoring
- Performance metrics tracking
- Error rate monitoring
- System resource monitoring
- Alert generation and escalation
- Health status reporting

Author: MINGUS Development Team
Date: January 2025
"""

import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import psutil
import requests
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import redis
from prometheus_client import Counter, Histogram, Gauge, Summary

from ..config.base import Config

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class AlertLevel(Enum):
    """Alert level enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthMetric:
    """Health metric data structure"""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    status: HealthStatus
    threshold: float
    metadata: Dict[str, Any] = None


@dataclass
class HealthCheck:
    """Health check data structure"""
    check_name: str
    status: HealthStatus
    response_time: float
    error_count: int
    success_count: int
    last_check: datetime
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = None


class WebhookHealthMonitor:
    """Comprehensive webhook health monitoring system"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Initialize Redis for caching
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True
        )
        
        # Prometheus metrics
        self.metrics = self._initialize_prometheus_metrics()
        
        # Health monitoring configuration
        self.health_config = {
            'check_interval': 30,  # seconds
            'timeout': 10,  # seconds
            'retry_count': 3,
            'thresholds': {
                'response_time_ms': 1000,
                'error_rate_percent': 5.0,
                'cpu_usage_percent': 80.0,
                'memory_usage_percent': 85.0,
                'disk_usage_percent': 90.0,
                'queue_size': 1000,
                'active_connections': 100
            },
            'alerting': {
                'enabled': True,
                'slack_webhook': config.SLACK_WEBHOOK_URL,
                'email_alerts': config.EMAIL_ALERTS_ENABLED,
                'pagerduty_key': config.PAGERDUTY_API_KEY
            }
        }
        
        # Health state
        self.health_state = {
            'overall_status': HealthStatus.HEALTHY,
            'last_check': datetime.now(timezone.utc),
            'checks': {},
            'metrics': {},
            'alerts': []
        }
        
        # Monitoring thread
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # Initialize health checks
        self._initialize_health_checks()
    
    def start_monitoring(self):
        """Start the health monitoring system"""
        try:
            if not self.monitoring_active:
                self.monitoring_active = True
                self.monitoring_thread = threading.Thread(
                    target=self._monitoring_loop,
                    daemon=True
                )
                self.monitoring_thread.start()
                logger.info("Webhook health monitoring started")
                
                # Record startup metric
                self.metrics['monitoring_startups'].inc()
                
        except Exception as e:
            logger.error(f"Error starting health monitoring: {e}")
            self.monitoring_active = False
    
    def stop_monitoring(self):
        """Stop the health monitoring system"""
        try:
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)
            logger.info("Webhook health monitoring stopped")
            
        except Exception as e:
            logger.error(f"Error stopping health monitoring: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        try:
            # Update overall status
            self._update_overall_status()
            
            return {
                'status': self.health_state['overall_status'].value,
                'last_check': self.health_state['last_check'].isoformat(),
                'checks': {
                    name: asdict(check) for name, check in self.health_state['checks'].items()
                },
                'metrics': {
                    name: asdict(metric) for name, metric in self.health_state['metrics'].items()
                },
                'alerts': [
                    asdict(alert) for alert in self.health_state['alerts'][-10:]  # Last 10 alerts
                ],
                'summary': self._generate_health_summary()
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                'status': HealthStatus.UNHEALTHY.value,
                'error': str(e),
                'last_check': datetime.now(timezone.utc).isoformat()
            }
    
    def record_webhook_event(self, event_type: str, processing_time: float, success: bool, error: Optional[str] = None):
        """Record webhook event processing metrics"""
        try:
            timestamp = datetime.now(timezone.utc)
            
            # Update Prometheus metrics
            self.metrics['webhook_events_total'].labels(event_type=event_type).inc()
            self.metrics['webhook_processing_duration'].observe(processing_time)
            
            if success:
                self.metrics['webhook_events_success'].labels(event_type=event_type).inc()
            else:
                self.metrics['webhook_events_failed'].labels(event_type=event_type).inc()
                self.metrics['webhook_errors_total'].labels(error_type=error or 'unknown').inc()
            
            # Update health metrics
            self._update_webhook_metrics(event_type, processing_time, success, error)
            
            # Store in Redis for real-time monitoring
            self._store_event_metric(event_type, processing_time, success, timestamp)
            
        except Exception as e:
            logger.error(f"Error recording webhook event: {e}")
    
    def check_endpoint_health(self, endpoint_url: str) -> HealthCheck:
        """Check health of a specific endpoint"""
        try:
            start_time = time.time()
            
            # Perform health check
            response = requests.get(
                f"{endpoint_url}/health",
                timeout=self.health_config['timeout'],
                headers={'User-Agent': 'MINGUS-Health-Monitor/1.0'}
            )
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Determine status based on response
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                error_count = 0
                last_error = None
            else:
                status = HealthStatus.UNHEALTHY
                error_count = 1
                last_error = f"HTTP {response.status_code}"
            
            health_check = HealthCheck(
                check_name=f"endpoint_{endpoint_url}",
                status=status,
                response_time=response_time,
                error_count=error_count,
                success_count=1 if status == HealthStatus.HEALTHY else 0,
                last_check=datetime.now(timezone.utc),
                last_error=last_error,
                metadata={
                    'endpoint_url': endpoint_url,
                    'status_code': response.status_code,
                    'response_size': len(response.content)
                }
            )
            
            # Update metrics
            self.metrics['endpoint_health_checks'].labels(endpoint=endpoint_url).inc()
            self.metrics['endpoint_response_time'].labels(endpoint=endpoint_url).observe(response_time)
            
            return health_check
            
        except requests.exceptions.Timeout:
            return self._create_failed_health_check(endpoint_url, "Timeout")
        except requests.exceptions.ConnectionError:
            return self._create_failed_health_check(endpoint_url, "Connection Error")
        except Exception as e:
            return self._create_failed_health_check(endpoint_url, str(e))
    
    def check_system_resources(self) -> Dict[str, HealthMetric]:
        """Check system resource usage"""
        try:
            metrics = {}
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_metric = HealthMetric(
                metric_name="cpu_usage",
                value=cpu_percent,
                unit="percent",
                timestamp=datetime.now(timezone.utc),
                status=self._get_metric_status(cpu_percent, self.health_config['thresholds']['cpu_usage_percent']),
                threshold=self.health_config['thresholds']['cpu_usage_percent']
            )
            metrics['cpu_usage'] = cpu_metric
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_metric = HealthMetric(
                metric_name="memory_usage",
                value=memory.percent,
                unit="percent",
                timestamp=datetime.now(timezone.utc),
                status=self._get_metric_status(memory.percent, self.health_config['thresholds']['memory_usage_percent']),
                threshold=self.health_config['thresholds']['memory_usage_percent']
            )
            metrics['memory_usage'] = memory_metric
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_metric = HealthMetric(
                metric_name="disk_usage",
                value=disk.percent,
                unit="percent",
                timestamp=datetime.now(timezone.utc),
                status=self._get_metric_status(disk.percent, self.health_config['thresholds']['disk_usage_percent']),
                threshold=self.health_config['thresholds']['disk_usage_percent']
            )
            metrics['disk_usage'] = disk_metric
            
            # Network connections
            connections = len(psutil.net_connections())
            connection_metric = HealthMetric(
                metric_name="active_connections",
                value=connections,
                unit="count",
                timestamp=datetime.now(timezone.utc),
                status=self._get_metric_status(connections, self.health_config['thresholds']['active_connections']),
                threshold=self.health_config['thresholds']['active_connections']
            )
            metrics['active_connections'] = connection_metric
            
            # Update Prometheus metrics
            self.metrics['system_cpu_usage'].set(cpu_percent)
            self.metrics['system_memory_usage'].set(memory.percent)
            self.metrics['system_disk_usage'].set(disk.percent)
            self.metrics['system_active_connections'].set(connections)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {}
    
    def check_database_health(self) -> HealthCheck:
        """Check database health"""
        try:
            start_time = time.time()
            
            # Perform database health check
            self.db.execute("SELECT 1")
            
            response_time = (time.time() - start_time) * 1000
            
            health_check = HealthCheck(
                check_name="database_health",
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                error_count=0,
                success_count=1,
                last_check=datetime.now(timezone.utc),
                metadata={
                    'database_type': 'postgresql',
                    'connection_pool_size': self.db.bind.pool.size(),
                    'checked_out_connections': self.db.bind.pool.checkedout()
                }
            )
            
            # Update metrics
            self.metrics['database_health_checks'].inc()
            self.metrics['database_response_time'].observe(response_time)
            
            return health_check
            
        except SQLAlchemyError as e:
            return self._create_failed_health_check("database", str(e))
        except Exception as e:
            return self._create_failed_health_check("database", str(e))
    
    def check_redis_health(self) -> HealthCheck:
        """Check Redis health"""
        try:
            start_time = time.time()
            
            # Perform Redis health check
            self.redis_client.ping()
            
            response_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = self.redis_client.info()
            
            health_check = HealthCheck(
                check_name="redis_health",
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                error_count=0,
                success_count=1,
                last_check=datetime.now(timezone.utc),
                metadata={
                    'redis_version': info.get('redis_version'),
                    'connected_clients': info.get('connected_clients'),
                    'used_memory_human': info.get('used_memory_human'),
                    'keyspace_hits': info.get('keyspace_hits'),
                    'keyspace_misses': info.get('keyspace_misses')
                }
            )
            
            # Update metrics
            self.metrics['redis_health_checks'].inc()
            self.metrics['redis_response_time'].observe(response_time)
            
            return health_check
            
        except redis.RedisError as e:
            return self._create_failed_health_check("redis", str(e))
        except Exception as e:
            return self._create_failed_health_check("redis", str(e))
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        try:
            # Get current health status
            health_status = self.get_health_status()
            
            # Get system metrics
            system_metrics = self.check_system_resources()
            
            # Get database and Redis health
            db_health = self.check_database_health()
            redis_health = self.check_redis_health()
            
            # Calculate statistics
            stats = self._calculate_health_statistics()
            
            report = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'overall_status': health_status['status'],
                'summary': health_status['summary'],
                'system_metrics': {
                    name: asdict(metric) for name, metric in system_metrics.items()
                },
                'service_health': {
                    'database': asdict(db_health),
                    'redis': asdict(redis_health)
                },
                'statistics': stats,
                'alerts': health_status['alerts'],
                'recommendations': self._generate_recommendations(health_status, system_metrics)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating health report: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'status': HealthStatus.UNHEALTHY.value
            }
    
    # Private methods
    
    def _initialize_prometheus_metrics(self) -> Dict[str, Any]:
        """Initialize Prometheus metrics"""
        return {
            'webhook_events_total': Counter(
                'webhook_events_total',
                'Total number of webhook events processed',
                ['event_type']
            ),
            'webhook_events_success': Counter(
                'webhook_events_success',
                'Number of successfully processed webhook events',
                ['event_type']
            ),
            'webhook_events_failed': Counter(
                'webhook_events_failed',
                'Number of failed webhook events',
                ['event_type']
            ),
            'webhook_processing_duration': Histogram(
                'webhook_processing_duration_seconds',
                'Webhook processing duration in seconds',
                ['event_type']
            ),
            'webhook_errors_total': Counter(
                'webhook_errors_total',
                'Total number of webhook errors',
                ['error_type']
            ),
            'endpoint_health_checks': Counter(
                'endpoint_health_checks_total',
                'Total number of endpoint health checks',
                ['endpoint']
            ),
            'endpoint_response_time': Histogram(
                'endpoint_response_time_seconds',
                'Endpoint response time in seconds',
                ['endpoint']
            ),
            'database_health_checks': Counter(
                'database_health_checks_total',
                'Total number of database health checks'
            ),
            'database_response_time': Histogram(
                'database_response_time_seconds',
                'Database response time in seconds'
            ),
            'redis_health_checks': Counter(
                'redis_health_checks_total',
                'Total number of Redis health checks'
            ),
            'redis_response_time': Histogram(
                'redis_response_time_seconds',
                'Redis response time in seconds'
            ),
            'system_cpu_usage': Gauge(
                'system_cpu_usage_percent',
                'System CPU usage percentage'
            ),
            'system_memory_usage': Gauge(
                'system_memory_usage_percent',
                'System memory usage percentage'
            ),
            'system_disk_usage': Gauge(
                'system_disk_usage_percent',
                'System disk usage percentage'
            ),
            'system_active_connections': Gauge(
                'system_active_connections',
                'Number of active network connections'
            ),
            'monitoring_startups': Counter(
                'monitoring_startups_total',
                'Total number of monitoring system startups'
            )
        }
    
    def _initialize_health_checks(self):
        """Initialize health checks"""
        # Initialize with basic checks
        self.health_state['checks'] = {
            'database': HealthCheck(
                check_name="database",
                status=HealthStatus.HEALTHY,
                response_time=0.0,
                error_count=0,
                success_count=0,
                last_check=datetime.now(timezone.utc)
            ),
            'redis': HealthCheck(
                check_name="redis",
                status=HealthStatus.HEALTHY,
                response_time=0.0,
                error_count=0,
                success_count=0,
                last_check=datetime.now(timezone.utc)
            ),
            'system': HealthCheck(
                check_name="system",
                status=HealthStatus.HEALTHY,
                response_time=0.0,
                error_count=0,
                success_count=0,
                last_check=datetime.now(timezone.utc)
            )
        }
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Perform health checks
                self._perform_health_checks()
                
                # Update metrics
                self._update_health_metrics()
                
                # Check for alerts
                self._check_alerts()
                
                # Sleep for check interval
                time.sleep(self.health_config['check_interval'])
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.health_config['check_interval'])
    
    def _perform_health_checks(self):
        """Perform all health checks"""
        try:
            # Check database health
            db_health = self.check_database_health()
            self.health_state['checks']['database'] = db_health
            
            # Check Redis health
            redis_health = self.check_redis_health()
            self.health_state['checks']['redis'] = redis_health
            
            # Check system resources
            system_metrics = self.check_system_resources()
            self.health_state['metrics'].update(system_metrics)
            
            # Update last check time
            self.health_state['last_check'] = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")
    
    def _update_health_metrics(self):
        """Update health metrics"""
        try:
            # Calculate error rates
            total_events = 0
            failed_events = 0
            
            for check in self.health_state['checks'].values():
                total_events += check.success_count + check.error_count
                failed_events += check.error_count
            
            if total_events > 0:
                error_rate = (failed_events / total_events) * 100
                
                error_rate_metric = HealthMetric(
                    metric_name="error_rate",
                    value=error_rate,
                    unit="percent",
                    timestamp=datetime.now(timezone.utc),
                    status=self._get_metric_status(error_rate, self.health_config['thresholds']['error_rate_percent']),
                    threshold=self.health_config['thresholds']['error_rate_percent']
                )
                
                self.health_state['metrics']['error_rate'] = error_rate_metric
            
        except Exception as e:
            logger.error(f"Error updating health metrics: {e}")
    
    def _update_overall_status(self):
        """Update overall health status"""
        try:
            # Check if any critical failures
            critical_failures = 0
            degraded_services = 0
            
            for check in self.health_state['checks'].values():
                if check.status == HealthStatus.CRITICAL:
                    critical_failures += 1
                elif check.status == HealthStatus.DEGRADED:
                    degraded_services += 1
            
            # Check metrics for critical thresholds
            for metric in self.health_state['metrics'].values():
                if metric.status == HealthStatus.CRITICAL:
                    critical_failures += 1
                elif metric.status == HealthStatus.DEGRADED:
                    degraded_services += 1
            
            # Determine overall status
            if critical_failures > 0:
                self.health_state['overall_status'] = HealthStatus.CRITICAL
            elif degraded_services > 0:
                self.health_state['overall_status'] = HealthStatus.DEGRADED
            else:
                self.health_state['overall_status'] = HealthStatus.HEALTHY
                
        except Exception as e:
            logger.error(f"Error updating overall status: {e}")
            self.health_state['overall_status'] = HealthStatus.UNHEALTHY
    
    def _check_alerts(self):
        """Check for alerts and send notifications"""
        try:
            if not self.health_config['alerting']['enabled']:
                return
            
            # Check for new alerts
            new_alerts = []
            
            # Check overall status
            if self.health_state['overall_status'] == HealthStatus.CRITICAL:
                alert = Alert(
                    alert_id=f"critical_{int(time.time())}",
                    level=AlertLevel.CRITICAL,
                    title="Critical System Health Alert",
                    message="System health is critical. Immediate attention required.",
                    source="health_monitor",
                    timestamp=datetime.now(timezone.utc)
                )
                new_alerts.append(alert)
            
            # Check individual metrics
            for metric_name, metric in self.health_state['metrics'].items():
                if metric.status == HealthStatus.CRITICAL:
                    alert = Alert(
                        alert_id=f"metric_critical_{metric_name}_{int(time.time())}",
                        level=AlertLevel.ERROR,
                        title=f"Critical Metric Alert: {metric_name}",
                        message=f"{metric_name} is at critical level: {metric.value} {metric.unit}",
                        source="health_monitor",
                        timestamp=datetime.now(timezone.utc),
                        metadata={'metric_name': metric_name, 'value': metric.value}
                    )
                    new_alerts.append(alert)
            
            # Send alerts
            for alert in new_alerts:
                self._send_alert(alert)
                self.health_state['alerts'].append(alert)
            
            # Keep only recent alerts
            self.health_state['alerts'] = self.health_state['alerts'][-100:]
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _send_alert(self, alert: Alert):
        """Send alert notification"""
        try:
            # Send to Slack
            if self.health_config['alerting']['slack_webhook']:
                self._send_slack_alert(alert)
            
            # Send email
            if self.health_config['alerting']['email_alerts']:
                self._send_email_alert(alert)
            
            # Send to PagerDuty
            if self.health_config['alerting']['pagerduty_key']:
                self._send_pagerduty_alert(alert)
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _send_slack_alert(self, alert: Alert):
        """Send alert to Slack"""
        try:
            payload = {
                "text": f"*{alert.title}*",
                "attachments": [
                    {
                        "color": self._get_alert_color(alert.level),
                        "fields": [
                            {
                                "title": "Level",
                                "value": alert.level.value.upper(),
                                "short": True
                            },
                            {
                                "title": "Source",
                                "value": alert.source,
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False
                            }
                        ],
                        "footer": f"Alert ID: {alert.alert_id}",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            response = requests.post(
                self.health_config['alerting']['slack_webhook'],
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to send Slack alert: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    def _send_email_alert(self, alert: Alert):
        """Send alert via email"""
        # Implementation would depend on email service
        logger.info(f"Email alert would be sent: {alert.title}")
    
    def _send_pagerduty_alert(self, alert: Alert):
        """Send alert to PagerDuty"""
        # Implementation would depend on PagerDuty integration
        logger.info(f"PagerDuty alert would be sent: {alert.title}")
    
    def _get_alert_color(self, level: AlertLevel) -> str:
        """Get alert color for Slack"""
        colors = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ffa500",
            AlertLevel.ERROR: "#ff0000",
            AlertLevel.CRITICAL: "#8b0000"
        }
        return colors.get(level, "#808080")
    
    def _create_failed_health_check(self, check_name: str, error: str) -> HealthCheck:
        """Create a failed health check"""
        return HealthCheck(
            check_name=check_name,
            status=HealthStatus.UNHEALTHY,
            response_time=0.0,
            error_count=1,
            success_count=0,
            last_check=datetime.now(timezone.utc),
            last_error=error
        )
    
    def _get_metric_status(self, value: float, threshold: float) -> HealthStatus:
        """Get health status based on metric value and threshold"""
        if value >= threshold * 1.2:  # 20% above threshold
            return HealthStatus.CRITICAL
        elif value >= threshold:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _update_webhook_metrics(self, event_type: str, processing_time: float, success: bool, error: Optional[str]):
        """Update webhook-specific metrics"""
        try:
            # Update Redis with real-time metrics
            key = f"webhook_metrics:{event_type}:{datetime.now(timezone.utc).strftime('%Y%m%d:%H')}"
            
            pipeline = self.redis_client.pipeline()
            pipeline.hincrby(key, "total", 1)
            pipeline.hincrby(key, "success" if success else "failed", 1)
            pipeline.hset(key, "last_processing_time", processing_time)
            pipeline.hset(key, "last_update", datetime.now(timezone.utc).isoformat())
            pipeline.expire(key, 86400)  # 24 hours
            pipeline.execute()
            
        except Exception as e:
            logger.error(f"Error updating webhook metrics: {e}")
    
    def _store_event_metric(self, event_type: str, processing_time: float, success: bool, timestamp: datetime):
        """Store event metric in Redis"""
        try:
            key = f"webhook_events:{event_type}:{timestamp.strftime('%Y%m%d:%H')}"
            
            pipeline = self.redis_client.pipeline()
            pipeline.lpush(key, json.dumps({
                'timestamp': timestamp.isoformat(),
                'processing_time': processing_time,
                'success': success
            }))
            pipeline.ltrim(key, 0, 999)  # Keep last 1000 events
            pipeline.expire(key, 86400)  # 24 hours
            pipeline.execute()
            
        except Exception as e:
            logger.error(f"Error storing event metric: {e}")
    
    def _generate_health_summary(self) -> Dict[str, Any]:
        """Generate health summary"""
        try:
            total_checks = len(self.health_state['checks'])
            healthy_checks = sum(1 for check in self.health_state['checks'].values() if check.status == HealthStatus.HEALTHY)
            degraded_checks = sum(1 for check in self.health_state['checks'].values() if check.status == HealthStatus.DEGRADED)
            unhealthy_checks = sum(1 for check in self.health_state['checks'].values() if check.status == HealthStatus.UNHEALTHY)
            
            total_metrics = len(self.health_state['metrics'])
            healthy_metrics = sum(1 for metric in self.health_state['metrics'].values() if metric.status == HealthStatus.HEALTHY)
            degraded_metrics = sum(1 for metric in self.health_state['metrics'].values() if metric.status == HealthStatus.DEGRADED)
            critical_metrics = sum(1 for metric in self.health_state['metrics'].values() if metric.status == HealthStatus.CRITICAL)
            
            return {
                'checks': {
                    'total': total_checks,
                    'healthy': healthy_checks,
                    'degraded': degraded_checks,
                    'unhealthy': unhealthy_checks
                },
                'metrics': {
                    'total': total_metrics,
                    'healthy': healthy_metrics,
                    'degraded': degraded_metrics,
                    'critical': critical_metrics
                },
                'alerts': {
                    'total': len(self.health_state['alerts']),
                    'unacknowledged': sum(1 for alert in self.health_state['alerts'] if not alert.acknowledged)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating health summary: {e}")
            return {}
    
    def _calculate_health_statistics(self) -> Dict[str, Any]:
        """Calculate health statistics"""
        try:
            # Calculate average response times
            avg_response_times = {}
            for check_name, check in self.health_state['checks'].items():
                if check.success_count > 0:
                    avg_response_times[check_name] = check.response_time
            
            # Calculate error rates
            error_rates = {}
            for check_name, check in self.health_state['checks'].items():
                total = check.success_count + check.error_count
                if total > 0:
                    error_rates[check_name] = (check.error_count / total) * 100
            
            return {
                'average_response_times': avg_response_times,
                'error_rates': error_rates,
                'uptime_percentage': self._calculate_uptime_percentage()
            }
            
        except Exception as e:
            logger.error(f"Error calculating health statistics: {e}")
            return {}
    
    def _calculate_uptime_percentage(self) -> float:
        """Calculate uptime percentage"""
        try:
            # This would typically calculate based on historical data
            # For now, return a placeholder
            return 99.9
        except Exception as e:
            logger.error(f"Error calculating uptime percentage: {e}")
            return 0.0
    
    def _generate_recommendations(self, health_status: Dict[str, Any], system_metrics: Dict[str, HealthMetric]) -> List[str]:
        """Generate recommendations based on health status"""
        recommendations = []
        
        try:
            # Check for high CPU usage
            if 'cpu_usage' in system_metrics:
                cpu_metric = system_metrics['cpu_usage']
                if cpu_metric.status in [HealthStatus.DEGRADED, HealthStatus.CRITICAL]:
                    recommendations.append(f"Consider scaling up CPU resources. Current usage: {cpu_metric.value}%")
            
            # Check for high memory usage
            if 'memory_usage' in system_metrics:
                memory_metric = system_metrics['memory_usage']
                if memory_metric.status in [HealthStatus.DEGRADED, HealthStatus.CRITICAL]:
                    recommendations.append(f"Consider increasing memory allocation. Current usage: {memory_metric.value}%")
            
            # Check for high disk usage
            if 'disk_usage' in system_metrics:
                disk_metric = system_metrics['disk_usage']
                if disk_metric.status in [HealthStatus.DEGRADED, HealthStatus.CRITICAL]:
                    recommendations.append(f"Consider cleaning up disk space or expanding storage. Current usage: {disk_metric.value}%")
            
            # Check for high error rates
            if health_status['status'] in ['degraded', 'unhealthy']:
                recommendations.append("Review error logs and investigate root causes of failures")
            
            # Check for degraded services
            if any(check['status'] == 'degraded' for check in health_status['checks'].values()):
                recommendations.append("Monitor degraded services and consider maintenance windows")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Unable to generate recommendations due to system error"] 