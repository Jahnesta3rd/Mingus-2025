"""
Financial Health Scoring API Routes

This module provides comprehensive API routes for financial health scoring including
user financial health assessment based on banking data, progress tracking over time,
goal achievement rates, risk factor identification, and success metric correlations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.analytics.financial_health_scoring import (
    FinancialHealthScoring, FinancialHealthMetric, RiskLevel, GoalStatus
)
from backend.security.access_control_service import AccessControlService, Permission
from backend.security.audit_logging import AuditLoggingService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
financial_health_bp = Blueprint('financial_health', __name__, url_prefix='/api/financial-health')


@financial_health_bp.route('/score', methods=['POST'])
@login_required
@require_auth
def calculate_health_score():
    """Calculate financial health score for current user"""
    try:
        data = request.get_json()
        banking_data = data.get('banking_data') if data else None
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Calculate health score
        score_id = health_service.calculate_financial_health_score(current_user.id, banking_data)
        
        return success_response({
            'score_id': score_id,
            'message': 'Financial health score calculated successfully'
        }, "Financial health score calculated successfully")
        
    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        return error_response("Failed to calculate financial health score", 500)


@financial_health_bp.route('/score/<user_id>', methods=['GET'])
@login_required
@require_auth
def get_health_score(user_id):
    """Get financial health score for a user (admin only)"""
    try:
        # Check admin permission
        if not current_user.has_role('admin'):
            return error_response("Admin access required", 403)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Get latest health score
        user_scores = [score for score in health_service.health_scores.values() if score.user_id == user_id]
        if not user_scores:
            return error_response("No health score found for user", 404)
        
        latest_score = max(user_scores, key=lambda x: x.score_date)
        
        score_data = {
            'score_id': latest_score.score_id,
            'user_id': latest_score.user_id,
            'overall_score': latest_score.overall_score,
            'score_date': latest_score.score_date.isoformat(),
            'metrics': latest_score.metrics,
            'risk_factors': latest_score.risk_factors,
            'recommendations': latest_score.recommendations,
            'goal_progress': latest_score.goal_progress,
            'trend_direction': latest_score.trend_direction,
            'confidence_level': latest_score.confidence_level
        }
        
        return success_response(score_data, "Financial health score retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting health score: {e}")
        return error_response("Failed to retrieve financial health score", 500)


@financial_health_bp.route('/score', methods=['GET'])
@login_required
@require_auth
def get_current_user_health_score():
    """Get financial health score for current user"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Get latest health score
        user_scores = [score for score in health_service.health_scores.values() if score.user_id == current_user.id]
        if not user_scores:
            return error_response("No health score found. Please calculate your health score first.", 404)
        
        latest_score = max(user_scores, key=lambda x: x.score_date)
        
        score_data = {
            'score_id': latest_score.score_id,
            'overall_score': latest_score.overall_score,
            'score_date': latest_score.score_date.isoformat(),
            'metrics': latest_score.metrics,
            'risk_factors': latest_score.risk_factors,
            'recommendations': latest_score.recommendations,
            'goal_progress': latest_score.goal_progress,
            'trend_direction': latest_score.trend_direction,
            'confidence_level': latest_score.confidence_level
        }
        
        return success_response(score_data, "Financial health score retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting current user health score: {e}")
        return error_response("Failed to retrieve financial health score", 500)


@financial_health_bp.route('/goals', methods=['POST'])
@login_required
@require_auth
def create_financial_goal():
    """Create a new financial goal"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        goal_type = data.get('goal_type')
        goal_name = data.get('goal_name')
        target_amount = data.get('target_amount')
        target_date_str = data.get('target_date')
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not all([goal_type, goal_name, target_amount, target_date_str]):
            return error_response("goal_type, goal_name, target_amount, and target_date are required", 400)
        
        # Parse target date
        try:
            target_date = datetime.fromisoformat(target_date_str.replace('Z', '+00:00'))
        except ValueError:
            return error_response("Invalid target date format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Create financial goal
        goal_id = health_service.create_financial_goal(
            user_id=current_user.id,
            goal_type=goal_type,
            goal_name=goal_name,
            target_amount=target_amount,
            target_date=target_date,
            metadata=metadata
        )
        
        return success_response({
            'goal_id': goal_id,
            'message': 'Financial goal created successfully'
        }, "Financial goal created successfully")
        
    except Exception as e:
        logger.error(f"Error creating financial goal: {e}")
        return error_response("Failed to create financial goal", 500)


@financial_health_bp.route('/goals', methods=['GET'])
@login_required
@require_auth
def get_financial_goals():
    """Get financial goals for current user"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Get user goals
        user_goals = [goal for goal in health_service.financial_goals.values() if goal.user_id == current_user.id]
        
        goals_data = [
            {
                'goal_id': goal.goal_id,
                'goal_type': goal.goal_type,
                'goal_name': goal.goal_name,
                'target_amount': goal.target_amount,
                'current_amount': goal.current_amount,
                'target_date': goal.target_date.isoformat(),
                'created_date': goal.created_date.isoformat(),
                'status': goal.status.value,
                'progress_percentage': goal.progress_percentage,
                'risk_level': goal.risk_level.value
            }
            for goal in user_goals
        ]
        
        return success_response({
            'goals': goals_data,
            'total_goals': len(goals_data)
        }, "Financial goals retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting financial goals: {e}")
        return error_response("Failed to retrieve financial goals", 500)


