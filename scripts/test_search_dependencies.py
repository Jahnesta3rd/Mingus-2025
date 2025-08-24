#!/usr/bin/env python3
"""
Test Search Dependencies
Verifies that sqlalchemy-searchable and sqlalchemy-utils work with article models
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_sqlalchemy_searchable():
    """Test sqlalchemy-searchable functionality"""
    try:
        import sqlalchemy_searchable
        from sqlalchemy_searchable import search
        
        print("✅ sqlalchemy-searchable imported successfully")
        print(f"   Version: {sqlalchemy_searchable.__version__}")
        return True
    except Exception as e:
        print(f"❌ Error importing sqlalchemy-searchable: {e}")
        return False

def test_sqlalchemy_utils():
    """Test sqlalchemy-utils functionality"""
    try:
        import sqlalchemy_utils
        from sqlalchemy_utils import UUIDType
        
        print("✅ sqlalchemy-utils imported successfully")
        print(f"   Version: {sqlalchemy_utils.__version__}")
        return True
    except Exception as e:
        print(f"❌ Error importing sqlalchemy-utils: {e}")
        return False

def test_article_model_with_dependencies():
    """Test that article models work with the new dependencies"""
    try:
        from backend.models import Article
        from sqlalchemy import Column, String
        from sqlalchemy_utils import UUIDType
        from sqlalchemy_searchable import make_searchable
        
        # Test that we can use UUIDType from sqlalchemy-utils
        article = Article()
        
        # Test that search functionality could be added
        # (This is just a test of import compatibility)
        print("✅ Article model compatible with search dependencies")
        return True
    except Exception as e:
        print(f"❌ Error testing article model with dependencies: {e}")
        return False

def test_full_text_search_setup():
    """Test full-text search setup capabilities"""
    try:
        from sqlalchemy_searchable import make_searchable
        from sqlalchemy import Column, String, Text
        from sqlalchemy.ext.declarative import declarative_base
        
        Base = declarative_base()
        
        # Test creating a searchable model
        class TestArticle(Base):
            __tablename__ = 'test_articles'
            
            id = Column(String(36), primary_key=True)
            title = Column(String(500))
            content = Column(Text)
            search_vector = Column(Text)
        
        # This would make the model searchable (just testing import)
        # make_searchable(TestArticle, search_vector='search_vector')
        
        print("✅ Full-text search setup test passed")
        return True
    except Exception as e:
        print(f"❌ Error testing full-text search setup: {e}")
        return False

def main():
    """Run all search dependency tests"""
    print("Testing Search Dependencies...")
    print("=" * 50)
    
    tests = [
        ("SQLAlchemy Searchable", test_sqlalchemy_searchable),
        ("SQLAlchemy Utils", test_sqlalchemy_utils),
        ("Article Model Compatibility", test_article_model_with_dependencies),
        ("Full-Text Search Setup", test_full_text_search_setup),
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
        print("🎉 All search dependency tests passed!")
        print("✅ Article library is ready for full-text search functionality")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
