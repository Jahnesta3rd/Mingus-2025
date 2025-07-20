import os
import sys
from datetime import datetime, date, timedelta
import pytest
from supabase import create_client, Client
from config import DevelopmentConfig
import uuid

# Initialize Supabase client with configuration
config = DevelopmentConfig()
SUPABASE_URL = config.SUPABASE_URL
SUPABASE_KEY = config.SUPABASE_SERVICE_ROLE_KEY  # Use service role key for admin operations

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {str(e)}")
    sys.exit(1)

# Test user credentials
TEST_EMAIL = "test.user@example.com"
TEST_PASSWORD = "test-password-123"
TEST_USER_ID = None

def get_future_date(days_ahead):
    """Get a date that's always in the future"""
    return (date.today() + timedelta(days=days_ahead)).isoformat()

def setup_date_types():
    """Set up date types as admin - this would typically be done in a migration"""
    try:
        print("\nSetting up date types...")
        date_types = [
            {'type_code': 'CHILD_BIRTHDAY', 'type_name': 'Child\'s Birthday', 'max_occurrences': 3, 'requires_names': True, 'description': 'Birthday celebrations for children'},
            {'type_code': 'WEDDING_ANNIV', 'type_name': 'Wedding Anniversary', 'max_occurrences': 1, 'requires_names': True, 'description': 'Wedding anniversary celebration'},
            {'type_code': 'ENGAGEMENT_ANNIV', 'type_name': 'Engagement Anniversary', 'max_occurrences': 1, 'requires_names': True, 'description': 'Engagement anniversary celebration'},
            {'type_code': 'GROUP_TRIP', 'type_name': 'Group Trip', 'max_occurrences': None, 'requires_names': True, 'description': 'Planned group trips and vacations'},
            {'type_code': 'SPOUSE_BIRTHDAY', 'type_name': 'Spouse\'s Birthday', 'max_occurrences': 1, 'requires_names': True, 'description': 'Birthday celebration for spouse'},
            {'type_code': 'PARENT_BIRTHDAY', 'type_name': 'Parent\'s Birthday', 'max_occurrences': 4, 'requires_names': True, 'description': 'Birthday celebrations for parents'},
            {'type_code': 'TAX_REFUND', 'type_name': 'Tax Refund Date', 'max_occurrences': None, 'requires_names': False, 'description': 'Expected tax refund dates'},
            {'type_code': 'FRATERNITY_DUES', 'type_name': 'Fraternity/Sorority Assessment', 'max_occurrences': None, 'requires_names': False, 'description': 'Fraternity or sorority membership dues and assessments'}
        ]
        
        # Note: In a real application, this would be done through a database migration
        # or admin API endpoint. For testing, we're using direct SQL execution.
        sql = """
        INSERT INTO date_types (type_code, type_name, max_occurrences, requires_names, description)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (type_code) DO UPDATE SET
            type_name = EXCLUDED.type_name,
            max_occurrences = EXCLUDED.max_occurrences,
            requires_names = EXCLUDED.requires_names,
            description = EXCLUDED.description
        """
        
        for date_type in date_types:
            supabase.table('date_types').upsert(date_type).execute()
            
        print("Date types setup completed")
        return True
    except Exception as e:
        print(f"Error setting up date types: {str(e)}")
        return False

