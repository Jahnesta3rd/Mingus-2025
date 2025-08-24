"""
MINGUS Article Library - Celery Configuration
=============================================
Background task processing for article library operations
"""

from celery import Celery
from flask import Flask
import os
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def make_celery(app: Flask) -> Celery:
    """
    Create and configure Celery instance with Flask app context
    
    Args:
        app: Flask application instance
        
    Returns:
        Configured Celery instance
    """
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        broker=app.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    
    # Configure task routes for different queues
    celery.conf.update(
        task_routes={
            'backend.tasks.article_processing.*': {'queue': 'article_processing'},
            'backend.tasks.email_processing.*': {'queue': 'email_processing'},
            'backend.tasks.ai_classification.*': {'queue': 'ai_classification'},
            'backend.tasks.analytics.*': {'queue': 'analytics'},
            'backend.tasks.cleanup.*': {'queue': 'cleanup'},
            'backend.tasks.recommendations.*': {'queue': 'recommendations'},
        },
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='UTC',
        enable_utc=True,
        task_always_eager=app.config.get('TESTING', False),
        task_eager_propagates=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_max_tasks_per_child=1000,
        broker_connection_retry_on_startup=True,
        result_expires=3600,  # 1 hour
        task_soft_time_limit=300,  # 5 minutes
        task_time_limit=600,  # 10 minutes
    )
    
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
        
        def on_failure(self, exc, task_id, args, kwargs, einfo):
            """Handle task failures"""
            logger.error(f"Task {task_id} failed: {exc}")
            super().on_failure(exc, task_id, args, kwargs, einfo)
        
        def on_retry(self, exc, task_id, args, kwargs, einfo):
            """Handle task retries"""
            logger.warning(f"Task {task_id} retrying: {exc}")
            super().on_retry(exc, task_id, args, kwargs, einfo)
    
    celery.Task = ContextTask
    return celery

# Create Flask app and Celery instance
try:
    from backend.app_factory import create_app
    flask_app = create_app()
    celery = make_celery(flask_app)
except ImportError:
    # Fallback for testing or when app factory is not available
    logger.warning("Could not import create_app, using basic Celery setup")
    celery = Celery('mingus_article_library')
    celery.conf.update(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/0',
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='UTC',
        enable_utc=True,
    )

# =====================================================
# ARTICLE PROCESSING TASKS
# =====================================================

@celery.task(bind=True, queue='article_processing')
def process_new_articles(self, article_urls: List[str]) -> List[Dict[str, Any]]:
    """
    Background task to scrape and classify new articles
    
    Args:
        article_urls: List of article URLs to process
        
    Returns:
        List of processing results for each URL
    """
    from backend.services.article_scraper import ArticleScraperService
    from backend.services.ai_classifier import AIClassifierService
    from backend.models.articles import Article
    from backend.extensions import db
    
    scraper = ArticleScraperService()
    classifier = AIClassifierService()
    
    results = []
    total_urls = len(article_urls)
    
    for i, url in enumerate(article_urls):
        try:
            # Update progress
            progress = (i / total_urls) * 100
            self.update_state(
                state='PROGRESS',
                meta={'current': i + 1, 'total': total_urls, 'progress': progress}
            )
            
            # Check if article already exists
            existing_article = Article.query.filter_by(url=url).first()
            if existing_article:
                results.append({
                    'url': url, 
                    'status': 'already_exists',
                    'article_id': existing_article.id
                })
                continue
            
            # Scrape article content
            article_data = scraper.scrape_article(url)
            if article_data:
                # Classify with AI
                classification = classifier.classify_article(article_data)
                article_data.update(classification)
                
                # Save to database
                article = Article(**article_data)
                db.session.add(article)
                db.session.commit()
                
                results.append({
                    'url': url, 
                    'status': 'success',
                    'article_id': article.id
                })
            else:
                results.append({'url': url, 'status': 'scraping_failed'})
                
        except Exception as e:
            logger.error(f"Error processing article {url}: {str(e)}")
            results.append({
                'url': url, 
                'status': 'error', 
                'error': str(e)
            })
    
    return results

