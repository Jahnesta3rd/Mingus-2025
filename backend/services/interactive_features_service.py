"""
Interactive Features Service

This module provides interactive features for the Budget tier dashboard,
including goal setting and tracking, budget creation and monitoring,
feature comparison tooltips, upgrade benefits highlighting, limited-time
upgrade offers, usage-based upgrade suggestions, and social proof.
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import random

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.services.basic_expense_tracking_service import BasicExpenseTrackingService
from backend.services.subscription_tier_service import SubscriptionTierService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class GoalType(Enum):
    """Types of financial goals"""
    SAVINGS = "savings"
    DEBT_PAYOFF = "debt_payoff"
    EMERGENCY_FUND = "emergency_fund"
    INVESTMENT = "investment"
    PURCHASE = "purchase"
    TRAVEL = "travel"
    EDUCATION = "education"


class GoalStatus(Enum):
    """Goal status types"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class BudgetStatus(Enum):
    """Budget status types"""
    UNDER_BUDGET = "under_budget"
    ON_TRACK = "on_track"
    OVER_BUDGET = "over_budget"
    WARNING = "warning"


@dataclass
class FinancialGoal:
    """Financial goal data structure"""
    goal_id: str
    user_id: str
    goal_type: GoalType
    title: str
    description: str
    target_amount: float
    current_amount: float
    target_date: date
    status: GoalStatus
    created_at: datetime
    updated_at: datetime
    monthly_contribution: float
    progress_percentage: float


@dataclass
class Budget:
    """Budget data structure"""
    budget_id: str
    user_id: str
    category: str
    amount: float
    spent: float
    remaining: float
    status: BudgetStatus
    created_at: datetime
    updated_at: datetime
    monthly_reset: bool
    alert_threshold: float  # Percentage for warnings


@dataclass
class FeatureComparison:
    """Feature comparison data structure"""
    feature_name: str
    budget_tier: Dict[str, Any]
    mid_tier: Dict[str, Any]
    professional: Dict[str, Any]
    description: str
    benefit_highlight: str


@dataclass
class UpgradeBenefit:
    """Upgrade benefit data structure"""
    benefit_id: str
    title: str
    description: str
    icon: str
    impact_score: float
    time_savings: str
    cost_savings: float
    tier: str  # 'mid_tier', 'professional'


@dataclass
class LimitedTimeOffer:
    """Limited time upgrade offer data structure"""
    offer_id: str
    title: str
    description: str
    original_price: float
    discounted_price: float
    discount_percentage: int
    expires_at: datetime
    features_included: List[str]
    urgency_level: str  # 'low', 'medium', 'high'
    remaining_time: str


@dataclass
class UsageBasedSuggestion:
    """Usage-based upgrade suggestion data structure"""
    suggestion_id: str
    trigger_type: str  # 'manual_entries', 'resume_parsing', 'insights_viewed'
    current_usage: int
    usage_limit: int
    suggestion_title: str
    suggestion_description: str
    upgrade_tier: str
    upgrade_price: float
    time_saved: str
    benefit_description: str


@dataclass
class SocialProof:
    """Social proof data structure"""
    proof_id: str
    user_type: str  # 'recent_upgrade', 'success_story', 'testimonial'
    user_name: str
    user_avatar: str
    user_location: str
    story_title: str
    story_description: str
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    upgrade_tier: str
    time_since_upgrade: str
    rating: int  # 1-5 stars


