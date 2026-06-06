#!/usr/bin/env python3
"""
Mingus Job Recommendation Engine
Central orchestration engine that coordinates all components for seamless resume-to-recommendation workflow.

This module provides the main orchestration engine that:
- Processes resumes and extracts structured data
- Performs income and market research
- Searches and filters job opportunities
- Generates three-tier recommendations
- Creates application strategies
- Formats and presents results
- Tracks analytics and performance metrics

Performance targets:
- Total processing time: <8 seconds
- Recommendation accuracy: 90%+ relevant matches
- User satisfaction: Clear, actionable recommendations
- System reliability: 99.5% uptime
"""

import asyncio
import json
import logging
import psycopg2
import psycopg2.extras
import os
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import aiohttp
from functools import lru_cache

# Import existing components
from .advanced_resume_parser import AdvancedResumeParser, IncomePotential, LeadershipIndicator
from .resume_format_handler import AdvancedResumeParserWithFormats
from .income_boost_job_matcher import IncomeBoostJobMatcher, SearchCriteria, CareerField, ExperienceLevel, JobOpportunity, JobBoard
from .three_tier_job_selector import ThreeTierJobSelector, JobTier, TieredJobRecommendation
from backend.services.career_title_classifier import classify_by_rules

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRANSITION_AFFINITY = {
    'Technology':                    ['Operations & Supply Chain', 'Finance & Accounting', 'Engineering (Civil/Mech/Ind)'],
    'Healthcare (Clinical)':         ['Healthcare (Admin/Ops)', 'Social Services & Nonprofit'],
    'Healthcare (Admin/Ops)':        ['Operations & Supply Chain', 'Human Resources', 'Finance & Accounting'],
    'Finance & Accounting':          ['Real Estate', 'Legal', 'Operations & Supply Chain'],
    'Legal':                         ['Finance & Accounting', 'Government & Public Policy', 'Human Resources'],
    'Marketing & Communications':    ['Sales', 'Creative & Design', 'Technology'],
    'Sales':                         ['Marketing & Communications', 'Operations & Supply Chain', 'Real Estate'],
    'Education & Training':          ['Social Services & Nonprofit', 'Government & Public Policy', 'Human Resources'],
    'Engineering (Civil/Mech/Ind)':  ['Operations & Supply Chain', 'Construction & Trades', 'Technology'],
    'Creative & Design':             ['Marketing & Communications', 'Technology', 'Media & Journalism'],
    'Operations & Supply Chain':     ['Technology', 'Engineering (Civil/Mech/Ind)', 'Finance & Accounting'],
    'Human Resources':               ['Legal', 'Operations & Supply Chain', 'Finance & Accounting'],
    'Real Estate':                   ['Finance & Accounting', 'Legal', 'Construction & Trades'],
    'Social Services & Nonprofit':   ['Education & Training', 'Government & Public Policy', 'Healthcare (Admin/Ops)'],
    'Government & Public Policy':    ['Legal', 'Finance & Accounting', 'Social Services & Nonprofit'],
    'Hospitality & Food Service':    ['Retail & Consumer', 'Operations & Supply Chain', 'Creative & Design'],
    'Retail & Consumer':             ['Sales', 'Operations & Supply Chain', 'Marketing & Communications'],
    'Construction & Trades':         ['Engineering (Civil/Mech/Ind)', 'Real Estate', 'Operations & Supply Chain'],
    'Media & Journalism':            ['Marketing & Communications', 'Creative & Design', 'Technology'],
    'Science & Research':            ['Technology', 'Healthcare (Clinical)', 'Education & Training'],
    'Military / Veterans':           ['Government & Public Policy', 'Operations & Supply Chain', 'Engineering (Civil/Mech/Ind)'],
    'Self-Employed / Entrepreneurship': [],
}

SENIORITY_ORDER = ['entry', 'mid', 'senior', 'director']

_SENIORITY_TO_EXPERIENCE = {
    'entry': ExperienceLevel.ENTRY,
    'mid': ExperienceLevel.MID,
    'senior': ExperienceLevel.SENIOR,
    'director': ExperienceLevel.EXECUTIVE,
}


def seniority_distance(level_a: str, level_b: str) -> int:
    """Return signed distance from level_a to level_b on the seniority ladder."""
    if level_a not in SENIORITY_ORDER:
        raise ValueError(f"Invalid seniority level: {level_a!r}")
    if level_b not in SENIORITY_ORDER:
        raise ValueError(f"Invalid seniority level: {level_b!r}")
    return SENIORITY_ORDER.index(level_b) - SENIORITY_ORDER.index(level_a)


def _resolve_user_career_field(career_profile: Dict[str, Any]) -> str:
    """Resolve BLS career field from profile, falling back to rule-based classification."""
    user_field = career_profile.get('bls_career_field')
    if user_field:
        return user_field
    current_role = career_profile.get('current_role') or ''
    return classify_by_rules(current_role)['career_field']


def _salary_in_range(job: Dict[str, Any], salary_target: Optional[int]) -> bool:
    if salary_target is None:
        return True
    salary_min = job.get('salary_min')
    salary_max = job.get('salary_max')
    if salary_min is None or salary_max is None:
        return False
    return salary_min <= salary_target <= salary_max


