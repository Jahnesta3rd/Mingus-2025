"""
Comprehensive Payment Service for MINGUS
Unified interface for all payment operations and subscription management
"""
import stripe
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func

from ..models.subscription import (
    Customer, Subscription, PaymentMethod, BillingHistory, 
    PricingTier, FeatureUsage, AuditLog, AuditEventType, AuditSeverity,
    Refund, Credit
)
from ..config.base import Config
from .billing_features import BillingFeatures
from .usage_tracker import UsageTracker
from .customer_portal import CustomerPortal
from .revenue_optimizer import RevenueOptimizer
from .subscription_lifecycle import SubscriptionLifecycleManager
from .automated_workflows import AutomatedWorkflowManager
from .feature_access_service import FeatureAccessService
from .billing_service import BillingService
from .payment_processor import PaymentProcessor
from .subscription_manager import SubscriptionManager
from .webhook_handler import StripeWebhookHandler
from .admin_dashboard import AdminBillingDashboard
from .stripe_portal import StripeCustomerPortal

logger = logging.getLogger(__name__)

class PaymentServiceError(Exception):
    """Custom exception for payment service errors"""
    pass

class PaymentService:
    """Comprehensive payment service for MINGUS subscriptions"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Initialize all payment services
        self.payment_processor = PaymentProcessor(db_session, config)
        self.subscription_manager = SubscriptionManager(db_session, config)
        self.webhook_handler = StripeWebhookHandler(db_session, config)
        self.billing_service = BillingService(db_session, config)
        self.billing_features = BillingFeatures(db_session, config)
        self.usage_tracker = UsageTracker(db_session, config)
        self.customer_portal = CustomerPortal(db_session, config)
        self.revenue_optimizer = RevenueOptimizer(db_session, config)
        self.lifecycle_manager = SubscriptionLifecycleManager(db_session, config)
        self.automated_workflows = AutomatedWorkflowManager(db_session, config)
        self.feature_access = FeatureAccessService(db_session, config)
        self.admin_dashboard = AdminBillingDashboard(db_session, config)
        self.stripe_portal = StripeCustomerPortal(db_session, config)
    
    # ============================================================================
    # SUBSCRIPTION CREATION WITH PAYMENT METHOD
    # ============================================================================
    
    def create_subscription_with_payment(
        self,
        user_id: int,
        email: str,
        name: str,
        pricing_tier_id: int,
        payment_method_id: str,
        billing_cycle: str = 'monthly',
        trial_days: int = 0,
        set_payment_method_default: bool = True
    ) -> Dict[str, Any]:
        """Create a customer, subscription, and payment method in one operation"""
        try:
            # Create or get customer
            customer = self._get_or_create_customer(user_id, email, name)
            
            # Add payment method
            payment_method = self.add_payment_method(
                customer_id=customer.id,
                payment_method_id=payment_method_id,
                set_as_default=set_payment_method_default
            )
            
            # Create subscription
            subscription = self.create_subscription(
                customer_id=customer.id,
                pricing_tier_id=pricing_tier_id,
                billing_cycle=billing_cycle,
                trial_days=trial_days,
                payment_method_id=payment_method_id
            )
            
            return {
                'success': True,
                'customer_id': customer.id,
                'subscription_id': subscription.id,
                'payment_method_id': payment_method.id,
                'stripe_customer_id': customer.stripe_customer_id,
                'stripe_subscription_id': subscription.stripe_subscription_id,
                'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None
            }
            
        except Exception as e:
            logger.error(f"Error creating subscription with payment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_customer(self, user_id: int, email: str, name: str) -> Customer:
        """Get existing customer or create new one"""
        # Check if customer already exists
        customer = self.db.query(Customer).filter(
            Customer.user_id == user_id
        ).first()
        
        if customer:
            return customer
        
        # Create new customer
        stripe_customer = self.stripe.Customer.create(
            email=email,
            name=name,
            metadata={'mingus_user_id': user_id}
        )
        
        customer = Customer(
            user_id=user_id,
            stripe_customer_id=stripe_customer.id,
            email=email,
            name=name
        )
        
        self.db.add(customer)
        self.db.commit()
        
        self._log_audit_event(
            event_type=AuditEventType.SUBSCRIPTION_CREATED,
            user_id=user_id,
            customer_id=customer.id,
            event_description=f"Customer created: {email}"
        )
        
        return customer
    
    def create_subscription(
        self,
        customer_id: int,
        pricing_tier_id: int,
        billing_cycle: str = 'monthly',
        trial_days: int = 0,
        payment_method_id: str = None
    ) -> Subscription:
        """Create a new subscription"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            pricing_tier = self.db.query(PricingTier).filter(PricingTier.id == pricing_tier_id).first()
            
            if not customer or not pricing_tier:
                raise PaymentServiceError("Customer or pricing tier not found")
            
            # Get appropriate Stripe price ID
            price_id = (pricing_tier.stripe_price_id_monthly if billing_cycle == 'monthly' 
                       else pricing_tier.stripe_price_id_yearly)
            
            if not price_id:
                raise PaymentServiceError(f"No Stripe price ID configured for {billing_cycle} billing")
            
            # Prepare subscription data
            subscription_data = {
                'customer': customer.stripe_customer_id,
                'items': [{'price': price_id}],
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent'],
                'metadata': {
                    'mingus_customer_id': customer_id,
                    'mingus_pricing_tier_id': pricing_tier_id,
                    'billing_cycle': billing_cycle
                }
            }
            
            # Add payment method if provided
            if payment_method_id:
                subscription_data['default_payment_method'] = payment_method_id
            
            # Add trial period if specified
            if trial_days > 0:
                subscription_data['trial_period_days'] = trial_days
            
            # Create Stripe subscription
            stripe_subscription = self.stripe.Subscription.create(**subscription_data)
            
            # Calculate amount
            amount = pricing_tier.monthly_price if billing_cycle == 'monthly' else pricing_tier.yearly_price
            
            # Create local subscription record
            subscription = Subscription(
                customer_id=customer_id,
                pricing_tier_id=pricing_tier_id,
                stripe_subscription_id=stripe_subscription.id,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                billing_cycle=billing_cycle,
                amount=amount,
                currency='USD'
            )
            
            if stripe_subscription.trial_start:
                subscription.trial_start = datetime.fromtimestamp(stripe_subscription.trial_start)
            if stripe_subscription.trial_end:
                subscription.trial_end = datetime.fromtimestamp(stripe_subscription.trial_end)
            
            self.db.add(subscription)
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CREATED,
                customer_id=customer_id,
                subscription_id=subscription.id,
                event_description=f"Subscription created: {pricing_tier.name} ({billing_cycle})"
            )
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise PaymentServiceError(f"Failed to create subscription: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating subscription: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    # ============================================================================
    # PAYMENT METHOD UPDATES AND VALIDATION
    # ============================================================================
    
    def add_payment_method(
        self,
        customer_id: int,
        payment_method_id: str,
        set_as_default: bool = False
    ) -> PaymentMethod:
        """Add a payment method to a customer"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            
            if not customer:
                raise PaymentServiceError("Customer not found")
            
            # Validate payment method with Stripe
            stripe_payment_method = self.stripe.PaymentMethod.retrieve(payment_method_id)
            
            # Attach to Stripe customer
            self.stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer.stripe_customer_id
            )
            
            # Set as default if requested
            if set_as_default:
                self.stripe.Customer.modify(
                    customer.stripe_customer_id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )
            
            # Create local payment method record
            payment_method = PaymentMethod(
                customer_id=customer_id,
                stripe_payment_method_id=payment_method_id,
                type=stripe_payment_method.type,
                brand=stripe_payment_method.card.brand if stripe_payment_method.type == 'card' else None,
                last4=stripe_payment_method.card.last4 if stripe_payment_method.type == 'card' else None,
                exp_month=stripe_payment_method.card.exp_month if stripe_payment_method.type == 'card' else None,
                exp_year=stripe_payment_method.card.exp_year if stripe_payment_method.type == 'card' else None,
                country=stripe_payment_method.card.country if stripe_payment_method.type == 'card' else None,
                fingerprint=stripe_payment_method.card.fingerprint if stripe_payment_method.type == 'card' else None,
                billing_details=stripe_payment_method.billing_details,
                is_default=set_as_default
            )
            
            self.db.add(payment_method)
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_METHOD_ADDED,
                customer_id=customer_id,
                payment_method_id=payment_method.id,
                event_description=f"Payment method added: {payment_method.type} ending in {payment_method.last4}"
            )
            
            return payment_method
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error adding payment method: {e}")
            raise PaymentServiceError(f"Failed to add payment method: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error adding payment method: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    def update_payment_method(
        self,
        payment_method_id: int,
        set_as_default: bool = None,
        billing_details: Dict = None
    ) -> PaymentMethod:
        """Update payment method details"""
        try:
            payment_method = self.db.query(PaymentMethod).filter(
                PaymentMethod.id == payment_method_id
            ).first()
            
            if not payment_method:
                raise PaymentServiceError("Payment method not found")
            
            # Update Stripe payment method
            stripe_update_data = {}
            
            if billing_details:
                stripe_update_data['billing_details'] = billing_details
                payment_method.billing_details = billing_details
            
            if stripe_update_data:
                self.stripe.PaymentMethod.modify(
                    payment_method.stripe_payment_method_id,
                    **stripe_update_data
                )
            
            # Set as default if requested
            if set_as_default is not None:
                if set_as_default:
                    # Set as default in Stripe
                    self.stripe.Customer.modify(
                        payment_method.customer.stripe_customer_id,
                        invoice_settings={'default_payment_method': payment_method.stripe_payment_method_id}
                    )
                    
                    # Update other payment methods to not default
                    self.db.query(PaymentMethod).filter(
                        and_(
                            PaymentMethod.customer_id == payment_method.customer_id,
                            PaymentMethod.id != payment_method_id
                        )
                    ).update({'is_default': False})
                
                payment_method.is_default = set_as_default
            
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_METHOD_UPDATED,
                customer_id=payment_method.customer_id,
                payment_method_id=payment_method.id,
                event_description=f"Payment method updated: {payment_method.stripe_payment_method_id}"
            )
            
            return payment_method
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating payment method: {e}")
            raise PaymentServiceError(f"Failed to update payment method: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error updating payment method: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    def validate_payment_method(self, payment_method_id: str) -> Dict[str, Any]:
        """Validate a payment method with Stripe"""
        try:
            # Retrieve payment method from Stripe
            stripe_payment_method = self.stripe.PaymentMethod.retrieve(payment_method_id)
            
            # Check if it's a card and validate it
            if stripe_payment_method.type == 'card':
                # Create a test payment intent to validate the card
                test_payment_intent = self.stripe.PaymentIntent.create(
                    amount=100,  # $1.00 test amount
                    currency='usd',
                    payment_method=payment_method_id,
                    confirm=True,
                    off_session=True,
                    error_on_requires_action=True
                )
                
                # Immediately cancel the test payment intent
                self.stripe.PaymentIntent.cancel(test_payment_intent.id)
                
                return {
                    'valid': True,
                    'payment_method_id': payment_method_id,
                    'type': stripe_payment_method.type,
                    'brand': stripe_payment_method.card.brand,
                    'last4': stripe_payment_method.card.last4,
                    'exp_month': stripe_payment_method.card.exp_month,
                    'exp_year': stripe_payment_method.card.exp_year
                }
            else:
                return {
                    'valid': True,
                    'payment_method_id': payment_method_id,
                    'type': stripe_payment_method.type
                }
                
        except stripe.error.CardError as e:
            return {
                'valid': False,
                'error': str(e),
                'error_type': 'card_error'
            }
        except stripe.error.StripeError as e:
            return {
                'valid': False,
                'error': str(e),
                'error_type': 'stripe_error'
            }
    
    # ============================================================================
    # SUBSCRIPTION UPGRADES AND DOWNGRADES WITH PRORATION
    # ============================================================================
    
    def upgrade_subscription(
        self,
        subscription_id: int,
        new_tier_id: int,
        billing_cycle: str = None,
        proration_behavior: str = 'create_prorations'
    ) -> Dict[str, Any]:
        """Upgrade subscription to a higher tier with proration"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise PaymentServiceError("Subscription not found")
            
            new_tier = self.db.query(PricingTier).filter(PricingTier.id == new_tier_id).first()
            if not new_tier:
                raise PaymentServiceError("Pricing tier not found")
            
            # Validate upgrade
            if not self._is_valid_upgrade(subscription.pricing_tier.tier_type, new_tier.tier_type):
                raise PaymentServiceError("New tier must be higher than current tier")
            
            # Store old values for audit
            old_values = {
                'pricing_tier_id': subscription.pricing_tier_id,
                'amount': subscription.amount,
                'billing_cycle': subscription.billing_cycle
            }
            
            # Get new price ID
            new_billing_cycle = billing_cycle or subscription.billing_cycle
            price_id = (new_tier.stripe_price_id_monthly if new_billing_cycle == 'monthly' 
                       else new_tier.stripe_price_id_yearly)
            
            # Update Stripe subscription
            stripe_update_data = {
                'items': [{
                    'id': self._get_stripe_subscription_item_id(subscription.stripe_subscription_id),
                    'price': price_id
                }],
                'proration_behavior': proration_behavior
            }
            
            stripe_subscription = self.stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                **stripe_update_data
            )
            
            # Update local subscription
            subscription.pricing_tier_id = new_tier_id
            subscription.amount = new_tier.monthly_price if new_billing_cycle == 'monthly' else new_tier.yearly_price
            subscription.billing_cycle = new_billing_cycle
            subscription.status = stripe_subscription.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
            
            self.db.commit()
            
            # Log audit event
            new_values = {
                'pricing_tier_id': subscription.pricing_tier_id,
                'amount': subscription.amount,
                'billing_cycle': subscription.billing_cycle
            }
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_TIER_CHANGED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description=f"Subscription upgraded: {subscription.pricing_tier.name}",
                old_values=old_values,
                new_values=new_values,
                changed_fields=['pricing_tier_id', 'amount', 'billing_cycle']
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'old_tier': subscription.pricing_tier.tier_type.value,
                'new_tier': new_tier.tier_type.value,
                'proration_behavior': proration_behavior
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error upgrading subscription: {e}")
            raise PaymentServiceError(f"Failed to upgrade subscription: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error upgrading subscription: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    def downgrade_subscription(
        self,
        subscription_id: int,
        new_tier_id: int,
        effective_date: str = 'period_end',
        proration_behavior: str = 'create_prorations'
    ) -> Dict[str, Any]:
        """Downgrade subscription to a lower tier"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise PaymentServiceError("Subscription not found")
            
            new_tier = self.db.query(PricingTier).filter(PricingTier.id == new_tier_id).first()
            if not new_tier:
                raise PaymentServiceError("Pricing tier not found")
            
            # Validate downgrade
            if not self._is_valid_downgrade(subscription.pricing_tier.tier_type, new_tier.tier_type):
                raise PaymentServiceError("New tier must be lower than current tier")
            
            if effective_date == 'immediate':
                # Downgrade immediately
                return self.upgrade_subscription(
                    subscription_id=subscription_id,
                    new_tier_id=new_tier_id,
                    proration_behavior=proration_behavior
                )
            else:
                # Schedule downgrade for period end
                stripe_subscription = self.stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True,
                    metadata={
                        'downgrade_to_tier_id': new_tier_id,
                        'downgrade_effective_date': 'period_end'
                    }
                )
                
                subscription.cancel_at_period_end = True
                subscription.canceled_at = datetime.utcnow()
                
                self.db.commit()
                
                self._log_audit_event(
                    event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                    customer_id=subscription.customer_id,
                    subscription_id=subscription.id,
                    event_description=f"Subscription downgrade scheduled for period end: {new_tier.name}"
                )
                
                return {
                    'success': True,
                    'subscription_id': subscription.id,
                    'effective_date': 'period_end',
                    'current_tier': subscription.pricing_tier.tier_type.value,
                    'new_tier': new_tier.tier_type.value
                }
                
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error downgrading subscription: {e}")
            raise PaymentServiceError(f"Failed to downgrade subscription: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error downgrading subscription: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    def _is_valid_upgrade(self, current_tier, new_tier) -> bool:
        """Check if upgrade is valid"""
        tier_order = {'budget': 1, 'mid_tier': 2, 'professional': 3}
        return tier_order.get(new_tier.value, 0) > tier_order.get(current_tier.value, 0)
    
    def _is_valid_downgrade(self, current_tier, new_tier) -> bool:
        """Check if downgrade is valid"""
        tier_order = {'budget': 1, 'mid_tier': 2, 'professional': 3}
        return tier_order.get(new_tier.value, 0) < tier_order.get(current_tier.value, 0)
    
    # ============================================================================
    # FAILED PAYMENT HANDLING AND RETRY LOGIC
    # ============================================================================
    
    def handle_failed_payment(
        self,
        invoice_id: str,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Handle failed payment with retry logic"""
        try:
            # Get invoice
            invoice = self.db.query(BillingHistory).filter(
                BillingHistory.stripe_invoice_id == invoice_id
            ).first()
            
            if not invoice:
                raise PaymentServiceError("Invoice not found")
            
            # Get subscription
            subscription = self.db.query(Subscription).filter(
                Subscription.id == invoice.subscription_id
            ).first()
            
            if not subscription:
                raise PaymentServiceError("Subscription not found")
            
            # Update retry count
            retry_count += 1
            
            if retry_count <= max_retries:
                # Attempt retry
                return self._retry_payment(invoice, subscription, retry_count)
            else:
                # Max retries exceeded, handle accordingly
                return self._handle_max_retries_exceeded(invoice, subscription)
                
        except Exception as e:
            logger.error(f"Error handling failed payment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _retry_payment(self, invoice: BillingHistory, subscription: Subscription, retry_count: int) -> Dict[str, Any]:
        """Retry a failed payment"""
        try:
            # Get customer's default payment method
            default_payment_method = self.db.query(PaymentMethod).filter(
                and_(
                    PaymentMethod.customer_id == subscription.customer_id,
                    PaymentMethod.is_default == True,
                    PaymentMethod.is_active == True
                )
            ).first()
            
            if not default_payment_method:
                return self._handle_no_payment_method(invoice, subscription)
            
            # Create new payment intent
            payment_intent = self.stripe.PaymentIntent.create(
                amount=int(invoice.amount_due * 100),  # Convert to cents
                currency=invoice.currency.lower(),
                customer=subscription.customer.stripe_customer_id,
                payment_method=default_payment_method.stripe_payment_method_id,
                confirm=True,
                off_session=True,
                error_on_requires_action=True,
                metadata={
                    'invoice_id': invoice.id,
                    'retry_count': retry_count
                }
            )
            
            if payment_intent.status == 'succeeded':
                # Payment succeeded
                invoice.status = 'succeeded'
                invoice.amount_paid = invoice.amount_due
                invoice.paid = True
                invoice.paid_date = datetime.utcnow()
                
                subscription.status = 'active'
                
                self.db.commit()
                
                self._log_audit_event(
                    event_type=AuditEventType.PAYMENT_SUCCEEDED,
                    customer_id=subscription.customer_id,
                    invoice_id=invoice.id,
                    event_description=f"Payment retry succeeded (attempt {retry_count})"
                )
                
                return {
                    'success': True,
                    'status': 'succeeded',
                    'retry_count': retry_count,
                    'payment_intent_id': payment_intent.id
                }
            else:
                # Payment still failed
                return {
                    'success': False,
                    'status': 'failed',
                    'retry_count': retry_count,
                    'error': 'Payment retry failed'
                }
                
        except stripe.error.CardError as e:
            # Card was declined
            return {
                'success': False,
                'status': 'card_declined',
                'retry_count': retry_count,
                'error': str(e)
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'status': 'stripe_error',
                'retry_count': retry_count,
                'error': str(e)
            }
    
    def _handle_no_payment_method(self, invoice: BillingHistory, subscription: Subscription) -> Dict[str, Any]:
        """Handle case where no payment method is available"""
        # Update subscription status
        subscription.status = 'past_due'
        invoice.status = 'failed'
        
        self.db.commit()
        
        self._log_audit_event(
            event_type=AuditEventType.PAYMENT_FAILED,
            customer_id=subscription.customer_id,
            invoice_id=invoice.id,
            event_description="Payment failed: No payment method available"
        )
        
        return {
            'success': False,
            'status': 'no_payment_method',
            'error': 'No payment method available'
        }
    
    def _handle_max_retries_exceeded(self, invoice: BillingHistory, subscription: Subscription) -> Dict[str, Any]:
        """Handle case where max retries have been exceeded"""
        # Update subscription status
        subscription.status = 'unpaid'
        invoice.status = 'failed'
        
        self.db.commit()
        
        self._log_audit_event(
            event_type=AuditEventType.PAYMENT_FAILED,
            customer_id=subscription.customer_id,
            invoice_id=invoice.id,
            event_description="Payment failed: Max retries exceeded"
        )
        
        return {
            'success': False,
            'status': 'max_retries_exceeded',
            'error': 'Maximum payment retries exceeded'
        }
    
    # ============================================================================
    # SUBSCRIPTION CANCELLATION AND REFUNDS
    # ============================================================================
    
    def cancel_subscription(
        self,
        subscription_id: int,
        immediate: bool = False,
        refund_amount: float = None
    ) -> Dict[str, Any]:
        """Cancel a subscription with optional refund"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise PaymentServiceError("Subscription not found")
            
            # Cancel in Stripe
            if immediate:
                stripe_subscription = self.stripe.Subscription.delete(
                    subscription.stripe_subscription_id
                )
                subscription.status = 'canceled'
                subscription.canceled_at = datetime.utcnow()
            else:
                stripe_subscription = self.stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
                subscription.canceled_at = datetime.utcnow()
            
            self.db.commit()
            
            # Process refund if requested
            refund_result = None
            if refund_amount and refund_amount > 0:
                refund_result = self.process_refund(
                    subscription_id=subscription_id,
                    amount=refund_amount,
                    reason='subscription_cancellation'
                )
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CANCELED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description=f"Subscription canceled {'immediately' if immediate else 'at period end'}"
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
                'refund': refund_result
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            raise PaymentServiceError(f"Failed to cancel subscription: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error canceling subscription: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    def process_refund(
        self,
        subscription_id: int = None,
        invoice_id: int = None,
        amount: float = None,
        reason: str = 'requested_by_customer'
    ) -> Dict[str, Any]:
        """Process a refund for a subscription or invoice"""
        try:
            if subscription_id:
                # Refund based on subscription
                subscription = self.db.query(Subscription).filter(
                    Subscription.id == subscription_id
                ).first()
                
                if not subscription:
                    raise PaymentServiceError("Subscription not found")
                
                # Get latest invoice
                invoice = self.db.query(BillingHistory).filter(
                    BillingHistory.subscription_id == subscription_id
                ).order_by(BillingHistory.created_at.desc()).first()
                
                if not invoice:
                    raise PaymentServiceError("No invoice found for subscription")
                    
            elif invoice_id:
                # Refund based on specific invoice
                invoice = self.db.query(BillingHistory).filter(
                    BillingHistory.id == invoice_id
                ).first()
                
                if not invoice:
                    raise PaymentServiceError("Invoice not found")
                    
                subscription = self.db.query(Subscription).filter(
                    Subscription.id == invoice.subscription_id
                ).first()
            else:
                raise PaymentServiceError("Either subscription_id or invoice_id must be provided")
            
            # Determine refund amount
            if amount is None:
                amount = invoice.amount_paid
            
            if amount > invoice.amount_paid:
                raise PaymentServiceError("Refund amount cannot exceed paid amount")
            
            # Create Stripe refund
            refund_data = {
                'payment_intent': invoice.stripe_payment_intent_id,
                'amount': int(amount * 100),  # Convert to cents
                'reason': reason
            }
            
            stripe_refund = self.stripe.Refund.create(**refund_data)
            
            # Create local refund record
            refund = Refund(
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                stripe_refund_id=stripe_refund.id,
                amount=amount,
                currency=invoice.currency,
                reason=reason,
                status=stripe_refund.status
            )
            
            self.db.add(refund)
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_REFUNDED,
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                event_description=f"Refund processed: ${amount} - {reason}"
            )
            
            return {
                'success': True,
                'refund_id': refund.id,
                'amount': amount,
                'status': refund.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing refund: {e}")
            raise PaymentServiceError(f"Failed to process refund: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error processing refund: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    # ============================================================================
    # TRIAL PERIOD MANAGEMENT AND CONVERSION
    # ============================================================================
    
    def extend_trial_period(
        self,
        subscription_id: int,
        additional_days: int
    ) -> Dict[str, Any]:
        """Extend the trial period for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise PaymentServiceError("Subscription not found")
            
            if subscription.status != 'trialing':
                raise PaymentServiceError("Subscription is not in trial period")
            
            # Extend trial in Stripe
            stripe_subscription = self.stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                trial_end=int((datetime.utcnow() + timedelta(days=additional_days)).timestamp())
            )
            
            # Update local subscription
            subscription.trial_end = datetime.fromtimestamp(stripe_subscription.trial_end)
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
            
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description=f"Trial extended by {additional_days} days"
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'new_trial_end': subscription.trial_end.isoformat(),
                'additional_days': additional_days
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error extending trial: {e}")
            raise PaymentServiceError(f"Failed to extend trial: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error extending trial: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    def convert_trial_to_paid(
        self,
        subscription_id: int,
        payment_method_id: str = None
    ) -> Dict[str, Any]:
        """Convert a trial subscription to paid"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise PaymentServiceError("Subscription not found")
            
            if subscription.status != 'trialing':
                raise PaymentServiceError("Subscription is not in trial period")
            
            # Update payment method if provided
            if payment_method_id:
                self.update_payment_method(
                    payment_method_id=payment_method_id,
                    set_as_default=True
                )
            
            # End trial immediately
            stripe_subscription = self.stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                trial_end='now'
            )
            
            # Update local subscription
            subscription.status = stripe_subscription.status
            subscription.trial_end = None
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
            
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description="Trial converted to paid subscription"
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'conversion_date': datetime.utcnow().isoformat()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error converting trial: {e}")
            raise PaymentServiceError(f"Failed to convert trial: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error converting trial: {e}")
            self.db.rollback()
            raise PaymentServiceError(f"Database error: {str(e)}")
    
    def get_trial_status(self, subscription_id: int) -> Dict[str, Any]:
        """Get trial status for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise PaymentServiceError("Subscription not found")
            
            if subscription.status != 'trialing':
                return {
                    'in_trial': False,
                    'status': subscription.status
                }
            
            now = datetime.utcnow()
            trial_end = subscription.trial_end
            
            if not trial_end:
                return {
                    'in_trial': False,
                    'status': subscription.status
                }
            
            days_remaining = (trial_end - now).days
            
            return {
                'in_trial': True,
                'trial_end': trial_end.isoformat(),
                'days_remaining': max(0, days_remaining),
                'trial_start': subscription.trial_start.isoformat() if subscription.trial_start else None
            }
            
        except Exception as e:
            logger.error(f"Error getting trial status: {e}")
            return {
                'error': str(e)
            }
    
    # ============================================================================
    # BILLING FEATURES INTEGRATION
    # ============================================================================
    
    def generate_automatic_invoice(
        self,
        subscription_id: int,
        invoice_type: str = 'recurring',
        custom_amount: float = None,
        description: str = None
    ) -> Dict[str, Any]:
        """Generate automatic invoice for a subscription"""
        return self.billing_features.generate_automatic_invoice(
            subscription_id=subscription_id,
            invoice_type=invoice_type,
            custom_amount=custom_amount,
            description=description
        )
    
    def send_invoice_email(self, invoice_id: int, pdf_path: str = None) -> Dict[str, Any]:
        """Send invoice email to customer"""
        return self.billing_features.send_invoice_email(invoice_id, pdf_path)
    
    def send_payment_receipt_email(self, invoice_id: int) -> Dict[str, Any]:
        """Send payment receipt email to customer"""
        return self.billing_features.send_payment_receipt_email(invoice_id)
    
    def process_dunning_management(self) -> Dict[str, Any]:
        """Process dunning management for failed payments"""
        return self.billing_features.process_dunning_management()
    
    def calculate_tax(
        self,
        customer_id: int,
        amount: float,
        currency: str = 'USD',
        tax_exempt: str = None
    ) -> Dict[str, Any]:
        """Calculate tax for a transaction"""
        return self.billing_features.calculate_tax(
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            tax_exempt=tax_exempt
        )
    
    def convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        date: datetime = None
    ) -> Dict[str, Any]:
        """Convert amount between currencies"""
        return self.billing_features.convert_currency(
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            date=date
        )
    
    def format_currency(
        self,
        amount: float,
        currency: str,
        locale: str = 'en_US'
    ) -> str:
        """Format currency amount for display"""
        return self.billing_features.format_currency(amount, currency, locale)
    
    def get_supported_currencies(self) -> List[Dict[str, Any]]:
        """Get list of supported currencies"""
        return self.billing_features.get_supported_currencies()
    
    # ============================================================================
    # USAGE TRACKING INTEGRATION
    # ============================================================================
    
    def track_feature_usage(
        self,
        customer_id: int,
        feature_name: str,
        quantity: int = 1,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Track usage of a specific feature"""
        return self.usage_tracker.track_feature_usage(
            customer_id=customer_id,
            feature_name=feature_name,
            quantity=quantity,
            metadata=metadata
        )
    
    def get_feature_usage(
        self,
        customer_id: int,
        feature_name: str = None,
        period: str = 'current'
    ) -> Dict[str, Any]:
        """Get feature usage for a customer"""
        return self.usage_tracker.get_feature_usage(
            customer_id=customer_id,
            feature_name=feature_name,
            period=period
        )
    
    def get_usage_history(
        self,
        customer_id: int,
        feature_name: str = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage history for a customer"""
        return self.usage_tracker.get_usage_history(
            customer_id=customer_id,
            feature_name=feature_name,
            days=days
        )
    
    def calculate_usage_overage(
        self,
        customer_id: int,
        period: str = 'current'
    ) -> Dict[str, Any]:
        """Calculate usage overage charges for a customer"""
        return self.usage_tracker.calculate_usage_overage(
            customer_id=customer_id,
            period=period
        )
    
    def generate_usage_overage_invoice(
        self,
        customer_id: int,
        period: str = 'current'
    ) -> Dict[str, Any]:
        """Generate invoice for usage overage charges"""
        return self.usage_tracker.generate_overage_invoice(
            customer_id=customer_id,
            period=period
        )
    
    def enforce_usage_limits(
        self,
        customer_id: int,
        feature_name: str,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Enforce usage limits for a feature"""
        return self.usage_tracker.enforce_usage_limits(
            customer_id=customer_id,
            feature_name=feature_name,
            quantity=quantity
        )
    
    def get_usage_alerts(
        self,
        customer_id: int,
        threshold_percentage: float = 80.0
    ) -> Dict[str, Any]:
        """Get usage alerts for approaching limits"""
        return self.usage_tracker.get_usage_alerts(
            customer_id=customer_id,
            threshold_percentage=threshold_percentage
        )
    
    def get_real_time_usage(
        self,
        customer_id: int
    ) -> Dict[str, Any]:
        """Get real-time usage data for a customer"""
        return self.usage_tracker.get_real_time_usage(customer_id)
    
    def update_usage_in_real_time(
        self,
        customer_id: int,
        feature_name: str,
        quantity: int = 1,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Update usage in real-time and return immediate response"""
        return self.usage_tracker.update_usage_in_real_time(
            customer_id=customer_id,
            feature_name=feature_name,
            quantity=quantity,
            metadata=metadata
        )
    
    def get_usage_dashboard_data(
        self,
        customer_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard data for usage monitoring"""
        return self.usage_tracker.get_usage_dashboard_data(customer_id)
    
    def reset_monthly_usage(self, subscription_id: int) -> Dict[str, Any]:
        """Reset monthly usage counters for a subscription"""
        try:
            # Get current usage record
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.subscription_id == subscription_id,
                    FeatureUsage.usage_month == current_month,
                    FeatureUsage.usage_year == current_year
                )
            ).first()
            
            if usage and not usage.is_reset:
                # Reset all usage counters
                for feature in self.usage_tracker.trackable_features:
                    setattr(usage, f'{feature}_used', 0)
                
                usage.is_reset = True
                usage.last_reset_date = datetime.utcnow()
                
                self.db.commit()
                
                # Log reset event
                self._log_audit_event(
                    event_type=AuditEventType.USAGE_RESET,
                    subscription_id=subscription_id,
                    event_description=f"Monthly usage reset for {current_month}/{current_year}"
                )
                
                return {
                    'success': True,
                    'subscription_id': subscription_id,
                    'reset_date': usage.last_reset_date.isoformat(),
                    'month': current_month,
                    'year': current_year
                }
            
            return {
                'success': True,
                'message': 'Usage already reset or no usage record found'
            }
            
        except Exception as e:
            logger.error(f"Error resetting monthly usage: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_automated_billing_cycle(self) -> Dict[str, Any]:
        """Run complete automated billing cycle"""
        try:
            results = {
                'invoices_generated': 0,
                'emails_sent': 0,
                'dunning_processed': 0,
                'errors': []
            }
            
            # Get subscriptions due for billing
            today = datetime.utcnow().date()
            subscriptions_to_bill = self.db.query(Subscription).filter(
                and_(
                    Subscription.status.in_(['active', 'trialing']),
                    func.date(Subscription.current_period_end) <= today
                )
            ).all()
            
            # Generate invoices
            for subscription in subscriptions_to_bill:
                try:
                    invoice_result = self.generate_automatic_invoice(
                        subscription_id=subscription.id,
                        invoice_type='recurring'
                    )
                    
                    if invoice_result['success']:
                        results['invoices_generated'] += 1
                        
                        # Send invoice email
                        email_result = self.send_invoice_email(invoice_result['invoice_id'])
                        if email_result['success']:
                            results['emails_sent'] += 1
                    else:
                        results['errors'].append({
                            'subscription_id': subscription.id,
                            'error': invoice_result.get('error', 'Unknown error')
                        })
                        
                except Exception as e:
                    results['errors'].append({
                        'subscription_id': subscription.id,
                        'error': str(e)
                    })
            
            # Process dunning management
            dunning_result = self.process_dunning_management()
            results['dunning_processed'] = dunning_result.get('processed', 0)
            
            logger.info(f"Automated billing cycle completed: {results['invoices_generated']} invoices, {results['emails_sent']} emails, {results['dunning_processed']} dunning processed")
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in automated billing cycle: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _get_stripe_subscription_item_id(self, stripe_subscription_id: str) -> str:
        """Get the subscription item ID from Stripe"""
        subscription = self.stripe.Subscription.retrieve(stripe_subscription_id)
        return subscription.items.data[0].id
    
    def _log_audit_event(
        self,
        event_type: AuditEventType,
        user_id: int = None,
        customer_id: int = None,
        subscription_id: int = None,
        invoice_id: int = None,
        payment_method_id: int = None,
        event_description: str = None,
        old_values: Dict = None,
        new_values: Dict = None,
        changed_fields: List[str] = None,
        metadata: Dict = None
    ):
        """Log an audit event"""
        try:
            audit_log = AuditLog(
                event_type=event_type,
                user_id=user_id,
                customer_id=customer_id,
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                payment_method_id=payment_method_id,
                event_description=event_description,
                old_values=old_values,
                new_values=new_values,
                changed_fields=changed_fields,
                metadata=metadata
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log audit event: {e}")
            # Don't raise exception for audit logging failures
    
    # ============================================================================
    # CUSTOMER PORTAL INTEGRATION
    # ============================================================================
    
    def create_customer_portal_session(
        self,
        customer_id: int,
        return_url: str = None,
        configuration: Dict = None
    ) -> Dict[str, Any]:
        """Create a Stripe customer portal session"""
        return self.customer_portal.create_customer_portal_session(
            customer_id=customer_id,
            return_url=return_url,
            configuration=configuration
        )
    
    def get_customer_portal_configuration(self) -> Dict[str, Any]:
        """Get customer portal configuration"""
        return self.customer_portal.get_customer_portal_configuration()
    
    def update_customer_portal_configuration(
        self,
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update customer portal configuration"""
        return self.customer_portal.update_customer_portal_configuration(configuration)
    
    def get_payment_history(
        self,
        customer_id: int,
        limit: int = 50,
        offset: int = 0,
        status: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get customer payment history"""
        return self.customer_portal.get_payment_history(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
    
    def get_payment_details(
        self,
        customer_id: int,
        invoice_id: int
    ) -> Dict[str, Any]:
        """Get detailed payment information"""
        return self.customer_portal.get_payment_details(
            customer_id=customer_id,
            invoice_id=invoice_id
        )
    
    def download_invoice_pdf(
        self,
        customer_id: int,
        invoice_id: int
    ) -> Dict[str, Any]:
        """Download invoice PDF"""
        return self.customer_portal.download_invoice_pdf(
            customer_id=customer_id,
            invoice_id=invoice_id
        )
    
    def get_subscription_modification_options(
        self,
        customer_id: int
    ) -> Dict[str, Any]:
        """Get available subscription modification options"""
        return self.customer_portal.get_subscription_modification_options(customer_id)
    
    def modify_subscription_self_service(
        self,
        customer_id: int,
        modification_type: str,
        new_tier_id: int = None,
        new_billing_cycle: str = None,
        effective_date: str = 'immediate',
        reason: str = None
    ) -> Dict[str, Any]:
        """Allow customers to modify their subscription"""
        return self.customer_portal.modify_subscription_self_service(
            customer_id=customer_id,
            modification_type=modification_type,
            new_tier_id=new_tier_id,
            new_billing_cycle=new_billing_cycle,
            effective_date=effective_date,
            reason=reason
        )
    
    def create_billing_dispute(
        self,
        customer_id: int,
        invoice_id: int,
        dispute_type: str,
        dispute_reason: str,
        dispute_amount: float = None,
        supporting_documents: List[str] = None,
        contact_preference: str = 'email'
    ) -> Dict[str, Any]:
        """Create a billing dispute"""
        return self.customer_portal.create_billing_dispute(
            customer_id=customer_id,
            invoice_id=invoice_id,
            dispute_type=dispute_type,
            dispute_reason=dispute_reason,
            dispute_amount=dispute_amount,
            supporting_documents=supporting_documents,
            contact_preference=contact_preference
        )
    
    def get_dispute_status(
        self,
        customer_id: int,
        dispute_id: int
    ) -> Dict[str, Any]:
        """Get dispute status and details"""
        return self.customer_portal.get_dispute_status(
            customer_id=customer_id,
            dispute_id=dispute_id
        )
    
    def get_customer_disputes(
        self,
        customer_id: int,
        status: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get all disputes for a customer"""
        return self.customer_portal.get_customer_disputes(
            customer_id=customer_id,
            status=status,
            limit=limit,
            offset=offset
        )
    
    def add_dispute_comment(
        self,
        customer_id: int,
        dispute_id: int,
        comment: str,
        is_customer_comment: bool = True
    ) -> Dict[str, Any]:
        """Add a comment to a dispute"""
        return self.customer_portal.add_dispute_comment(
            customer_id=customer_id,
            dispute_id=dispute_id,
            comment=comment,
            is_customer_comment=is_customer_comment
        )
    
    # ============================================================================
    # REVENUE OPTIMIZATION INTEGRATION
    # ============================================================================
    
    def check_upgrade_opportunities(
        self,
        customer_id: int = None,
        include_all_customers: bool = False
    ) -> Dict[str, Any]:
        """Check for upgrade opportunities across customers"""
        return self.revenue_optimizer.check_upgrade_opportunities(
            customer_id=customer_id,
            include_all_customers=include_all_customers
        )
    
    def generate_upgrade_prompt(
        self,
        customer_id: int,
        prompt_type: str = 'usage_based'
    ) -> Dict[str, Any]:
        """Generate personalized upgrade prompt"""
        return self.revenue_optimizer.generate_upgrade_prompt(
            customer_id=customer_id,
            prompt_type=prompt_type
        )
    
    def detect_churn_risk(
        self,
        customer_id: int = None,
        include_all_customers: bool = False
    ) -> Dict[str, Any]:
        """Detect customers at risk of churning"""
        return self.revenue_optimizer.detect_churn_risk(
            customer_id=customer_id,
            include_all_customers=include_all_customers
        )
    
    def execute_churn_prevention_workflow(
        self,
        customer_id: int,
        workflow_type: str = 'automated'
    ) -> Dict[str, Any]:
        """Execute churn prevention workflow for a customer"""
        return self.revenue_optimizer.execute_churn_prevention_workflow(
            customer_id=customer_id,
            workflow_type=workflow_type
        )
    
    def identify_payment_recovery_opportunities(
        self,
        include_all_customers: bool = True
    ) -> Dict[str, Any]:
        """Identify customers needing payment recovery"""
        return self.revenue_optimizer.identify_payment_recovery_opportunities(
            include_all_customers=include_all_customers
        )
    
    def execute_payment_recovery_automation(
        self,
        customer_id: int,
        invoice_id: int,
        strategy: str = 'auto'
    ) -> Dict[str, Any]:
        """Execute automated payment recovery for a specific invoice"""
        return self.revenue_optimizer.execute_payment_recovery_automation(
            customer_id=customer_id,
            invoice_id=invoice_id,
            strategy=strategy
        )
    
    def generate_revenue_recognition_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """Generate revenue recognition report"""
        return self.revenue_optimizer.generate_revenue_recognition_report(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type
        )
    
    def get_revenue_analytics(
        self,
        period: str = 'monthly',
        include_projections: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive revenue analytics"""
        return self.revenue_optimizer.get_revenue_analytics(
            period=period,
            include_projections=include_projections
        )
    
    def run_revenue_optimization_cycle(self) -> Dict[str, Any]:
        """Run complete revenue optimization cycle"""
        try:
            results = {
                'upgrade_opportunities': 0,
                'churn_risks': 0,
                'recovery_opportunities': 0,
                'actions_taken': 0,
                'errors': []
            }
            
            # Check for upgrade opportunities
            upgrade_result = self.check_upgrade_opportunities(include_all_customers=True)
            if upgrade_result['success']:
                results['upgrade_opportunities'] = upgrade_result['total_opportunities']
                
                # Generate upgrade prompts for high-confidence opportunities
                for opportunity in upgrade_result['upgrade_opportunities']:
                    if opportunity['confidence_score'] >= 0.7:
                        try:
                            prompt_result = self.generate_upgrade_prompt(
                                customer_id=opportunity['customer_id'],
                                prompt_type='usage_based'
                            )
                            if prompt_result['success']:
                                results['actions_taken'] += 1
                        except Exception as e:
                            results['errors'].append(f"Upgrade prompt error: {str(e)}")
            
            # Detect churn risks
            churn_result = self.detect_churn_risk(include_all_customers=True)
            if churn_result['success']:
                results['churn_risks'] = churn_result['total_risks']
                
                # Execute prevention workflows for high-risk customers
                for risk in churn_result['churn_risks']:
                    if risk['risk_level'] in ['high', 'critical']:
                        try:
                            workflow_result = self.execute_churn_prevention_workflow(
                                customer_id=risk['customer_id'],
                                workflow_type='automated'
                            )
                            if workflow_result['success']:
                                results['actions_taken'] += 1
                        except Exception as e:
                            results['errors'].append(f"Churn prevention error: {str(e)}")
            
            # Identify payment recovery opportunities
            recovery_result = self.identify_payment_recovery_opportunities()
            if recovery_result['success']:
                results['recovery_opportunities'] = recovery_result['total_opportunities']
                
                # Execute recovery for high-potential opportunities
                for opportunity in recovery_result['recovery_opportunities']:
                    if opportunity['recovery_potential'] == 'high':
                        try:
                            recovery_result = self.execute_payment_recovery_automation(
                                customer_id=opportunity['customer_id'],
                                invoice_id=opportunity['invoice_id'],
                                strategy='auto'
                            )
                            if recovery_result['success']:
                                results['actions_taken'] += 1
                        except Exception as e:
                            results['errors'].append(f"Payment recovery error: {str(e)}")
            
            logger.info(f"Revenue optimization cycle completed: {results['actions_taken']} actions taken")
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in revenue optimization cycle: {e}")
            return {
                'success': False,
                'error': str(e)
            } 
    
    # ============================================================================
    # SUBSCRIPTION LIFECYCLE MANAGEMENT INTEGRATION
    # ============================================================================
    
    def process_lifecycle_event(
        self,
        subscription_id: int,
        event: str,
        metadata: Dict = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Process a subscription lifecycle event"""
        from .subscription_lifecycle import LifecycleEvent
        
        try:
            lifecycle_event = LifecycleEvent(event)
            return self.lifecycle_manager.process_lifecycle_event(
                subscription_id=subscription_id,
                event=lifecycle_event,
                metadata=metadata,
                user_id=user_id
            )
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid lifecycle event: {event}'
            }
    
    def get_subscription_lifecycle_status(
        self,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive lifecycle status for a subscription"""
        return self.lifecycle_manager.get_subscription_lifecycle_status(
            subscription_id=subscription_id
        )
    
    def get_subscriptions_by_state(
        self,
        state: str = None,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """Get all subscriptions in a specific state"""
        from .subscription_lifecycle import SubscriptionState
        
        try:
            subscription_state = SubscriptionState(state) if state else None
            return self.lifecycle_manager.get_subscriptions_by_state(
                state=subscription_state,
                include_inactive=include_inactive
            )
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid subscription state: {state}'
            }
    
    def start_trial(
        self,
        subscription_id: int,
        trial_days: int = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Start a trial period for a subscription"""
        return self.lifecycle_manager.start_trial(
            subscription_id=subscription_id,
            trial_days=trial_days,
            user_id=user_id
        )
    
    def convert_trial_to_paid(
        self,
        subscription_id: int,
        payment_method_id: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Convert a trial subscription to paid"""
        return self.lifecycle_manager.convert_trial_to_paid(
            subscription_id=subscription_id,
            payment_method_id=payment_method_id,
            user_id=user_id
        )
    
    def request_cancellation(
        self,
        subscription_id: int,
        effective_date: str = 'period_end',
        reason: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Request subscription cancellation"""
        return self.lifecycle_manager.request_cancellation(
            subscription_id=subscription_id,
            effective_date=effective_date,
            reason=reason,
            user_id=user_id
        )
    
    def request_reactivation(
        self,
        subscription_id: int,
        payment_method_id: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Request subscription reactivation"""
        return self.lifecycle_manager.request_reactivation(
            subscription_id=subscription_id,
            payment_method_id=payment_method_id,
            user_id=user_id
        )
    
    # ============================================================================
    # SPECIFIC LIFECYCLE STAGES
    # ============================================================================
    
    def activate_subscription(
        self,
        subscription_id: int,
        payment_method_id: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Activate a subscription to active state with normal billing"""
        return self.lifecycle_manager.activate_subscription(
            subscription_id=subscription_id,
            payment_method_id=payment_method_id,
            user_id=user_id
        )
    
    def upgrade_subscription(
        self,
        subscription_id: int,
        new_tier_id: int,
        proration_behavior: str = 'create_prorations',
        user_id: int = None
    ) -> Dict[str, Any]:
        """Upgrade subscription to higher tier with proration"""
        return self.lifecycle_manager.upgrade_subscription(
            subscription_id=subscription_id,
            new_tier_id=new_tier_id,
            proration_behavior=proration_behavior,
            user_id=user_id
        )
    
    def downgrade_subscription(
        self,
        subscription_id: int,
        new_tier_id: int,
        effective_date: str = 'period_end',
        proration_behavior: str = 'create_prorations',
        user_id: int = None
    ) -> Dict[str, Any]:
        """Downgrade subscription to lower tier with proration"""
        return self.lifecycle_manager.downgrade_subscription(
            subscription_id=subscription_id,
            new_tier_id=new_tier_id,
            effective_date=effective_date,
            proration_behavior=proration_behavior,
            user_id=user_id
        )
    
    def pause_subscription(
        self,
        subscription_id: int,
        pause_reason: str = None,
        pause_duration_days: int = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Pause subscription (temporary suspension)"""
        return self.lifecycle_manager.pause_subscription(
            subscription_id=subscription_id,
            pause_reason=pause_reason,
            pause_duration_days=pause_duration_days,
            user_id=user_id
        )
    
    def unpause_subscription(
        self,
        subscription_id: int,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Unpause subscription and restore to active state"""
        return self.lifecycle_manager.unpause_subscription(
            subscription_id=subscription_id,
            user_id=user_id
        )
    
    def cancel_subscription(
        self,
        subscription_id: int,
        effective_date: str = 'period_end',
        reason: str = None,
        refund_amount: float = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Cancel subscription with access until period end"""
        return self.lifecycle_manager.cancel_subscription(
            subscription_id=subscription_id,
            effective_date=effective_date,
            reason=reason,
            refund_amount=refund_amount,
            user_id=user_id
        )
    
    def reactivate_subscription(
        self,
        subscription_id: int,
        payment_method_id: str = None,
        restore_features: bool = True,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Reactivate canceled subscription"""
        return self.lifecycle_manager.reactivate_subscription(
            subscription_id=subscription_id,
            payment_method_id=payment_method_id,
            restore_features=restore_features,
            user_id=user_id
        )
    
    def get_subscription_access_status(
        self,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Get current access status for a subscription"""
        return self.lifecycle_manager.get_subscription_access_status(
            subscription_id=subscription_id
        )
    
    def process_automated_lifecycle_events(self) -> Dict[str, Any]:
        """Process automated lifecycle events for all subscriptions"""
        return self.lifecycle_manager.process_automated_lifecycle_events()
    
    def get_lifecycle_analytics(
        self,
        period: str = 'monthly',
        include_transitions: bool = True
    ) -> Dict[str, Any]:
        """Get subscription lifecycle analytics"""
        try:
            from .subscription_lifecycle import SubscriptionState
            
            # Get all subscriptions
            all_subscriptions = self.db.query(Subscription).all()
            
            # Calculate state distribution
            state_distribution = {}
            for state in SubscriptionState:
                count = len([s for s in all_subscriptions if s.status == state.value])
                state_distribution[state.value] = count
            
            # Calculate lifecycle metrics
            total_subscriptions = len(all_subscriptions)
            active_subscriptions = len([s for s in all_subscriptions if s.status == 'active'])
            trial_subscriptions = len([s for s in all_subscriptions if s.status == 'trialing'])
            canceled_subscriptions = len([s for s in all_subscriptions if s.status == 'canceled'])
            
            # Calculate rates
            activation_rate = (active_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0
            trial_conversion_rate = (active_subscriptions / (active_subscriptions + trial_subscriptions) * 100) if (active_subscriptions + trial_subscriptions) > 0 else 0
            churn_rate = (canceled_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0
            
            analytics = {
                'period': period,
                'total_subscriptions': total_subscriptions,
                'state_distribution': state_distribution,
                'metrics': {
                    'activation_rate': activation_rate,
                    'trial_conversion_rate': trial_conversion_rate,
                    'churn_rate': churn_rate,
                    'active_subscriptions': active_subscriptions,
                    'trial_subscriptions': trial_subscriptions,
                    'canceled_subscriptions': canceled_subscriptions
                }
            }
            
            # Add transition data if requested
            if include_transitions:
                analytics['transitions'] = self._get_lifecycle_transitions(period)
            
            return {
                'success': True,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting lifecycle analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_lifecycle_transitions(self, period: str) -> Dict[str, Any]:
        """Get lifecycle transition data for analytics"""
        try:
            # Get audit logs for subscription transitions
            transition_logs = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.SUBSCRIPTION_UPDATED,
                    AuditLog.old_values.isnot(None),
                    AuditLog.new_values.isnot(None)
                )
            ).order_by(AuditLog.event_timestamp.desc()).limit(100).all()
            
            transitions = []
            for log in transition_logs:
                if log.old_values and log.new_values:
                    old_status = log.old_values.get('status')
                    new_status = log.new_values.get('status')
                    
                    if old_status and new_status and old_status != new_status:
                        transitions.append({
                            'timestamp': log.event_timestamp.isoformat(),
                            'subscription_id': log.subscription_id,
                            'customer_id': log.customer_id,
                            'from_state': old_status,
                            'to_state': new_status,
                            'metadata': log.metadata
                        })
            
            return {
                'total_transitions': len(transitions),
                'recent_transitions': transitions[:20],  # Last 20 transitions
                'transition_types': self._analyze_transition_types(transitions)
            }
            
        except Exception as e:
            logger.error(f"Error getting lifecycle transitions: {e}")
            return {
                'total_transitions': 0,
                'recent_transitions': [],
                'transition_types': {}
            }
    
    def _analyze_transition_types(self, transitions: List[Dict]) -> Dict[str, int]:
        """Analyze types of transitions"""
        transition_counts = {}
        
        for transition in transitions:
            transition_key = f"{transition['from_state']}_to_{transition['to_state']}"
            transition_counts[transition_key] = transition_counts.get(transition_key, 0) + 1
        
        return transition_counts 
    
    # ============================================================================
    # AUTOMATED WORKFLOWS INTEGRATION
    # ============================================================================
    
    def process_trial_expiration_workflows(self) -> Dict[str, Any]:
        """Process trial expiration notifications (3 days, 1 day, expiration)"""
        return self.automated_workflows.process_trial_expiration_workflows()
    
    def process_payment_recovery_workflows(self) -> Dict[str, Any]:
        """Process payment failure recovery (3 retry attempts over 7 days)"""
        return self.automated_workflows.process_payment_recovery_workflows()
    
    def process_renewal_confirmation_workflows(self) -> Dict[str, Any]:
        """Process subscription renewal confirmations"""
        return self.automated_workflows.process_renewal_confirmation_workflows()
    
    def process_upgrade_confirmation_workflow(
        self,
        subscription_id: int,
        old_tier_name: str,
        new_tier_name: str,
        proration_amount: float
    ) -> Dict[str, Any]:
        """Process upgrade confirmation workflow"""
        return self.automated_workflows.process_upgrade_confirmation_workflow(
            subscription_id=subscription_id,
            old_tier_name=old_tier_name,
            new_tier_name=new_tier_name,
            proration_amount=proration_amount
        )
    
    def process_downgrade_confirmation_workflow(
        self,
        subscription_id: int,
        old_tier_name: str,
        new_tier_name: str,
        effective_date: str
    ) -> Dict[str, Any]:
        """Process downgrade confirmation workflow"""
        return self.automated_workflows.process_downgrade_confirmation_workflow(
            subscription_id=subscription_id,
            old_tier_name=old_tier_name,
            new_tier_name=new_tier_name,
            effective_date=effective_date
        )
    
    def process_cancellation_retention_workflow(
        self,
        subscription_id: int,
        cancellation_reason: str = None
    ) -> Dict[str, Any]:
        """Process cancellation surveys and retention offers"""
        return self.automated_workflows.process_cancellation_retention_workflow(
            subscription_id=subscription_id,
            cancellation_reason=cancellation_reason
        )
    
    def run_all_automated_workflows(self) -> Dict[str, Any]:
        """Run all automated workflows"""
        return self.automated_workflows.run_all_automated_workflows()
    
    def get_workflow_analytics(
        self,
        period: str = 'monthly',
        workflow_type: str = None
    ) -> Dict[str, Any]:
        """Get automated workflow analytics"""
        try:
            from .automated_workflows import WorkflowType
            
            # Get audit logs for workflow events
            workflow_logs = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.event_type == AuditEventType.SUBSCRIPTION_UPDATED,
                    AuditLog.metadata.isnot(None)
                )
            ).all()
            
            # Filter by workflow type if specified
            if workflow_type:
                workflow_logs = [
                    log for log in workflow_logs 
                    if log.metadata and log.metadata.get('workflow_type') == workflow_type
                ]
            
            # Calculate analytics
            total_workflows = len(workflow_logs)
            workflow_types = {}
            success_rate = 0
            
            for log in workflow_logs:
                if log.metadata and 'workflow_type' in log.metadata:
                    workflow_type_name = log.metadata['workflow_type']
                    workflow_types[workflow_type_name] = workflow_types.get(workflow_type_name, 0) + 1
            
            # Calculate success rate (assuming no error logs means success)
            if total_workflows > 0:
                success_rate = 0.95  # Placeholder - would calculate based on actual success/failure tracking
            
            analytics = {
                'period': period,
                'total_workflows': total_workflows,
                'workflow_types': workflow_types,
                'success_rate': success_rate,
                'recent_workflows': []
            }
            
            # Get recent workflow details
            for log in workflow_logs[-10:]:  # Last 10 workflows
                if log.metadata:
                    analytics['recent_workflows'].append({
                        'timestamp': log.event_timestamp.isoformat(),
                        'workflow_type': log.metadata.get('workflow_type'),
                        'description': log.event_description,
                        'subscription_id': log.subscription_id,
                        'customer_id': log.customer_id
                    })
            
            return {
                'success': True,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def configure_workflow_settings(
        self,
        workflow_type: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure automated workflow settings"""
        try:
            # Update workflow configuration
            if hasattr(self.automated_workflows, 'workflow_config'):
                if workflow_type in self.automated_workflows.workflow_config:
                    self.automated_workflows.workflow_config[workflow_type].update(settings)
                    
                    return {
                        'success': True,
                        'message': f'Workflow settings updated for {workflow_type}',
                        'updated_settings': settings
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Unknown workflow type: {workflow_type}'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Workflow manager not properly initialized'
                }
                
        except Exception as e:
            logger.error(f"Error configuring workflow settings: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_workflow_status(
        self,
        subscription_id: int = None,
        workflow_type: str = None
    ) -> Dict[str, Any]:
        """Get workflow status for subscriptions"""
        try:
            # Get recent workflow events
            query = self.db.query(AuditLog).filter(
                AuditLog.event_type == AuditEventType.SUBSCRIPTION_UPDATED
            )
            
            if subscription_id:
                query = query.filter(AuditLog.subscription_id == subscription_id)
            
            workflow_logs = query.order_by(AuditLog.event_timestamp.desc()).limit(50).all()
            
            workflow_status = []
            
            for log in workflow_logs:
                if log.metadata and 'workflow_type' in log.metadata:
                    if workflow_type and log.metadata['workflow_type'] != workflow_type:
                        continue
                    
                    workflow_status.append({
                        'timestamp': log.event_timestamp.isoformat(),
                        'workflow_type': log.metadata['workflow_type'],
                        'description': log.event_description,
                        'subscription_id': log.subscription_id,
                        'customer_id': log.customer_id,
                        'metadata': log.metadata.get('workflow_metadata', {})
                    })
            
            return {
                'success': True,
                'workflow_status': workflow_status,
                'total_workflows': len(workflow_status)
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {
                'success': False,
                'error': str(e)
            } 
    
    # ============================================================================
    # FEATURE ACCESS CONTROL INTEGRATION
    # ============================================================================
    
    def check_feature_access(
        self,
        subscription_id: int,
        feature_type: str,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Check if user has access to a specific feature"""
        from .feature_access_service import FeatureType
        
        try:
            feature_enum = FeatureType(feature_type)
            return self.feature_access.check_feature_access(
                subscription_id=subscription_id,
                feature_type=feature_enum,
                user_id=user_id
            )
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid feature type: {feature_type}',
                'decision': 'denied'
            }
    
    def use_feature(
        self,
        subscription_id: int,
        feature_type: str,
        user_id: int = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Use a feature and track usage"""
        from .feature_access_service import FeatureType
        
        try:
            feature_enum = FeatureType(feature_type)
            return self.feature_access.use_feature(
                subscription_id=subscription_id,
                feature_type=feature_enum,
                user_id=user_id,
                metadata=metadata
            )
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid feature type: {feature_type}',
                'decision': 'denied'
            }
    
    def generate_upgrade_prompt(
        self,
        subscription_id: int,
        trigger_type: str = None
    ) -> Dict[str, Any]:
        """Generate contextual upgrade prompt"""
        from .feature_access_service import UpgradeTrigger
        
        try:
            trigger_enum = None
            if trigger_type:
                trigger_enum = UpgradeTrigger(trigger_type)
            
            return self.feature_access.generate_upgrade_prompt(
                subscription_id=subscription_id,
                trigger_type=trigger_enum
            )
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid trigger type: {trigger_type}'
            }
    
    def check_upgrade_opportunities(
        self,
        subscription_id: int = None,
        include_all_subscriptions: bool = False
    ) -> Dict[str, Any]:
        """Check for upgrade opportunities across subscriptions"""
        return self.feature_access.check_upgrade_opportunities(
            subscription_id=subscription_id,
            include_all_subscriptions=include_all_subscriptions
        )
    
    def get_feature_usage_analytics(
        self,
        subscription_id: int = None,
        period: str = 'monthly'
    ) -> Dict[str, Any]:
        """Get feature usage analytics for upgrade insights"""
        return self.feature_access.get_feature_usage_analytics(
            subscription_id=subscription_id,
            period=period
        )
    
    def get_feature_access_status(
        self,
        subscription_id: int,
        feature_type: str = None
    ) -> Dict[str, Any]:
        """Get comprehensive feature access status"""
        from .feature_access_service import FeatureType
        
        try:
            feature_enum = None
            if feature_type:
                feature_enum = FeatureType(feature_type)
            
            return self.feature_access.get_feature_access_status(
                subscription_id=subscription_id,
                feature_type=feature_enum
            )
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid feature type: {feature_type}'
            }
    
    def enforce_feature_limits(
        self,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Enforce feature limits for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get current usage
            usage_summary = self.feature_access._get_usage_summary(subscription_id)
            
            # Check for limit violations
            violations = []
            for feature_name, usage_data in usage_summary.items():
                if usage_data['used'] > usage_data['limit'] and usage_data['limit'] > 0:
                    violations.append({
                        'feature': feature_name,
                        'used': usage_data['used'],
                        'limit': usage_data['limit'],
                        'excess': usage_data['used'] - usage_data['limit']
                    })
            
            # Generate upgrade prompts for violations
            upgrade_prompts = []
            for violation in violations:
                prompt = self.generate_upgrade_prompt(
                    subscription_id=subscription_id,
                    trigger_type='feature_limit_reached'
                )
                if prompt['success']:
                    upgrade_prompts.append(prompt['upgrade_prompt'])
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'violations': violations,
                'upgrade_prompts': upgrade_prompts,
                'total_violations': len(violations)
            }
            
        except Exception as e:
            logger.error(f"Error enforcing feature limits: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_upgrade_recommendations(
        self,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Get personalized upgrade recommendations"""
        try:
            # Get current usage and access status
            usage_analytics = self.get_feature_usage_analytics(subscription_id)
            access_status = self.get_feature_access_status(subscription_id)
            
            if not usage_analytics['success'] or not access_status['success']:
                return {
                    'success': False,
                    'error': 'Failed to get usage or access data'
                }
            
            # Analyze usage patterns
            recommendations = []
            
            # Check for high usage features
            for feature_name, usage_data in usage_analytics['analytics']['usage_summary'].items():
                if usage_data['percentage'] >= 80:
                    recommendations.append({
                        'type': 'high_usage',
                        'feature': feature_name,
                        'usage_percentage': usage_data['percentage'],
                        'message': f'You\'re using {feature_name} extensively. Consider upgrading for higher limits.',
                        'priority': 'high' if usage_data['percentage'] >= 90 else 'medium'
                    })
            
            # Check for unavailable features
            for feature_name, access_data in access_status['features'].items():
                if access_data['access_level'] == 'none':
                    recommendations.append({
                        'type': 'feature_unavailable',
                        'feature': feature_name,
                        'message': f'Upgrade to access {feature_name} features.',
                        'priority': 'medium'
                    })
            
            # Check for upgrade threshold triggers
            upgrade_opportunities = self.check_upgrade_opportunities(subscription_id)
            if upgrade_opportunities['success']:
                for opportunity in upgrade_opportunities['opportunities']:
                    recommendations.append({
                        'type': 'upgrade_opportunity',
                        'trigger': opportunity['trigger_type'],
                        'message': f'Upgrade opportunity detected: {opportunity["trigger_type"]}',
                        'priority': opportunity.get('priority', 'medium')
                    })
            
            # Sort by priority
            recommendations.sort(key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['priority']], reverse=True)
            
            return {
                'success': True,
                'subscription_id': subscription_id,
                'recommendations': recommendations,
                'total_recommendations': len(recommendations),
                'high_priority_count': len([r for r in recommendations if r['priority'] == 'high'])
            }
            
        except Exception as e:
            logger.error(f"Error getting upgrade recommendations: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # SMART UPGRADE PROMPTS INTEGRATION
    # ============================================================================
    
    def generate_smart_upgrade_prompt(
        self,
        subscription_id: int,
        feature_type: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate smart upgrade prompt with A/B testing and contextual suggestions"""
        from .feature_access_service import FeatureType
        try:
            feature_enum = FeatureType(feature_type) if feature_type else None
            return self.feature_access.generate_smart_upgrade_prompt(
                subscription_id=subscription_id,
                feature_type=feature_enum,
                context=context
            )
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid feature type: {feature_type}'
            }
    
    def get_upgrade_prompt_analytics(
        self,
        subscription_id: int = None,
        date_range: Tuple[datetime, datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics for upgrade prompts"""
        return self.feature_access.get_upgrade_prompt_analytics(
            subscription_id=subscription_id,
            date_range=date_range
        )
    
    def check_usage_approaching_limits(
        self,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Check if usage is approaching limits for any features"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            usage_summary = self.feature_access._get_usage_summary(subscription_id)
            approaching_limits = []
            
            for feature_name, feature_data in usage_summary['features'].items():
                if feature_data['usage_percentage'] >= 80:  # 80% threshold
                    approaching_limits.append({
                        'feature': feature_name,
                        'current_usage': feature_data['used'],
                        'limit': feature_data['limit'],
                        'usage_percentage': feature_data['usage_percentage'],
                        'upgrade_prompt': self.generate_smart_upgrade_prompt(
                            subscription_id, feature_name
                        )
                    })
            
            return {
                'success': True,
                'approaching_limits': approaching_limits,
                'total_features_approaching': len(approaching_limits)
            }
            
        except Exception as e:
            logger.error(f"Error checking usage approaching limits: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_contextual_upgrade_suggestions(
        self,
        subscription_id: int,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get contextual upgrade suggestions based on user behavior"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            usage_summary = self.feature_access._get_usage_summary(subscription_id)
            suggestions = []
            
            # Check for high usage patterns
            high_usage_features = []
            for feature_name, feature_data in usage_summary['features'].items():
                if feature_data['usage_percentage'] > 70:
                    high_usage_features.append(feature_name)
            
            if len(high_usage_features) >= 2:
                suggestions.append({
                    'type': 'high_usage',
                    'message': f'You\'re using {", ".join(high_usage_features)} extensively',
                    'recommendation': 'Upgrade for unlimited access',
                    'priority': 'high'
                })
            
            # Check for team collaboration needs
            if user_context and user_context.get('team_size', 0) > 1:
                suggestions.append({
                    'type': 'team_collaboration',
                    'message': 'Working with a team?',
                    'recommendation': 'Upgrade to add team members',
                    'priority': 'medium'
                })
            
            # Check for API integration needs
            if user_context and user_context.get('integration_needs'):
                suggestions.append({
                    'type': 'api_integration',
                    'message': 'Need API access?',
                    'recommendation': 'Upgrade to integrate with your tools',
                    'priority': 'medium'
                })
            
            # Check for support needs
            support_usage = usage_summary['features'].get('support_requests', {}).get('used', 0)
            if support_usage > 0:
                suggestions.append({
                    'type': 'support_needs',
                    'message': 'Need better support?',
                    'recommendation': 'Upgrade for priority assistance',
                    'priority': 'low'
                })
            
            return {
                'success': True,
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
            
        except Exception as e:
            logger.error(f"Error getting contextual upgrade suggestions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # ENHANCED USAGE TRACKING INTEGRATION
    # ============================================================================
    
    def track_feature_usage_real_time(
        self,
        subscription_id: int,
        feature_name: str,
        user_id: int = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Track real-time feature usage with immediate cache update"""
        return self.usage_tracker.track_feature_usage(
            subscription_id=subscription_id,
            feature_name=feature_name,
            user_id=user_id,
            metadata=metadata
        )
    
    def get_real_time_usage(
        self,
        subscription_id: int,
        feature_name: str = None
    ) -> Dict[str, Any]:
        """Get real-time usage data from cache"""
        return self.usage_tracker.get_real_time_usage(
            subscription_id=subscription_id,
            feature_name=feature_name
        )
    
    def get_comprehensive_usage_analytics(
        self,
        subscription_id: int = None,
        date_range: Tuple[datetime, datetime] = None,
        feature_name: str = None
    ) -> Dict[str, Any]:
        """Get comprehensive usage analytics and reporting"""
        return self.usage_tracker.get_usage_analytics(
            subscription_id=subscription_id,
            date_range=date_range,
            feature_name=feature_name
        )
    
    def get_overage_report(
        self,
        subscription_id: int = None,
        date_range: Tuple[datetime, datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive overage report"""
        return self.usage_tracker.get_overage_report(
            subscription_id=subscription_id,
            date_range=date_range
        )
    
    def check_usage_limits_and_overages(
        self,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Check current usage against limits and identify overages"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get real-time usage
            usage_data = self.get_real_time_usage(subscription_id)
            
            if not usage_data['success']:
                return usage_data
            
            # Get tier limits
            tier_limits = self._get_tier_limits(subscription.pricing_tier.tier_type)
            
            # Analyze usage against limits
            usage_analysis = {
                'subscription_id': subscription_id,
                'tier': subscription.pricing_tier.tier_type,
                'features': {},
                'total_overages': 0,
                'total_overage_cost': 0.0,
                'warnings': [],
                'critical_alerts': []
            }
            
            for feature_name, limit in tier_limits.items():
                if feature_name in usage_data['usage']:
                    current_usage = usage_data['usage'][f"{feature_name}_used"]
                    usage_percentage = (current_usage / limit * 100) if limit > 0 else 0
                    
                    feature_analysis = {
                        'current_usage': current_usage,
                        'limit': limit,
                        'usage_percentage': usage_percentage,
                        'is_overage': limit > 0 and current_usage > limit,
                        'is_warning': limit > 0 and usage_percentage >= 80,
                        'is_critical': limit > 0 and usage_percentage >= 95
                    }
                    
                    # Calculate overage cost
                    if feature_analysis['is_overage']:
                        overage_amount = current_usage - limit
                        overage_cost = overage_amount * self.usage_tracker.feature_pricing.get(feature_name, 0)
                        feature_analysis['overage_amount'] = overage_amount
                        feature_analysis['overage_cost'] = overage_cost
                        usage_analysis['total_overages'] += 1
                        usage_analysis['total_overage_cost'] += overage_cost
                    
                    # Add warnings and alerts
                    if feature_analysis['is_warning']:
                        usage_analysis['warnings'].append({
                            'feature': feature_name,
                            'message': f'{feature_name.replace("_", " ").title()} usage at {usage_percentage:.1f}%'
                        })
                    
                    if feature_analysis['is_critical']:
                        usage_analysis['critical_alerts'].append({
                            'feature': feature_name,
                            'message': f'{feature_name.replace("_", " ").title()} usage at {usage_percentage:.1f}% - CRITICAL'
                        })
                    
                    usage_analysis['features'][feature_name] = feature_analysis
            
            return {
                'success': True,
                'usage_analysis': usage_analysis,
                'generated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error checking usage limits and overages: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_usage_dashboard_data(
        self,
        subscription_id: int = None,
        date_range: Tuple[datetime, datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive usage dashboard data"""
        try:
            # Get usage analytics
            analytics_result = self.get_comprehensive_usage_analytics(
                subscription_id=subscription_id,
                date_range=date_range
            )
            
            # Get overage report
            overage_result = self.get_overage_report(
                subscription_id=subscription_id,
                date_range=date_range
            )
            
            # Get real-time usage if specific subscription
            real_time_data = None
            if subscription_id:
                real_time_data = self.get_real_time_usage(subscription_id)
            
            dashboard_data = {
                'analytics': analytics_result.get('analytics', {}) if analytics_result['success'] else {},
                'overage_report': overage_result.get('overage_report', {}) if overage_result['success'] else {},
                'real_time_usage': real_time_data.get('usage', {}) if real_time_data and real_time_data['success'] else {},
                'summary': {
                    'total_features_tracked': len(self.usage_tracker.trackable_features),
                    'total_subscriptions': 0,
                    'active_subscriptions': 0,
                    'subscriptions_with_overages': 0,
                    'total_overage_cost': 0.0
                }
            }
            
            # Calculate summary statistics
            if analytics_result['success']:
                dashboard_data['summary']['total_subscriptions'] = analytics_result['analytics'].get('total_records', 0)
            
            if overage_result['success']:
                dashboard_data['summary']['subscriptions_with_overages'] = len(
                    overage_result['overage_report'].get('subscription_overages', {})
                )
                dashboard_data['summary']['total_overage_cost'] = overage_result['overage_report'].get('total_overage_cost', 0.0)
            
            # Get active subscriptions count
            active_subscriptions = self.db.query(Subscription).filter(
                Subscription.status == 'active'
            ).count()
            dashboard_data['summary']['active_subscriptions'] = active_subscriptions
            
            return {
                'success': True,
                'dashboard_data': dashboard_data,
                'generated_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error getting usage dashboard data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_tier_limits(self, tier_type: str) -> Dict[str, int]:
        """Get feature limits for a specific tier"""
        limits = {}
        
        if tier_type == 'budget':
            limits = {
                'health_checkin': 4,
                'financial_report': 2,
                'ai_insight': 0,
                'custom_reports': 0,
                'team_members': 0,
                'api_access': 0,
                'support_requests': 1,
                'career_risk_management': 0,
                'dedicated_account_manager': 0
            }
        elif tier_type == 'mid_tier':
            limits = {
                'health_checkin': 12,
                'financial_report': 10,
                'ai_insight': 50,
                'custom_reports': 5,
                'team_members': 0,
                'api_access': 0,
                'support_requests': 3,
                'career_risk_management': -1,  # Unlimited
                'dedicated_account_manager': 0
            }
        elif tier_type == 'professional':
            limits = {
                'health_checkin': -1,  # Unlimited
                'financial_report': -1,  # Unlimited
                'ai_insight': -1,  # Unlimited
                'custom_reports': -1,  # Unlimited
                'team_members': 10,
                'api_access': 10000,  # 10,000 per hour
                'support_requests': -1,  # Unlimited
                'career_risk_management': -1,  # Unlimited
                'dedicated_account_manager': 1
            }
        
        return limits
    
    # ============================================================================
    # GRACEFUL DEGRADATION INTEGRATION
    # ============================================================================
    
    def check_feature_access_with_graceful_degradation(
        self,
        subscription_id: int,
        feature_type: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Check feature access with graceful degradation and user education"""
        from .feature_access_service import FeatureType
        try:
            feature_enum = FeatureType(feature_type)
            return self.feature_access.check_feature_access_with_graceful_degradation(
                subscription_id=subscription_id,
                feature_type=feature_enum,
                context=context
            )
        except ValueError:
            return {
                'success': False,
                'error': f'Invalid feature type: {feature_type}',
                'graceful_degradation': {
                    'message': 'Invalid feature requested.',
                    'suggestion': 'Please check the feature name and try again.',
                    'temporary_access': False
                }
            }
    
    def get_graceful_degradation_info(
        self,
        subscription_id: int,
        feature_type: str,
        access_decision: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get comprehensive graceful degradation information"""
        from .feature_access_service import FeatureType
        try:
            feature_enum = FeatureType(feature_type)
            
            # Get subscription info
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found',
                    'graceful_degradation': {
                        'message': 'Subscription not found.',
                        'suggestion': 'Please contact support for assistance.',
                        'temporary_access': False
                    }
                }
            
            # Get degradation info based on decision
            degradation_info = {
                'subscription_status': subscription.status,
                'tier_type': subscription.pricing_tier.tier_type,
                'feature_type': feature_type,
                'access_decision': access_decision,
                'graceful_options': self._get_graceful_options(subscription, feature_enum, access_decision, context)
            }
            
            return {
                'success': True,
                'degradation_info': degradation_info
            }
            
        except Exception as e:
            logger.error(f"Error getting graceful degradation info: {e}")
            return {
                'success': False,
                'error': str(e),
                'graceful_degradation': {
                    'message': 'We\'re experiencing technical difficulties.',
                    'suggestion': 'Please try again later or contact support.',
                    'temporary_access': False
                }
            }
    
    def _get_graceful_options(
        self,
        subscription: Subscription,
        feature_type: FeatureType,
        access_decision: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get graceful options based on access decision"""
        options = {
            'clear_messaging': self._get_clear_messaging(subscription, feature_type, access_decision),
            'alternative_suggestions': self._get_alternative_suggestions(subscription, feature_type),
            'temporary_access': self._get_temporary_access_info(subscription, feature_type, context),
            'user_education': self._get_user_education_info(subscription, feature_type),
            'next_steps': self._get_next_steps(subscription, feature_type, access_decision)
        }
        
        return options
    
    def _get_clear_messaging(
        self,
        subscription: Subscription,
        feature_type: FeatureType,
        access_decision: str
    ) -> Dict[str, Any]:
        """Get clear messaging based on access decision"""
        feature_name = feature_type.value.replace('_', ' ').title()
        tier_type = subscription.pricing_tier.tier_type
        
        messaging = {
            'title': '',
            'message': '',
            'subtitle': '',
            'urgency': 'low'
        }
        
        if access_decision == 'limit_reached':
            messaging.update({
                'title': f'Monthly Limit Reached',
                'message': f'You\'ve used all your {feature_name} for this month.',
                'subtitle': f'Your {tier_type.replace("_", " ").title()} plan includes a monthly limit for {feature_name}.',
                'urgency': 'medium'
            })
        elif access_decision == 'feature_unavailable':
            messaging.update({
                'title': f'{feature_name} Not Available',
                'message': f'{feature_name} is not included in your current plan.',
                'subtitle': f'Upgrade to access {feature_name} and unlock premium features.',
                'urgency': 'low'
            })
        elif access_decision == 'subscription_inactive':
            messaging.update({
                'title': 'Subscription Inactive',
                'message': 'Your subscription is currently paused or canceled.',
                'subtitle': 'Reactivate your subscription to restore access to all features.',
                'urgency': 'high'
            })
        elif access_decision == 'trial_expired':
            messaging.update({
                'title': 'Trial Expired',
                'message': 'Your free trial has ended.',
                'subtitle': 'Choose a plan to continue using MINGUS and unlock premium features.',
                'urgency': 'medium'
            })
        else:
            messaging.update({
                'title': 'Access Restricted',
                'message': f'Access to {feature_name} is currently restricted.',
                'subtitle': 'Please contact support for assistance.',
                'urgency': 'low'
            })
        
        return messaging
    
    def _get_alternative_suggestions(
        self,
        subscription: Subscription,
        feature_type: FeatureType
    ) -> List[Dict[str, Any]]:
        """Get alternative feature suggestions"""
        tier_type = subscription.pricing_tier.tier_type
        alternatives = []
        
        # Define alternative mappings
        alternative_mappings = {
            'health_checkin': [
                {
                    'name': 'Financial Report',
                    'description': 'Get a comprehensive financial overview',
                    'available': self._is_feature_available_in_tier('financial_report', tier_type),
                    'action': 'Generate Report',
                    'icon': '📊'
                },
                {
                    'name': 'Account Dashboard',
                    'description': 'View your financial health overview',
                    'available': True,
                    'action': 'View Dashboard',
                    'icon': '🏠'
                }
            ],
            'financial_report': [
                {
                    'name': 'Health Check-in',
                    'description': 'Quick financial health assessment',
                    'available': self._is_feature_available_in_tier('health_checkin', tier_type),
                    'action': 'Start Check-in',
                    'icon': '❤️'
                },
                {
                    'name': 'AI Insight',
                    'description': 'AI-powered financial analysis',
                    'available': self._is_feature_available_in_tier('ai_insight', tier_type),
                    'action': 'Get Insight',
                    'icon': '🤖'
                }
            ],
            'ai_insight': [
                {
                    'name': 'Health Check-in',
                    'description': 'Basic financial health assessment',
                    'available': self._is_feature_available_in_tier('health_checkin', tier_type),
                    'action': 'Start Check-in',
                    'icon': '❤️'
                },
                {
                    'name': 'Financial Report',
                    'description': 'Detailed financial analysis',
                    'available': self._is_feature_available_in_tier('financial_report', tier_type),
                    'action': 'Generate Report',
                    'icon': '📊'
                }
            ],
            'custom_reports': [
                {
                    'name': 'Financial Report',
                    'description': 'Standard financial reports',
                    'available': self._is_feature_available_in_tier('financial_report', tier_type),
                    'action': 'Generate Report',
                    'icon': '📊'
                },
                {
                    'name': 'AI Insight',
                    'description': 'AI-generated insights',
                    'available': self._is_feature_available_in_tier('ai_insight', tier_type),
                    'action': 'Get Insight',
                    'icon': '🤖'
                }
            ]
        }
        
        feature_key = feature_type.value
        if feature_key in alternative_mappings:
            for alt in alternative_mappings[feature_key]:
                if alt['available']:
                    alternatives.append(alt)
        
        # Add universal alternatives
        alternatives.extend([
            {
                'name': 'Support Center',
                'description': 'Get help and find answers',
                'available': True,
                'action': 'Get Help',
                'icon': '❓'
            },
            {
                'name': 'Account Settings',
                'description': 'Manage your account and preferences',
                'available': True,
                'action': 'Manage Account',
                'icon': '⚙️'
            }
        ])
        
        return alternatives
    
    def _get_temporary_access_info(
        self,
        subscription: Subscription,
        feature_type: FeatureType,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get temporary access information"""
        # Check if temporary access should be granted
        should_grant = self._should_grant_temporary_access(subscription, feature_type, context)
        
        temp_access_info = {
            'available': should_grant,
            'reason': None,
            'duration': None,
            'conditions': [],
            'message': ''
        }
        
        if should_grant:
            temp_access_info.update({
                'reason': 'Good customer standing',
                'duration': '24 hours',
                'conditions': [
                    'One-time use only',
                    'Valid for 24 hours',
                    'Subject to fair use policy'
                ],
                'message': 'We\'ve granted you temporary access based on your excellent customer standing.'
            })
        else:
            temp_access_info.update({
                'message': 'Temporary access is not available for this request.',
                'conditions': [
                    'Available for long-term customers',
                    'Based on usage history',
                    'For critical features only'
                ]
            })
        
        return temp_access_info
    
    def _get_user_education_info(
        self,
        subscription: Subscription,
        feature_type: FeatureType
    ) -> Dict[str, Any]:
        """Get user education information about tier benefits"""
        tier_type = subscription.pricing_tier.tier_type
        feature_name = feature_type.value.replace('_', ' ').title()
        
        education_info = {
            'current_tier': {
                'name': tier_type.replace('_', ' ').title(),
                'description': self._get_tier_description(tier_type),
                'current_benefits': self._get_current_tier_benefits(tier_type),
                'limitations': self._get_current_tier_limitations(tier_type)
            },
            'upgrade_path': self._get_upgrade_path(tier_type, feature_type),
            'feature_education': {
                'title': f'About {feature_name}',
                'description': self._get_feature_description(feature_type),
                'benefits': self._get_feature_benefits(feature_type),
                'use_cases': self._get_feature_use_cases(feature_type)
            },
            'value_proposition': self._get_value_proposition(tier_type, feature_type)
        }
        
        return education_info
    
    def _get_next_steps(
        self,
        subscription: Subscription,
        feature_type: FeatureType,
        access_decision: str
    ) -> List[Dict[str, Any]]:
        """Get next steps for the user"""
        next_steps = []
        
        if access_decision == 'limit_reached':
            next_steps.extend([
                {
                    'action': 'upgrade',
                    'title': 'Upgrade Your Plan',
                    'description': 'Unlock unlimited access to this feature',
                    'priority': 'high',
                    'cta_text': 'View Upgrade Options'
                },
                {
                    'action': 'wait',
                    'title': 'Wait Until Next Month',
                    'description': 'Your usage will reset on the 1st of next month',
                    'priority': 'medium',
                    'cta_text': 'View Usage Calendar'
                },
                {
                    'action': 'alternatives',
                    'title': 'Try Alternative Features',
                    'description': 'Explore other features available in your plan',
                    'priority': 'low',
                    'cta_text': 'Browse Alternatives'
                }
            ])
        elif access_decision == 'feature_unavailable':
            next_steps.extend([
                {
                    'action': 'upgrade',
                    'title': 'Upgrade to Access Feature',
                    'description': 'This feature is available in higher-tier plans',
                    'priority': 'high',
                    'cta_text': 'View Plans'
                },
                {
                    'action': 'learn',
                    'title': 'Learn About the Feature',
                    'description': 'Understand what this feature offers',
                    'priority': 'medium',
                    'cta_text': 'Learn More'
                },
                {
                    'action': 'alternatives',
                    'title': 'Explore Alternatives',
                    'description': 'Find similar features in your current plan',
                    'priority': 'low',
                    'cta_text': 'Browse Alternatives'
                }
            ])
        elif access_decision == 'subscription_inactive':
            next_steps.extend([
                {
                    'action': 'reactivate',
                    'title': 'Reactivate Subscription',
                    'description': 'Restore access to all your features and data',
                    'priority': 'high',
                    'cta_text': 'Reactivate Now'
                },
                {
                    'action': 'contact_support',
                    'title': 'Contact Support',
                    'description': 'Get help with your subscription',
                    'priority': 'medium',
                    'cta_text': 'Contact Support'
                }
            ])
        
        return next_steps
    
    def _should_grant_temporary_access(
        self,
        subscription: Subscription,
        feature_type: FeatureType,
        context: Dict[str, Any] = None
    ) -> bool:
        """Determine if temporary access should be granted"""
        # This would integrate with the feature access service logic
        # For now, return False as a conservative approach
        return False
    
    def _is_feature_available_in_tier(self, feature_type: str, tier_type: str) -> bool:
        """Check if feature is available in the specified tier"""
        tier_limits = self._get_tier_limits(tier_type)
        limit = tier_limits.get(feature_type, 0)
        return limit != 0
    
    def _get_tier_description(self, tier_type: str) -> str:
        """Get tier description"""
        descriptions = {
            'budget': 'Perfect for individuals getting started with financial wellness',
            'mid_tier': 'Enhanced features for serious financial management',
            'professional': 'Complete solution for professionals and teams'
        }
        return descriptions.get(tier_type, '')
    
    def _get_current_tier_benefits(self, tier_type: str) -> List[str]:
        """Get current tier benefits"""
        benefits = {
            'budget': [
                '4 health check-ins per month',
                '2 financial reports per month',
                'Basic support',
                'Account dashboard'
            ],
            'mid_tier': [
                '12 health check-ins per month',
                '10 financial reports per month',
                '50 AI insights per month',
                '5 custom reports per month',
                'Unlimited career risk management',
                'Priority email support'
            ],
            'professional': [
                'Unlimited all features',
                '10 team members',
                '10,000 API calls/hour',
                'Dedicated account manager',
                'Phone + email support',
                'Custom integrations'
            ]
        }
        return benefits.get(tier_type, [])
    
    def _get_current_tier_limitations(self, tier_type: str) -> List[str]:
        """Get current tier limitations"""
        limitations = {
            'budget': [
                'Limited feature usage',
                'No AI insights',
                'No custom reports',
                'No team features',
                'Basic support only'
            ],
            'mid_tier': [
                'Some usage limits still apply',
                'No team collaboration',
                'Limited API access',
                'No dedicated account manager'
            ],
            'professional': [
                'Higher cost',
                'May be overkill for individual users'
            ]
        }
        return limitations.get(tier_type, [])
    
    def _get_upgrade_path(self, tier_type: str, feature_type: FeatureType) -> Dict[str, Any]:
        """Get upgrade path information"""
        feature_name = feature_type.value.replace('_', ' ').title()
        
        if tier_type == 'budget':
            return {
                'recommended_tier': 'mid_tier',
                'price_difference': '+$20/month',
                'key_benefits': [
                    f'Access to {feature_name}',
                    '50 AI insights per month',
                    '10 financial reports per month',
                    '5 custom reports per month',
                    'Unlimited career risk management'
                ],
                'upgrade_message': f'Upgrade to Mid-Tier to unlock {feature_name} and premium features.'
            }
        elif tier_type == 'mid_tier':
            return {
                'recommended_tier': 'professional',
                'price_difference': '+$40/month',
                'key_benefits': [
                    'Unlimited all features',
                    '10 team members',
                    '10,000 API calls/hour',
                    'Dedicated account manager',
                    'Phone + email support'
                ],
                'upgrade_message': 'Upgrade to Professional for unlimited access to all features.'
            }
        
        return {}
    
    def _get_feature_description(self, feature_type: FeatureType) -> str:
        """Get feature description"""
        descriptions = {
            'health_checkin': 'Quick assessment of your financial health and spending patterns',
            'financial_report': 'Comprehensive analysis of your financial situation and trends',
            'ai_insight': 'AI-powered insights and recommendations for financial optimization',
            'custom_reports': 'Customizable reports tailored to your specific financial needs',
            'team_members': 'Collaborate with team members on financial planning and analysis',
            'api_access': 'Programmatic access to MINGUS features and data',
            'support_requests': 'Priority support for technical and financial questions',
            'career_risk_management': 'Tools and insights for managing career-related financial risks',
            'dedicated_account_manager': 'Personal account manager for strategic guidance and support'
        }
        return descriptions.get(feature_type.value, '')
    
    def _get_feature_benefits(self, feature_type: FeatureType) -> List[str]:
        """Get feature benefits"""
        benefits = {
            'health_checkin': [
                'Quick financial health assessment',
                'Identify spending patterns',
                'Track progress over time',
                'Get actionable insights'
            ],
            'financial_report': [
                'Comprehensive financial analysis',
                'Detailed spending breakdown',
                'Trend identification',
                'Professional-grade reporting'
            ],
            'ai_insight': [
                'AI-powered recommendations',
                'Predictive analytics',
                'Personalized insights',
                'Optimization suggestions'
            ],
            'custom_reports': [
                'Tailored to your needs',
                'Flexible reporting options',
                'Professional presentation',
                'Export capabilities'
            ]
        }
        return benefits.get(feature_type.value, [])
    
    def _get_feature_use_cases(self, feature_type: FeatureType) -> List[str]:
        """Get feature use cases"""
        use_cases = {
            'health_checkin': [
                'Monthly financial review',
                'Before major purchases',
                'After life changes',
                'Regular wellness monitoring'
            ],
            'financial_report': [
                'Annual financial planning',
                'Business financial analysis',
                'Investment decision making',
                'Tax preparation'
            ],
            'ai_insight': [
                'Financial optimization',
                'Investment recommendations',
                'Risk assessment',
                'Trend analysis'
            ],
            'custom_reports': [
                'Client presentations',
                'Board reporting',
                'Compliance documentation',
                'Strategic planning'
            ]
        }
        return use_cases.get(feature_type.value, [])
    
    def _get_value_proposition(self, tier_type: str, feature_type: FeatureType) -> Dict[str, Any]:
        """Get value proposition for the feature"""
        feature_name = feature_type.value.replace('_', ' ').title()
        
        value_props = {
            'budget': {
                'title': f'Unlock the Power of {feature_name}',
                'message': f'Your current plan gives you a taste of {feature_name}. Upgrade to experience the full potential.',
                'roi_message': 'Invest in your financial future with enhanced capabilities',
                'time_to_value': 'Immediate access upon upgrade'
            },
            'mid_tier': {
                'title': f'Go Unlimited with {feature_name}',
                'message': f'Remove all limits and unlock unlimited {feature_name} with professional features.',
                'roi_message': 'Scale your financial operations without constraints',
                'time_to_value': 'Instant unlimited access'
            }
        }
        
        return value_props.get(tier_type, {})
    
    # ============================================================================
    # STRIPE CUSTOMER PORTAL INTEGRATION
    # ============================================================================
    
    def create_stripe_portal_session(
        self,
        customer_id: int,
        return_url: str = None,
        configuration_id: str = None
    ) -> Dict[str, Any]:
        """Create a Stripe Customer Portal session for seamless billing management"""
        return self.stripe_portal.create_customer_portal_session(
            customer_id=customer_id,
            return_url=return_url,
            configuration_id=configuration_id
        )
    
    def create_limited_portal_session(
        self,
        customer_id: int,
        allowed_features: List[str],
        return_url: str = None
    ) -> Dict[str, Any]:
        """Create a limited portal session with specific features only"""
        return self.stripe_portal.create_limited_portal_session(
            customer_id=customer_id,
            allowed_features=allowed_features,
            return_url=return_url
        )
    
    def get_customer_portal_access(
        self,
        customer_id: int,
        access_type: str = 'full'
    ) -> Dict[str, Any]:
        """Get customer portal access information and permissions"""
        return self.stripe_portal.get_customer_portal_access(
            customer_id=customer_id,
            access_type=access_type
        )
    
    def create_portal_configuration(
        self,
        configuration_name: str = "MINGUS Customer Portal",
        features: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a custom Stripe Customer Portal configuration"""
        return self.stripe_portal.create_portal_configuration(
            configuration_name=configuration_name,
            features=features
        )
    
    def get_portal_configurations(self) -> Dict[str, Any]:
        """Get all available portal configurations"""
        return self.stripe_portal.get_portal_configurations()
    
    def update_portal_configuration(
        self,
        configuration_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing portal configuration"""
        return self.stripe_portal.update_portal_configuration(
            configuration_id=configuration_id,
            updates=updates
        )
    
    def handle_portal_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe Customer Portal webhook events"""
        return self.stripe_portal.handle_portal_webhook(event_data)
    
    def apply_custom_portal_branding(
        self,
        session_or_config_id: str,
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom branding to a portal session or configuration"""
        try:
            # Validate branding data
            if not branding:
                return {
                    'success': False,
                    'error': 'No branding data provided'
                }
            
            # Apply branding to portal configuration
            branding_config = {
                'business_profile': {
                    'headline': branding.get('company_name', 'MINGUS Financial Management'),
                    'privacy_policy_url': branding.get('privacy_policy_url', 'https://mingus.com/privacy'),
                    'terms_of_service_url': branding.get('terms_of_service_url', 'https://mingus.com/terms'),
                    'support_url': branding.get('support_url', 'https://mingus.com/support')
                }
            }
            
            # Update portal configuration with branding
            update_result = self.stripe_portal.update_portal_configuration(
                configuration_id=session_or_config_id,
                updates=branding_config
            )
            
            if update_result['success']:
                logger.info(f"Applied custom branding to portal configuration: {session_or_config_id}")
            
            return update_result
            
        except Exception as e:
            logger.error(f"Error applying custom portal branding: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def synchronize_portal_data(
        self,
        customer_id: str,
        session_id: str,
        action: str
    ) -> Dict[str, Any]:
        """Synchronize data from Stripe Customer Portal"""
        try:
            # Get customer from database
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Initialize synchronization tracking
            synchronized_data = {
                'customer_updated': False,
                'subscription_changed': False,
                'payment_method_updated': False,
                'changes': []
            }
            
            # Synchronize based on action
            if action in ['payment_updated', 'payment_method_updated']:
                sync_result = self._synchronize_payment_methods(customer)
                synchronized_data['payment_method_updated'] = sync_result['success']
                synchronized_data['changes'].extend(sync_result.get('changes', []))
            
            elif action in ['subscription_changed', 'subscription_updated', 'subscription_canceled']:
                sync_result = self._synchronize_subscription(customer)
                synchronized_data['subscription_changed'] = sync_result['success']
                synchronized_data['changes'].extend(sync_result.get('changes', []))
            
            elif action in ['customer_updated', 'profile_updated']:
                sync_result = self._synchronize_customer_profile(customer)
                synchronized_data['customer_updated'] = sync_result['success']
                synchronized_data['changes'].extend(sync_result.get('changes', []))
            
            elif action == 'unknown':
                # Perform full synchronization
                payment_sync = self._synchronize_payment_methods(customer)
                subscription_sync = self._synchronize_subscription(customer)
                profile_sync = self._synchronize_customer_profile(customer)
                
                synchronized_data['payment_method_updated'] = payment_sync['success']
                synchronized_data['subscription_changed'] = subscription_sync['success']
                synchronized_data['customer_updated'] = profile_sync['success']
                
                synchronized_data['changes'].extend(payment_sync.get('changes', []))
                synchronized_data['changes'].extend(subscription_sync.get('changes', []))
                synchronized_data['changes'].extend(profile_sync.get('changes', []))
            
            # Log synchronization event
            self._log_portal_synchronization(
                customer_id=customer.id,
                session_id=session_id,
                action=action,
                synchronized_data=synchronized_data
            )
            
            return {
                'success': True,
                'synchronized_data': synchronized_data,
                'redirect_url': self._get_redirect_url_for_action(action)
            }
            
        except Exception as e:
            logger.error(f"Error synchronizing portal data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _synchronize_payment_methods(self, customer: Customer) -> Dict[str, Any]:
        """Synchronize payment methods from Stripe"""
        try:
            changes = []
            
            # Get payment methods from Stripe
            stripe_payment_methods = self.stripe.PaymentMethod.list(
                customer=customer.stripe_customer_id,
                type='card'
            )
            
            # Get local payment methods
            local_payment_methods = self.db.query(PaymentMethod).filter(
                PaymentMethod.customer_id == customer.id
            ).all()
            
            # Update local payment methods
            for stripe_pm in stripe_payment_methods.data:
                local_pm = next(
                    (pm for pm in local_payment_methods if pm.stripe_payment_method_id == stripe_pm.id),
                    None
                )
                
                if not local_pm:
                    # Create new payment method
                    new_pm = PaymentMethod(
                        customer_id=customer.id,
                        stripe_payment_method_id=stripe_pm.id,
                        type=stripe_pm.type,
                        card_brand=stripe_pm.card.brand if stripe_pm.card else None,
                        card_last4=stripe_pm.card.last4 if stripe_pm.card else None,
                        is_default=stripe_pm.metadata.get('is_default', False)
                    )
                    self.db.add(new_pm)
                    changes.append(f"Added payment method: {stripe_pm.card.last4 if stripe_pm.card else 'Unknown'}")
                else:
                    # Update existing payment method
                    local_pm.is_default = stripe_pm.metadata.get('is_default', False)
                    changes.append(f"Updated payment method: {local_pm.card_last4}")
            
            # Remove payment methods that no longer exist in Stripe
            stripe_pm_ids = [pm.id for pm in stripe_payment_methods.data]
            for local_pm in local_payment_methods:
                if local_pm.stripe_payment_method_id not in stripe_pm_ids:
                    self.db.delete(local_pm)
                    changes.append(f"Removed payment method: {local_pm.card_last4}")
            
            self.db.commit()
            
            return {
                'success': True,
                'changes': changes
            }
            
        except Exception as e:
            logger.error(f"Error synchronizing payment methods: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _synchronize_subscription(self, customer: Customer) -> Dict[str, Any]:
        """Synchronize subscription data from Stripe"""
        try:
            changes = []
            
            # Get subscription from Stripe
            stripe_subscriptions = self.stripe.Subscription.list(
                customer=customer.stripe_customer_id,
                limit=1
            )
            
            if not stripe_subscriptions.data:
                return {
                    'success': True,
                    'changes': ['No active subscription found']
                }
            
            stripe_sub = stripe_subscriptions.data[0]
            
            # Get local subscription
            local_subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == stripe_sub.id
            ).first()
            
            if local_subscription:
                # Update existing subscription
                old_status = local_subscription.status
                old_amount = local_subscription.amount
                
                local_subscription.status = stripe_sub.status
                local_subscription.current_period_start = datetime.fromtimestamp(stripe_sub.current_period_start)
                local_subscription.current_period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
                local_subscription.amount = stripe_sub.items.data[0].price.unit_amount / 100
                local_subscription.cancel_at_period_end = stripe_sub.cancel_at_period_end
                
                if stripe_sub.canceled_at:
                    local_subscription.canceled_at = datetime.fromtimestamp(stripe_sub.canceled_at)
                
                if old_status != local_subscription.status:
                    changes.append(f"Subscription status changed: {old_status} → {local_subscription.status}")
                
                if old_amount != local_subscription.amount:
                    changes.append(f"Subscription amount changed: ${old_amount} → ${local_subscription.amount}")
                
                if local_subscription.cancel_at_period_end:
                    changes.append("Subscription scheduled for cancellation at period end")
            else:
                # Create new subscription
                new_subscription = Subscription(
                    customer_id=customer.id,
                    stripe_subscription_id=stripe_sub.id,
                    status=stripe_sub.status,
                    current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
                    current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end),
                    amount=stripe_sub.items.data[0].price.unit_amount / 100,
                    cancel_at_period_end=stripe_sub.cancel_at_period_end
                )
                self.db.add(new_subscription)
                changes.append("New subscription created")
            
            self.db.commit()
            
            return {
                'success': True,
                'changes': changes
            }
            
        except Exception as e:
            logger.error(f"Error synchronizing subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _synchronize_customer_profile(self, customer: Customer) -> Dict[str, Any]:
        """Synchronize customer profile data from Stripe"""
        try:
            changes = []
            
            # Get customer from Stripe
            stripe_customer = self.stripe.Customer.retrieve(customer.stripe_customer_id)
            
            # Update customer information
            if stripe_customer.email and stripe_customer.email != customer.email:
                old_email = customer.email
                customer.email = stripe_customer.email
                changes.append(f"Email updated: {old_email} → {customer.email}")
            
            if stripe_customer.name and stripe_customer.name != customer.name:
                old_name = customer.name
                customer.name = stripe_customer.name
                changes.append(f"Name updated: {old_name} → {customer.name}")
            
            if stripe_customer.address:
                customer.address = stripe_customer.address
                changes.append("Address updated")
            
            if stripe_customer.phone and stripe_customer.phone != customer.phone:
                old_phone = customer.phone
                customer.phone = stripe_customer.phone
                changes.append(f"Phone updated: {old_phone} → {customer.phone}")
            
            self.db.commit()
            
            return {
                'success': True,
                'changes': changes
            }
            
        except Exception as e:
            logger.error(f"Error synchronizing customer profile: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_redirect_url_for_action(self, action: str) -> str:
        """Get appropriate redirect URL based on portal action"""
        redirect_urls = {
            'payment_updated': '/dashboard/billing/payment-methods',
            'payment_method_updated': '/dashboard/billing/payment-methods',
            'subscription_changed': '/dashboard/billing/subscription',
            'subscription_updated': '/dashboard/billing/subscription',
            'subscription_canceled': '/dashboard/billing/subscription',
            'customer_updated': '/dashboard/profile',
            'profile_updated': '/dashboard/profile',
            'unknown': '/dashboard/billing'
        }
        
        return redirect_urls.get(action, '/dashboard/billing')
    
    def _log_portal_synchronization(
        self,
        customer_id: int,
        session_id: str,
        action: str,
        synchronized_data: Dict[str, Any]
    ) -> None:
        """Log portal synchronization event"""
        try:
            # Create audit log entry
            audit_log = AuditLog(
                customer_id=customer_id,
                event_type=AuditEventType.PORTAL_SYNCHRONIZATION,
                event_description=f"Portal synchronization for action: {action}",
                severity=AuditSeverity.INFO,
                metadata={
                    'session_id': session_id,
                    'action': action,
                    'synchronized_data': synchronized_data,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            logger.info(f"Portal synchronization logged for customer {customer_id}, action: {action}")
            
        except Exception as e:
            logger.error(f"Error logging portal synchronization: {e}")