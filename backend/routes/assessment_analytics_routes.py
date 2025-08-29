"""
Assessment Analytics API Routes

Comprehensive analytics endpoints for assessment system and landing page:
- Event tracking endpoints
- Dashboard metrics
- Conversion funnel analysis
- Lead quality metrics
- Performance monitoring
- Geographic analytics
- Real-time metrics
"""

from flask import Blueprint, request, jsonify, session, current_app
from flask_caching import Cache
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import logging
from typing import Dict, List, Optional, Any
from functools import wraps
import json

from ..models.assessment_analytics_models import (
    AssessmentAnalyticsEvent, AssessmentSession, ConversionFunnel,
    LeadQualityMetrics, RealTimeMetrics, PerformanceMetrics, GeographicAnalytics,
    AnalyticsEventType, ConversionStage, LeadQualityScore
)
from ..models.assessment_models import Assessment, UserAssessment
from ..models.user import User
from ..analytics.assessment_analytics_service import AssessmentAnalyticsService, AnalyticsEvent
from ..config.base import Config

# Initialize cache
cache = Cache()

logger = logging.getLogger(__name__)

assessment_analytics_bp = Blueprint('assessment_analytics', __name__, url_prefix='/api/analytics')

def get_db_session() -> Session:
    """Get database session"""
    return current_app.db.session

def require_auth():
    """Decorator to require authentication"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def require_admin():
    """Decorator to require admin privileges"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            db_session = get_db_session()
            user = db_session.query(User).filter(User.id == user_id).first()
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def extract_utm_params():
    """Extract UTM parameters from request"""
    return {
        'utm_source': request.args.get('utm_source'),
        'utm_medium': request.args.get('utm_medium'),
        'utm_campaign': request.args.get('utm_campaign'),
        'utm_term': request.args.get('utm_term'),
        'utm_content': request.args.get('utm_content')
    }

# Error Handlers
@assessment_analytics_bp.errorhandler(404)
def analytics_not_found(error):
    return jsonify({'error': 'Analytics data not found'}), 404

@assessment_analytics_bp.errorhandler(403)
def access_denied(error):
    return jsonify({'error': 'Access denied'}), 403

@assessment_analytics_bp.errorhandler(500)
def internal_error(error):
    db_session = get_db_session()
    db_session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# EVENT TRACKING ENDPOINTS
# ============================================================================

