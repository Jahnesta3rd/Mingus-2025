#!/usr/bin/env python3
"""
MINGUS External API Service

Service for integrating with external APIs for the Optimal Living Location feature.
Provides methods for RentCast, Zillow, and Google Maps Distance Matrix API integration.

Features:
- Rental listings from RentCast
- Home listings from Zillow via RapidAPI
- Route distance calculations from Google Maps
- Caching for route calculations
- Comprehensive error handling and retry logic
- Rate limiting and request management
"""

import os
import sys
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlencode
import time
from requests.adapters import HTTPAdapter

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import configurations
from config.external_apis import (
    external_api_config,
    rentals_config,
    zillow_config,
    google_maps_config,
    rate_limiter,
    cache_manager
)

# Configure logging
logger = logging.getLogger(__name__)

class ExternalAPIService:
    """
    Service for integrating with external APIs for optimal living location features.
    
    Provides methods for:
    - Rental listings from RentCast
    - Home listings from Zillow
    - Route distance calculations from Google Maps
    - Caching and rate limiting
    - Error handling and retry logic
    """
    
    def __init__(self):
        """Initialize external API service"""
        self.session = self._create_session()
        self.rentals_base_url = rentals_config.BASE_URL
        self.zillow_base_url = zillow_config.BASE_URL
        self.google_maps_base_url = google_maps_config.BASE_URL
        
        logger.info("External API Service initialized successfully")
    
    def _create_session(self) -> requests.Session:
        """Create configured HTTP session"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = external_api_config._get_retry_strategy('default')
        adapter = HTTPAdapter(max_retries=retry_strategy)
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    # ============================================================================
    # RENTCAST RENTAL LISTINGS API
    # ============================================================================

    _HOUSING_TYPE_MAP = {
        'apartment': 'Apartment',
        'house': 'Single Family',
        'condo': 'Condo',
    }

    def get_rental_listings(self, zip_code: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get long-term rental listings from RentCast API.

        Args:
            zip_code: 5-digit US zipcode
            filters: Search filters (price_max, max_rent, bedrooms, min_bathrooms, housing_type, limit)

        Returns:
            Dictionary containing rental listings and metadata
        """
        filters = filters or {}
        try:
            if rate_limiter.is_rate_limited('rentals'):
                return self._rentcast_error_response('Rate limit exceeded for rentcast API')

            params = self._prepare_rentcast_search_params(zip_code, filters)
            url = f"{self.rentals_base_url}{rentals_config.ENDPOINTS['search']}"
            headers = {
                'X-Api-Key': os.environ.get('RENTCAST_API_KEY', ''),
                'Accept': 'application/json',
            }

            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()

            rate_limiter.record_request('rentals')
            payload = response.json()
            listings = self._extract_rentcast_listings(payload)

            return {
                'success': True,
                'data': listings,
                'source': 'rentcast',
                'zip_code': zip_code,
                'filters_applied': filters,
                'retrieved_at': datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error('ExternalAPIService.get_rental_listings failed: %s', e)
            return self._rentcast_error_response(str(e))

    def _prepare_rentcast_search_params(
        self,
        zip_code: str,
        filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Map Mingus filter dict to RentCast query parameters."""
        params: Dict[str, Any] = {
            'zipCode': zip_code,
            'limit': filters.get('limit', 20),
        }
        max_price = filters.get('max_rent') or filters.get('price_max')
        if max_price:
            params['maxPrice'] = max_price
        if filters.get('bedrooms'):
            params['bedrooms'] = filters['bedrooms']
        if filters.get('min_bathrooms'):
            params['bathrooms'] = filters['min_bathrooms']
        housing_type = filters.get('housing_type')
        if housing_type in self._HOUSING_TYPE_MAP:
            params['propertyType'] = self._HOUSING_TYPE_MAP[housing_type]
        return params

    @staticmethod
    def _extract_rentcast_listings(payload: Any) -> List[Any]:
        """RentCast returns a top-level JSON array."""
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ('listings', 'data'):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        logger.warning(
            'Unexpected RentCast listings payload shape: %s',
            type(payload).__name__,
        )
        return []

    def _rentcast_error_response(self, error_message: str) -> Dict[str, Any]:
        return {
            'success': False,
            'data': [],
            'source': 'rentcast',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat(),
        }
    
    # ============================================================================
    # ZILLOW API INTEGRATION
    # ============================================================================
    
    def get_home_listings(self, zip_code: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get home listings from Zillow API via RapidAPI.
        
        Args:
            zip_code: 5-digit US zipcode
            filters: Dictionary of search filters
            
        Returns:
            Dictionary containing home listings and metadata
        """
        try:
            # Check rate limits
            if rate_limiter.is_rate_limited('zillow'):
                return self._create_rate_limit_response('zillow')
            
            # Prepare search parameters
            search_params = self._prepare_zillow_search_params(zip_code, filters)
            
            # Make API request
            response = self._make_zillow_request('search', search_params)
            
            # Record request for rate limiting
            rate_limiter.record_request('zillow')
            
            if response['success']:
                return {
                    'success': True,
                    'data': response['data'],
                    'source': 'zillow.com',
                    'zip_code': zip_code,
                    'filters_applied': filters or {},
                    'retrieved_at': datetime.utcnow().isoformat()
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error getting home listings for zipcode {zip_code}: {e}")
            return self._create_error_response('zillow', str(e))
    
    def _prepare_zillow_search_params(self, zip_code: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare search parameters for Zillow API"""
        params = {
            'location': zip_code,
            'limit': filters.get('limit', 50) if filters else 50,
            'offset': filters.get('offset', 0) if filters else 0
        }
        
        if filters:
            # Map filter parameters to API parameters
            for filter_key, filter_value in filters.items():
                if filter_key in zillow_config.SEARCH_PARAMS:
                    api_param = zillow_config.SEARCH_PARAMS[filter_key]
                    params[api_param] = filter_value
        
        return params
    
    def _make_zillow_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Zillow API via RapidAPI"""
        try:
            url = f"{self.zillow_base_url}{zillow_config.ENDPOINTS[endpoint]}"
            headers = external_api_config._get_headers_config('zillow')
            
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=external_api_config._get_timeout_config('zillow')
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'data': data,
                    'status_code': response.status_code
                }
            else:
                error_msg = zillow_config.ERROR_CODES.get(
                    response.status_code, 
                    f"HTTP {response.status_code}"
                )
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Zillow API request failed: {e}")
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    # ============================================================================
    # GOOGLE MAPS DISTANCE MATRIX API INTEGRATION
    # ============================================================================
    
    def calculate_route_distance(self, origin: str, destination: str, 
                               mode: str = 'driving', avoid: List[str] = None) -> Dict[str, Any]:
        """
        Calculate route distance using Google Maps Distance Matrix API.
        
        Args:
            origin: Origin address or coordinates
            destination: Destination address or coordinates
            mode: Travel mode (driving, walking, bicycling, transit)
            avoid: List of things to avoid (tolls, highways, ferries, indoor)
            
        Returns:
            Dictionary containing route information and distance
        """
        try:
            # Check cache first
            cache_key = self._generate_route_cache_key(origin, destination, mode, avoid)
            cached_result = cache_manager.get_cached_response(cache_key)
            
            if cached_result:
                logger.debug(f"Using cached route data for {origin} -> {destination}")
                return cached_result
            
            # Check rate limits
            if rate_limiter.is_rate_limited('google_maps'):
                return self._create_rate_limit_response('google_maps')
            
            # Prepare request parameters
            params = self._prepare_google_maps_params(origin, destination, mode, avoid)
            
            # Make API request
            response = self._make_google_maps_request('distance_matrix', params)
            
            # Record request for rate limiting
            rate_limiter.record_request('google_maps')
            
            if response['success']:
                # Cache the result
                cache_manager.set_cached_response(cache_key, response)
                
                return {
                    'success': True,
                    'data': response['data'],
                    'source': 'google_maps',
                    'origin': origin,
                    'destination': destination,
                    'mode': mode,
                    'avoid': avoid or [],
                    'cached': False,
                    'retrieved_at': datetime.utcnow().isoformat()
                }
            else:
                return response
                
        except Exception as e:
            logger.error(f"Error calculating route distance from {origin} to {destination}: {e}")
            return self._create_error_response('google_maps', str(e))
    
    def get_cached_route(self, origin_zip: str, dest_zip: str, mode: str = 'driving') -> Optional[Dict[str, Any]]:
        """
        Get cached route data if available.
        
        Args:
            origin_zip: Origin zipcode
            dest_zip: Destination zipcode
            mode: Travel mode
            
        Returns:
            Cached route data or None if not found
        """
        cache_key = self._generate_route_cache_key(origin_zip, dest_zip, mode)
        return cache_manager.get_cached_response(cache_key)
    
    def update_route_cache(self, origin_zip: str, dest_zip: str, route_data: Dict[str, Any]):
        """
        Update route cache with new data.
        
        Args:
            origin_zip: Origin zipcode
            dest_zip: Destination zipcode
            route_data: Route data to cache
        """
        cache_key = self._generate_route_cache_key(origin_zip, dest_zip)
        cache_manager.set_cached_response(cache_key, route_data)
        logger.debug(f"Updated route cache for {origin_zip} -> {dest_zip}")
    
    def _generate_route_cache_key(self, origin: str, destination: str, 
                                 mode: str = 'driving', avoid: List[str] = None) -> str:
        """Generate cache key for route data"""
        avoid_str = ','.join(sorted(avoid or []))
        return f"route:{origin}:{destination}:{mode}:{avoid_str}"
    
    def _prepare_google_maps_params(self, origin: str, destination: str, 
                                   mode: str, avoid: List[str] = None) -> Dict[str, Any]:
        """Prepare parameters for Google Maps Distance Matrix API"""
        params = {
            'origins': origin,
            'destinations': destination,
            'mode': mode,
            'units': 'imperial',
            'key': os.environ.get('GOOGLE_MAPS_API_KEY')
        }
        
        if avoid:
            params['avoid'] = '|'.join(avoid)
        
        return params
    
    def _make_google_maps_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Google Maps API"""
        try:
            url = f"{self.google_maps_base_url}{google_maps_config.ENDPOINTS[endpoint]}"
            
            response = self.session.get(
                url,
                params=params,
                timeout=external_api_config._get_timeout_config('google_maps')
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for Google Maps API errors
                if data.get('status') != 'OK':
                    error_msg = data.get('error_message', 'Unknown Google Maps API error')
                    return {
                        'success': False,
                        'error': error_msg,
                        'status': data.get('status')
                    }
                
                return {
                    'success': True,
                    'data': data,
                    'status_code': response.status_code
                }
            else:
                error_msg = google_maps_config.ERROR_CODES.get(
                    response.status_code, 
                    f"HTTP {response.status_code}"
                )
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Maps API request failed: {e}")
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _create_rate_limit_response(self, api_name: str) -> Dict[str, Any]:
        """Create rate limit exceeded response"""
        return {
            'success': False,
            'error': f'Rate limit exceeded for {api_name} API',
            'retry_after': 60,
            'api_name': api_name
        }
    
    def _create_error_response(self, api_name: str, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'success': False,
            'error': error_message,
            'api_name': api_name,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and health information"""
        try:
            # Check API key availability
            api_keys_status = {
                'rentcast_api_key': bool(os.environ.get('RENTCAST_API_KEY')),
                'zillow_rapidapi_key': bool(os.environ.get('ZILLOW_RAPIDAPI_KEY')),
                'google_maps_api_key': bool(os.environ.get('GOOGLE_MAPS_API_KEY'))
            }
            
            # Check rate limiter status
            rate_limiter_status = {
                'rentals': {
                    'current_requests': rate_limiter.request_counts.get('rentals', 0),
                    'rate_limited': rate_limiter.is_rate_limited('rentals')
                },
                'zillow': {
                    'current_requests': rate_limiter.request_counts.get('zillow', 0),
                    'rate_limited': rate_limiter.is_rate_limited('zillow')
                },
                'google_maps': {
                    'current_requests': rate_limiter.request_counts.get('google_maps', 0),
                    'rate_limited': rate_limiter.is_rate_limited('google_maps')
                }
            }
            
            # Check cache status
            cache_status = {
                'total_entries': len(cache_manager.cache),
                'max_size': cache_manager.max_cache_size,
                'utilization_percent': (len(cache_manager.cache) / cache_manager.max_cache_size) * 100
            }
            
            return {
                'service_status': 'healthy',
                'api_keys': api_keys_status,
                'rate_limiter': rate_limiter_status,
                'cache': cache_status,
                'last_check': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                'service_status': 'error',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def clear_cache(self, cache_type: str = 'all') -> Dict[str, Any]:
        """Clear API cache"""
        try:
            if cache_type == 'all' or cache_type == 'routes':
                cache_manager.cache.clear()
                cache_manager.cache_ttl.clear()
                logger.info("Cleared all API cache")
            
            return {
                'success': True,
                'message': f'Cleared {cache_type} cache',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            return {
                'total_entries': len(cache_manager.cache),
                'max_size': cache_manager.max_cache_size,
                'utilization_percent': (len(cache_manager.cache) / cache_manager.max_cache_size) * 100,
                'cache_ttl_entries': len(cache_manager.cache_ttl),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

# Global service instance
external_api_service = ExternalAPIService()

# Export service
__all__ = ['external_api_service', 'ExternalAPIService']
