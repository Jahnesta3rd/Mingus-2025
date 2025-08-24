"""
Master Job Recommendation Engine API Routes
Provides complete workflow from resume upload to targeted job recommendations
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from loguru import logger
from typing import Dict, Any, Optional, List
import traceback
import time

from ..ml.models.mingus_job_recommendation_engine import MingusJobRecommendationEngine
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id

job_recommendation_engine_bp = Blueprint('job_recommendation_engine', __name__)

# Global engine instance
_engine = None

def get_engine():
    """Get or create global engine instance"""
    global _engine
    if _engine is None:
        db_session = current_app.config.get('DATABASE_SESSION')
        _engine = MingusJobRecommendationEngine(db_session)
    return _engine

@job_recommendation_engine_bp.route('/process-resume', methods=['POST'])
@cross_origin()
@require_auth
def process_resume_and_recommend_jobs():
    """
    Complete workflow from resume processing to job recommendations
    
    Request body:
    {
        "resume_text": "Complete resume text content",
        "current_salary": 75000,
        "target_locations": ["Atlanta", "Houston", "DC"],
        "risk_preference": "balanced",
        "enable_caching": true
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "user_profile": {...},
            "career_strategy": {...},
            "financial_impact": {...},
            "action_plan": {...},
            "success_probabilities": {...},
            "processing_metrics": {...},
            "analytics_data": {...}
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
        target_locations = data.get('target_locations')
        risk_preference = data.get('risk_preference', 'balanced')
        enable_caching = data.get('enable_caching', True)
        
        # Validate required fields
        if not resume_text:
            return jsonify({
                'success': False,
                'error': 'Resume text is required'
            }), 400
        
        if len(resume_text.strip()) < 100:
            return jsonify({
                'success': False,
                'error': 'Resume text is too short. Please provide a complete resume.'
            }), 400
        
        # Validate risk preference
        valid_preferences = ['conservative', 'balanced', 'aggressive']
        if risk_preference not in valid_preferences:
            return jsonify({
                'success': False,
                'error': f'Invalid risk preference. Must be one of: {valid_preferences}'
            }), 400
        
        # Get engine instance
        engine = get_engine()
        
        # Process resume and get recommendations
        start_time = time.time()
        result = engine.process_resume_and_recommend_jobs(
            resume_text=resume_text,
            user_id=user_id,
            current_salary=current_salary,
            target_locations=target_locations,
            risk_preference=risk_preference,
            enable_caching=enable_caching
        )
        total_time = time.time() - start_time
        
        logger.info(f"Complete job recommendation workflow completed for user {user_id} in {total_time:.2f} seconds")
        
        # Format response
        response_data = {
            'user_profile': _format_user_profile(result.user_profile),
            'career_strategy': _format_career_strategy(result.career_strategy),
            'financial_impact': _format_financial_impact(result.financial_impact),
            'action_plan': _format_action_plan(result.action_plan),
            'success_probabilities': result.success_probabilities,
            'processing_metrics': {
                'total_time': result.processing_metrics.total_processing_time,
                'resume_processing_time': result.processing_metrics.resume_processing_time,
                'income_comparison_time': result.processing_metrics.income_comparison_time,
                'job_search_time': result.processing_metrics.job_search_time,
                'job_selection_time': result.processing_metrics.job_selection_time,
                'cache_hits': result.processing_metrics.cache_hits,
                'cache_misses': result.processing_metrics.cache_misses,
                'errors_encountered': result.processing_metrics.errors_encountered
            },
            'analytics_data': result.analytics_data,
            'generated_at': result.generated_at.isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in job recommendation workflow: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during job recommendation processing'
        }), 500

