"""
Enhanced Job Recommendations API Routes
Comprehensive integration of MingusJobRecommendationEngine with Flask application
"""

from flask import Blueprint, request, jsonify, current_app, session, render_template
from flask_cors import cross_origin
from loguru import logger
from typing import Dict, Any, Optional, List
import traceback
import time
import uuid
import json
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import threading
from functools import wraps

from ..ml.models.mingus_job_recommendation_engine import MingusJobRecommendationEngine
from ..ml.models.income_comparator import IncomeComparator, EducationLevel
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id
from ..services.session_service import SessionService
from ..services.progress_service import ProgressService
from ..services.cache_service import CacheService

enhanced_job_recommendations_bp = Blueprint('enhanced_job_recommendations', __name__)

# Global services
_session_service = None
_progress_service = None
_cache_service = None
_engine = None

def get_services():
    """Get or create global service instances"""
    global _session_service, _progress_service, _cache_service, _engine
    
    if _session_service is None:
        _session_service = SessionService()
    if _progress_service is None:
        _progress_service = ProgressService()
    if _cache_service is None:
        _cache_service = CacheService()
    if _engine is None:
        db_session = current_app.config.get('DATABASE_SESSION')
        _engine = MingusJobRecommendationEngine(db_session)
    
    return _session_service, _progress_service, _cache_service, _engine

def rate_limit(max_requests: int = 10, window: int = 60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = get_current_user_id() or request.remote_addr
            key = f"rate_limit:{user_id}:{f.__name__}"
            
            session_service, _, cache_service, _ = get_services()
            
            # Check rate limit
            current_requests = cache_service.get(key, 0)
            if current_requests >= max_requests:
                return jsonify({
                    'success': False,
                    'error': f'Rate limit exceeded. Maximum {max_requests} requests per {window} seconds.'
                }), 429
            
            # Increment counter
            cache_service.set(key, current_requests + 1, window)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@enhanced_job_recommendations_bp.route('/upload', methods=['GET', 'POST'])
@cross_origin()
@require_auth
def enhanced_upload():
    """
    Enhanced upload route with comprehensive demographic collection
    
    GET: Returns upload form
    POST: Processes resume upload with demographic data
    """
    if request.method == 'GET':
        return render_template('enhanced_upload.html')
    
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Get form data
        resume_text = request.form.get('resume_text')
        current_salary = request.form.get('current_salary')
        target_locations = request.form.getlist('target_locations')
        risk_preference = request.form.get('risk_preference', 'balanced')
        
        # Enhanced demographic data with income comparison fields
        demographic_data = {
            'age_range': request.form.get('age_range'),
            'race': request.form.get('race'),
            'education_level': request.form.get('education_level'),
            'location': request.form.get('location'),
            'years_experience': request.form.get('years_experience'),
            'industry': request.form.get('industry'),
            'company_size': request.form.get('company_size'),
            'remote_preference': request.form.get('remote_preference') == 'true',
            'relocation_willingness': request.form.get('relocation_willingness'),
            'career_goals': request.form.get('career_goals'),
            'salary_expectations': request.form.get('salary_expectations'),
            'skills_assessment': request.form.getlist('skills'),
            'learning_preferences': request.form.getlist('learning_preferences'),
            'geographic_flexibility': request.form.get('geographic_flexibility')
        }
        
        # Validate required demographic fields for income comparison
        required_fields = ['age_range', 'race', 'education_level', 'location']
        missing_fields = [field for field in required_fields if not demographic_data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required demographic fields: {", ".join(missing_fields)}'
            }), 400
        
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
        
        # Store session data
        session_service, _, _, _ = get_services()
        session_id = str(uuid.uuid4())
        
        session_data = {
            'user_id': user_id,
            'resume_text': resume_text,
            'current_salary': int(current_salary) if current_salary else None,
            'target_locations': target_locations,
            'risk_preference': risk_preference,
            'demographic_data': demographic_data,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'uploaded'
        }
        
        session_service.store_session(session_id, session_data)
        
        logger.info(f"Enhanced upload completed for user {user_id}, session {session_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'message': 'Resume uploaded successfully. Ready for processing.',
                'next_step': 'process_recommendations'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in enhanced upload: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during upload'
        }), 500

