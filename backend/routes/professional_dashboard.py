"""
Professional Dashboard API Routes

This module provides API endpoints for Professional tier dashboard features,
including real-time account balances, advanced cash flow analysis, detailed spending analysis,
and bill prediction with payment optimization.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session

from backend.dashboard.professional_dashboard_service import ProfessionalDashboardService
from backend.services.feature_access_service import FeatureAccessService
from backend.models.subscription import SubscriptionTier
from backend.utils.auth import require_professional_tier
from backend.utils.response import success_response, error_response
from backend.utils.validation import validate_user_id, validate_date_range

logger = logging.getLogger(__name__)

# Create Blueprint
professional_dashboard_bp = Blueprint('professional_dashboard', __name__, url_prefix='/api/professional/dashboard')


@professional_dashboard_bp.route('/overview', methods=['GET'])
@login_required
@require_professional_tier
def get_professional_dashboard_overview():
    """
    Get comprehensive Professional tier dashboard overview
    
    Returns:
        Complete Professional dashboard data including:
        - Real-time account balances
        - Advanced cash flow analysis
        - Detailed spending analysis
        - Bill prediction and payment optimization
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get comprehensive dashboard data
        dashboard_data = dashboard_service.get_professional_dashboard(user_id)
        
        if 'error' in dashboard_data:
            return error_response(
                message="Failed to load Professional dashboard",
                error=dashboard_data['error'],
                status_code=500
            )
        
        return success_response(
            message="Professional dashboard loaded successfully",
            data=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"Error getting Professional dashboard overview: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/account-balances', methods=['GET'])
@login_required
@require_professional_tier
def get_real_time_account_balances():
    """
    Get real-time account balances across all linked accounts
    
    Query Parameters:
        refresh (bool): Force refresh of cached data
        
    Returns:
        Real-time account balance data for all linked accounts
    """
    try:
        user_id = current_user.id
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get account balances
        if refresh:
            # Clear cache and force refresh
            dashboard_service.balance_cache.clear()
        
        balance_data = dashboard_service._get_real_time_account_balances(user_id)
        
        if 'error' in balance_data:
            return error_response(
                message="Failed to load account balances",
                error=balance_data['error'],
                status_code=500
            )
        
        return success_response(
            message="Account balances loaded successfully",
            data=balance_data
        )
        
    except Exception as e:
        logger.error(f"Error getting account balances: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/cash-flow-analysis', methods=['GET'])
@login_required
@require_professional_tier
def get_advanced_cash_flow_analysis():
    """
    Get advanced cash flow analysis with 12-month projections
    
    Query Parameters:
        months (int): Number of months to project (default: 12, max: 24)
        include_historical (bool): Include historical data (default: true)
        
    Returns:
        Advanced cash flow analysis with projections
    """
    try:
        user_id = current_user.id
        months = min(int(request.args.get('months', 12)), 24)  # Cap at 24 months
        include_historical = request.args.get('include_historical', 'true').lower() == 'true'
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get cash flow analysis
        cash_flow_data = dashboard_service._get_advanced_cash_flow_analysis(user_id)
        
        if 'error' in cash_flow_data:
            return error_response(
                message="Failed to load cash flow analysis",
                error=cash_flow_data['error'],
                status_code=500
            )
        
        # Filter projections if needed
        if months != 12:
            cash_flow_data['projections'] = cash_flow_data['projections'][:months]
        
        return success_response(
            message="Cash flow analysis loaded successfully",
            data=cash_flow_data
        )
        
    except Exception as e:
        logger.error(f"Error getting cash flow analysis: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/spending-analysis', methods=['GET'])
@login_required
@require_professional_tier
def get_detailed_spending_analysis():
    """
    Get detailed spending analysis with custom categories
    
    Query Parameters:
        date_range (str): Date range for analysis (e.g., '30d', '90d', '1y')
        include_custom_categories (bool): Include custom categories (default: true)
        include_merchant_analysis (bool): Include merchant analysis (default: true)
        
    Returns:
        Detailed spending analysis with custom categories
    """
    try:
        user_id = current_user.id
        date_range = request.args.get('date_range', '30d')
        include_custom_categories = request.args.get('include_custom_categories', 'true').lower() == 'true'
        include_merchant_analysis = request.args.get('include_merchant_analysis', 'true').lower() == 'true'
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get spending analysis
        spending_data = dashboard_service._get_detailed_spending_analysis(user_id)
        
        if 'error' in spending_data:
            return error_response(
                message="Failed to load spending analysis",
                error=spending_data['error'],
                status_code=500
            )
        
        # Filter data based on parameters
        if not include_custom_categories:
            spending_data.pop('custom_categories', None)
        
        if not include_merchant_analysis:
            spending_data.pop('merchant_analysis', None)
        
        return success_response(
            message="Spending analysis loaded successfully",
            data=spending_data
        )
        
    except Exception as e:
        logger.error(f"Error getting spending analysis: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/bill-prediction', methods=['GET'])
@login_required
@require_professional_tier
def get_bill_prediction_data():
    """
    Get bill prediction and payment optimization data
    
    Query Parameters:
        upcoming_days (int): Days to look ahead for bills (default: 90)
        include_optimization (bool): Include payment optimization (default: true)
        
    Returns:
        Bill prediction and payment optimization data
    """
    try:
        user_id = current_user.id
        upcoming_days = int(request.args.get('upcoming_days', 90))
        include_optimization = request.args.get('include_optimization', 'true').lower() == 'true'
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get bill prediction data
        bill_data = dashboard_service._get_bill_prediction_data(user_id)
        
        if 'error' in bill_data:
            return error_response(
                message="Failed to load bill prediction data",
                error=bill_data['error'],
                status_code=500
            )
        
        # Filter data based on parameters
        if not include_optimization:
            bill_data.pop('optimized_payments', None)
            bill_data.pop('payment_optimization', None)
        
        return success_response(
            message="Bill prediction data loaded successfully",
            data=bill_data
        )
        
    except Exception as e:
        logger.error(f"Error getting bill prediction data: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/payment-optimization', methods=['GET'])
@login_required
@require_professional_tier
def get_payment_optimization_data():
    """
    Get payment optimization recommendations
    
    Returns:
        Payment optimization data and recommendations
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get payment optimization data
        optimization_data = dashboard_service._get_payment_optimization_data(user_id)
        
        if 'error' in optimization_data:
            return error_response(
                message="Failed to load payment optimization data",
                error=optimization_data['error'],
                status_code=500
            )
        
        return success_response(
            message="Payment optimization data loaded successfully",
            data=optimization_data
        )
        
    except Exception as e:
        logger.error(f"Error getting payment optimization data: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/financial-forecast', methods=['GET'])
@login_required
@require_professional_tier
def get_financial_forecast_data():
    """
    Get comprehensive financial forecast data
    
    Query Parameters:
        forecast_period (str): Forecast period (default: '12_months')
        include_scenarios (bool): Include scenario analysis (default: true)
        
    Returns:
        Comprehensive financial forecast data
    """
    try:
        user_id = current_user.id
        forecast_period = request.args.get('forecast_period', '12_months')
        include_scenarios = request.args.get('include_scenarios', 'true').lower() == 'true'
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get financial forecast data
        forecast_data = dashboard_service._get_financial_forecast_data(user_id)
        
        if 'error' in forecast_data:
            return error_response(
                message="Failed to load financial forecast data",
                error=forecast_data['error'],
                status_code=500
            )
        
        # Filter data based on parameters
        if not include_scenarios:
            forecast_data.pop('scenario_analysis', None)
        
        return success_response(
            message="Financial forecast data loaded successfully",
            data=forecast_data
        )
        
    except Exception as e:
        logger.error(f"Error getting financial forecast data: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/investment-overview', methods=['GET'])
@login_required
@require_professional_tier
def get_investment_overview_data():
    """
    Get investment overview data
    
    Returns:
        Investment overview and portfolio analysis data
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get investment overview data
        investment_data = dashboard_service._get_investment_overview_data(user_id)
        
        if 'error' in investment_data:
            return error_response(
                message="Failed to load investment overview data",
                error=investment_data['error'],
                status_code=500
            )
        
        return success_response(
            message="Investment overview data loaded successfully",
            data=investment_data
        )
        
    except Exception as e:
        logger.error(f"Error getting investment overview data: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/debt-management', methods=['GET'])
@login_required
@require_professional_tier
def get_debt_management_data():
    """
    Get debt management data
    
    Returns:
        Debt management and optimization data
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get debt management data
        debt_data = dashboard_service._get_debt_management_data(user_id)
        
        if 'error' in debt_data:
            return error_response(
                message="Failed to load debt management data",
                error=debt_data['error'],
                status_code=500
            )
        
        return success_response(
            message="Debt management data loaded successfully",
            data=debt_data
        )
        
    except Exception as e:
        logger.error(f"Error getting debt management data: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/alerts', methods=['GET'])
@login_required
@require_professional_tier
def get_dashboard_alerts():
    """
    Get dashboard alerts and notifications
    
    Query Parameters:
        alert_types (str): Comma-separated list of alert types to include
        include_resolved (bool): Include resolved alerts (default: false)
        
    Returns:
        Dashboard alerts and notifications
    """
    try:
        user_id = current_user.id
        alert_types = request.args.get('alert_types', '').split(',') if request.args.get('alert_types') else []
        include_resolved = request.args.get('include_resolved', 'false').lower() == 'true'
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get dashboard alerts
        alerts = dashboard_service._get_dashboard_alerts(user_id)
        
        # Filter alerts based on parameters
        if alert_types:
            alerts = [alert for alert in alerts if alert.get('type') in alert_types]
        
        if not include_resolved:
            alerts = [alert for alert in alerts if not alert.get('resolved', False)]
        
        return success_response(
            message="Dashboard alerts loaded successfully",
            data={
                'alerts': alerts,
                'alert_count': len(alerts),
                'unresolved_count': len([a for a in alerts if not a.get('resolved', False)])
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard alerts: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/insights', methods=['GET'])
@login_required
@require_professional_tier
def get_ai_insights():
    """
    Get AI-generated insights for the dashboard
    
    Query Parameters:
        insight_types (str): Comma-separated list of insight types to include
        limit (int): Maximum number of insights to return (default: 10)
        
    Returns:
        AI-generated insights for the dashboard
    """
    try:
        user_id = current_user.id
        insight_types = request.args.get('insight_types', '').split(',') if request.args.get('insight_types') else []
        limit = int(request.args.get('limit', 10))
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get AI insights
        insights = dashboard_service._get_ai_insights(user_id)
        
        # Filter insights based on parameters
        if insight_types:
            insights = [insight for insight in insights if insight.get('type') in insight_types]
        
        # Limit number of insights
        insights = insights[:limit]
        
        return success_response(
            message="AI insights loaded successfully",
            data={
                'insights': insights,
                'insight_count': len(insights),
                'generated_at': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting AI insights: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/widgets', methods=['GET'])
@login_required
@require_professional_tier
def get_custom_widgets():
    """
    Get custom dashboard widgets
    
    Returns:
        Custom dashboard widgets data
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get custom widgets
        widgets = dashboard_service._get_custom_widgets(user_id)
        
        return success_response(
            message="Custom widgets loaded successfully",
            data={
                'widgets': widgets,
                'widget_count': len(widgets)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting custom widgets: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/widgets/<widget_id>', methods=['GET'])
@login_required
@require_professional_tier
def get_specific_widget(widget_id: str):
    """
    Get data for a specific dashboard widget
    
    Args:
        widget_id: ID of the widget to get data for
        
    Returns:
        Data for the specific widget
    """
    try:
        user_id = current_user.id
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get user's widget preferences
        widget_preferences = dashboard_service._get_user_widget_preferences(user_id)
        
        # Find the specific widget
        widget_config = next((w for w in widget_preferences if w.get('id') == widget_id), None)
        
        if not widget_config:
            return error_response(
                message="Widget not found",
                error=f"Widget with ID {widget_id} not found",
                status_code=404
            )
        
        # Generate widget data
        widget_data = dashboard_service._generate_widget_data(user_id, widget_config)
        
        return success_response(
            message="Widget data loaded successfully",
            data=widget_data
        )
        
    except Exception as e:
        logger.error(f"Error getting specific widget {widget_id}: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


@professional_dashboard_bp.route('/export', methods=['GET'])
@login_required
@require_professional_tier
def export_dashboard_data():
    """
    Export Professional dashboard data
    
    Query Parameters:
        format (str): Export format ('json', 'csv', 'pdf') (default: 'json')
        sections (str): Comma-separated list of sections to export
        date_range (str): Date range for export
        
    Returns:
        Exported dashboard data in requested format
    """
    try:
        user_id = current_user.id
        export_format = request.args.get('format', 'json')
        sections = request.args.get('sections', '').split(',') if request.args.get('sections') else []
        date_range = request.args.get('date_range', '30d')
        
        # Get database session
        db_session = current_app.config['DB_SESSION']
        
        # Initialize services
        feature_service = FeatureAccessService(db_session)
        dashboard_service = ProfessionalDashboardService(db_session, feature_service)
        
        # Get comprehensive dashboard data
        dashboard_data = dashboard_service.get_professional_dashboard(user_id)
        
        if 'error' in dashboard_data:
            return error_response(
                message="Failed to export dashboard data",
                error=dashboard_data['error'],
                status_code=500
            )
        
        # Filter sections if specified
        if sections:
            filtered_data = {}
            for section in sections:
                if section in dashboard_data:
                    filtered_data[section] = dashboard_data[section]
            dashboard_data = filtered_data
        
        # Add export metadata
        export_data = {
            'export_info': {
                'user_id': user_id,
                'export_format': export_format,
                'export_date': datetime.utcnow().isoformat(),
                'sections_included': list(dashboard_data.keys()),
                'date_range': date_range
            },
            'data': dashboard_data
        }
        
        # Handle different export formats
        if export_format == 'json':
            return success_response(
                message="Dashboard data exported successfully",
                data=export_data
            )
        elif export_format == 'csv':
            # TODO: Implement CSV export
            return error_response(
                message="CSV export not yet implemented",
                error="CSV export functionality is under development",
                status_code=501
            )
        elif export_format == 'pdf':
            # TODO: Implement PDF export
            return error_response(
                message="PDF export not yet implemented",
                error="PDF export functionality is under development",
                status_code=501
            )
        else:
            return error_response(
                message="Unsupported export format",
                error=f"Export format '{export_format}' is not supported",
                status_code=400
            )
        
    except Exception as e:
        logger.error(f"Error exporting dashboard data: {e}")
        return error_response(
            message="Internal server error",
            error=str(e),
            status_code=500
        )


# Error handlers
@professional_dashboard_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return error_response(
        message="Endpoint not found",
        error="The requested Professional dashboard endpoint does not exist",
        status_code=404
    )


@professional_dashboard_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return error_response(
        message="Internal server error",
        error="An unexpected error occurred while processing your request",
        status_code=500
    ) 