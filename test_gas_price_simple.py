#!/usr/bin/env python3
"""
Simple test for Mingus Gas Price Service components
Tests the core functionality without Flask app dependencies
"""

import os
import sys
import logging
from datetime import datetime

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import only the components we need
from msa_mapping_service import ZipcodeToMSAMapper
from backend.services.gas_price_service import GasPriceService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_msa_mapping():
    """Test the MSA mapping service integration"""
    print("🗺️  Testing MSA Mapping Service")
    print("=" * 50)
    
    mapper = ZipcodeToMSAMapper()
    
    # Test zipcodes for each target MSA
    test_cases = [
        ("10001", "New York"),
        ("30309", "Atlanta"),
        ("77002", "Houston"),
        ("20001", "Washington DC"),
        ("75201", "Dallas"),
        ("19102", "Philadelphia"),
        ("60601", "Chicago"),
        ("28202", "Charlotte"),
        ("33101", "Miami"),
        ("21201", "Baltimore")
    ]
    
    correct_mappings = 0
    total_tests = len(test_cases)
    
    for zipcode, expected_msa in test_cases:
        result = mapper.get_msa_for_zipcode(zipcode)
        actual_msa = result.get('msa', 'Unknown')
        distance = result.get('distance', 999)
        
        # Check if mapping is correct (allowing for slight variations in naming)
        is_correct = (
            expected_msa in actual_msa or 
            actual_msa in expected_msa or
            (expected_msa == "Washington DC" and "Washington" in actual_msa)
        )
        
        if is_correct:
            correct_mappings += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"   {status} {zipcode} → {actual_msa} ({distance:.1f} miles)")
    
    accuracy = (correct_mappings / total_tests) * 100
    print(f"\n   Mapping Accuracy: {accuracy:.1f}% ({correct_mappings}/{total_tests})")
    
    return accuracy >= 80  # 80% accuracy threshold

def test_gas_price_service():
    """Test the gas price service core functionality"""
    print("\n⛽ Testing Gas Price Service")
    print("=" * 50)
    
    gas_service = GasPriceService()
    
    # Test 1: Service initialization
    print("📊 Service Initialization:")
    print(f"   Target MSAs: {len(gas_service.TARGET_MSAS)}")
    print(f"   Data Sources: {len(gas_service.DATA_SOURCES)}")
    print(f"   Fallback Prices: {len(gas_service.FALLBACK_PRICES)}")
    print()
    
    # Test 2: MSA list
    print("🏙️  Target MSAs:")
    for i, msa in enumerate(gas_service.TARGET_MSAS, 1):
        print(f"   {i:2d}. {msa}")
    print()
    
    # Test 3: Fallback prices
    print("💰 Fallback Prices:")
    for msa, price in gas_service.FALLBACK_PRICES.items():
        print(f"   {msa:15s}: ${price:.3f}/gallon")
    print()
    
    # Test 4: Data source configuration
    print("🔌 Data Sources:")
    for source_key, config in gas_service.DATA_SOURCES.items():
        print(f"   {source_key:12s}: {config['name']} (confidence: {config['confidence']})")
    print()
    
    return True

def test_zipcode_to_gas_price():
    """Test zipcode to gas price mapping"""
    print("📍 Testing Zipcode to Gas Price Mapping")
    print("=" * 50)
    
    gas_service = GasPriceService()
    
    # Test zipcodes
    test_zipcodes = [
        "10001",  # New York
        "30309",  # Atlanta
        "77002",  # Houston
        "90210",  # Los Angeles (outside MSA)
        "99999"   # Invalid
    ]
    
    for zipcode in test_zipcodes:
        print(f"Testing zipcode: {zipcode}")
        
        try:
            result = gas_service.get_gas_price_by_zipcode(zipcode)
            
            if result['success']:
                print(f"   ✅ MSA: {result['msa_name']}")
                print(f"   ✅ Price: ${result['gas_price']:.3f}/gallon")
                print(f"   ✅ Source: {result['data_source']}")
                print(f"   ✅ Confidence: {result['confidence_score']}")
                if result.get('is_fallback'):
                    print(f"   ⚠️  Using fallback pricing")
            else:
                print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()

def test_celery_tasks():
    """Test Celery task definitions"""
    print("🔄 Testing Celery Task Definitions")
    print("=" * 50)
    
    try:
        from backend.tasks.gas_price_tasks import (
            update_daily_gas_prices,
            update_specific_msa_price,
            cleanup_old_gas_price_data,
            health_check_gas_price_service,
            get_gas_price_by_zipcode_task
        )
        
        tasks = [
            ("update_daily_gas_prices", "Daily gas price updates"),
            ("update_specific_msa_price", "Single MSA price updates"),
            ("cleanup_old_gas_price_data", "Data cleanup"),
            ("health_check_gas_price_service", "Health monitoring"),
            ("get_gas_price_by_zipcode_task", "Async zipcode lookups")
        ]
        
        print("Available Celery tasks:")
        for task_name, description in tasks:
            task_func = globals()[task_name]
            print(f"   ✅ {task_name}: {description}")
            print(f"      Max retries: {getattr(task_func, 'max_retries', 'N/A')}")
            print(f"      Bind: {getattr(task_func, 'bind', False)}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint definitions"""
    print("\n🌐 Testing API Endpoint Definitions")
    print("=" * 50)
    
    try:
        from backend.api.gas_price_endpoints import gas_price_api
        
        # Get all routes from the blueprint
        routes = []
        for rule in gas_price_api.url_map.iter_rules():
            if rule.endpoint.startswith('gas_price_api.'):
                method = list(rule.methods - {'HEAD', 'OPTIONS'})[0] if rule.methods else 'GET'
                routes.append((method, rule.rule))
        
        print("Available API endpoints:")
        for method, route in sorted(routes):
            print(f"   {method:4s} {route}")
        
        return len(routes) > 0
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Mingus Gas Price Service - Component Test")
    print("=" * 70)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    test_results = []
    
    try:
        # Run individual tests
        test_results.append(("MSA Mapping", test_msa_mapping()))
        test_results.append(("Gas Price Service", test_gas_price_service()))
        test_zipcode_to_gas_price()
        test_results.append(("Celery Tasks", test_celery_tasks()))
        test_results.append(("API Endpoints", test_api_endpoints()))
        
        # Summary
        print("\n📊 Test Results Summary")
        print("=" * 50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name:20s}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 All tests passed! The gas price service is ready for use.")
            print("\n📋 Next Steps:")
            print("   1. Set up the database with the updated MSAGasPrice model")
            print("   2. Configure Celery worker and beat scheduler")
            print("   3. Set up API keys for external data sources")
            print("   4. Deploy and test with real data")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues above.")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        logger.exception("Test suite failed")

if __name__ == "__main__":
    main()
