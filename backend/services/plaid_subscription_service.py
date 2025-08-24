"""
Plaid Subscription Service for MINGUS

This module provides subscription tier integration for Plaid features:
- Professional tier: Full Plaid access (unlimited accounts)
- Mid-tier: Limited Plaid access (2 accounts max)
- Budget tier: No Plaid access (manual entry only)
- Upgrade prompts when tier limits reached
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from backend.models.plaid_models import PlaidConnection, PlaidAccount
from backend.models.subscription_models import MINGUSSubscriptionTier
from backend.services.enhanced_feature_access_service import (
    EnhancedFeatureAccessService,
    FeatureTier,
    FeatureCategory,
    AccessResult
)

logger = logging.getLogger(__name__)

class PlaidFeature(Enum):
    """Plaid features that can be gated by subscription tier"""
    BANK_ACCOUNT_LINKING = "bank_account_linking"
    ACCOUNT_BALANCE_RETRIEVAL = "account_balance_retrieval"
    TRANSACTION_HISTORY = "transaction_history"
    IDENTITY_VERIFICATION = "identity_verification"
    REAL_TIME_UPDATES = "real_time_updates"
    MULTIPLE_ACCOUNTS = "multiple_accounts"
    ADVANCED_ANALYTICS = "advanced_analytics"

@dataclass
class PlaidTierLimits:
    """Plaid feature limits by subscription tier"""
    tier: str
    max_accounts: int
    max_connections: int
    transaction_history_months: int
    real_time_updates: bool
    advanced_analytics: bool
    manual_entry_only: bool
    upgrade_prompt_threshold: float = 0.8  # Show upgrade at 80% usage

@dataclass
class PlaidUsageMetrics:
    """Current Plaid usage metrics for a user"""
    total_connections: int
    total_accounts: int
    active_connections: int
    active_accounts: int
    last_transaction_sync: Optional[datetime]
    total_transactions: int
    usage_percentage: float

@dataclass
class PlaidUpgradePrompt:
    """Upgrade prompt information for Plaid features"""
    feature: PlaidFeature
    current_usage: int
    current_limit: int
    upgrade_tier: str
    upgrade_benefits: List[str]
    upgrade_price: Optional[float]
    trial_available: bool
    trial_duration_days: int

class PlaidSubscriptionService:
    """Service for managing Plaid features based on subscription tiers"""
    
    def __init__(self, db_session: Session, feature_access_service: EnhancedFeatureAccessService):
        self.db = db_session
        self.feature_service = feature_access_service
        self.tier_limits = self._initialize_tier_limits()
        
    def _initialize_tier_limits(self) -> Dict[str, PlaidTierLimits]:
        """Initialize tier limits for Plaid features"""
        return {
            'budget': PlaidTierLimits(
                tier='budget',
                max_accounts=0,
                max_connections=0,
                transaction_history_months=0,
                real_time_updates=False,
                advanced_analytics=False,
                manual_entry_only=True
            ),
            'mid_tier': PlaidTierLimits(
                tier='mid_tier',
                max_accounts=2,
                max_connections=1,
                transaction_history_months=12,
                real_time_updates=True,
                advanced_analytics=False,
                manual_entry_only=False
            ),
            'professional': PlaidTierLimits(
                tier='professional',
                max_accounts=-1,  # Unlimited
                max_connections=-1,  # Unlimited
                transaction_history_months=24,
                real_time_updates=True,
                advanced_analytics=True,
                manual_entry_only=False
            )
        }
    
    def get_user_tier(self, user_id: str) -> str:
        """Get user's current subscription tier"""
        try:
            # Get user's subscription tier from the feature access service
            user_tier = self.feature_service.get_user_subscription_tier(user_id)
            
            # Map feature access tiers to Plaid tiers
            tier_mapping = {
                FeatureTier.BUDGET: 'budget',
                FeatureTier.MID_TIER: 'mid_tier',
                FeatureTier.PROFESSIONAL: 'professional'
            }
            
            return tier_mapping.get(user_tier, 'budget')
            
        except Exception as e:
            logger.error(f"Error getting user tier for {user_id}: {e}")
            return 'budget'  # Default to budget tier
    
    def get_tier_limits(self, user_id: str) -> PlaidTierLimits:
        """Get Plaid limits for user's subscription tier"""
        tier = self.get_user_tier(user_id)
        return self.tier_limits.get(tier, self.tier_limits['budget'])
    
    def check_plaid_feature_access(self, user_id: str, feature: PlaidFeature) -> AccessResult:
        """Check if user has access to a specific Plaid feature"""
        try:
            # Check feature access through the enhanced feature access service
            feature_id = f"plaid_{feature.value}"
            access_result = self.feature_service.check_feature_access(
                user_id=user_id,
                feature_id=feature_id,
                context={'feature': feature.value}
            )
            
            return access_result
            
        except Exception as e:
            logger.error(f"Error checking Plaid feature access: {e}")
            return AccessResult(
                has_access=False,
                reason="service_error",
                current_tier="budget",
                required_tier="professional",
                upgrade_required=True,
                educational_content="Plaid integration is temporarily unavailable. Please try again later."
            )
    
    def get_user_usage_metrics(self, user_id: str) -> PlaidUsageMetrics:
        """Get current Plaid usage metrics for a user"""
        try:
            # Get connection count
            total_connections = self.db.query(PlaidConnection).filter(
                PlaidConnection.user_id == user_id
            ).count()
            
            active_connections = self.db.query(PlaidConnection).filter(
                PlaidConnection.user_id == user_id,
                PlaidConnection.is_active == True
            ).count()
            
            # Get account count
            total_accounts = self.db.query(PlaidAccount).filter(
                PlaidAccount.user_id == user_id
            ).count()
            
            active_accounts = self.db.query(PlaidAccount).filter(
                PlaidAccount.user_id == user_id,
                PlaidAccount.is_active == True
            ).count()
            
            # Get last transaction sync
            last_sync = self.db.query(PlaidConnection).filter(
                PlaidConnection.user_id == user_id,
                PlaidConnection.last_sync_at.isnot(None)
            ).order_by(desc(PlaidConnection.last_sync_at)).first()
            
            last_transaction_sync = last_sync.last_sync_at if last_sync else None
            
            # Get total transactions (last 30 days for performance)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            total_transactions = self.db.query(PlaidAccount).join(
                PlaidConnection
            ).filter(
                PlaidConnection.user_id == user_id,
                PlaidAccount.created_at >= thirty_days_ago
            ).count()
            
            # Calculate usage percentage
            tier_limits = self.get_tier_limits(user_id)
            if tier_limits.max_accounts > 0:
                usage_percentage = min(active_accounts / tier_limits.max_accounts, 1.0)
            else:
                usage_percentage = 0.0
            
            return PlaidUsageMetrics(
                total_connections=total_connections,
                total_accounts=total_accounts,
                active_connections=active_connections,
                active_accounts=active_accounts,
                last_transaction_sync=last_transaction_sync,
                total_transactions=total_transactions,
                usage_percentage=usage_percentage
            )
            
        except Exception as e:
            logger.error(f"Error getting usage metrics for user {user_id}: {e}")
            return PlaidUsageMetrics(
                total_connections=0,
                total_accounts=0,
                active_connections=0,
                active_accounts=0,
                last_transaction_sync=None,
                total_transactions=0,
                usage_percentage=0.0
            )
    
    def can_add_connection(self, user_id: str) -> Tuple[bool, Optional[str], Optional[PlaidUpgradePrompt]]:
        """Check if user can add a new Plaid connection"""
        try:
            tier_limits = self.get_tier_limits(user_id)
            usage_metrics = self.get_user_usage_metrics(user_id)
            
            # Budget tier: No Plaid access
            if tier_limits.manual_entry_only:
                upgrade_prompt = self._create_upgrade_prompt(
                    PlaidFeature.BANK_ACCOUNT_LINKING,
                    usage_metrics.active_connections,
                    0,
                    'mid_tier'
                )
                return False, "Plaid integration requires Mid-Tier or higher subscription", upgrade_prompt
            
            # Check connection limit
            if tier_limits.max_connections > 0 and usage_metrics.active_connections >= tier_limits.max_connections:
                upgrade_prompt = self._create_upgrade_prompt(
                    PlaidFeature.BANK_ACCOUNT_LINKING,
                    usage_metrics.active_connections,
                    tier_limits.max_connections,
                    'professional'
                )
                return False, f"Connection limit reached ({tier_limits.max_connections} max)", upgrade_prompt
            
            # Check if approaching limit
            if tier_limits.max_connections > 0:
                usage_percentage = usage_metrics.active_connections / tier_limits.max_connections
                if usage_percentage >= tier_limits.upgrade_prompt_threshold:
                    upgrade_prompt = self._create_upgrade_prompt(
                        PlaidFeature.BANK_ACCOUNT_LINKING,
                        usage_metrics.active_connections,
                        tier_limits.max_connections,
                        'professional'
                    )
                    return True, None, upgrade_prompt
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking connection limit for user {user_id}: {e}")
            return False, "Service error occurred", None
    
    def can_add_account(self, user_id: str) -> Tuple[bool, Optional[str], Optional[PlaidUpgradePrompt]]:
        """Check if user can add a new bank account"""
        try:
            tier_limits = self.get_tier_limits(user_id)
            usage_metrics = self.get_user_usage_metrics(user_id)
            
            # Budget tier: No Plaid access
            if tier_limits.manual_entry_only:
                upgrade_prompt = self._create_upgrade_prompt(
                    PlaidFeature.MULTIPLE_ACCOUNTS,
                    usage_metrics.active_accounts,
                    0,
                    'mid_tier'
                )
                return False, "Multiple bank accounts require Mid-Tier or higher subscription", upgrade_prompt
            
            # Check account limit
            if tier_limits.max_accounts > 0 and usage_metrics.active_accounts >= tier_limits.max_accounts:
                upgrade_prompt = self._create_upgrade_prompt(
                    PlaidFeature.MULTIPLE_ACCOUNTS,
                    usage_metrics.active_accounts,
                    tier_limits.max_accounts,
                    'professional'
                )
                return False, f"Account limit reached ({tier_limits.max_accounts} max)", upgrade_prompt
            
            # Check if approaching limit
            if tier_limits.max_accounts > 0:
                usage_percentage = usage_metrics.active_accounts / tier_limits.max_accounts
                if usage_percentage >= tier_limits.upgrade_prompt_threshold:
                    upgrade_prompt = self._create_upgrade_prompt(
                        PlaidFeature.MULTIPLE_ACCOUNTS,
                        usage_metrics.active_accounts,
                        tier_limits.max_accounts,
                        'professional'
                    )
                    return True, None, upgrade_prompt
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking account limit for user {user_id}: {e}")
            return False, "Service error occurred", None
    
    def can_access_transaction_history(self, user_id: str, months_requested: int = 24) -> Tuple[bool, Optional[str], Optional[PlaidUpgradePrompt]]:
        """Check if user can access transaction history for specified months"""
        try:
            tier_limits = self.get_tier_limits(user_id)
            
            # Budget tier: No Plaid access
            if tier_limits.manual_entry_only:
                upgrade_prompt = self._create_upgrade_prompt(
                    PlaidFeature.TRANSACTION_HISTORY,
                    0,
                    0,
                    'mid_tier'
                )
                return False, "Transaction history requires Mid-Tier or higher subscription", upgrade_prompt
            
            # Check transaction history limit
            if months_requested > tier_limits.transaction_history_months:
                upgrade_prompt = self._create_upgrade_prompt(
                    PlaidFeature.TRANSACTION_HISTORY,
                    tier_limits.transaction_history_months,
                    months_requested,
                    'professional'
                )
                return False, f"Transaction history limited to {tier_limits.transaction_history_months} months", upgrade_prompt
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking transaction history access for user {user_id}: {e}")
            return False, "Service error occurred", None
    
    def can_access_advanced_analytics(self, user_id: str) -> Tuple[bool, Optional[str], Optional[PlaidUpgradePrompt]]:
        """Check if user can access advanced analytics"""
        try:
            tier_limits = self.get_tier_limits(user_id)
            
            if not tier_limits.advanced_analytics:
                upgrade_prompt = self._create_upgrade_prompt(
                    PlaidFeature.ADVANCED_ANALYTICS,
                    0,
                    0,
                    'professional'
                )
                return False, "Advanced analytics require Professional subscription", upgrade_prompt
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking advanced analytics access for user {user_id}: {e}")
            return False, "Service error occurred", None
    
    def _create_upgrade_prompt(self, feature: PlaidFeature, current_usage: int, 
                              current_limit: int, upgrade_tier: str) -> PlaidUpgradePrompt:
        """Create an upgrade prompt for a specific feature"""
        
        upgrade_benefits = {
            'mid_tier': [
                "Connect up to 2 bank accounts",
                "12 months of transaction history",
                "Real-time balance updates",
                "Basic financial insights"
            ],
            'professional': [
                "Unlimited bank accounts",
                "24 months of transaction history",
                "Advanced analytics and insights",
                "Priority support",
                "Custom financial planning tools"
            ]
        }
        
        upgrade_prices = {
            'mid_tier': 19.99,
            'professional': 49.99
        }
        
        return PlaidUpgradePrompt(
            feature=feature,
            current_usage=current_usage,
            current_limit=current_limit,
            upgrade_tier=upgrade_tier,
            upgrade_benefits=upgrade_benefits.get(upgrade_tier, []),
            upgrade_price=upgrade_prices.get(upgrade_tier),
            trial_available=True,
            trial_duration_days=7
        )
    
    def get_upgrade_recommendations(self, user_id: str) -> List[PlaidUpgradePrompt]:
        """Get upgrade recommendations based on user's current usage"""
        try:
            recommendations = []
            usage_metrics = self.get_user_usage_metrics(user_id)
            tier_limits = self.get_tier_limits(user_id)
            
            # Check if user is on budget tier and has no Plaid access
            if tier_limits.manual_entry_only:
                recommendations.append(
                    self._create_upgrade_prompt(
                        PlaidFeature.BANK_ACCOUNT_LINKING,
                        0,
                        0,
                        'mid_tier'
                    )
                )
                return recommendations
            
            # Check if approaching account limit
            if tier_limits.max_accounts > 0:
                usage_percentage = usage_metrics.active_accounts / tier_limits.max_accounts
                if usage_percentage >= 0.7:  # 70% usage threshold
                    recommendations.append(
                        self._create_upgrade_prompt(
                            PlaidFeature.MULTIPLE_ACCOUNTS,
                            usage_metrics.active_accounts,
                            tier_limits.max_accounts,
                            'professional'
                        )
                    )
            
            # Check if approaching connection limit
            if tier_limits.max_connections > 0:
                usage_percentage = usage_metrics.active_connections / tier_limits.max_connections
                if usage_percentage >= 0.7:  # 70% usage threshold
                    recommendations.append(
                        self._create_upgrade_prompt(
                            PlaidFeature.BANK_ACCOUNT_LINKING,
                            usage_metrics.active_connections,
                            tier_limits.max_connections,
                            'professional'
                        )
                    )
            
            # Recommend advanced analytics if not available
            if not tier_limits.advanced_analytics:
                recommendations.append(
                    self._create_upgrade_prompt(
                        PlaidFeature.ADVANCED_ANALYTICS,
                        0,
                        0,
                        'professional'
                    )
                )
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting upgrade recommendations for user {user_id}: {e}")
            return []
    
    def enforce_tier_limits(self, user_id: str) -> Dict[str, Any]:
        """Enforce tier limits and return any violations"""
        try:
            violations = {}
            tier_limits = self.get_tier_limits(user_id)
            usage_metrics = self.get_user_usage_metrics(user_id)
            
            # Check account limit violations
            if tier_limits.max_accounts > 0 and usage_metrics.active_accounts > tier_limits.max_accounts:
                violations['accounts'] = {
                    'current': usage_metrics.active_accounts,
                    'limit': tier_limits.max_accounts,
                    'message': f"Account limit exceeded: {usage_metrics.active_accounts}/{tier_limits.max_accounts}"
                }
            
            # Check connection limit violations
            if tier_limits.max_connections > 0 and usage_metrics.active_connections > tier_limits.max_connections:
                violations['connections'] = {
                    'current': usage_metrics.active_connections,
                    'limit': tier_limits.max_connections,
                    'message': f"Connection limit exceeded: {usage_metrics.active_connections}/{tier_limits.max_connections}"
                }
            
            return violations
            
        except Exception as e:
            logger.error(f"Error enforcing tier limits for user {user_id}: {e}")
            return {}
    
    def get_tier_comparison(self) -> Dict[str, Dict[str, Any]]:
        """Get comparison of Plaid features across tiers"""
        return {
            'budget': {
                'name': 'Budget',
                'price': 0,
                'plaid_features': {
                    'bank_account_linking': False,
                    'max_accounts': 0,
                    'max_connections': 0,
                    'transaction_history_months': 0,
                    'real_time_updates': False,
                    'advanced_analytics': False,
                    'manual_entry_only': True
                },
                'description': 'Manual financial entry only'
            },
            'mid_tier': {
                'name': 'Mid-Tier',
                'price': 19.99,
                'plaid_features': {
                    'bank_account_linking': True,
                    'max_accounts': 2,
                    'max_connections': 1,
                    'transaction_history_months': 12,
                    'real_time_updates': True,
                    'advanced_analytics': False,
                    'manual_entry_only': False
                },
                'description': 'Basic Plaid integration with 2 accounts'
            },
            'professional': {
                'name': 'Professional',
                'price': 49.99,
                'plaid_features': {
                    'bank_account_linking': True,
                    'max_accounts': -1,  # Unlimited
                    'max_connections': -1,  # Unlimited
                    'transaction_history_months': 24,
                    'real_time_updates': True,
                    'advanced_analytics': True,
                    'manual_entry_only': False
                },
                'description': 'Full Plaid integration with unlimited accounts'
            }
        } 