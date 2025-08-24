#!/usr/bin/env python3
"""
Subscription Controls System
Provides comprehensive integration between subscription controls and all MINGUS application features
to ensure proper tier access and upgrade prompts.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
from collections import defaultdict
import uuid
import functools
from abc import ABC, abstractmethod

# Configure logging
logger = logging.getLogger(__name__)

class FeatureCategory(Enum):
    """Feature categories"""
    BUDGETING = "budgeting"
    INVESTMENT = "investment"
    RETIREMENT = "retirement"
    TAX_OPTIMIZATION = "tax_optimization"
    DEBT_MANAGEMENT = "debt_management"
    INSURANCE = "insurance"
    ESTATE_PLANNING = "estate_planning"
    ANALYTICS = "analytics"
    REPORTING = "reporting"
    EXPORT = "export"
    API_ACCESS = "api_access"
    PREMIUM_SUPPORT = "premium_support"

class AccessLevel(Enum):
    """Access levels"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class FeatureStatus(Enum):
    """Feature status"""
    AVAILABLE = "available"
    RESTRICTED = "restricted"
    UPGRADE_REQUIRED = "upgrade_required"
    TRIAL_AVAILABLE = "trial_available"
    COMING_SOON = "coming_soon"

class UpgradeTrigger(Enum):
    """Upgrade triggers"""
    FEATURE_ACCESS = "feature_access"
    USAGE_LIMIT = "usage_limit"
    DATA_LIMIT = "data_limit"
    EXPORT_LIMIT = "export_limit"
    API_LIMIT = "api_limit"
    SUPPORT_LIMIT = "support_limit"
    CUSTOMIZATION_LIMIT = "customization_limit"

