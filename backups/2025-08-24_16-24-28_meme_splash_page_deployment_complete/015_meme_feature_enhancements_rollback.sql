-- =====================================================
-- ROLLBACK: Meme Feature Enhancements
-- =====================================================
-- Description: Rollback script for meme feature enhancements
-- Revision: 015_meme_feature_enhancements_rollback
-- Date: 2025-01-XX

-- =====================================================
-- DROP TRIGGERS AND FUNCTIONS
-- =====================================================

-- Drop trigger first
DROP TRIGGER IF EXISTS trigger_update_meme_analytics_summary ON user_meme_history;

-- Drop function
DROP FUNCTION IF EXISTS update_meme_analytics_summary();

-- =====================================================
-- DROP INDEXES
-- =====================================================

-- Drop performance optimization indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_memes_category_active_priority;
DROP INDEX CONCURRENTLY IF EXISTS idx_memes_engagement_active;
DROP INDEX CONCURRENTLY IF EXISTS idx_user_meme_history_user_interaction;
DROP INDEX CONCURRENTLY IF EXISTS idx_user_meme_preferences_user_enabled;

-- Drop new table indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_meme_categories_active;
DROP INDEX CONCURRENTLY IF EXISTS idx_meme_tags_active;
DROP INDEX CONCURRENTLY IF EXISTS idx_meme_tag_relationships_meme;
DROP INDEX CONCURRENTLY IF EXISTS idx_meme_tag_relationships_tag;
DROP INDEX CONCURRENTLY IF EXISTS idx_meme_analytics_summary_date;
DROP INDEX CONCURRENTLY IF EXISTS idx_meme_analytics_summary_meme_date;

-- =====================================================
-- DROP NEW TABLES
-- =====================================================

-- Drop new tables in reverse dependency order
DROP TABLE IF EXISTS meme_analytics_summary;
DROP TABLE IF EXISTS meme_tag_relationships;
DROP TABLE IF EXISTS meme_tags;
DROP TABLE IF EXISTS meme_categories;

-- =====================================================
-- DROP CONSTRAINTS
-- =====================================================

-- Drop constraints from memes table
ALTER TABLE memes DROP CONSTRAINT IF EXISTS valid_moderation_status;
ALTER TABLE memes DROP CONSTRAINT IF EXISTS valid_content_sensitivity;

-- Drop constraints from user_meme_preferences table
ALTER TABLE user_meme_preferences DROP CONSTRAINT IF EXISTS valid_time_of_day;
ALTER TABLE user_meme_preferences DROP CONSTRAINT IF EXISTS valid_notification_frequency;

-- =====================================================
-- DROP COLUMNS FROM MEMES TABLE
-- =====================================================

-- Drop image metadata columns
ALTER TABLE memes DROP COLUMN IF EXISTS image_width;
ALTER TABLE memes DROP COLUMN IF EXISTS image_height;
ALTER TABLE memes DROP COLUMN IF EXISTS image_size_bytes;
ALTER TABLE memes DROP COLUMN IF EXISTS image_format;
ALTER TABLE memes DROP COLUMN IF EXISTS thumbnail_url;
ALTER TABLE memes DROP COLUMN IF EXISTS preview_url;

-- Drop analytics columns
ALTER TABLE memes DROP COLUMN IF EXISTS skip_count;
ALTER TABLE memes DROP COLUMN IF EXISTS conversion_count;
ALTER TABLE memes DROP COLUMN IF EXISTS avg_view_duration_seconds;
ALTER TABLE memes DROP COLUMN IF EXISTS last_analytics_update;

-- Drop content moderation columns
ALTER TABLE memes DROP COLUMN IF EXISTS moderation_status;
ALTER TABLE memes DROP COLUMN IF EXISTS moderation_notes;
ALTER TABLE memes DROP COLUMN IF EXISTS moderated_by;
ALTER TABLE memes DROP COLUMN IF EXISTS moderated_at;

-- Drop scheduling columns
ALTER TABLE memes DROP COLUMN IF EXISTS scheduled_start_date;
ALTER TABLE memes DROP COLUMN IF EXISTS scheduled_end_date;
ALTER TABLE memes DROP COLUMN IF EXISTS is_scheduled;

-- =====================================================
-- DROP COLUMNS FROM USER_MEME_PREFERENCES TABLE
-- =====================================================

-- Drop enhanced preference columns
ALTER TABLE user_meme_preferences DROP COLUMN IF EXISTS preferred_time_of_day;
ALTER TABLE user_meme_preferences DROP COLUMN IF EXISTS preferred_days_of_week;
ALTER TABLE user_meme_preferences DROP COLUMN IF EXISTS content_sensitivity_level;
ALTER TABLE user_meme_preferences DROP COLUMN IF EXISTS language_preference;
ALTER TABLE user_meme_preferences DROP COLUMN IF EXISTS accessibility_preferences;

-- Drop notification preference columns
ALTER TABLE user_meme_preferences DROP COLUMN IF EXISTS email_notifications;
ALTER TABLE user_meme_preferences DROP COLUMN IF EXISTS push_notifications;
ALTER TABLE user_meme_preferences DROP COLUMN IF EXISTS notification_frequency;

-- =====================================================
-- DROP COLUMNS FROM USER_MEME_HISTORY TABLE
-- =====================================================

-- Drop enhanced analytics columns
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS view_duration_seconds;
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS scroll_depth_percentage;
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS device_type;
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS browser_type;
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS screen_resolution;
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS connection_speed;
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS user_agent;

-- Drop conversion tracking columns
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS conversion_type;
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS conversion_value;
ALTER TABLE user_meme_history DROP COLUMN IF EXISTS conversion_metadata;

-- =====================================================
-- ROLLBACK MIGRATION TRACKING
-- =====================================================

-- Remove migration record
DELETE FROM schema_migrations WHERE version = '015_meme_feature_enhancements';

-- =====================================================
-- ROLLBACK COMPLETION
-- =====================================================

-- Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'Rollback of meme feature enhancements completed successfully';
END $$;
