#!/usr/bin/env python3
"""
Simple test for Daily Outlook API endpoints

This script tests the Daily Outlook API endpoints by importing
and checking the basic structure without running a full server.
"""

import sys
import os
import json
from datetime import datetime, date, timedelta

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

def test_basic_imports():
    """Test basic imports"""
    print("=== Testing Basic Imports ===\n")
    
    try:
        # Test Flask imports
        from flask import Flask, Blueprint
        print("✅ Flask imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Flask: {e}")
        return False
    
    try:
        # Test marshmallow imports
        from marshmallow import Schema, fields, validate
        print("✅ Marshmallow imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Marshmallow: {e}")
        return False
    
    return True

def test_api_file_structure():
    """Test that the API file exists and has the right structure"""
    print("\n=== Testing API File Structure ===\n")
    
    api_file_path = os.path.join(os.path.dirname(__file__), 'daily_outlook_api.py')
    
    if not os.path.exists(api_file_path):
        print(f"❌ API file not found at: {api_file_path}")
        return False
    
    print(f"✅ API file exists at: {api_file_path}")
    
    # Read and check the file content
    try:
        with open(api_file_path, 'r') as f:
            content = f.read()
        
        # Check for key components
        required_components = [
            'daily_outlook_api = Blueprint',
            '@daily_outlook_api.route',
            'def get_todays_outlook',
            'def get_outlook_history',
            'def mark_action_completed',
            'def submit_rating',
            'def get_streak_info',
            'def update_relationship_status'
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing components: {missing_components}")
            return False
        else:
            print("✅ All required components found in API file")
        
        # Count endpoints
        endpoint_count = content.count('@daily_outlook_api.route')
        print(f"✅ Found {endpoint_count} API endpoints")
        
        # Check for proper imports
        import_checks = [
            'from flask import Blueprint',
            'from backend.models.daily_outlook import',
            'from backend.auth.decorators import',
            'from marshmallow import Schema'
        ]
        
        missing_imports = []
        for import_check in import_checks:
            if import_check not in content:
                missing_imports.append(import_check)
        
        if missing_imports:
            print(f"❌ Missing imports: {missing_imports}")
            return False
        else:
            print("✅ All required imports found")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to read API file: {e}")
        return False

def test_endpoint_definitions():
    """Test endpoint definitions by parsing the file"""
    print("\n=== Testing Endpoint Definitions ===\n")
    
    api_file_path = os.path.join(os.path.dirname(__file__), 'daily_outlook_api.py')
    
    try:
        with open(api_file_path, 'r') as f:
            content = f.read()
        
        # Expected endpoints (using relative paths as defined in the API)
        expected_endpoints = [
            ("GET", "/", "get_todays_outlook"),
            ("GET", "/history", "get_outlook_history"),
            ("POST", "/action-completed", "mark_action_completed"),
            ("POST", "/rating", "submit_rating"),
            ("GET", "/streak", "get_streak_info"),
            ("POST", "/relationship-status", "update_relationship_status")
        ]
        
        found_endpoints = []
        
        for method, route, function_name in expected_endpoints:
            # Check for route decorator
            route_pattern = f"@daily_outlook_api.route('{route}', methods=['{method}'])"
            if route_pattern in content:
                found_endpoints.append((method, route, function_name))
                print(f"✅ Found endpoint: {method} {route} -> {function_name}")
            else:
                print(f"❌ Missing endpoint: {method} {route} -> {function_name}")
        
        print(f"\nFound {len(found_endpoints)}/{len(expected_endpoints)} expected endpoints")
        
        if len(found_endpoints) == len(expected_endpoints):
            print("✅ All expected endpoints are defined")
            return True
        else:
            print("❌ Some endpoints are missing")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test endpoint definitions: {e}")
        return False

def test_validation_schemas():
    """Test validation schemas by parsing the file"""
    print("\n=== Testing Validation Schemas ===\n")
    
    api_file_path = os.path.join(os.path.dirname(__file__), 'daily_outlook_api.py')
    
    try:
        with open(api_file_path, 'r') as f:
            content = f.read()
        
        # Expected schemas
        expected_schemas = [
            "ActionCompletedSchema",
            "RatingSchema", 
            "RelationshipStatusSchema",
            "HistoryQuerySchema"
        ]
        
        found_schemas = []
        
        for schema_name in expected_schemas:
            if f"class {schema_name}(Schema):" in content:
                found_schemas.append(schema_name)
                print(f"✅ Found schema: {schema_name}")
            else:
                print(f"❌ Missing schema: {schema_name}")
        
        print(f"\nFound {len(found_schemas)}/{len(expected_schemas)} expected schemas")
        
        if len(found_schemas) == len(expected_schemas):
            print("✅ All expected schemas are defined")
            return True
        else:
            print("❌ Some schemas are missing")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test validation schemas: {e}")
        return False

def test_authentication_decorators():
    """Test authentication decorators"""
    print("\n=== Testing Authentication Decorators ===\n")
    
    api_file_path = os.path.join(os.path.dirname(__file__), 'daily_outlook_api.py')
    
    try:
        with open(api_file_path, 'r') as f:
            content = f.read()
        
        # Check for authentication decorators
        auth_checks = [
            "@require_auth",
            "@require_csrf",
            "get_current_user_id"
        ]
        
        found_auth = []
        
        for auth_check in auth_checks:
            if auth_check in content:
                found_auth.append(auth_check)
                print(f"✅ Found authentication: {auth_check}")
            else:
                print(f"❌ Missing authentication: {auth_check}")
        
        print(f"\nFound {len(found_auth)}/{len(auth_checks)} authentication components")
        
        if len(found_auth) == len(auth_checks):
            print("✅ All authentication components are present")
            return True
        else:
            print("❌ Some authentication components are missing")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test authentication decorators: {e}")
        return False

def test_error_handling():
    """Test error handling patterns"""
    print("\n=== Testing Error Handling ===\n")
    
    api_file_path = os.path.join(os.path.dirname(__file__), 'daily_outlook_api.py')
    
    try:
        with open(api_file_path, 'r') as f:
            content = f.read()
        
        # Check for error handling patterns
        error_patterns = [
            "try:",
            "except Exception as e:",
            "logger.error",
            "return jsonify",
            "status_code"
        ]
        
        found_patterns = []
        
        for pattern in error_patterns:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"✅ Found error handling: {pattern}")
            else:
                print(f"❌ Missing error handling: {pattern}")
        
        print(f"\nFound {len(found_patterns)}/{len(error_patterns)} error handling patterns")
        
        if len(found_patterns) >= len(error_patterns) - 1:  # Allow for some flexibility
            print("✅ Good error handling patterns found")
            return True
        else:
            print("❌ Insufficient error handling patterns")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test error handling: {e}")
        return False

