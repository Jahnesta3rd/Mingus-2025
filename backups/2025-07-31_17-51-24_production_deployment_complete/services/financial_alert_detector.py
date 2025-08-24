import logging
import json
import redis
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import uuid

# Import existing services and models
from .communication_router import communication_router, MessageType, UrgencyLevel, CommunicationMessage
from .twilio_sms_service import twilio_sms_service
from .resend_email_service import resend_email_service
from ..models.financial_alerts import (
    FinancialAlert, UserFinancialContext, AlertRule, CashFlowForecast, 
    SpendingPattern, AlertDeliveryLog
)

logger = logging.getLogger(__name__)

class AlertTriggerType(Enum):
    """Types of alert triggers"""
    CASH_FLOW_NEGATIVE = "cash_flow_negative"
    BILL_PAYMENT_UPCOMING = "bill_payment_upcoming"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    UNUSUAL_SPENDING = "unusual_spending"
    BUDGET_EXCEEDED = "budget_exceeded"
    EMERGENCY_FUND_LOW = "emergency_fund_low"
    STUDENT_LOAN_DUE = "student_loan_due"
    FAMILY_OBLIGATION = "family_obligation"

@dataclass
class AlertTrigger:
    """Alert trigger configuration"""
    trigger_type: AlertTriggerType
    urgency_level: UrgencyLevel
    message_type: MessageType
    advance_notice_days: int = 0
    threshold_percentage: float = 0.0
    threshold_amount: float = 0.0

