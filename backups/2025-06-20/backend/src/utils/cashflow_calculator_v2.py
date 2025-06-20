from datetime import datetime, date, timedelta
from typing import Dict, List, Any

def calculate_daily_cashflow(user_id: str, initial_balance: float = 0, start_date: str = None) -> List[Dict[str, Any]]:
    """
    Calculate daily cashflow for a user.
    This is a mock implementation for testing.
    """
    if not start_date:
        start_date = datetime.now().date().isoformat()
    
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    cashflow = []
    
    # Generate mock cashflow for 30 days
    balance = initial_balance
    for i in range(30):
        current_date = start + timedelta(days=i)
        
        # Mock daily change
        daily_change = 100 if i % 2 == 0 else -50
        balance += daily_change
        
        cashflow.append({
            "date": current_date.isoformat(),
            "balance": balance,
            "daily_change": daily_change
        })
    
    return cashflow 