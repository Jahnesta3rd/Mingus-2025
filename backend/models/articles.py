"""
Article Library Models for Mingus Application
SQLAlchemy models for managing the classified article library with Be-Do-Have framework
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, Date, 
    ForeignKey, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from .base import Base

# For SQLite compatibility, we'll use String instead of TSVECTOR
# In production with PostgreSQL, this would be TSVECTOR for full-text search
try:
    from sqlalchemy.dialects.postgresql import TSVECTOR as TSVectorType
except ImportError:
    # Fallback for SQLite
    TSVectorType = String

class Article(Base):
    """Core Article model for the Mingus article library"""
    __tablename__ = 'articles'
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(500), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    
    # Content fields
    content = Column(Text, nullable=False)
    content_preview = Column(String(500))  # First 500 chars for previews
    meta_description = Column(Text)
    author = Column(String(200))
    publish_date = Column(Date, index=True)
    word_count = Column(Integer, default=0)
    reading_time_minutes = Column(Integer, default=0)
    
    # Be-Do-Have Classification
    primary_phase = Column(
        Enum('BE', 'DO', 'HAVE', name='phase_enum'), 
        nullable=False, 
        index=True
    )
    difficulty_level = Column(
        Enum('Beginner', 'Intermediate', 'Advanced', name='difficulty_enum'), 
        nullable=False, 
        index=True
    )
    confidence_score = Column(Float, default=0.0)  # AI classification confidence
    
    # Scoring and relevance
    demographic_relevance = Column(Integer, default=0, index=True)  # 1-10 scale
    cultural_sensitivity = Column(Integer, default=0)  # 1-10 scale
    income_impact_potential = Column(Integer, default=0)  # 1-10 scale
    actionability_score = Column(Integer, default=0)  # 1-10 scale
    professional_development_value = Column(Integer, default=0)  # 1-10 scale
    
    # Content organization
    key_topics = Column(JSON)  # Array of topic strings
    learning_objectives = Column(JSON)  # Array of learning goal strings
    prerequisites = Column(JSON)  # Array of prerequisite strings
    cultural_relevance_keywords = Column(JSON)  # Cultural keyword matches
    
    # Targeting and personalization
    target_income_range = Column(String(50))  # "$40K-$60K", "$60K-$80K", etc.
    career_stage = Column(String(50))  # "Early career", "Mid-career", etc.
    recommended_reading_order = Column(Integer, default=50)  # 1-100 progression
    
    # Search and discovery
    search_vector = Column(TSVectorType(), index=True)  # PostgreSQL full-text search
    domain = Column(String(100), nullable=False, index=True)
    source_quality_score = Column(Float, default=0.0)
    
    # Administrative
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    admin_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_reads = relationship("UserArticleRead", back_populates="article")
    user_bookmarks = relationship("UserArticleBookmark", back_populates="article")
    user_ratings = relationship("UserArticleRating", back_populates="article")
    user_progress = relationship("UserArticleProgress", back_populates="article", foreign_keys="UserArticleProgress.article_id")
    
    def __repr__(self):
        return f'<Article {self.title[:50]}...>'
    
    def to_dict(self):
        """Convert article to dictionary"""
        return {
            'id': str(self.id),
            'url': self.url,
            'title': self.title,
            'content_preview': self.content_preview,
            'meta_description': self.meta_description,
            'author': self.author,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'word_count': self.word_count,
            'reading_time_minutes': self.reading_time_minutes,
            'primary_phase': self.primary_phase,
            'difficulty_level': self.difficulty_level,
            'confidence_score': self.confidence_score,
            'demographic_relevance': self.demographic_relevance,
            'cultural_sensitivity': self.cultural_sensitivity,
            'income_impact_potential': self.income_impact_potential,
            'actionability_score': self.actionability_score,
            'professional_development_value': self.professional_development_value,
            'key_topics': self.key_topics,
            'learning_objectives': self.learning_objectives,
            'prerequisites': self.prerequisites,
            'cultural_relevance_keywords': self.cultural_relevance_keywords,
            'target_income_range': self.target_income_range,
            'career_stage': self.career_stage,
            'recommended_reading_order': self.recommended_reading_order,
            'domain': self.domain,
            'source_quality_score': self.source_quality_score,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def can_user_access(self, user_id, db_session=None):
        """
        Check if a user can access this article based on their assessment scores
        
        Gatekeeping rules:
        - Beginner articles: All users can access
        - Intermediate articles: User needs Intermediate level in the article's phase
        - Advanced articles: User needs Advanced level in the article's phase
        
        Args:
            user_id: The user's ID
            db_session: SQLAlchemy session (optional, will create if not provided)
            
        Returns:
            bool: True if user can access, False otherwise
        """
        from sqlalchemy.orm import Session
        
        # If no session provided, create one
        if db_session is None:
            from backend.models import SessionLocal
            db_session = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        try:
            # Get user's assessment scores
            assessment = db_session.query(UserAssessmentScores).filter_by(user_id=user_id).first()
            
            # If no assessment, only allow Beginner articles
            if not assessment:
                return self.difficulty_level == 'Beginner'
            
            # Get user's level for this article's phase
            user_level = assessment.get_level_for_phase(self.primary_phase)
            
            # Gatekeeping logic
            if self.difficulty_level == 'Beginner':
                return True  # All users can access Beginner articles
            
            elif self.difficulty_level == 'Intermediate':
                # User needs at least Intermediate level in this phase
                return user_level in ['Intermediate', 'Advanced']
            
            elif self.difficulty_level == 'Advanced':
                # User needs Advanced level in this phase
                return user_level == 'Advanced'
            
            return False  # Default to no access
            
        finally:
            if should_close:
                db_session.close()


class UserArticleRead(Base):
    """Track user article reading history and engagement"""
    __tablename__ = 'user_article_reads'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), nullable=False, index=True)
    
    # Reading metrics
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)  # NULL if not completed
    time_spent_seconds = Column(Integer, default=0)
    scroll_depth_percentage = Column(Float, default=0.0)  # 0-100%
    engagement_score = Column(Float, default=0.0)  # Calculated engagement metric
    
    # User feedback
    found_helpful = Column(Boolean)  # NULL = no feedback, True/False = user feedback
    would_recommend = Column(Boolean)
    difficulty_rating = Column(Integer)  # 1-5 scale, user's perception
    relevance_rating = Column(Integer)  # 1-5 scale, user's perception
    
    # Context
    reading_session_id = Column(String(100))  # Group related reads
    source_page = Column(String(200))  # Where they came from
    device_type = Column(String(50))  # mobile, desktop, tablet
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="article_reads")
    article = relationship("Article", back_populates="user_reads")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'article_id', name='uq_user_article_read'),
    )
    
    def __repr__(self):
        return f'<UserArticleRead user_id={self.user_id} article_id={self.article_id}>'


class UserArticleBookmark(Base):
    """Track user bookmarks and saved articles"""
    __tablename__ = 'user_article_bookmarks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), nullable=False, index=True)
    
    # Bookmark metadata
    notes = Column(Text)  # User's personal notes about the article
    tags = Column(JSON)  # User-defined tags for organization
    priority = Column(Integer, default=1)  # 1-5 scale, user's priority rating
    
    # Organization
    folder_name = Column(String(100), default='General')  # User's folder organization
    is_archived = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="article_bookmarks")
    article = relationship("Article", back_populates="user_bookmarks")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'article_id', name='uq_user_article_bookmark'),
    )
    
    def __repr__(self):
        return f'<UserArticleBookmark user_id={self.user_id} article_id={self.article_id}>'


class UserArticleRating(Base):
    """Track user ratings and reviews of articles"""
    __tablename__ = 'user_article_ratings'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), nullable=False, index=True)
    
    # Rating metrics (1-5 scale)
    overall_rating = Column(Integer, nullable=False)  # 1-5 stars
    helpfulness_rating = Column(Integer)  # How helpful was the content
    clarity_rating = Column(Integer)  # How clear was the writing
    actionability_rating = Column(Integer)  # How actionable was the advice
    cultural_relevance_rating = Column(Integer)  # How culturally relevant
    
    # Review content
    review_text = Column(Text)  # User's written review
    review_title = Column(String(200))  # Brief review title
    
    # Moderation
    is_approved = Column(Boolean, default=True)  # For moderation
    is_anonymous = Column(Boolean, default=False)  # User choice
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="article_ratings")
    article = relationship("Article", back_populates="user_ratings")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'article_id', name='uq_user_article_rating'),
    )
    
    def __repr__(self):
        return f'<UserArticleRating user_id={self.user_id} article_id={self.article_id}>'


class UserArticleProgress(Base):
    """Track user progress through the Be-Do-Have journey"""
    __tablename__ = 'user_article_progress'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), nullable=False, index=True)
    
    # Progress tracking
    current_phase = Column(
        Enum('BE', 'DO', 'HAVE', name='user_phase_enum'), 
        nullable=False, 
        index=True
    )
    phase_progress = Column(Float, default=0.0)  # 0-100% completion in current phase
    total_progress = Column(Float, default=0.0)  # 0-100% overall journey progress
    
    # Learning outcomes
    learning_objectives_achieved = Column(JSON)  # Array of achieved objectives
    skills_developed = Column(JSON)  # Array of skills gained
    actions_taken = Column(JSON)  # Array of actions completed based on article
    
    # Assessment
    self_assessment_score = Column(Integer)  # 1-10 user's self-assessment
    confidence_increase = Column(Float)  # Change in confidence level
    knowledge_retention_score = Column(Float)  # 0-100% retention
    
    # Next steps
    next_recommended_article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'))
    next_phase_target = Column(
        Enum('BE', 'DO', 'HAVE', name='next_phase_enum')
    )
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="article_progress")
    article = relationship("Article", back_populates="user_progress", foreign_keys=[article_id])
    next_article = relationship("Article", foreign_keys=[next_recommended_article_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'article_id', name='uq_user_article_progress'),
    )
    
    def __repr__(self):
        return f'<UserArticleProgress user_id={self.user_id} article_id={self.article_id}>'


class ArticleRecommendation(Base):
    """Track article recommendations and personalization"""
    __tablename__ = 'article_recommendations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), nullable=False, index=True)
    
    # Recommendation metadata
    recommendation_score = Column(Float, nullable=False)  # 0-1 confidence score
    recommendation_reason = Column(String(200))  # Why this article was recommended
    recommendation_source = Column(String(100))  # 'ai', 'collaborative', 'content_based'
    
    # Personalization factors
    user_income_match = Column(Float)  # 0-1 match with user's income level
    user_career_match = Column(Float)  # 0-1 match with user's career stage
    user_goals_match = Column(Float)  # 0-1 match with user's financial goals
    cultural_relevance_match = Column(Float)  # 0-1 cultural relevance score
    
    # Recommendation status
    is_displayed = Column(Boolean, default=False)  # Whether shown to user
    is_clicked = Column(Boolean, default=False)  # Whether user clicked
    is_read = Column(Boolean, default=False)  # Whether user read the article
    display_position = Column(Integer)  # Position in recommendation list
    
    # Timing
    recommended_at = Column(DateTime, default=datetime.utcnow, index=True)
    displayed_at = Column(DateTime)
    clicked_at = Column(DateTime)
    read_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="article_recommendations")
    article = relationship("Article")
    
    def __repr__(self):
        return f'<ArticleRecommendation user_id={self.user_id} article_id={self.article_id}>'


class ArticleAnalytics(Base):
    """Track aggregate analytics for articles"""
    __tablename__ = 'article_analytics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'), nullable=False, unique=True, index=True)
    
    # Engagement metrics
    total_views = Column(Integer, default=0, index=True)
    total_reads = Column(Integer, default=0, index=True)
    total_bookmarks = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)
    
    # Completion metrics
    completion_rate = Column(Float, default=0.0)  # % of readers who finish
    average_time_spent = Column(Float, default=0.0)  # Average seconds spent
    average_scroll_depth = Column(Float, default=0.0)  # Average scroll depth %
    
    # Rating metrics
    average_rating = Column(Float, default=0.0, index=True)
    total_ratings = Column(Integer, default=0)
    helpfulness_score = Column(Float, default=0.0)
    clarity_score = Column(Float, default=0.0)
    actionability_score = Column(Float, default=0.0)
    cultural_relevance_score = Column(Float, default=0.0)
    
    # Recommendation metrics
    recommendation_click_rate = Column(Float, default=0.0)
    recommendation_read_rate = Column(Float, default=0.0)
    
    # Demographic breakdown
    demographic_breakdown = Column(JSON)  # Breakdown by user demographics
    phase_effectiveness = Column(JSON)  # Effectiveness by Be-Do-Have phase
    
    # Time-based metrics
    daily_views = Column(JSON)  # Last 30 days of daily views
    weekly_engagement = Column(JSON)  # Last 12 weeks of engagement
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    article = relationship("Article")
    
    def __repr__(self):
        return f'<ArticleAnalytics article_id={self.article_id}>'


class UserAssessmentScores(Base):
    """Track user assessment scores for Be-Do-Have gatekeeping"""
    __tablename__ = 'user_assessment_scores'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Be-Do-Have assessment scores (0-100)
    be_score = Column(Integer, default=0)  # Identity/mindset score
    do_score = Column(Integer, default=0)  # Skills/action score
    have_score = Column(Integer, default=0)  # Results/wealth score
    
    # Assessment metadata
    assessment_date = Column(DateTime, default=datetime.utcnow, index=True)
    assessment_version = Column(String(50), default='1.0')  # Assessment version
    total_questions = Column(Integer, default=0)
    completion_time_minutes = Column(Integer, default=0)
    
    # Score interpretations
    be_level = Column(String(20), default='Beginner')  # Beginner, Intermediate, Advanced
    do_level = Column(String(20), default='Beginner')
    have_level = Column(String(20), default='Beginner')
    overall_readiness_level = Column(String(20), default='Beginner')  # Overall readiness level
    
    # Confidence and validity
    confidence_score = Column(Float, default=0.0)  # 0-1 confidence in assessment
    is_valid = Column(Boolean, default=True)  # Whether assessment is still valid
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="assessment_scores")
    
    def __repr__(self):
        return f'<UserAssessmentScores user_id={self.user_id} be={self.be_score} do={self.do_score} have={self.have_score}>'
    
    def get_level_for_phase(self, phase):
        """Get the user's level for a specific phase"""
        if phase == 'BE':
            return self.be_level
        elif phase == 'DO':
            return self.do_level
        elif phase == 'HAVE':
            return self.have_level
        return 'Beginner'
    
    def get_score_for_phase(self, phase):
        """Get the user's score for a specific phase"""
        if phase == 'BE':
            return self.be_score
        elif phase == 'DO':
            return self.do_score
        elif phase == 'HAVE':
            return self.have_score
        return 0
    
    def get_overall_readiness_level(self):
        """Calculate overall readiness level based on average scores"""
        avg_score = (self.be_score + self.do_score + self.have_score) / 3
        if avg_score >= 80:
            return 'Advanced'
        elif avg_score >= 60:
            return 'Intermediate'
        else:
            return 'Beginner'


