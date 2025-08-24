"""
Resume Analysis API Routes
Provides endpoints for resume analysis and career insights
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from loguru import logger
from typing import Dict, Any, Optional
import traceback

from ..services.resume_analysis_service import ResumeAnalysisService
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id

resume_analysis_bp = Blueprint('resume_analysis', __name__)

@resume_analysis_bp.route('/analyze', methods=['POST'])
@cross_origin()
@require_auth
def analyze_resume():
    """
    Analyze user's resume and provide career insights
    
    Request body:
    {
        "resume_text": "Raw resume text content",
        "resume_data": {} // Optional structured data
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "analysis": {...},
            "recommendations": [...],
            "insights": {...},
            "salary_insights": {...}
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
        resume_data = data.get('resume_data')
        
        if not resume_text:
            return jsonify({
                'success': False,
                'error': 'Resume text is required'
            }), 400
        
        # Initialize service
        db_session = current_app.config.get('DATABASE_SESSION')
        if not db_session:
            return jsonify({
                'success': False,
                'error': 'Database session not available'
            }), 500
        
        service = ResumeAnalysisService(db_session)
        
        # Analyze resume
        result = service.analyze_user_resume(user_id, resume_text)
        
        logger.info(f"Resume analysis completed for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in resume analysis endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during resume analysis'
        }), 500

@resume_analysis_bp.route('/profile', methods=['GET'])
@cross_origin()
@require_auth
def get_career_profile():
    """
    Get user's career profile and analysis
    
    Returns:
    {
        "success": true,
        "data": {
            "user_profile": {...},
            "career_analysis": {...},
            "last_updated": "..."
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
        
        service = ResumeAnalysisService(db_session)
        
        # Get career profile
        result = service.get_user_career_profile(user_id)
        
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
        logger.error(f"Error getting career profile: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_analysis_bp.route('/recommendations', methods=['GET'])
@cross_origin()
@require_auth
def get_career_recommendations():
    """
    Get personalized career recommendations
    
    Returns:
    {
        "success": true,
        "data": {
            "recommendations": [...],
            "priority_level": "...",
            "timeline": {...}
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
        
        service = ResumeAnalysisService(db_session)
        
        # Get recommendations
        result = service.get_career_recommendations(user_id)
        
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
        logger.error(f"Error getting career recommendations: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_analysis_bp.route('/market-comparison', methods=['GET'])
@cross_origin()
@require_auth
def get_market_comparison():
    """
    Compare user's profile with market data
    
    Returns:
    {
        "success": true,
        "data": {
            "user_profile": {...},
            "market_comparison": {...},
            "competitive_position": "..."
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
        
        service = ResumeAnalysisService(db_session)
        
        # Get market comparison
        result = service.compare_with_market(user_id)
        
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
        logger.error(f"Error getting market comparison: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_analysis_bp.route('/fields', methods=['GET'])
@cross_origin()
def get_field_types():
    """
    Get available field types for classification
    
    Returns:
    {
        "success": true,
        "data": {
            "fields": [
                {"value": "Data Analysis", "keywords": [...]},
                {"value": "Software Development", "keywords": [...]},
                ...
            ]
        }
    }
    """
    try:
        from ..ml.models.resume_parser import FieldType, AdvancedResumeParser
        
        parser = AdvancedResumeParser()
        fields = []
        
        for field in FieldType:
            fields.append({
                'value': field.value,
                'keywords': parser.field_keywords[field]
            })
        
        return jsonify({
            'success': True,
            'data': {
                'fields': fields
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting field types: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@resume_analysis_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for resume analysis service
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "resume_analysis",
            "version": "1.0.0"
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'resume_analysis',
                'version': '1.0.0',
                'features': [
                    'field_expertise_analysis',
                    'career_trajectory_detection',
                    'experience_level_classification',
                    'skills_categorization',
                    'leadership_potential_scoring',
                    'salary_insights',
                    'market_comparison'
                ]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Service unhealthy'
        }), 500

@resume_analysis_bp.route('/demo', methods=['POST'])
@cross_origin()
def demo_analysis():
    """
    Demo endpoint for resume analysis (no authentication required)
    
    Request body:
    {
        "resume_text": "Sample resume text for demonstration"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "analysis": {...},
            "recommendations": [...],
            "insights": {...}
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
        
        resume_text = data.get('resume_text')
        if not resume_text:
            return jsonify({
                'success': False,
                'error': 'Resume text is required'
            }), 400
        
        # Use a mock service for demo
        from ..ml.models.resume_parser import AdvancedResumeParser
        
        parser = AdvancedResumeParser()
        analysis = parser.parse_resume(resume_text)
        
        # Generate demo recommendations
        recommendations = [
            {
                'category': 'skill_development',
                'title': 'Enhance Technical Skills',
                'description': 'Focus on building technical expertise',
                'priority': 'high',
                'estimated_impact': '15-25% salary increase potential'
            },
            {
                'category': 'networking',
                'title': 'Build Professional Network',
                'description': 'Connect with industry professionals',
                'priority': 'medium',
                'estimated_impact': '10-20% salary increase potential'
            }
        ]
        
        # Generate demo insights
        insights = {
            'market_position': 'competitive',
            'growth_trajectory': 'positive',
            'risk_factors': [],
            'opportunities': ['High growth potential in current field'],
            'skill_gaps': []
        }
        
        result = {
            'analysis': parser.get_analysis_summary(analysis),
            'recommendations': recommendations,
            'insights': insights,
            'timestamp': '2025-01-27T12:00:00Z'
        }
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in demo analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during demo analysis'
        }), 500 