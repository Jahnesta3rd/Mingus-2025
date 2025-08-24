"""
Mid-Tier Features API Routes

This module provides API endpoints for Mid-tier subscription features including
standard categorization, basic spending insights, 6-month cash flow forecasting,
and savings goal tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json

from backend.services.mid_tier_features_service import (
    MidTierFeaturesService, SpendingInsightType, GoalStatus, GoalType,
    SpendingInsight, SavingsGoal, StandardCategorization, CashFlowForecast6Month
)
from backend.services.subscription_tier_service import SubscriptionTierService, SubscriptionTier, FeatureType
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.models.bank_account_models import PlaidTransaction

logger = logging.getLogger(__name__)

mid_tier_bp = Blueprint('mid_tier', __name__, url_prefix='/api/mid-tier')


@mid_tier_bp.route('/standard-categorization/apply', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def apply_standard_categorization():
    """
    Apply standard categorization to transactions for Mid-tier users
    
    Request body:
    {
        "transaction_ids": ["tx1", "tx2"],  # Optional - specific transactions
        "auto_apply": true,  # Optional - auto-apply high confidence results
        "date_range": {  # Optional - date range for transactions
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        }
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'transaction_ids': {'type': 'list', 'required': False},
            'auto_apply': {'type': 'bool', 'required': False, 'default': True},
            'date_range': {'type': 'dict', 'required': False}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        mid_tier_service = MidTierFeaturesService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.STANDARD_CATEGORIZATION):
            return create_response(
                success=False,
                message="Standard categorization is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'standard_categorization'}
            )
        
        # Get transactions to categorize
        if data.get('transaction_ids'):
            # Get specific transactions
            transactions = db_session.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.user_id == current_user.id,
                    PlaidTransaction.transaction_id.in_(data['transaction_ids'])
                )
            ).all()
        else:
            # Get transactions from date range or recent transactions
            query = db_session.query(PlaidTransaction).filter(
                PlaidTransaction.user_id == current_user.id
            )
            
            if data.get('date_range'):
                start_date = datetime.fromisoformat(data['date_range']['start_date'])
                end_date = datetime.fromisoformat(data['date_range']['end_date'])
                query = query.filter(
                    PlaidTransaction.date.between(start_date, end_date)
                )
            else:
                # Default to last 30 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                query = query.filter(
                    PlaidTransaction.date.between(start_date, end_date)
                )
            
            transactions = query.all()
        
        if not transactions:
            return create_response(
                success=False,
                message="No transactions found for categorization",
                status_code=404
            )
        
        # Apply standard categorization
        results = mid_tier_service.apply_standard_categorization(current_user.id, transactions)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'transaction_id': result.transaction_id,
                'original_category': result.original_category,
                'suggested_category': result.suggested_category,
                'confidence_score': result.confidence_score,
                'categorization_method': result.categorization_method,
                'reasoning': result.reasoning,
                'created_at': result.created_at.isoformat()
            })
        
        # Save changes if auto-apply is enabled
        if data.get('auto_apply', True):
            db_session.commit()
        
        return create_response(
            success=True,
            message=f"Standard categorization applied to {len(formatted_results)} transactions",
            data={
                'results': formatted_results,
                'total_processed': len(formatted_results),
                'auto_applied': data.get('auto_apply', True)
            }
        )
        
    except Exception as e:
        logger.error(f"Error applying standard categorization: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during standard categorization",
            status_code=500
        )


