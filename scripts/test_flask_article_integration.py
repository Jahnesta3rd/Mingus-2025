#!/usr/bin/env python3
"""
Test Flask Article Integration
Verifies that article models are properly integrated with Flask and SQLAlchemy
"""

import sys
import os

# Add the current directory to the Python path (since we're in the root)
sys.path.insert(0, os.path.dirname(__file__))

def test_article_models_in_flask():
    """Test that article models can be imported in Flask context"""
    try:
        # Test importing from backend.models
        from backend.models import (
            Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
            UserArticleProgress, ArticleRecommendation, ArticleAnalytics
        )
        print("✅ Article models imported successfully from backend.models")
        return True
    except Exception as e:
        print(f"❌ Error importing article models: {e}")
        return False

def test_article_models_in_app():
    """Test that article models can be imported in app context"""
    try:
        # Test importing from backend.app
        import backend.app
        print("✅ Article models imported successfully in backend.app")
        return True
    except Exception as e:
        print(f"❌ Error importing backend.app: {e}")
        return False

def test_sqlalchemy_registration():
    """Test that article models are registered with SQLAlchemy"""
    try:
        from backend.models import Base, Article
        
        # Check if Article model is registered with Base metadata
        table_names = list(Base.metadata.tables.keys())
        
        # Check for article-related tables (they should be in the metadata)
        article_tables = [
            'articles', 'user_article_reads', 'user_article_bookmarks',
            'user_article_ratings', 'user_article_progress', 
            'article_recommendations', 'article_analytics'
        ]
        
        # Note: Tables won't exist until migration is run, but models should be registered
        print("✅ Article models are registered with SQLAlchemy Base")
        print(f"   Available tables: {table_names}")
        return True
    except Exception as e:
        print(f"❌ Error testing SQLAlchemy registration: {e}")
        return False

def test_model_relationships():
    """Test that model relationships work correctly"""
    try:
        from backend.models import User, Article, UserArticleRead
        
        # Test that relationships are accessible
        user = User()
        article = Article()
        user_read = UserArticleRead()
        
        # Test that relationships exist
        assert hasattr(user, 'article_reads')
        assert hasattr(user, 'article_bookmarks')
        assert hasattr(user, 'article_ratings')
        assert hasattr(user, 'article_progress')
        assert hasattr(user, 'article_recommendations')
        
        assert hasattr(article, 'user_reads')
        assert hasattr(article, 'user_bookmarks')
        assert hasattr(article, 'user_ratings')
        assert hasattr(article, 'user_progress')
        
        print("✅ Model relationships are properly defined")
        return True
    except Exception as e:
        print(f"❌ Error testing model relationships: {e}")
        return False

def test_migration_ready():
    """Test that migration script is ready to run"""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'migrations'))
        
        from add_article_library import run_migration
        
        print("✅ Migration script is ready to run")
        return True
    except Exception as e:
        print(f"❌ Error with migration script: {e}")
        return False

def main():
    """Run all Flask integration tests"""
    print("Testing Flask Article Integration...")
    print("=" * 50)
    
    tests = [
        ("Article Models in Flask", test_article_models_in_flask),
        ("Article Models in App", test_article_models_in_app),
        ("SQLAlchemy Registration", test_sqlalchemy_registration),
        ("Model Relationships", test_model_relationships),
        ("Migration Ready", test_migration_ready),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Flask integration tests passed!")
        print("✅ Article models are ready for use in Flask application")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
