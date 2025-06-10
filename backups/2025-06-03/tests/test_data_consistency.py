import os
import pytest
import uuid
import httpx
from datetime import datetime, timedelta
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    FinancialChallengeType,
    StressHandlingType,
    MotivationType
)

# Set test environment variables
os.environ['FLASK_ENV'] = 'testing'
os.environ['SUPABASE_URL'] = 'https://test-project.supabase.co'
os.environ['SUPABASE_KEY'] = 'test-key'
os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-role-key'

@pytest.fixture
async def async_client(app):
    """Create an async HTTP client for testing."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

def test_onboarding_data_consistency(test_client, supabase_client):
    """Test data consistency between onboarding_responses and personalization_analytics tables."""
    
    # Helper function to create test session data
    def complete_onboarding_session():
        session_id = str(uuid.uuid4())
        
        # Create onboarding response
        onboarding_data = AnonymousOnboardingCreate(
            session_id=session_id,
            financial_challenge=FinancialChallengeType.DEBT_MANAGEMENT,
            stress_handling=[StressHandlingType.BUDGETING, StressHandlingType.AUTOMATION],
            motivation=[MotivationType.FINANCIAL_FREEDOM, MotivationType.DEBT_FREE],
            monthly_income=5000.0,
            monthly_expenses=3000.0,
            savings_goal=20000.0,
            risk_tolerance=7,
            financial_knowledge=6,
            preferred_contact_method="email",
            contact_info="test@example.com",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0 (Test)",
            referrer="https://test.com"
        )
        
        # Submit onboarding response
        response = test_client.post(
            "/api/onboarding/anonymous",
            json=onboarding_data.model_dump()
        )
        assert response.status_code == 201
        
        return session_id
    
    # Test multiple sessions
    session_ids = []
    for _ in range(3):  # Create 3 different sessions
        session_id = complete_onboarding_session()
        session_ids.append(session_id)
    
    # Verify data consistency for each session
    for session_id in session_ids:
        # Check onboarding_responses table
        onboarding_response = supabase_client.table('onboarding_responses').select('*').eq('session_id', session_id).single().execute()
        assert onboarding_response is not None
        
        # Check personalization_analytics table
        analytics_data = supabase_client.table('personalization_analytics').select('*').eq('session_id', session_id).single().execute()
        assert analytics_data is not None
        
        # Verify data consistency
        assert onboarding_response['financial_challenge'] == analytics_data['financial_challenge']
        assert onboarding_response['stress_handling'] == analytics_data['stress_handling']
        assert onboarding_response['motivation'] == analytics_data['motivation']
        assert onboarding_response['monthly_income'] == analytics_data['monthly_income']
        assert onboarding_response['monthly_expenses'] == analytics_data['monthly_expenses']
        assert onboarding_response['savings_goal'] == analytics_data['savings_goal']
        assert onboarding_response['risk_tolerance'] == analytics_data['risk_tolerance']
        assert onboarding_response['financial_knowledge'] == analytics_data['financial_knowledge']

def test_multiple_sessions_separation(test_client, supabase_client):
    """Test that multiple sessions are properly separated in the database."""
    
    # Create two concurrent sessions
    session_id1 = str(uuid.uuid4())
    session_id2 = str(uuid.uuid4())
    
    # Submit responses for both sessions
    for session_id in [session_id1, session_id2]:
        onboarding_data = AnonymousOnboardingCreate(
            session_id=session_id,
            financial_challenge=FinancialChallengeType.DEBT_MANAGEMENT,
            stress_handling=[StressHandlingType.BUDGETING],
            motivation=[MotivationType.FINANCIAL_FREEDOM],
            monthly_income=5000.0,
            monthly_expenses=3000.0,
            savings_goal=20000.0,
            risk_tolerance=7,
            financial_knowledge=6,
            preferred_contact_method="email",
            contact_info="test@example.com",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0 (Test)",
            referrer="https://test.com"
        )
        
        response = test_client.post(
            "/api/onboarding/anonymous",
            json=onboarding_data.model_dump()
        )
        assert response.status_code == 201
    
    # Verify data separation
    for session_id in [session_id1, session_id2]:
        # Check onboarding_responses table
        onboarding_response = supabase_client.table('onboarding_responses').select('*').eq('session_id', session_id).single().execute()
        assert onboarding_response is not None
        assert onboarding_response['session_id'] == session_id
        
        # Check personalization_analytics table
        analytics_data = supabase_client.table('personalization_analytics').select('*').eq('session_id', session_id).single().execute()
        assert analytics_data is not None
        assert analytics_data['session_id'] == session_id
        
        # Verify no cross-contamination
        other_session_id = session_id2 if session_id == session_id1 else session_id1
        assert onboarding_response['session_id'] != other_session_id
        assert analytics_data['session_id'] != other_session_id

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 