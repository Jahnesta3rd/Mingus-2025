#!/usr/bin/env python3
"""
Cache Manager Utility

Simple cache manager for testing purposes
"""

import json
import time
from typing import Any, Optional, Dict


class CacheManager:
    """Simple in-memory cache manager for testing"""
    
    def __init__(self):
        self.cache = {}
        self.ttl = {}
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set cache value with TTL"""
        self.cache[key] = value
        self.ttl[key] = time.time() + ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if key in self.cache:
            if time.time() < self.ttl.get(key, 0):
                return self.cache[key]
            else:
                # Expired
                del self.cache[key]
                del self.ttl[key]
        return None
    
    def delete(self, key: str) -> None:
        """Delete cache entry"""
        if key in self.cache:
            del self.cache[key]
        if key in self.ttl:
            del self.ttl[key]
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        self.ttl.clear()
