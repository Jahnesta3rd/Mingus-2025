"""
Payment Service Factory for MINGUS
Initializes and provides access to all payment processing services
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from .payment_processor import PaymentProcessor
from .subscription_manager import SubscriptionManager
from .stripe_webhook_handler import StripeWebhookHandler
from .billing_service import BillingService

logger = logging.getLogger(__name__)

class PaymentServiceFactory:
    """Factory for creating and managing payment processing services"""
    
    def __init__(self, db_session: Session, config):
        self.db_session = db_session
        self.config = config
        
        # Initialize services
        self._payment_processor = None
        self._subscription_manager = None
        self._webhook_handler = None
        self._billing_service = None
    
    @property
    def payment_processor(self) -> PaymentProcessor:
        """Get the payment processor service"""
        if self._payment_processor is None:
            self._payment_processor = PaymentProcessor(self.db_session, self.config)
            logger.info("Payment processor service initialized")
        return self._payment_processor
    
    @property
    def subscription_manager(self) -> SubscriptionManager:
        """Get the subscription manager service"""
        if self._subscription_manager is None:
            self._subscription_manager = SubscriptionManager(
                self.db_session, 
                self.payment_processor
            )
            logger.info("Subscription manager service initialized")
        return self._subscription_manager
    
    @property
    def webhook_handler(self) -> StripeWebhookHandler:
        """Get the Stripe webhook handler service"""
        if self._webhook_handler is None:
            self._webhook_handler = StripeWebhookHandler(
                self.db_session, 
                self.payment_processor
            )
            logger.info("Stripe webhook handler service initialized")
        return self._webhook_handler
    
    @property
    def billing_service(self) -> BillingService:
        """Get the billing service"""
        if self._billing_service is None:
            self._billing_service = BillingService(
                self.db_session,
                self.payment_processor,
                self.subscription_manager
            )
            logger.info("Billing service initialized")
        return self._billing_service
    
    def get_all_services(self) -> dict:
        """Get all payment services"""
        return {
            'payment_processor': self.payment_processor,
            'subscription_manager': self.subscription_manager,
            'webhook_handler': self.webhook_handler,
            'billing_service': self.billing_service
        }
    
    def reset_services(self):
        """Reset all services (useful for testing)"""
        self._payment_processor = None
        self._subscription_manager = None
        self._webhook_handler = None
        self._billing_service = None
        logger.info("All payment services reset")


class PaymentServiceManager:
    """High-level manager for payment operations"""
    
    def __init__(self, service_factory: PaymentServiceFactory):
        self.factory = service_factory
    
    def create_customer_and_subscription(
        self, 
        user_id: int, 
        email: str, 
        name: str,
        pricing_tier_id: int,
        billing_cycle: str = 'monthly',
        trial_days: int = 0
    ) -> dict:
        """Create a customer and subscription in one operation"""
        try:
            # Create customer
            customer = self.factory.payment_processor.create_customer(
                user_id=user_id,
                email=email,
                name=name
            )
            
            # Create subscription
            subscription = self.factory.payment_processor.create_subscription(
                customer_id=customer.id,
                pricing_tier_id=pricing_tier_id,
                billing_cycle=billing_cycle,
                trial_days=trial_days
            )
            
            return {
                'success': True,
                'customer_id': customer.id,
                'subscription_id': subscription.id,
                'stripe_customer_id': customer.stripe_customer_id,
                'stripe_subscription_id': subscription.stripe_subscription_id
            }
            
        except Exception as e:
            logger.error(f"Error creating customer and subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_feature_usage(
        self, 
        customer_id: int, 
        feature_name: str,
        quantity: int = 1
    ) -> dict:
        """Process feature usage and check limits"""
        try:
            success, result = self.factory.subscription_manager.use_feature(
                customer_id=customer_id,
                feature_name=feature_name,
                quantity=quantity
            )
            
            return {
                'success': success,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error processing feature usage: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upgrade_subscription(
        self, 
        customer_id: int, 
        new_tier_id: int,
        billing_cycle: str = None
    ) -> dict:
        """Upgrade a customer's subscription"""
        try:
            result = self.factory.subscription_manager.upgrade_subscription(
                customer_id=customer_id,
                new_tier_id=new_tier_id,
                billing_cycle=billing_cycle
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_subscription(
        self, 
        customer_id: int, 
        immediate: bool = False
    ) -> dict:
        """Cancel a customer's subscription"""
        try:
            subscription = self.factory.subscription_manager.get_active_subscription(customer_id)
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'No active subscription found'
                }
            
            result = self.factory.payment_processor.cancel_subscription(
                subscription_id=subscription.id,
                immediate=immediate
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'status': result.status
            }
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_customer_billing_summary(self, customer_id: int) -> dict:
        """Get comprehensive billing summary for a customer"""
        try:
            # Get usage summary
            usage_summary = self.factory.subscription_manager.get_usage_summary(customer_id)
            
            # Get billing summary
            billing_summary = self.factory.billing_service.get_billing_summary(customer_id)
            
            # Combine summaries
            combined_summary = {
                'customer_id': customer_id,
                'usage': usage_summary,
                'billing': billing_summary
            }
            
            return {
                'success': True,
                'summary': combined_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting customer billing summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_webhook_event(
        self, 
        payload: bytes, 
        sig_header: str, 
        webhook_secret: str
    ) -> dict:
        """Process a Stripe webhook event"""
        try:
            result = self.factory.webhook_handler.process_webhook(
                payload=payload,
                sig_header=sig_header,
                webhook_secret=webhook_secret
            )
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_recurring_billing(self) -> dict:
        """Run recurring billing for all active subscriptions"""
        try:
            result = self.factory.billing_service.process_recurring_billing()
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error running recurring billing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def apply_customer_credit(
        self, 
        customer_id: int, 
        amount: float, 
        reason: str = "Credit applied"
    ) -> dict:
        """Apply credit to a customer account"""
        try:
            result = self.factory.billing_service.apply_credit(
                customer_id=customer_id,
                amount=amount,
                reason=reason
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying customer credit: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_custom_invoice(
        self, 
        customer_id: int, 
        custom_amount: float = None
    ) -> dict:
        """Generate a custom invoice for a customer"""
        try:
            subscription = self.factory.subscription_manager.get_active_subscription(customer_id)
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'No active subscription found'
                }
            
            result = self.factory.billing_service.generate_invoice(
                subscription_id=subscription.id,
                custom_amount=custom_amount
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating custom invoice: {e}")
            return {
                'success': False,
                'error': str(e)
            } 