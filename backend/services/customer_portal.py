"""
Customer Portal Service for MINGUS
Handles customer portal integration, payment history, subscription self-service, and billing disputes
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, desc
import stripe
import json

from ..models.subscription import (
    Customer, Subscription, PaymentMethod, BillingHistory,
    AuditLog, AuditEventType, AuditSeverity
)
from ..config.base import Config

logger = logging.getLogger(__name__)

class CustomerPortalError(Exception):
    """Custom exception for customer portal errors"""
    pass

class CustomerPortal:
    """Comprehensive customer portal management for MINGUS"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.stripe = stripe
        self.stripe.api_key = config.STRIPE_SECRET_KEY
        
        # Portal configuration
        self.portal_configuration = {
            'business_profile': {
                'headline': 'MINGUS Financial Management',
                'privacy_policy_url': 'https://mingus.com/privacy',
                'terms_of_service_url': 'https://mingus.com/terms',
                'support_url': 'https://mingus.com/support'
            },
            'features': {
                'customer_update': {
                    'enabled': True,
                    'allowed_updates': ['address', 'shipping', 'phone', 'tax_id']
                },
                'invoice_history': {
                    'enabled': True
                },
                'payment_method_update': {
                    'enabled': True
                },
                'subscription_cancel': {
                    'enabled': True,
                    'proration_behavior': 'create_prorations',
                    'cancellation_reason': {
                        'enabled': True,
                        'options': [
                            'too_expensive',
                            'missing_features',
                            'switched_service',
                            'unused',
                            'customer_service',
                            'too_complex',
                            'low_quality',
                            'other'
                        ]
                    }
                },
                'subscription_pause': {
                    'enabled': True
                },
                'subscription_update': {
                    'enabled': True,
                    'proration_behavior': 'create_prorations',
                    'default_allowed_updates': ['price', 'quantity']
                },
                'tax_id_collection': {
                    'enabled': True
                }
            }
        }
    
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
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                raise CustomerPortalError("Customer not found")
            
            # Use custom configuration or default
            portal_config = configuration or self.portal_configuration
            
            # Create portal session
            session = self.stripe.billing_portal.Session.create(
                customer=customer.stripe_customer_id,
                return_url=return_url or f"{self.config.FRONTEND_URL}/dashboard",
                configuration=portal_config
            )
            
            # Log portal session creation
            self._log_portal_event(
                event_type=AuditEventType.CUSTOMER_PORTAL_ACCESSED,
                customer_id=customer_id,
                event_description="Customer portal session created",
                metadata={
                    'session_id': session.id,
                    'return_url': return_url,
                    'configuration': portal_config
                }
            )
            
            return {
                'success': True,
                'session_id': session.id,
                'url': session.url,
                'expires_at': datetime.fromtimestamp(session.expires_at).isoformat()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            raise CustomerPortalError(f"Failed to create portal session: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating portal session: {e}")
            raise CustomerPortalError(f"Portal session error: {str(e)}")
    
    def get_customer_portal_configuration(self) -> Dict[str, Any]:
        """Get customer portal configuration"""
        return {
            'success': True,
            'configuration': self.portal_configuration
        }
    
    def update_customer_portal_configuration(
        self,
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update customer portal configuration"""
        try:
            # Validate configuration
            self._validate_portal_configuration(configuration)
            
            # Update configuration
            self.portal_configuration.update(configuration)
            
            # Log configuration update
            self._log_portal_event(
                event_type=AuditEventType.PORTAL_CONFIGURATION_UPDATED,
                event_description="Customer portal configuration updated",
                metadata={'configuration': configuration}
            )
            
            return {
                'success': True,
                'configuration': self.portal_configuration
            }
            
        except Exception as e:
            logger.error(f"Error updating portal configuration: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # PAYMENT HISTORY ACCESS
    # ============================================================================
    
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
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Build query
            query = self.db.query(BillingHistory).filter(
                BillingHistory.customer_id == customer_id
            )
            
            # Apply filters
            if status:
                query = query.filter(BillingHistory.status == status)
            
            if start_date:
                query = query.filter(BillingHistory.invoice_date >= start_date)
            
            if end_date:
                query = query.filter(BillingHistory.invoice_date <= end_date)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            payments = query.order_by(desc(BillingHistory.invoice_date)).offset(offset).limit(limit).all()
            
            # Format payment history
            payment_history = []
            for payment in payments:
                payment_data = {
                    'id': payment.id,
                    'invoice_number': payment.invoice_number,
                    'stripe_invoice_id': payment.stripe_invoice_id,
                    'amount_due': payment.amount_due,
                    'amount_paid': payment.amount_paid,
                    'currency': payment.currency,
                    'status': payment.status,
                    'paid': payment.paid,
                    'invoice_date': payment.invoice_date.isoformat() if payment.invoice_date else None,
                    'due_date': payment.due_date.isoformat() if payment.due_date else None,
                    'paid_date': payment.paid_date.isoformat() if payment.paid_date else None,
                    'invoice_type': payment.invoice_type,
                    'description': payment.description,
                    'subscription_id': payment.subscription_id
                }
                
                # Add subscription details if available
                if payment.subscription:
                    payment_data['subscription'] = {
                        'id': payment.subscription.id,
                        'tier_name': payment.subscription.pricing_tier.name,
                        'tier_type': payment.subscription.pricing_tier.tier_type.value,
                        'billing_cycle': payment.subscription.billing_cycle
                    }
                
                payment_history.append(payment_data)
            
            return {
                'success': True,
                'customer_id': customer_id,
                'payments': payment_history,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + limit) < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payment history: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_details(
        self,
        customer_id: int,
        invoice_id: int
    ) -> Dict[str, Any]:
        """Get detailed payment information"""
        try:
            payment = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.id == invoice_id,
                    BillingHistory.customer_id == customer_id
                )
            ).first()
            
            if not payment:
                return {
                    'success': False,
                    'error': 'Payment not found or access denied'
                }
            
            # Get Stripe invoice details if available
            stripe_invoice = None
            if payment.stripe_invoice_id:
                try:
                    stripe_invoice = self.stripe.Invoice.retrieve(payment.stripe_invoice_id)
                except stripe.error.StripeError:
                    logger.warning(f"Could not retrieve Stripe invoice: {payment.stripe_invoice_id}")
            
            payment_details = {
                'id': payment.id,
                'invoice_number': payment.invoice_number,
                'stripe_invoice_id': payment.stripe_invoice_id,
                'amount_due': payment.amount_due,
                'amount_paid': payment.amount_paid,
                'currency': payment.currency,
                'status': payment.status,
                'paid': payment.paid,
                'invoice_date': payment.invoice_date.isoformat() if payment.invoice_date else None,
                'due_date': payment.due_date.isoformat() if payment.due_date else None,
                'paid_date': payment.paid_date.isoformat() if payment.paid_date else None,
                'invoice_type': payment.invoice_type,
                'description': payment.description,
                'metadata': payment.metadata,
                'subscription_id': payment.subscription_id,
                'stripe_invoice': stripe_invoice
            }
            
            # Add subscription details
            if payment.subscription:
                payment_details['subscription'] = {
                    'id': payment.subscription.id,
                    'tier_name': payment.subscription.pricing_tier.name,
                    'tier_type': payment.subscription.pricing_tier.tier_type.value,
                    'billing_cycle': payment.subscription.billing_cycle,
                    'amount': payment.subscription.amount,
                    'current_period_start': payment.subscription.current_period_start.isoformat(),
                    'current_period_end': payment.subscription.current_period_end.isoformat()
                }
            
            return {
                'success': True,
                'payment': payment_details
            }
            
        except Exception as e:
            logger.error(f"Error getting payment details: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_invoice_pdf(
        self,
        customer_id: int,
        invoice_id: int
    ) -> Dict[str, Any]:
        """Download invoice PDF"""
        try:
            payment = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.id == invoice_id,
                    BillingHistory.customer_id == customer_id
                )
            ).first()
            
            if not payment:
                return {
                    'success': False,
                    'error': 'Invoice not found or access denied'
                }
            
            if not payment.stripe_invoice_id:
                return {
                    'success': False,
                    'error': 'No Stripe invoice ID available'
                }
            
            # Get PDF from Stripe
            try:
                pdf_data = self.stripe.Invoice.retrieve_pdf(payment.stripe_invoice_id)
                
                # Log download
                self._log_portal_event(
                    event_type=AuditEventType.INVOICE_DOWNLOADED,
                    customer_id=customer_id,
                    invoice_id=invoice_id,
                    event_description=f"Invoice PDF downloaded: {payment.invoice_number}"
                )
                
                return {
                    'success': True,
                    'pdf_data': pdf_data,
                    'filename': f"invoice_{payment.invoice_number}.pdf",
                    'content_type': 'application/pdf'
                }
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error downloading invoice PDF: {e}")
                return {
                    'success': False,
                    'error': f"Failed to download PDF: {str(e)}"
                }
            
        except Exception as e:
            logger.error(f"Error downloading invoice PDF: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # SUBSCRIPTION MODIFICATION SELF-SERVICE
    # ============================================================================
    
    def get_subscription_modification_options(
        self,
        customer_id: int
    ) -> Dict[str, Any]:
        """Get available subscription modification options"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get active subscription
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status.in_(['active', 'trialing'])
                )
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'No active subscription found'
                }
            
            # Get available pricing tiers
            available_tiers = self.db.query(PricingTier).all()
            
            # Determine upgrade/downgrade options
            current_tier = subscription.pricing_tier
            upgrade_options = []
            downgrade_options = []
            
            for tier in available_tiers:
                if tier.id != current_tier.id:
                    if tier.monthly_price > current_tier.monthly_price:
                        upgrade_options.append({
                            'id': tier.id,
                            'name': tier.name,
                            'description': tier.description,
                            'monthly_price': tier.monthly_price,
                            'yearly_price': tier.yearly_price,
                            'tier_type': tier.tier_type.value,
                            'feature_limits': {
                                'health_checkins': tier.max_health_checkins_per_month,
                                'financial_reports': tier.max_financial_reports_per_month,
                                'ai_insights': tier.max_ai_insights_per_month
                            }
                        })
                    else:
                        downgrade_options.append({
                            'id': tier.id,
                            'name': tier.name,
                            'description': tier.description,
                            'monthly_price': tier.monthly_price,
                            'yearly_price': tier.yearly_price,
                            'tier_type': tier.tier_type.value,
                            'feature_limits': {
                                'health_checkins': tier.max_health_checkins_per_month,
                                'financial_reports': tier.max_financial_reports_per_month,
                                'ai_insights': tier.max_ai_insights_per_month
                            }
                        })
            
            # Get billing cycle options
            billing_cycle_options = []
            if subscription.billing_cycle == 'monthly':
                billing_cycle_options.append({
                    'cycle': 'yearly',
                    'description': 'Switch to annual billing (save 17%)',
                    'current_price': subscription.amount,
                    'new_price': subscription.pricing_tier.yearly_price / 12,
                    'savings': subscription.amount - (subscription.pricing_tier.yearly_price / 12)
                })
            else:
                billing_cycle_options.append({
                    'cycle': 'monthly',
                    'description': 'Switch to monthly billing',
                    'current_price': subscription.amount,
                    'new_price': subscription.pricing_tier.monthly_price,
                    'savings': 0
                })
            
            return {
                'success': True,
                'current_subscription': {
                    'id': subscription.id,
                    'tier_name': current_tier.name,
                    'tier_type': current_tier.tier_type.value,
                    'billing_cycle': subscription.billing_cycle,
                    'amount': subscription.amount,
                    'current_period_end': subscription.current_period_end.isoformat(),
                    'cancel_at_period_end': subscription.cancel_at_period_end
                },
                'upgrade_options': upgrade_options,
                'downgrade_options': downgrade_options,
                'billing_cycle_options': billing_cycle_options,
                'modification_features': {
                    'upgrade_immediate': True,
                    'downgrade_end_of_period': True,
                    'billing_cycle_change': True,
                    'pause_subscription': True,
                    'cancel_subscription': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription modification options: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get active subscription
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status.in_(['active', 'trialing'])
                )
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'No active subscription found'
                }
            
            # Handle different modification types
            if modification_type == 'upgrade' and new_tier_id:
                return self._handle_subscription_upgrade(
                    subscription, new_tier_id, reason
                )
            elif modification_type == 'downgrade' and new_tier_id:
                return self._handle_subscription_downgrade(
                    subscription, new_tier_id, effective_date, reason
                )
            elif modification_type == 'billing_cycle' and new_billing_cycle:
                return self._handle_billing_cycle_change(
                    subscription, new_billing_cycle, reason
                )
            elif modification_type == 'pause':
                return self._handle_subscription_pause(subscription, reason)
            elif modification_type == 'cancel':
                return self._handle_subscription_cancellation(subscription, reason)
            else:
                return {
                    'success': False,
                    'error': 'Invalid modification type or missing parameters'
                }
            
        except Exception as e:
            logger.error(f"Error modifying subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_subscription_upgrade(
        self,
        subscription: Subscription,
        new_tier_id: int,
        reason: str = None
    ) -> Dict[str, Any]:
        """Handle subscription upgrade"""
        try:
            new_tier = self.db.query(PricingTier).filter(PricingTier.id == new_tier_id).first()
            if not new_tier:
                return {
                    'success': False,
                    'error': 'Invalid pricing tier'
                }
            
            # Validate upgrade
            if new_tier.monthly_price <= subscription.pricing_tier.monthly_price:
                return {
                    'success': False,
                    'error': 'Selected tier is not an upgrade'
                }
            
            # Process upgrade through Stripe
            try:
                stripe_subscription = self.stripe.Subscription.retrieve(
                    subscription.stripe_subscription_id
                )
                
                # Update subscription item
                subscription_item = stripe_subscription.items.data[0]
                self.stripe.SubscriptionItem.modify(
                    subscription_item.id,
                    price=new_tier.stripe_price_id
                )
                
                # Update local subscription
                subscription.pricing_tier_id = new_tier_id
                subscription.amount = new_tier.monthly_price if subscription.billing_cycle == 'monthly' else new_tier.yearly_price / 12
                
                self.db.commit()
                
                # Log modification
                self._log_portal_event(
                    event_type=AuditEventType.SUBSCRIPTION_UPGRADED,
                    customer_id=subscription.customer_id,
                    subscription_id=subscription.id,
                    event_description=f"Subscription upgraded to {new_tier.name}",
                    metadata={
                        'old_tier': subscription.pricing_tier.name,
                        'new_tier': new_tier.name,
                        'reason': reason
                    }
                )
                
                return {
                    'success': True,
                    'message': f'Successfully upgraded to {new_tier.name}',
                    'subscription_id': subscription.id,
                    'new_tier': new_tier.name,
                    'new_amount': subscription.amount
                }
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error during upgrade: {e}")
                return {
                    'success': False,
                    'error': f'Stripe error: {str(e)}'
                }
            
        except Exception as e:
            logger.error(f"Error handling subscription upgrade: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_subscription_downgrade(
        self,
        subscription: Subscription,
        new_tier_id: int,
        effective_date: str,
        reason: str = None
    ) -> Dict[str, Any]:
        """Handle subscription downgrade"""
        try:
            new_tier = self.db.query(PricingTier).filter(PricingTier.id == new_tier_id).first()
            if not new_tier:
                return {
                    'success': False,
                    'error': 'Invalid pricing tier'
                }
            
            # Validate downgrade
            if new_tier.monthly_price >= subscription.pricing_tier.monthly_price:
                return {
                    'success': False,
                    'error': 'Selected tier is not a downgrade'
                }
            
            # Set downgrade to take effect at period end
            subscription.cancel_at_period_end = True
            subscription.downgrade_to_tier_id = new_tier_id
            subscription.downgrade_reason = reason
            
            self.db.commit()
            
            # Log modification
            self._log_portal_event(
                event_type=AuditEventType.SUBSCRIPTION_DOWNGRADE_SCHEDULED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description=f"Subscription downgrade scheduled to {new_tier.name}",
                metadata={
                    'old_tier': subscription.pricing_tier.name,
                    'new_tier': new_tier.name,
                    'effective_date': subscription.current_period_end.isoformat(),
                    'reason': reason
                }
            )
            
            return {
                'success': True,
                'message': f'Downgrade to {new_tier.name} scheduled for end of current period',
                'subscription_id': subscription.id,
                'effective_date': subscription.current_period_end.isoformat(),
                'new_tier': new_tier.name
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription downgrade: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_billing_cycle_change(
        self,
        subscription: Subscription,
        new_billing_cycle: str,
        reason: str = None
    ) -> Dict[str, Any]:
        """Handle billing cycle change"""
        try:
            if new_billing_cycle not in ['monthly', 'annual']:
                return {
                    'success': False,
                    'error': 'Invalid billing cycle'
                }
            
            if new_billing_cycle == subscription.billing_cycle:
                return {
                    'success': False,
                    'error': 'Billing cycle is already set to requested value'
                }
            
            # Calculate new amount
            if new_billing_cycle == 'annual':
                new_amount = subscription.pricing_tier.yearly_price / 12
            else:
                new_amount = subscription.pricing_tier.monthly_price
            
            # Update subscription
            subscription.billing_cycle = new_billing_cycle
            subscription.amount = new_amount
            
            self.db.commit()
            
            # Log modification
            self._log_portal_event(
                event_type=AuditEventType.BILLING_CYCLE_CHANGED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description=f"Billing cycle changed to {new_billing_cycle}",
                metadata={
                    'old_cycle': subscription.billing_cycle,
                    'new_cycle': new_billing_cycle,
                    'new_amount': new_amount,
                    'reason': reason
                }
            )
            
            return {
                'success': True,
                'message': f'Billing cycle changed to {new_billing_cycle}',
                'subscription_id': subscription.id,
                'new_billing_cycle': new_billing_cycle,
                'new_amount': new_amount
            }
            
        except Exception as e:
            logger.error(f"Error handling billing cycle change: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_subscription_pause(
        self,
        subscription: Subscription,
        reason: str = None
    ) -> Dict[str, Any]:
        """Handle subscription pause"""
        try:
            # Pause subscription
            subscription.status = 'paused'
            subscription.paused_at = datetime.utcnow()
            subscription.pause_reason = reason
            
            self.db.commit()
            
            # Log modification
            self._log_portal_event(
                event_type=AuditEventType.SUBSCRIPTION_PAUSED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description="Subscription paused",
                metadata={'reason': reason}
            )
            
            return {
                'success': True,
                'message': 'Subscription paused successfully',
                'subscription_id': subscription.id,
                'paused_at': subscription.paused_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription pause: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_subscription_cancellation(
        self,
        subscription: Subscription,
        reason: str = None
    ) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        try:
            # Cancel subscription at period end
            subscription.cancel_at_period_end = True
            subscription.canceled_at = datetime.utcnow()
            subscription.cancellation_reason = reason
            
            self.db.commit()
            
            # Log modification
            self._log_portal_event(
                event_type=AuditEventType.SUBSCRIPTION_CANCELED,
                customer_id=subscription.customer_id,
                subscription_id=subscription.id,
                event_description="Subscription cancellation scheduled",
                metadata={
                    'reason': reason,
                    'effective_date': subscription.current_period_end.isoformat()
                }
            )
            
            return {
                'success': True,
                'message': 'Subscription cancellation scheduled for end of current period',
                'subscription_id': subscription.id,
                'effective_date': subscription.current_period_end.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # BILLING DISPUTE HANDLING
    # ============================================================================
    
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
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Verify invoice belongs to customer
            invoice = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.id == invoice_id,
                    BillingHistory.customer_id == customer_id
                )
            ).first()
            
            if not invoice:
                return {
                    'success': False,
                    'error': 'Invoice not found or access denied'
                }
            
            # Create dispute record
            dispute = BillingDispute(
                customer_id=customer_id,
                invoice_id=invoice_id,
                dispute_type=dispute_type,
                dispute_reason=dispute_reason,
                dispute_amount=dispute_amount or invoice.amount_due,
                original_amount=invoice.amount_due,
                status='pending',
                contact_preference=contact_preference,
                supporting_documents=supporting_documents or [],
                created_at=datetime.utcnow()
            )
            
            self.db.add(dispute)
            self.db.commit()
            
            # Log dispute creation
            self._log_portal_event(
                event_type=AuditEventType.BILLING_DISPUTE_CREATED,
                customer_id=customer_id,
                invoice_id=invoice_id,
                dispute_id=dispute.id,
                event_description=f"Billing dispute created: {dispute_type}",
                metadata={
                    'dispute_type': dispute_type,
                    'dispute_reason': dispute_reason,
                    'dispute_amount': dispute_amount,
                    'contact_preference': contact_preference
                }
            )
            
            # Send notification to support team
            self._notify_support_team(dispute)
            
            return {
                'success': True,
                'dispute_id': dispute.id,
                'dispute_number': f"DIS-{dispute.id:06d}",
                'status': dispute.status,
                'estimated_resolution_time': '3-5 business days',
                'message': 'Dispute submitted successfully. Our support team will review and respond within 3-5 business days.'
            }
            
        except Exception as e:
            logger.error(f"Error creating billing dispute: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_dispute_status(
        self,
        customer_id: int,
        dispute_id: int
    ) -> Dict[str, Any]:
        """Get dispute status and details"""
        try:
            dispute = self.db.query(BillingDispute).filter(
                and_(
                    BillingDispute.id == dispute_id,
                    BillingDispute.customer_id == customer_id
                )
            ).first()
            
            if not dispute:
                return {
                    'success': False,
                    'error': 'Dispute not found or access denied'
                }
            
            dispute_data = {
                'id': dispute.id,
                'dispute_number': f"DIS-{dispute.id:06d}",
                'invoice_id': dispute.invoice_id,
                'invoice_number': dispute.invoice.invoice_number if dispute.invoice else None,
                'dispute_type': dispute.dispute_type,
                'dispute_reason': dispute.dispute_reason,
                'dispute_amount': dispute.dispute_amount,
                'original_amount': dispute.original_amount,
                'status': dispute.status,
                'contact_preference': dispute.contact_preference,
                'supporting_documents': dispute.supporting_documents,
                'created_at': dispute.created_at.isoformat(),
                'updated_at': dispute.updated_at.isoformat() if dispute.updated_at else None,
                'resolved_at': dispute.resolved_at.isoformat() if dispute.resolved_at else None,
                'resolution_notes': dispute.resolution_notes,
                'resolution_amount': dispute.resolution_amount
            }
            
            return {
                'success': True,
                'dispute': dispute_data
            }
            
        except Exception as e:
            logger.error(f"Error getting dispute status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_customer_disputes(
        self,
        customer_id: int,
        status: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get all disputes for a customer"""
        try:
            query = self.db.query(BillingDispute).filter(
                BillingDispute.customer_id == customer_id
            )
            
            if status:
                query = query.filter(BillingDispute.status == status)
            
            total_count = query.count()
            disputes = query.order_by(desc(BillingDispute.created_at)).offset(offset).limit(limit).all()
            
            dispute_list = []
            for dispute in disputes:
                dispute_list.append({
                    'id': dispute.id,
                    'dispute_number': f"DIS-{dispute.id:06d}",
                    'invoice_number': dispute.invoice.invoice_number if dispute.invoice else None,
                    'dispute_type': dispute.dispute_type,
                    'dispute_amount': dispute.dispute_amount,
                    'status': dispute.status,
                    'created_at': dispute.created_at.isoformat(),
                    'resolved_at': dispute.resolved_at.isoformat() if dispute.resolved_at else None
                })
            
            return {
                'success': True,
                'disputes': dispute_list,
                'pagination': {
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + limit) < total_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting customer disputes: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_dispute_comment(
        self,
        customer_id: int,
        dispute_id: int,
        comment: str,
        is_customer_comment: bool = True
    ) -> Dict[str, Any]:
        """Add a comment to a dispute"""
        try:
            dispute = self.db.query(BillingDispute).filter(
                and_(
                    BillingDispute.id == dispute_id,
                    BillingDispute.customer_id == customer_id
                )
            ).first()
            
            if not dispute:
                return {
                    'success': False,
                    'error': 'Dispute not found or access denied'
                }
            
            # Create comment
            comment_record = DisputeComment(
                dispute_id=dispute_id,
                comment=comment,
                is_customer_comment=is_customer_comment,
                created_at=datetime.utcnow()
            )
            
            self.db.add(comment_record)
            self.db.commit()
            
            # Log comment
            self._log_portal_event(
                event_type=AuditEventType.DISPUTE_COMMENT_ADDED,
                customer_id=customer_id,
                dispute_id=dispute_id,
                event_description="Dispute comment added",
                metadata={
                    'is_customer_comment': is_customer_comment,
                    'comment_length': len(comment)
                }
            )
            
            return {
                'success': True,
                'comment_id': comment_record.id,
                'message': 'Comment added successfully'
            }
            
        except Exception as e:
            logger.error(f"Error adding dispute comment: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _validate_portal_configuration(self, configuration: Dict[str, Any]):
        """Validate portal configuration"""
        required_sections = ['business_profile', 'features']
        for section in required_sections:
            if section not in configuration:
                raise CustomerPortalError(f"Missing required section: {section}")
    
    def _log_portal_event(
        self,
        event_type: AuditEventType,
        customer_id: int = None,
        subscription_id: int = None,
        invoice_id: int = None,
        dispute_id: int = None,
        event_description: str = None,
        metadata: Dict = None
    ):
        """Log portal event for audit trail"""
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
            logger.error(f"Failed to log portal event: {e}")
    
    def _notify_support_team(self, dispute: 'BillingDispute'):
        """Notify support team of new dispute"""
        try:
            # This would integrate with your notification system
            # For now, just log the notification
            logger.info(f"Support team notification: New dispute DIS-{dispute.id:06d} from customer {dispute.customer_id}")
            
        except Exception as e:
            logger.error(f"Error notifying support team: {e}")

# Import these models at the top of the file
from ..models.subscription import BillingDispute, DisputeComment 