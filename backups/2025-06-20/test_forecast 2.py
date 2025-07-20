from supabase import create_client
import uuid
from datetime import datetime, date
import requests
import json
from config import config

def run_forecast_test():
    # Get configuration
    env = 'development'
    current_config = config.get(env, config['default'])()
    
    # Initialize Supabase client
    supabase = create_client(
        current_config.SUPABASE_URL,
        current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    
    # Create a test user in auth
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPassword123!"
    
    print(f"\nCreating test user: {email}")
    auth_response = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })
    
    test_user_id = auth_response.user.id
    
    # Set up test income schedule (bi-weekly salary)
    income_data = {
        "user_id": test_user_id,
        "income_type": "Salary",
        "amount": 5000.00,
        "frequency": "bi-weekly",
        "start_date": "2025-06-01",
        "preferred_day": 1  # Paid on 1st and 15th
    }
    
    print("\nCreating test income schedule:")
    print(json.dumps(income_data, indent=2))
    supabase.table("user_income_due_dates").insert(income_data).execute()
    
    # Set up test expense schedule (monthly rent)
    expense_data = {
        "user_id": test_user_id,
        "expense_type": "Rent",
        "amount": 2500.00,
        "frequency": "monthly",
        "start_date": "2025-06-01",
        "due_date": 1  # Due on the 1st of each month
    }
    
    print("\nCreating test expense schedule:")
    print(json.dumps(expense_data, indent=2))
    supabase.table("user_expense_due_dates").insert(expense_data).execute()
    
    # Run the cashflow calculation
    forecast_data = {
        "user_id": test_user_id,
        "initial_balance": 1000.00,
        "start_date": "2025-06-01"
    }
    
    print("\nRunning cashflow calculation:")
    print(json.dumps(forecast_data, indent=2))
    
    response = requests.post(
        "http://localhost:5003/api/cashflow/calculate",
        json=forecast_data
    )
    
    if response.status_code == 200:
        results = response.json()
        print("\nForecast Results:")
        print(f"Total records: {len(results)}")
        
        # Print first 5 days and last 5 days
        print("\nFirst 5 days:")
        for day in results[:5]:
            print(f"Date: {day['forecast_date']}")
            print(f"Opening Balance: ${day['opening_balance']:,.2f}")
            print(f"Income: ${day['income']:,.2f}")
            print(f"Expenses: ${day['expenses']:,.2f}")
            print(f"Closing Balance: ${day['closing_balance']:,.2f}")
            print(f"Status: {day['balance_status']}")
            print("-" * 50)
        
        print("\nLast 5 days:")
        for day in results[-5:]:
            print(f"Date: {day['forecast_date']}")
            print(f"Opening Balance: ${day['opening_balance']:,.2f}")
            print(f"Income: ${day['income']:,.2f}")
            print(f"Expenses: ${day['expenses']:,.2f}")
            print(f"Closing Balance: ${day['closing_balance']:,.2f}")
            print(f"Status: {day['balance_status']}")
            print("-" * 50)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    run_forecast_test() 