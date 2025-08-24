"""
Banking Engagement Metrics API Routes

This module provides comprehensive API routes for banking engagement metrics including
bank connection completion rates by tier, daily/weekly/monthly banking feature usage,
time spent in banking features, feature adoption progression, and user engagement
correlation with retention.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.analytics.banking_engagement_metrics import (
    BankingEngagementMetrics, EngagementMetric, TimePeriod, SubscriptionTier
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
banking_engagement_bp = Blueprint('banking_engagement', __name__, url_prefix='/api/banking-engagement')


@banking_engagement_bp.route('/connection-completion', methods=['GET'])
@login_required
@require_auth
def get_connection_completion_rates():
    """Get bank connection completion rates by tier (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '30d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Get connection completion rates
        completion_data = engagement_service.analyze_connection_completion_by_tier(time_period)
        
        if 'error' in completion_data:
            return error_response(completion_data['error'], 400)
        
        return success_response(completion_data, "Connection completion rates retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting connection completion rates: {e}")
        return error_response("Failed to retrieve connection completion rates", 500)


@banking_engagement_bp.route('/feature-usage/<period>', methods=['GET'])
@login_required
@require_auth
def get_feature_usage_by_period(period):
    """Get banking feature usage by period (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        feature_name = request.args.get('feature')
        
        # Validate period
        try:
            period_enum = TimePeriod(period)
        except ValueError:
            return error_response(f"Invalid period: {period}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Get feature usage data
        usage_data = engagement_service.analyze_feature_usage_by_period(period_enum, feature_name)
        
        if 'error' in usage_data:
            return error_response(usage_data['error'], 400)
        
        return success_response(usage_data, f"{period.title()} feature usage data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature usage by period: {e}")
        return error_response("Failed to retrieve feature usage data", 500)


@banking_engagement_bp.route('/time-spent', methods=['GET'])
@login_required
@require_auth
def get_time_spent_in_features():
    """Get time spent in banking features (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '30d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Get time spent data
        time_data = engagement_service.analyze_time_spent_in_features(time_period)
        
        if 'error' in time_data:
            return error_response(time_data['error'], 400)
        
        return success_response(time_data, "Time spent in features data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting time spent in features: {e}")
        return error_response("Failed to retrieve time spent data", 500)


@banking_engagement_bp.route('/feature-adoption', methods=['GET'])
@login_required
@require_auth
def get_feature_adoption_progression():
    """Get feature adoption progression (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Get feature adoption data
        adoption_data = engagement_service.analyze_feature_adoption_progression(time_period)
        
        if 'error' in adoption_data:
            return error_response(adoption_data['error'], 400)
        
        return success_response(adoption_data, "Feature adoption progression data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature adoption progression: {e}")
        return error_response("Failed to retrieve feature adoption data", 500)


@banking_engagement_bp.route('/retention-correlation', methods=['GET'])
@login_required
@require_auth
def get_engagement_retention_correlation():
    """Get user engagement correlation with retention (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Get retention correlation data
        correlation_data = engagement_service.analyze_engagement_retention_correlation(time_period)
        
        if 'error' in correlation_data:
            return error_response(correlation_data['error'], 400)
        
        return success_response(correlation_data, "Engagement retention correlation data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting engagement retention correlation: {e}")
        return error_response("Failed to retrieve retention correlation data", 500)


@banking_engagement_bp.route('/connection-completion', methods=['POST'])
@login_required
@require_auth
def record_connection_completion():
    """Record bank connection completion data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        user_id = data.get('user_id')
        subscription_tier_str = data.get('subscription_tier')
        connection_attempted = data.get('connection_attempted')
        connection_completed = data.get('connection_completed')
        completion_time = data.get('completion_time')
        error_type = data.get('error_type')
        retry_count = data.get('retry_count', 0)
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([user_id, subscription_tier_str, connection_attempted is not None, connection_completed is not None]):
            return error_response("user_id, subscription_tier, connection_attempted, and connection_completed are required", 400)
        
        # Validate subscription tier
        try:
            subscription_tier = SubscriptionTier(subscription_tier_str)
        except ValueError:
            return error_response(f"Invalid subscription tier: {subscription_tier_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Record connection completion
        completion_id = engagement_service.record_connection_completion(
            user_id=user_id,
            subscription_tier=subscription_tier,
            connection_attempted=connection_attempted,
            connection_completed=connection_completed,
            completion_time=completion_time,
            error_type=error_type,
            retry_count=retry_count,
            metadata=metadata
        )
        
        return success_response({
            'completion_id': completion_id,
            'message': 'Connection completion data recorded successfully'
        }, "Connection completion data recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording connection completion: {e}")
        return error_response("Failed to record connection completion data", 500)


@banking_engagement_bp.route('/feature-usage', methods=['POST'])
@login_required
@require_auth
def record_feature_usage():
    """Record feature usage data"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        feature_name = data.get('feature_name')
        subscription_tier_str = data.get('subscription_tier')
        usage_count = data.get('usage_count', 1)
        time_spent = data.get('time_spent', 0)
        session_count = data.get('session_count', 1)
        period_str = data.get('period', 'daily')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([feature_name, subscription_tier_str]):
            return error_response("feature_name and subscription_tier are required", 400)
        
        # Validate subscription tier
        try:
            subscription_tier = SubscriptionTier(subscription_tier_str)
        except ValueError:
            return error_response(f"Invalid subscription tier: {subscription_tier_str}", 400)
        
        # Validate period
        try:
            period = TimePeriod(period_str)
        except ValueError:
            return error_response(f"Invalid period: {period_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Record feature usage
        usage_id = engagement_service.record_feature_usage(
            user_id=current_user.id,
            feature_name=feature_name,
            subscription_tier=subscription_tier,
            usage_count=usage_count,
            time_spent=time_spent,
            session_count=session_count,
            period=period,
            metadata=metadata
        )
        
        return success_response({
            'usage_id': usage_id,
            'message': 'Feature usage data recorded successfully'
        }, "Feature usage data recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording feature usage: {e}")
        return error_response("Failed to record feature usage data", 500)


@banking_engagement_bp.route('/time-spent', methods=['POST'])
@login_required
@require_auth
def record_time_spent():
    """Record time spent in banking features"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        feature_name = data.get('feature_name')
        subscription_tier_str = data.get('subscription_tier')
        session_id = data.get('session_id')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')
        duration = data.get('duration')
        activity_type = data.get('activity_type', 'interact')
        success = data.get('success', True)
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([feature_name, subscription_tier_str, session_id]):
            return error_response("feature_name, subscription_tier, and session_id are required", 400)
        
        # Validate subscription tier
        try:
            subscription_tier = SubscriptionTier(subscription_tier_str)
        except ValueError:
            return error_response(f"Invalid subscription tier: {subscription_tier_str}", 400)
        
        # Parse timestamps
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00')) if start_time_str else datetime.utcnow()
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00')) if end_time_str else datetime.utcnow()
        except ValueError:
            return error_response("Invalid timestamp format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Record time spent
        time_id = engagement_service.record_time_spent(
            user_id=current_user.id,
            feature_name=feature_name,
            subscription_tier=subscription_tier,
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            duration=duration or (end_time - start_time).total_seconds(),
            activity_type=activity_type,
            success=success,
            metadata=metadata
        )
        
        return success_response({
            'time_id': time_id,
            'message': 'Time spent data recorded successfully'
        }, "Time spent data recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording time spent: {e}")
        return error_response("Failed to record time spent data", 500)


@banking_engagement_bp.route('/feature-adoption', methods=['POST'])
@login_required
@require_auth
def record_feature_adoption():
    """Record feature adoption progression"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        feature_name = data.get('feature_name')
        subscription_tier_str = data.get('subscription_tier')
        adoption_stage = data.get('adoption_stage')
        adoption_date_str = data.get('adoption_date')
        progression_time = data.get('progression_time')
        usage_frequency = data.get('usage_frequency')
        satisfaction_score = data.get('satisfaction_score')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([feature_name, subscription_tier_str, adoption_stage]):
            return error_response("feature_name, subscription_tier, and adoption_stage are required", 400)
        
        # Validate subscription tier
        try:
            subscription_tier = SubscriptionTier(subscription_tier_str)
        except ValueError:
            return error_response(f"Invalid subscription tier: {subscription_tier_str}", 400)
        
        # Parse adoption date
        try:
            adoption_date = datetime.fromisoformat(adoption_date_str.replace('Z', '+00:00')) if adoption_date_str else datetime.utcnow()
        except ValueError:
            return error_response("Invalid adoption date format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Record feature adoption
        adoption_id = engagement_service.record_feature_adoption(
            user_id=current_user.id,
            feature_name=feature_name,
            subscription_tier=subscription_tier,
            adoption_stage=adoption_stage,
            adoption_date=adoption_date,
            progression_time=progression_time,
            usage_frequency=usage_frequency,
            satisfaction_score=satisfaction_score,
            metadata=metadata
        )
        
        return success_response({
            'adoption_id': adoption_id,
            'message': 'Feature adoption data recorded successfully'
        }, "Feature adoption data recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording feature adoption: {e}")
        return error_response("Failed to record feature adoption data", 500)


@banking_engagement_bp.route('/dashboard', methods=['GET'])
@login_required
@require_auth
def get_engagement_dashboard():
    """Get comprehensive engagement dashboard data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        engagement_service = BankingEngagementMetrics(db_session, access_control_service, audit_service)
        
        # Get dashboard data
        dashboard_data = engagement_service.get_engagement_dashboard_data()
        
        if 'error' in dashboard_data:
            return error_response(dashboard_data['error'], 400)
        
        return success_response(dashboard_data, "Engagement dashboard data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting engagement dashboard: {e}")
        return error_response("Failed to retrieve engagement dashboard data", 500)


@banking_engagement_bp.route('/periods', methods=['GET'])
@login_required
@require_auth
def get_time_periods():
    """Get available time periods for analysis"""
    try:
        periods = [
            {
                'period': period.value,
                'name': period.value.replace('_', ' ').title(),
                'description': f'Analysis period for {period.value.replace("_", " ")}'
            }
            for period in TimePeriod
        ]
        
        return success_response({
            'periods': periods,
            'total_periods': len(periods)
        }, "Time periods retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting time periods: {e}")
        return error_response("Failed to retrieve time periods", 500)


@banking_engagement_bp.route('/subscription-tiers', methods=['GET'])
@login_required
@require_auth
def get_subscription_tiers():
    """Get available subscription tiers"""
    try:
        tiers = [
            {
                'tier': tier.value,
                'name': tier.value.replace('_', ' ').title(),
                'description': f'Subscription tier: {tier.value.replace("_", " ")}'
            }
            for tier in SubscriptionTier
        ]
        
        return success_response({
            'tiers': tiers,
            'total_tiers': len(tiers)
        }, "Subscription tiers retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting subscription tiers: {e}")
        return error_response("Failed to retrieve subscription tiers", 500)


@banking_engagement_bp.route('/metrics', methods=['GET'])
@login_required
@require_auth
def get_engagement_metrics():
    """Get available engagement metrics"""
    try:
        metrics = [
            {
                'metric': metric.value,
                'name': metric.value.replace('_', ' ').title(),
                'description': f'Engagement metric for {metric.value.replace("_", " ")}'
            }
            for metric in EngagementMetric
        ]
        
        return success_response({
            'metrics': metrics,
            'total_metrics': len(metrics)
        }, "Engagement metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting engagement metrics: {e}")
        return error_response("Failed to retrieve engagement metrics", 500) 