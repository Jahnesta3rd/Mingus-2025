"""
Intelligent Job Matching API Routes
Provides endpoints for income advancement job matching and salary analysis
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from loguru import logger
from typing import Dict, Any, Optional, List
import traceback

from ..services.intelligent_job_matching_service import IntelligentJobMatchingService
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id

intelligent_job_matching_bp = Blueprint('intelligent_job_matching', __name__)

@intelligent_job_matching_bp.route('/find-opportunities', methods=['POST'])
@cross_origin()
@require_auth
def find_income_advancement_opportunities():
    """
    Find income advancement job opportunities
    
    Request body:
    {
        "resume_text": "Optional resume text (will use stored if not provided)",
        "target_locations": ["Atlanta", "Houston", "DC"],
        "min_salary_increase": 0.15
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "job_opportunities": {...},
            "income_analysis": {...},
            "demographic_analysis": {...},
            "insights": [...]
        }
    }
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        resume_text = data.get('resume_text')
        target_locations = data.get('target_locations')
        min_salary_increase = data.get('min_salary_increase')
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = IntelligentJobMatchingService(db_session)
        
        # Find opportunities
        result = service.find_income_advancement_opportunities(
            user_id=user_id,
            resume_text=resume_text,
            target_locations=target_locations,
            min_salary_increase=min_salary_increase
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        logger.info(f"Income advancement opportunities found for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error finding income advancement opportunities: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during job search'
        }), 500

