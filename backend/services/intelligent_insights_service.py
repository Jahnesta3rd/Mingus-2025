"""
Intelligent Insights Service

This module provides intelligent financial insights and analysis for the MINGUS application,
including spending trend analysis, unusual transaction alerts, subscription management,
cash flow optimization, emergency fund recommendations, and debt payoff strategies.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from collections import defaultdict, Counter
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.services.basic_expense_tracking_service import BasicExpenseTrackingService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of intelligent insights"""
    SPENDING_TREND = "spending_trend"
    UNUSUAL_TRANSACTION = "unusual_transaction"
    SUBSCRIPTION_MANAGEMENT = "subscription_management"
    CASH_FLOW_OPTIMIZATION = "cash_flow_optimization"
    EMERGENCY_FUND = "emergency_fund"
    DEBT_PAYOFF = "debt_payoff"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SpendingTrendInsight:
    """Spending trend analysis insight"""
    insight_id: str
    trend_type: str  # 'increasing', 'decreasing', 'stable', 'seasonal'
    category: str
    percentage_change: float
    period_comparison: str
    description: str
    recommendation: str
    confidence_score: float
    generated_at: datetime


@dataclass
class UnusualTransactionAlert:
    """Unusual transaction alert"""
    alert_id: str
    transaction_id: str
    alert_type: str  # 'high_amount', 'unusual_category', 'unusual_time', 'duplicate'
    severity: AlertSeverity
    amount: float
    description: str
    category: str
    date: date
    reason: str
    action_needed: str
    generated_at: datetime


@dataclass
class SubscriptionInsight:
    """Subscription service management insight"""
    insight_id: str
    subscription_name: str
    monthly_cost: float
    usage_frequency: str
    last_used: Optional[date]
    recommendation: str
    potential_savings: float
    action_type: str  # 'cancel', 'downgrade', 'optimize'
    generated_at: datetime


@dataclass
class CashFlowOptimization:
    """Cash flow optimization suggestion"""
    insight_id: str
    optimization_type: str  # 'timing', 'expense_reduction', 'income_increase'
    description: str
    potential_impact: float
    implementation_difficulty: str  # 'easy', 'medium', 'hard'
    timeframe: str
    steps: List[str]
    generated_at: datetime


@dataclass
class EmergencyFundRecommendation:
    """Emergency fund recommendation"""
    insight_id: str
    current_emergency_fund: float
    recommended_amount: float
    monthly_expenses: float
    months_coverage: float
    current_coverage_months: float
    recommendation: str
    monthly_contribution: float
    timeline_months: int
    priority: str  # 'high', 'medium', 'low'
    generated_at: datetime


@dataclass
class DebtPayoffStrategy:
    """Debt payoff strategy recommendation"""
    insight_id: str
    strategy_name: str
    strategy_type: str  # 'avalanche', 'snowball', 'hybrid'
    total_debt: float
    monthly_payment: float
    interest_savings: float
    payoff_timeline_months: int
    priority_order: List[str]
    monthly_allocations: Dict[str, float]
    recommendation: str
    generated_at: datetime