@financial_health_bp.route('/goals/<goal_id>/progress', methods=['PUT'])
@login_required
@require_auth
def update_goal_progress(goal_id):
    """Update goal progress"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        current_amount = data.get('current_amount')
        
        # Validate required fields
        if current_amount is None:
            return error_response("current_amount is required", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Update goal progress
        success = health_service.update_goal_progress(goal_id, current_amount)
        
        if not success:
            return error_response("Goal not found or update failed", 404)
        
        return success_response({
            'goal_id': goal_id,
            'message': 'Goal progress updated successfully'
        }, "Goal progress updated successfully")
        
    except Exception as e:
        logger.error(f"Error updating goal progress: {e}")
        return error_response("Failed to update goal progress", 500)


@financial_health_bp.route('/risk-factors', methods=['GET'])
@login_required
@require_auth
def get_risk_factors():
    """Get risk factors for current user"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Get risk factors
        risk_factors = health_service.identify_risk_factors(current_user.id)
        
        return success_response({
            'risk_factors': risk_factors,
            'total_risk_factors': len(risk_factors)
        }, "Risk factors retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting risk factors: {e}")
        return error_response("Failed to retrieve risk factors", 500)


@financial_health_bp.route('/progress', methods=['POST'])
@login_required
@require_auth
def track_progress():
    """Track progress for a specific metric"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        metric_name = data.get('metric_name')
        current_value = data.get('current_value')
        period_type = data.get('period_type', 'monthly')
        
        # Validate required fields
        if not all([metric_name, current_value is not None]):
            return error_response("metric_name and current_value are required", 400)
        
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Track progress
        tracking_id = health_service.track_progress(
            user_id=current_user.id,
            metric_name=metric_name,
            current_value=current_value,
            period_type=period_type
        )
        
        return success_response({
            'tracking_id': tracking_id,
            'message': 'Progress tracked successfully'
        }, "Progress tracked successfully")
        
    except Exception as e:
        logger.error(f"Error tracking progress: {e}")
        return error_response("Failed to track progress", 500)


@financial_health_bp.route('/progress', methods=['GET'])
@login_required
@require_auth
def get_progress_tracking():
    """Get progress tracking data for current user"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Get user progress tracking
        user_progress = [track for track in health_service.progress_tracking.values() if track.user_id == current_user.id]
        
        progress_data = [
            {
                'tracking_id': track.tracking_id,
                'metric_name': track.metric_name,
                'current_value': track.current_value,
                'previous_value': track.previous_value,
                'change_percentage': track.change_percentage,
                'tracking_date': track.tracking_date.isoformat(),
                'period_type': track.period_type,
                'trend_direction': track.trend_direction
            }
            for track in user_progress
        ]
        
        return success_response({
            'progress_tracking': progress_data,
            'total_entries': len(progress_data)
        }, "Progress tracking data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting progress tracking: {e}")
        return error_response("Failed to retrieve progress tracking data", 500)


@financial_health_bp.route('/dashboard', methods=['GET'])
@login_required
@require_auth
def get_financial_health_dashboard():
    """Get comprehensive financial health dashboard data"""
    try:
        # Initialize services
        db_session = current_app.db.session
        access_control_service = AccessControlService(db_session, None, None, None)
        audit_service = AuditLoggingService(db_session)
        health_service = FinancialHealthScoring(db_session, access_control_service, audit_service)
        
        # Get dashboard data
        dashboard_data = health_service.get_financial_health_dashboard(current_user.id)
        
        if 'error' in dashboard_data:
            return error_response(dashboard_data['error'], 400)
        
        return success_response(dashboard_data, "Financial health dashboard data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting financial health dashboard: {e}")
        return error_response("Failed to retrieve financial health dashboard data", 500)


@financial_health_bp.route('/metrics', methods=['GET'])
@login_required
@require_auth
def get_financial_health_metrics():
    """Get available financial health metrics"""
    try:
        metrics = [
            {
                'metric': metric.value,
                'name': metric.value.replace('_', ' ').title(),
                'description': f'Financial health metric for {metric.value.replace("_", " ")}'
            }
            for metric in FinancialHealthMetric
        ]
        
        return success_response({
            'metrics': metrics,
            'total_metrics': len(metrics)
        }, "Financial health metrics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting financial health metrics: {e}")
        return error_response("Failed to retrieve financial health metrics", 500)


@financial_health_bp.route('/risk-levels', methods=['GET'])
@login_required
@require_auth
def get_risk_levels():
    """Get available risk levels"""
    try:
        risk_levels = [
            {
                'level': level.value,
                'name': level.value.title(),
                'description': f'Risk level: {level.value}'
            }
            for level in RiskLevel
        ]
        
        return success_response({
            'risk_levels': risk_levels,
            'total_levels': len(risk_levels)
        }, "Risk levels retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting risk levels: {e}")
        return error_response("Failed to retrieve risk levels", 500)


@financial_health_bp.route('/goal-statuses', methods=['GET'])
@login_required
@require_auth
def get_goal_statuses():
    """Get available goal statuses"""
    try:
        goal_statuses = [
            {
                'status': status.value,
                'name': status.value.replace('_', ' ').title(),
                'description': f'Goal status: {status.value.replace("_", " ")}'
            }
            for status in GoalStatus
        ]
        
        return success_response({
            'goal_statuses': goal_statuses,
            'total_statuses': len(goal_statuses)
        }, "Goal statuses retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting goal statuses: {e}")
        return error_response("Failed to retrieve goal statuses", 500) 