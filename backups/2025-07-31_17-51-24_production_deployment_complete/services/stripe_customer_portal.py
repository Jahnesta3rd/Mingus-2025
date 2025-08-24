"""
Stripe Customer Portal Integration for MINGUS
Handles seamless handoff to Stripe for complex billing management
"""
import logging
import stripe
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.subscription import Customer, Subscription, PricingTier, BillingHistory
from ..models.payment_method import PaymentMethod
from ..models.audit_log import AuditLog, AuditEventType, AuditSeverity
from ..config.base import Config

logger = logging.getLogger(__name__)

class StripeCustomerPortal:
    """Stripe Customer Portal integration for complex billing management"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        self.stripe = stripe
        self.stripe.api_key = config.STRIPE_SECRET_KEY
        
        # Portal configuration
        self.portal_configuration = {
            'business_profile': {
                'headline': 'MINGUS - Financial Health & Career Management',
                'privacy_policy_url': 'https://mingus.com/privacy',
                'terms_of_service_url': 'https://mingus.com/terms',
                'support_url': 'https://mingus.com/support'
            },
            'features': {
                'customer_update': {
                    'allowed_updates': ['address', 'shipping', 'tax_id'],
                    'enabled': True
                },
                'invoice_history': {
                    'enabled': True
                },
                'payment_method_update': {
                    'enabled': True
                },
                'subscription_cancel': {
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
                    },
                    'enabled': True,
                    'mode': 'at_period_end',
                    'proration_behavior': 'create_prorations'
                },
                'subscription_pause': {
                    'enabled': True
                },
                'subscription_update': {
                    'default_allowed_updates': ['price', 'quantity', 'promotion_code'],
                    'enabled': True,
                    'products': None,  # Allow all products
                    'proration_behavior': 'create_prorations'
                }
            }
        }
    
    def create_customer_portal_session(
        self,
        customer_id: int,
        return_url: str = None,
        configuration_id: str = None
    ) -> Dict[str, Any]:
        """Create a Stripe Customer Portal session for seamless billing management"""
        try:
            # Get customer from database
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Check if customer has Stripe customer ID
            if not customer.stripe_customer_id:
                return {
                    'success': False,
                    'error': 'Customer does not have a Stripe account'
                }
            
            # Prepare session parameters
            session_params = {
                'customer': customer.stripe_customer_id,
                'return_url': return_url or f"{self.config.BASE_URL}/dashboard/billing",
                'configuration': configuration_id
            }
            
            # Create portal session
            portal_session = stripe.billing_portal.Session.create(**session_params)
            
            # Log portal session creation
            logger.info(f"Created Stripe portal session for customer {customer_id}: {portal_session.id}")
            
            return {
                'success': True,
                'portal_session': {
                    'id': portal_session.id,
                    'url': portal_session.url,
                    'created': portal_session.created,
                    'customer': portal_session.customer,
                    'return_url': portal_session.return_url,
                    'expires_at': portal_session.expires_at
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            return {
                'success': False,
                'error': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error creating portal session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_portal_configuration(
        self,
        configuration_name: str = "MINGUS Customer Portal",
        features: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a custom Stripe Customer Portal configuration"""
        try:
            # Use default configuration if none provided
            if not features:
                features = self.portal_configuration['features']
            
            # Prepare configuration parameters
            config_params = {
                'business_profile': self.portal_configuration['business_profile'],
                'features': features
            }
            
            # Create portal configuration
            portal_config = stripe.billing_portal.Configuration.create(
                name=configuration_name,
                **config_params
            )
            
            logger.info(f"Created Stripe portal configuration: {portal_config.id}")
            
            return {
                'success': True,
                'configuration': {
                    'id': portal_config.id,
                    'name': portal_config.name,
                    'business_profile': portal_config.business_profile,
                    'features': portal_config.features,
                    'is_default': portal_config.is_default,
                    'created': portal_config.created
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal configuration: {e}")
            return {
                'success': False,
                'error': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error creating portal configuration: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_portal_configurations(self) -> Dict[str, Any]:
        """Get all available portal configurations"""
        try:
            configurations = stripe.billing_portal.Configuration.list(limit=100)
            
            config_list = []
            for config in configurations.data:
                config_list.append({
                    'id': config.id,
                    'name': config.name,
                    'business_profile': config.business_profile,
                    'features': config.features,
                    'is_default': config.is_default,
                    'created': config.created
                })
            
            return {
                'success': True,
                'configurations': config_list,
                'total_count': len(config_list)
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting portal configurations: {e}")
            return {
                'success': False,
                'error': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error getting portal configurations: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_portal_configuration(
        self,
        configuration_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing portal configuration"""
        try:
            # Update portal configuration
            portal_config = stripe.billing_portal.Configuration.modify(
                configuration_id,
                **updates
            )
            
            logger.info(f"Updated Stripe portal configuration: {configuration_id}")
            
            return {
                'success': True,
                'configuration': {
                    'id': portal_config.id,
                    'name': portal_config.name,
                    'business_profile': portal_config.business_profile,
                    'features': portal_config.features,
                    'is_default': portal_config.is_default,
                    'created': portal_config.created
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating portal configuration: {e}")
            return {
                'success': False,
                'error': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error updating portal configuration: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_portal_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Stripe Customer Portal webhook events"""
        try:
            event_type = event_data.get('type')
            
            if event_type == 'customer.updated':
                return self._handle_customer_updated(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return self._handle_invoice_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return self._handle_invoice_payment_failed(event_data)
            elif event_type == 'customer.subscription.updated':
                return self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return self._handle_subscription_deleted(event_data)
            elif event_type == 'payment_method.attached':
                return self._handle_payment_method_attached(event_data)
            elif event_type == 'payment_method.detached':
                return self._handle_payment_method_detached(event_data)
            else:
                logger.info(f"Unhandled portal webhook event: {event_type}")
                return {
                    'success': True,
                    'message': f'Unhandled event type: {event_type}'
                }
                
        except Exception as e:
            logger.error(f"Error handling portal webhook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_customer_portal_access(
        self,
        customer_id: int,
        access_type: str = 'full'
    ) -> Dict[str, Any]:
        """Get customer portal access information and permissions"""
        try:
            # Get customer from database
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get customer's active subscription
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer.id,
                    Subscription.status == 'active'
                )
            ).first()
            
            # Determine portal access based on subscription and access type
            portal_access = {
                'customer_id': customer.id,
                'stripe_customer_id': customer.stripe_customer_id,
                'has_active_subscription': subscription is not None,
                'subscription_status': subscription.status if subscription else None,
                'access_type': access_type,
                'permissions': self._get_portal_permissions(customer, subscription, access_type),
                'portal_url': None,  # Will be generated when needed
                'session_expires_at': None
            }
            
            return {
                'success': True,
                'portal_access': portal_access
            }
            
        except Exception as e:
            logger.error(f"Error getting customer portal access: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_limited_portal_session(
        self,
        customer_id: int,
        allowed_features: List[str],
        return_url: str = None
    ) -> Dict[str, Any]:
        """Create a limited portal session with specific features only"""
        try:
            # Get customer from database
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Create limited configuration
            limited_config = self._create_limited_configuration(allowed_features)
            
            # Create portal session with limited configuration
            session_params = {
                'customer': customer.stripe_customer_id,
                'return_url': return_url or f"{self.config.BASE_URL}/dashboard/billing",
                'configuration': limited_config['id']
            }
            
            portal_session = stripe.billing_portal.Session.create(**session_params)
            
            # Clean up temporary configuration
            stripe.billing_portal.Configuration.delete(limited_config['id'])
            
            return {
                'success': True,
                'portal_session': {
                    'id': portal_session.id,
                    'url': portal_session.url,
                    'created': portal_session.created,
                    'customer': portal_session.customer,
                    'return_url': portal_session.return_url,
                    'expires_at': portal_session.expires_at,
                    'allowed_features': allowed_features
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating limited portal session: {e}")
            return {
                'success': False,
                'error': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error creating limited portal session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_portal_return(
        self,
        customer_id: str,
        session_id: str,
        action: str = None
    ) -> Dict[str, Any]:
        """Handle return from Stripe Customer Portal with data synchronization"""
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
            
            # Retrieve portal session to verify it's valid
            try:
                session = stripe.billing_portal.Session.retrieve(session_id)
                if session.customer != customer_id:
                    return {
                        'success': False,
                        'error': 'Session customer mismatch'
                    }
            except stripe.error.StripeError as e:
                logger.warning(f"Could not retrieve portal session {session_id}: {e}")
            
            # Synchronize data based on action
            sync_result = self._synchronize_portal_data(customer, action)
            
            # Log portal return event
            self._log_portal_return_event(customer.id, session_id, action, sync_result)
            
            return {
                'success': True,
                'message': 'Portal return handled successfully',
                'synchronized_data': sync_result,
                'redirect_url': self._get_redirect_url_for_action(action)
            }
            
        except Exception as e:
            logger.error(f"Error handling portal return: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _synchronize_portal_data(self, customer: Customer, action: str = None) -> Dict[str, Any]:
        """Synchronize data from Stripe Customer Portal"""
        try:
            sync_result = {
                'customer_updated': False,
                'subscription_changed': False,
                'payment_method_updated': False,
                'changes': []
            }
            
            # Always sync customer data
            customer_sync = self._sync_customer_data(customer)
            sync_result['customer_updated'] = customer_sync['success']
            sync_result['changes'].extend(customer_sync.get('changes', []))
            
            # Sync subscription data
            subscription_sync = self._sync_subscription_data(customer)
            sync_result['subscription_changed'] = subscription_sync['success']
            sync_result['changes'].extend(subscription_sync.get('changes', []))
            
            # Sync payment methods
            payment_sync = self._sync_payment_methods(customer)
            sync_result['payment_method_updated'] = payment_sync['success']
            sync_result['changes'].extend(payment_sync.get('changes', []))
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Error synchronizing portal data: {e}")
            return {
                'customer_updated': False,
                'subscription_changed': False,
                'payment_method_updated': False,
                'changes': [f"Sync error: {str(e)}"]
            }
    
    def _sync_customer_data(self, customer: Customer) -> Dict[str, Any]:
        """Synchronize customer data from Stripe"""
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
            logger.error(f"Error syncing customer data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _sync_subscription_data(self, customer: Customer) -> Dict[str, Any]:
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
            logger.error(f"Error syncing subscription data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _sync_payment_methods(self, customer: Customer) -> Dict[str, Any]:
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
            logger.error(f"Error syncing payment methods: {e}")
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
    
    def _log_portal_return_event(
        self,
        customer_id: int,
        session_id: str,
        action: str,
        sync_result: Dict[str, Any]
    ) -> None:
        """Log portal return event"""
        try:
            # Create audit log entry
            audit_log = AuditLog(
                customer_id=customer_id,
                event_type=AuditEventType.PORTAL_RETURN,
                event_description=f"Portal return for action: {action}",
                severity=AuditSeverity.INFO,
                metadata={
                    'session_id': session_id,
                    'action': action,
                    'sync_result': sync_result,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            logger.info(f"Portal return logged for customer {customer_id}, action: {action}")
            
        except Exception as e:
            logger.error(f"Error logging portal return event: {e}")
    
    def apply_custom_branding(
        self,
        configuration_id: str,
        branding: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom branding to portal configuration"""
        try:
            # Validate branding data
            if not branding:
                return {
                    'success': False,
                    'error': 'No branding data provided'
                }
            
            # Prepare branding configuration
            branding_config = {
                'business_profile': {
                    'headline': branding.get('company_name', 'MINGUS Financial Management'),
                    'privacy_policy_url': branding.get('privacy_policy_url', 'https://mingus.com/privacy'),
                    'terms_of_service_url': branding.get('terms_of_service_url', 'https://mingus.com/terms'),
                    'support_url': branding.get('support_url', 'https://mingus.com/support')
                }
            }
            
            # Update portal configuration with branding
            update_result = self.update_portal_configuration(
                configuration_id=configuration_id,
                updates=branding_config
            )
            
            if update_result['success']:
                logger.info(f"Applied custom branding to portal configuration: {configuration_id}")
            
            return update_result
            
        except Exception as e:
            logger.error(f"Error applying custom branding: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_portal_analytics(
        self,
        start_date: str = None,
        end_date: str = None,
        customer_id: str = None
    ) -> Dict[str, Any]:
        """Get analytics and insights for portal usage"""
        try:
            # Parse dates
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Get portal sessions from audit logs
            query = self.db.query(AuditLog).filter(
                AuditLog.event_type == AuditEventType.CUSTOMER_PORTAL_ACCESSED
            )
            
            if start_dt:
                query = query.filter(AuditLog.created_at >= start_dt)
            if end_dt:
                query = query.filter(AuditLog.created_at <= end_dt)
            if customer_id:
                query = query.filter(AuditLog.customer_id == customer_id)
            
            portal_sessions = query.all()
            
            # Calculate analytics
            total_sessions = len(portal_sessions)
            unique_customers = len(set(session.customer_id for session in portal_sessions))
            
            # Get return events
            return_query = self.db.query(AuditLog).filter(
                AuditLog.event_type == AuditEventType.PORTAL_RETURN
            )
            
            if start_dt:
                return_query = return_query.filter(AuditLog.created_at >= start_dt)
            if end_dt:
                return_query = return_query.filter(AuditLog.created_at <= end_dt)
            if customer_id:
                return_query = return_query.filter(AuditLog.customer_id == customer_id)
            
            return_events = return_query.all()
            return_rate = len(return_events) / total_sessions if total_sessions > 0 else 0
            
            # Analyze most used features
            feature_usage = {}
            for session in portal_sessions:
                if session.metadata and 'configuration' in session.metadata:
                    config = session.metadata['configuration']
                    if 'features' in config:
                        for feature, settings in config['features'].items():
                            if settings.get('enabled', False):
                                feature_usage[feature] = feature_usage.get(feature, 0) + 1
            
            most_used_features = sorted(
                feature_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            analytics = {
                'total_sessions': total_sessions,
                'unique_customers': unique_customers,
                'most_used_features': most_used_features,
                'session_duration_stats': {
                    'average_duration_minutes': 15,  # Placeholder
                    'median_duration_minutes': 12    # Placeholder
                },
                'return_rate': round(return_rate, 2),
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
            return {
                'success': True,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting portal analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods
    def _handle_customer_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.updated webhook event"""
        customer_data = event_data['data']['object']
        stripe_customer_id = customer_data['id']
        
        # Update local customer data
        customer = self.db.query(Customer).filter(
            Customer.stripe_customer_id == stripe_customer_id
        ).first()
        
        if customer:
            # Update customer information
            if 'email' in customer_data:
                customer.email = customer_data['email']
            if 'name' in customer_data:
                customer.name = customer_data['name']
            if 'address' in customer_data:
                customer.address = customer_data['address']
            
            self.db.commit()
            logger.info(f"Updated customer {customer.id} from portal")
        
        return {
            'success': True,
            'message': 'Customer updated successfully'
        }
    
    def _handle_invoice_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_succeeded webhook event"""
        invoice_data = event_data['data']['object']
        
        # Update local billing history
        billing_record = self.db.query(BillingHistory).filter(
            BillingHistory.stripe_invoice_id == invoice_data['id']
        ).first()
        
        if billing_record:
            billing_record.status = 'paid'
            billing_record.paid_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Updated billing record {billing_record.id} to paid")
        
        return {
            'success': True,
            'message': 'Payment succeeded'
        }
    
    def _handle_invoice_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_failed webhook event"""
        invoice_data = event_data['data']['object']
        
        # Update local billing history
        billing_record = self.db.query(BillingHistory).filter(
            BillingHistory.stripe_invoice_id == invoice_data['id']
        ).first()
        
        if billing_record:
            billing_record.status = 'failed'
            self.db.commit()
            logger.info(f"Updated billing record {billing_record.id} to failed")
        
        return {
            'success': True,
            'message': 'Payment failed'
        }
    
    def _handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.updated webhook event"""
        subscription_data = event_data['data']['object']
        
        # Update local subscription
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_data['id']
        ).first()
        
        if subscription:
            subscription.status = subscription_data['status']
            subscription.current_period_start = datetime.fromtimestamp(subscription_data['current_period_start'])
            subscription.current_period_end = datetime.fromtimestamp(subscription_data['current_period_end'])
            subscription.amount = subscription_data['items']['data'][0]['price']['unit_amount'] / 100
            
            self.db.commit()
            logger.info(f"Updated subscription {subscription.id} from portal")
        
        return {
            'success': True,
            'message': 'Subscription updated successfully'
        }
    
    def _handle_subscription_deleted(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.deleted webhook event"""
        subscription_data = event_data['data']['object']
        
        # Update local subscription
        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_data['id']
        ).first()
        
        if subscription:
            subscription.status = 'canceled'
            subscription.canceled_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Canceled subscription {subscription.id} from portal")
        
        return {
            'success': True,
            'message': 'Subscription canceled successfully'
        }
    
    def _handle_payment_method_attached(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment_method.attached webhook event"""
        payment_method_data = event_data['data']['object']
        
        logger.info(f"Payment method {payment_method_data['id']} attached to customer {payment_method_data['customer']}")
        
        return {
            'success': True,
            'message': 'Payment method attached'
        }
    
    def _handle_payment_method_detached(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment_method.detached webhook event"""
        payment_method_data = event_data['data']['object']
        
        logger.info(f"Payment method {payment_method_data['id']} detached from customer {payment_method_data['customer']}")
        
        return {
            'success': True,
            'message': 'Payment method detached'
        }
    
    def _get_portal_permissions(
        self,
        customer: Customer,
        subscription: Subscription,
        access_type: str
    ) -> Dict[str, bool]:
        """Get portal permissions based on customer and subscription"""
        permissions = {
            'can_update_profile': True,
            'can_view_invoices': True,
            'can_update_payment_method': True,
            'can_cancel_subscription': False,
            'can_pause_subscription': False,
            'can_update_subscription': False,
            'can_view_billing_history': True
        }
        
        # Adjust permissions based on subscription status
        if subscription and subscription.status == 'active':
            permissions.update({
                'can_cancel_subscription': True,
                'can_pause_subscription': True,
                'can_update_subscription': True
            })
        
        # Adjust permissions based on access type
        if access_type == 'limited':
            permissions.update({
                'can_cancel_subscription': False,
                'can_pause_subscription': False,
                'can_update_subscription': False
            })
        
        return permissions
    
    def _create_limited_configuration(self, allowed_features: List[str]) -> Dict[str, Any]:
        """Create a temporary limited portal configuration"""
        limited_features = {}
        
        for feature in allowed_features:
            if feature == 'customer_update':
                limited_features['customer_update'] = {
                    'allowed_updates': ['address', 'shipping'],
                    'enabled': True
                }
            elif feature == 'invoice_history':
                limited_features['invoice_history'] = {'enabled': True}
            elif feature == 'payment_method_update':
                limited_features['payment_method_update'] = {'enabled': True}
            elif feature == 'subscription_cancel':
                limited_features['subscription_cancel'] = {
                    'enabled': True,
                    'mode': 'at_period_end'
                }
            elif feature == 'subscription_pause':
                limited_features['subscription_pause'] = {'enabled': True}
            elif feature == 'subscription_update':
                limited_features['subscription_update'] = {
                    'enabled': True,
                    'default_allowed_updates': ['quantity']
                }
        
        # Create temporary configuration
        config = stripe.billing_portal.Configuration.create(
            name="Temporary Limited Configuration",
            business_profile=self.portal_configuration['business_profile'],
            features=limited_features
        )
        
        return {
            'id': config.id,
            'features': limited_features
        }
    
    def _calculate_start_date(self, end_date: datetime, date_range: str) -> datetime:
        """Calculate start date based on date range string"""
        if date_range == '7d':
            return end_date - timedelta(days=7)
        elif date_range == '30d':
            return end_date - timedelta(days=30)
        elif date_range == '90d':
            return end_date - timedelta(days=90)
        elif date_range == '1y':
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=30)
    
    def _calculate_average_session_duration(self, sessions: List[Any]) -> float:
        """Calculate average portal session duration"""
        # This would require tracking session start/end times
        # For now, return estimated duration
        return 5.5  # minutes
    
    def _analyze_feature_usage(self, sessions: List[Any]) -> Dict[str, int]:
        """Analyze which portal features are most used"""
        # This would require detailed session analytics
        # For now, return example data
        return {
            'payment_method_update': 45,
            'invoice_history': 38,
            'subscription_update': 22,
            'customer_update': 15,
            'subscription_cancel': 8,
            'subscription_pause': 3
        }
    
    def _get_customer_satisfaction_metrics(self) -> Dict[str, Any]:
        """Get customer satisfaction metrics for portal usage"""
        # This would integrate with customer feedback system
        # For now, return example data
        return {
            'overall_satisfaction': 4.2,
            'ease_of_use': 4.1,
            'feature_completeness': 3.9,
            'support_quality': 4.3,
            'response_time': 4.0
        }
    
    def _get_common_portal_actions(self, sessions: List[Any]) -> List[Dict[str, Any]]:
        """Get most common actions taken in portal"""
        # This would analyze actual session data
        # For now, return example data
        return [
            {'action': 'update_payment_method', 'count': 45, 'percentage': 35.7},
            {'action': 'view_invoices', 'count': 38, 'percentage': 30.2},
            {'action': 'update_subscription', 'count': 22, 'percentage': 17.5},
            {'action': 'update_profile', 'count': 15, 'percentage': 11.9},
            {'action': 'cancel_subscription', 'count': 6, 'percentage': 4.8}
        ] 