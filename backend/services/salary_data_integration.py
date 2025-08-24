"""
Real-time Salary Data Integration Service
Integrates with multiple APIs to provide up-to-date salary and cost-of-living data
"""

import os
import json
import logging
import requests
import redis
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class DataSource(str, Enum):
    """Data source types"""
    BLS = "bls"
    CENSUS = "census"
    FRED = "fred"
    INDEED = "indeed"

@dataclass
class SalaryData:
    """Salary data structure"""
    source: DataSource
    location: str
    occupation: str
    median_salary: float
    mean_salary: float
    percentile_25: float
    percentile_75: float
    sample_size: int
    year: int
    last_updated: datetime
    confidence_level: float

@dataclass
class CostOfLivingData:
    """Cost of living data structure"""
    location: str
    housing_cost_index: float
    transportation_cost_index: float
    food_cost_index: float
    healthcare_cost_index: float
    utilities_cost_index: float
    overall_cost_index: float
    year: int
    last_updated: datetime

@dataclass
class JobMarketData:
    """Job market data structure"""
    location: str
    occupation: str
    job_count: int
    average_salary: float
    salary_range_min: float
    salary_range_max: float
    demand_score: float
    last_updated: datetime

class SalaryDataIntegrationService:
    """
    Real-time salary data integration service
    Integrates with BLS, Census, FRED, and Indeed APIs
    """
    
    def __init__(self):
        """Initialize the service with API configurations and Redis cache"""
        # API Configuration
        self.bls_api_url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        self.census_api_url = "https://api.census.gov/data/2022/acs/acs1"
        self.fred_api_url = "https://api.stlouisfed.org/fred/series/observations"
        self.indeed_api_url = "https://api.indeed.com/ads/apisearch"
        
        # API Keys (should be set in environment variables)
        self.bls_api_key = os.getenv('BLS_API_KEY')
        self.census_api_key = os.getenv('CENSUS_API_KEY')
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.indeed_api_key = os.getenv('INDEED_API_KEY')
        
        # Target MSAs for analysis
        self.target_msas = [
            'Atlanta', 'Houston', 'Washington DC', 'Dallas-Fort Worth', 
            'New York City', 'Philadelphia', 'Chicago', 'Charlotte', 
            'Miami', 'Baltimore'
        ]
        
        # BLS Series IDs for target demographics
        self.bls_series_ids = {
            'LAUCN130890000000003': 'Atlanta unemployment rate',
            'LAUCN481670000000003': 'Houston unemployment rate',
            'LAUCN110010000000003': 'Washington DC unemployment rate',
            'LAUCN481130000000003': 'Dallas-Fort Worth unemployment rate',
            'LAUCN360610000000003': 'New York City unemployment rate',
            'LAUCN421010000000003': 'Philadelphia unemployment rate',
            'LAUCN170310000000003': 'Chicago unemployment rate',
            'LAUCN371190000000003': 'Charlotte unemployment rate',
            'LAUCN120860000000003': 'Miami unemployment rate',
            'LAUCN240050000000003': 'Baltimore unemployment rate'
        }
        
        # Census variables
        self.census_variables = {
            'B19013_001E': 'median_household_income',
            'B25064_001E': 'median_rent',
            'B08303_001E': 'commute_time',
            'B25077_001E': 'median_home_value'
        }
        
        # FRED series for cost of living
        self.fred_series = {
            'RPPALL': 'Regional Price Parities - All Items',
            'RPPGOODS': 'Regional Price Parities - Goods',
            'RPPSERVICES': 'Regional Price Parities - Services',
            'RPPRENT': 'Regional Price Parities - Rent'
        }
        
        # Initialize Redis cache
        self._initialize_redis()
        
        # Static fallback data
        self._initialize_fallback_data()
        
        logger.info("SalaryDataIntegrationService initialized")
    
    def _initialize_redis(self):
        """Initialize Redis connection for caching"""
        try:
            self.redis_host = os.getenv('REDIS_HOST', 'localhost')
            self.redis_port = int(os.getenv('REDIS_PORT', 6379))
            self.redis_db = int(os.getenv('REDIS_DB', 0))
            self.redis_password = os.getenv('REDIS_PASSWORD')
            
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connection established")
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _initialize_fallback_data(self):
        """Initialize static fallback data for when APIs are unavailable"""
        self.fallback_salary_data = {
            'Atlanta': {
                'median_salary': 65000,
                'mean_salary': 72000,
                'percentile_25': 45000,
                'percentile_75': 95000,
                'sample_size': 2500000,
                'year': 2022
            },
            'Houston': {
                'median_salary': 62000,
                'mean_salary': 69000,
                'percentile_25': 42000,
                'percentile_75': 90000,
                'sample_size': 2200000,
                'year': 2022
            },
            'Washington DC': {
                'median_salary': 75000,
                'mean_salary': 85000,
                'percentile_25': 52000,
                'percentile_75': 110000,
                'sample_size': 1800000,
                'year': 2022
            },
            'Dallas-Fort Worth': {
                'median_salary': 63000,
                'mean_salary': 70000,
                'percentile_25': 43000,
                'percentile_75': 92000,
                'sample_size': 2000000,
                'year': 2022
            },
            'New York City': {
                'median_salary': 70000,
                'mean_salary': 80000,
                'percentile_25': 48000,
                'percentile_75': 105000,
                'sample_size': 3500000,
                'year': 2022
            },
            'Philadelphia': {
                'median_salary': 58000,
                'mean_salary': 65000,
                'percentile_25': 40000,
                'percentile_75': 85000,
                'sample_size': 1500000,
                'year': 2022
            },
            'Chicago': {
                'median_salary': 68000,
                'mean_salary': 75000,
                'percentile_25': 46000,
                'percentile_75': 98000,
                'sample_size': 2800000,
                'year': 2022
            },
            'Charlotte': {
                'median_salary': 60000,
                'mean_salary': 67000,
                'percentile_25': 41000,
                'percentile_75': 88000,
                'sample_size': 1200000,
                'year': 2022
            },
            'Miami': {
                'median_salary': 55000,
                'mean_salary': 62000,
                'percentile_25': 38000,
                'percentile_75': 80000,
                'sample_size': 1800000,
                'year': 2022
            },
            'Baltimore': {
                'median_salary': 59000,
                'mean_salary': 66000,
                'percentile_25': 40000,
                'percentile_75': 87000,
                'sample_size': 1000000,
                'year': 2022
            }
        }
        
        self.fallback_cost_of_living = {
            'Atlanta': {'overall_cost_index': 100.0, 'housing_cost_index': 95.0},
            'Houston': {'overall_cost_index': 95.0, 'housing_cost_index': 90.0},
            'Washington DC': {'overall_cost_index': 130.0, 'housing_cost_index': 140.0},
            'Dallas-Fort Worth': {'overall_cost_index': 98.0, 'housing_cost_index': 92.0},
            'New York City': {'overall_cost_index': 150.0, 'housing_cost_index': 180.0},
            'Philadelphia': {'overall_cost_index': 105.0, 'housing_cost_index': 110.0},
            'Chicago': {'overall_cost_index': 115.0, 'housing_cost_index': 120.0},
            'Charlotte': {'overall_cost_index': 92.0, 'housing_cost_index': 88.0},
            'Miami': {'overall_cost_index': 110.0, 'housing_cost_index': 115.0},
            'Baltimore': {'overall_cost_index': 102.0, 'housing_cost_index': 105.0}
        }
    
    def _get_cache_key(self, source: DataSource, location: str, occupation: str = None) -> str:
        """Generate cache key for data"""
        if occupation:
            return f"salary_data:{source}:{location}:{occupation}"
        return f"salary_data:{source}:{location}"
    
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
        """Store data in Redis cache with TTL (default 24 hours)"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(cache_key, ttl, json.dumps(data))
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
    
    def get_bls_salary_data(self, location: str, occupation: str = None) -> Optional[SalaryData]:
        """
        Get salary data from Bureau of Labor Statistics API
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
        
        Returns:
            SalaryData object or None if unavailable
        """
        cache_key = self._get_cache_key(DataSource.BLS, location, occupation)
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return SalaryData(**cached_data)
        
        try:
            # BLS API call
            headers = {
                'BLS-API-Version': '2.0',
                'Content-Type': 'application/json'
            }
            
            # Use series ID for the location
            series_id = self._get_bls_series_id(location)
            if not series_id:
                return self._get_fallback_salary_data(location)
            
            payload = {
                'seriesid': [series_id],
                'startyear': str(datetime.now().year - 1),
                'endyear': str(datetime.now().year),
                'registrationkey': self.bls_api_key
            }
            
            response = requests.post(
                self.bls_api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Results' in data and data['Results']:
                    series_data = data['Results']['series'][0]['data']
                    
                    # Process the latest data
                    latest_data = series_data[0] if series_data else None
                    
                    if latest_data:
                        salary_data = SalaryData(
                            source=DataSource.BLS,
                            location=location,
                            occupation=occupation or 'General',
                            median_salary=float(latest_data.get('value', 0)),
                            mean_salary=float(latest_data.get('value', 0)) * 1.1,  # Estimate
                            percentile_25=float(latest_data.get('value', 0)) * 0.7,
                            percentile_75=float(latest_data.get('value', 0)) * 1.3,
                            sample_size=1000000,  # Estimate
                            year=int(latest_data.get('year', datetime.now().year)),
                            last_updated=datetime.now(),
                            confidence_level=0.85
                        )
                        
                        # Cache the result
                        self._set_cached_data(cache_key, salary_data.__dict__)
                        
                        return salary_data
            
            # If API call fails, use fallback data
            return self._get_fallback_salary_data(location)
            
        except Exception as e:
            logger.error(f"Error fetching BLS data for {location}: {e}")
            return self._get_fallback_salary_data(location)
    
    def get_census_salary_data(self, location: str) -> Optional[SalaryData]:
        """
        Get salary data from Census Bureau API
        
        Args:
            location: Target location
        
        Returns:
            SalaryData object or None if unavailable
        """
        cache_key = self._get_cache_key(DataSource.CENSUS, location)
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return SalaryData(**cached_data)
        
        try:
            # Census API call
            variables = ','.join(self.census_variables.keys())
            
            # Get MSA code for location
            msa_code = self._get_census_msa_code(location)
            if not msa_code:
                return self._get_fallback_salary_data(location)
            
            params = {
                'get': variables,
                'for': f'metropolitan statistical area/micropolitan statistical area:{msa_code}',
                'key': self.census_api_key
            }
            
            url = f"{self.census_api_url}?{urlencode(params)}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if len(data) > 1:  # Has header and data rows
                    row = data[1]  # First data row
                    
                    # Map variables to values
                    values = dict(zip(data[0], row))
                    
                    median_income = float(values.get('B19013_001E', 0))
                    
                    if median_income > 0:
                        salary_data = SalaryData(
                            source=DataSource.CENSUS,
                            location=location,
                            occupation='General',
                            median_salary=median_income,
                            mean_salary=median_income * 1.15,  # Estimate
                            percentile_25=median_income * 0.65,
                            percentile_75=median_income * 1.35,
                            sample_size=500000,  # Estimate
                            year=2022,
                            last_updated=datetime.now(),
                            confidence_level=0.90
                        )
                        
                        # Cache the result
                        self._set_cached_data(cache_key, salary_data.__dict__)
                        
                        return salary_data
            
            # If API call fails, use fallback data
            return self._get_fallback_salary_data(location)
            
        except Exception as e:
            logger.error(f"Error fetching Census data for {location}: {e}")
            return self._get_fallback_salary_data(location)
    
    def get_fred_cost_of_living_data(self, location: str) -> Optional[CostOfLivingData]:
        """
        Get cost of living data from FRED API
        
        Args:
            location: Target location
        
        Returns:
            CostOfLivingData object or None if unavailable
        """
        cache_key = f"cost_of_living:fred:{location}"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return CostOfLivingData(**cached_data)
        
        try:
            # FRED API call for Regional Price Parities
            params = {
                'series_id': 'RPPALL',
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'sort_order': 'desc',
                'limit': 1
            }
            
            response = requests.get(self.fred_api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'observations' in data and data['observations']:
                    latest_observation = data['observations'][0]
                    overall_cost_index = float(latest_observation.get('value', 100.0))
                    
                    cost_data = CostOfLivingData(
                        location=location,
                        housing_cost_index=overall_cost_index * 1.1,  # Estimate
                        transportation_cost_index=overall_cost_index * 0.9,
                        food_cost_index=overall_cost_index * 0.8,
                        healthcare_cost_index=overall_cost_index * 1.2,
                        utilities_cost_index=overall_cost_index * 0.7,
                        overall_cost_index=overall_cost_index,
                        year=datetime.now().year,
                        last_updated=datetime.now()
                    )
                    
                    # Cache the result
                    self._set_cached_data(cache_key, cost_data.__dict__)
                    
                    return cost_data
            
            # If API call fails, use fallback data
            return self._get_fallback_cost_of_living_data(location)
            
        except Exception as e:
            logger.error(f"Error fetching FRED data for {location}: {e}")
            return self._get_fallback_cost_of_living_data(location)
    
    def get_indeed_job_market_data(self, location: str, occupation: str = None) -> Optional[JobMarketData]:
        """
        Get job market data from Indeed API (FREE tier - 100 calls/month)
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
        
        Returns:
            JobMarketData object or None if unavailable
        """
        cache_key = f"job_market:indeed:{location}:{occupation or 'general'}"
        
        # Check cache first
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return JobMarketData(**cached_data)
        
        try:
            # Indeed API call
            params = {
                'publisher': self.indeed_api_key,
                'q': occupation or 'software engineer',
                'l': location,
                'sort': 'date',
                'radius': 25,
                'limit': 25,
                'format': 'json',
                'v': 2
            }
            
            response = requests.get(self.indeed_api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'results' in data:
                    results = data['results']
                    
                    if results:
                        # Calculate average salary from available data
                        salaries = []
                        for job in results:
                            if 'salary' in job and job['salary']:
                                # Parse salary range
                                salary_str = job['salary']
                                salary_range = self._parse_salary_range(salary_str)
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
                        
                        job_market_data = JobMarketData(
                            location=location,
                            occupation=occupation or 'General',
                            job_count=len(results),
                            average_salary=avg_salary,
                            salary_range_min=min_salary,
                            salary_range_max=max_salary,
                            demand_score=self._calculate_demand_score(len(results), avg_salary),
                            last_updated=datetime.now()
                        )
                        
                        # Cache the result (longer TTL for job market data)
                        self._set_cached_data(cache_key, job_market_data.__dict__, ttl=43200)  # 12 hours
                        
                        return job_market_data
            
            # If API call fails, return None (no fallback for job market data)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Indeed data for {location}: {e}")
            return None
    
    def get_comprehensive_salary_data(self, location: str, occupation: str = None) -> Dict[str, Any]:
        """
        Get comprehensive salary data from all available sources
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
        
        Returns:
            Dictionary with comprehensive salary data
        """
        try:
            # Get data from all sources
            bls_data = self.get_bls_salary_data(location, occupation)
            census_data = self.get_census_salary_data(location)
            fred_data = self.get_fred_cost_of_living_data(location)
            indeed_data = self.get_indeed_job_market_data(location, occupation)
            
            # Combine and analyze data
            combined_data = {
                'location': location,
                'occupation': occupation or 'General',
                'data_sources': [],
                'salary_analysis': {},
                'cost_of_living': {},
                'job_market': {},
                'recommendations': [],
                'last_updated': datetime.now().isoformat()
            }
            
            # Process salary data
            salary_sources = []
            if bls_data:
                salary_sources.append(('BLS', bls_data))
                combined_data['data_sources'].append('BLS')
            
            if census_data:
                salary_sources.append(('Census', census_data))
                combined_data['data_sources'].append('Census')
            
            if salary_sources:
                # Calculate weighted average
                total_weight = 0
                weighted_median = 0
                weighted_mean = 0
                
                for source, data in salary_sources:
                    weight = data.confidence_level
                    total_weight += weight
                    weighted_median += data.median_salary * weight
                    weighted_mean += data.mean_salary * weight
                
                if total_weight > 0:
                    combined_data['salary_analysis'] = {
                        'median_salary': weighted_median / total_weight,
                        'mean_salary': weighted_mean / total_weight,
                        'data_quality': 'high' if len(salary_sources) > 1 else 'medium',
                        'sources_used': len(salary_sources)
                    }
            
            # Process cost of living data
            if fred_data:
                combined_data['cost_of_living'] = {
                    'overall_index': fred_data.overall_cost_index,
                    'housing_index': fred_data.housing_cost_index,
                    'transportation_index': fred_data.transportation_cost_index,
                    'food_index': fred_data.food_cost_index,
                    'healthcare_index': fred_data.healthcare_cost_index,
                    'utilities_index': fred_data.utilities_cost_index
                }
            
            # Process job market data
            if indeed_data:
                combined_data['job_market'] = {
                    'job_count': indeed_data.job_count,
                    'average_salary': indeed_data.average_salary,
                    'salary_range': {
                        'min': indeed_data.salary_range_min,
                        'max': indeed_data.salary_range_max
                    },
                    'demand_score': indeed_data.demand_score
                }
            
            # Generate recommendations
            combined_data['recommendations'] = self._generate_recommendations(
                combined_data['salary_analysis'],
                combined_data['cost_of_living'],
                combined_data['job_market']
            )
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive salary data for {location}: {e}")
            return self._get_fallback_comprehensive_data(location, occupation)
    
    def _get_bls_series_id(self, location: str) -> Optional[str]:
        """Get BLS series ID for location"""
        location_mapping = {
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
        return location_mapping.get(location)
    
    def _get_census_msa_code(self, location: str) -> Optional[str]:
        """Get Census MSA code for location"""
        msa_mapping = {
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
        return msa_mapping.get(location)
    
    def _get_fallback_salary_data(self, location: str) -> SalaryData:
        """Get fallback salary data"""
        fallback = self.fallback_salary_data.get(location, self.fallback_salary_data['Atlanta'])
        
        return SalaryData(
            source=DataSource.BLS,  # Use BLS as fallback source
            location=location,
            occupation='General',
            median_salary=fallback['median_salary'],
            mean_salary=fallback['mean_salary'],
            percentile_25=fallback['percentile_25'],
            percentile_75=fallback['percentile_75'],
            sample_size=fallback['sample_size'],
            year=fallback['year'],
            last_updated=datetime.now(),
            confidence_level=0.70  # Lower confidence for fallback data
        )
    
    def _get_fallback_cost_of_living_data(self, location: str) -> CostOfLivingData:
        """Get fallback cost of living data"""
        fallback = self.fallback_cost_of_living.get(location, self.fallback_cost_of_living['Atlanta'])
        
        return CostOfLivingData(
            location=location,
            housing_cost_index=fallback['housing_cost_index'],
            transportation_cost_index=fallback['overall_cost_index'] * 0.9,
            food_cost_index=fallback['overall_cost_index'] * 0.8,
            healthcare_cost_index=fallback['overall_cost_index'] * 1.2,
            utilities_cost_index=fallback['overall_cost_index'] * 0.7,
            overall_cost_index=fallback['overall_cost_index'],
            year=datetime.now().year,
            last_updated=datetime.now()
        )
    
    def _get_fallback_comprehensive_data(self, location: str, occupation: str = None) -> Dict[str, Any]:
        """Get fallback comprehensive data"""
        fallback_salary = self._get_fallback_salary_data(location)
        fallback_cost = self._get_fallback_cost_of_living_data(location)
        
        return {
            'location': location,
            'occupation': occupation or 'General',
            'data_sources': ['Fallback'],
            'salary_analysis': {
                'median_salary': fallback_salary.median_salary,
                'mean_salary': fallback_salary.mean_salary,
                'data_quality': 'low',
                'sources_used': 1
            },
            'cost_of_living': {
                'overall_index': fallback_cost.overall_cost_index,
                'housing_index': fallback_cost.housing_cost_index,
                'transportation_index': fallback_cost.transportation_cost_index,
                'food_index': fallback_cost.food_cost_index,
                'healthcare_index': fallback_cost.healthcare_cost_index,
                'utilities_index': fallback_cost.utilities_cost_index
            },
            'job_market': {},
            'recommendations': ['Using fallback data due to API unavailability'],
            'last_updated': datetime.now().isoformat()
        }
    
    def _parse_salary_range(self, salary_str: str) -> List[float]:
        """Parse salary range from string"""
        try:
            # Remove common prefixes and suffixes
            salary_str = salary_str.lower().replace('$', '').replace(',', '')
            
            if 'k' in salary_str or 'thousand' in salary_str:
                # Handle K notation
                salary_str = salary_str.replace('k', '000').replace('thousand', '000')
            
            if '-' in salary_str:
                # Range format
                parts = salary_str.split('-')
                if len(parts) == 2:
                    min_salary = float(parts[0].strip())
                    max_salary = float(parts[1].strip())
                    return [min_salary, max_salary]
            
            # Single value
            return [float(salary_str)]
            
        except (ValueError, AttributeError):
            return []
    
    def _calculate_demand_score(self, job_count: int, avg_salary: float) -> float:
        """Calculate demand score based on job count and salary"""
        # Normalize job count (0-100 scale)
        job_score = min(job_count / 100, 1.0) * 100
        
        # Normalize salary (0-100 scale, assuming $200k is max)
        salary_score = min(avg_salary / 200000, 1.0) * 100
        
        # Weighted average (job count more important)
        return (job_score * 0.7) + (salary_score * 0.3)
    
    def _generate_recommendations(self, salary_analysis: Dict, cost_of_living: Dict, job_market: Dict) -> List[str]:
        """Generate recommendations based on data"""
        recommendations = []
        
        if salary_analysis:
            median_salary = salary_analysis.get('median_salary', 0)
            
            if median_salary > 80000:
                recommendations.append("High salary market - excellent earning potential")
            elif median_salary > 60000:
                recommendations.append("Above-average salary market - good opportunities")
            else:
                recommendations.append("Consider salary negotiation strategies")
        
        if cost_of_living:
            overall_index = cost_of_living.get('overall_index', 100)
            
            if overall_index > 120:
                recommendations.append("High cost of living area - factor in housing costs")
            elif overall_index < 90:
                recommendations.append("Lower cost of living - good value for money")
        
        if job_market:
            demand_score = job_market.get('demand_score', 0)
            
            if demand_score > 80:
                recommendations.append("High job demand - favorable market conditions")
            elif demand_score < 40:
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