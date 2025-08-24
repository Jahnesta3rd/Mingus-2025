"""
Enhanced Salary Data Service with Redis Integration
Integrates with existing MINGUS Redis caching system and new PostgreSQL schema
"""

import asyncio
import logging
import json
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal
import redis
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text

# MINGUS imports
from ..database import get_db_session
from ..models.salary_data import (
    SalaryBenchmark, MarketData, ConfidenceScore, SalaryDataCache
)
from .cache_service import CacheService
from .api_client import AsyncAPIClient, APISource, APIResponse
from .data_validation import DataValidator, ValidationResult, ValidationLevel

logger = logging.getLogger(__name__)

class DataSource(str, Enum):
    """Data source types"""
    BLS = "bls"
    CENSUS = "census"
    FRED = "fred"
    INDEED = "indeed"
    FALLBACK = "fallback"
    CACHED = "cached"

class CacheStrategy(str, Enum):
    """Cache strategy types"""
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"

@dataclass
class SalaryDataRequest:
    """Request for salary data"""
    location: str
    occupation: Optional[str] = None
    industry: Optional[str] = None
    experience_level: Optional[str] = None
    education_level: Optional[str] = None
    year: Optional[int] = None
    quarter: Optional[int] = None
    include_market_data: bool = True
    include_confidence_scores: bool = True
    force_refresh: bool = False
    cache_strategy: CacheStrategy = CacheStrategy.STANDARD

@dataclass
class SalaryDataResponse:
    """Response with comprehensive salary data"""
    request: SalaryDataRequest
    salary_benchmarks: List[Dict[str, Any]]
    market_data: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, Any]] = None
    cache_info: Dict[str, Any] = None
    data_freshness: Dict[str, Any] = None
    recommendations: List[str] = None
    processing_time_ms: float = 0.0
    cache_hit: bool = False

