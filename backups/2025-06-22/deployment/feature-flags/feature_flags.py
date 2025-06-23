#!/usr/bin/env python3
"""
Feature Flag System for Mingus Application
Enables gradual rollouts, A/B testing, and feature toggles
"""

import os
import json
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureFlagType(Enum):
    """Types of feature flags"""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_GROUP = "user_group"
    TIME_BASED = "time_based"

@dataclass
class FeatureFlag:
    """Feature flag configuration"""
    name: str
    type: FeatureFlagType
    enabled: bool
    description: str
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    # Boolean flag
    value: bool = False
    
    # Percentage rollout (0-100)
    percentage: int = 0
    
    # User groups
    user_groups: List[str] = None
    
    # Time-based settings
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # A/B testing settings
    ab_test_enabled: bool = False
    ab_test_variants: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_groups is None:
            self.user_groups = []
        if self.ab_test_variants is None:
            self.ab_test_variants = {}

class FeatureFlagManager:
    def __init__(self):
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        self.cache_ttl = 300  # 5 minutes
        self.flags_cache_key = "feature_flags"
        
        # Initialize default flags
        self.initialize_default_flags()
    
    def initialize_default_flags(self):
        """Initialize default feature flags"""
        default_flags = [
            {
                "name": "job_security_ml",
                "type": FeatureFlagType.BOOLEAN,
                "enabled": True,
                "description": "Enable ML-powered job security predictions",
                "value": True,
                "created_by": "system"
            },
            {
                "name": "advanced_analytics",
                "type": FeatureFlagType.PERCENTAGE,
                "enabled": True,
                "description": "Rollout advanced analytics dashboard",
                "percentage": 50,
                "created_by": "system"
            },
            {
                "name": "real_time_notifications",
                "type": FeatureFlagType.USER_GROUP,
                "enabled": True,
                "description": "Enable real-time notifications for premium users",
                "user_groups": ["premium", "enterprise"],
                "created_by": "system"
            },
            {
                "name": "beta_features",
                "type": FeatureFlagType.BOOLEAN,
                "enabled": False,
                "description": "Enable beta features for testing",
                "value": False,
                "created_by": "system"
            },
            {
                "name": "new_onboarding_flow",
                "type": FeatureFlagType.PERCENTAGE,
                "enabled": True,
                "description": "Rollout new onboarding experience",
                "percentage": 25,
                "ab_test_enabled": True,
                "ab_test_variants": {
                    "control": {"flow": "original"},
                    "variant_a": {"flow": "new_simplified"},
                    "variant_b": {"flow": "new_guided"}
                },
                "created_by": "system"
            }
        ]
        
        for flag_data in default_flags:
            self.create_flag(FeatureFlag(
                name=flag_data["name"],
                type=flag_data["type"],
                enabled=flag_data["enabled"],
                description=flag_data["description"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by=flag_data["created_by"],
                value=flag_data.get("value", False),
                percentage=flag_data.get("percentage", 0),
                user_groups=flag_data.get("user_groups", []),
                ab_test_enabled=flag_data.get("ab_test_enabled", False),
                ab_test_variants=flag_data.get("ab_test_variants", {})
            ))
    
    def create_flag(self, flag: FeatureFlag) -> bool:
        """Create a new feature flag"""
        try:
            flag_dict = asdict(flag)
            flag_dict['created_at'] = flag.created_at.isoformat()
            flag_dict['updated_at'] = flag.updated_at.isoformat()
            flag_dict['type'] = flag.type.value
            
            self.redis_client.hset(
                self.flags_cache_key,
                flag.name,
                json.dumps(flag_dict)
            )
            
            # Invalidate cache
            self.redis_client.delete(f"{self.flags_cache_key}:cache")
            
            logger.info(f"Created feature flag: {flag.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating feature flag {flag.name}: {str(e)}")
            return False
    
    def update_flag(self, flag_name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing feature flag"""
        try:
            flag = self.get_flag(flag_name)
            if not flag:
                return False
            
            # Update fields
            for key, value in updates.items():
                if hasattr(flag, key):
                    setattr(flag, key, value)
            
            flag.updated_at = datetime.now()
            
            # Save updated flag
            return self.create_flag(flag)
            
        except Exception as e:
            logger.error(f"Error updating feature flag {flag_name}: {str(e)}")
            return False
    
    def delete_flag(self, flag_name: str) -> bool:
        """Delete a feature flag"""
        try:
            self.redis_client.hdel(self.flags_cache_key, flag_name)
            self.redis_client.delete(f"{self.flags_cache_key}:cache")
            
            logger.info(f"Deleted feature flag: {flag_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting feature flag {flag_name}: {str(e)}")
            return False
    
    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name"""
        try:
            # Try cache first
            cached = self.redis_client.get(f"{self.flags_cache_key}:cache")
            if cached:
                flags_data = json.loads(cached)
                if flag_name in flags_data:
                    return self._dict_to_flag(flags_data[flag_name])
            
            # Get from Redis
            flag_data = self.redis_client.hget(self.flags_cache_key, flag_name)
            if flag_data:
                flag = self._dict_to_flag(json.loads(flag_data))
                
                # Update cache
                self._update_cache()
                
                return flag
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting feature flag {flag_name}: {str(e)}")
            return None
    
    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags"""
        try:
            # Try cache first
            cached = self.redis_client.get(f"{self.flags_cache_key}:cache")
            if cached:
                flags_data = json.loads(cached)
                return {name: self._dict_to_flag(data) for name, data in flags_data.items()}
            
            # Get from Redis
            flags_data = self.redis_client.hgetall(self.flags_cache_key)
            flags = {}
            
            for name, data in flags_data.items():
                flags[name.decode()] = self._dict_to_flag(json.loads(data))
            
            # Update cache
            self._update_cache()
            
            return flags
            
        except Exception as e:
            logger.error(f"Error getting all feature flags: {str(e)}")
            return {}
    
    def is_enabled(self, flag_name: str, user_id: Optional[str] = None, 
                   user_groups: Optional[List[str]] = None) -> bool:
        """Check if a feature flag is enabled for a user"""
        try:
            flag = self.get_flag(flag_name)
            if not flag or not flag.enabled:
                return False
            
            # Check time-based flags
            if flag.start_date and datetime.now() < flag.start_date:
                return False
            
            if flag.end_date and datetime.now() > flag.end_date:
                return False
            
            # Boolean flags
            if flag.type == FeatureFlagType.BOOLEAN:
                return flag.value
            
            # Percentage rollout
            elif flag.type == FeatureFlagType.PERCENTAGE:
                if not user_id:
                    return False
                
                # Use user_id to determine consistent rollout
                import hashlib
                user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
                user_percentage = user_hash % 100
                
                return user_percentage < flag.percentage
            
            # User group flags
            elif flag.type == FeatureFlagType.USER_GROUP:
                if not user_groups:
                    return False
                
                return any(group in flag.user_groups for group in user_groups)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking feature flag {flag_name}: {str(e)}")
            return False
    
    def get_ab_test_variant(self, flag_name: str, user_id: str) -> Optional[str]:
        """Get A/B test variant for a user"""
        try:
            flag = self.get_flag(flag_name)
            if not flag or not flag.ab_test_enabled:
                return None
            
            if not flag.ab_test_variants:
                return None
            
            # Use user_id to determine consistent variant
            import hashlib
            user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            variant_index = user_hash % len(flag.ab_test_variants)
            
            variants = list(flag.ab_test_variants.keys())
            return variants[variant_index]
            
        except Exception as e:
            logger.error(f"Error getting A/B test variant for {flag_name}: {str(e)}")
            return None
    
    def track_feature_usage(self, flag_name: str, user_id: str, 
                           variant: Optional[str] = None, 
                           metadata: Optional[Dict[str, Any]] = None):
        """Track feature flag usage for analytics"""
        try:
            usage_data = {
                "flag_name": flag_name,
                "user_id": user_id,
                "variant": variant,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store in Redis for analytics
            self.redis_client.lpush(
                f"feature_usage:{flag_name}",
                json.dumps(usage_data)
            )
            
            # Keep only last 1000 events
            self.redis_client.ltrim(f"feature_usage:{flag_name}", 0, 999)
            
        except Exception as e:
            logger.error(f"Error tracking feature usage: {str(e)}")
    
    def get_feature_usage_stats(self, flag_name: str, 
                               days: int = 7) -> Dict[str, Any]:
        """Get feature usage statistics"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            usage_key = f"feature_usage:{flag_name}"
            
            # Get all usage events
            events = self.redis_client.lrange(usage_key, 0, -1)
            
            stats = {
                "total_usage": 0,
                "unique_users": set(),
                "variants": {},
                "daily_usage": {}
            }
            
            for event_data in events:
                event = json.loads(event_data)
                event_time = datetime.fromisoformat(event["timestamp"])
                
                if event_time >= cutoff_time:
                    stats["total_usage"] += 1
                    stats["unique_users"].add(event["user_id"])
                    
                    variant = event.get("variant", "default")
                    stats["variants"][variant] = stats["variants"].get(variant, 0) + 1
                    
                    date_key = event_time.strftime("%Y-%m-%d")
                    stats["daily_usage"][date_key] = stats["daily_usage"].get(date_key, 0) + 1
            
            # Convert set to count
            stats["unique_users"] = len(stats["unique_users"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting feature usage stats: {str(e)}")
            return {}
    
    def _dict_to_flag(self, flag_dict: Dict[str, Any]) -> FeatureFlag:
        """Convert dictionary to FeatureFlag object"""
        flag_dict['type'] = FeatureFlagType(flag_dict['type'])
        flag_dict['created_at'] = datetime.fromisoformat(flag_dict['created_at'])
        flag_dict['updated_at'] = datetime.fromisoformat(flag_dict['updated_at'])
        
        if flag_dict.get('start_date'):
            flag_dict['start_date'] = datetime.fromisoformat(flag_dict['start_date'])
        if flag_dict.get('end_date'):
            flag_dict['end_date'] = datetime.fromisoformat(flag_dict['end_date'])
        
        return FeatureFlag(**flag_dict)
    
    def _update_cache(self):
        """Update the feature flags cache"""
        try:
            flags_data = self.redis_client.hgetall(self.flags_cache_key)
            cache_data = {}
            
            for name, data in flags_data.items():
                cache_data[name.decode()] = json.loads(data)
            
            self.redis_client.setex(
                f"{self.flags_cache_key}:cache",
                self.cache_ttl,
                json.dumps(cache_data)
            )
            
        except Exception as e:
            logger.error(f"Error updating cache: {str(e)}")

# Global feature flag manager instance
feature_flags = FeatureFlagManager()

# Decorator for feature flag checks
def feature_flag(flag_name: str, user_id_func=None, user_groups_func=None):
    """Decorator to check feature flags"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get user context
            user_id = None
            user_groups = None
            
            if user_id_func:
                user_id = user_id_func(*args, **kwargs)
            if user_groups_func:
                user_groups = user_groups_func(*args, **kwargs)
            
            # Check if feature is enabled
            if feature_flags.is_enabled(flag_name, user_id, user_groups):
                # Track usage
                if user_id:
                    feature_flags.track_feature_usage(flag_name, user_id)
                
                return func(*args, **kwargs)
            else:
                # Return default behavior or raise exception
                logger.info(f"Feature flag {flag_name} disabled for user {user_id}")
                return None
        
        return wrapper
    return decorator 