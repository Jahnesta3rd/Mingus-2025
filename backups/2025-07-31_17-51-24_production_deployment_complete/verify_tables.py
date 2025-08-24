from config import config
from supabase import create_client

def verify_tables():
    """Verify that the required tables exist and show their structure"""
    # Get configuration
    env = 'development'
    current_config = config.get(env, config['default'])()
    
    # Initialize Supabase client with service role key
    supabase = create_client(
        current_config.SUPABASE_URL,
        current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    
    # List of tables to verify
    tables = [
        'users',
        'user_income_due_dates',
        'user_expense_due_dates',
        'daily_cashflow'
    ]
    
    try:
        for table in tables:
            print(f"\nVerifying table: {table}")
            # Try to select a single row to verify table exists
            response = supabase.table(table).select('*').limit(1).execute()
            print(f"Table exists and is accessible")
            print(f"Columns: {', '.join(response.data[0].keys()) if response.data else 'No data to show columns'}")
    except Exception as e:
        print(f"Error verifying tables: {str(e)}")
        raise e

if __name__ == "__main__":
    verify_tables() 