class InteractiveFeaturesService:
    """Service for interactive features in Budget tier dashboard"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.expense_service = BasicExpenseTrackingService(db_session)
        self.tier_service = SubscriptionTierService(db_session)
        
        # Mock data storage (in production, this would be database tables)
        self.financial_goals: Dict[str, List[FinancialGoal]] = {}
        self.budgets: Dict[str, List[Budget]] = {}
        self.feature_comparisons = self._initialize_feature_comparisons()
        self.upgrade_benefits = self._initialize_upgrade_benefits()
        self.limited_time_offers = self._initialize_limited_time_offers()
        self.social_proof = self._initialize_social_proof()
    
    def _initialize_feature_comparisons(self) -> List[FeatureComparison]:
        """Initialize feature comparison data"""
        return [
            FeatureComparison(
                feature_name="Bank Account Linking",
                budget_tier={"available": False, "limit": 0, "description": "Manual entry only"},
                mid_tier={"available": True, "limit": 2, "description": "Connect up to 2 accounts"},
                professional={"available": True, "limit": -1, "description": "Unlimited accounts"},
                description="Automatically import transactions from your bank accounts",
                benefit_highlight="Save 2-3 hours per month on manual data entry"
            ),
            FeatureComparison(
                feature_name="Transaction Categorization",
                budget_tier={"available": False, "limit": 0, "description": "Manual categorization"},
                mid_tier={"available": True, "limit": -1, "description": "AI-powered categorization"},
                professional={"available": True, "limit": -1, "description": "Advanced AI with learning"},
                description="Automatically categorize transactions with AI",
                benefit_highlight="Accurate categorization without manual work"
            ),
            FeatureComparison(
                feature_name="Financial Insights",
                budget_tier={"available": True, "limit": 5, "description": "Basic insights"},
                mid_tier={"available": True, "limit": 50, "description": "Advanced insights"},
                professional={"available": True, "limit": -1, "description": "Unlimited insights"},
                description="Get personalized financial insights and recommendations",
                benefit_highlight="Make better financial decisions with data-driven advice"
            ),
            FeatureComparison(
                feature_name="Resume Parsing",
                budget_tier={"available": True, "limit": 1, "description": "1 per month"},
                mid_tier={"available": True, "limit": 5, "description": "5 per month"},
                professional={"available": True, "limit": -1, "description": "Unlimited"},
                description="Parse resumes for career insights and job matching",
                benefit_highlight="Unlimited career advancement tools"
            ),
            FeatureComparison(
                feature_name="Cash Flow Forecasting",
                budget_tier={"available": False, "limit": 0, "description": "Not available"},
                mid_tier={"available": True, "limit": 6, "description": "6-month forecast"},
                professional={"available": True, "limit": 12, "description": "12-month forecast"},
                description="Predict future cash flow and plan accordingly",
                benefit_highlight="Plan your financial future with confidence"
            ),
            FeatureComparison(
                feature_name="Investment Analysis",
                budget_tier={"available": False, "limit": 0, "description": "Not available"},
                mid_tier={"available": False, "limit": 0, "description": "Not available"},
                professional={"available": True, "limit": -1, "description": "Full analysis"},
                description="Portfolio analysis and investment recommendations",
                benefit_highlight="Optimize your investment strategy"
            )
        ]
    
    def _initialize_upgrade_benefits(self) -> List[UpgradeBenefit]:
        """Initialize upgrade benefits data"""
        return [
            UpgradeBenefit(
                benefit_id="time_savings",
                title="Save 10+ Hours Monthly",
                description="Automate manual tasks and focus on what matters",
                icon="fas fa-clock",
                impact_score=0.9,
                time_savings="10+ hours/month",
                cost_savings=0,
                tier="mid_tier"
            ),
            UpgradeBenefit(
                benefit_id="accurate_categorization",
                title="99% Accurate Categorization",
                description="AI-powered categorization learns your spending patterns",
                icon="fas fa-brain",
                impact_score=0.8,
                time_savings="2 hours/month",
                cost_savings=0,
                tier="mid_tier"
            ),
            UpgradeBenefit(
                benefit_id="real_time_insights",
                title="Real-time Financial Insights",
                description="Get instant insights as transactions happen",
                icon="fas fa-chart-line",
                impact_score=0.85,
                time_savings="1 hour/month",
                cost_savings=0,
                tier="mid_tier"
            ),
            UpgradeBenefit(
                benefit_id="advanced_analytics",
                title="Advanced Analytics & Forecasting",
                description="Professional-grade financial planning tools",
                icon="fas fa-chart-bar",
                impact_score=0.95,
                time_savings="5 hours/month",
                cost_savings=500,
                tier="professional"
            ),
            UpgradeBenefit(
                benefit_id="investment_analysis",
                title="Investment Portfolio Analysis",
                description="Optimize your investment strategy with AI",
                icon="fas fa-chart-pie",
                impact_score=0.9,
                time_savings="3 hours/month",
                cost_savings=1000,
                tier="professional"
            ),
            UpgradeBenefit(
                benefit_id="unlimited_access",
                title="Unlimited Access to All Features",
                description="No limits on any feature or functionality",
                icon="fas fa-infinity",
                impact_score=0.7,
                time_savings="2 hours/month",
                cost_savings=0,
                tier="professional"
            )
        ]
    
    def _initialize_limited_time_offers(self) -> List[LimitedTimeOffer]:
        """Initialize limited time offers"""
        return [
            LimitedTimeOffer(
                offer_id="mid_tier_launch",
                title="Mid-Tier Launch Special",
                description="Get 50% off your first 3 months of Mid-Tier",
                original_price=35.0,
                discounted_price=17.50,
                discount_percentage=50,
                expires_at=datetime.utcnow() + timedelta(days=7),
                features_included=[
                    "Bank Account Linking (2 accounts)",
                    "AI-Powered Categorization",
                    "Advanced Insights (50/month)",
                    "Resume Parsing (5/month)"
                ],
                urgency_level="high",
                remaining_time="7 days"
            ),
            LimitedTimeOffer(
                offer_id="professional_trial",
                title="Professional Trial Upgrade",
                description="Try Professional features for 7 days, then 30% off",
                original_price=75.0,
                discounted_price=52.50,
                discount_percentage=30,
                expires_at=datetime.utcnow() + timedelta(days=3),
                features_included=[
                    "Unlimited Bank Accounts",
                    "12-Month Cash Flow Forecasting",
                    "Investment Analysis",
                    "Unlimited Everything"
                ],
                urgency_level="medium",
                remaining_time="3 days"
            )
        ]
    
    def _initialize_social_proof(self) -> List[SocialProof]:
        """Initialize social proof data"""
        return [
            SocialProof(
                proof_id="sarah_mid_tier",
                user_type="recent_upgrade",
                user_name="Sarah M.",
                user_avatar="https://via.placeholder.com/50/4CAF50/FFFFFF?text=S",
                user_location="Austin, TX",
                story_title="Saved 15 hours monthly with Mid-Tier",
                story_description="I was spending hours manually entering transactions. Mid-Tier's bank linking feature changed everything!",
                before_metrics={"manual_entries": 120, "time_spent": "15 hours/month"},
                after_metrics={"manual_entries": 5, "time_spent": "30 minutes/month"},
                upgrade_tier="mid_tier",
                time_since_upgrade="2 months ago",
                rating=5
            ),
            SocialProof(
                proof_id="mike_professional",
                user_type="success_story",
                user_name="Mike R.",
                user_avatar="https://via.placeholder.com/50/2196F3/FFFFFF?text=M",
                user_location="Seattle, WA",
                story_title="Built $50K emergency fund with Professional",
                story_description="The cash flow forecasting helped me plan my savings perfectly. I reached my goal 3 months early!",
                before_metrics={"emergency_fund": 5000, "savings_rate": "10%"},
                after_metrics={"emergency_fund": 50000, "savings_rate": "25%"},
                upgrade_tier="professional",
                time_since_upgrade="6 months ago",
                rating=5
            ),
            SocialProof(
                proof_id="jennifer_budget",
                user_type="testimonial",
                user_name="Jennifer L.",
                user_avatar="https://via.placeholder.com/50/FF9800/FFFFFF?text=J",
                user_location="Denver, CO",
                story_title="Budget Tier helped me get started",
                story_description="The manual entry and basic insights helped me understand my spending. Ready to upgrade to Mid-Tier!",
                before_metrics={"tracking": "none", "insights": 0},
                after_metrics={"tracking": "daily", "insights": 15},
                upgrade_tier="budget",
                time_since_upgrade="1 month ago",
                rating=4
            )
        ]
    
    def create_financial_goal(self, user_id: str, goal_data: Dict[str, Any]) -> Optional[FinancialGoal]:
        """Create a new financial goal for a user"""
        try:
            # Validate goal data
            if not self._validate_goal_data(goal_data):
                raise ValueError("Invalid goal data")
            
            # Create goal
            goal = FinancialGoal(
                goal_id=f"goal_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                goal_type=GoalType(goal_data['goal_type']),
                title=goal_data['title'],
                description=goal_data.get('description', ''),
                target_amount=float(goal_data['target_amount']),
                current_amount=float(goal_data.get('current_amount', 0)),
                target_date=goal_data['target_date'],
                status=GoalStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                monthly_contribution=float(goal_data.get('monthly_contribution', 0)),
                progress_percentage=0.0
            )
            
            # Calculate progress percentage
            goal.progress_percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
            
            # Store goal
            if user_id not in self.financial_goals:
                self.financial_goals[user_id] = []
            self.financial_goals[user_id].append(goal)
            
            self.logger.info(f"Created financial goal for user {user_id}: {goal.title}")
            return goal
            
        except Exception as e:
            self.logger.error(f"Error creating financial goal for user {user_id}: {e}")
            return None
    
    def _validate_goal_data(self, goal_data: Dict[str, Any]) -> bool:
        """Validate goal data"""
        required_fields = ['goal_type', 'title', 'target_amount', 'target_date']
        
        for field in required_fields:
            if field not in goal_data:
                return False
        
        try:
            GoalType(goal_data['goal_type'])
            float(goal_data['target_amount'])
            datetime.strptime(goal_data['target_date'], '%Y-%m-%d')
        except (ValueError, KeyError):
            return False
        
        return True
    
    def get_user_goals(self, user_id: str) -> List[FinancialGoal]:
        """Get all financial goals for a user"""
        try:
            goals = self.financial_goals.get(user_id, [])
            
            # Update progress for each goal
            for goal in goals:
                self._update_goal_progress(goal)
            
            return goals
            
        except Exception as e:
            self.logger.error(f"Error getting goals for user {user_id}: {e}")
            return []
    
    def _update_goal_progress(self, goal: FinancialGoal):
        """Update goal progress and status"""
        try:
            # Calculate progress percentage
            goal.progress_percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
            
            # Update status based on progress
            if goal.progress_percentage >= 100:
                goal.status = GoalStatus.COMPLETED
            elif goal.target_date < date.today():
                goal.status = GoalStatus.PAUSED
            
            goal.updated_at = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Error updating goal progress: {e}")
    
    def update_goal_progress(self, user_id: str, goal_id: str, amount: float) -> bool:
        """Update goal progress with a contribution"""
        try:
            goals = self.financial_goals.get(user_id, [])
            
            for goal in goals:
                if goal.goal_id == goal_id:
                    goal.current_amount += amount
                    self._update_goal_progress(goal)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating goal progress for user {user_id}: {e}")
            return False
    
    def create_budget(self, user_id: str, budget_data: Dict[str, Any]) -> Optional[Budget]:
        """Create a new budget for a user"""
        try:
            # Validate budget data
            if not self._validate_budget_data(budget_data):
                raise ValueError("Invalid budget data")
            
            # Create budget
            budget = Budget(
                budget_id=f"budget_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                category=budget_data['category'],
                amount=float(budget_data['amount']),
                spent=0.0,
                remaining=float(budget_data['amount']),
                status=BudgetStatus.UNDER_BUDGET,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                monthly_reset=budget_data.get('monthly_reset', True),
                alert_threshold=float(budget_data.get('alert_threshold', 80))
            )
            
            # Store budget
            if user_id not in self.budgets:
                self.budgets[user_id] = []
            self.budgets[user_id].append(budget)
            
            self.logger.info(f"Created budget for user {user_id}: {budget.category}")
            return budget
            
        except Exception as e:
            self.logger.error(f"Error creating budget for user {user_id}: {e}")
            return None
    
    def _validate_budget_data(self, budget_data: Dict[str, Any]) -> bool:
        """Validate budget data"""
        required_fields = ['category', 'amount']
        
        for field in required_fields:
            if field not in budget_data:
                return False
        
        try:
            float(budget_data['amount'])
        except ValueError:
            return False
        
        return True
    
    def get_user_budgets(self, user_id: str) -> List[Budget]:
        """Get all budgets for a user"""
        try:
            budgets = self.budgets.get(user_id, [])
            
            # Update budget status based on spending
            for budget in budgets:
                self._update_budget_status(budget, user_id)
            
            return budgets
            
        except Exception as e:
            self.logger.error(f"Error getting budgets for user {user_id}: {e}")
            return []
    
    def _update_budget_status(self, budget: Budget, user_id: str):
        """Update budget status based on current spending"""
        try:
            # Get current month spending for this category
            entries = self.expense_service.manual_entries.get(user_id, [])
            current_month = date.today().replace(day=1)
            
            category_spending = sum(
                e.amount for e in entries 
                if e.transaction_type.value == 'expense' 
                and e.category == budget.category 
                and e.date >= current_month
            )
            
            budget.spent = category_spending
            budget.remaining = budget.amount - category_spending
            budget.updated_at = datetime.utcnow()
            
            # Update status
            percentage_used = (category_spending / budget.amount * 100) if budget.amount > 0 else 0
            
            if percentage_used >= 100:
                budget.status = BudgetStatus.OVER_BUDGET
            elif percentage_used >= budget.alert_threshold:
                budget.status = BudgetStatus.WARNING
            elif percentage_used >= 80:
                budget.status = BudgetStatus.ON_TRACK
            else:
                budget.status = BudgetStatus.UNDER_BUDGET
                
        except Exception as e:
            self.logger.error(f"Error updating budget status: {e}")
    
    def get_feature_comparisons(self) -> List[FeatureComparison]:
        """Get feature comparison data"""
        return self.feature_comparisons
    
    def get_upgrade_benefits(self, tier: str = None) -> List[UpgradeBenefit]:
        """Get upgrade benefits, optionally filtered by tier"""
        benefits = self.upgrade_benefits
        
        if tier:
            benefits = [b for b in benefits if b.tier == tier]
        
        return benefits
    
    def get_active_limited_time_offers(self) -> List[LimitedTimeOffer]:
        """Get active limited time offers"""
        current_time = datetime.utcnow()
        active_offers = [offer for offer in self.limited_time_offers if offer.expires_at > current_time]
        
        # Update remaining time
        for offer in active_offers:
            time_diff = offer.expires_at - current_time
            if time_diff.days > 0:
                offer.remaining_time = f"{time_diff.days} days"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                offer.remaining_time = f"{hours} hours"
            else:
                offer.remaining_time = "Less than 1 hour"
        
        return active_offers
    
    def get_usage_based_suggestions(self, user_id: str) -> List[UsageBasedSuggestion]:
        """Get usage-based upgrade suggestions"""
        try:
            suggestions = []
            
            # Get user's current usage
            entries = self.expense_service.manual_entries.get(user_id, [])
            manual_entries_count = len(entries)
            
            # Manual entries suggestion
            if manual_entries_count >= 30:
                suggestions.append(UsageBasedSuggestion(
                    suggestion_id=f"manual_entries_{user_id}",
                    trigger_type="manual_entries",
                    current_usage=manual_entries_count,
                    usage_limit=50,
                    suggestion_title="Tired of Manual Entry?",
                    suggestion_description=f"You've entered {manual_entries_count} transactions manually. Upgrade to Mid-Tier for automatic bank imports.",
                    upgrade_tier="mid_tier",
                    upgrade_price=35.0,
                    time_saved="2-3 hours/month",
                    benefit_description="Connect your bank accounts and import transactions automatically"
                ))
            
            # Resume parsing suggestion (if used)
            # This would need integration with resume parsing service
            if manual_entries_count >= 50:
                suggestions.append(UsageBasedSuggestion(
                    suggestion_id=f"insights_{user_id}",
                    trigger_type="insights_viewed",
                    current_usage=manual_entries_count,
                    usage_limit=100,
                    suggestion_title="Get Deeper Insights",
                    suggestion_description="You're actively tracking your finances. Upgrade for advanced AI-powered insights.",
                    upgrade_tier="mid_tier",
                    upgrade_price=35.0,
                    time_saved="1 hour/month",
                    benefit_description="Get personalized financial recommendations and advanced analytics"
                ))
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting usage-based suggestions for user {user_id}: {e}")
            return []
    
    def get_social_proof(self, user_type: str = None, limit: int = 3) -> List[SocialProof]:
        """Get social proof data, optionally filtered by user type"""
        proof = self.social_proof
        
        if user_type:
            proof = [p for p in proof if p.user_type == user_type]
        
        # Randomize order and limit results
        random.shuffle(proof)
        return proof[:limit]
    
    def get_goal_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized goal recommendations"""
        try:
            entries = self.expense_service.manual_entries.get(user_id, [])
            expenses = [e for e in entries if e.transaction_type.value == 'expense']
            
            if not expenses:
                return []
            
            recommendations = []
            
            # Calculate monthly expenses
            monthly_expenses = self._calculate_monthly_expenses(expenses)
            
            # Emergency fund recommendation
            if monthly_expenses > 0:
                emergency_fund_target = monthly_expenses * 6
                recommendations.append({
                    'goal_type': 'emergency_fund',
                    'title': 'Build Emergency Fund',
                    'description': f'Save ${emergency_fund_target:.0f} for 6 months of expenses',
                    'target_amount': emergency_fund_target,
                    'monthly_contribution': emergency_fund_target / 12,
                    'priority': 'high'
                })
            
            # Debt payoff recommendation (if applicable)
            # This would need actual debt data
            if monthly_expenses > 2000:
                recommendations.append({
                    'goal_type': 'debt_payoff',
                    'title': 'Accelerate Debt Payoff',
                    'description': 'Increase debt payments to save on interest',
                    'target_amount': 5000,
                    'monthly_contribution': 500,
                    'priority': 'medium'
                })
            
            # Savings goal recommendation
            if monthly_expenses > 0:
                savings_target = monthly_expenses * 0.2 * 12  # 20% of monthly expenses for 1 year
                recommendations.append({
                    'goal_type': 'savings',
                    'title': 'Build Savings',
                    'description': f'Save ${savings_target:.0f} for future goals',
                    'target_amount': savings_target,
                    'monthly_contribution': savings_target / 12,
                    'priority': 'medium'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting goal recommendations for user {user_id}: {e}")
            return []
    
    def _calculate_monthly_expenses(self, expenses: List) -> float:
        """Calculate average monthly expenses"""
        try:
            if not expenses:
                return 0
            
            # Group by month
            monthly_expenses = {}
            for expense in expenses:
                month_key = expense.date.replace(day=1)
                if month_key not in monthly_expenses:
                    monthly_expenses[month_key] = 0
                monthly_expenses[month_key] += expense.amount
            
            if not monthly_expenses:
                return 0
            
            return sum(monthly_expenses.values()) / len(monthly_expenses)
            
        except Exception as e:
            self.logger.error(f"Error calculating monthly expenses: {e}")
            return 0
    
    def get_interactive_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive interactive dashboard data"""
        try:
            return {
                'goals': self.get_user_goals(user_id),
                'budgets': self.get_user_budgets(user_id),
                'feature_comparisons': self.get_feature_comparisons(),
                'upgrade_benefits': self.get_upgrade_benefits(),
                'limited_time_offers': self.get_active_limited_time_offers(),
                'usage_suggestions': self.get_usage_based_suggestions(user_id),
                'social_proof': self.get_social_proof(),
                'goal_recommendations': self.get_goal_recommendations(user_id),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting interactive dashboard data for user {user_id}: {e}")
            return {} 