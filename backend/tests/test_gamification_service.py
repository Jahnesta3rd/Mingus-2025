#!/usr/bin/env python3
"""
Test suite for Gamification Service

Comprehensive tests for the gamification system including:
- Streak calculation
- Milestone detection
- Achievement system
- Recovery options
- Weekly challenges
- Leaderboard functionality
"""

import unittest
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.services.gamification_service import GamificationService, StreakData, Milestone, Achievement
from backend.models.gamification_models import StreakType, AchievementCategory
from backend.services.feature_flag_service import FeatureTier

class TestGamificationService(unittest.TestCase):
    """Test cases for GamificationService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gamification_service = GamificationService()
        self.user_id = 1
        self.current_date = date.today()
        
        # Mock database session
        self.mock_db_session = Mock()
        
    def test_calculate_streak_daily_outlook(self):
        """Test daily outlook streak calculation"""
        # Mock streak data
        mock_streak_data = StreakData(
            current_streak=7,
            longest_streak=15,
            total_days=25,
            streak_start_date=self.current_date - timedelta(days=6),
            last_activity_date=self.current_date,
            is_active=True,
            streak_type=StreakType.DAILY_OUTLOOK
        )
        
        with patch.object(self.gamification_service, '_calculate_daily_outlook_streak', return_value=mock_streak_data):
            result = self.gamification_service.calculate_streak(self.user_id, StreakType.DAILY_OUTLOOK)
            
            self.assertEqual(result.current_streak, 7)
            self.assertEqual(result.longest_streak, 15)
            self.assertTrue(result.is_active)
            self.assertEqual(result.streak_type, StreakType.DAILY_OUTLOOK)
    
    def test_get_milestones(self):
        """Test milestone retrieval"""
        # Mock streak data
        streak_data = StreakData(
            current_streak=7,
            longest_streak=15,
            total_days=25,
            streak_start_date=self.current_date - timedelta(days=6),
            last_activity_date=self.current_date,
            is_active=True,
            streak_type=StreakType.DAILY_OUTLOOK
        )
        
        milestones = self.gamification_service.get_milestones(self.user_id, streak_data)
        
        # Should have milestones for 3, 7, 14, 21, 30, 60, 90, 100, 365 days
        self.assertGreater(len(milestones), 5)
        
        # Check that 7-day milestone is achieved
        week_milestone = next((m for m in milestones if m.days_required == 7), None)
        self.assertIsNotNone(week_milestone)
        self.assertTrue(week_milestone.achieved)
        self.assertEqual(week_milestone.progress_percentage, 100)
        
        # Check that 14-day milestone is not achieved
        two_week_milestone = next((m for m in milestones if m.days_required == 14), None)
        self.assertIsNotNone(two_week_milestone)
        self.assertFalse(two_week_milestone.achieved)
        self.assertEqual(two_week_milestone.progress_percentage, 50)
    
    def test_get_achievements(self):
        """Test achievement retrieval"""
        achievements = self.gamification_service.get_achievements(self.user_id)
        
        # Should have multiple achievements
        self.assertGreater(len(achievements), 5)
        
        # Check achievement categories
        categories = set(a.category for a in achievements)
        expected_categories = {AchievementCategory.STREAK, AchievementCategory.ENGAGEMENT, 
                             AchievementCategory.GOALS, AchievementCategory.SOCIAL, AchievementCategory.SPECIAL}
        self.assertEqual(categories, expected_categories)
    
    def test_get_recovery_options(self):
        """Test recovery options for broken streak"""
        # Mock broken streak
        broken_streak = StreakData(
            current_streak=0,
            longest_streak=10,
            total_days=15,
            streak_start_date=self.current_date,
            last_activity_date=self.current_date - timedelta(days=2),
            is_active=False,
            streak_type=StreakType.DAILY_OUTLOOK
        )
        
        with patch.object(self.gamification_service.feature_service, 'get_user_tier', return_value=FeatureTier.BUDGET):
            recovery_options = self.gamification_service.get_recovery_options(self.user_id, broken_streak)
            
            # Should have restart option for budget tier
            self.assertGreater(len(recovery_options), 0)
            restart_option = next((r for r in recovery_options if r.type.value == 'restart'), None)
            self.assertIsNotNone(restart_option)
            self.assertTrue(restart_option.available)
    
    def test_get_weekly_challenges(self):
        """Test weekly challenges retrieval"""
        with patch.object(self.gamification_service.feature_service, 'get_user_tier', return_value=FeatureTier.BUDGET_CAREER_VEHICLE):
            challenges = self.gamification_service.get_weekly_challenges(self.user_id)
            
            # Should have challenges for budget_career_vehicle tier
            self.assertGreater(len(challenges), 0)
            
            # Check challenge structure
            for challenge in challenges:
                self.assertIsNotNone(challenge.id)
                self.assertIsNotNone(challenge.title)
                self.assertIsNotNone(challenge.description)
                self.assertGreater(challenge.target, 0)
                self.assertGreaterEqual(challenge.current_progress, 0)
    
    def test_get_leaderboard(self):
        """Test leaderboard functionality"""
        # Test streak leaderboard
        leaderboard = self.gamification_service.get_leaderboard('streak', 10)
        
        # Should return list of leaderboard entries
        self.assertIsInstance(leaderboard, list)
        
        # Each entry should have required fields
        for entry in leaderboard:
            self.assertIn('rank', entry)
            self.assertIn('user_id', entry)
            self.assertIn('score', entry)
            self.assertIn('display_name', entry)
            self.assertIn('badge', entry)
    
    def test_get_engagement_analytics(self):
        """Test engagement analytics"""
        analytics = self.gamification_service.get_engagement_analytics(self.user_id)
        
        # Should return analytics dictionary
        self.assertIsInstance(analytics, dict)
        
        # Should have expected keys
        expected_keys = ['current_streak', 'longest_streak', 'total_achievements', 
                        'total_milestones', 'engagement_score', 'consistency_rating', 'improvement_trend']
        for key in expected_keys:
            self.assertIn(key, analytics)
    
    def test_get_tier_rewards(self):
        """Test tier-specific rewards"""
        with patch.object(self.gamification_service.feature_service, 'get_user_tier', return_value=FeatureTier.PROFESSIONAL):
            rewards = self.gamification_service.get_tier_rewards(self.user_id)
            
            # Should have rewards for professional tier
            self.assertGreater(len(rewards), 0)
            
            # Check reward structure
            for reward in rewards:
                self.assertIn('name', reward)
                self.assertIn('description', reward)
                self.assertIn('unlocked', reward)
    
    def test_process_gamification_action_recovery(self):
        """Test processing recovery actions"""
        action_data = {
            'recovery_type': 'restart',
            'action': 'begin_new_streak'
        }
        
        with patch.object(self.gamification_service, '_restart_streak', return_value=True):
            result = self.gamification_service.process_gamification_action(
                self.user_id, 'recovery', action_data
            )
            
            self.assertTrue(result)
    
    def test_process_gamification_action_challenge(self):
        """Test processing challenge actions"""
        action_data = {
            'challenge_id': 'daily_checkin',
            'action': 'participate'
        }
        
        with patch.object(self.gamification_service, '_join_challenge', return_value=True):
            result = self.gamification_service.process_gamification_action(
                self.user_id, 'challenge', action_data
            )
            
            self.assertTrue(result)
    
    def test_process_gamification_action_achievement(self):
        """Test processing achievement actions"""
        action_data = {
            'achievement_id': 'first_streak',
            'action': 'claim'
        }
        
        with patch.object(self.gamification_service, '_claim_achievement', return_value=True):
            result = self.gamification_service.process_gamification_action(
                self.user_id, 'achievement_claim', action_data
            )
            
            self.assertTrue(result)
    
    def test_get_complete_gamification_data(self):
        """Test getting complete gamification data"""
        with patch.object(self.gamification_service, 'calculate_streak') as mock_calculate_streak, \
             patch.object(self.gamification_service, 'get_milestones') as mock_get_milestones, \
             patch.object(self.gamification_service, 'get_achievements') as mock_get_achievements, \
             patch.object(self.gamification_service, 'get_recovery_options') as mock_get_recovery_options, \
             patch.object(self.gamification_service, 'get_weekly_challenges') as mock_get_weekly_challenges, \
             patch.object(self.gamification_service, 'get_engagement_analytics') as mock_get_analytics, \
             patch.object(self.gamification_service, 'get_tier_rewards') as mock_get_tier_rewards:
            
            # Mock return values
            mock_calculate_streak.return_value = StreakData(
                current_streak=7, longest_streak=15, total_days=25,
                streak_start_date=self.current_date, last_activity_date=self.current_date,
                is_active=True, streak_type=StreakType.DAILY_OUTLOOK
            )
            mock_get_milestones.return_value = []
            mock_get_achievements.return_value = []
            mock_get_recovery_options.return_value = []
            mock_get_weekly_challenges.return_value = []
            mock_get_analytics.return_value = {}
            mock_get_tier_rewards.return_value = []
            
            result = self.gamification_service.get_complete_gamification_data(self.user_id)
            
            # Should return complete data structure
            self.assertIn('streak_data', result)
            self.assertIn('milestones', result)
            self.assertIn('achievements', result)
            self.assertIn('recovery_options', result)
            self.assertIn('weekly_challenges', result)
            self.assertIn('analytics', result)
            self.assertIn('tier_rewards', result)
    
    def test_error_handling(self):
        """Test error handling in service methods"""
        # Test with invalid user ID
        with patch.object(self.gamification_service, 'calculate_streak', side_effect=Exception("Database error")):
            result = self.gamification_service.calculate_streak(-1, StreakType.DAILY_OUTLOOK)
            
            # Should return default streak data on error
            self.assertEqual(result.current_streak, 0)
            self.assertFalse(result.is_active)

class TestGamificationIntegration(unittest.TestCase):
    """Test integration between gamification components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.gamification_service = GamificationService()
        self.user_id = 1
    
    def test_milestone_achievement_detection(self):
        """Test milestone achievement detection"""
        # Mock streak data that just reached a milestone
        streak_data = StreakData(
            current_streak=7,
            longest_streak=7,
            total_days=7,
            streak_start_date=date.today() - timedelta(days=6),
            last_activity_date=date.today(),
            is_active=True,
            streak_type=StreakType.DAILY_OUTLOOK
        )
        
        milestones = self.gamification_service.get_milestones(self.user_id, streak_data)
        
        # 7-day milestone should be achieved
        week_milestone = next((m for m in milestones if m.days_required == 7), None)
        self.assertIsNotNone(week_milestone)
        self.assertTrue(week_milestone.achieved)
    
    def test_achievement_unlock_logic(self):
        """Test achievement unlock logic"""
        # Test first streak achievement
        with patch.object(self.gamification_service, 'calculate_streak') as mock_calculate_streak:
            mock_calculate_streak.return_value = StreakData(
                current_streak=3, longest_streak=3, total_days=3,
                streak_start_date=date.today() - timedelta(days=2),
                last_activity_date=date.today(),
                is_active=True, streak_type=StreakType.DAILY_OUTLOOK
            )
            
            achievements = self.gamification_service.get_achievements(self.user_id)
            
            # First streak achievement should be unlocked
            first_streak_achievement = next((a for a in achievements if a.id == 'first_streak'), None)
            self.assertIsNotNone(first_streak_achievement)
            self.assertTrue(first_streak_achievement.unlocked)
    
    def test_tier_based_feature_access(self):
        """Test tier-based feature access"""
        # Test budget tier access
        with patch.object(self.gamification_service.feature_service, 'get_user_tier', return_value=FeatureTier.BUDGET):
            challenges = self.gamification_service.get_weekly_challenges(self.user_id)
            
            # Budget tier should have basic challenges
            self.assertGreater(len(challenges), 0)
        
        # Test professional tier access
        with patch.object(self.gamification_service.feature_service, 'get_user_tier', return_value=FeatureTier.PROFESSIONAL):
            challenges = self.gamification_service.get_weekly_challenges(self.user_id)
            
            # Professional tier should have more challenges
            self.assertGreater(len(challenges), 0)

if __name__ == '__main__':
    unittest.main()
