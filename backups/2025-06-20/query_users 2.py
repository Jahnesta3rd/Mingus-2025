from supabase import create_client
from config import config

def get_users():
    # Get configuration
    env = 'development'
    current_config = config.get(env, config['default'])()
    
    # Initialize Supabase client with service role key
    supabase = create_client(
        current_config.SUPABASE_URL,
        current_config.SUPABASE_SERVICE_ROLE_KEY  # Use service role key instead
    )
    
    # Query users table
    try:
        # Try auth.users() first
        print("\nTrying auth.users():")
        try:
            response = supabase.auth.admin.list_users()
            print("\nExisting Users (from auth):")
            for user in response:
                print(f"ID: {user.id}")
                print(f"Email: {user.email}")
                print("-" * 50)
        except Exception as auth_e:
            print(f"Error querying auth.users: {str(auth_e)}")
        
        # Also try the users table
        print("\nTrying users table:")
        response = supabase.table('users').select('id, email').execute()
        print("\nExisting Users (from table):")
        for user in response.data:
            print(f"ID: {user['id']}")
            print(f"Email: {user['email']}")
            print("-" * 50)
        return response.data
    except Exception as e:
        print(f"Error querying users: {str(e)}")
        raise e

if __name__ == "__main__":
    get_users() 