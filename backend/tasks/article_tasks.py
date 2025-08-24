"""
Article Processing Celery Tasks for MINGUS Application
Background tasks for article library processing
"""

from celery import Celery, current_app
from celery.utils.log import get_task_logger
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import time

from config.article_library import ArticleLibraryConfig

logger = get_task_logger(__name__)


def setup_article_tasks(app):
    """Setup article processing Celery tasks"""
    config = ArticleLibraryConfig()
    
    # Configure Celery
    celery_app = Celery('mingus_articles')
    celery_app.config_from_object({
        'broker_url': config.CELERY_BROKER_URL,
        'result_backend': config.CELERY_RESULT_BACKEND,
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'UTC',
        'enable_utc': True,
        'task_routes': config.CELERY_TASK_ROUTES,
        'task_default_queue': 'articles',
        'task_create_missing_queues': True,
    })
    
    return celery_app


@current_app.task(bind=True, name='articles.process_email_articles')
def process_email_articles(self, batch_size: int = 50) -> Dict[str, Any]:
    """Process articles from email inbox"""
    config = ArticleLibraryConfig()
    
    try:
        logger.info(f"Processing {batch_size} email articles")
        
        # Simulate processing
        processed_count = 0
        failed_count = 0
        
        for i in range(batch_size):
            try:
                time.sleep(config.ARTICLE_SCRAPING_DELAY)
                processed_count += 1
            except Exception as e:
                failed_count += 1
        
        result = {
            'processed_count': processed_count,
            'failed_count': failed_count,
            'status': 'completed'
        }
        
        logger.info(f"Email processing completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in email processing: {str(e)}")
        self.retry(countdown=300, max_retries=3)
        raise


@current_app.task(bind=True, name='articles.classify_article')
def classify_article(self, article_id: int) -> Dict[str, Any]:
    """Classify article using AI"""
    config = ArticleLibraryConfig()
    
    try:
        logger.info(f"Classifying article {article_id}")
        
        # Simulate classification
        classification_result = {
            'be_score': 75,
            'do_score': 80,
            'have_score': 70,
            'phase': 'intermediate',
            'topics': ['investment', 'retirement'],
            'cultural_relevance_score': 7.5,
            'quality_score': 0.8
        }
        
        result = {
            'article_id': article_id,
            'classification_result': classification_result,
            'status': 'completed'
        }
        
        logger.info(f"Classification completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in classification: {str(e)}")
        self.retry(countdown=60, max_retries=3)
        raise


@current_app.task(bind=True, name='articles.update_analytics')
def update_article_analytics(self, article_id: int, user_id: int, action: str) -> Dict[str, Any]:
    """Update article analytics"""
    try:
        logger.info(f"Updating analytics for article {article_id}, action: {action}")
        
        result = {
            'article_id': article_id,
            'user_id': user_id,
            'action': action,
            'status': 'completed'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating analytics: {str(e)}")
        self.retry(countdown=30, max_retries=3)
        raise


@current_app.task(bind=True, name='articles.cleanup_old_articles')
def cleanup_old_articles(self, days_old: int = 365) -> Dict[str, Any]:
    """Clean up old articles and analytics data"""
    try:
        logger.info(f"Cleaning up articles older than {days_old} days")
        
        result = {
            'deleted_count': 0,
            'cutoff_date': datetime.utcnow().isoformat(),
            'status': 'completed'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")
        self.retry(countdown=300, max_retries=3)
        raise
