#!/usr/bin/env python3
"""
VIN Lookup Service Example
Demonstrates how to use the VIN lookup service in the Mingus Flask application
"""

import sys
import os
import json
from datetime import datetime

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.vin_lookup_service import VINLookupService, VINValidationError, VINAPIError

def example_vin_lookup():
    """Example of using the VIN lookup service"""
    print("VIN Lookup Service Example")
    print("=" * 50)
    
    # Initialize the service
    vin_service = VINLookupService()
    
    # Example VINs to lookup
    example_vins = [
        "1HGBH41JXMN109186",  # Honda Civic
        "1FTFW1ET5DFC12345",  # Ford F-150
        "WBAFR9C50BC123456",  # BMW 5 Series
    ]
    
    for vin in example_vins:
        print(f"\nLooking up VIN: {vin}")
        print("-" * 30)
        
        try:
            # Lookup the VIN
            vehicle_info = vin_service.lookup_vin(vin)
            
            # Display the results
            print(f"Make: {vehicle_info.make}")
            print(f"Model: {vehicle_info.model}")
            print(f"Year: {vehicle_info.year}")
            print(f"Trim: {vehicle_info.trim}")
            print(f"Engine: {vehicle_info.engine}")
            print(f"Fuel Type: {vehicle_info.fuel_type}")
            print(f"Body Class: {vehicle_info.body_class}")
            print(f"Drive Type: {vehicle_info.drive_type}")
            print(f"Transmission: {vehicle_info.transmission}")
            print(f"Doors: {vehicle_info.doors}")
            print(f"Windows: {vehicle_info.windows}")
            print(f"Series: {vehicle_info.series}")
            print(f"Manufacturer: {vehicle_info.manufacturer}")
            print(f"Vehicle Type: {vehicle_info.vehicle_type}")
            print(f"Plant City: {vehicle_info.plant_city}")
            print(f"Plant State: {vehicle_info.plant_state}")
            print(f"Plant Country: {vehicle_info.plant_country}")
            print(f"Source: {vehicle_info.source}")
            print(f"Lookup Time: {vehicle_info.lookup_timestamp}")
            
            if vehicle_info.error_code:
                print(f"Error Code: {vehicle_info.error_code}")
                print(f"Error Text: {vehicle_info.error_text}")
            
        except VINValidationError as e:
            print(f"Validation Error: {e}")
        except VINAPIError as e:
            print(f"API Error: {e}")
        except Exception as e:
            print(f"Unexpected Error: {e}")

def example_api_usage():
    """Example of using the VIN lookup via API endpoints"""
    print("\n\nAPI Usage Example")
    print("=" * 50)
    
    print("To use the VIN lookup service via API endpoints:")
    print("\n1. VIN Lookup:")
    print("   POST /api/vehicles/vin-lookup")
    print("   Body: {\"vin\": \"1HGBH41JXMN109186\"}")
    
    print("\n2. VIN Validation:")
    print("   POST /api/vehicles/vin-lookup/validate")
    print("   Body: {\"vin\": \"1HGBH41JXMN109186\"}")
    
    print("\n3. Service Status:")
    print("   GET /api/vehicles/vin-lookup/status")
    
    print("\n4. Health Check:")
    print("   GET /api/vehicles/vin-lookup/health")
    
    print("\n5. Clear Cache:")
    print("   POST /api/vehicles/vin-lookup/cache/clear")
    
    print("\nExample cURL commands:")
    print("\n# Lookup VIN")
    print('curl -X POST http://localhost:5000/api/vehicles/vin-lookup \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"vin": "1HGBH41JXMN109186"}\'')
    
    print("\n# Validate VIN")
    print('curl -X POST http://localhost:5000/api/vehicles/vin-lookup/validate \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"vin": "1HGBH41JXMN109186"}\'')
    
    print("\n# Get service status")
    print('curl -X GET http://localhost:5000/api/vehicles/vin-lookup/status')

def example_error_handling():
    """Example of error handling scenarios"""
    print("\n\nError Handling Example")
    print("=" * 50)
    
    vin_service = VINLookupService()
    
    # Test invalid VIN
    print("Testing invalid VIN:")
    try:
        vehicle_info = vin_service.lookup_vin("INVALID_VIN")
        print("Unexpected: Should have raised an error")
    except VINValidationError as e:
        print(f"✓ Correctly caught validation error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test empty VIN
    print("\nTesting empty VIN:")
    try:
        vehicle_info = vin_service.lookup_vin("")
        print("Unexpected: Should have raised an error")
    except VINValidationError as e:
        print(f"✓ Correctly caught validation error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

def example_service_management():
    """Example of service management functions"""
    print("\n\nService Management Example")
    print("=" * 50)
    
    vin_service = VINLookupService()
    
    # Get service status
    print("Service Status:")
    status = vin_service.get_service_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Perform health check
    print("\nHealth Check:")
    health = vin_service.health_check()
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    # Clear cache
    print("\nClearing cache...")
    vin_service.clear_cache()
    print("✓ Cache cleared")

if __name__ == "__main__":
    try:
        example_vin_lookup()
        example_api_usage()
        example_error_handling()
        example_service_management()
        
        print("\n" + "=" * 50)
        print("Example completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\n\nExample failed with error: {e}")
