from datetime import datetime, timedelta
from dateutil.rrule import rrule, WEEKLY, MONTHLY, YEARLY, MO, TU, WE, TH, FR
from dateutil.parser import parse
from typing import List, Optional

# US Federal Holidays (2024-2025 as example)
HOLIDAYS = [
    "2024-01-01",  # New Year's Day
    "2024-01-15",  # Martin Luther King Jr. Day
    "2024-02-19",  # Presidents' Day
    "2024-05-27",  # Memorial Day
    "2024-06-19",  # Juneteenth
    "2024-07-04",  # Independence Day
    "2024-09-02",  # Labor Day
    "2024-10-14",  # Columbus Day
    "2024-11-11",  # Veterans Day
    "2024-11-28",  # Thanksgiving Day
    "2024-12-25",  # Christmas Day
    "2025-01-01",  # New Year's Day
]

def is_business_day(date: datetime) -> bool:
    """Check if a given date is a business day (Monday-Friday, not a holiday)."""
    # Convert date to string format for holiday checking
    date_str = date.strftime("%Y-%m-%d")
    
    # Check if it's a weekend
    if date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
    
    # Check if it's a holiday
    return date_str not in HOLIDAYS

def get_next_business_day(date: datetime) -> datetime:
    """Get the next business day after a given date."""
    next_day = date
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day

def get_previous_business_day(date: datetime) -> datetime:
    """Get the previous business day before a given date."""
    prev_day = date
    while not is_business_day(prev_day):
        prev_day -= timedelta(days=-1)
    return prev_day

def generate_schedule(
    start_date_str: str,
    frequency: str,
    months: int = 12,
    adjust_for_business_days: bool = True,
    preferred_days: Optional[List[int]] = None  # 0=Monday, 4=Friday
) -> List[str]:
    """
    Generate a schedule of dates based on frequency.
    
    Args:
        start_date_str: Start date in YYYY-MM-DD format
        frequency: One of 'weekly', 'bi-weekly', 'monthly', 'quarterly', 'annually'
        months: Number of months to generate dates for
        adjust_for_business_days: Whether to adjust dates to fall on business days
        preferred_days: List of preferred weekdays (0=Monday, 4=Friday)
    
    Returns:
        List of dates in YYYY-MM-DD format
    """
    start_date = parse(start_date_str)
    end_date = start_date + timedelta(days=months * 30.44)  # Average month length
    
    # Set default preferred days if none provided
    if preferred_days is None:
        preferred_days = [4]  # Default to Friday
    
    # Create weekday parameters for rrule
    weekdays = [
        day for day in [MO, TU, WE, TH, FR] 
        if day.weekday in preferred_days
    ]
    
    # Configure frequency settings
    freq_settings = {
        'weekly': {
            'freq': WEEKLY,
            'interval': 1,
            'byweekday': weekdays if weekdays else None
        },
        'bi-weekly': {
            'freq': WEEKLY,
            'interval': 2,
            'byweekday': weekdays if weekdays else None
        },
        'monthly': {
            'freq': MONTHLY,
            'interval': 1
        },
        'quarterly': {
            'freq': MONTHLY,
            'interval': 3
        },
        'annually': {
            'freq': YEARLY,
            'interval': 1
        }
    }
    
    # Get base settings for the frequency
    settings = freq_settings[frequency].copy()
    settings.update({
        'dtstart': start_date,
        'until': end_date
    })
    
    # Generate dates
    dates = list(rrule(**settings))
    
    # Adjust for business days if requested
    if adjust_for_business_days:
        adjusted_dates = []
        for date in dates:
            if not is_business_day(date):
                # For monthly/quarterly/annual frequencies, try to maintain end of month
                if frequency in ['monthly', 'quarterly', 'annually']:
                    next_business = get_next_business_day(date)
                    prev_business = get_previous_business_day(date)
                    
                    # If date is closer to end of month, use previous business day
                    if date.day >= 28:
                        adjusted_date = prev_business
                    else:
                        adjusted_date = next_business
                else:
                    # For weekly/bi-weekly, always move forward
                    adjusted_date = get_next_business_day(date)
            else:
                adjusted_date = date
            adjusted_dates.append(adjusted_date)
        dates = adjusted_dates
    
    # Convert to string format
    return [dt.strftime("%Y-%m-%d") for dt in dates]

def get_paycheck_schedule(
    start_date_str: str,
    frequency: str = 'bi-weekly',
    preferred_weekday: int = 4  # Default to Friday
) -> List[str]:
    """
    Generate a paycheck schedule.
    
    Args:
        start_date_str: Start date in YYYY-MM-DD format
        frequency: 'weekly' or 'bi-weekly'
        preferred_weekday: 0=Monday through 4=Friday
    
    Returns:
        List of paycheck dates in YYYY-MM-DD format
    """
    return generate_schedule(
        start_date_str,
        frequency,
        months=12,
        adjust_for_business_days=True,
        preferred_days=[preferred_weekday]
    )

# Example usage:
if __name__ == "__main__":
    # Generate a bi-weekly paycheck schedule starting from today
    today = datetime.now().strftime("%Y-%m-%d")
    paychecks = get_paycheck_schedule(today)
    print("Paycheck Schedule:")
    for date in paychecks:
        print(date) 