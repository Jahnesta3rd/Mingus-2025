#!/usr/bin/env python3
"""
Meme Data Seeding Script
========================
Script to populate the database with initial meme content for the meme splash page feature.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.models.meme_models import Meme, UserMemePreferences, UserMemeHistory
from backend.models.user import User
from backend.database import get_db_session
from backend.config import Config

# Sample meme data with inspirational content
SAMPLE_MEMES = [
    {
        "category": "faith",
        "caption_text": "Faith is taking the first step even when you don't see the whole staircase.",
        "alt_text": "A beautiful staircase leading to a bright light, symbolizing faith and hope",
        "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
        "tags": ["faith", "inspiration", "hope", "spirituality"],
        "priority": 8,
        "engagement_score": 0.85
    },
    {
        "category": "work_life",
        "caption_text": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "alt_text": "A person climbing a mountain, representing perseverance and success",
        "image_url": "https://images.unsplash.com/photo-1551632811-561732d1e306?w=800&h=600&fit=crop",
        "tags": ["success", "motivation", "career", "perseverance"],
        "priority": 9,
        "engagement_score": 0.92
    },
    {
        "category": "friendships",
        "caption_text": "A real friend is one who walks in when the rest of the world walks out.",
        "alt_text": "Two people holding hands, symbolizing true friendship",
        "image_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800&h=600&fit=crop",
        "tags": ["friendship", "loyalty", "support", "relationships"],
        "priority": 7,
        "engagement_score": 0.78
    },
    {
        "category": "children",
        "caption_text": "The greatest legacy one can pass on to one's children and grandchildren is not money or other material things accumulated in one's life, but rather a legacy of character and faith.",
        "alt_text": "A parent and child reading together, representing family values",
        "image_url": "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=800&h=600&fit=crop",
        "tags": ["family", "parenting", "legacy", "values"],
        "priority": 8,
        "engagement_score": 0.88
    },
    {
        "category": "relationships",
        "caption_text": "Love is not about finding the perfect person, but about seeing an imperfect person perfectly.",
        "alt_text": "A couple embracing, representing love and acceptance",
        "image_url": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&h=600&fit=crop",
        "tags": ["love", "relationships", "acceptance", "romance"],
        "priority": 9,
        "engagement_score": 0.91
    },
    {
        "category": "going_out",
        "caption_text": "Life is either a daring adventure or nothing at all.",
        "alt_text": "People enjoying outdoor activities, representing adventure and fun",
        "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
        "tags": ["adventure", "fun", "social", "life"],
        "priority": 6,
        "engagement_score": 0.75
    },
    {
        "category": "faith",
        "caption_text": "Prayer does not change God, it changes me.",
        "alt_text": "A peaceful meditation scene with candles and spiritual elements",
        "image_url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
        "tags": ["prayer", "meditation", "spirituality", "inner peace"],
        "priority": 7,
        "engagement_score": 0.82
    },
    {
        "category": "work_life",
        "caption_text": "The only way to do great work is to love what you do.",
        "alt_text": "A person working passionately at their desk",
        "image_url": "https://images.unsplash.com/photo-1551632811-561732d1e306?w=800&h=600&fit=crop",
        "tags": ["passion", "work", "career", "motivation"],
        "priority": 8,
        "engagement_score": 0.87
    },
    {
        "category": "friendships",
        "caption_text": "Friendship is born at that moment when one person says to another, 'What! You too? I thought I was the only one.'",
        "alt_text": "Two friends laughing together, showing connection and understanding",
        "image_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=800&h=600&fit=crop",
        "tags": ["friendship", "connection", "understanding", "shared experiences"],
        "priority": 6,
        "engagement_score": 0.79
    },
    {
        "category": "children",
        "caption_text": "Children are not things to be molded, but are people to be unfolded.",
        "alt_text": "A child exploring and learning, representing growth and development",
        "image_url": "https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=800&h=600&fit=crop",
        "tags": ["parenting", "growth", "development", "children"],
        "priority": 7,
        "engagement_score": 0.84
    }
]

def create_sample_memes(session) -> List[Meme]:
    """Create sample memes in the database"""
    print("Creating sample memes...")
    
    memes = []
    for i, meme_data in enumerate(SAMPLE_MEMES):
        meme = Meme(
            id=str(uuid.uuid4()),
            image_url=meme_data["image_url"],
            category=meme_data["category"],
            caption_text=meme_data["caption_text"],
            alt_text=meme_data["alt_text"],
            tags=json.dumps(meme_data["tags"]),
            priority=meme_data["priority"],
            engagement_score=meme_data["engagement_score"],
            is_active=True,
            view_count=0,
            like_count=0,
            share_count=0,
            source_attribution="Unsplash",
            created_at=datetime.utcnow() - timedelta(days=i),
            updated_at=datetime.utcnow()
        )
        
        session.add(meme)
        memes.append(meme)
        print(f"  Created meme: {meme_data['caption_text'][:50]}...")
    
    session.commit()
    print(f"Successfully created {len(memes)} sample memes")
    return memes

def create_default_user_preferences(session) -> None:
    """Create default meme preferences for existing users"""
    print("Creating default user preferences...")
    
    # Get all users
    users = session.query(User).all()
    
    for user in users:
        # Check if user already has preferences
        existing_prefs = session.query(UserMemePreferences).filter_by(user_id=user.id).first()
        
        if not existing_prefs:
            prefs = UserMemePreferences(
                user_id=user.id,
                memes_enabled=True,
                preferred_categories=['faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out'],
                frequency_setting='daily',
                custom_frequency_days=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(prefs)
            print(f"  Created preferences for user {user.id}")
    
    session.commit()
    print(f"Successfully created default preferences for {len(users)} users")

def create_sample_analytics(session, memes: List[Meme]) -> None:
    """Create sample analytics data for memes"""
    print("Creating sample analytics data...")
    
    # Get some users for sample data
    users = session.query(User).limit(10).all()
    
    if not users:
        print("No users found for analytics data")
        return
    
    for meme in memes[:5]:  # Only create analytics for first 5 memes
        for user in users:
            # Create some sample view history
            history = UserMemeHistory(
                id=str(uuid.uuid4()),
                user_id=user.id,
                meme_id=meme.id,
                interaction_type='view',
                viewed_at=datetime.utcnow() - timedelta(days=user.id % 7),
                created_at=datetime.utcnow()
            )
            session.add(history)
            
            # Randomly add some likes and shares
            if user.id % 3 == 0:
                like_history = UserMemeHistory(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    meme_id=meme.id,
                    interaction_type='like',
                    viewed_at=datetime.utcnow() - timedelta(days=user.id % 5),
                    created_at=datetime.utcnow()
                )
                session.add(like_history)
            
            if user.id % 5 == 0:
                share_history = UserMemeHistory(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    meme_id=meme.id,
                    interaction_type='share',
                    viewed_at=datetime.utcnow() - timedelta(days=user.id % 3),
                    created_at=datetime.utcnow()
                )
                session.add(share_history)
    
    session.commit()
    print("Successfully created sample analytics data")

def main():
    """Main seeding function"""
    print("=" * 60)
    print("MINGUS MEME DATA SEEDING SCRIPT")
    print("=" * 60)
    
    # Initialize database session
    session = get_db_session()
    
    try:
        # Check if memes already exist
        existing_memes = session.query(Meme).count()
        if existing_memes > 0:
            print(f"Found {existing_memes} existing memes. Skipping meme creation.")
        else:
            # Create sample memes
            memes = create_sample_memes(session)
            
            # Create sample analytics
            create_sample_analytics(session, memes)
        
        # Create default user preferences
        create_default_user_preferences(session)
        
        print("\n" + "=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Print summary
        total_memes = session.query(Meme).count()
        total_preferences = session.query(UserMemePreferences).count()
        total_history = session.query(UserMemeHistory).count()
        
        print(f"Total memes in database: {total_memes}")
        print(f"Total user preferences: {total_preferences}")
        print(f"Total interaction history: {total_history}")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
