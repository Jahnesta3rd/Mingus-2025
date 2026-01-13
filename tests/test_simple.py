#!/usr/bin/env python3
"""
Simple test to verify the test framework works
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.utils.cache import CacheManager
from backend.utils.encryption import EncryptionService
from backend.utils.rate_limiting import RateLimiter
from backend.utils.notifications import NotificationService


class TestBasicFunctionality:
    """Test basic functionality without database dependencies"""
    
    def test_cache_manager(self):
        """Test cache manager functionality"""
        cache = CacheManager()
        cache.set('test_key', 'test_value', ttl=3600)
        value = cache.get('test_key')
        assert value == 'test_value'
        
        # Test cache expiration
        cache.set('expire_key', 'expire_value', ttl=1)
        import time
        time.sleep(1.1)
        expired_value = cache.get('expire_key')
        assert expired_value is None
    
    def test_encryption_service(self):
        """Test encryption service functionality with proper Fernet encryption"""
        import os
        from cryptography.fernet import Fernet
        
        # Set test encryption key if not already set
        if 'ENCRYPTION_KEY' not in os.environ:
            test_key = Fernet.generate_key().decode()
            os.environ['ENCRYPTION_KEY'] = test_key
        
        encryption = EncryptionService()
        test_data = 'sensitive data'
        encrypted = encryption.encrypt(test_data)
        decrypted = encryption.decrypt(encrypted)
        
        # Verify encryption works
        assert decrypted == test_data
        assert encrypted != test_data  # Should be different
        # Verify encrypted data is longer (Fernet adds authentication and metadata)
        assert len(encrypted) > len(test_data)
        
        # Test that same data produces different encrypted output (due to timestamp)
        encrypted2 = encryption.encrypt(test_data)
        # Note: Fernet includes timestamp, so same data encrypted twice may differ
        # But both should decrypt to the same value
        assert encryption.decrypt(encrypted2) == test_data
    
    def test_rate_limiter(self):
        """Test rate limiter functionality"""
        limiter = RateLimiter()
        
        # Test allowed requests
        for i in range(5):
            is_allowed = limiter.is_allowed(f'test_user_{i}', 'default')
            assert is_allowed == True
        
        # Test remaining requests
        remaining = limiter.get_remaining_requests('test_user_0', 'default')
        assert remaining >= 0
    
    def test_notification_service(self):
        """Test notification service functionality"""
        notification = NotificationService()
        
        # Test daily outlook notification
        result = notification.send_daily_outlook_notification(1, 1)
        assert result == True
        
        # Test streak milestone notification
        result = notification.send_streak_milestone_notification(1, 7)
        assert result == True
        
        # Check notifications were recorded
        assert len(notification.notifications_sent) == 2
    
    def test_basic_math(self):
        """Test basic math operations"""
        assert 1 + 1 == 2
        assert 2 * 3 == 6
        assert 10 / 2 == 5
        assert 2 ** 3 == 8
    
    def test_string_operations(self):
        """Test string operations"""
        text = 'Hello World'
        assert len(text) == 11
        assert text.upper() == 'HELLO WORLD'
        assert text.lower() == 'hello world'
        assert text.replace('World', 'Python') == 'Hello Python'
    
    def test_list_operations(self):
        """Test list operations"""
        numbers = [1, 2, 3, 4, 5]
        assert len(numbers) == 5
        assert sum(numbers) == 15
        assert max(numbers) == 5
        assert min(numbers) == 1
        assert 3 in numbers
        assert 6 not in numbers


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
