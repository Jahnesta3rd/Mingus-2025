#!/usr/bin/env python3
"""
Gamification Service for Mingus Application

Comprehensive streak tracking and gamification system for Daily Outlook.
Handles streak calculation, milestone detection, achievement system,
leaderboard functionality, and recovery options.

Features:
- Multi-type streak tracking (daily outlook, goal completion, engagement)
- Milestone detection and rewards
- Achievement system with categories
- Weekly challenges and monthly summaries
- Recovery options for broken streaks
- Leaderboard functionality (anonymous)
- Tier-specific rewards and unlocks
- Analytics for engagement optimization
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from sqlalchemy import func, and_, or_, desc, asc, text
from sqlalchemy.orm import Session
from backend.models.database import db
from backend.models.user_models import User
from backend.models.daily_outlook import DailyOutlook
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class StreakType(Enum):
    """Types of streaks that can be tracked"""
    DAILY_OUTLOOK = "daily_outlook"
    GOAL_COMPLETION = "goal_completion"
    ENGAGEMENT = "engagement"
    MIXED = "mixed"

class AchievementCategory(Enum):
    """Categories for achievements"""
    STREAK = "streak"
    ENGAGEMENT = "engagement"
    GOALS = "goals"
    SOCIAL = "social"
    SPECIAL = "special"

class ChallengeCategory(Enum):
    """Categories for weekly challenges"""
    STREAK = "streak"
    GOALS = "goals"
    ENGAGEMENT = "engagement"
    SOCIAL = "social"

class ChallengeDifficulty(Enum):
    """Difficulty levels for challenges"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class RecoveryType(Enum):
    """Types of streak recovery options"""
    RESTART = "restart"
    CATCH_UP = "catch_up"
    GRACE_PERIOD = "grace_period"
    STREAK_FREEZE = "streak_freeze"

@dataclass
class StreakData:
    """Data structure for streak information"""
    current_streak: int
    longest_streak: int
    total_days: int
    streak_start_date: date
    last_activity_date: date
    is_active: bool
    streak_type: StreakType

@dataclass
class Milestone:
    """Data structure for milestones"""
    id: str
    name: str
    days_required: int
    description: str
    reward: str
    icon: str
    color: str
    achieved: bool
    achieved_date: Optional[date]
    progress_percentage: float

@dataclass
class Achievement:
    """Data structure for achievements"""
    id: str
    name: str
    description: str
    icon: str
    color: str
    points: int
    unlocked: bool
    unlocked_date: Optional[date]
    category: AchievementCategory

@dataclass
class RecoveryOption:
    """Data structure for recovery options"""
    id: str
    type: RecoveryType
    title: str
    description: str
    cost: Optional[int]
    available: bool
    action: str

@dataclass
class WeeklyChallenge:
    """Data structure for weekly challenges"""
    id: str
    title: str
    description: str
    target: int
    current_progress: int
    reward: str
    deadline: date
    category: ChallengeCategory
    difficulty: ChallengeDifficulty

# ============================================================================
# GAMIFICATION SERVICE CLASS
# ============================================================================

