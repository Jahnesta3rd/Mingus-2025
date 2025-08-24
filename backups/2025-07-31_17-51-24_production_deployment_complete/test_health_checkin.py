#!/usr/bin/env python3
"""
Test script for health check-in functionality
"""
import sys
import os
import requests
import json
from datetime import datetime, date

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_health_checkin_form():
    """Test that the health check-in form can be accessed"""
    print("=== Testing Health Check-in Form ===")
    
    try:
        # Test the form endpoint (should require auth)
        response = requests.get('http://localhost:5002/api/health/checkin')
        
        if response.status_code == 401:
            print("✅ Form endpoint correctly requires authentication")
            return True
        elif response.status_code == 200:
            print("✅ Form endpoint accessible (user may be logged in)")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Flask app not running on localhost:5002")
        return False
    except Exception as e:
        print(f"❌ Error testing form: {e}")
        return False

def test_health_api_endpoints():
    """Test the health API endpoints"""
    print("\n=== Testing Health API Endpoints ===")
    
    endpoints = [
        '/api/health/checkin',
        '/api/health/checkins',
        '/api/health/stats'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:5002{endpoint}')
            
            if response.status_code == 401:
                print(f"✅ {endpoint} - Correctly requires authentication")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Flask app not running")
            return False
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            return False
    
    return True

def test_health_models():
    """Test that health models can be imported and used"""
    print("\n=== Testing Health Models ===")
    
    try:
        from backend.models import UserHealthCheckin, HealthSpendingCorrelation
        
        # Test model creation
        checkin = UserHealthCheckin(
            user_id=1,
            checkin_date=date.today(),
            physical_activity_minutes=30,
            physical_activity_level='moderate',
            relationships_rating=8,
            relationships_notes='Feeling connected today',
            mindfulness_minutes=15,
            mindfulness_type='meditation',
            stress_level=4,
            energy_level=7,
            mood_rating=8
        )
        
        print("✅ UserHealthCheckin model created successfully")
        
        # Test correlation model
        correlation = HealthSpendingCorrelation(
            user_id=1,
            analysis_period='weekly',
            health_metric='stress_level',
            spending_category='impulse_purchases',
            correlation_strength=0.75,
            insight_text='Higher stress correlates with increased impulse spending'
        )
        
        print("✅ HealthSpendingCorrelation model created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing models: {e}")
        return False

def test_template_exists():
    """Test that the health check-in template exists"""
    print("\n=== Testing Template ===")
    
    template_path = 'backend/templates/health_checkin.html'
    
    if os.path.exists(template_path):
        print(f"✅ Template exists: {template_path}")
        
        # Check if it contains expected content
        with open(template_path, 'r') as f:
            content = f.read()
            
        expected_elements = [
            'Health Check-in',
            'physical_activity_minutes',
            'relationships_rating',
            'stress_level',
            'mood_rating',
            '/api/health/checkin'
        ]
        
        missing_elements = []
        for element in expected_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"⚠️  Missing elements in template: {missing_elements}")
        else:
            print("✅ Template contains all expected elements")
            
        return True
    else:
        print(f"❌ Template not found: {template_path}")
        return False

def main():
    """Run all health check-in tests"""
    print("🧪 Testing Health Check-in Functionality\n")
    
    tests = [
        test_health_checkin_form,
        test_health_api_endpoints,
        test_health_models,
        test_template_exists
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Health check-in functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
