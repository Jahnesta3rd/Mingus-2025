"""
Budget Tier Dashboard Routes

This module provides Flask routes for the Budget tier dashboard,
including manual entry interface, banking feature previews, upgrade prompts,
basic expense tracking and budgeting, and resume parsing with 1 limit per month.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app, session
from flask_login import login_required, current_user
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden

from backend.dashboard.budget_tier_dashboard_service import BudgetTierDashboardService, DashboardWidgetType
from backend.services.basic_expense_tracking_service import BasicExpenseTrackingService
from backend.services.resume_parsing_service import ResumeParsingService
from backend.services.upgrade_prompts_service import UpgradePromptsService
from backend.services.feature_access_service import FeatureAccessService
from backend.services.intelligent_insights_service import IntelligentInsightsService
from backend.services.interactive_features_service import InteractiveFeaturesService
from backend.middleware.auth import require_auth
from backend.utils.response_helpers import success_response, error_response
from backend.utils.validation import validate_request_data

logger = logging.getLogger(__name__)

# Create blueprint
budget_tier_dashboard_bp = Blueprint('budget_tier_dashboard', __name__, url_prefix='/api/budget-tier/dashboard')


@budget_tier_dashboard_bp.route('/overview', methods=['GET'])
@login_required
@require_auth
def get_budget_tier_dashboard_overview():
    """Get comprehensive Budget tier dashboard overview"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get dashboard data
        dashboard_data = dashboard_service.get_budget_tier_dashboard(user_id)
        
        if 'error' in dashboard_data:
            return error_response(dashboard_data['error'], 400)
        
        return success_response(dashboard_data, "Budget tier dashboard data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting budget tier dashboard overview: {e}")
        return error_response("Failed to retrieve dashboard data", 500)


@budget_tier_dashboard_bp.route('/manual-entry', methods=['GET'])
@login_required
@require_auth
def get_manual_entry_interface():
    """Get manual entry interface data"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get manual entry data
        manual_entry_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.MANUAL_ENTRY
        )
        
        if 'error' in manual_entry_data:
            return error_response(manual_entry_data['error'], 400)
        
        return success_response(manual_entry_data, "Manual entry interface data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting manual entry interface: {e}")
        return error_response("Failed to retrieve manual entry data", 500)


@budget_tier_dashboard_bp.route('/manual-entry', methods=['POST'])
@login_required
@require_auth
def add_manual_entry():
    """Add a new manual entry transaction"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'description', 'category', 'date', 'transaction_type']
        if not validate_request_data(data, required_fields):
            return error_response("Missing required fields", 400)
        
        # Validate transaction type
        if data['transaction_type'] not in ['income', 'expense']:
            return error_response("Invalid transaction type", 400)
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return error_response("Amount must be positive", 400)
        except ValueError:
            return error_response("Invalid amount format", 400)
        
        # Validate date
        try:
            entry_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response("Invalid date format. Use YYYY-MM-DD", 400)
        
        # Initialize services
        db_session = current_app.db.session
        expense_service = BasicExpenseTrackingService(db_session)
        
        # Prepare entry data
        entry_data = {
            'amount': amount,
            'description': data['description'],
            'category': data['category'],
            'date': entry_date,
            'transaction_type': data['transaction_type']
        }
        
        # Add entry
        entry = expense_service.add_manual_entry(user_id, entry_data)
        
        if not entry:
            return error_response("Failed to add manual entry", 500)
        
        return success_response({
            'entry_id': entry.id,
            'message': 'Manual entry added successfully'
        }, "Manual entry added successfully")
        
    except Exception as e:
        logger.error(f"Error adding manual entry: {e}")
        return error_response("Failed to add manual entry", 500)


@budget_tier_dashboard_bp.route('/banking-previews', methods=['GET'])
@login_required
@require_auth
def get_banking_feature_previews():
    """Get banking feature previews"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get banking preview data
        preview_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.BANKING_PREVIEW
        )
        
        if 'error' in preview_data:
            return error_response(preview_data['error'], 400)
        
        return success_response(preview_data, "Banking feature previews retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting banking feature previews: {e}")
        return error_response("Failed to retrieve banking previews", 500)


@budget_tier_dashboard_bp.route('/upgrade-prompts', methods=['GET'])
@login_required
@require_auth
def get_upgrade_prompts():
    """Get personalized upgrade prompts"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get upgrade prompts data
        prompts_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.UPGRADE_PROMPTS
        )
        
        if 'error' in prompts_data:
            return error_response(prompts_data['error'], 400)
        
        return success_response(prompts_data, "Upgrade prompts retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting upgrade prompts: {e}")
        return error_response("Failed to retrieve upgrade prompts", 500)


