"""
Billing Service for MINGUS
Handles recurring billing, usage-based billing, and billing notifications
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func

from ..models.subscription import (
    Subscription, BillingHistory, FeatureUsage, Customer,
    PricingTier, AuditLog, AuditEventType, AuditSeverity
)
from .payment_processor import PaymentProcessor
from .subscription_manager import SubscriptionManager

logger = logging.getLogger(__name__)

class BillingServiceError(Exception):
    """Custom exception for billing service errors"""
    pass

class BillingService:
    """Handles billing operations and calculations"""
    
    def __init__(self, db_session: Session, payment_processor: PaymentProcessor, subscription_manager: SubscriptionManager):
        self.db = db_session
        self.payment_processor = payment_processor
        self.subscription_manager = subscription_manager
    
    def process_recurring_billing(self) -> Dict[str, Any]:
        """Process recurring billing for all active subscriptions"""
        try:
            # Get subscriptions that need billing
            today = datetime.utcnow().date()
            subscriptions_to_bill = self.db.query(Subscription).filter(
                and_(
                    Subscription.status.in_(['active', 'trialing']),
                    func.date(Subscription.current_period_end) <= today
                )
            ).all()
            
            results = {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'errors': []
            }
            
            for subscription in subscriptions_to_bill:
                try:
                    result = self._process_subscription_billing(subscription)
                    results['processed'] += 1
                    
                    if result['success']:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append({
                            'subscription_id': subscription.id,
                            'error': result['error']
                        })
                        
                except Exception as e:
                    results['processed'] += 1
                    results['failed'] += 1
                    results['errors'].append({
                        'subscription_id': subscription.id,
                        'error': str(e)
                    })
                    logger.error(f"Error processing billing for subscription {subscription.id}: {e}")
            
            logger.info(f"Recurring billing completed: {results['successful']} successful, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in recurring billing: {e}")
            raise BillingServiceError(f"Recurring billing error: {str(e)}")
    
    def _process_subscription_billing(self, subscription: Subscription) -> Dict[str, Any]:
        """Process billing for a single subscription"""
        try:
            # Calculate billing amount
            billing_amount = self._calculate_billing_amount(subscription)
            
            # Create invoice
            invoice = BillingHistory(
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                stripe_invoice_id=f"inv_{subscription.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                amount_due=billing_amount,
                amount_paid=0,
                currency=subscription.currency,
                status='pending',
                paid=False,
                invoice_date=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=7),
                description=f"Recurring billing for {subscription.pricing_tier.name} subscription"
            )
            
            self.db.add(invoice)
            self.db.commit()
            
            # Process payment
            payment_result = self.payment_processor.process_payment(invoice.stripe_invoice_id)
            
            if payment_result['paid']:
                # Update subscription period
                self._update_subscription_period(subscription)
                
                # Reset usage for new period
                self.subscription_manager.reset_monthly_usage(subscription.id)
                
                return {
                    'success': True,
                    'invoice_id': invoice.id,
                    'amount': billing_amount,
                    'status': 'paid'
                }
            else:
                # Handle payment failure
                self._handle_payment_failure(subscription, invoice)
                
                return {
                    'success': False,
                    'invoice_id': invoice.id,
                    'amount': billing_amount,
                    'status': 'failed',
                    'error': 'Payment processing failed'
                }
                
        except Exception as e:
            logger.error(f"Error processing subscription billing: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_billing_amount(self, subscription: Subscription) -> float:
        """Calculate billing amount for a subscription"""
        try:
            base_amount = subscription.amount
            
            # Add usage-based charges
            usage_charges = self._calculate_usage_charges(subscription)
            
            # Add tax if applicable
            tax_amount = self._calculate_tax_amount(subscription, base_amount + usage_charges)
            
            total_amount = base_amount + usage_charges + tax_amount
            
            return round(total_amount, 2)
            
        except Exception as e:
            logger.error(f"Error calculating billing amount: {e}")
            return subscription.amount  # Fallback to base amount
    
    def _calculate_usage_charges(self, subscription: Subscription) -> float:
        """Calculate usage-based charges for a subscription"""
        try:
            usage = self.subscription_manager.get_subscription_usage(subscription.id)
            tier = subscription.pricing_tier
            
            total_charges = 0.0
            
            # Calculate overage charges for each feature
            features = [
                'health_checkins',
                'financial_reports', 
                'ai_insights',
                'api_calls'
            ]
            
            for feature in features:
                used = getattr(usage, f'{feature}_used', 0)
                limit = getattr(tier, f'max_{feature}_per_month', 0)
                
                if limit > 0 and used > limit:
                    overage = used - limit
                    # Calculate charge based on overage (example rates)
                    if feature == 'health_checkins':
                        charge = overage * 0.50  # $0.50 per additional check-in
                    elif feature == 'financial_reports':
                        charge = overage * 2.00  # $2.00 per additional report
                    elif feature == 'ai_insights':
                        charge = overage * 1.00  # $1.00 per additional insight
                    elif feature == 'api_calls':
                        charge = overage * 0.01  # $0.01 per additional API call
                    else:
                        charge = 0
                    
                    total_charges += charge
            
            return round(total_charges, 2)
            
        except Exception as e:
            logger.error(f"Error calculating usage charges: {e}")
            return 0.0
    
    def _calculate_tax_amount(self, subscription: Subscription, subtotal: float) -> float:
        """Calculate tax amount for a subscription"""
        try:
            # Get customer tax information
            customer = self.db.query(Customer).filter(Customer.id == subscription.customer_id).first()
            
            if not customer or customer.tax_exempt == 'exempt':
                return 0.0
            
            # Simple tax calculation (in production, use a tax service)
            tax_rate = subscription.tax_percent / 100.0
            tax_amount = subtotal * tax_rate
            
            return round(tax_amount, 2)
            
        except Exception as e:
            logger.error(f"Error calculating tax amount: {e}")
            return 0.0
    
    def _update_subscription_period(self, subscription: Subscription):
        """Update subscription billing period"""
        try:
            if subscription.billing_cycle == 'monthly':
                new_period_start = subscription.current_period_end
                new_period_end = new_period_start + timedelta(days=30)
            else:  # annual
                new_period_start = subscription.current_period_end
                new_period_end = new_period_start + timedelta(days=365)
            
            subscription.current_period_start = new_period_start
            subscription.current_period_end = new_period_end
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating subscription period: {e}")
            raise
    
    def _handle_payment_failure(self, subscription: Subscription, invoice: BillingHistory):
        """Handle payment failure for a subscription"""
        try:
            # Update subscription status
            subscription.status = 'past_due'
            
            # Update invoice status
            invoice.status = 'failed'
            invoice.paid = False
            
            self.db.commit()
            
            # Log payment failure
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_FAILED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                invoice_id=invoice.id,
                event_description=f"Payment failed for recurring billing: ${invoice.amount_due}",
                metadata={
                    'invoice_id': invoice.id,
                    'amount_due': invoice.amount_due,
                    'subscription_status': subscription.status
                }
            )
            
            # Send notification (implement notification service)
            self._send_payment_failure_notification(subscription, invoice)
            
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            raise
    
    def generate_invoice(self, subscription_id: int, custom_amount: float = None) -> Dict[str, Any]:
        """Generate a custom invoice for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
            
            if not subscription:
                raise BillingServiceError("Subscription not found")
            
            # Calculate amount
            if custom_amount:
                amount = custom_amount
            else:
                amount = self._calculate_billing_amount(subscription)
            
            # Create invoice
            invoice = BillingHistory(
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                stripe_invoice_id=f"inv_custom_{subscription.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                amount_due=amount,
                amount_paid=0,
                currency=subscription.currency,
                status='pending',
                paid=False,
                invoice_date=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=30),
                description="Custom invoice"
            )
            
            self.db.add(invoice)
            self.db.commit()
            
            return {
                'success': True,
                'invoice_id': invoice.id,
                'amount': amount,
                'due_date': invoice.due_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating invoice: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def apply_credit(self, customer_id: int, amount: float, reason: str = "Credit applied") -> Dict[str, Any]:
        """Apply credit to a customer account"""
        try:
            from ..models.subscription import Credit
            
            # Create credit record
            credit = Credit(
                customer_id=customer_id,
                amount=amount,
                currency='USD',
                credit_type='adjustment',
                description=reason,
                original_amount=amount,
                remaining_amount=amount,
                is_used=False
            )
            
            self.db.add(credit)
            self.db.commit()
            
            # Log credit application
            self._log_audit_event(
                event_type=AuditEventType.PAYMENT_SUCCEEDED,
                customer_id=customer_id,
                event_description=f"Credit applied: ${amount} - {reason}",
                metadata={
                    'credit_id': credit.id,
                    'amount': amount,
                    'reason': reason
                }
            )
            
            return {
                'success': True,
                'credit_id': credit.id,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Error applying credit: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_billing_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get billing summary for a customer"""
        try:
            # Get customer
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {'error': 'Customer not found'}
            
            # Get active subscription
            subscription = self.subscription_manager.get_active_subscription(customer_id)
            
            # Get recent invoices
            recent_invoices = self.db.query(BillingHistory).filter(
                BillingHistory.customer_id == customer_id
            ).order_by(BillingHistory.created_at.desc()).limit(10).all()
            
            # Get usage summary
            usage_summary = self.subscription_manager.get_usage_summary(customer_id)
            
            # Calculate outstanding balance
            outstanding_invoices = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.customer_id == customer_id,
                    BillingHistory.status.in_(['pending', 'past_due']),
                    BillingHistory.paid == False
                )
            ).all()
            
            outstanding_balance = sum(invoice.amount_due - invoice.amount_paid for invoice in outstanding_invoices)
            
            summary = {
                'customer_id': customer_id,
                'customer_email': customer.email,
                'has_active_subscription': subscription is not None,
                'subscription': {
                    'id': subscription.id if subscription else None,
                    'tier': subscription.pricing_tier.tier_type.value if subscription else None,
                    'status': subscription.status if subscription else None,
                    'billing_cycle': subscription.billing_cycle if subscription else None,
                    'next_billing_date': subscription.current_period_end.isoformat() if subscription else None
                },
                'usage': usage_summary.get('usage', {}),
                'outstanding_balance': round(outstanding_balance, 2),
                'recent_invoices': [
                    {
                        'id': invoice.id,
                        'amount': invoice.amount_due,
                        'status': invoice.status,
                        'paid': invoice.paid,
                        'invoice_date': invoice.invoice_date.isoformat(),
                        'due_date': invoice.due_date.isoformat() if invoice.due_date else None
                    }
                    for invoice in recent_invoices
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting billing summary: {e}")
            return {
                'error': str(e)
            }
    
    def _send_payment_failure_notification(self, subscription: Subscription, invoice: BillingHistory):
        """Send payment failure notification (placeholder for notification service)"""
        try:
            # This would integrate with your notification service
            logger.info(f"Payment failure notification sent for subscription {subscription.id}")
            
            # Example notification data
            notification_data = {
                'type': 'payment_failure',
                'customer_id': subscription.customer_id,
                'subscription_id': subscription.id,
                'invoice_id': invoice.id,
                'amount_due': invoice.amount_due,
                'due_date': invoice.due_date.isoformat() if invoice.due_date else None
            }
            
            # TODO: Send email/SMS notification
            # notification_service.send_notification(notification_data)
            
        except Exception as e:
            logger.error(f"Error sending payment failure notification: {e}")
    
    def _log_audit_event(
        self,
        event_type: AuditEventType,
        customer_id: int = None,
        subscription_id: int = None,
        invoice_id: int = None,
        event_description: str = None,
        metadata: Dict = None
    ):
        """Log an audit event"""
        try:
            audit_log = AuditLog(
                event_type=event_type,
                customer_id=customer_id,
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                event_description=event_description,
                metadata=metadata
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log audit event: {e}")
            # Don't raise exception for audit logging failures 