class FinancialAlertDetector:
    """Financial alert detection system for MINGUS"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.redis_client = communication_router.redis_client
        
        # Alert trigger configurations
        self.alert_triggers = {
            AlertTriggerType.CASH_FLOW_NEGATIVE: AlertTrigger(
                trigger_type=AlertTriggerType.CASH_FLOW_NEGATIVE,
                urgency_level=UrgencyLevel.CRITICAL,
                message_type=MessageType.FINANCIAL_ALERT,
                advance_notice_days=7
            ),
            AlertTriggerType.BILL_PAYMENT_UPCOMING: AlertTrigger(
                trigger_type=AlertTriggerType.BILL_PAYMENT_UPCOMING,
                urgency_level=UrgencyLevel.HIGH,
                message_type=MessageType.PAYMENT_REMINDER,
                advance_notice_days=3
            ),
            AlertTriggerType.SUBSCRIPTION_RENEWAL: AlertTrigger(
                trigger_type=AlertTriggerType.SUBSCRIPTION_RENEWAL,
                urgency_level=UrgencyLevel.MEDIUM,
                message_type=MessageType.PAYMENT_REMINDER,
                advance_notice_days=2
            ),
            AlertTriggerType.UNUSUAL_SPENDING: AlertTrigger(
                trigger_type=AlertTriggerType.UNUSUAL_SPENDING,
                urgency_level=UrgencyLevel.MEDIUM,
                message_type=MessageType.DETAILED_ANALYSIS,
                threshold_percentage=50.0  # 50% above average
            ),
            AlertTriggerType.BUDGET_EXCEEDED: AlertTrigger(
                trigger_type=AlertTriggerType.BUDGET_EXCEEDED,
                urgency_level=UrgencyLevel.HIGH,
                message_type=MessageType.FINANCIAL_ALERT,
                threshold_percentage=20.0  # 20% over budget
            ),
            AlertTriggerType.EMERGENCY_FUND_LOW: AlertTrigger(
                trigger_type=AlertTriggerType.EMERGENCY_FUND_LOW,
                urgency_level=UrgencyLevel.MEDIUM,
                message_type=MessageType.FINANCIAL_ALERT,
                threshold_percentage=25.0  # Below 25% of target
            ),
            AlertTriggerType.STUDENT_LOAN_DUE: AlertTrigger(
                trigger_type=AlertTriggerType.STUDENT_LOAN_DUE,
                urgency_level=UrgencyLevel.HIGH,
                message_type=MessageType.PAYMENT_REMINDER,
                advance_notice_days=3
            ),
            AlertTriggerType.FAMILY_OBLIGATION: AlertTrigger(
                trigger_type=AlertTriggerType.FAMILY_OBLIGATION,
                urgency_level=UrgencyLevel.MEDIUM,
                message_type=MessageType.PAYMENT_REMINDER,
                advance_notice_days=2
            )
        }
        
        # Regional cost of living adjustments
        self.regional_adjustments = {
            'atlanta': {'cost_multiplier': 1.0, 'rent_multiplier': 1.0},
            'houston': {'cost_multiplier': 0.95, 'rent_multiplier': 0.9},
            'dc_metro': {'cost_multiplier': 1.3, 'rent_multiplier': 1.4},
            'new_york': {'cost_multiplier': 1.5, 'rent_multiplier': 1.8},
            'los_angeles': {'cost_multiplier': 1.4, 'rent_multiplier': 1.6},
            'chicago': {'cost_multiplier': 1.1, 'rent_multiplier': 1.2},
            'miami': {'cost_multiplier': 1.1, 'rent_multiplier': 1.3},
            'dallas': {'cost_multiplier': 0.9, 'rent_multiplier': 0.85}
        }
    
    def detect_alerts(self, user_id: str) -> List[FinancialAlert]:
        """
        Detect financial alerts for a user
        
        Args:
            user_id: User ID to check for alerts
        
        Returns:
            List of detected financial alerts
        """
        try:
            alerts = []
            
            # Get user financial context
            user_context = self._get_user_financial_context(user_id)
            if not user_context:
                logger.warning(f"No financial context found for user {user_id}")
                return alerts
            
            # Check cash flow alerts
            cash_flow_alerts = self._detect_cash_flow_alerts(user_id, user_context)
            alerts.extend(cash_flow_alerts)
            
            # Check bill payment alerts
            bill_alerts = self._detect_bill_payment_alerts(user_id, user_context)
            alerts.extend(bill_alerts)
            
            # Check subscription alerts
            subscription_alerts = self._detect_subscription_alerts(user_id, user_context)
            alerts.extend(subscription_alerts)
            
            # Check spending pattern alerts
            spending_alerts = self._detect_spending_pattern_alerts(user_id, user_context)
            alerts.extend(spending_alerts)
            
            # Check budget alerts
            budget_alerts = self._detect_budget_alerts(user_id, user_context)
            alerts.extend(budget_alerts)
            
            # Check emergency fund alerts
            emergency_alerts = self._detect_emergency_fund_alerts(user_id, user_context)
            alerts.extend(emergency_alerts)
            
            # Save alerts to database
            for alert in alerts:
                self.db.add(alert)
            
            self.db.commit()
            
            logger.info(f"Detected {len(alerts)} alerts for user {user_id}")
            return alerts
            
        except Exception as e:
            logger.error(f"Error detecting alerts for user {user_id}: {e}")
            self.db.rollback()
            return []
    
    def _detect_cash_flow_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]:
        """Detect cash flow alerts (negative balance warnings)"""
        alerts = []
        
        try:
            # Get latest cash flow forecast
            latest_forecast = self.db.query(CashFlowForecast).filter(
                CashFlowForecast.user_id == user_id
            ).order_by(CashFlowForecast.forecast_date.desc()).first()
            
            if not latest_forecast:
                return alerts
            
            # Check if balance will go negative within 7 days
            if latest_forecast.days_until_negative and latest_forecast.days_until_negative <= 7:
                # Check if we already sent an alert for this
                existing_alert = self.db.query(FinancialAlert).filter(
                    and_(
                        FinancialAlert.user_id == user_id,
                        FinancialAlert.alert_type == 'cash_flow',
                        FinancialAlert.alert_subtype == 'negative_balance',
                        FinancialAlert.status.in_(['pending', 'sent', 'delivered']),
                        FinancialAlert.created_at >= datetime.utcnow() - timedelta(days=1)
                    )
                ).first()
                
                if not existing_alert:
                    alert = self._create_cash_flow_alert(
                        user_id, user_context, latest_forecast
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error detecting cash flow alerts: {e}")
            return alerts
    
    def _detect_bill_payment_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]:
        """Detect bill payment alerts"""
        alerts = []
        
        try:
            today = datetime.utcnow().date()
            
            # Check rent/mortgage payments
            if user_context.rent_mortgage_due_date:
                days_until_rent = self._days_until_payment(today, user_context.rent_mortgage_due_date)
                if 2 <= days_until_rent <= 3:
                    alert = self._create_bill_payment_alert(
                        user_id, user_context, 'rent_mortgage', 
                        user_context.rent_mortgage, days_until_rent
                    )
                    alerts.append(alert)
            
            # Check student loan payments
            if user_context.student_loan_payment and user_context.student_loan_due_date:
                days_until_loan = self._days_until_payment(today, user_context.student_loan_due_date)
                if 2 <= days_until_loan <= 3:
                    alert = self._create_bill_payment_alert(
                        user_id, user_context, 'student_loan',
                        user_context.student_loan_payment, days_until_loan
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error detecting bill payment alerts: {e}")
            return alerts
    
    def _detect_subscription_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]:
        """Detect subscription renewal alerts"""
        alerts = []
        
        try:
            # This would typically query subscription data from Stripe or similar
            # For now, we'll use a placeholder approach
            
            # Check if user has active subscriptions
            # In a real implementation, this would query the subscription service
            active_subscriptions = self._get_active_subscriptions(user_id)
            
            for subscription in active_subscriptions:
                days_until_renewal = (subscription['next_billing_date'] - datetime.utcnow().date()).days
                
                if 1 <= days_until_renewal <= 2:
                    alert = self._create_subscription_alert(
                        user_id, user_context, subscription
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error detecting subscription alerts: {e}")
            return alerts
    
    def _detect_spending_pattern_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]:
        """Detect unusual spending pattern alerts"""
        alerts = []
        
        try:
            # Get spending patterns with anomalies
            anomaly_patterns = self.db.query(SpendingPattern).filter(
                and_(
                    SpendingPattern.user_id == user_id,
                    SpendingPattern.is_anomaly == True,
                    SpendingPattern.anomaly_score >= 0.7  # High confidence anomaly
                )
            ).all()
            
            for pattern in anomaly_patterns:
                # Check if we already sent an alert for this anomaly
                existing_alert = self.db.query(FinancialAlert).filter(
                    and_(
                        FinancialAlert.user_id == user_id,
                        FinancialAlert.alert_type == 'spending_pattern',
                        FinancialAlert.alert_subtype == pattern.category,
                        FinancialAlert.status.in_(['pending', 'sent', 'delivered']),
                        FinancialAlert.created_at >= datetime.utcnow() - timedelta(days=7)
                    )
                ).first()
                
                if not existing_alert:
                    alert = self._create_spending_pattern_alert(
                        user_id, user_context, pattern
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error detecting spending pattern alerts: {e}")
            return alerts
    
    def _detect_budget_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]:
        """Detect budget exceeded alerts"""
        alerts = []
        
        try:
            # Get current month's spending vs budget
            current_month = datetime.utcnow().replace(day=1)
            
            # This would typically query actual spending data
            # For now, we'll use a placeholder approach
            monthly_spending = self._get_monthly_spending(user_id, current_month)
            spending_categories = user_context.spending_categories or {}
            
            for category, budget in spending_categories.items():
                if category in monthly_spending:
                    spent = monthly_spending[category]
                    if spent > budget * 1.2:  # 20% over budget
                        alert = self._create_budget_alert(
                            user_id, user_context, category, spent, budget
                        )
                        alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error detecting budget alerts: {e}")
            return alerts
    
    def _detect_emergency_fund_alerts(self, user_id: str, user_context: UserFinancialContext) -> List[FinancialAlert]:
        """Detect emergency fund alerts"""
        alerts = []
        
        try:
            if user_context.emergency_fund_balance and user_context.emergency_fund_target:
                fund_percentage = (user_context.emergency_fund_balance / user_context.emergency_fund_target) * 100
                
                if fund_percentage < 25:  # Below 25% of target
                    # Check if we already sent an alert recently
                    existing_alert = self.db.query(FinancialAlert).filter(
                        and_(
                            FinancialAlert.user_id == user_id,
                            FinancialAlert.alert_type == 'emergency_fund',
                            FinancialAlert.status.in_(['pending', 'sent', 'delivered']),
                            FinancialAlert.created_at >= datetime.utcnow() - timedelta(days=30)
                        )
                    ).first()
                    
                    if not existing_alert:
                        alert = self._create_emergency_fund_alert(
                            user_id, user_context, fund_percentage
                        )
                        alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error detecting emergency fund alerts: {e}")
            return alerts
    
    def _create_cash_flow_alert(self, user_id: str, user_context: UserFinancialContext, 
                               forecast: CashFlowForecast) -> FinancialAlert:
        """Create cash flow alert"""
        days_until_negative = forecast.days_until_negative or 0
        negative_amount = forecast.negative_balance_amount or 0
        
        # Personalize message based on user context
        message = self._personalize_cash_flow_message(user_context, days_until_negative, negative_amount)
        
        alert = FinancialAlert(
            user_id=user_id,
            alert_type='cash_flow',
            alert_subtype='negative_balance',
            urgency_level='critical',
            trigger_amount=negative_amount,
            current_balance=forecast.projected_balance,
            projected_balance=forecast.projected_balance,
            days_until_negative=days_until_negative,
            title=f"⚠️ Cash Flow Alert: Balance Going Negative in {days_until_negative} Days",
            message=message,
            sms_message=f"⚠️ MINGUS Alert: Your balance will go negative in {days_until_negative} days. Current: ${forecast.projected_balance:.2f}. Consider transferring funds.",
            communication_channel='sms',
            status='pending',
            metadata={
                'forecast_id': str(forecast.id),
                'risk_level': forecast.risk_level,
                'confidence_level': forecast.confidence_level
            }
        )
        
        return alert
    
    def _create_bill_payment_alert(self, user_id: str, user_context: UserFinancialContext, 
                                  bill_type: str, amount: float, days_until_due: int) -> FinancialAlert:
        """Create bill payment alert"""
        bill_names = {
            'rent_mortgage': 'Rent/Mortgage',
            'student_loan': 'Student Loan',
            'family_obligation': 'Family Support'
        }
        
        bill_name = bill_names.get(bill_type, bill_type.title())
        
        # Personalize message based on user context
        message = self._personalize_bill_payment_message(user_context, bill_name, amount, days_until_due)
        
        alert = FinancialAlert(
            user_id=user_id,
            alert_type='bill_payment',
            alert_subtype=bill_type,
            urgency_level='high',
            trigger_amount=amount,
            due_date=datetime.utcnow() + timedelta(days=days_until_due),
            title=f"📅 {bill_name} Payment Due in {days_until_due} Days",
            message=message,
            sms_message=f"📅 MINGUS Reminder: Your {bill_name} payment of ${amount:.2f} is due in {days_until_due} days. Set up autopay to never miss a payment.",
            communication_channel='sms',
            status='pending',
            metadata={
                'bill_type': bill_type,
                'amount': amount,
                'days_until_due': days_until_due
            }
        )
        
        return alert
    
    def _create_subscription_alert(self, user_id: str, user_context: UserFinancialContext, 
                                  subscription: Dict[str, Any]) -> FinancialAlert:
        """Create subscription renewal alert"""
        subscription_name = subscription.get('name', 'Subscription')
        amount = subscription.get('amount', 0)
        days_until_renewal = subscription.get('days_until_renewal', 0)
        
        alert = FinancialAlert(
            user_id=user_id,
            alert_type='subscription',
            alert_subtype='renewal',
            urgency_level='medium',
            trigger_amount=amount,
            due_date=datetime.utcnow() + timedelta(days=days_until_renewal),
            title=f"🔄 {subscription_name} Renewal in {days_until_renewal} Days",
            message=f"Your {subscription_name} subscription will renew in {days_until_renewal} days for ${amount:.2f}. Review your subscription settings if needed.",
            sms_message=f"🔄 MINGUS: Your {subscription_name} subscription renews in {days_until_renewal} days for ${amount:.2f}.",
            communication_channel='sms',
            status='pending',
            metadata=subscription
        )
        
        return alert
    
    def _create_spending_pattern_alert(self, user_id: str, user_context: UserFinancialContext, 
                                      pattern: SpendingPattern) -> FinancialAlert:
        """Create spending pattern alert"""
        category = pattern.category
        average = pattern.average_amount
        anomaly_score = pattern.anomaly_score or 0
        
        alert = FinancialAlert(
            user_id=user_id,
            alert_type='spending_pattern',
            alert_subtype=category,
            urgency_level='medium',
            trigger_amount=average,
            title=f"📊 Unusual {category.title()} Spending Detected",
            message=f"We detected unusual spending in your {category} category. This is {anomaly_score:.0%} higher than your typical pattern. Review your recent transactions.",
            email_subject=f"MINGUS Alert: Unusual {category.title()} Spending",
            email_content=self._create_spending_pattern_email_content(category, pattern),
            communication_channel='email',
            status='pending',
            metadata={
                'category': category,
                'average_amount': average,
                'anomaly_score': anomaly_score,
                'pattern_type': pattern.pattern_type
            }
        )
        
        return alert
    
    def _create_budget_alert(self, user_id: str, user_context: UserFinancialContext, 
                            category: str, spent: float, budget: float) -> FinancialAlert:
        """Create budget exceeded alert"""
        overage_percentage = ((spent - budget) / budget) * 100
        
        alert = FinancialAlert(
            user_id=user_id,
            alert_type='budget_exceeded',
            alert_subtype=category,
            urgency_level='high',
            trigger_amount=spent,
            title=f"💰 {category.title()} Budget Exceeded by {overage_percentage:.0%}",
            message=f"You've exceeded your {category} budget by {overage_percentage:.0%}. Spent: ${spent:.2f}, Budget: ${budget:.2f}.",
            sms_message=f"💰 MINGUS Alert: Your {category} spending is {overage_percentage:.0%} over budget. Spent: ${spent:.2f}, Budget: ${budget:.2f}.",
            communication_channel='both',
            status='pending',
            metadata={
                'category': category,
                'spent': spent,
                'budget': budget,
                'overage_percentage': overage_percentage
            }
        )
        
        return alert
    
    def _create_emergency_fund_alert(self, user_id: str, user_context: UserFinancialContext, 
                                    fund_percentage: float) -> FinancialAlert:
        """Create emergency fund alert"""
        alert = FinancialAlert(
            user_id=user_id,
            alert_type='emergency_fund',
            alert_subtype='low_balance',
            urgency_level='medium',
            trigger_amount=user_context.emergency_fund_balance or 0,
            title=f"🛡️ Emergency Fund Below {fund_percentage:.0%} of Target",
            message=f"Your emergency fund is at {fund_percentage:.0%} of your target. Consider building it up to protect against unexpected expenses.",
            email_subject="MINGUS: Emergency Fund Alert",
            email_content=self._create_emergency_fund_email_content(user_context, fund_percentage),
            communication_channel='email',
            status='pending',
            metadata={
                'fund_percentage': fund_percentage,
                'current_balance': user_context.emergency_fund_balance,
                'target_balance': user_context.emergency_fund_target
            }
        )
        
        return alert
    
    def _personalize_cash_flow_message(self, user_context: UserFinancialContext, 
                                      days_until_negative: int, negative_amount: float) -> str:
        """Personalize cash flow message based on user context"""
        base_message = f"Your account balance will go negative in {days_until_negative} days."
        
        # Add context based on income sources
        if user_context.primary_income_source == 'gig_work':
            base_message += " Consider picking up additional gig work or adjusting your schedule."
        elif user_context.primary_income_source == 'full_time':
            base_message += " Check if you have any pending reimbursements or bonuses."
        
        # Add family context
        if user_context.family_obligations:
            base_message += f" Remember you have ${user_context.family_obligations:.2f} in family obligations this month."
        
        # Add regional context
        if user_context.regional_cost_of_living:
            region_name = user_context.regional_cost_of_living.replace('_', ' ').title()
            base_message += f" Living in {region_name} can be expensive - consider reviewing your spending categories."
        
        return base_message
    
    def _personalize_bill_payment_message(self, user_context: UserFinancialContext, 
                                         bill_name: str, amount: float, days_until_due: int) -> str:
        """Personalize bill payment message based on user context"""
        base_message = f"Your {bill_name} payment of ${amount:.2f} is due in {days_until_due} days."
        
        # Add student loan specific context
        if bill_name == 'Student Loan':
            base_message += " Consider income-driven repayment options if you're struggling with payments."
        
        # Add family obligation context
        if bill_name == 'Family Support':
            base_message += " Family support is important - consider setting up automatic transfers."
        
        # Add income context
        if user_context.income_frequency == 'weekly':
            base_message += " Since you're paid weekly, you may want to set aside funds each week."
        elif user_context.income_frequency == 'bi_weekly':
            base_message += " Since you're paid bi-weekly, plan your payment around your pay schedule."
        
        return base_message
    
    def _create_spending_pattern_email_content(self, category: str, pattern: SpendingPattern) -> str:
        """Create detailed email content for spending pattern alerts"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #d32f2f;">📊 Unusual {category.title()} Spending Detected</h2>
            
            <p>We detected unusual spending in your {category} category that's worth reviewing.</p>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Spending Analysis</h3>
                <ul>
                    <li><strong>Category:</strong> {category.title()}</li>
                    <li><strong>Your Average:</strong> ${pattern.average_amount:.2f}</li>
                    <li><strong>Anomaly Score:</strong> {pattern.anomaly_score:.0%} above normal</li>
                    <li><strong>Pattern Type:</strong> {pattern.pattern_type.title()}</li>
                </ul>
            </div>
            
            <p><strong>What to do:</strong></p>
            <ul>
                <li>Review your recent transactions in this category</li>
                <li>Check if this is a legitimate expense</li>
                <li>Consider if this fits your financial goals</li>
                <li>Update your budget if needed</li>
            </ul>
            
            <p>Remember, we're here to help you build wealth while maintaining healthy relationships.</p>
            
            <p>Best regards,<br>The MINGUS Team</p>
        </div>
        """
    
    def _create_emergency_fund_email_content(self, user_context: UserFinancialContext, 
                                            fund_percentage: float) -> str:
        """Create detailed email content for emergency fund alerts"""
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ff9800;">🛡️ Emergency Fund Alert</h2>
            
            <p>Your emergency fund is currently at {fund_percentage:.0%} of your target.</p>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Emergency Fund Status</h3>
                <ul>
                    <li><strong>Current Balance:</strong> ${user_context.emergency_fund_balance:.2f}</li>
                    <li><strong>Target Balance:</strong> ${user_context.emergency_fund_target:.2f}</li>
                    <li><strong>Percentage:</strong> {fund_percentage:.0%}</li>
                </ul>
            </div>
            
            <p><strong>Why this matters:</strong></p>
            <ul>
                <li>Emergency funds protect against unexpected expenses</li>
                <li>They prevent you from going into debt</li>
                <li>They provide peace of mind</li>
                <li>They're especially important for African American professionals building wealth</li>
            </ul>
            
            <p><strong>Next steps:</strong></p>
            <ul>
                <li>Set up automatic transfers to your emergency fund</li>
                <li>Aim to save 3-6 months of expenses</li>
                <li>Consider your family obligations in your target</li>
                <li>Review your budget to find additional savings</li>
            </ul>
            
            <p>We're here to support your financial wellness journey!</p>
            
            <p>Best regards,<br>The MINGUS Team</p>
        </div>
        """
    
    def _get_user_financial_context(self, user_id: str) -> Optional[UserFinancialContext]:
        """Get user financial context"""
        return self.db.query(UserFinancialContext).filter(
            UserFinancialContext.user_id == user_id
        ).first()
    
    def _days_until_payment(self, today: datetime.date, due_day: int) -> int:
        """Calculate days until payment is due"""
        current_month = today.replace(day=due_day)
        if current_month < today:
            # Payment is due next month
            if today.month == 12:
                current_month = today.replace(year=today.year + 1, month=1, day=due_day)
            else:
                current_month = today.replace(month=today.month + 1, day=due_day)
        
        return (current_month - today).days
    
    def _get_active_subscriptions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active subscriptions for user (placeholder)"""
        # This would typically query Stripe or similar service
        # For now, return empty list
        return []
    
    def _get_monthly_spending(self, user_id: str, month: datetime) -> Dict[str, float]:
        """Get monthly spending by category (placeholder)"""
        # This would typically query transaction data
        # For now, return empty dict
        return {}

# Create singleton instance
financial_alert_detector = None  # Will be initialized with db session 