@intelligent_job_matching_bp.route('/recommendations', methods=['GET'])
@cross_origin()
@require_auth
def get_job_recommendations():
    """
    Get job recommendations based on user profile
    
    Query parameters:
    - type: recommendation_type (income_advancement, career_growth, skill_development)
    
    Returns:
    {
        "success": true,
        "data": {
            "recommendations": [...],
            "recommendation_type": "...",
            "total_opportunities": 25
        }
    }
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get query parameters
        recommendation_type = request.args.get('type', 'income_advancement')
        
        # Validate recommendation type
        valid_types = ['income_advancement', 'career_growth', 'skill_development']
        if recommendation_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid recommendation type. Must be one of: {valid_types}'
            }), 400
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = IntelligentJobMatchingService(db_session)
        
        # Get recommendations
        result = service.get_job_recommendations(user_id, recommendation_type)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting job recommendations: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@intelligent_job_matching_bp.route('/salary-potential', methods=['GET'])
@cross_origin()
@require_auth
def analyze_salary_potential():
    """
    Analyze salary potential across locations and career paths
    
    Query parameters:
    - locations: Comma-separated list of target locations
    
    Returns:
    {
        "success": true,
        "data": {
            "current_salary": 75000,
            "location_analysis": {...},
            "career_path_analysis": {...},
            "recommendations": [...]
        }
    }
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get query parameters
        locations_param = request.args.get('locations')
        target_locations = None
        if locations_param:
            target_locations = [loc.strip() for loc in locations_param.split(',')]
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = IntelligentJobMatchingService(db_session)
        
        # Analyze salary potential
        result = service.analyze_salary_potential(user_id, target_locations)
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing salary potential: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@intelligent_job_matching_bp.route('/income-gap-analysis', methods=['POST'])
@cross_origin()
@require_auth
def analyze_income_gap():
    """
    Analyze income gap and improvement opportunities
    
    Request body:
    {
        "current_salary": 75000,
        "target_salary": 95000,
        "field": "Data Analysis",
        "experience_level": "Mid"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "income_gap": 20000,
            "gap_percentage": 26.67,
            "improvement_strategies": [...],
            "market_comparison": {...}
        }
    }
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        current_salary = data.get('current_salary')
        target_salary = data.get('target_salary')
        field = data.get('field')
        experience_level = data.get('experience_level')
        
        if not all([current_salary, target_salary, field, experience_level]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: current_salary, target_salary, field, experience_level'
            }), 400
        
        # Calculate income gap
        income_gap = target_salary - current_salary
        gap_percentage = (income_gap / current_salary) * 100
        
        # Generate improvement strategies
        improvement_strategies = []
        
        if gap_percentage >= 30:
            improvement_strategies.append({
                'strategy': 'Career Advancement',
                'description': 'Seek promotion or higher-level position',
                'potential_impact': '15-25% salary increase',
                'timeline': '6-12 months'
            })
            improvement_strategies.append({
                'strategy': 'Field Transition',
                'description': 'Consider transitioning to higher-paying field',
                'potential_impact': '20-40% salary increase',
                'timeline': '12-18 months'
            })
        elif gap_percentage >= 20:
            improvement_strategies.append({
                'strategy': 'Skill Development',
                'description': 'Develop in-demand skills for your field',
                'potential_impact': '10-20% salary increase',
                'timeline': '3-6 months'
            })
            improvement_strategies.append({
                'strategy': 'Location Change',
                'description': 'Consider relocating to higher-paying markets',
                'potential_impact': '15-30% salary increase',
                'timeline': '6-12 months'
            })
        else:
            improvement_strategies.append({
                'strategy': 'Negotiation',
                'description': 'Negotiate better compensation at current role',
                'potential_impact': '5-15% salary increase',
                'timeline': '1-3 months'
            })
        
        # Market comparison (simplified)
        market_comparison = {
            'field_average': _get_field_average_salary(field, experience_level),
            'percentile': _calculate_salary_percentile(current_salary, field, experience_level),
            'market_position': 'below_average' if current_salary < target_salary else 'above_average'
        }
        
        result = {
            'income_gap': income_gap,
            'gap_percentage': gap_percentage,
            'improvement_strategies': improvement_strategies,
            'market_comparison': market_comparison,
            'recommendations': _generate_gap_recommendations(gap_percentage, improvement_strategies)
        }
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing income gap: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@intelligent_job_matching_bp.route('/market-comparison', methods=['GET'])
@cross_origin()
@require_auth
def get_market_comparison():
    """
    Get market comparison data for user's field and experience
    
    Query parameters:
    - field: User's field
    - experience_level: User's experience level
    - location: Optional location for comparison
    
    Returns:
    {
        "success": true,
        "data": {
            "market_data": {...},
            "percentile_analysis": {...},
            "location_comparison": {...}
        }
    }
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get query parameters
        field = request.args.get('field')
        experience_level = request.args.get('experience_level')
        location = request.args.get('location')
        
        if not field or not experience_level:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: field, experience_level'
            }), 400
        
        # Get market data (simplified - in production, use real data sources)
        market_data = _get_market_data(field, experience_level, location)
        
        return jsonify({
            'success': True,
            'data': market_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting market comparison: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@intelligent_job_matching_bp.route('/search-strategy', methods=['POST'])
@cross_origin()
@require_auth
def generate_search_strategy():
    """
    Generate personalized job search strategy
    
    Request body:
    {
        "resume_text": "User's resume text",
        "current_salary": 75000,
        "target_locations": ["Atlanta", "Houston"],
        "preferences": {
            "remote_work": true,
            "company_size": ["fortune_500", "growth_company"],
            "min_salary_increase": 0.15
        }
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "search_strategy": {...},
            "keyword_optimization": [...],
            "timeline": {...},
            "success_metrics": {...}
        }
    }
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        resume_text = data.get('resume_text')
        current_salary = data.get('current_salary')
        target_locations = data.get('target_locations', [])
        preferences = data.get('preferences', {})
        
        if not resume_text or not current_salary:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: resume_text, current_salary'
            }), 400
        
        # Generate search strategy
        search_strategy = _generate_search_strategy(
            resume_text, current_salary, target_locations, preferences
        )
        
        return jsonify({
            'success': True,
            'data': search_strategy
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating search strategy: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@intelligent_job_matching_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for intelligent job matching service
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "intelligent_job_matching",
            "version": "1.0.0"
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'intelligent_job_matching',
                'version': '1.0.0',
                'features': [
                    'income_advancement_job_search',
                    'salary_potential_analysis',
                    'demographic_comparisons',
                    'career_path_analysis',
                    'market_comparison',
                    'search_strategy_generation'
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Service unhealthy'
        }), 500

# Helper methods for the routes

def _get_field_average_salary(field: str, experience_level: str) -> int:
    """Get average salary for field and experience level (simplified)"""
    base_salaries = {
        'Data Analysis': 85000,
        'Software Development': 95000,
        'Project Management': 90000,
        'Marketing': 75000,
        'Finance': 80000,
        'Sales': 70000,
        'Operations': 75000,
        'HR': 65000
    }
    
    experience_multipliers = {
        'Entry': 0.7,
        'Mid': 1.0,
        'Senior': 1.4
    }
    
    base_salary = base_salaries.get(field, 75000)
    multiplier = experience_multipliers.get(experience_level, 1.0)
    
    return int(base_salary * multiplier)

def _calculate_salary_percentile(salary: int, field: str, experience_level: str) -> float:
    """Calculate salary percentile (simplified)"""
    field_average = _get_field_average_salary(field, experience_level)
    
    if salary >= field_average * 1.5:
        return 90.0
    elif salary >= field_average * 1.25:
        return 75.0
    elif salary >= field_average:
        return 50.0
    elif salary >= field_average * 0.75:
        return 25.0
    else:
        return 10.0

def _generate_gap_recommendations(gap_percentage: float, 
                                improvement_strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate recommendations based on income gap"""
    recommendations = []
    
    if gap_percentage >= 30:
        recommendations.append({
            'priority': 'high',
            'title': 'Significant Income Gap Detected',
            'description': f'Your target salary is {gap_percentage:.1f}% above current. Focus on career advancement.',
            'action_items': ['Update resume', 'Network actively', 'Apply to senior positions']
        })
    elif gap_percentage >= 20:
        recommendations.append({
            'priority': 'medium',
            'title': 'Moderate Income Gap',
            'description': f'Your target salary is {gap_percentage:.1f}% above current. Develop skills and negotiate.',
            'action_items': ['Develop new skills', 'Negotiate current salary', 'Explore new opportunities']
        })
    else:
        recommendations.append({
            'priority': 'low',
            'title': 'Manageable Income Gap',
            'description': f'Your target salary is {gap_percentage:.1f}% above current. Focus on negotiation.',
            'action_items': ['Prepare negotiation strategy', 'Research market rates', 'Highlight achievements']
        })
    
    return recommendations

def _get_market_data(field: str, experience_level: str, location: str = None) -> Dict[str, Any]:
    """Get market data for field and experience level (simplified)"""
    field_average = _get_field_average_salary(field, experience_level)
    
    # Location adjustment
    location_multipliers = {
        'New York City': 1.4,
        'San Francisco': 1.5,
        'Washington DC': 1.25,
        'Chicago': 1.15,
        'Atlanta': 1.0,
        'Houston': 0.95,
        'Dallas': 0.98
    }
    
    location_adjustment = location_multipliers.get(location, 1.0) if location else 1.0
    adjusted_salary = int(field_average * location_adjustment)
    
    return {
        'market_data': {
            'field_average': field_average,
            'location_adjusted_average': adjusted_salary,
            'salary_range': {
                'min': int(field_average * 0.7),
                'max': int(field_average * 1.5)
            }
        },
        'percentile_analysis': {
            'percentiles': {
                '25th': int(field_average * 0.8),
                '50th': field_average,
                '75th': int(field_average * 1.25),
                '90th': int(field_average * 1.5)
            }
        },
        'location_comparison': {
            'location': location,
            'adjustment_factor': location_adjustment,
            'cost_of_living_impact': 'high' if location_adjustment > 1.2 else 'medium' if location_adjustment > 1.0 else 'low'
        }
    }

def _generate_search_strategy(resume_text: str, current_salary: int, 
                            target_locations: List[str], 
                            preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Generate personalized job search strategy"""
    from ..ml.models.resume_parser import AdvancedResumeParser
    
    # Parse resume
    parser = AdvancedResumeParser()
    resume_analysis = parser.parse_resume(resume_text)
    
    # Generate keyword optimization
    field = resume_analysis.field_analysis.primary_field.value
    skills = list(resume_analysis.skills_analysis.technical_skills.keys())
    
    keyword_optimization = [
        f"{field} {skill}" for skill in skills[:5]
    ]
    
    if preferences.get('remote_work'):
        keyword_optimization.extend([f"{field} remote", f"{field} work from home"])
    
    # Generate timeline
    timeline = {
        'week_1_2': ['Update resume', 'Optimize LinkedIn profile', 'Research target companies'],
        'week_3_4': ['Apply to 10-15 positions', 'Network with industry contacts', 'Prepare for interviews'],
        'week_5_8': ['Follow up on applications', 'Attend industry events', 'Continue networking'],
        'month_2_3': ['Interview preparation', 'Salary negotiation practice', 'Decision making']
    }
    
    # Success metrics
    success_metrics = {
        'target_applications_per_week': 5,
        'target_interviews_per_month': 3,
        'target_offers_per_month': 1,
        'salary_increase_target': preferences.get('min_salary_increase', 0.15) * 100
    }
    
    return {
        'search_strategy': {
            'primary_focus': f"Income advancement in {field}",
            'target_salary': int(current_salary * (1 + preferences.get('min_salary_increase', 0.15))),
            'priority_locations': target_locations,
            'company_preferences': preferences.get('company_size', []),
            'remote_preference': preferences.get('remote_work', False)
        },
        'keyword_optimization': keyword_optimization,
        'timeline': timeline,
        'success_metrics': success_metrics,
        'recommendations': [
            'Focus on companies with strong compensation packages',
            'Emphasize quantifiable achievements in applications',
            'Network with industry professionals for referrals',
            'Prepare compelling salary negotiation strategy'
        ]
    } 