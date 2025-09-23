#!/usr/bin/env python3
"""
Simple test script for Daily Outlook API endpoints

This script tests the Daily Outlook API endpoints without requiring
a full test framework setup.
"""

import sys
import os
import json
from datetime import datetime, date, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test that all required modules can be imported"""
    print("=== Testing Imports ===\n")
    
    try:
        # Test database import
        from models.database import db
        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import database module: {e}")
        return False
    
    try:
        # Test daily outlook models
        from models.daily_outlook import DailyOutlook, UserRelationshipStatus, RelationshipStatus
        print("✅ Daily outlook models imported successfully")
        print(f"   - DailyOutlook: {DailyOutlook.__name__}")
        print(f"   - UserRelationshipStatus: {UserRelationshipStatus.__name__}")
        print(f"   - RelationshipStatus: {RelationshipStatus.__name__}")
    except Exception as e:
        print(f"❌ Failed to import daily outlook models: {e}")
        return False
    
    try:
        # Test user models
        from models.user_models import User
        print("✅ User models imported successfully")
    except Exception as e:
        print(f"❌ Failed to import user models: {e}")
        return False
    
    try:
        # Test authentication decorators
        from auth.decorators import require_auth, require_csrf, get_current_user_id
        print("✅ Authentication decorators imported successfully")
    except Exception as e:
        print(f"❌ Failed to import authentication decorators: {e}")
        return False
    
    try:
        # Test validation utilities
        from utils.validation import APIValidator
        print("✅ Validation utilities imported successfully")
    except Exception as e:
        print(f"❌ Failed to import validation utilities: {e}")
        return False
    
    try:
        # Test feature flag service
        from services.feature_flag_service import FeatureFlagService, FeatureTier, FeatureFlag
        print("✅ Feature flag service imported successfully")
    except Exception as e:
        print(f"❌ Failed to import feature flag service: {e}")
        return False
    
    return True

def test_api_structure():
    """Test the API structure and endpoints"""
    print("\n=== Testing API Structure ===\n")
    
    try:
        # Import the daily outlook API
        from api.daily_outlook_api import daily_outlook_api
        print("✅ Daily outlook API imported successfully")
        print(f"   Blueprint name: {daily_outlook_api.name}")
        print(f"   URL prefix: {daily_outlook_api.url_prefix}")
        
        # Check if the blueprint has the expected routes
        routes = []
        for rule in daily_outlook_api.url_map.iter_rules():
            if rule.endpoint.startswith('daily_outlook_api.'):
                routes.append(f"{rule.methods} {rule.rule}")
        
        print(f"   Registered routes: {len(routes)}")
        for route in routes:
            print(f"     {route}")
        
    except Exception as e:
        print(f"❌ Failed to import daily outlook API: {e}")
        return False
    
    return True

def test_validation_schemas():
    """Test validation schemas"""
    print("\n=== Testing Validation Schemas ===\n")
    
    try:
        from api.daily_outlook_api import (
            ActionCompletedSchema, RatingSchema, RelationshipStatusSchema, HistoryQuerySchema
        )
        print("✅ Validation schemas imported successfully")
        
        # Test ActionCompletedSchema
        schema = ActionCompletedSchema()
        test_data = {
            'action_id': 'test_action',
            'completion_status': True,
            'completion_notes': 'Test notes'
        }
        result = schema.load(test_data)
        print(f"   ✅ ActionCompletedSchema validation passed: {result}")
        
        # Test RatingSchema
        rating_schema = RatingSchema()
        rating_data = {
            'rating': 4,
            'feedback': 'Great insights!'
        }
        rating_result = rating_schema.load(rating_data)
        print(f"   ✅ RatingSchema validation passed: {rating_result}")
        
        # Test RelationshipStatusSchema
        relationship_schema = RelationshipStatusSchema()
        relationship_data = {
            'status': 'dating',
            'satisfaction_score': 8,
            'financial_impact_score': 6
        }
        relationship_result = relationship_schema.load(relationship_data)
        print(f"   ✅ RelationshipStatusSchema validation passed: {relationship_result}")
        
    except Exception as e:
        print(f"❌ Failed to test validation schemas: {e}")
        return False
    
    return True

def test_utility_functions():
    """Test utility functions"""
    print("\n=== Testing Utility Functions ===\n")
    
    try:
        from api.daily_outlook_api import (
            check_user_tier_access, validate_request_data, calculate_streak_count, update_user_relationship_status
        )
        print("✅ Utility functions imported successfully")
        
        # Test validate_request_data function
        from api.daily_outlook_api import ActionCompletedSchema
        test_data = {
            'action_id': 'test_action',
            'completion_status': True
        }
        is_valid, errors, validated_data = validate_request_data(ActionCompletedSchema, test_data)
        print(f"   ✅ validate_request_data test passed: {is_valid}")
        if not is_valid:
            print(f"     Errors: {errors}")
        
    except Exception as e:
        print(f"❌ Failed to test utility functions: {e}")
        return False
    
    return True

def test_api_registration():
    """Test API registration"""
    print("\n=== Testing API Registration ===\n")
    
    try:
        from api import API_BLUEPRINTS
        print("✅ API blueprints imported successfully")
        
        # Check if daily_outlook_api is in the list
        from api.daily_outlook_api import daily_outlook_api
        if daily_outlook_api in API_BLUEPRINTS:
            print("✅ Daily outlook API is registered in API_BLUEPRINTS")
        else:
            print("❌ Daily outlook API is NOT registered in API_BLUEPRINTS")
            return False
        
        print(f"   Total registered APIs: {len(API_BLUEPRINTS)}")
        
    except Exception as e:
        print(f"❌ Failed to test API registration: {e}")
        return False
    
    return True

def test_endpoint_definitions():
    """Test that all expected endpoints are defined"""
    print("\n=== Testing Endpoint Definitions ===\n")
    
    try:
        from api.daily_outlook_api import daily_outlook_api
        
        # Get all routes from the blueprint
        routes = []
        for rule in daily_outlook_api.url_map.iter_rules():
            if rule.endpoint.startswith('daily_outlook_api.'):
                routes.append((rule.rule, rule.methods, rule.endpoint))
        
        expected_endpoints = [
            ('/api/daily-outlook/', 'GET', 'daily_outlook_api.get_todays_outlook'),
            ('/api/daily-outlook/history', 'GET', 'daily_outlook_api.get_outlook_history'),
            ('/api/daily-outlook/action-completed', 'POST', 'daily_outlook_api.mark_action_completed'),
            ('/api/daily-outlook/rating', 'POST', 'daily_outlook_api.submit_rating'),
            ('/api/daily-outlook/streak', 'GET', 'daily_outlook_api.get_streak_info'),
            ('/api/relationship-status', 'POST', 'daily_outlook_api.update_relationship_status')
        ]
        
        print(f"Found {len(routes)} routes in daily outlook API:")
        for route, methods, endpoint in routes:
            print(f"   {list(methods)} {route} -> {endpoint}")
        
        # Check if expected endpoints exist
        found_endpoints = []
        for route, methods, endpoint in routes:
            for expected_route, expected_method, expected_endpoint in expected_endpoints:
                if route == expected_route and expected_method in methods:
                    found_endpoints.append((route, expected_method, expected_endpoint))
                    print(f"   ✅ Found expected endpoint: {expected_method} {route}")
        
        print(f"\nFound {len(found_endpoints)}/{len(expected_endpoints)} expected endpoints")
        
        if len(found_endpoints) == len(expected_endpoints):
            print("✅ All expected endpoints are defined")
            return True
        else:
            print("❌ Some expected endpoints are missing")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test endpoint definitions: {e}")
        return False

def main():
    """Run all tests"""
    print("Daily Outlook API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("API Structure Tests", test_api_structure),
        ("Validation Schema Tests", test_validation_schemas),
        ("Utility Function Tests", test_utility_functions),
        ("API Registration Tests", test_api_registration),
        ("Endpoint Definition Tests", test_endpoint_definitions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Daily Outlook API is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
