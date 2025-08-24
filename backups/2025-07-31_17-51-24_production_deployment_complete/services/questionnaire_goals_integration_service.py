"""
Questionnaire Goals Integration Service

This service integrates questionnaire data with the savings goals system,
automatically creating goals based on the key dates and amounts from the
initial questionnaire for users who have that capability.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from backend.models.mid_tier_models import SavingsGoal, SavingsGoalProgress
from backend.models.financial_questionnaire_submission import FinancialQuestionnaireSubmission
from backend.services.mid_tier_features_service import MidTierFeaturesService, GoalType, GoalStatus
from backend.services.subscription_tier_service import SubscriptionTierService, SubscriptionTier, FeatureType
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class QuestionnaireGoalType(Enum):
    """Types of goals that can be created from questionnaire data"""
    EMERGENCY_FUND = "emergency_fund"
    DEBT_PAYOFF = "debt_payoff"
    SAVINGS_GROWTH = "savings_growth"
    MAJOR_PURCHASE = "major_purchase"
    INVESTMENT_START = "investment_start"
    RETIREMENT_PLANNING = "retirement_planning"
    HOME_PURCHASE = "home_purchase"
    CUSTOM_GOAL = "custom_goal"


@dataclass
class QuestionnaireGoalData:
    """Data extracted from questionnaire for goal creation"""
    goal_type: QuestionnaireGoalType
    target_amount: float
    current_amount: float
    target_date: datetime
    priority: int
    description: str
    motivation: str
    monthly_target: float
    confidence_score: float  # How confident we are in this goal
    source_data: Dict[str, Any]  # Original questionnaire data used


@dataclass
class QuestionnaireGoalRecommendation:
    """Goal recommendation based on questionnaire data"""
    goal_data: QuestionnaireGoalData
    reasoning: str
    expected_impact: str
    difficulty_level: str  # easy, medium, hard
    time_to_completion: str
    suggested_timeline: str


class QuestionnaireGoalsIntegrationService:
    """
    Service for integrating questionnaire data with savings goals system.
    Automatically creates goals based on questionnaire responses for users
    who have savings goal tracking capability.
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        self.mid_tier_service = MidTierFeaturesService(db_session)
        self.tier_service = SubscriptionTierService(db_session)
        
        # Initialize goal creation parameters
        self._initialize_goal_parameters()
    
    def _initialize_goal_parameters(self):
        """Initialize parameters for goal creation from questionnaire data"""
        self.goal_params = {
            'emergency_fund': {
                'target_multiplier': 6.0,  # 6 months of expenses
                'min_amount': 1000.0,
                'max_amount': 50000.0,
                'priority': 1,
                'timeline_months': 12
            },
            'debt_payoff': {
                'target_multiplier': 1.0,  # Full debt amount
                'min_amount': 500.0,
                'max_amount': 100000.0,
                'priority': 2,
                'timeline_months': 36
            },
            'savings_growth': {
                'target_multiplier': 0.2,  # 20% of annual income
                'min_amount': 1000.0,
                'max_amount': 50000.0,
                'priority': 3,
                'timeline_months': 24
            },
            'investment_start': {
                'target_multiplier': 0.1,  # 10% of annual income
                'min_amount': 500.0,
                'max_amount': 25000.0,
                'priority': 4,
                'timeline_months': 18
            },
            'retirement_planning': {
                'target_multiplier': 0.15,  # 15% of annual income
                'min_amount': 1000.0,
                'max_amount': 100000.0,
                'priority': 5,
                'timeline_months': 60
            }
        }
    
    def create_goals_from_questionnaire(self, user_id: int, questionnaire_data: Dict[str, Any]) -> List[SavingsGoal]:
        """
        Create savings goals based on questionnaire data for users with capability
        
        Args:
            user_id: User ID
            questionnaire_data: Questionnaire response data
            
        Returns:
            List of created savings goals
        """
        # Check if user has savings goal capability
        if not self._user_has_goal_capability(user_id):
            self.logger.info(f"User {user_id} does not have savings goal capability")
            return []
        
        # Extract goal recommendations from questionnaire data
        goal_recommendations = self._analyze_questionnaire_for_goals(questionnaire_data)
        
        # Create goals from recommendations
        created_goals = []
        for recommendation in goal_recommendations:
            try:
                goal = self._create_goal_from_recommendation(user_id, recommendation)
                if goal:
                    created_goals.append(goal)
            except Exception as e:
                self.logger.error(f"Error creating goal for user {user_id}: {str(e)}")
                continue
        
        # Log goal creation
        self.logger.info(f"Created {len(created_goals)} goals from questionnaire for user {user_id}")
        
        return created_goals
    
    def _user_has_goal_capability(self, user_id: int) -> bool:
        """Check if user has savings goal tracking capability"""
        try:
            # Check subscription tier for goal capability
            user_tier = self.tier_service.get_user_tier(user_id)
            
            # Mid-tier and Professional users have goal capability
            if user_tier in [SubscriptionTier.MID_TIER, SubscriptionTier.PROFESSIONAL]:
                return True
            
            # Check if user has basic analytics feature (includes goals)
            if self.tier_service.has_feature_access(user_id, FeatureType.BASIC_ANALYTICS):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking user goal capability: {str(e)}")
            return False
    
    def _analyze_questionnaire_for_goals(self, questionnaire_data: Dict[str, Any]) -> List[QuestionnaireGoalRecommendation]:
        """
        Analyze questionnaire data and generate goal recommendations
        
        Args:
            questionnaire_data: Questionnaire response data
            
        Returns:
            List of goal recommendations
        """
        recommendations = []
        
        # Extract key data
        monthly_income = questionnaire_data.get('monthly_income', 0)
        monthly_expenses = questionnaire_data.get('monthly_expenses', 0)
        current_savings = questionnaire_data.get('current_savings', 0)
        total_debt = questionnaire_data.get('total_debt', 0)
        risk_tolerance = questionnaire_data.get('risk_tolerance', 3)
        financial_goals = questionnaire_data.get('financial_goals', [])
        
        # Calculate derived metrics
        annual_income = monthly_income * 12
        debt_to_income_ratio = total_debt / annual_income if annual_income > 0 else 0
        savings_to_expenses_ratio = current_savings / monthly_expenses if monthly_expenses > 0 else 0
        
        # 1. Emergency Fund Goal
        if self._should_create_emergency_fund_goal(current_savings, monthly_expenses, financial_goals):
            emergency_fund_goal = self._create_emergency_fund_recommendation(
                monthly_expenses, current_savings, financial_goals
            )
            recommendations.append(emergency_fund_goal)
        
        # 2. Debt Payoff Goal
        if self._should_create_debt_payoff_goal(total_debt, debt_to_income_ratio, financial_goals):
            debt_payoff_goal = self._create_debt_payoff_recommendation(
                total_debt, monthly_income, debt_to_income_ratio, financial_goals
            )
            recommendations.append(debt_payoff_goal)
        
        # 3. Savings Growth Goal
        if self._should_create_savings_growth_goal(current_savings, annual_income, financial_goals):
            savings_growth_goal = self._create_savings_growth_recommendation(
                current_savings, annual_income, monthly_income, financial_goals
            )
            recommendations.append(savings_growth_goal)
        
        # 4. Investment Start Goal
        if self._should_create_investment_goal(risk_tolerance, current_savings, financial_goals):
            investment_goal = self._create_investment_recommendation(
                risk_tolerance, annual_income, current_savings, financial_goals
            )
            recommendations.append(investment_goal)
        
        # 5. Retirement Planning Goal
        if self._should_create_retirement_goal(monthly_income, current_savings, financial_goals):
            retirement_goal = self._create_retirement_recommendation(
                monthly_income, current_savings, financial_goals
            )
            recommendations.append(retirement_goal)
        
        # Sort recommendations by priority
        recommendations.sort(key=lambda x: x.goal_data.priority)
        
        return recommendations
    
    def _should_create_emergency_fund_goal(self, current_savings: float, monthly_expenses: float, financial_goals: List[str]) -> bool:
        """Determine if emergency fund goal should be created"""
        # Always create if user selected emergency fund goal
        if 'emergency_fund' in financial_goals:
            return True
        
        # Create if current savings is less than 3 months of expenses
        target_emergency_fund = monthly_expenses * 6
        return current_savings < target_emergency_fund * 0.5  # Less than 50% of target
    
    def _should_create_debt_payoff_goal(self, total_debt: float, debt_to_income_ratio: float, financial_goals: List[str]) -> bool:
        """Determine if debt payoff goal should be created"""
        # Always create if user selected debt payoff goal
        if 'debt_payoff' in financial_goals:
            return True
        
        # Create if debt-to-income ratio is high (>30%)
        return debt_to_income_ratio > 0.3 and total_debt > 1000
    
    def _should_create_savings_growth_goal(self, current_savings: float, annual_income: float, financial_goals: List[str]) -> bool:
        """Determine if savings growth goal should be created"""
        # Always create if user selected savings goal
        if 'savings' in financial_goals:
            return True
        
        # Create if current savings is less than 10% of annual income
        target_savings = annual_income * 0.1
        return current_savings < target_savings
    
    def _should_create_investment_goal(self, risk_tolerance: int, current_savings: float, financial_goals: List[str]) -> bool:
        """Determine if investment goal should be created"""
        # Always create if user selected investment goal
        if 'investment' in financial_goals:
            return True
        
        # Create if user has moderate risk tolerance and some savings
        return risk_tolerance >= 3 and current_savings >= 5000
    
    def _should_create_retirement_goal(self, monthly_income: float, current_savings: float, financial_goals: List[str]) -> bool:
        """Determine if retirement goal should be created"""
        # Always create if user selected retirement goal
        if 'retirement' in financial_goals:
            return True
        
        # Create if user has stable income and some savings
        return monthly_income >= 3000 and current_savings >= 2000
    
    def _create_emergency_fund_recommendation(self, monthly_expenses: float, current_savings: float, financial_goals: List[str]) -> QuestionnaireGoalRecommendation:
        """Create emergency fund goal recommendation"""
        target_amount = monthly_expenses * self.goal_params['emergency_fund']['target_multiplier']
        target_amount = max(target_amount, self.goal_params['emergency_fund']['min_amount'])
        target_amount = min(target_amount, self.goal_params['emergency_fund']['max_amount'])
        
        # Calculate timeline based on current savings
        months_needed = self.goal_params['emergency_fund']['timeline_months']
        if current_savings > 0:
            months_needed = max(6, int((target_amount - current_savings) / (monthly_expenses * 0.1)))
        
        target_date = datetime.now() + timedelta(days=months_needed * 30.44)
        monthly_target = (target_amount - current_savings) / months_needed
        
        goal_data = QuestionnaireGoalData(
            goal_type=QuestionnaireGoalType.EMERGENCY_FUND,
            target_amount=target_amount,
            current_amount=current_savings,
            target_date=target_date,
            priority=self.goal_params['emergency_fund']['priority'],
            description="Build a safety net for unexpected expenses",
            motivation="Protect yourself from financial emergencies",
            monthly_target=monthly_target,
            confidence_score=0.9 if 'emergency_fund' in financial_goals else 0.7,
            source_data={'monthly_expenses': monthly_expenses, 'current_savings': current_savings}
        )
        
        return QuestionnaireGoalRecommendation(
            goal_data=goal_data,
            reasoning="Emergency fund should cover 6 months of expenses for financial security",
            expected_impact="High - Provides financial safety net",
            difficulty_level="medium" if monthly_target <= monthly_expenses * 0.2 else "hard",
            time_to_completion=f"{months_needed} months",
            suggested_timeline="12 months"
        )
    
    def _create_debt_payoff_recommendation(self, total_debt: float, monthly_income: float, debt_to_income_ratio: float, financial_goals: List[str]) -> QuestionnaireGoalRecommendation:
        """Create debt payoff goal recommendation"""
        target_amount = total_debt
        target_amount = max(target_amount, self.goal_params['debt_payoff']['min_amount'])
        target_amount = min(target_amount, self.goal_params['debt_payoff']['max_amount'])
        
        # Calculate timeline based on debt-to-income ratio
        if debt_to_income_ratio > 0.5:
            months_needed = 60  # 5 years for high debt
        elif debt_to_income_ratio > 0.3:
            months_needed = 36  # 3 years for moderate debt
        else:
            months_needed = 24  # 2 years for low debt
        
        target_date = datetime.now() + timedelta(days=months_needed * 30.44)
        monthly_target = target_amount / months_needed
        
        goal_data = QuestionnaireGoalData(
            goal_type=QuestionnaireGoalType.DEBT_PAYOFF,
            target_amount=target_amount,
            current_amount=0.0,
            target_date=target_date,
            priority=self.goal_params['debt_payoff']['priority'],
            description="Pay off all outstanding debt",
            motivation="Achieve financial freedom and reduce interest payments",
            monthly_target=monthly_target,
            confidence_score=0.9 if 'debt_payoff' in financial_goals else 0.8,
            source_data={'total_debt': total_debt, 'debt_to_income_ratio': debt_to_income_ratio}
        )
        
        return QuestionnaireGoalRecommendation(
            goal_data=goal_data,
            reasoning=f"Debt-to-income ratio of {debt_to_income_ratio:.1%} indicates need for debt reduction",
            expected_impact="High - Reduces interest payments and improves credit score",
            difficulty_level="hard" if monthly_target > monthly_income * 0.3 else "medium",
            time_to_completion=f"{months_needed} months",
            suggested_timeline=f"{months_needed} months"
        )
    
    def _create_savings_growth_recommendation(self, current_savings: float, annual_income: float, monthly_income: float, financial_goals: List[str]) -> QuestionnaireGoalRecommendation:
        """Create savings growth goal recommendation"""
        target_amount = annual_income * self.goal_params['savings_growth']['target_multiplier']
        target_amount = max(target_amount, self.goal_params['savings_growth']['min_amount'])
        target_amount = min(target_amount, self.goal_params['savings_growth']['max_amount'])
        
        months_needed = self.goal_params['savings_growth']['timeline_months']
        target_date = datetime.now() + timedelta(days=months_needed * 30.44)
        monthly_target = (target_amount - current_savings) / months_needed
        
        goal_data = QuestionnaireGoalData(
            goal_type=QuestionnaireGoalType.SAVINGS_GROWTH,
            target_amount=target_amount,
            current_amount=current_savings,
            target_date=target_date,
            priority=self.goal_params['savings_growth']['priority'],
            description="Build savings for future goals and opportunities",
            motivation="Create financial flexibility and prepare for major purchases",
            monthly_target=monthly_target,
            confidence_score=0.8 if 'savings' in financial_goals else 0.6,
            source_data={'annual_income': annual_income, 'current_savings': current_savings}
        )
        
        return QuestionnaireGoalRecommendation(
            goal_data=goal_data,
            reasoning="Target savings of 20% of annual income for financial security",
            expected_impact="Medium - Provides financial flexibility",
            difficulty_level="medium" if monthly_target <= monthly_income * 0.15 else "hard",
            time_to_completion=f"{months_needed} months",
            suggested_timeline="24 months"
        )
    
    def _create_investment_recommendation(self, risk_tolerance: int, annual_income: float, current_savings: float, financial_goals: List[str]) -> QuestionnaireGoalRecommendation:
        """Create investment goal recommendation"""
        target_amount = annual_income * self.goal_params['investment_start']['target_multiplier']
        target_amount = max(target_amount, self.goal_params['investment_start']['min_amount'])
        target_amount = min(target_amount, self.goal_params['investment_start']['max_amount'])
        
        months_needed = self.goal_params['investment_start']['timeline_months']
        target_date = datetime.now() + timedelta(days=months_needed * 30.44)
        monthly_target = target_amount / months_needed
        
        goal_data = QuestionnaireGoalData(
            goal_type=QuestionnaireGoalType.INVESTMENT_START,
            target_amount=target_amount,
            current_amount=0.0,
            target_date=target_date,
            priority=self.goal_params['investment_start']['priority'],
            description="Start building an investment portfolio",
            motivation="Grow wealth through compound interest and market returns",
            monthly_target=monthly_target,
            confidence_score=0.8 if 'investment' in financial_goals else 0.5,
            source_data={'risk_tolerance': risk_tolerance, 'annual_income': annual_income}
        )
        
        return QuestionnaireGoalRecommendation(
            goal_data=goal_data,
            reasoning=f"Risk tolerance of {risk_tolerance}/5 indicates readiness for investment",
            expected_impact="High - Potential for long-term wealth growth",
            difficulty_level="easy" if monthly_target <= annual_income * 0.05 else "medium",
            time_to_completion=f"{months_needed} months",
            suggested_timeline="18 months"
        )
    
    def _create_retirement_recommendation(self, monthly_income: float, current_savings: float, financial_goals: List[str]) -> QuestionnaireGoalRecommendation:
        """Create retirement planning goal recommendation"""
        target_amount = monthly_income * 12 * self.goal_params['retirement_planning']['target_multiplier']
        target_amount = max(target_amount, self.goal_params['retirement_planning']['min_amount'])
        target_amount = min(target_amount, self.goal_params['retirement_planning']['max_amount'])
        
        months_needed = self.goal_params['retirement_planning']['timeline_months']
        target_date = datetime.now() + timedelta(days=months_needed * 30.44)
        monthly_target = target_amount / months_needed
        
        goal_data = QuestionnaireGoalData(
            goal_type=QuestionnaireGoalType.RETIREMENT_PLANNING,
            target_amount=target_amount,
            current_amount=current_savings,
            target_date=target_date,
            priority=self.goal_params['retirement_planning']['priority'],
            description="Start planning for retirement",
            motivation="Secure your financial future and maintain lifestyle in retirement",
            monthly_target=monthly_target,
            confidence_score=0.8 if 'retirement' in financial_goals else 0.6,
            source_data={'monthly_income': monthly_income, 'current_savings': current_savings}
        )
        
        return QuestionnaireGoalRecommendation(
            goal_data=goal_data,
            reasoning="Start retirement planning early for compound growth benefits",
            expected_impact="High - Long-term financial security",
            difficulty_level="medium" if monthly_target <= monthly_income * 0.1 else "hard",
            time_to_completion=f"{months_needed} months",
            suggested_timeline="60 months"
        )
    
    def _create_goal_from_recommendation(self, user_id: int, recommendation: QuestionnaireGoalRecommendation) -> Optional[SavingsGoal]:
        """Create a savings goal from a recommendation"""
        try:
            goal_data = recommendation.goal_data
            
            # Create goal using Mid-tier service
            goal_dict = {
                'name': goal_data.description,
                'goal_type': goal_data.goal_type.value,
                'target_amount': goal_data.target_amount,
                'current_amount': goal_data.current_amount,
                'target_date': goal_data.target_date.isoformat(),
                'metadata': {
                    'source': 'questionnaire',
                    'confidence_score': goal_data.confidence_score,
                    'reasoning': recommendation.reasoning,
                    'expected_impact': recommendation.expected_impact,
                    'difficulty_level': recommendation.difficulty_level,
                    'time_to_completion': recommendation.time_to_completion,
                    'suggested_timeline': recommendation.suggested_timeline,
                    'source_data': goal_data.source_data
                }
            }
            
            goal = self.mid_tier_service.create_savings_goal(user_id, goal_dict)
            
            # Log goal creation
            self.logger.info(f"Created goal '{goal.goal_name}' for user {user_id} from questionnaire data")
            
            return goal
            
        except Exception as e:
            self.logger.error(f"Error creating goal from recommendation: {str(e)}")
            return None
    
    def get_questionnaire_goals_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get summary of goals created from questionnaire data
        
        Args:
            user_id: User ID
            
        Returns:
            Summary of questionnaire-based goals
        """
        try:
            # Get user's savings goals
            goals = self.mid_tier_service._get_user_savings_goals(user_id)
            
            # Filter goals created from questionnaire
            questionnaire_goals = []
            for goal in goals:
                if hasattr(goal, 'metadata') and goal.metadata and goal.metadata.get('source') == 'questionnaire':
                    questionnaire_goals.append(goal)
            
            # Calculate summary statistics
            total_goals = len(questionnaire_goals)
            total_target = sum(goal.target_amount for goal in questionnaire_goals)
            total_current = sum(goal.current_amount for goal in questionnaire_goals)
            overall_progress = (total_current / total_target) * 100 if total_target > 0 else 0
            
            # Group by goal type
            goals_by_type = {}
            for goal in questionnaire_goals:
                goal_type = goal.goal_type.value
                if goal_type not in goals_by_type:
                    goals_by_type[goal_type] = []
                goals_by_type[goal_type].append({
                    'goal_id': goal.goal_id,
                    'goal_name': goal.goal_name,
                    'progress_percentage': goal.progress_percentage,
                    'target_amount': goal.target_amount,
                    'current_amount': goal.current_amount
                })
            
            return {
                'total_questionnaire_goals': total_goals,
                'total_target_amount': total_target,
                'total_current_amount': total_current,
                'overall_progress': overall_progress,
                'goals_by_type': goals_by_type,
                'questionnaire_source': True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting questionnaire goals summary: {str(e)}")
            return {
                'total_questionnaire_goals': 0,
                'total_target_amount': 0.0,
                'total_current_amount': 0.0,
                'overall_progress': 0.0,
                'goals_by_type': {},
                'questionnaire_source': False,
                'error': str(e)
            }
    
    def update_questionnaire_goals(self, user_id: int, updated_questionnaire_data: Dict[str, Any]) -> List[SavingsGoal]:
        """
        Update existing goals based on new questionnaire data
        
        Args:
            user_id: User ID
            updated_questionnaire_data: Updated questionnaire data
            
        Returns:
            List of updated goals
        """
        try:
            # Get current questionnaire-based goals
            current_goals = self.mid_tier_service._get_user_savings_goals(user_id)
            questionnaire_goals = [g for g in current_goals if hasattr(g, 'metadata') and g.metadata and g.metadata.get('source') == 'questionnaire']
            
            # Generate new recommendations
            new_recommendations = self._analyze_questionnaire_for_goals(updated_questionnaire_data)
            
            updated_goals = []
            
            # Update existing goals or create new ones
            for recommendation in new_recommendations:
                goal_type = recommendation.goal_data.goal_type.value
                
                # Find existing goal of this type
                existing_goal = next((g for g in questionnaire_goals if g.goal_type.value == goal_type), None)
                
                if existing_goal:
                    # Update existing goal
                    updated_goal = self._update_existing_goal(existing_goal, recommendation)
                    if updated_goal:
                        updated_goals.append(updated_goal)
                else:
                    # Create new goal
                    new_goal = self._create_goal_from_recommendation(user_id, recommendation)
                    if new_goal:
                        updated_goals.append(new_goal)
            
            self.logger.info(f"Updated {len(updated_goals)} goals for user {user_id} based on new questionnaire data")
            return updated_goals
            
        except Exception as e:
            self.logger.error(f"Error updating questionnaire goals: {str(e)}")
            return []
    
    def _update_existing_goal(self, existing_goal: SavingsGoal, recommendation: QuestionnaireGoalRecommendation) -> Optional[SavingsGoal]:
        """Update an existing goal based on new recommendation"""
        try:
            goal_data = recommendation.goal_data
            
            # Update goal properties
            existing_goal.target_amount = goal_data.target_amount
            existing_goal.target_date = goal_data.target_date
            existing_goal.monthly_target = goal_data.monthly_target
            
            # Update metadata
            if not existing_goal.metadata:
                existing_goal.metadata = {}
            
            existing_goal.metadata.update({
                'last_updated_from_questionnaire': datetime.now().isoformat(),
                'confidence_score': goal_data.confidence_score,
                'reasoning': recommendation.reasoning,
                'expected_impact': recommendation.expected_impact,
                'difficulty_level': recommendation.difficulty_level,
                'time_to_completion': recommendation.time_to_completion,
                'suggested_timeline': recommendation.suggested_timeline,
                'source_data': goal_data.source_data
            })
            
            # Update status and progress
            self.mid_tier_service._update_goal_status_and_progress(existing_goal)
            
            return existing_goal
            
        except Exception as e:
            self.logger.error(f"Error updating existing goal: {str(e)}")
            return None 