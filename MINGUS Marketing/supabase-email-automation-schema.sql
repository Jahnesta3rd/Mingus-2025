-- Email Automation Database Schema for Ratchet Money
-- This schema extends the existing assessment system with email automation capabilities

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Enhanced Leads Table with Email Automation Fields
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    segment VARCHAR(100) NOT NULL DEFAULT 'stress-free',
    score INTEGER NOT NULL DEFAULT 0,
    product_tier VARCHAR(100) NOT NULL DEFAULT 'Budget ($10)',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed BOOLEAN DEFAULT FALSE,
    assessment_completed BOOLEAN DEFAULT FALSE,
    assessment_answers JSONB DEFAULT '{}',
    email_sequence_sent INTEGER DEFAULT 0,
    last_email_sent TIMESTAMP WITH TIME ZONE,
    
    -- Email Preferences
    email_preferences JSONB DEFAULT '{
        "marketing": true,
        "transactional": true,
        "frequency": "weekly"
    }',
    
    -- Engagement Metrics
    engagement_metrics JSONB DEFAULT '{
        "emails_opened": 0,
        "emails_clicked": 0,
        "last_engaged": null,
        "total_emails_sent": 0,
        "open_rate": 0,
        "click_rate": 0
    }',
    
    -- A/B Testing
    ab_test_group VARCHAR(100),
    ab_test_variant VARCHAR(100),
    
    -- Lead Source and Attribution
    lead_source VARCHAR(100),
    utm_source VARCHAR(100),
    utm_medium VARCHAR(100),
    utm_campaign VARCHAR(100),
    utm_term VARCHAR(100),
    utm_content VARCHAR(100),
    
    -- Contact Information
    contact_method VARCHAR(50) DEFAULT 'email',
    beta_interest BOOLEAN DEFAULT FALSE,
    
    -- Status and Tags
    status VARCHAR(50) DEFAULT 'active',
    tags TEXT[],
    
    -- Verification
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP WITH TIME ZONE
);

-- 2. Email Logs Table for Tracking All Email Communications
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    email_type VARCHAR(100) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent',
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    
    -- Template and Campaign Tracking
    template_id VARCHAR(100),
    campaign_id VARCHAR(100),
    sequence_step INTEGER,
    
    -- Delivery and Bounce Information
    delivered_at TIMESTAMP WITH TIME ZONE,
    bounced_at TIMESTAMP WITH TIME ZONE,
    bounce_reason TEXT,
    
    -- Click Tracking
    clicks JSONB DEFAULT '[]',
    opens JSONB DEFAULT '[]',
    
    -- A/B Testing
    ab_test_group VARCHAR(100),
    ab_test_variant VARCHAR(100),
    
    -- Performance Metrics
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    unsubscribed BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Assessment Questions Table
CREATE TABLE IF NOT EXISTS assessment_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) NOT NULL, -- 'multiple_choice', 'scale', 'text', 'number'
    options JSONB, -- For multiple choice questions
    category VARCHAR(100) NOT NULL,
    weight INTEGER DEFAULT 1,
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Assessment Responses Table
CREATE TABLE IF NOT EXISTS assessment_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    question_id UUID REFERENCES assessment_questions(id) ON DELETE CASCADE,
    response TEXT NOT NULL,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(lead_id, question_id)
);

-- 5. Email Templates Table
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    template_type VARCHAR(100) NOT NULL, -- 'welcome', 'assessment_results', 'follow_up', 'product_launch'
    segment VARCHAR(100), -- NULL for universal templates
    is_active BOOLEAN DEFAULT TRUE,
    variables TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Template Metadata
    description TEXT,
    author VARCHAR(255),
    version VARCHAR(50) DEFAULT '1.0',
    
    -- A/B Testing
    ab_test_enabled BOOLEAN DEFAULT FALSE,
    ab_test_variants JSONB DEFAULT '[]'
);

