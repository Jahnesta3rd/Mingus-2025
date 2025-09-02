"""
Performance Monitoring API Blueprint
Provides REST endpoints for accessing comprehensive performance metrics
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional

from .comprehensive_monitor import comprehensive_monitor, CoreWebVital

# Create blueprint
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check for monitoring system"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "monitoring_active": True
    }), 200

@monitoring_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get comprehensive performance metrics summary"""
    try:
        # Get format parameter
        format_type = request.args.get('format', 'json').lower()
        
        if format_type == 'json':
            metrics = comprehensive_monitor.get_metrics_summary()
            return jsonify(metrics), 200
        elif format_type == 'csv':
            csv_data = comprehensive_monitor.export_metrics('csv')
            return csv_data, 200, {'Content-Type': 'text/csv'}
        else:
            return jsonify({"error": "Unsupported format. Use 'json' or 'csv'"}), 400
            
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve metrics",
            "message": str(e)
        }), 500

@monitoring_bp.route('/metrics/database', methods=['GET'])
def get_database_metrics():
    """Get database performance metrics"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)
        table = request.args.get('table')
        slow_only = request.args.get('slow_only', 'false').lower() == 'true'
        
        with comprehensive_monitor.lock:
            metrics = comprehensive_monitor.db_metrics.copy()
        
        # Apply filters
        if table:
            metrics = [m for m in metrics if m.table == table]
        
        if slow_only:
            metrics = [m for m in metrics if m.slow_query]
        
        # Sort by timestamp (newest first) and limit
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        metrics = metrics[:limit]
        
        # Convert to dict format
        result = {
            "total_queries": len(comprehensive_monitor.db_metrics),
            "filtered_queries": len(metrics),
            "slow_queries": len([m for m in comprehensive_monitor.db_metrics if m.slow_query]),
            "avg_duration": sum(m.duration for m in comprehensive_monitor.db_metrics) / len(comprehensive_monitor.db_metrics) if comprehensive_monitor.db_metrics else 0,
            "metrics": [{
                "query": m.query,
                "duration": m.duration,
                "timestamp": m.timestamp.isoformat(),
                "table": m.table,
                "rows_affected": m.rows_affected,
                "slow_query": m.slow_query
            } for m in metrics]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve database metrics",
            "message": str(e)
        }), 500

@monitoring_bp.route('/metrics/redis', methods=['GET'])
def get_redis_metrics():
    """Get Redis performance metrics"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)
        operation = request.args.get('operation')
        slow_only = request.args.get('slow_only', 'false').lower() == 'true'
        
        with comprehensive_monitor.lock:
            metrics = comprehensive_monitor.redis_metrics.copy()
        
        # Apply filters
        if operation:
            metrics = [m for m in metrics if m.operation == operation]
        
        if slow_only:
            metrics = [m for m in metrics if m.slow_query]
        
        # Sort by timestamp (newest first) and limit
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        metrics = metrics[:limit]
        
        # Convert to dict format
        result = {
            "total_operations": len(comprehensive_monitor.redis_metrics),
            "filtered_operations": len(metrics),
            "slow_operations": len([m for m in comprehensive_monitor.redis_metrics if m.slow_query]),
            "avg_duration": sum(m.duration for m in comprehensive_monitor.redis_metrics) / len(comprehensive_monitor.redis_metrics) if comprehensive_monitor.redis_metrics else 0,
            "operations_by_type": {},
            "metrics": [{
                "operation": m.operation,
                "key": m.key,
                "duration": m.duration,
                "timestamp": m.timestamp.isoformat(),
                "slow_query": m.slow_query
            } for m in metrics]
        }
        
        # Add operation type breakdown
        for metric in comprehensive_monitor.redis_metrics:
            op_type = metric.operation
            if op_type not in result["operations_by_type"]:
                result["operations_by_type"][op_type] = 0
            result["operations_by_type"][op_type] += 1
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve Redis metrics",
            "message": str(e)
        }), 500

