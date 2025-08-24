"""
Master Mingus Job Recommendation Engine
Orchestrates complete workflow from resume upload to targeted job recommendations
"""

import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from functools import lru_cache
import asyncio
from unittest.mock import Mock

from .resume_parser import AdvancedResumeParser
from .intelligent_job_matcher import IntelligentJobMatcher
from .job_selection_algorithm import JobSelectionAlgorithm, CareerAdvancementStrategy
from backend.services.intelligent_job_matching_service import IntelligentJobMatchingService
from backend.services.career_advancement_service import CareerAdvancementService

logger = logging.getLogger(__name__)

@dataclass
class ProcessingMetrics:
    """Processing performance metrics"""
    resume_processing_time: float = 0.0
    income_comparison_time: float = 0.0
    job_search_time: float = 0.0
    job_selection_time: float = 0.0
    total_processing_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    errors_encountered: List[str] = field(default_factory=list)

@dataclass
class UserProfileAnalysis:
    """Complete user profile analysis"""
    user_id: Optional[int] = None
    field_expertise: Dict[str, Any] = None
    experience_level: str = ""
    skills_analysis: Dict[str, Any] = None
    income_position: Dict[str, Any] = None
    career_trajectory: Dict[str, Any] = None
    leadership_potential: float = 0.0
    industry_focus: List[str] = None
    transferable_skills: List[str] = None
    
    def __post_init__(self):
        if self.field_expertise is None:
            self.field_expertise = {}
        if self.skills_analysis is None:
            self.skills_analysis = {}
        if self.income_position is None:
            self.income_position = {}
        if self.career_trajectory is None:
            self.career_trajectory = {}
        if self.industry_focus is None:
            self.industry_focus = []
        if self.transferable_skills is None:
            self.transferable_skills = []

@dataclass
class FinancialImpactAnalysis:
    """Financial impact analysis for recommendations"""
    current_salary: int
    current_percentile: float
    recommended_salary_ranges: Dict[str, Dict[str, int]]
    percentile_improvements: Dict[str, float]
    income_gap_analysis: Dict[str, Any]
    purchasing_power_impact: Dict[str, float]
    cost_of_living_adjustments: Dict[str, float]

@dataclass
class ActionPlan:
    """Comprehensive action plan for career advancement"""
    immediate_actions: List[str]
    skill_development_plan: Dict[str, Any]
    networking_strategy: Dict[str, Any]
    application_timeline: Dict[str, Any]
    success_metrics: Dict[str, Any]
    risk_mitigation: Dict[str, Any]

@dataclass
class JobRecommendationResult:
    """Complete job recommendation result"""
    user_profile: UserProfileAnalysis
    career_strategy: CareerAdvancementStrategy
    financial_impact: FinancialImpactAnalysis
    action_plan: ActionPlan
    processing_metrics: ProcessingMetrics
    success_probabilities: Dict[str, float]
    analytics_data: Dict[str, Any]
    generated_at: datetime
    success: bool = True

