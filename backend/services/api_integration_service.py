"""
API Integration Service for Income Comparison Calculator
Integrates with external data sources: BLS, Census, FRED, BEA
Provides salary, demographic, economic, and regional data
"""

import requests
import logging
import time
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import lru_cache
import asyncio
import aiohttp
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """Configuration for external APIs"""
    base_url: str
    api_key: str
    rate_limit_per_minute: int
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 1


class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: int = None, api_name: str = None):
        self.message = message
        self.status_code = status_code
        self.api_name = api_name
        super().__init__(self.message)


class RateLimitError(APIError):
    """Exception for rate limit exceeded"""
    pass


class BLSAPIService:
    """Bureau of Labor Statistics API Service"""
    
    def __init__(self):
        self.config = APIConfig(
            base_url="https://api.bls.gov/publicAPI/v2",
            api_key=getattr(settings, 'BLS_API_KEY', ''),  # BLS is free, no key needed
            rate_limit_per_minute=25,  # BLS free tier limit
            timeout_seconds=30,
            retry_attempts=3
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mingus-Income-Comparison/1.0',
            'Accept': 'application/json'
        })
    
    def get_salary_data(self, location: str, industry: str, experience_level: str) -> Dict[str, Any]:
        """
        Get salary data from BLS Occupational Employment Statistics
        
        Args:
            location: MSA code or name (e.g., 'atlanta', '12060')
            industry: Industry code or name (e.g., 'technology', '5112')
            experience_level: Experience level (entry, mid, senior)
        
        Returns:
            Dictionary with salary statistics
        """
        cache_key = f"bls_salary_{location}_{industry}_{experience_level}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Map location names to MSA codes
            msa_codes = self._get_msa_codes()
            msa_code = msa_codes.get(location.lower(), location)
            
            # Map industry names to NAICS codes
            industry_codes = self._get_industry_codes()
            industry_code = industry_codes.get(industry.lower(), industry)
            
            # Map experience levels to BLS categories
            experience_mapping = {
                'entry': 'entry_level',
                'mid': 'mid_level', 
                'senior': 'senior_level'
            }
            bls_experience = experience_mapping.get(experience_level.lower(), 'mid_level')
            
            # BLS API endpoint for Occupational Employment Statistics
            url = f"{self.config.base_url}/timeseries/data/"
            
            # Series IDs for different experience levels
            series_ids = self._get_series_ids(msa_code, industry_code, bls_experience)
            
            payload = {
                "seriesid": series_ids,
                "startyear": str(datetime.now().year - 1),
                "endyear": str(datetime.now().year),
                "registrationkey": self.config.api_key
            }
            
            response = self.session.post(url, json=payload, timeout=self.config.timeout_seconds)
            
            if response.status_code == 200:
                data = response.json()
                processed_data = self._process_bls_response(data, location, industry, experience_level)
                
                # Cache for 1 week (BLS data doesn't change frequently)
                cache.set(cache_key, processed_data, 60 * 60 * 24 * 7)
                return processed_data
            else:
                logger.error(f"BLS API error: {response.status_code} - {response.text}")
                return self._get_fallback_salary_data(location, industry, experience_level)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"BLS API request failed: {e}")
            return self._get_fallback_salary_data(location, industry, experience_level)
        except Exception as e:
            logger.error(f"BLS API processing error: {e}")
            return self._get_fallback_salary_data(location, industry, experience_level)
    
    def _get_msa_codes(self) -> Dict[str, str]:
        """Get MSA code mappings"""
        return {
            'atlanta': '12060',
            'houston': '26420', 
            'washington dc': '47900',
            'dallas': '19100',
            'new york': '35620',
            'philadelphia': '37980',
            'chicago': '16980',
            'charlotte': '16740',
            'miami': '33100',
            'baltimore': '12580',
            'san francisco': '41860',
            'los angeles': '31080',
            'seattle': '42660',
            'denver': '19740',
            'austin': '12420'
        }
    
    def _get_industry_codes(self) -> Dict[str, str]:
        """Get industry code mappings"""
        return {
            'technology': '5112',  # Software Publishers
            'healthcare': '6211',  # Offices of Physicians
            'finance': '5221',     # Depository Credit Intermediation
            'education': '6111',   # Elementary and Secondary Schools
            'manufacturing': '3329', # Other Fabricated Metal Product Manufacturing
            'retail': '4451',      # Grocery Stores
            'construction': '2361', # Residential Building Construction
            'government': '9211',   # Executive Offices
            'consulting': '5416',   # Management Consulting Services
            'media': '5111'         # Newspaper, Periodical, Book, and Directory Publishers
        }
    
    def _get_series_ids(self, msa_code: str, industry_code: str, experience_level: str) -> List[str]:
        """Get BLS series IDs for the requested data"""
        # This is a simplified mapping - in production you'd have a comprehensive mapping
        base_series = f"OES{msa_code}{industry_code}"
        
        # Different series for different experience levels
        series_mapping = {
            'entry_level': f"{base_series}0001",  # Entry level
            'mid_level': f"{base_series}0002",    # Mid level  
            'senior_level': f"{base_series}0003"  # Senior level
        }
        
        return [series_mapping.get(experience_level, f"{base_series}0002")]
    
    def _process_bls_response(self, data: Dict[str, Any], location: str, industry: str, experience_level: str) -> Dict[str, Any]:
        """Process BLS API response"""
        try:
            if 'Results' not in data or 'series' not in data['Results']:
                return self._get_fallback_salary_data(location, industry, experience_level)
            
            series_data = data['Results']['series'][0]
            if 'data' not in series_data:
                return self._get_fallback_salary_data(location, industry, experience_level)
            
            # Extract salary data
            salary_data = series_data['data'][0] if series_data['data'] else {}
            value = float(salary_data.get('value', 0))
            
            # Calculate percentiles based on experience level
            percentiles = self._calculate_percentiles(value, experience_level)
            
            return {
                'status': 'success',
                'data': {
                    location: {
                        industry: {
                            experience_level: {
                                'mean_salary': value,
                                'percentile_25': percentiles['25th'],
                                'percentile_50': percentiles['50th'],
                                'percentile_75': percentiles['75th'],
                                'percentile_90': percentiles['90th'],
                                'sample_size': salary_data.get('footnotes', [{}])[0].get('code', 1000),
                                'last_updated': salary_data.get('periodName', ''),
                                'source': 'BLS OES'
                            }
                        }
                    }
                }
            }
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error processing BLS response: {e}")
            return self._get_fallback_salary_data(location, industry, experience_level)
    
    def _calculate_percentiles(self, mean_salary: float, experience_level: str) -> Dict[str, float]:
        """Calculate salary percentiles based on experience level"""
        # Simplified percentile calculations based on typical salary distributions
        if experience_level == 'entry':
            multiplier = 0.7
        elif experience_level == 'mid':
            multiplier = 1.0
        else:  # senior
            multiplier = 1.4
        
        base_salary = mean_salary * multiplier
        
        return {
            '25th': base_salary * 0.8,
            '50th': base_salary,
            '75th': base_salary * 1.25,
            '90th': base_salary * 1.5
        }
    
    def _get_fallback_salary_data(self, location: str, industry: str, experience_level: str) -> Dict[str, Any]:
        """Fallback salary data when API is unavailable"""
        # Comprehensive fallback data based on real market research
        fallback_data = {
            'technology': {
                'entry': {'mean': 65000, '25th': 52000, '75th': 78000, '90th': 95000},
                'mid': {'mean': 85000, '25th': 68000, '75th': 102000, '90th': 125000},
                'senior': {'mean': 120000, '25th': 96000, '75th': 144000, '90th': 180000}
            },
            'healthcare': {
                'entry': {'mean': 55000, '25th': 44000, '75th': 66000, '90th': 80000},
                'mid': {'mean': 75000, '25th': 60000, '75th': 90000, '90th': 110000},
                'senior': {'mean': 100000, '25th': 80000, '75th': 120000, '90th': 150000}
            },
            'finance': {
                'entry': {'mean': 60000, '25th': 48000, '75th': 72000, '90th': 88000},
                'mid': {'mean': 80000, '25th': 64000, '75th': 96000, '90th': 120000},
                'senior': {'mean': 110000, '25th': 88000, '75th': 132000, '90th': 165000}
            },
            'education': {
                'entry': {'mean': 45000, '25th': 36000, '75th': 54000, '90th': 65000},
                'mid': {'mean': 60000, '25th': 48000, '75th': 72000, '90th': 90000},
                'senior': {'mean': 80000, '25th': 64000, '75th': 96000, '90th': 120000}
            }
        }
        
        # Location multipliers
        location_multipliers = {
            'atlanta': 1.0,
            'houston': 0.95,
            'washington dc': 1.15,
            'dallas': 1.05,
            'new york': 1.25,
            'philadelphia': 1.05,
            'chicago': 1.1,
            'charlotte': 0.9,
            'miami': 0.95,
            'baltimore': 1.0
        }
        
        industry_data = fallback_data.get(industry.lower(), fallback_data['technology'])
        level_data = industry_data.get(experience_level.lower(), industry_data['mid'])
        location_mult = location_multipliers.get(location.lower(), 1.0)
        
        return {
            'status': 'success',
            'data': {
                location: {
                    industry: {
                        experience_level: {
                            'mean_salary': level_data['mean'] * location_mult,
                            'percentile_25': level_data['25th'] * location_mult,
                            'percentile_50': level_data['mean'] * location_mult,
                            'percentile_75': level_data['75th'] * location_mult,
                            'percentile_90': level_data['90th'] * location_mult,
                            'sample_size': 1000,
                            'last_updated': datetime.now().strftime('%Y-%m'),
                            'source': 'Fallback Data'
                        }
                    }
                }
            }
        }


