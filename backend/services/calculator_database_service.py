"""
Calculator Database Integration Service for MINGUS
Connects calculator systems with existing database models and user profile system
Integrates with 25+ user profile fields, subscription management, and audit logging
"""
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
import threading
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, desc, text
import json

from ..models.user import User
from ..models.user_profile import UserProfile
from ..models.subscription import Subscription, PricingTier, AuditLog, AuditEventType, AuditSeverity
from ..models.income_comparison import IncomeComparison as IncomeComparisonModel
from ..models.salary_data import SalaryData
from ..models.user_goals import UserGoals
from ..models.onboarding_progress import OnboardingProgress
from ..models.user_preferences import UserPreferences
from ..config.base import Config

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class UserProfileData:
    """Immutable user profile data for memory efficiency"""
    user_id: int
    email: str
    full_name: str
    age_range: str
    location_state: str
    location_city: str
    monthly_income: float
    employment_status: str
    primary_goal: str
    risk_tolerance: str
    investment_experience: str
    current_savings: float
    current_debt: float
    credit_score_range: str
    household_size: int
    created_at: datetime
    updated_at: datetime

@dataclass(frozen=True)
class SubscriptionData:
    """Immutable subscription data for memory efficiency"""
    subscription_id: int
    user_id: int
    tier_name: str
    monthly_price: float
    status: str
    billing_cycle: str
    created_at: datetime
    expires_at: datetime

