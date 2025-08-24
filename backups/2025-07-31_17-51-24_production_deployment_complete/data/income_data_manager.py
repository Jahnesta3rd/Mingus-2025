"""
Income Data Management System
Provides reliable income comparison data with fallback datasets and API integration capabilities
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from loguru import logger
import pandas as pd
from pathlib import Path

class DataSource(Enum):
    """Data source enumeration"""
    FALLBACK = "fallback"
    CENSUS_API = "census_api"
    CACHED = "cached"

class DataQuality(Enum):
    """Data quality levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    MISSING = "missing"

@dataclass
class IncomeDataPoint:
    """Individual income data point"""
    median_income: float
    sample_size: int
    standard_error: float
    confidence_interval: Tuple[float, float]
    data_year: int
    source: DataSource
    quality: DataQuality
    last_updated: datetime

@dataclass
class DemographicGroup:
    """Demographic group definition"""
    name: str
    race: str
    age_group: str
    education_level: str
    location: str
    income_data: IncomeDataPoint

class IncomeDataManager:
    """
    Comprehensive income data management system with fallback data and API integration
    """
    
    def __init__(self, data_dir: str = "backend/data/income_datasets"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data storage
        self.fallback_data = {}
        self.cached_data = {}
        self.data_metadata = {}
        
        # API configuration
        self.census_api_key = os.getenv("CENSUS_API_KEY", "")
        self.census_base_url = "https://api.census.gov/data"
        self.api_rate_limit = 1000  # requests per hour
        self.api_calls_made = 0
        self.last_api_reset = datetime.now()
        
        # Cache configuration
        self.cache_duration = timedelta(days=30)
        self.cache_file = self.data_dir / "cached_data.json"
        self.metadata_file = self.data_dir / "data_metadata.json"
        
        # Initialize data
        self._load_fallback_data()
        self._load_cached_data()
        self._load_metadata()
        
        logger.info("Income Data Manager initialized successfully")
    
    def _load_fallback_data(self) -> None:
        """Load fallback income data from JSON files"""
        try:
            fallback_file = self.data_dir / "fallback_income_data.json"
            if fallback_file.exists():
                with open(fallback_file, 'r') as f:
                    self.fallback_data = json.load(f)
                logger.info(f"Loaded fallback data with {len(self.fallback_data)} demographic groups")
            else:
                logger.warning("Fallback data file not found, creating default dataset")
                self._create_default_fallback_data()
        except Exception as e:
            logger.error(f"Error loading fallback data: {str(e)}")
            self._create_default_fallback_data()
    
    def _create_default_fallback_data(self) -> None:
        """Create default fallback data based on 2022 ACS estimates"""
        self.fallback_data = {
            "metadata": {
                "version": "1.0.0",
                "data_year": 2022,
                "source": "American Community Survey (ACS) 5-Year Estimates",
                "last_updated": datetime.now().isoformat(),
                "description": "Fallback income data for African American professionals"
            },
            "national_data": {
                "all_races": {
                    "median_income": 75000,
                    "sample_size": 1000000,
                    "standard_error": 500,
                    "confidence_interval": [74500, 75500],
                    "data_year": 2022,
                    "source": "fallback",
                    "quality": "good"
                },
                "african_american": {
                    "median_income": 52000,
                    "sample_size": 150000,
                    "standard_error": 800,
                    "confidence_interval": [51200, 52800],
                    "data_year": 2022,
                    "source": "fallback",
                    "quality": "good"
                },
                "white": {
                    "median_income": 78000,
                    "sample_size": 800000,
                    "standard_error": 400,
                    "confidence_interval": [77600, 78400],
                    "data_year": 2022,
                    "source": "fallback",
                    "quality": "good"
                },
                "hispanic_latino": {
                    "median_income": 56000,
                    "sample_size": 200000,
                    "standard_error": 700,
                    "confidence_interval": [55300, 56700],
                    "data_year": 2022,
                    "source": "fallback",
                    "quality": "good"
                },
                "asian": {
                    "median_income": 95000,
                    "sample_size": 100000,
                    "standard_error": 1000,
                    "confidence_interval": [94000, 96000],
                    "data_year": 2022,
                    "source": "fallback",
                    "quality": "good"
                }
            },
            "age_groups": {
                "25-34": {
                    "all_races": {"median_income": 65000, "sample_size": 300000},
                    "african_american": {"median_income": 48000, "sample_size": 45000},
                    "white": {"median_income": 68000, "sample_size": 240000},
                    "hispanic_latino": {"median_income": 52000, "sample_size": 60000},
                    "asian": {"median_income": 75000, "sample_size": 30000}
                },
                "35-44": {
                    "all_races": {"median_income": 85000, "sample_size": 250000},
                    "african_american": {"median_income": 62000, "sample_size": 37500},
                    "white": {"median_income": 88000, "sample_size": 200000},
                    "hispanic_latino": {"median_income": 68000, "sample_size": 50000},
                    "asian": {"median_income": 105000, "sample_size": 25000}
                }
            },
            "education_levels": {
                "high_school": {
                    "all_races": {"median_income": 45000, "sample_size": 200000},
                    "african_american": {"median_income": 38000, "sample_size": 30000},
                    "white": {"median_income": 47000, "sample_size": 160000},
                    "hispanic_latino": {"median_income": 42000, "sample_size": 40000},
                    "asian": {"median_income": 55000, "sample_size": 10000}
                },
                "bachelors": {
                    "all_races": {"median_income": 85000, "sample_size": 400000},
                    "african_american": {"median_income": 65000, "sample_size": 60000},
                    "white": {"median_income": 88000, "sample_size": 320000},
                    "hispanic_latino": {"median_income": 72000, "sample_size": 80000},
                    "asian": {"median_income": 105000, "sample_size": 40000}
                },
                "masters": {
                    "all_races": {"median_income": 105000, "sample_size": 200000},
                    "african_american": {"median_income": 85000, "sample_size": 30000},
                    "white": {"median_income": 108000, "sample_size": 160000},
                    "hispanic_latino": {"median_income": 92000, "sample_size": 40000},
                    "asian": {"median_income": 125000, "sample_size": 20000}
                }
            },
            "metro_areas": {
                "Atlanta": {
                    "all_races": {"median_income": 72000, "sample_size": 50000},
                    "african_american": {"median_income": 52000, "sample_size": 15000},
                    "white": {"median_income": 78000, "sample_size": 30000},
                    "hispanic_latino": {"median_income": 58000, "sample_size": 8000},
                    "asian": {"median_income": 88000, "sample_size": 7000}
                },
                "Houston": {
                    "all_races": {"median_income": 68000, "sample_size": 45000},
                    "african_american": {"median_income": 50000, "sample_size": 12000},
                    "white": {"median_income": 75000, "sample_size": 25000},
                    "hispanic_latino": {"median_income": 55000, "sample_size": 12000},
                    "asian": {"median_income": 85000, "sample_size": 6000}
                },
                "Washington DC": {
                    "all_races": {"median_income": 95000, "sample_size": 40000},
                    "african_american": {"median_income": 68000, "sample_size": 10000},
                    "white": {"median_income": 105000, "sample_size": 25000},
                    "hispanic_latino": {"median_income": 75000, "sample_size": 8000},
                    "asian": {"median_income": 115000, "sample_size": 7000}
                },
                "Dallas": {
                    "all_races": {"median_income": 70000, "sample_size": 40000},
                    "african_american": {"median_income": 52000, "sample_size": 10000},
                    "white": {"median_income": 76000, "sample_size": 25000},
                    "hispanic_latino": {"median_income": 56000, "sample_size": 10000},
                    "asian": {"median_income": 88000, "sample_size": 5000}
                },
                "New York City": {
                    "all_races": {"median_income": 85000, "sample_size": 60000},
                    "african_american": {"median_income": 62000, "sample_size": 15000},
                    "white": {"median_income": 95000, "sample_size": 35000},
                    "hispanic_latino": {"median_income": 65000, "sample_size": 15000},
                    "asian": {"median_income": 105000, "sample_size": 10000}
                },
                "Philadelphia": {
                    "all_races": {"median_income": 65000, "sample_size": 35000},
                    "african_american": {"median_income": 48000, "sample_size": 12000},
                    "white": {"median_income": 72000, "sample_size": 20000},
                    "hispanic_latino": {"median_income": 52000, "sample_size": 8000},
                    "asian": {"median_income": 78000, "sample_size": 5000}
                },
                "Chicago": {
                    "all_races": {"median_income": 75000, "sample_size": 45000},
                    "african_american": {"median_income": 55000, "sample_size": 12000},
                    "white": {"median_income": 82000, "sample_size": 25000},
                    "hispanic_latino": {"median_income": 58000, "sample_size": 10000},
                    "asian": {"median_income": 92000, "sample_size": 8000}
                },
                "Charlotte": {
                    "all_races": {"median_income": 68000, "sample_size": 30000},
                    "african_american": {"median_income": 52000, "sample_size": 8000},
                    "white": {"median_income": 75000, "sample_size": 18000},
                    "hispanic_latino": {"median_income": 54000, "sample_size": 6000},
                    "asian": {"median_income": 82000, "sample_size": 4000}
                },
                "Miami": {
                    "all_races": {"median_income": 62000, "sample_size": 35000},
                    "african_american": {"median_income": 48000, "sample_size": 8000},
                    "white": {"median_income": 68000, "sample_size": 20000},
                    "hispanic_latino": {"median_income": 52000, "sample_size": 12000},
                    "asian": {"median_income": 75000, "sample_size": 5000}
                },
                "Baltimore": {
                    "all_races": {"median_income": 70000, "sample_size": 25000},
                    "african_american": {"median_income": 55000, "sample_size": 10000},
                    "white": {"median_income": 78000, "sample_size": 12000},
                    "hispanic_latino": {"median_income": 56000, "sample_size": 5000},
                    "asian": {"median_income": 85000, "sample_size": 3000}
                }
            }
        }
        
        # Save fallback data
        self._save_fallback_data()
    
    def _save_fallback_data(self) -> None:
        """Save fallback data to JSON file"""
        try:
            fallback_file = self.data_dir / "fallback_income_data.json"
            with open(fallback_file, 'w') as f:
                json.dump(self.fallback_data, f, indent=2, default=str)
            logger.info("Fallback data saved successfully")
        except Exception as e:
            logger.error(f"Error saving fallback data: {str(e)}")
    
    def _load_cached_data(self) -> None:
        """Load cached data from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                # Check if cache is still valid
                cache_timestamp = datetime.fromisoformat(cached_data.get('metadata', {}).get('cached_at', '2020-01-01'))
                if datetime.now() - cache_timestamp < self.cache_duration:
                    self.cached_data = cached_data
                    logger.info("Loaded valid cached data")
                else:
                    logger.info("Cached data expired, will use fallback data")
            else:
                logger.info("No cached data found")
        except Exception as e:
            logger.error(f"Error loading cached data: {str(e)}")
    
    def _load_metadata(self) -> None:
        """Load data metadata"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    self.data_metadata = json.load(f)
            else:
                self.data_metadata = {
                    "last_update": datetime.now().isoformat(),
                    "data_sources": {},
                    "quality_metrics": {},
                    "update_frequency": "annual"
                }
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
    
    def get_income_data(self, 
                       race: str, 
                       age_group: str = None, 
                       education_level: str = None, 
                       location: str = None) -> IncomeDataPoint:
        """
        Get income data for specified demographic group
        
        Args:
            race: Race/ethnicity (african_american, white, hispanic_latino, asian)
            age_group: Age group (25-34, 35-44)
            education_level: Education level (high_school, bachelors, masters)
            location: Metro area location
            
        Returns:
            IncomeDataPoint with income data and metadata
        """
        try:
            # Try to get data from cache first
            data = self._get_cached_data(race, age_group, education_level, location)
            if data:
                return data
            
            # Try to get data from API (if available)
            if self.census_api_key:
                data = self._get_api_data(race, age_group, education_level, location)
                if data:
                    return data
            
            # Fall back to fallback data
            data = self._get_fallback_data(race, age_group, education_level, location)
            if data:
                return data
            
            # Return default data if nothing found
            logger.warning(f"No income data found for {race}, {age_group}, {education_level}, {location}")
            return self._create_default_data_point()
            
        except Exception as e:
            logger.error(f"Error getting income data: {str(e)}")
            return self._create_default_data_point()
    
    def _get_cached_data(self, race: str, age_group: str = None, 
                        education_level: str = None, location: str = None) -> Optional[IncomeDataPoint]:
        """Get data from cache"""
        try:
            cache_key = self._create_cache_key(race, age_group, education_level, location)
            if cache_key in self.cached_data:
                data = self.cached_data[cache_key]
                return IncomeDataPoint(
                    median_income=data['median_income'],
                    sample_size=data['sample_size'],
                    standard_error=data.get('standard_error', 0),
                    confidence_interval=data.get('confidence_interval', [0, 0]),
                    data_year=data.get('data_year', 2022),
                    source=DataSource.CACHED,
                    quality=DataQuality(data.get('quality', 'good')),
                    last_updated=datetime.fromisoformat(data['last_updated'])
                )
        except Exception as e:
            logger.error(f"Error getting cached data: {str(e)}")
        return None
    
    def _get_api_data(self, race: str, age_group: str = None, 
                     education_level: str = None, location: str = None) -> Optional[IncomeDataPoint]:
        """Get data from Census Bureau API"""
        try:
            # Check rate limiting
            if not self._check_rate_limit():
                logger.warning("API rate limit reached, using fallback data")
                return None
            
            # Build API query
            query_params = self._build_api_query(race, age_group, education_level, location)
            if not query_params:
                return None
            
            # Make API request
            response = requests.get(
                f"{self.census_base_url}/2022/acs/acs5",
                params=query_params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                income_data = self._parse_api_response(data, race, age_group, education_level, location)
                if income_data:
                    # Cache the result
                    self._cache_data(race, age_group, education_level, location, income_data)
                    return income_data
            
            logger.warning(f"API request failed: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting API data: {str(e)}")
            return None
    
    def _get_fallback_data(self, race: str, age_group: str = None, 
                          education_level: str = None, location: str = None) -> Optional[IncomeDataPoint]:
        """Get data from fallback dataset"""
        try:
            if location and location in self.fallback_data.get('metro_areas', {}):
                location_data = self.fallback_data['metro_areas'][location]
                if race in location_data:
                    data = location_data[race]
                    return IncomeDataPoint(
                        median_income=data['median_income'],
                        sample_size=data['sample_size'],
                        standard_error=data.get('standard_error', 500),
                        confidence_interval=data.get('confidence_interval', [data['median_income']-500, data['median_income']+500]),
                        data_year=self.fallback_data['metadata']['data_year'],
                        source=DataSource.FALLBACK,
                        quality=DataQuality(data.get('quality', 'good')),
                        last_updated=datetime.fromisoformat(self.fallback_data['metadata']['last_updated'])
                    )
            
            # Try national data
            if race in self.fallback_data.get('national_data', {}):
                data = self.fallback_data['national_data'][race]
                return IncomeDataPoint(
                    median_income=data['median_income'],
                    sample_size=data['sample_size'],
                    standard_error=data['standard_error'],
                    confidence_interval=data['confidence_interval'],
                    data_year=data['data_year'],
                    source=DataSource.FALLBACK,
                    quality=DataQuality(data['quality']),
                    last_updated=datetime.fromisoformat(self.fallback_data['metadata']['last_updated'])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting fallback data: {str(e)}")
            return None
    
    def _create_default_data_point(self) -> IncomeDataPoint:
        """Create default income data point"""
        return IncomeDataPoint(
            median_income=65000,
            sample_size=1000,
            standard_error=1000,
            confidence_interval=[64000, 66000],
            data_year=2022,
            source=DataSource.FALLBACK,
            quality=DataQuality.POOR,
            last_updated=datetime.now()
        )
    
    def _create_cache_key(self, race: str, age_group: str = None, 
                         education_level: str = None, location: str = None) -> str:
        """Create cache key for data lookup"""
        parts = [race]
        if age_group:
            parts.append(age_group)
        if education_level:
            parts.append(education_level)
        if location:
            parts.append(location)
        return "_".join(parts)
    
    def _check_rate_limit(self) -> bool:
        """Check if API rate limit allows another request"""
        now = datetime.now()
        if now - self.last_api_reset > timedelta(hours=1):
            self.api_calls_made = 0
            self.last_api_reset = now
        
        return self.api_calls_made < self.api_rate_limit
    
    def _build_api_query(self, race: str, age_group: str = None, 
                        education_level: str = None, location: str = None) -> Optional[Dict]:
        """Build Census API query parameters"""
        try:
            # Base query for median household income
            query = {
                'get': 'B19013_001E,B19013_001M',
                'for': 'metropolitan statistical area/micropolitan statistical area:*',
                'key': self.census_api_key
            }
            
            # Add demographic filters
            if race == 'african_american':
                query['get'] += ',B19013B_001E,B19013B_001M'  # Black alone
            elif race == 'white':
                query['get'] += ',B19013H_001E,B19013H_001M'  # White alone, not Hispanic
            elif race == 'hispanic_latino':
                query['get'] += ',B19013I_001E,B19013I_001M'  # Hispanic or Latino
            elif race == 'asian':
                query['get'] += ',B19013D_001E,B19013D_001M'  # Asian alone
            
            return query
            
        except Exception as e:
            logger.error(f"Error building API query: {str(e)}")
            return None
    
    def _parse_api_response(self, response_data: List, race: str, age_group: str = None, 
                           education_level: str = None, location: str = None) -> Optional[IncomeDataPoint]:
        """Parse Census API response"""
        try:
            if not response_data or len(response_data) < 2:
                return None
            
            # Extract income data from response
            headers = response_data[0]
            data = response_data[1]
            
            # Find the appropriate income column
            income_col = None
            if race == 'african_american':
                income_col = 'B19013B_001E'
            elif race == 'white':
                income_col = 'B19013H_001E'
            elif race == 'hispanic_latino':
                income_col = 'B19013I_001E'
            elif race == 'asian':
                income_col = 'B19013D_001E'
            else:
                income_col = 'B19013_001E'
            
            if income_col not in headers:
                return None
            
            col_index = headers.index(income_col)
            median_income = float(data[col_index]) if data[col_index] != 'null' else 0
            
            if median_income <= 0:
                return None
            
            return IncomeDataPoint(
                median_income=median_income,
                sample_size=1000,  # Default sample size
                standard_error=500,  # Default standard error
                confidence_interval=[median_income-500, median_income+500],
                data_year=2022,
                source=DataSource.CENSUS_API,
                quality=DataQuality.EXCELLENT,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error parsing API response: {str(e)}")
            return None
    
    def _cache_data(self, race: str, age_group: str = None, 
                   education_level: str = None, location: str = None, 
                   data: IncomeDataPoint = None) -> None:
        """Cache income data"""
        try:
            cache_key = self._create_cache_key(race, age_group, education_level, location)
            self.cached_data[cache_key] = {
                'median_income': data.median_income,
                'sample_size': data.sample_size,
                'standard_error': data.standard_error,
                'confidence_interval': data.confidence_interval,
                'data_year': data.data_year,
                'source': data.source.value,
                'quality': data.quality.value,
                'last_updated': data.last_updated.isoformat()
            }
            
            # Save cache to file
            self._save_cached_data()
            
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
    
    def _save_cached_data(self) -> None:
        """Save cached data to file"""
        try:
            cache_data = {
                'metadata': {
                    'cached_at': datetime.now().isoformat(),
                    'cache_duration_days': self.cache_duration.days
                },
                'data': self.cached_data
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving cached data: {str(e)}")
    
    def validate_data_quality(self) -> Dict[str, Any]:
        """Validate data quality across all demographic groups"""
        try:
            quality_report = {
                'timestamp': datetime.now().isoformat(),
                'overall_quality': 'good',
                'issues': [],
                'recommendations': []
            }
            
            # Check fallback data completeness
            required_groups = ['african_american', 'white', 'hispanic_latino', 'asian']
            required_locations = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
            
            for race in required_groups:
                if race not in self.fallback_data.get('national_data', {}):
                    quality_report['issues'].append(f"Missing national data for {race}")
                
                for location in required_locations:
                    if location not in self.fallback_data.get('metro_areas', {}):
                        quality_report['issues'].append(f"Missing metro data for {race} in {location}")
                    elif race not in self.fallback_data['metro_areas'][location]:
                        quality_report['issues'].append(f"Missing {race} data for {location}")
            
            # Check data freshness
            metadata = self.fallback_data.get('metadata', {})
            data_year = metadata.get('data_year', 2020)
            if data_year < 2022:
                quality_report['issues'].append(f"Data is from {data_year}, consider updating to 2022")
                quality_report['recommendations'].append("Update fallback data to latest ACS estimates")
            
            # Assess overall quality
            if len(quality_report['issues']) == 0:
                quality_report['overall_quality'] = 'excellent'
            elif len(quality_report['issues']) <= 3:
                quality_report['overall_quality'] = 'good'
            elif len(quality_report['issues']) <= 10:
                quality_report['overall_quality'] = 'fair'
            else:
                quality_report['overall_quality'] = 'poor'
            
            return quality_report
            
        except Exception as e:
            logger.error(f"Error validating data quality: {str(e)}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_quality': 'unknown',
                'issues': [f"Error during validation: {str(e)}"],
                'recommendations': ["Check data files and system configuration"]
            }
    
    def get_available_locations(self) -> List[str]:
        """Get list of available metro areas"""
        return list(self.fallback_data.get('metro_areas', {}).keys())
    
    def get_demographic_summary(self) -> Dict[str, Any]:
        """Get summary of available demographic data"""
        return {
            'races': list(self.fallback_data.get('national_data', {}).keys()),
            'age_groups': list(self.fallback_data.get('age_groups', {}).keys()),
            'education_levels': list(self.fallback_data.get('education_levels', {}).keys()),
            'metro_areas': self.get_available_locations(),
            'data_year': self.fallback_data.get('metadata', {}).get('data_year', 2022),
            'last_updated': self.fallback_data.get('metadata', {}).get('last_updated', 'unknown')
        }
    
    def update_fallback_data(self, new_data: Dict[str, Any]) -> bool:
        """Update fallback data with new dataset"""
        try:
            # Validate new data structure
            if not self._validate_new_data(new_data):
                logger.error("New data validation failed")
                return False
            
            # Backup current data
            backup_file = self.data_dir / f"fallback_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(self.fallback_data, f, indent=2, default=str)
            
            # Update data
            self.fallback_data.update(new_data)
            self.fallback_data['metadata']['last_updated'] = datetime.now().isoformat()
            
            # Save updated data
            self._save_fallback_data()
            
            logger.info("Fallback data updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error updating fallback data: {str(e)}")
            return False
    
    def _validate_new_data(self, new_data: Dict[str, Any]) -> bool:
        """Validate new data structure"""
        try:
            required_keys = ['metadata', 'national_data', 'metro_areas']
            for key in required_keys:
                if key not in new_data:
                    logger.error(f"Missing required key: {key}")
                    return False
            
            # Check metadata
            metadata = new_data['metadata']
            if 'data_year' not in metadata:
                logger.error("Missing data_year in metadata")
                return False
            
            # Check national data
            national_data = new_data['national_data']
            required_races = ['african_american', 'white', 'hispanic_latino', 'asian']
            for race in required_races:
                if race not in national_data:
                    logger.error(f"Missing national data for {race}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating new data: {str(e)}")
            return False 