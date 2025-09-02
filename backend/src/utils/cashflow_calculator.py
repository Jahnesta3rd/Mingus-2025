from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid
from src.config.supabase_client import get_supabase_client

def calculate_daily_cashflow(user_id: str, initial_balance: float, start_date: str = None) -> List[Dict[str, Any]]:
    """
    Calculate daily cash flow for the next 12 months based on financial profile, actual expenses, and goals.
    """
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = current_date + timedelta(days=365)
    try:
        print(f"Calculating cashflow for user {user_id} from {start_date} to {end_date.strftime('%Y-%m-%d')}")
        supabase = get_supabase_client()
        # Delete existing projections
        supabase.table('daily_cashflow') \
            .delete() \
            .eq('user_id', user_id) \
            .gte('forecast_date', start_date) \
            .lte('forecast_date', end_date.strftime("%Y-%m-%d")) \
            .execute()
        # --- Fetch financial profile (income, etc.) ---
        profile_resp = supabase.table('user_financial_profiles').select('*').eq('user_id', user_id).single().execute()
        profile = profile_resp.data or {}
        # --- Fetch all expense schedules ---
        expense_response = supabase.table('user_expense_due_dates').select('*').eq('user_id', user_id).execute()
        expense_schedules = expense_response.data or []
        # --- Fetch actual expense items (recurring, variable) ---
        expense_items_resp = supabase.table('user_expense_items').select('*').eq('user_id', user_id).execute()
        expense_items = expense_items_resp.data or []
        # --- Fetch financial goals (future expenses) ---
        goals_resp = supabase.table('user_financial_goals').select('*').eq('user_id', user_id).execute()
        goals = goals_resp.data or []
        # --- Build daily transactions ---
        daily_transactions = {}
        # Income: add recurring income from profile
        income = profile.get('income', 0)
        income_frequency = profile.get('income_frequency', 'monthly')
        # Convert income to daily
        if income_frequency == 'monthly':
            daily_income = income / 30.44
        elif income_frequency == 'bi-weekly':
            daily_income = (income * 26) / 365
        elif income_frequency == 'weekly':
            daily_income = (income * 52) / 365
        else:
            daily_income = income / 30.44
        # Add daily income to each day
        temp_date = current_date
        while temp_date <= end_date:
            date_str = temp_date.strftime("%Y-%m-%d")
            if date_str not in daily_transactions:
                daily_transactions[date_str] = {'income': 0, 'expenses': 0}
            daily_transactions[date_str]['income'] += daily_income
            temp_date += timedelta(days=1)
        # Expenses: add scheduled and actual expenses
        for expense in expense_schedules:
            due_day = int(expense.get('due_date', 1))
            amount = float(expense.get('amount', 0))
            freq = expense.get('frequency', 'monthly')
            temp_date = current_date
            while temp_date <= end_date:
                if temp_date.day == due_day:
                    date_str = temp_date.strftime("%Y-%m-%d")
                    if date_str not in daily_transactions:
                        daily_transactions[date_str] = {'income': 0, 'expenses': 0}
                    daily_transactions[date_str]['expenses'] += amount
                temp_date += timedelta(days=1)
        # Add variable/one-off expenses from expense_items
        for item in expense_items:
            for field, val in item.items():
                if field.endswith('_expense') and val:
                    # Assume monthly for now
                    temp_date = current_date
                    while temp_date <= end_date:
                        if temp_date.day == 1:
                            date_str = temp_date.strftime("%Y-%m-%d")
                            if date_str not in daily_transactions:
                                daily_transactions[date_str] = {'income': 0, 'expenses': 0}
                            daily_transactions[date_str]['expenses'] += float(val)
                        temp_date += timedelta(days=1)
        # --- Factor in financial goals as future expenses ---
        for goal in goals:
            target_date = goal.get('target_date')
            target_amount = float(goal.get('target_amount', 0))
            if target_date and target_amount > 0:
                # Add as a one-time expense on the target date
                if target_date not in daily_transactions:
                    daily_transactions[target_date] = {'income': 0, 'expenses': 0}
                daily_transactions[target_date]['expenses'] += target_amount
        # --- Calculate daily balances ---
        cashflow_records = []
        running_balance = initial_balance
        temp_date = current_date
        while temp_date <= end_date:
            date_str = temp_date.strftime("%Y-%m-%d")
            daily_data = daily_transactions.get(date_str, {'income': 0, 'expenses': 0})
            income = daily_data['income']
            expenses = daily_data['expenses']
            opening_balance = running_balance
            net_change = income - expenses
            closing_balance = opening_balance + net_change
            if closing_balance >= 5000:
                balance_status = 'healthy'
            elif closing_balance >= 0:
                balance_status = 'warning'
            else:
                balance_status = 'danger'
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
            running_balance = closing_balance
            temp_date += timedelta(days=1)
        # Batch insert
        batch_size = 50
        for i in range(0, len(cashflow_records), batch_size):
            batch = cashflow_records[i:i + batch_size]
            try:
                supabase.table('daily_cashflow').insert(batch).execute()
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