@celery.task(bind=True, queue='article_processing')
def reprocess_article(self, article_id: int) -> Dict[str, Any]:
    """
    Background task to reprocess an existing article
    
    Args:
        article_id: ID of the article to reprocess
        
    Returns:
        Processing result
    """
    from backend.services.article_scraper import ArticleScraperService
    from backend.services.ai_classifier import AIClassifierService
    from backend.models.articles import Article
    from backend.extensions import db
    
    try:
        article = Article.query.get(article_id)
        if not article:
            return {'status': 'error', 'error': 'Article not found'}
        
        scraper = ArticleScraperService()
        classifier = AIClassifierService()
        
        # Re-scrape article content
        article_data = scraper.scrape_article(article.url)
        if article_data:
            # Re-classify with AI
            classification = classifier.classify_article(article_data)
            
            # Update article
            for key, value in classification.items():
                if hasattr(article, key):
                    setattr(article, key, value)
            
            db.session.commit()
            
            return {
                'status': 'success',
                'article_id': article.id,
                'updated_fields': list(classification.keys())
            }
        else:
            return {'status': 'error', 'error': 'Failed to scrape article'}
            
    except Exception as e:
        logger.error(f"Error reprocessing article {article_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# =====================================================
# EMAIL PROCESSING TASKS
# =====================================================

@celery.task(bind=True, queue='email_processing')
def process_email_articles(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Background task to process articles from email
    
    Args:
        email_data: Email data containing article links
        
    Returns:
        Processing result
    """
    from backend.services.email_extractor import EmailExtractorService
    from backend.services.article_scraper import ArticleScraperService
    
    try:
        extractor = EmailExtractorService()
        scraper = ArticleScraperService()
        
        # Extract article URLs from email
        article_urls = extractor.extract_article_urls(email_data)
        
        if not article_urls:
            return {'status': 'no_articles_found'}
        
        # Process each article
        results = []
        for url in article_urls:
            try:
                article_data = scraper.scrape_article(url)
                if article_data:
                    results.append({
                        'url': url,
                        'status': 'success',
                        'title': article_data.get('title', ''),
                        'domain': article_data.get('domain', '')
                    })
                else:
                    results.append({'url': url, 'status': 'scraping_failed'})
            except Exception as e:
                results.append({'url': url, 'status': 'error', 'error': str(e)})
        
        return {
            'status': 'success',
            'total_urls': len(article_urls),
            'processed': len([r for r in results if r['status'] == 'success']),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error processing email articles: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# =====================================================
# AI CLASSIFICATION TASKS
# =====================================================

@celery.task(bind=True, queue='ai_classification')
def classify_article_batch(self, article_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Background task to classify multiple articles with AI
    
    Args:
        article_ids: List of article IDs to classify
        
    Returns:
        Classification results
    """
    from backend.services.ai_classifier import AIClassifierService
    from backend.models.articles import Article
    from backend.extensions import db
    
    classifier = AIClassifierService()
    results = []
    
    for i, article_id in enumerate(article_ids):
        try:
            article = Article.query.get(article_id)
            if not article:
                results.append({
                    'article_id': article_id,
                    'status': 'not_found'
                })
                continue
            
            # Classify article
            classification = classifier.classify_article({
                'title': article.title,
                'content': article.content,
                'url': article.url
            })
            
            # Update article with classification
            for key, value in classification.items():
                if hasattr(article, key):
                    setattr(article, key, value)
            
            db.session.commit()
            
            results.append({
                'article_id': article_id,
                'status': 'success',
                'classification': classification
            })
            
        except Exception as e:
            logger.error(f"Error classifying article {article_id}: {str(e)}")
            results.append({
                'article_id': article_id,
                'status': 'error',
                'error': str(e)
            })
    
    return results

# =====================================================
# RECOMMENDATION TASKS
# =====================================================

@celery.task(bind=True, queue='recommendations')
def update_user_recommendations(self, user_id: int, limit: int = 20) -> Dict[str, Any]:
    """
    Background task to update user recommendations
    
    Args:
        user_id: User ID to update recommendations for
        limit: Maximum number of recommendations to generate
        
    Returns:
        Recommendation update result
    """
    from backend.services.article_recommendations import ArticleRecommendationEngine
    from backend.extensions import cache
    
    try:
        engine = ArticleRecommendationEngine()
        recommendations = engine.get_personalized_recommendations(user_id, limit=limit)
        
        # Cache recommendations
        cache_key = f'user_recommendations_{user_id}'
        cache.set(cache_key, recommendations, timeout=3600)  # 1 hour
        
        return {
            'status': 'success',
            'user_id': user_id,
            'recommendations_count': len(recommendations),
            'cache_key': cache_key
        }
        
    except Exception as e:
        logger.error(f"Error updating recommendations for user {user_id}: {str(e)}")
        return {
            'status': 'error',
            'user_id': user_id,
            'error': str(e)
        }

@celery.task(bind=True, queue='recommendations')
def update_all_user_recommendations(self) -> Dict[str, Any]:
    """
    Background task to update recommendations for all users
    
    Returns:
        Bulk update result
    """
    from backend.models.users import User
    from backend.extensions import db
    
    try:
        users = User.query.all()
        results = []
        
        for user in users:
            try:
                # Call the single user recommendation task
                result = update_user_recommendations.delay(user.id)
                results.append({
                    'user_id': user.id,
                    'task_id': result.id
                })
            except Exception as e:
                results.append({
                    'user_id': user.id,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'status': 'success',
            'total_users': len(users),
            'tasks_created': len([r for r in results if 'task_id' in r]),
            'errors': len([r for r in results if 'error' in r]),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error updating all user recommendations: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# =====================================================
# ANALYTICS TASKS
# =====================================================

@celery.task(bind=True, queue='analytics')
def update_article_analytics(self, article_id: int) -> Dict[str, Any]:
    """
    Background task to update article analytics
    
    Args:
        article_id: Article ID to update analytics for
        
    Returns:
        Analytics update result
    """
    from backend.models.articles import Article
    from backend.services.article_analytics import ArticleAnalyticsService
    from backend.extensions import db
    
    try:
        article = Article.query.get(article_id)
        if not article:
            return {'status': 'error', 'error': 'Article not found'}
        
        analytics_service = ArticleAnalyticsService()
        analytics = analytics_service.calculate_article_analytics(article)
        
        # Update article with analytics
        for key, value in analytics.items():
            if hasattr(article, key):
                setattr(article, key, value)
        
        db.session.commit()
        
        return {
            'status': 'success',
            'article_id': article_id,
            'analytics': analytics
        }
        
    except Exception as e:
        logger.error(f"Error updating analytics for article {article_id}: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True, queue='analytics')
def generate_daily_analytics_report(self) -> Dict[str, Any]:
    """
    Background task to generate daily analytics report
    
    Returns:
        Daily report data
    """
    from backend.services.article_analytics import ArticleAnalyticsService
    from datetime import datetime, timedelta
    
    try:
        analytics_service = ArticleAnalyticsService()
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        report = analytics_service.generate_daily_report(yesterday)
        
        return {
            'status': 'success',
            'date': yesterday.strftime('%Y-%m-%d'),
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Error generating daily analytics report: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# =====================================================
# CLEANUP TASKS
# =====================================================

@celery.task(bind=True, queue='cleanup')
def cleanup_old_articles(self, days_old: int = 90) -> Dict[str, Any]:
    """
    Background task to cleanup old articles
    
    Args:
        days_old: Number of days after which articles are considered old
        
    Returns:
        Cleanup result
    """
    from backend.models.articles import Article
    from backend.extensions import db
    from datetime import datetime, timedelta
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find old articles
        old_articles = Article.query.filter(
            Article.created_at < cutoff_date,
            Article.is_deleted == False
        ).all()
        
        deleted_count = 0
        for article in old_articles:
            try:
                article.is_deleted = True
                article.deleted_at = datetime.utcnow()
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error marking article {article.id} as deleted: {str(e)}")
        
        db.session.commit()
        
        return {
            'status': 'success',
            'cutoff_date': cutoff_date.strftime('%Y-%m-%d'),
            'articles_found': len(old_articles),
            'articles_deleted': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old articles: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@celery.task(bind=True, queue='cleanup')
def cleanup_expired_cache(self) -> Dict[str, Any]:
    """
    Background task to cleanup expired cache entries
    
    Returns:
        Cache cleanup result
    """
    from backend.extensions import cache
    
    try:
        # This is a simplified version - in production you might want to
        # implement more sophisticated cache cleanup logic
        cleaned_count = 0
        
        # For Redis, we can use SCAN to find and clean expired keys
        # This is a placeholder implementation
        try:
            redis_client = cache.cache._client
            if hasattr(redis_client, 'scan_iter'):
                for key in redis_client.scan_iter(match='mingus_articles:*'):
                    if redis_client.ttl(key) == -1:  # No expiration set
                        redis_client.expire(key, 3600)  # Set 1 hour expiration
                        cleaned_count += 1
        except Exception as e:
            logger.warning(f"Could not cleanup cache: {str(e)}")
        
        return {
            'status': 'success',
            'cache_entries_processed': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired cache: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# =====================================================
# TASK UTILITIES
# =====================================================

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a Celery task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status information
    """
    task_result = celery.AsyncResult(task_id)
    
    if task_result.state == 'PENDING':
        response = {
            'state': task_result.state,
            'status': 'Task is pending...'
        }
    elif task_result.state != 'FAILURE':
        response = {
            'state': task_result.state,
            'result': task_result.result
        }
    else:
        response = {
            'state': task_result.state,
            'error': str(task_result.info)
        }
    
    return response

def cancel_task(task_id: str) -> Dict[str, Any]:
    """
    Cancel a running Celery task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Cancellation result
    """
    try:
        celery.control.revoke(task_id, terminate=True)
        return {
            'status': 'success',
            'message': f'Task {task_id} cancelled successfully'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

# Export the celery instance
__all__ = ['celery', 'make_celery', 'get_task_status', 'cancel_task']
