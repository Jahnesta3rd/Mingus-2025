#!/usr/bin/env python3
"""
Enhanced Job Matching API Endpoints
Replaces basic job matching with problem-solution analysis methodology
"""

from flask import Blueprint, request, jsonify
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.enhanced_job_matching_engine import EnhancedJobMatchingEngine
from ..utils.job_problem_extractor import JobProblemExtractor
from ..utils.problem_solution_mapper import ProblemSolutionMapper
from ..utils.income_boost_job_matcher import SearchCriteria, CareerField, ExperienceLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
enhanced_job_matching_api = Blueprint('enhanced_job_matching_api', __name__)

# Initialize enhanced matching engine
enhanced_engine = EnhancedJobMatchingEngine()

@enhanced_job_matching_api.route('/analyze-job-problems', methods=['POST'])
def analyze_job_problems():
    """
    Analyze job description to extract business problems and create problem statement
    
    Request Body:
    {
        "job_description": "Job description text",
        "openai_api_key": "optional_api_key"
    }
    
    Returns:
    {
        "problem_analysis": {
            "problem_statement": {...},
            "primary_problems": [...],
            "secondary_problems": [...],
            "tertiary_problems": [...],
            "industry_context": "...",
            "company_stage": "...",
            "confidence_score": 0.85
        },
        "success": true
    }
    """
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        openai_api_key = data.get('openai_api_key')
        
        if not job_description:
            return jsonify({
                'error': 'Job description is required',
                'success': False
            }), 400
        
        # Initialize problem extractor with optional API key
        extractor = JobProblemExtractor(openai_api_key)
        
        # Extract problems
        problem_analysis = extractor.extract_problems(job_description)
        
        # Convert to JSON-serializable format
        result = {
            'problem_analysis': {
                'problem_statement': {
                    'context': problem_analysis.problem_statement.context,
                    'challenge': problem_analysis.problem_statement.challenge,
                    'impact': problem_analysis.problem_statement.impact,
                    'desired_outcome': problem_analysis.problem_statement.desired_outcome,
                    'timeframe': problem_analysis.problem_statement.timeframe,
                    'constraints': problem_analysis.problem_statement.constraints
                },
                'primary_problems': problem_analysis.primary_problems,
                'secondary_problems': problem_analysis.secondary_problems,
                'tertiary_problems': problem_analysis.tertiary_problems,
                'industry_context': problem_analysis.industry_context.value,
                'company_stage': problem_analysis.company_stage.value,
                'confidence_score': problem_analysis.confidence_score,
                'extracted_at': problem_analysis.extracted_at.isoformat()
            },
            'success': True
        }
        
        logger.info(f"Successfully analyzed job problems with confidence {problem_analysis.confidence_score:.2f}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analyzing job problems: {str(e)}")
        return jsonify({
            'error': f'Failed to analyze job problems: {str(e)}',
            'success': False
        }), 500

