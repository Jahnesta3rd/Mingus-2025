"""
Celery Background Tasks for Salary Data Refresh
Handles periodic data refresh, cache maintenance, and data quality monitoring
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from celery import current_task
import json

from ..services.salary_data_service import SalaryDataService, DataSource
from ..services.data_validation import DataValidator, ValidationLevel

logger = logging.getLogger(__name__)

class DataRefreshTasks:
    """Celery tasks for data refresh and maintenance"""
    
    def __init__(self):
        """Initialize the data refresh tasks"""
        self.salary_service = SalaryDataService()
        self.validator = DataValidator()
        
        # Target locations for data refresh
        self.target_locations = [
            'Atlanta', 'Houston', 'Washington DC', 'Dallas-Fort Worth',
            'New York City', 'Philadelphia', 'Chicago', 'Charlotte',
            'Miami', 'Baltimore'
        ]
        
        # Common occupations for data refresh
        self.common_occupations = [
            'Software Engineer', 'Data Scientist', 'Product Manager',
            'Marketing Manager', 'Financial Analyst', 'Sales Representative',
            'Human Resources Manager', 'Operations Manager'
        ]
    
    def refresh_all_salary_data(self) -> Dict[str, Any]:
        """
        Refresh salary data for all locations and common occupations
        
        Returns:
            Summary of refresh operations
        """
        logger.info("Starting comprehensive salary data refresh")
        
        refresh_summary = {
            'started_at': datetime.now().isoformat(),
            'locations_processed': 0,
            'occupations_processed': 0,
            'successful_refreshes': 0,
            'failed_refreshes': 0,
            'cache_entries_updated': 0,
            'errors': []
        }
        
        try:
            # Refresh general location data (no specific occupation)
            for location in self.target_locations:
                try:
                    current_task.update_state(
                        state='PROGRESS',
                        meta={'current_location': location, 'progress': f'Processing {location}'}
                    )
                    
                    # Run async function in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        comprehensive_data = loop.run_until_complete(
                            self.salary_service.get_comprehensive_salary_data(location)
                        )
                        
                        refresh_summary['locations_processed'] += 1
                        refresh_summary['successful_refreshes'] += 1
                        refresh_summary['cache_entries_updated'] += len(comprehensive_data.salary_data)
                        
                        logger.info(f"Successfully refreshed data for {location}")
                        
                    finally:
                        loop.close()
                        
                except Exception as e:
                    error_msg = f"Failed to refresh data for {location}: {str(e)}"
                    logger.error(error_msg)
                    refresh_summary['errors'].append(error_msg)
                    refresh_summary['failed_refreshes'] += 1
            
            # Refresh occupation-specific data for top locations
            top_locations = ['Atlanta', 'New York City', 'San Francisco', 'Chicago', 'Washington DC']
            
            for location in top_locations:
                for occupation in self.common_occupations[:3]:  # Limit to top 3 occupations
                    try:
                        current_task.update_state(
                            state='PROGRESS',
                            meta={'current_location': location, 'current_occupation': occupation}
                        )
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            comprehensive_data = loop.run_until_complete(
                                self.salary_service.get_comprehensive_salary_data(location, occupation)
                            )
                            
                            refresh_summary['occupations_processed'] += 1
                            refresh_summary['successful_refreshes'] += 1
                            refresh_summary['cache_entries_updated'] += len(comprehensive_data.salary_data)
                            
                            logger.info(f"Successfully refreshed data for {location} - {occupation}")
                            
                        finally:
                            loop.close()
                            
                    except Exception as e:
                        error_msg = f"Failed to refresh data for {location} - {occupation}: {str(e)}"
                        logger.error(error_msg)
                        refresh_summary['errors'].append(error_msg)
                        refresh_summary['failed_refreshes'] += 1
            
            refresh_summary['completed_at'] = datetime.now().isoformat()
            refresh_summary['total_operations'] = refresh_summary['successful_refreshes'] + refresh_summary['failed_refreshes']
            
            logger.info(f"Salary data refresh completed: {refresh_summary['successful_refreshes']} successful, {refresh_summary['failed_refreshes']} failed")
            
            return refresh_summary
            
        except Exception as e:
            error_msg = f"Critical error in salary data refresh: {str(e)}"
            logger.error(error_msg)
            refresh_summary['errors'].append(error_msg)
            refresh_summary['completed_at'] = datetime.now().isoformat()
            return refresh_summary
    
    def refresh_location_data(self, location: str, occupation: str = None) -> Dict[str, Any]:
        """
        Refresh salary data for a specific location and optional occupation
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
        
        Returns:
            Refresh operation summary
        """
        logger.info(f"Starting data refresh for {location}, occupation: {occupation}")
        
        refresh_summary = {
            'location': location,
            'occupation': occupation,
            'started_at': datetime.now().isoformat(),
            'successful': False,
            'cache_entries_updated': 0,
            'data_quality_score': 0.0,
            'confidence_score': 0.0,
            'errors': []
        }
        
        try:
            current_task.update_state(
                state='PROGRESS',
                meta={'current_location': location, 'current_occupation': occupation}
            )
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                comprehensive_data = loop.run_until_complete(
                    self.salary_service.get_comprehensive_salary_data(location, occupation)
                )
                
                refresh_summary['successful'] = True
                refresh_summary['cache_entries_updated'] = len(comprehensive_data.salary_data)
                refresh_summary['data_quality_score'] = comprehensive_data.data_quality_score
                refresh_summary['confidence_score'] = comprehensive_data.overall_confidence_score
                
                logger.info(f"Successfully refreshed data for {location}")
                
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = f"Failed to refresh data for {location}: {str(e)}"
            logger.error(error_msg)
            refresh_summary['errors'].append(error_msg)
        
        refresh_summary['completed_at'] = datetime.now().isoformat()
        return refresh_summary
    
    def validate_cached_data(self) -> Dict[str, Any]:
        """
        Validate all cached salary data for quality and consistency
        
        Returns:
            Validation summary
        """
        logger.info("Starting cached data validation")
        
        validation_summary = {
            'started_at': datetime.now().isoformat(),
            'cache_entries_checked': 0,
            'valid_entries': 0,
            'invalid_entries': 0,
            'quality_issues': [],
            'outliers_detected': 0,
            'recommendations': []
        }
        
        try:
            if not self.salary_service.redis_client:
                validation_summary['errors'] = ['Redis not available']
                return validation_summary
            
            # Get all salary data cache keys
            cache_keys = self.salary_service.redis_client.keys("salary_data:*")
            
            for cache_key in cache_keys:
                try:
                    cached_data = self.salary_service._get_cached_data(cache_key)
                    if cached_data:
                        validation_summary['cache_entries_checked'] += 1
                        
                        # Validate the data
                        if 'median_salary' in cached_data:
                            validation_result = self.validator.validate_salary_data(cached_data)
                        elif 'overall_cost_index' in cached_data:
                            validation_result = self.validator.validate_cost_of_living_data(cached_data)
                        elif 'job_count' in cached_data:
                            validation_result = self.validator.validate_job_market_data(cached_data)
                        else:
                            validation_summary['invalid_entries'] += 1
                            continue
                        
                        if validation_result.is_valid:
                            validation_summary['valid_entries'] += 1
                        else:
                            validation_summary['invalid_entries'] += 1
                            validation_summary['quality_issues'].append({
                                'cache_key': cache_key,
                                'issues': validation_result.issues,
                                'warnings': validation_result.warnings
                            })
                        
                        if validation_result.outliers_detected:
                            validation_summary['outliers_detected'] += len(validation_result.outliers_detected)
                        
                        # Check data age
                        if 'last_updated' in cached_data:
                            try:
                                last_updated = datetime.fromisoformat(cached_data['last_updated'])
                                if datetime.now() - last_updated > timedelta(days=7):
                                    validation_summary['recommendations'].append(
                                        f"Data in {cache_key} is older than 7 days"
                                    )
                            except:
                                pass
                
                except Exception as e:
                    logger.error(f"Error validating cache entry {cache_key}: {e}")
                    validation_summary['invalid_entries'] += 1
            
            validation_summary['completed_at'] = datetime.now().isoformat()
            
            # Generate overall recommendations
            if validation_summary['invalid_entries'] > 0:
                validation_summary['recommendations'].append(
                    f"Found {validation_summary['invalid_entries']} invalid cache entries that should be refreshed"
                )
            
            if validation_summary['outliers_detected'] > 0:
                validation_summary['recommendations'].append(
                    f"Detected {validation_summary['outliers_detected']} outliers that may need investigation"
                )
            
            logger.info(f"Data validation completed: {validation_summary['valid_entries']} valid, {validation_summary['invalid_entries']} invalid")
            
        except Exception as e:
            error_msg = f"Critical error in data validation: {str(e)}"
            logger.error(error_msg)
            validation_summary['errors'] = [error_msg]
            validation_summary['completed_at'] = datetime.now().isoformat()
        
        return validation_summary
    
    def cleanup_expired_cache(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up expired cache entries
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        
        Returns:
            Cleanup summary
        """
        logger.info(f"Starting cache cleanup for entries older than {max_age_hours} hours")
        
        cleanup_summary = {
            'started_at': datetime.now().isoformat(),
            'cache_entries_checked': 0,
            'entries_removed': 0,
            'errors': []
        }
        
        try:
            if not self.salary_service.redis_client:
                cleanup_summary['errors'] = ['Redis not available']
                return cleanup_summary
            
            # Get all salary data cache keys
            cache_keys = self.salary_service.redis_client.keys("salary_data:*")
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for cache_key in cache_keys:
                try:
                    cached_data = self.salary_service._get_cached_data(cache_key)
                    if cached_data:
                        cleanup_summary['cache_entries_checked'] += 1
                        
                        # Check if data is older than cutoff
                        if 'last_updated' in cached_data:
                            try:
                                last_updated = datetime.fromisoformat(cached_data['last_updated'])
                                if last_updated < cutoff_time:
                                    # Remove expired entry
                                    self.salary_service.redis_client.delete(cache_key)
                                    cleanup_summary['entries_removed'] += 1
                                    logger.info(f"Removed expired cache entry: {cache_key}")
                            except:
                                # If we can't parse the timestamp, remove the entry
                                self.salary_service.redis_client.delete(cache_key)
                                cleanup_summary['entries_removed'] += 1
                                logger.info(f"Removed cache entry with invalid timestamp: {cache_key}")
                
                except Exception as e:
                    logger.error(f"Error processing cache entry {cache_key}: {e}")
                    cleanup_summary['errors'].append(f"Error processing {cache_key}: {str(e)}")
            
            cleanup_summary['completed_at'] = datetime.now().isoformat()
            logger.info(f"Cache cleanup completed: {cleanup_summary['entries_removed']} entries removed")
            
        except Exception as e:
            error_msg = f"Critical error in cache cleanup: {str(e)}"
            logger.error(error_msg)
            cleanup_summary['errors'] = [error_msg]
            cleanup_summary['completed_at'] = datetime.now().isoformat()
        
        return cleanup_summary
    
    def monitor_data_quality(self) -> Dict[str, Any]:
        """
        Monitor overall data quality and generate health report
        
        Returns:
            Data quality health report
        """
        logger.info("Starting data quality monitoring")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'unknown',
            'cache_status': {},
            'api_health': {},
            'data_quality_metrics': {},
            'recommendations': []
        }
        
        try:
            # Check cache status
            cache_status = self.salary_service.get_cache_status()
            health_report['cache_status'] = cache_status
            
            if cache_status.get('status') == 'available':
                # Check cache hit rate
                hits = cache_status.get('keyspace_hits', 0)
                misses = cache_status.get('keyspace_misses', 0)
                total_requests = hits + misses
                
                if total_requests > 0:
                    hit_rate = hits / total_requests
                    health_report['data_quality_metrics']['cache_hit_rate'] = hit_rate
                    
                    if hit_rate < 0.5:
                        health_report['recommendations'].append("Low cache hit rate - consider adjusting cache TTL")
            
            # Check API health (simplified check)
            health_report['api_health'] = {
                'bls_configured': bool(self.salary_service.api_keys['bls']),
                'census_configured': bool(self.salary_service.api_keys['census']),
                'fred_configured': bool(self.salary_service.api_keys['fred']),
                'indeed_configured': bool(self.salary_service.api_keys['indeed'])
            }
            
            # Validate sample data for each location
            sample_validation_results = []
            for location in self.target_locations[:3]:  # Check first 3 locations
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        comprehensive_data = loop.run_until_complete(
                            self.salary_service.get_comprehensive_salary_data(location)
                        )
                        
                        sample_validation_results.append({
                            'location': location,
                            'data_quality_score': comprehensive_data.data_quality_score,
                            'confidence_score': comprehensive_data.overall_confidence_score,
                            'sources_count': len(comprehensive_data.salary_data)
                        })
                        
                    finally:
                        loop.close()
                        
                except Exception as e:
                    logger.error(f"Error validating sample data for {location}: {e}")
            
            if sample_validation_results:
                avg_quality = sum(r['data_quality_score'] for r in sample_validation_results) / len(sample_validation_results)
                avg_confidence = sum(r['confidence_score'] for r in sample_validation_results) / len(sample_validation_results)
                
                health_report['data_quality_metrics']['average_quality_score'] = avg_quality
                health_report['data_quality_metrics']['average_confidence_score'] = avg_confidence
                
                # Determine overall health
                if avg_quality >= 0.8 and avg_confidence >= 0.8:
                    health_report['overall_health'] = 'excellent'
                elif avg_quality >= 0.6 and avg_confidence >= 0.6:
                    health_report['overall_health'] = 'good'
                elif avg_quality >= 0.4 and avg_confidence >= 0.4:
                    health_report['overall_health'] = 'fair'
                else:
                    health_report['overall_health'] = 'poor'
                
                # Generate recommendations based on health
                if health_report['overall_health'] == 'poor':
                    health_report['recommendations'].append("Data quality is poor - investigate API issues and fallback data")
                elif health_report['overall_health'] == 'fair':
                    health_report['recommendations'].append("Data quality is fair - consider refreshing data more frequently")
            
            logger.info(f"Data quality monitoring completed: {health_report['overall_health']} health")
            
        except Exception as e:
            error_msg = f"Critical error in data quality monitoring: {str(e)}"
            logger.error(error_msg)
            health_report['errors'] = [error_msg]
            health_report['overall_health'] = 'error'
        
        return health_report
    
    def generate_data_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive data report for all locations
        
        Returns:
            Comprehensive data report
        """
        logger.info("Generating comprehensive data report")
        
        data_report = {
            'generated_at': datetime.now().isoformat(),
            'locations_covered': len(self.target_locations),
            'data_summary': {},
            'quality_metrics': {},
            'recommendations': []
        }
        
        try:
            location_summaries = []
            
            for location in self.target_locations:
                try:
                    current_task.update_state(
                        state='PROGRESS',
                        meta={'current_location': location, 'progress': f'Analyzing {location}'}
                    )
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        comprehensive_data = loop.run_until_complete(
                            self.salary_service.get_comprehensive_salary_data(location)
                        )
                        
                        location_summary = {
                            'location': location,
                            'salary_sources': len(comprehensive_data.salary_data),
                            'has_cost_of_living': comprehensive_data.cost_of_living_data is not None,
                            'has_job_market': comprehensive_data.job_market_data is not None,
                            'data_quality_score': comprehensive_data.data_quality_score,
                            'confidence_score': comprehensive_data.overall_confidence_score,
                            'best_salary_source': None,
                            'median_salary': None
                        }
                        
                        # Find best salary data
                        if comprehensive_data.salary_data:
                            best_salary = max(comprehensive_data.salary_data, key=lambda x: x.confidence_score)
                            location_summary['best_salary_source'] = best_salary.source.value
                            location_summary['median_salary'] = best_salary.median_salary
                        
                        location_summaries.append(location_summary)
                        
                    finally:
                        loop.close()
                        
                except Exception as e:
                    logger.error(f"Error generating report for {location}: {e}")
                    location_summaries.append({
                        'location': location,
                        'error': str(e)
                    })
            
            data_report['data_summary'] = {
                'locations_with_data': len([s for s in location_summaries if 'error' not in s]),
                'locations_with_errors': len([s for s in location_summaries if 'error' in s]),
                'average_quality_score': sum(s.get('data_quality_score', 0) for s in location_summaries if 'error' not in s) / max(1, len([s for s in location_summaries if 'error' not in s])),
                'average_confidence_score': sum(s.get('confidence_score', 0) for s in location_summaries if 'error' not in s) / max(1, len([s for s in location_summaries if 'error' not in s]))
            }
            
            data_report['location_details'] = location_summaries
            
            # Generate recommendations
            if data_report['data_summary']['locations_with_errors'] > 0:
                data_report['recommendations'].append(
                    f"{data_report['data_summary']['locations_with_errors']} locations have data errors that need attention"
                )
            
            if data_report['data_summary']['average_quality_score'] < 0.7:
                data_report['recommendations'].append("Overall data quality is below target - consider data source improvements")
            
            if data_report['data_summary']['average_confidence_score'] < 0.7:
                data_report['recommendations'].append("Overall confidence is below target - consider API improvements")
            
            logger.info(f"Data report generated: {data_report['data_summary']['locations_with_data']} locations with data")
            
        except Exception as e:
            error_msg = f"Critical error generating data report: {str(e)}"
            logger.error(error_msg)
            data_report['errors'] = [error_msg]
        
        return data_report 