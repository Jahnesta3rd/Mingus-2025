-- =====================================================
-- MIGRATION ROLLBACK: Create Assessment System Tables
-- =====================================================
-- Description: Rollback for comprehensive assessment functionality
-- Revision: 016_create_assessment_system_tables_rollback
-- Date: 2025-01-XX
-- Author: MINGUS Development Team

-- =====================================================
-- DROP VIEWS
-- =====================================================

DROP VIEW IF EXISTS user_assessment_history;
DROP VIEW IF EXISTS assessment_completion_stats;

-- =====================================================
-- DROP FUNCTIONS
-- =====================================================

DROP FUNCTION IF EXISTS determine_risk_level(INTEGER, assessment_type);
DROP FUNCTION IF EXISTS calculate_assessment_score(JSONB, JSONB);

-- =====================================================
-- DROP TRIGGERS
-- =====================================================

DROP TRIGGER IF EXISTS update_assessment_results_updated_at ON assessment_results;
DROP TRIGGER IF EXISTS update_user_assessments_updated_at ON user_assessments;
DROP TRIGGER IF EXISTS update_assessments_updated_at ON assessments;

-- =====================================================
-- DROP TABLES (in reverse order due to foreign key constraints)
-- =====================================================

DROP TABLE IF EXISTS assessment_results CASCADE;
DROP TABLE IF EXISTS user_assessments CASCADE;
DROP TABLE IF EXISTS assessments CASCADE;

-- =====================================================
-- DROP ENUM TYPES
-- =====================================================

DROP TYPE IF EXISTS risk_level_type CASCADE;
DROP TYPE IF EXISTS assessment_type CASCADE;

-- =====================================================
-- ROLLBACK COMPLETION
-- =====================================================

-- Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 016_create_assessment_system_tables rollback completed successfully';
    RAISE NOTICE 'Dropped tables: assessment_results, user_assessments, assessments';
    RAISE NOTICE 'Dropped types: risk_level_type, assessment_type';
    RAISE NOTICE 'Dropped views: assessment_completion_stats, user_assessment_history';
    RAISE NOTICE 'Dropped functions: calculate_assessment_score, determine_risk_level';
END $$;
