"""
Savings Goals Service

This module provides savings goal management, progress tracking, and milestone detection
for the MINGUS application.
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
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class GoalStatus(Enum):
    """Savings goal status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class GoalType(Enum):
    """Savings goal types"""
    EMERGENCY_FUND = "emergency_fund"
    VACATION = "vacation"
    HOME_DOWN_PAYMENT = "home_down_payment"
    CAR_PURCHASE = "car_purchase"
    EDUCATION = "education"
    RETIREMENT = "retirement"
    CUSTOM = "custom"


@dataclass
class SavingsGoal:
    """Savings goal data structure"""
    id: str
    user_id: str
    name: str
    description: str
    goal_type: GoalType
    target_amount: float
    current_amount: float
    target_date: Optional[date]
    status: GoalStatus
    created_at: datetime
    updated_at: datetime
    monthly_target: float = 0.0
    milestone_percentages: List[float] = field(default_factory=lambda: [25, 50, 75, 100])


class SavingsGoalsService:
    """Service for managing savings goals and progress tracking"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    def get_user_savings_goals(self, user_id: str) -> List[SavingsGoal]:
        """Get all savings goals for a user"""
        try:
            # This would query the actual savings goals table
            # For now, return mock data
            goals = [
                SavingsGoal(
                    id="goal_1",
                    user_id=user_id,
                    name="Emergency Fund",
                    description="Build a 6-month emergency fund",
                    goal_type=GoalType.EMERGENCY_FUND,
                    target_amount=15000.0,
                    current_amount=8500.0,
                    target_date=date.today() + timedelta(days=180),
                    status=GoalStatus.ACTIVE,
                    created_at=datetime.utcnow() - timedelta(days=30),
                    updated_at=datetime.utcnow(),
                    monthly_target=500.0
                ),
                SavingsGoal(
                    id="goal_2",
                    user_id=user_id,
                    name="Vacation Fund",
                    description="Save for summer vacation",
                    goal_type=GoalType.VACATION,
                    target_amount=5000.0,
                    current_amount=2000.0,
                    target_date=date.today() + timedelta(days=90),
                    status=GoalStatus.ACTIVE,
                    created_at=datetime.utcnow() - timedelta(days=15),
                    updated_at=datetime.utcnow(),
                    monthly_target=1000.0
                )
            ]
            
            return goals
            
        except Exception as e:
            self.logger.error(f"Error getting savings goals for user {user_id}: {e}")
            return []
    
    def create_savings_goal(self, user_id: str, goal_data: Dict[str, Any]) -> Optional[SavingsGoal]:
        """Create a new savings goal"""
        try:
            # This would create a new goal in the database
            # For now, return a mock goal
            goal = SavingsGoal(
                id=f"goal_{int(datetime.utcnow().timestamp())}",
                user_id=user_id,
                name=goal_data.get('name', 'New Goal'),
                description=goal_data.get('description', ''),
                goal_type=GoalType(goal_data.get('goal_type', 'custom')),
                target_amount=float(goal_data.get('target_amount', 0)),
                current_amount=0.0,
                target_date=goal_data.get('target_date'),
                status=GoalStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                monthly_target=self._calculate_monthly_target(
                    float(goal_data.get('target_amount', 0)),
                    goal_data.get('target_date')
                )
            )
            
            return goal
            
        except Exception as e:
            self.logger.error(f"Error creating savings goal for user {user_id}: {e}")
            return None
    
    def update_goal_progress(self, goal_id: str, amount: float) -> bool:
        """Update goal progress with a new contribution"""
        try:
            # This would update the goal in the database
            # For now, just log the update
            self.logger.info(f"Updated goal {goal_id} with contribution of ${amount}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating goal progress for goal {goal_id}: {e}")
            return False
    
    def get_goal_progress(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress information for a goal"""
        try:
            # This would query the goal from the database
            # For now, return mock data
            return {
                'goal_id': goal_id,
                'progress_percentage': 56.7,
                'current_amount': 8500.0,
                'target_amount': 15000.0,
                'remaining_amount': 6500.0,
                'days_remaining': 150,
                'monthly_target': 500.0,
                'on_track': True,
                'milestones_reached': [25, 50],
                'next_milestone': 75
            }
            
        except Exception as e:
            self.logger.error(f"Error getting goal progress for goal {goal_id}: {e}")
            return None
    
    def check_milestone_progress(self, goal: SavingsGoal) -> Optional[Dict[str, Any]]:
        """Check if a goal has reached a milestone"""
        try:
            progress_percentage = (goal.current_amount / goal.target_amount) * 100
            
            for milestone in goal.milestone_percentages:
                if progress_percentage >= milestone and progress_percentage < milestone + 25:
                    return {
                        'milestone_reached': True,
                        'milestone_percentage': milestone,
                        'milestone_name': f"{milestone}% Complete",
                        'current_progress': progress_percentage
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking milestone progress for goal {goal.id}: {e}")
            return None
    
    def _calculate_monthly_target(self, target_amount: float, target_date: Optional[date]) -> float:
        """Calculate monthly target based on goal amount and target date"""
        if not target_date:
            return target_amount / 12  # Default to 12 months
        
        days_remaining = (target_date - date.today()).days
        months_remaining = max(days_remaining / 30, 1)  # Minimum 1 month
        
        return target_amount / months_remaining
    
    def get_goal_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized goal recommendations"""
        try:
            # This would analyze user's financial situation and provide recommendations
            recommendations = [
                {
                    'type': 'emergency_fund',
                    'title': 'Build Emergency Fund',
                    'description': 'Save 3-6 months of expenses for emergencies',
                    'recommended_amount': 15000.0,
                    'priority': 'high',
                    'reasoning': 'Based on your monthly expenses of $2,500'
                },
                {
                    'type': 'debt_payoff',
                    'title': 'Pay Off High-Interest Debt',
                    'description': 'Focus on credit card debt with high interest rates',
                    'recommended_amount': 5000.0,
                    'priority': 'high',
                    'reasoning': 'You have $5,000 in credit card debt at 18% APR'
                },
                {
                    'type': 'retirement',
                    'title': 'Increase Retirement Savings',
                    'description': 'Contribute more to your 401(k) or IRA',
                    'recommended_amount': 6000.0,
                    'priority': 'medium',
                    'reasoning': 'You\'re currently saving 8% of income, aim for 15%'
                }
            ]
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting goal recommendations for user {user_id}: {e}")
            return [] 