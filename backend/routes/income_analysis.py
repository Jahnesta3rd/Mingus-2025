"""
Income Analysis Routes
Provides endpoints for income comparison analysis form and processing
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from flask_cors import cross_origin
from loguru import logger
from typing import Dict, Any, Optional
import traceback

from ..ml.models.income_comparator import IncomeComparator, EducationLevel
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id

income_analysis_bp = Blueprint('income_analysis', __name__)

@income_analysis_bp.route('/form', methods=['GET'])
@cross_origin()
def income_analysis_form():
    """
    Display the income analysis form
    
    Returns:
        Rendered HTML template for income analysis form
    """
    try:
        return render_template('income_analysis_form.html')
    except Exception as e:
        logger.error(f"Error rendering income analysis form: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error loading income analysis form'
        }), 500

@income_analysis_bp.route('/results', methods=['GET'])
@cross_origin()
def income_analysis_results():
    """
    Display the income analysis results
    
    Returns:
        Rendered HTML template for income analysis results
    """
    try:
        return render_template('income_analysis_results.html')
    except Exception as e:
        logger.error(f"Error rendering income analysis results: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error loading income analysis results'
        }), 500

@income_analysis_bp.route('/dashboard', methods=['GET'])
@cross_origin()
def comprehensive_dashboard():
    """
    Display the comprehensive career advancement dashboard
    
    Returns:
        Rendered HTML template for comprehensive dashboard
    """
    try:
        return render_template('comprehensive_career_dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering comprehensive dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error loading comprehensive dashboard'
        }), 500

@income_analysis_bp.route('/analyze', methods=['POST'])
@cross_origin()
def analyze_income():
    """
    Perform income comparison analysis
    
    Request body:
    {
        "current_salary": 65000,
        "age_range": "25-27",
        "race": "African American",
        "education_level": "bachelors",
        "location": "Atlanta",
        "years_experience": "2-5",
        "industry": "technology"
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
        # Get form data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
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
        
        # Validate required fields
        required_fields = ['age_range', 'race', 'education_level', 'location']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Validate salary if provided
        if current_salary is not None:
            try:
                current_salary = int(current_salary)
                if current_salary <= 0:
                    return jsonify({
                        'success': False,
                        'error': 'Salary must be a positive number'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid salary value'
                }), 400
        else:
            # If no salary provided, use a default for demonstration
            current_salary = 65000
        
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
        
        logger.info(f"Income analysis completed for salary: ${current_salary:,}, location: {location}")
        
        return jsonify({
            'success': True,
            'data': {
                'income_comparison': response_data
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in income analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during income analysis'
        }), 500

@income_analysis_bp.route('/demo', methods=['GET'])
@cross_origin()
def demo_analysis():
    """
    Provide demo income analysis results
    
    Returns:
    {
        "success": true,
        "data": {
            "income_comparison": {...}
        }
    }
    """
    try:
        # Initialize IncomeComparator
        income_comparator = IncomeComparator()
        
        # Demo data: African American professional in Atlanta
        income_analysis_result = income_comparator.analyze_income(
            user_income=65000,
            location="Atlanta",
            education_level=EducationLevel.BACHELORS,
            age_group="25-35"
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
        
        return jsonify({
            'success': True,
            'data': {
                'income_comparison': response_data,
                'demo_note': 'This is a demo analysis for an African American professional earning $65,000 in Atlanta with a Bachelor\'s degree.'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in demo analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during demo analysis'
        }), 500

@income_analysis_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for income analysis service
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "income_analysis",
            "available_locations": [...],
            "demographic_groups": [...]
        }
    }
    """
    try:
        income_comparator = IncomeComparator()
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'income_analysis',
                'available_locations': income_comparator.get_available_locations(),
                'demographic_summary': income_comparator.get_demographic_summary()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Service unhealthy',
            'data': {
                'status': 'unhealthy',
                'service': 'income_analysis',
                'error': str(e)
            }
        }), 500 