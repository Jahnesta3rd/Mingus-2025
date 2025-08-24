"""
Real-time Salary Data Routes
Provides endpoints for accessing real-time salary and cost-of-living data
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from loguru import logger
from typing import Dict, Any, Optional
import traceback

from ..services.salary_data_integration import SalaryDataIntegrationService
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id

real_time_salary_bp = Blueprint('real_time_salary', __name__)

@real_time_salary_bp.route('/comprehensive', methods=['POST'])
@cross_origin()
def get_comprehensive_salary_data():
    """
    Get comprehensive real-time salary data for a location and occupation
    
    Request body:
    {
        "location": "Atlanta",
        "occupation": "Software Engineer",
        "include_job_market": true,
        "include_cost_of_living": true
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "location": "Atlanta",
            "occupation": "Software Engineer",
            "data_sources": ["BLS", "Census"],
            "salary_analysis": {
                "median_salary": 75000,
                "mean_salary": 82000,
                "data_quality": "high",
                "sources_used": 2
            },
            "cost_of_living": {
                "overall_index": 100.0,
                "housing_index": 95.0,
                "transportation_index": 90.0,
                "food_index": 80.0,
                "healthcare_index": 120.0,
                "utilities_index": 70.0
            },
            "job_market": {
                "job_count": 150,
                "average_salary": 78000,
                "salary_range": {
                    "min": 60000,
                    "max": 120000
                },
                "demand_score": 85.5
            },
            "recommendations": [
                "High salary market - excellent earning potential",
                "Lower cost of living - good value for money"
            ],
            "last_updated": "2025-01-27T10:30:00"
        }
    }
    """
    try:
        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract parameters
        location = data.get('location')
        occupation = data.get('occupation')
        include_job_market = data.get('include_job_market', True)
        include_cost_of_living = data.get('include_cost_of_living', True)
        
        # Validate required fields
        if not location:
            return jsonify({
                'success': False,
                'error': 'Location is required'
            }), 400
        
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        # Get comprehensive data
        comprehensive_data = salary_service.get_comprehensive_salary_data(location, occupation)
        
        # Filter data based on request parameters
        if not include_job_market and 'job_market' in comprehensive_data:
            comprehensive_data['job_market'] = {}
        
        if not include_cost_of_living and 'cost_of_living' in comprehensive_data:
            comprehensive_data['cost_of_living'] = {}
        
        logger.info(f"Comprehensive salary data retrieved for {location}, occupation: {occupation}")
        
        return jsonify({
            'success': True,
            'data': comprehensive_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting comprehensive salary data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error while retrieving salary data'
        }), 500

@real_time_salary_bp.route('/bls', methods=['POST'])
@cross_origin()
def get_bls_salary_data():
    """
    Get salary data from Bureau of Labor Statistics API
    
    Request body:
    {
        "location": "Atlanta",
        "occupation": "Software Engineer"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "source": "bls",
            "location": "Atlanta",
            "occupation": "Software Engineer",
            "median_salary": 75000,
            "mean_salary": 82000,
            "percentile_25": 60000,
            "percentile_75": 95000,
            "sample_size": 1000000,
            "year": 2024,
            "last_updated": "2025-01-27T10:30:00",
            "confidence_level": 0.85
        }
    }
    """
    try:
        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract parameters
        location = data.get('location')
        occupation = data.get('occupation')
        
        # Validate required fields
        if not location:
            return jsonify({
                'success': False,
                'error': 'Location is required'
            }), 400
        
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        # Get BLS data
        bls_data = salary_service.get_bls_salary_data(location, occupation)
        
        if not bls_data:
            return jsonify({
                'success': False,
                'error': 'Unable to retrieve BLS salary data'
            }), 404
        
        logger.info(f"BLS salary data retrieved for {location}, occupation: {occupation}")
        
        return jsonify({
            'success': True,
            'data': {
                'source': bls_data.source,
                'location': bls_data.location,
                'occupation': bls_data.occupation,
                'median_salary': bls_data.median_salary,
                'mean_salary': bls_data.mean_salary,
                'percentile_25': bls_data.percentile_25,
                'percentile_75': bls_data.percentile_75,
                'sample_size': bls_data.sample_size,
                'year': bls_data.year,
                'last_updated': bls_data.last_updated.isoformat(),
                'confidence_level': bls_data.confidence_level
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting BLS salary data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error while retrieving BLS data'
        }), 500

@real_time_salary_bp.route('/census', methods=['POST'])
@cross_origin()
def get_census_salary_data():
    """
    Get salary data from Census Bureau API
    
    Request body:
    {
        "location": "Atlanta"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "source": "census",
            "location": "Atlanta",
            "occupation": "General",
            "median_salary": 65000,
            "mean_salary": 75000,
            "percentile_25": 45000,
            "percentile_75": 95000,
            "sample_size": 500000,
            "year": 2022,
            "last_updated": "2025-01-27T10:30:00",
            "confidence_level": 0.90
        }
    }
    """
    try:
        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract parameters
        location = data.get('location')
        
        # Validate required fields
        if not location:
            return jsonify({
                'success': False,
                'error': 'Location is required'
            }), 400
        
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        # Get Census data
        census_data = salary_service.get_census_salary_data(location)
        
        if not census_data:
            return jsonify({
                'success': False,
                'error': 'Unable to retrieve Census salary data'
            }), 404
        
        logger.info(f"Census salary data retrieved for {location}")
        
        return jsonify({
            'success': True,
            'data': {
                'source': census_data.source,
                'location': census_data.location,
                'occupation': census_data.occupation,
                'median_salary': census_data.median_salary,
                'mean_salary': census_data.mean_salary,
                'percentile_25': census_data.percentile_25,
                'percentile_75': census_data.percentile_75,
                'sample_size': census_data.sample_size,
                'year': census_data.year,
                'last_updated': census_data.last_updated.isoformat(),
                'confidence_level': census_data.confidence_level
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting Census salary data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error while retrieving Census data'
        }), 500

@real_time_salary_bp.route('/cost-of-living', methods=['POST'])
@cross_origin()
def get_cost_of_living_data():
    """
    Get cost of living data from FRED API
    
    Request body:
    {
        "location": "Atlanta"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "location": "Atlanta",
            "housing_cost_index": 95.0,
            "transportation_cost_index": 90.0,
            "food_cost_index": 80.0,
            "healthcare_cost_index": 120.0,
            "utilities_cost_index": 70.0,
            "overall_cost_index": 100.0,
            "year": 2024,
            "last_updated": "2025-01-27T10:30:00"
        }
    }
    """
    try:
        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract parameters
        location = data.get('location')
        
        # Validate required fields
        if not location:
            return jsonify({
                'success': False,
                'error': 'Location is required'
            }), 400
        
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        # Get cost of living data
        cost_data = salary_service.get_fred_cost_of_living_data(location)
        
        if not cost_data:
            return jsonify({
                'success': False,
                'error': 'Unable to retrieve cost of living data'
            }), 404
        
        logger.info(f"Cost of living data retrieved for {location}")
        
        return jsonify({
            'success': True,
            'data': {
                'location': cost_data.location,
                'housing_cost_index': cost_data.housing_cost_index,
                'transportation_cost_index': cost_data.transportation_cost_index,
                'food_cost_index': cost_data.food_cost_index,
                'healthcare_cost_index': cost_data.healthcare_cost_index,
                'utilities_cost_index': cost_data.utilities_cost_index,
                'overall_cost_index': cost_data.overall_cost_index,
                'year': cost_data.year,
                'last_updated': cost_data.last_updated.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cost of living data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error while retrieving cost of living data'
        }), 500

@real_time_salary_bp.route('/job-market', methods=['POST'])
@cross_origin()
def get_job_market_data():
    """
    Get job market data from Indeed API
    
    Request body:
    {
        "location": "Atlanta",
        "occupation": "Software Engineer"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "location": "Atlanta",
            "occupation": "Software Engineer",
            "job_count": 150,
            "average_salary": 78000,
            "salary_range": {
                "min": 60000,
                "max": 120000
            },
            "demand_score": 85.5,
            "last_updated": "2025-01-27T10:30:00"
        }
    }
    """
    try:
        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract parameters
        location = data.get('location')
        occupation = data.get('occupation')
        
        # Validate required fields
        if not location:
            return jsonify({
                'success': False,
                'error': 'Location is required'
            }), 400
        
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        # Get job market data
        job_data = salary_service.get_indeed_job_market_data(location, occupation)
        
        if not job_data:
            return jsonify({
                'success': False,
                'error': 'Unable to retrieve job market data'
            }), 404
        
        logger.info(f"Job market data retrieved for {location}, occupation: {occupation}")
        
        return jsonify({
            'success': True,
            'data': {
                'location': job_data.location,
                'occupation': job_data.occupation,
                'job_count': job_data.job_count,
                'average_salary': job_data.average_salary,
                'salary_range': {
                    'min': job_data.salary_range_min,
                    'max': job_data.salary_range_max
                },
                'demand_score': job_data.demand_score,
                'last_updated': job_data.last_updated.isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting job market data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error while retrieving job market data'
        }), 500

@real_time_salary_bp.route('/cache/status', methods=['GET'])
@cross_origin()
def get_cache_status():
    """
    Get Redis cache status and statistics
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "available",
            "connected_clients": 5,
            "used_memory_human": "2.5M",
            "keyspace_hits": 1500,
            "keyspace_misses": 200
        }
    }
    """
    try:
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        # Get cache status
        cache_status = salary_service.get_cache_status()
        
        return jsonify({
            'success': True,
            'data': cache_status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting cache status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error while retrieving cache status'
        }), 500

@real_time_salary_bp.route('/cache/clear', methods=['POST'])
@cross_origin()
def clear_cache():
    """
    Clear Redis cache entries
    
    Request body:
    {
        "pattern": "salary_data:*"  // Optional, defaults to "salary_data:*"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "cleared_entries": 25,
            "pattern": "salary_data:*"
        }
    }
    """
    try:
        # Get request data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Extract parameters
        pattern = data.get('pattern', 'salary_data:*')
        
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        # Clear cache
        success = salary_service.clear_cache(pattern)
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'message': 'Cache cleared successfully',
                    'pattern': pattern
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
            'error': 'Internal server error while clearing cache'
        }), 500

@real_time_salary_bp.route('/locations', methods=['GET'])
@cross_origin()
def get_available_locations():
    """
    Get list of available locations for salary data
    
    Returns:
    {
        "success": true,
        "data": {
            "locations": [
                "Atlanta",
                "Houston",
                "Washington DC",
                "Dallas-Fort Worth",
                "New York City",
                "Philadelphia",
                "Chicago",
                "Charlotte",
                "Miami",
                "Baltimore"
            ],
            "total_count": 10
        }
    }
    """
    try:
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        locations = salary_service.target_msas
        
        return jsonify({
            'success': True,
            'data': {
                'locations': locations,
                'total_count': len(locations)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting available locations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error while retrieving locations'
        }), 500

@real_time_salary_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for real-time salary data service
    
    Returns:
    {
        "success": true,
        "data": {
            "status": "healthy",
            "service": "real_time_salary_data",
            "available_apis": ["BLS", "Census", "FRED", "Indeed"],
            "cache_status": "available",
            "supported_locations": 10
        }
    }
    """
    try:
        # Initialize service
        salary_service = SalaryDataIntegrationService()
        
        # Get cache status
        cache_status = salary_service.get_cache_status()
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'service': 'real_time_salary_data',
                'available_apis': ['BLS', 'Census', 'FRED', 'Indeed'],
                'cache_status': cache_status.get('status', 'unknown'),
                'supported_locations': len(salary_service.target_msas),
                'api_keys_configured': {
                    'bls': bool(salary_service.bls_api_key),
                    'census': bool(salary_service.census_api_key),
                    'fred': bool(salary_service.fred_api_key),
                    'indeed': bool(salary_service.indeed_api_key)
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
                'service': 'real_time_salary_data',
                'error': str(e)
            }
        }), 500 