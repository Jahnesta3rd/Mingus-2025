"""
Budget Tier Service for MINGUS

This module provides comprehensive Budget tier functionality including:
- Manual transaction entry
- Basic expense tracking
- 1-month cash flow forecasting
- Upgrade prompts with banking insights
"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, sum, case, when
from sqlalchemy.exc import SQLAlchemyError

from backend.models.plaid_models import PlaidTransaction
from backend.models.subscription import Subscription, PricingTier, FeatureUsage
from backend.models.analytics import TransactionInsight, SpendingCategory
from backend.services.tier_access_control_service import TierAccessControlService
from backend.services.notification_service import NotificationService
from backend.utils.encryption import encrypt_data, decrypt_data
from backend.utils.validation import validate_amount, validate_date

logger = logging.getLogger(__name__)


class TransactionEntryType(Enum):
    """Manual transaction entry types"""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"


class ExpenseCategory(Enum):
    """Basic expense categories for Budget tier"""
    FOOD_DINING = "food_dining"
    TRANSPORTATION = "transportation"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    UTILITIES = "utilities"
    HOUSING = "housing"
    INSURANCE = "insurance"
    EDUCATION = "education"
    TRAVEL = "travel"
    SUBSCRIPTIONS = "subscriptions"
    PERSONAL_CARE = "personal_care"
    GIFTS = "gifts"
    CHARITY = "charity"
    OTHER = "other"


@dataclass
class ManualTransaction:
    """Manual transaction entry data structure"""
    id: str
    user_id: str
    name: str
    amount: Decimal
    entry_type: TransactionEntryType
    category: ExpenseCategory
    date: date
    description: Optional[str] = None
    merchant_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_recurring: bool = False
    recurring_frequency: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExpenseSummary:
    """Basic expense tracking summary"""
    total_expenses: Decimal
    total_income: Decimal
    net_amount: Decimal
    category_breakdown: Dict[str, Decimal]
    monthly_trend: str  # "increasing", "decreasing", "stable"
    top_categories: List[Tuple[str, Decimal]]
    average_daily_spending: Decimal
    days_tracked: int


@dataclass
class CashFlowForecast:
    """1-month cash flow forecast for Budget tier"""
    forecast_start_date: date
    forecast_end_date: date
    opening_balance: Decimal
    projected_income: Decimal
    projected_expenses: Decimal
    closing_balance: Decimal
    daily_balances: List[Dict[str, Any]]
    risk_dates: List[date]
    recommendations: List[str]
    confidence_score: float


@dataclass
class UpgradeInsight:
    """Banking insights for upgrade prompts"""
    insight_type: str
    title: str
    description: str
    potential_savings: Optional[Decimal]
    data_points: List[str]
    upgrade_benefits: List[str]
    urgency_level: str  # "low", "medium", "high"


class BudgetTierService:
    """Service for Budget tier functionality"""
    
    def __init__(self, db_session: Session, tier_service: TierAccessControlService, 
                 notification_service: NotificationService):
        self.db_session = db_session
        self.tier_service = tier_service
        self.notification_service = notification_service
        
        # Budget tier limits
        self.max_manual_transactions_per_month = 100
        self.max_cash_flow_forecasts_per_month = 2
        self.max_expense_categories = 15
        
    def add_manual_transaction(self, user_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a manual transaction entry for Budget tier users
        
        Args:
            user_id: User ID
            transaction_data: Transaction data dictionary
            
        Returns:
            Result dictionary with success status and transaction details
        """
        try:
            # Check if user is on Budget tier
            user_tier = self.tier_service.get_user_tier(user_id)
            if user_tier.value != 'budget':
                return {
                    'success': False,
                    'error': 'Manual transaction entry is only available for Budget tier users',
                    'upgrade_required': True
                }
            
            # Validate transaction data
            validation_result = self._validate_transaction_data(transaction_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error']
                }
            
            # Check monthly transaction limit
            monthly_count = self._get_monthly_transaction_count(user_id)
            if monthly_count >= self.max_manual_transactions_per_month:
                return {
                    'success': False,
                    'error': f'Monthly transaction limit reached ({self.max_manual_transactions_per_month})',
                    'upgrade_required': True,
                    'upgrade_prompt': self._generate_upgrade_prompt('transaction_limit')
                }
            
            # Create manual transaction
            transaction = ManualTransaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=transaction_data['name'],
                amount=Decimal(str(transaction_data['amount'])),
                entry_type=TransactionEntryType(transaction_data['entry_type']),
                category=ExpenseCategory(transaction_data['category']),
                date=datetime.strptime(transaction_data['date'], '%Y-%m-%d').date(),
                description=transaction_data.get('description'),
                merchant_name=transaction_data.get('merchant_name'),
                tags=transaction_data.get('tags', []),
                is_recurring=transaction_data.get('is_recurring', False),
                recurring_frequency=transaction_data.get('recurring_frequency')
            )
            
            # Save to database
            self._save_manual_transaction(transaction)
            
            # Track usage
            self._track_transaction_usage(user_id)
            
            # Generate insights if this is a significant transaction
            insights = self._generate_transaction_insights(transaction)
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'transaction': transaction.__dict__,
                'insights': insights,
                'monthly_usage': {
                    'transactions_used': monthly_count + 1,
                    'transactions_limit': self.max_manual_transactions_per_month
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding manual transaction for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to add transaction. Please try again.'
            }
    
    def get_expense_summary(self, user_id: str, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """
        Get basic expense tracking summary for Budget tier users
        
        Args:
            user_id: User ID
            start_date: Start date for summary (defaults to current month)
            end_date: End date for summary (defaults to current month)
            
        Returns:
            Expense summary dictionary
        """
        try:
            # Set default date range to current month
            if not start_date:
                start_date = date.today().replace(day=1)
            if not end_date:
                end_date = date.today()
            
            # Get manual transactions for the period
            transactions = self._get_manual_transactions(user_id, start_date, end_date)
            
            # Calculate summary
            total_expenses = sum(t.amount for t in transactions if t.entry_type == TransactionEntryType.EXPENSE)
            total_income = sum(t.amount for t in transactions if t.entry_type == TransactionEntryType.INCOME)
            net_amount = total_income - total_expenses
            
            # Category breakdown
            category_breakdown = {}
            for transaction in transactions:
                if transaction.entry_type == TransactionEntryType.EXPENSE:
                    category = transaction.category.value
                    category_breakdown[category] = category_breakdown.get(category, Decimal('0')) + transaction.amount
            
            # Top categories
            top_categories = sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Calculate average daily spending
            days_tracked = (end_date - start_date).days + 1
            average_daily_spending = total_expenses / days_tracked if days_tracked > 0 else Decimal('0')
            
            # Determine monthly trend
            monthly_trend = self._calculate_monthly_trend(user_id)
            
            summary = ExpenseSummary(
                total_expenses=total_expenses,
                total_income=total_income,
                net_amount=net_amount,
                category_breakdown=category_breakdown,
                monthly_trend=monthly_trend,
                top_categories=top_categories,
                average_daily_spending=average_daily_spending,
                days_tracked=days_tracked
            )
            
            # Generate upgrade insights
            upgrade_insights = self._generate_expense_upgrade_insights(summary)
            
            return {
                'success': True,
                'summary': summary.__dict__,
                'upgrade_insights': [insight.__dict__ for insight in upgrade_insights],
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting expense summary for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to generate expense summary'
            }
    
    def generate_cash_flow_forecast(self, user_id: str, opening_balance: Decimal = None) -> Dict[str, Any]:
        """
        Generate 1-month cash flow forecast for Budget tier users
        
        Args:
            user_id: User ID
            opening_balance: Starting balance (optional)
            
        Returns:
            Cash flow forecast dictionary
        """
        try:
            # Check if user is on Budget tier
            user_tier = self.tier_service.get_user_tier(user_id)
            if user_tier.value != 'budget':
                return {
                    'success': False,
                    'error': 'Cash flow forecasting is only available for Budget tier users',
                    'upgrade_required': True
                }
            
            # Check monthly forecast limit
            monthly_count = self._get_monthly_forecast_count(user_id)
            if monthly_count >= self.max_cash_flow_forecasts_per_month:
                return {
                    'success': False,
                    'error': f'Monthly forecast limit reached ({self.max_cash_flow_forecasts_per_month})',
                    'upgrade_required': True,
                    'upgrade_prompt': self._generate_upgrade_prompt('forecast_limit')
                }
            
            # Set forecast period (next 30 days)
            forecast_start_date = date.today()
            forecast_end_date = forecast_start_date + timedelta(days=30)
            
            # Get opening balance or use default
            if not opening_balance:
                opening_balance = self._get_estimated_balance(user_id)
            
            # Get projected income and expenses
            projected_income = self._project_monthly_income(user_id)
            projected_expenses = self._project_monthly_expenses(user_id)
            
            # Calculate daily balances
            daily_balances = self._calculate_daily_balances(
                opening_balance, projected_income, projected_expenses, 
                forecast_start_date, forecast_end_date
            )
            
            # Identify risk dates (negative balance)
            risk_dates = [day['date'] for day in daily_balances if day['balance'] < 0]
            
            # Generate recommendations
            recommendations = self._generate_forecast_recommendations(
                opening_balance, projected_income, projected_expenses, risk_dates
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_forecast_confidence(user_id)
            
            forecast = CashFlowForecast(
                forecast_start_date=forecast_start_date,
                forecast_end_date=forecast_end_date,
                opening_balance=opening_balance,
                projected_income=projected_income,
                projected_expenses=projected_expenses,
                closing_balance=daily_balances[-1]['balance'] if daily_balances else opening_balance,
                daily_balances=daily_balances,
                risk_dates=risk_dates,
                recommendations=recommendations,
                confidence_score=confidence_score
            )
            
            # Track usage
            self._track_forecast_usage(user_id)
            
            # Generate upgrade insights
            upgrade_insights = self._generate_forecast_upgrade_insights(forecast)
            
            return {
                'success': True,
                'forecast': forecast.__dict__,
                'upgrade_insights': [insight.__dict__ for insight in upgrade_insights],
                'monthly_usage': {
                    'forecasts_used': monthly_count + 1,
                    'forecasts_limit': self.max_cash_flow_forecasts_per_month
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating cash flow forecast for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to generate cash flow forecast'
            }
    
    def get_upgrade_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get banking insights for upgrade prompts
        
        Args:
            user_id: User ID
            
        Returns:
            Upgrade insights dictionary
        """
        try:
            # Check if user is on Budget tier
            user_tier = self.tier_service.get_user_tier(user_id)
            if user_tier.value != 'budget':
                return {
                    'success': False,
                    'error': 'Upgrade insights are only available for Budget tier users'
                }
            
            insights = []
            
            # Analyze spending patterns
            spending_insight = self._analyze_spending_patterns(user_id)
            if spending_insight:
                insights.append(spending_insight)
            
            # Analyze recurring expenses
            recurring_insight = self._analyze_recurring_expenses(user_id)
            if recurring_insight:
                insights.append(recurring_insight)
            
            # Analyze category optimization
            category_insight = self._analyze_category_optimization(user_id)
            if category_insight:
                insights.append(category_insight)
            
            # Analyze cash flow patterns
            cash_flow_insight = self._analyze_cash_flow_patterns(user_id)
            if cash_flow_insight:
                insights.append(cash_flow_insight)
            
            return {
                'success': True,
                'insights': [insight.__dict__ for insight in insights],
                'upgrade_benefits': self._get_upgrade_benefits(),
                'tier_comparison': self._get_tier_comparison()
            }
            
        except Exception as e:
            logger.error(f"Error getting upgrade insights for user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to generate upgrade insights'
            }
    
    def _validate_transaction_data(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate manual transaction data"""
        required_fields = ['name', 'amount', 'entry_type', 'category', 'date']
        
        for field in required_fields:
            if field not in transaction_data:
                return {'valid': False, 'error': f'Missing required field: {field}'}
        
        # Validate amount
        try:
            amount = Decimal(str(transaction_data['amount']))
            if amount <= 0:
                return {'valid': False, 'error': 'Amount must be greater than 0'}
        except (ValueError, TypeError):
            return {'valid': False, 'error': 'Invalid amount format'}
        
        # Validate entry type
        try:
            TransactionEntryType(transaction_data['entry_type'])
        except ValueError:
            return {'valid': False, 'error': 'Invalid entry type'}
        
        # Validate category
        try:
            ExpenseCategory(transaction_data['category'])
        except ValueError:
            return {'valid': False, 'error': 'Invalid category'}
        
        # Validate date
        try:
            datetime.strptime(transaction_data['date'], '%Y-%m-%d')
        except ValueError:
            return {'valid': False, 'error': 'Invalid date format (use YYYY-MM-DD)'}
        
        return {'valid': True}
    
    def _save_manual_transaction(self, transaction: ManualTransaction):
        """Save manual transaction to database"""
        # This would typically save to a manual_transactions table
        # For now, we'll simulate saving
        logger.info(f"Saving manual transaction: {transaction.id} for user {transaction.user_id}")
    
    def _get_manual_transactions(self, user_id: str, start_date: date, end_date: date) -> List[ManualTransaction]:
        """Get manual transactions for a user within a date range"""
        # This would typically query the manual_transactions table
        # For now, return empty list as placeholder
        return []
    
    def _get_monthly_transaction_count(self, user_id: str) -> int:
        """Get monthly transaction count for user"""
        # This would typically query the database
        # For now, return 0 as placeholder
        return 0
    
    def _track_transaction_usage(self, user_id: str):
        """Track transaction usage for the user"""
        # This would typically update usage tracking
        logger.info(f"Tracking transaction usage for user {user_id}")
    
    def _generate_transaction_insights(self, transaction: ManualTransaction) -> List[str]:
        """Generate insights for a transaction"""
        insights = []
        
        # Large transaction insight
        if transaction.amount > Decimal('100'):
            insights.append(f"Large {transaction.entry_type.value} transaction detected")
        
        # Category spending insight
        if transaction.entry_type == TransactionEntryType.EXPENSE:
            insights.append(f"Added to {transaction.category.value} category")
        
        # Recurring transaction insight
        if transaction.is_recurring:
            insights.append("Recurring transaction detected")
        
        return insights
    
    def _calculate_monthly_trend(self, user_id: str) -> str:
        """Calculate monthly spending trend"""
        # This would typically analyze historical data
        # For now, return stable as placeholder
        return "stable"
    
    def _generate_expense_upgrade_insights(self, summary: ExpenseSummary) -> List[UpgradeInsight]:
        """Generate upgrade insights based on expense summary"""
        insights = []
        
        # High spending insight
        if summary.total_expenses > Decimal('2000'):
            insights.append(UpgradeInsight(
                insight_type="high_spending",
                title="High Monthly Spending Detected",
                description=f"Your monthly spending of ${summary.total_expenses} suggests you could benefit from advanced budgeting tools.",
                potential_savings=summary.total_expenses * Decimal('0.1'),  # 10% potential savings
                data_points=[f"Monthly spending: ${summary.total_expenses}"],
                upgrade_benefits=["Advanced budgeting tools", "Spending alerts", "Category optimization"],
                urgency_level="medium"
            ))
        
        # Category optimization insight
        if len(summary.top_categories) > 0:
            top_category = summary.top_categories[0]
            if top_category[1] > summary.total_expenses * Decimal('0.3'):  # More than 30%
                insights.append(UpgradeInsight(
                    insight_type="category_optimization",
                    title="Spending Concentration Detected",
                    description=f"Your {top_category[0]} spending represents {top_category[1]/summary.total_expenses*100:.1f}% of total expenses.",
                    potential_savings=top_category[1] * Decimal('0.15'),  # 15% potential savings
                    data_points=[f"{top_category[0]}: ${top_category[1]}"],
                    upgrade_benefits=["Detailed category analysis", "Spending optimization", "Alternative suggestions"],
                    urgency_level="low"
                ))
        
        return insights
    
    def _get_monthly_forecast_count(self, user_id: str) -> int:
        """Get monthly forecast count for user"""
        # This would typically query the database
        # For now, return 0 as placeholder
        return 0
    
    def _get_estimated_balance(self, user_id: str) -> Decimal:
        """Get estimated current balance for user"""
        # This would typically calculate from transactions
        # For now, return 1000 as placeholder
        return Decimal('1000')
    
    def _project_monthly_income(self, user_id: str) -> Decimal:
        """Project monthly income based on historical data"""
        # This would typically analyze historical income
        # For now, return 3000 as placeholder
        return Decimal('3000')
    
    def _project_monthly_expenses(self, user_id: str) -> Decimal:
        """Project monthly expenses based on historical data"""
        # This would typically analyze historical expenses
        # For now, return 2500 as placeholder
        return Decimal('2500')
    
    def _calculate_daily_balances(self, opening_balance: Decimal, projected_income: Decimal, 
                                 projected_expenses: Decimal, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Calculate daily balances for the forecast period"""
        daily_balances = []
        current_balance = opening_balance
        
        # Distribute income and expenses across the month
        daily_income = projected_income / 30
        daily_expenses = projected_expenses / 30
        
        current_date = start_date
        while current_date <= end_date:
            current_balance += daily_income - daily_expenses
            
            daily_balances.append({
                'date': current_date.isoformat(),
                'balance': float(current_balance),
                'income': float(daily_income),
                'expenses': float(daily_expenses)
            })
            
            current_date += timedelta(days=1)
        
        return daily_balances
    
    def _generate_forecast_recommendations(self, opening_balance: Decimal, projected_income: Decimal,
                                         projected_expenses: Decimal, risk_dates: List[date]) -> List[str]:
        """Generate recommendations based on forecast"""
        recommendations = []
        
        if projected_expenses > projected_income:
            recommendations.append("Consider reducing expenses to avoid negative cash flow")
        
        if risk_dates:
            recommendations.append(f"Monitor spending around {len(risk_dates)} potential risk dates")
        
        if opening_balance < projected_expenses * Decimal('0.5'):
            recommendations.append("Consider building emergency savings")
        
        return recommendations
    
    def _calculate_forecast_confidence(self, user_id: str) -> float:
        """Calculate confidence score for forecast"""
        # This would typically be based on data quality and consistency
        # For now, return 0.7 as placeholder
        return 0.7
    
    def _track_forecast_usage(self, user_id: str):
        """Track forecast usage for the user"""
        # This would typically update usage tracking
        logger.info(f"Tracking forecast usage for user {user_id}")
    
    def _generate_forecast_upgrade_insights(self, forecast: CashFlowForecast) -> List[UpgradeInsight]:
        """Generate upgrade insights based on forecast"""
        insights = []
        
        # Risk dates insight
        if forecast.risk_dates:
            insights.append(UpgradeInsight(
                insight_type="cash_flow_risk",
                title="Cash Flow Risk Detected",
                description=f"Your forecast shows {len(forecast.risk_dates)} potential negative balance dates.",
                potential_savings=forecast.projected_expenses * Decimal('0.05'),  # 5% potential savings
                data_points=[f"Risk dates: {len(forecast.risk_dates)}"],
                upgrade_benefits=["Advanced cash flow planning", "Real-time balance tracking", "Early warning alerts"],
                urgency_level="high" if len(forecast.risk_dates) > 5 else "medium"
            ))
        
        # Low confidence insight
        if forecast.confidence_score < 0.6:
            insights.append(UpgradeInsight(
                insight_type="low_confidence",
                title="Limited Data for Accurate Forecasting",
                description="Your forecast has low confidence due to limited transaction history.",
                potential_savings=None,
                data_points=[f"Confidence score: {forecast.confidence_score:.1%}"],
                upgrade_benefits=["Bank account linking", "Automatic transaction sync", "Enhanced forecasting"],
                urgency_level="low"
            ))
        
        return insights
    
    def _analyze_spending_patterns(self, user_id: str) -> Optional[UpgradeInsight]:
        """Analyze spending patterns for upgrade insights"""
        # This would typically analyze historical spending
        # For now, return None as placeholder
        return None
    
    def _analyze_recurring_expenses(self, user_id: str) -> Optional[UpgradeInsight]:
        """Analyze recurring expenses for upgrade insights"""
        # This would typically analyze recurring transactions
        # For now, return None as placeholder
        return None
    
    def _analyze_category_optimization(self, user_id: str) -> Optional[UpgradeInsight]:
        """Analyze category optimization for upgrade insights"""
        # This would typically analyze category spending
        # For now, return None as placeholder
        return None
    
    def _analyze_cash_flow_patterns(self, user_id: str) -> Optional[UpgradeInsight]:
        """Analyze cash flow patterns for upgrade insights"""
        # This would typically analyze cash flow history
        # For now, return None as placeholder
        return None
    
    def _get_upgrade_benefits(self) -> List[str]:
        """Get list of upgrade benefits"""
        return [
            "Unlimited bank account linking",
            "Automatic transaction sync",
            "Advanced analytics and insights",
            "Real-time balance tracking",
            "Custom spending alerts",
            "Detailed financial reports",
            "Priority customer support"
        ]
    
    def _get_tier_comparison(self) -> Dict[str, Any]:
        """Get tier comparison for upgrade prompts"""
        return {
            'budget': {
                'name': 'Budget',
                'price': '$15/month',
                'features': [
                    'Manual transaction entry',
                    'Basic expense tracking',
                    '1-month cash flow forecasting',
                    'Limited categories'
                ]
            },
            'mid_tier': {
                'name': 'Mid-Tier',
                'price': '$35/month',
                'features': [
                    'Bank account linking (2 accounts)',
                    'Automatic transaction sync',
                    '6-month cash flow forecasting',
                    'Advanced expense tracking',
                    'Spending insights'
                ]
            },
            'professional': {
                'name': 'Professional',
                'price': '$75/month',
                'features': [
                    'Unlimited bank accounts',
                    'Real-time sync',
                    '12-month cash flow forecasting',
                    'Advanced analytics',
                    'Custom integrations',
                    'Priority support'
                ]
            }
        }
    
    def _generate_upgrade_prompt(self, trigger: str) -> Dict[str, Any]:
        """Generate upgrade prompt based on trigger"""
        prompts = {
            'transaction_limit': {
                'title': 'Transaction Limit Reached',
                'message': 'You\'ve reached your monthly transaction limit. Upgrade to add unlimited transactions with automatic bank sync.',
                'benefits': ['Unlimited transactions', 'Automatic bank sync', 'Advanced categorization']
            },
            'forecast_limit': {
                'title': 'Forecast Limit Reached',
                'message': 'You\'ve reached your monthly forecast limit. Upgrade for unlimited cash flow forecasting.',
                'benefits': ['Unlimited forecasts', 'Longer forecast periods', 'Advanced projections']
            }
        }
        
        return prompts.get(trigger, {
            'title': 'Upgrade Available',
            'message': 'Upgrade to unlock more features and insights.',
            'benefits': ['More features', 'Better insights', 'Advanced tools']
        }) 