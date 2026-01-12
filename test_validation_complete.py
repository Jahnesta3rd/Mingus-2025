#!/usr/bin/env python3
"""
Complete test of all 9 validation fixes
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.validation import APIValidator

def test_all_9_cases():
    """Test all 9 cases that were causing warnings"""
    print("\n" + "="*70)
    print("COMPLETE VALIDATION FIXES TEST - All 9 Cases")
    print("="*70)
    
    # Base valid data
    base_data = {
        'email': 'test@example.com',
        'assessmentType': 'ai-risk',
        'answers': {}
    }
    
    test_cases = [
        # Type validation (6 tests)
        ({'email': 123}, 'Email as integer', 'type'),
        ({'email': []}, 'Email as list', 'type'),
        ({'email': {}}, 'Email as dictionary', 'type'),
        ({**base_data, 'age': 'not_a_number'}, 'Age as string (unknown field)', 'type'),
        ({**base_data, 'age': -1}, 'Negative age (unknown field)', 'type'),
        ({**base_data, 'age': 1000}, 'Too large age (unknown field)', 'type'),
        
        # Length validation (3 tests)
        ({'email': 'a' * 10000, 'assessmentType': 'ai-risk', 'answers': {}}, 'Email 10,000 chars', 'length'),
        ({**base_data, 'firstName': 'a' * 10000}, 'First name 10,000 chars', 'length'),
        ({**base_data, 'input': 'a' * 100000}, 'Unknown field 100,000 chars', 'length'),
    ]
    
    results = {'type': {'passed': 0, 'failed': 0}, 'length': {'passed': 0, 'failed': 0}}
    
    for i, (data, description, category) in enumerate(test_cases, 1):
        is_valid, errors, sanitized_data = APIValidator.validate_assessment_data(data)
        
        # All should be rejected
        if not is_valid:
            print(f"✅ Test {i} ({category}): {description}")
            print(f"   Status: REJECTED ✓")
            if errors:
                # Show first relevant error
                relevant_error = errors[0] if len(errors) == 1 else errors[0]
                print(f"   Error: {relevant_error[:80]}...")
            results[category]['passed'] += 1
        else:
            print(f"❌ Test {i} ({category}): {description}")
            print(f"   Status: ACCEPTED (should be rejected!)")
            results[category]['failed'] += 1
        print()
    
    return results

def main():
    """Run complete validation test"""
    print("\n" + "="*70)
    print("VALIDATION FIXES - COMPLETE VERIFICATION")
    print("="*70)
    print("Testing all 9 cases that were causing warnings")
    print()
    
    results = test_all_9_cases()
    
    type_passed = results['type']['passed']
    type_failed = results['type']['failed']
    length_passed = results['length']['passed']
    length_failed = results['length']['failed']
    
    total_passed = type_passed + length_passed
    total_failed = type_failed + length_failed
    
    print("="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Type Validation:   {type_passed}/6 passed, {type_failed} failed")
    print(f"Length Validation: {length_passed}/3 passed, {length_failed} failed")
    print(f"\nTotal: {total_passed}/9 passed, {total_failed} failed")
    
    if total_failed == 0:
        print("\n" + "="*70)
        print("✅ SUCCESS: ALL 9 WARNINGS HAVE BEEN FIXED!")
        print("="*70)
        print("\nAll validation tests are passing:")
        print("  ✓ Type validation working correctly")
        print("  ✓ Length validation working correctly")
        print("  ✓ Unknown field validation working correctly")
        return 0
    else:
        print(f"\n❌ {total_failed} test(s) still failing. Review errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
