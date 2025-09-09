#!/usr/bin/env python3
"""
Mingus Personal Finance App - Smart Meme Selector
Advanced meme selection system for African American users aged 25-35
"""

import sqlite3
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache
import json

# Configure logging for analytics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('meme_analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MemeObject:
    """Data class representing a meme object"""
    id: int
    image_url: str
    caption: str
    category: str
    alt_text: str
    created_at: str

class MemeSelector:
    """
    Smart meme selector for Mingus personal finance app.
    
    Features:
    - Day-of-week based category selection
    - Avoids recently viewed memes (30-day window)
    - Fallback logic for unavailable categories
    - Simple caching for performance
    - Analytics logging
    - Error handling for database issues
    """
    
    # Day-of-week to category mapping as specified
    DAY_CATEGORY_MAP = {
        0: 'faith',           # Sunday
        1: 'work_life',       # Monday - work_life/Relationships
        2: 'health',          # Tuesday - Health/Working out
        3: 'housing',         # Wednesday - Housing
        4: 'transportation',  # Thursday - Transportation
        5: 'relationships',   # Friday - Relationships
        6: 'family'           # Saturday - Kids/Family
    }
    
    # Fallback categories in order of preference
    FALLBACK_CATEGORIES = ['relationships', 'work_life', 'faith', 'family', 'health', 'housing', 'transportation']
    
    def __init__(self, db_path: str = "mingus_memes.db"):
        """
        Initialize the meme selector.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes cache TTL
        self._ensure_database_setup()
    
    def _ensure_database_setup(self) -> None:
        """
        Ensure the database has the correct schema with updated categories.
        This method updates the existing schema to match our requirements.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # First, let's check if the table exists and get its structure
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memes'")
                if not cursor.fetchone():
                    # Table doesn't exist, create it with the new schema
                    cursor.execute("""
                        CREATE TABLE memes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            image_url TEXT NOT NULL,
                            category TEXT NOT NULL CHECK (category IN (
                                'faith', 
                                'work_life', 
                                'health',
                                'housing',
                                'transportation',
                                'relationships', 
                                'family'
                            )),
                            caption TEXT NOT NULL,
                            alt_text TEXT NOT NULL,
                            is_active BOOLEAN NOT NULL DEFAULT 1,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_meme_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            meme_id INTEGER NOT NULL,
                            viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, meme_id)
                        )
                    """)
                    
                    # Create indexes
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memes_category ON memes(category)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_memes_active ON memes(is_active)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_meme_history_user_id ON user_meme_history(user_id)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_meme_history_meme_id ON user_meme_history(meme_id)")
                    
                    # Insert sample data
                    sample_memes = [
                        ('https://example.com/faith1.jpg', 'faith', 'Faith meme 1', 'Alt text 1', 1),
                        ('https://example.com/work1.jpg', 'work_life', 'Work meme 1', 'Alt text 2', 1),
                        ('https://example.com/health1.jpg', 'health', 'Health meme 1', 'Alt text 3', 1),
                        ('https://example.com/housing1.jpg', 'housing', 'Housing meme 1', 'Alt text 4', 1),
                        ('https://example.com/transport1.jpg', 'transportation', 'Transport meme 1', 'Alt text 5', 1),
                        ('https://example.com/relationship1.jpg', 'relationships', 'Relationship meme 1', 'Alt text 6', 1),
                        ('https://example.com/family1.jpg', 'family', 'Family meme 1', 'Alt text 7', 1),
                    ]
                    
                    cursor.executemany("""
                        INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                        VALUES (?, ?, ?, ?, ?)
                    """, sample_memes)
                    
                else:
                    # Table exists, we need to handle the constraint issue
                    # SQLite doesn't support ALTER TABLE to modify CHECK constraints
                    # So we'll work around it by temporarily disabling the constraint
                    
                    # Update existing memes to new categories if needed
                    category_mapping = {
                        'friendships': 'relationships',
                        'children': 'family',
                        'going_out': 'transportation'
                    }
                    
                    for old_cat, new_cat in category_mapping.items():
                        cursor.execute(
                            "UPDATE memes SET category = ? WHERE category = ?",
                            (new_cat, old_cat)
                        )
                    
                    # Add new categories if they don't exist
                    new_categories = ['health', 'housing', 'transportation']
                    for category in new_categories:
                        # Insert a placeholder meme if category doesn't exist
                        cursor.execute(
                            "SELECT COUNT(*) FROM memes WHERE category = ?",
                            (category,)
                        )
                        if cursor.fetchone()[0] == 0:
                            cursor.execute("""
                                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                f'https://example.com/placeholder_{category}.jpg',
                                category,
                                f'Placeholder meme for {category} category',
                                f'Placeholder image for {category}',
                                1
                            ))
                
                conn.commit()
                logger.info("Database schema updated successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database setup error: {e}")
            # If there's a constraint error, try to work around it
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    # Disable foreign key constraints temporarily
                    cursor.execute("PRAGMA foreign_keys = OFF")
                    
                    # Try to insert memes without the constraint
                    sample_memes = [
                        ('https://example.com/faith1.jpg', 'faith', 'Faith meme 1', 'Alt text 1', 1),
                        ('https://example.com/work1.jpg', 'work_life', 'Work meme 1', 'Alt text 2', 1),
                        ('https://example.com/health1.jpg', 'health', 'Health meme 1', 'Alt text 3', 1),
                        ('https://example.com/housing1.jpg', 'housing', 'Housing meme 1', 'Alt text 4', 1),
                        ('https://example.com/transport1.jpg', 'transportation', 'Transport meme 1', 'Alt text 5', 1),
                        ('https://example.com/relationship1.jpg', 'relationships', 'Relationship meme 1', 'Alt text 6', 1),
                        ('https://example.com/family1.jpg', 'family', 'Family meme 1', 'Alt text 7', 1),
                    ]
                    
                    for meme_data in sample_memes:
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO memes (image_url, category, caption, alt_text, is_active)
                                VALUES (?, ?, ?, ?, ?)
                            """, meme_data)
                        except sqlite3.Error:
                            # Skip if there's still an issue
                            continue
                    
                    conn.commit()
                    logger.info("Database populated with fallback method")
                    
            except Exception as fallback_error:
                logger.error(f"Fallback database setup also failed: {fallback_error}")
                # Don't raise here, let the system try to work with what it has
    
    def _get_day_category(self, date: Optional[datetime] = None) -> str:
        """
        Get the preferred category based on the day of the week.
        
        Args:
            date: Date to check (defaults to today)
            
        Returns:
            Category name for the given day
        """
        if date is None:
            date = datetime.now()
        
        # Convert Python weekday (0=Monday, 6=Sunday) to our mapping (0=Sunday, 6=Saturday)
        python_weekday = date.weekday()  # 0=Monday, 6=Sunday
        our_weekday = (python_weekday + 1) % 7  # Convert to 0=Sunday, 6=Saturday
        return self.DAY_CATEGORY_MAP.get(our_weekday, 'relationships')
    
    def _get_recently_viewed_memes(self, user_id: int, days: int = 30) -> List[int]:
        """
        Get list of meme IDs that the user has viewed in the last N days.
        
        Args:
            user_id: User ID to check
            days: Number of days to look back (default 30)
            
        Returns:
            List of meme IDs recently viewed by the user
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=days)
                cursor.execute("""
                    SELECT meme_id FROM user_meme_history 
                    WHERE user_id = ? AND viewed_at >= ?
                """, (user_id, cutoff_date))
                
                return [row[0] for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting recently viewed memes: {e}")
            return []
    
    def _get_memes_by_category(self, category: str, exclude_ids: List[int] = None) -> List[Dict]:
        """
        Get active memes from a specific category, excluding certain IDs.
        
        Args:
            category: Category to search in
            exclude_ids: List of meme IDs to exclude
            
        Returns:
            List of meme dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if exclude_ids:
                    placeholders = ','.join('?' * len(exclude_ids))
                    query = f"""
                        SELECT * FROM memes 
                        WHERE category = ? AND is_active = 1 AND id NOT IN ({placeholders})
                        ORDER BY RANDOM()
                    """
                    params = [category] + exclude_ids
                else:
                    query = """
                        SELECT * FROM memes 
                        WHERE category = ? AND is_active = 1 
                        ORDER BY RANDOM()
                    """
                    params = [category]
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting memes by category {category}: {e}")
            return []
    
    def _record_meme_view(self, user_id: int, meme_id: int) -> bool:
        """
        Record that a user viewed a specific meme.
        
        Args:
            user_id: User ID
            meme_id: Meme ID that was viewed
            
        Returns:
            True if successfully recorded, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO user_meme_history (user_id, meme_id, viewed_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (user_id, meme_id))
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error recording meme view: {e}")
            return False
    
    def _log_analytics(self, user_id: int, meme: MemeObject, selection_reason: str) -> None:
        """
        Log analytics data for tracking meme performance.
        
        Args:
            user_id: User ID
            meme: Selected meme object
            selection_reason: Reason why this meme was selected
        """
        analytics_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'meme_id': meme.id,
            'category': meme.category,
            'selection_reason': selection_reason,
            'day_of_week': datetime.now().weekday()
        }
        
        logger.info(f"MEME_ANALYTICS: {json.dumps(analytics_data)}")
    
    @lru_cache(maxsize=100)
    def _get_cached_memes(self, category: str, cache_key: str) -> Tuple[List[Dict], float]:
        """
        Simple caching mechanism for frequently accessed memes.
        
        Args:
            category: Meme category
            cache_key: Unique cache key
            
        Returns:
            Tuple of (meme_list, timestamp)
        """
        current_time = datetime.now().timestamp()
        
        # Check if we have cached data that's still valid
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if current_time - timestamp < self.cache_ttl:
                return cached_data, timestamp
        
        # Get fresh data
        memes = self._get_memes_by_category(category)
        self.cache[cache_key] = (memes, current_time)
        
        return memes, current_time
    
    def select_best_meme(self, user_id: int, date: Optional[datetime] = None) -> Optional[MemeObject]:
        """
        Select the best meme for a user based on day of week and viewing history.
        
        This is the main function that implements all the requirements:
        - Avoids memes seen in last 30 days
        - Considers day of week for category selection
        - Has fallback logic for unavailable categories
        - Includes error handling for database issues
        - Logs analytics data for tracking
        
        Args:
            user_id: ID of the user requesting a meme
            date: Optional date to use for day-of-week calculation (defaults to today)
            
        Returns:
            MemeObject with image, caption, and category, or None if no memes available
        """
        try:
            # Step 1: Determine preferred category based on day of week
            preferred_category = self._get_day_category(date)
            logger.info(f"User {user_id} - Preferred category for today: {preferred_category}")
            
            # Step 2: Get recently viewed memes to avoid repetition
            recently_viewed = self._get_recently_viewed_memes(user_id)
            logger.info(f"User {user_id} - Recently viewed {len(recently_viewed)} memes")
            
            # Step 3: Try to get a meme from the preferred category
            selected_meme = None
            selection_reason = ""
            
            # Use caching for performance
            cache_key = f"{preferred_category}_{user_id}_{len(recently_viewed)}"
            available_memes, _ = self._get_cached_memes(preferred_category, cache_key)
            
            # Filter out recently viewed memes
            filtered_memes = [m for m in available_memes if m['id'] not in recently_viewed]
            
            if filtered_memes:
                selected_meme = random.choice(filtered_memes)
                selection_reason = f"preferred_category_{preferred_category}"
                logger.info(f"User {user_id} - Selected meme from preferred category: {preferred_category}")
            else:
                # Step 4: Fallback logic - try other categories
                logger.info(f"User {user_id} - No memes in preferred category, trying fallbacks")
                
                for fallback_category in self.FALLBACK_CATEGORIES:
                    if fallback_category == preferred_category:
                        continue  # Skip the category we already tried
                    
                    fallback_cache_key = f"{fallback_category}_{user_id}_{len(recently_viewed)}"
                    fallback_memes, _ = self._get_cached_memes(fallback_category, fallback_cache_key)
                    fallback_filtered = [m for m in fallback_memes if m['id'] not in recently_viewed]
                    
                    if fallback_filtered:
                        selected_meme = random.choice(fallback_filtered)
                        selection_reason = f"fallback_category_{fallback_category}"
                        logger.info(f"User {user_id} - Selected meme from fallback category: {fallback_category}")
                        break
                
                # Step 5: Last resort - show any meme (even if recently viewed)
                if not selected_meme:
                    logger.warning(f"User {user_id} - No unviewed memes available, showing any meme")
                    all_memes = self._get_memes_by_category(preferred_category)
                    if all_memes:
                        selected_meme = random.choice(all_memes)
                        selection_reason = "any_meme_available"
                    else:
                        # Try any category
                        for category in self.FALLBACK_CATEGORIES:
                            any_memes = self._get_memes_by_category(category)
                            if any_memes:
                                selected_meme = random.choice(any_memes)
                                selection_reason = f"any_meme_from_{category}"
                                break
            
            # Step 6: Record the view and log analytics
            if selected_meme:
                # Convert to MemeObject
                meme_obj = MemeObject(
                    id=selected_meme['id'],
                    image_url=selected_meme['image_url'],
                    caption=selected_meme['caption'],
                    category=selected_meme['category'],
                    alt_text=selected_meme['alt_text'],
                    created_at=selected_meme['created_at']
                )
                
                # Record the view
                self._record_meme_view(user_id, selected_meme['id'])
                
                # Log analytics
                self._log_analytics(user_id, meme_obj, selection_reason)
                
                logger.info(f"User {user_id} - Successfully selected meme {selected_meme['id']} from {selected_meme['category']}")
                return meme_obj
            else:
                logger.warning(f"User {user_id} - No memes available in any category")
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Database error for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for user {user_id}: {e}")
            return None
    
    def get_user_meme_stats(self, user_id: int) -> Dict:
        """
        Get statistics about a user's meme viewing history.
        
        Args:
            user_id: User ID to get stats for
            
        Returns:
            Dictionary with user statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total views
                cursor.execute("SELECT COUNT(*) FROM user_meme_history WHERE user_id = ?", (user_id,))
                total_views = cursor.fetchone()[0]
                
                # Views by category
                cursor.execute("""
                    SELECT m.category, COUNT(*) as view_count 
                    FROM user_meme_history umh 
                    JOIN memes m ON umh.meme_id = m.id 
                    WHERE umh.user_id = ? 
                    GROUP BY m.category
                    ORDER BY view_count DESC
                """, (user_id,))
                category_stats = dict(cursor.fetchall())
                
                # Recent activity (last 30 days)
                cutoff_date = datetime.now() - timedelta(days=30)
                cursor.execute("""
                    SELECT COUNT(*) FROM user_meme_history 
                    WHERE user_id = ? AND viewed_at >= ?
                """, (user_id, cutoff_date))
                recent_views = cursor.fetchone()[0]
                
                return {
                    'user_id': user_id,
                    'total_views': total_views,
                    'recent_views_30_days': recent_views,
                    'category_breakdown': category_stats,
                    'most_viewed_category': max(category_stats.items(), key=lambda x: x[1])[0] if category_stats else None
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {'error': str(e)}


# Example usage and testing
def main():
    """
    Example usage of the MemeSelector class.
    This demonstrates how to use the function in a real application.
    """
    print("🎭 Mingus Meme Selector - Example Usage")
    print("=" * 50)
    
    # Initialize the selector
    selector = MemeSelector()
    
    # Test with different users
    test_users = [1, 2, 3]
    
    for user_id in test_users:
        print(f"\n👤 Testing with User {user_id}")
        print("-" * 30)
        
        # Get a meme for the user
        meme = selector.select_best_meme(user_id)
        
        if meme:
            print(f"✅ Selected Meme:")
            print(f"   ID: {meme.id}")
            print(f"   Category: {meme.category}")
            print(f"   Caption: {meme.caption}")
            print(f"   Image URL: {meme.image_url}")
            print(f"   Alt Text: {meme.alt_text}")
        else:
            print("❌ No meme available")
        
        # Get user statistics
        stats = selector.get_user_meme_stats(user_id)
        if 'error' not in stats:
            print(f"📊 User Stats:")
            print(f"   Total Views: {stats['total_views']}")
            print(f"   Recent Views (30 days): {stats['recent_views_30_days']}")
            print(f"   Most Viewed Category: {stats['most_viewed_category']}")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()
