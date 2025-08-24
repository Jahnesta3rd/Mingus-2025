"""
Business Intelligence API Routes

This module provides comprehensive API routes for business intelligence including
revenue attribution to banking features, cost-per-connection analysis, Plaid API
usage optimization, feature development prioritization, and competitive analysis integration.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.analytics.business_intelligence import (
    BusinessIntelligence, BusinessIntelligenceMetric, RevenueSource, CostType
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
business_intelligence_bp = Blueprint('business_intelligence', __name__, url_prefix='/api/business-intelligence')


@business_intelligence_bp.route('/revenue-attribution', methods=['GET'])
@login_required
@require_auth
def get_revenue_attribution():
    """Get revenue attribution analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get revenue attribution analysis
        revenue_attribution = bi_service.analyze_revenue_attribution(time_period)
        
        if 'error' in revenue_attribution:
            return error_response(revenue_attribution['error'], 400)
        
        return success_response(revenue_attribution, "Revenue attribution analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting revenue attribution: {e}")
        return error_response("Failed to retrieve revenue attribution analysis", 500)


@business_intelligence_bp.route('/cost-per-connection', methods=['GET'])
@login_required
@require_auth
def get_cost_per_connection():
    """Get cost per connection analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get cost per connection analysis
        cost_analysis = bi_service.analyze_cost_per_connection(time_period)
        
        if 'error' in cost_analysis:
            return error_response(cost_analysis['error'], 400)
        
        return success_response(cost_analysis, "Cost per connection analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting cost per connection: {e}")
        return error_response("Failed to retrieve cost per connection analysis", 500)


@business_intelligence_bp.route('/plaid-api-optimization', methods=['GET'])
@login_required
@require_auth
def get_plaid_api_optimization():
    """Get Plaid API optimization analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '30d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get Plaid API optimization analysis
        api_optimization = bi_service.analyze_plaid_api_optimization(time_period)
        
        if 'error' in api_optimization:
            return error_response(api_optimization['error'], 400)
        
        return success_response(api_optimization, "Plaid API optimization analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting Plaid API optimization: {e}")
        return error_response("Failed to retrieve Plaid API optimization analysis", 500)


