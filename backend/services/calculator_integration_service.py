"""
Calculator Integration Service for MINGUS
Connects ML calculator systems with existing project structure
Integrates intelligent job matching, income comparison, and assessment services
"""
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
import threading
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, func, desc

from ..models.user import User
from ..models.user_profile import UserProfile
from ..models.subscription import Subscription, PricingTier, AuditLog, AuditEventType, AuditSeverity
from ..models.income_comparison import SalaryBenchmark as IncomeComparisonModel
from ..models.salary_data import MarketData as SalaryData
from ..ml.models.intelligent_job_matcher import IntelligentJobMatcher, JobPosting, SearchParameters
from ..ml.models.income_comparator_optimized import OptimizedIncomeComparator, get_income_comparator
from ..services.billing_features import BillingFeatures
from ..services.user_profile_service import UserProfileService
from ..services.subscription_tier_service import SubscriptionTierService
from ..config.base import Config

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CalculatorResult:
    """Immutable calculator result for memory efficiency"""
    user_id: int
    calculation_type: str
    result_data: Dict[str, Any]
    performance_metrics: Dict[str, float]
    cultural_context: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class CulturalContext:
    """Cultural personalization data for target demographic"""
    target_metro_areas: Dict[str, int] = field(default_factory=lambda: {
        'Atlanta': 95000,
        'Houston': 88000,
        'Washington DC': 75000,
        'Dallas-Fort Worth': 72000,
        'New York City': 65000,
        'Philadelphia': 58000,
        'Chicago': 52000,
        'Charlotte': 48000,
        'Miami': 42000,
        'Baltimore': 35000
    })
    
    community_challenges: List[str] = field(default_factory=lambda: [
        'Income instability',
        'Student debt burden',
        'Career path barriers',
        'Homeownership challenges',
        'Financial literacy gaps'
    ])
    
    age_based_focus: Dict[str, List[str]] = field(default_factory=lambda: {
        '25-35': [
            'Career advancement opportunities',
            'Student loan management strategies',
            'Home ownership preparation',
            'Investment portfolio building',
            'Emergency fund establishment'
        ]
    })

