"""
Upgrade Prompts Service

This module provides personalized upgrade prompts and suggestions based on user behavior,
usage patterns, and tier limitations to encourage upgrades to higher subscription tiers.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.services.subscription_tier_service import SubscriptionTierService
from backend.services.feature_access_service import FeatureAccessService

logger = logging.getLogger(__name__)


class PromptPriority(Enum):
    """Upgrade prompt priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PromptType(Enum):
    """Types of upgrade prompts"""
    USAGE_LIMIT = "usage_limit"
    FEATURE_PREVIEW = "feature_preview"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    PERSONALIZED_RECOMMENDATION = "personalized_recommendation"
    TIME_BASED = "time_based"


@dataclass
class UpgradePrompt:
    """Upgrade prompt data structure"""
    prompt_id: str
    user_id: str
    prompt_type: PromptType
    title: str
    description: str
    benefit_description: str
    current_limitation: str
    upgrade_feature: str
    upgrade_tier: str
    upgrade_price: float
    cta_text: str
    priority: PromptPriority
    triggered_by: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    dismissed: bool = False
    clicked: bool = False


@dataclass
class UserBehavior:
    """User behavior data structure"""
    user_id: str
    feature_usage: Dict[str, int]
    manual_entries_count: int
    active_days: int
    last_activity: datetime
    tier_upgrade_attempts: int
    feature_requests: List[str]


