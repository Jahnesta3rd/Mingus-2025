#!/usr/bin/env python3
"""
Test script for Mingus Article Library API
Tests the comprehensive Flask API endpoints for article library operations
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_endpoint(method, endpoint, data=None, headers=None, description=""):
    """Test an API endpoint and return the response"""
    url = f"{API_BASE}{endpoint}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"Description: {description}")
    print(f"{'='*60}")
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            print(f"❌ Unsupported method: {method}")
            return None
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response Body: {json.dumps(response_json, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response Body (raw): {response.text}")
        
        if response.status_code < 400:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return None

def main():
    """Main test function"""
    print("🚀 Starting Mingus Article Library API Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test 1: Health check
    test_endpoint('GET', '/health', description="Health check endpoint")
    
    # Test 2: Get available filters (public endpoint)
    test_endpoint('GET', '/articles/filters', description="Get available filter options")
    
    # Test 3: Get available topics (public endpoint)
    test_endpoint('GET', '/articles/topics', description="Get available topics and categories")
    
    # Test 4: Get trending articles (public endpoint)
    test_endpoint('GET', '/articles/trending?limit=5', description="Get trending articles")
    
    # Test 5: Get recent articles (public endpoint)
    test_endpoint('GET', '/articles/recent?limit=5', description="Get recently added articles")
    
    # Test 6: Get featured articles (public endpoint)
    test_endpoint('GET', '/articles/featured?limit=5', description="Get admin-featured articles")
    
    # Test 7: Get popular articles (public endpoint)
    test_endpoint('GET', '/articles/popular?limit=5', description="Get most read articles")
    
    # Test 8: Search suggestions (public endpoint)
    test_endpoint('GET', '/articles/autocomplete?q=financial', description="Get search suggestions")
    
    # Test 9: Advanced search (requires authentication)
    search_data = {
        "query": "financial planning",
        "filters": {
            "phase": "BE",
            "difficulty": "Beginner"
        },
        "page": 1,
        "per_page": 10
    }
    test_endpoint('POST', '/articles/search', data=search_data, description="Advanced search (requires auth)")
    
    # Test 9.1: Track search click (requires authentication)
    click_data = {
        "search_id": "test-search-id",
        "article_id": "test-article-id",
        "position": 1
    }
    test_endpoint('POST', '/articles/search/click', data=click_data, description="Track search click (requires auth)")
    
    # Test 10: Get articles by phase (requires authentication)
    test_endpoint('GET', '/articles/phases/BE?page=1&per_page=5', description="Get articles by BE phase (requires auth)")
    
    # Test 11: Get recommendations (requires authentication)
    test_endpoint('GET', '/articles/recommendations?limit=5', description="Get personalized recommendations (requires auth)")
    
    # Test 11.1: Get recommendations with explanations (requires authentication)
    test_endpoint('GET', '/articles/recommendations?limit=5&explanations=true', description="Get recommendations with explanations (requires auth)")
    
    # Test 12: List articles (requires authentication)
    test_endpoint('GET', '/articles/?page=1&per_page=5', description="List articles with filtering (requires auth)")
    
    # Test 13: Get user assessment (requires authentication)
    test_endpoint('GET', '/articles/user/assessment', description="Get user assessment with content access (requires auth)")
    
    # Test 14: Submit assessment (requires authentication)
    assessment_data = {
        "be_score": 75,
        "do_score": 60,
        "have_score": 45,
        "version": "1.0",
        "confidence_score": 0.85,
        "total_questions": 30,
        "completion_time_minutes": 15
    }
    test_endpoint('POST', '/articles/user/assessment', data=assessment_data, description="Submit assessment with recommendations (requires auth)")
    
    # Test 15: Test Input Validation - Invalid Assessment Scores
    invalid_assessment_data = {
        "be_score": 150,  # Invalid: > 100
        "do_score": 80,
        "have_score": 70
    }
    test_endpoint('POST', '/articles/user/assessment', data=invalid_assessment_data, description="Test validation - Invalid assessment scores (should return 400)")
    
    # Test 16: Test Input Validation - Invalid Rating
    invalid_rating_data = {
        "overall_rating": 6  # Invalid: > 5
    }
    test_endpoint('POST', '/articles/test-article-id/rating', data=invalid_rating_data, description="Test validation - Invalid rating (should return 400)")
    
    # Test 17: Test Input Validation - Invalid Pagination
    test_endpoint('GET', '/articles/?page=0&per_page=200', description="Test validation - Invalid pagination (should return 400)")
    
    # Test 18: Test Input Validation - Invalid JSON
    test_endpoint('POST', '/articles/search', data="invalid json", description="Test validation - Invalid JSON (should return 400)")
    
    print(f"\n{'='*60}")
    print("🎯 Test Summary")
    print(f"{'='*60}")
    print("✅ Public endpoints should work without authentication")
    print("❌ Authenticated endpoints will return 401 (expected)")
    print("✅ Validation tests should return 400 for invalid input")
    print("\nTo test authenticated endpoints:")
    print("1. Register/login to get a session")
    print("2. Include session cookies in requests")
    print("3. Or implement JWT token authentication")
    
    print(f"\n📊 Test completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
