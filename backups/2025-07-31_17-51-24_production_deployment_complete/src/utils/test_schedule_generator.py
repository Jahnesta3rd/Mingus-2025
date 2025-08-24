import unittest
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.schedule_generator import generate_income_schedule, generate_expense_schedule
import uuid

class TestScheduleGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test cases with a test user ID"""
        self.test_user_id = str(uuid.uuid4())
        self.start_date = datetime.now().strftime("%Y-%m-%d")

    def test_biweekly_salary(self):
        """Test bi-weekly salary schedule generation"""
        income_data = {
            'income_type': 'salary',
            'amount': 5000.00,
            'frequency': 'bi-weekly',
            'preferred_day': 4,  # Friday
            'start_date': self.start_date
        }
        
        dates = generate_income_schedule(self.test_user_id, income_data, months=3)
        
        # Verify we got the correct number of dates (approximately 6 bi-weekly payments in 3 months)
        self.assertTrue(5 <= len(dates) <= 7)
        
        # Verify all dates are strings in YYYY-MM-DD format
        for date in dates:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                self.fail(f"Date {date} is not in YYYY-MM-DD format")

    def test_monthly_rent(self):
        """Test monthly rent expense schedule generation"""
        expense_data = {
            'expense_type': 'rent',
            'amount': 2000.00,
            'frequency': 'monthly',
            'due_date': 1,  # First of the month
            'start_date': self.start_date
        }
        
        dates = generate_expense_schedule(self.test_user_id, expense_data, months=3)
        
        # Verify we got 3 dates (one per month)
        self.assertEqual(len(dates), 3)
        
        # Verify all dates are business days
        for date in dates:
            dt = datetime.strptime(date, "%Y-%m-%d")
            self.assertTrue(0 <= dt.weekday() <= 4, f"Date {date} is not a business day")

    def test_weekly_allowance(self):
        """Test weekly allowance schedule generation"""
        income_data = {
            'income_type': 'allowance',
            'amount': 100.00,
            'frequency': 'weekly',
            'preferred_day': 2,  # Wednesday
            'start_date': self.start_date
        }
        
        dates = generate_income_schedule(self.test_user_id, income_data, months=1)
        
        # Verify we got approximately 4-5 dates (weeks in a month)
        self.assertTrue(4 <= len(dates) <= 5)
        
        # Verify dates are sequential and at least 5 days apart
        prev_date = None
        for date in dates:
            current_date = datetime.strptime(date, "%Y-%m-%d")
            if prev_date:
                days_diff = (current_date - prev_date).days
                self.assertTrue(days_diff >= 5, f"Dates {prev_date} and {current_date} are too close")
            prev_date = current_date

    def test_quarterly_tax(self):
        """Test quarterly tax payment schedule generation"""
        expense_data = {
            'expense_type': 'estimated_tax',
            'amount': 3000.00,
            'frequency': 'quarterly',
            'start_date': self.start_date
        }
        
        dates = generate_expense_schedule(self.test_user_id, expense_data, months=12)
        
        # Verify we got 4 dates (quarterly for a year)
        self.assertEqual(len(dates), 4)
        
        # Verify dates are roughly 3 months apart
        prev_date = None
        for date in dates:
            current_date = datetime.strptime(date, "%Y-%m-%d")
            if prev_date:
                days_diff = (current_date - prev_date).days
                self.assertTrue(85 <= days_diff <= 95, f"Quarterly dates {prev_date} and {current_date} are not ~3 months apart")
            prev_date = current_date

    def test_invalid_frequency(self):
        """Test handling of invalid frequency"""
        income_data = {
            'income_type': 'salary',
            'amount': 5000.00,
            'frequency': 'invalid_frequency',  # Invalid frequency
            'start_date': self.start_date
        }
        
        # Should raise a KeyError due to invalid frequency
        with self.assertRaises(KeyError):
            generate_income_schedule(self.test_user_id, income_data)

if __name__ == '__main__':
    unittest.main(verbosity=2) 