-- MINGUS Development Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create additional indexes for article library (if tables exist)
DO $$
BEGIN
    -- Create indexes for articles table
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'articles') THEN
        CREATE INDEX IF NOT EXISTS idx_articles_title_gin ON articles USING gin(to_tsvector('english', title));
        CREATE INDEX IF NOT EXISTS idx_articles_content_gin ON articles USING gin(to_tsvector('english', content));
        CREATE INDEX IF NOT EXISTS idx_articles_published_date ON articles(published_date DESC);
        CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
        CREATE INDEX IF NOT EXISTS idx_articles_cultural_relevance ON articles(cultural_relevance_score DESC);
        RAISE NOTICE 'Created indexes for articles table';
    END IF;

    -- Create indexes for user_article_progress table
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_article_progress') THEN
        CREATE INDEX IF NOT EXISTS idx_user_article_progress_user_id ON user_article_progress(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_article_progress_article_id ON user_article_progress(article_id);
        CREATE INDEX IF NOT EXISTS idx_user_article_progress_completed_at ON user_article_progress(completed_at DESC);
        RAISE NOTICE 'Created indexes for user_article_progress table';
    END IF;

    -- Create indexes for user_assessment_scores table
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_assessment_scores') THEN
        CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_user_id ON user_assessment_scores(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_framework ON user_assessment_scores(framework);
        RAISE NOTICE 'Created indexes for user_assessment_scores table';
    END IF;

    -- Create indexes for article_folders table
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'article_folders') THEN
        CREATE INDEX IF NOT EXISTS idx_article_folders_user_id ON article_folders(user_id);
        CREATE INDEX IF NOT EXISTS idx_article_folders_name ON article_folders(name);
        RAISE NOTICE 'Created indexes for article_folders table';
    END IF;

    -- Create indexes for article_bookmarks table
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'article_bookmarks') THEN
        CREATE INDEX IF NOT EXISTS idx_article_bookmarks_user_id ON article_bookmarks(user_id);
        CREATE INDEX IF NOT EXISTS idx_article_bookmarks_article_id ON article_bookmarks(article_id);
        RAISE NOTICE 'Created indexes for article_bookmarks table';
    END IF;

    -- Create indexes for article_analytics table
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'article_analytics') THEN
        CREATE INDEX IF NOT EXISTS idx_article_analytics_article_id ON article_analytics(article_id);
        CREATE INDEX IF NOT EXISTS idx_article_analytics_date ON article_analytics(date);
        RAISE NOTICE 'Created indexes for article_analytics table';
    END IF;

END $$;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mingus;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mingus;

-- Create some sample data for development (optional)
DO $$
BEGIN
    -- Insert sample article categories if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'articles') THEN
        RAISE NOTICE 'Articles table does not exist yet - will be created by Flask-Migrate';
    ELSE
        -- Insert sample categories if table is empty
        IF (SELECT COUNT(*) FROM articles) = 0 THEN
            RAISE NOTICE 'Articles table is empty - ready for sample data';
        END IF;
    END IF;
END $$;
