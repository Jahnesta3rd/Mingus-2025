#!/usr/bin/env python3
"""
Mingus Application - Optimized Daily Outlook API
High-performance Daily Outlook API with comprehensive caching and optimization
"""

import time
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, g, Response
from functools import wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import optimization modules
from backend.services.cache_manager import cache_manager, CacheStrategy, get_daily_outlook_cache, set_daily_outlook_cache
from backend.optimization.database_optimization import DatabaseOptimizer
from backend.optimization.api_performance import APIPerformanceOptimizer
from backend.monitoring.performance_monitoring import monitor_performance, get_performance_monitor
from backend.services.daily_outlook_service import DailyOutlookService
from backend.services.daily_outlook_content_service import DailyOutlookContentService
from backend.models.daily_outlook import DailyOutlook
from backend.models.database import db

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
optimized_daily_outlook_bp = Blueprint('optimized_daily_outlook', __name__)

# Initialize optimization services
db_optimizer = None
api_optimizer = None
daily_outlook_service = None
content_service = None

def initialize_services(redis_client, db_session):
    """Initialize optimization services"""
    global db_optimizer, api_optimizer, daily_outlook_service, content_service
    
    db_optimizer = DatabaseOptimizer(db_session)
    api_optimizer = APIPerformanceOptimizer(redis_client)
    daily_outlook_service = DailyOutlookService()
    content_service = DailyOutlookContentService()