class UpgradePromptsService:
    """Service for generating and managing upgrade prompts"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.tier_service = SubscriptionTierService(db_session)
        self.feature_service = FeatureAccessService(db_session)
        
        # Mock data storage (in production, this would be database tables)
        self.upgrade_prompts: Dict[str, List[UpgradePrompt]] = {}
        self.user_behaviors: Dict[str, UserBehavior] = {}
        self.prompt_templates = self._initialize_prompt_templates()
    
    def _initialize_prompt_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize prompt templates for different scenarios"""
        return {
            'manual_entry_frequency': {
                'title': "Tired of Manual Entry?",
                'description': "You've entered {count} transactions this month manually. Connect your bank accounts for automatic transaction import.",
                'benefit_description': "Save 2-3 hours per month on manual data entry",
                'current_limitation': "Manual entry only - no automatic transaction import",
                'upgrade_feature': "Bank Account Linking",
                'upgrade_tier': "mid_tier",
                'upgrade_price': 35.0,
                'cta_text': "Upgrade to Mid-Tier",
                'priority': PromptPriority.HIGH,
                'trigger_threshold': 30
            },
            'resume_parsing_limit': {
                'title': "Resume Parsing Limit Reached",
                'description': "You've used your {limit} resume parsing this month. Upgrade for unlimited parsing and advanced career insights.",
                'benefit_description': "Unlimited resume parsing and career advancement tools",
                'current_limitation': "{limit} resume parsing per month",
                'upgrade_feature': "Unlimited Resume Parsing",
                'upgrade_tier': "mid_tier",
                'upgrade_price': 35.0,
                'cta_text': "Get Unlimited Parsing",
                'priority': PromptPriority.MEDIUM,
                'trigger_threshold': 1
            },
            'basic_insights_limit': {
                'title': "Get Deeper Financial Insights",
                'description': "Unlock AI-powered insights and personalized recommendations for your financial health.",
                'benefit_description': "Get personalized financial advice and optimization suggestions",
                'current_limitation': "Basic insights only - no AI recommendations",
                'upgrade_feature': "AI-Powered Insights",
                'upgrade_tier': "mid_tier",
                'upgrade_price': 35.0,
                'cta_text': "Unlock AI Insights",
                'priority': PromptPriority.MEDIUM,
                'trigger_threshold': 7
            },
            'advanced_analytics': {
                'title': "Advanced Financial Analytics",
                'description': "Get cash flow forecasting, investment analysis, and comprehensive financial planning tools.",
                'benefit_description': "Professional-grade financial planning and forecasting",
                'current_limitation': "Basic expense tracking only",
                'upgrade_feature': "Advanced Analytics",
                'upgrade_tier': "professional",
                'upgrade_price': 75.0,
                'cta_text': "Upgrade to Professional",
                'priority': PromptPriority.LOW,
                'trigger_threshold': 100
            },
            'banking_preview': {
                'title': "Connect Your Bank Accounts",
                'description': "See your real-time account balances and automatic transaction categorization.",
                'benefit_description': "Never worry about outdated balance information again",
                'current_limitation': "Manual entry only",
                'upgrade_feature': "Bank Account Linking",
                'upgrade_tier': "mid_tier",
                'upgrade_price': 35.0,
                'cta_text': "Connect Banks",
                'priority': PromptPriority.HIGH,
                'trigger_threshold': 50
            },
            'career_advancement': {
                'title': "Advance Your Career",
                'description': "Get unlimited resume parsing, job market analysis, and career development insights.",
                'benefit_description': "Professional career advancement tools and insights",
                'current_limitation': "Limited career tools",
                'upgrade_feature': "Career Advancement Suite",
                'upgrade_tier': "professional",
                'upgrade_price': 75.0,
                'cta_text': "Advance Career",
                'priority': PromptPriority.MEDIUM,
                'trigger_threshold': 3
            }
        }
    
    def generate_upgrade_prompts(self, user_id: str) -> List[UpgradePrompt]:
        """
        Generate personalized upgrade prompts for a user
        
        Args:
            user_id: User ID to generate prompts for
            
        Returns:
            List of personalized upgrade prompts
        """
        try:
            # Get user's current tier
            user_tier = self.tier_service.get_user_tier(user_id)
            
            # Get user behavior data
            behavior = self._get_user_behavior(user_id)
            
            # Generate prompts based on behavior and tier
            prompts = []
            
            if user_tier.value == 'budget':
                prompts.extend(self._generate_budget_tier_prompts(user_id, behavior))
            elif user_tier.value == 'mid_tier':
                prompts.extend(self._generate_mid_tier_prompts(user_id, behavior))
            
            # Filter and prioritize prompts
            filtered_prompts = self._filter_and_prioritize_prompts(prompts, user_id)
            
            # Store prompts
            if user_id not in self.upgrade_prompts:
                self.upgrade_prompts[user_id] = []
            self.upgrade_prompts[user_id].extend(filtered_prompts)
            
            return filtered_prompts
            
        except Exception as e:
            self.logger.error(f"Error generating upgrade prompts for user {user_id}: {e}")
            return []
    
    def _generate_budget_tier_prompts(self, user_id: str, behavior: UserBehavior) -> List[UpgradePrompt]:
        """Generate prompts for Budget tier users"""
        prompts = []
        
        # Manual entry frequency prompt
        if behavior.manual_entries_count >= 30:
            template = self.prompt_templates['manual_entry_frequency']
            prompt = self._create_prompt_from_template(
                user_id, template, PromptType.USAGE_LIMIT,
                count=behavior.manual_entries_count
            )
            prompts.append(prompt)
        
        # Resume parsing limit prompt
        if behavior.feature_usage.get('resume_parsing', 0) >= 1:
            template = self.prompt_templates['resume_parsing_limit']
            prompt = self._create_prompt_from_template(
                user_id, template, PromptType.USAGE_LIMIT,
                limit=1
            )
            prompts.append(prompt)
        
        # Basic insights limit prompt
        if behavior.active_days >= 7:
            template = self.prompt_templates['basic_insights_limit']
            prompt = self._create_prompt_from_template(
                user_id, template, PromptType.FEATURE_PREVIEW
            )
            prompts.append(prompt)
        
        # Banking preview prompt
        if behavior.manual_entries_count >= 50:
            template = self.prompt_templates['banking_preview']
            prompt = self._create_prompt_from_template(
                user_id, template, PromptType.FEATURE_PREVIEW
            )
            prompts.append(prompt)
        
        # Advanced analytics prompt (for high-usage users)
        if behavior.manual_entries_count >= 100:
            template = self.prompt_templates['advanced_analytics']
            prompt = self._create_prompt_from_template(
                user_id, template, PromptType.PERSONALIZED_RECOMMENDATION
            )
            prompts.append(prompt)
        
        return prompts
    
    def _generate_mid_tier_prompts(self, user_id: str, behavior: UserBehavior) -> List[UpgradePrompt]:
        """Generate prompts for Mid-Tier users"""
        prompts = []
        
        # Career advancement prompt
        if behavior.feature_usage.get('resume_parsing', 0) >= 3:
            template = self.prompt_templates['career_advancement']
            prompt = self._create_prompt_from_template(
                user_id, template, PromptType.PERSONALIZED_RECOMMENDATION
            )
            prompts.append(prompt)
        
        # Advanced analytics prompt
        if behavior.manual_entries_count >= 200:
            template = self.prompt_templates['advanced_analytics']
            prompt = self._create_prompt_from_template(
                user_id, template, PromptType.PERSONALIZED_RECOMMENDATION
            )
            prompts.append(prompt)
        
        return prompts
    
    def _create_prompt_from_template(self, user_id: str, template: Dict[str, Any], 
                                   prompt_type: PromptType, **kwargs) -> UpgradePrompt:
        """Create an upgrade prompt from a template"""
        prompt_id = f"prompt_{int(datetime.utcnow().timestamp())}"
        
        # Format description with kwargs
        description = template['description'].format(**kwargs)
        current_limitation = template['current_limitation'].format(**kwargs)
        
        return UpgradePrompt(
            prompt_id=prompt_id,
            user_id=user_id,
            prompt_type=prompt_type,
            title=template['title'],
            description=description,
            benefit_description=template['benefit_description'],
            current_limitation=current_limitation,
            upgrade_feature=template['upgrade_feature'],
            upgrade_tier=template['upgrade_tier'],
            upgrade_price=template['upgrade_price'],
            cta_text=template['cta_text'],
            priority=template['priority'],
            triggered_by=f"{prompt_type.value}_{kwargs.get('count', kwargs.get('limit', 'general'))}",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
    
    def _filter_and_prioritize_prompts(self, prompts: List[UpgradePrompt], user_id: str) -> List[UpgradePrompt]:
        """Filter and prioritize prompts for a user"""
        try:
            # Remove duplicate prompts
            seen_triggers = set()
            unique_prompts = []
            
            for prompt in prompts:
                if prompt.triggered_by not in seen_triggers:
                    unique_prompts.append(prompt)
                    seen_triggers.add(prompt.triggered_by)
            
            # Sort by priority
            priority_order = {PromptPriority.HIGH: 3, PromptPriority.MEDIUM: 2, PromptPriority.LOW: 1}
            unique_prompts.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=True)
            
            # Limit to top 3 prompts
            return unique_prompts[:3]
            
        except Exception as e:
            self.logger.error(f"Error filtering prompts for user {user_id}: {e}")
            return prompts
    
    def _get_user_behavior(self, user_id: str) -> UserBehavior:
        """Get or create user behavior data"""
        try:
            if user_id not in self.user_behaviors:
                # Create default behavior data
                self.user_behaviors[user_id] = UserBehavior(
                    user_id=user_id,
                    feature_usage={
                        'manual_entries': 0,
                        'resume_parsing': 0,
                        'budget_creation': 0,
                        'insights_viewed': 0
                    },
                    manual_entries_count=0,
                    active_days=0,
                    last_activity=datetime.utcnow(),
                    tier_upgrade_attempts=0,
                    feature_requests=[]
                )
            
            return self.user_behaviors[user_id]
            
        except Exception as e:
            self.logger.error(f"Error getting user behavior for user {user_id}: {e}")
            return UserBehavior(
                user_id=user_id,
                feature_usage={},
                manual_entries_count=0,
                active_days=0,
                last_activity=datetime.utcnow(),
                tier_upgrade_attempts=0,
                feature_requests=[]
            )
    
    def get_user_prompts(self, user_id: str, include_dismissed: bool = False) -> List[UpgradePrompt]:
        """Get upgrade prompts for a user"""
        try:
            prompts = self.upgrade_prompts.get(user_id, [])
            
            if not include_dismissed:
                prompts = [p for p in prompts if not p.dismissed]
            
            # Filter expired prompts
            current_time = datetime.utcnow()
            active_prompts = [p for p in prompts if p.expires_at is None or p.expires_at > current_time]
            
            # Sort by priority and creation date
            priority_order = {PromptPriority.HIGH: 3, PromptPriority.MEDIUM: 2, PromptPriority.LOW: 1}
            active_prompts.sort(key=lambda x: (priority_order.get(x.priority, 0), x.created_at), reverse=True)
            
            return active_prompts
            
        except Exception as e:
            self.logger.error(f"Error getting user prompts for user {user_id}: {e}")
            return []
    
    def dismiss_prompt(self, user_id: str, prompt_id: str) -> bool:
        """Dismiss an upgrade prompt"""
        try:
            if user_id in self.upgrade_prompts:
                for prompt in self.upgrade_prompts[user_id]:
                    if prompt.prompt_id == prompt_id:
                        prompt.dismissed = True
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error dismissing prompt {prompt_id} for user {user_id}: {e}")
            return False
    
    def track_prompt_click(self, user_id: str, prompt_id: str) -> bool:
        """Track when a user clicks on an upgrade prompt"""
        try:
            if user_id in self.upgrade_prompts:
                for prompt in self.upgrade_prompts[user_id]:
                    if prompt.prompt_id == prompt_id:
                        prompt.clicked = True
                        
                        # Update user behavior
                        behavior = self._get_user_behavior(user_id)
                        behavior.tier_upgrade_attempts += 1
                        
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error tracking prompt click for prompt {prompt_id}, user {user_id}: {e}")
            return False
    
    def update_user_behavior(self, user_id: str, behavior_data: Dict[str, Any]):
        """Update user behavior data"""
        try:
            behavior = self._get_user_behavior(user_id)
            
            # Update behavior data
            if 'manual_entries_count' in behavior_data:
                behavior.manual_entries_count = behavior_data['manual_entries_count']
            
            if 'active_days' in behavior_data:
                behavior.active_days = behavior_data['active_days']
            
            if 'feature_usage' in behavior_data:
                behavior.feature_usage.update(behavior_data['feature_usage'])
            
            if 'last_activity' in behavior_data:
                behavior.last_activity = behavior_data['last_activity']
            
            # Store updated behavior
            self.user_behaviors[user_id] = behavior
            
        except Exception as e:
            self.logger.error(f"Error updating user behavior for user {user_id}: {e}")
    
    def get_prompt_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics for upgrade prompts"""
        try:
            prompts = self.upgrade_prompts.get(user_id, [])
            
            total_prompts = len(prompts)
            dismissed_prompts = len([p for p in prompts if p.dismissed])
            clicked_prompts = len([p for p in prompts if p.clicked])
            
            # Calculate conversion rate
            conversion_rate = (clicked_prompts / total_prompts * 100) if total_prompts > 0 else 0
            
            # Get prompt performance by type
            prompt_performance = {}
            for prompt in prompts:
                prompt_type = prompt.prompt_type.value
                if prompt_type not in prompt_performance:
                    prompt_performance[prompt_type] = {
                        'total': 0,
                        'clicked': 0,
                        'dismissed': 0
                    }
                
                prompt_performance[prompt_type]['total'] += 1
                if prompt.clicked:
                    prompt_performance[prompt_type]['clicked'] += 1
                if prompt.dismissed:
                    prompt_performance[prompt_type]['dismissed'] += 1
            
            return {
                'total_prompts': total_prompts,
                'dismissed_prompts': dismissed_prompts,
                'clicked_prompts': clicked_prompts,
                'conversion_rate': conversion_rate,
                'prompt_performance': prompt_performance
            }
            
        except Exception as e:
            self.logger.error(f"Error getting prompt analytics for user {user_id}: {e}")
            return {}
    
    def create_custom_prompt(self, user_id: str, prompt_data: Dict[str, Any]) -> Optional[UpgradePrompt]:
        """Create a custom upgrade prompt"""
        try:
            prompt = UpgradePrompt(
                prompt_id=f"custom_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                prompt_type=PromptType.PERSONALIZED_RECOMMENDATION,
                title=prompt_data['title'],
                description=prompt_data['description'],
                benefit_description=prompt_data['benefit_description'],
                current_limitation=prompt_data['current_limitation'],
                upgrade_feature=prompt_data['upgrade_feature'],
                upgrade_tier=prompt_data['upgrade_tier'],
                upgrade_price=prompt_data['upgrade_price'],
                cta_text=prompt_data['cta_text'],
                priority=PromptPriority(prompt_data.get('priority', 'medium')),
                triggered_by='custom',
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=prompt_data.get('expiry_days', 30))
            )
            
            # Store prompt
            if user_id not in self.upgrade_prompts:
                self.upgrade_prompts[user_id] = []
            self.upgrade_prompts[user_id].append(prompt)
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"Error creating custom prompt for user {user_id}: {e}")
            return None 