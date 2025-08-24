"""
Intelligent Job Matching System
Prioritizes income advancement opportunities based on resume analysis and demographic income comparisons
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict, Counter
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .resume_parser import AdvancedResumeParser, FieldType, ExperienceLevel
from ..job_security_predictor import JobSecurityPredictor

logger = logging.getLogger(__name__)

class CompanyTier(str, Enum):
    """Company tier classification for compensation reliability"""
    FORTUNE_500 = "fortune_500"
    GROWTH_COMPANY = "growth_company"
    STARTUP = "startup"
    ESTABLISHED = "established"
    UNKNOWN = "unknown"

class JobSource(str, Enum):
    """Job posting sources"""
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    ZIPRECRUITER = "ziprecruiter"
    COMPANY_CAREERS = "company_careers"
    ANGEL_LIST = "angel_list"

@dataclass
class SalaryRange:
    """Salary range with validation"""
    min_salary: int
    max_salary: int
    currency: str = "USD"
    confidence: float = 0.8
    
    def __post_init__(self):
        if self.min_salary > self.max_salary:
            self.min_salary, self.max_salary = self.max_salary, self.min_salary
    
    @property
    def midpoint(self) -> int:
        return (self.min_salary + self.max_salary) // 2
    
    @property
    def range_width(self) -> int:
        return self.max_salary - self.min_salary

@dataclass
class JobPosting:
    """Job posting data structure"""
    id: str
    title: str
    company: str
    location: str
    salary_range: Optional[SalaryRange] = None
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    experience_level: str = ""
    field: str = ""
    industry: str = ""
    remote_work: bool = False
    source: JobSource = JobSource.LINKEDIN
    posted_date: Optional[datetime] = None
    company_tier: CompanyTier = CompanyTier.UNKNOWN
    company_size: str = ""
    funding_stage: str = ""
    glassdoor_rating: Optional[float] = None
    application_count: Optional[int] = None
    
    def __post_init__(self):
        if isinstance(self.posted_date, str):
            try:
                self.posted_date = datetime.fromisoformat(self.posted_date.replace('Z', '+00:00'))
            except:
                self.posted_date = None

@dataclass
class JobScore:
    """Job scoring results"""
    job: JobPosting
    overall_score: float
    salary_improvement_score: float
    skills_alignment_score: float
    career_progression_score: float
    company_stability_score: float
    location_compatibility_score: float
    growth_potential_score: float
    score_breakdown: Dict[str, float]
    recommendations: List[str]
    risk_factors: List[str]

@dataclass
class SearchParameters:
    """Job search parameters"""
    current_salary: int
    target_salary_min: int
    primary_field: FieldType
    experience_level: ExperienceLevel
    skills: List[str]
    locations: List[str]
    remote_preference: bool = True
    min_salary_increase: float = 0.15  # 15% minimum increase
    max_search_radius: int = 50  # miles
    company_tier_preference: List[CompanyTier] = field(default_factory=list)

class IntelligentJobMatcher:
    """
    Intelligent job matching system that prioritizes income advancement opportunities
    """
    
    def __init__(self):
        """Initialize the intelligent job matcher"""
        self.resume_parser = AdvancedResumeParser()
        self.job_security_predictor = JobSecurityPredictor()
        
        # Target MSAs for job search
        self.target_msas = [
            'Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City',
            'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore'
        ]
        
        # Job scoring weights
        self.scoring_weights = {
            'salary_improvement': 0.35,
            'skills_match': 0.25,
            'career_progression': 0.20,
            'company_quality': 0.10,
            'location_fit': 0.05,
            'industry_alignment': 0.05
        }
        
        # Company tier scoring
        self.company_tier_scores = {
            CompanyTier.FORTUNE_500: 0.9,
            CompanyTier.GROWTH_COMPANY: 0.8,
            CompanyTier.ESTABLISHED: 0.7,
            CompanyTier.STARTUP: 0.6,
            CompanyTier.UNKNOWN: 0.5
        }
        
        # Experience level progression mapping
        self.career_progression = {
            ExperienceLevel.ENTRY: [ExperienceLevel.MID],
            ExperienceLevel.MID: [ExperienceLevel.SENIOR],
            ExperienceLevel.SENIOR: ['Manager', 'Director', 'Principal']
        }
        
        # Field-specific salary multipliers
        self.field_salary_multipliers = {
            FieldType.SOFTWARE_DEVELOPMENT: 1.2,
            FieldType.DATA_ANALYSIS: 1.1,
            FieldType.PROJECT_MANAGEMENT: 1.0,
            FieldType.MARKETING: 0.95,
            FieldType.FINANCE: 1.05,
            FieldType.SALES: 0.9,
            FieldType.OPERATIONS: 0.95,
            FieldType.HR: 0.9
        }
        
        # Initialize job sources
        self.job_sources = self._initialize_job_sources()
        
        # Cache for job search results
        self.search_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
    def _initialize_job_sources(self) -> Dict[str, Any]:
        """Initialize job search sources"""
        return {
            'linkedin': {
                'api_key': None,  # Set in environment
                'base_url': 'https://api.linkedin.com/v2',
                'enabled': True
            },
            'indeed': {
                'api_key': None,  # Set in environment
                'base_url': 'https://api.indeed.com',
                'enabled': True
            },
            'glassdoor': {
                'api_key': None,  # Set in environment
                'base_url': 'https://api.glassdoor.com',
                'enabled': True
            }
        }
    
    def find_income_advancement_jobs(self, user_id: int, resume_text: str, 
                                   current_salary: int, target_locations: List[str] = None) -> Dict[str, Any]:
        """
        Find jobs that offer significant income advancement opportunities
        
        Args:
            user_id: User ID
            resume_text: User's resume text
            current_salary: Current annual salary
            target_locations: Preferred locations (defaults to target MSAs)
            
        Returns:
            Dictionary with job recommendations and analysis
        """
        try:
            logger.info(f"Starting income advancement job search for user {user_id}")
            
            # Parse resume to get user profile
            resume_analysis = self.resume_parser.parse_resume(resume_text)
            
            # Calculate target salary based on income gap analysis
            target_salary = self._calculate_target_salary(current_salary, resume_analysis)
            
            # Set up search parameters
            search_params = SearchParameters(
                current_salary=current_salary,
                target_salary_min=target_salary,
                primary_field=resume_analysis.field_analysis.primary_field,
                experience_level=resume_analysis.experience_analysis.level,
                skills=list(resume_analysis.skills_analysis.technical_skills.keys()) + 
                       list(resume_analysis.skills_analysis.business_skills.keys()),
                locations=target_locations or self.target_msas,
                remote_preference=True
            )
            
            # Search for jobs
            job_postings = self._search_jobs(search_params)
            
            # Score and rank jobs
            scored_jobs = self._score_jobs(job_postings, search_params, resume_analysis)
            
            # Filter by minimum salary increase
            filtered_jobs = self._filter_by_salary_threshold(scored_jobs, search_params)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(filtered_jobs, resume_analysis, search_params)
            
            # Calculate search statistics
            search_stats = self._calculate_search_statistics(filtered_jobs, search_params)
            
            return {
                'user_profile': self.resume_parser.get_analysis_summary(resume_analysis),
                'search_parameters': {
                    'current_salary': current_salary,
                    'target_salary': target_salary,
                    'min_increase_percentage': search_params.min_salary_increase * 100,
                    'target_locations': search_params.locations
                },
                'job_recommendations': [self._format_job_recommendation(job) for job in filtered_jobs[:20]],
                'recommendations': recommendations,
                'search_statistics': search_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in income advancement job search: {str(e)}")
            raise
    
    def _calculate_target_salary(self, current_salary: int, resume_analysis: Any) -> int:
        """Calculate target salary based on income gap analysis"""
        base_multiplier = 1.25  # 25% increase as baseline
        
        # Adjust based on field
        field_multiplier = self.field_salary_multipliers.get(
            resume_analysis.field_analysis.primary_field, 1.0
        )
        
        # Adjust based on experience level
        experience_multiplier = {
            ExperienceLevel.ENTRY: 1.15,  # 15% increase for entry level
            ExperienceLevel.MID: 1.25,    # 25% increase for mid level
            ExperienceLevel.SENIOR: 1.35  # 35% increase for senior level
        }.get(resume_analysis.experience_analysis.level, 1.25)
        
        # Adjust based on leadership potential
        leadership_bonus = 1.0 + (resume_analysis.leadership_potential * 0.1)
        
        # Calculate target salary
        target_salary = int(current_salary * base_multiplier * field_multiplier * 
                           experience_multiplier * leadership_bonus)
        
        # Ensure minimum 15% increase
        min_target = int(current_salary * 1.15)
        target_salary = max(target_salary, min_target)
        
        logger.info(f"Target salary calculated: {current_salary} -> {target_salary} "
                   f"({(target_salary/current_salary-1)*100:.1f}% increase)")
        
        return target_salary
    
    def _search_jobs(self, search_params: SearchParameters) -> List[JobPosting]:
        """Search for jobs across multiple sources"""
        logger.info(f"Searching jobs for {search_params.primary_field.value} in {search_params.locations}")
        
        all_jobs = []
        
        # Generate search queries
        search_queries = self._generate_search_queries(search_params)
        
        # Search across multiple sources in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {}
            
            for source_name, source_config in self.job_sources.items():
                if source_config['enabled']:
                    for query in search_queries:
                        future = executor.submit(
                            self._search_single_source, 
                            source_name, 
                            query, 
                            search_params
                        )
                        future_to_source[future] = source_name
            
            # Collect results
            for future in as_completed(future_to_source):
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                    logger.info(f"Found {len(jobs)} jobs from {future_to_source[future]}")
                except Exception as e:
                    logger.error(f"Error searching {future_to_source[future]}: {str(e)}")
        
        # Remove duplicates
        unique_jobs = self._deduplicate_jobs(all_jobs)
        
        logger.info(f"Total unique jobs found: {len(unique_jobs)}")
        return unique_jobs
    
    def _generate_search_queries(self, search_params: SearchParameters) -> List[str]:
        """Generate optimized search queries for job search"""
        queries = []
        
        # Primary field queries
        field_queries = self._get_field_specific_queries(search_params.primary_field)
        
        # Experience level queries
        experience_queries = self._get_experience_queries(search_params.experience_level)
        
        # Combine field and experience
        for field_query in field_queries:
            for exp_query in experience_queries:
                queries.append(f"{field_query} {exp_query}")
        
        # Skills-based queries
        for skill in search_params.skills[:5]:  # Top 5 skills
            queries.append(f"{skill} {search_params.primary_field.value}")
        
        # Remote work queries
        if search_params.remote_preference:
            queries.extend([f"{q} remote" for q in queries[:3]])
        
        return queries[:10]  # Limit to top 10 queries
    
    def _get_field_specific_queries(self, field: FieldType) -> List[str]:
        """Get field-specific search queries"""
        field_queries = {
            FieldType.DATA_ANALYSIS: [
                "Data Analyst", "Business Intelligence Analyst", "Data Scientist",
                "Analytics Manager", "Data Engineer", "Business Analyst"
            ],
            FieldType.SOFTWARE_DEVELOPMENT: [
                "Software Engineer", "Software Developer", "Full Stack Developer",
                "Backend Developer", "Frontend Developer", "DevOps Engineer"
            ],
            FieldType.PROJECT_MANAGEMENT: [
                "Project Manager", "Program Manager", "Product Manager",
                "Technical Project Manager", "Scrum Master", "Agile Coach"
            ],
            FieldType.MARKETING: [
                "Marketing Manager", "Digital Marketing Specialist", "Marketing Analyst",
                "Brand Manager", "Growth Marketing Manager", "Marketing Director"
            ],
            FieldType.FINANCE: [
                "Financial Analyst", "Finance Manager", "Investment Analyst",
                "Financial Controller", "Treasury Analyst", "FP&A Analyst"
            ],
            FieldType.SALES: [
                "Sales Manager", "Account Executive", "Sales Representative",
                "Business Development Manager", "Sales Director", "Sales Engineer"
            ],
            FieldType.OPERATIONS: [
                "Operations Manager", "Operations Analyst", "Process Manager",
                "Supply Chain Manager", "Operations Director", "Business Operations"
            ],
            FieldType.HR: [
                "HR Manager", "HR Business Partner", "Talent Acquisition",
                "HR Generalist", "Compensation Analyst", "HR Director"
            ]
        }
        
        return field_queries.get(field, [field.value])
    
    def _get_experience_queries(self, experience_level: ExperienceLevel) -> List[str]:
        """Get experience-level specific queries"""
        if experience_level == ExperienceLevel.ENTRY:
            return ["entry level", "junior", "associate", "trainee"]
        elif experience_level == ExperienceLevel.MID:
            return ["mid level", "intermediate", "specialist", "senior"]
        else:  # Senior
            return ["senior", "lead", "principal", "manager", "director"]
    
    def _search_single_source(self, source_name: str, query: str, 
                            search_params: SearchParameters) -> List[JobPosting]:
        """Search a single job source"""
        try:
            # This would integrate with actual job APIs
            # For now, return mock data
            return self._get_mock_jobs(source_name, query, search_params)
        except Exception as e:
            logger.error(f"Error searching {source_name}: {str(e)}")
            return []
    
    def _get_mock_jobs(self, source_name: str, query: str, 
                      search_params: SearchParameters) -> List[JobPosting]:
        """Generate mock job data for demonstration"""
        mock_jobs = []
        
        # Generate jobs based on query and search parameters
        base_salary = search_params.target_salary_min
        
        for i in range(5):  # Generate 5 mock jobs per query
            salary_multiplier = 1.0 + (i * 0.1)  # 0%, 10%, 20%, 30%, 40% above target
            salary = int(base_salary * salary_multiplier)
            
            job = JobPosting(
                id=f"{source_name}_{query}_{i}",
                title=f"{query} - Mock Job {i+1}",
                company=f"Mock Company {i+1}",
                location=search_params.locations[i % len(search_params.locations)],
                salary_range=SalaryRange(
                    min_salary=int(salary * 0.9),
                    max_salary=int(salary * 1.1),
                    confidence=0.8
                ),
                description=f"Mock job description for {query}",
                requirements=["Python", "SQL", "Analytics"],
                skills=["python", "sql", "analytics"],
                experience_level=search_params.experience_level.value,
                field=search_params.primary_field.value,
                industry="Technology",
                remote_work=i % 2 == 0,
                source=JobSource(source_name.lower()),
                posted_date=datetime.utcnow() - timedelta(days=i),
                company_tier=CompanyTier.GROWTH_COMPANY if i % 2 == 0 else CompanyTier.ESTABLISHED,
                company_size="100-500 employees",
                glassdoor_rating=4.0 + (i * 0.1)
            )
            
            mock_jobs.append(job)
        
        return mock_jobs
    
    def _deduplicate_jobs(self, jobs: List[JobPosting]) -> List[JobPosting]:
        """Remove duplicate job postings"""
        seen_ids = set()
        unique_jobs = []
        
        for job in jobs:
            # Create a unique identifier based on title, company, and location
            job_id = f"{job.title}_{job.company}_{job.location}".lower()
            
            if job_id not in seen_ids:
                seen_ids.add(job_id)
                unique_jobs.append(job)
        
        return unique_jobs
    
    def _score_jobs(self, jobs: List[JobPosting], search_params: SearchParameters, 
                   resume_analysis: Any) -> List[JobScore]:
        """Score jobs based on multiple criteria"""
        logger.info(f"Scoring {len(jobs)} jobs")
        
        scored_jobs = []
        
        for job in jobs:
            try:
                # Calculate individual scores
                salary_score = self._calculate_salary_improvement_score(job, search_params)
                skills_score = self._calculate_skills_alignment_score(job, search_params)
                career_score = self._calculate_career_progression_score(job, search_params, resume_analysis)
                company_score = self._calculate_company_stability_score(job)
                location_score = self._calculate_location_compatibility_score(job, search_params)
                growth_score = self._calculate_growth_potential_score(job, resume_analysis)
                
                # Calculate weighted overall score
                overall_score = (
                    salary_score * self.scoring_weights['salary_improvement'] +
                    skills_score * self.scoring_weights['skills_match'] +
                    career_score * self.scoring_weights['career_progression'] +
                    company_score * self.scoring_weights['company_quality'] +
                    location_score * self.scoring_weights['location_fit'] +
                    growth_score * self.scoring_weights['industry_alignment']
                )
                
                # Generate recommendations and risk factors
                recommendations = self._generate_job_recommendations(job, search_params)
                risk_factors = self._identify_job_risk_factors(job, search_params)
                
                # Create job score
                job_score = JobScore(
                    job=job,
                    overall_score=overall_score,
                    salary_improvement_score=salary_score,
                    skills_alignment_score=skills_score,
                    career_progression_score=career_score,
                    company_stability_score=company_score,
                    location_compatibility_score=location_score,
                    growth_potential_score=growth_score,
                    score_breakdown={
                        'salary_improvement': salary_score,
                        'skills_match': skills_score,
                        'career_progression': career_score,
                        'company_quality': company_score,
                        'location_fit': location_score,
                        'growth_potential': growth_score
                    },
                    recommendations=recommendations,
                    risk_factors=risk_factors
                )
                
                scored_jobs.append(job_score)
                
            except Exception as e:
                logger.error(f"Error scoring job {job.id}: {str(e)}")
                continue
        
        # Sort by overall score
        scored_jobs.sort(key=lambda x: x.overall_score, reverse=True)
        
        logger.info(f"Successfully scored {len(scored_jobs)} jobs")
        return scored_jobs
    
    def _calculate_salary_improvement_score(self, job: JobPosting, 
                                          search_params: SearchParameters) -> float:
        """Calculate salary improvement score"""
        if not job.salary_range:
            return 0.5  # Neutral score for unknown salary
        
        # Calculate percentage increase
        salary_increase = (job.salary_range.midpoint - search_params.current_salary) / search_params.current_salary
        
        # Score based on increase percentage
        if salary_increase >= 0.45:  # 45%+ increase
            return 1.0
        elif salary_increase >= 0.35:  # 35%+ increase
            return 0.9
        elif salary_increase >= 0.25:  # 25%+ increase
            return 0.8
        elif salary_increase >= 0.15:  # 15%+ increase
            return 0.7
        elif salary_increase >= 0.10:  # 10%+ increase
            return 0.6
        elif salary_increase >= 0.05:  # 5%+ increase
            return 0.5
        else:
            return 0.3  # Below 5% increase
    
    def _calculate_skills_alignment_score(self, job: JobPosting, 
                                        search_params: SearchParameters) -> float:
        """Calculate skills alignment score"""
        if not job.requirements:
            return 0.5  # Neutral score for unknown requirements
        
        # Convert to lowercase for comparison
        job_requirements = set(req.lower() for req in job.requirements)
        user_skills = set(skill.lower() for skill in search_params.skills)
        
        # Calculate match percentage
        if not job_requirements:
            return 0.5
        
        matches = job_requirements.intersection(user_skills)
        match_percentage = len(matches) / len(job_requirements)
        
        # Score based on match percentage
        if match_percentage >= 0.8:
            return 1.0
        elif match_percentage >= 0.6:
            return 0.8
        elif match_percentage >= 0.4:
            return 0.6
        elif match_percentage >= 0.2:
            return 0.4
        else:
            return 0.2
    
    def _calculate_career_progression_score(self, job: JobPosting, 
                                          search_params: SearchParameters,
                                          resume_analysis: Any) -> float:
        """Calculate career progression score"""
        current_level = search_params.experience_level
        job_title = job.title.lower()
        
        # Check if job represents progression
        if current_level == ExperienceLevel.ENTRY:
            if any(word in job_title for word in ['senior', 'lead', 'manager', 'director']):
                return 1.0
            elif any(word in job_title for word in ['specialist', 'analyst']):
                return 0.8
            else:
                return 0.5
        elif current_level == ExperienceLevel.MID:
            if any(word in job_title for word in ['manager', 'director', 'principal']):
                return 1.0
            elif any(word in job_title for word in ['senior', 'lead']):
                return 0.8
            else:
                return 0.6
        else:  # Senior level
            if any(word in job_title for word in ['director', 'principal', 'head', 'vp']):
                return 1.0
            elif any(word in job_title for word in ['manager', 'lead']):
                return 0.7
            else:
                return 0.5
    
    def _calculate_company_stability_score(self, job: JobPosting) -> float:
        """Calculate company stability score"""
        # Base score from company tier
        base_score = self.company_tier_scores.get(job.company_tier, 0.5)
        
        # Adjust based on Glassdoor rating
        if job.glassdoor_rating:
            rating_bonus = (job.glassdoor_rating - 3.0) * 0.1  # -0.1 to +0.2
            base_score = min(1.0, base_score + rating_bonus)
        
        # Adjust based on company size
        if '1000+' in job.company_size or 'fortune' in job.company_size.lower():
            base_score = min(1.0, base_score + 0.1)
        
        return base_score
    
    def _calculate_location_compatibility_score(self, job: JobPosting, 
                                              search_params: SearchParameters) -> float:
        """Calculate location compatibility score"""
        # Check if location is in preferred locations
        job_location = job.location.lower()
        preferred_locations = [loc.lower() for loc in search_params.locations]
        
        if any(pref_loc in job_location for pref_loc in preferred_locations):
            return 1.0
        elif job.remote_work and search_params.remote_preference:
            return 0.9
        else:
            return 0.3
    
    def _calculate_growth_potential_score(self, job: JobPosting, 
                                        resume_analysis: Any) -> float:
        """Calculate growth potential score"""
        # Base score from company tier
        base_score = self.company_tier_scores.get(job.company_tier, 0.5)
        
        # Adjust based on industry alignment
        if job.field == resume_analysis.field_analysis.primary_field.value:
            base_score = min(1.0, base_score + 0.2)
        
        # Adjust based on remote work (expands opportunities)
        if job.remote_work:
            base_score = min(1.0, base_score + 0.1)
        
        return base_score
    
    def _filter_by_salary_threshold(self, scored_jobs: List[JobScore], 
                                  search_params: SearchParameters) -> List[JobScore]:
        """Filter jobs by minimum salary increase threshold"""
        filtered_jobs = []
        
        for job_score in scored_jobs:
            if job_score.job.salary_range:
                salary_increase = (job_score.job.salary_range.midpoint - search_params.current_salary) / search_params.current_salary
                
                if salary_increase >= search_params.min_salary_increase:
                    filtered_jobs.append(job_score)
            else:
                # Include jobs with unknown salary but high overall score
                if job_score.overall_score >= 0.7:
                    filtered_jobs.append(job_score)
        
        logger.info(f"Filtered to {len(filtered_jobs)} jobs meeting salary threshold")
        return filtered_jobs
    
    def _generate_job_recommendations(self, job: JobPosting, 
                                    search_params: SearchParameters) -> List[str]:
        """Generate specific recommendations for a job"""
        recommendations = []
        
        # Salary recommendations
        if job.salary_range:
            salary_increase = (job.salary_range.midpoint - search_params.current_salary) / search_params.current_salary
            if salary_increase >= 0.25:
                recommendations.append("High salary increase potential - prioritize this opportunity")
            elif salary_increase >= 0.15:
                recommendations.append("Good salary improvement - worth pursuing")
        
        # Skills recommendations
        if job.requirements:
            missing_skills = set(req.lower() for req in job.requirements) - set(skill.lower() for skill in search_params.skills)
            if missing_skills:
                recommendations.append(f"Consider developing: {', '.join(list(missing_skills)[:3])}")
        
        # Company recommendations
        if job.company_tier == CompanyTier.FORTUNE_500:
            recommendations.append("Fortune 500 company - excellent for career growth")
        elif job.company_tier == CompanyTier.GROWTH_COMPANY:
            recommendations.append("High-growth company - potential for rapid advancement")
        
        # Remote work recommendations
        if job.remote_work:
            recommendations.append("Remote opportunity - expands your geographic reach")
        
        return recommendations
    
    def _identify_job_risk_factors(self, job: JobPosting, 
                                 search_params: SearchParameters) -> List[str]:
        """Identify potential risk factors for a job"""
        risk_factors = []
        
        # Salary risks
        if job.salary_range:
            salary_increase = (job.salary_range.midpoint - search_params.current_salary) / search_params.current_salary
            if salary_increase < 0.15:
                risk_factors.append("Below target salary increase")
        
        # Company risks
        if job.company_tier == CompanyTier.STARTUP:
            risk_factors.append("Startup risk - less stable than established companies")
        
        if job.glassdoor_rating and job.glassdoor_rating < 3.5:
            risk_factors.append("Low company rating on Glassdoor")
        
        # Location risks
        if not job.remote_work and job.location not in search_params.locations:
            risk_factors.append("Requires relocation")
        
        return risk_factors
    
    def _generate_recommendations(self, scored_jobs: List[JobScore], 
                                resume_analysis: Any, 
                                search_params: SearchParameters) -> List[Dict[str, Any]]:
        """Generate overall recommendations"""
        recommendations = []
        
        if not scored_jobs:
            recommendations.append({
                'type': 'warning',
                'title': 'No suitable jobs found',
                'description': 'Consider expanding your search criteria or developing additional skills'
            })
            return recommendations
        
        # Top opportunities
        top_jobs = scored_jobs[:5]
        avg_salary_increase = np.mean([
            (job.job.salary_range.midpoint - search_params.current_salary) / search_params.current_salary
            for job in top_jobs if job.job.salary_range
        ])
        
        recommendations.append({
            'type': 'opportunity',
            'title': f'Found {len(scored_jobs)} high-quality opportunities',
            'description': f'Average salary increase: {avg_salary_increase*100:.1f}%'
        })
        
        # Skills development
        missing_skills = self._identify_missing_skills(scored_jobs, search_params)
        if missing_skills:
            recommendations.append({
                'type': 'development',
                'title': 'Skills development opportunities',
                'description': f'Focus on: {", ".join(missing_skills[:3])}'
            })
        
        # Career progression
        progression_opportunities = [job for job in scored_jobs if job.career_progression_score >= 0.8]
        if progression_opportunities:
            recommendations.append({
                'type': 'career',
                'title': f'{len(progression_opportunities)} career advancement opportunities',
                'description': 'These roles represent logical next steps in your career'
            })
        
        return recommendations
    
    def _identify_missing_skills(self, scored_jobs: List[JobScore], 
                               search_params: SearchParameters) -> List[str]:
        """Identify commonly required skills that user lacks"""
        all_requirements = []
        for job in scored_jobs[:10]:  # Top 10 jobs
            all_requirements.extend(job.job.requirements)
        
        requirement_counts = Counter(all_requirements)
        user_skills = set(skill.lower() for skill in search_params.skills)
        
        missing_skills = []
        for req, count in requirement_counts.most_common(10):
            if req.lower() not in user_skills and count >= 2:
                missing_skills.append(req)
        
        return missing_skills[:5]
    
    def _calculate_search_statistics(self, scored_jobs: List[JobScore], 
                                   search_params: SearchParameters) -> Dict[str, Any]:
        """Calculate search statistics"""
        if not scored_jobs:
            return {'total_jobs': 0}
        
        salaries = [job.job.salary_range.midpoint for job in scored_jobs if job.job.salary_range]
        salary_increases = [(salary - search_params.current_salary) / search_params.current_salary for salary in salaries]
        
        return {
            'total_jobs': len(scored_jobs),
            'avg_salary': int(np.mean(salaries)) if salaries else 0,
            'avg_salary_increase': np.mean(salary_increases) if salary_increases else 0,
            'max_salary_increase': max(salary_increases) if salary_increases else 0,
            'remote_opportunities': len([job for job in scored_jobs if job.job.remote_work]),
            'fortune_500_opportunities': len([job for job in scored_jobs if job.job.company_tier == CompanyTier.FORTUNE_500])
        }
    
    def _format_job_recommendation(self, job_score: JobScore) -> Dict[str, Any]:
        """Format job recommendation for API response"""
        job = job_score.job
        
        return {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'salary_range': {
                'min': job.salary_range.min_salary if job.salary_range else None,
                'max': job.salary_range.max_salary if job.salary_range else None,
                'midpoint': job.salary_range.midpoint if job.salary_range else None
            },
            'remote_work': job.remote_work,
            'company_tier': job.company_tier.value,
            'glassdoor_rating': job.glassdoor_rating,
            'posted_date': job.posted_date.isoformat() if job.posted_date else None,
            'overall_score': job_score.overall_score,
            'score_breakdown': job_score.score_breakdown,
            'recommendations': job_score.recommendations,
            'risk_factors': job_score.risk_factors
        } 