class EnhancedSalaryDataService:
    """Enhanced salary data service with Redis integration"""
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize the enhanced salary data service"""
        self.db_session = db_session or get_db_session()
        
        # Initialize Redis cache service
        self.cache_service = CacheService()
        
        # Initialize API client
        self.api_client = AsyncAPIClient()
        
        # Initialize data validator
        self.validator = DataValidator()
        
        # Cache configuration
        self.cache_config = {
            CacheStrategy.STANDARD: {
                'salary_ttl': 86400,      # 24 hours
                'market_ttl': 604800,     # 7 days
                'confidence_ttl': 3600,   # 1 hour
                'compression': True
            },
            CacheStrategy.AGGRESSIVE: {
                'salary_ttl': 604800,     # 7 days
                'market_ttl': 2592000,    # 30 days
                'confidence_ttl': 86400,  # 24 hours
                'compression': True
            },
            CacheStrategy.CONSERVATIVE: {
                'salary_ttl': 3600,       # 1 hour
                'market_ttl': 86400,      # 24 hours
                'confidence_ttl': 1800,   # 30 minutes
                'compression': False
            }
        }
        
        # API rate limiting
        self.rate_limits = {
            DataSource.BLS: {'requests_per_minute': 10, 'requests_per_hour': 500},
            DataSource.CENSUS: {'requests_per_minute': 20, 'requests_per_hour': 1000},
            DataSource.FRED: {'requests_per_minute': 30, 'requests_per_hour': 1500},
            DataSource.INDEED: {'requests_per_minute': 5, 'requests_per_hour': 200}
        }
        
        logger.info("Enhanced Salary Data Service initialized")
    
    async def get_salary_data(self, request: SalaryDataRequest) -> SalaryDataResponse:
        """
        Get comprehensive salary data with caching and validation
        
        Args:
            request: Salary data request parameters
            
        Returns:
            Comprehensive salary data response
        """
        start_time = datetime.now()
        
        try:
            # Generate cache keys
            cache_keys = self._generate_cache_keys(request)
            
            # Check cache first (unless force refresh)
            if not request.force_refresh:
                cached_data = await self._get_cached_data(cache_keys)
                if cached_data:
                    processing_time = (datetime.now() - start_time).total_seconds() * 1000
                    return SalaryDataResponse(
                        request=request,
                        salary_benchmarks=cached_data['salary_benchmarks'],
                        market_data=cached_data.get('market_data'),
                        confidence_scores=cached_data.get('confidence_scores'),
                        cache_info=cached_data.get('cache_info'),
                        data_freshness=cached_data.get('data_freshness'),
                        recommendations=cached_data.get('recommendations'),
                        processing_time_ms=processing_time,
                        cache_hit=True
                    )
            
            # Fetch fresh data from APIs and database
            salary_data = await self._fetch_salary_data(request)
            market_data = await self._fetch_market_data(request) if request.include_market_data else None
            confidence_scores = await self._calculate_confidence_scores(request) if request.include_confidence_scores else None
            
            # Store in cache
            await self._cache_data(cache_keys, {
                'salary_benchmarks': salary_data,
                'market_data': market_data,
                'confidence_scores': confidence_scores,
                'cache_info': self._get_cache_info(cache_keys),
                'data_freshness': self._get_data_freshness(salary_data, market_data),
                'recommendations': self._generate_recommendations(salary_data, market_data)
            }, request.cache_strategy)
            
            # Update cache tracking in database
            self._update_cache_tracking(cache_keys, request.cache_strategy)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SalaryDataResponse(
                request=request,
                salary_benchmarks=salary_data,
                market_data=market_data,
                confidence_scores=confidence_scores,
                cache_info=self._get_cache_info(cache_keys),
                data_freshness=self._get_data_freshness(salary_data, market_data),
                recommendations=self._generate_recommendations(salary_data, market_data),
                processing_time_ms=processing_time,
                cache_hit=False
            )
            
        except Exception as e:
            logger.error(f"Error getting salary data: {e}")
            # Return fallback data
            return await self._get_fallback_data(request, start_time)
    
    def _generate_cache_keys(self, request: SalaryDataRequest) -> Dict[str, str]:
        """Generate cache keys for different data types"""
        base_key = f"salary_data:{request.location.lower().replace(' ', '_')}"
        
        keys = {
            'salary': f"{base_key}:salary:{request.occupation or 'all'}:{request.industry or 'all'}:{request.year or 'latest'}",
            'market': f"{base_key}:market:{request.occupation or 'all'}:{request.industry or 'all'}:{request.year or 'latest'}",
            'confidence': f"{base_key}:confidence:{request.occupation or 'all'}:{request.industry or 'all'}:{request.year or 'latest'}"
        }
        
        return keys
    
    async def _get_cached_data(self, cache_keys: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache"""
        try:
            cached_data = {}
            
            # Try to get salary data from cache
            salary_cache = await self.cache_service.get(cache_keys['salary'])
            if salary_cache:
                cached_data['salary_benchmarks'] = salary_cache.get('salary_benchmarks', [])
                cached_data['cache_info'] = salary_cache.get('cache_info', {})
                cached_data['data_freshness'] = salary_cache.get('data_freshness', {})
                cached_data['recommendations'] = salary_cache.get('recommendations', [])
                
                # Update cache hit tracking
                self._increment_cache_hit(cache_keys['salary'])
                
                # Try to get market data from cache
                market_cache = await self.cache_service.get(cache_keys['market'])
                if market_cache:
                    cached_data['market_data'] = market_cache.get('market_data')
                    self._increment_cache_hit(cache_keys['market'])
                
                # Try to get confidence scores from cache
                confidence_cache = await self.cache_service.get(cache_keys['confidence'])
                if confidence_cache:
                    cached_data['confidence_scores'] = confidence_cache.get('confidence_scores')
                    self._increment_cache_hit(cache_keys['confidence'])
                
                return cached_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None
    
    async def _fetch_salary_data(self, request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Fetch salary data from APIs and database"""
        try:
            # First, try to get from database
            db_data = self._get_salary_data_from_db(request)
            
            # If we have recent data, return it
            if db_data and self._is_data_fresh(db_data):
                return db_data
            
            # Fetch from APIs
            api_data = await self._fetch_salary_data_from_apis(request)
            
            # Combine and validate data
            combined_data = self._combine_salary_data(db_data, api_data)
            
            # Store in database
            self._store_salary_data_in_db(combined_data, request)
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error fetching salary data: {e}")
            return self._get_fallback_salary_data(request)
    
    def _get_salary_data_from_db(self, request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Get salary data from database"""
        try:
            query = self.db_session.query(SalaryBenchmark)
            
            # Apply filters
            query = query.filter(SalaryBenchmark.location == request.location)
            
            if request.occupation:
                query = query.filter(SalaryBenchmark.occupation == request.occupation)
            
            if request.industry:
                query = query.filter(SalaryBenchmark.industry == request.industry)
            
            if request.experience_level:
                query = query.filter(SalaryBenchmark.experience_level == request.experience_level)
            
            if request.education_level:
                query = query.filter(SalaryBenchmark.education_level == request.education_level)
            
            if request.year:
                query = query.filter(SalaryBenchmark.year == request.year)
            
            if request.quarter:
                query = query.filter(SalaryBenchmark.quarter == request.quarter)
            
            # Order by most recent and highest confidence
            query = query.order_by(
                desc(SalaryBenchmark.last_updated),
                desc(SalaryBenchmark.source_confidence_score)
            )
            
            results = query.limit(10).all()
            return [result.to_dict() for result in results]
            
        except Exception as e:
            logger.error(f"Error getting salary data from database: {e}")
            return []
    
    async def _fetch_salary_data_from_apis(self, request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Fetch salary data from external APIs"""
        api_data = []
        
        # Fetch from BLS API
        try:
            bls_data = await self._fetch_bls_data(request)
            if bls_data:
                api_data.extend(bls_data)
        except Exception as e:
            logger.error(f"Error fetching BLS data: {e}")
        
        # Fetch from Census API
        try:
            census_data = await self._fetch_census_data(request)
            if census_data:
                api_data.extend(census_data)
        except Exception as e:
            logger.error(f"Error fetching Census data: {e}")
        
        # Fetch from Indeed API
        try:
            indeed_data = await self._fetch_indeed_data(request)
            if indeed_data:
                api_data.extend(indeed_data)
        except Exception as e:
            logger.error(f"Error fetching Indeed data: {e}")
        
        return api_data
    
    async def _fetch_bls_data(self, request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Fetch data from Bureau of Labor Statistics API"""
        try:
            # Check rate limits
            if not self._check_rate_limit(DataSource.BLS):
                logger.warning("BLS API rate limit exceeded")
                return []
            
            # Make API request
            response = await self.api_client.fetch_data(
                source=APISource.BLS,
                endpoint="wages",
                params={
                    'location': request.location,
                    'occupation': request.occupation,
                    'year': request.year or datetime.now().year
                }
            )
            
            if response and response.status_code == 200:
                return self._parse_bls_response(response.data, request)
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching BLS data: {e}")
            return []
    
    async def _fetch_census_data(self, request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Fetch data from Census Bureau API"""
        try:
            # Check rate limits
            if not self._check_rate_limit(DataSource.CENSUS):
                logger.warning("Census API rate limit exceeded")
                return []
            
            # Make API request
            response = await self.api_client.fetch_data(
                source=APISource.CENSUS,
                endpoint="acs",
                params={
                    'location': request.location,
                    'year': request.year or datetime.now().year
                }
            )
            
            if response and response.status_code == 200:
                return self._parse_census_response(response.data, request)
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching Census data: {e}")
            return []
    
    async def _fetch_indeed_data(self, request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Fetch data from Indeed API"""
        try:
            # Check rate limits
            if not self._check_rate_limit(DataSource.INDEED):
                logger.warning("Indeed API rate limit exceeded")
                return []
            
            # Make API request
            response = await self.api_client.fetch_data(
                source=APISource.INDEED,
                endpoint="salaries",
                params={
                    'location': request.location,
                    'job_title': request.occupation,
                    'limit': 50
                }
            )
            
            if response and response.status_code == 200:
                return self._parse_indeed_response(response.data, request)
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching Indeed data: {e}")
            return []
    
    def _parse_bls_response(self, data: Dict[str, Any], request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Parse BLS API response"""
        parsed_data = []
        
        try:
            if 'data' in data:
                for item in data['data']:
                    parsed_item = {
                        'location': request.location,
                        'occupation': item.get('occupation', request.occupation),
                        'industry': item.get('industry', request.industry),
                        'experience_level': item.get('experience_level', request.experience_level),
                        'education_level': item.get('education_level', request.education_level),
                        'median_salary': float(item.get('median_salary', 0)),
                        'mean_salary': float(item.get('mean_salary', 0)),
                        'percentile_25': float(item.get('percentile_25', 0)),
                        'percentile_75': float(item.get('percentile_75', 0)),
                        'percentile_90': float(item.get('percentile_90', 0)),
                        'sample_size': int(item.get('sample_size', 0)),
                        'data_source': DataSource.BLS.value,
                        'source_confidence_score': 0.9,  # BLS is highly reliable
                        'data_freshness_days': 0,  # Fresh from API
                        'year': request.year or datetime.now().year,
                        'quarter': request.quarter,
                        'metadata': {
                            'bls_series_id': item.get('series_id'),
                            'bls_area_code': item.get('area_code'),
                            'bls_occupation_code': item.get('occupation_code')
                        }
                    }
                    parsed_data.append(parsed_item)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing BLS response: {e}")
            return []
    
    def _parse_census_response(self, data: Dict[str, Any], request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Parse Census API response"""
        parsed_data = []
        
        try:
            if 'data' in data:
                for item in data['data']:
                    parsed_item = {
                        'location': request.location,
                        'occupation': item.get('occupation', request.occupation),
                        'industry': item.get('industry', request.industry),
                        'experience_level': item.get('experience_level', request.experience_level),
                        'education_level': item.get('education_level', request.education_level),
                        'median_salary': float(item.get('median_income', 0)),
                        'mean_salary': float(item.get('mean_income', 0)),
                        'sample_size': int(item.get('sample_size', 0)),
                        'data_source': DataSource.CENSUS.value,
                        'source_confidence_score': 0.8,  # Census is reliable
                        'data_freshness_days': 0,
                        'year': request.year or datetime.now().year,
                        'quarter': request.quarter,
                        'metadata': {
                            'census_table': item.get('table'),
                            'census_variable': item.get('variable')
                        }
                    }
                    parsed_data.append(parsed_item)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing Census response: {e}")
            return []
    
    def _parse_indeed_response(self, data: Dict[str, Any], request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Parse Indeed API response"""
        parsed_data = []
        
        try:
            if 'salaries' in data:
                for item in data['salaries']:
                    parsed_item = {
                        'location': request.location,
                        'occupation': item.get('job_title', request.occupation),
                        'industry': item.get('industry', request.industry),
                        'experience_level': item.get('experience_level', request.experience_level),
                        'education_level': item.get('education_level', request.education_level),
                        'median_salary': float(item.get('median_salary', 0)),
                        'mean_salary': float(item.get('average_salary', 0)),
                        'sample_size': int(item.get('sample_size', 0)),
                        'data_source': DataSource.INDEED.value,
                        'source_confidence_score': 0.7,  # Indeed is moderately reliable
                        'data_freshness_days': 0,
                        'year': request.year or datetime.now().year,
                        'quarter': request.quarter,
                        'metadata': {
                            'indeed_job_id': item.get('job_id'),
                            'indeed_company': item.get('company')
                        }
                    }
                    parsed_data.append(parsed_item)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing Indeed response: {e}")
            return []
    
    def _combine_salary_data(self, db_data: List[Dict[str, Any]], api_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine and deduplicate salary data"""
        combined = {}
        
        # Add database data
        for item in db_data:
            key = f"{item['location']}:{item['occupation']}:{item['industry']}:{item['data_source']}"
            combined[key] = item
        
        # Add API data (overwrite if more recent)
        for item in api_data:
            key = f"{item['location']}:{item['occupation']}:{item['industry']}:{item['data_source']}"
            if key not in combined or item.get('data_freshness_days', 999) < combined[key].get('data_freshness_days', 999):
                combined[key] = item
        
        return list(combined.values())
    
    def _store_salary_data_in_db(self, data: List[Dict[str, Any]], request: SalaryDataRequest):
        """Store salary data in database"""
        try:
            for item in data:
                # Check if record already exists
                existing = self.db_session.query(SalaryBenchmark).filter(
                    and_(
                        SalaryBenchmark.location == item['location'],
                        SalaryBenchmark.occupation == item['occupation'],
                        SalaryBenchmark.industry == item['industry'],
                        SalaryBenchmark.data_source == item['data_source'],
                        SalaryBenchmark.year == item['year'],
                        SalaryBenchmark.quarter == item['quarter']
                    )
                ).first()
                
                if existing:
                    # Update existing record
                    for key, value in item.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # Create new record
                    benchmark = SalaryBenchmark(**item)
                    self.db_session.add(benchmark)
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error storing salary data in database: {e}")
            self.db_session.rollback()
    
    async def _fetch_market_data(self, request: SalaryDataRequest) -> Optional[Dict[str, Any]]:
        """Fetch market data"""
        try:
            # Get from database first
            db_market_data = self._get_market_data_from_db(request)
            
            if db_market_data and self._is_data_fresh(db_market_data):
                return db_market_data
            
            # Fetch from APIs
            api_market_data = await self._fetch_market_data_from_apis(request)
            
            # Combine data
            combined_data = self._combine_market_data(db_market_data, api_market_data)
            
            # Store in database
            if combined_data:
                self._store_market_data_in_db(combined_data, request)
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return None
    
    def _get_market_data_from_db(self, request: SalaryDataRequest) -> Optional[Dict[str, Any]]:
        """Get market data from database"""
        try:
            query = self.db_session.query(MarketData).filter(
                MarketData.location == request.location
            )
            
            if request.occupation:
                query = query.filter(MarketData.occupation == request.occupation)
            
            if request.industry:
                query = query.filter(MarketData.industry == request.industry)
            
            if request.year:
                query = query.filter(MarketData.year == request.year)
            
            result = query.order_by(desc(MarketData.last_updated)).first()
            
            return result.to_dict() if result else None
            
        except Exception as e:
            logger.error(f"Error getting market data from database: {e}")
            return None
    
    async def _fetch_market_data_from_apis(self, request: SalaryDataRequest) -> Optional[Dict[str, Any]]:
        """Fetch market data from APIs"""
        try:
            # Fetch from FRED API for economic indicators
            fred_data = await self._fetch_fred_data(request)
            
            # Fetch from Indeed API for job market data
            indeed_market_data = await self._fetch_indeed_market_data(request)
            
            # Combine the data
            combined_data = {}
            if fred_data:
                combined_data.update(fred_data)
            if indeed_market_data:
                combined_data.update(indeed_market_data)
            
            return combined_data if combined_data else None
            
        except Exception as e:
            logger.error(f"Error fetching market data from APIs: {e}")
            return None
    
    async def _calculate_confidence_scores(self, request: SalaryDataRequest) -> Optional[Dict[str, Any]]:
        """Calculate confidence scores for the data"""
        try:
            # Get existing confidence scores from database
            db_confidence = self._get_confidence_scores_from_db(request)
            
            if db_confidence and self._is_data_fresh(db_confidence):
                return db_confidence
            
            # Calculate new confidence scores
            salary_data = self._get_salary_data_from_db(request)
            market_data = self._get_market_data_from_db(request)
            
            confidence_scores = self._calculate_comprehensive_confidence_scores(
                salary_data, market_data, request
            )
            
            # Store in database
            if confidence_scores:
                self._store_confidence_scores_in_db(confidence_scores, request)
            
            return confidence_scores
            
        except Exception as e:
            logger.error(f"Error calculating confidence scores: {e}")
            return None
    
    def _check_rate_limit(self, source: DataSource) -> bool:
        """Check if API rate limit is exceeded"""
        try:
            current_time = datetime.now()
            key = f"rate_limit:{source.value}:{current_time.strftime('%Y-%m-%d:%H')}"
            
            current_count = self.cache_service.redis_client.get(key)
            if current_count is None:
                current_count = 0
            else:
                current_count = int(current_count)
            
            limit = self.rate_limits[source]['requests_per_hour']
            
            if current_count >= limit:
                return False
            
            # Increment counter
            self.cache_service.redis_client.incr(key)
            self.cache_service.redis_client.expire(key, 3600)  # 1 hour
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow request if rate limiting fails
    
    async def _cache_data(self, cache_keys: Dict[str, str], data: Dict[str, Any], strategy: CacheStrategy):
        """Cache data in Redis"""
        try:
            config = self.cache_config[strategy]
            
            # Cache salary data
            if 'salary_benchmarks' in data:
                await self.cache_service.set(
                    cache_keys['salary'],
                    data,
                    ttl=config['salary_ttl'],
                    compress=config['compression']
                )
            
            # Cache market data
            if 'market_data' in data:
                await self.cache_service.set(
                    cache_keys['market'],
                    {'market_data': data['market_data']},
                    ttl=config['market_ttl'],
                    compress=config['compression']
                )
            
            # Cache confidence scores
            if 'confidence_scores' in data:
                await self.cache_service.set(
                    cache_keys['confidence'],
                    {'confidence_scores': data['confidence_scores']},
                    ttl=config['confidence_ttl'],
                    compress=config['compression']
                )
            
        except Exception as e:
            logger.error(f"Error caching data: {e}")
    
    def _get_cache_info(self, cache_keys: Dict[str, str]) -> Dict[str, Any]:
        """Get cache information"""
        return {
            'cache_keys': cache_keys,
            'cache_strategy': 'standard',
            'compression_enabled': True,
            'cache_timestamp': datetime.now().isoformat()
        }
    
    def _get_data_freshness(self, salary_data: List[Dict[str, Any]], market_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get data freshness information"""
        freshness = {
            'salary_data_freshness': 'unknown',
            'market_data_freshness': 'unknown',
            'overall_freshness': 'unknown'
        }
        
        if salary_data:
            # Calculate average freshness
            freshness_days = [item.get('data_freshness_days', 999) for item in salary_data]
            avg_freshness = sum(freshness_days) / len(freshness_days)
            
            if avg_freshness <= 1:
                freshness['salary_data_freshness'] = 'very_fresh'
            elif avg_freshness <= 7:
                freshness['salary_data_freshness'] = 'fresh'
            elif avg_freshness <= 30:
                freshness['salary_data_freshness'] = 'moderate'
            else:
                freshness['salary_data_freshness'] = 'stale'
        
        if market_data:
            market_freshness = market_data.get('data_freshness_days', 999)
            if market_freshness <= 1:
                freshness['market_data_freshness'] = 'very_fresh'
            elif market_freshness <= 7:
                freshness['market_data_freshness'] = 'fresh'
            elif market_freshness <= 30:
                freshness['market_data_freshness'] = 'moderate'
            else:
                freshness['market_data_freshness'] = 'stale'
        
        # Overall freshness
        if freshness['salary_data_freshness'] == 'very_fresh' and freshness['market_data_freshness'] == 'very_fresh':
            freshness['overall_freshness'] = 'very_fresh'
        elif freshness['salary_data_freshness'] in ['very_fresh', 'fresh'] and freshness['market_data_freshness'] in ['very_fresh', 'fresh']:
            freshness['overall_freshness'] = 'fresh'
        elif freshness['salary_data_freshness'] in ['very_fresh', 'fresh', 'moderate'] and freshness['market_data_freshness'] in ['very_fresh', 'fresh', 'moderate']:
            freshness['overall_freshness'] = 'moderate'
        else:
            freshness['overall_freshness'] = 'stale'
        
        return freshness
    
    def _generate_recommendations(self, salary_data: List[Dict[str, Any]], market_data: Optional[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on salary and market data"""
        recommendations = []
        
        if not salary_data:
            recommendations.append("Limited salary data available. Consider expanding your search criteria.")
            return recommendations
        
        # Analyze salary ranges
        salaries = [item.get('median_salary', 0) for item in salary_data if item.get('median_salary')]
        if salaries:
            avg_salary = sum(salaries) / len(salaries)
            min_salary = min(salaries)
            max_salary = max(salaries)
            
            if max_salary - min_salary > avg_salary * 0.5:
                recommendations.append("High salary variance detected. Consider factors like experience level and industry specialization.")
            
            if avg_salary < 50000:
                recommendations.append("Consider upskilling or exploring higher-paying industries to increase earning potential.")
        
        # Analyze market data
        if market_data:
            demand_score = market_data.get('demand_score', 0)
            if demand_score > 0.8:
                recommendations.append("High demand detected for this role. Good time to negotiate salary or explore new opportunities.")
            elif demand_score < 0.3:
                recommendations.append("Low demand detected. Consider developing additional skills or exploring related roles.")
            
            remote_work_pct = market_data.get('remote_work_percentage', 0)
            if remote_work_pct > 50:
                recommendations.append("High remote work availability. Consider remote opportunities for better work-life balance.")
        
        return recommendations
    
    def _is_data_fresh(self, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> bool:
        """Check if data is fresh enough"""
        if isinstance(data, list):
            if not data:
                return False
            # Check the most recent item
            data = data[0]
        
        freshness_days = data.get('data_freshness_days', 999)
        return freshness_days <= 7  # Consider data fresh if less than 7 days old
    
    def _increment_cache_hit(self, cache_key: str):
        """Increment cache hit counter in database"""
        try:
            cache_entry = self.db_session.query(SalaryDataCache).filter(
                SalaryDataCache.cache_key == cache_key
            ).first()
            
            if cache_entry:
                cache_entry.increment_hit()
                self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error incrementing cache hit: {e}")
    
    def _update_cache_tracking(self, cache_keys: Dict[str, str], strategy: CacheStrategy):
        """Update cache tracking in database"""
        try:
            for data_type, cache_key in cache_keys.items():
                cache_entry = self.db_session.query(SalaryDataCache).filter(
                    SalaryDataCache.cache_key == cache_key
                ).first()
                
                if not cache_entry:
                    cache_entry = SalaryDataCache(
                        cache_key=cache_key,
                        data_type=data_type,
                        redis_key=cache_key,
                        cache_strategy=strategy.value,
                        expires_at=datetime.now() + timedelta(seconds=self.cache_config[strategy][f'{data_type}_ttl'])
                    )
                    self.db_session.add(cache_entry)
                else:
                    cache_entry.last_updated = datetime.now()
                
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error updating cache tracking: {e}")
            self.db_session.rollback()
    
    async def _get_fallback_data(self, request: SalaryDataRequest, start_time: datetime) -> SalaryDataResponse:
        """Get fallback data when APIs fail"""
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SalaryDataResponse(
            request=request,
            salary_benchmarks=self._get_fallback_salary_data(request),
            processing_time_ms=processing_time,
            cache_hit=False
        )
    
    def _get_fallback_salary_data(self, request: SalaryDataRequest) -> List[Dict[str, Any]]:
        """Get fallback salary data"""
        # Return basic fallback data based on location and occupation
        fallback_data = {
            'location': request.location,
            'occupation': request.occupation or 'General',
            'industry': request.industry or 'General',
            'experience_level': request.experience_level or 'Mid',
            'education_level': request.education_level or 'Bachelor\'s',
            'median_salary': 60000.0,
            'mean_salary': 65000.0,
            'percentile_25': 45000.0,
            'percentile_75': 80000.0,
            'sample_size': 100,
            'data_source': DataSource.FALLBACK.value,
            'source_confidence_score': 0.3,
            'data_freshness_days': 365,
            'year': request.year or datetime.now().year,
            'quarter': request.quarter,
            'metadata': {'fallback': True}
        }
        
        return [fallback_data]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            stats = {
                'total_cache_entries': 0,
                'total_hits': 0,
                'total_misses': 0,
                'overall_hit_rate': 0.0,
                'cache_strategies': {},
                'data_types': {}
            }
            
            # Get overall stats
            cache_entries = self.db_session.query(SalaryDataCache).all()
            stats['total_cache_entries'] = len(cache_entries)
            
            for entry in cache_entries:
                stats['total_hits'] += entry.cache_hits
                stats['total_misses'] += entry.cache_misses
                
                # Strategy stats
                strategy = entry.cache_strategy
                if strategy not in stats['cache_strategies']:
                    stats['cache_strategies'][strategy] = {'hits': 0, 'misses': 0}
                stats['cache_strategies'][strategy]['hits'] += entry.cache_hits
                stats['cache_strategies'][strategy]['misses'] += entry.cache_misses
                
                # Data type stats
                data_type = entry.data_type
                if data_type not in stats['data_types']:
                    stats['data_types'][data_type] = {'hits': 0, 'misses': 0}
                stats['data_types'][data_type]['hits'] += entry.cache_hits
                stats['data_types'][data_type]['misses'] += entry.cache_misses
            
            # Calculate overall hit rate
            total_requests = stats['total_hits'] + stats['total_misses']
            if total_requests > 0:
                stats['overall_hit_rate'] = (stats['total_hits'] / total_requests) * 100
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def clear_cache(self, pattern: str = "salary_data:*") -> bool:
        """Clear cache entries matching pattern"""
        try:
            # Clear Redis cache
            cleared = self.cache_service.clear_cache(pattern)
            
            # Clear database cache tracking
            cache_entries = self.db_session.query(SalaryDataCache).filter(
                SalaryDataCache.cache_key.like(pattern.replace('*', '%'))
            ).all()
            
            for entry in cache_entries:
                entry.is_active = False
                entry.last_updated = datetime.now()
            
            self.db_session.commit()
            
            return cleared
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False 