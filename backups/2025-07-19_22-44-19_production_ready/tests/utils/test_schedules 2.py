import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from datetime import datetime
from backend.src.utils.schedule_generator import generate_income_schedule, generate_expense_schedule
import uuid

def test_schedules():
    """Run basic tests for schedule generation"""
    test_user_id = str(uuid.uuid4())
    start_date = datetime.now().strftime("%Y-%m-%d")
    
    print("\n=== Testing Schedule Generator ===\n")
    
    # Test 1: Bi-weekly salary
    print("Test 1: Bi-weekly Salary")
    income_data = {
        'income_type': 'salary',
        'amount': 5000.00,
        'frequency': 'bi-weekly',
        'preferred_day': 4,  # Friday
        'start_date': start_date
    }
    
    try:
        salary_dates = generate_income_schedule(test_user_id, income_data, months=3)
        print(f"Generated {len(salary_dates)} bi-weekly salary dates:")
        for date in salary_dates:
            print(f"  {date}")
    except Exception as e:
        print(f"Error in salary test: {str(e)}")
    
    # Test 2: Monthly rent
    print("\nTest 2: Monthly Rent")
    expense_data = {
        'expense_type': 'rent',
        'amount': 2000.00,
        'frequency': 'monthly',
        'due_date': 1,
        'start_date': start_date
    }
    
    try:
        rent_dates = generate_expense_schedule(test_user_id, expense_data, months=3)
        print(f"Generated {len(rent_dates)} monthly rent dates:")
        for date in rent_dates:
            print(f"  {date}")
    except Exception as e:
        print(f"Error in rent test: {str(e)}")
    
    # Test 3: Weekly allowance
    print("\nTest 3: Weekly Allowance")
    allowance_data = {
        'income_type': 'allowance',
        'amount': 100.00,
        'frequency': 'weekly',
        'preferred_day': 2,  # Wednesday
        'start_date': start_date
    }
    
    try:
        allowance_dates = generate_income_schedule(test_user_id, allowance_data, months=1)
        print(f"Generated {len(allowance_dates)} weekly allowance dates:")
        for date in allowance_dates:
            print(f"  {date}")
    except Exception as e:
        print(f"Error in allowance test: {str(e)}")
    
    # Test 4: Quarterly tax payments
    print("\nTest 4: Quarterly Tax Payments")
    tax_data = {
        'expense_type': 'estimated_tax',
        'amount': 3000.00,
        'frequency': 'quarterly',
        'start_date': start_date
    }
    
    try:
        tax_dates = generate_expense_schedule(test_user_id, tax_data, months=12)
        print(f"Generated {len(tax_dates)} quarterly tax dates:")
        for date in tax_dates:
            print(f"  {date}")
    except Exception as e:
        print(f"Error in tax test: {str(e)}")

if __name__ == '__main__':
    test_schedules() 