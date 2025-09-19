#!/usr/bin/env python3
"""
MINGUS Optimal Living Location - Feature Flag Configuration

Production feature flags for housing location feature including:
- Gradual rollout configuration
- A/B testing setup
- Emergency kill switch
- Tier-based feature enablement
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

class FeatureFlagType(Enum):
    """Types of feature flags"""
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    USER_GROUP = "user_group"
    TIER_BASED = "tier_based"
    A_B_TEST = "a_b_test"

class FeatureFlagStatus(Enum):
    """Feature flag status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ROLLING_OUT = "rolling_out"
    ROLLING_BACK = "rolling_back"

class HousingFeatureFlags:
    """Feature flag manager for housing location feature"""
    
    def __init__(self):
        self.flags = self._initialize_feature_flags()
        self.rollout_config = self._initialize_rollout_config()
        self.ab_test_config = self._initialize_ab_test_config()
        self.emergency_switches = self._initialize_emergency_switches()
    
    def _initialize_feature_flags(self) -> Dict[str, Dict[str, Any]]:
        """Initialize housing feature flags"""
        return {
            'optimal_location_enabled': {
                'type': FeatureFlagType.BOOLEAN,
                'status': FeatureFlagStatus.ENABLED,
                'description': 'Enable/disable optimal location feature',
                'default_value': True,
                'tier_requirements': ['mid_tier', 'professional'],
                'rollout_percentage': 100
            },
            'housing_search_enabled': {
                'type': FeatureFlagType.BOOLEAN,
                'status': FeatureFlagStatus.ENABLED,
                'description': 'Enable/disable housing search functionality',
                'default_value': True,
                'tier_requirements': ['mid_tier', 'professional'],
                'rollout_percentage': 100
            },
            'scenario_creation_enabled': {
                'type': FeatureFlagType.BOOLEAN,
                'status': FeatureFlagStatus.ENABLED,
                'description': 'Enable/disable scenario creation',
                'default_value': True,
                'tier_requirements': ['mid_tier', 'professional'],
                'rollout_percentage': 100
            },
            'career_integration_enabled': {
                'type': FeatureFlagType.BOOLEAN,
                'status': FeatureFlagStatus.ENABLED,
                'description': 'Enable/disable career integration features',
                'default_value': True,
                'tier_requirements': ['mid_tier', 'professional'],
                'rollout_percentage': 100
            },
            'external_api_integration': {
                'type': FeatureFlagType.BOOLEAN,
                'status': FeatureFlagStatus.ENABLED,
                'description': 'Enable/disable external API integrations',
                'default_value': True,
                'tier_requirements': ['mid_tier', 'professional'],
                'rollout_percentage': 100
            },
            'advanced_analytics': {
                'type': FeatureFlagType.BOOLEAN,
                'status': FeatureFlagStatus.ROLLING_OUT,
                'description': 'Enable/disable advanced analytics',
                'default_value': False,
                'tier_requirements': ['professional'],
                'rollout_percentage': 50
            },
            'real_time_notifications': {
                'type': FeatureFlagType.BOOLEAN,
                'status': FeatureFlagStatus.ROLLING_OUT,
                'description': 'Enable/disable real-time notifications',
                'default_value': False,
                'tier_requirements': ['professional'],
                'rollout_percentage': 25
            },
            'ai_recommendations': {
                'type': FeatureFlagType.BOOLEAN,
                'status': FeatureFlagStatus.DISABLED,
                'description': 'Enable/disable AI-powered recommendations',
                'default_value': False,
                'tier_requirements': ['professional'],
                'rollout_percentage': 0
            }
        }
    
    def _initialize_rollout_config(self) -> Dict[str, Any]:
        """Initialize gradual rollout configuration"""
        return {
            'rollout_strategy': os.environ.get('HOUSING_ROLLOUT_STRATEGY', 'percentage'),
            'rollout_percentage': int(os.environ.get('HOUSING_ROLLOUT_PERCENTAGE', 100)),
            'rollout_groups': [
                'beta_users',
                'premium_users', 
                'new_users',
                'returning_users'
            ],
            'rollout_regions': [
                'us-east-1',
                'us-west-2',
                'eu-west-1'
            ],
            'rollout_schedule': {
                'start_date': datetime.utcnow(),
                'phases': [
                    {'percentage': 10, 'duration_hours': 24},
                    {'percentage': 25, 'duration_hours': 48},
                    {'percentage': 50, 'duration_hours': 72},
                    {'percentage': 100, 'duration_hours': 168}
                ]
            }
        }
    
    def _initialize_ab_test_config(self) -> Dict[str, Any]:
        """Initialize A/B testing configuration"""
        return {
            'ui_variations': {
                'search_interface': {
                    'control': 'original_search_ui',
                    'variants': [
                        'simplified_search_ui',
                        'advanced_search_ui',
                        'mobile_optimized_ui'
                    ],
                    'traffic_split': [50, 25, 25],
                    'metrics': ['conversion_rate', 'time_to_search', 'user_satisfaction']
                },
                'scenario_display': {
                    'control': 'list_view',
                    'variants': [
                        'card_view',
                        'map_view',
                        'comparison_view'
                    ],
                    'traffic_split': [40, 30, 30],
                    'metrics': ['scenario_creation_rate', 'time_spent', 'favorite_rate']
                },
                'recommendation_algorithm': {
                    'control': 'basic_algorithm',
                    'variants': [
                        'ml_enhanced_algorithm',
                        'user_preference_algorithm',
                        'location_intelligence_algorithm'
                    ],
                    'traffic_split': [60, 20, 20],
                    'metrics': ['recommendation_accuracy', 'user_engagement', 'conversion_rate']
                }
            },
            'test_duration_days': 14,
            'minimum_sample_size': 1000,
            'statistical_significance': 0.95
        }
    
    def _initialize_emergency_switches(self) -> Dict[str, Any]:
        """Initialize emergency kill switches"""
        return {
            'housing_feature_kill_switch': {
                'enabled': False,
                'reason': None,
                'activated_at': None,
                'activated_by': None
            },
            'external_api_kill_switch': {
                'enabled': False,
                'reason': None,
                'activated_at': None,
                'activated_by': None
            },
            'database_kill_switch': {
                'enabled': False,
                'reason': None,
                'activated_at': None,
                'activated_by': None
            },
            'rate_limiting_kill_switch': {
                'enabled': False,
                'reason': None,
                'activated_at': None,
                'activated_by': None
            }
        }
    
    def is_feature_enabled(self, feature_name: str, user_id: int = None, 
                          user_tier: str = None, ip_address: str = None) -> bool:
        """Check if feature is enabled for user"""
        try:
            # Check emergency kill switches first
            if self._is_emergency_kill_switch_active(feature_name):
                return False
            
            # Get feature flag
            flag = self.flags.get(feature_name)
            if not flag:
                logger.warning(f"Unknown feature flag: {feature_name}")
                return False
            
            # Check if feature is disabled
            if flag['status'] == FeatureFlagStatus.DISABLED:
                return False
            
            # Check tier requirements
            if user_tier and not self._check_tier_requirements(flag, user_tier):
                return False
            
            # Check rollout percentage
            if not self._check_rollout_percentage(flag, user_id, ip_address):
                return False
            
            # Check A/B test assignment
            if flag['type'] == FeatureFlagType.A_B_TEST:
                return self._get_ab_test_assignment(feature_name, user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking feature flag {feature_name}: {e}")
            return False
    
    def _is_emergency_kill_switch_active(self, feature_name: str) -> bool:
        """Check if emergency kill switch is active"""
        # Check general housing feature kill switch
        if self.emergency_switches['housing_feature_kill_switch']['enabled']:
            return True
        
        # Check specific feature kill switches
        if feature_name in ['housing_search_enabled', 'scenario_creation_enabled']:
            return self.emergency_switches['external_api_kill_switch']['enabled']
        
        return False
    
    def _check_tier_requirements(self, flag: Dict[str, Any], user_tier: str) -> bool:
        """Check if user tier meets requirements"""
        tier_requirements = flag.get('tier_requirements', [])
        if not tier_requirements:
            return True
        
        tier_hierarchy = {
            'budget': 1,
            'mid_tier': 2,
            'professional': 3
        }
        
        user_tier_level = tier_hierarchy.get(user_tier, 0)
        required_tier_level = min(tier_hierarchy.get(tier, 0) for tier in tier_requirements)
        
        return user_tier_level >= required_tier_level
    
    def _check_rollout_percentage(self, flag: Dict[str, Any], user_id: int, ip_address: str) -> bool:
        """Check if user is in rollout percentage"""
        rollout_percentage = flag.get('rollout_percentage', 100)
        
        if rollout_percentage >= 100:
            return True
        
        # Use user ID for consistent assignment
        if user_id:
            user_hash = hashlib.md5(f"{user_id}".encode()).hexdigest()
            user_percentage = int(user_hash[:2], 16) % 100
            return user_percentage < rollout_percentage
        
        # Fallback to IP address
        if ip_address:
            ip_hash = hashlib.md5(ip_address.encode()).hexdigest()
            ip_percentage = int(ip_hash[:2], 16) % 100
            return ip_percentage < rollout_percentage
        
        return False
    
    def _get_ab_test_assignment(self, feature_name: str, user_id: int) -> bool:
        """Get A/B test assignment for user"""
        ab_config = self.ab_test_config.get('ui_variations', {})
        
        if feature_name not in ab_config:
            return True
        
        # Use user ID for consistent assignment
        user_hash = hashlib.md5(f"{user_id}_{feature_name}".encode()).hexdigest()
        assignment = int(user_hash[:2], 16) % 100
        
        # Check if user is in control group
        return assignment < 50  # 50% control, 50% variants
    
    def activate_emergency_kill_switch(self, switch_name: str, reason: str, 
                                     activated_by: str) -> bool:
        """Activate emergency kill switch"""
        try:
            if switch_name not in self.emergency_switches:
                logger.error(f"Unknown emergency switch: {switch_name}")
                return False
            
            self.emergency_switches[switch_name] = {
                'enabled': True,
                'reason': reason,
                'activated_at': datetime.utcnow().isoformat(),
                'activated_by': activated_by
            }
            
            logger.critical(f"Emergency kill switch activated: {switch_name} - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating emergency switch {switch_name}: {e}")
            return False
    
    def deactivate_emergency_kill_switch(self, switch_name: str, deactivated_by: str) -> bool:
        """Deactivate emergency kill switch"""
        try:
            if switch_name not in self.emergency_switches:
                logger.error(f"Unknown emergency switch: {switch_name}")
                return False
            
            self.emergency_switches[switch_name] = {
                'enabled': False,
                'reason': None,
                'activated_at': None,
                'activated_by': None,
                'deactivated_at': datetime.utcnow().isoformat(),
                'deactivated_by': deactivated_by
            }
            
            logger.info(f"Emergency kill switch deactivated: {switch_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating emergency switch {switch_name}: {e}")
            return False
    
    def get_ab_test_variant(self, test_name: str, user_id: int) -> str:
        """Get A/B test variant for user"""
        try:
            ab_config = self.ab_test_config.get('ui_variations', {})
            
            if test_name not in ab_config:
                return 'control'
            
            test_config = ab_config[test_name]
            variants = [test_config['control']] + test_config['variants']
            traffic_split = [50] + test_config['traffic_split']
            
            # Use user ID for consistent assignment
            user_hash = hashlib.md5(f"{user_id}_{test_name}".encode()).hexdigest()
            assignment = int(user_hash[:2], 16) % 100
            
            # Determine variant based on traffic split
            cumulative = 0
            for i, percentage in enumerate(traffic_split):
                cumulative += percentage
                if assignment < cumulative:
                    return variants[i]
            
            return variants[0]  # Fallback to control
            
        except Exception as e:
            logger.error(f"Error getting A/B test variant: {e}")
            return 'control'
    
    def update_feature_flag(self, feature_name: str, updates: Dict[str, Any]) -> bool:
        """Update feature flag configuration"""
        try:
            if feature_name not in self.flags:
                logger.error(f"Unknown feature flag: {feature_name}")
                return False
            
            # Validate updates
            allowed_updates = ['status', 'rollout_percentage', 'default_value']
            for key in updates:
                if key not in allowed_updates:
                    logger.error(f"Invalid update field: {key}")
                    return False
            
            # Apply updates
            self.flags[feature_name].update(updates)
            
            logger.info(f"Feature flag updated: {feature_name} - {updates}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating feature flag {feature_name}: {e}")
            return False
    
    def get_feature_flag_status(self, feature_name: str) -> Dict[str, Any]:
        """Get feature flag status"""
        return self.flags.get(feature_name, {})
    
    def get_all_feature_flags(self) -> Dict[str, Any]:
        """Get all feature flags"""
        return {
            'flags': self.flags,
            'rollout_config': self.rollout_config,
            'ab_test_config': self.ab_test_config,
            'emergency_switches': self.emergency_switches
        }
    
    def get_rollout_progress(self) -> Dict[str, Any]:
        """Get current rollout progress"""
        current_time = datetime.utcnow()
        start_date = self.rollout_config['rollout_schedule']['start_date']
        elapsed_hours = (current_time - start_date).total_seconds() / 3600
        
        phases = self.rollout_config['rollout_schedule']['phases']
        current_phase = 0
        cumulative_hours = 0
        
        for i, phase in enumerate(phases):
            cumulative_hours += phase['duration_hours']
            if elapsed_hours <= cumulative_hours:
                current_phase = i
                break
        
        return {
            'current_phase': current_phase,
            'elapsed_hours': elapsed_hours,
            'current_percentage': phases[current_phase]['percentage'] if current_phase < len(phases) else 100,
            'next_phase_in_hours': max(0, cumulative_hours - elapsed_hours) if current_phase < len(phases) else 0
        }

class HousingFeatureFlagMiddleware:
    """Middleware for feature flag integration"""
    
    def __init__(self, feature_flags: HousingFeatureFlags):
        self.feature_flags = feature_flags
    
    def check_feature_access(self, feature_name: str, user_id: int = None, 
                           user_tier: str = None, ip_address: str = None) -> bool:
        """Check feature access with middleware logic"""
        # Add additional middleware logic here
        # e.g., logging, metrics, caching
        
        return self.feature_flags.is_feature_enabled(
            feature_name, user_id, user_tier, ip_address
        )
    
    def get_user_feature_set(self, user_id: int, user_tier: str = None, 
                           ip_address: str = None) -> Dict[str, bool]:
        """Get all enabled features for user"""
        user_features = {}
        
        for feature_name in self.feature_flags.flags.keys():
            user_features[feature_name] = self.check_feature_access(
                feature_name, user_id, user_tier, ip_address
            )
        
        return user_features

# Global instances
housing_feature_flags = HousingFeatureFlags()
housing_feature_middleware = HousingFeatureFlagMiddleware(housing_feature_flags)

# Export feature flag components
__all__ = [
    'housing_feature_flags',
    'housing_feature_middleware',
    'FeatureFlagType',
    'FeatureFlagStatus'
]