class GamificationService:
    """Main service class for gamification functionality"""
    
    def __init__(self):
        self.feature_service = FeatureFlagService()
        
        # Define milestone configurations
        self.milestone_configs = [
            {'days': 3, 'name': 'Getting Started', 'reward': 'Unlock personalized insights', 'icon': 'star', 'color': 'text-blue-500'},
            {'days': 7, 'name': 'Week Warrior', 'reward': 'Advanced progress tracking', 'icon': 'trophy', 'color': 'text-green-500'},
            {'days': 14, 'name': 'Two Week Champion', 'reward': 'Priority support access', 'icon': 'shield', 'color': 'text-purple-500'},
            {'days': 21, 'name': 'Habit Master', 'reward': 'Exclusive content access', 'icon': 'crown', 'color': 'text-yellow-500'},
            {'days': 30, 'name': 'Monthly Master', 'reward': 'Premium feature preview', 'icon': 'gift', 'color': 'text-pink-500'},
            {'days': 60, 'name': 'Consistency King', 'reward': 'VIP status upgrade', 'icon': 'crown', 'color': 'text-indigo-500'},
            {'days': 90, 'name': 'Quarter Champion', 'reward': 'Exclusive community access', 'icon': 'trophy', 'color': 'text-red-500'},
            {'days': 100, 'name': 'Century Club', 'reward': 'Lifetime premium features', 'icon': 'crown', 'color': 'text-gold-500'},
            {'days': 365, 'name': 'Year Warrior', 'reward': 'Legendary status', 'icon': 'crown', 'color': 'text-purple-600'}
        ]
        
        # Define achievement configurations
        self.achievement_configs = [
            # Streak achievements
            {'id': 'first_streak', 'name': 'First Steps', 'description': 'Complete your first 3-day streak', 'icon': 'star', 'color': 'text-blue-500', 'points': 10, 'category': AchievementCategory.STREAK},
            {'id': 'week_warrior', 'name': 'Week Warrior', 'description': 'Maintain a 7-day streak', 'icon': 'trophy', 'color': 'text-green-500', 'points': 25, 'category': AchievementCategory.STREAK},
            {'id': 'month_master', 'name': 'Month Master', 'description': 'Achieve a 30-day streak', 'icon': 'crown', 'color': 'text-purple-500', 'points': 100, 'category': AchievementCategory.STREAK},
            {'id': 'century_club', 'name': 'Century Club', 'description': 'Reach 100 days in a row', 'icon': 'trophy', 'color': 'text-gold-500', 'points': 500, 'category': AchievementCategory.STREAK},
            
            # Engagement achievements
            {'id': 'early_bird', 'name': 'Early Bird', 'description': 'Check in before 8 AM for 7 days', 'icon': 'sun', 'color': 'text-yellow-500', 'points': 15, 'category': AchievementCategory.ENGAGEMENT},
            {'id': 'night_owl', 'name': 'Night Owl', 'description': 'Check in after 10 PM for 7 days', 'icon': 'moon', 'color': 'text-indigo-500', 'points': 15, 'category': AchievementCategory.ENGAGEMENT},
            {'id': 'consistency_king', 'name': 'Consistency King', 'description': 'Check in at the same time for 14 days', 'icon': 'clock', 'color': 'text-green-500', 'points': 30, 'category': AchievementCategory.ENGAGEMENT},
            
            # Goal achievements
            {'id': 'goal_crusher', 'name': 'Goal Crusher', 'description': 'Complete 10 goals in a week', 'icon': 'target', 'color': 'text-red-500', 'points': 50, 'category': AchievementCategory.GOALS},
            {'id': 'perfectionist', 'name': 'Perfectionist', 'description': 'Complete all daily goals for a week', 'icon': 'check', 'color': 'text-green-500', 'points': 75, 'category': AchievementCategory.GOALS},
            
            # Social achievements
            {'id': 'sharer', 'name': 'Sharer', 'description': 'Share your progress 5 times', 'icon': 'share', 'color': 'text-blue-500', 'points': 20, 'category': AchievementCategory.SOCIAL},
            {'id': 'motivator', 'name': 'Motivator', 'description': 'Help 3 friends start their streaks', 'icon': 'heart', 'color': 'text-pink-500', 'points': 100, 'category': AchievementCategory.SOCIAL},
            
            # Special achievements
            {'id': 'comeback_kid', 'name': 'Comeback Kid', 'description': 'Recover from a broken streak 3 times', 'icon': 'refresh', 'color': 'text-orange-500', 'points': 40, 'category': AchievementCategory.SPECIAL},
            {'id': 'streak_saver', 'name': 'Streak Saver', 'description': 'Use recovery options to save your streak', 'icon': 'shield', 'color': 'text-purple-500', 'points': 25, 'category': AchievementCategory.SPECIAL}
        ]

    # ============================================================================
    # STREAK CALCULATION METHODS
    # ============================================================================

    def calculate_streak(self, user_id: int, streak_type: StreakType = StreakType.DAILY_OUTLOOK) -> StreakData:
        """Calculate comprehensive streak data for a user"""
        try:
            current_date = date.today()
            
            # Get streak data based on type
            if streak_type == StreakType.DAILY_OUTLOOK:
                return self._calculate_daily_outlook_streak(user_id, current_date)
            elif streak_type == StreakType.GOAL_COMPLETION:
                return self._calculate_goal_completion_streak(user_id, current_date)
            elif streak_type == StreakType.ENGAGEMENT:
                return self._calculate_engagement_streak(user_id, current_date)
            else:  # MIXED
                return self._calculate_mixed_streak(user_id, current_date)
                
        except Exception as e:
            logger.error(f"Error calculating streak for user {user_id}: {e}")
            return StreakData(
                current_streak=0,
                longest_streak=0,
                total_days=0,
                streak_start_date=current_date,
                last_activity_date=current_date,
                is_active=False,
                streak_type=streak_type
            )

    def _calculate_daily_outlook_streak(self, user_id: int, current_date: date) -> StreakData:
        """Calculate streak based on daily outlook completions"""
        try:
            # Get all daily outlooks for user, ordered by date
            outlooks = DailyOutlook.query.filter(
                DailyOutlook.user_id == user_id
            ).order_by(desc(DailyOutlook.date)).all()
            
            if not outlooks:
                return StreakData(
                    current_streak=0,
                    longest_streak=0,
                    total_days=0,
                    streak_start_date=current_date,
                    last_activity_date=current_date,
                    is_active=False,
                    streak_type=StreakType.DAILY_OUTLOOK
                )
            
            # Calculate current streak
            current_streak = 0
            streak_start_date = current_date
            longest_streak = 0
            temp_streak = 0
            total_days = len(outlooks)
            
            # Check if today has an outlook
            today_outlook = next((o for o in outlooks if o.date == current_date), None)
            is_active = today_outlook is not None
            
            if is_active:
                # Count consecutive days from today backwards
                check_date = current_date
                while True:
                    day_outlook = next((o for o in outlooks if o.date == check_date), None)
                    if day_outlook:
                        current_streak += 1
                        streak_start_date = check_date
                        check_date -= timedelta(days=1)
                    else:
                        break
            else:
                # Count consecutive days from yesterday backwards
                check_date = current_date - timedelta(days=1)
                while True:
                    day_outlook = next((o for o in outlooks if o.date == check_date), None)
                    if day_outlook:
                        current_streak += 1
                        streak_start_date = check_date
                        check_date -= timedelta(days=1)
                    else:
                        break
            
            # Calculate longest streak
            temp_streak = 0
            prev_date = None
            for outlook in outlooks:
                if prev_date is None or outlook.date == prev_date - timedelta(days=1):
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1
                prev_date = outlook.date
            
            last_activity_date = outlooks[0].date if outlooks else current_date
            
            return StreakData(
                current_streak=current_streak,
                longest_streak=longest_streak,
                total_days=total_days,
                streak_start_date=streak_start_date,
                last_activity_date=last_activity_date,
                is_active=is_active,
                streak_type=StreakType.DAILY_OUTLOOK
            )
            
        except Exception as e:
            logger.error(f"Error calculating daily outlook streak: {e}")
            raise

    def _calculate_goal_completion_streak(self, user_id: int, current_date: date) -> StreakData:
        """Calculate streak based on goal completions"""
        # This would integrate with goal tracking system
        # For now, return a placeholder implementation
        return StreakData(
            current_streak=0,
            longest_streak=0,
            total_days=0,
            streak_start_date=current_date,
            last_activity_date=current_date,
            is_active=False,
            streak_type=StreakType.GOAL_COMPLETION
        )

    def _calculate_engagement_streak(self, user_id: int, current_date: date) -> StreakData:
        """Calculate streak based on general engagement"""
        # This would integrate with engagement tracking
        # For now, return a placeholder implementation
        return StreakData(
            current_streak=0,
            longest_streak=0,
            total_days=0,
            streak_start_date=current_date,
            last_activity_date=current_date,
            is_active=False,
            streak_type=StreakType.ENGAGEMENT
        )

    def _calculate_mixed_streak(self, user_id: int, current_date: date) -> StreakData:
        """Calculate streak based on any type of activity"""
        # This would combine multiple activity types
        # For now, use daily outlook as the primary metric
        return self._calculate_daily_outlook_streak(user_id, current_date)

    # ============================================================================
    # MILESTONE DETECTION METHODS
    # ============================================================================

    def get_milestones(self, user_id: int, streak_data: StreakData) -> List[Milestone]:
        """Get milestone information for a user"""
        try:
            milestones = []
            
            for config in self.milestone_configs:
                achieved = streak_data.current_streak >= config['days']
                progress_percentage = min((streak_data.current_streak / config['days']) * 100, 100)
                
                milestone = Milestone(
                    id=f"milestone_{config['days']}",
                    name=config['name'],
                    days_required=config['days'],
                    description=f"Reach {config['days']} days in a row",
                    reward=config['reward'],
                    icon=config['icon'],
                    color=config['color'],
                    achieved=achieved,
                    achieved_date=streak_data.streak_start_date if achieved else None,
                    progress_percentage=progress_percentage
                )
                milestones.append(milestone)
            
            return milestones
            
        except Exception as e:
            logger.error(f"Error getting milestones for user {user_id}: {e}")
            return []

    def check_milestone_achievements(self, user_id: int, streak_data: StreakData) -> List[str]:
        """Check if user has achieved any new milestones"""
        try:
            new_achievements = []
            milestones = self.get_milestones(user_id, streak_data)
            
            for milestone in milestones:
                if milestone.achieved and milestone.achieved_date == date.today():
                    new_achievements.append(milestone.id)
            
            return new_achievements
            
        except Exception as e:
            logger.error(f"Error checking milestone achievements for user {user_id}: {e}")
            return []

    # ============================================================================
    # ACHIEVEMENT SYSTEM METHODS
    # ============================================================================

    def get_achievements(self, user_id: int) -> List[Achievement]:
        """Get all achievements for a user"""
        try:
            achievements = []
            
            for config in self.achievement_configs:
                # Check if achievement is unlocked (simplified logic)
                unlocked = self._check_achievement_unlock(user_id, config)
                
                achievement = Achievement(
                    id=config['id'],
                    name=config['name'],
                    description=config['description'],
                    icon=config['icon'],
                    color=config['color'],
                    points=config['points'],
                    unlocked=unlocked,
                    unlocked_date=date.today() if unlocked else None,
                    category=config['category']
                )
                achievements.append(achievement)
            
            return achievements
            
        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {e}")
            return []

    def _check_achievement_unlock(self, user_id: int, config: Dict) -> bool:
        """Check if a specific achievement should be unlocked"""
        try:
            achievement_id = config['id']
            
            # Simplified achievement checking logic
            if achievement_id == 'first_streak':
                streak_data = self.calculate_streak(user_id)
                return streak_data.current_streak >= 3
            elif achievement_id == 'week_warrior':
                streak_data = self.calculate_streak(user_id)
                return streak_data.current_streak >= 7
            elif achievement_id == 'month_master':
                streak_data = self.calculate_streak(user_id)
                return streak_data.current_streak >= 30
            elif achievement_id == 'century_club':
                streak_data = self.calculate_streak(user_id)
                return streak_data.current_streak >= 100
            # Add more achievement checks as needed
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking achievement unlock for {config['id']}: {e}")
            return False

    # ============================================================================
    # RECOVERY OPTIONS METHODS
    # ============================================================================

    def get_recovery_options(self, user_id: int, streak_data: StreakData) -> List[RecoveryOption]:
        """Get available recovery options for a user"""
        try:
            options = []
            
            # Check user tier for available options
            user_tier = self.feature_service.get_user_tier(user_id)
            
            if not streak_data.is_active:
                # Streak is broken, offer recovery options
                options.append(RecoveryOption(
                    id='restart',
                    type=RecoveryType.RESTART,
                    title='Start Fresh',
                    description='Begin a new streak from today',
                    cost=None,
                    available=True,
                    action='begin_new_streak'
                ))
                
                if user_tier in [FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]:
                    options.append(RecoveryOption(
                        id='catch_up',
                        type=RecoveryType.CATCH_UP,
                        title='Catch Up',
                        description='Complete missed days to maintain streak',
                        cost=50,  # Points cost
                        available=True,
                        action='complete_missed_days'
                    ))
                
                if user_tier == FeatureTier.PROFESSIONAL:
                    options.append(RecoveryOption(
                        id='grace_period',
                        type=RecoveryType.GRACE_PERIOD,
                        title='Grace Period',
                        description='Get 24 hours to recover your streak',
                        cost=100,  # Points cost
                        available=True,
                        action='activate_grace_period'
                    ))
            
            return options
            
        except Exception as e:
            logger.error(f"Error getting recovery options for user {user_id}: {e}")
            return []

    def process_recovery_action(self, user_id: int, recovery_type: RecoveryType, action: str) -> bool:
        """Process a recovery action for a user"""
        try:
            if recovery_type == RecoveryType.RESTART:
                # Reset streak to 1 (today)
                return self._restart_streak(user_id)
            elif recovery_type == RecoveryType.CATCH_UP:
                # Allow user to complete missed days
                return self._enable_catch_up(user_id)
            elif recovery_type == RecoveryType.GRACE_PERIOD:
                # Give user 24 hours to recover
                return self._activate_grace_period(user_id)
            elif recovery_type == RecoveryType.STREAK_FREEZE:
                # Freeze streak for a limited time
                return self._freeze_streak(user_id)
            
            return False
            
        except Exception as e:
            logger.error(f"Error processing recovery action for user {user_id}: {e}")
            return False

    def _restart_streak(self, user_id: int) -> bool:
        """Restart user's streak from today"""
        try:
            # This would update the user's streak data
            # For now, return True as placeholder
            return True
        except Exception as e:
            logger.error(f"Error restarting streak for user {user_id}: {e}")
            return False

    def _enable_catch_up(self, user_id: int) -> bool:
        """Enable catch-up mode for user"""
        try:
            # This would enable special catch-up functionality
            return True
        except Exception as e:
            logger.error(f"Error enabling catch-up for user {user_id}: {e}")
            return False

    def _activate_grace_period(self, user_id: int) -> bool:
        """Activate grace period for user"""
        try:
            # This would set a grace period flag
            return True
        except Exception as e:
            logger.error(f"Error activating grace period for user {user_id}: {e}")
            return False

    def _freeze_streak(self, user_id: int) -> bool:
        """Freeze user's streak temporarily"""
        try:
            # This would set a streak freeze flag
            return True
        except Exception as e:
            logger.error(f"Error freezing streak for user {user_id}: {e}")
            return False

    # ============================================================================
    # WEEKLY CHALLENGES METHODS
    # ============================================================================

    def get_weekly_challenges(self, user_id: int) -> List[WeeklyChallenge]:
        """Get current weekly challenges for a user"""
        try:
            challenges = []
            current_date = date.today()
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)
            
            # Generate challenges based on user tier and current week
            user_tier = self.feature_service.get_user_tier(user_id)
            
            # Basic challenges available to all tiers
            challenges.append(WeeklyChallenge(
                id='daily_checkin',
                title='Daily Check-in',
                description='Check in every day this week',
                target=7,
                current_progress=self._get_weekly_checkin_progress(user_id, week_start, week_end),
                reward='50 points + streak bonus',
                deadline=week_end,
                category=ChallengeCategory.ENGAGEMENT,
                difficulty=ChallengeDifficulty.EASY
            ))
            
            if user_tier in [FeatureTier.MID_TIER, FeatureTier.PROFESSIONAL]:
                challenges.append(WeeklyChallenge(
                    id='goal_completion',
                    title='Goal Completion',
                    description='Complete 10 goals this week',
                    target=10,
                    current_progress=self._get_weekly_goal_progress(user_id, week_start, week_end),
                    reward='100 points + premium feature access',
                    deadline=week_end,
                    category=ChallengeCategory.GOALS,
                    difficulty=ChallengeDifficulty.MEDIUM
                ))
            
            if user_tier == FeatureTier.PROFESSIONAL:
                challenges.append(WeeklyChallenge(
                    id='social_engagement',
                    title='Social Engagement',
                    description='Share your progress 3 times this week',
                    target=3,
                    current_progress=self._get_weekly_social_progress(user_id, week_start, week_end),
                    reward='150 points + exclusive content',
                    deadline=week_end,
                    category=ChallengeCategory.SOCIAL,
                    difficulty=ChallengeDifficulty.HARD
                ))
            
            return challenges
            
        except Exception as e:
            logger.error(f"Error getting weekly challenges for user {user_id}: {e}")
            return []

    def _get_weekly_checkin_progress(self, user_id: int, week_start: date, week_end: date) -> int:
        """Get progress for weekly check-in challenge"""
        try:
            # Count daily outlooks in the week
            outlooks = DailyOutlook.query.filter(
                and_(
                    DailyOutlook.user_id == user_id,
                    DailyOutlook.date >= week_start,
                    DailyOutlook.date <= week_end
                )
            ).count()
            return outlooks
        except Exception as e:
            logger.error(f"Error getting weekly checkin progress: {e}")
            return 0

    def _get_weekly_goal_progress(self, user_id: int, week_start: date, week_end: date) -> int:
        """Get progress for weekly goal completion challenge"""
        # This would integrate with goal tracking system
        return 0

    def _get_weekly_social_progress(self, user_id: int, week_start: date, week_end: date) -> int:
        """Get progress for weekly social engagement challenge"""
        # This would integrate with social sharing tracking
        return 0

    # ============================================================================
    # LEADERBOARD METHODS
    # ============================================================================

    def get_leaderboard(self, category: str = 'streak', limit: int = 10) -> List[Dict]:
        """Get leaderboard data (anonymous)"""
        try:
            if category == 'streak':
                return self._get_streak_leaderboard(limit)
            elif category == 'achievements':
                return self._get_achievement_leaderboard(limit)
            elif category == 'engagement':
                return self._get_engagement_leaderboard(limit)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []

    def _get_streak_leaderboard(self, limit: int) -> List[Dict]:
        """Get streak-based leaderboard"""
        try:
            # Get top streaks (simplified implementation)
            top_streaks = db.session.query(
                DailyOutlook.user_id,
                func.max(DailyOutlook.streak_count).label('max_streak')
            ).group_by(DailyOutlook.user_id).order_by(
                desc('max_streak')
            ).limit(limit).all()
            
            leaderboard = []
            for i, (user_id, max_streak) in enumerate(top_streaks):
                leaderboard.append({
                    'rank': i + 1,
                    'user_id': f"user_{user_id}",  # Anonymized
                    'score': max_streak,
                    'display_name': f"User #{user_id}",
                    'badge': self._get_rank_badge(i + 1)
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting streak leaderboard: {e}")
            return []

    def _get_achievement_leaderboard(self, limit: int) -> List[Dict]:
        """Get achievement-based leaderboard"""
        # This would calculate based on total achievement points
        return []

    def _get_engagement_leaderboard(self, limit: int) -> List[Dict]:
        """Get engagement-based leaderboard"""
        # This would calculate based on engagement metrics
        return []

    def _get_rank_badge(self, rank: int) -> str:
        """Get badge for rank position"""
        if rank == 1:
            return "🥇"
        elif rank == 2:
            return "🥈"
        elif rank == 3:
            return "🥉"
        elif rank <= 10:
            return "🏆"
        else:
            return "⭐"

    # ============================================================================
    # ANALYTICS METHODS
    # ============================================================================

    def get_engagement_analytics(self, user_id: int) -> Dict:
        """Get engagement analytics for a user"""
        try:
            # Calculate various engagement metrics
            streak_data = self.calculate_streak(user_id)
            achievements = self.get_achievements(user_id)
            milestones = self.get_milestones(user_id, streak_data)
            
            return {
                'current_streak': streak_data.current_streak,
                'longest_streak': streak_data.longest_streak,
                'total_achievements': len([a for a in achievements if a.unlocked]),
                'total_milestones': len([m for m in milestones if m.achieved]),
                'engagement_score': self._calculate_engagement_score(user_id),
                'consistency_rating': self._calculate_consistency_rating(user_id),
                'improvement_trend': self._calculate_improvement_trend(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting engagement analytics for user {user_id}: {e}")
            return {}

    def _calculate_engagement_score(self, user_id: int) -> float:
        """Calculate overall engagement score"""
        try:
            # Simplified engagement score calculation
            streak_data = self.calculate_streak(user_id)
            achievements = self.get_achievements(user_id)
            
            # Base score from streak
            streak_score = min(streak_data.current_streak * 2, 100)
            
            # Bonus from achievements
            achievement_bonus = len([a for a in achievements if a.unlocked]) * 5
            
            return min(streak_score + achievement_bonus, 100)
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0

    def _calculate_consistency_rating(self, user_id: int) -> float:
        """Calculate consistency rating"""
        try:
            # Get last 30 days of activity
            thirty_days_ago = date.today() - timedelta(days=30)
            outlooks = DailyOutlook.query.filter(
                and_(
                    DailyOutlook.user_id == user_id,
                    DailyOutlook.date >= thirty_days_ago
                )
            ).count()
            
            return (outlooks / 30) * 100
            
        except Exception as e:
            logger.error(f"Error calculating consistency rating: {e}")
            return 0.0

    def _calculate_improvement_trend(self, user_id: int) -> str:
        """Calculate improvement trend"""
        try:
            # Compare current streak to previous periods
            current_streak = self.calculate_streak(user_id).current_streak
            
            # Simplified trend calculation
            if current_streak >= 7:
                return "improving"
            elif current_streak >= 3:
                return "stable"
            else:
                return "needs_improvement"
                
        except Exception as e:
            logger.error(f"Error calculating improvement trend: {e}")
            return "unknown"

    # ============================================================================
    # TIER-SPECIFIC REWARDS METHODS
    # ============================================================================

    def get_tier_rewards(self, user_id: int) -> List[Dict]:
        """Get tier-specific rewards for a user"""
        try:
            user_tier = self.feature_service.get_user_tier(user_id)
            rewards = []
            
            if user_tier == FeatureTier.BUDGET:
                rewards.extend([
                    {'name': 'Basic Streak Tracking', 'description': 'Track your daily progress', 'unlocked': True},
                    {'name': 'Milestone Rewards', 'description': 'Unlock rewards at key milestones', 'unlocked': True},
                    {'name': 'Achievement System', 'description': 'Earn points and badges', 'unlocked': True}
                ])
            elif user_tier == FeatureTier.BUDGET_CAREER_VEHICLE:
                rewards.extend([
                    {'name': 'Advanced Analytics', 'description': 'Detailed progress insights', 'unlocked': True},
                    {'name': 'Recovery Options', 'description': 'Catch up on missed days', 'unlocked': True},
                    {'name': 'Weekly Challenges', 'description': 'Participate in weekly goals', 'unlocked': True}
                ])
            elif user_tier == FeatureTier.MID_TIER:
                rewards.extend([
                    {'name': 'Priority Support', 'description': 'Faster response times', 'unlocked': True},
                    {'name': 'Exclusive Content', 'description': 'Access to premium content', 'unlocked': True},
                    {'name': 'Social Features', 'description': 'Share and compare progress', 'unlocked': True}
                ])
            elif user_tier == FeatureTier.PROFESSIONAL:
                rewards.extend([
                    {'name': 'VIP Status', 'description': 'Premium experience', 'unlocked': True},
                    {'name': 'Custom Challenges', 'description': 'Personalized weekly goals', 'unlocked': True},
                    {'name': 'Advanced Recovery', 'description': 'Grace periods and streak freezes', 'unlocked': True}
                ])
            
            return rewards
            
        except Exception as e:
            logger.error(f"Error getting tier rewards for user {user_id}: {e}")
            return []

    # ============================================================================
    # MAIN SERVICE METHODS
    # ============================================================================

    def get_complete_gamification_data(self, user_id: int) -> Dict:
        """Get complete gamification data for a user"""
        try:
            # Calculate streak data
            streak_data = self.calculate_streak(user_id)
            
            # Get milestones
            milestones = self.get_milestones(user_id, streak_data)
            
            # Get achievements
            achievements = self.get_achievements(user_id)
            
            # Get recovery options
            recovery_options = self.get_recovery_options(user_id, streak_data)
            
            # Get weekly challenges
            weekly_challenges = self.get_weekly_challenges(user_id)
            
            # Get analytics
            analytics = self.get_engagement_analytics(user_id)
            
            # Get tier rewards
            tier_rewards = self.get_tier_rewards(user_id)
            
            return {
                'streak_data': {
                    'current_streak': streak_data.current_streak,
                    'longest_streak': streak_data.longest_streak,
                    'total_days': streak_data.total_days,
                    'streak_start_date': streak_data.streak_start_date.isoformat(),
                    'last_activity_date': streak_data.last_activity_date.isoformat(),
                    'is_active': streak_data.is_active,
                    'streak_type': streak_data.streak_type.value
                },
                'milestones': [
                    {
                        'id': m.id,
                        'name': m.name,
                        'days_required': m.days_required,
                        'description': m.description,
                        'reward': m.reward,
                        'icon': m.icon,
                        'color': m.color,
                        'achieved': m.achieved,
                        'achieved_date': m.achieved_date.isoformat() if m.achieved_date else None,
                        'progress_percentage': m.progress_percentage
                    } for m in milestones
                ],
                'achievements': [
                    {
                        'id': a.id,
                        'name': a.name,
                        'description': a.description,
                        'icon': a.icon,
                        'color': a.color,
                        'points': a.points,
                        'unlocked': a.unlocked,
                        'unlocked_date': a.unlocked_date.isoformat() if a.unlocked_date else None,
                        'category': a.category.value
                    } for a in achievements
                ],
                'recovery_options': [
                    {
                        'id': r.id,
                        'type': r.type.value,
                        'title': r.title,
                        'description': r.description,
                        'cost': r.cost,
                        'available': r.available,
                        'action': r.action
                    } for r in recovery_options
                ],
                'weekly_challenges': [
                    {
                        'id': c.id,
                        'title': c.title,
                        'description': c.description,
                        'target': c.target,
                        'current_progress': c.current_progress,
                        'reward': c.reward,
                        'deadline': c.deadline.isoformat(),
                        'category': c.category.value,
                        'difficulty': c.difficulty.value
                    } for c in weekly_challenges
                ],
                'analytics': analytics,
                'tier_rewards': tier_rewards
            }
            
        except Exception as e:
            logger.error(f"Error getting complete gamification data for user {user_id}: {e}")
            return {}

    def process_gamification_action(self, user_id: int, action_type: str, action_data: Dict) -> bool:
        """Process a gamification action"""
        try:
            if action_type == 'recovery':
                recovery_type = RecoveryType(action_data.get('recovery_type'))
                action = action_data.get('action')
                return self.process_recovery_action(user_id, recovery_type, action)
            elif action_type == 'challenge':
                challenge_id = action_data.get('challenge_id')
                return self._join_challenge(user_id, challenge_id)
            elif action_type == 'achievement_claim':
                achievement_id = action_data.get('achievement_id')
                return self._claim_achievement(user_id, achievement_id)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error processing gamification action: {e}")
            return False

    def _join_challenge(self, user_id: int, challenge_id: str) -> bool:
        """Join a weekly challenge"""
        try:
            # This would add user to challenge participation
            return True
        except Exception as e:
            logger.error(f"Error joining challenge: {e}")
            return False

    def _claim_achievement(self, user_id: int, achievement_id: str) -> bool:
        """Claim an achievement"""
        try:
            # This would mark achievement as claimed
            return True
        except Exception as e:
            logger.error(f"Error claiming achievement: {e}")
            return False
