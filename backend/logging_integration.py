# backend/logging_integration.py
"""
MINGUS Article Library - Logging Integration
==========================================
Integration of structured logging with Flask application and article library components
"""

import time
from functools import wraps
from typing import Callable, Any, Dict, Optional

from flask import Flask, request, g, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy

from .logging_config import (
    setup_logging, get_logger, log_request_start, log_request_end,
    log_error, log_performance_metric, log_user_action, log_article_event,
    log_ai_classification, log_search_query, log_recommendation_generation,
    log_cache_operation, log_database_operation, log_celery_task,
    log_external_api_call
)

def integrate_logging_with_flask(app: Flask):
    """Integrate structured logging with Flask application"""
    
    # Setup logging configuration
    setup_logging(app)
    
    # Add request logging middleware
    @app.before_request
    def before_request():
        """Log request start and add request ID"""
        log_request_start()
        
        # Add request ID to Flask g object
        g.request_id = request.headers.get('X-Request-ID', f"req_{int(time.time() * 1000)}")
        
        # Add user ID if authenticated
        if hasattr(g, 'user') and g.user:
            g.user_id = g.user.id
    
    @app.after_request
    def after_request(response):
        """Log request end"""
        return log_request_end(response)
    
    # Add error logging
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Log unhandled exceptions"""
        log_error(e, {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'user_id': getattr(g, 'user_id', None)
        })
        
        # Return JSON error response
        return jsonify({
            'error': 'Internal server error',
            'message': str(e) if app.debug else 'An unexpected error occurred'
        }), 500
    
    # Add specific error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Log 404 errors"""
        log_error(error, {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'error_type': 'not_found'
        })
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Log 400 errors"""
        log_error(error, {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'error_type': 'bad_request'
        })
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Log 401 errors"""
        log_error(error, {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'error_type': 'unauthorized'
        })
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Log 403 errors"""
        log_error(error, {
            'endpoint': request.endpoint,
            'method': request.method,
            'path': request.path,
            'error_type': 'forbidden'
        })
        return jsonify({'error': 'Forbidden'}), 403

def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            processing_time = time.time() - start_time
            
            # Log performance metric
            log_performance_metric(
                metric_name=f"{func.__module__}.{func.__name__}",
                value=processing_time * 1000,  # Convert to milliseconds
                unit='ms',
                context={
                    'function': func.__name__,
                    'module': func.__module__
                }
            )
            
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            log_error(e, {
                'function': func.__name__,
                'module': func.__module__,
                'processing_time_ms': processing_time * 1000
            })
            raise
    
    return wrapper

def log_user_activity(action: str):
    """Decorator to log user activities"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Extract user_id from request context
                user_id = getattr(g, 'user_id', None)
                if user_id:
                    log_user_action(action, user_id, {
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'path': request.path
                    })
                
                return result
            except Exception as e:
                log_error(e, {
                    'action': action,
                    'user_id': getattr(g, 'user_id', None),
                    'endpoint': request.endpoint
                })
                raise
        
        return wrapper
    return decorator