@budget_tier_dashboard_bp.route('/upgrade-prompts/<prompt_id>/dismiss', methods=['POST'])
@login_required
@require_auth
def dismiss_upgrade_prompt(prompt_id):
    """Dismiss an upgrade prompt"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        upgrade_service = UpgradePromptsService(db_session)
        
        # Dismiss prompt
        success = upgrade_service.dismiss_prompt(user_id, prompt_id)
        
        if not success:
            return error_response("Prompt not found or already dismissed", 404)
        
        return success_response({
            'prompt_id': prompt_id,
            'message': 'Prompt dismissed successfully'
        }, "Upgrade prompt dismissed successfully")
        
    except Exception as e:
        logger.error(f"Error dismissing upgrade prompt: {e}")
        return error_response("Failed to dismiss prompt", 500)


@budget_tier_dashboard_bp.route('/upgrade-prompts/<prompt_id>/click', methods=['POST'])
@login_required
@require_auth
def track_upgrade_prompt_click(prompt_id):
    """Track when a user clicks on an upgrade prompt"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        upgrade_service = UpgradePromptsService(db_session)
        
        # Track click
        success = upgrade_service.track_prompt_click(user_id, prompt_id)
        
        if not success:
            return error_response("Prompt not found", 404)
        
        return success_response({
            'prompt_id': prompt_id,
            'message': 'Prompt click tracked successfully'
        }, "Upgrade prompt click tracked successfully")
        
    except Exception as e:
        logger.error(f"Error tracking upgrade prompt click: {e}")
        return error_response("Failed to track prompt click", 500)


@budget_tier_dashboard_bp.route('/expense-tracking', methods=['GET'])
@login_required
@require_auth
def get_expense_tracking():
    """Get basic expense tracking data"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get expense tracking data
        expense_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.EXPENSE_TRACKING
        )
        
        if 'error' in expense_data:
            return error_response(expense_data['error'], 400)
        
        return success_response(expense_data, "Expense tracking data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting expense tracking: {e}")
        return error_response("Failed to retrieve expense tracking data", 500)


@budget_tier_dashboard_bp.route('/budget-overview', methods=['GET'])
@login_required
@require_auth
def get_budget_overview():
    """Get budget overview data"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get budget overview data
        budget_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.BUDGET_OVERVIEW
        )
        
        if 'error' in budget_data:
            return error_response(budget_data['error'], 400)
        
        return success_response(budget_data, "Budget overview data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting budget overview: {e}")
        return error_response("Failed to retrieve budget overview data", 500)


@budget_tier_dashboard_bp.route('/budget', methods=['POST'])
@login_required
@require_auth
def create_budget():
    """Create a new budget"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['category', 'amount']
        if not validate_request_data(data, required_fields):
            return error_response("Missing required fields", 400)
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return error_response("Budget amount must be positive", 400)
        except ValueError:
            return error_response("Invalid amount format", 400)
        
        # Initialize services
        db_session = current_app.db.session
        expense_service = BasicExpenseTrackingService(db_session)
        
        # Prepare budget data
        budget_data = {
            'category': data['category'],
            'amount': amount
        }
        
        # Create budget
        budget = expense_service.create_budget(user_id, budget_data)
        
        if not budget:
            return error_response("Failed to create budget", 500)
        
        return success_response({
            'budget_id': budget.budget_id,
            'message': 'Budget created successfully'
        }, "Budget created successfully")
        
    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        return error_response("Failed to create budget", 500)


@budget_tier_dashboard_bp.route('/resume-parsing', methods=['GET'])
@login_required
@require_auth
def get_resume_parsing_status():
    """Get resume parsing status and limits"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get resume parsing data
        parsing_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.RESUME_PARSING
        )
        
        if 'error' in parsing_data:
            return error_response(parsing_data['error'], 400)
        
        return success_response(parsing_data, "Resume parsing status retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting resume parsing status: {e}")
        return error_response("Failed to retrieve resume parsing status", 500)


