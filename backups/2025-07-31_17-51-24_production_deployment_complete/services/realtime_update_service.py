"""
Real-time Update Service for Professional Dashboard

This module provides real-time updates for the Professional dashboard including:
- Live balance monitoring
- Transaction notifications
- Goal progress updates
- Alert system for important changes
- Performance metric calculations
"""

import logging
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import defaultdict, deque
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from backend.models.bank_account_models import PlaidAccount, PlaidTransaction
from backend.models.analytics import SpendingCategory, SpendingPattern
from backend.models.subscription import SubscriptionTier
from backend.models.goals import FinancialGoal, GoalProgress
from backend.models.alerts import Alert, AlertType, AlertSeverity
from backend.services.feature_access_service import FeatureAccessService
from backend.utils.websocket_manager import WebSocketManager
from backend.utils.cache_manager import CacheManager
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class UpdateType(Enum):
    """Types of real-time updates"""
    BALANCE_UPDATE = "balance_update"
    TRANSACTION_UPDATE = "transaction_update"
    GOAL_PROGRESS = "goal_progress"
    ALERT = "alert"
    PERFORMANCE_METRIC = "performance_metric"
    CASH_FLOW_UPDATE = "cash_flow_update"
    SPENDING_UPDATE = "spending_update"
    BILL_UPDATE = "bill_update"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RealTimeUpdate:
    """Real-time update data structure"""
    update_id: str
    user_id: str
    update_type: UpdateType
    timestamp: datetime
    data: Dict[str, Any]
    priority: NotificationPriority
    requires_action: bool = False
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class BalanceUpdate:
    """Balance update data"""
    account_id: str
    account_name: str
    previous_balance: float
    current_balance: float
    change_amount: float
    change_percentage: float
    last_updated: datetime
    institution_name: str


@dataclass
class TransactionNotification:
    """Transaction notification data"""
    transaction_id: str
    account_id: str
    amount: float
    merchant: str
    category: str
    description: str
    transaction_date: datetime
    is_large_transaction: bool
    is_unusual: bool
    risk_score: float


@dataclass
class GoalProgressUpdate:
    """Goal progress update data"""
    goal_id: str
    goal_name: str
    goal_type: str
    current_amount: float
    target_amount: float
    progress_percentage: float
    days_remaining: int
    is_on_track: bool
    milestone_reached: bool


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    metric_name: str
    current_value: float
    previous_value: float
    change_amount: float
    change_percentage: float
    trend: str
    benchmark: float
    status: str