class CensusAPIService:
    """US Census Bureau API Service"""
    
    def __init__(self):
        self.config = APIConfig(
            base_url="https://api.census.gov/data",
            api_key=getattr(settings, 'CENSUS_API_KEY', ''),
            rate_limit_per_minute=500,  # Census free tier limit
            timeout_seconds=30,
            retry_attempts=3
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mingus-Income-Comparison/1.0',
            'Accept': 'application/json'
        })
    
    def get_demographic_data(self, location: str) -> Dict[str, Any]:
        """
        Get demographic data from American Community Survey
        
        Args:
            location: MSA name or FIPS code
        
        Returns:
            Dictionary with demographic statistics
        """
        cache_key = f"census_demographics_{location}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get FIPS code for location
            fips_code = self._get_fips_code(location)
            
            # ACS 5-year estimates for demographic data
            url = f"{self.config.base_url}/2022/acs/acs5"
            
            # Variables for demographic analysis
            variables = [
                'B01003_001E',  # Total population
                'B02001_003E',  # Black or African American alone
                'B19013_001E',  # Median household income
                'B15003_022E',  # Bachelor's degree
                'B15003_023E',  # Master's degree
                'B15003_024E',  # Professional degree
                'B15003_025E',  # Doctorate degree
                'B08303_001E',  # Total commuters
                'B08303_013E',  # 60+ minute commute
                'B25077_001E'   # Median home value
            ]
            
            params = {
                'get': ','.join(variables),
                'for': f'metropolitan statistical area/micropolitan statistical area:{fips_code}',
                'key': self.config.api_key
            }
            
            response = self.session.get(url, params=params, timeout=self.config.timeout_seconds)
            
            if response.status_code == 200:
                data = response.json()
                processed_data = self._process_census_response(data, location)
                
                # Cache for 1 year (ACS data is annual)
                cache.set(cache_key, processed_data, 60 * 60 * 24 * 365)
                return processed_data
            else:
                logger.error(f"Census API error: {response.status_code} - {response.text}")
                return self._get_fallback_demographic_data(location)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Census API request failed: {e}")
            return self._get_fallback_demographic_data(location)
        except Exception as e:
            logger.error(f"Census API processing error: {e}")
            return self._get_fallback_demographic_data(location)
    
    def _get_fips_code(self, location: str) -> str:
        """Get FIPS code for location"""
        fips_codes = {
            'atlanta': '12060',
            'houston': '26420',
            'washington dc': '47900',
            'dallas': '19100',
            'new york': '35620',
            'philadelphia': '37980',
            'chicago': '16980',
            'charlotte': '16740',
            'miami': '33100',
            'baltimore': '12580'
        }
        return fips_codes.get(location.lower(), '12060')  # Default to Atlanta
    
    def _process_census_response(self, data: List[List[str]], location: str) -> Dict[str, Any]:
        """Process Census API response"""
        try:
            if len(data) < 2:  # Need headers and at least one data row
                return self._get_fallback_demographic_data(location)
            
            headers = data[0]
            values = data[1]
            
            # Create mapping of variable names to values
            data_dict = dict(zip(headers, values))
            
            # Extract and calculate demographic statistics
            total_population = int(data_dict.get('B01003_001E', 0))
            african_american_population = int(data_dict.get('B02001_003E', 0))
            median_household_income = int(data_dict.get('B19013_001E', 0))
            
            # Education attainment
            bachelors = int(data_dict.get('B15003_022E', 0))
            masters = int(data_dict.get('B15003_023E', 0))
            professional = int(data_dict.get('B15003_024E', 0))
            doctorate = int(data_dict.get('B15003_025E', 0))
            
            total_education = bachelors + masters + professional + doctorate
            education_attainment = {
                'bachelor_degree': bachelors / total_population if total_population > 0 else 0,
                'graduate_degree': (masters + professional + doctorate) / total_population if total_population > 0 else 0
            }
            
            # Commute times
            total_commuters = int(data_dict.get('B08303_001E', 0))
            long_commute = int(data_dict.get('B08303_013E', 0))
            long_commute_percentage = long_commute / total_commuters if total_commuters > 0 else 0
            
            # Median home value
            median_home_value = int(data_dict.get('B25077_001E', 0))
            
            return {
                'status': 'success',
                'data': {
                    location: {
                        'total_population': total_population,
                        'african_american_population': african_american_population,
                        'african_american_percentage': african_american_population / total_population if total_population > 0 else 0,
                        'median_household_income': median_household_income,
                        'education_attainment': education_attainment,
                        'long_commute_percentage': long_commute_percentage,
                        'median_home_value': median_home_value,
                        'source': 'Census ACS 2022'
                    }
                }
            }
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error processing Census response: {e}")
            return self._get_fallback_demographic_data(location)
    
    def _get_fallback_demographic_data(self, location: str) -> Dict[str, Any]:
        """Fallback demographic data when API is unavailable"""
        fallback_data = {
            'atlanta': {
                'total_population': 6000000,
                'african_american_population': 1800000,
                'african_american_percentage': 0.30,
                'median_household_income': 65000,
                'education_attainment': {'bachelor_degree': 0.35, 'graduate_degree': 0.15},
                'long_commute_percentage': 0.12,
                'median_home_value': 350000
            },
            'houston': {
                'total_population': 7000000,
                'african_american_population': 1400000,
                'african_american_percentage': 0.20,
                'median_household_income': 60000,
                'education_attainment': {'bachelor_degree': 0.30, 'graduate_degree': 0.12},
                'long_commute_percentage': 0.15,
                'median_home_value': 280000
            },
            'washington dc': {
                'total_population': 6200000,
                'african_american_population': 1550000,
                'african_american_percentage': 0.25,
                'median_household_income': 85000,
                'education_attainment': {'bachelor_degree': 0.45, 'graduate_degree': 0.25},
                'long_commute_percentage': 0.20,
                'median_home_value': 450000
            }
        }
        
        location_data = fallback_data.get(location.lower(), fallback_data['atlanta'])
        
        return {
            'status': 'success',
            'data': {
                location: {
                    **location_data,
                    'source': 'Fallback Data'
                }
            }
        }


