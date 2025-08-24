"""
Budget Tier Dashboard Service

This module provides dashboard features for Budget tier subscription users,
including manual entry interface, banking feature previews, upgrade prompts,
basic expense tracking and budgeting, and resume parsing with 1 limit per month.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from collections import defaultdict, Counter
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text, case, cast, Float
from sqlalchemy.exc import IntegrityError

from backend.models.user_models import User
from backend.models.analytics import SpendingCategory, SpendingPattern
from backend.models.subscription import SubscriptionTier
from backend.services.feature_access_service import FeatureAccessService
from backend.services.resume_parsing_service import ResumeParsingService
from backend.services.basic_expense_tracking_service import BasicExpenseTrackingService
from backend.services.upgrade_prompts_service import UpgradePromptsService
from backend.services.intelligent_insights_service import IntelligentInsightsService
from backend.services.interactive_features_service import InteractiveFeaturesService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class DashboardWidgetType(Enum):
    """Dashboard widget types for Budget tier"""
    MANUAL_ENTRY = "manual_entry"
    BANKING_PREVIEW = "banking_preview"
    UPGRADE_PROMPTS = "upgrade_prompts"
    EXPENSE_TRACKING = "expense_tracking"
    BUDGET_OVERVIEW = "budget_overview"
    RESUME_PARSING = "resume_parsing"
    BASIC_INSIGHTS = "basic_insights"
    FEATURE_PREVIEWS = "feature_previews"
    INTELLIGENT_INSIGHTS = "intelligent_insights"
    INTERACTIVE_FEATURES = "interactive_features"


@dataclass
class ManualEntryTransaction:
    """Manual entry transaction data structure"""
    id: str
    user_id: str
    amount: float
    description: str
    category: str
    date: date
    transaction_type: str  # 'income', 'expense'
    created_at: datetime
    updated_at: datetime


@dataclass
class BankingFeaturePreview:
    """Banking feature preview data structure"""
    feature_name: str
    description: str
    preview_data: Dict[str, Any]
    upgrade_benefit: str
    trial_available: bool
    trial_duration_days: int


@dataclass
class UpgradePrompt:
    """Upgrade prompt data structure"""
    prompt_id: str
    title: str
    description: str
    benefit_description: str
    current_limitation: str
    upgrade_feature: str
    upgrade_tier: str
    upgrade_price: float
    cta_text: str
    priority: str  # 'high', 'medium', 'low'


@dataclass
class BasicExpenseSummary:
    """Basic expense summary data structure"""
    total_expenses: float
    total_income: float
    net_amount: float
    expense_categories: Dict[str, float]
    monthly_trend: str  # 'increasing', 'decreasing', 'stable'
    top_expense_category: str
    budget_status: str  # 'under_budget', 'over_budget', 'on_track'


@dataclass
class ResumeParsingStatus:
    """Resume parsing status data structure"""
    parsing_used_this_month: bool
    last_parsed_date: Optional[date]
    parsing_limit: int
    parsing_remaining: int
    parsed_resume_count: int
    next_reset_date: date


@dataclass
class BasicInsight:
    """Basic insight data structure"""
    insight_id: str
    title: str
    description: str
    category: str
    impact_score: float
    actionable: bool
    recommendation: str
    generated_at: datetime


class BudgetTierDashboardService:
    """Budget tier dashboard service with basic features and upgrade prompts"""
    
    def __init__(self, db_session: Session, feature_access_service: FeatureAccessService):
        self.db = db_session
        self.feature_service = feature_access_service
        self.resume_service = ResumeParsingService(db_session)
        self.expense_service = BasicExpenseTrackingService(db_session)
        self.upgrade_service = UpgradePromptsService(db_session)
        self.intelligent_insights_service = IntelligentInsightsService(db_session)
        self.interactive_features_service = InteractiveFeaturesService(db_session)
        
        # Cache for dashboard data
        self.dashboard_cache = {}
        self.cache_ttl = 600  # 10 minutes
        
    def get_budget_tier_dashboard(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive Budget tier dashboard data
        
        Args:
            user_id: User ID to get dashboard data for
            
        Returns:
            Complete Budget tier dashboard data
        """
        try:
            # Verify Budget tier access
            if not self._verify_budget_tier_access(user_id):
                return self._get_error_data("Access denied")
            
            # Get all dashboard components
            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'tier': 'budget',
                'manual_entry': self._get_manual_entry_interface(user_id),
                'banking_preview': self._get_banking_feature_previews(user_id),
                'upgrade_prompts': self._get_upgrade_prompts(user_id),
                'expense_tracking': self._get_basic_expense_tracking(user_id),
                'budget_overview': self._get_budget_overview(user_id),
                'resume_parsing': self._get_resume_parsing_status(user_id),
                'basic_insights': self._get_basic_insights(user_id),
                'feature_previews': self._get_feature_previews(user_id),
                'intelligent_insights': self._get_intelligent_insights(user_id),
                'interactive_features': self._get_interactive_features(user_id)
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating Budget tier dashboard for user {user_id}: {e}")
            return {'error': str(e)}
    
    def _verify_budget_tier_access(self, user_id: str) -> bool:
        """Verify user has Budget tier or higher access"""
        try:
            # Check if user has Budget tier or higher
            user_tier = self.feature_service.get_user_subscription_tier(user_id)
            return user_tier in ['budget', 'mid_tier', 'professional']
        except Exception as e:
            logger.error(f"Error verifying Budget tier access for user {user_id}: {e}")
            return False
    
    def _get_error_data(self, message: str) -> Dict[str, Any]:
        """Get error data for dashboard"""
        return {
            'error': 'access_denied',
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_manual_entry_interface(self, user_id: str) -> Dict[str, Any]:
        """Get manual entry interface data"""
        try:
            # Get recent manual entries
            recent_entries = self.expense_service.get_recent_manual_entries(user_id, limit=10)
            
            # Get entry statistics
            entry_stats = self.expense_service.get_manual_entry_statistics(user_id)
            
            return {
                'recent_entries': recent_entries,
                'entry_statistics': entry_stats,
                'categories_available': self._get_available_categories(),
                'entry_limits': {
                    'daily_entries': 50,
                    'monthly_entries': 500,
                    'entry_history_days': 90
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting manual entry interface for user {user_id}: {e}")
            return {}
    
    def _get_available_categories(self) -> List[str]:
        """Get available categories for manual entry"""
        return [
            'Food & Dining',
            'Transportation',
            'Housing',
            'Utilities',
            'Entertainment',
            'Shopping',
            'Healthcare',
            'Education',
            'Travel',
            'Other'
        ]
    
    def _get_banking_feature_previews(self, user_id: str) -> List[BankingFeaturePreview]:
        """Get banking feature previews to encourage upgrades"""
        try:
            previews = [
                BankingFeaturePreview(
                    feature_name="Real-time Account Balances",
                    description="See your account balances update in real-time across all your banks",
                    preview_data={
                        'sample_accounts': [
                            {'name': 'Chase Checking', 'balance': 2547.89, 'last_updated': '2 minutes ago'},
                            {'name': 'Wells Fargo Savings', 'balance': 12500.00, 'last_updated': '5 minutes ago'}
                        ],
                        'total_balance': 15047.89,
                        'balance_change': '+$125.50'
                    },
                    upgrade_benefit="Never worry about outdated balance information again",
                    trial_available=True,
                    trial_duration_days=7
                ),
                BankingFeaturePreview(
                    feature_name="Automatic Transaction Categorization",
                    description="AI-powered categorization of all your transactions automatically",
                    preview_data={
                        'sample_transactions': [
                            {'description': 'STARBUCKS', 'amount': -5.75, 'category': 'Food & Dining', 'confidence': 95},
                            {'description': 'SHELL OIL', 'amount': -45.20, 'category': 'Transportation', 'confidence': 98},
                            {'description': 'NETFLIX', 'amount': -15.99, 'category': 'Entertainment', 'confidence': 100}
                        ],
                        'categorization_accuracy': '98%',
                        'time_saved': '2 hours/month'
                    },
                    upgrade_benefit="Save hours of manual categorization every month",
                    trial_available=True,
                    trial_duration_days=7
                ),
                BankingFeaturePreview(
                    feature_name="Advanced Spending Insights",
                    description="Get detailed insights into your spending patterns and trends",
                    preview_data={
                        'insights': [
                            'You spend 23% more on dining out than the average user',
                            'Your transportation costs have increased 15% this month',
                            'You could save $127/month by reducing entertainment spending'
                        ],
                        'savings_potential': 127.00,
                        'trend_analysis': 'Monthly spending analysis'
                    },
                    upgrade_benefit="Discover hidden opportunities to save money",
                    trial_available=False,
                    trial_duration_days=0
                )
            ]
            
            return previews
            
        except Exception as e:
            logger.error(f"Error getting banking feature previews for user {user_id}: {e}")
            return []
    
    def _get_upgrade_prompts(self, user_id: str) -> List[UpgradePrompt]:
        """Get personalized upgrade prompts"""
        try:
            # Get user's usage patterns to create targeted prompts
            usage_patterns = self._analyze_user_usage_patterns(user_id)
            
            prompts = [
                UpgradePrompt(
                    prompt_id="manual_entry_frequency",
                    title="Tired of Manual Entry?",
                    description="You've entered 47 transactions this month manually. Connect your bank accounts for automatic transaction import.",
                    benefit_description="Save 2-3 hours per month on manual data entry",
                    current_limitation="Manual entry only - no automatic transaction import",
                    upgrade_feature="Bank Account Linking",
                    upgrade_tier="Mid-Tier",
                    upgrade_price=35.0,
                    cta_text="Upgrade to Mid-Tier",
                    priority="high"
                ),
                UpgradePrompt(
                    prompt_id="basic_insights_limit",
                    title="Get Deeper Financial Insights",
                    description="Unlock AI-powered insights and personalized recommendations for your financial health.",
                    benefit_description="Get personalized financial advice and optimization suggestions",
                    current_limitation="Basic insights only - no AI recommendations",
                    upgrade_feature="AI-Powered Insights",
                    upgrade_tier="Mid-Tier",
                    upgrade_price=35.0,
                    cta_text="Unlock AI Insights",
                    priority="medium"
                ),
                UpgradePrompt(
                    prompt_id="resume_parsing_limit",
                    title="Resume Parsing Limit Reached",
                    description="You've used your 1 resume parsing this month. Upgrade for unlimited parsing and advanced career insights.",
                    benefit_description="Unlimited resume parsing and career advancement tools",
                    current_limitation="1 resume parsing per month",
                    upgrade_feature="Unlimited Resume Parsing",
                    upgrade_tier="Mid-Tier",
                    upgrade_price=35.0,
                    cta_text="Get Unlimited Parsing",
                    priority="medium"
                ),
                UpgradePrompt(
                    prompt_id="advanced_analytics",
                    title="Advanced Financial Analytics",
                    description="Get cash flow forecasting, investment analysis, and comprehensive financial planning tools.",
                    benefit_description="Professional-grade financial planning and forecasting",
                    current_limitation="Basic expense tracking only",
                    upgrade_feature="Advanced Analytics",
                    upgrade_tier="Professional",
                    upgrade_price=75.0,
                    cta_text="Upgrade to Professional",
                    priority="low"
                )
            ]
            
            # Filter prompts based on user's specific usage patterns
            filtered_prompts = self._filter_prompts_by_usage(prompts, usage_patterns)
            
            return filtered_prompts[:3]  # Return top 3 most relevant prompts
            
        except Exception as e:
            logger.error(f"Error getting upgrade prompts for user {user_id}: {e}")
            return []
    
    def _analyze_user_usage_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's usage patterns for targeted upgrade prompts"""
        try:
            # Get user's manual entry frequency
            manual_entries = self.expense_service.get_manual_entry_statistics(user_id)
            
            # Get resume parsing usage
            resume_status = self._get_resume_parsing_status(user_id)
            
            # Get feature usage
            feature_usage = self.feature_service.get_user_feature_usage(user_id)
            
            return {
                'manual_entries_this_month': manual_entries.get('entries_this_month', 0),
                'resume_parsing_used': resume_status.get('parsing_used_this_month', False),
                'feature_usage': feature_usage,
                'active_days': manual_entries.get('active_days', 0),
                'total_entries': manual_entries.get('total_entries', 0)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing usage patterns for user {user_id}: {e}")
            return {}
    
    def _filter_prompts_by_usage(self, prompts: List[UpgradePrompt], usage_patterns: Dict[str, Any]) -> List[UpgradePrompt]:
        """Filter upgrade prompts based on user's usage patterns"""
        try:
            filtered_prompts = []
            
            for prompt in prompts:
                if prompt.prompt_id == "manual_entry_frequency":
                    if usage_patterns.get('manual_entries_this_month', 0) > 30:
                        filtered_prompts.append(prompt)
                        
                elif prompt.prompt_id == "basic_insights_limit":
                    if usage_patterns.get('active_days', 0) > 7:
                        filtered_prompts.append(prompt)
                        
                elif prompt.prompt_id == "resume_parsing_limit":
                    if usage_patterns.get('resume_parsing_used', False):
                        filtered_prompts.append(prompt)
                        
                elif prompt.prompt_id == "advanced_analytics":
                    if usage_patterns.get('total_entries', 0) > 100:
                        filtered_prompts.append(prompt)
            
            # Sort by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            filtered_prompts.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=True)
            
            return filtered_prompts
            
        except Exception as e:
            logger.error(f"Error filtering prompts by usage: {e}")
            return prompts
    
    def _get_basic_expense_tracking(self, user_id: str) -> Dict[str, Any]:
        """Get basic expense tracking data"""
        try:
            # Get expense summary
            expense_summary = self.expense_service.get_expense_summary(user_id)
            
            # Get recent transactions
            recent_transactions = self.expense_service.get_recent_transactions(user_id, limit=10)
            
            # Get category breakdown
            category_breakdown = self.expense_service.get_category_breakdown(user_id)
            
            return {
                'expense_summary': expense_summary,
                'recent_transactions': recent_transactions,
                'category_breakdown': category_breakdown,
                'tracking_limits': {
                    'max_transactions': 1000,
                    'max_categories': 20,
                    'history_days': 365
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting basic expense tracking for user {user_id}: {e}")
            return {}
    
    def _get_budget_overview(self, user_id: str) -> Dict[str, Any]:
        """Get budget overview data"""
        try:
            # Get budget information
            budget_info = self.expense_service.get_budget_overview(user_id)
            
            # Get spending vs budget comparison
            spending_vs_budget = self.expense_service.get_spending_vs_budget(user_id)
            
            # Get budget recommendations
            budget_recommendations = self.expense_service.get_budget_recommendations(user_id)
            
            return {
                'budget_info': budget_info,
                'spending_vs_budget': spending_vs_budget,
                'budget_recommendations': budget_recommendations,
                'budget_limits': {
                    'max_budgets': 5,
                    'budget_categories': 10,
                    'budget_history_months': 12
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting budget overview for user {user_id}: {e}")
            return {}
    
    def _get_resume_parsing_status(self, user_id: str) -> Dict[str, Any]:
        """Get resume parsing status and limits"""
        try:
            # Get parsing status from resume service
            parsing_status = self.resume_service.get_parsing_status(user_id)
            
            # Calculate remaining parsing for the month
            parsing_used = parsing_status.get('parsing_used_this_month', False)
            parsing_limit = 1  # Budget tier limit
            parsing_remaining = 0 if parsing_used else 1
            
            # Calculate next reset date (first day of next month)
            today = date.today()
            if today.month == 12:
                next_month = date(today.year + 1, 1, 1)
            else:
                next_month = date(today.year, today.month + 1, 1)
            
            return {
                'parsing_used_this_month': parsing_used,
                'last_parsed_date': parsing_status.get('last_parsed_date'),
                'parsing_limit': parsing_limit,
                'parsing_remaining': parsing_remaining,
                'parsed_resume_count': parsing_status.get('parsed_resume_count', 0),
                'next_reset_date': next_month.isoformat(),
                'upgrade_benefit': 'Unlimited resume parsing with advanced career insights'
            }
            
        except Exception as e:
            logger.error(f"Error getting resume parsing status for user {user_id}: {e}")
            return {}
    
    def _get_basic_insights(self, user_id: str) -> List[BasicInsight]:
        """Get basic insights for Budget tier users"""
        try:
            # Get basic insights from expense service
            insights = self.expense_service.get_basic_insights(user_id, limit=5)
            
            # Convert to BasicInsight format
            basic_insights = []
            for insight in insights:
                basic_insight = BasicInsight(
                    insight_id=insight.get('id', f"insight_{len(basic_insights)}"),
                    title=insight.get('title', 'Basic Insight'),
                    description=insight.get('description', ''),
                    category=insight.get('category', 'general'),
                    impact_score=insight.get('impact_score', 0.5),
                    actionable=insight.get('actionable', True),
                    recommendation=insight.get('recommendation', ''),
                    generated_at=datetime.utcnow()
                )
                basic_insights.append(basic_insight)
            
            return basic_insights
            
        except Exception as e:
            logger.error(f"Error getting basic insights for user {user_id}: {e}")
            return []
    
    def _get_feature_previews(self, user_id: str) -> Dict[str, Any]:
        """Get feature previews for Budget tier users"""
        try:
            previews = {
                'mid_tier_features': [
                    {
                        'feature': 'Bank Account Linking',
                        'description': 'Connect up to 2 bank accounts for automatic transaction import',
                        'benefit': 'Save hours of manual data entry',
                        'preview_available': True
                    },
                    {
                        'feature': 'AI-Powered Categorization',
                        'description': 'Automatic categorization of transactions with AI',
                        'benefit': 'Accurate categorization without manual work',
                        'preview_available': True
                    },
                    {
                        'feature': 'Advanced Insights',
                        'description': 'Get personalized financial insights and recommendations',
                        'benefit': 'Make better financial decisions with data-driven advice',
                        'preview_available': False
                    }
                ],
                'professional_features': [
                    {
                        'feature': 'Unlimited Bank Accounts',
                        'description': 'Connect unlimited bank accounts and institutions',
                        'benefit': 'Complete financial picture across all accounts',
                        'preview_available': False
                    },
                    {
                        'feature': 'Cash Flow Forecasting',
                        'description': '12-month cash flow projections with confidence intervals',
                        'benefit': 'Plan your financial future with confidence',
                        'preview_available': False
                    },
                    {
                        'feature': 'Investment Analysis',
                        'description': 'Portfolio analysis and investment recommendations',
                        'benefit': 'Optimize your investment strategy',
                        'preview_available': False
                    }
                ]
            }
            
            return previews
            
        except Exception as e:
            logger.error(f"Error getting feature previews for user {user_id}: {e}")
            return {}
    
    def get_dashboard_widget_data(self, user_id: str, widget_type: DashboardWidgetType) -> Dict[str, Any]:
        """Get data for a specific dashboard widget"""
        try:
            if widget_type == DashboardWidgetType.MANUAL_ENTRY:
                return self._get_manual_entry_interface(user_id)
            elif widget_type == DashboardWidgetType.BANKING_PREVIEW:
                return {'previews': self._get_banking_feature_previews(user_id)}
            elif widget_type == DashboardWidgetType.UPGRADE_PROMPTS:
                return {'prompts': self._get_upgrade_prompts(user_id)}
            elif widget_type == DashboardWidgetType.EXPENSE_TRACKING:
                return self._get_basic_expense_tracking(user_id)
            elif widget_type == DashboardWidgetType.BUDGET_OVERVIEW:
                return self._get_budget_overview(user_id)
            elif widget_type == DashboardWidgetType.RESUME_PARSING:
                return self._get_resume_parsing_status(user_id)
            elif widget_type == DashboardWidgetType.BASIC_INSIGHTS:
                return {'insights': self._get_basic_insights(user_id)}
            elif widget_type == DashboardWidgetType.FEATURE_PREVIEWS:
                return self._get_feature_previews(user_id)
            elif widget_type == DashboardWidgetType.INTELLIGENT_INSIGHTS:
                return self._get_intelligent_insights(user_id)
            elif widget_type == DashboardWidgetType.INTERACTIVE_FEATURES:
                return self._get_interactive_features(user_id)
            else:
                return {'error': 'Unknown widget type'}
                
        except Exception as e:
            logger.error(f"Error getting widget data for user {user_id}, widget {widget_type}: {e}")
            return {'error': str(e)}
    
    def _get_intelligent_insights(self, user_id: str) -> Dict[str, Any]:
        """Get intelligent insights for Budget tier users"""
        try:
            # Get intelligent insights from the service
            insights = self.intelligent_insights_service.get_intelligent_insights(user_id)
            
            if not insights:
                return {
                    'spending_trends': [],
                    'unusual_transactions': [],
                    'subscription_management': [],
                    'cash_flow_optimization': [],
                    'emergency_fund': None,
                    'debt_payoff': None,
                    'message': 'Add more transactions to get intelligent insights'
                }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting intelligent insights for user {user_id}: {e}")
            return {}
    
    def _get_interactive_features(self, user_id: str) -> Dict[str, Any]:
        """Get interactive features for Budget tier users"""
        try:
            # Get interactive features from the service
            interactive_data = self.interactive_features_service.get_interactive_dashboard_data(user_id)
            
            if not interactive_data:
                return {
                    'goals': [],
                    'budgets': [],
                    'feature_comparisons': [],
                    'upgrade_benefits': [],
                    'limited_time_offers': [],
                    'usage_suggestions': [],
                    'social_proof': [],
                    'goal_recommendations': [],
                    'message': 'Interactive features will be available once you start using the app'
                }
            
            return interactive_data
            
        except Exception as e:
            logger.error(f"Error getting interactive features for user {user_id}: {e}")
            return {} 