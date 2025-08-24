#!/usr/bin/env python3
"""
Simple test script for UserArticleProgress using correct field names
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models import (
    UserArticleProgress, Article, User, db_session
)
import uuid
from datetime import datetime

def main():
    """Test the progress tracking functionality with correct field names"""
    
    print("📊 Testing UserArticleProgress Model")
    print("=" * 50)
    
    # Get test user and article
    test_user_id = 1
    beginner_article = db_session.query(Article).filter_by(difficulty_level='Beginner').first()
    
    if not beginner_article:
        print("❌ No beginner article found for testing")
        return
    
    print(f"👤 Test User ID: {test_user_id}")
    print(f"📖 Test Article: {beginner_article.title[:50]}...")
    print(f"   Phase: {beginner_article.primary_phase}")
    print(f"   Difficulty: {beginner_article.difficulty_level}")
    print()
    
    # Check if progress already exists
    existing_progress = db_session.query(UserArticleProgress).filter_by(
        user_id=test_user_id,
        article_id=beginner_article.id
    ).first()
    
    if existing_progress:
        print(f"⚠️  Progress already exists for this user/article combination")
        print(f"   Current phase progress: {existing_progress.phase_progress}%")
        print(f"   Total progress: {existing_progress.total_progress}%")
        print(f"   Current phase: {existing_progress.current_phase}")
        print(f"   Last updated: {existing_progress.updated_at}")
        
        # Update the existing progress
        existing_progress.phase_progress = 75.0
        existing_progress.total_progress = 25.0  # Assuming this is early in the journey
        existing_progress.updated_at = datetime.utcnow()
        
        db_session.commit()
        print(f"✅ Updated progress to 75% phase progress")
        
        progress = existing_progress
        
    else:
        # Create new progress tracking record with correct field names
        print("🆕 Creating new progress tracking record...")
        
        progress = UserArticleProgress(
            user_id=test_user_id,
            article_id=beginner_article.id,
            current_phase=beginner_article.primary_phase,
            phase_progress=75.0,
            total_progress=25.0
        )
        
        db_session.add(progress)
        db_session.commit()
        
        print("✅ Progress tracking record created successfully!")
    
    # Verify the progress was saved
    print(f"\n📊 Progress Details:")
    print(f"   User ID: {progress.user_id}")
    print(f"   Article ID: {progress.article_id}")
    print(f"   Current Phase: {progress.current_phase}")
    print(f"   Phase Progress: {progress.phase_progress}%")
    print(f"   Total Progress: {progress.total_progress}%")
    print(f"   Created At: {progress.created_at}")
    print(f"   Updated At: {progress.updated_at}")
    
    print("\n✅ Progress tracking works!")
    
    # Test basic queries
    print(f"\n🔍 Testing Basic Queries:")
    total_progress_records = db_session.query(UserArticleProgress).count()
    print(f"   Total progress records: {total_progress_records}")
    
    user_progress_records = db_session.query(UserArticleProgress).filter_by(user_id=test_user_id).count()
    print(f"   User progress records: {user_progress_records}")
    
    # Test relationship
    if progress.article:
        print(f"   Article relationship working: {progress.article.title[:30]}...")
    else:
        print(f"   ⚠️  Article relationship not working")

if __name__ == "__main__":
    main()
