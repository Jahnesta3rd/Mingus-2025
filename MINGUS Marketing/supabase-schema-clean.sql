-- Clean Supabase Database Schema for MINGUS Assessment Workflow
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE user_segment AS ENUM (
    'stress-free',
    'relationship-spender',
    'emotional-manager',
    'crisis-mode'
);

CREATE TYPE product_tier AS ENUM (
    'Budget ($10)',
    'Mid-tier ($20)',
    'Professional ($50)'
);

CREATE TYPE email_type AS ENUM (
    'confirmation',
    'assessment_results',
    'follow_up'
);

CREATE TYPE email_status AS ENUM (
    'sent',
    'delivered',
    'failed'
);

-- Leads table to store user information and assessment results
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    segment user_segment,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    product_tier product_tier,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed BOOLEAN DEFAULT FALSE,
    assessment_completed BOOLEAN DEFAULT FALSE,
    assessment_answers JSONB,
    email_sequence_sent INTEGER DEFAULT 0,
    last_email_sent TIMESTAMP WITH TIME ZONE,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    assessment_started_at TIMESTAMP WITH TIME ZONE,
    assessment_completed_at TIMESTAMP WITH TIME ZONE
);

-- Email logs table to track all emails sent
CREATE TABLE email_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    email_type email_type NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status email_status DEFAULT 'sent',
    external_id VARCHAR(255), -- For email service tracking
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- Assessment questions table (for future flexibility)
CREATE TABLE assessment_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id VARCHAR(50) UNIQUE NOT NULL,
    question_text TEXT NOT NULL,
    question_type VARCHAR(20) NOT NULL, -- 'radio', 'checkbox', 'rating', 'text', 'dropdown'
    options JSONB, -- For multiple choice questions
    points JSONB, -- Points for each option
    required BOOLEAN DEFAULT TRUE,
    order_index INTEGER NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Assessment responses table (detailed responses)
CREATE TABLE assessment_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    question_id VARCHAR(50) NOT NULL,
    response_value TEXT,
    response_points INTEGER,
    answered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email templates table
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(100) UNIQUE NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    variables JSONB, -- Template variables
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_segment ON leads(segment);
CREATE INDEX idx_leads_confirmed ON leads(confirmed);
CREATE INDEX idx_leads_assessment_completed ON leads(assessment_completed);
CREATE INDEX idx_email_logs_lead_id ON email_logs(lead_id);
CREATE INDEX idx_email_logs_sent_at ON email_logs(sent_at);
CREATE INDEX idx_email_logs_status ON email_logs(status);
CREATE INDEX idx_assessment_responses_lead_id ON assessment_responses(lead_id);
CREATE INDEX idx_assessment_questions_order ON assessment_questions(order_index);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assessment_questions_updated_at BEFORE UPDATE ON assessment_questions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;

-- Policies for leads table
CREATE POLICY "Leads are viewable by authenticated users" ON leads
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Leads can be inserted by anyone" ON leads
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Leads can be updated by authenticated users" ON leads
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Policies for email_logs table
CREATE POLICY "Email logs are viewable by authenticated users" ON email_logs
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Email logs can be inserted by authenticated users" ON email_logs
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Policies for assessment_responses table
CREATE POLICY "Assessment responses are viewable by authenticated users" ON assessment_responses
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Assessment responses can be inserted by anyone" ON assessment_responses
    FOR INSERT WITH CHECK (true);

-- Policies for assessment_questions table
CREATE POLICY "Assessment questions are viewable by everyone" ON assessment_questions
    FOR SELECT USING (true);

-- Policies for email_templates table
CREATE POLICY "Email templates are viewable by authenticated users" ON email_templates
    FOR SELECT USING (auth.role() = 'authenticated');

-- Insert default assessment questions
INSERT INTO assessment_questions (question_id, question_text, question_type, options, points, order_index) VALUES
('q1', 'How often do you lose sleep thinking about money?', 'radio',
 '[{"value":"never", "label": "Never (0 points)"}, {"value":"monthly", "label": "Once a month (1 point)"}, {"value": "weekly", "label":"Weekly (2 points)"}, {"value": "multiple_weekly", "label": "Multiple times per week (3 points)"}, {"value":"daily", "label": "Daily (4 points)"}]',
 '[0, 1, 2, 3, 4]', 1),

('q2', 'In the past month, how often have you spent money you didn''t plan to spend because of: (Select all that apply)?', 'checkbox',
 '[{"value":"impress_date","label": "Wanting to impress someone on a date (2 points)"}, {"value": "stress_shopping", "label": "Stress-shopping after an argument with family/partner (3 points)"}, {"value": "keep_up_friends","label": "Keeping up with friends'' social activities (2 points)"}, {"value":"guilt_family", "label": "Guilt purchases for family members (2 points)"}, {"value":"emotional_eating", "label":"Emotional eating/drinking after relationship stress (2 points)"}, {"value": "none","label": "None of the above (0 points)"}]',
 '[2, 3, 2, 2, 2, 0]', 2),

('q3', 'How comfortable are you discussing money with: (Rate 1-5: 1=Very Uncomfortable, 5=Very Comfortable)?', 'rating',
 '[{"value":"partner", "label": "Your romantic partner"}, {"value": "family", "label":"Your family"}, {"value":"friends", "label":"Close friends"}]',
 '[1, 2, 3, 4, 5]', 3),