@mid_tier_bp.route('/spending-insights', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_spending_insights():
    """
    Get basic spending insights for Mid-tier users
    
    Query parameters:
    - date_range: Date range for analysis (JSON string)
    - insight_types: Filter by insight types (comma-separated)
    """
    try:
        date_range = None
        if request.args.get('date_range'):
            try:
                date_range_data = json.loads(request.args.get('date_range'))
                start_date = datetime.fromisoformat(date_range_data['start_date'])
                end_date = datetime.fromisoformat(date_range_data['end_date'])
                date_range = (start_date, end_date)
            except (json.JSONDecodeError, KeyError, ValueError):
                return create_response(
                    success=False,
                    message="Invalid date_range format",
                    status_code=400
                )
        
        insight_types = None
        if request.args.get('insight_types'):
            insight_types = request.args.get('insight_types').split(',')
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        mid_tier_service = MidTierFeaturesService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.BASIC_ANALYTICS):
            return create_response(
                success=False,
                message="Basic spending insights are not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'basic_analytics'}
            )
        
        # Generate insights
        insights = mid_tier_service.generate_basic_spending_insights(current_user.id, date_range)
        
        # Filter by insight types if specified
        if insight_types:
            insights = [insight for insight in insights if insight.insight_type.value in insight_types]
        
        # Format response
        formatted_insights = []
        for insight in insights:
            formatted_insights.append({
                'insight_id': insight.insight_id,
                'insight_type': insight.insight_type.value,
                'title': insight.title,
                'description': insight.description,
                'data': insight.data,
                'impact_score': insight.impact_score,
                'priority': insight.priority,
                'is_actionable': insight.is_actionable,
                'action_description': insight.action_description,
                'created_at': insight.created_at.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Generated {len(formatted_insights)} spending insights",
            data={
                'insights': formatted_insights,
                'total_count': len(formatted_insights),
                'insight_types': [insight.insight_type.value for insight in insights]
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating spending insights: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while generating spending insights",
            status_code=500
        )


@mid_tier_bp.route('/cash-flow-forecast/6month', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def generate_6month_cash_flow_forecast():
    """
    Generate 6-month cash flow forecast for Mid-tier users
    
    Request body:
    {
        "include_confidence_intervals": true  # Optional - include confidence intervals
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'include_confidence_intervals': {'type': 'bool', 'required': False, 'default': True}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        mid_tier_service = MidTierFeaturesService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.CASH_FLOW_FORECASTING):
            return create_response(
                success=False,
                message="Cash flow forecasting is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'cash_flow_forecasting'}
            )
        
        # Generate 6-month forecast
        forecast = mid_tier_service.generate_6month_cash_flow_forecast(current_user.id)
        
        # Format response
        response_data = {
            'forecast_id': forecast.forecast_id,
            'forecast_period': forecast.forecast_period,
            'start_date': forecast.start_date.isoformat(),
            'end_date': forecast.end_date.isoformat(),
            'monthly_forecasts': forecast.monthly_forecasts,
            'projected_income': forecast.projected_income,
            'projected_expenses': forecast.projected_expenses,
            'projected_cash_flow': forecast.projected_cash_flow,
            'cash_flow_trend': forecast.cash_flow_trend,
            'model_version': forecast.model_version,
            'accuracy_score': forecast.accuracy_score,
            'last_updated': forecast.last_updated.isoformat()
        }
        
        return create_response(
            success=True,
            message=f"6-month cash flow forecast generated successfully",
            data=response_data
        )
        
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error generating 6-month cash flow forecast: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during cash flow forecasting",
            status_code=500
        )


@mid_tier_bp.route('/savings-goals', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def create_savings_goal():
    """
    Create a savings goal for Mid-tier users
    
    Request body:
    {
        "name": "Emergency Fund",
        "goal_type": "emergency_fund",
        "target_amount": 10000.0,
        "target_date": "2025-12-31",
        "current_amount": 0.0,  # Optional
        "metadata": {}  # Optional
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'name': {'type': 'str', 'required': True},
            'goal_type': {'type': 'str', 'required': True},
            'target_amount': {'type': 'float', 'required': True},
            'target_date': {'type': 'str', 'required': True},
            'current_amount': {'type': 'float', 'required': False, 'default': 0.0},
            'metadata': {'type': 'dict', 'required': False}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        mid_tier_service = MidTierFeaturesService(db_session)
        
        # Check feature access (savings goals are part of basic analytics)
        if not tier_service.has_feature_access(current_user.id, FeatureType.BASIC_ANALYTICS):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Create savings goal
        goal = mid_tier_service.create_savings_goal(current_user.id, data)
        
        return create_response(
            success=True,
            message=f"Savings goal '{goal.goal_name}' created successfully",
            data={
                'goal_id': goal.goal_id,
                'goal_name': goal.goal_name,
                'goal_type': goal.goal_type.value,
                'target_amount': goal.target_amount,
                'current_amount': goal.current_amount,
                'target_date': goal.target_date.isoformat(),
                'monthly_target': goal.monthly_target,
                'status': goal.status.value,
                'progress_percentage': goal.progress_percentage,
                'created_at': goal.created_at.isoformat()
            }
        )
        
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating savings goal: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while creating savings goal",
            status_code=500
        )


@mid_tier_bp.route('/savings-goals', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_savings_goals():
    """
    Get user's savings goals
    
    Query parameters:
    - status: Filter by goal status
    - goal_type: Filter by goal type
    """
    try:
        status_filter = request.args.get('status')
        goal_type_filter = request.args.get('goal_type')
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        mid_tier_service = MidTierFeaturesService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.BASIC_ANALYTICS):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Get savings goals
        goals = mid_tier_service._get_user_savings_goals(current_user.id)
        
        # Apply filters
        if status_filter:
            goals = [goal for goal in goals if goal.status.value == status_filter]
        
        if goal_type_filter:
            goals = [goal for goal in goals if goal.goal_type.value == goal_type_filter]
        
        # Format response
        formatted_goals = []
        for goal in goals:
            formatted_goals.append({
                'goal_id': goal.goal_id,
                'goal_name': goal.goal_name,
                'goal_type': goal.goal_type.value,
                'target_amount': goal.target_amount,
                'current_amount': goal.current_amount,
                'target_date': goal.target_date.isoformat(),
                'monthly_target': goal.monthly_target,
                'status': goal.status.value,
                'progress_percentage': goal.progress_percentage,
                'created_at': goal.created_at.isoformat(),
                'updated_at': goal.updated_at.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(formatted_goals)} savings goals",
            data={
                'goals': formatted_goals,
                'total_count': len(formatted_goals)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting savings goals: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving savings goals",
            status_code=500
        )


@mid_tier_bp.route('/savings-goals/<goal_id>/update', methods=['PUT'])
@login_required
@require_auth
@handle_api_errors
def update_savings_goal_progress(goal_id: str):
    """
    Update savings goal progress
    
    Request body:
    {
        "new_amount": 2500.0
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'new_amount': {'type': 'float', 'required': True}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        mid_tier_service = MidTierFeaturesService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.BASIC_ANALYTICS):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Update goal progress
        goal = mid_tier_service.update_savings_goal_progress(goal_id, data['new_amount'])
        
        return create_response(
            success=True,
            message=f"Savings goal progress updated successfully",
            data={
                'goal_id': goal.goal_id,
                'goal_name': goal.goal_name,
                'current_amount': goal.current_amount,
                'status': goal.status.value,
                'progress_percentage': goal.progress_percentage,
                'updated_at': goal.updated_at.isoformat()
            }
        )
        
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error updating savings goal progress: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while updating savings goal progress",
            status_code=500
        )


@mid_tier_bp.route('/savings-goals/summary', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_savings_goals_summary():
    """
    Get summary of user's savings goals
    """
    try:
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        mid_tier_service = MidTierFeaturesService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.BASIC_ANALYTICS):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Get summary
        summary = mid_tier_service.get_savings_goals_summary(current_user.id)
        
        return create_response(
            success=True,
            message="Savings goals summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"Error getting savings goals summary: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving savings goals summary",
            status_code=500
        )


@mid_tier_bp.route('/features/summary', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_mid_tier_features_summary():
    """
    Get summary of available Mid-tier features and usage
    """
    try:
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        
        # Get user's tier
        user_tier = tier_service.get_user_tier(current_user.id)
        
        # Check if user has Mid-tier or higher
        if user_tier not in [SubscriptionTier.MID_TIER, SubscriptionTier.PROFESSIONAL]:
            return create_response(
                success=False,
                message="Mid-tier features are not available in your current tier. Please upgrade to Mid-tier or higher.",
                status_code=403,
                data={'upgrade_required': True, 'current_tier': user_tier.value}
            )
        
        # Get feature access
        features = {}
        for feature in FeatureType:
            features[feature.value] = tier_service.has_feature_access(current_user.id, feature)
        
        # Get feature limits
        limits = tier_service.get_feature_limits(current_user.id)
        
        # Generate feature summary
        feature_summary = {
            'standard_categorization': {
                'available': features.get('standard_categorization', False),
                'description': 'Automatic transaction categorization using standard patterns',
                'usage': 'Apply to transactions for automatic category suggestions'
            },
            'basic_spending_insights': {
                'available': features.get('basic_analytics', False),
                'description': 'Basic spending insights and trend analysis',
                'usage': 'Get actionable insights about your spending patterns'
            },
            'cash_flow_forecasting_6month': {
                'available': features.get('cash_flow_forecasting', False),
                'description': '6-month cash flow forecasting with trend analysis',
                'usage': 'Generate 6-month cash flow projections'
            },
            'savings_goal_tracking': {
                'available': features.get('basic_analytics', False),
                'description': 'Track and manage savings goals with progress monitoring',
                'usage': 'Create and track progress towards financial goals'
            }
        }
        
        return create_response(
            success=True,
            message="Mid-tier features summary retrieved successfully",
            data={
                'current_tier': user_tier.value,
                'features': feature_summary,
                'limits': limits,
                'upgrade_recommendations': [
                    "Upgrade to Professional for advanced AI categorization",
                    "Upgrade to Professional for detailed merchant analysis",
                    "Upgrade to Professional for 12+ month cash flow forecasting",
                    "Upgrade to Professional for unlimited custom categories"
                ] if user_tier == SubscriptionTier.MID_TIER else []
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting Mid-tier features summary: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving features summary",
            status_code=500
        )


@mid_tier_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for Mid-tier features
    """
    try:
        return create_response(
            success=True,
            message="Mid-tier features service is healthy",
            data={
                'service': 'mid_tier_features',
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'available_features': [
                    'standard_categorization',
                    'basic_spending_insights',
                    'cash_flow_forecasting_6month',
                    'savings_goal_tracking'
                ]
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            success=False,
            message="Mid-tier features service is unhealthy",
            status_code=500,
            data={
                'service': 'mid_tier_features',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


def register_mid_tier_routes(app):
    """Register Mid-tier feature routes with the Flask app"""
    app.register_blueprint(mid_tier_bp)
    logger.info("Mid-tier feature routes registered successfully") 