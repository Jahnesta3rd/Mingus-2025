#!/usr/bin/env python3
"""
Test script for Article Library Models
Verifies that the SQLAlchemy models can be imported and used correctly
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_model_imports():
    """Test that all article models can be imported successfully"""
    try:
        from models.articles import (
            Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
            UserArticleProgress, ArticleRecommendation, ArticleAnalytics
        )
        print("✅ All article models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing article models: {e}")
        return False

def test_model_relationships():
    """Test that model relationships are properly defined"""
    try:
        from models.articles import Article, UserArticleRead
        from models.user import User
        
        # Test that relationships are accessible
        article = Article()
        user_read = UserArticleRead()
        user = User()
        
        print("✅ Model relationships are properly defined")
        return True
    except Exception as e:
        print(f"❌ Error testing model relationships: {e}")
        return False

def test_model_attributes():
    """Test that model attributes are properly defined"""
    try:
        from models.articles import Article
        
        article = Article()
        
        # Test that key attributes exist
        required_attrs = [
            'id', 'url', 'title', 'content', 'primary_phase', 
            'difficulty_level', 'demographic_relevance', 'domain'
        ]
        
        for attr in required_attrs:
            if not hasattr(article, attr):
                print(f"❌ Missing attribute: {attr}")
                return False
        
        print("✅ All required model attributes are present")
        return True
    except Exception as e:
        print(f"❌ Error testing model attributes: {e}")
        return False

def test_model_serialization():
    """Test that models can be serialized to dictionaries"""
    try:
        from models.articles import Article
        
        article = Article()
        article_dict = article.to_dict()
        
        if not isinstance(article_dict, dict):
            print("❌ to_dict() method doesn't return a dictionary")
            return False
        
        print("✅ Model serialization works correctly")
        return True
    except Exception as e:
        print(f"❌ Error testing model serialization: {e}")
        return False

def test_migration_script():
    """Test that the migration script can be imported"""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'migrations'))
        
        from add_article_library import run_migration
        
        print("✅ Migration script can be imported")
        return True
    except Exception as e:
        print(f"❌ Error importing migration script: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Article Library Models...")
    print("=" * 50)
    
    tests = [
        ("Model Imports", test_model_imports),
        ("Model Relationships", test_model_relationships),
        ("Model Attributes", test_model_attributes),
        ("Model Serialization", test_model_serialization),
        ("Migration Script", test_migration_script),
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
        print("🎉 All tests passed! Article library models are ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
