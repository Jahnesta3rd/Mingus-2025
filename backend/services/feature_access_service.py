"""
Feature Access Service for MINGUS
=================================

Comprehensive feature access management system providing:
- Immediate feature access updates for subscription changes
- Feature access caching and optimization
- Access level management
- Feature permission validation
- Real-time access control
- Performance monitoring and optimization

Author: MINGUS Development Team
Date: January 2025
"""

import logging
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uuid

from ..config.base import Config
from ..models.subscription import Customer, Subscription, User
from ..models.feature_access import FeatureAccessUpdate, FeatureAccessLevel

logger = logging.getLogger(__name__)


class FeatureType(Enum):
    """Feature types"""
    CORE = "core"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ANALYTICS = "analytics"
    API = "api"
    INTEGRATION = "integration"
    SUPPORT = "support"
    CUSTOM = "custom"


class AccessAction(Enum):
    """Access actions"""
    GRANT = "grant"
    REVOKE = "revoke"
    UPDATE = "update"
    RESTRICT = "restrict"


@dataclass
class FeatureAccess:
    """Feature access data structure"""
    feature_id: str
    feature_name: str
    feature_type: FeatureType
    access_level: FeatureAccessLevel
    granted_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


@dataclass
class AccessUpdate:
    """Access update data structure"""
    update_id: str
    customer_id: str
    user_id: Optional[str]
    action: AccessAction
    features_affected: List[str]
    access_level: FeatureAccessLevel
    reason: str
    timestamp: datetime
    metadata: Dict[str, Any] = None


