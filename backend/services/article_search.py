"""
Article Search Service for Mingus Application
Advanced search engine with personalization and cultural relevance
"""

from sqlalchemy import and_, or_, desc, func, text
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from backend.models.articles import (
    Article, UserArticleRead, UserArticleBookmark, UserArticleRating,
    UserAssessmentScores, ArticleRecommendation, ArticleAnalytics
)
from backend.models.user import User

logger = logging.getLogger(__name__)

class ArticleSearchService:
    """Advanced search service with personalization and access control"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def search(self, query: str = None, filters: Dict = None, user_id: int = None, 
               page: int = 1, per_page: int = 20) -> Dict:
        """
        Advanced search with personalization and cultural relevance
        
        Args:
            query: Search query string
            filters: Dictionary of filters (phase, difficulty, topics, etc.)
            user_id: User ID for personalization and access control
            page: Page number for pagination
            per_page: Items per page
            
        Returns:
            Dictionary with articles, pagination info, and metadata
        """
        try:
            base_query = self.db.query(Article).filter(Article.is_active == True)
            
            # Full-text search with PostgreSQL
            if query and query.strip():
                search_query = func.plainto_tsquery('english', query.strip())
                base_query = base_query.filter(
                    Article.search_vector.match(search_query)
                ).order_by(
                    desc(func.ts_rank(Article.search_vector, search_query))
                )
            
            # Apply filters
            if filters:
                base_query = self._apply_filters(base_query, filters)
            
            # Personalization based on user profile
            if user_id:
                base_query = self._add_personalization(base_query, user_id)
            
            # Apply access control (only show articles user can access)
            if user_id:
                base_query = self._apply_access_control(base_query, user_id)
            
            # Get total count before pagination
            total_count = base_query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            articles = base_query.offset(offset).limit(per_page).all()
            
            # Convert to dictionaries
            article_list = []
            for article in articles:
                article_dict = article.to_dict()
                
                # Add user-specific data if available
                if user_id:
                    article_dict.update(self._get_user_specific_data(article.id, user_id))
                
                article_list.append(article_dict)
            
            return {
                'articles': article_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                },
                'metadata': {
                    'query': query,
                    'filters_applied': filters,
                    'user_id': user_id
                }
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise
    
    def _apply_filters(self, query, filters: Dict):
        """Apply search filters to the query"""
        if filters.get('phase'):
            query = query.filter(Article.primary_phase == filters['phase'])
        
        if filters.get('difficulty'):
            query = query.filter(Article.difficulty_level == filters['difficulty'])
        
        if filters.get('cultural_relevance_min'):
            query = query.filter(
                Article.demographic_relevance >= filters['cultural_relevance_min']
            )
        
        if filters.get('reading_time_max'):
            query = query.filter(
                Article.reading_time_minutes <= filters['reading_time_max']
            )
        
        if filters.get('topics'):
            # Search within JSON array of topics
            for topic in filters['topics']:
                query = query.filter(
                    Article.key_topics.contains([topic])
                )
        
        if filters.get('income_range'):
            query = query.filter(Article.target_income_range == filters['income_range'])
        
        if filters.get('career_stage'):
            query = query.filter(Article.career_stage == filters['career_stage'])
        
        if filters.get('is_featured'):
            query = query.filter(Article.is_featured == filters['is_featured'])
        
        if filters.get('date_from'):
            query = query.filter(Article.publish_date >= filters['date_from'])
        
        if filters.get('date_to'):
            query = query.filter(Article.publish_date <= filters['date_to'])
        
        return query
    
    def _add_personalization(self, query, user_id: int):
        """Add personalized ranking based on user profile and reading history"""
        try:
            # Get user's reading history
            user_reads = self.db.query(UserArticleRead).filter_by(user_id=user_id).all()
            read_article_ids = [read.article_id for read in user_reads]
            
            # Get user's bookmarks
            user_bookmarks = self.db.query(UserArticleBookmark).filter_by(user_id=user_id).all()
            bookmarked_article_ids = [bookmark.article_id for bookmark in user_bookmarks]
            
            # Boost articles matching user's reading patterns
            if read_article_ids:
                # Boost articles in phases user has read before
                read_phases = self.db.query(Article.primary_phase).filter(
                    Article.id.in_(read_article_ids)
                ).distinct().all()
                
                if read_phases:
                    phase_conditions = [Article.primary_phase == phase[0] for phase in read_phases]
                    query = query.order_by(
                        desc(or_(*phase_conditions)),
                        desc(Article.demographic_relevance)
                    )
            
            # Boost culturally relevant content
            query = query.order_by(desc(Article.demographic_relevance))
            
            return query
            
        except Exception as e:
            logger.error(f"Personalization error: {str(e)}")
            return query
    
    def _apply_access_control(self, query, user_id: int):
        """Filter articles based on user's assessment scores"""
        try:
            user_assessment = self.db.query(UserAssessmentScores).filter_by(user_id=user_id).first()
            
            if not user_assessment:
                # New users can only access Beginner content
                return query.filter(Article.difficulty_level == 'Beginner')
            
            # Build access control conditions
            access_conditions = []
            
            # Beginner content always accessible
            access_conditions.append(Article.difficulty_level == 'Beginner')
            
            # Intermediate content based on assessment scores
            if user_assessment.be_score >= 60:
                access_conditions.append(
                    and_(Article.primary_phase == 'BE', Article.difficulty_level == 'Intermediate')
                )
            
            if user_assessment.do_score >= 60:
                access_conditions.append(
                    and_(Article.primary_phase == 'DO', Article.difficulty_level == 'Intermediate')
                )
            
            if user_assessment.have_score >= 60:
                access_conditions.append(
                    and_(Article.primary_phase == 'HAVE', Article.difficulty_level == 'Intermediate')
                )
            
            # Advanced content based on higher thresholds
            if user_assessment.be_score >= 80:
                access_conditions.append(
                    and_(Article.primary_phase == 'BE', Article.difficulty_level == 'Advanced')
                )
            
            if user_assessment.do_score >= 80:
                access_conditions.append(
                    and_(Article.primary_phase == 'DO', Article.difficulty_level == 'Advanced')
                )
            
            if user_assessment.have_score >= 80:
                access_conditions.append(
                    and_(Article.primary_phase == 'HAVE', Article.difficulty_level == 'Advanced')
                )
            
            return query.filter(or_(*access_conditions))
            
        except Exception as e:
            logger.error(f"Access control error: {str(e)}")
            # Default to beginner content only
            return query.filter(Article.difficulty_level == 'Beginner')
    
    def _get_user_specific_data(self, article_id, user_id: int) -> Dict:
        """Get user-specific data for an article"""
        try:
            data = {}
            
            # Check if user has read this article
            user_read = self.db.query(UserArticleRead).filter_by(
                user_id=user_id, article_id=article_id
            ).first()
            
            if user_read:
                data['user_read'] = {
                    'started_at': user_read.started_at.isoformat() if user_read.started_at else None,
                    'completed_at': user_read.completed_at.isoformat() if user_read.completed_at else None,
                    'time_spent_seconds': user_read.time_spent_seconds,
                    'scroll_depth_percentage': user_read.scroll_depth_percentage,
                    'engagement_score': user_read.engagement_score
                }
            
            # Check if user has bookmarked this article
            user_bookmark = self.db.query(UserArticleBookmark).filter_by(
                user_id=user_id, article_id=article_id
            ).first()
            
            if user_bookmark:
                data['user_bookmark'] = {
                    'notes': user_bookmark.notes,
                    'tags': user_bookmark.tags,
                    'priority': user_bookmark.priority,
                    'folder_name': user_bookmark.folder_name,
                    'is_archived': user_bookmark.is_archived
                }
            
            # Check if user has rated this article
            user_rating = self.db.query(UserArticleRating).filter_by(
                user_id=user_id, article_id=article_id
            ).first()
            
            if user_rating:
                data['user_rating'] = {
                    'overall_rating': user_rating.overall_rating,
                    'helpfulness_rating': user_rating.helpfulness_rating,
                    'clarity_rating': user_rating.clarity_rating,
                    'actionability_rating': user_rating.actionability_rating,
                    'cultural_relevance_rating': user_rating.cultural_relevance_rating,
                    'review_text': user_rating.review_text,
                    'review_title': user_rating.review_title
                }
            
            return data
            
        except Exception as e:
            logger.error(f"Get user specific data error: {str(e)}")
            return {}
    
    def get_recommendations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get personalized article recommendations for a user"""
        try:
            # Use the enhanced recommendation engine
            recommendation_engine = ArticleRecommendationEngine(self.db)
            recommendations = recommendation_engine.get_personalized_recommendations(user_id, limit)
            
            # Convert to dictionaries and add user-specific data
            recommendation_list = []
            for article in recommendations:
                article_dict = article.to_dict()
                article_dict.update(self._get_user_specific_data(article.id, user_id))
                recommendation_list.append(article_dict)
            
            return recommendation_list
            
        except Exception as e:
            logger.error(f"Get recommendations error: {str(e)}")
            return []

class ArticleRecommendationEngine:
    """Advanced recommendation engine with multiple recommendation strategies"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_personalized_recommendations(self, user_id, limit=10):
        """Generate personalized article recommendations using multiple strategies"""
        
        try:
            # Get user data
            user_profile = self._get_user_profile(user_id)
            user_assessment = self.db.query(UserAssessmentScores).filter_by(user_id=user_id).first()
            reading_history = self._get_user_reading_history(user_id)
            
            recommendations = []
            
            # 1. Next step in Be-Do-Have progression
            progression_recs = self._get_progression_recommendations(user_assessment, reading_history)
            recommendations.extend(progression_recs[:4])
            
            # 2. Cultural relevance matches
            cultural_recs = self._get_cultural_recommendations(user_profile, user_id)
            recommendations.extend(cultural_recs[:3])
            
            # 3. Similar to recently read articles
            similar_recs = self._get_similar_article_recommendations(reading_history)
            recommendations.extend(similar_recs[:3])
            
            # 4. Featured articles for user's level
            featured_recs = self._get_featured_recommendations(user_assessment)
            recommendations.extend(featured_recs[:2])
            
            # Remove duplicates and apply access control
            unique_recs = self._deduplicate_and_filter_access(recommendations, user_id)
            
            return unique_recs[:limit]
            
        except Exception as e:
            logger.error(f"Get personalized recommendations error: {str(e)}")
            return []
    
    def _get_user_profile(self, user_id):
        """Get user profile information"""
        try:
            # Import UserProfile if available, otherwise return None
            from backend.models.user_profile import UserProfile
            return self.db.query(UserProfile).filter_by(user_id=user_id).first()
        except ImportError:
            return None
    
    def _get_user_reading_history(self, user_id):
        """Get user's reading history"""
        return self.db.query(UserArticleRead).filter_by(user_id=user_id).order_by(
            desc(UserArticleRead.started_at)
        ).limit(20).all()
    
    def _get_progression_recommendations(self, user_assessment, reading_history):
        """Recommend next steps in user's learning journey"""
        
        if not user_assessment:
            # New users start with BE Beginner
            return self.db.query(Article).filter(
                Article.primary_phase == 'BE', 
                Article.difficulty_level == 'Beginner',
                Article.is_active == True
            ).order_by(
                desc(Article.demographic_relevance),
                desc(Article.is_featured)
            ).limit(5).all()
        
        # Identify user's strongest and weakest areas
        scores = {
            'BE': user_assessment.be_score,
            'DO': user_assessment.do_score,
            'HAVE': user_assessment.have_score
        }
        
        # Get read article IDs to avoid duplicates
        read_article_ids = [read.article_id for read in reading_history]
        
        # Recommend articles to strengthen weakest areas
        weakest_phase = min(scores, key=scores.get)
        
        return self.db.query(Article).filter(
            Article.primary_phase == weakest_phase,
            Article.is_active == True,
            ~Article.id.in_(read_article_ids) if read_article_ids else True
        ).order_by(
            desc(Article.professional_development_value),
            desc(Article.demographic_relevance),
            Article.recommended_reading_order
        ).limit(5).all()
    
    def _get_cultural_recommendations(self, user_profile, user_id):
        """Recommend culturally relevant articles"""
        
        # Get user's reading history to avoid duplicates
        reading_history = self._get_user_reading_history(user_id)
        read_article_ids = [read.article_id for read in reading_history]
        
        return self.db.query(Article).filter(
            Article.demographic_relevance >= 8,
            Article.cultural_sensitivity >= 7,
            Article.is_active == True,
            ~Article.id.in_(read_article_ids) if read_article_ids else True
        ).order_by(
            desc(Article.demographic_relevance),
            desc(Article.cultural_sensitivity)
        ).limit(5).all()
    
    def _get_similar_article_recommendations(self, reading_history):
        """Recommend articles similar to recently read articles"""
        
        if not reading_history:
            return []
        
        # Get topics from recently read articles
        recent_articles = []
        for read in reading_history[:5]:  # Last 5 reads
            article = self.db.query(Article).filter_by(id=read.article_id).first()
            if article:
                recent_articles.append(article)
        
        if not recent_articles:
            return []
        
        # Collect topics from recent articles
        all_topics = set()
        for article in recent_articles:
            if article.key_topics:
                all_topics.update(article.key_topics)
        
        if not all_topics:
            return []
        
        # Find articles with similar topics
        read_article_ids = [read.article_id for read in reading_history]
        
        similar_articles = self.db.query(Article).filter(
            Article.is_active == True,
            ~Article.id.in_(read_article_ids) if read_article_ids else True
        ).filter(
            or_(*[Article.key_topics.contains([topic]) for topic in list(all_topics)[:3]])
        ).order_by(
            desc(Article.demographic_relevance),
            desc(Article.is_featured)
        ).limit(5).all()
        
        return similar_articles
    
    def _get_featured_recommendations(self, user_assessment):
        """Get featured articles appropriate for user's level"""
        
        if not user_assessment:
            # For new users, recommend featured beginner articles
            return self.db.query(Article).filter(
                Article.is_featured == True,
                Article.difficulty_level == 'Beginner',
                Article.is_active == True
            ).order_by(
                desc(Article.demographic_relevance)
            ).limit(3).all()
        
        # Get user's level for each phase
        levels = {
            'BE': user_assessment.be_level,
            'DO': user_assessment.do_level,
            'HAVE': user_assessment.have_level
        }
        
        # Find the highest level the user has achieved
        level_order = ['Beginner', 'Intermediate', 'Advanced']
        max_level = 'Beginner'
        for level in levels.values():
            if level_order.index(level) > level_order.index(max_level):
                max_level = level
        
        # Recommend featured articles at or below user's level
        difficulty_conditions = []
        if max_level == 'Advanced':
            difficulty_conditions = ['Beginner', 'Intermediate', 'Advanced']
        elif max_level == 'Intermediate':
            difficulty_conditions = ['Beginner', 'Intermediate']
        else:
            difficulty_conditions = ['Beginner']
        
        return self.db.query(Article).filter(
            Article.is_featured == True,
            Article.difficulty_level.in_(difficulty_conditions),
            Article.is_active == True
        ).order_by(
            desc(Article.demographic_relevance),
            Article.recommended_reading_order
        ).limit(3).all()
    
    def _deduplicate_and_filter_access(self, recommendations, user_id):
        """Remove duplicates and apply access control"""
        
        seen_ids = set()
        unique_recommendations = []
        
        for article in recommendations:
            if article.id not in seen_ids:
                # Check if user can access this article
                if article.can_user_access(user_id, self.db):
                    unique_recommendations.append(article)
                    seen_ids.add(article.id)
        
        return unique_recommendations
    
    def get_recommendation_explanation(self, article_id, user_id):
        """Get explanation for why an article was recommended"""
        
        try:
            user_assessment = self.db.query(UserAssessmentScores).filter_by(user_id=user_id).first()
            article = self.db.query(Article).filter_by(id=article_id).first()
            
            if not article:
                return "Article not found"
            
            explanations = []
            
            # Check if it's a progression recommendation
            if user_assessment:
                scores = {
                    'BE': user_assessment.be_score,
                    'DO': user_assessment.do_score,
                    'HAVE': user_assessment.have_score
                }
                weakest_phase = min(scores, key=scores.get)
                
                if article.primary_phase == weakest_phase:
                    explanations.append(f"Recommended to strengthen your {weakest_phase} skills (your current score: {scores[weakest_phase]})")
            
            # Check if it's culturally relevant
            if article.demographic_relevance >= 8:
                explanations.append("Highly relevant to your demographic and cultural background")
            
            # Check if it's featured
            if article.is_featured:
                explanations.append("Featured content selected by our experts")
            
            # Check if it's similar to recently read
            reading_history = self._get_user_reading_history(user_id)
            if reading_history:
                recent_topics = set()
                for read in reading_history[:3]:
                    recent_article = self.db.query(Article).filter_by(id=read.article_id).first()
                    if recent_article and recent_article.key_topics:
                        recent_topics.update(recent_article.key_topics)
                
                if article.key_topics and any(topic in recent_topics for topic in article.key_topics):
                    explanations.append("Similar to topics you've been reading about")
            
            # Check if it's appropriate for user's level
            if user_assessment:
                user_level = user_assessment.get_level_for_phase(article.primary_phase)
                if article.difficulty_level == user_level:
                    explanations.append(f"Perfect for your current {user_level} level in {article.primary_phase}")
                elif article.difficulty_level == 'Beginner':
                    explanations.append("Great starting point for building foundational knowledge")
            
            return " | ".join(explanations) if explanations else "Recommended based on your learning profile"
            
        except Exception as e:
            logger.error(f"Get recommendation explanation error: {str(e)}")
            return "Recommended for your learning journey"
    
    def get_trending_articles(self, user_id: int = None, limit: int = 10) -> List[Dict]:
        """Get trending articles based on engagement metrics"""
        try:
            # Get articles with highest engagement in the last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            trending_query = self.db.query(Article).join(ArticleAnalytics).filter(
                Article.is_active == True,
                ArticleAnalytics.total_views > 0
            ).order_by(
                desc(ArticleAnalytics.total_views),
                desc(ArticleAnalytics.average_rating)
            ).limit(limit)
            
            # Apply access control if user_id provided
            if user_id:
                trending_query = self._apply_access_control(trending_query, user_id)
            
            trending_articles = trending_query.all()
            
            # Convert to dictionaries
            trending_list = []
            for article in trending_articles:
                article_dict = article.to_dict()
                if user_id:
                    article_dict.update(self._get_user_specific_data(article.id, user_id))
                trending_list.append(article_dict)
            
            return trending_list
            
        except Exception as e:
            logger.error(f"Get trending articles error: {str(e)}")
            return []
    
    def get_featured_articles(self, user_id: int = None, limit: int = 10) -> List[Dict]:
        """Get admin-featured articles"""
        try:
            featured_query = self.db.query(Article).filter(
                Article.is_featured == True,
                Article.is_active == True
            ).order_by(
                desc(Article.demographic_relevance),
                Article.recommended_reading_order
            ).limit(limit)
            
            # Apply access control if user_id provided
            if user_id:
                featured_query = self._apply_access_control(featured_query, user_id)
            
            featured_articles = featured_query.all()
            
            # Convert to dictionaries
            featured_list = []
            for article in featured_articles:
                article_dict = article.to_dict()
                if user_id:
                    article_dict.update(self._get_user_specific_data(article.id, user_id))
                featured_list.append(article_dict)
            
            return featured_list
            
        except Exception as e:
            logger.error(f"Get featured articles error: {str(e)}")
            return []
    
    def get_articles_by_phase(self, phase: str, user_id: int = None, 
                            page: int = 1, per_page: int = 20) -> Dict:
        """Get articles by Be-Do-Have phase"""
        try:
            base_query = self.db.query(Article).filter(
                Article.primary_phase == phase,
                Article.is_active == True
            ).order_by(
                Article.recommended_reading_order,
                desc(Article.demographic_relevance)
            )
            
            # Apply access control if user_id provided
            if user_id:
                base_query = self._apply_access_control(base_query, user_id)
            
            # Get total count
            total_count = base_query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            articles = base_query.offset(offset).limit(per_page).all()
            
            # Convert to dictionaries
            article_list = []
            for article in articles:
                article_dict = article.to_dict()
                if user_id:
                    article_dict.update(self._get_user_specific_data(article.id, user_id))
                article_list.append(article_dict)
            
            return {
                'articles': article_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                },
                'metadata': {
                    'phase': phase,
                    'user_id': user_id
                }
            }
            
        except Exception as e:
            logger.error(f"Get articles by phase error: {str(e)}")
            return {'articles': [], 'pagination': {}, 'metadata': {}}
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search term autocomplete suggestions"""
        try:
            if not query or len(query) < 2:
                return []
            
            # Search in titles and key topics
            suggestions = self.db.query(Article.title).filter(
                Article.is_active == True,
                Article.title.ilike(f'%{query}%')
            ).limit(limit).all()
            
            # Also search in key topics
            topic_suggestions = self.db.query(Article.key_topics).filter(
                Article.is_active == True,
                Article.key_topics.isnot(None)
            ).limit(limit).all()
            
            # Combine and deduplicate suggestions
            all_suggestions = []
            
            for suggestion in suggestions:
                if suggestion[0]:
                    all_suggestions.append(suggestion[0])
            
            for topic_suggestion in topic_suggestions:
                if topic_suggestion[0]:
                    for topic in topic_suggestion[0]:
                        if query.lower() in topic.lower() and topic not in all_suggestions:
                            all_suggestions.append(topic)
            
            return all_suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Get search suggestions error: {str(e)}")
            return []
    
    def get_available_filters(self) -> Dict:
        """Get available filter options"""
        try:
            filters = {}
            
            # Get all phases
            phases = self.db.query(Article.primary_phase).filter(
                Article.is_active == True
            ).distinct().all()
            filters['phases'] = [phase[0] for phase in phases]
            
            # Get all difficulty levels
            difficulties = self.db.query(Article.difficulty_level).filter(
                Article.is_active == True
            ).distinct().all()
            filters['difficulty_levels'] = [diff[0] for diff in difficulties]
            
            # Get all topics
            topics = self.db.query(Article.key_topics).filter(
                Article.is_active == True,
                Article.key_topics.isnot(None)
            ).all()
            
            all_topics = set()
            for topic_list in topics:
                if topic_list[0]:
                    all_topics.update(topic_list[0])
            
            filters['topics'] = sorted(list(all_topics))
            
            # Get income ranges
            income_ranges = self.db.query(Article.target_income_range).filter(
                Article.is_active == True,
                Article.target_income_range.isnot(None)
            ).distinct().all()
            filters['income_ranges'] = [income[0] for income in income_ranges if income[0]]
            
            # Get career stages
            career_stages = self.db.query(Article.career_stage).filter(
                Article.is_active == True,
                Article.career_stage.isnot(None)
            ).distinct().all()
            filters['career_stages'] = [stage[0] for stage in career_stages if stage[0]]
            
            return filters
            
        except Exception as e:
            logger.error(f"Get available filters error: {str(e)}")
            return {}
