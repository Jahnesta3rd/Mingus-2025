from dotenv import load_dotenv
import os
from supabase import create_client, Client
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

def create_test_user():
    # Initialize Supabase client with service role key
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not service_role_key:
        raise EnvironmentError("Missing required environment variables")
    
    supabase = create_client(supabase_url, service_role_key)
    
    # Test user details
    email = "test_user_2@example.com"
    password = "TestPassword123!"
    full_name = "Test User 2"
    
    try:
        # Create auth user
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            raise Exception("Failed to create auth user")
        
        user_id = auth_response.user.id
        
        # Insert into users table
        user_data = {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "created_at": datetime.utcnow().isoformat()
        }
        
        user_response = supabase.table("users").insert(user_data).execute()
        
        print(f"Created user successfully:")
        print(f"User ID: {user_id}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        
        # Create test expenses
        expenses = [
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "expense_type": "rent",
                "amount": 1500,
                "due_date": 1,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "expense_type": "utilities",
                "amount": 200,
                "due_date": 15,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        expense_response = supabase.table("user_expense_due_dates").insert(expenses).execute()
        print(f"\nCreated {len(expenses)} test expenses")
        
        return user_id
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    user_id = create_test_user()
    if user_id:
        print("\nTest setup completed successfully!")
    else:
        print("\nFailed to complete test setup") 