@budget_tier_dashboard_bp.route('/resume-parsing', methods=['POST'])
@login_required
@require_auth
def parse_resume():
    """Parse a resume (with tier limits)"""
    try:
        user_id = current_user.id
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return error_response("No file uploaded", 400)
        
        file = request.files['file']
        
        if file.filename == '':
            return error_response("No file selected", 400)
        
        # Validate file type
        allowed_extensions = {'pdf', 'doc', 'docx', 'txt'}
        if not file.filename.lower().endswith(tuple(f'.{ext}' for ext in allowed_extensions)):
            return error_response("Invalid file type. Allowed: PDF, DOC, DOCX, TXT", 400)
        
        # Read file content
        file_content = file.read()
        
        # Check file size (max 10MB)
        if len(file_content) > 10 * 1024 * 1024:
            return error_response("File too large. Maximum size: 10MB", 400)
        
        # Initialize services
        db_session = current_app.db.session
        resume_service = ResumeParsingService(db_session)
        
        # Prepare file data
        file_data = {
            'filename': file.filename,
            'content': file_content.decode('utf-8', errors='ignore'),
            'size': len(file_content),
            'type': file.filename.split('.')[-1].lower()
        }
        
        # Parse resume
        result = resume_service.parse_resume(user_id, file_data)
        
        if not result['success']:
            if result['error'] == 'limit_exceeded':
                return error_response(result['message'], 429, extra_data=result.get('upgrade_required', False))
            else:
                return error_response(result['message'], 400)
        
        return success_response(result, "Resume parsed successfully")
        
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        return error_response("Failed to parse resume", 500)


@budget_tier_dashboard_bp.route('/basic-insights', methods=['GET'])
@login_required
@require_auth
def get_basic_insights():
    """Get basic insights for Budget tier users"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get basic insights data
        insights_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.BASIC_INSIGHTS
        )
        
        if 'error' in insights_data:
            return error_response(insights_data['error'], 400)
        
        return success_response(insights_data, "Basic insights retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting basic insights: {e}")
        return error_response("Failed to retrieve basic insights", 500)


@budget_tier_dashboard_bp.route('/feature-previews', methods=['GET'])
@login_required
@require_auth
def get_feature_previews():
    """Get feature previews for Budget tier users"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get feature previews data
        previews_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.FEATURE_PREVIEWS
        )
        
        if 'error' in previews_data:
            return error_response(previews_data['error'], 400)
        
        return success_response(previews_data, "Feature previews retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature previews: {e}")
        return error_response("Failed to retrieve feature previews", 500)


@budget_tier_dashboard_bp.route('/widget/<widget_type>', methods=['GET'])
@login_required
@require_auth
def get_dashboard_widget(widget_type):
    """Get data for a specific dashboard widget"""
    try:
        user_id = current_user.id
        
        # Validate widget type
        try:
            widget_enum = DashboardWidgetType(widget_type)
        except ValueError:
            return error_response("Invalid widget type", 400)
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get widget data
        widget_data = dashboard_service.get_dashboard_widget_data(user_id, widget_enum)
        
        if 'error' in widget_data:
            return error_response(widget_data['error'], 400)
        
        return success_response(widget_data, f"{widget_type} widget data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting dashboard widget {widget_type}: {e}")
        return error_response("Failed to retrieve widget data", 500)


@budget_tier_dashboard_bp.route('/refresh', methods=['POST'])
@login_required
@require_auth
def refresh_dashboard():
    """Trigger dashboard refresh"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get fresh dashboard data
        dashboard_data = dashboard_service.get_budget_tier_dashboard(user_id)
        
        if 'error' in dashboard_data:
            return error_response(dashboard_data['error'], 400)
        
        return success_response(dashboard_data, "Dashboard refreshed successfully")
        
    except Exception as e:
        logger.error(f"Error refreshing dashboard: {e}")
        return error_response("Failed to refresh dashboard", 500)


@budget_tier_dashboard_bp.route('/intelligent-insights', methods=['GET'])
@login_required
@require_auth
def get_intelligent_insights():
    """Get intelligent insights for Budget tier users"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get intelligent insights data
        insights_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.INTELLIGENT_INSIGHTS
        )
        
        if 'error' in insights_data:
            return error_response(insights_data['error'], 400)
        
        return success_response(insights_data, "Intelligent insights retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting intelligent insights: {e}")
        return error_response("Failed to retrieve intelligent insights", 500)


