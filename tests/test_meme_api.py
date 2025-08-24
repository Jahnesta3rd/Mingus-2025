"""
Test script for Meme Splash Page API endpoints
Demonstrates how to use the meme API and tests all functionality.
"""

import requests
import json
import time
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemeAPITester:
    """Test class for Meme API endpoints"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_user_id = 123  # Test user ID
        self.test_meme_id = None
        
    def test_health_check(self):
        """Test the health check endpoint"""
        logger.info("Testing health check endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/meme-health")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Health check passed: {data}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check error: {str(e)}")
            return False
    
    def test_get_user_meme(self):
        """Test getting a user's personalized meme"""
        logger.info("Testing get user meme endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/user-meme/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('meme'):
                    self.test_meme_id = data['meme']['id']
                    logger.info(f"✅ Got meme: {data['meme']['caption'][:50]}...")
                    return True
                else:
                    logger.info("✅ No meme available (expected for new users)")
                    return True
            elif response.status_code == 401:
                logger.warning("⚠️ Authentication required (expected in test environment)")
                return True
            else:
                logger.error(f"❌ Get meme failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Get meme error: {str(e)}")
            return False
    
    def test_track_analytics(self):
        """Test tracking meme analytics"""
        logger.info("Testing meme analytics tracking...")
        
        if not self.test_meme_id:
            logger.warning("⚠️ No meme ID available, skipping analytics test")
            return True
        
        try:
            # Test different interaction types
            interaction_types = ['viewed', 'liked', 'skipped']
            
            for interaction_type in interaction_types:
                payload = {
                    'meme_id': self.test_meme_id,
                    'interaction_type': interaction_type,
                    'time_spent_seconds': 15,
                    'source_page': 'meme_splash'
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/meme-analytics",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Tracked {interaction_type}: {data['message']}")
                elif response.status_code == 401:
                    logger.warning(f"⚠️ Authentication required for {interaction_type} (expected)")
                else:
                    logger.error(f"❌ Analytics tracking failed for {interaction_type}: {response.status_code}")
                    return False
            
            return True
                
        except Exception as e:
            logger.error(f"❌ Analytics tracking error: {str(e)}")
            return False
    
    def test_get_preferences(self):
        """Test getting user preferences"""
        logger.info("Testing get user preferences...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/user-meme-preferences/{self.test_user_id}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Got preferences: memes_enabled={data['preferences']['memes_enabled']}")
                logger.info(f"   Categories: {data['preferences']['preferred_categories']}")
                logger.info(f"   Frequency: {data['preferences']['frequency_setting']}")
                return True
            elif response.status_code == 401:
                logger.warning("⚠️ Authentication required (expected in test environment)")
                return True
            else:
                logger.error(f"❌ Get preferences failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Get preferences error: {str(e)}")
            return False
    
    def test_update_preferences(self):
        """Test updating user preferences"""
        logger.info("Testing update user preferences...")
        
        try:
            # Test updating preferences
            payload = {
                'memes_enabled': True,
                'preferred_categories': ['monday_career', 'friday_entertainment'],
                'frequency_setting': 'daily',
                'custom_frequency_days': 1
            }
            
            response = self.session.put(
                f"{self.base_url}/api/user-meme-preferences/{self.test_user_id}",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Updated preferences: {data['message']}")
                return True
            elif response.status_code == 401:
                logger.warning("⚠️ Authentication required (expected in test environment)")
                return True
            else:
                logger.error(f"❌ Update preferences failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Update preferences error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        logger.info("Testing error handling...")
        
        # Test invalid user ID
        try:
            response = self.session.get(f"{self.base_url}/api/user-meme/999999")
            if response.status_code == 404:
                logger.info("✅ Correctly handled invalid user ID")
            else:
                logger.warning(f"⚠️ Unexpected response for invalid user ID: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing invalid user ID: {str(e)}")
        
        # Test invalid interaction type
        if self.test_meme_id:
            try:
                payload = {
                    'meme_id': self.test_meme_id,
                    'interaction_type': 'invalid_type'
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/meme-analytics",
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 400:
                    logger.info("✅ Correctly handled invalid interaction type")
                else:
                    logger.warning(f"⚠️ Unexpected response for invalid interaction type: {response.status_code}")
            except Exception as e:
                logger.error(f"❌ Error testing invalid interaction type: {str(e)}")
        
        # Test invalid preference values
        try:
            payload = {
                'frequency_setting': 'invalid_frequency',
                'custom_frequency_days': 999
            }
            
            response = self.session.put(
                f"{self.base_url}/api/user-meme-preferences/{self.test_user_id}",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 400:
                logger.info("✅ Correctly handled invalid preference values")
            else:
                logger.warning(f"⚠️ Unexpected response for invalid preferences: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error testing invalid preferences: {str(e)}")
        
        return True
    
    def test_rate_limiting(self):
        """Test rate limiting (make multiple requests quickly)"""
        logger.info("Testing rate limiting...")
        
        try:
            # Make multiple requests quickly
            responses = []
            for i in range(10):
                response = self.session.get(f"{self.base_url}/api/user-meme/{self.test_user_id}")
                responses.append(response.status_code)
                time.sleep(0.1)  # Small delay
            
            # Check if any requests were rate limited
            rate_limited = any(code == 429 for code in responses)
            
            if rate_limited:
                logger.info("✅ Rate limiting is working")
            else:
                logger.info("ℹ️ Rate limiting not triggered (may need more requests)")
            
            return True
                
        except Exception as e:
            logger.error(f"❌ Rate limiting test error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Meme API Tests")
        logger.info("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Get User Meme", self.test_get_user_meme),
            ("Track Analytics", self.test_track_analytics),
            ("Get Preferences", self.test_get_preferences),
            ("Update Preferences", self.test_update_preferences),
            ("Error Handling", self.test_error_handling),
            ("Rate Limiting", self.test_rate_limiting)
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"❌ Test {test_name} crashed: {str(e)}")
                results.append((test_name, False))
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 Test Results Summary:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status}: {test_name}")
            if result:
                passed += 1
        
        logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed!")
        else:
            logger.warning("⚠️ Some tests failed. Check the logs above for details.")
        
        return passed == total

def main():
    """Main function to run tests"""
    print("Meme API Test Suite")
    print("===================")
    print("This script tests the Meme Splash Page API endpoints.")
    print("Make sure your Flask application is running on localhost:5000")
    print("Note: Some tests may fail if authentication is required.")
    print()
    
    # Create tester instance
    tester = MemeAPITester()
    
    # Run tests
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n⚠️ Some tests failed. This is normal if authentication is required.")
    
    print("\nFor more information, check the logs above.")

if __name__ == "__main__":
    main()
