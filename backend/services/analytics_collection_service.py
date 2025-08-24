"""
Analytics Collection Service for Mingus Article Library

Service for collecting and aggregating analytics data in real-time,
providing comprehensive tracking of user engagement, article performance,
and cultural relevance metrics.
"""

from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
import pandas as pd
import logging
from typing import Optional, Dict, Any, List

from backend.models.article_analytics import (
    UserEngagementMetrics, ArticlePerformanceMetrics, SearchAnalytics,
    CulturalRelevanceAnalytics
)
from backend.models.articles import Article, UserArticleProgress

logger = logging.getLogger(__name__)


class AnalyticsCollectionService:
    """Service for collecting and aggregating analytics data"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def track_article_view(self, user_id: int, article_id: str, reading_time_seconds: int = 0, 
                          device_type: str = None, user_agent: str = None) -> bool:
        """Track article view and update performance metrics"""
        try:
            # Update user engagement metrics
            engagement = self._get_or_create_user_session(user_id, device_type, user_agent)
            engagement.articles_viewed += 1
            
            # Update article performance metrics
            article_perf = self._get_or_create_article_performance(article_id)
            article_perf.total_views += 1
            
            # Check if this is a unique viewer
            existing_view = UserArticleProgress.query.filter_by(
                user_id=user_id, article_id=article_id
            ).first()
            
            if not existing_view:
                article_perf.unique_viewers += 1
            
            # Update reading time
            if reading_time_seconds > 0:
                total_time = (article_perf.average_reading_time * (article_perf.total_views - 1) + reading_time_seconds)
                article_perf.average_reading_time = total_time / article_perf.total_views
            
            # Update last updated timestamp
            article_perf.last_updated = datetime.utcnow()
            article_perf.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Tracked article view: user_id={user_id}, article_id={article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking article view: {str(e)}")
            self.db.rollback()
            return False
    
    def track_article_completion(self, user_id: int, article_id: str, total_reading_time: int) -> bool:
        """Track article completion and calculate completion rates"""
        try:
            engagement = self._get_or_create_user_session(user_id)
            engagement.articles_completed += 1
            
            article_perf = self._get_or_create_article_performance(article_id)
            
            # Calculate new completion rate
            total_completions = UserArticleProgress.query.filter_by(
                article_id=article_id
            ).filter(UserArticleProgress.completed_at.isnot(None)).count()
            
            if article_perf.total_views > 0:
                article_perf.completion_rate = (total_completions / article_perf.total_views) * 100
            
            # Update reading time if provided
            if total_reading_time > 0:
                total_time = (article_perf.average_reading_time * (article_perf.total_views - 1) + total_reading_time)
                article_perf.average_reading_time = total_time / article_perf.total_views
            
            # Update cultural engagement score if article has cultural relevance
            article = Article.query.filter_by(id=article_id).first()
            if article and article.cultural_relevance_score:
                self._update_cultural_engagement_score(article_perf, article.cultural_relevance_score)
            
            article_perf.last_updated = datetime.utcnow()
            article_perf.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Tracked article completion: user_id={user_id}, article_id={article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking article completion: {str(e)}")
            self.db.rollback()
            return False
    
    def track_article_bookmark(self, user_id: int, article_id: str) -> bool:
        """Track article bookmark and update bookmark rates"""
        try:
            engagement = self._get_or_create_user_session(user_id)
            engagement.articles_bookmarked += 1
            
            article_perf = self._get_or_create_article_performance(article_id)
            
            # Calculate bookmark rate
            if article_perf.total_views > 0:
                # Get total bookmarks for this article
                total_bookmarks = UserArticleProgress.query.filter_by(
                    article_id=article_id, bookmarked=True
                ).count()
                article_perf.bookmark_rate = (total_bookmarks / article_perf.total_views) * 100
            
            article_perf.last_updated = datetime.utcnow()
            article_perf.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Tracked article bookmark: user_id={user_id}, article_id={article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking article bookmark: {str(e)}")
            self.db.rollback()
            return False
    
    def track_article_share(self, user_id: int, article_id: str, share_platform: str = None) -> bool:
        """Track article share and update share rates"""
        try:
            engagement = self._get_or_create_user_session(user_id)
            engagement.articles_shared += 1
            
            article_perf = self._get_or_create_article_performance(article_id)
            
            # Calculate share rate
            if article_perf.total_views > 0:
                # Get total shares for this article (you might need to track this separately)
                # For now, we'll increment a counter
                article_perf.share_rate = ((article_perf.share_rate * article_perf.total_views / 100) + 1) / article_perf.total_views * 100
            
            article_perf.last_updated = datetime.utcnow()
            article_perf.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Tracked article share: user_id={user_id}, article_id={article_id}, platform={share_platform}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking article share: {str(e)}")
            self.db.rollback()
            return False
    
    def track_search_query(self, user_id: int, query: str, results_count: int, 
                          clicked_article_id: str = None, selected_phase: str = None,
                          cultural_relevance_filter: int = None) -> bool:
        """Track search queries and success rates"""
        try:
            search_analytics = SearchAnalytics(
                user_id=user_id,
                search_query=query,
                results_count=results_count,
                clicked_article_id=clicked_article_id,
                result_clicked=clicked_article_id is not None,
                query_length=len(query),
                selected_phase=selected_phase,
                cultural_relevance_filter=cultural_relevance_filter,
                cultural_keywords_present=self._contains_cultural_keywords(query),
                query_type=self._categorize_query_type(query)
            )
            
            self.db.add(search_analytics)
            
            # Update user engagement
            engagement = self._get_or_create_user_session(user_id)
            engagement.search_queries_count += 1
            
            # Calculate search success rate
            user_searches = SearchAnalytics.query.filter_by(user_id=user_id).all()
            successful_searches = sum(1 for s in user_searches if s.result_clicked)
            if user_searches:
                engagement.search_success_rate = (successful_searches / len(user_searches)) * 100
            
            self.db.commit()
            logger.info(f"Tracked search query: user_id={user_id}, query='{query}', results={results_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking search query: {str(e)}")
            self.db.rollback()
            return False
    
    def track_assessment_completion(self, user_id: int, be_score_change: int = 0, 
                                  do_score_change: int = 0, have_score_change: int = 0) -> bool:
        """Track assessment completion and score changes"""
        try:
            engagement = self._get_or_create_user_session(user_id)
            engagement.assessment_completed = True
            engagement.be_score_change = be_score_change
            engagement.do_score_change = do_score_change
            engagement.have_score_change = have_score_change
            
            # Calculate content unlocked count based on assessment scores
            # This would depend on your assessment logic
            engagement.content_unlocked_count = self._calculate_unlocked_content_count(
                be_score_change, do_score_change, have_score_change
            )
            
            self.db.commit()
            logger.info(f"Tracked assessment completion: user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking assessment completion: {str(e)}")
            self.db.rollback()
            return False
    
    def calculate_cultural_relevance_metrics(self, user_id: int) -> bool:
        """Calculate and update cultural relevance engagement metrics"""
        try:
            # Get user's article interactions
            user_progress = UserArticleProgress.query.filter_by(user_id=user_id).all()
            
            if not user_progress:
                return True
            
            cultural_analytics = CulturalRelevanceAnalytics.query.filter_by(
                user_id=user_id
            ).first()
            
            if not cultural_analytics:
                cultural_analytics = CulturalRelevanceAnalytics(user_id=user_id)
                self.db.add(cultural_analytics)
            
            # Calculate high relevance content preference
            high_relevance_articles = [
                p for p in user_progress 
                if p.article and p.article.cultural_relevance_score and p.article.cultural_relevance_score >= 8
            ]
            
            if user_progress:
                cultural_analytics.high_relevance_content_preference = (
                    len(high_relevance_articles) / len(user_progress)
                ) * 10  # Scale to 0-10
            
            # Calculate community content engagement
            community_articles = [
                p for p in user_progress
                if p.article and p.article.cultural_keywords and 
                any(keyword in ['African American', 'Black professionals', 'diversity', 'community'] 
                    for keyword in p.article.cultural_keywords)
            ]
            
            if user_progress:
                cultural_analytics.community_content_engagement = (
                    len(community_articles) / len(user_progress)
                ) * 10  # Scale to 0-10
            
            # Calculate cultural search terms frequency
            user_searches = SearchAnalytics.query.filter_by(user_id=user_id).all()
            cultural_searches = sum(1 for s in user_searches if s.cultural_keywords_present)
            cultural_analytics.cultural_search_terms_frequency = cultural_searches
            
            cultural_analytics.last_calculated = datetime.utcnow()
            cultural_analytics.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Calculated cultural relevance metrics: user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error calculating cultural relevance metrics: {str(e)}")
            self.db.rollback()
            return False
    
    def end_user_session(self, user_id: int, session_id: str = None) -> bool:
        """End user session and calculate session metrics"""
        try:
            # Find active session
            if session_id:
                session = UserEngagementMetrics.query.filter_by(
                    user_id=user_id, session_id=session_id
                ).first()
            else:
                session = UserEngagementMetrics.query.filter(
                    and_(
                        UserEngagementMetrics.user_id == user_id,
                        UserEngagementMetrics.session_end.is_(None)
                    )
                ).order_by(desc(UserEngagementMetrics.session_start)).first()
            
            if session:
                session.session_end = datetime.utcnow()
                session.total_session_time = int((session.session_end - session.session_start).total_seconds())
                session.updated_at = datetime.utcnow()
                
                self.db.commit()
                logger.info(f"Ended user session: user_id={user_id}, session_id={session.session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error ending user session: {str(e)}")
            self.db.rollback()
            return False
    
    def _contains_cultural_keywords(self, query: str) -> bool:
        """Check if search query contains cultural keywords"""
        cultural_keywords = [
            'African American', 'Black professional', 'diversity', 'inclusion',
            'cultural', 'community', 'representation', 'systemic', 'equity',
            'Black', 'African', 'minority', 'underrepresented', 'BIPOC'
        ]
        
        query_lower = query.lower()
        return any(keyword.lower() in query_lower for keyword in cultural_keywords)
    
    def _categorize_query_type(self, query: str) -> str:
        """Categorize search query type"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['how', 'what', 'why', 'when', 'where']):
            return 'specific_question'
        elif any(word in query_lower for word in ['author', 'writer', 'by']):
            return 'author'
        elif len(query.split()) <= 2:
            return 'topic'
        else:
            return 'general'
    
    def _calculate_unlocked_content_count(self, be_score: int, do_score: int, have_score: int) -> int:
        """Calculate content unlocked count based on assessment scores"""
        # This is a simplified calculation - adjust based on your assessment logic
        total_score = be_score + do_score + have_score
        if total_score >= 75:
            return 100  # All content unlocked
        elif total_score >= 50:
            return 75   # Most content unlocked
        elif total_score >= 25:
            return 50   # Half content unlocked
        else:
            return 25   # Limited content unlocked
    
    def _update_cultural_engagement_score(self, article_perf: ArticlePerformanceMetrics, 
                                        cultural_score: float) -> None:
        """Update cultural engagement score for article"""
        # Simple average calculation - could be more sophisticated
        if article_perf.cultural_engagement_score == 0:
            article_perf.cultural_engagement_score = cultural_score
        else:
            article_perf.cultural_engagement_score = (
                (article_perf.cultural_engagement_score + cultural_score) / 2
            )
    
    def _get_or_create_user_session(self, user_id: int, device_type: str = None, 
                                   user_agent: str = None) -> UserEngagementMetrics:
        """Get or create user engagement metrics for current session"""
        
        # Try to get recent session (within last hour)
        recent_session = UserEngagementMetrics.query.filter(
            and_(
                UserEngagementMetrics.user_id == user_id,
                UserEngagementMetrics.session_start > datetime.utcnow() - timedelta(hours=1),
                UserEngagementMetrics.session_end.is_(None)
            )
        ).first()
        
        if recent_session:
            return recent_session
        
        # Create new session
        new_session = UserEngagementMetrics(
            user_id=user_id,
            session_id=f"session_{user_id}_{int(datetime.utcnow().timestamp())}",
            device_type=device_type,
            user_agent=user_agent
        )
        self.db.add(new_session)
        return new_session
    
    def _get_or_create_article_performance(self, article_id: str) -> ArticlePerformanceMetrics:
        """Get or create article performance metrics"""
        
        performance = ArticlePerformanceMetrics.query.filter_by(
            article_id=article_id
        ).first()
        
        if not performance:
            performance = ArticlePerformanceMetrics(article_id=article_id)
            self.db.add(performance)
        
        return performance
    
    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """Generate daily analytics report"""
        if not date:
            date = datetime.utcnow().date()
        
        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date, datetime.max.time())
        
        # Get daily metrics
        daily_views = self.db.query(func.sum(ArticlePerformanceMetrics.total_views)).filter(
            and_(
                ArticlePerformanceMetrics.updated_at >= start_date,
                ArticlePerformanceMetrics.updated_at <= end_date
            )
        ).scalar() or 0
        
        daily_searches = self.db.query(func.count(SearchAnalytics.id)).filter(
            and_(
                SearchAnalytics.search_timestamp >= start_date,
                SearchAnalytics.search_timestamp <= end_date
            )
        ).scalar() or 0
        
        active_users = self.db.query(func.count(func.distinct(UserEngagementMetrics.user_id))).filter(
            and_(
                UserEngagementMetrics.session_start >= start_date,
                UserEngagementMetrics.session_start <= end_date
            )
        ).scalar() or 0
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'total_views': daily_views,
            'total_searches': daily_searches,
            'active_users': active_users,
            'generated_at': datetime.utcnow().isoformat()
        }
