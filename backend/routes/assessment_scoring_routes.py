"""
Assessment Scoring API Routes

REST API endpoints for the comprehensive assessment scoring service that implements
the EXACT calculation logic from the MINGUS Calculator Analysis Summary.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from sqlalchemy.orm import Session
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import json

from backend.services.assessment_scoring_service import AssessmentScoringService
from backend.models.assessment_models import UserAssessment, AssessmentResult
from backend.utils.auth import require_auth, get_current_user
from backend.utils.validation import validate_json_schema
from backend.utils.error_handling import handle_api_error, APIError

# Import security components
from backend.security.assessment_security import (
    validate_assessment_input,
    SecurityValidator,
    add_assessment_security_headers
)

logger = logging.getLogger(__name__)

# Create blueprint
assessment_scoring_bp = Blueprint('assessment_scoring', __name__, url_prefix='/api/v1/assessment-scoring')

# JSON schemas for request validation
ASSESSMENT_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "current_salary": {"type": "integer", "minimum": 10000, "maximum": 1000000},
        "field": {"type": "string", "enum": [
            "software_development", "data_analysis", "project_management", 
            "marketing", "finance", "sales", "operations", "hr"
        ]},
        "experience_level": {"type": "string", "enum": [
            "entry", "mid", "senior", "lead", "executive"
        ]},
        "company_size": {"type": "string", "enum": [
            "startup", "small", "medium", "large", "enterprise"
        ]},
        "location": {"type": "string"},
        "industry": {"type": "string"},
        "skills": {"type": "array", "items": {"type": "string"}},
        "required_skills": {"type": "array", "items": {"type": "string"}},
        "relationship_status": {"type": "string", "enum": [
            "single", "dating", "serious", "married", "complicated"
        ]},
        "financial_stress_frequency": {"type": "string", "enum": [
            "never", "rarely", "sometimes", "often", "always"
        ]},
        "emotional_triggers": {"type": "array", "items": {"type": "string", "enum": [
            "after_breakup", "after_arguments", "when_lonely", 
            "when_jealous", "social_pressure"
        ]}},
        "education_level": {"type": "string", "enum": [
            "high_school", "some_college", "bachelors", "masters", "doctorate"
        ]},
        "age_group": {"type": "string", "enum": [
            "18-24", "25-35", "36-45", "46-55", "55+"
        ]}
    },
    "required": ["current_salary", "field", "relationship_status", "financial_stress_frequency"]
}

@assessment_scoring_bp.route('/calculate', methods=['POST'])
@cross_origin()
@require_auth
@validate_assessment_input
@handle_api_error
def calculate_comprehensive_assessment():
    """
    Calculate comprehensive assessment using EXACT MINGUS algorithms
    
    Request Body:
    {
        "assessment_data": {
            "current_salary": 75000,
            "field": "software_development",
            "experience_level": "mid",
            "relationship_status": "married",
            "financial_stress_frequency": "sometimes",
            "emotional_triggers": ["after_arguments"],
            "location": "San Francisco, CA",
            "education_level": "bachelors",
            "age_group": "25-35"
        }
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "overall_risk_level": "Medium Risk",
            "primary_concerns": ["Job Security Risk"],
            "action_priorities": ["Address job security concerns"],
            "subscription_recommendation": "Mid-tier ($20)",
            "confidence_score": 0.75,
            "job_risk": {...},
            "relationship_impact": {...},
            "income_comparison": {...},
            "calculation_time_ms": 125.5,
            "timestamp": "2025-01-27T10:30:00Z"
        }
    }
    """
    try:
        # Get validated data from security decorator
        request_data = getattr(request, 'validated_data', request.get_json())
        if not request_data:
            raise APIError("Request body is required", status_code=400)
        
        assessment_data = request_data.get('assessment_data')
        if not assessment_data:
            raise APIError("assessment_data is required", status_code=400)
        
        # Validate assessment data schema
        validation_result = validate_json_schema(assessment_data, ASSESSMENT_DATA_SCHEMA)
        if not validation_result['valid']:
            raise APIError(f"Invalid assessment data: {validation_result['errors']}", status_code=400)
        
        # Get current user
        current_user = get_current_user()
        user_id = str(current_user.id) if current_user else "anonymous"
        
        # Get database session
        db_session: Session = current_app.db.session
        
        # Initialize scoring service
        scoring_service = AssessmentScoringService(db_session, current_app.config)
        
        # Calculate comprehensive assessment
        start_time = time.time()
        result = scoring_service.calculate_comprehensive_assessment(user_id, assessment_data)
        calculation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Save assessment result to database if user is authenticated
        if current_user and current_user.id:
            try:
                # Create user assessment record
                user_assessment = UserAssessment(
                    user_id=current_user.id,
                    assessment_type='comprehensive',
                    responses_json=assessment_data,
                    score=result.confidence_score,
                    is_complete=True,
                    time_spent_seconds=int(calculation_time / 1000),
                    created_at=datetime.utcnow()
                )
                db_session.add(user_assessment)
                
                # Create assessment result record
                assessment_result = AssessmentResult(
                    user_assessment_id=user_assessment.id,
                    result_json=json.dumps({
                        'overall_risk_level': result.overall_risk_level,
                        'primary_concerns': result.primary_concerns,
                        'action_priorities': result.action_priorities,
                        'subscription_recommendation': result.subscription_recommendation,
                        'confidence_score': result.confidence_score,
                        'job_risk': {
                            'overall_score': result.job_risk.overall_score,
                            'final_risk_level': result.job_risk.final_risk_level.value,
                            'field_multiplier': result.job_risk.field_multiplier,
                            'recommendations': result.job_risk.recommendations
                        },
                        'relationship_impact': {
                            'total_score': result.relationship_impact.total_score,
                            'segment': result.relationship_impact.segment.value,
                            'product_tier': result.relationship_impact.product_tier,
                            'challenges': result.relationship_impact.challenges,
                            'recommendations': result.relationship_impact.recommendations
                        },
                        'income_comparison': {
                            'overall_percentile': result.income_comparison.overall_percentile,
                            'career_opportunity_score': result.income_comparison.career_opportunity_score,
                            'motivational_summary': result.income_comparison.motivational_summary
                        }
                    }),
                    created_at=datetime.utcnow()
                )
                db_session.add(assessment_result)
                
                db_session.commit()
                
            except Exception as e:
                logger.error(f"Error saving assessment result: {str(e)}")
                db_session.rollback()
                # Don't fail the request if saving fails
        
        # Prepare response
        response_data = {
            'overall_risk_level': result.overall_risk_level,
            'primary_concerns': result.primary_concerns,
            'action_priorities': result.action_priorities,
            'subscription_recommendation': result.subscription_recommendation,
            'confidence_score': result.confidence_score,
            'job_risk': {
                'overall_score': result.job_risk.overall_score,
                'final_risk_level': result.job_risk.final_risk_level.value,
                'field_multiplier': result.job_risk.field_multiplier,
                'confidence_interval': result.job_risk.confidence_interval,
                'recommendations': result.job_risk.recommendations,
                'risk_factors': result.job_risk.risk_factors
            },
            'relationship_impact': {
                'total_score': result.relationship_impact.total_score,
                'segment': result.relationship_impact.segment.value,
                'product_tier': result.relationship_impact.product_tier,
                'relationship_points': result.relationship_impact.relationship_points,
                'stress_points': result.relationship_impact.stress_points,
                'trigger_points': result.relationship_impact.trigger_points,
                'challenges': result.relationship_impact.challenges,
                'recommendations': result.relationship_impact.recommendations,
                'financial_impact': result.relationship_impact.financial_impact
            },
            'income_comparison': {
                'user_income': result.income_comparison.user_income,
                'overall_percentile': result.income_comparison.overall_percentile,
                'career_opportunity_score': result.income_comparison.career_opportunity_score,
                'confidence_level': result.income_comparison.confidence_level,
                'motivational_summary': result.income_comparison.motivational_summary,
                'action_plan': result.income_comparison.action_plan,
                'next_steps': result.income_comparison.next_steps
            },
            'calculation_time_ms': calculation_time,
            'timestamp': result.timestamp.isoformat()
        }
        
        logger.info(f"Comprehensive assessment completed for user {user_id} in {calculation_time:.2f}ms")
        
        response = jsonify({
            'success': True,
            'data': response_data
        })
        return add_assessment_security_headers(response), 200
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive assessment calculation: {str(e)}")
        raise APIError("Internal server error", status_code=500)

@assessment_scoring_bp.route('/breakdown', methods=['POST'])
@cross_origin()
@require_auth
@handle_api_error
def get_assessment_breakdown():
    """
    Get detailed breakdown of assessment calculations
    
    Request Body:
    {
        "assessment_data": {
            "current_salary": 75000,
            "field": "software_development",
            "relationship_status": "married",
            "financial_stress_frequency": "sometimes"
        }
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "overall_result": {...},
            "job_risk_breakdown": {...},
            "relationship_breakdown": {...},
            "income_comparison_breakdown": {...},
            "performance_metrics": {...}
        }
    }
    """
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            raise APIError("Request body is required", status_code=400)
        
        assessment_data = request_data.get('assessment_data')
        if not assessment_data:
            raise APIError("assessment_data is required", status_code=400)
        
        # Validate assessment data
        validation_result = validate_json_schema(assessment_data, ASSESSMENT_DATA_SCHEMA)
        if not validation_result['valid']:
            raise APIError(f"Invalid assessment data: {validation_result['errors']}", status_code=400)
        
        # Get current user
        current_user = get_current_user()
        user_id = str(current_user.id) if current_user else "anonymous"
        
        # Get database session
        db_session: Session = current_app.db.session
        
        # Initialize scoring service
        scoring_service = AssessmentScoringService(db_session, current_app.config)
        
        # Get detailed breakdown
        breakdown = scoring_service.get_assessment_breakdown(user_id, assessment_data)
        
        logger.info(f"Assessment breakdown retrieved for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': breakdown
        }), 200
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error getting assessment breakdown: {str(e)}")
        raise APIError("Internal server error", status_code=500)

@assessment_scoring_bp.route('/job-risk', methods=['POST'])
@cross_origin()
@require_auth
@handle_api_error
def calculate_job_risk():
    """
    Calculate AI Job Risk assessment only
    
    Request Body:
    {
        "assessment_data": {
            "current_salary": 75000,
            "field": "software_development",
            "experience_level": "mid",
            "company_size": "large",
            "location": "urban",
            "industry": "technology",
            "skills": ["python", "javascript", "react"],
            "required_skills": ["python", "javascript", "react", "node.js"]
        }
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "overall_score": 0.65,
            "final_risk_level": "medium",
            "field_multiplier": 1.2,
            "confidence_interval": [0.60, 0.70],
            "recommendations": [...],
            "risk_factors": [...]
        }
    }
    """
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            raise APIError("Request body is required", status_code=400)
        
        assessment_data = request_data.get('assessment_data')
        if not assessment_data:
            raise APIError("assessment_data is required", status_code=400)
        
        # Get database session
        db_session: Session = current_app.db.session
        
        # Initialize scoring service
        scoring_service = AssessmentScoringService(db_session, current_app.config)
        
        # Calculate job risk only
        job_risk = scoring_service._calculate_ai_job_risk(assessment_data)
        
        response_data = {
            'overall_score': job_risk.overall_score,
            'final_risk_level': job_risk.final_risk_level.value,
            'field_multiplier': job_risk.field_multiplier,
            'confidence_interval': job_risk.confidence_interval,
            'recommendations': job_risk.recommendations,
            'risk_factors': job_risk.risk_factors,
            'component_scores': {
                'salary_score': job_risk.salary_score,
                'skills_score': job_risk.skills_score,
                'career_score': job_risk.career_score,
                'company_score': job_risk.company_score,
                'location_score': job_risk.location_score,
                'growth_score': job_risk.growth_score
            }
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error in job risk calculation: {str(e)}")
        raise APIError("Internal server error", status_code=500)

@assessment_scoring_bp.route('/relationship-impact', methods=['POST'])
@cross_origin()
@require_auth
@handle_api_error
def calculate_relationship_impact():
    """
    Calculate Relationship Impact assessment only
    
    Request Body:
    {
        "assessment_data": {
            "relationship_status": "married",
            "financial_stress_frequency": "sometimes",
            "emotional_triggers": ["after_arguments", "when_lonely"],
            "current_salary": 75000
        }
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "total_score": 17,
            "segment": "relationship-spender",
            "product_tier": "Mid-tier ($20)",
            "challenges": [...],
            "recommendations": [...],
            "financial_impact": {...}
        }
    }
    """
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            raise APIError("Request body is required", status_code=400)
        
        assessment_data = request_data.get('assessment_data')
        if not assessment_data:
            raise APIError("assessment_data is required", status_code=400)
        
        # Get database session
        db_session: Session = current_app.db.session
        
        # Initialize scoring service
        scoring_service = AssessmentScoringService(db_session, current_app.config)
        
        # Calculate relationship impact only
        relationship_impact = scoring_service._calculate_relationship_impact(assessment_data)
        
        response_data = {
            'total_score': relationship_impact.total_score,
            'segment': relationship_impact.segment.value,
            'product_tier': relationship_impact.product_tier,
            'relationship_points': relationship_impact.relationship_points,
            'stress_points': relationship_impact.stress_points,
            'trigger_points': relationship_impact.trigger_points,
            'challenges': relationship_impact.challenges,
            'recommendations': relationship_impact.recommendations,
            'financial_impact': relationship_impact.financial_impact
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error in relationship impact calculation: {str(e)}")
        raise APIError("Internal server error", status_code=500)

@assessment_scoring_bp.route('/income-comparison', methods=['POST'])
@cross_origin()
@require_auth
@handle_api_error
def calculate_income_comparison():
    """
    Calculate Income Comparison assessment only
    
    Request Body:
    {
        "assessment_data": {
            "current_salary": 75000,
            "location": "New York, NY",
            "education_level": "bachelors",
            "age_group": "25-35"
        }
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "user_income": 75000,
            "overall_percentile": 65.5,
            "career_opportunity_score": 0.75,
            "confidence_level": 0.85,
            "calculation_time_ms": 25.5,
            "motivational_summary": "...",
            "action_plan": [...],
            "next_steps": [...]
        }
    }
    """
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            raise APIError("Request body is required", status_code=400)
        
        assessment_data = request_data.get('assessment_data')
        if not assessment_data:
            raise APIError("assessment_data is required", status_code=400)
        
        # Get database session
        db_session: Session = current_app.db.session
        
        # Initialize scoring service
        scoring_service = AssessmentScoringService(db_session, current_app.config)
        
        # Calculate income comparison only
        income_comparison = scoring_service._calculate_income_comparison(assessment_data)
        
        response_data = {
            'user_income': income_comparison.user_income,
            'overall_percentile': income_comparison.overall_percentile,
            'career_opportunity_score': income_comparison.career_opportunity_score,
            'confidence_level': income_comparison.confidence_level,
            'calculation_time_ms': income_comparison.calculation_time_ms,
            'motivational_summary': income_comparison.motivational_summary,
            'action_plan': income_comparison.action_plan,
            'next_steps': income_comparison.next_steps
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error in income comparison calculation: {str(e)}")
        raise APIError("Internal server error", status_code=500)

@assessment_scoring_bp.route('/performance-stats', methods=['GET'])
@cross_origin()
@require_auth
@handle_api_error
def get_performance_stats():
    """
    Get performance statistics for assessment calculations
    
    Returns:
    {
        "success": true,
        "data": {
            "comprehensive_assessment": 0.125,
            "ai_job_risk_calculation": 0.045,
            "relationship_impact_calculation": 0.012,
            "income_comparison_calculation": 0.025
        }
    }
    """
    try:
        # Get database session
        db_session: Session = current_app.db.session
        
        # Initialize scoring service
        scoring_service = AssessmentScoringService(db_session, current_app.config)
        
        # Get performance statistics
        performance_stats = scoring_service.get_performance_stats()
        
        return jsonify({
            'success': True,
            'data': performance_stats
        }), 200
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        raise APIError("Internal server error", status_code=500)

@assessment_scoring_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for assessment scoring service
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "timestamp": "2025-01-27T10:30:00Z",
            "version": "1.0.0"
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0',
                'service': 'assessment_scoring'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'success': False,
            'data': {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 500