class ArticleSearch(Base):
    """Track article search analytics for insights and optimization"""
    __tablename__ = 'article_searches'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Search metadata
    search_query = Column(String(500))  # The search query used
    search_filters = Column(JSON)  # Applied filters
    results_count = Column(Integer, default=0)  # Number of results returned
    
    # Search performance
    search_time_ms = Column(Integer)  # Time taken for search in milliseconds
    search_success = Column(Boolean, default=True)  # Whether search was successful
    
    # User context
    session_id = Column(String(100))  # User session identifier
    user_agent = Column(String(500))  # Browser/user agent info
    ip_address = Column(String(45))  # User IP address (for analytics)
    
    # Search outcome
    clicked_article_id = Column(UUID(as_uuid=True), ForeignKey('articles.id'))  # If user clicked a result
    clicked_position = Column(Integer)  # Position of clicked result
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="article_searches")
    clicked_article = relationship("Article")
    
    def __repr__(self):
        return f'<ArticleSearch user_id={self.user_id} query="{self.search_query[:50]}...">'
    
    def to_dict(self):
        """Convert search record to dictionary"""
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'search_query': self.search_query,
            'search_filters': self.search_filters,
            'results_count': self.results_count,
            'search_time_ms': self.search_time_ms,
            'search_success': self.search_success,
            'clicked_article_id': str(self.clicked_article_id) if self.clicked_article_id else None,
            'clicked_position': self.clicked_position,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
