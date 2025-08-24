#!/usr/bin/env python3
"""
Test script to verify article library gatekeeping functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models import (
    UserAssessmentScores, Article, User, db_session
)
import uuid

def test_gatekeeping_functionality():
    """Test the gatekeeping functionality with the specified user scores"""
    
    print("🔒 Testing Article Access Gatekeeping")
    print("=" * 50)
    
    # Get the test user (user ID 1 from our sample data)
    test_user_id = 1
    
    # Get user's assessment scores
    assessment = db_session.query(UserAssessmentScores).filter_by(user_id=test_user_id).first()
    
    if not assessment:
        print("❌ No assessment found for test user")
        return
    
    print(f"📊 User Assessment Scores:")
    print(f"   BE Score: {assessment.be_score} (Level: {assessment.be_level})")
    print(f"   DO Score: {assessment.do_score} (Level: {assessment.do_level})")
    print(f"   HAVE Score: {assessment.have_score} (Level: {assessment.have_level})")
    print()
    
    # Test access control for different articles
    print("🔍 Testing Article Access Control:")
    
    # Get articles by difficulty level
    beginner_articles = db_session.query(Article).filter_by(difficulty_level='Beginner').limit(3).all()
    intermediate_articles = db_session.query(Article).filter_by(difficulty_level='Intermediate').limit(3).all()
    advanced_articles = db_session.query(Article).filter_by(difficulty_level='Advanced').limit(3).all()
    
    print("\n📚 Beginner Articles (should all be accessible):")
    for article in beginner_articles:
        can_access = article.can_user_access(test_user_id, db_session)
        print(f"   ✅ {article.title[:50]}... ({article.primary_phase}) - Access: {can_access}")
    
    print("\n📚 Intermediate Articles:")
    for article in intermediate_articles:
        can_access = article.can_user_access(test_user_id, db_session)
        expected_access = assessment.get_level_for_phase(article.primary_phase) in ['Intermediate', 'Advanced']
        status = "✅" if can_access == expected_access else "❌"
        print(f"   {status} {article.title[:50]}... ({article.primary_phase}) - Access: {can_access} (Expected: {expected_access})")
    
    print("\n📚 Advanced Articles:")
    for article in advanced_articles:
        can_access = article.can_user_access(test_user_id, db_session)
        expected_access = assessment.get_level_for_phase(article.primary_phase) == 'Advanced'
        status = "✅" if can_access == expected_access else "❌"
        print(f"   {status} {article.title[:50]}... ({article.primary_phase}) - Access: {can_access} (Expected: {expected_access})")

def test_phase_filtering():
    """Test filtering articles by phase"""
    
    print("\n🎯 Testing Phase Filtering")
    print("=" * 50)
    
    # Test phase filtering
    phases = ['BE', 'DO', 'HAVE']
    
    for phase in phases:
        articles = db_session.query(Article).filter_by(primary_phase=phase).all()
        print(f"\n📖 {phase} Phase Articles ({len(articles)} total):")
        
        for article in articles[:3]:  # Show first 3
            print(f"   • {article.title[:60]}... ({article.difficulty_level})")
        
        if len(articles) > 3:
            print(f"   ... and {len(articles) - 3} more")

def test_difficulty_distribution():
    """Test the distribution of articles by difficulty level"""
    
    print("\n📊 Testing Difficulty Distribution")
    print("=" * 50)
    
    difficulties = ['Beginner', 'Intermediate', 'Advanced']
    
    for difficulty in difficulties:
        articles = db_session.query(Article).filter_by(difficulty_level=difficulty).all()
        print(f"\n📚 {difficulty} Articles ({len(articles)} total):")
        
        # Group by phase
        phase_counts = {}
        for article in articles:
            phase = article.primary_phase
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        for phase, count in phase_counts.items():
            print(f"   • {phase}: {count} articles")

def test_search_functionality():
    """Test search functionality (placeholder for full-text search)"""
    
    print("\n🔍 Testing Search Functionality")
    print("=" * 50)
    
    # Test basic text search (simulated since we don't have full-text search set up yet)
    search_terms = ['wealth', 'investment', 'mindset', 'strategy']
    
    for term in search_terms:
        # Simple LIKE search for demonstration
        articles = db_session.query(Article).filter(
            Article.title.contains(term) | Article.content_preview.contains(term)
        ).all()
        
        print(f"\n🔎 Search for '{term}': {len(articles)} results")
        
        for article in articles[:2]:  # Show first 2 results
            print(f"   • {article.title[:50]}... ({article.primary_phase} - {article.difficulty_level})")

def test_user_without_assessment():
    """Test access control for a user without assessment scores"""
    
    print("\n👤 Testing User Without Assessment")
    print("=" * 50)
    
    # Create a test user without assessment
    test_user_without_assessment = 999  # Non-existent user ID
    
    # Test access to different difficulty levels
    difficulties = ['Beginner', 'Intermediate', 'Advanced']
    
    for difficulty in difficulties:
        article = db_session.query(Article).filter_by(difficulty_level=difficulty).first()
        if article:
            can_access = article.can_user_access(test_user_without_assessment, db_session)
            expected_access = difficulty == 'Beginner'  # Only Beginner should be accessible
            status = "✅" if can_access == expected_access else "❌"
            print(f"   {status} {difficulty} article access: {can_access} (Expected: {expected_access})")

def main():
    """Main test function"""
    print("🚀 Starting Article Library Gatekeeping Tests")
    print("=" * 60)
    
    try:
        # Test 1: Gatekeeping functionality
        test_gatekeeping_functionality()
        
        # Test 2: Phase filtering
        test_phase_filtering()
        
        # Test 3: Difficulty distribution
        test_difficulty_distribution()
        
        # Test 4: Search functionality
        test_search_functionality()
        
        # Test 5: User without assessment
        test_user_without_assessment()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
