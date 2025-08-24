"""
Financial Analysis API Routes

This module provides API endpoints for comprehensive financial analysis
including spending pattern analysis and monthly cash flow calculations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
from sqlalchemy import text

from backend.banking.financial_analyzer import FinancialAnalyzer, AnalysisPeriod
from backend.utils.auth_decorators import require_auth, handle_api_errors
from backend.utils.api_utils import validate_request_data, create_response
from backend.models.bank_account_models import PlaidTransaction

logger = logging.getLogger(__name__)

financial_analysis_bp = Blueprint('financial_analysis', __name__, url_prefix='/api/financial-analysis')


@financial_analysis_bp.route('/spending-patterns', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def analyze_spending_patterns():
    """
    Analyze spending patterns by category
    
    Query parameters:
    - period: Analysis period (daily, weekly, monthly, quarterly, yearly)
    - start_date: Start date for analysis
    - end_date: End date for analysis
    - categories: Filter by specific categories
    - account_ids: Filter by account IDs
    """
    try:
        # Parse query parameters
        period_str = request.args.get('period', 'monthly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        categories = request.args.getlist('categories')
        account_ids = request.args.getlist('account_ids')
        
        # Parse period
        try:
            period = AnalysisPeriod(period_str)
        except ValueError:
            return create_response(
                success=False,
                message=f"Invalid period: {period_str}. Valid options: daily, weekly, monthly, quarterly, yearly",
                status_code=400
            )
        
        # Parse date range
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = (start_date, end_date)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid date format. Use ISO format (YYYY-MM-DD)",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        # Analyze spending patterns
        patterns = analyzer.analyze_spending_patterns(
            user_id=current_user.id,
            period=period,
            date_range=date_range,
            categories=categories if categories else None
        )
        
        # Format response
        patterns_data = []
        for pattern in patterns:
            patterns_data.append({
                'category': pattern.category,
                'period': pattern.period.value,
                'start_date': pattern.start_date.isoformat(),
                'end_date': pattern.end_date.isoformat(),
                'total_amount': pattern.total_amount,
                'transaction_count': pattern.transaction_count,
                'average_amount': pattern.average_amount,
                'median_amount': pattern.median_amount,
                'min_amount': pattern.min_amount,
                'max_amount': pattern.max_amount,
                'trend_direction': pattern.trend_direction.value,
                'percentage_change': pattern.percentage_change,
                'trend_strength': pattern.trend_strength,
                'is_recurring': pattern.is_recurring,
                'frequency_score': pattern.frequency_score,
                'consistency_score': pattern.consistency_score,
                'category_rank': pattern.category_rank,
                'percentage_of_total': pattern.percentage_of_total,
                'average_daily_spending': pattern.average_daily_spending,
                'metadata': pattern.metadata
            })
        
        return create_response(
            success=True,
            message=f"Analyzed {len(patterns_data)} spending patterns",
            data={
                'patterns': patterns_data,
                'total_patterns': len(patterns_data),
                'analysis_period': period.value,
                'date_range': {
                    'start_date': date_range[0].isoformat() if date_range else None,
                    'end_date': date_range[1].isoformat() if date_range else None
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error analyzing spending patterns: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during spending pattern analysis",
            status_code=500
        )


@financial_analysis_bp.route('/cash-flow/monthly', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def calculate_monthly_cash_flow():
    """
    Calculate monthly cash flow
    
    Query parameters:
    - year: Year to analyze (default: current year)
    - months: Specific months to analyze (comma-separated)
    - account_ids: Filter by account IDs
    """
    try:
        # Parse query parameters
        year = request.args.get('year')
        months_str = request.args.get('months')
        account_ids = request.args.getlist('account_ids')
        
        # Parse year
        if year:
            try:
                year = int(year)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid year format",
                    status_code=400
                )
        
        # Parse months
        months = None
        if months_str:
            try:
                months = [int(m.strip()) for m in months_str.split(',')]
                # Validate months
                for month in months:
                    if month < 1 or month > 12:
                        raise ValueError(f"Invalid month: {month}")
            except ValueError as e:
                return create_response(
                    success=False,
                    message=f"Invalid months format: {str(e)}",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        # Calculate monthly cash flow
        cash_flows = analyzer.calculate_monthly_cash_flow(
            user_id=current_user.id,
            year=year,
            months=months
        )
        
        # Format response
        cash_flows_data = []
        for cf in cash_flows:
            cash_flows_data.append({
                'year': cf.year,
                'month': cf.month,
                'month_name': cf.month_name,
                'total_income': cf.total_income,
                'income_transactions': cf.income_transactions,
                'average_income': cf.average_income,
                'income_categories': cf.income_categories,
                'total_expenses': cf.total_expenses,
                'expense_transactions': cf.expense_transactions,
                'average_expense': cf.average_expense,
                'expense_categories': cf.expense_categories,
                'net_cash_flow': cf.net_cash_flow,
                'cash_flow_type': cf.cash_flow_type.value,
                'cash_flow_ratio': cf.cash_flow_ratio,
                'month_over_month_change': cf.month_over_month_change,
                'year_over_year_change': cf.year_over_year_change,
                'budget_variance': cf.budget_variance,
                'budget_percentage': cf.budget_percentage,
                'metadata': cf.metadata
            })
        
        return create_response(
            success=True,
            message=f"Calculated cash flow for {len(cash_flows_data)} months",
            data={
                'cash_flows': cash_flows_data,
                'total_months': len(cash_flows_data),
                'analysis_year': year,
                'total_income': sum(cf.total_income for cf in cash_flows),
                'total_expenses': sum(cf.total_expenses for cf in cash_flows),
                'net_cash_flow': sum(cf.net_cash_flow for cf in cash_flows)
            }
        )
        
    except Exception as e:
        logger.error(f"Error calculating monthly cash flow: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during cash flow calculation",
            status_code=500
        )


@financial_analysis_bp.route('/comprehensive', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def generate_comprehensive_analysis():
    """
    Generate comprehensive financial analysis
    
    Query parameters:
    - period: Analysis period (daily, weekly, monthly, quarterly, yearly)
    - start_date: Start date for analysis
    - end_date: End date for analysis
    - account_ids: Filter by account IDs
    - save_to_database: Save analysis results to database
    """
    try:
        # Parse query parameters
        period_str = request.args.get('period', 'monthly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        account_ids = request.args.getlist('account_ids')
        save_to_database = request.args.get('save_to_database', 'true').lower() == 'true'
        
        # Parse period
        try:
            period = AnalysisPeriod(period_str)
        except ValueError:
            return create_response(
                success=False,
                message=f"Invalid period: {period_str}. Valid options: daily, weekly, monthly, quarterly, yearly",
                status_code=400
            )
        
        # Parse date range
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = (start_date, end_date)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid date format. Use ISO format (YYYY-MM-DD)",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        # Generate comprehensive analysis
        analysis = analyzer.generate_financial_analysis(
            user_id=current_user.id,
            period=period,
            date_range=date_range
        )
        
        if not analysis:
            return create_response(
                success=False,
                message="No data available for analysis",
                status_code=404
            )
        
        # Save to database if requested
        if save_to_database:
            analyzer.save_analysis_to_database(analysis)
        
        # Format response
        return create_response(
            success=True,
            message="Generated comprehensive financial analysis",
            data={
                'user_id': analysis.user_id,
                'analysis_period': analysis.analysis_period.value,
                'start_date': analysis.start_date.isoformat(),
                'end_date': analysis.end_date.isoformat(),
                'overall_metrics': {
                    'total_income': analysis.total_income,
                    'total_expenses': analysis.total_expenses,
                    'net_cash_flow': analysis.net_cash_flow,
                    'savings_rate': analysis.savings_rate
                },
                'spending_patterns': [
                    {
                        'category': pattern.category,
                        'total_amount': pattern.total_amount,
                        'transaction_count': pattern.transaction_count,
                        'average_amount': pattern.average_amount,
                        'trend_direction': pattern.trend_direction.value,
                        'percentage_change': pattern.percentage_change,
                        'is_recurring': pattern.is_recurring,
                        'category_rank': pattern.category_rank,
                        'percentage_of_total': pattern.percentage_of_total
                    }
                    for pattern in analysis.spending_patterns
                ],
                'top_spending_categories': analysis.top_spending_categories,
                'spending_trends': analysis.spending_trends,
                'monthly_cash_flows': [
                    {
                        'year': cf.year,
                        'month': cf.month,
                        'month_name': cf.month_name,
                        'total_income': cf.total_income,
                        'total_expenses': cf.total_expenses,
                        'net_cash_flow': cf.net_cash_flow,
                        'cash_flow_type': cf.cash_flow_type.value,
                        'cash_flow_ratio': cf.cash_flow_ratio
                    }
                    for cf in analysis.monthly_cash_flows
                ],
                'cash_flow_trends': analysis.cash_flow_trends,
                'insights': analysis.insights,
                'recommendations': analysis.recommendations,
                'metadata': analysis.metadata
            }
        )
        
    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during analysis generation",
            status_code=500
        )


@financial_analysis_bp.route('/categories/top-spending', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_top_spending_categories():
    """
    Get top spending categories
    
    Query parameters:
    - limit: Number of categories to return (default: 5)
    - period: Analysis period
    - start_date: Start date for analysis
    - end_date: End date for analysis
    """
    try:
        # Parse query parameters
        limit = int(request.args.get('limit', 5))
        period_str = request.args.get('period', 'monthly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse period
        try:
            period = AnalysisPeriod(period_str)
        except ValueError:
            return create_response(
                success=False,
                message=f"Invalid period: {period_str}",
                status_code=400
            )
        
        # Parse date range
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = (start_date, end_date)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid date format",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        # Analyze spending patterns
        patterns = analyzer.analyze_spending_patterns(
            user_id=current_user.id,
            period=period,
            date_range=date_range
        )
        
        # Get top categories
        top_categories = analyzer._get_top_spending_categories(patterns, limit)
        
        return create_response(
            success=True,
            message=f"Retrieved top {len(top_categories)} spending categories",
            data={
                'categories': top_categories,
                'total_categories': len(top_categories),
                'analysis_period': period.value
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting top spending categories: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving top spending categories",
            status_code=500
        )


@financial_analysis_bp.route('/trends', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_financial_trends():
    """
    Get financial trends analysis
    
    Query parameters:
    - period: Analysis period
    - start_date: Start date for analysis
    - end_date: End date for analysis
    - trend_type: Type of trends to analyze (spending, cash_flow, both)
    """
    try:
        # Parse query parameters
        period_str = request.args.get('period', 'monthly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        trend_type = request.args.get('trend_type', 'both')
        
        # Parse period
        try:
            period = AnalysisPeriod(period_str)
        except ValueError:
            return create_response(
                success=False,
                message=f"Invalid period: {period_str}",
                status_code=400
            )
        
        # Parse date range
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = (start_date, end_date)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid date format",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        trends_data = {}
        
        # Get spending trends
        if trend_type in ['spending', 'both']:
            patterns = analyzer.analyze_spending_patterns(
                user_id=current_user.id,
                period=period,
                date_range=date_range
            )
            trends_data['spending_trends'] = analyzer._get_spending_trends(patterns)
        
        # Get cash flow trends
        if trend_type in ['cash_flow', 'both']:
            year = date_range[0].year if date_range else datetime.now().year
            cash_flows = analyzer.calculate_monthly_cash_flow(user_id=current_user.id, year=year)
            
            # Filter to date range
            if date_range:
                filtered_cash_flows = [
                    cf for cf in cash_flows
                    if cf.year == year and cf.month >= date_range[0].month and cf.month <= date_range[1].month
                ]
            else:
                filtered_cash_flows = cash_flows
            
            trends_data['cash_flow_trends'] = analyzer._get_cash_flow_trends(filtered_cash_flows)
        
        return create_response(
            success=True,
            message="Retrieved financial trends analysis",
            data=trends_data
        )
        
    except Exception as e:
        logger.error(f"Error getting financial trends: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving financial trends",
            status_code=500
        )


@financial_analysis_bp.route('/insights', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def get_financial_insights():
    """
    Get financial insights and recommendations
    
    Query parameters:
    - period: Analysis period
    - start_date: Start date for analysis
    - end_date: End date for analysis
    - insight_type: Type of insights (spending, cash_flow, both)
    """
    try:
        # Parse query parameters
        period_str = request.args.get('period', 'monthly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        insight_type = request.args.get('insight_type', 'both')
        
        # Parse period
        try:
            period = AnalysisPeriod(period_str)
        except ValueError:
            return create_response(
                success=False,
                message=f"Invalid period: {period_str}",
                status_code=400
            )
        
        # Parse date range
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = (start_date, end_date)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid date format",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        # Generate comprehensive analysis
        analysis = analyzer.generate_financial_analysis(
            user_id=current_user.id,
            period=period,
            date_range=date_range
        )
        
        if not analysis:
            return create_response(
                success=False,
                message="No data available for insights",
                status_code=404
            )
        
        insights_data = {}
        
        if insight_type in ['spending', 'both']:
            insights_data['insights'] = analysis.insights
        
        if insight_type in ['recommendations', 'both']:
            insights_data['recommendations'] = analysis.recommendations
        
        return create_response(
            success=True,
            message="Retrieved financial insights and recommendations",
            data=insights_data
        )
        
    except Exception as e:
        logger.error(f"Error getting financial insights: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error retrieving financial insights",
            status_code=500
        )


@financial_analysis_bp.route('/budget-variance', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def analyze_budget_variance():
    """
    Analyze budget variance tracking
    
    Query parameters:
    - period: Analysis period (daily, weekly, monthly, quarterly, yearly)
    - start_date: Start date for analysis
    - end_date: End date for analysis
    - categories: Filter by specific categories
    - account_ids: Filter by account IDs
    """
    try:
        # Parse query parameters
        period_str = request.args.get('period', 'monthly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        categories = request.args.getlist('categories')
        account_ids = request.args.getlist('account_ids')
        
        # Parse period
        try:
            period = AnalysisPeriod(period_str)
        except ValueError:
            return create_response(
                success=False,
                message=f"Invalid period: {period_str}. Valid options: daily, weekly, monthly, quarterly, yearly",
                status_code=400
            )
        
        # Parse date range
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = (start_date, end_date)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid date format. Use ISO format (YYYY-MM-DD)",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        # Generate comprehensive analysis to get budget variance data
        analysis = analyzer.generate_financial_analysis(
            user_id=current_user.id,
            period=period,
            date_range=date_range
        )
        
        if not analysis:
            return create_response(
                success=False,
                message="Failed to generate financial analysis",
                status_code=500
            )
        
        # Format budget variance response
        variances_data = []
        for variance in analysis.budget_variances:
            variances_data.append({
                'category': variance.category,
                'period': variance.period.value,
                'start_date': variance.start_date.isoformat(),
                'end_date': variance.end_date.isoformat(),
                'budget_amount': variance.budget_amount,
                'actual_spending': variance.actual_spending,
                'variance_amount': variance.variance_amount,
                'variance_percentage': variance.variance_percentage,
                'variance_type': variance.variance_type.value,
                'transaction_count': variance.transaction_count,
                'average_transaction': variance.average_transaction,
                'largest_transaction': variance.largest_transaction,
                'previous_period_variance': variance.previous_period_variance,
                'variance_trend': variance.variance_trend.value,
                'consistency_score': variance.consistency_score,
                'alerts': variance.alerts,
                'recommendations': variance.recommendations,
                'metadata': variance.metadata
            })
        
        return create_response(
            success=True,
            message=f"Budget variance analysis completed for {len(variances_data)} categories",
            data={
                'budget_variances': variances_data,
                'overall_budget_adherence': analysis.overall_budget_adherence,
                'analysis_period': period.value,
                'total_categories_analyzed': len(variances_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error analyzing budget variance: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during budget variance analysis",
            status_code=500
        )


@financial_analysis_bp.route('/savings-rate', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def analyze_savings_rate():
    """
    Analyze savings rate computation
    
    Query parameters:
    - period: Analysis period (daily, weekly, monthly, quarterly, yearly)
    - start_date: Start date for analysis
    - end_date: End date for analysis
    - account_ids: Filter by account IDs
    """
    try:
        # Parse query parameters
        period_str = request.args.get('period', 'yearly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        account_ids = request.args.getlist('account_ids')
        
        # Parse period
        try:
            period = AnalysisPeriod(period_str)
        except ValueError:
            return create_response(
                success=False,
                message=f"Invalid period: {period_str}. Valid options: daily, weekly, monthly, quarterly, yearly",
                status_code=400
            )
        
        # Parse date range
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = (start_date, end_date)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid date format. Use ISO format (YYYY-MM-DD)",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        # Generate comprehensive analysis to get savings rate data
        analysis = analyzer.generate_financial_analysis(
            user_id=current_user.id,
            period=period,
            date_range=date_range
        )
        
        if not analysis:
            return create_response(
                success=False,
                message="Failed to generate financial analysis",
                status_code=500
            )
        
        # Format savings rate response
        savings_data = {
            'period': analysis.savings_analysis.period.value,
            'start_date': analysis.savings_analysis.start_date.isoformat(),
            'end_date': analysis.savings_analysis.end_date.isoformat(),
            'total_income': analysis.savings_analysis.total_income,
            'gross_income': analysis.savings_analysis.gross_income,
            'net_income': analysis.savings_analysis.net_income,
            'income_sources': analysis.savings_analysis.income_sources,
            'total_expenses': analysis.savings_analysis.total_expenses,
            'essential_expenses': analysis.savings_analysis.essential_expenses,
            'discretionary_expenses': analysis.savings_analysis.discretionary_expenses,
            'expense_breakdown': analysis.savings_analysis.expense_breakdown,
            'total_savings': analysis.savings_analysis.total_savings,
            'savings_rate': analysis.savings_analysis.savings_rate,
            'savings_rate_gross': analysis.savings_analysis.savings_rate_gross,
            'savings_rate_net': analysis.savings_analysis.savings_rate_net,
            'emergency_fund': analysis.savings_analysis.emergency_fund,
            'retirement_savings': analysis.savings_analysis.retirement_savings,
            'investment_savings': analysis.savings_analysis.investment_savings,
            'other_savings': analysis.savings_analysis.other_savings,
            'recommended_savings_rate': analysis.savings_analysis.recommended_savings_rate,
            'benchmark_percentile': analysis.savings_analysis.benchmark_percentile,
            'savings_goal_progress': analysis.savings_analysis.savings_goal_progress,
            'savings_trend': analysis.savings_analysis.savings_trend.value,
            'savings_consistency': analysis.savings_analysis.savings_consistency,
            'month_over_month_change': analysis.savings_analysis.month_over_month_change,
            'insights': analysis.savings_analysis.insights,
            'recommendations': analysis.savings_analysis.recommendations,
            'metadata': analysis.savings_analysis.metadata
        }
        
        return create_response(
            success=True,
            message="Savings rate analysis completed successfully",
            data=savings_data
        )
        
    except Exception as e:
        logger.error(f"Error analyzing savings rate: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during savings rate analysis",
            status_code=500
        )


@financial_analysis_bp.route('/financial-health', methods=['GET'])
@login_required
@require_auth
@handle_api_errors
def analyze_financial_health():
    """
    Analyze financial health scoring
    
    Query parameters:
    - period: Analysis period (daily, weekly, monthly, quarterly, yearly)
    - start_date: Start date for analysis
    - end_date: End date for analysis
    - account_ids: Filter by account IDs
    """
    try:
        # Parse query parameters
        period_str = request.args.get('period', 'yearly')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        account_ids = request.args.getlist('account_ids')
        
        # Parse period
        try:
            period = AnalysisPeriod(period_str)
        except ValueError:
            return create_response(
                success=False,
                message=f"Invalid period: {period_str}. Valid options: daily, weekly, monthly, quarterly, yearly",
                status_code=400
            )
        
        # Parse date range
        date_range = None
        if start_date_str and end_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                date_range = (start_date, end_date)
            except ValueError:
                return create_response(
                    success=False,
                    message="Invalid date format. Use ISO format (YYYY-MM-DD)",
                    status_code=400
                )
        
        # Initialize analyzer
        db_session = current_app.db.session
        analyzer = FinancialAnalyzer(db_session)
        
        # Generate comprehensive analysis to get financial health data
        analysis = analyzer.generate_financial_analysis(
            user_id=current_user.id,
            period=period,
            date_range=date_range
        )
        
        if not analysis:
            return create_response(
                success=False,
                message="Failed to generate financial analysis",
                status_code=500
            )
        
        # Format financial health response
        health_data = {
            'user_id': analysis.financial_health_score.user_id,
            'assessment_date': analysis.financial_health_score.assessment_date.isoformat(),
            'period': analysis.financial_health_score.period.value,
            'overall_score': analysis.financial_health_score.overall_score,
            'health_level': analysis.financial_health_score.health_level.value,
            'component_scores': {
                'income_stability_score': analysis.financial_health_score.income_stability_score,
                'expense_management_score': analysis.financial_health_score.expense_management_score,
                'savings_score': analysis.financial_health_score.savings_score,
                'debt_management_score': analysis.financial_health_score.debt_management_score,
                'emergency_fund_score': analysis.financial_health_score.emergency_fund_score,
                'investment_score': analysis.financial_health_score.investment_score,
                'budget_adherence_score': analysis.financial_health_score.budget_adherence_score,
                'cash_flow_score': analysis.financial_health_score.cash_flow_score
            },
            'detailed_metrics': {
                'income_stability_metrics': analysis.financial_health_score.income_stability_metrics,
                'expense_management_metrics': analysis.financial_health_score.expense_management_metrics,
                'savings_metrics': analysis.financial_health_score.savings_metrics,
                'debt_metrics': analysis.financial_health_score.debt_metrics,
                'emergency_fund_metrics': analysis.financial_health_score.emergency_fund_metrics,
                'investment_metrics': analysis.financial_health_score.investment_metrics,
                'budget_metrics': analysis.financial_health_score.budget_metrics,
                'cash_flow_metrics': analysis.financial_health_score.cash_flow_metrics
            },
            'risk_factors': analysis.financial_health_score.risk_factors,
            'risk_level': analysis.financial_health_score.risk_level,
            'priority_actions': analysis.financial_health_score.priority_actions,
            'improvement_areas': analysis.financial_health_score.improvement_areas,
            'strengths': analysis.financial_health_score.strengths,
            'previous_score': analysis.financial_health_score.previous_score,
            'score_change': analysis.financial_health_score.score_change,
            'trend_direction': analysis.financial_health_score.trend_direction.value,
            'metadata': analysis.financial_health_score.metadata
        }
        
        return create_response(
            success=True,
            message="Financial health analysis completed successfully",
            data=health_data
        )
        
    except Exception as e:
        logger.error(f"Error analyzing financial health: {str(e)}")
        return create_response(
            success=False,
            message="Internal server error during financial health analysis",
            status_code=500
        )


@financial_analysis_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for financial analysis service
    """
    try:
        # Check database connection
        db_session = current_app.db.session
        db_session.execute(text('SELECT 1'))
        
        return create_response(
            success=True,
            message="Financial analysis service is healthy",
            data={
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_response(
            success=False,
            message="Financial analysis service is unhealthy",
            status_code=503,
            data={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )


def register_financial_analysis_routes(app):
    """Register financial analysis routes with the Flask app"""
    app.register_blueprint(financial_analysis_bp)
    logger.info("Financial analysis routes registered successfully") 