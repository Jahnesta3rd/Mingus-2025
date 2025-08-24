"""
Questionnaire Goals Integration API Routes

This module provides API endpoints for integrating questionnaire data with
the savings goals system, automatically creating goals based on questionnaire
responses for users who have that capability.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json

from backend.services.questionnaire_goals_integration_service import (
    QuestionnaireGoalsIntegrationService, QuestionnaireGoalType,
    QuestionnaireGoalData, QuestionnaireGoalRecommendation
)
from backend.services.subscription_tier_service import SubscriptionTierService, SubscriptionTier, FeatureType
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.models.financial_questionnaire_submission import FinancialQuestionnaireSubmission

logger = logging.getLogger(__name__)

questionnaire_goals_bp = Blueprint('questionnaire_goals', __name__, url_prefix='/api/questionnaire-goals')


@questionnaire_goals_bp.route('/create-from-questionnaire', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def create_goals_from_questionnaire():
    """
    Create savings goals based on questionnaire data for users with capability
    
    Request body:
    {
        "questionnaire_data": {
            "monthly_income": 5000,
            "monthly_expenses": 3000,
            "current_savings": 5000,
            "total_debt": 15000,
            "risk_tolerance": 3,
            "financial_goals": ["emergency_fund", "debt_payoff"]
        },
        "auto_create": true  # Optional - automatically create goals
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'questionnaire_data': {'type': 'dict', 'required': True},
            'auto_create': {'type': 'bool', 'required': False, 'default': True}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        questionnaire_goals_service = QuestionnaireGoalsIntegrationService(db_session)
        
        # Check if user has goal capability
        if not questionnaire_goals_service._user_has_goal_capability(current_user.id):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Create goals from questionnaire data
        created_goals = questionnaire_goals_service.create_goals_from_questionnaire(
            current_user.id, 
            data['questionnaire_data']
        )
        
        # Format response
        formatted_goals = []
        for goal in created_goals:
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
                'metadata': goal.metadata
            })
        
        return create_response(
            success=True,
            message=f"Successfully created {len(formatted_goals)} savings goals from questionnaire data",
            data={
                'goals': formatted_goals,
                'total_created': len(formatted_goals),
                'auto_created': data.get('auto_create', True)
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating goals from questionnaire: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while creating goals from questionnaire",
            status_code=500
        )


@questionnaire_goals_bp.route('/analyze-questionnaire', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def analyze_questionnaire_for_goals():
    """
    Analyze questionnaire data and provide goal recommendations without creating goals
    
    Request body:
    {
        "questionnaire_data": {
            "monthly_income": 5000,
            "monthly_expenses": 3000,
            "current_savings": 5000,
            "total_debt": 15000,
            "risk_tolerance": 3,
            "financial_goals": ["emergency_fund", "debt_payoff"]
        }
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'questionnaire_data': {'type': 'dict', 'required': True}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        questionnaire_goals_service = QuestionnaireGoalsIntegrationService(db_session)
        
        # Check if user has goal capability
        if not questionnaire_goals_service._user_has_goal_capability(current_user.id):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Analyze questionnaire data for goal recommendations
        recommendations = questionnaire_goals_service._analyze_questionnaire_for_goals(
            data['questionnaire_data']
        )
        
        # Format recommendations
        formatted_recommendations = []
        for recommendation in recommendations:
            goal_data = recommendation.goal_data
            formatted_recommendations.append({
                'goal_type': goal_data.goal_type.value,
                'target_amount': goal_data.target_amount,
                'current_amount': goal_data.current_amount,
                'target_date': goal_data.target_date.isoformat(),
                'priority': goal_data.priority,
                'description': goal_data.description,
                'motivation': goal_data.motivation,
                'monthly_target': goal_data.monthly_target,
                'confidence_score': goal_data.confidence_score,
                'reasoning': recommendation.reasoning,
                'expected_impact': recommendation.expected_impact,
                'difficulty_level': recommendation.difficulty_level,
                'time_to_completion': recommendation.time_to_completion,
                'suggested_timeline': recommendation.suggested_timeline,
                'source_data': goal_data.source_data
            })
        
        return create_response(
            success=True,
            message=f"Analyzed questionnaire data and found {len(formatted_recommendations)} goal recommendations",
            data={
                'recommendations': formatted_recommendations,
                'total_recommendations': len(formatted_recommendations),
                'questionnaire_data': data['questionnaire_data']
            }
        )
        
    except Exception as e:
        logger.error(f"Error analyzing questionnaire for goals: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while analyzing questionnaire data",
            status_code=500
        )


@questionnaire_goals_bp.route('/summary', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_questionnaire_goals_summary():
    """
    Get summary of goals created from questionnaire data
    """
    try:
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        questionnaire_goals_service = QuestionnaireGoalsIntegrationService(db_session)
        
        # Check if user has goal capability
        if not questionnaire_goals_service._user_has_goal_capability(current_user.id):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Get questionnaire goals summary
        summary = questionnaire_goals_service.get_questionnaire_goals_summary(current_user.id)
        
        return create_response(
            success=True,
            message="Questionnaire goals summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"Error getting questionnaire goals summary: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving questionnaire goals summary",
            status_code=500
        )


@questionnaire_goals_bp.route('/update-from-questionnaire', methods=['PUT'])
@login_required
@require_auth
@handle_api_errors
def update_goals_from_questionnaire():
    """
    Update existing goals based on new questionnaire data
    
    Request body:
    {
        "updated_questionnaire_data": {
            "monthly_income": 6000,
            "monthly_expenses": 3500,
            "current_savings": 8000,
            "total_debt": 12000,
            "risk_tolerance": 4,
            "financial_goals": ["emergency_fund", "investment"]
        }
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'updated_questionnaire_data': {'type': 'dict', 'required': True}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        questionnaire_goals_service = QuestionnaireGoalsIntegrationService(db_session)
        
        # Check if user has goal capability
        if not questionnaire_goals_service._user_has_goal_capability(current_user.id):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Update goals from new questionnaire data
        updated_goals = questionnaire_goals_service.update_questionnaire_goals(
            current_user.id, 
            data['updated_questionnaire_data']
        )
        
        # Format response
        formatted_goals = []
        for goal in updated_goals:
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
                'updated_at': goal.updated_at.isoformat(),
                'metadata': goal.metadata
            })
        
        return create_response(
            success=True,
            message=f"Successfully updated {len(formatted_goals)} savings goals from new questionnaire data",
            data={
                'goals': formatted_goals,
                'total_updated': len(formatted_goals),
                'updated_questionnaire_data': data['updated_questionnaire_data']
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating goals from questionnaire: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while updating goals from questionnaire",
            status_code=500
        )


@questionnaire_goals_bp.route('/questionnaire-history', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_questionnaire_history():
    """
    Get history of questionnaire submissions and associated goals
    """
    try:
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        questionnaire_goals_service = QuestionnaireGoalsIntegrationService(db_session)
        
        # Check if user has goal capability
        if not questionnaire_goals_service._user_has_goal_capability(current_user.id):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Get questionnaire submission history
        submissions = db_session.query(FinancialQuestionnaireSubmission).filter(
            FinancialQuestionnaireSubmission.user_id == current_user.id
        ).order_by(FinancialQuestionnaireSubmission.submitted_at.desc()).all()
        
        # Format submissions with associated goals
        formatted_history = []
        for submission in submissions:
            # Get goals created from this submission
            submission_goals = []
            if hasattr(submission, 'goals_created'):
                for goal in submission.goals_created:
                    submission_goals.append({
                        'goal_id': goal.goal_id,
                        'goal_name': goal.goal_name,
                        'goal_type': goal.goal_type.value,
                        'target_amount': goal.target_amount,
                        'current_amount': goal.current_amount,
                        'progress_percentage': goal.progress_percentage,
                        'status': goal.status.value
                    })
            
            formatted_history.append({
                'submission_id': submission.id,
                'submitted_at': submission.submitted_at.isoformat(),
                'financial_health_score': submission.financial_health_score,
                'financial_health_level': submission.financial_health_level,
                'monthly_income': submission.monthly_income,
                'monthly_expenses': submission.monthly_expenses,
                'current_savings': submission.current_savings,
                'total_debt': submission.total_debt,
                'risk_tolerance': submission.risk_tolerance,
                'financial_goals': submission.financial_goals,
                'goals_created': submission_goals,
                'total_goals_created': len(submission_goals)
            })
        
        return create_response(
            success=True,
            message="Questionnaire history retrieved successfully",
            data={
                'history': formatted_history,
                'total_submissions': len(formatted_history)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting questionnaire history: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving questionnaire history",
            status_code=500
        )


@questionnaire_goals_bp.route('/auto-create-settings', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_auto_create_settings():
    """
    Get user's auto-create settings for questionnaire goals
    """
    try:
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        questionnaire_goals_service = QuestionnaireGoalsIntegrationService(db_session)
        
        # Check if user has goal capability
        if not questionnaire_goals_service._user_has_goal_capability(current_user.id):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Get user's auto-create settings (this would be stored in user preferences)
        # For now, return default settings
        settings = {
            'auto_create_enabled': True,
            'goal_types_enabled': [
                'emergency_fund',
                'debt_payoff',
                'savings_growth',
                'investment_start',
                'retirement_planning'
            ],
            'min_confidence_score': 0.6,
            'max_goals_per_questionnaire': 5,
            'update_existing_goals': True,
            'notifications_enabled': True
        }
        
        return create_response(
            success=True,
            message="Auto-create settings retrieved successfully",
            data=settings
        )
        
    except Exception as e:
        logger.error(f"Error getting auto-create settings: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while retrieving auto-create settings",
            status_code=500
        )


@questionnaire_goals_bp.route('/auto-create-settings', methods=['PUT'])
@login_required
@require_auth
@handle_api_errors
def update_auto_create_settings():
    """
    Update user's auto-create settings for questionnaire goals
    
    Request body:
    {
        "auto_create_enabled": true,
        "goal_types_enabled": ["emergency_fund", "debt_payoff"],
        "min_confidence_score": 0.7,
        "max_goals_per_questionnaire": 3,
        "update_existing_goals": true,
        "notifications_enabled": true
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'auto_create_enabled': {'type': 'bool', 'required': False},
            'goal_types_enabled': {'type': 'list', 'required': False},
            'min_confidence_score': {'type': 'float', 'required': False},
            'max_goals_per_questionnaire': {'type': 'int', 'required': False},
            'update_existing_goals': {'type': 'bool', 'required': False},
            'notifications_enabled': {'type': 'bool', 'required': False}
        })
        
        db_session = current_app.db.session
        tier_service = SubscriptionTierService(db_session)
        questionnaire_goals_service = QuestionnaireGoalsIntegrationService(db_session)
        
        # Check if user has goal capability
        if not questionnaire_goals_service._user_has_goal_capability(current_user.id):
            return create_response(
                success=False,
                message="Savings goal tracking is not available in your current tier. Please upgrade to Mid-tier or higher to access this feature.",
                status_code=403,
                data={'upgrade_required': True, 'feature': 'savings_goals'}
            )
        
        # Update user's auto-create settings (this would be stored in user preferences)
        # For now, just return success
        updated_settings = {
            'auto_create_enabled': data.get('auto_create_enabled', True),
            'goal_types_enabled': data.get('goal_types_enabled', [
                'emergency_fund', 'debt_payoff', 'savings_growth', 'investment_start', 'retirement_planning'
            ]),
            'min_confidence_score': data.get('min_confidence_score', 0.6),
            'max_goals_per_questionnaire': data.get('max_goals_per_questionnaire', 5),
            'update_existing_goals': data.get('update_existing_goals', True),
            'notifications_enabled': data.get('notifications_enabled', True)
        }
        
        return create_response(
            success=True,
            message="Auto-create settings updated successfully",
            data=updated_settings
        )
        
    except Exception as e:
        logger.error(f"Error updating auto-create settings: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error while updating auto-create settings",
            status_code=500
        )


@questionnaire_goals_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for questionnaire goals integration
    """
    try:
        return create_response(
            success=True,
            message="Questionnaire goals integration service is healthy",
            data={
                'service': 'questionnaire_goals_integration',
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'available_features': [
                    'create_goals_from_questionnaire',
                    'analyze_questionnaire_for_goals',
                    'update_goals_from_questionnaire',
                    'questionnaire_history',
                    'auto_create_settings'
                ]
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            success=False,
            message="Questionnaire goals integration service is unhealthy",
            status_code=500,
            data={
                'service': 'questionnaire_goals_integration',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


def register_questionnaire_goals_routes(app):
    """Register questionnaire goals integration routes with the Flask app"""
    app.register_blueprint(questionnaire_goals_bp)
    logger.info("Questionnaire goals integration routes registered successfully") 