('q4', 'When you''re stressed about money, who do you talk to?', 'radio',
 '[{"value":"partner", "label": "My partner/spouse"}, {"value": "family", "label": "Close family members"}, {"value":"friends","label": "Friends"}, {"value": "myself", "label": "I keep it to myself"}, {"value":"professional", "label":"A professional (therapist, financial advisor, etc.)"}]',
 '[1, 2, 3, 4, 5]', 4),

('q5', 'Which situation most often leads to unplanned spending?', 'radio',
 '[{"value": "work_stress","label":"After a stressful day at work"}, {"value": "argument", "label": "Following an argument with someone close to me"}, {"value": "lonely", "label": "When I''m feeling lonely or disconnected"}, {"value": "comparison", "label": "When I see others enjoying things I can''t afford"}, {"value": "celebration", "label":"When I''m trying to celebrate or connect with others"}]',
 '[2, 3, 3, 2, 2]', 5);

-- Insert default email templates
INSERT INTO email_templates (template_name, subject, body, variables) VALUES
('confirmation', 'Confirm Your Email - Start Your Money & Relationship Assessment',
 'Hi there!<br><br>Thanks for signing up for your personalized Money & Relationship Assessment. Click the link below to confirm your email and start your assessment:<br><br><a href="{{confirmation_link}}">Confirm Email & Start Assessment</a><br><br>This assessment will help you understand how your relationships impact your spending habits and provide personalized strategies for financial harmony.<br><br>Best regards,<br>The MINGUS Team',
 '{"confirmation_link": "string"}'),

('assessment_results_stress_free','Congratulations! You''re a Stress-Free Lover',
 'Hi {{first_name}},<br><br>Congratulations! Your assessment results show you have a healthy and balanced relationship with money and relationships.<br><br><strong>Your Type: Stress-Free Lover</strong><br><br>You''re doing amazing! Here are some ways to maintain and enhance your current success...<br><br>Best regards,<br>The MINGUS Team',
 '{"first_name": "string"}'),

('assessment_results_relationship_spender', 'You''re a Relationship Spender - Here''s How to Find Balance',
 'Hi {{first_name}},<br><br>Your assessment results show you''re aware of how relationships impact your spending, which is a great first step!<br><br><strong>Your Type: Relationship Spender</strong><br><br>Here are practical strategies to maintain your generosity while protecting your financial future...<br><br>Best regards,<br>The MINGUS Team',
 '{"first_name": "string"}'),

('assessment_results_emotional_manager', 'You''re an Emotional Money Manager - Let''s Build Better Habits',
 'Hi {{first_name}},<br><br>Your assessment results show that your emotions significantly influence your spending decisions. This is common and fixable!<br><br><strong>Your Type: Emotional Money Manager</strong><br><br>Here are proven strategies to recognize triggers and develop healthier coping mechanisms...<br><br>Best regards,<br>The MINGUS Team',
 '{"first_name": "string"}'),

('assessment_results_crisis_mode', 'You''re in Crisis Mode - Let''s Get You Back in Control',
 'Hi {{first_name}},<br><br>Your assessment results show that your relationship dynamics are creating significant financial stress. This is serious, but you''re taking the right step by seeking help.<br><br><strong>Your Type: Crisis Mode</strong><br><br>Here''s your immediate action plan...<br><br>Best regards,<br>The MINGUS Team',
 '{"first_name": "string"}');

-- Create functions for common operations
CREATE OR REPLACE FUNCTION calculate_user_segment(score INTEGER)
RETURNS user_segment AS $$
BEGIN
    IF score <= 16 THEN
        RETURN 'stress-free';
    ELSIF score <= 30 THEN
        RETURN 'relationship-spender';
    ELSIF score <= 45 THEN
        RETURN 'emotional-manager';
    ELSE
        RETURN 'crisis-mode';
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_product_tier(segment user_segment)
RETURNS product_tier AS $$
BEGIN
    CASE segment
        WHEN 'stress-free' THEN RETURN 'Budget ($10)';
        WHEN 'relationship-spender' THEN RETURN 'Mid-tier ($20)';
        WHEN 'emotional-manager' THEN RETURN 'Mid-tier ($20)';
        WHEN 'crisis-mode' THEN RETURN 'Professional ($50)';
        ELSE RETURN 'Budget ($10)';
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Function to update lead after assessment completion
CREATE OR REPLACE FUNCTION complete_assessment(
    lead_email VARCHAR,
    assessment_answers JSONB,
    total_score INTEGER
)
RETURNS UUID AS $$
DECLARE
    lead_id UUID;
    user_segment user_segment;
    product_tier product_tier;
BEGIN
    -- Get the lead
    SELECT id INTO lead_id FROM leads WHERE email = lead_email;
    
    IF lead_id IS NULL THEN
        RAISE EXCEPTION 'Lead not found with email: %', lead_email;
    END IF;
    
    -- Calculate segment and product tier
    user_segment := calculate_user_segment(total_score);
    product_tier := get_product_tier(user_segment);
    
    -- Update the lead
    UPDATE leads
    SET
        segment = user_segment,
        score = total_score,
        product_tier = product_tier,
        assessment_completed = TRUE,
        assessment_answers = assessment_answers,
        assessment_completed_at = NOW()
    WHERE id = lead_id;
    
    RETURN lead_id;
END;
$$ LANGUAGE plpgsql;