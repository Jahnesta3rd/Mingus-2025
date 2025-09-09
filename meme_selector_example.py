#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme Selector Usage Examples
Simple examples showing how to use the meme selection system
"""

from meme_selector import MemeSelector, MemeObject
from datetime import datetime, timedelta
import json

def basic_usage_example():
    """
    Basic usage example - the simplest way to use the meme selector
    """
    print("🎭 Basic Usage Example")
    print("=" * 40)
    
    # Initialize the selector (uses default database path)
    selector = MemeSelector()
    
    # Get a meme for user ID 1
    user_id = 1
    meme = selector.select_best_meme(user_id)
    
    if meme:
        print(f"✅ Selected meme for user {user_id}:")
        print(f"   📸 Image: {meme.image_url}")
        print(f"   📝 Caption: {meme.caption}")
        print(f"   🏷️  Category: {meme.category}")
        print(f"   ♿ Alt Text: {meme.alt_text}")
    else:
        print("❌ No meme available")
    
    return meme

def day_specific_example():
    """
    Example showing how day of week affects meme selection
    """
    print("\n📅 Day-Specific Selection Example")
    print("=" * 40)
    
    selector = MemeSelector()
    user_id = 2
    
    # Test different days of the week
    days = [
        (0, "Sunday", "faith"),
        (1, "Monday", "work_life"), 
        (2, "Tuesday", "health"),
        (3, "Wednesday", "housing"),
        (4, "Thursday", "transportation"),
        (5, "Friday", "relationships"),
        (6, "Saturday", "family")
    ]
    
    for day_num, day_name, expected_category in days:
        # Create a date for this day of the week
        test_date = datetime(2024, 1, 7 + day_num)  # Start from Sunday
        
        meme = selector.select_best_meme(user_id, test_date)
        
        if meme:
            print(f"📅 {day_name}: {meme.category} - '{meme.caption[:50]}...'")
        else:
            print(f"📅 {day_name}: No meme available")

def user_journey_example():
    """
    Example showing a complete user journey with multiple selections
    """
    print("\n👤 User Journey Example")
    print("=" * 40)
    
    selector = MemeSelector()
    user_id = 3
    
    print(f"Simulating user {user_id} selecting multiple memes...")
    
    selected_memes = []
    for i in range(5):
        meme = selector.select_best_meme(user_id)
        if meme:
            selected_memes.append(meme)
            print(f"   {i+1}. {meme.category}: '{meme.caption[:40]}...'")
        else:
            print(f"   {i+1}. No meme available")
    
    # Show user statistics
    stats = selector.get_user_meme_stats(user_id)
    print(f"\n📊 User {user_id} Statistics:")
    print(f"   Total views: {stats.get('total_views', 0)}")
    print(f"   Recent views (30 days): {stats.get('recent_views_30_days', 0)}")
    print(f"   Most viewed category: {stats.get('most_viewed_category', 'None')}")
    
    if 'category_breakdown' in stats:
        print("   Category breakdown:")
        for category, count in stats['category_breakdown'].items():
            print(f"     {category}: {count} views")

def error_handling_example():
    """
    Example showing error handling capabilities
    """
    print("\n🛡️  Error Handling Example")
    print("=" * 40)
    
    # Test with invalid database path
    print("Testing with invalid database path...")
    invalid_selector = MemeSelector("/invalid/path/database.db")
    meme = invalid_selector.select_best_meme(1)
    
    if meme is None:
        print("✅ Correctly handled database error - returned None")
    else:
        print("❌ Should have returned None for database error")
    
    # Test with valid selector
    print("\nTesting with valid database...")
    valid_selector = MemeSelector()
    meme = valid_selector.select_best_meme(1)
    
    if meme:
        print("✅ Successfully selected meme from valid database")
    else:
        print("ℹ️  No meme available (this is normal if database is empty)")

def analytics_example():
    """
    Example showing how analytics are logged
    """
    print("\n📈 Analytics Example")
    print("=" * 40)
    
    selector = MemeSelector()
    user_id = 4
    
    print("Selecting memes and checking analytics logs...")
    print("(Check meme_analytics.log file for detailed analytics)")
    
    # Select a few memes to generate analytics
    for i in range(3):
        meme = selector.select_best_meme(user_id)
        if meme:
            print(f"   Selected: {meme.category} - {meme.caption[:30]}...")
    
    print("\nAnalytics data includes:")
    print("   - User ID")
    print("   - Meme ID and category")
    print("   - Selection reason (preferred/fallback)")
    print("   - Day of week")
    print("   - Timestamp")

def caching_example():
    """
    Example demonstrating the caching mechanism
    """
    print("\n⚡ Caching Example")
    print("=" * 40)
    
    selector = MemeSelector()
    user_id = 5
    
    print("Testing caching performance...")
    
    import time
    
    # First call (populates cache)
    start_time = time.time()
    meme1 = selector.select_best_meme(user_id)
    first_call_time = time.time() - start_time
    
    # Second call (uses cache)
    start_time = time.time()
    meme2 = selector.select_best_meme(user_id)
    second_call_time = time.time() - start_time
    
    print(f"   First call: {first_call_time*1000:.2f}ms")
    print(f"   Second call: {second_call_time*1000:.2f}ms")
    
    if second_call_time < first_call_time:
        print("✅ Caching appears to be working (second call faster)")
    else:
        print("ℹ️  Caching effect may not be visible with small dataset")

def integration_example():
    """
    Example showing integration with a web application
    """
    print("\n🌐 Web Integration Example")
    print("=" * 40)
    
    def get_meme_for_user_api(user_id: int) -> dict:
        """
        Example API endpoint function that could be used in a web app
        """
        selector = MemeSelector()
        meme = selector.select_best_meme(user_id)
        
        if meme:
            return {
                'success': True,
                'meme': {
                    'id': meme.id,
                    'image_url': meme.image_url,
                    'caption': meme.caption,
                    'category': meme.category,
                    'alt_text': meme.alt_text
                }
            }
        else:
            return {
                'success': False,
                'error': 'No memes available'
            }
    
    # Test the API function
    user_id = 6
    result = get_meme_for_user_api(user_id)
    
    print(f"API Response for user {user_id}:")
    print(json.dumps(result, indent=2))

def main():
    """
    Run all examples
    """
    print("🎭 Mingus Meme Selector - Usage Examples")
    print("=" * 60)
    
    try:
        # Run all examples
        basic_usage_example()
        day_specific_example()
        user_journey_example()
        error_handling_example()
        analytics_example()
        caching_example()
        integration_example()
        
        print("\n✅ All examples completed successfully!")
        print("\n💡 Tips for using the meme selector:")
        print("   - Always check if the returned meme is None")
        print("   - The system automatically handles day-of-week logic")
        print("   - Analytics are logged to meme_analytics.log")
        print("   - Caching improves performance for repeated calls")
        print("   - Fallback logic ensures users always get content")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Make sure the database is properly set up!")

if __name__ == "__main__":
    main()