@business_intelligence_bp.route('/feature-priorities', methods=['GET'])
@login_required
@require_auth
def get_feature_priorities():
    """Get feature development priorities analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get feature development priorities analysis
        feature_priorities = bi_service.analyze_feature_development_priorities()
        
        if 'error' in feature_priorities:
            return error_response(feature_priorities['error'], 400)
        
        return success_response(feature_priorities, "Feature development priorities analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature priorities: {e}")
        return error_response("Failed to retrieve feature development priorities analysis", 500)


@business_intelligence_bp.route('/competitive-analysis', methods=['GET'])
@login_required
@require_auth
def get_competitive_analysis():
    """Get competitive analysis (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get competitive analysis
        competitive_analysis = bi_service.analyze_competitive_analysis()
        
        if 'error' in competitive_analysis:
            return error_response(competitive_analysis['error'], 400)
        
        return success_response(competitive_analysis, "Competitive analysis retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting competitive analysis: {e}")
        return error_response("Failed to retrieve competitive analysis", 500)


@business_intelligence_bp.route('/revenue-attribution', methods=['POST'])
@login_required
@require_auth
def record_revenue_attribution():
    """Record revenue attribution data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        feature_name = data.get('feature_name')
        subscription_tier = data.get('subscription_tier')
        revenue_amount = data.get('revenue_amount')
        revenue_source_str = data.get('revenue_source')
        attribution_percentage = data.get('attribution_percentage')
        attribution_method = data.get('attribution_method')
        user_count = data.get('user_count')
        conversion_rate = data.get('conversion_rate')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([feature_name, subscription_tier, revenue_amount, revenue_source_str, 
                   attribution_percentage, attribution_method, user_count, conversion_rate]):
            return error_response("All fields are required", 400)
        
        # Validate revenue source
        try:
            revenue_source = RevenueSource(revenue_source_str)
        except ValueError:
            return error_response(f"Invalid revenue source: {revenue_source_str}", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Record revenue attribution
        attribution_id = bi_service.record_revenue_attribution(
            feature_name=feature_name,
            subscription_tier=subscription_tier,
            revenue_amount=revenue_amount,
            revenue_source=revenue_source,
            attribution_percentage=attribution_percentage,
            attribution_method=attribution_method,
            user_count=user_count,
            conversion_rate=conversion_rate,
            metadata=metadata
        )
        
        return success_response({
            'attribution_id': attribution_id,
            'message': 'Revenue attribution recorded successfully'
        }, "Revenue attribution recorded successfully")
        
    except Exception as e:
        logger.error(f"Error recording revenue attribution: {e}")
        return error_response("Failed to record revenue attribution", 500)


@business_intelligence_bp.route('/dashboard', methods=['GET'])
@login_required
@require_auth
def get_business_intelligence_dashboard():
    """Get comprehensive business intelligence dashboard data (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get dashboard data
        dashboard_data = bi_service.get_business_intelligence_dashboard()
        
        if 'error' in dashboard_data:
            return error_response(dashboard_data['error'], 400)
        
        return success_response(dashboard_data, "Business intelligence dashboard data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting business intelligence dashboard: {e}")
        return error_response("Failed to retrieve business intelligence dashboard data", 500)


@business_intelligence_bp.route('/metrics', methods=['GET'])
@login_required
@require_auth
def get_business_intelligence_metrics():
    """Get available business intelligence metrics"""
    try:
        metrics = [
            {
                'metric': metric.value,
                'name': metric.value.replace('_', ' ').title(),
                'description': f'Business intelligence metric for {metric.value.replace("_", " ")}'
            }
            for metric in BusinessIntelligenceMetric
        ]
        
        return success_response({
            'metrics': metrics,
            'total_metrics': len(metrics)
        }, "Business intelligence metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting business intelligence metrics: {e}")
        return error_response("Failed to retrieve business intelligence metrics", 500)


@business_intelligence_bp.route('/revenue-sources', methods=['GET'])
@login_required
@require_auth
def get_revenue_sources():
    """Get available revenue sources"""
    try:
        revenue_sources = [
            {
                'source': source.value,
                'name': source.value.replace('_', ' ').title(),
                'description': f'Revenue source: {source.value.replace("_", " ")}'
            }
            for source in RevenueSource
        ]
        
        return success_response({
            'revenue_sources': revenue_sources,
            'total_sources': len(revenue_sources)
        }, "Revenue sources retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting revenue sources: {e}")
        return error_response("Failed to retrieve revenue sources", 500)


@business_intelligence_bp.route('/cost-types', methods=['GET'])
@login_required
@require_auth
def get_cost_types():
    """Get available cost types"""
    try:
        cost_types = [
            {
                'type': cost_type.value,
                'name': cost_type.value.replace('_', ' ').title(),
                'description': f'Cost type: {cost_type.value.replace("_", " ")}'
            }
            for cost_type in CostType
        ]
        
        return success_response({
            'cost_types': cost_types,
            'total_types': len(cost_types)
        }, "Cost types retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting cost types: {e}")
        return error_response("Failed to retrieve cost types", 500)


@business_intelligence_bp.route('/revenue-attribution/summary', methods=['GET'])
@login_required
@require_auth
def get_revenue_attribution_summary():
    """Get revenue attribution summary (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get revenue attribution analysis
        revenue_attribution = bi_service.analyze_revenue_attribution(time_period)
        
        if 'error' in revenue_attribution:
            return error_response(revenue_attribution['error'], 400)
        
        # Create summary
        summary = {
            'time_period': time_period,
            'total_revenue_attributed': revenue_attribution.get('total_revenue_attributed', 0),
            'total_attributions': revenue_attribution.get('total_attributions', 0),
            'top_features': [],
            'revenue_by_tier': {}
        }
        
        # Get top features by revenue
        feature_analysis = revenue_attribution.get('feature_analysis', {})
        if feature_analysis:
            top_features = sorted(
                feature_analysis.items(),
                key=lambda x: x[1]['total_revenue'],
                reverse=True
            )[:5]
            
            summary['top_features'] = [
                {
                    'feature_name': feature_name,
                    'total_revenue': data['total_revenue'],
                    'attribution_score': data['revenue_attribution_score']
                }
                for feature_name, data in top_features
            ]
        
        return success_response(summary, "Revenue attribution summary retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting revenue attribution summary: {e}")
        return error_response("Failed to retrieve revenue attribution summary", 500)


@business_intelligence_bp.route('/cost-per-connection/summary', methods=['GET'])
@login_required
@require_auth
def get_cost_per_connection_summary():
    """Get cost per connection summary (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '90d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get cost per connection analysis
        cost_analysis = bi_service.analyze_cost_per_connection(time_period)
        
        if 'error' in cost_analysis:
            return error_response(cost_analysis['error'], 400)
        
        # Create summary
        summary = {
            'time_period': time_period,
            'total_cost': cost_analysis.get('total_cost', 0),
            'total_connections': cost_analysis.get('total_connections', 0),
            'average_cost_per_connection': cost_analysis.get('total_cost', 0) / cost_analysis.get('total_connections', 1) if cost_analysis.get('total_connections', 0) > 0 else 0,
            'most_expensive_connections': [],
            'optimization_opportunities': []
        }
        
        # Get most expensive connections
        connection_analysis = cost_analysis.get('connection_analysis', {})
        if connection_analysis:
            expensive_connections = sorted(
                connection_analysis.items(),
                key=lambda x: x[1]['average_cost_per_connection'],
                reverse=True
            )[:3]
            
            summary['most_expensive_connections'] = [
                {
                    'connection_type': connection_type,
                    'average_cost_per_connection': data['average_cost_per_connection'],
                    'total_connections': data['total_connections']
                }
                for connection_type, data in expensive_connections
            ]
            
            # Collect optimization opportunities
            all_opportunities = []
            for data in connection_analysis.values():
                all_opportunities.extend(data.get('optimization_opportunities', []))
            summary['optimization_opportunities'] = list(set(all_opportunities))[:5]
        
        return success_response(summary, "Cost per connection summary retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting cost per connection summary: {e}")
        return error_response("Failed to retrieve cost per connection summary", 500)


@business_intelligence_bp.route('/plaid-api-optimization/summary', methods=['GET'])
@login_required
@require_auth
def get_plaid_api_optimization_summary():
    """Get Plaid API optimization summary (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        time_period = request.args.get('time_period', '30d')
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        bi_service = BusinessIntelligence(db_session, access_control_service, audit_service)
        
        # Get Plaid API optimization analysis
        api_optimization = bi_service.analyze_plaid_api_optimization(time_period)
        
        if 'error' in api_optimization:
            return error_response(api_optimization['error'], 400)
        
        # Create summary
        summary = {
            'time_period': time_period,
            'total_api_requests': api_optimization.get('total_api_requests', 0),
            'total_api_cost': api_optimization.get('total_api_cost', 0),
            'average_cost_per_request': api_optimization.get('total_api_cost', 0) / api_optimization.get('total_api_requests', 1) if api_optimization.get('total_api_requests', 0) > 0 else 0,
            'most_expensive_endpoints': [],
            'optimization_recommendations': []
        }
        
        # Get most expensive endpoints
        endpoint_analysis = api_optimization.get('endpoint_analysis', {})
        if endpoint_analysis:
            expensive_endpoints = sorted(
                endpoint_analysis.items(),
                key=lambda x: x[1]['cost_per_request'],
                reverse=True
            )[:3]
            
            summary['most_expensive_endpoints'] = [
                {
                    'endpoint': endpoint,
                    'cost_per_request': data['cost_per_request'],
                    'total_requests': data['total_requests']
                }
                for endpoint, data in expensive_endpoints
            ]
            
            # Collect optimization recommendations
            all_recommendations = []
            for data in endpoint_analysis.values():
                all_recommendations.extend(data.get('optimization_recommendations', []))
            summary['optimization_recommendations'] = list(set(all_recommendations))[:5]
        
        return success_response(summary, "Plaid API optimization summary retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting Plaid API optimization summary: {e}")
        return error_response("Failed to retrieve Plaid API optimization summary", 500) 