def create_test_user():
    """Create test user and return user ID"""
    global TEST_USER_ID
    try:
        # Try to sign up the test user
        user = supabase.auth.sign_up({
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        TEST_USER_ID = user.user.id
        print(f"Created new test user with ID: {TEST_USER_ID}")
    except Exception as e:
        # If user already exists, try to sign in
        try:
            user = supabase.auth.sign_in_with_password({
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            TEST_USER_ID = user.user.id
            print(f"Signed in existing test user with ID: {TEST_USER_ID}")
        except Exception as e:
            print(f"Error setting up test user: {str(e)}")
            sys.exit(1)
    return TEST_USER_ID

def execute_test_data_script(user_id):
    """Execute the test data script using Supabase table API"""
    try:
        print("\nSetting up test data...")
        
        # Step 1: Clear existing test data
        print("Clearing existing data...")
        supabase.table('important_dates').delete().eq('user_id', user_id).execute()
        
        # Step 2: Get CHILD_BIRTHDAY type ID
        print("\nGetting CHILD_BIRTHDAY type ID...")
        result = supabase.table('date_types').select('id').eq('type_code', 'CHILD_BIRTHDAY').execute()
        if not result.data:
            print("Error: Could not find CHILD_BIRTHDAY type. Please ensure migrations have been run.")
            return False
        child_birthday_id = result.data[0]['id']
        
        # Step 3: Insert first child's birthday
        print("\nInserting first child's birthday...")
        important_date = supabase.table('important_dates').insert({
            'user_id': user_id,
            'date_type_id': child_birthday_id,
            'event_date': get_future_date(30),  # 30 days ahead
            'amount': 300.00,
            'description': 'First Child Birthday Party',
            'balance_impact': 'expense'
        }).execute()
        
        if not important_date.data:
            print("Error: Failed to insert first child's birthday")
            return False
            
        supabase.table('associated_people').insert({
            'important_date_id': important_date.data[0]['id'],
            'full_name': 'John Jr Smith',
            'relationship': 'Son'
        }).execute()
        
        # Step 4: Insert second child's birthday
        print("\nInserting second child's birthday...")
        important_date = supabase.table('important_dates').insert({
            'user_id': user_id,
            'date_type_id': child_birthday_id,
            'event_date': get_future_date(60),  # 60 days ahead
            'amount': 250.00,
            'description': 'Second Child Birthday Party',
            'balance_impact': 'expense'
        }).execute()
        
        if not important_date.data:
            print("Error: Failed to insert second child's birthday")
            return False
            
        supabase.table('associated_people').insert({
            'important_date_id': important_date.data[0]['id'],
            'full_name': 'Sarah Smith',
            'relationship': 'Daughter'
        }).execute()
        
        # Step 5: Insert wedding anniversary
        print("\nInserting wedding anniversary...")
        result = supabase.table('date_types').select('id').eq('type_code', 'WEDDING_ANNIV').execute()
        if not result.data:
            print("Error: Could not find WEDDING_ANNIV type")
            return False
        
        wedding_anniv_id = result.data[0]['id']
        important_date = supabase.table('important_dates').insert({
            'user_id': user_id,
            'date_type_id': wedding_anniv_id,
            'event_date': get_future_date(90),  # 90 days ahead
            'amount': 1000.00,
            'description': '15th Wedding Anniversary',
            'balance_impact': 'expense'
        }).execute()
        
        if not important_date.data:
            print("Error: Failed to insert wedding anniversary")
            return False
            
        supabase.table('associated_people').insert({
            'important_date_id': important_date.data[0]['id'],
            'full_name': 'Mary Smith',
            'relationship': 'Spouse'
        }).execute()
        
        # Step 6: Insert parent birthdays
        print("\nInserting parent birthdays...")
        result = supabase.table('date_types').select('id').eq('type_code', 'PARENT_BIRTHDAY').execute()
        if not result.data:
            print("Error: Could not find PARENT_BIRTHDAY type")
            return False
            
        parent_birthday_id = result.data[0]['id']
        
        # Father's birthday
        important_date = supabase.table('important_dates').insert({
            'user_id': user_id,
            'date_type_id': parent_birthday_id,
            'event_date': get_future_date(150),  # 150 days ahead
            'amount': 200.00,
            'description': 'Father\'s Birthday',
            'balance_impact': 'expense'
        }).execute()
        
        supabase.table('associated_people').insert({
            'important_date_id': important_date.data[0]['id'],
            'full_name': 'Robert Smith Sr',
            'relationship': 'Father'
        }).execute()
        
        # Mother's birthday
        important_date = supabase.table('important_dates').insert({
            'user_id': user_id,
            'date_type_id': parent_birthday_id,
            'event_date': get_future_date(180),  # 180 days ahead
            'amount': 200.00,
            'description': 'Mother\'s Birthday',
            'balance_impact': 'expense'
        }).execute()
        
        supabase.table('associated_people').insert({
            'important_date_id': important_date.data[0]['id'],
            'full_name': 'Linda Smith',
            'relationship': 'Mother'
        }).execute()
        
        # Step 7: Insert group trip
        print("\nInserting group trip...")
        result = supabase.table('date_types').select('id').eq('type_code', 'GROUP_TRIP').execute()
        if not result.data:
            print("Error: Could not find GROUP_TRIP type")
            return False
            
        group_trip_id = result.data[0]['id']
        important_date = supabase.table('important_dates').insert({
            'user_id': user_id,
            'date_type_id': group_trip_id,
            'event_date': get_future_date(210),  # 210 days ahead
            'amount': 5000.00,
            'description': 'Family Vacation',
            'balance_impact': 'expense'
        }).execute()
        
        # Add trip participants
        supabase.table('associated_people').insert([
            {
                'important_date_id': important_date.data[0]['id'],
                'full_name': 'John Smith',
                'relationship': 'Self'
            },
            {
                'important_date_id': important_date.data[0]['id'],
                'full_name': 'Mary Smith',
                'relationship': 'Spouse'
            },
            {
                'important_date_id': important_date.data[0]['id'],
                'full_name': 'John Jr Smith',
                'relationship': 'Son'
            }
        ]).execute()
        
        # Step 8: Insert tax refund
        print("\nInserting tax refund...")
        result = supabase.table('date_types').select('id').eq('type_code', 'TAX_REFUND').execute()
        if not result.data:
            print("Error: Could not find TAX_REFUND type")
            return False
            
        tax_refund_id = result.data[0]['id']
        supabase.table('important_dates').insert({
            'user_id': user_id,
            'date_type_id': tax_refund_id,
            'event_date': get_future_date(120),  # 120 days ahead
            'amount': 3500.00,
            'description': 'Expected Tax Refund 2024',
            'balance_impact': 'income'
        }).execute()
        
        print("\nTest data script executed successfully")
        return True
        
    except Exception as e:
        print(f"Error executing test data script: {str(e)}")
        return False

def setup_module(module):
    """Setup function that runs before tests"""
    global TEST_USER_ID
    TEST_USER_ID = create_test_user()

def test_date_types_exist():
    """Verify that all required date types exist"""
    response = supabase.table("date_types").select("*").execute()
    date_types = response.data
    
    required_types = [
        "CHILD_BIRTHDAY", "WEDDING_ANNIV", "ENGAGEMENT_ANNIV",
        "GROUP_TRIP", "SPOUSE_BIRTHDAY", "PARENT_BIRTHDAY",
        "TAX_REFUND", "FRATERNITY_DUES"
    ]
    
    type_codes = [dt["type_code"] for dt in date_types]
    for required_type in required_types:
        assert required_type in type_codes, f"Missing date type: {required_type}"

def test_important_dates_constraints():
    """Test constraints on important_dates table"""
    date_type_id = supabase.table("date_types").select("id").eq("type_code", "CHILD_BIRTHDAY").execute().data[0]["id"]
    
    # Test future date constraint
    with pytest.raises(Exception):
        supabase.table("important_dates").insert({
            "user_id": TEST_USER_ID,
            "date_type_id": date_type_id,
            "event_date": "2020-01-01",  # Past date
            "amount": 100.00,
            "description": "Test past date"
        }).execute()
    
    # Test invalid status
    with pytest.raises(Exception):
        supabase.table("important_dates").insert({
            "user_id": TEST_USER_ID,
            "date_type_id": date_type_id,
            "event_date": "2025-01-01",
            "status": "invalid_status"  # Invalid status
        }).execute()
    
    # Test invalid balance_impact
    with pytest.raises(Exception):
        supabase.table("important_dates").insert({
            "user_id": TEST_USER_ID,
            "date_type_id": date_type_id,
            "event_date": "2025-01-01",
            "balance_impact": "invalid_impact"  # Invalid balance impact
        }).execute()

def test_test_data_integrity():
    """Verify test data was inserted correctly"""
    # Get all important dates for test user
    response = supabase.table("important_dates").select(
        "*",
        count="exact"
    ).eq("user_id", TEST_USER_ID).execute()
    
    dates = response.data
    count = response.count
    
    # We should have at least 7 dates (2 children, 1 wedding, 2 parents, 1 trip, 1 tax)
    assert count >= 7, f"Expected at least 7 dates, got {count}"
    
    # Verify children's birthdays
    child_dates = [d for d in dates if d["description"] and "Child Birthday" in d["description"]]
    assert len(child_dates) == 2, "Should have exactly 2 child birthdays"
    
    # Verify wedding anniversary
    wedding = next((d for d in dates if d["description"] and "Wedding Anniversary" in d["description"]), None)
    assert wedding is not None, "Wedding anniversary not found"
    assert wedding["amount"] == 1000.00, "Incorrect wedding anniversary amount"
    
    # Verify tax refund
    tax_refund = next((d for d in dates if d["description"] and "Tax Refund" in d["description"]), None)
    assert tax_refund is not None, "Tax refund not found"
    assert tax_refund["balance_impact"] == "income", "Tax refund should be income"
    assert tax_refund["amount"] == 3500.00, "Incorrect tax refund amount"

def test_associated_people():
    """Test associated people relationships"""
    # Get all important dates with associated people
    response = supabase.table("important_dates").select(
        "id, description"
    ).eq("user_id", TEST_USER_ID).execute()
    
    for date in response.data:
        people = supabase.table("associated_people").select(
            "*"
        ).eq("important_date_id", date["id"]).execute().data
        
        # Group trip should have 3 people
        if "Family Vacation" in date["description"]:
            assert len(people) == 3, "Group trip should have 3 associated people"
        
        # Wedding anniversary should have 1 person (spouse)
        elif "Wedding Anniversary" in date["description"]:
            assert len(people) == 1, "Wedding anniversary should have 1 associated person"
            assert people[0]["relationship"] == "Spouse", "Wedding anniversary person should be spouse"

def test_rls_policies():
    """Test Row Level Security policies"""
    global TEST_USER_ID, supabase
    
    # First, create a test date to use
    date_type_id = supabase.table("date_types").select("id").eq("type_code", "CHILD_BIRTHDAY").execute().data[0]["id"]
    test_date = {
        "user_id": TEST_USER_ID,
        "date_type_id": date_type_id,
        "event_date": get_future_date(30),
        "amount": 100.00,
        "description": "Test RLS"
    }
    
    # 1. Test access as authenticated user
    try:
        # Should succeed - user can insert their own data
        response = supabase.table("important_dates").insert(test_date).execute()
        assert response.data, "Should be able to insert data as authenticated user"
        
        # Should succeed - user can read their own data
        response = supabase.table("important_dates").select("*").eq("user_id", TEST_USER_ID).execute()
        assert len(response.data) > 0, "Should be able to read own data"
        
        # Clean up the test date
        supabase.table("important_dates").delete().eq("description", "Test RLS").execute()
        
    except Exception as e:
        assert False, f"Authenticated access failed: {str(e)}"
    
    # 2. Test access as unauthenticated user
    try:
        # Create a new client with anon key for unauthenticated access
        config = DevelopmentConfig()
        anon_client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
        
        # Should fail - unauthenticated users cannot insert
        with pytest.raises(Exception):
            anon_client.table("important_dates").insert(test_date).execute()
        
        # Should fail - unauthenticated users cannot read
        with pytest.raises(Exception):
            anon_client.table("important_dates").select("*").execute()
            
    except Exception as e:
        if "AuthApiError" not in str(e) and "AuthError" not in str(e):
            assert False, f"Unexpected error during unauthenticated test: {str(e)}"
    
    # 3. Test cross-user access
    try:
        # Create another test date
        response = supabase.table("important_dates").insert(test_date).execute()
        test_date_id = response.data[0]["id"]
        
        # Try to access as a different user ID
        different_user_id = "00000000-0000-0000-0000-000000000000"
        
        # Should return empty result - cannot see other user's data
        response = supabase.table("important_dates").select("*").eq("user_id", different_user_id).execute()
        assert len(response.data) == 0, "Should not be able to read other user's data"
        
        # Clean up
        supabase.table("important_dates").delete().eq("id", test_date_id).execute()
        
    except Exception as e:
        assert False, f"Cross-user access test failed: {str(e)}"

def test_important_dates():
    """Test important_dates table functionality and RLS policies"""
    try:
        # Initialize clients with different auth contexts
        config = DevelopmentConfig()
        
        # Service role client (bypasses RLS)
        admin_client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
        
        # User client (subject to RLS)
        user_client = create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
        
        # Test data
        user_id_1 = str(uuid.uuid4())
        user_id_2 = str(uuid.uuid4())
        date_type_id = str(uuid.uuid4())
        future_date = (datetime.now() + timedelta(days=30)).date().isoformat()
        
        print("\nTesting Important Dates Functionality")
        print("=" * 80)
        
        # 1. Test Insertion
        print("\n1. Testing Insert Operations:")
        
        # Insert as admin
        insert_query = f"""
        INSERT INTO important_dates (user_id, date_type_id, event_date, amount, description)
        VALUES 
            ('{user_id_1}', '{date_type_id}', '{future_date}', 100.00, 'Test Event 1'),
            ('{user_id_2}', '{date_type_id}', '{future_date}', 200.00, 'Test Event 2')
        RETURNING *;
        """
        
        result = admin_client.postgrest.rpc('exec_sql', {'query': insert_query}).execute()
        print("✓ Admin insert successful")
        
        # 2. Test Select Operations
        print("\n2. Testing Select Operations:")
        
        # Try to select all records as admin
        select_query = """
        SELECT * FROM important_dates ORDER BY created_at DESC;
        """
        
        result = admin_client.postgrest.rpc('exec_sql', {'query': select_query}).execute()
        print(f"✓ Admin can see all records: {len(result.data)} records found")
        
        # Try to select records as user 1
        user_client.auth.sign_in_with_password({
            "email": "test1@example.com",
            "password": "test123"
        })
        
        result = user_client.postgrest.rpc('exec_sql', {'query': select_query}).execute()
        print(f"✓ User 1 can only see their records: {len(result.data)} records found")
        
        # 3. Test Update Operations
        print("\n3. Testing Update Operations:")
        
        # Try to update user 1's record
        update_query = f"""
        UPDATE important_dates 
        SET amount = 150.00 
        WHERE user_id = '{user_id_1}'
        RETURNING *;
        """
        
        result = user_client.postgrest.rpc('exec_sql', {'query': update_query}).execute()
        print("✓ User 1 can update their own record")
        
        # Try to update user 2's record (should fail)
        update_query = f"""
        UPDATE important_dates 
        SET amount = 250.00 
        WHERE user_id = '{user_id_2}'
        RETURNING *;
        """
        
        try:
            result = user_client.postgrest.rpc('exec_sql', {'query': update_query}).execute()
            print("✗ User 1 should not be able to update User 2's record")
        except Exception as e:
            print("✓ User 1 cannot update User 2's record")
        
        # 4. Test Delete Operations
        print("\n4. Testing Delete Operations:")
        
        # Try to delete user 1's record
        delete_query = f"""
        DELETE FROM important_dates 
        WHERE user_id = '{user_id_1}'
        RETURNING *;
        """
        
        result = user_client.postgrest.rpc('exec_sql', {'query': delete_query}).execute()
        print("✓ User 1 can delete their own record")
        
        # Try to delete user 2's record (should fail)
        delete_query = f"""
        DELETE FROM important_dates 
        WHERE user_id = '{user_id_2}'
        RETURNING *;
        """
        
        try:
            result = user_client.postgrest.rpc('exec_sql', {'query': delete_query}).execute()
            print("✗ User 1 should not be able to delete User 2's record")
        except Exception as e:
            print("✓ User 1 cannot delete User 2's record")
        
        # 5. Test Data Validation
        print("\n5. Testing Data Validation:")
        
        # Try to insert a past date (should fail)
        past_date = (datetime.now() - timedelta(days=1)).date().isoformat()
        insert_query = f"""
        INSERT INTO important_dates (user_id, date_type_id, event_date, amount, description)
        VALUES ('{user_id_1}', '{date_type_id}', '{past_date}', 100.00, 'Past Event')
        RETURNING *;
        """
        
        try:
            result = admin_client.postgrest.rpc('exec_sql', {'query': insert_query}).execute()
            print("✗ Should not allow past dates")
        except Exception as e:
            print("✓ Past dates are correctly rejected")
        
        print("\nAll tests completed!")
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    print("Setting up test environment...")
    
    # Create test user and execute SQL script
    user_id = create_test_user()
    if not execute_test_data_script(user_id):
        print("Failed to execute test data script")
        sys.exit(1)
    
    print("\nRunning Important Dates schema tests...")
    
    # Run all tests
    test_functions = [
        test_date_types_exist,
        test_important_dates_constraints,
        test_test_data_integrity,
        test_associated_people,
        test_rls_policies,
        test_important_dates
    ]
    
    for test in test_functions:
        try:
            test()
            print(f"✅ {test.__name__} passed")
        except Exception as e:
            print(f"❌ {test.__name__} failed: {str(e)}")
            sys.exit(1)
    
    print("\nAll tests passed successfully! 🎉") 