class CalculatorDatabaseService:
    """
    Calculator Database Integration Service
    Connects calculator systems with existing MINGUS database infrastructure
    """
    
    def __init__(self, db_session: Session, config: Config):
        """Initialize calculator database service"""
        self.db = db_session
        self.config = config
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Cache for frequently accessed data
        self._user_profile_cache = {}
        self._subscription_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        logger.info("CalculatorDatabaseService initialized successfully")
    
    @lru_cache(maxsize=1000)
    def get_user_profile_data(self, user_id: int) -> Optional[UserProfileData]:
        """
        Get comprehensive user profile data with 25+ fields
        Uses LRU cache for performance optimization
        """
        try:
            # Check cache first
            cache_key = f"user_profile_{user_id}"
            if cache_key in self._user_profile_cache:
                cached_data, timestamp = self._user_profile_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    return cached_data
            
            # Query database with eager loading
            user = self.db.query(User).options(
                joinedload(User.profile),
                joinedload(User.onboarding_progress),
                joinedload(User.health_checkins),
                joinedload(User.health_correlations)
            ).filter(User.id == user_id).first()
            
            if not user or not user.profile:
                logger.warning(f"User {user_id} or profile not found")
                return None
            
            # Create immutable profile data
            profile_data = UserProfileData(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name or '',
                age_range=user.profile.age_range or '25-35',
                location_state=user.profile.location_state or '',
                location_city=user.profile.location_city or '',
                monthly_income=user.profile.monthly_income or 0.0,
                employment_status=user.profile.employment_status or '',
                primary_goal=user.profile.primary_goal or '',
                risk_tolerance=user.profile.risk_tolerance or '',
                investment_experience=user.profile.investment_experience or '',
                current_savings=user.profile.current_savings or 0.0,
                current_debt=user.profile.current_debt or 0.0,
                credit_score_range=user.profile.credit_score_range or '',
                household_size=user.profile.household_size or 1,
                created_at=user.profile.created_at or datetime.utcnow(),
                updated_at=user.profile.updated_at or datetime.utcnow()
            )
            
            # Cache the result
            self._user_profile_cache[cache_key] = (profile_data, time.time())
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Failed to get user profile data for user {user_id}: {str(e)}")
            return None
    
    @lru_cache(maxsize=1000)
    def get_user_subscription_data(self, user_id: int) -> Optional[SubscriptionData]:
        """
        Get user subscription data with 3 tiers: $10, $20, $50
        Uses LRU cache for performance optimization
        """
        try:
            # Check cache first
            cache_key = f"user_subscription_{user_id}"
            if cache_key in self._subscription_cache:
                cached_data, timestamp = self._subscription_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    return cached_data
            
            # Query active subscription
            subscription = self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == user_id,
                    Subscription.status == 'active'
                )
            ).first()
            
            if not subscription:
                logger.info(f"No active subscription found for user {user_id}")
                return None
            
            # Create immutable subscription data
            subscription_data = SubscriptionData(
                subscription_id=subscription.id,
                user_id=subscription.customer_id,
                tier_name=subscription.pricing_tier.name if subscription.pricing_tier else '',
                monthly_price=subscription.pricing_tier.monthly_price if subscription.pricing_tier else 0.0,
                status=subscription.status,
                billing_cycle=subscription.billing_cycle.value if subscription.billing_cycle else 'monthly',
                created_at=subscription.created_at,
                expires_at=subscription.expires_at
            )
            
            # Cache the result
            self._subscription_cache[cache_key] = (subscription_data, time.time())
            
            return subscription_data
            
        except Exception as e:
            logger.error(f"Failed to get subscription data for user {user_id}: {str(e)}")
            return None
    
    def save_income_comparison_results(self, user_id: int, comparison_data: Dict[str, Any]) -> bool:
        """
        Save income comparison results to database
        Integrates with existing income_comparison table
        """
        try:
            with self._lock:
                # Create income comparison record
                income_comparison = IncomeComparisonModel(
                    user_id=user_id,
                    comparison_type='comprehensive_analysis',
                    national_median_income=comparison_data.get('national_median', 0),
                    user_income=comparison_data.get('current_income', 0),
                    percentile_rank=comparison_data.get('overall_percentile', 50.0),
                    career_opportunity_score=comparison_data.get('career_opportunity_score', 0.0),
                    primary_gap=comparison_data.get('primary_gap', {}),
                    cultural_insights=json.dumps(comparison_data.get('cultural_insights', {})),
                    recommendations=json.dumps(comparison_data.get('recommendations', [])),
                    calculation_timestamp=datetime.utcnow(),
                    data_source='2022_ACS_BLS_LINKEDIN',
                    confidence_level=0.95
                )
                
                self.db.add(income_comparison)
                self.db.commit()
                
                # Log audit event
                self._log_audit_event(
                    user_id, 'income_comparison_saved',
                    f"Income comparison results saved for user {user_id}",
                    AuditSeverity.INFO
                )
                
                logger.info(f"Income comparison results saved for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save income comparison results for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def save_job_matching_results(self, user_id: int, job_data: Dict[str, Any]) -> bool:
        """
        Save job matching results to database
        Integrates with existing salary_data table
        """
        try:
            with self._lock:
                # Save job recommendations as salary data entries
                job_recommendations = job_data.get('job_recommendations', [])
                
                for job in job_recommendations[:10]:  # Limit to top 10 jobs
                    salary_data = SalaryData(
                        user_id=user_id,
                        job_title=job.get('title', ''),
                        company_name=job.get('company', ''),
                        location=job.get('location', ''),
                        salary_min=job.get('salary_range', {}).get('min', 0),
                        salary_max=job.get('salary_range', {}).get('max', 0),
                        salary_midpoint=job.get('salary_range', {}).get('midpoint', 0),
                        overall_score=job.get('overall_score', 0.0),
                        salary_improvement_score=job.get('score_breakdown', {}).get('salary_improvement', 0.0),
                        skills_alignment_score=job.get('score_breakdown', {}).get('skills_match', 0.0),
                        career_progression_score=job.get('score_breakdown', {}).get('career_progression', 0.0),
                        company_stability_score=job.get('score_breakdown', {}).get('company_quality', 0.0),
                        location_compatibility_score=job.get('score_breakdown', {}).get('location_fit', 0.0),
                        growth_potential_score=job.get('score_breakdown', {}).get('growth_potential', 0.0),
                        recommendations=json.dumps(job.get('recommendations', [])),
                        risk_factors=json.dumps(job.get('risk_factors', [])),
                        data_source='intelligent_job_matcher',
                        confidence_level=0.85,
                        created_at=datetime.utcnow()
                    )
                    
                    self.db.add(salary_data)
                
                self.db.commit()
                
                # Log audit event
                self._log_audit_event(
                    user_id, 'job_matching_saved',
                    f"Job matching results saved for user {user_id} - {len(job_recommendations)} jobs",
                    AuditSeverity.INFO
                )
                
                logger.info(f"Job matching results saved for user {user_id} - {len(job_recommendations)} jobs")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save job matching results for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def save_assessment_results(self, user_id: int, assessment_data: Dict[str, Any]) -> bool:
        """
        Save assessment results to database
        Updates user profile with assessment segment and product tier
        """
        try:
            with self._lock:
                # Update user profile with assessment results
                user_profile = self.db.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).first()
                
                if user_profile:
                    # Add assessment fields to user profile
                    user_profile.assessment_segment = assessment_data.get('segment', 'stress-free')
                    user_profile.assessment_score = assessment_data.get('score', 0)
                    user_profile.product_tier = assessment_data.get('product_tier', 'Budget ($10)')
                    user_profile.assessment_challenges = json.dumps(assessment_data.get('challenges', []))
                    user_profile.assessment_recommendations = json.dumps(assessment_data.get('recommendations', []))
                    user_profile.assessment_completed_at = datetime.utcnow()
                    user_profile.updated_at = datetime.utcnow()
                    
                    self.db.commit()
                    
                    # Log audit event
                    self._log_audit_event(
                        user_id, 'assessment_results_saved',
                        f"Assessment results saved for user {user_id} - segment: {assessment_data.get('segment')}",
                        AuditSeverity.INFO
                    )
                    
                    logger.info(f"Assessment results saved for user {user_id} - segment: {assessment_data.get('segment')}")
                    return True
                else:
                    logger.warning(f"User profile not found for user {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to save assessment results for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def get_user_goals_data(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user goals data for calculator integration
        Integrates with existing user_goals table
        """
        try:
            goals = self.db.query(UserGoals).filter(
                UserGoals.user_id == user_id
            ).all()
            
            return [
                {
                    'id': goal.id,
                    'goal_type': goal.goal_type,
                    'target_amount': goal.target_amount,
                    'current_amount': goal.current_amount,
                    'target_date': goal.target_date.isoformat() if goal.target_date else None,
                    'priority': goal.priority,
                    'status': goal.status
                }
                for goal in goals
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user goals for user {user_id}: {str(e)}")
            return []
    
    def get_onboarding_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Get user onboarding progress for calculator integration
        Integrates with existing onboarding_progress table
        """
        try:
            progress = self.db.query(OnboardingProgress).filter(
                OnboardingProgress.user_id == user_id
            ).first()
            
            if progress:
                return {
                    'current_step': progress.current_step,
                    'total_steps': progress.total_steps,
                    'completion_percentage': progress.completion_percentage,
                    'last_completed_step': progress.last_completed_step,
                    'started_at': progress.started_at.isoformat() if progress.started_at else None,
                    'completed_at': progress.completed_at.isoformat() if progress.completed_at else None
                }
            else:
                return {
                    'current_step': 0,
                    'total_steps': 0,
                    'completion_percentage': 0.0,
                    'last_completed_step': None,
                    'started_at': None,
                    'completed_at': None
                }
                
        except Exception as e:
            logger.error(f"Failed to get onboarding progress for user {user_id}: {str(e)}")
            return {}
    
    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences for calculator personalization
        Integrates with existing user_preferences table
        """
        try:
            preferences = self.db.query(UserPreferences).filter(
                UserPreferences.user_id == user_id
            ).first()
            
            if preferences:
                return {
                    'communication_frequency': preferences.communication_frequency,
                    'preferred_contact_method': preferences.preferred_contact_method,
                    'notification_preferences': json.loads(preferences.notification_preferences) if preferences.notification_preferences else {},
                    'privacy_settings': json.loads(preferences.privacy_settings) if preferences.privacy_settings else {},
                    'cultural_preferences': json.loads(preferences.cultural_preferences) if preferences.cultural_preferences else {}
                }
            else:
                return {
                    'communication_frequency': 'weekly',
                    'preferred_contact_method': 'email',
                    'notification_preferences': {},
                    'privacy_settings': {},
                    'cultural_preferences': {}
                }
                
        except Exception as e:
            logger.error(f"Failed to get user preferences for user {user_id}: {str(e)}")
            return {}
    
    def update_user_profile_calculator_data(self, user_id: int, calculator_data: Dict[str, Any]) -> bool:
        """
        Update user profile with calculator-generated data
        Integrates with existing user_profile table
        """
        try:
            with self._lock:
                user_profile = self.db.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).first()
                
                if user_profile:
                    # Update profile with calculator insights
                    user_profile.calculator_last_run = datetime.utcnow()
                    user_profile.calculator_insights = json.dumps(calculator_data.get('insights', {}))
                    user_profile.calculator_recommendations = json.dumps(calculator_data.get('recommendations', []))
                    user_profile.calculator_performance_metrics = json.dumps(calculator_data.get('performance_metrics', {}))
                    user_profile.calculator_cultural_context = json.dumps(calculator_data.get('cultural_context', {}))
                    user_profile.updated_at = datetime.utcnow()
                    
                    self.db.commit()
                    
                    # Log audit event
                    self._log_audit_event(
                        user_id, 'calculator_profile_updated',
                        f"User profile updated with calculator data for user {user_id}",
                        AuditSeverity.INFO
                    )
                    
                    logger.info(f"User profile updated with calculator data for user {user_id}")
                    return True
                else:
                    logger.warning(f"User profile not found for user {user_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update user profile with calculator data for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def get_calculator_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get calculator usage history for user
        Integrates with existing audit_log table
        """
        try:
            audit_logs = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.event_type.in_(['comprehensive_analysis_completed', 'income_comparison_saved', 'job_matching_saved', 'assessment_results_saved'])
                )
            ).order_by(desc(AuditLog.timestamp)).limit(limit).all()
            
            return [
                {
                    'id': log.id,
                    'event_type': log.event_type.value,
                    'description': log.description,
                    'severity': log.severity.value,
                    'timestamp': log.timestamp.isoformat(),
                    'metadata': json.loads(log.metadata) if log.metadata else {}
                }
                for log in audit_logs
            ]
            
        except Exception as e:
            logger.error(f"Failed to get calculator history for user {user_id}: {str(e)}")
            return []
    
    def get_performance_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Get performance analytics for calculator usage
        Integrates with existing audit_log table
        """
        try:
            # Get recent calculator events
            recent_events = self.db.query(AuditLog).filter(
                and_(
                    AuditLog.user_id == user_id,
                    AuditLog.event_type == 'comprehensive_analysis_completed',
                    AuditLog.timestamp >= datetime.utcnow() - timedelta(days=30)
                )
            ).all()
            
            if not recent_events:
                return {
                    'total_calculations': 0,
                    'average_calculation_time': 0.0,
                    'last_calculation': None,
                    'performance_trend': 'stable'
                }
            
            # Calculate performance metrics
            total_calculations = len(recent_events)
            calculation_times = []
            
            for event in recent_events:
                if event.metadata:
                    metadata = json.loads(event.metadata)
                    if 'performance_metrics' in metadata:
                        total_time = metadata['performance_metrics'].get('total_calculation_time', 0)
                        calculation_times.append(total_time)
            
            average_calculation_time = sum(calculation_times) / len(calculation_times) if calculation_times else 0.0
            last_calculation = max(event.timestamp for event in recent_events)
            
            # Determine performance trend
            if len(calculation_times) >= 2:
                recent_avg = sum(calculation_times[-5:]) / min(5, len(calculation_times[-5:]))
                older_avg = sum(calculation_times[:-5]) / max(1, len(calculation_times[:-5]))
                
                if recent_avg < older_avg * 0.9:
                    performance_trend = 'improving'
                elif recent_avg > older_avg * 1.1:
                    performance_trend = 'declining'
                else:
                    performance_trend = 'stable'
            else:
                performance_trend = 'stable'
            
            return {
                'total_calculations': total_calculations,
                'average_calculation_time': average_calculation_time,
                'last_calculation': last_calculation.isoformat(),
                'performance_trend': performance_trend,
                'target_performance': 0.5  # 500ms target
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance analytics for user {user_id}: {str(e)}")
            return {}
    
    def _log_audit_event(self, user_id: int, event_type: str, description: str, severity: AuditSeverity):
        """Log audit event for compliance and tracking"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                event_type=AuditEventType(event_type),
                severity=severity,
                description=description,
                timestamp=datetime.utcnow(),
                metadata=json.dumps({
                    'service': 'calculator_database',
                    'timestamp': datetime.utcnow().isoformat()
                })
            )
            self.db.add(audit_log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            self.db.rollback()
    
    def clear_cache(self):
        """Clear all caches to free memory"""
        with self._lock:
            self._user_profile_cache.clear()
            self._subscription_cache.clear()
        
        # Clear LRU caches
        self.get_user_profile_data.cache_clear()
        self.get_user_subscription_data.cache_clear()
        
        logger.info("Calculator database cache cleared")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics for monitoring"""
        try:
            stats = {}
            
            # User profile stats
            total_users = self.db.query(User).count()
            users_with_profiles = self.db.query(UserProfile).count()
            stats['user_profiles'] = {
                'total_users': total_users,
                'users_with_profiles': users_with_profiles,
                'profile_completion_rate': (users_with_profiles / total_users * 100) if total_users > 0 else 0
            }
            
            # Subscription stats
            active_subscriptions = self.db.query(Subscription).filter(
                Subscription.status == 'active'
            ).count()
            stats['subscriptions'] = {
                'active_subscriptions': active_subscriptions
            }
            
            # Calculator usage stats
            calculator_events = self.db.query(AuditLog).filter(
                AuditLog.event_type.in_(['comprehensive_analysis_completed', 'income_comparison_saved', 'job_matching_saved', 'assessment_results_saved'])
            ).count()
            stats['calculator_usage'] = {
                'total_calculator_events': calculator_events
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            return {}
