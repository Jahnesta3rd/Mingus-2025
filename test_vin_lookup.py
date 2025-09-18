#!/usr/bin/env python3
"""
Test script for VIN Lookup Service
Tests the VIN lookup functionality with various scenarios
"""

import sys
import os
import logging
from datetime import datetime

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.vin_lookup_service import VINLookupService, VINValidationError, VINAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_vin_validation():
    """Test VIN validation functionality"""
    print("\n=== Testing VIN Validation ===")
    
    service = VINLookupService()
    
    # Test valid VINs
    valid_vins = [
        "1HGBH41JXMN109186",  # Honda
        "1FTFW1ET5DFC12345",  # Ford
        "1G1ZT53826F109149",  # Chevrolet
        "WBAFR9C50BC123456",  # BMW
        "1N4AL3AP8JC123456"   # Nissan
    ]
    
    # Test invalid VINs
    invalid_vins = [
        "1HGBH41JXMN10918",   # Too short
        "1HGBH41JXMN1091867", # Too long
        "1HGBH41JXMN10918I",  # Contains I
        "1HGBH41JXMN10918O",  # Contains O
        "1HGBH41JXMN10918Q",  # Contains Q
        "1HGBH41JXMN10918@",  # Contains special character
        "",                   # Empty
        None                  # None
    ]
    
    print("Testing valid VINs:")
    for vin in valid_vins:
        is_valid = service.validate_vin(vin)
        print(f"  {vin}: {'✓' if is_valid else '✗'}")
    
    print("\nTesting invalid VINs:")
    for vin in invalid_vins:
        is_valid = service.validate_vin(vin)
        print(f"  {vin}: {'✓' if is_valid else '✗'}")

def test_vin_lookup():
    """Test VIN lookup functionality"""
    print("\n=== Testing VIN Lookup ===")
    
    service = VINLookupService()
    
    # Test VINs (using real VINs that should work with NHTSA API)
    test_vins = [
        "1HGBH41JXMN109186",  # Honda Civic
        "1FTFW1ET5DFC12345",  # Ford F-150
        "1G1ZT53826F109149",  # Chevrolet Camaro
        "WBAFR9C50BC123456",  # BMW 3 Series
        "1N4AL3AP8JC123456"   # Nissan Altima
    ]
    
    for vin in test_vins:
        print(f"\nLooking up VIN: {vin}")
        try:
            vehicle_info = service.lookup_vin(vin)
            
            print(f"  Year: {vehicle_info.year}")
            print(f"  Make: {vehicle_info.make}")
            print(f"  Model: {vehicle_info.model}")
            print(f"  Trim: {vehicle_info.trim}")
            print(f"  Engine: {vehicle_info.engine}")
            print(f"  Fuel Type: {vehicle_info.fuel_type}")
            print(f"  Body Class: {vehicle_info.body_class}")
            print(f"  Drive Type: {vehicle_info.drive_type}")
            print(f"  Transmission: {vehicle_info.transmission}")
            print(f"  Doors: {vehicle_info.doors}")
            print(f"  Windows: {vehicle_info.windows}")
            print(f"  Series: {vehicle_info.series}")
            print(f"  Manufacturer: {vehicle_info.manufacturer}")
            print(f"  Vehicle Type: {vehicle_info.vehicle_type}")
            print(f"  Plant City: {vehicle_info.plant_city}")
            print(f"  Plant State: {vehicle_info.plant_state}")
            print(f"  Plant Country: {vehicle_info.plant_country}")
            print(f"  Source: {vehicle_info.source}")
            print(f"  Lookup Timestamp: {vehicle_info.lookup_timestamp}")
            
            if vehicle_info.error_code:
                print(f"  Error Code: {vehicle_info.error_code}")
                print(f"  Error Text: {vehicle_info.error_text}")
            
        except VINValidationError as e:
            print(f"  Validation Error: {e}")
        except VINAPIError as e:
            print(f"  API Error: {e}")
        except Exception as e:
            print(f"  Unexpected Error: {e}")

def test_error_handling():
    """Test error handling scenarios"""
    print("\n=== Testing Error Handling ===")
    
    service = VINLookupService()
    
    # Test with invalid VIN
    try:
        vehicle_info = service.lookup_vin("INVALID_VIN")
        print("  Invalid VIN test: Should have raised VINValidationError")
    except VINValidationError:
        print("  Invalid VIN test: ✓ Correctly raised VINValidationError")
    except Exception as e:
        print(f"  Invalid VIN test: ✗ Unexpected error: {e}")
    
    # Test with empty VIN
    try:
        vehicle_info = service.lookup_vin("")
        print("  Empty VIN test: Should have raised VINValidationError")
    except VINValidationError:
        print("  Empty VIN test: ✓ Correctly raised VINValidationError")
    except Exception as e:
        print(f"  Empty VIN test: ✗ Unexpected error: {e}")

def test_caching():
    """Test caching functionality"""
    print("\n=== Testing Caching ===")
    
    service = VINLookupService()
    test_vin = "1HGBH41JXMN109186"
    
    print(f"First lookup for VIN: {test_vin}")
    start_time = datetime.now()
    vehicle_info1 = service.lookup_vin(test_vin)
    first_lookup_time = (datetime.now() - start_time).total_seconds()
    print(f"  First lookup took: {first_lookup_time:.2f} seconds")
    
    print(f"Second lookup for VIN: {test_vin} (should use cache)")
    start_time = datetime.now()
    vehicle_info2 = service.lookup_vin(test_vin)
    second_lookup_time = (datetime.now() - start_time).total_seconds()
    print(f"  Second lookup took: {second_lookup_time:.2f} seconds")
    
    print(f"  Cache hit: {'✓' if second_lookup_time < first_lookup_time else '✗'}")
    print(f"  Same source: {'✓' if vehicle_info1.source == vehicle_info2.source else '✗'}")

def test_service_status():
    """Test service status and health check"""
    print("\n=== Testing Service Status ===")
    
    service = VINLookupService()
    
    # Get service status
    status = service.get_service_status()
    print("Service Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Perform health check
    health = service.health_check()
    print("\nHealth Check:")
    for key, value in health.items():
        print(f"  {key}: {value}")

def test_fallback():
    """Test fallback mechanism"""
    print("\n=== Testing Fallback Mechanism ===")
    
    # Create service with very short timeout to force fallback
    service = VINLookupService(timeout=0.1, max_retries=1)
    
    test_vin = "1HGBH41JXMN109186"
    print(f"Testing fallback with VIN: {test_vin}")
    
    try:
        vehicle_info = service.lookup_vin(test_vin)
        print(f"  Source: {vehicle_info.source}")
        print(f"  Error Code: {vehicle_info.error_code}")
        print(f"  Error Text: {vehicle_info.error_text}")
        print(f"  Fallback used: {'✓' if vehicle_info.source == 'fallback' else '✗'}")
    except Exception as e:
        print(f"  Error during fallback test: {e}")

def main():
    """Run all tests"""
    print("VIN Lookup Service Test Suite")
    print("=" * 50)
    
    try:
        test_vin_validation()
        test_vin_lookup()
        test_error_handling()
        test_caching()
        test_service_status()
        test_fallback()
        
        print("\n" + "=" * 50)
        print("All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
    except Exception as e:
        print(f"\n\nTest suite failed with error: {e}")
        logger.exception("Test suite error")

if __name__ == "__main__":
    main()
