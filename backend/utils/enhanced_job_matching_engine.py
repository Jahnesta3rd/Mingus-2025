#!/usr/bin/env python3
"""
Enhanced Job Matching Engine - Integrates Problem-Solution Analysis with Existing Job Matching
Replaces basic job matching with sophisticated problem-solution positioning methodology
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

from .job_problem_extractor import JobProblemExtractor, ProblemAnalysis, IndustryContext, CompanyStage
from .problem_solution_mapper import ProblemSolutionMapper, SolutionAnalysis, SolutionRecommendation
from .income_boost_job_matcher import IncomeBoostJobMatcher, SearchCriteria, JobOpportunity
from .three_tier_job_selector import ThreeTierJobSelector, JobTier, TieredJobRecommendation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedJobMatch:
    """Enhanced job match with problem-solution analysis"""
    job_opportunity: JobOpportunity
    problem_analysis: ProblemAnalysis
    solution_analysis: SolutionAnalysis
    enhanced_score: float
    problem_solution_alignment: float
    positioning_strategy: Dict[str, Any]
    application_insights: Dict[str, Any]

@dataclass
class EnhancedMatchingResult:
    """Complete enhanced matching result"""
    job_matches: List[EnhancedJobMatch]
    problem_solution_summary: Dict[str, Any]
    career_positioning_plan: Dict[str, Any]
    success_probability: float
    generated_at: datetime

class EnhancedJobMatchingEngine:
    """
    Enhanced job matching engine that integrates problem-solution analysis
    with existing job matching to provide strategic career positioning
    """
    
    def __init__(self, db_path: str = "backend/mingus_recommendations.db", openai_api_key: Optional[str] = None):
        """Initialize the enhanced matching engine"""
        self.db_path = db_path
        
        # Initialize components
        self.problem_extractor = JobProblemExtractor(openai_api_key)
        self.solution_mapper = ProblemSolutionMapper(openai_api_key)
        self.income_matcher = IncomeBoostJobMatcher(db_path)
        self.three_tier_selector = ThreeTierJobSelector(db_path)
        
        logger.info("Enhanced Job Matching Engine initialized successfully")
    
    async def enhanced_job_matching(self, job_description: str, user_profile: Dict[str, Any], 
                                  search_criteria: Optional[SearchCriteria] = None) -> EnhancedMatchingResult:
        """
        Perform enhanced job matching with problem-solution analysis
        
        Args:
            job_description: Job description to analyze
            user_profile: User's profile and preferences
            search_criteria: Optional search criteria for job matching
            
        Returns:
            EnhancedMatchingResult with comprehensive analysis
        """
        try:
            logger.info("Starting enhanced job matching with problem-solution analysis")
            
            # Phase 1: Problem Extraction
            problem_analysis = self.problem_extractor.extract_problems(job_description)
            logger.info(f"Extracted {len(problem_analysis.primary_problems)} primary problems")
            
            # Phase 2: Solution Mapping
            solution_analysis = self.solution_mapper.map_solutions(problem_analysis, user_profile)
            logger.info(f"Generated {len(solution_analysis.top_skills)} skill recommendations")
            
            # Phase 3: Enhanced Job Search
            if not search_criteria:
                search_criteria = self._create_search_criteria_from_profile(user_profile)
            
            # Get job opportunities using existing system
            job_opportunities = await self.income_matcher.salary_focused_search(search_criteria)
            logger.info(f"Found {len(job_opportunities)} job opportunities")
            
            # Phase 4: Enhanced Scoring and Matching
            enhanced_matches = []
            for job in job_opportunities[:20]:  # Limit to top 20 for performance
                enhanced_match = await self._create_enhanced_match(
                    job, problem_analysis, solution_analysis, user_profile
                )
                if enhanced_match:
                    enhanced_matches.append(enhanced_match)
            
            # Sort by enhanced score
            enhanced_matches.sort(key=lambda x: x.enhanced_score, reverse=True)
            
            # Phase 5: Generate Career Positioning Plan
            career_plan = self._generate_career_positioning_plan(
                problem_analysis, solution_analysis, enhanced_matches
            )
            
            # Phase 6: Calculate Success Probability
            success_probability = self._calculate_success_probability(enhanced_matches, user_profile)
            
            return EnhancedMatchingResult(
                job_matches=enhanced_matches[:10],  # Top 10 matches
                problem_solution_summary=self._create_problem_solution_summary(problem_analysis, solution_analysis),
                career_positioning_plan=career_plan,
                success_probability=success_probability,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in enhanced job matching: {str(e)}")
            return self._create_fallback_result(job_description, user_profile)
    
    async def _create_enhanced_match(self, job: JobOpportunity, problem_analysis: ProblemAnalysis,
                                   solution_analysis: SolutionAnalysis, user_profile: Dict[str, Any]) -> Optional[EnhancedJobMatch]:
        """Create enhanced job match with problem-solution analysis"""
        try:
            # Calculate problem-solution alignment score
            problem_solution_alignment = self._calculate_problem_solution_alignment(
                job, problem_analysis, solution_analysis, user_profile
            )
            
            # Calculate enhanced overall score
            enhanced_score = self._calculate_enhanced_score(job, problem_solution_alignment)
            
            # Generate positioning strategy
            positioning_strategy = self._generate_positioning_strategy(
                job, problem_analysis, solution_analysis, user_profile
            )
            
            # Generate application insights
            application_insights = self._generate_application_insights(
                job, problem_analysis, solution_analysis, user_profile
            )
            
            return EnhancedJobMatch(
                job_opportunity=job,
                problem_analysis=problem_analysis,
                solution_analysis=solution_analysis,
                enhanced_score=enhanced_score,
                problem_solution_alignment=problem_solution_alignment,
                positioning_strategy=positioning_strategy,
                application_insights=application_insights
            )
            
        except Exception as e:
            logger.error(f"Error creating enhanced match: {str(e)}")
            return None
    
    def _calculate_problem_solution_alignment(self, job: JobOpportunity, problem_analysis: ProblemAnalysis,
                                            solution_analysis: SolutionAnalysis, user_profile: Dict[str, Any]) -> float:
        """Calculate how well the job aligns with problem-solution analysis"""
        alignment_score = 0.0
        
        # Check job title alignment with problem-solving focus
        job_title_lower = job.title.lower()
        problem_keywords = []
        for problem in problem_analysis.primary_problems:
            problem_keywords.extend(problem.get('indicators', []))
        
        title_alignment = sum(1 for keyword in problem_keywords if keyword in job_title_lower)
        alignment_score += min(20, title_alignment * 5)  # Max 20 points
        
        # Check job description alignment with problems
        job_desc_lower = job.description.lower()
        problem_sentence_alignment = 0
        for problem in problem_analysis.primary_problems:
            problem_sentence = problem.get('sentence', '').lower()
            if any(word in job_desc_lower for word in problem_sentence.split()):
                problem_sentence_alignment += 1
        
        alignment_score += min(30, problem_sentence_alignment * 10)  # Max 30 points
        
        # Check solution skills alignment
        user_skills = user_profile.get('skills', [])
        recommended_skills = [skill.name for skill in solution_analysis.top_skills]
        
        skill_alignment = len(set(user_skills) & set(recommended_skills))
        alignment_score += min(25, skill_alignment * 5)  # Max 25 points
        
        # Check industry context alignment
        if problem_analysis.industry_context.value in job_desc_lower:
            alignment_score += 15
        
        # Check company stage alignment
        company_stage_indicators = {
            CompanyStage.STARTUP: ['startup', 'early', 'innovative', 'disruptive'],
            CompanyStage.SCALE_UP: ['growing', 'scaling', 'expanding', 'established'],
            CompanyStage.ENTERPRISE: ['enterprise', 'fortune', 'global', 'corporate']
        }
        
        stage_indicators = company_stage_indicators.get(problem_analysis.company_stage, [])
        if any(indicator in job_desc_lower for indicator in stage_indicators):
            alignment_score += 10
        
        return min(100, alignment_score)
    
    def _calculate_enhanced_score(self, job: JobOpportunity, problem_solution_alignment: float) -> float:
        """Calculate enhanced overall score incorporating problem-solution alignment"""
        
        # Get existing scores from the job
        existing_scores = {
            'salary_score': getattr(job, 'salary_increase_potential', 50),
            'advancement_score': getattr(job, 'career_advancement_score', 50),
            'diversity_score': getattr(job, 'diversity_score', 50),
            'culture_score': getattr(job, 'work_life_balance_score', 50)
        }
        
        # Apply original weights (from existing system)
        original_score = (
            existing_scores['salary_score'] * 0.40 +
            existing_scores['advancement_score'] * 0.25 +
            existing_scores['diversity_score'] * 0.20 +
            existing_scores['culture_score'] * 0.15
        )
        
        # Add problem-solution alignment with 15% weight
        enhanced_score = (original_score * 0.85) + (problem_solution_alignment * 0.15)
        
        return min(100, enhanced_score)
    
    def _generate_positioning_strategy(self, job: JobOpportunity, problem_analysis: ProblemAnalysis,
                                     solution_analysis: SolutionAnalysis, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic positioning strategy for the job application"""
        
        strategy = {
            'problem_focus': problem_analysis.problem_statement.challenge,
            'solution_approach': [],
            'key_skills_to_highlight': [],
            'value_proposition': '',
            'interview_talking_points': [],
            'resume_keywords': []
        }
        
        # Identify key problems to address
        primary_problems = [p.get('sentence', '') for p in problem_analysis.primary_problems[:3]]
        strategy['problem_focus'] = primary_problems[0] if primary_problems else problem_analysis.problem_statement.challenge
        
        # Identify solution approach based on top skills
        top_skills = solution_analysis.top_skills[:3]
        for skill in top_skills:
            strategy['solution_approach'].append(f"Leverage {skill.name} to address {strategy['problem_focus']}")
            strategy['key_skills_to_highlight'].append(skill.name)
        
        # Generate value proposition
        industry = problem_analysis.industry_context.value
        stage = problem_analysis.company_stage.value
        strategy['value_proposition'] = f"As a {job.title} with expertise in {', '.join([s.name for s in top_skills[:2]])}, I can help {industry} {stage} companies solve {strategy['problem_focus']} to achieve {problem_analysis.problem_statement.desired_outcome}"
        
        # Generate interview talking points
        for i, problem in enumerate(problem_analysis.primary_problems[:3]):
            strategy['interview_talking_points'].append({
                'problem': problem.get('sentence', ''),
                'solution': f"Based on my experience with {top_skills[i].name if i < len(top_skills) else 'relevant skills'}, I would approach this by...",
                'impact': f"This would help achieve {problem_analysis.problem_statement.desired_outcome}"
            })
        
        # Generate resume keywords
        strategy['resume_keywords'] = [skill.name for skill in top_skills] + problem_keywords
        
        return strategy
    
    def _generate_application_insights(self, job: JobOpportunity, problem_analysis: ProblemAnalysis,
                                     solution_analysis: SolutionAnalysis, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific application insights and recommendations"""
        
        insights = {
            'application_strength': 0,
            'skill_gaps': [],
            'immediate_actions': [],
            'salary_negotiation_points': [],
            'company_research_focus': [],
            'cover_letter_angles': []
        }
        
        # Calculate application strength
        user_skills = user_profile.get('skills', [])
        recommended_skills = [skill.name for skill in solution_analysis.top_skills]
        skill_match_ratio = len(set(user_skills) & set(recommended_skills)) / len(recommended_skills) if recommended_skills else 0
        
        insights['application_strength'] = int(skill_match_ratio * 100)
        
        # Identify skill gaps
        for skill in solution_analysis.top_skills[:5]:
            if skill.name not in user_skills:
                insights['skill_gaps'].append({
                    'skill': skill.name,
                    'priority': 'High' if skill.total_score >= 80 else 'Medium',
                    'time_to_learn': skill.time_to_acquire,
                    'cost': skill.cost_estimate
                })
        
        # Generate immediate actions
        insights['immediate_actions'] = [
            f"Update resume to highlight {skill.name}" for skill in solution_analysis.top_skills[:3]
        ] + [
            f"Research {problem_analysis.industry_context.value} industry trends",
            f"Prepare examples of solving {problem_analysis.problem_statement.challenge}"
        ]
        
        # Generate salary negotiation points
        insights['salary_negotiation_points'] = [
            f"Problem-solving expertise in {problem_analysis.problem_statement.challenge}",
            f"Industry experience in {problem_analysis.industry_context.value}",
            f"Track record of achieving {problem_analysis.problem_statement.desired_outcome}"
        ]
        
        # Generate company research focus
        insights['company_research_focus'] = [
            f"How they currently handle {problem_analysis.problem_statement.challenge}",
            f"Their approach to {problem_analysis.problem_statement.desired_outcome}",
            f"Recent initiatives in {problem_analysis.industry_context.value} sector"
        ]
        
        # Generate cover letter angles
        insights['cover_letter_angles'] = [
            f"Addressing {problem_analysis.problem_statement.challenge} with {solution_analysis.top_skills[0].name}",
            f"Helping achieve {problem_analysis.problem_statement.desired_outcome}",
            f"Bringing {problem_analysis.industry_context.value} expertise to solve their challenges"
        ]
        
        return insights
    
    def _create_search_criteria_from_profile(self, user_profile: Dict[str, Any]) -> SearchCriteria:
        """Create search criteria from user profile"""
        # This would extract criteria from user profile
        # For now, return a basic criteria
        return SearchCriteria(
            current_salary=user_profile.get('current_salary', 75000),
            target_salary_increase=0.20,
            career_field=user_profile.get('career_field', 'TECHNOLOGY'),
            experience_level=user_profile.get('experience_level', 'MID'),
            preferred_msas=user_profile.get('preferred_locations', ['New York']),
            remote_ok=user_profile.get('remote_ok', True),
            company_size_preference=user_profile.get('company_size', None),
            max_commute_time=30,  # Default 30 minutes
            must_have_benefits=[],  # Empty list
            industry_preference=None,  # No preference
            equity_required=False  # Not required
        )
    
    def _generate_career_positioning_plan(self, problem_analysis: ProblemAnalysis, 
                                        solution_analysis: SolutionAnalysis, 
                                        enhanced_matches: List[EnhancedJobMatch]) -> Dict[str, Any]:
        """Generate comprehensive career positioning plan"""
        
        plan = {
            'problem_solving_focus': problem_analysis.problem_statement.challenge,
            'solution_roadmap': [],
            'skill_development_plan': [],
            'networking_strategy': [],
            'portfolio_projects': [],
            'interview_preparation': []
        }
        
        # Solution roadmap
        for skill in solution_analysis.top_skills[:5]:
            plan['solution_roadmap'].append({
                'skill': skill.name,
                'timeline': skill.time_to_acquire,
                'cost': skill.cost_estimate,
                'expected_impact': skill.salary_impact
            })
        
        # Skill development plan
        plan['skill_development_plan'] = solution_analysis.action_plan
        
        # Networking strategy
        industry = problem_analysis.industry_context.value
        plan['networking_strategy'] = [
            f"Join {industry} professional associations",
            f"Attend {industry} conferences and meetups",
            f"Connect with {industry} professionals on LinkedIn",
            f"Participate in {industry} online communities"
        ]
        
        # Portfolio projects
        plan['portfolio_projects'] = [
            f"Build a project solving {problem_analysis.problem_statement.challenge}",
            f"Create case study showing {problem_analysis.problem_statement.desired_outcome}",
            f"Develop {solution_analysis.top_skills[0].name} demonstration"
        ]
        
        # Interview preparation
        plan['interview_preparation'] = [
            f"Prepare STAR stories about solving {problem_analysis.problem_statement.challenge}",
            f"Research company's approach to {problem_analysis.problem_statement.desired_outcome}",
            f"Practice explaining {solution_analysis.top_skills[0].name} solutions"
        ]
        
        return plan
    
    def _calculate_success_probability(self, enhanced_matches: List[EnhancedJobMatch], 
                                     user_profile: Dict[str, Any]) -> float:
        """Calculate overall success probability for job applications"""
        if not enhanced_matches:
            return 0.0
        
        # Calculate average enhanced score
        avg_enhanced_score = sum(match.enhanced_score for match in enhanced_matches) / len(enhanced_matches)
        
        # Calculate average problem-solution alignment
        avg_alignment = sum(match.problem_solution_alignment for match in enhanced_matches) / len(enhanced_matches)
        
        # Calculate user readiness score
        user_skills = user_profile.get('skills', [])
        recommended_skills = []
        for match in enhanced_matches[:3]:  # Top 3 matches
            recommended_skills.extend([skill.name for skill in match.solution_analysis.top_skills[:3]])
        
        skill_readiness = len(set(user_skills) & set(recommended_skills)) / len(set(recommended_skills)) if recommended_skills else 0
        
        # Combine factors
        success_probability = (
            avg_enhanced_score * 0.4 +
            avg_alignment * 0.3 +
            skill_readiness * 100 * 0.3
        ) / 100
        
        return min(1.0, success_probability)
    
    def _create_problem_solution_summary(self, problem_analysis: ProblemAnalysis, 
                                       solution_analysis: SolutionAnalysis) -> Dict[str, Any]:
        """Create summary of problem-solution analysis"""
        return {
            'problem_statement': {
                'context': problem_analysis.problem_statement.context,
                'challenge': problem_analysis.problem_statement.challenge,
                'impact': problem_analysis.problem_statement.impact,
                'desired_outcome': problem_analysis.problem_statement.desired_outcome
            },
            'industry_context': problem_analysis.industry_context.value,
            'company_stage': problem_analysis.company_stage.value,
            'confidence_score': problem_analysis.confidence_score,
            'top_solutions': {
                'skills': [{'name': s.name, 'score': s.total_score} for s in solution_analysis.top_skills[:3]],
                'certifications': [{'name': c.name, 'score': c.total_score} for c in solution_analysis.top_certifications[:3]],
                'titles': [{'name': t.name, 'score': t.total_score} for t in solution_analysis.optimal_titles[:3]]
            }
        }
    
    def _create_fallback_result(self, job_description: str, user_profile: Dict[str, Any]) -> EnhancedMatchingResult:
        """Create fallback result when enhanced matching fails"""
        return EnhancedMatchingResult(
            job_matches=[],
            problem_solution_summary={},
            career_positioning_plan={},
            success_probability=0.0,
            generated_at=datetime.now()
        )

# Example usage and testing
if __name__ == "__main__":
    # Test the enhanced matching engine
    engine = EnhancedJobMatchingEngine()
    
    sample_job_description = """
    We're looking for a Senior Data Analyst to help us understand customer behavior 
    and improve campaign performance. You'll work with large datasets, create dashboards, 
    and provide insights to drive marketing strategy. The role involves challenging 
    data integration problems and requires someone who can optimize our reporting processes.
    """
    
    sample_user_profile = {
        'skills': ['Python', 'SQL', 'Excel', 'Data Analysis'],
        'current_salary': 75000,
        'career_field': 'TECHNOLOGY',
        'experience_level': 'MID',
        'preferred_locations': ['New York', 'San Francisco'],
        'remote_ok': True
    }
    
    # Run enhanced matching
    result = asyncio.run(engine.enhanced_job_matching(sample_job_description, sample_user_profile))
    
    print("Enhanced Job Matching Results:")
    print(f"Job Matches: {len(result.job_matches)}")
    print(f"Success Probability: {result.success_probability:.2%}")
    print(f"Problem-Solution Summary: {result.problem_solution_summary}")
    print(f"Career Positioning Plan: {len(result.career_positioning_plan)} items")
