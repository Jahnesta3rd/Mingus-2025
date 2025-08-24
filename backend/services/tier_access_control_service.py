"""
Tier-Based Access Control Service for MINGUS

This service manages tier-based access controls for account linking:
- Professional: Unlimited accounts from any institution
- Mid-tier: Up to 2 accounts with full features
- Budget: Upgrade prompt with preview of banking features
- Usage tracking and limit enforcement
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError

from backend.models.bank_account_models import BankAccount, PlaidConnection
from backend.models.user_models import User, Subscription
from backend.services.analytics_service import AnalyticsService
from backend.services.notification_service import NotificationService
from backend.utils.validation import validate_user_tier

logger = logging.getLogger(__name__)

class TierLevel(Enum):
    """Subscription tier levels"""
    BUDGET = "budget"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"

class AccessResult(Enum):
    """Access control results"""
    ALLOWED = "allowed"
    DENIED = "denied"
    UPGRADE_REQUIRED = "upgrade_required"
    LIMIT_REACHED = "limit_reached"
    FEATURE_RESTRICTED = "feature_restricted"

@dataclass
class TierLimits:
    """Tier-specific limits and features"""
    max_accounts: int
    max_institutions: int
    max_connections: int
    sync_frequency: str
    transaction_history_months: int
    advanced_analytics: bool
    real_time_sync: bool
    priority_support: bool
    custom_alerts: bool
    data_export: bool
    api_access: bool

@dataclass
class UsageMetrics:
    """Current usage metrics for a user"""
    total_accounts: int
    total_institutions: int
    total_connections: int
    active_accounts: int
    last_sync_at: Optional[datetime]
    sync_frequency: str
    monthly_transactions: int
    storage_used_mb: float

@dataclass
class UpgradePrompt:
    """Upgrade prompt configuration"""
    title: str
    message: str
    benefits: List[str]
    current_tier: str
    recommended_tier: str
    upgrade_url: str
    preview_features: List[str]
    trial_available: bool
    trial_days: int

class TierAccessControlService:
    """Service for managing tier-based access controls"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db_session = db_session
        self.config = config
        self.analytics_service = AnalyticsService(db_session, config)
        self.notification_service = NotificationService(db_session, config)
        
        # Initialize tier limits
        self.tier_limits = self._initialize_tier_limits()
        
        # Usage tracking cache (in production, use Redis)
        self.usage_cache: Dict[str, UsageMetrics] = {}
        self.cache_ttl = timedelta(minutes=15)
    
    def _initialize_tier_limits(self) -> Dict[TierLevel, TierLimits]:
        """Initialize tier-specific limits and features"""
        return {
            TierLevel.BUDGET: TierLimits(
                max_accounts=0,  # No account linking allowed
                max_institutions=0,
                max_connections=0,
                sync_frequency='manual',
                transaction_history_months=0,
                advanced_analytics=False,
                real_time_sync=False,
                priority_support=False,
                custom_alerts=False,
                data_export=False,
                api_access=False
            ),
            TierLevel.MID_TIER: TierLimits(
                max_accounts=2,
                max_institutions=2,
                max_connections=2,
                sync_frequency='daily',
                transaction_history_months=12,
                advanced_analytics=True,
                real_time_sync=False,
                priority_support=False,
                custom_alerts=True,
                data_export=True,
                api_access=False
            ),
            TierLevel.PROFESSIONAL: TierLimits(
                max_accounts=-1,  # Unlimited
                max_institutions=-1,
                max_connections=-1,
                sync_frequency='real_time',
                transaction_history_months=24,
                advanced_analytics=True,
                real_time_sync=True,
                priority_support=True,
                custom_alerts=True,
                data_export=True,
                api_access=True
            )
        }
    
    def get_user_tier(self, user_id: str) -> TierLevel:
        """
        Get user's current subscription tier
        
        Args:
            user_id: User ID
            
        Returns:
            User's current tier level
        """
        try:
            # Get user's active subscription
            subscription = self.db_session.query(Subscription).filter(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == 'active',
                    Subscription.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not subscription:
                return TierLevel.BUDGET
            
            # Map subscription plan to tier
            tier_mapping = {
                'budget': TierLevel.BUDGET,
                'basic': TierLevel.BUDGET,
                'mid_tier': TierLevel.MID_TIER,
                'standard': TierLevel.MID_TIER,
                'professional': TierLevel.PROFESSIONAL,
                'premium': TierLevel.PROFESSIONAL,
                'enterprise': TierLevel.PROFESSIONAL
            }
            
            return tier_mapping.get(subscription.plan_type, TierLevel.BUDGET)
            
        except Exception as e:
            logger.error(f"Error getting user tier for user {user_id}: {str(e)}")
            return TierLevel.BUDGET
    
    def get_tier_limits(self, tier: TierLevel) -> TierLimits:
        """
        Get limits for a specific tier
        
        Args:
            tier: Tier level
            
        Returns:
            Tier limits configuration
        """
        return self.tier_limits.get(tier, self.tier_limits[TierLevel.BUDGET])
    
    def get_user_usage_metrics(self, user_id: str) -> UsageMetrics:
        """
        Get current usage metrics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Current usage metrics
        """
        try:
            # Check cache first
            cache_key = f"usage_{user_id}"
            if cache_key in self.usage_cache:
                cached_metrics = self.usage_cache[cache_key]
                if cached_metrics and hasattr(cached_metrics, 'cached_at'):
                    if datetime.utcnow() - cached_metrics.cached_at < self.cache_ttl:
                        return cached_metrics
            
            # Get account counts
            total_accounts = self.db_session.query(func.count(BankAccount.id)).filter(
                BankAccount.user_id == user_id,
                BankAccount.is_active == True
            ).scalar() or 0
            
            # Get institution counts
            total_institutions = self.db_session.query(func.count(func.distinct(PlaidConnection.institution_id))).filter(
                PlaidConnection.user_id == user_id,
                PlaidConnection.is_active == True
            ).scalar() or 0
            
            # Get connection counts
            total_connections = self.db_session.query(func.count(PlaidConnection.id)).filter(
                PlaidConnection.user_id == user_id,
                PlaidConnection.is_active == True
            ).scalar() or 0
            
            # Get active accounts
            active_accounts = self.db_session.query(func.count(BankAccount.id)).filter(
                and_(
                    BankAccount.user_id == user_id,
                    BankAccount.is_active == True,
                    BankAccount.status == 'active'
                )
            ).scalar() or 0
            
            # Get last sync time
            last_sync = self.db_session.query(func.max(BankAccount.last_sync_at)).filter(
                BankAccount.user_id == user_id
            ).scalar()
            
            # Get monthly transaction count (approximate)
            monthly_transactions = self._get_monthly_transaction_count(user_id)
            
            # Get storage usage (approximate)
            storage_used = self._get_storage_usage(user_id)
            
            # Create usage metrics
            metrics = UsageMetrics(
                total_accounts=total_accounts,
                total_institutions=total_institutions,
                total_connections=total_connections,
                active_accounts=active_accounts,
                last_sync_at=last_sync,
                sync_frequency='daily',  # Default, could be dynamic
                monthly_transactions=monthly_transactions,
                storage_used_mb=storage_used
            )
            
            # Cache the results
            metrics.cached_at = datetime.utcnow()
            self.usage_cache[cache_key] = metrics
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting usage metrics for user {user_id}: {str(e)}")
            return UsageMetrics(
                total_accounts=0,
                total_institutions=0,
                total_connections=0,
                active_accounts=0,
                last_sync_at=None,
                sync_frequency='manual',
                monthly_transactions=0,
                storage_used_mb=0.0
            )
    
    def check_account_linking_access(self, user_id: str, institution_id: str = None) -> Dict[str, Any]:
        """
        Check if user can link additional accounts
        
        Args:
            user_id: User ID
            institution_id: Optional institution ID for new connection
            
        Returns:
            Access control result with details
        """
        try:
            # Get user tier and limits
            user_tier = self.get_user_tier(user_id)
            tier_limits = self.get_tier_limits(user_tier)
            usage_metrics = self.get_user_usage_metrics(user_id)
            
            # Budget tier: No account linking allowed
            if user_tier == TierLevel.BUDGET:
                return {
                    'access': AccessResult.UPGRADE_REQUIRED,
                    'reason': 'Account linking requires a paid subscription',
                    'current_tier': user_tier.value,
                    'upgrade_prompt': self._create_upgrade_prompt(user_tier, 'account_linking'),
                    'usage': usage_metrics,
                    'limits': tier_limits
                }
            
            # Check account limits
            if tier_limits.max_accounts > 0 and usage_metrics.total_accounts >= tier_limits.max_accounts:
                return {
                    'access': AccessResult.LIMIT_REACHED,
                    'reason': f'Account limit reached ({usage_metrics.total_accounts}/{tier_limits.max_accounts})',
                    'current_tier': user_tier.value,
                    'upgrade_prompt': self._create_upgrade_prompt(user_tier, 'account_limit'),
                    'usage': usage_metrics,
                    'limits': tier_limits
                }
            
            # Check institution limits
            if tier_limits.max_institutions > 0 and usage_metrics.total_institutions >= tier_limits.max_institutions:
                return {
                    'access': AccessResult.LIMIT_REACHED,
                    'reason': f'Institution limit reached ({usage_metrics.total_institutions}/{tier_limits.max_institutions})',
                    'current_tier': user_tier.value,
                    'upgrade_prompt': self._create_upgrade_prompt(user_tier, 'institution_limit'),
                    'usage': usage_metrics,
                    'limits': tier_limits
                }
            
            # Check connection limits
            if tier_limits.max_connections > 0 and usage_metrics.total_connections >= tier_limits.max_connections:
                return {
                    'access': AccessResult.LIMIT_REACHED,
                    'reason': f'Connection limit reached ({usage_metrics.total_connections}/{tier_limits.max_connections})',
                    'current_tier': user_tier.value,
                    'upgrade_prompt': self._create_upgrade_prompt(user_tier, 'connection_limit'),
                    'usage': usage_metrics,
                    'limits': tier_limits
                }
            
            # Access allowed
            return {
                'access': AccessResult.ALLOWED,
                'reason': 'Account linking allowed',
                'current_tier': user_tier.value,
                'usage': usage_metrics,
                'limits': tier_limits,
                'remaining_accounts': tier_limits.max_accounts - usage_metrics.total_accounts if tier_limits.max_accounts > 0 else -1,
                'remaining_institutions': tier_limits.max_institutions - usage_metrics.total_institutions if tier_limits.max_institutions > 0 else -1
            }
            
        except Exception as e:
            logger.error(f"Error checking account linking access for user {user_id}: {str(e)}")
            return {
                'access': AccessResult.DENIED,
                'reason': 'Error checking access permissions',
                'current_tier': 'unknown',
                'usage': None,
                'limits': None
            }
    
    def check_feature_access(self, user_id: str, feature: str) -> Dict[str, Any]:
        """
        Check if user has access to a specific feature
        
        Args:
            user_id: User ID
            feature: Feature name to check
            
        Returns:
            Feature access result
        """
        try:
            user_tier = self.get_user_tier(user_id)
            tier_limits = self.get_tier_limits(user_tier)
            
            # Feature access mapping
            feature_access = {
                'advanced_analytics': tier_limits.advanced_analytics,
                'real_time_sync': tier_limits.real_time_sync,
                'priority_support': tier_limits.priority_support,
                'custom_alerts': tier_limits.custom_alerts,
                'data_export': tier_limits.data_export,
                'api_access': tier_limits.api_access,
                'transaction_history': usage_metrics.total_accounts > 0 and tier_limits.transaction_history_months > 0
            }
            
            has_access = feature_access.get(feature, False)
            
            if has_access:
                return {
                    'access': AccessResult.ALLOWED,
                    'reason': f'Feature {feature} is available in {user_tier.value} tier',
                    'current_tier': user_tier.value
                }
            else:
                return {
                    'access': AccessResult.FEATURE_RESTRICTED,
                    'reason': f'Feature {feature} requires a higher tier',
                    'current_tier': user_tier.value,
                    'upgrade_prompt': self._create_upgrade_prompt(user_tier, feature)
                }
                
        except Exception as e:
            logger.error(f"Error checking feature access for user {user_id}, feature {feature}: {str(e)}")
            return {
                'access': AccessResult.DENIED,
                'reason': 'Error checking feature access',
                'current_tier': 'unknown'
            }
    
    def enforce_account_limits(self, user_id: str, new_accounts: int = 1) -> Dict[str, Any]:
        """
        Enforce account limits when adding new accounts
        
        Args:
            user_id: User ID
            new_accounts: Number of new accounts being added
            
        Returns:
            Enforcement result
        """
        try:
            user_tier = self.get_user_tier(user_id)
            tier_limits = self.get_tier_limits(user_tier)
            usage_metrics = self.get_user_usage_metrics(user_id)
            
            # Check if adding new accounts would exceed limits
            if tier_limits.max_accounts > 0:
                total_after_addition = usage_metrics.total_accounts + new_accounts
                if total_after_addition > tier_limits.max_accounts:
                    return {
                        'enforced': False,
                        'reason': f'Adding {new_accounts} accounts would exceed limit ({tier_limits.max_accounts})',
                        'current_accounts': usage_metrics.total_accounts,
                        'requested_addition': new_accounts,
                        'limit': tier_limits.max_accounts,
                        'upgrade_prompt': self._create_upgrade_prompt(user_tier, 'account_limit')
                    }
            
            # Limits satisfied
            return {
                'enforced': True,
                'reason': 'Account limits satisfied',
                'current_accounts': usage_metrics.total_accounts,
                'requested_addition': new_accounts,
                'remaining_accounts': tier_limits.max_accounts - usage_metrics.total_accounts if tier_limits.max_accounts > 0 else -1
            }
            
        except Exception as e:
            logger.error(f"Error enforcing account limits for user {user_id}: {str(e)}")
            return {
                'enforced': False,
                'reason': 'Error enforcing account limits',
                'current_accounts': 0,
                'requested_addition': new_accounts,
                'limit': 0
            }
    
    def track_account_linking_usage(self, user_id: str, accounts_added: int, institution_id: str):
        """
        Track account linking usage for analytics
        
        Args:
            user_id: User ID
            accounts_added: Number of accounts added
            institution_id: Institution ID
        """
        try:
            # Track in analytics
            self.analytics_service.track_event(
                user_id=user_id,
                event_type='account_linked',
                properties={
                    'accounts_added': accounts_added,
                    'institution_id': institution_id,
                    'user_tier': self.get_user_tier(user_id).value
                }
            )
            
            # Clear usage cache to force refresh
            cache_key = f"usage_{user_id}"
            if cache_key in self.usage_cache:
                del self.usage_cache[cache_key]
            
            # Send usage notification if approaching limits
            self._check_usage_notifications(user_id)
            
        except Exception as e:
            logger.error(f"Error tracking account linking usage for user {user_id}: {str(e)}")
    
    def get_upgrade_recommendations(self, user_id: str) -> List[UpgradePrompt]:
        """
        Get personalized upgrade recommendations for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of upgrade recommendations
        """
        try:
            user_tier = self.get_user_tier(user_id)
            usage_metrics = self.get_user_usage_metrics(user_id)
            recommendations = []
            
            # Check if user is approaching limits
            tier_limits = self.get_tier_limits(user_tier)
            
            if user_tier == TierLevel.BUDGET:
                # Budget users: Recommend mid-tier for basic features
                recommendations.append(self._create_upgrade_prompt(user_tier, 'account_linking'))
            
            elif user_tier == TierLevel.MID_TIER:
                # Mid-tier users: Check for limit proximity
                if tier_limits.max_accounts > 0:
                    usage_percentage = (usage_metrics.total_accounts / tier_limits.max_accounts) * 100
                    if usage_percentage >= 80:
                        recommendations.append(self._create_upgrade_prompt(user_tier, 'account_limit'))
                
                # Recommend professional for advanced features
                if usage_metrics.total_accounts > 0:
                    recommendations.append(self._create_upgrade_prompt(user_tier, 'advanced_features'))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting upgrade recommendations for user {user_id}: {str(e)}")
            return []
    
    def _create_upgrade_prompt(self, current_tier: TierLevel, trigger: str) -> UpgradePrompt:
        """
        Create upgrade prompt based on current tier and trigger
        
        Args:
            current_tier: Current user tier
            trigger: What triggered the upgrade prompt
            
        Returns:
            Upgrade prompt configuration
        """
        prompts = {
            TierLevel.BUDGET: {
                'account_linking': UpgradePrompt(
                    title="Unlock Bank Account Linking",
                    message="Connect your bank accounts to get started with MINGUS financial management.",
                    benefits=[
                        "Link up to 2 bank accounts",
                        "Automatic transaction sync",
                        "Basic spending insights",
                        "Email notifications"
                    ],
                    current_tier="budget",
                    recommended_tier="mid_tier",
                    upgrade_url="/billing/upgrade?plan=mid_tier",
                    preview_features=[
                        "Account balance tracking",
                        "Transaction categorization",
                        "Monthly spending reports"
                    ],
                    trial_available=True,
                    trial_days=14
                ),
                'feature_preview': UpgradePrompt(
                    title="Preview Banking Features",
                    message="See what you can do with connected bank accounts.",
                    benefits=[
                        "Real-time account balances",
                        "Transaction history",
                        "Spending analytics",
                        "Budget tracking"
                    ],
                    current_tier="budget",
                    recommended_tier="mid_tier",
                    upgrade_url="/billing/upgrade?plan=mid_tier&trial=true",
                    preview_features=[
                        "Sample dashboard view",
                        "Demo transaction data",
                        "Feature comparison"
                    ],
                    trial_available=True,
                    trial_days=14
                )
            },
            TierLevel.MID_TIER: {
                'account_limit': UpgradePrompt(
                    title="Unlock Unlimited Accounts",
                    message="You've reached your account limit. Upgrade to link unlimited accounts.",
                    benefits=[
                        "Unlimited bank accounts",
                        "Unlimited institutions",
                        "Real-time sync",
                        "Priority support",
                        "Advanced analytics",
                        "API access"
                    ],
                    current_tier="mid_tier",
                    recommended_tier="professional",
                    upgrade_url="/billing/upgrade?plan=professional",
                    preview_features=[
                        "Multi-account dashboard",
                        "Cross-account analytics",
                        "Advanced reporting"
                    ],
                    trial_available=True,
                    trial_days=7
                ),
                'advanced_features': UpgradePrompt(
                    title="Unlock Advanced Features",
                    message="Upgrade to access advanced financial management features.",
                    benefits=[
                        "Real-time data sync",
                        "Advanced analytics",
                        "Custom alerts",
                        "Data export",
                        "API access",
                        "Priority support"
                    ],
                    current_tier="mid_tier",
                    recommended_tier="professional",
                    upgrade_url="/billing/upgrade?plan=professional",
                    preview_features=[
                        "Advanced analytics demo",
                        "Custom alert setup",
                        "API documentation"
                    ],
                    trial_available=True,
                    trial_days=7
                )
            }
        }
        
        return prompts.get(current_tier, {}).get(trigger, UpgradePrompt(
            title="Upgrade Your Plan",
            message="Upgrade to access more features and higher limits.",
            benefits=["More features", "Higher limits", "Better support"],
            current_tier=current_tier.value,
            recommended_tier="professional",
            upgrade_url="/billing/upgrade",
            preview_features=[],
            trial_available=False,
            trial_days=0
        ))
    
    def _get_monthly_transaction_count(self, user_id: str) -> int:
        """Get approximate monthly transaction count for user"""
        try:
            # This would typically query transaction data
            # For now, return a placeholder
            return 0
        except Exception as e:
            logger.error(f"Error getting monthly transaction count for user {user_id}: {str(e)}")
            return 0
    
    def _get_storage_usage(self, user_id: str) -> float:
        """Get approximate storage usage for user in MB"""
        try:
            # This would typically calculate storage usage
            # For now, return a placeholder
            return 0.0
        except Exception as e:
            logger.error(f"Error getting storage usage for user {user_id}: {str(e)}")
            return 0.0
    
    def _check_usage_notifications(self, user_id: str):
        """Check if user should receive usage notifications"""
        try:
            user_tier = self.get_user_tier(user_id)
            tier_limits = self.get_tier_limits(user_tier)
            usage_metrics = self.get_user_usage_metrics(user_id)
            
            # Check account usage
            if tier_limits.max_accounts > 0:
                usage_percentage = (usage_metrics.total_accounts / tier_limits.max_accounts) * 100
                
                if usage_percentage >= 90:
                    # Send warning notification
                    self.notification_service.send_notification(
                        user_id=user_id,
                        notification_type='usage_limit_warning',
                        data={
                            'limit_type': 'accounts',
                            'current_usage': usage_metrics.total_accounts,
                            'limit': tier_limits.max_accounts,
                            'percentage': usage_percentage
                        }
                    )
                elif usage_percentage >= 80:
                    # Send info notification
                    self.notification_service.send_notification(
                        user_id=user_id,
                        notification_type='usage_limit_info',
                        data={
                            'limit_type': 'accounts',
                            'current_usage': usage_metrics.total_accounts,
                            'limit': tier_limits.max_accounts,
                            'percentage': usage_percentage
                        }
                    )
            
        except Exception as e:
            logger.error(f"Error checking usage notifications for user {user_id}: {str(e)}")
    
    def clear_usage_cache(self, user_id: str):
        """Clear usage cache for a user"""
        cache_key = f"usage_{user_id}"
        if cache_key in self.usage_cache:
            del self.usage_cache[cache_key]
    
    def get_tier_comparison(self) -> Dict[str, Any]:
        """Get tier comparison for display"""
        return {
            'budget': {
                'name': 'Budget',
                'price': '$0/month',
                'limits': self.tier_limits[TierLevel.BUDGET],
                'features': [
                    'Basic financial tracking',
                    'Manual transaction entry',
                    'Basic reports'
                ]
            },
            'mid_tier': {
                'name': 'Mid-Tier',
                'price': '$9.99/month',
                'limits': self.tier_limits[TierLevel.MID_TIER],
                'features': [
                    'Up to 2 bank accounts',
                    'Automatic transaction sync',
                    'Advanced analytics',
                    'Custom alerts',
                    'Data export'
                ]
            },
            'professional': {
                'name': 'Professional',
                'price': '$29.99/month',
                'limits': self.tier_limits[TierLevel.PROFESSIONAL],
                'features': [
                    'Unlimited bank accounts',
                    'Real-time sync',
                    'Advanced analytics',
                    'Priority support',
                    'API access',
                    'Custom integrations'
                ]
            }
        } 