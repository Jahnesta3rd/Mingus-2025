"""
Mid-Tier Features Service

This module provides specialized services for Mid-tier subscription features including
standard categorization, basic spending insights, 6-month cash flow forecasting,
and savings goal tracking.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter
import json
import re
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidTransaction
from backend.models.analytics import SpendingCategory, SpendingPattern
from backend.services.subscription_tier_service import SubscriptionTierService, SubscriptionTier, FeatureType
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class SpendingInsightType(Enum):
    """Types of spending insights"""
    SPENDING_TREND = "spending_trend"
    CATEGORY_BREAKDOWN = "category_breakdown"
    UNUSUAL_SPENDING = "unusual_spending"
    RECURRING_EXPENSES = "recurring_expenses"
    SAVINGS_OPPORTUNITY = "savings_opportunity"
    BUDGET_ALERT = "budget_alert"


class GoalStatus(Enum):
    """Savings goal status"""
    ON_TRACK = "on_track"
    BEHIND = "behind"
    AHEAD = "ahead"
    COMPLETED = "completed"
    NOT_STARTED = "not_started"


class GoalType(Enum):
    """Types of savings goals"""
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    DOWN_PAYMENT = "down_payment"
    RETIREMENT = "retirement"
    EDUCATION = "education"
    CUSTOM = "custom"


@dataclass
class SpendingInsight:
    """Basic spending insight for Mid-tier users"""
    insight_id: str
    user_id: int
    insight_type: SpendingInsightType
    title: str
    description: str
    data: Dict[str, Any]
    impact_score: float  # 0-1 scale
    priority: str  # low, medium, high
    is_actionable: bool
    action_description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SavingsGoal:
    """Savings goal for Mid-tier users"""
    goal_id: str
    user_id: int
    goal_name: str
    goal_type: GoalType
    target_amount: float
    current_amount: float
    target_date: datetime
    monthly_target: float
    status: GoalStatus
    progress_percentage: float
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StandardCategorization:
    """Standard categorization result for Mid-tier users"""
    transaction_id: str
    user_id: int
    original_category: str
    suggested_category: str
    confidence_score: float
    categorization_method: str
    reasoning: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CashFlowForecast6Month:
    """6-month cash flow forecast for Mid-tier users"""
    forecast_id: str
    user_id: int
    forecast_period: int = 6  # Fixed at 6 months for Mid-tier
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=180))
    
    # Monthly forecasts
    monthly_forecasts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Summary data
    projected_income: float = 0.0
    projected_expenses: float = 0.0
    projected_cash_flow: float = 0.0
    cash_flow_trend: str = "stable"
    
    # Model information
    model_version: str = "1.0"
    accuracy_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class MidTierFeaturesService:
    """
    Service for Mid-tier subscription features including standard categorization,
    basic spending insights, 6-month cash flow forecasting, and savings goal tracking.
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        self.tier_service = SubscriptionTierService(db_session)
        
        # Initialize Mid-tier specific parameters
        self._initialize_mid_tier_parameters()
    
    def _initialize_mid_tier_parameters(self):
        """Initialize Mid-tier specific parameters"""
        self.mid_tier_params = {
            'categorization': {
                'confidence_threshold': 0.6,
                'max_suggestions': 3,
                'methods': ['merchant_pattern', 'amount_heuristic', 'basic_ml']
            },
            'insights': {
                'min_transactions_for_insight': 5,
                'insight_generation_frequency': 'weekly',
                'max_insights_per_user': 10
            },
            'forecasting': {
                'forecast_months': 6,
                'min_data_points': 3,
                'confidence_level': 0.8
            },
            'savings_goals': {
                'max_goals_per_user': 5,
                'min_monthly_target': 10.0,
                'goal_update_frequency': 'daily'
            }
        }
    
    def apply_standard_categorization(self, user_id: int, transactions: List[PlaidTransaction]) -> List[StandardCategorization]:
        """Apply standard categorization to transactions for Mid-tier users"""
        if not self.tier_service.has_feature_access(user_id, FeatureType.STANDARD_CATEGORIZATION):
            raise ValueError("User does not have access to standard categorization")
        
        results = []
        
        for transaction in transactions:
            # Apply standard categorization logic
            suggested_category, confidence, method, reasoning = self._categorize_standard(transaction)
            
            result = StandardCategorization(
                transaction_id=transaction.transaction_id,
                user_id=user_id,
                original_category=transaction.category or "uncategorized",
                suggested_category=suggested_category,
                confidence_score=confidence,
                categorization_method=method,
                reasoning=reasoning
            )
            
            results.append(result)
            
            # Auto-apply high-confidence categorizations
            if confidence >= self.mid_tier_params['categorization']['confidence_threshold']:
                transaction.category = suggested_category
                self.logger.info(f"Auto-applied standard categorization: {transaction.transaction_id} -> {suggested_category}")
        
        return results
    
    def _categorize_standard(self, transaction: PlaidTransaction) -> Tuple[str, float, str, str]:
        """Apply standard categorization to a single transaction"""
        merchant_name = transaction.merchant_name or transaction.name or ""
        amount = abs(float(transaction.amount))
        
        # Standard merchant pattern matching
        standard_patterns = {
            'food_dining': ['restaurant', 'cafe', 'dining', 'food', 'pizza', 'burger', 'coffee'],
            'transportation': ['uber', 'lyft', 'taxi', 'gas', 'fuel', 'parking', 'transit'],
            'shopping': ['amazon', 'walmart', 'target', 'costco', 'shop', 'store'],
            'entertainment': ['netflix', 'spotify', 'movie', 'theater', 'concert', 'game'],
            'utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'cable'],
            'healthcare': ['doctor', 'pharmacy', 'medical', 'dental', 'vision', 'hospital']
        }
        
        # Find matching patterns
        best_match = "other"
        best_confidence = 0.0
        
        for category, patterns in standard_patterns.items():
            for pattern in patterns:
                if pattern.lower() in merchant_name.lower():
                    confidence = len(pattern) / len(merchant_name) if merchant_name else 0
                    if confidence > best_confidence:
                        best_match = category
                        best_confidence = confidence
        
        # Basic amount heuristics
        if amount > 500:
            if best_confidence < 0.3:
                best_match = "large_purchase"
                best_confidence = 0.7
        
        return (
            best_match,
            min(best_confidence, 0.9),
            "merchant_pattern_matching",
            f"Matched '{merchant_name}' to {best_match} category"
        )
    
    def generate_basic_spending_insights(self, user_id: int, date_range: Optional[Tuple[datetime, datetime]] = None) -> List[SpendingInsight]:
        """Generate basic spending insights for Mid-tier users"""
        if not self.tier_service.has_feature_access(user_id, FeatureType.BASIC_ANALYTICS):
            raise ValueError("User does not have access to basic analytics")
        
        # Get user transactions
        transactions = self._get_user_transactions(user_id, date_range)
        
        if len(transactions) < self.mid_tier_params['insights']['min_transactions_for_insight']:
            return []
        
        insights = []
        
        # Generate different types of insights
        insights.extend(self._generate_spending_trend_insights(transactions, user_id))
        insights.extend(self._generate_category_breakdown_insights(transactions, user_id))
        insights.extend(self._generate_unusual_spending_insights(transactions, user_id))
        insights.extend(self._generate_recurring_expenses_insights(transactions, user_id))
        insights.extend(self._generate_savings_opportunity_insights(transactions, user_id))
        
        # Limit insights per user
        max_insights = self.mid_tier_params['insights']['max_insights_per_user']
        insights = sorted(insights, key=lambda x: x.impact_score, reverse=True)[:max_insights]
        
        return insights
    
    def _get_user_transactions(self, user_id: int, date_range: Optional[Tuple[datetime, datetime]] = None) -> List[PlaidTransaction]:
        """Get user transactions for analysis"""
        query = self.db_session.query(PlaidTransaction).filter(
            PlaidTransaction.user_id == user_id
        )
        
        if date_range:
            start_date, end_date = date_range
            query = query.filter(
                PlaidTransaction.date.between(start_date, end_date)
            )
        else:
            # Default to last 3 months
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            query = query.filter(
                PlaidTransaction.date.between(start_date, end_date)
            )
        
        return query.all()
    
    def _generate_spending_trend_insights(self, transactions: List[PlaidTransaction], user_id: int) -> List[SpendingInsight]:
        """Generate spending trend insights"""
        insights = []
        
        # Calculate monthly spending trends
        monthly_spending = defaultdict(float)
        for tx in transactions:
            month_key = tx.date.strftime('%Y-%m')
            monthly_spending[month_key] += abs(float(tx.amount))
        
        if len(monthly_spending) >= 2:
            months = sorted(monthly_spending.keys())
            recent_months = months[-2:]
            
            current_month = monthly_spending[recent_months[-1]]
            previous_month = monthly_spending[recent_months[-2]]
            
            if previous_month > 0:
                change_percentage = ((current_month - previous_month) / previous_month) * 100
                
                if change_percentage > 20:
                    insights.append(SpendingInsight(
                        insight_id=f"trend_{user_id}_{datetime.now().timestamp()}",
                        user_id=user_id,
                        insight_type=SpendingInsightType.SPENDING_TREND,
                        title="Spending Increase Detected",
                        description=f"Your spending increased by {change_percentage:.1f}% this month compared to last month.",
                        data={
                            'current_month': current_month,
                            'previous_month': previous_month,
                            'change_percentage': change_percentage
                        },
                        impact_score=0.7,
                        priority="medium",
                        is_actionable=True,
                        action_description="Review your recent transactions to identify areas where you can reduce spending."
                    ))
                elif change_percentage < -20:
                    insights.append(SpendingInsight(
                        insight_id=f"trend_{user_id}_{datetime.now().timestamp()}",
                        user_id=user_id,
                        insight_type=SpendingInsightType.SPENDING_TREND,
                        title="Spending Decrease Detected",
                        description=f"Great job! Your spending decreased by {abs(change_percentage):.1f}% this month.",
                        data={
                            'current_month': current_month,
                            'previous_month': previous_month,
                            'change_percentage': change_percentage
                        },
                        impact_score=0.5,
                        priority="low",
                        is_actionable=False
                    ))
        
        return insights
    
    def _generate_category_breakdown_insights(self, transactions: List[PlaidTransaction], user_id: int) -> List[SpendingInsight]:
        """Generate category breakdown insights"""
        insights = []
        
        # Calculate category spending
        category_spending = defaultdict(float)
        for tx in transactions:
            category = tx.category or "uncategorized"
            category_spending[category] += abs(float(tx.amount))
        
        total_spending = sum(category_spending.values())
        
        if total_spending > 0:
            # Find highest spending category
            highest_category = max(category_spending.items(), key=lambda x: x[1])
            category_name, category_amount = highest_category
            category_percentage = (category_amount / total_spending) * 100
            
            if category_percentage > 40:
                insights.append(SpendingInsight(
                    insight_id=f"category_{user_id}_{datetime.now().timestamp()}",
                    user_id=user_id,
                    insight_type=SpendingInsightType.CATEGORY_BREAKDOWN,
                    title=f"High Spending in {category_name.title()}",
                    description=f"{category_name.title()} accounts for {category_percentage:.1f}% of your total spending.",
                    data={
                        'category': category_name,
                        'amount': category_amount,
                        'percentage': category_percentage,
                        'total_spending': total_spending
                    },
                    impact_score=0.6,
                    priority="medium",
                    is_actionable=True,
                    action_description=f"Consider setting a budget for {category_name} to better control your spending."
                ))
        
        return insights
    
    def _generate_unusual_spending_insights(self, transactions: List[PlaidTransaction], user_id: int) -> List[SpendingInsight]:
        """Generate unusual spending insights"""
        insights = []
        
        # Find unusually large transactions
        amounts = [abs(float(tx.amount)) for tx in transactions]
        if amounts:
            mean_amount = sum(amounts) / len(amounts)
            std_dev = math.sqrt(sum((x - mean_amount) ** 2 for x in amounts) / len(amounts))
            
            for tx in transactions:
                amount = abs(float(tx.amount))
                if amount > mean_amount + (2 * std_dev):  # 2 standard deviations above mean
                    insights.append(SpendingInsight(
                        insight_id=f"unusual_{user_id}_{datetime.now().timestamp()}",
                        user_id=user_id,
                        insight_type=SpendingInsightType.UNUSUAL_SPENDING,
                        title="Unusual Transaction Detected",
                        description=f"Transaction of ${amount:.2f} to {tx.merchant_name or tx.name} is unusually large.",
                        data={
                            'transaction_id': tx.transaction_id,
                            'amount': amount,
                            'merchant': tx.merchant_name or tx.name,
                            'date': tx.date.isoformat(),
                            'mean_amount': mean_amount,
                            'std_dev': std_dev
                        },
                        impact_score=0.8,
                        priority="high",
                        is_actionable=True,
                        action_description="Review this transaction to ensure it's legitimate and within your budget."
                    ))
        
        return insights
    
    def _generate_recurring_expenses_insights(self, transactions: List[PlaidTransaction], user_id: int) -> List[SpendingInsight]:
        """Generate recurring expenses insights"""
        insights = []
        
        # Group transactions by merchant
        merchant_transactions = defaultdict(list)
        for tx in transactions:
            merchant = tx.merchant_name or tx.name
            if merchant:
                merchant_transactions[merchant].append(tx)
        
        # Find potential recurring expenses
        for merchant, txs in merchant_transactions.items():
            if len(txs) >= 2:
                # Check if transactions are roughly the same amount
                amounts = [abs(float(tx.amount)) for tx in txs]
                if len(set(amounts)) <= 2:  # Only 1-2 different amounts
                    avg_amount = sum(amounts) / len(amounts)
                    insights.append(SpendingInsight(
                        insight_id=f"recurring_{user_id}_{datetime.now().timestamp()}",
                        user_id=user_id,
                        insight_type=SpendingInsightType.RECURRING_EXPENSES,
                        title=f"Potential Recurring Expense: {merchant}",
                        description=f"You've made {len(txs)} transactions to {merchant} averaging ${avg_amount:.2f}.",
                        data={
                            'merchant': merchant,
                            'transaction_count': len(txs),
                            'average_amount': avg_amount,
                            'total_amount': sum(amounts)
                        },
                        impact_score=0.5,
                        priority="low",
                        is_actionable=True,
                        action_description="Consider setting up a budget category for this recurring expense."
                    ))
        
        return insights
    
    def _generate_savings_opportunity_insights(self, transactions: List[PlaidTransaction], user_id: int) -> List[SpendingInsight]:
        """Generate savings opportunity insights"""
        insights = []
        
        # Find potential savings opportunities
        category_spending = defaultdict(float)
        for tx in transactions:
            category = tx.category or "uncategorized"
            category_spending[category] += abs(float(tx.amount))
        
        # Look for high-spending categories that might have savings opportunities
        high_spending_categories = ['food_dining', 'entertainment', 'shopping']
        
        for category in high_spending_categories:
            if category in category_spending:
                amount = category_spending[category]
                if amount > 200:  # High spending threshold
                    insights.append(SpendingInsight(
                        insight_id=f"savings_{user_id}_{datetime.now().timestamp()}",
                        user_id=user_id,
                        insight_type=SpendingInsightType.SAVINGS_OPPORTUNITY,
                        title=f"Savings Opportunity in {category.replace('_', ' ').title()}",
                        description=f"You've spent ${amount:.2f} on {category.replace('_', ' ')} this period.",
                        data={
                            'category': category,
                            'amount': amount,
                            'potential_savings': amount * 0.1  # 10% potential savings
                        },
                        impact_score=0.6,
                        priority="medium",
                        is_actionable=True,
                        action_description=f"Consider ways to reduce spending in {category.replace('_', ' ')} by 10-20%."
                    ))
        
        return insights
    
    def generate_6month_cash_flow_forecast(self, user_id: int) -> CashFlowForecast6Month:
        """Generate 6-month cash flow forecast for Mid-tier users"""
        if not self.tier_service.has_feature_access(user_id, FeatureType.CASH_FLOW_FORECASTING):
            raise ValueError("User does not have access to cash flow forecasting")
        
        # Get historical transaction data
        historical_data = self._get_historical_cash_flow_data(user_id)
        
        if len(historical_data) < self.mid_tier_params['forecasting']['min_data_points']:
            raise ValueError(f"Insufficient historical data for forecasting. Need at least {self.mid_tier_params['forecasting']['min_data_points']} months")
        
        # Generate 6-month forecast
        forecast = self._generate_6month_forecast(historical_data, user_id)
        
        return forecast
    
    def _get_historical_cash_flow_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Get historical cash flow data for forecasting"""
        # This would query the database for historical cash flow data
        # For now, return sample data
        return [
            {'month': '2024-01', 'income': 4000, 'expenses': 2800, 'cash_flow': 1200},
            {'month': '2024-02', 'income': 4200, 'expenses': 2900, 'cash_flow': 1300},
            {'month': '2024-03', 'income': 3800, 'expenses': 2700, 'cash_flow': 1100},
            {'month': '2024-04', 'income': 4100, 'expenses': 3000, 'cash_flow': 1100},
            {'month': '2024-05', 'income': 4300, 'expenses': 2800, 'cash_flow': 1500},
            {'month': '2024-06', 'income': 3900, 'expenses': 2600, 'cash_flow': 1300},
        ]
    
    def _generate_6month_forecast(self, historical_data: List[Dict[str, Any]], user_id: int) -> CashFlowForecast6Month:
        """Generate 6-month cash flow forecast"""
        # Calculate trends
        income_trend = self._calculate_trend([d['income'] for d in historical_data])
        expense_trend = self._calculate_trend([d['expenses'] for d in historical_data])
        
        # Generate monthly forecasts
        monthly_forecasts = []
        current_date = datetime.now()
        base_income = historical_data[-1]['income']
        base_expenses = historical_data[-1]['expenses']
        
        for month in range(1, 7):  # 6 months
            forecast_date = current_date + timedelta(days=30*month)
            
            # Project income and expenses
            projected_income = base_income * (1 + income_trend) ** month
            projected_expenses = base_expenses * (1 + expense_trend) ** month
            projected_cash_flow = projected_income - projected_expenses
            
            monthly_forecast = {
                'month': forecast_date.strftime('%Y-%m'),
                'projected_income': projected_income,
                'projected_expenses': projected_expenses,
                'projected_cash_flow': projected_cash_flow,
                'confidence_level': 0.8 - (month * 0.05)  # Decreasing confidence over time
            }
            
            monthly_forecasts.append(monthly_forecast)
        
        # Calculate summary data
        total_projected_income = sum(f['projected_income'] for f in monthly_forecasts)
        total_projected_expenses = sum(f['projected_expenses'] for f in monthly_forecasts)
        total_projected_cash_flow = sum(f['projected_cash_flow'] for f in monthly_forecasts)
        
        # Determine cash flow trend
        if total_projected_cash_flow > 0:
            cash_flow_trend = "positive"
        elif total_projected_cash_flow < 0:
            cash_flow_trend = "negative"
        else:
            cash_flow_trend = "stable"
        
        return CashFlowForecast6Month(
            forecast_id=f"forecast_6m_{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            start_date=current_date,
            end_date=current_date + timedelta(days=180),
            monthly_forecasts=monthly_forecasts,
            projected_income=total_projected_income,
            projected_expenses=total_projected_expenses,
            projected_cash_flow=total_projected_cash_flow,
            cash_flow_trend=cash_flow_trend,
            model_version="1.0",
            accuracy_score=0.75,
            last_updated=datetime.now()
        )
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend (growth rate) from a list of values"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * val for i, val in enumerate(values))
        x_squared_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x_squared_sum - x_sum * x_sum)
        
        # Convert to growth rate
        if values[0] != 0:
            growth_rate = slope / values[0]
        else:
            growth_rate = 0.0
        
        return growth_rate
    
    def create_savings_goal(self, user_id: int, goal_data: Dict[str, Any]) -> SavingsGoal:
        """Create a savings goal for Mid-tier users"""
        # Check if user has reached goal limit
        current_goals = self._get_user_savings_goals(user_id)
        max_goals = self.mid_tier_params['savings_goals']['max_goals_per_user']
        
        if len(current_goals) >= max_goals:
            raise ValueError(f"User has reached the limit of {max_goals} savings goals")
        
        # Validate goal data
        self._validate_savings_goal_data(goal_data)
        
        # Calculate monthly target
        target_amount = goal_data['target_amount']
        target_date = datetime.fromisoformat(goal_data['target_date'])
        months_until_target = max(1, (target_date - datetime.now()).days / 30.44)
        monthly_target = target_amount / months_until_target
        
        # Validate monthly target
        min_monthly_target = self.mid_tier_params['savings_goals']['min_monthly_target']
        if monthly_target < min_monthly_target:
            raise ValueError(f"Monthly target (${monthly_target:.2f}) is below minimum (${min_monthly_target:.2f})")
        
        # Create goal
        goal = SavingsGoal(
            goal_id=f"goal_{user_id}_{datetime.now().timestamp()}",
            user_id=user_id,
            goal_name=goal_data['name'],
            goal_type=GoalType(goal_data['goal_type']),
            target_amount=target_amount,
            current_amount=goal_data.get('current_amount', 0.0),
            target_date=target_date,
            monthly_target=monthly_target,
            status=GoalStatus.NOT_STARTED,
            progress_percentage=0.0,
            metadata=goal_data.get('metadata', {})
        )
        
        # Update status and progress
        self._update_goal_status_and_progress(goal)
        
        return goal
    
    def _validate_savings_goal_data(self, goal_data: Dict[str, Any]):
        """Validate savings goal data"""
        required_fields = ['name', 'goal_type', 'target_amount', 'target_date']
        for field in required_fields:
            if field not in goal_data:
                raise ValueError(f"Missing required field: {field}")
        
        if goal_data['target_amount'] <= 0:
            raise ValueError("Target amount must be positive")
        
        target_date = datetime.fromisoformat(goal_data['target_date'])
        if target_date <= datetime.now():
            raise ValueError("Target date must be in the future")
    
    def _get_user_savings_goals(self, user_id: int) -> List[SavingsGoal]:
        """Get user's savings goals"""
        # This would query the database for user's savings goals
        # For now, return empty list
        return []
    
    def _update_goal_status_and_progress(self, goal: SavingsGoal):
        """Update goal status and progress percentage"""
        if goal.current_amount >= goal.target_amount:
            goal.status = GoalStatus.COMPLETED
            goal.progress_percentage = 100.0
        else:
            goal.progress_percentage = (goal.current_amount / goal.target_amount) * 100
            
            # Calculate expected progress
            months_elapsed = max(0, (datetime.now() - goal.created_at).days / 30.44)
            expected_amount = months_elapsed * goal.monthly_target
            expected_progress = (expected_amount / goal.target_amount) * 100
            
            if goal.progress_percentage >= expected_progress + 10:
                goal.status = GoalStatus.AHEAD
            elif goal.progress_percentage >= expected_progress - 10:
                goal.status = GoalStatus.ON_TRACK
            else:
                goal.status = GoalStatus.BEHIND
    
    def update_savings_goal_progress(self, goal_id: str, new_amount: float) -> SavingsGoal:
        """Update savings goal progress"""
        # This would update the goal in the database
        # For now, return a mock updated goal
        goal = SavingsGoal(
            goal_id=goal_id,
            user_id=1,
            goal_name="Emergency Fund",
            goal_type=GoalType.EMERGENCY_FUND,
            target_amount=10000.0,
            current_amount=new_amount,
            target_date=datetime.now() + timedelta(days=365),
            monthly_target=833.33,
            status=GoalStatus.ON_TRACK,
            progress_percentage=(new_amount / 10000.0) * 100
        )
        
        self._update_goal_status_and_progress(goal)
        return goal
    
    def get_savings_goals_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary of user's savings goals"""
        goals = self._get_user_savings_goals(user_id)
        
        if not goals:
            return {
                'total_goals': 0,
                'total_target_amount': 0.0,
                'total_current_amount': 0.0,
                'overall_progress': 0.0,
                'goals_by_status': {},
                'recommendations': []
            }
        
        total_target = sum(goal.target_amount for goal in goals)
        total_current = sum(goal.current_amount for goal in goals)
        overall_progress = (total_current / total_target) * 100 if total_target > 0 else 0
        
        goals_by_status = defaultdict(list)
        for goal in goals:
            goals_by_status[goal.status.value].append({
                'goal_id': goal.goal_id,
                'goal_name': goal.goal_name,
                'progress_percentage': goal.progress_percentage
            })
        
        # Generate recommendations
        recommendations = []
        if overall_progress < 50:
            recommendations.append("Consider increasing your monthly savings contributions")
        if len([g for g in goals if g.status == GoalStatus.BEHIND]) > 0:
            recommendations.append("Review goals that are behind schedule and adjust your strategy")
        
        return {
            'total_goals': len(goals),
            'total_target_amount': total_target,
            'total_current_amount': total_current,
            'overall_progress': overall_progress,
            'goals_by_status': dict(goals_by_status),
            'recommendations': recommendations
        } 