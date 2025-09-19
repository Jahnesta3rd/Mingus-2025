#!/usr/bin/env python3
"""
MINGUS External API Configuration

Configuration for external API integrations used by the Optimal Living Location feature.
Includes Rentals.com, Zillow, and Google Maps Distance Matrix API configurations.

Features:
- API key management and validation
- Rate limiting configurations
- Error handling and retry logic
- Caching settings for route calculations
- Comprehensive logging integration
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logger = logging.getLogger(__name__)

class ExternalAPIConfig:
    """
    Configuration class for external API integrations.
    
    Manages API keys, rate limits, retry logic, and error handling
    for Rentals.com, Zillow, and Google Maps APIs.
    """
    
    def __init__(self):
        """Initialize external API configuration"""
        self._validate_api_keys()
        self._setup_session_configs()
        logger.info("External API configuration initialized")
    
    def _validate_api_keys(self):
        """Validate that required API keys are present"""
        required_keys = {
            'RENTALS_API_KEY': os.environ.get('RENTALS_API_KEY'),
            'ZILLOW_RAPIDAPI_KEY': os.environ.get('ZILLOW_RAPIDAPI_KEY'),
            'GOOGLE_MAPS_API_KEY': os.environ.get('GOOGLE_MAPS_API_KEY')
        }
        
        missing_keys = [key for key, value in required_keys.items() if not value]
        if missing_keys:
            logger.warning(f"Missing API keys: {missing_keys}")
            logger.warning("Some external API features may not work properly")
    
    def _setup_session_configs(self):
        """Setup HTTP session configurations for each API"""
        self.session_configs = {
            'rentals': self._create_session_config('rentals'),
            'zillow': self._create_session_config('zillow'),
            'google_maps': self._create_session_config('google_maps')
        }
    
    def _create_session_config(self, api_name: str) -> Dict[str, Any]:
        """Create session configuration for a specific API"""
        return {
            'timeout': self._get_timeout_config(api_name),
            'retry_strategy': self._get_retry_strategy(api_name),
            'rate_limit': self._get_rate_limit_config(api_name),
            'headers': self._get_headers_config(api_name)
        }
    
    def _get_timeout_config(self, api_name: str) -> Dict[str, int]:
        """Get timeout configuration for API"""
        timeouts = {
            'rentals': {'connect': 10, 'read': 30},
            'zillow': {'connect': 10, 'read': 30},
            'google_maps': {'connect': 5, 'read': 15}
        }
        return timeouts.get(api_name, {'connect': 10, 'read': 30})
    
    def _get_retry_strategy(self, api_name: str) -> Retry:
        """Get retry strategy for API"""
        retry_configs = {
            'rentals': Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"]
            ),
            'zillow': Retry(
                total=3,
                backoff_factor=2,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"]
            ),
            'google_maps': Retry(
                total=2,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"]
            )
        }
        return retry_configs.get(api_name, Retry(total=3, backoff_factor=1))
    
    def _get_rate_limit_config(self, api_name: str) -> Dict[str, Any]:
        """Get rate limiting configuration for API"""
        rate_limits = {
            'rentals': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000,
                'burst_limit': 10
            },
            'zillow': {
                'requests_per_minute': 30,
                'requests_per_hour': 500,
                'burst_limit': 5
            },
            'google_maps': {
                'requests_per_minute': 100,
                'requests_per_hour': 2000,
                'burst_limit': 20
            }
        }
        return rate_limits.get(api_name, {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'burst_limit': 10
        })
    
    def _get_headers_config(self, api_name: str) -> Dict[str, str]:
        """Get headers configuration for API"""
        base_headers = {
            'User-Agent': 'MINGUS-OptimalLiving/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        
        api_specific_headers = {
            'rentals': {
                **base_headers,
                'X-API-Key': os.environ.get('RENTALS_API_KEY', ''),
                'Content-Type': 'application/json'
            },
            'zillow': {
                **base_headers,
                'X-RapidAPI-Key': os.environ.get('ZILLOW_RAPIDAPI_KEY', ''),
                'X-RapidAPI-Host': 'zillow-com1.p.rapidapi.com'
            },
            'google_maps': {
                **base_headers,
                'Content-Type': 'application/json'
            }
        }
        
        return api_specific_headers.get(api_name, base_headers)

class RentalsAPIConfig:
    """Configuration for Rentals.com API integration"""
    
    BASE_URL = "https://api.rentals.com/v1"
    ENDPOINTS = {
        'search': '/listings/search',
        'details': '/listings/{listing_id}',
        'photos': '/listings/{listing_id}/photos',
        'amenities': '/listings/{listing_id}/amenities'
    }
    
    # Search parameters and filters
    SEARCH_PARAMS = {
        'location': 'zip_code',
        'price_min': 'min_price',
        'price_max': 'max_price',
        'bedrooms': 'bedrooms',
        'bathrooms': 'bathrooms',
        'property_type': 'property_type',
        'pet_friendly': 'pet_friendly',
        'furnished': 'furnished',
        'parking': 'parking',
        'laundry': 'laundry',
        'air_conditioning': 'air_conditioning',
        'dishwasher': 'dishwasher',
        'pool': 'pool',
        'gym': 'gym'
    }
    
    # Property types supported
    PROPERTY_TYPES = [
        'apartment',
        'house',
        'condo',
        'townhouse',
        'studio',
        'loft'
    ]
    
    # Rate limiting
    RATE_LIMITS = {
        'requests_per_minute': 60,
        'requests_per_hour': 1000,
        'daily_limit': 10000
    }
    
    # Error handling
    ERROR_CODES = {
        400: 'Bad Request - Invalid parameters',
        401: 'Unauthorized - Invalid API key',
        403: 'Forbidden - API key lacks permissions',
        404: 'Not Found - No listings found',
        429: 'Rate Limit Exceeded',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable'
    }

class ZillowAPIConfig:
    """Configuration for Zillow API integration via RapidAPI"""
    
    BASE_URL = "https://zillow-com1.p.rapidapi.com"
    ENDPOINTS = {
        'search': '/property/search',
        'details': '/property/details',
        'photos': '/property/photos',
        'price_history': '/property/price-history',
        'similar_homes': '/property/similar-homes'
    }
    
    # Search parameters
    SEARCH_PARAMS = {
        'location': 'location',
        'price_min': 'minPrice',
        'price_max': 'maxPrice',
        'bedrooms': 'bedrooms',
        'bathrooms': 'bathrooms',
        'home_type': 'homeType',
        'square_feet_min': 'minSqft',
        'square_feet_max': 'maxSqft',
        'year_built_min': 'minYearBuilt',
        'year_built_max': 'maxYearBuilt',
        'lot_size_min': 'minLotSize',
        'lot_size_max': 'maxLotSize',
        'has_pool': 'hasPool',
        'has_garage': 'hasGarage',
        'new_construction': 'newConstruction'
    }
    
    # Home types supported
    HOME_TYPES = [
        'house',
        'condo',
        'townhouse',
        'apartment',
        'mobile',
        'land',
        'other'
    ]
    
    # Rate limiting
    RATE_LIMITS = {
        'requests_per_minute': 30,
        'requests_per_hour': 500,
        'daily_limit': 5000
    }
    
    # Error handling
    ERROR_CODES = {
        400: 'Bad Request - Invalid search parameters',
        401: 'Unauthorized - Invalid RapidAPI key',
        403: 'Forbidden - Insufficient permissions',
        404: 'Not Found - No properties found',
        429: 'Rate Limit Exceeded',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable'
    }

class GoogleMapsAPIConfig:
    """Configuration for Google Maps Distance Matrix API"""
    
    BASE_URL = "https://maps.googleapis.com/maps/api"
    ENDPOINTS = {
        'distance_matrix': '/distancematrix/json',
        'geocoding': '/geocode/json',
        'places': '/place/textsearch/json'
    }
    
    # Distance Matrix parameters
    DISTANCE_MATRIX_PARAMS = {
        'origins': 'origins',
        'destinations': 'destinations',
        'mode': 'mode',
        'avoid': 'avoid',
        'units': 'units',
        'departure_time': 'departure_time',
        'traffic_model': 'traffic_model'
    }
    
    # Travel modes
    TRAVEL_MODES = [
        'driving',
        'walking',
        'bicycling',
        'transit'
    ]
    
    # Avoid options
    AVOID_OPTIONS = [
        'tolls',
        'highways',
        'ferries',
        'indoor'
    ]
    
    # Units
    UNITS = ['metric', 'imperial']
    
    # Rate limiting
    RATE_LIMITS = {
        'requests_per_minute': 100,
        'requests_per_hour': 2000,
        'daily_limit': 40000
    }
    
    # Caching configuration
    CACHE_CONFIG = {
        'route_cache_ttl': int(os.environ.get('ROUTE_CACHE_REFRESH_DAYS', 7)) * 24 * 60 * 60,  # seconds
        'max_cache_size': 10000,
        'cache_cleanup_interval': 3600  # 1 hour
    }
    
    # Error handling
    ERROR_CODES = {
        400: 'Bad Request - Invalid parameters',
        403: 'Forbidden - Invalid API key or quota exceeded',
        404: 'Not Found - No route found',
        429: 'Rate Limit Exceeded',
        500: 'Internal Server Error'
    }

class APIRateLimiter:
    """Rate limiter for external API calls"""
    
    def __init__(self):
        self.rate_limits = {}
        self.request_counts = {}
        self.last_reset = {}
    
    def is_rate_limited(self, api_name: str, endpoint: str = None) -> bool:
        """Check if API call would exceed rate limits"""
        current_time = self._get_current_time()
        
        # Reset counters if needed
        if self._should_reset_counters(api_name, current_time):
            self._reset_counters(api_name, current_time)
        
        # Check rate limits
        config = self._get_rate_limit_config(api_name)
        current_count = self.request_counts.get(api_name, 0)
        
        return current_count >= config['requests_per_minute']
    
    def record_request(self, api_name: str, endpoint: str = None):
        """Record an API request for rate limiting"""
        current_time = self._get_current_time()
        
        if api_name not in self.request_counts:
            self.request_counts[api_name] = 0
        
        self.request_counts[api_name] += 1
        self.last_reset[api_name] = current_time
    
    def _get_current_time(self) -> int:
        """Get current time in seconds"""
        import time
        return int(time.time())
    
    def _should_reset_counters(self, api_name: str, current_time: int) -> bool:
        """Check if counters should be reset"""
        last_reset = self.last_reset.get(api_name, 0)
        return current_time - last_reset >= 60  # Reset every minute
    
    def _reset_counters(self, api_name: str, current_time: int):
        """Reset request counters"""
        self.request_counts[api_name] = 0
        self.last_reset[api_name] = current_time
    
    def _get_rate_limit_config(self, api_name: str) -> Dict[str, int]:
        """Get rate limit configuration for API"""
        configs = {
            'rentals': RentalsAPIConfig.RATE_LIMITS,
            'zillow': ZillowAPIConfig.RATE_LIMITS,
            'google_maps': GoogleMapsAPIConfig.RATE_LIMITS
        }
        return configs.get(api_name, {'requests_per_minute': 60})

class APICacheManager:
    """Cache manager for external API responses"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = {}
        self.max_cache_size = GoogleMapsAPIConfig.CACHE_CONFIG['max_cache_size']
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached API response"""
        if cache_key in self.cache:
            if self._is_cache_valid(cache_key):
                logger.debug(f"Cache hit for key: {cache_key}")
                return self.cache[cache_key]
            else:
                # Remove expired cache entry
                self._remove_cache_entry(cache_key)
        
        return None
    
    def set_cached_response(self, cache_key: str, response: Dict[str, Any], ttl: int = None):
        """Cache API response"""
        if ttl is None:
            ttl = GoogleMapsAPIConfig.CACHE_CONFIG['route_cache_ttl']
        
        # Check cache size limit
        if len(self.cache) >= self.max_cache_size:
            self._cleanup_old_entries()
        
        self.cache[cache_key] = response
        self.cache_ttl[cache_key] = self._get_expiry_time(ttl)
        
        logger.debug(f"Cached response for key: {cache_key}")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.cache_ttl:
            return False
        
        current_time = self._get_current_time()
        return current_time < self.cache_ttl[cache_key]
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove cache entry"""
        if cache_key in self.cache:
            del self.cache[cache_key]
        if cache_key in self.cache_ttl:
            del self.cache_ttl[cache_key]
    
    def _cleanup_old_entries(self):
        """Clean up old cache entries"""
        current_time = self._get_current_time()
        expired_keys = [
            key for key, expiry in self.cache_ttl.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            self._remove_cache_entry(key)
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _get_expiry_time(self, ttl: int) -> int:
        """Get expiry time for cache entry"""
        current_time = self._get_current_time()
        return current_time + ttl
    
    def _get_current_time(self) -> int:
        """Get current time in seconds"""
        import time
        return int(time.time())

# Global instances
external_api_config = ExternalAPIConfig()
rentals_config = RentalsAPIConfig()
zillow_config = ZillowAPIConfig()
google_maps_config = GoogleMapsAPIConfig()
rate_limiter = APIRateLimiter()
cache_manager = APICacheManager()

# Export configurations
__all__ = [
    'external_api_config',
    'rentals_config', 
    'zillow_config',
    'google_maps_config',
    'rate_limiter',
    'cache_manager'
]
