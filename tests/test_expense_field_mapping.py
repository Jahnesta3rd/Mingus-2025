"""
Test script to verify expense field mapping and standardization.
This ensures compatibility between frontend and backend field names.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.field_mapping import (
    EXPENSE_FIELDS,
    TEXT_FIELDS,
    EXPENSE_CATEGORIES,
    validate_expense_data,
    normalize_expense_data,
    calculate_monthly_totals,
    to_monthly_amount,
    get_frequency_field,
    get_due_date_field
)

def test_field_definitions():
    """Test that all field definitions are consistent."""
    print("Testing field definitions...")
    
    # Check that all expense fields end with _expense
    for field in EXPENSE_FIELDS:
        assert field.endswith('_expense'), f"Expense field {field} should end with _expense"
    
    # Check that all text fields end with _name
    for field in TEXT_FIELDS:
        assert field.endswith('_name'), f"Text field {field} should end with _name"
    
    # Check that all categories contain valid fields
    all_fields = set(EXPENSE_FIELDS + TEXT_FIELDS)
    for category, fields in EXPENSE_CATEGORIES.items():
        for field in fields:
            assert field in all_fields, f"Field {field} in category {category} not found in field definitions"
    
    print("✓ Field definitions are consistent")

def test_field_mapping_functions():
    """Test field mapping utility functions."""
    print("Testing field mapping functions...")
    
    # Test frequency field mapping
    assert get_frequency_field('rent_or_mortgage_expense') == 'rent_or_mortgage_frequency'
    assert get_frequency_field('utilities_expense') == 'utilities_frequency'
    assert get_frequency_field('credit_card1_name') is None  # Should return None for non-expense fields
    
    # Test due date field mapping
    assert get_due_date_field('rent_or_mortgage_expense') == 'rent_or_mortgage_due_date'
    assert get_due_date_field('utilities_expense') == 'utilities_due_date'
    assert get_due_date_field('credit_card1_name') is None  # Should return None for non-expense fields
    
    print("✓ Field mapping functions work correctly")

def test_monthly_calculation():
    """Test monthly amount calculations."""
    print("Testing monthly calculations...")
    
    # Test various frequencies
    assert to_monthly_amount(100, 'weekly') == round(100 * 52 / 12, 2)
    assert to_monthly_amount(200, 'bi-weekly') == round(200 * 26 / 12, 2)
    assert to_monthly_amount(500, 'monthly') == 500
    assert to_monthly_amount(1500, 'quarterly') == 500
    assert to_monthly_amount(6000, 'annually') == 500
    
    # Test edge cases
    assert to_monthly_amount(0, 'monthly') == 0
    assert to_monthly_amount(100, 'unknown') == 100  # Default to original amount
    
    print("✓ Monthly calculations work correctly")

def test_data_validation():
    """Test expense data validation."""
    print("Testing data validation...")
    
    # Valid data
    valid_data = {
        'starting_balance': 1000,
        'expenses': {
            'rent_or_mortgage_expense': {
                'amount': 1500,
                'frequency': 'monthly',
                'due_date': '2024-01-01'
            },
            'credit_card1_name': 'Chase Visa'
        }
    }
    
    is_valid, errors = validate_expense_data(valid_data)
    assert is_valid, f"Valid data should pass validation: {errors}"
    
    # Invalid data - missing starting balance
    invalid_data = {
        'expenses': {
            'rent_or_mortgage_expense': {
                'amount': 1500,
                'frequency': 'monthly'
            }
        }
    }
    
    is_valid, errors = validate_expense_data(invalid_data)
    assert not is_valid, "Invalid data should fail validation"
    assert 'Starting balance is required' in errors
    
    # Invalid data - missing amount
    invalid_data = {
        'starting_balance': 1000,
        'expenses': {
            'rent_or_mortgage_expense': {
                'frequency': 'monthly'
            }
        }
    }
    
    is_valid, errors = validate_expense_data(invalid_data)
    assert not is_valid, "Invalid data should fail validation"
    assert 'Amount is required for rent_or_mortgage_expense' in errors
    
    print("✓ Data validation works correctly")

def test_data_normalization():
    """Test expense data normalization."""
    print("Testing data normalization...")
    
    # Test with extra fields
    raw_data = {
        'starting_balance': 1000,
        'expenses': {
            'rent_or_mortgage_expense': {
                'amount': 1500,
                'frequency': 'monthly',
                'due_date': '2024-01-01'
            },
            'credit_card1_name': 'Chase Visa',
            'unknown_field': 'should_be_removed'
        },
        'extra_field': 'should_be_removed'
    }
    
    normalized = normalize_expense_data(raw_data)
    
    # Check that only valid fields are included
    assert 'starting_balance' in normalized
    assert 'expenses' in normalized
    assert 'rent_or_mortgage_expense' in normalized['expenses']
    assert 'credit_card1_name' in normalized['expenses']
    assert 'unknown_field' not in normalized['expenses']
    assert 'extra_field' not in normalized
    
    print("✓ Data normalization works correctly")

def test_totals_calculation():
    """Test monthly totals calculation."""
    print("Testing totals calculation...")
    
    # Test data with expenses in different categories
    test_data = {
        'expenses': {
            'rent_or_mortgage_expense': {'monthly': 1500},  # Essential
            'utilities_expense': {'monthly': 200},          # Essential
            'grocery_expense': {'monthly': 400},            # Living
            'entertainment_expense': {'monthly': 100},      # Discretionary
            'credit_card1_expense': {'monthly': 300},       # Debt
            'credit_card1_name': 'Chase Visa'               # Text field
        }
    }
    
    totals = calculate_monthly_totals(test_data)
    
    assert totals['essential'] == 1700  # 1500 + 200
    assert totals['living'] == 400      # 400
    assert totals['debt'] == 300        # 300
    assert totals['discretionary'] == 100  # 100
    assert totals['total'] == 2500      # 1700 + 400 + 300 + 100
    
    print("✓ Totals calculation works correctly")

def test_frontend_backend_compatibility():
    """Test that frontend and backend field names are compatible."""
    print("Testing frontend-backend compatibility...")
    
    # Simulate frontend data (snake_case)
    frontend_data = {
        'starting_balance': 1000,
        'expenses': {
            'rent_or_mortgage_expense': {
                'amount': 1500,
                'frequency': 'monthly',
                'due_date': '2024-01-01'
            },
            'utilities_expense': {
                'amount': 200,
                'frequency': 'monthly',
                'due_date': '2024-01-15'
            },
            'credit_card1_name': 'Chase Visa',
            'credit_card1_expense': {
                'amount': 300,
                'frequency': 'monthly',
                'due_date': '2024-01-20'
            }
        }
    }
    
    # Validate frontend data
    is_valid, errors = validate_expense_data(frontend_data)
    assert is_valid, f"Frontend data should be valid: {errors}"
    
    # Normalize data
    normalized = normalize_expense_data(frontend_data)
    
    # Calculate monthly amounts
    expenses = normalized.get('expenses', {})
    for field, value in expenses.items():
        if isinstance(value, dict) and 'amount' in value and 'frequency' in value:
            monthly_amount = to_monthly_amount(value['amount'], value['frequency'])
            value['monthly'] = monthly_amount
    
    # Calculate totals
    totals = calculate_monthly_totals(normalized)
    
    # Verify the data structure matches backend expectations
    assert normalized['starting_balance'] == 1000
    assert expenses['rent_or_mortgage_expense']['monthly'] == 1500
    assert expenses['utilities_expense']['monthly'] == 200
    assert expenses['credit_card1_expense']['monthly'] == 300
    assert totals['essential'] == 1700
    assert totals['total'] == 2000
    
    print("✓ Frontend-backend compatibility verified")

def run_all_tests():
    """Run all tests and report results."""
    print("Running expense field mapping tests...\n")
    
    tests = [
        test_field_definitions,
        test_field_mapping_functions,
        test_monthly_calculation,
        test_data_validation,
        test_data_normalization,
        test_totals_calculation,
        test_frontend_backend_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {str(e)}")
            failed += 1
        print()
    
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Expense field standardization is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 