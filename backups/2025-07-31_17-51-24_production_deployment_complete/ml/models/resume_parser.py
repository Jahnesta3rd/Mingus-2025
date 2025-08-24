"""
Advanced Resume Parser with Field Expertise Analysis
Extends resume analysis to identify field expertise, experience level, and career trajectory
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import Counter, defaultdict
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class FieldType(str, Enum):
    """Primary fields of expertise"""
    DATA_ANALYSIS = "Data Analysis"
    PROJECT_MANAGEMENT = "Project Management"
    SOFTWARE_DEVELOPMENT = "Software Development"
    MARKETING = "Marketing"
    FINANCE = "Finance"
    SALES = "Sales"
    OPERATIONS = "Operations"
    HR = "HR"

class ExperienceLevel(str, Enum):
    """Experience level classifications"""
    ENTRY = "Entry"
    MID = "Mid"
    SENIOR = "Senior"

class SkillCategory(str, Enum):
    """Skill categories"""
    TECHNICAL = "Technical"
    BUSINESS = "Business"
    SOFT = "Soft"

@dataclass
class FieldAnalysis:
    """Field expertise analysis results"""
    primary_field: FieldType
    secondary_field: Optional[FieldType]
    confidence_score: float
    field_keywords: List[str]
    field_experience_years: float

@dataclass
class ExperienceAnalysis:
    """Experience level analysis results"""
    level: ExperienceLevel
    confidence_score: float
    total_years: float
    progression_indicator: str
    leadership_indicators: List[str]

@dataclass
class SkillsAnalysis:
    """Skills analysis results"""
    technical_skills: Dict[str, float]
    business_skills: Dict[str, float]
    soft_skills: Dict[str, float]
    technical_business_ratio: float
    proficiency_levels: Dict[str, str]

@dataclass
class IncomeAnalysis:
    """Income analysis results"""
    estimated_salary: int
    percentile: float
    market_position: str
    salary_range: Dict[str, int]
    compensation_breakdown: Dict[str, float]

@dataclass
class CareerTrajectory:
    """Career trajectory analysis"""
    current_position: str
    career_progression: List[str]
    next_logical_steps: List[str]
    growth_potential: float
    advancement_readiness: float
    industry_focus: List[str]

@dataclass
class ResumeAnalysis:
    """Complete resume analysis results"""
    field_analysis: FieldAnalysis
    experience_analysis: ExperienceAnalysis
    skills_analysis: SkillsAnalysis
    career_trajectory: CareerTrajectory
    income_analysis: IncomeAnalysis
    leadership_potential: float
    transferable_skills: List[str]
    industry_experience: List[str]

class AdvancedResumeParser:
    """
    Advanced resume parser with field expertise analysis and career trajectory detection
    """
    
    def __init__(self):
        """Initialize the advanced resume parser"""
        self.field_keywords = self._initialize_field_keywords()
        self.experience_indicators = self._initialize_experience_indicators()
        self.leadership_indicators = self._initialize_leadership_indicators()
        self.skill_categories = self._initialize_skill_categories()
        
        # Initialize NLP components
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Initialize TF-IDF vectorizer for keyword analysis
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Analysis weights
        self.weights = {
            'job_title': 0.4,
            'responsibilities': 0.3,
            'skills': 0.2,
            'education': 0.1
        }
    
    def _initialize_field_keywords(self) -> Dict[FieldType, List[str]]:
        """Initialize field-specific keywords"""
        return {
            FieldType.DATA_ANALYSIS: [
                'sql', 'python', 'r', 'tableau', 'power bi', 'excel', 'analytics',
                'statistics', 'data mining', 'machine learning', 'reporting',
                'data visualization', 'etl', 'data warehouse', 'business intelligence',
                'predictive analytics', 'statistical analysis', 'data modeling'
            ],
            FieldType.PROJECT_MANAGEMENT: [
                'pmp', 'agile', 'scrum', 'kanban', 'waterfall', 'stakeholder management',
                'project planning', 'timeline management', 'risk management',
                'budget management', 'team leadership', 'project coordination',
                'sprint planning', 'backlog management', 'project delivery'
            ],
            FieldType.SOFTWARE_DEVELOPMENT: [
                'java', 'python', 'javascript', 'c++', 'c#', 'react', 'angular',
                'node.js', 'git', 'docker', 'kubernetes', 'aws', 'azure',
                'api development', 'microservices', 'devops', 'ci/cd',
                'database design', 'system architecture', 'code review'
            ],
            FieldType.MARKETING: [
                'campaigns', 'social media', 'seo', 'sem', 'google analytics',
                'content creation', 'email marketing', 'brand management',
                'digital marketing', 'market research', 'customer acquisition',
                'lead generation', 'conversion optimization', 'marketing automation'
            ],
            FieldType.FINANCE: [
                'financial modeling', 'accounting', 'budgeting', 'forecasting',
                'financial analysis', 'investment analysis', 'risk assessment',
                'financial planning', 'audit', 'tax', 'treasury', 'compliance',
                'financial reporting', 'cost analysis', 'valuation'
            ],
            FieldType.SALES: [
                'crm', 'salesforce', 'lead generation', 'client relations',
                'revenue growth', 'sales pipeline', 'account management',
                'business development', 'negotiation', 'sales strategy',
                'customer success', 'sales training', 'territory management'
            ],
            FieldType.OPERATIONS: [
                'process improvement', 'supply chain', 'logistics', 'quality control',
                'operations management', 'efficiency optimization', 'vendor management',
                'inventory management', 'production planning', 'six sigma',
                'lean methodology', 'operational excellence'
            ],
            FieldType.HR: [
                'recruitment', 'talent acquisition', 'employee relations',
                'performance management', 'training and development', 'compensation',
                'benefits administration', 'hr policies', 'workplace culture',
                'diversity and inclusion', 'hr analytics', 'employee engagement'
            ]
        }
    
    def _initialize_experience_indicators(self) -> Dict[ExperienceLevel, List[str]]:
        """Initialize experience level indicators"""
        return {
            ExperienceLevel.ENTRY: [
                'intern', 'internship', 'junior', 'assistant', 'associate',
                'coordinator', 'trainee', 'entry level', 'graduate', 'student'
            ],
            ExperienceLevel.MID: [
                'analyst', 'specialist', 'senior', 'lead', 'consultant',
                'coordinator', 'representative', 'technician', 'developer'
            ],
            ExperienceLevel.SENIOR: [
                'manager', 'director', 'principal', 'head', 'chief',
                'vp', 'vice president', 'executive', 'senior manager',
                'team lead', 'supervisor', 'architect'
            ]
        }
    
    def _initialize_leadership_indicators(self) -> List[str]:
        """Initialize leadership indicators"""
        return [
            'led', 'managed', 'supervised', 'directed', 'oversaw', 'coordinated',
            'mentored', 'trained', 'guided', 'facilitated', 'orchestrated',
            'spearheaded', 'championed', 'drove', 'established', 'developed',
            'team leadership', 'project leadership', 'department leadership'
        ]
    
    def _initialize_skill_categories(self) -> Dict[SkillCategory, List[str]]:
        """Initialize skill categories"""
        return {
            SkillCategory.TECHNICAL: [
                'programming', 'coding', 'software', 'database', 'api',
                'cloud', 'devops', 'automation', 'algorithm', 'data structure',
                'framework', 'library', 'tool', 'platform', 'system'
            ],
            SkillCategory.BUSINESS: [
                'strategy', 'planning', 'analysis', 'management', 'operations',
                'finance', 'marketing', 'sales', 'customer', 'business',
                'process', 'project', 'stakeholder', 'budget', 'forecast'
            ],
            SkillCategory.SOFT: [
                'communication', 'leadership', 'teamwork', 'problem solving',
                'critical thinking', 'adaptability', 'creativity', 'collaboration',
                'time management', 'organization', 'interpersonal', 'presentation'
            ]
        }
    
    def parse_resume(self, resume_text: str, resume_data: Dict[str, Any] = None) -> ResumeAnalysis:
        """
        Parse resume and perform comprehensive analysis
        
        Args:
            resume_text: Raw resume text
            resume_data: Structured resume data (optional)
            
        Returns:
            ResumeAnalysis object with comprehensive results
        """
        try:
            logger.info("Starting advanced resume analysis")
            
            # Preprocess resume text
            processed_text = self._preprocess_text(resume_text)
            
            # Perform field analysis
            field_analysis = self._analyze_field_expertise(processed_text, resume_data)
            
            # Perform experience analysis
            experience_analysis = self._analyze_experience_level(processed_text, resume_data)
            
            # Perform skills analysis
            skills_analysis = self._analyze_skills(processed_text, resume_data)
            
            # Perform career trajectory analysis
            career_trajectory = self._analyze_career_trajectory(processed_text, resume_data)
            
            # Calculate leadership potential
            leadership_potential = self._calculate_leadership_potential(processed_text)
            
            # Extract transferable skills
            transferable_skills = self._extract_transferable_skills(processed_text, field_analysis)
            
            # Extract industry experience
            industry_experience = self._extract_industry_experience(processed_text, resume_data)
            
            # Perform income analysis
            income_analysis = self._analyze_income(processed_text, experience_analysis, field_analysis, resume_data)
            
            # Create comprehensive analysis
            analysis = ResumeAnalysis(
                field_analysis=field_analysis,
                experience_analysis=experience_analysis,
                skills_analysis=skills_analysis,
                career_trajectory=career_trajectory,
                income_analysis=income_analysis,
                leadership_potential=leadership_potential,
                transferable_skills=transferable_skills,
                industry_experience=industry_experience
            )
            
            logger.info("Resume analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in resume analysis: {str(e)}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess resume text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\-\.\,\&\+\#]', ' ', text)
        
        return text.strip()
    
    def _analyze_field_expertise(self, text: str, resume_data: Dict[str, Any] = None) -> FieldAnalysis:
        """Analyze primary and secondary fields of expertise"""
        field_scores = {}
        
        for field, keywords in self.field_keywords.items():
            score = 0
            matched_keywords = []
            
            # Calculate keyword matches
            for keyword in keywords:
                if keyword in text:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Normalize score by number of keywords
            normalized_score = score / len(keywords) if keywords else 0
            field_scores[field] = {
                'score': normalized_score,
                'keywords': matched_keywords
            }
        
        # Find primary and secondary fields
        sorted_fields = sorted(field_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        primary_field = sorted_fields[0][0] if sorted_fields else FieldType.OPERATIONS
        secondary_field = sorted_fields[1][0] if len(sorted_fields) > 1 and sorted_fields[1][1]['score'] > 0.1 else None
        
        # Calculate confidence score
        primary_score = sorted_fields[0][1]['score'] if sorted_fields else 0
        confidence_score = min(primary_score * 2, 1.0)  # Scale to 0-1
        
        # Estimate field experience years
        field_experience_years = self._estimate_field_experience(text, primary_field, resume_data)
        
        return FieldAnalysis(
            primary_field=primary_field,
            secondary_field=secondary_field,
            confidence_score=confidence_score,
            field_keywords=sorted_fields[0][1]['keywords'] if sorted_fields else [],
            field_experience_years=field_experience_years
        )
    
    def _analyze_experience_level(self, text: str, resume_data: Dict[str, Any] = None) -> ExperienceAnalysis:
        """Analyze experience level and progression"""
        level_scores = {}
        
        for level, indicators in self.experience_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in text:
                    score += 1
            level_scores[level] = score
        
        # Determine experience level with more nuanced logic
        # Check if senior indicators are just part of other words (like "team leads" vs "team lead")
        senior_score = level_scores[ExperienceLevel.SENIOR]
        if 'team lead' in text and 'team leads' in text:
            # If both singular and plural exist, it's likely just part of a description
            senior_score = max(0, senior_score - 1)
        
        # Check for job title patterns that might be misleading
        # If we have both "senior" and "specialist" in the same context, it might be a mid-level role
        if 'senior' in text and 'specialist' in text and 'manager' not in text and 'director' not in text:
            # "Senior Specialist" is often a mid-level role, not truly senior
            senior_score = max(0, senior_score - 1)
        
        # If we have "senior" and "specialist" but no strong senior indicators, classify as mid
        if 'senior' in text and 'specialist' in text and level_scores[ExperienceLevel.MID] > 0:
            # This is likely a mid-level role with "senior" in the title
            if senior_score <= 1:  # Only one senior indicator
                senior_score = 0  # Don't classify as senior
        
        # Special case: "Senior Specialist" should be classified as MID level
        if 'senior' in text and 'specialist' in text and level_scores[ExperienceLevel.MID] > 0:
            level = ExperienceLevel.MID
            confidence = min(level_scores[ExperienceLevel.MID] / 2, 1.0)
        elif level_scores[ExperienceLevel.ENTRY] > 0 and senior_score == 0:
            # If we have entry-level indicators and no real senior indicators, classify as entry
            level = ExperienceLevel.ENTRY
            confidence = min(level_scores[ExperienceLevel.ENTRY] / 2, 1.0)
        elif senior_score > 0:
            level = ExperienceLevel.SENIOR
            confidence = min(senior_score / 3, 1.0)
        elif level_scores[ExperienceLevel.MID] > 0:
            level = ExperienceLevel.MID
            confidence = min(level_scores[ExperienceLevel.MID] / 2, 1.0)
        else:
            level = ExperienceLevel.ENTRY
            confidence = 0.8
        
        # Calculate total years of experience
        total_years = self._calculate_total_experience(text, resume_data)
        
        # Analyze progression
        progression_indicator = self._analyze_career_progression(text, resume_data)
        
        # Extract leadership indicators
        leadership_indicators = self._extract_leadership_indicators(text)
        
        return ExperienceAnalysis(
            level=level,
            confidence_score=confidence,
            total_years=total_years,
            progression_indicator=progression_indicator,
            leadership_indicators=leadership_indicators
        )
    
    def _analyze_skills(self, text: str, resume_data: Dict[str, Any] = None) -> SkillsAnalysis:
        """Analyze and categorize skills"""
        # Extract skills from text
        skills = self._extract_skills_from_text(text)
        
        # Categorize skills
        technical_skills = {}
        business_skills = {}
        soft_skills = {}
        
        for skill, frequency in skills.items():
            category = self._categorize_skill(skill)
            proficiency = self._calculate_skill_proficiency(skill, frequency, text)
            
            if category == SkillCategory.TECHNICAL:
                technical_skills[skill] = proficiency
            elif category == SkillCategory.BUSINESS:
                business_skills[skill] = proficiency
            else:
                soft_skills[skill] = proficiency
        
        # Calculate technical vs business ratio
        technical_total = sum(technical_skills.values()) if technical_skills else 0
        business_total = sum(business_skills.values()) if business_skills else 0
        total_skills = technical_total + business_total
        
        technical_business_ratio = technical_total / total_skills if total_skills > 0 else 0.5
        
        # Determine proficiency levels
        proficiency_levels = {}
        for skill, score in {**technical_skills, **business_skills, **soft_skills}.items():
            if score >= 0.8:
                proficiency_levels[skill] = "Expert"
            elif score >= 0.6:
                proficiency_levels[skill] = "Advanced"
            elif score >= 0.4:
                proficiency_levels[skill] = "Intermediate"
            else:
                proficiency_levels[skill] = "Beginner"
        
        return SkillsAnalysis(
            technical_skills=technical_skills,
            business_skills=business_skills,
            soft_skills=soft_skills,
            technical_business_ratio=technical_business_ratio,
            proficiency_levels=proficiency_levels
        )
    
    def _analyze_career_trajectory(self, text: str, resume_data: Dict[str, Any] = None) -> CareerTrajectory:
        """Analyze career trajectory and predict next steps"""
        # Extract job history
        job_history = self._extract_job_history(text, resume_data)
        
        # Determine current position
        current_position = job_history[0] if job_history else "Unknown"
        
        # Analyze career progression
        career_progression = self._analyze_progression_pattern(job_history)
        
        # Predict next logical steps
        next_steps = self._predict_next_career_steps(job_history, text)
        
        # Calculate growth potential
        growth_potential = self._calculate_growth_potential(job_history, text)
        
        # Calculate advancement readiness
        advancement_readiness = self._calculate_advancement_readiness(text, job_history)
        
        # Extract industry focus
        industry_focus = self._extract_industry_focus(text, job_history)
        
        return CareerTrajectory(
            current_position=current_position,
            career_progression=career_progression,
            next_logical_steps=next_steps,
            growth_potential=growth_potential,
            advancement_readiness=advancement_readiness,
            industry_focus=industry_focus
        )
    
    def _calculate_leadership_potential(self, text: str) -> float:
        """Calculate leadership potential score"""
        leadership_score = 0
        total_indicators = len(self.leadership_indicators)
        
        for indicator in self.leadership_indicators:
            if indicator in text:
                leadership_score += 1
        
        # Normalize to 0-1 scale
        return min(leadership_score / total_indicators, 1.0)
    
    def _extract_transferable_skills(self, text: str, field_analysis: FieldAnalysis) -> List[str]:
        """Extract transferable skills across fields"""
        transferable_skills = []
        
        # Define transferable skill patterns
        transferable_patterns = [
            'communication', 'leadership', 'problem solving', 'analytical thinking',
            'project management', 'teamwork', 'time management', 'adaptability',
            'creativity', 'critical thinking', 'decision making', 'strategic thinking'
        ]
        
        for skill in transferable_patterns:
            if skill in text:
                transferable_skills.append(skill)
        
        return transferable_skills
    
    def _extract_industry_experience(self, text: str, resume_data: Dict[str, Any] = None) -> List[str]:
        """Extract industry experience"""
        industries = []
        
        # Common industry keywords
        industry_keywords = [
            'technology', 'finance', 'healthcare', 'education', 'retail',
            'manufacturing', 'consulting', 'government', 'non-profit',
            'media', 'entertainment', 'real estate', 'transportation'
        ]
        
        for industry in industry_keywords:
            if industry in text:
                industries.append(industry)
        
        return industries
    
    def _analyze_income(self, text: str, experience_analysis: ExperienceAnalysis, 
                       field_analysis: FieldAnalysis, resume_data: Dict[str, Any] = None) -> IncomeAnalysis:
        """Analyze income and compensation based on experience and field"""
        
        # Base salary ranges by field and experience level
        salary_ranges = {
            FieldType.DATA_ANALYSIS: {
                ExperienceLevel.ENTRY: (45000, 65000),
                ExperienceLevel.MID: (65000, 95000),
                ExperienceLevel.SENIOR: (95000, 140000)
            },
            FieldType.PROJECT_MANAGEMENT: {
                ExperienceLevel.ENTRY: (50000, 70000),
                ExperienceLevel.MID: (70000, 100000),
                ExperienceLevel.SENIOR: (100000, 150000)
            },
            FieldType.SOFTWARE_DEVELOPMENT: {
                ExperienceLevel.ENTRY: (55000, 75000),
                ExperienceLevel.MID: (75000, 110000),
                ExperienceLevel.SENIOR: (110000, 180000)
            },
            FieldType.MARKETING: {
                ExperienceLevel.ENTRY: (40000, 60000),
                ExperienceLevel.MID: (60000, 90000),
                ExperienceLevel.SENIOR: (90000, 130000)
            },
            FieldType.FINANCE: {
                ExperienceLevel.ENTRY: (45000, 65000),
                ExperienceLevel.MID: (65000, 95000),
                ExperienceLevel.SENIOR: (95000, 150000)
            },
            FieldType.SALES: {
                ExperienceLevel.ENTRY: (40000, 60000),
                ExperienceLevel.MID: (60000, 90000),
                ExperienceLevel.SENIOR: (90000, 140000)
            },
            FieldType.OPERATIONS: {
                ExperienceLevel.ENTRY: (40000, 60000),
                ExperienceLevel.MID: (60000, 85000),
                ExperienceLevel.SENIOR: (85000, 120000)
            },
            FieldType.HR: {
                ExperienceLevel.ENTRY: (40000, 55000),
                ExperienceLevel.MID: (55000, 80000),
                ExperienceLevel.SENIOR: (80000, 110000)
            }
        }
        
        # Get base range for field and experience level
        field = field_analysis.primary_field
        level = experience_analysis.level
        base_min, base_max = salary_ranges.get(field, salary_ranges[FieldType.OPERATIONS]).get(level, (50000, 75000))
        
        # Adjust based on experience years
        experience_factor = min(experience_analysis.total_years / 5.0, 1.5)
        adjusted_min = int(base_min * experience_factor)
        adjusted_max = int(base_max * experience_factor)
        
        # Estimate current salary (middle of range)
        estimated_salary = (adjusted_min + adjusted_max) // 2
        
        # Calculate percentile (simplified)
        percentile = min(0.5 + (experience_analysis.total_years * 0.1), 0.95)
        
        # Determine market position
        if percentile >= 0.8:
            market_position = "Above Market"
        elif percentile >= 0.6:
            market_position = "Market Rate"
        else:
            market_position = "Below Market"
        
        # Create salary range
        salary_range = {
            "min": adjusted_min,
            "max": adjusted_max,
            "median": estimated_salary
        }
        
        # Compensation breakdown (simplified)
        compensation_breakdown = {
            "base_salary": 0.85,
            "bonus": 0.10,
            "benefits": 0.05
        }
        
        return IncomeAnalysis(
            estimated_salary=estimated_salary,
            percentile=percentile,
            market_position=market_position,
            salary_range=salary_range,
            compensation_breakdown=compensation_breakdown
        )
    
    def _estimate_field_experience(self, text: str, field: FieldType, resume_data: Dict[str, Any] = None) -> float:
        """Estimate years of experience in specific field"""
        # This is a simplified estimation - in practice, you'd use more sophisticated NLP
        field_keywords = self.field_keywords[field]
        keyword_count = sum(1 for keyword in field_keywords if keyword in text)
        
        # Rough estimation: more keywords = more experience
        if keyword_count >= 10:
            return 5.0  # 5+ years
        elif keyword_count >= 6:
            return 3.0  # 3-5 years
        elif keyword_count >= 3:
            return 1.5  # 1-2 years
        else:
            return 0.5  # < 1 year
    
    def _calculate_total_experience(self, text: str, resume_data: Dict[str, Any] = None) -> float:
        """Calculate total years of experience"""
        # Look for year patterns (both 4-digit years and year ranges)
        year_pattern = r'\b(19\d{2}|20\d{2})\b'
        years = re.findall(year_pattern, text)
        
        # Convert to full years
        full_years = []
        for year in years:
            if len(year) == 2:
                # If it's a 2-digit year, assume it's 20xx
                full_years.append(int('20' + year))
            else:
                full_years.append(int(year))
        
        if len(full_years) >= 2:
            # Calculate difference between earliest and latest years
            return max(full_years) - min(full_years)
        
        # Fallback estimation based on job titles and experience level
        senior_indicators = len([ind for ind in self.experience_indicators[ExperienceLevel.SENIOR] if ind in text])
        mid_indicators = len([ind for ind in self.experience_indicators[ExperienceLevel.MID] if ind in text])
        
        if senior_indicators > 0:
            return 8.0
        elif mid_indicators > 0:
            return 4.0
        else:
            return 1.0
    
    def _analyze_career_progression(self, text: str, resume_data: Dict[str, Any] = None) -> str:
        """Analyze career progression pattern"""
        # Look for progression indicators
        if any(indicator in text for indicator in ['promoted', 'advanced', 'progressed']):
            return "Steady progression"
        elif any(indicator in text for indicator in ['senior', 'lead', 'manager']):
            return "Leadership track"
        elif any(indicator in text for indicator in ['specialist', 'expert', 'principal']):
            return "Specialist track"
        else:
            return "Standard progression"
    
    def _extract_leadership_indicators(self, text: str) -> List[str]:
        """Extract leadership indicators from text"""
        found_indicators = []
        for indicator in self.leadership_indicators:
            if indicator in text:
                found_indicators.append(indicator)
        return found_indicators
    
    def _extract_skills_from_text(self, text: str) -> Dict[str, int]:
        """Extract skills and their frequencies from text"""
        # This is a simplified extraction - in practice, you'd use more sophisticated NLP
        skills = {}
        
        # Common skill patterns
        skill_patterns = [
            r'\b\w+(?:\.js|\.py|\.net|\.com)\b',  # Technologies
            r'\b(?:sql|python|java|javascript|react|angular|node)\b',  # Programming
            r'\b(?:excel|tableau|power bi|salesforce|crm)\b',  # Tools
            r'\b(?:agile|scrum|waterfall|pmp)\b',  # Methodologies
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                skills[match.lower()] = skills.get(match.lower(), 0) + 1
        
        return skills
    
    def _categorize_skill(self, skill: str) -> SkillCategory:
        """Categorize a skill into technical, business, or soft skills"""
        skill_lower = skill.lower()
        
        for category, keywords in self.skill_categories.items():
            for keyword in keywords:
                if keyword in skill_lower:
                    return category
        
        # Default to technical if unclear
        return SkillCategory.TECHNICAL
    
    def _calculate_skill_proficiency(self, skill: str, frequency: int, text: str) -> float:
        """Calculate skill proficiency level (0-1)"""
        # Base score from frequency
        base_score = min(frequency / 5, 1.0)
        
        # Boost score if skill appears in context with proficiency indicators
        proficiency_indicators = ['expert', 'advanced', 'proficient', 'experienced']
        context_boost = 0.2 if any(indicator in text for indicator in proficiency_indicators) else 0
        
        return min(base_score + context_boost, 1.0)
    
    def _extract_job_history(self, text: str, resume_data: Dict[str, Any] = None) -> List[str]:
        """Extract job history from text"""
        # This is a simplified extraction - in practice, you'd use more sophisticated NLP
        job_titles = []
        
        # Common job title patterns
        title_patterns = [
            r'\b(?:senior|junior|lead|principal|chief|vp|director|manager|analyst|developer|engineer)\s+\w+\b',
            r'\b(?:software|data|business|product|project|marketing|sales|finance|hr)\s+(?:engineer|analyst|manager|specialist|coordinator)\b'
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            job_titles.extend(matches)
        
        return job_titles[:5]  # Return top 5 most recent
    
    def _analyze_progression_pattern(self, job_history: List[str]) -> List[str]:
        """Analyze career progression pattern"""
        if len(job_history) < 2:
            return ["Early career"]
        
        progression = []
        for i in range(len(job_history) - 1):
            current = job_history[i].lower()
            previous = job_history[i + 1].lower()
            
            if 'senior' in current and 'senior' not in previous:
                progression.append("Promotion to senior level")
            elif 'manager' in current and 'manager' not in previous:
                progression.append("Promotion to management")
            elif 'lead' in current and 'lead' not in previous:
                progression.append("Promotion to lead role")
            else:
                progression.append("Role transition")
        
        return progression
    
    def _predict_next_career_steps(self, job_history: List[str], text: str) -> List[str]:
        """Predict next logical career steps"""
        if not job_history:
            return ["Entry-level position"]
        
        current_role = job_history[0].lower()
        next_steps = []
        
        if 'junior' in current_role or 'associate' in current_role:
            next_steps.extend(["Senior role", "Specialist position"])
        elif 'senior' in current_role:
            next_steps.extend(["Lead role", "Manager position"])
        elif 'lead' in current_role:
            next_steps.extend(["Manager", "Director"])
        elif 'manager' in current_role:
            next_steps.extend(["Senior Manager", "Director"])
        elif 'director' in current_role:
            next_steps.extend(["VP", "C-level position"])
        
        return next_steps
    
    def _calculate_growth_potential(self, job_history: List[str], text: str) -> float:
        """Calculate career growth potential (0-1)"""
        if not job_history:
            return 0.8  # High potential for entry level
        
        current_role = job_history[0].lower()
        
        # Higher potential for lower-level positions
        if any(level in current_role for level in ['junior', 'associate', 'entry']):
            return 0.9
        elif any(level in current_role for level in ['senior', 'specialist']):
            return 0.7
        elif any(level in current_role for level in ['lead', 'manager']):
            return 0.6
        elif any(level in current_role for level in ['director', 'vp']):
            return 0.4
        else:
            return 0.3
    
    def _calculate_advancement_readiness(self, text: str, job_history: List[str]) -> float:
        """Calculate advancement readiness (0-1)"""
        readiness_score = 0
        
        # Leadership indicators
        leadership_count = len(self._extract_leadership_indicators(text))
        readiness_score += min(leadership_count / 5, 0.3)
        
        # Experience level
        if job_history:
            current_role = job_history[0].lower()
            if any(level in current_role for level in ['senior', 'lead']):
                readiness_score += 0.4
            elif any(level in current_role for level in ['manager', 'director']):
                readiness_score += 0.6
            else:
                readiness_score += 0.2
        
        # Skills diversity
        skills_analysis = self._analyze_skills(text)
        if skills_analysis.technical_skills and skills_analysis.business_skills:
            readiness_score += 0.2
        
        return min(readiness_score, 1.0)
    
    def _extract_industry_focus(self, text: str, job_history: List[str]) -> List[str]:
        """Extract industry focus from experience"""
        industries = []
        
        # Industry keywords
        industry_keywords = {
            'technology': ['tech', 'software', 'it', 'digital', 'startup'],
            'finance': ['banking', 'investment', 'financial', 'trading'],
            'healthcare': ['medical', 'health', 'pharmaceutical', 'clinical'],
            'education': ['academic', 'university', 'school', 'learning'],
            'retail': ['e-commerce', 'retail', 'consumer', 'sales']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                industries.append(industry)
        
        return industries

    def get_analysis_summary(self, analysis: ResumeAnalysis) -> Dict[str, Any]:
        """Get a summary of the resume analysis"""
        return {
            'primary_field': analysis.field_analysis.primary_field.value,
            'secondary_field': analysis.field_analysis.secondary_field.value if analysis.field_analysis.secondary_field else None,
            'experience_level': analysis.experience_analysis.level.value,
            'total_experience_years': analysis.experience_analysis.total_years,
            'leadership_potential': analysis.leadership_potential,
            'technical_business_ratio': analysis.skills_analysis.technical_business_ratio,
            'growth_potential': analysis.career_trajectory.growth_potential,
            'advancement_readiness': analysis.career_trajectory.advancement_readiness,
            'next_career_steps': analysis.career_trajectory.next_logical_steps,
            'transferable_skills': analysis.transferable_skills,
            'industry_experience': analysis.industry_experience
        } 