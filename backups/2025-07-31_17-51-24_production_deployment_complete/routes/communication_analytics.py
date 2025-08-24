"""
Communication Analytics API Routes
Provides endpoints for analytics data and reporting
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from ..services.analytics_service import AnalyticsService
from ..models.communication_analytics import (
    ChannelType, UserSegment, FinancialOutcome, MetricType
)
from ..database import get_db_session
from ..models.communication_analytics import CommunicationMetrics

logger = logging.getLogger(__name__)

# Create blueprint
communication_analytics_bp = Blueprint('communication_analytics', __name__)


# Schema definitions
class RealTimeMetricsRequestSchema(Schema):
    """Schema for real-time metrics request"""
    channel = fields.Str(validate=lambda x: x in [c.value for c in ChannelType], required=False)
    alert_type = fields.Str(required=False)
    time_period = fields.Str(validate=lambda x: x in ["last_24_hours", "last_7_days", "last_30_days"], required=False)


class ChannelComparisonRequestSchema(Schema):
    """Schema for channel comparison request"""
    alert_type = fields.Str(required=False)
    user_segment = fields.Str(validate=lambda x: x in [s.value for s in UserSegment], required=False)
    time_period = fields.Str(validate=lambda x: x in ["last_7_days", "last_30_days"], required=False)


class CostAnalysisRequestSchema(Schema):
    """Schema for cost analysis request"""
    channel = fields.Str(validate=lambda x: x in [c.value for c in ChannelType], required=False)
    time_period = fields.Str(validate=lambda x: x in ["last_30_days", "last_90_days"], required=False)


class TrackMetricsRequestSchema(Schema):
    """Schema for tracking communication metrics"""
    channel = fields.Str(validate=lambda x: x in [c.value for c in ChannelType], required=True)
    alert_type = fields.Str(required=True)
    user_segment = fields.Str(validate=lambda x: x in [s.value for s in UserSegment], required=False)
    total_sent = fields.Int(required=True, validate=lambda x: x >= 0)
    total_delivered = fields.Int(required=True, validate=lambda x: x >= 0)
    total_opened = fields.Int(required=True, validate=lambda x: x >= 0)
    total_clicked = fields.Int(required=True, validate=lambda x: x >= 0)
    total_responded = fields.Int(required=True, validate=lambda x: x >= 0)
    total_converted = fields.Int(required=True, validate=lambda x: x >= 0)
    total_cost = fields.Decimal(required=True, validate=lambda x: x >= 0)


class TrackEngagementRequestSchema(Schema):
    """Schema for tracking user engagement"""
    user_id = fields.Int(required=True)
    channel = fields.Str(validate=lambda x: x in [c.value for c in ChannelType], required=True)
    alert_type = fields.Str(required=True)
    engaged = fields.Bool(required=True)
    response_time_minutes = fields.Float(required=False, validate=lambda x: x >= 0 if x else True)


class TrackFinancialImpactRequestSchema(Schema):
    """Schema for tracking financial impact"""
    user_id = fields.Int(required=True)
    outcome_type = fields.Str(validate=lambda x: x in [o.value for o in FinancialOutcome], required=True)
    outcome_value = fields.Decimal(required=True)
    communication_channel = fields.Str(validate=lambda x: x in [c.value for c in ChannelType], required=False)
    alert_type = fields.Str(required=False)
    message_id = fields.Str(required=False)
    attributed_to_communication = fields.Bool(required=False)


class TrackCostsRequestSchema(Schema):
    """Schema for tracking costs"""
    channel = fields.Str(validate=lambda x: x in [c.value for c in ChannelType], required=True)
    alert_type = fields.Str(required=True)
    user_segment = fields.Str(validate=lambda x: x in [s.value for s in UserSegment], required=False)
    period_type = fields.Str(validate=lambda x: x in ["daily", "weekly", "monthly"], required=True)
    sms_cost = fields.Decimal(required=True, validate=lambda x: x >= 0)
    email_cost = fields.Decimal(required=True, validate=lambda x: x >= 0)
    push_cost = fields.Decimal(required=True, validate=lambda x: x >= 0)
    in_app_cost = fields.Decimal(required=True, validate=lambda x: x >= 0)
    twilio_cost = fields.Decimal(required=True, validate=lambda x: x >= 0)
    resend_cost = fields.Decimal(required=True, validate=lambda x: x >= 0)
    total_messages = fields.Int(required=True, validate=lambda x: x >= 0)


# API Routes
@communication_analytics_bp.route('/metrics/real-time', methods=['GET'])
@jwt_required()
def get_real_time_metrics():
    """
    Get real-time communication metrics
    
    Query Parameters:
        channel: Communication channel (sms, email, push, in_app)
        alert_type: Type of alert/message
        time_period: Time period (last_24_hours, last_7_days, last_30_days)
    
    Returns:
        JSON with real-time metrics data
    """
    try:
        # Validate request
        schema = RealTimeMetricsRequestSchema()
        errors = schema.validate(request.args)
        if errors:
            return jsonify({"error": "Validation error", "details": errors}), 400
        
        # Get parameters
        channel = request.args.get('channel')
        alert_type = request.args.get('alert_type')
        time_period = request.args.get('time_period', 'last_24_hours')
        
        # Convert channel string to enum if provided
        channel_enum = None
        if channel:
            channel_enum = ChannelType(channel)
        
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Get real-time metrics
        metrics = analytics_service.get_real_time_metrics(
            channel=channel_enum,
            alert_type=alert_type,
            time_period=time_period
        )
        
        return jsonify({
            "success": True,
            "data": metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        return jsonify({"error": "Internal server error"}), 500


@communication_analytics_bp.route('/metrics/channel-comparison', methods=['GET'])
@jwt_required()
def get_channel_comparison():
    """
    Get SMS vs Email performance comparison
    
    Query Parameters:
        alert_type: Type of alert/message
        user_segment: User segment
        time_period: Time period (last_7_days, last_30_days)
    
    Returns:
        JSON with channel comparison data
    """
    try:
        # Validate request
        schema = ChannelComparisonRequestSchema()
        errors = schema.validate(request.args)
        if errors:
            return jsonify({"error": "Validation error", "details": errors}), 400
        
        # Get parameters
        alert_type = request.args.get('alert_type')
        user_segment = request.args.get('user_segment')
        time_period = request.args.get('time_period', 'last_7_days')
        
        # Convert user_segment string to enum if provided
        user_segment_enum = None
        if user_segment:
            user_segment_enum = UserSegment(user_segment)
        
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Get channel comparison
        comparison = analytics_service.get_channel_comparison(
            alert_type=alert_type,
            user_segment=user_segment_enum,
            time_period=time_period
        )
        
        return jsonify({
            "success": True,
            "data": comparison
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting channel comparison: {e}")
        return jsonify({"error": "Internal server error"}), 500


@communication_analytics_bp.route('/costs/analysis', methods=['GET'])
@jwt_required()
def get_cost_analysis():
    """
    Get cost analysis for budget monitoring
    
    Query Parameters:
        channel: Communication channel (sms, email, push, in_app)
        time_period: Time period (last_30_days, last_90_days)
    
    Returns:
        JSON with cost analysis data
    """
    try:
        # Validate request
        schema = CostAnalysisRequestSchema()
        errors = schema.validate(request.args)
        if errors:
            return jsonify({"error": "Validation error", "details": errors}), 400
        
        # Get parameters
        channel = request.args.get('channel')
        time_period = request.args.get('time_period', 'last_30_days')
        
        # Convert channel string to enum if provided
        channel_enum = None
        if channel:
            channel_enum = ChannelType(channel)
        
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Get cost analysis
        analysis = analytics_service.get_cost_analysis(
            channel=channel_enum,
            time_period=time_period
        )
        
        return jsonify({
            "success": True,
            "data": analysis
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cost analysis: {e}")
        return jsonify({"error": "Internal server error"}), 500


@communication_analytics_bp.route('/metrics/track', methods=['POST'])
@jwt_required()
def track_communication_metrics():
    """
    Track communication metrics
    
    Request Body:
        JSON with communication metrics data
    
    Returns:
        JSON with tracking confirmation
    """
    try:
        # Validate request
        schema = TrackMetricsRequestSchema()
        errors = schema.validate(request.json)
        if errors:
            return jsonify({"error": "Validation error", "details": errors}), 400
        
        data = request.json
        
        # Convert string to enum
        channel = ChannelType(data['channel'])
        user_segment = None
        if data.get('user_segment'):
            user_segment = UserSegment(data['user_segment'])
        
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Track metrics
        metrics = analytics_service.track_communication_metrics(
            channel=channel,
            alert_type=data['alert_type'],
            user_segment=user_segment,
            total_sent=data['total_sent'],
            total_delivered=data['total_delivered'],
            total_opened=data['total_opened'],
            total_clicked=data['total_clicked'],
            total_responded=data['total_responded'],
            total_converted=data['total_converted'],
            total_cost=Decimal(str(data['total_cost']))
        )
        
        return jsonify({
            "success": True,
            "message": "Communication metrics tracked successfully",
            "data": {
                "id": metrics.id,
                "channel": metrics.channel.value,
                "alert_type": metrics.alert_type,
                "delivery_rate": metrics.delivery_rate,
                "engagement_rate": metrics.engagement_rate
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error tracking communication metrics: {e}")
        return jsonify({"error": "Internal server error"}), 500


@communication_analytics_bp.route('/engagement/track', methods=['POST'])
@jwt_required()
def track_user_engagement():
    """
    Track user engagement
    
    Request Body:
        JSON with user engagement data
    
    Returns:
        JSON with tracking confirmation
    """
    try:
        # Validate request
        schema = TrackEngagementRequestSchema()
        errors = schema.validate(request.json)
        if errors:
            return jsonify({"error": "Validation error", "details": errors}), 400
        
        data = request.json
        
        # Convert string to enum
        channel = ChannelType(data['channel'])
        
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Track engagement
        engagement = analytics_service.update_user_engagement(
            user_id=data['user_id'],
            channel=channel,
            alert_type=data['alert_type'],
            engaged=data['engaged'],
            response_time_minutes=data.get('response_time_minutes')
        )
        
        return jsonify({
            "success": True,
            "message": "User engagement tracked successfully",
            "data": {
                "id": engagement.id,
                "user_id": engagement.user_id,
                "engagement_score": engagement.engagement_score,
                "engagement_trend": engagement.engagement_trend
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error tracking user engagement: {e}")
        return jsonify({"error": "Internal server error"}), 500


@communication_analytics_bp.route('/financial-impact/track', methods=['POST'])
@jwt_required()
def track_financial_impact():
    """
    Track financial impact correlation
    
    Request Body:
        JSON with financial impact data
    
    Returns:
        JSON with tracking confirmation
    """
    try:
        # Validate request
        schema = TrackFinancialImpactRequestSchema()
        errors = schema.validate(request.json)
        if errors:
            return jsonify({"error": "Validation error", "details": errors}), 400
        
        data = request.json
        
        # Convert strings to enums
        outcome_type = FinancialOutcome(data['outcome_type'])
        communication_channel = None
        if data.get('communication_channel'):
            communication_channel = ChannelType(data['communication_channel'])
        
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Track financial impact
        impact = analytics_service.track_financial_impact(
            user_id=data['user_id'],
            outcome_type=outcome_type,
            outcome_value=Decimal(str(data['outcome_value'])),
            communication_channel=communication_channel,
            alert_type=data.get('alert_type'),
            message_id=data.get('message_id'),
            attributed_to_communication=data.get('attributed_to_communication', False)
        )
        
        return jsonify({
            "success": True,
            "message": "Financial impact tracked successfully",
            "data": {
                "id": impact.id,
                "user_id": impact.user_id,
                "outcome_type": impact.outcome_type.value,
                "outcome_value": float(impact.outcome_value),
                "attribution_confidence": impact.attribution_confidence
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error tracking financial impact: {e}")
        return jsonify({"error": "Internal server error"}), 500


@communication_analytics_bp.route('/costs/track', methods=['POST'])
@jwt_required()
def track_costs():
    """
    Track communication costs
    
    Request Body:
        JSON with cost data
    
    Returns:
        JSON with tracking confirmation
    """
    try:
        # Validate request
        schema = TrackCostsRequestSchema()
        errors = schema.validate(request.json)
        if errors:
            return jsonify({"error": "Validation error", "details": errors}), 400
        
        data = request.json
        
        # Convert string to enum
        channel = ChannelType(data['channel'])
        user_segment = None
        if data.get('user_segment'):
            user_segment = UserSegment(data['user_segment'])
        
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Track costs
        cost_tracking = analytics_service.track_costs(
            channel=channel,
            alert_type=data['alert_type'],
            user_segment=user_segment,
            period_type=data['period_type'],
            sms_cost=Decimal(str(data['sms_cost'])),
            email_cost=Decimal(str(data['email_cost'])),
            push_cost=Decimal(str(data['push_cost'])),
            in_app_cost=Decimal(str(data['in_app_cost'])),
            twilio_cost=Decimal(str(data['twilio_cost'])),
            resend_cost=Decimal(str(data['resend_cost'])),
            total_messages=data['total_messages']
        )
        
        return jsonify({
            "success": True,
            "message": "Costs tracked successfully",
            "data": {
                "id": cost_tracking.id,
                "channel": cost_tracking.channel.value,
                "total_cost": float(cost_tracking.total_cost),
                "cost_per_message": float(cost_tracking.cost_per_message),
                "budget_utilization": cost_tracking.budget_utilization,
                "cost_efficiency_score": cost_tracking.cost_efficiency_score
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error tracking costs: {e}")
        return jsonify({"error": "Internal server error"}), 500


@communication_analytics_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
def get_analytics_dashboard():
    """
    Get comprehensive analytics dashboard data
    
    Returns:
        JSON with dashboard summary data
    """
    try:
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Get various analytics data
        real_time_metrics = analytics_service.get_real_time_metrics(time_period="last_24_hours")
        channel_comparison = analytics_service.get_channel_comparison(time_period="last_7_days")
        cost_analysis = analytics_service.get_cost_analysis(time_period="last_30_days")
        
        # Create dashboard summary
        dashboard_data = {
            "real_time_metrics": real_time_metrics,
            "channel_comparison": channel_comparison,
            "cost_analysis": cost_analysis,
            "summary": {
                "total_messages_today": real_time_metrics.get("total_sent", 0),
                "avg_delivery_rate": real_time_metrics.get("delivery_rate", 0.0),
                "avg_engagement_rate": real_time_metrics.get("response_rate", 0.0),
                "total_cost_month": cost_analysis.get("total_cost", 0.0),
                "best_performing_channel": channel_comparison.get("winner"),
                "cost_per_message": real_time_metrics.get("cost_per_message", 0.0)
            }
        }
        
        return jsonify({
            "success": True,
            "data": dashboard_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        return jsonify({"error": "Internal server error"}), 500


@communication_analytics_bp.route('/health', methods=['GET'])
def analytics_health_check():
    """
    Health check endpoint for analytics system
    
    Returns:
        JSON with health status
    """
    try:
        # Get analytics service
        analytics_service = AnalyticsService()
        
        # Test basic functionality
        test_metrics = analytics_service.get_real_time_metrics(time_period="last_24_hours")
        
        return jsonify({
            "status": "healthy",
            "service": "communication_analytics",
            "timestamp": datetime.utcnow().isoformat(),
            "test_metrics_available": bool(test_metrics)
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "service": "communication_analytics",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500 


@communication_analytics_bp.route('/api/analytics/communication-summary', methods=['GET'])
@jwt_required()
def get_communication_summary():
    """
    Get comprehensive communication analytics summary
    
    Query Parameters:
    - start_date: Start date for analysis (YYYY-MM-DD)
    - end_date: End date for analysis (YYYY-MM-DD)
    - user_id: Filter by specific user (optional)
    - channel: Filter by channel (sms/email)
    - message_type: Filter by message type
    
    Returns:
    - Total messages sent
    - Delivery rates by channel
    - Open/click rates for emails
    - User engagement metrics
    - Cost analysis
    """
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id', type=int)
        channel = request.args.get('channel')
        message_type = request.args.get('message_type')
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get database session
        db = get_db_session()
        
        # Build base query
        query = db.query(CommunicationMetrics)
        
        # Apply filters
        if start_dt:
            query = query.filter(CommunicationMetrics.sent_at >= start_dt)
        if end_dt:
            query = query.filter(CommunicationMetrics.sent_at <= end_dt)
        if user_id:
            query = query.filter(CommunicationMetrics.user_id == user_id)
        if channel:
            query = query.filter(CommunicationMetrics.channel == channel)
        if message_type:
            query = query.filter(CommunicationMetrics.message_type == message_type)
        
        # Get all metrics
        metrics = query.all()
        
        if not metrics:
            return jsonify({
                'summary': {
                    'total_messages': 0,
                    'delivery_rate': 0.0,
                    'open_rate': 0.0,
                    'click_rate': 0.0,
                    'total_cost': 0.0,
                    'average_cost_per_message': 0.0
                },
                'by_channel': {},
                'by_message_type': {},
                'time_period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }), 200
        
        # Calculate summary statistics
        total_messages = len(metrics)
        delivered_messages = len([m for m in metrics if m.status == 'delivered'])
        opened_messages = len([m for m in metrics if m.opened_at is not None])
        clicked_messages = len([m for m in metrics if m.clicked_at is not None])
        total_cost = sum(m.cost or 0 for m in metrics)
        
        delivery_rate = (delivered_messages / total_messages * 100) if total_messages > 0 else 0
        open_rate = (opened_messages / total_messages * 100) if total_messages > 0 else 0
        click_rate = (clicked_messages / total_messages * 100) if total_messages > 0 else 0
        avg_cost_per_message = total_cost / total_messages if total_messages > 0 else 0
        
        # Group by channel
        by_channel = {}
        for m in metrics:
            if m.channel not in by_channel:
                by_channel[m.channel] = {
                    'total': 0,
                    'delivered': 0,
                    'opened': 0,
                    'clicked': 0,
                    'cost': 0.0
                }
            
            by_channel[m.channel]['total'] += 1
            if m.status == 'delivered':
                by_channel[m.channel]['delivered'] += 1
            if m.opened_at:
                by_channel[m.channel]['opened'] += 1
            if m.clicked_at:
                by_channel[m.channel]['clicked'] += 1
            by_channel[m.channel]['cost'] += m.cost or 0
        
        # Calculate rates for each channel
        for channel_data in by_channel.values():
            total = channel_data['total']
            channel_data['delivery_rate'] = (channel_data['delivered'] / total * 100) if total > 0 else 0
            channel_data['open_rate'] = (channel_data['opened'] / total * 100) if total > 0 else 0
            channel_data['click_rate'] = (channel_data['clicked'] / total * 100) if total > 0 else 0
            channel_data['avg_cost'] = channel_data['cost'] / total if total > 0 else 0
        
        # Group by message type
        by_message_type = {}
        for m in metrics:
            if m.message_type not in by_message_type:
                by_message_type[m.message_type] = {
                    'total': 0,
                    'delivered': 0,
                    'opened': 0,
                    'clicked': 0,
                    'cost': 0.0
                }
            
            by_message_type[m.message_type]['total'] += 1
            if m.status == 'delivered':
                by_message_type[m.message_type]['delivered'] += 1
            if m.opened_at:
                by_message_type[m.message_type]['opened'] += 1
            if m.clicked_at:
                by_message_type[m.message_type]['clicked'] += 1
            by_message_type[m.message_type]['cost'] += m.cost or 0
        
        # Calculate rates for each message type
        for msg_type_data in by_message_type.values():
            total = msg_type_data['total']
            msg_type_data['delivery_rate'] = (msg_type_data['delivered'] / total * 100) if total > 0 else 0
            msg_type_data['open_rate'] = (msg_type_data['opened'] / total * 100) if total > 0 else 0
            msg_type_data['click_rate'] = (msg_type_data['clicked'] / total * 100) if total > 0 else 0
            msg_type_data['avg_cost'] = msg_type_data['cost'] / total if total > 0 else 0
        
        return jsonify({
            'summary': {
                'total_messages': total_messages,
                'delivery_rate': round(delivery_rate, 2),
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'total_cost': round(total_cost, 2),
                'average_cost_per_message': round(avg_cost_per_message, 4)
            },
            'by_channel': by_channel,
            'by_message_type': by_message_type,
            'time_period': {
                'start_date': start_date,
                'end_date': end_date
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting communication summary: {e}")
        return jsonify({'error': 'Failed to get communication summary'}), 500


@communication_analytics_bp.route('/api/analytics/user-engagement/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_engagement(user_id):
    """
    Get detailed user engagement analytics
    
    Path Parameters:
    - user_id: User ID to analyze
    
    Query Parameters:
    - start_date: Start date for analysis (YYYY-MM-DD)
    - end_date: End date for analysis (YYYY-MM-DD)
    - limit: Number of recent messages to include (default: 50)
    
    Returns:
    - User engagement metrics
    - Communication history
    - Response patterns
    - Channel preferences
    """
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get database session
        db = get_db_session()
        
        # Build base query for user
        query = db.query(CommunicationMetrics).filter(CommunicationMetrics.user_id == user_id)
        
        # Apply date filters
        if start_dt:
            query = query.filter(CommunicationMetrics.sent_at >= start_dt)
        if end_dt:
            query = query.filter(CommunicationMetrics.sent_at <= end_dt)
        
        # Get all user metrics
        all_metrics = query.all()
        
        if not all_metrics:
            return jsonify({
                'user_id': user_id,
                'engagement_summary': {
                    'total_messages_received': 0,
                    'delivery_rate': 0.0,
                    'open_rate': 0.0,
                    'click_rate': 0.0,
                    'response_rate': 0.0,
                    'average_response_time': None
                },
                'channel_preferences': {},
                'message_type_engagement': {},
                'recent_communications': [],
                'response_patterns': {}
            }), 200
        
        # Calculate engagement metrics
        total_messages = len(all_metrics)
        delivered_messages = len([m for m in all_metrics if m.status == 'delivered'])
        opened_messages = len([m for m in all_metrics if m.opened_at is not None])
        clicked_messages = len([m for m in all_metrics if m.clicked_at is not None])
        action_messages = len([m for m in all_metrics if m.action_taken is not None])
        
        delivery_rate = (delivered_messages / total_messages * 100) if total_messages > 0 else 0
        open_rate = (opened_messages / total_messages * 100) if total_messages > 0 else 0
        click_rate = (clicked_messages / total_messages * 100) if total_messages > 0 else 0
        response_rate = (action_messages / total_messages * 100) if total_messages > 0 else 0
        
        # Calculate average response time
        response_times = []
        for m in all_metrics:
            if m.opened_at and m.sent_at:
                response_time = (m.opened_at - m.sent_at).total_seconds() / 3600  # hours
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        # Channel preferences
        channel_preferences = {}
        for m in all_metrics:
            if m.channel not in channel_preferences:
                channel_preferences[m.channel] = {
                    'total': 0,
                    'delivered': 0,
                    'opened': 0,
                    'clicked': 0,
                    'actions': 0
                }
            
            channel_preferences[m.channel]['total'] += 1
            if m.status == 'delivered':
                channel_preferences[m.channel]['delivered'] += 1
            if m.opened_at:
                channel_preferences[m.channel]['opened'] += 1
            if m.clicked_at:
                channel_preferences[m.channel]['clicked'] += 1
            if m.action_taken:
                channel_preferences[m.channel]['actions'] += 1
        
        # Calculate rates for each channel
        for channel_data in channel_preferences.values():
            total = channel_data['total']
            channel_data['delivery_rate'] = (channel_data['delivered'] / total * 100) if total > 0 else 0
            channel_data['open_rate'] = (channel_data['opened'] / total * 100) if total > 0 else 0
            channel_data['click_rate'] = (channel_data['clicked'] / total * 100) if total > 0 else 0
            channel_data['action_rate'] = (channel_data['actions'] / total * 100) if total > 0 else 0
        
        # Message type engagement
        message_type_engagement = {}
        for m in all_metrics:
            if m.message_type not in message_type_engagement:
                message_type_engagement[m.message_type] = {
                    'total': 0,
                    'delivered': 0,
                    'opened': 0,
                    'clicked': 0,
                    'actions': 0
                }
            
            message_type_engagement[m.message_type]['total'] += 1
            if m.status == 'delivered':
                message_type_engagement[m.message_type]['delivered'] += 1
            if m.opened_at:
                message_type_engagement[m.message_type]['opened'] += 1
            if m.clicked_at:
                message_type_engagement[m.message_type]['clicked'] += 1
            if m.action_taken:
                message_type_engagement[m.message_type]['actions'] += 1
        
        # Calculate rates for each message type
        for msg_type_data in message_type_engagement.values():
            total = msg_type_data['total']
            msg_type_data['delivery_rate'] = (msg_type_data['delivered'] / total * 100) if total > 0 else 0
            msg_type_data['open_rate'] = (msg_type_data['opened'] / total * 100) if total > 0 else 0
            msg_type_data['click_rate'] = (msg_type_data['clicked'] / total * 100) if total > 0 else 0
            msg_type_data['action_rate'] = (msg_type_data['actions'] / total * 100) if total > 0 else 0
        
        # Recent communications
        recent_query = db.query(CommunicationMetrics).filter(
            CommunicationMetrics.user_id == user_id
        ).order_by(CommunicationMetrics.sent_at.desc()).limit(limit)
        
        recent_communications = []
        for m in recent_query.all():
            recent_communications.append({
                'id': m.id,
                'message_type': m.message_type,
                'channel': m.channel,
                'status': m.status,
                'sent_at': m.sent_at.isoformat() if m.sent_at else None,
                'delivered_at': m.delivered_at.isoformat() if m.delivered_at else None,
                'opened_at': m.opened_at.isoformat() if m.opened_at else None,
                'clicked_at': m.clicked_at.isoformat() if m.clicked_at else None,
                'action_taken': m.action_taken,
                'cost': m.cost
            })
        
        # Response patterns (time of day, day of week)
        response_patterns = {
            'hour_of_day': {},
            'day_of_week': {},
            'response_delay': {
                'immediate': 0,  # < 1 hour
                'same_day': 0,   # 1-24 hours
                'next_day': 0,   # 1-7 days
                'never': 0       # > 7 days
            }
        }
        
        for m in all_metrics:
            if m.opened_at:
                # Hour of day
                hour = m.opened_at.hour
                response_patterns['hour_of_day'][hour] = response_patterns['hour_of_day'].get(hour, 0) + 1
                
                # Day of week
                day = m.opened_at.weekday()
                response_patterns['day_of_week'][day] = response_patterns['day_of_week'].get(day, 0) + 1
                
                # Response delay
                if m.sent_at:
                    delay_hours = (m.opened_at - m.sent_at).total_seconds() / 3600
                    if delay_hours < 1:
                        response_patterns['response_delay']['immediate'] += 1
                    elif delay_hours < 24:
                        response_patterns['response_delay']['same_day'] += 1
                    elif delay_hours < 168:  # 7 days
                        response_patterns['response_delay']['next_day'] += 1
            else:
                response_patterns['response_delay']['never'] += 1
        
        return jsonify({
            'user_id': user_id,
            'engagement_summary': {
                'total_messages_received': total_messages,
                'delivery_rate': round(delivery_rate, 2),
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'response_rate': round(response_rate, 2),
                'average_response_time_hours': round(avg_response_time, 2) if avg_response_time else None
            },
            'channel_preferences': channel_preferences,
            'message_type_engagement': message_type_engagement,
            'recent_communications': recent_communications,
            'response_patterns': response_patterns
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user engagement for user {user_id}: {e}")
        return jsonify({'error': 'Failed to get user engagement data'}), 500


@communication_analytics_bp.route('/api/analytics/channel-effectiveness', methods=['GET'])
@jwt_required()
def get_channel_effectiveness():
    """
    Get channel effectiveness comparison (SMS vs Email)
    
    Query Parameters:
    - start_date: Start date for analysis (YYYY-MM-DD)
    - end_date: End date for analysis (YYYY-MM-DD)
    - user_id: Filter by specific user (optional)
    - message_type: Filter by message type (optional)
    
    Returns:
    - SMS vs Email performance comparison
    - Delivery rates by channel
    - Engagement rates by channel
    - Cost effectiveness by channel
    - Optimal channel recommendations
    """
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id', type=int)
        message_type = request.args.get('message_type')
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get database session
        db = get_db_session()
        
        # Build base query
        query = db.query(CommunicationMetrics)
        
        # Apply filters
        if start_dt:
            query = query.filter(CommunicationMetrics.sent_at >= start_dt)
        if end_dt:
            query = query.filter(CommunicationMetrics.sent_at <= end_dt)
        if user_id:
            query = query.filter(CommunicationMetrics.user_id == user_id)
        if message_type:
            query = query.filter(CommunicationMetrics.message_type == message_type)
        
        # Get all metrics
        metrics = query.all()
        
        if not metrics:
            return jsonify({
                'channel_comparison': {},
                'performance_metrics': {},
                'cost_analysis': {},
                'recommendations': []
            }), 200
        
        # Group by channel
        channel_data = {'sms': [], 'email': []}
        for m in metrics:
            if m.channel in channel_data:
                channel_data[m.channel].append(m)
        
        # Calculate metrics for each channel
        channel_comparison = {}
        performance_metrics = {}
        cost_analysis = {}
        
        for channel, channel_metrics in channel_data.items():
            if not channel_metrics:
                continue
                
            total = len(channel_metrics)
            delivered = len([m for m in channel_metrics if m.status == 'delivered'])
            opened = len([m for m in channel_metrics if m.opened_at is not None])
            clicked = len([m for m in channel_metrics if m.clicked_at is not None])
            actions = len([m for m in channel_metrics if m.action_taken is not None])
            total_cost = sum(m.cost or 0 for m in channel_metrics)
            
            delivery_rate = (delivered / total * 100) if total > 0 else 0
            open_rate = (opened / total * 100) if total > 0 else 0
            click_rate = (clicked / total * 100) if total > 0 else 0
            action_rate = (actions / total * 100) if total > 0 else 0
            avg_cost = total_cost / total if total > 0 else 0
            
            channel_comparison[channel] = {
                'total_messages': total,
                'delivery_rate': round(delivery_rate, 2),
                'open_rate': round(open_rate, 2),
                'click_rate': round(click_rate, 2),
                'action_rate': round(action_rate, 2),
                'total_cost': round(total_cost, 2),
                'average_cost_per_message': round(avg_cost, 4)
            }
            
            # Performance metrics
            performance_metrics[channel] = {
                'effectiveness_score': round((delivery_rate * 0.3 + open_rate * 0.4 + action_rate * 0.3), 2),
                'engagement_score': round((open_rate * 0.6 + action_rate * 0.4), 2),
                'cost_efficiency': round(action_rate / avg_cost * 1000 if avg_cost > 0 else 0, 2)
            }
            
            # Cost analysis
            cost_analysis[channel] = {
                'total_spent': round(total_cost, 2),
                'cost_per_delivery': round(total_cost / delivered if delivered > 0 else 0, 4),
                'cost_per_action': round(total_cost / actions if actions > 0 else 0, 4),
                'roi_percentage': round((actions * 10 - total_cost) / total_cost * 100 if total_cost > 0 else 0, 2)  # Assuming $10 value per action
            }
        
        # Generate recommendations
        recommendations = []
        
        if 'sms' in channel_comparison and 'email' in channel_comparison:
            sms_data = channel_comparison['sms']
            email_data = channel_comparison['email']
            
            # Delivery rate comparison
            if sms_data['delivery_rate'] > email_data['delivery_rate'] + 5:
                recommendations.append({
                    'type': 'delivery_rate',
                    'recommendation': 'SMS has significantly higher delivery rate',
                    'priority': 'high',
                    'action': 'Consider using SMS for critical communications'
                })
            elif email_data['delivery_rate'] > sms_data['delivery_rate'] + 5:
                recommendations.append({
                    'type': 'delivery_rate',
                    'recommendation': 'Email has significantly higher delivery rate',
                    'priority': 'high',
                    'action': 'Consider using email for non-critical communications'
                })
            
            # Engagement comparison
            if sms_data['action_rate'] > email_data['action_rate'] + 10:
                recommendations.append({
                    'type': 'engagement',
                    'recommendation': 'SMS drives higher user actions',
                    'priority': 'medium',
                    'action': 'Use SMS for calls-to-action and urgent notifications'
                })
            elif email_data['action_rate'] > sms_data['action_rate'] + 10:
                recommendations.append({
                    'type': 'engagement',
                    'recommendation': 'Email drives higher user actions',
                    'priority': 'medium',
                    'action': 'Use email for detailed content and complex actions'
                })
            
            # Cost effectiveness
            if sms_data['average_cost_per_message'] > email_data['average_cost_per_message'] * 2:
                recommendations.append({
                    'type': 'cost',
                    'recommendation': 'Email is significantly more cost-effective',
                    'priority': 'medium',
                    'action': 'Use email for high-volume communications'
                })
            elif email_data['average_cost_per_message'] > sms_data['average_cost_per_message'] * 2:
                recommendations.append({
                    'type': 'cost',
                    'recommendation': 'SMS is significantly more cost-effective',
                    'priority': 'medium',
                    'action': 'Use SMS for low-volume, high-impact communications'
                })
        
        return jsonify({
            'channel_comparison': channel_comparison,
            'performance_metrics': performance_metrics,
            'cost_analysis': cost_analysis,
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting channel effectiveness: {e}")
        return jsonify({'error': 'Failed to get channel effectiveness data'}), 500


@communication_analytics_bp.route('/api/analytics/cost-tracking', methods=['GET'])
@jwt_required()
def get_cost_tracking():
    """
    Get detailed cost tracking and analysis
    
    Query Parameters:
    - start_date: Start date for analysis (YYYY-MM-DD)
    - end_date: End date for analysis (YYYY-MM-DD)
    - user_id: Filter by specific user (optional)
    - channel: Filter by channel (sms/email)
    - message_type: Filter by message type
    - group_by: Group by (day/week/month/channel/message_type)
    
    Returns:
    - Cost breakdown by various dimensions
    - Cost trends over time
    - ROI analysis
    - Budget tracking
    """
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id', type=int)
        channel = request.args.get('channel')
        message_type = request.args.get('message_type')
        group_by = request.args.get('group_by', 'day')  # day, week, month, channel, message_type
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get database session
        db = get_db_session()
        
        # Build base query
        query = db.query(CommunicationMetrics)
        
        # Apply filters
        if start_dt:
            query = query.filter(CommunicationMetrics.sent_at >= start_dt)
        if end_dt:
            query = query.filter(CommunicationMetrics.sent_at <= end_dt)
        if user_id:
            query = query.filter(CommunicationMetrics.user_id == user_id)
        if channel:
            query = query.filter(CommunicationMetrics.channel == channel)
        if message_type:
            query = query.filter(CommunicationMetrics.message_type == message_type)
        
        # Get all metrics
        metrics = query.all()
        
        if not metrics:
            return jsonify({
                'cost_summary': {
                    'total_cost': 0.0,
                    'total_messages': 0,
                    'average_cost_per_message': 0.0,
                    'cost_per_delivery': 0.0,
                    'cost_per_action': 0.0
                },
                'cost_breakdown': {},
                'cost_trends': [],
                'roi_analysis': {},
                'budget_status': {}
            }), 200
        
        # Calculate summary statistics
        total_cost = sum(m.cost or 0 for m in metrics)
        total_messages = len(metrics)
        delivered_messages = len([m for m in metrics if m.status == 'delivered'])
        action_messages = len([m for m in metrics if m.action_taken is not None])
        
        avg_cost_per_message = total_cost / total_messages if total_messages > 0 else 0
        cost_per_delivery = total_cost / delivered_messages if delivered_messages > 0 else 0
        cost_per_action = total_cost / action_messages if action_messages > 0 else 0
        
        # Cost breakdown by group_by parameter
        cost_breakdown = {}
        
        if group_by in ['day', 'week', 'month']:
            # Time-based grouping
            for m in metrics:
                if m.sent_at:
                    if group_by == 'day':
                        key = m.sent_at.strftime('%Y-%m-%d')
                    elif group_by == 'week':
                        key = m.sent_at.strftime('%Y-W%U')
                    else:  # month
                        key = m.sent_at.strftime('%Y-%m')
                    
                    if key not in cost_breakdown:
                        cost_breakdown[key] = {
                            'total_cost': 0.0,
                            'message_count': 0,
                            'delivered_count': 0,
                            'action_count': 0
                        }
                    
                    cost_breakdown[key]['total_cost'] += m.cost or 0
                    cost_breakdown[key]['message_count'] += 1
                    if m.status == 'delivered':
                        cost_breakdown[key]['delivered_count'] += 1
                    if m.action_taken:
                        cost_breakdown[key]['action_count'] += 1
        
        elif group_by == 'channel':
            # Group by channel
            for m in metrics:
                if m.channel not in cost_breakdown:
                    cost_breakdown[m.channel] = {
                        'total_cost': 0.0,
                        'message_count': 0,
                        'delivered_count': 0,
                        'action_count': 0
                    }
                
                cost_breakdown[m.channel]['total_cost'] += m.cost or 0
                cost_breakdown[m.channel]['message_count'] += 1
                if m.status == 'delivered':
                    cost_breakdown[m.channel]['delivered_count'] += 1
                if m.action_taken:
                    cost_breakdown[m.channel]['action_count'] += 1
        
        elif group_by == 'message_type':
            # Group by message type
            for m in metrics:
                if m.message_type not in cost_breakdown:
                    cost_breakdown[m.message_type] = {
                        'total_cost': 0.0,
                        'message_count': 0,
                        'delivered_count': 0,
                        'action_count': 0
                    }
                
                cost_breakdown[m.message_type]['total_cost'] += m.cost or 0
                cost_breakdown[m.message_type]['message_count'] += 1
                if m.status == 'delivered':
                    cost_breakdown[m.message_type]['delivered_count'] += 1
                if m.action_taken:
                    cost_breakdown[m.message_type]['action_count'] += 1
        
        # Calculate additional metrics for each group
        for group_data in cost_breakdown.values():
            message_count = group_data['message_count']
            delivered_count = group_data['delivered_count']
            action_count = group_data['action_count']
            
            group_data['average_cost_per_message'] = round(group_data['total_cost'] / message_count, 4) if message_count > 0 else 0
            group_data['cost_per_delivery'] = round(group_data['total_cost'] / delivered_count, 4) if delivered_count > 0 else 0
            group_data['cost_per_action'] = round(group_data['total_cost'] / action_count, 4) if action_count > 0 else 0
            group_data['delivery_rate'] = round(delivered_count / message_count * 100, 2) if message_count > 0 else 0
            group_data['action_rate'] = round(action_count / message_count * 100, 2) if message_count > 0 else 0
        
        # Cost trends (daily for the last 30 days if no date range specified)
        cost_trends = []
        if not start_dt:
            start_dt = datetime.now() - timedelta(days=30)
        if not end_dt:
            end_dt = datetime.now()
        
        current_date = start_dt.date()
        while current_date <= end_dt.date():
            daily_metrics = [m for m in metrics if m.sent_at and m.sent_at.date() == current_date]
            daily_cost = sum(m.cost or 0 for m in daily_metrics)
            daily_messages = len(daily_metrics)
            daily_actions = len([m for m in daily_metrics if m.action_taken])
            
            cost_trends.append({
                'date': current_date.isoformat(),
                'total_cost': round(daily_cost, 2),
                'message_count': daily_messages,
                'action_count': daily_actions,
                'average_cost_per_message': round(daily_cost / daily_messages, 4) if daily_messages > 0 else 0
            })
            
            current_date += timedelta(days=1)
        
        # ROI Analysis
        total_actions = len([m for m in metrics if m.action_taken])
        estimated_value_per_action = 10.0  # $10 value per user action
        total_value_generated = total_actions * estimated_value_per_action
        roi_percentage = ((total_value_generated - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        roi_analysis = {
            'total_investment': round(total_cost, 2),
            'total_value_generated': round(total_value_generated, 2),
            'net_return': round(total_value_generated - total_cost, 2),
            'roi_percentage': round(roi_percentage, 2),
            'value_per_action': estimated_value_per_action,
            'break_even_point': round(total_cost / estimated_value_per_action, 0) if estimated_value_per_action > 0 else 0
        }
        
        # Budget tracking (assuming monthly budget of $1000)
        monthly_budget = 1000.0
        current_month = datetime.now().strftime('%Y-%m')
        current_month_cost = sum(m.cost or 0 for m in metrics if m.sent_at and m.sent_at.strftime('%Y-%m') == current_month)
        budget_utilization = (current_month_cost / monthly_budget * 100) if monthly_budget > 0 else 0
        
        budget_status = {
            'monthly_budget': monthly_budget,
            'current_month_cost': round(current_month_cost, 2),
            'budget_utilization_percentage': round(budget_utilization, 2),
            'budget_remaining': round(monthly_budget - current_month_cost, 2),
            'budget_status': 'under_budget' if budget_utilization < 80 else 'approaching_limit' if budget_utilization < 100 else 'over_budget'
        }
        
        return jsonify({
            'cost_summary': {
                'total_cost': round(total_cost, 2),
                'total_messages': total_messages,
                'average_cost_per_message': round(avg_cost_per_message, 4),
                'cost_per_delivery': round(cost_per_delivery, 4),
                'cost_per_action': round(cost_per_action, 4)
            },
            'cost_breakdown': cost_breakdown,
            'cost_trends': cost_trends,
            'roi_analysis': roi_analysis,
            'budget_status': budget_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cost tracking: {e}")
        return jsonify({'error': 'Failed to get cost tracking data'}), 500 