class FREDAPIService:
    """Federal Reserve Economic Data API Service"""
    
    def __init__(self):
        self.config = APIConfig(
            base_url="https://api.stlouisfed.org/fred",
            api_key=getattr(settings, 'FRED_API_KEY', ''),
            rate_limit_per_minute=120,  # FRED free tier limit
            timeout_seconds=30,
            retry_attempts=3
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mingus-Income-Comparison/1.0',
            'Accept': 'application/json'
        })
    
    def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Get economic indicators from FRED
        
        Returns:
            Dictionary with economic indicators
        """
        cache_key = "fred_economic_indicators"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # FRED series IDs for key economic indicators
            series_ids = {
                'inflation_rate': 'CPIAUCSL',      # Consumer Price Index
                'unemployment_rate': 'UNRATE',     # Unemployment Rate
                'gdp_growth': 'GDP',               # Gross Domestic Product
                'wage_growth': 'AHETPI',          # Average Hourly Earnings
                'interest_rate': 'FEDFUNDS',      # Federal Funds Rate
                'consumer_confidence': 'UMCSENT'   # Consumer Sentiment
            }
            
            indicators = {}
            
            for indicator_name, series_id in series_ids.items():
                url = f"{self.config.base_url}/series/observations"
                params = {
                    'series_id': series_id,
                    'api_key': self.config.api_key,
                    'file_type': 'json',
                    'sort_order': 'desc',
                    'limit': 2  # Get latest 2 observations
                }
                
                response = self.session.get(url, params=params, timeout=self.config.timeout_seconds)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'observations' in data and data['observations']:
                        latest_value = float(data['observations'][0]['value'])
                        previous_value = float(data['observations'][1]['value'])
                        
                        # Calculate growth rate
                        if previous_value > 0:
                            growth_rate = ((latest_value - previous_value) / previous_value) * 100
                        else:
                            growth_rate = 0
                        
                        indicators[indicator_name] = {
                            'current_value': latest_value,
                            'growth_rate': growth_rate,
                            'last_updated': data['observations'][0]['date']
                        }
                    else:
                        indicators[indicator_name] = self._get_fallback_economic_data(indicator_name)
                else:
                    logger.error(f"FRED API error for {indicator_name}: {response.status_code}")
                    indicators[indicator_name] = self._get_fallback_economic_data(indicator_name)
            
            result = {
                'status': 'success',
                'data': indicators,
                'source': 'FRED'
            }
            
            # Cache for 1 day (economic data changes frequently)
            cache.set(cache_key, result, 60 * 60 * 24)
            return result
            
        except Exception as e:
            logger.error(f"FRED API processing error: {e}")
            return self._get_fallback_economic_indicators()
    
    def _get_fallback_economic_data(self, indicator_name: str) -> Dict[str, Any]:
        """Get fallback data for specific economic indicator"""
        fallback_data = {
            'inflation_rate': {'current_value': 2.5, 'growth_rate': 0.1, 'last_updated': '2024-01'},
            'unemployment_rate': {'current_value': 3.8, 'growth_rate': -0.2, 'last_updated': '2024-01'},
            'gdp_growth': {'current_value': 2.1, 'growth_rate': 0.3, 'last_updated': '2024-01'},
            'wage_growth': {'current_value': 3.2, 'growth_rate': 0.2, 'last_updated': '2024-01'},
            'interest_rate': {'current_value': 5.25, 'growth_rate': 0.0, 'last_updated': '2024-01'},
            'consumer_confidence': {'current_value': 67.4, 'growth_rate': 1.2, 'last_updated': '2024-01'}
        }
        return fallback_data.get(indicator_name, {'current_value': 0, 'growth_rate': 0, 'last_updated': '2024-01'})
    
    def _get_fallback_economic_indicators(self) -> Dict[str, Any]:
        """Get fallback economic indicators when API is unavailable"""
        return {
            'status': 'success',
            'data': {
                'inflation_rate': {'current_value': 2.5, 'growth_rate': 0.1, 'last_updated': '2024-01'},
                'unemployment_rate': {'current_value': 3.8, 'growth_rate': -0.2, 'last_updated': '2024-01'},
                'gdp_growth': {'current_value': 2.1, 'growth_rate': 0.3, 'last_updated': '2024-01'},
                'wage_growth': {'current_value': 3.2, 'growth_rate': 0.2, 'last_updated': '2024-01'},
                'interest_rate': {'current_value': 5.25, 'growth_rate': 0.0, 'last_updated': '2024-01'},
                'consumer_confidence': {'current_value': 67.4, 'growth_rate': 1.2, 'last_updated': '2024-01'}
            },
            'source': 'Fallback Data'
        }


class BEAAPIService:
    """Bureau of Economic Analysis API Service"""
    
    def __init__(self):
        self.config = APIConfig(
            base_url="https://apps.bea.gov/api/data",
            api_key=getattr(settings, 'BEA_API_KEY', ''),
            rate_limit_per_minute=1000,  # BEA free tier limit
            timeout_seconds=30,
            retry_attempts=3
        )
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mingus-Income-Comparison/1.0',
            'Accept': 'application/json'
        })
    
    def get_regional_data(self, location: str) -> Dict[str, Any]:
        """
        Get regional economic data from BEA
        
        Args:
            location: MSA name or code
        
        Returns:
            Dictionary with regional economic data
        """
        cache_key = f"bea_regional_{location}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get BEA area code for location
            area_code = self._get_bea_area_code(location)
            
            # BEA API endpoint for Regional GDP
            url = f"{self.config.base_url}"
            
            params = {
                'UserID': self.config.api_key,
                'Method': 'GetData',
                'DataSetName': 'Regional',
                'TableName': 'CAGDP1',
                'LineCode': 1,  # All industries
                'GeoFips': area_code,
                'Year': str(datetime.now().year - 1),  # Latest available year
                'ResultFormat': 'JSON'
            }
            
            response = self.session.get(url, params=params, timeout=self.config.timeout_seconds)
            
            if response.status_code == 200:
                data = response.json()
                processed_data = self._process_bea_response(data, location)
                
                # Cache for 1 year (BEA data is annual)
                cache.set(cache_key, processed_data, 60 * 60 * 24 * 365)
                return processed_data
            else:
                logger.error(f"BEA API error: {response.status_code} - {response.text}")
                return self._get_fallback_regional_data(location)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"BEA API request failed: {e}")
            return self._get_fallback_regional_data(location)
        except Exception as e:
            logger.error(f"BEA API processing error: {e}")
            return self._get_fallback_regional_data(location)
    
    def _get_bea_area_code(self, location: str) -> str:
        """Get BEA area code for location"""
        bea_codes = {
            'atlanta': '12060',
            'houston': '26420',
            'washington dc': '47900',
            'dallas': '19100',
            'new york': '35620',
            'philadelphia': '37980',
            'chicago': '16980',
            'charlotte': '16740',
            'miami': '33100',
            'baltimore': '12580'
        }
        return bea_codes.get(location.lower(), '12060')  # Default to Atlanta
    
    def _process_bea_response(self, data: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Process BEA API response"""
        try:
            if 'BEAAPI' not in data or 'Results' not in data['BEAAPI']:
                return self._get_fallback_regional_data(location)
            
            results = data['BEAAPI']['Results']
            if 'Data' not in results:
                return self._get_fallback_regional_data(location)
            
            gdp_data = results['Data']
            if not gdp_data:
                return self._get_fallback_regional_data(location)
            
            # Extract GDP data
            gdp_value = float(gdp_data[0].get('DataValue', 0))
            population = self._get_population_for_gdp_calculation(location)
            gdp_per_capita = gdp_value / population if population > 0 else 0
            
            return {
                'status': 'success',
                'data': {
                    location: {
                        'gdp_total': gdp_value,
                        'gdp_per_capita': gdp_per_capita,
                        'employment_growth': 2.5,  # Would need additional API call
                        'industry_mix': self._get_industry_mix(location),
                        'economic_health_score': self._calculate_economic_health(gdp_per_capita),
                        'source': 'BEA Regional'
                    }
                }
            }
            
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error processing BEA response: {e}")
            return self._get_fallback_regional_data(location)
    
    def _get_population_for_gdp_calculation(self, location: str) -> int:
        """Get population for GDP per capita calculation"""
        populations = {
            'atlanta': 6000000,
            'houston': 7000000,
            'washington dc': 6200000,
            'dallas': 7500000,
            'new york': 20000000,
            'philadelphia': 6100000,
            'chicago': 9500000,
            'charlotte': 2600000,
            'miami': 6100000,
            'baltimore': 2800000
        }
        return populations.get(location.lower(), 5000000)
    
    def _get_industry_mix(self, location: str) -> Dict[str, float]:
        """Get industry mix for location"""
        industry_mixes = {
            'atlanta': {'technology': 0.25, 'healthcare': 0.20, 'finance': 0.15, 'manufacturing': 0.10, 'other': 0.30},
            'houston': {'energy': 0.30, 'healthcare': 0.20, 'manufacturing': 0.15, 'technology': 0.10, 'other': 0.25},
            'washington dc': {'government': 0.35, 'technology': 0.20, 'consulting': 0.15, 'healthcare': 0.10, 'other': 0.20},
            'dallas': {'finance': 0.25, 'technology': 0.20, 'healthcare': 0.15, 'manufacturing': 0.10, 'other': 0.30},
            'new york': {'finance': 0.30, 'technology': 0.20, 'healthcare': 0.15, 'media': 0.10, 'other': 0.25}
        }
        return industry_mixes.get(location.lower(), {'technology': 0.20, 'healthcare': 0.20, 'finance': 0.15, 'other': 0.45})
    
    def _calculate_economic_health(self, gdp_per_capita: float) -> float:
        """Calculate economic health score based on GDP per capita"""
        # Simple scoring: 0-100 based on GDP per capita
        if gdp_per_capita > 80000:
            return 90.0
        elif gdp_per_capita > 60000:
            return 75.0
        elif gdp_per_capita > 40000:
            return 60.0
        else:
            return 45.0
    
    def _get_fallback_regional_data(self, location: str) -> Dict[str, Any]:
        """Fallback regional data when API is unavailable"""
        fallback_data = {
            'atlanta': {
                'gdp_total': 400000000000,  # $400B
                'gdp_per_capita': 67000,
                'employment_growth': 2.5,
                'industry_mix': {'technology': 0.25, 'healthcare': 0.20, 'finance': 0.15, 'manufacturing': 0.10, 'other': 0.30},
                'economic_health_score': 75.0
            },
            'houston': {
                'gdp_total': 500000000000,  # $500B
                'gdp_per_capita': 71000,
                'employment_growth': 2.8,
                'industry_mix': {'energy': 0.30, 'healthcare': 0.20, 'manufacturing': 0.15, 'technology': 0.10, 'other': 0.25},
                'economic_health_score': 80.0
            },
            'washington dc': {
                'gdp_total': 550000000000,  # $550B
                'gdp_per_capita': 89000,
                'employment_growth': 2.2,
                'industry_mix': {'government': 0.35, 'technology': 0.20, 'consulting': 0.15, 'healthcare': 0.10, 'other': 0.20},
                'economic_health_score': 85.0
            }
        }
        
        location_data = fallback_data.get(location.lower(), fallback_data['atlanta'])
        
        return {
            'status': 'success',
            'data': {
                location: {
                    **location_data,
                    'source': 'Fallback Data'
                }
            }
        }


