"""
Monitoring Dashboard
Provides real-time performance metrics, alert status, and system health information
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from flask import Blueprint, jsonify, render_template
from loguru import logger

# Import monitoring components
from .performance_monitoring import performance_monitor
from .alerting import alerting_system
from ..analytics.business_intelligence import business_intelligence

dashboard_bp = Blueprint('monitoring_dashboard', __name__)

@dataclass
class DashboardMetric:
    """Dashboard metric display"""
    name: str
    value: float
    unit: str
    trend: str  # 'up', 'down', 'stable'
    status: str  # 'good', 'warning', 'critical'
    description: str

class MonitoringDashboard:
    """Main monitoring dashboard class"""
    
    def __init__(self):
        self.last_update = datetime.now()
        self.metric_history = {}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Performance metrics
            performance_data = self._get_performance_metrics()
            
            # Alert status
            alert_data = self._get_alert_status()
            
            # System health
            system_health = self._get_system_health()
            
            # Business metrics
            business_metrics = self._get_business_metrics()
            
            # Recent activity
            recent_activity = self._get_recent_activity()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'performance': performance_data,
                'alerts': alert_data,
                'system_health': system_health,
                'business_metrics': business_metrics,
                'recent_activity': recent_activity,
                'overall_status': self._calculate_overall_status(
                    performance_data, alert_data, system_health
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)}
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance monitoring metrics"""
        try:
            # API performance
            api_summary = performance_monitor.get_api_performance_summary(1)  # Last hour
            
            # Database performance
            db_summary = performance_monitor.get_database_performance_summary(1)
            
            # Score calculation performance
            score_summary = performance_monitor.get_score_performance_summary(1)
            
            # User engagement
            engagement_summary = performance_monitor.get_user_engagement_summary(1)
            
            # System health
            system_health = performance_monitor.get_system_health_metrics()
            
            return {
                'api_performance': {
                    'avg_response_time': api_summary.get('overall', {}).get('avg_response_time', 0),
                    'total_requests': api_summary.get('overall', {}).get('total_requests', 0),
                    'error_rate': api_summary.get('overall', {}).get('error_rate', 0),
                    'status': self._get_performance_status(
                        api_summary.get('overall', {}).get('avg_response_time', 0),
                        thresholds={'good': 1.0, 'warning': 2.0, 'critical': 5.0}
                    )
                },
                'database_performance': {
                    'avg_execution_time': db_summary.get('overall', {}).get('avg_execution_time', 0),
                    'total_queries': db_summary.get('overall', {}).get('total_queries', 0),
                    'slow_queries': len(db_summary.get('slowest_queries', [])),
                    'status': self._get_performance_status(
                        db_summary.get('overall', {}).get('avg_execution_time', 0),
                        thresholds={'good': 0.1, 'warning': 0.5, 'critical': 1.0}
                    )
                },
                'score_calculations': {
                    'total_calculations': sum(
                        calc.get('count', 0) for calc in score_summary.get('calculations', [])
                    ),
                    'avg_execution_time': np.mean([
                        calc.get('avg_execution_time', 0) 
                        for calc in score_summary.get('calculations', [])
                    ]) if score_summary.get('calculations') else 0,
                    'status': 'good'  # Default status
                },
                'user_engagement': {
                    'active_users': engagement_summary.get('overall', {}).get('active_users', 0),
                    'total_sessions': engagement_summary.get('overall', {}).get('total_sessions', 0),
                    'avg_engagement_time': engagement_summary.get('overall', {}).get('total_engagement_time', 0),
                    'status': 'good'  # Default status
                },
                'system_resources': {
                    'cpu_usage': system_health.get('system', {}).get('cpu_percent', 0),
                    'memory_usage': system_health.get('system', {}).get('memory_percent', 0),
                    'disk_usage': system_health.get('system', {}).get('disk_percent', 0),
                    'status': self._get_system_status(system_health)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def _get_alert_status(self) -> Dict[str, Any]:
        """Get current alert status"""
        try:
            alert_summary = alerting_system.get_alert_summary()
            active_alerts = alerting_system.get_active_alerts()
            
            # Get recent alerts
            recent_alerts = alerting_system.get_alert_history(1)  # Last hour
            
            return {
                'active_alerts': len(active_alerts),
                'critical_alerts': alert_summary.get('critical_alerts', 0),
                'high_alerts': alert_summary.get('high_alerts', 0),
                'medium_alerts': alert_summary.get('medium_alerts', 0),
                'low_alerts': alert_summary.get('low_alerts', 0),
                'recent_alerts': [
                    {
                        'rule_name': alert.rule_name,
                        'severity': alert.severity,
                        'message': alert.message,
                        'timestamp': alert.timestamp.isoformat()
                    }
                    for alert in recent_alerts[:10]  # Last 10 alerts
                ],
                'status': self._get_alert_status_level(alert_summary)
            }
            
        except Exception as e:
            logger.error(f"Failed to get alert status: {e}")
            return {}
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            system_health = performance_monitor.get_system_health_metrics()
            
            return {
                'cpu': {
                    'usage_percent': system_health.get('system', {}).get('cpu_percent', 0),
                    'status': self._get_resource_status(
                        system_health.get('system', {}).get('cpu_percent', 0),
                        thresholds={'good': 70, 'warning': 85, 'critical': 95}
                    )
                },
                'memory': {
                    'usage_percent': system_health.get('system', {}).get('memory_percent', 0),
                    'available_gb': system_health.get('system', {}).get('memory_available', 0) / (1024**3),
                    'status': self._get_resource_status(
                        system_health.get('system', {}).get('memory_percent', 0),
                        thresholds={'good': 80, 'warning': 90, 'critical': 95}
                    )
                },
                'disk': {
                    'usage_percent': system_health.get('system', {}).get('disk_percent', 0),
                    'free_gb': system_health.get('system', {}).get('disk_free', 0) / (1024**3),
                    'status': self._get_resource_status(
                        system_health.get('system', {}).get('disk_percent', 0),
                        thresholds={'good': 80, 'warning': 90, 'critical': 95}
                    )
                },
                'process': {
                    'memory_mb': system_health.get('process', {}).get('memory_rss', 0) / (1024**2),
                    'cpu_percent': system_health.get('process', {}).get('cpu_percent', 0),
                    'status': 'good'  # Default status
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {}
    
    def _get_business_metrics(self) -> Dict[str, Any]:
        """Get business intelligence metrics"""
        try:
            # Get business intelligence data
            bi_data = business_intelligence.get_insights_report(1)  # Last day
            
            return {
                'user_metrics': {
                    'total_users': bi_data.get('summary', {}).get('total_users', 0),
                    'active_features': bi_data.get('summary', {}).get('active_features', 0),
                    'avg_satisfaction': bi_data.get('summary', {}).get('avg_satisfaction', 0),
                    'total_roi': bi_data.get('summary', {}).get('total_roi', 0)
                },
                'insights': [
                    {
                        'type': insight.get('type'),
                        'category': insight.get('category'),
                        'message': insight.get('message'),
                        'priority': insight.get('priority')
                    }
                    for insight in bi_data.get('insights', [])[:5]  # Top 5 insights
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get business metrics: {e}")
            return {}
    
    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent system activity"""
        try:
            # Get recent performance metrics
            api_metrics = performance_monitor.get_api_performance_summary(1)
            recent_endpoints = api_metrics.get('endpoints', [])[:5]
            
            # Get recent alerts
            recent_alerts = alerting_system.get_alert_history(1)
            
            activity = []
            
            # Add endpoint activity
            for endpoint in recent_endpoints:
                activity.append({
                    'type': 'api_request',
                    'description': f"{endpoint['method']} {endpoint['endpoint']}",
                    'value': f"{endpoint['request_count']} requests",
                    'timestamp': datetime.now().isoformat(),
                    'status': 'info'
                })
            
            # Add alert activity
            for alert in recent_alerts[:5]:
                activity.append({
                    'type': 'alert',
                    'description': alert.message,
                    'value': alert.severity.upper(),
                    'timestamp': alert.timestamp.isoformat(),
                    'status': alert.severity
                })
            
            # Sort by timestamp
            activity.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return activity[:20]  # Last 20 activities
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def _get_performance_status(self, value: float, thresholds: Dict[str, float]) -> str:
        """Get performance status based on thresholds"""
        if value <= thresholds.get('good', float('inf')):
            return 'good'
        elif value <= thresholds.get('warning', float('inf')):
            return 'warning'
        else:
            return 'critical'
    
    def _get_system_status(self, system_health: Dict[str, Any]) -> str:
        """Get overall system status"""
        cpu_usage = system_health.get('system', {}).get('cpu_percent', 0)
        memory_usage = system_health.get('system', {}).get('memory_percent', 0)
        disk_usage = system_health.get('system', {}).get('disk_percent', 0)
        
        if cpu_usage > 95 or memory_usage > 95 or disk_usage > 95:
            return 'critical'
        elif cpu_usage > 85 or memory_usage > 90 or disk_usage > 90:
            return 'warning'
        else:
            return 'good'
    
    def _get_alert_status_level(self, alert_summary: Dict[str, Any]) -> str:
        """Get alert status level"""
        if alert_summary.get('critical_alerts', 0) > 0:
            return 'critical'
        elif alert_summary.get('high_alerts', 0) > 0:
            return 'warning'
        elif alert_summary.get('active_alerts', 0) > 0:
            return 'info'
        else:
            return 'good'
    
    def _get_resource_status(self, usage: float, thresholds: Dict[str, float]) -> str:
        """Get resource status based on usage"""
        if usage <= thresholds.get('good', float('inf')):
            return 'good'
        elif usage <= thresholds.get('warning', float('inf')):
            return 'warning'
        else:
            return 'critical'
    
    def _calculate_overall_status(self, performance: Dict, alerts: Dict, system_health: Dict) -> str:
        """Calculate overall system status"""
        # Check for critical issues
        if (alerts.get('critical_alerts', 0) > 0 or 
            performance.get('api_performance', {}).get('status') == 'critical' or
            performance.get('database_performance', {}).get('status') == 'critical' or
            performance.get('system_resources', {}).get('status') == 'critical'):
            return 'critical'
        
        # Check for warnings
        if (alerts.get('high_alerts', 0) > 0 or 
            performance.get('api_performance', {}).get('status') == 'warning' or
            performance.get('database_performance', {}).get('status') == 'warning' or
            performance.get('system_resources', {}).get('status') == 'warning'):
            return 'warning'
        
        return 'good'

# Global dashboard instance
monitoring_dashboard = MonitoringDashboard()

# Dashboard routes
@dashboard_bp.route('/api/monitoring/dashboard')
def get_dashboard():
    """Get monitoring dashboard data"""
    try:
        dashboard_data = monitoring_dashboard.get_dashboard_data()
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@dashboard_bp.route('/api/monitoring/metrics')
def get_metrics():
    """Get current metrics"""
    try:
        metrics = {
            'performance': monitoring_dashboard._get_performance_metrics(),
            'alerts': monitoring_dashboard._get_alert_status(),
            'system_health': monitoring_dashboard._get_system_health(),
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return jsonify({'error': 'Failed to load metrics'}), 500

@dashboard_bp.route('/api/monitoring/alerts')
def get_alerts():
    """Get current alerts"""
    try:
        alerts = {
            'active': [
                {
                    'rule_name': alert.rule_name,
                    'severity': alert.severity,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in alerting_system.get_active_alerts()
            ],
            'summary': alerting_system.get_alert_summary(),
            'statistics': alerting_system.get_alert_statistics(24)
        }
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Alerts error: {e}")
        return jsonify({'error': 'Failed to load alerts'}), 500

@dashboard_bp.route('/api/monitoring/performance')
def get_performance():
    """Get performance metrics"""
    try:
        performance_data = monitoring_dashboard._get_performance_metrics()
        return jsonify(performance_data)
    except Exception as e:
        logger.error(f"Performance error: {e}")
        return jsonify({'error': 'Failed to load performance data'}), 500

@dashboard_bp.route('/api/monitoring/system-health')
def get_system_health():
    """Get system health metrics"""
    try:
        system_health = monitoring_dashboard._get_system_health()
        return jsonify(system_health)
    except Exception as e:
        logger.error(f"System health error: {e}")
        return jsonify({'error': 'Failed to load system health data'}), 500 