@budget_tier_dashboard_bp.route('/intelligent-insights/spending-trends', methods=['GET'])
@login_required
@require_auth
def get_spending_trends():
    """Get spending trend analysis"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        intelligent_service = IntelligentInsightsService(db_session)
        
        # Get spending trends
        insights = intelligent_service.get_intelligent_insights(user_id)
        spending_trends = insights.get('spending_trends', [])
        
        return success_response({
            'spending_trends': spending_trends,
            'total_trends': len(spending_trends)
        }, "Spending trends retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting spending trends: {e}")
        return error_response("Failed to retrieve spending trends", 500)


@budget_tier_dashboard_bp.route('/intelligent-insights/unusual-transactions', methods=['GET'])
@login_required
@require_auth
def get_unusual_transactions():
    """Get unusual transaction alerts"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        intelligent_service = IntelligentInsightsService(db_session)
        
        # Get unusual transactions
        insights = intelligent_service.get_intelligent_insights(user_id)
        unusual_transactions = insights.get('unusual_transactions', [])
        
        return success_response({
            'unusual_transactions': unusual_transactions,
            'total_alerts': len(unusual_transactions)
        }, "Unusual transactions retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting unusual transactions: {e}")
        return error_response("Failed to retrieve unusual transactions", 500)


@budget_tier_dashboard_bp.route('/intelligent-insights/subscription-management', methods=['GET'])
@login_required
@require_auth
def get_subscription_management():
    """Get subscription service management insights"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        intelligent_service = IntelligentInsightsService(db_session)
        
        # Get subscription insights
        insights = intelligent_service.get_intelligent_insights(user_id)
        subscription_insights = insights.get('subscription_management', [])
        
        return success_response({
            'subscription_insights': subscription_insights,
            'total_subscriptions': len(subscription_insights),
            'potential_savings': sum(insight.get('potential_savings', 0) for insight in subscription_insights)
        }, "Subscription management insights retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting subscription management: {e}")
        return error_response("Failed to retrieve subscription management insights", 500)


@budget_tier_dashboard_bp.route('/intelligent-insights/cash-flow-optimization', methods=['GET'])
@login_required
@require_auth
def get_cash_flow_optimization():
    """Get cash flow optimization suggestions"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        intelligent_service = IntelligentInsightsService(db_session)
        
        # Get cash flow optimization
        insights = intelligent_service.get_intelligent_insights(user_id)
        cash_flow_optimizations = insights.get('cash_flow_optimization', [])
        
        return success_response({
            'cash_flow_optimizations': cash_flow_optimizations,
            'total_optimizations': len(cash_flow_optimizations),
            'total_potential_impact': sum(opt.get('potential_impact', 0) for opt in cash_flow_optimizations)
        }, "Cash flow optimization suggestions retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting cash flow optimization: {e}")
        return error_response("Failed to retrieve cash flow optimization", 500)


@budget_tier_dashboard_bp.route('/intelligent-insights/emergency-fund', methods=['GET'])
@login_required
@require_auth
def get_emergency_fund_recommendations():
    """Get emergency fund recommendations"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        intelligent_service = IntelligentInsightsService(db_session)
        
        # Get emergency fund insights
        insights = intelligent_service.get_intelligent_insights(user_id)
        emergency_fund = insights.get('emergency_fund')
        
        if not emergency_fund:
            return success_response({
                'emergency_fund': None,
                'message': 'Add more transactions to get emergency fund recommendations'
            }, "Emergency fund analysis not available")
        
        return success_response({
            'emergency_fund': emergency_fund
        }, "Emergency fund recommendations retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting emergency fund recommendations: {e}")
        return error_response("Failed to retrieve emergency fund recommendations", 500)


@budget_tier_dashboard_bp.route('/intelligent-insights/debt-payoff', methods=['GET'])
@login_required
@require_auth
def get_debt_payoff_strategies():
    """Get debt payoff strategies"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        intelligent_service = IntelligentInsightsService(db_session)
        
        # Get debt payoff insights
        insights = intelligent_service.get_intelligent_insights(user_id)
        debt_payoff = insights.get('debt_payoff')
        
        if not debt_payoff:
            return success_response({
                'debt_payoff': None,
                'message': 'Add more transactions to get debt payoff strategies'
            }, "Debt payoff analysis not available")
        
        return success_response({
            'debt_payoff': debt_payoff
        }, "Debt payoff strategies retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting debt payoff strategies: {e}")
        return error_response("Failed to retrieve debt payoff strategies", 500)


