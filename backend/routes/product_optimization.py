"""
Product Optimization Insights API Routes

This module provides comprehensive API routes for product optimization insights including
most valuable banking features by tier, feature usage patterns and workflows, user journey
analysis through banking features, drop-off points in banking workflows, and optimization
opportunities identification.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.analytics.product_optimization_insights import (
    ProductOptimizationInsights, OptimizationMetric, JourneyStage, DropOffType
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
product_optimization_bp = Blueprint('product_optimization', __name__, url_prefix='/api/product-optimization')


@product_optimization_bp.route('/feature-values', methods=['GET'])
@login_required
@require_auth
def get_feature_value_analysis():
    """Get feature value analysis by tier (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = ProductOptimizationInsights(db_session, access_control_service, audit_service)
        
        # Get feature value analysis
        feature_values = optimization_service.analyze_feature_value_by_tier(time_period)
        
        if 'error' in feature_values:
            return error_response(feature_values['error'], 400)
        
        return success_response(feature_values, "Feature value analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature value analysis: {e}")
        return error_response("Failed to retrieve feature value analysis", 500)


@product_optimization_bp.route('/usage-patterns', methods=['GET'])
@login_required
@require_auth
def get_usage_patterns():
    """Get feature usage patterns analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = ProductOptimizationInsights(db_session, access_control_service, audit_service)
        
        # Get usage patterns analysis
        usage_patterns = optimization_service.analyze_feature_usage_patterns(time_period)
        
        if 'error' in usage_patterns:
            return error_response(usage_patterns['error'], 400)
        
        return success_response(usage_patterns, "Usage patterns analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting usage patterns: {e}")
        return error_response("Failed to retrieve usage patterns analysis", 500)


@product_optimization_bp.route('/user-journeys', methods=['GET'])
@login_required
@require_auth
def get_user_journey_analysis():
    """Get user journey analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = ProductOptimizationInsights(db_session, access_control_service, audit_service)
        
        # Get user journey analysis
        user_journeys = optimization_service.analyze_user_journey_through_features(time_period)
        
        if 'error' in user_journeys:
            return error_response(user_journeys['error'], 400)
        
        return success_response(user_journeys, "User journey analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting user journey analysis: {e}")
        return error_response("Failed to retrieve user journey analysis", 500)


@product_optimization_bp.route('/drop-off-points', methods=['GET'])
@login_required
@require_auth
def get_drop_off_points():
    """Get drop-off points analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = ProductOptimizationInsights(db_session, access_control_service, audit_service)
        
        # Get drop-off points analysis
        drop_off_points = optimization_service.identify_drop_off_points(time_period)
        
        if 'error' in drop_off_points:
            return error_response(drop_off_points['error'], 400)
        
        return success_response(drop_off_points, "Drop-off points analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting drop-off points: {e}")
        return error_response("Failed to retrieve drop-off points analysis", 500)


@product_optimization_bp.route('/optimization-opportunities', methods=['GET'])
@login_required
@require_auth
def get_optimization_opportunities():
    """Get optimization opportunities analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = ProductOptimizationInsights(db_session, access_control_service, audit_service)
        
        # Get optimization opportunities analysis
        opportunities = optimization_service.identify_optimization_opportunities(time_period)
        
        if 'error' in opportunities:
            return error_response(opportunities['error'], 400)
        
        return success_response(opportunities, "Optimization opportunities analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting optimization opportunities: {e}")
        return error_response("Failed to retrieve optimization opportunities analysis", 500)


@product_optimization_bp.route('/usage-patterns', methods=['POST'])
@login_required
@require_auth
def record_usage_pattern():
    """Record feature usage pattern"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        feature_name = data.get('feature_name')
        session_id = data.get('session_id')
        workflow_steps = data.get('workflow_steps', [])
        step_durations = data.get('step_durations', {})
        step_completion_rates = data.get('step_completion_rates', {})
        total_duration = data.get('total_duration', 0.0)
        completion_status = data.get('completion_status', 'incomplete')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([feature_name, session_id]):
            return error_response("feature_name and session_id are required", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = ProductOptimizationInsights(db_session, access_control_service, audit_service)
        
        # Record usage pattern
        pattern_id = optimization_service.record_feature_usage_pattern(
            user_id=current_user.id,
            feature_name=feature_name,
            session_id=session_id,
            workflow_steps=workflow_steps,
            step_durations=step_durations,
            step_completion_rates=step_completion_rates,
            total_duration=total_duration,
            completion_status=completion_status,
            metadata=metadata
        )
        
        return success_response({
            'pattern_id': pattern_id,
            'message': 'Usage pattern recorded successfully'
        }, "Usage pattern recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording usage pattern: {e}")
        return error_response("Failed to record usage pattern", 500)


@product_optimization_bp.route('/user-journeys', methods=['POST'])
@login_required
@require_auth
def record_user_journey():
    """Record user journey analysis"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        journey_type = data.get('journey_type')
        stages_completed_str = data.get('stages_completed', [])
        stage_durations = data.get('stage_durations', {})
        stage_transitions = data.get('stage_transitions', [])
        conversion_points = data.get('conversion_points', [])
        drop_off_points = data.get('drop_off_points', [])
        journey_duration = data.get('journey_duration', 0.0)
        success_rate = data.get('success_rate', 0.0)
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not journey_type:
            return error_response("journey_type is required", 400)
        
        # Convert stage strings to JourneyStage enums
        try:
            stages_completed = [JourneyStage(stage) for stage in stages_completed_str]
        except ValueError as e:
            return error_response(f"Invalid journey stage: {e}", 400)
        
        # Convert stage durations to JourneyStage keys
        stage_durations_enum = {}
        for stage_str, duration in stage_durations.items():
            try:
                stage_enum = JourneyStage(stage_str)
                stage_durations_enum[stage_enum] = duration
            except ValueError:
                continue
        
        # Convert stage transitions to JourneyStage tuples
        stage_transitions_enum = []
        for transition in stage_transitions:
            if len(transition) == 2:
                try:
                    from_stage = JourneyStage(transition[0])
                    to_stage = JourneyStage(transition[1])
                    stage_transitions_enum.append((from_stage, to_stage))
                except ValueError:
                    continue
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = ProductOptimizationInsights(db_session, access_control_service, audit_service)
        
        # Record user journey
        journey_id = optimization_service.record_user_journey(
            user_id=current_user.id,
            journey_type=journey_type,
            stages_completed=stages_completed,
            stage_durations=stage_durations_enum,
            stage_transitions=stage_transitions_enum,
            conversion_points=conversion_points,
            drop_off_points=drop_off_points,
            journey_duration=journey_duration,
            success_rate=success_rate,
            metadata=metadata
        )
        
        return success_response({
            'journey_id': journey_id,
            'message': 'User journey recorded successfully'
        }, "User journey recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording user journey: {e}")
        return error_response("Failed to record user journey", 500)


@product_optimization_bp.route('/dashboard', methods=['GET'])
@login_required
@require_auth
def get_optimization_dashboard():
    """Get comprehensive optimization dashboard data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = ProductOptimizationInsights(db_session, access_control_service, audit_service)
        
        # Get dashboard data
        dashboard_data = optimization_service.get_optimization_dashboard()
        
        if 'error' in dashboard_data:
            return error_response(dashboard_data['error'], 400)
        
        return success_response(dashboard_data, "Optimization dashboard data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting optimization dashboard: {e}")
        return error_response("Failed to retrieve optimization dashboard data", 500)


@product_optimization_bp.route('/metrics', methods=['GET'])
@login_required
@require_auth
def get_optimization_metrics():
    """Get available optimization metrics"""
    try:
        metrics = [
            {
                'metric': metric.value,
                'name': metric.value.replace('_', ' ').title(),
                'description': f'Optimization metric for {metric.value.replace("_", " ")}'
            }
            for metric in OptimizationMetric
        ]
        
        return success_response({
            'metrics': metrics,
            'total_metrics': len(metrics)
        }, "Optimization metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting optimization metrics: {e}")
        return error_response("Failed to retrieve optimization metrics", 500)


@product_optimization_bp.route('/journey-stages', methods=['GET'])
@login_required
@require_auth
def get_journey_stages():
    """Get available journey stages"""
    try:
        stages = [
            {
                'stage': stage.value,
                'name': stage.value.replace('_', ' ').title(),
                'description': f'Journey stage: {stage.value.replace("_", " ")}'
            }
            for stage in JourneyStage
        ]
        
        return success_response({
            'stages': stages,
            'total_stages': len(stages)
        }, "Journey stages retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting journey stages: {e}")
        return error_response("Failed to retrieve journey stages", 500)


@product_optimization_bp.route('/drop-off-types', methods=['GET'])
@login_required
@require_auth
def get_drop_off_types():
    """Get available drop-off types"""
    try:
        drop_off_types = [
            {
                'type': drop_off_type.value,
                'name': drop_off_type.value.replace('_', ' ').title(),
                'description': f'Drop-off type: {drop_off_type.value.replace("_", " ")}'
            }
            for drop_off_type in DropOffType
        ]
        
        return success_response({
            'drop_off_types': drop_off_types,
            'total_types': len(drop_off_types)
        }, "Drop-off types retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting drop-off types: {e}")
        return error_response("Failed to retrieve drop-off types", 500) 