-- 6. Email Campaigns Table
CREATE TABLE IF NOT EXISTS email_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_id UUID REFERENCES email_templates(id),
    trigger_type VARCHAR(100) NOT NULL, -- 'immediate', 'delayed', 'sequence', 'event_based'
    delay_hours INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Campaign Metrics
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    open_rate DECIMAL(5,2) DEFAULT 0,
    click_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Campaign Settings
    target_segment VARCHAR(100),
    target_criteria JSONB DEFAULT '{}',
    send_time TIME DEFAULT '09:00:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Sequence Settings
    sequence_order INTEGER DEFAULT 0,
    parent_campaign_id UUID REFERENCES email_campaigns(id),
    
    -- A/B Testing
    ab_test_enabled BOOLEAN DEFAULT FALSE,
    ab_test_variants JSONB DEFAULT '[]'
);

-- 7. A/B Tests Table
CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    test_type VARCHAR(100) NOT NULL, -- 'email_subject', 'email_content', 'landing_page', 'cta_button'
    variants JSONB NOT NULL, -- Array of test variants
    traffic_split JSONB NOT NULL, -- Percentage allocation for each variant
    is_active BOOLEAN DEFAULT TRUE,
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Test Settings
    confidence_level DECIMAL(3,2) DEFAULT 0.95,
    minimum_sample_size INTEGER DEFAULT 100,
    primary_metric VARCHAR(100) DEFAULT 'open_rate',
    
    -- Results
    winner_variant VARCHAR(100),
    statistical_significance BOOLEAN DEFAULT FALSE,
    p_value DECIMAL(10,8),
    results_summary JSONB DEFAULT '{}'
);

-- 8. Email Sequences Table
CREATE TABLE IF NOT EXISTS email_sequences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Sequence Settings
    trigger_event VARCHAR(100), -- 'signup', 'assessment_complete', 'purchase', 'custom'
    target_segment VARCHAR(100),
    max_emails INTEGER DEFAULT 5,
    delay_between_emails_hours INTEGER DEFAULT 24
);

-- 9. Sequence Steps Table
CREATE TABLE IF NOT EXISTS sequence_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sequence_id UUID REFERENCES email_sequences(id) ON DELETE CASCADE,
    template_id UUID REFERENCES email_templates(id),
    step_order INTEGER NOT NULL,
    delay_hours INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Step Conditions
    conditions JSONB DEFAULT '{}', -- Conditions for sending this step
    fallback_template_id UUID REFERENCES email_templates(id)
);

-- 10. Lead Tags Table for Advanced Segmentation
CREATE TABLE IF NOT EXISTS lead_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    tag_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(lead_id, tag_name)
);

-- 11. Email Events Table for Detailed Tracking
CREATE TABLE IF NOT EXISTS email_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_log_id UUID REFERENCES email_logs(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL, -- 'sent', 'delivered', 'opened', 'clicked', 'bounced', 'unsubscribed'
    event_data JSONB DEFAULT '{}',
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- User Agent and Device Information
    user_agent TEXT,
    ip_address INET,
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100)
);

-- 12. Conversion Tracking Table
CREATE TABLE IF NOT EXISTS conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    conversion_type VARCHAR(100) NOT NULL, -- 'purchase', 'signup', 'download', 'consultation'
    conversion_value DECIMAL(10,2),
    conversion_data JSONB DEFAULT '{}',
    attributed_email_log_id UUID REFERENCES email_logs(id),
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Attribution
    attribution_model VARCHAR(50) DEFAULT 'last_touch',
    attribution_window_days INTEGER DEFAULT 30
);

-- 13. Email Preferences Table for Detailed Preference Management
CREATE TABLE IF NOT EXISTS email_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    preference_type VARCHAR(100) NOT NULL, -- 'frequency', 'content_type', 'unsubscribe_reason'
    preference_value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 14. Email Suppression List Table