@budget_tier_dashboard_bp.route('/interactive-features', methods=['GET'])
@login_required
@require_auth
def get_interactive_features():
    """Get interactive features for Budget tier users"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        feature_service = FeatureAccessService(db_session)
        dashboard_service = BudgetTierDashboardService(db_session, feature_service)
        
        # Get interactive features data
        interactive_data = dashboard_service.get_dashboard_widget_data(
            user_id, DashboardWidgetType.INTERACTIVE_FEATURES
        )
        
        if 'error' in interactive_data:
            return error_response(interactive_data['error'], 400)
        
        return success_response(interactive_data, "Interactive features retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting interactive features: {e}")
        return error_response("Failed to retrieve interactive features", 500)


@budget_tier_dashboard_bp.route('/goals', methods=['GET'])
@login_required
@require_auth
def get_user_goals():
    """Get user's financial goals"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Get user goals
        goals = interactive_service.get_user_goals(user_id)
        
        return success_response({
            'goals': goals,
            'total_goals': len(goals),
            'active_goals': len([g for g in goals if g.status.value == 'active'])
        }, "User goals retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting user goals: {e}")
        return error_response("Failed to retrieve user goals", 500)


@budget_tier_dashboard_bp.route('/goals', methods=['POST'])
@login_required
@require_auth
def create_goal():
    """Create a new financial goal"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['goal_type', 'title', 'target_amount', 'target_date']
        if not validate_request_data(data, required_fields):
            return error_response("Missing required fields", 400)
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Create goal
        goal = interactive_service.create_financial_goal(user_id, data)
        
        if not goal:
            return error_response("Failed to create goal", 400)
        
        return success_response({'goal': goal}, "Goal created successfully")
        
    except Exception as e:
        logger.error(f"Error creating goal: {e}")
        return error_response("Failed to create goal", 500)


@budget_tier_dashboard_bp.route('/goals/<goal_id>/progress', methods=['POST'])
@login_required
@require_auth
def update_goal_progress(goal_id):
    """Update goal progress with a contribution"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        if 'amount' not in data:
            return error_response("Missing amount field", 400)
        
        amount = float(data['amount'])
        if amount <= 0:
            return error_response("Amount must be positive", 400)
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Update goal progress
        success = interactive_service.update_goal_progress(user_id, goal_id, amount)
        
        if not success:
            return error_response("Goal not found or update failed", 404)
        
        return success_response({'message': 'Goal progress updated successfully'}, "Goal progress updated")
        
    except Exception as e:
        logger.error(f"Error updating goal progress: {e}")
        return error_response("Failed to update goal progress", 500)


@budget_tier_dashboard_bp.route('/budgets', methods=['GET'])
@login_required
@require_auth
def get_user_budgets():
    """Get user's budgets"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Get user budgets
        budgets = interactive_service.get_user_budgets(user_id)
        
        return success_response({
            'budgets': budgets,
            'total_budgets': len(budgets),
            'over_budget_count': len([b for b in budgets if b.status.value == 'over_budget'])
        }, "User budgets retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting user budgets: {e}")
        return error_response("Failed to retrieve user budgets", 500)


@budget_tier_dashboard_bp.route('/budgets', methods=['POST'])
@login_required
@require_auth
def create_budget():
    """Create a new budget"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['category', 'amount']
        if not validate_request_data(data, required_fields):
            return error_response("Missing required fields", 400)
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Create budget
        budget = interactive_service.create_budget(user_id, data)
        
        if not budget:
            return error_response("Failed to create budget", 400)
        
        return success_response({'budget': budget}, "Budget created successfully")
        
    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        return error_response("Failed to create budget", 500)


