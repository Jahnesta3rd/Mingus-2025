#!/usr/bin/env python3
"""
Gamification Models for Mingus Application

Database models for streak tracking and gamification system.
Includes user streaks, achievements, daily engagement metrics,
milestone tracking, and weekly challenges.
"""

from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.models.database import db
import uuid

# ============================================================================
# ENUMS
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

# ============================================================================
# USER STREAKS TABLE
# ============================================================================

class UserStreak(db.Model):
    """Track user streaks across different activity types"""
    __tablename__ = 'user_streaks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    streak_type = Column(String(50), nullable=False, default='daily_outlook')
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    total_days = Column(Integer, default=0, nullable=False)
    streak_start_date = Column(Date, nullable=False)
    last_activity_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    streak_frozen = Column(Boolean, default=False, nullable=False)
    freeze_expires_at = Column(DateTime, nullable=True)
    grace_period_active = Column(Boolean, default=False, nullable=False)
    grace_period_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="streaks")
    milestone_achievements = relationship("MilestoneAchievement", back_populates="streak")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'streak_type': self.streak_type,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'total_days': self.total_days,
            'streak_start_date': self.streak_start_date.isoformat() if self.streak_start_date else None,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'is_active': self.is_active,
            'streak_frozen': self.streak_frozen,
            'freeze_expires_at': self.freeze_expires_at.isoformat() if self.freeze_expires_at else None,
            'grace_period_active': self.grace_period_active,
            'grace_period_expires_at': self.grace_period_expires_at.isoformat() if self.grace_period_expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ============================================================================
# ACHIEVEMENTS TABLE
# ============================================================================

class Achievement(db.Model):
    """Define available achievements"""
    __tablename__ = 'achievements'
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(50), nullable=False)
    color = Column(String(50), nullable=False)
    points = Column(Integer, default=0, nullable=False)
    category = Column(String(50), nullable=False)
    unlock_conditions = Column(JSON, nullable=True)  # Store conditions as JSON
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'points': self.points,
            'category': self.category,
            'unlock_conditions': self.unlock_conditions,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserAchievement(db.Model):
    """Track user achievement unlocks"""
    __tablename__ = 'user_achievements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    achievement_id = Column(String(100), ForeignKey('achievements.id'), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    points_awarded = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None,
            'claimed_at': self.claimed_at.isoformat() if self.claimed_at else None,
            'points_awarded': self.points_awarded,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ============================================================================
# MILESTONES TABLE
# ============================================================================

class Milestone(db.Model):
    """Define milestone configurations"""
    __tablename__ = 'milestones'
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    days_required = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    reward = Column(String(500), nullable=False)
    icon = Column(String(50), nullable=False)
    color = Column(String(50), nullable=False)
    points_reward = Column(Integer, default=0, nullable=False)
    tier_requirement = Column(String(50), nullable=True)  # Minimum tier required
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    milestone_achievements = relationship("MilestoneAchievement", back_populates="milestone")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'days_required': self.days_required,
            'description': self.description,
            'reward': self.reward,
            'icon': self.icon,
            'color': self.color,
            'points_reward': self.points_reward,
            'tier_requirement': self.tier_requirement,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MilestoneAchievement(db.Model):
    """Track user milestone achievements"""
    __tablename__ = 'milestone_achievements'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    milestone_id = Column(String(100), ForeignKey('milestones.id'), nullable=False)
    streak_id = Column(Integer, ForeignKey('user_streaks.id'), nullable=True)
    achieved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    points_awarded = Column(Integer, default=0, nullable=False)
    reward_claimed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="milestone_achievements")
    milestone = relationship("Milestone", back_populates="milestone_achievements")
    streak = relationship("UserStreak", back_populates="milestone_achievements")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'milestone_id': self.milestone_id,
            'streak_id': self.streak_id,
            'achieved_at': self.achieved_at.isoformat() if self.achieved_at else None,
            'points_awarded': self.points_awarded,
            'reward_claimed': self.reward_claimed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ============================================================================
# DAILY ENGAGEMENT METRICS TABLE
# ============================================================================

class DailyEngagement(db.Model):
    """Track daily engagement metrics"""
    __tablename__ = 'daily_engagement'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    engagement_date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 rating
    goals_completed = Column(Integer, default=0, nullable=False)
    actions_completed = Column(Integer, default=0, nullable=False)
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    engagement_score = Column(Float, default=0.0, nullable=False)
    mood_score = Column(Integer, nullable=True)  # 1-10 mood rating
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional engagement data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="daily_engagement")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'engagement_date': self.engagement_date.isoformat() if self.engagement_date else None,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'rating': self.rating,
            'goals_completed': self.goals_completed,
            'actions_completed': self.actions_completed,
            'time_spent_minutes': self.time_spent_minutes,
            'engagement_score': self.engagement_score,
            'mood_score': self.mood_score,
            'notes': self.notes,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ============================================================================
