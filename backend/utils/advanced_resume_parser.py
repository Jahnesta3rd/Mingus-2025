"""
Advanced Resume Parser for Mingus Financial App
Extends the existing ResumeParser with advanced analytics for African American professionals
Target demographic: 25-35 years old, $40k-$100k income, major metro areas
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

# Import the base ResumeParser
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import ResumeParser, fallback to a minimal implementation if not available
try:
    from api.resume_endpoints import ResumeParser
except ImportError:
    # Fallback implementation for testing
    class ResumeParser:
        def __init__(self):
            self.errors = []
            self.warnings = []
            self.confidence_score = 0.0
        
        def parse_resume(self, content: str, file_name: str = None) -> Dict[str, Any]:
            # Minimal implementation for testing
            return {
                'success': True,
                'parsed_data': {
                    'personal_info': {'full_name': 'Test User'},
                    'contact_info': {'email': 'test@example.com'},
                    'experience': [],
                    'education': [],
                    'skills': [],
                    'certifications': [],
                    'projects': [],
                    'languages': [],
                    'summary': ''
                },
                'metadata': {'confidence_score': 0.0},
                'errors': [],
                'warnings': []
            }

logger = logging.getLogger(__name__)

class CareerField(Enum):
    """Career field classifications"""
    TECHNOLOGY = "Technology"
    FINANCE = "Finance"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    MARKETING = "Marketing"
    SALES = "Sales"
    CONSULTING = "Consulting"
    REAL_ESTATE = "Real Estate"
    LEGAL = "Legal"
    NON_PROFIT = "Non-Profit"
    GOVERNMENT = "Government"
    RETAIL = "Retail"
    MANUFACTURING = "Manufacturing"
    OTHER = "Other"

class ExperienceLevel(Enum):
    """Experience level classifications"""
    ENTRY = "Entry Level"
    MID = "Mid Level"
    SENIOR = "Senior Level"
    EXECUTIVE = "Executive Level"

class SkillCategory(Enum):
    """Skill category classifications"""
    TECHNICAL = "Technical"
    SOFT = "Soft Skills"
    LEADERSHIP = "Leadership"
    FINANCIAL = "Financial"
    COMMUNICATION = "Communication"
    ANALYTICAL = "Analytical"

@dataclass
class CareerTrajectory:
    """Career trajectory analysis result"""
    growth_pattern: str
    promotion_frequency: float
    salary_progression: List[float]
    role_advancement: List[str]
    industry_consistency: bool
    leadership_development: bool

@dataclass
class LeadershipIndicator:
    """Leadership experience indicator"""
    title_keywords: List[str]
    responsibility_keywords: List[str]
    team_size_indicators: List[str]
    management_terms: List[str]
    leadership_score: float

@dataclass
class IncomePotential:
    """Income potential analysis result"""
    estimated_current_salary: float
    market_value_range: Tuple[float, float]
    growth_potential: float
    industry_multiplier: float
    location_multiplier: float
    experience_multiplier: float

class AdvancedResumeParser(ResumeParser):
    """
    Advanced Resume Parser extending the base ResumeParser
    Focused on African American professionals aged 25-35 earning $40k-$100k
    """
    
    def __init__(self):
        super().__init__()
        self.career_field_keywords = self._initialize_career_keywords()
        self.skill_categories = self._initialize_skill_categories()
        self.leadership_indicators = self._initialize_leadership_indicators()
        self.salary_data = self._initialize_salary_data()
        
    def _initialize_career_keywords(self) -> Dict[CareerField, List[str]]:
        """Initialize career field classification keywords"""
        return {
            CareerField.TECHNOLOGY: [
                'software', 'developer', 'engineer', 'programming', 'coding', 'data science',
                'machine learning', 'artificial intelligence', 'cybersecurity', 'cloud',
                'devops', 'frontend', 'backend', 'full stack', 'mobile', 'web development',
                'database', 'api', 'system administrator', 'IT', 'information technology'
            ],
            CareerField.FINANCE: [
                'financial', 'banking', 'investment', 'accounting', 'audit', 'tax',
                'financial analyst', 'portfolio', 'wealth management', 'insurance',
                'risk management', 'compliance', 'treasury', 'corporate finance',
                'investment banking', 'private equity', 'hedge fund', 'fintech'
            ],
            CareerField.HEALTHCARE: [
                'healthcare', 'medical', 'nursing', 'physician', 'doctor', 'therapist',
                'pharmacy', 'healthcare administration', 'public health', 'clinical',
                'patient care', 'medical research', 'healthcare technology', 'biomedical'
            ],
            CareerField.EDUCATION: [
                'education', 'teaching', 'teacher', 'professor', 'instructor', 'curriculum',
                'academic', 'student', 'learning', 'training', 'educational technology',
                'school administration', 'higher education', 'K-12', 'elementary', 'secondary'
            ],
            CareerField.MARKETING: [
                'marketing', 'advertising', 'brand', 'digital marketing', 'social media',
                'content marketing', 'SEO', 'SEM', 'marketing analyst', 'campaign',
                'public relations', 'PR', 'communications', 'brand management'
            ],
            CareerField.SALES: [
                'sales', 'account executive', 'business development', 'revenue',
                'client relations', 'customer success', 'territory', 'quota',
                'prospecting', 'lead generation', 'account management'
            ],
            CareerField.CONSULTING: [
                'consulting', 'consultant', 'advisory', 'strategy', 'management consulting',
                'business consulting', 'process improvement', 'transformation'
            ],
            CareerField.REAL_ESTATE: [
                'real estate', 'property', 'broker', 'agent', 'commercial real estate',
                'residential', 'property management', 'real estate development'
            ],
            CareerField.LEGAL: [
                'legal', 'attorney', 'lawyer', 'paralegal', 'compliance', 'litigation',
                'corporate law', 'contract', 'legal counsel', 'juris doctor'
            ],
            CareerField.NON_PROFIT: [
                'non-profit', 'nonprofit', 'foundation', 'charity', 'advocacy',
                'community', 'social impact', 'philanthropy', 'volunteer'
            ],
            CareerField.GOVERNMENT: [
                'government', 'federal', 'state', 'local', 'public sector', 'policy',
                'administration', 'civil service', 'municipal', 'county'
            ],
            CareerField.RETAIL: [
                'retail', 'merchandising', 'store management', 'customer service',
                'inventory', 'supply chain', 'e-commerce', 'omnichannel'
            ],
            CareerField.MANUFACTURING: [
                'manufacturing', 'production', 'operations', 'supply chain', 'logistics',
                'quality control', 'process improvement', 'lean manufacturing'
            ]
        }
    
    def _initialize_skill_categories(self) -> Dict[SkillCategory, List[str]]:
        """Initialize skill category classifications"""
        return {
            SkillCategory.TECHNICAL: [
                'python', 'javascript', 'java', 'sql', 'react', 'node.js', 'aws',
                'machine learning', 'data analysis', 'excel', 'power bi', 'tableau',
                'programming', 'coding', 'software development', 'database', 'api'
            ],
            SkillCategory.SOFT: [
                'communication', 'teamwork', 'problem solving', 'critical thinking',
                'adaptability', 'time management', 'organization', 'creativity',
                'interpersonal', 'collaboration', 'flexibility', 'work ethic'
            ],
            SkillCategory.LEADERSHIP: [
                'leadership', 'management', 'mentoring', 'coaching', 'team building',
                'strategic planning', 'decision making', 'project management',
                'supervision', 'delegation', 'motivation', 'influence'
            ],
            SkillCategory.FINANCIAL: [
                'financial analysis', 'budgeting', 'forecasting', 'financial modeling',
                'accounting', 'bookkeeping', 'tax preparation', 'investment analysis',
                'risk assessment', 'cost control', 'revenue optimization'
            ],
            SkillCategory.COMMUNICATION: [
                'public speaking', 'presentation', 'writing', 'editing', 'copywriting',
                'technical writing', 'documentation', 'reporting', 'negotiation',
                'client relations', 'customer service', 'sales'
            ],
            SkillCategory.ANALYTICAL: [
                'data analysis', 'statistical analysis', 'research', 'market research',
                'trend analysis', 'performance metrics', 'KPI', 'reporting',
                'business intelligence', 'data visualization', 'forecasting'
            ]
        }
    
    def _initialize_leadership_indicators(self) -> LeadershipIndicator:
        """Initialize leadership experience indicators"""
        return LeadershipIndicator(
            title_keywords=[
                'manager', 'director', 'supervisor', 'lead', 'head', 'chief', 'vp',
                'vice president', 'senior', 'principal', 'executive', 'coordinator',
                'team lead', 'project manager', 'program manager'
            ],
            responsibility_keywords=[
                'managed', 'led', 'supervised', 'directed', 'coordinated', 'oversaw',
                'mentored', 'coached', 'trained', 'developed', 'guided', 'facilitated',
                'organized', 'planned', 'strategized', 'delegated', 'assigned'
            ],
            team_size_indicators=[
                'team of', 'managed team', 'led team', 'supervised team', 'direct reports',
                'team members', 'staff of', 'department of', 'group of'
            ],
            management_terms=[
                'budget', 'hiring', 'firing', 'performance review', 'strategic planning',
                'resource allocation', 'project management', 'stakeholder management',
                'cross-functional', 'interdepartmental', 'vendor management'
            ],
            leadership_score=0.0
        )
    
    def _initialize_salary_data(self) -> Dict[str, Dict[str, float]]:
        """Initialize salary data for income potential calculation"""
        return {
            'base_salaries': {
                'entry': 40000,
                'mid': 65000,
                'senior': 85000,
                'executive': 120000
            },
            'industry_multipliers': {
                'Technology': 1.2,
                'Finance': 1.15,
                'Healthcare': 1.0,
                'Education': 0.85,
                'Marketing': 0.95,
                'Sales': 0.9,
                'Consulting': 1.1,
                'Real Estate': 0.9,
                'Legal': 1.1,
                'Non-Profit': 0.8,
                'Government': 0.9,
                'Retail': 0.75,
                'Manufacturing': 0.95
            },
            'location_multipliers': {
                'New York': 1.3,
                'San Francisco': 1.4,
                'Los Angeles': 1.2,
                'Chicago': 1.1,
                'Houston': 1.0,
                'Phoenix': 0.95,
                'Philadelphia': 1.05,
                'San Antonio': 0.9,
                'San Diego': 1.15,
                'Dallas': 1.0,
                'Austin': 1.1,
                'Jacksonville': 0.85,
                'Fort Worth': 0.95,
                'Columbus': 0.9,
                'Charlotte': 0.95,
                'San Jose': 1.35,
                'Nashville': 0.9,
                'Denver': 1.05,
                'Washington': 1.2,
                'Boston': 1.25
            }
        }
    
    def classify_career_field(self, parsed_data: Dict[str, Any]) -> CareerField:
        """
        Classify the primary career field based on resume content
        
        Args:
            parsed_data: Parsed resume data from base parser
            
        Returns:
            CareerField enum value
        """
        try:
            # Combine all text content for analysis
            content_parts = []
            
            # Add experience descriptions
            for exp in parsed_data.get('experience', []):
                content_parts.append(exp.get('description', ''))
                content_parts.append(exp.get('job_title', ''))
                content_parts.append(exp.get('company', ''))
            
            # Add skills
            content_parts.extend(parsed_data.get('skills', []))
            
            # Add summary
            content_parts.append(parsed_data.get('summary', ''))
            
            # Add education
            for edu in parsed_data.get('education', []):
                content_parts.append(edu.get('degree', ''))
                content_parts.append(edu.get('university', ''))
            
            # Combine all text
            full_text = ' '.join(content_parts).lower()
            
            # Score each career field
            field_scores = {}
            for field, keywords in self.career_field_keywords.items():
                score = 0
                for keyword in keywords:
                    # Count occurrences with word boundaries
                    matches = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', full_text))
                    score += matches
                field_scores[field] = score
            
            # Find the field with highest score
            if field_scores:
                best_field = max(field_scores.items(), key=lambda x: x[1])
                if best_field[1] > 0:
                    logger.debug(f"Career field classified as: {best_field[0].value} (score: {best_field[1]})")
                    return best_field[0]
            
            logger.debug("No specific career field identified, defaulting to OTHER")
            return CareerField.OTHER
            
        except Exception as e:
            logger.error(f"Error classifying career field: {str(e)}")
            return CareerField.OTHER
    
    def calculate_experience_level(self, parsed_data: Dict[str, Any]) -> ExperienceLevel:
        """
        Calculate experience level based on years of experience and job titles
        
        Args:
            parsed_data: Parsed resume data from base parser
            
        Returns:
            ExperienceLevel enum value
        """
        try:
            experience_entries = parsed_data.get('experience', [])
            if not experience_entries:
                return ExperienceLevel.ENTRY
            
            # Calculate total years of experience
            total_years = self._calculate_total_experience_years(experience_entries)
            
            # Analyze job titles for seniority indicators
            title_seniority = self._analyze_title_seniority(experience_entries)
            
            # Combine years and title analysis
            if total_years >= 10 or title_seniority >= 0.8:
                return ExperienceLevel.EXECUTIVE
            elif total_years >= 6 or title_seniority >= 0.6:
                return ExperienceLevel.SENIOR
            elif total_years >= 3 or title_seniority >= 0.3:
                return ExperienceLevel.MID
            else:
                return ExperienceLevel.ENTRY
                
        except Exception as e:
            logger.error(f"Error calculating experience level: {str(e)}")
            return ExperienceLevel.ENTRY
    
    def _calculate_total_experience_years(self, experience_entries: List[Dict[str, Any]]) -> float:
        """Calculate total years of experience from experience entries"""
        total_months = 0
        
        for exp in experience_entries:
            start_date = exp.get('start_date')
            end_date = exp.get('end_date')
            
            if start_date and end_date:
                try:
                    # Parse dates (assuming format like "2020-01" or "Jan 2020")
                    start = self._parse_date(start_date)
                    end = self._parse_date(end_date) if end_date.lower() != 'present' else datetime.now()
                    
                    if start and end:
                        months = (end.year - start.year) * 12 + (end.month - start.month)
                        total_months += max(0, months)
                except Exception as e:
                    logger.debug(f"Error parsing dates for experience entry: {e}")
                    continue
        
        return total_months / 12.0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
            
        date_str = date_str.strip()
        
        # Common date formats
        formats = [
            '%Y-%m',  # 2020-01
            '%m/%Y',  # 01/2020
            '%B %Y',  # January 2020
            '%b %Y',  # Jan 2020
            '%Y',     # 2020
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _analyze_title_seniority(self, experience_entries: List[Dict[str, Any]]) -> float:
        """Analyze job titles for seniority indicators"""
        seniority_keywords = {
            'executive': ['ceo', 'cto', 'cfo', 'vp', 'vice president', 'director', 'chief'],
            'senior': ['senior', 'lead', 'principal', 'head', 'manager', 'supervisor'],
            'mid': ['analyst', 'specialist', 'coordinator', 'associate'],
            'entry': ['junior', 'assistant', 'intern', 'trainee', 'entry']
        }
        
        total_score = 0
        entry_count = 0
        
        for exp in experience_entries:
            title = exp.get('job_title', '').lower()
            if not title:
                continue
                
            entry_count += 1
            entry_score = 0
            
            # Check for seniority keywords
            for level, keywords in seniority_keywords.items():
                for keyword in keywords:
                    if keyword in title:
                        if level == 'executive':
                            entry_score = 1.0
                        elif level == 'senior':
                            entry_score = 0.7
                        elif level == 'mid':
                            entry_score = 0.4
                        elif level == 'entry':
                            entry_score = 0.1
                        break
                if entry_score > 0:
                    break
            
            total_score += entry_score
        
        return total_score / max(1, entry_count)
    
    def analyze_career_trajectory(self, parsed_data: Dict[str, Any]) -> CareerTrajectory:
        """
        Analyze career trajectory and growth patterns
        
        Args:
            parsed_data: Parsed resume data from base parser
            
        Returns:
            CareerTrajectory analysis result
        """
        try:
            experience_entries = parsed_data.get('experience', [])
            if not experience_entries:
                return CareerTrajectory(
                    growth_pattern="No experience data",
                    promotion_frequency=0.0,
                    salary_progression=[],
                    role_advancement=[],
                    industry_consistency=False,
                    leadership_development=False
                )
            
            # Sort experience by date (most recent first)
            sorted_experience = sorted(experience_entries, 
                                    key=lambda x: self._parse_date(x.get('start_date', '1900-01')) or datetime(1900, 1, 1),
                                    reverse=True)
            
            # Analyze growth patterns
            growth_pattern = self._determine_growth_pattern(sorted_experience)
            promotion_frequency = self._calculate_promotion_frequency(sorted_experience)
            role_advancement = [exp.get('job_title', '') for exp in sorted_experience]
            industry_consistency = self._check_industry_consistency(sorted_experience)
            leadership_development = self._check_leadership_development(sorted_experience)
            
            # Estimate salary progression (simplified)
            salary_progression = self._estimate_salary_progression(sorted_experience)
            
            return CareerTrajectory(
                growth_pattern=growth_pattern,
                promotion_frequency=promotion_frequency,
                salary_progression=salary_progression,
                role_advancement=role_advancement,
                industry_consistency=industry_consistency,
                leadership_development=leadership_development
            )
            
        except Exception as e:
            logger.error(f"Error analyzing career trajectory: {str(e)}")
            return CareerTrajectory(
                growth_pattern="Analysis error",
                promotion_frequency=0.0,
                salary_progression=[],
                role_advancement=[],
                industry_consistency=False,
                leadership_development=False
            )
    
    def _determine_growth_pattern(self, experience_entries: List[Dict[str, Any]]) -> str:
        """Determine the overall growth pattern"""
        if len(experience_entries) < 2:
            return "Insufficient data"
        
        # Analyze title progression
        titles = [exp.get('job_title', '').lower() for exp in experience_entries]
        
        # Check for upward progression
        seniority_indicators = ['senior', 'lead', 'manager', 'director', 'vp', 'chief']
        progression_score = 0
        
        for i in range(len(titles) - 1):
            current_title = titles[i]
            previous_title = titles[i + 1]
            
            # Check if current role has higher seniority indicators
            current_seniority = sum(1 for indicator in seniority_indicators if indicator in current_title)
            previous_seniority = sum(1 for indicator in seniority_indicators if indicator in previous_title)
            
            if current_seniority > previous_seniority:
                progression_score += 1
            elif current_seniority < previous_seniority:
                progression_score -= 1
        
        if progression_score > 0:
            return "Upward trajectory"
        elif progression_score < 0:
            return "Downward trajectory"
        else:
            return "Lateral movement"
    
    def _calculate_promotion_frequency(self, experience_entries: List[Dict[str, Any]]) -> float:
        """Calculate frequency of promotions/role changes"""
        if len(experience_entries) < 2:
            return 0.0
        
        # Calculate total career span
        earliest_start = min(
            self._parse_date(exp.get('start_date', '1900-01')) or datetime(1900, 1, 1)
            for exp in experience_entries
        )
        latest_end = max(
            self._parse_date(exp.get('end_date', '1900-01')) or datetime.now()
            for exp in experience_entries
        )
        
        career_span_years = (latest_end - earliest_start).days / 365.25
        role_changes = len(experience_entries) - 1
        
        return role_changes / max(1, career_span_years)
    
    def _check_industry_consistency(self, experience_entries: List[Dict[str, Any]]) -> bool:
        """Check if career has been within consistent industry"""
        if len(experience_entries) < 2:
            return True
        
        # Extract company names and job titles for industry analysis
        companies = [exp.get('company', '').lower() for exp in experience_entries]
        titles = [exp.get('job_title', '').lower() for exp in experience_entries]
        
        # Simple industry consistency check based on keywords
        industry_keywords = set()
        for company in companies:
            for field, keywords in self.career_field_keywords.items():
                for keyword in keywords:
                    if keyword in company:
                        industry_keywords.add(field)
                        break
        
        # If most entries share similar industry keywords, consider consistent
        return len(industry_keywords) <= 2
    
    def _check_leadership_development(self, experience_entries: List[Dict[str, Any]]) -> bool:
        """Check if there's evidence of leadership development over time"""
        leadership_scores = []
        
        for exp in experience_entries:
            title = exp.get('job_title', '').lower()
            description = exp.get('description', '').lower()
            
            score = 0
            # Check title for leadership indicators
            for keyword in self.leadership_indicators.title_keywords:
                if keyword in title:
                    score += 1
            
            # Check description for leadership indicators
            for keyword in self.leadership_indicators.responsibility_keywords:
                if keyword in description:
                    score += 0.5
            
            leadership_scores.append(score)
        
        # Check if leadership scores generally increase over time
        if len(leadership_scores) >= 2:
            return leadership_scores[0] > leadership_scores[-1]  # Most recent > oldest
        
        return False
    
    def _estimate_salary_progression(self, experience_entries: List[Dict[str, Any]]) -> List[float]:
        """Estimate salary progression based on role progression"""
        # This is a simplified estimation - in practice, you'd use more sophisticated models
        base_salaries = [50000, 60000, 70000, 80000, 90000, 100000]
        
        progression = []
        for i, exp in enumerate(experience_entries):
            # Simple progression based on role order and seniority
            base_salary = base_salaries[min(i, len(base_salaries) - 1)]
            
            # Adjust based on title seniority
            title = exp.get('job_title', '').lower()
            if any(keyword in title for keyword in ['senior', 'lead', 'manager']):
                base_salary *= 1.2
            elif any(keyword in title for keyword in ['director', 'vp', 'chief']):
                base_salary *= 1.5
            
            progression.append(base_salary)
        
        return progression
    
    def categorize_skills(self, parsed_data: Dict[str, Any]) -> Dict[SkillCategory, List[str]]:
        """
        Categorize skills into different skill types
        
        Args:
            parsed_data: Parsed resume data from base parser
            
        Returns:
            Dictionary mapping skill categories to lists of skills
        """
        try:
            skills = parsed_data.get('skills', [])
            if not skills:
                return {category: [] for category in SkillCategory}
            
            categorized_skills = {category: [] for category in SkillCategory}
            
            for skill in skills:
                skill_lower = skill.lower()
                categorized = False
                
                # Check each category
                for category, keywords in self.skill_categories.items():
                    for keyword in keywords:
                        if keyword.lower() in skill_lower:
                            categorized_skills[category].append(skill)
                            categorized = True
                            break
                    if categorized:
                        break
                
                # If not categorized, add to technical by default
                if not categorized:
                    categorized_skills[SkillCategory.TECHNICAL].append(skill)
            
            return categorized_skills
            
        except Exception as e:
            logger.error(f"Error categorizing skills: {str(e)}")
            return {category: [] for category in SkillCategory}
    
    def extract_leadership_indicators(self, parsed_data: Dict[str, Any]) -> LeadershipIndicator:
        """
        Extract leadership indicators from resume content
        
        Args:
            parsed_data: Parsed resume data from base parser
            
        Returns:
            LeadershipIndicator with leadership analysis
        """
        try:
            # Combine all text content
            content_parts = []
            
            for exp in parsed_data.get('experience', []):
                content_parts.append(exp.get('description', ''))
                content_parts.append(exp.get('job_title', ''))
            
            content_parts.append(parsed_data.get('summary', ''))
            
            full_text = ' '.join(content_parts).lower()
            
            # Calculate leadership score
            leadership_score = 0.0
            total_indicators = 0
            
            # Check title keywords
            title_matches = sum(1 for keyword in self.leadership_indicators.title_keywords 
                              if keyword in full_text)
            leadership_score += title_matches * 2
            total_indicators += len(self.leadership_indicators.title_keywords)
            
            # Check responsibility keywords
            responsibility_matches = sum(1 for keyword in self.leadership_indicators.responsibility_keywords 
                                       if keyword in full_text)
            leadership_score += responsibility_matches * 1.5
            total_indicators += len(self.leadership_indicators.responsibility_keywords)
            
            # Check team size indicators
            team_matches = sum(1 for keyword in self.leadership_indicators.team_size_indicators 
                             if keyword in full_text)
            leadership_score += team_matches * 1
            total_indicators += len(self.leadership_indicators.team_size_indicators)
            
            # Check management terms
            management_matches = sum(1 for keyword in self.leadership_indicators.management_terms 
                                   if keyword in full_text)
            leadership_score += management_matches * 1.2
            total_indicators += len(self.leadership_indicators.management_terms)
            
            # Normalize score
            normalized_score = leadership_score / max(1, total_indicators) if total_indicators > 0 else 0
            
            return LeadershipIndicator(
                title_keywords=self.leadership_indicators.title_keywords,
                responsibility_keywords=self.leadership_indicators.responsibility_keywords,
                team_size_indicators=self.leadership_indicators.team_size_indicators,
                management_terms=self.leadership_indicators.management_terms,
                leadership_score=normalized_score
            )
            
        except Exception as e:
            logger.error(f"Error extracting leadership indicators: {str(e)}")
            return LeadershipIndicator(
                title_keywords=[],
                responsibility_keywords=[],
                team_size_indicators=[],
                management_terms=[],
                leadership_score=0.0
            )
    
    def calculate_income_potential(self, parsed_data: Dict[str, Any], location: str = "New York") -> IncomePotential:
        """
        Calculate income potential based on experience, skills, and location
        
        Args:
            parsed_data: Parsed resume data from base parser
            location: Location for cost of living adjustment
            
        Returns:
            IncomePotential analysis result
        """
        try:
            # Get experience level
            experience_level = self.calculate_experience_level(parsed_data)
            
            # Get career field
            career_field = self.classify_career_field(parsed_data)
            
            # Get leadership indicators
            leadership = self.extract_leadership_indicators(parsed_data)
            
            # Base salary from experience level
            level_key = experience_level.value.lower().replace(' ', '_')
            base_salary = self.salary_data['base_salaries'].get(level_key, 50000)
            
            # Apply industry multiplier
            industry_multiplier = self.salary_data['industry_multipliers'].get(career_field.value, 1.0)
            
            # Apply location multiplier
            location_multiplier = self.salary_data['location_multipliers'].get(location, 1.0)
            
            # Apply experience multiplier based on years
            experience_entries = parsed_data.get('experience', [])
            total_years = self._calculate_total_experience_years(experience_entries)
            experience_multiplier = min(1.5, 1.0 + (total_years - 2) * 0.05)  # 5% per year after 2 years
            
            # Apply leadership bonus
            leadership_multiplier = 1.0 + (leadership.leadership_score * 0.2)  # Up to 20% bonus
            
            # Calculate final salary
            estimated_salary = (base_salary * industry_multiplier * location_multiplier * 
                              experience_multiplier * leadership_multiplier)
            
            # Calculate market value range (±15%)
            market_min = estimated_salary * 0.85
            market_max = estimated_salary * 1.15
            
            # Calculate growth potential (simplified)
            growth_potential = min(1.0, (leadership.leadership_score + experience_multiplier - 1) / 2)
            
            return IncomePotential(
                estimated_current_salary=estimated_salary,
                market_value_range=(market_min, market_max),
                growth_potential=growth_potential,
                industry_multiplier=industry_multiplier,
                location_multiplier=location_multiplier,
                experience_multiplier=experience_multiplier
            )
            
        except Exception as e:
            logger.error(f"Error calculating income potential: {str(e)}")
            return IncomePotential(
                estimated_current_salary=50000,
                market_value_range=(42500, 57500),
                growth_potential=0.3,
                industry_multiplier=1.0,
                location_multiplier=1.0,
                experience_multiplier=1.0
            )
    
    def parse_resume_advanced(self, content: str, file_name: str = None, location: str = "New York") -> Dict[str, Any]:
        """
        Parse resume with advanced analytics
        
        Args:
            content: Raw resume text content
            file_name: Original file name (optional)
            location: Location for income potential calculation
            
        Returns:
            Dictionary containing parsed resume data and advanced analytics
        """
        try:
            # Use base parser to get basic parsed data
            base_result = self.parse_resume(content, file_name)
            
            if not base_result.get('success', False):
                return base_result
            
            parsed_data = base_result.get('parsed_data', {})
            
            # Add advanced analytics
            advanced_analytics = {
                'career_field': self.classify_career_field(parsed_data).value,
                'experience_level': self.calculate_experience_level(parsed_data).value,
                'career_trajectory': self.analyze_career_trajectory(parsed_data).__dict__,
                'skills_categorized': {
                    category.value: skills 
                    for category, skills in self.categorize_skills(parsed_data).items()
                },
                'leadership_indicators': self.extract_leadership_indicators(parsed_data).__dict__,
                'income_potential': self.calculate_income_potential(parsed_data, location).__dict__
            }
            
            # Add advanced analytics to the result
            result = base_result.copy()
            result['advanced_analytics'] = advanced_analytics
            
            # Update metadata
            if 'metadata' in result:
                result['metadata']['advanced_analysis'] = True
                result['metadata']['analysis_timestamp'] = datetime.utcnow().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in advanced resume parsing: {str(e)}")
            return {
                'success': False,
                'error': f"Advanced parsing failed: {str(e)}",
                'parsed_data': {},
                'advanced_analytics': {}
            }