@budget_tier_dashboard_bp.route('/feature-comparisons', methods=['GET'])
@login_required
@require_auth
def get_feature_comparisons():
    """Get feature comparison data"""
    try:
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Get feature comparisons
        comparisons = interactive_service.get_feature_comparisons()
        
        return success_response({
            'feature_comparisons': comparisons,
            'total_features': len(comparisons)
        }, "Feature comparisons retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting feature comparisons: {e}")
        return error_response("Failed to retrieve feature comparisons", 500)


@budget_tier_dashboard_bp.route('/upgrade-benefits', methods=['GET'])
@login_required
@require_auth
def get_upgrade_benefits():
    """Get upgrade benefits"""
    try:
        tier = request.args.get('tier')  # Optional tier filter
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Get upgrade benefits
        benefits = interactive_service.get_upgrade_benefits(tier)
        
        return success_response({
            'upgrade_benefits': benefits,
            'total_benefits': len(benefits)
        }, "Upgrade benefits retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting upgrade benefits: {e}")
        return error_response("Failed to retrieve upgrade benefits", 500)


@budget_tier_dashboard_bp.route('/limited-time-offers', methods=['GET'])
@login_required
@require_auth
def get_limited_time_offers():
    """Get active limited time offers"""
    try:
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Get limited time offers
        offers = interactive_service.get_active_limited_time_offers()
        
        return success_response({
            'limited_time_offers': offers,
            'total_offers': len(offers)
        }, "Limited time offers retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting limited time offers: {e}")
        return error_response("Failed to retrieve limited time offers", 500)


@budget_tier_dashboard_bp.route('/usage-suggestions', methods=['GET'])
@login_required
@require_auth
def get_usage_suggestions():
    """Get usage-based upgrade suggestions"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Get usage suggestions
        suggestions = interactive_service.get_usage_based_suggestions(user_id)
        
        return success_response({
            'usage_suggestions': suggestions,
            'total_suggestions': len(suggestions)
        }, "Usage suggestions retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting usage suggestions: {e}")
        return error_response("Failed to retrieve usage suggestions", 500)


@budget_tier_dashboard_bp.route('/social-proof', methods=['GET'])
@login_required
@require_auth
def get_social_proof():
    """Get social proof data"""
    try:
        user_type = request.args.get('user_type')  # Optional filter
        limit = int(request.args.get('limit', 3))
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Get social proof
        social_proof = interactive_service.get_social_proof(user_type, limit)
        
        return success_response({
            'social_proof': social_proof,
            'total_proofs': len(social_proof)
        }, "Social proof retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting social proof: {e}")
        return error_response("Failed to retrieve social proof", 500)


@budget_tier_dashboard_bp.route('/goal-recommendations', methods=['GET'])
@login_required
@require_auth
def get_goal_recommendations():
    """Get personalized goal recommendations"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        interactive_service = InteractiveFeaturesService(db_session)
        
        # Get goal recommendations
        recommendations = interactive_service.get_goal_recommendations(user_id)
        
        return success_response({
            'goal_recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }, "Goal recommendations retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting goal recommendations: {e}")
        return error_response("Failed to retrieve goal recommendations", 500)


@budget_tier_dashboard_bp.route('/analytics', methods=['GET'])
@login_required
@require_auth
def get_dashboard_analytics():
    """Get dashboard analytics and usage statistics"""
    try:
        user_id = current_user.id
        
        # Initialize services
        db_session = current_app.db.session
        expense_service = BasicExpenseTrackingService(db_session)
        upgrade_service = UpgradePromptsService(db_session)
        
        # Get various analytics
        expense_stats = expense_service.get_manual_entry_statistics(user_id)
        prompt_analytics = upgrade_service.get_prompt_analytics(user_id)
        
        analytics_data = {
            'expense_statistics': expense_stats,
            'prompt_analytics': prompt_analytics,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return success_response(analytics_data, "Dashboard analytics retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting dashboard analytics: {e}")
        return error_response("Failed to retrieve dashboard analytics", 500) 