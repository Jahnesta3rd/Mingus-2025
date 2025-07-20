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
from backend.services.personalization_service import PersonalizationService

def cleanup_test_data(supabase_client, session_id=None):
    """Clean up test data from previous test runs."""
    try:
        if session_id:
            supabase_client.table('personalization_analytics').delete().eq('session_id', session_id).execute()
            supabase_client.table('anonymous_onboarding_responses').delete().eq('session_id', session_id).execute()
    except Exception as e:
        print(f"Warning: Error during cleanup: {str(e)}")

def test_personalization():
    print("\nTesting Personalization Service...")
    
    # Get configuration and initialize services with service role key
    current_config = config.get('development', config['default'])()
    supabase_client = create_client(
        supabase_url=current_config.SUPABASE_URL,
        supabase_key=current_config.SUPABASE_SERVICE_ROLE_KEY
    )
    onboarding_service = OnboardingService(supabase_client)
    personalization_service = PersonalizationService(supabase_client)
    
    # Generate test session ID
    test_session_id = str(uuid.uuid4())
    
    try:
        # Clean up any existing test data
        cleanup_test_data(supabase_client, test_session_id)
        
        # Create test onboarding response
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
        
        # Create onboarding response
        print("Creating test onboarding response...")
        response = onboarding_service.create_anonymous_onboarding(test_data)
        print("✓ Successfully created onboarding response")
        
        # Test getting user responses
        print("\nTesting get_user_responses...")
        responses = personalization_service.get_user_responses(test_session_id)
        if not responses:
            raise ValueError("Failed to retrieve user responses")
        print("✓ Successfully retrieved user responses")
        print(f"  Found {len(responses)} response(s)")
        
        # Test getting testimonial
        print("\nTesting get_testimonial...")
        testimonial = personalization_service.get_testimonial(FinancialChallengeType.DEBT)
        if not testimonial or 'quote' not in testimonial:
            raise ValueError("Failed to get testimonial")
        print("✓ Successfully retrieved testimonial")
        print(f"  Author: {testimonial['author']}")
        print(f"  Quote: {testimonial['quote'][:50]}...")
        
        # Test getting CTA text
        print("\nTesting get_cta_text...")
        cta_text = personalization_service.get_cta_text(MotivationType.FINANCIAL_FREEDOM)
        if not cta_text:
            raise ValueError("Failed to get CTA text")
        print("✓ Successfully retrieved CTA text")
        print(f"  Text: {cta_text}")
        
        # Test tracking conversion
        print("\nTesting track_personalization_conversion...")
        personalization_service.track_personalization_conversion(
            session_id=test_session_id,
            financial_challenge=FinancialChallengeType.DEBT,
            motivation=MotivationType.FINANCIAL_FREEDOM,
            converted=True
        )
        print("✓ Successfully tracked conversion")
        
        # Test getting personalization stats
        print("\nTesting get_personalization_stats...")
        stats = personalization_service.get_personalization_stats()
        if not stats:
            raise ValueError("Failed to get personalization stats")
        print("✓ Successfully retrieved personalization stats")
        print("  Financial Challenge Stats:")
        for challenge, data in stats['financial_challenges'].items():
            print(f"    - {challenge}: {data['conversion_rate']:.1%} conversion rate")
        print("  Motivation Stats:")
        for motivation, data in stats['motivations'].items():
            print(f"    - {motivation}: {data['conversion_rate']:.1%} conversion rate")
        
        print("\nAll personalization tests passed! ✓")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during personalization test: {str(e)}")
        return False
    finally:
        # Clean up test data
        cleanup_test_data(supabase_client, test_session_id)

def main():
    print("Starting Personalization Tests...")
    
    # Run test
    success = test_personalization()
    
    # Print final results
    print("\nTest Results Summary:")
    print(f"Personalization Tests: {'✓ Passed' if success else '❌ Failed'}")
    
    if success:
        print("\nAll tests passed successfully! ✓")
        sys.exit(0)
    else:
        print("\nSome tests failed. Please check the logs above. ❌")
        sys.exit(1)

if __name__ == "__main__":
    main() 