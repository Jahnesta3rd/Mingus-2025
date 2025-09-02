-- AI Calculator Integration Migration
-- Add new tables for AI calculator integration with existing Mingus application

-- Create AI User Profile Extension table
CREATE TABLE IF NOT EXISTS ai_user_profile_extensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    latest_ai_assessment_id UUID REFERENCES ai_job_assessments(id) ON DELETE SET NULL,
    overall_risk_level VARCHAR(20),
    automation_score INTEGER,
    augmentation_score INTEGER,
    career_risk_alerts_enabled BOOLEAN DEFAULT TRUE,
    ai_skill_development_goals JSONB DEFAULT '[]',
    career_transition_plans JSONB DEFAULT '[]',
    risk_mitigation_strategies JSONB DEFAULT '[]',
    ai_career_insights_enabled BOOLEAN DEFAULT TRUE,
    industry_risk_monitoring BOOLEAN DEFAULT TRUE,
    skill_gap_analysis_enabled BOOLEAN DEFAULT TRUE,
    career_advancement_tracking BOOLEAN DEFAULT TRUE,
    ai_assessment_completed BOOLEAN DEFAULT FALSE,
    ai_assessment_completion_date TIMESTAMP WITH TIME ZONE,
    ai_onboarding_step VARCHAR(50) DEFAULT 'not_started',
    ai_career_email_frequency VARCHAR(20) DEFAULT 'weekly',
    ai_career_sms_enabled BOOLEAN DEFAULT FALSE,
    ai_career_push_notifications BOOLEAN DEFAULT TRUE,
    ai_assessment_count INTEGER DEFAULT 0,
    last_ai_assessment_date TIMESTAMP WITH TIME ZONE,
    ai_career_insights_engagement_score DECIMAL(3, 2) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Create AI Onboarding Progress table
