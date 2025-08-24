"""
Meme Service for Meme Splash Page Feature
Handles meme operations, user interactions, and recommendations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import json
import random
import logging

from ..models.meme_models import Meme, UserMemeHistory, UserMemePreferences
from ..models.user import User

# Set up logging
logger = logging.getLogger(__name__)

class MemeService:
    """Service class for meme operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        # Simple in-memory cache for performance
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def create_meme(self, meme_data: Dict[str, Any]) -> Meme:
        """Create a new meme"""
        meme = Meme(
            id=str(uuid.uuid4()),
            image_url=meme_data['image_url'],
            image_file_path=meme_data.get('image_file_path'),
            category=meme_data['category'],
            caption_text=meme_data['caption_text'],
            alt_text=meme_data['alt_text'],
            priority=meme_data.get('priority', 5),
            tags=meme_data.get('tags'),
            source_attribution=meme_data.get('source_attribution'),
            admin_notes=meme_data.get('admin_notes')
        )
        
        self.db.add(meme)
        self.db.commit()
        self.db.refresh(meme)
        return meme
    
    def get_meme_by_id(self, meme_id: str) -> Optional[Meme]:
        """Get a meme by ID"""
        return self.db.query(Meme).filter(Meme.id == meme_id).first()
    
    def get_active_memes_by_category(self, category: str, limit: int = 10) -> List[Meme]:
        """Get active memes by category, ordered by priority and engagement"""
        return self.db.query(Meme).filter(
            and_(
                Meme.category == category,
                Meme.is_active == True
            )
        ).order_by(
            desc(Meme.priority),
            desc(Meme.engagement_score)
        ).limit(limit).all()
    
    def get_all_active_memes(self, limit: int = 50) -> List[Meme]:
        """Get all active memes, ordered by priority and engagement"""
        return self.db.query(Meme).filter(
            Meme.is_active == True
        ).order_by(
            desc(Meme.priority),
            desc(Meme.engagement_score)
        ).limit(limit).all()
    
    def get_all_memes(self, limit: int = 100) -> List[Meme]:
        """Get all memes (active and inactive), ordered by creation date"""
        return self.db.query(Meme).order_by(
            desc(Meme.created_at)
        ).limit(limit).all()
    
    def get_memes_for_user(self, user_id: int, limit: int = 1) -> List[Meme]:
        """Get memes for a specific user based on their preferences"""
        # Get user preferences
        user_prefs = self.get_user_preferences(user_id)
        if not user_prefs or not user_prefs.memes_enabled:
            return []
        
        # Check if user should see a meme based on frequency
        if not user_prefs.should_show_meme():
            return []
        
        # Get user's preferred categories
        preferred_categories = user_prefs.preferred_categories_list
        if not preferred_categories:
            # Default to all categories if none specified
            preferred_categories = ['monday_career', 'tuesday_health', 'wednesday_home', 'thursday_relationships', 'friday_entertainment', 'saturday_kids', 'sunday_faith']
        
        # Get memes user hasn't seen recently
        recently_viewed = self.get_recently_viewed_meme_ids(user_id, days=7)
        
        # Query for memes
        query = self.db.query(Meme).filter(
            and_(
                Meme.is_active == True,
                Meme.category.in_(preferred_categories),
                ~Meme.id.in_(recently_viewed) if recently_viewed else True
            )
        ).order_by(
            desc(Meme.priority),
            desc(Meme.engagement_score)
        ).limit(limit)
        
        memes = query.all()
        
        # Update user's last meme shown
        if memes:
            user_prefs.last_meme_shown_at = datetime.utcnow()
            user_prefs.last_meme_shown_id = memes[0].id
            self.db.commit()
        
        return memes
    
    def get_todays_meme_for_user(self, user_id: int, limit: int = 1) -> List[Meme]:
        """Get today's themed meme for a specific user based on day of week"""
        # Get user preferences
        user_prefs = self.get_user_preferences(user_id)
        if not user_prefs or not user_prefs.memes_enabled:
            return []
        
        # Check if user should see a meme based on frequency
        if not user_prefs.should_show_meme():
            return []
        
        # Get today's category based on day of week
        today = datetime.utcnow()
        day_of_week = today.weekday()  # Monday = 0, Sunday = 6
        
        day_categories = {
            0: 'monday_career',      # Monday
            1: 'tuesday_health',     # Tuesday
            2: 'wednesday_home',     # Wednesday
            3: 'thursday_relationships', # Thursday
            4: 'friday_entertainment',   # Friday
            5: 'saturday_kids',      # Saturday
            6: 'sunday_faith'        # Sunday
        }
        
        todays_category = day_categories.get(day_of_week, 'monday_career')
        
        # Check if user has this category in their preferences
        preferred_categories = user_prefs.preferred_categories_list
        if preferred_categories and todays_category not in preferred_categories:
            # If user doesn't prefer today's category, fall back to any preferred category
            category_filter = preferred_categories
        else:
            # Use today's category
            category_filter = [todays_category]
        
        # Get memes user hasn't seen recently
        recently_viewed = self.get_recently_viewed_meme_ids(user_id, days=7)
        
        # Query for memes
        query = self.db.query(Meme).filter(
            and_(
                Meme.is_active == True,
                Meme.category.in_(category_filter),
                ~Meme.id.in_(recently_viewed) if recently_viewed else True
            )
        ).order_by(
            desc(Meme.priority),
            desc(Meme.engagement_score)
        ).limit(limit)
        
        memes = query.all()
        
        # Update user's last meme shown
        if memes:
            user_prefs.last_meme_shown_at = datetime.utcnow()
            user_prefs.last_meme_shown_id = memes[0].id
            self.db.commit()
        
        return memes
    
    def record_user_interaction(self, user_id: int, meme_id: str, 
                               interaction_type: str = 'view', 
                               time_spent: int = 0,
                               session_id: str = None,
                               source_page: str = None,
                               device_type: str = None,
                               user_agent: str = None,
                               ip_address: str = None) -> UserMemeHistory:
        """Record a user's interaction with a meme"""
        history = UserMemeHistory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            meme_id=meme_id,
            interaction_type=interaction_type,
            time_spent_seconds=time_spent,
            session_id=session_id,
            source_page=source_page,
            device_type=device_type,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        self.db.add(history)
        
        # Update meme engagement metrics
        meme = self.get_meme_by_id(meme_id)
        if meme:
            if interaction_type == 'view':
                meme.view_count += 1
            elif interaction_type == 'like':
                meme.like_count += 1
            elif interaction_type == 'share':
                meme.share_count += 1
            
            # Update engagement score (simple formula: likes + shares / views)
            if meme.view_count > 0:
                meme.engagement_score = (meme.like_count + meme.share_count) / meme.view_count
        
        self.db.commit()
        self.db.refresh(history)
        return history
    
    def get_user_preferences(self, user_id: int) -> Optional[UserMemePreferences]:
        """Get user's meme preferences"""
        return self.db.query(UserMemePreferences).filter(
            UserMemePreferences.user_id == user_id
        ).first()
    
    def create_user_preferences(self, user_id: int, preferences_data: Dict[str, Any]) -> UserMemePreferences:
        """Create user meme preferences"""
        prefs = UserMemePreferences(
            id=str(uuid.uuid4()),
            user_id=user_id,
            memes_enabled=preferences_data.get('memes_enabled', True),
            preferred_categories=preferences_data.get('preferred_categories'),
            frequency_setting=preferences_data.get('frequency_setting', 'daily'),
            custom_frequency_days=preferences_data.get('custom_frequency_days', 1)
        )
        
        self.db.add(prefs)
        self.db.commit()
        self.db.refresh(prefs)
        return prefs
    
    def update_user_preferences(self, user_id: int, preferences_data: Dict[str, Any]) -> Optional[UserMemePreferences]:
        """Update user's meme preferences"""
        prefs = self.get_user_preferences(user_id)
        if not prefs:
            return self.create_user_preferences(user_id, preferences_data)
        
        # Update fields
        if 'memes_enabled' in preferences_data:
            prefs.memes_enabled = preferences_data['memes_enabled']
            if not prefs.memes_enabled:
                prefs.opt_out_date = datetime.utcnow()
                prefs.opt_out_reason = preferences_data.get('opt_out_reason')
        
        if 'preferred_categories' in preferences_data:
            prefs.preferred_categories_list = preferences_data['preferred_categories']
        
        if 'frequency_setting' in preferences_data:
            prefs.frequency_setting = preferences_data['frequency_setting']
        
        if 'custom_frequency_days' in preferences_data:
            prefs.custom_frequency_days = preferences_data['custom_frequency_days']
        
        self.db.commit()
        self.db.refresh(prefs)
        return prefs
    
    def get_recently_viewed_meme_ids(self, user_id: int, days: int = 7) -> List[str]:
        """Get meme IDs that user has viewed recently"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        results = self.db.query(UserMemeHistory.meme_id).filter(
            and_(
                UserMemeHistory.user_id == user_id,
                UserMemeHistory.viewed_at >= cutoff_date
            )
        ).distinct().all()
        
        return [result[0] for result in results]
    
    def get_user_meme_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's meme interaction statistics"""
        # Get total interactions
        total_interactions = self.db.query(func.count(UserMemeHistory.id)).filter(
            UserMemeHistory.user_id == user_id
        ).scalar()
        
        # Get interactions by type
        interactions_by_type = self.db.query(
            UserMemeHistory.interaction_type,
            func.count(UserMemeHistory.id)
        ).filter(
            UserMemeHistory.user_id == user_id
        ).group_by(UserMemeHistory.interaction_type).all()
        
        # Get favorite categories
        favorite_categories = self.db.query(
            Meme.category,
            func.count(UserMemeHistory.id)
        ).join(UserMemeHistory).filter(
            UserMemeHistory.user_id == user_id,
            UserMemeHistory.interaction_type == 'like'
        ).group_by(Meme.category).order_by(
            desc(func.count(UserMemeHistory.id))
        ).limit(3).all()
        
        return {
            'total_interactions': total_interactions,
            'interactions_by_type': dict(interactions_by_type),
            'favorite_categories': [cat[0] for cat in favorite_categories]
        }
    
    def get_meme_analytics(self) -> Dict[str, Any]:
        """Get overall meme analytics"""
        # Total memes by category
        memes_by_category = self.db.query(
            Meme.category,
            func.count(Meme.id)
        ).filter(Meme.is_active == True).group_by(Meme.category).all()
        
        # Top performing memes
        top_memes = self.db.query(Meme).filter(
            Meme.is_active == True
        ).order_by(
            desc(Meme.engagement_score)
        ).limit(10).all()
        
        # Total interactions today
        today = datetime.utcnow().date()
        today_interactions = self.db.query(func.count(UserMemeHistory.id)).filter(
            func.date(UserMemeHistory.created_at) == today
        ).scalar()
        
        return {
            'memes_by_category': dict(memes_by_category),
            'top_memes': [meme.to_dict() for meme in top_memes],
            'today_interactions': today_interactions
        }
    
    def seed_sample_memes(self):
        """Seed the database with sample memes"""
        sample_memes = [
            # Monday - Career & Business
            {
                'image_url': 'https://mingus-app.com/memes/monday_career/monday-motivation.jpg',
                'category': 'monday_career',
                'caption_text': 'Monday motivation: Building wealth one paycheck at a time 💼💪',
                'alt_text': 'A person in business attire flexing muscles with money symbols',
                'tags': ['career', 'motivation', 'wealth', 'monday', 'business'],
                'priority': 9
            },
            {
                'image_url': 'https://mingus-app.com/memes/monday_career/side-hustle-life.jpg',
                'category': 'monday_career',
                'caption_text': 'Side hustle life: Because one income stream is never enough 🚀💰',
                'alt_text': 'Multiple streams of water flowing into one bucket',
                'tags': ['career', 'side-hustle', 'income', 'multiple-streams', 'business'],
                'priority': 8
            },
            {
                'image_url': 'https://mingus-app.com/memes/monday_career/career-growth.jpg',
                'category': 'monday_career',
                'caption_text': 'Investing in yourself is the best investment you can make 📈🎯',
                'alt_text': 'A person climbing a ladder made of books and certificates',
                'tags': ['career', 'investment', 'growth', 'education', 'professional'],
                'priority': 9
            },
            
            # Tuesday - Health & Wellness
            {
                'image_url': 'https://mingus-app.com/memes/tuesday_health/health-investment.jpg',
                'category': 'tuesday_health',
                'caption_text': 'Your health is an investment, not an expense 🏃‍♀️💪',
                'alt_text': 'A person exercising with dollar signs representing health investment',
                'tags': ['health', 'wellness', 'investment', 'fitness', 'medical'],
                'priority': 9
            },
            {
                'image_url': 'https://mingus-app.com/memes/tuesday_health/medical-savings.jpg',
                'category': 'tuesday_health',
                'caption_text': 'Emergency fund + health savings = peace of mind 🏥💰',
                'alt_text': 'A medical cross with a piggy bank and peace sign',
                'tags': ['health', 'emergency-fund', 'medical', 'savings', 'peace-of-mind'],
                'priority': 8
            },
            {
                'image_url': 'https://mingus-app.com/memes/tuesday_health/wellness-budget.jpg',
                'category': 'tuesday_health',
                'caption_text': 'Budgeting for wellness today saves money tomorrow 🌱💚',
                'alt_text': 'A budget planner with healthy food and wellness items',
                'tags': ['health', 'wellness', 'budgeting', 'prevention', 'savings'],
                'priority': 7
            },
            
            # Wednesday - Home & Transportation
            {
                'image_url': 'https://mingus-app.com/memes/wednesday_home/home-investment.jpg',
                'category': 'wednesday_home',
                'caption_text': 'Your home is more than shelter, it\'s an investment 🏠📈',
                'alt_text': 'A house with a chart showing upward growth',
                'tags': ['home', 'investment', 'property', 'housing', 'real-estate'],
                'priority': 9
            },
            {
                'image_url': 'https://mingus-app.com/memes/wednesday_home/transportation-smart.jpg',
                'category': 'wednesday_home',
                'caption_text': 'Smart transportation choices = more money in your pocket 🚗💡',
                'alt_text': 'A person choosing between different transportation options with money saved',
                'tags': ['transportation', 'smart-choices', 'savings', 'commute', 'efficiency'],
                'priority': 8
            },
            {
                'image_url': 'https://mingus-app.com/memes/wednesday_home/home-improvement.jpg',
                'category': 'wednesday_home',
                'caption_text': 'Home improvements that pay for themselves 🛠️💸',
                'alt_text': 'Tools and materials with a return on investment chart',
                'tags': ['home', 'improvement', 'roi', 'investment', 'value'],
                'priority': 7
            },
            
            # Thursday - Relationships & Family
            {
                'image_url': 'https://mingus-app.com/memes/thursday_relationships/money-talks.jpg',
                'category': 'thursday_relationships',
                'caption_text': 'Couples who budget together, stay together 💕💰',
                'alt_text': 'Two people working on a budget together',
                'tags': ['relationships', 'couples', 'budgeting', 'communication', 'family'],
                'priority': 9
            },
            {
                'image_url': 'https://mingus-app.com/memes/thursday_relationships/financial-goals.jpg',
                'category': 'thursday_relationships',
                'caption_text': 'Shared financial goals make relationships stronger 🎯💪',
                'alt_text': 'Two people reaching for the same financial target',
                'tags': ['relationships', 'goals', 'partnership', 'strength', 'family'],
                'priority': 8
            },
            {
                'image_url': 'https://mingus-app.com/memes/thursday_relationships/money-mindset.jpg',
                'category': 'thursday_relationships',
                'caption_text': 'Finding someone who matches your money mindset is priceless 💎❤️',
                'alt_text': 'Two puzzle pieces fitting together with money symbols',
                'tags': ['relationships', 'mindset', 'compatibility', 'values', 'family'],
                'priority': 7
            },
            
            # Friday - Entertainment & Fun
            {
                'image_url': 'https://mingus-app.com/memes/friday_entertainment/weekend-fun.jpg',
                'category': 'friday_entertainment',
                'caption_text': 'Friday vibes: Having fun doesn\'t have to break the bank 🎉💸',
                'alt_text': 'A person enjoying themselves while watching their wallet',
                'tags': ['entertainment', 'fun', 'budget', 'weekend', 'friday'],
                'priority': 9
            },
            {
                'image_url': 'https://mingus-app.com/memes/friday_entertainment/social-spending.jpg',
                'category': 'friday_entertainment',
                'caption_text': 'Social spending: Finding the balance between fun and financial responsibility ⚖️🎊',
                'alt_text': 'A scale balancing fun activities and savings',
                'tags': ['entertainment', 'balance', 'social', 'responsibility', 'weekend'],
                'priority': 8
            },
            {
                'image_url': 'https://mingus-app.com/memes/friday_entertainment/memories-over-money.jpg',
                'category': 'friday_entertainment',
                'caption_text': 'Creating memories is priceless, but being smart about it is priceless too 📸💡',
                'alt_text': 'A camera capturing happy moments with a budget in the background',
                'tags': ['entertainment', 'memories', 'smart-spending', 'experiences', 'weekend'],
                'priority': 7
            },
            
            # Saturday - Kids & Education
            {
                'image_url': 'https://mingus-app.com/memes/saturday_kids/college-fund.jpg',
                'category': 'saturday_kids',
                'caption_text': 'Building a college fund one diaper at a time 🍼🎓',
                'alt_text': 'A piggy bank filled with baby items and graduation cap',
                'tags': ['kids', 'college', 'savings', 'education', 'children'],
                'priority': 9
            },
            {
                'image_url': 'https://mingus-app.com/memes/saturday_kids/legacy-building.jpg',
                'category': 'saturday_kids',
                'caption_text': 'Creating generational wealth for the little ones 👶💎',
                'alt_text': 'A family tree with money growing on the branches',
                'tags': ['kids', 'legacy', 'generational-wealth', 'family', 'children'],
                'priority': 8
            },
            {
                'image_url': 'https://mingus-app.com/memes/saturday_kids/financial-education.jpg',
                'category': 'saturday_kids',
                'caption_text': 'Teaching kids about money: The gift that keeps on giving 📚💡',
                'alt_text': 'A parent and child learning about money together',
                'tags': ['kids', 'education', 'teaching', 'financial-literacy', 'children'],
                'priority': 7
            },
            
            # Sunday - Faith & Reflection
            {
                'image_url': 'https://mingus-app.com/memes/sunday_faith/blessed-budget.jpg',
                'category': 'sunday_faith',
                'caption_text': 'When you finally stick to your budget and God rewards you with unexpected income 🙏💰',
                'alt_text': 'A person praying with dollar bills floating around them',
                'tags': ['faith', 'budgeting', 'blessings', 'income', 'reflection'],
                'priority': 9
            },
            {
                'image_url': 'https://mingus-app.com/memes/sunday_faith/trust-the-process.jpg',
                'category': 'sunday_faith',
                'caption_text': 'Trusting God with your finances while still being responsible with your money 💪✝️',
                'alt_text': 'A person balancing a cross and a piggy bank',
                'tags': ['faith', 'trust', 'responsibility', 'balance', 'reflection'],
                'priority': 8
            },
            {
                'image_url': 'https://mingus-app.com/memes/sunday_faith/grateful-heart.jpg',
                'category': 'sunday_faith',
                'caption_text': 'Grateful for what I have, working for what I want, and trusting God for what I need 🙌',
                'alt_text': 'A heart made of coins with a cross in the center',
                'tags': ['faith', 'gratitude', 'goals', 'trust', 'reflection'],
                'priority': 7
            }
        ]
        
        for meme_data in sample_memes:
            meme_data['tags'] = json.dumps(meme_data['tags'])
            self.create_meme(meme_data)

    def select_best_meme_for_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Select the best meme to show a user based on their preferences and context.
        
        This function implements a comprehensive meme selection algorithm that:
        1. Checks if user has opted out of memes (FIRST PRIORITY)
        2. Respects user's category preferences and frequency settings
        3. Avoids showing memes the user saw in the last 30 days
        4. Considers day of week for contextual relevance
        5. Includes fallback logic if no memes available in preferred category
        6. Handles database errors gracefully
        7. Logs analytics data for tracking
        8. Tracks and respects permanent opt-outs
        
        Args:
            user_id (int): The ID of the user requesting a meme
            
        Returns:
            Optional[Dict[str, Any]]: Meme object with image, caption, category, or None if no meme should be shown
            
        Raises:
            Exception: Logs database errors but doesn't crash the application
        """
        try:
            # Check cache first for performance
            cache_key = f"meme_selection_{user_id}"
            if cache_key in self._cache:
                cached_result, timestamp = self._cache[cache_key]
                if (datetime.utcnow() - timestamp).seconds < self._cache_ttl:
                    logger.info(f"Returning cached meme selection for user {user_id}")
                    return cached_result
            
            # STEP 1: Check if user has opted out of memes (FIRST PRIORITY)
            user_prefs = self.get_user_preferences(user_id)
            if not user_prefs or not user_prefs.memes_enabled:
                logger.info(f"User {user_id} has opted out of memes - returning None")
                self._log_analytics(user_id, "meme_opt_out", {"reason": "user_disabled"})
                return None
            
            # STEP 2: Check frequency settings
            if not user_prefs.should_show_meme():
                logger.info(f"User {user_id} not due for meme based on frequency settings")
                self._log_analytics(user_id, "meme_frequency_limit", {
                    "frequency_setting": user_prefs.frequency_setting,
                    "last_shown": user_prefs.last_meme_shown_at.isoformat() if user_prefs.last_meme_shown_at else None
                })
                return None
            
            # STEP 3: Get user's preferred categories
            preferred_categories = user_prefs.preferred_categories_list
            if not preferred_categories:
                # Default categories if none specified
                preferred_categories = [
                    'monday_career', 'tuesday_health', 'wednesday_home', 
                    'thursday_relationships', 'friday_entertainment', 
                    'saturday_kids', 'sunday_faith'
                ]
            
            # STEP 4: Consider day of week for contextual relevance
            today = datetime.utcnow()
            day_of_week = today.weekday()  # Monday = 0, Sunday = 6
            
            day_categories = {
                0: 'monday_career',      # Monday - Career & work life
                1: 'tuesday_health',     # Tuesday - Health & wellness
                2: 'wednesday_home',     # Wednesday - Home & transportation
                3: 'thursday_relationships', # Thursday - Relationships & family
                4: 'friday_entertainment',   # Friday - Entertainment & going out
                5: 'saturday_kids',      # Saturday - Kids & education
                6: 'sunday_faith'        # Sunday - Faith & reflection
            }
            
            todays_category = day_categories.get(day_of_week, 'monday_career')
            
            # STEP 5: Get memes user hasn't seen in last 30 days
            recently_viewed_meme_ids = self.get_recently_viewed_meme_ids(user_id, days=30)
            
            # STEP 6: Build query with priority logic
            # First try: Today's category + user preferences
            if todays_category in preferred_categories:
                category_filter = [todays_category]
                fallback_categories = [cat for cat in preferred_categories if cat != todays_category]
            else:
                # If user doesn't prefer today's category, use all preferred categories
                category_filter = preferred_categories
                fallback_categories = []
            
            # Query for memes in preferred categories
            meme = self._query_memes_for_user(
                user_id, category_filter, recently_viewed_meme_ids
            )
            
            # STEP 7: Fallback logic if no memes in preferred category
            if not meme and fallback_categories:
                logger.info(f"No memes found in today's category for user {user_id}, trying fallback categories")
                meme = self._query_memes_for_user(
                    user_id, fallback_categories, recently_viewed_meme_ids
                )
            
            # STEP 8: Final fallback - any available meme
            if not meme:
                logger.info(f"No memes found in preferred categories for user {user_id}, trying any available meme")
                meme = self._query_memes_for_user(user_id, None, recently_viewed_meme_ids)
            
            # STEP 9: Update user's last meme shown and cache result
            if meme:
                user_prefs.last_meme_shown_at = datetime.utcnow()
                user_prefs.last_meme_shown_id = meme.id
                self.db.commit()
                
                # Create meme object for return
                meme_object = {
                    'id': meme.id,
                    'image': meme.image_url,
                    'caption': meme.caption_text,
                    'category': meme.category,
                    'alt_text': meme.alt_text,
                    'tags': meme.tags_list
                }
                
                # Cache the result
                self._cache[cache_key] = (meme_object, datetime.utcnow())
                
                # Log analytics
                self._log_analytics(user_id, "meme_shown", {
                    "meme_id": meme.id,
                    "category": meme.category,
                    "day_of_week": day_of_week,
                    "todays_category": todays_category,
                    "used_fallback": not meme.category in category_filter
                })
                
                logger.info(f"Selected meme {meme.id} (category: {meme.category}) for user {user_id}")
                return meme_object
            else:
                # No memes available
                self._log_analytics(user_id, "no_memes_available", {
                    "preferred_categories": preferred_categories,
                    "recently_viewed_count": len(recently_viewed_meme_ids)
                })
                logger.warning(f"No suitable memes found for user {user_id}")
                return None
                
        except Exception as e:
            # STEP 10: Error handling - log but don't crash
            logger.error(f"Error selecting meme for user {user_id}: {str(e)}")
            self._log_analytics(user_id, "meme_selection_error", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return None
    
    def _query_memes_for_user(self, user_id: int, categories: Optional[List[str]], 
                             recently_viewed_ids: List[str]) -> Optional[Meme]:
        """
        Helper method to query memes with specific criteria.
        
        Args:
            user_id (int): User ID
            categories (Optional[List[str]]): Categories to filter by, None for all
            recently_viewed_ids (List[str]): Meme IDs to exclude
            
        Returns:
            Optional[Meme]: Best matching meme or None
        """
        query = self.db.query(Meme).filter(
            and_(
                Meme.is_active == True,
                ~Meme.id.in_(recently_viewed_ids) if recently_viewed_ids else True
            )
        )
        
        # Add category filter if specified
        if categories:
            query = query.filter(Meme.category.in_(categories))
        
        # Order by priority and engagement score
        meme = query.order_by(
            desc(Meme.priority),
            desc(Meme.engagement_score),
            desc(Meme.created_at)  # Newer memes as final tiebreaker
        ).first()
        
        return meme
    
    def _log_analytics(self, user_id: int, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Log analytics data for tracking meme selection patterns.
        
        Args:
            user_id (int): User ID
            event_type (str): Type of event (e.g., 'meme_shown', 'meme_opt_out')
            event_data (Dict[str, Any]): Additional event data
        """
        try:
            # In a production environment, this would send to an analytics service
            # For now, we'll just log it
            analytics_data = {
                'user_id': user_id,
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': datetime.utcnow().isoformat(),
                'session_id': f"meme_analytics_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}"
            }
            
            logger.info(f"Meme Analytics: {json.dumps(analytics_data)}")
            
            # TODO: Send to analytics service (e.g., Google Analytics, Mixpanel, etc.)
            # self._send_to_analytics_service(analytics_data)
            
        except Exception as e:
            logger.error(f"Error logging analytics for user {user_id}: {str(e)}")
