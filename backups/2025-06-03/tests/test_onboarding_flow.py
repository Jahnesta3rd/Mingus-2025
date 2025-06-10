import sys
import os
import uuid
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from supabase.client import create_client
import pytest
import pytest_asyncio
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    AnonymousOnboardingResponse,
    FinancialChallengeType,
    StressHandlingType,
    MotivationType,
    OnboardingStatus
)
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

class OnboardingFlowTest:
    def __init__(self):
        # Initialize Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Initialize WebDriver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Initialize Supabase client
        current_config = config.get('development', config['default'])()
        self.supabase = create_client(
            supabase_url=current_config.SUPABASE_URL,
            supabase_key=current_config.SUPABASE_SERVICE_ROLE_KEY
        )
        
        # Base URL for testing
        self.base_url = "http://localhost:5000"
    
    def cleanup(self):
        """Clean up test data."""
        try:
            # Get session ID from cookie
            session_id = self.driver.get_cookie('session_id')['value']
            
            # Clean up analytics data
            self.supabase.table('personalization_analytics').delete().eq('session_id', session_id).execute()
            
            # Clean up onboarding responses
            self.supabase.table('anonymous_onboarding_responses').delete().eq('session_id', session_id).execute()
            
        except Exception as e:
            print(f"Warning: Cleanup error: {str(e)}")
        finally:
            self.driver.quit()
    
    def verify_session_persistence(self):
        """Verify that session persists after page refresh."""
        # Get initial session ID
        initial_session_id = self.driver.get_cookie('session_id')['value']
        
        # Refresh page
        self.driver.refresh()
        time.sleep(2)  # Wait for page to reload
        
        # Get new session ID
        new_session_id = self.driver.get_cookie('session_id')['value']
        
        assert initial_session_id == new_session_id, "Session ID changed after refresh"
        print("✓ Session persistence verified")
    
    def verify_analytics_data(self, session_id, expected_challenge, expected_motivation):
        """Verify that analytics data was saved correctly."""
        result = self.supabase.table('personalization_analytics').select('*').eq('session_id', session_id).execute()
        
        assert result.data, "No analytics data found"
        latest = result.data[-1]
        
        assert latest['financial_challenge'] == expected_challenge, "Wrong financial challenge in analytics"
        assert latest['motivation'] == expected_motivation, "Wrong motivation in analytics"
        print("✓ Analytics data verified")
    
    def verify_personalization(self, expected_testimonial_text, expected_cta_text):
        """Verify that personalization changes are visible."""
        # Wait for testimonial to be visible
        testimonial = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "testimonial"))
        )
        assert expected_testimonial_text.lower() in testimonial.text.lower(), \
            f"Expected testimonial text not found. Expected: {expected_testimonial_text}, Got: {testimonial.text}"
        
        # Check CTA button text
        cta_button = self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "cta-button"))
        )
        assert expected_cta_text.lower() in cta_button.text.lower(), \
            f"Expected CTA text not found. Expected: {expected_cta_text}, Got: {cta_button.text}"
        
        print("✓ Personalization changes verified")
    
    def run_test(self):
        """Run the complete onboarding flow test."""
        try:
            print("\nStarting Onboarding Flow Test...")
            
            # Step 1: Load onboarding page and verify session ID generation
            print("\nTesting initial page load...")
            self.driver.get(f"{self.base_url}/onboarding")
            session_cookie = self.wait.until(lambda d: d.get_cookie('session_id'))
            assert session_cookie, "Session ID cookie not generated"
            print("✓ Initial page load successful")
            
            # Step 2: Answer financial challenge question
            print("\nTesting financial challenge question...")
            challenge_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "challenge-debt"))
            )
            challenge_btn.click()
            
            # Verify personalization after challenge selection
            self.verify_personalization(
                "I was drowning in debt",
                "Take control of your debt"
            )
            print("✓ Financial challenge step completed")
            
            # Step 3: Answer stress handling question
            print("\nTesting stress handling question...")
            stress_btns = self.wait.until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "stress-option"))
            )
            for btn in stress_btns[:2]:  # Select first two options
                btn.click()
            
            next_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "next-button"))
            )
            next_btn.click()
            print("✓ Stress handling step completed")
            
            # Step 4: Answer motivation question
            print("\nTesting motivation question...")
            motivation_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "motivation-financial-freedom"))
            )
            motivation_btn.click()
            
            # Verify final personalization
            self.verify_personalization(
                "Breaking free from debt gave me financial freedom",
                "Start your journey to financial freedom"
            )
            print("✓ Motivation step completed")
            
            # Step 5: Verify analytics data
            print("\nVerifying analytics data...")
            session_id = self.driver.get_cookie('session_id')['value']
            self.verify_analytics_data(
                session_id,
                FinancialChallengeType.DEBT.value,
                MotivationType.FINANCIAL_FREEDOM.value
            )
            
            # Step 6: Test session persistence
            print("\nTesting session persistence...")
            self.verify_session_persistence()
            
            print("\nAll onboarding flow tests passed! ✓")
            return True
            
        except Exception as e:
            print(f"\n❌ Error during onboarding flow test: {str(e)}")
            return False
        finally:
            self.cleanup()

