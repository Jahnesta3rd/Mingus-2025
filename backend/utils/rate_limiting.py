#!/usr/bin/env python3
"""
Rate Limiting Utility

Simple rate limiter for testing purposes
"""

import time
from typing import Dict, Optional


class RateLimiter:
    """Simple rate limiter for testing"""
    
    def __init__(self):
        self.requests = {}
        self.limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'api': {'requests': 1000, 'window': 3600},    # 1000 requests per hour
            'user': {'requests': 50, 'window': 3600}      # 50 requests per hour per user
        }
    
    def is_allowed(self, key: str, limit_type: str = 'default') -> bool:
        """Check if request is allowed"""
        current_time = time.time()
        limit_config = self.limits.get(limit_type, self.limits['default'])
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests outside window
        window_start = current_time - limit_config['window']
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        # Check if under limit
        if len(self.requests[key]) < limit_config['requests']:
            self.requests[key].append(current_time)
            return True
        
        return False
    
    def get_remaining_requests(self, key: str, limit_type: str = 'default') -> int:
        """Get remaining requests for key"""
        current_time = time.time()
        limit_config = self.limits.get(limit_type, self.limits['default'])
        
        if key not in self.requests:
            return limit_config['requests']
        
        # Clean old requests
        window_start = current_time - limit_config['window']
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        return max(0, limit_config['requests'] - len(self.requests[key]))
