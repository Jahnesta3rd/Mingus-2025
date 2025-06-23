from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid
from backend.src.config.supabase_client import get_supabase_client

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
    # Set start date to today if not provided
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    
    # Convert start_date to datetime
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = current_date + timedelta(days=365)  # 12 months from start
    
    try:
        print(f"Calculating cashflow for user {user_id} from {start_date} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # First, delete existing projections for this user and date range
        delete_response = supabase.table('daily_cashflow') \
            .delete() \
            .eq('user_id', user_id) \
            .gte('forecast_date', start_date) \
            .lte('forecast_date', end_date.strftime("%Y-%m-%d")) \
            .execute()
        
        print(f"Deleted existing records: {delete_response}")
        
        # Fetch all expense dates
        expense_response = supabase.table('user_expense_due_dates') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
        expense_schedules = expense_response.data

        # Create a dictionary to store daily transactions
        daily_transactions = {}
        
        # Process expense schedules
        for expense in expense_schedules:
            # Get the day of the month for this expense
            due_day = expense['due_date']
            expense_type = expense['expense_type']
            
            # Set default amounts based on expense type
            amount = {
                'rent': 2500.00,
                'utilities': 200.00,
                'car_payment': 400.00
            }.get(expense_type, 0.00)
            
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
        raise e

# Example usage:
if __name__ == "__main__":
    # Test the function
    test_user_id = "your-test-user-id"
    initial_balance = 10000.00
    
    cashflow = calculate_daily_cashflow(test_user_id, initial_balance)
    
    # Print first week of projections
    print("\nFirst week of cash flow projections:")
    for record in cashflow[:7]:
        print(f"\nDate: {record['forecast_date']}")
        print(f"Opening Balance: ${record['opening_balance']:,.2f}")
        print(f"Income: ${record['income']:,.2f}")
        print(f"Expenses: ${record['expenses']:,.2f}")
        print(f"Closing Balance: ${record['closing_balance']:,.2f}")
        print(f"Status: {record['balance_status']}") 