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
    date_str = date.strftime("%Y-%m-%d")
    if date.weekday() >= 5:  # Weekend
        return False
    return date_str not in HOLIDAYS

def get_next_business_day(date: datetime) -> datetime:
    """Get the next business day after a given date."""
    next_day = date
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    return next_day

def generate_schedule(
    start_date_str: str,
    frequency: str,
    months: int = 12,
    adjust_for_business_days: bool = True,
    preferred_days: Optional[List[int]] = None
) -> List[str]:
    """Generate a schedule of dates."""
    start_date = parse(start_date_str)
    end_date = start_date + timedelta(days=months * 30.44)
    
    if preferred_days is None:
        preferred_days = [4]  # Default to Friday
    
    weekdays = [
        day for day in [MO, TU, WE, TH, FR] 
        if day.weekday in preferred_days
    ]
    
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
    
    settings = freq_settings[frequency].copy()
    settings.update({
        'dtstart': start_date,
        'until': end_date
    })
    
    dates = list(rrule(**settings))
    
    if adjust_for_business_days:
        adjusted_dates = []
        for date in dates:
            if not is_business_day(date):
                if frequency in ['monthly', 'quarterly', 'annually']:
                    next_business = get_next_business_day(date)
                    adjusted_date = next_business
                else:
                    adjusted_date = get_next_business_day(date)
            else:
                adjusted_date = date
            adjusted_dates.append(adjusted_date)
        dates = adjusted_dates
    
    return [dt.strftime("%Y-%m-%d") for dt in dates]

def test_date_generation():
    """Test the date generation functionality"""
    start_date = datetime.now().strftime("%Y-%m-%d")
    
    print("\n=== Testing Date Generation ===\n")
    
    # Test 1: Bi-weekly schedule
    print("Test 1: Bi-weekly Schedule (Next 3 months)")
    dates = generate_schedule(
        start_date_str=start_date,
        frequency="bi-weekly",
        months=3,
        preferred_days=[4]  # Friday
    )
    print("\nBi-weekly dates:")
    for date in dates:
        print(f"  {date}")
    
    # Test 2: Monthly schedule
    print("\nTest 2: Monthly Schedule (Next 3 months)")
    dates = generate_schedule(
        start_date_str=start_date,
        frequency="monthly",
        months=3
    )
    print("\nMonthly dates:")
    for date in dates:
        print(f"  {date}")
    
    # Test 3: Weekly schedule
    print("\nTest 3: Weekly Schedule (Next 1 month)")
    dates = generate_schedule(
        start_date_str=start_date,
        frequency="weekly",
        months=1,
        preferred_days=[2]  # Wednesday
    )
    print("\nWeekly dates:")
    for date in dates:
        print(f"  {date}")
    
    # Test 4: Quarterly schedule
    print("\nTest 4: Quarterly Schedule (Next 12 months)")
    dates = generate_schedule(
        start_date_str=start_date,
        frequency="quarterly",
        months=12
    )
    print("\nQuarterly dates:")
    for date in dates:
        print(f"  {date}")

if __name__ == '__main__':
    test_date_generation() 