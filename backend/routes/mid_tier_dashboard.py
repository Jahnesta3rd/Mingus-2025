"""
Mid-Tier Dashboard API Routes

This module provides API endpoints for Mid-tier dashboard features including
current balances for up to 2 accounts, 6-month cash flow projections,
standard spending categories and insights, savings goal progress tracking,
and basic bill tracking with key dates and reminders.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.dashboard.mid_tier_dashboard_service import (
    MidTierDashboardService, DashboardWidgetType, AccountBalance, 
    CashFlowProjection, SpendingCategoryInsight, SavingsGoalProgress,
    BillReminder, KeyDate, RealTimeAlert
)
from backend.services.feature_access_service import FeatureAccessService
from backend.services.real_time_updates_service import RealTimeUpdatesService
from backend.models.subscription import SubscriptionTier
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.utils.response import success_response, error_response

logger = logging.getLogger(__name__)

# Create Blueprint
mid_tier_dashboard_bp = Blueprint('mid_tier_dashboard', __name__, url_prefix='/api/mid-tier/dashboard')


@mid_tier_dashboard_bp.route('/overview', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_mid_tier_dashboard_overview():
    """
    Get comprehensive Mid-tier dashboard overview
    
    Returns:
        Complete Mid-tier dashboard data including:
        - Current balances for up to 2 accounts
        - 6-month cash flow projections
        - Standard spending categories and insights
        - Savings goal progress tracking
        - Basic bill tracking and key dates
        - Real-time alerts and notifications
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get comprehensive dashboard data
        dashboard_data = dashboard_service.get_mid_tier_dashboard(user_id)
        
        if 'error' in dashboard_data:
            return error_response(
                message="Failed to load Mid-tier dashboard",
                error=dashboard_data['error'],
                status_code=500
            )
        
        return success_response(
            message="Mid-tier dashboard loaded successfully",
            data=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"Error getting Mid-tier dashboard overview: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/account-balances', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_account_balances():
    """
    Get current balances for up to 2 accounts
    
    Returns:
        Current account balances with real-time updates
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get account balances
        balances = dashboard_service._get_current_account_balances(user_id)
        
        # Convert to dictionary format
        balances_data = []
        for balance in balances:
            balance_dict = {
                'account_id': balance.account_id,
                'account_name': balance.account_name,
                'account_type': balance.account_type,
                'institution_name': balance.institution_name,
                'current_balance': balance.current_balance,
                'available_balance': balance.available_balance,
                'last_updated': balance.last_updated.isoformat(),
                'currency': balance.currency,
                'is_primary': balance.is_primary
            }
            balances_data.append(balance_dict)
        
        return success_response(
            message="Account balances retrieved successfully",
            data={
                'balances': balances_data,
                'total_accounts': len(balances_data),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting account balances: {e}")
        return error_response(
            message="Failed to retrieve account balances",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/cash-flow-projection', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_cash_flow_projection():
    """
    Get 6-month cash flow projections
    
    Returns:
        6-month cash flow projection data with confidence levels
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get cash flow projections
        projections = dashboard_service._get_6_month_cash_flow_projection(user_id)
        
        # Convert to dictionary format
        projections_data = []
        for projection in projections:
            projection_dict = {
                'month': projection.month,
                'projected_income': projection.projected_income,
                'projected_expenses': projection.projected_expenses,
                'net_cash_flow': projection.net_cash_flow,
                'confidence_level': projection.confidence_level,
                'key_factors': projection.key_factors
            }
            projections_data.append(projection_dict)
        
        return success_response(
            message="Cash flow projections retrieved successfully",
            data={
                'projections': projections_data,
                'forecast_months': len(projections_data),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting cash flow projections: {e}")
        return error_response(
            message="Failed to retrieve cash flow projections",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/spending-categories', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_spending_categories():
    """
    Get standard spending categories and insights
    
    Returns:
        Spending categories with insights and recommendations
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get spending categories and insights
        categories = dashboard_service._get_spending_categories_and_insights(user_id)
        
        # Convert to dictionary format
        categories_data = []
        for category in categories:
            category_dict = {
                'category_name': category.category_name,
                'total_spent': category.total_spent,
                'percentage_of_total': category.percentage_of_total,
                'transaction_count': category.transaction_count,
                'average_transaction': category.average_transaction,
                'trend': category.trend,
                'trend_percentage': category.trend_percentage,
                'recommendations': category.recommendations
            }
            categories_data.append(category_dict)
        
        return success_response(
            message="Spending categories retrieved successfully",
            data={
                'categories': categories_data,
                'total_categories': len(categories_data),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting spending categories: {e}")
        return error_response(
            message="Failed to retrieve spending categories",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/savings-goals', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_savings_goals():
    """
    Get savings goal progress tracking
    
    Returns:
        Savings goals with progress tracking and milestones
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get savings goal progress
        goals = dashboard_service._get_savings_goal_progress(user_id)
        
        # Convert to dictionary format
        goals_data = []
        for goal in goals:
            goal_dict = {
                'goal_id': goal.goal_id,
                'goal_name': goal.goal_name,
                'target_amount': goal.target_amount,
                'current_amount': goal.current_amount,
                'progress_percentage': goal.progress_percentage,
                'monthly_target': goal.monthly_target,
                'days_remaining': goal.days_remaining,
                'status': goal.status,
                'next_milestone': goal.next_milestone
            }
            goals_data.append(goal_dict)
        
        return success_response(
            message="Savings goals retrieved successfully",
            data={
                'goals': goals_data,
                'total_goals': len(goals_data),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting savings goals: {e}")
        return error_response(
            message="Failed to retrieve savings goals",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/bill-tracking', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_bill_tracking():
    """
    Get basic bill tracking data
    
    Returns:
        Bill tracking data with due dates and reminders
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get bill tracking data
        bills = dashboard_service._get_bill_tracking_data(user_id)
        
        # Convert to dictionary format
        bills_data = []
        for bill in bills:
            bill_dict = {
                'bill_id': bill.bill_id,
                'bill_name': bill.bill_name,
                'due_date': bill.due_date.isoformat(),
                'amount': bill.amount,
                'is_paid': bill.is_paid,
                'days_until_due': bill.days_until_due,
                'category': bill.category,
                'priority': bill.priority
            }
            bills_data.append(bill_dict)
        
        return success_response(
            message="Bill tracking data retrieved successfully",
            data={
                'bills': bills_data,
                'total_bills': len(bills_data),
                'upcoming_bills': len([b for b in bills_data if b['days_until_due'] <= 7]),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting bill tracking data: {e}")
        return error_response(
            message="Failed to retrieve bill tracking data",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/key-dates', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_key_dates():
    """
    Get key dates tracking and reminders
    
    Returns:
        Key dates with reminders and tracking information
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get key dates
        dates = dashboard_service._get_key_dates_and_reminders(user_id)
        
        # Convert to dictionary format
        dates_data = []
        for date_info in dates:
            date_dict = {
                'date_id': date_info.date_id,
                'title': date_info.title,
                'date': date_info.date.isoformat(),
                'category': date_info.category,
                'description': date_info.description,
                'days_until': date_info.days_until,
                'is_recurring': date_info.is_recurring,
                'reminder_sent': date_info.reminder_sent
            }
            dates_data.append(date_dict)
        
        return success_response(
            message="Key dates retrieved successfully",
            data={
                'dates': dates_data,
                'total_dates': len(dates_data),
                'upcoming_dates': len([d for d in dates_data if d['days_until'] <= 30]),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting key dates: {e}")
        return error_response(
            message="Failed to retrieve key dates",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/spending-insights', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_spending_insights():
    """
    Get spending insights and recommendations
    
    Returns:
        Spending insights with actionable recommendations
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get spending insights
        insights = dashboard_service._get_spending_insights(user_id)
        
        return success_response(
            message="Spending insights retrieved successfully",
            data={
                'insights': insights,
                'total_insights': len(insights),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting spending insights: {e}")
        return error_response(
            message="Failed to retrieve spending insights",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/alerts', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_alerts():
    """
    Get real-time alerts and notifications
    
    Returns:
        Real-time alerts with severity levels and actions
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        real_time_service = RealTimeUpdatesService(db_session, current_app.config)
        
        # Get alerts
        alerts = real_time_service.get_user_alerts(user_id)
        
        # Convert to dictionary format
        alerts_data = []
        for alert in alerts:
            alert_dict = {
                'alert_id': alert.alert_id,
                'alert_type': alert.alert_type.value,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity.value,
                'timestamp': alert.timestamp.isoformat(),
                'is_read': alert.is_read,
                'action_required': alert.action_required,
                'metadata': alert.metadata
            }
            alerts_data.append(alert_dict)
        
        return success_response(
            message="Alerts retrieved successfully",
            data={
                'alerts': alerts_data,
                'total_alerts': len(alerts_data),
                'unread_alerts': len([a for a in alerts_data if not a['is_read']]),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return error_response(
            message="Failed to retrieve alerts",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/alerts/<alert_id>/read', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def mark_alert_read(alert_id):
    """
    Mark an alert as read
    
    Args:
        alert_id: ID of the alert to mark as read
        
    Returns:
        Success response
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        real_time_service = RealTimeUpdatesService(db_session, current_app.config)
        
        # Mark alert as read
        real_time_service.mark_alert_read(user_id, alert_id)
        
        return success_response(
            message="Alert marked as read successfully",
            data={'alert_id': alert_id}
        )
        
    except Exception as e:
        logger.error(f"Error marking alert as read: {e}")
        return error_response(
            message="Failed to mark alert as read",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/live-balance', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_live_balance():
    """
    Get live balance updates
    
    Returns:
        Live balance updates with change information
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        real_time_service = RealTimeUpdatesService(db_session, current_app.config)
        
        # Get live balance updates
        balance_updates = real_time_service.get_live_balance(user_id)
        
        # Convert to dictionary format
        updates_data = []
        for update in balance_updates:
            update_dict = {
                'account_id': update.account_id,
                'user_id': update.user_id,
                'previous_balance': update.previous_balance,
                'current_balance': update.current_balance,
                'change_amount': update.change_amount,
                'change_percentage': update.change_percentage,
                'timestamp': update.timestamp.isoformat(),
                'transaction_count': update.transaction_count
            }
            updates_data.append(update_dict)
        
        return success_response(
            message="Live balance updates retrieved successfully",
            data={
                'updates': updates_data,
                'total_updates': len(updates_data),
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting live balance updates: {e}")
        return error_response(
            message="Failed to retrieve live balance updates",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/performance-metrics', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_performance_metrics():
    """
    Get performance metrics
    
    Returns:
        Performance metrics and calculations
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        real_time_service = RealTimeUpdatesService(db_session, current_app.config)
        
        # Get performance metrics
        metrics = real_time_service.get_user_metrics(user_id)
        
        return success_response(
            message="Performance metrics retrieved successfully",
            data={
                'metrics': metrics,
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return error_response(
            message="Failed to retrieve performance metrics",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/widget/<widget_type>', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_widget_data(widget_type):
    """
    Get data for a specific dashboard widget
    
    Args:
        widget_type: Type of widget to get data for
        
    Returns:
        Widget-specific data
    """
    try:
        user_id = current_user.id
        
        # Validate widget type
        try:
            widget_enum = DashboardWidgetType(widget_type)
        except ValueError:
            return error_response(
                message="Invalid widget type",
                error=f"Widget type '{widget_type}' is not supported",
                status_code=400
            )
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get widget data
        widget_data = dashboard_service.get_dashboard_widget_data(user_id, widget_enum)
        
        if 'error' in widget_data:
            return error_response(
                message="Failed to get widget data",
                error=widget_data['error'],
                status_code=500
            )
        
        return success_response(
            message=f"Widget data for '{widget_type}' retrieved successfully",
            data={
                'widget_type': widget_type,
                'data': widget_data,
                'last_updated': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting widget data for {widget_type}: {e}")
        return error_response(
            message="Failed to retrieve widget data",
            error=str(e),
            status_code=500
        )


@mid_tier_dashboard_bp.route('/refresh', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def refresh_dashboard():
    """
    Refresh all dashboard data
    
    Returns:
        Updated dashboard data
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = MidTierDashboardService(db_session, feature_service)
        
        # Get refreshed dashboard data
        dashboard_data = dashboard_service.get_mid_tier_dashboard(user_id)
        
        if 'error' in dashboard_data:
            return error_response(
                message="Failed to refresh dashboard",
                error=dashboard_data['error'],
                status_code=500
            )
        
        return success_response(
            message="Dashboard refreshed successfully",
            data={
                'dashboard': dashboard_data,
                'refreshed_at': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error refreshing dashboard: {e}")
        return error_response(
            message="Failed to refresh dashboard",
            error=str(e),
            status_code=500
        ) 