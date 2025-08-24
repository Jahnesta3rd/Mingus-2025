"""
Enhanced Income Comparison API
Integrates with the new salary data service for comprehensive income analysis
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from loguru import logger
import traceback

from ..services.salary_data_service import SalaryDataService, ComprehensiveSalaryData
from ..ml.models.income_comparator import IncomeComparator, EducationLevel
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id

income_comparison_bp = Blueprint('income_comparison', __name__)

class EnhancedIncomeComparisonAPI:
    """
    Enhanced income comparison API with real-time salary data integration
    """
    
    def __init__(self):
        """Initialize the enhanced income comparison API"""
        self.salary_service = SalaryDataService()
        self.income_comparator = IncomeComparator()
        
        # Education level mapping
        self.education_mapping = {
            'high_school': EducationLevel.HIGH_SCHOOL,
            'some_college': EducationLevel.SOME_COLLEGE,
            'bachelors': EducationLevel.BACHELORS,
            'masters': EducationLevel.MASTERS,
            'doctorate': EducationLevel.DOCTORATE
        }
    
    async def get_comprehensive_income_analysis(self, 
                                              current_salary: float,
                                              location: str,
                                              education_level: str = 'bachelors',
                                              occupation: str = None,
                                              include_real_time_data: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive income analysis with real-time data integration
        
        Args:
            current_salary: Current salary
            location: Target location
            education_level: Education level
            occupation: Target occupation (optional)
            include_real_time_data: Whether to include real-time data
        
        Returns:
            Comprehensive income analysis
        """
        try:
            # Get demographic income analysis
            education_enum = self.education_mapping.get(education_level, EducationLevel.BACHELORS)
            
            income_analysis_result = self.income_comparator.analyze_income(
                current_salary=current_salary,
                location=location,
                education_level=education_enum
            )
            
            # Get real-time salary data if requested
            real_time_data = None
            if include_real_time_data:
                try:
                    comprehensive_data = await self.salary_service.get_comprehensive_salary_data(
                        location, occupation
                    )
                    real_time_data = self._format_real_time_data(comprehensive_data)
                except Exception as e:
                    logger.error(f"Error retrieving real-time data: {e}")
                    real_time_data = {
                        'error': 'Unable to retrieve real-time data',
                        'fallback_used': True
                    }
            
            # Combine and enhance analysis
            enhanced_analysis = self._enhance_analysis_with_real_time_data(
                income_analysis_result, real_time_data, current_salary, location
            )
            
            return {
                'success': True,
                'data': {
                    'income_comparison': enhanced_analysis,
                    'real_time_data': real_time_data,
                    'analysis_metadata': {
                        'timestamp': datetime.now().isoformat(),
                        'location': location,
                        'education_level': education_level,
                        'occupation': occupation,
                        'real_time_data_included': include_real_time_data
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive income analysis: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': 'Internal server error during income analysis'
            }
    
    def _format_real_time_data(self, comprehensive_data: ComprehensiveSalaryData) -> Dict[str, Any]:
        """
        Format real-time data for API response
        
        Args:
            comprehensive_data: Comprehensive salary data
        
        Returns:
            Formatted real-time data
        """
        if not comprehensive_data:
            return {'error': 'No real-time data available'}
        
        formatted_data = {
            'location': comprehensive_data.location,
            'occupation': comprehensive_data.occupation,
            'overall_confidence_score': comprehensive_data.overall_confidence_score,
            'data_quality_score': comprehensive_data.data_quality_score,
            'recommendations': comprehensive_data.recommendations,
            'salary_data': [],
            'cost_of_living': None,
            'job_market': None
        }
        
        # Format salary data from different sources
        for salary_point in comprehensive_data.salary_data:
            formatted_salary = {
                'source': salary_point.source.value,
                'median_salary': salary_point.median_salary,
                'mean_salary': salary_point.mean_salary,
                'percentile_25': salary_point.percentile_25,
                'percentile_75': salary_point.percentile_75,
                'sample_size': salary_point.sample_size,
                'year': salary_point.year,
                'confidence_score': salary_point.confidence_score,
                'validation': {
                    'is_valid': salary_point.validation_result.is_valid if salary_point.validation_result else False,
                    'validation_level': salary_point.validation_result.validation_level.value if salary_point.validation_result else 'unknown',
                    'issues': salary_point.validation_result.issues if salary_point.validation_result else [],
                    'warnings': salary_point.validation_result.warnings if salary_point.validation_result else []
                } if salary_point.validation_result else None
            }
            formatted_data['salary_data'].append(formatted_salary)
        
        # Format cost of living data
        if comprehensive_data.cost_of_living_data:
            col_data = comprehensive_data.cost_of_living_data
            formatted_data['cost_of_living'] = {
                'overall_cost_index': col_data.overall_cost_index,
                'housing_cost_index': col_data.housing_cost_index,
                'transportation_cost_index': col_data.transportation_cost_index,
                'food_cost_index': col_data.food_cost_index,
                'healthcare_cost_index': col_data.healthcare_cost_index,
                'utilities_cost_index': col_data.utilities_cost_index,
                'year': col_data.year,
                'confidence_score': col_data.confidence_score,
                'validation': {
                    'is_valid': col_data.validation_result.is_valid if col_data.validation_result else False,
                    'validation_level': col_data.validation_result.validation_level.value if col_data.validation_result else 'unknown',
                    'issues': col_data.validation_result.issues if col_data.validation_result else [],
                    'warnings': col_data.validation_result.warnings if col_data.validation_result else []
                } if col_data.validation_result else None
            }
        
        # Format job market data
        if comprehensive_data.job_market_data:
            job_data = comprehensive_data.job_market_data
            formatted_data['job_market'] = {
                'job_count': job_data.job_count,
                'average_salary': job_data.average_salary,
                'salary_range_min': job_data.salary_range_min,
                'salary_range_max': job_data.salary_range_max,
                'demand_score': job_data.demand_score,
                'confidence_score': job_data.confidence_score,
                'validation': {
                    'is_valid': job_data.validation_result.is_valid if job_data.validation_result else False,
                    'validation_level': job_data.validation_result.validation_level.value if job_data.validation_result else 'unknown',
                    'issues': job_data.validation_result.issues if job_data.validation_result else [],
                    'warnings': job_data.validation_result.warnings if job_data.validation_result else []
                } if job_data.validation_result else None
            }
        
        return formatted_data
    
    def _enhance_analysis_with_real_time_data(self, 
                                            income_analysis: Dict[str, Any],
                                            real_time_data: Dict[str, Any],
                                            current_salary: float,
                                            location: str) -> Dict[str, Any]:
        """
        Enhance income analysis with real-time data insights
        
        Args:
            income_analysis: Original income analysis
            real_time_data: Real-time salary data
            current_salary: Current salary
            location: Target location
        
        Returns:
            Enhanced income analysis
        """
        enhanced_analysis = income_analysis.copy()
        
        if not real_time_data or 'error' in real_time_data:
            enhanced_analysis['real_time_insights'] = {
                'available': False,
                'message': 'Real-time data not available'
            }
            return enhanced_analysis
        
        # Add real-time insights
        real_time_insights = {
            'available': True,
            'data_quality': real_time_data.get('data_quality_score', 0.0),
            'confidence': real_time_data.get('overall_confidence_score', 0.0),
            'salary_comparison': {},
            'cost_of_living_impact': {},
            'job_market_insights': {},
            'recommendations': real_time_data.get('recommendations', [])
        }
        
        # Analyze salary comparison with real-time data
        if real_time_data.get('salary_data'):
            best_salary_data = max(real_time_data['salary_data'], 
                                 key=lambda x: x.get('confidence_score', 0))
            
            real_time_median = best_salary_data.get('median_salary', 0)
            if real_time_median > 0:
                salary_ratio = current_salary / real_time_median
                real_time_insights['salary_comparison'] = {
                    'real_time_median': real_time_median,
                    'salary_ratio': salary_ratio,
                    'percentile_estimate': self._estimate_percentile(current_salary, best_salary_data),
                    'market_position': self._determine_market_position(salary_ratio),
                    'source': best_salary_data.get('source'),
                    'data_quality': best_salary_data.get('validation', {}).get('validation_level', 'unknown')
                }
        
        # Analyze cost of living impact
        if real_time_data.get('cost_of_living'):
            col_data = real_time_data['cost_of_living']
            real_time_insights['cost_of_living_impact'] = {
                'overall_cost_index': col_data.get('overall_cost_index', 100),
                'housing_cost_index': col_data.get('housing_cost_index', 100),
                'cost_adjusted_salary': self._calculate_cost_adjusted_salary(
                    current_salary, col_data.get('overall_cost_index', 100)
                ),
                'relative_affordability': self._assess_affordability(
                    current_salary, col_data.get('overall_cost_index', 100)
                )
            }
        
        # Analyze job market insights
        if real_time_data.get('job_market'):
            job_data = real_time_data['job_market']
            real_time_insights['job_market_insights'] = {
                'job_count': job_data.get('job_count', 0),
                'demand_score': job_data.get('demand_score', 0),
                'salary_range': {
                    'min': job_data.get('salary_range_min', 0),
                    'max': job_data.get('salary_range_max', 0)
                },
                'market_competitiveness': self._assess_market_competitiveness(
                    current_salary, job_data.get('average_salary', 0), job_data.get('demand_score', 0)
                )
            }
        
        enhanced_analysis['real_time_insights'] = real_time_insights
        
        # Add enhanced recommendations
        enhanced_recommendations = enhanced_analysis.get('recommendations', [])
        enhanced_recommendations.extend(real_time_insights.get('recommendations', []))
        enhanced_analysis['recommendations'] = enhanced_recommendations
        
        return enhanced_analysis
    
    def _estimate_percentile(self, salary: float, salary_data: Dict[str, Any]) -> str:
        """Estimate salary percentile based on real-time data"""
        median = salary_data.get('median_salary', 0)
        p25 = salary_data.get('percentile_25', 0)
        p75 = salary_data.get('percentile_75', 0)
        
        if not median or not p25 or not p75:
            return 'unknown'
        
        if salary < p25:
            return 'below_25th'
        elif salary < median:
            return '25th_to_50th'
        elif salary < p75:
            return '50th_to_75th'
        else:
            return 'above_75th'
    
    def _determine_market_position(self, salary_ratio: float) -> str:
        """Determine market position based on salary ratio"""
        if salary_ratio < 0.8:
            return 'below_market'
        elif salary_ratio < 1.0:
            return 'slightly_below_market'
        elif salary_ratio < 1.2:
            return 'at_market'
        elif salary_ratio < 1.5:
            return 'above_market'
        else:
            return 'well_above_market'
    
    def _calculate_cost_adjusted_salary(self, salary: float, cost_index: float) -> float:
        """Calculate cost-adjusted salary"""
        if cost_index == 0:
            return salary
        return (salary * 100) / cost_index
    
    def _assess_affordability(self, salary: float, cost_index: float) -> str:
        """Assess relative affordability"""
        if cost_index < 90:
            return 'very_affordable'
        elif cost_index < 110:
            return 'moderately_affordable'
        elif cost_index < 130:
            return 'somewhat_expensive'
        else:
            return 'very_expensive'
    
    def _assess_market_competitiveness(self, current_salary: float, avg_salary: float, demand_score: float) -> str:
        """Assess market competitiveness"""
        if not avg_salary:
            return 'unknown'
        
        salary_ratio = current_salary / avg_salary
        
        if demand_score > 80 and salary_ratio < 1.0:
            return 'high_demand_low_salary'
        elif demand_score > 80 and salary_ratio >= 1.0:
            return 'high_demand_competitive_salary'
        elif demand_score < 40 and salary_ratio < 1.0:
            return 'low_demand_low_salary'
        else:
            return 'moderate_competitiveness'

# Initialize the enhanced API
enhanced_api = EnhancedIncomeComparisonAPI()

@income_comparison_bp.route('/comprehensive', methods=['POST'])
@cross_origin()
@require_auth
def comprehensive_income_analysis():
    """
    Enhanced income comparison analysis with real-time data integration
    
    Request Body:
    {
        "current_salary": 75000,
        "location": "Atlanta",
        "education_level": "bachelors",
        "occupation": "Software Engineer",
        "include_real_time_data": true
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "income_comparison": {...},
            "real_time_data": {...},
            "analysis_metadata": {...}
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Validate required fields
        required_fields = ['current_salary', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Extract and validate parameters
        current_salary = float(data['current_salary'])
        location = str(data['location'])
        education_level = str(data.get('education_level', 'bachelors'))
        occupation = str(data.get('occupation')) if data.get('occupation') else None
        include_real_time_data = bool(data.get('include_real_time_data', True))
        
        # Validate salary
        if current_salary <= 0:
            return jsonify({
                'success': False,
                'error': 'Current salary must be positive'
            }), 400
        
        # Validate education level
        valid_education_levels = ['high_school', 'some_college', 'bachelors', 'masters', 'doctorate']
        if education_level not in valid_education_levels:
            return jsonify({
                'success': False,
                'error': f'Invalid education level. Must be one of: {valid_education_levels}'
            }), 400
        
        # Get user ID for logging
        user_id = get_current_user_id()
        
        logger.info(f"Comprehensive income analysis requested by user {user_id} for salary: ${current_salary:,}, location: {location}")
        
        # Run async analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                enhanced_api.get_comprehensive_income_analysis(
                    current_salary=current_salary,
                    location=location,
                    education_level=education_level,
                    occupation=occupation,
                    include_real_time_data=include_real_time_data
                )
            )
        finally:
            loop.close()
        
        if result['success']:
            logger.info(f"Comprehensive income analysis completed for user {user_id}")
            return jsonify(result), 200
        else:
            logger.error(f"Comprehensive income analysis failed for user {user_id}: {result.get('error')}")
            return jsonify(result), 500
        
    except ValueError as e:
        logger.error(f"Invalid request data: {e}")
        return jsonify({
            'success': False,
            'error': f'Invalid data format: {str(e)}'
        }), 400
    
    except Exception as e:
        logger.error(f"Error in comprehensive income analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during income analysis'
        }), 500

@income_comparison_bp.route('/real-time-data', methods=['POST'])
@cross_origin()
@require_auth
def get_real_time_salary_data():
    """
    Get real-time salary data for a location and occupation
    
    Request Body:
    {
        "location": "Atlanta",
        "occupation": "Software Engineer"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "real_time_data": {...}
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Validate required fields
        if 'location' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: location'
            }), 400
        
        # Extract parameters
        location = str(data['location'])
        occupation = str(data.get('occupation')) if data.get('occupation') else None
        
        # Get user ID for logging
        user_id = get_current_user_id()
        
        logger.info(f"Real-time salary data requested by user {user_id} for location: {location}, occupation: {occupation}")
        
        # Run async data fetch
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            comprehensive_data = loop.run_until_complete(
                enhanced_api.salary_service.get_comprehensive_salary_data(location, occupation)
            )
            
            real_time_data = enhanced_api._format_real_time_data(comprehensive_data)
            
        finally:
            loop.close()
        
        logger.info(f"Real-time salary data retrieved for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'real_time_data': real_time_data,
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'location': location,
                    'occupation': occupation
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving real-time salary data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error retrieving real-time data'
        }), 500

