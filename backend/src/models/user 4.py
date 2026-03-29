from ..config.supabase import get_supabase
from datetime import datetime
import os
from config import config

# Get configuration based on environment
env = os.getenv('FLASK_ENV', 'development')
current_config = config.get(env, config['default'])

class User:
    @staticmethod
    def get_by_id(user_id):
        """
        Retrieve a user by their ID.
        """
        supabase = get_supabase()
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def create_user(email, password, full_name):
        """
        Create a new user in Supabase.
        """
        # Get service role key from config
        service_role_key = current_config.get_service_role_key()
        if not service_role_key:
            raise EnvironmentError(
                "Missing service role key in configuration"
            )
        
        # Create admin client with service role key
        admin_supabase = get_supabase(service_role_key)
        
        # First create auth user
        auth_response = admin_supabase.auth.sign_up({
            'email': email,
            'password': password
        })
        
        if auth_response.user:
            # Then store additional user data using service role client
            user_data = {
                'id': auth_response.user.id,
                'email': email,
                'full_name': full_name,
                'created_at': datetime.utcnow().isoformat()
            }
            
            response = admin_supabase.table('users').insert(user_data).execute()
            return response.data[0] if response.data else None
        return None

    @staticmethod
    def update_user(user_id, update_data):
        """
        Update user information.
        """
        supabase = get_supabase()
        response = supabase.table('users').update(update_data).eq('id', user_id).execute()
        return response.data[0] if response.data else None 