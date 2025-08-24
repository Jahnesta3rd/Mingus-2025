"""
Stripe Webhook Handler Service for MINGUS
Processes Stripe webhook events and updates local database
"""
import stripe
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.subscription import (
    Customer, Subscription, PaymentMethod, BillingHistory,
    AuditLog, AuditEventType, AuditSeverity
)
from .payment_processor import PaymentProcessor

logger = logging.getLogger(__name__)

class WebhookHandlerError(Exception):
    """Custom exception for webhook handling errors"""
    pass

class StripeWebhookHandler:
    """Handles Stripe webhook events"""
    
    def __init__(self, db_session: Session, payment_processor: PaymentProcessor):
        self.db = db_session
        self.payment_processor = payment_processor
        self.stripe = stripe
    
    def process_webhook(self, payload: bytes, sig_header: str, webhook_secret: str) -> Dict[str, Any]:
        """Process a Stripe webhook event"""
        try:
            # Verify webhook signature
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            logger.info(f"Processing webhook event: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'customer.created':
                return self._handle_customer_created(event['data']['object'])
            elif event['type'] == 'customer.updated':
                return self._handle_customer_updated(event['data']['object'])
            elif event['type'] == 'customer.deleted':
                return self._handle_customer_deleted(event['data']['object'])
            elif event['type'] == 'subscription.created':
                return self._handle_subscription_created(event['data']['object'])
            elif event['type'] == 'subscription.updated':
                return self._handle_subscription_updated(event['data']['object'])
            elif event['type'] == 'subscription.deleted':
                return self._handle_subscription_deleted(event['data']['object'])
            elif event['type'] == 'invoice.created':
                return self._handle_invoice_created(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                return self._handle_invoice_payment_succeeded(event['data']['object'])
            elif event['type'] == 'invoice.payment_failed':
                return self._handle_invoice_payment_failed(event['data']['object'])
            elif event['type'] == 'payment_method.attached':
                return self._handle_payment_method_attached(event['data']['object'])
            elif event['type'] == 'payment_method.detached':
                return self._handle_payment_method_detached(event['data']['object'])
            elif event['type'] == 'charge.refunded':
                return self._handle_charge_refunded(event['data']['object'])
            elif event['type'] == 'charge.dispute.created':
                return self._handle_charge_dispute_created(event['data']['object'])
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return {'status': 'ignored', 'event_type': event['type']}
                
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise WebhookHandlerError("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise WebhookHandlerError("Invalid signature")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise WebhookHandlerError(f"Webhook processing error: {str(e)}")
    
    def _handle_customer_created(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.created webhook"""
        try:
            # Check if customer already exists
            existing_customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_data['id']
            ).first()
            
            if existing_customer:
                logger.info(f"Customer {customer_data['id']} already exists")
                return {'status': 'exists', 'customer_id': existing_customer.id}
            
            # Get user ID from metadata
            user_id = customer_data.get('metadata', {}).get('mingus_user_id')
            if not user_id:
                logger.warning(f"No user ID in customer metadata: {customer_data['id']}")
                return {'status': 'no_user_id'}
            
            # Create customer record
            customer = Customer(
                user_id=int(user_id),
                stripe_customer_id=customer_data['id'],
                email=customer_data.get('email'),
                name=customer_data.get('name'),
                phone=customer_data.get('phone'),
                address=customer_data.get('address'),
                tax_exempt=customer_data.get('tax_exempt', 'none')
            )
            
            self.db.add(customer)
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CREATED,
                customer_id=customer.id,
                event_description=f"Customer created via webhook: {customer_data['email']}",
                metadata={'stripe_customer_id': customer_data['id']}
            )
            
            return {'status': 'created', 'customer_id': customer.id}
            
        except Exception as e:
            logger.error(f"Error handling customer.created: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_customer_updated(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.updated webhook"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_data['id']
            ).first()
            
            if not customer:
                logger.warning(f"Customer not found: {customer_data['id']}")
                return {'status': 'not_found'}
            
            # Update customer fields
            customer.email = customer_data.get('email', customer.email)
            customer.name = customer_data.get('name', customer.name)
            customer.phone = customer_data.get('phone', customer.phone)
            customer.address = customer_data.get('address', customer.address)
            customer.tax_exempt = customer_data.get('tax_exempt', customer.tax_exempt)
            
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                customer_id=customer.id,
                event_description=f"Customer updated via webhook: {customer_data['email']}",
                metadata={'stripe_customer_id': customer_data['id']}
            )
            
            return {'status': 'updated', 'customer_id': customer.id}
            
        except Exception as e:
            logger.error(f"Error handling customer.updated: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_customer_deleted(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.deleted webhook"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == customer_data['id']
            ).first()
            
            if not customer:
                logger.warning(f"Customer not found: {customer_data['id']}")
                return {'status': 'not_found'}
            
            # Mark customer as deleted (soft delete)
            customer.is_active = False
            
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CANCELED,
                customer_id=customer.id,
                event_description=f"Customer deleted via webhook: {customer_data['id']}",
                metadata={'stripe_customer_id': customer_data['id']}
            )
            
            return {'status': 'deleted', 'customer_id': customer.id}
            
        except Exception as e:
            logger.error(f"Error handling customer.deleted: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_subscription_created(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.created webhook"""
        try:
            # Check if subscription already exists
            existing_subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_data['id']
            ).first()
            
            if existing_subscription:
                logger.info(f"Subscription {subscription_data['id']} already exists")
                return {'status': 'exists', 'subscription_id': existing_subscription.id}
            
            # Get customer
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == subscription_data['customer']
            ).first()
            
            if not customer:
                logger.warning(f"Customer not found for subscription: {subscription_data['customer']}")
                return {'status': 'customer_not_found'}
            
            # Get pricing tier from metadata
            pricing_tier_id = subscription_data.get('metadata', {}).get('mingus_pricing_tier_id')
            if not pricing_tier_id:
                logger.warning(f"No pricing tier ID in subscription metadata: {subscription_data['id']}")
                return {'status': 'no_pricing_tier_id'}
            
            # Create subscription record
            subscription = Subscription(
                customer_id=customer.id,
                pricing_tier_id=int(pricing_tier_id),
                stripe_subscription_id=subscription_data['id'],
                status=subscription_data['status'],
                current_period_start=datetime.fromtimestamp(subscription_data['current_period_start']),
                current_period_end=datetime.fromtimestamp(subscription_data['current_period_end']),
                billing_cycle=subscription_data.get('metadata', {}).get('billing_cycle', 'monthly'),
                amount=subscription_data['items']['data'][0]['price']['unit_amount'] / 100,
                currency=subscription_data['currency'].upper()
            )
            
            if subscription_data.get('trial_start'):
                subscription.trial_start = datetime.fromtimestamp(subscription_data['trial_start'])
            if subscription_data.get('trial_end'):
                subscription.trial_end = datetime.fromtimestamp(subscription_data['trial_end'])
            
            self.db.add(subscription)
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CREATED,
                customer_id=customer.id,
                subscription_id=subscription.id,
                event_description=f"Subscription created via webhook: {subscription_data['id']}",
                metadata={'stripe_subscription_id': subscription_data['id']}
            )
            
            return {'status': 'created', 'subscription_id': subscription.id}
            
        except Exception as e:
            logger.error(f"Error handling subscription.created: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.updated webhook"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_data['id']
            ).first()
            
            if not subscription:
                logger.warning(f"Subscription not found: {subscription_data['id']}")
                return {'status': 'not_found'}
            
            # Store old values for audit
            old_values = {
                'status': subscription.status,
                'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
            
            # Update subscription fields
            subscription.status = subscription_data['status']
            subscription.current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
            subscription.cancel_at_period_end = subscription_data.get('cancel_at_period_end', False)
            
            if subscription_data.get('canceled_at'):
                subscription.canceled_at = datetime.fromtimestamp(subscription_data['canceled_at'])
            
            self.db.commit()
            
            # Log audit event
            new_values = {
                'status': subscription.status,
                'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
            
            changed_fields = [field for field in old_values if old_values[field] != new_values[field]]
            
            if changed_fields:
                self._log_audit_event(
                    event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                    customer_id=subscription.customer_id,
                    subscription_id=subscription.id,
                    event_description=f"Subscription updated via webhook: {', '.join(changed_fields)}",
                    old_values=old_values,
                    new_values=new_values,
                    changed_fields=changed_fields
                )
            
            return {'status': 'updated', 'subscription_id': subscription.id}
            
        except Exception as e:
            logger.error(f"Error handling subscription.updated: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.deleted webhook"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_data['id']
            ).first()
            
            if not subscription:
                logger.warning(f"Subscription not found: {subscription_data['id']}")
                return {'status': 'not_found'}
            
            # Update subscription status
            subscription.status = 'canceled'
            subscription.canceled_at = datetime.utcnow()
            
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.SUBSCRIPTION_CANCELED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description=f"Subscription canceled via webhook: {subscription_data['id']}",
                metadata={'stripe_subscription_id': subscription_data['id']}
            )
            
            return {'status': 'canceled', 'subscription_id': subscription.id}
            
        except Exception as e:
            logger.error(f"Error handling subscription.deleted: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_invoice_created(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.created webhook"""
        try:
            # Check if invoice already exists
            existing_invoice = self.db.query(BillingHistory).filter(
                BillingHistory.stripe_invoice_id == invoice_data['id']
            ).first()
            
            if existing_invoice:
                logger.info(f"Invoice {invoice_data['id']} already exists")
                return {'status': 'exists', 'invoice_id': existing_invoice.id}
            
            # Get customer
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == invoice_data['customer']
            ).first()
            
            if not customer:
                logger.warning(f"Customer not found for invoice: {invoice_data['customer']}")
                return {'status': 'customer_not_found'}
            
            # Create invoice record
            invoice = BillingHistory(
                customer_id=customer.id,
                stripe_invoice_id=invoice_data['id'],
                amount_due=invoice_data['amount_due'] / 100,
                amount_paid=invoice_data['amount_paid'] / 100,
                currency=invoice_data['currency'].upper(),
                status=invoice_data['status'],
                paid=invoice_data['paid'],
                invoice_date=datetime.fromtimestamp(invoice_data['created']),
                due_date=datetime.fromtimestamp(invoice_data['due_date']) if invoice_data.get('due_date') else None,
                description=invoice_data.get('description')
            )
            
            if invoice_data.get('subscription'):
                subscription = self.db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == invoice_data['subscription']
                ).first()
                if subscription:
                    invoice.subscription_id = subscription.id
            
            self.db.add(invoice)
            self.db.commit()
            
            return {'status': 'created', 'invoice_id': invoice.id}
            
        except Exception as e:
            logger.error(f"Error handling invoice.created: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_invoice_payment_succeeded(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_succeeded webhook"""
        try:
            # Process payment using payment processor
            result = self.payment_processor.process_payment(invoice_data['id'])
            
            return {'status': 'processed', 'result': result}
            
        except Exception as e:
            logger.error(f"Error handling invoice.payment_succeeded: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _handle_invoice_payment_failed(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_failed webhook"""
        try:
            # Process payment failure
            result = self.payment_processor.process_payment(invoice_data['id'])
            
            # Log payment failure event
            invoice = self.db.query(BillingHistory).filter(
                BillingHistory.stripe_invoice_id == invoice_data['id']
            ).first()
            
            if invoice:
                self._log_audit_event(
                    event_type=AuditEventType.PAYMENT_FAILED,
                    customer_id=invoice.customer_id,
                    invoice_id=invoice.id,
                    event_description=f"Payment failed for invoice: {invoice_data['id']}",
                    metadata={
                        'stripe_invoice_id': invoice_data['id'],
                        'attempt_count': invoice_data.get('attempt_count', 1)
                    }
                )
            
            return {'status': 'processed', 'result': result}
            
        except Exception as e:
            logger.error(f"Error handling invoice.payment_failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _handle_payment_method_attached(self, payment_method_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment_method.attached webhook"""
        try:
            # Check if payment method already exists
            existing_payment_method = self.db.query(PaymentMethod).filter(
                PaymentMethod.stripe_payment_method_id == payment_method_data['id']
            ).first()
            
            if existing_payment_method:
                logger.info(f"Payment method {payment_method_data['id']} already exists")
                return {'status': 'exists', 'payment_method_id': existing_payment_method.id}
            
            # Get customer
            customer = self.db.query(Customer).filter(
                Customer.stripe_customer_id == payment_method_data['customer']
            ).first()
            
            if not customer:
                logger.warning(f"Customer not found for payment method: {payment_method_data['customer']}")
                return {'status': 'customer_not_found'}
            
            # Create payment method record
            payment_method = PaymentMethod(
                customer_id=customer.id,
                stripe_payment_method_id=payment_method_data['id'],
                type=payment_method_data['type'],
                brand=payment_method_data.get('card', {}).get('brand'),
                last4=payment_method_data.get('card', {}).get('last4'),
                exp_month=payment_method_data.get('card', {}).get('exp_month'),
                exp_year=payment_method_data.get('card', {}).get('exp_year'),
                country=payment_method_data.get('card', {}).get('country'),
                fingerprint=payment_method_data.get('card', {}).get('fingerprint'),
                billing_details=payment_method_data.get('billing_details')
            )
            
            self.db.add(payment_method)
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_METHOD_ADDED,
                customer_id=customer.id,
                payment_method_id=payment_method.id,
                event_description=f"Payment method attached via webhook: {payment_method_data['id']}",
                metadata={'stripe_payment_method_id': payment_method_data['id']}
            )
            
            return {'status': 'created', 'payment_method_id': payment_method.id}
            
        except Exception as e:
            logger.error(f"Error handling payment_method.attached: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_payment_method_detached(self, payment_method_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment_method.detached webhook"""
        try:
            payment_method = self.db.query(PaymentMethod).filter(
                PaymentMethod.stripe_payment_method_id == payment_method_data['id']
            ).first()
            
            if not payment_method:
                logger.warning(f"Payment method not found: {payment_method_data['id']}")
                return {'status': 'not_found'}
            
            # Mark payment method as inactive
            payment_method.is_active = False
            
            self.db.commit()
            
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_METHOD_REMOVED,
                customer_id=payment_method.customer_id,
                payment_method_id=payment_method.id,
                event_description=f"Payment method detached via webhook: {payment_method_data['id']}",
                metadata={'stripe_payment_method_id': payment_method_data['id']}
            )
            
            return {'status': 'detached', 'payment_method_id': payment_method.id}
            
        except Exception as e:
            logger.error(f"Error handling payment_method.detached: {e}")
            self.db.rollback()
            return {'status': 'error', 'error': str(e)}
    
    def _handle_charge_refunded(self, charge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.refunded webhook"""
        try:
            # Find invoice for this charge
            invoice = self.db.query(BillingHistory).filter(
                BillingHistory.stripe_payment_intent_id == charge_data.get('payment_intent')
            ).first()
            
            if not invoice:
                logger.warning(f"Invoice not found for charge: {charge_data['id']}")
                return {'status': 'invoice_not_found'}
            
            # Process refund
            result = self.payment_processor.process_refund(
                invoice_id=invoice.id,
                amount=charge_data['amount_refunded'] / 100,
                reason='requested_by_customer'
            )
            
            return {'status': 'processed', 'result': result}
            
        except Exception as e:
            logger.error(f"Error handling charge.refunded: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _handle_charge_dispute_created(self, dispute_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.dispute.created webhook"""
        try:
            # Find invoice for this charge
            invoice = self.db.query(BillingHistory).filter(
                BillingHistory.stripe_payment_intent_id == dispute_data.get('payment_intent')
            ).first()
            
            if not invoice:
                logger.warning(f"Invoice not found for dispute: {dispute_data['id']}")
                return {'status': 'invoice_not_found'}
            
            # Log dispute event
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_DISPUTED,
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                event_description=f"Payment dispute created: {dispute_data['id']}",
                metadata={
                    'stripe_dispute_id': dispute_data['id'],
                    'reason': dispute_data.get('reason'),
                    'amount': dispute_data['amount'] / 100
                }
            )
            
            return {'status': 'logged', 'dispute_id': dispute_data['id']}
            
        except Exception as e:
            logger.error(f"Error handling charge.dispute.created: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _log_audit_event(
        self,
        event_type: AuditEventType,
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