@dataclass
class FeatureDefinition:
    """Feature definition"""
    feature_id: str
    name: str
    description: str
    category: FeatureCategory
    access_level: AccessLevel
    status: FeatureStatus
    usage_limits: Dict[str, Any]
    upgrade_triggers: List[UpgradeTrigger]
    dependencies: List[str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class UserFeatureAccess:
    """User feature access"""
    user_id: str
    feature_id: str
    access_level: AccessLevel
    current_usage: Dict[str, Any]
    usage_limits: Dict[str, Any]
    last_accessed: datetime
    access_count: int
    is_active: bool = True
    trial_expires_at: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass
class UpgradePrompt:
    """Upgrade prompt"""
    prompt_id: str
    user_id: str
    feature_id: str
    trigger_type: UpgradeTrigger
    current_tier: str
    recommended_tier: str
    value_proposition: str
    urgency_level: int
    context_data: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

@dataclass
class FeatureUsage:
    """Feature usage tracking"""
    usage_id: str
    user_id: str
    feature_id: str
    usage_type: str
    usage_data: Dict[str, Any]
    timestamp: datetime
    session_id: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class FeatureAccessManager:
    """Manages feature access and permissions"""
    
    def __init__(self, db, subscription_service, upgrade_optimization_service):
        self.db = db
        self.subscription_service = subscription_service
        self.upgrade_optimization_service = upgrade_optimization_service
        self.feature_definitions = self._initialize_feature_definitions()
        self.access_cache = {}
    
    def check_feature_access(self, user_id: str, feature_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if user has access to a feature"""
        try:
            # Get user subscription
            subscription = self.subscription_service.get_user_subscription(user_id)
            user_tier = subscription.get('plan_id', 'free')
            
            # Get feature definition
            feature_def = self.feature_definitions.get(feature_id)
            if not feature_def:
                return {
                    'has_access': False,
                    'reason': 'feature_not_found',
                    'upgrade_required': False,
                    'trial_available': False
                }
            
            # Check basic access level
            has_access = self._check_access_level(user_tier, feature_def.access_level)
            
            if not has_access:
                return {
                    'has_access': False,
                    'reason': 'upgrade_required',
                    'upgrade_required': True,
                    'trial_available': feature_def.status == FeatureStatus.TRIAL_AVAILABLE,
                    'recommended_tier': feature_def.access_level.value
                }
            
            # Check usage limits
            usage_check = self._check_usage_limits(user_id, feature_id, feature_def)
            if not usage_check['within_limits']:
                return {
                    'has_access': False,
                    'reason': 'usage_limit_exceeded',
                    'upgrade_required': True,
                    'trial_available': False,
                    'current_usage': usage_check['current_usage'],
                    'usage_limit': usage_check['usage_limit']
                }
            
            # Check dependencies
            dependency_check = self._check_dependencies(user_id, feature_def.dependencies)
            if not dependency_check['all_available']:
                return {
                    'has_access': False,
                    'reason': 'dependency_not_met',
                    'upgrade_required': True,
                    'trial_available': False,
                    'missing_dependencies': dependency_check['missing_dependencies']
                }
            
            # Update usage tracking
            self._track_feature_usage(user_id, feature_id, context)
            
            return {
                'has_access': True,
                'reason': 'access_granted',
                'upgrade_required': False,
                'trial_available': False,
                'current_usage': usage_check['current_usage'],
                'usage_limit': usage_check['usage_limit']
            }
            
        except Exception as e:
            logger.error(f"Error checking feature access for user {user_id}, feature {feature_id}: {e}")
            return {
                'has_access': False,
                'reason': 'error',
                'upgrade_required': False,
                'trial_available': False
            }
    
    def get_user_features(self, user_id: str) -> Dict[str, Any]:
        """Get all features available to user"""
        try:
            subscription = self.subscription_service.get_user_subscription(user_id)
            user_tier = subscription.get('plan_id', 'free')
            
            features = {
                'available_features': [],
                'restricted_features': [],
                'trial_features': [],
                'upgrade_recommendations': []
            }
            
            for feature_id, feature_def in self.feature_definitions.items():
                access_check = self.check_feature_access(user_id, feature_id)
                
                if access_check['has_access']:
                    features['available_features'].append({
                        'feature_id': feature_id,
                        'name': feature_def.name,
                        'description': feature_def.description,
                        'category': feature_def.category.value,
                        'current_usage': access_check.get('current_usage', {}),
                        'usage_limit': access_check.get('usage_limit', {})
                    })
                elif access_check['trial_available']:
                    features['trial_features'].append({
                        'feature_id': feature_id,
                        'name': feature_def.name,
                        'description': feature_def.description,
                        'category': feature_def.category.value,
                        'recommended_tier': feature_def.access_level.value
                    })
                else:
                    features['restricted_features'].append({
                        'feature_id': feature_id,
                        'name': feature_def.name,
                        'description': feature_def.description,
                        'category': feature_def.category.value,
                        'recommended_tier': feature_def.access_level.value,
                        'upgrade_required': access_check['upgrade_required']
                    })
            
            # Generate upgrade recommendations
            features['upgrade_recommendations'] = self._generate_upgrade_recommendations(user_id, features)
            
            return features
            
        except Exception as e:
            logger.error(f"Error getting user features for user {user_id}: {e}")
            return {'available_features': [], 'restricted_features': [], 'trial_features': [], 'upgrade_recommendations': []}
    
    def create_upgrade_prompt(self, user_id: str, feature_id: str, trigger_type: UpgradeTrigger, context: Dict[str, Any] = None) -> Optional[UpgradePrompt]:
        """Create upgrade prompt for user"""
        try:
            # Get feature definition
            feature_def = self.feature_definitions.get(feature_id)
            if not feature_def:
                return None
            
            # Get user subscription
            subscription = self.subscription_service.get_user_subscription(user_id)
            current_tier = subscription.get('plan_id', 'free')
            
            # Determine recommended tier
            recommended_tier = feature_def.access_level.value
            
            # Generate value proposition
            value_proposition = self._generate_value_proposition(feature_def, trigger_type, context)
            
            # Calculate urgency level
            urgency_level = self._calculate_urgency_level(trigger_type, context)
            
            # Create upgrade prompt
            prompt = UpgradePrompt(
                prompt_id=str(uuid.uuid4()),
                user_id=user_id,
                feature_id=feature_id,
                trigger_type=trigger_type,
                current_tier=current_tier,
                recommended_tier=recommended_tier,
                value_proposition=value_proposition,
                urgency_level=urgency_level,
                context_data=context or {},
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            )
            
            # Save prompt
            self._save_upgrade_prompt(prompt)
            
            # Track analytics
            self._track_upgrade_prompt_creation(user_id, prompt)
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error creating upgrade prompt for user {user_id}, feature {feature_id}: {e}")
            return None
    
    def track_feature_usage(self, user_id: str, feature_id: str, usage_type: str, usage_data: Dict[str, Any], session_id: str = None) -> None:
        """Track feature usage"""
        try:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            usage = FeatureUsage(
                usage_id=str(uuid.uuid4()),
                user_id=user_id,
                feature_id=feature_id,
                usage_type=usage_type,
                usage_data=usage_data,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id
            )
            
            # Save usage
            self._save_feature_usage(usage)
            
            # Check for upgrade triggers
            self._check_upgrade_triggers(user_id, feature_id, usage)
            
        except Exception as e:
            logger.error(f"Error tracking feature usage for user {user_id}, feature {feature_id}: {e}")
    
    def get_feature_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get feature usage analytics for user"""
        try:
            analytics = {
                'user_id': user_id,
                'feature_usage': {},
                'usage_trends': {},
                'upgrade_opportunities': [],
                'recommendations': []
            }
            
            # Get feature usage data
            feature_usage = self._get_user_feature_usage(user_id)
            analytics['feature_usage'] = feature_usage
            
            # Calculate usage trends
            analytics['usage_trends'] = self._calculate_usage_trends(user_id)
            
            # Identify upgrade opportunities
            analytics['upgrade_opportunities'] = self._identify_upgrade_opportunities(user_id, feature_usage)
            
            # Generate recommendations
            analytics['recommendations'] = self._generate_feature_recommendations(user_id, analytics)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting feature analytics for user {user_id}: {e}")
            return {}
    
    def _initialize_feature_definitions(self) -> Dict[str, FeatureDefinition]:
        """Initialize feature definitions"""
        features = {
            # Budgeting Features
            'budget_tracker': FeatureDefinition(
                feature_id='budget_tracker',
                name='Budget Tracker',
                description='Track income and expenses with detailed categorization',
                category=FeatureCategory.BUDGETING,
                access_level=AccessLevel.FREE,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'transactions_per_month': 100, 'categories': 10},
                upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT],
                dependencies=[]
            ),
            'expense_categorizer': FeatureDefinition(
                feature_id='expense_categorizer',
                name='Expense Categorizer',
                description='Automatically categorize expenses with AI',
                category=FeatureCategory.BUDGETING,
                access_level=AccessLevel.BASIC,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'categorizations_per_month': 500},
                upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT],
                dependencies=['budget_tracker']
            ),
            'savings_goals': FeatureDefinition(
                feature_id='savings_goals',
                name='Savings Goals',
                description='Set and track savings goals with progress visualization',
                category=FeatureCategory.BUDGETING,
                access_level=AccessLevel.BASIC,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'goals': 5, 'goal_amount': 10000},
                upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT],
                dependencies=['budget_tracker']
            ),
            
            # Investment Features
            'investment_analysis': FeatureDefinition(
                feature_id='investment_analysis',
                name='Investment Analysis',
                description='Analyze investment opportunities and portfolio performance',
                category=FeatureCategory.INVESTMENT,
                access_level=AccessLevel.PREMIUM,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'analyses_per_month': 10, 'portfolios': 3},
                upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT, UpgradeTrigger.FEATURE_ACCESS],
                dependencies=['budget_tracker']
            ),
            'portfolio_tracker': FeatureDefinition(
                feature_id='portfolio_tracker',
                name='Portfolio Tracker',
                description='Track investment portfolio with real-time updates',
                category=FeatureCategory.INVESTMENT,
                access_level=AccessLevel.PREMIUM,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'portfolios': 5, 'holdings_per_portfolio': 50},
                upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT, UpgradeTrigger.FEATURE_ACCESS],
                dependencies=['investment_analysis']
            ),
            'risk_assessment': FeatureDefinition(
                feature_id='risk_assessment',
                name='Risk Assessment',
                description='Assess investment risk tolerance and portfolio risk',
                category=FeatureCategory.INVESTMENT,
                access_level=AccessLevel.PROFESSIONAL,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'assessments_per_month': 5},
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
                dependencies=['portfolio_tracker']
            ),
            
            # Retirement Features
            'retirement_planner': FeatureDefinition(
                feature_id='retirement_planner',
                name='Retirement Planner',
                description='Plan for retirement with comprehensive analysis',
                category=FeatureCategory.RETIREMENT,
                access_level=AccessLevel.PREMIUM,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'plans': 3, 'scenarios_per_plan': 5},
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
                dependencies=['budget_tracker']
            ),
            'social_security_optimizer': FeatureDefinition(
                feature_id='social_security_optimizer',
                name='Social Security Optimizer',
                description='Optimize Social Security claiming strategy',
                category=FeatureCategory.RETIREMENT,
                access_level=AccessLevel.PROFESSIONAL,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'optimizations_per_month': 3},
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
                dependencies=['retirement_planner']
            ),
            
            # Tax Optimization Features
            'tax_optimizer': FeatureDefinition(
                feature_id='tax_optimizer',
                name='Tax Optimizer',
                description='Optimize tax strategy and identify deductions',
                category=FeatureCategory.TAX_OPTIMIZATION,
                access_level=AccessLevel.PROFESSIONAL,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'optimizations_per_year': 10},
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
                dependencies=['budget_tracker', 'investment_analysis']
            ),
            'tax_loss_harvesting': FeatureDefinition(
                feature_id='tax_loss_harvesting',
                name='Tax Loss Harvesting',
                description='Identify tax loss harvesting opportunities',
                category=FeatureCategory.TAX_OPTIMIZATION,
                access_level=AccessLevel.PROFESSIONAL,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'harvests_per_year': 12},
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
                dependencies=['portfolio_tracker', 'tax_optimizer']
            ),
            
            # Debt Management Features
            'debt_tracker': FeatureDefinition(
                feature_id='debt_tracker',
                name='Debt Tracker',
                description='Track and manage debt with payoff strategies',
                category=FeatureCategory.DEBT_MANAGEMENT,
                access_level=AccessLevel.BASIC,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'debts': 10, 'strategies': 3},
                upgrade_triggers=[UpgradeTrigger.USAGE_LIMIT],
                dependencies=['budget_tracker']
            ),
            'debt_payoff_optimizer': FeatureDefinition(
                feature_id='debt_payoff_optimizer',
                name='Debt Payoff Optimizer',
                description='Optimize debt payoff strategy for maximum savings',
                category=FeatureCategory.DEBT_MANAGEMENT,
                access_level=AccessLevel.PREMIUM,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'optimizations_per_month': 5},
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
                dependencies=['debt_tracker']
            ),
            
            # Analytics Features
            'financial_analytics': FeatureDefinition(
                feature_id='financial_analytics',
                name='Financial Analytics',
                description='Advanced financial analytics and insights',
                category=FeatureCategory.ANALYTICS,
                access_level=AccessLevel.PREMIUM,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'reports_per_month': 20},
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
                dependencies=['budget_tracker']
            ),
            'predictive_analytics': FeatureDefinition(
                feature_id='predictive_analytics',
                name='Predictive Analytics',
                description='Predict future financial outcomes using AI',
                category=FeatureCategory.ANALYTICS,
                access_level=AccessLevel.PROFESSIONAL,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'predictions_per_month': 10},
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS, UpgradeTrigger.USAGE_LIMIT],
                dependencies=['financial_analytics']
            ),
            
            # Export Features
            'data_export': FeatureDefinition(
                feature_id='data_export',
                name='Data Export',
                description='Export financial data in various formats',
                category=FeatureCategory.EXPORT,
                access_level=AccessLevel.BASIC,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'exports_per_month': 5, 'data_limit_mb': 10},
                upgrade_triggers=[UpgradeTrigger.EXPORT_LIMIT],
                dependencies=['budget_tracker']
            ),
            'advanced_export': FeatureDefinition(
                feature_id='advanced_export',
                name='Advanced Export',
                description='Advanced data export with custom formatting',
                category=FeatureCategory.EXPORT,
                access_level=AccessLevel.PREMIUM,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'exports_per_month': 50, 'data_limit_mb': 100},
                upgrade_triggers=[UpgradeTrigger.EXPORT_LIMIT, UpgradeTrigger.FEATURE_ACCESS],
                dependencies=['data_export']
            ),
            
            # API Access
            'api_access': FeatureDefinition(
                feature_id='api_access',
                name='API Access',
                description='Access MINGUS data via API',
                category=FeatureCategory.API_ACCESS,
                access_level=AccessLevel.PROFESSIONAL,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'requests_per_day': 1000, 'endpoints': ['read']},
                upgrade_triggers=[UpgradeTrigger.API_LIMIT, UpgradeTrigger.FEATURE_ACCESS],
                dependencies=[]
            ),
            'full_api_access': FeatureDefinition(
                feature_id='full_api_access',
                name='Full API Access',
                description='Full API access with write capabilities',
                category=FeatureCategory.API_ACCESS,
                access_level=AccessLevel.ENTERPRISE,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'requests_per_day': 10000, 'endpoints': ['read', 'write']},
                upgrade_triggers=[UpgradeTrigger.API_LIMIT, UpgradeTrigger.FEATURE_ACCESS],
                dependencies=['api_access']
            ),
            
            # Support Features
            'basic_support': FeatureDefinition(
                feature_id='basic_support',
                name='Basic Support',
                description='Email support with 48-hour response',
                category=FeatureCategory.PREMIUM_SUPPORT,
                access_level=AccessLevel.FREE,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'tickets_per_month': 3},
                upgrade_triggers=[UpgradeTrigger.SUPPORT_LIMIT],
                dependencies=[]
            ),
            'premium_support': FeatureDefinition(
                feature_id='premium_support',
                name='Premium Support',
                description='Priority support with 24-hour response',
                category=FeatureCategory.PREMIUM_SUPPORT,
                access_level=AccessLevel.PREMIUM,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'tickets_per_month': 10},
                upgrade_triggers=[UpgradeTrigger.SUPPORT_LIMIT, UpgradeTrigger.FEATURE_ACCESS],
                dependencies=['basic_support']
            ),
            'dedicated_support': FeatureDefinition(
                feature_id='dedicated_support',
                name='Dedicated Support',
                description='Dedicated support representative',
                category=FeatureCategory.PREMIUM_SUPPORT,
                access_level=AccessLevel.ENTERPRISE,
                status=FeatureStatus.AVAILABLE,
                usage_limits={'tickets_per_month': -1},  # Unlimited
                upgrade_triggers=[UpgradeTrigger.FEATURE_ACCESS],
                dependencies=['premium_support']
            )
        }
        
        return features
    
    def _check_access_level(self, user_tier: str, required_level: AccessLevel) -> bool:
        """Check if user tier meets required access level"""
        tier_hierarchy = {
            'free': 0,
            'basic': 1,
            'premium': 2,
            'professional': 3,
            'enterprise': 4
        }
        
        user_level = tier_hierarchy.get(user_tier, 0)
        required_level_value = tier_hierarchy.get(required_level.value, 0)
        
        return user_level >= required_level_value
    
    def _check_usage_limits(self, user_id: str, feature_id: str, feature_def: FeatureDefinition) -> Dict[str, Any]:
        """Check if user is within usage limits"""
        # Get current usage
        current_usage = self._get_current_usage(user_id, feature_id)
        
        # Check each limit
        within_limits = True
        exceeded_limits = []
        
        for limit_key, limit_value in feature_def.usage_limits.items():
            current_value = current_usage.get(limit_key, 0)
            
            if limit_value > 0 and current_value >= limit_value:
                within_limits = False
                exceeded_limits.append(limit_key)
        
        return {
            'within_limits': within_limits,
            'current_usage': current_usage,
            'usage_limit': feature_def.usage_limits,
            'exceeded_limits': exceeded_limits
        }
    
    def _check_dependencies(self, user_id: str, dependencies: List[str]) -> Dict[str, Any]:
        """Check if user has access to all dependencies"""
        missing_dependencies = []
        
        for dependency in dependencies:
            access_check = self.check_feature_access(user_id, dependency)
            if not access_check['has_access']:
                missing_dependencies.append(dependency)
        
        return {
            'all_available': len(missing_dependencies) == 0,
            'missing_dependencies': missing_dependencies
        }
    
    def _track_feature_usage(self, user_id: str, feature_id: str, context: Dict[str, Any] = None) -> None:
        """Track feature usage"""
        usage_data = {
            'timestamp': datetime.now(timezone.utc),
            'context': context or {}
        }
        
        self.track_feature_usage(user_id, feature_id, 'access', usage_data)
    
    def _generate_upgrade_recommendations(self, user_id: str, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate upgrade recommendations"""
        recommendations = []
        
        # Check for restricted features
        for feature in features['restricted_features']:
            if feature['upgrade_required']:
                recommendations.append({
                    'type': 'feature_access',
                    'feature_id': feature['feature_id'],
                    'feature_name': feature['name'],
                    'recommended_tier': feature['recommended_tier'],
                    'priority': 'high' if feature['category'] in ['budgeting', 'investment'] else 'medium'
                })
        
        # Check for trial features
        for feature in features['trial_features']:
            recommendations.append({
                'type': 'trial_feature',
                'feature_id': feature['feature_id'],
                'feature_name': feature['name'],
                'recommended_tier': feature['recommended_tier'],
                'priority': 'medium'
            })
        
        # Check usage-based recommendations
        usage_recommendations = self._get_usage_based_recommendations(user_id)
        recommendations.extend(usage_recommendations)
        
        return recommendations
    
    def _generate_value_proposition(self, feature_def: FeatureDefinition, trigger_type: UpgradeTrigger, context: Dict[str, Any] = None) -> str:
        """Generate value proposition for upgrade prompt"""
        if trigger_type == UpgradeTrigger.FEATURE_ACCESS:
            return f"Unlock {feature_def.name} to {feature_def.description.lower()}"
        elif trigger_type == UpgradeTrigger.USAGE_LIMIT:
            return f"Get unlimited access to {feature_def.name} and more features"
        elif trigger_type == UpgradeTrigger.DATA_LIMIT:
            return f"Handle larger datasets with {feature_def.name}"
        elif trigger_type == UpgradeTrigger.EXPORT_LIMIT:
            return f"Export more data with {feature_def.name}"
        else:
            return f"Upgrade to access {feature_def.name} and unlock your full potential"
    
    def _calculate_urgency_level(self, trigger_type: UpgradeTrigger, context: Dict[str, Any] = None) -> int:
        """Calculate urgency level for upgrade prompt"""
        base_urgency = {
            UpgradeTrigger.FEATURE_ACCESS: 8,
            UpgradeTrigger.USAGE_LIMIT: 6,
            UpgradeTrigger.DATA_LIMIT: 5,
            UpgradeTrigger.EXPORT_LIMIT: 4,
            UpgradeTrigger.API_LIMIT: 7,
            UpgradeTrigger.SUPPORT_LIMIT: 3,
            UpgradeTrigger.CUSTOMIZATION_LIMIT: 5
        }
        
        urgency = base_urgency.get(trigger_type, 5)
        
        # Adjust based on context
        if context:
            if context.get('high_value_user', False):
                urgency += 2
            if context.get('frequent_user', False):
                urgency += 1
            if context.get('trial_expiring_soon', False):
                urgency += 3
        
        return min(urgency, 10)  # Max urgency of 10
    
    def _check_upgrade_triggers(self, user_id: str, feature_id: str, usage: FeatureUsage) -> None:
        """Check for upgrade triggers based on usage"""
        feature_def = self.feature_definitions.get(feature_id)
        if not feature_def:
            return
        
        # Check usage limits
        usage_check = self._check_usage_limits(user_id, feature_id, feature_def)
        if not usage_check['within_limits']:
            for limit in usage_check['exceeded_limits']:
                self.create_upgrade_prompt(user_id, feature_id, UpgradeTrigger.USAGE_LIMIT, {
                    'exceeded_limit': limit,
                    'current_usage': usage_check['current_usage'],
                    'usage_limit': usage_check['usage_limit']
                })
    
    def _get_current_usage(self, user_id: str, feature_id: str) -> Dict[str, Any]:
        """Get current usage for feature"""
        # Mock implementation - in production, retrieve from database
        return {
            'transactions_per_month': 45,
            'categories': 8,
            'categorizations_per_month': 200,
            'goals': 3,
            'analyses_per_month': 5,
            'portfolios': 2,
            'exports_per_month': 2,
            'requests_per_day': 500,
            'tickets_per_month': 1
        }
    
    def _get_usage_based_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get usage-based upgrade recommendations"""
        # Mock implementation - in production, analyze usage patterns
        return [
            {
                'type': 'usage_based',
                'feature_id': 'investment_analysis',
                'feature_name': 'Investment Analysis',
                'recommended_tier': 'premium',
                'priority': 'medium',
                'reason': 'High usage of basic features suggests need for advanced tools'
            }
        ]
    
    def _calculate_usage_trends(self, user_id: str) -> Dict[str, Any]:
        """Calculate usage trends for user"""
        # Mock implementation - in production, calculate trends
        return {
            'total_features_used': 8,
            'most_used_features': ['budget_tracker', 'expense_categorizer', 'savings_goals'],
            'usage_growth_rate': 0.15,
            'feature_adoption_rate': 0.6
        }
    
    def _identify_upgrade_opportunities(self, user_id: str, feature_usage: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify upgrade opportunities based on usage"""
        opportunities = []
        
        # Check for high usage of basic features
        if feature_usage.get('budget_tracker', {}).get('usage_count', 0) > 50:
            opportunities.append({
                'type': 'high_basic_usage',
                'feature_id': 'investment_analysis',
                'recommended_tier': 'premium',
                'confidence': 0.8
            })
        
        # Check for export limitations
        if feature_usage.get('data_export', {}).get('usage_count', 0) >= 5:
            opportunities.append({
                'type': 'export_limit_reached',
                'feature_id': 'advanced_export',
                'recommended_tier': 'premium',
                'confidence': 0.9
            })
        
        return opportunities
    
    def _generate_feature_recommendations(self, user_id: str, analytics: Dict[str, Any]) -> List[str]:
        """Generate feature recommendations for user"""
        recommendations = []
        
        # Based on usage patterns
        if analytics['usage_trends']['total_features_used'] < 5:
            recommendations.append("Explore more features to get the most out of MINGUS")
        
        # Based on upgrade opportunities
        if analytics['upgrade_opportunities']:
            recommendations.append("Consider upgrading to access advanced features")
        
        # Based on usage growth
        if analytics['usage_trends']['usage_growth_rate'] > 0.1:
            recommendations.append("Your usage is growing! Consider premium features for advanced capabilities")
        
        return recommendations
    
    def _get_user_feature_usage(self, user_id: str) -> Dict[str, Any]:
        """Get user feature usage data"""
        # Mock implementation - in production, retrieve from database
        return {
            'budget_tracker': {'usage_count': 75, 'last_used': datetime.now(timezone.utc)},
            'expense_categorizer': {'usage_count': 45, 'last_used': datetime.now(timezone.utc)},
            'savings_goals': {'usage_count': 12, 'last_used': datetime.now(timezone.utc)},
            'data_export': {'usage_count': 5, 'last_used': datetime.now(timezone.utc)}
        }
    
    # Database operations (mock implementations)
    def _save_upgrade_prompt(self, prompt: UpgradePrompt) -> None:
        """Save upgrade prompt to database"""
        # Mock implementation - in production, save to database
        pass
    
    def _save_feature_usage(self, usage: FeatureUsage) -> None:
        """Save feature usage to database"""
        # Mock implementation - in production, save to database
        pass
    
    # Analytics and tracking methods (mock implementations)
    def _track_upgrade_prompt_creation(self, user_id: str, prompt: UpgradePrompt) -> None:
        """Track upgrade prompt creation analytics"""
        # Mock implementation - in production, track analytics
        pass

class SubscriptionControlsDecorator:
    """Decorator for subscription controls"""
    
    def __init__(self, feature_access_manager: FeatureAccessManager):
        self.feature_access_manager = feature_access_manager
    
    def require_feature_access(self, feature_id: str):
        """Decorator to require feature access"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user_id from args or kwargs
                user_id = self._extract_user_id(args, kwargs)
                if not user_id:
                    raise ValueError("user_id not found in function arguments")
                
                # Check feature access
                access_check = self.feature_access_manager.check_feature_access(user_id, feature_id)
                
                if not access_check['has_access']:
                    # Create upgrade prompt if needed
                    if access_check['upgrade_required']:
                        self.feature_access_manager.create_upgrade_prompt(
                            user_id, feature_id, UpgradeTrigger.FEATURE_ACCESS
                        )
                    
                    raise PermissionError(f"Access to {feature_id} requires upgrade")
                
                # Track usage
                self.feature_access_manager.track_feature_usage(
                    user_id, feature_id, 'function_call', {'function': func.__name__}
                )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def check_usage_limits(self, feature_id: str, usage_type: str):
        """Decorator to check usage limits"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Extract user_id from args or kwargs
                user_id = self._extract_user_id(args, kwargs)
                if not user_id:
                    raise ValueError("user_id not found in function arguments")
                
                # Check usage limits
                access_check = self.feature_access_manager.check_feature_access(user_id, feature_id)
                
                if not access_check['has_access'] and access_check['reason'] == 'usage_limit_exceeded':
                    # Create upgrade prompt
                    self.feature_access_manager.create_upgrade_prompt(
                        user_id, feature_id, UpgradeTrigger.USAGE_LIMIT,
                        access_check.get('context_data', {})
                    )
                    
                    raise PermissionError(f"Usage limit exceeded for {feature_id}")
                
                # Track usage
                self.feature_access_manager.track_feature_usage(
                    user_id, feature_id, usage_type, {'function': func.__name__}
                )
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def _extract_user_id(self, args, kwargs) -> Optional[str]:
        """Extract user_id from function arguments"""
        # Check kwargs first
        if 'user_id' in kwargs:
            return kwargs['user_id']
        
        # Check args (assuming user_id is first argument)
        if args and len(args) > 0:
            return args[0]
        
        return None

# Example usage decorators
def require_subscription_access(feature_id: str):
    """Decorator to require subscription access for a feature"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This would be implemented with actual feature access manager
            return func(*args, **kwargs)
        return wrapper
    return decorator

def track_feature_usage(feature_id: str, usage_type: str = 'function_call'):
    """Decorator to track feature usage"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # This would be implemented with actual feature access manager
            return func(*args, **kwargs)
        return wrapper
    return decorator 