class MingusJobRecommendationEngine:
    """
    Master job recommendation engine orchestrating complete workflow
    """
    
    def __init__(self, db_session=None):
        """Initialize the recommendation engine"""
        self.db_session = db_session
        
        # Initialize core components
        self.resume_parser = AdvancedResumeParser()
        self.job_matcher = IntelligentJobMatcher()
        self.job_selector = JobSelectionAlgorithm()
        
        # Initialize services
        self.job_matching_service = IntelligentJobMatchingService(db_session) if db_session else None
        self.career_advancement_service = CareerAdvancementService(db_session) if db_session else None
        
        # Performance tracking
        self.processing_metrics = ProcessingMetrics()
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        # Error tracking
        self.error_counts = {}
        self.success_rates = {}
        
        # Performance targets
        self.performance_targets = {
            'resume_processing': 2.0,
            'income_comparison': 1.0,
            'job_search': 5.0,
            'job_selection': 2.0,
            'total_workflow': 8.0
        }
        
        logger.info("MingusJobRecommendationEngine initialized successfully")
    
    def process_resume_and_recommend_jobs(self, 
                                        resume_text: str,
                                        user_id: Optional[int] = None,
                                        current_salary: Optional[int] = None,
                                        target_locations: Optional[List[str]] = None,
                                        risk_preference: str = 'balanced',
                                        enable_caching: bool = True) -> JobRecommendationResult:
        # Input validation
        if current_salary is not None and current_salary < 0:
            raise ValueError("Current salary cannot be negative")
        
        valid_risk_preferences = ['conservative', 'balanced', 'aggressive']
        if risk_preference not in valid_risk_preferences:
            raise ValueError(f"Risk preference must be one of: {valid_risk_preferences}")
        
        valid_locations = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City', 'Chicago', 'Los Angeles', 'Remote']
        if target_locations:
            for location in target_locations:
                if location not in valid_locations:
                    raise ValueError(f"Invalid location: {location}. Valid locations are: {valid_locations}")
        """
        Complete workflow from resume processing to job recommendations
        
        Args:
            resume_text: Resume text content
            user_id: Optional user ID for database integration
            current_salary: Optional current salary (will estimate if not provided)
            target_locations: Optional target locations
            risk_preference: Risk preference (conservative, balanced, aggressive)
            enable_caching: Whether to use caching
            
        Returns:
            Complete job recommendation result
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting complete job recommendation workflow for user {user_id}")
            
            # Check cache first
            cache_key = self._generate_cache_key(resume_text, user_id, current_salary, target_locations, risk_preference)
            if enable_caching and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if datetime.utcnow() - cached_result['timestamp'] < timedelta(seconds=self.cache_ttl):
                    logger.info("Returning cached result")
                    self.processing_metrics.cache_hits += 1
                    return cached_result['result']
            
            self.processing_metrics.cache_misses += 1
            
            # Step 1: Resume Processing and Profile Analysis
            user_profile = self._process_resume_and_analyze_profile(resume_text, user_id)
            
            # Step 2: Income Comparison and Financial Analysis
            financial_impact = self._analyze_income_and_financial_impact(
                user_profile, current_salary, target_locations
            )
            
            # Step 3: Job Search and Matching
            job_opportunities = self._search_and_match_jobs(
                user_profile, financial_impact, target_locations
            )
            
            # Step 4: Job Selection and Strategy Generation
            career_strategy = self._select_jobs_and_generate_strategy(
                job_opportunities, user_profile, financial_impact, risk_preference
            )
            
            # Step 5: Action Plan Generation
            action_plan = self._generate_comprehensive_action_plan(
                user_profile, career_strategy, financial_impact
            )
            
            # Step 6: Success Probability Assessment
            success_probabilities = self._assess_success_probabilities(
                career_strategy, user_profile, action_plan
            )
            
            # Step 7: Analytics Data Collection
            analytics_data = self._collect_analytics_data(
                user_profile, career_strategy, financial_impact, action_plan
            )
            
            # Calculate total processing time
            total_time = time.time() - start_time
            self.processing_metrics.total_processing_time = total_time
            
            # Create result
            result = JobRecommendationResult(
                user_profile=user_profile,
                career_strategy=career_strategy,
                financial_impact=financial_impact,
                action_plan=action_plan,
                processing_metrics=self.processing_metrics,
                success_probabilities=success_probabilities,
                analytics_data=analytics_data,
                generated_at=datetime.utcnow()
            )
            
            # Cache result
            if enable_caching:
                self.cache[cache_key] = {
                    'result': result,
                    'timestamp': datetime.utcnow()
                }
            
            # Log performance metrics
            self._log_performance_metrics()
            
            logger.info(f"Job recommendation workflow completed in {total_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in job recommendation workflow: {str(e)}")
            logger.error(traceback.format_exc())
            self._handle_workflow_error(e)
            raise
    
    def _process_resume_and_analyze_profile(self, resume_text: str, user_id: Optional[int]) -> UserProfileAnalysis:
        """Step 1: Process resume and analyze user profile"""
        step_start = time.time()
        
        try:
            logger.info("Processing resume and analyzing user profile")
            
            # Validate resume text
            if not resume_text or len(resume_text.strip()) < 100:
                raise ValueError("Resume text is too short or empty")
            
            # Parse resume
            resume_analysis = self.resume_parser.parse_resume(resume_text)
            
            # Extract profile components
            field_expertise = {
                'primary_field': resume_analysis.field_analysis.primary_field.value,
                'secondary_field': resume_analysis.field_analysis.secondary_field.value if resume_analysis.field_analysis.secondary_field else None,
                'confidence_score': resume_analysis.field_analysis.confidence_score
            }
            
            experience_level = resume_analysis.experience_analysis.level.value
            
            skills_analysis = {
                'technical_skills': dict(resume_analysis.skills_analysis.technical_skills),
                'business_skills': dict(resume_analysis.skills_analysis.business_skills),
                'soft_skills': dict(resume_analysis.skills_analysis.soft_skills),
                'skills_ratio': resume_analysis.skills_analysis.technical_business_ratio
            }
            
            income_position = {
                'estimated_salary': resume_analysis.income_analysis.estimated_salary,
                'percentile': resume_analysis.income_analysis.percentile,
                'market_position': resume_analysis.income_analysis.market_position
            }
            
            career_trajectory = {
                'progression_pattern': resume_analysis.career_trajectory.career_progression,
                'next_steps': resume_analysis.career_trajectory.next_logical_steps,
                'growth_potential': resume_analysis.career_trajectory.growth_potential
            }
            
            leadership_potential = resume_analysis.leadership_potential
            industry_focus = resume_analysis.industry_experience
            transferable_skills = resume_analysis.transferable_skills
            
            # Store in database if user_id provided
            if user_id and self.career_advancement_service:
                self.career_advancement_service._store_resume_analysis(user_id, resume_analysis)
            
            step_time = time.time() - step_start
            self.processing_metrics.resume_processing_time = step_time
            
            logger.info(f"Resume processing completed in {step_time:.2f} seconds")
            
            return UserProfileAnalysis(
                user_id=user_id,
                field_expertise=field_expertise,
                experience_level=experience_level,
                skills_analysis=skills_analysis,
                income_position=income_position,
                career_trajectory=career_trajectory,
                leadership_potential=leadership_potential,
                industry_focus=industry_focus,
                transferable_skills=transferable_skills
            )
            
        except Exception as e:
            logger.error(f"Error in resume processing: {str(e)}")
            self.processing_metrics.errors_encountered.append(f"Resume processing: {str(e)}")
            raise
    
    def _analyze_income_and_financial_impact(self, 
                                           user_profile: UserProfileAnalysis,
                                           current_salary: Optional[int],
                                           target_locations: Optional[List[str]]) -> FinancialImpactAnalysis:
        """Step 2: Analyze income and financial impact"""
        step_start = time.time()
        
        try:
            logger.info("Analyzing income and financial impact")
            
            # Use provided salary or estimate from profile
            if current_salary is None:
                current_salary = user_profile.income_position['estimated_salary']
            
            current_percentile = user_profile.income_position['percentile']
            
            # Calculate recommended salary ranges for each tier
            recommended_salary_ranges = {
                'conservative': {
                    'min': int(current_salary * 1.15),
                    'max': int(current_salary * 1.20),
                    'target': int(current_salary * 1.175)
                },
                'optimal': {
                    'min': int(current_salary * 1.25),
                    'max': int(current_salary * 1.30),
                    'target': int(current_salary * 1.275)
                },
                'stretch': {
                    'min': int(current_salary * 1.35),
                    'max': int(current_salary * 1.50),
                    'target': int(current_salary * 1.425)
                }
            }
            
            # Calculate percentile improvements
            percentile_improvements = {
                'conservative': self._calculate_percentile_improvement(current_percentile, recommended_salary_ranges['conservative']['target']),
                'optimal': self._calculate_percentile_improvement(current_percentile, recommended_salary_ranges['optimal']['target']),
                'stretch': self._calculate_percentile_improvement(current_percentile, recommended_salary_ranges['stretch']['target'])
            }
            
            # Income gap analysis
            gap_percentage = 0
            if current_salary > 0:
                gap_percentage = (recommended_salary_ranges['optimal']['target'] - current_salary) / current_salary * 100
            
            income_gap_analysis = {
                'current_salary': current_salary,
                'target_salary': recommended_salary_ranges['optimal']['target'],
                'gap_amount': recommended_salary_ranges['optimal']['target'] - current_salary,
                'gap_percentage': gap_percentage
            }
            
            # Purchasing power impact
            purchasing_power_impact = {}
            cost_of_living_adjustments = {}
            
            if target_locations:
                for location in target_locations:
                    col_adjustment = self._get_cost_of_living_adjustment(location)
                    cost_of_living_adjustments[location] = col_adjustment
                    
                    # Calculate purchasing power impact
                    salary_increase = 0
                    if current_salary > 0:
                        salary_increase = (recommended_salary_ranges['optimal']['target'] - current_salary) / current_salary
                    purchasing_power_impact[location] = salary_increase - (col_adjustment - 1.0)
            
            step_time = time.time() - step_start
            self.processing_metrics.income_comparison_time = step_time
            
            logger.info(f"Income analysis completed in {step_time:.2f} seconds")
            
            return FinancialImpactAnalysis(
                current_salary=current_salary,
                current_percentile=current_percentile,
                recommended_salary_ranges=recommended_salary_ranges,
                percentile_improvements=percentile_improvements,
                income_gap_analysis=income_gap_analysis,
                purchasing_power_impact=purchasing_power_impact,
                cost_of_living_adjustments=cost_of_living_adjustments
            )
            
        except Exception as e:
            logger.error(f"Error in income analysis: {str(e)}")
            self.processing_metrics.errors_encountered.append(f"Income analysis: {str(e)}")
            raise
    
    def _search_and_match_jobs(self, 
                              user_profile: UserProfileAnalysis,
                              financial_impact: FinancialImpactAnalysis,
                              target_locations: Optional[List[str]]) -> List[Any]:
        """Step 3: Search and match jobs"""
        step_start = time.time()
        
        try:
            logger.info("Searching and matching jobs")
            
            # Set default locations if not provided
            if not target_locations:
                target_locations = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
            
            # Create search parameters
            search_params = self._create_search_parameters(user_profile, financial_impact, target_locations)
            
            # Search for jobs
            job_results = self.job_matcher.find_income_advancement_jobs(
                user_id=0,  # Use 0 for non-database searches
                resume_text="",  # We already have parsed data
                current_salary=financial_impact.current_salary,
                target_locations=target_locations
            )
            
            if 'error' in job_results:
                raise ValueError(f"Job search failed: {job_results['error']}")
            
            # Convert to job scores
            job_recommendations = job_results.get('job_recommendations', [])
            scored_jobs = self._convert_to_job_scores(job_recommendations)
            
            step_time = time.time() - step_start
            self.processing_metrics.job_search_time = step_time
            
            logger.info(f"Job search completed in {step_time:.2f} seconds, found {len(scored_jobs)} jobs")
            
            return scored_jobs
            
        except Exception as e:
            logger.error(f"Error in job search: {str(e)}")
            self.processing_metrics.errors_encountered.append(f"Job search: {str(e)}")
            raise
    
    def _select_jobs_and_generate_strategy(self, 
                                         job_opportunities: List[Any],
                                         user_profile: UserProfileAnalysis,
                                         financial_impact: FinancialImpactAnalysis,
                                         risk_preference: str) -> CareerAdvancementStrategy:
        """Step 4: Select jobs and generate strategy"""
        step_start = time.time()
        
        try:
            logger.info("Selecting jobs and generating strategy")
            
            # Create search parameters for selection
            search_params = self._create_search_parameters(user_profile, financial_impact, [])
            
            # Create mock resume analysis for selection
            mock_resume_analysis = self._create_mock_resume_analysis(user_profile)
            
            # Generate career advancement strategy
            strategy = self.job_selector.select_career_advancement_strategy(
                job_opportunities, search_params, mock_resume_analysis
            )
            
            # Adjust strategy based on risk preference
            strategy = self._adjust_strategy_for_risk_preference(strategy, risk_preference)
            
            step_time = time.time() - step_start
            self.processing_metrics.job_selection_time = step_time
            
            logger.info(f"Job selection completed in {step_time:.2f} seconds")
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error in job selection: {str(e)}")
            self.processing_metrics.errors_encountered.append(f"Job selection: {str(e)}")
            raise
    
    def _generate_comprehensive_action_plan(self, 
                                          user_profile: UserProfileAnalysis,
                                          career_strategy: CareerAdvancementStrategy,
                                          financial_impact: FinancialImpactAnalysis) -> ActionPlan:
        """Step 5: Generate comprehensive action plan"""
        try:
            logger.info("Generating comprehensive action plan")
            
            # Immediate actions
            immediate_actions = [
                f"Apply to {career_strategy.conservative_opportunity.job.company} ({career_strategy.conservative_opportunity.job.title})",
                "Begin skill development for optimal opportunity",
                "Start networking for stretch opportunity"
            ]
            
            # Skill development plan
            skill_development_plan = self._generate_skill_development_plan(career_strategy)
            
            # Networking strategy
            networking_strategy = self._generate_networking_strategy(career_strategy, user_profile)
            
            # Application timeline
            application_timeline = self._generate_application_timeline(career_strategy)
            
            # Success metrics
            success_metrics = self._calculate_success_metrics(career_strategy, financial_impact)
            
            # Risk mitigation
            risk_mitigation = self._generate_risk_mitigation_plan(career_strategy)
            
            return ActionPlan(
                immediate_actions=immediate_actions,
                skill_development_plan=skill_development_plan,
                networking_strategy=networking_strategy,
                application_timeline=application_timeline,
                success_metrics=success_metrics,
                risk_mitigation=risk_mitigation
            )
            
        except Exception as e:
            logger.error(f"Error in action plan generation: {str(e)}")
            self.processing_metrics.errors_encountered.append(f"Action plan generation: {str(e)}")
            raise
    
    def _assess_success_probabilities(self, 
                                    career_strategy: CareerAdvancementStrategy,
                                    user_profile: UserProfileAnalysis,
                                    action_plan: ActionPlan) -> Dict[str, float]:
        """Step 6: Assess success probabilities"""
        try:
            logger.info("Assessing success probabilities")
            
            success_probabilities = {}
            
            # Conservative opportunity
            conservative_prob = career_strategy.conservative_opportunity.application_strategy.success_probability
            success_probabilities['conservative'] = conservative_prob
            
            # Optimal opportunity
            optimal_prob = career_strategy.optimal_opportunity.application_strategy.success_probability
            success_probabilities['optimal'] = optimal_prob
            
            # Stretch opportunity
            stretch_prob = career_strategy.stretch_opportunity.application_strategy.success_probability
            success_probabilities['stretch'] = stretch_prob
            
            # Overall success probability
            success_probabilities['overall'] = (conservative_prob + optimal_prob + stretch_prob) / 3
            
            return success_probabilities
            
        except Exception as e:
            logger.error(f"Error in success probability assessment: {str(e)}")
            self.processing_metrics.errors_encountered.append(f"Success probability assessment: {str(e)}")
            raise
    
    def _collect_analytics_data(self, 
                              user_profile: UserProfileAnalysis,
                              career_strategy: CareerAdvancementStrategy,
                              financial_impact: FinancialImpactAnalysis,
                              action_plan: ActionPlan) -> Dict[str, Any]:
        """Step 7: Collect analytics data"""
        try:
            logger.info("Collecting analytics data")
            
            analytics_data = {
                'user_profile_summary': {
                    'field': user_profile.field_expertise['primary_field'],
                    'experience_level': user_profile.experience_level,
                    'leadership_potential': user_profile.leadership_potential,
                    'skills_count': len(user_profile.skills_analysis['technical_skills']) + len(user_profile.skills_analysis['business_skills'])
                },
                'financial_analysis': {
                    'current_salary': financial_impact.current_salary,
                    'current_percentile': financial_impact.current_percentile,
                    'average_salary_increase': sum(financial_impact.percentile_improvements.values()) / len(financial_impact.percentile_improvements),
                    'income_gap_percentage': financial_impact.income_gap_analysis['gap_percentage']
                },
                'job_opportunities': {
                    'total_opportunities': 3,
                    'geographic_diversity': len(set([
                        career_strategy.conservative_opportunity.job.location,
                        career_strategy.optimal_opportunity.job.location,
                        career_strategy.stretch_opportunity.job.location
                    ])),
                    'company_diversity': len(set([
                        career_strategy.conservative_opportunity.job.company,
                        career_strategy.optimal_opportunity.job.company,
                        career_strategy.stretch_opportunity.job.company
                    ]))
                },
                'performance_metrics': {
                    'total_processing_time': self.processing_metrics.total_processing_time,
                    'cache_hits': self.processing_metrics.cache_hits,
                    'cache_misses': self.processing_metrics.cache_misses,
                    'errors_encountered': len(self.processing_metrics.errors_encountered)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error in analytics data collection: {str(e)}")
            self.processing_metrics.errors_encountered.append(f"Analytics collection: {str(e)}")
            raise
    
    # Helper methods
    
    def _generate_cache_key(self, resume_text: str, user_id: Optional[int], 
                           current_salary: Optional[int], target_locations: Optional[List[str]], 
                           risk_preference: str) -> str:
        """Generate cache key for results"""
        content = f"{resume_text[:1000]}_{user_id}_{current_salary}_{'_'.join(target_locations or [])}_{risk_preference}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _create_search_parameters(self, user_profile: UserProfileAnalysis, 
                                financial_impact: FinancialImpactAnalysis, 
                                target_locations: List[str]) -> Any:
        """Create search parameters for job matching"""
        from .intelligent_job_matcher import SearchParameters
        from .resume_parser import FieldType, ExperienceLevel
        
        # Map field to FieldType enum
        field_mapping = {
            'Data Analysis': FieldType.DATA_ANALYSIS,
            'Software Development': FieldType.SOFTWARE_DEVELOPMENT,
            'Project Management': FieldType.PROJECT_MANAGEMENT,
            'Marketing': FieldType.MARKETING,
            'Finance': FieldType.FINANCE,
            'Sales': FieldType.SALES,
            'Operations': FieldType.OPERATIONS,
            'HR': FieldType.HR
        }
        
        primary_field = field_mapping.get(user_profile.field_expertise['primary_field'], FieldType.DATA_ANALYSIS)
        
        # Map experience level to ExperienceLevel enum
        experience_mapping = {
            'Entry': ExperienceLevel.ENTRY,
            'Mid': ExperienceLevel.MID,
            'Senior': ExperienceLevel.SENIOR
        }
        
        experience_level = experience_mapping.get(user_profile.experience_level, ExperienceLevel.MID)
        
        # Combine skills
        all_skills = list(user_profile.skills_analysis['technical_skills'].keys()) + list(user_profile.skills_analysis['business_skills'].keys())
        
        return SearchParameters(
            current_salary=financial_impact.current_salary,
            target_salary_min=int(financial_impact.current_salary * 1.15),
            primary_field=primary_field,
            experience_level=experience_level,
            skills=all_skills,
            locations=target_locations,
            remote_preference=True,
            min_salary_increase=0.15
        )
    
    def _convert_to_job_scores(self, job_recommendations: List[Dict[str, Any]]) -> List[Any]:
        """Convert job recommendations to JobScore objects"""
        from .intelligent_job_matcher import JobScore, JobPosting, SalaryRange, CompanyTier, JobSource
        
        scored_jobs = []
        
        for job_data in job_recommendations:
            try:
                # Create JobPosting object
                job = JobPosting(
                    id=job_data.get('id', ''),
                    title=job_data.get('title', ''),
                    company=job_data.get('company', ''),
                    location=job_data.get('location', ''),
                    salary_range=SalaryRange(
                        min_salary=job_data.get('salary_range', {}).get('min', 0),
                        max_salary=job_data.get('salary_range', {}).get('max', 0)
                    ) if job_data.get('salary_range') else None,
                    description=job_data.get('description', ''),
                    requirements=job_data.get('requirements', []),
                    skills=job_data.get('skills', []),
                    experience_level=job_data.get('experience_level', ''),
                    field=job_data.get('field', ''),
                    industry=job_data.get('industry', ''),
                    remote_work=job_data.get('remote_work', False),
                    source=JobSource(job_data.get('source', 'linkedin').lower()),
                    company_tier=CompanyTier(job_data.get('company_tier', 'unknown')),
                    glassdoor_rating=job_data.get('glassdoor_rating')
                )
                
                # Create JobScore object
                score_breakdown = job_data.get('score_breakdown', {})
                job_score = JobScore(
                    job=job,
                    overall_score=job_data.get('overall_score', 0.0),
                    salary_improvement_score=score_breakdown.get('salary_improvement', 0.0),
                    skills_alignment_score=score_breakdown.get('skills_match', 0.0),
                    career_progression_score=score_breakdown.get('career_progression', 0.0),
                    company_stability_score=score_breakdown.get('company_quality', 0.0),
                    location_compatibility_score=score_breakdown.get('location_fit', 0.0),
                    growth_potential_score=score_breakdown.get('growth_potential', 0.0),
                    score_breakdown=score_breakdown,
                    recommendations=job_data.get('recommendations', []),
                    risk_factors=job_data.get('risk_factors', [])
                )
                
                scored_jobs.append(job_score)
                
            except Exception as e:
                logger.error(f"Error converting job recommendation: {str(e)}")
                continue
        
        return scored_jobs
    
    def _create_mock_resume_analysis(self, user_profile: UserProfileAnalysis) -> Any:
        """Create mock resume analysis for job selection"""
        mock_analysis = Mock()
        mock_analysis.field_analysis.primary_field.value = user_profile.field_expertise['primary_field']
        mock_analysis.experience_analysis.level.value = user_profile.experience_level
        mock_analysis.skills_analysis.technical_skills = user_profile.skills_analysis['technical_skills']
        mock_analysis.skills_analysis.business_skills = user_profile.skills_analysis['business_skills']
        mock_analysis.leadership_potential = user_profile.leadership_potential
        return mock_analysis
    
    def _adjust_strategy_for_risk_preference(self, strategy: CareerAdvancementStrategy, 
                                           risk_preference: str) -> CareerAdvancementStrategy:
        """Adjust strategy based on risk preference"""
        if risk_preference == 'conservative':
            strategy.strategy_summary['risk_distribution']['conservative'] = 'very_low'
            strategy.strategy_summary['risk_distribution']['optimal'] = 'low'
            strategy.strategy_summary['risk_distribution']['stretch'] = 'medium'
        elif risk_preference == 'aggressive':
            strategy.strategy_summary['risk_distribution']['conservative'] = 'medium'
            strategy.strategy_summary['risk_distribution']['optimal'] = 'high'
            strategy.strategy_summary['risk_distribution']['stretch'] = 'very_high'
        
        return strategy
    
    def _calculate_percentile_improvement(self, current_percentile: float, new_salary: int) -> float:
        """Calculate percentile improvement"""
        # Simplified calculation - in production, use real salary distribution data
        if new_salary > 150000:
            return min(100, current_percentile + 30)
        elif new_salary > 120000:
            return min(100, current_percentile + 20)
        elif new_salary > 100000:
            return min(100, current_percentile + 15)
        else:
            return min(100, current_percentile + 10)
    
    def _get_cost_of_living_adjustment(self, location: str) -> float:
        """Get cost of living adjustment for location"""
        adjustments = {
            'New York': 1.5,
            'San Francisco': 1.6,
            'Washington DC': 1.3,
            'Chicago': 1.2,
            'Atlanta': 1.0,
            'Houston': 0.95,
            'Dallas': 0.98,
            'Remote': 1.0
        }
        
        for city, adjustment in adjustments.items():
            if city.lower() in location.lower():
                return adjustment
        
        return 1.0
    
    def _generate_skill_development_plan(self, career_strategy: CareerAdvancementStrategy) -> Dict[str, Any]:
        """Generate skill development plan"""
        skill_plans = {}
        
        for tier in ['conservative', 'optimal', 'stretch']:
            opportunity = getattr(career_strategy, f'{tier}_opportunity')
            missing_skills = opportunity.skill_gap_analysis.missing_critical_skills
            
            skill_plans[tier] = {
                'missing_skills': missing_skills,
                'learning_recommendations': opportunity.skill_gap_analysis.learning_recommendations,
                'timeline_to_readiness': opportunity.skill_gap_analysis.timeline_to_readiness
            }
        
        return skill_plans
    
    def _generate_networking_strategy(self, career_strategy: CareerAdvancementStrategy, 
                                    user_profile: UserProfileAnalysis) -> Dict[str, Any]:
        """Generate networking strategy"""
        return {
            'immediate_connections': [
                f"Connect with employees at {career_strategy.conservative_opportunity.job.company}",
                f"Join {user_profile.field_expertise['primary_field']} professional groups",
                "Attend industry meetups and conferences"
            ],
            'long_term_networking': [
                "Build relationships with industry leaders",
                "Participate in online professional communities",
                "Mentor junior professionals to expand network"
            ],
            'target_companies': [
                career_strategy.conservative_opportunity.job.company,
                career_strategy.optimal_opportunity.job.company,
                career_strategy.stretch_opportunity.job.company
            ]
        }
    
    def _generate_application_timeline(self, career_strategy: CareerAdvancementStrategy) -> Dict[str, Any]:
        """Generate application timeline"""
        return {
            'immediate': [
                f"Apply to {career_strategy.conservative_opportunity.job.company}",
                "Update resume and LinkedIn profile"
            ],
            'week_1_2': [
                "Follow up on applications",
                "Begin skill development for optimal opportunity"
            ],
            'week_3_4': [
                f"Apply to {career_strategy.optimal_opportunity.job.company}",
                "Complete skill development projects"
            ],
            'month_2_3': [
                f"Apply to {career_strategy.stretch_opportunity.job.company}",
                "Continue networking and relationship building"
            ]
        }
    
    def _calculate_success_metrics(self, career_strategy: CareerAdvancementStrategy, 
                                 financial_impact: FinancialImpactAnalysis) -> Dict[str, Any]:
        """Calculate success metrics"""
        return {
            'average_salary_increase': sum(financial_impact.percentile_improvements.values()) / len(financial_impact.percentile_improvements),
            'average_success_probability': (
                career_strategy.conservative_opportunity.application_strategy.success_probability +
                career_strategy.optimal_opportunity.application_strategy.success_probability +
                career_strategy.stretch_opportunity.application_strategy.success_probability
            ) / 3,
            'total_opportunities': 3,
            'geographic_diversity': len(set([
                career_strategy.conservative_opportunity.job.location,
                career_strategy.optimal_opportunity.job.location,
                career_strategy.stretch_opportunity.job.location
            ]))
        }
    
    def _generate_risk_mitigation_plan(self, career_strategy: CareerAdvancementStrategy) -> Dict[str, Any]:
        """Generate risk mitigation plan"""
        return {
            'conservative_risks': career_strategy.conservative_opportunity.application_strategy.risk_factors,
            'conservative_mitigation': career_strategy.conservative_opportunity.application_strategy.mitigation_strategies,
            'optimal_risks': career_strategy.optimal_opportunity.application_strategy.risk_factors,
            'optimal_mitigation': career_strategy.optimal_opportunity.application_strategy.mitigation_strategies,
            'stretch_risks': career_strategy.stretch_opportunity.application_strategy.risk_factors,
            'stretch_mitigation': career_strategy.stretch_opportunity.application_strategy.mitigation_strategies,
            'overall_risk_management': [
                "Maintain current job while pursuing opportunities",
                "Build emergency fund for potential career transitions",
                "Develop backup skills for alternative career paths",
                "Maintain strong professional network"
            ]
        }
    
    def _log_performance_metrics(self):
        """Log performance metrics"""
        logger.info(f"Performance Metrics:")
        logger.info(f"  Resume Processing: {self.processing_metrics.resume_processing_time:.2f}s")
        logger.info(f"  Income Analysis: {self.processing_metrics.income_comparison_time:.2f}s")
        logger.info(f"  Job Search: {self.processing_metrics.job_search_time:.2f}s")
        logger.info(f"  Job Selection: {self.processing_metrics.job_selection_time:.2f}s")
        logger.info(f"  Total Time: {self.processing_metrics.total_processing_time:.2f}s")
        logger.info(f"  Cache Hits: {self.processing_metrics.cache_hits}")
        logger.info(f"  Cache Misses: {self.processing_metrics.cache_misses}")
        
        # Check performance targets
        if self.processing_metrics.total_processing_time > self.performance_targets['total_workflow']:
            logger.warning(f"Total processing time exceeded target of {self.performance_targets['total_workflow']}s")
    
    def _handle_workflow_error(self, error: Exception):
        """Handle workflow errors gracefully"""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        logger.error(f"Workflow error: {error_type} - {str(error)}")
        logger.error(traceback.format_exc())
        
        # Update success rates
        total_attempts = sum(self.error_counts.values()) + len(self.success_rates)
        if total_attempts > 0:
            success_rate = len(self.success_rates) / total_attempts
            logger.info(f"Current success rate: {success_rate:.2%}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'processing_metrics': {
                'resume_processing_time': self.processing_metrics.resume_processing_time,
                'income_comparison_time': self.processing_metrics.income_comparison_time,
                'job_search_time': self.processing_metrics.job_search_time,
                'job_selection_time': self.processing_metrics.job_selection_time,
                'total_processing_time': self.processing_metrics.total_processing_time
            },
            'cache_stats': {
                'hits': self.processing_metrics.cache_hits,
                'misses': self.processing_metrics.cache_misses,
                'hit_rate': self.processing_metrics.cache_hits / (self.processing_metrics.cache_hits + self.processing_metrics.cache_misses) if (self.processing_metrics.cache_hits + self.processing_metrics.cache_misses) > 0 else 0
            },
            'error_stats': {
                'error_counts': self.error_counts,
                'total_errors': len(self.processing_metrics.errors_encountered)
            },
            'performance_targets': self.performance_targets
        }
    
    def clear_cache(self):
        """Clear the result cache"""
        self.cache.clear()
        logger.info("Result cache cleared")
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.processing_metrics = ProcessingMetrics()
        logger.info("Performance metrics reset")
    
    def _calculate_salary_range(self, current_salary: int, min_increase: float, max_increase: float) -> Dict[str, int]:
        """Calculate salary range based on current salary and increase percentages"""
        min_salary = int(current_salary * (1 + min_increase))
        max_salary = int(current_salary * (1 + max_increase))
        
        return {
            'min': min_salary,
            'max': max_salary,
            'midpoint': (min_salary + max_salary) // 2
        } 