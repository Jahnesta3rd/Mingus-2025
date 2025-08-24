"""
Automated Optimization API Routes

This module provides comprehensive API routes for automated optimization including
A/B testing framework for banking features, personalized feature recommendations,
usage-based upgrade timing optimization, retention campaign triggers, and feature sunset analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.analytics.automated_optimization import (
    AutomatedOptimization, OptimizationType, ABTestStatus, RecommendationType, CampaignTrigger
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
automated_optimization_bp = Blueprint('automated_optimization', __name__, url_prefix='/api/automated-optimization')


@automated_optimization_bp.route('/ab-tests', methods=['GET'])
@login_required
@require_auth
def get_ab_tests():
    """Get A/B tests (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Get A/B tests
        ab_tests = list(optimization_service.ab_tests.values())
        
        # Format response
        formatted_tests = []
        for test in ab_tests:
            formatted_tests.append({
                'test_id': test.test_id,
                'test_name': test.test_name,
                'feature_name': test.feature_name,
                'description': test.description,
                'status': test.status.value,
                'start_date': test.start_date.isoformat(),
                'end_date': test.end_date.isoformat() if test.end_date else None,
                'created_by': test.created_by,
                'created_at': test.created_at.isoformat()
            })
        
        return success_response({
            'ab_tests': formatted_tests,
            'total_tests': len(formatted_tests)
        }, "A/B tests retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting A/B tests: {e}")
        return error_response("Failed to retrieve A/B tests", 500)


@automated_optimization_bp.route('/ab-tests', methods=['POST'])
@login_required
@require_auth
def create_ab_test():
    """Create A/B test (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        test_name = data.get('test_name')
        feature_name = data.get('feature_name')
        description = data.get('description')
        hypothesis = data.get('hypothesis')
        success_metrics = data.get('success_metrics', [])
        test_groups = data.get('test_groups', {})
        traffic_allocation = data.get('traffic_allocation', {})
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([test_name, feature_name, description, hypothesis, test_groups, traffic_allocation]):
            return error_response("test_name, feature_name, description, hypothesis, test_groups, and traffic_allocation are required", 400)
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00')) if start_date_str else datetime.utcnow()
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')) if end_date_str else None
        except ValueError:
            return error_response("Invalid date format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Create A/B test
        test_id = optimization_service.create_ab_test(
            test_name=test_name,
            feature_name=feature_name,
            description=description,
            hypothesis=hypothesis,
            success_metrics=success_metrics,
            test_groups=test_groups,
            traffic_allocation=traffic_allocation,
            start_date=start_date,
            end_date=end_date,
            created_by=current_user.id,
            metadata=metadata
        )
        
        return success_response({
            'test_id': test_id,
            'message': 'A/B test created successfully'
        }, "A/B test created successfully")
        
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        return error_response("Failed to create A/B test", 500)


@automated_optimization_bp.route('/ab-tests/<test_id>/start', methods=['POST'])
@login_required
@require_auth
def start_ab_test(test_id):
    """Start A/B test (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Start A/B test
        success = optimization_service.start_ab_test(test_id)
        
        if not success:
            return error_response("Failed to start A/B test", 400)
        
        return success_response({
            'test_id': test_id,
            'message': 'A/B test started successfully'
        }, "A/B test started successfully")
        
    except Exception as e:
        logger.error(f"Error starting A/B test: {e}")
        return error_response("Failed to start A/B test", 500)


@automated_optimization_bp.route('/ab-tests/<test_id>/results', methods=['GET'])
@login_required
@require_auth
def get_ab_test_results(test_id):
    """Get A/B test results (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Get A/B test results
        results = optimization_service.analyze_ab_test_results(test_id)
        
        if 'error' in results:
            return error_response(results['error'], 400)
        
        return success_response(results, "A/B test results retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting A/B test results: {e}")
        return error_response("Failed to retrieve A/B test results", 500)


@automated_optimization_bp.route('/feature-recommendations/<user_id>', methods=['GET'])
@login_required
@require_auth
def get_feature_recommendations(user_id):
    """Get feature recommendations for user"""
    try:
        # Check if user is requesting their own recommendations or is admin
        if current_user.id != user_id and not current_user.has_role('admin'):
            return error_response("Access denied", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Get feature recommendations
        recommendations = optimization_service.generate_feature_recommendations(user_id)
        
        return success_response({
            'user_id': user_id,
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }, "Feature recommendations retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature recommendations: {e}")
        return error_response("Failed to retrieve feature recommendations", 500)


@automated_optimization_bp.route('/upgrade-timing/<user_id>', methods=['GET'])
@login_required
@require_auth
def get_upgrade_timing(user_id):
    """Get upgrade timing optimization for user"""
    try:
        # Check if user is requesting their own timing or is admin
        if current_user.id != user_id and not current_user.has_role('admin'):
            return error_response("Access denied", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Get upgrade timing optimization
        timing = optimization_service.optimize_upgrade_timing(user_id)
        
        if 'error' in timing:
            return error_response(timing['error'], 400)
        
        return success_response(timing, "Upgrade timing optimization retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting upgrade timing: {e}")
        return error_response("Failed to retrieve upgrade timing optimization", 500)


@automated_optimization_bp.route('/retention-campaigns', methods=['GET'])
@login_required
@require_auth
def get_retention_campaigns():
    """Get retention campaigns (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Get retention campaigns
        campaigns = optimization_service.trigger_retention_campaigns()
        
        return success_response({
            'campaigns': campaigns,
            'total_campaigns': len(campaigns)
        }, "Retention campaigns retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting retention campaigns: {e}")
        return error_response("Failed to retrieve retention campaigns", 500)


@automated_optimization_bp.route('/feature-sunset', methods=['GET'])
@login_required
@require_auth
def get_feature_sunset():
    """Get feature sunset analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Get feature sunset analysis
        sunset_analyses = optimization_service.analyze_feature_sunset()
        
        return success_response({
            'sunset_analyses': sunset_analyses,
            'total_analyses': len(sunset_analyses)
        }, "Feature sunset analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature sunset analysis: {e}")
        return error_response("Failed to retrieve feature sunset analysis", 500)


@automated_optimization_bp.route('/dashboard', methods=['GET'])
@login_required
@require_auth
def get_optimization_dashboard():
    """Get optimization dashboard (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        optimization_service = AutomatedOptimization(db_session, access_control_service, audit_service)
        
        # Get dashboard data
        dashboard_data = {
            'ab_tests': {
                'total_tests': len(optimization_service.ab_tests),
                'active_tests': len([t for t in optimization_service.ab_tests.values() if t.status == ABTestStatus.ACTIVE]),
                'completed_tests': len([t for t in optimization_service.ab_tests.values() if t.status == ABTestStatus.COMPLETED])
            },
            'feature_recommendations': {
                'total_recommendations': len(optimization_service.feature_recommendations),
                'acted_upon': len([r for r in optimization_service.feature_recommendations.values() if r.is_acted_upon])
            },
            'upgrade_timings': {
                'total_timings': len(optimization_service.upgrade_timings),
                'acted_upon': len([t for t in optimization_service.upgrade_timings.values() if t.is_acted_upon])
            },
            'retention_campaigns': {
                'total_campaigns': len(optimization_service.retention_campaigns),
                'active_campaigns': len([c for c in optimization_service.retention_campaigns.values() if c.is_active])
            },
            'feature_sunsets': {
                'total_analyses': len(optimization_service.feature_sunsets),
                'recommended_sunset': len([s for s in optimization_service.feature_sunsets.values() if s.sunset_recommendation])
            }
        }
        
        return success_response(dashboard_data, "Optimization dashboard retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting optimization dashboard: {e}")
        return error_response("Failed to retrieve optimization dashboard", 500)


@automated_optimization_bp.route('/optimization-types', methods=['GET'])
@login_required
@require_auth
def get_optimization_types():
    """Get available optimization types"""
    try:
        optimization_types = [
            {
                'type': opt_type.value,
                'name': opt_type.value.replace('_', ' ').title(),
                'description': f'Optimization type for {opt_type.value.replace("_", " ")}'
            }
            for opt_type in OptimizationType
        ]
        
        return success_response({
            'optimization_types': optimization_types,
            'total_types': len(optimization_types)
        }, "Optimization types retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting optimization types: {e}")
        return error_response("Failed to retrieve optimization types", 500)


@automated_optimization_bp.route('/ab-test-statuses', methods=['GET'])
@login_required
@require_auth
def get_ab_test_statuses():
    """Get available A/B test statuses"""
    try:
        statuses = [
            {
                'status': status.value,
                'name': status.value.replace('_', ' ').title(),
                'description': f'A/B test status: {status.value.replace("_", " ")}'
            }
            for status in ABTestStatus
        ]
        
        return success_response({
            'statuses': statuses,
            'total_statuses': len(statuses)
        }, "A/B test statuses retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting A/B test statuses: {e}")
        return error_response("Failed to retrieve A/B test statuses", 500)


@automated_optimization_bp.route('/recommendation-types', methods=['GET'])
@login_required
@require_auth
def get_recommendation_types():
    """Get available recommendation types"""
    try:
        recommendation_types = [
            {
                'type': rec_type.value,
                'name': rec_type.value.replace('_', ' ').title(),
                'description': f'Recommendation type for {rec_type.value.replace("_", " ")}'
            }
            for rec_type in RecommendationType
        ]
        
        return success_response({
            'recommendation_types': recommendation_types,
            'total_types': len(recommendation_types)
        }, "Recommendation types retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting recommendation types: {e}")
        return error_response("Failed to retrieve recommendation types", 500)


@automated_optimization_bp.route('/campaign-triggers', methods=['GET'])
@login_required
@require_auth
def get_campaign_triggers():
    """Get available campaign triggers"""
    try:
        triggers = [
            {
                'trigger': trigger.value,
                'name': trigger.value.replace('_', ' ').title(),
                'description': f'Campaign trigger for {trigger.value.replace("_", " ")}'
            }
            for trigger in CampaignTrigger
        ]
        
        return success_response({
            'triggers': triggers,
            'total_triggers': len(triggers)
        }, "Campaign triggers retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting campaign triggers: {e}")
        return error_response("Failed to retrieve campaign triggers", 500) 