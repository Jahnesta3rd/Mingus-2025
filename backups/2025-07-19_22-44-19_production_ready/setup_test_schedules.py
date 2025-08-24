from datetime import datetime
from config import config
from supabase import create_client
import uuid

def setup_test_schedules(user_id: str):
    """Set up test income and expense schedules for a user"""
    # Get configuration
    env = 'development'
    current_config = config.get(env, config['default'])()
    
    # Initialize Supabase client with service role key
    supabase = create_client(
        current_config.SUPABASE_URL,
        current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    
    start_date = datetime.now().strftime("%Y-%m-%d")
    
    # Set up income schedules
    income_schedules = [
        {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'income_type': 'salary',
            'amount': 5000.00,
            'frequency': 'bi-weekly',
            'preferred_day': 4,  # Friday
            'start_date': start_date,
            'due_date': None
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'income_type': 'rental',
            'amount': 2000.00,
            'frequency': 'monthly',
            'preferred_day': None,
            'start_date': start_date,
            'due_date': 1  # First of the month
        }
    ]
    
    # Set up expense schedules
    expense_schedules = [
        {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'expense_type': 'rent',
            'amount': 2500.00,
            'frequency': 'monthly',
            'preferred_day': None,
            'start_date': start_date,
            'due_date': 1  # First of the month
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'expense_type': 'utilities',
            'amount': 200.00,
            'frequency': 'monthly',
            'preferred_day': None,
            'start_date': start_date,
            'due_date': 15  # 15th of the month
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'expense_type': 'car_payment',
            'amount': 400.00,
            'frequency': 'monthly',
            'preferred_day': None,
            'start_date': start_date,
            'due_date': 5  # 5th of the month
        }
    ]
    
    try:
        # First, delete any existing schedules for this user
        print("Deleting existing schedules...")
        supabase.table('user_income_due_dates').delete().eq('user_id', user_id).execute()
        supabase.table('user_expense_due_dates').delete().eq('user_id', user_id).execute()
        
        # Insert income schedules
        print("Inserting income schedules...")
        income_response = supabase.table('user_income_due_dates').insert(income_schedules).execute()
        print(f"Added {len(income_response.data)} income schedules")
        
        # Insert expense schedules
        print("Inserting expense schedules...")
        expense_response = supabase.table('user_expense_due_dates').insert(expense_schedules).execute()
        print(f"Added {len(expense_response.data)} expense schedules")
        
        return True
    except Exception as e:
        print(f"Error setting up schedules: {str(e)}")
        raise e

if __name__ == "__main__":
    # Use the johnnie_watson_3rd@mac.com user ID
    user_id = "c2d59afb-514d-4275-ab63-165fb03a8f4e"
    setup_test_schedules(user_id) 