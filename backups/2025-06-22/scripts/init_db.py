import sys
import os
from supabase.client import create_client

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

def init_personalization_analytics(supabase_client):
    """Initialize the personalization analytics table."""
    try:
        # Create personalization analytics table using REST API
        print("Creating personalization analytics table...")
        
        # First, check if table exists
        try:
            supabase_client.table('personalization_analytics').select('*').limit(1).execute()
            print("✓ Table already exists")
            return True
        except Exception:
            pass  # Table doesn't exist, continue with creation
        
        # Create table with basic structure
        supabase_client.table('personalization_analytics').upsert({
            'id': 1,  # Dummy record that will be deleted
            'session_id': '00000000-0000-0000-0000-000000000000',
            'financial_challenge': 'emergency_savings',
            'motivation': 'family_goals',
            'converted': False,
            'timestamp': '2024-01-01T00:00:00Z'
        }).execute()
        
        # Delete the dummy record
        supabase_client.table('personalization_analytics').delete().eq('id', 1).execute()
        
        print("✓ Table created")
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating personalization analytics: {str(e)}")
        return False

def main():
    print("Starting database initialization...")
    
    # Get configuration and initialize Supabase client with service role key
    current_config = config.get('development', config['default'])()
    supabase_client = create_client(
        supabase_url=current_config.SUPABASE_URL,
        supabase_key=current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    
    success = init_personalization_analytics(supabase_client)
    
    if success:
        print("\nDatabase initialization completed successfully! ✓")
        sys.exit(0)
    else:
        print("\nDatabase initialization failed. Please check the logs above. ❌")
        sys.exit(1)

if __name__ == "__main__":
    main() 