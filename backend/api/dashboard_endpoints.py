#!/usr/bin/env python3
"""
Dashboard API Endpoints
Provides data for monitoring dashboard
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from backend.monitoring.system_monitor import SystemResourceMonitor
from backend.monitoring.error_monitor import get_error_monitor
import logging

logger = logging.getLogger(__name__)

dashboard_api = Blueprint('dashboard_api', __name__)

# Global references (will be set by app.py)
_system_monitor: SystemResourceMonitor = None
_error_monitor = None

def init_dashboard(system_monitor: SystemResourceMonitor, error_monitor):
    """Initialize dashboard with monitor instances"""
    global _system_monitor, _error_monitor
    _system_monitor = system_monitor
    _error_monitor = error_monitor

@dashboard_api.route('/api/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get dashboard overview data"""
    try:
        # Get system metrics
        system_metrics = _system_monitor.get_metrics() if _system_monitor else None
        
        # Get error stats
        error_stats = _error_monitor.get_error_stats(hours=24) if _error_monitor else None
        
        # Get health status
        health_status = _system_monitor.get_health_status() if _system_monitor else None
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'system': system_metrics.get('system') if system_metrics else None,
            'application': system_metrics.get('application') if system_metrics else None,
            'errors': error_stats,
            'health': health_status,
            'alerts': system_metrics.get('alerts', []) if system_metrics else []
        })
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/api/dashboard/system', methods=['GET'])
def get_system_metrics():
    """Get system resource metrics"""
    try:
        metrics = _system_monitor.get_metrics() if _system_monitor else None
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'system': metrics.get('system') if metrics else None
        })
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/api/dashboard/application', methods=['GET'])
def get_application_metrics():
    """Get application metrics"""
    try:
        metrics = _system_monitor.get_metrics() if _system_monitor else None
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'application': metrics.get('application') if metrics else None
        })
    except Exception as e:
        logger.error(f"Error getting application metrics: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/api/dashboard/errors', methods=['GET'])
def get_error_metrics():
    """Get error metrics"""
    try:
        hours = int(request.args.get('hours', 24))
        stats = _error_monitor.get_error_stats(hours=hours) if _error_monitor else None
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'errors': stats
        })
    except Exception as e:
        logger.error(f"Error getting error metrics: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/api/dashboard/history', methods=['GET'])
def get_metrics_history():
    """Get metrics history for charts"""
    try:
        hours = int(request.args.get('hours', 1))
        metric_type = request.args.get('type', 'all')  # 'system', 'application', 'all'
        
        if not _system_monitor:
            return jsonify({'history': []})
        
        # Get history from system monitor
        history = list(_system_monitor.metrics_history)
        
        # Filter by time
        cutoff = datetime.now() - timedelta(hours=hours)
        filtered_history = [
            h for h in history
            if datetime.fromisoformat(h['timestamp']) >= cutoff
        ]
        
        # Format for charts
        chart_data = {
            'timestamps': [],
            'cpu': [],
            'memory': [],
            'disk': [],
            'request_rate': [],
            'error_rate': [],
            'response_time': []
        }
        
        for entry in filtered_history:
            timestamp = entry['timestamp']
            system = entry.get('system', {})
            application = entry.get('application', {})
            
            chart_data['timestamps'].append(timestamp)
            
            if system:
                chart_data['cpu'].append(system.get('cpu_percent', 0))
                chart_data['memory'].append(system.get('memory_percent', 0))
                chart_data['disk'].append(system.get('disk_percent', 0))
            
            if application:
                chart_data['request_rate'].append(application.get('request_rate', 0))
                chart_data['error_rate'].append(application.get('error_rate', 0))
                chart_data['response_time'].append(application.get('avg_response_time', 0))
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'history': chart_data,
            'count': len(filtered_history)
        })
    except Exception as e:
        logger.error(f"Error getting metrics history: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/api/dashboard/alerts', methods=['GET'])
def get_alerts():
    """Get active alerts"""
    try:
        metrics = _system_monitor.get_metrics() if _system_monitor else None
        error_stats = _error_monitor.get_error_stats(hours=1) if _error_monitor else None
        
        alerts = []
        
        # System alerts
        if metrics and metrics.get('alerts'):
            alerts.extend(metrics['alerts'])
        
        # Error alerts
        if error_stats and error_stats.get('alerts'):
            alerts.extend(error_stats['alerts'])
        
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'alerts': alerts,
            'count': len(alerts)
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_api.route('/api/dashboard/recommendations', methods=['GET'])
def get_recommendations():
    """Get performance recommendations"""
    try:
        recommendations = _system_monitor.get_recommendations() if _system_monitor else []
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'recommendations': recommendations,
            'count': len(recommendations)
        })
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({'error': str(e)}), 500
