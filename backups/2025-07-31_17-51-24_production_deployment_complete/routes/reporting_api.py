"""
Reporting API Endpoints
Flask API endpoints for comprehensive reporting and analytics data
"""

from flask import Blueprint, request, jsonify, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, InternalServerError

from ..services.reporting_service import ReportingService
from ..database import get_flask_db_session, close_flask_db_session

logger = logging.getLogger(__name__)

# Create blueprint
reporting_api_bp = Blueprint('reporting_api', __name__)


def parse_date_param(date_str: str) -> datetime:
    """Parse date string parameter"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}, using default")
        return datetime.utcnow() - timedelta(days=30)


def handle_reporting_error(operation: str, error: Exception):
    """Centralized error handling for reporting operations"""
    if isinstance(error, SQLAlchemyError):
        logger.error(f"Database error during {operation}: {error}")
        return jsonify({
            'error': 'Database error occurred',
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat()
        }), 500
    elif isinstance(error, ValueError):
        logger.warning(f"Validation error during {operation}: {error}")
        return jsonify({
            'error': str(error),
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat()
        }), 400
    else:
        logger.error(f"Unexpected error during {operation}: {error}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@reporting_api_bp.route('/api/reporting/dashboard-summary', methods=['GET'])
@jwt_required()
def get_dashboard_summary():
    """
    Get comprehensive dashboard summary data
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    
    Returns:
    - Dashboard summary metrics
    - Channel breakdown
    - Message type breakdown
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested dashboard summary")
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = parse_date_param(start_date_str) if start_date_str else None
        end_date = parse_date_param(end_date_str) if end_date_str else None
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Get dashboard summary
        summary = reporting_service.get_dashboard_summary(start_date, end_date)
        
        logger.info(f"Dashboard summary generated successfully for user {current_user_id}")
        return jsonify(summary), 200
        
    except Exception as e:
        return handle_reporting_error("dashboard summary", e)


@reporting_api_bp.route('/api/reporting/performance-metrics', methods=['GET'])
@jwt_required()
def get_performance_metrics():
    """
    Get detailed performance metrics with aggregation
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - group_by: Grouping level (day, week, month, channel, message_type)
    
    Returns:
    - Performance metrics by grouping
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested performance metrics")
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        group_by = request.args.get('group_by', 'day')
        
        # Validate group_by parameter
        valid_groupings = ['day', 'week', 'month', 'channel', 'message_type']
        if group_by not in valid_groupings:
            raise ValueError(f'Invalid group_by parameter. Must be one of: {valid_groupings}')
        
        # Parse dates
        start_date = parse_date_param(start_date_str) if start_date_str else None
        end_date = parse_date_param(end_date_str) if end_date_str else None
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Get performance metrics
        metrics = reporting_service.get_performance_metrics(start_date, end_date, group_by)
        
        logger.info(f"Performance metrics generated successfully for user {current_user_id} with group_by={group_by}")
        return jsonify(metrics), 200
        
    except Exception as e:
        return handle_reporting_error("performance metrics", e)


@reporting_api_bp.route('/api/reporting/time-series', methods=['GET'])
@jwt_required()
def get_time_series_data():
    """
    Get time-series data for trend analysis
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - metric: Metric to analyze (messages, delivery_rate, open_rate, cost, actions)
    - interval: Time interval (hour, day, week, month)
    
    Returns:
    - Time-series data points
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested time series data")
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        metric = request.args.get('metric', 'messages')
        interval = request.args.get('interval', 'day')
        
        # Validate parameters
        valid_metrics = ['messages', 'delivery_rate', 'open_rate', 'click_rate', 'cost', 'actions']
        valid_intervals = ['hour', 'day', 'week', 'month']
        
        if metric not in valid_metrics:
            raise ValueError(f'Invalid metric parameter. Must be one of: {valid_metrics}')
        
        if interval not in valid_intervals:
            raise ValueError(f'Invalid interval parameter. Must be one of: {valid_intervals}')
        
        # Parse dates
        start_date = parse_date_param(start_date_str) if start_date_str else None
        end_date = parse_date_param(end_date_str) if end_date_str else None
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Get time series data
        time_series = reporting_service.get_time_series_data(start_date, end_date, metric, interval)
        
        logger.info(f"Time series data generated successfully for user {current_user_id} with metric={metric}, interval={interval}")
        return jsonify({
            'metric': metric,
            'interval': interval,
            'data': time_series
        }), 200
        
    except Exception as e:
        return handle_reporting_error("time series data", e)


