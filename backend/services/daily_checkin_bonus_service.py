#!/usr/bin/env python3
"""
Daily Check-in Bonus Service for Mingus Application

Handles daily check-in bonuses, streak multipliers, and engagement rewards.
Integrates with the gamification system to provide tier-specific bonuses.

Features:
- Daily check-in bonuses based on user tier
- Streak multipliers for consecutive days
- Time-based bonuses (early bird, night owl)
- Weekend and holiday bonuses
- Engagement-based rewards
- Social sharing bonuses
"""

import logging
from datetime import datetime, date, timedelta, time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session
from backend.models.database import db
from backend.models.user_models import User
from backend.models.gamification_models import *
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
from backend.services.gamification_service import GamificationService

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class BonusType(Enum):
    """Types of bonuses that can be awarded"""
    DAILY_CHECKIN = "daily_checkin"
    STREAK_MULTIPLIER = "streak_multiplier"
    EARLY_BIRD = "early_bird"
    NIGHT_OWL = "night_owl"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"
    ENGAGEMENT = "engagement"
    SOCIAL_SHARE = "social_share"
    TIER_UPGRADE = "tier_upgrade"
    SPECIAL_EVENT = "special_event"

class TimeSlot(Enum):
    """Time slots for check-in bonuses"""
    EARLY_MORNING = "early_morning"  # 5:00-8:00 AM
    MORNING = "morning"  # 8:00-12:00 PM
    AFTERNOON = "afternoon"  # 12:00-5:00 PM
    EVENING = "evening"  # 5:00-10:00 PM
    NIGHT = "night"  # 10:00 PM-5:00 AM

@dataclass
class BonusConfig:
    """Configuration for a bonus type"""
    bonus_type: BonusType
    name: str
    description: str
    base_points: int
    multiplier: float
    tier_requirement: FeatureTier
    max_daily_uses: int
    cooldown_hours: int
    conditions: Dict[str, any]

@dataclass
class BonusAward:
    """Record of a bonus award"""
    user_id: int
    bonus_type: BonusType
    points_awarded: int
    multiplier_applied: float
    conditions_met: List[str]
    awarded_at: datetime
    metadata: Dict[str, any]

# ============================================================================
# DAILY CHECK-IN BONUS SERVICE
# ============================================================================

