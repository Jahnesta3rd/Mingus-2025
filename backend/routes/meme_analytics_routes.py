"""
Meme Analytics API Routes
========================

Flask API endpoints for the meme analytics dashboard.
Provides metrics, charts, alerts, and data export functionality.

Features:
- Dashboard metrics endpoints
- Chart generation endpoints
- Alert monitoring endpoints
- Data export endpoints
- Sample queries and reports
- Admin dashboard functionality

Author: MINGUS Development Team
Date: January 2025
"""

from flask import Blueprint, request, jsonify, session, current_app, send_file
from flask_cors import cross_origin
from functools import wraps
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
import time
from datetime import datetime, timedelta, timezone
import json
import io
import uuid

from ..analytics.meme_analytics import (
    MemeAnalyticsService, create_meme_analytics_service,
    track_meme_view, track_meme_skip, track_meme_conversion
)
from ..config.base import Config

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
meme_analytics_bp = Blueprint('meme_analytics', __name__, url_prefix='/api/meme-analytics')

def get_db_session() -> Session:
    """Get database session"""
    return current_app.db.session

def require_admin_auth():
    """Decorator to require admin authentication"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user is admin (simplified - would need proper admin check)
            # In production, implement proper admin role checking
            return f(*args, **kwargs)
        return wrapper
    return decorator

def get_analytics_service() -> MemeAnalyticsService:
    """Get meme analytics service instance"""
    return create_meme_analytics_service(get_db_session(), current_app.config)

def parse_date_range(request) -> tuple[datetime, datetime]:
    """Parse date range from request parameters"""
    try:
        # Default to last 30 days
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)
        
        # Parse custom date range if provided
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date').replace('Z', '+00:00'))
        
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date').replace('Z', '+00:00'))
        
        return start_date, end_date
    except Exception as e:
        logger.error(f"Error parsing date range: {e}")
        # Return default range on error
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=30)
        return start_date, end_date


@meme_analytics_bp.route('/dashboard/metrics', methods=['GET'])
@cross_origin()
@require_admin_auth()
def get_dashboard_metrics():
    """
    Get dashboard metrics for meme analytics
    
    Query Parameters:
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - category: Optional category filter
    
    Returns:
        JSON with dashboard metrics
    """
    try:
        start_date, end_date = parse_date_range(request)
        category = request.args.get('category')
        
        analytics_service = get_analytics_service()
        
        # Get engagement metrics
        engagement_metrics = analytics_service.get_meme_engagement_metrics(
            start_date, end_date, category
        )
        
        # Get category performance
        category_metrics = analytics_service.get_category_performance_metrics(
            start_date, end_date
        )
        
        # Get daily trends
        days = (end_date - start_date).days
        daily_trends = analytics_service.get_daily_engagement_trends(days)
        
        # Get user demographics
        demographics = analytics_service.get_user_demographics_metrics(
            start_date, end_date
        )
        
        # Get retention analysis
        retention_analysis = analytics_service.get_user_retention_analysis(days)
        
        return jsonify({
            'success': True,
            'data': {
                'engagement_metrics': {
                    'total_views': engagement_metrics.total_views,
                    'total_skips': engagement_metrics.total_skips,
                    'total_likes': engagement_metrics.total_likes,
                    'total_shares': engagement_metrics.total_shares,
                    'total_conversions': engagement_metrics.total_conversions,
                    'skip_rate': engagement_metrics.skip_rate,
                    'engagement_rate': engagement_metrics.engagement_rate,
                    'conversion_rate': engagement_metrics.conversion_rate,
                    'avg_time_spent': engagement_metrics.avg_time_spent,
                    'unique_users': engagement_metrics.unique_users
                },
                'category_metrics': [
                    {
                        'category': metric.category,
                        'total_views': metric.total_views,
                        'total_skips': metric.total_skips,
                        'skip_rate': metric.skip_rate,
                        'engagement_rate': metric.engagement_rate,
                        'avg_time_spent': metric.avg_time_spent,
                        'unique_users': metric.unique_users,
                        'conversion_rate': metric.conversion_rate
                    }
                    for metric in category_metrics
                ],
                'daily_trends': daily_trends,
                'demographics': [
                    {
                        'age_group': demo.age_group,
                        'gender': demo.gender,
                        'location': demo.location,
                        'device_type': demo.device_type,
                        'skip_rate': demo.skip_rate,
                        'engagement_rate': demo.engagement_rate,
                        'avg_time_spent': demo.avg_time_spent,
                        'user_count': demo.user_count
                    }
                    for demo in demographics
                ],
                'retention_analysis': retention_analysis,
                'date_range': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get dashboard metrics'
        }), 500


@meme_analytics_bp.route('/dashboard/charts', methods=['GET'])
@cross_origin()
@require_admin_auth()
def get_dashboard_charts():
    """
    Get visualization charts for the admin dashboard
    
    Query Parameters:
    - days: Number of days to analyze (default: 30)
    
    Returns:
        JSON with chart HTML data
    """
    try:
        days = int(request.args.get('days', 30))
        
        analytics_service = get_analytics_service()
        charts = analytics_service.generate_visualization_charts(days)
        
        return jsonify({
            'success': True,
            'data': {
                'charts': charts,
                'days_analyzed': days
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating charts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate charts'
        }), 500


@meme_analytics_bp.route('/alerts', methods=['GET'])
@cross_origin()
@require_admin_auth()
def get_alerts():
    """
    Get current alerts for meme analytics
    
    Returns:
        JSON with current alerts
    """
    try:
        analytics_service = get_analytics_service()
        alerts = analytics_service.check_alert_conditions()
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': [
                    {
                        'alert_id': alert.alert_id,
                        'alert_type': alert.alert_type,
                        'severity': alert.severity,
                        'message': alert.message,
                        'threshold': alert.threshold,
                        'current_value': alert.current_value,
                        'timestamp': alert.timestamp.isoformat(),
                        'is_resolved': alert.is_resolved,
                        'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None
                    }
                    for alert in alerts
                ],
                'total_alerts': len(alerts),
                'critical_alerts': len([a for a in alerts if a.severity == 'critical']),
                'warning_alerts': len([a for a in alerts if a.severity == 'warning'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get alerts'
        }), 500


@meme_analytics_bp.route('/export', methods=['GET'])
@cross_origin()
@require_admin_auth()
def export_analytics_data():
    """
    Export analytics data for deeper analysis
    
    Query Parameters:
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - format: Export format ('csv' or 'json')
    
    Returns:
        File download or JSON data
    """
    try:
        start_date, end_date = parse_date_range(request)
        export_format = request.args.get('format', 'csv').lower()
        
        if export_format not in ['csv', 'json']:
            return jsonify({
                'success': False,
                'error': 'Unsupported export format. Use "csv" or "json"'
            }), 400
        
        analytics_service = get_analytics_service()
        exported_data = analytics_service.export_analytics_data(
            start_date, end_date, export_format
        )
        
        if export_format == 'csv':
            # Return CSV file
            output = io.BytesIO(exported_data.encode('utf-8'))
            output.seek(0)
            
            filename = f"meme_analytics_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        else:
            # Return JSON data
            return jsonify({
                'success': True,
                'data': json.loads(exported_data),
                'export_info': {
                    'format': export_format,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'records': len(json.loads(exported_data))
                }
            })
        
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to export analytics data'
        }), 500


@meme_analytics_bp.route('/sample-queries', methods=['GET'])
@cross_origin()
@require_admin_auth()
def get_sample_queries():
    """
    Get sample queries for non-technical users
    
    Returns:
        JSON with sample queries and descriptions
    """
    try:
        analytics_service = get_analytics_service()
        sample_queries = analytics_service.get_sample_queries()
        
        return jsonify({
            'success': True,
            'data': {
                'sample_queries': sample_queries,
                'total_queries': len(sample_queries)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting sample queries: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get sample queries'
        }), 500


@meme_analytics_bp.route('/sample-reports', methods=['GET'])
@cross_origin()
@require_admin_auth()
def get_sample_reports():
    """
    Get sample reports for non-technical users
    
    Returns:
        JSON with sample reports and data
    """
    try:
        analytics_service = get_analytics_service()
        sample_reports = analytics_service.get_sample_reports()
        
        return jsonify({
            'success': True,
            'data': {
                'sample_reports': sample_reports,
                'total_reports': len(sample_reports)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting sample reports: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get sample reports'
        }), 500


@meme_analytics_bp.route('/track/event', methods=['POST'])
@cross_origin()
def track_meme_event():
    """
    Track a meme analytics event
    
    Request Body:
        JSON with event data
        
    Returns:
        JSON with tracking result
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['event_type', 'user_id', 'meme_id', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        user_id = data['user_id']
        meme_id = data['meme_id']
        category = data['category']
        event_type = data['event_type']
        time_spent = data.get('time_spent_seconds', 0)
        session_id = data.get('session_id')
        source_page = data.get('source_page')
        device_type = data.get('device_type')
        user_agent = data.get('user_agent')
        ip_address = data.get('ip_address', request.remote_addr)
        
        # Track event based on type
        success = False
        if event_type == 'view':
            success = track_meme_view(
                user_id=user_id,
                meme_id=meme_id,
                category=category,
                time_spent=time_spent,
                session_id=session_id,
                source_page=source_page,
                device_type=device_type,
                user_agent=user_agent,
                ip_address=ip_address,
                db_session=get_db_session(),
                config=current_app.config
            )
        elif event_type == 'skip':
            success = track_meme_skip(
                user_id=user_id,
                meme_id=meme_id,
                category=category,
                time_spent=time_spent,
                session_id=session_id,
                source_page=source_page,
                device_type=device_type,
                user_agent=user_agent,
                ip_address=ip_address,
                db_session=get_db_session(),
                config=current_app.config
            )
        elif event_type == 'conversion':
            success = track_meme_conversion(
                user_id=user_id,
                meme_id=meme_id,
                category=category,
                time_spent=time_spent,
                session_id=session_id,
                source_page=source_page,
                device_type=device_type,
                user_agent=user_agent,
                ip_address=ip_address,
                db_session=get_db_session(),
                config=current_app.config
            )
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported event type: {event_type}'
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Event {event_type} tracked successfully',
                'event_id': str(uuid.uuid4())
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to track event'
            }), 500
        
    except Exception as e:
        logger.error(f"Error tracking meme event: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to track event'
        }), 500


@meme_analytics_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for meme analytics
    
    Returns:
        JSON with health status
    """
    try:
        analytics_service = get_analytics_service()
        
        # Check if analytics service is working
        start_date = datetime.now(timezone.utc) - timedelta(days=1)
        end_date = datetime.now(timezone.utc)
        
        metrics = analytics_service.get_meme_engagement_metrics(start_date, end_date)
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'service': 'meme_analytics',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics_available': True,
            'total_views_last_24h': metrics.total_views
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'service': 'meme_analytics',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error': str(e)
        }), 500


# Error handlers
@meme_analytics_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@meme_analytics_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
