"""
MINGUS Analytics API Routes
API endpoints for analytics tracking and reporting
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from ..services.analytics_service import (
    analytics_service, 
    AnalyticsEvent, 
    AnalyticsEventType,
    ConversionEvent, 
    ConversionGoal
)
from ..middleware.auth import require_auth, optional_auth
from ..middleware.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/track', methods=['POST'])
@cross_origin()
@rate_limit(100, 60)  # 100 requests per minute
def track_event():
    """
    Track an analytics event
    
    Expected payload:
    {
        "event_type": "page_view|user_action|conversion|assessment_selection|modal_interaction|form_submission|cta_click|scroll_depth|time_on_page|error|performance",
        "properties": {
            "key": "value",
            ...
        },
        "session_id": "optional_session_id",
        "user_id": "optional_user_id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'event_type' not in data:
            return jsonify({'error': 'Missing required field: event_type'}), 400
        
        # Validate event type
        try:
            event_type = AnalyticsEventType(data['event_type'])
        except ValueError:
            return jsonify({'error': f'Invalid event_type: {data["event_type"]}'}), 400
        
        # Create event
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            properties=data.get('properties', {}),
            source=data.get('source', 'web'),
            platform=data.get('platform', 'mingus')
        )
        
        # Track event
        success = analytics_service.track_event(event)
        
        if success:
            return jsonify({
                'success': True,
                'event_id': event.event_id,
                'message': 'Event tracked successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to track event'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/conversion', methods=['POST'])
@cross_origin()
@rate_limit(50, 60)  # 50 conversions per minute
def track_conversion():
    """
    Track a conversion event
    
    Expected payload:
    {
        "goal": "lead_generation|assessment_completion|subscription_signup|form_submission",
        "value": 20.0,
        "currency": "USD",
        "properties": {
            "key": "value",
            ...
        },
        "session_id": "optional_session_id",
        "user_id": "optional_user_id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'goal' not in data:
            return jsonify({'error': 'Missing required field: goal'}), 400
        
        if 'value' not in data:
            return jsonify({'error': 'Missing required field: value'}), 400
        
        # Validate goal
        try:
            goal = ConversionGoal(data['goal'])
        except ValueError:
            return jsonify({'error': f'Invalid goal: {data["goal"]}'}), 400
        
        # Create conversion
        conversion = ConversionEvent(
            conversion_id=str(uuid.uuid4()),
            goal=goal,
            value=float(data['value']),
            currency=data.get('currency', 'USD'),
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            properties=data.get('properties', {}),
            source=data.get('source', 'web')
        )
        
        # Track conversion
        success = analytics_service.track_conversion(conversion)
        
        if success:
            return jsonify({
                'success': True,
                'conversion_id': conversion.conversion_id,
                'message': 'Conversion tracked successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to track conversion'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking conversion: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/events', methods=['GET'])
@cross_origin()
@optional_auth
@rate_limit(100, 60)
def get_events():
    """
    Get analytics events with filters
    
    Query parameters:
    - event_type: Filter by event type
    - user_id: Filter by user ID
    - session_id: Filter by session ID
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - limit: Number of events to return (default: 100, max: 1000)
    """
    try:
        # Get query parameters
        event_type = request.args.get('event_type')
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = min(int(request.args.get('limit', 100)), 1000)
        
        # Parse dates
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Convert event_type string to enum
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AnalyticsEventType(event_type)
            except ValueError:
                return jsonify({'error': f'Invalid event_type: {event_type}'}), 400
        
        # Get events
        events = analytics_service.get_events(
            event_type=event_type_enum,
            user_id=user_id,
            session_id=session_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # Convert to JSON-serializable format
        events_data = []
        for event in events:
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'user_id': event.user_id,
                'session_id': event.session_id,
                'timestamp': event.timestamp.isoformat(),
                'properties': event.properties,
                'source': event.source,
                'platform': event.platform
            }
            events_data.append(event_data)
        
        return jsonify({
            'success': True,
            'events': events_data,
            'count': len(events_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/conversions', methods=['GET'])
@cross_origin()
@optional_auth
@rate_limit(100, 60)
def get_conversions():
    """
    Get conversion events with filters
    
    Query parameters:
    - goal: Filter by conversion goal
    - user_id: Filter by user ID
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - limit: Number of conversions to return (default: 100, max: 1000)
    """
    try:
        # Get query parameters
        goal = request.args.get('goal')
        user_id = request.args.get('user_id')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit = min(int(request.args.get('limit', 100)), 1000)
        
        # Parse dates
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Convert goal string to enum
        goal_enum = None
        if goal:
            try:
                goal_enum = ConversionGoal(goal)
            except ValueError:
                return jsonify({'error': f'Invalid goal: {goal}'}), 400
        
        # Get conversions
        conversions = analytics_service.get_conversions(
            goal=goal_enum,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        # Convert to JSON-serializable format
        conversions_data = []
        for conversion in conversions:
            conversion_data = {
                'conversion_id': conversion.conversion_id,
                'goal': conversion.goal.value,
                'value': conversion.value,
                'currency': conversion.currency,
                'user_id': conversion.user_id,
                'session_id': conversion.session_id,
                'timestamp': conversion.timestamp.isoformat(),
                'properties': conversion.properties,
                'source': conversion.source
            }
            conversions_data.append(conversion_data)
        
        return jsonify({
            'success': True,
            'conversions': conversions_data,
            'count': len(conversions_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conversions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/metrics', methods=['GET'])
@cross_origin()
@optional_auth
@rate_limit(50, 60)
def get_metrics():
    """
    Get analytics metrics
    
    Query parameters:
    - metric_name: Name of the metric to retrieve
    - start_date: Start date (ISO format)
    - end_date: End date (ISO format)
    - segment_id: Filter by user segment
    """
    try:
        # Get query parameters
        metric_name = request.args.get('metric_name')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        segment_id = request.args.get('segment_id')
        
        if not metric_name:
            return jsonify({'error': 'Missing required parameter: metric_name'}), 400
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'Missing required parameters: start_date, end_date'}), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get metrics
        metrics = analytics_service.get_metrics(
            metric_name=metric_name,
            start_date=start_date,
            end_date=end_date,
            segment_id=segment_id
        )
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'count': len(metrics)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/realtime', methods=['GET'])
@cross_origin()
@optional_auth
@rate_limit(30, 60)
def get_realtime_stats():
    """
    Get real-time analytics statistics
    """
    try:
        stats = analytics_service.get_real_time_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting real-time stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/user-segment/<user_id>', methods=['GET'])
@cross_origin()
@optional_auth
@rate_limit(100, 60)
def get_user_segment(user_id: str):
    """
    Get user segment for a specific user
    """
    try:
        segment_id = analytics_service.get_user_segment(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'segment_id': segment_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user segment: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/calculate-metrics', methods=['POST'])
@cross_origin()
@require_auth
@rate_limit(10, 60)  # Admin only
def calculate_metrics():
    """
    Calculate analytics metrics for a specific date
    
    Expected payload:
    {
        "date": "2024-01-01"  # Optional, defaults to today
    }
    """
    try:
        data = request.get_json() or {}
        date_str = data.get('date')
        
        if date_str:
            try:
                date = datetime.fromisoformat(date_str)
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        else:
            date = datetime.utcnow()
        
        # Calculate metrics
        analytics_service.calculate_metrics(date)
        
        return jsonify({
            'success': True,
            'message': f'Metrics calculated for {date.date()}',
            'date': date.date().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@analytics_bp.route('/health', methods=['GET'])
@cross_origin()
def analytics_health():
    """
    Analytics service health check
    """
    try:
        # Check Redis connection
        redis_healthy = analytics_service.redis_client is not None
        
        # Check database connection
        try:
            with analytics_service.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                db_healthy = True
        except Exception:
            db_healthy = False
        
        health_status = {
            'service': 'analytics',
            'status': 'healthy' if redis_healthy and db_healthy else 'unhealthy',
            'redis': 'connected' if redis_healthy else 'disconnected',
            'database': 'connected' if db_healthy else 'disconnected',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return jsonify({
            'service': 'analytics',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

# Register blueprint
def init_analytics_routes(app):
    """Initialize analytics routes"""
    app.register_blueprint(analytics_bp)
    logger.info("Analytics routes registered")
