"""
Enhanced Salary Data Service with Async Data Fetching
Provides comprehensive salary data with intelligent caching, validation, and confidence scoring
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import numpy as np

# Import with fallbacks to support tests importing 'services.*' with sys.path tweaks
try:
    from backend.services.api_client import AsyncAPIClient, APISource, APIResponse
    from backend.services.data_validation import DataValidator, ValidationResult, ValidationLevel
    # Import inside function scope later to avoid circular import
    SalaryDataRepository = None  # type: ignore
except Exception:  # pragma: no cover - fallback path when 'backend' package not used
    from services.api_client import AsyncAPIClient, APISource, APIResponse
    from services.data_validation import DataValidator, ValidationResult, ValidationLevel
    SalaryDataRepository = None  # type: ignore

logger = logging.getLogger(__name__)

class DataSource(str, Enum):
    """Data source types"""
    BLS = "bls"
    CENSUS = "census"
    FRED = "fred"
    INDEED = "indeed"
    FALLBACK = "fallback"
    CACHED = "cached"

@dataclass
class SalaryDataPoint:
    """Individual salary data point"""
    source: DataSource
    location: str
    occupation: str
    median_salary: float
    mean_salary: float
    percentile_25: float
    percentile_75: float
    sample_size: int
    year: int
    confidence_score: float
    validation_result: Optional[ValidationResult] = None
    last_updated: datetime = None
    cache_key: Optional[str] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class CostOfLivingDataPoint:
    """Cost of living data point"""
    location: str
    overall_cost_index: float
    housing_cost_index: float
    transportation_cost_index: float
    food_cost_index: float
    healthcare_cost_index: float
    utilities_cost_index: float
    year: int
    confidence_score: float
    validation_result: Optional[ValidationResult] = None
    last_updated: datetime = None
    cache_key: Optional[str] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class JobMarketDataPoint:
    """Job market data point"""
    location: str
    occupation: str
    job_count: int
    average_salary: float
    salary_range_min: float
    salary_range_max: float
    demand_score: float
    confidence_score: float
    validation_result: Optional[ValidationResult] = None
    last_updated: datetime = None
    cache_key: Optional[str] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class ComprehensiveSalaryData:
    """Comprehensive salary data combining multiple sources"""
    location: str
    occupation: str
    salary_data: List[SalaryDataPoint]
    cost_of_living_data: Optional[CostOfLivingDataPoint] = None
    job_market_data: Optional[JobMarketDataPoint] = None
    overall_confidence_score: float = 0.0
    data_quality_score: float = 0.0
    recommendations: List[str] = None
    last_updated: datetime = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
        if self.recommendations is None:
            self.recommendations = []

class SalaryDataService:
    """
    Enhanced salary data service with async data fetching and intelligent caching
    """
    
    def __init__(self, db_session=None):
        """Initialize the salary data service"""
        # Initialize components
        self.validator = DataValidator()
        # Lazy import repository to avoid circular import at module import time
        repository_cls = None
        if db_session is not None:
            try:
                if SalaryDataRepository is None:
                    try:
                        from backend.services.salary_data_repository import SalaryDataRepository as _Repo
                    except Exception:
                        from services.salary_data_repository import SalaryDataRepository as _Repo  # type: ignore
                    repository_cls = _Repo
                else:
                    repository_cls = SalaryDataRepository
            except Exception:
                repository_cls = None
        self.repository = repository_cls(db_session) if repository_cls else None
        
        # API configuration
        self.api_keys = {
            'bls': os.getenv('BLS_API_KEY'),
            'census': os.getenv('CENSUS_API_KEY'),
            'fred': os.getenv('FRED_API_KEY'),
            'indeed': os.getenv('INDEED_API_KEY')
        }
        
        # Target locations and their mappings
        self.target_locations = [
            'Atlanta', 'Houston', 'Washington DC', 'Dallas-Fort Worth',
            'New York City', 'Philadelphia', 'Chicago', 'Charlotte',
            'Miami', 'Baltimore'
        ]
        
        # BLS Series IDs mapping
        self.bls_series_ids = {
            'Atlanta': 'LAUCN130890000000003',
            'Houston': 'LAUCN481670000000003',
            'Washington DC': 'LAUCN110010000000003',
            'Dallas-Fort Worth': 'LAUCN481130000000003',
            'New York City': 'LAUCN360610000000003',
            'Philadelphia': 'LAUCN421010000000003',
            'Chicago': 'LAUCN170310000000003',
            'Charlotte': 'LAUCN371190000000003',
            'Miami': 'LAUCN120860000000003',
            'Baltimore': 'LAUCN240050000000003'
        }
        
        # Census MSA codes
        self.census_msa_codes = {
            'Atlanta': '12060',
            'Houston': '26420',
            'Washington DC': '47900',
            'Dallas-Fort Worth': '19100',
            'New York City': '35620',
            'Philadelphia': '37980',
            'Chicago': '16980',
            'Charlotte': '16740',
            'Miami': '33100',
            'Baltimore': '12580'
        }
        
        # Initialize Redis cache using existing infrastructure
        self._initialize_redis()
        
        # Initialize fallback data
        self._initialize_fallback_data()
        
        logger.info("SalaryDataService initialized")
    
    def _initialize_redis(self):
        """Initialize Redis connection for caching using existing infrastructure"""
        try:
            # Use existing Redis configuration from the project
            self.redis_host = os.getenv('REDIS_HOST', 'localhost')
            self.redis_port = int(os.getenv('REDIS_PORT', 6379))
            self.redis_db = int(os.getenv('REDIS_DB', 0))
            self.redis_password = os.getenv('REDIS_PASSWORD')
            
            # Use the same Redis client configuration as existing services
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connection established using existing infrastructure")
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _initialize_fallback_data(self):
        """Initialize static fallback data"""
        self.fallback_salary_data = {
            'Atlanta': {
                'median_salary': 65000,
                'mean_salary': 72000,
                'percentile_25': 45000,
                'percentile_75': 95000,
                'sample_size': 2500000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Houston': {
                'median_salary': 62000,
                'mean_salary': 69000,
                'percentile_25': 42000,
                'percentile_75': 90000,
                'sample_size': 2200000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Washington DC': {
                'median_salary': 75000,
                'mean_salary': 85000,
                'percentile_25': 52000,
                'percentile_75': 110000,
                'sample_size': 1800000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Dallas-Fort Worth': {
                'median_salary': 63000,
                'mean_salary': 70000,
                'percentile_25': 43000,
                'percentile_75': 92000,
                'sample_size': 2000000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'New York City': {
                'median_salary': 70000,
                'mean_salary': 80000,
                'percentile_25': 48000,
                'percentile_75': 105000,
                'sample_size': 3500000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Philadelphia': {
                'median_salary': 58000,
                'mean_salary': 65000,
                'percentile_25': 40000,
                'percentile_75': 85000,
                'sample_size': 1500000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Chicago': {
                'median_salary': 68000,
                'mean_salary': 75000,
                'percentile_25': 46000,
                'percentile_75': 98000,
                'sample_size': 2800000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Charlotte': {
                'median_salary': 60000,
                'mean_salary': 67000,
                'percentile_25': 41000,
                'percentile_75': 88000,
                'sample_size': 1200000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Miami': {
                'median_salary': 55000,
                'mean_salary': 62000,
                'percentile_25': 38000,
                'percentile_75': 80000,
                'sample_size': 1800000,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Baltimore': {
                'median_salary': 59000,
                'mean_salary': 66000,
                'percentile_25': 40000,
                'percentile_75': 87000,
                'sample_size': 1000000,
                'year': 2022,
                'confidence_score': 0.70
            }
        }
        
        self.fallback_cost_of_living = {
            'Atlanta': {
                'overall_cost_index': 100.0,
                'housing_cost_index': 95.0,
                'transportation_cost_index': 90.0,
                'food_cost_index': 80.0,
                'healthcare_cost_index': 120.0,
                'utilities_cost_index': 70.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Houston': {
                'overall_cost_index': 95.0,
                'housing_cost_index': 90.0,
                'transportation_cost_index': 85.0,
                'food_cost_index': 75.0,
                'healthcare_cost_index': 115.0,
                'utilities_cost_index': 65.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Washington DC': {
                'overall_cost_index': 130.0,
                'housing_cost_index': 140.0,
                'transportation_cost_index': 110.0,
                'food_cost_index': 100.0,
                'healthcare_cost_index': 130.0,
                'utilities_cost_index': 90.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Dallas-Fort Worth': {
                'overall_cost_index': 98.0,
                'housing_cost_index': 92.0,
                'transportation_cost_index': 88.0,
                'food_cost_index': 78.0,
                'healthcare_cost_index': 118.0,
                'utilities_cost_index': 68.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'New York City': {
                'overall_cost_index': 150.0,
                'housing_cost_index': 180.0,
                'transportation_cost_index': 120.0,
                'food_cost_index': 110.0,
                'healthcare_cost_index': 140.0,
                'utilities_cost_index': 100.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Philadelphia': {
                'overall_cost_index': 105.0,
                'housing_cost_index': 110.0,
                'transportation_cost_index': 95.0,
                'food_cost_index': 85.0,
                'healthcare_cost_index': 125.0,
                'utilities_cost_index': 75.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Chicago': {
                'overall_cost_index': 115.0,
                'housing_cost_index': 120.0,
                'transportation_cost_index': 105.0,
                'food_cost_index': 95.0,
                'healthcare_cost_index': 135.0,
                'utilities_cost_index': 85.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Charlotte': {
                'overall_cost_index': 92.0,
                'housing_cost_index': 88.0,
                'transportation_cost_index': 85.0,
                'food_cost_index': 75.0,
                'healthcare_cost_index': 115.0,
                'utilities_cost_index': 65.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Miami': {
                'overall_cost_index': 110.0,
                'housing_cost_index': 115.0,
                'transportation_cost_index': 100.0,
                'food_cost_index': 90.0,
                'healthcare_cost_index': 130.0,
                'utilities_cost_index': 80.0,
                'year': 2022,
                'confidence_score': 0.70
            },
            'Baltimore': {
                'overall_cost_index': 102.0,
                'housing_cost_index': 105.0,
                'transportation_cost_index': 90.0,
                'food_cost_index': 80.0,
                'healthcare_cost_index': 120.0,
                'utilities_cost_index': 70.0,
                'year': 2022,
                'confidence_score': 0.70
            }
        }
    
    def _get_cache_key(self, data_type: str, location: str, occupation: str = None) -> str:
        """Generate cache key for data"""
        if occupation:
            return f"salary_data:{data_type}:{location}:{occupation}"
        return f"salary_data:{data_type}:{location}"
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get data from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Error reading from cache: {e}")
        
        return None
    
    def _set_cached_data(self, cache_key: str, data: Dict, ttl: int = 86400):
        """Store data in Redis cache with TTL"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(cache_key, ttl, json.dumps(data))
            
            # Update cache metrics if repository is available
            if self.repository:
                try:
                    # Get cache statistics
                    info = self.redis_client.info()
                    hits = info.get('keyspace_hits', 0)
                    misses = info.get('keyspace_misses', 0)
                    total_requests = hits + misses
                    hit_rate = hits / total_requests if total_requests > 0 else 0
                    
                    # Get cache size for this pattern
                    pattern_keys = self.redis_client.keys(f"{cache_key.split(':')[0]}:*")
                    total_size = sum(len(self.redis_client.get(key) or '') for key in pattern_keys)
                    
                    self.repository.save_cache_metric(
                        cache_key_pattern=f"{cache_key.split(':')[0]}:*",
                        hits=hits,
                        misses=misses,
                        hit_rate=hit_rate,
                        total_size_bytes=total_size,
                        entries_count=len(pattern_keys)
                    )
                except Exception as e:
                    logger.warning(f"Failed to save cache metrics: {e}")
                    
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
    
    async def fetch_bls_salary_data(self, location: str, occupation: str = None) -> Optional[SalaryDataPoint]:
        """
        Fetch salary data from BLS API
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
        
        Returns:
            SalaryDataPoint or None if unavailable
        """
        cache_key = self._get_cache_key('bls', location, occupation)
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"BLS data retrieved from cache for {location}")
            return SalaryDataPoint(**cached_data)
        
        # Check if API key is available
        if not self.api_keys['bls']:
            logger.warning("BLS API key not configured")
            return self._get_fallback_salary_data(location, occupation)
        
        try:
            async with AsyncAPIClient() as api_client:
                series_id = self.bls_series_ids.get(location)
                if not series_id:
                    logger.warning(f"No BLS series ID found for {location}")
                    return self._get_fallback_salary_data(location, occupation)
                
                response = await api_client.get_bls_data(
                    series_ids=[series_id],
                    start_year=str(datetime.now().year - 1),
                    end_year=str(datetime.now().year),
                    api_key=self.api_keys['bls']
                )
                
                if response.success and response.data:
                    # Parse BLS response
                    salary_data = self._parse_bls_response(response.data, location, occupation)
                    if salary_data:
                        # Validate data
                        validation_result = self.validator.validate_salary_data(asdict(salary_data))
                        salary_data.validation_result = validation_result
                        
                        # Cache the result
                        self._set_cached_data(cache_key, asdict(salary_data))
                        
                        # Save to database if repository is available
                        if self.repository:
                            try:
                                self.repository.save_salary_benchmark(salary_data)
                            except Exception as e:
                                logger.warning(f"Failed to save salary benchmark to database: {e}")
                        
                        logger.info(f"BLS data fetched successfully for {location}")
                        return salary_data
                
                logger.warning(f"BLS API call failed for {location}: {response.error}")
                return self._get_fallback_salary_data(location, occupation)
                
        except Exception as e:
            logger.error(f"Error fetching BLS data for {location}: {e}")
            return self._get_fallback_salary_data(location, occupation)
    
    async def fetch_census_salary_data(self, location: str) -> Optional[SalaryDataPoint]:
        """
        Fetch salary data from Census API
        
        Args:
            location: Target location
        
        Returns:
            SalaryDataPoint or None if unavailable
        """
        cache_key = self._get_cache_key('census', location)
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Census data retrieved from cache for {location}")
            return SalaryDataPoint(**cached_data)
        
        # Check if API key is available
        if not self.api_keys['census']:
            logger.warning("Census API key not configured")
            return self._get_fallback_salary_data(location)
        
        try:
            async with AsyncAPIClient() as api_client:
                msa_code = self.census_msa_codes.get(location)
                if not msa_code:
                    logger.warning(f"No Census MSA code found for {location}")
                    return self._get_fallback_salary_data(location)
                
                variables = ['B19013_001E', 'B25064_001E', 'B08303_001E', 'B25077_001E']
                geography = f'metropolitan statistical area/micropolitan statistical area:{msa_code}'
                
                response = await api_client.get_census_data(
                    variables=variables,
                    geography=geography,
                    api_key=self.api_keys['census']
                )
                
                if response.success and response.data:
                    # Parse Census response
                    salary_data = self._parse_census_response(response.data, location)
                    if salary_data:
                        # Validate data
                        validation_result = self.validator.validate_salary_data(asdict(salary_data))
                        salary_data.validation_result = validation_result
                        
                        # Cache the result
                        self._set_cached_data(cache_key, asdict(salary_data))
                        
                        # Save to database if repository is available
                        if self.repository:
                            try:
                                self.repository.save_salary_benchmark(salary_data)
                            except Exception as e:
                                logger.warning(f"Failed to save salary benchmark to database: {e}")
                        
                        logger.info(f"Census data fetched successfully for {location}")
                        return salary_data
                
                logger.warning(f"Census API call failed for {location}: {response.error}")
                return self._get_fallback_salary_data(location)
                
        except Exception as e:
            logger.error(f"Error fetching Census data for {location}: {e}")
            return self._get_fallback_salary_data(location)
    
    async def fetch_fred_cost_of_living_data(self, location: str) -> Optional[CostOfLivingDataPoint]:
        """
        Fetch cost of living data from FRED API
        
        Args:
            location: Target location
        
        Returns:
            CostOfLivingDataPoint or None if unavailable
        """
        cache_key = self._get_cache_key('cost_of_living', location)
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"FRED data retrieved from cache for {location}")
            return CostOfLivingDataPoint(**cached_data)
        
        # Check if API key is available
        if not self.api_keys['fred']:
            logger.warning("FRED API key not configured")
            return self._get_fallback_cost_of_living_data(location)
        
        try:
            async with AsyncAPIClient() as api_client:
                response = await api_client.get_fred_data(
                    series_id='RPPALL',
                    api_key=self.api_keys['fred'],
                    sort_order='desc',
                    limit=1
                )
                
                if response.success and response.data:
                    # Parse FRED response
                    cost_data = self._parse_fred_response(response.data, location)
                    if cost_data:
                        # Validate data
                        validation_result = self.validator.validate_cost_of_living_data(asdict(cost_data))
                        cost_data.validation_result = validation_result
                        
                        # Cache the result
                        self._set_cached_data(cache_key, asdict(cost_data))
                        
                        # Save to database if repository is available
                        if self.repository:
                            try:
                                self.repository.save_cost_of_living_data(cost_data)
                            except Exception as e:
                                logger.warning(f"Failed to save cost of living data to database: {e}")
                        
                        logger.info(f"FRED data fetched successfully for {location}")
                        return cost_data
                
                logger.warning(f"FRED API call failed for {location}: {response.error}")
                return self._get_fallback_cost_of_living_data(location)
                
        except Exception as e:
            logger.error(f"Error fetching FRED data for {location}: {e}")
            return self._get_fallback_cost_of_living_data(location)
    
    async def fetch_indeed_job_market_data(self, location: str, occupation: str = None) -> Optional[JobMarketDataPoint]:
        """
        Fetch job market data from Indeed API
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
        
        Returns:
            JobMarketDataPoint or None if unavailable
        """
        cache_key = self._get_cache_key('job_market', location, occupation)
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            logger.info(f"Indeed data retrieved from cache for {location}")
            return JobMarketDataPoint(**cached_data)
        
        # Check if API key is available
        if not self.api_keys['indeed']:
            logger.warning("Indeed API key not configured")
            return None
        
        try:
            async with AsyncAPIClient() as api_client:
                params = {
                    'q': occupation or 'software engineer',
                    'l': location,
                    'sort': 'date',
                    'radius': 25,
                    'limit': 25
                }
                
                response = await api_client.get_indeed_data(
                    publisher_id=self.api_keys['indeed'],
                    **params
                )
                
                if response.success and response.data:
                    # Parse Indeed response
                    job_data = self._parse_indeed_response(response.data, location, occupation)
                    if job_data:
                        # Validate data
                        validation_result = self.validator.validate_job_market_data(asdict(job_data))
                        job_data.validation_result = validation_result
                        
                        # Cache the result (longer TTL for job market data)
                        self._set_cached_data(cache_key, asdict(job_data), ttl=43200)
                        
                        # Save to database if repository is available
                        if self.repository:
                            try:
                                self.repository.save_job_market_data(job_data)
                            except Exception as e:
                                logger.warning(f"Failed to save job market data to database: {e}")
                        
                        logger.info(f"Indeed data fetched successfully for {location}")
                        return job_data
                
                logger.warning(f"Indeed API call failed for {location}: {response.error}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Indeed data for {location}: {e}")
            return None
    
    async def get_comprehensive_salary_data(self, location: str, occupation: str = None) -> ComprehensiveSalaryData:
        """
        Get comprehensive salary data from all available sources
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
        
        Returns:
            ComprehensiveSalaryData with all available data
        """
        logger.info(f"Fetching comprehensive salary data for {location}, occupation: {occupation}")
        
        # Fetch data from all sources concurrently
        tasks = [
            self.fetch_bls_salary_data(location, occupation),
            self.fetch_census_salary_data(location),
            self.fetch_fred_cost_of_living_data(location),
            self.fetch_indeed_job_market_data(location, occupation)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        salary_data_points = []
        cost_of_living_data = None
        job_market_data = None
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in data fetch task {i}: {result}")
                continue
            
            if result is None:
                continue
            
            if isinstance(result, SalaryDataPoint):
                salary_data_points.append(result)
            elif isinstance(result, CostOfLivingDataPoint):
                cost_of_living_data = result
            elif isinstance(result, JobMarketDataPoint):
                job_market_data = result
        
        # Calculate overall confidence and quality scores
        overall_confidence = self._calculate_overall_confidence(salary_data_points, cost_of_living_data, job_market_data)
        data_quality_score = self._calculate_data_quality_score(salary_data_points, cost_of_living_data, job_market_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(salary_data_points, cost_of_living_data, job_market_data)
        
        comprehensive_data = ComprehensiveSalaryData(
            location=location,
            occupation=occupation or 'General',
            salary_data=salary_data_points,
            cost_of_living_data=cost_of_living_data,
            job_market_data=job_market_data,
            overall_confidence_score=overall_confidence,
            data_quality_score=data_quality_score,
            recommendations=recommendations
        )
        
        # Save confidence score to database if repository is available
        if self.repository:
            try:
                self.repository.save_confidence_score(comprehensive_data)
            except Exception as e:
                logger.warning(f"Failed to save confidence score to database: {e}")
        
        logger.info(f"Comprehensive salary data compiled for {location} with {len(salary_data_points)} salary sources")
        return comprehensive_data
    
    def _parse_bls_response(self, data: Dict[str, Any], location: str, occupation: str = None) -> Optional[SalaryDataPoint]:
        """Parse BLS API response"""
        try:
            if 'Results' in data and data['Results']:
                series_data = data['Results']['series'][0]['data']
                
                if series_data:
                    latest_data = series_data[0]
                    median_salary = float(latest_data.get('value', 0))
                    
                    if median_salary > 0:
                        return SalaryDataPoint(
                            source=DataSource.BLS,
                            location=location,
                            occupation=occupation or 'General',
                            median_salary=median_salary,
                            mean_salary=median_salary * 1.1,
                            percentile_25=median_salary * 0.7,
                            percentile_75=median_salary * 1.3,
                            sample_size=1000000,
                            year=int(latest_data.get('year', datetime.now().year)),
                            confidence_score=0.85
                        )
        except Exception as e:
            logger.error(f"Error parsing BLS response: {e}")
        
        return None
    
    def _parse_census_response(self, data: List[List[str]], location: str) -> Optional[SalaryDataPoint]:
        """Parse Census API response"""
        try:
            if len(data) > 1:
                row = data[1]
                values = dict(zip(data[0], row))
                
                median_income = float(values.get('B19013_001E', 0))
                
                if median_income > 0:
                    return SalaryDataPoint(
                        source=DataSource.CENSUS,
                        location=location,
                        occupation='General',
                        median_salary=median_income,
                        mean_salary=median_income * 1.15,
                        percentile_25=median_income * 0.65,
                        percentile_75=median_income * 1.35,
                        sample_size=500000,
                        year=2022,
                        confidence_score=0.90
                    )
        except Exception as e:
            logger.error(f"Error parsing Census response: {e}")
        
        return None
    
    def _parse_fred_response(self, data: Dict[str, Any], location: str) -> Optional[CostOfLivingDataPoint]:
        """Parse FRED API response"""
        try:
            if 'observations' in data and data['observations']:
                latest_observation = data['observations'][0]
                overall_cost_index = float(latest_observation.get('value', 100.0))
                
                return CostOfLivingDataPoint(
                    location=location,
                    overall_cost_index=overall_cost_index,
                    housing_cost_index=overall_cost_index * 1.1,
                    transportation_cost_index=overall_cost_index * 0.9,
                    food_cost_index=overall_cost_index * 0.8,
                    healthcare_cost_index=overall_cost_index * 1.2,
                    utilities_cost_index=overall_cost_index * 0.7,
                    year=datetime.now().year,
                    confidence_score=0.80
                )
        except Exception as e:
            logger.error(f"Error parsing FRED response: {e}")
        
        return None
    
    def _parse_indeed_response(self, data: Dict[str, Any], location: str, occupation: str = None) -> Optional[JobMarketDataPoint]:
        """Parse Indeed API response"""
        try:
            if 'results' in data:
                results = data['results']
                
                if results:
                    # Calculate average salary from available data
                    salaries = []
                    for job in results:
                        if 'salary' in job and job['salary']:
                            salary_range = self._parse_salary_range(job['salary'])
                            if salary_range:
                                salaries.extend(salary_range)
                    
                    if salaries:
                        avg_salary = sum(salaries) / len(salaries)
                        min_salary = min(salaries)
                        max_salary = max(salaries)
                    else:
                        # Use fallback data if no salary info
                        fallback = self.fallback_salary_data.get(location, {})
                        avg_salary = fallback.get('median_salary', 60000)
                        min_salary = fallback.get('percentile_25', 40000)
                        max_salary = fallback.get('percentile_75', 90000)
                    
                    return JobMarketDataPoint(
                        location=location,
                        occupation=occupation or 'General',
                        job_count=len(results),
                        average_salary=avg_salary,
                        salary_range_min=min_salary,
                        salary_range_max=max_salary,
                        demand_score=self._calculate_demand_score(len(results), avg_salary),
                        confidence_score=0.75
                    )
        except Exception as e:
            logger.error(f"Error parsing Indeed response: {e}")
        
        return None
    
    def _get_fallback_salary_data(self, location: str, occupation: str = None) -> SalaryDataPoint:
        """Get fallback salary data"""
        fallback = self.fallback_salary_data.get(location, self.fallback_salary_data['Atlanta'])
        
        return SalaryDataPoint(
            source=DataSource.FALLBACK,
            location=location,
            occupation=occupation or 'General',
            median_salary=fallback['median_salary'],
            mean_salary=fallback['mean_salary'],
            percentile_25=fallback['percentile_25'],
            percentile_75=fallback['percentile_75'],
            sample_size=fallback['sample_size'],
            year=fallback['year'],
            confidence_score=fallback['confidence_score']
        )
    
    def _get_fallback_cost_of_living_data(self, location: str) -> CostOfLivingDataPoint:
        """Get fallback cost of living data"""
        fallback = self.fallback_cost_of_living.get(location, self.fallback_cost_of_living['Atlanta'])
        
        return CostOfLivingDataPoint(
            location=location,
            overall_cost_index=fallback['overall_cost_index'],
            housing_cost_index=fallback['housing_cost_index'],
            transportation_cost_index=fallback['transportation_cost_index'],
            food_cost_index=fallback['food_cost_index'],
            healthcare_cost_index=fallback['healthcare_cost_index'],
            utilities_cost_index=fallback['utilities_cost_index'],
            year=fallback['year'],
            confidence_score=fallback['confidence_score']
        )
    
    def _parse_salary_range(self, salary_str: str) -> List[float]:
        """Parse salary range from string"""
        try:
            salary_str = salary_str.lower().replace('$', '').replace(',', '')
            
            if 'k' in salary_str or 'thousand' in salary_str:
                salary_str = salary_str.replace('k', '000').replace('thousand', '000')
            
            if '-' in salary_str:
                parts = salary_str.split('-')
                if len(parts) == 2:
                    min_salary = float(parts[0].strip())
                    max_salary = float(parts[1].strip())
                    return [min_salary, max_salary]
            
            return [float(salary_str)]
            
        except (ValueError, AttributeError):
            return []
    
    def _calculate_demand_score(self, job_count: int, avg_salary: float) -> float:
        """Calculate demand score based on job count and salary"""
        job_score = min(job_count / 100, 1.0) * 100
        salary_score = min(avg_salary / 200000, 1.0) * 100
        return (job_score * 0.7) + (salary_score * 0.3)
    
    def _calculate_overall_confidence(self, salary_data: List[SalaryDataPoint], 
                                   cost_data: Optional[CostOfLivingDataPoint],
                                   job_data: Optional[JobMarketDataPoint]) -> float:
        """Calculate overall confidence score"""
        if not salary_data:
            return 0.0
        
        # Weight by source confidence and validation
        total_weight = 0
        weighted_confidence = 0
        
        for data_point in salary_data:
            weight = data_point.confidence_score
            if data_point.validation_result:
                weight *= data_point.validation_result.confidence_score
            total_weight += weight
            weighted_confidence += data_point.confidence_score * weight
        
        if cost_data:
            weight = cost_data.confidence_score
            if cost_data.validation_result:
                weight *= cost_data.validation_result.confidence_score
            total_weight += weight
            weighted_confidence += cost_data.confidence_score * weight
        
        if job_data:
            weight = job_data.confidence_score
            if job_data.validation_result:
                weight *= job_data.validation_result.confidence_score
            total_weight += weight
            weighted_confidence += job_data.confidence_score * weight
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _calculate_data_quality_score(self, salary_data: List[SalaryDataPoint],
                                   cost_data: Optional[CostOfLivingDataPoint],
                                   job_data: Optional[JobMarketDataPoint]) -> float:
        """Calculate overall data quality score"""
        scores = []
        
        for data_point in salary_data:
            if data_point.validation_result:
                scores.append(data_point.validation_result.data_quality_score)
        
        if cost_data and cost_data.validation_result:
            scores.append(cost_data.validation_result.data_quality_score)
        
        if job_data and job_data.validation_result:
            scores.append(job_data.validation_result.data_quality_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _generate_recommendations(self, salary_data: List[SalaryDataPoint],
                               cost_data: Optional[CostOfLivingDataPoint],
                               job_data: Optional[JobMarketDataPoint]) -> List[str]:
        """Generate recommendations based on data"""
        recommendations = []
        
        if salary_data:
            # Find the highest confidence salary data
            best_salary = max(salary_data, key=lambda x: x.confidence_score)
            
            if best_salary.median_salary > 80000:
                recommendations.append("High salary market - excellent earning potential")
            elif best_salary.median_salary > 60000:
                recommendations.append("Above-average salary market - good opportunities")
            else:
                recommendations.append("Consider salary negotiation strategies")
        
        if cost_data:
            if cost_data.overall_cost_index > 120:
                recommendations.append("High cost of living area - factor in housing costs")
            elif cost_data.overall_cost_index < 90:
                recommendations.append("Lower cost of living - good value for money")
        
        if job_data:
            if job_data.demand_score > 80:
                recommendations.append("High job demand - favorable market conditions")
            elif job_data.demand_score < 40:
                recommendations.append("Lower job demand - consider expanding search area")
        
        if not recommendations:
            recommendations.append("Consider multiple data sources for comprehensive analysis")
        
        return recommendations
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status and statistics"""
        if not self.redis_client:
            return {'status': 'unavailable', 'error': 'Redis not connected'}
        
        try:
            info = self.redis_client.info()
            return {
                'status': 'available',
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def clear_cache(self, pattern: str = "salary_data:*") -> bool:
        """Clear cache entries matching pattern"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries matching pattern: {pattern}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False 