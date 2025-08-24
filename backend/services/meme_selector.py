"""
Meme Selector Function for Personal Finance App
===============================================

A comprehensive Python function for selecting the best meme to show a user in the Mingus
personal finance app. This function is designed for African Americans age 25-35, connecting
wellness to money decisions.

Author: MINGUS Development Team
Date: January 2025
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory cache for performance
_meme_cache = {}
_cache_ttl = 300  # 5 minutes cache TTL


def select_best_meme_for_user(user_id: int, db_path: str = "instance/mingus.db") -> Optional[Dict[str, Any]]:
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
        db_path (str): Path to the SQLite database file
        
    Returns:
        Optional[Dict[str, Any]]: Meme object with image, caption, category, or None if no meme should be shown
        
    Example:
        >>> meme = select_best_meme_for_user(123)
        >>> if meme:
        ...     print(f"Showing meme: {meme['caption']}")
        ... else:
        ...     print("No meme to show")
    """
    try:
        # Check cache first for performance
        cache_key = f"meme_selection_{user_id}"
        if cache_key in _meme_cache:
            cached_result, timestamp = _meme_cache[cache_key]
            if (datetime.utcnow() - timestamp).seconds < _cache_ttl:
                logger.info(f"Returning cached meme selection for user {user_id}")
                return cached_result
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        try:
            # STEP 1: Check if user has opted out of memes (FIRST PRIORITY)
            user_prefs = _get_user_meme_preferences(cursor, user_id)
            if not user_prefs or not user_prefs['memes_enabled']:
                logger.info(f"User {user_id} has opted out of memes - returning None")
                _log_analytics(user_id, "meme_opt_out", {"reason": "user_disabled"})
                return None
            
            # STEP 2: Check frequency settings
            if not _should_show_meme(user_prefs):
                logger.info(f"User {user_id} not due for meme based on frequency settings")
                _log_analytics(user_id, "meme_frequency_limit", {
                    "frequency_setting": user_prefs['frequency_setting'],
                    "last_shown": user_prefs['last_meme_shown_at']
                })
                return None
            
            # STEP 3: Get user's preferred categories
            preferred_categories = _get_preferred_categories(user_prefs)
            
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
            recently_viewed_meme_ids = _get_recently_viewed_meme_ids(cursor, user_id, days=30)
            
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
            meme = _query_memes_for_user(cursor, category_filter, recently_viewed_meme_ids)
            
            # STEP 7: Fallback logic if no memes in preferred category
            if not meme and fallback_categories:
                logger.info(f"No memes found in today's category for user {user_id}, trying fallback categories")
                meme = _query_memes_for_user(cursor, fallback_categories, recently_viewed_meme_ids)
            
            # STEP 8: Final fallback - any available meme
            if not meme:
                logger.info(f"No memes found in preferred categories for user {user_id}, trying any available meme")
                meme = _query_memes_for_user(cursor, None, recently_viewed_meme_ids)
            
            # STEP 9: Update user's last meme shown and cache result
            if meme:
                _update_user_last_meme_shown(cursor, user_id, meme['id'])
                conn.commit()
                
                # Create meme object for return
                meme_object = {
                    'id': meme['id'],
                    'image': meme['image_url'],
                    'caption': meme['caption_text'],
                    'category': meme['category'],
                    'alt_text': meme['alt_text'],
                    'tags': _parse_tags(meme['tags'])
                }
                
                # Cache the result
                _meme_cache[cache_key] = (meme_object, datetime.utcnow())
                
                # Log analytics
                _log_analytics(user_id, "meme_shown", {
                    "meme_id": meme['id'],
                    "category": meme['category'],
                    "day_of_week": day_of_week,
                    "todays_category": todays_category,
                    "used_fallback": not meme['category'] in category_filter
                })
                
                logger.info(f"Selected meme {meme['id']} (category: {meme['category']}) for user {user_id}")
                return meme_object
            else:
                # No memes available
                _log_analytics(user_id, "no_memes_available", {
                    "preferred_categories": preferred_categories,
                    "recently_viewed_count": len(recently_viewed_meme_ids)
                })
                logger.warning(f"No suitable memes found for user {user_id}")
                return None
                
        finally:
            conn.close()
            
    except Exception as e:
        # STEP 10: Error handling - log but don't crash
        logger.error(f"Error selecting meme for user {user_id}: {str(e)}")
        _log_analytics(user_id, "meme_selection_error", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        return None


def _get_user_meme_preferences(cursor: sqlite3.Cursor, user_id: int) -> Optional[Dict[str, Any]]:
    """Get user's meme preferences from database."""
    cursor.execute("""
        SELECT * FROM user_meme_preferences 
        WHERE user_id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    return dict(result) if result else None


def _should_show_meme(user_prefs: Dict[str, Any]) -> bool:
    """Determine if a meme should be shown based on frequency settings."""
    if not user_prefs['memes_enabled']:
        return False
    
    if user_prefs['frequency_setting'] == 'disabled':
        return False
    
    if not user_prefs['last_meme_shown_at']:
        return True
    
    # Parse the last shown date
    try:
        last_shown = datetime.fromisoformat(user_prefs['last_meme_shown_at'])
        now = datetime.utcnow()
        days_since_last = (now - last_shown).days
        
        if user_prefs['frequency_setting'] == 'daily':
            return days_since_last >= 1
        elif user_prefs['frequency_setting'] == 'weekly':
            return days_since_last >= 7
        elif user_prefs['frequency_setting'] == 'custom':
            return days_since_last >= user_prefs['custom_frequency_days']
        
        return True
    except (ValueError, TypeError):
        # If date parsing fails, show meme
        return True


def _get_preferred_categories(user_prefs: Dict[str, Any]) -> List[str]:
    """Get user's preferred categories, with defaults if none specified."""
    if user_prefs['preferred_categories']:
        try:
            return json.loads(user_prefs['preferred_categories'])
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Default categories if none specified
    return [
        'monday_career', 'tuesday_health', 'wednesday_home', 
        'thursday_relationships', 'friday_entertainment', 
        'saturday_kids', 'sunday_faith'
    ]


def _get_recently_viewed_meme_ids(cursor: sqlite3.Cursor, user_id: int, days: int = 30) -> List[str]:
    """Get meme IDs that user has viewed recently."""
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    cursor.execute("""
        SELECT DISTINCT meme_id FROM user_meme_history 
        WHERE user_id = ? AND viewed_at >= ?
    """, (user_id, cutoff_date))
    
    return [row['meme_id'] for row in cursor.fetchall()]


def _query_memes_for_user(cursor: sqlite3.Cursor, categories: Optional[List[str]], 
                         recently_viewed_ids: List[str]) -> Optional[Dict[str, Any]]:
    """Query memes with specific criteria."""
    # Build the base query
    query = """
        SELECT * FROM memes 
        WHERE is_active = 1
    """
    params = []
    
    # Add category filter if specified
    if categories:
        placeholders = ','.join(['?' for _ in categories])
        query += f" AND category IN ({placeholders})"
        params.extend(categories)
    
    # Add recently viewed filter
    if recently_viewed_ids:
        placeholders = ','.join(['?' for _ in recently_viewed_ids])
        query += f" AND id NOT IN ({placeholders})"
        params.extend(recently_viewed_ids)
    
    # Order by priority and engagement score
    query += " ORDER BY priority DESC, engagement_score DESC, created_at DESC LIMIT 1"
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    
    return dict(result) if result else None


def _update_user_last_meme_shown(cursor: sqlite3.Cursor, user_id: int, meme_id: str) -> None:
    """Update user's last meme shown timestamp."""
    cursor.execute("""
        UPDATE user_meme_preferences 
        SET last_meme_shown_at = ?, last_meme_shown_id = ?, updated_at = ?
        WHERE user_id = ?
    """, (datetime.utcnow().isoformat(), meme_id, datetime.utcnow().isoformat(), user_id))


def _parse_tags(tags: Optional[str]) -> List[str]:
    """Parse tags from JSON string."""
    if not tags:
        return []
    try:
        return json.loads(tags)
    except (json.JSONDecodeError, TypeError):
        return []


def _log_analytics(user_id: int, event_type: str, event_data: Dict[str, Any]) -> None:
    """Log analytics data for tracking meme selection patterns."""
    try:
        # In a production environment, this would send to an analytics service
        analytics_data = {
            'user_id': user_id,
            'event_type': event_type,
            'event_data': event_data,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': f"meme_analytics_{user_id}_{datetime.utcnow().strftime('%Y%m%d')}"
        }
        
        logger.info(f"Meme Analytics: {json.dumps(analytics_data)}")
        
        # TODO: Send to analytics service (e.g., Google Analytics, Mixpanel, etc.)
        # _send_to_analytics_service(analytics_data)
        
    except Exception as e:
        logger.error(f"Error logging analytics for user {user_id}: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    user_id = 123
    meme = select_best_meme_for_user(user_id)
    
    if meme:
        print(f"Selected meme for user {user_id}:")
        print(f"  ID: {meme['id']}")
        print(f"  Category: {meme['category']}")
        print(f"  Caption: {meme['caption']}")
        print(f"  Image: {meme['image']}")
    else:
        print(f"No meme selected for user {user_id}")
