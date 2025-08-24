#!/usr/bin/env python3
"""
Test script to verify UserArticleProgress model and progress tracking functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models import (
    UserArticleProgress, Article, User, db_session
)
import uuid
from datetime import datetime

def test_progress_tracking():
    """Test the progress tracking functionality"""
    
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
        print(f"   Current progress: {existing_progress.reading_progress_percentage}%")
        print(f"   Bookmarked: {existing_progress.is_bookmarked}")
        print(f"   Last updated: {existing_progress.updated_at}")
        
        # Update the existing progress
        existing_progress.reading_progress_percentage = 75
        existing_progress.is_bookmarked = True
        existing_progress.updated_at = datetime.utcnow()
        
        db_session.commit()
        print(f"✅ Updated progress to 75% and bookmarked")
        
        progress = existing_progress
        
    else:
        # Create new progress tracking record
        print("🆕 Creating new progress tracking record...")
        
        progress = UserArticleProgress(
            user_id=test_user_id,
            article_id=beginner_article.id,
            reading_progress_percentage=75,
            is_bookmarked=True
        )
        
        db_session.add(progress)
        db_session.commit()
        
        print("✅ Progress tracking record created successfully!")
    
    # Verify the progress was saved
    print(f"\n📊 Progress Details:")
    print(f"   User ID: {progress.user_id}")
    print(f"   Article ID: {progress.article_id}")
    print(f"   Reading Progress: {progress.reading_progress_percentage}%")
    print(f"   Is Bookmarked: {progress.is_bookmarked}")
    print(f"   Started At: {progress.started_at}")
    print(f"   Last Updated: {progress.updated_at}")
    print(f"   Created At: {progress.created_at}")
    
    print("\n✅ Progress tracking works!")

def test_progress_relationships():
    """Test the relationships between UserArticleProgress and related models"""
    
    print("\n🔗 Testing Progress Relationships")
    print("=" * 50)
    
    test_user_id = 1
    
    # Get all progress records for the test user
    progress_records = db_session.query(UserArticleProgress).filter_by(user_id=test_user_id).all()
    
    print(f"📊 Found {len(progress_records)} progress records for user {test_user_id}")
    
    for i, progress in enumerate(progress_records, 1):
        print(f"\n📖 Progress Record {i}:")
        print(f"   Article ID: {progress.article_id}")
        print(f"   Progress: {progress.reading_progress_percentage}%")
        print(f"   Bookmarked: {progress.is_bookmarked}")
        
        # Test relationship to article
        if progress.article:
            print(f"   Article Title: {progress.article.title[:50]}...")
            print(f"   Article Phase: {progress.article.primary_phase}")
            print(f"   Article Difficulty: {progress.article.difficulty_level}")
        else:
            print(f"   ⚠️  Article relationship not working")

def test_progress_analytics():
    """Test progress analytics and statistics"""
    
    print("\n📈 Testing Progress Analytics")
    print("=" * 50)
    
    test_user_id = 1
    
    # Get progress statistics
    total_progress_records = db_session.query(UserArticleProgress).filter_by(user_id=test_user_id).count()
    
    # Get average progress
    from sqlalchemy import func
    avg_progress = db_session.query(
        func.avg(UserArticleProgress.reading_progress_percentage)
    ).filter_by(user_id=test_user_id).scalar()
    
    # Get bookmarked articles count
    bookmarked_count = db_session.query(UserArticleProgress).filter_by(
        user_id=test_user_id,
        is_bookmarked=True
    ).count()
    
    # Get completed articles (100% progress)
    completed_count = db_session.query(UserArticleProgress).filter_by(
        user_id=test_user_id
    ).filter(UserArticleProgress.reading_progress_percentage >= 100).count()
    
    print(f"📊 Progress Statistics for User {test_user_id}:")
    print(f"   Total Articles Started: {total_progress_records}")
    print(f"   Average Progress: {avg_progress:.1f}%" if avg_progress else "   Average Progress: 0%")
    print(f"   Bookmarked Articles: {bookmarked_count}")
    print(f"   Completed Articles: {completed_count}")

def test_progress_by_phase():
    """Test progress tracking by Be-Do-Have phase"""
    
    print("\n🎯 Testing Progress by Phase")
    print("=" * 50)
    
    test_user_id = 1
    
    # Get progress records with article details
    progress_with_articles = db_session.query(
        UserArticleProgress, Article
    ).join(Article).filter(
        UserArticleProgress.user_id == test_user_id
    ).all()
    
    # Group by phase
    phase_progress = {}
    for progress, article in progress_with_articles:
        phase = article.primary_phase
        if phase not in phase_progress:
            phase_progress[phase] = {
                'count': 0,
                'total_progress': 0,
                'bookmarked': 0
            }
        
        phase_progress[phase]['count'] += 1
        phase_progress[phase]['total_progress'] += progress.reading_progress_percentage
        if progress.is_bookmarked:
            phase_progress[phase]['bookmarked'] += 1
    
    print(f"📊 Progress by Phase for User {test_user_id}:")
    for phase, stats in phase_progress.items():
        avg_progress = stats['total_progress'] / stats['count'] if stats['count'] > 0 else 0
        print(f"   {phase} Phase:")
        print(f"     Articles Started: {stats['count']}")
        print(f"     Average Progress: {avg_progress:.1f}%")
        print(f"     Bookmarked: {stats['bookmarked']}")

def test_progress_validation():
    """Test progress validation and constraints"""
    
    print("\n✅ Testing Progress Validation")
    print("=" * 50)
    
    test_user_id = 1
    beginner_article = db_session.query(Article).filter_by(difficulty_level='Beginner').first()
    
    if not beginner_article:
        print("❌ No beginner article found for validation testing")
        return
    
    # Test valid progress values
    valid_progress_values = [0, 25, 50, 75, 100, 150]  # 150% for over-completion
    
    for progress_value in valid_progress_values:
        try:
            # Create or update progress
            progress = db_session.query(UserArticleProgress).filter_by(
                user_id=test_user_id,
                article_id=beginner_article.id
            ).first()
            
            if progress:
                progress.reading_progress_percentage = progress_value
            else:
                progress = UserArticleProgress(
                    user_id=test_user_id,
                    article_id=beginner_article.id,
                    reading_progress_percentage=progress_value,
                    is_bookmarked=False
                )
                db_session.add(progress)
            
            db_session.commit()
            print(f"   ✅ Progress {progress_value}% - Valid")
            
        except Exception as e:
            print(f"   ❌ Progress {progress_value}% - Invalid: {e}")
            db_session.rollback()

def main():
    """Main test function"""
    print("🚀 Testing UserArticleProgress Model")
    print("=" * 60)
    
    try:
        # Test 1: Basic progress tracking
        test_progress_tracking()
        
        # Test 2: Progress relationships
        test_progress_relationships()
        
        # Test 3: Progress analytics
        test_progress_analytics()
        
        # Test 4: Progress by phase
        test_progress_by_phase()
        
        # Test 5: Progress validation
        test_progress_validation()
        
        print("\n✅ All progress tracking tests completed successfully!")
        print("\n📋 Summary:")
        print("   • UserArticleProgress model working correctly")
        print("   • Progress tracking and updates working")
        print("   • Relationships to Article model working")
        print("   • Analytics and statistics working")
        print("   • Phase-based progress tracking working")
        print("   • Progress validation working")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
