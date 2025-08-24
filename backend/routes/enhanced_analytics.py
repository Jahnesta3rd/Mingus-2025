"""
Enhanced Analytics Routes for Mingus Article Library

Comprehensive analytics dashboard with JWT authentication and advanced metrics
for user engagement, cultural impact, and business intelligence.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from sqlalchemy import func, desc, and_, case
from datetime import datetime, timedelta
import logging

from backend.services.analytics_collection_service import AnalyticsCollectionService
from backend.models.article_analytics import (
    UserEngagementMetrics, ArticlePerformanceMetrics, SearchAnalytics,
    CulturalRelevanceAnalytics, BeDoHaveTransformationAnalytics
)
from backend.models.articles import Article, UserArticleProgress
from backend.models.user import User, UserAssessmentScores

logger = logging.getLogger(__name__)

enhanced_analytics_bp = Blueprint('enhanced_analytics', __name__, url_prefix='/api/analytics')

def get_db_session():
    """Get database session"""
    from backend.database import get_db_session
    return get_db_session()

@enhanced_analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    
    # Only allow admin users to access analytics
    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        db_session = get_db_session()
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # User engagement overview
        user_metrics = db_session.query(
            func.count(UserEngagementMetrics.user_id.distinct()).label('active_users'),
            func.avg(UserEngagementMetrics.total_session_time).label('avg_session_time'),
            func.sum(UserEngagementMetrics.articles_viewed).label('total_article_views'),
            func.sum(UserEngagementMetrics.articles_completed).label('total_completions'),
            func.avg(UserEngagementMetrics.search_success_rate).label('avg_search_success')
        ).filter(UserEngagementMetrics.session_start >= start_date).first()
        
        # Article performance
        top_articles = db_session.query(
            Article.title,
            Article.phase,
            ArticlePerformanceMetrics.total_views,
            ArticlePerformanceMetrics.completion_rate,
            ArticlePerformanceMetrics.cultural_engagement_score
        ).join(ArticlePerformanceMetrics).order_by(
            desc(ArticlePerformanceMetrics.total_views)
        ).limit(10).all()
        
        # Be-Do-Have distribution
        phase_distribution = db_session.query(
            Article.phase,
            func.count(ArticlePerformanceMetrics.article_id).label('article_count'),
            func.sum(ArticlePerformanceMetrics.total_views).label('total_views'),
            func.avg(ArticlePerformanceMetrics.completion_rate).label('avg_completion_rate')
        ).join(ArticlePerformanceMetrics).group_by(Article.phase).all()
        
        # Cultural relevance effectiveness
        cultural_metrics = db_session.query(
            func.avg(CulturalRelevanceAnalytics.high_relevance_content_preference).label('high_relevance_preference'),
            func.avg(CulturalRelevanceAnalytics.community_content_engagement).label('community_engagement'),
            func.avg(CulturalRelevanceAnalytics.cultural_content_completion_rate).label('cultural_completion_rate')
        ).first()
        
        # Search behavior
        search_metrics = db_session.query(
            func.count(SearchAnalytics.id).label('total_searches'),
            func.avg(case([(SearchAnalytics.result_clicked == True, 1)], else_=0)).label('click_through_rate'),
            func.count(case([(SearchAnalytics.cultural_keywords_present == True, 1)])).label('cultural_searches')
        ).filter(SearchAnalytics.search_timestamp >= start_date).first()
        
        # System performance metrics
        system_metrics = db_session.query(
            func.avg(UserEngagementMetrics.total_session_time).label('avg_session_duration'),
            func.count(UserEngagementMetrics.session_id.distinct()).label('total_sessions'),
            func.avg(UserEngagementMetrics.articles_viewed).label('avg_articles_per_session')
        ).filter(UserEngagementMetrics.session_start >= start_date).first()
        
        return jsonify({
            'success': True,
            'period_days': days,
            'user_engagement': {
                'active_users': user_metrics.active_users or 0,
                'avg_session_time_minutes': round((user_metrics.avg_session_time or 0) / 60, 1),
                'total_article_views': user_metrics.total_article_views or 0,
                'total_completions': user_metrics.total_completions or 0,
                'avg_search_success_rate': round(user_metrics.avg_search_success or 0, 1),
                'avg_session_duration_minutes': round((system_metrics.avg_session_duration or 0) / 60, 1),
                'total_sessions': system_metrics.total_sessions or 0,
                'avg_articles_per_session': round(system_metrics.avg_articles_per_session or 0, 1)
            },
            'top_articles': [
                {
                    'title': article.title,
                    'phase': article.phase,
                    'views': article.total_views,
                    'completion_rate': round(article.completion_rate, 1),
                    'cultural_engagement': round(article.cultural_engagement_score, 1)
                }
                for article in top_articles
            ],
            'phase_performance': [
                {
                    'phase': phase.phase,
                    'article_count': phase.article_count,
                    'total_views': phase.total_views,
                    'avg_completion_rate': round(phase.avg_completion_rate, 1)
                }
                for phase in phase_distribution
            ],
            'cultural_effectiveness': {
                'high_relevance_preference': round(cultural_metrics.high_relevance_preference or 0, 1),
                'community_engagement': round(cultural_metrics.community_engagement or 0, 1),
                'cultural_completion_rate': round(cultural_metrics.cultural_completion_rate or 0, 1)
            },
            'search_behavior': {
                'total_searches': search_metrics.total_searches or 0,
                'click_through_rate': round((search_metrics.click_through_rate or 0) * 100, 1),
                'cultural_search_percentage': round(
                    ((search_metrics.cultural_searches or 0) / max(search_metrics.total_searches, 1)) * 100, 1
                )
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analytics dashboard'}), 500

@enhanced_analytics_bp.route('/user-journey', methods=['GET'])
@jwt_required() 
def get_user_journey_analytics():
    """Get user journey and progression analytics"""
    
    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        db_session = get_db_session()
        
        # Assessment progression analysis
        assessment_progression = db_session.query(
            UserAssessmentScores.overall_readiness_level,
            func.count(UserAssessmentScores.user_id).label('user_count'),
            func.avg(UserAssessmentScores.be_score).label('avg_be_score'),
            func.avg(UserAssessmentScores.do_score).label('avg_do_score'),
            func.avg(UserAssessmentScores.have_score).label('avg_have_score')
        ).group_by(UserAssessmentScores.overall_readiness_level).all()
        
        # Content unlocking patterns
        content_unlocking = db_session.query(
            Article.difficulty_level,
            Article.phase,
            func.count(UserArticleProgress.user_id.distinct()).label('unique_readers')
        ).join(UserArticleProgress).group_by(
            Article.difficulty_level, Article.phase
        ).all()
        
        # Transformation journey analytics
        transformation_analytics = db_session.query(
            BeDoHaveTransformationAnalytics.current_phase,
            func.count(BeDoHaveTransformationAnalytics.user_id).label('user_count'),
            func.avg(BeDoHaveTransformationAnalytics.phase_duration_days).label('avg_phase_duration'),
            func.avg(BeDoHaveTransformationAnalytics.be_phase_articles_read).label('avg_be_articles'),
            func.avg(BeDoHaveTransformationAnalytics.do_phase_articles_read).label('avg_do_articles'),
            func.avg(BeDoHaveTransformationAnalytics.have_phase_articles_read).label('avg_have_articles')
        ).group_by(BeDoHaveTransformationAnalytics.current_phase).all()
        
        return jsonify({
            'success': True,
            'assessment_distribution': [
                {
                    'level': prog.overall_readiness_level,
                    'user_count': prog.user_count,
                    'avg_be_score': round(prog.avg_be_score, 1),
                    'avg_do_score': round(prog.avg_do_score, 1),
                    'avg_have_score': round(prog.avg_have_score, 1)
                }
                for prog in assessment_progression
            ],
            'content_access_patterns': [
                {
                    'difficulty': unlock.difficulty_level,
                    'phase': unlock.phase,
                    'unique_readers': unlock.unique_readers
                }
                for unlock in content_unlocking
            ],
            'transformation_journey': [
                {
                    'current_phase': trans.current_phase,
                    'user_count': trans.user_count,
                    'avg_phase_duration_days': round(trans.avg_phase_duration, 1),
                    'avg_be_articles': round(trans.avg_be_articles, 1),
                    'avg_do_articles': round(trans.avg_do_articles, 1),
                    'avg_have_articles': round(trans.avg_have_articles, 1)
                }
                for trans in transformation_analytics
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting user journey analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user journey analytics'}), 500

@enhanced_analytics_bp.route('/track-view', methods=['POST'])
@jwt_required()
def track_article_view():
    """Track article view for analytics"""
    
    try:
        data = request.get_json()
        user_id = get_current_user().id
        article_id = data.get('article_id')
        reading_time = data.get('reading_time_seconds', 0)
        device_type = data.get('device_type')
        user_agent = data.get('user_agent')
        
        if not article_id:
            return jsonify({'error': 'article_id is required'}), 400
        
        db_session = get_db_session()
        analytics_service = AnalyticsCollectionService(db_session)
        
        success = analytics_service.track_article_view(
            user_id=user_id, 
            article_id=article_id, 
            reading_time_seconds=reading_time,
            device_type=device_type,
            user_agent=user_agent
        )
        
        if success:
            return jsonify({'success': True, 'status': 'tracked'})
        else:
            return jsonify({'error': 'Failed to track article view'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking article view: {str(e)}")
        return jsonify({'error': 'Failed to track article view'}), 500

@enhanced_analytics_bp.route('/cultural-impact', methods=['GET'])
@jwt_required()
def get_cultural_impact_metrics():
    """Get cultural personalization impact metrics"""
    
    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        db_session = get_db_session()
        
        # Cultural content performance vs general content
        cultural_vs_general = db_session.query(
            case(
                [(Article.cultural_relevance_score >= 8, 'High Cultural Relevance')],
                else_='Standard Content'
            ).label('content_type'),
            func.avg(ArticlePerformanceMetrics.completion_rate).label('avg_completion'),
            func.avg(ArticlePerformanceMetrics.bookmark_rate).label('avg_bookmark_rate'),
            func.avg(ArticlePerformanceMetrics.rating_average).label('avg_rating'),
            func.count(ArticlePerformanceMetrics.article_id).label('article_count')
        ).join(ArticlePerformanceMetrics).group_by('content_type').all()
        
        # User engagement with cultural content
        cultural_engagement = db_session.query(
            func.avg(CulturalRelevanceAnalytics.high_relevance_content_preference).label('preference_score'),
            func.avg(CulturalRelevanceAnalytics.community_content_engagement).label('engagement_score'),
            func.count(CulturalRelevanceAnalytics.user_id).label('users_tracked'),
            func.avg(CulturalRelevanceAnalytics.cultural_search_terms_frequency).label('avg_cultural_searches')
        ).first()
        
        # Cultural search patterns
        cultural_search_patterns = db_session.query(
            func.count(case([(SearchAnalytics.cultural_keywords_present == True, 1)])).label('cultural_searches'),
            func.count(SearchAnalytics.id).label('total_searches'),
            func.avg(case([
                (SearchAnalytics.cultural_keywords_present == True, 
                 case([(SearchAnalytics.result_clicked == True, 1)], else_=0))
            ], else_=0)).label('cultural_search_success_rate')
        ).first()
        
        return jsonify({
            'success': True,
            'content_performance_comparison': [
                {
                    'content_type': comp.content_type,
                    'avg_completion_rate': round(comp.avg_completion, 1),
                    'avg_bookmark_rate': round(comp.avg_bookmark_rate, 1),
                    'avg_rating': round(comp.avg_rating, 2),
                    'article_count': comp.article_count
                }
                for comp in cultural_vs_general
            ],
            'cultural_engagement_summary': {
                'preference_score': round(cultural_engagement.preference_score or 0, 1),
                'engagement_score': round(cultural_engagement.engagement_score or 0, 1),
                'users_tracked': cultural_engagement.users_tracked or 0,
                'avg_cultural_searches': round(cultural_engagement.avg_cultural_searches or 0, 1)
            },
            'cultural_search_analysis': {
                'cultural_searches': cultural_search_patterns.cultural_searches or 0,
                'total_searches': cultural_search_patterns.total_searches or 0,
                'cultural_search_percentage': round(
                    ((cultural_search_patterns.cultural_searches or 0) / 
                     max(cultural_search_patterns.total_searches, 1)) * 100, 1
                ),
                'cultural_search_success_rate': round(
                    (cultural_search_patterns.cultural_search_success_rate or 0) * 100, 1
                )
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting cultural impact metrics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve cultural impact metrics'}), 500

@enhanced_analytics_bp.route('/business-impact', methods=['GET'])
@jwt_required()
def get_business_impact_metrics():
    """Get business impact and ROI metrics"""
    
    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        db_session = get_db_session()
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Subscription conversion correlation
        conversion_metrics = db_session.query(
            func.avg(ArticlePerformanceMetrics.subscription_conversion_rate).label('avg_conversion_rate'),
            func.avg(ArticlePerformanceMetrics.user_retention_impact).label('avg_retention_impact'),
            func.count(ArticlePerformanceMetrics.article_id).label('articles_analyzed')
        ).filter(ArticlePerformanceMetrics.created_at >= start_date).first()
        
        # User retention analysis
        retention_metrics = db_session.query(
            func.count(UserEngagementMetrics.user_id.distinct()).label('total_users'),
            func.count(case([
                (UserEngagementMetrics.session_start >= start_date, UserEngagementMetrics.user_id)
            ])).label('returning_users')
        ).first()
        
        # Content ROI analysis
        content_roi = db_session.query(
            func.avg(ArticlePerformanceMetrics.cultural_engagement_score).label('avg_cultural_engagement'),
            func.avg(ArticlePerformanceMetrics.completion_rate).label('avg_completion_rate'),
            func.avg(ArticlePerformanceMetrics.bookmark_rate).label('avg_bookmark_rate'),
            func.avg(ArticlePerformanceMetrics.share_rate).label('avg_share_rate')
        ).filter(ArticlePerformanceMetrics.created_at >= start_date).first()
        
        return jsonify({
            'success': True,
            'conversion_metrics': {
                'avg_subscription_conversion_rate': round(conversion_metrics.avg_conversion_rate or 0, 2),
                'avg_retention_impact': round(conversion_metrics.avg_retention_impact or 0, 2),
                'articles_analyzed': conversion_metrics.articles_analyzed or 0
            },
            'retention_analysis': {
                'total_users': retention_metrics.total_users or 0,
                'returning_users': retention_metrics.returning_users or 0,
                'retention_rate': round(
                    ((retention_metrics.returning_users or 0) / 
                     max(retention_metrics.total_users, 1)) * 100, 1
                )
            },
            'content_roi': {
                'avg_cultural_engagement_score': round(content_roi.avg_cultural_engagement or 0, 1),
                'avg_completion_rate': round(content_roi.avg_completion_rate or 0, 1),
                'avg_bookmark_rate': round(content_roi.avg_bookmark_rate or 0, 1),
                'avg_share_rate': round(content_roi.avg_share_rate or 0, 1)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting business impact metrics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve business impact metrics'}), 500

@enhanced_analytics_bp.route('/real-time-metrics', methods=['GET'])
@jwt_required()
def get_real_time_metrics():
    """Get real-time analytics metrics"""
    
    current_user = get_current_user()
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        db_session = get_db_session()
        
        # Last 24 hours metrics
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Active users in last 24 hours
        active_users_24h = db_session.query(
            func.count(UserEngagementMetrics.user_id.distinct())
        ).filter(UserEngagementMetrics.session_start >= yesterday).scalar() or 0
        
        # Articles viewed in last 24 hours
        views_24h = db_session.query(
            func.sum(UserEngagementMetrics.articles_viewed)
        ).filter(UserEngagementMetrics.session_start >= yesterday).scalar() or 0
        
        # Searches in last 24 hours
        searches_24h = db_session.query(
            func.count(SearchAnalytics.id)
        ).filter(SearchAnalytics.search_timestamp >= yesterday).scalar() or 0
        
        # Cultural searches in last 24 hours
        cultural_searches_24h = db_session.query(
            func.count(case([(SearchAnalytics.cultural_keywords_present == True, 1)]))
        ).filter(SearchAnalytics.search_timestamp >= yesterday).scalar() or 0
        
        return jsonify({
            'success': True,
            'last_24_hours': {
                'active_users': active_users_24h,
                'article_views': views_24h,
                'total_searches': searches_24h,
                'cultural_searches': cultural_searches_24h,
                'cultural_search_percentage': round(
                    ((cultural_searches_24h / max(searches_24h, 1)) * 100), 1
                )
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting real-time metrics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve real-time metrics'}), 500
