"""
Article Library API Routes for Mingus Application
Comprehensive Flask API endpoints for article library operations
"""

from flask import Blueprint, request, jsonify, session, current_app
from flask_caching import Cache
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import uuid
import logging
from typing import Dict, List, Optional
from functools import wraps

from backend.models.articles import (
    Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
    UserArticleProgress, UserAssessmentScores, ArticleRecommendation, ArticleAnalytics
)
from backend.services.article_search import ArticleSearchService

# Initialize cache
cache = Cache()

# Cache invalidation functions
def invalidate_article_caches():
    """Invalidate all article-related caches when content is updated"""
    try:
        cache.delete_memoized(get_popular_articles)
        cache.delete_memoized(get_trending_articles)
        cache.delete_memoized(get_recent_articles)
        cache.delete_memoized(get_featured_articles)
        cache.delete_memoized(get_available_topics)
        cache.delete_memoized(get_available_filters)
        logger.info("Article caches invalidated successfully")
    except Exception as e:
        logger.error(f"Error invalidating caches: {str(e)}")

logger = logging.getLogger(__name__)

articles_bp = Blueprint('articles', __name__, url_prefix='/api/articles')

def get_db_session() -> Session:
    """Get database session"""
    return current_app.db.session

def require_auth():
    """Decorator to require authentication"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

def get_user_id() -> Optional[int]:
    """Get current user ID from session"""
    return session.get('user_id')

# Error Handlers
@articles_bp.errorhandler(404)
def article_not_found(error):
    return jsonify({'error': 'Article not found'}), 404

@articles_bp.errorhandler(403)
def access_denied(error):
    return jsonify({'error': 'Access denied', 'message': 'Complete assessment to unlock this content'}), 403

@articles_bp.errorhandler(500)
def internal_error(error):
    db_session = get_db_session()
    db_session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Input Validation Decorators
def validate_json_input(required_fields):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_assessment_scores():
    """Decorator to validate assessment scores"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if data:
                required_scores = ['be_score', 'do_score', 'have_score']
                for score in required_scores:
                    if score in data and not (0 <= data[score] <= 100):
                        return jsonify({'error': f'{score} must be between 0 and 100'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_rating_scores():
    """Decorator to validate rating scores"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if data:
                rating_fields = ['overall_rating', 'helpfulness_rating', 'clarity_rating', 
                               'actionability_rating', 'cultural_relevance_rating']
                for field in rating_fields:
                    if field in data and not (1 <= data[field] <= 5):
                        return jsonify({'error': f'{field} must be between 1 and 5'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_pagination_params():
    """Decorator to validate pagination parameters"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            if page < 1:
                return jsonify({'error': 'Page must be greater than 0'}), 400
            
            if per_page < 1 or per_page > 100:
                return jsonify({'error': 'Per page must be between 1 and 100'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_phase_parameter():
    """Decorator to validate phase parameter"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            phase = kwargs.get('phase')
            if phase and phase not in ['BE', 'DO', 'HAVE']:
                return jsonify({'error': 'Invalid phase. Must be BE, DO, or HAVE'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Article Discovery & Browsing Endpoints

@articles_bp.route('/', methods=['GET'])
@require_auth()
@validate_pagination_params()
def list_articles():
    """List articles with filtering, pagination, and personalization"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        query = request.args.get('q', '').strip()
        
        # Parse filters
        filters = {}
        if request.args.get('phase'):
            filters['phase'] = request.args.get('phase')
        if request.args.get('difficulty'):
            filters['difficulty'] = request.args.get('difficulty')
        if request.args.get('topics'):
            filters['topics'] = request.args.get('topics').split(',')
        if request.args.get('cultural_relevance_min'):
            filters['cultural_relevance_min'] = int(request.args.get('cultural_relevance_min'))
        if request.args.get('reading_time_max'):
            filters['reading_time_max'] = int(request.args.get('reading_time_max'))
        
        # Perform search
        result = search_service.search(
            query=query,
            filters=filters,
            user_id=user_id,
            page=page,
            per_page=per_page
        )
        
        # Return in both formats for compatibility
        return jsonify({
            'success': True,
            'data': result,
            # Alternative format for frontend compatibility
            'articles': result['articles'],
            'pagination': {
                'page': result['pagination']['page'],
                'pages': result['pagination']['pages'],
                'per_page': result['pagination']['per_page'],
                'total': result['pagination']['total'],
                'has_prev': result['pagination']['page'] > 1,
                'has_next': result['pagination']['page'] < result['pagination']['pages']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"List articles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/search', methods=['POST'])
@require_auth()
@validate_json_input([])  # No required fields for search
def advanced_search():
    """Advanced search with multiple filters and ranking"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        data = request.get_json()
        
        # Extract search parameters
        query = data.get('query', '').strip()
        filters = data.get('filters', {})
        page = data.get('page', 1)
        per_page = min(data.get('per_page', 20), 100)
        
        # Perform search
        result = search_service.search(
            query=query,
            filters=filters,
            user_id=user_id,
            page=page,
            per_page=per_page
        )
        
        # Track search for analytics (if ArticleSearch model exists)
        search_id = None
        try:
            from backend.models.articles import ArticleSearch
            search_analytics = ArticleSearch(
                user_id=user_id,
                search_query=query,
                search_filters=filters,
                results_count=result['pagination']['total']
            )
            db_session.add(search_analytics)
            db_session.commit()
            search_id = str(search_analytics.id)
        except ImportError:
            # ArticleSearch model doesn't exist, skip analytics
            pass
        
        return jsonify({
            'success': True,
            'data': result,
            # Alternative format for frontend compatibility
            'articles': result['articles'],
            'query': query,
            'filters_applied': filters,
            'search_id': search_id,  # For click tracking
            'pagination': {
                'page': result['pagination']['page'],
                'pages': result['pagination']['pages'],
                'per_page': result['pagination']['per_page'],
                'total': result['pagination']['total'],
                'has_prev': result['pagination']['page'] > 1,
                'has_next': result['pagination']['page'] < result['pagination']['pages']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Advanced search error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/phases/<phase>', methods=['GET'])
@require_auth()
def get_articles_by_phase(phase):
    """Get articles by Be-Do-Have phase (BE/DO/HAVE)"""
    try:
        if phase not in ['BE', 'DO', 'HAVE']:
            return jsonify({'error': 'Invalid phase. Must be BE, DO, or HAVE'}), 400
        
        user_id = get_user_id()
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        result = search_service.get_articles_by_phase(
            phase=phase,
            user_id=user_id,
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Get articles by phase error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/recommendations', methods=['GET'])
@require_auth()
def get_recommendations():
    """Get personalized article recommendations"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        limit = min(int(request.args.get('limit', 10)), 50)
        include_explanations = request.args.get('explanations', 'false').lower() == 'true'
        
        recommendations = search_service.get_recommendations(
            user_id=user_id,
            limit=limit
        )
        
        # Add recommendation explanations if requested
        if include_explanations:
            recommendation_engine = search_service.recommendation_engine if hasattr(search_service, 'recommendation_engine') else None
            if recommendation_engine:
                for rec in recommendations:
                    explanation = recommendation_engine.get_recommendation_explanation(rec['id'], user_id)
                    rec['recommendation_reason'] = explanation
        
        # Format recommendations for both compatibility modes
        formatted_recommendations = []
        for rec in recommendations:
            formatted_rec = {
                'article': rec,
                'recommendation_reason': rec.get('recommendation_reason', 'Personalized for your profile')
            }
            formatted_recommendations.append(formatted_rec)
        
        return jsonify({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'count': len(recommendations),
                'include_explanations': include_explanations
            },
            # Alternative format for frontend compatibility
            'recommendations': formatted_recommendations
        }), 200
        
    except Exception as e:
        logger.error(f"Get recommendations error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/recommendations/explanation/<article_id>', methods=['GET'])
@require_auth()
def get_recommendation_explanation(article_id):
    """Get explanation for why an article was recommended"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        # Create recommendation engine to get explanation
        from backend.services.article_search import ArticleRecommendationEngine
        recommendation_engine = ArticleRecommendationEngine(db_session)
        
        explanation = recommendation_engine.get_recommendation_explanation(article_id, user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'article_id': article_id,
                'explanation': explanation
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get recommendation explanation error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/trending', methods=['GET'])
@cache.cached(timeout=1800)  # Cache for 30 minutes
def get_trending_articles():
    """Get trending articles for user demographic (cached)"""
    try:
        user_id = get_user_id()  # Optional for trending
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        limit = min(int(request.args.get('limit', 10)), 50)
        
        trending = search_service.get_trending_articles(
            user_id=user_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': {
                'trending': trending,
                'count': len(trending)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get trending articles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/recent', methods=['GET'])
@cache.cached(timeout=900)  # Cache for 15 minutes
def get_recent_articles():
    """Get recently added articles (cached)"""
    try:
        user_id = get_user_id()  # Optional for recent
        db_session = get_db_session()
        
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Get recent articles
        recent_articles = db_session.query(Article).filter(
            Article.is_active == True
        ).order_by(
            desc(Article.created_at)
        ).limit(limit).all()
        
        # Apply access control if user is authenticated
        if user_id:
            search_service = ArticleSearchService(db_session)
            filtered_articles = []
            for article in recent_articles:
                if article.can_user_access(user_id, db_session):
                    article_dict = article.to_dict()
                    article_dict.update(search_service._get_user_specific_data(article.id, user_id))
                    filtered_articles.append(article_dict)
        else:
            # For unauthenticated users, only show beginner articles
            filtered_articles = []
            for article in recent_articles:
                if article.difficulty_level == 'Beginner':
                    filtered_articles.append(article.to_dict())
        
        return jsonify({
            'success': True,
            'data': {
                'recent': filtered_articles,
                'count': len(filtered_articles)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get recent articles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/featured', methods=['GET'])
@cache.cached(timeout=7200)  # Cache for 2 hours
def get_featured_articles():
    """Get admin-featured high-value articles (cached)"""
    try:
        user_id = get_user_id()  # Optional for featured
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        limit = min(int(request.args.get('limit', 10)), 50)
        
        featured = search_service.get_featured_articles(
            user_id=user_id,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': {
                'featured': featured,
                'count': len(featured)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get featured articles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Individual Article Operations

@articles_bp.route('/<article_id>', methods=['GET'])
@require_auth()
def get_article(article_id):
    """Get full article details with access control validation"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get article
        article = db_session.query(Article).filter(
            Article.id == article_id,
            Article.is_active == True
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Check access control
        if not article.can_user_access(user_id, db_session):
            return jsonify({'error': 'Access denied. Complete assessment to unlock this content.'}), 403
        
        # Get user-specific data
        search_service = ArticleSearchService(db_session)
        article_dict = article.to_dict()
        article_dict.update(search_service._get_user_specific_data(article.id, user_id))
        
        # Add full content for authenticated users
        article_dict['content'] = article.content
        
        return jsonify({
            'success': True,
            'data': article_dict
        }), 200
        
    except Exception as e:
        logger.error(f"Get article error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/<article_id>/related', methods=['GET'])
@require_auth()
def get_related_articles(article_id):
    """Get similar articles and next-step suggestions"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get the main article
        article = db_session.query(Article).filter(
            Article.id == article_id,
            Article.is_active == True
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Find related articles based on topics and phase
        related_articles = db_session.query(Article).filter(
            Article.id != article_id,
            Article.is_active == True,
            Article.primary_phase == article.primary_phase,
            Article.key_topics.overlap(article.key_topics) if article.key_topics else True
        ).order_by(
            desc(Article.demographic_relevance),
            desc(Article.is_featured)
        ).limit(5).all()
        
        # Apply access control
        search_service = ArticleSearchService(db_session)
        filtered_related = []
        for related in related_articles:
            if related.can_user_access(user_id, db_session):
                article_dict = related.to_dict()
                article_dict.update(search_service._get_user_specific_data(related.id, user_id))
                filtered_related.append(article_dict)
        
        # Get next-step suggestions (next phase)
        next_phase_map = {'BE': 'DO', 'DO': 'HAVE', 'HAVE': 'BE'}
        next_phase = next_phase_map.get(article.primary_phase)
        
        next_articles = []
        if next_phase:
            next_articles_query = db_session.query(Article).filter(
                Article.primary_phase == next_phase,
                Article.is_active == True,
                Article.difficulty_level == article.difficulty_level
            ).order_by(
                Article.recommended_reading_order
            ).limit(3).all()
            
            for next_article in next_articles_query:
                if next_article.can_user_access(user_id, db_session):
                    article_dict = next_article.to_dict()
                    article_dict.update(search_service._get_user_specific_data(next_article.id, user_id))
                    next_articles.append(article_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'related': filtered_related,
                'next_steps': next_articles,
                'current_phase': article.primary_phase,
                'next_phase': next_phase
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get related articles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/<article_id>/access', methods=['GET'])
@require_auth()
def check_article_access(article_id):
    """Check if user can access article (assessment requirements)"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get article
        article = db_session.query(Article).filter(
            Article.id == article_id,
            Article.is_active == True
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Check access
        can_access = article.can_user_access(user_id, db_session)
        
        # Get user's assessment scores for context
        assessment = db_session.query(UserAssessmentScores).filter_by(user_id=user_id).first()
        
        response_data = {
            'can_access': can_access,
            'article_phase': article.primary_phase,
            'article_difficulty': article.difficulty_level
        }
        
        if assessment:
            response_data['user_scores'] = {
                'be_score': assessment.be_score,
                'do_score': assessment.do_score,
                'have_score': assessment.have_score
            }
        
        if not can_access:
            # Provide guidance on what's needed
            if article.difficulty_level == 'Intermediate':
                response_data['required_score'] = 60
            elif article.difficulty_level == 'Advanced':
                response_data['required_score'] = 80
            
            response_data['message'] = f"Complete the {article.primary_phase} assessment to unlock this content."
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Check article access error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/<article_id>/view', methods=['POST'])
@require_auth()
def track_article_view(article_id):
    """Track article view for analytics"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get article
        article = db_session.query(Article).filter(
            Article.id == article_id,
            Article.is_active == True
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Check if user has already read this article
        existing_read = db_session.query(UserArticleRead).filter_by(
            user_id=user_id,
            article_id=article_id
        ).first()
        
        if existing_read:
            # Update existing read record
            existing_read.updated_at = datetime.utcnow()
        else:
            # Create new read record
            new_read = UserArticleRead(
                user_id=user_id,
                article_id=article_id,
                started_at=datetime.utcnow()
            )
            db_session.add(new_read)
        
        # Update analytics
        analytics = db_session.query(ArticleAnalytics).filter_by(article_id=article_id).first()
        if analytics:
            analytics.total_views += 1
            analytics.updated_at = datetime.utcnow()
        else:
            # Create analytics record if it doesn't exist
            new_analytics = ArticleAnalytics(
                article_id=article_id,
                total_views=1
            )
            db_session.add(new_analytics)
        
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': 'View tracked successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Track article view error: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# User Progress & Interaction Endpoints

@articles_bp.route('/<article_id>/progress', methods=['POST'])
@require_auth()
@validate_json_input([])  # Progress data is optional
def update_reading_progress(article_id):
    """Update reading progress (start, progress %, completion)"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        data = request.get_json()
        
        # Get article
        article = db_session.query(Article).filter(
            Article.id == article_id,
            Article.is_active == True
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Get or create user read record
        user_read = db_session.query(UserArticleRead).filter_by(
            user_id=user_id,
            article_id=article_id
        ).first()
        
        if not user_read:
            user_read = UserArticleRead(
                user_id=user_id,
                article_id=article_id,
                started_at=datetime.utcnow()
            )
            db_session.add(user_read)
        
        # Update progress data
        if 'progress_percentage' in data:
            user_read.scroll_depth_percentage = min(float(data['progress_percentage']), 100.0)
        
        if 'time_spent_seconds' in data:
            user_read.time_spent_seconds = int(data['time_spent_seconds'])
        
        if 'engagement_score' in data:
            user_read.engagement_score = float(data['engagement_score'])
        
        if 'completed' in data and data['completed']:
            user_read.completed_at = datetime.utcnow()
        
        if 'found_helpful' in data:
            user_read.found_helpful = bool(data['found_helpful'])
        
        if 'would_recommend' in data:
            user_read.would_recommend = bool(data['would_recommend'])
        
        if 'difficulty_rating' in data:
            user_read.difficulty_rating = int(data['difficulty_rating'])
        
        if 'relevance_rating' in data:
            user_read.relevance_rating = int(data['relevance_rating'])
        
        user_read.updated_at = datetime.utcnow()
        
        # Update analytics
        analytics = db_session.query(ArticleAnalytics).filter_by(article_id=article_id).first()
        if analytics:
            if 'completed' in data and data['completed']:
                analytics.total_reads += 1
            
            # Update average time spent
            if 'time_spent_seconds' in data:
                # Simple average calculation (in production, you might want more sophisticated)
                if analytics.total_reads > 0:
                    analytics.average_time_spent = (
                        (analytics.average_time_spent * (analytics.total_reads - 1) + data['time_spent_seconds']) 
                        / analytics.total_reads
                    )
            
            analytics.updated_at = datetime.utcnow()
        
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Update reading progress error: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/<article_id>/bookmark', methods=['POST'])
@require_auth()
def toggle_bookmark(article_id):
    """Toggle bookmark status"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get article
        article = db_session.query(Article).filter(
            Article.id == article_id,
            Article.is_active == True
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        data = request.get_json() or {}
        
        # Check if already bookmarked
        existing_bookmark = db_session.query(UserArticleBookmark).filter_by(
            user_id=user_id,
            article_id=article_id
        ).first()
        
        if existing_bookmark:
            # Remove bookmark
            db_session.delete(existing_bookmark)
            action = 'removed'
        else:
            # Add bookmark
            new_bookmark = UserArticleBookmark(
                user_id=user_id,
                article_id=article_id,
                notes=data.get('notes'),
                tags=data.get('tags', []),
                priority=data.get('priority', 1),
                folder_name=data.get('folder_name', 'General')
            )
            db_session.add(new_bookmark)
            action = 'added'
        
        # Update analytics
        analytics = db_session.query(ArticleAnalytics).filter_by(article_id=article_id).first()
        if analytics:
            if action == 'added':
                analytics.total_bookmarks += 1
            else:
                analytics.total_bookmarks = max(0, analytics.total_bookmarks - 1)
            analytics.updated_at = datetime.utcnow()
        
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Bookmark {action} successfully',
            'data': {'action': action}
        }), 200
        
    except Exception as e:
        logger.error(f"Toggle bookmark error: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/<article_id>/rating', methods=['POST'])
@require_auth()
@validate_json_input(['overall_rating'])
@validate_rating_scores()
def rate_article(article_id):
    """Rate article helpfulness (1-5 stars)"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        data = request.get_json()
        
        # Validate rating
        overall_rating = data.get('overall_rating')
        
        # Get article
        article = db_session.query(Article).filter(
            Article.id == article_id,
            Article.is_active == True
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Check if user has already rated this article
        existing_rating = db_session.query(UserArticleRating).filter_by(
            user_id=user_id,
            article_id=article_id
        ).first()
        
        if existing_rating:
            # Update existing rating
            existing_rating.overall_rating = overall_rating
            existing_rating.helpfulness_rating = data.get('helpfulness_rating')
            existing_rating.clarity_rating = data.get('clarity_rating')
            existing_rating.actionability_rating = data.get('actionability_rating')
            existing_rating.cultural_relevance_rating = data.get('cultural_relevance_rating')
            existing_rating.review_text = data.get('review_text')
            existing_rating.review_title = data.get('review_title')
            existing_rating.updated_at = datetime.utcnow()
            action = 'updated'
        else:
            # Create new rating
            new_rating = UserArticleRating(
                user_id=user_id,
                article_id=article_id,
                overall_rating=overall_rating,
                helpfulness_rating=data.get('helpfulness_rating'),
                clarity_rating=data.get('clarity_rating'),
                actionability_rating=data.get('actionability_rating'),
                cultural_relevance_rating=data.get('cultural_relevance_rating'),
                review_text=data.get('review_text'),
                review_title=data.get('review_title')
            )
            db_session.add(new_rating)
            action = 'created'
        
        # Update analytics
        analytics = db_session.query(ArticleAnalytics).filter_by(article_id=article_id).first()
        if analytics:
            if action == 'created':
                analytics.total_ratings += 1
            
            # Recalculate average rating
            all_ratings = db_session.query(UserArticleRating.overall_rating).filter_by(
                article_id=article_id
            ).all()
            
            if all_ratings:
                total_rating = sum(rating[0] for rating in all_ratings)
                analytics.average_rating = total_rating / len(all_ratings)
            
            analytics.updated_at = datetime.utcnow()
        
        db_session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Rating {action} successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Rate article error: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

# User Progress & Reading History Endpoints

@articles_bp.route('/user/reading-progress', methods=['GET'])
@require_auth()
def get_reading_progress():
    """Get user's reading history and progress"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get user's reading history
        user_reads = db_session.query(UserArticleRead).filter_by(
            user_id=user_id
        ).order_by(
            desc(UserArticleRead.started_at)
        ).all()
        
        # Get user's bookmarks
        user_bookmarks = db_session.query(UserArticleBookmark).filter_by(
            user_id=user_id
        ).order_by(
            desc(UserArticleBookmark.created_at)
        ).all()
        
        # Get user's ratings
        user_ratings = db_session.query(UserArticleRating).filter_by(
            user_id=user_id
        ).order_by(
            desc(UserArticleRating.created_at)
        ).all()
        
        # Compile reading history
        reading_history = []
        for read in user_reads:
            article = db_session.query(Article).filter_by(id=read.article_id).first()
            if article:
                history_item = {
                    'article': article.to_dict(),
                    'read_data': {
                        'started_at': read.started_at.isoformat() if read.started_at else None,
                        'completed_at': read.completed_at.isoformat() if read.completed_at else None,
                        'time_spent_seconds': read.time_spent_seconds,
                        'scroll_depth_percentage': read.scroll_depth_percentage,
                        'engagement_score': read.engagement_score,
                        'found_helpful': read.found_helpful,
                        'would_recommend': read.would_recommend
                    }
                }
                reading_history.append(history_item)
        
        # Compile bookmarks
        bookmarks = []
        for bookmark in user_bookmarks:
            article = db_session.query(Article).filter_by(id=bookmark.article_id).first()
            if article:
                bookmark_item = {
                    'article': article.to_dict(),
                    'bookmark_data': {
                        'notes': bookmark.notes,
                        'tags': bookmark.tags,
                        'priority': bookmark.priority,
                        'folder_name': bookmark.folder_name,
                        'is_archived': bookmark.is_archived,
                        'created_at': bookmark.created_at.isoformat()
                    }
                }
                bookmarks.append(bookmark_item)
        
        # Compile ratings
        ratings = []
        for rating in user_ratings:
            article = db_session.query(Article).filter_by(id=rating.article_id).first()
            if article:
                rating_item = {
                    'article': article.to_dict(),
                    'rating_data': {
                        'overall_rating': rating.overall_rating,
                        'helpfulness_rating': rating.helpfulness_rating,
                        'clarity_rating': rating.clarity_rating,
                        'actionability_rating': rating.actionability_rating,
                        'cultural_relevance_rating': rating.cultural_relevance_rating,
                        'review_text': rating.review_text,
                        'review_title': rating.review_title,
                        'created_at': rating.created_at.isoformat()
                    }
                }
                ratings.append(rating_item)
        
        return jsonify({
            'success': True,
            'data': {
                'reading_history': reading_history,
                'bookmarks': bookmarks,
                'ratings': ratings,
                'stats': {
                    'total_articles_read': len(reading_history),
                    'total_bookmarks': len(bookmarks),
                    'total_ratings': len(ratings),
                    'completed_articles': len([r for r in reading_history if r['read_data']['completed_at']])
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get reading progress error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/user/bookmarks', methods=['GET'])
@require_auth()
def get_user_bookmarks():
    """Get user's bookmarked articles with metadata"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get user's bookmarks
        user_bookmarks = db_session.query(UserArticleBookmark).filter_by(
            user_id=user_id
        ).order_by(
            desc(UserArticleBookmark.created_at)
        ).all()
        
        bookmarks = []
        for bookmark in user_bookmarks:
            article = db_session.query(Article).filter_by(id=bookmark.article_id).first()
            if article and article.is_active:
                bookmark_item = {
                    'article': article.to_dict(),
                    'bookmark_data': {
                        'notes': bookmark.notes,
                        'tags': bookmark.tags,
                        'priority': bookmark.priority,
                        'folder_name': bookmark.folder_name,
                        'is_archived': bookmark.is_archived,
                        'created_at': bookmark.created_at.isoformat()
                    }
                }
                bookmarks.append(bookmark_item)
        
        return jsonify({
            'success': True,
            'data': {
                'bookmarks': bookmarks,
                'count': len(bookmarks)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user bookmarks error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/user/reading-stats', methods=['GET'])
@require_auth()
def get_reading_stats():
    """Get user's reading statistics and achievements"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get user's reading data
        user_reads = db_session.query(UserArticleRead).filter_by(user_id=user_id).all()
        
        # Calculate statistics
        total_articles_read = len(user_reads)
        completed_articles = len([r for r in user_reads if r.completed_at])
        total_time_spent = sum(r.time_spent_seconds for r in user_reads if r.time_spent_seconds)
        average_engagement = sum(r.engagement_score for r in user_reads if r.engagement_score) / len(user_reads) if user_reads else 0
        
        # Phase breakdown
        phase_stats = {'BE': 0, 'DO': 0, 'HAVE': 0}
        for read in user_reads:
            article = db_session.query(Article).filter_by(id=read.article_id).first()
            if article:
                phase_stats[article.primary_phase] += 1
        
        # Difficulty breakdown
        difficulty_stats = {'Beginner': 0, 'Intermediate': 0, 'Advanced': 0}
        for read in user_reads:
            article = db_session.query(Article).filter_by(id=read.article_id).first()
            if article:
                difficulty_stats[article.difficulty_level] += 1
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_reads = [r for r in user_reads if r.started_at and r.started_at >= thirty_days_ago]
        
        stats = {
            'total_articles_read': total_articles_read,
            'completed_articles': completed_articles,
            'completion_rate': (completed_articles / total_articles_read * 100) if total_articles_read > 0 else 0,
            'total_time_spent_hours': total_time_spent / 3600,
            'average_engagement_score': average_engagement,
            'phase_breakdown': phase_stats,
            'difficulty_breakdown': difficulty_stats,
            'recent_activity': {
                'articles_read_30_days': len(recent_reads),
                'last_read_date': max(r.started_at for r in user_reads).isoformat() if user_reads else None
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Get reading stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Assessment & Access Control Endpoints

@articles_bp.route('/user/assessment', methods=['GET'])
@require_auth()
def get_user_assessment():
    """Get current Be-Do-Have assessment scores with content access information"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get latest assessment
        assessment = db_session.query(UserAssessmentScores).filter_by(
            user_id=user_id
        ).order_by(desc(UserAssessmentScores.assessment_date)).first()
        
        if not assessment:
            return jsonify({
                'success': True,
                'data': {
                    'has_assessment': False,
                    'message': 'No assessment completed yet'
                }
            }), 200
        
        # Calculate content access information
        total_articles = db_session.query(Article).filter_by(is_active=True).count()
        accessible_articles = 0
        
        # Count accessible articles
        all_articles = db_session.query(Article).filter_by(is_active=True).all()
        for article in all_articles:
            if article.can_user_access(user_id, db_session):
                accessible_articles += 1
        
        access_percentage = round((accessible_articles / total_articles) * 100, 1) if total_articles > 0 else 0
        
        assessment_data = {
            'has_assessment': True,
            'assessment': {
                'scores': {
                    'be_score': assessment.be_score,
                    'do_score': assessment.do_score,
                    'have_score': assessment.have_score
                },
                'levels': {
                    'be_level': assessment.be_level,
                    'do_level': assessment.do_level,
                    'have_level': assessment.have_level
                },
                'metadata': {
                    'assessment_date': assessment.assessment_date.isoformat() if assessment.assessment_date else None,
                    'assessment_version': assessment.assessment_version,
                    'confidence_score': assessment.confidence_score,
                    'is_valid': assessment.is_valid
                }
            },
            'content_access': {
                'total_articles': total_articles,
                'accessible_articles': accessible_articles,
                'access_percentage': access_percentage
            }
        }
        
        return jsonify({
            'success': True,
            'data': assessment_data,
            # Alternative format for frontend compatibility
            'assessment': assessment.to_dict(),
            'content_access': {
                'total_articles': total_articles,
                'accessible_articles': accessible_articles,
                'access_percentage': access_percentage
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get user assessment error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/user/assessment', methods=['POST'])
@require_auth()
@validate_json_input(['be_score', 'do_score', 'have_score'])
@validate_assessment_scores()
def submit_assessment():
    """Submit/update assessment scores with automatic recommendation generation"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        data = request.get_json()
        
        # Calculate overall readiness level
        avg_score = (data['be_score'] + data['do_score'] + data['have_score']) / 3
        if avg_score >= 80:
            readiness_level = 'Advanced'
        elif avg_score >= 60:
            readiness_level = 'Intermediate'
        else:
            readiness_level = 'Beginner'
        
        # Check if user already has an assessment
        existing_assessment = db_session.query(UserAssessmentScores).filter_by(user_id=user_id).first()
        
        if existing_assessment:
            # Update existing assessment
            existing_assessment.be_score = data['be_score']
            existing_assessment.do_score = data['do_score']
            existing_assessment.have_score = data['have_score']
            existing_assessment.assessment_date = datetime.utcnow()
            existing_assessment.assessment_version = data.get('version', '1.0')
            existing_assessment.confidence_score = data.get('confidence_score', 0.0)
            existing_assessment.updated_at = datetime.utcnow()
            
            # Update levels based on scores
            existing_assessment.be_level = _get_level_from_score(data['be_score'])
            existing_assessment.do_level = _get_level_from_score(data['do_score'])
            existing_assessment.have_level = _get_level_from_score(data['have_score'])
            
            # Add overall readiness level if field exists
            if hasattr(existing_assessment, 'overall_readiness_level'):
                existing_assessment.overall_readiness_level = readiness_level
            
            action = 'updated'
            assessment = existing_assessment
        else:
            # Create new assessment
            new_assessment = UserAssessmentScores(
                user_id=user_id,
                be_score=data['be_score'],
                do_score=data['do_score'],
                have_score=data['have_score'],
                be_level=_get_level_from_score(data['be_score']),
                do_level=_get_level_from_score(data['do_score']),
                have_level=_get_level_from_score(data['have_score']),
                assessment_version=data.get('version', '1.0'),
                confidence_score=data.get('confidence_score', 0.0),
                total_questions=data.get('total_questions', 0),
                completion_time_minutes=data.get('completion_time_minutes', 0)
            )
            
            # Add overall readiness level if field exists
            if hasattr(new_assessment, 'overall_readiness_level'):
                new_assessment.overall_readiness_level = readiness_level
            
            db_session.add(new_assessment)
            action = 'created'
            assessment = new_assessment
        
        db_session.commit()
        
        # Generate new recommendations based on updated assessment
        try:
            from backend.services.article_search import ArticleRecommendationEngine
            recommendation_engine = ArticleRecommendationEngine(db_session)
            new_recommendations = recommendation_engine.get_personalized_recommendations(
                user_id=user_id,
                limit=5
            )
            
            # Convert recommendations to dictionaries
            recommendation_list = []
            for article in new_recommendations:
                article_dict = article.to_dict()
                # Add recommendation explanation
                explanation = recommendation_engine.get_recommendation_explanation(article.id, user_id)
                article_dict['recommendation_reason'] = explanation
                recommendation_list.append(article_dict)
                
        except Exception as rec_error:
            logger.error(f"Failed to generate recommendations: {str(rec_error)}")
            recommendation_list = []
        
        return jsonify({
            'success': True,
            'message': f'Assessment {action} successfully',
            'data': {
                'assessment': assessment.to_dict(),
                'overall_readiness_level': readiness_level,
                'new_recommendations': recommendation_list
            },
            # Alternative format for frontend compatibility
            'assessment': assessment.to_dict(),
            'overall_readiness_level': readiness_level,
            'new_recommendations': recommendation_list
        }), 200
        
    except Exception as e:
        logger.error(f"Submit assessment error: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

def _get_level_from_score(score):
    """Convert score to level"""
    if score >= 80:
        return 'Advanced'
    elif score >= 60:
        return 'Intermediate'
    else:
        return 'Beginner'

@articles_bp.route('/user/unlocked-articles', methods=['GET'])
@require_auth()
def get_unlocked_articles():
    """Get articles user can access based on assessment"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        # Get all articles user can access
        all_articles = db_session.query(Article).filter(Article.is_active == True).all()
        
        unlocked_articles = []
        for article in all_articles:
            if article.can_user_access(user_id, db_session):
                article_dict = article.to_dict()
                article_dict.update(search_service._get_user_specific_data(article.id, user_id))
                unlocked_articles.append(article_dict)
        
        return jsonify({
            'success': True,
            'data': {
                'unlocked_articles': unlocked_articles,
                'count': len(unlocked_articles)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get unlocked articles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/user/locked-articles', methods=['GET'])
@require_auth()
def get_locked_articles():
    """Get articles requiring higher assessment scores"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Get all articles
        all_articles = db_session.query(Article).filter(Article.is_active == True).all()
        
        locked_articles = []
        for article in all_articles:
            if not article.can_user_access(user_id, db_session):
                locked_articles.append(article.to_dict())
        
        return jsonify({
            'success': True,
            'data': {
                'locked_articles': locked_articles,
                'count': len(locked_articles)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get locked articles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/user/assessment-progress', methods=['GET'])
@require_auth()
def get_assessment_progress():
    """Get progress toward unlocking advanced content"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        assessment = db_session.query(UserAssessmentScores).filter_by(user_id=user_id).first()
        
        if not assessment:
            return jsonify({
                'success': True,
                'data': {
                    'has_assessment': False,
                    'message': 'Complete assessment to unlock content'
                }
            }), 200
        
        # Calculate progress toward next levels
        progress = {}
        for phase in ['BE', 'DO', 'HAVE']:
            score = getattr(assessment, f'{phase.lower()}_score')
            level = getattr(assessment, f'{phase.lower()}_level')
            
            if level == 'Beginner':
                progress_to_next = (score / 60) * 100  # Progress to Intermediate
                next_level = 'Intermediate'
                required_score = 60
            elif level == 'Intermediate':
                progress_to_next = ((score - 60) / 20) * 100  # Progress to Advanced
                next_level = 'Advanced'
                required_score = 80
            else:
                progress_to_next = 100  # Already at max level
                next_level = None
                required_score = None
            
            progress[phase] = {
                'current_score': score,
                'current_level': level,
                'next_level': next_level,
                'required_score': required_score,
                'progress_to_next': min(progress_to_next, 100)
            }
        
        return jsonify({
            'success': True,
            'data': {
                'has_assessment': True,
                'progress': progress
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get assessment progress error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Search & Discovery Endpoints

@articles_bp.route('/autocomplete', methods=['GET'])
def get_search_suggestions():
    """Get search term autocomplete suggestions"""
    try:
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'data': {'suggestions': []}
            }), 200
        
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        suggestions = search_service.get_search_suggestions(query, limit=10)
        
        return jsonify({
            'success': True,
            'data': {'suggestions': suggestions}
        }), 200
        
    except Exception as e:
        logger.error(f"Get search suggestions error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/topics', methods=['GET'])
@cache.cached(timeout=7200)  # Cache for 2 hours
def get_available_topics():
    """Get available topics and categories (cached)"""
    try:
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        filters = search_service.get_available_filters()
        
        return jsonify({
            'success': True,
            'data': {
                'topics': filters.get('topics', []),
                'phases': filters.get('phases', []),
                'difficulty_levels': filters.get('difficulty_levels', []),
                'income_ranges': filters.get('income_ranges', []),
                'career_stages': filters.get('career_stages', [])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get available topics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/filters', methods=['GET'])
@cache.cached(timeout=7200)  # Cache for 2 hours
def get_available_filters():
    """Get available filter options (phases, levels, topics) (cached)"""
    try:
        db_session = get_db_session()
        search_service = ArticleSearchService(db_session)
        
        filters = search_service.get_available_filters()
        
        return jsonify({
            'success': True,
            'data': filters
        }), 200
        
    except Exception as e:
        logger.error(f"Get available filters error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Analytics & Tracking Endpoints

@articles_bp.route('/popular', methods=['GET'])
@cache.cached(timeout=3600)  # Cache for 1 hour
def get_popular_articles():
    """Get most read articles in user's demographic (cached)"""
    try:
        user_id = get_user_id()  # Optional for popular articles
        db_session = get_db_session()
        
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Get articles with highest views
        popular_articles = db_session.query(Article).join(ArticleAnalytics).filter(
            Article.is_active == True,
            ArticleAnalytics.total_views > 0
        ).order_by(
            desc(ArticleAnalytics.total_views),
            desc(ArticleAnalytics.average_rating)
        ).limit(limit).all()
        
        # Apply access control if user is authenticated
        if user_id:
            search_service = ArticleSearchService(db_session)
            filtered_articles = []
            for article in popular_articles:
                if article.can_user_access(user_id, db_session):
                    article_dict = article.to_dict()
                    article_dict.update(search_service._get_user_specific_data(article.id, user_id))
                    filtered_articles.append(article_dict)
        else:
            # For unauthenticated users, only show beginner articles
            filtered_articles = []
            for article in popular_articles:
                if article.difficulty_level == 'Beginner':
                    filtered_articles.append(article.to_dict())
        
        return jsonify({
            'success': True,
            'data': {
                'popular_articles': filtered_articles,
                'count': len(filtered_articles)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get popular articles error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/<article_id>/share', methods=['POST'])
@require_auth()
def track_article_share(article_id):
    """Track social sharing"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        data = request.get_json() or {}
        share_platform = data.get('platform', 'unknown')
        
        # Get article
        article = db_session.query(Article).filter(
            Article.id == article_id,
            Article.is_active == True
        ).first()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        # Update analytics
        analytics = db_session.query(ArticleAnalytics).filter_by(article_id=article_id).first()
        if analytics:
            analytics.total_shares += 1
            analytics.updated_at = datetime.utcnow()
        
        # Log the share event (you might want to create a separate table for this)
        logger.info(f"User {user_id} shared article {article_id} on {share_platform}")
        
        return jsonify({
            'success': True,
            'message': 'Share tracked successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Track article share error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/search/click', methods=['POST'])
@require_auth()
@validate_json_input(['search_id', 'article_id'])
def track_search_click():
    """Track when user clicks on a search result"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        data = request.get_json()
        
        search_id = data.get('search_id')
        article_id = data.get('article_id')
        position = data.get('position')
        
        # Update the search record with click information
        try:
            from backend.models.articles import ArticleSearch
            search_record = db_session.query(ArticleSearch).filter_by(id=search_id).first()
            
            if search_record and search_record.user_id == user_id:
                search_record.clicked_article_id = article_id
                search_record.clicked_position = position
                db_session.commit()
                
                logger.info(f"User {user_id} clicked article {article_id} at position {position} from search {search_id}")
            else:
                logger.warning(f"Search record not found or user mismatch: search_id={search_id}, user_id={user_id}")
                
        except ImportError:
            # ArticleSearch model not available, just log the click
            logger.info(f"User {user_id} clicked article {article_id} at position {position}")
        
        return jsonify({
            'success': True,
            'message': 'Search click tracked successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Track search click error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@articles_bp.route('/stats', methods=['GET'])
@require_auth()
def get_article_stats():
    """Get article engagement statistics (admin)"""
    try:
        user_id = get_user_id()
        db_session = get_db_session()
        
        # Check if user is admin (you might want to add admin role checking)
        # For now, we'll return basic stats for all users
        
        # Get overall statistics
        total_articles = db_session.query(Article).filter(Article.is_active == True).count()
        total_views = db_session.query(func.sum(ArticleAnalytics.total_views)).scalar() or 0
        total_reads = db_session.query(func.sum(ArticleAnalytics.total_reads)).scalar() or 0
        total_bookmarks = db_session.query(func.sum(ArticleAnalytics.total_bookmarks)).scalar() or 0
        
        # Get top performing articles
        top_articles = db_session.query(Article).join(ArticleAnalytics).filter(
            Article.is_active == True
        ).order_by(
            desc(ArticleAnalytics.total_views)
        ).limit(10).all()
        
        top_articles_data = []
        for article in top_articles:
            analytics = db_session.query(ArticleAnalytics).filter_by(article_id=article.id).first()
            article_data = article.to_dict()
            if analytics:
                article_data['analytics'] = {
                    'total_views': analytics.total_views,
                    'total_reads': analytics.total_reads,
                    'average_rating': analytics.average_rating,
                    'completion_rate': analytics.completion_rate
                }
            top_articles_data.append(article_data)
        
        stats = {
            'overall': {
                'total_articles': total_articles,
                'total_views': total_views,
                'total_reads': total_reads,
                'total_bookmarks': total_bookmarks,
                'average_completion_rate': (total_reads / total_views * 100) if total_views > 0 else 0
            },
            'top_performing': top_articles_data
        }
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Get article stats error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