CREATE TABLE IF NOT EXISTS ai_onboarding_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ai_assessment_introduced BOOLEAN DEFAULT FALSE,
    ai_assessment_started BOOLEAN DEFAULT FALSE,
    ai_assessment_completed BOOLEAN DEFAULT FALSE,
    ai_insights_explained BOOLEAN DEFAULT FALSE,
    ai_career_plan_created BOOLEAN DEFAULT FALSE,
    introduction_date TIMESTAMP WITH TIME ZONE,
    started_date TIMESTAMP WITH TIME ZONE,
    completed_date TIMESTAMP WITH TIME ZONE,
    insights_explained_date TIMESTAMP WITH TIME ZONE,
    career_plan_date TIMESTAMP WITH TIME ZONE,
    user_opted_in BOOLEAN,
    skip_reason VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_user_profile_extensions_user_id ON ai_user_profile_extensions(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_user_profile_extensions_risk_level ON ai_user_profile_extensions(overall_risk_level);
CREATE INDEX IF NOT EXISTS idx_ai_user_profile_extensions_assessment_completed ON ai_user_profile_extensions(ai_assessment_completed);

CREATE INDEX IF NOT EXISTS idx_ai_onboarding_progress_user_id ON ai_onboarding_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_onboarding_progress_completed ON ai_onboarding_progress(ai_assessment_completed);

-- Add constraints
ALTER TABLE ai_user_profile_extensions 
ADD CONSTRAINT valid_risk_level CHECK (overall_risk_level IN ('low', 'medium', 'high'));

ALTER TABLE ai_user_profile_extensions 
ADD CONSTRAINT valid_automation_score CHECK (automation_score >= 0 AND automation_score <= 100);

ALTER TABLE ai_user_profile_extensions 
ADD CONSTRAINT valid_augmentation_score CHECK (augmentation_score >= 0 AND augmentation_score <= 100);

ALTER TABLE ai_user_profile_extensions 
ADD CONSTRAINT valid_onboarding_step CHECK (ai_onboarding_step IN ('not_started', 'optional', 'completed', 'skipped'));

ALTER TABLE ai_user_profile_extensions 
ADD CONSTRAINT valid_email_frequency CHECK (ai_career_email_frequency IN ('daily', 'weekly', 'monthly', 'never'));

-- Update existing ai_job_assessments table to add user_id foreign key if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'ai_job_assessments' 
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE ai_job_assessments ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_ai_job_assessments_user_id ON ai_job_assessments(user_id);
    END IF;
END $$;

-- Add new conversion types to existing ai_calculator_conversions table
-- (Assuming the table already exists from previous AI calculator implementation)

-- Insert sample data for testing (optional)
-- INSERT INTO ai_user_profile_extensions (user_id, overall_risk_level, automation_score, augmentation_score)
-- SELECT id, 'medium', 45, 60 FROM users LIMIT 5;

-- Create views for analytics
CREATE OR REPLACE VIEW ai_calculator_user_analytics AS
SELECT 
    u.id as user_id,
    u.email,
    u.full_name,
    aipe.overall_risk_level,
    aipe.automation_score,
    aipe.augmentation_score,
    aipe.ai_assessment_completed,
    aipe.ai_assessment_count,
    aipe.ai_career_insights_engagement_score,
    aiop.ai_assessment_introduced,
    aiop.ai_assessment_started,
    aiop.ai_assessment_completed as onboarding_completed,
    aiop.user_opted_in,
    COUNT(acc.id) as total_conversions,
    SUM(acc.conversion_revenue) as total_revenue
FROM users u
LEFT JOIN ai_user_profile_extensions aipe ON u.id = aipe.user_id
LEFT JOIN ai_onboarding_progress aiop ON u.id = aiop.user_id
LEFT JOIN ai_calculator_conversions acc ON aipe.latest_ai_assessment_id = acc.assessment_id
GROUP BY u.id, u.email, u.full_name, aipe.overall_risk_level, aipe.automation_score, 
         aipe.augmentation_score, aipe.ai_assessment_completed, aipe.ai_assessment_count,
         aipe.ai_career_insights_engagement_score, aiop.ai_assessment_introduced,
         aiop.ai_assessment_started, aiop.ai_assessment_completed, aiop.user_opted_in;

-- Create view for conversion funnel analysis
CREATE OR REPLACE VIEW ai_calculator_conversion_funnel AS
SELECT 
    'assessments_started' as funnel_step,
    COUNT(*) as count,
    1 as step_order
FROM ai_job_assessments
WHERE created_at >= NOW() - INTERVAL '30 days'

UNION ALL

SELECT 
    'assessments_completed' as funnel_step,
    COUNT(*) as count,
    2 as step_order
FROM ai_job_assessments
WHERE completed_at IS NOT NULL 
AND created_at >= NOW() - INTERVAL '30 days'

UNION ALL

SELECT 
    'emails_sent' as funnel_step,
    COUNT(*) as count,
    3 as step_order
FROM ai_calculator_conversions
WHERE conversion_type = 'email_sent'
AND created_at >= NOW() - INTERVAL '30 days'

UNION ALL

SELECT 
    'career_plans_purchased' as funnel_step,
    COUNT(*) as count,
    4 as step_order
FROM ai_calculator_conversions
WHERE conversion_type = 'paid_upgrade'
AND created_at >= NOW() - INTERVAL '30 days';

-- Add comments for documentation
COMMENT ON TABLE ai_user_profile_extensions IS 'AI Job Risk Profile Extension for existing users - extends user profiles with AI assessment data';
COMMENT ON TABLE ai_onboarding_progress IS 'AI Assessment Onboarding Progress Tracking - tracks user progress through AI calculator onboarding';
COMMENT ON VIEW ai_calculator_user_analytics IS 'Analytics view combining user data with AI calculator performance metrics';
COMMENT ON VIEW ai_calculator_conversion_funnel IS 'Conversion funnel analysis for AI calculator user journey';

-- Grant permissions (adjust as needed for your database setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ai_user_profile_extensions TO mingus_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ai_onboarding_progress TO mingus_app;
-- GRANT SELECT ON ai_calculator_user_analytics TO mingus_app;
-- GRANT SELECT ON ai_calculator_conversion_funnel TO mingus_app;
