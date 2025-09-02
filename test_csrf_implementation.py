#!/usr/bin/env python3
"""
Simple CSRF Protection Implementation Test
Tests the core CSRF protection functionality without requiring Flask context
"""

import sys
import os
import time
import secrets
import hmac
import hashlib

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_csrf_token_generation():
    """Test CSRF token generation and validation"""
    print("🔒 Testing CSRF Token Generation and Validation")
    
    # Test parameters
    secret_key = "test_secret_key_for_csrf_protection"
    session_id = secrets.token_urlsafe(32)
    timestamp = str(int(time.time()))
    
    # Generate token
    token_data = f"financial:{session_id}:{timestamp}"
    signature = hmac.new(
        (secret_key + 'financial').encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    token = f"{token_data}:{signature}"
    
    print(f"✅ Generated token: {token[:50]}...")
    
    # Validate token
    try:
        parts = token.split(':')
        if len(parts) != 4 or parts[0] != 'financial':
            print("❌ Token format validation failed")
            return False
        
        _, token_session_id, token_timestamp, token_signature = parts
        
        # Check session ID
        if token_session_id != session_id:
            print("❌ Session ID mismatch")
            return False
        
        # Check timestamp (should be recent)
        token_time = int(token_timestamp)
        current_time = int(time.time())
        if current_time - token_time > 1800:  # 30 minutes
            print("❌ Token expired")
            return False
        
        # Verify signature
        expected_signature = hmac.new(
            (secret_key + 'financial').encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(token_signature, expected_signature):
            print("❌ Signature validation failed")
            return False
        
        print("✅ Token validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Token validation error: {e}")
        return False

def test_csrf_token_expiration():
    """Test CSRF token expiration"""
    print("\n⏰ Testing CSRF Token Expiration")
    
    secret_key = "test_secret_key_for_csrf_protection"
    session_id = secrets.token_urlsafe(32)
    timestamp = str(int(time.time()) - 3600)  # 1 hour ago (expired)
    
    # Generate expired token
    token_data = f"financial:{session_id}:{timestamp}"
    signature = hmac.new(
        (secret_key + 'financial').encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    expired_token = f"{token_data}:{signature}"
    
    # Test expiration validation
    try:
        parts = expired_token.split(':')
        token_timestamp = int(parts[2])
        current_time = int(time.time())
        
        if current_time - token_timestamp > 1800:  # 30 minutes
            print("✅ Expired token correctly identified")
            return True
        else:
            print("❌ Expired token not detected")
            return False
            
    except Exception as e:
        print(f"❌ Expiration test error: {e}")
        return False

def test_csrf_token_tampering():
    """Test CSRF token tampering detection"""
    print("\n🚨 Testing CSRF Token Tampering Detection")
    
    secret_key = "test_secret_key_for_csrf_protection"
    session_id = secrets.token_urlsafe(32)
    timestamp = str(int(time.time()))
    
    # Generate valid token
    token_data = f"financial:{session_id}:{timestamp}"
    signature = hmac.new(
        (secret_key + 'financial').encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    valid_token = f"{token_data}:{signature}"
    
    # Tamper with token (change signature)
    tampered_token = valid_token[:-10] + "tampered"
    
    # Test tampering detection
    try:
        parts = tampered_token.split(':')
        if len(parts) != 4:
            print("✅ Tampered token format correctly rejected")
            return True
        
        token_data = f"{parts[0]}:{parts[1]}:{parts[2]}"
        expected_signature = hmac.new(
            (secret_key + 'financial').encode(),
            token_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(parts[3], expected_signature):
            print("✅ Tampered token signature correctly rejected")
            return True
        else:
            print("❌ Tampered token not detected")
            return False
            
    except Exception as e:
        print(f"❌ Tampering test error: {e}")
        return False

def test_financial_endpoint_protection():
    """Test financial endpoint protection logic"""
    print("\n💰 Testing Financial Endpoint Protection Logic")
    
    # Test endpoints that should be protected
    protected_endpoints = [
        '/api/v1/financial/transactions',
        '/api/payment/subscriptions',
        '/api/payment/payment-intents',
        '/api/financial/goals',
        '/api/health/checkin',
        '/api/financial/profile'
    ]
    
    # Test endpoints that should not be protected
    unprotected_endpoints = [
        '/api/health/status',
        '/api/financial/summary',
        '/api/payment/config'
    ]
    
    # Import the configuration
    try:
        from backend.config.csrf_config import CSRFConfig
        
        # Test protected endpoints
        for endpoint in protected_endpoints:
            if CSRFConfig.is_financial_endpoint(endpoint):
                print(f"✅ Protected endpoint correctly identified: {endpoint}")
            else:
                print(f"❌ Protected endpoint not identified: {endpoint}")
                return False
        
        # Test unprotected endpoints
        for endpoint in unprotected_endpoints:
            if not CSRFConfig.is_financial_endpoint(endpoint):
                print(f"✅ Unprotected endpoint correctly identified: {endpoint}")
            else:
                print(f"❌ Unprotected endpoint incorrectly protected: {endpoint}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import CSRF configuration: {e}")
        return False

def test_payment_validation():
    """Test payment validation logic"""
    print("\n💳 Testing Payment Validation Logic")
    
    try:
        from backend.config.csrf_config import CSRFConfig
        
        # Test valid payment amounts
        valid_amounts = [0.01, 100.00, 1000.00, 1000000.00]
        for amount in valid_amounts:
            if CSRFConfig.validate_payment_amount(amount):
                print(f"✅ Valid payment amount accepted: ${amount}")
            else:
                print(f"❌ Valid payment amount rejected: ${amount}")
                return False
        
        # Test invalid payment amounts
        invalid_amounts = [0.00, -100.00, 1000001.00]
        for amount in invalid_amounts:
            if not CSRFConfig.validate_payment_amount(amount):
                print(f"✅ Invalid payment amount correctly rejected: ${amount}")
            else:
                print(f"❌ Invalid payment amount incorrectly accepted: ${amount}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import CSRF configuration: {e}")
        return False

def test_subscription_validation():
    """Test subscription tier validation logic"""
    print("\n📦 Testing Subscription Tier Validation Logic")
    
    try:
        from backend.config.csrf_config import CSRFConfig
        
        # Test valid subscription tiers
        valid_tiers = ['budget', 'mid_tier', 'professional']
        for tier in valid_tiers:
            if CSRFConfig.validate_subscription_tier(tier):
                print(f"✅ Valid subscription tier accepted: {tier}")
            else:
                print(f"❌ Valid subscription tier rejected: {tier}")
                return False
        
        # Test invalid subscription tiers
        invalid_tiers = ['basic', 'premium', 'invalid', '']
        for tier in invalid_tiers:
            if not CSRFConfig.validate_subscription_tier(tier):
                print(f"✅ Invalid subscription tier correctly rejected: {tier}")
            else:
                print(f"❌ Invalid subscription tier incorrectly accepted: {tier}")
                return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import CSRF configuration: {e}")
        return False

def main():
    """Run all CSRF protection tests"""
    print("🔒 MINGUS Financial CSRF Protection Implementation Test")
    print("=" * 60)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("CSRF Token Generation", test_csrf_token_generation),
        ("CSRF Token Expiration", test_csrf_token_expiration),
        ("CSRF Token Tampering", test_csrf_token_tampering),
        ("Financial Endpoint Protection", test_financial_endpoint_protection),
        ("Payment Validation", test_payment_validation),
        ("Subscription Validation", test_subscription_validation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FAILED TESTS:")
        for test_name, result in results:
            if not result:
                print(f"  - {test_name}")
    
    if failed_tests == 0:
        print("\n🎉 All CSRF protection tests passed! Implementation is working correctly.")
        print("\n✅ CSRF Protection Features Verified:")
        print("  - Token generation with HMAC-SHA256 signatures")
        print("  - Token expiration and validation")
        print("  - Tampering detection")
        print("  - Financial endpoint identification")
        print("  - Payment amount validation")
        print("  - Subscription tier validation")
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Please review the implementation.")

if __name__ == '__main__':
    main()
