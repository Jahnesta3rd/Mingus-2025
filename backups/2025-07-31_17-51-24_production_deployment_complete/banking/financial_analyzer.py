"""
Financial Analysis Service

This module provides comprehensive financial analysis features including
spending pattern analysis by category, monthly cash flow calculations,
budget variance tracking, savings rate computation, and financial health scoring
for the MINGUS application.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import statistics
import calendar
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text, extract
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidTransaction
from backend.models.analytics import SpendingCategory, SpendingPattern, FinancialInsight
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class AnalysisPeriod(Enum):
    """Analysis period types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TrendDirection(Enum):
    """Trend direction indicators"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class CashFlowType(Enum):
    """Cash flow type indicators"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class BudgetVarianceType(Enum):
    """Budget variance types"""
    UNDER_BUDGET = "under_budget"
    OVER_BUDGET = "over_budget"
    ON_BUDGET = "on_budget"
    NO_BUDGET = "no_budget"


class FinancialHealthLevel(Enum):
    """Financial health levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class BudgetVarianceAnalysis:
    """Budget variance tracking analysis"""
    category: str
    period: AnalysisPeriod
    start_date: datetime
    end_date: datetime
    
    # Budget information
    budget_amount: float
    actual_spending: float
    variance_amount: float
    variance_percentage: float
    variance_type: BudgetVarianceType
    
    # Spending details
    transaction_count: int
    average_transaction: float
    largest_transaction: float
    
    # Trend analysis
    previous_period_variance: float
    variance_trend: TrendDirection
    consistency_score: float  # How consistent is the variance
    
    # Alerts and recommendations
    alerts: List[str]
    recommendations: List[str]
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SavingsRateAnalysis:
    """Savings rate computation analysis"""
    period: AnalysisPeriod
    start_date: datetime
    end_date: datetime
    
    # Income analysis
    total_income: float
    gross_income: float
    net_income: float
    income_sources: Dict[str, float]
    
    # Expense analysis
    total_expenses: float
    essential_expenses: float
    discretionary_expenses: float
    expense_breakdown: Dict[str, float]
    
    # Savings calculation
    total_savings: float
    savings_rate: float  # percentage of income saved
    savings_rate_gross: float  # percentage of gross income saved
    savings_rate_net: float  # percentage of net income saved
    
    # Savings categories
    emergency_fund: float
    retirement_savings: float
    investment_savings: float
    other_savings: float
    
    # Benchmarking
    recommended_savings_rate: float
    benchmark_percentile: float  # where user ranks compared to others
    savings_goal_progress: float
    
    # Trend analysis
    savings_trend: TrendDirection
    savings_consistency: float
    month_over_month_change: float
    
    # Insights
    insights: List[str]
    recommendations: List[str]
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialHealthScore:
    """Financial health scoring analysis"""
    user_id: int
    assessment_date: datetime
    period: AnalysisPeriod
    
    # Overall health score (0-100)
    overall_score: float
    health_level: FinancialHealthLevel
    
    # Component scores (0-100 each)
    income_stability_score: float
    expense_management_score: float
    savings_score: float
    debt_management_score: float
    emergency_fund_score: float
    investment_score: float
    budget_adherence_score: float
    cash_flow_score: float
    
    # Detailed metrics
    income_stability_metrics: Dict[str, float]
    expense_management_metrics: Dict[str, float]
    savings_metrics: Dict[str, float]
    debt_metrics: Dict[str, float]
    emergency_fund_metrics: Dict[str, float]
    investment_metrics: Dict[str, float]
    budget_metrics: Dict[str, float]
    cash_flow_metrics: Dict[str, float]
    
    # Risk factors
    risk_factors: List[str]
    risk_level: str  # low, medium, high, critical
    
    # Recommendations
    priority_actions: List[str]
    improvement_areas: List[str]
    strengths: List[str]
    
    # Historical comparison
    previous_score: Optional[float]
    score_change: Optional[float]
    trend_direction: TrendDirection
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpendingPatternAnalysis:
    """Analysis of spending patterns by category"""
    category: str
    period: AnalysisPeriod
    start_date: datetime
    end_date: datetime
    
    # Spending statistics
    total_amount: float
    transaction_count: int
    average_amount: float
    median_amount: float
    min_amount: float
    max_amount: float
    
    # Trend analysis
    trend_direction: TrendDirection
    percentage_change: float
    trend_strength: float  # 0-1 scale
    
    # Pattern characteristics
    is_recurring: bool
    frequency_score: float
    consistency_score: float
    
    # Comparative analysis
    category_rank: int
    percentage_of_total: float
    average_daily_spending: float
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonthlyCashFlow:
    """Monthly cash flow analysis"""
    year: int
    month: int
    month_name: str
    
    # Income analysis
    total_income: float
    income_transactions: int
    average_income: float
    income_sources: Dict[str, float]
    
    # Expense analysis
    total_expenses: float
    expense_transactions: int
    average_expense: float
    expense_categories: Dict[str, float]
    
    # Cash flow analysis
    net_cash_flow: float
    cash_flow_type: CashFlowType
    cash_flow_ratio: float  # income/expenses ratio
    
    # Trend analysis
    month_over_month_change: float
    year_over_year_change: float
    
    # Budget analysis
    budget_variance: float
    budget_percentage: float
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialAnalysisSummary:
    """Comprehensive financial analysis summary"""
    user_id: int
    analysis_period: AnalysisPeriod
    start_date: datetime
    end_date: datetime
    
    # Overall financial metrics
    total_income: float
    total_expenses: float
    net_cash_flow: float
    savings_rate: float
    
    # Spending analysis
    spending_patterns: List[SpendingPatternAnalysis]
    top_spending_categories: List[Dict[str, Any]]
    spending_trends: Dict[str, TrendDirection]
    
    # Cash flow analysis
    monthly_cash_flows: List[MonthlyCashFlow]
    cash_flow_trends: Dict[str, Any]
    
    # Budget variance analysis
    budget_variances: List[BudgetVarianceAnalysis]
    overall_budget_adherence: float
    
    # Savings rate analysis
    savings_analysis: SavingsRateAnalysis
    
    # Financial health scoring
    financial_health_score: FinancialHealthScore
    
    # Insights and recommendations
    insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class FinancialAnalyzer:
    """
    Comprehensive financial analysis service that provides spending pattern analysis,
    cash flow calculations, budget variance tracking, savings rate computation,
    and financial health scoring.
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        # Initialize analysis parameters
        self._initialize_analysis_parameters()
        
        # Initialize trend detection
        self._initialize_trend_detection()
        
        # Initialize insight generation
        self._initialize_insight_generation()
        
        # Initialize budget tracking
        self._initialize_budget_tracking()
        
        # Initialize savings analysis
        self._initialize_savings_analysis()
        
        # Initialize health scoring
        self._initialize_health_scoring()
    
    def _initialize_analysis_parameters(self):
        """Initialize analysis parameters and thresholds"""
        self.analysis_params = {
            # Trend detection thresholds
            'trend_thresholds': {
                'significant_change': 0.1,  # 10% change is significant
                'strong_trend': 0.25,  # 25% change indicates strong trend
                'volatility_threshold': 0.5,  # 50% variance indicates volatility
            },
            
            # Pattern detection parameters
            'pattern_params': {
                'min_transactions': 3,  # Minimum transactions for pattern analysis
                'recurring_threshold': 0.7,  # 70% consistency for recurring pattern
                'frequency_threshold': 0.6,  # 60% frequency for pattern detection
            },
            
            # Cash flow analysis parameters
            'cash_flow_params': {
                'positive_ratio': 1.2,  # Income 20% higher than expenses
                'negative_ratio': 0.8,  # Expenses 20% higher than income
                'savings_rate_target': 0.2,  # 20% savings rate target
            },
            
            # Analysis periods
            'default_periods': {
                'short_term': 30,  # 30 days
                'medium_term': 90,  # 90 days
                'long_term': 365,  # 1 year
            }
        }
    
    def _initialize_trend_detection(self):
        """Initialize trend detection algorithms"""
        self.trend_detection = {
            # Trend calculation methods
            'methods': {
                'linear_regression': self._calculate_linear_trend,
                'moving_average': self._calculate_moving_average_trend,
                'percentage_change': self._calculate_percentage_change,
            },
            
            # Trend strength indicators
            'strength_indicators': {
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2,
            }
        }
    
    def _initialize_insight_generation(self):
        """Initialize insight generation rules"""
        self.insight_rules = {
            # Spending insights
            'spending_insights': {
                'high_spending': {
                    'threshold': 0.3,  # 30% of total spending
                    'message': "High spending in {category} category"
                },
                'increasing_trend': {
                    'threshold': 0.2,  # 20% increase
                    'message': "Spending in {category} is increasing"
                },
                'unusual_spending': {
                    'threshold': 2.0,  # 2x average
                    'message': "Unusual spending detected in {category}"
                }
            },
            
            # Cash flow insights
            'cash_flow_insights': {
                'negative_cash_flow': {
                    'message': "Negative cash flow detected for {month}"
                },
                'low_savings_rate': {
                    'threshold': 0.1,  # 10% savings rate
                    'message': "Low savings rate detected"
                },
                'improving_trend': {
                    'message': "Cash flow is improving over time"
                }
            }
        }
    
    def _initialize_budget_tracking(self):
        """Initialize budget tracking parameters and rules"""
        self.budget_tracking_params = {
            'min_budget_threshold': 0.1,  # 10% variance is significant
            'budget_consistency_threshold': 0.7,  # 70% consistency for budget adherence
            'budget_alert_thresholds': {
                'under_budget': 0.05,  # 5% under budget
                'over_budget': 0.05,  # 5% over budget
            },
            'budget_recommendations': {
                'under_budget': "Consider increasing budget for {category}",
                'over_budget': "Consider reducing budget for {category}",
                'on_budget': "Budget adherence is good for {category}"
            }
        }
    
    def _initialize_savings_analysis(self):
        """Initialize savings rate analysis parameters and rules"""
        self.savings_analysis_params = {
            'income_sources': ['salary', 'investments', 'rental income', 'other'],
            'essential_expense_categories': ['housing', 'transportation', 'food', 'utilities', 'insurance'],
            'discretionary_expense_categories': ['entertainment', 'dining out', 'shopping', 'travel', 'subscriptions'],
            'savings_categories': ['emergency fund', 'retirement savings', 'investment savings', 'other'],
            'recommended_savings_rate': 0.2,  # 20% savings rate target
            'benchmark_percentile': 0.75,  # 75th percentile for benchmark
            'savings_goal_progress_threshold': 0.8,  # 80% of savings goal achieved
            'savings_trend_thresholds': {
                'increasing': 0.1,  # 10% increase in savings rate
                'decreasing': -0.05,  # 5% decrease in savings rate
            }
        }
    
    def _initialize_health_scoring(self):
        """Initialize financial health scoring parameters and rules"""
        self.health_scoring_params = {
            'component_weights': {
                'income_stability': 0.25,
                'expense_management': 0.25,
                'savings': 0.20,
                'debt_management': 0.10,
                'emergency_fund': 0.05,
                'investment': 0.05,
                'budget_adherence': 0.10,
                'cash_flow': 0.05,
            },
            'risk_factors': {
                'income_instability': "Income fluctuations or irregularity",
                'high_essential_expenses': "Significant proportion of income dedicated to essential expenses",
                'excessive_discretionary_spending': "High spending on discretionary items",
                'high_debt_load': "Significant outstanding debt",
                'lack_of_emergency_fund': "No emergency fund or insufficient",
                'poor_investment_returns': "Low returns on investments",
                'inconsistent_budgeting': "Inconsistent or unrealistic budgeting",
                'negative_cash_flow': "Persistent negative cash flow",
            },
            'health_levels': {
                'excellent': (0.85, 0.95),
                'good': (0.75, 0.85),
                'fair': (0.65, 0.75),
                'poor': (0.50, 0.65),
                'critical': (0.0, 0.50),
            },
            'score_change_thresholds': {
                'significant_improvement': 0.10,
                'significant_decline': -0.05,
            }
        }
    
    def analyze_spending_patterns(self, user_id: int, 
                                period: AnalysisPeriod = AnalysisPeriod.MONTHLY,
                                date_range: Tuple[datetime, datetime] = None,
                                categories: List[str] = None) -> List[SpendingPatternAnalysis]:
        """
        Analyze spending patterns by category
        
        Args:
            user_id: User ID to analyze
            period: Analysis period (daily, weekly, monthly, etc.)
            date_range: Date range for analysis
            categories: Specific categories to analyze (None for all)
            
        Returns:
            List of spending pattern analyses
        """
        try:
            # Set default date range if not provided
            if date_range is None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=self.analysis_params['default_periods']['medium_term'])
                date_range = (start_date, end_date)
            
            # Get transactions for analysis
            transactions = self._get_transactions_for_analysis(user_id, date_range, categories)
            
            if not transactions:
                return []
            
            # Group transactions by category
            category_groups = self._group_transactions_by_category(transactions)
            
            # Analyze each category
            analyses = []
            for category, category_transactions in category_groups.items():
                if len(category_transactions) < self.analysis_params['pattern_params']['min_transactions']:
                    continue
                
                analysis = self._analyze_category_spending(
                    category, category_transactions, period, date_range
                )
                analyses.append(analysis)
            
            # Sort by total amount (descending)
            analyses.sort(key=lambda x: x.total_amount, reverse=True)
            
            # Add ranking information
            for i, analysis in enumerate(analyses):
                analysis.category_rank = i + 1
                total_spending = sum(a.total_amount for a in analyses)
                analysis.percentage_of_total = (analysis.total_amount / total_spending * 100) if total_spending > 0 else 0
            
            return analyses
            
        except Exception as e:
            self.logger.error(f"Error analyzing spending patterns: {str(e)}")
            return []
    
    def calculate_monthly_cash_flow(self, user_id: int,
                                  year: int = None,
                                  months: List[int] = None) -> List[MonthlyCashFlow]:
        """
        Calculate monthly cash flow for a user
        
        Args:
            user_id: User ID to analyze
            year: Specific year to analyze (None for current year)
            months: Specific months to analyze (None for all months)
            
        Returns:
            List of monthly cash flow analyses
        """
        try:
            # Set default year if not provided
            if year is None:
                year = datetime.now().year
            
            # Set default months if not provided
            if months is None:
                months = list(range(1, 13))
            
            cash_flows = []
            
            for month in months:
                # Calculate date range for the month
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                
                # Get transactions for the month
                transactions = self._get_transactions_for_analysis(user_id, (start_date, end_date))
                
                # Calculate cash flow for the month
                cash_flow = self._calculate_monthly_cash_flow_data(
                    year, month, transactions
                )
                
                cash_flows.append(cash_flow)
            
            # Calculate trend information
            cash_flows = self._add_cash_flow_trends(cash_flows)
            
            return cash_flows
            
        except Exception as e:
            self.logger.error(f"Error calculating monthly cash flow: {str(e)}")
            return []
    
    def generate_financial_analysis(self, user_id: int,
                                  period: AnalysisPeriod = AnalysisPeriod.MONTHLY,
                                  date_range: Tuple[datetime, datetime] = None) -> FinancialAnalysisSummary:
        """
        Generate comprehensive financial analysis
        
        Args:
            user_id: User ID to analyze
            period: Analysis period
            date_range: Date range for analysis
            
        Returns:
            Comprehensive financial analysis summary
        """
        try:
            # Set default date range if not provided
            if date_range is None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=self.analysis_params['default_periods']['medium_term'])
                date_range = (start_date, end_date)
            
            # Analyze spending patterns
            spending_patterns = self.analyze_spending_patterns(user_id, period, date_range)
            
            # Calculate monthly cash flow
            year = date_range[0].year
            monthly_cash_flows = self.calculate_monthly_cash_flow(user_id, year)
            
            # Filter cash flows to date range
            filtered_cash_flows = [
                cf for cf in monthly_cash_flows
                if cf.year == year and cf.month >= date_range[0].month and cf.month <= date_range[1].month
            ]
            
            # Calculate overall metrics
            total_income = sum(cf.total_income for cf in filtered_cash_flows)
            total_expenses = sum(cf.total_expenses for cf in filtered_cash_flows)
            net_cash_flow = total_income - total_expenses
            savings_rate = (net_cash_flow / total_income * 100) if total_income > 0 else 0
            
            # Generate insights and recommendations
            insights = self._generate_insights(spending_patterns, filtered_cash_flows)
            recommendations = self._generate_recommendations(spending_patterns, filtered_cash_flows)
            
            # Create summary
            summary = FinancialAnalysisSummary(
                user_id=user_id,
                analysis_period=period,
                start_date=date_range[0],
                end_date=date_range[1],
                total_income=total_income,
                total_expenses=total_expenses,
                net_cash_flow=net_cash_flow,
                savings_rate=savings_rate,
                spending_patterns=spending_patterns,
                top_spending_categories=self._get_top_spending_categories(spending_patterns),
                spending_trends=self._get_spending_trends(spending_patterns),
                monthly_cash_flows=filtered_cash_flows,
                cash_flow_trends=self._get_cash_flow_trends(filtered_cash_flows),
                budget_variances=self._analyze_budget_variance(user_id, spending_patterns, filtered_cash_flows, year),
                overall_budget_adherence=self._calculate_overall_budget_adherence(filtered_cash_flows),
                savings_analysis=self._analyze_savings_rate(filtered_cash_flows, year),
                financial_health_score=self._generate_financial_health_score(user_id, year),
                insights=insights,
                recommendations=recommendations
            )
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating financial analysis: {str(e)}")
            return None
    
    def _get_transactions_for_analysis(self, user_id: int,
                                     date_range: Tuple[datetime, datetime],
                                     categories: List[str] = None) -> List[PlaidTransaction]:
        """Get transactions for analysis"""
        query = self.db_session.query(PlaidTransaction).filter(
            and_(
                PlaidTransaction.user_id == user_id,
                PlaidTransaction.date.between(date_range[0], date_range[1])
            )
        )
        
        if categories:
            query = query.filter(PlaidTransaction.category.in_(categories))
        
        return query.order_by(PlaidTransaction.date.asc()).all()
    
    def _group_transactions_by_category(self, transactions: List[PlaidTransaction]) -> Dict[str, List[PlaidTransaction]]:
        """Group transactions by category"""
        groups = defaultdict(list)
        
        for transaction in transactions:
            category = transaction.category or "other"
            groups[category].append(transaction)
        
        return dict(groups)
    
    def _analyze_category_spending(self, category: str,
                                 transactions: List[PlaidTransaction],
                                 period: AnalysisPeriod,
                                 date_range: Tuple[datetime, datetime]) -> SpendingPatternAnalysis:
        """Analyze spending for a specific category"""
        
        # Calculate basic statistics
        amounts = [abs(float(tx.amount)) for tx in transactions]
        total_amount = sum(amounts)
        transaction_count = len(transactions)
        average_amount = statistics.mean(amounts) if amounts else 0
        median_amount = statistics.median(amounts) if amounts else 0
        min_amount = min(amounts) if amounts else 0
        max_amount = max(amounts) if amounts else 0
        
        # Calculate trend analysis
        trend_analysis = self._calculate_spending_trend(transactions, period)
        
        # Calculate pattern characteristics
        pattern_analysis = self._analyze_spending_pattern(transactions, period)
        
        # Calculate average daily spending
        days_in_period = (date_range[1] - date_range[0]).days
        average_daily_spending = total_amount / days_in_period if days_in_period > 0 else 0
        
        return SpendingPatternAnalysis(
            category=category,
            period=period,
            start_date=date_range[0],
            end_date=date_range[1],
            total_amount=total_amount,
            transaction_count=transaction_count,
            average_amount=average_amount,
            median_amount=median_amount,
            min_amount=min_amount,
            max_amount=max_amount,
            trend_direction=trend_analysis['direction'],
            percentage_change=trend_analysis['percentage_change'],
            trend_strength=trend_analysis['strength'],
            is_recurring=pattern_analysis['is_recurring'],
            frequency_score=pattern_analysis['frequency_score'],
            consistency_score=pattern_analysis['consistency_score'],
            category_rank=0,  # Will be set later
            percentage_of_total=0,  # Will be set later
            average_daily_spending=average_daily_spending,
            metadata={
                'trend_analysis': trend_analysis,
                'pattern_analysis': pattern_analysis
            }
        )
    
    def _calculate_spending_trend(self, transactions: List[PlaidTransaction],
                                period: AnalysisPeriod) -> Dict[str, Any]:
        """Calculate spending trend for a category"""
        
        if len(transactions) < 2:
            return {
                'direction': TrendDirection.STABLE,
                'percentage_change': 0.0,
                'strength': 0.0
            }
        
        # Group transactions by period
        period_groups = self._group_transactions_by_period(transactions, period)
        
        if len(period_groups) < 2:
            return {
                'direction': TrendDirection.STABLE,
                'percentage_change': 0.0,
                'strength': 0.0
            }
        
        # Calculate spending by period
        period_spending = []
        for period_key, period_transactions in sorted(period_groups.items()):
            total = sum(abs(float(tx.amount)) for tx in period_transactions)
            period_spending.append(total)
        
        # Calculate trend
        if len(period_spending) >= 2:
            first_half = period_spending[:len(period_spending)//2]
            second_half = period_spending[len(period_spending)//2:]
            
            first_avg = statistics.mean(first_half) if first_half else 0
            second_avg = statistics.mean(second_half) if second_half else 0
            
            if first_avg == 0:
                percentage_change = 0.0
            else:
                percentage_change = ((second_avg - first_avg) / first_avg) * 100
            
            # Determine trend direction
            if abs(percentage_change) < self.analysis_params['trend_thresholds']['significant_change'] * 100:
                direction = TrendDirection.STABLE
            elif percentage_change > self.analysis_params['trend_thresholds']['strong_trend'] * 100:
                direction = TrendDirection.INCREASING
            elif percentage_change < -self.analysis_params['trend_thresholds']['strong_trend'] * 100:
                direction = TrendDirection.DECREASING
            else:
                direction = TrendDirection.VOLATILE
            
            # Calculate trend strength
            strength = min(abs(percentage_change) / 100, 1.0)
            
        else:
            direction = TrendDirection.STABLE
            percentage_change = 0.0
            strength = 0.0
        
        return {
            'direction': direction,
            'percentage_change': percentage_change,
            'strength': strength
        }
    
    def _group_transactions_by_period(self, transactions: List[PlaidTransaction],
                                    period: AnalysisPeriod) -> Dict[str, List[PlaidTransaction]]:
        """Group transactions by analysis period"""
        groups = defaultdict(list)
        
        for transaction in transactions:
            if period == AnalysisPeriod.DAILY:
                key = transaction.date.strftime('%Y-%m-%d')
            elif period == AnalysisPeriod.WEEKLY:
                key = f"{transaction.date.year}-W{transaction.date.isocalendar()[1]}"
            elif period == AnalysisPeriod.MONTHLY:
                key = f"{transaction.date.year}-{transaction.date.month:02d}"
            elif period == AnalysisPeriod.QUARTERLY:
                quarter = (transaction.date.month - 1) // 3 + 1
                key = f"{transaction.date.year}-Q{quarter}"
            else:  # YEARLY
                key = str(transaction.date.year)
            
            groups[key].append(transaction)
        
        return dict(groups)
    
    def _analyze_spending_pattern(self, transactions: List[PlaidTransaction],
                                period: AnalysisPeriod) -> Dict[str, Any]:
        """Analyze spending pattern characteristics"""
        
        if len(transactions) < self.analysis_params['pattern_params']['min_transactions']:
            return {
                'is_recurring': False,
                'frequency_score': 0.0,
                'consistency_score': 0.0
            }
        
        # Calculate frequency score
        total_days = (transactions[-1].date - transactions[0].date).days
        if total_days == 0:
            frequency_score = 1.0
        else:
            frequency_score = len(transactions) / (total_days / 30)  # Transactions per month
        
        # Calculate consistency score
        amounts = [abs(float(tx.amount)) for tx in transactions]
        if len(amounts) > 1:
            mean_amount = statistics.mean(amounts)
            variance = statistics.variance(amounts)
            coefficient_of_variation = math.sqrt(variance) / mean_amount if mean_amount > 0 else 0
            consistency_score = max(0, 1 - coefficient_of_variation)
        else:
            consistency_score = 1.0
        
        # Determine if recurring
        is_recurring = (
            frequency_score >= self.analysis_params['pattern_params']['frequency_threshold'] and
            consistency_score >= self.analysis_params['pattern_params']['recurring_threshold']
        )
        
        return {
            'is_recurring': is_recurring,
            'frequency_score': min(frequency_score, 1.0),
            'consistency_score': consistency_score
        }
    
    def _calculate_monthly_cash_flow_data(self, year: int, month: int,
                                        transactions: List[PlaidTransaction]) -> MonthlyCashFlow:
        """Calculate cash flow data for a specific month"""
        
        # Separate income and expenses
        income_transactions = [tx for tx in transactions if float(tx.amount) > 0]
        expense_transactions = [tx for tx in transactions if float(tx.amount) < 0]
        
        # Calculate income metrics
        total_income = sum(float(tx.amount) for tx in income_transactions)
        income_sources = defaultdict(float)
        for tx in income_transactions:
            source = tx.source or "other"
            income_sources[source] += float(tx.amount)
        
        # Calculate expense metrics
        total_expenses = abs(sum(float(tx.amount) for tx in expense_transactions))
        expense_categories = defaultdict(float)
        for tx in expense_transactions:
            category = tx.category or "other"
            expense_categories[category] += abs(float(tx.amount))
        
        # Calculate cash flow metrics
        net_cash_flow = total_income - total_expenses
        cash_flow_ratio = total_income / total_expenses if total_expenses > 0 else float('inf')
        
        # Determine cash flow type
        if cash_flow_ratio > self.analysis_params['cash_flow_params']['positive_ratio']:
            cash_flow_type = CashFlowType.POSITIVE
        elif cash_flow_ratio < self.analysis_params['cash_flow_params']['negative_ratio']:
            cash_flow_type = CashFlowType.NEGATIVE
        else:
            cash_flow_type = CashFlowType.NEUTRAL
        
        return MonthlyCashFlow(
            year=year,
            month=month,
            month_name=calendar.month_name[month],
            total_income=total_income,
            income_transactions=len(income_transactions),
            average_income=total_income / len(income_transactions) if income_transactions else 0,
            income_sources=dict(income_sources),
            total_expenses=total_expenses,
            expense_transactions=len(expense_transactions),
            average_expense=total_expenses / len(expense_transactions) if expense_transactions else 0,
            expense_categories=dict(expense_categories),
            net_cash_flow=net_cash_flow,
            cash_flow_type=cash_flow_type,
            cash_flow_ratio=cash_flow_ratio,
            month_over_month_change=0.0,  # Will be calculated later
            year_over_year_change=0.0,  # Will be calculated later
            budget_variance=0.0,  # Will be calculated if budget data available
            budget_percentage=0.0  # Will be calculated if budget data available
        )
    
    def _add_cash_flow_trends(self, cash_flows: List[MonthlyCashFlow]) -> List[MonthlyCashFlow]:
        """Add trend information to cash flows"""
        
        for i, cash_flow in enumerate(cash_flows):
            # Calculate month-over-month change
            if i > 0:
                prev_cash_flow = cash_flows[i-1]
                if prev_cash_flow.net_cash_flow != 0:
                    cash_flow.month_over_month_change = (
                        (cash_flow.net_cash_flow - prev_cash_flow.net_cash_flow) / 
                        abs(prev_cash_flow.net_cash_flow) * 100
                    )
            
            # Calculate year-over-year change (if we have data from previous year)
            # This would require additional data from previous years
            
        return cash_flows
    
    def _get_top_spending_categories(self, spending_patterns: List[SpendingPatternAnalysis],
                                   top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top spending categories"""
        sorted_patterns = sorted(spending_patterns, key=lambda x: x.total_amount, reverse=True)
        
        return [
            {
                'category': pattern.category,
                'total_amount': pattern.total_amount,
                'percentage_of_total': pattern.percentage_of_total,
                'transaction_count': pattern.transaction_count,
                'average_amount': pattern.average_amount,
                'trend_direction': pattern.trend_direction.value
            }
            for pattern in sorted_patterns[:top_n]
        ]
    
    def _get_spending_trends(self, spending_patterns: List[SpendingPatternAnalysis]) -> Dict[str, TrendDirection]:
        """Get overall spending trends"""
        trends = {}
        
        for pattern in spending_patterns:
            trends[pattern.category] = pattern.trend_direction
        
        return trends
    
    def _get_cash_flow_trends(self, cash_flows: List[MonthlyCashFlow]) -> Dict[str, Any]:
        """Get cash flow trends"""
        if not cash_flows:
            return {}
        
        # Calculate overall trends
        total_income = sum(cf.total_income for cf in cash_flows)
        total_expenses = sum(cf.total_expenses for cf in cash_flows)
        net_cash_flow = sum(cf.net_cash_flow for cf in cash_flows)
        
        # Calculate trend direction
        if len(cash_flows) >= 2:
            first_half = cash_flows[:len(cash_flows)//2]
            second_half = cash_flows[len(cash_flows)//2:]
            
            first_avg = statistics.mean([cf.net_cash_flow for cf in first_half])
            second_avg = statistics.mean([cf.net_cash_flow for cf in second_half])
            
            if second_avg > first_avg:
                trend_direction = "improving"
            elif second_avg < first_avg:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_cash_flow': net_cash_flow,
            'trend_direction': trend_direction,
            'average_monthly_income': total_income / len(cash_flows) if cash_flows else 0,
            'average_monthly_expenses': total_expenses / len(cash_flows) if cash_flows else 0,
            'average_monthly_cash_flow': net_cash_flow / len(cash_flows) if cash_flows else 0
        }
    
    def _generate_insights(self, spending_patterns: List[SpendingPatternAnalysis],
                         cash_flows: List[MonthlyCashFlow]) -> List[Dict[str, Any]]:
        """Generate insights from analysis"""
        insights = []
        
        # Spending insights
        for pattern in spending_patterns:
            # High spending insight
            if pattern.percentage_of_total > self.insight_rules['spending_insights']['high_spending']['threshold'] * 100:
                insights.append({
                    'type': 'high_spending',
                    'category': pattern.category,
                    'message': self.insight_rules['spending_insights']['high_spending']['message'].format(
                        category=pattern.category
                    ),
                    'severity': 'medium',
                    'data': {
                        'percentage': pattern.percentage_of_total,
                        'total_amount': pattern.total_amount
                    }
                })
            
            # Increasing trend insight
            if (pattern.trend_direction == TrendDirection.INCREASING and 
                pattern.percentage_change > self.insight_rules['spending_insights']['increasing_trend']['threshold'] * 100):
                insights.append({
                    'type': 'increasing_trend',
                    'category': pattern.category,
                    'message': self.insight_rules['spending_insights']['increasing_trend']['message'].format(
                        category=pattern.category
                    ),
                    'severity': 'low',
                    'data': {
                        'percentage_change': pattern.percentage_change,
                        'trend_strength': pattern.trend_strength
                    }
                })
        
        # Cash flow insights
        for cash_flow in cash_flows:
            if cash_flow.cash_flow_type == CashFlowType.NEGATIVE:
                insights.append({
                    'type': 'negative_cash_flow',
                    'month': cash_flow.month_name,
                    'message': self.insight_rules['cash_flow_insights']['negative_cash_flow']['message'].format(
                        month=cash_flow.month_name
                    ),
                    'severity': 'high',
                    'data': {
                        'net_cash_flow': cash_flow.net_cash_flow,
                        'cash_flow_ratio': cash_flow.cash_flow_ratio
                    }
                })
        
        return insights
    
    def _generate_recommendations(self, spending_patterns: List[SpendingPatternAnalysis],
                                cash_flows: List[MonthlyCashFlow]) -> List[Dict[str, Any]]:
        """Generate recommendations from analysis"""
        recommendations = []
        
        # Spending recommendations
        for pattern in spending_patterns:
            if pattern.percentage_of_total > 0.3:  # More than 30% of total spending
                recommendations.append({
                    'type': 'reduce_spending',
                    'category': pattern.category,
                    'message': f"Consider reducing spending in {pattern.category} category",
                    'priority': 'medium',
                    'action': f"Review {pattern.category} expenses and identify areas for reduction"
                })
            
            if pattern.trend_direction == TrendDirection.INCREASING:
                recommendations.append({
                    'type': 'monitor_trend',
                    'category': pattern.category,
                    'message': f"Monitor increasing trend in {pattern.category} spending",
                    'priority': 'low',
                    'action': f"Track {pattern.category} spending to understand the increase"
                })
        
        # Cash flow recommendations
        negative_months = [cf for cf in cash_flows if cf.cash_flow_type == CashFlowType.NEGATIVE]
        if len(negative_months) > len(cash_flows) * 0.5:  # More than 50% of months are negative
            recommendations.append({
                'type': 'improve_cash_flow',
                'message': "Focus on improving overall cash flow",
                'priority': 'high',
                'action': "Increase income or reduce expenses to achieve positive cash flow"
            })
        
        return recommendations
    
    def _analyze_budget_variance(self, user_id: int, spending_patterns: List[SpendingPatternAnalysis],
                                cash_flows: List[MonthlyCashFlow],
                                year: int) -> List[BudgetVarianceAnalysis]:
        """Analyze budget variance for each category and month"""
        variances = []
        
        for month_flow in cash_flows:
            month_name = month_flow.month_name
            month_start_date = datetime(year, month_flow.month, 1)
            month_end_date = datetime(year, month_flow.month + 1, 1) - timedelta(days=1)
            
            # Get transactions for the month
            transactions_in_month = self._get_transactions_for_analysis(
                user_id=user_id,
                date_range=(month_start_date, month_end_date)
            )
            
            # Analyze budget variance for each category
            for category, category_transactions in self._group_transactions_by_category(transactions_in_month).items():
                if category in spending_patterns: # Only analyze categories that have spending patterns
                    pattern = next(p for p in spending_patterns if p.category == category)
                    
                    # Calculate actual spending for the month
                    actual_spending = sum(abs(float(tx.amount)) for tx in category_transactions)
                    
                    # Determine variance type
                    if pattern.total_amount > 0:
                        variance_amount = actual_spending - pattern.total_amount
                        variance_percentage = (variance_amount / pattern.total_amount) * 100
                        
                        if variance_amount > 0:
                            variance_type = BudgetVarianceType.OVER_BUDGET
                        elif variance_amount < 0:
                            variance_type = BudgetVarianceType.UNDER_BUDGET
                        else:
                            variance_type = BudgetVarianceType.ON_BUDGET
                    else:
                        variance_amount = actual_spending
                        variance_percentage = 0.0
                        variance_type = BudgetVarianceType.NO_BUDGET
                    
                    # Calculate trend for variance
                    if len(category_transactions) >= 2:
                        first_half_variance = sum(abs(float(tx.amount)) for tx in category_transactions[:len(category_transactions)//2])
                        second_half_variance = sum(abs(float(tx.amount)) for tx in category_transactions[len(category_transactions)//2:])
                        
                        first_avg_variance = first_half_variance / (len(category_transactions) / 2) if len(category_transactions) > 0 else 0
                        second_avg_variance = second_half_variance / (len(category_transactions) / 2) if len(category_transactions) > 0 else 0
                        
                        if first_avg_variance == 0:
                            variance_trend_percentage = 0.0
                        else:
                            variance_trend_percentage = ((second_avg_variance - first_avg_variance) / first_avg_variance) * 100
                        
                        if abs(variance_trend_percentage) < self.budget_tracking_params['budget_alert_thresholds']['under_budget'] * 100:
                            variance_trend = TrendDirection.STABLE
                        elif variance_trend_percentage > self.budget_tracking_params['budget_alert_thresholds']['under_budget'] * 100:
                            variance_trend = TrendDirection.INCREASING
                        elif variance_trend_percentage < -self.budget_tracking_params['budget_alert_thresholds']['under_budget'] * 100:
                            variance_trend = TrendDirection.DECREASING
                        else:
                            variance_trend = TrendDirection.VOLATILE
                    else:
                        variance_trend = TrendDirection.STABLE
                        variance_trend_percentage = 0.0
                    
                    # Calculate consistency score
                    if len(category_transactions) > 1:
                        amounts = [abs(float(tx.amount)) for tx in category_transactions]
                        mean_amount = statistics.mean(amounts)
                        variance_consistency = statistics.variance(amounts) / (mean_amount ** 2) if mean_amount > 0 else 0
                        consistency_score = max(0, 1 - variance_consistency)
                    else:
                        consistency_score = 1.0
                    
                    # Generate recommendations and alerts
                    recommendations = []
                    alerts = []
                    
                    if variance_type == BudgetVarianceType.OVER_BUDGET:
                        recommendations.append(self.budget_tracking_params['budget_recommendations']['over_budget'].format(category=category))
                        alerts.append(f"Over budget by {variance_percentage:.2f}% in {category} for {month_name}")
                    elif variance_type == BudgetVarianceType.UNDER_BUDGET:
                        recommendations.append(self.budget_tracking_params['budget_recommendations']['under_budget'].format(category=category))
                        alerts.append(f"Under budget by {variance_percentage:.2f}% in {category} for {month_name}")
                    elif variance_type == BudgetVarianceType.ON_BUDGET:
                        recommendations.append(self.budget_tracking_params['budget_recommendations']['on_budget'].format(category=category))
                        alerts.append(f"On budget for {category} for {month_name}")
                    elif variance_type == BudgetVarianceType.NO_BUDGET:
                        recommendations.append(f"No budget set for {category} for {month_name}")
                        alerts.append(f"No budget set for {category} for {month_name}")
                    
                    variances.append(BudgetVarianceAnalysis(
                        category=category,
                        period=AnalysisPeriod.MONTHLY, # Assuming monthly for simplicity
                        start_date=month_start_date,
                        end_date=month_end_date,
                        budget_amount=pattern.total_amount,
                        actual_spending=actual_spending,
                        variance_amount=variance_amount,
                        variance_percentage=variance_percentage,
                        variance_type=variance_type,
                        transaction_count=len(category_transactions),
                        average_transaction=statistics.mean(amounts) if amounts else 0,
                        largest_transaction=max(amounts) if amounts else 0,
                        previous_period_variance=0.0, # Will be calculated if previous month data is available
                        variance_trend=variance_trend,
                        consistency_score=consistency_score,
                        alerts=alerts,
                        recommendations=recommendations,
                        metadata={
                            'actual_spending_transactions': [
                                {
                                    'date': tx.date.isoformat(),
                                    'amount': float(tx.amount),
                                    'source': tx.source,
                                    'category': tx.category
                                } for tx in category_transactions
                            ]
                        }
                    ))
        
        return variances
    
    def _calculate_overall_budget_adherence(self, cash_flows: List[MonthlyCashFlow]) -> float:
        """Calculate overall budget adherence percentage"""
        if not cash_flows:
            return 0.0
        
        total_budget_amount = 0.0
        total_actual_spending = 0.0
        
        for month_flow in cash_flows:
            # Assuming a default budget amount for each category if not available
            # This is a simplification; ideally, budget data would be stored per category
            # For now, we'll use a placeholder or calculate a rough average
            # For simplicity, let's assume a default budget for all categories
            # This will need to be refined based on actual budget data
            default_budget_amount = 1000.0 # Placeholder for a default budget
            
            total_budget_amount += default_budget_amount * 12 # Assuming 12 months
            total_actual_spending += month_flow.total_expenses
        
        adherence_percentage = (total_budget_amount / total_actual_spending * 100) if total_actual_spending > 0 else 0
        
        return adherence_percentage
    
    def _analyze_savings_rate(self, cash_flows: List[MonthlyCashFlow], year: int) -> SavingsRateAnalysis:
        """Analyze savings rate over time"""
        if not cash_flows:
            return SavingsRateAnalysis(
                period=AnalysisPeriod.YEARLY, # Default period
                start_date=datetime(year, 1, 1),
                end_date=datetime(year, 12, 31),
                total_income=0.0,
                gross_income=0.0,
                net_income=0.0,
                income_sources={},
                total_expenses=0.0,
                essential_expenses=0.0,
                discretionary_expenses=0.0,
                expense_breakdown={},
                total_savings=0.0,
                savings_rate=0.0,
                savings_rate_gross=0.0,
                savings_rate_net=0.0,
                emergency_fund=0.0,
                retirement_savings=0.0,
                investment_savings=0.0,
                other_savings=0.0,
                recommended_savings_rate=0.2,
                benchmark_percentile=0.75,
                savings_goal_progress=0.0,
                savings_trend=TrendDirection.STABLE,
                savings_consistency=0.0,
                month_over_month_change=0.0,
                insights=[],
                recommendations=[],
                metadata={}
            )
        
        # Aggregate income and expenses across all months
        total_income = sum(cf.total_income for cf in cash_flows)
        total_expenses = sum(cf.total_expenses for cf in cash_flows)
        
        # Aggregate income sources
        income_sources = defaultdict(float)
        for month_flow in cash_flows:
            for source, amount in month_flow.income_sources.items():
                income_sources[source] += amount
        
        # Aggregate expense categories
        expense_breakdown = defaultdict(float)
        for month_flow in cash_flows:
            for category, amount in month_flow.expense_categories.items():
                expense_breakdown[category] += amount
        
        # Calculate savings
        total_savings = total_income - total_expenses
        savings_rate = (total_savings / total_income * 100) if total_income > 0 else 0
        
        # Calculate gross and net savings rates
        gross_income = sum(income_sources.values())
        savings_rate_gross = (total_savings / gross_income * 100) if gross_income > 0 else 0
        
        # Calculate net savings rate (after taxes, if applicable)
        # This is a simplification; a real implementation would require tax data
        net_income = total_income # Assuming no taxes for now
        savings_rate_net = (total_savings / net_income * 100) if net_income > 0 else 0
        
        # Calculate savings categories
        emergency_fund = 0.0
        retirement_savings = 0.0
        investment_savings = 0.0
        other_savings = 0.0
        
        # This part would require actual savings data or a savings goal
        # For now, we'll use placeholders
        emergency_fund = 5000.0 # Placeholder
        retirement_savings = 10000.0 # Placeholder
        investment_savings = 5000.0 # Placeholder
        other_savings = 2000.0 # Placeholder
        
        # Calculate savings trend
        if len(cash_flows) >= 2:
            first_half_savings = sum(cf.total_savings for cf in cash_flows[:len(cash_flows)//2])
            second_half_savings = sum(cf.total_savings for cf in cash_flows[len(cash_flows)//2:])
            
            first_avg_savings = first_half_savings / (len(cash_flows) / 2) if len(cash_flows) > 0 else 0
            second_avg_savings = second_half_savings / (len(cash_flows) / 2) if len(cash_flows) > 0 else 0
            
            if first_avg_savings == 0:
                savings_trend_percentage = 0.0
            else:
                savings_trend_percentage = ((second_avg_savings - first_avg_savings) / first_avg_savings) * 100
            
            if abs(savings_trend_percentage) < self.savings_analysis_params['savings_trend_thresholds']['increasing'] * 100:
                savings_trend = TrendDirection.STABLE
            elif savings_trend_percentage > self.savings_analysis_params['savings_trend_thresholds']['increasing'] * 100:
                savings_trend = TrendDirection.INCREASING
            elif savings_trend_percentage < -self.savings_analysis_params['savings_trend_thresholds']['decreasing'] * 100:
                savings_trend = TrendDirection.DECREASING
            else:
                savings_trend = TrendDirection.VOLATILE
        else:
            savings_trend = TrendDirection.STABLE
            savings_trend_percentage = 0.0
        
        # Calculate savings consistency
        if len(cash_flows) > 1:
            amounts = [cf.total_savings for cf in cash_flows]
            mean_savings = statistics.mean(amounts)
            variance_savings = statistics.variance(amounts)
            coefficient_of_variation_savings = math.sqrt(variance_savings) / mean_savings if mean_savings > 0 else 0
            savings_consistency = max(0, 1 - coefficient_of_variation_savings)
        else:
            savings_consistency = 1.0
        
        # Calculate month-over-month change
        if len(cash_flows) > 1:
            prev_savings = cash_flows[-2].total_savings
            if prev_savings != 0:
                month_over_month_change = ((total_savings - prev_savings) / abs(prev_savings)) * 100
            else:
                month_over_month_change = 0.0
        else:
            month_over_month_change = 0.0
        
        # Generate insights and recommendations
        insights = []
        recommendations = []
        
        if savings_rate < self.savings_analysis_params['recommended_savings_rate'] * 0.8: # Significantly below recommended
            recommendations.append("Consider increasing your savings rate to achieve your financial goals.")
            insights.append("Your current savings rate is below the recommended level.")
        elif savings_rate > self.savings_analysis_params['recommended_savings_rate'] * 1.2: # Significantly above recommended
            recommendations.append("Your savings rate is higher than recommended. Consider re-evaluating your financial goals.")
        
        if savings_rate_gross < self.savings_analysis_params['recommended_savings_rate'] * 0.8: # Significantly below recommended
            recommendations.append("Your gross savings rate is below recommended. Focus on increasing income or reducing expenses.")
            insights.append("Your gross savings rate is below recommended. Consider improving income or reducing expenses.")
        elif savings_rate_gross > self.savings_analysis_params['recommended_savings_rate'] * 1.2: # Significantly above recommended
            recommendations.append("Your gross savings rate is higher than recommended. This might indicate a need to re-evaluate your financial goals.")
        
        if savings_rate_net < self.savings_analysis_params['recommended_savings_rate'] * 0.8: # Significantly below recommended
            recommendations.append("Your net savings rate is below recommended. This might indicate a need to re-evaluate your financial goals.")
            insights.append("Your net savings rate is below recommended. This might indicate a need to re-evaluate your financial goals.")
        
        if savings_consistency < 0.7: # Consistency below threshold
            recommendations.append("Your savings rate consistency is low. Consider reviewing your spending patterns.")
            insights.append("Your savings rate consistency is low. This indicates inconsistent savings behavior.")
        
        if month_over_month_change > self.savings_analysis_params['savings_trend_thresholds']['increasing'] * 100: # Significantly increasing
            recommendations.append("Your savings rate is increasing. This is a positive trend.")
            insights.append("Your savings rate is increasing. This is a positive trend.")
        elif month_over_month_change < self.savings_analysis_params['savings_trend_thresholds']['decreasing'] * 100: # Significantly decreasing
            recommendations.append("Your savings rate is decreasing. This is a concerning trend.")
            insights.append("Your savings rate is decreasing. This is a concerning trend.")
        
        return SavingsRateAnalysis(
            period=AnalysisPeriod.YEARLY, # Default period
            start_date=datetime(year, 1, 1),
            end_date=datetime(year, 12, 31),
            total_income=total_income,
            gross_income=gross_income,
            net_income=net_income,
            income_sources=dict(income_sources),
            total_expenses=total_expenses,
            essential_expenses=sum(expense_breakdown[cat] for cat in self.savings_analysis_params['essential_expense_categories']),
            discretionary_expenses=sum(expense_breakdown[cat] for cat in self.savings_analysis_params['discretionary_expense_categories']),
            expense_breakdown=dict(expense_breakdown),
            total_savings=total_savings,
            savings_rate=savings_rate,
            savings_rate_gross=savings_rate_gross,
            savings_rate_net=savings_rate_net,
            emergency_fund=emergency_fund,
            retirement_savings=retirement_savings,
            investment_savings=investment_savings,
            other_savings=other_savings,
            recommended_savings_rate=self.savings_analysis_params['recommended_savings_rate'],
            benchmark_percentile=self.savings_analysis_params['benchmark_percentile'],
            savings_goal_progress=0.0, # Will be calculated if savings goal is set
            savings_trend=savings_trend,
            savings_consistency=savings_consistency,
            month_over_month_change=month_over_month_change,
            insights=insights,
            recommendations=recommendations,
            metadata={
                'total_savings_transactions': [
                    {
                        'date': cf.date.isoformat(),
                        'amount': float(cf.amount),
                        'source': cf.source,
                        'category': cf.category
                    } for cf in cash_flows
                ]
            }
        )
    
    def _generate_financial_health_score(self, user_id: int, year: int) -> FinancialHealthScore:
        """Generate a comprehensive financial health score"""
        # This is a simplified example. A real implementation would require
        # extensive data from multiple years and external benchmarks.
        
        # Placeholder for component scores (replace with actual calculations)
        income_stability_score = 0.8
        expense_management_score = 0.7
        savings_score = 0.9
        debt_management_score = 0.6
        emergency_fund_score = 0.8
        investment_score = 0.7
        budget_adherence_score = 0.8
        cash_flow_score = 0.8
        
        # Calculate overall score
        overall_score = (
            income_stability_score * self.health_scoring_params['component_weights']['income_stability'] +
            expense_management_score * self.health_scoring_params['component_weights']['expense_management'] +
            savings_score * self.health_scoring_params['component_weights']['savings'] +
            debt_management_score * self.health_scoring_params['component_weights']['debt_management'] +
            emergency_fund_score * self.health_scoring_params['component_weights']['emergency_fund'] +
            investment_score * self.health_scoring_params['component_weights']['investment'] +
            budget_adherence_score * self.health_scoring_params['component_weights']['budget_adherence'] +
            cash_flow_score * self.health_scoring_params['component_weights']['cash_flow']
        )
        
        # Determine health level
        health_level = FinancialHealthLevel.EXCELLENT
        for level, (min_score, max_score) in self.health_scoring_params['health_levels'].items():
            if min_score <= overall_score < max_score:
                health_level = FinancialHealthLevel(level)
                break
        
        # Placeholder for detailed metrics
        income_stability_metrics = {
            'income_stability_score': income_stability_score,
            'income_variance': 0.05, # Placeholder
            'income_consistency': 0.95 # Placeholder
        }
        expense_management_metrics = {
            'expense_management_score': expense_management_score,
            'essential_expense_ratio': 0.6, # Placeholder
            'discretionary_expense_ratio': 0.4 # Placeholder
        }
        savings_metrics = {
            'savings_score': savings_score,
            'savings_rate': 0.25, # Placeholder
            'savings_consistency': 0.9 # Placeholder
        }
        debt_metrics = {
            'debt_management_score': debt_management_score,
            'total_debt': 10000.0, # Placeholder
            'debt_to_income_ratio': 0.2 # Placeholder
        }
        emergency_fund_metrics = {
            'emergency_fund_score': emergency_fund_score,
            'emergency_fund_amount': 8000.0, # Placeholder
            'emergency_fund_ratio': 0.8 # Placeholder
        }
        investment_metrics = {
            'investment_score': investment_score,
            'investment_returns': 0.08, # Placeholder
            'investment_risk': 'medium' # Placeholder
        }
        budget_metrics = {
            'budget_adherence_score': budget_adherence_score,
            'overall_budget_adherence': 0.95, # Placeholder
            'budget_variance_percentage': 0.02 # Placeholder
        }
        cash_flow_metrics = {
            'cash_flow_score': cash_flow_score,
            'net_cash_flow': 5000.0, # Placeholder
            'cash_flow_ratio': 1.5 # Placeholder
        }
        
        # Placeholder for risk factors and recommendations
        risk_factors = [
            "Income fluctuations or irregularity",
            "High essential expenses",
            "Excessive discretionary spending",
            "High debt load",
            "Lack of emergency fund",
            "Poor investment returns",
            "Inconsistent budgeting",
            "Negative cash flow"
        ]
        risk_level = "fair"
        priority_actions = ["Review income sources", "Optimize expenses", "Increase savings"]
        improvement_areas = ["Emergency fund", "Investment strategy", "Budget adherence"]
        strengths = ["Good savings rate", "Stable cash flow"]
        
        # Placeholder for previous score and score change
        previous_score = None
        score_change = None
        trend_direction = TrendDirection.STABLE
        
        return FinancialHealthScore(
            user_id=user_id,
            assessment_date=datetime.now(),
            period=AnalysisPeriod.YEARLY, # Default period
            overall_score=overall_score,
            health_level=health_level,
            income_stability_score=income_stability_score,
            expense_management_score=expense_management_score,
            savings_score=savings_score,
            debt_management_score=debt_management_score,
            emergency_fund_score=emergency_fund_score,
            investment_score=investment_score,
            budget_adherence_score=budget_adherence_score,
            cash_flow_score=cash_flow_score,
            income_stability_metrics=income_stability_metrics,
            expense_management_metrics=expense_management_metrics,
            savings_metrics=savings_metrics,
            debt_metrics=debt_metrics,
            emergency_fund_metrics=emergency_fund_metrics,
            investment_metrics=investment_metrics,
            budget_metrics=budget_metrics,
            cash_flow_metrics=cash_flow_metrics,
            risk_factors=risk_factors,
            risk_level=risk_level,
            priority_actions=priority_actions,
            improvement_areas=improvement_areas,
            strengths=strengths,
            previous_score=previous_score,
            score_change=score_change,
            trend_direction=trend_direction,
            metadata={}
        )
    
    def save_analysis_to_database(self, analysis: FinancialAnalysisSummary) -> bool:
        """Save analysis results to database"""
        try:
            # Save spending patterns
            for pattern in analysis.spending_patterns:
                spending_category = SpendingCategory(
                    user_id=analysis.user_id,
                    category_name=pattern.category,
                    total_amount=pattern.total_amount,
                    transaction_count=pattern.transaction_count,
                    average_amount=pattern.average_amount,
                    trend_direction=pattern.trend_direction.value,
                    percentage_change=pattern.percentage_change,
                    trend_period=pattern.period.value,
                    period_start=pattern.start_date,
                    period_end=pattern.end_date,
                    recommendations=json.dumps(pattern.metadata),
                    created_at=datetime.now()
                )
                self.db_session.add(spending_category)
            
            # Save financial insights
            for insight in analysis.insights:
                financial_insight = FinancialInsight(
                    user_id=analysis.user_id,
                    insight_type=insight['type'],
                    title=insight['message'],
                    description=insight['message'],
                    data=json.dumps(insight['data']),
                    impact_score=0.7 if insight['severity'] == 'high' else 0.5,
                    priority=insight['severity'],
                    is_actionable=True,
                    action_type='review',
                    action_description=insight.get('action', ''),
                    is_active=True,
                    generated_at=datetime.now(),
                    created_at=datetime.now()
                )
                self.db_session.add(financial_insight)
            
            self.db_session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving analysis to database: {str(e)}")
            self.db_session.rollback()
            return False 