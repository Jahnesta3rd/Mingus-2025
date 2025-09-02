"""
AI Calculator Payment Service
Payment processing for AI Career Plan product ($27)
"""

import logging
import stripe
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.models.ai_job_models import AIJobAssessment, AICalculatorConversion
from backend.models.ai_user_profile_extension import AIUserProfileExtension
from backend.payment.stripe_integration import StripeService
from backend.services.reporting_service import ReportingService
from backend.utils.validation import validate_email_format

logger = logging.getLogger(__name__)


class AICalculatorPaymentService:
    """Payment service for AI calculator career plan product"""
    
    def __init__(self):
        self.stripe_service = StripeService()
        self.reporting_service = ReportingService()
        
        # AI Career Plan product configuration
        self.career_plan_product = {
            'name': 'AI-Proof Career Plan',
            'description': 'Personalized career strategy to stay ahead of AI changes',
            'price': 2700,  # $27.00 in cents
            'currency': 'usd',
            'stripe_price_id': 'price_ai_career_plan_monthly',  # Would be created in Stripe
            'features': [
                'Personalized AI risk assessment',
                'Custom skill development roadmap',
                'Industry-specific insights',
                'Career transition strategies',
                'Ongoing risk monitoring',
                'Priority support'
            ]
        }
    
    def create_career_plan_checkout_session(self, assessment: AIJobAssessment, db: Session) -> Dict[str, Any]:
        """Create Stripe checkout session for AI Career Plan"""
        try:
            # Create or get customer
            customer = self._get_or_create_customer(assessment, db)
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': self.career_plan_product['stripe_price_id'],
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"/api/ai-calculator/payment/success?session_id={{CHECKOUT_SESSION_ID}}&assessment_id={assessment.id}",
                cancel_url=f"/api/ai-calculator/payment/cancel?assessment_id={assessment.id}",
                metadata={
                    'assessment_id': str(assessment.id),
                    'product_type': 'ai_career_plan',
                    'user_email': assessment.email,
                    'risk_level': assessment.overall_risk_level,
                    'industry': assessment.industry
                }
            )
            
            # Track checkout session creation
            self._track_checkout_session(assessment.id, checkout_session.id, db)
            
            return {
                'success': True,
                'checkout_session_id': checkout_session.id,
                'checkout_url': checkout_session.url,
                'amount': self.career_plan_product['price'],
                'currency': self.career_plan_product['currency']
            }
            
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_payment_success(self, session_id: str, assessment_id: str, db: Session) -> Dict[str, Any]:
        """Process successful payment and generate career plan"""
        try:
            # Retrieve checkout session
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status != 'paid':
                return {'success': False, 'error': 'Payment not completed'}
            
            # Get assessment
            assessment = db.query(AIJobAssessment).filter(
                AIJobAssessment.id == assessment_id
            ).first()
            
            if not assessment:
                return {'success': False, 'error': 'Assessment not found'}
            
            # Create conversion record
            conversion = AICalculatorConversion(
                assessment_id=assessment_id,
                conversion_type='paid_upgrade',
                conversion_value=float(self.career_plan_product['price']) / 100,
                conversion_revenue=float(self.career_plan_product['price']) / 100,
                conversion_source='stripe_checkout',
                conversion_medium='web',
                conversion_campaign='ai_career_plan',
                touchpoints_before_conversion=1,
                days_to_conversion=0,
                conversion_funnel_stage='purchase'
            )
            
            db.add(conversion)
            
            # Update user profile extension if user exists
            if assessment.user_id:
                self._update_user_profile_extension(assessment, db)
            
            # Generate career plan PDF
            pdf_url = self._generate_career_plan_pdf(assessment, db)
            
            # Send confirmation email
            self._send_payment_confirmation(assessment, pdf_url, db)
            
            db.commit()
            
            return {
                'success': True,
                'pdf_url': pdf_url,
                'conversion_id': str(conversion.id),
                'amount_paid': float(self.career_plan_product['price']) / 100
            }
            
        except Exception as e:
            logger.error(f"Error processing payment success: {e}")
            db.rollback()
            return {'success': False, 'error': str(e)}
    
    def _get_or_create_customer(self, assessment: AIJobAssessment, db: Session) -> stripe.Customer:
        """Get existing Stripe customer or create new one"""
        try:
            # Check if customer already exists
            existing_customers = stripe.Customer.list(email=assessment.email, limit=1)
            
            if existing_customers.data:
                return existing_customers.data[0]
            
            # Create new customer
            customer = stripe.Customer.create(
                email=assessment.email,
                name=assessment.first_name,
                metadata={
                    'assessment_id': str(assessment.id),
                    'source': 'ai_calculator',
                    'risk_level': assessment.overall_risk_level
                }
            )
            
            return customer
            
        except Exception as e:
            logger.error(f"Error creating/getting customer: {e}")
            raise
    
    def _track_checkout_session(self, assessment_id: str, session_id: str, db: Session) -> None:
        """Track checkout session creation for analytics"""
        try:
            conversion = AICalculatorConversion(
                assessment_id=assessment_id,
                conversion_type='checkout_session_created',
                conversion_value=0.0,
                conversion_source='stripe_checkout',
                conversion_medium='web',
                conversion_campaign='ai_career_plan',
                conversion_funnel_stage='checkout'
            )
            
            db.add(conversion)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking checkout session: {e}")
            db.rollback()
    
    def _update_user_profile_extension(self, assessment: AIJobAssessment, db: Session) -> None:
        """Update user profile extension with AI career plan purchase"""
        try:
            profile_extension = db.query(AIUserProfileExtension).filter(
                AIUserProfileExtension.user_id == assessment.user_id
            ).first()
            
            if not profile_extension:
                # Create new profile extension
                profile_extension = AIUserProfileExtension(
                    user_id=assessment.user_id,
                    latest_ai_assessment_id=assessment.id,
                    overall_risk_level=assessment.overall_risk_level,
                    automation_score=assessment.automation_score,
                    augmentation_score=assessment.augmentation_score,
                    ai_assessment_completed=True,
                    ai_assessment_completion_date=assessment.completed_at,
                    ai_onboarding_step='completed',
                    ai_career_insights_enabled=True
                )
                db.add(profile_extension)
            else:
                # Update existing profile extension
                profile_extension.latest_ai_assessment_id = assessment.id
                profile_extension.overall_risk_level = assessment.overall_risk_level
                profile_extension.automation_score = assessment.automation_score
                profile_extension.augmentation_score = assessment.augmentation_score
                profile_extension.ai_assessment_completed = True
                profile_extension.ai_assessment_completion_date = assessment.completed_at
                profile_extension.ai_onboarding_step = 'completed'
                profile_extension.ai_career_insights_enabled = True
                profile_extension.ai_assessment_count += 1
                profile_extension.last_ai_assessment_date = assessment.completed_at
            
        except Exception as e:
            logger.error(f"Error updating user profile extension: {e}")
            raise
    
    def _generate_career_plan_pdf(self, assessment: AIJobAssessment, db: Session) -> str:
        """Generate personalized career plan PDF"""
        try:
            # Prepare data for PDF generation
            pdf_data = {
                'assessment_id': str(assessment.id),
                'user_name': assessment.first_name,
                'job_title': assessment.job_title,
                'industry': assessment.industry,
                'experience_level': assessment.experience_level,
                'risk_level': assessment.overall_risk_level,
                'automation_score': assessment.automation_score,
                'augmentation_score': assessment.augmentation_score,
                'risk_factors': assessment.risk_factors,
                'mitigation_strategies': assessment.mitigation_strategies,
                'recommended_skills': assessment.recommended_skills,
                'career_advice': assessment.career_advice,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'product_name': self.career_plan_product['name'],
                'product_features': self.career_plan_product['features']
            }
            
            # Generate PDF using existing reporting service
            pdf_url = self.reporting_service.generate_ai_career_plan_pdf(pdf_data)
            
            return pdf_url
            
        except Exception as e:
            logger.error(f"Error generating career plan PDF: {e}")
            return ""
    
    def _send_payment_confirmation(self, assessment: AIJobAssessment, pdf_url: str, db: Session) -> None:
        """Send payment confirmation email with career plan"""
        try:
            from backend.services.ai_calculator_email_service import AICalculatorEmailService
            
            email_service = AICalculatorEmailService()
            
            # Send confirmation email with PDF
            template_data = {
                'first_name': assessment.first_name,
                'job_title': assessment.job_title,
                'industry': assessment.industry,
                'risk_level': assessment.overall_risk_level,
                'pdf_url': pdf_url,
                'product_name': self.career_plan_product['name'],
                'product_features': self.career_plan_product['features']
            }
            
            email_service.resend_service.send_email(
                to_email=assessment.email,
                subject='🎯 Your AI-Proof Career Plan is Ready!',
                template_id='ai_career_plan_confirmation',
                template_data=template_data
            )
            
        except Exception as e:
            logger.error(f"Error sending payment confirmation: {e}")
    
    def get_payment_analytics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get payment and revenue analytics"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get all paid conversions
            conversions = db.query(AICalculatorConversion).filter(
                and_(
                    AICalculatorConversion.conversion_type == 'paid_upgrade',
                    AICalculatorConversion.created_at >= cutoff_date
                )
            ).all()
            
            # Calculate metrics
            total_conversions = len(conversions)
            total_revenue = sum(conv.conversion_revenue for conv in conversions)
            average_order_value = total_revenue / total_conversions if total_conversions > 0 else 0
            
            # Revenue by risk level
            revenue_by_risk = {}
            for conv in conversions:
                assessment = db.query(AIJobAssessment).filter(
                    AIJobAssessment.id == conv.assessment_id
                ).first()
                if assessment:
                    risk_level = assessment.overall_risk_level
                    if risk_level not in revenue_by_risk:
                        revenue_by_risk[risk_level] = {'conversions': 0, 'revenue': 0}
                    revenue_by_risk[risk_level]['conversions'] += 1
                    revenue_by_risk[risk_level]['revenue'] += float(conv.conversion_revenue)
            
            # Revenue by industry
            revenue_by_industry = {}
            for conv in conversions:
                assessment = db.query(AIJobAssessment).filter(
                    AIJobAssessment.id == conv.assessment_id
                ).first()
                if assessment:
                    industry = assessment.industry
                    if industry not in revenue_by_industry:
                        revenue_by_industry[industry] = {'conversions': 0, 'revenue': 0}
                    revenue_by_industry[industry]['conversions'] += 1
                    revenue_by_industry[industry]['revenue'] += float(conv.conversion_revenue)
            
            return {
                'period_days': days,
                'total_conversions': total_conversions,
                'total_revenue': float(total_revenue),
                'average_order_value': float(average_order_value),
                'revenue_by_risk': revenue_by_risk,
                'revenue_by_industry': revenue_by_industry,
                'conversion_rate': self._calculate_conversion_rate(db, cutoff_date)
            }
            
        except Exception as e:
            logger.error(f"Error getting payment analytics: {e}")
            return {}
    
    def _calculate_conversion_rate(self, db: Session, cutoff_date: datetime) -> float:
        """Calculate conversion rate from assessment to purchase"""
        try:
            total_assessments = db.query(AIJobAssessment).filter(
                and_(
                    AIJobAssessment.created_at >= cutoff_date,
                    AIJobAssessment.completed_at.isnot(None)
                )
            ).count()
            
            total_conversions = db.query(AICalculatorConversion).filter(
                and_(
                    AICalculatorConversion.conversion_type == 'paid_upgrade',
                    AICalculatorConversion.created_at >= cutoff_date
                )
            ).count()
            
            return (total_conversions / total_assessments * 100) if total_assessments > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating conversion rate: {e}")
            return 0.0
    
    def create_subscription_upgrade_offer(self, assessment: AIJobAssessment, db: Session) -> Dict[str, Any]:
        """Create upgrade offer to include AI career insights in existing subscription"""
        try:
            # Check if user has existing subscription
            if not assessment.user_id:
                return {'success': False, 'error': 'User not authenticated'}
            
            # Get user's current subscription tier
            user_subscription = self.stripe_service.get_user_subscription(assessment.user_id)
            
            if not user_subscription:
                return {'success': False, 'error': 'No existing subscription found'}
            
            # Create upgrade offer
            upgrade_offer = {
                'current_tier': user_subscription.tier,
                'upgrade_price': 500,  # $5.00 additional per month
                'new_features': [
                    'AI Career Risk Monitoring',
                    'Personalized Skill Development',
                    'Industry AI Insights',
                    'Career Transition Planning'
                ],
                'upgrade_url': f"/api/ai-calculator/upgrade-subscription?assessment_id={assessment.id}"
            }
            
            return {
                'success': True,
                'upgrade_offer': upgrade_offer
            }
            
        except Exception as e:
            logger.error(f"Error creating upgrade offer: {e}")
            return {'success': False, 'error': str(e)}
