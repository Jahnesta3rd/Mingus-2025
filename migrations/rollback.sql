-- =====================================================
-- Rollback Script for Mingus Meme Database
-- WARNING: This will remove all data and tables
-- Use only in emergency situations
-- =====================================================

-- WARNING: This script will DROP ALL TABLES
-- Make sure you have a backup before running this!

-- Drop all tables in reverse order of creation
DROP TABLE IF EXISTS daily_analytics_summary;
DROP TABLE IF EXISTS analytics_alerts;
DROP TABLE IF EXISTS user_engagement_sessions;
DROP TABLE IF EXISTS category_performance;
DROP TABLE IF EXISTS meme_performance_metrics;
DROP TABLE IF EXISTS user_demographics;
DROP TABLE IF EXISTS meme_analytics_events;
DROP TABLE IF EXISTS user_mood_data;
DROP TABLE IF EXISTS user_meme_history;
DROP TABLE IF EXISTS memes;
DROP TABLE IF EXISTS migrations;

-- Drop all indexes
DROP INDEX IF EXISTS idx_daily_summary_date;
DROP INDEX IF EXISTS idx_alerts_created;
DROP INDEX IF EXISTS idx_alerts_resolved;
DROP INDEX IF EXISTS idx_alerts_severity;
DROP INDEX IF EXISTS idx_alerts_type;
DROP INDEX IF EXISTS idx_engagement_sessions_start;
DROP INDEX IF EXISTS idx_engagement_sessions_session_id;
DROP INDEX IF EXISTS idx_engagement_sessions_user_id;
DROP INDEX IF EXISTS idx_category_performance_category_date;
DROP INDEX IF EXISTS idx_category_performance_date;
DROP INDEX IF EXISTS idx_category_performance_category;
DROP INDEX IF EXISTS idx_performance_metrics_meme_date;
DROP INDEX IF EXISTS idx_performance_metrics_date;
DROP INDEX IF EXISTS idx_performance_metrics_meme_id;
DROP INDEX IF EXISTS idx_analytics_events_meme_timestamp;
DROP INDEX IF EXISTS idx_analytics_events_user_timestamp;
DROP INDEX IF EXISTS idx_analytics_events_type;
DROP INDEX IF EXISTS idx_analytics_events_timestamp;
DROP INDEX IF EXISTS idx_analytics_events_meme_id;
DROP INDEX IF EXISTS idx_analytics_events_user_id;
DROP INDEX IF EXISTS idx_user_mood_data_user_timestamp;
DROP INDEX IF EXISTS idx_user_mood_data_mood_score;
DROP INDEX IF EXISTS idx_user_mood_data_timestamp;
DROP INDEX IF EXISTS idx_user_mood_data_user_id;
DROP INDEX IF EXISTS idx_user_meme_history_user_viewed;
DROP INDEX IF EXISTS idx_user_meme_history_viewed_at;
DROP INDEX IF EXISTS idx_user_meme_history_meme_id;
DROP INDEX IF EXISTS idx_user_meme_history_user_id;
DROP INDEX IF EXISTS idx_memes_created_at;
DROP INDEX IF EXISTS idx_memes_category_active;
DROP INDEX IF EXISTS idx_memes_active;
DROP INDEX IF EXISTS idx_memes_category;

-- Drop triggers
DROP TRIGGER IF EXISTS update_memes_timestamp;
DROP TRIGGER IF EXISTS update_performance_metrics_after_event;

-- Vacuum database to reclaim space
VACUUM;