def _tier_for_job(
    job: Dict[str, Any],
    user_field: str,
    user_seniority: str,
    salary_target: Optional[int],
) -> Optional[str]:
    """Assign a single tier to a job, or None if it does not qualify."""
    job_field = job.get('career_field')
    job_seniority = job.get('seniority_level')
    if not job_field or not job_seniority:
        return None

    if job_field == user_field:
        dist = seniority_distance(user_seniority, job_seniority)
        if dist == 0:
            if _salary_in_range(job, salary_target):
                return 'same_level'
            return 'conservative'
        if dist == 1:
            return 'reach'
        if dist <= 0:
            return 'conservative'
        return None

    affinity_fields = TRANSITION_AFFINITY.get(user_field, [])
    if job_field in affinity_fields and job_seniority == user_seniority:
        return 'conservative'
    return None


def _query_curated_jobs(msa: str) -> List[Dict[str, Any]]:
    """Load job postings for an MSA; returns [] if table is empty or unavailable."""
    if not msa:
        return []
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id, title, company,
                   city || ', ' || state AS location,
                   msa_code AS msa, career_field, seniority_level,
                   salary_min, salary_max, advancement_trajectory
            FROM job_postings
            WHERE msa_code = %s AND is_active = true
            ORDER BY career_field, seniority_level, title
            ''',
            (str(msa),),
        )
        rows = cursor.fetchall()
        conn.close()
        results = []
        for row in rows:
            job = dict(row)
            job['job_id'] = job.get('id')
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            if salary_min is not None and salary_max is not None:
                job['salary_median'] = (salary_min + salary_max) // 2
            results.append(job)
        return results
    except Exception as exc:
        logger.warning(f"Could not load job_postings for msa={msa}: {exc}")
        return []


def _build_search_criteria(
    career_profile: Dict[str, Any],
    user_seniority: str,
) -> SearchCriteria:
    salary_target = career_profile.get('salary_target') or career_profile.get('target_comp')
    current_salary = int(salary_target) if salary_target is not None else 75000
    experience_level = _SENIORITY_TO_EXPERIENCE.get(user_seniority, ExperienceLevel.MID)
    msa = career_profile.get('msa')
    return SearchCriteria(
        current_salary=current_salary,
        target_salary_increase=0.25,
        career_field=CareerField.TECHNOLOGY,
        experience_level=experience_level,
        preferred_msas=[str(msa)] if msa else [],
        remote_ok=True,
        max_commute_time=30,
        must_have_benefits=[],
        company_size_preference=None,
        industry_preference=None,
        equity_required=False,
        min_company_rating=3.0,
    )


def _curated_row_to_job_opportunity(row: Dict[str, Any]) -> JobOpportunity:
    requirements = row.get('requirements') or []
    if isinstance(requirements, str):
        try:
            requirements = json.loads(requirements)
        except (json.JSONDecodeError, TypeError):
            requirements = []
    benefits = row.get('benefits') or []
    if isinstance(benefits, str):
        try:
            benefits = json.loads(benefits)
        except (json.JSONDecodeError, TypeError):
            benefits = []

    salary_median = row.get('salary_median')
    if salary_median is None and row.get('salary_min') and row.get('salary_max'):
        salary_median = (row['salary_min'] + row['salary_max']) // 2

    return JobOpportunity(
        job_id=str(row.get('job_id') or row.get('id') or ''),
        title=row.get('title') or '',
        company=row.get('company') or '',
        location=row.get('location') or '',
        msa=str(row.get('msa') or ''),
        salary_min=row.get('salary_min'),
        salary_max=row.get('salary_max'),
        salary_median=salary_median,
        salary_increase_potential=0.0,
        remote_friendly=bool(row.get('remote_friendly', False)),
        job_board=JobBoard.INDEED,
        url=row.get('url') or '',
        description=row.get('description') or '',
        requirements=requirements,
        benefits=benefits,
        diversity_score=0.0,
        growth_score=0.0,
        culture_score=0.0,
        overall_score=0.0,
        field=CareerField.TECHNOLOGY,
        experience_level=_SENIORITY_TO_EXPERIENCE.get(
            row.get('seniority_level') or 'mid',
            ExperienceLevel.MID,
        ),
        posted_date=datetime.now(),
        application_deadline=None,
        company_size=row.get('company_size'),
        company_industry=row.get('company_industry'),
        equity_offered=bool(row.get('equity_offered', False)),
        bonus_potential=row.get('bonus_potential'),
        career_advancement_score=0.0,
        work_life_balance_score=0.0,
    )


def _serialize_recommendation(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'job_id': job.get('job_id') or job.get('id'),
        'title': job.get('title'),
        'company': job.get('company'),
        'location': job.get('location'),
        'msa': job.get('msa'),
        'career_field': job.get('career_field'),
        'seniority_level': job.get('seniority_level'),
        'salary_min': job.get('salary_min'),
        'salary_max': job.get('salary_max'),
        'salary_median': job.get('salary_median'),
        'advancement_trajectory': job.get('advancement_trajectory'),
        'overall_score': job.get('overall_score'),
        'url': job.get('url'),
        'remote_friendly': job.get('remote_friendly'),
    }


class ProcessingStatus(Enum):
    """Processing status for workflow steps"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CACHED = "cached"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ProcessingMetrics:
    """Metrics for processing performance"""
    total_time: float
    resume_parsing_time: float
    market_research_time: float
    job_search_time: float
    recommendation_generation_time: float
    formatting_time: float
    cache_hits: int
    cache_misses: int
    errors_count: int
    warnings_count: int

@dataclass
class WorkflowStep:
    """Individual workflow step tracking"""
    step_name: str
    status: ProcessingStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    error_message: Optional[str]
    result_data: Optional[Dict[str, Any]]

@dataclass
class UserAnalytics:
    """User behavior and success metrics"""
    user_id: str
    session_id: str
    resume_upload_time: datetime
    processing_completion_time: Optional[datetime]
    total_processing_time: Optional[float]
    recommendations_generated: int
    user_interactions: List[Dict[str, Any]]
    satisfaction_score: Optional[float]
    conversion_events: List[Dict[str, Any]]

def get_pg_connection():
    """Get PostgreSQL database connection"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    return conn

class MingusJobRecommendationEngine:
    """
    Central orchestration engine for the complete resume-to-recommendation workflow.
    
    This engine coordinates all components to provide seamless job recommendations
    with comprehensive error handling, performance optimization, and analytics tracking.
    """
    
    def __init__(self, db_path: str = None):
        """Initialize the recommendation engine"""
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.max_processing_time = 8.0  # 8 seconds max processing time
        self.performance_targets = {
            'total_time': 8.0,
            'recommendation_accuracy': 0.90,
            'system_reliability': 0.995
        }
        
        # Initialize components
        self.resume_parser = AdvancedResumeParserWithFormats()
        self.job_matcher = IncomeBoostJobMatcher()
        self.three_tier_selector = ThreeTierJobSelector()
        self.basic_parser = None
        
        # Initialize database
        self._init_database()
        
        # Performance monitoring
        self.metrics = ProcessingMetrics(
            total_time=0.0,
            resume_parsing_time=0.0,
            market_research_time=0.0,
            job_search_time=0.0,
            recommendation_generation_time=0.0,
            formatting_time=0.0,
            cache_hits=0,
            cache_misses=0,
            errors_count=0,
            warnings_count=0
        )
        
        logger.info("MingusJobRecommendationEngine initialized successfully")

    def process_recommendations(self, user_id: str, career_profile: dict) -> dict:
        """
        Generate three-tier recommendations from a career profile (#113 Phase A1).

        Tiers: same_level, reach, conservative — max 5 per tier, sorted by score desc.
        """
        user_field = _resolve_user_career_field(career_profile)
        user_seniority = career_profile.get('seniority_level') or 'mid'
        msa = career_profile.get('msa')
        salary_target = career_profile.get('salary_target') or career_profile.get('target_comp')
        if salary_target is not None:
            salary_target = int(salary_target)

        logger.info(
            f"process_recommendations for user {user_id}: "
            f"field={user_field!r}, seniority={user_seniority!r}, msa={msa!r}"
        )

        raw_jobs = _query_curated_jobs(str(msa) if msa else '')
        criteria = _build_search_criteria(career_profile, user_seniority)

        tier_buckets: Dict[str, List[Dict[str, Any]]] = {
            'same_level': [],
            'reach': [],
            'conservative': [],
        }

        for row in raw_jobs:
            tier = _tier_for_job(row, user_field, user_seniority, salary_target)
            if tier is None:
                continue
            scored = self.job_matcher.multi_dimensional_scoring(
                _curated_row_to_job_opportunity(row),
                criteria,
            )
            enriched = dict(row)
            enriched['overall_score'] = scored.overall_score
            tier_buckets[tier].append(enriched)

        result: Dict[str, List[Dict[str, Any]]] = {}
        for tier_name, jobs in tier_buckets.items():
            jobs.sort(key=lambda j: j.get('overall_score') or 0, reverse=True)
            result[tier_name] = [_serialize_recommendation(j) for j in jobs[:5]]

        return result
    
    def _init_database(self):
        """Verify PostgreSQL database connection"""
        try:
            conn = get_pg_connection()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    async def process_resume_completely(
        self, 
        resume_content: str,
        user_id: str = "anonymous",
        file_name: str = None,
        location: str = "New York",
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete resume-to-recommendation workflow.
        
        This is the main entry point that orchestrates all components:
        1. Resume parsing and analysis
        2. Income and market research
        3. Job searching and filtering
        4. Three-tier recommendation generation
        5. Application strategy creation
        6. Results formatting and presentation
        
        Args:
            resume_content: Raw resume text content
            user_id: User identifier
            file_name: Original file name (optional)
            location: User location for market research
            preferences: User preferences for job search
            
        Returns:
            Complete recommendation results with analytics
        """
        session_id = self._generate_session_id(user_id, resume_content)
        start_time = time.time()
        
        try:
            # Initialize workflow tracking
            workflow_steps = []
            self._track_workflow_start(session_id, user_id, resume_content)
            
            # Step 1: Resume Parsing and Analysis
            step1 = await self._execute_step(
                "resume_parsing",
                self._parse_resume_advanced,
                resume_content, file_name, location
            )
            workflow_steps.append(step1)
            
            if step1.status == ProcessingStatus.FAILED:
                return self._create_error_response("Resume parsing failed", step1.error_message)
            
            parsed_data = step1.result_data
            
            # Step 2: Income and Market Research
            step2 = await self._execute_step(
                "market_research",
                self._perform_market_research,
                parsed_data, location
            )
            workflow_steps.append(step2)
            
            # Step 3: Job Search and Filtering
            search_criteria = self._create_search_criteria(parsed_data, preferences, location)
            step3 = await self._execute_step(
                "job_search",
                self._search_job_opportunities,
                search_criteria
            )
            workflow_steps.append(step3)
            
            if step3.status == ProcessingStatus.FAILED:
                return self._create_error_response("Job search failed", step3.error_message)
            
            # Step 4: Three-Tier Recommendation Generation
            step4 = await self._execute_step(
                "recommendation_generation",
                self._generate_tiered_recommendations,
                search_criteria, step3.result_data
            )
            workflow_steps.append(step4)
            
            if step4.status == ProcessingStatus.FAILED:
                return self._create_error_response("Recommendation generation failed", step4.error_message)
            
            # Step 5: Application Strategy Creation
            step5 = await self._execute_step(
                "strategy_creation",
                self._create_application_strategies,
                step4.result_data
            )
            workflow_steps.append(step5)
            
            # Step 6: Results Formatting and Presentation
            step6 = await self._execute_step(
                "results_formatting",
                self._format_final_results,
                parsed_data, step4.result_data, step5.result_data, workflow_steps
            )
            workflow_steps.append(step6)
            
            # Calculate total processing time
            total_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(workflow_steps, total_time)
            
            # Track completion
            self._track_workflow_completion(session_id, total_time, step6.result_data)
            
            # Generate final response
            final_result = step6.result_data
            final_result['processing_metrics'] = asdict(self.metrics)
            final_result['workflow_steps'] = [asdict(step) for step in workflow_steps]
            final_result['session_id'] = session_id
            
            # Track analytics
            await self._track_analytics(user_id, session_id, "workflow_completed", {
                "total_time": total_time,
                "recommendations_count": len(final_result.get('recommendations', {})),
                "success": True
            })
            
            logger.info(f"Workflow completed successfully in {total_time:.2f}s for session {session_id}")
            return final_result
            
        except Exception as e:
            error_time = time.time() - start_time
            error_message = f"Workflow failed: {str(e)}"
            
            # Track error
            self._track_workflow_error(session_id, error_message)
            await self._track_analytics(user_id, session_id, "workflow_failed", {
                "error": error_message,
                "processing_time": error_time
            })
            
            logger.error(f"Workflow failed for session {session_id}: {e}")
            return self._create_error_response("Workflow execution failed", error_message)
    
    async def _execute_step(
        self, 
        step_name: str, 
        step_function, 
        *args, 
        **kwargs
    ) -> WorkflowStep:
        """Execute a workflow step with error handling and timing"""
        step = WorkflowStep(
            step_name=step_name,
            status=ProcessingStatus.IN_PROGRESS,
            start_time=datetime.now(),
            end_time=None,
            duration=None,
            error_message=None,
            result_data=None
        )
        
        try:
            # Check if step can be cached
            cache_key = self._generate_cache_key(step_name, args, kwargs)
            cached_result = await self._get_cached_result(cache_key)
            
            if cached_result:
                step.status = ProcessingStatus.CACHED
                step.result_data = cached_result
                self.metrics.cache_hits += 1
                logger.info(f"Step {step_name} served from cache")
            else:
                # Execute step
                if asyncio.iscoroutinefunction(step_function):
                    result = await step_function(*args, **kwargs)
                else:
                    result = step_function(*args, **kwargs)
                
                step.result_data = result
                step.status = ProcessingStatus.COMPLETED
                self.metrics.cache_misses += 1
                
                # Cache result
                await self._cache_result(cache_key, result)
                
                logger.info(f"Step {step_name} completed successfully")
        
        except Exception as e:
            step.status = ProcessingStatus.FAILED
            step.error_message = str(e)
            self.metrics.errors_count += 1
            logger.error(f"Step {step_name} failed: {e}")
        
        finally:
            step.end_time = datetime.now()
            if step.start_time:
                step.duration = (step.end_time - step.start_time).total_seconds()
        
        return step
    
    async def _parse_resume_advanced(
        self, 
        content: str, 
        file_name: str = None, 
        location: str = "New York"
    ) -> Dict[str, Any]:
        """Parse resume with advanced analytics"""
        try:
            start_time = time.time()
            
            # Use advanced parser for comprehensive analysis
            result = self.resume_parser.parse_resume_from_bytes(
                content.encode('utf-8'), 
                file_name or "resume.txt", 
                location
            )
            
            self.metrics.resume_parsing_time = time.time() - start_time
            
            if not result.get('success', False):
                raise Exception(f"Resume parsing failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Advanced resume parsing failed: {e}")
            # Fallback to basic parser
            try:
                if self.basic_parser is None:
                    from backend.api.resume_endpoints import ResumeParser
                    self.basic_parser = ResumeParser()
                basic_result = self.basic_parser.parse_resume(content, file_name)
                return {
                    'success': True,
                    'parsed_data': basic_result.get('parsed_data', {}),
                    'metadata': basic_result.get('metadata', {}),
                    'fallback_used': True
                }
            except Exception as fallback_error:
                raise Exception(f"Both advanced and basic parsing failed: {fallback_error}")
    
    async def _perform_market_research(
        self, 
        parsed_data: Dict[str, Any], 
        location: str
    ) -> Dict[str, Any]:
        """Perform income and market research"""
        try:
            start_time = time.time()
            
            # Extract income potential from parsed data
            income_potential = parsed_data.get('advanced_analytics', {}).get('income_potential', {})
            
            # Perform additional market research
            market_data = {
                'location': location,
                'salary_benchmarks': self._get_salary_benchmarks(parsed_data, location),
                'industry_trends': self._get_industry_trends(parsed_data),
                'growth_opportunities': self._identify_growth_opportunities(parsed_data),
                'skill_demand': self._analyze_skill_demand(parsed_data, location)
            }
            
            self.metrics.market_research_time = time.time() - start_time
            
            return {
                'income_potential': income_potential,
                'market_data': market_data,
                'research_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Market research failed: {e}")
            return {
                'income_potential': {},
                'market_data': {},
                'error': str(e),
                'research_timestamp': datetime.now().isoformat()
            }
    
    async def _search_job_opportunities(
        self, 
        search_criteria: SearchCriteria
    ) -> List[Dict[str, Any]]:
        """Search and filter job opportunities"""
        try:
            start_time = time.time()
            
            # Use the job matcher to find opportunities
            job_opportunities = await self.job_matcher.salary_focused_search(search_criteria)
            
            # Convert to serializable format
            jobs_data = []
            for job in job_opportunities:
                jobs_data.append({
                    'job_id': job.job_id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'salary_median': job.salary_median,
                    'salary_range': job.salary_range,
                    'description': job.description,
                    'requirements': job.requirements,
                    'benefits': job.benefits,
                    'overall_score': job.overall_score,
                    'salary_increase_potential': job.salary_increase_potential,
                    'diversity_score': job.diversity_score,
                    'growth_score': job.growth_score,
                    'culture_score': job.culture_score,
                    'remote_friendly': job.remote_friendly,
                    'equity_offered': job.equity_offered,
                    'company_size': job.company_size,
                    'company_industry': job.company_industry,
                    'msa': job.msa,
                    'field': job.field.value if job.field else None,
                    'experience_level': job.experience_level.value if job.experience_level else None,
                    'job_board': job.job_board.value if job.job_board else None,
                    'posted_date': job.posted_date.isoformat() if job.posted_date else None,
                    'application_deadline': job.application_deadline.isoformat() if job.application_deadline else None
                })
            
            self.metrics.job_search_time = time.time() - start_time
            
            return jobs_data
            
        except Exception as e:
            logger.error(f"Job search failed: {e}")
            raise Exception(f"Job search failed: {e}")
    
    async def _generate_tiered_recommendations(
        self, 
        search_criteria: SearchCriteria,
        job_opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate three-tier job recommendations"""
        try:
            start_time = time.time()
            
            # Convert job data back to JobOpportunity objects for the selector
            job_objects = self._convert_to_job_objects(job_opportunities)
            
            # Generate tiered recommendations
            recommendations = await self.three_tier_selector.generate_tiered_recommendations(
                search_criteria, 
                max_recommendations_per_tier=5
            )
            
            # Convert to serializable format
            serialized_recommendations = {}
            for tier, tier_recommendations in recommendations.items():
                serialized_recommendations[tier.value] = []
                for rec in tier_recommendations:
                    serialized_recommendations[tier.value].append({
                        'job': {
                            'job_id': rec.job.job_id,
                            'title': rec.job.title,
                            'company': rec.job.company,
                            'location': rec.job.location,
                            'salary_median': rec.job.salary_median,
                            'description': rec.job.description
                        },
                        'tier': rec.tier.value,
                        'success_probability': rec.success_probability,
                        'salary_increase_potential': rec.salary_increase_potential,
                        'skills_gap_analysis': [asdict(sg) for sg in rec.skills_gap_analysis],
                        'application_strategy': asdict(rec.application_strategy),
                        'preparation_roadmap': asdict(rec.preparation_roadmap),
                        'diversity_analysis': rec.diversity_analysis,
                        'company_culture_fit': rec.company_culture_fit,
                        'career_advancement_potential': rec.career_advancement_potential
                    })
            
            # Generate tier summary
            tier_summary = self.three_tier_selector.get_tier_summary(recommendations)
            
            self.metrics.recommendation_generation_time = time.time() - start_time
            
            return {
                'recommendations': serialized_recommendations,
                'tier_summary': tier_summary,
                'total_recommendations': sum(len(recs) for recs in serialized_recommendations.values())
            }
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            raise Exception(f"Recommendation generation failed: {e}")
    
    async def _create_application_strategies(
        self, 
        recommendations_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive application strategies"""
        try:
            start_time = time.time()
            
            strategies = {}
            
            for tier, tier_recommendations in recommendations_data.get('recommendations', {}).items():
                strategies[tier] = []
                for rec in tier_recommendations:
                    strategy = {
                        'job_id': rec['job']['job_id'],
                        'tier': tier,
                        'application_strategy': rec['application_strategy'],
                        'preparation_roadmap': rec['preparation_roadmap'],
                        'priority_actions': self._extract_priority_actions(rec),
                        'timeline': self._create_timeline(rec),
                        'success_factors': self._identify_success_factors(rec)
                    }
                    strategies[tier].append(strategy)
            
            self.metrics.formatting_time = time.time() - start_time
            
            return strategies
            
        except Exception as e:
            logger.error(f"Strategy creation failed: {e}")
            return {}
    
    async def _format_final_results(
        self,
        parsed_data: Dict[str, Any],
        recommendations_data: Dict[str, Any],
        strategies_data: Dict[str, Any],
        workflow_steps: List[WorkflowStep]
    ) -> Dict[str, Any]:
        """Format final results for presentation"""
        try:
            start_time = time.time()
            
            # Create comprehensive results
            results = {
                'success': True,
                'session_id': None,  # Will be set by caller
                'processing_time': sum(step.duration or 0 for step in workflow_steps),
                'timestamp': datetime.now().isoformat(),
                'resume_analysis': {
                    'parsed_data': parsed_data.get('parsed_data', {}),
                    'advanced_analytics': parsed_data.get('advanced_analytics', {}),
                    'confidence_score': parsed_data.get('metadata', {}).get('confidence_score', 0.0)
                },
                'recommendations': recommendations_data.get('recommendations', {}),
                'tier_summary': recommendations_data.get('tier_summary', {}),
                'application_strategies': strategies_data,
                'insights': self._generate_insights(parsed_data, recommendations_data),
                'action_plan': self._create_action_plan(recommendations_data, strategies_data),
                'next_steps': self._generate_next_steps(recommendations_data),
                'performance_metrics': {
                    'total_processing_time': sum(step.duration or 0 for step in workflow_steps),
                    'steps_completed': len([s for s in workflow_steps if s.status == ProcessingStatus.COMPLETED]),
                    'steps_cached': len([s for s in workflow_steps if s.status == ProcessingStatus.CACHED]),
                    'steps_failed': len([s for s in workflow_steps if s.status == ProcessingStatus.FAILED]),
                    'cache_hit_rate': self.metrics.cache_hits / max(1, self.metrics.cache_hits + self.metrics.cache_misses)
                }
            }
            
            self.metrics.formatting_time = time.time() - start_time
            
            return results
            
        except Exception as e:
            logger.error(f"Results formatting failed: {e}")
            return self._create_error_response("Results formatting failed", str(e))
    
    def _generate_session_id(self, user_id: str, content: str) -> str:
        """Generate unique session ID"""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{user_id}_{content_hash}_{timestamp}"
    
    def _generate_cache_key(self, step_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key for step"""
        key_data = {
            'step_name': step_name,
            'args': str(args),
            'kwargs': str(kwargs)
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT result_data, expires_at FROM recommendation_cache 
                WHERE cache_key = %s AND expires_at > CURRENT_TIMESTAMP
            ''', (cache_key,))
            
            result = cursor.fetchone()
            
            if result:
                cursor.execute('''
                    UPDATE recommendation_cache 
                    SET hit_count = hit_count + 1 
                    WHERE cache_key = %s
                ''', (cache_key,))
                conn.commit()
                conn.close()
                
                return json.loads(result['result_data'])
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result: {e}")
            return None
    
    async def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache result with expiration"""
        try:
            expires_at = datetime.now() + timedelta(seconds=self.cache_ttl)
            
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO recommendation_cache 
                (cache_key, result_data, expires_at) 
                VALUES (%s, %s, %s)
                ON CONFLICT (cache_key) DO UPDATE SET
                    result_data = EXCLUDED.result_data,
                    expires_at = EXCLUDED.expires_at,
                    hit_count = recommendation_cache.hit_count
            ''', (cache_key, json.dumps(result), expires_at))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error caching result: {e}")
    
    def _create_search_criteria(
        self, 
        parsed_data: Dict[str, Any], 
        preferences: Optional[Dict[str, Any]], 
        location: str
    ) -> SearchCriteria:
        """Create search criteria from parsed resume data"""
        try:
            # Extract basic info from parsed data
            personal_info = parsed_data.get('parsed_data', {}).get('personal_info', {})
            experience = parsed_data.get('parsed_data', {}).get('experience', [])
            skills = parsed_data.get('parsed_data', {}).get('skills', [])
            
            # Determine career field from experience and skills
            career_field = self._determine_career_field(experience, skills)
            
            # Determine experience level
            experience_level = self._determine_experience_level(experience)
            
            # Estimate current salary
            current_salary = self._estimate_current_salary(parsed_data, location)
            
            # Create search criteria
            criteria = SearchCriteria(
                current_salary=current_salary,
                target_salary_increase=0.25,  # Default 25% increase target
                career_field=career_field,
                experience_level=experience_level,
                preferred_msas=[location] if location else [],
                remote_ok=preferences.get('remote_ok', True) if preferences else True,
                max_commute_time=preferences.get('max_commute_time', 30) if preferences else 30,
                must_have_benefits=preferences.get('must_have_benefits', []) if preferences else [],
                company_size_preference=preferences.get('company_size_preference') if preferences else None,
                industry_preference=preferences.get('industry_preference') if preferences else None,
                equity_required=preferences.get('equity_required', False) if preferences else False,
                min_company_rating=preferences.get('min_company_rating', 3.0) if preferences else 3.0
            )
            
            return criteria
            
        except Exception as e:
            logger.error(f"Error creating search criteria: {e}")
            # Return default criteria
            return SearchCriteria(
                current_salary=75000,
                target_salary_increase=0.25,
                career_field=CareerField.TECHNOLOGY,
                experience_level=ExperienceLevel.MID,
                preferred_msas=[location] if location else [],
                remote_ok=True,
                max_commute_time=30,
                must_have_benefits=[],
                company_size_preference=None,
                industry_preference=None,
                equity_required=False,
                min_company_rating=3.0
            )
    
    def _determine_career_field(self, experience: List[Dict], skills: List[str]) -> CareerField:
        """Determine career field from experience and skills"""
        try:
            # Analyze experience and skills to determine field
            field_keywords = {
                CareerField.TECHNOLOGY: ['software', 'developer', 'engineer', 'programming', 'python', 'java', 'javascript'],
                CareerField.FINANCE: ['finance', 'financial', 'accounting', 'banking', 'investment', 'analyst'],
                CareerField.HEALTHCARE: ['healthcare', 'medical', 'nurse', 'doctor', 'health', 'clinical'],
                CareerField.EDUCATION: ['education', 'teacher', 'professor', 'academic', 'teaching', 'curriculum'],
                CareerField.MARKETING: ['marketing', 'advertising', 'brand', 'digital', 'social media', 'content'],
                CareerField.SALES: ['sales', 'business development', 'account manager', 'revenue', 'client'],
                CareerField.CONSULTING: ['consulting', 'advisor', 'strategy', 'management consulting'],
                CareerField.ENGINEERING: ['engineering', 'mechanical', 'electrical', 'civil', 'design'],
                CareerField.DATA_SCIENCE: ['data', 'analytics', 'machine learning', 'statistics', 'research'],
                CareerField.PRODUCT_MANAGEMENT: ['product', 'product manager', 'strategy', 'roadmap', 'agile']
            }
            
            # Combine experience and skills text
            combined_text = ' '.join([
                str(exp.get('title', '')) + ' ' + str(exp.get('description', '')) 
                for exp in experience
            ] + skills).lower()
            
            # Count field keyword matches
            field_scores = {}
            for field, keywords in field_keywords.items():
                score = sum(1 for keyword in keywords if keyword in combined_text)
                field_scores[field] = score
            
            # Return field with highest score, default to TECHNOLOGY
            if field_scores:
                return max(field_scores, key=field_scores.get)
            else:
                return CareerField.TECHNOLOGY
                
        except Exception as e:
            logger.error(f"Error determining career field: {e}")
            return CareerField.TECHNOLOGY
    
    def _determine_experience_level(self, experience: List[Dict]) -> ExperienceLevel:
        """Determine experience level from work history"""
        try:
            if not experience:
                return ExperienceLevel.ENTRY
            
            # Count years of experience
            total_years = 0
            for exp in experience:
                if 'duration' in exp:
                    # Parse duration (simplified)
                    duration = str(exp['duration']).lower()
                    if 'year' in duration:
                        years = 1
                        if any(char.isdigit() for char in duration):
                            # Extract number
                            import re
                            numbers = re.findall(r'\d+', duration)
                            if numbers:
                                years = int(numbers[0])
                        total_years += years
            
            # Determine level based on years
            if total_years < 2:
                return ExperienceLevel.ENTRY
            elif total_years < 5:
                return ExperienceLevel.MID
            elif total_years < 10:
                return ExperienceLevel.SENIOR
            else:
                return ExperienceLevel.EXECUTIVE
                
        except Exception as e:
            logger.error(f"Error determining experience level: {e}")
            return ExperienceLevel.MID
    
    def _estimate_current_salary(self, parsed_data: Dict[str, Any], location: str) -> int:
        """Estimate current salary from resume data"""
        try:
            # Try to get from advanced analytics first
            income_potential = parsed_data.get('advanced_analytics', {}).get('income_potential', {})
            if income_potential and 'estimated_current_salary' in income_potential:
                return int(income_potential['estimated_current_salary'])
            
            # Fallback estimation based on experience and field
            experience = parsed_data.get('parsed_data', {}).get('experience', [])
            skills = parsed_data.get('parsed_data', {}).get('skills', [])
            
            # Base salary by experience level
            experience_level = self._determine_experience_level(experience)
            base_salaries = {
                ExperienceLevel.ENTRY: 50000,
                ExperienceLevel.MID: 75000,
                ExperienceLevel.SENIOR: 100000,
                ExperienceLevel.EXECUTIVE: 150000
            }
            
            base_salary = base_salaries.get(experience_level, 75000)
            
            # Location adjustment
            location_multipliers = {
                'New York': 1.3,
                'San Francisco': 1.4,
                'Seattle': 1.2,
                'Boston': 1.2,
                'Los Angeles': 1.1,
                'Chicago': 1.0,
                'Atlanta': 0.9,
                'Dallas': 0.9
            }
            
            multiplier = location_multipliers.get(location, 1.0)
            
            return int(base_salary * multiplier)
            
        except Exception as e:
            logger.error(f"Error estimating current salary: {e}")
            return 75000  # Default salary
    
    def _convert_to_job_objects(self, job_data: List[Dict[str, Any]]) -> List:
        """Convert job data back to JobOpportunity objects"""
        # This would convert the serialized job data back to JobOpportunity objects
        # For now, return the data as-is since the three-tier selector can work with it
        return job_data
    
    def _create_error_response(self, error_type: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'success': False,
            'error_type': error_type,
            'error_message': error_message,
            'timestamp': datetime.now().isoformat(),
            'processing_metrics': asdict(self.metrics)
        }
    
    def _track_workflow_start(self, session_id: str, user_id: str, content: str):
        """Track workflow start"""
        try:
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO workflow_sessions 
                (session_id, user_id, resume_content_hash, status) 
                VALUES (%s, %s, %s, %s)
            ''', (session_id, user_id, content_hash, ProcessingStatus.IN_PROGRESS.value))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error tracking workflow start: {e}")
    
    def _track_workflow_completion(self, session_id: str, total_time: float, result_data: Dict[str, Any]):
        """Track workflow completion"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE workflow_sessions 
                SET status = %s, completed_at = CURRENT_TIMESTAMP, 
                    total_processing_time = %s, result_data = %s
                WHERE session_id = %s
            ''', (ProcessingStatus.COMPLETED.value, total_time, json.dumps(result_data), session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error tracking workflow completion: {e}")
    
    def _track_workflow_error(self, session_id: str, error_message: str):
        """Track workflow error"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE workflow_sessions 
                SET status = %s, error_message = %s
                WHERE session_id = %s
            ''', (ProcessingStatus.FAILED.value, error_message, session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error tracking workflow error: {e}")
    
    async def _track_analytics(self, user_id: str, session_id: str, event_type: str, event_data: Dict[str, Any]):
        """Track user analytics"""
        try:
            conn = get_pg_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_analytics 
                (user_id, session_id, event_type, event_data) 
                VALUES (%s, %s, %s, %s)
            ''', (user_id, session_id, event_type, json.dumps(event_data)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error tracking analytics: {e}")
    
    def _update_metrics(self, workflow_steps: List[WorkflowStep], total_time: float):
        """Update processing metrics"""
        self.metrics.total_time = total_time
        
        # Update step-specific times
        for step in workflow_steps:
            if step.duration:
                if step.step_name == "resume_parsing":
                    self.metrics.resume_parsing_time = step.duration
                elif step.step_name == "market_research":
                    self.metrics.market_research_time = step.duration
                elif step.step_name == "job_search":
                    self.metrics.job_search_time = step.duration
                elif step.step_name == "recommendation_generation":
                    self.metrics.recommendation_generation_time = step.duration
                elif step.step_name == "results_formatting":
                    self.metrics.formatting_time = step.duration
        
        # Count errors and warnings
        self.metrics.errors_count = len([s for s in workflow_steps if s.status == ProcessingStatus.FAILED])
        self.metrics.warnings_count = len([s for s in workflow_steps if s.error_message and s.status != ProcessingStatus.FAILED])
    
    # Placeholder methods for additional functionality
    def _get_salary_benchmarks(self, parsed_data: Dict, location: str) -> Dict[str, Any]:
        """Get salary benchmarks for the role and location"""
        return {"location": location, "benchmarks": {}}
    
    def _get_industry_trends(self, parsed_data: Dict) -> Dict[str, Any]:
        """Get industry trends and insights"""
        return {"trends": []}
    
    def _identify_growth_opportunities(self, parsed_data: Dict) -> List[str]:
        """Identify growth opportunities"""
        return []
    
    def _analyze_skill_demand(self, parsed_data: Dict, location: str) -> Dict[str, Any]:
        """Analyze skill demand in the market"""
        return {"demand": {}}
    
    def _extract_priority_actions(self, recommendation: Dict) -> List[str]:
        """Extract priority actions from recommendation"""
        return []
    
    def _create_timeline(self, recommendation: Dict) -> Dict[str, str]:
        """Create timeline for recommendation"""
        return {}
    
    def _identify_success_factors(self, recommendation: Dict) -> List[str]:
        """Identify success factors for recommendation"""
        return []
    
    def _generate_insights(self, parsed_data: Dict, recommendations_data: Dict) -> Dict[str, Any]:
        """Generate personalized career insights"""
        return {"insights": []}
    
    def _create_action_plan(self, recommendations_data: Dict, strategies_data: Dict) -> Dict[str, Any]:
        """Create specific next steps for user"""
        return {"action_plan": []}
    
    def _generate_next_steps(self, recommendations_data: Dict) -> List[str]:
        """Generate next steps for user"""
        return []
