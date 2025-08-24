from datetime import datetime
from config import config
from supabase import create_client
import uuid

def test_insert():
    """Test inserting a single record into each table"""
    # Get configuration
    env = 'development'
    current_config = config.get(env, config['default'])()
    
    # Initialize Supabase client with service role key
    supabase = create_client(
        current_config.SUPABASE_URL,
        current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    
    user_id = "c2d59afb-514d-4275-ab63-165fb03a8f4e"  # johnnie_watson_3rd@mac.com
    start_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Test income insert
        income_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'income_type': 'salary',
            'amount': 5000.00,
            'frequency': 'bi-weekly',
            'preferred_day': 4,
            'start_date': start_date,
            'due_date': None
        }
        
        print("\nTesting income insert...")
        income_response = supabase.table('user_income_due_dates').insert(income_data).execute()
        print("Income insert successful!")
        print(f"Response: {income_response}")
        
        # Test expense insert
        expense_data = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'expense_type': 'rent',
            'amount': 2500.00,
            'frequency': 'monthly',
            'preferred_day': None,
            'start_date': start_date,
            'due_date': 1
        }
        
        print("\nTesting expense insert...")
        expense_response = supabase.table('user_expense_due_dates').insert(expense_data).execute()
        print("Expense insert successful!")
        print(f"Response: {expense_response}")
        
        return True
    except Exception as e:
        print(f"\nError in test insert:")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        raise e

if __name__ == "__main__":
    test_insert() 