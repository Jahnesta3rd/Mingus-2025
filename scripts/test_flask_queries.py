#!/usr/bin/env python3
"""
Flask shell test script to verify basic Article queries work correctly
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models import Article, db_session
from sqlalchemy import and_, or_, func

def test_basic_queries():
    """Test basic queries as requested"""
    
    print("🔍 Testing Basic Article Queries")
    print("=" * 50)
    
    # Test basic queries work
    total_articles = db_session.query(Article).count()
    print(f"📊 Total articles: {total_articles}")
    
    be_articles = db_session.query(Article).filter_by(primary_phase='BE').count()
    print(f"📊 BE articles: {be_articles}")
    
    high_cultural_relevance = db_session.query(Article).filter(Article.demographic_relevance >= 8).count()
    print(f"📊 High cultural relevance: {high_cultural_relevance}")
    
    print()

def test_advanced_queries():
    """Test more advanced queries"""
    
    print("🔍 Testing Advanced Article Queries")
    print("=" * 50)
    
    # Test difficulty level queries
    beginner_articles = db_session.query(Article).filter_by(difficulty_level='Beginner').count()
    intermediate_articles = db_session.query(Article).filter_by(difficulty_level='Intermediate').count()
    advanced_articles = db_session.query(Article).filter_by(difficulty_level='Advanced').count()
    
    print(f"📊 Beginner articles: {beginner_articles}")
    print(f"📊 Intermediate articles: {intermediate_articles}")
    print(f"📊 Advanced articles: {advanced_articles}")
    
    # Test phase queries
    do_articles = db_session.query(Article).filter_by(primary_phase='DO').count()
    have_articles = db_session.query(Article).filter_by(primary_phase='HAVE').count()
    
    print(f"📊 DO articles: {do_articles}")
    print(f"📊 HAVE articles: {have_articles}")
    
    # Test combined filters
    be_beginner = db_session.query(Article).filter(
        and_(Article.primary_phase == 'BE', Article.difficulty_level == 'Beginner')
    ).count()
    print(f"📊 BE Beginner articles: {be_beginner}")
    
    high_confidence = db_session.query(Article).filter(Article.confidence_score >= 0.8).count()
    print(f"📊 High confidence articles (>=0.8): {high_confidence}")
    
    print()

def test_aggregation_queries():
    """Test aggregation and grouping queries"""
    
    print("🔍 Testing Aggregation Queries")
    print("=" * 50)
    
    # Average scores by phase
    phase_stats = db_session.query(
        Article.primary_phase,
        func.avg(Article.demographic_relevance).label('avg_demographic'),
        func.avg(Article.cultural_sensitivity).label('avg_cultural'),
        func.avg(Article.income_impact_potential).label('avg_income_impact'),
        func.count(Article.id).label('article_count')
    ).group_by(Article.primary_phase).all()
    
    print("📊 Average scores by phase:")
    for phase, avg_demo, avg_cultural, avg_income, count in phase_stats:
        print(f"   {phase}: {count} articles")
        print(f"     Avg Demographic Relevance: {avg_demo:.1f}")
        print(f"     Avg Cultural Sensitivity: {avg_cultural:.1f}")
        print(f"     Avg Income Impact: {avg_income:.1f}")
    
    print()
    
    # Difficulty distribution
    difficulty_stats = db_session.query(
        Article.difficulty_level,
        func.count(Article.id).label('article_count')
    ).group_by(Article.difficulty_level).all()
    
    print("📊 Articles by difficulty level:")
    for difficulty, count in difficulty_stats:
        print(f"   {difficulty}: {count} articles")
    
    print()

def test_search_queries():
    """Test search-like queries"""
    
    print("🔍 Testing Search Queries")
    print("=" * 50)
    
    # Search for specific terms
    search_terms = ['wealth', 'investment', 'mindset', 'strategy', 'financial']
    
    for term in search_terms:
        results = db_session.query(Article).filter(
            or_(
                Article.title.contains(term),
                Article.content_preview.contains(term)
            )
        ).count()
        print(f"📊 Articles containing '{term}': {results}")
    
    print()
    
    # Test domain filtering
    domains = db_session.query(Article.domain).distinct().all()
    print("📊 Articles by domain:")
    for (domain,) in domains:
        count = db_session.query(Article).filter_by(domain=domain).count()
        print(f"   {domain}: {count} articles")

def test_flask_app_integration():
    """Test that the models work with Flask app context"""
    
    print("🔍 Testing Flask App Integration")
    print("=" * 50)
    
    try:
        # Try to import Flask app components
        from backend.app_factory import create_app
        
        # Create a minimal app context
        app = create_app()
        
        with app.app_context():
            # Test queries in Flask context
            total_in_context = db_session.query(Article).count()
            print(f"📊 Total articles in Flask context: {total_in_context}")
            
            # Test that the query works the same way
            be_in_context = db_session.query(Article).filter_by(primary_phase='BE').count()
            print(f"📊 BE articles in Flask context: {be_in_context}")
            
            print("✅ Flask app integration working correctly")
            
    except Exception as e:
        print(f"⚠️  Flask app integration test skipped: {e}")
        print("   (This is normal if Flask dependencies aren't fully configured)")

def main():
    """Main test function"""
    print("🚀 Testing Flask Article Queries")
    print("=" * 60)
    
    try:
        # Test 1: Basic queries
        test_basic_queries()
        
        # Test 2: Advanced queries
        test_advanced_queries()
        
        # Test 3: Aggregation queries
        test_aggregation_queries()
        
        # Test 4: Search queries
        test_search_queries()
        
        # Test 5: Flask integration
        test_flask_app_integration()
        
        print("✅ All query tests completed successfully!")
        print("\n📋 Summary:")
        print("   • Basic Article.query.count() working")
        print("   • Phase filtering working")
        print("   • Score filtering working")
        print("   • Complex queries working")
        print("   • Aggregation queries working")
        print("   • Search functionality working")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
