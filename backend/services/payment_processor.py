"""
Comprehensive Payment Processing Service for MINGUS
Handles all subscription billing scenarios with Stripe integration
"""
import stripe
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.subscription import (
    Customer, Subscription, PaymentMethod, BillingHistory, 
    PricingTier, FeatureUsage, AuditLog, AuditEventType, AuditSeverity
)
from ..config.base import Config

# Configure logging
logger = logging.getLogger(__name__)

class PaymentProcessorError(Exception):
    """Custom exception for payment processing errors"""
    pass

class PaymentProcessor:
    """Main payment processing service for MINGUS subscriptions"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.stripe = stripe
        self.stripe.api_key = config.STRIPE_SECRET_KEY
        
    def create_customer(self, user_id: int, email: str, name: str = None) -> Customer:
        """Create a new Stripe customer and link to MINGUS user"""
        try:
            # Create Stripe customer
            stripe_customer = self.stripe.Customer.create(
                email=email,
                name=name,
                metadata={'mingus_user_id': user_id}
            )
            
            # Create local customer record
            customer = Customer(
                user_id=user_id,
                stripe_customer_id=stripe_customer.id,
                email=email,
                name=name
            )
            
            self.db.add(customer)
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CREATED,
                user_id=user_id,
                customer_id=customer.id,
                event_description=f"Customer created: {email}",
                metadata={'stripe_customer_id': stripe_customer.id}
            )
            
            logger.info(f"Created customer {customer.id} for user {user_id}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise PaymentProcessorError(f"Failed to create customer: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating customer: {e}")
            self.db.rollback()
            raise PaymentProcessorError(f"Database error: {str(e)}")
    
    def create_subscription(
        self, 
        customer_id: int, 
        pricing_tier_id: int, 
        billing_cycle: str = 'monthly',
        trial_days: int = 0
    ) -> Subscription:
        """Create a new subscription with Stripe"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            pricing_tier = self.db.query(PricingTier).filter(PricingTier.id == pricing_tier_id).first()
            
            if not customer or not pricing_tier:
                raise PaymentProcessorError("Customer or pricing tier not found")
            
            # Get appropriate Stripe price ID
            price_id = (pricing_tier.stripe_price_id_monthly if billing_cycle == 'monthly' 
                       else pricing_tier.stripe_price_id_yearly)
            
            if not price_id:
                raise PaymentProcessorError(f"No Stripe price ID configured for {billing_cycle} billing")
            
            # Create Stripe subscription
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
            
            if trial_days > 0:
                subscription_data['trial_period_days'] = trial_days
            
            stripe_subscription = self.stripe.Subscription.create(**subscription_data)
            
            # Calculate amounts
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
            
            # Log audit event
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CREATED,
                user_id=customer.user_id,
                customer_id=customer_id,
                subscription_id=subscription.id,
                event_description=f"Subscription created: {pricing_tier.name} ({billing_cycle})",
                metadata={
                    'stripe_subscription_id': stripe_subscription.id,
                    'pricing_tier': pricing_tier.tier_type.value,
                    'billing_cycle': billing_cycle,
                    'amount': amount
                }
            )
            
            logger.info(f"Created subscription {subscription.id} for customer {customer_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise PaymentProcessorError(f"Failed to create subscription: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error creating subscription: {e}")
            self.db.rollback()
            raise PaymentProcessorError(f"Database error: {str(e)}")
    
    def process_payment(self, invoice_id: str) -> Dict[str, Any]:
        """Process a payment for an invoice"""
        try:
            # Retrieve Stripe invoice
            stripe_invoice = self.stripe.Invoice.retrieve(invoice_id)
            
            # Find local invoice record
            invoice = self.db.query(BillingHistory).filter(
                BillingHistory.stripe_invoice_id == invoice_id
            ).first()
            
            if not invoice:
                # Create invoice record if it doesn't exist
                customer = self.db.query(Customer).filter(
                    Customer.stripe_customer_id == stripe_invoice.customer
                ).first()
                
                if not customer:
                    raise PaymentProcessorError("Customer not found for invoice")
                
                invoice = BillingHistory(
                    customer_id=customer.id,
                    stripe_invoice_id=invoice_id,
                    amount_due=stripe_invoice.amount_due / 100,  # Convert from cents
                    amount_paid=stripe_invoice.amount_paid / 100,
                    currency=stripe_invoice.currency.upper(),
                    status=stripe_invoice.status,
                    paid=stripe_invoice.paid,
                    invoice_date=datetime.fromtimestamp(stripe_invoice.created),
                    description=stripe_invoice.description
                )
                
                self.db.add(invoice)
                self.db.commit()
            
            # Update invoice status
            invoice.status = stripe_invoice.status
            invoice.amount_paid = stripe_invoice.amount_paid / 100
            invoice.paid = stripe_invoice.paid
            
            if stripe_invoice.paid:
                invoice.paid_date = datetime.utcnow()
            
            self.db.commit()
            
            # Log payment event
            event_type = (AuditEventType.PAYMENT_SUCCEEDED if stripe_invoice.paid 
                         else AuditEventType.PAYMENT_FAILED)
            
            self._log_audit_event(
                event_type=event_type,
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                event_description=f"Payment {'succeeded' if stripe_invoice.paid else 'failed'} for invoice {invoice_id}",
                metadata={
                    'stripe_invoice_id': invoice_id,
                    'amount_paid': invoice.amount_paid,
                    'status': invoice.status
                }
            )
            
            return {
                'invoice_id': invoice.id,
                'stripe_invoice_id': invoice_id,
                'status': invoice.status,
                'paid': invoice.paid,
                'amount_paid': invoice.amount_paid
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing payment: {e}")
            raise PaymentProcessorError(f"Failed to process payment: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error processing payment: {e}")
            self.db.rollback()
            raise PaymentProcessorError(f"Database error: {str(e)}")
    
    def update_subscription(
        self, 
        subscription_id: int, 
        pricing_tier_id: int = None,
        billing_cycle: str = None,
        cancel_at_period_end: bool = None
    ) -> Subscription:
        """Update subscription details"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise PaymentProcessorError("Subscription not found")
            
            # Store old values for audit
            old_values = {
                'pricing_tier_id': subscription.pricing_tier_id,
                'billing_cycle': subscription.billing_cycle,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
            
            # Update Stripe subscription
            stripe_update_data = {}
            
            if pricing_tier_id is not None:
                pricing_tier = self.db.query(PricingTier).filter(
                    PricingTier.id == pricing_tier_id
                ).first()
                
                if not pricing_tier:
                    raise PaymentProcessorError("Pricing tier not found")
                
                # Get new price ID
                price_id = (pricing_tier.stripe_price_id_monthly if billing_cycle == 'monthly' 
                           else pricing_tier.stripe_price_id_yearly)
                
                stripe_update_data['items'] = [{
                    'id': self._get_stripe_subscription_item_id(subscription.stripe_subscription_id),
                    'price': price_id
                }]
                
                subscription.pricing_tier_id = pricing_tier_id
                subscription.amount = (pricing_tier.monthly_price if billing_cycle == 'monthly' 
                                     else pricing_tier.yearly_price)
            
            if billing_cycle is not None:
                subscription.billing_cycle = billing_cycle
            
            if cancel_at_period_end is not None:
                stripe_update_data['cancel_at_period_end'] = cancel_at_period_end
                subscription.cancel_at_period_end = cancel_at_period_end
                
                if cancel_at_period_end:
                    subscription.canceled_at = datetime.utcnow()
            
            # Update Stripe subscription
            if stripe_update_data:
                self.stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    **stripe_update_data
                )
            
            # Get updated Stripe subscription
            stripe_subscription = self.stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )
            
            # Update local subscription
            subscription.status = stripe_subscription.status
            subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
            
            self.db.commit()
            
            # Log audit event
            changed_fields = []
            new_values = {
                'pricing_tier_id': subscription.pricing_tier_id,
                'billing_cycle': subscription.billing_cycle,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
            
            for field, old_value in old_values.items():
                if new_values[field] != old_value:
                    changed_fields.append(field)
            
            if changed_fields:
                self._log_audit_event(
                    event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                    customer_id=subscription.customer_id,
                    subscription_id=subscription.id,
                    event_description=f"Subscription updated: {', '.join(changed_fields)}",
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields
                )
            
            logger.info(f"Updated subscription {subscription_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            raise PaymentProcessorError(f"Failed to update subscription: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error updating subscription: {e}")
            self.db.rollback()
            raise PaymentProcessorError(f"Database error: {str(e)}")
    
    def cancel_subscription(self, subscription_id: int, immediate: bool = False) -> Subscription:
        """Cancel a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise PaymentProcessorError("Subscription not found")
            
            # Cancel Stripe subscription
            if immediate:
                self.stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = 'canceled'
                subscription.canceled_at = datetime.utcnow()
            else:
                self.stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
                subscription.canceled_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CANCELED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description=f"Subscription canceled {'immediately' if immediate else 'at period end'}",
                metadata={'immediate_cancel': immediate}
            )
            
            logger.info(f"Canceled subscription {subscription_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            raise PaymentProcessorError(f"Failed to cancel subscription: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error canceling subscription: {e}")
            self.db.rollback()
            raise PaymentProcessorError(f"Database error: {str(e)}")
    
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
                raise PaymentProcessorError("Customer not found")
            
            # Attach payment method to Stripe customer
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
            
            # Get payment method details from Stripe
            stripe_payment_method = self.stripe.PaymentMethod.retrieve(payment_method_id)
            
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
            
            # Log audit event
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_METHOD_ADDED,
                customer_id=customer_id,
                payment_method_id=payment_method.id,
                event_description=f"Payment method added: {payment_method.type} ending in {payment_method.last4}",
                metadata={
                    'stripe_payment_method_id': payment_method_id,
                    'is_default': set_as_default
                }
            )
            
            logger.info(f"Added payment method {payment_method.id} to customer {customer_id}")
            return payment_method
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error adding payment method: {e}")
            raise PaymentProcessorError(f"Failed to add payment method: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error adding payment method: {e}")
            self.db.rollback()
            raise PaymentProcessorError(f"Database error: {str(e)}")
    
    def process_refund(
        self, 
        invoice_id: int, 
        amount: float = None,
        reason: str = 'requested_by_customer'
    ) -> Dict[str, Any]:
        """Process a refund for an invoice"""
        try:
            invoice = self.db.query(BillingHistory).filter(
                BillingHistory.id == invoice_id
            ).first()
            
            if not invoice:
                raise PaymentProcessorError("Invoice not found")
            
            # Create Stripe refund
            refund_data = {
                'payment_intent': invoice.stripe_payment_intent_id,
                'reason': reason
            }
            
            if amount:
                refund_data['amount'] = int(amount * 100)  # Convert to cents
            
            stripe_refund = self.stripe.Refund.create(**refund_data)
            
            # Create local refund record
            from ..models.subscription import Refund, RefundStatus
            
            refund = Refund(
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                stripe_refund_id=stripe_refund.id,
                amount=stripe_refund.amount / 100,  # Convert from cents
                currency=stripe_refund.currency.upper(),
                reason=reason,
                status=stripe_refund.status,
                processing_fee=stripe_refund.processing_fee / 100 if stripe_refund.processing_fee else 0
            )
            
            self.db.add(refund)
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_REFUNDED,
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                event_description=f"Refund processed: ${refund.amount} for reason: {reason}",
                metadata={
                    'stripe_refund_id': stripe_refund.id,
                    'amount': refund.amount,
                    'reason': reason
                }
            )
            
            return {
                'refund_id': refund.id,
                'stripe_refund_id': stripe_refund.id,
                'amount': refund.amount,
                'status': refund.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing refund: {e}")
            raise PaymentProcessorError(f"Failed to process refund: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error processing refund: {e}")
            self.db.rollback()
            raise PaymentProcessorError(f"Database error: {str(e)}")
    
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
        feature_usage_id: int = None,
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
                feature_usage_id=feature_usage_id,
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