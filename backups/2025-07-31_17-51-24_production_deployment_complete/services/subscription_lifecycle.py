"""
Subscription Lifecycle Management Service for MINGUS
Handles all subscription states, transitions, and lifecycle events
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
import json

from ..models.subscription import (
    Customer, Subscription, BillingHistory, FeatureUsage,
    AuditLog, AuditEventType, AuditSeverity, PricingTier
)
from ..config.base import Config

logger = logging.getLogger(__name__)

class SubscriptionLifecycleError(Exception):
    """Custom exception for subscription lifecycle errors"""
    pass

class SubscriptionState(Enum):
    """All possible subscription states"""
    # Initial states
    DRAFT = "draft"                    # Subscription being created
    PENDING_ACTIVATION = "pending_activation"  # Waiting for activation
    
    # Active states
    TRIALING = "trialing"              # Free trial period
    ACTIVE = "active"                  # Fully active subscription
    PAST_DUE = "past_due"              # Payment failed, grace period
    
    # Suspended states
    SUSPENDED = "suspended"            # Temporarily suspended
    UNPAID = "unpaid"                  # Payment failed, access suspended
    
    # Cancellation states
    CANCELING = "canceling"            # Cancellation in progress
    CANCELED = "canceled"              # Subscription canceled
    
    # Recovery states
    REACTIVATING = "reactivating"      # Reactivation in progress
    PAST_DUE_RECOVERY = "past_due_recovery"  # Recovering from past due
    
    # Error states
    ERROR = "error"                    # System error state
    EXPIRED = "expired"                # Subscription expired

class LifecycleEvent(Enum):
    """Lifecycle events that trigger state transitions"""
    # Creation events
    SUBSCRIPTION_CREATED = "subscription_created"
    TRIAL_STARTED = "trial_started"
    ACTIVATION_REQUESTED = "activation_requested"
    
    # Payment events
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_RETRY = "payment_retry"
    PAYMENT_RECOVERED = "payment_recovered"
    
    # Trial events
    TRIAL_ENDING = "trial_ending"
    TRIAL_ENDED = "trial_ended"
    TRIAL_CONVERTED = "trial_converted"
    
    # Cancellation events
    CANCELLATION_REQUESTED = "cancellation_requested"
    CANCELLATION_IMMEDIATE = "cancellation_immediate"
    CANCELLATION_SCHEDULED = "cancellation_scheduled"
    CANCELLATION_COMPLETED = "cancellation_completed"
    
    # Recovery events
    REACTIVATION_REQUESTED = "reactivation_requested"
    REACTIVATION_COMPLETED = "reactivation_completed"
    
    # System events
    SYSTEM_ERROR = "system_error"
    EXPIRATION = "expiration"
    GRACE_PERIOD_STARTED = "grace_period_started"
    GRACE_PERIOD_ENDED = "grace_period_ended"

    # State change events
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription_downgraded"
    SUBSCRIPTION_PAUSED = "subscription_paused"
    SUBSCRIPTION_UNPAUSED = "subscription_unpaused"

class SubscriptionLifecycleManager:
    """Comprehensive subscription lifecycle management for MINGUS"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # State transition rules
        self.state_transitions = self._define_state_transitions()
        
        # Lifecycle hooks
        self.lifecycle_hooks = self._define_lifecycle_hooks()
        
        # Configuration
        self.config = {
            'trial_duration_days': 14,
            'grace_period_days': 7,
            'past_due_retry_attempts': 3,
            'suspension_threshold_days': 30,
            'auto_cancel_after_days': 90,
            'reactivation_window_days': 30
        }
    
    def _define_state_transitions(self) -> Dict[SubscriptionState, Dict[LifecycleEvent, SubscriptionState]]:
        """Define valid state transitions"""
        return {
            # Draft state transitions
            SubscriptionState.DRAFT: {
                LifecycleEvent.SUBSCRIPTION_CREATED: SubscriptionState.PENDING_ACTIVATION,
                LifecycleEvent.TRIAL_STARTED: SubscriptionState.TRIALING,
                LifecycleEvent.ACTIVATION_REQUESTED: SubscriptionState.ACTIVE
            },
            
            # Pending activation transitions
            SubscriptionState.PENDING_ACTIVATION: {
                LifecycleEvent.TRIAL_STARTED: SubscriptionState.TRIALING,
                LifecycleEvent.ACTIVATION_REQUESTED: SubscriptionState.ACTIVE,
                LifecycleEvent.CANCELLATION_REQUESTED: SubscriptionState.CANCELED
            },
            
            # Trialing transitions
            SubscriptionState.TRIALING: {
                LifecycleEvent.TRIAL_CONVERTED: SubscriptionState.ACTIVE,
                LifecycleEvent.TRIAL_ENDED: SubscriptionState.PAST_DUE,
                LifecycleEvent.CANCELLATION_REQUESTED: SubscriptionState.CANCELING,
                LifecycleEvent.CANCELLATION_IMMEDIATE: SubscriptionState.CANCELED,
                LifecycleEvent.SUBSCRIPTION_UPGRADED: SubscriptionState.ACTIVE,
                LifecycleEvent.SUBSCRIPTION_DOWNGRADED: SubscriptionState.ACTIVE
            },
            
            # Active transitions
            SubscriptionState.ACTIVE: {
                LifecycleEvent.PAYMENT_FAILED: SubscriptionState.PAST_DUE,
                LifecycleEvent.CANCELLATION_REQUESTED: SubscriptionState.CANCELING,
                LifecycleEvent.CANCELLATION_IMMEDIATE: SubscriptionState.CANCELED,
                LifecycleEvent.EXPIRATION: SubscriptionState.EXPIRED,
                LifecycleEvent.SUBSCRIPTION_UPGRADED: SubscriptionState.ACTIVE,
                LifecycleEvent.SUBSCRIPTION_DOWNGRADED: SubscriptionState.ACTIVE,
                LifecycleEvent.SUBSCRIPTION_PAUSED: SubscriptionState.SUSPENDED
            },
            
            # Past due transitions
            SubscriptionState.PAST_DUE: {
                LifecycleEvent.PAYMENT_SUCCEEDED: SubscriptionState.ACTIVE,
                LifecycleEvent.PAYMENT_RECOVERED: SubscriptionState.ACTIVE,
                LifecycleEvent.GRACE_PERIOD_STARTED: SubscriptionState.PAST_DUE,
                LifecycleEvent.GRACE_PERIOD_ENDED: SubscriptionState.UNPAID,
                LifecycleEvent.CANCELLATION_REQUESTED: SubscriptionState.CANCELING,
                LifecycleEvent.CANCELLATION_IMMEDIATE: SubscriptionState.CANCELED
            },
            
            # Unpaid transitions
            SubscriptionState.UNPAID: {
                LifecycleEvent.PAYMENT_SUCCEEDED: SubscriptionState.ACTIVE,
                LifecycleEvent.PAYMENT_RECOVERED: SubscriptionState.ACTIVE,
                LifecycleEvent.REACTIVATION_REQUESTED: SubscriptionState.REACTIVATING,
                LifecycleEvent.CANCELLATION_REQUESTED: SubscriptionState.CANCELING,
                LifecycleEvent.CANCELLATION_IMMEDIATE: SubscriptionState.CANCELED,
                LifecycleEvent.EXPIRATION: SubscriptionState.EXPIRED
            },
            
            # Suspended transitions (paused)
            SubscriptionState.SUSPENDED: {
                LifecycleEvent.REACTIVATION_REQUESTED: SubscriptionState.REACTIVATING,
                LifecycleEvent.SUBSCRIPTION_UNPAUSED: SubscriptionState.ACTIVE,
                LifecycleEvent.CANCELLATION_REQUESTED: SubscriptionState.CANCELING,
                LifecycleEvent.CANCELLATION_IMMEDIATE: SubscriptionState.CANCELED
            },
            
            # Canceling transitions
            SubscriptionState.CANCELING: {
                LifecycleEvent.CANCELLATION_COMPLETED: SubscriptionState.CANCELED,
                LifecycleEvent.REACTIVATION_REQUESTED: SubscriptionState.ACTIVE
            },
            
            # Reactivating transitions
            SubscriptionState.REACTIVATING: {
                LifecycleEvent.REACTIVATION_COMPLETED: SubscriptionState.ACTIVE,
                LifecycleEvent.SYSTEM_ERROR: SubscriptionState.ERROR
            },
            
            # Error transitions
            SubscriptionState.ERROR: {
                LifecycleEvent.REACTIVATION_REQUESTED: SubscriptionState.REACTIVATING,
                LifecycleEvent.CANCELLATION_REQUESTED: SubscriptionState.CANCELING
            }
        }
    
    def _define_lifecycle_hooks(self) -> Dict[LifecycleEvent, List[Callable]]:
        """Define lifecycle hooks for each event"""
        return {
            LifecycleEvent.SUBSCRIPTION_CREATED: [
                self._hook_welcome_email,
                self._hook_initialize_usage_tracking,
                self._hook_create_audit_log
            ],
            LifecycleEvent.TRIAL_STARTED: [
                self._hook_trial_welcome,
                self._hook_set_trial_period,
                self._hook_create_audit_log
            ],
            LifecycleEvent.TRIAL_ENDING: [
                self._hook_trial_ending_notification,
                self._hook_create_audit_log
            ],
            LifecycleEvent.TRIAL_CONVERTED: [
                self._hook_trial_conversion,
                self._hook_create_audit_log
            ],
            LifecycleEvent.PAYMENT_FAILED: [
                self._hook_payment_failure_notification,
                self._hook_start_grace_period,
                self._hook_create_audit_log
            ],
            LifecycleEvent.PAYMENT_SUCCEEDED: [
                self._hook_payment_success,
                self._hook_reset_grace_period,
                self._hook_create_audit_log
            ],
            LifecycleEvent.CANCELLATION_REQUESTED: [
                self._hook_cancellation_request,
                self._hook_create_audit_log
            ],
            LifecycleEvent.CANCELLATION_COMPLETED: [
                self._hook_cancellation_complete,
                self._hook_create_audit_log
            ],
            LifecycleEvent.REACTIVATION_REQUESTED: [
                self._hook_reactivation_request,
                self._hook_create_audit_log
            ],
            LifecycleEvent.REACTIVATION_COMPLETED: [
                self._hook_reactivation_complete,
                self._hook_create_audit_log
            ]
        }
    
    # ============================================================================
    # CORE LIFECYCLE MANAGEMENT
    # ============================================================================
    
    def process_lifecycle_event(
        self,
        subscription_id: int,
        event: LifecycleEvent,
        metadata: Dict = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Process a lifecycle event and transition subscription state"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            current_state = SubscriptionState(subscription.status)
            
            # Check if transition is valid
            if not self._is_valid_transition(current_state, event):
                return {
                    'success': False,
                    'error': f'Invalid transition from {current_state.value} with event {event.value}'
                }
            
            # Get new state
            new_state = self.state_transitions[current_state][event]
            
            # Execute pre-transition hooks
            pre_hooks_result = self._execute_pre_transition_hooks(
                subscription, event, current_state, new_state, metadata
            )
            
            if not pre_hooks_result['success']:
                return pre_hooks_result
            
            # Update subscription state
            old_status = subscription.status
            subscription.status = new_state.value
            subscription.updated_at = datetime.utcnow()
            
            # Update state-specific fields
            self._update_state_specific_fields(subscription, new_state, event, metadata)
            
            # Execute post-transition hooks
            post_hooks_result = self._execute_post_transition_hooks(
                subscription, event, current_state, new_state, metadata
            )
            
            # Commit changes
            self.db.commit()
            
            # Log state transition
            self._log_state_transition(
                subscription, old_status, new_state.value, event, metadata, user_id
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'old_state': old_status,
                'new_state': new_state.value,
                'event': event.value,
                'metadata': metadata,
                'pre_hooks_result': pre_hooks_result,
                'post_hooks_result': post_hooks_result
            }
            
        except Exception as e:
            logger.error(f"Error processing lifecycle event: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_subscription_lifecycle_status(
        self,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive lifecycle status for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get current state
            current_state = SubscriptionState(subscription.status)
            
            # Get available transitions
            available_transitions = self._get_available_transitions(current_state)
            
            # Get lifecycle history
            lifecycle_history = self._get_lifecycle_history(subscription_id)
            
            # Get state-specific information
            state_info = self._get_state_specific_info(subscription, current_state)
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'customer_id': subscription.customer_id,
                'current_state': current_state.value,
                'current_state_info': state_info,
                'available_transitions': available_transitions,
                'lifecycle_history': lifecycle_history,
                'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
                'updated_at': subscription.updated_at.isoformat() if subscription.updated_at else None,
                'next_billing_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription lifecycle status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_subscriptions_by_state(
        self,
        state: SubscriptionState = None,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """Get all subscriptions in a specific state"""
        try:
            query = self.db.query(Subscription)
            
            if state:
                query = query.filter(Subscription.status == state.value)
            
            if not include_inactive:
                inactive_states = [
                    SubscriptionState.CANCELED.value,
                    SubscriptionState.EXPIRED.value,
                    SubscriptionState.ERROR.value
                ]
                query = query.filter(~Subscription.status.in_(inactive_states))
            
            subscriptions = query.all()
            
            result = []
            for subscription in subscriptions:
                result.append({
                    'subscription_id': subscription.id,
                    'customer_id': subscription.customer_id,
                    'status': subscription.status,
                    'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
                    'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                    'amount': subscription.amount,
                    'currency': subscription.currency
                })
            
            return {
                'success': True,
                'subscriptions': result,
                'count': len(result),
                'state': state.value if state else 'all'
            }
            
        except Exception as e:
            logger.error(f"Error getting subscriptions by state: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # LIFECYCLE OPERATIONS
    # ============================================================================
    
    def start_trial(
        self,
        subscription_id: int,
        trial_days: int = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Start a trial period for a subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Check if subscription can start trial
            if subscription.status not in ['draft', 'pending_activation']:
                return {
                    'success': False,
                    'error': f'Cannot start trial for subscription in {subscription.status} state'
                }
            
            # Set trial period
            trial_duration = trial_days or self.config['trial_duration_days']
            subscription.trial_start = datetime.utcnow()
            subscription.trial_end = datetime.utcnow() + timedelta(days=trial_duration)
            
            # Process trial start event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=LifecycleEvent.TRIAL_STARTED,
                metadata={
                    'trial_days': trial_duration,
                    'trial_start': subscription.trial_start.isoformat(),
                    'trial_end': subscription.trial_end.isoformat()
                },
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error starting trial: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def convert_trial_to_paid(
        self,
        subscription_id: int,
        payment_method_id: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Convert a trial subscription to paid"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            if subscription.status != 'trialing':
                return {
                    'success': False,
                    'error': f'Cannot convert subscription in {subscription.status} state'
                }
            
            # Update subscription for paid status
            subscription.trial_end = datetime.utcnow()
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)  # Monthly billing
            
            # Process trial conversion event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=LifecycleEvent.TRIAL_CONVERTED,
                metadata={
                    'payment_method_id': payment_method_id,
                    'conversion_date': datetime.utcnow().isoformat()
                },
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error converting trial to paid: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def request_cancellation(
        self,
        subscription_id: int,
        effective_date: str = 'period_end',
        reason: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Request subscription cancellation"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Check if subscription can be canceled
            if subscription.status in ['canceled', 'expired']:
                return {
                    'success': False,
                    'error': f'Cannot cancel subscription in {subscription.status} state'
                }
            
            # Set cancellation details
            if effective_date == 'immediate':
                subscription.canceled_at = datetime.utcnow()
                event = LifecycleEvent.CANCELLATION_IMMEDIATE
            else:
                subscription.cancel_at_period_end = True
                event = LifecycleEvent.CANCELLATION_REQUESTED
            
            # Process cancellation event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=event,
                metadata={
                    'effective_date': effective_date,
                    'reason': reason,
                    'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None
                },
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error requesting cancellation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def request_reactivation(
        self,
        subscription_id: int,
        payment_method_id: str = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Request subscription reactivation"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == subscription_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get churn risk analysis
            risk_analysis = self._analyze_churn_risk(customer, customer.subscriptions[0])
            
            if risk_analysis['risk_level'] == 'low':
                return {
                    'success': True,
                    'message': 'No churn prevention action needed - low risk',
                    'risk_level': risk_analysis['risk_level']
                }
            
            # Execute appropriate workflow
            if workflow_type == 'automated':
                workflow_result = self._execute_automated_churn_workflow(
                    customer, risk_analysis
                )
            else:
                workflow_result = self._execute_manual_churn_workflow(
                    customer, risk_analysis
                )
            
            # Log workflow execution
            self._log_revenue_event(
                event_type=AuditEventType.CHURN_PREVENTION_WORKFLOW_EXECUTED,
                customer_id=customer_id,
                event_description=f"Churn prevention workflow executed: {workflow_type}",
                metadata={
                    'workflow_type': workflow_type,
                    'risk_level': risk_analysis['risk_level'],
                    'risk_score': risk_analysis['risk_score'],
                    'actions_taken': workflow_result['actions_taken']
                }
            )
            
            return {
                'success': True,
                'workflow_result': workflow_result,
                'risk_analysis': risk_analysis
            }
            
        except Exception as e:
            logger.error(f"Error executing churn prevention workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
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
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Check if subscription can be activated
            if subscription.status not in ['draft', 'pending_activation', 'trialing']:
                return {
                    'success': False,
                    'error': f'Cannot activate subscription in {subscription.status} state'
                }
            
            # Set up billing period
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)  # Monthly billing
            
            # Process activation event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=LifecycleEvent.ACTIVATION_REQUESTED,
                metadata={
                    'payment_method_id': payment_method_id,
                    'activation_date': datetime.utcnow().isoformat(),
                    'billing_period_start': subscription.current_period_start.isoformat(),
                    'billing_period_end': subscription.current_period_end.isoformat()
                },
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error activating subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upgrade_subscription(
        self,
        subscription_id: int,
        new_tier_id: int,
        proration_behavior: str = 'create_prorations',
        user_id: int = None
    ) -> Dict[str, Any]:
        """Upgrade subscription to higher tier with proration"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get current and new pricing tiers
            current_tier = subscription.pricing_tier
            new_tier = self.db.query(PricingTier).filter(PricingTier.id == new_tier_id).first()
            
            if not new_tier:
                return {
                    'success': False,
                    'error': 'New pricing tier not found'
                }
            
            # Validate upgrade
            if not self._is_valid_upgrade(current_tier, new_tier):
                return {
                    'success': False,
                    'error': f'Invalid upgrade from {current_tier.name} to {new_tier.name}'
                }
            
            # Calculate proration
            proration_amount = self._calculate_upgrade_proration(
                subscription, current_tier, new_tier, proration_behavior
            )
            
            # Update subscription
            old_tier_id = subscription.pricing_tier_id
            subscription.pricing_tier_id = new_tier_id
            subscription.amount = new_tier.monthly_price
            
            # Process upgrade event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=LifecycleEvent.SUBSCRIPTION_UPGRADED,
                metadata={
                    'old_tier_id': old_tier_id,
                    'new_tier_id': new_tier_id,
                    'old_tier_name': current_tier.name,
                    'new_tier_name': new_tier.name,
                    'proration_amount': proration_amount,
                    'proration_behavior': proration_behavior,
                    'upgrade_date': datetime.utcnow().isoformat()
                },
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error upgrading subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def downgrade_subscription(
        self,
        subscription_id: int,
        new_tier_id: int,
        effective_date: str = 'period_end',
        proration_behavior: str = 'create_prorations',
        user_id: int = None
    ) -> Dict[str, Any]:
        """Downgrade subscription to lower tier with proration"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get current and new pricing tiers
            current_tier = subscription.pricing_tier
            new_tier = self.db.query(PricingTier).filter(PricingTier.id == new_tier_id).first()
            
            if not new_tier:
                return {
                    'success': False,
                    'error': 'New pricing tier not found'
                }
            
            # Validate downgrade
            if not self._is_valid_downgrade(current_tier, new_tier):
                return {
                    'success': False,
                    'error': f'Invalid downgrade from {current_tier.name} to {new_tier.name}'
                }
            
            # Handle effective date
            if effective_date == 'immediate':
                # Immediate downgrade with proration
                proration_amount = self._calculate_downgrade_proration(
                    subscription, current_tier, new_tier, proration_behavior
                )
                
                # Update subscription immediately
                old_tier_id = subscription.pricing_tier_id
                subscription.pricing_tier_id = new_tier_id
                subscription.amount = new_tier.monthly_price
                
                event = LifecycleEvent.SUBSCRIPTION_DOWNGRADED
                metadata = {
                    'old_tier_id': old_tier_id,
                    'new_tier_id': new_tier_id,
                    'old_tier_name': current_tier.name,
                    'new_tier_name': new_tier.name,
                    'proration_amount': proration_amount,
                    'proration_behavior': proration_behavior,
                    'effective_date': 'immediate',
                    'downgrade_date': datetime.utcnow().isoformat()
                }
            else:
                # Schedule downgrade for period end
                subscription.downgrade_at_period_end = True
                subscription.downgrade_to_tier_id = new_tier_id
                
                event = LifecycleEvent.SUBSCRIPTION_DOWNGRADED
                metadata = {
                    'old_tier_id': subscription.pricing_tier_id,
                    'new_tier_id': new_tier_id,
                    'old_tier_name': current_tier.name,
                    'new_tier_name': new_tier.name,
                    'effective_date': 'period_end',
                    'scheduled_date': subscription.current_period_end.isoformat(),
                    'downgrade_date': datetime.utcnow().isoformat()
                }
            
            # Process downgrade event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=event,
                metadata=metadata,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error downgrading subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def pause_subscription(
        self,
        subscription_id: int,
        pause_reason: str = None,
        pause_duration_days: int = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Pause subscription (temporary suspension)"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Check if subscription can be paused
            if subscription.status != 'active':
                return {
                    'success': False,
                    'error': f'Cannot pause subscription in {subscription.status} state'
                }
            
            # Set pause details
            subscription.paused_at = datetime.utcnow()
            subscription.pause_reason = pause_reason
            subscription.pause_duration_days = pause_duration_days
            
            if pause_duration_days:
                subscription.pause_until = datetime.utcnow() + timedelta(days=pause_duration_days)
            
            # Process pause event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=LifecycleEvent.SUBSCRIPTION_PAUSED,
                metadata={
                    'pause_reason': pause_reason,
                    'pause_duration_days': pause_duration_days,
                    'pause_until': subscription.pause_until.isoformat() if subscription.pause_until else None,
                    'paused_at': subscription.paused_at.isoformat()
                },
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error pausing subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def unpause_subscription(
        self,
        subscription_id: int,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Unpause subscription and restore to active state"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Check if subscription can be unpaused
            if subscription.status != 'suspended':
                return {
                    'success': False,
                    'error': f'Cannot unpause subscription in {subscription.status} state'
                }
            
            # Clear pause details
            pause_duration = (datetime.utcnow() - subscription.paused_at).days if subscription.paused_at else None
            subscription.paused_at = None
            subscription.pause_reason = None
            subscription.pause_duration_days = None
            subscription.pause_until = None
            
            # Process unpause event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=LifecycleEvent.SUBSCRIPTION_UNPAUSED,
                metadata={
                    'pause_duration_days': pause_duration,
                    'unpaused_at': datetime.utcnow().isoformat()
                },
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error unpausing subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_subscription(
        self,
        subscription_id: int,
        effective_date: str = 'period_end',
        reason: str = None,
        refund_amount: float = None,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Cancel subscription with access until period end"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Check if subscription can be canceled
            if subscription.status in ['canceled', 'expired']:
                return {
                    'success': False,
                    'error': f'Cannot cancel subscription in {subscription.status} state'
                }
            
            # Handle effective date
            if effective_date == 'immediate':
                # Immediate cancellation
                subscription.canceled_at = datetime.utcnow()
                subscription.cancel_at_period_end = False
                
                event = LifecycleEvent.CANCELLATION_IMMEDIATE
                metadata = {
                    'effective_date': 'immediate',
                    'reason': reason,
                    'refund_amount': refund_amount,
                    'canceled_at': subscription.canceled_at.isoformat()
                }
            else:
                # Cancel at period end (maintain access until then)
                subscription.cancel_at_period_end = True
                subscription.canceled_at = None  # Will be set when period ends
                
                event = LifecycleEvent.CANCELLATION_REQUESTED
                metadata = {
                    'effective_date': 'period_end',
                    'reason': reason,
                    'access_until': subscription.current_period_end.isoformat(),
                    'cancel_requested_at': datetime.utcnow().isoformat()
                }
            
            # Process cancellation event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=event,
                metadata=metadata,
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reactivate_subscription(
        self,
        subscription_id: int,
        payment_method_id: str = None,
        restore_features: bool = True,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Reactivate canceled subscription"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Check if subscription can be reactivated
            if subscription.status not in ['canceled', 'unpaid', 'suspended']:
                return {
                    'success': False,
                    'error': f'Cannot reactivate subscription in {subscription.status} state'
                }
            
            # Check reactivation window for canceled subscriptions
            if subscription.status == 'canceled' and subscription.canceled_at:
                days_since_canceled = (datetime.utcnow() - subscription.canceled_at).days
                if days_since_canceled > self.config['reactivation_window_days']:
                    return {
                        'success': False,
                        'error': f'Subscription canceled more than {self.config["reactivation_window_days"]} days ago'
                    }
            
            # Clear cancellation details
            subscription.canceled_at = None
            subscription.cancel_at_period_end = False
            
            # Set up new billing period
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            
            # Process reactivation event
            return self.process_lifecycle_event(
                subscription_id=subscription_id,
                event=LifecycleEvent.REACTIVATION_REQUESTED,
                metadata={
                    'payment_method_id': payment_method_id,
                    'restore_features': restore_features,
                    'reactivation_date': datetime.utcnow().isoformat(),
                    'new_billing_period_start': subscription.current_period_start.isoformat(),
                    'new_billing_period_end': subscription.current_period_end.isoformat()
                },
                user_id=user_id
            )
            
        except Exception as e:
            logger.error(f"Error reactivating subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # AUTOMATED LIFECYCLE PROCESSING
    # ============================================================================
    
    def process_automated_lifecycle_events(self) -> Dict[str, Any]:
        """Process automated lifecycle events for all subscriptions"""
        try:
            results = {
                'events_processed': 0,
                'subscriptions_updated': 0,
                'errors': []
            }
            
            # Process trial endings
            trial_results = self._process_trial_endings()
            results['events_processed'] += trial_results['events_processed']
            results['subscriptions_updated'] += trial_results['subscriptions_updated']
            results['errors'].extend(trial_results['errors'])
            
            # Process grace period endings
            grace_results = self._process_grace_period_endings()
            results['events_processed'] += grace_results['events_processed']
            results['subscriptions_updated'] += grace_results['subscriptions_updated']
            results['errors'].extend(grace_results['errors'])
            
            # Process scheduled cancellations
            cancel_results = self._process_scheduled_cancellations()
            results['events_processed'] += cancel_results['events_processed']
            results['subscriptions_updated'] += cancel_results['subscriptions_updated']
            results['errors'].extend(cancel_results['errors'])
            
            # Process expirations
            expiry_results = self._process_expirations()
            results['events_processed'] += expiry_results['events_processed']
            results['subscriptions_updated'] += expiry_results['subscriptions_updated']
            results['errors'].extend(expiry_results['errors'])
            
            logger.info(f"Automated lifecycle processing completed: {results['events_processed']} events processed")
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in automated lifecycle processing: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_trial_endings(self) -> Dict[str, Any]:
        """Process subscriptions with ending trials"""
        try:
            # Find subscriptions with trials ending soon
            trial_ending_threshold = datetime.utcnow() + timedelta(days=1)
            
            trial_ending_subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == 'trialing',
                    Subscription.trial_end <= trial_ending_threshold,
                    Subscription.trial_end > datetime.utcnow()
                )
            ).all()
            
            events_processed = 0
            subscriptions_updated = 0
            errors = []
            
            for subscription in trial_ending_subscriptions:
                try:
                    # Send trial ending notification
                    result = self.process_lifecycle_event(
                        subscription_id=subscription.id,
                        event=LifecycleEvent.TRIAL_ENDING,
                        metadata={
                            'trial_end': subscription.trial_end.isoformat(),
                            'days_remaining': (subscription.trial_end - datetime.utcnow()).days
                        }
                    )
                    
                    if result['success']:
                        events_processed += 1
                        subscriptions_updated += 1
                    else:
                        errors.append(f"Trial ending notification failed for subscription {subscription.id}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"Error processing trial ending for subscription {subscription.id}: {str(e)}")
            
            # Process expired trials
            expired_trials = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == 'trialing',
                    Subscription.trial_end <= datetime.utcnow()
                )
            ).all()
            
            for subscription in expired_trials:
                try:
                    result = self.process_lifecycle_event(
                        subscription_id=subscription.id,
                        event=LifecycleEvent.TRIAL_ENDED
                    )
                    
                    if result['success']:
                        events_processed += 1
                        subscriptions_updated += 1
                    else:
                        errors.append(f"Trial ended processing failed for subscription {subscription.id}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"Error processing expired trial for subscription {subscription.id}: {str(e)}")
            
            return {
                'events_processed': events_processed,
                'subscriptions_updated': subscriptions_updated,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error processing trial endings: {e}")
            return {
                'events_processed': 0,
                'subscriptions_updated': 0,
                'errors': [str(e)]
            }
    
    def _process_grace_period_endings(self) -> Dict[str, Any]:
        """Process subscriptions with ending grace periods"""
        try:
            # Find subscriptions with grace periods ending
            grace_period_threshold = datetime.utcnow() - timedelta(days=self.config['grace_period_days'])
            
            grace_period_subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == 'past_due',
                    Subscription.updated_at <= grace_period_threshold
                )
            ).all()
            
            events_processed = 0
            subscriptions_updated = 0
            errors = []
            
            for subscription in grace_period_subscriptions:
                try:
                    result = self.process_lifecycle_event(
                        subscription_id=subscription.id,
                        event=LifecycleEvent.GRACE_PERIOD_ENDED
                    )
                    
                    if result['success']:
                        events_processed += 1
                        subscriptions_updated += 1
                    else:
                        errors.append(f"Grace period ending failed for subscription {subscription.id}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"Error processing grace period ending for subscription {subscription.id}: {str(e)}")
            
            return {
                'events_processed': events_processed,
                'subscriptions_updated': subscriptions_updated,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error processing grace period endings: {e}")
            return {
                'events_processed': 0,
                'subscriptions_updated': 0,
                'errors': [str(e)]
            }
    
    def _process_scheduled_cancellations(self) -> Dict[str, Any]:
        """Process scheduled cancellations"""
        try:
            # Find subscriptions with scheduled cancellations
            scheduled_cancellations = self.db.query(Subscription).filter(
                and_(
                    Subscription.status == 'canceling',
                    Subscription.current_period_end <= datetime.utcnow()
                )
            ).all()
            
            events_processed = 0
            subscriptions_updated = 0
            errors = []
            
            for subscription in scheduled_cancellations:
                try:
                    result = self.process_lifecycle_event(
                        subscription_id=subscription.id,
                        event=LifecycleEvent.CANCELLATION_COMPLETED
                    )
                    
                    if result['success']:
                        events_processed += 1
                        subscriptions_updated += 1
                    else:
                        errors.append(f"Scheduled cancellation failed for subscription {subscription.id}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"Error processing scheduled cancellation for subscription {subscription.id}: {str(e)}")
            
            return {
                'events_processed': events_processed,
                'subscriptions_updated': subscriptions_updated,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error processing scheduled cancellations: {e}")
            return {
                'events_processed': 0,
                'subscriptions_updated': 0,
                'errors': [str(e)]
            }
    
    def _process_expirations(self) -> Dict[str, Any]:
        """Process expired subscriptions"""
        try:
            # Find expired subscriptions
            expired_subscriptions = self.db.query(Subscription).filter(
                and_(
                    Subscription.status.in_(['unpaid', 'suspended']),
                    Subscription.updated_at <= datetime.utcnow() - timedelta(days=self.config['auto_cancel_after_days'])
                )
            ).all()
            
            events_processed = 0
            subscriptions_updated = 0
            errors = []
            
            for subscription in expired_subscriptions:
                try:
                    result = self.process_lifecycle_event(
                        subscription_id=subscription.id,
                        event=LifecycleEvent.EXPIRATION
                    )
                    
                    if result['success']:
                        events_processed += 1
                        subscriptions_updated += 1
                    else:
                        errors.append(f"Expiration processing failed for subscription {subscription.id}: {result['error']}")
                        
                except Exception as e:
                    errors.append(f"Error processing expiration for subscription {subscription.id}: {str(e)}")
            
            return {
                'events_processed': events_processed,
                'subscriptions_updated': subscriptions_updated,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error processing expirations: {e}")
            return {
                'events_processed': 0,
                'subscriptions_updated': 0,
                'errors': [str(e)]
            }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _is_valid_transition(
        self,
        current_state: SubscriptionState,
        event: LifecycleEvent
    ) -> bool:
        """Check if a state transition is valid"""
        if current_state not in self.state_transitions:
            return False
        
        return event in self.state_transitions[current_state]
    
    def _get_available_transitions(
        self,
        current_state: SubscriptionState
    ) -> List[Dict[str, Any]]:
        """Get available transitions for a state"""
        if current_state not in self.state_transitions:
            return []
        
        transitions = []
        for event, new_state in self.state_transitions[current_state].items():
            transitions.append({
                'event': event.value,
                'new_state': new_state.value,
                'description': self._get_event_description(event)
            })
        
        return transitions
    
    def _get_event_description(self, event: LifecycleEvent) -> str:
        """Get human-readable description of an event"""
        descriptions = {
            LifecycleEvent.SUBSCRIPTION_CREATED: "Subscription created",
            LifecycleEvent.TRIAL_STARTED: "Trial period started",
            LifecycleEvent.TRIAL_CONVERTED: "Trial converted to paid",
            LifecycleEvent.TRIAL_ENDED: "Trial period ended",
            LifecycleEvent.PAYMENT_SUCCEEDED: "Payment succeeded",
            LifecycleEvent.PAYMENT_FAILED: "Payment failed",
            LifecycleEvent.CANCELLATION_REQUESTED: "Cancellation requested",
            LifecycleEvent.CANCELLATION_COMPLETED: "Cancellation completed",
            LifecycleEvent.REACTIVATION_REQUESTED: "Reactivation requested",
            LifecycleEvent.REACTIVATION_COMPLETED: "Reactivation completed"
        }
        
        return descriptions.get(event, event.value)
    
    def _get_lifecycle_history(self, subscription_id: int) -> List[Dict[str, Any]]:
        """Get lifecycle history for a subscription"""
        try:
            audit_logs = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.subscription_id == subscription_id,
                    AuditLog.event_type.in_([
                        AuditEventType.SUBSCRIPTION_CREATED,
                        AuditEventType.SUBSCRIPTION_UPDATED,
                        AuditEventType.SUBSCRIPTION_CANCELED,
                        AuditEventType.PAYMENT_SUCCEEDED,
                        AuditEventType.PAYMENT_FAILED
                    ])
                )
            ).order_by(AuditLog.event_timestamp.desc()).limit(20).all()
            
            history = []
            for log in audit_logs:
                history.append({
                    'timestamp': log.event_timestamp.isoformat(),
                    'event_type': log.event_type.value,
                    'description': log.event_description,
                    'metadata': log.metadata
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting lifecycle history: {e}")
            return []
    
    def _get_state_specific_info(
        self,
        subscription: Subscription,
        state: SubscriptionState
    ) -> Dict[str, Any]:
        """Get state-specific information for a subscription"""
        info = {
            'state': state.value,
            'status_description': self._get_state_description(state)
        }
        
        if state == SubscriptionState.TRIALING:
            info.update({
                'trial_start': subscription.trial_start.isoformat() if subscription.trial_start else None,
                'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
                'days_remaining': (subscription.trial_end - datetime.utcnow()).days if subscription.trial_end else None
            })
        elif state == SubscriptionState.PAST_DUE:
            info.update({
                'grace_period_end': (subscription.updated_at + timedelta(days=self.config['grace_period_days'])).isoformat(),
                'days_in_grace_period': (datetime.utcnow() - subscription.updated_at).days
            })
        elif state == SubscriptionState.CANCELING:
            info.update({
                'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'effective_cancel_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None
            })
        
        return info
    
    def _get_state_description(self, state: SubscriptionState) -> str:
        """Get human-readable description of a state"""
        descriptions = {
            SubscriptionState.DRAFT: "Draft subscription being created",
            SubscriptionState.PENDING_ACTIVATION: "Waiting for activation",
            SubscriptionState.TRIALING: "In free trial period",
            SubscriptionState.ACTIVE: "Active and billing",
            SubscriptionState.PAST_DUE: "Payment failed, in grace period",
            SubscriptionState.UNPAID: "Payment failed, access suspended",
            SubscriptionState.SUSPENDED: "Temporarily suspended",
            SubscriptionState.CANCELING: "Cancellation in progress",
            SubscriptionState.CANCELED: "Subscription canceled",
            SubscriptionState.REACTIVATING: "Reactivation in progress",
            SubscriptionState.ERROR: "System error state",
            SubscriptionState.EXPIRED: "Subscription expired"
        }
        
        return descriptions.get(state, state.value)
    
    def _update_state_specific_fields(
        self,
        subscription: Subscription,
        new_state: SubscriptionState,
        event: LifecycleEvent,
        metadata: Dict = None
    ):
        """Update subscription fields based on new state"""
        if new_state == SubscriptionState.ACTIVE:
            subscription.cancel_at_period_end = False
            subscription.canceled_at = None
        elif new_state == SubscriptionState.CANCELED:
            subscription.canceled_at = datetime.utcnow()
        elif new_state == SubscriptionState.EXPIRED:
            subscription.expired_at = datetime.utcnow()
    
    def _execute_pre_transition_hooks(
        self,
        subscription: Subscription,
        event: LifecycleEvent,
        current_state: SubscriptionState,
        new_state: SubscriptionState,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Execute pre-transition hooks"""
        try:
            if event not in self.lifecycle_hooks:
                return {'success': True, 'hooks_executed': 0}
            
            hooks_executed = 0
            errors = []
            
            for hook in self.lifecycle_hooks[event]:
                try:
                    hook(subscription, event, current_state, new_state, metadata)
                    hooks_executed += 1
                except Exception as e:
                    errors.append(f"Hook {hook.__name__} failed: {str(e)}")
            
            return {
                'success': len(errors) == 0,
                'hooks_executed': hooks_executed,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'hooks_executed': 0,
                'errors': [str(e)]
            }
    
    def _execute_post_transition_hooks(
        self,
        subscription: Subscription,
        event: LifecycleEvent,
        current_state: SubscriptionState,
        new_state: SubscriptionState,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Execute post-transition hooks"""
        # Similar to pre-transition hooks but executed after state change
        return {'success': True, 'hooks_executed': 0}
    
    def _log_state_transition(
        self,
        subscription: Subscription,
        old_status: str,
        new_status: str,
        event: LifecycleEvent,
        metadata: Dict = None,
        user_id: int = None
    ):
        """Log state transition"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                subscription_id=subscription.id,
                customer_id=subscription.customer_id,
                event_description=f"Subscription state changed from {old_status} to {new_status}",
                old_values={'status': old_status},
                new_values={'status': new_status},
                changed_fields=['status'],
                metadata={
                    'lifecycle_event': event.value,
                    'transition_metadata': metadata
                }
            )
            
            self.db.add(audit_log)
            
        except Exception as e:
            logger.error(f"Error logging state transition: {e}")
    
    # ============================================================================
    # LIFECYCLE HOOKS
    # ============================================================================
    
    def _hook_welcome_email(self, subscription, event, current_state, new_state, metadata):
        """Send welcome email for new subscriptions"""
        logger.info(f"Sending welcome email for subscription {subscription.id}")
        # Email sending logic would go here
    
    def _hook_initialize_usage_tracking(self, subscription, event, current_state, new_state, metadata):
        """Initialize usage tracking for new subscriptions"""
        logger.info(f"Initializing usage tracking for subscription {subscription.id}")
        # Usage tracking initialization logic would go here
    
    def _hook_create_audit_log(self, subscription, event, current_state, new_state, metadata):
        """Create audit log entry for lifecycle event"""
        logger.info(f"Creating audit log for {event.value} on subscription {subscription.id}")
        # Audit logging logic would go here
    
    def _hook_trial_welcome(self, subscription, event, current_state, new_state, metadata):
        """Send trial welcome email"""
        logger.info(f"Sending trial welcome email for subscription {subscription.id}")
        # Trial welcome email logic would go here
    
    def _hook_set_trial_period(self, subscription, event, current_state, new_state, metadata):
        """Set trial period details"""
        logger.info(f"Setting trial period for subscription {subscription.id}")
        # Trial period setup logic would go here
    
    def _hook_trial_ending_notification(self, subscription, event, current_state, new_state, metadata):
        """Send trial ending notification"""
        logger.info(f"Sending trial ending notification for subscription {subscription.id}")
        # Trial ending notification logic would go here
    
    def _hook_trial_conversion(self, subscription, event, current_state, new_state, metadata):
        """Handle trial conversion"""
        logger.info(f"Processing trial conversion for subscription {subscription.id}")
        # Trial conversion logic would go here
    
    def _hook_payment_failure_notification(self, subscription, event, current_state, new_state, metadata):
        """Send payment failure notification"""
        logger.info(f"Sending payment failure notification for subscription {subscription.id}")
        # Payment failure notification logic would go here
    
    def _hook_start_grace_period(self, subscription, event, current_state, new_state, metadata):
        """Start grace period"""
        logger.info(f"Starting grace period for subscription {subscription.id}")
        # Grace period start logic would go here
    
    def _hook_payment_success(self, subscription, event, current_state, new_state, metadata):
        """Handle successful payment"""
        logger.info(f"Processing successful payment for subscription {subscription.id}")
        # Payment success logic would go here
    
    def _hook_reset_grace_period(self, subscription, event, current_state, new_state, metadata):
        """Reset grace period"""
        logger.info(f"Resetting grace period for subscription {subscription.id}")
        # Grace period reset logic would go here
    
    def _hook_cancellation_request(self, subscription, event, current_state, new_state, metadata):
        """Handle cancellation request"""
        logger.info(f"Processing cancellation request for subscription {subscription.id}")
        # Cancellation request logic would go here
    
    def _hook_cancellation_complete(self, subscription, event, current_state, new_state, metadata):
        """Handle cancellation completion"""
        logger.info(f"Processing cancellation completion for subscription {subscription.id}")
        # Cancellation completion logic would go here
    
    def _hook_reactivation_request(self, subscription, event, current_state, new_state, metadata):
        """Handle reactivation request"""
        logger.info(f"Processing reactivation request for subscription {subscription.id}")
        # Reactivation request logic would go here
    
    def _hook_reactivation_complete(self, subscription, event, current_state, new_state, metadata):
        """Handle reactivation completion"""
        logger.info(f"Processing reactivation completion for subscription {subscription.id}")
        # Reactivation completion logic would go here 