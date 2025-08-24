-- =====================================================
-- MIGRATION: Meme Feature Enhancements
-- =====================================================
-- Description: Enhanced meme feature with performance optimizations
-- Revision: 015_meme_feature_enhancements
-- Date: 2025-01-XX

-- =====================================================
-- PERFORMANCE OPTIMIZATIONS
-- =====================================================

-- Add composite indexes for better query performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memes_category_active_priority 
ON memes (category, is_active, priority DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_memes_engagement_active 
ON memes (engagement_score DESC, is_active) WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_meme_history_user_interaction 
ON user_meme_history (user_id, interaction_type, viewed_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_meme_preferences_user_enabled 
ON user_meme_preferences (user_id, memes_enabled) WHERE memes_enabled = true;

-- =====================================================
-- ADDITIONAL COLUMNS FOR ENHANCED FEATURES
-- =====================================================

-- Add image metadata columns to memes table
ALTER TABLE memes ADD COLUMN IF NOT EXISTS image_width INTEGER;
ALTER TABLE memes ADD COLUMN IF NOT EXISTS image_height INTEGER;
ALTER TABLE memes ADD COLUMN IF NOT EXISTS image_size_bytes BIGINT;
ALTER TABLE memes ADD COLUMN IF NOT EXISTS image_format VARCHAR(10);
ALTER TABLE memes ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);
ALTER TABLE memes ADD COLUMN IF NOT EXISTS preview_url VARCHAR(500);

-- Add analytics columns
ALTER TABLE memes ADD COLUMN IF NOT EXISTS skip_count INTEGER DEFAULT 0;
ALTER TABLE memes ADD COLUMN IF NOT EXISTS conversion_count INTEGER DEFAULT 0;
ALTER TABLE memes ADD COLUMN IF NOT EXISTS avg_view_duration_seconds DECIMAL(5,2);
ALTER TABLE memes ADD COLUMN IF NOT EXISTS last_analytics_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add content moderation columns
ALTER TABLE memes ADD COLUMN IF NOT EXISTS moderation_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE memes ADD COLUMN IF NOT EXISTS moderation_notes TEXT;
ALTER TABLE memes ADD COLUMN IF NOT EXISTS moderated_by INTEGER REFERENCES users(id);
ALTER TABLE memes ADD COLUMN IF NOT EXISTS moderated_at TIMESTAMP;

-- Add scheduling columns
ALTER TABLE memes ADD COLUMN IF NOT EXISTS scheduled_start_date TIMESTAMP;
ALTER TABLE memes ADD COLUMN IF NOT EXISTS scheduled_end_date TIMESTAMP;
ALTER TABLE memes ADD COLUMN IF NOT EXISTS is_scheduled BOOLEAN DEFAULT false;

-- =====================================================
-- ENHANCED USER PREFERENCES
-- =====================================================

-- Add more granular preference options
ALTER TABLE user_meme_preferences ADD COLUMN IF NOT EXISTS preferred_time_of_day VARCHAR(20) DEFAULT 'any';
ALTER TABLE user_meme_preferences ADD COLUMN IF NOT EXISTS preferred_days_of_week INTEGER[] DEFAULT '{1,2,3,4,5,6,7}';
ALTER TABLE user_meme_preferences ADD COLUMN IF NOT EXISTS content_sensitivity_level VARCHAR(20) DEFAULT 'family_friendly';
ALTER TABLE user_meme_preferences ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10) DEFAULT 'en';
ALTER TABLE user_meme_preferences ADD COLUMN IF NOT EXISTS accessibility_preferences JSONB DEFAULT '{}';

-- Add notification preferences
ALTER TABLE user_meme_preferences ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN DEFAULT false;
ALTER TABLE user_meme_preferences ADD COLUMN IF NOT EXISTS push_notifications BOOLEAN DEFAULT false;
ALTER TABLE user_meme_preferences ADD COLUMN IF NOT EXISTS notification_frequency VARCHAR(20) DEFAULT 'daily';

-- =====================================================
-- ENHANCED ANALYTICS TRACKING
-- =====================================================

-- Add more detailed interaction tracking
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS view_duration_seconds INTEGER;
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS scroll_depth_percentage INTEGER;
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS device_type VARCHAR(20);
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS browser_type VARCHAR(50);
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS screen_resolution VARCHAR(20);
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS connection_speed VARCHAR(20);
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS user_agent TEXT;

-- Add conversion tracking
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS conversion_type VARCHAR(50);
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS conversion_value DECIMAL(10,2);
ALTER TABLE user_meme_history ADD COLUMN IF NOT EXISTS conversion_metadata JSONB;

-- =====================================================
-- NEW TABLES FOR ENHANCED FEATURES
-- =====================================================

