"""
Automated Workflows Service for MINGUS
Handles automated workflows for trial expiration, payment recovery, renewals,
upgrade/downgrade confirmations, and cancellation retention
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, func
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from ..models.subscription import (
    Customer, Subscription, BillingHistory, FeatureUsage,
    AuditLog, AuditEventType, AuditSeverity
)
from ..config.base import Config

logger = logging.getLogger(__name__)

class WorkflowType(Enum):
    """Types of automated workflows"""
    TRIAL_EXPIRATION = "trial_expiration"
    PAYMENT_RECOVERY = "payment_recovery"
    RENEWAL_CONFIRMATION = "renewal_confirmation"
    UPGRADE_CONFIRMATION = "upgrade_confirmation"
    DOWNGRADE_CONFIRMATION = "downgrade_confirmation"
    CANCELLATION_RETENTION = "cancellation_retention"

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AutomatedWorkflowManager:
    """Comprehensive automated workflow management for MINGUS"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Workflow configuration
        self.workflow_config = {
            'trial_expiration': {
                'notifications': [
                    {'days_before': 3, 'template': 'trial_expiring_3_days'},
                    {'days_before': 1, 'template': 'trial_expiring_1_day'},
                    {'days_before': 0, 'template': 'trial_expired'}
                ],
                'enabled': True
            },
            'payment_recovery': {
                'retry_attempts': 3,
                'retry_schedule': [0, 3, 7],  # Days after failure
                'enabled': True
            },
            'renewal_confirmation': {
                'days_before': 7,
                'enabled': True
            },
            'upgrade_confirmation': {
                'enabled': True,
                'confirmation_required': False
            },
            'downgrade_confirmation': {
                'enabled': True,
                'confirmation_required': True
            },
            'cancellation_retention': {
                'survey_enabled': True,
                'retention_offers': [
                    {'discount': 0.20, 'duration': 3, 'description': '20% off for 3 months'},
                    {'discount': 0.15, 'duration': 6, 'description': '15% off for 6 months'},
                    {'discount': 0.10, 'duration': 12, 'description': '10% off for 1 year'}
                ],
                'enabled': True
            }
        }
        
        # Email templates
        self.email_templates = self._load_email_templates()
    
    def _load_email_templates(self) -> Dict[str, Dict[str, str]]:
        """Load email templates for workflows"""
        return {
            'trial_expiring_3_days': {
                'subject': 'Your MINGUS trial ends in 3 days',
                'body': """
                Hi {customer_name},
                
                Your MINGUS trial will expire in 3 days. Don't lose access to your financial insights!
                
                Upgrade now to continue enjoying:
                - Unlimited health check-ins
                - Advanced financial reports
                - AI-powered insights
                - Priority support
                
                Upgrade now: {upgrade_url}
                
                Best regards,
                The MINGUS Team
                """
            },
            'trial_expiring_1_day': {
                'subject': 'Your MINGUS trial ends tomorrow',
                'body': """
                Hi {customer_name},
                
                Your MINGUS trial expires tomorrow! This is your final reminder to upgrade.
                
                Don't lose your progress and insights. Upgrade now to keep everything:
                - Your financial data and reports
                - Health check-in history
                - AI insights and recommendations
                
                Upgrade now: {upgrade_url}
                
                Best regards,
                The MINGUS Team
                """
            },
            'trial_expired': {
                'subject': 'Your MINGUS trial has expired',
                'body': """
                Hi {customer_name},
                
                Your MINGUS trial has expired. We'd love to have you back!
                
                Upgrade now to restore access to all your data and continue your financial journey.
                
                Special offer: 20% off your first month when you upgrade today!
                
                Upgrade now: {upgrade_url}
                
                Best regards,
                The MINGUS Team
                """
            },
            'payment_failed': {
                'subject': 'Payment failed - Action required',
                'body': """
                Hi {customer_name},
                
                We couldn't process your payment for your MINGUS subscription.
                
                Amount: ${amount}
                Due date: {due_date}
                
                Please update your payment method: {payment_url}
                
                If you need help, contact our support team.
                
                Best regards,
                The MINGUS Team
                """
            },
            'renewal_confirmation': {
                'subject': 'Your MINGUS subscription renews soon',
                'body': """
                Hi {customer_name},
                
                Your MINGUS subscription will automatically renew on {renewal_date}.
                
                Renewal details:
                - Plan: {plan_name}
                - Amount: ${amount}
                - Next billing: {renewal_date}
                
                If you want to make changes, visit your account: {account_url}
                
                Best regards,
                The MINGUS Team
                """
            },
            'upgrade_confirmation': {
                'subject': 'Your MINGUS upgrade is complete',
                'body': """
                Hi {customer_name},
                
                Your MINGUS subscription has been successfully upgraded!
                
                Upgrade details:
                - New plan: {new_plan}
                - New monthly amount: ${new_amount}
                - Proration: ${proration_amount}
                
                Enjoy your new features!
                
                Best regards,
                The MINGUS Team
                """
            },
            'downgrade_confirmation': {
                'subject': 'Your MINGUS downgrade is scheduled',
                'body': """
                Hi {customer_name},
                
                Your MINGUS subscription downgrade has been scheduled.
                
                Downgrade details:
                - New plan: {new_plan}
                - Effective date: {effective_date}
                - New monthly amount: ${new_amount}
                
                You can cancel this change anytime before {effective_date}.
                
                Best regards,
                The MINGUS Team
                """
            },
            'cancellation_survey': {
                'subject': 'Help us improve MINGUS',
                'body': """
                Hi {customer_name},
                
                We're sorry to see you go. Before you leave, could you help us improve?
                
                Please take a quick survey: {survey_url}
                
                Your feedback helps us make MINGUS better for everyone.
                
                Best regards,
                The MINGUS Team
                """
            },
            'retention_offer': {
                'subject': 'Special offer to keep you with MINGUS',
                'body': """
                Hi {customer_name},
                
                We'd love to keep you as part of the MINGUS family!
                
                Special offer: {offer_description}
                
                This offer expires in 7 days. Reactivate now: {reactivate_url}
                
                Best regards,
                The MINGUS Team
                """
            }
        }
    
    # ============================================================================
    # TRIAL EXPIRATION WORKFLOW
    # ============================================================================
    
    def process_trial_expiration_workflows(self) -> Dict[str, Any]:
        """Process trial expiration notifications"""
        try:
            results = {
                'notifications_sent': 0,
                'workflows_created': 0,
                'errors': []
            }
            
            # Get subscriptions with expiring trials
            trial_subscriptions = self._get_expiring_trials()
            
            for subscription in trial_subscriptions:
                try:
                    workflow_result = self._process_trial_expiration_workflow(subscription)
                    
                    if workflow_result['success']:
                        results['notifications_sent'] += workflow_result['notifications_sent']
                        results['workflows_created'] += 1
                    else:
                        results['errors'].append(f"Trial workflow failed for subscription {subscription.id}: {workflow_result['error']}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing trial workflow for subscription {subscription.id}: {str(e)}")
            
            logger.info(f"Trial expiration workflows processed: {results['notifications_sent']} notifications sent")
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing trial expiration workflows: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_expiring_trials(self) -> List[Subscription]:
        """Get subscriptions with expiring trials"""
        now = datetime.utcnow()
        
        # Get trials expiring in the next 3 days
        expiring_trials = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'trialing',
                Subscription.trial_end.isnot(None),
                Subscription.trial_end >= now,
                Subscription.trial_end <= now + timedelta(days=3)
            )
        ).all()
        
        return expiring_trials
    
    def _process_trial_expiration_workflow(self, subscription: Subscription) -> Dict[str, Any]:
        """Process trial expiration workflow for a subscription"""
        try:
            customer = subscription.customer
            trial_end = subscription.trial_end
            days_until_expiry = (trial_end - datetime.utcnow()).days
            
            notifications_sent = 0
            
            # Check which notifications to send
            for notification in self.workflow_config['trial_expiration']['notifications']:
                if notification['days_before'] == days_until_expiry:
                    # Send notification
                    email_result = self._send_trial_notification(
                        customer, subscription, notification['template']
                    )
                    
                    if email_result['success']:
                        notifications_sent += 1
                        
                        # Log workflow event
                        self._log_workflow_event(
                            workflow_type=WorkflowType.TRIAL_EXPIRATION,
                            subscription_id=subscription.id,
                            customer_id=customer.id,
                            event_description=f"Trial expiration notification sent: {notification['days_before']} days before",
                            metadata={
                                'days_before_expiry': notification['days_before'],
                                'template': notification['template'],
                                'trial_end': trial_end.isoformat()
                            }
                        )
            
            return {
                'success': True,
                'notifications_sent': notifications_sent,
                'days_until_expiry': days_until_expiry
            }
            
        except Exception as e:
            logger.error(f"Error processing trial expiration workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # PAYMENT FAILURE RECOVERY WORKFLOW
    # ============================================================================
    
    def process_payment_recovery_workflows(self) -> Dict[str, Any]:
        """Process payment failure recovery workflows"""
        try:
            results = {
                'retry_attempts': 0,
                'recoveries_successful': 0,
                'workflows_created': 0,
                'errors': []
            }
            
            # Get failed payments that need retry
            failed_payments = self._get_failed_payments_for_retry()
            
            for payment in failed_payments:
                try:
                    recovery_result = self._process_payment_recovery_workflow(payment)
                    
                    if recovery_result['success']:
                        results['retry_attempts'] += recovery_result['retry_attempts']
                        results['recoveries_successful'] += recovery_result['recoveries_successful']
                        results['workflows_created'] += 1
                    else:
                        results['errors'].append(f"Payment recovery failed for payment {payment.id}: {recovery_result['error']}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing payment recovery for payment {payment.id}: {str(e)}")
            
            logger.info(f"Payment recovery workflows processed: {results['retry_attempts']} retry attempts")
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing payment recovery workflows: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_failed_payments_for_retry(self) -> List[BillingHistory]:
        """Get failed payments that need retry"""
        now = datetime.utcnow()
        
        # Get failed payments within retry window
        failed_payments = self.db.query(BillingHistory).filter(
            and_(
                BillingHistory.status == 'failed',
                BillingHistory.paid == False,
                BillingHistory.retry_count < self.workflow_config['payment_recovery']['retry_attempts']
            )
        ).all()
        
        # Filter by retry schedule
        retry_schedule = self.workflow_config['payment_recovery']['retry_schedule']
        eligible_payments = []
        
        for payment in failed_payments:
            days_since_failure = (now - payment.invoice_date).days
            if days_since_failure in retry_schedule:
                eligible_payments.append(payment)
        
        return eligible_payments
    
    def _process_payment_recovery_workflow(self, payment: BillingHistory) -> Dict[str, Any]:
        """Process payment recovery workflow for a failed payment"""
        try:
            customer = payment.customer
            subscription = payment.subscription
            
            retry_attempts = 0
            recoveries_successful = 0
            
            # Attempt payment retry
            retry_result = self._retry_payment(payment)
            
            if retry_result['success']:
                retry_attempts += 1
                
                if retry_result['payment_succeeded']:
                    recoveries_successful += 1
                    
                    # Update payment status
                    payment.status = 'succeeded'
                    payment.paid = True
                    payment.paid_date = datetime.utcnow()
                    payment.retry_count += 1
                    
                    # Log successful recovery
                    self._log_workflow_event(
                        workflow_type=WorkflowType.PAYMENT_RECOVERY,
                        subscription_id=subscription.id,
                        customer_id=customer.id,
                        event_description="Payment recovery successful",
                        metadata={
                            'payment_id': payment.id,
                            'retry_count': payment.retry_count,
                            'recovery_amount': payment.amount_due
                        }
                    )
                else:
                    # Update retry count
                    payment.retry_count += 1
                    
                    # Send failure notification
                    self._send_payment_failure_notification(customer, payment)
                    
                    # Log retry attempt
                    self._log_workflow_event(
                        workflow_type=WorkflowType.PAYMENT_RECOVERY,
                        subscription_id=subscription.id,
                        customer_id=customer.id,
                        event_description="Payment retry attempt failed",
                        metadata={
                            'payment_id': payment.id,
                            'retry_count': payment.retry_count,
                            'next_retry_days': self._get_next_retry_days(payment.retry_count)
                        }
                    )
            
            self.db.commit()
            
            return {
                'success': True,
                'retry_attempts': retry_attempts,
                'recoveries_successful': recoveries_successful
            }
            
        except Exception as e:
            logger.error(f"Error processing payment recovery workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # RENEWAL CONFIRMATION WORKFLOW
    # ============================================================================
    
    def process_renewal_confirmation_workflows(self) -> Dict[str, Any]:
        """Process subscription renewal confirmations"""
        try:
            results = {
                'confirmations_sent': 0,
                'workflows_created': 0,
                'errors': []
            }
            
            # Get subscriptions with upcoming renewals
            renewing_subscriptions = self._get_upcoming_renewals()
            
            for subscription in renewing_subscriptions:
                try:
                    confirmation_result = self._process_renewal_confirmation_workflow(subscription)
                    
                    if confirmation_result['success']:
                        results['confirmations_sent'] += 1
                        results['workflows_created'] += 1
                    else:
                        results['errors'].append(f"Renewal confirmation failed for subscription {subscription.id}: {confirmation_result['error']}")
                        
                except Exception as e:
                    results['errors'].append(f"Error processing renewal confirmation for subscription {subscription.id}: {str(e)}")
            
            logger.info(f"Renewal confirmation workflows processed: {results['confirmations_sent']} confirmations sent")
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing renewal confirmation workflows: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_upcoming_renewals(self) -> List[Subscription]:
        """Get subscriptions with upcoming renewals"""
        now = datetime.utcnow()
        days_before = self.workflow_config['renewal_confirmation']['days_before']
        
        renewing_subscriptions = self.db.query(Subscription).filter(
            and_(
                Subscription.status == 'active',
                Subscription.current_period_end.isnot(None),
                Subscription.current_period_end >= now,
                Subscription.current_period_end <= now + timedelta(days=days_before)
            )
        ).all()
        
        return renewing_subscriptions
    
    def _process_renewal_confirmation_workflow(self, subscription: Subscription) -> Dict[str, Any]:
        """Process renewal confirmation workflow for a subscription"""
        try:
            customer = subscription.customer
            
            # Send renewal confirmation email
            email_result = self._send_renewal_confirmation(customer, subscription)
            
            if email_result['success']:
                # Log workflow event
                self._log_workflow_event(
                    workflow_type=WorkflowType.RENEWAL_CONFIRMATION,
                    subscription_id=subscription.id,
                    customer_id=customer.id,
                    event_description="Renewal confirmation sent",
                    metadata={
                        'renewal_date': subscription.current_period_end.isoformat(),
                        'plan_name': subscription.pricing_tier.name,
                        'amount': subscription.amount
                    }
                )
                
                return {
                    'success': True,
                    'confirmation_sent': True
                }
            else:
                return {
                    'success': False,
                    'error': email_result['error']
                }
            
        except Exception as e:
            logger.error(f"Error processing renewal confirmation workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # UPGRADE/DOWNGRADE CONFIRMATION WORKFLOW
    # ============================================================================
    
    def process_upgrade_confirmation_workflow(
        self,
        subscription_id: int,
        old_tier_name: str,
        new_tier_name: str,
        proration_amount: float
    ) -> Dict[str, Any]:
        """Process upgrade confirmation workflow"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            customer = subscription.customer
            
            # Send upgrade confirmation email
            email_result = self._send_upgrade_confirmation(
                customer, subscription, old_tier_name, new_tier_name, proration_amount
            )
            
            if email_result['success']:
                # Log workflow event
                self._log_workflow_event(
                    workflow_type=WorkflowType.UPGRADE_CONFIRMATION,
                    subscription_id=subscription.id,
                    customer_id=customer.id,
                    event_description="Upgrade confirmation sent",
                    metadata={
                        'old_tier': old_tier_name,
                        'new_tier': new_tier_name,
                        'proration_amount': proration_amount
                    }
                )
                
                return {
                    'success': True,
                    'confirmation_sent': True
                }
            else:
                return {
                    'success': False,
                    'error': email_result['error']
                }
            
        except Exception as e:
            logger.error(f"Error processing upgrade confirmation workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_downgrade_confirmation_workflow(
        self,
        subscription_id: int,
        old_tier_name: str,
        new_tier_name: str,
        effective_date: str
    ) -> Dict[str, Any]:
        """Process downgrade confirmation workflow"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            customer = subscription.customer
            
            # Send downgrade confirmation email
            email_result = self._send_downgrade_confirmation(
                customer, subscription, old_tier_name, new_tier_name, effective_date
            )
            
            if email_result['success']:
                # Log workflow event
                self._log_workflow_event(
                    workflow_type=WorkflowType.DOWNGRADE_CONFIRMATION,
                    subscription_id=subscription.id,
                    customer_id=customer.id,
                    event_description="Downgrade confirmation sent",
                    metadata={
                        'old_tier': old_tier_name,
                        'new_tier': new_tier_name,
                        'effective_date': effective_date
                    }
                )
                
                return {
                    'success': True,
                    'confirmation_sent': True
                }
            else:
                return {
                    'success': False,
                    'error': email_result['error']
                }
            
        except Exception as e:
            logger.error(f"Error processing downgrade confirmation workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # CANCELLATION RETENTION WORKFLOW
    # ============================================================================
    
    def process_cancellation_retention_workflow(
        self,
        subscription_id: int,
        cancellation_reason: str = None
    ) -> Dict[str, Any]:
        """Process cancellation retention workflow"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()
            
            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }
            
            customer = subscription.customer
            
            results = {
                'survey_sent': False,
                'retention_offers_sent': 0,
                'workflow_completed': False
            }
            
            # Send cancellation survey
            if self.workflow_config['cancellation_retention']['survey_enabled']:
                survey_result = self._send_cancellation_survey(customer, subscription, cancellation_reason)
                if survey_result['success']:
                    results['survey_sent'] = True
            
            # Send retention offers
            retention_offers = self.workflow_config['cancellation_retention']['retention_offers']
            for offer in retention_offers:
                offer_result = self._send_retention_offer(customer, subscription, offer)
                if offer_result['success']:
                    results['retention_offers_sent'] += 1
            
            # Log workflow event
            self._log_workflow_event(
                workflow_type=WorkflowType.CANCELLATION_RETENTION,
                subscription_id=subscription.id,
                customer_id=customer.id,
                event_description="Cancellation retention workflow executed",
                metadata={
                    'cancellation_reason': cancellation_reason,
                    'survey_sent': results['survey_sent'],
                    'offers_sent': results['retention_offers_sent']
                }
            )
            
            results['workflow_completed'] = True
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error processing cancellation retention workflow: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # EMAIL SENDING METHODS
    # ============================================================================
    
    def _send_trial_notification(
        self,
        customer: Customer,
        subscription: Subscription,
        template_name: str
    ) -> Dict[str, Any]:
        """Send trial expiration notification"""
        try:
            template = self.email_templates[template_name]
            
            # Prepare email content
            subject = template['subject']
            body = template['body'].format(
                customer_name=customer.name,
                upgrade_url=f"{self.config.BASE_URL}/upgrade/{subscription.id}",
                trial_end=subscription.trial_end.strftime('%B %d, %Y') if subscription.trial_end else 'N/A'
            )
            
            # Send email
            email_result = self._send_email(customer.email, subject, body)
            
            return {
                'success': True,
                'template': template_name,
                'email_sent': email_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error sending trial notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_payment_failure_notification(
        self,
        customer: Customer,
        payment: BillingHistory
    ) -> Dict[str, Any]:
        """Send payment failure notification"""
        try:
            template = self.email_templates['payment_failed']
            
            # Prepare email content
            subject = template['subject']
            body = template['body'].format(
                customer_name=customer.name,
                amount=payment.amount_due,
                due_date=payment.due_date.strftime('%B %d, %Y') if payment.due_date else 'N/A',
                payment_url=f"{self.config.BASE_URL}/account/payment"
            )
            
            # Send email
            email_result = self._send_email(customer.email, subject, body)
            
            return {
                'success': True,
                'email_sent': email_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error sending payment failure notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_renewal_confirmation(
        self,
        customer: Customer,
        subscription: Subscription
    ) -> Dict[str, Any]:
        """Send renewal confirmation email"""
        try:
            template = self.email_templates['renewal_confirmation']
            
            # Prepare email content
            subject = template['subject']
            body = template['body'].format(
                customer_name=customer.name,
                renewal_date=subscription.current_period_end.strftime('%B %d, %Y') if subscription.current_period_end else 'N/A',
                plan_name=subscription.pricing_tier.name,
                amount=subscription.amount,
                account_url=f"{self.config.BASE_URL}/account"
            )
            
            # Send email
            email_result = self._send_email(customer.email, subject, body)
            
            return {
                'success': True,
                'email_sent': email_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error sending renewal confirmation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_upgrade_confirmation(
        self,
        customer: Customer,
        subscription: Subscription,
        old_tier_name: str,
        new_tier_name: str,
        proration_amount: float
    ) -> Dict[str, Any]:
        """Send upgrade confirmation email"""
        try:
            template = self.email_templates['upgrade_confirmation']
            
            # Prepare email content
            subject = template['subject']
            body = template['body'].format(
                customer_name=customer.name,
                new_plan=new_tier_name,
                new_amount=subscription.amount,
                proration_amount=proration_amount
            )
            
            # Send email
            email_result = self._send_email(customer.email, subject, body)
            
            return {
                'success': True,
                'email_sent': email_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error sending upgrade confirmation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_downgrade_confirmation(
        self,
        customer: Customer,
        subscription: Subscription,
        old_tier_name: str,
        new_tier_name: str,
        effective_date: str
    ) -> Dict[str, Any]:
        """Send downgrade confirmation email"""
        try:
            template = self.email_templates['downgrade_confirmation']
            
            # Prepare email content
            subject = template['subject']
            body = template['body'].format(
                customer_name=customer.name,
                new_plan=new_tier_name,
                effective_date=effective_date,
                new_amount=subscription.amount
            )
            
            # Send email
            email_result = self._send_email(customer.email, subject, body)
            
            return {
                'success': True,
                'email_sent': email_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error sending downgrade confirmation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_cancellation_survey(
        self,
        customer: Customer,
        subscription: Subscription,
        cancellation_reason: str = None
    ) -> Dict[str, Any]:
        """Send cancellation survey"""
        try:
            template = self.email_templates['cancellation_survey']
            
            # Prepare email content
            subject = template['subject']
            body = template['body'].format(
                customer_name=customer.name,
                survey_url=f"{self.config.BASE_URL}/survey/cancellation/{subscription.id}"
            )
            
            # Send email
            email_result = self._send_email(customer.email, subject, body)
            
            return {
                'success': True,
                'email_sent': email_result['success']
            }
            
        except Exception as e:
            logger.error(f"Error sending cancellation survey: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_retention_offer(
        self,
        customer: Customer,
        subscription: Subscription,
        offer: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send retention offer"""
        try:
            template = self.email_templates['retention_offer']
            
            # Prepare email content
            subject = template['subject']
            body = template['body'].format(
                customer_name=customer.name,
                offer_description=offer['description'],
                reactivate_url=f"{self.config.BASE_URL}/reactivate/{subscription.id}?offer={offer['discount']}"
            )
            
            # Send email
            email_result = self._send_email(customer.email, subject, body)
            
            return {
                'success': True,
                'email_sent': email_result['success'],
                'offer': offer
            }
            
        except Exception as e:
            logger.error(f"Error sending retention offer: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email using configured SMTP settings"""
        try:
            # This would integrate with your email service (SendGrid, AWS SES, etc.)
            # For now, we'll log the email details
            logger.info(f"Email would be sent to {to_email}: {subject}")
            
            return {
                'success': True,
                'to_email': to_email,
                'subject': subject
            }
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _retry_payment(self, payment: BillingHistory) -> Dict[str, Any]:
        """Retry a failed payment"""
        try:
            # This would integrate with your payment processor (Stripe, etc.)
            # For now, we'll simulate a retry
            logger.info(f"Payment retry attempted for payment {payment.id}")
            
            # Simulate 70% success rate
            import random
            success = random.random() < 0.7
            
            return {
                'success': True,
                'payment_succeeded': success,
                'retry_attempt': payment.retry_count + 1
            }
            
        except Exception as e:
            logger.error(f"Error retrying payment: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_next_retry_days(self, current_retry_count: int) -> int:
        """Get days until next retry"""
        retry_schedule = self.workflow_config['payment_recovery']['retry_schedule']
        
        if current_retry_count < len(retry_schedule):
            return retry_schedule[current_retry_count]
        
        return None
    
    def _log_workflow_event(
        self,
        workflow_type: WorkflowType,
        subscription_id: int,
        customer_id: int,
        event_description: str,
        metadata: Dict = None
    ):
        """Log workflow event"""
        try:
            audit_log = AuditLog(
                event_type=AuditEventType.SUBSCRIPTION_UPDATED,
                subscription_id=subscription_id,
                customer_id=customer_id,
                event_description=event_description,
                metadata={
                    'workflow_type': workflow_type.value,
                    'workflow_metadata': metadata
                }
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to log workflow event: {e}")
    
    def run_all_automated_workflows(self) -> Dict[str, Any]:
        """Run all automated workflows"""
        try:
            results = {
                'trial_expiration': {},
                'payment_recovery': {},
                'renewal_confirmation': {},
                'total_workflows': 0,
                'total_errors': 0
            }
            
            # Run trial expiration workflows
            if self.workflow_config['trial_expiration']['enabled']:
                trial_result = self.process_trial_expiration_workflows()
                results['trial_expiration'] = trial_result
                results['total_workflows'] += 1
                if not trial_result['success']:
                    results['total_errors'] += 1
            
            # Run payment recovery workflows
            if self.workflow_config['payment_recovery']['enabled']:
                payment_result = self.process_payment_recovery_workflows()
                results['payment_recovery'] = payment_result
                results['total_workflows'] += 1
                if not payment_result['success']:
                    results['total_errors'] += 1
            
            # Run renewal confirmation workflows
            if self.workflow_config['renewal_confirmation']['enabled']:
                renewal_result = self.process_renewal_confirmation_workflows()
                results['renewal_confirmation'] = renewal_result
                results['total_workflows'] += 1
                if not renewal_result['success']:
                    results['total_errors'] += 1
            
            logger.info(f"All automated workflows completed: {results['total_workflows']} workflows, {results['total_errors']} errors")
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error running automated workflows: {e}")
            return {
                'success': False,
                'error': str(e)
            } 