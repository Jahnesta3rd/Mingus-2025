"""
Real-Time Updates Service

This module provides real-time updates and notifications for the MINGUS application,
including live balance monitoring, transaction notifications, goal progress updates,
alert systems, and performance metric calculations.
"""

import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from collections import defaultdict, deque
import threading
import queue

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.bank_account_models import PlaidAccount, PlaidTransaction
from backend.models.analytics import SpendingCategory, SpendingPattern
from backend.models.user_models import User
from backend.services.notification_service import NotificationService
from backend.services.websocket_service import WebSocketService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of real-time alerts"""
    BALANCE_CHANGE = "balance_change"
    TRANSACTION_RECEIVED = "transaction_received"
    GOAL_MILESTONE = "goal_milestone"
    BILL_DUE_SOON = "bill_due_soon"
    SPENDING_ALERT = "spending_alert"
    CASH_FLOW_WARNING = "cash_flow_warning"
    SECURITY_ALERT = "security_alert"
    SYSTEM_UPDATE = "system_update"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class RealTimeAlert:
    """Real-time alert data structure"""
    alert_id: str
    user_id: str
    alert_type: AlertType
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    is_read: bool = False
    action_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BalanceUpdate:
    """Balance update data structure"""
    account_id: str
    user_id: str
    previous_balance: float
    current_balance: float
    change_amount: float
    change_percentage: float
    timestamp: datetime
    transaction_count: int = 0


@dataclass
class TransactionNotification:
    """Transaction notification data structure"""
    transaction_id: str
    user_id: str
    account_id: str
    amount: float
    merchant_name: str
    category: str
    transaction_type: str  # 'credit', 'debit'
    timestamp: datetime
    is_large_transaction: bool = False
    is_unusual_category: bool = False


@dataclass
class GoalProgressUpdate:
    """Goal progress update data structure"""
    goal_id: str
    user_id: str
    goal_name: str
    previous_progress: float
    current_progress: float
    progress_change: float
    milestone_reached: bool = False
    milestone_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    metric_name: str
    value: float
    unit: str
    trend: str  # 'up', 'down', 'stable'
    trend_value: float
    timestamp: datetime
    comparison_period: str  # 'day', 'week', 'month'


class RealTimeUpdatesService:
    """Service for managing real-time updates and notifications"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.notification_service = NotificationService(db_session, config)
        self.websocket_service = WebSocketService(db_session, config)
        
        # Cache for real-time data
        self.balance_cache: Dict[str, float] = {}
        self.alert_cache: Dict[str, List[RealTimeAlert]] = {}
        self.metric_cache: Dict[str, Dict[str, float]] = {}
        
        # Configuration
        self.update_interval = 30  # seconds
        self.alert_thresholds = self._initialize_alert_thresholds()
        self.monitoring_active = False
        
        # Threading for background updates
        self.update_queue = queue.Queue()
        self.update_thread = None
        
    def _initialize_alert_thresholds(self) -> Dict[str, Any]:
        """Initialize alert thresholds for different types of alerts"""
        return {
            'balance_change': {
                'percentage_threshold': 10.0,  # 10% change
                'amount_threshold': 100.0,     # $100 change
                'time_window': 3600  # 1 hour
            },
            'large_transaction': {
                'amount_threshold': 500.0,     # $500
                'percentage_of_balance': 20.0  # 20% of balance
            },
            'spending_alert': {
                'daily_limit': 200.0,          # $200 per day
                'category_limit': 100.0,       # $100 per category per day
                'unusual_category_threshold': 50.0  # $50 for unusual categories
            },
            'goal_progress': {
                'milestone_threshold': 25.0,   # 25% milestones
                'stagnation_days': 7           # Alert if no progress for 7 days
            },
            'cash_flow_warning': {
                'negative_balance_threshold': -100.0,  # -$100
                'low_balance_threshold': 500.0        # $500
            }
        }
    
    def start_monitoring(self):
        """Start real-time monitoring for all active users"""
        if self.monitoring_active:
            logger.warning("Real-time monitoring is already active")
            return
        
        self.monitoring_active = True
        self.update_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.update_thread.start()
        logger.info("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("Real-time monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop for real-time updates"""
        while self.monitoring_active:
            try:
                # Get all active users
                active_users = self._get_active_users()
                
                for user_id in active_users:
                    try:
                        # Check for balance updates
                        self._check_balance_updates(user_id)
                        
                        # Check for new transactions
                        self._check_new_transactions(user_id)
                        
                        # Check goal progress
                        self._check_goal_progress(user_id)
                        
                        # Check bill due dates
                        self._check_bill_due_dates(user_id)
                        
                        # Check spending alerts
                        self._check_spending_alerts(user_id)
                        
                        # Update performance metrics
                        self._update_performance_metrics(user_id)
                        
                    except Exception as e:
                        logger.error(f"Error monitoring user {user_id}: {e}")
                
                # Wait for next update cycle
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.update_interval)
    
    def _get_active_users(self) -> List[str]:
        """Get list of active users for monitoring"""
        try:
            # Get users who have been active in the last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            active_users = self.db.query(User.id).filter(
                and_(
                    User.is_active == True,
                    User.last_login >= cutoff_date
                )
            ).all()
            
            return [user.id for user in active_users]
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def _check_balance_updates(self, user_id: str):
        """Check for balance updates and generate alerts"""
        try:
            # Get user's accounts
            accounts = self.db.query(PlaidAccount).filter(
                and_(
                    PlaidAccount.user_id == user_id,
                    PlaidAccount.is_active == True
                )
            ).all()
            
            for account in accounts:
                # Get current balance
                current_balance = self._get_current_balance(account.id)
                previous_balance = self.balance_cache.get(account.id, current_balance)
                
                if previous_balance != current_balance:
                    # Calculate change
                    change_amount = current_balance - previous_balance
                    change_percentage = (change_amount / previous_balance * 100) if previous_balance > 0 else 0
                    
                    # Check if change exceeds thresholds
                    if self._should_alert_balance_change(change_amount, change_percentage):
                        alert = self._create_balance_alert(
                            user_id, account.id, previous_balance, current_balance, 
                            change_amount, change_percentage
                        )
                        self._send_alert(alert)
                    
                    # Update cache
                    self.balance_cache[account.id] = current_balance
                    
        except Exception as e:
            logger.error(f"Error checking balance updates for user {user_id}: {e}")
    
    def _get_current_balance(self, account_id: str) -> float:
        """Get current balance for an account"""
        try:
            # Get latest transaction with balance
            latest_transaction = self.db.query(PlaidTransaction).filter(
                PlaidTransaction.account_id == account_id
            ).order_by(desc(PlaidTransaction.date)).first()
            
            return latest_transaction.balance if latest_transaction else 0.0
            
        except Exception as e:
            logger.error(f"Error getting current balance for account {account_id}: {e}")
            return 0.0
    
    def _should_alert_balance_change(self, change_amount: float, change_percentage: float) -> bool:
        """Determine if balance change should trigger an alert"""
        thresholds = self.alert_thresholds['balance_change']
        
        return (abs(change_amount) >= thresholds['amount_threshold'] or 
                abs(change_percentage) >= thresholds['percentage_threshold'])
    
    def _create_balance_alert(self, user_id: str, account_id: str, previous_balance: float, 
                             current_balance: float, change_amount: float, change_percentage: float) -> RealTimeAlert:
        """Create a balance change alert"""
        if change_amount > 0:
            title = "Account Balance Increased"
            message = f"Your account balance increased by ${change_amount:,.2f} ({change_percentage:+.1f}%)"
            severity = AlertSeverity.INFO
        else:
            title = "Account Balance Decreased"
            message = f"Your account balance decreased by ${abs(change_amount):,.2f} ({change_percentage:+.1f}%)"
            severity = AlertSeverity.WARNING if abs(change_percentage) > 20 else AlertSeverity.INFO
        
        return RealTimeAlert(
            alert_id=f"balance_{account_id}_{int(time.time())}",
            user_id=user_id,
            alert_type=AlertType.BALANCE_CHANGE,
            title=title,
            message=message,
            severity=severity,
            timestamp=datetime.utcnow(),
            metadata={
                'account_id': account_id,
                'previous_balance': previous_balance,
                'current_balance': current_balance,
                'change_amount': change_amount,
                'change_percentage': change_percentage
            }
        )
    
    def _check_new_transactions(self, user_id: str):
        """Check for new transactions and generate notifications"""
        try:
            # Get recent transactions (last hour)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            recent_transactions = self.db.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.created_at >= cutoff_time
                )
            ).all()
            
            for transaction in recent_transactions:
                # Check if this is a large transaction
                is_large = self._is_large_transaction(transaction)
                
                # Check if this is an unusual category
                is_unusual = self._is_unusual_category(transaction)
                
                if is_large or is_unusual:
                    notification = self._create_transaction_notification(transaction, is_large, is_unusual)
                    self._send_transaction_notification(notification)
                    
        except Exception as e:
            logger.error(f"Error checking new transactions for user {user_id}: {e}")
    
    def _is_large_transaction(self, transaction: PlaidTransaction) -> bool:
        """Check if transaction is considered large"""
        thresholds = self.alert_thresholds['large_transaction']
        
        # Check absolute amount
        if abs(transaction.amount) >= thresholds['amount_threshold']:
            return True
        
        # Check percentage of account balance
        account_balance = self._get_current_balance(transaction.account_id)
        if account_balance > 0:
            percentage = (abs(transaction.amount) / account_balance) * 100
            if percentage >= thresholds['percentage_of_balance']:
                return True
        
        return False
    
    def _is_unusual_category(self, transaction: PlaidTransaction) -> bool:
        """Check if transaction is in an unusual category for the user"""
        try:
            # Get user's typical spending categories
            user_categories = self.db.query(PlaidTransaction.category).filter(
                and_(
                    PlaidTransaction.user_id == transaction.user_id,
                    PlaidTransaction.amount < 0,  # Only expenses
                    PlaidTransaction.date >= datetime.utcnow() - timedelta(days=30)
                )
            ).group_by(PlaidTransaction.category).all()
            
            typical_categories = {cat[0] for cat in user_categories if cat[0]}
            
            return transaction.category not in typical_categories
            
        except Exception as e:
            logger.error(f"Error checking unusual category: {e}")
            return False
    
    def _create_transaction_notification(self, transaction: PlaidTransaction, 
                                       is_large: bool, is_unusual: bool) -> TransactionNotification:
        """Create a transaction notification"""
        return TransactionNotification(
            transaction_id=transaction.id,
            user_id=transaction.user_id,
            account_id=transaction.account_id,
            amount=transaction.amount,
            merchant_name=transaction.merchant_name or "Unknown",
            category=transaction.category or "Uncategorized",
            transaction_type="credit" if transaction.amount > 0 else "debit",
            timestamp=transaction.date,
            is_large_transaction=is_large,
            is_unusual_category=is_unusual
        )
    
    def _check_goal_progress(self, user_id: str):
        """Check goal progress and generate milestone alerts"""
        try:
            # This would integrate with the savings goals service
            # For now, we'll create a placeholder implementation
            
            # Get user's savings goals
            goals = self._get_user_savings_goals(user_id)
            
            for goal in goals:
                # Check for milestone progress
                milestone_reached = self._check_milestone_progress(goal)
                
                if milestone_reached:
                    alert = self._create_goal_milestone_alert(user_id, goal)
                    self._send_alert(alert)
                    
        except Exception as e:
            logger.error(f"Error checking goal progress for user {user_id}: {e}")
    
    def _get_user_savings_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's savings goals (placeholder implementation)"""
        # This would integrate with the actual savings goals service
        return []
    
    def _check_milestone_progress(self, goal: Dict[str, Any]) -> bool:
        """Check if a goal has reached a milestone"""
        # Placeholder implementation
        return False
    
    def _create_goal_milestone_alert(self, user_id: str, goal: Dict[str, Any]) -> RealTimeAlert:
        """Create a goal milestone alert"""
        return RealTimeAlert(
            alert_id=f"goal_{goal.get('id', 'unknown')}_{int(time.time())}",
            user_id=user_id,
            alert_type=AlertType.GOAL_MILESTONE,
            title="Savings Goal Milestone Reached!",
            message=f"Congratulations! You've reached a milestone in your '{goal.get('name', 'Unknown')}' goal.",
            severity=AlertSeverity.INFO,
            timestamp=datetime.utcnow(),
            metadata={'goal_id': goal.get('id'), 'goal_name': goal.get('name')}
        )
    
    def _check_bill_due_dates(self, user_id: str):
        """Check bill due dates and generate reminders"""
        try:
            # This would integrate with the bill tracking service
            # For now, we'll create a placeholder implementation
            
            upcoming_bills = self._get_upcoming_bills(user_id)
            
            for bill in upcoming_bills:
                if bill['days_until_due'] <= 3:
                    alert = self._create_bill_due_alert(user_id, bill)
                    self._send_alert(alert)
                    
        except Exception as e:
            logger.error(f"Error checking bill due dates for user {user_id}: {e}")
    
    def _get_upcoming_bills(self, user_id: str) -> List[Dict[str, Any]]:
        """Get upcoming bills (placeholder implementation)"""
        # This would integrate with the actual bill tracking service
        return []
    
    def _create_bill_due_alert(self, user_id: str, bill: Dict[str, Any]) -> RealTimeAlert:
        """Create a bill due alert"""
        return RealTimeAlert(
            alert_id=f"bill_{bill.get('id', 'unknown')}_{int(time.time())}",
            user_id=user_id,
            alert_type=AlertType.BILL_DUE_SOON,
            title="Bill Due Soon",
            message=f"Your {bill.get('name', 'Unknown')} bill of ${bill.get('amount', 0):,.2f} is due in {bill.get('days_until_due', 0)} days.",
            severity=AlertSeverity.WARNING,
            timestamp=datetime.utcnow(),
            action_required=True,
            metadata={'bill_id': bill.get('id'), 'bill_name': bill.get('name'), 'amount': bill.get('amount')}
        )
    
    def _check_spending_alerts(self, user_id: str):
        """Check for spending alerts"""
        try:
            # Get today's spending
            today = date.today()
            today_transactions = self.db.query(PlaidTransaction).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.amount < 0,  # Only expenses
                    func.date(PlaidTransaction.date) == today
                )
            ).all()
            
            # Calculate daily spending
            daily_total = sum(abs(t.amount) for t in today_transactions)
            
            # Check daily limit
            thresholds = self.alert_thresholds['spending_alert']
            if daily_total >= thresholds['daily_limit']:
                alert = self._create_spending_alert(user_id, daily_total, "daily")
                self._send_alert(alert)
            
            # Check category spending
            category_spending = defaultdict(float)
            for transaction in today_transactions:
                category = transaction.category or "Uncategorized"
                category_spending[category] += abs(transaction.amount)
            
            for category, amount in category_spending.items():
                if amount >= thresholds['category_limit']:
                    alert = self._create_spending_alert(user_id, amount, "category", category)
                    self._send_alert(alert)
                    
        except Exception as e:
            logger.error(f"Error checking spending alerts for user {user_id}: {e}")
    
    def _create_spending_alert(self, user_id: str, amount: float, alert_type: str, 
                              category: Optional[str] = None) -> RealTimeAlert:
        """Create a spending alert"""
        if alert_type == "daily":
            title = "Daily Spending Limit Reached"
            message = f"You've spent ${amount:,.2f} today, which exceeds your daily spending limit."
        else:
            title = "Category Spending Alert"
            message = f"You've spent ${amount:,.2f} on {category} today, which exceeds your category limit."
        
        return RealTimeAlert(
            alert_id=f"spending_{alert_type}_{int(time.time())}",
            user_id=user_id,
            alert_type=AlertType.SPENDING_ALERT,
            title=title,
            message=message,
            severity=AlertSeverity.WARNING,
            timestamp=datetime.utcnow(),
            metadata={'amount': amount, 'alert_type': alert_type, 'category': category}
        )
    
    def _update_performance_metrics(self, user_id: str):
        """Update performance metrics for the user"""
        try:
            # Calculate various performance metrics
            metrics = {
                'daily_spending': self._calculate_daily_spending(user_id),
                'weekly_savings': self._calculate_weekly_savings(user_id),
                'goal_progress_rate': self._calculate_goal_progress_rate(user_id),
                'transaction_frequency': self._calculate_transaction_frequency(user_id),
                'category_diversity': self._calculate_category_diversity(user_id)
            }
            
            # Store metrics in cache
            self.metric_cache[user_id] = metrics
            
            # Send metrics update via WebSocket
            self.websocket_service.send_metrics_update(user_id, metrics)
            
        except Exception as e:
            logger.error(f"Error updating performance metrics for user {user_id}: {e}")
    
    def _calculate_daily_spending(self, user_id: str) -> float:
        """Calculate daily spending"""
        try:
            today = date.today()
            daily_spending = self.db.query(func.sum(func.abs(PlaidTransaction.amount))).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.amount < 0,
                    func.date(PlaidTransaction.date) == today
                )
            ).scalar()
            
            return float(daily_spending) if daily_spending else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating daily spending: {e}")
            return 0.0
    
    def _calculate_weekly_savings(self, user_id: str) -> float:
        """Calculate weekly savings"""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            weekly_income = self.db.query(func.sum(PlaidTransaction.amount)).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.amount > 0,
                    PlaidTransaction.date >= week_ago
                )
            ).scalar()
            
            weekly_expenses = self.db.query(func.sum(func.abs(PlaidTransaction.amount))).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.amount < 0,
                    PlaidTransaction.date >= week_ago
                )
            ).scalar()
            
            income = float(weekly_income) if weekly_income else 0.0
            expenses = float(weekly_expenses) if weekly_expenses else 0.0
            
            return income - expenses
            
        except Exception as e:
            logger.error(f"Error calculating weekly savings: {e}")
            return 0.0
    
    def _calculate_goal_progress_rate(self, user_id: str) -> float:
        """Calculate goal progress rate (placeholder)"""
        # This would integrate with the savings goals service
        return 0.0
    
    def _calculate_transaction_frequency(self, user_id: str) -> float:
        """Calculate transaction frequency (transactions per day)"""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            transaction_count = self.db.query(func.count(PlaidTransaction.id)).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.date >= week_ago
                )
            ).scalar()
            
            return float(transaction_count) / 7.0  # Average per day
            
        except Exception as e:
            logger.error(f"Error calculating transaction frequency: {e}")
            return 0.0
    
    def _calculate_category_diversity(self, user_id: str) -> float:
        """Calculate category diversity (number of unique categories used)"""
        try:
            month_ago = datetime.utcnow() - timedelta(days=30)
            unique_categories = self.db.query(func.count(func.distinct(PlaidTransaction.category))).filter(
                and_(
                    PlaidTransaction.user_id == user_id,
                    PlaidTransaction.date >= month_ago
                )
            ).scalar()
            
            return float(unique_categories) if unique_categories else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating category diversity: {e}")
            return 0.0
    
    def _send_alert(self, alert: RealTimeAlert):
        """Send an alert to the user"""
        try:
            # Store alert in database
            self._store_alert(alert)
            
            # Send via WebSocket for real-time delivery
            self.websocket_service.send_alert(alert.user_id, alert)
            
            # Send email notification for critical alerts
            if alert.severity == AlertSeverity.CRITICAL:
                self.notification_service.send_email_alert(alert)
            
            # Send push notification for mobile app
            self.notification_service.send_push_notification(alert)
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def _store_alert(self, alert: RealTimeAlert):
        """Store alert in database"""
        try:
            # This would store the alert in the database
            # For now, we'll just cache it
            if alert.user_id not in self.alert_cache:
                self.alert_cache[alert.user_id] = []
            
            self.alert_cache[alert.user_id].append(alert)
            
            # Keep only the latest 50 alerts per user
            if len(self.alert_cache[alert.user_id]) > 50:
                self.alert_cache[alert.user_id] = self.alert_cache[alert.user_id][-50:]
                
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    def _send_transaction_notification(self, notification: TransactionNotification):
        """Send transaction notification"""
        try:
            # Send via WebSocket
            self.websocket_service.send_transaction_notification(notification.user_id, notification)
            
            # Send email for large transactions
            if notification.is_large_transaction:
                self.notification_service.send_transaction_email(notification)
                
        except Exception as e:
            logger.error(f"Error sending transaction notification: {e}")
    
    def get_user_alerts(self, user_id: str, limit: int = 20) -> List[RealTimeAlert]:
        """Get alerts for a user"""
        try:
            alerts = self.alert_cache.get(user_id, [])
            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
            
        except Exception as e:
            logger.error(f"Error getting alerts for user {user_id}: {e}")
            return []
    
    def mark_alert_read(self, user_id: str, alert_id: str):
        """Mark an alert as read"""
        try:
            alerts = self.alert_cache.get(user_id, [])
            for alert in alerts:
                if alert.alert_id == alert_id:
                    alert.is_read = True
                    break
                    
        except Exception as e:
            logger.error(f"Error marking alert as read: {e}")
    
    def get_user_metrics(self, user_id: str) -> Dict[str, float]:
        """Get performance metrics for a user"""
        try:
            return self.metric_cache.get(user_id, {})
            
        except Exception as e:
            logger.error(f"Error getting metrics for user {user_id}: {e}")
            return {}
    
    def get_live_balance(self, user_id: str) -> List[BalanceUpdate]:
        """Get live balance updates for a user"""
        try:
            accounts = self.db.query(PlaidAccount).filter(
                and_(
                    PlaidAccount.user_id == user_id,
                    PlaidAccount.is_active == True
                )
            ).all()
            
            balance_updates = []
            for account in accounts:
                current_balance = self._get_current_balance(account.id)
                previous_balance = self.balance_cache.get(account.id, current_balance)
                
                if previous_balance != current_balance:
                    change_amount = current_balance - previous_balance
                    change_percentage = (change_amount / previous_balance * 100) if previous_balance > 0 else 0
                    
                    update = BalanceUpdate(
                        account_id=account.id,
                        user_id=user_id,
                        previous_balance=previous_balance,
                        current_balance=current_balance,
                        change_amount=change_amount,
                        change_percentage=change_percentage,
                        timestamp=datetime.utcnow()
                    )
                    balance_updates.append(update)
                    
                    # Update cache
                    self.balance_cache[account.id] = current_balance
            
            return balance_updates
            
        except Exception as e:
            logger.error(f"Error getting live balance for user {user_id}: {e}")
            return [] 