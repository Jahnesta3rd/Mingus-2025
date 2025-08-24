"""
Subscription Tier Features API Routes

This module provides API endpoints for Professional tier features including
advanced AI-powered categorization, custom category creation and rules,
detailed merchant analysis, and cash flow forecasting.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json

from backend.services.subscription_tier_service import (
    SubscriptionTierService, SubscriptionTier, FeatureType,
    CategoryRuleType, CustomCategory, CategoryRule, MerchantAnalysis,
    CashFlowForecast, AICategorizationResult
)
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.models.bank_account_models import PlaidTransaction

logger = logging.getLogger(__name__)

subscription_tier_bp = Blueprint('subscription_tier', __name__, url_prefix='/api/subscription-tier')


@subscription_tier_bp.route('/tier/info', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_user_tier_info():
    """
    Get user's subscription tier information and feature access
    
    Returns:
    - Current tier
    - Available features
    - Feature limits
    - Upgrade recommendations
    """
    try:
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        
        # Get user's tier
        user_tier = tier_service.get_user_tier(current_user.id)
        
        # Get feature access
        features = {}
        for feature in FeatureType:
            features[feature.value] = tier_service.has_feature_access(current_user.id, feature)
        
        # Get feature limits
        limits = tier_service.get_feature_limits(current_user.id)
        
        # Generate upgrade recommendations
        upgrade_recommendations = []
        if user_tier == SubscriptionTier.BUDGET:
            upgrade_recommendations = [
                "Upgrade to Mid-tier for AI-powered categorization",
                "Upgrade to Mid-tier for custom category creation",
                "Upgrade to Professional for advanced merchant analysis",
                "Upgrade to Professional for cash flow forecasting"
            ]
        elif user_tier == SubscriptionTier.MID_TIER:
            upgrade_recommendations = [
                "Upgrade to Professional for detailed merchant analysis",
                "Upgrade to Professional for cash flow forecasting",
                "Upgrade to Professional for unlimited custom categories"
            ]
        
        return create_response(
            success=True,
            message="User tier information retrieved successfully",
            data={
                'current_tier': user_tier.value,
                'features': features,
                'limits': limits,
                'upgrade_recommendations': upgrade_recommendations
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting user tier info: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving tier information",
            status_code=500
        )


@subscription_tier_bp.route('/ai-categorization/apply', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def apply_ai_categorization():
    """
    Apply AI-powered categorization to transactions
    
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
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.AI_CATEGORIZATION):
            return create_response(
                success=False,
                message="AI categorization is not available in your current tier. Please upgrade to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'ai_categorization'}
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
        
        # Apply AI categorization
        results = tier_service.apply_ai_categorization(current_user.id, transactions)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'transaction_id': result.transaction_id,
                'original_category': result.original_category,
                'ai_category': result.ai_category,
                'confidence_score': result.confidence_score,
                'categorization_method': result.categorization_method,
                'reasoning': result.reasoning,
                'alternatives': result.alternatives,
                'created_at': result.created_at.isoformat()
            })
        
        # Save changes if auto-apply is enabled
        if data.get('auto_apply', True):
            db_session.commit()
        
        return create_response(
            success=True,
            message=f"AI categorization applied to {len(formatted_results)} transactions",
            data={
                'results': formatted_results,
                'total_processed': len(formatted_results),
                'auto_applied': data.get('auto_apply', True)
            }
        )
        
    except Exception as e:
        logger.error(f"Error applying AI categorization: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during AI categorization",
            status_code=500
        )


