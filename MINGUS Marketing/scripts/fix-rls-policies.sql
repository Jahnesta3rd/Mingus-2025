-- Fix RLS Policies for Marketing Funnel
-- Run this in your Supabase SQL Editor after deploying the main schema

-- Drop existing policies that are too restrictive
DROP POLICY IF EXISTS "Leads are viewable by authenticated users" ON leads;
DROP POLICY IF EXISTS "Leads can be updated by authenticated users" ON leads;
DROP POLICY IF EXISTS "Email logs are viewable by authenticated users" ON email_logs;
DROP POLICY IF EXISTS "Email logs can be inserted by authenticated users" ON email_logs;
DROP POLICY IF EXISTS "Assessment responses are viewable by authenticated users" ON assessment_responses;
DROP POLICY IF EXISTS "Email templates are viewable by authenticated users" ON email_templates;

-- Create new policies that allow marketing funnel operations
-- Leads table policies
CREATE POLICY "Marketing funnel can insert leads" ON leads
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Marketing funnel can read leads" ON leads
    FOR SELECT USING (true);

CREATE POLICY "Marketing funnel can update leads" ON leads
    FOR UPDATE USING (true);

-- Email logs table policies
CREATE POLICY "Marketing funnel can insert email logs" ON email_logs
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Marketing funnel can read email logs" ON email_logs
    FOR SELECT USING (true);

-- Assessment responses table policies
CREATE POLICY "Marketing funnel can insert assessment responses" ON assessment_responses
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Marketing funnel can read assessment responses" ON assessment_responses
    FOR SELECT USING (true);

-- Email templates table policies
CREATE POLICY "Marketing funnel can read email templates" ON email_templates
    FOR SELECT USING (true);

-- Assessment questions table policies (already public, but ensure it's correct)
CREATE POLICY "Marketing funnel can read assessment questions" ON assessment_questions
    FOR SELECT USING (true);

-- Verify policies are created
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies 
WHERE tablename IN ('leads', 'email_logs', 'assessment_responses', 'email_templates', 'assessment_questions')
ORDER BY tablename, policyname; 