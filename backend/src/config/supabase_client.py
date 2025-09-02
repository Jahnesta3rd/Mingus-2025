from supabase import create_client, Client
import os

def get_supabase_client() -> Client:
    """
    Get a configured Supabase client instance.
    Uses environment variables for configuration.
    """
    supabase_url = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
    supabase_key = os.getenv('SUPABASE_KEY', 'your-supabase-anon-key')
    
    return create_client(supabase_url, supabase_key) 