"""
Subscription Management Service for MINGUS
Handles subscription lifecycle, feature usage, and tier management
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func

from ..models.subscription import (
    Subscription, PricingTier, FeatureUsage, Customer,
    AuditLog, AuditEventType, AuditSeverity
)
from .payment_processor import PaymentProcessor

logger = logging.getLogger(__name__)

class SubscriptionManagerError(Exception):
    """Custom exception for subscription management errors"""
    pass

class SubscriptionManager:
    """Manages subscription lifecycle and feature usage"""
    
    def __init__(self, db_session: Session, payment_processor: PaymentProcessor):
        self.db = db_session
        self.payment_processor = payment_processor
    
    def get_active_subscription(self, customer_id: int) -> Optional[Subscription]:
        """Get the active subscription for a customer"""
        return self.db.query(Subscription).filter(
            and_(
                Subscription.customer_id == customer_id,
                Subscription.status.in_(['active', 'trialing'])
            )
        ).first()
    
    def get_subscription_usage(self, subscription_id: int, month: int = None, year: int = None) -> FeatureUsage:
        """Get or create feature usage record for a subscription"""
        if month is None:
            month = datetime.utcnow().month
        if year is None:
            year = datetime.utcnow().year
        
        usage = self.db.query(FeatureUsage).filter(
            and_(
                FeatureUsage.subscription_id == subscription_id,
                FeatureUsage.usage_month == month,
                FeatureUsage.usage_year == year
            )
        ).first()
        
        if not usage:
            usage = FeatureUsage(
                subscription_id=subscription_id,
                usage_month=month,
                usage_year=year
            )
            self.db.add(usage)
            self.db.commit()
        
        return usage
    
    def check_feature_availability(
        self, 
        customer_id: int, 
        feature_name: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if a feature is available for a customer"""
        try:
            subscription = self.get_active_subscription(customer_id)
            if not subscription:
                return False, {
                    'available': False,
                    'reason': 'no_active_subscription',
                    'message': 'No active subscription found'
                }
            
            # Get current usage
            usage = self.get_subscription_usage(subscription.id)
            
            # Get tier limits
            tier_limits = subscription.pricing_tier
            
            # Check if feature is available
            is_available = usage.is_feature_available(feature_name, tier_limits)
            
            if is_available:
                return True, {
                    'available': True,
                    'subscription_id': subscription.id,
                    'tier': tier_limits.tier_type.value,
                    'current_usage': getattr(usage, f'{feature_name}_used', 0),
                    'limit': getattr(tier_limits, f'max_{feature_name}_per_month', 0)
                }
            else:
                return False, {
                    'available': False,
                    'reason': 'limit_reached',
                    'subscription_id': subscription.id,
                    'tier': tier_limits.tier_type.value,
                    'current_usage': getattr(usage, f'{feature_name}_used', 0),
                    'limit': getattr(tier_limits, f'max_{feature_name}_per_month', 0),
                    'message': f'{feature_name} limit reached for current tier'
                }
                
        except Exception as e:
            logger.error(f"Error checking feature availability: {e}")
            return False, {
                'available': False,
                'reason': 'error',
                'message': str(e)
            }
    
    def use_feature(
        self, 
        customer_id: int, 
        feature_name: str,
        quantity: int = 1
    ) -> Tuple[bool, Dict[str, Any]]:
        """Use a feature and track usage"""
        try:
            # Check if feature is available
            is_available, details = self.check_feature_availability(customer_id, feature_name)
            
            if not is_available:
                # Log access denied event
                subscription = self.get_active_subscription(customer_id)
                if subscription:
                    self._log_audit_event(
                        event_type=AuditEventType.FEATURE_ACCESS_DENIED,
                        customer_id=customer_id,
                        subscription_id=subscription.id,
                        event_description=f"Feature access denied: {feature_name}",
                        metadata=details
                    )
                
                return False, details
            
            # Get usage record
            subscription = self.get_active_subscription(customer_id)
            usage = self.get_subscription_usage(subscription.id)
            
            # Update usage
            current_usage = getattr(usage, f'{feature_name}_used', 0)
            setattr(usage, f'{feature_name}_used', current_usage + quantity)
            usage.last_usage_date = datetime.utcnow()
            
            self.db.commit()
            
            # Log feature usage event
            self._log_audit_event(
                event_type=AuditEventType.FEATURE_USED,
                customer_id=customer_id,
                subscription_id=subscription.id,
                feature_usage_id=usage.id,
                event_description=f"Feature used: {feature_name} (quantity: {quantity})",
                metadata={
                    'feature_name': feature_name,
                    'quantity': quantity,
                    'new_total': current_usage + quantity
                }
            )
            
            # Check if limit is now reached
            tier_limits = subscription.pricing_tier
            new_usage = current_usage + quantity
            limit = getattr(tier_limits, f'max_{feature_name}_per_month', 0)
            
            if limit > 0 and new_usage >= limit:
                self._log_audit_event(
                    event_type=AuditEventType.FEATURE_LIMIT_REACHED,
                    customer_id=customer_id,
                    subscription_id=subscription.id,
                    feature_usage_id=usage.id,
                    event_description=f"Feature limit reached: {feature_name}",
                    metadata={
                        'feature_name': feature_name,
                        'usage': new_usage,
                        'limit': limit
                    }
                )
            
            return True, {
                'success': True,
                'feature_name': feature_name,
                'quantity_used': quantity,
                'new_total': new_usage,
                'limit': limit
            }
            
        except Exception as e:
            logger.error(f"Error using feature: {e}")
            self.db.rollback()
            return False, {
                'success': False,
                'error': str(e)
            }
    
    def upgrade_subscription(
        self, 
        customer_id: int, 
        new_tier_id: int,
        billing_cycle: str = None
    ) -> Dict[str, Any]:
        """Upgrade a customer's subscription to a higher tier"""
        try:
            subscription = self.get_active_subscription(customer_id)
            if not subscription:
                raise SubscriptionManagerError("No active subscription found")
            
            new_tier = self.db.query(PricingTier).filter(PricingTier.id == new_tier_id).first()
            if not new_tier:
                raise SubscriptionManagerError("Pricing tier not found")
            
            # Check if it's actually an upgrade
            current_tier_order = self._get_tier_order(subscription.pricing_tier.tier_type)
            new_tier_order = self._get_tier_order(new_tier.tier_type)
            
            if new_tier_order <= current_tier_order:
                raise SubscriptionManagerError("New tier must be higher than current tier")
            
            # Update subscription
            old_tier = subscription.pricing_tier.tier_type.value
            result = self.payment_processor.update_subscription(
                subscription_id=subscription.id,
                pricing_tier_id=new_tier_id,
                billing_cycle=billing_cycle or subscription.billing_cycle
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'old_tier': old_tier,
                'new_tier': new_tier.tier_type.value,
                'billing_cycle': result.billing_cycle
            }
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def downgrade_subscription(
        self, 
        customer_id: int, 
        new_tier_id: int,
        effective_date: str = 'period_end'
    ) -> Dict[str, Any]:
        """Downgrade a customer's subscription to a lower tier"""
        try:
            subscription = self.get_active_subscription(customer_id)
            if not subscription:
                raise SubscriptionManagerError("No active subscription found")
            
            new_tier = self.db.query(PricingTier).filter(PricingTier.id == new_tier_id).first()
            if not new_tier:
                raise SubscriptionManagerError("Pricing tier not found")
            
            # Check if it's actually a downgrade
            current_tier_order = self._get_tier_order(subscription.pricing_tier.tier_type)
            new_tier_order = self._get_tier_order(new_tier.tier_type)
            
            if new_tier_order >= current_tier_order:
                raise SubscriptionManagerError("New tier must be lower than current tier")
            
            if effective_date == 'immediate':
                # Update immediately
                result = self.payment_processor.update_subscription(
                    subscription_id=subscription.id,
                    pricing_tier_id=new_tier_id
                )
            else:
                # Schedule for period end
                result = self.payment_processor.update_subscription(
                    subscription_id=subscription.id,
                    pricing_tier_id=new_tier_id,
                    cancel_at_period_end=True
                )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'old_tier': subscription.pricing_tier.tier_type.value,
                'new_tier': new_tier.tier_type.value,
                'effective_date': effective_date
            }
            
        except Exception as e:
            logger.error(f"Error downgrading subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reset_monthly_usage(self, subscription_id: int) -> bool:
        """Reset monthly usage counters for a subscription"""
        try:
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            # Get current usage record
            usage = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.subscription_id == subscription_id,
                    FeatureUsage.usage_month == current_month,
                    FeatureUsage.usage_year == current_year
                )
            ).first()
            
            if usage and not usage.is_reset:
                # Reset all usage counters
                usage.health_checkins_used = 0
                usage.financial_reports_used = 0
                usage.ai_insights_used = 0
                usage.projects_created = 0
                usage.team_members_added = 0
                usage.storage_used_mb = 0
                usage.api_calls_made = 0
                usage.login_count = 0
                usage.is_reset = True
                
                self.db.commit()
                
                # Log reset event
                self._log_audit_event(
                    event_type=AuditEventType.USAGE_RESET,
                    subscription_id=subscription_id,
                    event_description=f"Monthly usage reset for {current_month}/{current_year}",
                    metadata={'month': current_month, 'year': current_year}
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resetting monthly usage: {e}")
            self.db.rollback()
            return False
    
    def get_usage_summary(self, customer_id: int) -> Dict[str, Any]:
        """Get a summary of current usage for a customer"""
        try:
            subscription = self.get_active_subscription(customer_id)
            if not subscription:
                return {
                    'has_subscription': False,
                    'message': 'No active subscription'
                }
            
            usage = self.get_subscription_usage(subscription.id)
            tier = subscription.pricing_tier
            
            summary = {
                'has_subscription': True,
                'subscription_id': subscription.id,
                'tier': tier.tier_type.value,
                'tier_name': tier.name,
                'billing_cycle': subscription.billing_cycle,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                'usage': {
                    'health_checkins': {
                        'used': usage.health_checkins_used,
                        'limit': tier.max_health_checkins_per_month,
                        'percentage': usage.get_usage_percentage('health_checkins', tier)
                    },
                    'financial_reports': {
                        'used': usage.financial_reports_used,
                        'limit': tier.max_financial_reports_per_month,
                        'percentage': usage.get_usage_percentage('financial_reports', tier)
                    },
                    'ai_insights': {
                        'used': usage.ai_insights_used,
                        'limit': tier.max_ai_insights_per_month,
                        'percentage': usage.get_usage_percentage('ai_insights', tier)
                    },
                    'projects': {
                        'used': usage.projects_created,
                        'limit': tier.max_projects,
                        'percentage': usage.get_usage_percentage('projects', tier)
                    },
                    'team_members': {
                        'used': usage.team_members_added,
                        'limit': tier.max_team_members,
                        'percentage': usage.get_usage_percentage('team_members', tier)
                    },
                    'storage_mb': {
                        'used': usage.storage_used_mb,
                        'limit': tier.max_storage_gb * 1024,  # Convert GB to MB
                        'percentage': min(100.0, (usage.storage_used_mb / (tier.max_storage_gb * 1024)) * 100) if tier.max_storage_gb > 0 else 0
                    },
                    'api_calls': {
                        'used': usage.api_calls_made,
                        'limit': tier.max_api_calls_per_month,
                        'percentage': usage.get_usage_percentage('api_calls', tier)
                    }
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting usage summary: {e}")
            return {
                'has_subscription': False,
                'error': str(e)
            }
    
    def _get_tier_order(self, tier_type) -> int:
        """Get the order/level of a tier (higher number = higher tier)"""
        tier_order = {
            'budget': 1,
            'mid_tier': 2,
            'professional': 3
        }
        return tier_order.get(tier_type.value, 0)
    
    def _log_audit_event(
        self,
        event_type: AuditEventType,
        customer_id: int = None,
        subscription_id: int = None,
        feature_usage_id: int = None,
        event_description: str = None,
        metadata: Dict = None
    ):
        """Log an audit event"""
        try:
            audit_log = AuditLog(
                event_type=event_type,
                customer_id=customer_id,
                subscription_id=subscription_id,
                feature_usage_id=feature_usage_id,
                event_description=event_description,
                metadata=metadata
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log audit event: {e}")
            # Don't raise exception for audit logging failures 