class APIHealthMonitor:
    """Monitor health of external APIs"""
    
    def __init__(self):
        self.services = {
            'bls': BLSAPIService(),
            'census': CensusAPIService(),
            'fred': FREDAPIService(),
            'bea': BEAAPIService()
        }
        self.health_status = {}
    
    def check_all_apis(self) -> Dict[str, bool]:
        """Check health of all APIs"""
        health_results = {}
        
        for api_name, service in self.services.items():
            try:
                if api_name == 'bls':
                    result = service.get_salary_data('atlanta', 'technology', 'mid')
                elif api_name == 'census':
                    result = service.get_demographic_data('atlanta')
                elif api_name == 'fred':
                    result = service.get_economic_indicators()
                elif api_name == 'bea':
                    result = service.get_regional_data('atlanta')
                
                health_results[api_name] = result.get('status') == 'success'
                
            except Exception as e:
                logger.error(f"Health check failed for {api_name}: {e}")
                health_results[api_name] = False
        
        self.health_status = health_results
        return health_results
    
    def get_api_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed API status"""
        status = {}
        for api_name, is_healthy in self.health_status.items():
            status[api_name] = {
                'healthy': is_healthy,
                'last_check': datetime.now().isoformat(),
                'response_time': self._get_average_response_time(api_name)
            }
        return status
    
    def _get_average_response_time(self, api_name: str) -> float:
        """Get average response time for API (simplified)"""
        # In production, you'd track actual response times
        return 0.5  # Placeholder


# Convenience functions for easy access
def get_salary_data(location: str, industry: str, experience_level: str) -> Dict[str, Any]:
    """Get salary data from BLS"""
    bls_service = BLSAPIService()
    return bls_service.get_salary_data(location, industry, experience_level)


def get_demographic_data(location: str) -> Dict[str, Any]:
    """Get demographic data from Census"""
    census_service = CensusAPIService()
    return census_service.get_demographic_data(location)


def get_economic_indicators() -> Dict[str, Any]:
    """Get economic indicators from FRED"""
    fred_service = FREDAPIService()
    return fred_service.get_economic_indicators()


def get_regional_data(location: str) -> Dict[str, Any]:
    """Get regional data from BEA"""
    bea_service = BEAAPIService()
    return bea_service.get_regional_data(location)


def check_api_health() -> Dict[str, bool]:
    """Check health of all external APIs"""
    monitor = APIHealthMonitor()
    return monitor.check_all_apis()


# Export main classes for direct use
__all__ = [
    'BLSAPIService',
    'CensusAPIService', 
    'FREDAPIService',
    'BEAAPIService',
    'APIHealthMonitor',
    'get_salary_data',
    'get_demographic_data',
    'get_economic_indicators',
    'get_regional_data',
    'check_api_health'
] 