"""
Analytics API Routes for Mingus Article Library

Comprehensive analytics endpoints for tracking user engagement, article performance,
search behavior, cultural relevance effectiveness, and system performance.
"""

from flask import Blueprint, request, jsonify, session, current_app
from flask_caching import Cache
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text, case, cast, Float
from datetime import datetime, timedelta
import uuid
import logging
from typing import Dict, List, Optional, Any
from functools import wraps
import json

from backend.models.article_analytics import (
    UserEngagementMetrics, ArticlePerformanceMetrics, SearchAnalytics,
    CulturalRelevanceAnalytics, BeDoHaveTransformationAnalytics,
    ContentGapAnalysis, SystemPerformanceMetrics, A_BTestResults
)
from backend.models.articles import Article, UserArticleRead, UserArticleBookmark
from backend.models.user import User
from backend.services.analytics_collection_service import AnalyticsCollectionService

# Initialize cache
cache = Cache()

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

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

def require_admin():
    """Decorator to require admin privileges"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            db_session = get_db_session()
            user = db_session.query(User).filter(User.id == user_id).first()
            if not user or not user.is_admin:
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# Error Handlers
@analytics_bp.errorhandler(404)
def analytics_not_found(error):
    return jsonify({'error': 'Analytics data not found'}), 404

@analytics_bp.errorhandler(403)
def access_denied(error):
    return jsonify({'error': 'Access denied'}), 403

@analytics_bp.errorhandler(500)
def internal_error(error):
    db_session = get_db_session()
    db_session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# USER ENGAGEMENT ANALYTICS
# ============================================================================

@analytics_bp.route('/user-engagement', methods=['GET'])
@require_auth
def get_user_engagement_analytics():
    """Get comprehensive user engagement analytics"""
    try:
        user_id = session.get('user_id')
        db_session = get_db_session()
        
        # Get date range from query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user engagement metrics
        engagement_metrics = db_session.query(UserEngagementMetrics).filter(
            and_(
                UserEngagementMetrics.user_id == user_id,
                UserEngagementMetrics.created_at >= start_date
            )
        ).all()
        
        # Calculate aggregated metrics
        total_sessions = len(engagement_metrics)
        total_session_time = sum(m.total_session_time for m in engagement_metrics)
        total_articles_viewed = sum(m.articles_viewed for m in engagement_metrics)
        total_articles_completed = sum(m.articles_completed for m in engagement_metrics)
        total_search_queries = sum(m.search_queries_count for m in engagement_metrics)
        
        # Calculate averages
        avg_session_time = total_session_time / total_sessions if total_sessions > 0 else 0
        avg_articles_per_session = total_articles_viewed / total_sessions if total_sessions > 0 else 0
        completion_rate = (total_articles_completed / total_articles_viewed * 100) if total_articles_viewed > 0 else 0
        
        # Get cultural engagement metrics
        cultural_metrics = db_session.query(CulturalRelevanceAnalytics).filter(
            CulturalRelevanceAnalytics.user_id == user_id
        ).first()
        
        # Get Be-Do-Have transformation metrics
        transformation_metrics = db_session.query(BeDoHaveTransformationAnalytics).filter(
            BeDoHaveTransformationAnalytics.user_id == user_id
        ).first()
        
        return jsonify({
            'success': True,
            'data': {
                'session_analytics': {
                    'total_sessions': total_sessions,
                    'total_session_time_minutes': round(total_session_time / 60, 2),
                    'average_session_time_minutes': round(avg_session_time / 60, 2),
                    'average_articles_per_session': round(avg_articles_per_session, 2)
                },
                'content_engagement': {
                    'total_articles_viewed': total_articles_viewed,
                    'total_articles_completed': total_articles_completed,
                    'completion_rate_percent': round(completion_rate, 2),
                    'total_bookmarks': sum(m.articles_bookmarked for m in engagement_metrics),
                    'total_shares': sum(m.articles_shared for m in engagement_metrics)
                },
                'search_behavior': {
                    'total_search_queries': total_search_queries,
                    'average_search_success_rate': sum(m.search_success_rate for m in engagement_metrics) / total_sessions if total_sessions > 0 else 0,
                    'recommendations_clicked': sum(m.recommendations_clicked for m in engagement_metrics)
                },
                'assessment_progression': {
                    'assessment_completed': any(m.assessment_completed for m in engagement_metrics),
                    'be_score_change': sum(m.be_score_change for m in engagement_metrics),
                    'do_score_change': sum(m.do_score_change for m in engagement_metrics),
                    'have_score_change': sum(m.have_score_change for m in engagement_metrics),
                    'content_unlocked_count': sum(m.content_unlocked_count for m in engagement_metrics)
                },
                'cultural_engagement': {
                    'cultural_content_preference': cultural_metrics.high_relevance_content_preference if cultural_metrics else 0,
                    'community_content_engagement': cultural_metrics.community_content_engagement if cultural_metrics else 0,
                    'cultural_search_terms_frequency': cultural_metrics.cultural_search_terms_frequency if cultural_metrics else 0
                },
                'transformation_journey': {
                    'current_phase': transformation_metrics.current_phase if transformation_metrics else 'BE',
                    'phase_duration_days': transformation_metrics.phase_duration_days if transformation_metrics else 0,
                    'be_phase_articles_read': transformation_metrics.be_phase_articles_read if transformation_metrics else 0,
                    'do_phase_articles_read': transformation_metrics.do_phase_articles_read if transformation_metrics else 0,
                    'have_phase_articles_read': transformation_metrics.have_phase_articles_read if transformation_metrics else 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user engagement analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user engagement analytics'}), 500

@analytics_bp.route('/user-engagement/session', methods=['POST'])
@require_auth
def track_user_session():
    """Track user session engagement"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        db_session = get_db_session()
        
        analytics_service = AnalyticsCollectionService(db_session)
        
        # Track session data
        session_id = data.get('session_id')
        device_type = data.get('device_type')
        user_agent = data.get('user_agent')
        
        # Get or create session
        engagement = analytics_service._get_or_create_user_session(user_id, device_type, user_agent)
        
        # Update session metrics
        if 'articles_viewed' in data:
            engagement.articles_viewed = data['articles_viewed']
        if 'articles_completed' in data:
            engagement.articles_completed = data['articles_completed']
        if 'articles_bookmarked' in data:
            engagement.articles_bookmarked = data['articles_bookmarked']
        if 'articles_shared' in data:
            engagement.articles_shared = data['articles_shared']
        if 'search_queries_count' in data:
            engagement.search_queries_count = data['search_queries_count']
        if 'recommendations_clicked' in data:
            engagement.recommendations_clicked = data['recommendations_clicked']
        if 'total_session_time' in data:
            engagement.total_session_time = data['total_session_time']
        
        # End session if requested
        if data.get('session_ended'):
            analytics_service.end_user_session(user_id, session_id)
        
        db_session.commit()
        
        return jsonify({'success': True, 'message': 'Session tracked successfully'})
        
    except Exception as e:
        logger.error(f"Error tracking user session: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Failed to track session'}), 500

# ============================================================================
# ARTICLE PERFORMANCE ANALYTICS
# ============================================================================

@analytics_bp.route('/article-performance', methods=['GET'])
@require_admin
def get_article_performance_analytics():
    """Get comprehensive article performance analytics"""
    try:
        db_session = get_db_session()
        
        # Get date range and filters
        days = request.args.get('days', 30, type=int)
        phase = request.args.get('phase')  # BE, DO, HAVE
        min_views = request.args.get('min_views', 0, type=int)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Build query
        query = db_session.query(ArticlePerformanceMetrics).filter(
            ArticlePerformanceMetrics.created_at >= start_date
        )
        
        if min_views > 0:
            query = query.filter(ArticlePerformanceMetrics.total_views >= min_views)
        
        # Get article performance metrics
        performance_metrics = query.all()
        
        # Calculate aggregated metrics
        total_articles = len(performance_metrics)
        total_views = sum(m.total_views for m in performance_metrics)
        total_unique_viewers = sum(m.unique_viewers for m in performance_metrics)
        avg_completion_rate = sum(m.completion_rate for m in performance_metrics) / total_articles if total_articles > 0 else 0
        avg_reading_time = sum(m.average_reading_time for m in performance_metrics) / total_articles if total_articles > 0 else 0
        
        # Get top performing articles
        top_articles = db_session.query(
            ArticlePerformanceMetrics,
            Article.title,
            Article.phase
        ).join(Article).filter(
            ArticlePerformanceMetrics.created_at >= start_date
        ).order_by(desc(ArticlePerformanceMetrics.total_views)).limit(10).all()
        
        # Get phase performance breakdown
        phase_performance = db_session.query(
            Article.phase,
            func.count(ArticlePerformanceMetrics.id).label('article_count'),
            func.sum(ArticlePerformanceMetrics.total_views).label('total_views'),
            func.avg(ArticlePerformanceMetrics.completion_rate).label('avg_completion_rate'),
            func.avg(ArticlePerformanceMetrics.cultural_engagement_score).label('avg_cultural_score')
        ).join(Article).filter(
            ArticlePerformanceMetrics.created_at >= start_date
        ).group_by(Article.phase).all()
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_articles_analyzed': total_articles,
                    'total_views': total_views,
                    'total_unique_viewers': total_unique_viewers,
                    'average_completion_rate_percent': round(avg_completion_rate, 2),
                    'average_reading_time_minutes': round(avg_reading_time / 60, 2)
                },
                'top_performing_articles': [
                    {
                        'title': article.title,
                        'phase': article.phase,
                        'total_views': metrics.total_views,
                        'completion_rate_percent': round(metrics.completion_rate, 2),
                        'cultural_engagement_score': round(metrics.cultural_engagement_score, 2),
                        'bookmark_rate_percent': round(metrics.bookmark_rate, 2)
                    }
                    for metrics, article in top_articles
                ],
                'phase_performance': [
                    {
                        'phase': phase,
                        'article_count': count,
                        'total_views': views,
                        'average_completion_rate_percent': round(completion_rate, 2),
                        'average_cultural_score': round(cultural_score, 2)
                    }
                    for phase, count, views, completion_rate, cultural_score in phase_performance
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting article performance analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve article performance analytics'}), 500

@analytics_bp.route('/article-performance/<article_id>', methods=['GET'])
@require_auth
def get_article_performance_detail(article_id):
    """Get detailed performance metrics for a specific article"""
    try:
        db_session = get_db_session()
        
        # Get article performance metrics
        performance = db_session.query(ArticlePerformanceMetrics).filter(
            ArticlePerformanceMetrics.article_id == article_id
        ).first()
        
        if not performance:
            return jsonify({'error': 'Article performance data not found'}), 404
        
        # Get article details
        article = db_session.query(Article).filter(Article.id == article_id).first()
        
        return jsonify({
            'success': True,
            'data': {
                'article_info': {
                    'title': article.title,
                    'phase': article.phase,
                    'cultural_relevance_score': article.cultural_relevance_score
                },
                'engagement_metrics': {
                    'total_views': performance.total_views,
                    'unique_viewers': performance.unique_viewers,
                    'average_reading_time_minutes': round(performance.average_reading_time / 60, 2),
                    'completion_rate_percent': round(performance.completion_rate, 2)
                },
                'interaction_metrics': {
                    'bookmark_rate_percent': round(performance.bookmark_rate, 2),
                    'share_rate_percent': round(performance.share_rate, 2),
                    'rating_average': round(performance.rating_average, 2),
                    'rating_count': performance.rating_count
                },
                'cultural_performance': {
                    'cultural_engagement_score': round(performance.cultural_engagement_score, 2),
                    'demographic_reach': performance.demographic_reach
                },
                'business_impact': {
                    'subscription_conversion_rate_percent': round(performance.subscription_conversion_rate, 2),
                    'user_retention_impact': round(performance.user_retention_impact, 2)
                },
                'quality_indicators': {
                    'bounce_rate_percent': round(performance.bounce_rate, 2),
                    'return_reader_rate_percent': round(performance.return_reader_rate, 2),
                    'recommendation_click_rate_percent': round(performance.recommendation_click_rate, 2)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting article performance detail: {str(e)}")
        return jsonify({'error': 'Failed to retrieve article performance detail'}), 500

# ============================================================================
# SEARCH ANALYTICS
# ============================================================================

@analytics_bp.route('/search-analytics', methods=['GET'])
@require_admin
def get_search_analytics():
    """Get comprehensive search behavior analytics"""
    try:
        db_session = get_db_session()
        
        # Get date range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get search analytics
        search_analytics = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.search_timestamp >= start_date
        ).all()
        
        # Calculate aggregated metrics
        total_searches = len(search_analytics)
        successful_searches = sum(1 for s in search_analytics if s.result_clicked)
        search_success_rate = (successful_searches / total_searches * 100) if total_searches > 0 else 0
        
        # Get popular search queries
        popular_queries = db_session.query(
            SearchAnalytics.search_query,
            func.count(SearchAnalytics.id).label('search_count'),
            func.avg(case((SearchAnalytics.result_clicked == True, 1), else_=0)).label('success_rate')
        ).filter(
            SearchAnalytics.search_timestamp >= start_date
        ).group_by(SearchAnalytics.search_query).order_by(desc('search_count')).limit(20).all()
        
        # Get phase-based search patterns
        phase_search_patterns = db_session.query(
            SearchAnalytics.selected_phase,
            func.count(SearchAnalytics.id).label('search_count'),
            func.avg(case((SearchAnalytics.result_clicked == True, 1), else_=0)).label('success_rate'),
            func.avg(SearchAnalytics.results_count).label('avg_results')
        ).filter(
            SearchAnalytics.search_timestamp >= start_date
        ).group_by(SearchAnalytics.selected_phase).all()
        
        # Get cultural search patterns
        cultural_searches = sum(1 for s in search_analytics if s.cultural_keywords_present)
        cultural_search_rate = (cultural_searches / total_searches * 100) if total_searches > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_searches': total_searches,
                    'successful_searches': successful_searches,
                    'search_success_rate_percent': round(search_success_rate, 2),
                    'cultural_search_rate_percent': round(cultural_search_rate, 2)
                },
                'popular_queries': [
                    {
                        'query': query,
                        'search_count': count,
                        'success_rate_percent': round(success_rate * 100, 2)
                    }
                    for query, count, success_rate in popular_queries
                ],
                'phase_search_patterns': [
                    {
                        'phase': phase,
                        'search_count': count,
                        'success_rate_percent': round(success_rate * 100, 2),
                        'average_results': round(avg_results, 2)
                    }
                    for phase, count, success_rate, avg_results in phase_search_patterns
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting search analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve search analytics'}), 500

@analytics_bp.route('/search-analytics/track', methods=['POST'])
@require_auth
def track_search_behavior():
    """Track user search behavior"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        db_session = get_db_session()
        
        analytics_service = AnalyticsCollectionService(db_session)
        
        # Track search query using the collection service
        success = analytics_service.track_search_query(
            user_id=user_id,
            query=data.get('search_query'),
            results_count=data.get('results_count', 0),
            clicked_article_id=data.get('clicked_article_id'),
            selected_phase=data.get('selected_phase'),
            cultural_relevance_filter=data.get('cultural_relevance_filter')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Search behavior tracked successfully'})
        else:
            return jsonify({'error': 'Failed to track search behavior'}), 500
        
    except Exception as e:
        logger.error(f"Error tracking search behavior: {str(e)}")
        return jsonify({'error': 'Failed to track search behavior'}), 500

# ============================================================================
# CULTURAL RELEVANCE ANALYTICS
# ============================================================================

@analytics_bp.route('/cultural-relevance', methods=['GET'])
@require_admin
def get_cultural_relevance_analytics():
    """Get cultural relevance effectiveness analytics"""
    try:
        db_session = get_db_session()
        
        # Get date range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get cultural relevance analytics
        cultural_analytics = db_session.query(CulturalRelevanceAnalytics).filter(
            CulturalRelevanceAnalytics.created_at >= start_date
        ).all()
        
        # Calculate aggregated metrics
        total_users = len(cultural_analytics)
        avg_high_relevance_preference = sum(c.high_relevance_content_preference for c in cultural_analytics) / total_users if total_users > 0 else 0
        avg_community_engagement = sum(c.community_content_engagement for c in cultural_analytics) / total_users if total_users > 0 else 0
        avg_cultural_completion_rate = sum(c.cultural_content_completion_rate for c in cultural_analytics) / total_users if total_users > 0 else 0
        
        # Get cultural engagement distribution
        high_engagement_users = sum(1 for c in cultural_analytics if c.high_relevance_content_preference >= 7.0)
        medium_engagement_users = sum(1 for c in cultural_analytics if 4.0 <= c.high_relevance_content_preference < 7.0)
        low_engagement_users = sum(1 for c in cultural_analytics if c.high_relevance_content_preference < 4.0)
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'total_users_analyzed': total_users,
                    'average_high_relevance_preference': round(avg_high_relevance_preference, 2),
                    'average_community_engagement': round(avg_community_engagement, 2),
                    'average_cultural_completion_rate_percent': round(avg_cultural_completion_rate, 2)
                },
                'engagement_distribution': {
                    'high_engagement_users': high_engagement_users,
                    'medium_engagement_users': medium_engagement_users,
                    'low_engagement_users': low_engagement_users
                },
                'professional_development_alignment': {
                    'corporate_navigation_interest': sum(c.corporate_navigation_interest for c in cultural_analytics) / total_users if total_users > 0 else 0,
                    'generational_wealth_focus': sum(c.generational_wealth_focus for c in cultural_analytics) / total_users if total_users > 0 else 0,
                    'systemic_barrier_awareness': sum(c.systemic_barrier_awareness_content for c in cultural_analytics) / total_users if total_users > 0 else 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting cultural relevance analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve cultural relevance analytics'}), 500

# ============================================================================
# BE-DO-HAVE TRANSFORMATION ANALYTICS
# ============================================================================

@analytics_bp.route('/transformation-journey', methods=['GET'])
@require_admin
def get_transformation_journey_analytics():
    """Get Be-Do-Have transformation journey analytics"""
    try:
        db_session = get_db_session()
        
        # Get transformation analytics
        transformation_analytics = db_session.query(BeDoHaveTransformationAnalytics).all()
        
        # Calculate phase distribution
        phase_distribution = {}
        for analytics in transformation_analytics:
            phase = analytics.current_phase
            if phase not in phase_distribution:
                phase_distribution[phase] = 0
            phase_distribution[phase] += 1
        
        # Calculate average phase duration
        avg_phase_duration = sum(a.phase_duration_days for a in transformation_analytics) / len(transformation_analytics) if transformation_analytics else 0
        
        # Get phase progression patterns
        phase_progression = {
            'be_phase_users': sum(1 for a in transformation_analytics if a.current_phase == 'BE'),
            'do_phase_users': sum(1 for a in transformation_analytics if a.current_phase == 'DO'),
            'have_phase_users': sum(1 for a in transformation_analytics if a.current_phase == 'HAVE')
        }
        
        return jsonify({
            'success': True,
            'data': {
                'phase_distribution': phase_distribution,
                'average_phase_duration_days': round(avg_phase_duration, 2),
                'phase_progression': phase_progression,
                'total_users_in_journey': len(transformation_analytics)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting transformation journey analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve transformation journey analytics'}), 500

# ============================================================================
# CONTENT GAP ANALYSIS
# ============================================================================

@analytics_bp.route('/content-gaps', methods=['GET'])
@require_admin
def get_content_gap_analysis():
    """Get content gap analysis"""
    try:
        db_session = get_db_session()
        
        # Get content gaps
        content_gaps = db_session.query(ContentGapAnalysis).filter(
            ContentGapAnalysis.status != 'addressed'
        ).order_by(desc(ContentGapAnalysis.priority_score)).all()
        
        # Group by severity
        gaps_by_severity = {}
        for gap in content_gaps:
            severity = gap.gap_severity
            if severity not in gaps_by_severity:
                gaps_by_severity[severity] = []
            gaps_by_severity[severity].append({
                'id': str(gap.id),
                'category': gap.gap_category,
                'description': gap.gap_description,
                'affected_user_count': gap.affected_user_count,
                'priority_score': gap.priority_score,
                'recommended_topics': gap.recommended_topics
            })
        
        return jsonify({
            'success': True,
            'data': {
                'gaps_by_severity': gaps_by_severity,
                'total_gaps': len(content_gaps)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting content gap analysis: {str(e)}")
        return jsonify({'error': 'Failed to retrieve content gap analysis'}), 500

# ============================================================================
# SYSTEM PERFORMANCE MONITORING
# ============================================================================

@analytics_bp.route('/system-performance', methods=['GET'])
@require_admin
def get_system_performance():
    """Get system performance metrics"""
    try:
        db_session = get_db_session()
        
        # Get recent performance metrics
        hours = request.args.get('hours', 24, type=int)
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        performance_metrics = db_session.query(SystemPerformanceMetrics).filter(
            SystemPerformanceMetrics.recorded_at >= start_time
        ).order_by(desc(SystemPerformanceMetrics.recorded_at)).all()
        
        # Calculate averages
        avg_response_time = sum(m.response_time_ms for m in performance_metrics) / len(performance_metrics) if performance_metrics else 0
        avg_success_rate = sum(m.success_rate for m in performance_metrics) / len(performance_metrics) if performance_metrics else 100
        avg_cpu_usage = sum(m.cpu_usage_percent for m in performance_metrics) / len(performance_metrics) if performance_metrics else 0
        avg_memory_usage = sum(m.memory_usage_mb for m in performance_metrics) / len(performance_metrics) if performance_metrics else 0
        
        # Get endpoint performance
        endpoint_performance = db_session.query(
            SystemPerformanceMetrics.endpoint_name,
            func.avg(SystemPerformanceMetrics.response_time_ms).label('avg_response_time'),
            func.sum(SystemPerformanceMetrics.request_count).label('total_requests'),
            func.avg(SystemPerformanceMetrics.success_rate).label('avg_success_rate')
        ).filter(
            SystemPerformanceMetrics.recorded_at >= start_time
        ).group_by(SystemPerformanceMetrics.endpoint_name).all()
        
        return jsonify({
            'success': True,
            'data': {
                'overview': {
                    'average_response_time_ms': round(avg_response_time, 2),
                    'average_success_rate_percent': round(avg_success_rate, 2),
                    'average_cpu_usage_percent': round(avg_cpu_usage, 2),
                    'average_memory_usage_mb': round(avg_memory_usage, 2)
                },
                'endpoint_performance': [
                    {
                        'endpoint': endpoint,
                        'average_response_time_ms': round(avg_response_time, 2),
                        'total_requests': total_requests,
                        'average_success_rate_percent': round(avg_success_rate, 2)
                    }
                    for endpoint, avg_response_time, total_requests, avg_success_rate in endpoint_performance
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting system performance: {str(e)}")
        return jsonify({'error': 'Failed to retrieve system performance'}), 500

@analytics_bp.route('/system-performance/track', methods=['POST'])
def track_system_performance():
    """Track system performance metrics"""
    try:
        data = request.get_json()
        db_session = get_db_session()
        
        # Create performance metrics record
        performance_metrics = SystemPerformanceMetrics(
            endpoint_name=data.get('endpoint_name'),
            response_time_ms=data.get('response_time_ms'),
            request_count=data.get('request_count', 1),
            error_count=data.get('error_count', 0),
            success_rate=data.get('success_rate', 100.0),
            cpu_usage_percent=data.get('cpu_usage_percent', 0.0),
            memory_usage_mb=data.get('memory_usage_mb', 0.0),
            database_connection_count=data.get('database_connection_count', 0),
            cache_hit_rate=data.get('cache_hit_rate', 0.0),
            cache_miss_count=data.get('cache_miss_count', 0),
            concurrent_users=data.get('concurrent_users', 0),
            peak_concurrent_users=data.get('peak_concurrent_users', 0)
        )
        
        db_session.add(performance_metrics)
        db_session.commit()
        
        return jsonify({'success': True, 'message': 'System performance tracked successfully'})
        
    except Exception as e:
        logger.error(f"Error tracking system performance: {str(e)}")
        db_session.rollback()
        return jsonify({'error': 'Failed to track system performance'}), 500

# ============================================================================
# ENHANCED ANALYTICS COLLECTION ENDPOINTS
# ============================================================================

@analytics_bp.route('/track/article-view', methods=['POST'])
@require_auth
def track_article_view():
    """Track article view using analytics collection service"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        db_session = get_db_session()
        
        analytics_service = AnalyticsCollectionService(db_session)
        
        success = analytics_service.track_article_view(
            user_id=user_id,
            article_id=data.get('article_id'),
            reading_time_seconds=data.get('reading_time_seconds', 0),
            device_type=data.get('device_type'),
            user_agent=data.get('user_agent')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Article view tracked successfully'})
        else:
            return jsonify({'error': 'Failed to track article view'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking article view: {str(e)}")
        return jsonify({'error': 'Failed to track article view'}), 500

@analytics_bp.route('/track/article-completion', methods=['POST'])
@require_auth
def track_article_completion():
    """Track article completion using analytics collection service"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        db_session = get_db_session()
        
        analytics_service = AnalyticsCollectionService(db_session)
        
        success = analytics_service.track_article_completion(
            user_id=user_id,
            article_id=data.get('article_id'),
            total_reading_time=data.get('total_reading_time', 0)
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Article completion tracked successfully'})
        else:
            return jsonify({'error': 'Failed to track article completion'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking article completion: {str(e)}")
        return jsonify({'error': 'Failed to track article completion'}), 500

@analytics_bp.route('/track/article-bookmark', methods=['POST'])
@require_auth
def track_article_bookmark():
    """Track article bookmark using analytics collection service"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        db_session = get_db_session()
        
        analytics_service = AnalyticsCollectionService(db_session)
        
        success = analytics_service.track_article_bookmark(
            user_id=user_id,
            article_id=data.get('article_id')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Article bookmark tracked successfully'})
        else:
            return jsonify({'error': 'Failed to track article bookmark'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking article bookmark: {str(e)}")
        return jsonify({'error': 'Failed to track article bookmark'}), 500

@analytics_bp.route('/track/article-share', methods=['POST'])
@require_auth
def track_article_share():
    """Track article share using analytics collection service"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        db_session = get_db_session()
        
        analytics_service = AnalyticsCollectionService(db_session)
        
        success = analytics_service.track_article_share(
            user_id=user_id,
            article_id=data.get('article_id'),
            share_platform=data.get('share_platform')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Article share tracked successfully'})
        else:
            return jsonify({'error': 'Failed to track article share'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking article share: {str(e)}")
        return jsonify({'error': 'Failed to track article share'}), 500

@analytics_bp.route('/track/assessment-completion', methods=['POST'])
@require_auth
def track_assessment_completion():
    """Track assessment completion using analytics collection service"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        db_session = get_db_session()
        
        analytics_service = AnalyticsCollectionService(db_session)
        
        success = analytics_service.track_assessment_completion(
            user_id=user_id,
            be_score_change=data.get('be_score_change', 0),
            do_score_change=data.get('do_score_change', 0),
            have_score_change=data.get('have_score_change', 0)
        )
        
        if success:
            # Also calculate cultural relevance metrics
            analytics_service.calculate_cultural_relevance_metrics(user_id)
            return jsonify({'success': True, 'message': 'Assessment completion tracked successfully'})
        else:
            return jsonify({'error': 'Failed to track assessment completion'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking assessment completion: {str(e)}")
        return jsonify({'error': 'Failed to track assessment completion'}), 500

@analytics_bp.route('/track/session-end', methods=['POST'])
@require_auth
def track_session_end():
    """End user session using analytics collection service"""
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        db_session = get_db_session()
        
        analytics_service = AnalyticsCollectionService(db_session)
        
        success = analytics_service.end_user_session(
            user_id=user_id,
            session_id=data.get('session_id')
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Session ended successfully'})
        else:
            return jsonify({'error': 'Failed to end session'}), 500
            
    except Exception as e:
        logger.error(f"Error ending session: {str(e)}")
        return jsonify({'error': 'Failed to end session'}), 500

@analytics_bp.route('/reports/daily', methods=['GET'])
@require_admin
def get_daily_report():
    """Get daily analytics report"""
    try:
        db_session = get_db_session()
        analytics_service = AnalyticsCollectionService(db_session)
        
        # Get date from query parameters or use today
        date_str = request.args.get('date')
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        else:
            report_date = None
        
        report = analytics_service.generate_daily_report(report_date)
        
        return jsonify({
            'success': True,
            'data': report
        })
        
    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")
        return jsonify({'error': 'Failed to generate daily report'}), 500

# ============================================================================
# A/B TESTING ANALYTICS
# ============================================================================

@analytics_bp.route('/ab-testing', methods=['GET'])
@require_admin
def get_ab_testing_analytics():
    """Get A/B testing results"""
    try:
        db_session = get_db_session()
        
        # Get active A/B tests
        active_tests = db_session.query(A_BTestResults).filter(
            A_BTestResults.test_status == 'active'
        ).all()
        
        # Group by test name
        test_results = {}
        for test in active_tests:
            test_name = test.test_name
            if test_name not in test_results:
                test_results[test_name] = {
                    'variants': {},
                    'feature': test.test_feature
                }
            
            variant = test.test_variant
            if variant not in test_results[test_name]['variants']:
                test_results[test_name]['variants'][variant] = {
                    'user_count': 0,
                    'engagement_rate': 0.0,
                    'conversion_rate': 0.0,
                    'retention_rate': 0.0,
                    'satisfaction_score': 0.0
                }
            
            test_results[test_name]['variants'][variant]['user_count'] += 1
            test_results[test_name]['variants'][variant]['engagement_rate'] = test.engagement_rate
            test_results[test_name]['variants'][variant]['conversion_rate'] = test.conversion_rate
            test_results[test_name]['variants'][variant]['retention_rate'] = test.retention_rate
            test_results[test_name]['variants'][variant]['satisfaction_score'] = test.satisfaction_score
        
        return jsonify({
            'success': True,
            'data': {
                'active_tests': test_results,
                'total_active_tests': len(test_results)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting A/B testing analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve A/B testing analytics'}), 500

# ============================================================================
# DASHBOARD SUMMARY ENDPOINTS
# ============================================================================

@analytics_bp.route('/dashboard-summary', methods=['GET'])
@require_admin
def get_dashboard_summary():
    """Get comprehensive dashboard summary for admin"""
    try:
        db_session = get_db_session()
        
        # Get date range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get key metrics
        total_users = db_session.query(User).count()
        active_users = db_session.query(UserEngagementMetrics).filter(
            UserEngagementMetrics.created_at >= start_date
        ).distinct(UserEngagementMetrics.user_id).count()
        
        total_articles = db_session.query(Article).count()
        total_views = db_session.query(func.sum(ArticlePerformanceMetrics.total_views)).filter(
            ArticlePerformanceMetrics.created_at >= start_date
        ).scalar() or 0
        
        total_searches = db_session.query(SearchAnalytics).filter(
            SearchAnalytics.search_timestamp >= start_date
        ).count()
        
        # Get recent content gaps
        recent_gaps = db_session.query(ContentGapAnalysis).filter(
            ContentGapAnalysis.status == 'identified'
        ).order_by(desc(ContentGapAnalysis.priority_score)).limit(5).all()
        
        # Get system health
        recent_performance = db_session.query(SystemPerformanceMetrics).filter(
            SystemPerformanceMetrics.recorded_at >= start_date
        ).order_by(desc(SystemPerformanceMetrics.recorded_at)).first()
        
        return jsonify({
            'success': True,
            'data': {
                'user_metrics': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'user_activity_rate_percent': round((active_users / total_users * 100) if total_users > 0 else 0, 2)
                },
                'content_metrics': {
                    'total_articles': total_articles,
                    'total_views': total_views,
                    'average_views_per_article': round(total_views / total_articles, 2) if total_articles > 0 else 0
                },
                'engagement_metrics': {
                    'total_searches': total_searches,
                    'search_activity_per_day': round(total_searches / days, 2) if days > 0 else 0
                },
                'content_gaps': [
                    {
                        'category': gap.gap_category,
                        'severity': gap.gap_severity,
                        'affected_users': gap.affected_user_count,
                        'priority_score': gap.priority_score
                    }
                    for gap in recent_gaps
                ],
                'system_health': {
                    'average_response_time_ms': round(recent_performance.response_time_ms, 2) if recent_performance else 0,
                    'success_rate_percent': round(recent_performance.success_rate, 2) if recent_performance else 100,
                    'cpu_usage_percent': round(recent_performance.cpu_usage_percent, 2) if recent_performance else 0
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {str(e)}")
        return jsonify({'error': 'Failed to retrieve dashboard summary'}), 500
