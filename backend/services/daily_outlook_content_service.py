#!/usr/bin/env python3
"""
Daily Outlook Content Generation Service for Mingus Application
Generates personalized daily content based on user tier, activity, and engagement patterns
"""

import logging
import sqlite3
import json
import random
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from backend.models.daily_outlook import TemplateTier, TemplateCategory, DailyOutlook
from backend.services.daily_outlook_service import DailyOutlookService
from backend.services.feature_flag_service import FeatureFlagService, FeatureTier

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class UserData:
    """User data for content generation"""
    user_id: int
    tier: FeatureTier
    location: str
    relationship_status: str
    financial_score: float
    wellness_score: float
    relationship_score: float
    career_score: float
    streak_count: int
    recent_activity: Dict[str, Any]
    spending_patterns: Dict[str, Any]
    goals: Dict[str, Any]
    assessment_results: Dict[str, Any]

@dataclass
class ContentTemplate:
    """Content template structure"""
    template_id: str
    tier: TemplateTier
    category: TemplateCategory
    content: str
    trigger_conditions: Dict[str, Any]
    cultural_relevance: bool
    city_specific: Optional[str]

class DailyOutlookContentService:
    """
    Service for generating personalized daily outlook content
    
    Features:
    - Tier-specific content depth and complexity
    - Cultural relevance for African American professionals
    - City-specific insights for major metros
    - Dynamic relationship status considerations
    - Integration with existing user data systems
    """
    
    def __init__(self, profile_db_path: str = "user_profiles.db"):
        """Initialize the content generation service"""
        self.profile_db_path = profile_db_path
        self.daily_outlook_service = DailyOutlookService(profile_db_path)
        self.feature_flag_service = FeatureFlagService()
        
        # Major metros for city-specific content
        self.major_metros = {
            'Atlanta': {'state': 'GA', 'region': 'Southeast', 'cultural_hub': True},
            'Houston': {'state': 'TX', 'region': 'South', 'cultural_hub': True},
            'Washington DC': {'state': 'DC', 'region': 'Mid-Atlantic', 'cultural_hub': True},
            'Dallas': {'state': 'TX', 'region': 'South', 'cultural_hub': True},
            'New York City': {'state': 'NY', 'region': 'Northeast', 'cultural_hub': True},
            'Philadelphia': {'state': 'PA', 'region': 'Northeast', 'cultural_hub': True},
            'Chicago': {'state': 'IL', 'region': 'Midwest', 'cultural_hub': True},
            'Charlotte': {'state': 'NC', 'region': 'Southeast', 'cultural_hub': True},
            'Miami': {'state': 'FL', 'region': 'Southeast', 'cultural_hub': True},
            'Baltimore': {'state': 'MD', 'region': 'Mid-Atlantic', 'cultural_hub': True}
        }
        
        logger.info("DailyOutlookContentService initialized successfully")
    
    def generate_daily_outlook(self, user_id: int) -> Dict[str, Any]:
        """
        Generate personalized daily content for a user
        
        Args:
            user_id: User ID to generate content for
            
        Returns:
            Dictionary containing all daily outlook content
        """
        try:
            # Get user data
            user_data = self._get_user_data(user_id)
            if not user_data:
                logger.error(f"Could not retrieve user data for user {user_id}")
                return self._get_default_content()
            
            # Get dynamic weights from DailyOutlookService
            weights = self.daily_outlook_service.calculate_dynamic_weights(user_id)
            
            # Generate content components
            primary_insight = self.select_primary_insight(user_data, weights)
            quick_actions = self.generate_quick_actions(user_data, user_data.tier)
            encouragement_message = self.create_encouragement_message(user_data, user_data.streak_count)
            surprise_element = self.get_surprise_element(user_id, datetime.now().weekday())
            tomorrow_teaser = self.build_tomorrow_teaser(user_data)
            
            # Calculate balance score
            balance_score, individual_scores = self.daily_outlook_service.calculate_balance_score(user_id)
            
            # Create daily outlook record
            daily_outlook = {
                'user_id': user_id,
                'date': date.today(),
                'balance_score': balance_score,
                'financial_weight': weights['financial'],
                'wellness_weight': weights['wellness'],
                'relationship_weight': weights['relationship'],
                'career_weight': weights['career'],
                'primary_insight': primary_insight,
                'quick_actions': quick_actions,
                'encouragement_message': encouragement_message,
                'surprise_element': surprise_element,
                'tomorrow_teaser': tomorrow_teaser,
                'streak_count': user_data.streak_count,
                'tier': user_data.tier.value,
                'location': user_data.location,
                'cultural_relevance': True,
                'city_specific': user_data.location in self.major_metros
            }
            
            # Save to database
            self._save_daily_outlook(daily_outlook)
            
            logger.info(f"Generated daily outlook for user {user_id}")
            return daily_outlook
            
        except Exception as e:
            logger.error(f"Error generating daily outlook for user {user_id}: {e}")
            return self._get_default_content()
    
    def select_primary_insight(self, user_data: UserData, weights: Dict[str, float]) -> str:
        """
        Select the highest impact insight based on user data and weights
        
        Args:
            user_data: User data object
            weights: Dynamic weights from DailyOutlookService
            
        Returns:
            Primary insight message
        """
        try:
            # Determine which category has the highest weight
            max_weight_category = max(weights.items(), key=lambda x: x[1])[0]
            
            # Get templates for the highest weight category
            templates = self._get_templates_for_category(max_weight_category, user_data.tier)
            
            if not templates:
                return self._get_default_insight(user_data)
            
            # Select template based on user data and conditions
            selected_template = self._select_template_by_conditions(templates, user_data)
            
            # Personalize the template
            personalized_insight = self._personalize_template(selected_template, user_data)
            
            return personalized_insight
            
        except Exception as e:
            logger.error(f"Error selecting primary insight: {e}")
            return self._get_default_insight(user_data)
    
    def generate_quick_actions(self, user_data: UserData, tier: FeatureTier) -> List[Dict[str, Any]]:
        """
        Generate 2-3 actionable items based on user tier and data
        
        Args:
            user_data: User data object
            tier: User subscription tier
            
        Returns:
            List of quick action dictionaries
        """
        try:
            actions = []
            
            # Tier-specific action complexity
            if tier == FeatureTier.BUDGET:
                actions = self._get_budget_tier_actions(user_data)
            elif tier == FeatureTier.MID_TIER:
                actions = self._get_mid_tier_actions(user_data)
            elif tier == FeatureTier.PROFESSIONAL:
                actions = self._get_professional_tier_actions(user_data)
            else:
                actions = self._get_budget_tier_actions(user_data)
            
            # Limit to 2-3 actions
            return actions[:3]
            
        except Exception as e:
            logger.error(f"Error generating quick actions: {e}")
            return self._get_default_actions()
    
    def create_encouragement_message(self, user_data: UserData, streak_count: int) -> str:
        """
        Create personalized encouragement message based on user data and streak
        
        Args:
            user_data: User data object
            streak_count: Current streak count
            
        Returns:
            Personalized encouragement message
        """
        try:
            # Base encouragement templates
            encouragement_templates = [
                "You're building something powerful, one day at a time. Your consistency is your superpower.",
                "Every step forward is progress. You're not just managing money, you're building generational wealth.",
                "Your dedication to financial wellness is inspiring. Keep pushing toward your goals.",
                "Remember, every successful person started exactly where you are. Keep going.",
                "Your financial journey is uniquely yours, and you're writing an incredible story."
            ]
            
            # Streak-based encouragement
            if streak_count >= 30:
                message = f"🔥 {streak_count} days strong! You're not just consistent, you're unstoppable. This is how legends are built."
            elif streak_count >= 14:
                message = f"💪 {streak_count} days in a row! You're building habits that will transform your future. Keep this momentum going!"
            elif streak_count >= 7:
                message = f"⭐ {streak_count} days and counting! You're proving to yourself that you can do this. The best is yet to come."
            elif streak_count >= 3:
                message = f"🚀 {streak_count} days strong! You're building the foundation for something amazing. Every day counts."
            else:
                message = random.choice(encouragement_templates)
            
            # Add cultural relevance
            if user_data.location in self.major_metros:
                cultural_additions = [
                    " Your ancestors' dreams are being realized through your actions.",
                    " You're part of a legacy of financial empowerment and community building.",
                    " Every dollar you save is a vote for the future you deserve.",
                    " You're not just building wealth, you're building generational impact."
                ]
                message += random.choice(cultural_additions)
            
            return message
            
        except Exception as e:
            logger.error(f"Error creating encouragement message: {e}")
            return "You've got this! Every step forward is progress."
    
    def get_surprise_element(self, user_id: int, day_of_week: int) -> str:
        """
        Generate rotating surprise content based on day of week
        
        Args:
            user_id: User ID
            day_of_week: Day of week (0=Monday, 6=Sunday)
            
        Returns:
            Surprise element content
        """
        try:
            # Day-specific surprise elements
            surprise_elements = {
                0: [  # Monday
                    "💡 Monday Motivation: Did you know that starting your week with a financial check-in increases your success rate by 40%?",
                    "🎯 This week's focus: Track one expense that surprised you last week. Knowledge is power!",
                    "📈 Fun fact: People who review their finances on Mondays save 15% more than those who don't."
                ],
                1: [  # Tuesday
                    "💪 Tuesday Tip: The most successful people review their goals daily. What's one financial goal you're working toward?",
                    "🌟 Today's insight: Small, consistent actions compound into extraordinary results. Keep going!",
                    "📊 Did you know? Tracking expenses for just 7 days can reveal patterns that save you hundreds."
                ],
                2: [  # Wednesday
                    "🔥 Wednesday Wisdom: Midweek is perfect for adjusting your financial plan. What needs tweaking?",
                    "💎 Midweek reminder: Your future self will thank you for every smart financial decision you make today.",
                    "🎪 Wednesday surprise: You're halfway through the week and still committed to your financial goals. That's powerful!"
                ],
                3: [  # Thursday
                    "🚀 Thursday Thrive: You're building momentum! What financial win can you celebrate today?",
                    "💡 Thursday thought: Every dollar you don't spend on something you don't need is a dollar invested in your dreams.",
                    "🌟 Almost there: Your consistency this week is setting you up for long-term success."
                ],
                4: [  # Friday
                    "🎉 Friday Focus: End your week strong! What's one financial action you can take before the weekend?",
                    "💪 Friday power: You've made it through another week of financial awareness. That's growth!",
                    "🌟 Weekend prep: Set yourself up for success by planning one financial task for next week."
                ],
                5: [  # Saturday
                    "🌅 Saturday Success: Weekend financial planning can set the tone for your entire week ahead.",
                    "💎 Saturday insight: The best time to plant a tree was 20 years ago. The second best time is now. Start today!",
                    "🎯 Weekend wisdom: Use this time to reflect on your financial progress. You're doing better than you think."
                ],
                6: [  # Sunday
                    "🙏 Sunday Reflection: Take a moment to appreciate how far you've come on your financial journey.",
                    "🌟 Sunday prep: Tomorrow is a fresh start. What's one financial goal you want to focus on this week?",
                    "💪 Sunday strength: You're building habits that will serve you for life. That's something to be proud of."
                ]
            }
            
            # Get surprise elements for the day
            day_surprises = surprise_elements.get(day_of_week, surprise_elements[0])
            
            # Add user-specific elements based on their data
            user_data = self._get_user_data(user_id)
            if user_data:
                # Add personalized elements
                if user_data.streak_count > 0:
                    day_surprises.append(f"🔥 Your {user_data.streak_count}-day streak is inspiring! Keep this energy going.")
                
                if user_data.financial_score > 70:
                    day_surprises.append("💎 Your financial health is strong! You're setting an example for others.")
                elif user_data.financial_score < 40:
                    day_surprises.append("💪 Every expert was once a beginner. You're exactly where you need to be.")
            
            return random.choice(day_surprises)
            
        except Exception as e:
            logger.error(f"Error generating surprise element: {e}")
            return "🌟 You're doing great! Keep focusing on your financial goals."
    
    def build_tomorrow_teaser(self, user_data: UserData) -> str:
        """
        Create anticipation builder for tomorrow's content
        
        Args:
            user_data: User data object
            
        Returns:
            Tomorrow teaser message
        """
        try:
            # Base teaser templates
            teaser_templates = [
                "Tomorrow: Discover how small changes in your daily routine can boost your financial health.",
                "Coming up: Learn about the power of compound interest and how it can work for you.",
                "Next up: We'll explore strategies to build your emergency fund faster than you thought possible.",
                "Tomorrow's insight: The secret to financial confidence starts with one simple habit.",
                "Coming tomorrow: How to turn your biggest financial challenge into your greatest opportunity."
            ]
            
            # Tier-specific teasers
            if user_data.tier == FeatureTier.PROFESSIONAL:
                professional_teasers = [
                    "Tomorrow: Advanced wealth-building strategies that successful professionals use.",
                    "Coming up: Executive-level financial planning techniques for career growth.",
                    "Next: How to optimize your income and build generational wealth.",
                    "Tomorrow's focus: Professional development investments that pay dividends.",
                    "Coming tomorrow: Leadership strategies for financial independence."
                ]
                teaser_templates.extend(professional_teasers)
            
            # Location-specific teasers
            if user_data.location in self.major_metros:
                location_teasers = [
                    f"Tomorrow: {user_data.location}-specific financial opportunities you should know about.",
                    f"Coming up: How to leverage your {user_data.location} location for financial growth.",
                    f"Next: {user_data.location} market insights that could impact your financial decisions.",
                ]
                teaser_templates.extend(location_teasers)
            
            # Select and personalize teaser
            selected_teaser = random.choice(teaser_templates)
            
            # Add streak-based anticipation
            if user_data.streak_count > 0:
                selected_teaser += f" (Your {user_data.streak_count}-day streak is building something amazing!)"
            
            return selected_teaser
            
        except Exception as e:
            logger.error(f"Error building tomorrow teaser: {e}")
            return "Tomorrow: More insights to help you on your financial journey."
    
    def _get_user_data(self, user_id: int) -> Optional[UserData]:
        """Get comprehensive user data for content generation"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            # Get user tier
            tier = self.feature_flag_service.get_user_tier(user_id)
            
            # Get user profile data
            cursor.execute("""
                SELECT personal_info, financial_info, goals, location
                FROM user_profiles 
                WHERE email = (SELECT email FROM users WHERE id = ?)
            """, (user_id,))
            
            profile_result = cursor.fetchone()
            if not profile_result:
                conn.close()
                return None
            
            personal_info = json.loads(profile_result[0]) if profile_result[0] else {}
            financial_info = json.loads(profile_result[1]) if profile_result[1] else {}
            goals = json.loads(profile_result[2]) if profile_result[2] else {}
            location = profile_result[3] or "Unknown"
            
            # Get relationship status
            cursor.execute("""
                SELECT status FROM user_relationship_status 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (user_id,))
            
            relationship_result = cursor.fetchone()
            relationship_status = relationship_result[0] if relationship_result else "single_career_focused"
            
            # Get recent activity and spending patterns
            recent_activity = self._get_recent_activity(user_id, cursor)
            spending_patterns = self._get_spending_patterns(user_id, cursor)
            
            # Get assessment results
            assessment_results = self._get_assessment_results(user_id, cursor)
            
            # Get individual scores
            _, individual_scores = self.daily_outlook_service.calculate_balance_score(user_id)
            
            # Get streak count
            cursor.execute("""
                SELECT streak_count FROM daily_outlooks 
                WHERE user_id = ? 
                ORDER BY date DESC 
                LIMIT 1
            """, (user_id,))
            
            streak_result = cursor.fetchone()
            streak_count = streak_result[0] if streak_result else 0
            
            conn.close()
            
            return UserData(
                user_id=user_id,
                tier=tier,
                location=location,
                relationship_status=relationship_status,
                financial_score=individual_scores.financial_score,
                wellness_score=individual_scores.wellness_score,
                relationship_score=individual_scores.relationship_score,
                career_score=individual_scores.career_score,
                streak_count=streak_count,
                recent_activity=recent_activity,
                spending_patterns=spending_patterns,
                goals=goals,
                assessment_results=assessment_results
            )
            
        except Exception as e:
            logger.error(f"Error getting user data for user {user_id}: {e}")
            return None
    
    def _get_recent_activity(self, user_id: int, cursor) -> Dict[str, Any]:
        """Get recent user activity data"""
        try:
            # Get recent mood data
            cursor.execute("""
                SELECT AVG(mood_score), COUNT(*) FROM user_mood_data 
                WHERE user_id = ? 
                AND timestamp >= datetime('now', '-7 days')
            """, (user_id,))
            
            mood_result = cursor.fetchone()
            avg_mood = mood_result[0] if mood_result[0] else 3.0
            mood_entries = mood_result[1] if mood_result[1] else 0
            
            # Get recent check-ins
            cursor.execute("""
                SELECT AVG(physical_activity), AVG(meditation_minutes), AVG(relationship_satisfaction)
                FROM weekly_checkins 
                WHERE user_id = ? 
                AND check_in_date >= date('now', '-14 days')
            """, (user_id,))
            
            wellness_result = cursor.fetchone()
            
            return {
                'avg_mood': avg_mood,
                'mood_entries': mood_entries,
                'physical_activity': wellness_result[0] if wellness_result[0] else 0,
                'meditation_minutes': wellness_result[1] if wellness_result[1] else 0,
                'relationship_satisfaction': wellness_result[2] if wellness_result[2] else 5
            }
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return {}
    
    def _get_spending_patterns(self, user_id: int, cursor) -> Dict[str, Any]:
        """Get user spending patterns"""
        try:
            # This would integrate with actual spending data
            # For now, return default patterns
            return {
                'avg_daily_spending': 0,
                'largest_expense_category': 'unknown',
                'spending_trend': 'stable',
                'budget_adherence': 0.8
            }
            
        except Exception as e:
            logger.error(f"Error getting spending patterns: {e}")
            return {}
    
    def _get_assessment_results(self, user_id: int, cursor) -> Dict[str, Any]:
        """Get user assessment results"""
        try:
            # This would integrate with assessment data
            # For now, return default results
            return {
                'financial_literacy_score': 70,
                'risk_tolerance': 'moderate',
                'investment_knowledge': 'beginner',
                'goal_clarity': 'high'
            }
            
        except Exception as e:
            logger.error(f"Error getting assessment results: {e}")
            return {}
    
    def _get_templates_for_category(self, category: str, tier: FeatureTier) -> List[ContentTemplate]:
        """Get content templates for a specific category and tier"""
        try:
            # Convert tier to TemplateTier
            template_tier = TemplateTier.BUDGET
            if tier == FeatureTier.MID_TIER:
                template_tier = TemplateTier.MID_TIER
            elif tier == FeatureTier.PROFESSIONAL:
                template_tier = TemplateTier.PROFESSIONAL
            
            # Convert category to TemplateCategory
            template_category = TemplateCategory.FINANCIAL
            if category == 'wellness':
                template_category = TemplateCategory.WELLNESS
            elif category == 'relationship':
                template_category = TemplateCategory.RELATIONSHIP
            elif category == 'career':
                template_category = TemplateCategory.CAREER
            
            # Return tier and category specific templates
            return self._get_tier_category_templates(template_tier, template_category)
            
        except Exception as e:
            logger.error(f"Error getting templates for category {category}: {e}")
            return []
    
    def _get_tier_category_templates(self, tier: TemplateTier, category: TemplateCategory) -> List[ContentTemplate]:
        """Get templates for specific tier and category"""
        templates = []
        
        # Financial templates
        if category == TemplateCategory.FINANCIAL:
            if tier == TemplateTier.BUDGET:
                templates = [
                    ContentTemplate(
                        template_id="budget_financial_1",
                        tier=tier,
                        category=category,
                        content="Your financial foundation is growing stronger every day. Small, consistent actions lead to big results.",
                        trigger_conditions={'financial_score': '>50'},
                        cultural_relevance=True,
                        city_specific=None
                    ),
                    ContentTemplate(
                        template_id="budget_financial_2",
                        tier=tier,
                        category=category,
                        content="Every dollar you save is a step toward financial freedom. You're building the future you deserve.",
                        trigger_conditions={'financial_score': '<50'},
                        cultural_relevance=True,
                        city_specific=None
                    )
                ]
            elif tier == TemplateTier.MID_TIER:
                templates = [
                    ContentTemplate(
                        template_id="mid_financial_1",
                        tier=tier,
                        category=category,
                        content="Your financial strategy is showing results. Consider how to optimize your next moves for maximum impact.",
                        trigger_conditions={'financial_score': '>60'},
                        cultural_relevance=True,
                        city_specific=None
                    )
                ]
            elif tier == TemplateTier.PROFESSIONAL:
                templates = [
                    ContentTemplate(
                        template_id="pro_financial_1",
                        tier=tier,
                        category=category,
                        content="Your sophisticated approach to wealth building is paying dividends. Time to explore advanced strategies.",
                        trigger_conditions={'financial_score': '>70'},
                        cultural_relevance=True,
                        city_specific=None
                    )
                ]
        
        # Career templates
        elif category == TemplateCategory.CAREER:
            if tier == TemplateTier.BUDGET:
                templates = [
                    ContentTemplate(
                        template_id="budget_career_1",
                        tier=tier,
                        category=category,
                        content="Your career journey is unique and valuable. Every skill you develop opens new doors.",
                        trigger_conditions={'career_score': '>50'},
                        cultural_relevance=True,
                        city_specific=None
                    )
                ]
            elif tier == TemplateTier.MID_TIER:
                templates = [
                    ContentTemplate(
                        template_id="mid_career_1",
                        tier=tier,
                        category=category,
                        content="Your professional growth is accelerating. Consider how to leverage your network for the next opportunity.",
                        trigger_conditions={'career_score': '>60'},
                        cultural_relevance=True,
                        city_specific=None
                    )
                ]
            elif tier == TemplateTier.PROFESSIONAL:
                templates = [
                    ContentTemplate(
                        template_id="pro_career_1",
                        tier=tier,
                        category=category,
                        content="Your leadership in your field is creating opportunities for others. How can you expand your impact?",
                        trigger_conditions={'career_score': '>70'},
                        cultural_relevance=True,
                        city_specific=None
                    )
                ]
        
        # Relationship templates
        elif category == TemplateCategory.RELATIONSHIP:
            templates = [
                ContentTemplate(
                    template_id="relationship_1",
                    tier=tier,
                    category=category,
                    content="Your relationships are a source of strength and support. Nurture them as you grow.",
                    trigger_conditions={'relationship_score': '>50'},
                    cultural_relevance=True,
                    city_specific=None
                )
            ]
        
        # Wellness templates
        elif category == TemplateCategory.WELLNESS:
            templates = [
                ContentTemplate(
                    template_id="wellness_1",
                    tier=tier,
                    category=category,
                    content="Your well-being is the foundation for everything else. Take care of yourself as you pursue your goals.",
                    trigger_conditions={'wellness_score': '>50'},
                    cultural_relevance=True,
                    city_specific=None
                )
            ]
        
        return templates
    
    def _select_template_by_conditions(self, templates: List[ContentTemplate], user_data: UserData) -> ContentTemplate:
        """Select template based on trigger conditions"""
        try:
            # Filter templates by conditions
            matching_templates = []
            
            for template in templates:
                if self._check_trigger_conditions(template.trigger_conditions, user_data):
                    matching_templates.append(template)
            
            # If no templates match, return the first one
            if not matching_templates:
                return templates[0] if templates else None
            
            # Select randomly from matching templates
            return random.choice(matching_templates)
            
        except Exception as e:
            logger.error(f"Error selecting template: {e}")
            return templates[0] if templates else None
    
    def _check_trigger_conditions(self, conditions: Dict[str, Any], user_data: UserData) -> bool:
        """Check if trigger conditions are met"""
        try:
            for condition, value in conditions.items():
                if condition == 'financial_score':
                    if value.startswith('>'):
                        threshold = float(value[1:])
                        if user_data.financial_score <= threshold:
                            return False
                    elif value.startswith('<'):
                        threshold = float(value[1:])
                        if user_data.financial_score >= threshold:
                            return False
                
                # Add more condition checks as needed
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking trigger conditions: {e}")
            return True
    
    def _personalize_template(self, template: ContentTemplate, user_data: UserData) -> str:
        """Personalize template content"""
        try:
            content = template.content
            
            # Add location-specific elements
            if user_data.location in self.major_metros:
                metro_info = self.major_metros[user_data.location]
                if metro_info['cultural_hub']:
                    content += f" Your {user_data.location} location offers unique opportunities for growth and networking."
            
            # Add tier-specific depth
            if user_data.tier == FeatureTier.PROFESSIONAL:
                content += " As a professional, you have access to advanced strategies that can accelerate your progress."
            elif user_data.tier == FeatureTier.MID_TIER:
                content += " Your mid-tier status gives you access to tools that can significantly impact your financial future."
            
            return content
            
        except Exception as e:
            logger.error(f"Error personalizing template: {e}")
            return template.content if template else "Keep focusing on your goals."
    
    def _get_budget_tier_actions(self, user_data: UserData) -> List[Dict[str, Any]]:
        """Get actions for Budget tier users"""
        return [
            {
                'action': 'Track one expense today',
                'description': 'Write down every dollar you spend today. Awareness is the first step to control.',
                'category': 'financial',
                'difficulty': 'easy',
                'estimated_time': '5 minutes'
            },
            {
                'action': 'Set a small savings goal',
                'description': 'Choose one small expense to skip this week and save that money instead.',
                'category': 'financial',
                'difficulty': 'easy',
                'estimated_time': '2 minutes'
            },
            {
                'action': 'Review your biggest expense',
                'description': 'Look at your largest expense from last month. Is it aligned with your goals?',
                'category': 'financial',
                'difficulty': 'medium',
                'estimated_time': '10 minutes'
            }
        ]
    
    def _get_mid_tier_actions(self, user_data: UserData) -> List[Dict[str, Any]]:
        """Get actions for Mid-tier users"""
        return [
            {
                'action': 'Optimize your highest expense category',
                'description': 'Review your spending in your largest category and find one way to reduce it by 10%.',
                'category': 'financial',
                'difficulty': 'medium',
                'estimated_time': '15 minutes'
            },
            {
                'action': 'Research one investment option',
                'description': 'Spend 15 minutes learning about a new investment or savings vehicle.',
                'category': 'financial',
                'difficulty': 'medium',
                'estimated_time': '15 minutes'
            },
            {
                'action': 'Network with one professional',
                'description': 'Reach out to one person in your field for a brief conversation or coffee.',
                'category': 'career',
                'difficulty': 'medium',
                'estimated_time': '30 minutes'
            }
        ]
    
    def _get_professional_tier_actions(self, user_data: UserData) -> List[Dict[str, Any]]:
        """Get actions for Professional tier users"""
        return [
            {
                'action': 'Analyze your investment portfolio',
                'description': 'Review your current investments and identify one optimization opportunity.',
                'category': 'financial',
                'difficulty': 'hard',
                'estimated_time': '30 minutes'
            },
            {
                'action': 'Mentor someone in your field',
                'description': 'Share your knowledge with someone earlier in their career journey.',
                'category': 'career',
                'difficulty': 'medium',
                'estimated_time': '45 minutes'
            },
            {
                'action': 'Plan your next career move',
                'description': 'Research and plan your next professional advancement opportunity.',
                'category': 'career',
                'difficulty': 'hard',
                'estimated_time': '60 minutes'
            }
        ]
    
    def _get_default_actions(self) -> List[Dict[str, Any]]:
        """Get default actions when generation fails"""
        return [
            {
                'action': 'Review your financial goals',
                'description': 'Take a moment to reflect on what you want to achieve financially.',
                'category': 'financial',
                'difficulty': 'easy',
                'estimated_time': '5 minutes'
            }
        ]
    
    def _get_default_insight(self, user_data: UserData) -> str:
        """Get default insight when generation fails"""
        return "Your financial journey is unique and valuable. Every step forward is progress worth celebrating."
    
    def _get_default_content(self) -> Dict[str, Any]:
        """Get default content when generation fails"""
        return {
            'user_id': 0,
            'date': date.today(),
            'balance_score': 50,
            'financial_weight': 0.4,
            'wellness_weight': 0.25,
            'relationship_weight': 0.15,
            'career_weight': 0.2,
            'primary_insight': "Your financial journey is unique and valuable. Every step forward is progress worth celebrating.",
            'quick_actions': self._get_default_actions(),
            'encouragement_message': "You've got this! Every step forward is progress.",
            'surprise_element': "🌟 You're doing great! Keep focusing on your financial goals.",
            'tomorrow_teaser': "Tomorrow: More insights to help you on your financial journey.",
            'streak_count': 0,
            'tier': 'budget',
            'location': 'Unknown',
            'cultural_relevance': True,
            'city_specific': False
        }
    
    def _save_daily_outlook(self, daily_outlook: Dict[str, Any]) -> bool:
        """Save daily outlook to database"""
        try:
            conn = sqlite3.connect(self.profile_db_path)
            cursor = conn.cursor()
            
            # Insert daily outlook
            cursor.execute("""
                INSERT OR REPLACE INTO daily_outlooks 
                (user_id, date, balance_score, financial_weight, wellness_weight, 
                 relationship_weight, career_weight, primary_insight, quick_actions,
                 encouragement_message, surprise_element, streak_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                daily_outlook['user_id'],
                daily_outlook['date'],
                daily_outlook['balance_score'],
                daily_outlook['financial_weight'],
                daily_outlook['wellness_weight'],
                daily_outlook['relationship_weight'],
                daily_outlook['career_weight'],
                daily_outlook['primary_insight'],
                json.dumps(daily_outlook['quick_actions']),
                daily_outlook['encouragement_message'],
                daily_outlook['surprise_element'],
                daily_outlook['streak_count'],
                datetime.utcnow()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved daily outlook for user {daily_outlook['user_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving daily outlook: {e}")
            return False
