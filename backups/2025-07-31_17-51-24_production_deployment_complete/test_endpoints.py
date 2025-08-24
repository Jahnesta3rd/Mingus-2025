import requests
import json
from datetime import datetime, timedelta
from create_test_user import create_test_user

def test_health_endpoint(base_url):
    """Test the health check endpoint"""
    response = requests.get(f"{base_url}/health")
    print("\nHealth Check Test:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_forecast_endpoint(base_url, user_id):
    """Test the forecast endpoint"""
    data = {
        "user_id": user_id,
        "initial_balance": 1000.00,
        "start_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    }
    
    response = requests.post(
        f"{base_url}/forecast",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    print("\nForecast Test:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def main():
    base_url = "http://localhost:5002"
    
    print("Starting endpoint tests...")
    
    # Test health endpoint
    if not test_health_endpoint(base_url):
        print("Health check failed!")
        return
    
    # Create test user
    print("\nCreating test user...")
    user_id = create_test_user()
    if not user_id:
        print("Failed to create test user!")
        return
    
    print(f"Test user created with ID: {user_id}")
    
    # Test forecast endpoint
    if not test_forecast_endpoint(base_url, user_id):
        print("Forecast endpoint test failed!")
        return
    
    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    main() 