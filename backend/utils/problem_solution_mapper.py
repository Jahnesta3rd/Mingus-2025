#!/usr/bin/env python3
"""
Problem Solution Mapper - Phase 3 of Job Description to Problem Statement Analysis
AI-powered solution mapping that identifies top skills, certifications, and titles
that maximize hiring probability by positioning candidates as solution providers
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from datetime import datetime, timedelta
from .job_problem_extractor import ProblemAnalysis, IndustryContext, CompanyStage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    """Types of recommendations that can be generated"""
    SKILL = "skill"
    CERTIFICATION = "certification"
    TITLE = "title"

@dataclass
class SolutionRecommendation:
    """Individual solution recommendation with scoring"""
    recommendation_type: RecommendationType
    name: str
    description: str
    relevance_score: int  # 0-100
    industry_demand_score: int  # 0-100
    career_impact_score: int  # 0-100
    learning_roi_score: int  # 0-100
    competitive_advantage_score: int  # 0-100
    total_score: int  # 0-100
    rank: int
    reasoning: str
    time_to_acquire: str
    cost_estimate: str
    salary_impact: str

@dataclass
class SolutionAnalysis:
    """Complete solution analysis for a problem statement"""
    problem_analysis: ProblemAnalysis
    top_skills: List[SolutionRecommendation]
    top_certifications: List[SolutionRecommendation]
    optimal_titles: List[SolutionRecommendation]
    action_plan: Dict[str, Any]
    generated_at: datetime

class ProblemSolutionMapper:
    """
    Maps business problems to potential solutions using AI analysis
    and generates prioritized recommendations for skills, certifications, and titles
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the solution mapper"""
        self.solution_frameworks = {
            'technical_solutions': {
                'automation': {
                    'skills': ['Python', 'RPA', 'Zapier', 'Power Automate', 'Automation Scripting'],
                    'certifications': ['Microsoft Power Platform', 'UiPath RPA Developer', 'Blue Prism Developer'],
                    'titles': ['Automation Engineer', 'Process Automation Specialist', 'RPA Developer']
                },
                'data_analysis': {
                    'skills': ['SQL', 'Tableau', 'Power BI', 'Python', 'R', 'Excel Advanced', 'Statistics'],
                    'certifications': ['Tableau Desktop Specialist', 'Microsoft Power BI', 'Google Analytics', 'SAS Certified'],
                    'titles': ['Data Analyst', 'Business Intelligence Analyst', 'Data Scientist', 'Analytics Manager']
                },
                'system_integration': {
                    'skills': ['APIs', 'ETL', 'Cloud Platforms', 'Middleware', 'Database Design'],
                    'certifications': ['AWS Solutions Architect', 'Azure Data Engineer', 'Google Cloud Professional'],
                    'titles': ['Integration Specialist', 'Systems Analyst', 'Cloud Architect', 'Data Engineer']
                }
            },
            'strategic_solutions': {
                'process_improvement': {
                    'skills': ['Lean Six Sigma', 'Agile', 'Project Management', 'Process Mapping', 'Change Management'],
                    'certifications': ['PMP', 'Lean Six Sigma Green Belt', 'Agile Certified Practitioner', 'ITIL'],
                    'titles': ['Process Improvement Manager', 'Operations Analyst', 'Business Process Consultant']
                },
                'change_management': {
                    'skills': ['Change Management', 'Training', 'Communication', 'Stakeholder Management', 'Leadership'],
                    'certifications': ['Prosci Change Management', 'Certified Change Management Professional'],
                    'titles': ['Change Management Specialist', 'Transformation Manager', 'Organizational Development Manager']
                },
                'leadership': {
                    'skills': ['Team Leadership', 'Stakeholder Management', 'Vision Setting', 'Strategic Planning', 'Decision Making'],
                    'certifications': ['Executive Leadership Program', 'Strategic Management Certificate'],
                    'titles': ['Team Lead', 'Manager', 'Director', 'VP', 'C-Level Executive']
                }
            },
            'industry_specific': {
                'finance': {
                    'skills': ['Financial Modeling', 'Risk Assessment', 'Regulatory Compliance', 'Accounting', 'Investment Analysis'],
                    'certifications': ['CFA', 'CPA', 'FRM', 'Series 7', 'CISA'],
                    'titles': ['Financial Analyst', 'Risk Manager', 'Compliance Officer', 'Investment Advisor']
                },
                'healthcare': {
                    'skills': ['HIPAA', 'Clinical Workflows', 'Patient Safety', 'Medical Terminology', 'Healthcare Analytics'],
                    'certifications': ['RHIA', 'CHPS', 'CPHIMS', 'Healthcare Analytics Certificate'],
                    'titles': ['Healthcare Analyst', 'Clinical Data Manager', 'Health Informatics Specialist']
                },
                'technology': {
                    'skills': ['DevOps', 'Cloud Architecture', 'Cybersecurity', 'Software Development', 'System Administration'],
                    'certifications': ['AWS Solutions Architect', 'CISSP', 'CISM', 'Google Cloud Professional'],
                    'titles': ['DevOps Engineer', 'Cloud Architect', 'Security Engineer', 'Software Engineer']
                }
            }
        }
        
        # Initialize OpenAI if API key provided
        if openai_api_key:
            openai.api_key = openai_api_key
            self.use_ai = True
        else:
            self.use_ai = False
            logger.warning("OpenAI API key not provided. Using rule-based solution mapping only.")
    
    def map_solutions(self, problem_analysis: ProblemAnalysis, user_profile: Optional[Dict] = None) -> SolutionAnalysis:
        """
        Map problems to potential solutions using AI analysis
        
        Args:
            problem_analysis: Problem analysis from JobProblemExtractor
            user_profile: Optional user profile for personalized recommendations
            
        Returns:
            SolutionAnalysis with prioritized recommendations
        """
        try:
            logger.info("Starting solution mapping for problem analysis")
            
            # Step 1: Identify relevant solution categories
            solution_categories = self._identify_solution_categories(problem_analysis)
            
            # Step 2: Generate skill recommendations
            skill_recommendations = self._generate_skill_recommendations(
                problem_analysis, solution_categories, user_profile
            )
            
            # Step 3: Generate certification recommendations
            certification_recommendations = self._generate_certification_recommendations(
                problem_analysis, solution_categories, user_profile
            )
            
            # Step 4: Generate title recommendations
            title_recommendations = self._generate_title_recommendations(
                problem_analysis, solution_categories, user_profile
            )
            
            # Step 5: Create action plan
            action_plan = self._create_action_plan(
                skill_recommendations, certification_recommendations, title_recommendations
            )
            
            return SolutionAnalysis(
                problem_analysis=problem_analysis,
                top_skills=skill_recommendations[:5],
                top_certifications=certification_recommendations[:5],
                optimal_titles=title_recommendations[:5],
                action_plan=action_plan,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error mapping solutions: {str(e)}")
            return self._create_fallback_analysis(problem_analysis)
    
    def _identify_solution_categories(self, problem_analysis: ProblemAnalysis) -> List[str]:
        """Identify relevant solution categories based on problem analysis"""
        categories = []
        
        # Analyze primary problems to identify solution categories
        for problem in problem_analysis.primary_problems:
            problem_text = problem.get('sentence', '').lower()
            
            # Technical solutions
            if any(keyword in problem_text for keyword in ['data', 'system', 'automation', 'integration', 'technical']):
                categories.extend(['automation', 'data_analysis', 'system_integration'])
            
            # Strategic solutions
            if any(keyword in problem_text for keyword in ['process', 'efficiency', 'improve', 'optimize', 'change']):
                categories.extend(['process_improvement', 'change_management'])
            
            # Leadership solutions
            if any(keyword in problem_text for keyword in ['lead', 'manage', 'team', 'strategy', 'vision']):
                categories.extend(['leadership'])
        
        # Add industry-specific categories
        industry = problem_analysis.industry_context.value
        if industry in ['finance', 'healthcare', 'technology']:
            categories.append(industry)
        
        # Remove duplicates and return
        return list(set(categories))
    
    def _generate_skill_recommendations(self, problem_analysis: ProblemAnalysis, 
                                      solution_categories: List[str], 
                                      user_profile: Optional[Dict] = None) -> List[SolutionRecommendation]:
        """Generate skill recommendations based on problem analysis"""
        recommendations = []
        
        # Get user's current skills for gap analysis
        user_skills = user_profile.get('skills', []) if user_profile else []
        
        # Collect all relevant skills
        all_skills = set()
        for category in solution_categories:
            if category in ['automation', 'data_analysis', 'system_integration']:
                all_skills.update(self.solution_frameworks['technical_solutions'].get(category, {}).get('skills', []))
            elif category in ['process_improvement', 'change_management', 'leadership']:
                all_skills.update(self.solution_frameworks['strategic_solutions'].get(category, {}).get('skills', []))
            elif category in ['finance', 'healthcare', 'technology']:
                all_skills.update(self.solution_frameworks['industry_specific'].get(category, {}).get('skills', []))
        
        # Score each skill
        for skill in all_skills:
            recommendation = self._score_skill(skill, problem_analysis, user_skills)
            if recommendation:
                recommendations.append(recommendation)
        
        # Sort by total score and return top recommendations
        recommendations.sort(key=lambda x: x.total_score, reverse=True)
        return recommendations
    
    def _score_skill(self, skill: str, problem_analysis: ProblemAnalysis, user_skills: List[str]) -> Optional[SolutionRecommendation]:
        """Score a specific skill based on problem relevance and other factors"""
        
        # Calculate relevance score (0-100)
        relevance_score = self._calculate_relevance_score(skill, problem_analysis)
        
        # Calculate industry demand score (0-100)
        industry_demand_score = self._calculate_industry_demand_score(skill, problem_analysis.industry_context)
        
        # Calculate career impact score (0-100)
        career_impact_score = self._calculate_career_impact_score(skill, problem_analysis.company_stage)
        
        # Calculate learning ROI score (0-100)
        learning_roi_score = self._calculate_learning_roi_score(skill, user_skills)
        
        # Calculate competitive advantage score (0-100)
        competitive_advantage_score = self._calculate_competitive_advantage_score(skill, problem_analysis)
        
        # Calculate total score with weights
        total_score = int(
            relevance_score * 0.30 +
            industry_demand_score * 0.25 +
            career_impact_score * 0.25 +
            learning_roi_score * 0.10 +
            competitive_advantage_score * 0.10
        )
        
        # Only return recommendations with meaningful scores
        if total_score < 30:
            return None
        
        return SolutionRecommendation(
            recommendation_type=RecommendationType.SKILL,
            name=skill,
            description=self._get_skill_description(skill),
            relevance_score=relevance_score,
            industry_demand_score=industry_demand_score,
            career_impact_score=career_impact_score,
            learning_roi_score=learning_roi_score,
            competitive_advantage_score=competitive_advantage_score,
            total_score=total_score,
            rank=0,  # Will be set after sorting
            reasoning=self._generate_skill_reasoning(skill, problem_analysis),
            time_to_acquire=self._estimate_skill_acquisition_time(skill),
            cost_estimate=self._estimate_skill_cost(skill),
            salary_impact=self._estimate_salary_impact(skill)
        )
    
    def _calculate_relevance_score(self, skill: str, problem_analysis: ProblemAnalysis) -> int:
        """Calculate how directly the skill addresses the core problems"""
        skill_lower = skill.lower()
        relevance_score = 50  # Base score
        
        # Check against primary problems
        for problem in problem_analysis.primary_problems:
            problem_text = problem.get('sentence', '').lower()
            
            # Direct keyword matches
            if skill_lower in problem_text:
                relevance_score += 20
            
            # Related concept matches
            related_concepts = self._get_related_concepts(skill)
            for concept in related_concepts:
                if concept in problem_text:
                    relevance_score += 10
        
        # Check against problem statement
        problem_statement = problem_analysis.problem_statement
        if skill_lower in problem_statement.challenge.lower():
            relevance_score += 15
        if skill_lower in problem_statement.desired_outcome.lower():
            relevance_score += 15
        
        return min(100, relevance_score)
    
    def _calculate_industry_demand_score(self, skill: str, industry_context: IndustryContext) -> int:
        """Calculate industry demand for the skill"""
        # Industry-specific skill demand scores
        industry_demand = {
            IndustryContext.TECHNOLOGY: {
                'python': 95, 'sql': 90, 'javascript': 85, 'aws': 90, 'devops': 85,
                'machine learning': 80, 'data analysis': 85, 'cloud': 90
            },
            IndustryContext.FINANCE: {
                'financial modeling': 95, 'excel': 90, 'sql': 85, 'risk management': 90,
                'accounting': 85, 'compliance': 90, 'data analysis': 80
            },
            IndustryContext.HEALTHCARE: {
                'healthcare analytics': 95, 'hipaa': 90, 'clinical data': 85,
                'data analysis': 80, 'compliance': 90, 'patient safety': 85
            }
        }
        
        skill_lower = skill.lower()
        industry_scores = industry_demand.get(industry_context, {})
        
        # Check for exact matches
        if skill_lower in industry_scores:
            return industry_scores[skill_lower]
        
        # Check for partial matches
        for key, score in industry_scores.items():
            if key in skill_lower or skill_lower in key:
                return score
        
        # Default score based on industry
        return 70 if industry_context == IndustryContext.TECHNOLOGY else 60
    
    def _calculate_career_impact_score(self, skill: str, company_stage: CompanyStage) -> int:
        """Calculate career impact potential of the skill"""
        # Skills that are more valuable at different company stages
        stage_impact = {
            CompanyStage.STARTUP: {
                'python': 90, 'javascript': 85, 'product management': 90, 'growth': 85,
                'marketing': 80, 'sales': 80, 'leadership': 85
            },
            CompanyStage.SCALE_UP: {
                'data analysis': 90, 'process improvement': 85, 'team leadership': 90,
                'project management': 85, 'automation': 80, 'strategy': 85
            },
            CompanyStage.ENTERPRISE: {
                'change management': 90, 'compliance': 85, 'risk management': 90,
                'strategic planning': 90, 'executive leadership': 95, 'governance': 85
            }
        }
        
        skill_lower = skill.lower()
        stage_scores = stage_impact.get(company_stage, {})
        
        # Check for exact matches
        if skill_lower in stage_scores:
            return stage_scores[skill_lower]
        
        # Check for partial matches
        for key, score in stage_scores.items():
            if key in skill_lower or skill_lower in key:
                return score
        
        # Default score
        return 60
    
    def _calculate_learning_roi_score(self, skill: str, user_skills: List[str]) -> int:
        """Calculate learning ROI based on time investment vs. career benefit"""
        skill_lower = skill.lower()
        
        # Check if user already has this skill
        if skill_lower in [s.lower() for s in user_skills]:
            return 20  # Low ROI if already have it
        
        # Skill difficulty and time to learn
        difficulty_scores = {
            'excel': 90, 'power bi': 85, 'tableau': 80, 'sql': 75,
            'python': 70, 'javascript': 65, 'aws': 60, 'machine learning': 50,
            'leadership': 60, 'project management': 70, 'change management': 65
        }
        
        # Find best match for difficulty
        for key, score in difficulty_scores.items():
            if key in skill_lower or skill_lower in key:
                return score
        
        # Default score
        return 70
    
    def _calculate_competitive_advantage_score(self, skill: str, problem_analysis: ProblemAnalysis) -> int:
        """Calculate competitive advantage of having this skill"""
        skill_lower = skill.lower()
        
        # Skills that are less common but high-value
        high_value_skills = {
            'machine learning': 90, 'ai': 85, 'blockchain': 80, 'cybersecurity': 85,
            'cloud architecture': 80, 'data science': 85, 'product management': 80,
            'change management': 75, 'strategic planning': 80
        }
        
        # Check for high-value skills
        for key, score in high_value_skills.items():
            if key in skill_lower or skill_lower in key:
                return score
        
        # Industry-specific advantage
        industry = problem_analysis.industry_context.value
        if industry == 'technology' and any(tech in skill_lower for tech in ['python', 'aws', 'devops']):
            return 80
        elif industry == 'finance' and any(fin in skill_lower for fin in ['financial modeling', 'risk', 'compliance']):
            return 80
        elif industry == 'healthcare' and any(health in skill_lower for health in ['healthcare', 'clinical', 'hipaa']):
            return 80
        
        # Default score
        return 60
    
    def _get_related_concepts(self, skill: str) -> List[str]:
        """Get related concepts for a skill to improve matching"""
        concept_map = {
            'python': ['programming', 'coding', 'automation', 'data analysis'],
            'sql': ['database', 'query', 'data', 'analytics'],
            'excel': ['spreadsheet', 'data', 'analysis', 'reporting'],
            'leadership': ['management', 'team', 'strategy', 'vision'],
            'project management': ['planning', 'coordination', 'delivery', 'timeline']
        }
        
        skill_lower = skill.lower()
        for key, concepts in concept_map.items():
            if key in skill_lower or skill_lower in key:
                return concepts
        
        return []
    
    def _get_skill_description(self, skill: str) -> str:
        """Get description for a skill"""
        descriptions = {
            'python': 'Programming language for data analysis, automation, and web development',
            'sql': 'Database query language for data extraction and analysis',
            'excel': 'Spreadsheet software for data analysis and reporting',
            'leadership': 'Ability to guide and inspire teams toward common goals',
            'project management': 'Planning and execution of projects within scope, time, and budget'
        }
        
        skill_lower = skill.lower()
        for key, desc in descriptions.items():
            if key in skill_lower or skill_lower in key:
                return desc
        
        return f"Professional skill in {skill}"
    
    def _generate_skill_reasoning(self, skill: str, problem_analysis: ProblemAnalysis) -> str:
        """Generate reasoning for why this skill is recommended"""
        reasoning_parts = []
        
        # Problem relevance
        if any(skill.lower() in p.get('sentence', '').lower() for p in problem_analysis.primary_problems):
            reasoning_parts.append("Directly addresses primary business problems")
        
        # Industry alignment
        industry = problem_analysis.industry_context.value
        reasoning_parts.append(f"High demand in {industry} industry")
        
        # Company stage alignment
        stage = problem_analysis.company_stage.value
        reasoning_parts.append(f"Valuable for {stage} companies")
        
        return "; ".join(reasoning_parts)
    
    def _estimate_skill_acquisition_time(self, skill: str) -> str:
        """Estimate time to acquire skill"""
        time_estimates = {
            'excel': '2-4 weeks',
            'sql': '1-2 months',
            'python': '3-6 months',
            'leadership': '6-12 months',
            'project management': '2-4 months'
        }
        
        skill_lower = skill.lower()
        for key, time in time_estimates.items():
            if key in skill_lower or skill_lower in key:
                return time
        
        return '2-6 months'
    
    def _estimate_skill_cost(self, skill: str) -> str:
        """Estimate cost to acquire skill"""
        cost_estimates = {
            'excel': '$50-200 (online courses)',
            'sql': '$100-500 (courses + practice)',
            'python': '$200-1000 (comprehensive training)',
            'leadership': '$500-2000 (programs + coaching)',
            'project management': '$300-800 (certification prep)'
        }
        
        skill_lower = skill.lower()
        for key, cost in cost_estimates.items():
            if key in skill_lower or skill_lower in key:
                return cost
        
        return '$200-800'
    
    def _estimate_salary_impact(self, skill: str) -> str:
        """Estimate salary impact of acquiring skill"""
        impact_estimates = {
            'python': '+$10,000-25,000',
            'sql': '+$5,000-15,000',
            'excel': '+$3,000-8,000',
            'leadership': '+$15,000-40,000',
            'project management': '+$8,000-20,000'
        }
        
        skill_lower = skill.lower()
        for key, impact in impact_estimates.items():
            if key in skill_lower or skill_lower in key:
                return impact
        
        return '+$5,000-15,000'
    
    def _generate_certification_recommendations(self, problem_analysis: ProblemAnalysis, 
                                              solution_categories: List[str], 
                                              user_profile: Optional[Dict] = None) -> List[SolutionRecommendation]:
        """Generate certification recommendations"""
        # Similar implementation to skills but for certifications
        recommendations = []
        
        # Collect relevant certifications
        all_certifications = set()
        for category in solution_categories:
            if category in ['automation', 'data_analysis', 'system_integration']:
                all_certifications.update(self.solution_frameworks['technical_solutions'].get(category, {}).get('certifications', []))
            elif category in ['process_improvement', 'change_management', 'leadership']:
                all_certifications.update(self.solution_frameworks['strategic_solutions'].get(category, {}).get('certifications', []))
            elif category in ['finance', 'healthcare', 'technology']:
                all_certifications.update(self.solution_frameworks['industry_specific'].get(category, {}).get('certifications', []))
        
        # Score each certification
        for cert in all_certifications:
            recommendation = self._score_certification(cert, problem_analysis)
            if recommendation:
                recommendations.append(recommendation)
        
        # Sort by total score
        recommendations.sort(key=lambda x: x.total_score, reverse=True)
        return recommendations
    
    def _score_certification(self, certification: str, problem_analysis: ProblemAnalysis) -> Optional[SolutionRecommendation]:
        """Score a specific certification"""
        # Similar scoring logic to skills but adjusted for certifications
        relevance_score = self._calculate_relevance_score(certification, problem_analysis)
        industry_demand_score = self._calculate_industry_demand_score(certification, problem_analysis.industry_context)
        career_impact_score = self._calculate_career_impact_score(certification, problem_analysis.company_stage)
        learning_roi_score = 70  # Certifications generally have good ROI
        competitive_advantage_score = self._calculate_competitive_advantage_score(certification, problem_analysis)
        
        total_score = int(
            relevance_score * 0.30 +
            industry_demand_score * 0.25 +
            career_impact_score * 0.25 +
            learning_roi_score * 0.10 +
            competitive_advantage_score * 0.10
        )
        
        if total_score < 30:
            return None
        
        return SolutionRecommendation(
            recommendation_type=RecommendationType.CERTIFICATION,
            name=certification,
            description=f"Professional certification in {certification}",
            relevance_score=relevance_score,
            industry_demand_score=industry_demand_score,
            career_impact_score=career_impact_score,
            learning_roi_score=learning_roi_score,
            competitive_advantage_score=competitive_advantage_score,
            total_score=total_score,
            rank=0,
            reasoning=f"Industry-recognized certification in {certification}",
            time_to_acquire="1-3 months",
            cost_estimate="$200-1000",
            salary_impact="+$5,000-20,000"
        )
    
    def _generate_title_recommendations(self, problem_analysis: ProblemAnalysis, 
                                      solution_categories: List[str], 
                                      user_profile: Optional[Dict] = None) -> List[SolutionRecommendation]:
        """Generate title recommendations"""
        # Similar implementation to skills but for titles
        recommendations = []
        
        # Collect relevant titles
        all_titles = set()
        for category in solution_categories:
            if category in ['automation', 'data_analysis', 'system_integration']:
                all_titles.update(self.solution_frameworks['technical_solutions'].get(category, {}).get('titles', []))
            elif category in ['process_improvement', 'change_management', 'leadership']:
                all_titles.update(self.solution_frameworks['strategic_solutions'].get(category, {}).get('titles', []))
            elif category in ['finance', 'healthcare', 'technology']:
                all_titles.update(self.solution_frameworks['industry_specific'].get(category, {}).get('titles', []))
        
        # Score each title
        for title in all_titles:
            recommendation = self._score_title(title, problem_analysis)
            if recommendation:
                recommendations.append(recommendation)
        
        # Sort by total score
        recommendations.sort(key=lambda x: x.total_score, reverse=True)
        return recommendations
    
    def _score_title(self, title: str, problem_analysis: ProblemAnalysis) -> Optional[SolutionRecommendation]:
        """Score a specific title"""
        # Similar scoring logic to skills but adjusted for titles
        relevance_score = self._calculate_relevance_score(title, problem_analysis)
        industry_demand_score = self._calculate_industry_demand_score(title, problem_analysis.industry_context)
        career_impact_score = self._calculate_career_impact_score(title, problem_analysis.company_stage)
        learning_roi_score = 80  # Titles have high career impact
        competitive_advantage_score = self._calculate_competitive_advantage_score(title, problem_analysis)
        
        total_score = int(
            relevance_score * 0.30 +
            industry_demand_score * 0.25 +
            career_impact_score * 0.25 +
            learning_roi_score * 0.10 +
            competitive_advantage_score * 0.10
        )
        
        if total_score < 30:
            return None
        
        return SolutionRecommendation(
            recommendation_type=RecommendationType.TITLE,
            name=title,
            description=f"Professional title: {title}",
            relevance_score=relevance_score,
            industry_demand_score=industry_demand_score,
            career_impact_score=career_impact_score,
            learning_roi_score=learning_roi_score,
            competitive_advantage_score=competitive_advantage_score,
            total_score=total_score,
            rank=0,
            reasoning=f"Title that positions you as a {title}",
            time_to_acquire="Immediate (resume positioning)",
            cost_estimate="$0 (resume update)",
            salary_impact="+$10,000-30,000"
        )
    
    def _create_action_plan(self, skills: List[SolutionRecommendation], 
                          certifications: List[SolutionRecommendation], 
                          titles: List[SolutionRecommendation]) -> Dict[str, Any]:
        """Create actionable plan for skill development and career positioning"""
        
        # Prioritize by total score
        all_recommendations = skills + certifications + titles
        all_recommendations.sort(key=lambda x: x.total_score, reverse=True)
        
        # Create 30-60-90 day plan
        plan = {
            'immediate_actions': [],  # 0-30 days
            'short_term_goals': [],  # 30-60 days
            'medium_term_goals': [],  # 60-90 days
            'long_term_goals': [],  # 90+ days
            'total_investment': 0,
            'expected_salary_impact': 0
        }
        
        # Categorize recommendations by timeline
        for i, rec in enumerate(all_recommendations[:10]):  # Top 10 recommendations
            if i < 3:
                plan['immediate_actions'].append({
                    'action': f"Start learning {rec.name}",
                    'timeline': rec.time_to_acquire,
                    'cost': rec.cost_estimate,
                    'priority': 'High'
                })
            elif i < 6:
                plan['short_term_goals'].append({
                    'action': f"Complete {rec.name}",
                    'timeline': rec.time_to_acquire,
                    'cost': rec.cost_estimate,
                    'priority': 'Medium'
                })
            elif i < 8:
                plan['medium_term_goals'].append({
                    'action': f"Master {rec.name}",
                    'timeline': rec.time_to_acquire,
                    'cost': rec.cost_estimate,
                    'priority': 'Medium'
                })
            else:
                plan['long_term_goals'].append({
                    'action': f"Advanced {rec.name}",
                    'timeline': rec.time_to_acquire,
                    'cost': rec.cost_estimate,
                    'priority': 'Low'
                })
        
        # Calculate total investment and expected impact
        total_investment = 0
        for rec in all_recommendations[:5]:  # Top 5
            if '$' in rec.cost_estimate and rec.cost_estimate != '$0 (resume update)':
                try:
                    cost_str = rec.cost_estimate.split('$')[1].split('-')[0]
                    total_investment += int(cost_str)
                except (ValueError, IndexError):
                    continue
        
        plan['total_investment'] = total_investment
        
        expected_impact = 0
        for rec in all_recommendations[:5]:  # Top 5
            if '+$' in rec.salary_impact:
                try:
                    impact_str = rec.salary_impact.split('+$')[1].split('-')[0]
                    expected_impact += int(impact_str)
                except (ValueError, IndexError):
                    continue
        
        plan['expected_salary_impact'] = expected_impact
        
        return plan
    
    def _create_fallback_analysis(self, problem_analysis: ProblemAnalysis) -> SolutionAnalysis:
        """Create fallback analysis when solution mapping fails"""
        return SolutionAnalysis(
            problem_analysis=problem_analysis,
            top_skills=[],
            top_certifications=[],
            optimal_titles=[],
            action_plan={},
            generated_at=datetime.now()
        )

# Example usage and testing
if __name__ == "__main__":
    # Test the solution mapper
    mapper = ProblemSolutionMapper()
    
    # Create a sample problem analysis
    from .job_problem_extractor import ProblemStatement, ProblemAnalysis, IndustryContext, CompanyStage
    
    sample_problem_analysis = ProblemAnalysis(
        problem_statement=ProblemStatement(
            context="TechStartup is a technology scale-up",
            challenge="inefficient data analysis processes",
            impact="delayed decision making",
            desired_outcome="real-time insights",
            timeframe="3 months",
            constraints=["limited budget", "small team"]
        ),
        primary_problems=[{
            'sentence': 'We need to improve our data analysis processes',
            'indicators': ['need', 'improve'],
            'category': 'operational_challenges',
            'confidence': 0.8
        }],
        secondary_problems=[],
        tertiary_problems=[],
        industry_context=IndustryContext.TECHNOLOGY,
        company_stage=CompanyStage.SCALE_UP,
        confidence_score=0.8,
        extracted_at=datetime.now()
    )
    
    solution_analysis = mapper.map_solutions(sample_problem_analysis)
    
    print("Solution Analysis Results:")
    print(f"Top Skills: {len(solution_analysis.top_skills)}")
    for skill in solution_analysis.top_skills[:3]:
        print(f"  - {skill.name}: {skill.total_score}% ({skill.reasoning})")
    
    print(f"Top Certifications: {len(solution_analysis.top_certifications)}")
    for cert in solution_analysis.top_certifications[:3]:
        print(f"  - {cert.name}: {cert.total_score}%")
    
    print(f"Optimal Titles: {len(solution_analysis.optimal_titles)}")
    for title in solution_analysis.optimal_titles[:3]:
        print(f"  - {title.name}: {title.total_score}%")