@monitoring_bp.route('/metrics/api', methods=['GET'])
def get_api_metrics():
    """Get API performance metrics"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)
        endpoint = request.args.get('endpoint')
        method = request.args.get('method')
        status_code = request.args.get('status_code')
        slow_only = request.args.get('slow_only', 'false').lower() == 'true'
        
        with comprehensive_monitor.lock:
            metrics = comprehensive_monitor.api_metrics.copy()
        
        # Apply filters
        if endpoint:
            metrics = [m for m in metrics if endpoint in m.endpoint]
        
        if method:
            metrics = [m for m in metrics if m.method.upper() == method.upper()]
        
        if status_code:
            metrics = [m for m in metrics if str(m.status_code) == status_code]
        
        if slow_only:
            metrics = [m for m in metrics if m.duration > comprehensive_monitor.thresholds['slow_api_threshold_ms']]
        
        # Sort by timestamp (newest first) and limit
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        metrics = metrics[:limit]
        
        # Convert to dict format
        result = {
            "total_requests": len(comprehensive_monitor.api_metrics),
            "filtered_requests": len(metrics),
            "slow_requests": len([m for m in comprehensive_monitor.api_metrics if m.duration > comprehensive_monitor.thresholds['slow_api_threshold_ms']]),
            "avg_response_time": sum(m.duration for m in comprehensive_monitor.api_metrics) / len(comprehensive_monitor.api_metrics) if comprehensive_monitor.api_metrics else 0,
            "status_code_distribution": comprehensive_monitor._get_status_code_distribution(),
            "endpoints": list(set(m.endpoint for m in comprehensive_monitor.api_metrics)),
            "methods": list(set(m.method for m in comprehensive_monitor.api_metrics)),
            "metrics": [{
                "endpoint": m.endpoint,
                "method": m.method,
                "duration": m.duration,
                "timestamp": m.timestamp.isoformat(),
                "status_code": m.status_code,
                "user_agent": m.user_agent,
                "ip_address": m.ip_address,
                "request_size": m.request_size,
                "response_size": m.response_size
            } for m in metrics]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve API metrics",
            "message": str(e)
        }), 500

@monitoring_bp.route('/metrics/celery', methods=['GET'])
def get_celery_metrics():
    """Get Celery task performance metrics"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)
        task_name = request.args.get('task_name')
        success_only = request.args.get('success_only')
        slow_only = request.args.get('slow_only', 'false').lower() == 'true'
        
        with comprehensive_monitor.lock:
            metrics = comprehensive_monitor.celery_metrics.copy()
        
        # Apply filters
        if task_name:
            metrics = [m for m in metrics if task_name in m.task_name]
        
        if success_only is not None:
            success_bool = success_only.lower() == 'true'
            metrics = [m for m in metrics if m.success == success_bool]
        
        if slow_only:
            metrics = [m for m in metrics if m.duration > comprehensive_monitor.thresholds['slow_celery_threshold_ms']]
        
        # Sort by timestamp (newest first) and limit
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        metrics = metrics[:limit]
        
        # Convert to dict format
        result = {
            "total_tasks": len(comprehensive_monitor.celery_metrics),
            "filtered_tasks": len(metrics),
            "successful_tasks": len([m for m in comprehensive_monitor.celery_metrics if m.success]),
            "failed_tasks": len([m for m in comprehensive_monitor.celery_metrics if not m.success]),
            "avg_duration": sum(m.duration for m in comprehensive_monitor.celery_metrics) / len(comprehensive_monitor.celery_metrics) if comprehensive_monitor.celery_metrics else 0,
            "task_names": list(set(m.task_name for m in comprehensive_monitor.celery_metrics)),
            "queue_names": list(set(m.queue_name for m in comprehensive_monitor.celery_metrics if m.queue_name)),
            "metrics": [{
                "task_name": m.task_name,
                "duration": m.duration,
                "timestamp": m.timestamp.isoformat(),
                "success": m.success,
                "queue_name": m.queue_name,
                "worker_name": m.worker_name,
                "retries": m.retries
            } for m in metrics]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve Celery metrics",
            "message": str(e)
        }), 500