# Performance monitoring decorator
def track_performance(metric_name: str):
    """Decorator for tracking API performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Record performance metrics
                duration = time.time() - start_time
                performance_monitor = get_performance_monitor()
                if performance_monitor:
                    performance_monitor.record_request('GET', metric_name, 200, duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor = get_performance_monitor()
                if performance_monitor:
                    performance_monitor.record_request('GET', metric_name, 500, duration)
                
                raise e
        
        return wrapper
    return decorator

@optimized_daily_outlook_bp.route('/api/v2/daily-outlook/<int:user_id>', methods=['GET'])
@api_optimizer.rate_limit_decorator('/api/daily-outlook')
@api_optimizer.compression_decorator()
@api_optimizer.etag_decorator(lambda user_id: f"daily_outlook:{user_id}:{date.today()}")
@track_performance('daily_outlook')
def get_daily_outlook_optimized(user_id: int):
    """
    Get optimized daily outlook for user
    
    Features:
    - Redis caching with smart invalidation
    - Database query optimization
    - Response compression
    - ETag caching
    - Rate limiting
    - Performance monitoring
    """
    try:
        target_date = request.args.get('date', date.today().isoformat())
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Check cache first
        cached_outlook = get_daily_outlook_cache(user_id, target_date)
        if cached_outlook:
            logger.info(f"Cache hit for daily outlook user {user_id} date {target_date}")
            return jsonify({
                'success': True,
                'data': cached_outlook,
                'cached': True,
                'timestamp': datetime.now().isoformat()
            })
        
        # Generate new daily outlook
        start_time = time.time()
        
        # Get user data with optimized query
        user_data = db_optimizer.get_user_daily_outlook_optimized(user_id, target_date_obj)
        
        if not user_data:
            # Generate new outlook if not exists
            outlook_data = _generate_daily_outlook_data(user_id, target_date_obj)
        else:
            outlook_data = user_data
        
        # Cache the result
        set_daily_outlook_cache(user_id, target_date, outlook_data)
        
        # Record performance metrics
        load_time = time.time() - start_time
        performance_monitor = get_performance_monitor()
        if performance_monitor:
            performance_monitor.record_daily_outlook_load(load_time, user_id)
        
        logger.info(f"Generated daily outlook for user {user_id} in {load_time:.3f}s")
        
        return jsonify({
            'success': True,
            'data': outlook_data,
            'cached': False,
            'load_time': load_time,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting daily outlook for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get daily outlook',
            'message': str(e)
        }), 500

@optimized_daily_outlook_bp.route('/api/v2/daily-outlook/<int:user_id>/balance-score', methods=['GET'])
@api_optimizer.rate_limit_decorator('/api/balance-score')
@api_optimizer.compression_decorator()
@track_performance('balance_score')
def get_balance_score_optimized(user_id: int):
    """
    Get optimized balance score for user
    
    Features:
    - Pre-computed balance scores
    - Cache-first strategy
    - Performance monitoring
    """
    try:
        # Check cache first
        cached_score = cache_manager.get(CacheStrategy.USER_BALANCE_SCORE, str(user_id))
        if cached_score:
            logger.info(f"Cache hit for balance score user {user_id}")
            return jsonify({
                'success': True,
                'data': cached_score,
                'cached': True,
                'timestamp': datetime.now().isoformat()
            })
        
        # Calculate balance score
        start_time = time.time()
        
        balance_score, individual_scores = daily_outlook_service.calculate_balance_score(user_id)
        
        score_data = {
            'balance_score': balance_score,
            'individual_scores': individual_scores.to_dict(),
            'calculated_at': datetime.now().isoformat()
        }
        
        # Cache the result
        cache_manager.set(CacheStrategy.USER_BALANCE_SCORE, str(user_id), score_data)
        
        # Record performance metrics
        calculation_time = time.time() - start_time
        performance_monitor = get_performance_monitor()
        if performance_monitor:
            performance_monitor.record_balance_score_calculation(calculation_time, user_id)
        
        logger.info(f"Calculated balance score for user {user_id} in {calculation_time:.3f}s")
        
        return jsonify({
            'success': True,
            'data': score_data,
            'cached': False,
            'calculation_time': calculation_time,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error calculating balance score for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate balance score',
            'message': str(e)
        }), 500

@optimized_daily_outlook_bp.route('/api/v2/daily-outlook/<int:user_id>/peer-comparison', methods=['GET'])
@api_optimizer.rate_limit_decorator('/api/peer-comparison')
@api_optimizer.compression_decorator()
@track_performance('peer_comparison')
def get_peer_comparison_optimized(user_id: int):
    """
    Get optimized peer comparison data
    
    Features:
    - Pre-computed peer data
    - Tier and location-based comparison
    - Cache optimization
    """
    try:
        target_date = request.args.get('date', date.today().isoformat())
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        # Get user info for comparison
        user_query = db_optimizer.db_session.execute(
            "SELECT tier, location FROM users WHERE id = :user_id",
            {'user_id': user_id}
        ).fetchone()
        
        if not user_query:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user_tier, user_location = user_query
        
        # Check cache for peer comparison data
        cache_key = f"{user_tier}:{user_location}"
        cached_comparison = cache_manager.get(
            CacheStrategy.PEER_COMPARISON, 
            cache_key, 
            {"date": target_date}
        )
        
        if cached_comparison:
            logger.info(f"Cache hit for peer comparison {cache_key}")
            return jsonify({
                'success': True,
                'data': cached_comparison,
                'cached': True,
                'timestamp': datetime.now().isoformat()
            })
        
        # Get peer comparison data with optimized query
        start_time = time.time()
        peer_data = db_optimizer.get_peer_comparison_data_optimized(
            user_id, user_tier, user_location, target_date_obj
        )
        
        # Calculate comparison metrics
        comparison_data = _calculate_peer_comparison_metrics(peer_data, user_id)
        
        # Cache the result
        cache_manager.set(
            CacheStrategy.PEER_COMPARISON,
            cache_key,
            comparison_data,
            {"date": target_date}
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Generated peer comparison for user {user_id} in {processing_time:.3f}s")
        
        return jsonify({
            'success': True,
            'data': comparison_data,
            'cached': False,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting peer comparison for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get peer comparison',
            'message': str(e)
        }), 500

@optimized_daily_outlook_bp.route('/api/v2/daily-outlook/batch', methods=['POST'])
@api_optimizer.rate_limit_decorator('/api/batch')
@api_optimizer.compression_decorator()
@track_performance('batch_daily_outlook')
def batch_get_daily_outlooks():
    """
    Batch get daily outlooks for multiple users
    
    Features:
    - Single request for multiple users
    - Parallel processing
    - Optimized database queries
    """
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        target_date = data.get('date', date.today().isoformat())
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        if not user_ids:
            return jsonify({'success': False, 'error': 'No user IDs provided'}), 400
        
        if len(user_ids) > 50:  # Limit batch size
            return jsonify({'success': False, 'error': 'Batch size too large (max 50)'}), 400
        
        start_time = time.time()
        
        # Use optimized batch query
        outlooks = db_optimizer.batch_get_daily_outlooks(user_ids, target_date_obj)
        
        # Fill in missing outlooks with generated data
        results = {}
        for user_id in user_ids:
            if user_id in outlooks:
                results[user_id] = outlooks[user_id]
            else:
                # Generate outlook for missing users
                outlook_data = _generate_daily_outlook_data(user_id, target_date_obj)
                results[user_id] = outlook_data
        
        processing_time = time.time() - start_time
        logger.info(f"Batch processed {len(user_ids)} users in {processing_time:.3f}s")
        
        return jsonify({
            'success': True,
            'data': results,
            'total_users': len(user_ids),
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in batch daily outlook request: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process batch request',
            'message': str(e)
        }), 500

@optimized_daily_outlook_bp.route('/api/v2/daily-outlook/<int:user_id>/analytics', methods=['GET'])
@api_optimizer.rate_limit_decorator('/api/analytics')
@api_optimizer.compression_decorator()
@track_performance('daily_outlook_analytics')
def get_daily_outlook_analytics(user_id: int):
    """
    Get daily outlook analytics for user
    
    Features:
    - Historical trend analysis
    - Performance metrics
    - Optimized aggregation queries
    """
    try:
        days = int(request.args.get('days', 30))
        
        # Get analytics with optimized query
        start_time = time.time()
        analytics_data = db_optimizer.get_balance_score_analytics_optimized(user_id, days)
        
        # Get outlook history
        outlook_history = db_optimizer.get_user_outlook_history_optimized(user_id, days)
        
        # Calculate trends
        trends = _calculate_analytics_trends(outlook_history, analytics_data)
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'data': {
                'analytics': analytics_data,
                'trends': trends,
                'outlook_history': outlook_history[-10:],  # Last 10 outlooks
                'period_days': days
            },
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics for user {user_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get analytics',
            'message': str(e)
        }), 500

@optimized_daily_outlook_bp.route('/api/v2/daily-outlook/performance', methods=['GET'])
def get_performance_metrics():
    """Get API performance metrics"""
    try:
        performance_monitor = get_performance_monitor()
        if not performance_monitor:
            return jsonify({'error': 'Performance monitor not available'}), 503
        
        # Get performance metrics
        metrics = performance_monitor.get_performance_metrics('1h')
        system_health = performance_monitor.get_system_health()
        
        # Get cache metrics
        cache_metrics = cache_manager.get_metrics()
        
        # Get database metrics
        db_metrics = db_optimizer.get_performance_metrics()
        
        # Get API metrics
        api_metrics = api_optimizer.get_performance_metrics()
        
        return jsonify({
            'success': True,
            'data': {
                'performance_metrics': metrics,
                'system_health': {
                    'status': system_health.status,
                    'alerts': system_health.alerts,
                    'recommendations': system_health.recommendations
                },
                'cache_metrics': cache_metrics,
                'database_metrics': db_metrics,
                'api_metrics': api_metrics
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get performance metrics',
            'message': str(e)
        }), 500

def _generate_daily_outlook_data(user_id: int, target_date: date) -> Dict[str, Any]:
    """Generate daily outlook data for user"""
    try:
        # Use content service to generate outlook
        outlook_data = content_service.generate_daily_outlook(user_id)
        
        # Add metadata
        outlook_data.update({
            'user_id': user_id,
            'date': target_date.isoformat(),
            'generated_at': datetime.now().isoformat()
        })
        
        return outlook_data
        
    except Exception as e:
        logger.error(f"Error generating daily outlook for user {user_id}: {e}")
        return {
            'user_id': user_id,
            'date': target_date.isoformat(),
            'error': 'Failed to generate outlook',
            'generated_at': datetime.now().isoformat()
        }

def _calculate_peer_comparison_metrics(peer_data: List[Dict[str, Any]], user_id: int) -> Dict[str, Any]:
    """Calculate peer comparison metrics"""
    if not peer_data:
        return {'error': 'No peer data available'}
    
    # Extract balance scores
    balance_scores = [peer['balance_score'] for peer in peer_data]
    
    # Calculate statistics
    avg_score = sum(balance_scores) / len(balance_scores)
    min_score = min(balance_scores)
    max_score = max(balance_scores)
    
    # Calculate percentiles
    sorted_scores = sorted(balance_scores)
    n = len(sorted_scores)
    
    percentiles = {
        'p25': sorted_scores[int(n * 0.25)] if n > 0 else 0,
        'p50': sorted_scores[int(n * 0.50)] if n > 0 else 0,
        'p75': sorted_scores[int(n * 0.75)] if n > 0 else 0,
        'p90': sorted_scores[int(n * 0.90)] if n > 0 else 0
    }
    
    return {
        'peer_count': len(peer_data),
        'average_score': round(avg_score, 2),
        'min_score': min_score,
        'max_score': max_score,
        'percentiles': percentiles,
        'calculated_at': datetime.now().isoformat()
    }

def _calculate_analytics_trends(outlook_history: List[Dict[str, Any]], analytics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate analytics trends"""
    if not outlook_history:
        return {'error': 'No historical data available'}
    
    # Calculate trend direction
    if len(outlook_history) >= 2:
        recent_scores = [outlook['balance_score'] for outlook in outlook_history[-7:]]  # Last 7 days
        older_scores = [outlook['balance_score'] for outlook in outlook_history[-14:-7]]  # Previous 7 days
        
        if recent_scores and older_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            trend_direction = 'improving' if recent_avg > older_avg else 'declining'
            trend_magnitude = abs(recent_avg - older_avg)
        else:
            trend_direction = 'stable'
            trend_magnitude = 0
    else:
        trend_direction = 'insufficient_data'
        trend_magnitude = 0
    
    return {
        'trend_direction': trend_direction,
        'trend_magnitude': round(trend_magnitude, 2),
        'data_points': len(outlook_history),
        'calculated_at': datetime.now().isoformat()
    }

# Health check endpoint
@optimized_daily_outlook_bp.route('/api/v2/daily-outlook/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check cache health
        cache_health = cache_manager.health_check()
        
        # Check database health
        db_health = db_optimizer.health_check() if hasattr(db_optimizer, 'health_check') else {'status': 'unknown'}
        
        # Check API health
        api_health = api_optimizer.health_check()
        
        overall_status = 'healthy'
        if (cache_health['status'] != 'healthy' or 
            db_health.get('status') != 'healthy' or 
            api_health['status'] != 'healthy'):
            overall_status = 'degraded'
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'components': {
                'cache': cache_health,
                'database': db_health,
                'api': api_health
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
