import sys
import os
from datetime import datetime, timezone
import uuid
from supabase.client import create_client

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    OnboardingCreate,
    FinancialChallengeType,
    StressHandlingType,
    MotivationType
)
from backend.services.onboarding_service import OnboardingService

def cleanup_test_data(supabase_client, session_id=None, user_id=None):
    """Clean up test data from previous test runs."""
    try:
        if session_id:
            supabase_client.table('anonymous_onboarding_responses').delete().eq('session_id', session_id).execute()
        if user_id:
            supabase_client.table('user_onboarding_profiles').delete().eq('user_id', user_id).execute()
    except Exception as e:
        print(f"Warning: Error during cleanup: {str(e)}")

def test_anonymous_onboarding():
    print("\nTesting Anonymous Onboarding...")
    
    # Get configuration and initialize service with service role key
    current_config = config.get('development', config['default'])()
    supabase_client = create_client(
        supabase_url=current_config.SUPABASE_URL,
        supabase_key=current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    onboarding_service = OnboardingService(supabase_client)
    
    # Generate test IDs
    test_session_id = str(uuid.uuid4())
    
    try:
        # Clean up any existing test data
        cleanup_test_data(supabase_client, session_id=test_session_id)
        
        # Create test data
        test_data = AnonymousOnboardingCreate(
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
            contact_info="test@example.com",
            ip_address="127.0.0.1",
            user_agent="Test Script",
            referrer="test"
        )
        
        # Test creating anonymous response
        print("Creating anonymous onboarding response...")
        response = onboarding_service.create_anonymous_onboarding(test_data)
        print("✓ Successfully created anonymous response")
        print(f"  Session ID: {response.session_id}")
        
        # Test retrieving the response
        print("\nRetrieving anonymous responses...")
        responses = onboarding_service.get_anonymous_onboarding(response.session_id)
        if not responses:
            raise ValueError("Failed to retrieve created anonymous response")
        print("✓ Successfully retrieved responses")
        print(f"  Found {len(responses)} response(s)")
        
        # Test converting to user
        print("\nTesting conversion to user...")
        test_user_id = str(uuid.uuid4())
        converted = onboarding_service.convert_anonymous_to_user(
            session_id=response.session_id,
            user_id=test_user_id
        )
        if not converted:
            raise ValueError("Failed to convert anonymous response to user")
        print("✓ Successfully converted anonymous response to user")
        print(f"  User ID: {converted.user_id}")
        
        # Test analytics
        print("\nFetching onboarding analytics...")
        stats = onboarding_service.get_anonymous_onboarding_stats()
        print("✓ Successfully retrieved analytics")
        print("  Statistics:")
        print(f"  - Total responses: {stats.total_responses}")
        print(f"  - Conversion rate: {stats.conversion_rate:.2%}")
        print(f"  - Average income: ${stats.average_income:.2f}")
        
        print("\nAll anonymous onboarding tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during anonymous onboarding test: {str(e)}")
        return False
    finally:
        # Clean up test data
        cleanup_test_data(supabase_client, session_id=test_session_id)

def test_user_onboarding():
    print("\nTesting User Onboarding...")
    
    # Get configuration and initialize service with service role key
    current_config = config.get('development', config['default'])()
    supabase_client = create_client(
        supabase_url=current_config.SUPABASE_URL,
        supabase_key=current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    onboarding_service = OnboardingService(supabase_client)
    
    # Generate test ID
    test_user_id = str(uuid.uuid4())
    
    try:
        # Clean up any existing test data
        cleanup_test_data(supabase_client, user_id=test_user_id)
        
        # Create test data
        test_data = OnboardingCreate(
            financial_challenge=FinancialChallengeType.MULTIPLE_INCOME,
            stress_handling=[StressHandlingType.EXERCISE, StressHandlingType.RESEARCH_PLAN],
            motivation=[MotivationType.FAMILY_GOALS, MotivationType.COMMUNITY_IMPACT],
            monthly_income=7500.00,
            monthly_expenses=4500.00,
            savings_goal=50000.00,
            risk_tolerance=8,
            financial_knowledge=7,
            preferred_contact_method="email",
            contact_info="test@example.com"
        )
        
        # Test creating user profile
        print("Creating user onboarding profile...")
        response = onboarding_service.create_onboarding_profile(test_user_id, test_data)
        if not response:
            raise ValueError("Failed to create user onboarding profile")
        print("✓ Successfully created user profile")
        print(f"  User ID: {response.user_id}")
        
        # Test retrieving the profile
        print("\nRetrieving user profile...")
        profile = onboarding_service.get_onboarding_profile(test_user_id)
        if not profile:
            raise ValueError("Failed to retrieve created user profile")
        print("✓ Successfully retrieved profile")
        print(f"  Financial Challenge: {profile.financial_challenge}")
        
        # Test checking onboarding status
        print("\nChecking onboarding status...")
        status = onboarding_service.check_onboarding_status(test_user_id)
        if not status:
            raise ValueError("Failed to check onboarding status")
        print("✓ Successfully checked status")
        print(f"  Complete: {status.is_complete}")
        if not status.is_complete:
            print(f"  Missing fields: {', '.join(status.missing_fields)}")
        
        # Test analytics
        print("\nFetching onboarding statistics...")
        stats = onboarding_service.get_onboarding_stats()
        print("✓ Successfully retrieved statistics")
        print("  Statistics:")
        print(f"  - Total responses: {stats.total_responses}")
        print(f"  - Conversion rate: {stats.conversion_rate:.2%}")
        print(f"  - Average income: ${stats.average_income:.2f}")
        
        print("\nAll user onboarding tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during user onboarding test: {str(e)}")
        return False
    finally:
        # Clean up test data
        cleanup_test_data(supabase_client, user_id=test_user_id)

def main():
    print("Starting Onboarding Database Tests...")
    
    # Run tests
    anonymous_success = test_anonymous_onboarding()
    user_success = test_user_onboarding()
    
    # Print final results
    print("\nTest Results Summary:")
    print(f"Anonymous Onboarding: {'✓ Passed' if anonymous_success else '❌ Failed'}")
    print(f"User Onboarding: {'✓ Passed' if user_success else '❌ Failed'}")
    
    if anonymous_success and user_success:
        print("\nAll tests passed successfully! ✓")
        sys.exit(0)
    else:
        print("\nSome tests failed. Please check the logs above. ❌")
        sys.exit(1)

if __name__ == "__main__":
    main() 