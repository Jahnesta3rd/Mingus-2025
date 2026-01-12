#!/usr/bin/env python3
"""
Direct test of validation fixes for the 9 warnings
Tests the validation functions directly without needing the server
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.validation import APIValidator

def test_type_validation():
    """Test the 6 type validation cases"""
    print("\n" + "="*70)
    print("TESTING TYPE VALIDATION (6 tests)")
    print("="*70)
    
    test_cases = [
        {'email': 123, 'description': 'Email as integer'},
        {'email': [], 'description': 'Email as list'},
        {'email': {}, 'description': 'Email as dictionary'},
        {'age': 'not_a_number', 'description': 'Age as string (unknown field)'},
        {'age': -1, 'description': 'Negative age (unknown field)'},
        {'age': 1000, 'description': 'Too large age (unknown field)'},
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        description = test_case.pop('description')
        data = test_case.copy()
        
        # Add required fields for assessment validation
        if 'email' not in data:
            data['email'] = 'test@example.com'
        if 'assessmentType' not in data:
            data['assessmentType'] = 'ai-risk'
        if 'answers' not in data:
            data['answers'] = {}
        
        is_valid, errors, sanitized_data = APIValidator.validate_assessment_data(data)
        
        if not is_valid and len(errors) > 0:
            print(f"✅ Test {i}: {description}")
            print(f"   Status: REJECTED (as expected)")
            print(f"   Errors: {errors[0] if errors else 'None'}")
            passed += 1
        else:
            print(f"❌ Test {i}: {description}")
            print(f"   Status: ACCEPTED (should be rejected!)")
            print(f"   Errors: {errors}")
            failed += 1
        print()
    
    return passed, failed

def test_length_validation():
    """Test the 3 length validation cases"""
    print("\n" + "="*70)
    print("TESTING LENGTH VALIDATION (3 tests)")
    print("="*70)
    
    test_cases = [
        {'email': 'a' * 10000, 'description': 'Email 10,000 characters'},
        {'firstName': 'a' * 10000, 'description': 'First name 10,000 characters'},
        {'input': 'a' * 100000, 'description': 'Unknown field 100,000 characters'},
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        description = test_case.pop('description')
        data = test_case.copy()
        
        # Add required fields for assessment validation
        if 'email' not in data:
            data['email'] = 'test@example.com'
        if 'assessmentType' not in data:
            data['assessmentType'] = 'ai-risk'
        if 'answers' not in data:
            data['answers'] = {}
        
        is_valid, errors, sanitized_data = APIValidator.validate_assessment_data(data)
        
        if not is_valid and len(errors) > 0:
            # Check if any error mentions length
            has_length_error = any('too long' in str(err).lower() or 'too large' in str(err).lower() for err in errors)
            if has_length_error:
                print(f"✅ Test {i}: {description}")
                print(f"   Status: REJECTED (as expected)")
                print(f"   Errors: {[e for e in errors if 'too long' in e.lower() or 'too large' in e.lower()][0]}")
                passed += 1
            else:
                print(f"⚠️  Test {i}: {description}")
                print(f"   Status: REJECTED but for wrong reason")
                print(f"   Errors: {errors}")
                failed += 1
        else:
            print(f"❌ Test {i}: {description}")
            print(f"   Status: ACCEPTED (should be rejected!)")
            print(f"   Errors: {errors}")
            failed += 1
        print()
    
    return passed, failed

def main():
    """Run all validation tests"""
    print("\n" + "="*70)
    print("VALIDATION FIXES VERIFICATION TEST")
    print("="*70)
    print("Testing the 9 warnings that should now be fixed")
    print()
    
    # Test type validation
    type_passed, type_failed = test_type_validation()
    
    # Test length validation
    length_passed, length_failed = test_length_validation()
    
    # Summary
    total_passed = type_passed + length_passed
    total_failed = type_failed + length_failed
    total_tests = 9
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Type Validation:   {type_passed}/6 passed, {6-type_passed} failed")
    print(f"Length Validation: {length_passed}/3 passed, {3-length_passed} failed")
    print(f"\nTotal: {total_passed}/{total_tests} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("\n✅ ALL 9 WARNINGS HAVE BEEN FIXED!")
        return 0
    else:
        print(f"\n❌ {total_failed} test(s) still failing. Review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
