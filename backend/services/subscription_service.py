"""
MINGUS Application - Subscription Service
========================================

Comprehensive subscription service that integrates SQLAlchemy models
with Stripe for complete subscription management.

Author: MINGUS Development Team
Date: January 2025
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from uuid import UUID

from ..models.subscription_models import (
    MINGUSSubscription, MINGUSInvoice, MINGUSPaymentMethod, MINGUSUsageRecord,
    MINGUSSubscriptionTier, MINGUSBillingEvent, BillingCycle, SubscriptionStatus,
    PaymentStatus, UsageType
)
from ..payment.stripe_integration import StripeService, SubscriptionTier
from ..payment.payment_models import Customer, Subscription, Invoice, PaymentMethod


class SubscriptionService:
    """Comprehensive subscription service for MINGUS."""
    
    def __init__(self, db_session: Session, stripe_service: Optional[StripeService] = None):
        """
        Initialize subscription service.
        
        Args:
            db_session: Database session
            stripe_service: Stripe service instance
        """
        self.db = db_session
        self.stripe_service = stripe_service or StripeService()
        self.logger = logging.getLogger('mingus.subscription')
    
    # =====================================================
    # SUBSCRIPTION TIER MANAGEMENT
    # =====================================================
    
    def get_all_tiers(self) -> List[MINGUSSubscriptionTier]:
        """Get all active subscription tiers."""
        return self.db.query(MINGUSSubscriptionTier).filter(
            MINGUSSubscriptionTier.is_active == True
        ).order_by(MINGUSSubscriptionTier.sort_order).all()
    
    def get_tier_by_id(self, tier_id: UUID) -> Optional[MINGUSSubscriptionTier]:
        """Get subscription tier by ID."""
        return self.db.query(MINGUSSubscriptionTier).filter(
            MINGUSSubscriptionTier.id == tier_id
        ).first()
    
    def get_tier_by_stripe_price_id(self, stripe_price_id: str) -> Optional[MINGUSSubscriptionTier]:
        """Get subscription tier by Stripe price ID."""
        return self.db.query(MINGUSSubscriptionTier).filter(
            or_(
                MINGUSSubscriptionTier.stripe_monthly_price_id == stripe_price_id,
                MINGUSSubscriptionTier.stripe_yearly_price_id == stripe_price_id
            )
        ).first()
    
    def update_tier_stripe_prices(self, tier_id: UUID, monthly_price_id: str, yearly_price_id: str) -> bool:
        """Update Stripe price IDs for a tier."""
        try:
            tier = self.get_tier_by_id(tier_id)
            if not tier:
                return False
            
            tier.stripe_monthly_price_id = monthly_price_id
            tier.stripe_yearly_price_id = yearly_price_id
            tier.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.logger.info(f"Updated Stripe price IDs for tier {tier_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to update tier Stripe prices: {e}")
            return False
    
    # =====================================================
    # SUBSCRIPTION MANAGEMENT
    # =====================================================
    
    def create_subscription_from_stripe(
        self, 
        user_id: UUID, 
        stripe_subscription: Subscription,
        tier: SubscriptionTier,
        billing_cycle: BillingCycle
    ) -> Optional[MINGUSSubscription]:
        """
        Create MINGUS subscription from Stripe subscription.
        
        Args:
            user_id: User ID
            stripe_subscription: Stripe subscription object
            tier: Subscription tier
            billing_cycle: Billing cycle
            
        Returns:
            Created MINGUS subscription or None
        """
        try:
            # Get tier configuration
            tier_config = self.stripe_service.get_subscription_tier_info(tier)
            
            # Create subscription
            subscription = MINGUSSubscription(
                user_id=user_id,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=stripe_subscription.customer_id,
                stripe_price_id=stripe_subscription.price_id,
                tier=tier,
                billing_cycle=billing_cycle,
                status=SubscriptionStatus(stripe_subscription.status),
                amount=stripe_subscription.amount,
                currency=stripe_subscription.currency,
                current_period_start=stripe_subscription.current_period_start,
                current_period_end=stripe_subscription.current_period_end,
                trial_start=stripe_subscription.trial_start,
                trial_end=stripe_subscription.trial_end,
                usage_limits=tier_config.limits,
                current_usage={},
                metadata=stripe_subscription.metadata
            )
            
            self.db.add(subscription)
            self.db.commit()
            
            # Log billing event
            self._log_billing_event(
                event_type='subscription.created',
                subscription_id=subscription.id,
                user_id=user_id,
                event_data={
                    'stripe_subscription_id': stripe_subscription.id,
                    'tier': tier.value,
                    'billing_cycle': billing_cycle.value,
                    'amount': float(stripe_subscription.amount)
                }
            )
            
            self.logger.info(f"Created subscription {subscription.id} for user {user_id}")
            return subscription
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to create subscription: {e}")
            return None
    
    def get_user_subscriptions(self, user_id: UUID) -> List[MINGUSSubscription]:
        """Get all subscriptions for a user."""
        return self.db.query(MINGUSSubscription).filter(
            MINGUSSubscription.user_id == user_id
        ).order_by(desc(MINGUSSubscription.created_at)).all()
    
    def get_active_subscription(self, user_id: UUID) -> Optional[MINGUSSubscription]:
        """Get active subscription for a user."""
        return self.db.query(MINGUSSubscription).filter(
            and_(
                MINGUSSubscription.user_id == user_id,
                MINGUSSubscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIAL
                ])
            )
        ).first()
    
    def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[MINGUSSubscription]:
        """Get subscription by Stripe subscription ID."""
        return self.db.query(MINGUSSubscription).filter(
            MINGUSSubscription.stripe_subscription_id == stripe_subscription_id
        ).first()
    
    def update_subscription_from_stripe(self, stripe_subscription: Subscription) -> bool:
        """
        Update MINGUS subscription from Stripe subscription.
        
        Args:
            stripe_subscription: Stripe subscription object
            
        Returns:
            Success status
        """
        try:
            subscription = self.get_subscription_by_stripe_id(stripe_subscription.id)
            if not subscription:
                return False
            
            # Store previous state for audit
            previous_state = subscription.to_dict()
            
            # Update subscription
            subscription.status = SubscriptionStatus(stripe_subscription.status)
            subscription.amount = stripe_subscription.amount
            subscription.current_period_start = stripe_subscription.current_period_start
            subscription.current_period_end = stripe_subscription.current_period_end
            subscription.trial_start = stripe_subscription.trial_start
            subscription.trial_end = stripe_subscription.trial_end
            subscription.canceled_at = stripe_subscription.canceled_at
            subscription.ended_at = stripe_subscription.ended_at
            subscription.metadata = stripe_subscription.metadata
            subscription.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log billing event
            self._log_billing_event(
                event_type='subscription.updated',
                subscription_id=subscription.id,
                user_id=subscription.user_id,
                previous_state=previous_state,
                new_state=subscription.to_dict(),
                event_data={
                    'stripe_subscription_id': stripe_subscription.id,
                    'status': stripe_subscription.status
                }
            )
            
            self.logger.info(f"Updated subscription {subscription.id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to update subscription: {e}")
            return False
    
    def cancel_subscription(self, subscription_id: UUID, at_period_end: bool = True) -> bool:
        """
        Cancel subscription.
        
        Args:
            subscription_id: Subscription ID
            at_period_end: Cancel at period end
            
        Returns:
            Success status
        """
        try:
            subscription = self.db.query(MINGUSSubscription).filter(
                MINGUSSubscription.id == subscription_id
            ).first()
            
            if not subscription:
                return False
            
            # Cancel in Stripe
            stripe_subscription = self.stripe_service.cancel_subscription(
                subscription.stripe_subscription_id,
                at_period_end=at_period_end
            )
            
            # Update local subscription
            subscription.status = SubscriptionStatus(stripe_subscription.status)
            subscription.canceled_at = stripe_subscription.canceled_at
            subscription.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log billing event
            self._log_billing_event(
                event_type='subscription.canceled',
                subscription_id=subscription.id,
                user_id=subscription.user_id,
                event_data={
                    'at_period_end': at_period_end,
                    'canceled_at': stripe_subscription.canceled_at.isoformat() if stripe_subscription.canceled_at else None
                }
            )
            
            self.logger.info(f"Canceled subscription {subscription_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    # =====================================================
    # INVOICE MANAGEMENT
    # =====================================================
    
    def create_invoice_from_stripe(self, stripe_invoice: Invoice) -> Optional[MINGUSInvoice]:
        """
        Create MINGUS invoice from Stripe invoice.
        
        Args:
            stripe_invoice: Stripe invoice object
            
        Returns:
            Created MINGUS invoice or None
        """
        try:
            # Get subscription
            subscription = self.get_subscription_by_stripe_id(stripe_invoice.subscription_id)
            if not subscription:
                return None
            
            # Create invoice
            invoice = MINGUSInvoice(
                subscription_id=subscription.id,
                stripe_invoice_id=stripe_invoice.id,
                stripe_payment_intent_id=stripe_invoice.payment_intent_id,
                invoice_number=stripe_invoice.number,
                status=PaymentStatus(stripe_invoice.status),
                subtotal=stripe_invoice.subtotal,
                tax=stripe_invoice.tax,
                discount=stripe_invoice.discount,
                total=stripe_invoice.total,
                amount_paid=stripe_invoice.amount_paid,
                amount_remaining=stripe_invoice.amount_remaining,
                currency=stripe_invoice.currency,
                due_date=stripe_invoice.due_date,
                paid_at=stripe_invoice.paid_at,
                items=stripe_invoice.items,
                metadata=stripe_invoice.metadata
            )
            
            self.db.add(invoice)
            self.db.commit()
            
            # Log billing event
            self._log_billing_event(
                event_type='invoice.created',
                subscription_id=subscription.id,
                invoice_id=invoice.id,
                user_id=subscription.user_id,
                event_data={
                    'stripe_invoice_id': stripe_invoice.id,
                    'amount': float(stripe_invoice.total),
                    'status': stripe_invoice.status
                }
            )
            
            self.logger.info(f"Created invoice {invoice.id} for subscription {subscription.id}")
            return invoice
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to create invoice: {e}")
            return None
    
    def update_invoice_from_stripe(self, stripe_invoice: Invoice) -> bool:
        """
        Update MINGUS invoice from Stripe invoice.
        
        Args:
            stripe_invoice: Stripe invoice object
            
        Returns:
            Success status
        """
        try:
            invoice = self.db.query(MINGUSInvoice).filter(
                MINGUSInvoice.stripe_invoice_id == stripe_invoice.id
            ).first()
            
            if not invoice:
                return False
            
            # Store previous state
            previous_state = invoice.to_dict()
            
            # Update invoice
            invoice.status = PaymentStatus(stripe_invoice.status)
            invoice.amount_paid = stripe_invoice.amount_paid
            invoice.amount_remaining = stripe_invoice.amount_remaining
            invoice.paid_at = stripe_invoice.paid_at
            invoice.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Log billing event
            self._log_billing_event(
                event_type='invoice.updated',
                subscription_id=invoice.subscription_id,
                invoice_id=invoice.id,
                user_id=invoice.subscription.user_id,
                previous_state=previous_state,
                new_state=invoice.to_dict(),
                event_data={
                    'stripe_invoice_id': stripe_invoice.id,
                    'status': stripe_invoice.status
                }
            )
            
            self.logger.info(f"Updated invoice {invoice.id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to update invoice: {e}")
            return False
    
    def get_subscription_invoices(self, subscription_id: UUID, limit: int = 10) -> List[MINGUSInvoice]:
        """Get invoices for a subscription."""
        return self.db.query(MINGUSInvoice).filter(
            MINGUSInvoice.subscription_id == subscription_id
        ).order_by(desc(MINGUSInvoice.created_at)).limit(limit).all()
    
    # =====================================================
    # PAYMENT METHOD MANAGEMENT
    # =====================================================
    
    def create_payment_method_from_stripe(
        self, 
        subscription_id: UUID, 
        stripe_payment_method: PaymentMethod
    ) -> Optional[MINGUSPaymentMethod]:
        """
        Create MINGUS payment method from Stripe payment method.
        
        Args:
            subscription_id: Subscription ID
            stripe_payment_method: Stripe payment method object
            
        Returns:
            Created MINGUS payment method or None
        """
        try:
            # Create payment method
            payment_method = MINGUSPaymentMethod(
                subscription_id=subscription_id,
                stripe_payment_method_id=stripe_payment_method.id,
                type=stripe_payment_method.type,
                brand=stripe_payment_method.brand,
                last4=stripe_payment_method.last4,
                exp_month=stripe_payment_method.exp_month,
                exp_year=stripe_payment_method.exp_year,
                country=stripe_payment_method.country,
                billing_details=stripe_payment_method.billing_details,
                is_default=stripe_payment_method.is_default,
                is_active=stripe_payment_method.is_active,
                metadata=stripe_payment_method.metadata
            )
            
            self.db.add(payment_method)
            self.db.commit()
            
            self.logger.info(f"Created payment method {payment_method.id}")
            return payment_method
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to create payment method: {e}")
            return None
    
    def get_subscription_payment_methods(self, subscription_id: UUID) -> List[MINGUSPaymentMethod]:
        """Get payment methods for a subscription."""
        return self.db.query(MINGUSPaymentMethod).filter(
            and_(
                MINGUSPaymentMethod.subscription_id == subscription_id,
                MINGUSPaymentMethod.is_active == True
            )
        ).order_by(desc(MINGUSPaymentMethod.is_default), desc(MINGUSPaymentMethod.created_at)).all()
    
    # =====================================================
    # USAGE TRACKING
    # =====================================================
    
    def track_usage(
        self, 
        subscription_id: UUID, 
        usage_type: UsageType, 
        quantity: int = 1,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track usage for a subscription feature.
        
        Args:
            subscription_id: Subscription ID
            usage_type: Type of usage
            quantity: Usage quantity
            description: Usage description
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            # Get subscription
            subscription = self.db.query(MINGUSSubscription).filter(
                MINGUSSubscription.id == subscription_id
            ).first()
            
            if not subscription:
                return False
            
            # Check if usage is allowed
            if not subscription.can_use_feature(usage_type, quantity):
                self.logger.warning(f"Usage limit exceeded for {usage_type.value} on subscription {subscription_id}")
                return False
            
            # Create usage record
            usage_record = MINGUSUsageRecord(
                subscription_id=subscription_id,
                usage_type=usage_type,
                quantity=quantity,
                description=description,
                metadata=metadata
            )
            
            self.db.add(usage_record)
            
            # Update current usage
            current_usage = subscription.current_usage.copy()
            current_usage[usage_type.value] = current_usage.get(usage_type.value, 0) + quantity
            subscription.current_usage = current_usage
            subscription.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            self.logger.info(f"Tracked usage {usage_type.value} for subscription {subscription_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to track usage: {e}")
            return False
    
    def get_usage_summary(self, subscription_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Get usage summary for a subscription.
        
        Args:
            subscription_id: Subscription ID
            days: Number of days to look back
            
        Returns:
            Usage summary
        """
        try:
            subscription = self.db.query(MINGUSSubscription).filter(
                MINGUSSubscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {}
            
            # Get usage records for the period
            since_date = datetime.utcnow() - timedelta(days=days)
            usage_records = self.db.query(MINGUSUsageRecord).filter(
                and_(
                    MINGUSUsageRecord.subscription_id == subscription_id,
                    MINGUSUsageRecord.usage_date >= since_date
                )
            ).all()
            
            # Calculate usage by type
            usage_by_type = {}
            for record in usage_records:
                usage_type = record.usage_type.value
                if usage_type not in usage_by_type:
                    usage_by_type[usage_type] = {
                        'total_quantity': 0,
                        'total_records': 0,
                        'last_used': None
                    }
                
                usage_by_type[usage_type]['total_quantity'] += record.quantity
                usage_by_type[usage_type]['total_records'] += 1
                
                if not usage_by_type[usage_type]['last_used'] or record.usage_date > usage_by_type[usage_type]['last_used']:
                    usage_by_type[usage_type]['last_used'] = record.usage_date
            
            # Add limits and percentages
            for usage_type, data in usage_by_type.items():
                limit = subscription.usage_limits.get(usage_type, 0)
                current = subscription.current_usage.get(usage_type, 0)
                
                data['limit'] = limit
                data['current'] = current
                data['percentage'] = subscription.get_usage_percentage(UsageType(usage_type))
                data['can_use'] = subscription.can_use_feature(UsageType(usage_type))
            
            return {
                'subscription_id': str(subscription_id),
                'period_days': days,
                'usage_by_type': usage_by_type,
                'total_usage_records': len(usage_records)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get usage summary: {e}")
            return {}
    
    # =====================================================
    # BILLING EVENTS
    # =====================================================
    
    def _log_billing_event(
        self,
        event_type: str,
        subscription_id: Optional[UUID] = None,
        invoice_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        event_data: Optional[Dict[str, Any]] = None,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        stripe_event_id: Optional[str] = None
    ) -> None:
        """Log a billing event."""
        try:
            event = MINGUSBillingEvent(
                subscription_id=subscription_id,
                invoice_id=invoice_id,
                event_type=event_type,
                event_source='stripe',
                event_data=event_data or {},
                previous_state=previous_state,
                new_state=new_state,
                user_id=user_id,
                stripe_event_id=stripe_event_id
            )
            
            self.db.add(event)
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log billing event: {e}")
            self.db.rollback()
    
    def get_billing_events(
        self,
        user_id: Optional[UUID] = None,
        subscription_id: Optional[UUID] = None,
        event_type: Optional[str] = None,
        limit: int = 50
    ) -> List[MINGUSBillingEvent]:
        """Get billing events with optional filters."""
        query = self.db.query(MINGUSBillingEvent)
        
        if user_id:
            query = query.filter(MINGUSBillingEvent.user_id == user_id)
        
        if subscription_id:
            query = query.filter(MINGUSBillingEvent.subscription_id == subscription_id)
        
        if event_type:
            query = query.filter(MINGUSBillingEvent.event_type == event_type)
        
        return query.order_by(desc(MINGUSBillingEvent.event_timestamp)).limit(limit).all()
    
    # =====================================================
    # ANALYTICS AND REPORTING
    # =====================================================
    
    def get_subscription_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get subscription analytics for reporting.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics data
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Active subscriptions
            active_subscriptions = self.db.query(MINGUSSubscription).filter(
                and_(
                    MINGUSSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
                    MINGUSSubscription.created_at >= since_date
                )
            ).count()
            
            # New subscriptions
            new_subscriptions = self.db.query(MINGUSSubscription).filter(
                MINGUSSubscription.created_at >= since_date
            ).count()
            
            # Canceled subscriptions
            canceled_subscriptions = self.db.query(MINGUSSubscription).filter(
                and_(
                    MINGUSSubscription.status == SubscriptionStatus.CANCELED,
                    MINGUSSubscription.canceled_at >= since_date
                )
            ).count()
            
            # Revenue data
            revenue_data = self.db.query(
                MINGUSSubscription.tier,
                MINGUSSubscription.billing_cycle,
                func.sum(MINGUSSubscription.amount).label('total_revenue'),
                func.count(MINGUSSubscription.id).label('subscription_count')
            ).filter(
                MINGUSSubscription.created_at >= since_date
            ).group_by(
                MINGUSSubscription.tier,
                MINGUSSubscription.billing_cycle
            ).all()
            
            # Usage analytics
            usage_data = self.db.query(
                MINGUSUsageRecord.usage_type,
                func.sum(MINGUSUsageRecord.quantity).label('total_usage'),
                func.count(MINGUSUsageRecord.id).label('usage_count')
            ).filter(
                MINGUSUsageRecord.usage_date >= since_date
            ).group_by(MINGUSUsageRecord.usage_type).all()
            
            return {
                'period_days': days,
                'active_subscriptions': active_subscriptions,
                'new_subscriptions': new_subscriptions,
                'canceled_subscriptions': canceled_subscriptions,
                'revenue_by_tier': [
                    {
                        'tier': row.tier.value,
                        'billing_cycle': row.billing_cycle.value,
                        'total_revenue': float(row.total_revenue),
                        'subscription_count': row.subscription_count
                    }
                    for row in revenue_data
                ],
                'usage_by_type': [
                    {
                        'usage_type': row.usage_type.value,
                        'total_usage': row.total_usage,
                        'usage_count': row.usage_count
                    }
                    for row in usage_data
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get subscription analytics: {e}")
            return {} 