@income_comparison_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for enhanced income comparison service
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "enhanced_income_comparison",
            "available_locations": [...],
            "real_time_integration": {...},
            "cache_status": {...}
        }
    }
    """
    try:
        # Get available locations
        available_locations = enhanced_api.income_comparator.get_available_locations()
        
        # Get cache status
        cache_status = enhanced_api.salary_service.get_cache_status()
        
        # Get API health status
        api_health = {
            'bls_configured': bool(enhanced_api.salary_service.api_keys['bls']),
            'census_configured': bool(enhanced_api.salary_service.api_keys['census']),
            'fred_configured': bool(enhanced_api.salary_service.api_keys['fred']),
            'indeed_configured': bool(enhanced_api.salary_service.api_keys['indeed'])
        }
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'enhanced_income_comparison',
                'available_locations': available_locations,
                'demographic_summary': enhanced_api.income_comparator.get_demographic_summary(),
                'real_time_integration': {
                    'status': 'available' if cache_status.get('status') == 'available' else 'unavailable',
                    'apis': ['BLS', 'Census', 'FRED', 'Indeed'],
                    'api_health': api_health,
                    'cache_status': cache_status.get('status', 'unknown')
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Service unhealthy',
            'data': {
                'status': 'unhealthy',
                'service': 'enhanced_income_comparison',
                'error': str(e)
            }
        }), 500

@income_comparison_bp.route('/cache/status', methods=['GET'])
@cross_origin()
@require_auth
def get_cache_status():
    """
    Get cache status and statistics
    
    Returns:
    {
        "success": true,
        "data": {
            "cache_status": {...}
        }
    }
    """
    try:
        cache_status = enhanced_api.salary_service.get_cache_status()
        
        return jsonify({
            'success': True,
            'data': {
                'cache_status': cache_status
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cache status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve cache status'
        }), 500

@income_comparison_bp.route('/cache/clear', methods=['POST'])
@cross_origin()
@require_auth
def clear_cache():
    """
    Clear cache entries
    
    Request Body:
    {
        "pattern": "salary_data:*"  // Optional, defaults to all salary data
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "cleared": true,
            "message": "Cache cleared successfully"
        }
    }
    """
    try:
        data = request.get_json() or {}
        pattern = data.get('pattern', 'salary_data:*')
        
        # Get user ID for logging
        user_id = get_current_user_id()
        
        logger.info(f"Cache clear requested by user {user_id} with pattern: {pattern}")
        
        success = enhanced_api.salary_service.clear_cache(pattern)
        
        if success:
            logger.info(f"Cache cleared successfully for user {user_id}")
            return jsonify({
                'success': True,
                'data': {
                    'cleared': True,
                    'message': 'Cache cleared successfully'
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to clear cache'
            }), 500
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to clear cache'
        }), 500 