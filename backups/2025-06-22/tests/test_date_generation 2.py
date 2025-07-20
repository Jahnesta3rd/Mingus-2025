from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.src.utils.enhanced_schedule import generate_schedule

def test_date_generation():
    """Test the core date generation functionality"""
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