@reporting_api_bp.route('/api/reporting/trend-analysis', methods=['GET'])
@jwt_required()
def get_trend_analysis():
    """
    Get comprehensive trend analysis
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    
    Returns:
    - Trend analysis data
    - Comparison between periods
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested trend analysis")
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = parse_date_param(start_date_str) if start_date_str else None
        end_date = parse_date_param(end_date_str) if end_date_str else None
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Get trend analysis
        trends = reporting_service.get_trend_analysis(start_date, end_date)
        
        logger.info(f"Trend analysis generated successfully for user {current_user_id}")
        return jsonify(trends), 200
        
    except Exception as e:
        return handle_reporting_error("trend analysis", e)


@reporting_api_bp.route('/api/reporting/user-segments', methods=['GET'])
@jwt_required()
def get_user_segments():
    """
    Get user segmentation analysis
    
    Returns:
    - User segment data
    - Channel preferences by segment
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested user segments")
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Get user segments
        segments = reporting_service.get_user_segments()
        
        logger.info(f"User segments generated successfully for user {current_user_id}")
        return jsonify(segments), 200
        
    except Exception as e:
        return handle_reporting_error("user segments", e)


@reporting_api_bp.route('/api/reporting/segment-performance/<segment>', methods=['GET'])
@jwt_required()
def get_segment_performance(segment):
    """
    Get performance metrics for specific user segment
    
    Path Parameters:
    - segment: Segment to analyze (high_engagement, medium_engagement, low_engagement, inactive)
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    
    Returns:
    - Segment performance data
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested segment performance for {segment}")
        
        # Validate segment parameter
        valid_segments = ['high_engagement', 'medium_engagement', 'low_engagement', 'inactive']
        if segment not in valid_segments:
            raise ValueError(f'Invalid segment parameter. Must be one of: {valid_segments}')
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = parse_date_param(start_date_str) if start_date_str else None
        end_date = parse_date_param(end_date_str) if end_date_str else None
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Get segment performance
        performance = reporting_service.get_segment_performance(segment, start_date, end_date)
        
        logger.info(f"Segment performance generated successfully for user {current_user_id} for segment {segment}")
        return jsonify(performance), 200
        
    except Exception as e:
        return handle_reporting_error(f"segment performance for {segment}", e)


@reporting_api_bp.route('/api/reporting/correlation-analysis', methods=['GET'])
@jwt_required()
def get_correlation_analysis():
    """
    Get correlation analysis between different metrics
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    
    Returns:
    - Correlation analysis data
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested correlation analysis")
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = parse_date_param(start_date_str) if start_date_str else None
        end_date = parse_date_param(end_date_str) if end_date_str else None
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Get correlation analysis
        correlations = reporting_service.get_correlation_analysis(start_date, end_date)
        
        logger.info(f"Correlation analysis generated successfully for user {current_user_id}")
        return jsonify(correlations), 200
        
    except Exception as e:
        return handle_reporting_error("correlation analysis", e)


