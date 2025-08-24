-- Migration: Create Complete Article Library Tables
-- Description: Comprehensive creation of all article library tables with proper structure, indexes, and constraints
-- Date: 2025-08-23
-- Author: Mingus Development Team

-- Enable required extensions for PostgreSQL (if using PostgreSQL)
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE EXTENSION IF NOT EXISTS unaccent;

-- Create enum types for PostgreSQL
-- For SQLite compatibility, we'll use CHECK constraints instead

-- Articles table - Core article storage
CREATE TABLE IF NOT EXISTS articles (
    id VARCHAR(36) PRIMARY KEY,
    url VARCHAR(500) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    content_preview VARCHAR(500),
    meta_description TEXT,
    author VARCHAR(200),
    publish_date DATE,
    word_count INTEGER DEFAULT 0,
    reading_time_minutes INTEGER DEFAULT 0,
    primary_phase VARCHAR(10) NOT NULL CHECK (primary_phase IN ('BE', 'DO', 'HAVE')),
    difficulty_level VARCHAR(20) NOT NULL CHECK (difficulty_level IN ('Beginner', 'Intermediate', 'Advanced')),
    confidence_score REAL DEFAULT 0.0,
    demographic_relevance INTEGER DEFAULT 0,
    cultural_sensitivity INTEGER DEFAULT 0,
    income_impact_potential INTEGER DEFAULT 0,
    actionability_score INTEGER DEFAULT 0,
    professional_development_value INTEGER DEFAULT 0,
    key_topics TEXT, -- JSON stored as TEXT
    learning_objectives TEXT, -- JSON stored as TEXT
    prerequisites TEXT, -- JSON stored as TEXT
    cultural_relevance_keywords TEXT, -- JSON stored as TEXT
    target_income_range VARCHAR(50),
    career_stage VARCHAR(50),
    recommended_reading_order INTEGER DEFAULT 50,
    search_vector TEXT, -- For full-text search
    domain VARCHAR(100) NOT NULL,
    source_quality_score REAL DEFAULT 0.0,
    is_active BOOLEAN DEFAULT 1,
    is_featured BOOLEAN DEFAULT 0,
    admin_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User article reads table - Track reading history and engagement
CREATE TABLE IF NOT EXISTS user_article_reads (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    article_id VARCHAR(36) NOT NULL,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    time_spent_seconds INTEGER DEFAULT 0,
    scroll_depth_percentage REAL DEFAULT 0.0,
    engagement_score REAL DEFAULT 0.0,
    found_helpful BOOLEAN,
    would_recommend BOOLEAN,
    difficulty_rating INTEGER,
    relevance_rating INTEGER,
    reading_session_id VARCHAR(100),
    source_page VARCHAR(200),
    device_type VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    UNIQUE(user_id, article_id)
);

-- User article bookmarks table - Track bookmarks and saved articles
CREATE TABLE IF NOT EXISTS user_article_bookmarks (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    article_id VARCHAR(36) NOT NULL,
    notes TEXT,
    tags TEXT, -- JSON stored as TEXT
    priority INTEGER DEFAULT 1,
    folder_name VARCHAR(100) DEFAULT 'General',
    is_archived BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    UNIQUE(user_id, article_id)
);

-- User article ratings table - Track ratings and reviews
CREATE TABLE IF NOT EXISTS user_article_ratings (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    article_id VARCHAR(36) NOT NULL,
    overall_rating INTEGER NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),
    helpfulness_rating INTEGER CHECK (helpfulness_rating >= 1 AND helpfulness_rating <= 5),
    clarity_rating INTEGER CHECK (clarity_rating >= 1 AND clarity_rating <= 5),
    actionability_rating INTEGER CHECK (actionability_rating >= 1 AND actionability_rating <= 5),
    cultural_relevance_rating INTEGER CHECK (cultural_relevance_rating >= 1 AND cultural_relevance_rating <= 5),
    review_text TEXT,
    review_title VARCHAR(200),
    is_approved BOOLEAN DEFAULT 1,
    is_anonymous BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    UNIQUE(user_id, article_id)
);

