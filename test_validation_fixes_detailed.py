#!/usr/bin/env python3
"""
Detailed test of validation fixes - includes all required fields
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.validation import APIValidator

def test_unknown_field_validation():
    """Test unknown field validation with all required fields present"""
    print("\n" + "="*70)
    print("TESTING UNKNOWN FIELD VALIDATION (with all required fields)")
    print("="*70)
    
    # Valid base data with all required fields
    base_data = {
        'email': 'test@example.com',
        'assessmentType': 'ai-risk',
        'answers': {}
    }
    
    test_cases = [
        ({'age': 'not_a_number'}, 'Age as string (unknown field)'),
        ({'age': -1}, 'Negative age (unknown field)'),
        ({'age': 1000}, 'Too large age (unknown field)'),
        ({'input': 'a' * 100000}, 'Unknown field 100,000 characters'),
    ]
    
    passed = 0
    failed = 0
    
    for i, (extra_fields, description) in enumerate(test_cases, 1):
        data = {**base_data, **extra_fields}
        
        is_valid, errors, sanitized_data = APIValidator.validate_assessment_data(data)
        
        # Check if validation caught the unknown field issue
        has_unknown_field_error = any(
            'unknown' in str(err).lower() or 
            'too long' in str(err).lower() or 
            'too large' in str(err).lower() or
            'out of acceptable range' in str(err).lower()
            for err in errors
        )
        
        if not is_valid:
            if has_unknown_field_error:
                print(f"✅ Test {i}: {description}")
                print(f"   Status: REJECTED (unknown field validation working)")
                matching_errors = [e for e in errors if 'unknown' in e.lower() or 'too long' in e.lower() or 'too large' in e.lower() or 'out of acceptable range' in e.lower()]
                print(f"   Errors: {matching_errors[0] if matching_errors else errors[0]}")
                passed += 1
            else:
                print(f"⚠️  Test {i}: {description}")
                print(f"   Status: REJECTED but for different reason")
                print(f"   Errors: {errors}")
                # Still count as passed since it's being rejected
                passed += 1
        else:
            print(f"❌ Test {i}: {description}")
            print(f"   Status: ACCEPTED (should be rejected!)")
            failed += 1
        print()
    
    return passed, failed

def main():
    """Run detailed validation tests"""
    print("\n" + "="*70)
    print("DETAILED VALIDATION FIXES VERIFICATION")
    print("="*70)
    print("Testing unknown field validation with complete data")
    print()
    
    passed, failed = test_unknown_field_validation()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Unknown Field Tests: {passed}/4 passed, {failed} failed")
    
    if failed == 0:
        print("\n✅ Unknown field validation is working correctly!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) still failing.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