class CalculatorIntegrationService:
    """
    Calculator Integration Service
    Connects ML calculator systems with existing MINGUS infrastructure
    """
    
    def __init__(self, db_session: Session, config: Config):
        """Initialize calculator integration service"""
        self.db = db_session
        self.config = config
        
        # Initialize ML models with performance optimizations
        self.job_matcher = IntelligentJobMatcher()
        self.income_comparator = get_income_comparator()
        
        # Initialize supporting services
        self.billing_features = BillingFeatures(db_session, config)
        self.user_profile_service = UserProfileService(db_session)
        self.subscription_tier_service = SubscriptionTierService(db_session)
        
        # Cultural personalization
        self.cultural_context = CulturalContext()
        
        # Performance monitoring
        self.performance_monitor = self._initialize_performance_monitor()
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info("CalculatorIntegrationService initialized successfully")
    
    def _initialize_performance_monitor(self) -> Dict[str, List[float]]:
        """Initialize performance monitoring with sub-500ms targets"""
        return {
            'income_analysis': [],
            'job_matching': [],
            'assessment_scoring': [],
            'tax_calculation': [],
            'cultural_personalization': []
        }
    
    def _record_performance(self, operation: str, duration: float):
        """Record performance metric with thread safety"""
        with self._lock:
            if operation in self.performance_monitor:
                self.performance_monitor[operation].append(duration)
                # Keep only last 100 measurements to prevent memory bloat
                if len(self.performance_monitor[operation]) > 100:
                    self.performance_monitor[operation] = self.performance_monitor[operation][-100:]
    
    def _get_average_performance(self, operation: str) -> float:
        """Get average performance for operation"""
        with self._lock:
            if not self.performance_monitor[operation]:
                return 0.0
            return sum(self.performance_monitor[operation]) / len(self.performance_monitor[operation])
    
    def perform_comprehensive_analysis(self, user_id: int) -> CalculatorResult:
        """
        Perform comprehensive analysis integrating all calculator systems
        Target: <500ms total calculation time
        """
        start_time = time.time()
        
        try:
            # Get user and profile data
            user = self._get_user_with_profile(user_id)
            if not user or not user.profile:
                raise ValueError(f"User {user_id} or profile not found")
            
            # Perform income analysis with cultural personalization
            income_analysis = self._perform_income_analysis(user)
            
            # Perform job matching analysis
            job_matching = self._perform_job_matching_analysis(user)
            
            # Perform assessment scoring
            assessment_scoring = self._perform_assessment_scoring(user)
            
            # Calculate tax implications
            tax_calculation = self._perform_tax_calculation(user)
            
            # Generate cultural recommendations
            cultural_recommendations = self._generate_cultural_recommendations(user)
            
            # Combine results
            result_data = {
                'income_analysis': income_analysis,
                'job_matching': job_matching,
                'assessment_scoring': assessment_scoring,
                'tax_calculation': tax_calculation,
                'cultural_context': cultural_recommendations
            }
            
            # Calculate performance metrics
            total_time = time.time() - start_time
            performance_metrics = {
                'total_calculation_time': total_time,
                'income_analysis_time': self._get_average_performance('income_analysis'),
                'job_matching_time': self._get_average_performance('job_matching'),
                'assessment_scoring_time': self._get_average_performance('assessment_scoring'),
                'tax_calculation_time': self._get_average_performance('tax_calculation'),
                'cultural_personalization_time': self._get_average_performance('cultural_personalization')
            }
            
            # Generate recommendations
            recommendations = self._generate_integrated_recommendations(
                income_analysis, job_matching, assessment_scoring, tax_calculation
            )
            
            # Create result
            result = CalculatorResult(
                user_id=user_id,
                calculation_type='comprehensive_analysis',
                result_data=result_data,
                performance_metrics=performance_metrics,
                cultural_context=cultural_recommendations,
                recommendations=recommendations
            )
            
            # Log audit event
            self._log_audit_event(
                user_id, 'comprehensive_analysis_completed', 
                f"Analysis completed in {total_time:.3f}s", AuditSeverity.INFO
            )
            
            logger.info(f"Comprehensive analysis completed for user {user_id} in {total_time:.3f}s")
            return result
            
        except Exception as e:
            calculation_time = time.time() - start_time
            logger.error(f"Comprehensive analysis failed for user {user_id} after {calculation_time:.3f}s: {str(e)}")
            self._log_audit_event(
                user_id, 'comprehensive_analysis_failed', 
                f"Analysis failed after {calculation_time:.3f}s: {str(e)}", AuditSeverity.ERROR
            )
            raise
    
    def _perform_income_analysis(self, user: User) -> Dict[str, Any]:
        """Perform income analysis with cultural personalization"""
        start_time = time.time()
        
        try:
            # Get user income data
            current_income = user.profile.monthly_income * 12 if user.profile.monthly_income else 50000
            location = user.profile.location_city or 'Atlanta'
            age_group = user.profile.age_range or '25-35'
            
            # Perform income comparison using optimized comparator
            income_analysis = self.income_comparator.analyze_income(
                user_income=int(current_income),
                location=location,
                age_group=age_group
            )
            
            # Add cultural context
            cultural_insights = self._add_cultural_insights(income_analysis, user)
            
            result = {
                'current_income': current_income,
                'comparisons': [comp.__dict__ for comp in income_analysis.comparisons],
                'overall_percentile': income_analysis.overall_percentile,
                'career_opportunity_score': income_analysis.career_opportunity_score,
                'cultural_insights': cultural_insights,
                'motivational_summary': income_analysis.motivational_summary,
                'action_plan': income_analysis.action_plan
            }
            
            duration = time.time() - start_time
            self._record_performance('income_analysis', duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Income analysis failed after {duration:.3f}s: {str(e)}")
            raise
    
    def _perform_job_matching_analysis(self, user: User) -> Dict[str, Any]:
        """Perform job matching analysis"""
        start_time = time.time()
        
        try:
            # Get user profile data for job matching
            current_salary = user.profile.monthly_income * 12 if user.profile.monthly_income else 50000
            location = user.profile.location_city or 'Atlanta'
            
            # Create search parameters
            search_params = SearchParameters(
                current_salary=int(current_salary),
                target_salary_min=int(current_salary * 1.15),  # 15% minimum increase
                primary_field=self._determine_primary_field(user),
                experience_level=self._determine_experience_level(user),
                skills=self._extract_user_skills(user),
                locations=[location] if location else self.cultural_context.target_metro_areas.keys(),
                remote_preference=True
            )
            
            # Perform job search and matching
            job_results = self.job_matcher.find_income_advancement_jobs(
                user_id=user.id,
                resume_text=self._generate_resume_text(user),
                current_salary=int(current_salary),
                target_locations=[location] if location else list(self.cultural_context.target_metro_areas.keys())
            )
            
            duration = time.time() - start_time
            self._record_performance('job_matching', duration)
            
            return job_results
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Job matching analysis failed after {duration:.3f}s: {str(e)}")
            raise
    
    def _perform_assessment_scoring(self, user: User) -> Dict[str, Any]:
        """Perform assessment scoring using existing patterns"""
        start_time = time.time()
        
        try:
            # Get user assessment data from database
            assessment_data = self._get_user_assessment_data(user.id)
            
            if not assessment_data:
                return {
                    'score': 0,
                    'segment': 'stress-free',
                    'product_tier': 'Budget ($10)',
                    'challenges': [],
                    'recommendations': []
                }
            
            # Calculate score using exact formulas from assessment service
            score_result = self._calculate_assessment_score(assessment_data)
            
            duration = time.time() - start_time
            self._record_performance('assessment_scoring', duration)
            
            return score_result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Assessment scoring failed after {duration:.3f}s: {str(e)}")
            raise
    
    def _perform_tax_calculation(self, user: User) -> Dict[str, Any]:
        """Perform tax calculation using billing features"""
        start_time = time.time()
        
        try:
            # Get user subscription and income data
            subscription = self._get_user_subscription(user.id)
            current_income = user.profile.monthly_income * 12 if user.profile.monthly_income else 50000
            
            # Calculate tax implications
            tax_calculation = self.billing_features.calculate_tax_implications(
                customer_id=user.id,
                amount=current_income,
                location=user.profile.location_state or 'GA',
                tax_year=datetime.now().year
            )
            
            duration = time.time() - start_time
            self._record_performance('tax_calculation', duration)
            
            return tax_calculation
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Tax calculation failed after {duration:.3f}s: {str(e)}")
            raise
    
    def _generate_cultural_recommendations(self, user: User) -> Dict[str, Any]:
        """Generate cultural recommendations for target demographic"""
        start_time = time.time()
        
        try:
            age_group = user.profile.age_range or '25-35'
            location = user.profile.location_city or 'Atlanta'
            
            # Generate age-based recommendations
            age_recommendations = self.cultural_context.age_based_focus.get(age_group, [])
            
            # Generate location-based opportunities
            location_opportunities = self._get_location_opportunities(location)
            
            # Generate community-specific insights
            community_insights = self._get_community_insights(user)
            
            result = {
                'age_group': age_group,
                'location': location,
                'age_based_recommendations': age_recommendations,
                'location_opportunities': location_opportunities,
                'community_insights': community_insights,
                'target_metro_areas': self.cultural_context.target_metro_areas,
                'community_challenges': self.cultural_context.community_challenges
            }
            
            duration = time.time() - start_time
            self._record_performance('cultural_personalization', duration)
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Cultural recommendations failed after {duration:.3f}s: {str(e)}")
            raise
    
    def _add_cultural_insights(self, income_analysis: Any, user: User) -> Dict[str, Any]:
        """Add cultural insights to income analysis"""
        age_group = user.profile.age_range or '25-35'
        location = user.profile.location_city or 'Atlanta'
        
        return {
            'target_demographic': 'African American professionals, ages 25-35',
            'income_range': '$40K-$100K',
            'age_group_focus': age_group,
            'location_context': location,
            'community_challenges': self.cultural_context.community_challenges,
            'metro_opportunities': self.cultural_context.target_metro_areas.get(location, 0)
        }
    
    def _determine_primary_field(self, user: User) -> Any:
        """Determine user's primary field based on profile data"""
        # This would be enhanced with actual field detection logic
        from ..ml.models.resume_parser import FieldType
        return FieldType.DATA_ANALYSIS  # Default for now
    
    def _determine_experience_level(self, user: User) -> Any:
        """Determine user's experience level"""
        # This would be enhanced with actual experience detection logic
        from ..ml.models.resume_parser import ExperienceLevel
        return ExperienceLevel.MID  # Default for now
    
    def _extract_user_skills(self, user: User) -> List[str]:
        """Extract user skills from profile data"""
        # This would be enhanced with actual skill extraction logic
        return ['python', 'sql', 'analytics', 'project_management']
    
    def _generate_resume_text(self, user: User) -> str:
        """Generate resume text from user profile data"""
        # This would be enhanced with actual resume generation logic
        return f"""
        {user.full_name or 'Professional'}
        Experience: {user.profile.employment_status or 'Professional'}
        Skills: {', '.join(self._extract_user_skills(user))}
        Location: {user.profile.location_city or 'Atlanta'}
        """
    
    def _get_user_assessment_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user assessment data from database"""
        try:
            # This would query the actual assessment data table
            # For now, return mock data
            return {
                'relationship_status': 'single',
                'spending_habits': 'keep_separate',
                'financial_stress': 'sometimes',
                'emotional_triggers': ['none']
            }
        except Exception as e:
            logger.error(f"Failed to get assessment data for user {user_id}: {str(e)}")
            return None
    
    def _calculate_assessment_score(self, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate assessment score using exact formulas"""
        total_score = 0
        
        # EXACT point assignments from Calculator Analysis Summary
        relationship_status_points = {
            'single': 0, 'dating': 2, 'serious_relationship': 4,
            'married': 6, 'complicated': 8
        }
        
        spending_habits_points = {
            'keep_separate': 0, 'share_some': 2, 'joint_accounts': 4,
            'spend_more_relationships': 6, 'overspend_impress': 8
        }
        
        financial_stress_points = {
            'never': 0, 'rarely': 2, 'sometimes': 4, 'often': 6, 'always': 8
        }
        
        emotional_triggers_points = {
            'after_breakup': 3, 'after_arguments': 3, 'when_lonely': 2,
            'when_jealous': 2, 'social_pressure': 2, 'none': 0
        }
        
        # Calculate score
        total_score += relationship_status_points.get(assessment_data.get('relationship_status', 'single'), 0)
        total_score += spending_habits_points.get(assessment_data.get('spending_habits', 'keep_separate'), 0)
        total_score += financial_stress_points.get(assessment_data.get('financial_stress', 'sometimes'), 0)
        
        # Handle emotional triggers
        triggers = assessment_data.get('emotional_triggers', [])
        for trigger in triggers:
            total_score += emotional_triggers_points.get(trigger, 0)
        
        # EXACT segment classification
        if total_score <= 16:
            segment = 'stress-free'
            product_tier = 'Budget ($10)'
        elif total_score <= 25:
            segment = 'relationship-spender'
            product_tier = 'Mid-tier ($20)'
        elif total_score <= 35:
            segment = 'emotional-manager'
            product_tier = 'Mid-tier ($20)'
        else:
            segment = 'crisis-mode'
            product_tier = 'Professional ($50)'
        
        return {
            'score': total_score,
            'segment': segment,
            'product_tier': product_tier,
            'challenges': self._get_segment_challenges(segment),
            'recommendations': self._get_segment_recommendations(segment)
        }
    
    def _get_segment_challenges(self, segment: str) -> List[str]:
        """Get challenges for user segment"""
        challenges = {
            'stress-free': [
                'Maintaining this balance during life changes',
                'Helping others achieve similar harmony',
                'Taking your success to the next level'
            ],
            'relationship-spender': [
                'Setting healthy financial boundaries',
                'Balancing generosity with self-care',
                'Planning for long-term financial security'
            ],
            'emotional-manager': [
                'Identifying emotional spending triggers',
                'Developing healthier coping mechanisms',
                'Building financial resilience'
            ],
            'crisis-mode': [
                'Breaking the cycle of financial stress',
                'Creating immediate financial stability',
                'Building healthy relationship boundaries'
            ]
        }
        return challenges.get(segment, [])
    
    def _get_segment_recommendations(self, segment: str) -> List[str]:
        """Get recommendations for user segment"""
        recommendations = {
            'stress-free': [
                'Share your wisdom with others',
                'Consider becoming a mentor',
                'Explore advanced financial strategies'
            ],
            'relationship-spender': [
                'Learn boundary-setting techniques',
                'Create a relationship spending budget',
                'Build an emergency fund for emotional times'
            ],
            'emotional-manager': [
                'Track your emotional spending patterns',
                'Create a 30-day spending pause strategy',
                'Build a support system for financial goals'
            ],
            'crisis-mode': [
                'Implement emergency financial controls',
                'Seek professional financial counseling',
                'Create a 90-day recovery plan'
            ]
        }
        return recommendations.get(segment, [])
    
    def _get_location_opportunities(self, location: str) -> Dict[str, Any]:
        """Get location-specific opportunities"""
        target_income = self.cultural_context.target_metro_areas.get(location, 50000)
        
        return {
            'target_income': target_income,
            'growth_potential': target_income * 1.25,  # 25% growth potential
            'metro_ranking': list(self.cultural_context.target_metro_areas.keys()).index(location) + 1 if location in self.cultural_context.target_metro_areas else 0,
            'opportunity_score': min(100, (target_income / 50000) * 100)
        }
    
    def _get_community_insights(self, user: User) -> Dict[str, Any]:
        """Get community-specific insights"""
        return {
            'income_instability_risk': 'medium',
            'student_debt_impact': 'high',
            'career_barriers': 'moderate',
            'homeownership_readiness': 'developing',
            'financial_literacy_level': 'intermediate'
        }
    
    def _get_user_with_profile(self, user_id: int) -> Optional[User]:
        """Get user with profile data"""
        try:
            return self.db.query(User).filter(
                User.id == user_id
            ).options(
                # Eager load profile
                lambda q: q.joinedload(User.profile)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            return None
    
    def _get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription"""
        try:
            return self.db.query(Subscription).filter(
                and_(
                    Subscription.customer_id == user_id,
                    Subscription.status == 'active'
                )
            ).first()
        except Exception as e:
            logger.error(f"Failed to get subscription for user {user_id}: {str(e)}")
            return None
    
    def _generate_integrated_recommendations(
        self, 
        income_analysis: Dict[str, Any],
        job_matching: Dict[str, Any],
        assessment_scoring: Dict[str, Any],
        tax_calculation: Dict[str, Any]
    ) -> List[str]:
        """Generate integrated recommendations from all analyses"""
        recommendations = []
        
        # Income-based recommendations
        if income_analysis.get('career_opportunity_score', 0) > 20:
            recommendations.append("High career advancement potential - prioritize skill development")
        
        # Job matching recommendations
        if job_matching.get('job_recommendations'):
            recommendations.append(f"Found {len(job_matching['job_recommendations'])} high-quality job opportunities")
        
        # Assessment-based recommendations
        if assessment_scoring.get('segment') == 'crisis-mode':
            recommendations.append("Consider professional financial counseling for immediate support")
        
        # Tax-based recommendations
        if tax_calculation.get('tax_liability', 0) > 0:
            recommendations.append("Optimize tax strategy to reduce liability")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _log_audit_event(self, user_id: int, event_type: str, description: str, severity: AuditSeverity):
        """Log audit event for compliance"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                event_type=AuditEventType(event_type),
                severity=severity,
                description=description,
                timestamp=datetime.utcnow(),
                metadata={
                    'service': 'calculator_integration',
                    'performance_metrics': self.performance_monitor
                }
            )
            self.db.add(audit_log)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            self.db.rollback()
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        return {
            'income_analysis_avg': self._get_average_performance('income_analysis'),
            'job_matching_avg': self._get_average_performance('job_matching'),
            'assessment_scoring_avg': self._get_average_performance('assessment_scoring'),
            'tax_calculation_avg': self._get_average_performance('tax_calculation'),
            'cultural_personalization_avg': self._get_average_performance('cultural_personalization')
        }
    
    def clear_performance_cache(self):
        """Clear performance cache to free memory"""
        with self._lock:
            for operation in self.performance_monitor:
                self.performance_monitor[operation].clear()
        logger.info("Performance cache cleared")