-- User article progress table - Track Be-Do-Have journey progress
CREATE TABLE IF NOT EXISTS user_article_progress (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    article_id VARCHAR(36) NOT NULL,
    current_phase VARCHAR(10) NOT NULL CHECK (current_phase IN ('BE', 'DO', 'HAVE')),
    phase_progress REAL DEFAULT 0.0,
    total_progress REAL DEFAULT 0.0,
    learning_objectives_achieved TEXT, -- JSON stored as TEXT
    skills_developed TEXT, -- JSON stored as TEXT
    actions_taken TEXT, -- JSON stored as TEXT
    self_assessment_score INTEGER CHECK (self_assessment_score >= 1 AND self_assessment_score <= 10),
    confidence_increase REAL,
    knowledge_retention_score REAL,
    next_recommended_article_id VARCHAR(36),
    next_phase_target VARCHAR(10) CHECK (next_phase_target IN ('BE', 'DO', 'HAVE')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
    FOREIGN KEY (next_recommended_article_id) REFERENCES articles(id) ON DELETE SET NULL,
    UNIQUE(user_id, article_id)
);

-- Article recommendations table - Track recommendations and personalization
CREATE TABLE IF NOT EXISTS article_recommendations (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    article_id VARCHAR(36) NOT NULL,
    recommendation_score REAL NOT NULL CHECK (recommendation_score >= 0.0 AND recommendation_score <= 1.0),
    recommendation_reason VARCHAR(200),
    recommendation_source VARCHAR(100),
    user_income_match REAL CHECK (user_income_match >= 0.0 AND user_income_match <= 1.0),
    user_career_match REAL CHECK (user_career_match >= 0.0 AND user_career_match <= 1.0),
    user_goals_match REAL CHECK (user_goals_match >= 0.0 AND user_goals_match <= 1.0),
    cultural_relevance_match REAL CHECK (cultural_relevance_match >= 0.0 AND cultural_relevance_match <= 1.0),
    is_displayed BOOLEAN DEFAULT 0,
    is_clicked BOOLEAN DEFAULT 0,
    is_read BOOLEAN DEFAULT 0,
    display_position INTEGER,
    recommended_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    displayed_at DATETIME,
    clicked_at DATETIME,
    read_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);

-- Article analytics table - Track aggregate analytics
CREATE TABLE IF NOT EXISTS article_analytics (
    id VARCHAR(36) PRIMARY KEY,
    article_id VARCHAR(36) NOT NULL UNIQUE,
    total_views INTEGER DEFAULT 0,
    total_reads INTEGER DEFAULT 0,
    total_bookmarks INTEGER DEFAULT 0,
    total_shares INTEGER DEFAULT 0,
    completion_rate REAL DEFAULT 0.0,
    average_time_spent REAL DEFAULT 0.0,
    average_scroll_depth REAL DEFAULT 0.0,
    average_rating REAL DEFAULT 0.0,
    total_ratings INTEGER DEFAULT 0,
    helpfulness_score REAL DEFAULT 0.0,
    clarity_score REAL DEFAULT 0.0,
    actionability_score REAL DEFAULT 0.0,
    cultural_relevance_score REAL DEFAULT 0.0,
    recommendation_click_rate REAL DEFAULT 0.0,
    recommendation_read_rate REAL DEFAULT 0.0,
    demographic_breakdown TEXT, -- JSON stored as TEXT
    phase_effectiveness TEXT, -- JSON stored as TEXT
    daily_views TEXT, -- JSON stored as TEXT
    weekly_engagement TEXT, -- JSON stored as TEXT
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
);

-- User assessment scores table - Track Be-Do-Have assessment scores
CREATE TABLE IF NOT EXISTS user_assessment_scores (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    be_score INTEGER DEFAULT 0 CHECK (be_score >= 0 AND be_score <= 100),
    do_score INTEGER DEFAULT 0 CHECK (do_score >= 0 AND do_score <= 100),
    have_score INTEGER DEFAULT 0 CHECK (have_score >= 0 AND have_score <= 100),
    assessment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    assessment_version VARCHAR(50) DEFAULT '1.0',
    total_questions INTEGER DEFAULT 0,
    completion_time_minutes INTEGER DEFAULT 0,
    be_level VARCHAR(20) DEFAULT 'Beginner' CHECK (be_level IN ('Beginner', 'Intermediate', 'Advanced')),
    do_level VARCHAR(20) DEFAULT 'Beginner' CHECK (do_level IN ('Beginner', 'Intermediate', 'Advanced')),
    have_level VARCHAR(20) DEFAULT 'Beginner' CHECK (have_level IN ('Beginner', 'Intermediate', 'Advanced')),
    overall_readiness_level VARCHAR(20) DEFAULT 'Beginner' CHECK (overall_readiness_level IN ('Beginner', 'Intermediate', 'Advanced')),
    confidence_score REAL DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    is_valid BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Article searches table - Track search analytics
CREATE TABLE IF NOT EXISTS article_searches (
    id VARCHAR(36) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    search_query VARCHAR(500),
    search_filters TEXT, -- JSON stored as TEXT
    results_count INTEGER DEFAULT 0,
    search_time_ms INTEGER,
    search_success BOOLEAN DEFAULT 1,
    session_id VARCHAR(100),
    user_agent VARCHAR(500),
    ip_address VARCHAR(45),
    clicked_article_id VARCHAR(36),
    clicked_position INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (clicked_article_id) REFERENCES articles(id) ON DELETE SET NULL
);

-- Create indexes for optimal performance

-- Articles table indexes
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_title ON articles(title);
CREATE INDEX IF NOT EXISTS idx_articles_primary_phase ON articles(primary_phase);
CREATE INDEX IF NOT EXISTS idx_articles_difficulty_level ON articles(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_articles_demographic_relevance ON articles(demographic_relevance);
CREATE INDEX IF NOT EXISTS idx_articles_domain ON articles(domain);
CREATE INDEX IF NOT EXISTS idx_articles_is_active ON articles(is_active);
CREATE INDEX IF NOT EXISTS idx_articles_is_featured ON articles(is_featured);
CREATE INDEX IF NOT EXISTS idx_articles_created_at ON articles(created_at);
CREATE INDEX IF NOT EXISTS idx_articles_publish_date ON articles(publish_date);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_articles_phase_difficulty ON articles(primary_phase, difficulty_level);
CREATE INDEX IF NOT EXISTS idx_articles_domain_active ON articles(domain, is_active);

-- User article reads indexes
CREATE INDEX IF NOT EXISTS idx_user_article_reads_user_id ON user_article_reads(user_id);
CREATE INDEX IF NOT EXISTS idx_user_article_reads_article_id ON user_article_reads(article_id);
CREATE INDEX IF NOT EXISTS idx_user_article_reads_created_at ON user_article_reads(created_at);
CREATE INDEX IF NOT EXISTS idx_user_article_reads_completed_at ON user_article_reads(completed_at);

-- User article bookmarks indexes
CREATE INDEX IF NOT EXISTS idx_user_article_bookmarks_user_id ON user_article_bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_user_article_bookmarks_article_id ON user_article_bookmarks(article_id);
CREATE INDEX IF NOT EXISTS idx_user_article_bookmarks_folder_name ON user_article_bookmarks(folder_name);

-- User article ratings indexes
CREATE INDEX IF NOT EXISTS idx_user_article_ratings_user_id ON user_article_ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_article_ratings_article_id ON user_article_ratings(article_id);
CREATE INDEX IF NOT EXISTS idx_user_article_ratings_overall_rating ON user_article_ratings(overall_rating);
CREATE INDEX IF NOT EXISTS idx_user_article_ratings_is_approved ON user_article_ratings(is_approved);

-- User article progress indexes
CREATE INDEX IF NOT EXISTS idx_user_article_progress_user_id ON user_article_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_article_progress_article_id ON user_article_progress(article_id);
CREATE INDEX IF NOT EXISTS idx_user_article_progress_current_phase ON user_article_progress(current_phase);

-- Article recommendations indexes
CREATE INDEX IF NOT EXISTS idx_article_recommendations_user_id ON article_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_article_recommendations_article_id ON article_recommendations(article_id);
CREATE INDEX IF NOT EXISTS idx_article_recommendations_score ON article_recommendations(recommendation_score);
CREATE INDEX IF NOT EXISTS idx_article_recommendations_recommended_at ON article_recommendations(recommended_at);

-- Article analytics indexes
CREATE INDEX IF NOT EXISTS idx_article_analytics_article_id ON article_analytics(article_id);
CREATE INDEX IF NOT EXISTS idx_article_analytics_total_views ON article_analytics(total_views);
CREATE INDEX IF NOT EXISTS idx_article_analytics_total_reads ON article_analytics(total_reads);
CREATE INDEX IF NOT EXISTS idx_article_analytics_average_rating ON article_analytics(average_rating);

-- User assessment scores indexes
CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_user_id ON user_assessment_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_assessment_date ON user_assessment_scores(assessment_date);

-- Article searches indexes
CREATE INDEX IF NOT EXISTS idx_article_searches_user_id ON article_searches(user_id);
CREATE INDEX IF NOT EXISTS idx_article_searches_created_at ON article_searches(created_at);
CREATE INDEX IF NOT EXISTS idx_article_searches_query ON article_searches(search_query);

-- PostgreSQL-specific full-text search configuration
-- Uncomment and modify for PostgreSQL installations

/*
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Create full-text search function
CREATE OR REPLACE FUNCTION update_article_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.content_preview, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.meta_description, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.key_topics::text, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic search vector updates
DROP TRIGGER IF EXISTS update_article_search_vector_trigger ON articles;
CREATE TRIGGER update_article_search_vector_trigger
    BEFORE INSERT OR UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_article_search_vector();

-- Create GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_articles_search_vector ON articles USING GIN(search_vector);

-- Update existing articles to populate search vectors
UPDATE articles SET search_vector = 
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(content_preview, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(meta_description, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(key_topics::text, '')), 'B')
WHERE search_vector IS NULL;
*/

-- Insert sample data for testing (optional)
-- Uncomment to add sample articles for testing

/*
INSERT OR REPLACE INTO articles (
    id, url, title, content, content_preview, primary_phase, 
    difficulty_level, confidence_score, demographic_relevance,
    cultural_sensitivity, income_impact_potential, actionability_score,
    professional_development_value, key_topics, learning_objectives,
    prerequisites, cultural_relevance_keywords, target_income_range,
    career_stage, recommended_reading_order, domain, source_quality_score,
    is_active, is_featured, created_at, updated_at
) VALUES (
    'sample-article-1', 
    'https://example.com/sample-article-1',
    'Building Financial Confidence: A Beginner''s Guide',
    'This comprehensive guide helps beginners build financial confidence through practical steps and mindset shifts...',
    'Learn how to build financial confidence with practical steps and mindset shifts for beginners.',
    'BE',
    'Beginner',
    0.85,
    8,
    7,
    6,
    8,
    7,
    '["financial confidence", "mindset", "beginner finance"]',
    '["Understand basic financial concepts", "Develop positive money mindset", "Create simple financial plan"]',
    '["No prior financial knowledge required"]',
    '["financial literacy", "money management", "personal finance"]',
    '$40K-$60K',
    'Early career',
    10,
    'example.com',
    0.8,
    1,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Create analytics record for sample article
INSERT OR REPLACE INTO article_analytics (
    id, article_id, total_views, total_reads, total_bookmarks,
    total_shares, completion_rate, average_time_spent,
    average_scroll_depth, average_rating, total_ratings,
    helpfulness_score, clarity_score, actionability_score,
    cultural_relevance_score, recommendation_click_rate,
    recommendation_read_rate, created_at, updated_at
) VALUES (
    'sample-analytics-1',
    'sample-article-1',
    0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
*/

-- Verify table creation
SELECT 'Articles table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='articles');
SELECT 'User article reads table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_article_reads');
SELECT 'User article bookmarks table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_article_bookmarks');
SELECT 'User article ratings table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_article_ratings');
SELECT 'User article progress table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_article_progress');
SELECT 'Article recommendations table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='article_recommendations');
SELECT 'Article analytics table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='article_analytics');
SELECT 'User assessment scores table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_assessment_scores');
SELECT 'Article searches table created successfully' as status WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='article_searches');