@assessment_analytics_bp.route('/track-event', methods=['POST'])
def track_event():
    """Central event tracking endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['event_type', 'session_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate event type
        try:
            event_type = AnalyticsEventType(data['event_type'])
        except ValueError:
            return jsonify({'error': f'Invalid event type: {data["event_type"]}'}), 400
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        # Create analytics event
        event = AnalyticsEvent(
            event_type=event_type,
            session_id=data['session_id'],
            user_id=session.get('user_id'),
            assessment_id=data.get('assessment_id'),
            assessment_type=data.get('assessment_type'),
            properties=data.get('properties', {}),
            source=data.get('source', 'web'),
            user_agent=request.headers.get('User-Agent'),
            ip_address=get_client_ip(),
            referrer=request.headers.get('Referer'),
            utm_source=data.get('utm_source'),
            utm_medium=data.get('utm_medium'),
            utm_campaign=data.get('utm_campaign'),
            utm_term=data.get('utm_term'),
            utm_content=data.get('utm_content'),
            page_load_time=data.get('page_load_time'),
            time_on_page=data.get('time_on_page')
        )
        
        # Track the event
        success = analytics_service.track_event(event)
        
        if success:
            return jsonify({
                'success': True,
                'event_id': str(uuid.uuid4()),
                'message': 'Event tracked successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to track event'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/track-assessment-landing', methods=['POST'])
def track_assessment_landing():
    """Track assessment landing page view"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        # Create landing view event
        event = AnalyticsEvent(
            event_type=AnalyticsEventType.ASSESSMENT_LANDING_VIEWED,
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=session.get('user_id'),
            assessment_type=data.get('assessment_type'),
            properties={
                'landing_page_url': request.url,
                'referrer': request.headers.get('Referer'),
                **extract_utm_params()
            },
            user_agent=request.headers.get('User-Agent'),
            ip_address=get_client_ip(),
            referrer=request.headers.get('Referer'),
            **extract_utm_params()
        )
        
        success = analytics_service.track_event(event)
        
        return jsonify({
            'success': success,
            'session_id': event.session_id,
            'message': 'Landing page view tracked' if success else 'Failed to track'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error tracking landing page: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/track-assessment-start', methods=['POST'])
def track_assessment_start():
    """Track assessment start"""
    try:
        data = request.get_json()
        if not data or 'assessment_type' not in data:
            return jsonify({'error': 'Assessment type required'}), 400
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        event = AnalyticsEvent(
            event_type=AnalyticsEventType.ASSESSMENT_STARTED,
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=session.get('user_id'),
            assessment_type=data['assessment_type'],
            properties={
                'assessment_id': data.get('assessment_id'),
                'estimated_duration': data.get('estimated_duration'),
                'questions_count': data.get('questions_count')
            },
            user_agent=request.headers.get('User-Agent'),
            ip_address=get_client_ip(),
            **extract_utm_params()
        )
        
        success = analytics_service.track_event(event)
        
        return jsonify({
            'success': success,
            'session_id': event.session_id,
            'message': 'Assessment start tracked' if success else 'Failed to track'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error tracking assessment start: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/track-question-answered', methods=['POST'])
def track_question_answered():
    """Track assessment question answered"""
    try:
        data = request.get_json()
        if not data or 'question_id' not in data:
            return jsonify({'error': 'Question ID required'}), 400
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        event = AnalyticsEvent(
            event_type=AnalyticsEventType.ASSESSMENT_QUESTION_ANSWERED,
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=session.get('user_id'),
            assessment_type=data.get('assessment_type'),
            properties={
                'question_id': data['question_id'],
                'question_number': data.get('question_number'),
                'time_spent': data.get('time_spent'),
                'answer_type': data.get('answer_type')
            },
            user_agent=request.headers.get('User-Agent'),
            ip_address=get_client_ip()
        )
        
        success = analytics_service.track_event(event)
        
        return jsonify({
            'success': success,
            'message': 'Question answered tracked' if success else 'Failed to track'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error tracking question answered: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/track-assessment-completed', methods=['POST'])
def track_assessment_completed():
    """Track assessment completion"""
    try:
        data = request.get_json()
        if not data or 'assessment_type' not in data:
            return jsonify({'error': 'Assessment type required'}), 400
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        event = AnalyticsEvent(
            event_type=AnalyticsEventType.ASSESSMENT_COMPLETED,
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=session.get('user_id'),
            assessment_type=data['assessment_type'],
            properties={
                'assessment_id': data.get('assessment_id'),
                'score': data.get('score'),
                'risk_level': data.get('risk_level'),
                'completion_time': data.get('completion_time'),
                'questions_answered': data.get('questions_answered'),
                'conversion_eligible': data.get('conversion_eligible', False)
            },
            user_agent=request.headers.get('User-Agent'),
            ip_address=get_client_ip()
        )
        
        success = analytics_service.track_event(event)
        
        return jsonify({
            'success': success,
            'message': 'Assessment completion tracked' if success else 'Failed to track'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error tracking assessment completion: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/track-email-captured', methods=['POST'])
def track_email_captured():
    """Track email capture for lead generation"""
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'error': 'Email required'}), 400
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        event = AnalyticsEvent(
            event_type=AnalyticsEventType.EMAIL_CAPTURED,
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=session.get('user_id'),
            assessment_type=data.get('assessment_type'),
            properties={
                'email': data['email'],
                'lead_source': data.get('lead_source', 'assessment'),
                'conversion_eligible': data.get('conversion_eligible', False)
            },
            user_agent=request.headers.get('User-Agent'),
            ip_address=get_client_ip(),
            **extract_utm_params()
        )
        
        success = analytics_service.track_event(event)
        
        return jsonify({
            'success': success,
            'message': 'Email capture tracked' if success else 'Failed to track'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error tracking email capture: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/track-conversion-modal', methods=['POST'])
def track_conversion_modal():
    """Track conversion modal opened"""
    try:
        data = request.get_json()
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        event = AnalyticsEvent(
            event_type=AnalyticsEventType.CONVERSION_MODAL_OPENED,
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=session.get('user_id'),
            assessment_type=data.get('assessment_type'),
            properties={
                'modal_type': data.get('modal_type', 'conversion'),
                'trigger_source': data.get('trigger_source'),
                'conversion_value': data.get('conversion_value')
            },
            user_agent=request.headers.get('User-Agent'),
            ip_address=get_client_ip()
        )
        
        success = analytics_service.track_event(event)
        
        return jsonify({
            'success': success,
            'message': 'Conversion modal tracked' if success else 'Failed to track'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error tracking conversion modal: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/track-payment-initiated', methods=['POST'])
def track_payment_initiated():
    """Track payment initiation"""
    try:
        data = request.get_json()
        if not data or 'payment_amount' not in data:
            return jsonify({'error': 'Payment amount required'}), 400
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        event = AnalyticsEvent(
            event_type=AnalyticsEventType.PAYMENT_INITIATED,
            session_id=data.get('session_id', str(uuid.uuid4())),
            user_id=session.get('user_id'),
            assessment_type=data.get('assessment_type'),
            properties={
                'payment_amount': data['payment_amount'],
                'payment_method': data.get('payment_method'),
                'currency': data.get('currency', 'USD'),
                'subscription_type': data.get('subscription_type')
            },
            user_agent=request.headers.get('User-Agent'),
            ip_address=get_client_ip()
        )
        
        success = analytics_service.track_event(event)
        
        return jsonify({
            'success': success,
            'message': 'Payment initiation tracked' if success else 'Failed to track'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error tracking payment initiation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# DASHBOARD AND ANALYTICS ENDPOINTS
# ============================================================================

@assessment_analytics_bp.route('/dashboard', methods=['GET'])
@require_admin
def get_analytics_dashboard():
    """Get real-time analytics dashboard metrics"""
    try:
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        # Get real-time metrics
        real_time_metrics = analytics_service.get_real_time_metrics()
        
        # Get conversion funnel (last 30 days)
        conversion_funnel = analytics_service.get_conversion_funnel(days=30)
        
        # Get lead quality metrics (last 30 days)
        lead_quality = analytics_service.get_lead_quality_metrics(days=30)
        
        # Get performance metrics (last 7 days)
        performance_metrics = analytics_service.get_performance_metrics(days=7)
        
        # Get geographic analytics (last 30 days)
        geographic_analytics = analytics_service.get_geographic_analytics(days=30)
        
        return jsonify({
            'real_time_metrics': real_time_metrics,
            'conversion_funnel': conversion_funnel,
            'lead_quality_metrics': lead_quality,
            'performance_metrics': performance_metrics,
            'geographic_analytics': geographic_analytics,
            'last_updated': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/conversion-funnel', methods=['GET'])
@require_admin
def get_conversion_funnel():
    """Get conversion funnel analysis"""
    try:
        assessment_type = request.args.get('assessment_type')
        days = request.args.get('days', 30, type=int)
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        funnel_data = analytics_service.get_conversion_funnel(
            assessment_type=assessment_type,
            days=days
        )
        
        return jsonify(funnel_data), 200
        
    except Exception as e:
        logger.error(f"Error getting conversion funnel: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/lead-quality', methods=['GET'])
@require_admin
def get_lead_quality_metrics():
    """Get lead quality scoring and segmentation metrics"""
    try:
        assessment_type = request.args.get('assessment_type')
        days = request.args.get('days', 30, type=int)
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        lead_quality_data = analytics_service.get_lead_quality_metrics(
            assessment_type=assessment_type,
            days=days
        )
        
        return jsonify(lead_quality_data), 200
        
    except Exception as e:
        logger.error(f"Error getting lead quality metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/performance', methods=['GET'])
@require_admin
def get_performance_metrics():
    """Get performance monitoring metrics"""
    try:
        days = request.args.get('days', 7, type=int)
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        performance_data = analytics_service.get_performance_metrics(days=days)
        
        return jsonify(performance_data), 200
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/geographic', methods=['GET'])
@require_admin
def get_geographic_analytics():
    """Get geographic distribution analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        geographic_data = analytics_service.get_geographic_analytics(days=days)
        
        return jsonify(geographic_data), 200
        
    except Exception as e:
        logger.error(f"Error getting geographic analytics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/real-time', methods=['GET'])
def get_real_time_metrics():
    """Get real-time metrics for social proof"""
    try:
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        real_time_data = analytics_service.get_real_time_metrics()
        
        return jsonify(real_time_data), 200
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# DATA EXPORT AND CLEANUP ENDPOINTS
# ============================================================================

@assessment_analytics_bp.route('/export', methods=['GET'])
@require_admin
def export_analytics_data():
    """Export analytics data for reporting"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        data_type = request.args.get('data_type', 'events')  # events, funnel, leads, performance
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start and end dates required'}), 400
        
        db_session = get_db_session()
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if data_type == 'events':
            data = db_session.query(AssessmentAnalyticsEvent).filter(
                AssessmentAnalyticsEvent.timestamp >= start_dt,
                AssessmentAnalyticsEvent.timestamp <= end_dt
            ).all()
            
            export_data = []
            for event in data:
                export_data.append({
                    'event_id': str(event.id),
                    'event_type': event.event_type,
                    'session_id': event.session_id,
                    'user_id': str(event.user_id) if event.user_id else None,
                    'assessment_type': event.assessment_type,
                    'timestamp': event.timestamp.isoformat(),
                    'properties': event.properties,
                    'source': event.source,
                    'device_type': event.device_type,
                    'browser': event.browser,
                    'os': event.os,
                    'country': event.country,
                    'region': event.region,
                    'city': event.city
                })
        
        elif data_type == 'funnel':
            data = db_session.query(ConversionFunnel).filter(
                ConversionFunnel.created_at >= start_dt,
                ConversionFunnel.created_at <= end_dt
            ).all()
            
            export_data = []
            for funnel in data:
                export_data.append({
                    'session_id': funnel.session_id,
                    'assessment_type': funnel.assessment_type,
                    'current_stage': funnel.current_stage,
                    'conversion_value': float(funnel.conversion_value) if funnel.conversion_value else None,
                    'lead_quality_score': funnel.lead_quality_score,
                    'risk_level': funnel.risk_level,
                    'assessment_score': funnel.assessment_score,
                    'created_at': funnel.created_at.isoformat()
                })
        
        else:
            return jsonify({'error': 'Invalid data type'}), 400
        
        return jsonify({
            'data_type': data_type,
            'start_date': start_date,
            'end_date': end_date,
            'total_records': len(export_data),
            'data': export_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@assessment_analytics_bp.route('/cleanup', methods=['POST'])
@require_admin
def cleanup_old_data():
    """Clean up old analytics data for privacy compliance"""
    try:
        data = request.get_json()
        days = data.get('days', 365) if data else 365
        
        db_session = get_db_session()
        analytics_service = AssessmentAnalyticsService(db_session, current_app.config)
        
        analytics_service.cleanup_old_data(days=days)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up data older than {days} days',
            'retention_days': days
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# HEALTH CHECK AND STATUS ENDPOINTS
# ============================================================================

@assessment_analytics_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for analytics system"""
    try:
        db_session = get_db_session()
        
        # Check database connectivity
        event_count = db_session.query(AssessmentAnalyticsEvent).count()
        
        return jsonify({
            'status': 'healthy',
            'database_connected': True,
            'total_events': event_count,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@assessment_analytics_bp.route('/status', methods=['GET'])
@require_admin
def get_system_status():
    """Get analytics system status and configuration"""
    try:
        db_session = get_db_session()
        
        # Get system statistics
        total_events = db_session.query(AssessmentAnalyticsEvent).count()
        total_sessions = db_session.query(AssessmentSession).count()
        total_funnels = db_session.query(ConversionFunnel).count()
        total_leads = db_session.query(LeadQualityMetrics).count()
        
        # Get recent activity
        recent_events = db_session.query(AssessmentAnalyticsEvent).filter(
            AssessmentAnalyticsEvent.timestamp >= datetime.now() - timedelta(hours=24)
        ).count()
        
        return jsonify({
            'system_status': 'operational',
            'statistics': {
                'total_events': total_events,
                'total_sessions': total_sessions,
                'total_funnels': total_funnels,
                'total_leads': total_leads,
                'recent_events_24h': recent_events
            },
            'configuration': {
                'privacy_mode': True,
                'retention_days': 365,
                'real_time_updates': True,
                'geoip_enabled': True
            },
            'last_updated': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': 'Internal server error'}), 500
