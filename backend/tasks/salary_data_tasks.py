"""
Celery Tasks for Real-time Salary Data Processing
Integrates with existing MINGUS Celery worker configuration
"""

import os
import uuid
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal

# Celery imports
from celery import Celery, current_task
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError

# Database imports
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.exc import SQLAlchemyError

# MINGUS imports
from ..database import get_db_session
from ..models.salary_data import (
    SalaryBenchmark, MarketData, ConfidenceScore, SalaryDataCache
)
from ..services.enhanced_salary_data_service import (
    EnhancedSalaryDataService, SalaryDataRequest, CacheStrategy, DataSource
)
from ..services.cache_service import CacheService
from ..services.api_client import AsyncAPIClient, APISource

# Configure logging
logger = get_task_logger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Celery app
celery_app = Celery('salary_data_tasks')
celery_app.config_from_object('celeryconfig')

class SalaryDataTasks:
    """Celery tasks for salary data processing"""
    
    @staticmethod
    @celery_app.task(
        bind=True,
        name='backend.tasks.salary_data_tasks.fetch_salary_data',
        queue='salary_data',
        routing_key='salary_data',
        priority=5,
        rate_limit='10/m',
        time_limit=300,
        soft_time_limit=240,
        autoretry_for=(Exception,),
        retry_kwargs={'max_retries': 3, 'countdown': 60},
        retry_backoff=True
    )
    def fetch_salary_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch salary data from multiple sources with caching
        
        Args:
            request_data: Salary data request parameters
            
        Returns:
            Comprehensive salary data response
        """
        task_id = current_task.request.id
        logger.info(f"Starting salary data fetch task {task_id}")
        
        try:
            # Initialize services
            db_session = get_db_session()
            salary_service = EnhancedSalaryDataService(db_session)
            
            # Create request object
            request = SalaryDataRequest(**request_data)
            
            # Fetch salary data
            response = await salary_service.get_salary_data(request)
            
            # Log success
            logger.info(f"Salary data fetch completed for task {task_id}")
            
            return {
                'task_id': task_id,
                'status': 'success',
                'cache_hit': response.cache_hit,
                'processing_time_ms': response.processing_time_ms,
                'data_count': len(response.salary_benchmarks),
                'data_freshness': response.data_freshness,
                'recommendations_count': len(response.recommendations) if response.recommendations else 0
            }
            
        except Exception as e:
            logger.error(f"Error in salary data fetch task {task_id}: {e}")
            
            # Retry logic
            try:
                self.retry(countdown=60, max_retries=3)
            except MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for task {task_id}")
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e),
                    'max_retries_exceeded': True
                }
    
    @staticmethod
    @celery_app.task(
        bind=True,
        name='backend.tasks.salary_data_tasks.refresh_salary_cache',
        queue='salary_data',
        routing_key='salary_data',
        priority=3,
        rate_limit='5/m',
        time_limit=600,
        soft_time_limit=540,
        autoretry_for=(Exception,),
        retry_kwargs={'max_retries': 2, 'countdown': 120},
        retry_backoff=True
    )
    def refresh_salary_cache(self, cache_pattern: str = "salary_data:*") -> Dict[str, Any]:
        """
        Refresh salary data cache entries
        
        Args:
            cache_pattern: Redis cache pattern to refresh
            
        Returns:
            Cache refresh results
        """
        task_id = current_task.request.id
        logger.info(f"Starting salary cache refresh task {task_id}")
        
        try:
            # Initialize services
            db_session = get_db_session()
            cache_service = CacheService()
            
            # Get cache entries to refresh
            cache_entries = db_session.query(SalaryDataCache).filter(
                SalaryDataCache.cache_key.like(cache_pattern.replace('*', '%')),
                SalaryDataCache.is_active == True
            ).all()
            
            refreshed_count = 0
            failed_count = 0
            
            for entry in cache_entries:
                try:
                    # Check if cache entry is expired or needs refresh
                    if entry.is_expired() or entry.hit_rate < 50.0:
                        # Extract request data from cache key
                        request_data = SalaryDataTasks._parse_cache_key(entry.cache_key)
                        
                        if request_data:
                            # Create salary service and fetch fresh data
                            salary_service = EnhancedSalaryDataService(db_session)
                            request = SalaryDataRequest(**request_data)
                            
                            # Force refresh
                            request.force_refresh = True
                            response = await salary_service.get_salary_data(request)
                            
                            refreshed_count += 1
                            logger.info(f"Refreshed cache entry: {entry.cache_key}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to refresh cache entry {entry.cache_key}: {e}")
            
            logger.info(f"Salary cache refresh completed for task {task_id}")
            
            return {
                'task_id': task_id,
                'status': 'success',
                'total_entries': len(cache_entries),
                'refreshed_count': refreshed_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"Error in salary cache refresh task {task_id}: {e}")
            
            try:
                self.retry(countdown=120, max_retries=2)
            except MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for task {task_id}")
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e),
                    'max_retries_exceeded': True
                }
    
    @staticmethod
    @celery_app.task(
        bind=True,
        name='backend.tasks.salary_data_tasks.update_confidence_scores',
        queue='salary_data',
        routing_key='salary_data',
        priority=4,
        rate_limit='15/m',
        time_limit=1800,
        soft_time_limit=1500,
        autoretry_for=(Exception,),
        retry_kwargs={'max_retries': 2, 'countdown': 300},
        retry_backoff=True
    )
    def update_confidence_scores(self, location: str, occupation: Optional[str] = None) -> Dict[str, Any]:
        """
        Update confidence scores for salary data
        
        Args:
            location: Geographic location
            occupation: Optional occupation filter
            
        Returns:
            Confidence score update results
        """
        task_id = current_task.request.id
        logger.info(f"Starting confidence score update task {task_id}")
        
        try:
            # Initialize services
            db_session = get_db_session()
            
            # Get salary benchmarks for the location/occupation
            query = db_session.query(SalaryBenchmark).filter(
                SalaryBenchmark.location == location
            )
            
            if occupation:
                query = query.filter(SalaryBenchmark.occupation == occupation)
            
            salary_benchmarks = query.all()
            
            updated_count = 0
            failed_count = 0
            
            for benchmark in salary_benchmarks:
                try:
                    # Calculate confidence score
                    confidence_score = SalaryDataTasks._calculate_benchmark_confidence(benchmark)
                    
                    # Update or create confidence score record
                    existing_confidence = db_session.query(ConfidenceScore).filter(
                        and_(
                            ConfidenceScore.data_type == 'salary',
                            ConfidenceScore.location == benchmark.location,
                            ConfidenceScore.occupation == benchmark.occupation,
                            ConfidenceScore.industry == benchmark.industry,
                            ConfidenceScore.year == benchmark.year,
                            ConfidenceScore.quarter == benchmark.quarter
                        )
                    ).first()
                    
                    if existing_confidence:
                        # Update existing confidence score
                        existing_confidence.sample_size_score = confidence_score['sample_size_score']
                        existing_confidence.data_freshness_score = confidence_score['data_freshness_score']
                        existing_confidence.source_reliability_score = confidence_score['source_reliability_score']
                        existing_confidence.methodology_score = confidence_score['methodology_score']
                        existing_confidence.consistency_score = confidence_score['consistency_score']
                        existing_confidence.calculate_overall_confidence()
                        existing_confidence.last_calculated = datetime.now()
                    else:
                        # Create new confidence score
                        new_confidence = ConfidenceScore(
                            data_type='salary',
                            location=benchmark.location,
                            occupation=benchmark.occupation,
                            industry=benchmark.industry,
                            year=benchmark.year,
                            quarter=benchmark.quarter,
                            sample_size_score=confidence_score['sample_size_score'],
                            data_freshness_score=confidence_score['data_freshness_score'],
                            source_reliability_score=confidence_score['source_reliability_score'],
                            methodology_score=confidence_score['methodology_score'],
                            consistency_score=confidence_score['consistency_score'],
                            scoring_methodology=confidence_score['scoring_methodology'],
                            contributing_sources=confidence_score['contributing_sources']
                        )
                        new_confidence.calculate_overall_confidence()
                        db_session.add(new_confidence)
                    
                    updated_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to update confidence score for benchmark {benchmark.id}: {e}")
            
            # Commit changes
            db_session.commit()
            
            logger.info(f"Confidence score update completed for task {task_id}")
            
            return {
                'task_id': task_id,
                'status': 'success',
                'total_benchmarks': len(salary_benchmarks),
                'updated_count': updated_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"Error in confidence score update task {task_id}: {e}")
            db_session.rollback()
            
            try:
                self.retry(countdown=300, max_retries=2)
            except MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for task {task_id}")
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e),
                    'max_retries_exceeded': True
                }
    
    @staticmethod
    @celery_app.task(
        bind=True,
        name='backend.tasks.salary_data_tasks.cleanup_expired_cache',
        queue='salary_data',
        routing_key='salary_data',
        priority=2,
        rate_limit='2/m',
        time_limit=900,
        soft_time_limit=600,
        autoretry_for=(Exception,),
        retry_kwargs={'max_retries': 1, 'countdown': 300},
        retry_backoff=True
    )
    def cleanup_expired_cache(self) -> Dict[str, Any]:
        """
        Clean up expired cache entries
        
        Returns:
            Cleanup results
        """
        task_id = current_task.request.id
        logger.info(f"Starting cache cleanup task {task_id}")
        
        try:
            # Initialize services
            db_session = get_db_session()
            cache_service = CacheService()
            
            # Find expired cache entries
            expired_entries = db_session.query(SalaryDataCache).filter(
                SalaryDataCache.expires_at < datetime.now()
            ).all()
            
            cleaned_count = 0
            failed_count = 0
            
            for entry in expired_entries:
                try:
                    # Remove from Redis
                    cache_service.redis_client.delete(entry.redis_key)
                    
                    # Mark as inactive in database
                    entry.is_active = False
                    entry.last_updated = datetime.now()
                    
                    cleaned_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to cleanup cache entry {entry.cache_key}: {e}")
            
            # Commit changes
            db_session.commit()
            
            logger.info(f"Cache cleanup completed for task {task_id}")
            
            return {
                'task_id': task_id,
                'status': 'success',
                'total_expired': len(expired_entries),
                'cleaned_count': cleaned_count,
                'failed_count': failed_count
            }
            
        except Exception as e:
            logger.error(f"Error in cache cleanup task {task_id}: {e}")
            db_session.rollback()
            
            try:
                self.retry(countdown=300, max_retries=1)
            except MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for task {task_id}")
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e),
                    'max_retries_exceeded': True
                }
    
    @staticmethod
    @celery_app.task(
        bind=True,
        name='backend.tasks.salary_data_tasks.monitor_cache_performance',
        queue='monitoring',
        routing_key='monitoring',
        priority=1,
        rate_limit='1/m',
        time_limit=300,
        soft_time_limit=240,
        autoretry_for=(Exception,),
        retry_kwargs={'max_retries': 1, 'countdown': 600},
        retry_backoff=True
    )
    def monitor_cache_performance(self) -> Dict[str, Any]:
        """
        Monitor cache performance and generate metrics
        
        Returns:
            Cache performance metrics
        """
        task_id = current_task.request.id
        logger.info(f"Starting cache performance monitoring task {task_id}")
        
        try:
            # Initialize services
            db_session = get_db_session()
            salary_service = EnhancedSalaryDataService(db_session)
            
            # Get cache statistics
            cache_stats = salary_service.get_cache_stats()
            
            # Calculate performance metrics
            performance_metrics = {
                'overall_hit_rate': cache_stats.get('overall_hit_rate', 0.0),
                'total_cache_entries': cache_stats.get('total_cache_entries', 0),
                'total_requests': cache_stats.get('total_hits', 0) + cache_stats.get('total_misses', 0),
                'cache_efficiency': 'good' if cache_stats.get('overall_hit_rate', 0) > 70 else 'needs_improvement',
                'strategy_performance': {},
                'data_type_performance': {}
            }
            
            # Analyze strategy performance
            for strategy, stats in cache_stats.get('cache_strategies', {}).items():
                total_strategy_requests = stats['hits'] + stats['misses']
                if total_strategy_requests > 0:
                    hit_rate = (stats['hits'] / total_strategy_requests) * 100
                    performance_metrics['strategy_performance'][strategy] = {
                        'hit_rate': hit_rate,
                        'total_requests': total_strategy_requests,
                        'efficiency': 'good' if hit_rate > 70 else 'needs_improvement'
                    }
            
            # Analyze data type performance
            for data_type, stats in cache_stats.get('data_types', {}).items():
                total_type_requests = stats['hits'] + stats['misses']
                if total_type_requests > 0:
                    hit_rate = (stats['hits'] / total_type_requests) * 100
                    performance_metrics['data_type_performance'][data_type] = {
                        'hit_rate': hit_rate,
                        'total_requests': total_type_requests,
                        'efficiency': 'good' if hit_rate > 70 else 'needs_improvement'
                    }
            
            # Log performance issues
            if performance_metrics['overall_hit_rate'] < 70:
                logger.warning(f"Low cache hit rate detected: {performance_metrics['overall_hit_rate']}%")
            
            logger.info(f"Cache performance monitoring completed for task {task_id}")
            
            return {
                'task_id': task_id,
                'status': 'success',
                'performance_metrics': performance_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in cache performance monitoring task {task_id}: {e}")
            
            try:
                self.retry(countdown=600, max_retries=1)
            except MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for task {task_id}")
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e),
                    'max_retries_exceeded': True
                }
    
    @staticmethod
    @celery_app.task(
        bind=True,
        name='backend.tasks.salary_data_tasks.sync_salary_data',
        queue='salary_data',
        routing_key='salary_data',
        priority=6,
        rate_limit='3/m',
        time_limit=3600,
        soft_time_limit=3300,
        autoretry_for=(Exception,),
        retry_kwargs={'max_retries': 2, 'countdown': 600},
        retry_backoff=True
    )
    def sync_salary_data(self, locations: List[str], occupations: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Sync salary data for multiple locations and occupations
        
        Args:
            locations: List of locations to sync
            occupations: Optional list of occupations to sync
            
        Returns:
            Sync results
        """
        task_id = current_task.request.id
        logger.info(f"Starting salary data sync task {task_id}")
        
        try:
            # Initialize services
            db_session = get_db_session()
            salary_service = EnhancedSalaryDataService(db_session)
            
            synced_count = 0
            failed_count = 0
            total_requests = 0
            
            # Default occupations if none provided
            if not occupations:
                occupations = [
                    'Software Engineer', 'Data Scientist', 'Product Manager',
                    'Marketing Manager', 'Sales Representative', 'Financial Analyst',
                    'Human Resources Manager', 'Operations Manager', 'Designer'
                ]
            
            # Sync data for each location and occupation combination
            for location in locations:
                for occupation in occupations:
                    try:
                        # Create request
                        request = SalaryDataRequest(
                            location=location,
                            occupation=occupation,
                            force_refresh=True,
                            cache_strategy=CacheStrategy.STANDARD
                        )
                        
                        # Fetch data
                        response = await salary_service.get_salary_data(request)
                        
                        if response.salary_benchmarks:
                            synced_count += 1
                        
                        total_requests += 1
                        
                        # Add delay to respect rate limits
                        import asyncio
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Failed to sync data for {location}, {occupation}: {e}")
            
            logger.info(f"Salary data sync completed for task {task_id}")
            
            return {
                'task_id': task_id,
                'status': 'success',
                'total_requests': total_requests,
                'synced_count': synced_count,
                'failed_count': failed_count,
                'success_rate': (synced_count / total_requests * 100) if total_requests > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in salary data sync task {task_id}: {e}")
            
            try:
                self.retry(countdown=600, max_retries=2)
            except MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for task {task_id}")
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(e),
                    'max_retries_exceeded': True
                }
    
    # Helper methods
    @staticmethod
    def _parse_cache_key(cache_key: str) -> Optional[Dict[str, Any]]:
        """Parse cache key to extract request parameters"""
        try:
            parts = cache_key.split(':')
            if len(parts) >= 5:
                return {
                    'location': parts[1].replace('_', ' '),
                    'occupation': parts[3] if parts[3] != 'all' else None,
                    'industry': parts[4] if parts[4] != 'all' else None,
                    'year': int(parts[5]) if parts[5] != 'latest' else None
                }
            return None
        except Exception as e:
            logger.error(f"Error parsing cache key {cache_key}: {e}")
            return None
    
    @staticmethod
    def _calculate_benchmark_confidence(benchmark: SalaryBenchmark) -> Dict[str, Any]:
        """Calculate confidence score for a salary benchmark"""
        try:
            # Sample size score (0-1)
            sample_size = benchmark.sample_size or 0
            if sample_size >= 10000:
                sample_size_score = 1.0
            elif sample_size >= 1000:
                sample_size_score = 0.8
            elif sample_size >= 100:
                sample_size_score = 0.6
            elif sample_size >= 10:
                sample_size_score = 0.4
            else:
                sample_size_score = 0.2
            
            # Data freshness score (0-1)
            freshness_days = benchmark.data_freshness_days or 999
            if freshness_days <= 30:
                data_freshness_score = 1.0
            elif freshness_days <= 90:
                data_freshness_score = 0.8
            elif freshness_days <= 365:
                data_freshness_score = 0.6
            elif freshness_days <= 730:
                data_freshness_score = 0.4
            else:
                data_freshness_score = 0.2
            
            # Source reliability score (0-1)
            source_reliability_score = float(benchmark.source_confidence_score or 0.5)
            
            # Methodology score (0-1) - based on data source
            methodology_scores = {
                'bls': 0.9,
                'census': 0.8,
                'indeed': 0.7,
                'fallback': 0.3
            }
            methodology_score = methodology_scores.get(benchmark.data_source.lower(), 0.5)
            
            # Consistency score (0-1) - placeholder for cross-source validation
            consistency_score = 0.7  # Default value, could be enhanced with cross-validation
            
            return {
                'sample_size_score': sample_size_score,
                'data_freshness_score': data_freshness_score,
                'source_reliability_score': source_reliability_score,
                'methodology_score': methodology_score,
                'consistency_score': consistency_score,
                'scoring_methodology': {
                    'weights': {
                        'sample_size': 0.25,
                        'data_freshness': 0.25,
                        'source_reliability': 0.2,
                        'methodology': 0.2,
                        'consistency': 0.1
                    },
                    'calculation_method': 'weighted_average'
                },
                'contributing_sources': [benchmark.data_source]
            }
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return {
                'sample_size_score': 0.0,
                'data_freshness_score': 0.0,
                'source_reliability_score': 0.0,
                'methodology_score': 0.0,
                'consistency_score': 0.0,
                'scoring_methodology': {},
                'contributing_sources': []
            }

# Create task instances
salary_data_tasks = SalaryDataTasks() 