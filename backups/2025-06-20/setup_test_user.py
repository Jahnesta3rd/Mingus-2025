from supabase import create_client
from config import DevelopmentConfig

def setup_test_user():
    """Set up a test user in Supabase"""
    try:
        # Initialize Supabase admin client
        config = DevelopmentConfig()
        admin_client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        
        # Create test user
        user_data = {
            "email": "test1@example.com",
            "password": "test123",
            "email_confirm": True
        }
        
        # First try to delete the user if it exists
        delete_query = """
        DELETE FROM auth.users WHERE email = 'test1@example.com';
        """
        
        try:
            admin_client.postgrest.rpc('exec_sql', {'query': delete_query}).execute()
            print("Cleaned up existing test user")
        except:
            pass
        
        # Create the user
        response = admin_client.auth.admin.create_user(user_data)
        user_id = response.user.id
        print(f"Created test user with ID: {user_id}")
        
        return True
        
    except Exception as e:
        print(f"Error setting up test user: {str(e)}")
        return False

if __name__ == "__main__":
    setup_test_user() 