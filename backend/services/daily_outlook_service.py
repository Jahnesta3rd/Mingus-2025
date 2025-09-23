#!/usr/bin/env python3
"""
Mingus Application - Daily Outlook Service
Service for implementing dynamic weighting algorithm for Daily Outlook feature
"""

import logging
import sqlite3
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..models.daily_outlook import RelationshipStatus, UserRelationshipStatus, DailyOutlook
from ..models.user_models import User
from ..models.database import db

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DynamicWeights:
    """Data class for dynamic weights based on relationship status"""
    financial: float
    wellness: float
    relationship: float
    career: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'financial': self.financial,
            'wellness': self.wellness,
            'relationship': self.relationship,
            'career': self.career
        }

@dataclass
class BalanceScores:
    """Data class for individual balance scores"""
    financial_score: float
    wellness_score: float
    relationship_score: float
    career_score: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'financial_score': self.financial_score,
            'wellness_score': self.wellness_score,
            'relationship_score': self.relationship_score,
            'career_score': self.career_score
        }

class DailyOutlookService:
    """
    Service for implementing dynamic weighting algorithm for Daily Outlook feature
    
    This service provides:
    - Dynamic weight calculation based on user relationship status
    - Balance score calculation using weighted averages
    - Integration with existing financial, wellness, career, and relationship data
    - Relationship status management
    """
    
    # Dynamic weight configurations based on relationship status
    WEIGHT_CONFIGURATIONS = {
        RelationshipStatus.SINGLE_CAREER_FOCUSED: DynamicWeights(
            financial=0.40,
            wellness=0.25,
            relationship=0.10,
            career=0.25
        ),
        RelationshipStatus.SINGLE_LOOKING: DynamicWeights(
            financial=0.35,
            wellness=0.25,
            relationship=0.25,
            career=0.15
        ),
        RelationshipStatus.DATING: DynamicWeights(
            financial=0.35,
            wellness=0.20,
            relationship=0.30,
            career=0.15
        ),
        RelationshipStatus.EARLY_RELATIONSHIP: DynamicWeights(
            financial=0.35,
            wellness=0.20,
            relationship=0.30,
            career=0.15
        ),
        RelationshipStatus.COMMITTED: DynamicWeights(
            financial=0.35,
            wellness=0.20,
            relationship=0.30,
            career=0.15
        ),
        RelationshipStatus.ENGAGED: DynamicWeights(
            financial=0.35,
            wellness=0.20,
            relationship=0.30,
            career=0.15
        ),
        RelationshipStatus.MARRIED: DynamicWeights(
            financial=0.35,
            wellness=0.20,
            relationship=0.30,
            career=0.15
        ),
        RelationshipStatus.COMPLICATED: DynamicWeights(
            financial=0.40,
            wellness=0.20,
            relationship=0.25,
            career=0.15
        )
    }
    
    def __init__(self, profile_db_path: str = "user_profiles.db"):
        """Initialize the Daily Outlook service"""
        self.profile_db_path = profile_db_path
        
        logger.info("DailyOutlookService initialized successfully")
    
    def calculate_dynamic_weights(self, user_id: int) -> Dict[str, float]:
        """
        Calculate dynamic weights based on user's relationship status
        
        Args:
            user_id: User ID to calculate weights for
            
        Returns:
            Dictionary with weight percentages for each category
        """
        try:
            # Get user's current relationship status
            relationship_status = self.get_user_relationship_status(user_id)
            
            if not relationship_status:
                # Default to single career focused if no status found
                logger.warning(f"No relationship status found for user {user_id}, using default weights")
                relationship_status = RelationshipStatus.SINGLE_CAREER_FOCUSED
            
            # Get weights for the relationship status
            weights = self.WEIGHT_CONFIGURATIONS.get(
                relationship_status, 
                self.WEIGHT_CONFIGURATIONS[RelationshipStatus.SINGLE_CAREER_FOCUSED]
            )
            
            logger.info(f"Calculated dynamic weights for user {user_id}: {weights.to_dict()}")
            return weights.to_dict()
            
        except Exception as e:
            logger.error(f"Error calculating dynamic weights for user {user_id}: {e}")
            # Return default weights on error
            default_weights = self.WEIGHT_CONFIGURATIONS[RelationshipStatus.SINGLE_CAREER_FOCUSED]
            return default_weights.to_dict()
    
    def calculate_balance_score(self, user_id: int) -> Tuple[int, BalanceScores]:
        """
        Calculate 0-100 balance score using weighted averages
        
        Args:
            user_id: User ID to calculate balance score for
            
        Returns:
            Tuple of (overall_balance_score, individual_scores)
        """
        try:
            # Get dynamic weights
            weights = self.calculate_dynamic_weights(user_id)
            
            # Get individual category scores
            individual_scores = self._get_individual_scores(user_id)
            
            # Calculate weighted average
            weighted_score = (
                individual_scores.financial_score * weights['financial'] +
                individual_scores.wellness_score * weights['wellness'] +
                individual_scores.relationship_score * weights['relationship'] +
                individual_scores.career_score * weights['career']
            )
            
            # Round to integer (0-100)
            balance_score = int(round(weighted_score))
            
            logger.info(f"Calculated balance score for user {user_id}: {balance_score}")
            return balance_score, individual_scores
            
        except Exception as e:
            logger.error(f"Error calculating balance score for user {user_id}: {e}")
            # Return default score on error
            return 50, BalanceScores(50.0, 50.0, 50.0, 50.0)
    
    def get_user_relationship_status(self, user_id: int) -> Optional[RelationshipStatus]:
        """
        Retrieve current relationship status for a user
        
        Args:
            user_id: User ID to get relationship status for
            
        Returns:
            Current relationship status or None if not found
        """
        try:
            # Query the database for user's relationship status
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            # First check if user exists in the main users table
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                logger.warning(f"User {user_id} not found in users table")
                conn.close()
                return None
            
            # Get relationship status from UserRelationshipStatus table
            cursor.execute("""
                SELECT status FROM user_relationship_status 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                status_value = result[0]
                # Convert string to enum
                try:
                    status = RelationshipStatus(status_value)
                    logger.info(f"Retrieved relationship status for user {user_id}: {status.value}")
                    return status
                except ValueError:
                    logger.error(f"Invalid relationship status value: {status_value}")
                    return None
            else:
                logger.info(f"No relationship status found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving relationship status for user {user_id}: {e}")
            return None
    
    def update_relationship_status(self, user_id: int, status: RelationshipStatus, 
                                 satisfaction_score: int) -> bool:
        """
        Update user's relationship status and satisfaction score
        
        Args:
            user_id: User ID to update
            status: New relationship status
            satisfaction_score: Satisfaction score (1-10)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate satisfaction score
            if not (1 <= satisfaction_score <= 10):
                logger.error(f"Invalid satisfaction score {satisfaction_score}. Must be 1-10.")
                return False
            
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                logger.error(f"User {user_id} not found")
                conn.close()
                return False
            
            # Update or insert relationship status
            cursor.execute("""
                INSERT OR REPLACE INTO user_relationship_status 
                (user_id, status, satisfaction_score, financial_impact_score, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, status.value, satisfaction_score, 5, datetime.utcnow()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated relationship status for user {user_id}: {status.value} (satisfaction: {satisfaction_score})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating relationship status for user {user_id}: {e}")
            return False
    
    def _get_individual_scores(self, user_id: int) -> BalanceScores:
        """
        Get individual category scores for a user
        
        Args:
            user_id: User ID to get scores for
            
        Returns:
            BalanceScores object with individual category scores
        """
        try:
            # Initialize default scores
            financial_score = 50.0
            wellness_score = 50.0
            relationship_score = 50.0
            career_score = 50.0
            
            # Get financial score from profile data
            financial_score = self._get_financial_score(user_id)
            
            # Get wellness score from mood tracking and activity data
            wellness_score = self._get_wellness_score(user_id)
            
            # Get relationship score from relationship status
            relationship_score = self._get_relationship_score(user_id)
            
            # Get career score from user goals and profile
            career_score = self._get_career_score(user_id)
            
            return BalanceScores(
                financial_score=financial_score,
                wellness_score=wellness_score,
                relationship_score=relationship_score,
                career_score=career_score
            )
            
        except Exception as e:
            logger.error(f"Error getting individual scores for user {user_id}: {e}")
            return BalanceScores(50.0, 50.0, 50.0, 50.0)
    
    def _get_financial_score(self, user_id: int) -> float:
        """Get financial health score (0-100)"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            # Get financial data from user profiles
            cursor.execute("""
                SELECT financial_info FROM user_profiles 
                WHERE email = (SELECT email FROM users WHERE id = ?)
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                import json
                financial_info = json.loads(result[0])
                
                # Calculate score based on financial health indicators
                score = 50.0  # Base score
                
                # Check for emergency fund
                current_savings = financial_info.get('currentSavings', 0)
                monthly_income = financial_info.get('monthlyIncome', 0)
                if monthly_income > 0:
                    emergency_fund_months = current_savings / monthly_income
                    if emergency_fund_months >= 6:
                        score += 20
                    elif emergency_fund_months >= 3:
                        score += 10
                
                # Check debt-to-income ratio
                annual_income = financial_info.get('annualIncome', 0)
                student_loans = financial_info.get('studentLoans', 0)
                credit_card_debt = financial_info.get('creditCardDebt', 0)
                total_debt = student_loans + credit_card_debt
                
                if annual_income > 0:
                    debt_to_income = total_debt / annual_income
                    if debt_to_income < 0.2:
                        score += 15
                    elif debt_to_income < 0.4:
                        score += 5
                    else:
                        score -= 10
                
                # Check savings rate
                monthly_expenses = financial_info.get('monthlyExpenses', {})
                total_expenses = sum([
                    monthly_expenses.get('rent', 0),
                    monthly_expenses.get('carPayment', 0),
                    monthly_expenses.get('insurance', 0),
                    monthly_expenses.get('groceries', 0),
                    monthly_expenses.get('utilities', 0),
                    monthly_expenses.get('studentLoanPayment', 0),
                    monthly_expenses.get('creditCardMinimum', 0)
                ])
                
                if monthly_income > 0:
                    savings_rate = (monthly_income - total_expenses) / monthly_income
                    if savings_rate > 0.2:
                        score += 15
                    elif savings_rate > 0.1:
                        score += 5
                    else:
                        score -= 5
                
                return max(0, min(100, score))
            
            return 50.0
            
        except Exception as e:
            logger.error(f"Error calculating financial score for user {user_id}: {e}")
            return 50.0
    
    def _get_wellness_score(self, user_id: int) -> float:
        """Get wellness score (0-100) from mood tracking and activity data"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            # Get recent mood data
            cursor.execute("""
                SELECT AVG(mood_score) FROM user_mood_data 
                WHERE user_id = ? 
                AND timestamp >= datetime('now', '-30 days')
            """, (user_id,))
            
            mood_result = cursor.fetchone()
            mood_score = mood_result[0] if mood_result[0] else 3.0  # Default neutral
            
            # Get wellness data from weekly check-ins
            cursor.execute("""
                SELECT AVG(physical_activity), AVG(meditation_minutes), AVG(relationship_satisfaction)
                FROM weekly_checkins 
                WHERE user_id = ? 
                AND check_in_date >= date('now', '-30 days')
            """, (user_id,))
            
            wellness_result = cursor.fetchone()
            conn.close()
            
            # Calculate wellness score
            score = 50.0  # Base score
            
            # Mood contribution (1-5 scale, convert to 0-100)
            mood_contribution = (mood_score - 1) * 25  # Convert 1-5 to 0-100
            score += (mood_contribution - 50) * 0.4  # 40% weight
            
            if wellness_result and wellness_result[0]:
                # Physical activity contribution
                physical_activity = wellness_result[0] or 0
                if physical_activity >= 3:
                    score += 15
                elif physical_activity >= 1:
                    score += 5
                
                # Meditation contribution
                meditation_minutes = wellness_result[1] or 0
                if meditation_minutes >= 60:
                    score += 10
                elif meditation_minutes >= 30:
                    score += 5
                
                # Relationship satisfaction contribution
                relationship_satisfaction = wellness_result[2] or 5
                if relationship_satisfaction >= 8:
                    score += 10
                elif relationship_satisfaction >= 6:
                    score += 5
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating wellness score for user {user_id}: {e}")
            return 50.0
    
    def _get_relationship_score(self, user_id: int) -> float:
        """Get relationship score (0-100) from relationship status and satisfaction"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT satisfaction_score, status FROM user_relationship_status 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                satisfaction_score = result[0]
                status = result[1]
                
                # Base score from satisfaction (1-10 scale, convert to 0-100)
                score = (satisfaction_score - 1) * 11.11  # Convert 1-10 to 0-100
                
                # Adjust based on relationship status
                if status in ['married', 'engaged', 'committed']:
                    score += 10  # Bonus for committed relationships
                elif status in ['dating', 'early_relationship']:
                    score += 5   # Small bonus for developing relationships
                
                return max(0, min(100, score))
            
            return 50.0  # Default score if no relationship data
            
        except Exception as e:
            logger.error(f"Error calculating relationship score for user {user_id}: {e}")
            return 50.0
    
    def _get_career_score(self, user_id: int) -> float:
        """Get career score (0-100) from user goals and profile data"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            # Get career data from user profiles
            cursor.execute("""
                SELECT goals FROM user_profiles 
                WHERE email = (SELECT email FROM users WHERE id = ?)
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                import json
                goals = json.loads(result[0])
                
                score = 50.0  # Base score
                
                # Check for career-related goals
                career_goals = goals.get('careerGoals', [])
                if career_goals:
                    score += 20  # Bonus for having career goals
                
                # Check for skill development goals
                skill_goals = goals.get('skillDevelopment', [])
                if skill_goals:
                    score += 15  # Bonus for skill development
                
                # Check for education goals
                education_goals = goals.get('education', [])
                if education_goals:
                    score += 10  # Bonus for education goals
                
                return max(0, min(100, score))
            
            return 50.0  # Default score if no career data
            
        except Exception as e:
            logger.error(f"Error calculating career score for user {user_id}: {e}")
            return 50.0
    
    def calculate_streak_count(self, user_id: int, target_date: date) -> int:
        """
        Calculate streak count for a user up to a target date
        
        Args:
            user_id: User ID to calculate streak for
            target_date: Date to calculate streak up to
            
        Returns:
            Number of consecutive days with daily outlooks
        """
        try:
            # Get all daily outlooks for the user, ordered by date descending
            outlooks = DailyOutlook.query.filter_by(user_id=user_id)\
                .filter(DailyOutlook.date <= target_date)\
                .order_by(DailyOutlook.date.desc())\
                .all()
            
            if not outlooks:
                return 0
            
            streak_count = 0
            current_date = target_date
            
            for outlook in outlooks:
                if outlook.date == current_date:
                    streak_count += 1
                    current_date = current_date - timedelta(days=1)
                else:
                    break
            
            return streak_count
            
        except Exception as e:
            logger.error(f"Error calculating streak count for user {user_id}: {e}")
            return 0
    
    def update_user_relationship_status(self, user_id: int, status: str, 
                                      satisfaction_score: int, financial_impact_score: int) -> bool:
        """
        Update user's relationship status
        
        Args:
            user_id: User ID to update
            status: Relationship status string
            satisfaction_score: Satisfaction score (1-10)
            financial_impact_score: Financial impact score (1-10)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            if satisfaction_score < 1 or satisfaction_score > 10:
                logger.error(f"Invalid satisfaction score: {satisfaction_score}")
                return False
            
            if financial_impact_score < 1 or financial_impact_score > 10:
                logger.error(f"Invalid financial impact score: {financial_impact_score}")
                return False
            
            # Convert status string to enum
            try:
                relationship_status = RelationshipStatus(status.lower())
            except ValueError:
                logger.error(f"Invalid relationship status: {status}")
                return False
            
            # Update or create relationship status
            existing_status = UserRelationshipStatus.query.filter_by(user_id=user_id).first()
            
            if existing_status:
                existing_status.status = relationship_status
                existing_status.satisfaction_score = satisfaction_score
                existing_status.financial_impact_score = financial_impact_score
            else:
                new_status = UserRelationshipStatus(
                    user_id=user_id,
                    status=relationship_status,
                    satisfaction_score=satisfaction_score,
                    financial_impact_score=financial_impact_score
                )
                db.session.add(new_status)
            
            db.session.commit()
            logger.info(f"Updated relationship status for user {user_id}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating relationship status for user {user_id}: {e}")
            db.session.rollback()
            return False