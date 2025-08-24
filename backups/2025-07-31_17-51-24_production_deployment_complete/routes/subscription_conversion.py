"""
Subscription Conversion Analytics API Routes

This module provides comprehensive API routes for subscription conversion analytics including
trial-to-paid conversion impact of banking features, tier upgrade rates after bank connection,
banking feature usage correlation with upgrades, churn reduction from banking engagement, and
customer lifetime value impact.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.analytics.subscription_conversion_analytics import (
    SubscriptionConversionAnalytics, ConversionMetric, ConversionStage
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
subscription_conversion_bp = Blueprint('subscription_conversion', __name__, url_prefix='/api/subscription-conversion')


@subscription_conversion_bp.route('/trial-conversion', methods=['GET'])
@login_required
@require_auth
def get_trial_conversion_analysis():
    """Get trial-to-paid conversion analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        conversion_service = SubscriptionConversionAnalytics(db_session, access_control_service, audit_service)
        
        # Get trial conversion analysis
        conversion_data = conversion_service.analyze_trial_to_paid_conversion(time_period)
        
        if 'error' in conversion_data:
            return error_response(conversion_data['error'], 400)
        
        return success_response(conversion_data, "Trial conversion analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting trial conversion analysis: {e}")
        return error_response("Failed to retrieve trial conversion analysis", 500)


@subscription_conversion_bp.route('/tier-upgrades', methods=['GET'])
@login_required
@require_auth
def get_tier_upgrade_analysis():
    """Get tier upgrade rates analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        conversion_service = SubscriptionConversionAnalytics(db_session, access_control_service, audit_service)
        
        # Get tier upgrade analysis
        upgrade_data = conversion_service.analyze_tier_upgrade_rates(time_period)
        
        if 'error' in upgrade_data:
            return error_response(upgrade_data['error'], 400)
        
        return success_response(upgrade_data, "Tier upgrade analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting tier upgrade analysis: {e}")
        return error_response("Failed to retrieve tier upgrade analysis", 500)


@subscription_conversion_bp.route('/feature-correlation', methods=['GET'])
@login_required
@require_auth
def get_feature_usage_correlation():
    """Get feature usage correlation analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        conversion_service = SubscriptionConversionAnalytics(db_session, access_control_service, audit_service)
        
        # Get feature correlation analysis
        correlation_data = conversion_service.analyze_feature_usage_correlation(time_period)
        
        if 'error' in correlation_data:
            return error_response(correlation_data['error'], 400)
        
        return success_response(correlation_data, "Feature usage correlation analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature usage correlation: {e}")
        return error_response("Failed to retrieve feature usage correlation analysis", 500)


@subscription_conversion_bp.route('/churn-reduction', methods=['GET'])
@login_required
@require_auth
def get_churn_reduction_analysis():
    """Get churn reduction analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        conversion_service = SubscriptionConversionAnalytics(db_session, access_control_service, audit_service)
        
        # Get churn reduction analysis
        churn_data = conversion_service.analyze_churn_reduction(time_period)
        
        if 'error' in churn_data:
            return error_response(churn_data['error'], 400)
        
        return success_response(churn_data, "Churn reduction analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting churn reduction analysis: {e}")
        return error_response("Failed to retrieve churn reduction analysis", 500)


@subscription_conversion_bp.route('/customer-lifetime-value', methods=['GET'])
@login_required
@require_auth
def get_customer_lifetime_value_analysis():
    """Get customer lifetime value analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '180d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        conversion_service = SubscriptionConversionAnalytics(db_session, access_control_service, audit_service)
        
        # Get CLV analysis
        clv_data = conversion_service.analyze_customer_lifetime_value(time_period)
        
        if 'error' in clv_data:
            return error_response(clv_data['error'], 400)
        
        return success_response(clv_data, "Customer lifetime value analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting customer lifetime value analysis: {e}")
        return error_response("Failed to retrieve customer lifetime value analysis", 500)


