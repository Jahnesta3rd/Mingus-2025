"""
Banking Analytics API Routes

This module provides comprehensive API routes for banking performance analytics including
performance metrics, revenue analysis, user behavior tracking, and predictive analytics
for optimizing bank integration performance and driving subscription revenue.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.analytics.banking_performance import (
    BankingPerformanceAnalytics, PerformanceMetric, RevenueMetric, 
    BankingFeature
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
banking_analytics_bp = Blueprint('banking_analytics', __name__, url_prefix='/api/banking-analytics')


@banking_analytics_bp.route('/performance/connection', methods=['GET'])
@login_required
@require_auth
def get_connection_performance():
    """Get bank connection performance analytics (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '24h')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Get connection performance
        performance_data = analytics_service.analyze_connection_performance(time_period)
        
        if 'error' in performance_data:
            return error_response(performance_data['error'], 400)
        
        return success_response(performance_data, "Connection performance data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting connection performance: {e}")
        return error_response("Failed to retrieve connection performance data", 500)


@banking_analytics_bp.route('/performance/feature-usage', methods=['GET'])
@login_required
@require_auth
def get_feature_usage():
    """Get feature usage analytics (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        feature = request.args.get('feature')
        time_period = request.args.get('time_period', '30d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Get feature usage
        if feature:
            try:
                feature_enum = BankingFeature(feature)
                usage_data = analytics_service.analyze_feature_usage(feature_enum, time_period)
            except ValueError:
                return error_response(f"Invalid feature: {feature}", 400)
        else:
            usage_data = analytics_service.analyze_feature_usage(time_period=time_period)
        
        if 'error' in usage_data:
            return error_response(usage_data['error'], 400)
        
        return success_response(usage_data, "Feature usage data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature usage: {e}")
        return error_response("Failed to retrieve feature usage data", 500)


@banking_analytics_bp.route('/revenue/impact', methods=['GET'])
@login_required
@require_auth
def get_revenue_impact():
    """Get revenue impact analytics (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        feature = request.args.get('feature')
        time_period = request.args.get('time_period', '30d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Get revenue impact
        if feature:
            try:
                feature_enum = BankingFeature(feature)
                revenue_data = analytics_service.analyze_revenue_impact(feature_enum, time_period)
            except ValueError:
                return error_response(f"Invalid feature: {feature}", 400)
        else:
            revenue_data = analytics_service.analyze_revenue_impact(time_period=time_period)
        
        if 'error' in revenue_data:
            return error_response(revenue_data['error'], 400)
        
        return success_response(revenue_data, "Revenue impact data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting revenue impact: {e}")
        return error_response("Failed to retrieve revenue impact data", 500)


@banking_analytics_bp.route('/user/churn-prediction/<user_id>', methods=['GET'])
@login_required
@require_auth
def get_user_churn_prediction(user_id):
    """Get user churn prediction (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Get churn prediction
        churn_data = analytics_service.predict_user_churn(user_id)
        
        if 'error' in churn_data:
            return error_response(churn_data['error'], 400)
        
        return success_response(churn_data, "User churn prediction retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting user churn prediction: {e}")
        return error_response("Failed to retrieve user churn prediction", 500)


@banking_analytics_bp.route('/performance/metric', methods=['POST'])
@login_required
@require_auth
def record_performance_metric():
    """Record a performance metric (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        metric_type_str = data.get('metric_type')
        feature_str = data.get('feature')
        value = data.get('value')
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([metric_type_str, feature_str, value is not None]):
            return error_response("metric_type, feature, and value are required", 400)
        
        # Validate metric type
        try:
            metric_type = PerformanceMetric(metric_type_str)
        except ValueError:
            return error_response(f"Invalid metric type: {metric_type_str}", 400)
        
        # Validate feature
        try:
            feature = BankingFeature(feature_str)
        except ValueError:
            return error_response(f"Invalid feature: {feature_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Record performance metric
        metric_id = analytics_service.record_performance_metric(
            metric_type=metric_type,
            feature=feature,
            value=value,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata
        )
        
        return success_response({
            'metric_id': metric_id,
            'message': 'Performance metric recorded successfully'
        }, "Performance metric recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording performance metric: {e}")
        return error_response("Failed to record performance metric", 500)


@banking_analytics_bp.route('/revenue/metric', methods=['POST'])
@login_required
@require_auth
def record_revenue_metric():
    """Record a revenue metric (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        metric_type_str = data.get('metric_type')
        feature_str = data.get('feature')
        amount = data.get('amount')
        user_id = data.get('user_id')
        subscription_tier = data.get('subscription_tier')
        conversion_source = data.get('conversion_source')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([metric_type_str, feature_str, amount is not None, user_id, subscription_tier, conversion_source]):
            return error_response("metric_type, feature, amount, user_id, subscription_tier, and conversion_source are required", 400)
        
        # Validate metric type
        try:
            metric_type = RevenueMetric(metric_type_str)
        except ValueError:
            return error_response(f"Invalid metric type: {metric_type_str}", 400)
        
        # Validate feature
        try:
            feature = BankingFeature(feature_str)
        except ValueError:
            return error_response(f"Invalid feature: {feature_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Record revenue metric
        revenue_id = analytics_service.record_revenue_metric(
            metric_type=metric_type,
            feature=feature,
            amount=amount,
            user_id=user_id,
            subscription_tier=subscription_tier,
            conversion_source=conversion_source,
            metadata=metadata
        )
        
        return success_response({
            'revenue_id': revenue_id,
            'message': 'Revenue metric recorded successfully'
        }, "Revenue metric recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording revenue metric: {e}")
        return error_response("Failed to record revenue metric", 500)


@banking_analytics_bp.route('/user/behavior', methods=['POST'])
@login_required
@require_auth
def record_user_behavior():
    """Record user behavior data"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        feature_str = data.get('feature')
        action = data.get('action')
        duration = data.get('duration')
        success = data.get('success', True)
        session_id = data.get('session_id')
        device_type = data.get('device_type', 'web')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([feature_str, action]):
            return error_response("feature and action are required", 400)
        
        # Validate feature
        try:
            feature = BankingFeature(feature_str)
        except ValueError:
            return error_response(f"Invalid feature: {feature_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Record user behavior
        behavior_id = analytics_service.record_user_behavior(
            user_id=current_user.id,
            feature=feature,
            action=action,
            duration=duration,
            success=success,
            session_id=session_id,
            device_type=device_type,
            metadata=metadata
        )
        
        return success_response({
            'behavior_id': behavior_id,
            'message': 'User behavior recorded successfully'
        }, "User behavior recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording user behavior: {e}")
        return error_response("Failed to record user behavior", 500)


@banking_analytics_bp.route('/dashboard/performance', methods=['GET'])
@login_required
@require_auth
def get_performance_dashboard():
    """Get comprehensive performance dashboard data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Get dashboard data
        dashboard_data = analytics_service.get_performance_dashboard_data()
        
        if 'error' in dashboard_data:
            return error_response(dashboard_data['error'], 400)
        
        return success_response(dashboard_data, "Performance dashboard data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}")
        return error_response("Failed to retrieve performance dashboard data", 500)


@banking_analytics_bp.route('/revenue/optimization-recommendations', methods=['GET'])
@login_required
@require_auth
def get_revenue_optimization_recommendations():
    """Get revenue optimization recommendations (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Get recommendations
        recommendations = analytics_service.get_revenue_optimization_recommendations()
        
        return success_response({
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }, "Revenue optimization recommendations retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting revenue optimization recommendations: {e}")
        return error_response("Failed to retrieve revenue optimization recommendations", 500)


@banking_analytics_bp.route('/features', methods=['GET'])
@login_required
@require_auth
def get_banking_features():
    """Get available banking features"""
    try:
        features = [
            {
                'feature': feature.value,
                'name': feature.value.replace('_', ' ').title(),
                'description': f'Analytics for {feature.value.replace("_", " ")}'
            }
            for feature in BankingFeature
        ]
        
        return success_response({
            'features': features,
            'total_features': len(features)
        }, "Banking features retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting banking features: {e}")
        return error_response("Failed to retrieve banking features", 500)


@banking_analytics_bp.route('/metrics/performance', methods=['GET'])
@login_required
@require_auth
def get_performance_metrics():
    """Get available performance metrics"""
    try:
        metrics = [
            {
                'metric': metric.value,
                'name': metric.value.replace('_', ' ').title(),
                'description': f'Performance metric for {metric.value.replace("_", " ")}'
            }
            for metric in PerformanceMetric
        ]
        
        return success_response({
            'metrics': metrics,
            'total_metrics': len(metrics)
        }, "Performance metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return error_response("Failed to retrieve performance metrics", 500)


@banking_analytics_bp.route('/metrics/revenue', methods=['GET'])
@login_required
@require_auth
def get_revenue_metrics():
    """Get available revenue metrics"""
    try:
        metrics = [
            {
                'metric': metric.value,
                'name': metric.value.replace('_', ' ').title(),
                'description': f'Revenue metric for {metric.value.replace("_", " ")}'
            }
            for metric in RevenueMetric
        ]
        
        return success_response({
            'metrics': metrics,
            'total_metrics': len(metrics)
        }, "Revenue metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting revenue metrics: {e}")
        return error_response("Failed to retrieve revenue metrics", 500)


@banking_analytics_bp.route('/user/behavior/summary', methods=['GET'])
@login_required
@require_auth
def get_user_behavior_summary():
    """Get user behavior summary for current user"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        analytics_service = BankingPerformanceAnalytics(db_session, access_control_service, audit_service)
        
        # Get user's behavior data
        user_behavior = [
            data for data in analytics_service.user_behavior_data.values()
            if data.user_id == current_user.id
        ]
        
        # Calculate summary statistics
        total_actions = len(user_behavior)
        successful_actions = len([data for data in user_behavior if data.success])
        success_rate = successful_actions / total_actions if total_actions > 0 else 0
        
        # Feature usage
        feature_usage = {}
        for data in user_behavior:
            feature_name = data.feature.value
            if feature_name not in feature_usage:
                feature_usage[feature_name] = {
                    'total_actions': 0,
                    'successful_actions': 0,
                    'total_duration': 0
                }
            
            feature_usage[feature_name]['total_actions'] += 1
            if data.success:
                feature_usage[feature_name]['successful_actions'] += 1
            if data.duration:
                feature_usage[feature_name]['total_duration'] += data.duration
        
        # Calculate success rates and average durations
        for feature_name, usage in feature_usage.items():
            usage['success_rate'] = usage['successful_actions'] / usage['total_actions']
            usage['average_duration'] = usage['total_duration'] / usage['total_actions'] if usage['total_actions'] > 0 else 0
        
        # Recent activity
        recent_activity = [
            {
                'feature': data.feature.value,
                'action': data.action,
                'success': data.success,
                'timestamp': data.timestamp.isoformat(),
                'duration': data.duration
            }
            for data in user_behavior
            if data.timestamp >= datetime.utcnow() - timedelta(days=7)
        ]
        
        return success_response({
            'total_actions': total_actions,
            'successful_actions': successful_actions,
            'success_rate': success_rate,
            'feature_usage': feature_usage,
            'recent_activity': recent_activity,
            'last_updated': datetime.utcnow().isoformat()
        }, "User behavior summary retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting user behavior summary: {e}")
        return error_response("Failed to retrieve user behavior summary", 500) 