class FeatureAccessService:
    """Comprehensive feature access management service"""
    
    def __init__(self, db_session: Session, config: Config):
        self.db = db_session
        self.config = config
        
        # Feature access configuration
        self.feature_config = {
            'tiers': {
                'basic': {
                    'features': ['core_features', 'basic_analytics', 'email_support'],
                    'access_level': FeatureAccessLevel.BASIC,
                    'limits': {
                        'api_calls_per_day': 1000,
                        'storage_gb': 5,
                        'users': 1
                    }
                },
                'premium': {
                    'features': ['core_features', 'premium_analytics', 'advanced_api', 'priority_support'],
                    'access_level': FeatureAccessLevel.PREMIUM,
                    'limits': {
                        'api_calls_per_day': 10000,
                        'storage_gb': 50,
                        'users': 5
                    }
                },
                'enterprise': {
                    'features': ['core_features', 'enterprise_analytics', 'unlimited_api', 'dedicated_support', 'custom_integrations'],
                    'access_level': FeatureAccessLevel.ENTERPRISE,
                    'limits': {
                        'api_calls_per_day': 100000,
                        'storage_gb': 500,
                        'users': 50
                    }
                },
                'unlimited': {
                    'features': ['all_features'],
                    'access_level': FeatureAccessLevel.UNLIMITED,
                    'limits': {
                        'api_calls_per_day': -1,  # Unlimited
                        'storage_gb': -1,  # Unlimited
                        'users': -1  # Unlimited
                    }
                }
            },
            'trial_features': {
                'features': ['core_features', 'basic_analytics'],
                'access_level': FeatureAccessLevel.BASIC,
                'limits': {
                    'api_calls_per_day': 500,
                    'storage_gb': 2,
                    'users': 1
                }
            },
            'grace_period_features': {
                'features': ['core_features'],
                'access_level': FeatureAccessLevel.BASIC,
                'limits': {
                    'api_calls_per_day': 100,
                    'storage_gb': 1,
                    'users': 1
                }
            }
        }
        
        # Cache configuration
        self.cache_config = {
            'enabled': True,
            'ttl_seconds': 300,  # 5 minutes
            'max_size': 10000
        }
        
        # Performance metrics
        self.performance_metrics = {
            'access_updates': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_update_time_ms': 0.0
        }
    
    def update_feature_access_immediately(
        self,
        customer_id: str,
        subscription_tier: str,
        subscription_status: str,
        subscription_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update feature access immediately for subscription changes"""
        try:
            start_time = time.time()
            
            # Get customer and user information
            customer = self._get_customer(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': f"Customer not found: {customer_id}",
                    'changes': [],
                    'features_granted': [],
                    'features_removed': [],
                    'access_level': None
                }
            
            # Determine current access level
            current_access = self._get_current_feature_access(customer_id)
            
            # Determine new access level based on subscription
            new_access_level = self._determine_access_level(subscription_tier, subscription_status)
            
            # Get features for new access level
            new_features = self._get_features_for_tier(subscription_tier, subscription_status)
            
            # Calculate changes
            features_granted = [f for f in new_features if f not in current_access.get('features', [])]
            features_removed = [f for f in current_access.get('features', []) if f not in new_features]
            
            # Update feature access in database
            update_result = self._update_feature_access_database(
                customer_id=customer_id,
                user_id=str(customer.user_id) if customer.user_id else None,
                new_features=new_features,
                new_access_level=new_access_level,
                features_granted=features_granted,
                features_removed=features_removed,
                subscription_tier=subscription_tier,
                subscription_status=subscription_status
            )
            
            # Update cache
            if self.cache_config['enabled']:
                self._update_feature_cache(customer_id, new_features, new_access_level)
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, True)
            
            return {
                'success': True,
                'changes': update_result['changes'],
                'features_granted': features_granted,
                'features_removed': features_removed,
                'access_level': new_access_level.value,
                'processing_time_ms': processing_time,
                'cache_updated': self.cache_config['enabled']
            }
            
        except Exception as e:
            logger.error(f"Error updating feature access immediately: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'features_granted': [],
                'features_removed': [],
                'access_level': None
            }
    
    def revoke_feature_access_immediately(
        self,
        customer_id: str,
        subscription_tier: str,
        cancellation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Revoke feature access immediately for subscription cancellation"""
        try:
            start_time = time.time()
            
            # Get customer information
            customer = self._get_customer(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': f"Customer not found: {customer_id}",
                    'changes': [],
                    'features_revoked': [],
                    'access_level': None
                }
            
            # Get current features
            current_access = self._get_current_feature_access(customer_id)
            current_features = current_access.get('features', [])
            
            # Determine grace period access level
            grace_access_level = self._determine_grace_period_access_level()
            grace_features = self._get_grace_period_features()
            
            # Calculate revoked features
            features_revoked = [f for f in current_features if f not in grace_features]
            
            # Update feature access in database
            update_result = self._update_feature_access_database(
                customer_id=customer_id,
                user_id=str(customer.user_id) if customer.user_id else None,
                new_features=grace_features,
                new_access_level=grace_access_level,
                features_granted=[],
                features_removed=features_revoked,
                subscription_tier=subscription_tier,
                subscription_status='cancelled',
                cancellation_data=cancellation_data
            )
            
            # Update cache
            if self.cache_config['enabled']:
                self._update_feature_cache(customer_id, grace_features, grace_access_level)
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, True)
            
            return {
                'success': True,
                'changes': update_result['changes'],
                'features_revoked': features_revoked,
                'access_level': grace_access_level.value,
                'processing_time_ms': processing_time,
                'cache_updated': self.cache_config['enabled']
            }
            
        except Exception as e:
            logger.error(f"Error revoking feature access immediately: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'features_revoked': [],
                'access_level': None
            }
    
    def update_feature_access_for_trial_ending(
        self,
        customer_id: str,
        subscription_tier: str,
        trial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update feature access for trial ending"""
        try:
            start_time = time.time()
            
            # Get customer information
            customer = self._get_customer(customer_id)
            if not customer:
                return {
                    'success': False,
                    'error': f"Customer not found: {customer_id}",
                    'changes': [],
                    'features_restricted': [],
                    'access_level': None
                }
            
            # Get current features
            current_access = self._get_current_feature_access(customer_id)
            current_features = current_access.get('features', [])
            
            # Determine trial ending access level
            trial_ending_access_level = self._determine_trial_ending_access_level()
            trial_ending_features = self._get_trial_ending_features()
            
            # Calculate restricted features
            features_restricted = [f for f in current_features if f not in trial_ending_features]
            
            # Update feature access in database
            update_result = self._update_feature_access_database(
                customer_id=customer_id,
                user_id=str(customer.user_id) if customer.user_id else None,
                new_features=trial_ending_features,
                new_access_level=trial_ending_access_level,
                features_granted=[],
                features_removed=features_restricted,
                subscription_tier=subscription_tier,
                subscription_status='trial_ending',
                trial_data=trial_data
            )
            
            # Update cache
            if self.cache_config['enabled']:
                self._update_feature_cache(customer_id, trial_ending_features, trial_ending_access_level)
            
            # Record performance metric
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(processing_time, True)
            
            return {
                'success': True,
                'changes': update_result['changes'],
                'features_restricted': features_restricted,
                'access_level': trial_ending_access_level.value,
                'processing_time_ms': processing_time,
                'cache_updated': self.cache_config['enabled']
            }
            
        except Exception as e:
            logger.error(f"Error updating feature access for trial ending: {e}")
            return {
                'success': False,
                'error': str(e),
                'changes': [],
                'features_restricted': [],
                'access_level': None
            }
    
    def get_user_feature_access(self, user_id: str) -> Dict[str, Any]:
        """Get user's current feature access"""
        try:
            # Try cache first
            if self.cache_config['enabled']:
                cached_access = self._get_cached_feature_access(user_id)
                if cached_access:
                    self.performance_metrics['cache_hits'] += 1
                    return cached_access
            
            self.performance_metrics['cache_misses'] += 1
            
            # Get from database
            user = self._get_user(user_id)
            if not user:
                return {
                    'success': False,
                    'error': f"User not found: {user_id}",
                    'features': [],
                    'access_level': FeatureAccessLevel.NONE.value,
                    'limits': {}
                }
            
            # Get customer for user
            customer = self._get_customer_by_user_id(user_id)
            if not customer:
                return {
                    'success': True,
                    'features': [],
                    'access_level': FeatureAccessLevel.NONE.value,
                    'limits': {}
                }
            
            # Get feature access
            access = self._get_current_feature_access(str(customer.id))
            
            # Cache the result
            if self.cache_config['enabled']:
                self._set_cached_feature_access(user_id, access)
            
            return access
            
        except Exception as e:
            logger.error(f"Error getting user feature access: {e}")
            return {
                'success': False,
                'error': str(e),
                'features': [],
                'access_level': FeatureAccessLevel.NONE.value,
                'limits': {}
            }
    
    def validate_feature_access(self, user_id: str, feature_name: str) -> bool:
        """Validate if user has access to a specific feature"""
        try:
            user_access = self.get_user_feature_access(user_id)
            
            if not user_access.get('success', True):
                return False
            
            features = user_access.get('features', [])
            return feature_name in features
            
        except Exception as e:
            logger.error(f"Error validating feature access: {e}")
            return False
    
    def get_feature_limits(self, user_id: str) -> Dict[str, Any]:
        """Get user's feature limits"""
        try:
            user_access = self.get_user_feature_access(user_id)
            
            if not user_access.get('success', True):
                return {}
            
            return user_access.get('limits', {})
            
        except Exception as e:
            logger.error(f"Error getting feature limits: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    # Private methods
    
    def _get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            return self.db.query(Customer).filter(Customer.id == customer_id).first()
        except Exception as e:
            logger.error(f"Error getting customer: {e}")
            return None
    
    def _get_customer_by_user_id(self, user_id: str) -> Optional[Customer]:
        """Get customer by user ID"""
        try:
            return self.db.query(Customer).filter(Customer.user_id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting customer by user ID: {e}")
            return None
    
    def _get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def _get_current_feature_access(self, customer_id: str) -> Dict[str, Any]:
        """Get current feature access for customer"""
        try:
            # Query the latest feature access update
            latest_update = self.db.query(FeatureAccessUpdate).filter(
                FeatureAccessUpdate.customer_id == customer_id
            ).order_by(FeatureAccessUpdate.effective_date.desc()).first()
            
            if latest_update:
                return {
                    'success': True,
                    'features': latest_update.features_added,
                    'access_level': latest_update.access_level.value,
                    'effective_date': latest_update.effective_date.isoformat(),
                    'reason': latest_update.reason
                }
            else:
                return {
                    'success': True,
                    'features': [],
                    'access_level': FeatureAccessLevel.NONE.value,
                    'effective_date': None,
                    'reason': 'No access record found'
                }
                
        except Exception as e:
            logger.error(f"Error getting current feature access: {e}")
            return {
                'success': False,
                'error': str(e),
                'features': [],
                'access_level': FeatureAccessLevel.NONE.value
            }
    
    def _determine_access_level(self, subscription_tier: str, subscription_status: str) -> FeatureAccessLevel:
        """Determine access level based on subscription"""
        try:
            if subscription_status in ['canceled', 'unpaid', 'past_due']:
                return FeatureAccessLevel.NONE
            
            tier_config = self.feature_config['tiers'].get(subscription_tier.lower())
            if tier_config:
                return tier_config['access_level']
            
            return FeatureAccessLevel.BASIC
            
        except Exception as e:
            logger.error(f"Error determining access level: {e}")
            return FeatureAccessLevel.NONE
    
    def _get_features_for_tier(self, subscription_tier: str, subscription_status: str) -> List[str]:
        """Get features for subscription tier"""
        try:
            if subscription_status in ['canceled', 'unpaid', 'past_due']:
                return []
            
            tier_config = self.feature_config['tiers'].get(subscription_tier.lower())
            if tier_config:
                return tier_config['features']
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting features for tier: {e}")
            return []
    
    def _determine_grace_period_access_level(self) -> FeatureAccessLevel:
        """Determine grace period access level"""
        return self.feature_config['grace_period_features']['access_level']
    
    def _get_grace_period_features(self) -> List[str]:
        """Get grace period features"""
        return self.feature_config['grace_period_features']['features']
    
    def _determine_trial_ending_access_level(self) -> FeatureAccessLevel:
        """Determine trial ending access level"""
        return self.feature_config['trial_features']['access_level']
    
    def _get_trial_ending_features(self) -> List[str]:
        """Get trial ending features"""
        return self.feature_config['trial_features']['features']
    
    def _update_feature_access_database(
        self,
        customer_id: str,
        user_id: Optional[str],
        new_features: List[str],
        new_access_level: FeatureAccessLevel,
        features_granted: List[str],
        features_removed: List[str],
        subscription_tier: str,
        subscription_status: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update feature access in database"""
        try:
            # Create feature access update record
            feature_update = FeatureAccessUpdate(
                id=uuid.uuid4(),
                customer_id=customer_id,
                subscription_id=kwargs.get('subscription_id'),
                old_tier=kwargs.get('old_tier'),
                new_tier=subscription_tier,
                features_added=new_features,
                features_removed=features_removed,
                access_level=new_access_level,
                effective_date=datetime.now(timezone.utc),
                reason=f"Subscription {subscription_status}: {subscription_tier}"
            )
            
            self.db.add(feature_update)
            self.db.commit()
            
            # Create access update record
            access_update = AccessUpdate(
                update_id=str(uuid.uuid4()),
                customer_id=customer_id,
                user_id=user_id,
                action=AccessAction.UPDATE,
                features_affected=new_features,
                access_level=new_access_level,
                reason=f"Immediate update for {subscription_status} subscription",
                timestamp=datetime.now(timezone.utc),
                metadata={
                    'subscription_tier': subscription_tier,
                    'subscription_status': subscription_status,
                    'features_granted': features_granted,
                    'features_removed': features_removed,
                    **kwargs
                }
            )
            
            return {
                'success': True,
                'changes': [
                    f"Updated feature access for customer {customer_id}",
                    f"Access level: {new_access_level.value}",
                    f"Features granted: {len(features_granted)}",
                    f"Features removed: {len(features_removed)}"
                ],
                'feature_update_id': str(feature_update.id),
                'access_update_id': access_update.update_id
            }
            
        except Exception as e:
            logger.error(f"Error updating feature access database: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'changes': []
            }
    
    def _get_cached_feature_access(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached feature access"""
        try:
            # This would use Redis or memory cache
            # For now, return None to indicate cache miss
            return None
        except Exception as e:
            logger.error(f"Error getting cached feature access: {e}")
            return None
    
    def _set_cached_feature_access(self, user_id: str, access_data: Dict[str, Any]):
        """Set cached feature access"""
        try:
            # This would use Redis or memory cache
            pass
        except Exception as e:
            logger.error(f"Error setting cached feature access: {e}")
    
    def _update_feature_cache(self, customer_id: str, features: List[str], access_level: FeatureAccessLevel):
        """Update feature cache"""
        try:
            # This would update Redis or memory cache
            pass
        except Exception as e:
            logger.error(f"Error updating feature cache: {e}")
    
    def _update_performance_metrics(self, processing_time: float, success: bool):
        """Update performance metrics"""
        try:
            self.performance_metrics['access_updates'] += 1
            
            # Update average processing time
            current_avg = self.performance_metrics['average_update_time_ms']
            total_updates = self.performance_metrics['access_updates']
            
            if total_updates > 0:
                new_avg = ((current_avg * (total_updates - 1)) + processing_time) / total_updates
                self.performance_metrics['average_update_time_ms'] = new_avg
            else:
                self.performance_metrics['average_update_time_ms'] = processing_time
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}") 