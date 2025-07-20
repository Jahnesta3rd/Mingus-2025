"""
Field mapping utilities for expense categories and other form fields.
Ensures consistency between frontend snake_case and backend field names.
"""

# Standard expense field definitions
EXPENSE_FIELDS = [
    'rent_or_mortgage_expense',
    'utilities_expense', 
    'auto_payment_expense',
    'auto_insurance_expense',
    'auto_gas_expense',
    'bus_fare_expense',
    'rideshare_expense',
    'health_insurance_expense',
    'healthcare_expense',
    'grocery_expense',
    'restaurant_meals_expense',
    'personal_care_expense',
    'selfcare_expense',
    'daycare_expense',
    'child_support_expense',
    'cash_to_family_expense',
    'credit_card1_expense',
    'credit_card2_expense',
    'credit_card3_expense',
    'loan_1_expense',
    'loan_2_expense',
    'loan_3_expense',
    'subscriptions_expense',
    'mobile_phone_expense',
    'entertainment_expense',
    'gift_others_expense',
    'career_expense',
    'pet_expense',
    'fraternity_sorority_expense'
]

# Text fields (names, descriptions, etc.)
TEXT_FIELDS = [
    'credit_card1_name',
    'credit_card2_name', 
    'credit_card3_name',
    'loan_1_name',
    'loan_2_name',
    'loan_3_name'
]

# Field categories for grouping and calculations
EXPENSE_CATEGORIES = {
    'essential': [
        'rent_or_mortgage_expense',
        'utilities_expense',
        'auto_payment_expense', 
        'auto_insurance_expense',
        'auto_gas_expense',
        'health_insurance_expense'
    ],
    'living': [
        'grocery_expense',
        'restaurant_meals_expense',
        'personal_care_expense',
        'daycare_expense',
        'child_support_expense',
        'cash_to_family_expense'
    ],
    'debt': [
        'credit_card1_expense',
        'credit_card2_expense',
        'credit_card3_expense',
        'loan_1_expense',
        'loan_2_expense',
        'loan_3_expense',
        'subscriptions_expense',
        'mobile_phone_expense'
    ],
    'discretionary': [
        'entertainment_expense',
        'gift_others_expense',
        'career_expense',
        'pet_expense',
        'fraternity_sorority_expense',
        'selfcare_expense',
        'healthcare_expense',
        'bus_fare_expense',
        'rideshare_expense'
    ]
}

def get_frequency_field(expense_field):
    """Get the corresponding frequency field name for an expense field."""
    if not expense_field.endswith('_expense'):
        return None
    return expense_field.replace('_expense', '_frequency')

def get_due_date_field(expense_field):
    """Get the corresponding due date field name for an expense field."""
    if not expense_field.endswith('_expense'):
        return None
    return expense_field.replace('_expense', '_due_date')

def get_monthly_field(expense_field):
    """Get the corresponding monthly calculation field name for an expense field."""
    if not expense_field.endswith('_expense'):
        return None
    return expense_field.replace('_expense', '_monthly')

def validate_expense_data(data):
    """
    Validate expense data structure and field names.
    
    Args:
        data (dict): Expense data from frontend
        
    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []
    
    # Check required fields
    if 'starting_balance' not in data:
        errors.append('Starting balance is required')
    
    if 'expenses' not in data:
        errors.append('Expenses data is required')
        return False, errors
    
    # Validate expense fields
    expenses = data.get('expenses', {})
    for field, value in expenses.items():
        if field in EXPENSE_FIELDS:
            if isinstance(value, dict):
                # Check required expense object fields
                if 'amount' not in value:
                    errors.append(f'Amount is required for {field}')
                if 'frequency' not in value:
                    errors.append(f'Frequency is required for {field}')
            else:
                errors.append(f'{field} must be an object with amount and frequency')
        elif field in TEXT_FIELDS:
            # Text fields can be strings
            if not isinstance(value, str):
                errors.append(f'{field} must be a string')
        else:
            # Unknown field
            errors.append(f'Unknown field: {field}')
    
    return len(errors) == 0, errors

def normalize_expense_data(data):
    """
    Normalize expense data to ensure consistent field names and structure.
    
    Args:
        data (dict): Raw expense data from frontend
        
    Returns:
        dict: Normalized expense data
    """
    normalized = {
        'starting_balance': data.get('starting_balance', 0),
        'expenses': {},
        'timestamp': data.get('timestamp')
    }
    
    expenses = data.get('expenses', {})
    for field, value in expenses.items():
        if field in EXPENSE_FIELDS + TEXT_FIELDS:
            normalized['expenses'][field] = value
    
    return normalized

def calculate_monthly_totals(expenses_data):
    """
    Calculate monthly totals for each expense category.
    
    Args:
        expenses_data (dict): Normalized expenses data
        
    Returns:
        dict: Category totals and overall total
    """
    totals = {
        'essential': 0,
        'living': 0, 
        'debt': 0,
        'discretionary': 0,
        'total': 0
    }
    
    expenses = expenses_data.get('expenses', {})
    
    for category, fields in EXPENSE_CATEGORIES.items():
        for field in fields:
            if field in expenses and isinstance(expenses[field], dict):
                monthly_amount = expenses[field].get('monthly', 0)
                totals[category] += float(monthly_amount or 0)
    
    totals['total'] = sum(totals[cat] for cat in ['essential', 'living', 'debt', 'discretionary'])
    
    return totals

def to_monthly_amount(amount, frequency):
    """
    Convert an amount to monthly equivalent based on frequency.
    
    Args:
        amount (float): The amount
        frequency (str): The frequency (weekly, bi-weekly, monthly, quarterly, etc.)
        
    Returns:
        float: Monthly equivalent amount
    """
    if not amount or not frequency:
        return 0
    
    amount = float(amount)
    
    frequency_map = {
        'weekly': amount * 52 / 12,
        'bi-weekly': amount * 26 / 12,
        'semi-monthly': amount * 2,
        'monthly': amount,
        'quarterly': amount / 3,
        'semi-annually': amount / 6,
        'annually': amount / 12
    }
    
    return round(frequency_map.get(frequency.lower(), amount), 2)

def format_currency(amount):
    """
    Format amount as currency string.
    
    Args:
        amount (float): The amount to format
        
    Returns:
        str: Formatted currency string
    """
    if not amount:
        return '$0.00'
    return f'${float(amount):,.2f}' 