@enhanced_job_matching_api.route('/generate-solutions', methods=['POST'])
def generate_solutions():
    """
    Generate solution recommendations based on problem analysis
    
    Request Body:
    {
        "problem_analysis": {...},
        "user_profile": {...},
        "openai_api_key": "optional_api_key"
    }
    
    Returns:
    {
        "solution_analysis": {
            "top_skills": [...],
            "top_certifications": [...],
            "optimal_titles": [...],
            "action_plan": {...}
        },
        "success": true
    }
    """
    try:
        data = request.get_json()
        problem_analysis_data = data.get('problem_analysis', {})
        user_profile = data.get('user_profile', {})
        openai_api_key = data.get('openai_api_key')
        
        if not problem_analysis_data:
            return jsonify({
                'error': 'Problem analysis is required',
                'success': False
            }), 400
        
        # Initialize solution mapper with optional API key
        mapper = ProblemSolutionMapper(openai_api_key)
        
        # Convert problem analysis data back to object
        from ..utils.job_problem_extractor import ProblemAnalysis, ProblemStatement, IndustryContext, CompanyStage
        
        problem_statement = ProblemStatement(
            context=problem_analysis_data['problem_statement']['context'],
            challenge=problem_analysis_data['problem_statement']['challenge'],
            impact=problem_analysis_data['problem_statement']['impact'],
            desired_outcome=problem_analysis_data['problem_statement']['desired_outcome'],
            timeframe=problem_analysis_data['problem_statement']['timeframe'],
            constraints=problem_analysis_data['problem_statement']['constraints']
        )
        
        problem_analysis = ProblemAnalysis(
            problem_statement=problem_statement,
            primary_problems=problem_analysis_data['primary_problems'],
            secondary_problems=problem_analysis_data['secondary_problems'],
            tertiary_problems=problem_analysis_data['tertiary_problems'],
            industry_context=IndustryContext(problem_analysis_data['industry_context']),
            company_stage=CompanyStage(problem_analysis_data['company_stage']),
            confidence_score=problem_analysis_data['confidence_score'],
            extracted_at=datetime.fromisoformat(problem_analysis_data['extracted_at'])
        )
        
        # Generate solutions
        solution_analysis = mapper.map_solutions(problem_analysis, user_profile)
        
        # Convert to JSON-serializable format
        result = {
            'solution_analysis': {
                'top_skills': [
                    {
                        'name': skill.name,
                        'description': skill.description,
                        'total_score': skill.total_score,
                        'relevance_score': skill.relevance_score,
                        'industry_demand_score': skill.industry_demand_score,
                        'career_impact_score': skill.career_impact_score,
                        'learning_roi_score': skill.learning_roi_score,
                        'competitive_advantage_score': skill.competitive_advantage_score,
                        'reasoning': skill.reasoning,
                        'time_to_acquire': skill.time_to_acquire,
                        'cost_estimate': skill.cost_estimate,
                        'salary_impact': skill.salary_impact
                    }
                    for skill in solution_analysis.top_skills
                ],
                'top_certifications': [
                    {
                        'name': cert.name,
                        'description': cert.description,
                        'total_score': cert.total_score,
                        'relevance_score': cert.relevance_score,
                        'industry_demand_score': cert.industry_demand_score,
                        'career_impact_score': cert.career_impact_score,
                        'learning_roi_score': cert.learning_roi_score,
                        'competitive_advantage_score': cert.competitive_advantage_score,
                        'reasoning': cert.reasoning,
                        'time_to_acquire': cert.time_to_acquire,
                        'cost_estimate': cert.cost_estimate,
                        'salary_impact': cert.salary_impact
                    }
                    for cert in solution_analysis.top_certifications
                ],
                'optimal_titles': [
                    {
                        'name': title.name,
                        'description': title.description,
                        'total_score': title.total_score,
                        'relevance_score': title.relevance_score,
                        'industry_demand_score': title.industry_demand_score,
                        'career_impact_score': title.career_impact_score,
                        'learning_roi_score': title.learning_roi_score,
                        'competitive_advantage_score': title.competitive_advantage_score,
                        'reasoning': title.reasoning,
                        'time_to_acquire': title.time_to_acquire,
                        'cost_estimate': title.cost_estimate,
                        'salary_impact': title.salary_impact
                    }
                    for title in solution_analysis.optimal_titles
                ],
                'action_plan': solution_analysis.action_plan,
                'generated_at': solution_analysis.generated_at.isoformat()
            },
            'success': True
        }
        
        logger.info(f"Successfully generated {len(solution_analysis.top_skills)} skill recommendations")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating solutions: {str(e)}")
        return jsonify({
            'error': f'Failed to generate solutions: {str(e)}',
            'success': False
        }), 500

