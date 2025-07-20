#!/usr/bin/env python3
"""
Test script for phone verification endpoints
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5001"  # Adjust port as needed
API_BASE = f"{BASE_URL}/api/onboarding"

def test_send_verification():
    """Test sending verification code"""
    print("Testing send verification endpoint...")
    
    url = f"{API_BASE}/send-verification"
    data = {
        "phone_number": "+1234567890"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_verify_phone():
    """Test verifying phone number"""
    print("\nTesting verify phone endpoint...")
    
    url = f"{API_BASE}/verify-phone"
    data = {
        "phone_number": "+1234567890",
        "verification_code": "123456"  # Mock code for testing
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_resend_verification():
    """Test resending verification code"""
    print("\nTesting resend verification endpoint...")
    
    url = f"{API_BASE}/resend-verification"
    data = {
        "phone_number": "+1234567890"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all tests"""
    print("Phone Verification Endpoints Test")
    print("=" * 40)
    
    # Note: These tests will fail without authentication
    # In a real scenario, you'd need to authenticate first
    
    print("Note: These tests require authentication and a running Flask server")
    print("The endpoints are:")
    print(f"  POST {API_BASE}/send-verification")
    print(f"  POST {API_BASE}/verify-phone")
    print(f"  POST {API_BASE}/resend-verification")
    
    print("\nExpected request format:")
    print("""
    Send Verification:
    {
        "phone_number": "+1234567890"
    }
    
    Verify Phone:
    {
        "phone_number": "+1234567890",
        "verification_code": "123456"
    }
    
    Resend Verification:
    {
        "phone_number": "+1234567890"
    }
    """)
    
    print("Expected responses:")
    print("""
    Success Response:
    {
        "success": true,
        "message": "Verification code sent successfully",
        "expires_at": "2024-01-01T12:00:00",
        "resend_count": 1
    }
    
    Error Response:
    {
        "success": false,
        "error": "Error message here"
    }
    """)

if __name__ == "__main__":
    main() 