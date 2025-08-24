"""
Budget Tier Intelligent Insights API Routes

This module provides API endpoints for intelligent insights functionality:
- Unusual spending detection
- Subscription service identification
- Bill due date predictions
- Cash flow optimization suggestions
- Financial goal progress tracking
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from backend.services.budget_tier_service import BudgetTierService
from backend.services.budget_tier_insights_service import BudgetTierInsightsService
from backend.services.tier_access_control_service import TierAccessControlService
from backend.services.notification_service import NotificationService
from backend.utils.validation import validate_amount, validate_date
from backend.utils.response import success_response, error_response
from backend.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

# Create Blueprint
budget_insights_bp = Blueprint('budget_insights', __name__, url_prefix='/api/budget-insights')


@budget_insights_bp.route('/comprehensive', methods=['GET'])
@login_required
def get_comprehensive_insights():
    """
    Get comprehensive intelligent insights for Budget tier users
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 90)
    
    Returns:
    {
        "success": true,
        "insights": {
            "unusual_spending": [...],
            "subscriptions": [...],
            "bill_predictions": [...],
            "cash_flow_optimization": [...],
            "goal_progress": [...]
        },
        "summary": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        days_back = int(request.args.get('days_back', 90))
        
        # Validate parameters
        if days_back < 30 or days_back > 365:
            return error_response("days_back must be between 30 and 365", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        insights_service = BudgetTierInsightsService(db_session, budget_service)
        
        # Generate comprehensive insights
        result = insights_service.generate_comprehensive_insights(user_id, days_back)
        
        if result['success']:
            return success_response("Insights generated successfully", result)
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting comprehensive insights: {str(e)}")
        return error_response("Internal server error", 500)


@budget_insights_bp.route('/unusual-spending', methods=['GET'])
@login_required
def get_unusual_spending_insights():
    """
    Get unusual spending detection insights
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 90)
    - threshold: Unusual spending threshold multiplier (default: 2.0)
    
    Returns:
    {
        "success": true,
        "insights": [...],
        "summary": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        days_back = int(request.args.get('days_back', 90))
        threshold = float(request.args.get('threshold', 2.0))
        
        # Validate parameters
        if days_back < 30 or days_back > 365:
            return error_response("days_back must be between 30 and 365", 400)
        if threshold < 1.0 or threshold > 5.0:
            return error_response("threshold must be between 1.0 and 5.0", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        insights_service = BudgetTierInsightsService(db_session, budget_service)
        
        # Set custom threshold
        insights_service.unusual_spending_threshold = threshold
        
        # Generate insights
        result = insights_service.generate_comprehensive_insights(user_id, days_back)
        
        if result['success']:
            unusual_spending = result['insights']['unusual_spending']
            return success_response("Unusual spending insights retrieved successfully", {
                'insights': unusual_spending,
                'summary': {
                    'total_insights': len(unusual_spending),
                    'threshold_used': threshold,
                    'analysis_period_days': days_back
                }
            })
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting unusual spending insights: {str(e)}")
        return error_response("Internal server error", 500)


@budget_insights_bp.route('/subscriptions', methods=['GET'])
@login_required
def get_subscription_insights():
    """
    Get subscription service identification insights
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 90)
    - confidence_threshold: Minimum confidence score (default: 0.7)
    
    Returns:
    {
        "success": true,
        "insights": [...],
        "summary": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        days_back = int(request.args.get('days_back', 90))
        confidence_threshold = float(request.args.get('confidence_threshold', 0.7))
        
        # Validate parameters
        if days_back < 30 or days_back > 365:
            return error_response("days_back must be between 30 and 365", 400)
        if confidence_threshold < 0.0 or confidence_threshold > 1.0:
            return error_response("confidence_threshold must be between 0.0 and 1.0", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        insights_service = BudgetTierInsightsService(db_session, budget_service)
        
        # Set custom confidence threshold
        insights_service.subscription_confidence_threshold = confidence_threshold
        
        # Generate insights
        result = insights_service.generate_comprehensive_insights(user_id, days_back)
        
        if result['success']:
            subscriptions = result['insights']['subscriptions']
            return success_response("Subscription insights retrieved successfully", {
                'insights': subscriptions,
                'summary': {
                    'total_subscriptions': len(subscriptions),
                    'confidence_threshold': confidence_threshold,
                    'analysis_period_days': days_back,
                    'total_monthly_cost': sum(
                        float(sub['amount']) for sub in subscriptions 
                        if sub['frequency'] == 'monthly'
                    )
                }
            })
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting subscription insights: {str(e)}")
        return error_response("Internal server error", 500)


@budget_insights_bp.route('/bill-predictions', methods=['GET'])
@login_required
def get_bill_prediction_insights():
    """
    Get bill due date prediction insights
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 90)
    - confidence_threshold: Minimum confidence score (default: 0.6)
    
    Returns:
    {
        "success": true,
        "insights": [...],
        "summary": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        days_back = int(request.args.get('days_back', 90))
        confidence_threshold = float(request.args.get('confidence_threshold', 0.6))
        
        # Validate parameters
        if days_back < 30 or days_back > 365:
            return error_response("days_back must be between 30 and 365", 400)
        if confidence_threshold < 0.0 or confidence_threshold > 1.0:
            return error_response("confidence_threshold must be between 0.0 and 1.0", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        insights_service = BudgetTierInsightsService(db_session, budget_service)
        
        # Set custom confidence threshold
        insights_service.bill_prediction_confidence_threshold = confidence_threshold
        
        # Generate insights
        result = insights_service.generate_comprehensive_insights(user_id, days_back)
        
        if result['success']:
            bill_predictions = result['insights']['bill_predictions']
            
            # Filter upcoming bills (due within next 30 days)
            upcoming_bills = [
                bill for bill in bill_predictions
                if datetime.strptime(bill['predicted_due_date'], '%Y-%m-%d').date() <= date.today() + timedelta(days=30)
            ]
            
            return success_response("Bill prediction insights retrieved successfully", {
                'insights': bill_predictions,
                'upcoming_bills': upcoming_bills,
                'summary': {
                    'total_bills': len(bill_predictions),
                    'upcoming_bills_count': len(upcoming_bills),
                    'confidence_threshold': confidence_threshold,
                    'analysis_period_days': days_back,
                    'total_predicted_amount': sum(
                        float(bill['predicted_amount']) for bill in upcoming_bills
                    )
                }
            })
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting bill prediction insights: {str(e)}")
        return error_response("Internal server error", 500)


@budget_insights_bp.route('/cash-flow-optimization', methods=['GET'])
@login_required
def get_cash_flow_optimization_insights():
    """
    Get cash flow optimization suggestions
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 90)
    
    Returns:
    {
        "success": true,
        "insights": [...],
        "summary": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        days_back = int(request.args.get('days_back', 90))
        
        # Validate parameters
        if days_back < 30 or days_back > 365:
            return error_response("days_back must be between 30 and 365", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        insights_service = BudgetTierInsightsService(db_session, budget_service)
        
        # Generate insights
        result = insights_service.generate_comprehensive_insights(user_id, days_back)
        
        if result['success']:
            optimizations = result['insights']['cash_flow_optimization']
            
            # Calculate total potential savings
            total_potential_savings = sum(
                float(opt['potential_savings']) for opt in optimizations
            )
            
            return success_response("Cash flow optimization insights retrieved successfully", {
                'insights': optimizations,
                'summary': {
                    'total_optimizations': len(optimizations),
                    'total_potential_savings': total_potential_savings,
                    'analysis_period_days': days_back,
                    'optimization_types': list(set(opt['insight_type'] for opt in optimizations))
                }
            })
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting cash flow optimization insights: {str(e)}")
        return error_response("Internal server error", 500)


@budget_insights_bp.route('/goal-progress', methods=['GET'])
@login_required
def get_goal_progress_insights():
    """
    Get financial goal progress tracking insights
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 90)
    
    Returns:
    {
        "success": true,
        "insights": [...],
        "summary": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        days_back = int(request.args.get('days_back', 90))
        
        # Validate parameters
        if days_back < 30 or days_back > 365:
            return error_response("days_back must be between 30 and 365", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        insights_service = BudgetTierInsightsService(db_session, budget_service)
        
        # Generate insights
        result = insights_service.generate_comprehensive_insights(user_id, days_back)
        
        if result['success']:
            goal_progress = result['insights']['goal_progress']
            
            # Calculate summary statistics
            on_track_goals = [goal for goal in goal_progress if goal['on_track']]
            total_progress = sum(goal['current_progress'] for goal in goal_progress)
            avg_progress = total_progress / len(goal_progress) if goal_progress else 0
            
            return success_response("Goal progress insights retrieved successfully", {
                'insights': goal_progress,
                'summary': {
                    'total_goals': len(goal_progress),
                    'on_track_goals': len(on_track_goals),
                    'average_progress': avg_progress,
                    'analysis_period_days': days_back,
                    'goal_types': list(set(goal['goal_type'] for goal in goal_progress))
                }
            })
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting goal progress insights: {str(e)}")
        return error_response("Internal server error", 500)


@budget_insights_bp.route('/insights-summary', methods=['GET'])
@login_required
def get_insights_summary():
    """
    Get a summary of all intelligent insights
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 90)
    
    Returns:
    {
        "success": true,
        "summary": {
            "total_insights": 15,
            "insights_by_type": {...},
            "key_recommendations": [...],
            "potential_savings": 250.00
        }
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        days_back = int(request.args.get('days_back', 90))
        
        # Validate parameters
        if days_back < 30 or days_back > 365:
            return error_response("days_back must be between 30 and 365", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        insights_service = BudgetTierInsightsService(db_session, budget_service)
        
        # Generate comprehensive insights
        result = insights_service.generate_comprehensive_insights(user_id, days_back)
        
        if result['success']:
            insights = result['insights']
            
            # Calculate summary statistics
            total_insights = sum(len(insight_list) for insight_list in insights.values())
            
            insights_by_type = {
                'unusual_spending': len(insights['unusual_spending']),
                'subscriptions': len(insights['subscriptions']),
                'bill_predictions': len(insights['bill_predictions']),
                'cash_flow_optimization': len(insights['cash_flow_optimization']),
                'goal_progress': len(insights['goal_progress'])
            }
            
            # Calculate total potential savings
            total_potential_savings = sum(
                float(opt['potential_savings']) for opt in insights['cash_flow_optimization']
            )
            
            # Generate key recommendations
            key_recommendations = []
            
            # Add top optimization recommendations
            optimizations = insights['cash_flow_optimization']
            if optimizations:
                top_optimization = max(optimizations, key=lambda x: float(x['potential_savings']))
                key_recommendations.append({
                    'type': 'optimization',
                    'title': top_optimization['title'],
                    'description': top_optimization['description'],
                    'potential_savings': top_optimization['potential_savings']
                })
            
            # Add unusual spending alerts
            unusual_spending = insights['unusual_spending']
            if unusual_spending:
                critical_spending = [s for s in unusual_spending if s['severity'] in ['alert', 'critical']]
                if critical_spending:
                    key_recommendations.append({
                        'type': 'alert',
                        'title': 'Unusual Spending Detected',
                        'description': f"{len(critical_spending)} transactions with unusual spending patterns",
                        'count': len(critical_spending)
                    })
            
            # Add subscription insights
            subscriptions = insights['subscriptions']
            if subscriptions:
                monthly_cost = sum(
                    float(sub['amount']) for sub in subscriptions 
                    if sub['frequency'] == 'monthly'
                )
                key_recommendations.append({
                    'type': 'subscription',
                    'title': 'Subscription Services',
                    'description': f"Track {len(subscriptions)} subscription services",
                    'monthly_cost': monthly_cost
                })
            
            return success_response("Insights summary retrieved successfully", {
                'summary': {
                    'total_insights': total_insights,
                    'insights_by_type': insights_by_type,
                    'key_recommendations': key_recommendations,
                    'potential_savings': total_potential_savings,
                    'analysis_period_days': days_back
                }
            })
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting insights summary: {str(e)}")
        return error_response("Internal server error", 500)


@budget_insights_bp.route('/alerts', methods=['GET'])
@login_required
def get_insights_alerts():
    """
    Get high-priority insights alerts
    
    Query Parameters:
    - days_back: Number of days to analyze (default: 30)
    
    Returns:
    {
        "success": true,
        "alerts": [...],
        "summary": {...}
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Get query parameters
        days_back = int(request.args.get('days_back', 30))
        
        # Validate parameters
        if days_back < 7 or days_back > 90:
            return error_response("days_back must be between 7 and 90", 400)
        
        # Initialize services
        db_session = current_app.config['db_session']
        tier_service = TierAccessControlService(db_session, current_app.config)
        notification_service = NotificationService(db_session, current_app.config)
        budget_service = BudgetTierService(db_session, tier_service, notification_service)
        insights_service = BudgetTierInsightsService(db_session, budget_service)
        
        # Generate insights
        result = insights_service.generate_comprehensive_insights(user_id, days_back)
        
        if result['success']:
            insights = result['insights']
            alerts = []
            
            # Critical unusual spending
            unusual_spending = insights['unusual_spending']
            critical_spending = [
                spending for spending in unusual_spending 
                if spending['severity'] in ['alert', 'critical']
            ]
            if critical_spending:
                alerts.append({
                    'type': 'unusual_spending',
                    'severity': 'high',
                    'title': 'Unusual Spending Alert',
                    'description': f"{len(critical_spending)} transactions with unusual spending patterns",
                    'count': len(critical_spending),
                    'insights': critical_spending[:3]  # Top 3
                })
            
            # Upcoming bills
            bill_predictions = insights['bill_predictions']
            upcoming_bills = [
                bill for bill in bill_predictions
                if datetime.strptime(bill['predicted_due_date'], '%Y-%m-%d').date() <= date.today() + timedelta(days=7)
            ]
            if upcoming_bills:
                alerts.append({
                    'type': 'bill_due',
                    'severity': 'medium',
                    'title': 'Bills Due Soon',
                    'description': f"{len(upcoming_bills)} bills due within 7 days",
                    'count': len(upcoming_bills),
                    'insights': upcoming_bills
                })
            
            # High-cost subscriptions
            subscriptions = insights['subscriptions']
            high_cost_subscriptions = [
                sub for sub in subscriptions
                if float(sub['amount']) > 50.0  # Subscriptions over $50
            ]
            if high_cost_subscriptions:
                alerts.append({
                    'type': 'high_cost_subscription',
                    'severity': 'medium',
                    'title': 'High-Cost Subscriptions',
                    'description': f"{len(high_cost_subscriptions)} subscriptions over $50/month",
                    'count': len(high_cost_subscriptions),
                    'insights': high_cost_subscriptions
                })
            
            return success_response("Insights alerts retrieved successfully", {
                'alerts': alerts,
                'summary': {
                    'total_alerts': len(alerts),
                    'high_priority_alerts': len([a for a in alerts if a['severity'] == 'high']),
                    'analysis_period_days': days_back
                }
            })
        else:
            return error_response(result['error'], 400)
            
    except Exception as e:
        logger.error(f"Error getting insights alerts: {str(e)}")
        return error_response("Internal server error", 500)


# Error handlers
@budget_insights_bp.errorhandler(400)
def bad_request(error):
    return error_response("Bad request", 400)


@budget_insights_bp.errorhandler(401)
def unauthorized(error):
    return error_response("Unauthorized", 401)


@budget_insights_bp.errorhandler(403)
def forbidden(error):
    return error_response("Forbidden", 403)


@budget_insights_bp.errorhandler(404)
def not_found(error):
    return error_response("Not found", 404)


@budget_insights_bp.errorhandler(500)
def internal_error(error):
    return error_response("Internal server error", 500) 