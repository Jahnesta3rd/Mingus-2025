from dotenv import load_dotenv
import os
from supabase import create_client, Client
import uuid
import json
from backend.src.models.user import User

# Load environment variables
load_dotenv()

# Print environment variables (without sensitive data)
print("Environment variables check:")
print(f"SUPABASE_URL exists: {'SUPABASE_URL' in os.environ}")
print(f"SUPABASE_ANON_KEY exists: {'SUPABASE_ANON_KEY' in os.environ}")
print(f"SUPABASE_SERVICE_ROLE_KEY exists: {'SUPABASE_SERVICE_ROLE_KEY' in os.environ}")

# Initialize Supabase client
try:
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )
    
    # Create test user using the User class
    test_user_email = 'test@example.com'
    test_user_password = 'TestPassword123!'  # Strong password for testing
    test_user_name = 'Test User'
    
    print("\nCreating test user via User class...")
    try:
        # Try to create the user
        user_data = User.create_user(test_user_email, test_user_password, test_user_name)
        if user_data:
            test_user_id = user_data['id']
            print(f"Created user with ID: {test_user_id}")
        else:
            # User might already exist, try to sign in
            print("User might already exist, trying to sign in...")
            auth_response = supabase.auth.sign_in_with_password({
                "email": test_user_email,
                "password": test_user_password
            })
            test_user_id = auth_response.user.id
            print(f"Signed in as user: {test_user_id}")
    except Exception as auth_error:
        print(f"Auth error: {str(auth_error)}")
        raise auth_error
    
    print("\nInserting test data...")
    
    # First, delete any existing expense records for this user
    try:
        delete_response = supabase.table('user_expense_due_dates') \
            .delete() \
            .eq('user_id', test_user_id) \
            .execute()
        print("Deleted existing expense records")
    except Exception as delete_error:
        print(f"Error deleting existing records: {str(delete_error)}")
    
    # Insert test expense records
    expense_data = [
        {
            'id': str(uuid.uuid4()),
            'user_id': test_user_id,
            'expense_type': 'rent',
            'due_date': 1
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': test_user_id,
            'expense_type': 'utilities',
            'due_date': 15
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': test_user_id,
            'expense_type': 'car_payment',
            'due_date': 5
        }
    ]
    
    expense_response = supabase.table('user_expense_due_dates').insert(expense_data).execute()
    print("Inserted expense records")
    
    # Test connection by fetching user expenses
    response = supabase.table('user_expense_due_dates') \
        .select('*') \
        .eq('user_id', test_user_id) \
        .execute()
    
    print("\nConnection successful!")
    print(f"Found {len(response.data)} expense records")
    print("\nSample data:")
    for expense in response.data[:2]:  # Show first 2 records
        print(expense)
        
    print("\nTest user credentials for future use:")
    print(f"Email: {test_user_email}")
    print(f"Password: {test_user_password}")
    print(f"User ID: {test_user_id}")
        
except Exception as e:
    print(f"\nError: {str(e)}") 