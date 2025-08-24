"""
Integration Tests for Article Library

Tests for component interactions, workflows, and end-to-end functionality
in the Mingus article library system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from backend.models.articles import (
    Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
    UserArticleProgress, UserAssessmentScores, ArticleRecommendation, ArticleAnalytics
)
from backend.models.user import User, UserProfile
from backend.services.article_search import ArticleSearchService
from backend.services.email_processing import EmailProcessingService
from backend.services.article_classification import ArticleClassificationService

class TestEmailProcessingWorkflow:
    """Test complete email processing workflow"""
    
    def test_email_to_article_pipeline(self, db_session, mock_email_extractor, mock_domain_analyzer, mock_ai_classifier):
        """Test complete pipeline from email extraction to article creation"""
        # Mock email data
        email_data = {
            'subject': 'Weekly Financial Tips',
            'from': 'newsletter@nerdwallet.com',
            'body': '''
            Check out these great articles:
            https://nerdwallet.com/article/careers/salary-negotiation
            https://blackenterprise.com/wealth-building-strategies
            '''
        }
        
        # Mock extracted URLs
        mock_email_extractor.extract_urls_from_email_text.return_value = [
            'https://nerdwallet.com/article/careers/salary-negotiation',
            'https://blackenterprise.com/wealth-building-strategies'
        ]
        
        # Mock domain analysis
        mock_domain_analyzer.analyze_domains.return_value = {
            'total_urls': 2,
            'unique_domains': 2,
            'domain_distribution': {
                'nerdwallet.com': 1,
                'blackenterprise.com': 1
            }
        }
        
        # Mock AI classification
        mock_ai_classifier.classify_article.return_value = {
            'primary_phase': 'DO',
            'difficulty_level': 'Intermediate',
            'demographic_relevance': 8,
            'cultural_sensitivity': 7,
            'key_topics': ['salary negotiation', 'career advancement'],
            'learning_objectives': ['Learn negotiation strategies'],
            'confidence_score': 0.85
        }
        
        # Test the workflow
        service = EmailProcessingService(db_session)
        result = service.process_email_to_articles(email_data)
        
        assert result['success'] == True
        assert len(result['articles_created']) == 2
        assert result['total_urls_processed'] == 2

    def test_domain_approval_workflow(self, db_session, mock_domain_analyzer):
        """Test domain approval and filtering workflow"""
        # Mock domain data
        domain_data = [
            {'url': 'https://nerdwallet.com/article/1', 'domain': 'nerdwallet.com'},
            {'url': 'https://facebook.com/share/post', 'domain': 'facebook.com'},
            {'url': 'https://blackenterprise.com/article/1', 'domain': 'blackenterprise.com'}
        ]
        
        # Mock domain analysis
        mock_domain_analyzer.analyze_domains.return_value = {
            'total_urls': 3,
            'unique_domains': 3,
            'domain_distribution': {
                'nerdwallet.com': 1,
                'facebook.com': 1,
                'blackenterprise.com': 1
            }
        }
        
        # Test domain filtering
        service = EmailProcessingService(db_session)
        approved_domains = service.filter_approved_domains(domain_data)
        
        # Should only include financial/educational domains
        assert len(approved_domains) == 2
        assert any('nerdwallet.com' in domain['domain'] for domain in approved_domains)
        assert any('blackenterprise.com' in domain['domain'] for domain in approved_domains)
        assert not any('facebook.com' in domain['domain'] for domain in approved_domains)

class TestArticleClassificationPipeline:
    """Test article classification and processing pipeline"""
    
    def test_article_scraping_and_classification(self, db_session, mock_article_scraper, mock_ai_classifier):
        """Test complete article scraping and classification workflow"""
        # Mock article URL
        article_url = 'https://nerdwallet.com/article/careers/salary-negotiation'
        
        # Mock scraped content
        mock_article_scraper.scrape_article.return_value = {
            'title': 'How to Negotiate Your Salary Like a Pro',
            'content': 'Salary negotiation is a crucial skill for career advancement...',
            'author': 'John Smith',
            'publish_date': '2024-01-15',
            'word_count': 1500,
            'meta_description': 'Learn effective salary negotiation strategies...'
        }
        
        # Mock AI classification
        mock_ai_classifier.classify_article.return_value = {
            'primary_phase': 'DO',
            'difficulty_level': 'Intermediate',
            'demographic_relevance': 8,
            'cultural_sensitivity': 7,
            'key_topics': ['salary negotiation', 'career advancement'],
            'learning_objectives': ['Learn negotiation strategies', 'Understand market rates'],
            'prerequisites': ['Basic communication skills', 'Professional experience'],
            'confidence_score': 0.88
        }
        
        # Test the classification pipeline
        service = ArticleClassificationService(db_session)
        result = service.process_article(article_url)
        
        assert result['success'] == True
        assert result['article']['title'] == 'How to Negotiate Your Salary Like a Pro'
        assert result['article']['primary_phase'] == 'DO'
        assert result['article']['difficulty_level'] == 'Intermediate'
        assert result['classification_confidence'] == 0.88

    def test_be_do_have_classification_logic(self, db_session, mock_ai_classifier):
        """Test Be-Do-Have framework classification logic"""
        # Test different article types
        test_cases = [
            {
                'content': 'Building confidence and developing a growth mindset...',
                'expected_phase': 'BE',
                'expected_difficulty': 'Beginner'
            },
            {
                'content': 'Step-by-step guide to salary negotiation...',
                'expected_phase': 'DO',
                'expected_difficulty': 'Intermediate'
            },
            {
                'content': 'Advanced investment strategies and portfolio management...',
                'expected_phase': 'HAVE',
                'expected_difficulty': 'Advanced'
            }
        ]
        
        service = ArticleClassificationService(db_session)
        
        for test_case in test_cases:
            mock_ai_classifier.classify_article.return_value = {
                'primary_phase': test_case['expected_phase'],
                'difficulty_level': test_case['expected_difficulty'],
                'demographic_relevance': 7,
                'cultural_sensitivity': 6,
                'confidence_score': 0.85
            }
            
            result = service.classify_article_content(test_case['content'])
            
            assert result['primary_phase'] == test_case['expected_phase']
            assert result['difficulty_level'] == test_case['expected_difficulty']

class TestUserJourneyIntegration:
    """Test complete user journeys through the article library"""
    
    def test_user_onboarding_to_article_access(self, db_session, sample_users):
        """Test complete user journey from onboarding to article access"""
        # Create user
        user_data = sample_users[0]
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        
        # Create assessment scores
        assessment_data = {
            'user_id': user.id,
            'be_score': 6,
            'do_score': 7,
            'have_score': 4,
            'assessment_date': datetime.now(),
            'overall_readiness_level': 'Intermediate'
        }
        
        assessment = UserAssessmentScores(**assessment_data)
        db_session.add(assessment)
        db_session.commit()
        
        # Create articles with different difficulty levels
        articles_data = [
            {
                'url': 'https://example.com/beginner-article',
                'title': 'Beginner Career Guide',
                'content': 'Basic career advice...',
                'content_preview': 'Basic career advice...',
                'primary_phase': 'BE',
                'difficulty_level': 'Beginner',
                'domain': 'example.com'
            },
            {
                'url': 'https://example.com/intermediate-article',
                'title': 'Intermediate Leadership Skills',
                'content': 'Advanced leadership techniques...',
                'content_preview': 'Advanced leadership techniques...',
                'primary_phase': 'DO',
                'difficulty_level': 'Intermediate',
                'domain': 'example.com'
            }
        ]
        
        articles = []
        for article_data in articles_data:
            article = Article(**article_data)
            db_session.add(article)
            articles.append(article)
        db_session.commit()
        
        # Test article access based on assessment
        search_service = ArticleSearchService(db_session)
        accessible_articles = search_service.get_accessible_articles(user.id)
        
        # User should be able to access both Beginner and Intermediate articles
        assert len(accessible_articles) >= 2
        assert any(article.difficulty_level == 'Beginner' for article in accessible_articles)
        assert any(article.difficulty_level == 'Intermediate' for article in accessible_articles)

    def test_article_reading_and_progress_tracking(self, db_session, sample_users, sample_articles):
        """Test complete article reading and progress tracking workflow"""
        user = sample_users[0]
        article = sample_articles[0]
        
        # Create user and article in database
        db_user = User(**user)
        db_article = Article(**article)
        db_session.add(db_user)
        db_session.add(db_article)
        db_session.commit()
        
        # Simulate user starting to read article
        progress_data = {
            'user_id': db_user.id,
            'article_id': db_article.id,
            'progress_percentage': 25,
            'last_read_position': 500,
            'time_spent_seconds': 120,
            'last_activity': datetime.now()
        }
        
        progress = UserArticleProgress(**progress_data)
        db_session.add(progress)
        db_session.commit()
        
        # Simulate user bookmarking article
        bookmark_data = {
            'user_id': db_user.id,
            'article_id': db_article.id,
            'bookmark_date': datetime.now(),
            'notes': 'Great article on career development'
        }
        
        bookmark = UserArticleBookmark(**bookmark_data)
        db_session.add(bookmark)
        db_session.commit()
        
        # Simulate user completing article
        progress.progress_percentage = 100
        progress.time_spent_seconds = 600
        db_session.commit()
        
        # Create read record
        read_data = {
            'user_id': db_user.id,
            'article_id': db_article.id,
            'read_date': datetime.now(),
            'read_duration_minutes': 10,
            'completion_percentage': 100
        }
        
        user_read = UserArticleRead(**read_data)
        db_session.add(user_read)
        db_session.commit()
        
        # Test that all records are created correctly
        assert progress.progress_percentage == 100
        assert progress.time_spent_seconds == 600
        assert bookmark.notes == 'Great article on career development'
        assert user_read.completion_percentage == 100

    def test_recommendation_system_integration(self, db_session, sample_users, sample_articles):
        """Test recommendation system integration with user behavior"""
        user = sample_users[0]
        articles = sample_articles[:3]  # Use first 3 articles
        
        # Create user and articles in database
        db_user = User(**user)
        db_articles = []
        for article_data in articles:
            article = Article(**article_data)
            db_session.add(article)
            db_articles.append(article)
        db_session.commit()
        
        # Simulate user reading articles
        for i, article in enumerate(db_articles):
            read_data = {
                'user_id': db_user.id,
                'article_id': article.id,
                'read_date': datetime.now() - timedelta(days=i),
                'read_duration_minutes': 10 + i,
                'completion_percentage': 100
            }
            
            user_read = UserArticleRead(**read_data)
            db_session.add(user_read)
        
        db_session.commit()
        
        # Test recommendation generation
        search_service = ArticleSearchService(db_session)
        recommendations = search_service.get_personalized_recommendations(db_user.id, limit=5)
        
        # Should return recommendations based on user's reading history
        assert len(recommendations) > 0
        assert all(hasattr(rec, 'recommendation_score') for rec in recommendations)

class TestSearchAndDiscoveryIntegration:
    """Test search and discovery functionality integration"""
    
    def test_search_with_filters_and_personalization(self, db_session, sample_users, sample_articles):
        """Test search functionality with filters and personalization"""
        user = sample_users[0]
        
        # Create user and articles in database
        db_user = User(**user)
        db_articles = []
        for article_data in sample_articles:
            article = Article(**article_data)
            db_session.add(article)
            db_articles.append(article)
        db_session.commit()
        
        # Create assessment for personalization
        assessment_data = {
            'user_id': db_user.id,
            'be_score': 6,
            'do_score': 7,
            'have_score': 4,
            'assessment_date': datetime.now()
        }
        
        assessment = UserAssessmentScores(**assessment_data)
        db_session.add(assessment)
        db_session.commit()
        
        # Test search with filters
        search_service = ArticleSearchService(db_session)
        
        # Search for DO phase articles
        do_results = search_service.search(
            query='career',
            filters={'phase': 'DO'},
            user_id=db_user.id,
            page=1,
            per_page=10
        )
        
        assert do_results['pagination']['total'] > 0
        assert all(article['primary_phase'] == 'DO' for article in do_results['articles'])
        
        # Search with difficulty filter
        intermediate_results = search_service.search(
            query='',
            filters={'difficulty': 'Intermediate'},
            user_id=db_user.id,
            page=1,
            per_page=10
        )
        
        assert intermediate_results['pagination']['total'] > 0
        assert all(article['difficulty_level'] == 'Intermediate' for article in intermediate_results['articles'])

    def test_article_analytics_integration(self, db_session, sample_users, sample_articles):
        """Test article analytics integration with user interactions"""
        user = sample_users[0]
        article = sample_articles[0]
        
        # Create user and article in database
        db_user = User(**user)
        db_article = Article(**article)
        db_session.add(db_user)
        db_session.add(db_article)
        db_session.commit()
        
        # Simulate multiple user interactions
        interactions = [
            # User reads article
            {
                'type': 'read',
                'data': {
                    'user_id': db_user.id,
                    'article_id': db_article.id,
                    'read_date': datetime.now(),
                    'read_duration_minutes': 15,
                    'completion_percentage': 100
                }
            },
            # User bookmarks article
            {
                'type': 'bookmark',
                'data': {
                    'user_id': db_user.id,
                    'article_id': db_article.id,
                    'bookmark_date': datetime.now(),
                    'notes': 'Excellent article'
                }
            },
            # User rates article
            {
                'type': 'rating',
                'data': {
                    'user_id': db_user.id,
                    'article_id': db_article.id,
                    'rating': 5,
                    'rating_date': datetime.now(),
                    'feedback': 'Very helpful content'
                }
            }
        ]
        
        # Create interaction records
        for interaction in interactions:
            if interaction['type'] == 'read':
                record = UserArticleRead(**interaction['data'])
            elif interaction['type'] == 'bookmark':
                record = UserArticleBookmark(**interaction['data'])
            elif interaction['type'] == 'rating':
                record = UserArticleRating(**interaction['data'])
            
            db_session.add(record)
        
        db_session.commit()
        
        # Test analytics aggregation
        analytics_data = {
            'article_id': db_article.id,
            'view_count': 1,
            'read_count': 1,
            'bookmark_count': 1,
            'rating_count': 1,
            'avg_rating': 5.0,
            'completion_rate': 1.0,
            'avg_read_time_minutes': 15.0,
            'last_updated': datetime.now()
        }
        
        analytics = ArticleAnalytics(**analytics_data)
        db_session.add(analytics)
        db_session.commit()
        
        # Verify analytics reflect user interactions
        assert analytics.read_count == 1
        assert analytics.bookmark_count == 1
        assert analytics.rating_count == 1
        assert analytics.avg_rating == 5.0
        assert analytics.completion_rate == 1.0

class TestCacheAndPerformanceIntegration:
    """Test caching and performance integration"""
    
    def test_search_cache_integration(self, db_session, mock_cache, sample_articles):
        """Test search caching integration"""
        # Create articles in database
        db_articles = []
        for article_data in sample_articles:
            article = Article(**article_data)
            db_session.add(article)
            db_articles.append(article)
        db_session.commit()
        
        # Mock cache behavior
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.set.return_value = True
        
        search_service = ArticleSearchService(db_session)
        
        # First search (cache miss)
        result1 = search_service.search(
            query='career',
            filters={},
            user_id=None,
            page=1,
            per_page=10
        )
        
        # Mock cache hit for second search
        mock_cache.get.return_value = result1
        
        # Second search (cache hit)
        result2 = search_service.search(
            query='career',
            filters={},
            user_id=None,
            page=1,
            per_page=10
        )
        
        # Verify cache was used
        assert mock_cache.get.called
        assert mock_cache.set.called
        assert result1 == result2

    def test_recommendation_cache_integration(self, db_session, mock_cache, sample_users, sample_articles):
        """Test recommendation caching integration"""
        user = sample_users[0]
        
        # Create user and articles in database
        db_user = User(**user)
        db_articles = []
        for article_data in sample_articles:
            article = Article(**article_data)
            db_session.add(article)
            db_articles.append(article)
        db_session.commit()
        
        # Mock cache behavior
        mock_cache.get.return_value = None  # Cache miss
        mock_cache.set.return_value = True
        
        search_service = ArticleSearchService(db_session)
        
        # First recommendation request (cache miss)
        recommendations1 = search_service.get_personalized_recommendations(db_user.id, limit=5)
        
        # Mock cache hit for second request
        mock_cache.get.return_value = recommendations1
        
        # Second recommendation request (cache hit)
        recommendations2 = search_service.get_personalized_recommendations(db_user.id, limit=5)
        
        # Verify cache was used
        assert mock_cache.get.called
        assert mock_cache.set.called
        assert recommendations1 == recommendations2