def main():
    print("Starting Onboarding Flow Tests...")
    
    # Ensure the Flask server is running
    print("Note: Ensure the Flask server is running on http://localhost:5000")
    
    # Run test
    test = OnboardingFlowTest()
    success = test.run_test()
    
    # Print final results
    print("\nTest Results Summary:")
    print(f"Onboarding Flow Tests: {'✓ Passed' if success else '❌ Failed'}")
    
    if success:
        print("\nAll tests passed successfully! ✓")
        sys.exit(0)
    else:
        print("\nSome tests failed. Please check the logs above. ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()

def test_create_anonymous_onboarding(client, sample_anonymous_onboarding_data):
    """Test creating an anonymous onboarding response."""
    response = client.post('/api/onboarding/anonymous', json=sample_anonymous_onboarding_data)
    assert response.status_code == 201
    data = response.get_json()
    assert data['financial_challenge'] == sample_anonymous_onboarding_data['financial_challenge']
    assert data['monthly_income'] == sample_anonymous_onboarding_data['monthly_income']
    assert data['session_id'] == sample_anonymous_onboarding_data['session_id']

def test_get_anonymous_onboarding(client, sample_anonymous_onboarding_data):
    """Test retrieving anonymous onboarding responses."""
    # First create an anonymous onboarding response
    create_response = client.post('/api/onboarding/anonymous', json=sample_anonymous_onboarding_data)
    assert create_response.status_code == 201
    
    # Then retrieve it
    session_id = sample_anonymous_onboarding_data['session_id']
    response = client.get(f'/api/onboarding/anonymous/{session_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['financial_challenge'] == sample_anonymous_onboarding_data['financial_challenge']

def test_convert_anonymous_to_user(client, auth_headers, sample_anonymous_onboarding_data):
    """Test converting anonymous responses to user responses."""
    # First create an anonymous onboarding response
    create_response = client.post('/api/onboarding/anonymous', json=sample_anonymous_onboarding_data)
    assert create_response.status_code == 201
    
    # Then convert it
    convert_response = client.post(
        '/api/onboarding/anonymous/convert',
        json={'session_id': sample_anonymous_onboarding_data['session_id']},
        headers=auth_headers
    )
    assert convert_response.status_code == 200
    data = convert_response.get_json()
    assert data['user_id'] == 'test-user'

def test_get_anonymous_onboarding_stats(client):
    """Test retrieving anonymous onboarding statistics."""
    response = client.get('/api/onboarding/anonymous/stats')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_responses' in data
    assert 'conversion_rate' in data

def test_invalid_anonymous_onboarding_data(client):
    """Test validation of anonymous onboarding data."""
    invalid_data = {
        "financial_challenge": "invalid_challenge",
        "stress_handling": ["invalid_handling"],
        "motivation": ["invalid_motivation"],
        "monthly_income": -100,
        "monthly_expenses": -50,
        "savings_goal": -1000,
        "risk_tolerance": 11,
        "financial_knowledge": 0,
        "preferred_contact_method": "invalid",
        "contact_info": "invalid"
    }
    response = client.post('/api/onboarding/anonymous', json=invalid_data)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "details" in data

def test_duplicate_session_id(client, sample_anonymous_onboarding_data):
    """Test handling of duplicate session IDs."""
    # First submission
    response1 = client.post('/api/onboarding/anonymous', json=sample_anonymous_onboarding_data)
    assert response1.status_code == 201
    
    # Second submission with same session ID
    response2 = client.post('/api/onboarding/anonymous', json=sample_anonymous_onboarding_data)
    assert response2.status_code == 400
    data = response2.get_json()
    assert "error" in data
    assert "duplicate session" in data["error"].lower()

def test_convert_nonexistent_session(client, auth_headers):
    """Test converting a nonexistent session."""
    response = client.post(
        '/api/onboarding/anonymous/convert',
        json={'session_id': '550e8400-e29b-41d4-a716-446655440999'},  # Non-existent session
        headers=auth_headers
    )
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data

def test_get_nonexistent_session(client):
    """Test retrieving a nonexistent session."""
    response = client.get('/api/onboarding/anonymous/550e8400-e29b-41d4-a716-446655440999')
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data

def test_convert_already_converted_session(client, auth_headers, sample_anonymous_onboarding_data):
    """Test converting an already converted session."""
    # First create and convert a session
    create_response = client.post('/api/onboarding/anonymous', json=sample_anonymous_onboarding_data)
    assert create_response.status_code == 201
    
    convert_response1 = client.post(
        '/api/onboarding/anonymous/convert',
        json={'session_id': sample_anonymous_onboarding_data['session_id']},
        headers=auth_headers
    )
    assert convert_response1.status_code == 200
    
    # Try to convert again
    convert_response2 = client.post(
        '/api/onboarding/anonymous/convert',
        json={'session_id': sample_anonymous_onboarding_data['session_id']},
        headers=auth_headers
    )
    assert convert_response2.status_code == 400
    data = convert_response2.get_json()
    assert "error" in data
    assert "already converted" in data["error"].lower()

pytestmark = pytest.mark.asyncio

async def test_anonymous_onboarding_creation(client, sample_anonymous_onboarding_data):
    """Test creating an anonymous onboarding profile."""
    response = await client.post(
        "/api/onboarding/anonymous",
        json=sample_anonymous_onboarding_data
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["financial_challenge"] == sample_anonymous_onboarding_data["financial_challenge"]
    assert data["session_id"] == sample_anonymous_onboarding_data["session_id"]

async def test_anonymous_onboarding_retrieval(client, sample_anonymous_onboarding_data):
    """Test retrieving anonymous onboarding responses."""
    # Create anonymous onboarding
    response = await client.post(
        "/api/onboarding/anonymous",
        json=sample_anonymous_onboarding_data
    )
    assert response.status_code == 201

    # Retrieve responses
    session_id = sample_anonymous_onboarding_data["session_id"]
    response = await client.get(f"/api/onboarding/anonymous/{session_id}")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["financial_challenge"] == sample_anonymous_onboarding_data["financial_challenge"]

async def test_user_signup_and_onboarding_conversion(
    client,
    sample_anonymous_onboarding_data,
    sample_user_data
):
    """Test user signup and onboarding conversion flow."""
    # Create anonymous onboarding
    response = await client.post(
        "/api/onboarding/anonymous",
        json=sample_anonymous_onboarding_data
    )
    assert response.status_code == 201

    # Sign up user
    response = await client.post(
        "/api/signup",
        json={
            **sample_user_data,
            "session_id": sample_anonymous_onboarding_data["session_id"]
        }
    )
    assert response.status_code == 201
    user_data = response.get_json()
    assert "user" in user_data
    assert "welcome_message" in user_data

    # Get auth token
    auth_token = user_data["user"]["id"]  # In real app, this would be a JWT

    # Convert anonymous onboarding
    response = await client.post(
        "/api/onboarding/anonymous/convert",
        json={"session_id": sample_anonymous_onboarding_data["session_id"]},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["financial_challenge"] == sample_anonymous_onboarding_data["financial_challenge"]

async def test_onboarding_status_progression(client, sample_user_data, sample_onboarding_data):
    """Test onboarding status progression."""
    # Sign up user
    response = await client.post("/api/signup", json=sample_user_data)
    assert response.status_code == 201
    user_data = response.get_json()
    auth_token = user_data["user"]["id"]

    # Check initial status
    response = await client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data == OnboardingStatus.NOT_STARTED

    # Create onboarding profile
    response = await client.post(
        "/api/onboarding/profile",
        json=sample_onboarding_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201

    # Check in-progress status
    response = await client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data == OnboardingStatus.IN_PROGRESS

    # Update onboarding profile
    response = await client.put(
        "/api/onboarding/profile",
        json={"risk_tolerance": 8},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

    # Check completed status
    response = await client.get(
        "/api/onboarding/status",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data == OnboardingStatus.COMPLETED

async def test_onboarding_validation(client):
    """Test onboarding data validation."""
    invalid_data = {
        "financial_challenge": "invalid_challenge",
        "stress_handling": ["invalid_handling"],
        "motivation": ["invalid_motivation"],
        "monthly_income": -1000,
        "monthly_expenses": -500,
        "savings_goal": -10000,
        "risk_tolerance": 11,
        "financial_knowledge": 0,
        "preferred_contact_method": "invalid",
        "contact_info": "invalid-email"
    }

    response = await client.post("/api/onboarding/anonymous", json=invalid_data)
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "details" in data

async def test_onboarding_stats(client, sample_anonymous_onboarding_data):
    """Test onboarding statistics."""
    # Create multiple anonymous onboarding responses
    for _ in range(3):
        response = await client.post(
            "/api/onboarding/anonymous",
            json=sample_anonymous_onboarding_data
        )
        assert response.status_code == 201

    # Get anonymous stats
    response = await client.get("/api/onboarding/anonymous/stats")
    assert response.status_code == 200
    data = response.get_json()
    assert data["total_profiles"] == 3
    assert "top_challenges" in data
    assert "top_stress_handling" in data
    assert "top_motivations" in data

async def test_client_info_tracking(client, sample_anonymous_onboarding_data):
    """Test client information tracking."""
    # Create onboarding with client info
    response = await client.post(
        "/api/onboarding/anonymous",
        json=sample_anonymous_onboarding_data,
        headers={
            "User-Agent": "Test Browser",
            "Referer": "https://test.com"
        }
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["user_agent"] == "Test Browser"
    assert "session_id" in data

    # Check cookie setting
    assert "session_id" in response.headers.get("Set-Cookie", "") 