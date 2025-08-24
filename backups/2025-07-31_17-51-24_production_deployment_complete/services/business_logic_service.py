"""
Business Logic Service for Webhook Events
========================================

Comprehensive service for handling business logic in webhook events,
including feature access control updates and user notifications for billing events.

Features:
- Feature access control management
- User notification system for billing events
- Subscription lifecycle management
- Payment status tracking
- Customer communication management

Author: MINGUS Development Team
Date: January 2025
"""

import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.subscription import Customer, Subscription, PricingTier, BillingHistory, FeatureAccess
from ..models.user import User
from ..services.notification_service import NotificationService
from ..services.email_service import EmailService
from ..config.base import Config

logger = logging.getLogger(__name__)


class FeatureAccessLevel(Enum):
    """Feature access levels"""
    NONE = "none"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    UNLIMITED = "unlimited"


class NotificationType(Enum):
    """Notification types for billing events"""
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    TRIAL_ENDING = "trial_ending"
    INVOICE_UPCOMING = "invoice_upcoming"
    PAYMENT_METHOD_EXPIRING = "payment_method_expiring"
    SUBSCRIPTION_REACTIVATED = "subscription_reactivated"
    FEATURE_ACCESS_UPDATED = "feature_access_updated"


class BillingEventType(Enum):
    """Billing event types"""
    SUBSCRIPTION_START = "subscription_start"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    SUBSCRIPTION_DOWNGRADE = "subscription_downgrade"
    SUBSCRIPTION_CANCELLATION = "subscription_cancellation"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILURE = "payment_failure"
    TRIAL_END = "trial_end"
    INVOICE_DUE = "invoice_due"
    PAYMENT_METHOD_UPDATE = "payment_method_update"


@dataclass
class FeatureAccessUpdate:
    """Feature access update information"""
    customer_id: str
    subscription_id: str
    old_tier: Optional[str]
    new_tier: str
    features_added: List[str]
    features_removed: List[str]
    access_level: FeatureAccessLevel
    effective_date: datetime
    reason: str


@dataclass
class UserNotification:
    """User notification information"""
    user_id: str
    customer_id: str
    notification_type: NotificationType
    subject: str
    message: str
    priority: str  # low, medium, high, urgent
    channels: List[str]  # email, sms, push, in_app
    metadata: Dict[str, Any]
    scheduled_at: Optional[datetime] = None


