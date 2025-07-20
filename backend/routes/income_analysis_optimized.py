"""
Optimized Income Analysis Routes for Production Deployment
Ultra-budget optimized endpoints with caching, rate limiting, and performance monitoring
"""

from flask import Blueprint, request, jsonify, render_template, current_app, g
from flask_cors import cross_origin
from loguru import logger
from typing import Dict, Any, Optional, Union
import time
import hashlib
import json
import threading
from functools import wraps
from collections import defaultdict, deque
import traceback

from ..ml.models.income_comparator_optimized import get_income_comparator, EducationLevel, PerformanceMonitor
from ..middleware.auth import require_auth
from ..utils.auth_decorators import get_current_user_id

income_analysis_bp = Blueprint('income_analysis', __name__)

# Performance monitoring
perf_monitor = PerformanceMonitor()

# Rate limiting for ultra-budget deployment
class SimpleRateLimiter:
    """Simple in-memory rate limiter for ultra-budget deployment"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed"""
        now = time.time()
        
        with self.lock:
            # Clean old requests
            if identifier in self.requests:
                while self.requests[identifier] and self.requests[identifier][0] < now - self.window_seconds:
                    self.requests[identifier].popleft()
            
            # Check if under limit
            if len(self.requests[identifier]) >= self.max_requests:
                return False
            
            # Add current request
            self.requests[identifier].append(now)
            return True
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        now = time.time()
        
        with self.lock:
            if identifier not in self.requests:
                return self.max_requests
            
            # Clean old requests
            while self.requests[identifier] and self.requests[identifier][0] < now - self.window_seconds:
                self.requests[identifier].popleft()
            
            return max(0, self.max_requests - len(self.requests[identifier]))

# Global rate limiter
rate_limiter = SimpleRateLimiter(max_requests=20, window_seconds=60)  # 20 requests per minute

# Response caching for ultra-budget deployment
class SimpleResponseCache:
    """Simple in-memory response cache for ultra-budget deployment"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.timestamps = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Dict]:
        """Get cached response"""
        now = time.time()
        
        with self.lock:
            if key in self.cache:
                if now - self.timestamps[key] < self.ttl_seconds:
                    return self.cache[key]
                else:
                    # Expired, remove
                    del self.cache[key]
                    del self.timestamps[key]
        
        return None
    
    def set(self, key: str, value: Dict):
        """Set cached response"""
        now = time.time()
        
        with self.lock:
            # Remove oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = now
    
    def clear(self):
        """Clear cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()

# Global response cache
response_cache = SimpleResponseCache(max_size=500, ttl_seconds=1800)  # 30 minutes TTL

