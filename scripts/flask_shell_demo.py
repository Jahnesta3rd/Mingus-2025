#!/usr/bin/env python3
"""
Flask shell demo script showing the exact queries requested
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models import Article, db_session

def main():
    """Demo the exact queries requested"""
    
    print("🚀 Flask Shell Demo - Article Queries")
    print("=" * 50)
    
    # Test basic queries work (exactly as requested)
    print("from backend.models import Article")
    print("from your_app import db")
    print()
    
    print("# Test basic queries work")
    total_articles = db_session.query(Article).count()
    print(f"print(f\"Total articles: {total_articles}\")")
    print(f"# Output: Total articles: {total_articles}")
    print()
    
    be_articles = db_session.query(Article).filter_by(primary_phase='BE').count()
    print(f"print(f\"BE articles: {be_articles}\")")
    print(f"# Output: BE articles: {be_articles}")
    print()
    
    high_cultural_relevance = db_session.query(Article).filter(Article.demographic_relevance >= 8).count()
    print(f"print(f\"High cultural relevance: {high_cultural_relevance}\")")
    print(f"# Output: High cultural relevance: {high_cultural_relevance}")
    print()
    
    # Show some additional useful queries
    print("# Additional useful queries:")
    print()
    
    # Show sample articles
    sample_articles = db_session.query(Article).limit(3).all()
    print("print(\"Sample articles:\")")
    for i, article in enumerate(sample_articles, 1):
        print(f"# {i}. {article.title[:50]}... ({article.primary_phase} - {article.difficulty_level})")
    
    print()
    
    # Show phase distribution
    phases = ['BE', 'DO', 'HAVE']
    print("print(\"Phase distribution:\")")
    for phase in phases:
        count = db_session.query(Article).filter_by(primary_phase=phase).count()
        print(f"# {phase}: {count} articles")
    
    print()
    
    # Show difficulty distribution
    difficulties = ['Beginner', 'Intermediate', 'Advanced']
    print("print(\"Difficulty distribution:\")")
    for difficulty in difficulties:
        count = db_session.query(Article).filter_by(difficulty_level=difficulty).count()
        print(f"# {difficulty}: {count} articles")
    
    print()
    print("✅ All queries working correctly!")

if __name__ == "__main__":
    main()
