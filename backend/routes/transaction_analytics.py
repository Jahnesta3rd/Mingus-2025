"""
Transaction Analytics API Routes

This module provides API endpoints for transaction processing, analysis,
and insight generation for MINGUS users.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.services.transaction_processor import TransactionProcessor
from backend.services.analytics_service import AnalyticsService
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.models.analytics import (
    TransactionInsight, SpendingCategory, BudgetAlert, 
    SpendingPattern, AnomalyDetection, SubscriptionAnalysis,
    FinancialInsight, AnalyticsReport
)

logger = logging.getLogger(__name__)

transaction_analytics_bp = Blueprint('transaction_analytics', __name__, url_prefix='/api/transaction-analytics')


@transaction_analytics_bp.route('/process', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def process_transactions():
    """
    Process transactions and generate insights
    
    Request body:
    {
        "account_ids": ["account1", "account2"],  # Optional
        "date_range": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31"
        },  # Optional
        "force_reprocess": false  # Optional
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'account_ids': {'type': 'list', 'required': False},
            'date_range': {'type': 'dict', 'required': False},
            'force_reprocess': {'type': 'bool', 'required': False, 'default': False}
        })
        
        # Parse date range if provided
        date_range = None
        if data.get('date_range'):
            start_date = datetime.fromisoformat(data['date_range']['start_date'])
            end_date = datetime.fromisoformat(data['date_range']['end_date'])
            date_range = (start_date, end_date)
        
        # Initialize services
        db_session = current_app.db.session
        analytics_service = AnalyticsService(db_session)
        processor = TransactionProcessor(db_session, analytics_service)
        
        # Process transactions
        result = processor.process_transactions(
            user_id=current_user.id,
            account_ids=data.get('account_ids'),
            date_range=date_range
        )
        
        if result['success']:
            return create_response(
                success=True,
                message=result['message'],
                data={
                    'processed_count': result['processed_count'],
                    'insights_summary': result['summary'],
                    'insights_count': len(result['insights'])
                }
            )
        else:
            return create_response(
                success=False,
                message=f"Processing failed: {result['error']}",
                status_code=500
            )
            
    except Exception as e:
        logger.error(f"Error processing transactions: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during transaction processing",
            status_code=500
        )