@enhanced_job_matching_api.route('/enhanced-job-matching', methods=['POST'])
def enhanced_job_matching():
    """
    Perform enhanced job matching with problem-solution analysis
    
    Request Body:
    {
        "job_description": "Job description text",
        "user_profile": {
            "skills": [...],
            "current_salary": 75000,
            "career_field": "TECHNOLOGY",
            "experience_level": "MID",
            "preferred_locations": [...],
            "remote_ok": true
        },
        "search_criteria": {
            "current_salary": 75000,
            "target_salary_increase": 0.20,
            "career_field": "TECHNOLOGY",
            "experience_level": "MID",
            "preferred_msas": [...],
            "remote_ok": true
        },
        "openai_api_key": "optional_api_key"
    }
    
    Returns:
    {
        "enhanced_matches": [...],
        "problem_solution_summary": {...},
        "career_positioning_plan": {...},
        "success_probability": 0.85,
        "success": true
    }
    """
    try:
        data = request.get_json()
        job_description = data.get('job_description', '')
        user_profile = data.get('user_profile', {})
        search_criteria_data = data.get('search_criteria')
        openai_api_key = data.get('openai_api_key')
        
        if not job_description:
            return jsonify({
                'error': 'Job description is required',
                'success': False
            }), 400
        
        # Create search criteria if not provided
        search_criteria = None
        if search_criteria_data:
            search_criteria = SearchCriteria(
                current_salary=search_criteria_data.get('current_salary', 75000),
                target_salary_increase=search_criteria_data.get('target_salary_increase', 0.20),
                career_field=CareerField(search_criteria_data.get('career_field', 'TECHNOLOGY')),
                experience_level=ExperienceLevel(search_criteria_data.get('experience_level', 'MID')),
                preferred_msas=search_criteria_data.get('preferred_msas', ['New York']),
                remote_ok=search_criteria_data.get('remote_ok', True),
                company_size_preference=search_criteria_data.get('company_size_preference')
            )
        
        # Initialize enhanced engine with optional API key
        engine = EnhancedJobMatchingEngine(openai_api_key=openai_api_key)
        
        # Perform enhanced matching
        import asyncio
        result = asyncio.run(engine.enhanced_job_matching(
            job_description, user_profile, search_criteria
        ))
        
        # Convert to JSON-serializable format
        enhanced_matches = []
        for match in result.job_matches:
            enhanced_matches.append({
                'job_opportunity': {
                    'job_id': match.job_opportunity.job_id,
                    'title': match.job_opportunity.title,
                    'company': match.job_opportunity.company,
                    'location': match.job_opportunity.location,
                    'salary_min': match.job_opportunity.salary_min,
                    'salary_max': match.job_opportunity.salary_max,
                    'salary_median': match.job_opportunity.salary_median,
                    'url': match.job_opportunity.url,
                    'description': match.job_opportunity.description,
                    'overall_score': match.job_opportunity.overall_score
                },
                'enhanced_score': match.enhanced_score,
                'problem_solution_alignment': match.problem_solution_alignment,
                'positioning_strategy': match.positioning_strategy,
                'application_insights': match.application_insights
            })
        
        response = {
            'enhanced_matches': enhanced_matches,
            'problem_solution_summary': result.problem_solution_summary,
            'career_positioning_plan': result.career_positioning_plan,
            'success_probability': result.success_probability,
            'generated_at': result.generated_at.isoformat(),
            'success': True
        }
        
        logger.info(f"Successfully generated {len(enhanced_matches)} enhanced job matches")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in enhanced job matching: {str(e)}")
        return jsonify({
            'error': f'Failed to perform enhanced job matching: {str(e)}',
            'success': False
        }), 500

