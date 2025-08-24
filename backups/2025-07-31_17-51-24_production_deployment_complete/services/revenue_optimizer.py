"""
Revenue Optimization Service for MINGUS
Handles upgrade prompts, churn prevention, payment recovery, and revenue recognition
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, desc, case, extract
import json

from ..models.subscription import (
    Customer, Subscription, BillingHistory, FeatureUsage,
    AuditLog, AuditEventType, AuditSeverity
)
from ..config.base import Config

logger = logging.getLogger(__name__)

class RevenueOptimizerError(Exception):
    """Custom exception for revenue optimization errors"""
    pass

class RevenueOptimizer:
    """Comprehensive revenue optimization for MINGUS"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Upgrade prompt configuration
        self.upgrade_triggers = {
            'usage_threshold': 0.8,  # 80% usage threshold
            'feature_limit_reached': True,
            'consecutive_months': 2,  # Months of consistent usage
            'value_indicators': ['high_api_usage', 'team_collaboration', 'advanced_features']
        }
        
        # Churn prevention configuration
        self.churn_indicators = {
            'usage_decline_threshold': 0.5,  # 50% usage decline
            'payment_failure_count': 2,
            'support_ticket_count': 3,
            'login_frequency_decline': 0.7,
            'feature_usage_decline': 0.6
        }
        
        # Payment recovery configuration
        self.recovery_strategies = {
            'immediate_retry': {'delay_hours': 0, 'max_attempts': 1},
            'short_delay': {'delay_hours': 24, 'max_attempts': 2},
            'medium_delay': {'delay_hours': 72, 'max_attempts': 2},
            'long_delay': {'delay_hours': 168, 'max_attempts': 1},  # 1 week
            'final_attempt': {'delay_hours': 336, 'max_attempts': 1}  # 2 weeks
        }
    
    # ============================================================================
    # UPGRADE PROMPT TRIGGERS
    # ============================================================================
    
    def check_upgrade_opportunities(
        self,
        customer_id: int = None,
        include_all_customers: bool = False
    ) -> Dict[str, Any]:
        """Check for upgrade opportunities across customers"""
        try:
            if include_all_customers:
                customers = self.db.query(Customer).all()
            elif customer_id:
                customers = [self.db.query(Customer).filter(Customer.id == customer_id).first()]
            else:
                return {
                    'success': False,
                    'error': 'Must specify customer_id or include_all_customers=True'
                }
            
            upgrade_opportunities = []
            
            for customer in customers:
                if not customer:
                    continue
                
                # Get active subscription
                subscription = self.db.query(Subscription).filter(
                    and_(
                        Subscription.customer_id == customer.id,
                        Subscription.status.in_(['active', 'trialing'])
                    )
                ).first()
                
                if not subscription:
                    continue
                
                # Check upgrade triggers
                triggers = self._check_upgrade_triggers(customer, subscription)
                
                if triggers['should_upgrade']:
                    upgrade_opportunities.append({
                        'customer_id': customer.id,
                        'customer_name': customer.name,
                        'customer_email': customer.email,
                        'current_tier': subscription.pricing_tier.tier_type.value,
                        'current_tier_name': subscription.pricing_tier.name,
                        'triggers': triggers['triggered_reasons'],
                        'confidence_score': triggers['confidence_score'],
                        'recommended_tier': triggers['recommended_tier'],
                        'estimated_value': triggers['estimated_value'],
                        'last_checked': datetime.utcnow().isoformat()
                    })
            
            return {
                'success': True,
                'upgrade_opportunities': upgrade_opportunities,
                'total_opportunities': len(upgrade_opportunities),
                'check_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error checking upgrade opportunities: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_upgrade_triggers(
        self,
        customer: Customer,
        subscription: Subscription
    ) -> Dict[str, Any]:
        """Check specific upgrade triggers for a customer"""
        triggered_reasons = []
        confidence_score = 0.0
        
        # Get current usage
        current_usage = self._get_current_usage(subscription.id)
        if not current_usage:
            return {
                'should_upgrade': False,
                'triggered_reasons': [],
                'confidence_score': 0.0,
                'recommended_tier': None,
                'estimated_value': 0.0
            }
        
        # Check usage threshold
        usage_percentage = self._calculate_usage_percentage(current_usage, subscription.pricing_tier)
        if usage_percentage >= self.upgrade_triggers['usage_threshold']:
            triggered_reasons.append({
                'type': 'usage_threshold',
                'description': f'Usage at {usage_percentage:.1%} of current tier limits',
                'value': usage_percentage
            })
            confidence_score += 0.3
        
        # Check feature limit reached
        if self.upgrade_triggers['feature_limit_reached']:
            limited_features = self._check_feature_limits(current_usage, subscription.pricing_tier)
            if limited_features:
                triggered_reasons.append({
                    'type': 'feature_limit_reached',
                    'description': f'Limited by {len(limited_features)} features',
                    'value': limited_features
                })
                confidence_score += 0.4
        
        # Check consecutive months of usage
        consecutive_months = self._check_consecutive_usage(subscription.id)
        if consecutive_months >= self.upgrade_triggers['consecutive_months']:
            triggered_reasons.append({
                'type': 'consecutive_usage',
                'description': f'{consecutive_months} consecutive months of consistent usage',
                'value': consecutive_months
            })
            confidence_score += 0.2
        
        # Check value indicators
        value_indicators = self._check_value_indicators(customer, subscription)
        if value_indicators:
            triggered_reasons.append({
                'type': 'value_indicators',
                'description': f'High-value indicators detected: {", ".join(value_indicators)}',
                'value': value_indicators
            })
            confidence_score += 0.3
        
        # Determine if upgrade is recommended
        should_upgrade = confidence_score >= 0.5 and len(triggered_reasons) >= 2
        
        # Get recommended tier
        recommended_tier = None
        estimated_value = 0.0
        
        if should_upgrade:
            recommended_tier = self._get_recommended_tier(subscription.pricing_tier)
            estimated_value = self._calculate_upgrade_value(subscription, recommended_tier)
        
        return {
            'should_upgrade': should_upgrade,
            'triggered_reasons': triggered_reasons,
            'confidence_score': min(confidence_score, 1.0),
            'recommended_tier': recommended_tier,
            'estimated_value': estimated_value
        }
    
    def generate_upgrade_prompt(
        self,
        customer_id: int,
        prompt_type: str = 'usage_based'
    ) -> Dict[str, Any]:
        """Generate personalized upgrade prompt"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
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
            
            # Get upgrade analysis
            upgrade_analysis = self._check_upgrade_triggers(customer, subscription)
            
            if not upgrade_analysis['should_upgrade']:
                return {
                    'success': False,
                    'error': 'No upgrade opportunity detected'
                }
            
            # Generate personalized prompt
            prompt_data = self._create_upgrade_prompt(
                customer, subscription, upgrade_analysis, prompt_type
            )
            
            # Log upgrade prompt generation
            self._log_revenue_event(
                event_type=AuditEventType.UPGRADE_PROMPT_GENERATED,
                customer_id=customer_id,
                subscription_id=subscription.id,
                event_description=f"Upgrade prompt generated: {prompt_type}",
                metadata={
                    'prompt_type': prompt_type,
                    'confidence_score': upgrade_analysis['confidence_score'],
                    'triggered_reasons': upgrade_analysis['triggered_reasons'],
                    'recommended_tier': upgrade_analysis['recommended_tier']
                }
            )
            
            return {
                'success': True,
                'prompt_data': prompt_data,
                'upgrade_analysis': upgrade_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating upgrade prompt: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # CHURN PREVENTION WORKFLOWS
    # ============================================================================
    
    def detect_churn_risk(
        self,
        customer_id: int = None,
        include_all_customers: bool = False
    ) -> Dict[str, Any]:
        """Detect customers at risk of churning"""
        try:
            if include_all_customers:
                customers = self.db.query(Customer).all()
            elif customer_id:
                customers = [self.db.query(Customer).filter(Customer.id == customer_id).first()]
            else:
                return {
                    'success': False,
                    'error': 'Must specify customer_id or include_all_customers=True'
                }
            
            churn_risks = []
            
            for customer in customers:
                if not customer:
                    continue
                
                # Get active subscription
                subscription = self.db.query(Subscription).filter(
                    and_(
                        Subscription.customer_id == customer.id,
                        Subscription.status.in_(['active', 'trialing'])
                    )
                ).first()
                
                if not subscription:
                    continue
                
                # Check churn indicators
                risk_analysis = self._analyze_churn_risk(customer, subscription)
                
                if risk_analysis['risk_level'] in ['medium', 'high', 'critical']:
                    churn_risks.append({
                        'customer_id': customer.id,
                        'customer_name': customer.name,
                        'customer_email': customer.email,
                        'current_tier': subscription.pricing_tier.tier_type.value,
                        'risk_level': risk_analysis['risk_level'],
                        'risk_score': risk_analysis['risk_score'],
                        'risk_indicators': risk_analysis['risk_indicators'],
                        'recommended_actions': risk_analysis['recommended_actions'],
                        'last_checked': datetime.utcnow().isoformat()
                    })
            
            return {
                'success': True,
                'churn_risks': churn_risks,
                'total_risks': len(churn_risks),
                'check_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting churn risk: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_churn_risk(
        self,
        customer: Customer,
        subscription: Subscription
    ) -> Dict[str, Any]:
        """Analyze churn risk for a specific customer"""
        risk_indicators = []
        risk_score = 0.0
        
        # Check usage decline
        usage_decline = self._check_usage_decline(subscription.id)
        if usage_decline >= self.churn_indicators['usage_decline_threshold']:
            risk_indicators.append({
                'type': 'usage_decline',
                'description': f'Usage declined by {usage_decline:.1%}',
                'severity': 'high' if usage_decline > 0.7 else 'medium'
            })
            risk_score += 0.4
        
        # Check payment failures
        payment_failures = self._check_payment_failures(customer.id)
        if payment_failures >= self.churn_indicators['payment_failure_count']:
            risk_indicators.append({
                'type': 'payment_failures',
                'description': f'{payment_failures} recent payment failures',
                'severity': 'critical' if payment_failures > 3 else 'high'
            })
            risk_score += 0.5
        
        # Check support tickets
        support_tickets = self._check_support_tickets(customer.id)
        if support_tickets >= self.churn_indicators['support_ticket_count']:
            risk_indicators.append({
                'type': 'support_tickets',
                'description': f'{support_tickets} recent support tickets',
                'severity': 'medium'
            })
            risk_score += 0.2
        
        # Check login frequency
        login_decline = self._check_login_frequency_decline(customer.id)
        if login_decline >= self.churn_indicators['login_frequency_decline']:
            risk_indicators.append({
                'type': 'login_decline',
                'description': f'Login frequency declined by {login_decline:.1%}',
                'severity': 'high'
            })
            risk_score += 0.3
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = 'critical'
        elif risk_score >= 0.6:
            risk_level = 'high'
        elif risk_score >= 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Generate recommended actions
        recommended_actions = self._generate_churn_prevention_actions(
            risk_indicators, risk_level
        )
        
        return {
            'risk_level': risk_level,
            'risk_score': min(risk_score, 1.0),
            'risk_indicators': risk_indicators,
            'recommended_actions': recommended_actions
        }
    
    def execute_churn_prevention_workflow(
        self,
        customer_id: int,
        workflow_type: str = 'automated'
    ) -> Dict[str, Any]:
        """Execute churn prevention workflow for a customer"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
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
    # PAYMENT RECOVERY AUTOMATION
    # ============================================================================
    
    def identify_payment_recovery_opportunities(
        self,
        include_all_customers: bool = True
    ) -> Dict[str, Any]:
        """Identify customers needing payment recovery"""
        try:
            # Find failed payments
            failed_payments = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.status.in_(['failed', 'past_due']),
                    BillingHistory.paid == False
                )
            ).all()
            
            recovery_opportunities = []
            
            for payment in failed_payments:
                # Get customer and subscription
                customer = payment.customer
                subscription = payment.subscription
                
                if not customer or not subscription:
                    continue
                
                # Analyze recovery potential
                recovery_analysis = self._analyze_payment_recovery_potential(
                    customer, subscription, payment
                )
                
                if recovery_analysis['recovery_potential'] in ['high', 'medium']:
                    recovery_opportunities.append({
                        'customer_id': customer.id,
                        'customer_name': customer.name,
                        'customer_email': customer.email,
                        'invoice_id': payment.id,
                        'invoice_number': payment.invoice_number,
                        'amount_due': payment.amount_due,
                        'days_overdue': recovery_analysis['days_overdue'],
                        'recovery_potential': recovery_analysis['recovery_potential'],
                        'recovery_score': recovery_analysis['recovery_score'],
                        'recommended_strategy': recovery_analysis['recommended_strategy'],
                        'next_action': recovery_analysis['next_action']
                    })
            
            return {
                'success': True,
                'recovery_opportunities': recovery_opportunities,
                'total_opportunities': len(recovery_opportunities),
                'check_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error identifying payment recovery opportunities: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def execute_payment_recovery_automation(
        self,
        customer_id: int,
        invoice_id: int,
        strategy: str = 'auto'
    ) -> Dict[str, Any]:
        """Execute automated payment recovery for a specific invoice"""
        try:
            customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return {
                    'success': False,
                    'error': 'Customer not found'
                }
            
            invoice = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.id == invoice_id,
                    BillingHistory.customer_id == customer_id
                )
            ).first()
            
            if not invoice:
                return {
                    'success': False,
                    'error': 'Invoice not found'
                }
            
            if invoice.paid:
                return {
                    'success': True,
                    'message': 'Invoice already paid',
                    'status': 'already_paid'
                }
            
            # Execute recovery strategy
            if strategy == 'auto':
                recovery_result = self._execute_automatic_recovery(customer, invoice)
            else:
                recovery_result = self._execute_manual_recovery(customer, invoice, strategy)
            
            # Log recovery attempt
            self._log_revenue_event(
                event_type=AuditEventType.PAYMENT_RECOVERY_ATTEMPTED,
                customer_id=customer_id,
                invoice_id=invoice_id,
                event_description=f"Payment recovery attempted: {strategy}",
                metadata={
                    'strategy': strategy,
                    'amount': invoice.amount_due,
                    'days_overdue': (datetime.utcnow() - invoice.due_date).days if invoice.due_date else 0,
                    'result': recovery_result['status']
                }
            )
            
            return {
                'success': True,
                'recovery_result': recovery_result
            }
            
        except Exception as e:
            logger.error(f"Error executing payment recovery: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # REVENUE RECOGNITION REPORTING
    # ============================================================================
    
    def generate_revenue_recognition_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """Generate revenue recognition report"""
        try:
            # Get all billing history in date range
            billing_history = self.db.query(BillingHistory).filter(
                and_(
                    BillingHistory.invoice_date >= start_date,
                    BillingHistory.invoice_date <= end_date,
                    BillingHistory.paid == True
                )
            ).all()
            
            # Calculate revenue metrics
            revenue_metrics = self._calculate_revenue_metrics(billing_history, start_date, end_date)
            
            # Generate recognition schedule
            recognition_schedule = self._generate_recognition_schedule(billing_history)
            
            # Calculate deferred revenue
            deferred_revenue = self._calculate_deferred_revenue(billing_history, end_date)
            
            # Generate report
            report = {
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'generated_at': datetime.utcnow().isoformat()
                },
                'revenue_metrics': revenue_metrics,
                'recognition_schedule': recognition_schedule,
                'deferred_revenue': deferred_revenue,
                'summary': {
                    'total_revenue': revenue_metrics['total_revenue'],
                    'recognized_revenue': revenue_metrics['recognized_revenue'],
                    'deferred_revenue': deferred_revenue['total_deferred'],
                    'revenue_growth': revenue_metrics['growth_rate']
                }
            }
            
            return {
                'success': True,
                'report': report
            }
            
        except Exception as e:
            logger.error(f"Error generating revenue recognition report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_revenue_analytics(
        self,
        period: str = 'monthly',
        include_projections: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive revenue analytics"""
        try:
            # Calculate current period
            end_date = datetime.utcnow()
            if period == 'monthly':
                start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == 'quarterly':
                quarter = (end_date.month - 1) // 3
                start_date = end_date.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:  # yearly
                start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Get revenue data
            revenue_data = self._get_revenue_data(start_date, end_date)
            
            # Calculate key metrics
            analytics = {
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'metrics': {
                    'total_revenue': revenue_data['total_revenue'],
                    'recurring_revenue': revenue_data['recurring_revenue'],
                    'one_time_revenue': revenue_data['one_time_revenue'],
                    'average_order_value': revenue_data['average_order_value'],
                    'customer_count': revenue_data['customer_count'],
                    'churn_rate': revenue_data['churn_rate'],
                    'upgrade_rate': revenue_data['upgrade_rate'],
                    'downgrade_rate': revenue_data['downgrade_rate']
                },
                'tier_breakdown': revenue_data['tier_breakdown'],
                'trends': revenue_data['trends']
            }
            
            # Add projections if requested
            if include_projections:
                analytics['projections'] = self._calculate_revenue_projections(revenue_data)
            
            return {
                'success': True,
                'analytics': analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _get_current_usage(self, subscription_id: int) -> Optional[FeatureUsage]:
        """Get current usage for a subscription"""
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        return self.db.query(FeatureUsage).filter(
            and_(
                FeatureUsage.subscription_id == subscription_id,
                FeatureUsage.usage_month == current_month,
                FeatureUsage.usage_year == current_year
            )
        ).first()
    
    def _calculate_usage_percentage(self, usage: FeatureUsage, tier) -> float:
        """Calculate usage percentage for current tier"""
        total_usage = 0
        total_limit = 0
        
        features = ['health_checkins', 'financial_reports', 'ai_insights']
        
        for feature in features:
            feature_usage = getattr(usage, f'{feature}_used', 0)
            feature_limit = getattr(tier, f'max_{feature}_per_month', 0)
            
            if feature_limit > 0:  # Skip unlimited features
                total_usage += feature_usage
                total_limit += feature_limit
        
        return total_usage / total_limit if total_limit > 0 else 0.0
    
    def _check_feature_limits(self, usage: FeatureUsage, tier) -> List[str]:
        """Check which features are at their limits"""
        limited_features = []
        features = ['health_checkins', 'financial_reports', 'ai_insights']
        
        for feature in features:
            feature_usage = getattr(usage, f'{feature}_used', 0)
            feature_limit = getattr(tier, f'max_{feature}_per_month', 0)
            
            if feature_limit > 0 and feature_usage >= feature_limit:
                limited_features.append(feature)
        
        return limited_features
    
    def _check_consecutive_usage(self, subscription_id: int) -> int:
        """Check consecutive months of usage"""
        # This would implement logic to check historical usage
        # For now, return a placeholder value
        return 3
    
    def _check_value_indicators(self, customer: Customer, subscription: Subscription) -> List[str]:
        """Check for high-value indicators"""
        indicators = []
        
        # Check for team collaboration (multiple users)
        if hasattr(subscription, 'team_members') and subscription.team_members > 1:
            indicators.append('team_collaboration')
        
        # Check for high API usage
        current_usage = self._get_current_usage(subscription.id)
        if current_usage and current_usage.api_calls_made > 1000:
            indicators.append('high_api_usage')
        
        # Check for advanced features usage
        if subscription.pricing_tier.advanced_analytics:
            indicators.append('advanced_features')
        
        return indicators
    
    def _get_recommended_tier(self, current_tier) -> Optional[PricingTier]:
        """Get recommended upgrade tier"""
        if current_tier.tier_type.value == 'budget':
            return self.db.query(PricingTier).filter(
                PricingTier.tier_type == 'mid_tier'
            ).first()
        elif current_tier.tier_type.value == 'mid_tier':
            return self.db.query(PricingTier).filter(
                PricingTier.tier_type == 'professional'
            ).first()
        
        return None
    
    def _calculate_upgrade_value(self, subscription: Subscription, new_tier) -> float:
        """Calculate the value of upgrading to a new tier"""
        if not new_tier:
            return 0.0
        
        current_value = subscription.amount * 12  # Annual value
        new_value = new_tier.yearly_price
        
        return new_value - current_value
    
    def _create_upgrade_prompt(
        self,
        customer: Customer,
        subscription: Subscription,
        upgrade_analysis: Dict,
        prompt_type: str
    ) -> Dict[str, Any]:
        """Create personalized upgrade prompt"""
        if prompt_type == 'usage_based':
            return {
                'title': f'Unlock More Power, {customer.name}!',
                'subtitle': 'You\'re using 80% of your current plan. Upgrade to get unlimited access.',
                'message': f'Based on your usage patterns, you\'re getting great value from MINGUS! Consider upgrading to {upgrade_analysis["recommended_tier"].name} for unlimited features.',
                'benefits': [
                    'Unlimited health check-ins',
                    'Advanced AI insights',
                    'Priority support',
                    'Team collaboration features'
                ],
                'cta_text': 'Upgrade Now',
                'cta_url': f'/upgrade/{subscription.id}',
                'urgency': 'medium'
            }
        else:
            return {
                'title': 'Ready for the Next Level?',
                'subtitle': 'Upgrade your MINGUS experience',
                'message': 'Take your financial management to the next level with our advanced features.',
                'benefits': [
                    'More features and capabilities',
                    'Better support and service',
                    'Advanced analytics and insights'
                ],
                'cta_text': 'Learn More',
                'cta_url': f'/pricing',
                'urgency': 'low'
            }
    
    def _log_revenue_event(
        self,
        event_type: AuditEventType,
        customer_id: int = None,
        subscription_id: int = None,
        invoice_id: int = None,
        event_description: str = None,
        metadata: Dict = None
    ):
        """Log revenue optimization event"""
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
            logger.error(f"Failed to log revenue event: {e}") 