@subscription_conversion_bp.route('/trial-conversion', methods=['POST'])
@login_required
@require_auth
def record_trial_conversion():
    """Record trial conversion data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        user_id = data.get('user_id')
        trial_start_date_str = data.get('trial_start_date')
        trial_end_date_str = data.get('trial_end_date')
        converted = data.get('converted')
        subscription_tier = data.get('subscription_tier')
        banking_features_used = data.get('banking_features_used', [])
        bank_connection_date_str = data.get('bank_connection_date')
        conversion_date_str = data.get('conversion_date')
        conversion_reason = data.get('conversion_reason')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([user_id, trial_start_date_str, trial_end_date_str, converted is not None, subscription_tier]):
            return error_response("user_id, trial_start_date, trial_end_date, converted, and subscription_tier are required", 400)
        
        # Parse dates
        try:
            trial_start_date = datetime.fromisoformat(trial_start_date_str.replace('Z', '+00:00'))
            trial_end_date = datetime.fromisoformat(trial_end_date_str.replace('Z', '+00:00'))
            bank_connection_date = datetime.fromisoformat(bank_connection_date_str.replace('Z', '+00:00')) if bank_connection_date_str else None
            conversion_date = datetime.fromisoformat(conversion_date_str.replace('Z', '+00:00')) if conversion_date_str else None
        except ValueError:
            return error_response("Invalid date format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        conversion_service = SubscriptionConversionAnalytics(db_session, access_control_service, audit_service)
        
        # Record trial conversion
        conversion_id = conversion_service.record_trial_conversion(
            user_id=user_id,
            trial_start_date=trial_start_date,
            trial_end_date=trial_end_date,
            converted=converted,
            subscription_tier=subscription_tier,
            banking_features_used=banking_features_used,
            bank_connection_date=bank_connection_date,
            conversion_date=conversion_date,
            conversion_reason=conversion_reason,
            metadata=metadata
        )
        
        return success_response({
            'conversion_id': conversion_id,
            'message': 'Trial conversion data recorded successfully'
        }, "Trial conversion data recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording trial conversion: {e}")
        return error_response("Failed to record trial conversion data", 500)


@subscription_conversion_bp.route('/tier-upgrade', methods=['POST'])
@login_required
@require_auth
def record_tier_upgrade():
    """Record tier upgrade data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        user_id = data.get('user_id')
        from_tier = data.get('from_tier')
        to_tier = data.get('to_tier')
        upgrade_date_str = data.get('upgrade_date')
        bank_connection_date_str = data.get('bank_connection_date')
        banking_features_used = data.get('banking_features_used', [])
        upgrade_reason = data.get('upgrade_reason')
        revenue_impact = data.get('revenue_impact', 0.0)
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([user_id, from_tier, to_tier, upgrade_date_str]):
            return error_response("user_id, from_tier, to_tier, and upgrade_date are required", 400)
        
        # Parse dates
        try:
            upgrade_date = datetime.fromisoformat(upgrade_date_str.replace('Z', '+00:00'))
            bank_connection_date = datetime.fromisoformat(bank_connection_date_str.replace('Z', '+00:00')) if bank_connection_date_str else None
        except ValueError:
            return error_response("Invalid date format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        conversion_service = SubscriptionConversionAnalytics(db_session, access_control_service, audit_service)
        
        # Record tier upgrade
        upgrade_id = conversion_service.record_tier_upgrade(
            user_id=user_id,
            from_tier=from_tier,
            to_tier=to_tier,
            upgrade_date=upgrade_date,
            bank_connection_date=bank_connection_date,
            banking_features_used=banking_features_used,
            upgrade_reason=upgrade_reason,
            revenue_impact=revenue_impact,
            metadata=metadata
        )
        
        return success_response({
            'upgrade_id': upgrade_id,
            'message': 'Tier upgrade data recorded successfully'
        }, "Tier upgrade data recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording tier upgrade: {e}")
        return error_response("Failed to record tier upgrade data", 500)


@subscription_conversion_bp.route('/dashboard', methods=['GET'])
@login_required
@require_auth
def get_conversion_dashboard():
    """Get comprehensive conversion dashboard data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        conversion_service = SubscriptionConversionAnalytics(db_session, access_control_service, audit_service)
        
        # Get dashboard data
        dashboard_data = conversion_service.get_conversion_dashboard_data()
        
        if 'error' in dashboard_data:
            return error_response(dashboard_data['error'], 400)
        
        return success_response(dashboard_data, "Conversion dashboard data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting conversion dashboard: {e}")
        return error_response("Failed to retrieve conversion dashboard data", 500)


@subscription_conversion_bp.route('/metrics', methods=['GET'])
@login_required
@require_auth
def get_conversion_metrics():
    """Get available conversion metrics"""
    try:
        metrics = [
            {
                'metric': metric.value,
                'name': metric.value.replace('_', ' ').title(),
                'description': f'Conversion metric for {metric.value.replace("_", " ")}'
            }
            for metric in ConversionMetric
        ]
        
        return success_response({
            'metrics': metrics,
            'total_metrics': len(metrics)
        }, "Conversion metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting conversion metrics: {e}")
        return error_response("Failed to retrieve conversion metrics", 500)


@subscription_conversion_bp.route('/stages', methods=['GET'])
@login_required
@require_auth
def get_conversion_stages():
    """Get available conversion stages"""
    try:
        stages = [
            {
                'stage': stage.value,
                'name': stage.value.replace('_', ' ').title(),
                'description': f'Conversion stage: {stage.value.replace("_", " ")}'
            }
            for stage in ConversionStage
        ]
        
        return success_response({
            'stages': stages,
            'total_stages': len(stages)
        }, "Conversion stages retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting conversion stages: {e}")
        return error_response("Failed to retrieve conversion stages", 500) 