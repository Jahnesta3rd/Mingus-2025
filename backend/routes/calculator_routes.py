"""
Calculator Routes for MINGUS
Integrates calculator systems with existing Flask API structure
Provides endpoints for comprehensive analysis, income comparison, job matching, and assessment scoring
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy.orm import Session
from datetime import datetime
import time

from ..services.calculator_integration_service import CalculatorIntegrationService
from ..services.calculator_database_service import CalculatorDatabaseService
from ..database import get_db_session
from ..config.base import Config
from ..models.subscription import AuditLog, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)

# Create blueprint
calculator_bp = Blueprint('calculator', __name__, url_prefix='/api/v1/calculator')

@calculator_bp.route('/comprehensive-analysis', methods=['POST'])
@login_required
def perform_comprehensive_analysis():
    """
    Perform comprehensive analysis integrating all calculator systems
    Target: <500ms total calculation time
    """
    start_time = time.time()
    
    try:
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize services
        calculator_service = CalculatorIntegrationService(db_session, config)
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Perform comprehensive analysis
        result = calculator_service.perform_comprehensive_analysis(current_user.id)
        
        # Save results to database
        database_service.save_income_comparison_results(
            current_user.id, 
            result.result_data['income_analysis']
        )
        
        database_service.save_job_matching_results(
            current_user.id, 
            result.result_data['job_matching']
        )
        
        database_service.save_assessment_results(
            current_user.id, 
            result.result_data['assessment_scoring']
        )
        
        # Update user profile with calculator data
        database_service.update_user_profile_calculator_data(
            current_user.id,
            {
                'insights': result.result_data,
                'recommendations': result.recommendations,
                'performance_metrics': result.performance_metrics,
                'cultural_context': result.cultural_context
            }
        )
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Log performance
        logger.info(f"Comprehensive analysis completed for user {current_user.id} in {total_time:.3f}s")
        
        # Return response
        return jsonify({
            'success': True,
            'data': {
                'user_id': result.user_id,
                'calculation_type': result.calculation_type,
                'result_data': result.result_data,
                'performance_metrics': result.performance_metrics,
                'cultural_context': result.cultural_context,
                'recommendations': result.recommendations,
                'generated_at': result.generated_at.isoformat(),
                'total_calculation_time': total_time
            },
            'message': f'Comprehensive analysis completed successfully in {total_time:.3f}s'
        }), 200
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Comprehensive analysis failed for user {current_user.id} after {total_time:.3f}s: {str(e)}")
        
        # Log audit event
        try:
            audit_log = AuditLog(
                user_id=current_user.id,
                event_type=AuditEventType('comprehensive_analysis_failed'),
                severity=AuditSeverity.ERROR,
                description=f"Comprehensive analysis failed after {total_time:.3f}s: {str(e)}",
                timestamp=datetime.utcnow(),
                metadata={
                    'service': 'calculator_routes',
                    'error': str(e),
                    'calculation_time': total_time
                }
            )
            db_session.add(audit_log)
            db_session.commit()
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': 'Comprehensive analysis failed',
            'message': str(e),
            'calculation_time': total_time
        }), 500

@calculator_bp.route('/income-analysis', methods=['POST'])
@login_required
def perform_income_analysis():
    """
    Perform income analysis with cultural personalization
    Target: <200ms calculation time
    """
    start_time = time.time()
    
    try:
        # Get request data
        data = request.get_json() or {}
        location = data.get('location')
        age_group = data.get('age_group', '25-35')
        
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize services
        calculator_service = CalculatorIntegrationService(db_session, config)
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Get user profile data
        user_profile = database_service.get_user_profile_data(current_user.id)
        if not user_profile:
            return jsonify({
                'success': False,
                'error': 'User profile not found',
                'message': 'Please complete your profile before running income analysis'
            }), 404
        
        # Perform income analysis
        income_analysis = calculator_service._perform_income_analysis(
            type('User', (), {
                'id': current_user.id,
                'profile': type('Profile', (), {
                    'monthly_income': user_profile.monthly_income,
                    'location_city': location or user_profile.location_city,
                    'age_range': age_group
                })()
            })()
        )
        
        # Save results to database
        database_service.save_income_comparison_results(current_user.id, income_analysis)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'data': income_analysis,
            'performance_metrics': {
                'calculation_time': total_time,
                'target_time': 0.2
            },
            'message': f'Income analysis completed in {total_time:.3f}s'
        }), 200
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Income analysis failed for user {current_user.id} after {total_time:.3f}s: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'Income analysis failed',
            'message': str(e),
            'calculation_time': total_time
        }), 500

@calculator_bp.route('/job-matching', methods=['POST'])
@login_required
def perform_job_matching():
    """
    Perform job matching analysis
    Target: <300ms calculation time
    """
    start_time = time.time()
    
    try:
        # Get request data
        data = request.get_json() or {}
        target_locations = data.get('target_locations', [])
        
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize services
        calculator_service = CalculatorIntegrationService(db_session, config)
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Get user profile data
        user_profile = database_service.get_user_profile_data(current_user.id)
        if not user_profile:
            return jsonify({
                'success': False,
                'error': 'User profile not found',
                'message': 'Please complete your profile before running job matching'
            }), 404
        
        # Perform job matching analysis
        job_matching = calculator_service._perform_job_matching_analysis(
            type('User', (), {
                'id': current_user.id,
                'profile': type('Profile', (), {
                    'monthly_income': user_profile.monthly_income,
                    'location_city': user_profile.location_city,
                    'employment_status': user_profile.employment_status
                })()
            })()
        )
        
        # Save results to database
        database_service.save_job_matching_results(current_user.id, job_matching)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'data': job_matching,
            'performance_metrics': {
                'calculation_time': total_time,
                'target_time': 0.3
            },
            'message': f'Job matching completed in {total_time:.3f}s'
        }), 200
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Job matching failed for user {current_user.id} after {total_time:.3f}s: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'Job matching failed',
            'message': str(e),
            'calculation_time': total_time
        }), 500

@calculator_bp.route('/assessment-scoring', methods=['POST'])
@login_required
def perform_assessment_scoring():
    """
    Perform assessment scoring using exact formulas
    Target: <100ms calculation time
    """
    start_time = time.time()
    
    try:
        # Get request data
        data = request.get_json() or {}
        assessment_answers = data.get('answers', {})
        
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize services
        calculator_service = CalculatorIntegrationService(db_session, config)
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Calculate assessment score using exact formulas
        assessment_result = calculator_service._calculate_assessment_score(assessment_answers)
        
        # Save results to database
        database_service.save_assessment_results(current_user.id, assessment_result)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'data': assessment_result,
            'performance_metrics': {
                'calculation_time': total_time,
                'target_time': 0.1
            },
            'message': f'Assessment scoring completed in {total_time:.3f}s'
        }), 200
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Assessment scoring failed for user {current_user.id} after {total_time:.3f}s: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'Assessment scoring failed',
            'message': str(e),
            'calculation_time': total_time
        }), 500

@calculator_bp.route('/cultural-recommendations', methods=['GET'])
@login_required
def get_cultural_recommendations():
    """
    Get cultural recommendations for target demographic
    """
    try:
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize services
        calculator_service = CalculatorIntegrationService(db_session, config)
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Get user profile data
        user_profile = database_service.get_user_profile_data(current_user.id)
        if not user_profile:
            return jsonify({
                'success': False,
                'error': 'User profile not found',
                'message': 'Please complete your profile before getting recommendations'
            }), 404
        
        # Generate cultural recommendations
        cultural_recommendations = calculator_service._generate_cultural_recommendations(
            type('User', (), {
                'id': current_user.id,
                'profile': type('Profile', (), {
                    'age_range': user_profile.age_range,
                    'location_city': user_profile.location_city
                })()
            })()
        )
        
        return jsonify({
            'success': True,
            'data': cultural_recommendations,
            'message': 'Cultural recommendations generated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Cultural recommendations failed for user {current_user.id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'Cultural recommendations failed',
            'message': str(e)
        }), 500

@calculator_bp.route('/performance-stats', methods=['GET'])
@login_required
def get_performance_stats():
    """
    Get performance statistics for calculator systems
    """
    try:
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize services
        calculator_service = CalculatorIntegrationService(db_session, config)
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Get performance stats
        calculator_stats = calculator_service.get_performance_stats()
        database_stats = database_service.get_performance_analytics(current_user.id)
        
        return jsonify({
            'success': True,
            'data': {
                'calculator_performance': calculator_stats,
                'database_performance': database_stats,
                'target_performance': {
                    'comprehensive_analysis': 0.5,  # 500ms
                    'income_analysis': 0.2,         # 200ms
                    'job_matching': 0.3,            # 300ms
                    'assessment_scoring': 0.1       # 100ms
                }
            },
            'message': 'Performance statistics retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Performance stats failed for user {current_user.id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'Performance stats failed',
            'message': str(e)
        }), 500

@calculator_bp.route('/history', methods=['GET'])
@login_required
def get_calculator_history():
    """
    Get calculator usage history for user
    """
    try:
        # Get request parameters
        limit = request.args.get('limit', 10, type=int)
        
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize database service
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Get calculator history
        history = database_service.get_calculator_history(current_user.id, limit)
        
        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'total_entries': len(history)
            },
            'message': 'Calculator history retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Calculator history failed for user {current_user.id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'Calculator history failed',
            'message': str(e)
        }), 500

@calculator_bp.route('/user-profile', methods=['GET'])
@login_required
def get_user_profile_data():
    """
    Get comprehensive user profile data for calculator integration
    """
    try:
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize database service
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Get user profile data
        profile_data = database_service.get_user_profile_data(current_user.id)
        if not profile_data:
            return jsonify({
                'success': False,
                'error': 'User profile not found',
                'message': 'Please complete your profile'
            }), 404
        
        # Get additional data
        goals_data = database_service.get_user_goals_data(current_user.id)
        onboarding_progress = database_service.get_onboarding_progress(current_user.id)
        user_preferences = database_service.get_user_preferences(current_user.id)
        subscription_data = database_service.get_user_subscription_data(current_user.id)
        
        return jsonify({
            'success': True,
            'data': {
                'profile': {
                    'user_id': profile_data.user_id,
                    'email': profile_data.email,
                    'full_name': profile_data.full_name,
                    'age_range': profile_data.age_range,
                    'location_state': profile_data.location_state,
                    'location_city': profile_data.location_city,
                    'monthly_income': profile_data.monthly_income,
                    'employment_status': profile_data.employment_status,
                    'primary_goal': profile_data.primary_goal,
                    'risk_tolerance': profile_data.risk_tolerance,
                    'investment_experience': profile_data.investment_experience,
                    'current_savings': profile_data.current_savings,
                    'current_debt': profile_data.current_debt,
                    'credit_score_range': profile_data.credit_score_range,
                    'household_size': profile_data.household_size,
                    'created_at': profile_data.created_at.isoformat(),
                    'updated_at': profile_data.updated_at.isoformat()
                },
                'goals': goals_data,
                'onboarding_progress': onboarding_progress,
                'preferences': user_preferences,
                'subscription': {
                    'subscription_id': subscription_data.subscription_id,
                    'tier_name': subscription_data.tier_name,
                    'monthly_price': subscription_data.monthly_price,
                    'status': subscription_data.status,
                    'billing_cycle': subscription_data.billing_cycle,
                    'created_at': subscription_data.created_at.isoformat(),
                    'expires_at': subscription_data.expires_at.isoformat() if subscription_data.expires_at else None
                } if subscription_data else None
            },
            'message': 'User profile data retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"User profile data failed for user {current_user.id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'User profile data failed',
            'message': str(e)
        }), 500

@calculator_bp.route('/clear-cache', methods=['POST'])
@login_required
def clear_calculator_cache():
    """
    Clear calculator cache to free memory
    """
    try:
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize services
        calculator_service = CalculatorIntegrationService(db_session, config)
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Clear caches
        calculator_service.clear_performance_cache()
        database_service.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Calculator cache cleared successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Clear cache failed for user {current_user.id}: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'Clear cache failed',
            'message': str(e)
        }), 500

@calculator_bp.route('/database-stats', methods=['GET'])
@login_required
def get_database_stats():
    """
    Get database statistics for monitoring
    """
    try:
        # Get database session
        db_session = get_db_session()
        config = current_app.config
        
        # Initialize database service
        database_service = CalculatorDatabaseService(db_session, config)
        
        # Get database stats
        stats = database_service.get_database_stats()
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': 'Database statistics retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Database stats failed: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': 'Database stats failed',
            'message': str(e)
        }), 500
