from datetime import datetime
import uuid
from cashflow_calculator import calculate_daily_cashflow
from schedule_generator import generate_income_schedule, generate_expense_schedule

def test_cashflow_calculation():
    """Test the cash flow calculator with sample data"""
    # Create a test user ID
    test_user_id = str(uuid.uuid4())
    start_date = datetime.now().strftime("%Y-%m-%d")
    
    # Set up test income schedules
    income_data = [
        {
            'income_type': 'salary',
            'amount': 5000.00,
            'frequency': 'bi-weekly',
            'preferred_day': 4,  # Friday
            'start_date': start_date
        },
        {
            'income_type': 'rental',
            'amount': 2000.00,
            'frequency': 'monthly',
            'due_date': 1,
            'start_date': start_date
        }
    ]
    
    # Set up test expense schedules
    expense_data = [
        {
            'expense_type': 'rent',
            'amount': 2500.00,
            'frequency': 'monthly',
            'due_date': 1,
            'start_date': start_date
        },
        {
            'expense_type': 'utilities',
            'amount': 200.00,
            'frequency': 'monthly',
            'due_date': 15,
            'start_date': start_date
        },
        {
            'expense_type': 'car_payment',
            'amount': 400.00,
            'frequency': 'monthly',
            'due_date': 5,
            'start_date': start_date
        }
    ]
    
    # Generate schedules
    print("\nGenerating test schedules...")
    for income in income_data:
        generate_income_schedule(test_user_id, income)
    
    for expense in expense_data:
        generate_expense_schedule(test_user_id, expense)
    
    # Calculate cash flow
    print("\nCalculating cash flow...")
    initial_balance = 10000.00
    cashflow = calculate_daily_cashflow(test_user_id, initial_balance)
    
    # Print first month of projections
    print("\nFirst month of cash flow projections:")
    print("\nInitial Balance: ${:,.2f}".format(initial_balance))
    print("\nSample of significant days (with transactions):")
    
    # Track monthly totals
    monthly_income = 0
    monthly_expenses = 0
    
    for record in cashflow[:30]:  # First 30 days
        if record['income'] > 0 or record['expenses'] > 0:
            print(f"\nDate: {record['forecast_date']}")
            print(f"Opening Balance: ${record['opening_balance']:,.2f}")
            if record['income'] > 0:
                print(f"Income: ${record['income']:,.2f}")
            if record['expenses'] > 0:
                print(f"Expenses: ${record['expenses']:,.2f}")
            print(f"Closing Balance: ${record['closing_balance']:,.2f}")
            print(f"Status: {record['balance_status']}")
            
            monthly_income += record['income']
            monthly_expenses += record['expenses']
    
    # Print monthly summary
    print("\nMonthly Summary:")
    print(f"Total Income: ${monthly_income:,.2f}")
    print(f"Total Expenses: ${monthly_expenses:,.2f}")
    print(f"Net Change: ${(monthly_income - monthly_expenses):,.2f}")

if __name__ == '__main__':
    test_cashflow_calculation() 