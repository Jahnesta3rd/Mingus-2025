#!/usr/bin/env python3
"""
Three-Tier Job Recommendation API Endpoints
Provides REST API access to the three-tier job recommendation system
"""

import json
import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from datetime import datetime
from typing import Dict, List, Any

from ..utils.three_tier_job_selector import (
    ThreeTierJobSelector, JobTier, TieredJobRecommendation
)
from ..utils.income_boost_job_matcher import (
    SearchCriteria, CareerField, ExperienceLevel
)

# Create blueprint
three_tier_api = Blueprint('three_tier_api', __name__, url_prefix='/api/three-tier')

# Configure logging
logger = logging.getLogger(__name__)

@three_tier_api.route('/recommendations', methods=['POST'])
@cross_origin()
def get_tiered_recommendations():
    """
    Get job recommendations across all three tiers
    
    Request body:
    {
        "current_salary": 75000,
        "career_field": "technology",
        "experience_level": "mid",
        "preferred_msas": ["Atlanta-Sandy Springs-Alpharetta, GA"],
        "remote_ok": true,
        "max_commute_time": 30,
        "must_have_benefits": ["health insurance", "401k"],
        "company_size_preference": "mid",
        "industry_preference": "technology",
        "equity_required": false,
        "min_company_rating": 3.5,
        "max_recommendations_per_tier": 5
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['current_salary', 'career_field', 'experience_level']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create search criteria
        criteria = SearchCriteria(
            current_salary=int(data['current_salary']),
            target_salary_increase=float(data.get('target_salary_increase', 0.25)),
            career_field=CareerField(data['career_field']),
            experience_level=ExperienceLevel(data['experience_level']),
            preferred_msas=data.get('preferred_msas', []),
            remote_ok=bool(data.get('remote_ok', True)),
            max_commute_time=data.get('max_commute_time'),
            must_have_benefits=data.get('must_have_benefits', []),
            company_size_preference=data.get('company_size_preference'),
            industry_preference=data.get('industry_preference'),
            equity_required=bool(data.get('equity_required', False)),
            min_company_rating=float(data.get('min_company_rating', 3.0))
        )
        
        # Generate tiered recommendations
        selector = ThreeTierJobSelector()
        max_per_tier = data.get('max_recommendations_per_tier', 5)
        
        import asyncio
        recommendations = asyncio.run(
            selector.generate_tiered_recommendations(criteria, max_per_tier)
        )
        
        # Convert recommendations to JSON-serializable format
        serialized_recommendations = {}
        for tier, tier_recommendations in recommendations.items():
            serialized_recommendations[tier.value] = [
                _serialize_recommendation(rec) for rec in tier_recommendations
            ]
        
        # Generate tier summary
        tier_summary = selector.get_tier_summary(recommendations)
        
        return jsonify({
            'success': True,
            'recommendations': serialized_recommendations,
            'tier_summary': tier_summary,
            'total_recommendations': sum(len(recs) for recs in recommendations.values()),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating tiered recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate tiered recommendations',
            'details': str(e)
        }), 500

@three_tier_api.route('/tier/<tier_name>', methods=['GET'])
@cross_origin()
def get_tier_recommendations(tier_name):
    """
    Get recommendations for a specific tier
    
    Path parameters:
    - tier_name: conservative, optimal, or stretch
    """
    try:
        # Validate tier name
        try:
            tier = JobTier(tier_name.lower())
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid tier name: {tier_name}. Must be conservative, optimal, or stretch'
            }), 400
        
        # Get query parameters for search criteria
        current_salary = request.args.get('current_salary', type=int)
        career_field = request.args.get('career_field')
        experience_level = request.args.get('experience_level')
        
        if not all([current_salary, career_field, experience_level]):
            return jsonify({
                'success': False,
                'error': 'Missing required query parameters: current_salary, career_field, experience_level'
            }), 400
        
        # Create search criteria
        criteria = SearchCriteria(
            current_salary=current_salary,
            target_salary_increase=0.25,  # Default
            career_field=CareerField(career_field),
            experience_level=ExperienceLevel(experience_level),
            preferred_msas=request.args.getlist('preferred_msas'),
            remote_ok=request.args.get('remote_ok', 'true').lower() == 'true',
            max_commute_time=request.args.get('max_commute_time', type=int),
            must_have_benefits=request.args.getlist('must_have_benefits'),
            company_size_preference=request.args.get('company_size_preference'),
            industry_preference=request.args.get('industry_preference'),
            equity_required=request.args.get('equity_required', 'false').lower() == 'true',
            min_company_rating=float(request.args.get('min_company_rating', 3.0))
        )
        
        # Generate recommendations for specific tier
        selector = ThreeTierJobSelector()
        max_per_tier = request.args.get('max_recommendations', 5, type=int)
        
        import asyncio
        all_recommendations = asyncio.run(
            selector.generate_tiered_recommendations(criteria, max_per_tier)
        )
        
        tier_recommendations = all_recommendations.get(tier, [])
        serialized_recommendations = [
            _serialize_recommendation(rec) for rec in tier_recommendations
        ]
        
        return jsonify({
            'success': True,
            'tier': tier_name,
            'recommendations': serialized_recommendations,
            'count': len(serialized_recommendations),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting tier recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get tier recommendations',
            'details': str(e)
        }), 500

@three_tier_api.route('/job/<job_id>/analysis', methods=['GET'])
@cross_origin()
def get_job_analysis(job_id):
    """
    Get detailed analysis for a specific job
    
    Path parameters:
    - job_id: Job ID to analyze
    """
    try:
        # Get query parameters for context
        current_salary = request.args.get('current_salary', type=int)
        career_field = request.args.get('career_field')
        experience_level = request.args.get('experience_level')
        
        if not all([current_salary, career_field, experience_level]):
            return jsonify({
                'success': False,
                'error': 'Missing required query parameters: current_salary, career_field, experience_level'
            }), 400
        
        # Create search criteria
        criteria = SearchCriteria(
            current_salary=current_salary,
            target_salary_increase=0.25,
            career_field=CareerField(career_field),
            experience_level=ExperienceLevel(experience_level),
            preferred_msas=request.args.getlist('preferred_msas'),
            remote_ok=request.args.get('remote_ok', 'true').lower() == 'true',
            max_commute_time=request.args.get('max_commute_time', type=int),
            must_have_benefits=request.args.getlist('must_have_benefits'),
            company_size_preference=request.args.get('company_size_preference'),
            industry_preference=request.args.get('industry_preference'),
            equity_required=request.args.get('equity_required', 'false').lower() == 'true',
            min_company_rating=float(request.args.get('min_company_rating', 3.0))
        )
        
        # Get job from database
        selector = ThreeTierJobSelector()
        
        # This would need to be implemented to fetch a specific job
        # For now, return a placeholder response
        return jsonify({
            'success': False,
            'error': 'Job analysis endpoint not yet implemented',
            'job_id': job_id
        }), 501
        
    except Exception as e:
        logger.error(f"Error getting job analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get job analysis',
            'details': str(e)
        }), 500

@three_tier_api.route('/tiers/summary', methods=['GET'])
@cross_origin()
def get_tiers_summary():
    """
    Get summary information about all three tiers
    """
    try:
        selector = ThreeTierJobSelector()
        
        # Get tier specifications
        tier_specs = {}
        for tier in JobTier:
            spec = selector.tier_specs[tier]
            tier_specs[tier.value] = {
                'salary_increase_range': f"{int(spec['salary_increase_min'] * 100)}-{int(spec['salary_increase_max'] * 100)}%",
                'success_probability_min': f"{int(spec['success_probability_min'] * 100)}%",
                'description': spec['description'],
                'company_types': spec['company_types'],
                'risk_level': spec['risk_level']
            }
        
        return jsonify({
            'success': True,
            'tier_specifications': tier_specs,
            'total_tiers': len(JobTier)
        })
        
    except Exception as e:
        logger.error(f"Error getting tiers summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get tiers summary',
            'details': str(e)
        }), 500

@three_tier_api.route('/skills/gap-analysis', methods=['POST'])
@cross_origin()
def analyze_skills_gap():
    """
    Analyze skills gap for a specific job
    
    Request body:
    {
        "job_id": "job_123",
        "current_skills": ["python", "javascript", "sql"],
        "job_requirements": ["python", "aws", "docker", "kubernetes"]
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'job_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: job_id'
            }), 400
        
        # This would need to be implemented to analyze skills gap
        # For now, return a placeholder response
        return jsonify({
            'success': False,
            'error': 'Skills gap analysis endpoint not yet implemented',
            'job_id': data['job_id']
        }), 501
        
    except Exception as e:
        logger.error(f"Error analyzing skills gap: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze skills gap',
            'details': str(e)
        }), 500

