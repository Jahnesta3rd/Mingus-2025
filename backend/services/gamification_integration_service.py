#!/usr/bin/env python3
"""
Gamification Integration Service for Mingus Application

Integrates streak tracking and gamification with existing systems:
- Daily Outlook integration
- Goal tracking integration
- Tier upgrade incentives
- Social sharing features
- Analytics for engagement optimization

Features:
- Seamless integration with Daily Outlook
- Goal completion tracking
- Tier-specific feature unlocks
- Social sharing rewards
- Engagement analytics
- Performance optimization
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from sqlalchemy import func, and_, or_, desc, asc
from sqlalchemy.orm import Session
from backend.models.database import db
from backend.models.user_models import User
from backend.models.daily_outlook import DailyOutlook
from backend.models.gamification_models import *
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier
from backend.services.gamification_service import GamificationService
from backend.services.daily_checkin_bonus_service import DailyCheckinBonusService

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class IntegrationType(Enum):
    """Types of system integrations"""
    DAILY_OUTLOOK = "daily_outlook"
    GOAL_TRACKING = "goal_tracking"
    TIER_UPGRADE = "tier_upgrade"
    SOCIAL_SHARING = "social_sharing"
    ANALYTICS = "analytics"

class SocialAction(Enum):
    """Types of social actions"""
    SHARE_STREAK = "share_streak"
    SHARE_ACHIEVEMENT = "share_achievement"
    SHARE_MILESTONE = "share_milestone"
    INVITE_FRIEND = "invite_friend"
    COMPARE_PROGRESS = "compare_progress"

@dataclass
class IntegrationEvent:
    """Event data for system integration"""
    user_id: int
    integration_type: IntegrationType
    event_data: Dict[str, Any]
    timestamp: datetime
    points_awarded: int
    metadata: Dict[str, Any]

# ============================================================================
# GAMIFICATION INTEGRATION SERVICE
# ============================================================================

class GamificationIntegrationService:
    """Service for integrating gamification with existing systems"""
    
    def __init__(self):
        self.feature_service = FeatureFlagService()
        self.gamification_service = GamificationService()
        self.bonus_service = DailyCheckinBonusService()
        
        # Integration configurations
        self.integration_configs = {
            IntegrationType.DAILY_OUTLOOK: {
                'enabled': True,
                'points_per_checkin': 10,
                'streak_bonus_multiplier': 1.5,
                'rating_bonus_threshold': 4
            },
            IntegrationType.GOAL_TRACKING: {
                'enabled': True,
                'points_per_goal': 5,
                'completion_bonus': 25,
                'streak_goal_bonus': 50
            },
            IntegrationType.TIER_UPGRADE: {
                'enabled': True,
                'upgrade_bonus_points': 100,
                'feature_unlock_bonus': 50
            },
            IntegrationType.SOCIAL_SHARING: {
                'enabled': True,
                'share_points': 15,
                'invite_points': 50,
                'viral_bonus': 100
            }
        }

    # ============================================================================
    # DAILY OUTLOOK INTEGRATION
    # ============================================================================

    def integrate_daily_outlook_checkin(self, user_id: int, outlook_data: Dict) -> IntegrationEvent:
        """Integrate daily outlook check-in with gamification"""
        try:
            # Calculate bonuses for daily check-in
            bonuses = self.bonus_service.calculate_daily_bonuses(user_id)
            total_points = sum(bonus.points_awarded for bonus in bonuses)
            
            # Get streak data
            streak_data = self.gamification_service.calculate_streak(user_id)
            
            # Check for milestone achievements
            new_milestones = self.gamification_service.check_milestone_achievements(user_id, streak_data)
            
            # Create integration event
            event = IntegrationEvent(
                user_id=user_id,
                integration_type=IntegrationType.DAILY_OUTLOOK,
                event_data={
                    'outlook_id': outlook_data.get('id'),
                    'rating': outlook_data.get('rating'),
                    'actions_completed': outlook_data.get('actions_completed', 0),
                    'time_spent': outlook_data.get('time_spent', 0)
                },
                timestamp=datetime.now(),
                points_awarded=total_points,
                metadata={
                    'bonuses_awarded': [bonus.bonus_type.value for bonus in bonuses],
                    'streak_count': streak_data.current_streak,
                    'new_milestones': new_milestones,
                    'tier_multiplier': self._get_tier_multiplier(user_id)
                }
            )
            
            # Record the event
            self._record_integration_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error integrating daily outlook checkin: {e}")
            return None

    def process_daily_outlook_rating(self, user_id: int, rating: int) -> IntegrationEvent:
        """Process daily outlook rating for gamification"""
        try:
            # Calculate rating-based bonuses
            rating_bonus = self._calculate_rating_bonus(rating)
            
            # Get user tier for multiplier
            tier_multiplier = self._get_tier_multiplier(user_id)
            final_points = int(rating_bonus * tier_multiplier)
            
            # Create integration event
            event = IntegrationEvent(
                user_id=user_id,
                integration_type=IntegrationType.DAILY_OUTLOOK,
                event_data={'rating': rating},
                timestamp=datetime.now(),
                points_awarded=final_points,
                metadata={
                    'rating_bonus': rating_bonus,
                    'tier_multiplier': tier_multiplier,
                    'rating_category': self._get_rating_category(rating)
                }
            )
            
            # Record the event
            self._record_integration_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error processing daily outlook rating: {e}")
            return None

    def _calculate_rating_bonus(self, rating: int) -> int:
        """Calculate bonus points based on rating"""
        rating_bonuses = {
            1: 0,   # No bonus for poor rating
            2: 5,   # Small bonus for below average
            3: 10,  # Standard bonus for average
            4: 20,  # Good bonus for above average
            5: 35   # Excellent bonus for perfect rating
        }
        return rating_bonuses.get(rating, 0)

    def _get_rating_category(self, rating: int) -> str:
        """Get category for rating"""
        if rating >= 5:
            return "excellent"
        elif rating >= 4:
            return "good"
        elif rating >= 3:
            return "average"
        elif rating >= 2:
            return "below_average"
        else:
            return "poor"

    # ============================================================================
    # GOAL TRACKING INTEGRATION
    # ============================================================================

    def integrate_goal_completion(self, user_id: int, goal_data: Dict) -> IntegrationEvent:
        """Integrate goal completion with gamification"""
        try:
            # Calculate goal completion bonuses
            base_points = self.integration_configs[IntegrationType.GOAL_TRACKING]['points_per_goal']
            completion_bonus = self.integration_configs[IntegrationType.GOAL_TRACKING]['completion_bonus']
            
            # Check for streak goals
            streak_bonus = 0
            if goal_data.get('is_streak_goal', False):
                streak_bonus = self.integration_configs[IntegrationType.GOAL_TRACKING]['streak_goal_bonus']
            
            # Get user tier multiplier
            tier_multiplier = self._get_tier_multiplier(user_id)
            
            # Calculate total points
            total_points = int((base_points + completion_bonus + streak_bonus) * tier_multiplier)
            
            # Create integration event
            event = IntegrationEvent(
                user_id=user_id,
                integration_type=IntegrationType.GOAL_TRACKING,
                event_data={
                    'goal_id': goal_data.get('id'),
                    'goal_type': goal_data.get('type'),
                    'completion_time': goal_data.get('completion_time'),
                    'difficulty': goal_data.get('difficulty')
                },
                timestamp=datetime.now(),
                points_awarded=total_points,
                metadata={
                    'base_points': base_points,
                    'completion_bonus': completion_bonus,
                    'streak_bonus': streak_bonus,
                    'tier_multiplier': tier_multiplier
                }
            )
            
            # Record the event
            self._record_integration_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error integrating goal completion: {e}")
            return None

    def process_goal_streak(self, user_id: int, streak_count: int) -> IntegrationEvent:
        """Process goal completion streak"""
        try:
            # Calculate streak bonus
            streak_bonus = min(streak_count * 5, 100)  # Cap at 100 points
            
            # Get user tier multiplier
            tier_multiplier = self._get_tier_multiplier(user_id)
            final_points = int(streak_bonus * tier_multiplier)
            
            # Create integration event
            event = IntegrationEvent(
                user_id=user_id,
                integration_type=IntegrationType.GOAL_TRACKING,
                event_data={'streak_count': streak_count},
                timestamp=datetime.now(),
                points_awarded=final_points,
                metadata={
                    'streak_bonus': streak_bonus,
                    'tier_multiplier': tier_multiplier,
                    'streak_category': self._get_streak_category(streak_count)
                }
            )
            
            # Record the event
            self._record_integration_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error processing goal streak: {e}")
            return None

    def _get_streak_category(self, streak_count: int) -> str:
        """Get category for streak count"""
        if streak_count >= 30:
            return "legendary"
        elif streak_count >= 14:
            return "excellent"
        elif streak_count >= 7:
            return "good"
        elif streak_count >= 3:
            return "building"
        else:
            return "starting"

    # ============================================================================
    # TIER UPGRADE INTEGRATION
    # ============================================================================

    def integrate_tier_upgrade(self, user_id: int, old_tier: FeatureTier, new_tier: FeatureTier) -> IntegrationEvent:
        """Integrate tier upgrade with gamification"""
        try:
            # Calculate upgrade bonus
            upgrade_bonus = self.integration_configs[IntegrationType.TIER_UPGRADE]['upgrade_bonus_points']
            feature_unlock_bonus = self.integration_configs[IntegrationType.TIER_UPGRADE]['feature_unlock_bonus']
            
            # Calculate tier difference multiplier
            tier_multiplier = self._get_tier_upgrade_multiplier(old_tier, new_tier)
            
            # Calculate total points
            total_points = int((upgrade_bonus + feature_unlock_bonus) * tier_multiplier)
            
            # Get new tier rewards
            new_rewards = self.gamification_service.get_tier_rewards(user_id)
            
            # Create integration event
            event = IntegrationEvent(
                user_id=user_id,
                integration_type=IntegrationType.TIER_UPGRADE,
                event_data={
                    'old_tier': old_tier.value,
                    'new_tier': new_tier.value,
                    'upgrade_date': datetime.now().isoformat()
                },
                timestamp=datetime.now(),
                points_awarded=total_points,
                metadata={
                    'upgrade_bonus': upgrade_bonus,
                    'feature_unlock_bonus': feature_unlock_bonus,
                    'tier_multiplier': tier_multiplier,
                    'new_rewards': new_rewards
                }
            )
            
            # Record the event
            self._record_integration_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error integrating tier upgrade: {e}")
            return None

    def _get_tier_upgrade_multiplier(self, old_tier: FeatureTier, new_tier: FeatureTier) -> float:
        """Get multiplier for tier upgrade"""
        tier_values = {
            FeatureTier.BUDGET: 1,
            FeatureTier.BUDGET_CAREER_VEHICLE: 2,
            FeatureTier.MID_TIER: 3,
            FeatureTier.PROFESSIONAL: 4
        }
        
        old_value = tier_values.get(old_tier, 0)
        new_value = tier_values.get(new_tier, 0)
        
        # Higher tier upgrades get better multipliers
        if new_value - old_value >= 2:
            return 2.0
        elif new_value - old_value == 1:
            return 1.5
        else:
            return 1.0

    # ============================================================================
    # SOCIAL SHARING INTEGRATION
    # ============================================================================

    def integrate_social_share(self, user_id: int, share_type: SocialAction, share_data: Dict) -> IntegrationEvent:
        """Integrate social sharing with gamification"""
        try:
            # Calculate sharing bonuses
            base_share_points = self.integration_configs[IntegrationType.SOCIAL_SHARING]['share_points']
            invite_points = self.integration_configs[IntegrationType.SOCIAL_SHARING]['invite_points']
            viral_bonus = self.integration_configs[IntegrationType.SOCIAL_SHARING]['viral_bonus']
            
            # Calculate points based on share type
            if share_type == SocialAction.SHARE_STREAK:
                points = base_share_points
            elif share_type == SocialAction.SHARE_ACHIEVEMENT:
                points = base_share_points * 2  # Double for achievements
            elif share_type == SocialAction.SHARE_MILESTONE:
                points = base_share_points * 3  # Triple for milestones
            elif share_type == SocialAction.INVITE_FRIEND:
                points = invite_points
            else:
                points = base_share_points
            
            # Check for viral bonus (if share gets engagement)
            if share_data.get('engagement_count', 0) > 10:
                points += viral_bonus
            
            # Get user tier multiplier
            tier_multiplier = self._get_tier_multiplier(user_id)
            final_points = int(points * tier_multiplier)
            
            # Create integration event
            event = IntegrationEvent(
                user_id=user_id,
                integration_type=IntegrationType.SOCIAL_SHARING,
                event_data={
                    'share_type': share_type.value,
                    'platform': share_data.get('platform'),
                    'engagement_count': share_data.get('engagement_count', 0)
                },
                timestamp=datetime.now(),
                points_awarded=final_points,
                metadata={
                    'base_points': points,
                    'viral_bonus': viral_bonus if share_data.get('engagement_count', 0) > 10 else 0,
                    'tier_multiplier': tier_multiplier
                }
            )
            
            # Record the event
            self._record_integration_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error integrating social share: {e}")
            return None

    def process_social_engagement(self, user_id: int, engagement_data: Dict) -> IntegrationEvent:
        """Process social engagement for gamification"""
        try:
            # Calculate engagement bonus
            engagement_bonus = min(engagement_data.get('likes', 0) * 2, 50)  # Cap at 50 points
            
            # Get user tier multiplier
            tier_multiplier = self._get_tier_multiplier(user_id)
            final_points = int(engagement_bonus * tier_multiplier)
            
            # Create integration event
            event = IntegrationEvent(
                user_id=user_id,
                integration_type=IntegrationType.SOCIAL_SHARING,
                event_data=engagement_data,
                timestamp=datetime.now(),
                points_awarded=final_points,
                metadata={
                    'engagement_bonus': engagement_bonus,
                    'tier_multiplier': tier_multiplier
                }
            )
            
            # Record the event
            self._record_integration_event(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error processing social engagement: {e}")
            return None

    # ============================================================================
    # ANALYTICS INTEGRATION
    # ============================================================================

    def get_integration_analytics(self, user_id: int) -> Dict:
        """Get comprehensive integration analytics"""
        try:
            # Get gamification analytics
            gamification_analytics = self.gamification_service.get_engagement_analytics(user_id)
            
            # Get bonus analytics
            bonus_analytics = self.bonus_service.get_bonus_analytics(user_id)
            
            # Get integration event analytics
            integration_analytics = self._get_integration_event_analytics(user_id)
            
            # Combine all analytics
            combined_analytics = {
                'gamification': gamification_analytics,
                'bonuses': bonus_analytics,
                'integration': integration_analytics,
                'recommendations': self._generate_recommendations(user_id, gamification_analytics)
            }
            
            return combined_analytics
            
        except Exception as e:
            logger.error(f"Error getting integration analytics: {e}")
            return {}

    def _get_integration_event_analytics(self, user_id: int) -> Dict:
        """Get analytics for integration events"""
        try:
            # This would query the integration_events table
            # For now, return mock data
            return {
                'total_events': 150,
                'daily_outlook_events': 45,
                'goal_tracking_events': 30,
                'social_sharing_events': 25,
                'tier_upgrade_events': 2,
                'total_points_earned': 2500,
                'average_points_per_day': 16.7,
                'most_active_integration': 'daily_outlook'
            }
            
        except Exception as e:
            logger.error(f"Error getting integration event analytics: {e}")
            return {}

    def _generate_recommendations(self, user_id: int, analytics: Dict) -> List[Dict]:
        """Generate personalized recommendations"""
        try:
            recommendations = []
            
            # Streak-based recommendations
            current_streak = analytics.get('current_streak', 0)
            if current_streak < 7:
                recommendations.append({
                    'type': 'streak',
                    'title': 'Build Your Streak',
                    'description': 'Try to check in daily for 7 days to unlock streak bonuses',
                    'priority': 'high'
                })
            
            # Achievement recommendations
            total_achievements = analytics.get('total_achievements', 0)
            if total_achievements < 5:
                recommendations.append({
                    'type': 'achievement',
                    'title': 'Unlock More Achievements',
                    'description': 'Complete more daily actions to unlock achievements',
                    'priority': 'medium'
                })
            
            # Social sharing recommendations
            if analytics.get('engagement_score', 0) > 70:
                recommendations.append({
                    'type': 'social',
                    'title': 'Share Your Progress',
                    'description': 'Share your achievements to earn bonus points',
                    'priority': 'low'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _get_tier_multiplier(self, user_id: int) -> float:
        """Get tier-based multiplier"""
        try:
            user_tier = self.feature_service.get_user_tier(user_id)
            tier_multipliers = {
                FeatureTier.BUDGET: 1.0,
                FeatureTier.BUDGET_CAREER_VEHICLE: 1.2,
                FeatureTier.MID_TIER: 1.5,
                FeatureTier.PROFESSIONAL: 2.0
            }
            return tier_multipliers.get(user_tier, 1.0)
            
        except Exception as e:
            logger.error(f"Error getting tier multiplier: {e}")
            return 1.0

    def _record_integration_event(self, event: IntegrationEvent):
        """Record integration event in database"""
        try:
            # This would create a record in the integration_events table
            # For now, we'll log the event
            logger.info(f"Integration event: {event.integration_type.value} - {event.points_awarded} points to user {event.user_id}")
            
        except Exception as e:
            logger.error(f"Error recording integration event: {e}")

    # ============================================================================
    # PERFORMANCE OPTIMIZATION
    # ============================================================================

    def optimize_engagement(self, user_id: int) -> Dict:
        """Optimize user engagement based on analytics"""
        try:
            # Get user analytics
            analytics = self.get_integration_analytics(user_id)
            
            # Identify optimization opportunities
            optimizations = []
            
            # Check engagement patterns
            engagement_score = analytics.get('gamification', {}).get('engagement_score', 0)
            if engagement_score < 50:
                optimizations.append({
                    'type': 'engagement',
                    'action': 'increase_checkin_frequency',
                    'description': 'Try checking in more frequently to improve engagement',
                    'impact': 'high'
                })
            
            # Check streak patterns
            current_streak = analytics.get('gamification', {}).get('current_streak', 0)
            if current_streak == 0:
                optimizations.append({
                    'type': 'streak',
                    'action': 'start_new_streak',
                    'description': 'Start a new streak to unlock streak bonuses',
                    'impact': 'medium'
                })
            
            # Check social engagement
            social_events = analytics.get('integration', {}).get('social_sharing_events', 0)
            if social_events < 5:
                optimizations.append({
                    'type': 'social',
                    'action': 'increase_social_sharing',
                    'description': 'Share your progress more often to earn bonus points',
                    'impact': 'low'
                })
            
            return {
                'optimizations': optimizations,
                'current_score': engagement_score,
                'improvement_potential': self._calculate_improvement_potential(analytics)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing engagement: {e}")
            return {}

    def _calculate_improvement_potential(self, analytics: Dict) -> float:
        """Calculate potential for improvement"""
        try:
            # This would calculate improvement potential based on analytics
            # For now, return a mock value
            return 0.75
            
        except Exception as e:
            logger.error(f"Error calculating improvement potential: {e}")
            return 0.0
