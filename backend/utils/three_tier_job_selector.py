#!/usr/bin/env python3
"""
Three-Tier Job Recommendation System for Mingus
Presents opportunities at different risk/reward levels for career advancement

This module provides a comprehensive job recommendation system that categorizes
opportunities into three distinct tiers based on risk/reward profiles:
- Conservative: 15-20% salary increase, high success probability
- Optimal: 25-30% salary increase, moderate stretch
- Stretch: 35%+ salary increase, aspirational goals
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import re
import random
from collections import defaultdict

# Import existing job matching components
from .income_boost_job_matcher import (
    JobOpportunity, CompanyProfile, SearchCriteria, 
    CareerField, ExperienceLevel, JobBoard, IncomeBoostJobMatcher
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobTier(Enum):
    """Job recommendation tiers based on risk/reward profile"""
    CONSERVATIVE = "conservative"
    OPTIMAL = "optimal"
    STRETCH = "stretch"

class SkillCategory(Enum):
    """Skill categories for gap analysis"""
    TECHNICAL = "technical"
    SOFT_SKILLS = "soft_skills"
    LEADERSHIP = "leadership"
    FINANCIAL = "financial"
    COMMUNICATION = "communication"
    ANALYTICAL = "analytical"
    INDUSTRY_SPECIFIC = "industry_specific"

@dataclass
class SkillGap:
    """Represents a skill gap analysis"""
    skill: str
    category: SkillCategory
    current_level: float  # 0-1 scale
    required_level: float  # 0-1 scale
    gap_size: float  # required - current
    priority: str  # "high", "medium", "low"
    learning_time_estimate: str  # "1-3 months", "3-6 months", "6+ months"
    resources: List[str]  # Learning resources and recommendations

@dataclass
class ApplicationStrategy:
    """Customized application strategy for a job"""
    job_id: str
    tier: JobTier
    timeline: Dict[str, str]  # Phase -> timeline
    key_selling_points: List[str]
    potential_challenges: List[str]
    interview_preparation: Dict[str, List[str]]  # Phase -> preparation tasks
    salary_negotiation_tips: List[str]
    networking_opportunities: List[str]
    follow_up_strategy: List[str]

@dataclass
class PreparationRoadmap:
    """Preparation roadmap for becoming competitive"""
    job_id: str
    tier: JobTier
    total_preparation_time: str
    phases: List[Dict[str, Any]]  # Phase details
    skill_development_plan: List[SkillGap]
    networking_plan: List[str]
    portfolio_building: List[str]
    certification_recommendations: List[str]

@dataclass
class TieredJobRecommendation:
    """Complete job recommendation with tier-specific analysis"""
    job: JobOpportunity
    tier: JobTier
    success_probability: float
    salary_increase_potential: float
    skills_gap_analysis: List[SkillGap]
    application_strategy: ApplicationStrategy
    preparation_roadmap: PreparationRoadmap
    diversity_analysis: Dict[str, Any]
    company_culture_fit: float
    career_advancement_potential: float

class ThreeTierJobSelector:
    """
    Three-tier job recommendation system that presents opportunities
    at different risk/reward levels for career advancement
    """
    
    def __init__(self, db_path: str = "backend/job_matching.db"):
        self.db_path = db_path
        self.job_matcher = IncomeBoostJobMatcher(db_path)
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Tier specifications
        self.tier_specs = {
            JobTier.CONSERVATIVE: {
                "salary_increase_min": 0.15,
                "salary_increase_max": 0.20,
                "success_probability_min": 0.70,
                "description": "Similar roles, established companies, proven career path",
                "company_types": ["Fortune 500", "Large Enterprise", "Government"],
                "risk_level": "low"
            },
            JobTier.OPTIMAL: {
                "salary_increase_min": 0.25,
                "salary_increase_max": 0.30,
                "success_probability_min": 0.50,
                "description": "Role elevation, growth companies, manageable skill gaps",
                "company_types": ["Growth Company", "Mid-size", "Scale-up"],
                "risk_level": "medium"
            },
            JobTier.STRETCH: {
                "salary_increase_min": 0.35,
                "salary_increase_max": 0.50,
                "success_probability_min": 0.30,
                "description": "Career pivots, innovation companies, significant skill development",
                "company_types": ["Startup", "Innovation", "High-growth"],
                "risk_level": "high"
            }
        }
        
        # Skill categories for gap analysis
        self.skill_categories = {
            SkillCategory.TECHNICAL: [
                'python', 'javascript', 'java', 'sql', 'aws', 'azure', 'react', 'angular',
                'node.js', 'django', 'flask', 'spring', 'docker', 'kubernetes', 'git',
                'machine learning', 'ai', 'cloud computing', 'devops', 'api', 'rest'
            ],
            SkillCategory.SOFT_SKILLS: [
                'leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
                'creative', 'time management', 'adaptability', 'emotional intelligence'
            ],
            SkillCategory.LEADERSHIP: [
                'team management', 'mentoring', 'strategic planning', 'decision making',
                'change management', 'stakeholder management', 'project leadership'
            ],
            SkillCategory.FINANCIAL: [
                'financial analysis', 'budgeting', 'forecasting', 'p&l', 'roi analysis',
                'cost management', 'investment analysis', 'risk assessment'
            ],
            SkillCategory.COMMUNICATION: [
                'presentation skills', 'public speaking', 'writing', 'negotiation',
                'client relations', 'cross-cultural communication', 'influencing'
            ],
            SkillCategory.ANALYTICAL: [
                'data analysis', 'statistics', 'research', 'metrics', 'kpi development',
                'trend analysis', 'market research', 'competitive analysis'
            ]
        }
        
        self._init_database()
    
    def _init_database(self):
        """Initialize the three-tier job recommendation database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tiered recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tiered_recommendations (
                recommendation_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                success_probability REAL,
                salary_increase_potential REAL,
                skills_gap_analysis TEXT,
                application_strategy TEXT,
                preparation_roadmap TEXT,
                diversity_analysis TEXT,
                company_culture_fit REAL,
                career_advancement_potential REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES job_opportunities (job_id)
            )
        ''')
        
        # Create skills gap analysis table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills_gap_analysis (
                gap_id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                skill TEXT NOT NULL,
                category TEXT NOT NULL,
                current_level REAL,
                required_level REAL,
                gap_size REAL,
                priority TEXT,
                learning_time_estimate TEXT,
                resources TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES job_opportunities (job_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def generate_tiered_recommendations(
        self, 
        criteria: SearchCriteria,
        max_recommendations_per_tier: int = 5
    ) -> Dict[JobTier, List[TieredJobRecommendation]]:
        """
        Generate job recommendations across all three tiers
        
        Args:
            criteria: Job search criteria
            max_recommendations_per_tier: Maximum recommendations per tier
            
        Returns:
            Dictionary mapping tiers to lists of recommendations
        """
        try:
            # Get job opportunities from existing matcher
            job_opportunities = await self.job_matcher.salary_focused_search(criteria)
            
            # Classify jobs into tiers
            tiered_jobs = self._classify_jobs_into_tiers(job_opportunities, criteria)
            
            # Ensure diversity within each tier
            diverse_tiered_jobs = self._ensure_tier_diversity(tiered_jobs)
            
            # Generate comprehensive recommendations
            recommendations = {}
            
            for tier in JobTier:
                tier_jobs = diverse_tiered_jobs.get(tier, [])[:max_recommendations_per_tier]
                tier_recommendations = []
                
                for job in tier_jobs:
                    recommendation = await self._create_comprehensive_recommendation(
                        job, tier, criteria
                    )
                    tier_recommendations.append(recommendation)
                
                recommendations[tier] = tier_recommendations
            
            # Store recommendations in database
            await self._store_tiered_recommendations(recommendations)
            
            logger.info(f"Generated {sum(len(recs) for recs in recommendations.values())} tiered recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating tiered recommendations: {str(e)}")
            return {tier: [] for tier in JobTier}
    
    def _classify_jobs_into_tiers(
        self, 
        jobs: List[JobOpportunity], 
        criteria: SearchCriteria
    ) -> Dict[JobTier, List[JobOpportunity]]:
        """
        Classify jobs into appropriate tiers based on salary increase and risk factors
        
        Args:
            jobs: List of job opportunities
            criteria: Search criteria
            
        Returns:
            Dictionary mapping tiers to job lists
        """
        tiered_jobs = {tier: [] for tier in JobTier}
        
        for job in jobs:
            tier = self.classify_job_tier(job, criteria)
            if tier:
                tiered_jobs[tier].append(job)
        
        # Sort jobs within each tier by overall score
        for tier in JobTier:
            tiered_jobs[tier].sort(key=lambda x: x.overall_score, reverse=True)
        
        return tiered_jobs
    
    def classify_job_tier(self, job: JobOpportunity, criteria: SearchCriteria) -> Optional[JobTier]:
        """
        Determine appropriate tier for a job opportunity
        
        Args:
            job: Job opportunity to classify
            criteria: Search criteria
            
        Returns:
            Appropriate tier or None if job doesn't fit any tier
        """
        try:
            # Calculate salary increase potential
            if job.salary_median and criteria.current_salary:
                salary_increase = (job.salary_median - criteria.current_salary) / criteria.current_salary
            else:
                salary_increase = job.salary_increase_potential
            
            # Calculate success probability factors
            success_factors = self._calculate_success_factors(job, criteria)
            
            # Classify based on salary increase and success probability
            if (self.tier_specs[JobTier.CONSERVATIVE]["salary_increase_min"] <= salary_increase <= 
                self.tier_specs[JobTier.CONSERVATIVE]["salary_increase_max"] and
                success_factors >= self.tier_specs[JobTier.CONSERVATIVE]["success_probability_min"]):
                return JobTier.CONSERVATIVE
            
            elif (self.tier_specs[JobTier.OPTIMAL]["salary_increase_min"] <= salary_increase <= 
                  self.tier_specs[JobTier.OPTIMAL]["salary_increase_max"] and
                  success_factors >= self.tier_specs[JobTier.OPTIMAL]["success_probability_min"]):
                return JobTier.OPTIMAL
            
            elif (salary_increase >= self.tier_specs[JobTier.STRETCH]["salary_increase_min"] and
                  success_factors >= self.tier_specs[JobTier.STRETCH]["success_probability_min"]):
                return JobTier.STRETCH
            
            return None
            
        except Exception as e:
            logger.error(f"Error classifying job tier: {str(e)}")
            return None
    
    def _calculate_success_factors(self, job: JobOpportunity, criteria: SearchCriteria) -> float:
        """
        Calculate success probability factors for a job
        
        Args:
            job: Job opportunity
            criteria: Search criteria
            
        Returns:
            Success probability score (0-1)
        """
        try:
            factors = []
            
            # Experience level match
            if job.experience_level == criteria.experience_level:
                factors.append(0.9)
            elif self._is_experience_upgrade(job.experience_level, criteria.experience_level):
                factors.append(0.7)
            else:
                factors.append(0.4)
            
            # Career field match
            if job.field == criteria.career_field:
                factors.append(0.9)
            else:
                factors.append(0.6)
            
            # Company size preference
            if criteria.company_size_preference:
                if self._matches_company_size(job.company_size, criteria.company_size_preference):
                    factors.append(0.8)
                else:
                    factors.append(0.6)
            else:
                factors.append(0.7)
            
            # Location preference
            if criteria.preferred_msas and job.msa in criteria.preferred_msas:
                factors.append(0.9)
            elif criteria.remote_ok and job.remote_friendly:
                factors.append(0.8)
            else:
                factors.append(0.6)
            
            # Company quality scores
            factors.append(job.diversity_score / 100)
            factors.append(job.growth_score / 100)
            factors.append(job.culture_score / 100)
            
            return sum(factors) / len(factors)
            
        except Exception as e:
            logger.error(f"Error calculating success factors: {str(e)}")
            return 0.5
    
    def _is_experience_upgrade(self, job_level: ExperienceLevel, current_level: ExperienceLevel) -> bool:
        """Check if job level is an appropriate upgrade from current level"""
        level_hierarchy = {
            ExperienceLevel.ENTRY: 1,
            ExperienceLevel.MID: 2,
            ExperienceLevel.SENIOR: 3,
            ExperienceLevel.EXECUTIVE: 4
        }
        
        return level_hierarchy.get(job_level, 0) > level_hierarchy.get(current_level, 0)
    
    def _matches_company_size(self, job_size: Optional[str], preferred_size: str) -> bool:
        """Check if job company size matches preference"""
        if not job_size:
            return False
        
        size_mapping = {
            "startup": ["startup", "small"],
            "mid": ["mid", "medium", "mid-size"],
            "large": ["large", "enterprise", "fortune 500"]
        }
        
        job_size_lower = job_size.lower()
        preferred_sizes = size_mapping.get(preferred_size.lower(), [])
        
        return any(size in job_size_lower for size in preferred_sizes)
    
    def _ensure_tier_diversity(
        self, 
        tiered_jobs: Dict[JobTier, List[JobOpportunity]]
    ) -> Dict[JobTier, List[JobOpportunity]]:
        """
        Ensure diversity across industries, company sizes, and locations within each tier
        
        Args:
            tiered_jobs: Jobs organized by tier
            
        Returns:
            Diversified jobs by tier
        """
        try:
            diversified = {}
            
            for tier, jobs in tiered_jobs.items():
                if not jobs:
                    diversified[tier] = []
                    continue
                
                # Track diversity metrics
                industries = set()
                company_sizes = set()
                locations = set()
                
                diversified_jobs = []
                
                # First pass: Add jobs that increase diversity
                for job in jobs:
                    job_industry = job.company_industry or "unknown"
                    job_size = job.company_size or "unknown"
                    job_location = job.msa or job.location
                    
                    # Check if this job adds diversity
                    adds_diversity = (
                        job_industry not in industries or
                        job_size not in company_sizes or
                        job_location not in locations
                    )
                    
                    if adds_diversity or len(diversified_jobs) < 3:
                        diversified_jobs.append(job)
                        industries.add(job_industry)
                        company_sizes.add(job_size)
                        locations.add(job_location)
                    
                    if len(diversified_jobs) >= 5:  # Limit per tier
                        break
                
                # Second pass: Fill remaining slots with highest scoring jobs
                if len(diversified_jobs) < 5:
                    remaining_jobs = [job for job in jobs if job not in diversified_jobs]
                    remaining_jobs.sort(key=lambda x: x.overall_score, reverse=True)
                    
                    for job in remaining_jobs[:5 - len(diversified_jobs)]:
                        diversified_jobs.append(job)
                
                diversified[tier] = diversified_jobs
            
            return diversified
            
        except Exception as e:
            logger.error(f"Error ensuring tier diversity: {str(e)}")
            return tiered_jobs
    
    async def _create_comprehensive_recommendation(
        self, 
        job: JobOpportunity, 
        tier: JobTier, 
        criteria: SearchCriteria
    ) -> TieredJobRecommendation:
        """
        Create comprehensive recommendation for a job
        
        Args:
            job: Job opportunity
            tier: Job tier
            criteria: Search criteria
            
        Returns:
            Complete tiered job recommendation
        """
        try:
            # Calculate success probability
            success_probability = self.calculate_success_probability(job, criteria)
            
            # Analyze skills gap
            skills_gap_analysis = self.analyze_skills_gap(job, criteria)
            
            # Generate application strategy
            application_strategy = self.generate_application_strategy(job, tier, criteria)
            
            # Create preparation roadmap
            preparation_roadmap = self.create_preparation_roadmap(job, tier, skills_gap_analysis)
            
            # Calculate salary increase potential
            if job.salary_median and criteria.current_salary:
                salary_increase_potential = (job.salary_median - criteria.current_salary) / criteria.current_salary
            else:
                salary_increase_potential = job.salary_increase_potential
            
            # Analyze diversity and culture fit
            diversity_analysis = self._analyze_diversity_factors(job)
            company_culture_fit = self._calculate_culture_fit(job, criteria)
            career_advancement_potential = self._calculate_advancement_potential(job)
            
            return TieredJobRecommendation(
                job=job,
                tier=tier,
                success_probability=success_probability,
                salary_increase_potential=salary_increase_potential,
                skills_gap_analysis=skills_gap_analysis,
                application_strategy=application_strategy,
                preparation_roadmap=preparation_roadmap,
                diversity_analysis=diversity_analysis,
                company_culture_fit=company_culture_fit,
                career_advancement_potential=career_advancement_potential
            )
            
        except Exception as e:
            logger.error(f"Error creating comprehensive recommendation: {str(e)}")
            # Return minimal recommendation on error
            return TieredJobRecommendation(
                job=job,
                tier=tier,
                success_probability=0.5,
                salary_increase_potential=0.2,
                skills_gap_analysis=[],
                application_strategy=ApplicationStrategy(
                    job_id=job.job_id,
                    tier=tier,
                    timeline={},
                    key_selling_points=[],
                    potential_challenges=[],
                    interview_preparation={},
                    salary_negotiation_tips=[],
                    networking_opportunities=[],
                    follow_up_strategy=[]
                ),
                preparation_roadmap=PreparationRoadmap(
                    job_id=job.job_id,
                    tier=tier,
                    total_preparation_time="3-6 months",
                    phases=[],
                    skill_development_plan=[],
                    networking_plan=[],
                    portfolio_building=[],
                    certification_recommendations=[]
                ),
                diversity_analysis={},
                company_culture_fit=0.5,
                career_advancement_potential=0.5
            )
    
    def calculate_success_probability(self, job: JobOpportunity, criteria: SearchCriteria) -> float:
        """
        Calculate likelihood of job offer success
        
        Args:
            job: Job opportunity
            criteria: Search criteria
            
        Returns:
            Success probability (0-1)
        """
        try:
            # Base success factors
            factors = self._calculate_success_factors(job, criteria)
            
            # Adjust based on tier
            tier_adjustment = {
                JobTier.CONSERVATIVE: 1.1,  # Higher success for conservative
                JobTier.OPTIMAL: 1.0,       # Baseline
                JobTier.STRETCH: 0.8        # Lower success for stretch
            }
            
            adjusted_probability = factors * tier_adjustment.get(job.tier if hasattr(job, 'tier') else JobTier.OPTIMAL, 1.0)
            
            # Ensure probability is within bounds
            return max(0.1, min(0.95, adjusted_probability))
            
        except Exception as e:
            logger.error(f"Error calculating success probability: {str(e)}")
            return 0.5
    
    def analyze_skills_gap(self, job: JobOpportunity, criteria: SearchCriteria) -> List[SkillGap]:
        """
        Identify required vs. current skills and analyze gaps
        
        Args:
            job: Job opportunity
            criteria: Search criteria
            
        Returns:
            List of skill gaps with analysis
        """
        try:
            skills_gaps = []
            
            # Extract required skills from job description and requirements
            required_skills = self._extract_required_skills(job)
            
            # For now, we'll create sample skill gaps based on common patterns
            # In a real implementation, this would analyze the user's resume/profile
            sample_skills = [
                ("Python", SkillCategory.TECHNICAL, 0.6, 0.9),
                ("Leadership", SkillCategory.LEADERSHIP, 0.4, 0.8),
                ("Data Analysis", SkillCategory.ANALYTICAL, 0.7, 0.9),
                ("Project Management", SkillCategory.LEADERSHIP, 0.5, 0.8),
                ("AWS", SkillCategory.TECHNICAL, 0.3, 0.7)
            ]
            
            for skill, category, current, required in sample_skills:
                gap_size = required - current
                priority = "high" if gap_size > 0.4 else "medium" if gap_size > 0.2 else "low"
                
                learning_time = "6+ months" if gap_size > 0.5 else "3-6 months" if gap_size > 0.3 else "1-3 months"
                
                resources = self._get_learning_resources(skill, category)
                
                skills_gaps.append(SkillGap(
                    skill=skill,
                    category=category,
                    current_level=current,
                    required_level=required,
                    gap_size=gap_size,
                    priority=priority,
                    learning_time_estimate=learning_time,
                    resources=resources
                ))
            
            return skills_gaps
            
        except Exception as e:
            logger.error(f"Error analyzing skills gap: {str(e)}")
            return []
    
    def _extract_required_skills(self, job: JobOpportunity) -> List[str]:
        """Extract required skills from job description and requirements"""
        try:
            skills = []
            
            # Extract from job description
            if job.description:
                description_lower = job.description.lower()
                for category, skill_list in self.skill_categories.items():
                    for skill in skill_list:
                        if skill.lower() in description_lower:
                            skills.append(skill)
            
            # Extract from requirements
            if job.requirements:
                for requirement in job.requirements:
                    requirement_lower = requirement.lower()
                    for category, skill_list in self.skill_categories.items():
                        for skill in skill_list:
                            if skill.lower() in requirement_lower:
                                skills.append(skill)
            
            return list(set(skills))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting required skills: {str(e)}")
            return []
    
    def _get_learning_resources(self, skill: str, category: SkillCategory) -> List[str]:
        """Get learning resources for a specific skill"""
        resources = {
            "Python": [
                "Python.org official tutorial",
                "Coursera Python for Everybody",
                "Real Python tutorials",
                "LeetCode Python problems"
            ],
            "Leadership": [
                "Harvard Business Review leadership articles",
                "LinkedIn Learning leadership courses",
                "Mentorship opportunities",
                "Leadership books (e.g., 'The 7 Habits')"
            ],
            "Data Analysis": [
                "Coursera Data Science specialization",
                "Kaggle Learn modules",
                "Tableau Public tutorials",
                "SQL practice on HackerRank"
            ],
            "Project Management": [
                "PMI.org resources",
                "Coursera Project Management courses",
                "Agile/Scrum certifications",
                "Project management software training"
            ],
            "AWS": [
                "AWS Free Tier practice",
                "AWS Training and Certification",
                "A Cloud Guru courses",
                "AWS documentation and tutorials"
            ]
        }
        
        return resources.get(skill, [
            f"Online courses for {skill}",
            f"Practice projects in {skill}",
            f"Professional certification in {skill}",
            f"Industry networking for {skill}"
        ])
    
    def generate_application_strategy(
        self, 
        job: JobOpportunity, 
        tier: JobTier, 
        criteria: SearchCriteria
    ) -> ApplicationStrategy:
        """
        Create customized application approach for each job
        
        Args:
            job: Job opportunity
            tier: Job tier
            criteria: Search criteria
            
        Returns:
            Customized application strategy
        """
        try:
            # Generate tier-specific strategy
            if tier == JobTier.CONSERVATIVE:
                timeline = {
                    "Week 1": "Research company and role thoroughly",
                    "Week 2": "Tailor resume and cover letter",
                    "Week 3": "Submit application and follow up",
                    "Week 4": "Prepare for interviews"
                }
                
                key_selling_points = [
                    "Proven track record in similar roles",
                    "Strong technical skills match",
                    "Experience with established processes",
                    "Reliable and consistent performance"
                ]
                
                challenges = [
                    "Competition from internal candidates",
                    "Need to demonstrate cultural fit",
                    "Salary negotiation within budget constraints"
                ]
                
            elif tier == JobTier.OPTIMAL:
                timeline = {
                    "Week 1-2": "Deep dive into company culture and values",
                    "Week 3": "Customize application materials",
                    "Week 4": "Submit application and network",
                    "Week 5-6": "Intensive interview preparation"
                }
                
                key_selling_points = [
                    "Growth mindset and adaptability",
                    "Transferable skills from current role",
                    "Eagerness to learn and develop",
                    "Track record of taking on challenges"
                ]
                
                challenges = [
                    "Demonstrating readiness for next level",
                    "Addressing skill gaps proactively",
                    "Showing potential for growth"
                ]
                
            else:  # STRETCH
                timeline = {
                    "Month 1": "Skill development and portfolio building",
                    "Month 2": "Networking and industry research",
                    "Month 3": "Application preparation and submission",
                    "Month 4+": "Interview process and follow-up"
                }
                
                key_selling_points = [
                    "Fresh perspective and innovative thinking",
                    "Passion for the industry/role",
                    "Transferable skills from other domains",
                    "Commitment to rapid learning and growth"
                ]
                
                challenges = [
                    "Significant skill development required",
                    "Need to demonstrate potential over experience",
                    "Higher risk of rejection",
                    "Longer preparation timeline"
                ]
            
            # Generate interview preparation tasks
            interview_prep = {
                "Technical": [
                    "Review job-specific technical requirements",
                    "Practice coding problems (if applicable)",
                    "Prepare examples of relevant projects",
                    "Study company's technology stack"
                ],
                "Behavioral": [
                    "Prepare STAR method examples",
                    "Research company values and culture",
                    "Practice common interview questions",
                    "Prepare questions to ask interviewer"
                ],
                "Case Study": [
                    "Practice industry-specific case studies",
                    "Review company's business model",
                    "Prepare analytical frameworks",
                    "Practice presenting solutions"
                ]
            }
            
            # Salary negotiation tips
            salary_tips = [
                "Research market rates for the role and location",
                "Prepare justification for salary requests",
                "Consider total compensation package",
                "Practice negotiation scenarios",
                "Know your walk-away point"
            ]
            
            # Networking opportunities
            networking = [
                f"Connect with {job.company} employees on LinkedIn",
                "Attend industry events and conferences",
                "Join relevant professional associations",
                "Reach out to mutual connections",
                "Engage with company content on social media"
            ]
            
            # Follow-up strategy
            follow_up = [
                "Send thank you email within 24 hours",
                "Follow up on timeline if no response in 1 week",
                "Maintain professional relationship regardless of outcome",
                "Ask for feedback if not selected",
                "Keep door open for future opportunities"
            ]
            
            return ApplicationStrategy(
                job_id=job.job_id,
                tier=tier,
                timeline=timeline,
                key_selling_points=key_selling_points,
                potential_challenges=challenges,
                interview_preparation=interview_prep,
                salary_negotiation_tips=salary_tips,
                networking_opportunities=networking,
                follow_up_strategy=follow_up
            )
            
        except Exception as e:
            logger.error(f"Error generating application strategy: {str(e)}")
            return ApplicationStrategy(
                job_id=job.job_id,
                tier=tier,
                timeline={},
                key_selling_points=[],
                potential_challenges=[],
                interview_preparation={},
                salary_negotiation_tips=[],
                networking_opportunities=[],
                follow_up_strategy=[]
            )
    
    def create_preparation_roadmap(
        self, 
        job: JobOpportunity, 
        tier: JobTier, 
        skills_gaps: List[SkillGap]
    ) -> PreparationRoadmap:
        """
        Outline steps to become competitive for the role
        
        Args:
            job: Job opportunity
            tier: Job tier
            skills_gaps: List of skill gaps to address
            
        Returns:
            Comprehensive preparation roadmap
        """
        try:
            # Determine total preparation time based on tier and skill gaps
            if tier == JobTier.CONSERVATIVE:
                total_time = "2-4 weeks"
                phases = [
                    {
                        "name": "Research and Preparation",
                        "duration": "1-2 weeks",
                        "tasks": [
                            "Research company culture and values",
                            "Study job requirements thoroughly",
                            "Prepare tailored application materials",
                            "Practice common interview questions"
                        ]
                    },
                    {
                        "name": "Application and Follow-up",
                        "duration": "1-2 weeks",
                        "tasks": [
                            "Submit application",
                            "Follow up professionally",
                            "Prepare for interviews",
                            "Network with company employees"
                        ]
                    }
                ]
            elif tier == JobTier.OPTIMAL:
                total_time = "1-3 months"
                phases = [
                    {
                        "name": "Skill Development",
                        "duration": "2-4 weeks",
                        "tasks": [
                            "Address high-priority skill gaps",
                            "Complete relevant online courses",
                            "Practice new skills in projects",
                            "Seek mentorship or guidance"
                        ]
                    },
                    {
                        "name": "Portfolio Building",
                        "duration": "2-3 weeks",
                        "tasks": [
                            "Create relevant project examples",
                            "Update resume with new skills",
                            "Build professional portfolio",
                            "Prepare case study examples"
                        ]
                    },
                    {
                        "name": "Application and Interview Prep",
                        "duration": "1-2 weeks",
                        "tasks": [
                            "Submit application",
                            "Intensive interview preparation",
                            "Network extensively",
                            "Practice role-specific scenarios"
                        ]
                    }
                ]
            else:  # STRETCH
                total_time = "3-6 months"
                phases = [
                    {
                        "name": "Foundation Building",
                        "duration": "4-6 weeks",
                        "tasks": [
                            "Complete comprehensive skill development",
                            "Take multiple relevant courses",
                            "Build foundational knowledge",
                            "Find mentors in the field"
                        ]
                    },
                    {
                        "name": "Portfolio and Experience",
                        "duration": "4-6 weeks",
                        "tasks": [
                            "Complete significant projects",
                            "Build comprehensive portfolio",
                            "Gain relevant experience through volunteering/freelancing",
                            "Create case studies and examples"
                        ]
                    },
                    {
                        "name": "Networking and Industry Immersion",
                        "duration": "2-4 weeks",
                        "tasks": [
                            "Attend industry events and conferences",
                            "Join professional associations",
                            "Build extensive professional network",
                            "Engage with industry thought leaders"
                        ]
                    },
                    {
                        "name": "Application and Interview Process",
                        "duration": "2-4 weeks",
                        "tasks": [
                            "Submit application with strong portfolio",
                            "Prepare for extensive interview process",
                            "Demonstrate learning and growth",
                            "Showcase potential and passion"
                        ]
                    }
                ]
            
            # Skill development plan based on gaps
            skill_development_plan = skills_gaps
            
            # Networking plan
            networking_plan = [
                f"Connect with {job.company} employees on LinkedIn",
                "Join relevant professional groups and associations",
                "Attend industry meetups and conferences",
                "Reach out to alumni from your school/company",
                "Engage with industry content and discussions",
                "Consider informational interviews"
            ]
            
            # Portfolio building recommendations
            portfolio_building = [
                "Create projects that demonstrate required skills",
                "Document your learning journey and growth",
                "Showcase problem-solving abilities",
                "Include metrics and measurable results",
                "Make portfolio easily accessible and professional",
                "Include testimonials and recommendations"
            ]
            
            # Certification recommendations
            certifications = []
            if "python" in job.description.lower():
                certifications.append("Python Institute PCAP or PCPP")
            if "aws" in job.description.lower():
                certifications.append("AWS Cloud Practitioner or Solutions Architect")
            if "project management" in job.description.lower():
                certifications.append("PMP or CAPM certification")
            if "data" in job.description.lower():
                certifications.append("Google Data Analytics Certificate")
            
            return PreparationRoadmap(
                job_id=job.job_id,
                tier=tier,
                total_preparation_time=total_time,
                phases=phases,
                skill_development_plan=skill_development_plan,
                networking_plan=networking_plan,
                portfolio_building=portfolio_building,
                certification_recommendations=certifications
            )
            
        except Exception as e:
            logger.error(f"Error creating preparation roadmap: {str(e)}")
            return PreparationRoadmap(
                job_id=job.job_id,
                tier=tier,
                total_preparation_time="3-6 months",
                phases=[],
                skill_development_plan=[],
                networking_plan=[],
                portfolio_building=[],
                certification_recommendations=[]
            )
    
    def _analyze_diversity_factors(self, job: JobOpportunity) -> Dict[str, Any]:
        """Analyze diversity and inclusion factors for the job"""
        try:
            return {
                "company_diversity_score": job.diversity_score,
                "leadership_diversity": "High" if job.diversity_score > 80 else "Medium" if job.diversity_score > 60 else "Low",
                "inclusive_benefits": len([b for b in job.benefits if any(keyword in b.lower() for keyword in 
                    ["diversity", "inclusion", "equity", "belonging", "unconscious bias", "mentorship"])]),
                "remote_friendly": job.remote_friendly,
                "work_life_balance_score": job.work_life_balance_score
            }
        except Exception as e:
            logger.error(f"Error analyzing diversity factors: {str(e)}")
            return {}
    
    def _calculate_culture_fit(self, job: JobOpportunity, criteria: SearchCriteria) -> float:
        """Calculate company culture fit score"""
        try:
            factors = []
            
            # Work-life balance alignment
            factors.append(job.work_life_balance_score / 100)
            
            # Remote work preference alignment
            if criteria.remote_ok and job.remote_friendly:
                factors.append(0.9)
            elif not criteria.remote_ok and not job.remote_friendly:
                factors.append(0.8)
            else:
                factors.append(0.6)
            
            # Company culture score
            factors.append(job.culture_score / 100)
            
            return sum(factors) / len(factors)
            
        except Exception as e:
            logger.error(f"Error calculating culture fit: {str(e)}")
            return 0.5
    
    def _calculate_advancement_potential(self, job: JobOpportunity) -> float:
        """Calculate career advancement potential"""
        try:
            factors = []
            
            # Growth score from job
            factors.append(job.growth_score / 100)
            
            # Career advancement score
            factors.append(job.career_advancement_score / 100)
            
            # Title advancement potential
            title_keywords = ["senior", "lead", "principal", "director", "manager", "head", "chief"]
            title_advancement = any(keyword in job.title.lower() for keyword in title_keywords)
            factors.append(0.8 if title_advancement else 0.5)
            
            # Equity/ownership potential
            factors.append(0.9 if job.equity_offered else 0.6)
            
            return sum(factors) / len(factors)
            
        except Exception as e:
            logger.error(f"Error calculating advancement potential: {str(e)}")
            return 0.5
    
    async def _store_tiered_recommendations(
        self, 
        recommendations: Dict[JobTier, List[TieredJobRecommendation]]
    ):
        """Store tiered recommendations in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for tier, tier_recommendations in recommendations.items():
                for rec in tier_recommendations:
                    recommendation_id = f"{rec.job.job_id}_{tier.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO tiered_recommendations (
                            recommendation_id, job_id, tier, success_probability,
                            salary_increase_potential, skills_gap_analysis,
                            application_strategy, preparation_roadmap,
                            diversity_analysis, company_culture_fit,
                            career_advancement_potential
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        recommendation_id,
                        rec.job.job_id,
                        tier.value,
                        rec.success_probability,
                        rec.salary_increase_potential,
                        json.dumps([asdict(sg) for sg in rec.skills_gap_analysis]),
                        json.dumps(asdict(rec.application_strategy)),
                        json.dumps(asdict(rec.preparation_roadmap)),
                        json.dumps(rec.diversity_analysis),
                        rec.company_culture_fit,
                        rec.career_advancement_potential
                    ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing tiered recommendations: {str(e)}")
    
    def get_tier_summary(self, recommendations: Dict[JobTier, List[TieredJobRecommendation]]) -> Dict[str, Any]:
        """
        Generate summary statistics for each tier
        
        Args:
            recommendations: Tiered job recommendations
            
        Returns:
            Summary statistics by tier
        """
        try:
            summary = {}
            
            for tier, tier_recommendations in recommendations.items():
                if not tier_recommendations:
                    summary[tier.value] = {
                        "count": 0,
                        "avg_salary_increase": 0,
                        "avg_success_probability": 0,
                        "avg_preparation_time": "N/A",
                        "industries": [],
                        "company_sizes": []
                    }
                    continue
                
                # Calculate averages
                avg_salary_increase = sum(r.salary_increase_potential for r in tier_recommendations) / len(tier_recommendations)
                avg_success_probability = sum(r.success_probability for r in tier_recommendations) / len(tier_recommendations)
                
                # Extract preparation times
                prep_times = [r.preparation_roadmap.total_preparation_time for r in tier_recommendations]
                avg_prep_time = max(set(prep_times), key=prep_times.count) if prep_times else "N/A"
                
                # Extract industries and company sizes
                industries = list(set(r.job.company_industry for r in tier_recommendations if r.job.company_industry))
                company_sizes = list(set(r.job.company_size for r in tier_recommendations if r.job.company_size))
                
                summary[tier.value] = {
                    "count": len(tier_recommendations),
                    "avg_salary_increase": round(avg_salary_increase * 100, 1),
                    "avg_success_probability": round(avg_success_probability * 100, 1),
                    "avg_preparation_time": avg_prep_time,
                    "industries": industries,
                    "company_sizes": company_sizes,
                    "description": self.tier_specs[tier]["description"]
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating tier summary: {str(e)}")
            return {}