class RealTimeUpdateService:
    """Real-time update service for Professional dashboard"""
    
    def __init__(self, db_session: Session, websocket_manager: WebSocketManager, cache_manager: CacheManager):
        self.db = db_session
        self.websocket_manager = websocket_manager
        self.cache_manager = cache_manager
        self.feature_service = FeatureAccessService(db_session)
        
        # Update tracking
        self.user_updates = defaultdict(deque)
        self.update_callbacks = defaultdict(list)
        self.monitoring_threads = {}
        self.is_running = False
        
        # Configuration
        self.update_intervals = {
            'balance': 30,  # 30 seconds
            'transactions': 60,  # 1 minute
            'goals': 300,  # 5 minutes
            'performance': 600,  # 10 minutes
            'alerts': 30  # 30 seconds
        }
        
        # Thresholds for alerts
        self.alert_thresholds = {
            'balance_change_percentage': 5.0,  # 5% balance change
            'large_transaction_amount': 1000.0,  # $1000 large transaction
            'unusual_spending_threshold': 2.0,  # 2x average spending
            'goal_off_track_threshold': 10.0,  # 10% off track
            'performance_decline_threshold': 5.0  # 5% performance decline
        }
        
    def start_monitoring(self, user_id: str):
        """Start real-time monitoring for a user"""
        try:
            if user_id in self.monitoring_threads:
                logger.info(f"Monitoring already active for user {user_id}")
                return
            
            # Verify Professional tier access
            if not self._verify_professional_access(user_id):
                logger.warning(f"User {user_id} does not have Professional tier access")
                return
            
            # Start monitoring thread
            monitoring_thread = threading.Thread(
                target=self._monitor_user_updates,
                args=(user_id,),
                daemon=True
            )
            monitoring_thread.start()
            
            self.monitoring_threads[user_id] = monitoring_thread
            logger.info(f"Started real-time monitoring for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error starting monitoring for user {user_id}: {e}")
    
    def stop_monitoring(self, user_id: str):
        """Stop real-time monitoring for a user"""
        try:
            if user_id in self.monitoring_threads:
                # Signal thread to stop
                self.monitoring_threads[user_id].join(timeout=5)
                del self.monitoring_threads[user_id]
                logger.info(f"Stopped real-time monitoring for user {user_id}")
        except Exception as e:
            logger.error(f"Error stopping monitoring for user {user_id}: {e}")
    
    def _monitor_user_updates(self, user_id: str):
        """Monitor and send real-time updates for a user"""
        try:
            while user_id in self.monitoring_threads:
                # Check for balance updates
                self._check_balance_updates(user_id)
                
                # Check for transaction updates
                self._check_transaction_updates(user_id)
                
                # Check for goal progress updates
                self._check_goal_progress_updates(user_id)
                
                # Check for performance metric updates
                self._check_performance_metric_updates(user_id)
                
                # Check for alerts
                self._check_alerts(user_id)
                
                # Wait before next check
                time.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.error(f"Error in monitoring thread for user {user_id}: {e}")
    
    def _check_balance_updates(self, user_id: str):
        """Check for balance updates and send notifications"""
        try:
            # Get current account balances
            accounts = self.db.query(PlaidAccount).filter(
                PlaidAccount.user_id == user_id,
                PlaidAccount.status == 'active'
            ).all()
            
            for account in accounts:
                # Get cached previous balance
                cache_key = f"balance_{user_id}_{account.account_id}"
                previous_balance = self.cache_manager.get(cache_key)
                
                if previous_balance is None:
                    # First time checking, cache current balance
                    self.cache_manager.set(cache_key, account.current_balance, ttl=3600)
                    continue
                
                current_balance = account.current_balance or 0.0
                change_amount = current_balance - previous_balance
                change_percentage = (change_amount / previous_balance * 100) if previous_balance > 0 else 0
                
                # Check if change is significant
                if abs(change_percentage) >= self.alert_thresholds['balance_change_percentage']:
                    # Create balance update
                    balance_update = BalanceUpdate(
                        account_id=account.account_id,
                        account_name=account.name,
                        previous_balance=previous_balance,
                        current_balance=current_balance,
                        change_amount=change_amount,
                        change_percentage=change_percentage,
                        last_updated=account.last_updated or datetime.utcnow(),
                        institution_name=account.institution_name
                    )
                    
                    # Send real-time update
                    self._send_balance_update(user_id, balance_update)
                    
                    # Create alert if significant change
                    if abs(change_percentage) >= 10.0:  # 10% or more
                        self._create_balance_alert(user_id, balance_update)
                
                # Update cached balance
                self.cache_manager.set(cache_key, current_balance, ttl=3600)
                
        except Exception as e:
            logger.error(f"Error checking balance updates for user {user_id}: {e}")
    
    def _check_transaction_updates(self, user_id: str):
        """Check for new transactions and send notifications"""
        try:
            # Get recent transactions (last 5 minutes)
            recent_time = datetime.utcnow() - timedelta(minutes=5)
            
            transactions = self.db.query(PlaidTransaction).filter(
                PlaidTransaction.user_id == user_id,
                PlaidTransaction.created_at >= recent_time
            ).all()
            
            for transaction in transactions:
                # Check if transaction is large
                is_large = abs(transaction.amount) >= self.alert_thresholds['large_transaction_amount']
                
                # Check if transaction is unusual
                is_unusual = self._check_unusual_transaction(user_id, transaction)
                
                # Calculate risk score
                risk_score = self._calculate_transaction_risk(transaction, is_large, is_unusual)
                
                # Create transaction notification
                transaction_notification = TransactionNotification(
                    transaction_id=transaction.transaction_id,
                    account_id=transaction.account_id,
                    amount=transaction.amount,
                    merchant=transaction.merchant_name or 'Unknown',
                    category=transaction.category or 'Uncategorized',
                    description=transaction.name,
                    transaction_date=transaction.date,
                    is_large_transaction=is_large,
                    is_unusual=is_unusual,
                    risk_score=risk_score
                )
                
                # Send real-time update
                self._send_transaction_update(user_id, transaction_notification)
                
                # Create alert for high-risk transactions
                if risk_score >= 0.7:  # High risk threshold
                    self._create_transaction_alert(user_id, transaction_notification)
                    
        except Exception as e:
            logger.error(f"Error checking transaction updates for user {user_id}: {e}")
    
    def _check_goal_progress_updates(self, user_id: str):
        """Check for goal progress updates and send notifications"""
        try:
            # Get active financial goals
            goals = self.db.query(FinancialGoal).filter(
                FinancialGoal.user_id == user_id,
                FinancialGoal.status == 'active'
            ).all()
            
            for goal in goals:
                # Get latest progress
                latest_progress = self.db.query(GoalProgress).filter(
                    GoalProgress.goal_id == goal.id
                ).order_by(GoalProgress.date.desc()).first()
                
                if not latest_progress:
                    continue
                
                # Calculate progress metrics
                current_amount = latest_progress.current_amount
                target_amount = goal.target_amount
                progress_percentage = (current_amount / target_amount * 100) if target_amount > 0 else 0
                
                # Calculate days remaining
                days_remaining = (goal.target_date - datetime.utcnow().date()).days if goal.target_date else 0
                
                # Check if on track
                expected_progress = self._calculate_expected_progress(goal, days_remaining)
                is_on_track = progress_percentage >= (expected_progress - self.alert_thresholds['goal_off_track_threshold'])
                
                # Check for milestone reached
                milestone_reached = self._check_milestone_reached(goal, current_amount)
                
                # Create goal progress update
                goal_update = GoalProgressUpdate(
                    goal_id=str(goal.id),
                    goal_name=goal.name,
                    goal_type=goal.goal_type,
                    current_amount=current_amount,
                    target_amount=target_amount,
                    progress_percentage=progress_percentage,
                    days_remaining=days_remaining,
                    is_on_track=is_on_track,
                    milestone_reached=milestone_reached
                )
                
                # Send real-time update
                self._send_goal_progress_update(user_id, goal_update)
                
                # Create alert if off track
                if not is_on_track:
                    self._create_goal_alert(user_id, goal_update)
                    
        except Exception as e:
            logger.error(f"Error checking goal progress updates for user {user_id}: {e}")
    
    def _check_performance_metric_updates(self, user_id: str):
        """Check for performance metric updates and send notifications"""
        try:
            # Calculate key performance metrics
            metrics = self._calculate_performance_metrics(user_id)
            
            for metric in metrics:
                # Check for significant changes
                if abs(metric.change_percentage) >= self.alert_thresholds['performance_decline_threshold']:
                    # Send real-time update
                    self._send_performance_metric_update(user_id, metric)
                    
                    # Create alert for significant declines
                    if metric.change_percentage < -10.0:  # 10% or more decline
                        self._create_performance_alert(user_id, metric)
                        
        except Exception as e:
            logger.error(f"Error checking performance metric updates for user {user_id}: {e}")
    
    def _check_alerts(self, user_id: str):
        """Check for new alerts and send notifications"""
        try:
            # Get recent alerts (last 5 minutes)
            recent_time = datetime.utcnow() - timedelta(minutes=5)
            
            alerts = self.db.query(Alert).filter(
                Alert.user_id == user_id,
                Alert.created_at >= recent_time,
                Alert.status == 'active'
            ).all()
            
            for alert in alerts:
                # Send real-time alert update
                self._send_alert_update(user_id, alert)
                
        except Exception as e:
            logger.error(f"Error checking alerts for user {user_id}: {e}")
    
    def _send_balance_update(self, user_id: str, balance_update: BalanceUpdate):
        """Send balance update via WebSocket"""
        try:
            update_data = {
                'type': UpdateType.BALANCE_UPDATE.value,
                'data': {
                    'account_id': balance_update.account_id,
                    'account_name': balance_update.account_name,
                    'previous_balance': balance_update.previous_balance,
                    'current_balance': balance_update.current_balance,
                    'change_amount': balance_update.change_amount,
                    'change_percentage': balance_update.change_percentage,
                    'last_updated': balance_update.last_updated.isoformat(),
                    'institution_name': balance_update.institution_name
                },
                'timestamp': datetime.utcnow().isoformat(),
                'priority': NotificationPriority.MEDIUM.value
            }
            
            self.websocket_manager.send_to_user(user_id, 'dashboard_update', update_data)
            
            # Store update in cache
            self._store_update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Error sending balance update for user {user_id}: {e}")
    
    def _send_transaction_update(self, user_id: str, transaction: TransactionNotification):
        """Send transaction update via WebSocket"""
        try:
            update_data = {
                'type': UpdateType.TRANSACTION_UPDATE.value,
                'data': {
                    'transaction_id': transaction.transaction_id,
                    'account_id': transaction.account_id,
                    'amount': transaction.amount,
                    'merchant': transaction.merchant,
                    'category': transaction.category,
                    'description': transaction.description,
                    'transaction_date': transaction.transaction_date.isoformat(),
                    'is_large_transaction': transaction.is_large_transaction,
                    'is_unusual': transaction.is_unusual,
                    'risk_score': transaction.risk_score
                },
                'timestamp': datetime.utcnow().isoformat(),
                'priority': NotificationPriority.HIGH.value if transaction.is_large_transaction else NotificationPriority.MEDIUM.value
            }
            
            self.websocket_manager.send_to_user(user_id, 'dashboard_update', update_data)
            
            # Store update in cache
            self._store_update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Error sending transaction update for user {user_id}: {e}")
    
    def _send_goal_progress_update(self, user_id: str, goal_update: GoalProgressUpdate):
        """Send goal progress update via WebSocket"""
        try:
            update_data = {
                'type': UpdateType.GOAL_PROGRESS.value,
                'data': {
                    'goal_id': goal_update.goal_id,
                    'goal_name': goal_update.goal_name,
                    'goal_type': goal_update.goal_type,
                    'current_amount': goal_update.current_amount,
                    'target_amount': goal_update.target_amount,
                    'progress_percentage': goal_update.progress_percentage,
                    'days_remaining': goal_update.days_remaining,
                    'is_on_track': goal_update.is_on_track,
                    'milestone_reached': goal_update.milestone_reached
                },
                'timestamp': datetime.utcnow().isoformat(),
                'priority': NotificationPriority.MEDIUM.value
            }
            
            self.websocket_manager.send_to_user(user_id, 'dashboard_update', update_data)
            
            # Store update in cache
            self._store_update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Error sending goal progress update for user {user_id}: {e}")
    
    def _send_performance_metric_update(self, user_id: str, metric: PerformanceMetric):
        """Send performance metric update via WebSocket"""
        try:
            update_data = {
                'type': UpdateType.PERFORMANCE_METRIC.value,
                'data': {
                    'metric_name': metric.metric_name,
                    'current_value': metric.current_value,
                    'previous_value': metric.previous_value,
                    'change_amount': metric.change_amount,
                    'change_percentage': metric.change_percentage,
                    'trend': metric.trend,
                    'benchmark': metric.benchmark,
                    'status': metric.status
                },
                'timestamp': datetime.utcnow().isoformat(),
                'priority': NotificationPriority.LOW.value
            }
            
            self.websocket_manager.send_to_user(user_id, 'dashboard_update', update_data)
            
            # Store update in cache
            self._store_update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Error sending performance metric update for user {user_id}: {e}")
    
    def _send_alert_update(self, user_id: str, alert: Alert):
        """Send alert update via WebSocket"""
        try:
            update_data = {
                'type': UpdateType.ALERT.value,
                'data': {
                    'alert_id': str(alert.id),
                    'alert_type': alert.alert_type.value,
                    'severity': alert.severity.value,
                    'title': alert.title,
                    'message': alert.message,
                    'created_at': alert.created_at.isoformat(),
                    'requires_action': alert.requires_action,
                    'action_url': alert.action_url
                },
                'timestamp': datetime.utcnow().isoformat(),
                'priority': self._get_alert_priority(alert.severity)
            }
            
            self.websocket_manager.send_to_user(user_id, 'dashboard_update', update_data)
            
            # Store update in cache
            self._store_update(user_id, update_data)
            
        except Exception as e:
            logger.error(f"Error sending alert update for user {user_id}: {e}")
    
    def _store_update(self, user_id: str, update_data: Dict[str, Any]):
        """Store update in cache for history"""
        try:
            cache_key = f"updates_{user_id}"
            updates = self.cache_manager.get(cache_key) or []
            
            # Add new update
            updates.append(update_data)
            
            # Keep only last 100 updates
            if len(updates) > 100:
                updates = updates[-100:]
            
            # Store in cache
            self.cache_manager.set(cache_key, updates, ttl=86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error storing update for user {user_id}: {e}")
    
    def get_user_updates(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent updates for a user"""
        try:
            cache_key = f"updates_{user_id}"
            updates = self.cache_manager.get(cache_key) or []
            return updates[-limit:] if updates else []
        except Exception as e:
            logger.error(f"Error getting updates for user {user_id}: {e}")
            return []
    
    def _verify_professional_access(self, user_id: str) -> bool:
        """Verify user has Professional tier access"""
        try:
            return self.feature_service.can_access_feature(user_id, 'real_time_updates')
        except Exception as e:
            logger.error(f"Error verifying Professional access for user {user_id}: {e}")
            return False
    
    def _check_unusual_transaction(self, user_id: str, transaction: PlaidTransaction) -> bool:
        """Check if transaction is unusual based on spending patterns"""
        try:
            # Get average spending for this category
            avg_spending = self.db.query(func.avg(PlaidTransaction.amount)).filter(
                PlaidTransaction.user_id == user_id,
                PlaidTransaction.category == transaction.category,
                PlaidTransaction.date >= datetime.utcnow() - timedelta(days=30)
            ).scalar() or 0
            
            # Check if transaction is significantly higher than average
            return abs(transaction.amount) > (avg_spending * self.alert_thresholds['unusual_spending_threshold'])
            
        except Exception as e:
            logger.error(f"Error checking unusual transaction: {e}")
            return False
    
    def _calculate_transaction_risk(self, transaction: PlaidTransaction, is_large: bool, is_unusual: bool) -> float:
        """Calculate risk score for a transaction"""
        try:
            risk_score = 0.0
            
            # Large transaction risk
            if is_large:
                risk_score += 0.4
            
            # Unusual transaction risk
            if is_unusual:
                risk_score += 0.3
            
            # Negative amount risk (withdrawals)
            if transaction.amount < 0:
                risk_score += 0.2
            
            # Unknown merchant risk
            if not transaction.merchant_name or transaction.merchant_name == 'Unknown':
                risk_score += 0.1
            
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating transaction risk: {e}")
            return 0.0
    
    def _calculate_expected_progress(self, goal: FinancialGoal, days_remaining: int) -> float:
        """Calculate expected progress for a goal"""
        try:
            if not goal.target_date or days_remaining <= 0:
                return 100.0
            
            total_days = (goal.target_date - goal.created_at.date()).days
            if total_days <= 0:
                return 100.0
            
            elapsed_days = total_days - days_remaining
            return (elapsed_days / total_days) * 100
            
        except Exception as e:
            logger.error(f"Error calculating expected progress: {e}")
            return 0.0
    
    def _check_milestone_reached(self, goal: FinancialGoal, current_amount: float) -> bool:
        """Check if a milestone has been reached"""
        try:
            # Check for 25%, 50%, 75% milestones
            target_amount = goal.target_amount
            milestones = [0.25, 0.5, 0.75]
            
            for milestone in milestones:
                milestone_amount = target_amount * milestone
                if current_amount >= milestone_amount:
                    # Check if this milestone was just reached
                    cache_key = f"milestone_{goal.id}_{milestone}"
                    if not self.cache_manager.get(cache_key):
                        self.cache_manager.set(cache_key, True, ttl=86400)  # 24 hours
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking milestone: {e}")
            return False
    
    def _calculate_performance_metrics(self, user_id: str) -> List[PerformanceMetric]:
        """Calculate performance metrics for a user"""
        try:
            metrics = []
            
            # Calculate savings rate
            savings_rate = self._calculate_savings_rate(user_id)
            metrics.append(savings_rate)
            
            # Calculate spending efficiency
            spending_efficiency = self._calculate_spending_efficiency(user_id)
            metrics.append(spending_efficiency)
            
            # Calculate investment performance
            investment_performance = self._calculate_investment_performance(user_id)
            metrics.append(investment_performance)
            
            # Calculate debt-to-income ratio
            debt_to_income = self._calculate_debt_to_income_ratio(user_id)
            metrics.append(debt_to_income)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics for user {user_id}: {e}")
            return []
    
    def _calculate_savings_rate(self, user_id: str) -> PerformanceMetric:
        """Calculate savings rate performance metric"""
        try:
            # Get current month's income and expenses
            current_month = datetime.utcnow().replace(day=1)
            
            income = self.db.query(func.sum(PlaidTransaction.amount)).filter(
                PlaidTransaction.user_id == user_id,
                PlaidTransaction.amount > 0,
                PlaidTransaction.date >= current_month
            ).scalar() or 0
            
            expenses = abs(self.db.query(func.sum(PlaidTransaction.amount)).filter(
                PlaidTransaction.user_id == user_id,
                PlaidTransaction.amount < 0,
                PlaidTransaction.date >= current_month
            ).scalar() or 0)
            
            current_savings_rate = ((income - expenses) / income * 100) if income > 0 else 0
            
            # Get previous month's savings rate
            previous_month = (current_month - timedelta(days=1)).replace(day=1)
            
            prev_income = self.db.query(func.sum(PlaidTransaction.amount)).filter(
                PlaidTransaction.user_id == user_id,
                PlaidTransaction.amount > 0,
                PlaidTransaction.date >= previous_month,
                PlaidTransaction.date < current_month
            ).scalar() or 0
            
            prev_expenses = abs(self.db.query(func.sum(PlaidTransaction.amount)).filter(
                PlaidTransaction.user_id == user_id,
                PlaidTransaction.amount < 0,
                PlaidTransaction.date >= previous_month,
                PlaidTransaction.date < current_month
            ).scalar() or 0)
            
            previous_savings_rate = ((prev_income - prev_expenses) / prev_income * 100) if prev_income > 0 else 0
            
            change_amount = current_savings_rate - previous_savings_rate
            change_percentage = (change_amount / previous_savings_rate * 100) if previous_savings_rate > 0 else 0
            
            return PerformanceMetric(
                metric_name='Savings Rate',
                current_value=current_savings_rate,
                previous_value=previous_savings_rate,
                change_amount=change_amount,
                change_percentage=change_percentage,
                trend='up' if change_amount > 0 else 'down',
                benchmark=20.0,  # 20% benchmark
                status='good' if current_savings_rate >= 20.0 else 'needs_improvement'
            )
            
        except Exception as e:
            logger.error(f"Error calculating savings rate: {e}")
            return PerformanceMetric(
                metric_name='Savings Rate',
                current_value=0.0,
                previous_value=0.0,
                change_amount=0.0,
                change_percentage=0.0,
                trend='stable',
                benchmark=20.0,
                status='unknown'
            )
    
    def _calculate_spending_efficiency(self, user_id: str) -> PerformanceMetric:
        """Calculate spending efficiency performance metric"""
        try:
            # Calculate spending efficiency based on budget adherence
            # This is a simplified calculation - in practice, you'd compare against actual budgets
            
            current_month = datetime.utcnow().replace(day=1)
            
            total_spending = abs(self.db.query(func.sum(PlaidTransaction.amount)).filter(
                PlaidTransaction.user_id == user_id,
                PlaidTransaction.amount < 0,
                PlaidTransaction.date >= current_month
            ).scalar() or 0)
            
            # Assume 100% efficiency for now (would compare against budget)
            current_efficiency = 100.0
            previous_efficiency = 95.0  # Assume previous month
            
            change_amount = current_efficiency - previous_efficiency
            change_percentage = (change_amount / previous_efficiency * 100) if previous_efficiency > 0 else 0
            
            return PerformanceMetric(
                metric_name='Spending Efficiency',
                current_value=current_efficiency,
                previous_value=previous_efficiency,
                change_amount=change_amount,
                change_percentage=change_percentage,
                trend='up' if change_amount > 0 else 'down',
                benchmark=90.0,  # 90% benchmark
                status='good' if current_efficiency >= 90.0 else 'needs_improvement'
            )
            
        except Exception as e:
            logger.error(f"Error calculating spending efficiency: {e}")
            return PerformanceMetric(
                metric_name='Spending Efficiency',
                current_value=0.0,
                previous_value=0.0,
                change_amount=0.0,
                change_percentage=0.0,
                trend='stable',
                benchmark=90.0,
                status='unknown'
            )
    
    def _calculate_investment_performance(self, user_id: str) -> PerformanceMetric:
        """Calculate investment performance metric"""
        try:
            # This would integrate with investment accounts
            # For now, return a placeholder metric
            
            return PerformanceMetric(
                metric_name='Investment Performance',
                current_value=8.5,  # 8.5% return
                previous_value=7.2,  # 7.2% previous
                change_amount=1.3,
                change_percentage=18.1,
                trend='up',
                benchmark=7.0,  # 7% benchmark
                status='good'
            )
            
        except Exception as e:
            logger.error(f"Error calculating investment performance: {e}")
            return PerformanceMetric(
                metric_name='Investment Performance',
                current_value=0.0,
                previous_value=0.0,
                change_amount=0.0,
                change_percentage=0.0,
                trend='stable',
                benchmark=7.0,
                status='unknown'
            )
    
    def _calculate_debt_to_income_ratio(self, user_id: str) -> PerformanceMetric:
        """Calculate debt-to-income ratio performance metric"""
        try:
            # This would calculate actual debt-to-income ratio
            # For now, return a placeholder metric
            
            return PerformanceMetric(
                metric_name='Debt-to-Income Ratio',
                current_value=25.0,  # 25%
                previous_value=28.0,  # 28% previous
                change_amount=-3.0,
                change_percentage=-10.7,
                trend='down',
                benchmark=30.0,  # 30% benchmark (lower is better)
                status='good'
            )
            
        except Exception as e:
            logger.error(f"Error calculating debt-to-income ratio: {e}")
            return PerformanceMetric(
                metric_name='Debt-to-Income Ratio',
                current_value=0.0,
                previous_value=0.0,
                change_amount=0.0,
                change_percentage=0.0,
                trend='stable',
                benchmark=30.0,
                status='unknown'
            )
    
    def _get_alert_priority(self, severity: AlertSeverity) -> str:
        """Get notification priority based on alert severity"""
        priority_map = {
            AlertSeverity.LOW: NotificationPriority.LOW.value,
            AlertSeverity.MEDIUM: NotificationPriority.MEDIUM.value,
            AlertSeverity.HIGH: NotificationPriority.HIGH.value,
            AlertSeverity.CRITICAL: NotificationPriority.CRITICAL.value
        }
        return priority_map.get(severity, NotificationPriority.MEDIUM.value)
    
    def _create_balance_alert(self, user_id: str, balance_update: BalanceUpdate):
        """Create balance alert"""
        try:
            alert = Alert(
                user_id=user_id,
                alert_type=AlertType.BALANCE_CHANGE,
                severity=AlertSeverity.HIGH if abs(balance_update.change_percentage) >= 20.0 else AlertSeverity.MEDIUM,
                title=f"Significant Balance Change - {balance_update.account_name}",
                message=f"Your {balance_update.account_name} balance changed by {balance_update.change_percentage:.1f}% ({formatCurrency(balance_update.change_amount)})",
                requires_action=False,
                status='active'
            )
            
            self.db.add(alert)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating balance alert: {e}")
    
    def _create_transaction_alert(self, user_id: str, transaction: TransactionNotification):
        """Create transaction alert"""
        try:
            alert = Alert(
                user_id=user_id,
                alert_type=AlertType.SUSPICIOUS_TRANSACTION,
                severity=AlertSeverity.HIGH if transaction.risk_score >= 0.8 else AlertSeverity.MEDIUM,
                title=f"High-Risk Transaction Detected",
                message=f"Transaction of {formatCurrency(transaction.amount)} at {transaction.merchant} has been flagged as high-risk",
                requires_action=True,
                action_url=f"/transactions/{transaction.transaction_id}",
                status='active'
            )
            
            self.db.add(alert)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating transaction alert: {e}")
    
    def _create_goal_alert(self, user_id: str, goal_update: GoalProgressUpdate):
        """Create goal alert"""
        try:
            alert = Alert(
                user_id=user_id,
                alert_type=AlertType.GOAL_OFF_TRACK,
                severity=AlertSeverity.MEDIUM,
                title=f"Goal Off Track - {goal_update.goal_name}",
                message=f"Your {goal_update.goal_name} goal is {goal_update.progress_percentage:.1f}% complete but may be off track",
                requires_action=True,
                action_url=f"/goals/{goal_update.goal_id}",
                status='active'
            )
            
            self.db.add(alert)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating goal alert: {e}")
    
    def _create_performance_alert(self, user_id: str, metric: PerformanceMetric):
        """Create performance alert"""
        try:
            alert = Alert(
                user_id=user_id,
                alert_type=AlertType.PERFORMANCE_DECLINE,
                severity=AlertSeverity.MEDIUM,
                title=f"Performance Decline - {metric.metric_name}",
                message=f"Your {metric.metric_name} has declined by {abs(metric.change_percentage):.1f}%",
                requires_action=False,
                status='active'
            )
            
            self.db.add(alert)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error creating performance alert: {e}")


def formatCurrency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}" 