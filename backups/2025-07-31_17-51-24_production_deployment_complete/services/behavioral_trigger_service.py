"""
Behavioral Trigger Service
Handles intelligent trigger detection and contextual communication initiation
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import json
import statistics
from decimal import Decimal

from ..models.behavioral_triggers import (
    BehavioralTrigger, TriggerEvent, TriggerEffectiveness, UserBehaviorPattern,
    MLModel, TriggerTemplate, TriggerSchedule, TriggerType, TriggerCategory,
    TriggerStatus, TriggerPriority
)
from ..models.communication_preferences import (
    CommunicationPreferences, AlertType, CommunicationChannel
)
from ..models.communication_analytics import (
    CommunicationMetrics, UserEngagementAnalytics, FinancialImpactMetrics
)
from ..models.user import User
from ..database import get_db_session

logger = logging.getLogger(__name__)


class BehavioralTriggerService:
    """Service for intelligent behavioral trigger detection and management"""
    
    def __init__(self):
        self.db: Session = get_db_session()
    
    def detect_financial_triggers(self, user_id: str, financial_data: Dict[str, Any]) -> List[TriggerEvent]:
        """
        Detect financial behavior triggers for a user
        
        Args:
            user_id: User ID
            financial_data: Current financial data
            
        Returns:
            List of triggered events
        """
        try:
            triggered_events = []
            
            # Get user's behavior patterns
            patterns = self._get_user_patterns(user_id, 'financial')
            
            # Check for spending spike
            if self._detect_spending_spike(user_id, financial_data, patterns):
                event = self._create_trigger_event(
                    user_id, 'spending_spike', financial_data, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for income drop
            if self._detect_income_drop(user_id, financial_data, patterns):
                event = self._create_trigger_event(
                    user_id, 'income_drop', financial_data, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for savings stall
            if self._detect_savings_stall(user_id, financial_data, patterns):
                event = self._create_trigger_event(
                    user_id, 'savings_stall', financial_data, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for milestone reached
            if self._detect_milestone_reached(user_id, financial_data):
                event = self._create_trigger_event(
                    user_id, 'milestone_reached', financial_data, 'rule_based'
                )
                triggered_events.append(event)
            
            return triggered_events
            
        except Exception as e:
            logger.error(f"Error detecting financial triggers for user {user_id}: {e}")
            raise
    
    def detect_health_wellness_triggers(self, user_id: str, health_data: Dict[str, Any], 
                                      financial_data: Dict[str, Any]) -> List[TriggerEvent]:
        """
        Detect health/wellness correlation triggers
        
        Args:
            user_id: User ID
            health_data: Current health data
            financial_data: Current financial data
            
        Returns:
            List of triggered events
        """
        try:
            triggered_events = []
            
            # Check for low exercise + high spending correlation
            if self._detect_low_exercise_high_spending(user_id, health_data, financial_data):
                event = self._create_trigger_event(
                    user_id, 'low_exercise_high_spending', 
                    {'health': health_data, 'financial': financial_data}, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for high stress + financial decisions
            if self._detect_high_stress_financial(user_id, health_data, financial_data):
                event = self._create_trigger_event(
                    user_id, 'high_stress_financial',
                    {'health': health_data, 'financial': financial_data}, 'rule_based'
                )
                triggered_events.append(event)
            
            return triggered_events
            
        except Exception as e:
            logger.error(f"Error detecting health/wellness triggers for user {user_id}: {e}")
            raise
    
    def detect_career_triggers(self, user_id: str, career_data: Dict[str, Any]) -> List[TriggerEvent]:
        """
        Detect career advancement triggers
        
        Args:
            user_id: User ID
            career_data: Current career data
            
        Returns:
            List of triggered events
        """
        try:
            triggered_events = []
            
            # Check for job opportunities
            if self._detect_job_opportunities(user_id, career_data):
                event = self._create_trigger_event(
                    user_id, 'job_opportunity', career_data, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for skill gaps
            if self._detect_skill_gaps(user_id, career_data):
                event = self._create_trigger_event(
                    user_id, 'skill_gap', career_data, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for salary below market
            if self._detect_salary_below_market(user_id, career_data):
                event = self._create_trigger_event(
                    user_id, 'salary_below_market', career_data, 'rule_based'
                )
                triggered_events.append(event)
            
            return triggered_events
            
        except Exception as e:
            logger.error(f"Error detecting career triggers for user {user_id}: {e}")
            raise
    
    def detect_life_event_triggers(self, user_id: str, user_profile: Dict[str, Any]) -> List[TriggerEvent]:
        """
        Detect life event triggers
        
        Args:
            user_id: User ID
            user_profile: User profile data
            
        Returns:
            List of triggered events
        """
        try:
            triggered_events = []
            
            # Check for birthday approaching
            if self._detect_birthday_approaching(user_id, user_profile):
                event = self._create_trigger_event(
                    user_id, 'birthday_approaching', user_profile, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for lease renewal
            if self._detect_lease_renewal(user_id, user_profile):
                event = self._create_trigger_event(
                    user_id, 'lease_renewal', user_profile, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for student loan grace period ending
            if self._detect_student_loan_grace_ending(user_id, user_profile):
                event = self._create_trigger_event(
                    user_id, 'student_loan_grace_ending', user_profile, 'rule_based'
                )
                triggered_events.append(event)
            
            return triggered_events
            
        except Exception as e:
            logger.error(f"Error detecting life event triggers for user {user_id}: {e}")
            raise
    
    def detect_engagement_triggers(self, user_id: str, engagement_data: Dict[str, Any]) -> List[TriggerEvent]:
        """
        Detect engagement triggers
        
        Args:
            user_id: User ID
            engagement_data: User engagement data
            
        Returns:
            List of triggered events
        """
        try:
            triggered_events = []
            
            # Check for app usage decline
            if self._detect_app_usage_decline(user_id, engagement_data):
                event = self._create_trigger_event(
                    user_id, 'app_usage_decline', engagement_data, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for unused features
            if self._detect_feature_unused(user_id, engagement_data):
                event = self._create_trigger_event(
                    user_id, 'feature_unused', engagement_data, 'rule_based'
                )
                triggered_events.append(event)
            
            # Check for premium upgrade opportunity
            if self._detect_premium_upgrade_opportunity(user_id, engagement_data):
                event = self._create_trigger_event(
                    user_id, 'premium_upgrade_opportunity', engagement_data, 'rule_based'
                )
                triggered_events.append(event)
            
            return triggered_events
            
        except Exception as e:
            logger.error(f"Error detecting engagement triggers for user {user_id}: {e}")
            raise
    
    def process_trigger_event(self, trigger_event: TriggerEvent) -> bool:
        """
        Process a trigger event and send communications
        
        Args:
            trigger_event: Trigger event to process
            
        Returns:
            True if communication was sent successfully
        """
        try:
            # Get trigger configuration
            trigger = self.db.query(BehavioralTrigger).filter(
                BehavioralTrigger.id == trigger_event.trigger_id
            ).first()
            
            if not trigger or trigger.status != TriggerStatus.ACTIVE:
                logger.warning(f"Trigger {trigger_event.trigger_id} is not active")
                return False
            
            # Check if user should receive this trigger
            if not self._should_send_to_user(trigger_event.user_id, trigger):
                logger.info(f"User {trigger_event.user_id} excluded from trigger {trigger.id}")
                return False
            
            # Check cooldown periods
            if self._is_in_cooldown(trigger_event.user_id, trigger):
                logger.info(f"User {trigger_event.user_id} in cooldown for trigger {trigger.id}")
                return False
            
            # Get optimal send time
            send_time = self._get_optimal_send_time(trigger_event.user_id, trigger)
            
            # Send communications
            sms_sent = False
            email_sent = False
            
            if trigger.sms_template:
                sms_sent = self._send_sms_communication(trigger_event, trigger)
            
            if trigger.email_template:
                email_sent = self._send_email_communication(trigger_event, trigger)
            
            # Update trigger event
            trigger_event.sms_sent = sms_sent
            trigger_event.email_sent = email_sent
            trigger_event.sent_at = datetime.utcnow()
            trigger_event.event_type = 'sent'
            
            self.db.commit()
            
            logger.info(f"Processed trigger event {trigger_event.id}: SMS={sms_sent}, Email={email_sent}")
            return sms_sent or email_sent
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing trigger event {trigger_event.id}: {e}")
            raise
    
    def update_user_behavior_patterns(self, user_id: str, pattern_type: str, 
                                    pattern_data: Dict[str, Any]) -> None:
        """
        Update user behavior patterns for trigger detection
        
        Args:
            user_id: User ID
            pattern_type: Type of pattern (spending, income, savings, etc.)
            pattern_data: Pattern data
        """
        try:
            # Get or create pattern record
            pattern = self.db.query(UserBehaviorPattern).filter(
                and_(
                    UserBehaviorPattern.user_id == user_id,
                    UserBehaviorPattern.pattern_type == pattern_type
                )
            ).first()
            
            if not pattern:
                pattern = UserBehaviorPattern(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    pattern_type=pattern_type,
                    pattern_name=f"{pattern_type}_pattern",
                    pattern_data=pattern_data,
                    pattern_last_updated=datetime.utcnow()
                )
                self.db.add(pattern)
            else:
                pattern.pattern_data = pattern_data
                pattern.pattern_last_updated = datetime.utcnow()
            
            # Calculate pattern characteristics
            self._calculate_pattern_characteristics(pattern)
            
            pattern.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Updated behavior pattern for user {user_id}, type: {pattern_type}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating behavior pattern for user {user_id}: {e}")
            raise
    
    def get_trigger_effectiveness(self, trigger_id: str = None, 
                                time_period: str = "30d") -> Dict[str, Any]:
        """
        Get trigger effectiveness metrics
        
        Args:
            trigger_id: Specific trigger ID (optional)
            time_period: Time period for analysis
            
        Returns:
            Effectiveness metrics dictionary
        """
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            if time_period == "7d":
                start_time = end_time - timedelta(days=7)
            elif time_period == "30d":
                start_time = end_time - timedelta(days=30)
            elif time_period == "90d":
                start_time = end_time - timedelta(days=90)
            else:
                start_time = end_time - timedelta(days=30)
            
            # Build query
            query = self.db.query(TriggerEvent).filter(
                and_(
                    TriggerEvent.triggered_at >= start_time,
                    TriggerEvent.triggered_at <= end_time
                )
            )
            
            if trigger_id:
                query = query.filter(TriggerEvent.trigger_id == trigger_id)
            
            events = query.all()
            
            if not events:
                return {
                    'total_triggers': 0,
                    'total_sent': 0,
                    'total_engaged': 0,
                    'total_converted': 0,
                    'send_rate': 0,
                    'engagement_rate': 0,
                    'conversion_rate': 0,
                    'avg_conversion_value': 0
                }
            
            # Calculate metrics
            total_triggers = len(events)
            total_sent = len([e for e in events if e.sms_sent or e.email_sent])
            total_engaged = len([e for e in events if e.user_engaged])
            total_converted = len([e for e in events if e.conversion_achieved])
            
            # Calculate rates
            send_rate = (total_sent / total_triggers * 100) if total_triggers > 0 else 0
            engagement_rate = (total_engaged / total_sent * 100) if total_sent > 0 else 0
            conversion_rate = (total_converted / total_engaged * 100) if total_engaged > 0 else 0
            
            # Calculate average conversion value
            conversion_values = [float(e.conversion_value or 0) for e in events if e.conversion_achieved]
            avg_conversion_value = sum(conversion_values) / len(conversion_values) if conversion_values else 0
            
            # Get breakdown by trigger category
            category_breakdown = {}
            for event in events:
                trigger = self.db.query(BehavioralTrigger).filter(
                    BehavioralTrigger.id == event.trigger_id
                ).first()
                if trigger:
                    category = trigger.trigger_category.value
                    if category not in category_breakdown:
                        category_breakdown[category] = {
                            'triggers': 0,
                            'sent': 0,
                            'engaged': 0,
                            'converted': 0
                        }
                    category_breakdown[category]['triggers'] += 1
                    if event.sms_sent or event.email_sent:
                        category_breakdown[category]['sent'] += 1
                    if event.user_engaged:
                        category_breakdown[category]['engaged'] += 1
                    if event.conversion_achieved:
                        category_breakdown[category]['converted'] += 1
            
            return {
                'total_triggers': total_triggers,
                'total_sent': total_sent,
                'total_engaged': total_engaged,
                'total_converted': total_converted,
                'send_rate': round(send_rate, 2),
                'engagement_rate': round(engagement_rate, 2),
                'conversion_rate': round(conversion_rate, 2),
                'avg_conversion_value': round(avg_conversion_value, 2),
                'category_breakdown': category_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error getting trigger effectiveness: {e}")
            raise
    
    def train_ml_model(self, model_name: str, model_type: str, 
                      training_data: Dict[str, Any]) -> MLModel:
        """
        Train a machine learning model for trigger prediction
        
        Args:
            model_name: Name of the model
            model_type: Type of model (classification, regression, clustering)
            training_data: Training data and configuration
            
        Returns:
            Trained ML model
        """
        try:
            # This would integrate with actual ML training pipeline
            # For now, we'll create a placeholder model
            
            model = MLModel(
                id=str(uuid.uuid4()),
                model_name=model_name,
                model_type=model_type,
                model_version="1.0.0",
                model_config=training_data.get('config', {}),
                feature_columns=training_data.get('features', []),
                target_column=training_data.get('target', ''),
                training_data_size=training_data.get('data_size', 0),
                training_date=datetime.utcnow(),
                training_duration_minutes=training_data.get('duration_minutes', 0),
                accuracy_score=training_data.get('accuracy', 0.0),
                precision_score=training_data.get('precision', 0.0),
                recall_score=training_data.get('recall', 0.0),
                f1_score=training_data.get('f1', 0.0),
                is_active=True,
                is_production=False
            )
            
            self.db.add(model)
            self.db.commit()
            
            logger.info(f"Trained ML model: {model_name}")
            return model
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error training ML model {model_name}: {e}")
            raise
    
    # Helper methods for trigger detection
    def _detect_spending_spike(self, user_id: str, financial_data: Dict[str, Any], 
                             patterns: List[UserBehaviorPattern]) -> bool:
        """Detect spending spike trigger"""
        try:
            current_spending = financial_data.get('weekly_spending', 0)
            
            # Get baseline from patterns
            baseline = self._get_spending_baseline(patterns)
            if not baseline:
                return False
            
            # Calculate percentage increase
            percentage_increase = ((current_spending - baseline) / baseline) * 100
            
            # Check threshold (20% increase)
            return percentage_increase >= 20
            
        except Exception as e:
            logger.error(f"Error detecting spending spike: {e}")
            return False
    
    def _detect_income_drop(self, user_id: str, financial_data: Dict[str, Any], 
                          patterns: List[UserBehaviorPattern]) -> bool:
        """Detect income drop trigger"""
        try:
            current_income = financial_data.get('monthly_income', 0)
            
            # Get baseline from patterns
            baseline = self._get_income_baseline(patterns)
            if not baseline:
                return False
            
            # Calculate percentage decrease
            percentage_decrease = ((baseline - current_income) / baseline) * 100
            
            # Check threshold (15% decrease)
            return percentage_decrease >= 15
            
        except Exception as e:
            logger.error(f"Error detecting income drop: {e}")
            return False
    
    def _detect_savings_stall(self, user_id: str, financial_data: Dict[str, Any], 
                            patterns: List[UserBehaviorPattern]) -> bool:
        """Detect savings goal stall trigger"""
        try:
            savings_goals = financial_data.get('savings_goals', [])
            
            for goal in savings_goals:
                if goal.get('progress_stalled', False):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting savings stall: {e}")
            return False
    
    def _detect_milestone_reached(self, user_id: str, financial_data: Dict[str, Any]) -> bool:
        """Detect financial milestone reached trigger"""
        try:
            milestones = financial_data.get('milestones', [])
            
            for milestone in milestones:
                if milestone.get('just_reached', False):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting milestone reached: {e}")
            return False
    
    def _detect_low_exercise_high_spending(self, user_id: str, health_data: Dict[str, Any], 
                                         financial_data: Dict[str, Any]) -> bool:
        """Detect low exercise + high spending correlation"""
        try:
            exercise_level = health_data.get('exercise_level', 'normal')
            spending_level = financial_data.get('spending_level', 'normal')
            
            return exercise_level == 'low' and spending_level == 'high'
            
        except Exception as e:
            logger.error(f"Error detecting low exercise high spending: {e}")
            return False
    
    def _detect_high_stress_financial(self, user_id: str, health_data: Dict[str, Any], 
                                    financial_data: Dict[str, Any]) -> bool:
        """Detect high stress + financial decisions"""
        try:
            stress_level = health_data.get('stress_level', 'normal')
            recent_large_purchase = financial_data.get('recent_large_purchase', False)
            
            return stress_level == 'high' and recent_large_purchase
            
        except Exception as e:
            logger.error(f"Error detecting high stress financial: {e}")
            return False
    
    def _detect_job_opportunities(self, user_id: str, career_data: Dict[str, Any]) -> bool:
        """Detect job market opportunities"""
        try:
            opportunities = career_data.get('job_opportunities', [])
            return len(opportunities) >= 3
            
        except Exception as e:
            logger.error(f"Error detecting job opportunities: {e}")
            return False
    
    def _detect_skill_gaps(self, user_id: str, career_data: Dict[str, Any]) -> bool:
        """Detect skill gaps"""
        try:
            skill_gaps = career_data.get('skill_gaps', [])
            return len(skill_gaps) > 0
            
        except Exception as e:
            logger.error(f"Error detecting skill gaps: {e}")
            return False
    
    def _detect_salary_below_market(self, user_id: str, career_data: Dict[str, Any]) -> bool:
        """Detect salary below market rate"""
        try:
            current_salary = career_data.get('current_salary', 0)
            market_rate = career_data.get('market_rate', 0)
            
            if market_rate > 0:
                percentage_below = ((market_rate - current_salary) / market_rate) * 100
                return percentage_below >= 10
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting salary below market: {e}")
            return False
    
    def _detect_birthday_approaching(self, user_id: str, user_profile: Dict[str, Any]) -> bool:
        """Detect birthday approaching"""
        try:
            birthday = user_profile.get('birthday')
            if not birthday:
                return False
            
            # Calculate days until birthday
            today = datetime.now().date()
            next_birthday = birthday.replace(year=today.year)
            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)
            
            days_until = (next_birthday - today).days
            return days_until <= 7
            
        except Exception as e:
            logger.error(f"Error detecting birthday approaching: {e}")
            return False
    
    def _detect_lease_renewal(self, user_id: str, user_profile: Dict[str, Any]) -> bool:
        """Detect lease renewal period"""
        try:
            lease_end_date = user_profile.get('lease_end_date')
            if not lease_end_date:
                return False
            
            days_until = (lease_end_date - datetime.now().date()).days
            return days_until <= 30
            
        except Exception as e:
            logger.error(f"Error detecting lease renewal: {e}")
            return False
    
    def _detect_student_loan_grace_ending(self, user_id: str, user_profile: Dict[str, Any]) -> bool:
        """Detect student loan grace period ending"""
        try:
            grace_end_date = user_profile.get('student_loan_grace_end')
            if not grace_end_date:
                return False
            
            days_until = (grace_end_date - datetime.now().date()).days
            return days_until <= 30
            
        except Exception as e:
            logger.error(f"Error detecting student loan grace ending: {e}")
            return False
    
    def _detect_app_usage_decline(self, user_id: str, engagement_data: Dict[str, Any]) -> bool:
        """Detect app usage decline"""
        try:
            days_since_last_use = engagement_data.get('days_since_last_use', 0)
            return days_since_last_use >= 7
            
        except Exception as e:
            logger.error(f"Error detecting app usage decline: {e}")
            return False
    
    def _detect_feature_unused(self, user_id: str, engagement_data: Dict[str, Any]) -> bool:
        """Detect unused features"""
        try:
            unused_features = engagement_data.get('unused_features', [])
            return len(unused_features) > 0
            
        except Exception as e:
            logger.error(f"Error detecting unused features: {e}")
            return False
    
    def _detect_premium_upgrade_opportunity(self, user_id: str, engagement_data: Dict[str, Any]) -> bool:
        """Detect premium upgrade opportunity"""
        try:
            usage_frequency = engagement_data.get('usage_frequency', 'low')
            feature_usage = engagement_data.get('feature_usage', 0)
            is_premium_eligible = engagement_data.get('premium_eligible', False)
            
            return (usage_frequency == 'high' and 
                   feature_usage >= 3 and 
                   is_premium_eligible)
            
        except Exception as e:
            logger.error(f"Error detecting premium upgrade opportunity: {e}")
            return False
    
    # Helper methods for communication
    def _create_trigger_event(self, user_id: str, trigger_category: str, 
                            event_data: Dict[str, Any], detection_method: str) -> TriggerEvent:
        """Create a trigger event"""
        # Get trigger by category
        trigger = self.db.query(BehavioralTrigger).filter(
            BehavioralTrigger.trigger_category == TriggerCategory(trigger_category)
        ).first()
        
        if not trigger:
            raise ValueError(f"No trigger found for category: {trigger_category}")
        
        event = TriggerEvent(
            id=str(uuid.uuid4()),
            trigger_id=trigger.id,
            user_id=user_id,
            event_type='triggered',
            event_data=event_data,
            detection_method=detection_method,
            confidence_score=1.0,
            trigger_conditions_met=event_data
        )
        
        self.db.add(event)
        self.db.commit()
        
        return event
    
    def _should_send_to_user(self, user_id: str, trigger: BehavioralTrigger) -> bool:
        """Check if user should receive this trigger"""
        # Check user preferences
        preferences = self.db.query(CommunicationPreferences).filter(
            CommunicationPreferences.user_id == user_id
        ).first()
        
        if not preferences:
            return True  # Default to allow if no preferences set
        
        # Check if user has opted out of this type of communication
        # This would be more sophisticated in production
        
        return True
    
    def _is_in_cooldown(self, user_id: str, trigger: BehavioralTrigger) -> bool:
        """Check if user is in cooldown period for this trigger"""
        # Get schedule for this trigger
        schedule = self.db.query(TriggerSchedule).filter(
            TriggerSchedule.trigger_id == trigger.id
        ).first()
        
        if not schedule:
            return False
        
        # Check recent trigger events
        cooldown_start = datetime.utcnow() - timedelta(hours=schedule.cooldown_hours)
        
        recent_events = self.db.query(TriggerEvent).filter(
            and_(
                TriggerEvent.user_id == user_id,
                TriggerEvent.trigger_id == trigger.id,
                TriggerEvent.triggered_at >= cooldown_start
            )
        ).count()
        
        return recent_events > 0
    
    def _get_optimal_send_time(self, user_id: str, trigger: BehavioralTrigger) -> datetime:
        """Get optimal send time for user"""
        # Get user's engagement analytics
        analytics = self.db.query(UserEngagementAnalytics).filter(
            UserEngagementAnalytics.user_id == user_id
        ).first()
        
        if analytics and analytics.engagement_by_hour:
            # Find hour with highest engagement
            best_hour = max(analytics.engagement_by_hour.items(), 
                          key=lambda x: x[1])[0]
            
            # Set time to today at best hour
            now = datetime.utcnow()
            optimal_time = now.replace(hour=int(best_hour), minute=0, second=0, microsecond=0)
            
            # If optimal time has passed, set to tomorrow
            if optimal_time <= now:
                optimal_time += timedelta(days=1)
            
            return optimal_time
        
        # Default to current time + 1 hour
        return datetime.utcnow() + timedelta(hours=1)
    
    def _send_sms_communication(self, trigger_event: TriggerEvent, trigger: BehavioralTrigger) -> bool:
        """Send SMS communication for trigger"""
        try:
            # Get SMS template
            template = self.db.query(TriggerTemplate).filter(
                and_(
                    TriggerTemplate.template_name == trigger.sms_template,
                    TriggerTemplate.is_active == True
                )
            ).first()
            
            if not template:
                logger.warning(f"SMS template not found: {trigger.sms_template}")
                return False
            
            # Personalize message
            message = self._personalize_message(template.message_content, trigger_event.event_data)
            
            # Send SMS (would integrate with SMS service)
            # For now, just log the message
            logger.info(f"Sending SMS to user {trigger_event.user_id}: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS communication: {e}")
            return False
    
    def _send_email_communication(self, trigger_event: TriggerEvent, trigger: BehavioralTrigger) -> bool:
        """Send email communication for trigger"""
        try:
            # Get email template
            template = self.db.query(TriggerTemplate).filter(
                and_(
                    TriggerTemplate.template_name == trigger.email_template,
                    TriggerTemplate.is_active == True
                )
            ).first()
            
            if not template:
                logger.warning(f"Email template not found: {trigger.email_template}")
                return False
            
            # Personalize message
            subject = self._personalize_message(template.subject_line or '', trigger_event.event_data)
            message = self._personalize_message(template.message_content, trigger_event.event_data)
            
            # Send email (would integrate with email service)
            # For now, just log the message
            logger.info(f"Sending email to user {trigger_event.user_id}: {subject} - {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email communication: {e}")
            return False
    
    def _personalize_message(self, template: str, data: Dict[str, Any]) -> str:
        """Personalize message template with data"""
        try:
            # Simple template replacement
            # In production, would use a more sophisticated templating engine
            
            personalized = template
            
            # Replace common variables
            replacements = {
                '{{user_name}}': data.get('user_name', 'there'),
                '{{percentage}}': str(data.get('percentage', 0)),
                '{{amount}}': f"${data.get('amount', 0):,.2f}",
                '{{days}}': str(data.get('days', 0)),
                '{{milestone_name}}': data.get('milestone_name', 'goal'),
                '{{field}}': data.get('field', 'your field'),
                '{{skill_name}}': data.get('skill_name', 'new skills'),
                '{{feature_name}}': data.get('feature_name', 'this feature'),
                '{{benefit_count}}': str(data.get('benefit_count', 0)),
                '{{job_count}}': str(data.get('job_count', 0)),
                '{{potential_savings}}': f"${data.get('potential_savings', 0):,.2f}"
            }
            
            for placeholder, value in replacements.items():
                personalized = personalized.replace(placeholder, value)
            
            return personalized
            
        except Exception as e:
            logger.error(f"Error personalizing message: {e}")
            return template
    
    # Helper methods for pattern analysis
    def _get_user_patterns(self, user_id: str, pattern_type: str) -> List[UserBehaviorPattern]:
        """Get user behavior patterns"""
        return self.db.query(UserBehaviorPattern).filter(
            and_(
                UserBehaviorPattern.user_id == user_id,
                UserBehaviorPattern.pattern_type == pattern_type
            )
        ).all()
    
    def _get_spending_baseline(self, patterns: List[UserBehaviorPattern]) -> float:
        """Get spending baseline from patterns"""
        for pattern in patterns:
            if pattern.pattern_name == 'weekly_spending_cycle':
                return pattern.baseline_value or 0
        return 0
    
    def _get_income_baseline(self, patterns: List[UserBehaviorPattern]) -> float:
        """Get income baseline from patterns"""
        for pattern in patterns:
            if pattern.pattern_name == 'monthly_income_pattern':
                return pattern.baseline_value or 0
        return 0
    
    def _calculate_pattern_characteristics(self, pattern: UserBehaviorPattern) -> None:
        """Calculate pattern characteristics"""
        try:
            data = pattern.pattern_data
            
            if isinstance(data, list) and len(data) > 0:
                # Calculate baseline (mean)
                pattern.baseline_value = statistics.mean(data)
                
                # Calculate variance threshold (standard deviation)
                if len(data) > 1:
                    std_dev = statistics.stdev(data)
                    pattern.variance_threshold = std_dev * 2  # 2 standard deviations
                
                # Calculate trend direction
                if len(data) >= 3:
                    recent_avg = statistics.mean(data[-3:])
                    older_avg = statistics.mean(data[:-3])
                    
                    if recent_avg > older_avg * 1.1:
                        pattern.trend_direction = 'increasing'
                    elif recent_avg < older_avg * 0.9:
                        pattern.trend_direction = 'decreasing'
                    else:
                        pattern.trend_direction = 'stable'
                
                # Calculate confidence based on data consistency
                pattern.pattern_confidence = min(1.0, len(data) / 10.0)  # More data = higher confidence
            
        except Exception as e:
            logger.error(f"Error calculating pattern characteristics: {e}")


# Global service instance
behavioral_trigger_service = BehavioralTriggerService() 