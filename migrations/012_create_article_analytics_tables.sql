-- Migration: Create Article Analytics Tables
-- Description: Creates analytics tables for tracking user engagement and article performance

-- User Engagement Metrics Table
CREATE TABLE IF NOT EXISTS user_engagement_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(50) NOT NULL,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    total_session_time INTEGER DEFAULT 0,
    articles_viewed INTEGER DEFAULT 0,
    articles_completed INTEGER DEFAULT 0,
    articles_bookmarked INTEGER DEFAULT 0,
    articles_shared INTEGER DEFAULT 0,
    search_queries_count INTEGER DEFAULT 0,
    search_success_rate FLOAT DEFAULT 0.0,
    recommendations_clicked INTEGER DEFAULT 0,
    assessment_completed BOOLEAN DEFAULT FALSE,
    be_score_change INTEGER DEFAULT 0,
    do_score_change INTEGER DEFAULT 0,
    have_score_change INTEGER DEFAULT 0,
    content_unlocked_count INTEGER DEFAULT 0,
    cultural_content_preference FLOAT DEFAULT 0.0,
    community_focused_articles_read INTEGER DEFAULT 0,
    device_type VARCHAR(20),
    user_agent VARCHAR(200),
    ip_location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Article Performance Metrics Table
CREATE TABLE IF NOT EXISTS article_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    total_views INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    average_reading_time FLOAT DEFAULT 0.0,
    completion_rate FLOAT DEFAULT 0.0,
    bookmark_rate FLOAT DEFAULT 0.0,
    share_rate FLOAT DEFAULT 0.0,
    rating_average FLOAT DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0,
    cultural_engagement_score FLOAT DEFAULT 0.0,
    demographic_reach JSONB,
    subscription_conversion_rate FLOAT DEFAULT 0.0,
    user_retention_impact FLOAT DEFAULT 0.0,
    bounce_rate FLOAT DEFAULT 0.0,
    return_reader_rate FLOAT DEFAULT 0.0,
    recommendation_click_rate FLOAT DEFAULT 0.0,
    peak_reading_hours JSONB,
    seasonal_performance JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search Analytics Table
CREATE TABLE IF NOT EXISTS search_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    search_query VARCHAR(500) NOT NULL,
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    selected_phase VARCHAR(10),
    cultural_relevance_filter INTEGER,
    results_count INTEGER DEFAULT 0,
    clicked_article_id UUID REFERENCES articles(id) ON DELETE SET NULL,
    click_position INTEGER,
    result_clicked BOOLEAN DEFAULT FALSE,
    session_continued BOOLEAN DEFAULT FALSE,
    query_length INTEGER DEFAULT 0,
    query_type VARCHAR(50),
    cultural_keywords_present BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cultural Relevance Analytics Table
CREATE TABLE IF NOT EXISTS cultural_relevance_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    high_relevance_content_preference FLOAT DEFAULT 0.0,
    community_content_engagement FLOAT DEFAULT 0.0,
    diverse_representation_response FLOAT DEFAULT 0.0,
    corporate_navigation_interest FLOAT DEFAULT 0.0,
    generational_wealth_focus FLOAT DEFAULT 0.0,
    systemic_barrier_awareness_content FLOAT DEFAULT 0.0,
    cultural_search_terms_frequency INTEGER DEFAULT 0,
    cultural_recommendation_click_rate FLOAT DEFAULT 0.0,
    cultural_content_completion_rate FLOAT DEFAULT 0.0,
    cultural_content_sharing_rate FLOAT DEFAULT 0.0,
    cultural_content_return_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_engagement_user_session ON user_engagement_metrics(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_article_performance_article ON article_performance_metrics(article_id);
CREATE INDEX IF NOT EXISTS idx_search_analytics_user_time ON search_analytics(user_id, search_timestamp);
CREATE INDEX IF NOT EXISTS idx_cultural_analytics_user ON cultural_relevance_analytics(user_id);

SELECT 'Migration 012: Article Analytics Tables created successfully' as status;
