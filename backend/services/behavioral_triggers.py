"""
Behavioral Triggers Service for MINGUS Email Automation
Handles incomplete assessments, engagement tracking, referral requests, and feedback surveys
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from enum import Enum
import random
import json

from backend.services.email_automation_service import EmailAutomationService
from backend.models.assessment_models import Lead, AIJobAssessment
from backend.database import get_db_session

logger = logging.getLogger(__name__)

class TriggerType(Enum):
    INCOMPLETE_ASSESSMENT = "incomplete_assessment"
    ENGAGEMENT_UPGRADE = "engagement_upgrade"
    REFERRAL_REQUEST = "referral_request"
    FEEDBACK_SURVEY = "feedback_survey"
    RE_ENGAGEMENT = "re_engagement"

class EngagementLevel(Enum):
    HIGH = "high"  # Opens 80%+ emails, clicks regularly
    MEDIUM = "medium"  # Opens 50-79% emails, occasional clicks
    LOW = "low"  # Opens <50% emails, rarely clicks
    INACTIVE = "inactive"  # No engagement in 30+ days

class ABTestVariant(Enum):
    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"

class BehavioralTriggersService:
    """Service for handling behavioral email triggers and A/B testing"""
    
    def __init__(self):
        self.email_service = EmailAutomationService()
        self.ab_tests = self._load_ab_tests()
    
    def _load_ab_tests(self) -> Dict[str, Dict[str, Any]]:
        """Load A/B test configurations"""
        return {
            "welcome_subject": {
                "name": "Welcome Email Subject Line Test",
                "variants": {
                    ABTestVariant.CONTROL: "Your AI Job Impact Analysis: {{risk_level}} Risk Level",
                    ABTestVariant.VARIANT_A: "🤖 {{first_name}}, Here's Your AI Risk Assessment",
                    ABTestVariant.VARIANT_B: "{{first_name}}, Will AI Replace Your Job? Find Out Now"
                },
                "traffic_split": {ABTestVariant.CONTROL: 33, ABTestVariant.VARIANT_A: 33, ABTestVariant.VARIANT_B: 34},
                "primary_metric": "open_rate",
                "confidence_level": 0.95
            },
            "cta_button": {
                "name": "Call-to-Action Button Test",
                "variants": {
                    ABTestVariant.CONTROL: "Get Your Complete Career Protection Plan",
                    ABTestVariant.VARIANT_A: "Start My AI Career Strategy",
                    ABTestVariant.VARIANT_B: "Unlock My Career Intelligence Report"
                },
                "traffic_split": {ABTestVariant.CONTROL: 33, ABTestVariant.VARIANT_A: 33, ABTestVariant.VARIANT_B: 34},
                "primary_metric": "click_rate",
                "confidence_level": 0.95
            },
            "offer_timing": {
                "name": "Offer Timing Test",
                "variants": {
                    ABTestVariant.CONTROL: "day_14",  # Standard 14-day delay
                    ABTestVariant.VARIANT_A: "day_7",  # Early offer
                    ABTestVariant.VARIANT_B: "day_21"  # Late offer
                },
                "traffic_split": {ABTestVariant.CONTROL: 33, ABTestVariant.VARIANT_A: 33, ABTestVariant.VARIANT_B: 34},
                "primary_metric": "conversion_rate",
                "confidence_level": 0.95
            }
        }
    
    def check_incomplete_assessments(self) -> List[Dict[str, Any]]:
        """Check for users who started but didn't complete assessments"""
        try:
            db = get_db_session()
            
            # Find assessments started but not completed in the last 7 days
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            
            incomplete_assessments = db.query(AIJobAssessment).filter(
                AIJobAssessment.created_at >= cutoff_date,
                AIJobAssessment.completed == False
            ).all()
            
            triggers = []
            for assessment in incomplete_assessments:
                # Check if we've already sent a reminder
                last_reminder = self._get_last_reminder_sent(assessment.id, db)
                
                if not last_reminder or (datetime.now(timezone.utc) - last_reminder).days >= 3:
                    triggers.append({
                        'assessment_id': assessment.id,
                        'email': assessment.email,
                        'first_name': assessment.first_name,
                        'assessment_type': 'AI Job Impact Assessment',
                        'days_incomplete': (datetime.now(timezone.utc) - assessment.created_at).days,
                        'trigger_type': TriggerType.INCOMPLETE_ASSESSMENT
                    })
            
            return triggers
            
        except Exception as e:
            logger.error(f"Error checking incomplete assessments: {e}")
            return []
        finally:
            db.close()
    
    def check_engagement_levels(self) -> List[Dict[str, Any]]:
        """Check user engagement levels and trigger appropriate emails"""
        try:
            db = get_db_session()
            
            # Get users with engagement data
            users_with_engagement = self._get_users_with_engagement(db)
            
            triggers = []
            for user_data in users_with_engagement:
                engagement_level = self._calculate_engagement_level(user_data)
                
                if engagement_level == EngagementLevel.HIGH:
                    # High engagement: Send upgrade offer
                    triggers.append({
                        'user_id': user_data['user_id'],
                        'email': user_data['email'],
                        'first_name': user_data['first_name'],
                        'engagement_level': engagement_level.value,
                        'open_rate': user_data['open_rate'],
                        'click_rate': user_data['click_rate'],
                        'trigger_type': TriggerType.ENGAGEMENT_UPGRADE
                    })
                elif engagement_level == EngagementLevel.INACTIVE:
                    # Inactive: Send re-engagement email
                    triggers.append({
                        'user_id': user_data['user_id'],
                        'email': user_data['email'],
                        'first_name': user_data['first_name'],
                        'days_inactive': user_data['days_inactive'],
                        'trigger_type': TriggerType.RE_ENGAGEMENT
                    })
            
            return triggers
            
        except Exception as e:
            logger.error(f"Error checking engagement levels: {e}")
            return []
        finally:
            db.close()
    
    def check_referral_opportunities(self) -> List[Dict[str, Any]]:
        """Check for users who might be good referral candidates"""
        try:
            db = get_db_session()
            
            # Find users who completed assessments and had positive experiences
            potential_referrers = db.query(AIJobAssessment).filter(
                AIJobAssessment.completed == True,
                AIJobAssessment.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
            ).all()
            
            triggers = []
            for assessment in potential_referrers:
                # Check if they haven't been asked for referrals recently
                last_referral_request = self._get_last_referral_request(assessment.id, db)
                
                if not last_referral_request or (datetime.now(timezone.utc) - last_referral_request).days >= 14:
                    triggers.append({
                        'assessment_id': assessment.id,
                        'email': assessment.email,
                        'first_name': assessment.first_name,
                        'assessment_type': 'AI Job Impact Assessment',
                        'risk_level': assessment.overall_risk_level,
                        'trigger_type': TriggerType.REFERRAL_REQUEST
                    })
            
            return triggers
            
        except Exception as e:
            logger.error(f"Error checking referral opportunities: {e}")
            return []
        finally:
            db.close()
    
    def check_feedback_opportunities(self) -> List[Dict[str, Any]]:
        """Check for users who should be asked for feedback"""
        try:
            db = get_db_session()
            
            # Find users who completed assessments 7-14 days ago
            feedback_candidates = db.query(AIJobAssessment).filter(
                AIJobAssessment.completed == True,
                AIJobAssessment.created_at >= datetime.now(timezone.utc) - timedelta(days=14),
                AIJobAssessment.created_at <= datetime.now(timezone.utc) - timedelta(days=7)
            ).all()
            
            triggers = []
            for assessment in feedback_candidates:
                # Check if they haven't been asked for feedback
                feedback_requested = self._get_feedback_requested(assessment.id, db)
                
                if not feedback_requested:
                    triggers.append({
                        'assessment_id': assessment.id,
                        'email': assessment.email,
                        'first_name': assessment.first_name,
                        'assessment_type': 'AI Job Impact Assessment',
                        'days_since_completion': (datetime.now(timezone.utc) - assessment.created_at).days,
                        'trigger_type': TriggerType.FEEDBACK_SURVEY
                    })
            
            return triggers
            
        except Exception as e:
            logger.error(f"Error checking feedback opportunities: {e}")
            return []
        finally:
            db.close()
    
    def process_behavioral_triggers(self) -> Dict[str, int]:
        """Process all behavioral triggers and return summary"""
        try:
            results = {
                'incomplete_assessments': 0,
                'engagement_upgrades': 0,
                'referral_requests': 0,
                'feedback_surveys': 0,
                're_engagement': 0
            }
            
            # Process incomplete assessments
            incomplete_triggers = self.check_incomplete_assessments()
            for trigger in incomplete_triggers:
                if self._send_incomplete_assessment_email(trigger):
                    results['incomplete_assessments'] += 1
            
            # Process engagement-based triggers
            engagement_triggers = self.check_engagement_levels()
            for trigger in engagement_triggers:
                if trigger['trigger_type'] == TriggerType.ENGAGEMENT_UPGRADE:
                    if self._send_engagement_upgrade_email(trigger):
                        results['engagement_upgrades'] += 1
                elif trigger['trigger_type'] == TriggerType.RE_ENGAGEMENT:
                    if self._send_re_engagement_email(trigger):
                        results['re_engagement'] += 1
            
            # Process referral requests
            referral_triggers = self.check_referral_opportunities()
            for trigger in referral_triggers:
                if self._send_referral_request_email(trigger):
                    results['referral_requests'] += 1
            
            # Process feedback surveys
            feedback_triggers = self.check_feedback_opportunities()
            for trigger in feedback_triggers:
                if self._send_feedback_survey_email(trigger):
                    results['feedback_surveys'] += 1
            
            logger.info(f"Behavioral triggers processed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing behavioral triggers: {e}")
            return {}
    
    def get_ab_test_variant(self, test_name: str, user_id: str) -> ABTestVariant:
        """Get A/B test variant for a user"""
        try:
            if test_name not in self.ab_tests:
                return ABTestVariant.CONTROL
            
            # Use user_id to consistently assign variants
            hash_value = hash(user_id) % 100
            cumulative = 0
            
            test_config = self.ab_tests[test_name]
            for variant, percentage in test_config['traffic_split'].items():
                cumulative += percentage
                if hash_value < cumulative:
                    return variant
            
            return ABTestVariant.CONTROL
            
        except Exception as e:
            logger.error(f"Error getting A/B test variant: {e}")
            return ABTestVariant.CONTROL
    
    def track_ab_test_result(self, test_name: str, variant: ABTestVariant, metric: str, value: float) -> bool:
        """Track A/B test results"""
        try:
            # This would save to A/B test results table
            logger.info(f"A/B test result tracked: {test_name} - {variant.value} - {metric}: {value}")
            return True
        except Exception as e:
            logger.error(f"Error tracking A/B test result: {e}")
            return False
    
    def _send_incomplete_assessment_email(self, trigger: Dict[str, Any]) -> bool:
        """Send incomplete assessment reminder email"""
        try:
            # Get A/B test variant for subject line
            variant = self.get_ab_test_variant("welcome_subject", trigger['assessment_id'])
            
            # Create assessment object for email service
            assessment = AIJobAssessment(
                id=trigger['assessment_id'],
                email=trigger['email'],
                first_name=trigger['first_name'],
                assessment_type=trigger['assessment_type']
            )
            
            # Send email with A/B test variant
            success = self.email_service._send_welcome_email(assessment, "incomplete_assessment", None)
            
            if success:
                self._log_trigger_sent(trigger['assessment_id'], TriggerType.INCOMPLETE_ASSESSMENT, variant)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending incomplete assessment email: {e}")
            return False
    
    def _send_engagement_upgrade_email(self, trigger: Dict[str, Any]) -> bool:
        """Send engagement-based upgrade offer email"""
        try:
            # Create assessment object for email service
            assessment = AIJobAssessment(
                id=trigger['user_id'],
                email=trigger['email'],
                first_name=trigger['first_name']
            )
            
            # Send engagement upgrade email
            success = self.email_service._send_welcome_email(assessment, "engagement_upgrade", None)
            
            if success:
                self._log_trigger_sent(trigger['user_id'], TriggerType.ENGAGEMENT_UPGRADE)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending engagement upgrade email: {e}")
            return False
    
    def _send_referral_request_email(self, trigger: Dict[str, Any]) -> bool:
        """Send referral request email"""
        try:
            # Create assessment object for email service
            assessment = AIJobAssessment(
                id=trigger['assessment_id'],
                email=trigger['email'],
                first_name=trigger['first_name'],
                assessment_type=trigger['assessment_type']
            )
            
            # Send referral request email
            success = self.email_service._send_welcome_email(assessment, "referral_request", None)
            
            if success:
                self._log_trigger_sent(trigger['assessment_id'], TriggerType.REFERRAL_REQUEST)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending referral request email: {e}")
            return False
    
    def _send_feedback_survey_email(self, trigger: Dict[str, Any]) -> bool:
        """Send feedback survey email"""
        try:
            # Create assessment object for email service
            assessment = AIJobAssessment(
                id=trigger['assessment_id'],
                email=trigger['email'],
                first_name=trigger['first_name'],
                assessment_type=trigger['assessment_type']
            )
            
            # Send feedback survey email
            success = self.email_service._send_welcome_email(assessment, "feedback_survey", None)
            
            if success:
                self._log_trigger_sent(trigger['assessment_id'], TriggerType.FEEDBACK_SURVEY)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending feedback survey email: {e}")
            return False
    
    def _send_re_engagement_email(self, trigger: Dict[str, Any]) -> bool:
        """Send re-engagement email"""
        try:
            # Create assessment object for email service
            assessment = AIJobAssessment(
                id=trigger['user_id'],
                email=trigger['email'],
                first_name=trigger['first_name']
            )
            
            # Send re-engagement email
            success = self.email_service._send_welcome_email(assessment, "re_engagement", None)
            
            if success:
                self._log_trigger_sent(trigger['user_id'], TriggerType.RE_ENGAGEMENT)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending re-engagement email: {e}")
            return False
    
    def _calculate_engagement_level(self, user_data: Dict[str, Any]) -> EngagementLevel:
        """Calculate user engagement level based on email metrics"""
        open_rate = user_data.get('open_rate', 0)
        click_rate = user_data.get('click_rate', 0)
        days_inactive = user_data.get('days_inactive', 0)
        
        if days_inactive > 30:
            return EngagementLevel.INACTIVE
        elif open_rate >= 0.8 and click_rate >= 0.1:
            return EngagementLevel.HIGH
        elif open_rate >= 0.5:
            return EngagementLevel.MEDIUM
        else:
            return EngagementLevel.LOW
    
    def _get_users_with_engagement(self, db) -> List[Dict[str, Any]]:
        """Get users with engagement data"""
        # This would query the email_logs table for engagement metrics
        # For now, return mock data
        return [
            {
                'user_id': 'user1',
                'email': 'user1@example.com',
                'first_name': 'John',
                'open_rate': 0.85,
                'click_rate': 0.15,
                'days_inactive': 0
            }
        ]
    
    def _get_last_reminder_sent(self, assessment_id: str, db) -> Optional[datetime]:
        """Get the last reminder sent for an assessment"""
        # This would query the email_logs table
        return None
    
    def _get_last_referral_request(self, assessment_id: str, db) -> Optional[datetime]:
        """Get the last referral request sent for an assessment"""
        # This would query the email_logs table
        return None
    
    def _get_feedback_requested(self, assessment_id: str, db) -> bool:
        """Check if feedback was already requested for an assessment"""
        # This would query the email_logs table
        return False
    
    def _log_trigger_sent(self, user_id: str, trigger_type: TriggerType, variant: ABTestVariant = None) -> None:
        """Log that a trigger was sent"""
        logger.info(f"Trigger sent: {trigger_type.value} for user {user_id} (variant: {variant.value if variant else 'none'})")
