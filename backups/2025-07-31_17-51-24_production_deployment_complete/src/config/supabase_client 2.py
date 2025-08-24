from supabase import create_client, Client
from config import config
import os

def get_supabase_client() -> Client:
    """
    Get a configured Supabase client instance.
    Uses the configuration from config.py instead of environment variables.
    """
    env = os.getenv('FLASK_ENV', 'development')
    current_config = config.get(env, config['default'])()
    
    return create_client(
        current_config.SUPABASE_URL,
        current_config.SUPABASE_ANON_KEY
    ) 