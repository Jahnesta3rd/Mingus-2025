#!/usr/bin/env python3
"""
Income-Focused Job Matching System for Mingus
Prioritizes salary improvement opportunities for African American professionals

This module provides comprehensive job matching functionality that focuses on:
- Salary increase potential (15-45% improvements)
- Top 10 metro areas with high opportunity
- Multi-dimensional job scoring
- Field-specific search strategies
- Company quality assessment
- Remote opportunity detection
"""

import json
import logging
import requests
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobBoard(Enum):
    """Supported job boards"""
    INDEED = "indeed"
    LINKEDIN = "linkedin"
    GLASSDOOR = "glassdoor"
    ZIPRECRUITER = "ziprecruiter"
    MONSTER = "monster"
    CAREERBUILDER = "careerbuilder"

class CareerField(Enum):
    """Career field categories"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    MARKETING = "marketing"
    SALES = "sales"
    CONSULTING = "consulting"
    ENGINEERING = "engineering"
    DATA_SCIENCE = "data_science"
    PRODUCT_MANAGEMENT = "product_management"
    HUMAN_RESOURCES = "human_resources"
    OPERATIONS = "operations"
    LEGAL = "legal"
    MEDIA = "media"
    NONPROFIT = "nonprofit"

class ExperienceLevel(Enum):
    """Experience level categories"""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    EXECUTIVE = "executive"

@dataclass
class JobOpportunity:
    """Represents a job opportunity with comprehensive scoring"""
    job_id: str
    title: str
    company: str
    location: str
    msa: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_median: Optional[int]
    salary_increase_potential: float
    remote_friendly: bool
    job_board: JobBoard
    url: str
    description: str
    requirements: List[str]
    benefits: List[str]
    diversity_score: float
    growth_score: float
    culture_score: float
    overall_score: float
    field: CareerField
    experience_level: ExperienceLevel
    posted_date: datetime
    application_deadline: Optional[datetime]
    company_size: Optional[str]
    company_industry: Optional[str]
    equity_offered: bool
    bonus_potential: Optional[int]
    career_advancement_score: float
    work_life_balance_score: float

@dataclass
class CompanyProfile:
    """Company profile with diversity and growth metrics"""
    company_id: str
    name: str
    industry: str
    size: str
    diversity_score: float
    growth_score: float
    culture_score: float
    benefits_score: float
    leadership_diversity: float
    employee_retention: float
    glassdoor_rating: Optional[float]
    indeed_rating: Optional[float]
    remote_friendly: bool
    headquarters: str
    founded_year: Optional[int]
    funding_stage: Optional[str]
    revenue: Optional[str]

@dataclass
class SearchCriteria:
    """Job search criteria"""
    current_salary: int
    target_salary_increase: float  # 0.15 to 0.45 (15% to 45%)
    career_field: CareerField
    experience_level: ExperienceLevel
    preferred_msas: List[str]
    remote_ok: bool
    max_commute_time: Optional[int]  # minutes
    must_have_benefits: List[str]
    company_size_preference: Optional[str]
    industry_preference: Optional[str]
    equity_required: bool
    min_company_rating: float = 3.0

class IncomeBoostJobMatcher:
    """
    Main class for income-focused job matching system
    Prioritizes salary improvement opportunities for African American professionals
    """
    
    def __init__(self, db_path: str = "backend/job_matching.db"):
        self.db_path = db_path
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Top 10 metro areas for African American professionals
        self.target_msas = [
            "Atlanta-Sandy Springs-Alpharetta, GA",
            "Houston-The Woodlands-Sugar Land, TX", 
            "Washington-Arlington-Alexandria, DC-VA-MD-WV",
            "Dallas-Fort Worth-Arlington, TX",
            "New York-Newark-Jersey City, NY-NJ-PA",
            "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD",
            "Chicago-Naperville-Elgin, IL-IN-WI",
            "Charlotte-Concord-Gastonia, NC-SC",
            "Miami-Fort Lauderdale-Pompano Beach, FL",
            "Baltimore-Columbia-Towson, MD"
        ]
        
        # MSA-specific salary multipliers
        self.msa_salary_multipliers = {
            "New York-Newark-Jersey City, NY-NJ-PA": 1.4,
            "San Francisco-Oakland-Berkeley, CA": 1.5,
            "Washington-Arlington-Alexandria, DC-VA-MD-WV": 1.3,
            "Boston-Cambridge-Newton, MA-NH": 1.25,
            "Seattle-Tacoma-Bellevue, WA": 1.2,
            "Atlanta-Sandy Springs-Alpharetta, GA": 1.1,
            "Houston-The Woodlands-Sugar Land, TX": 1.05,
            "Dallas-Fort Worth-Arlington, TX": 1.05,
            "Chicago-Naperville-Elgin, IL-IN-WI": 1.1,
            "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD": 1.1,
            "Charlotte-Concord-Gastonia, NC-SC": 1.0,
            "Miami-Fort Lauderdale-Pompano Beach, FL": 1.0,
            "Baltimore-Columbia-Towson, MD": 1.05
        }
        
        # Field-specific salary data
        self.field_salary_data = {
            CareerField.TECHNOLOGY: {
                "entry": 65000, "mid": 95000, "senior": 140000, "executive": 200000
            },
            CareerField.FINANCE: {
                "entry": 55000, "mid": 85000, "senior": 130000, "executive": 180000
            },
            CareerField.HEALTHCARE: {
                "entry": 50000, "mid": 75000, "senior": 110000, "executive": 160000
            },
            CareerField.EDUCATION: {
                "entry": 40000, "mid": 55000, "senior": 75000, "executive": 100000
            },
            CareerField.MARKETING: {
                "entry": 45000, "mid": 70000, "senior": 100000, "executive": 150000
            },
            CareerField.SALES: {
                "entry": 40000, "mid": 80000, "senior": 120000, "executive": 200000
            },
            CareerField.CONSULTING: {
                "entry": 60000, "mid": 90000, "senior": 140000, "executive": 220000
            },
            CareerField.ENGINEERING: {
                "entry": 70000, "mid": 100000, "senior": 150000, "executive": 220000
            },
            CareerField.DATA_SCIENCE: {
                "entry": 75000, "mid": 110000, "senior": 160000, "executive": 240000
            },
            CareerField.PRODUCT_MANAGEMENT: {
                "entry": 80000, "mid": 120000, "senior": 170000, "executive": 250000
            }
        }
        
        self._init_database()
    
    def _init_database(self):
        """Initialize the job matching database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_opportunities (
                job_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                msa TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                salary_median INTEGER,
                salary_increase_potential REAL,
                remote_friendly BOOLEAN,
                job_board TEXT,
                url TEXT,
                description TEXT,
                requirements TEXT,
                benefits TEXT,
                diversity_score REAL,
                growth_score REAL,
                culture_score REAL,
                overall_score REAL,
                field TEXT,
                experience_level TEXT,
                posted_date TIMESTAMP,
                application_deadline TIMESTAMP,
                company_size TEXT,
                company_industry TEXT,
                equity_offered BOOLEAN,
                bonus_potential INTEGER,
                career_advancement_score REAL,
                work_life_balance_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create companies table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_profiles (
                company_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                industry TEXT,
                size TEXT,
                diversity_score REAL,
                growth_score REAL,
                culture_score REAL,
                benefits_score REAL,
                leadership_diversity REAL,
                employee_retention REAL,
                glassdoor_rating REAL,
                indeed_rating REAL,
                remote_friendly BOOLEAN,
                headquarters TEXT,
                founded_year INTEGER,
                funding_stage TEXT,
                revenue TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                search_id TEXT PRIMARY KEY,
                user_email TEXT,
                search_criteria TEXT,
                results_count INTEGER,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def salary_focused_search(self, criteria: SearchCriteria) -> List[JobOpportunity]:
        """
        Filter jobs by income improvement potential
        Focus on jobs offering 15-45% salary increases
        """
        logger.info(f"Starting salary-focused search for {criteria.career_field.value}")
        
        # Calculate target salary range
        target_salary_min = int(criteria.current_salary * (1 + criteria.target_salary_increase))
        target_salary_max = int(criteria.current_salary * (1.45))  # Max 45% increase
        
        # Get field-specific salary expectations
        field_salaries = self.field_salary_data.get(criteria.career_field, {})
        experience_key = criteria.experience_level.value
        
        # Search across multiple job boards
        all_jobs = []
        
        # Search Indeed
        indeed_jobs = await self._search_indeed(criteria, target_salary_min, target_salary_max)
        all_jobs.extend(indeed_jobs)
        
        # Search LinkedIn
        linkedin_jobs = await self._search_linkedin(criteria, target_salary_min, target_salary_max)
        all_jobs.extend(linkedin_jobs)
        
        # Search Glassdoor
        glassdoor_jobs = await self._search_glassdoor(criteria, target_salary_min, target_salary_max)
        all_jobs.extend(glassdoor_jobs)
        
        # Filter and score jobs
        filtered_jobs = []
        for job in all_jobs:
            if self._meets_salary_criteria(job, criteria, target_salary_min, target_salary_max):
                scored_job = self.multi_dimensional_scoring(job, criteria)
                if scored_job.overall_score >= 70:  # Minimum score threshold
                    filtered_jobs.append(scored_job)
        
        # Sort by overall score and salary increase potential
        filtered_jobs.sort(key=lambda x: (x.overall_score, x.salary_increase_potential), reverse=True)
        
        # Store search results
        await self._store_search_results(criteria, filtered_jobs)
        
        logger.info(f"Found {len(filtered_jobs)} salary-focused opportunities")
        return filtered_jobs[:50]  # Return top 50 results
    
    def multi_dimensional_scoring(self, job: JobOpportunity, criteria: SearchCriteria) -> JobOpportunity:
        """
        Score jobs on multiple dimensions with specified weights:
        - Salary increase potential (40% weight)
        - Career advancement opportunities (25% weight) 
        - Company diversity metrics (20% weight)
        - Benefits and work-life balance (15% weight)
        """
        # Calculate salary increase potential score (0-100)
        salary_score = self._calculate_salary_score(job, criteria)
        
        # Calculate career advancement score (0-100)
        advancement_score = self._calculate_advancement_score(job, criteria)
        
        # Calculate diversity score (0-100)
        diversity_score = self._calculate_diversity_score(job)
        
        # Calculate benefits/work-life balance score (0-100)
        benefits_score = self._calculate_benefits_score(job, criteria)
        
        # Apply weights
        overall_score = (
            salary_score * 0.40 +
            advancement_score * 0.25 +
            diversity_score * 0.20 +
            benefits_score * 0.15
        )
        
        # Update job with scores
        job.salary_increase_potential = self._calculate_salary_increase_potential(job, criteria)
        job.diversity_score = diversity_score
        job.growth_score = advancement_score
        job.culture_score = benefits_score
        job.overall_score = overall_score
        job.career_advancement_score = advancement_score
        job.work_life_balance_score = benefits_score
        
        return job
    
    def field_specific_strategies(self, field: CareerField) -> Dict[str, Any]:
        """
        Customize search strategies by career field
        Returns field-specific search parameters and keywords
        """
        strategies = {
            CareerField.TECHNOLOGY: {
                "keywords": ["software engineer", "developer", "programmer", "architect", "devops"],
                "salary_keywords": ["competitive salary", "equity", "stock options", "bonus"],
                "growth_keywords": ["senior", "lead", "principal", "staff", "director"],
                "benefits_keywords": ["unlimited PTO", "flexible hours", "remote work", "learning budget"],
                "companies": ["Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Uber", "Airbnb"]
            },
            CareerField.FINANCE: {
                "keywords": ["financial analyst", "investment banker", "portfolio manager", "risk analyst"],
                "salary_keywords": ["bonus", "commission", "profit sharing", "performance bonus"],
                "growth_keywords": ["VP", "director", "managing director", "partner"],
                "benefits_keywords": ["401k match", "health insurance", "bonus structure", "pension"],
                "companies": ["Goldman Sachs", "JPMorgan", "Morgan Stanley", "BlackRock", "Vanguard"]
            },
            CareerField.HEALTHCARE: {
                "keywords": ["nurse", "physician", "pharmacist", "therapist", "technician"],
                "salary_keywords": ["shift differential", "overtime", "call pay", "holiday pay"],
                "growth_keywords": ["charge nurse", "supervisor", "manager", "director"],
                "benefits_keywords": ["health insurance", "retirement", "tuition reimbursement", "CEU"],
                "companies": ["Mayo Clinic", "Cleveland Clinic", "Johns Hopkins", "Kaiser Permanente"]
            },
            CareerField.EDUCATION: {
                "keywords": ["teacher", "professor", "administrator", "counselor", "librarian"],
                "salary_keywords": ["step increase", "lane change", "summer pay", "stipend"],
                "growth_keywords": ["department head", "principal", "superintendent", "dean"],
                "benefits_keywords": ["summer break", "pension", "health insurance", "sabbatical"],
                "companies": ["Harvard", "Stanford", "MIT", "Princeton", "Yale"]
            },
            CareerField.MARKETING: {
                "keywords": ["marketing manager", "brand manager", "digital marketing", "content creator"],
                "salary_keywords": ["performance bonus", "commission", "equity", "profit sharing"],
                "growth_keywords": ["senior manager", "director", "VP marketing", "CMO"],
                "benefits_keywords": ["creative freedom", "budget authority", "team building", "conferences"],
                "companies": ["Nike", "Coca-Cola", "PepsiCo", "Procter & Gamble", "Unilever"]
            }
        }
        
        return strategies.get(field, strategies[CareerField.TECHNOLOGY])
    
    def company_quality_assessment(self, company_name: str) -> CompanyProfile:
        """
        Evaluate employers for diversity and growth metrics
        Integrates with multiple data sources
        """
        # Check if company exists in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM company_profiles WHERE name = ?
        ''', (company_name,))
        
        existing_profile = cursor.fetchone()
        if existing_profile:
            conn.close()
            return self._row_to_company_profile(existing_profile)
        
        # Create new company profile
        profile = CompanyProfile(
            company_id=f"comp_{hash(company_name) % 1000000}",
            name=company_name,
            industry="Unknown",
            size="Unknown",
            diversity_score=0.0,
            growth_score=0.0,
            culture_score=0.0,
            benefits_score=0.0,
            leadership_diversity=0.0,
            employee_retention=0.0,
            glassdoor_rating=None,
            indeed_rating=None,
            remote_friendly=False,
            headquarters="Unknown",
            founded_year=None,
            funding_stage=None,
            revenue=None
        )
        
        # Gather data from multiple sources
        try:
            # Glassdoor data
            glassdoor_data = self._get_glassdoor_data(company_name)
            if glassdoor_data:
                profile.glassdoor_rating = glassdoor_data.get('rating')
                profile.culture_score = glassdoor_data.get('culture_score', 0.0)
                profile.benefits_score = glassdoor_data.get('benefits_score', 0.0)
            
            # Indeed data
            indeed_data = self._get_indeed_company_data(company_name)
            if indeed_data:
                profile.indeed_rating = indeed_data.get('rating')
                profile.employee_retention = indeed_data.get('retention_rate', 0.0)
            
            # Diversity data
            diversity_data = self._get_diversity_data(company_name)
            if diversity_data:
                profile.diversity_score = diversity_data.get('diversity_score', 0.0)
                profile.leadership_diversity = diversity_data.get('leadership_diversity', 0.0)
            
            # Growth data
            growth_data = self._get_growth_data(company_name)
            if growth_data:
                profile.growth_score = growth_data.get('growth_score', 0.0)
                profile.industry = growth_data.get('industry', 'Unknown')
                profile.size = growth_data.get('size', 'Unknown')
                profile.headquarters = growth_data.get('headquarters', 'Unknown')
                profile.founded_year = growth_data.get('founded_year')
                profile.funding_stage = growth_data.get('funding_stage')
                profile.revenue = growth_data.get('revenue')
            
        except Exception as e:
            logger.error(f"Error gathering company data for {company_name}: {e}")
        
        # Store in database
        self._store_company_profile(profile)
        conn.close()
        
        return profile
    
    def msa_targeting(self, jobs: List[JobOpportunity], preferred_msas: List[str]) -> List[JobOpportunity]:
        """
        Focus on high-opportunity metro areas
        Prioritizes jobs in target MSAs
        """
        if not preferred_msas:
            preferred_msas = self.target_msas
        
        # Score jobs based on MSA preference
        for job in jobs:
            if job.msa in preferred_msas:
                # Boost score for preferred MSAs
                job.overall_score += 10
            elif job.msa in self.target_msas:
                # Moderate boost for other target MSAs
                job.overall_score += 5
        
        # Sort by MSA preference and overall score
        jobs.sort(key=lambda x: (
            x.msa not in preferred_msas,  # Preferred MSAs first
            x.msa not in self.target_msas,  # Other target MSAs second
            -x.overall_score  # Then by score
        ))
        
        return jobs
    
    def remote_opportunity_detection(self, jobs: List[JobOpportunity]) -> List[JobOpportunity]:
        """
        Identify remote-friendly positions
        Scores jobs based on remote work potential
        """
        remote_keywords = [
            "remote", "work from home", "virtual", "distributed", "flexible location",
            "telecommute", "hybrid", "anywhere", "location independent"
        ]
        
        for job in jobs:
            remote_score = 0
            
            # Check job title
            if any(keyword in job.title.lower() for keyword in remote_keywords):
                remote_score += 30
            
            # Check description
            if any(keyword in job.description.lower() for keyword in remote_keywords):
                remote_score += 40
            
            # Check benefits
            if any(keyword in " ".join(job.benefits).lower() for keyword in remote_keywords):
                remote_score += 20
            
            # Check company profile
            if hasattr(job, 'company_profile') and job.company_profile:
                if job.company_profile.remote_friendly:
                    remote_score += 10
            
            # Set remote friendly flag
            job.remote_friendly = remote_score >= 30
            
            # Boost score for remote opportunities
            if job.remote_friendly:
                job.overall_score += 5
        
        return jobs
    
    # Helper methods
    def _calculate_salary_score(self, job: JobOpportunity, criteria: SearchCriteria) -> float:
        """Calculate salary-based score (0-100)"""
        if not job.salary_median:
            return 50  # Neutral score if no salary data
        
        target_salary = criteria.current_salary * (1 + criteria.target_salary_increase)
        increase_ratio = job.salary_median / criteria.current_salary
        
        if increase_ratio >= 1.45:  # 45%+ increase
            return 100
        elif increase_ratio >= 1.30:  # 30-45% increase
            return 90
        elif increase_ratio >= 1.15:  # 15-30% increase
            return 80
        elif increase_ratio >= 1.05:  # 5-15% increase
            return 60
        else:
            return 30
    
    def _calculate_advancement_score(self, job: JobOpportunity, criteria: SearchCriteria) -> float:
        """Calculate career advancement score (0-100)"""
        score = 50  # Base score
        
        # Check for advancement keywords in title
        advancement_keywords = ["senior", "lead", "principal", "staff", "director", "manager", "head"]
        if any(keyword in job.title.lower() for keyword in advancement_keywords):
            score += 20
        
        # Check for growth opportunities in description
        growth_keywords = ["growth", "advancement", "leadership", "mentoring", "development"]
        if any(keyword in job.description.lower() for keyword in growth_keywords):
            score += 15
        
        # Check for equity/stock options
        if job.equity_offered:
            score += 15
        
        # Check for bonus potential
        if job.bonus_potential and job.bonus_potential > 0:
            score += 10
        
        return min(100, score)
    
    def _calculate_diversity_score(self, job: JobOpportunity) -> float:
        """Calculate diversity score (0-100)"""
        # This would integrate with diversity data APIs
        # For now, return a placeholder score
        return 75.0
    
    def _calculate_benefits_score(self, job: JobOpportunity, criteria: SearchCriteria) -> float:
        """Calculate benefits and work-life balance score (0-100)"""
        score = 50  # Base score
        
        # Check for key benefits
        key_benefits = ["health insurance", "401k", "dental", "vision", "PTO", "vacation"]
        benefits_found = sum(1 for benefit in key_benefits if benefit in " ".join(job.benefits).lower())
        score += benefits_found * 5
        
        # Check for work-life balance keywords
        wlb_keywords = ["flexible", "work-life balance", "unlimited PTO", "remote", "hybrid"]
        if any(keyword in job.description.lower() for keyword in wlb_keywords):
            score += 15
        
        # Check for remote work
        if job.remote_friendly:
            score += 10
        
        return min(100, score)
    
    def _calculate_salary_increase_potential(self, job: JobOpportunity, criteria: SearchCriteria) -> float:
        """Calculate salary increase potential as a percentage"""
        if not job.salary_median:
            return 0.0
        
        return (job.salary_median - criteria.current_salary) / criteria.current_salary
    
    def _meets_salary_criteria(self, job: JobOpportunity, criteria: SearchCriteria, 
                              min_salary: int, max_salary: int) -> bool:
        """Check if job meets salary criteria"""
        if not job.salary_median:
            return True  # Include if no salary data
        
        return min_salary <= job.salary_median <= max_salary
    
    async def _search_indeed(self, criteria: SearchCriteria, min_salary: int, max_salary: int) -> List[JobOpportunity]:
        """Search Indeed for jobs"""
        # This would integrate with Indeed API
        # For now, return mock data
        return []
    
    async def _search_linkedin(self, criteria: SearchCriteria, min_salary: int, max_salary: int) -> List[JobOpportunity]:
        """Search LinkedIn for jobs"""
        # This would integrate with LinkedIn API
        # For now, return mock data
        return []
    
    async def _search_glassdoor(self, criteria: SearchCriteria, min_salary: int, max_salary: int) -> List[JobOpportunity]:
        """Search Glassdoor for jobs"""
        # This would integrate with Glassdoor API
        # For now, return mock data
        return []
    
    def _get_glassdoor_data(self, company_name: str) -> Optional[Dict]:
        """Get company data from Glassdoor"""
        # This would integrate with Glassdoor API
        return None
    
    def _get_indeed_company_data(self, company_name: str) -> Optional[Dict]:
        """Get company data from Indeed"""
        # This would integrate with Indeed API
        return None
    
    def _get_diversity_data(self, company_name: str) -> Optional[Dict]:
        """Get diversity data from various sources"""
        # This would integrate with diversity data APIs
        return None
    
    def _get_growth_data(self, company_name: str) -> Optional[Dict]:
        """Get company growth data"""
        # This would integrate with company data APIs
        return None
    
    def _store_company_profile(self, profile: CompanyProfile):
        """Store company profile in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO company_profiles 
            (company_id, name, industry, size, diversity_score, growth_score, culture_score,
             benefits_score, leadership_diversity, employee_retention, glassdoor_rating,
             indeed_rating, remote_friendly, headquarters, founded_year, funding_stage, revenue)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            profile.company_id, profile.name, profile.industry, profile.size,
            profile.diversity_score, profile.growth_score, profile.culture_score,
            profile.benefits_score, profile.leadership_diversity, profile.employee_retention,
            profile.glassdoor_rating, profile.indeed_rating, profile.remote_friendly,
            profile.headquarters, profile.founded_year, profile.funding_stage, profile.revenue
        ))
        
        conn.commit()
        conn.close()
    
    def _store_search_results(self, criteria: SearchCriteria, jobs: List[JobOpportunity]):
        """Store search results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for job in jobs:
            cursor.execute('''
                INSERT OR REPLACE INTO job_opportunities 
                (job_id, title, company, location, msa, salary_min, salary_max, salary_median,
                 salary_increase_potential, remote_friendly, job_board, url, description,
                 requirements, benefits, diversity_score, growth_score, culture_score,
                 overall_score, field, experience_level, posted_date, application_deadline,
                 company_size, company_industry, equity_offered, bonus_potential,
                 career_advancement_score, work_life_balance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.job_id, job.title, job.company, job.location, job.msa,
                job.salary_min, job.salary_max, job.salary_median, job.salary_increase_potential,
                job.remote_friendly, job.job_board.value, job.url, job.description,
                json.dumps(job.requirements), json.dumps(job.benefits),
                job.diversity_score, job.growth_score, job.culture_score, job.overall_score,
                job.field.value, job.experience_level.value, job.posted_date, job.application_deadline,
                job.company_size, job.company_industry, job.equity_offered, job.bonus_potential,
                job.career_advancement_score, job.work_life_balance_score
            ))
        
        conn.commit()
        conn.close()
    
    def _row_to_company_profile(self, row) -> CompanyProfile:
        """Convert database row to CompanyProfile object"""
        return CompanyProfile(
            company_id=row[0],
            name=row[1],
            industry=row[2],
            size=row[3],
            diversity_score=row[4],
            growth_score=row[5],
            culture_score=row[6],
            benefits_score=row[7],
            leadership_diversity=row[8],
            employee_retention=row[9],
            glassdoor_rating=row[10],
            indeed_rating=row[11],
            remote_friendly=bool(row[12]),
            headquarters=row[13],
            founded_year=row[14],
            funding_stage=row[15],
            revenue=row[16]
        )
    
    async def _store_search_results(self, criteria: SearchCriteria, jobs: List[JobOpportunity]):
        """Store search results in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_id = f"search_{hash(str(criteria)) % 1000000}"
        
        # Store search criteria
        cursor.execute('''
            INSERT INTO search_history (search_id, search_criteria, results_count)
            VALUES (?, ?, ?)
        ''', (search_id, json.dumps(asdict(criteria)), len(jobs)))
        
        # Store job opportunities
        for job in jobs:
            cursor.execute('''
                INSERT OR REPLACE INTO job_opportunities 
                (job_id, title, company, location, msa, salary_min, salary_max, salary_median,
                 salary_increase_potential, remote_friendly, job_board, url, description,
                 requirements, benefits, diversity_score, growth_score, culture_score,
                 overall_score, field, experience_level, posted_date, application_deadline,
                 company_size, company_industry, equity_offered, bonus_potential,
                 career_advancement_score, work_life_balance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.job_id, job.title, job.company, job.location, job.msa,
                job.salary_min, job.salary_max, job.salary_median, job.salary_increase_potential,
                job.remote_friendly, job.job_board.value, job.url, job.description,
                json.dumps(job.requirements), json.dumps(job.benefits),
                job.diversity_score, job.growth_score, job.culture_score, job.overall_score,
                job.field.value, job.experience_level.value, job.posted_date, job.application_deadline,
                job.company_size, job.company_industry, job.equity_offered, job.bonus_potential,
                job.career_advancement_score, job.work_life_balance_score
            ))
        
        conn.commit()
        conn.close()

# Example usage and testing
async def main():
    """Example usage of the IncomeBoostJobMatcher"""
    matcher = IncomeBoostJobMatcher()
    
    # Create search criteria
    criteria = SearchCriteria(
        current_salary=75000,
        target_salary_increase=0.25,  # 25% increase
        career_field=CareerField.TECHNOLOGY,
        experience_level=ExperienceLevel.MID,
        preferred_msas=["Atlanta-Sandy Springs-Alpharetta, GA", "Houston-The Woodlands-Sugar Land, TX"],
        remote_ok=True,
        max_commute_time=30,
        must_have_benefits=["health insurance", "401k"],
        company_size_preference="mid",
        industry_preference="technology",
        equity_required=False
    )
    
    # Perform salary-focused search
    jobs = await matcher.salary_focused_search(criteria)
    
    print(f"Found {len(jobs)} job opportunities")
    for job in jobs[:5]:  # Show top 5
        print(f"{job.title} at {job.company} - ${job.salary_median:,} ({job.salary_increase_potential:.1%} increase)")

if __name__ == "__main__":
    asyncio.run(main())
