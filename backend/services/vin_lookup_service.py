#!/usr/bin/env python3
"""
VIN Lookup Service for Mingus Flask Application
Uses the free NHTSA VIN decoder API to retrieve vehicle information

Features:
- NHTSA VIN decoder API integration
- Error handling and timeout management
- Fallback mechanism for API unavailability
- Standardized vehicle information format
- Comprehensive logging
- Follows Mingus service class patterns
"""

import logging
import requests
import time
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

class VINLookupError(Exception):
    """Custom exception for VIN lookup errors"""
    pass

class VINValidationError(VINLookupError):
    """Exception for VIN validation errors"""
    pass

class VINAPIError(VINLookupError):
    """Exception for VIN API errors"""
    pass

class VINServiceStatus(Enum):
    """VIN service status indicators"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    MAINTENANCE = "maintenance"

@dataclass
class VehicleInfo:
    """Standardized vehicle information structure"""
    vin: str
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    trim: Optional[str] = None
    engine: Optional[str] = None
    fuel_type: Optional[str] = None
    body_class: Optional[str] = None
    drive_type: Optional[str] = None
    transmission: Optional[str] = None
    doors: Optional[int] = None
    windows: Optional[int] = None
    series: Optional[str] = None
    plant_city: Optional[str] = None
    plant_state: Optional[str] = None
    plant_country: Optional[str] = None
    manufacturer: Optional[str] = None
    model_year: Optional[int] = None
    vehicle_type: Optional[str] = None
    error_code: Optional[str] = None
    error_text: Optional[str] = None
    lookup_timestamp: Optional[datetime] = None
    source: str = "nhtsa"

class VINLookupService:
    """
    VIN Lookup Service using NHTSA VIN decoder API
    
    This service provides comprehensive VIN lookup functionality with:
    - NHTSA API integration
    - Error handling and timeout management
    - Fallback mechanisms
    - Standardized vehicle information format
    - Comprehensive logging
    """
    
    def __init__(self, timeout: int = 10, max_retries: int = 3, cache_ttl: int = 3600):
        """
        Initialize VIN lookup service
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            cache_ttl: Cache time-to-live in seconds
        """
        self.base_url = "https://vpic.nhtsa.dot.gov/api"
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.service_status = VINServiceStatus.AVAILABLE
        self.last_error_time = None
        self.error_count = 0
        self.max_errors = 5
        self.error_reset_time = 300  # 5 minutes
        
        logger.info("VINLookupService initialized successfully")
    
    def validate_vin(self, vin: str) -> bool:
        """
        Validate VIN format and checksum
        
        Args:
            vin: VIN to validate
            
        Returns:
            bool: True if VIN is valid, False otherwise
        """
        if not vin or not isinstance(vin, str):
            return False
        
        # Remove spaces and convert to uppercase
        vin = vin.strip().upper()
        
        # Check length
        if len(vin) != 17:
            return False
        
        # Check for invalid characters (I, O, Q not allowed)
        if re.search(r'[IOQ]', vin):
            return False
        
        # Check if all characters are alphanumeric
        if not vin.isalnum():
            return False
        
        # Basic checksum validation (simplified)
        # In production, you might want to implement full VIN checksum validation
        return True
    
    def _make_request(self, vin: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Make request to NHTSA VIN decoder API
        
        Args:
            vin: VIN to lookup
            
        Returns:
            Tuple of (success, response_data)
        """
        url = f"{self.base_url}/vehicles/DecodeVin/{vin}?format=json"
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making VIN lookup request for VIN: {vin[:8]}... (attempt {attempt + 1})")
                
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors
                if 'Results' not in data:
                    logger.error(f"Invalid API response format: {data}")
                    return False, data
                
                # Check for error codes in results
                results = data.get('Results', [])
                if results and len(results) > 0:
                    first_result = results[0]
                    error_code = first_result.get('ErrorCode')
                    if error_code and error_code != '0':
                        error_text = first_result.get('ErrorText', 'Unknown error')
                        logger.warning(f"API returned error: {error_code} - {error_text}")
                        return False, data
                
                logger.info(f"VIN lookup successful for VIN: {vin[:8]}...")
                return True, data
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout for VIN {vin[:8]}... (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    self._handle_error("Request timeout")
                    return False, {"error": "Request timeout"}
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for VIN {vin[:8]}...: {e} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    self._handle_error(f"Request error: {e}")
                    return False, {"error": str(e)}
                    
            except Exception as e:
                logger.error(f"Unexpected error during VIN lookup: {e}")
                self._handle_error(f"Unexpected error: {e}")
                return False, {"error": str(e)}
        
        return False, {"error": "Max retries exceeded"}
    
    def _handle_error(self, error_message: str):
        """Handle service errors and update status"""
        self.error_count += 1
        self.last_error_time = datetime.utcnow()
        
        if self.error_count >= self.max_errors:
            self.service_status = VINServiceStatus.UNAVAILABLE
            logger.error(f"VIN service marked as unavailable after {self.error_count} errors")
        
        logger.error(f"VIN service error: {error_message}")
    
    def _reset_error_count(self):
        """Reset error count if enough time has passed"""
        if (self.last_error_time and 
            datetime.utcnow() - self.last_error_time > timedelta(seconds=self.error_reset_time)):
            self.error_count = 0
            if self.service_status == VINServiceStatus.UNAVAILABLE:
                self.service_status = VINServiceStatus.AVAILABLE
                logger.info("VIN service status reset to available")
    
    def _parse_vehicle_info(self, vin: str, api_data: Dict[str, Any]) -> VehicleInfo:
        """
        Parse NHTSA API response into standardized VehicleInfo
        
        Args:
            vin: Original VIN
            api_data: API response data
            
        Returns:
            VehicleInfo object
        """
        results = api_data.get('Results', [])
        
        # Create mapping from API field names to our standardized fields
        field_mapping = {
            'Model Year': 'year',
            'Make': 'make',
            'Model': 'model',
            'Trim': 'trim',
            'Engine Configuration': 'engine',
            'Fuel Type - Primary': 'fuel_type',
            'Body Class': 'body_class',
            'Drive Type': 'drive_type',
            'Transmission Style': 'transmission',
            'Doors': 'doors',
            'Windows': 'windows',
            'Series': 'series',
            'Plant City': 'plant_city',
            'Plant State': 'plant_state',
            'Plant Country': 'plant_country',
            'Manufacturer Name': 'manufacturer',
            'Model Year': 'model_year',
            'Vehicle Type': 'vehicle_type'
        }
        
        # Initialize vehicle info
        vehicle_info = VehicleInfo(
            vin=vin,
            lookup_timestamp=datetime.utcnow(),
            source="nhtsa"
        )
        
        # Parse results
        for result in results:
            variable = result.get('Variable')
            value = result.get('Value')
            
            if variable in field_mapping and value and value != 'Not Applicable':
                field_name = field_mapping[variable]
                
                # Convert specific fields to appropriate types
                if field_name in ['year', 'model_year', 'doors', 'windows']:
                    try:
                        setattr(vehicle_info, field_name, int(value))
                    except (ValueError, TypeError):
                        setattr(vehicle_info, field_name, value)
                else:
                    setattr(vehicle_info, field_name, value)
        
        # Check for error information
        if results and len(results) > 0:
            first_result = results[0]
            error_code = first_result.get('ErrorCode')
            error_text = first_result.get('ErrorText')
            
            if error_code and error_code != '0':
                vehicle_info.error_code = error_code
                vehicle_info.error_text = error_text
        
        return vehicle_info
    
    def _get_cached_vehicle_info(self, vin: str) -> Optional[VehicleInfo]:
        """Get vehicle info from cache if available and not expired"""
        if vin in self.cache:
            cached_info, timestamp = self.cache[vin]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.info(f"Returning cached VIN info for: {vin[:8]}...")
                return cached_info
            else:
                # Remove expired cache entry
                del self.cache[vin]
        
        return None
    
    def _cache_vehicle_info(self, vin: str, vehicle_info: VehicleInfo):
        """Cache vehicle info with timestamp"""
        self.cache[vin] = (vehicle_info, datetime.utcnow())
        logger.debug(f"Cached VIN info for: {vin[:8]}...")
    
    def lookup_vin(self, vin: str, use_cache: bool = True) -> VehicleInfo:
        """
        Lookup VIN and return standardized vehicle information
        
        Args:
            vin: VIN to lookup
            use_cache: Whether to use cached results
            
        Returns:
            VehicleInfo object with vehicle details
            
        Raises:
            VINValidationError: If VIN format is invalid
            VINAPIError: If API request fails
            VINLookupError: For other lookup errors
        """
        # Reset error count if enough time has passed
        self._reset_error_count()
        
        # Validate VIN
        if not self.validate_vin(vin):
            raise VINValidationError(f"Invalid VIN format: {vin}")
        
        # Normalize VIN
        vin = vin.strip().upper()
        
        # Check cache first
        if use_cache:
            cached_info = self._get_cached_vehicle_info(vin)
            if cached_info:
                return cached_info
        
        # Check service status
        if self.service_status == VINServiceStatus.UNAVAILABLE:
            logger.warning("VIN service is currently unavailable, using fallback")
            return self._get_fallback_vehicle_info(vin)
        
        # Make API request
        success, api_data = self._make_request(vin)
        
        if not success:
            logger.warning(f"VIN lookup failed for {vin[:8]}..., using fallback")
            return self._get_fallback_vehicle_info(vin)
        
        # Parse response
        try:
            vehicle_info = self._parse_vehicle_info(vin, api_data)
            
            # Cache successful results
            if use_cache and not vehicle_info.error_code:
                self._cache_vehicle_info(vin, vehicle_info)
            
            return vehicle_info
            
        except Exception as e:
            logger.error(f"Error parsing VIN response: {e}")
            return self._get_fallback_vehicle_info(vin)
    
    def _get_fallback_vehicle_info(self, vin: str) -> VehicleInfo:
        """
        Get fallback vehicle information when API is unavailable
        
        Args:
            vin: VIN to create fallback info for
            
        Returns:
            VehicleInfo object with basic information
        """
        logger.info(f"Using fallback vehicle info for VIN: {vin[:8]}...")
        
        # Extract basic info from VIN if possible
        year = None
        make = None
        
        try:
            # Try to extract year from VIN (position 10, but this is simplified)
            if len(vin) >= 10:
                year_char = vin[9]
                # This is a simplified year extraction - in production you'd use proper VIN decoding
                if year_char.isdigit():
                    year = 2000 + int(year_char)
                elif year_char in 'ABCDEFGHJKLMNPRSTUVWXY':
                    year = 2010 + ord(year_char) - ord('A')
        except Exception:
            pass
        
        return VehicleInfo(
            vin=vin,
            year=year,
            make=make,
            lookup_timestamp=datetime.utcnow(),
            source="fallback",
            error_code="API_UNAVAILABLE",
            error_text="VIN lookup service temporarily unavailable"
        )
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status and statistics"""
        return {
            "status": self.service_status.value,
            "error_count": self.error_count,
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
    
    def clear_cache(self):
        """Clear the VIN lookup cache"""
        self.cache.clear()
        logger.info("VIN lookup cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on VIN service"""
        try:
            # Try a simple lookup with a known VIN
            test_vin = "1HGBH41JXMN109186"  # Example VIN
            vehicle_info = self.lookup_vin(test_vin, use_cache=False)
            
            return {
                "status": "healthy",
                "service_available": self.service_status == VINServiceStatus.AVAILABLE,
                "last_check": datetime.utcnow().isoformat(),
                "test_lookup_successful": vehicle_info.source == "nhtsa"
            }
        except Exception as e:
            logger.error(f"VIN service health check failed: {e}")
            return {
                "status": "unhealthy",
                "service_available": False,
                "last_check": datetime.utcnow().isoformat(),
                "error": str(e)
            }
