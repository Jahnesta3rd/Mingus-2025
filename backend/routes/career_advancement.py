"""
Career Advancement API Routes
Provides endpoints for 3-tier career advancement strategy
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from loguru import logger
from typing import Dict, Any, Optional, List
import traceback

from ..services.career_advancement_service import CareerAdvancementService
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id

career_advancement_bp = Blueprint('career_advancement', __name__)

@career_advancement_bp.route('/generate-strategy', methods=['POST'])
@cross_origin()
@require_auth
def generate_career_advancement_strategy():
    """
    Generate comprehensive career advancement strategy with 3 opportunities
    
    Request body:
    {
        "resume_text": "Optional resume text",
        "target_locations": ["Atlanta", "Houston", "DC"],
        "risk_preference": "balanced"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "career_strategy": {
                "conservative_opportunity": {...},
                "optimal_opportunity": {...},
                "stretch_opportunity": {...},
                "strategy_summary": {...}
            },
            "insights": [...],
            "risk_analysis": {...},
            "timeline_guidance": {...},
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
        target_locations = data.get('target_locations')
        risk_preference = data.get('risk_preference', 'balanced')
        
        # Validate risk preference
        valid_preferences = ['conservative', 'balanced', 'aggressive']
        if risk_preference not in valid_preferences:
            return jsonify({
                'success': False,
                'error': f'Invalid risk preference. Must be one of: {valid_preferences}'
            }), 400
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = CareerAdvancementService(db_session)
        
        # Generate strategy
        result = service.generate_career_advancement_strategy(
            user_id=user_id,
            resume_text=resume_text,
            target_locations=target_locations,
            risk_preference=risk_preference
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        logger.info(f"Career advancement strategy generated for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating career advancement strategy: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during strategy generation'
        }), 500

@career_advancement_bp.route('/strategy', methods=['GET'])
@cross_origin()
@require_auth
def get_career_strategy():
    """
    Get stored career advancement strategy
    
    Returns:
    {
        "success": true,
        "data": {
            "career_strategy": {...},
            "insights": [...],
            "risk_analysis": {...}
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
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = CareerAdvancementService(db_session)
        
        # Get strategy
        result = service.get_career_strategy(user_id)
        
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
        logger.error(f"Error getting career strategy: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@career_advancement_bp.route('/strategy', methods=['PUT'])
@cross_origin()
@require_auth
def update_career_strategy():
    """
    Update career advancement strategy based on user feedback
    
    Request body:
    {
        "strategy_updates": {
            "preferred_tier": "optimal",
            "additional_skills": ["python", "machine_learning"],
            "timeline_preference": "accelerated"
        }
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "updated_strategy": {...}
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
        
        strategy_updates = data.get('strategy_updates', {})
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = CareerAdvancementService(db_session)
        
        # Update strategy
        result = service.update_career_strategy(user_id, strategy_updates)
        
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
        logger.error(f"Error updating career strategy: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@career_advancement_bp.route('/progress', methods=['GET'])
@cross_origin()
@require_auth
def analyze_strategy_progress():
    """
    Analyze progress on career advancement strategy
    
    Returns:
    {
        "success": true,
        "data": {
            "progress_analysis": {
                "conservative": {...},
                "optimal": {...},
                "stretch": {...}
            },
            "overall_progress": {...},
            "recommendations": [...],
            "next_steps": [...]
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
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = CareerAdvancementService(db_session)
        
        # Analyze progress
        result = service.analyze_strategy_progress(user_id)
        
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
        logger.error(f"Error analyzing strategy progress: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@career_advancement_bp.route('/opportunity-details/<tier>', methods=['GET'])
@cross_origin()
@require_auth
def get_opportunity_details(tier):
    """
    Get detailed information about a specific opportunity tier
    
    Path parameters:
    - tier: conservative, optimal, or stretch
    
    Returns:
    {
        "success": true,
        "data": {
            "opportunity": {...},
            "detailed_analysis": {...},
            "action_plan": {...}
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
        
        # Validate tier parameter
        valid_tiers = ['conservative', 'optimal', 'stretch']
        if tier not in valid_tiers:
            return jsonify({
                'success': False,
                'error': f'Invalid tier. Must be one of: {valid_tiers}'
            }), 400
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = CareerAdvancementService(db_session)
        
        # Get strategy
        strategy_result = service.get_career_strategy(user_id)
        if 'error' in strategy_result:
            return jsonify({
                'success': False,
                'error': strategy_result['error']
            }), 404
        
        # Extract opportunity details
        career_strategy = strategy_result.get('data', {}).get('career_strategy', {})
        opportunity = career_strategy.get(f'{tier}_opportunity')
        
        if not opportunity:
            return jsonify({
                'success': False,
                'error': f'No {tier} opportunity found'
            }), 404
        
        # Generate detailed analysis
        detailed_analysis = _generate_detailed_analysis(opportunity, tier)
        action_plan = _generate_action_plan(opportunity, tier)
        
        return jsonify({
            'success': True,
            'data': {
                'opportunity': opportunity,
                'detailed_analysis': detailed_analysis,
                'action_plan': action_plan
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting opportunity details: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@career_advancement_bp.route('/compare-opportunities', methods=['POST'])
@cross_origin()
@require_auth
def compare_opportunities():
    """
    Compare two or more opportunities side by side
    
    Request body:
    {
        "opportunities": ["conservative", "optimal"],
        "comparison_criteria": ["salary", "skills", "timeline"]
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "comparison_matrix": {...},
            "recommendations": [...],
            "trade_offs": [...]
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
        
        opportunities = data.get('opportunities', [])
        comparison_criteria = data.get('comparison_criteria', ['salary', 'skills', 'timeline'])
        
        # Validate opportunities
        valid_tiers = ['conservative', 'optimal', 'stretch']
        if not all(opp in valid_tiers for opp in opportunities):
            return jsonify({
                'success': False,
                'error': f'Invalid opportunities. Must be from: {valid_tiers}'
            }), 400
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = CareerAdvancementService(db_session)
        
        # Get strategy
        strategy_result = service.get_career_strategy(user_id)
        if 'error' in strategy_result:
            return jsonify({
                'success': False,
                'error': strategy_result['error']
            }), 404
        
        # Generate comparison
        career_strategy = strategy_result.get('data', {}).get('career_strategy', {})
        comparison_result = _generate_opportunity_comparison(
            career_strategy, opportunities, comparison_criteria
        )
        
        return jsonify({
            'success': True,
            'data': comparison_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error comparing opportunities: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@career_advancement_bp.route('/skill-development-plan', methods=['POST'])
@cross_origin()
@require_auth
def generate_skill_development_plan():
    """
    Generate personalized skill development plan for career advancement
    
    Request body:
    {
        "target_tier": "optimal",
        "timeline_preference": "accelerated",
        "learning_style": "hands_on"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "skill_plan": {...},
            "learning_path": [...],
            "timeline": {...},
            "resources": [...]
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
        
        target_tier = data.get('target_tier', 'optimal')
        timeline_preference = data.get('timeline_preference', 'standard')
        learning_style = data.get('learning_style', 'balanced')
        
        # Validate parameters
        valid_tiers = ['conservative', 'optimal', 'stretch']
        if target_tier not in valid_tiers:
            return jsonify({
                'success': False,
                'error': f'Invalid target tier. Must be one of: {valid_tiers}'
            }), 400
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = CareerAdvancementService(db_session)
        
        # Get strategy
        strategy_result = service.get_career_strategy(user_id)
        if 'error' in strategy_result:
            return jsonify({
                'success': False,
                'error': strategy_result['error']
            }), 404
        
        # Generate skill development plan
        career_strategy = strategy_result.get('data', {}).get('career_strategy', {})
        opportunity = career_strategy.get(f'{target_tier}_opportunity')
        
        if not opportunity:
            return jsonify({
                'success': False,
                'error': f'No {target_tier} opportunity found'
            }), 404
        
        skill_plan = _generate_skill_development_plan(
            opportunity, target_tier, timeline_preference, learning_style
        )
        
        return jsonify({
            'success': True,
            'data': skill_plan
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating skill development plan: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@career_advancement_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for career advancement service
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "career_advancement",
            "version": "1.0.0"
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'career_advancement',
                'version': '1.0.0',
                'features': [
                    'three_tier_job_selection',
                    'career_advancement_strategy',
                    'skill_gap_analysis',
                    'application_strategy_guidance',
                    'progress_tracking',
                    'opportunity_comparison'
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Service unhealthy'
        }), 500

# Helper functions for the routes

def _generate_detailed_analysis(opportunity: Dict[str, Any], tier: str) -> Dict[str, Any]:
    """Generate detailed analysis for an opportunity"""
    return {
        'tier_analysis': {
            'tier': tier,
            'risk_level': 'low' if tier == 'conservative' else 'medium' if tier == 'optimal' else 'high',
            'effort_required': 'minimal' if tier == 'conservative' else 'moderate' if tier == 'optimal' else 'significant',
            'time_to_readiness': opportunity.get('skill_gap_analysis', {}).get('timeline_to_readiness', 'Unknown')
        },
        'salary_analysis': {
            'increase_percentage': opportunity.get('income_impact', {}).get('salary_increase_percentage', 0),
            'percentile_improvement': opportunity.get('income_impact', {}).get('percentile_improvement', 0),
            'purchasing_power_impact': opportunity.get('income_impact', {}).get('purchasing_power_impact', 0)
        },
        'skills_analysis': {
            'match_percentage': opportunity.get('skill_gap_analysis', {}).get('skills_match_percentage', 0),
            'critical_gaps': opportunity.get('skill_gap_analysis', {}).get('missing_critical_skills', []),
            'learning_recommendations': opportunity.get('skill_gap_analysis', {}).get('learning_recommendations', [])
        },
        'company_analysis': {
            'company_tier': opportunity.get('job', {}).get('company_tier', 'unknown'),
            'glassdoor_rating': opportunity.get('job', {}).get('glassdoor_rating'),
            'remote_work': opportunity.get('job', {}).get('remote_work', False)
        }
    }

def _generate_action_plan(opportunity: Dict[str, Any], tier: str) -> Dict[str, Any]:
    """Generate action plan for an opportunity"""
    app_strategy = opportunity.get('application_strategy', {})
    
    return {
        'immediate_actions': app_strategy.get('preparation_steps', []),
        'timeline': {
            'to_application': app_strategy.get('timeline_to_application', 'Unknown'),
            'to_readiness': opportunity.get('skill_gap_analysis', {}).get('timeline_to_readiness', 'Unknown')
        },
        'success_probability': app_strategy.get('success_probability', 0),
        'risk_factors': app_strategy.get('risk_factors', []),
        'mitigation_strategies': app_strategy.get('mitigation_strategies', []),
        'networking_requirements': app_strategy.get('networking_requirements', [])
    }

def _generate_opportunity_comparison(career_strategy: Dict[str, Any], 
                                   opportunities: List[str], 
                                   criteria: List[str]) -> Dict[str, Any]:
    """Generate comparison matrix for opportunities"""
    comparison_matrix = {}
    
    for criterion in criteria:
        comparison_matrix[criterion] = {}
        for opp in opportunities:
            opportunity = career_strategy.get(f'{opp}_opportunity', {})
            
            if criterion == 'salary':
                comparison_matrix[criterion][opp] = {
                    'increase_percentage': opportunity.get('income_impact', {}).get('salary_increase_percentage', 0),
                    'percentile_improvement': opportunity.get('income_impact', {}).get('percentile_improvement', 0)
                }
            elif criterion == 'skills':
                comparison_matrix[criterion][opp] = {
                    'match_percentage': opportunity.get('skill_gap_analysis', {}).get('skills_match_percentage', 0),
                    'missing_skills': len(opportunity.get('skill_gap_analysis', {}).get('missing_critical_skills', []))
                }
            elif criterion == 'timeline':
                comparison_matrix[criterion][opp] = {
                    'to_application': opportunity.get('application_strategy', {}).get('timeline_to_application', 'Unknown'),
                    'to_readiness': opportunity.get('skill_gap_analysis', {}).get('timeline_to_readiness', 'Unknown')
                }
    
    # Generate recommendations
    recommendations = []
    if len(opportunities) >= 2:
        salary_increases = [comparison_matrix['salary'][opp]['increase_percentage'] for opp in opportunities]
        max_salary_opp = opportunities[salary_increases.index(max(salary_increases))]
        recommendations.append(f"{max_salary_opp.title()} offers the highest salary increase")
    
    # Generate trade-offs
    trade_offs = []
    if 'conservative' in opportunities and 'stretch' in opportunities:
        trade_offs.append("Conservative offers lower risk but lower reward compared to stretch")
    
    return {
        'comparison_matrix': comparison_matrix,
        'recommendations': recommendations,
        'trade_offs': trade_offs
    }

def _generate_skill_development_plan(opportunity: Dict[str, Any], 
                                   target_tier: str, 
                                   timeline_preference: str, 
                                   learning_style: str) -> Dict[str, Any]:
    """Generate personalized skill development plan"""
    skill_gap_analysis = opportunity.get('skill_gap_analysis', {})
    missing_skills = skill_gap_analysis.get('missing_critical_skills', [])
    learning_recommendations = skill_gap_analysis.get('learning_recommendations', [])
    
    # Adjust timeline based on preference
    timeline_multiplier = {
        'accelerated': 0.7,
        'standard': 1.0,
        'flexible': 1.3
    }.get(timeline_preference, 1.0)
    
    # Generate learning path
    learning_path = []
    for rec in learning_recommendations[:3]:  # Top 3 skills
        skill = rec.get('skill', '')
        resources = rec.get('resources', {})
        
        # Adjust timeline
        original_timeline = resources.get('timeline', '4 weeks')
        adjusted_timeline = f"{int(float(original_timeline.split()[0]) * timeline_multiplier)} weeks"
        
        learning_path.append({
            'skill': skill,
            'priority': rec.get('priority', 'medium'),
            'timeline': adjusted_timeline,
            'resources': resources.get('courses', []),
            'learning_style': learning_style
        })
    
    return {
        'skill_plan': {
            'target_tier': target_tier,
            'total_skills_to_develop': len(missing_skills),
            'estimated_timeline': f"{int(len(missing_skills) * 4 * timeline_multiplier)} weeks",
            'difficulty_level': 'intermediate' if target_tier == 'optimal' else 'advanced' if target_tier == 'stretch' else 'beginner'
        },
        'learning_path': learning_path,
        'timeline': {
            'preferred_pace': timeline_preference,
            'adjusted_multiplier': timeline_multiplier,
            'milestones': [
                f"Week {int(4 * timeline_multiplier)}: Complete first skill",
                f"Week {int(8 * timeline_multiplier)}: Complete second skill",
                f"Week {int(12 * timeline_multiplier)}: Ready for application"
            ]
        },
        'resources': {
            'courses': [rec.get('resources', {}).get('courses', []) for rec in learning_recommendations],
            'learning_style': learning_style,
            'estimated_cost': sum([rec.get('resources', {}).get('cost', '$100') for rec in learning_recommendations])
        }
    } 