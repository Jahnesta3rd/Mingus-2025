import os
import sys
from datetime import date, timedelta
from supabase import create_client, Client
from config import DevelopmentConfig

def get_future_date(days_ahead):
    """Get a date that's always in the future"""
    return (date.today() + timedelta(days=days_ahead)).isoformat()

def test_anon_access():
    """Test anonymous access to important_dates table"""
    try:
        # Initialize Supabase client with anon key
        config = DevelopmentConfig()
        anon_client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
        
        print("\nTesting anonymous access to important_dates table:")
        print("=" * 80)
        
        # 1. Test SELECT
        print("\nTesting SELECT...")
        try:
            result = anon_client.table("important_dates").select("*").execute()
            print("❌ SELECT succeeded when it should have failed!")
            print(f"Retrieved {len(result.data)} records")
        except Exception as e:
            print("✅ SELECT properly denied")
            print(f"Error: {str(e)}")
            
        # 2. Test INSERT
        print("\nTesting INSERT...")
        try:
            test_date = {
                "user_id": "00000000-0000-0000-0000-000000000000",
                "date_type_id": "00000000-0000-0000-0000-000000000000",
                "event_date": get_future_date(30),
                "description": "Test Anonymous Insert"
            }
            result = anon_client.table("important_dates").insert(test_date).execute()
            print("❌ INSERT succeeded when it should have failed!")
        except Exception as e:
            print("✅ INSERT properly denied")
            print(f"Error: {str(e)}")
            
        # 3. Test UPDATE
        print("\nTesting UPDATE...")
        try:
            result = anon_client.table("important_dates").update({"description": "Hacked!"}).execute()
            print("❌ UPDATE succeeded when it should have failed!")
        except Exception as e:
            print("✅ UPDATE properly denied")
            print(f"Error: {str(e)}")
            
        # 4. Test DELETE
        print("\nTesting DELETE...")
        try:
            result = anon_client.table("important_dates").delete().execute()
            print("❌ DELETE succeeded when it should have failed!")
        except Exception as e:
            print("✅ DELETE properly denied")
            print(f"Error: {str(e)}")
            
        return True
        
    except Exception as e:
        print(f"Error during anonymous access test: {str(e)}")
        return False

if __name__ == "__main__":
    if not test_anon_access():
        sys.exit(1) 