@monitoring_bp.route('/metrics/system', methods=['GET'])
def get_system_metrics():
    """Get system performance metrics"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)
        hours = int(request.args.get('hours', 24))
        
        with comprehensive_monitor.lock:
            metrics = comprehensive_monitor.system_metrics.copy()
        
        # Filter by time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        metrics = [m for m in metrics if m.timestamp > cutoff_time]
        
        # Sort by timestamp (newest first) and limit
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        metrics = metrics[:limit]
        
        # Calculate averages for the time period
        if metrics:
            avg_cpu = sum(m.cpu_percent for m in metrics) / len(metrics)
            avg_memory = sum(m.memory_percent for m in metrics) / len(metrics)
            avg_disk = sum(m.disk_usage_percent for m in metrics) / len(metrics)
        else:
            avg_cpu = avg_memory = avg_disk = 0
        
        # Convert to dict format
        result = {
            "total_metrics": len(comprehensive_monitor.system_metrics),
            "filtered_metrics": len(metrics),
            "time_range_hours": hours,
            "current_cpu": comprehensive_monitor.system_metrics[-1].cpu_percent if comprehensive_monitor.system_metrics else 0,
            "current_memory": comprehensive_monitor.system_metrics[-1].memory_percent if comprehensive_monitor.system_metrics else 0,
            "current_disk": comprehensive_monitor.system_metrics[-1].disk_usage_percent if comprehensive_monitor.system_metrics else 0,
            "avg_cpu": avg_cpu,
            "avg_memory": avg_memory,
            "avg_disk": avg_disk,
            "thresholds": comprehensive_monitor.thresholds,
            "metrics": [{
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "memory_available": m.memory_available,
                "disk_usage_percent": m.disk_usage_percent,
                "network_io": m.network_io,
                "timestamp": m.timestamp.isoformat()
            } for m in metrics]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve system metrics",
            "message": str(e)
        }), 500

@monitoring_bp.route('/metrics/web-vitals', methods=['GET'])
def get_web_vitals():
    """Get Core Web Vitals metrics"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 100)), 1000)
        metric_name = request.args.get('metric_name')
        page_url = request.args.get('page_url')
        hours = int(request.args.get('hours', 24))
        
        with comprehensive_monitor.lock:
            metrics = comprehensive_monitor.web_vitals.copy()
        
        # Apply filters
        if metric_name:
            metrics = [m for m in metrics if m.metric_name.upper() == metric_name.upper()]
        
        if page_url:
            metrics = [m for m in metrics if page_url in m.page_url]
        
        # Filter by time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        metrics = [m for m in metrics if m.timestamp > cutoff_time]
        
        # Sort by timestamp (newest first) and limit
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        metrics = metrics[:limit]
        
        # Convert to dict format
        result = {
            "total_metrics": len(comprehensive_monitor.web_vitals),
            "filtered_metrics": len(metrics),
            "time_range_hours": hours,
            "metric_names": list(set(m.metric_name for m in comprehensive_monitor.web_vitals)),
            "page_urls": list(set(m.page_url for m in comprehensive_monitor.web_vitals)),
            "metrics": [{
                "metric_name": m.metric_name,
                "value": m.value,
                "timestamp": m.timestamp.isoformat(),
                "page_url": m.page_url,
                "user_id": m.user_id,
                "device_type": m.device_type,
                "browser": m.browser
            } for m in metrics]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve web vitals",
            "message": str(e)
        }), 500

@monitoring_bp.route('/web-vitals', methods=['POST'])
def add_web_vital():
    """Add a Core Web Vital metric"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['metric_name', 'value', 'page_url']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create CoreWebVital metric
        metric = CoreWebVital(
            metric_name=data['metric_name'],
            value=float(data['value']),
            timestamp=datetime.utcnow(),
            page_url=data['page_url'],
            user_id=data.get('user_id'),
            device_type=data.get('device_type'),
            browser=data.get('browser')
        )
        
        comprehensive_monitor.add_web_vital(metric)
        
        return jsonify({
            "status": "success",
            "message": "Web vital metric added successfully"
        }), 201
        
    except Exception as e:
        return jsonify({
            "error": "Failed to add web vital metric",
            "message": str(e)
        }), 500

@monitoring_bp.route('/reset', methods=['POST'])
def reset_metrics():
    """Reset all performance metrics (admin only)"""
    try:
        # In production, you might want to add authentication here
        comprehensive_monitor.reset_metrics()
        
        return jsonify({
            "status": "success",
            "message": "All metrics reset successfully"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to reset metrics",
            "message": str(e)
        }), 500

@monitoring_bp.route('/config', methods=['GET'])
def get_config():
    """Get current monitoring configuration"""
    try:
        return jsonify({
            "config": comprehensive_monitor.config,
            "thresholds": comprehensive_monitor.thresholds
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve configuration",
            "message": str(e)
        }), 500

@monitoring_bp.route('/config/thresholds', methods=['PUT'])
def update_thresholds():
    """Update performance thresholds"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update thresholds
        for key, value in data.items():
            if key in comprehensive_monitor.thresholds:
                comprehensive_monitor.thresholds[key] = float(value)
            else:
                return jsonify({"error": f"Invalid threshold key: {key}"}), 400
        
        return jsonify({
            "status": "success",
            "message": "Thresholds updated successfully",
            "thresholds": comprehensive_monitor.thresholds
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to update thresholds",
            "message": str(e)
        }), 500

@monitoring_bp.route('/export', methods=['GET'])
def export_metrics():
    """Export metrics in various formats"""
    try:
        format_type = request.args.get('format', 'json').lower()
        
        if format_type not in ['json', 'csv']:
            return jsonify({"error": "Unsupported format. Use 'json' or 'csv'"}), 400
        
        exported_data = comprehensive_monitor.export_metrics(format_type)
        
        if format_type == 'json':
            return jsonify(json.loads(exported_data)), 200
        else:
            return exported_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=performance_metrics_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
            }
            
    except Exception as e:
        return jsonify({
            "error": "Failed to export metrics",
            "message": str(e)
        }), 500