def rate_limit(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get client identifier (IP or user ID)
        client_id = request.remote_addr
        if hasattr(g, 'user_id') and g.user_id:
            client_id = f"user_{g.user_id}"
        
        if not rate_limiter.is_allowed(client_id):
            remaining = rate_limiter.get_remaining(client_id)
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'retry_after': 60,
                'remaining_requests': remaining
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

def cache_response(ttl_seconds: int = 1800):
    """Response caching decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from request
            cache_key = _generate_cache_key(request)
            
            # Check cache
            cached_response = response_cache.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for {cache_key}")
                return jsonify(cached_response)
            
            # Execute function
            response = f(*args, **kwargs)
            
            # Cache successful responses
            if response.status_code == 200:
                try:
                    response_data = response.get_json()
                    if response_data and response_data.get('success'):
                        response_cache.set(cache_key, response_data)
                        logger.info(f"Cached response for {cache_key}")
                except Exception as e:
                    logger.warning(f"Failed to cache response: {e}")
            
            return response
        return decorated_function
    return decorator

def _generate_cache_key(request) -> str:
    """Generate cache key from request"""
    # Include relevant request data for cache key
    key_data = {
        'method': request.method,
        'path': request.path,
        'args': dict(request.args),
        'json': request.get_json() if request.is_json else None,
        'form': dict(request.form) if request.form else None
    }
    
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()

def validate_income_data(data: Dict[str, Any]) -> tuple[bool, str, Dict[str, Any]]:
    """Validate income analysis request data"""
    try:
        # Extract and validate required fields
        current_salary = data.get('current_salary')
        age_range = data.get('age_range')
        education_level = data.get('education_level')
        location = data.get('location')
        
        # Validate required fields
        required_fields = ['age_range', 'education_level', 'location']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return False, f'Missing required fields: {", ".join(missing_fields)}', {}
        
        # Validate salary if provided
        if current_salary is not None:
            try:
                current_salary = int(current_salary)
                if current_salary <= 0:
                    return False, 'Salary must be a positive number', {}
                if current_salary > 1000000:  # Reasonable upper limit
                    return False, 'Salary value seems unrealistic', {}
            except (ValueError, TypeError):
                return False, 'Invalid salary value', {}
        else:
            # Use default for demonstration
            current_salary = 65000
        
        # Validate education level
        education_mapping = {
            'high_school': EducationLevel.HIGH_SCHOOL,
            'some_college': EducationLevel.SOME_COLLEGE,
            'bachelors': EducationLevel.BACHELORS,
            'masters': EducationLevel.MASTERS,
            'doctorate': EducationLevel.DOCTORATE
        }
        
        mapped_education = education_mapping.get(education_level)
        if not mapped_education:
            return False, 'Invalid education level', {}
        
        # Validate age range
        valid_age_ranges = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
        if age_range not in valid_age_ranges:
            return False, 'Invalid age range', {}
        
        # Validate location (basic check)
        if not location or len(location.strip()) == 0:
            return False, 'Location is required', {}
        
        validated_data = {
            'current_salary': current_salary,
            'age_range': age_range,
            'education_level': mapped_education,
            'location': location.strip()
        }
        
        return True, '', validated_data
        
    except Exception as e:
        logger.error(f"Data validation error: {e}")
        return False, 'Invalid request data', {}

@income_analysis_bp.route('/form', methods=['GET'])
@cross_origin()
def income_analysis_form():
    """
    Display the income analysis form
    
    Returns:
        Rendered HTML template for income analysis form
    """
    start_time = time.time()
    
    try:
        response = render_template('income_analysis_form.html')
        perf_monitor.record_metric("form_render", time.time() - start_time)
        return response
    except Exception as e:
        perf_monitor.record_metric("form_render_error", time.time() - start_time)
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
    start_time = time.time()
    
    try:
        response = render_template('income_analysis_results.html')
        perf_monitor.record_metric("results_render", time.time() - start_time)
        return response
    except Exception as e:
        perf_monitor.record_metric("results_render_error", time.time() - start_time)
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
    start_time = time.time()
    
    try:
        response = render_template('comprehensive_career_dashboard.html')
        perf_monitor.record_metric("dashboard_render", time.time() - start_time)
        return response
    except Exception as e:
        perf_monitor.record_metric("dashboard_render_error", time.time() - start_time)
        logger.error(f"Error rendering comprehensive dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error loading comprehensive dashboard'
        }), 500

@income_analysis_bp.route('/analyze', methods=['POST'])
@cross_origin()
@rate_limit
@cache_response(ttl_seconds=1800)  # Cache for 30 minutes
def analyze_income():
    """
    Perform optimized income comparison analysis
    
    Request body:
    {
        "current_salary": 65000,
        "age_range": "25-34",
        "education_level": "bachelors",
        "location": "atlanta"
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
                "next_steps": [...],
                "calculation_time": 0.045
            }
        },
        "performance": {
            "cache_hit": false,
            "rate_limit_remaining": 19
        }
    }
    """
    start_time = time.time()
    
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate data
        is_valid, error_message, validated_data = validate_income_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_message
            }), 400
        
        # Get singleton instance of income comparator
        income_comparator = get_income_comparator()
        
        # Perform income analysis
        analysis_start = time.time()
        income_analysis_result = income_comparator.analyze_income(
            user_income=validated_data['current_salary'],
            location=validated_data['location'],
            education_level=validated_data['education_level'],
            age_group=validated_data['age_range']
        )
        analysis_time = time.time() - analysis_start
        
        # Format response
        response_data = {
            'overall_percentile': round(income_analysis_result.overall_percentile, 1),
            'career_opportunity_score': round(income_analysis_result.career_opportunity_score, 1),
            'primary_gap': {
                'group_name': income_analysis_result.primary_gap.group_name,
                'income_gap': income_analysis_result.primary_gap.income_gap,
                'gap_percentage': round(income_analysis_result.primary_gap.gap_percentage, 1),
                'motivational_insight': income_analysis_result.primary_gap.motivational_insight
            },
            'comparisons': [
                {
                    'group_name': comp.group_name,
                    'median_income': comp.median_income,
                    'percentile_rank': round(comp.percentile_rank, 1),
                    'income_gap': comp.income_gap,
                    'gap_percentage': round(comp.gap_percentage, 1),
                    'context_message': comp.context_message,
                    'motivational_insight': comp.motivational_insight,
                    'action_item': comp.action_item
                }
                for comp in income_analysis_result.comparisons
            ],
            'motivational_summary': income_analysis_result.motivational_summary,
            'action_plan': income_analysis_result.action_plan,
            'next_steps': income_analysis_result.next_steps,
            'calculation_time': round(analysis_time, 3)
        }
        
        # Get performance metrics
        client_id = request.remote_addr
        if hasattr(g, 'user_id') and g.user_id:
            client_id = f"user_{g.user_id}"
        
        performance_data = {
            'cache_hit': False,  # Will be set by cache decorator
            'rate_limit_remaining': rate_limiter.get_remaining(client_id),
            'analysis_time_ms': round(analysis_time * 1000, 1)
        }
        
        total_time = time.time() - start_time
        perf_monitor.record_metric("income_analysis_total", total_time)
        
        logger.info(f"Income analysis completed in {total_time:.3f}s (analysis: {analysis_time:.3f}s)")
        
        return jsonify({
            'success': True,
            'data': {
                'income_comparison': response_data
            },
            'performance': performance_data
        })
        
    except Exception as e:
        total_time = time.time() - start_time
        perf_monitor.record_metric("income_analysis_error", total_time)
        
        logger.error(f"Income analysis failed after {total_time:.3f}s: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': 'An error occurred during income analysis',
            'details': str(e) if current_app.debug else 'Please try again later'
        }), 500

@income_analysis_bp.route('/demo', methods=['GET'])
@cross_origin()
@rate_limit
@cache_response(ttl_seconds=3600)  # Cache demo for 1 hour
def demo_analysis():
    """
    Provide demo income analysis for testing
    
    Returns:
        Demo income analysis results
    """
    start_time = time.time()
    
    try:
        # Get singleton instance of income comparator
        income_comparator = get_income_comparator()
        
        # Demo data
        demo_data = {
            'current_salary': 65000,
            'age_range': '25-34',
            'education_level': EducationLevel.BACHELORS,
            'location': 'atlanta'
        }
        
        # Perform analysis
        analysis_start = time.time()
        income_analysis_result = income_comparator.analyze_income(
            user_income=demo_data['current_salary'],
            location=demo_data['location'],
            education_level=demo_data['education_level'],
            age_group=demo_data['age_range']
        )
        analysis_time = time.time() - analysis_start
        
        # Format response
        response_data = {
            'overall_percentile': round(income_analysis_result.overall_percentile, 1),
            'career_opportunity_score': round(income_analysis_result.career_opportunity_score, 1),
            'primary_gap': {
                'group_name': income_analysis_result.primary_gap.group_name,
                'income_gap': income_analysis_result.primary_gap.income_gap,
                'gap_percentage': round(income_analysis_result.primary_gap.gap_percentage, 1),
                'motivational_insight': income_analysis_result.primary_gap.motivational_insight
            },
            'comparisons': [
                {
                    'group_name': comp.group_name,
                    'median_income': comp.median_income,
                    'percentile_rank': round(comp.percentile_rank, 1),
                    'income_gap': comp.income_gap,
                    'gap_percentage': round(comp.gap_percentage, 1),
                    'context_message': comp.context_message,
                    'motivational_insight': comp.motivational_insight,
                    'action_item': comp.action_item
                }
                for comp in income_analysis_result.comparisons
            ],
            'motivational_summary': income_analysis_result.motivational_summary,
            'action_plan': income_analysis_result.action_plan,
            'next_steps': income_analysis_result.next_steps,
            'calculation_time': round(analysis_time, 3)
        }
        
        total_time = time.time() - start_time
        perf_monitor.record_metric("demo_analysis", total_time)
        
        return jsonify({
            'success': True,
            'data': {
                'income_comparison': response_data
            },
            'demo': True,
            'performance': {
                'analysis_time_ms': round(analysis_time * 1000, 1)
            }
        })
        
    except Exception as e:
        total_time = time.time() - start_time
        perf_monitor.record_metric("demo_analysis_error", total_time)
        
        logger.error(f"Demo analysis failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Demo analysis failed'
        }), 500

@income_analysis_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint for monitoring
    
    Returns:
        Health status and performance metrics
    """
    try:
        # Get performance statistics
        perf_stats = perf_monitor.get_stats()
        
        # Get income comparator stats
        income_comparator = get_income_comparator()
        comparator_stats = income_comparator.get_performance_stats()
        
        # Check cache status
        cache_status = {
            'response_cache_size': len(response_cache.cache),
            'rate_limiter_active_requests': sum(len(requests) for requests in rate_limiter.requests.values())
        }
        
        # Calculate average response times
        avg_analysis_time = perf_stats.get('income_analysis', 0)
        avg_total_time = perf_stats.get('income_analysis_total', 0)
        
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'performance': {
                'avg_analysis_time_ms': round(avg_analysis_time * 1000, 1),
                'avg_total_time_ms': round(avg_total_time * 1000, 1),
                'target_analysis_time_ms': 500,
                'target_total_time_ms': 3000
            },
            'cache': cache_status,
            'rate_limiter': {
                'active_clients': len(rate_limiter.requests)
            },
            'comparator_stats': {
                'avg_percentile_calculation_ms': round(comparator_stats.get('percentile_calculation', 0) * 1000, 1),
                'cache_hit_rate': 'N/A'  # Would need more sophisticated tracking
            }
        }
        
        # Check if performance is within targets
        if avg_analysis_time > 0.5:  # 500ms target
            health_status['status'] = 'degraded'
            health_status['warnings'] = ['Analysis time exceeds target']
        
        if avg_total_time > 3.0:  # 3s target
            health_status['status'] = 'degraded'
            health_status['warnings'] = health_status.get('warnings', []) + ['Total time exceeds target']
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500

