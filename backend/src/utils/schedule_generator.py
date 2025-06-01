from datetime import datetime, timedelta
from typing import List, Dict, Any
from enhanced_schedule import generate_schedule
from supabase import create_client, Client
import os
from config import config
from backend.src.config.supabase_client import get_supabase_client
import uuid

# Get configuration based on environment
env = os.getenv('FLASK_ENV', 'development')
current_config = config.get(env, config['default'])()  # Create an instance of the config class

# Initialize Supabase client lazily
_supabase_client = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            current_config.SUPABASE_URL,  # Access the class attribute directly
            current_config.SUPABASE_ANON_KEY  # Access the class attribute directly
        )
    return _supabase_client

def generate_income_schedule(
    user_id: str,
    income_data: Dict[str, Any],
    months: int = 12
) -> List[str]:
    """
    Generate income schedule dates and store them in the database.
    
    Args:
        user_id: The user's UUID
        income_data: Dictionary containing:
            - income_type: str (e.g., 'salary', 'freelance', 'rental')
            - amount: float
            - frequency: str ('weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually')
            - preferred_day: int (0=Monday through 6=Sunday)
            - start_date: str (YYYY-MM-DD)
            - due_date: int (day of month for monthly payments)
        months: Number of months to generate schedule for
    
    Returns:
        List of generated dates in YYYY-MM-DD format
    """
    # Generate the schedule
    dates = generate_schedule(
        start_date_str=income_data['start_date'],
        frequency=income_data['frequency'],
        months=months,
        adjust_for_business_days=True,
        preferred_days=[income_data.get('preferred_day', 4)]  # Default to Friday
    )
    
    # Store the income schedule in the database
    get_supabase_client().table('user_income_due_dates').insert({
        'user_id': user_id,
        'income_type': income_data['income_type'],
        'amount': income_data['amount'],
        'frequency': income_data['frequency'],
        'preferred_day': income_data.get('preferred_day'),
        'start_date': income_data['start_date'],
        'due_date': income_data.get('due_date')
    }).execute()
    
    return dates

def generate_expense_schedule(user_id: str, expense_type: str, due_day: int) -> dict:
    """
    Generate an expense schedule for a user.
    
    Args:
        user_id: The user's UUID
        expense_type: Type of expense (rent, utilities, etc.)
        due_day: Day of the month the expense is due
    
    Returns:
        The created expense schedule record
    """
    try:
        # Validate due day
        if not 1 <= due_day <= 31:
            raise ValueError("Due day must be between 1 and 31")
            
        # Create the schedule record
        schedule = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'expense_type': expense_type,
            'due_date': due_day,
            'created_at': datetime.now().isoformat()
        }
        
        # Insert into Supabase
        supabase = get_supabase_client()
        response = supabase.table('user_expense_due_dates').insert(schedule).execute()
        
        return response.data[0] if response.data else None
        
    except Exception as e:
        print(f"Error in generate_expense_schedule: {str(e)}")
        raise e

# Example usage:
if __name__ == "__main__":
    # Example income schedule
    income_example = {
        'income_type': 'salary',
        'amount': 5000.00,
        'frequency': 'bi-weekly',
        'preferred_day': 4,  # Friday
        'start_date': '2024-01-01'
    }
    
    # Example expense schedule
    expense_example = {
        'expense_type': 'rent',
        'amount': 2000.00,
        'frequency': 'monthly',
        'due_date': 1,  # First of the month
        'start_date': '2024-01-01'
    }
    
    # Test user ID
    test_user_id = "your-test-user-id"
    
    # Generate schedules
    income_dates = generate_income_schedule(test_user_id, income_example)
    expense_dates = generate_expense_schedule(test_user_id, expense_example['expense_type'], expense_example['due_date'])
    
    print("Income Dates:", income_dates)
    print("Expense Dates:", expense_dates) 