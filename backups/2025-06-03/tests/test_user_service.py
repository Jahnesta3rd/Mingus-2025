import sys
import os
import uuid
from datetime import datetime
from supabase.client import create_client

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    FinancialChallengeType,
    StressHandlingType,
    MotivationType
)
from backend.services.onboarding_service import OnboardingService
from backend.services.user_service import UserService, UserCreate, IncomeRange

def cleanup_test_data(supabase_client, session_id=None, email=None):
    """Clean up test data from previous test runs."""
    try:
        if email:
            supabase_client.table('users').delete().eq('email', email).execute()
        if session_id:
            supabase_client.table('anonymous_onboarding_responses').delete().eq('session_id', session_id).execute()
            supabase_client.table('user_onboarding_profiles').delete().eq('session_id', session_id).execute()
    except Exception as e:
        print(f"Warning: Error during cleanup: {str(e)}")

async def test_user_service():
    print("\nTesting User Service...")
    
    # Get configuration and initialize services
    current_config = config.get('development', config['default'])()
    supabase_client = create_client(
        supabase_url=current_config.SUPABASE_URL,
        supabase_key=current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    onboarding_service = OnboardingService(supabase_client)
    user_service = UserService(supabase_client)
    
    # Generate test data
    test_session_id = str(uuid.uuid4())
    test_email = f"test_{test_session_id}@example.com"
    
    try:
        # Clean up any existing test data
        cleanup_test_data(supabase_client, test_session_id, test_email)
        
        # Create test onboarding response
        print("Creating test onboarding response...")
        onboarding_data = AnonymousOnboardingCreate(
            session_id=test_session_id,
            financial_challenge=FinancialChallengeType.DEBT,
            stress_handling=[StressHandlingType.TALK_TO_PEOPLE, StressHandlingType.RESEARCH_PLAN],
            motivation=[MotivationType.FINANCIAL_FREEDOM, MotivationType.PERSONAL_GROWTH],
            monthly_income=5000.00,
            monthly_expenses=3000.00,
            savings_goal=20000.00,
            risk_tolerance=7,
            financial_knowledge=6,
            preferred_contact_method="email",
            contact_info=test_email,
            ip_address="127.0.0.1",
            user_agent="Test Script",
            referrer="test"
        )
        response = await onboarding_service.create_anonymous_onboarding(onboarding_data)
        print("✓ Successfully created onboarding response")
        
        # Test user creation
        print("\nTesting user creation...")
        user_data = UserCreate(
            email=test_email,
            full_name="Test User",
            income_range=IncomeRange.RANGE_50K_75K,
            session_id=test_session_id
        )
        user = await user_service.create_user(user_data)
        if not user or not user.id:
            raise ValueError("Failed to create user")
        print("✓ Successfully created user")
        print(f"  User ID: {user.id}")
        
        # Test duplicate email handling
        print("\nTesting duplicate email handling...")
        try:
            await user_service.create_user(user_data)
            raise ValueError("Should not allow duplicate email")
        except ValueError as e:
            if "Email already registered" in str(e):
                print("✓ Successfully prevented duplicate email")
            else:
                raise
        
        # Test onboarding conversion
        print("\nTesting onboarding conversion...")
        converted_response = await onboarding_service.get_anonymous_onboarding(test_session_id)
        if not converted_response or not converted_response[0].converted_to_signup:
            raise ValueError("Failed to convert onboarding response")
        print("✓ Successfully converted onboarding response")
        
        # Test user profile creation
        print("\nTesting user profile creation...")
        profile = supabase_client.table('user_onboarding_profiles').select('*').eq('user_id', user.id).execute()
        if not profile.data:
            raise ValueError("Failed to create user profile")
        print("✓ Successfully created user profile")
        
        # Test welcome message
        print("\nTesting welcome message...")
        welcome_message = user_service.get_welcome_message(user.id)
        if not welcome_message or "debt" not in welcome_message.lower():
            raise ValueError("Failed to get personalized welcome message")
        print("✓ Successfully generated welcome message")
        print(f"  Message: {welcome_message}")
        
        print("\nAll user service tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during user service test: {str(e)}")
        return False
    finally:
        # Clean up test data
        cleanup_test_data(supabase_client, test_session_id, test_email)

def main():
    print("Starting User Service Tests...")
    
    # Run test
    success = asyncio.run(test_user_service())
    
    # Print final results
    print("\nTest Results Summary:")
    print(f"User Service Tests: {'✓ Passed' if success else '❌ Failed'}")
    
    if success:
        print("\nAll tests passed successfully! ✓")
        sys.exit(0)
    else:
        print("\nSome tests failed. Please check the logs above. ❌")
        sys.exit(1)

if __name__ == "__main__":
    main() 