@income_analysis_bp.route('/metrics', methods=['GET'])
@cross_origin()
def get_metrics():
    """
    Get detailed performance metrics for monitoring
    
    Returns:
        Detailed performance metrics
    """
    try:
        # Get all performance statistics
        perf_stats = perf_monitor.get_stats()
        
        # Get income comparator stats
        income_comparator = get_income_comparator()
        comparator_stats = income_comparator.get_performance_stats()
        
        # Format metrics for monitoring
        metrics = {
            'timestamp': time.time(),
            'endpoint_metrics': {
                'form_render_avg_ms': round(perf_stats.get('form_render', 0) * 1000, 1),
                'results_render_avg_ms': round(perf_stats.get('results_render', 0) * 1000, 1),
                'dashboard_render_avg_ms': round(perf_stats.get('dashboard_render', 0) * 1000, 1),
                'income_analysis_avg_ms': round(perf_stats.get('income_analysis', 0) * 1000, 1),
                'income_analysis_total_avg_ms': round(perf_stats.get('income_analysis_total', 0) * 1000, 1),
                'demo_analysis_avg_ms': round(perf_stats.get('demo_analysis', 0) * 1000, 1)
            },
            'error_metrics': {
                'form_render_errors': len([k for k in perf_stats.keys() if 'form_render_error' in k]),
                'results_render_errors': len([k for k in perf_stats.keys() if 'results_render_error' in k]),
                'dashboard_render_errors': len([k for k in perf_stats.keys() if 'dashboard_render_error' in k]),
                'analysis_errors': len([k for k in perf_stats.keys() if 'analysis_error' in k])
            },
            'cache_metrics': {
                'response_cache_size': len(response_cache.cache),
                'response_cache_max_size': response_cache.max_size,
                'response_cache_ttl_seconds': response_cache.ttl_seconds
            },
            'rate_limiter_metrics': {
                'active_clients': len(rate_limiter.requests),
                'max_requests_per_window': rate_limiter.max_requests,
                'window_seconds': rate_limiter.window_seconds
            },
            'comparator_metrics': {
                'initialization_time_ms': round(comparator_stats.get('initialization', 0) * 1000, 1),
                'demographic_data_init_ms': round(comparator_stats.get('demographic_data_init', 0) * 1000, 1),
                'metro_data_init_ms': round(comparator_stats.get('metro_data_init', 0) * 1000, 1)
            }
        }
        
        return jsonify(metrics)
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'timestamp': time.time()
        }), 500

@income_analysis_bp.route('/cache/clear', methods=['POST'])
@cross_origin()
def clear_cache():
    """
    Clear all caches (admin function)
    
    Returns:
        Cache clear status
    """
    try:
        # Clear response cache
        response_cache.clear()
        
        # Clear income comparator cache
        income_comparator = get_income_comparator()
        income_comparator.clear_cache()
        
        logger.info("All caches cleared")
        
        return jsonify({
            'success': True,
            'message': 'All caches cleared successfully',
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Cache clear failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 