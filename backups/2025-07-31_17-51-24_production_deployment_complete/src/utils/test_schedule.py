from enhanced_schedule import generate_schedule, get_paycheck_schedule
from datetime import datetime
from pprint import pprint

def run_tests():
    print("\n=== Testing Enhanced Schedule Generator ===\n")
    
    # Test 1: Basic Bi-weekly Paycheck
    print("Test 1: Bi-weekly Paycheck Schedule (Next 3 months)")
    paychecks = generate_schedule(
        "2024-01-01",  # Start from New Year's Day (a holiday)
        frequency="bi-weekly",
        months=3,
        preferred_days=[4]  # Prefer Fridays
    )
    print("\nBi-weekly paychecks (should move from holiday to business day):")
    pprint(paychecks)

    # Test 2: Monthly Rent Payment
    print("\nTest 2: Monthly Rent Schedule (Next 3 months)")
    rent_dates = generate_schedule(
        "2024-01-31",  # Start from January 31st
        frequency="monthly",
        months=3,
        preferred_days=None  # No day preference, just business days
    )
    print("\nMonthly rent dates (should handle end of month properly):")
    pprint(rent_dates)

    # Test 3: Weekly Allowance
    print("\nTest 3: Weekly Allowance Schedule (Next 2 months)")
    allowance_dates = generate_schedule(
        "2024-02-19",  # Start from Presidents' Day
        frequency="weekly",
        months=2,
        preferred_days=[2]  # Prefer Wednesdays
    )
    print("\nWeekly allowance dates (should handle holiday):")
    pprint(allowance_dates)

    # Test 4: Quarterly Business Payment
    print("\nTest 4: Quarterly Payment Schedule (Next 12 months)")
    quarterly_dates = generate_schedule(
        "2024-01-01",
        frequency="quarterly",
        months=12,
        preferred_days=None
    )
    print("\nQuarterly payment dates:")
    pprint(quarterly_dates)

    # Test 5: Different Preferred Days
    print("\nTest 5: Monthly Schedule with Monday Preference")
    monday_dates = generate_schedule(
        "2024-01-01",
        frequency="monthly",
        months=3,
        preferred_days=[0]  # Prefer Mondays
    )
    print("\nMonthly dates (Monday preference):")
    pprint(monday_dates)

if __name__ == "__main__":
    run_tests() 