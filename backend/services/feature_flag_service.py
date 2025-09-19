#!/usr/bin/env python3
"""
Feature Flag Service for Mingus Application
Manages feature access control and billing integration for add-ons
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class FeatureTier(Enum):
    """User subscription tiers"""
    BUDGET = "budget"
    BUDGET_CAREER_VEHICLE = "budget_career_vehicle"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"

class FeatureFlag(Enum):
    """Available feature flags"""
    CAREER_VEHICLE_OPTIMIZATION = "career_vehicle_optimization"
    ADVANCED_ANALYTICS = "advanced_analytics"
    BUSINESS_FEATURES = "business_features"
    PRIORITY_SUPPORT = "priority_support"
    OPTIMAL_LOCATION = "optimal_location"

class FeatureFlagService:
    """Service for managing feature flags and user access control"""
    
    def __init__(self):
        self.feature_tiers = {
            FeatureTier.BUDGET: {
                'price': 15.00,
                'features': [],
                'description': 'Basic financial wellness only'
            },
            FeatureTier.BUDGET_CAREER_VEHICLE: {
                'price': 22.00,
                'features': [FeatureFlag.CAREER_VEHICLE_OPTIMIZATION],
                'description': 'Basic + job/commute optimization',
                'addon_price': 7.00,
                'base_tier': FeatureTier.BUDGET
            },
            FeatureTier.MID_TIER: {
                'price': 35.00,
                'features': [
                    FeatureFlag.CAREER_VEHICLE_OPTIMIZATION,
                    FeatureFlag.ADVANCED_ANALYTICS,
                    FeatureFlag.OPTIMAL_LOCATION
                ],
                'description': 'Complete vehicle management + career optimization'
            },
            FeatureTier.PROFESSIONAL: {
                'price': 100.00,
                'features': [
                    FeatureFlag.CAREER_VEHICLE_OPTIMIZATION,
                    FeatureFlag.ADVANCED_ANALYTICS,
                    FeatureFlag.BUSINESS_FEATURES,
                    FeatureFlag.PRIORITY_SUPPORT,
                    FeatureFlag.OPTIMAL_LOCATION
                ],
                'description': 'Everything + business/executive features'
            }
        }
        
        self.feature_descriptions = {
            FeatureFlag.CAREER_VEHICLE_OPTIMIZATION: {
                'name': 'Career-Vehicle Optimization',
                'description': 'Job opportunity cost calculator, commute impact analysis, career move planning, and budget optimization',
                'addon_price': 7.00,
                'available_tiers': [FeatureTier.BUDGET_CAREER_VEHICLE, FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]
            },
            FeatureFlag.ADVANCED_ANALYTICS: {
                'name': 'Advanced Analytics',
                'description': 'Comprehensive financial analytics and reporting',
                'addon_price': None,
                'available_tiers': [FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]
            },
            FeatureFlag.BUSINESS_FEATURES: {
                'name': 'Business Features',
                'description': 'Business and executive-level financial management tools',
                'addon_price': None,
                'available_tiers': [FeatureTier.PROFESSIONAL]
            },
            FeatureFlag.PRIORITY_SUPPORT: {
                'name': 'Priority Support',
                'description': '24/7 priority customer support',
                'addon_price': None,
                'available_tiers': [FeatureTier.PROFESSIONAL]
            },
            FeatureFlag.OPTIMAL_LOCATION: {
                'name': 'Optimal Living Location',
                'description': 'Find the best housing locations based on commute, financial situation, and career opportunities',
                'addon_price': None,
                'available_tiers': [FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]
            }
        }
        
        # Optimal Location feature configuration by tier
        self.OPTIMAL_LOCATION_FEATURES = {
            FeatureTier.BUDGET: {
                'housing_searches_per_month': 5,
                'scenarios_saved': 3,
                'career_integration': False,
                'export_functionality': False,
                'advanced_analytics': False
            },
            FeatureTier.MID_TIER: {
                'housing_searches_per_month': -1,  # unlimited
                'scenarios_saved': 10,
                'career_integration': True,
                'export_functionality': False,
                'advanced_analytics': True
            },
            FeatureTier.PROFESSIONAL: {
                'housing_searches_per_month': -1,  # unlimited
                'scenarios_saved': -1,  # unlimited
                'career_integration': True,
                'export_functionality': True,
                'advanced_analytics': True
            }
        }

    def get_user_tier(self, user_id: int) -> FeatureTier:
        """
        Get user's current subscription tier
        In a real implementation, this would query the billing system
        """
        # TODO: Integrate with actual billing system
        # For now, return a default tier for testing
        return FeatureTier.BUDGET

    def has_feature_access(self, user_id: int, feature: FeatureFlag) -> bool:
        """
        Check if user has access to a specific feature
        
        Args:
            user_id: User ID to check
            feature: Feature flag to check
            
        Returns:
            True if user has access, False otherwise
        """
        try:
            user_tier = self.get_user_tier(user_id)
            tier_config = self.feature_tiers.get(user_tier, {})
            return feature in tier_config.get('features', [])
        except Exception as e:
            logger.error(f"Error checking feature access for user {user_id}, feature {feature}: {e}")
            return False

    def get_available_addons(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get available add-ons for user's current tier
        
        Args:
            user_id: User ID to check
            
        Returns:
            List of available add-ons with pricing and details
        """
        try:
            user_tier = self.get_user_tier(user_id)
            available_addons = []
            
            for feature, config in self.feature_descriptions.items():
                if (config['addon_price'] is not None and 
                    user_tier in config['available_tiers'] and
                    not self.has_feature_access(user_id, feature)):
                    
                    available_addons.append({
                        'feature': feature.value,
                        'name': config['name'],
                        'description': config['description'],
                        'addon_price': config['addon_price'],
                        'current_tier_price': self.feature_tiers[user_tier]['price'],
                        'total_price': self.feature_tiers[user_tier]['price'] + config['addon_price']
                    })
            
            return available_addons
        except Exception as e:
            logger.error(f"Error getting available addons for user {user_id}: {e}")
            return []

    def get_tier_upgrade_options(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get available tier upgrade options for user
        
        Args:
            user_id: User ID to check
            
        Returns:
            List of available tier upgrades with pricing and features
        """
        try:
            current_tier = self.get_user_tier(user_id)
            upgrade_options = []
            
            for tier, config in self.feature_tiers.items():
                if tier != current_tier and config['price'] > self.feature_tiers[current_tier]['price']:
                    upgrade_options.append({
                        'tier': tier.value,
                        'price': config['price'],
                        'description': config['description'],
                        'features': [f.value for f in config['features']],
                        'price_difference': config['price'] - self.feature_tiers[current_tier]['price']
                    })
            
            return upgrade_options
        except Exception as e:
            logger.error(f"Error getting tier upgrade options for user {user_id}: {e}")
            return []

    def get_feature_access_info(self, user_id: int, feature: FeatureFlag) -> Dict[str, Any]:
        """
        Get detailed access information for a specific feature
        
        Args:
            user_id: User ID to check
            feature: Feature flag to check
            
        Returns:
            Dictionary with access information and upgrade options
        """
        try:
            has_access = self.has_feature_access(user_id, feature)
            current_tier = self.get_user_tier(user_id)
            
            result = {
                'has_access': has_access,
                'current_tier': current_tier.value,
                'feature': feature.value,
                'feature_name': self.feature_descriptions[feature]['name'],
                'feature_description': self.feature_descriptions[feature]['description']
            }
            
            if not has_access:
                # Check if it's available as an add-on
                if self.feature_descriptions[feature]['addon_price'] is not None:
                    result['available_as_addon'] = True
                    result['addon_price'] = self.feature_descriptions[feature]['addon_price']
                    result['current_tier_price'] = self.feature_tiers[current_tier]['price']
                    result['total_price'] = self.feature_tiers[current_tier]['price'] + self.feature_descriptions[feature]['addon_price']
                else:
                    # Check if it's available in higher tiers
                    available_tiers = self.feature_descriptions[feature]['available_tiers']
                    higher_tiers = [t for t in available_tiers if self.feature_tiers[t]['price'] > self.feature_tiers[current_tier]['price']]
                    
                    if higher_tiers:
                        result['available_in_higher_tiers'] = True
                        result['upgrade_options'] = [
                            {
                                'tier': tier.value,
                                'price': self.feature_tiers[tier]['price'],
                                'description': self.feature_tiers[tier]['description']
                            }
                            for tier in higher_tiers
                        ]
                    else:
                        result['not_available'] = True
            
            return result
        except Exception as e:
            logger.error(f"Error getting feature access info for user {user_id}, feature {feature}: {e}")
            return {
                'has_access': False,
                'error': str(e)
            }

    def get_all_tiers_info(self) -> Dict[str, Any]:
        """
        Get information about all available tiers
        
        Returns:
            Dictionary with all tier information
        """
        try:
            tiers_info = {}
            for tier, config in self.feature_tiers.items():
                tiers_info[tier.value] = {
                    'price': config['price'],
                    'description': config['description'],
                    'features': [f.value for f in config['features']],
                    'feature_names': [self.feature_descriptions[f]['name'] for f in config['features']]
                }
            
            return {
                'tiers': tiers_info,
                'feature_descriptions': {
                    feature.value: {
                        'name': config['name'],
                        'description': config['description'],
                        'addon_price': config['addon_price']
                    }
                    for feature, config in self.feature_descriptions.items()
                }
            }
        except Exception as e:
            logger.error(f"Error getting all tiers info: {e}")
            return {}

    def simulate_addon_purchase(self, user_id: int, feature: FeatureFlag) -> Dict[str, Any]:
        """
        Simulate purchasing an add-on (for testing purposes)
        
        Args:
            user_id: User ID
            feature: Feature to add
            
        Returns:
            Dictionary with purchase simulation results
        """
        try:
            if not self.feature_descriptions[feature]['addon_price']:
                return {
                    'success': False,
                    'error': 'Feature is not available as an add-on'
                }
            
            current_tier = self.get_user_tier(user_id)
            addon_price = self.feature_descriptions[feature]['addon_price']
            
            # In a real implementation, this would:
            # 1. Process payment
            # 2. Update user's subscription
            # 3. Send confirmation email
            # 4. Update billing records
            
            return {
                'success': True,
                'user_id': user_id,
                'feature': feature.value,
                'addon_price': addon_price,
                'new_tier': f"{current_tier.value}_with_{feature.value}",
                'total_monthly_cost': self.feature_tiers[current_tier]['price'] + addon_price,
                'message': f'Successfully added {self.feature_descriptions[feature]["name"]} add-on'
            }
        except Exception as e:
            logger.error(f"Error simulating addon purchase for user {user_id}, feature {feature}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_optimal_location_features(self, user_id: int) -> Dict[str, Any]:
        """
        Get optimal location feature configuration for user's tier
        
        Args:
            user_id: User ID to check
            
        Returns:
            Dictionary with optimal location feature configuration
        """
        try:
            user_tier = self.get_user_tier(user_id)
            return self.OPTIMAL_LOCATION_FEATURES.get(user_tier, {})
        except Exception as e:
            logger.error(f"Error getting optimal location features for user {user_id}: {e}")
            return {}

    def check_housing_search_limit(self, user_id: int, current_searches_this_month: int) -> bool:
        """
        Check if user can perform more housing searches this month
        
        Args:
            user_id: User ID to check
            current_searches_this_month: Number of searches already performed this month
            
        Returns:
            True if user can perform more searches, False otherwise
        """
        try:
            features = self.get_optimal_location_features(user_id)
            limit = features.get('housing_searches_per_month', 0)
            
            # -1 means unlimited
            if limit == -1:
                return True
                
            return current_searches_this_month < limit
        except Exception as e:
            logger.error(f"Error checking housing search limit for user {user_id}: {e}")
            return False

    def check_scenario_save_limit(self, user_id: int, current_saved_scenarios: int) -> bool:
        """
        Check if user can save more housing scenarios
        
        Args:
            user_id: User ID to check
            current_saved_scenarios: Number of scenarios already saved
            
        Returns:
            True if user can save more scenarios, False otherwise
        """
        try:
            features = self.get_optimal_location_features(user_id)
            limit = features.get('scenarios_saved', 0)
            
            # -1 means unlimited
            if limit == -1:
                return True
                
            return current_saved_scenarios < limit
        except Exception as e:
            logger.error(f"Error checking scenario save limit for user {user_id}: {e}")
            return False

    def has_optimal_location_feature(self, user_id: int, feature_name: str) -> bool:
        """
        Check if user has access to a specific optimal location feature
        
        Args:
            user_id: User ID to check
            feature_name: Name of the feature to check (e.g., 'career_integration', 'export_functionality')
            
        Returns:
            True if user has access to the feature, False otherwise
        """
        try:
            features = self.get_optimal_location_features(user_id)
            return features.get(feature_name, False)
        except Exception as e:
            logger.error(f"Error checking optimal location feature {feature_name} for user {user_id}: {e}")
            return False

# Global instance
feature_flag_service = FeatureFlagService()