def test_documentation():
    """Test documentation and comments"""
    print("\n=== Testing Documentation ===\n")
    
    api_file_path = os.path.join(os.path.dirname(__file__), 'daily_outlook_api.py')
    
    try:
        with open(api_file_path, 'r') as f:
            content = f.read()
        
        # Check for documentation patterns
        doc_patterns = [
            '"""',
            "REST API endpoints",
            "Authentication",
            "Validation",
            "Error handling"
        ]
        
        found_docs = []
        
        for pattern in doc_patterns:
            if pattern in content:
                found_docs.append(pattern)
                print(f"✅ Found documentation: {pattern}")
            else:
                print(f"❌ Missing documentation: {pattern}")
        
        print(f"\nFound {len(found_docs)}/{len(doc_patterns)} documentation patterns")
        
        if len(found_docs) >= len(doc_patterns) - 1:
            print("✅ Good documentation found")
            return True
        else:
            print("❌ Insufficient documentation")
            return False
        
    except Exception as e:
        print(f"❌ Failed to test documentation: {e}")
        return False

def main():
    """Run all tests"""
    print("Daily Outlook API Structure Test")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("API File Structure", test_api_file_structure),
        ("Endpoint Definitions", test_endpoint_definitions),
        ("Validation Schemas", test_validation_schemas),
        ("Authentication Decorators", test_authentication_decorators),
        ("Error Handling", test_error_handling),
        ("Documentation", test_documentation)
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
        print("🎉 All tests passed! Daily Outlook API structure is correct.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