@job_recommendation_engine_bp.route('/quick-analysis', methods=['POST'])
@cross_origin()
@require_auth
def quick_resume_analysis():
    """
    Quick resume analysis without full job search (faster response)
    
    Request body:
    {
        "resume_text": "Resume text content"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "user_profile": {...},
            "financial_analysis": {...},
            "career_insights": {...}
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
        if not resume_text:
            return jsonify({
                'success': False,
                'error': 'Resume text is required'
            }), 400
        
        # Get engine instance
        engine = get_engine()
        
        # Quick analysis (resume processing only)
        start_time = time.time()
        user_profile = engine._process_resume_and_analyze_profile(resume_text, user_id)
        financial_impact = engine._analyze_income_and_financial_impact(user_profile, None, None)
        analysis_time = time.time() - start_time
        
        # Generate career insights
        career_insights = _generate_career_insights(user_profile, financial_impact)
        
        logger.info(f"Quick resume analysis completed for user {user_id} in {analysis_time:.2f} seconds")
        
        return jsonify({
            'success': True,
            'data': {
                'user_profile': _format_user_profile(user_profile),
                'financial_analysis': _format_financial_impact(financial_impact),
                'career_insights': career_insights,
                'processing_time': analysis_time
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in quick resume analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during quick analysis'
        }), 500

@job_recommendation_engine_bp.route('/performance-stats', methods=['GET'])
@cross_origin()
@require_auth
def get_performance_stats():
    """
    Get engine performance statistics
    
    Returns:
    {
        "success": true,
        "data": {
            "processing_metrics": {...},
            "cache_stats": {...},
            "error_stats": {...},
            "performance_targets": {...}
        }
    }
    """
    try:
        engine = get_engine()
        stats = engine.get_performance_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_recommendation_engine_bp.route('/clear-cache', methods=['POST'])
@cross_origin()
@require_auth
def clear_cache():
    """
    Clear the recommendation engine cache
    
    Returns:
    {
        "success": true,
        "message": "Cache cleared successfully"
    }
    """
    try:
        engine = get_engine()
        engine.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_recommendation_engine_bp.route('/reset-metrics', methods=['POST'])
@cross_origin()
@require_auth
def reset_metrics():
    """
    Reset performance metrics
    
    Returns:
    {
        "success": true,
        "message": "Metrics reset successfully"
    }
    """
    try:
        engine = get_engine()
        engine.reset_metrics()
        
        return jsonify({
            'success': True,
            'message': 'Metrics reset successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting metrics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_recommendation_engine_bp.route('/validate-resume', methods=['POST'])
@cross_origin()
@require_auth
def validate_resume():
    """
    Validate resume text before processing
    
    Request body:
    {
        "resume_text": "Resume text content"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "is_valid": true,
            "word_count": 500,
            "estimated_processing_time": 3.5,
            "recommendations": [...]
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        resume_text = data.get('resume_text', '')
        
        # Validate resume
        validation_result = _validate_resume_text(resume_text)
        
        return jsonify({
            'success': True,
            'data': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating resume: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@job_recommendation_engine_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for job recommendation engine
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "job_recommendation_engine",
            "version": "1.0.0",
            "components": {...}
        }
    }
    """
    try:
        engine = get_engine()
        stats = engine.get_performance_stats()
        
        # Check component health
        components_health = {
            'resume_parser': 'healthy',
            'job_matcher': 'healthy',
            'job_selector': 'healthy',
            'cache_system': 'healthy'
        }
        
        # Check for recent errors
        if stats['error_stats']['total_errors'] > 10:
            components_health['overall'] = 'degraded'
        else:
            components_health['overall'] = 'healthy'
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'job_recommendation_engine',
                'version': '1.0.0',
                'components': components_health,
                'performance': {
                    'avg_processing_time': stats['processing_metrics']['total_processing_time'],
                    'cache_hit_rate': stats['cache_stats']['hit_rate'],
                    'error_rate': stats['error_stats']['total_errors']
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Service unhealthy'
        }), 500

# Helper functions for formatting responses

def _format_user_profile(user_profile):
    """Format user profile for API response"""
    return {
        'field_expertise': user_profile.field_expertise,
        'experience_level': user_profile.experience_level,
        'skills_analysis': user_profile.skills_analysis,
        'income_position': user_profile.income_position,
        'career_trajectory': user_profile.career_trajectory,
        'leadership_potential': user_profile.leadership_potential,
        'industry_focus': user_profile.industry_focus,
        'transferable_skills': user_profile.transferable_skills
    }

def _format_career_strategy(career_strategy):
    """Format career strategy for API response"""
    return {
        'conservative_opportunity': _format_opportunity(career_strategy.conservative_opportunity),
        'optimal_opportunity': _format_opportunity(career_strategy.optimal_opportunity),
        'stretch_opportunity': _format_opportunity(career_strategy.stretch_opportunity),
        'strategy_summary': career_strategy.strategy_summary,
        'timeline_recommendations': career_strategy.timeline_recommendations,
        'risk_mitigation_plan': career_strategy.risk_mitigation_plan,
        'generated_at': career_strategy.generated_at.isoformat()
    }

def _format_opportunity(opportunity):
    """Format individual opportunity for API response"""
    return {
        'tier': opportunity.tier.value,
        'job': {
            'title': opportunity.job.title,
            'company': opportunity.job.company,
            'location': opportunity.job.location,
            'salary_range': {
                'min': opportunity.job.salary_range.min_salary if opportunity.job.salary_range else None,
                'max': opportunity.job.salary_range.max_salary if opportunity.job.salary_range else None,
                'midpoint': opportunity.job.salary_range.midpoint if opportunity.job.salary_range else None
            },
            'remote_work': opportunity.job.remote_work,
            'company_tier': opportunity.job.company_tier.value,
            'glassdoor_rating': opportunity.job.glassdoor_rating
        },
        'income_impact': {
            'salary_increase_percentage': opportunity.income_impact.salary_increase_percentage * 100,
            'current_percentile': opportunity.income_impact.current_percentile,
            'new_percentile': opportunity.income_impact.new_percentile,
            'percentile_improvement': opportunity.income_impact.percentile_improvement
        },
        'skill_gap_analysis': {
            'skills_match_percentage': opportunity.skill_gap_analysis.skills_match_percentage * 100,
            'missing_critical_skills': opportunity.skill_gap_analysis.missing_critical_skills,
            'learning_recommendations': opportunity.skill_gap_analysis.learning_recommendations,
            'timeline_to_readiness': opportunity.skill_gap_analysis.timeline_to_readiness
        },
        'application_strategy': {
            'strategy_type': opportunity.application_strategy.strategy_type.value,
            'recommended_approach': opportunity.application_strategy.recommended_approach,
            'timeline_to_application': opportunity.application_strategy.timeline_to_application,
            'preparation_steps': opportunity.application_strategy.preparation_steps,
            'success_probability': opportunity.application_strategy.success_probability,
            'risk_factors': opportunity.application_strategy.risk_factors,
            'mitigation_strategies': opportunity.application_strategy.mitigation_strategies
        },
        'selection_reasoning': opportunity.selection_reasoning,
        'alternative_options': opportunity.alternative_options,
        'backup_recommendations': opportunity.backup_recommendations
    }

def _format_financial_impact(financial_impact):
    """Format financial impact for API response"""
    return {
        'current_salary': financial_impact.current_salary,
        'current_percentile': financial_impact.current_percentile,
        'recommended_salary_ranges': financial_impact.recommended_salary_ranges,
        'percentile_improvements': financial_impact.percentile_improvements,
        'income_gap_analysis': financial_impact.income_gap_analysis,
        'purchasing_power_impact': financial_impact.purchasing_power_impact,
        'cost_of_living_adjustments': financial_impact.cost_of_living_adjustments
    }

def _format_action_plan(action_plan):
    """Format action plan for API response"""
    return {
        'immediate_actions': action_plan.immediate_actions,
        'skill_development_plan': action_plan.skill_development_plan,
        'networking_strategy': action_plan.networking_strategy,
        'application_timeline': action_plan.application_timeline,
        'success_metrics': action_plan.success_metrics,
        'risk_mitigation': action_plan.risk_mitigation
    }

def _generate_career_insights(user_profile, financial_impact):
    """Generate career insights for quick analysis"""
    insights = []
    
    # Field expertise insights
    insights.append({
        'type': 'field_expertise',
        'title': f'Primary Field: {user_profile.field_expertise["primary_field"]}',
        'description': f'You have strong expertise in {user_profile.field_expertise["primary_field"]} with {user_profile.field_expertise["confidence_score"]*100:.1f}% confidence',
        'priority': 'high'
    })
    
    # Experience level insights
    insights.append({
        'type': 'experience_level',
        'title': f'Experience Level: {user_profile.experience_level}',
        'description': f'Your {user_profile.experience_level} level positions you for advancement opportunities',
        'priority': 'medium'
    })
    
    # Income position insights
    current_percentile = financial_impact.current_percentile
    if current_percentile < 50:
        insights.append({
            'type': 'income_opportunity',
            'title': 'Income Advancement Opportunity',
            'description': f'Your current percentile ({current_percentile:.1f}%) indicates significant income advancement potential',
            'priority': 'high'
        })
    elif current_percentile < 75:
        insights.append({
            'type': 'income_opportunity',
            'title': 'Moderate Income Advancement',
            'description': f'Your current percentile ({current_percentile:.1f}%) shows room for income growth',
            'priority': 'medium'
        })
    
    # Skills insights
    technical_skills_count = len(user_profile.skills_analysis['technical_skills'])
    business_skills_count = len(user_profile.skills_analysis['business_skills'])
    
    if technical_skills_count > 5:
        insights.append({
            'type': 'skills_strength',
            'title': 'Strong Technical Skills',
            'description': f'You have {technical_skills_count} technical skills, positioning you well for technical roles',
            'priority': 'medium'
        })
    
    if business_skills_count > 3:
        insights.append({
            'type': 'skills_strength',
            'title': 'Strong Business Skills',
            'description': f'You have {business_skills_count} business skills, valuable for leadership roles',
            'priority': 'medium'
        })
    
    return insights

def _validate_resume_text(resume_text):
    """Validate resume text and provide recommendations"""
    word_count = len(resume_text.split())
    
    validation_result = {
        'is_valid': True,
        'word_count': word_count,
        'estimated_processing_time': 3.5,  # Default estimate
        'recommendations': []
    }
    
    # Check length
    if word_count < 100:
        validation_result['is_valid'] = False
        validation_result['recommendations'].append('Resume is too short. Please provide a complete resume with more details.')
    elif word_count < 300:
        validation_result['recommendations'].append('Consider adding more details to your resume for better analysis.')
    
    # Check for key sections
    sections_to_check = ['experience', 'education', 'skills']
    missing_sections = []
    
    for section in sections_to_check:
        if section.lower() not in resume_text.lower():
            missing_sections.append(section)
    
    if missing_sections:
        validation_result['recommendations'].append(f'Consider adding sections for: {", ".join(missing_sections)}')
    
    # Estimate processing time based on length
    if word_count > 1000:
        validation_result['estimated_processing_time'] = 5.0
    elif word_count > 500:
        validation_result['estimated_processing_time'] = 4.0
    else:
        validation_result['estimated_processing_time'] = 3.0
    
    return validation_result 