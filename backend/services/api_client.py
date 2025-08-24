"""
Async API Client for External Salary Data APIs
Handles HTTP requests with retry logic, rate limiting, and error handling
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class APISource(str, Enum):
    """API source types"""
    BLS = "bls"
    CENSUS = "census"
    FRED = "fred"
    INDEED = "indeed"

@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: int = 200
    source: Optional[APISource] = None
    timestamp: datetime = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, calls_per_minute: int, calls_per_hour: int = None):
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour or (calls_per_minute * 60)
        self.minute_calls = []
        self.hour_calls = []
    
    async def acquire(self) -> bool:
        """Check if we can make an API call"""
        now = datetime.now()
        
        # Clean old minute calls
        self.minute_calls = [call_time for call_time in self.minute_calls 
                           if now - call_time < timedelta(minutes=1)]
        
        # Clean old hour calls
        self.hour_calls = [call_time for call_time in self.hour_calls 
                          if now - call_time < timedelta(hours=1)]
        
        # Check limits
        if len(self.minute_calls) >= self.calls_per_minute:
            return False
        
        if len(self.hour_calls) >= self.calls_per_hour:
            return False
        
        # Record call
        self.minute_calls.append(now)
        self.hour_calls.append(now)
        return True
    
    def get_wait_time(self) -> float:
        """Get wait time until next available slot"""
        now = datetime.now()
        
        if self.minute_calls:
            oldest_minute = min(self.minute_calls)
            minute_wait = 60 - (now - oldest_minute).total_seconds()
        else:
            minute_wait = 0
        
        if self.hour_calls:
            oldest_hour = min(self.hour_calls)
            hour_wait = 3600 - (now - oldest_hour).total_seconds()
        else:
            hour_wait = 0
        
        return max(minute_wait, hour_wait, 0)

class AsyncAPIClient:
    """
    Async API client for external salary data APIs
    """
    
    def __init__(self):
        """Initialize the API client with rate limiters"""
        self.session = None
        self.rate_limiters = {
            APISource.BLS: RateLimiter(calls_per_minute=10, calls_per_hour=500),
            APISource.CENSUS: RateLimiter(calls_per_minute=20, calls_per_hour=1000),
            APISource.FRED: RateLimiter(calls_per_minute=15, calls_per_hour=800),
            APISource.INDEED: RateLimiter(calls_per_minute=5, calls_per_hour=100)  # Free tier limit
        }
        
        # API configurations
        self.api_configs = {
            APISource.BLS: {
                'base_url': 'https://api.bls.gov/publicAPI/v2/timeseries/data/',
                'headers': {
                    'BLS-API-Version': '2.0',
                    'Content-Type': 'application/json'
                },
                'timeout': 30
            },
            APISource.CENSUS: {
                'base_url': 'https://api.census.gov/data/2022/acs/acs1',
                'headers': {
                    'User-Agent': 'Mingus-Salary-Data-Client/1.0'
                },
                'timeout': 30
            },
            APISource.FRED: {
                'base_url': 'https://api.stlouisfed.org/fred/series/observations',
                'headers': {
                    'User-Agent': 'Mingus-Salary-Data-Client/1.0'
                },
                'timeout': 30
            },
            APISource.INDEED: {
                'base_url': 'https://api.indeed.com/ads/apisearch',
                'headers': {
                    'User-Agent': 'Mingus-Salary-Data-Client/1.0'
                },
                'timeout': 30
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _wait_for_rate_limit(self, source: APISource) -> None:
        """Wait for rate limit to reset"""
        rate_limiter = self.rate_limiters[source]
        
        while not await rate_limiter.acquire():
            wait_time = rate_limiter.get_wait_time()
            logger.info(f"Rate limit reached for {source}, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(min(wait_time + 1, 60))  # Add 1 second buffer
    
    async def _make_request(self, 
                          method: str, 
                          url: str, 
                          source: APISource,
                          **kwargs) -> APIResponse:
        """
        Make an HTTP request with retry logic and error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            source: API source for rate limiting
            **kwargs: Additional request parameters
        
        Returns:
            APIResponse object
        """
        # Wait for rate limit
        await self._wait_for_rate_limit(source)
        
        # Get API config
        config = self.api_configs[source]
        headers = {**config['headers'], **kwargs.get('headers', {})}
        timeout = aiohttp.ClientTimeout(total=config['timeout'])
        
        # Retry configuration
        max_retries = 3
        retry_delays = [1, 2, 5]  # Exponential backoff
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                
                async with self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=timeout,
                    **{k: v for k, v in kwargs.items() if k != 'headers'}
                ) as response:
                    
                    response_time = time.time() - start_time
                    logger.info(f"API call to {source} completed in {response_time:.2f}s (attempt {attempt + 1})")
                    
                    # Parse response
                    if response.status == 200:
                        try:
                            if 'application/json' in response.headers.get('content-type', ''):
                                data = await response.json()
                            else:
                                data = await response.text()
                            
                            # Extract rate limit info
                            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
                            rate_limit_reset = response.headers.get('X-RateLimit-Reset')
                            
                            return APIResponse(
                                success=True,
                                data=data,
                                status_code=response.status,
                                source=source,
                                rate_limit_remaining=int(rate_limit_remaining) if rate_limit_remaining else None,
                                rate_limit_reset=datetime.fromtimestamp(int(rate_limit_reset)) if rate_limit_reset else None
                            )
                            
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.error(f"Failed to parse response from {source}: {e}")
                            return APIResponse(
                                success=False,
                                error=f"Invalid response format: {str(e)}",
                                status_code=response.status,
                                source=source
                            )
                    
                    elif response.status == 429:  # Rate limited
                        retry_after = response.headers.get('Retry-After', 60)
                        logger.warning(f"Rate limited by {source}, retrying after {retry_after}s")
                        await asyncio.sleep(int(retry_after))
                        continue
                    
                    elif response.status >= 500:  # Server error
                        logger.warning(f"Server error from {source}: {response.status}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delays[attempt])
                            continue
                    
                    else:  # Client error
                        error_text = await response.text()
                        logger.error(f"API error from {source}: {response.status} - {error_text}")
                        return APIResponse(
                            success=False,
                            error=f"HTTP {response.status}: {error_text}",
                            status_code=response.status,
                            source=source
                        )
            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout from {source} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delays[attempt])
                    continue
                return APIResponse(
                    success=False,
                    error="Request timeout",
                    source=source
                )
            
            except aiohttp.ClientError as e:
                logger.error(f"Network error from {source}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delays[attempt])
                    continue
                return APIResponse(
                    success=False,
                    error=f"Network error: {str(e)}",
                    source=source
                )
            
            except Exception as e:
                logger.error(f"Unexpected error from {source}: {e}")
                return APIResponse(
                    success=False,
                    error=f"Unexpected error: {str(e)}",
                    source=source
                )
        
        return APIResponse(
            success=False,
            error="Max retries exceeded",
            source=source
        )
    
    async def get_bls_data(self, series_ids: List[str], start_year: str, end_year: str, api_key: str) -> APIResponse:
        """
        Get data from Bureau of Labor Statistics API
        
        Args:
            series_ids: List of BLS series IDs
            start_year: Start year for data
            end_year: End year for data
            api_key: BLS API key
        
        Returns:
            APIResponse with BLS data
        """
        payload = {
            'seriesid': series_ids,
            'startyear': start_year,
            'endyear': end_year,
            'registrationkey': api_key
        }
        
        return await self._make_request(
            method='POST',
            url=self.api_configs[APISource.BLS]['base_url'],
            source=APISource.BLS,
            json=payload
        )
    
    async def get_census_data(self, variables: List[str], geography: str, api_key: str) -> APIResponse:
        """
        Get data from Census Bureau API
        
        Args:
            variables: List of census variables
            geography: Geographic filter
            api_key: Census API key
        
        Returns:
            APIResponse with census data
        """
        params = {
            'get': ','.join(variables),
            'for': geography,
            'key': api_key
        }
        
        return await self._make_request(
            method='GET',
            url=self.api_configs[APISource.CENSUS]['base_url'],
            source=APISource.CENSUS,
            params=params
        )
    
    async def get_fred_data(self, series_id: str, api_key: str, **params) -> APIResponse:
        """
        Get data from FRED API
        
        Args:
            series_id: FRED series ID
            api_key: FRED API key
            **params: Additional parameters
        
        Returns:
            APIResponse with FRED data
        """
        params.update({
            'series_id': series_id,
            'api_key': api_key,
            'file_type': 'json'
        })
        
        return await self._make_request(
            method='GET',
            url=self.api_configs[APISource.FRED]['base_url'],
            source=APISource.FRED,
            params=params
        )
    
    async def get_indeed_data(self, publisher_id: str, **params) -> APIResponse:
        """
        Get data from Indeed API
        
        Args:
            publisher_id: Indeed publisher ID
            **params: Search parameters
        
        Returns:
            APIResponse with Indeed data
        """
        params.update({
            'publisher': publisher_id,
            'format': 'json',
            'v': 2
        })
        
        return await self._make_request(
            method='GET',
            url=self.api_configs[APISource.INDEED]['base_url'],
            source=APISource.INDEED,
            params=params
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all APIs
        
        Returns:
            Health status for all APIs
        """
        health_status = {}
        
        for source in APISource:
            try:
                # Simple health check - just test connectivity
                if source == APISource.BLS:
                    response = await self._make_request(
                        method='GET',
                        url='https://api.bls.gov/publicAPI/v2/timeseries/data/',
                        source=source
                    )
                elif source == APISource.CENSUS:
                    response = await self._make_request(
                        method='GET',
                        url='https://api.census.gov/data/2022/acs/acs1',
                        source=source
                    )
                elif source == APISource.FRED:
                    response = await self._make_request(
                        method='GET',
                        url='https://api.stlouisfed.org/fred/series/observations',
                        source=source
                    )
                elif source == APISource.INDEED:
                    response = await self._make_request(
                        method='GET',
                        url='https://api.indeed.com/ads/apisearch',
                        source=source
                    )
                
                health_status[source.value] = {
                    'status': 'healthy' if response.success else 'unhealthy',
                    'response_time': (response.timestamp - datetime.now()).total_seconds() if response.timestamp else None,
                    'error': response.error
                }
                
            except Exception as e:
                health_status[source.value] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return health_status 