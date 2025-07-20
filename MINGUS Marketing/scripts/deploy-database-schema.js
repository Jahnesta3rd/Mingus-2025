#!/usr/bin/env node

/**
 * Database Schema Deployment Script
 * 
 * This script provides the SQL commands to deploy the marketing funnel
 * database schema to your Supabase project.
 */

const fs = require('fs')
const path = require('path')

console.log('🗄️  Database Schema Deployment')
console.log('==============================')

// Read the schema file
const schemaFile = path.join(__dirname, '..', 'supabase-schema-clean.sql')

if (!fs.existsSync(schemaFile)) {
  console.log('❌ Schema file not found:', schemaFile)
  process.exit(1)
}

const schema = fs.readFileSync(schemaFile, 'utf8')

console.log('✅ Schema file found')
console.log('📋 Schema contents:')
console.log('==================')
console.log(schema)
console.log('==================')

console.log('\n🎯 Deployment Instructions')
console.log('=========================')

console.log('1️⃣  Open your Supabase Dashboard:')
console.log('   https://supabase.com/dashboard/project/wiemjrvxlqkpbsukdqnb')

console.log('\n2️⃣  Navigate to SQL Editor:')
console.log('   - Click on "SQL Editor" in the left sidebar')
console.log('   - Click "New query"')

console.log('\n3️⃣  Copy and paste the schema above into the SQL editor')

console.log('\n4️⃣  Click "Run" to execute the schema')

console.log('\n5️⃣  Verify the tables were created:')
console.log('   - Go to "Table Editor" in the left sidebar')
console.log('   - You should see: leads, email_logs, email_templates')

console.log('\n6️⃣  Test the deployment:')
console.log('   node scripts/test-database-access.js')

console.log('\n📋 Required Tables:')
console.log('==================')
console.log('✅ leads - Store lead information and assessment results')
console.log('✅ email_logs - Track email automation events')
console.log('✅ email_templates - Store email templates')

console.log('\n🔧 Alternative: Manual Deployment')
console.log('===============================')
console.log('If you prefer to run the SQL manually, here are the key commands:')

const keyCommands = `
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create leads table
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
  lead_source VARCHAR(100),
  utm_source VARCHAR(100),
  utm_medium VARCHAR(100),
  utm_campaign VARCHAR(100),
  utm_term VARCHAR(100),
  utm_content VARCHAR(100),
  contact_method VARCHAR(50) DEFAULT 'email',
  beta_interest BOOLEAN DEFAULT FALSE,
  status VARCHAR(50) DEFAULT 'active'
);

-- Create email_logs table
CREATE TABLE IF NOT EXISTS email_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
  email_type VARCHAR(50) NOT NULL,
  subject VARCHAR(500) NOT NULL,
  body TEXT NOT NULL,
  sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  status VARCHAR(50) DEFAULT 'sent',
  external_id VARCHAR(255),
  opened_at TIMESTAMP WITH TIME ZONE,
  clicked_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT
);

-- Create email_templates table
CREATE TABLE IF NOT EXISTS email_templates (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  template_name VARCHAR(100) NOT NULL,
  subject VARCHAR(500) NOT NULL,
  body TEXT NOT NULL,
  email_type VARCHAR(50) NOT NULL,
  segment VARCHAR(100),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_segment ON leads(segment);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_email_logs_lead_id ON email_logs(lead_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at);

-- Enable RLS
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;

-- Create policies for marketing funnel
CREATE POLICY "Marketing funnel can insert leads" ON leads
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Marketing funnel can read leads" ON leads
  FOR SELECT USING (true);

CREATE POLICY "Marketing funnel can update leads" ON leads
  FOR UPDATE USING (true);

CREATE POLICY "Marketing funnel can insert email logs" ON email_logs
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Marketing funnel can read email logs" ON email_logs
  FOR SELECT USING (true);

CREATE POLICY "Marketing funnel can read email templates" ON email_templates
  FOR SELECT USING (true);
`

console.log(keyCommands)

console.log('\n✅ Schema deployment ready!')
console.log('   Follow the instructions above to deploy to your Supabase project.') 