@enhanced_job_matching_api.route('/career-positioning-strategy', methods=['POST'])
def career_positioning_strategy():
    """
    Generate comprehensive career positioning strategy
    
    Request Body:
    {
        "problem_analysis": {...},
        "solution_analysis": {...},
        "user_profile": {...}
    }
    
    Returns:
    {
        "positioning_strategy": {
            "problem_focus": "...",
            "solution_approach": [...],
            "key_skills_to_highlight": [...],
            "value_proposition": "...",
            "interview_talking_points": [...],
            "resume_keywords": [...]
        },
        "application_insights": {
            "application_strength": 85,
            "skill_gaps": [...],
            "immediate_actions": [...],
            "salary_negotiation_points": [...],
            "company_research_focus": [...],
            "cover_letter_angles": [...]
        },
        "success": true
    }
    """
    try:
        data = request.get_json()
        problem_analysis_data = data.get('problem_analysis', {})
        solution_analysis_data = data.get('solution_analysis', {})
        user_profile = data.get('user_profile', {})
        
        if not problem_analysis_data or not solution_analysis_data:
            return jsonify({
                'error': 'Problem analysis and solution analysis are required',
                'success': False
            }), 400
        
        # Create positioning strategy
        positioning_strategy = {
            'problem_focus': problem_analysis_data['problem_statement']['challenge'],
            'solution_approach': [
                f"Leverage {skill['name']} to address {problem_analysis_data['problem_statement']['challenge']}"
                for skill in solution_analysis_data['top_skills'][:3]
            ],
            'key_skills_to_highlight': [skill['name'] for skill in solution_analysis_data['top_skills'][:5]],
            'value_proposition': f"As a professional with expertise in {', '.join([skill['name'] for skill in solution_analysis_data['top_skills'][:2]])}, I can help {problem_analysis_data['industry_context']} companies solve {problem_analysis_data['problem_statement']['challenge']} to achieve {problem_analysis_data['problem_statement']['desired_outcome']}",
            'interview_talking_points': [
                {
                    'problem': problem_analysis_data['problem_statement']['challenge'],
                    'solution': f"Based on my experience with {skill['name']}, I would approach this by...",
                    'impact': f"This would help achieve {problem_analysis_data['problem_statement']['desired_outcome']}"
                }
                for skill in solution_analysis_data['top_skills'][:3]
            ],
            'resume_keywords': [skill['name'] for skill in solution_analysis_data['top_skills'][:5]]
        }
        
        # Create application insights
        user_skills = user_profile.get('skills', [])
        recommended_skills = [skill['name'] for skill in solution_analysis_data['top_skills']]
        skill_match_ratio = len(set(user_skills) & set(recommended_skills)) / len(recommended_skills) if recommended_skills else 0
        
        application_insights = {
            'application_strength': int(skill_match_ratio * 100),
            'skill_gaps': [
                {
                    'skill': skill['name'],
                    'priority': 'High' if skill['total_score'] >= 80 else 'Medium',
                    'time_to_learn': skill['time_to_acquire'],
                    'cost': skill['cost_estimate']
                }
                for skill in solution_analysis_data['top_skills'][:5]
                if skill['name'] not in user_skills
            ],
            'immediate_actions': [
                f"Update resume to highlight {skill['name']}" 
                for skill in solution_analysis_data['top_skills'][:3]
            ] + [
                f"Research {problem_analysis_data['industry_context']} industry trends",
                f"Prepare examples of solving {problem_analysis_data['problem_statement']['challenge']}"
            ],
            'salary_negotiation_points': [
                f"Problem-solving expertise in {problem_analysis_data['problem_statement']['challenge']}",
                f"Industry experience in {problem_analysis_data['industry_context']}",
                f"Track record of achieving {problem_analysis_data['problem_statement']['desired_outcome']}"
            ],
            'company_research_focus': [
                f"How they currently handle {problem_analysis_data['problem_statement']['challenge']}",
                f"Their approach to {problem_analysis_data['problem_statement']['desired_outcome']}",
                f"Recent initiatives in {problem_analysis_data['industry_context']} sector"
            ],
            'cover_letter_angles': [
                f"Addressing {problem_analysis_data['problem_statement']['challenge']} with {solution_analysis_data['top_skills'][0]['name']}",
                f"Helping achieve {problem_analysis_data['problem_statement']['desired_outcome']}",
                f"Bringing {problem_analysis_data['industry_context']} expertise to solve their challenges"
            ]
        }
        
        result = {
            'positioning_strategy': positioning_strategy,
            'application_insights': application_insights,
            'success': True
        }
        
        logger.info("Successfully generated career positioning strategy")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating career positioning strategy: {str(e)}")
        return jsonify({
            'error': f'Failed to generate career positioning strategy: {str(e)}',
            'success': False
        }), 500

@enhanced_job_matching_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for enhanced job matching service"""
    return jsonify({
        'status': 'healthy',
        'service': 'enhanced_job_matching',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@enhanced_job_matching_api.route('/analytics', methods=['GET'])
def get_analytics():
    """
    Get analytics for problem-solution analysis
    
    Query Parameters:
    - user_id: Optional user ID to filter analytics
    - analysis_type: Optional analysis type filter
    - days: Number of days to look back (default: 30)
    
    Returns:
    {
        "analytics": {
            "total_analyses": 150,
            "avg_confidence": 0.82,
            "top_problems": [...],
            "top_solutions": [...],
            "success_rates": {...}
        },
        "success": true
    }
    """
    try:
        user_id = request.args.get('user_id')
        analysis_type = request.args.get('analysis_type')
        days = int(request.args.get('days', 30))
        
        # This would query the database for analytics
        # For now, return mock data
        analytics = {
            'total_analyses': 150,
            'avg_confidence': 0.82,
            'top_problems': [
                {'problem': 'Data analysis inefficiency', 'frequency': 45},
                {'problem': 'Process automation needs', 'frequency': 38},
                {'problem': 'Team collaboration challenges', 'frequency': 32}
            ],
            'top_solutions': [
                {'solution': 'Python', 'type': 'skill', 'avg_score': 89},
                {'solution': 'SQL', 'type': 'skill', 'avg_score': 85},
                {'solution': 'PMP Certification', 'type': 'certification', 'avg_score': 82}
            ],
            'success_rates': {
                'high_confidence_analyses': 0.78,
                'successful_positioning': 0.65,
                'skill_acquisition': 0.72
            }
        }
        
        return jsonify({
            'analytics': analytics,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        return jsonify({
            'error': f'Failed to get analytics: {str(e)}',
            'success': False
        }), 500