CREATE TABLE IF NOT EXISTS email_suppressions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    suppression_type VARCHAR(100) NOT NULL, -- 'bounce', 'complaint', 'unsubscribe', 'manual'
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(email, suppression_type)
);

-- Indexes for Performance
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_segment ON leads(segment);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_ab_test_group ON leads(ab_test_group);

CREATE INDEX idx_email_logs_lead_id ON email_logs(lead_id);
CREATE INDEX idx_email_logs_email_type ON email_logs(email_type);
CREATE INDEX idx_email_logs_sent_at ON email_logs(sent_at);
CREATE INDEX idx_email_logs_status ON email_logs(status);
CREATE INDEX idx_email_logs_campaign_id ON email_logs(campaign_id);

CREATE INDEX idx_assessment_responses_lead_id ON assessment_responses(lead_id);
CREATE INDEX idx_assessment_responses_question_id ON assessment_responses(question_id);

CREATE INDEX idx_email_templates_type ON email_templates(template_type);
CREATE INDEX idx_email_templates_segment ON email_templates(segment);
CREATE INDEX idx_email_templates_active ON email_templates(is_active);

CREATE INDEX idx_email_campaigns_trigger_type ON email_campaigns(trigger_type);
CREATE INDEX idx_email_campaigns_active ON email_campaigns(is_active);
CREATE INDEX idx_email_campaigns_target_segment ON email_campaigns(target_segment);

CREATE INDEX idx_ab_tests_active ON ab_tests(is_active);
CREATE INDEX idx_ab_tests_type ON ab_tests(test_type);

CREATE INDEX idx_email_events_email_log_id ON email_events(email_log_id);
CREATE INDEX idx_email_events_type ON email_events(event_type);
CREATE INDEX idx_email_events_occurred_at ON email_events(occurred_at);

CREATE INDEX idx_conversions_lead_id ON conversions(lead_id);
CREATE INDEX idx_conversions_type ON conversions(conversion_type);
CREATE INDEX idx_conversions_occurred_at ON conversions(occurred_at);

CREATE INDEX idx_lead_tags_lead_id ON lead_tags(lead_id);
CREATE INDEX idx_lead_tags_name ON lead_tags(tag_name);

CREATE INDEX idx_email_suppressions_email ON email_suppressions(email);
CREATE INDEX idx_email_suppressions_type ON email_suppressions(suppression_type);

-- Triggers for Updated At Timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assessment_questions_updated_at BEFORE UPDATE ON assessment_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_preferences_updated_at BEFORE UPDATE ON email_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate engagement metrics
CREATE OR REPLACE FUNCTION update_lead_engagement_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update engagement metrics when email events occur
    IF NEW.event_type IN ('opened', 'clicked') THEN
        UPDATE leads 
        SET engagement_metrics = jsonb_set(
            engagement_metrics,
            '{emails_opened}',
            to_jsonb(
                (engagement_metrics->>'emails_opened')::int + 
                CASE WHEN NEW.event_type = 'opened' THEN 1 ELSE 0 END
            )
        ) || jsonb_set(
            engagement_metrics,
            '{emails_clicked}',
            to_jsonb(
                (engagement_metrics->>'emails_clicked')::int + 
                CASE WHEN NEW.event_type = 'clicked' THEN 1 ELSE 0 END
            )
        ) || jsonb_set(
            engagement_metrics,
            '{last_engaged}',
            to_jsonb(NOW())
        )
        WHERE id = (
            SELECT lead_id FROM email_logs WHERE id = NEW.email_log_id
        );
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_engagement_on_email_event AFTER INSERT ON email_events
    FOR EACH ROW EXECUTE FUNCTION update_lead_engagement_metrics();

