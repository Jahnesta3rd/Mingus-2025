#!/usr/bin/env python3
"""
PostgreSQL Monitoring and Alerting System for MINGUS Application
Monitors database performance, uptime, and health metrics
"""

import os
import time
import json
import logging
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import psycopg2
from psycopg2.extras import RealDictCursor
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('postgresql_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    metric: str
    warning_threshold: float
    critical_threshold: float
    time_window: int  # minutes
    description: str

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    timestamp: datetime
    connection_count: int
    active_connections: int
    idle_connections: int
    query_time_avg: float
    query_time_max: float
    slow_queries: int
    cache_hit_ratio: float
    disk_usage_percent: float
    memory_usage_percent: float
    uptime_seconds: int
    total_queries: int
    error_rate: float

class PostgreSQLMonitor:
    """PostgreSQL database monitoring and alerting system"""
    
    def __init__(self, database_url: str, alert_config: Dict[str, Any]):
        self.database_url = database_url
        self.alert_config = alert_config
        self.alert_thresholds = self._load_alert_thresholds()
        self.alert_history = []
        self.metrics_history = []
        
    def _load_alert_thresholds(self) -> List[AlertThreshold]:
        """Load alert thresholds from configuration"""
        return [
            AlertThreshold(
                metric="connection_count",
                warning_threshold=80,
                critical_threshold=95,
                time_window=5,
                description="Database connection pool utilization"
            ),
            AlertThreshold(
                metric="query_time_avg",
                warning_threshold=100,  # ms
                critical_threshold=500,  # ms
                time_window=5,
                description="Average query response time"
            ),
            AlertThreshold(
                metric="cache_hit_ratio",
                warning_threshold=0.85,  # 85%
                critical_threshold=0.70,  # 70%
                time_window=10,
                description="Database cache hit ratio"
            ),
            AlertThreshold(
                metric="disk_usage_percent",
                warning_threshold=80,
                critical_threshold=90,
                time_window=15,
                description="Disk space utilization"
            ),
            AlertThreshold(
                metric="memory_usage_percent",
                warning_threshold=85,
                critical_threshold=95,
                time_window=5,
                description="Memory utilization"
            ),
            AlertThreshold(
                metric="error_rate",
                warning_threshold=0.05,  # 5%
                critical_threshold=0.10,  # 10%
                time_window=5,
                description="Database error rate"
            ),
            AlertThreshold(
                metric="slow_queries",
                warning_threshold=10,
                critical_threshold=50,
                time_window=5,
                description="Number of slow queries"
            )
        ]
    
    def get_database_connection(self):
        """Get database connection with error handling"""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._send_alert("CRITICAL", "Database Connection Failure", 
                           f"Unable to connect to PostgreSQL database: {e}")
            return None
    
    def collect_metrics(self) -> Optional[DatabaseMetrics]:
        """Collect current database metrics"""
        conn = self.get_database_connection()
        if not conn:
            return None
            
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                metrics = {}
                
                # Connection metrics
                cursor.execute("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections
                    FROM pg_stat_activity
                """)
                conn_stats = cursor.fetchone()
                metrics['connection_count'] = conn_stats['total_connections']
                metrics['active_connections'] = conn_stats['active_connections']
                metrics['idle_connections'] = conn_stats['idle_connections']
                
                # Query performance metrics
                cursor.execute("""
                    SELECT 
                        avg(total_time) as avg_query_time,
                        max(total_time) as max_query_time,
                        count(*) FILTER (WHERE total_time > 1000) as slow_queries,
                        count(*) as total_queries
                    FROM pg_stat_statements
                    WHERE calls > 0
                """)
                query_stats = cursor.fetchone()
                metrics['query_time_avg'] = query_stats['avg_query_time'] or 0
                metrics['query_time_max'] = query_stats['max_query_time'] or 0
                metrics['slow_queries'] = query_stats['slow_queries'] or 0
                metrics['total_queries'] = query_stats['total_queries'] or 0
                
                # Cache hit ratio
                cursor.execute("""
                    SELECT 
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
                    FROM pg_statio_user_tables
                """)
                cache_stats = cursor.fetchone()
                metrics['cache_hit_ratio'] = cache_stats['cache_hit_ratio'] or 0
                
                # Disk usage
                cursor.execute("""
                    SELECT 
                        pg_database_size(current_database()) as db_size,
                        pg_size_pretty(pg_database_size(current_database())) as db_size_pretty
                """)
                disk_stats = cursor.fetchone()
                # Estimate disk usage (this would need to be adjusted based on actual disk size)
                metrics['disk_usage_percent'] = min(50, (disk_stats['db_size'] / (1024**3)) * 10)  # Rough estimate
                
                # Uptime
                cursor.execute("SELECT extract(epoch from now() - pg_postmaster_start_time()) as uptime")
                uptime_stats = cursor.fetchone()
                metrics['uptime_seconds'] = int(uptime_stats['uptime'])
                
                # Error rate (approximation based on failed connections)
                cursor.execute("""
                    SELECT 
                        sum(confl_tablespace) + sum(confl_lock) + sum(confl_snapshot) + 
                        sum(confl_bufferpin) + sum(confl_deadlock) as total_conflicts
                    FROM pg_stat_database_conflicts
                """)
                conflict_stats = cursor.fetchone()
                total_conflicts = conflict_stats['total_conflicts'] or 0
                metrics['error_rate'] = min(1.0, total_conflicts / max(metrics['total_queries'], 1))
                
                # Memory usage (approximation)
                cursor.execute("""
                    SELECT 
                        sum(shared_blks_hit + shared_blks_read) as total_blocks,
                        sum(shared_blks_hit) as cached_blocks
                    FROM pg_stat_database
                """)
                memory_stats = cursor.fetchone()
                total_blocks = memory_stats['total_blocks'] or 1
                cached_blocks = memory_stats['cached_blocks'] or 0
                metrics['memory_usage_percent'] = min(100, (cached_blocks / total_blocks) * 100)
                
                return DatabaseMetrics(
                    timestamp=datetime.now(),
                    **metrics
                )
                
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return None
        finally:
            conn.close()
    
    def check_alerts(self, metrics: DatabaseMetrics) -> List[Dict[str, Any]]:
        """Check metrics against alert thresholds"""
        alerts = []
        
        for threshold in self.alert_thresholds:
            metric_value = getattr(metrics, threshold.metric)
            
            if metric_value >= threshold.critical_threshold:
                alerts.append({
                    'level': 'CRITICAL',
                    'metric': threshold.metric,
                    'value': metric_value,
                    'threshold': threshold.critical_threshold,
                    'description': threshold.description,
                    'timestamp': metrics.timestamp
                })
            elif metric_value >= threshold.warning_threshold:
                alerts.append({
                    'level': 'WARNING',
                    'metric': threshold.metric,
                    'value': metric_value,
                    'threshold': threshold.warning_threshold,
                    'description': threshold.description,
                    'timestamp': metrics.timestamp
                })
        
        return alerts
    
    def _send_alert(self, level: str, subject: str, message: str):
        """Send alert via configured channels"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log alert
        logger.warning(f"ALERT [{level}] {subject}: {message}")
        
        # Store in alert history
        self.alert_history.append({
            'timestamp': datetime.now(),
            'level': level,
            'subject': subject,
            'message': message
        })
        
        # Send email alert if configured
        if self.alert_config.get('email_enabled', False):
            self._send_email_alert(level, subject, message)
        
        # Send webhook alert if configured
        if self.alert_config.get('webhook_enabled', False):
            self._send_webhook_alert(level, subject, message)
        
        # Send Slack alert if configured
        if self.alert_config.get('slack_enabled', False):
            self._send_slack_alert(level, subject, message)
    
    def _send_email_alert(self, level: str, subject: str, message: str):
        """Send email alert"""
        try:
            email_config = self.alert_config.get('email', {})
            
            msg = MIMEMultipart()
            msg['From'] = email_config.get('from_email')
            msg['To'] = email_config.get('to_email')
            msg['Subject'] = f"[MINGUS DB] {level}: {subject}"
            
            body = f"""
            PostgreSQL Database Alert
            
            Level: {level}
            Subject: {subject}
            Message: {message}
            Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            
            This is an automated alert from the MINGUS PostgreSQL monitoring system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(email_config.get('smtp_server'), email_config.get('smtp_port'))
            server.starttls()
            server.login(email_config.get('username'), email_config.get('password'))
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def _send_webhook_alert(self, level: str, subject: str, message: str):
        """Send webhook alert"""
        try:
            webhook_url = self.alert_config.get('webhook', {}).get('url')
            
            payload = {
                'level': level,
                'subject': subject,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'source': 'mingus_postgresql_monitor'
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def _send_slack_alert(self, level: str, subject: str, message: str):
        """Send Slack alert"""
        try:
            slack_config = self.alert_config.get('slack', {})
            webhook_url = slack_config.get('webhook_url')
            
            color = '#ff0000' if level == 'CRITICAL' else '#ffa500'
            
            payload = {
                'attachments': [{
                    'color': color,
                    'title': f"PostgreSQL Alert: {subject}",
                    'text': message,
                    'fields': [
                        {
                            'title': 'Level',
                            'value': level,
                            'short': True
                        },
                        {
                            'title': 'Time',
                            'value': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'short': True
                        }
                    ],
                    'footer': 'MINGUS PostgreSQL Monitor'
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Slack alert sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        if not self.metrics_history:
            return {'status': 'No data available'}
        
        latest_metrics = self.metrics_history[-1]
        
        # Calculate trends
        if len(self.metrics_history) >= 2:
            previous_metrics = self.metrics_history[-2]
            trends = {
                'connection_trend': latest_metrics.connection_count - previous_metrics.connection_count,
                'query_time_trend': latest_metrics.query_time_avg - previous_metrics.query_time_avg,
                'cache_hit_trend': latest_metrics.cache_hit_ratio - previous_metrics.cache_hit_ratio
            }
        else:
            trends = {'connection_trend': 0, 'query_time_trend': 0, 'cache_hit_trend': 0}
        
        # Determine overall health status
        health_score = 100
        
        if latest_metrics.connection_count > 80:
            health_score -= 20
        if latest_metrics.query_time_avg > 200:
            health_score -= 20
        if latest_metrics.cache_hit_ratio < 0.8:
            health_score -= 15
        if latest_metrics.error_rate > 0.05:
            health_score -= 25
        
        health_status = 'HEALTHY' if health_score >= 80 else 'DEGRADED' if health_score >= 60 else 'CRITICAL'
        
        return {
            'status': health_status,
            'health_score': health_score,
            'timestamp': latest_metrics.timestamp.isoformat(),
            'metrics': {
                'connection_count': latest_metrics.connection_count,
                'active_connections': latest_metrics.active_connections,
                'query_time_avg': latest_metrics.query_time_avg,
                'cache_hit_ratio': latest_metrics.cache_hit_ratio,
                'disk_usage_percent': latest_metrics.disk_usage_percent,
                'memory_usage_percent': latest_metrics.memory_usage_percent,
                'error_rate': latest_metrics.error_rate,
                'uptime_seconds': latest_metrics.uptime_seconds
            },
            'trends': trends,
            'recent_alerts': self.alert_history[-10:] if self.alert_history else []
        }
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        logger.info("Starting monitoring cycle...")
        
        # Collect metrics
        metrics = self.collect_metrics()
        if not metrics:
            logger.error("Failed to collect metrics")
            return
        
        # Store metrics
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 metrics (about 8 hours at 30-second intervals)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Check for alerts
        alerts = self.check_alerts(metrics)
        for alert in alerts:
            self._send_alert(
                alert['level'],
                f"Database {alert['metric']} Alert",
                f"{alert['description']}: {alert['value']} (threshold: {alert['threshold']})"
            )
        
        # Generate and log health report
        health_report = self.generate_health_report()
        logger.info(f"Health Status: {health_report['status']} (Score: {health_report['health_score']})")
        
        logger.info("Monitoring cycle completed")

def main():
    """Main monitoring function"""
    # Configuration
    database_url = os.getenv('DATABASE_URL', 'postgresql://mingus_user:mingus_password@localhost:5432/mingus_production')
    
    alert_config = {
        'email_enabled': os.getenv('EMAIL_ALERTS_ENABLED', 'false').lower() == 'true',
        'webhook_enabled': os.getenv('WEBHOOK_ALERTS_ENABLED', 'false').lower() == 'true',
        'slack_enabled': os.getenv('SLACK_ALERTS_ENABLED', 'false').lower() == 'true',
        'email': {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL'),
            'to_email': os.getenv('TO_EMAIL')
        },
        'webhook': {
            'url': os.getenv('WEBHOOK_URL')
        },
        'slack': {
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL')
        }
    }
    
    # Initialize monitor
    monitor = PostgreSQLMonitor(database_url, alert_config)
    
    # Schedule monitoring
    schedule.every(30).seconds.do(monitor.run_monitoring_cycle)
    
    logger.info("PostgreSQL monitoring started. Running every 30 seconds...")
    
    # Run monitoring loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            time.sleep(30)  # Wait before retrying

if __name__ == "__main__":
    main() 