def log_article_activity(event_type: str):
    """Decorator to log article-related activities"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Extract article_id from request or result
                article_id = None
                if hasattr(request, 'view_args') and 'article_id' in request.view_args:
                    article_id = request.view_args['article_id']
                elif isinstance(result, dict) and 'article_id' in result:
                    article_id = result['article_id']
                
                if article_id:
                    log_article_event(event_type, article_id, {
                        'user_id': getattr(g, 'user_id', None),
                        'endpoint': request.endpoint,
                        'method': request.method
                    })
                
                return result
            except Exception as e:
                log_error(e, {
                    'event_type': event_type,
                    'endpoint': request.endpoint
                })
                raise
        
        return wrapper
    return decorator

class DatabaseLogger:
    """Database operation logger"""
    
    def __init__(self, db: SQLAlchemy):
        self.db = db
        self.logger = get_logger('database')
    
    def log_query(self, query: str, params: Dict[str, Any] = None, execution_time: float = None):
        """Log database query"""
        log_data = {
            'query': query,
            'params': params or {}
        }
        
        if execution_time:
            log_data['execution_time_ms'] = execution_time * 1000
        
        self.logger.debug("Database query", **log_data)
    
    def log_operation(self, operation: str, table: str, row_count: int = None, execution_time: float = None):
        """Log database operation"""
        log_database_operation(operation, table, execution_time or 0, row_count)

class CacheLogger:
    """Cache operation logger"""
    
    def __init__(self):
        self.logger = get_logger('cache')
    
    def log_get(self, key: str, hit: bool, execution_time: float = None):
        """Log cache get operation"""
        log_cache_operation('get', key, hit, execution_time or 0)
    
    def log_set(self, key: str, execution_time: float = None):
        """Log cache set operation"""
        log_cache_operation('set', key, True, execution_time or 0)
    
    def log_delete(self, key: str, execution_time: float = None):
        """Log cache delete operation"""
        log_cache_operation('delete', key, True, execution_time or 0)

class AILogger:
    """AI service logger"""
    
    def __init__(self):
        self.logger = get_logger('ai')
    
    def log_classification(self, article_id: int, classification_result: Dict[str, Any], processing_time: float):
        """Log AI classification"""
        log_ai_classification(article_id, classification_result, processing_time)
    
    def log_api_call(self, service: str, endpoint: str, method: str, status_code: int, processing_time: float):
        """Log AI API call"""
        log_external_api_call(service, endpoint, method, status_code, processing_time)

class SearchLogger:
    """Search service logger"""
    
    def __init__(self):
        self.logger = get_logger('search')
    
    def log_query(self, query: str, filters: Dict[str, Any], result_count: int, processing_time: float):
        """Log search query"""
        log_search_query(query, filters, result_count, processing_time)
    
    def log_indexing(self, article_id: int, processing_time: float):
        """Log search indexing"""
        self.logger.info(
            "Search indexing completed",
            article_id=article_id,
            processing_time_ms=processing_time * 1000
        )

class RecommendationLogger:
    """Recommendation service logger"""
    
    def __init__(self):
        self.logger = get_logger('recommendations')
    
    def log_generation(self, user_id: int, recommendation_count: int, processing_time: float):
        """Log recommendation generation"""
        log_recommendation_generation(user_id, recommendation_count, processing_time)
    
    def log_user_preferences(self, user_id: int, preferences: Dict[str, Any]):
        """Log user preference updates"""
        self.logger.info(
            "User preferences updated",
            user_id=user_id,
            preferences=preferences
        )

class CeleryLogger:
    """Celery task logger"""
    
    def __init__(self):
        self.logger = get_logger('celery')
    
    def log_task_start(self, task_name: str, task_id: str):
        """Log task start"""
        log_celery_task(task_name, task_id, 'started')
    
    def log_task_success(self, task_name: str, task_id: str, processing_time: float):
        """Log task success"""
        log_celery_task(task_name, task_id, 'completed', processing_time)
    
    def log_task_failure(self, task_name: str, task_id: str, error: Exception, processing_time: float = None):
        """Log task failure"""
        log_error(error, {
            'task_name': task_name,
            'task_id': task_id,
            'processing_time_ms': processing_time * 1000 if processing_time else None
        })

# Convenience functions for common logging scenarios
def log_article_view(article_id: int, user_id: Optional[int] = None):
    """Log article view"""
    log_article_event('view', article_id, {
        'user_id': user_id,
        'timestamp': time.time()
    })

def log_article_share(article_id: int, platform: str, user_id: Optional[int] = None):
    """Log article share"""
    log_article_event('share', article_id, {
        'user_id': user_id,
        'platform': platform,
        'timestamp': time.time()
    })

def log_article_bookmark(article_id: int, user_id: int, action: str = 'add'):
    """Log article bookmark"""
    log_article_event('bookmark', article_id, {
        'user_id': user_id,
        'action': action,
        'timestamp': time.time()
    })

def log_assessment_completion(user_id: int, scores: Dict[str, int]):
    """Log assessment completion"""
    log_user_action('assessment_completed', user_id, {
        'scores': scores,
        'timestamp': time.time()
    })

def log_search_performed(query: str, filters: Dict[str, Any], result_count: int, processing_time: float):
    """Log search operation"""
    log_search_query(query, filters, result_count, processing_time)

def log_recommendation_requested(user_id: int, recommendation_count: int, processing_time: float):
    """Log recommendation request"""
    log_recommendation_generation(user_id, recommendation_count, processing_time)

# Example usage in Flask routes
def example_route_logging():
    """Example of how to use logging in Flask routes"""
    
    @app.route('/api/articles/<int:article_id>', methods=['GET'])
    @performance_monitor
    @log_article_activity('view')
    def get_article(article_id):
        """Get article with logging"""
        try:
            # Your route logic here
            article = Article.query.get_or_404(article_id)
            
            # Log the view
            log_article_view(article_id, getattr(g, 'user_id', None))
            
            return jsonify(article.to_dict())
        except Exception as e:
            log_error(e, {
                'article_id': article_id,
                'endpoint': 'get_article'
            })
            raise
    
    @app.route('/api/articles/search', methods=['POST'])
    @performance_monitor
    def search_articles():
        """Search articles with logging"""
        try:
            start_time = time.time()
            
            # Your search logic here
            query = request.json.get('query', '')
            filters = request.json.get('filters', {})
            
            # Perform search
            results = perform_search(query, filters)
            
            processing_time = time.time() - start_time
            
            # Log the search
            log_search_performed(query, filters, len(results), processing_time)
            
            return jsonify({'articles': results})
        except Exception as e:
            log_error(e, {
                'endpoint': 'search_articles',
                'query': request.json.get('query', '')
            })
            raise

# Initialize loggers for different components
def initialize_component_loggers():
    """Initialize loggers for different components"""
    return {
        'database': DatabaseLogger(current_app.extensions['sqlalchemy'].db),
        'cache': CacheLogger(),
        'ai': AILogger(),
        'search': SearchLogger(),
        'recommendations': RecommendationLogger(),
        'celery': CeleryLogger()
    }

if __name__ == '__main__':
    # Test logging integration
    print("Logging integration module loaded successfully")
    print("Available loggers:")
    print("- DatabaseLogger")
    print("- CacheLogger") 
    print("- AILogger")
    print("- SearchLogger")
    print("- RecommendationLogger")
    print("- CeleryLogger")
    print("\nAvailable decorators:")
    print("- @performance_monitor")
    print("- @log_user_activity(action)")
    print("- @log_article_activity(event_type)")