@enhanced_job_recommendations_bp.route('/process-recommendations', methods=['POST'])
@cross_origin()
@require_auth
@rate_limit(max_requests=5, window=300)  # 5 requests per 5 minutes
def process_recommendations():
    """
    Process job recommendations asynchronously with progress tracking
    
    Request body:
    {
        "session_id": "uuid",
        "processing_options": {
            "enable_caching": true,
            "priority": "normal",
            "include_alternatives": true
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
        
        session_id = data.get('session_id')
        processing_options = data.get('processing_options', {})
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            }), 400
        
        # Get session data
        session_service, progress_service, _, _ = get_services()
        session_data = session_service.get_session(session_id)
        
        if not session_data or session_data.get('user_id') != user_id:
            return jsonify({
                'success': False,
                'error': 'Invalid session or unauthorized access'
            }), 403
        
        # Initialize progress tracking
        progress_id = str(uuid.uuid4())
        progress_data = {
            'session_id': session_id,
            'user_id': user_id,
            'status': 'processing',
            'progress': 0,
            'current_step': 'initializing',
            'started_at': datetime.utcnow().isoformat(),
            'estimated_completion': None,
            'steps': [
                {'name': 'resume_processing', 'status': 'pending', 'progress': 0},
                {'name': 'income_analysis', 'status': 'pending', 'progress': 0},
                {'name': 'job_search', 'status': 'pending', 'progress': 0},
                {'name': 'job_selection', 'status': 'pending', 'progress': 0},
                {'name': 'action_planning', 'status': 'pending', 'progress': 0}
            ]
        }
        
        progress_service.store_progress(progress_id, progress_data)
        
        # Start async processing
        def process_async():
            try:
                _, _, _, engine = get_services()
                
                # Step 1: Resume Processing
                progress_service.update_step(progress_id, 'resume_processing', 'processing', 25)
                user_profile = engine._process_resume_and_analyze_profile(
                    session_data['resume_text'], user_id
                )
                progress_service.update_step(progress_id, 'resume_processing', 'completed', 100)
                
                # Step 2: Income Analysis with Demographic Comparison
                progress_service.update_step(progress_id, 'income_analysis', 'processing', 50)
                
                # Initialize IncomeComparator for demographic analysis
                income_comparator = IncomeComparator()
                income_analysis_result = None
                
                # Perform income comparison if salary is provided
                if session_data.get('current_salary') and session_data.get('demographic_data'):
                    try:
                        demographic_data = session_data['demographic_data']
                        current_salary = session_data['current_salary']
                        
                        # Map education level to IncomeComparator format
                        education_mapping = {
                            'high_school': EducationLevel.HIGH_SCHOOL,
                            'some_college': EducationLevel.SOME_COLLEGE,
                            'bachelors': EducationLevel.BACHELORS,
                            'masters': EducationLevel.MASTERS,
                            'doctorate': EducationLevel.DOCTORATE
                        }
                        
                        education_level = education_mapping.get(demographic_data.get('education_level'))
                        location = demographic_data.get('location')
                        
                        # Perform comprehensive income analysis
                        income_analysis_result = income_comparator.analyze_income(
                            user_income=current_salary,
                            location=location,
                            education_level=education_level,
                            age_group=demographic_data.get('age_range', '25-35')
                        )
                        
                        logger.info(f"Income comparison completed for user {user_id}, salary: ${current_salary:,}")
                        
                    except Exception as e:
                        logger.warning(f"Income comparison failed for user {user_id}: {str(e)}")
                        # Continue without income comparison
                
                # Get existing financial impact analysis
                financial_impact = engine._analyze_income_and_financial_impact(
                    user_profile, 
                    session_data['current_salary'], 
                    session_data['target_locations']
                )
                
                # Add income comparison results to financial impact
                if income_analysis_result:
                    financial_impact['income_comparison'] = {
                        'overall_percentile': income_analysis_result.overall_percentile,
                        'career_opportunity_score': income_analysis_result.career_opportunity_score,
                        'primary_gap': {
                            'group_name': income_analysis_result.primary_gap.group_name,
                            'income_gap': income_analysis_result.primary_gap.income_gap,
                            'gap_percentage': income_analysis_result.primary_gap.gap_percentage,
                            'motivational_insight': income_analysis_result.primary_gap.motivational_insight
                        },
                        'comparisons': [
                            {
                                'group_name': comp.group_name,
                                'median_income': comp.median_income,
                                'percentile_rank': comp.percentile_rank,
                                'income_gap': comp.income_gap,
                                'gap_percentage': comp.gap_percentage,
                                'context_message': comp.context_message,
                                'motivational_insight': comp.motivational_insight,
                                'action_item': comp.action_item
                            }
                            for comp in income_analysis_result.comparisons
                        ],
                        'motivational_summary': income_analysis_result.motivational_summary,
                        'action_plan': income_analysis_result.action_plan,
                        'next_steps': income_analysis_result.next_steps
                    }
                
                progress_service.update_step(progress_id, 'income_analysis', 'completed', 100)
                
                # Step 3: Job Search
                progress_service.update_step(progress_id, 'job_search', 'processing', 75)
                job_opportunities = engine._search_and_match_jobs(
                    user_profile, financial_impact, session_data['target_locations']
                )
                progress_service.update_step(progress_id, 'job_search', 'completed', 100)
                
                # Step 4: Job Selection
                progress_service.update_step(progress_id, 'job_selection', 'processing', 90)
                career_strategy = engine._select_jobs_and_generate_strategy(
                    job_opportunities, user_profile, financial_impact, session_data['risk_preference']
                )
                progress_service.update_step(progress_id, 'job_selection', 'completed', 100)
                
                # Step 5: Action Planning
                progress_service.update_step(progress_id, 'action_planning', 'processing', 95)
                action_plan = engine._generate_comprehensive_action_plan(
                    user_profile, career_strategy, financial_impact
                )
                progress_service.update_step(progress_id, 'action_planning', 'completed', 100)
                
                # Generate final result
                success_probabilities = engine._assess_success_probabilities(
                    career_strategy, user_profile, action_plan
                )
                analytics_data = engine._collect_analytics_data(
                    user_profile, career_strategy, financial_impact, action_plan
                )
                
                # Store results
                result = {
                    'user_profile': user_profile,
                    'career_strategy': career_strategy,
                    'financial_impact': financial_impact,
                    'action_plan': action_plan,
                    'success_probabilities': success_probabilities,
                    'analytics_data': analytics_data,
                    'processing_metrics': engine.processing_metrics,
                    'generated_at': datetime.utcnow().isoformat(),
                    'session_id': session_id
                }
                
                session_service.store_result(session_id, result)
                progress_service.update_progress(progress_id, 'completed', 100)
                
                logger.info(f"Async processing completed for session {session_id}")
                
            except Exception as e:
                logger.error(f"Error in async processing for session {session_id}: {str(e)}")
                progress_service.update_progress(progress_id, 'failed', 0, str(e))
        
        # Start processing in background thread
        thread = threading.Thread(target=process_async)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'data': {
                'progress_id': progress_id,
                'session_id': session_id,
                'message': 'Processing started successfully',
                'estimated_time': '5-8 seconds'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in process recommendations: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during processing'
        }), 500

@enhanced_job_recommendations_bp.route('/progress/<progress_id>', methods=['GET'])
@cross_origin()
@require_auth
def get_progress(progress_id):
    """
    Get real-time processing progress
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "processing",
            "progress": 45,
            "current_step": "job_search",
            "estimated_completion": "2024-01-15T10:30:00Z",
            "steps": [...]
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
        
        _, progress_service, _, _ = get_services()
        progress_data = progress_service.get_progress(progress_id)
        
        if not progress_data or progress_data.get('user_id') != user_id:
            return jsonify({
                'success': False,
                'error': 'Progress not found or unauthorized access'
            }), 404
        
        return jsonify({
            'success': True,
            'data': progress_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@enhanced_job_recommendations_bp.route('/results/<session_id>', methods=['GET'])
@cross_origin()
@require_auth
def get_results(session_id):
    """
    Get processing results
    
    Returns:
    {
        "success": true,
        "data": {
            "user_profile": {...},
            "career_strategy": {...},
            "financial_impact": {...},
            "action_plan": {...},
            "success_probabilities": {...},
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
        
        session_service, _, _, _ = get_services()
        
        # Check session ownership
        session_data = session_service.get_session(session_id)
        if not session_data or session_data.get('user_id') != user_id:
            return jsonify({
                'success': False,
                'error': 'Session not found or unauthorized access'
            }), 404
        
        # Get results
        result = session_service.get_result(session_id)
        if not result:
            return jsonify({
                'success': False,
                'error': 'Results not found or processing not completed'
            }), 404
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@enhanced_job_recommendations_bp.route('/api/recommendations', methods=['POST'])
@cross_origin()
@rate_limit(max_requests=20, window=3600)  # 20 requests per hour
def api_recommendations():
    """
    Programmatic API endpoint for external integration
    
    Request body:
    {
        "resume_text": "Resume content",
        "current_salary": 75000,
        "target_locations": ["Atlanta", "Houston"],
        "risk_preference": "balanced",
        "api_key": "optional_api_key"
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
        current_salary = data.get('current_salary')
        target_locations = data.get('target_locations', [])
        risk_preference = data.get('risk_preference', 'balanced')
        api_key = data.get('api_key')
        
        # Validate required fields
        if not resume_text:
            return jsonify({
                'success': False,
                'error': 'Resume text is required'
            }), 400
        
        # Validate API key if required
        if current_app.config.get('REQUIRE_API_KEY', False) and not api_key:
            return jsonify({
                'success': False,
                'error': 'API key is required'
            }), 401
        
        # Process recommendations
        _, _, _, engine = get_services()
        
        start_time = time.time()
        result = engine.process_resume_and_recommend_jobs(
            resume_text=resume_text,
            user_id=None,  # No user ID for API calls
            current_salary=current_salary,
            target_locations=target_locations,
            risk_preference=risk_preference,
            enable_caching=True
        )
        processing_time = time.time() - start_time
        
        # Format response for API
        api_response = {
            'user_profile': _format_user_profile_api(result.user_profile),
            'career_strategy': _format_career_strategy_api(result.career_strategy),
            'financial_impact': _format_financial_impact_api(result.financial_impact),
            'action_plan': _format_action_plan_api(result.action_plan),
            'success_probabilities': result.success_probabilities,
            'processing_metrics': {
                'total_time': processing_time,
                'cache_hit': result.processing_metrics.cache_hits > 0
            },
            'generated_at': result.generated_at.isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': api_response
        }), 200
        
    except Exception as e:
        logger.error(f"Error in API recommendations: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during processing'
        }), 500

@enhanced_job_recommendations_bp.route('/admin/analytics', methods=['GET'])
@cross_origin()
@require_auth
def admin_analytics():
    """
    Admin endpoint for monitoring recommendation effectiveness
    
    Query parameters:
    - start_date: Start date for analytics (YYYY-MM-DD)
    - end_date: End date for analytics (YYYY-MM-DD)
    - user_id: Specific user ID (optional)
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        # Check admin privileges (simplified - in production, implement proper admin check)
        if not _is_admin(user_id):
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        specific_user_id = request.args.get('user_id')
        
        # Get analytics data
        _, _, _, engine = get_services()
        stats = engine.get_performance_stats()
        
        # Get session analytics
        session_service, _, _, _ = get_services()
        session_analytics = session_service.get_analytics(start_date, end_date, specific_user_id)
        
        analytics_data = {
            'performance_stats': stats,
            'session_analytics': session_analytics,
            'recommendation_effectiveness': _calculate_effectiveness_metrics(),
            'user_engagement': _calculate_engagement_metrics(),
            'error_analysis': _analyze_errors(),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': analytics_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error in admin analytics: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@enhanced_job_recommendations_bp.route('/admin/cache-management', methods=['GET', 'POST', 'DELETE'])
@cross_origin()
@require_auth
def admin_cache_management():
    """
    Admin endpoint for cache management
    
    GET: Get cache statistics
    POST: Clear specific cache entries
    DELETE: Clear all cache
    """
    try:
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        if not _is_admin(user_id):
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        _, _, cache_service, engine = get_services()
        
        if request.method == 'GET':
            # Get cache statistics
            cache_stats = cache_service.get_statistics()
            engine_stats = engine.get_performance_stats()
            
            return jsonify({
                'success': True,
                'data': {
                    'cache_stats': cache_stats,
                    'engine_cache_stats': engine_stats['cache_stats']
                }
            }), 200
        
        elif request.method == 'POST':
            # Clear specific cache entries
            data = request.get_json()
            pattern = data.get('pattern', '*')
            cache_service.clear_pattern(pattern)
            
            return jsonify({
                'success': True,
                'message': f'Cache entries matching "{pattern}" cleared successfully'
            }), 200
        
        elif request.method == 'DELETE':
            # Clear all cache
            cache_service.clear_all()
            engine.clear_cache()
            
            return jsonify({
                'success': True,
                'message': 'All cache cleared successfully'
            }), 200
        
    except Exception as e:
        logger.error(f"Error in cache management: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@enhanced_job_recommendations_bp.route('/income-comparison', methods=['POST'])
@cross_origin()
@require_auth
@rate_limit(max_requests=10, window=300)  # 10 requests per 5 minutes
def income_comparison_analysis():
    """
    Perform standalone income comparison analysis
    
    Request body:
    {
        "current_salary": 65000,
        "age_range": "25-27",
        "race": "African American",
        "education_level": "bachelors",
        "location": "Atlanta"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "income_comparison": {
                "overall_percentile": 53.1,
                "career_opportunity_score": 27.2,
                "primary_gap": {...},
                "comparisons": [...],
                "motivational_summary": "...",
                "action_plan": [...],
                "next_steps": [...]
            }
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
        
        # Extract and validate required fields
        current_salary = data.get('current_salary')
        age_range = data.get('age_range')
        race = data.get('race')
        education_level = data.get('education_level')
        location = data.get('location')
        
        if not all([current_salary, age_range, race, education_level, location]):
            return jsonify({
                'success': False,
                'error': 'All fields are required: current_salary, age_range, race, education_level, location'
            }), 400
        
        # Validate salary
        try:
            current_salary = int(current_salary)
            if current_salary <= 0:
                raise ValueError("Salary must be positive")
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid salary value'
            }), 400
        
        # Initialize IncomeComparator
        income_comparator = IncomeComparator()
        
        # Map education level
        education_mapping = {
            'high_school': EducationLevel.HIGH_SCHOOL,
            'some_college': EducationLevel.SOME_COLLEGE,
            'bachelors': EducationLevel.BACHELORS,
            'masters': EducationLevel.MASTERS,
            'doctorate': EducationLevel.DOCTORATE
        }
        
        mapped_education = education_mapping.get(education_level)
        if not mapped_education:
            return jsonify({
                'success': False,
                'error': 'Invalid education level'
            }), 400
        
        # Perform income analysis
        income_analysis_result = income_comparator.analyze_income(
            user_income=current_salary,
            location=location,
            education_level=mapped_education,
            age_group=age_range
        )
        
        # Format response
        response_data = {
            'overall_percentile': income_analysis_result.overall_percentile,
            'career_opportunity_score': income_analysis_result.career_opportunity_score,
            'primary_gap': {
                'group_name': income_analysis_result.primary_gap.group_name,
                'income_gap': income_analysis_result.primary_gap.income_gap,
                'gap_percentage': income_analysis_result.primary_gap.gap_percentage,
                'motivational_insight': income_analysis_result.primary_gap.motivational_insight
            },
            'comparisons': [
                {
                    'group_name': comp.group_name,
                    'median_income': comp.median_income,
                    'percentile_rank': comp.percentile_rank,
                    'income_gap': comp.income_gap,
                    'gap_percentage': comp.gap_percentage,
                    'context_message': comp.context_message,
                    'motivational_insight': comp.motivational_insight,
                    'action_item': comp.action_item
                }
                for comp in income_analysis_result.comparisons
            ],
            'motivational_summary': income_analysis_result.motivational_summary,
            'action_plan': income_analysis_result.action_plan,
            'next_steps': income_analysis_result.next_steps
        }
        
        logger.info(f"Income comparison analysis completed for user {user_id}, salary: ${current_salary:,}")
        
        return jsonify({
            'success': True,
            'data': {
                'income_comparison': response_data
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in income comparison analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during income comparison analysis'
        }), 500

@enhanced_job_recommendations_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for enhanced job recommendations
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "enhanced_job_recommendations",
            "components": {...},
            "performance": {...}
        }
    }
    """
    try:
        session_service, progress_service, cache_service, engine = get_services()
        
        # Check component health
        components_health = {
            'session_service': 'healthy',
            'progress_service': 'healthy',
            'cache_service': 'healthy',
            'recommendation_engine': 'healthy'
        }
        
        # Check services
        try:
            session_service.ping()
        except Exception:
            components_health['session_service'] = 'unhealthy'
        
        try:
            progress_service.ping()
        except Exception:
            components_health['progress_service'] = 'unhealthy'
        
        try:
            cache_service.ping()
        except Exception:
            components_health['cache_service'] = 'unhealthy'
        
        try:
            engine_stats = engine.get_performance_stats()
            if engine_stats['error_stats']['total_errors'] > 20:
                components_health['recommendation_engine'] = 'degraded'
        except Exception:
            components_health['recommendation_engine'] = 'unhealthy'
        
        # Overall health
        overall_health = 'healthy'
        if any(status != 'healthy' for status in components_health.values()):
            overall_health = 'degraded'
        if any(status == 'unhealthy' for status in components_health.values()):
            overall_health = 'unhealthy'
        
        return jsonify({
            'success': True,
            'data': {
                'status': overall_health,
                'service': 'enhanced_job_recommendations',
                'version': '1.0.0',
                'components': components_health,
                'performance': {
                    'avg_processing_time': engine_stats.get('processing_metrics', {}).get('total_processing_time', 0),
                    'cache_hit_rate': engine_stats.get('cache_stats', {}).get('hit_rate', 0),
                    'error_rate': engine_stats.get('error_stats', {}).get('total_errors', 0)
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Service unhealthy'
        }), 500

# Helper functions

def _format_user_profile_api(user_profile):
    """Format user profile for API response"""
    return {
        'field_expertise': user_profile.field_expertise,
        'experience_level': user_profile.experience_level,
        'skills_summary': {
            'technical_skills_count': len(user_profile.skills_analysis['technical_skills']),
            'business_skills_count': len(user_profile.skills_analysis['business_skills']),
            'leadership_potential': user_profile.leadership_potential
        },
        'income_position': user_profile.income_position,
        'career_trajectory': user_profile.career_trajectory
    }

def _format_career_strategy_api(career_strategy):
    """Format career strategy for API response"""
    return {
        'opportunities': {
            'conservative': {
                'job_title': career_strategy.conservative_opportunity.job.title,
                'company': career_strategy.conservative_opportunity.job.company,
                'location': career_strategy.conservative_opportunity.job.location,
                'salary_increase': career_strategy.conservative_opportunity.income_impact.salary_increase_percentage * 100,
                'success_probability': career_strategy.conservative_opportunity.application_strategy.success_probability
            },
            'optimal': {
                'job_title': career_strategy.optimal_opportunity.job.title,
                'company': career_strategy.optimal_opportunity.job.company,
                'location': career_strategy.optimal_opportunity.job.location,
                'salary_increase': career_strategy.optimal_opportunity.income_impact.salary_increase_percentage * 100,
                'success_probability': career_strategy.optimal_opportunity.application_strategy.success_probability
            },
            'stretch': {
                'job_title': career_strategy.stretch_opportunity.job.title,
                'company': career_strategy.stretch_opportunity.job.company,
                'location': career_strategy.stretch_opportunity.job.location,
                'salary_increase': career_strategy.stretch_opportunity.income_impact.salary_increase_percentage * 100,
                'success_probability': career_strategy.stretch_opportunity.application_strategy.success_probability
            }
        },
        'strategy_summary': career_strategy.strategy_summary
    }

def _format_financial_impact_api(financial_impact):
    """Format financial impact for API response"""
    return {
        'current_salary': financial_impact.current_salary,
        'current_percentile': financial_impact.current_percentile,
        'salary_ranges': financial_impact.recommended_salary_ranges,
        'percentile_improvements': financial_impact.percentile_improvements,
        'income_gap': financial_impact.income_gap_analysis
    }

def _format_action_plan_api(action_plan):
    """Format action plan for API response"""
    return {
        'immediate_actions': action_plan.immediate_actions,
        'skill_development': action_plan.skill_development_plan,
        'networking': action_plan.networking_strategy,
        'timeline': action_plan.application_timeline
    }

def _is_admin(user_id):
    """Check if user has admin privileges (simplified)"""
    # In production, implement proper admin role checking
    admin_user_ids = current_app.config.get('ADMIN_USER_IDS', [])
    return user_id in admin_user_ids

def _calculate_effectiveness_metrics():
    """Calculate recommendation effectiveness metrics"""
    # Placeholder for effectiveness calculations
    return {
        'success_rate': 0.75,
        'salary_improvement_avg': 0.25,
        'user_satisfaction': 0.85,
        'application_rate': 0.60
    }

def _calculate_engagement_metrics():
    """Calculate user engagement metrics"""
    # Placeholder for engagement calculations
    return {
        'daily_active_users': 150,
        'session_duration_avg': 300,
        'feature_usage': {
            'resume_upload': 0.80,
            'job_recommendations': 0.65,
            'action_plans': 0.45
        }
    }

def _analyze_errors():
    """Analyze error patterns"""
    # Placeholder for error analysis
    return {
        'total_errors': 15,
        'error_types': {
            'resume_parsing': 5,
            'job_search': 7,
            'income_analysis': 3
        },
        'resolution_rate': 0.90
    } 