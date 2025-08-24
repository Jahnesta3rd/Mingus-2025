"""
End-to-End Tests for Article Library

Tests for complete user journeys and system workflows
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

class TestCompleteUserJourney:
    """Test complete user journey from registration to article completion"""
    
    def test_new_user_onboarding_journey(self, db_session, mock_email_extractor, mock_ai_classifier):
        """Test complete journey for a new user"""
        # Step 1: User registration
        user_data = {
            'email': 'newuser@example.com',
            'password_hash': 'hashed_password',
            'created_at': datetime.now()
        }
        
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == 'newuser@example.com'
        
        # Step 2: User completes assessment
        assessment_data = {
            'user_id': user.id,
            'be_score': 5,
            'do_score': 6,
            'have_score': 4,
            'assessment_date': datetime.now(),
            'overall_readiness_level': 'Intermediate'
        }
        
        assessment = UserAssessmentScores(**assessment_data)
        db_session.add(assessment)
        db_session.commit()
        
        assert assessment.be_score == 5
        assert assessment.do_score == 6
        assert assessment.have_score == 4
        
        # Step 3: System creates articles for user
        articles_data = [
            {
                'url': 'https://example.com/article1',
                'title': 'Beginner Career Guide',
                'content': 'Basic career advice for beginners...',
                'content_preview': 'Basic career advice for beginners...',
                'primary_phase': 'BE',
                'difficulty_level': 'Beginner',
                'demographic_relevance': 7,
                'cultural_sensitivity': 6,
                'domain': 'example.com'
            },
            {
                'url': 'https://example.com/article2',
                'title': 'Intermediate Leadership Skills',
                'content': 'Advanced leadership techniques...',
                'content_preview': 'Advanced leadership techniques...',
                'primary_phase': 'DO',
                'difficulty_level': 'Intermediate',
                'demographic_relevance': 8,
                'cultural_sensitivity': 7,
                'domain': 'example.com'
            }
        ]
        
        articles = []
        for article_data in articles_data:
            article = Article(**article_data)
            db_session.add(article)
            articles.append(article)
        db_session.commit()
        
        # Step 4: User searches for articles
        search_service = ArticleSearchService(db_session)
        search_results = search_service.search(
            query='career',
            filters={},
            user_id=user.id,
            page=1,
            per_page=10
        )
        
        assert search_results['pagination']['total'] >= 2
        assert len(search_results['articles']) >= 2
        
        # Step 5: User reads first article
        first_article = articles[0]
        
        # Start reading
        progress_data = {
            'user_id': user.id,
            'article_id': first_article.id,
            'progress_percentage': 25,
            'last_read_position': 500,
            'time_spent_seconds': 120,
            'last_activity': datetime.now()
        }
        
        progress = UserArticleProgress(**progress_data)
        db_session.add(progress)
        db_session.commit()
        
        # Complete reading
        progress.progress_percentage = 100
        progress.time_spent_seconds = 600
        db_session.commit()
        
        # Create read record
        read_data = {
            'user_id': user.id,
            'article_id': first_article.id,
            'read_date': datetime.now(),
            'read_duration_minutes': 10,
            'completion_percentage': 100
        }
        
        user_read = UserArticleRead(**read_data)
        db_session.add(user_read)
        db_session.commit()
        
        # Step 6: User bookmarks article
        bookmark_data = {
            'user_id': user.id,
            'article_id': first_article.id,
            'bookmark_date': datetime.now(),
            'notes': 'Great beginner article'
        }
        
        bookmark = UserArticleBookmark(**bookmark_data)
        db_session.add(bookmark)
        db_session.commit()
        
        # Step 7: User rates article
        rating_data = {
            'user_id': user.id,
            'article_id': first_article.id,
            'rating': 5,
            'rating_date': datetime.now(),
            'feedback': 'Excellent content for beginners'
        }
        
        rating = UserArticleRating(**rating_data)
        db_session.add(rating)
        db_session.commit()
        
        # Step 8: System generates recommendations
        recommendations = search_service.get_personalized_recommendations(user.id, limit=5)
        
        assert len(recommendations) > 0
        
        # Step 9: Verify user progress
        user_progress = db_session.query(UserArticleProgress).filter_by(user_id=user.id).first()
        user_reads = db_session.query(UserArticleRead).filter_by(user_id=user.id).all()
        user_bookmarks = db_session.query(UserArticleBookmark).filter_by(user_id=user.id).all()
        user_ratings = db_session.query(UserArticleRating).filter_by(user_id=user.id).all()
        
        assert user_progress.progress_percentage == 100
        assert len(user_reads) == 1
        assert len(user_bookmarks) == 1
        assert len(user_ratings) == 1
        assert user_ratings[0].rating == 5

    def test_advanced_user_journey(self, db_session, sample_users, sample_articles):
        """Test journey for an advanced user with existing history"""
        # Create advanced user with existing assessment
        user_data = sample_users[0]
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        
        # Create advanced assessment
        assessment_data = {
            'user_id': user.id,
            'be_score': 8,
            'do_score': 9,
            'have_score': 7,
            'assessment_date': datetime.now(),
            'overall_readiness_level': 'Advanced'
        }
        
        assessment = UserAssessmentScores(**assessment_data)
        db_session.add(assessment)
        db_session.commit()
        
        # Create articles with different difficulty levels
        articles_data = [
            {
                'url': 'https://example.com/advanced1',
                'title': 'Advanced Investment Strategies',
                'content': 'Complex investment strategies for advanced users...',
                'content_preview': 'Complex investment strategies...',
                'primary_phase': 'HAVE',
                'difficulty_level': 'Advanced',
                'demographic_relevance': 9,
                'cultural_sensitivity': 8,
                'domain': 'example.com'
            },
            {
                'url': 'https://example.com/advanced2',
                'title': 'Executive Leadership Mastery',
                'content': 'Master-level leadership techniques...',
                'content_preview': 'Master-level leadership techniques...',
                'primary_phase': 'DO',
                'difficulty_level': 'Advanced',
                'demographic_relevance': 9,
                'cultural_sensitivity': 8,
                'domain': 'example.com'
            }
        ]
        
        articles = []
        for article_data in articles_data:
            article = Article(**article_data)
            db_session.add(article)
            articles.append(article)
        db_session.commit()
        
        # User searches for advanced content
        search_service = ArticleSearchService(db_session)
        advanced_results = search_service.search(
            query='',
            filters={'difficulty': 'Advanced'},
            user_id=user.id,
            page=1,
            per_page=10
        )
        
        assert advanced_results['pagination']['total'] >= 2
        assert all(article['difficulty_level'] == 'Advanced' for article in advanced_results['articles'])
        
        # User reads multiple articles
        for i, article in enumerate(articles):
            # Read article
            read_data = {
                'user_id': user.id,
                'article_id': article.id,
                'read_date': datetime.now() - timedelta(days=i),
                'read_duration_minutes': 15 + i,
                'completion_percentage': 100
            }
            
            user_read = UserArticleRead(**read_data)
            db_session.add(user_read)
            
            # Rate article
            rating_data = {
                'user_id': user.id,
                'article_id': article.id,
                'rating': 4 + (i % 2),  # Alternate between 4 and 5
                'rating_date': datetime.now() - timedelta(days=i),
                'feedback': f'Great advanced content {i+1}'
            }
            
            rating = UserArticleRating(**rating_data)
            db_session.add(rating)
        
        db_session.commit()
        
        # System generates advanced recommendations
        recommendations = search_service.get_personalized_recommendations(user.id, limit=10)
        
        assert len(recommendations) > 0
        
        # Verify user's advanced status
        user_reads = db_session.query(UserArticleRead).filter_by(user_id=user.id).all()
        user_ratings = db_session.query(UserArticleRating).filter_by(user_id=user.id).all()
        
        assert len(user_reads) == 2
        assert len(user_ratings) == 2

class TestSystemWorkflows:
    """Test complete system workflows"""
    
    def test_email_processing_to_article_creation_workflow(self, db_session, mock_email_extractor, mock_domain_analyzer, mock_ai_classifier):
        """Test complete workflow from email processing to article creation"""
        # Step 1: Process email with articles
        email_data = {
            'subject': 'Weekly Financial Newsletter',
            'from': 'newsletter@nerdwallet.com',
            'body': '''
            This week's top articles:
            https://nerdwallet.com/article/careers/salary-negotiation
            https://blackenterprise.com/wealth-building-strategies
            https://investopedia.com/emergency-fund-guide
            '''
        }
        
        # Mock email processing
        mock_email_extractor.extract_urls_from_email_text.return_value = [
            'https://nerdwallet.com/article/careers/salary-negotiation',
            'https://blackenterprise.com/wealth-building-strategies',
            'https://investopedia.com/emergency-fund-guide'
        ]
        
        mock_domain_analyzer.analyze_domains.return_value = {
            'total_urls': 3,
            'unique_domains': 3,
            'domain_distribution': {
                'nerdwallet.com': 1,
                'blackenterprise.com': 1,
                'investopedia.com': 1
            }
        }
        
        # Mock AI classification for each article
        mock_ai_classifier.classify_article.side_effect = [
            {
                'primary_phase': 'DO',
                'difficulty_level': 'Intermediate',
                'demographic_relevance': 8,
                'cultural_sensitivity': 7,
                'key_topics': ['salary negotiation'],
                'confidence_score': 0.85
            },
            {
                'primary_phase': 'HAVE',
                'difficulty_level': 'Intermediate',
                'demographic_relevance': 8,
                'cultural_sensitivity': 8,
                'key_topics': ['wealth building'],
                'confidence_score': 0.88
            },
            {
                'primary_phase': 'HAVE',
                'difficulty_level': 'Beginner',
                'demographic_relevance': 7,
                'cultural_sensitivity': 6,
                'key_topics': ['emergency fund'],
                'confidence_score': 0.82
            }
        ]
        
        # Process email
        email_service = EmailProcessingService(db_session)
        result = email_service.process_email_to_articles(email_data)
        
        assert result['success'] == True
        assert result['total_urls_processed'] == 3
        
        # Step 2: Verify articles were created
        created_articles = db_session.query(Article).all()
        assert len(created_articles) >= 3
        
        # Step 3: Verify article classification
        do_articles = [a for a in created_articles if a.primary_phase == 'DO']
        have_articles = [a for a in created_articles if a.primary_phase == 'HAVE']
        
        assert len(do_articles) >= 1
        assert len(have_articles) >= 2
        
        # Step 4: Test search functionality with new articles
        search_service = ArticleSearchService(db_session)
        search_results = search_service.search(
            query='salary',
            filters={},
            user_id=None,
            page=1,
            per_page=10
        )
        
        assert search_results['pagination']['total'] > 0

    def test_recommendation_system_workflow(self, db_session, sample_users, sample_articles):
        """Test complete recommendation system workflow"""
        # Create user with assessment
        user_data = sample_users[0]
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        
        assessment_data = {
            'user_id': user.id,
            'be_score': 6,
            'do_score': 7,
            'have_score': 5,
            'assessment_date': datetime.now()
        }
        
        assessment = UserAssessmentScores(**assessment_data)
        db_session.add(assessment)
        db_session.commit()
        
        # Create diverse articles
        articles_data = [
            {
                'url': 'https://example.com/article1',
                'title': 'Career Development Basics',
                'content': 'Basic career development content...',
                'content_preview': 'Basic career development content...',
                'primary_phase': 'BE',
                'difficulty_level': 'Beginner',
                'demographic_relevance': 7,
                'cultural_sensitivity': 6,
                'domain': 'example.com'
            },
            {
                'url': 'https://example.com/article2',
                'title': 'Salary Negotiation Strategies',
                'content': 'Advanced salary negotiation...',
                'content_preview': 'Advanced salary negotiation...',
                'primary_phase': 'DO',
                'difficulty_level': 'Intermediate',
                'demographic_relevance': 8,
                'cultural_sensitivity': 7,
                'domain': 'example.com'
            },
            {
                'url': 'https://example.com/article3',
                'title': 'Investment Portfolio Management',
                'content': 'Investment strategies...',
                'content_preview': 'Investment strategies...',
                'primary_phase': 'HAVE',
                'difficulty_level': 'Advanced',
                'demographic_relevance': 8,
                'cultural_sensitivity': 7,
                'domain': 'example.com'
            }
        ]
        
        articles = []
        for article_data in articles_data:
            article = Article(**article_data)
            db_session.add(article)
            articles.append(article)
        db_session.commit()
        
        # User reads articles in sequence
        for i, article in enumerate(articles):
            read_data = {
                'user_id': user.id,
                'article_id': article.id,
                'read_date': datetime.now() - timedelta(days=i),
                'read_duration_minutes': 10 + i,
                'completion_percentage': 100
            }
            
            user_read = UserArticleRead(**read_data)
            db_session.add(user_read)
            
            # Rate articles
            rating_data = {
                'user_id': user.id,
                'article_id': article.id,
                'rating': 4 + (i % 2),
                'rating_date': datetime.now() - timedelta(days=i),
                'feedback': f'Good article {i+1}'
            }
            
            rating = UserArticleRating(**rating_data)
            db_session.add(rating)
        
        db_session.commit()
        
        # Generate recommendations
        search_service = ArticleSearchService(db_session)
        recommendations = search_service.get_personalized_recommendations(user.id, limit=5)
        
        assert len(recommendations) > 0
        
        # Verify recommendation quality
        recommendation_scores = [rec.recommendation_score for rec in recommendations]
        assert all(score > 0 for score in recommendation_scores)
        assert all(score <= 1 for score in recommendation_scores)

class TestPerformanceE2E:
    """Test end-to-end performance scenarios"""
    
    def test_large_dataset_performance(self, db_session, sample_users):
        """Test system performance with large dataset"""
        # Create multiple users
        users = []
        for i in range(10):
            user_data = {
                'email': f'user{i}@example.com',
                'password_hash': f'hashed_password_{i}',
                'created_at': datetime.now()
            }
            user = User(**user_data)
            db_session.add(user)
            users.append(user)
        
        db_session.commit()
        
        # Create large number of articles
        articles = []
        for i in range(100):
            article_data = {
                'url': f'https://example.com/article{i}',
                'title': f'Article {i} - Career Development',
                'content': f'Content for article {i}...',
                'content_preview': f'Content for article {i}...',
                'primary_phase': ['BE', 'DO', 'HAVE'][i % 3],
                'difficulty_level': ['Beginner', 'Intermediate', 'Advanced'][i % 3],
                'demographic_relevance': 5 + (i % 5),
                'cultural_sensitivity': 5 + (i % 5),
                'domain': 'example.com'
            }
            article = Article(**article_data)
            db_session.add(article)
            articles.append(article)
        
        db_session.commit()
        
        # Test search performance
        search_service = ArticleSearchService(db_session)
        
        # Test basic search
        start_time = datetime.now()
        search_results = search_service.search(
            query='career',
            filters={},
            user_id=None,
            page=1,
            per_page=20
        )
        end_time = datetime.now()
        
        search_duration = (end_time - start_time).total_seconds()
        
        assert search_duration < 2.0  # Should complete within 2 seconds
        assert search_results['pagination']['total'] > 0
        
        # Test filtered search
        start_time = datetime.now()
        filtered_results = search_service.search(
            query='',
            filters={'phase': 'DO', 'difficulty': 'Intermediate'},
            user_id=None,
            page=1,
            per_page=20
        )
        end_time = datetime.now()
        
        filtered_duration = (end_time - start_time).total_seconds()
        
        assert filtered_duration < 2.0  # Should complete within 2 seconds
        assert filtered_results['pagination']['total'] > 0

    def test_concurrent_user_simulation(self, db_session, sample_articles):
        """Test system behavior with concurrent users"""
        # Create multiple users
        users = []
        for i in range(5):
            user_data = {
                'email': f'concurrent_user{i}@example.com',
                'password_hash': f'hashed_password_{i}',
                'created_at': datetime.now()
            }
            user = User(**user_data)
            db_session.add(user)
            users.append(user)
        
        db_session.commit()
        
        # Create articles
        articles = []
        for article_data in sample_articles:
            article = Article(**article_data)
            db_session.add(article)
            articles.append(article)
        db_session.commit()
        
        # Simulate concurrent user activities
        search_service = ArticleSearchService(db_session)
        
        # Simulate multiple users searching simultaneously
        search_results = []
        for user in users:
            result = search_service.search(
                query='career',
                filters={},
                user_id=user.id,
                page=1,
                per_page=10
            )
            search_results.append(result)
        
        # Verify all searches completed successfully
        assert len(search_results) == 5
        for result in search_results:
            assert result['pagination']['total'] > 0
            assert len(result['articles']) > 0

class TestErrorHandlingE2E:
    """Test end-to-end error handling scenarios"""
    
    def test_database_connection_failure(self, db_session, mock_cache):
        """Test system behavior during database connection failure"""
        # Mock database failure
        mock_db_session = Mock()
        mock_db_session.query.side_effect = Exception("Database connection failed")
        
        # Test search service with failed database
        search_service = ArticleSearchService(mock_db_session)
        
        try:
            result = search_service.search(
                query='test',
                filters={},
                user_id=None,
                page=1,
                per_page=10
            )
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "Database connection failed" in str(e)
    
    def test_cache_failure_scenario(self, db_session, sample_articles):
        """Test system behavior when cache fails"""
        # Create articles
        articles = []
        for article_data in sample_articles:
            article = Article(**article_data)
            db_session.add(article)
            articles.append(article)
        db_session.commit()
        
        # Mock cache failure
        mock_cache = Mock()
        mock_cache.get.side_effect = Exception("Cache connection failed")
        mock_cache.set.side_effect = Exception("Cache connection failed")
        
        # Test search service with failed cache
        search_service = ArticleSearchService(db_session)
        
        # Should still work without cache
        result = search_service.search(
            query='career',
            filters={},
            user_id=None,
            page=1,
            per_page=10
        )
        
        assert result['pagination']['total'] > 0
        assert len(result['articles']) > 0

class TestDataIntegrityE2E:
    """Test end-to-end data integrity scenarios"""
    
    def test_user_data_isolation(self, db_session, sample_users, sample_articles):
        """Test that user data is properly isolated"""
        # Create two users
        user1_data = sample_users[0]
        user2_data = sample_users[1]
        
        user1 = User(**user1_data)
        user2 = User(**user2_data)
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()
        
        # Create articles
        articles = []
        for article_data in sample_articles:
            article = Article(**article_data)
            db_session.add(article)
            articles.append(article)
        db_session.commit()
        
        # User 1 reads and rates articles
        for i, article in enumerate(articles[:2]):
            read_data = {
                'user_id': user1.id,
                'article_id': article.id,
                'read_date': datetime.now(),
                'read_duration_minutes': 10,
                'completion_percentage': 100
            }
            
            user_read = UserArticleRead(**read_data)
            db_session.add(user_read)
            
            rating_data = {
                'user_id': user1.id,
                'article_id': article.id,
                'rating': 5,
                'rating_date': datetime.now(),
                'feedback': 'Great article'
            }
            
            rating = UserArticleRating(**rating_data)
            db_session.add(rating)
        
        db_session.commit()
        
        # User 2 reads different articles
        for i, article in enumerate(articles[2:4]):
            read_data = {
                'user_id': user2.id,
                'article_id': article.id,
                'read_date': datetime.now(),
                'read_duration_minutes': 15,
                'completion_percentage': 100
            }
            
            user_read = UserArticleRead(**read_data)
            db_session.add(user_read)
        
        db_session.commit()
        
        # Verify data isolation
        user1_reads = db_session.query(UserArticleRead).filter_by(user_id=user1.id).all()
        user2_reads = db_session.query(UserArticleRead).filter_by(user_id=user2.id).all()
        user1_ratings = db_session.query(UserArticleRating).filter_by(user_id=user1.id).all()
        user2_ratings = db_session.query(UserArticleRating).filter_by(user_id=user2.id).all()
        
        assert len(user1_reads) == 2
        assert len(user2_reads) == 2
        assert len(user1_ratings) == 2
        assert len(user2_ratings) == 0  # User 2 didn't rate any articles
        
        # Verify no cross-contamination
        assert all(read.user_id == user1.id for read in user1_reads)
        assert all(read.user_id == user2.id for read in user2_reads)
        assert all(rating.user_id == user1.id for rating in user1_ratings)

    def test_article_data_consistency(self, db_session, sample_articles):
        """Test article data consistency across operations"""
        # Create article
        article_data = sample_articles[0]
        article = Article(**article_data)
        db_session.add(article)
        db_session.commit()
        
        # Verify article data
        original_title = article.title
        original_content = article.content
        original_phase = article.primary_phase
        
        # Simulate article update
        article.title = "Updated Title"
        article.content = "Updated content..."
        db_session.commit()
        
        # Verify update
        updated_article = db_session.query(Article).filter_by(id=article.id).first()
        assert updated_article.title == "Updated Title"
        assert updated_article.content == "Updated content..."
        assert updated_article.primary_phase == original_phase  # Should not change
        
        # Verify article relationships
        assert updated_article.id == article.id
        assert updated_article.url == article.url
