"""
AI Calculator Email Marketing Service
Dedicated email sequences for AI calculator leads with risk-based segmentation
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.models.ai_job_models import AIJobAssessment, AICalculatorConversion
from backend.models.ai_user_profile_extension import AIUserProfileExtension
from backend.services.resend_email_service import ResendEmailService
from backend.utils.validation import validate_email_format

logger = logging.getLogger(__name__)


class AICalculatorEmailService:
    """Email marketing service for AI calculator leads"""
    
    def __init__(self):
        self.resend_service = ResendEmailService()
        
        # Email sequence templates
        self.email_templates = {
            'welcome': {
                'subject': 'Your AI Job Risk Assessment Results Are Ready! 🤖',
                'template_id': 'ai_calculator_welcome'
            },
            'high_risk_followup': {
                'subject': '🚨 High Risk Alert: Your Career Needs Immediate Attention',
                'template_id': 'ai_calculator_high_risk'
            },
            'medium_risk_followup': {
                'subject': '⚠️ Medium Risk: Proactive Steps for Your Career',
                'template_id': 'ai_calculator_medium_risk'
            },
            'low_risk_followup': {
                'subject': '✅ Low Risk: How to Stay Ahead of AI Changes',
                'template_id': 'ai_calculator_low_risk'
            },
            'career_plan_offer': {
                'subject': '🎯 Your Personalized AI-Proof Career Plan (Only $27)',
                'template_id': 'ai_calculator_career_plan'
            },
            'industry_insights': {
                'subject': '📊 Industry-Specific AI Insights for {industry}',
                'template_id': 'ai_calculator_industry_insights'
            },
            'skill_development': {
                'subject': '🚀 AI-Proof Skills: Your Personalized Learning Path',
                'template_id': 'ai_calculator_skill_development'
            },
            'conversion_reminder': {
                'subject': '⏰ Last Chance: Secure Your AI-Proof Career Plan',
                'template_id': 'ai_calculator_conversion_reminder'
            }
        }
        
        # Industry-specific content
        self.industry_content = {
            'technology': {
                'title': 'Tech Industry AI Impact',
                'key_skills': ['AI/ML Development', 'Cloud Architecture', 'DevOps', 'Data Science'],
                'risk_factors': ['Automated coding', 'AI-powered testing', 'Low-code platforms'],
                'opportunities': ['AI tool development', 'MLOps', 'AI ethics', 'Edge computing']
            },
            'healthcare': {
                'title': 'Healthcare AI Transformation',
                'key_skills': ['Clinical AI', 'Healthcare Data Analytics', 'Telemedicine', 'Regulatory Compliance'],
                'risk_factors': ['AI diagnostics', 'Automated patient care', 'Administrative automation'],
                'opportunities': ['AI-assisted diagnosis', 'Precision medicine', 'Healthcare AI ethics', 'Patient data security']
            },
            'finance': {
                'title': 'Financial Services AI Revolution',
                'key_skills': ['FinTech', 'Risk Analytics', 'RegTech', 'Blockchain'],
                'risk_factors': ['Automated trading', 'AI credit scoring', 'Robo-advisors'],
                'opportunities': ['AI risk management', 'Regulatory compliance', 'Financial inclusion', 'Cryptocurrency']
            },
            'marketing': {
                'title': 'Marketing AI Evolution',
                'key_skills': ['Marketing Automation', 'Data Analytics', 'Content Strategy', 'Customer Experience'],
                'risk_factors': ['AI content generation', 'Automated ad buying', 'Chatbot marketing'],
                'opportunities': ['Personalization at scale', 'Predictive analytics', 'Voice search optimization', 'AR/VR marketing']
            },
            'education': {
                'title': 'Education AI Integration',
                'key_skills': ['EdTech', 'Learning Analytics', 'Curriculum Design', 'Student Assessment'],
                'risk_factors': ['AI tutoring', 'Automated grading', 'Online learning platforms'],
                'opportunities': ['Personalized learning', 'AI-powered assessment', 'Virtual classrooms', 'Lifelong learning platforms']
            }
        }
    
    def send_welcome_email(self, assessment: AIJobAssessment, db: Session) -> bool:
        """Send welcome email with assessment results"""
        try:
            template_data = {
                'first_name': assessment.first_name,
                'job_title': assessment.job_title,
                'industry': assessment.industry,
                'risk_level': assessment.overall_risk_level,
                'automation_score': assessment.automation_score,
                'augmentation_score': assessment.augmentation_score,
                'assessment_id': str(assessment.id)
            }
            
            # Add industry-specific content
            if assessment.industry.lower() in self.industry_content:
                industry_data = self.industry_content[assessment.industry.lower()]
                template_data.update({
                    'industry_title': industry_data['title'],
                    'key_skills': industry_data['key_skills'],
                    'risk_factors': industry_data['risk_factors'],
                    'opportunities': industry_data['opportunities']
                })
            
            success = self.resend_service.send_email(
                to_email=assessment.email,
                subject=self.email_templates['welcome']['subject'],
                template_id=self.email_templates['welcome']['template_id'],
                template_data=template_data
            )
            
            if success:
                self._log_email_sent(assessment.id, 'welcome', db)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
            return False
    
    def send_risk_based_followup(self, assessment: AIJobAssessment, db: Session) -> bool:
        """Send risk-level specific follow-up email"""
        try:
            risk_level = assessment.overall_risk_level.lower()
            
            if risk_level == 'high':
                template_key = 'high_risk_followup'
                delay_hours = 24  # Send high-risk follow-up quickly
            elif risk_level == 'medium':
                template_key = 'medium_risk_followup'
                delay_hours = 48
            else:  # low risk
                template_key = 'low_risk_followup'
                delay_hours = 72
            
            template_data = {
                'first_name': assessment.first_name,
                'job_title': assessment.job_title,
                'industry': assessment.industry,
                'risk_level': assessment.overall_risk_level,
                'mitigation_strategies': assessment.mitigation_strategies,
                'recommended_skills': assessment.recommended_skills,
                'assessment_id': str(assessment.id)
            }
            
            success = self.resend_service.send_email(
                to_email=assessment.email,
                subject=self.email_templates[template_key]['subject'],
                template_id=self.email_templates[template_key]['template_id'],
                template_data=template_data
            )
            
            if success:
                self._log_email_sent(assessment.id, template_key, db)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending risk-based followup: {e}")
            return False
    
    def send_career_plan_offer(self, assessment: AIJobAssessment, db: Session) -> bool:
        """Send career plan purchase offer"""
        try:
            template_data = {
                'first_name': assessment.first_name,
                'job_title': assessment.job_title,
                'industry': assessment.industry,
                'risk_level': assessment.overall_risk_level,
                'assessment_id': str(assessment.id),
                'offer_price': 27,
                'offer_url': f"/api/ai-calculator/career-plan/{assessment.id}"
            }
            
            success = self.resend_service.send_email(
                to_email=assessment.email,
                subject=self.email_templates['career_plan_offer']['subject'],
                template_id=self.email_templates['career_plan_offer']['template_id'],
                template_data=template_data
            )
            
            if success:
                self._log_email_sent(assessment.id, 'career_plan_offer', db)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending career plan offer: {e}")
            return False
    
    def send_industry_insights(self, assessment: AIJobAssessment, db: Session) -> bool:
        """Send industry-specific AI insights"""
        try:
            industry = assessment.industry.lower()
            
            if industry not in self.industry_content:
                return False  # Skip if no industry-specific content
            
            industry_data = self.industry_content[industry]
            
            template_data = {
                'first_name': assessment.first_name,
                'industry': assessment.industry,
                'industry_title': industry_data['title'],
                'key_skills': industry_data['key_skills'],
                'risk_factors': industry_data['risk_factors'],
                'opportunities': industry_data['opportunities'],
                'assessment_id': str(assessment.id)
            }
            
            subject = self.email_templates['industry_insights']['subject'].format(
                industry=assessment.industry
            )
            
            success = self.resend_service.send_email(
                to_email=assessment.email,
                subject=subject,
                template_id=self.email_templates['industry_insights']['template_id'],
                template_data=template_data
            )
            
            if success:
                self._log_email_sent(assessment.id, 'industry_insights', db)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending industry insights: {e}")
            return False
    
    def send_conversion_reminder(self, assessment: AIJobAssessment, db: Session) -> bool:
        """Send final conversion reminder"""
        try:
            # Check if user has already converted
            existing_conversion = db.query(AICalculatorConversion).filter(
                and_(
                    AICalculatorConversion.assessment_id == assessment.id,
                    AICalculatorConversion.conversion_type == 'paid_upgrade'
                )
            ).first()
            
            if existing_conversion:
                return False  # Already converted
            
            template_data = {
                'first_name': assessment.first_name,
                'job_title': assessment.job_title,
                'industry': assessment.industry,
                'risk_level': assessment.overall_risk_level,
                'assessment_id': str(assessment.id),
                'offer_price': 27,
                'offer_url': f"/api/ai-calculator/career-plan/{assessment.id}"
            }
            
            success = self.resend_service.send_email(
                to_email=assessment.email,
                subject=self.email_templates['conversion_reminder']['subject'],
                template_id=self.email_templates['conversion_reminder']['template_id'],
                template_data=template_data
            )
            
            if success:
                self._log_email_sent(assessment.id, 'conversion_reminder', db)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending conversion reminder: {e}")
            return False
    
    def schedule_email_sequence(self, assessment: AIJobAssessment, db: Session) -> bool:
        """Schedule the complete email sequence for a new assessment"""
        try:
            # Send welcome email immediately
            self.send_welcome_email(assessment, db)
            
            # Schedule follow-up emails based on risk level
            risk_level = assessment.overall_risk_level.lower()
            
            if risk_level == 'high':
                # High risk: More aggressive sequence
                self._schedule_delayed_email(assessment.id, 'high_risk_followup', 24, db)
                self._schedule_delayed_email(assessment.id, 'career_plan_offer', 48, db)
                self._schedule_delayed_email(assessment.id, 'conversion_reminder', 120, db)
            elif risk_level == 'medium':
                # Medium risk: Balanced sequence
                self._schedule_delayed_email(assessment.id, 'medium_risk_followup', 48, db)
                self._schedule_delayed_email(assessment.id, 'industry_insights', 96, db)
                self._schedule_delayed_email(assessment.id, 'career_plan_offer', 144, db)
                self._schedule_delayed_email(assessment.id, 'conversion_reminder', 168, db)
            else:
                # Low risk: Gentle sequence
                self._schedule_delayed_email(assessment.id, 'low_risk_followup', 72, db)
                self._schedule_delayed_email(assessment.id, 'industry_insights', 144, db)
                self._schedule_delayed_email(assessment.id, 'skill_development', 216, db)
                self._schedule_delayed_email(assessment.id, 'career_plan_offer', 240, db)
            
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling email sequence: {e}")
            return False
    
    def _schedule_delayed_email(self, assessment_id: str, email_type: str, delay_hours: int, db: Session) -> None:
        """Schedule a delayed email (placeholder for actual scheduling system)"""
        # This would integrate with a task queue like Celery
        # For now, we'll just log the scheduled email
        scheduled_time = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
        logger.info(f"Scheduled {email_type} email for assessment {assessment_id} at {scheduled_time}")
    
    def _log_email_sent(self, assessment_id: str, email_type: str, db: Session) -> None:
        """Log email sent for analytics"""
        try:
            # Create conversion record for email tracking
            conversion = AICalculatorConversion(
                assessment_id=assessment_id,
                conversion_type='email_sent',
                conversion_value=0.0,
                conversion_source='email_marketing',
                conversion_medium='email',
                conversion_campaign=f'ai_calculator_{email_type}'
            )
            
            db.add(conversion)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging email sent: {e}")
            db.rollback()
    
    def get_email_analytics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """Get email marketing analytics"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get email conversion data
            email_conversions = db.query(AICalculatorConversion).filter(
                and_(
                    AICalculatorConversion.conversion_type == 'email_sent',
                    AICalculatorConversion.created_at >= cutoff_date
                )
            ).all()
            
            # Get paid conversions
            paid_conversions = db.query(AICalculatorConversion).filter(
                and_(
                    AICalculatorConversion.conversion_type == 'paid_upgrade',
                    AICalculatorConversion.created_at >= cutoff_date
                )
            ).all()
            
            # Calculate metrics
            total_emails_sent = len(email_conversions)
            total_paid_conversions = len(paid_conversions)
            total_revenue = sum(conv.conversion_revenue for conv in paid_conversions)
            
            # Email performance by type
            email_performance = {}
            for conv in email_conversions:
                campaign = conv.conversion_campaign
                if campaign not in email_performance:
                    email_performance[campaign] = 0
                email_performance[campaign] += 1
            
            return {
                'total_emails_sent': total_emails_sent,
                'total_paid_conversions': total_paid_conversions,
                'total_revenue': float(total_revenue),
                'conversion_rate': (total_paid_conversions / total_emails_sent * 100) if total_emails_sent > 0 else 0,
                'email_performance': email_performance,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting email analytics: {e}")
            return {}
