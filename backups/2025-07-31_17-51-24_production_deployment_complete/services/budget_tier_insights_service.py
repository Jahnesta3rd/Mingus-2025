"""
Budget Tier Intelligent Insights Service

This module provides intelligent insights for Budget tier users including:
- Unusual spending detection
- Subscription service identification
- Bill due date predictions
- Cash flow optimization suggestions
- Financial goal progress tracking
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re
from collections import defaultdict, Counter
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, extract
from sqlalchemy.exc import SQLAlchemyError

from backend.models.manual_transaction_models import ManualTransaction, ExpenseCategory
from backend.services.budget_tier_service import BudgetTierService
from backend.utils.validation import validate_amount, validate_date

logger = logging.getLogger(__name__)


class InsightType(Enum):
    """Types of intelligent insights"""
    UNUSUAL_SPENDING = "unusual_spending"
    SUBSCRIPTION_IDENTIFICATION = "subscription_identification"
    BILL_DUE_PREDICTION = "bill_due_prediction"
    CASH_FLOW_OPTIMIZATION = "cash_flow_optimization"
    GOAL_PROGRESS = "goal_progress"


class InsightSeverity(Enum):
    """Insight severity levels"""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


@dataclass
class UnusualSpendingInsight:
    """Unusual spending pattern insight"""
    transaction_id: str
    transaction_name: str
    amount: Decimal
    category: str
    date: date
    unusual_factor: float  # How unusual this spending is (1.0 = normal, 2.0 = 2x normal)
    historical_average: Decimal
    historical_std: Decimal
    reason: str
    severity: InsightSeverity
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SubscriptionInsight:
    """Subscription service identification insight"""
    service_name: str
    amount: Decimal
    frequency: str  # monthly, quarterly, yearly
    next_due_date: date
    confidence: float  # 0.0 to 1.0
    category: str
    merchant_patterns: List[str] = field(default_factory=list)
    total_spent: Decimal
    recommendations: List[str] = field(default_factory=list)


@dataclass
class BillDuePrediction:
    """Bill due date prediction"""
    bill_name: str
    predicted_amount: Decimal
    predicted_due_date: date
    confidence: float  # 0.0 to 1.0
    category: str
    historical_pattern: Dict[str, Any]
    last_paid_date: date
    recommendations: List[str] = field(default_factory=list)


@dataclass
class CashFlowOptimizationInsight:
    """Cash flow optimization suggestion"""
    insight_type: str
    title: str
    description: str
    potential_savings: Decimal
    implementation_difficulty: str  # easy, medium, hard
    time_to_impact: str  # immediate, short_term, long_term
    category: str
    data_points: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)


@dataclass
class GoalProgressInsight:
    """Financial goal progress tracking"""
    goal_name: str
    goal_type: str  # savings, debt_payoff, spending_reduction, income_increase
    current_progress: float  # 0.0 to 1.0
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    projected_completion_date: date
    on_track: bool
    recommendations: List[str] = field(default_factory=list)


class BudgetTierInsightsService:
    """Service for intelligent insights in Budget tier"""
    
    def __init__(self, db_session: Session, budget_service: BudgetTierService):
        self.db_session = db_session
        self.budget_service = budget_service
        
        # Configuration for insights
        self.unusual_spending_threshold = 2.0  # 2x standard deviation
        self.subscription_confidence_threshold = 0.7
        self.bill_prediction_confidence_threshold = 0.6
        
        # Subscription patterns
        self.subscription_keywords = [
            'netflix', 'spotify', 'amazon prime', 'hulu', 'disney+', 'hbo max',
            'youtube premium', 'apple music', 'microsoft 365', 'adobe',
            'dropbox', 'box', 'slack', 'zoom', 'asana', 'trello',
            'gym', 'fitness', 'yoga', 'pilates', 'crossfit',
            'insurance', 'phone', 'internet', 'cable', 'electricity',
            'water', 'gas', 'trash', 'sewage', 'hoa', 'rent', 'mortgage'
        ]
        
        # Bill patterns
        self.bill_keywords = [
            'bill', 'payment', 'due', 'statement', 'invoice',
            'rent', 'mortgage', 'insurance', 'utilities', 'phone',
            'internet', 'cable', 'electricity', 'water', 'gas'
        ]
    
    def generate_comprehensive_insights(self, user_id: str, days_back: int = 90) -> Dict[str, Any]:
        """
        Generate comprehensive intelligent insights for a user
        
        Args:
            user_id: User ID
            days_back: Number of days to analyze (default: 90)
            
        Returns:
            Dictionary containing all insights
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            # Get user's transactions
            transactions = self._get_user_transactions(user_id, start_date, end_date)
            
            if not transactions:
                return {
                    'success': True,
                    'insights': {
                        'unusual_spending': [],
                        'subscriptions': [],
                        'bill_predictions': [],
                        'cash_flow_optimization': [],
                        'goal_progress': []
                    },
                    'message': 'No transactions found for analysis'
                }
            
            # Generate insights
            unusual_spending = self._detect_unusual_spending(transactions, user_id)
            subscriptions = self._identify_subscriptions(transactions)
            bill_predictions = self._predict_bill_due_dates(transactions, user_id)
            cash_flow_optimization = self._generate_cash_flow_optimizations(transactions, user_id)
            goal_progress = self._track_goal_progress(transactions, user_id)
            
            return {
                'success': True,
                'insights': {
                    'unusual_spending': [insight.__dict__ for insight in unusual_spending],
                    'subscriptions': [insight.__dict__ for insight in subscriptions],
                    'bill_predictions': [insight.__dict__ for insight in bill_predictions],
                    'cash_flow_optimization': [insight.__dict__ for insight in cash_flow_optimization],
                    'goal_progress': [insight.__dict__ for insight in goal_progress]
                },
                'summary': {
                    'total_insights': len(unusual_spending) + len(subscriptions) + 
                                    len(bill_predictions) + len(cash_flow_optimization) + 
                                    len(goal_progress),
                    'analysis_period': f"{start_date} to {end_date}",
                    'transactions_analyzed': len(transactions)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive insights for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to generate insights'
            }
    
    def _get_user_transactions(self, user_id: str, start_date: date, end_date: date) -> List[ManualTransaction]:
        """Get user transactions for analysis"""
        try:
            # This would typically query the database
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            logger.error(f"Error getting user transactions: {str(e)}")
            return []
    
    def _detect_unusual_spending(self, transactions: List[ManualTransaction], user_id: str) -> List[UnusualSpendingInsight]:
        """Detect unusual spending patterns"""
        insights = []
        
        try:
            # Group transactions by category
            category_transactions = defaultdict(list)
            for transaction in transactions:
                if transaction.entry_type == 'expense':
                    category_transactions[transaction.category].append(transaction)
            
            # Analyze each category
            for category, category_txns in category_transactions.items():
                if len(category_txns) < 3:  # Need at least 3 transactions for analysis
                    continue
                
                # Calculate statistics
                amounts = [txn.amount for txn in category_txns]
                mean_amount = statistics.mean(amounts)
                std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
                
                if std_amount == 0:
                    continue
                
                # Check for unusual transactions
                for transaction in category_txns:
                    z_score = abs((transaction.amount - mean_amount) / std_amount)
                    
                    if z_score > self.unusual_spending_threshold:
                        unusual_factor = transaction.amount / mean_amount
                        
                        # Determine severity
                        if z_score > 4.0:
                            severity = InsightSeverity.CRITICAL
                        elif z_score > 3.0:
                            severity = InsightSeverity.ALERT
                        elif z_score > 2.0:
                            severity = InsightSeverity.WARNING
                        else:
                            severity = InsightSeverity.INFO
                        
                        # Generate recommendations
                        recommendations = self._generate_unusual_spending_recommendations(
                            transaction, category, unusual_factor, mean_amount
                        )
                        
                        insight = UnusualSpendingInsight(
                            transaction_id=str(transaction.id),
                            transaction_name=transaction.name,
                            amount=transaction.amount,
                            category=category,
                            date=transaction.date,
                            unusual_factor=unusual_factor,
                            historical_average=Decimal(str(mean_amount)),
                            historical_std=Decimal(str(std_amount)),
                            reason=f"Transaction is {unusual_factor:.1f}x higher than average for {category}",
                            severity=severity,
                            recommendations=recommendations
                        )
                        
                        insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error detecting unusual spending: {str(e)}")
        
        return insights
    
    def _identify_subscriptions(self, transactions: List[ManualTransaction]) -> List[SubscriptionInsight]:
        """Identify subscription services from transactions"""
        insights = []
        
        try:
            # Group transactions by merchant name
            merchant_transactions = defaultdict(list)
            for transaction in transactions:
                if transaction.merchant_name:
                    merchant_transactions[transaction.merchant_name.lower()].append(transaction)
            
            # Analyze each merchant for subscription patterns
            for merchant, merchant_txns in merchant_transactions.items():
                if len(merchant_txns) < 2:  # Need at least 2 transactions
                    continue
                
                # Check if merchant matches subscription patterns
                subscription_score = self._calculate_subscription_score(merchant, merchant_txns)
                
                if subscription_score > self.subscription_confidence_threshold:
                    # Analyze frequency
                    frequency = self._determine_subscription_frequency(merchant_txns)
                    
                    # Calculate next due date
                    next_due_date = self._predict_next_due_date(merchant_txns, frequency)
                    
                    # Calculate total spent
                    total_spent = sum(txn.amount for txn in merchant_txns)
                    
                    # Generate recommendations
                    recommendations = self._generate_subscription_recommendations(
                        merchant, total_spent, frequency
                    )
                    
                    insight = SubscriptionInsight(
                        service_name=merchant,
                        amount=merchant_txns[-1].amount,  # Most recent amount
                        frequency=frequency,
                        next_due_date=next_due_date,
                        confidence=subscription_score,
                        category=merchant_txns[0].category,
                        merchant_patterns=[merchant],
                        total_spent=total_spent,
                        recommendations=recommendations
                    )
                    
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error identifying subscriptions: {str(e)}")
        
        return insights
    
    def _predict_bill_due_dates(self, transactions: List[ManualTransaction], user_id: str) -> List[BillDuePrediction]:
        """Predict upcoming bill due dates"""
        insights = []
        
        try:
            # Group transactions by bill type
            bill_transactions = defaultdict(list)
            for transaction in transactions:
                if self._is_bill_transaction(transaction):
                    bill_type = self._categorize_bill(transaction)
                    bill_transactions[bill_type].append(transaction)
            
            # Analyze each bill type
            for bill_type, bill_txns in bill_transactions.items():
                if len(bill_txns) < 2:  # Need at least 2 transactions
                    continue
                
                # Analyze payment pattern
                payment_pattern = self._analyze_payment_pattern(bill_txns)
                
                if payment_pattern['confidence'] > self.bill_prediction_confidence_threshold:
                    # Predict next due date
                    next_due_date = self._predict_bill_due_date(bill_txns, payment_pattern)
                    
                    # Predict amount
                    predicted_amount = self._predict_bill_amount(bill_txns)
                    
                    # Generate recommendations
                    recommendations = self._generate_bill_recommendations(
                        bill_type, predicted_amount, next_due_date
                    )
                    
                    insight = BillDuePrediction(
                        bill_name=bill_type,
                        predicted_amount=predicted_amount,
                        predicted_due_date=next_due_date,
                        confidence=payment_pattern['confidence'],
                        category=bill_txns[0].category,
                        historical_pattern=payment_pattern,
                        last_paid_date=bill_txns[-1].date,
                        recommendations=recommendations
                    )
                    
                    insights.append(insight)
            
        except Exception as e:
            logger.error(f"Error predicting bill due dates: {str(e)}")
        
        return insights
    
    def _generate_cash_flow_optimizations(self, transactions: List[ManualTransaction], user_id: str) -> List[CashFlowOptimizationInsight]:
        """Generate cash flow optimization suggestions"""
        insights = []
        
        try:
            # Analyze spending patterns
            spending_analysis = self._analyze_spending_patterns(transactions)
            
            # Generate optimization insights
            insights.extend(self._generate_spending_optimizations(spending_analysis))
            insights.extend(self._generate_income_optimizations(transactions))
            insights.extend(self._generate_timing_optimizations(transactions))
            
        except Exception as e:
            logger.error(f"Error generating cash flow optimizations: {str(e)}")
        
        return insights
    
    def _track_goal_progress(self, transactions: List[ManualTransaction], user_id: str) -> List[GoalProgressInsight]:
        """Track financial goal progress"""
        insights = []
        
        try:
            # This would typically integrate with user's financial goals
            # For now, generate sample insights based on spending patterns
            
            # Savings goal tracking
            savings_insight = self._track_savings_goal(transactions, user_id)
            if savings_insight:
                insights.append(savings_insight)
            
            # Spending reduction goal tracking
            spending_insight = self._track_spending_reduction_goal(transactions, user_id)
            if spending_insight:
                insights.append(spending_insight)
            
            # Debt payoff goal tracking
            debt_insight = self._track_debt_payoff_goal(transactions, user_id)
            if debt_insight:
                insights.append(debt_insight)
            
        except Exception as e:
            logger.error(f"Error tracking goal progress: {str(e)}")
        
        return insights
    
    def _calculate_subscription_score(self, merchant: str, transactions: List[ManualTransaction]) -> float:
        """Calculate confidence score for subscription identification"""
        score = 0.0
        
        # Check for subscription keywords
        merchant_lower = merchant.lower()
        for keyword in self.subscription_keywords:
            if keyword in merchant_lower:
                score += 0.3
                break
        
        # Check for regular intervals
        if len(transactions) >= 3:
            dates = sorted([txn.date for txn in transactions])
            intervals = []
            for i in range(1, len(dates)):
                interval = (dates[i] - dates[i-1]).days
                intervals.append(interval)
            
            # Check if intervals are consistent
            if len(intervals) > 1:
                avg_interval = statistics.mean(intervals)
                std_interval = statistics.stdev(intervals)
                if std_interval < avg_interval * 0.2:  # Within 20% of average
                    score += 0.4
        
        # Check for similar amounts
        amounts = [txn.amount for txn in transactions]
        if len(amounts) > 1:
            amount_std = statistics.stdev(amounts)
            amount_mean = statistics.mean(amounts)
            if amount_std < amount_mean * 0.1:  # Within 10% of average
                score += 0.3
        
        return min(score, 1.0)
    
    def _determine_subscription_frequency(self, transactions: List[ManualTransaction]) -> str:
        """Determine subscription frequency"""
        if len(transactions) < 2:
            return "unknown"
        
        dates = sorted([txn.date for txn in transactions])
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            intervals.append(interval)
        
        avg_interval = statistics.mean(intervals)
        
        if avg_interval <= 7:
            return "weekly"
        elif avg_interval <= 35:
            return "monthly"
        elif avg_interval <= 100:
            return "quarterly"
        else:
            return "yearly"
    
    def _predict_next_due_date(self, transactions: List[ManualTransaction], frequency: str) -> date:
        """Predict next due date for subscription"""
        if not transactions:
            return date.today()
        
        last_transaction = max(transactions, key=lambda x: x.date)
        
        if frequency == "weekly":
            return last_transaction.date + timedelta(days=7)
        elif frequency == "monthly":
            return last_transaction.date + timedelta(days=30)
        elif frequency == "quarterly":
            return last_transaction.date + timedelta(days=90)
        elif frequency == "yearly":
            return last_transaction.date + timedelta(days=365)
        else:
            return last_transaction.date + timedelta(days=30)  # Default to monthly
    
    def _is_bill_transaction(self, transaction: ManualTransaction) -> bool:
        """Check if transaction is likely a bill payment"""
        if not transaction.merchant_name:
            return False
        
        merchant_lower = transaction.merchant_name.lower()
        return any(keyword in merchant_lower for keyword in self.bill_keywords)
    
    def _categorize_bill(self, transaction: ManualTransaction) -> str:
        """Categorize bill type"""
        merchant_lower = transaction.merchant_name.lower()
        
        if any(word in merchant_lower for word in ['rent', 'mortgage']):
            return "Housing"
        elif any(word in merchant_lower for word in ['electricity', 'power']):
            return "Electricity"
        elif any(word in merchant_lower for word in ['water', 'sewage']):
            return "Water"
        elif any(word in merchant_lower for word in ['gas', 'natural gas']):
            return "Gas"
        elif any(word in merchant_lower for word in ['phone', 'mobile', 'cell']):
            return "Phone"
        elif any(word in merchant_lower for word in ['internet', 'wifi', 'broadband']):
            return "Internet"
        elif any(word in merchant_lower for word in ['insurance']):
            return "Insurance"
        else:
            return "Other Bills"
    
    def _analyze_payment_pattern(self, transactions: List[ManualTransaction]) -> Dict[str, Any]:
        """Analyze payment pattern for bill prediction"""
        if len(transactions) < 2:
            return {'confidence': 0.0}
        
        dates = sorted([txn.date for txn in transactions])
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            intervals.append(interval)
        
        avg_interval = statistics.mean(intervals)
        std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
        
        # Calculate confidence based on consistency
        if std_interval == 0:
            confidence = 1.0
        else:
            confidence = max(0.0, 1.0 - (std_interval / avg_interval))
        
        return {
            'confidence': confidence,
            'avg_interval': avg_interval,
            'std_interval': std_interval,
            'last_payment': dates[-1]
        }
    
    def _predict_bill_due_date(self, transactions: List[ManualTransaction], pattern: Dict[str, Any]) -> date:
        """Predict next bill due date"""
        if not transactions:
            return date.today()
        
        last_payment = pattern['last_payment']
        avg_interval = pattern['avg_interval']
        
        return last_payment + timedelta(days=int(avg_interval))
    
    def _predict_bill_amount(self, transactions: List[ManualTransaction]) -> Decimal:
        """Predict next bill amount"""
        if not transactions:
            return Decimal('0')
        
        amounts = [txn.amount for txn in transactions]
        return Decimal(str(statistics.mean(amounts)))
    
    def _analyze_spending_patterns(self, transactions: List[ManualTransaction]) -> Dict[str, Any]:
        """Analyze spending patterns for optimization"""
        expenses = [txn for txn in transactions if txn.entry_type == 'expense']
        
        if not expenses:
            return {}
        
        # Category analysis
        category_totals = defaultdict(Decimal)
        for expense in expenses:
            category_totals[expense.category] += expense.amount
        
        # Monthly spending
        monthly_spending = defaultdict(Decimal)
        for expense in expenses:
            month_key = expense.date.replace(day=1)
            monthly_spending[month_key] += expense.amount
        
        return {
            'category_totals': dict(category_totals),
            'monthly_spending': dict(monthly_spending),
            'total_expenses': sum(category_totals.values()),
            'avg_monthly_spending': statistics.mean(monthly_spending.values()) if monthly_spending else 0
        }
    
    def _generate_spending_optimizations(self, spending_analysis: Dict[str, Any]) -> List[CashFlowOptimizationInsight]:
        """Generate spending optimization insights"""
        insights = []
        
        if not spending_analysis:
            return insights
        
        category_totals = spending_analysis.get('category_totals', {})
        total_expenses = spending_analysis.get('total_expenses', Decimal('0'))
        
        # Find highest spending categories
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        for category, amount in sorted_categories[:3]:  # Top 3 categories
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            
            if percentage > 20:  # More than 20% of total spending
                potential_savings = amount * Decimal('0.15')  # 15% potential savings
                
                insight = CashFlowOptimizationInsight(
                    insight_type="spending_reduction",
                    title=f"High {category.title()} Spending",
                    description=f"Your {category} spending represents {percentage:.1f}% of total expenses",
                    potential_savings=potential_savings,
                    implementation_difficulty="medium",
                    time_to_impact="short_term",
                    category=category,
                    data_points=[f"{category}: ${amount}"],
                    action_items=[
                        f"Review {category} expenses",
                        "Look for cheaper alternatives",
                        "Set spending limits for this category"
                    ]
                )
                
                insights.append(insight)
        
        return insights
    
    def _generate_income_optimizations(self, transactions: List[ManualTransaction]) -> List[CashFlowOptimizationInsight]:
        """Generate income optimization insights"""
        insights = []
        
        income_transactions = [txn for txn in transactions if txn.entry_type == 'income']
        
        if not income_transactions:
            # No income data
            insight = CashFlowOptimizationInsight(
                insight_type="income_tracking",
                title="Track Your Income",
                description="Start tracking your income to get better cash flow insights",
                potential_savings=Decimal('0'),
                implementation_difficulty="easy",
                time_to_impact="immediate",
                category="income",
                data_points=["No income transactions found"],
                action_items=[
                    "Add your salary payments",
                    "Track side hustle income",
                    "Record any other income sources"
                ]
            )
            insights.append(insight)
        
        return insights
    
    def _generate_timing_optimizations(self, transactions: List[ManualTransaction]) -> List[CashFlowOptimizationInsight]:
        """Generate timing optimization insights"""
        insights = []
        
        # Analyze payment timing
        expenses = [txn for txn in transactions if txn.entry_type == 'expense']
        
        if len(expenses) < 5:
            return insights
        
        # Check for end-of-month spending spike
        monthly_spending = defaultdict(Decimal)
        for expense in expenses:
            month_key = expense.date.replace(day=1)
            monthly_spending[month_key] += expense.amount
        
        # Look for patterns
        if len(monthly_spending) >= 2:
            spending_values = list(monthly_spending.values())
            avg_spending = statistics.mean(spending_values)
            max_spending = max(spending_values)
            
            if max_spending > avg_spending * 1.5:  # 50% higher than average
                insight = CashFlowOptimizationInsight(
                    insight_type="timing_optimization",
                    title="End-of-Month Spending Spike",
                    description="Your spending tends to spike at the end of the month",
                    potential_savings=avg_spending * Decimal('0.1'),  # 10% potential savings
                    implementation_difficulty="medium",
                    time_to_impact="short_term",
                    category="timing",
                    data_points=[f"Average monthly spending: ${avg_spending}"],
                    action_items=[
                        "Plan major purchases earlier in the month",
                        "Set aside money for end-of-month expenses",
                        "Review what causes the spending spike"
                    ]
                )
                insights.append(insight)
        
        return insights
    
    def _track_savings_goal(self, transactions: List[ManualTransaction], user_id: str) -> Optional[GoalProgressInsight]:
        """Track savings goal progress"""
        # This would typically integrate with user's savings goals
        # For now, generate a sample insight
        
        income_transactions = [txn for txn in transactions if txn.entry_type == 'income']
        expense_transactions = [txn for txn in transactions if txn.entry_type == 'expense']
        
        if not income_transactions or not expense_transactions:
            return None
        
        total_income = sum(txn.amount for txn in income_transactions)
        total_expenses = sum(txn.amount for txn in expense_transactions)
        
        if total_income <= total_expenses:
            return None
        
        savings = total_income - total_expenses
        savings_rate = savings / total_income if total_income > 0 else 0
        
        # Assume 20% savings goal
        target_savings_rate = 0.20
        current_progress = min(savings_rate / target_savings_rate, 1.0)
        
        insight = GoalProgressInsight(
            goal_name="Emergency Fund Savings",
            goal_type="savings",
            current_progress=current_progress,
            target_amount=total_income * Decimal(str(target_savings_rate)),
            current_amount=savings,
            remaining_amount=max(Decimal('0'), total_income * Decimal(str(target_savings_rate)) - savings),
            projected_completion_date=date.today() + timedelta(days=30),  # Placeholder
            on_track=current_progress >= 0.8,
            recommendations=[
                "Aim to save 20% of your income",
                "Set up automatic transfers to savings",
                "Reduce expenses to increase savings rate"
            ]
        )
        
        return insight
    
    def _track_spending_reduction_goal(self, transactions: List[ManualTransaction], user_id: str) -> Optional[GoalProgressInsight]:
        """Track spending reduction goal progress"""
        # This would typically integrate with user's spending reduction goals
        # For now, generate a sample insight
        
        expense_transactions = [txn for txn in transactions if txn.entry_type == 'expense']
        
        if len(expense_transactions) < 2:
            return None
        
        # Compare recent vs older spending
        recent_transactions = [txn for txn in expense_transactions if txn.date >= date.today() - timedelta(days=30)]
        older_transactions = [txn for txn in expense_transactions if txn.date < date.today() - timedelta(days=30)]
        
        if not recent_transactions or not older_transactions:
            return None
        
        recent_spending = sum(txn.amount for txn in recent_transactions)
        older_spending = sum(txn.amount for txn in older_transactions)
        
        if older_spending <= 0:
            return None
        
        reduction_percentage = (older_spending - recent_spending) / older_spending
        target_reduction = 0.10  # 10% reduction goal
        
        current_progress = min(reduction_percentage / target_reduction, 1.0)
        
        insight = GoalProgressInsight(
            goal_name="Spending Reduction",
            goal_type="spending_reduction",
            current_progress=current_progress,
            target_amount=older_spending * Decimal(str(target_reduction)),
            current_amount=older_spending - recent_spending,
            remaining_amount=max(Decimal('0'), older_spending * Decimal(str(target_reduction)) - (older_spending - recent_spending)),
            projected_completion_date=date.today() + timedelta(days=60),  # Placeholder
            on_track=current_progress >= 0.8,
            recommendations=[
                "Continue monitoring your spending",
                "Look for areas to cut back further",
                "Set specific spending limits by category"
            ]
        )
        
        return insight
    
    def _track_debt_payoff_goal(self, transactions: List[ManualTransaction], user_id: str) -> Optional[GoalProgressInsight]:
        """Track debt payoff goal progress"""
        # This would typically integrate with user's debt payoff goals
        # For now, return None as debt tracking requires more complex logic
        return None
    
    def _generate_unusual_spending_recommendations(self, transaction: ManualTransaction, category: str, 
                                                 unusual_factor: float, avg_amount: float) -> List[str]:
        """Generate recommendations for unusual spending"""
        recommendations = []
        
        if unusual_factor > 3.0:
            recommendations.append("This is significantly higher than your usual spending")
            recommendations.append("Consider if this was a necessary expense")
            recommendations.append("Review your budget for this category")
        elif unusual_factor > 2.0:
            recommendations.append("This is higher than your average spending")
            recommendations.append("Monitor if this becomes a pattern")
        
        recommendations.append(f"Your average {category} spending is ${avg_amount:.2f}")
        
        return recommendations
    
    def _generate_subscription_recommendations(self, service_name: str, total_spent: Decimal, 
                                            frequency: str) -> List[str]:
        """Generate recommendations for subscription services"""
        recommendations = []
        
        recommendations.append(f"Track your {service_name} subscription")
        recommendations.append(f"Total spent: ${total_spent}")
        recommendations.append(f"Billing frequency: {frequency}")
        
        if frequency == "monthly" and total_spent > Decimal('50'):
            recommendations.append("Consider annual billing for potential savings")
        
        recommendations.append("Review if you're getting value from this service")
        
        return recommendations
    
    def _generate_bill_recommendations(self, bill_name: str, predicted_amount: Decimal, 
                                     due_date: date) -> List[str]:
        """Generate recommendations for bill predictions"""
        recommendations = []
        
        days_until_due = (due_date - date.today()).days
        
        recommendations.append(f"Prepare for {bill_name} payment")
        recommendations.append(f"Predicted amount: ${predicted_amount}")
        recommendations.append(f"Due date: {due_date.strftime('%B %d, %Y')}")
        
        if days_until_due <= 7:
            recommendations.append("Payment due soon - ensure funds are available")
        elif days_until_due <= 14:
            recommendations.append("Payment due in 2 weeks - start planning")
        
        return recommendations 