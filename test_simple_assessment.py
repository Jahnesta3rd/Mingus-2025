#!/usr/bin/env python3
"""
Simple test to check assessment endpoints without security decorators
"""

import requests
import json

def test_simple_endpoints():
    """Test endpoints with minimal data"""
    
    base_url = "http://localhost:5000"
    
    print("Testing Simple Assessment Endpoints...")
    print("=" * 50)
    
    # Test 1: Available assessments endpoint
    try:
        response = requests.get(f"{base_url}/api/assessments/available")
        print(f"GET /api/assessments/available")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print("-" * 30)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Simple POST to submit endpoint
    try:
        test_data = {
            "responses": {
                "test_question": "test_answer"
            }
        }
        response = requests.post(
            f"{base_url}/api/assessments/income-comparison/submit",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"POST /api/assessments/income-comparison/submit")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print("-" * 30)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Check if Flask app is running
    try:
        response = requests.get(f"{base_url}/")
        print(f"GET / (root endpoint)")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print("-" * 30)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple_endpoints()
