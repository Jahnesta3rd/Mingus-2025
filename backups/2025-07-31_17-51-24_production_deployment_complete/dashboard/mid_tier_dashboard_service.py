"""
Mid-Tier Dashboard Service

This module provides comprehensive dashboard features for Mid-tier subscription users,
including current balances for up to 2 accounts, 6-month cash flow projections,
standard spending categories and insights, savings goal progress tracking,
and basic bill tracking with key dates and reminders.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from collections import defaultdict, Counter
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text, case, cast, Float
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidAccount, PlaidTransaction
from backend.models.analytics import SpendingCategory, SpendingPattern
from backend.models.subscription import SubscriptionTier
from backend.services.feature_access_service import FeatureAccessService
from backend.services.mid_tier_features_service import MidTierFeaturesService
from backend.services.cash_flow_analysis_service import CashFlowAnalysisService
from backend.services.savings_goals_service import SavingsGoalsService
from backend.services.bill_tracking_service import BillTrackingService
from backend.services.real_time_updates_service import RealTimeUpdatesService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class DashboardWidgetType(Enum):
    """Dashboard widget types for Mid-tier"""
    ACCOUNT_BALANCES = "account_balances"
    CASH_FLOW_PROJECTION = "cash_flow_projection"
    SPENDING_CATEGORIES = "spending_categories"
    SAVINGS_GOALS = "savings_goals"
    BILL_TRACKING = "bill_tracking"
    KEY_DATES = "key_dates"
    SPENDING_INSIGHTS = "spending_insights"
    ALERTS = "alerts"


@dataclass
class AccountBalance:
    """Account balance data structure"""
    account_id: str
    account_name: str
    account_type: str
    institution_name: str
    current_balance: float
    available_balance: float
    last_updated: datetime
    currency: str = "USD"
    is_primary: bool = False


@dataclass
class CashFlowProjection:
    """6-month cash flow projection data"""
    month: str
    projected_income: float
    projected_expenses: float
    net_cash_flow: float
    confidence_level: float
    key_factors: List[str] = field(default_factory=list)


@dataclass
class SpendingCategoryInsight:
    """Spending category insight data"""
    category_name: str
    total_spent: float
    percentage_of_total: float
    transaction_count: int
    average_transaction: float
    trend: str  # 'increasing', 'decreasing', 'stable'
    trend_percentage: float
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SavingsGoalProgress:
    """Savings goal progress data"""
    goal_id: str
    goal_name: str
    target_amount: float
    current_amount: float
    progress_percentage: float
    monthly_target: float
    days_remaining: int
    status: str  # 'on_track', 'behind', 'ahead'
    next_milestone: Optional[str] = None


@dataclass
class BillReminder:
    """Bill reminder data"""
    bill_id: str
    bill_name: str
    due_date: date
    amount: float
    is_paid: bool
    days_until_due: int
    category: str
    priority: str  # 'high', 'medium', 'low'


@dataclass
class KeyDate:
    """Key date tracking data"""
    date_id: str
    title: str
    date: date
    category: str
    description: str
    days_until: int
    is_recurring: bool
    reminder_sent: bool


@dataclass
class RealTimeAlert:
    """Real-time alert data"""
    alert_id: str
    alert_type: str
    title: str
    message: str
    severity: str  # 'info', 'warning', 'critical'
    timestamp: datetime
    is_read: bool
    action_required: bool


class MidTierDashboardService:
    """Mid-tier dashboard service with comprehensive features"""
    
    def __init__(self, db_session: Session, feature_access_service: FeatureAccessService):
        self.db = db_session
        self.feature_service = feature_access_service
        self.mid_tier_service = MidTierFeaturesService(db_session)
        self.cash_flow_service = CashFlowAnalysisService(db_session)
        self.savings_service = SavingsGoalsService(db_session)
        self.bill_service = BillTrackingService(db_session)
        self.real_time_service = RealTimeUpdatesService(db_session)
        
        # Cache for real-time data
        self.balance_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def get_mid_tier_dashboard(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive Mid-tier dashboard data
        
        Args:
            user_id: User ID to get dashboard data for
            
        Returns:
            Complete Mid-tier dashboard data
        """
        try:
            # Verify Mid-tier access
            if not self._verify_mid_tier_access(user_id):
                return self._get_upgrade_prompt_data()
            
            # Get all dashboard components
            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'tier': 'mid_tier',
                'account_balances': self._get_current_account_balances(user_id),
                'cash_flow_projection': self._get_6_month_cash_flow_projection(user_id),
                'spending_categories': self._get_spending_categories_and_insights(user_id),
                'savings_goals': self._get_savings_goal_progress(user_id),
                'bill_tracking': self._get_bill_tracking_data(user_id),
                'key_dates': self._get_key_dates_and_reminders(user_id),
                'spending_insights': self._get_spending_insights(user_id),
                'alerts': self._get_real_time_alerts(user_id),
                'performance_metrics': self._get_performance_metrics(user_id)
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating Mid-tier dashboard for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _verify_mid_tier_access(self, user_id: str) -> bool:
        """Verify user has Mid-tier or higher access"""
        try:
            # Check if user has Mid-tier or Professional tier
            user_tier = self.feature_service.get_user_subscription_tier(user_id)
            return user_tier in ['mid_tier', 'professional']
        except Exception as e:
            logger.error(f"Error verifying Mid-tier access for user {user_id}: {e}")
            return False
    
    def _get_upgrade_prompt_data(self) -> Dict[str, Any]:
        """Get upgrade prompt data for non-Mid-tier users"""
        return {
            'error': 'upgrade_required',
            'message': 'Mid-tier dashboard features require Mid-tier or higher subscription',
            'upgrade_info': {
                'current_tier': 'budget',
                'required_tier': 'mid_tier',
                'features': [
                    'Current balances for up to 2 accounts',
                    '6-month cash flow projections',
                    'Standard spending categories and insights',
                    'Savings goal progress tracking',
                    'Basic bill tracking and key dates',
                    'Real-time updates and alerts'
                ],
                'upgrade_url': '/api/subscription/upgrade'
            }
        }
    
    def _get_current_account_balances(self, user_id: str) -> List[AccountBalance]:
        """Get current balances for up to 2 accounts"""
        try:
            # Get user's linked accounts (limited to 2 for Mid-tier)
            accounts = self.db.query(PlaidAccount).filter(
                and_(
                    PlaidAccount.user_id == user_id,
                    PlaidAccount.is_active == True
                )
            ).limit(2).all()
            
            balances = []
            for account in accounts:
                # Get latest balance from transactions or cached data
                latest_transaction = self.db.query(PlaidTransaction).filter(
                    PlaidTransaction.account_id == account.id
                ).order_by(desc(PlaidTransaction.date)).first()
                
                current_balance = latest_transaction.balance if latest_transaction else 0.0
                available_balance = current_balance  # Simplified for Mid-tier
                
                balance = AccountBalance(
                    account_id=account.id,
                    account_name=account.name,
                    account_type=account.type,
                    institution_name=account.institution_name,
                    current_balance=current_balance,
                    available_balance=available_balance,
                    last_updated=datetime.utcnow(),
                    is_primary=len(balances) == 0  # First account is primary
                )
                balances.append(balance)
            
            return balances
            
        except Exception as e:
            logger.error(f"Error getting account balances for user {user_id}: {e}")
            return []
    
    def _get_6_month_cash_flow_projection(self, user_id: str) -> List[CashFlowProjection]:
        """Get 6-month cash flow projections"""
        try:
            # Get historical transaction data for projection
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=180)  # 6 months of history
            
            transactions = self.db.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.date >= start_date,
                    PlaidTransaction.date <= end_date
                )
            ).all()
            
            # Calculate monthly averages
            monthly_data = defaultdict(lambda: {'income': 0, 'expenses': 0, 'count': 0})
            
            for transaction in transactions:
                month_key = transaction.date.strftime('%Y-%m')
                if transaction.amount > 0:
                    monthly_data[month_key]['income'] += transaction.amount
                else:
                    monthly_data[month_key]['expenses'] += abs(transaction.amount)
                monthly_data[month_key]['count'] += 1
            
            # Generate 6-month projection
            projections = []
            current_date = datetime.utcnow()
            
            for i in range(6):
                projection_date = current_date + timedelta(days=30*i)
                month_key = projection_date.strftime('%Y-%m')
                
                # Calculate averages from historical data
                avg_income = sum(data['income'] for data in monthly_data.values()) / max(len(monthly_data), 1)
                avg_expenses = sum(data['expenses'] for data in monthly_data.values()) / max(len(monthly_data), 1)
                
                # Apply seasonal adjustments (simplified)
                seasonal_factor = self._get_seasonal_factor(projection_date.month)
                projected_income = avg_income * seasonal_factor
                projected_expenses = avg_expenses * seasonal_factor
                
                net_cash_flow = projected_income - projected_expenses
                
                # Calculate confidence level based on data consistency
                confidence_level = min(0.95, max(0.6, len(monthly_data) / 6))
                
                projection = CashFlowProjection(
                    month=projection_date.strftime('%B %Y'),
                    projected_income=projected_income,
                    projected_expenses=projected_expenses,
                    net_cash_flow=net_cash_flow,
                    confidence_level=confidence_level,
                    key_factors=self._get_cash_flow_factors(projection_date)
                )
                projections.append(projection)
            
            return projections
            
        except Exception as e:
            logger.error(f"Error getting cash flow projection for user {user_id}: {e}")
            return []
    
    def _get_seasonal_factor(self, month: int) -> float:
        """Get seasonal adjustment factor for cash flow projection"""
        # Simplified seasonal factors
        seasonal_factors = {
            1: 0.9,   # January - post-holiday spending
            2: 0.95,  # February
            3: 1.0,   # March
            4: 1.05,  # April - tax season
            5: 1.0,   # May
            6: 0.95,  # June
            7: 0.9,   # July - summer spending
            8: 0.95,  # August
            9: 1.0,   # September
            10: 1.05, # October
            11: 1.1,  # November - holiday preparation
            12: 1.15  # December - holiday spending
        }
        return seasonal_factors.get(month, 1.0)
    
    def _get_cash_flow_factors(self, date: datetime) -> List[str]:
        """Get key factors affecting cash flow for a given month"""
        factors = []
        
        if date.month == 4:
            factors.append("Tax season may affect income")
        elif date.month == 12:
            factors.append("Holiday spending typically increases")
        elif date.month == 1:
            factors.append("Post-holiday spending typically decreases")
        
        return factors
    
    def _get_spending_categories_and_insights(self, user_id: str) -> List[SpendingCategoryInsight]:
        """Get standard spending categories and insights"""
        try:
            # Get recent transactions (last 3 months)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
            
            transactions = self.db.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.date >= start_date,
                    PlaidTransaction.date <= end_date,
                    PlaidTransaction.amount < 0  # Only expenses
                )
            ).all()
            
            # Group by category
            category_data = defaultdict(lambda: {'total': 0, 'count': 0, 'transactions': []})
            
            for transaction in transactions:
                category = transaction.category or 'Uncategorized'
                category_data[category]['total'] += abs(transaction.amount)
                category_data[category]['count'] += 1
                category_data[category]['transactions'].append(transaction)
            
            # Calculate total spending
            total_spending = sum(data['total'] for data in category_data.values())
            
            insights = []
            for category, data in category_data.items():
                percentage = (data['total'] / total_spending * 100) if total_spending > 0 else 0
                avg_transaction = data['total'] / data['count'] if data['count'] > 0 else 0
                
                # Calculate trend (simplified)
                trend, trend_percentage = self._calculate_spending_trend(data['transactions'])
                
                # Generate recommendations
                recommendations = self._generate_category_recommendations(
                    category, data['total'], percentage, avg_transaction
                )
                
                insight = SpendingCategoryInsight(
                    category_name=category,
                    total_spent=data['total'],
                    percentage_of_total=percentage,
                    transaction_count=data['count'],
                    average_transaction=avg_transaction,
                    trend=trend,
                    trend_percentage=trend_percentage,
                    recommendations=recommendations
                )
                insights.append(insight)
            
            # Sort by total spent
            insights.sort(key=lambda x: x.total_spent, reverse=True)
            
            return insights[:10]  # Return top 10 categories
            
        except Exception as e:
            logger.error(f"Error getting spending categories for user {user_id}: {e}")
            return []
    
    def _calculate_spending_trend(self, transactions: List[PlaidTransaction]) -> Tuple[str, float]:
        """Calculate spending trend for a category"""
        if len(transactions) < 2:
            return 'stable', 0.0
        
        # Split transactions into two periods
        mid_point = len(transactions) // 2
        first_half = transactions[:mid_point]
        second_half = transactions[mid_point:]
        
        first_total = sum(abs(t.amount) for t in first_half)
        second_total = sum(abs(t.amount) for t in second_half)
        
        if first_total == 0:
            return 'stable', 0.0
        
        change_percentage = ((second_total - first_total) / first_total) * 100
        
        if change_percentage > 10:
            return 'increasing', change_percentage
        elif change_percentage < -10:
            return 'decreasing', abs(change_percentage)
        else:
            return 'stable', 0.0
    
    def _generate_category_recommendations(self, category: str, total: float, percentage: float, avg_transaction: float) -> List[str]:
        """Generate recommendations for a spending category"""
        recommendations = []
        
        # High percentage spending
        if percentage > 30:
            recommendations.append(f"Consider reducing {category} spending - it's {percentage:.1f}% of your total")
        
        # High average transaction
        if avg_transaction > 100:
            recommendations.append(f"Look for ways to reduce individual {category} purchases")
        
        # Category-specific recommendations
        if category.lower() in ['dining', 'restaurants', 'food']:
            recommendations.append("Consider meal planning to reduce dining out costs")
        elif category.lower() in ['entertainment', 'recreation']:
            recommendations.append("Look for free or low-cost entertainment alternatives")
        elif category.lower() in ['shopping', 'retail']:
            recommendations.append("Wait 24 hours before making non-essential purchases")
        
        return recommendations[:3]  # Limit to 3 recommendations
    
    def _get_savings_goal_progress(self, user_id: str) -> List[SavingsGoalProgress]:
        """Get savings goal progress tracking"""
        try:
            # Get user's savings goals
            goals = self.savings_service.get_user_savings_goals(user_id)
            
            progress_data = []
            for goal in goals:
                current_amount = goal.current_amount
                target_amount = goal.target_amount
                progress_percentage = (current_amount / target_amount * 100) if target_amount > 0 else 0
                
                # Calculate monthly target
                if goal.target_date:
                    days_remaining = (goal.target_date - date.today()).days
                    remaining_amount = target_amount - current_amount
                    monthly_target = (remaining_amount / max(days_remaining / 30, 1))
                else:
                    days_remaining = 0
                    monthly_target = 0
                
                # Determine status
                if progress_percentage >= 100:
                    status = 'completed'
                elif progress_percentage >= 80:
                    status = 'ahead'
                elif progress_percentage >= 60:
                    status = 'on_track'
                else:
                    status = 'behind'
                
                # Get next milestone
                next_milestone = self._get_next_milestone(goal, current_amount)
                
                progress = SavingsGoalProgress(
                    goal_id=goal.id,
                    goal_name=goal.name,
                    target_amount=target_amount,
                    current_amount=current_amount,
                    progress_percentage=progress_percentage,
                    monthly_target=monthly_target,
                    days_remaining=days_remaining,
                    status=status,
                    next_milestone=next_milestone
                )
                progress_data.append(progress)
            
            return progress_data
            
        except Exception as e:
            logger.error(f"Error getting savings goal progress for user {user_id}: {e}")
            return []
    
    def _get_next_milestone(self, goal, current_amount: float) -> Optional[str]:
        """Get next milestone for a savings goal"""
        target_amount = goal.target_amount
        milestones = [0.25, 0.5, 0.75, 1.0]
        
        for milestone in milestones:
            milestone_amount = target_amount * milestone
            if current_amount < milestone_amount:
                return f"{milestone * 100:.0f}% - ${milestone_amount:,.0f}"
        
        return None
    
    def _get_bill_tracking_data(self, user_id: str) -> List[BillReminder]:
        """Get basic bill tracking data"""
        try:
            # Get user's bills
            bills = self.bill_service.get_user_bills(user_id)
            
            reminders = []
            today = date.today()
            
            for bill in bills:
                days_until_due = (bill.due_date - today).days
                
                # Determine priority
                if days_until_due <= 3:
                    priority = 'high'
                elif days_until_due <= 7:
                    priority = 'medium'
                else:
                    priority = 'low'
                
                reminder = BillReminder(
                    bill_id=bill.id,
                    bill_name=bill.name,
                    due_date=bill.due_date,
                    amount=bill.amount,
                    is_paid=bill.is_paid,
                    days_until_due=days_until_due,
                    category=bill.category,
                    priority=priority
                )
                reminders.append(reminder)
            
            # Sort by due date
            reminders.sort(key=lambda x: x.days_until_due)
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error getting bill tracking data for user {user_id}: {e}")
            return []
    
    def _get_key_dates_and_reminders(self, user_id: str) -> List[KeyDate]:
        """Get key dates tracking and reminders"""
        try:
            # Get user's key dates
            key_dates = self.bill_service.get_user_key_dates(user_id)
            
            dates_data = []
            today = date.today()
            
            for key_date in key_dates:
                days_until = (key_date.date - today).days
                
                date_info = KeyDate(
                    date_id=key_date.id,
                    title=key_date.title,
                    date=key_date.date,
                    category=key_date.category,
                    description=key_date.description,
                    days_until=days_until,
                    is_recurring=key_date.is_recurring,
                    reminder_sent=key_date.reminder_sent
                )
                dates_data.append(date_info)
            
            # Sort by date
            dates_data.sort(key=lambda x: x.days_until)
            
            return dates_data
            
        except Exception as e:
            logger.error(f"Error getting key dates for user {user_id}: {e}")
            return []
    
    def _get_spending_insights(self, user_id: str) -> List[Dict[str, Any]]:
        """Get spending insights and recommendations"""
        try:
            # Get basic spending insights from Mid-tier service
            insights = self.mid_tier_service.generate_basic_spending_insights(user_id)
            
            insights_data = []
            for insight in insights:
                insight_dict = {
                    'id': insight.id,
                    'type': insight.insight_type.value,
                    'title': insight.title,
                    'description': insight.description,
                    'impact_score': insight.impact_score,
                    'recommendations': insight.recommendations,
                    'generated_at': insight.generated_at.isoformat()
                }
                insights_data.append(insight_dict)
            
            return insights_data
            
        except Exception as e:
            logger.error(f"Error getting spending insights for user {user_id}: {e}")
            return []
    
    def _get_real_time_alerts(self, user_id: str) -> List[RealTimeAlert]:
        """Get real-time alerts and notifications"""
        try:
            # Get real-time alerts from the service
            alerts = self.real_time_service.get_user_alerts(user_id)
            
            alerts_data = []
            for alert in alerts:
                alert_info = RealTimeAlert(
                    alert_id=alert.id,
                    alert_type=alert.alert_type,
                    title=alert.title,
                    message=alert.message,
                    severity=alert.severity,
                    timestamp=alert.timestamp,
                    is_read=alert.is_read,
                    action_required=alert.action_required
                )
                alerts_data.append(alert_info)
            
            # Sort by timestamp (newest first)
            alerts_data.sort(key=lambda x: x.timestamp, reverse=True)
            
            return alerts_data[:10]  # Return latest 10 alerts
            
        except Exception as e:
            logger.error(f"Error getting real-time alerts for user {user_id}: {e}")
            return []
    
    def _get_performance_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get performance metrics for the dashboard"""
        try:
            # Calculate various performance metrics
            metrics = {
                'total_accounts': len(self._get_current_account_balances(user_id)),
                'total_savings_goals': len(self._get_savings_goal_progress(user_id)),
                'upcoming_bills': len([b for b in self._get_bill_tracking_data(user_id) if b.days_until_due <= 7]),
                'unread_alerts': len([a for a in self._get_real_time_alerts(user_id) if not a.is_read]),
                'spending_categories': len(self._get_spending_categories_and_insights(user_id)),
                'key_dates_this_month': len([d for d in self._get_key_dates_and_reminders(user_id) if d.days_until <= 30])
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics for user {user_id}: {e}")
            return {}
    
    def get_dashboard_widget_data(self, user_id: str, widget_type: DashboardWidgetType) -> Dict[str, Any]:
        """Get data for a specific dashboard widget"""
        try:
            if widget_type == DashboardWidgetType.ACCOUNT_BALANCES:
                return {'balances': self._get_current_account_balances(user_id)}
            elif widget_type == DashboardWidgetType.CASH_FLOW_PROJECTION:
                return {'projections': self._get_6_month_cash_flow_projection(user_id)}
            elif widget_type == DashboardWidgetType.SPENDING_CATEGORIES:
                return {'categories': self._get_spending_categories_and_insights(user_id)}
            elif widget_type == DashboardWidgetType.SAVINGS_GOALS:
                return {'goals': self._get_savings_goal_progress(user_id)}
            elif widget_type == DashboardWidgetType.BILL_TRACKING:
                return {'bills': self._get_bill_tracking_data(user_id)}
            elif widget_type == DashboardWidgetType.KEY_DATES:
                return {'dates': self._get_key_dates_and_reminders(user_id)}
            elif widget_type == DashboardWidgetType.SPENDING_INSIGHTS:
                return {'insights': self._get_spending_insights(user_id)}
            elif widget_type == DashboardWidgetType.ALERTS:
                return {'alerts': self._get_real_time_alerts(user_id)}
            else:
                return {'error': 'Unknown widget type'}
                
        except Exception as e:
            logger.error(f"Error getting widget data for user {user_id}, widget {widget_type}: {e}")
            return {'error': str(e)} 