-- Function to automatically tag leads based on behavior
CREATE OR REPLACE FUNCTION auto_tag_leads()
RETURNS TRIGGER AS $$
BEGIN
    -- Tag based on email opens
    IF NEW.event_type = 'opened' THEN
        INSERT INTO lead_tags (lead_id, tag_name, tag_value)
        SELECT 
            l.id,
            'email_engaged',
            'opened_' || NEW.email_log_id
        FROM leads l
        JOIN email_logs el ON l.id = el.lead_id
        WHERE el.id = NEW.email_log_id
        ON CONFLICT (lead_id, tag_name) DO NOTHING;
    END IF;
    
    -- Tag based on clicks
    IF NEW.event_type = 'clicked' THEN
        INSERT INTO lead_tags (lead_id, tag_name, tag_value)
        SELECT 
            l.id,
            'email_clicked',
            'clicked_' || NEW.email_log_id
        FROM leads l
        JOIN email_logs el ON l.id = el.lead_id
        WHERE el.id = NEW.email_log_id
        ON CONFLICT (lead_id, tag_name) DO NOTHING;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER auto_tag_on_email_event AFTER INSERT ON email_events
    FOR EACH ROW EXECUTE FUNCTION auto_tag_leads();

-- Row Level Security (RLS) Policies
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_tags ENABLE ROW LEVEL SECURITY;

-- RLS Policies for leads
CREATE POLICY "Users can view their own lead data" ON leads
    FOR SELECT USING (email = current_setting('request.jwt.claims', true)::json->>'email');

CREATE POLICY "Users can update their own lead data" ON leads
    FOR UPDATE USING (email = current_setting('request.jwt.claims', true)::json->>'email');

CREATE POLICY "Users can insert their own lead data" ON leads
    FOR INSERT WITH CHECK (email = current_setting('request.jwt.claims', true)::json->>'email');

-- RLS Policies for email_logs
CREATE POLICY "Users can view their own email logs" ON email_logs
    FOR SELECT USING (
        lead_id IN (
            SELECT id FROM leads 
            WHERE email = current_setting('request.jwt.claims', true)::json->>'email'
        )
    );

-- RLS Policies for assessment_responses
CREATE POLICY "Users can view their own assessment responses" ON assessment_responses
    FOR SELECT USING (
        lead_id IN (
            SELECT id FROM leads 
            WHERE email = current_setting('request.jwt.claims', true)::json->>'email'
        )
    );

-- Insert sample data for testing
INSERT INTO assessment_questions (question_text, question_type, options, category, weight, order_index) VALUES
('How do you typically feel about your financial situation?', 'multiple_choice', '["Very stressed", "Somewhat stressed", "Neutral", "Somewhat confident", "Very confident"]', 'emotional_state', 2, 1),
('How often do you check your bank account?', 'multiple_choice', '["Daily", "Weekly", "Monthly", "Rarely", "Never"]', 'financial_awareness', 1, 2),
('What is your primary financial goal?', 'multiple_choice', '["Pay off debt", "Save for emergency fund", "Invest for retirement", "Buy a home", "Start a business"]', 'financial_goals', 3, 3),
('How do you typically make financial decisions?', 'multiple_choice', '["Based on emotions", "After careful research", "Following advice from others", "Impulsively", "I avoid making decisions"]', 'decision_making', 2, 4),
('What is your current income level?', 'multiple_choice', '["Under $30k", "$30k-$50k", "$50k-$75k", "$75k-$100k", "Over $100k"]', 'income', 1, 5);

-- Insert sample email templates
INSERT INTO email_templates (id, name, subject, body, template_type, segment, variables) VALUES
('welcome-template', 'Welcome Email', 'Welcome to Ratchet Money, {{name}}!', '<h1>Welcome {{name}}!</h1><p>Thank you for joining Ratchet Money.</p>', 'welcome', NULL, ARRAY['name']),
('results-template', 'Assessment Results', 'Your Financial Profile: {{segment}}', '<h1>Your Results</h1><p>You are a {{segment}} with a score of {{score}}.</p>', 'assessment_results', NULL, ARRAY['name', 'segment', 'score']);

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated; 