@subscription_tier_bp.route('/custom-categories', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def create_custom_category():
    """
    Create a custom category with rules
    
    Request body:
    {
        "name": "Custom Category Name",
        "parent_category": "parent_category",  # Optional
        "color": "#FF6B6B",  # Optional
        "icon": "shopping",  # Optional
        "description": "Category description",  # Optional
        "rules": [  # Optional
            {
                "rule_type": "merchant_name",
                "conditions": {
                    "merchant_pattern": "amazon"
                },
                "priority": 1,
                "is_active": true
            }
        ]
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'name': {'type': 'str', 'required': True},
            'parent_category': {'type': 'str', 'required': False},
            'color': {'type': 'str', 'required': False},
            'icon': {'type': 'str', 'required': False},
            'description': {'type': 'str', 'required': False},
            'rules': {'type': 'list', 'required': False}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.CUSTOM_CATEGORIES):
            return create_response(
                success=False,
                message="Custom categories are not available in your current tier. Please upgrade to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'custom_categories'}
            )
        
        # Create custom category
        category = tier_service.create_custom_category(current_user.id, data)
        
        return create_response(
            success=True,
            message=f"Custom category '{category.category_name}' created successfully",
            data={
                'category_id': category.category_id,
                'category_name': category.category_name,
                'parent_category': category.parent_category,
                'color': category.color,
                'icon': category.icon,
                'description': category.description,
                'rules_count': len(category.rules),
                'created_at': category.created_at.isoformat()
            }
        )
        
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error creating custom category: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while creating custom category",
            status_code=500
        )


@subscription_tier_bp.route('/custom-categories', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_custom_categories():
    """
    Get user's custom categories
    
    Query parameters:
    - active_only: Filter to active categories only
    """
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.CUSTOM_CATEGORIES):
            return create_response(
                success=False,
                message="Custom categories are not available in your current tier. Please upgrade to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'custom_categories'}
            )
        
        # Get custom categories
        categories = tier_service._get_user_custom_categories(current_user.id)
        
        # Filter by active status if requested
        if active_only:
            categories = [cat for cat in categories if cat.is_active]
        
        # Format response
        formatted_categories = []
        for category in categories:
            formatted_categories.append({
                'category_id': category.category_id,
                'category_name': category.category_name,
                'parent_category': category.parent_category,
                'color': category.color,
                'icon': category.icon,
                'description': category.description,
                'is_active': category.is_active,
                'rules_count': len(category.rules),
                'created_at': category.created_at.isoformat(),
                'updated_at': category.updated_at.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(formatted_categories)} custom categories",
            data={
                'categories': formatted_categories,
                'total_count': len(formatted_categories)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting custom categories: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving custom categories",
            status_code=500
        )


@subscription_tier_bp.route('/merchant-analysis/<merchant_name>', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def analyze_merchant(merchant_name: str):
    """
    Perform detailed merchant analysis
    
    Path parameters:
    - merchant_name: Name of the merchant to analyze
    
    Query parameters:
    - analysis_period: Period for analysis (months)
    """
    try:
        analysis_period = int(request.args.get('analysis_period', 12))
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.MERCHANT_ANALYSIS):
            return create_response(
                success=False,
                message="Merchant analysis is not available in your current tier. Please upgrade to Professional tier to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'merchant_analysis'}
            )
        
        # Perform merchant analysis
        analysis = tier_service.analyze_merchant(current_user.id, merchant_name)
        
        return create_response(
            success=True,
            message=f"Merchant analysis completed for '{merchant_name}'",
            data={
                'merchant_id': analysis.merchant_id,
                'merchant_name': analysis.merchant_name,
                'standardized_name': analysis.standardized_name,
                'merchant_type': analysis.merchant_type,
                'category': analysis.category,
                'subcategory': analysis.subcategory,
                'total_transactions': analysis.total_transactions,
                'total_amount': analysis.total_amount,
                'average_amount': analysis.average_amount,
                'first_transaction': analysis.first_transaction.isoformat(),
                'last_transaction': analysis.last_transaction.isoformat(),
                'spending_frequency': analysis.spending_frequency,
                'spending_consistency': analysis.spending_consistency,
                'seasonal_patterns': analysis.seasonal_patterns,
                'merchant_score': analysis.merchant_score,
                'risk_level': analysis.risk_level,
                'fraud_indicators': analysis.fraud_indicators,
                'business_type': analysis.business_type,
                'location': analysis.location,
                'website': analysis.website,
                'phone': analysis.phone,
                'created_at': analysis.created_at.isoformat(),
                'updated_at': analysis.updated_at.isoformat()
            }
        )
        
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error analyzing merchant: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during merchant analysis",
            status_code=500
        )


@subscription_tier_bp.route('/cash-flow-forecast', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def generate_cash_flow_forecast():
    """
    Generate cash flow forecast
    
    Request body:
    {
        "forecast_months": 12,  # Optional - number of months to forecast
        "include_confidence_intervals": true  # Optional - include confidence intervals
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'forecast_months': {'type': 'int', 'required': False, 'default': 12},
            'include_confidence_intervals': {'type': 'bool', 'required': False, 'default': True}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.CASH_FLOW_FORECASTING):
            return create_response(
                success=False,
                message="Cash flow forecasting is not available in your current tier. Please upgrade to Professional tier to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'cash_flow_forecasting'}
            )
        
        # Generate forecast
        forecast = tier_service.generate_cash_flow_forecast(
            current_user.id, 
            data.get('forecast_months', 12)
        )
        
        # Format response
        response_data = {
            'forecast_id': forecast.forecast_id,
            'forecast_period': forecast.forecast_period,
            'start_date': forecast.start_date.isoformat(),
            'end_date': forecast.end_date.isoformat(),
            'monthly_forecasts': forecast.monthly_forecasts,
            'projected_income': forecast.projected_income,
            'income_growth_rate': forecast.income_growth_rate,
            'income_volatility': forecast.income_volatility,
            'projected_expenses': forecast.projected_expenses,
            'expense_growth_rate': forecast.expense_growth_rate,
            'expense_volatility': forecast.expense_volatility,
            'projected_cash_flow': forecast.projected_cash_flow,
            'cash_flow_trend': forecast.cash_flow_trend,
            'break_even_date': forecast.break_even_date.isoformat() if forecast.break_even_date else None,
            'model_version': forecast.model_version,
            'accuracy_score': forecast.accuracy_score,
            'last_updated': forecast.last_updated.isoformat()
        }
        
        # Include confidence intervals if requested
        if data.get('include_confidence_intervals', True):
            response_data['confidence_intervals'] = forecast.confidence_intervals
        
        return create_response(
            success=True,
            message=f"Cash flow forecast generated for {forecast.forecast_period} months",
            data=response_data
        )
        
    except ValueError as e:
        return create_response(
            success=False,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error generating cash flow forecast: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during cash flow forecasting",
            status_code=500
        )


@subscription_tier_bp.route('/cash-flow-forecast/history', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_forecast_history():
    """
    Get user's cash flow forecast history
    
    Query parameters:
    - limit: Number of forecasts to return
    - include_details: Include detailed forecast data
    """
    try:
        limit = int(request.args.get('limit', 10))
        include_details = request.args.get('include_details', 'false').lower() == 'true'
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        
        # Check feature access
        if not tier_service.has_feature_access(current_user.id, FeatureType.CASH_FLOW_FORECASTING):
            return create_response(
                success=False,
                message="Cash flow forecasting is not available in your current tier. Please upgrade to Professional tier to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'cash_flow_forecasting'}
            )
        
        # This would query the database for forecast history
        # For now, return empty list
        forecasts = []
        
        return create_response(
            success=True,
            message="Forecast history retrieved successfully",
            data={
                'forecasts': forecasts,
                'total_count': len(forecasts)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting forecast history: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving forecast history",
            status_code=500
        )


@subscription_tier_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for subscription tier features
    """
    try:
        return create_response(
            success=True,
            message="Subscription tier features service is healthy",
            data={
                'service': 'subscription_tier_features',
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'available_features': [
                    'ai_categorization',
                    'custom_categories', 
                    'merchant_analysis',
                    'cash_flow_forecasting'
                ]
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            success=False,
            message="Subscription tier features service is unhealthy",
            status_code=500,
            data={
                'service': 'subscription_tier_features',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


def register_subscription_tier_routes(app):
    """Register subscription tier feature routes with the Flask app"""
    app.register_blueprint(subscription_tier_bp)
    logger.info("Subscription tier feature routes registered successfully") 