class BusinessLogicService:
    """Comprehensive business logic service for webhook events"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Initialize services
        self.notification_service = NotificationService(db_session, config)
        self.email_service = EmailService(config)
        
        # Feature access configuration
        self.feature_configs = {
            'basic': {
                'features': ['basic_analytics', 'standard_reports', 'email_support'],
                'limits': {
                    'api_calls_per_month': 1000,
                    'storage_gb': 5,
                    'users': 1
                }
            },
            'premium': {
                'features': ['advanced_analytics', 'custom_reports', 'priority_support', 'api_access'],
                'limits': {
                    'api_calls_per_month': 10000,
                    'storage_gb': 50,
                    'users': 5
                }
            },
            'enterprise': {
                'features': ['enterprise_analytics', 'white_label_reports', 'dedicated_support', 'api_access', 'custom_integrations'],
                'limits': {
                    'api_calls_per_month': 100000,
                    'storage_gb': 500,
                    'users': 25
                }
            },
            'unlimited': {
                'features': ['unlimited_analytics', 'unlimited_reports', 'dedicated_support', 'api_access', 'custom_integrations', 'premium_features'],
                'limits': {
                    'api_calls_per_month': -1,  # Unlimited
                    'storage_gb': -1,  # Unlimited
                    'users': -1  # Unlimited
                }
            }
        }
        
        # Notification templates
        self.notification_templates = self._load_notification_templates()
    
    def handle_subscription_created(self, customer: Customer, subscription: Subscription, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle business logic for subscription creation"""
        try:
            changes = []
            notifications_sent = 0
            
            # Step 1: Update feature access
            feature_update = self._update_feature_access_for_subscription(
                customer, subscription, subscription_data
            )
            changes.append(f"Feature access updated: {feature_update.reason}")
            
            # Step 2: Send welcome notifications
            welcome_notifications = self._send_subscription_welcome_notifications(
                customer, subscription, subscription_data
            )
            notifications_sent += len(welcome_notifications)
            changes.append(f"Welcome notifications sent: {len(welcome_notifications)}")
            
            # Step 3: Setup trial notifications if applicable
            if subscription.trial_end:
                trial_notifications = self._setup_trial_notifications(
                    customer, subscription, subscription_data
                )
                notifications_sent += len(trial_notifications)
                changes.append(f"Trial notifications scheduled: {len(trial_notifications)}")
            
            # Step 4: Update customer status
            self._update_customer_status_for_new_subscription(customer, subscription)
            changes.append("Customer status updated")
            
            # Step 5: Track business metrics
            self._track_subscription_creation_metrics(customer, subscription, subscription_data)
            changes.append("Business metrics tracked")
            
            return {
                'success': True,
                'changes': changes,
                'notifications_sent': notifications_sent,
                'feature_update': feature_update,
                'message': f"Subscription created successfully with {notifications_sent} notifications sent"
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription creation: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def handle_subscription_updated(self, customer: Customer, subscription: Subscription, old_values: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle business logic for subscription updates"""
        try:
            changes = []
            notifications_sent = 0
            
            # Step 1: Check for pricing tier changes
            if 'pricing_tier' in old_values and old_values['pricing_tier'] != subscription.pricing_tier:
                tier_changes = self._handle_pricing_tier_change(
                    customer, subscription, old_values['pricing_tier'], subscription.pricing_tier
                )
                changes.extend(tier_changes['changes'])
                notifications_sent += tier_changes['notifications_sent']
            
            # Step 2: Check for status changes
            if 'status' in old_values and old_values['status'] != subscription.status:
                status_changes = self._handle_status_change(
                    customer, subscription, old_values['status'], subscription.status
                )
                changes.extend(status_changes['changes'])
                notifications_sent += status_changes['notifications_sent']
            
            # Step 3: Check for billing cycle changes
            if 'billing_cycle' in old_values and old_values['billing_cycle'] != subscription.billing_cycle:
                billing_changes = self._handle_billing_cycle_change(
                    customer, subscription, old_values['billing_cycle'], subscription.billing_cycle
                )
                changes.extend(billing_changes['changes'])
                notifications_sent += billing_changes['notifications_sent']
            
            # Step 4: Update feature access if needed
            if any(key in old_values for key in ['pricing_tier', 'status']):
                feature_update = self._update_feature_access_for_subscription(
                    customer, subscription, new_data
                )
                changes.append(f"Feature access updated: {feature_update.reason}")
            
            # Step 5: Track business metrics
            self._track_subscription_update_metrics(customer, subscription, old_values, new_data)
            changes.append("Business metrics tracked")
            
            return {
                'success': True,
                'changes': changes,
                'notifications_sent': notifications_sent,
                'message': f"Subscription updated successfully with {notifications_sent} notifications sent"
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def handle_subscription_cancelled(self, customer: Customer, subscription: Subscription, cancellation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle business logic for subscription cancellation"""
        try:
            changes = []
            notifications_sent = 0
            
            # Step 1: Update feature access to basic/free tier
            feature_update = self._downgrade_feature_access_for_cancellation(
                customer, subscription, cancellation_data
            )
            changes.append(f"Feature access downgraded: {feature_update.reason}")
            
            # Step 2: Send cancellation notifications
            cancellation_notifications = self._send_cancellation_notifications(
                customer, subscription, cancellation_data
            )
            notifications_sent += len(cancellation_notifications)
            changes.append(f"Cancellation notifications sent: {len(cancellation_notifications)}")
            
            # Step 3: Setup reactivation offers if applicable
            if self._should_offer_reactivation(customer, subscription, cancellation_data):
                reactivation_notifications = self._setup_reactivation_offers(
                    customer, subscription, cancellation_data
                )
                notifications_sent += len(reactivation_notifications)
                changes.append(f"Reactivation offers scheduled: {len(reactivation_notifications)}")
            
            # Step 4: Update customer status
            self._update_customer_status_for_cancellation(customer, subscription)
            changes.append("Customer status updated")
            
            # Step 5: Track business metrics
            self._track_cancellation_metrics(customer, subscription, cancellation_data)
            changes.append("Business metrics tracked")
            
            return {
                'success': True,
                'changes': changes,
                'notifications_sent': notifications_sent,
                'feature_update': feature_update,
                'message': f"Subscription cancelled successfully with {notifications_sent} notifications sent"
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def handle_payment_succeeded(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle business logic for successful payments"""
        try:
            changes = []
            notifications_sent = 0
            
            # Step 1: Update subscription status if needed
            if customer.subscription and customer.subscription.status != 'active':
                self._reactivate_subscription_for_payment(customer, billing_record)
                changes.append("Subscription reactivated")
            
            # Step 2: Send payment confirmation
            payment_notifications = self._send_payment_success_notifications(
                customer, billing_record, payment_data
            )
            notifications_sent += len(payment_notifications)
            changes.append(f"Payment confirmation sent: {len(payment_notifications)}")
            
            # Step 3: Update customer payment status
            self._update_customer_payment_status(customer, billing_record)
            changes.append("Customer payment status updated")
            
            # Step 4: Track payment metrics
            self._track_payment_success_metrics(customer, billing_record, payment_data)
            changes.append("Payment metrics tracked")
            
            return {
                'success': True,
                'changes': changes,
                'notifications_sent': notifications_sent,
                'message': f"Payment processed successfully with {notifications_sent} notifications sent"
            }
            
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def handle_payment_failed(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle business logic for failed payments"""
        try:
            changes = []
            notifications_sent = 0
            
            # Step 1: Update subscription status
            if customer.subscription:
                self._handle_subscription_for_failed_payment(customer, billing_record)
                changes.append("Subscription status updated for failed payment")
            
            # Step 2: Send payment failure notifications
            failure_notifications = self._send_payment_failure_notifications(
                customer, billing_record, payment_data
            )
            notifications_sent += len(failure_notifications)
            changes.append(f"Payment failure notifications sent: {len(failure_notifications)}")
            
            # Step 3: Setup retry notifications
            retry_notifications = self._setup_payment_retry_notifications(
                customer, billing_record, payment_data
            )
            notifications_sent += len(retry_notifications)
            changes.append(f"Payment retry notifications scheduled: {len(retry_notifications)}")
            
            # Step 4: Update customer payment status
            self._update_customer_payment_status_for_failure(customer, billing_record)
            changes.append("Customer payment status updated")
            
            # Step 5: Track failure metrics
            self._track_payment_failure_metrics(customer, billing_record, payment_data)
            changes.append("Payment failure metrics tracked")
            
            return {
                'success': True,
                'changes': changes,
                'notifications_sent': notifications_sent,
                'message': f"Payment failure handled with {notifications_sent} notifications sent"
            }
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def handle_trial_ending(self, customer: Customer, subscription: Subscription, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle business logic for trial ending"""
        try:
            changes = []
            notifications_sent = 0
            
            # Step 1: Send trial ending notifications
            trial_notifications = self._send_trial_ending_notifications(
                customer, subscription, trial_data
            )
            notifications_sent += len(trial_notifications)
            changes.append(f"Trial ending notifications sent: {len(trial_notifications)}")
            
            # Step 2: Setup conversion offers
            conversion_notifications = self._setup_trial_conversion_offers(
                customer, subscription, trial_data
            )
            notifications_sent += len(conversion_notifications)
            changes.append(f"Conversion offers scheduled: {len(conversion_notifications)}")
            
            # Step 3: Update customer trial status
            self._update_customer_trial_status(customer, subscription)
            changes.append("Customer trial status updated")
            
            # Step 4: Track trial metrics
            self._track_trial_ending_metrics(customer, subscription, trial_data)
            changes.append("Trial metrics tracked")
            
            return {
                'success': True,
                'changes': changes,
                'notifications_sent': notifications_sent,
                'message': f"Trial ending handled with {notifications_sent} notifications sent"
            }
            
        except Exception as e:
            logger.error(f"Error handling trial ending: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    # Feature Access Control Methods
    
    def _update_feature_access_for_subscription(self, customer: Customer, subscription: Subscription, subscription_data: Dict[str, Any]) -> FeatureAccessUpdate:
        """Update feature access based on subscription"""
        try:
            # Get current feature access
            current_access = self.db.query(FeatureAccess).filter(
                FeatureAccess.customer_id == customer.id
            ).first()
            
            # Determine new tier and features
            new_tier = subscription.pricing_tier or 'basic'
            tier_config = self.feature_configs.get(new_tier, self.feature_configs['basic'])
            
            # Calculate feature changes
            old_features = set(current_access.features if current_access else [])
            new_features = set(tier_config['features'])
            
            features_added = list(new_features - old_features)
            features_removed = list(old_features - new_features)
            
            # Update or create feature access record
            if current_access:
                current_access.features = list(new_features)
                current_access.access_level = FeatureAccessLevel(new_tier.upper())
                current_access.updated_at = datetime.now(timezone.utc)
                current_access.subscription_id = subscription.id
            else:
                current_access = FeatureAccess(
                    customer_id=customer.id,
                    subscription_id=subscription.id,
                    features=list(new_features),
                    access_level=FeatureAccessLevel(new_tier.upper()),
                    limits=tier_config['limits']
                )
                self.db.add(current_access)
            
            self.db.commit()
            
            return FeatureAccessUpdate(
                customer_id=str(customer.id),
                subscription_id=str(subscription.id),
                old_tier=None,  # Will be set by caller if needed
                new_tier=new_tier,
                features_added=features_added,
                features_removed=features_removed,
                access_level=FeatureAccessLevel(new_tier.upper()),
                effective_date=datetime.now(timezone.utc),
                reason=f"Subscription {subscription.status} - {new_tier} tier"
            )
            
        except Exception as e:
            logger.error(f"Error updating feature access: {e}")
            self.db.rollback()
            raise
    
    def _downgrade_feature_access_for_cancellation(self, customer: Customer, subscription: Subscription, cancellation_data: Dict[str, Any]) -> FeatureAccessUpdate:
        """Downgrade feature access for cancelled subscription"""
        try:
            # Get current feature access
            current_access = self.db.query(FeatureAccess).filter(
                FeatureAccess.customer_id == customer.id
            ).first()
            
            # Determine downgrade tier (usually basic or none)
            downgrade_tier = 'basic'  # Could be configurable based on business rules
            tier_config = self.feature_configs.get(downgrade_tier, self.feature_configs['basic'])
            
            # Calculate feature changes
            old_features = set(current_access.features if current_access else [])
            new_features = set(tier_config['features'])
            
            features_added = list(new_features - old_features)
            features_removed = list(old_features - new_features)
            
            # Update feature access
            if current_access:
                current_access.features = list(new_features)
                current_access.access_level = FeatureAccessLevel(downgrade_tier.upper())
                current_access.updated_at = datetime.now(timezone.utc)
                current_access.subscription_id = None  # No active subscription
            
            self.db.commit()
            
            return FeatureAccessUpdate(
                customer_id=str(customer.id),
                subscription_id=str(subscription.id),
                old_tier=subscription.pricing_tier,
                new_tier=downgrade_tier,
                features_added=features_added,
                features_removed=features_removed,
                access_level=FeatureAccessLevel(downgrade_tier.upper()),
                effective_date=datetime.now(timezone.utc),
                reason=f"Subscription cancelled - downgraded to {downgrade_tier} tier"
            )
            
        except Exception as e:
            logger.error(f"Error downgrading feature access: {e}")
            self.db.rollback()
            raise
    
    # Notification Methods
    
    def _send_subscription_welcome_notifications(self, customer: Customer, subscription: Subscription, subscription_data: Dict[str, Any]) -> List[UserNotification]:
        """Send welcome notifications for new subscription"""
        try:
            notifications = []
            
            # Get user for customer
            user = self.db.query(User).filter(User.customer_id == customer.id).first()
            if not user:
                logger.warning(f"No user found for customer {customer.id}")
                return notifications
            
            # Create welcome notification
            welcome_notification = UserNotification(
                user_id=str(user.id),
                customer_id=str(customer.id),
                notification_type=NotificationType.SUBSCRIPTION_CREATED,
                subject="Welcome to MINGUS! Your subscription is active",
                message=self._get_welcome_message(customer, subscription, subscription_data),
                priority="medium",
                channels=["email", "in_app"],
                metadata={
                    'subscription_id': str(subscription.id),
                    'pricing_tier': subscription.pricing_tier,
                    'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None
                }
            )
            
            # Send notification
            self.notification_service.send_notification(welcome_notification)
            notifications.append(welcome_notification)
            
            # Send feature access notification
            feature_notification = UserNotification(
                user_id=str(user.id),
                customer_id=str(customer.id),
                notification_type=NotificationType.FEATURE_ACCESS_UPDATED,
                subject="Your MINGUS features are now available",
                message=self._get_feature_access_message(customer, subscription),
                priority="medium",
                channels=["email", "in_app"],
                metadata={
                    'subscription_id': str(subscription.id),
                    'pricing_tier': subscription.pricing_tier,
                    'features': subscription.features if hasattr(subscription, 'features') else []
                }
            )
            
            self.notification_service.send_notification(feature_notification)
            notifications.append(feature_notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error sending welcome notifications: {e}")
            return []
    
    def _send_payment_success_notifications(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> List[UserNotification]:
        """Send payment success notifications"""
        try:
            notifications = []
            
            # Get user for customer
            user = self.db.query(User).filter(User.customer_id == customer.id).first()
            if not user:
                return notifications
            
            # Create payment success notification
            payment_notification = UserNotification(
                user_id=str(user.id),
                customer_id=str(customer.id),
                notification_type=NotificationType.PAYMENT_SUCCEEDED,
                subject="Payment Successful - MINGUS Subscription",
                message=self._get_payment_success_message(customer, billing_record, payment_data),
                priority="medium",
                channels=["email", "in_app"],
                metadata={
                    'billing_record_id': str(billing_record.id),
                    'amount': billing_record.amount,
                    'currency': billing_record.currency,
                    'payment_date': billing_record.payment_date.isoformat() if billing_record.payment_date else None
                }
            )
            
            self.notification_service.send_notification(payment_notification)
            notifications.append(payment_notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error sending payment success notifications: {e}")
            return []
    
    def _send_payment_failure_notifications(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> List[UserNotification]:
        """Send payment failure notifications"""
        try:
            notifications = []
            
            # Get user for customer
            user = self.db.query(User).filter(User.customer_id == customer.id).first()
            if not user:
                return notifications
            
            # Create payment failure notification
            failure_notification = UserNotification(
                user_id=str(user.id),
                customer_id=str(customer.id),
                notification_type=NotificationType.PAYMENT_FAILED,
                subject="Payment Failed - Action Required",
                message=self._get_payment_failure_message(customer, billing_record, payment_data),
                priority="high",
                channels=["email", "sms", "in_app"],
                metadata={
                    'billing_record_id': str(billing_record.id),
                    'amount': billing_record.amount,
                    'currency': billing_record.currency,
                    'failure_reason': payment_data.get('failure_reason', 'Unknown')
                }
            )
            
            self.notification_service.send_notification(failure_notification)
            notifications.append(failure_notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error sending payment failure notifications: {e}")
            return []
    
    def _send_cancellation_notifications(self, customer: Customer, subscription: Subscription, cancellation_data: Dict[str, Any]) -> List[UserNotification]:
        """Send cancellation notifications"""
        try:
            notifications = []
            
            # Get user for customer
            user = self.db.query(User).filter(User.customer_id == customer.id).first()
            if not user:
                return notifications
            
            # Create cancellation notification
            cancellation_notification = UserNotification(
                user_id=str(user.id),
                customer_id=str(customer.id),
                notification_type=NotificationType.SUBSCRIPTION_CANCELLED,
                subject="Subscription Cancelled - MINGUS",
                message=self._get_cancellation_message(customer, subscription, cancellation_data),
                priority="medium",
                channels=["email", "in_app"],
                metadata={
                    'subscription_id': str(subscription.id),
                    'cancellation_reason': cancellation_data.get('reason', 'Unknown'),
                    'effective_date': cancellation_data.get('effective_date')
                }
            )
            
            self.notification_service.send_notification(cancellation_notification)
            notifications.append(cancellation_notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error sending cancellation notifications: {e}")
            return []
    
    def _send_trial_ending_notifications(self, customer: Customer, subscription: Subscription, trial_data: Dict[str, Any]) -> List[UserNotification]:
        """Send trial ending notifications"""
        try:
            notifications = []
            
            # Get user for customer
            user = self.db.query(User).filter(User.customer_id == customer.id).first()
            if not user:
                return notifications
            
            # Create trial ending notification
            trial_notification = UserNotification(
                user_id=str(user.id),
                customer_id=str(customer.id),
                notification_type=NotificationType.TRIAL_ENDING,
                subject="Your MINGUS trial is ending soon",
                message=self._get_trial_ending_message(customer, subscription, trial_data),
                priority="high",
                channels=["email", "sms", "in_app"],
                metadata={
                    'subscription_id': str(subscription.id),
                    'trial_end_date': trial_data.get('trial_end_date'),
                    'days_remaining': trial_data.get('days_remaining')
                }
            )
            
            self.notification_service.send_notification(trial_notification)
            notifications.append(trial_notification)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error sending trial ending notifications: {e}")
            return []
    
    # Helper Methods
    
    def _load_notification_templates(self) -> Dict[str, str]:
        """Load notification message templates"""
        return {
            'welcome': """
Welcome to MINGUS! Your subscription is now active.

Subscription Details:
- Plan: {pricing_tier}
- Billing Cycle: {billing_cycle}
- Next Billing Date: {next_billing_date}

Your features are now available. Get started by exploring your dashboard!

Best regards,
The MINGUS Team
            """,
            'payment_success': """
Payment Successful!

Your payment of {amount} {currency} has been processed successfully.

Payment Details:
- Date: {payment_date}
- Invoice: {invoice_id}
- Next Billing: {next_billing_date}

Thank you for your continued support!

Best regards,
The MINGUS Team
            """,
            'payment_failure': """
Payment Failed - Action Required

We were unable to process your payment of {amount} {currency}.

Reason: {failure_reason}

Please update your payment method to avoid service interruption.

Update Payment Method: {payment_portal_url}

Best regards,
The MINGUS Team
            """,
            'cancellation': """
Subscription Cancelled

Your MINGUS subscription has been cancelled as requested.

Cancellation Details:
- Effective Date: {effective_date}
- Reason: {reason}

Your account will remain active until {effective_date}. After that, you'll have access to basic features only.

To reactivate your subscription, visit your account settings.

Best regards,
The MINGUS Team
            """,
            'trial_ending': """
Your Trial is Ending Soon

Your MINGUS trial will end on {trial_end_date} ({days_remaining} days remaining).

To continue enjoying all features, please add a payment method:

{payment_setup_url}

Don't lose access to your data and features!

Best regards,
The MINGUS Team
            """
        }
    
    def _get_welcome_message(self, customer: Customer, subscription: Subscription, subscription_data: Dict[str, Any]) -> str:
        """Get welcome message for new subscription"""
        template = self.notification_templates['welcome']
        return template.format(
            pricing_tier=subscription.pricing_tier or 'Basic',
            billing_cycle=subscription.billing_cycle or 'Monthly',
            next_billing_date=subscription.next_billing_date.strftime('%B %d, %Y') if subscription.next_billing_date else 'N/A'
        )
    
    def _get_payment_success_message(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> str:
        """Get payment success message"""
        template = self.notification_templates['payment_success']
        return template.format(
            amount=billing_record.amount,
            currency=billing_record.currency,
            payment_date=billing_record.payment_date.strftime('%B %d, %Y') if billing_record.payment_date else 'N/A',
            invoice_id=billing_record.invoice_id or 'N/A',
            next_billing_date=billing_record.next_billing_date.strftime('%B %d, %Y') if billing_record.next_billing_date else 'N/A'
        )
    
    def _get_payment_failure_message(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> str:
        """Get payment failure message"""
        template = self.notification_templates['payment_failure']
        return template.format(
            amount=billing_record.amount,
            currency=billing_record.currency,
            failure_reason=payment_data.get('failure_reason', 'Unknown error'),
            payment_portal_url=f"{self.config.BASE_URL}/account/billing"
        )
    
    def _get_cancellation_message(self, customer: Customer, subscription: Subscription, cancellation_data: Dict[str, Any]) -> str:
        """Get cancellation message"""
        template = self.notification_templates['cancellation']
        return template.format(
            effective_date=cancellation_data.get('effective_date', 'N/A'),
            reason=cancellation_data.get('reason', 'Customer request')
        )
    
    def _get_trial_ending_message(self, customer: Customer, subscription: Subscription, trial_data: Dict[str, Any]) -> str:
        """Get trial ending message"""
        template = self.notification_templates['trial_ending']
        return template.format(
            trial_end_date=trial_data.get('trial_end_date', 'N/A'),
            days_remaining=trial_data.get('days_remaining', 'N/A'),
            payment_setup_url=f"{self.config.BASE_URL}/account/billing/setup"
        )
    
    def _get_feature_access_message(self, customer: Customer, subscription: Subscription) -> str:
        """Get feature access message"""
        tier = subscription.pricing_tier or 'basic'
        tier_config = self.feature_configs.get(tier, self.feature_configs['basic'])
        
        features_text = "\n".join([f"- {feature}" for feature in tier_config['features']])
        
        return f"""
Your MINGUS features are now available!

Plan: {tier.title()}

Available Features:
{features_text}

Get started by exploring your dashboard!

Best regards,
The MINGUS Team
        """
    
    # Additional helper methods for business logic
    
    def _handle_pricing_tier_change(self, customer: Customer, subscription: Subscription, old_tier: str, new_tier: str) -> Dict[str, Any]:
        """Handle pricing tier changes"""
        changes = []
        notifications_sent = 0
        
        # Update feature access
        feature_update = self._update_feature_access_for_subscription(
            customer, subscription, {'pricing_tier': new_tier}
        )
        changes.append(f"Feature access updated for tier change: {old_tier} -> {new_tier}")
        
        # Send tier change notification
        user = self.db.query(User).filter(User.customer_id == customer.id).first()
        if user:
            tier_notification = UserNotification(
                user_id=str(user.id),
                customer_id=str(customer.id),
                notification_type=NotificationType.SUBSCRIPTION_UPDATED,
                subject=f"Your MINGUS plan has been updated to {new_tier.title()}",
                message=self._get_tier_change_message(customer, subscription, old_tier, new_tier),
                priority="medium",
                channels=["email", "in_app"],
                metadata={
                    'subscription_id': str(subscription.id),
                    'old_tier': old_tier,
                    'new_tier': new_tier
                }
            )
            self.notification_service.send_notification(tier_notification)
            notifications_sent += 1
            changes.append("Tier change notification sent")
        
        return {
            'changes': changes,
            'notifications_sent': notifications_sent
        }
    
    def _get_tier_change_message(self, customer: Customer, subscription: Subscription, old_tier: str, new_tier: str) -> str:
        """Get tier change message"""
        return f"""
Your MINGUS plan has been updated!

Previous Plan: {old_tier.title()}
New Plan: {new_tier.title()}

Your new features are now available. Check your dashboard to explore what's new!

Best regards,
The MINGUS Team
        """
    
    # Placeholder methods for additional business logic
    def _setup_trial_notifications(self, customer: Customer, subscription: Subscription, subscription_data: Dict[str, Any]) -> List[UserNotification]:
        """Setup trial notifications"""
        return []
    
    def _setup_payment_retry_notifications(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> List[UserNotification]:
        """Setup payment retry notifications"""
        return []
    
    def _setup_reactivation_offers(self, customer: Customer, subscription: Subscription, cancellation_data: Dict[str, Any]) -> List[UserNotification]:
        """Setup reactivation offers"""
        return []
    
    def _setup_trial_conversion_offers(self, customer: Customer, subscription: Subscription, trial_data: Dict[str, Any]) -> List[UserNotification]:
        """Setup trial conversion offers"""
        return []
    
    def _should_offer_reactivation(self, customer: Customer, subscription: Subscription, cancellation_data: Dict[str, Any]) -> bool:
        """Determine if reactivation offer should be sent"""
        return True  # Business logic to determine
    
    def _update_customer_status_for_new_subscription(self, customer: Customer, subscription: Subscription) -> None:
        """Update customer status for new subscription"""
        pass
    
    def _update_customer_status_for_cancellation(self, customer: Customer, subscription: Subscription) -> None:
        """Update customer status for cancellation"""
        pass
    
    def _reactivate_subscription_for_payment(self, customer: Customer, billing_record: BillingHistory) -> None:
        """Reactivate subscription for successful payment"""
        pass
    
    def _handle_subscription_for_failed_payment(self, customer: Customer, billing_record: BillingHistory) -> None:
        """Handle subscription for failed payment"""
        pass
    
    def _update_customer_payment_status(self, customer: Customer, billing_record: BillingHistory) -> None:
        """Update customer payment status"""
        pass
    
    def _update_customer_payment_status_for_failure(self, customer: Customer, billing_record: BillingHistory) -> None:
        """Update customer payment status for failure"""
        pass
    
    def _update_customer_trial_status(self, customer: Customer, subscription: Subscription) -> None:
        """Update customer trial status"""
        pass
    
    def _track_subscription_creation_metrics(self, customer: Customer, subscription: Subscription, subscription_data: Dict[str, Any]) -> None:
        """Track subscription creation metrics"""
        pass
    
    def _track_subscription_update_metrics(self, customer: Customer, subscription: Subscription, old_values: Dict[str, Any], new_data: Dict[str, Any]) -> None:
        """Track subscription update metrics"""
        pass
    
    def _track_cancellation_metrics(self, customer: Customer, subscription: Subscription, cancellation_data: Dict[str, Any]) -> None:
        """Track cancellation metrics"""
        pass
    
    def _track_payment_success_metrics(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> None:
        """Track payment success metrics"""
        pass
    
    def _track_payment_failure_metrics(self, customer: Customer, billing_record: BillingHistory, payment_data: Dict[str, Any]) -> None:
        """Track payment failure metrics"""
        pass
    
    def _track_trial_ending_metrics(self, customer: Customer, subscription: Subscription, trial_data: Dict[str, Any]) -> None:
        """Track trial ending metrics"""
        pass
    
    def _handle_status_change(self, customer: Customer, subscription: Subscription, old_status: str, new_status: str) -> Dict[str, Any]:
        """Handle subscription status changes"""
        return {'changes': [], 'notifications_sent': 0}
    
    def _handle_billing_cycle_change(self, customer: Customer, subscription: Subscription, old_cycle: str, new_cycle: str) -> Dict[str, Any]:
        """Handle billing cycle changes"""
        return {'changes': [], 'notifications_sent': 0} 
    
    # Payment Recovery Integration
    
    def handle_payment_failure_with_recovery(
        self,
        customer: Customer,
        billing_record: BillingHistory,
        failure_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle payment failure with comprehensive recovery workflow"""
        try:
            from .payment_recovery_service import PaymentRecoveryService
            
            # Initialize payment recovery service
            recovery_service = PaymentRecoveryService(self.db, self.config)
            
            # Execute payment recovery workflow
            recovery_result = recovery_service.handle_payment_failure(
                customer, billing_record, failure_data
            )
            
            # Add recovery-specific changes to business logic result
            if recovery_result['success']:
                return {
                    'success': True,
                    'changes': recovery_result['changes'],
                    'notifications_sent': recovery_result['notifications_sent'],
                    'recovery_strategy': recovery_result['recovery_strategy'],
                    'dunning_stage': recovery_result['dunning_event'].stage.value if 'dunning_event' in recovery_result else None,
                    'next_action': recovery_result['next_action'],
                    'message': f"Payment recovery workflow initiated: {recovery_result['recovery_strategy']}"
                }
            else:
                return {
                    'success': False,
                    'error': recovery_result['error'],
                    'changes': recovery_result['changes'],
                    'notifications_sent': recovery_result['notifications_sent']
                }
                
        except Exception as e:
            logger.error(f"Error handling payment failure with recovery: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def handle_payment_success_after_recovery(
        self,
        customer: Customer,
        billing_record: BillingHistory,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle successful payment after recovery workflow"""
        try:
            from .payment_recovery_service import PaymentRecoveryService
            
            # Initialize payment recovery service
            recovery_service = PaymentRecoveryService(self.db, self.config)
            
            # Execute recovery success workflow
            recovery_result = recovery_service.handle_payment_success_after_failure(
                customer, billing_record, payment_data
            )
            
            # Combine with business logic success handling
            business_result = self.handle_payment_succeeded(
                customer, billing_record, payment_data
            )
            
            # Merge results
            combined_changes = recovery_result['changes'] + business_result['changes']
            combined_notifications = recovery_result['notifications_sent'] + business_result['notifications_sent']
            
            return {
                'success': True,
                'changes': combined_changes,
                'notifications_sent': combined_notifications,
                'recovery_events_cleared': recovery_result['cleared_events'],
                'message': f"Payment recovery successful with {combined_notifications} notifications sent"
            }
            
        except Exception as e:
            logger.error(f"Error handling payment success after recovery: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def process_dunning_escalation(
        self,
        customer: Customer,
        billing_record: BillingHistory,
        dunning_event: Any
    ) -> Dict[str, Any]:
        """Process dunning escalation"""
        try:
            from .payment_recovery_service import PaymentRecoveryService
            
            # Initialize payment recovery service
            recovery_service = PaymentRecoveryService(self.db, self.config)
            
            # Process dunning escalation
            escalation_result = recovery_service.process_dunning_escalation(
                customer, billing_record, dunning_event
            )
            
            return escalation_result
            
        except Exception as e:
            logger.error(f"Error processing dunning escalation: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def handle_payment_method_update_during_recovery(
        self,
        customer: Customer,
        billing_record: BillingHistory,
        payment_method_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle payment method update during recovery"""
        try:
            from .payment_recovery_service import PaymentRecoveryService
            
            # Initialize payment recovery service
            recovery_service = PaymentRecoveryService(self.db, self.config)
            
            # Handle payment method update
            update_result = recovery_service.handle_payment_method_update(
                customer, billing_record, payment_method_data
            )
            
            return update_result
            
        except Exception as e:
            logger.error(f"Error handling payment method update during recovery: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }
    
    def handle_grace_period_management(
        self,
        customer: Customer,
        billing_record: BillingHistory,
        grace_period_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle grace period management"""
        try:
            from .payment_recovery_service import PaymentRecoveryService
            
            # Initialize payment recovery service
            recovery_service = PaymentRecoveryService(self.db, self.config)
            
            # Handle grace period management
            grace_result = recovery_service.handle_grace_period_management(
                customer, billing_record, grace_period_data
            )
            
            return grace_result
            
        except Exception as e:
            logger.error(f"Error handling grace period management: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'notifications_sent': 0
            }