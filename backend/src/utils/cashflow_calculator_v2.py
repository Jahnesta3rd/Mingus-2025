from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid
from supabase import create_client, Client
from config import config
import re
from urllib.parse import urlparse

def validate_supabase_url(url: str) -> bool:
    """Validate Supabase URL format."""
    if not url:
        return False
    
    # Basic URL validation
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_supabase() -> Client:
    """Get Supabase client with service role key for admin access"""
    try:
        env = 'development'
        current_config = config.get(env, config['default'])()
        
        # Print debug info about configuration
        print("\nSupabase Client Debug:")
        print(f"Config type: {type(current_config)}")
        print(f"URL type: {type(current_config.SUPABASE_URL)}")
        print(f"URL value: {current_config.SUPABASE_URL}")
        print(f"Key type: {type(current_config.SUPABASE_SERVICE_ROLE_KEY)}")
        print(f"Key value: {current_config.SUPABASE_SERVICE_ROLE_KEY[:10]}...")
        
        # Validate URL
        url = current_config.SUPABASE_URL
        if not validate_supabase_url(url):
            raise ValueError(f"Invalid Supabase URL format: {url}")
            
        # Ensure URL starts with https://
        if not url.startswith('https://'):
            url = f'https://{url}'
        
        return create_client(
            url,
            current_config.SUPABASE_SERVICE_ROLE_KEY
        )
    except Exception as e:
        print(f"\nError in get_supabase:")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        raise

def calculate_daily_cashflow(user_id: str, initial_balance: float, start_date: str = None) -> List[Dict[str, Any]]:
    """
    Calculate daily cash flow for the next 12 months based on income and expense schedules.
    
    Args:
        user_id: The user's UUID
        initial_balance: Starting balance
        start_date: Optional start date (YYYY-MM-DD), defaults to today
    
    Returns:
        List of daily cash flow records
    """
    try:
        # Set start date to today if not provided
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        # Convert start_date to datetime
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = current_date + timedelta(days=365)  # 12 months from start
        
        print(f"Calculating cashflow for user {user_id} from {start_date} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get Supabase client
        try:
            supabase = get_supabase()
        except Exception as e:
            print(f"\nError getting Supabase client:")
            print(f"Error type: {type(e)}")
            print(f"Error message: {str(e)}")
            print(f"Error details: {repr(e)}")
            raise
        
        # First, delete existing projections for this user and date range
        delete_response = supabase.table('daily_cashflow') \
            .delete() \
            .eq('user_id', user_id) \
            .gte('forecast_date', start_date) \
            .lte('forecast_date', end_date.strftime("%Y-%m-%d")) \
            .execute()
        
        print(f"Deleted existing records: {delete_response}")
        
        # Fetch all income dates
        income_response = supabase.table('user_income_due_dates') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
        income_schedules = income_response.data
        
        # Fetch all expense dates
        expense_response = supabase.table('user_expense_due_dates') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
        expense_schedules = expense_response.data

        # Create a dictionary to store daily transactions
        daily_transactions = {}
        
        # Process income schedules
        for income in income_schedules:
            if income['frequency'] == 'monthly' and income['due_date']:
                # Monthly income on specific day
                due_day = income['due_date']
                amount = income['amount']
                
                # Generate dates for the next 12 months
                current = current_date
                while current <= end_date:
                    # If this is the due day for this month
                    if current.day == due_day:
                        date_str = current.strftime("%Y-%m-%d")
                        if date_str not in daily_transactions:
                            daily_transactions[date_str] = {'income': 0, 'expenses': 0}
                        daily_transactions[date_str]['income'] += amount
                    
                    # Move to next day
                    current += timedelta(days=1)
            
            elif income['frequency'] == 'bi-weekly' and income['preferred_day'] is not None:
                # Bi-weekly income on preferred day (0=Monday through 6=Sunday)
                preferred_day = income['preferred_day']
                amount = income['amount']
                
                # Start from the first occurrence of preferred day
                current = current_date
                while current.weekday() != preferred_day:
                    current += timedelta(days=1)
                
                # Generate bi-weekly dates
                while current <= end_date:
                    date_str = current.strftime("%Y-%m-%d")
                    if date_str not in daily_transactions:
                        daily_transactions[date_str] = {'income': 0, 'expenses': 0}
                    daily_transactions[date_str]['income'] += amount
                    
                    # Move to next bi-weekly date
                    current += timedelta(days=14)
        
        # Process expense schedules
        for expense in expense_schedules:
            if expense['frequency'] == 'monthly' and expense['due_date']:
                # Monthly expense on specific day
                due_day = expense['due_date']
                amount = expense['amount']
                
                # Generate dates for the next 12 months
                current = current_date
                while current <= end_date:
                    # If this is the due day for this month
                    if current.day == due_day:
                        date_str = current.strftime("%Y-%m-%d")
                        if date_str not in daily_transactions:
                            daily_transactions[date_str] = {'income': 0, 'expenses': 0}
                        daily_transactions[date_str]['expenses'] += amount
                    
                    # Move to next day
                    current += timedelta(days=1)

        # Calculate daily balances
        cashflow_records = []
        running_balance = initial_balance
        current = current_date
        
        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            
            # Get transactions for the day (or default to 0)
            daily_data = daily_transactions.get(date_str, {'income': 0, 'expenses': 0})
            income = daily_data['income']
            expenses = daily_data['expenses']
            
            # Calculate balances
            opening_balance = running_balance
            net_change = income - expenses
            closing_balance = opening_balance + net_change
            
            # Determine balance status
            if closing_balance >= 5000:
                balance_status = 'healthy'
            elif closing_balance >= 0:
                balance_status = 'warning'
            else:
                balance_status = 'danger'
            
            # Create record
            record = {
                'id': str(uuid.uuid4()),
                'user_id': user_id,
                'forecast_date': date_str,
                'opening_balance': opening_balance,
                'income': income,
                'expenses': expenses,
                'closing_balance': closing_balance,
                'net_change': net_change,
                'balance_status': balance_status
            }
            
            cashflow_records.append(record)
            
            # Update running balance for next day
            running_balance = closing_balance
            current += timedelta(days=1)
        
        # Batch insert records with explicit handling
        batch_size = 50
        for i in range(0, len(cashflow_records), batch_size):
            batch = cashflow_records[i:i + batch_size]
            try:
                insert_response = supabase.table('daily_cashflow') \
                    .insert(batch) \
                    .execute()
                print(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as batch_error:
                print(f"Error inserting batch {i//batch_size + 1}: {str(batch_error)}")
                raise batch_error
        
        return cashflow_records

    except Exception as e:
        print(f"Error in calculate_daily_cashflow: {str(e)}")
        print(f"\nError in calculate_daily_cashflow:")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {repr(e)}")
        raise e 