def _serialize_recommendation(rec: TieredJobRecommendation) -> Dict[str, Any]:
    """
    Serialize a TieredJobRecommendation to JSON-serializable format
    
    Args:
        rec: TieredJobRecommendation to serialize
        
    Returns:
        Serialized recommendation dictionary
    """
    try:
        from dataclasses import asdict
        
        return {
            'job': {
                'job_id': rec.job.job_id,
                'title': rec.job.title,
                'company': rec.job.company,
                'location': rec.job.location,
                'msa': rec.job.msa,
                'salary_min': rec.job.salary_min,
                'salary_max': rec.job.salary_max,
                'salary_median': rec.job.salary_median,
                'remote_friendly': rec.job.remote_friendly,
                'url': rec.job.url,
                'description': rec.job.description,
                'requirements': rec.job.requirements,
                'benefits': rec.job.benefits,
                'field': rec.job.field.value if rec.job.field else None,
                'experience_level': rec.job.experience_level.value if rec.job.experience_level else None,
                'company_size': rec.job.company_size,
                'company_industry': rec.job.company_industry,
                'equity_offered': rec.job.equity_offered,
                'bonus_potential': rec.job.bonus_potential,
                'overall_score': rec.job.overall_score,
                'diversity_score': rec.job.diversity_score,
                'growth_score': rec.job.growth_score,
                'culture_score': rec.job.culture_score,
                'career_advancement_score': rec.job.career_advancement_score,
                'work_life_balance_score': rec.job.work_life_balance_score
            },
            'tier': rec.tier.value,
            'success_probability': round(rec.success_probability * 100, 1),
            'salary_increase_potential': round(rec.salary_increase_potential * 100, 1),
            'skills_gap_analysis': [asdict(sg) for sg in rec.skills_gap_analysis],
            'application_strategy': asdict(rec.application_strategy),
            'preparation_roadmap': asdict(rec.preparation_roadmap),
            'diversity_analysis': rec.diversity_analysis,
            'company_culture_fit': round(rec.company_culture_fit * 100, 1),
            'career_advancement_potential': round(rec.career_advancement_potential * 100, 1)
        }
        
    except Exception as e:
        logger.error(f"Error serializing recommendation: {str(e)}")
        return {
            'job': {'job_id': rec.job.job_id, 'title': rec.job.title, 'company': rec.job.company},
            'tier': rec.tier.value,
            'error': 'Failed to serialize recommendation'
        }
