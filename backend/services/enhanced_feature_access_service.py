"""
Enhanced Feature Access Service for MINGUS

This module provides comprehensive feature access control with subscription tier-based access,
graceful degradation, educational content, trial offers, and alternative suggestions.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

logger = logging.getLogger(__name__)

class FeatureTier(Enum):
    """Feature access tiers"""
    BUDGET = "budget"
    MID_TIER = "mid_tier"
    PROFESSIONAL = "professional"

class FeatureCategory(Enum):
    """Feature categories"""
    HEALTH_WELLNESS = "health_wellness"
    FINANCIAL_PLANNING = "financial_planning"
    AI_ANALYTICS = "ai_analytics"
    PLAID_INTEGRATION = "plaid_integration"
    CAREER_ADVANCEMENT = "career_advancement"
    GENERAL = "general"

class UpgradeTrigger(Enum):
    """Upgrade trigger types"""
    USAGE_LIMIT = "usage_limit"
    FEATURE_ACCESS = "feature_access"
    TIER_UPGRADE = "tier_upgrade"
    TRIAL_EXPIRY = "trial_expiry"

@dataclass
class FeatureDefinition:
    """Feature definition with access control"""
    feature_id: str
    name: str
    description: str
    category: FeatureCategory
    required_tier: FeatureTier
    usage_limits: Dict[str, int]
    trial_available: bool = False
    trial_duration_days: int = 7
    educational_content: str = ""
    alternative_suggestions: List[str] = None
    upgrade_benefits: List[str] = None

@dataclass
class AccessResult:
    """Result of feature access check"""
    has_access: bool
    reason: str
    current_tier: str
    required_tier: str
    current_usage: Dict[str, int] = None
    usage_limits: Dict[str, int] = None
    upgrade_required: bool = False
    trial_available: bool = False
    educational_content: str = ""
    alternative_suggestions: List[str] = None
    upgrade_benefits: List[str] = None
    trial_offer: Dict[str, Any] = None
    grace_period_remaining: Optional[int] = None

class EnhancedFeatureAccessService:
    """Enhanced feature access service with subscription gating and graceful degradation"""
    
    def __init__(self, db_session: Session, config: Dict[str, Any]):
        self.db = db_session
        self.config = config
        self.feature_definitions = self._initialize_feature_definitions()
        self.tier_configs = self._initialize_tier_configs()
        self.educational_content = self._initialize_educational_content()
        self.trial_offers = self._initialize_trial_offers()
        
    def _initialize_feature_definitions(self) -> Dict[str, FeatureDefinition]:
        """Initialize feature definitions with comprehensive access control"""
        return {
            # Health & Wellness Features
            'health_checkin': FeatureDefinition(
                feature_id='health_checkin',
                name='Health Check-ins',
                description='Track your daily health and wellness metrics',
                category=FeatureCategory.HEALTH_WELLNESS,
                required_tier=FeatureTier.BUDGET,
                usage_limits={'per_month': 4},
                trial_available=True,
                trial_duration_days=7,
                educational_content="Health check-ins help you maintain awareness of your wellness patterns and identify areas for improvement.",
                alternative_suggestions=[
                    "Use our free wellness assessment tool",
                    "Download our wellness tracking template",
                    "Join our wellness community for support"
                ],
                upgrade_benefits=[
                    "Unlimited health check-ins",
                    "Advanced wellness analytics",
                    "Personalized health recommendations",
                    "Integration with fitness trackers"
                ]
            ),
            
            # Financial Planning Features
            'budget_creation': FeatureDefinition(
                feature_id='budget_creation',
                name='Budget Creation',
                description='Create and manage comprehensive budgets',
                category=FeatureCategory.FINANCIAL_PLANNING,
                required_tier=FeatureTier.BUDGET,
                usage_limits={'per_month': 2},
                trial_available=True,
                trial_duration_days=14,
                educational_content="Creating a budget is the foundation of financial success. Learn how to track income, expenses, and savings goals.",
                alternative_suggestions=[
                    "Use our free budget template",
                    "Try our simplified budget calculator",
                    "Access our budget planning guide"
                ],
                upgrade_benefits=[
                    "Unlimited budget creation",
                    "Advanced budget analytics",
                    "Multi-category budgeting",
                    "Budget forecasting and planning"
                ]
            ),
            
            # AI Analytics Features
            'ai_spending_analysis': FeatureDefinition(
                feature_id='ai_spending_analysis',
                name='AI Spending Analysis',
                description='Advanced AI-powered spending pattern analysis',
                category=FeatureCategory.AI_ANALYTICS,
                required_tier=FeatureTier.MID_TIER,
                usage_limits={'per_month': 5},
                trial_available=True,
                trial_duration_days=7,
                educational_content="AI spending analysis provides deep insights into your financial patterns, helping you make better financial decisions.",
                alternative_suggestions=[
                    "Use our basic spending tracker",
                    "Download our spending analysis template",
                    "Try our manual categorization tool"
                ],
                upgrade_benefits=[
                    "Unlimited AI analysis",
                    "Predictive spending insights",
                    "Custom spending categories",
                    "Advanced financial recommendations"
                ]
            ),
            
            # Plaid Integration Features
            'plaid_bank_account_linking': FeatureDefinition(
                feature_id='plaid_bank_account_linking',
                name='Bank Account Linking',
                description='Securely connect your bank accounts via Plaid',
                category=FeatureCategory.PLAID_INTEGRATION,
                required_tier=FeatureTier.MID_TIER,
                usage_limits={'max_accounts': 2, 'max_connections': 1},
                trial_available=True,
                trial_duration_days=14,
                educational_content="Bank account linking provides real-time financial data for better budgeting and financial planning.",
                alternative_suggestions=[
                    "Use manual transaction entry",
                    "Import bank statements manually",
                    "Use our expense tracking templates"
                ],
                upgrade_benefits=[
                    "Unlimited bank accounts",
                    "Multiple financial institutions",
                    "Real-time transaction sync",
                    "Advanced financial insights"
                ]
            ),
            
            'plaid_transaction_history': FeatureDefinition(
                feature_id='plaid_transaction_history',
                name='Transaction History',
                description='Access up to 24 months of transaction history',
                category=FeatureCategory.PLAID_INTEGRATION,
                required_tier=FeatureTier.MID_TIER,
                usage_limits={'history_months': 12},
                trial_available=True,
                trial_duration_days=7,
                educational_content="Transaction history helps you understand your spending patterns and make informed financial decisions.",
                alternative_suggestions=[
                    "Use manual transaction entry",
                    "Import recent bank statements",
                    "Track expenses manually"
                ],
                upgrade_benefits=[
                    "24 months of transaction history",
                    "Advanced transaction categorization",
                    "Spending pattern analysis",
                    "Financial trend insights"
                ]
            ),
            
            'plaid_advanced_analytics': FeatureDefinition(
                feature_id='plaid_advanced_analytics',
                name='Advanced Financial Analytics',
                description='Advanced analytics and insights for your financial data',
                category=FeatureCategory.PLAID_INTEGRATION,
                required_tier=FeatureTier.PROFESSIONAL,
                usage_limits={'per_month': 10},
                trial_available=True,
                trial_duration_days=7,
                educational_content="Advanced analytics provide deep insights into your financial health and help you optimize your financial strategy.",
                alternative_suggestions=[
                    "Use basic financial reports",
                    "Access our financial planning guides",
                    "Try our simplified analytics"
                ],
                upgrade_benefits=[
                    "Unlimited advanced analytics",
                    "Custom financial reports",
                    "Predictive financial modeling",
                    "Personalized financial recommendations"
                ]
            ),
            
            'plaid_identity_verification': FeatureDefinition(
                feature_id='plaid_identity_verification',
                name='Identity Verification',
                description='Verify account holder identity information',
                category=FeatureCategory.PLAID_INTEGRATION,
                required_tier=FeatureTier.MID_TIER,
                usage_limits={'per_month': 5},
                trial_available=True,
                trial_duration_days=7,
                educational_content="Identity verification ensures secure access to your financial information and helps prevent fraud.",
                alternative_suggestions=[
                    "Use manual identity verification",
                    "Contact support for verification",
                    "Use alternative verification methods"
                ],
                upgrade_benefits=[
                    "Unlimited identity verification",
                    "Advanced security features",
                    "Multi-factor authentication",
                    "Enhanced fraud protection"
                ]
            ),
            
            'plaid_real_time_updates': FeatureDefinition(
                feature_id='plaid_real_time_updates',
                name='Real-time Updates',
                description='Real-time balance and transaction updates',
                category=FeatureCategory.PLAID_INTEGRATION,
                required_tier=FeatureTier.MID_TIER,
                usage_limits={'per_day': 100},
                trial_available=True,
                trial_duration_days=7,
                educational_content="Real-time updates keep your financial information current and help you make timely financial decisions.",
                alternative_suggestions=[
                    "Use manual balance updates",
                    "Check your bank account directly",
                    "Set up manual reminders"
                ],
                upgrade_benefits=[
                    "Unlimited real-time updates",
                    "Instant notifications",
                    "Advanced alert system",
                    "Custom update schedules"
                ]
            ),
            
            # Career Advancement Features
            'career_planning': FeatureDefinition(
                feature_id='career_planning',
                name='Career Planning',
                description='Comprehensive career planning and advancement tools',
                category=FeatureCategory.CAREER_ADVANCEMENT,
                required_tier=FeatureTier.MID_TIER,
                usage_limits={'per_month': 3},
                trial_available=True,
                trial_duration_days=14,
                educational_content="Career planning helps you set clear goals, develop skills, and advance in your professional journey.",
                alternative_suggestions=[
                    "Use our career assessment tools",
                    "Access our career planning guides",
                    "Join our career development community"
                ],
                upgrade_benefits=[
                    "Unlimited career planning",
                    "Personalized career coaching",
                    "Advanced skill assessment",
                    "Industry-specific insights"
                ]
            ),
            
            'salary_negotiation': FeatureDefinition(
                feature_id='salary_negotiation',
                name='Salary Negotiation',
                description='Tools and guidance for salary negotiation',
                category=FeatureCategory.CAREER_ADVANCEMENT,
                required_tier=FeatureTier.PROFESSIONAL,
                usage_limits={'per_month': 2},
                trial_available=True,
                trial_duration_days=7,
                educational_content="Salary negotiation skills can significantly impact your earning potential and career growth.",
                alternative_suggestions=[
                    "Use our salary research tools",
                    "Access our negotiation guides",
                    "Practice with our role-play scenarios"
                ],
                upgrade_benefits=[
                    "Unlimited negotiation support",
                    "Personalized coaching sessions",
                    "Market analysis reports",
                    "Advanced negotiation strategies"
                ]
            )
        }
    
    def _initialize_tier_configs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize tier configurations"""
        return {
            'budget': {
                'name': 'Budget',
                'price': 0,
                'features': ['health_checkin', 'budget_creation'],
                'limits': {
                    'health_checkin': {'per_month': 4},
                    'budget_creation': {'per_month': 2}
                },
                'upgrade_to': 'mid_tier',
                'upgrade_price': 19.99
            },
            'mid_tier': {
                'name': 'Mid-Tier',
                'price': 19.99,
                'features': [
                    'health_checkin', 'budget_creation', 'ai_spending_analysis',
                    'plaid_bank_account_linking', 'plaid_transaction_history',
                    'plaid_identity_verification', 'plaid_real_time_updates',
                    'career_planning'
                ],
                'limits': {
                    'health_checkin': {'per_month': 30},
                    'budget_creation': {'per_month': 10},
                    'ai_spending_analysis': {'per_month': 5},
                    'plaid_bank_account_linking': {'max_accounts': 2, 'max_connections': 1},
                    'plaid_transaction_history': {'history_months': 12},
                    'plaid_identity_verification': {'per_month': 5},
                    'plaid_real_time_updates': {'per_day': 100},
                    'career_planning': {'per_month': 3}
                },
                'upgrade_to': 'professional',
                'upgrade_price': 49.99
            },
            'professional': {
                'name': 'Professional',
                'price': 49.99,
                'features': [
                    'health_checkin', 'budget_creation', 'ai_spending_analysis',
                    'plaid_bank_account_linking', 'plaid_transaction_history',
                    'plaid_identity_verification', 'plaid_real_time_updates',
                    'plaid_advanced_analytics', 'career_planning', 'salary_negotiation'
                ],
                'limits': {
                    'health_checkin': {'per_month': -1},  # Unlimited
                    'budget_creation': {'per_month': -1},  # Unlimited
                    'ai_spending_analysis': {'per_month': -1},  # Unlimited
                    'plaid_bank_account_linking': {'max_accounts': -1, 'max_connections': -1},  # Unlimited
                    'plaid_transaction_history': {'history_months': 24},
                    'plaid_identity_verification': {'per_month': -1},  # Unlimited
                    'plaid_real_time_updates': {'per_day': -1},  # Unlimited
                    'plaid_advanced_analytics': {'per_month': 10},
                    'career_planning': {'per_month': -1},  # Unlimited
                    'salary_negotiation': {'per_month': 2}
                },
                'upgrade_to': None,
                'upgrade_price': None
            }
        }
    
    def _initialize_educational_content(self) -> Dict[str, str]:
        """Initialize educational content for features"""
        return {
            'plaid_integration': """
                <h3>Understanding Plaid Integration</h3>
                <p>Plaid is a secure financial technology platform that allows you to connect your bank accounts to MINGUS for automatic transaction tracking and financial insights.</p>
                
                <h4>Benefits of Plaid Integration:</h4>
                <ul>
                    <li><strong>Automatic Transaction Sync:</strong> Your transactions are automatically imported and categorized</li>
                    <li><strong>Real-time Balances:</strong> Always see your current account balances</li>
                    <li><strong>Comprehensive History:</strong> Access up to 24 months of transaction history</li>
                    <li><strong>Advanced Analytics:</strong> Get insights into your spending patterns</li>
                </ul>
                
                <h4>Security & Privacy:</h4>
                <p>Plaid uses bank-level security and encryption. Your banking credentials are never stored by MINGUS - they're securely handled by Plaid's infrastructure.</p>
                
                <h4>Getting Started:</h4>
                <ol>
                    <li>Upgrade to Mid-Tier or Professional subscription</li>
                    <li>Navigate to the Plaid integration section</li>
                    <li>Click "Connect Bank Account"</li>
                    <li>Select your bank and follow the secure authentication process</li>
                    <li>Start enjoying automatic financial tracking!</li>
                </ol>
            """,
            
            'subscription_tiers': """
                <h3>MINGUS Subscription Tiers</h3>
                
                <div class="tier-comparison">
                    <div class="tier budget">
                        <h4>Budget Tier (Free)</h4>
                        <ul>
                            <li>Basic health check-ins (4/month)</li>
                            <li>Simple budget creation (2/month)</li>
                            <li>Manual financial entry</li>
                            <li>Community support</li>
                        </ul>
                    </div>
                    
                    <div class="tier mid-tier">
                        <h4>Mid-Tier ($19.99/month)</h4>
                        <ul>
                            <li>Unlimited health check-ins</li>
                            <li>Advanced budget tools</li>
                            <li>AI spending analysis</li>
                            <li>Plaid integration (2 accounts)</li>
                            <li>12 months transaction history</li>
                            <li>Career planning tools</li>
                            <li>Priority support</li>
                        </ul>
                    </div>
                    
                    <div class="tier professional">
                        <h4>Professional ($49.99/month)</h4>
                        <ul>
                            <li>Everything in Mid-Tier</li>
                            <li>Unlimited Plaid accounts</li>
                            <li>24 months transaction history</li>
                            <li>Advanced financial analytics</li>
                            <li>Salary negotiation tools</li>
                            <li>Personalized coaching</li>
                            <li>Premium support</li>
                        </ul>
                    </div>
                </div>
            """
        }
    
    def _initialize_trial_offers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize trial offers for features"""
        return {
            'plaid_bank_account_linking': {
                'duration_days': 14,
                'description': 'Try Plaid integration free for 14 days',
                'features': ['bank_account_linking', 'transaction_history', 'real_time_updates'],
                'upgrade_required': True
            },
            'plaid_advanced_analytics': {
                'duration_days': 7,
                'description': 'Try advanced analytics free for 7 days',
                'features': ['advanced_analytics', 'predictive_insights'],
                'upgrade_required': True
            },
            'ai_spending_analysis': {
                'duration_days': 7,
                'description': 'Try AI spending analysis free for 7 days',
                'features': ['ai_analysis', 'spending_insights'],
                'upgrade_required': True
            }
        }
    
    def get_user_subscription_tier(self, user_id: str) -> FeatureTier:
        """Get user's current subscription tier"""
        try:
            # This would typically query the user's subscription from the database
            # For now, return a default tier - implement based on your subscription system
            return FeatureTier.BUDGET
        except Exception as e:
            logger.error(f"Error getting subscription tier for user {user_id}: {e}")
            return FeatureTier.BUDGET
    
    def check_feature_access(self, user_id: str, feature_id: str, context: Dict[str, Any] = None) -> AccessResult:
        """Check if user has access to a specific feature"""
        try:
            # Get feature definition
            feature_def = self.feature_definitions.get(feature_id)
            if not feature_def:
                return AccessResult(
                    has_access=False,
                    reason="feature_not_found",
                    current_tier="unknown",
                    required_tier="unknown"
                )
            
            # Get user's current tier
            current_tier = self.get_user_subscription_tier(user_id)
            current_tier_name = current_tier.value
            
            # Check if user's tier meets the requirement
            tier_hierarchy = {
                FeatureTier.BUDGET: 1,
                FeatureTier.MID_TIER: 2,
                FeatureTier.PROFESSIONAL: 3
            }
            
            current_tier_level = tier_hierarchy.get(current_tier, 1)
            required_tier_level = tier_hierarchy.get(feature_def.required_tier, 1)
            
            has_access = current_tier_level >= required_tier_level
            
            # Get usage information
            current_usage = self._get_feature_usage(user_id, feature_id)
            usage_limits = feature_def.usage_limits
            
            # Check if usage limits are exceeded
            usage_exceeded = False
            if has_access and usage_limits:
                for limit_key, limit_value in usage_limits.items():
                    if limit_value > 0:  # -1 means unlimited
                        current_value = current_usage.get(limit_key, 0)
                        if current_value >= limit_value:
                            usage_exceeded = True
                            break
            
            # Determine if upgrade is required
            upgrade_required = not has_access or usage_exceeded
            
            # Get educational content and alternatives
            educational_content = feature_def.educational_content
            alternative_suggestions = feature_def.alternative_suggestions or []
            upgrade_benefits = feature_def.upgrade_benefits or []
            
            # Check if trial is available
            trial_available = feature_def.trial_available and not has_access
            
            # Create trial offer if available
            trial_offer = None
            if trial_available:
                trial_offer = {
                    'feature_id': feature_id,
                    'duration_days': feature_def.trial_duration_days,
                    'description': f"Try {feature_def.name} free for {feature_def.trial_duration_days} days"
                }
            
            return AccessResult(
                has_access=has_access and not usage_exceeded,
                reason="tier_insufficient" if not has_access else ("usage_limit_exceeded" if usage_exceeded else "access_granted"),
                current_tier=current_tier_name,
                required_tier=feature_def.required_tier.value,
                current_usage=current_usage,
                usage_limits=usage_limits,
                upgrade_required=upgrade_required,
                trial_available=trial_available,
                educational_content=educational_content,
                alternative_suggestions=alternative_suggestions,
                upgrade_benefits=upgrade_benefits,
                trial_offer=trial_offer
            )
            
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return AccessResult(
                has_access=False,
                reason="service_error",
                current_tier="unknown",
                required_tier="unknown",
                upgrade_required=True
            )
    
    def _get_feature_usage(self, user_id: str, feature_id: str) -> Dict[str, int]:
        """Get current usage for a specific feature"""
        try:
            # This would typically query usage from the database
            # For now, return empty usage - implement based on your usage tracking system
            return {}
        except Exception as e:
            logger.error(f"Error getting feature usage: {e}")
            return {}
    
    def get_feature_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of all features and their access status"""
        try:
            current_tier = self.get_user_subscription_tier(user_id)
            tier_config = self.tier_configs.get(current_tier.value, {})
            
            feature_summary = {}
            for feature_id, feature_def in self.feature_definitions.items():
                access_result = self.check_feature_access(user_id, feature_id)
                feature_summary[feature_id] = {
                    'name': feature_def.name,
                    'description': feature_def.description,
                    'category': feature_def.category.value,
                    'has_access': access_result.has_access,
                    'reason': access_result.reason,
                    'current_usage': access_result.current_usage,
                    'usage_limits': access_result.usage_limits,
                    'trial_available': access_result.trial_available,
                    'upgrade_required': access_result.upgrade_required
                }
            
            return {
                'user_tier': current_tier.value,
                'tier_name': tier_config.get('name', 'Unknown'),
                'tier_price': tier_config.get('price', 0),
                'features': feature_summary,
                'upgrade_available': tier_config.get('upgrade_to') is not None,
                'upgrade_to': tier_config.get('upgrade_to'),
                'upgrade_price': tier_config.get('upgrade_price')
            }
            
        except Exception as e:
            logger.error(f"Error getting feature summary: {e}")
            return {}
    
    def get_educational_content(self, topic: str) -> str:
        """Get educational content for a specific topic"""
        return self.educational_content.get(topic, "")
    
    def get_trial_offer(self, feature_id: str) -> Optional[Dict[str, Any]]:
        """Get trial offer for a specific feature"""
        return self.trial_offers.get(feature_id) 