#!/usr/bin/env python3
"""
Create test articles with different difficulty levels for testing gatekeeping
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.models import Article, db_session
import uuid
from datetime import datetime

def create_test_articles():
    """Create test articles with different phases and difficulty levels"""
    
    test_articles = [
        # BE Phase Articles
        {
            'title': 'Building a Wealth Mindset: The Foundation of Financial Success',
            'url': 'https://example.com/wealth-mindset-beginner',
            'content_preview': 'Learn the fundamental mindset shifts needed to build wealth...',
            'primary_phase': 'BE',
            'difficulty_level': 'Beginner',
            'domain': 'example.com'
        },
        {
            'title': 'Advanced Identity Transformation for High Net Worth Individuals',
            'url': 'https://example.com/identity-transformation-intermediate',
            'content_preview': 'Deep dive into identity transformation for those already on the wealth journey...',
            'primary_phase': 'BE',
            'difficulty_level': 'Intermediate',
            'domain': 'example.com'
        },
        {
            'title': 'Mastering the Psychology of Wealth: Expert Level Insights',
            'url': 'https://example.com/psychology-wealth-advanced',
            'content_preview': 'Expert-level psychological frameworks for wealth mastery...',
            'primary_phase': 'BE',
            'difficulty_level': 'Advanced',
            'domain': 'example.com'
        },
        
        # DO Phase Articles
        {
            'title': 'Basic Investment Strategies for Beginners',
            'url': 'https://example.com/investment-basics-beginner',
            'content_preview': 'Start your investment journey with these fundamental strategies...',
            'primary_phase': 'DO',
            'difficulty_level': 'Beginner',
            'domain': 'example.com'
        },
        {
            'title': 'Intermediate Portfolio Management Techniques',
            'url': 'https://example.com/portfolio-management-intermediate',
            'content_preview': 'Advanced portfolio management for intermediate investors...',
            'primary_phase': 'DO',
            'difficulty_level': 'Intermediate',
            'domain': 'example.com'
        },
        {
            'title': 'Advanced Trading Strategies and Risk Management',
            'url': 'https://example.com/advanced-trading-strategies',
            'content_preview': 'Expert-level trading strategies and sophisticated risk management...',
            'primary_phase': 'DO',
            'difficulty_level': 'Advanced',
            'domain': 'example.com'
        },
        
        # HAVE Phase Articles
        {
            'title': 'Understanding Wealth Metrics: A Beginner\'s Guide',
            'url': 'https://example.com/wealth-metrics-beginner',
            'content_preview': 'Learn the basic metrics to measure your wealth building progress...',
            'primary_phase': 'HAVE',
            'difficulty_level': 'Beginner',
            'domain': 'example.com'
        },
        {
            'title': 'Intermediate Wealth Preservation Strategies',
            'url': 'https://example.com/wealth-preservation-intermediate',
            'content_preview': 'Strategies for preserving and growing wealth at the intermediate level...',
            'primary_phase': 'HAVE',
            'difficulty_level': 'Intermediate',
            'domain': 'example.com'
        },
        {
            'title': 'Advanced Estate Planning and Legacy Building',
            'url': 'https://example.com/estate-planning-advanced',
            'content_preview': 'Expert-level estate planning and legacy building strategies...',
            'primary_phase': 'HAVE',
            'difficulty_level': 'Advanced',
            'domain': 'example.com'
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for article_data in test_articles:
        try:
            # Check if article already exists
            existing = db_session.query(Article).filter_by(url=article_data['url']).first()
            if existing:
                print(f"⚠️  Article already exists: {article_data['title']}")
                skipped_count += 1
                continue
            
            # Create new article
            article = Article(
                id=uuid.uuid4(),
                url=article_data['url'],
                title=article_data['title'],
                content=article_data['content_preview'] + " [Full content would be here...]",
                content_preview=article_data['content_preview'],
                primary_phase=article_data['primary_phase'],
                difficulty_level=article_data['difficulty_level'],
                domain=article_data['domain'],
                confidence_score=0.9,
                demographic_relevance=7,
                cultural_sensitivity=6,
                income_impact_potential=8,
                actionability_score=7,
                professional_development_value=8,
                is_active=True,
                is_featured=False
            )
            
            db_session.add(article)
            created_count += 1
            print(f"✅ Created: {article_data['title']} ({article_data['primary_phase']} - {article_data['difficulty_level']})")
            
        except Exception as e:
            print(f"❌ Error creating article {article_data['title']}: {e}")
    
    try:
        db_session.commit()
        print(f"\n📊 Summary:")
        print(f"   Created: {created_count} articles")
        print(f"   Skipped: {skipped_count} articles (already exist)")
        print(f"   Total articles in database: {db_session.query(Article).count()}")
        
    except Exception as e:
        print(f"❌ Error committing to database: {e}")
        db_session.rollback()

def main():
    """Main function"""
    print("🚀 Creating test articles for gatekeeping verification...")
    create_test_articles()
    print("✅ Test article creation completed!")

if __name__ == "__main__":
    main()