# WEEKLY CHALLENGES TABLE
# ============================================================================

class WeeklyChallenge(db.Model):
    """Define weekly challenges"""
    __tablename__ = 'weekly_challenges'
    
    id = Column(String(100), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    target_value = Column(Integer, nullable=False)
    reward_description = Column(String(500), nullable=False)
    points_reward = Column(Integer, default=0, nullable=False)
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False)
    tier_requirement = Column(String(50), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    max_participants = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    challenge_participants = relationship("ChallengeParticipant", back_populates="challenge")
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'target_value': self.target_value,
            'reward_description': self.reward_description,
            'points_reward': self.points_reward,
            'category': self.category,
            'difficulty': self.difficulty,
            'tier_requirement': self.tier_requirement,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'max_participants': self.max_participants,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ChallengeParticipant(db.Model):
    """Track user participation in weekly challenges"""
    __tablename__ = 'challenge_participants'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    challenge_id = Column(String(100), ForeignKey('weekly_challenges.id'), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    current_progress = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    reward_claimed = Column(Boolean, default=False, nullable=False)
    points_awarded = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="challenge_participations")
    challenge = relationship("WeeklyChallenge", back_populates="challenge_participants")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'challenge_id': self.challenge_id,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'current_progress': self.current_progress,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'reward_claimed': self.reward_claimed,
            'points_awarded': self.points_awarded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ============================================================================
# RECOVERY OPTIONS TABLE
# ============================================================================

class RecoveryOption(db.Model):
    """Define streak recovery options"""
    __tablename__ = 'recovery_options'
    
    id = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    recovery_type = Column(String(50), nullable=False)
    cost_points = Column(Integer, default=0, nullable=False)
    cost_money = Column(Float, default=0.0, nullable=False)
    tier_requirement = Column(String(50), nullable=True)
    cooldown_hours = Column(Integer, default=24, nullable=False)
    max_uses_per_month = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    recovery_usage = relationship("RecoveryUsage", back_populates="recovery_option")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'recovery_type': self.recovery_type,
            'cost_points': self.cost_points,
            'cost_money': self.cost_money,
            'tier_requirement': self.tier_requirement,
            'cooldown_hours': self.cooldown_hours,
            'max_uses_per_month': self.max_uses_per_month,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RecoveryUsage(db.Model):
    """Track user usage of recovery options"""
    __tablename__ = 'recovery_usage'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    recovery_option_id = Column(String(100), ForeignKey('recovery_options.id'), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cost_paid = Column(Integer, default=0, nullable=False)
    success = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="recovery_usage")
    recovery_option = relationship("RecoveryOption", back_populates="recovery_usage")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recovery_option_id': self.recovery_option_id,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'cost_paid': self.cost_paid,
            'success': self.success,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# ============================================================================
# LEADERBOARD TABLE
# ============================================================================

class LeaderboardEntry(db.Model):
    """Store leaderboard data for performance"""
    __tablename__ = 'leaderboard_entries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # streak, achievements, engagement
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="leaderboard_entries")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'score': self.score,
            'rank': self.rank,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ============================================================================
# USER POINTS TABLE
# ============================================================================

class UserPoints(db.Model):
    """Track user points and rewards"""
    __tablename__ = 'user_points'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    total_points = Column(Integer, default=0, nullable=False)
    available_points = Column(Integer, default=0, nullable=False)
    lifetime_points = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="points")
    point_transactions = relationship("PointTransaction", back_populates="user_points")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_points': self.total_points,
            'available_points': self.available_points,
            'lifetime_points': self.lifetime_points,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class PointTransaction(db.Model):
    """Track point transactions"""
    __tablename__ = 'point_transactions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    user_points_id = Column(Integer, ForeignKey('user_points.id'), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # earned, spent, bonus, penalty
    points = Column(Integer, nullable=False)
    description = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=True)  # achievement, milestone, challenge, etc.
    source_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="point_transactions")
    user_points = relationship("UserPoints", back_populates="point_transactions")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_points_id': self.user_points_id,
            'transaction_type': self.transaction_type,
            'points': self.points,
            'description': self.description,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