-- Meme categories table for better management
CREATE TABLE IF NOT EXISTS meme_categories (
    id SERIAL PRIMARY KEY,
    category_id VARCHAR(20) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(10),
    color_hex VARCHAR(7),
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meme tags table for better categorization
CREATE TABLE IF NOT EXISTS meme_tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meme-tag relationship table
CREATE TABLE IF NOT EXISTS meme_tag_relationships (
    meme_id VARCHAR(36) REFERENCES memes(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES meme_tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (meme_id, tag_id)
);

-- Meme analytics summary table for performance
CREATE TABLE IF NOT EXISTS meme_analytics_summary (
    meme_id VARCHAR(36) REFERENCES memes(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_views INTEGER DEFAULT 0,
    total_likes INTEGER DEFAULT 0,
    total_shares INTEGER DEFAULT 0,
    total_skips INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    avg_view_duration_seconds DECIMAL(5,2),
    engagement_rate DECIMAL(5,4),
    conversion_rate DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (meme_id, date)
);

-- =====================================================
-- CONSTRAINTS AND VALIDATIONS
-- =====================================================

-- Add constraints for new columns
ALTER TABLE memes ADD CONSTRAINT IF NOT EXISTS valid_moderation_status 
CHECK (moderation_status IN ('pending', 'approved', 'rejected', 'flagged'));

ALTER TABLE memes ADD CONSTRAINT IF NOT EXISTS valid_content_sensitivity 
CHECK (content_sensitivity_level IN ('family_friendly', 'teen', 'adult'));

ALTER TABLE user_meme_preferences ADD CONSTRAINT IF NOT EXISTS valid_time_of_day 
CHECK (preferred_time_of_day IN ('morning', 'afternoon', 'evening', 'night', 'any'));

ALTER TABLE user_meme_preferences ADD CONSTRAINT IF NOT EXISTS valid_notification_frequency 
CHECK (notification_frequency IN ('immediate', 'hourly', 'daily', 'weekly', 'never'));

-- =====================================================
-- INDEXES FOR NEW TABLES
-- =====================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_meme_categories_active 
ON meme_categories (is_active, sort_order);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_meme_tags_active 
ON meme_tags (is_active, usage_count DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_meme_tag_relationships_meme 
ON meme_tag_relationships (meme_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_meme_tag_relationships_tag 
ON meme_tag_relationships (tag_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_meme_analytics_summary_date 
ON meme_analytics_summary (date);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_meme_analytics_summary_meme_date 
ON meme_analytics_summary (meme_id, date DESC);

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================

-- Function to update meme analytics summary
CREATE OR REPLACE FUNCTION update_meme_analytics_summary()
RETURNS TRIGGER AS $$
BEGIN
    -- Update or insert analytics summary
    INSERT INTO meme_analytics_summary (
        meme_id, date, total_views, total_likes, total_shares, 
        total_skips, total_conversions, avg_view_duration_seconds
    ) VALUES (
        NEW.meme_id, 
        DATE(NEW.viewed_at),
        CASE WHEN NEW.interaction_type = 'view' THEN 1 ELSE 0 END,
        CASE WHEN NEW.interaction_type = 'like' THEN 1 ELSE 0 END,
        CASE WHEN NEW.interaction_type = 'share' THEN 1 ELSE 0 END,
        CASE WHEN NEW.interaction_type = 'skip' THEN 1 ELSE 0 END,
        CASE WHEN NEW.conversion_type IS NOT NULL THEN 1 ELSE 0 END,
        NEW.view_duration_seconds
    )
    ON CONFLICT (meme_id, date) DO UPDATE SET
        total_views = meme_analytics_summary.total_views + EXCLUDED.total_views,
        total_likes = meme_analytics_summary.total_likes + EXCLUDED.total_likes,
        total_shares = meme_analytics_summary.total_shares + EXCLUDED.total_shares,
        total_skips = meme_analytics_summary.total_skips + EXCLUDED.total_skips,
        total_conversions = meme_analytics_summary.total_conversions + EXCLUDED.total_conversions,
        avg_view_duration_seconds = CASE 
            WHEN EXCLUDED.avg_view_duration_seconds IS NOT NULL 
            THEN (meme_analytics_summary.avg_view_duration_seconds + EXCLUDED.avg_view_duration_seconds) / 2
            ELSE meme_analytics_summary.avg_view_duration_seconds
        END,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for analytics summary updates
DROP TRIGGER IF EXISTS trigger_update_meme_analytics_summary ON user_meme_history;
CREATE TRIGGER trigger_update_meme_analytics_summary
    AFTER INSERT ON user_meme_history
    FOR EACH ROW
    EXECUTE FUNCTION update_meme_analytics_summary();

-- =====================================================
-- SEED DATA FOR CATEGORIES
-- =====================================================

INSERT INTO meme_categories (category_id, display_name, description, icon, color_hex, sort_order) VALUES
('faith', 'Faith & Spirituality', 'Inspirational content related to faith, spirituality, and personal growth', '🙏', '#4F46E5', 1),
('work_life', 'Work & Career', 'Motivational content about professional development and work-life balance', '💼', '#059669', 2),
('friendships', 'Friendships', 'Content about building and maintaining meaningful friendships', '👥', '#DC2626', 3),
('children', 'Parenting & Children', 'Family-focused content about parenting and raising children', '👶', '#EA580C', 4),
('relationships', 'Relationships', 'Content about romantic relationships and partnership', '❤️', '#DB2777', 5),
('going_out', 'Social Life', 'Content about social activities, entertainment, and leisure', '🎉', '#7C3AED', 6)
ON CONFLICT (category_id) DO NOTHING;

-- =====================================================
-- MIGRATION COMPLETION
-- =====================================================

-- Update migration tracking
INSERT INTO schema_migrations (version, applied_at) 
VALUES ('015_meme_feature_enhancements', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;