class DailyCheckinBonusService:
    """Service for managing daily check-in bonuses and rewards"""
    
    def __init__(self):
        self.feature_service = FeatureFlagService()
        self.gamification_service = GamificationService()
        
        # Define bonus configurations
        self.bonus_configs = {
            BonusType.DAILY_CHECKIN: BonusConfig(
                bonus_type=BonusType.DAILY_CHECKIN,
                name="Daily Check-in",
                description="Points for checking in daily",
                base_points=10,
                multiplier=1.0,
                tier_requirement=FeatureTier.BUDGET,
                max_daily_uses=1,
                cooldown_hours=24,
                conditions={}
            ),
            BonusType.STREAK_MULTIPLIER: BonusConfig(
                bonus_type=BonusType.STREAK_MULTIPLIER,
                name="Streak Multiplier",
                description="Bonus points for maintaining streaks",
                base_points=5,
                multiplier=1.0,
                tier_requirement=FeatureTier.BUDGET,
                max_daily_uses=1,
                cooldown_hours=0,
                conditions={"min_streak": 3}
            ),
            BonusType.EARLY_BIRD: BonusConfig(
                bonus_type=BonusType.EARLY_BIRD,
                name="Early Bird",
                description="Bonus for checking in early",
                base_points=15,
                multiplier=1.0,
                tier_requirement=FeatureTier.BUDGET,
                max_daily_uses=1,
                cooldown_hours=24,
                conditions={"time_range": "05:00-08:00"}
            ),
            BonusType.NIGHT_OWL: BonusConfig(
                bonus_type=BonusType.NIGHT_OWL,
                name="Night Owl",
                description="Bonus for checking in late",
                base_points=15,
                multiplier=1.0,
                tier_requirement=FeatureTier.BUDGET,
                max_daily_uses=1,
                cooldown_hours=24,
                conditions={"time_range": "22:00-05:00"}
            ),
            BonusType.WEEKEND: BonusConfig(
                bonus_type=BonusType.WEEKEND,
                name="Weekend Warrior",
                description="Bonus for weekend check-ins",
                base_points=20,
                multiplier=1.0,
                tier_requirement=FeatureTier.BUDGET,
                max_daily_uses=2,
                cooldown_hours=24,
                conditions={"days": ["saturday", "sunday"]}
            ),
            BonusType.ENGAGEMENT: BonusConfig(
                bonus_type=BonusType.ENGAGEMENT,
                name="Engagement Bonus",
                description="Bonus for high engagement",
                base_points=25,
                multiplier=1.0,
                tier_requirement=FeatureTier.BUDGET_CAREER_VEHICLE,
                max_daily_uses=1,
                cooldown_hours=24,
                conditions={"min_rating": 4, "min_time_spent": 10}
            ),
            BonusType.SOCIAL_SHARE: BonusConfig(
                bonus_type=BonusType.SOCIAL_SHARE,
                name="Social Share",
                description="Bonus for sharing progress",
                base_points=30,
                multiplier=1.0,
                tier_requirement=FeatureTier.MID_TIER,
                max_daily_uses=3,
                cooldown_hours=6,
                conditions={}
            )
        }

    # ============================================================================
    # BONUS CALCULATION METHODS
    # ============================================================================

    def calculate_daily_bonuses(self, user_id: int, checkin_time: datetime = None) -> List[BonusAward]:
        """Calculate all applicable bonuses for a daily check-in"""
        try:
            if checkin_time is None:
                checkin_time = datetime.now()
            
            bonuses = []
            
            # Get user tier
            user_tier = self.feature_service.get_user_tier(user_id)
            
            # Get user streak data
            streak_data = self.gamification_service.calculate_streak(user_id)
            
            # Check each bonus type
            for bonus_type, config in self.bonus_configs.items():
                if self._is_bonus_available(user_id, bonus_type, checkin_time):
                    if self._meets_bonus_conditions(user_id, bonus_type, config, checkin_time, streak_data):
                        bonus_award = self._award_bonus(user_id, bonus_type, config, checkin_time, streak_data)
                        if bonus_award:
                            bonuses.append(bonus_award)
            
            return bonuses
            
        except Exception as e:
            logger.error(f"Error calculating daily bonuses for user {user_id}: {e}")
            return []

    def _is_bonus_available(self, user_id: int, bonus_type: BonusType, checkin_time: datetime) -> bool:
        """Check if a bonus is available for the user"""
        try:
            config = self.bonus_configs.get(bonus_type)
            if not config:
                return False
            
            # Check tier requirement
            user_tier = self.feature_service.get_user_tier(user_id)
            tier_hierarchy = {
                FeatureTier.BUDGET: 1,
                FeatureTier.BUDGET_CAREER_VEHICLE: 2,
                FeatureTier.MID_TIER: 3,
                FeatureTier.PROFESSIONAL: 4
            }
            
            user_level = tier_hierarchy.get(user_tier, 0)
            required_level = tier_hierarchy.get(config.tier_requirement, 999)
            
            if user_level < required_level:
                return False
            
            # Check daily usage limit
            today = checkin_time.date()
            daily_usage = self._get_daily_bonus_usage(user_id, bonus_type, today)
            if daily_usage >= config.max_daily_uses:
                return False
            
            # Check cooldown
            if config.cooldown_hours > 0:
                last_usage = self._get_last_bonus_usage(user_id, bonus_type)
                if last_usage:
                    time_since_last = checkin_time - last_usage
                    if time_since_last.total_seconds() < (config.cooldown_hours * 3600):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking bonus availability: {e}")
            return False

    def _meets_bonus_conditions(self, user_id: int, bonus_type: BonusType, config: BonusConfig, 
                                checkin_time: datetime, streak_data) -> bool:
        """Check if bonus conditions are met"""
        try:
            conditions = config.conditions
            
            # Time-based conditions
            if "time_range" in conditions:
                time_range = conditions["time_range"]
                if not self._check_time_condition(checkin_time, time_range):
                    return False
            
            # Day-based conditions
            if "days" in conditions:
                allowed_days = conditions["days"]
                day_name = checkin_time.strftime("%A").lower()
                if day_name not in allowed_days:
                    return False
            
            # Streak-based conditions
            if "min_streak" in conditions:
                min_streak = conditions["min_streak"]
                if streak_data.current_streak < min_streak:
                    return False
            
            # Rating-based conditions
            if "min_rating" in conditions:
                min_rating = conditions["min_rating"]
                # This would check user's daily rating
                # For now, assume condition is met
                pass
            
            # Time spent conditions
            if "min_time_spent" in conditions:
                min_time = conditions["min_time_spent"]
                # This would check user's engagement time
                # For now, assume condition is met
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking bonus conditions: {e}")
            return False

    def _check_time_condition(self, checkin_time: datetime, time_range: str) -> bool:
        """Check if check-in time falls within specified range"""
        try:
            start_time_str, end_time_str = time_range.split("-")
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()
            checkin_time_only = checkin_time.time()
            
            # Handle overnight ranges (e.g., 22:00-05:00)
            if start_time > end_time:
                return checkin_time_only >= start_time or checkin_time_only <= end_time
            else:
                return start_time <= checkin_time_only <= end_time
                
        except Exception as e:
            logger.error(f"Error checking time condition: {e}")
            return False

    def _award_bonus(self, user_id: int, bonus_type: BonusType, config: BonusConfig, 
                    checkin_time: datetime, streak_data) -> Optional[BonusAward]:
        """Award a bonus to the user"""
        try:
            # Calculate points with multipliers
            base_points = config.base_points
            multiplier = config.multiplier
            
            # Apply streak multiplier
            if bonus_type == BonusType.STREAK_MULTIPLIER:
                streak_multiplier = min(1.0 + (streak_data.current_streak * 0.1), 3.0)
                multiplier *= streak_multiplier
            
            # Apply tier multiplier
            user_tier = self.feature_service.get_user_tier(user_id)
            tier_multiplier = self._get_tier_multiplier(user_tier)
            multiplier *= tier_multiplier
            
            # Calculate final points
            final_points = int(base_points * multiplier)
            
            # Create bonus award record
            bonus_award = BonusAward(
                user_id=user_id,
                bonus_type=bonus_type,
                points_awarded=final_points,
                multiplier_applied=multiplier,
                conditions_met=self._get_met_conditions(bonus_type, config, checkin_time, streak_data),
                awarded_at=checkin_time,
                metadata={
                    'base_points': base_points,
                    'streak_count': streak_data.current_streak,
                    'tier_multiplier': tier_multiplier,
                    'checkin_time': checkin_time.isoformat()
                }
            )
            
            # Record the bonus in database
            self._record_bonus_award(bonus_award)
            
            return bonus_award
            
        except Exception as e:
            logger.error(f"Error awarding bonus: {e}")
            return None

    def _get_tier_multiplier(self, user_tier: FeatureTier) -> float:
        """Get tier-based multiplier for bonuses"""
        tier_multipliers = {
            FeatureTier.BUDGET: 1.0,
            FeatureTier.BUDGET_CAREER_VEHICLE: 1.2,
            FeatureTier.MID_TIER: 1.5,
            FeatureTier.PROFESSIONAL: 2.0
        }
        return tier_multipliers.get(user_tier, 1.0)

    def _get_met_conditions(self, bonus_type: BonusType, config: BonusConfig, 
                          checkin_time: datetime, streak_data) -> List[str]:
        """Get list of conditions that were met for the bonus"""
        conditions = []
        
        if bonus_type == BonusType.DAILY_CHECKIN:
            conditions.append("daily_checkin")
        
        if bonus_type == BonusType.STREAK_MULTIPLIER:
            conditions.append(f"streak_{streak_data.current_streak}_days")
        
        if bonus_type == BonusType.EARLY_BIRD:
            conditions.append("early_morning_checkin")
        
        if bonus_type == BonusType.NIGHT_OWL:
            conditions.append("night_time_checkin")
        
        if bonus_type == BonusType.WEEKEND:
            day_name = checkin_time.strftime("%A").lower()
            conditions.append(f"weekend_{day_name}")
        
        return conditions

    def _record_bonus_award(self, bonus_award: BonusAward):
        """Record bonus award in database"""
        try:
            # This would create a record in the bonus_awards table
            # For now, we'll log the award
            logger.info(f"Bonus awarded: {bonus_award.bonus_type.value} - {bonus_award.points_awarded} points to user {bonus_award.user_id}")
            
        except Exception as e:
            logger.error(f"Error recording bonus award: {e}")

    def _get_daily_bonus_usage(self, user_id: int, bonus_type: BonusType, date: date) -> int:
        """Get daily usage count for a bonus type"""
        try:
            # This would query the bonus_awards table
            # For now, return 0
            return 0
            
        except Exception as e:
            logger.error(f"Error getting daily bonus usage: {e}")
            return 0

    def _get_last_bonus_usage(self, user_id: int, bonus_type: BonusType) -> Optional[datetime]:
        """Get last usage time for a bonus type"""
        try:
            # This would query the bonus_awards table
            # For now, return None
            return None
            
        except Exception as e:
            logger.error(f"Error getting last bonus usage: {e}")
            return None

    # ============================================================================
    # WEEKLY CHALLENGE BONUSES
    # ============================================================================

    def calculate_weekly_challenge_bonuses(self, user_id: int) -> List[BonusAward]:
        """Calculate bonuses for weekly challenge participation"""
        try:
            bonuses = []
            
            # Get user's weekly challenges
            challenges = self.gamification_service.get_weekly_challenges(user_id)
            
            for challenge in challenges:
                if challenge.current_progress >= challenge.target:
                    # Challenge completed - award bonus
                    bonus_award = BonusAward(
                        user_id=user_id,
                        bonus_type=BonusType.SPECIAL_EVENT,
                        points_awarded=challenge.points_reward or 50,
                        multiplier_applied=1.0,
                        conditions_met=[f"challenge_{challenge.id}_completed"],
                        awarded_at=datetime.now(),
                        metadata={
                            'challenge_id': challenge.id,
                            'challenge_title': challenge.title,
                            'target_achieved': challenge.target
                        }
                    )
                    bonuses.append(bonus_award)
            
            return bonuses
            
        except Exception as e:
            logger.error(f"Error calculating weekly challenge bonuses: {e}")
            return []

    # ============================================================================
    # MONTHLY SUMMARY BONUSES
    # ============================================================================

    def calculate_monthly_bonuses(self, user_id: int, month: int, year: int) -> List[BonusAward]:
        """Calculate monthly summary bonuses"""
        try:
            bonuses = []
            
            # Get monthly engagement data
            engagement_data = self._get_monthly_engagement(user_id, month, year)
            
            # Perfect month bonus (30+ days of check-ins)
            if engagement_data['checkin_days'] >= 30:
                bonus_award = BonusAward(
                    user_id=user_id,
                    bonus_type=BonusType.SPECIAL_EVENT,
                    points_awarded=100,
                    multiplier_applied=1.0,
                    conditions_met=["perfect_month"],
                    awarded_at=datetime.now(),
                    metadata={
                        'month': month,
                        'year': year,
                        'checkin_days': engagement_data['checkin_days']
                    }
                )
                bonuses.append(bonus_award)
            
            # Consistency bonus (80%+ check-in rate)
            checkin_rate = engagement_data['checkin_days'] / 30
            if checkin_rate >= 0.8:
                bonus_award = BonusAward(
                    user_id=user_id,
                    bonus_type=BonusType.ENGAGEMENT,
                    points_awarded=50,
                    multiplier_applied=checkin_rate,
                    conditions_met=["high_consistency"],
                    awarded_at=datetime.now(),
                    metadata={
                        'month': month,
                        'year': year,
                        'checkin_rate': checkin_rate
                    }
                )
                bonuses.append(bonus_award)
            
            return bonuses
            
        except Exception as e:
            logger.error(f"Error calculating monthly bonuses: {e}")
            return []

    def _get_monthly_engagement(self, user_id: int, month: int, year: int) -> Dict:
        """Get monthly engagement data"""
        try:
            # This would query the daily_engagement table
            # For now, return mock data
            return {
                'checkin_days': 25,
                'total_points': 500,
                'average_rating': 4.2,
                'streak_high': 15
            }
            
        except Exception as e:
            logger.error(f"Error getting monthly engagement: {e}")
            return {}

    # ============================================================================
    # TIER-SPECIFIC REWARDS
    # ============================================================================

    def get_tier_specific_bonuses(self, user_id: int) -> List[Dict]:
        """Get tier-specific bonus opportunities"""
        try:
            user_tier = self.feature_service.get_user_tier(user_id)
            bonuses = []
            
            if user_tier == FeatureTier.BUDGET:
                bonuses.extend([
                    {
                        'name': 'Daily Check-in',
                        'description': '10 points for checking in daily',
                        'points': 10,
                        'available': True
                    },
                    {
                        'name': 'Streak Multiplier',
                        'description': 'Bonus points for maintaining streaks',
                        'points': 5,
                        'available': True
                    }
                ])
            elif user_tier == FeatureTier.BUDGET_CAREER_VEHICLE:
                bonuses.extend([
                    {
                        'name': 'Engagement Bonus',
                        'description': '25 points for high engagement',
                        'points': 25,
                        'available': True
                    },
                    {
                        'name': 'Time-based Bonuses',
                        'description': 'Early bird and night owl bonuses',
                        'points': 15,
                        'available': True
                    }
                ])
            elif user_tier == FeatureTier.MID_TIER:
                bonuses.extend([
                    {
                        'name': 'Social Share Bonus',
                        'description': '30 points for sharing progress',
                        'points': 30,
                        'available': True
                    },
                    {
                        'name': 'Weekend Warrior',
                        'description': '20 points for weekend check-ins',
                        'points': 20,
                        'available': True
                    }
                ])
            elif user_tier == FeatureTier.PROFESSIONAL:
                bonuses.extend([
                    {
                        'name': 'VIP Multiplier',
                        'description': '2x points on all bonuses',
                        'multiplier': 2.0,
                        'available': True
                    },
                    {
                        'name': 'Premium Challenges',
                        'description': 'Exclusive weekly challenges',
                        'points': 100,
                        'available': True
                    }
                ])
            
            return bonuses
            
        except Exception as e:
            logger.error(f"Error getting tier-specific bonuses: {e}")
            return []

    # ============================================================================
    # BONUS HISTORY AND ANALYTICS
    # ============================================================================

    def get_bonus_history(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get user's bonus history"""
        try:
            # This would query the bonus_awards table
            # For now, return mock data
            return [
                {
                    'date': '2024-01-15',
                    'bonus_type': 'daily_checkin',
                    'points': 10,
                    'multiplier': 1.0
                },
                {
                    'date': '2024-01-15',
                    'bonus_type': 'streak_multiplier',
                    'points': 15,
                    'multiplier': 1.5
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting bonus history: {e}")
            return []

    def get_bonus_analytics(self, user_id: int) -> Dict:
        """Get bonus analytics for user"""
        try:
            # This would calculate various bonus metrics
            return {
                'total_bonus_points': 500,
                'daily_average': 16.7,
                'favorite_bonus': 'streak_multiplier',
                'bonus_frequency': 'high',
                'tier_multiplier': 1.2
            }
            
        except Exception as e:
            logger.error(f"Error getting bonus analytics: {e}")
            return {}