@transaction_analytics_bp.route('/insights', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_insights():
    """
    Get transaction insights for the current user
    
    Query parameters:
    - insight_type: Type of insight to retrieve
    - category: Filter by category
    - date_range: Date range filter
    - limit: Number of insights to return
    """
    try:
        insight_type = request.args.get('insight_type')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        
        # Build query
        query = current_app.db.session.query(TransactionInsight).filter(
            TransactionInsight.user_id == current_user.id
        )
        
        if insight_type:
            query = query.filter(TransactionInsight.transaction_type == insight_type)
        
        if category:
            query = query.filter(TransactionInsight.category == category)
        
        # Apply date range if provided
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(
                TransactionInsight.created_at.between(start_dt, end_dt)
            )
        
        # Get results
        insights = query.order_by(TransactionInsight.created_at.desc()).limit(limit).all()
        
        # Format response
        insights_data = []
        for insight in insights:
            insights_data.append({
                'id': str(insight.id),
                'transaction_id': insight.transaction_id,
                'category': insight.category,
                'confidence': insight.confidence,
                'transaction_type': insight.transaction_type,
                'merchant_name': insight.merchant_name,
                'is_recurring': insight.is_recurring,
                'is_subscription': insight.is_subscription,
                'is_anomaly': insight.is_anomaly,
                'risk_score': insight.risk_score,
                'fraud_score': insight.fraud_score,
                'insights': insight.insights,
                'tags': insight.tags,
                'created_at': insight.created_at.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(insights_data)} insights",
            data={
                'insights': insights_data,
                'total_count': len(insights_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving insights: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving insights",
            status_code=500
        )


@transaction_analytics_bp.route('/spending-categories', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_spending_categories():
    """
    Get spending category analysis for the current user
    
    Query parameters:
    - period: Analysis period (week, month, quarter, year)
    - start_date: Start date for custom period
    - end_date: End date for custom period
    """
    try:
        period = request.args.get('period', 'month')
        
        # Calculate date range based on period
        end_date = datetime.now()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'quarter':
            start_date = end_date - timedelta(days=90)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            # Custom period
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            if start_date_str and end_date_str:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
            else:
                start_date = end_date - timedelta(days=30)
        
        # Query spending categories
        categories = current_app.db.session.query(SpendingCategory).filter(
            and_(
                SpendingCategory.user_id == current_user.id,
                SpendingCategory.period_start >= start_date,
                SpendingCategory.period_end <= end_date
            )
        ).order_by(SpendingCategory.total_amount.desc()).all()
        
        # Format response
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': str(category.id),
                'category_name': category.category_name,
                'total_amount': category.total_amount,
                'transaction_count': category.transaction_count,
                'average_amount': category.average_amount,
                'trend_direction': category.trend_direction,
                'percentage_change': category.percentage_change,
                'trend_period': category.trend_period,
                'budget_limit': category.budget_limit,
                'budget_used': category.budget_used,
                'budget_percentage': category.budget_percentage,
                'recommendations': category.recommendations,
                'period_start': category.period_start.isoformat(),
                'period_end': category.period_end.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(categories_data)} spending categories",
            data={
                'categories': categories_data,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving spending categories: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving spending categories",
            status_code=500
        )


@transaction_analytics_bp.route('/budget-alerts', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_budget_alerts():
    """
    Get budget alerts for the current user
    
    Query parameters:
    - alert_level: Filter by alert level (low, medium, high)
    - is_active: Filter by active status
    - limit: Number of alerts to return
    """
    try:
        alert_level = request.args.get('alert_level')
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        
        # Build query
        query = current_app.db.session.query(BudgetAlert).filter(
            and_(
                BudgetAlert.user_id == current_user.id,
                BudgetAlert.is_active == is_active
            )
        )
        
        if alert_level:
            query = query.filter(BudgetAlert.alert_level == alert_level)
        
        # Get results
        alerts = query.order_by(BudgetAlert.alert_date.desc()).limit(limit).all()
        
        # Format response
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': str(alert.id),
                'category_name': alert.category_name,
                'alert_type': alert.alert_type,
                'alert_level': alert.alert_level,
                'current_spending': alert.current_spending,
                'budget_limit': alert.budget_limit,
                'percentage_used': alert.percentage_used,
                'days_remaining': alert.days_remaining,
                'alert_date': alert.alert_date.isoformat(),
                'is_dismissed': alert.is_dismissed,
                'recommendations': alert.recommendations
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(alerts_data)} budget alerts",
            data={
                'alerts': alerts_data,
                'active_count': len([a for a in alerts_data if not a['is_dismissed']])
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving budget alerts: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving budget alerts",
            status_code=500
        )


@transaction_analytics_bp.route('/budget-alerts/<alert_id>/dismiss', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def dismiss_budget_alert(alert_id: str):
    """
    Dismiss a budget alert
    
    Path parameters:
    - alert_id: ID of the alert to dismiss
    """
    try:
        # Find the alert
        alert = current_app.db.session.query(BudgetAlert).filter(
            and_(
                BudgetAlert.id == alert_id,
                BudgetAlert.user_id == current_user.id
            )
        ).first()
        
        if not alert:
            return create_response(
                success=False,
                message="Budget alert not found",
                status_code=404
            )
        
        # Dismiss the alert
        alert.is_dismissed = True
        alert.dismissed_at = datetime.now()
        alert.dismissed_by = current_user.id
        
        current_app.db.session.commit()
        
        return create_response(
            success=True,
            message="Budget alert dismissed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error dismissing budget alert: {str(e)}")
        current_app.db.session.rollback()
        return create_response(
            success=False,
            message="Internal server error dismissing alert",
            status_code=500
        )


@transaction_analytics_bp.route('/spending-patterns', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_spending_patterns():
    """
    Get spending patterns for the current user
    
    Query parameters:
    - pattern_type: Filter by pattern type (daily, weekly, monthly, seasonal)
    - category: Filter by category
    - is_active: Filter by active status
    """
    try:
        pattern_type = request.args.get('pattern_type')
        category = request.args.get('category')
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        
        # Build query
        query = current_app.db.session.query(SpendingPattern).filter(
            and_(
                SpendingPattern.user_id == current_user.id,
                SpendingPattern.is_active == is_active
            )
        )
        
        if pattern_type:
            query = query.filter(SpendingPattern.pattern_type == pattern_type)
        
        if category:
            query = query.filter(SpendingPattern.category_name == category)
        
        # Get results
        patterns = query.order_by(SpendingPattern.frequency.desc()).all()
        
        # Format response
        patterns_data = []
        for pattern in patterns:
            patterns_data.append({
                'id': str(pattern.id),
                'pattern_type': pattern.pattern_type,
                'category_name': pattern.category_name,
                'merchant_name': pattern.merchant_name,
                'frequency': pattern.frequency,
                'average_amount': pattern.average_amount,
                'total_amount': pattern.total_amount,
                'day_of_week': pattern.day_of_week,
                'day_of_month': pattern.day_of_month,
                'month_of_year': pattern.month_of_year,
                'hour_of_day': pattern.hour_of_day,
                'confidence_score': pattern.confidence_score,
                'reliability_score': pattern.reliability_score,
                'first_occurrence': pattern.first_occurrence.isoformat(),
                'last_occurrence': pattern.last_occurrence.isoformat(),
                'next_predicted': pattern.next_predicted.isoformat() if pattern.next_predicted else None,
                'is_recurring': pattern.is_recurring
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(patterns_data)} spending patterns",
            data={'patterns': patterns_data}
        )
        
    except Exception as e:
        logger.error(f"Error retrieving spending patterns: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving spending patterns",
            status_code=500
        )


@transaction_analytics_bp.route('/anomalies', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_anomalies():
    """
    Get anomaly detections for the current user
    
    Query parameters:
    - anomaly_type: Filter by anomaly type
    - severity: Filter by severity level
    - is_confirmed: Filter by confirmation status
    - limit: Number of anomalies to return
    """
    try:
        anomaly_type = request.args.get('anomaly_type')
        severity = request.args.get('severity')
        is_confirmed = request.args.get('is_confirmed')
        limit = int(request.args.get('limit', 20))
        
        # Build query
        query = current_app.db.session.query(AnomalyDetection).filter(
            AnomalyDetection.user_id == current_user.id
        )
        
        if anomaly_type:
            query = query.filter(AnomalyDetection.anomaly_type == anomaly_type)
        
        if severity:
            query = query.filter(AnomalyDetection.severity == severity)
        
        if is_confirmed is not None:
            is_confirmed_bool = is_confirmed.lower() == 'true'
            query = query.filter(AnomalyDetection.is_confirmed == is_confirmed_bool)
        
        # Get results
        anomalies = query.order_by(AnomalyDetection.detected_at.desc()).limit(limit).all()
        
        # Format response
        anomalies_data = []
        for anomaly in anomalies:
            anomalies_data.append({
                'id': str(anomaly.id),
                'transaction_id': anomaly.transaction_id,
                'anomaly_type': anomaly.anomaly_type,
                'severity': anomaly.severity,
                'confidence': anomaly.confidence,
                'expected_value': anomaly.expected_value,
                'actual_value': anomaly.actual_value,
                'deviation_percentage': anomaly.deviation_percentage,
                'category_name': anomaly.category_name,
                'merchant_name': anomaly.merchant_name,
                'location': anomaly.location,
                'detection_method': anomaly.detection_method,
                'is_confirmed': anomaly.is_confirmed,
                'is_false_positive': anomaly.is_false_positive,
                'user_feedback': anomaly.user_feedback,
                'detected_at': anomaly.detected_at.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(anomalies_data)} anomalies",
            data={'anomalies': anomalies_data}
        )
        
    except Exception as e:
        logger.error(f"Error retrieving anomalies: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving anomalies",
            status_code=500
        )


@transaction_analytics_bp.route('/anomalies/<anomaly_id>/feedback', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def provide_anomaly_feedback(anomaly_id: str):
    """
    Provide feedback on an anomaly detection
    
    Path parameters:
    - anomaly_id: ID of the anomaly
    
    Request body:
    {
        "feedback": "confirmed|false_positive|ignored",
        "notes": "Optional notes"
    }
    """
    try:
        data = validate_request_data(request.get_json(), {
            'feedback': {'type': 'str', 'required': True, 'allowed': ['confirmed', 'false_positive', 'ignored']},
            'notes': {'type': 'str', 'required': False}
        })
        
        # Find the anomaly
        anomaly = current_app.db.session.query(AnomalyDetection).filter(
            and_(
                AnomalyDetection.id == anomaly_id,
                AnomalyDetection.user_id == current_user.id
            )
        ).first()
        
        if not anomaly:
            return create_response(
                success=False,
                message="Anomaly not found",
                status_code=404
            )
        
        # Update feedback
        anomaly.user_feedback = data['feedback']
        anomaly.is_confirmed = data['feedback'] == 'confirmed'
        anomaly.is_false_positive = data['feedback'] == 'false_positive'
        
        current_app.db.session.commit()
        
        return create_response(
            success=True,
            message="Anomaly feedback recorded successfully"
        )
        
    except Exception as e:
        logger.error(f"Error recording anomaly feedback: {str(e)}")
        current_app.db.session.rollback()
        return create_response(
            success=False,
            message="Internal server error recording feedback",
            status_code=500
        )


@transaction_analytics_bp.route('/subscriptions', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_subscription_analysis():
    """
    Get subscription analysis for the current user
    
    Query parameters:
    - is_active: Filter by active status
    - recommendation: Filter by recommendation
    """
    try:
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        recommendation = request.args.get('recommendation')
        
        # Build query
        query = current_app.db.session.query(SubscriptionAnalysis).filter(
            and_(
                SubscriptionAnalysis.user_id == current_user.id,
                SubscriptionAnalysis.is_active == is_active
            )
        )
        
        if recommendation:
            query = query.filter(SubscriptionAnalysis.recommendation == recommendation)
        
        # Get results
        subscriptions = query.order_by(SubscriptionAnalysis.monthly_cost.desc()).all()
        
        # Format response
        subscriptions_data = []
        total_monthly_cost = 0
        total_annual_cost = 0
        
        for subscription in subscriptions:
            subscriptions_data.append({
                'id': str(subscription.id),
                'merchant_name': subscription.merchant_name,
                'subscription_name': subscription.subscription_name,
                'monthly_cost': subscription.monthly_cost,
                'annual_cost': subscription.annual_cost,
                'total_spent': subscription.total_spent,
                'transaction_count': subscription.transaction_count,
                'first_transaction': subscription.first_transaction.isoformat(),
                'last_transaction': subscription.last_transaction.isoformat(),
                'next_expected': subscription.next_expected.isoformat() if subscription.next_expected else None,
                'billing_cycle': subscription.billing_cycle,
                'category': subscription.category,
                'usage_score': subscription.usage_score,
                'cost_score': subscription.cost_score,
                'recommendation': subscription.recommendation,
                'user_rating': subscription.user_rating,
                'user_notes': subscription.user_notes
            })
            
            total_monthly_cost += subscription.monthly_cost
            total_annual_cost += subscription.annual_cost
        
        return create_response(
            success=True,
            message=f"Retrieved {len(subscriptions_data)} subscriptions",
            data={
                'subscriptions': subscriptions_data,
                'summary': {
                    'total_subscriptions': len(subscriptions_data),
                    'total_monthly_cost': total_monthly_cost,
                    'total_annual_cost': total_annual_cost
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving subscription analysis: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving subscription analysis",
            status_code=500
        )


@transaction_analytics_bp.route('/financial-insights', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_financial_insights():
    """
    Get financial insights for the current user
    
    Query parameters:
    - insight_type: Filter by insight type
    - priority: Filter by priority level
    - is_actionable: Filter by actionable status
    - limit: Number of insights to return
    """
    try:
        insight_type = request.args.get('insight_type')
        priority = request.args.get('priority')
        is_actionable = request.args.get('is_actionable')
        limit = int(request.args.get('limit', 20))
        
        # Build query
        query = current_app.db.session.query(FinancialInsight).filter(
            and_(
                FinancialInsight.user_id == current_user.id,
                FinancialInsight.is_active == True,
                FinancialInsight.is_dismissed == False
            )
        )
        
        if insight_type:
            query = query.filter(FinancialInsight.insight_type == insight_type)
        
        if priority:
            query = query.filter(FinancialInsight.priority == priority)
        
        if is_actionable is not None:
            is_actionable_bool = is_actionable.lower() == 'true'
            query = query.filter(FinancialInsight.is_actionable == is_actionable_bool)
        
        # Get results
        insights = query.order_by(
            FinancialInsight.priority.desc(),
            FinancialInsight.impact_score.desc()
        ).limit(limit).all()
        
        # Format response
        insights_data = []
        for insight in insights:
            insights_data.append({
                'id': str(insight.id),
                'insight_type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'data': insight.data,
                'metrics': insight.metrics,
                'impact_score': insight.impact_score,
                'priority': insight.priority,
                'is_actionable': insight.is_actionable,
                'action_type': insight.action_type,
                'action_description': insight.action_description,
                'generated_at': insight.generated_at.isoformat()
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(insights_data)} financial insights",
            data={'insights': insights_data}
        )
        
    except Exception as e:
        logger.error(f"Error retrieving financial insights: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving financial insights",
            status_code=500
        )


@transaction_analytics_bp.route('/financial-insights/<insight_id>/dismiss', methods=['POST'])
@login_required
@require_auth
@handle_api_errors
def dismiss_financial_insight(insight_id: str):
    """
    Dismiss a financial insight
    
    Path parameters:
    - insight_id: ID of the insight to dismiss
    """
    try:
        # Find the insight
        insight = current_app.db.session.query(FinancialInsight).filter(
            and_(
                FinancialInsight.id == insight_id,
                FinancialInsight.user_id == current_user.id
            )
        ).first()
        
        if not insight:
            return create_response(
                success=False,
                message="Financial insight not found",
                status_code=404
            )
        
        # Dismiss the insight
        insight.is_dismissed = True
        insight.dismissed_at = datetime.now()
        
        current_app.db.session.commit()
        
        return create_response(
            success=True,
            message="Financial insight dismissed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error dismissing financial insight: {str(e)}")
        current_app.db.session.rollback()
        return create_response(
            success=False,
            message="Internal server error dismissing insight",
            status_code=500
        )


@transaction_analytics_bp.route('/reports', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_analytics_reports():
    """
    Get analytics reports for the current user
    
    Query parameters:
    - report_type: Filter by report type
    - status: Filter by report status
    - limit: Number of reports to return
    """
    try:
        report_type = request.args.get('report_type')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 10))
        
        # Build query
        query = current_app.db.session.query(AnalyticsReport).filter(
            AnalyticsReport.user_id == current_user.id
        )
        
        if report_type:
            query = query.filter(AnalyticsReport.report_type == report_type)
        
        if status:
            query = query.filter(AnalyticsReport.status == status)
        
        # Get results
        reports = query.order_by(AnalyticsReport.generated_at.desc()).limit(limit).all()
        
        # Format response
        reports_data = []
        for report in reports:
            reports_data.append({
                'id': str(report.id),
                'report_type': report.report_type,
                'report_name': report.report_name,
                'description': report.description,
                'period_start': report.period_start.isoformat(),
                'period_end': report.period_end.isoformat(),
                'status': report.status,
                'generated_at': report.generated_at.isoformat(),
                'delivered_at': report.delivered_at.isoformat() if report.delivered_at else None,
                'viewed_at': report.viewed_at.isoformat() if report.viewed_at else None
            })
        
        return create_response(
            success=True,
            message=f"Retrieved {len(reports_data)} analytics reports",
            data={'reports': reports_data}
        )
        
    except Exception as e:
        logger.error(f"Error retrieving analytics reports: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving analytics reports",
            status_code=500
        )


@transaction_analytics_bp.route('/reports/<report_id>', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_analytics_report(report_id: str):
    """
    Get a specific analytics report
    
    Path parameters:
    - report_id: ID of the report to retrieve
    """
    try:
        # Find the report
        report = current_app.db.session.query(AnalyticsReport).filter(
            and_(
                AnalyticsReport.id == report_id,
                AnalyticsReport.user_id == current_user.id
            )
        ).first()
        
        if not report:
            return create_response(
                success=False,
                message="Analytics report not found",
                status_code=404
            )
        
        # Mark as viewed if not already
        if not report.viewed_at:
            report.viewed_at = datetime.now()
            current_app.db.session.commit()
        
        return create_response(
            success=True,
            message="Analytics report retrieved successfully",
            data={
                'id': str(report.id),
                'report_type': report.report_type,
                'report_name': report.report_name,
                'description': report.description,
                'period_start': report.period_start.isoformat(),
                'period_end': report.period_end.isoformat(),
                'data': report.data,
                'summary': report.summary,
                'charts': report.charts,
                'status': report.status,
                'generated_at': report.generated_at.isoformat(),
                'delivered_at': report.delivered_at.isoformat() if report.delivered_at else None,
                'viewed_at': report.viewed_at.isoformat() if report.viewed_at else None
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving analytics report: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving analytics report",
            status_code=500
        )


@transaction_analytics_bp.route('/summary', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_analytics_summary():
    """
    Get a comprehensive analytics summary for the current user
    """
    try:
        # Get summary statistics from various analytics tables
        db_session = current_app.db.session
        
        # Count insights
        insights_count = db_session.query(TransactionInsight).filter(
            TransactionInsight.user_id == current_user.id
        ).count()
        
        # Count active budget alerts
        active_alerts_count = db_session.query(BudgetAlert).filter(
            and_(
                BudgetAlert.user_id == current_user.id,
                BudgetAlert.is_active == True,
                BudgetAlert.is_dismissed == False
            )
        ).count()
        
        # Count active subscriptions
        active_subscriptions_count = db_session.query(SubscriptionAnalysis).filter(
            and_(
                SubscriptionAnalysis.user_id == current_user.id,
                SubscriptionAnalysis.is_active == True
            )
        ).count()
        
        # Count unconfirmed anomalies
        unconfirmed_anomalies_count = db_session.query(AnomalyDetection).filter(
            and_(
                AnomalyDetection.user_id == current_user.id,
                AnomalyDetection.is_confirmed == False
            )
        ).count()
        
        # Count actionable insights
        actionable_insights_count = db_session.query(FinancialInsight).filter(
            and_(
                FinancialInsight.user_id == current_user.id,
                FinancialInsight.is_actionable == True,
                FinancialInsight.is_active == True,
                FinancialInsight.is_dismissed == False
            )
        ).count()
        
        return create_response(
            success=True,
            message="Analytics summary retrieved successfully",
            data={
                'summary': {
                    'total_insights': insights_count,
                    'active_budget_alerts': active_alerts_count,
                    'active_subscriptions': active_subscriptions_count,
                    'unconfirmed_anomalies': unconfirmed_anomalies_count,
                    'actionable_insights': actionable_insights_count
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error retrieving analytics summary: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving analytics summary",
            status_code=500
        )


def register_transaction_analytics_routes(app):
    """Register transaction analytics routes with the Flask app"""
    app.register_blueprint(transaction_analytics_bp)
    logger.info("Transaction analytics routes registered successfully") 