class IntelligentInsightsService:
    """Service for generating intelligent financial insights"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.expense_service = BasicExpenseTrackingService(db_session)
        
        # Configuration for insights
        self.config = {
            'unusual_amount_threshold': 2.0,  # Standard deviations for unusual amounts
            'spending_trend_periods': 3,  # Number of months to analyze trends
            'subscription_usage_threshold': 30,  # Days without usage to flag
            'emergency_fund_target_months': 6,  # Target months of expenses
            'debt_avalanche_threshold': 0.05,  # 5% interest rate difference for avalanche
        }
    
    def get_intelligent_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive intelligent insights for a user
        
        Args:
            user_id: User ID to generate insights for
            
        Returns:
            Complete intelligent insights data
        """
        try:
            insights = {
                'spending_trends': self._analyze_spending_trends(user_id),
                'unusual_transactions': self._detect_unusual_transactions(user_id),
                'subscription_management': self._analyze_subscriptions(user_id),
                'cash_flow_optimization': self._optimize_cash_flow(user_id),
                'emergency_fund': self._analyze_emergency_fund(user_id),
                'debt_payoff': self._generate_debt_payoff_strategy(user_id),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating intelligent insights for user {user_id}: {e}")
            return {}
    
    def _analyze_spending_trends(self, user_id: str) -> List[SpendingTrendInsight]:
        """Analyze spending trends across categories and time periods"""
        try:
            # Get user's transaction history
            entries = self.expense_service.manual_entries.get(user_id, [])
            expenses = [e for e in entries if e.transaction_type.value == 'expense']
            
            if len(expenses) < 10:  # Need minimum data for trend analysis
                return []
            
            insights = []
            
            # Analyze overall spending trend
            overall_trend = self._calculate_overall_spending_trend(expenses)
            if overall_trend:
                insights.append(overall_trend)
            
            # Analyze category-specific trends
            category_trends = self._calculate_category_spending_trends(expenses)
            insights.extend(category_trends)
            
            # Analyze seasonal patterns
            seasonal_insights = self._detect_seasonal_patterns(expenses)
            insights.extend(seasonal_insights)
            
            return insights[:5]  # Return top 5 insights
            
        except Exception as e:
            self.logger.error(f"Error analyzing spending trends for user {user_id}: {e}")
            return []
    
    def _calculate_overall_spending_trend(self, expenses: List) -> Optional[SpendingTrendInsight]:
        """Calculate overall spending trend"""
        try:
            # Group expenses by month
            monthly_expenses = defaultdict(float)
            for expense in expenses:
                month_key = expense.date.replace(day=1)
                monthly_expenses[month_key] += expense.amount
            
            if len(monthly_expenses) < 2:
                return None
            
            # Calculate trend
            months = sorted(monthly_expenses.keys())
            recent_months = months[-3:] if len(months) >= 3 else months
            previous_months = months[-6:-3] if len(months) >= 6 else months[:-3]
            
            if not previous_months:
                return None
            
            recent_avg = sum(monthly_expenses[m] for m in recent_months) / len(recent_months)
            previous_avg = sum(monthly_expenses[m] for m in previous_months) / len(previous_months)
            
            if previous_avg == 0:
                return None
            
            percentage_change = ((recent_avg - previous_avg) / previous_avg) * 100
            
            # Determine trend type
            if percentage_change > 10:
                trend_type = 'increasing'
                recommendation = "Consider reviewing your spending habits and identifying areas for cost reduction."
            elif percentage_change < -10:
                trend_type = 'decreasing'
                recommendation = "Great job! Your spending has decreased. Consider allocating the savings to your emergency fund or debt payoff."
            else:
                trend_type = 'stable'
                recommendation = "Your spending is stable. Consider setting specific financial goals to optimize your budget."
            
            return SpendingTrendInsight(
                insight_id=f"trend_overall_{int(datetime.utcnow().timestamp())}",
                trend_type=trend_type,
                category="Overall Spending",
                percentage_change=percentage_change,
                period_comparison=f"Last {len(recent_months)} months vs previous {len(previous_months)} months",
                description=f"Your overall spending has {trend_type} by {abs(percentage_change):.1f}%",
                recommendation=recommendation,
                confidence_score=0.85,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating overall spending trend: {e}")
            return None
    
    def _calculate_category_spending_trends(self, expenses: List) -> List[SpendingTrendInsight]:
        """Calculate spending trends for individual categories"""
        try:
            insights = []
            
            # Group expenses by category and month
            category_monthly = defaultdict(lambda: defaultdict(float))
            for expense in expenses:
                month_key = expense.date.replace(day=1)
                category_monthly[expense.category][month_key] += expense.amount
            
            for category, monthly_data in category_monthly.items():
                if len(monthly_data) < 2:
                    continue
                
                months = sorted(monthly_data.keys())
                recent_months = months[-2:] if len(months) >= 2 else months
                previous_months = months[-4:-2] if len(months) >= 4 else months[:-2]
                
                if not previous_months:
                    continue
                
                recent_avg = sum(monthly_data[m] for m in recent_months) / len(recent_months)
                previous_avg = sum(monthly_data[m] for m in previous_months) / len(previous_months)
                
                if previous_avg == 0:
                    continue
                
                percentage_change = ((recent_avg - previous_avg) / previous_avg) * 100
                
                # Only create insights for significant changes
                if abs(percentage_change) > 15:
                    if percentage_change > 0:
                        recommendation = f"Consider setting a budget for {category} or looking for ways to reduce spending in this category."
                    else:
                        recommendation = f"Great job reducing {category} spending! Consider maintaining this trend."
                    
                    insights.append(SpendingTrendInsight(
                        insight_id=f"trend_{category}_{int(datetime.utcnow().timestamp())}",
                        trend_type='increasing' if percentage_change > 0 else 'decreasing',
                        category=category,
                        percentage_change=percentage_change,
                        period_comparison=f"Recent vs previous {len(previous_months)} months",
                        description=f"{category} spending has {'increased' if percentage_change > 0 else 'decreased'} by {abs(percentage_change):.1f}%",
                        recommendation=recommendation,
                        confidence_score=0.80,
                        generated_at=datetime.utcnow()
                    ))
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error calculating category spending trends: {e}")
            return []
    
    def _detect_seasonal_patterns(self, expenses: List) -> List[SpendingTrendInsight]:
        """Detect seasonal spending patterns"""
        try:
            insights = []
            
            # Group by month to detect seasonal patterns
            monthly_totals = defaultdict(float)
            for expense in expenses:
                month = expense.date.month
                monthly_totals[month] += expense.amount
            
            if len(monthly_totals) < 6:
                return insights
            
            # Calculate average spending by month
            avg_by_month = {}
            for month in range(1, 13):
                if month in monthly_totals:
                    avg_by_month[month] = monthly_totals[month]
            
            if len(avg_by_month) < 6:
                return insights
            
            # Find months with significantly higher spending
            overall_avg = sum(avg_by_month.values()) / len(avg_by_month)
            threshold = overall_avg * 1.3  # 30% above average
            
            for month, amount in avg_by_month.items():
                if amount > threshold:
                    month_name = datetime(2024, month, 1).strftime('%B')
                    insights.append(SpendingTrendInsight(
                        insight_id=f"seasonal_{month}_{int(datetime.utcnow().timestamp())}",
                        trend_type='seasonal',
                        category=f"{month_name} Spending",
                        percentage_change=((amount - overall_avg) / overall_avg) * 100,
                        period_comparison="Seasonal pattern detected",
                        description=f"Your spending in {month_name} is typically {((amount - overall_avg) / overall_avg) * 100:.1f}% higher than average",
                        recommendation=f"Plan ahead for {month_name} by setting aside extra funds or adjusting your budget.",
                        confidence_score=0.75,
                        generated_at=datetime.utcnow()
                    ))
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error detecting seasonal patterns: {e}")
            return []
    
    def _detect_unusual_transactions(self, user_id: str) -> List[UnusualTransactionAlert]:
        """Detect unusual transactions based on patterns"""
        try:
            entries = self.expense_service.manual_entries.get(user_id, [])
            expenses = [e for e in entries if e.transaction_type.value == 'expense']
            
            if len(expenses) < 5:
                return []
            
            alerts = []
            
            # Calculate statistical measures
            amounts = [e.amount for e in expenses]
            mean_amount = statistics.mean(amounts)
            std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            # Detect high amount transactions
            threshold = mean_amount + (self.config['unusual_amount_threshold'] * std_amount)
            for expense in expenses:
                if expense.amount > threshold:
                    alerts.append(UnusualTransactionAlert(
                        alert_id=f"high_amount_{expense.id}",
                        transaction_id=expense.id,
                        alert_type='high_amount',
                        severity=AlertSeverity.HIGH if expense.amount > threshold * 1.5 else AlertSeverity.MEDIUM,
                        amount=expense.amount,
                        description=expense.description,
                        category=expense.category,
                        date=expense.date,
                        reason=f"Amount (${expense.amount:.2f}) is significantly higher than your average transaction (${mean_amount:.2f})",
                        action_needed="Verify this transaction and consider if it was necessary or if there's a billing error.",
                        generated_at=datetime.utcnow()
                    ))
            
            # Detect unusual categories
            category_counts = Counter(e.category for e in expenses)
            common_categories = {cat for cat, count in category_counts.items() if count >= 3}
            
            for expense in expenses:
                if expense.category not in common_categories and expense.amount > mean_amount:
                    alerts.append(UnusualTransactionAlert(
                        alert_id=f"unusual_category_{expense.id}",
                        transaction_id=expense.id,
                        alert_type='unusual_category',
                        severity=AlertSeverity.MEDIUM,
                        amount=expense.amount,
                        description=expense.description,
                        category=expense.category,
                        date=expense.date,
                        reason=f"Unusual category '{expense.category}' with high amount",
                        action_needed="Review if this expense was necessary or if it represents a new spending pattern.",
                        generated_at=datetime.utcnow()
                    ))
            
            # Detect duplicate transactions
            transaction_groups = defaultdict(list)
            for expense in expenses:
                key = (expense.description.lower(), expense.amount, expense.date)
                transaction_groups[key].append(expense)
            
            for key, group in transaction_groups.items():
                if len(group) > 1:
                    for expense in group:
                        alerts.append(UnusualTransactionAlert(
                            alert_id=f"duplicate_{expense.id}",
                            transaction_id=expense.id,
                            alert_type='duplicate',
                            severity=AlertSeverity.HIGH,
                            amount=expense.amount,
                            description=expense.description,
                            category=expense.category,
                            date=expense.date,
                            reason=f"Possible duplicate transaction - {len(group)} similar transactions found",
                            action_needed="Verify if this is a legitimate duplicate or if you were charged multiple times.",
                            generated_at=datetime.utcnow()
                        ))
            
            return alerts[:10]  # Return top 10 alerts
            
        except Exception as e:
            self.logger.error(f"Error detecting unusual transactions for user {user_id}: {e}")
            return []
    
    def _analyze_subscriptions(self, user_id: str) -> List[SubscriptionInsight]:
        """Analyze subscription services and provide optimization recommendations"""
        try:
            entries = self.expense_service.manual_entries.get(user_id, [])
            expenses = [e for e in entries if e.transaction_type.value == 'expense']
            
            # Identify potential subscriptions (recurring payments)
            subscription_patterns = self._identify_subscription_patterns(expenses)
            
            insights = []
            
            for subscription in subscription_patterns:
                # Analyze usage patterns
                usage_analysis = self._analyze_subscription_usage(subscription, expenses)
                
                if usage_analysis['recommendation']:
                    insights.append(SubscriptionInsight(
                        insight_id=f"subscription_{subscription['name']}_{int(datetime.utcnow().timestamp())}",
                        subscription_name=subscription['name'],
                        monthly_cost=subscription['monthly_cost'],
                        usage_frequency=usage_analysis['usage_frequency'],
                        last_used=usage_analysis['last_used'],
                        recommendation=usage_analysis['recommendation'],
                        potential_savings=subscription['monthly_cost'] * 12 if usage_analysis['action_type'] == 'cancel' else subscription['monthly_cost'] * 6,
                        action_type=usage_analysis['action_type'],
                        generated_at=datetime.utcnow()
                    ))
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error analyzing subscriptions for user {user_id}: {e}")
            return []
    
    def _identify_subscription_patterns(self, expenses: List) -> List[Dict[str, Any]]:
        """Identify potential subscription services from transactions"""
        try:
            # Common subscription keywords
            subscription_keywords = [
                'netflix', 'spotify', 'amazon prime', 'hulu', 'disney+', 'hbo', 'youtube premium',
                'adobe', 'microsoft', 'dropbox', 'icloud', 'google one', 'zoom', 'slack',
                'gym', 'fitness', 'weight watchers', 'hello fresh', 'blue apron',
                'audible', 'kindle unlimited', 'apple music', 'tidal'
            ]
            
            subscriptions = []
            
            # Group by description to find recurring payments
            description_groups = defaultdict(list)
            for expense in expenses:
                desc_lower = expense.description.lower()
                description_groups[desc_lower].append(expense)
            
            for desc, group in description_groups.items():
                if len(group) >= 2:  # At least 2 occurrences to be considered recurring
                    # Check if it matches subscription keywords
                    is_subscription = any(keyword in desc for keyword in subscription_keywords)
                    
                    if is_subscription:
                        # Calculate average monthly cost
                        amounts = [e.amount for e in group]
                        avg_amount = statistics.mean(amounts)
                        
                        subscriptions.append({
                            'name': expense.description,
                            'monthly_cost': avg_amount,
                            'frequency': len(group),
                            'last_payment': max(e.date for e in group),
                            'first_payment': min(e.date for e in group)
                        })
            
            return subscriptions
            
        except Exception as e:
            self.logger.error(f"Error identifying subscription patterns: {e}")
            return []
    
    def _analyze_subscription_usage(self, subscription: Dict[str, Any], expenses: List) -> Dict[str, Any]:
        """Analyze usage patterns for a subscription"""
        try:
            # This is a simplified analysis - in a real implementation,
            # you would integrate with actual usage APIs or user feedback
            
            days_since_last_payment = (date.today() - subscription['last_payment']).days
            
            if days_since_last_payment > 45:  # No recent payments
                return {
                    'usage_frequency': 'Inactive',
                    'last_used': subscription['last_payment'],
                    'recommendation': f"Consider canceling {subscription['name']} as there have been no recent payments.",
                    'action_type': 'cancel'
                }
            elif subscription['monthly_cost'] > 50:  # High-cost subscription
                return {
                    'usage_frequency': 'Active',
                    'last_used': subscription['last_payment'],
                    'recommendation': f"Review {subscription['name']} usage. Consider downgrading if not fully utilized.",
                    'action_type': 'downgrade'
                }
            else:
                return {
                    'usage_frequency': 'Active',
                    'last_used': subscription['last_payment'],
                    'recommendation': f"{subscription['name']} appears to be actively used.",
                    'action_type': 'optimize'
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing subscription usage: {e}")
            return {}
    
    def _optimize_cash_flow(self, user_id: str) -> List[CashFlowOptimization]:
        """Generate cash flow optimization suggestions"""
        try:
            entries = self.expense_service.manual_entries.get(user_id, [])
            expenses = [e for e in entries if e.transaction_type.value == 'expense']
            income = [e for e in entries if e.transaction_type.value == 'income']
            
            if not expenses or not income:
                return []
            
            optimizations = []
            
            # Analyze income timing
            income_timing = self._analyze_income_timing(income)
            if income_timing:
                optimizations.append(income_timing)
            
            # Analyze expense timing
            expense_timing = self._analyze_expense_timing(expenses)
            if expense_timing:
                optimizations.append(expense_timing)
            
            # Analyze expense reduction opportunities
            expense_reduction = self._analyze_expense_reduction(expenses)
            if expense_reduction:
                optimizations.append(expense_reduction)
            
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Error optimizing cash flow for user {user_id}: {e}")
            return []
    
    def _analyze_income_timing(self, income: List) -> Optional[CashFlowOptimization]:
        """Analyze income timing for optimization"""
        try:
            if len(income) < 2:
                return None
            
            # Group by month
            monthly_income = defaultdict(float)
            for inc in income:
                month_key = inc.date.replace(day=1)
                monthly_income[month_key] += inc.amount
            
            # Check for irregular income patterns
            amounts = list(monthly_income.values())
            if len(amounts) < 2:
                return None
            
            variance = statistics.variance(amounts)
            mean_income = statistics.mean(amounts)
            
            if variance > (mean_income * 0.3):  # High variance
                return CashFlowOptimization(
                    insight_id=f"income_timing_{int(datetime.utcnow().timestamp())}",
                    optimization_type='timing',
                    description="Your income varies significantly from month to month",
                    potential_impact=mean_income * 0.1,  # 10% improvement potential
                    implementation_difficulty='medium',
                    timeframe='3-6 months',
                    steps=[
                        "Consider negotiating consistent payment schedules with clients/employers",
                        "Set up automatic transfers to smooth out income fluctuations",
                        "Build a buffer fund to handle income gaps"
                    ],
                    generated_at=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing income timing: {e}")
            return None
    
    def _analyze_expense_timing(self, expenses: List) -> Optional[CashFlowOptimization]:
        """Analyze expense timing for optimization"""
        try:
            if len(expenses) < 10:
                return None
            
            # Check for expenses clustered at month end
            end_of_month_expenses = [e for e in expenses if e.date.day >= 25]
            mid_month_expenses = [e for e in expenses if 10 <= e.date.day <= 20]
            
            if len(end_of_month_expenses) > len(mid_month_expenses) * 1.5:
                return CashFlowOptimization(
                    insight_id=f"expense_timing_{int(datetime.utcnow().timestamp())}",
                    optimization_type='timing',
                    description="Many of your expenses occur at the end of the month",
                    potential_impact=sum(e.amount for e in end_of_month_expenses) * 0.05,
                    implementation_difficulty='easy',
                    timeframe='1-2 months',
                    steps=[
                        "Contact service providers to change billing dates to mid-month",
                        "Set up automatic payments for mid-month dates",
                        "Plan major purchases for mid-month when cash flow is better"
                    ],
                    generated_at=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing expense timing: {e}")
            return None
    
    def _analyze_expense_reduction(self, expenses: List) -> Optional[CashFlowOptimization]:
        """Analyze opportunities for expense reduction"""
        try:
            if len(expenses) < 5:
                return None
            
            # Find highest spending categories
            category_totals = defaultdict(float)
            for expense in expenses:
                category_totals[expense.category] += expense.amount
            
            top_category = max(category_totals.items(), key=lambda x: x[1])
            
            if top_category[1] > sum(category_totals.values()) * 0.3:  # More than 30% of spending
                return CashFlowOptimization(
                    insight_id=f"expense_reduction_{int(datetime.utcnow().timestamp())}",
                    optimization_type='expense_reduction',
                    description=f"{top_category[0]} represents {top_category[1]/sum(category_totals.values())*100:.1f}% of your spending",
                    potential_impact=top_category[1] * 0.15,  # 15% reduction potential
                    implementation_difficulty='medium',
                    timeframe='2-3 months',
                    steps=[
                        f"Review your {top_category[0]} spending habits",
                        "Look for cheaper alternatives or bulk purchasing options",
                        "Set a specific budget for this category",
                        "Track your progress monthly"
                    ],
                    generated_at=datetime.utcnow()
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing expense reduction: {e}")
            return None
    
    def _analyze_emergency_fund(self, user_id: str) -> Optional[EmergencyFundRecommendation]:
        """Analyze emergency fund status and provide recommendations"""
        try:
            entries = self.expense_service.manual_entries.get(user_id, [])
            expenses = [e for e in entries if e.transaction_type.value == 'expense']
            income = [e for e in entries if e.transaction_type.value == 'income']
            
            if not expenses:
                return None
            
            # Calculate monthly expenses
            monthly_expenses = self._calculate_monthly_expenses(expenses)
            
            # Estimate current emergency fund (simplified - would need actual savings data)
            current_emergency_fund = self._estimate_emergency_fund(income, expenses)
            
            # Calculate recommended amount
            recommended_amount = monthly_expenses * self.config['emergency_fund_target_months']
            
            # Calculate current coverage
            current_coverage_months = current_emergency_fund / monthly_expenses if monthly_expenses > 0 else 0
            
            # Determine priority
            if current_coverage_months < 1:
                priority = 'high'
                recommendation = "Build your emergency fund immediately. Start with a goal of 1 month of expenses."
            elif current_coverage_months < 3:
                priority = 'medium'
                recommendation = "Continue building your emergency fund to reach 6 months of expenses."
            else:
                priority = 'low'
                recommendation = "Your emergency fund is in good shape. Consider investing excess funds."
            
            # Calculate monthly contribution needed
            if current_coverage_months < self.config['emergency_fund_target_months']:
                shortfall = recommended_amount - current_emergency_fund
                timeline_months = 12  # 1 year timeline
                monthly_contribution = shortfall / timeline_months
            else:
                monthly_contribution = 0
                timeline_months = 0
            
            return EmergencyFundRecommendation(
                insight_id=f"emergency_fund_{int(datetime.utcnow().timestamp())}",
                current_emergency_fund=current_emergency_fund,
                recommended_amount=recommended_amount,
                monthly_expenses=monthly_expenses,
                months_coverage=self.config['emergency_fund_target_months'],
                current_coverage_months=current_coverage_months,
                recommendation=recommendation,
                monthly_contribution=monthly_contribution,
                timeline_months=timeline_months,
                priority=priority,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing emergency fund for user {user_id}: {e}")
            return None
    
    def _calculate_monthly_expenses(self, expenses: List) -> float:
        """Calculate average monthly expenses"""
        try:
            if not expenses:
                return 0
            
            # Group by month
            monthly_expenses = defaultdict(float)
            for expense in expenses:
                month_key = expense.date.replace(day=1)
                monthly_expenses[month_key] += expense.amount
            
            if not monthly_expenses:
                return 0
            
            return sum(monthly_expenses.values()) / len(monthly_expenses)
            
        except Exception as e:
            self.logger.error(f"Error calculating monthly expenses: {e}")
            return 0
    
    def _estimate_emergency_fund(self, income: List, expenses: List) -> float:
        """Estimate current emergency fund based on income and expenses"""
        try:
            # This is a simplified estimation - in reality, you'd need actual savings account data
            
            if not income or not expenses:
                return 0
            
            # Calculate net income over time
            total_income = sum(inc.amount for inc in income)
            total_expenses = sum(exp.amount for exp in expenses)
            
            # Assume some savings rate (simplified)
            net_income = total_income - total_expenses
            estimated_savings = max(0, net_income * 0.2)  # Assume 20% savings rate
            
            return estimated_savings
            
        except Exception as e:
            self.logger.error(f"Error estimating emergency fund: {e}")
            return 0
    
    def _generate_debt_payoff_strategy(self, user_id: str) -> Optional[DebtPayoffStrategy]:
        """Generate debt payoff strategy recommendations"""
        try:
            # This is a simplified implementation - in reality, you'd need actual debt data
            # For now, we'll create a sample strategy based on common debt scenarios
            
            # Mock debt data (in real implementation, this would come from debt tracking)
            mock_debts = [
                {'name': 'Credit Card 1', 'balance': 5000, 'interest_rate': 0.18, 'minimum_payment': 150},
                {'name': 'Student Loan', 'balance': 25000, 'interest_rate': 0.05, 'minimum_payment': 300},
                {'name': 'Car Loan', 'balance': 15000, 'interest_rate': 0.06, 'minimum_payment': 400}
            ]
            
            if not mock_debts:
                return None
            
            total_debt = sum(debt['balance'] for debt in mock_debts)
            total_monthly_payment = sum(debt['minimum_payment'] for debt in mock_debts)
            
            # Determine best strategy
            high_interest_debts = [d for d in mock_debts if d['interest_rate'] > 0.10]
            low_balance_debts = [d for d in mock_debts if d['balance'] < 5000]
            
            if high_interest_debts and low_balance_debts:
                strategy_type = 'hybrid'
                strategy_name = 'Hybrid Approach'
                recommendation = "Focus on high-interest debts first, but also pay off small balances for quick wins."
            elif high_interest_debts:
                strategy_type = 'avalanche'
                strategy_name = 'Avalanche Method'
                recommendation = "Pay off high-interest debts first to minimize total interest paid."
            else:
                strategy_type = 'snowball'
                strategy_name = 'Snowball Method'
                recommendation = "Pay off smallest debts first for psychological wins and momentum."
            
            # Calculate priority order
            if strategy_type == 'avalanche':
                priority_order = sorted(mock_debts, key=lambda x: x['interest_rate'], reverse=True)
            elif strategy_type == 'snowball':
                priority_order = sorted(mock_debts, key=lambda x: x['balance'])
            else:  # hybrid
                priority_order = sorted(mock_debts, key=lambda x: (x['interest_rate'], x['balance']), reverse=True)
            
            # Calculate monthly allocations
            monthly_allocations = {}
            extra_payment = 200  # Assume $200 extra per month
            
            for i, debt in enumerate(priority_order):
                if i == 0:  # First priority gets extra payment
                    monthly_allocations[debt['name']] = debt['minimum_payment'] + extra_payment
                else:
                    monthly_allocations[debt['name']] = debt['minimum_payment']
            
            # Estimate payoff timeline and interest savings
            payoff_timeline_months = self._estimate_payoff_timeline(mock_debts, monthly_allocations)
            interest_savings = self._calculate_interest_savings(mock_debts, strategy_type)
            
            return DebtPayoffStrategy(
                insight_id=f"debt_strategy_{int(datetime.utcnow().timestamp())}",
                strategy_name=strategy_name,
                strategy_type=strategy_type,
                total_debt=total_debt,
                monthly_payment=total_monthly_payment + extra_payment,
                interest_savings=interest_savings,
                payoff_timeline_months=payoff_timeline_months,
                priority_order=[debt['name'] for debt in priority_order],
                monthly_allocations=monthly_allocations,
                recommendation=recommendation,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error generating debt payoff strategy for user {user_id}: {e}")
            return None
    
    def _estimate_payoff_timeline(self, debts: List[Dict], allocations: Dict[str, float]) -> int:
        """Estimate debt payoff timeline"""
        try:
            # Simplified calculation - in reality, this would be more complex
            total_balance = sum(debt['balance'] for debt in debts)
            total_monthly_payment = sum(allocations.values())
            
            if total_monthly_payment <= 0:
                return 999  # Never
            
            # Assume average interest rate of 10%
            effective_monthly_rate = 0.10 / 12
            
            # Simplified payoff calculation
            months = 0
            remaining_balance = total_balance
            
            while remaining_balance > 0 and months < 120:  # Max 10 years
                interest = remaining_balance * effective_monthly_rate
                principal_payment = total_monthly_payment - interest
                remaining_balance -= principal_payment
                months += 1
            
            return months
            
        except Exception as e:
            self.logger.error(f"Error estimating payoff timeline: {e}")
            return 60  # Default 5 years
    
    def _calculate_interest_savings(self, debts: List[Dict], strategy: str) -> float:
        """Calculate potential interest savings"""
        try:
            # Simplified calculation
            total_interest = sum(debt['balance'] * debt['interest_rate'] for debt in debts)
            
            if strategy == 'avalanche':
                savings_rate = 0.25  # 25% savings with avalanche
            elif strategy == 'snowball':
                savings_rate = 0.15  # 15% savings with snowball
            else:  # hybrid
                savings_rate = 0.20  # 20% savings with hybrid
            
            return total_interest * savings_rate
            
        except Exception as e:
            self.logger.error(f"Error calculating interest savings: {e}")
            return 0 