@reporting_api_bp.route('/api/reporting/predictive-insights', methods=['GET'])
@jwt_required()
def get_predictive_insights():
    """
    Get predictive insights based on historical data
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    
    Returns:
    - Predictive insights data
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested predictive insights")
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = parse_date_param(start_date_str) if start_date_str else None
        end_date = parse_date_param(end_date_str) if end_date_str else None
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Get predictive insights
        insights = reporting_service.get_predictive_insights(start_date, end_date)
        
        logger.info(f"Predictive insights generated successfully for user {current_user_id}")
        return jsonify(insights), 200
        
    except Exception as e:
        return handle_reporting_error("predictive insights", e)


@reporting_api_bp.route('/api/reporting/comprehensive-report', methods=['GET'])
@jwt_required()
def get_comprehensive_report():
    """
    Get comprehensive report with all analytics data
    
    Query Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - include_segments: Include user segments (true/false)
    - include_predictions: Include predictive insights (true/false)
    
    Returns:
    - Comprehensive report with all analytics data
    """
    try:
        # Get current user for logging
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} requested comprehensive report")
        
        # Get query parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        include_segments = request.args.get('include_segments', 'true').lower() == 'true'
        include_predictions = request.args.get('include_predictions', 'true').lower() == 'true'
        
        # Parse dates
        start_date = parse_date_param(start_date_str) if start_date_str else None
        end_date = parse_date_param(end_date_str) if end_date_str else None
        
        # Get reporting service with Flask session management
        reporting_service = ReportingService()
        
        # Build comprehensive report
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            }
        }
        
        # Get dashboard summary
        report['dashboard_summary'] = reporting_service.get_dashboard_summary(start_date, end_date)
        
        # Get performance metrics by day
        report['performance_metrics'] = reporting_service.get_performance_metrics(start_date, end_date, 'day')
        
        # Get trend analysis
        report['trend_analysis'] = reporting_service.get_trend_analysis(start_date, end_date)
        
        # Get time series data for key metrics
        report['time_series'] = {
            'messages': reporting_service.get_time_series_data(start_date, end_date, 'messages', 'day'),
            'delivery_rate': reporting_service.get_time_series_data(start_date, end_date, 'delivery_rate', 'day'),
            'open_rate': reporting_service.get_time_series_data(start_date, end_date, 'open_rate', 'day'),
            'cost': reporting_service.get_time_series_data(start_date, end_date, 'cost', 'day')
        }
        
        # Get correlation analysis
        report['correlation_analysis'] = reporting_service.get_correlation_analysis(start_date, end_date)
        
        # Include user segments if requested
        if include_segments:
            report['user_segments'] = reporting_service.get_user_segments()
            
            # Get performance for each segment
            segments = ['high_engagement', 'medium_engagement', 'low_engagement']
            report['segment_performance'] = {}
            for segment in segments:
                try:
                    report['segment_performance'][segment] = reporting_service.get_segment_performance(
                        segment, start_date, end_date
                    )
                except Exception as e:
                    logger.warning(f"Could not get performance for segment {segment}: {e}")
        
        # Include predictive insights if requested
        if include_predictions:
            report['predictive_insights'] = reporting_service.get_predictive_insights(start_date, end_date)
        
        logger.info(f"Comprehensive report generated successfully for user {current_user_id}")
        return jsonify(report), 200
        
    except Exception as e:
        return handle_reporting_error("comprehensive report", e)


@reporting_api_bp.route('/api/reporting/health', methods=['GET'])
def get_reporting_health():
    """
    Health check endpoint for reporting API
    
    Returns:
    - Health status of reporting service
    """
    try:
        # Test basic functionality
        reporting_service = ReportingService()
        
        # Try to get a simple dashboard summary
        summary = reporting_service.get_dashboard_summary()
        
        return jsonify({
            'status': 'healthy',
            'service': 'reporting_api',
            'timestamp': datetime.utcnow().isoformat(),
            'test_summary': {
                'total_messages': summary.get('summary', {}).get('total_messages', 0),
                'period': summary.get('period', {})
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Reporting health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'reporting_api',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# Flask error handlers
@reporting_api_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    logger.warning(f"Bad request in reporting API: {error}")
    return jsonify({
        "error": "Bad request",
        "message": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }), 400


@reporting_api_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    logger.warning(f"Unauthorized access attempt in reporting API: {error}")
    return jsonify({
        "error": "Unauthorized",
        "message": "Authentication required",
        "timestamp": datetime.utcnow().isoformat()
    }), 401


@reporting_api_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    logger.warning(f"Resource not found in reporting API: {error}")
    return jsonify({
        "error": "Not found",
        "message": "The requested resource was not found",
        "timestamp": datetime.utcnow().isoformat()
    }), 404


@reporting_api_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error in reporting API: {error}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.utcnow().isoformat()
    }), 500


# Flask teardown handler for session cleanup
@reporting_api_bp.teardown_app_request
def cleanup_session(error):
    """Clean up database session after each request"""
    if error is not None:
        logger.error(f"Request error in reporting API: {error}")
    
    # Close Flask database session
    close_flask_db_session(error) 