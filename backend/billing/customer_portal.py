"""
MINGUS Customer Portal - Comprehensive Billing Dashboard and Self-Service
Provides complete subscription management, billing history, and account controls
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import json
import stripe
from flask import jsonify, request, session

from ..models.subscription import (
    Customer, Subscription, PricingTier, PaymentMethod, BillingHistory, 
    FeatureUsage, AuditLog, AuditEventType, AuditSeverity, BillingDispute
)
from ..models.user import User
from ..config.billing_config import BillingConfig

logger = logging.getLogger(__name__)

class CustomerPortal:
    """Comprehensive customer portal for subscription and billing management"""
    
    def __init__(self, db_session: Session, config: BillingConfig):
        self.db = db_session
        self.config = config
        self.stripe = stripe
        self.stripe.api_key = config.STRIPE_SECRET_KEY
        
        # Portal configuration
        self.portal_config = {
            'features': {
                'subscription_management': True,
                'billing_history': True,
                'payment_methods': True,
                'usage_tracking': True,
                'upgrade_downgrade': True,
                'invoice_download': True,
                'support_requests': True,
                'account_settings': True
            },
            'branding': {
                'company_name': 'MINGUS',
                'logo_url': '/static/images/mingus-logo.png',
                'primary_color': '#2563eb',
                'secondary_color': '#1e40af'
            },
            'limits': {
                'max_payment_methods': 3,
                'max_support_requests': 5,
                'invoice_retention_days': 365
            }
        }
    
    def get_customer_dashboard(self, customer_id: int) -> Dict[str, Any]:
        """Get comprehensive customer dashboard data"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get active subscription
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status.in_(['active', 'past_due'])
                )
            ).first()
            
            # Get billing history
            billing_history = self._get_billing_history(customer_id)
            
            # Get usage data
            usage_data = self._get_usage_data(subscription.id if subscription else None)
            
            # Get payment methods
            payment_methods = self._get_payment_methods(customer_id)
            
            # Get recent activity
            recent_activity = self._get_recent_activity(customer_id)
            
            dashboard_data = {
                'customer_info': {
                    'id': customer.id,
                    'name': customer.name,
                    'email': customer.email,
                    'created_at': customer.created_at.isoformat() if customer.created_at else None,
                    'status': 'active' if subscription else 'inactive'
                },
                'subscription': self._format_subscription_data(subscription) if subscription else None,
                'billing_summary': {
                    'total_billed': billing_history.get('total_billed', 0),
                    'total_paid': billing_history.get('total_paid', 0),
                    'outstanding_balance': billing_history.get('outstanding_balance', 0),
                    'next_billing_date': subscription.current_period_end.isoformat() if subscription else None,
                    'billing_cycle': subscription.billing_cycle if subscription else None
                },
                'usage_summary': usage_data,
                'payment_methods': payment_methods,
                'recent_activity': recent_activity,
                'quick_actions': self._get_quick_actions(customer_id, subscription),
                'notifications': self._get_notifications(customer_id, subscription)
            }
            
            return {
                'success': True,
                'dashboard': dashboard_data
            }
            
        except Exception as e:
            logger.error(f"Error getting customer dashboard: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_subscription_management(self, customer_id: int) -> Dict[str, Any]:
        """Get subscription management interface"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get current subscription
            current_subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status.in_(['active', 'past_due', 'canceled'])
                )
            ).order_by(desc(Subscription.created_at)).first()
            
            # Get available pricing tiers
            pricing_tiers = self._get_available_pricing_tiers()
            
            # Get upgrade/downgrade options
            upgrade_options = self._get_upgrade_options(current_subscription) if current_subscription else []
            downgrade_options = self._get_downgrade_options(current_subscription) if current_subscription else []
            
            # Get cancellation options
            cancellation_options = self._get_cancellation_options(current_subscription) if current_subscription else {}
            
            management_data = {
                'current_subscription': self._format_subscription_data(current_subscription) if current_subscription else None,
                'available_tiers': pricing_tiers,
                'upgrade_options': upgrade_options,
                'downgrade_options': downgrade_options,
                'cancellation_options': cancellation_options,
                'subscription_actions': self._get_subscription_actions(current_subscription)
            }
            
            return {
                'success': True,
                'subscription_management': management_data
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription management: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_billing_history(self, customer_id: int, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get detailed billing history with pagination"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get billing history with pagination
            offset = (page - 1) * per_page
            billing_records = self.db.query(BillingHistory).filter(
                BillingHistory.customer_id == customer_id
            ).order_by(desc(BillingHistory.created_at)).offset(offset).limit(per_page).all()
            
            # Get total count
            total_count = self.db.query(BillingHistory).filter(
                BillingHistory.customer_id == customer_id
            ).count()
            
            # Format billing records
            formatted_records = []
            for record in billing_records:
                formatted_records.append({
                    'id': record.id,
                    'invoice_number': record.invoice_number,
                    'amount': record.amount,
                    'currency': record.currency,
                    'status': record.status,
                    'description': record.description,
                    'created_at': record.created_at.isoformat() if record.created_at else None,
                    'due_date': record.due_date.isoformat() if record.due_date else None,
                    'paid_at': record.paid_at.isoformat() if record.paid_at else None,
                    'stripe_invoice_id': record.stripe_invoice_id,
                    'download_url': f'/api/billing/invoice/{record.id}/download' if record.stripe_invoice_id else None
                })
            
            # Calculate pagination info
            total_pages = (total_count + per_page - 1) // per_page
            
            billing_data = {
                'records': formatted_records,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'summary': {
                    'total_billed': sum(r.amount for r in billing_records if r.amount),
                    'total_paid': sum(r.amount for r in billing_records if r.status == 'paid' and r.amount),
                    'outstanding': sum(r.amount for r in billing_records if r.status == 'unpaid' and r.amount)
                }
            }
            
            return {
                'success': True,
                'billing_history': billing_data
            }
            
        except Exception as e:
            logger.error(f"Error getting billing history: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_payment_methods(self, customer_id: int) -> Dict[str, Any]:
        """Get customer payment methods"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get payment methods from database
            payment_methods = self.db.query(PaymentMethod).filter(
                PaymentMethod.customer_id == customer_id
            ).all()
            
            # Get payment methods from Stripe
            stripe_payment_methods = []
            if customer.stripe_customer_id:
                try:
                    stripe_payment_methods = self.stripe.PaymentMethod.list(
                        customer=customer.stripe_customer_id,
                        type='card'
                    ).data
                except Exception as e:
                    logger.error(f"Error fetching Stripe payment methods: {e}")
            
            # Format payment methods
            formatted_methods = []
            for method in payment_methods:
                formatted_methods.append({
                    'id': method.id,
                    'stripe_payment_method_id': method.stripe_payment_method_id,
                    'type': method.payment_type,
                    'last4': method.last4,
                    'brand': method.brand,
                    'exp_month': method.exp_month,
                    'exp_year': method.exp_year,
                    'is_default': method.is_default,
                    'created_at': method.created_at.isoformat() if method.created_at else None
                })
            
            payment_data = {
                'payment_methods': formatted_methods,
                'stripe_payment_methods': stripe_payment_methods,
                'can_add_methods': len(formatted_methods) < self.portal_config['limits']['max_payment_methods'],
                'max_methods': self.portal_config['limits']['max_payment_methods']
            }
            
            return {
                'success': True,
                'payment_methods': payment_data
            }
            
        except Exception as e:
            logger.error(f"Error getting payment methods: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_usage_analytics(self, customer_id: int, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get usage analytics and insights"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get customer's subscriptions
            subscriptions = self.db.query(Subscription).filter(
                Subscription.customer_id == customer_id
            ).all()
            
            if not subscriptions:
                return {
                    'success': True,
                    'usage_analytics': {
                        'subscriptions': [],
                        'usage_summary': {},
                        'trends': {},
                        'recommendations': []
                    }
                }
            
            # Get usage data for all subscriptions
            usage_data = []
            for subscription in subscriptions:
                subscription_usage = self._get_subscription_usage_data(subscription.id, date_range)
                usage_data.append({
                    'subscription_id': subscription.id,
                    'tier': subscription.pricing_tier.tier_type,
                    'usage': subscription_usage
                })
            
            # Calculate overall usage summary
            usage_summary = self._calculate_usage_summary(usage_data)
            
            # Get usage trends
            usage_trends = self._get_usage_trends(customer_id, date_range)
            
            # Get recommendations
            recommendations = self._get_usage_recommendations(usage_data)
            
            analytics_data = {
                'subscriptions': usage_data,
                'usage_summary': usage_summary,
                'trends': usage_trends,
                'recommendations': recommendations,
                'date_range': {
                    'start': date_range[0].isoformat() if date_range else None,
                    'end': date_range[1].isoformat() if date_range else None
                }
            }
            
            return {
                'success': True,
                'usage_analytics': analytics_data
            }
            
        except Exception as e:
            logger.error(f"Error getting usage analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_payment_method(self, customer_id: int, payment_method_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update payment method information"""
        try:
            payment_method = self.db.query(PaymentMethod).filter(
                and_(
                    PaymentMethod.id == payment_method_id,
                    PaymentMethod.customer_id == customer_id
                )
            ).first()
            
            if not payment_method:
                return {
                    'success': False,
                    'error': 'Payment method not found'
                }
            
            # Update payment method in Stripe
            if payment_method.stripe_payment_method_id:
                try:
                    stripe_updates = {}
                    if 'exp_month' in updates:
                        stripe_updates['exp_month'] = updates['exp_month']
                    if 'exp_year' in updates:
                        stripe_updates['exp_year'] = updates['exp_year']
                    
                    if stripe_updates:
                        self.stripe.PaymentMethod.modify(
                            payment_method.stripe_payment_method_id,
                            **stripe_updates
                        )
                except Exception as e:
                    logger.error(f"Error updating Stripe payment method: {e}")
                    return {
                        'success': False,
                        'error': 'Failed to update payment method in Stripe'
                    }
            
            # Update local database
            for key, value in updates.items():
                if hasattr(payment_method, key):
                    setattr(payment_method, key, value)
            
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                customer_id,
                AuditEventType.PAYMENT_METHOD_UPDATED,
                AuditSeverity.INFO,
                f'Payment method {payment_method_id} updated'
            )
            
            return {
                'success': True,
                'message': 'Payment method updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating payment method: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_default_payment_method(self, customer_id: int, payment_method_id: int) -> Dict[str, Any]:
        """Set default payment method"""
        try:
            # Get customer
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get payment method
            payment_method = self.db.query(PaymentMethod).filter(
                and_(
                    PaymentMethod.id == payment_method_id,
                    PaymentMethod.customer_id == customer_id
                )
            ).first()
            
            if not payment_method:
                return {
                    'success': False,
                    'error': 'Payment method not found'
                }
            
            # Update Stripe customer default payment method
            if customer.stripe_customer_id and payment_method.stripe_payment_method_id:
                try:
                    self.stripe.Customer.modify(
                        customer.stripe_customer_id,
                        invoice_settings={
                            'default_payment_method': payment_method.stripe_payment_method_id
                        }
                    )
                except Exception as e:
                    logger.error(f"Error updating Stripe customer default payment method: {e}")
                    return {
                        'success': False,
                        'error': 'Failed to update default payment method in Stripe'
                    }
            
            # Update local database
            # Remove default from all other payment methods
            self.db.query(PaymentMethod).filter(
                PaymentMethod.customer_id == customer_id
            ).update({'is_default': False})
            
            # Set new default
            payment_method.is_default = True
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                customer_id,
                AuditEventType.PAYMENT_METHOD_UPDATED,
                AuditSeverity.INFO,
                f'Default payment method set to {payment_method_id}'
            )
            
            return {
                'success': True,
                'message': 'Default payment method updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error setting default payment method: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_payment_method(self, customer_id: int, payment_method_id: int) -> Dict[str, Any]:
        """Remove payment method"""
        try:
            payment_method = self.db.query(PaymentMethod).filter(
                and_(
                    PaymentMethod.id == payment_method_id,
                    PaymentMethod.customer_id == customer_id
                )
            ).first()
            
            if not payment_method:
                return {
                    'success': False,
                    'error': 'Payment method not found'
                }
            
            # Check if it's the default payment method
            if payment_method.is_default:
                return {
                    'success': False,
                    'error': 'Cannot remove default payment method. Set another as default first.'
                }
            
            # Remove from Stripe
            if payment_method.stripe_payment_method_id:
                try:
                    self.stripe.PaymentMethod.detach(payment_method.stripe_payment_method_id)
                except Exception as e:
                    logger.error(f"Error removing Stripe payment method: {e}")
            
            # Remove from local database
            self.db.delete(payment_method)
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                customer_id,
                AuditEventType.PAYMENT_METHOD_REMOVED,
                AuditSeverity.INFO,
                f'Payment method {payment_method_id} removed'
            )
            
            return {
                'success': True,
                'message': 'Payment method removed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error removing payment method: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_invoice(self, customer_id: int, invoice_id: int) -> Dict[str, Any]:
        """Download invoice PDF"""
        try:
            # Verify customer owns this invoice
            billing_record = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.id == invoice_id,
                    BillingHistory.customer_id == customer_id
                )
            ).first()
            
            if not billing_record:
                return {
                    'success': False,
                    'error': 'Invoice not found'
                }
            
            if not billing_record.stripe_invoice_id:
                return {
                    'success': False,
                    'error': 'Invoice not available for download'
                }
            
            # Get invoice from Stripe
            try:
                invoice = self.stripe.Invoice.retrieve(billing_record.stripe_invoice_id)
                invoice_pdf = self.stripe.Invoice.retrieve_pdf(billing_record.stripe_invoice_id)
                
                return {
                    'success': True,
                    'invoice_data': {
                        'id': billing_record.id,
                        'invoice_number': billing_record.invoice_number,
                        'amount': billing_record.amount,
                        'currency': billing_record.currency,
                        'status': billing_record.status,
                        'created_at': billing_record.created_at.isoformat() if billing_record.created_at else None,
                        'pdf_url': invoice_pdf,
                        'stripe_invoice_id': billing_record.stripe_invoice_id
                    }
                }
                
            except Exception as e:
                logger.error(f"Error retrieving Stripe invoice: {e}")
                return {
                    'success': False,
                    'error': 'Failed to retrieve invoice from Stripe'
                }
            
        except Exception as e:
            logger.error(f"Error downloading invoice: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_support_request(self, customer_id: int, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create support request"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Check support request limits
            recent_requests = self.db.query(BillingDispute).filter(
                and_(
                    BillingDispute.customer_id == customer_id,
                    BillingDispute.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).count()
            
            if recent_requests >= self.portal_config['limits']['max_support_requests']:
                return {
                    'success': False,
                    'error': 'Support request limit reached for this month'
                }
            
            # Create support request
            support_request = BillingDispute(
                customer_id=customer_id,
                dispute_type='support_request',
                subject=request_data.get('subject', ''),
                description=request_data.get('description', ''),
                priority=request_data.get('priority', 'medium'),
                status='open'
            )
            
            self.db.add(support_request)
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                customer_id,
                AuditEventType.SUPPORT_REQUEST_CREATED,
                AuditSeverity.INFO,
                f'Support request created: {support_request.subject}'
            )
            
            return {
                'success': True,
                'support_request': {
                    'id': support_request.id,
                    'subject': support_request.subject,
                    'status': support_request.status,
                    'priority': support_request.priority,
                    'created_at': support_request.created_at.isoformat() if support_request.created_at else None
                },
                'message': 'Support request created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating support request: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_settings(self, customer_id: int) -> Dict[str, Any]:
        """Get account settings and preferences"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get user preferences
            user = self.db.query(User).filter(User.id == customer.user_id).first()
            
            settings_data = {
                'customer_info': {
                    'name': customer.name,
                    'email': customer.email,
                    'phone': customer.phone,
                    'address': customer.address
                },
                'billing_preferences': {
                    'billing_cycle': 'monthly',  # Default, could be stored in preferences
                    'invoice_delivery': 'email',
                    'payment_reminders': True,
                    'usage_alerts': True
                },
                'notification_settings': {
                    'email_notifications': True,
                    'billing_alerts': True,
                    'usage_alerts': True,
                    'security_alerts': True
                },
                'security_settings': {
                    'two_factor_enabled': False,  # Could be implemented
                    'session_timeout': 30,  # minutes
                    'login_history': []  # Could be implemented
                }
            }
            
            return {
                'success': True,
                'account_settings': settings_data
            }
            
        except Exception as e:
            logger.error(f"Error getting account settings: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_account_settings(self, customer_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update account settings"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Update customer information
            if 'customer_info' in updates:
                customer_info = updates['customer_info']
                if 'name' in customer_info:
                    customer.name = customer_info['name']
                if 'email' in customer_info:
                    customer.email = customer_info['email']
                if 'phone' in customer_info:
                    customer.phone = customer_info['phone']
                if 'address' in customer_info:
                    customer.address = customer_info['address']
            
            # Update Stripe customer if needed
            if customer.stripe_customer_id:
                try:
                    stripe_updates = {}
                    if 'name' in updates.get('customer_info', {}):
                        stripe_updates['name'] = updates['customer_info']['name']
                    if 'email' in updates.get('customer_info', {}):
                        stripe_updates['email'] = updates['customer_info']['email']
                    
                    if stripe_updates:
                        self.stripe.Customer.modify(
                            customer.stripe_customer_id,
                            **stripe_updates
                        )
                except Exception as e:
                    logger.error(f"Error updating Stripe customer: {e}")
            
            self.db.commit()
            
            # Log audit event
            self._log_audit_event(
                customer_id,
                AuditEventType.ACCOUNT_UPDATED,
                AuditSeverity.INFO,
                'Account settings updated'
            )
            
            return {
                'success': True,
                'message': 'Account settings updated successfully'
            }
            
        except Exception as e:
            logger.error(f"Error updating account settings: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_current_subscription_status(self, customer_id: int) -> Dict[str, Any]:
        """Get current subscription status and detailed information"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get active subscription
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status.in_(['active', 'past_due', 'canceled'])
                )
            ).order_by(desc(Subscription.created_at)).first()
            
            if not subscription:
                return {
                    'success': True,
                    'subscription_status': {
                        'has_subscription': False,
                        'status': 'no_subscription',
                        'message': 'No active subscription found'
                    }
                }
            
            # Get usage data
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            usage_record = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.subscription_id == subscription.id,
                    FeatureUsage.usage_month == current_month,
                    FeatureUsage.usage_year == current_year
                )
            ).first()
            
            # Calculate usage percentages
            usage_data = {}
            if usage_record:
                tier = subscription.pricing_tier
                usage_data = {
                    'health_checkins': {
                        'used': usage_record.health_checkins_used or 0,
                        'limit': tier.max_health_checkins_per_month,
                        'percentage': self._calculate_usage_percentage(
                            usage_record.health_checkins_used or 0,
                            tier.max_health_checkins_per_month
                        )
                    },
                    'financial_reports': {
                        'used': usage_record.financial_reports_used or 0,
                        'limit': tier.max_financial_reports_per_month,
                        'percentage': self._calculate_usage_percentage(
                            usage_record.financial_reports_used or 0,
                            tier.max_financial_reports_per_month
                        )
                    },
                    'ai_insights': {
                        'used': usage_record.ai_insights_used or 0,
                        'limit': tier.max_ai_insights_per_month,
                        'percentage': self._calculate_usage_percentage(
                            usage_record.ai_insights_used or 0,
                            tier.max_ai_insights_per_month
                        )
                    },
                    'custom_reports': {
                        'used': usage_record.custom_reports_used or 0,
                        'limit': tier.max_custom_reports_per_month,
                        'percentage': self._calculate_usage_percentage(
                            usage_record.custom_reports_used or 0,
                            tier.max_custom_reports_per_month
                        )
                    }
                }
            
            # Get next billing information
            next_billing = None
            if subscription.current_period_end:
                days_until_billing = (subscription.current_period_end - datetime.utcnow()).days
                next_billing = {
                    'date': subscription.current_period_end.isoformat(),
                    'days_remaining': max(0, days_until_billing),
                    'amount': subscription.amount,
                    'currency': subscription.currency
                }
            
            status_data = {
                'has_subscription': True,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'tier': {
                    'name': subscription.pricing_tier.name,
                    'type': subscription.pricing_tier.tier_type,
                    'description': subscription.pricing_tier.description
                },
                'billing': {
                    'amount': subscription.amount,
                    'currency': subscription.currency,
                    'cycle': subscription.billing_cycle,
                    'next_billing': next_billing
                },
                'usage': usage_data,
                'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
                'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
                'status_message': self._get_status_message(subscription.status),
                'actions_available': self._get_available_actions(subscription)
            }
            
            return {
                'success': True,
                'subscription_status': status_data
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def manage_payment_methods(self, customer_id: int, action: str, payment_method_id: int = None, payment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Comprehensive payment method management"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            if action == 'list':
                return self.get_payment_methods(customer_id)
            
            elif action == 'add':
                return self._add_payment_method(customer_id, payment_data)
            
            elif action == 'update':
                if not payment_method_id:
                    return {
                        'success': False,
                        'error': 'Payment method ID required for update'
                    }
                return self.update_payment_method(customer_id, payment_method_id, payment_data or {})
            
            elif action == 'set_default':
                if not payment_method_id:
                    return {
                        'success': False,
                        'error': 'Payment method ID required for set default'
                    }
                return self.set_default_payment_method(customer_id, payment_method_id)
            
            elif action == 'remove':
                if not payment_method_id:
                    return {
                        'success': False,
                        'error': 'Payment method ID required for removal'
                    }
                return self.remove_payment_method(customer_id, payment_method_id)
            
            else:
                return {
                    'success': False,
                    'error': f'Invalid action: {action}'
                }
                
        except Exception as e:
            logger.error(f"Error managing payment methods: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_billing_history_with_downloads(self, customer_id: int, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get billing history with download capabilities"""
        try:
            # Get basic billing history
            history_result = self.get_billing_history(customer_id, page, per_page)
            
            if not history_result['success']:
                return history_result
            
            history_data = history_result['billing_history']
            
            # Enhance records with download information
            for record in history_data['records']:
                if record['stripe_invoice_id']:
                    record['download_available'] = True
                    record['download_url'] = f'/api/portal/invoice/{record["id"]}/download'
                else:
                    record['download_available'] = False
                    record['download_url'] = None
            
            # Add summary statistics
            history_data['summary'] = {
                'total_invoices': history_data['pagination']['total_count'],
                'paid_invoices': len([r for r in history_data['records'] if r['status'] == 'paid']),
                'unpaid_invoices': len([r for r in history_data['records'] if r['status'] == 'unpaid']),
                'downloadable_invoices': len([r for r in history_data['records'] if r['download_available']])
            }
            
            return {
                'success': True,
                'billing_history': history_data
            }
            
        except Exception as e:
            logger.error(f"Error getting billing history with downloads: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_usage_tracking_and_limits(self, customer_id: int) -> Dict[str, Any]:
        """Get comprehensive usage tracking and limits display"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get active subscription
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status.in_(['active', 'past_due'])
                )
            ).first()
            
            if not subscription:
                return {
                    'success': True,
                    'usage_tracking': {
                        'has_subscription': False,
                        'message': 'No active subscription for usage tracking'
                    }
                }
            
            # Get current month usage
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            usage_record = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.subscription_id == subscription.id,
                    FeatureUsage.usage_month == current_month,
                    FeatureUsage.usage_year == current_year
                )
            ).first()
            
            # Get tier limits
            tier = subscription.pricing_tier
            tier_limits = {
                'health_checkins': tier.max_health_checkins_per_month,
                'financial_reports': tier.max_financial_reports_per_month,
                'ai_insights': tier.max_ai_insights_per_month,
                'custom_reports': tier.max_custom_reports_per_month,
                'team_members': tier.max_team_members,
                'api_calls_per_hour': tier.max_api_calls_per_hour
            }
            
            # Calculate usage data
            current_usage = {
                'health_checkins': usage_record.health_checkins_used or 0 if usage_record else 0,
                'financial_reports': usage_record.financial_reports_used or 0 if usage_record else 0,
                'ai_insights': usage_record.ai_insights_used or 0 if usage_record else 0,
                'custom_reports': usage_record.custom_reports_used or 0 if usage_record else 0,
                'team_members': usage_record.team_members_used or 0 if usage_record else 0,
                'support_requests': usage_record.support_requests_used or 0 if usage_record else 0,
                'career_risk_management': usage_record.career_risk_management_used or 0 if usage_record else 0,
                'dedicated_account_manager': usage_record.dedicated_account_manager_used or 0 if usage_record else 0
            }
            
            # Calculate usage percentages and status
            usage_analysis = {}
            for feature, used in current_usage.items():
                limit = tier_limits.get(feature, -1)  # -1 means unlimited
                if limit == -1:
                    percentage = 0
                    status = 'unlimited'
                else:
                    percentage = self._calculate_usage_percentage(used, limit)
                    if percentage >= 100:
                        status = 'limit_reached'
                    elif percentage >= 80:
                        status = 'approaching_limit'
                    else:
                        status = 'normal'
                
                usage_analysis[feature] = {
                    'used': used,
                    'limit': limit,
                    'percentage': percentage,
                    'status': status,
                    'remaining': max(0, limit - used) if limit != -1 else -1
                }
            
            # Get usage trends (last 3 months)
            usage_trends = self._get_usage_trends_for_display(subscription.id)
            
            # Get upgrade recommendations
            upgrade_recommendations = self._get_usage_based_upgrade_recommendations(usage_analysis)
            
            usage_data = {
                'has_subscription': True,
                'subscription_id': subscription.id,
                'tier': {
                    'name': tier.name,
                    'type': tier.tier_type,
                    'description': tier.description
                },
                'current_usage': current_usage,
                'tier_limits': tier_limits,
                'usage_analysis': usage_analysis,
                'usage_trends': usage_trends,
                'upgrade_recommendations': upgrade_recommendations,
                'usage_period': {
                    'month': current_month,
                    'year': current_year,
                    'period_start': datetime(current_year, current_month, 1).isoformat(),
                    'period_end': (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).isoformat()
                }
            }
            
            return {
                'success': True,
                'usage_tracking': usage_data
            }
            
        except Exception as e:
            logger.error(f"Error getting usage tracking: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_subscription_upgrade_downgrade_options(self, customer_id: int) -> Dict[str, Any]:
        """Get detailed upgrade and downgrade options"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get current subscription
            current_subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status.in_(['active', 'past_due'])
                )
            ).first()
            
            if not current_subscription:
                return {
                    'success': True,
                    'upgrade_downgrade_options': {
                        'has_subscription': False,
                        'message': 'No active subscription to upgrade or downgrade'
                    }
                }
            
            # Get all pricing tiers
            all_tiers = self.db.query(PricingTier).order_by(PricingTier.monthly_price).all()
            
            # Find current tier index
            current_tier_index = None
            for i, tier in enumerate(all_tiers):
                if tier.id == current_subscription.pricing_tier_id:
                    current_tier_index = i
                    break
            
            # Generate upgrade options
            upgrade_options = []
            if current_tier_index is not None:
                for i in range(current_tier_index + 1, len(all_tiers)):
                    tier = all_tiers[i]
                    price_difference = tier.monthly_price - current_subscription.amount
                    
                    upgrade_options.append({
                        'tier_id': tier.id,
                        'tier_name': tier.name,
                        'tier_type': tier.tier_type,
                        'current_price': current_subscription.amount,
                        'new_price': tier.monthly_price,
                        'price_difference': price_difference,
                        'price_difference_formatted': f"+${price_difference:.2f}/month",
                        'benefits': self._get_tier_benefits(tier),
                        'feature_comparison': self._get_feature_comparison(current_subscription.pricing_tier, tier),
                        'upgrade_url': f'/api/portal/subscription/{current_subscription.id}/upgrade/{tier.id}',
                        'recommended': self._is_upgrade_recommended(tier, current_subscription)
                    })
            
            # Generate downgrade options
            downgrade_options = []
            if current_tier_index is not None:
                for i in range(current_tier_index - 1, -1, -1):
                    tier = all_tiers[i]
                    price_difference = tier.monthly_price - current_subscription.amount
                    
                    downgrade_options.append({
                        'tier_id': tier.id,
                        'tier_name': tier.name,
                        'tier_type': tier.tier_type,
                        'current_price': current_subscription.amount,
                        'new_price': tier.monthly_price,
                        'price_difference': price_difference,
                        'price_difference_formatted': f"${price_difference:.2f}/month",
                        'limitations': self._get_tier_limitations(tier),
                        'feature_comparison': self._get_feature_comparison(current_subscription.pricing_tier, tier),
                        'downgrade_url': f'/api/portal/subscription/{current_subscription.id}/downgrade/{tier.id}',
                        'savings_percentage': abs(price_difference / current_subscription.amount * 100)
                    })
            
            options_data = {
                'has_subscription': True,
                'current_subscription': {
                    'id': current_subscription.id,
                    'tier_name': current_subscription.pricing_tier.name,
                    'tier_type': current_subscription.pricing_tier.tier_type,
                    'current_price': current_subscription.amount,
                    'billing_cycle': current_subscription.billing_cycle
                },
                'upgrade_options': upgrade_options,
                'downgrade_options': downgrade_options,
                'proration_info': {
                    'proration_available': True,
                    'proration_method': 'create_prorations',
                    'proration_description': 'You will be charged a prorated amount for the remaining period'
                }
            }
            
            return {
                'success': True,
                'upgrade_downgrade_options': options_data
            }
            
        except Exception as e:
            logger.error(f"Error getting upgrade/downgrade options: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_subscription_with_retention_offers(self, customer_id: int, subscription_id: int, cancellation_reason: str = None) -> Dict[str, Any]:
        """Cancel subscription with retention offers"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Verify subscription ownership
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.customer_id == customer_id
                )
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            if subscription.status not in ['active', 'past_due']:
                return {
                    'success': False,
                    'error': 'Subscription cannot be canceled in current status'
                }
            
            # Generate retention offers based on subscription and customer data
            retention_offers = self._generate_retention_offers(subscription, customer)
            
            # Create cancellation request
            cancellation_data = {
                'subscription_id': subscription_id,
                'customer_id': customer_id,
                'reason': cancellation_reason,
                'requested_at': datetime.utcnow(),
                'effective_date': subscription.current_period_end,
                'retention_offers': retention_offers,
                'cancellation_url': f'/api/portal/subscription/{subscription_id}/cancel/confirm',
                'retention_url': f'/api/portal/subscription/{subscription_id}/retention'
            }
            
            # Log cancellation request
            self._log_audit_event(
                customer_id,
                AuditEventType.CANCELLATION_REQUESTED,
                AuditSeverity.INFO,
                f'Cancellation requested for subscription {subscription_id}. Reason: {cancellation_reason}'
            )
            
            return {
                'success': True,
                'cancellation_request': cancellation_data
            }
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reactivate_canceled_subscription(self, customer_id: int, subscription_id: int, payment_method_id: int = None) -> Dict[str, Any]:
        """Reactivate a canceled subscription"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Verify subscription ownership
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.customer_id == customer_id
                )
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            if subscription.status != 'canceled':
                return {
                    'success': False,
                    'error': 'Subscription is not canceled'
                }
            
            # Check if reactivation is within allowed period (90 days)
            if subscription.canceled_at:
                days_since_cancellation = (datetime.utcnow() - subscription.canceled_at).days
                if days_since_cancellation > 90:
                    return {
                        'success': False,
                        'error': 'Subscription cannot be reactivated after 90 days'
                    }
            
            # Check if payment method is available
            if not payment_method_id:
                # Get default payment method
                default_payment_method = self.db.query(PaymentMethod).filter(
                    and_(
                        PaymentMethod.customer_id == customer_id,
                        PaymentMethod.is_default == True
                    )
                ).first()
                
                if not default_payment_method:
                    return {
                        'success': False,
                        'error': 'No payment method available for reactivation'
                    }
                
                payment_method_id = default_payment_method.id
            
            # Reactivate in Stripe
            try:
                if subscription.stripe_subscription_id:
                    stripe_subscription = self.stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=False
                    )
                    
                    # Update local subscription
                    subscription.status = 'active'
                    subscription.canceled_at = None
                    subscription.updated_at = datetime.utcnow()
                    
                    self.db.commit()
                    
                    # Log reactivation
                    self._log_audit_event(
                        customer_id,
                        AuditEventType.SUBSCRIPTION_REACTIVATED,
                        AuditSeverity.INFO,
                        f'Subscription {subscription_id} reactivated successfully'
                    )
                    
                    reactivation_data = {
                        'subscription_id': subscription_id,
                        'status': 'reactivated',
                        'reactivated_at': datetime.utcnow().isoformat(),
                        'next_billing_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                        'amount': subscription.amount,
                        'currency': subscription.currency,
                        'message': 'Subscription reactivated successfully'
                    }
                    
                    return {
                        'success': True,
                        'reactivation': reactivation_data
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Stripe subscription ID not found'
                    }
                    
            except Exception as e:
                logger.error(f"Error reactivating Stripe subscription: {e}")
                return {
                    'success': False,
                    'error': 'Failed to reactivate subscription in Stripe'
                }
            
        except Exception as e:
            logger.error(f"Error reactivating subscription: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods
    def _get_billing_history(self, customer_id: int) -> Dict[str, Any]:
        """Get billing history summary"""
        try:
            billing_records = self.db.query(BillingHistory).filter(
                BillingHistory.customer_id == customer_id
            ).all()
            
            total_billed = sum(r.amount for r in billing_records if r.amount)
            total_paid = sum(r.amount for r in billing_records if r.status == 'paid' and r.amount)
            outstanding_balance = sum(r.amount for r in billing_records if r.status == 'unpaid' and r.amount)
            
            return {
                'total_billed': total_billed,
                'total_paid': total_paid,
                'outstanding_balance': outstanding_balance,
                'record_count': len(billing_records)
            }
        except Exception as e:
            logger.error(f"Error getting billing history: {e}")
            return {}
    
    def _get_usage_data(self, subscription_id: Optional[int]) -> Dict[str, Any]:
        """Get usage data for subscription"""
        if not subscription_id:
            return {}
        
        try:
            current_month = datetime.utcnow().month
            current_year = datetime.utcnow().year
            
            usage_record = self.db.query(FeatureUsage).filter(
                and_(
                    FeatureUsage.subscription_id == subscription_id,
                    FeatureUsage.usage_month == current_month,
                    FeatureUsage.usage_year == current_year
                )
            ).first()
            
            if not usage_record:
                return {}
            
            return {
                'health_checkins_used': usage_record.health_checkins_used or 0,
                'financial_reports_used': usage_record.financial_reports_used or 0,
                'ai_insights_used': usage_record.ai_insights_used or 0,
                'custom_reports_used': usage_record.custom_reports_used or 0,
                'team_members_used': usage_record.team_members_used or 0,
                'support_requests_used': usage_record.support_requests_used or 0,
                'career_risk_management_used': usage_record.career_risk_management_used or 0,
                'dedicated_account_manager_used': usage_record.dedicated_account_manager_used or 0
            }
        except Exception as e:
            logger.error(f"Error getting usage data: {e}")
            return {}
    
    def _get_payment_methods(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get payment methods for customer"""
        try:
            payment_methods = self.db.query(PaymentMethod).filter(
                PaymentMethod.customer_id == customer_id
            ).all()
            
            return [
                {
                    'id': pm.id,
                    'type': pm.payment_type,
                    'last4': pm.last4,
                    'brand': pm.brand,
                    'exp_month': pm.exp_month,
                    'exp_year': pm.exp_year,
                    'is_default': pm.is_default
                }
                for pm in payment_methods
            ]
        except Exception as e:
            logger.error(f"Error getting payment methods: {e}")
            return []
    
    def _get_recent_activity(self, customer_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity for customer"""
        try:
            audit_logs = self.db.query(AuditLog).filter(
                AuditLog.user_id == customer_id
            ).order_by(desc(AuditLog.event_timestamp)).limit(limit).all()
            
            return [
                {
                    'event_type': log.event_type.value,
                    'message': log.message,
                    'timestamp': log.event_timestamp.isoformat() if log.event_timestamp else None,
                    'severity': log.severity.value
                }
                for log in audit_logs
            ]
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    def _get_quick_actions(self, customer_id: int, subscription: Optional[Subscription]) -> List[Dict[str, Any]]:
        """Get quick actions for customer"""
        actions = []
        
        if subscription:
            if subscription.status == 'active':
                actions.extend([
                    {
                        'action': 'view_usage',
                        'title': 'View Usage',
                        'description': 'Check your current usage',
                        'icon': '📊',
                        'url': '/portal/usage'
                    },
                    {
                        'action': 'manage_payment',
                        'title': 'Manage Payment',
                        'description': 'Update payment methods',
                        'icon': '💳',
                        'url': '/portal/payment-methods'
                    },
                    {
                        'action': 'download_invoice',
                        'title': 'Download Invoice',
                        'description': 'Get your latest invoice',
                        'icon': '📄',
                        'url': '/portal/invoices'
                    }
                ])
            
            if subscription.status == 'past_due':
                actions.append({
                    'action': 'update_payment',
                    'title': 'Update Payment',
                    'description': 'Resolve payment issue',
                    'icon': '⚠️',
                    'url': '/portal/payment-methods',
                    'urgent': True
                })
        
        actions.extend([
            {
                'action': 'contact_support',
                'title': 'Contact Support',
                'description': 'Get help and answers',
                'icon': '❓',
                'url': '/portal/support'
            },
            {
                'action': 'account_settings',
                'title': 'Account Settings',
                'description': 'Manage your account',
                'icon': '⚙️',
                'url': '/portal/settings'
            }
        ])
        
        return actions
    
    def _get_notifications(self, customer_id: int, subscription: Optional[Subscription]) -> List[Dict[str, Any]]:
        """Get notifications for customer"""
        notifications = []
        
        if subscription:
            if subscription.status == 'past_due':
                notifications.append({
                    'type': 'warning',
                    'title': 'Payment Past Due',
                    'message': 'Your payment is overdue. Please update your payment method.',
                    'action': 'update_payment',
                    'urgent': True
                })
            
            # Check usage limits
            usage_data = self._get_usage_data(subscription.id)
            if usage_data:
                # Add usage-based notifications
                pass
        
        return notifications
    
    def _format_subscription_data(self, subscription: Subscription) -> Dict[str, Any]:
        """Format subscription data for portal"""
        if not subscription:
            return {}
        
        return {
            'id': subscription.id,
            'status': subscription.status,
            'tier': {
                'name': subscription.pricing_tier.name,
                'type': subscription.pricing_tier.tier_type,
                'description': subscription.pricing_tier.description
            },
            'billing': {
                'amount': subscription.amount,
                'currency': subscription.currency,
                'cycle': subscription.billing_cycle,
                'next_billing': subscription.current_period_end.isoformat() if subscription.current_period_end else None
            },
            'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
            'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None
        }
    
    def _get_available_pricing_tiers(self) -> List[Dict[str, Any]]:
        """Get available pricing tiers"""
        try:
            tiers = self.db.query(PricingTier).all()
            
            return [
                {
                    'id': tier.id,
                    'name': tier.name,
                    'type': tier.tier_type,
                    'description': tier.description,
                    'monthly_price': tier.monthly_price,
                    'yearly_price': tier.yearly_price,
                    'features': {
                        'health_checkins': tier.max_health_checkins_per_month,
                        'financial_reports': tier.max_financial_reports_per_month,
                        'ai_insights': tier.max_ai_insights_per_month
                    }
                }
                for tier in tiers
            ]
        except Exception as e:
            logger.error(f"Error getting pricing tiers: {e}")
            return []
    
    def _get_upgrade_options(self, subscription: Subscription) -> List[Dict[str, Any]]:
        """Get upgrade options for subscription"""
        options = []
        current_tier = subscription.pricing_tier.tier_type
        
        if current_tier == 'budget':
            options.append({
                'tier': 'mid_tier',
                'name': 'Mid-Tier',
                'price': '$35/month',
                'price_difference': '+$20/month',
                'benefits': [
                    '50 AI insights per month',
                    '10 financial reports per month',
                    '5 custom reports per month',
                    'Unlimited career risk management'
                ]
            })
        
        if current_tier in ['budget', 'mid_tier']:
            options.append({
                'tier': 'professional',
                'name': 'Professional',
                'price': '$75/month',
                'price_difference': f'+${60 if current_tier == "budget" else 40}/month',
                'benefits': [
                    'Unlimited all features',
                    '10 team members',
                    '10,000 API calls/hour',
                    'Dedicated account manager'
                ]
            })
        
        return options
    
    def _get_downgrade_options(self, subscription: Subscription) -> List[Dict[str, Any]]:
        """Get downgrade options for subscription"""
        options = []
        current_tier = subscription.pricing_tier.tier_type
        
        if current_tier == 'professional':
            options.append({
                'tier': 'mid_tier',
                'name': 'Mid-Tier',
                'price': '$35/month',
                'price_difference': '-$40/month',
                'limitations': [
                    'Limited feature usage',
                    'No team collaboration',
                    'No dedicated account manager'
                ]
            })
        
        if current_tier in ['professional', 'mid_tier']:
            options.append({
                'tier': 'budget',
                'name': 'Budget',
                'price': '$15/month',
                'price_difference': f'-${60 if current_tier == "professional" else 20}/month',
                'limitations': [
                    'Very limited feature usage',
                    'No AI insights',
                    'No custom reports',
                    'Basic support only'
                ]
            })
        
        return options
    
    def _get_cancellation_options(self, subscription: Subscription) -> Dict[str, Any]:
        """Get cancellation options for subscription"""
        return {
            'can_cancel': subscription.status in ['active', 'past_due'],
            'cancel_at_period_end': True,
            'immediate_cancellation': True,
            'refund_policy': 'Pro-rated refund for unused period',
            'data_retention': '30 days after cancellation',
            'reactivation': 'Available within 90 days'
        }
    
    def _get_subscription_actions(self, subscription: Optional[Subscription]) -> List[Dict[str, Any]]:
        """Get available subscription actions"""
        if not subscription:
            return []
        
        actions = []
        
        if subscription.status == 'active':
            actions.extend([
                {
                    'action': 'upgrade',
                    'title': 'Upgrade Plan',
                    'description': 'Get more features and higher limits',
                    'available': True
                },
                {
                    'action': 'downgrade',
                    'title': 'Downgrade Plan',
                    'description': 'Reduce costs with fewer features',
                    'available': True
                },
                {
                    'action': 'cancel',
                    'title': 'Cancel Subscription',
                    'description': 'Cancel your subscription',
                    'available': True
                }
            ])
        
        if subscription.status == 'canceled':
            actions.append({
                'action': 'reactivate',
                'title': 'Reactivate Subscription',
                'description': 'Restore your subscription',
                'available': True
            })
        
        return actions
    
    def _get_subscription_usage_data(self, subscription_id: int, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get usage data for subscription"""
        try:
            query = self.db.query(FeatureUsage).filter(
                FeatureUsage.subscription_id == subscription_id
            )
            
            if date_range:
                start_date, end_date = date_range
                query = query.filter(
                    and_(
                        FeatureUsage.usage_year >= start_date.year,
                        FeatureUsage.usage_year <= end_date.year,
                        FeatureUsage.usage_month >= start_date.month,
                        FeatureUsage.usage_month <= end_date.month
                    )
                )
            
            usage_records = query.all()
            
            if not usage_records:
                return {}
            
            # Aggregate usage data
            total_usage = {}
            for record in usage_records:
                total_usage['health_checkins'] = total_usage.get('health_checkins', 0) + (record.health_checkins_used or 0)
                total_usage['financial_reports'] = total_usage.get('financial_reports', 0) + (record.financial_reports_used or 0)
                total_usage['ai_insights'] = total_usage.get('ai_insights', 0) + (record.ai_insights_used or 0)
                total_usage['custom_reports'] = total_usage.get('custom_reports', 0) + (record.custom_reports_used or 0)
                total_usage['team_members'] = total_usage.get('team_members', 0) + (record.team_members_used or 0)
                total_usage['support_requests'] = total_usage.get('support_requests', 0) + (record.support_requests_used or 0)
                total_usage['career_risk_management'] = total_usage.get('career_risk_management', 0) + (record.career_risk_management_used or 0)
                total_usage['dedicated_account_manager'] = total_usage.get('dedicated_account_manager', 0) + (record.dedicated_account_manager_used or 0)
            
            return total_usage
            
        except Exception as e:
            logger.error(f"Error getting subscription usage data: {e}")
            return {}
    
    def _calculate_usage_summary(self, usage_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate usage summary across all subscriptions"""
        total_usage = {}
        
        for subscription_data in usage_data:
            usage = subscription_data.get('usage', {})
            for feature, amount in usage.items():
                total_usage[feature] = total_usage.get(feature, 0) + amount
        
        return total_usage
    
    def _get_usage_trends(self, customer_id: int, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get usage trends for customer"""
        # This would implement trend analysis
        # For now, return placeholder data
        return {
            'trend': 'increasing',
            'growth_rate': 15.5,
            'peak_usage_month': 'December',
            'usage_pattern': 'consistent'
        }
    
    def _get_usage_recommendations(self, usage_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get usage recommendations"""
        recommendations = []
        
        for subscription_data in usage_data:
            usage = subscription_data.get('usage', {})
            tier = subscription_data.get('tier', '')
            
            # Check for high usage
            if usage.get('health_checkins', 0) > 10:
                recommendations.append({
                    'type': 'upgrade',
                    'title': 'Consider Upgrading',
                    'message': f'You\'re using {usage["health_checkins"]} health check-ins. Consider upgrading for unlimited access.',
                    'priority': 'medium'
                })
            
            # Check for unused features
            if tier == 'professional' and usage.get('team_members', 0) == 0:
                recommendations.append({
                    'type': 'feature',
                    'title': 'Try Team Features',
                    'message': 'You have access to team collaboration features. Consider inviting team members.',
                    'priority': 'low'
                })
        
        return recommendations
    
    def _log_audit_event(self, customer_id: int, event_type: AuditEventType, severity: AuditSeverity, message: str):
        """Log audit event"""
        try:
            audit_log = AuditLog(
                event_type=event_type,
                severity=severity,
                event_timestamp=datetime.utcnow(),
                user_id=customer_id,
                message=message
            )
            self.db.add(audit_log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}") 
    
    # Helper methods for the new features
    def _calculate_usage_percentage(self, used: int, limit: int) -> float:
        """Calculate usage percentage"""
        if limit == -1 or limit == 0:
            return 0.0
        return min(100.0, (used / limit) * 100)
    
    def _get_status_message(self, status: str) -> str:
        """Get human-readable status message"""
        status_messages = {
            'active': 'Your subscription is active and billing normally',
            'past_due': 'Payment is past due. Please update your payment method',
            'canceled': 'Your subscription has been canceled',
            'unpaid': 'Payment failed. Access has been suspended'
        }
        return status_messages.get(status, 'Unknown status')
    
    def _get_available_actions(self, subscription: Subscription) -> List[str]:
        """Get available actions for subscription"""
        actions = []
        
        if subscription.status == 'active':
            actions.extend(['upgrade', 'downgrade', 'cancel', 'update_payment'])
        elif subscription.status == 'past_due':
            actions.extend(['update_payment', 'cancel'])
        elif subscription.status == 'canceled':
            actions.append('reactivate')
        
        actions.extend(['view_usage', 'view_billing', 'contact_support'])
        return actions
    
    def _add_payment_method(self, customer_id: int, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new payment method"""
        try:
            # This would integrate with Stripe to add payment method
            # For now, return a placeholder response
            return {
                'success': True,
                'message': 'Payment method added successfully',
                'payment_method_id': 999  # Placeholder
            }
        except Exception as e:
            logger.error(f"Error adding payment method: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_usage_trends_for_display(self, subscription_id: int) -> Dict[str, Any]:
        """Get usage trends for display"""
        try:
            # Get last 3 months of usage
            trends = {}
            current_date = datetime.utcnow()
            
            for i in range(3):
                month_date = current_date - timedelta(days=30 * i)
                month = month_date.month
                year = month_date.year
                
                usage_record = self.db.query(FeatureUsage).filter(
                    and_(
                        FeatureUsage.subscription_id == subscription_id,
                        FeatureUsage.usage_month == month,
                        FeatureUsage.usage_year == year
                    )
                ).first()
                
                if usage_record:
                    trends[f"{year}-{month:02d}"] = {
                        'health_checkins': usage_record.health_checkins_used or 0,
                        'financial_reports': usage_record.financial_reports_used or 0,
                        'ai_insights': usage_record.ai_insights_used or 0,
                        'custom_reports': usage_record.custom_reports_used or 0
                    }
            
            return trends
        except Exception as e:
            logger.error(f"Error getting usage trends: {e}")
            return {}
    
    def _get_usage_based_upgrade_recommendations(self, usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get upgrade recommendations based on usage"""
        recommendations = []
        
        for feature, analysis in usage_analysis.items():
            if analysis['status'] == 'limit_reached':
                recommendations.append({
                    'type': 'limit_reached',
                    'feature': feature,
                    'message': f'You have reached your {feature} limit',
                    'priority': 'high'
                })
            elif analysis['status'] == 'approaching_limit':
                recommendations.append({
                    'type': 'approaching_limit',
                    'feature': feature,
                    'message': f'You are approaching your {feature} limit ({analysis["percentage"]:.1f}% used)',
                    'priority': 'medium'
                })
        
        return recommendations
    
    def _get_tier_benefits(self, tier: PricingTier) -> List[str]:
        """Get benefits of a pricing tier"""
        benefits = []
        
        if tier.max_health_checkins_per_month == -1:
            benefits.append('Unlimited health check-ins')
        elif tier.max_health_checkins_per_month > 0:
            benefits.append(f'{tier.max_health_checkins_per_month} health check-ins per month')
        
        if tier.max_financial_reports_per_month == -1:
            benefits.append('Unlimited financial reports')
        elif tier.max_financial_reports_per_month > 0:
            benefits.append(f'{tier.max_financial_reports_per_month} financial reports per month')
        
        if tier.max_ai_insights_per_month == -1:
            benefits.append('Unlimited AI insights')
        elif tier.max_ai_insights_per_month > 0:
            benefits.append(f'{tier.max_ai_insights_per_month} AI insights per month')
        
        if tier.max_custom_reports_per_month == -1:
            benefits.append('Unlimited custom reports')
        elif tier.max_custom_reports_per_month > 0:
            benefits.append(f'{tier.max_custom_reports_per_month} custom reports per month')
        
        if tier.max_team_members > 0:
            benefits.append(f'{tier.max_team_members} team members')
        
        if tier.max_api_calls_per_hour > 0:
            benefits.append(f'{tier.max_api_calls_per_hour} API calls per hour')
        
        return benefits
    
    def _get_tier_limitations(self, tier: PricingTier) -> List[str]:
        """Get limitations of a pricing tier"""
        limitations = []
        
        if tier.max_health_checkins_per_month == 0:
            limitations.append('No health check-ins')
        elif tier.max_health_checkins_per_month > 0 and tier.max_health_checkins_per_month < 10:
            limitations.append(f'Limited to {tier.max_health_checkins_per_month} health check-ins per month')
        
        if tier.max_financial_reports_per_month == 0:
            limitations.append('No financial reports')
        elif tier.max_financial_reports_per_month > 0 and tier.max_financial_reports_per_month < 10:
            limitations.append(f'Limited to {tier.max_financial_reports_per_month} financial reports per month')
        
        if tier.max_ai_insights_per_month == 0:
            limitations.append('No AI insights')
        elif tier.max_ai_insights_per_month > 0 and tier.max_ai_insights_per_month < 50:
            limitations.append(f'Limited to {tier.max_ai_insights_per_month} AI insights per month')
        
        if tier.max_custom_reports_per_month == 0:
            limitations.append('No custom reports')
        elif tier.max_custom_reports_per_month > 0 and tier.max_custom_reports_per_month < 5:
            limitations.append(f'Limited to {tier.max_custom_reports_per_month} custom reports per month')
        
        if tier.max_team_members == 0:
            limitations.append('No team collaboration')
        
        if tier.max_api_calls_per_hour == 0:
            limitations.append('No API access')
        
        return limitations
    
    def _get_feature_comparison(self, current_tier: PricingTier, new_tier: PricingTier) -> Dict[str, Any]:
        """Get feature comparison between tiers"""
        features = ['health_checkins', 'financial_reports', 'ai_insights', 'custom_reports', 'team_members', 'api_calls_per_hour']
        comparison = {}
        
        for feature in features:
            current_limit = getattr(current_tier, f'max_{feature}_per_month', 0)
            new_limit = getattr(new_tier, f'max_{feature}_per_month', 0)
            
            if current_limit == -1 and new_limit == -1:
                status = 'same_unlimited'
            elif current_limit == -1:
                status = 'downgrade'
            elif new_limit == -1:
                status = 'upgrade'
            elif new_limit > current_limit:
                status = 'upgrade'
            elif new_limit < current_limit:
                status = 'downgrade'
            else:
                status = 'same'
            
            comparison[feature] = {
                'current': current_limit,
                'new': new_limit,
                'status': status
            }
        
        return comparison
    
    def _is_upgrade_recommended(self, tier: PricingTier, current_subscription: Subscription) -> bool:
        """Determine if upgrade is recommended"""
        # Simple logic: recommend if current usage is high
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        usage_record = self.db.query(FeatureUsage).filter(
            and_(
                FeatureUsage.subscription_id == current_subscription.id,
                FeatureUsage.usage_month == current_month,
                FeatureUsage.usage_year == current_year
            )
        ).first()
        
        if not usage_record:
            return False
        
        # Check if any feature is near limit
        current_tier = current_subscription.pricing_tier
        features = [
            ('health_checkins_used', 'max_health_checkins_per_month'),
            ('financial_reports_used', 'max_financial_reports_per_month'),
            ('ai_insights_used', 'max_ai_insights_per_month'),
            ('custom_reports_used', 'max_custom_reports_per_month')
        ]
        
        for usage_attr, limit_attr in features:
            used = getattr(usage_record, usage_attr, 0) or 0
            limit = getattr(current_tier, limit_attr, 0)
            
            if limit > 0 and used >= limit * 0.8:  # 80% usage threshold
                return True
        
        return False
    
    def _generate_retention_offers(self, subscription: Subscription, customer: Customer) -> List[Dict[str, Any]]:
        """Generate retention offers based on subscription and customer data"""
        offers = []
        
        # Get customer tenure
        customer_tenure_days = (datetime.utcnow() - customer.created_at).days if customer.created_at else 0
        
        # Get usage data
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        usage_record = self.db.query(FeatureUsage).filter(
            and_(
                FeatureUsage.subscription_id == subscription.id,
                FeatureUsage.usage_month == current_month,
                FeatureUsage.usage_year == current_year
            )
        ).first()
        
        # Offer 1: Discount for long-term customers
        if customer_tenure_days > 365:  # More than 1 year
            offers.append({
                'type': 'loyalty_discount',
                'title': 'Loyalty Discount',
                'description': 'Stay with us and get 20% off for the next 3 months',
                'discount_percentage': 20,
                'duration_months': 3,
                'savings': subscription.amount * 0.2 * 3,
                'offer_code': 'LOYAL20'
            })
        
        # Offer 2: Free upgrade for high usage
        if usage_record:
            total_usage = (
                (usage_record.health_checkins_used or 0) +
                (usage_record.financial_reports_used or 0) +
                (usage_record.ai_insights_used or 0) +
                (usage_record.custom_reports_used or 0)
            )
            
            if total_usage > 50:  # High usage threshold
                offers.append({
                    'type': 'free_upgrade',
                    'title': 'Free Tier Upgrade',
                    'description': 'Upgrade to the next tier free for 1 month',
                    'upgrade_tier': 'next_tier',
                    'duration_months': 1,
                    'savings': subscription.amount,
                    'offer_code': 'UPGRADE1'
                })
        
        # Offer 3: Pause subscription
        offers.append({
            'type': 'pause_subscription',
            'title': 'Pause Your Subscription',
            'description': 'Pause your subscription for up to 3 months',
            'pause_duration_months': 3,
            'savings': subscription.amount * 3,
            'offer_code': 'PAUSE3'
        })
        
        # Offer 4: Reduced rate
        offers.append({
            'type': 'reduced_rate',
            'title': 'Reduced Rate',
            'description': 'Get 50% off for the next 2 months',
            'discount_percentage': 50,
            'duration_months': 2,
            'savings': subscription.amount * 0.5 * 2,
            'offer_code': 'HALF50'
        })
        
        return offers 

    def get_billing_dashboard(self, customer_id: int) -> Dict[str, Any]:
        """Get comprehensive billing dashboard with all billing features"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get active subscription
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == customer_id,
                    Subscription.status.in_(['active', 'past_due'])
                )
            ).first()
            
            if not subscription:
                return {
                    'success': True,
                    'billing_dashboard': {
                        'has_subscription': False,
                        'message': 'No active subscription for billing dashboard'
                    }
                }
            
            # Get billing cycle options
            billing_cycle_options = self._get_billing_cycle_options(subscription)
            
            # Get next billing information
            next_billing_info = self._get_next_billing_info(subscription)
            
            # Get proration calculations
            proration_calculations = self._get_proration_calculations(subscription)
            
            # Get tax information
            tax_info = self._get_tax_information(subscription, customer)
            
            # Get payment failure information
            payment_failure_info = self._get_payment_failure_info(subscription)
            
            # Get billing dispute information
            billing_dispute_info = self._get_billing_dispute_info(customer_id)
            
            dashboard_data = {
                'has_subscription': True,
                'subscription_id': subscription.id,
                'billing_cycle_options': billing_cycle_options,
                'next_billing_info': next_billing_info,
                'proration_calculations': proration_calculations,
                'tax_information': tax_info,
                'payment_failure_info': payment_failure_info,
                'billing_dispute_info': billing_dispute_info,
                'quick_actions': self._get_billing_quick_actions(subscription)
            }
            
            return {
                'success': True,
                'billing_dashboard': dashboard_data
            }
            
        except Exception as e:
            logger.error(f"Error getting billing dashboard: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def toggle_billing_cycle(self, customer_id: int, subscription_id: int, new_cycle: str) -> Dict[str, Any]:
        """Toggle between monthly and annual billing cycles"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Verify subscription ownership
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.customer_id == customer_id
                )
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            if subscription.status not in ['active', 'past_due']:
                return {
                    'success': False,
                    'error': 'Subscription cannot be modified in current status'
                }
            
            if new_cycle not in ['monthly', 'annual']:
                return {
                    'success': False,
                    'error': 'Invalid billing cycle. Must be monthly or annual'
                }
            
            # Calculate new pricing
            current_tier = subscription.pricing_tier
            if new_cycle == 'monthly':
                new_amount = current_tier.monthly_price
            else:
                new_amount = current_tier.yearly_price / 12  # Monthly equivalent
            
            # Calculate proration
            proration_info = self._calculate_billing_cycle_change_proration(
                subscription, new_cycle, new_amount
            )
            
            # Update Stripe subscription
            try:
                if subscription.stripe_subscription_id:
                    # Get current Stripe subscription
                    stripe_subscription = self.stripe.Subscription.retrieve(
                        subscription.stripe_subscription_id
                    )
                    
                    # Update billing cycle in Stripe
                    updated_subscription = self.stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        items=[{
                            'id': stripe_subscription['items']['data'][0]['id'],
                            'price': self._get_stripe_price_id(current_tier, new_cycle)
                        }],
                        proration_behavior='create_prorations'
                    )
                    
                    # Update local subscription
                    subscription.billing_cycle = new_cycle
                    subscription.amount = new_amount
                    subscription.updated_at = datetime.utcnow()
                    
                    self.db.commit()
                    
                    # Log billing cycle change
                    self._log_audit_event(
                        customer_id,
                        AuditEventType.BILLING_CYCLE_CHANGED,
                        AuditSeverity.INFO,
                        f'Billing cycle changed from {subscription.billing_cycle} to {new_cycle}'
                    )
                    
                    return {
                        'success': True,
                        'billing_cycle_change': {
                            'subscription_id': subscription_id,
                            'old_cycle': subscription.billing_cycle,
                            'new_cycle': new_cycle,
                            'old_amount': subscription.amount,
                            'new_amount': new_amount,
                            'proration_info': proration_info,
                            'next_billing_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                            'message': f'Billing cycle changed to {new_cycle} successfully'
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Stripe subscription ID not found'
                    }
                    
            except Exception as e:
                logger.error(f"Error updating Stripe subscription billing cycle: {e}")
                return {
                    'success': False,
                    'error': 'Failed to update billing cycle in Stripe'
                }
            
        except Exception as e:
            logger.error(f"Error toggling billing cycle: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_next_billing_details(self, customer_id: int, subscription_id: int) -> Dict[str, Any]:
        """Get detailed next billing information"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Verify subscription ownership
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.customer_id == customer_id
                )
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get detailed billing information
            billing_details = self._get_detailed_billing_info(subscription, customer)
            
            return {
                'success': True,
                'next_billing_details': billing_details
            }
            
        except Exception as e:
            logger.error(f"Error getting next billing details: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_proration(self, customer_id: int, subscription_id: int, new_tier_id: int, effective_date: str = 'immediate') -> Dict[str, Any]:
        """Calculate proration for subscription changes"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Verify subscription ownership
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.customer_id == customer_id
                )
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            # Get new pricing tier
            new_tier = self.db.query(PricingTier).filter(
                PricingTier.id == new_tier_id
            ).first()
            
            if not new_tier:
                return {
                    'success': False,
                    'error': 'Pricing tier not found'
                }
            
            # Calculate proration
            proration_calculation = self._calculate_detailed_proration(
                subscription, new_tier, effective_date
            )
            
            return {
                'success': True,
                'proration_calculation': proration_calculation
            }
            
        except Exception as e:
            logger.error(f"Error calculating proration: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tax_information_and_receipts(self, customer_id: int, invoice_id: int = None) -> Dict[str, Any]:
        """Get tax information and receipts"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Get tax information
            tax_info = self._get_customer_tax_information(customer)
            
            # Get receipts
            receipts = self._get_customer_receipts(customer_id, invoice_id)
            
            return {
                'success': True,
                'tax_information': tax_info,
                'receipts': receipts
            }
            
        except Exception as e:
            logger.error(f"Error getting tax information and receipts: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_payment_failure(self, customer_id: int, subscription_id: int, action: str, payment_method_id: int = None) -> Dict[str, Any]:
        """Handle payment failure notifications and resolution"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            # Verify subscription ownership
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.customer_id == customer_id
                )
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            if action == 'retry_payment':
                return self._retry_failed_payment(subscription, payment_method_id)
            
            elif action == 'update_payment_method':
                return self._update_payment_method_for_failure(subscription, payment_method_id)
            
            elif action == 'get_failure_details':
                return self._get_payment_failure_details(subscription)
            
            elif action == 'acknowledge_failure':
                return self._acknowledge_payment_failure(subscription)
            
            else:
                return {
                    'success': False,
                    'error': f'Invalid action: {action}'
                }
                
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def manage_billing_disputes(self, customer_id: int, action: str, dispute_id: int = None, dispute_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Manage billing disputes and support contact"""
        try:
            customer = self.db.query(Customer).filter(
                Customer.id == customer_id
            ).first()
            
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            if action == 'create_dispute':
                return self._create_billing_dispute(customer_id, dispute_data or {})
            
            elif action == 'get_disputes':
                return self._get_customer_disputes(customer_id)
            
            elif action == 'get_dispute_details':
                if not dispute_id:
                    return {
                        'success': False,
                        'error': 'Dispute ID required'
                    }
                return self._get_dispute_details(customer_id, dispute_id)
            
            elif action == 'add_dispute_comment':
                if not dispute_id:
                    return {
                        'success': False,
                        'error': 'Dispute ID required'
                    }
                return self._add_dispute_comment(customer_id, dispute_id, dispute_data or {})
            
            elif action == 'contact_support':
                return self._contact_billing_support(customer_id, dispute_data or {})
            
            else:
                return {
                    'success': False,
                    'error': f'Invalid action: {action}'
                }
                
        except Exception as e:
            logger.error(f"Error managing billing disputes: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Helper methods for billing dashboard features
    def _get_billing_cycle_options(self, subscription: Subscription) -> Dict[str, Any]:
        """Get billing cycle options for subscription"""
        current_tier = subscription.pricing_tier
        
        return {
            'current_cycle': subscription.billing_cycle,
            'available_cycles': ['monthly', 'annual'],
            'pricing': {
                'monthly': {
                    'amount': current_tier.monthly_price,
                    'currency': subscription.currency,
                    'savings': 0
                },
                'annual': {
                    'amount': current_tier.yearly_price,
                    'currency': subscription.currency,
                    'monthly_equivalent': current_tier.yearly_price / 12,
                    'savings': current_tier.monthly_price * 12 - current_tier.yearly_price,
                    'savings_percentage': ((current_tier.monthly_price * 12 - current_tier.yearly_price) / (current_tier.monthly_price * 12)) * 100
                }
            },
            'can_change': subscription.status in ['active', 'past_due'],
            'change_url': f'/api/portal/subscription/{subscription.id}/billing-cycle/toggle'
        }
    
    def _get_next_billing_info(self, subscription: Subscription) -> Dict[str, Any]:
        """Get next billing information"""
        if not subscription.current_period_end:
            return None
        
        days_until_billing = (subscription.current_period_end - datetime.utcnow()).days
        
        return {
            'next_billing_date': subscription.current_period_end.isoformat(),
            'days_until_billing': max(0, days_until_billing),
            'amount': subscription.amount,
            'currency': subscription.currency,
            'billing_cycle': subscription.billing_cycle,
            'status': 'upcoming' if days_until_billing > 0 else 'due',
            'payment_method': self._get_default_payment_method_info(subscription.customer_id)
        }
    
    def _get_proration_calculations(self, subscription: Subscription) -> Dict[str, Any]:
        """Get proration calculations for potential changes"""
        current_tier = subscription.pricing_tier
        
        # Calculate proration for upgrade scenarios
        upgrade_prorations = {}
        if current_tier.tier_type == 'budget':
            mid_tier = self.db.query(PricingTier).filter(PricingTier.tier_type == 'mid_tier').first()
            if mid_tier:
                upgrade_prorations['mid_tier'] = self._calculate_tier_upgrade_proration(
                    subscription, mid_tier
                )
        
        if current_tier.tier_type in ['budget', 'mid_tier']:
            professional_tier = self.db.query(PricingTier).filter(PricingTier.tier_type == 'professional').first()
            if professional_tier:
                upgrade_prorations['professional'] = self._calculate_tier_upgrade_proration(
                    subscription, professional_tier
                )
        
        return {
            'available_calculations': list(upgrade_prorations.keys()),
            'calculations': upgrade_prorations,
            'calculation_url': f'/api/portal/subscription/{subscription.id}/proration/calculate'
        }
    
    def _get_tax_information(self, subscription: Subscription, customer: Customer) -> Dict[str, Any]:
        """Get tax information for customer"""
        # This would integrate with tax calculation services
        # For now, return placeholder data
        
        return {
            'tax_exempt': False,
            'tax_rate': 0.085,  # 8.5% tax rate
            'tax_location': {
                'country': customer.address.get('country', 'US'),
                'state': customer.address.get('state', 'CA'),
                'city': customer.address.get('city', 'San Francisco')
            },
            'last_tax_calculation': datetime.utcnow().isoformat(),
            'tax_documents_available': True,
            'tax_documents_url': f'/api/portal/customer/{customer.id}/tax-documents'
        }
    
    def _get_payment_failure_info(self, subscription: Subscription) -> Dict[str, Any]:
        """Get payment failure information"""
        if subscription.status != 'past_due':
            return {
                'has_failures': False,
                'message': 'No payment failures'
            }
        
        # Get recent failed payments
        failed_payments = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.subscription_id == subscription.id,
                BillingHistory.status == 'failed'
            )
        ).order_by(desc(BillingHistory.created_at)).limit(3).all()
        
        return {
            'has_failures': True,
            'status': subscription.status,
            'failed_payments': [
                {
                    'invoice_number': payment.invoice_number,
                    'amount': payment.amount,
                    'currency': payment.currency,
                    'failed_at': payment.created_at.isoformat() if payment.created_at else None,
                    'retry_count': 0  # This would be tracked in a separate table
                }
                for payment in failed_payments
            ],
            'resolution_actions': [
                'retry_payment',
                'update_payment_method',
                'contact_support'
            ],
            'grace_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }
    
    def _get_billing_dispute_info(self, customer_id: int) -> Dict[str, Any]:
        """Get billing dispute information"""
        # Get recent disputes
        recent_disputes = self.db.query(BillingDispute).filter(
            BillingDispute.customer_id == customer_id
        ).order_by(desc(BillingDispute.created_at)).limit(5).all()
        
        return {
            'recent_disputes': [
                {
                    'id': dispute.id,
                    'subject': dispute.subject,
                    'status': dispute.status,
                    'created_at': dispute.created_at.isoformat() if dispute.created_at else None,
                    'priority': dispute.priority
                }
                for dispute in recent_disputes
            ],
            'dispute_count': len(recent_disputes),
            'support_contact': {
                'email': 'billing-support@mingus.com',
                'phone': '+1-555-0123',
                'hours': 'Monday-Friday 9AM-6PM PST'
            },
            'create_dispute_url': f'/api/portal/customer/{customer_id}/disputes/create'
        }
    
    def _get_billing_quick_actions(self, subscription: Subscription) -> List[Dict[str, Any]]:
        """Get quick actions for billing dashboard"""
        actions = []
        
        if subscription.status == 'active':
            actions.extend([
                {
                    'action': 'change_billing_cycle',
                    'title': 'Change Billing Cycle',
                    'description': 'Switch between monthly and annual billing',
                    'icon': '🔄',
                    'url': f'/api/portal/subscription/{subscription.id}/billing-cycle'
                },
                {
                    'action': 'download_receipts',
                    'title': 'Download Receipts',
                    'description': 'Get your billing receipts and tax documents',
                    'icon': '📄',
                    'url': f'/api/portal/customer/{subscription.customer_id}/receipts'
                }
            ])
        
        if subscription.status == 'past_due':
            actions.extend([
                {
                    'action': 'resolve_payment',
                    'title': 'Resolve Payment Issue',
                    'description': 'Update payment method or retry payment',
                    'icon': '⚠️',
                    'url': f'/api/portal/subscription/{subscription.id}/payment-failure',
                    'urgent': True
                }
            ])
        
        actions.extend([
            {
                'action': 'contact_billing_support',
                'title': 'Contact Billing Support',
                'description': 'Get help with billing questions',
                'icon': '❓',
                'url': f'/api/portal/customer/{subscription.customer_id}/billing-support'
            },
            {
                'action': 'create_dispute',
                'title': 'Create Billing Dispute',
                'description': 'Dispute a charge or billing issue',
                'icon': '⚖️',
                'url': f'/api/portal/customer/{subscription.customer_id}/disputes/create'
            }
        ])
        
        return actions
    
    def _calculate_billing_cycle_change_proration(self, subscription: Subscription, new_cycle: str, new_amount: float) -> Dict[str, Any]:
        """Calculate proration for billing cycle change"""
        current_amount = subscription.amount
        amount_difference = new_amount - current_amount
        
        # Calculate remaining days in current period
        if subscription.current_period_end:
            remaining_days = (subscription.current_period_end - datetime.utcnow()).days
            total_days = 30 if subscription.billing_cycle == 'monthly' else 365
            
            proration_amount = (amount_difference / total_days) * remaining_days
        else:
            proration_amount = 0
        
        return {
            'current_amount': current_amount,
            'new_amount': new_amount,
            'amount_difference': amount_difference,
            'proration_amount': proration_amount,
            'proration_type': 'credit' if proration_amount < 0 else 'charge',
            'effective_date': 'immediate'
        }
    
    def _get_stripe_price_id(self, tier: PricingTier, cycle: str) -> str:
        """Get Stripe price ID for tier and cycle"""
        # This would map to actual Stripe price IDs
        # For now, return placeholder
        return f'price_{tier.tier_type}_{cycle}'
    
    def _get_detailed_billing_info(self, subscription: Subscription, customer: Customer) -> Dict[str, Any]:
        """Get detailed billing information"""
        return {
            'subscription_details': {
                'id': subscription.id,
                'status': subscription.status,
                'tier': subscription.pricing_tier.name,
                'billing_cycle': subscription.billing_cycle,
                'amount': subscription.amount,
                'currency': subscription.currency
            },
            'next_billing': self._get_next_billing_info(subscription),
            'payment_method': self._get_default_payment_method_info(customer.id),
            'tax_info': self._get_tax_information(subscription, customer),
            'billing_address': customer.address,
            'invoice_preferences': {
                'email_invoices': True,
                'paper_invoices': False,
                'invoice_frequency': 'monthly'
            }
        }
    
    def _get_default_payment_method_info(self, customer_id: int) -> Dict[str, Any]:
        """Get default payment method information"""
        payment_method = self.db.query(PaymentMethod).filter(
            and_(
                PaymentMethod.customer_id == customer_id,
                PaymentMethod.is_default == True
            )
        ).first()
        
        if not payment_method:
            return None
        
        return {
            'id': payment_method.id,
            'type': payment_method.payment_type,
            'last4': payment_method.last4,
            'brand': payment_method.brand,
            'exp_month': payment_method.exp_month,
            'exp_year': payment_method.exp_year
        }
    
    def _calculate_tier_upgrade_proration(self, subscription: Subscription, new_tier: PricingTier) -> Dict[str, Any]:
        """Calculate proration for tier upgrade"""
        current_amount = subscription.amount
        new_amount = new_tier.monthly_price
        amount_difference = new_amount - current_amount
        
        # Calculate remaining days in current period
        if subscription.current_period_end:
            remaining_days = (subscription.current_period_end - datetime.utcnow()).days
            total_days = 30 if subscription.billing_cycle == 'monthly' else 365
            
            proration_amount = (amount_difference / total_days) * remaining_days
        else:
            proration_amount = 0
        
        return {
            'current_tier': subscription.pricing_tier.name,
            'new_tier': new_tier.name,
            'current_amount': current_amount,
            'new_amount': new_amount,
            'amount_difference': amount_difference,
            'proration_amount': proration_amount,
            'proration_type': 'charge' if proration_amount > 0 else 'credit',
            'effective_date': 'immediate'
        }
    
    def _calculate_detailed_proration(self, subscription: Subscription, new_tier: PricingTier, effective_date: str) -> Dict[str, Any]:
        """Calculate detailed proration for subscription changes"""
        current_amount = subscription.amount
        new_amount = new_tier.monthly_price
        amount_difference = new_amount - current_amount
        
        # Calculate proration based on effective date
        if effective_date == 'immediate':
            if subscription.current_period_end:
                remaining_days = (subscription.current_period_end - datetime.utcnow()).days
                total_days = 30 if subscription.billing_cycle == 'monthly' else 365
                
                proration_amount = (amount_difference / total_days) * remaining_days
            else:
                proration_amount = 0
        else:
            proration_amount = 0
        
        return {
            'current_subscription': {
                'tier': subscription.pricing_tier.name,
                'amount': current_amount,
                'billing_cycle': subscription.billing_cycle
            },
            'new_subscription': {
                'tier': new_tier.name,
                'amount': new_amount,
                'billing_cycle': subscription.billing_cycle
            },
            'proration_details': {
                'amount_difference': amount_difference,
                'proration_amount': proration_amount,
                'proration_type': 'charge' if proration_amount > 0 else 'credit',
                'effective_date': effective_date,
                'next_billing_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None
            },
            'total_charge': new_amount + proration_amount if proration_amount > 0 else new_amount
        }
    
    def _get_customer_tax_information(self, customer: Customer) -> Dict[str, Any]:
        """Get customer tax information"""
        return {
            'tax_exempt': False,
            'tax_rate': 0.085,
            'tax_location': customer.address,
            'tax_id': None,  # Would be stored if available
            'tax_documents': [
                {
                    'type': 'invoice',
                    'year': 2024,
                    'download_url': f'/api/portal/customer/{customer.id}/tax-documents/2024'
                }
            ]
        }
    
    def _get_customer_receipts(self, customer_id: int, invoice_id: int = None) -> List[Dict[str, Any]]:
        """Get customer receipts"""
        query = self.db.query(BillingHistory).filter(
            BillingHistory.customer_id == customer_id
        )
        
        if invoice_id:
            query = query.filter(BillingHistory.id == invoice_id)
        
        receipts = query.order_by(desc(BillingHistory.created_at)).limit(10).all()
        
        return [
            {
                'id': receipt.id,
                'invoice_number': receipt.invoice_number,
                'amount': receipt.amount,
                'currency': receipt.currency,
                'status': receipt.status,
                'created_at': receipt.created_at.isoformat() if receipt.created_at else None,
                'download_url': f'/api/portal/invoice/{receipt.id}/download' if receipt.stripe_invoice_id else None
            }
            for receipt in receipts
        ]
    
    def _retry_failed_payment(self, subscription: Subscription, payment_method_id: int = None) -> Dict[str, Any]:
        """Retry failed payment"""
        try:
            # This would integrate with Stripe to retry payment
            # For now, return placeholder response
            
            return {
                'success': True,
                'retry_result': {
                    'status': 'scheduled',
                    'retry_date': (datetime.utcnow() + timedelta(days=1)).isoformat(),
                    'payment_method_id': payment_method_id,
                    'message': 'Payment retry scheduled for tomorrow'
                }
            }
        except Exception as e:
            logger.error(f"Error retrying payment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_payment_method_for_failure(self, subscription: Subscription, payment_method_id: int) -> Dict[str, Any]:
        """Update payment method for failed payment"""
        try:
            # This would update the default payment method and retry
            return {
                'success': True,
                'update_result': {
                    'status': 'updated',
                    'payment_method_id': payment_method_id,
                    'retry_scheduled': True,
                    'message': 'Payment method updated and retry scheduled'
                }
            }
        except Exception as e:
            logger.error(f"Error updating payment method: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_payment_failure_details(self, subscription: Subscription) -> Dict[str, Any]:
        """Get payment failure details"""
        return {
            'failure_reason': 'insufficient_funds',
            'failure_date': datetime.utcnow().isoformat(),
            'retry_attempts': 2,
            'max_retries': 3,
            'next_retry': (datetime.utcnow() + timedelta(days=1)).isoformat(),
            'grace_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }
    
    def _acknowledge_payment_failure(self, subscription: Subscription) -> Dict[str, Any]:
        """Acknowledge payment failure"""
        return {
            'success': True,
            'acknowledgment': {
                'status': 'acknowledged',
                'acknowledged_at': datetime.utcnow().isoformat(),
                'message': 'Payment failure acknowledged'
            }
        }
    
    def _create_billing_dispute(self, customer_id: int, dispute_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create billing dispute"""
        try:
            dispute = BillingDispute(
                customer_id=customer_id,
                dispute_type='billing_dispute',
                subject=dispute_data.get('subject', ''),
                description=dispute_data.get('description', ''),
                priority=dispute_data.get('priority', 'medium'),
                status='open'
            )
            
            self.db.add(dispute)
            self.db.commit()
            
            return {
                'success': True,
                'dispute': {
                    'id': dispute.id,
                    'subject': dispute.subject,
                    'status': dispute.status,
                    'created_at': dispute.created_at.isoformat() if dispute.created_at else None
                },
                'message': 'Billing dispute created successfully'
            }
        except Exception as e:
            logger.error(f"Error creating billing dispute: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_customer_disputes(self, customer_id: int) -> Dict[str, Any]:
        """Get customer disputes"""
        disputes = self.db.query(BillingDispute).filter(
            BillingDispute.customer_id == customer_id
        ).order_by(desc(BillingDispute.created_at)).all()
        
        return {
            'success': True,
            'disputes': [
                {
                    'id': dispute.id,
                    'subject': dispute.subject,
                    'status': dispute.status,
                    'priority': dispute.priority,
                    'created_at': dispute.created_at.isoformat() if dispute.created_at else None
                }
                for dispute in disputes
            ]
        }
    
    def _get_dispute_details(self, customer_id: int, dispute_id: int) -> Dict[str, Any]:
        """Get dispute details"""
        dispute = self.db.query(BillingDispute).filter(
            and_(
                BillingDispute.id == dispute_id,
                BillingDispute.customer_id == customer_id
            )
        ).first()
        
        if not dispute:
            return {
                'success': False,
                'error': 'Dispute not found'
            }
        
        return {
            'success': True,
            'dispute_details': {
                'id': dispute.id,
                'subject': dispute.subject,
                'description': dispute.description,
                'status': dispute.status,
                'priority': dispute.priority,
                'created_at': dispute.created_at.isoformat() if dispute.created_at else None,
                'updated_at': dispute.updated_at.isoformat() if dispute.updated_at else None
            }
        }
    
    def _add_dispute_comment(self, customer_id: int, dispute_id: int, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add comment to dispute"""
        try:
            # This would add a comment to the dispute
            # For now, return placeholder response
            return {
                'success': True,
                'comment': {
                    'id': 999,
                    'dispute_id': dispute_id,
                    'message': comment_data.get('message', ''),
                    'created_at': datetime.utcnow().isoformat()
                },
                'message': 'Comment added successfully'
            }
        except Exception as e:
            logger.error(f"Error adding dispute comment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _contact_billing_support(self, customer_id: int, support_data: Dict[str, Any]) -> Dict[str, Any]:
        """Contact billing support"""
        try:
            # This would create a support ticket
            # For now, return placeholder response
            return {
                'success': True,
                'support_ticket': {
                    'id': 999,
                    'customer_id': customer_id,
                    'subject': support_data.get('subject', ''),
                    'priority': support_data.get('priority', 'medium'),
                    'created_at': datetime.utcnow().isoformat()
                },
                'message': 'Support ticket created successfully'
            }
        except Exception as e:
            logger.error(f"Error contacting billing support: {e}")
            return {
                'success': False,
                'error': str(e)
            }