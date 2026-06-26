-- Mingus Reddit Engine — PostgreSQL schema
-- Safe to re-run: all objects use IF NOT EXISTS

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS communities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT,
    members INTEGER,
    posts_per_day FLOAT,
    growth_rate_3mo FLOAT,
    peak_day TEXT,
    peak_hour_et INTEGER,
    heat_score FLOAT,
    priority_tier TEXT,
    primary_domain TEXT,
    date_added TIMESTAMP DEFAULT NOW(),
    last_heat_check TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    source TEXT DEFAULT 'reddit',
    ig_handle TEXT,
    post_id TEXT UNIQUE NOT NULL,
    community_id UUID REFERENCES communities(id),
    author TEXT,
    title TEXT,
    body TEXT,
    url TEXT,
    created_at TIMESTAMP,
    ingested_at TIMESTAMP DEFAULT NOW(),
    domain_id TEXT,
    matched_keywords JSONB,
    pain_score INTEGER,
    readiness_score INTEGER,
    composite_score FLOAT,
    ai_summary TEXT,
    suggested_reply_angle TEXT,
    drafted_reply TEXT,
    notified BOOLEAN DEFAULT FALSE,
    responded BOOLEAN DEFAULT FALSE,
    response_upvotes INTEGER,
    response_got_dm BOOLEAN,
    lead_quality_rating INTEGER,
    promoted_to_ad_brief BOOLEAN DEFAULT FALSE,
    pipeline_stage TEXT DEFAULT 'prospect'
      CHECK (pipeline_stage IN (
        'prospect',
        'meeting_booked',
        'qualified',
        'offer_made',
        'decision_pending',
        'closed_won',
        'closed_lost'
      )),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ad_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_at TIMESTAMP DEFAULT NOW(),
    period_start DATE,
    period_end DATE,
    top_communities JSONB,
    top_keywords JSONB,
    top_domains JSONB,
    suggested_copy_angles JSONB,
    geo_targets JSONB,
    budget_allocation JSONB,
    status TEXT DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS ad_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID REFERENCES ad_briefs(id),
    campaign_type TEXT,
    targeting_value TEXT,
    impressions INTEGER,
    clicks INTEGER,
    ctr FLOAT,
    assessment_starts INTEGER,
    cost_per_lead FLOAT,
    date_recorded DATE
);

CREATE TABLE IF NOT EXISTS signal_library_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id TEXT,
    keyword_added TEXT,
    keyword_removed TEXT,
    reason TEXT,
    source TEXT,
    date TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_leads_ig_handle ON leads(ig_handle);
CREATE INDEX IF NOT EXISTS idx_leads_post_id ON leads(post_id);
CREATE INDEX IF NOT EXISTS idx_leads_composite ON leads(composite_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_notified ON leads(notified) WHERE notified = false;
CREATE INDEX IF NOT EXISTS idx_leads_community ON leads(community_id);
CREATE INDEX IF NOT EXISTS idx_leads_pipeline_stage ON leads(pipeline_stage);
CREATE INDEX IF NOT EXISTS idx_leads_updated_at ON leads(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_communities_heat ON communities(heat_score DESC);
CREATE INDEX IF NOT EXISTS idx_communities_tier ON communities(priority_tier);

-- IG import columns (idempotent on existing databases)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'reddit';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ig_handle TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS pipeline_stage TEXT DEFAULT 'prospect';
ALTER TABLE leads DROP CONSTRAINT IF EXISTS chk_leads_pipeline_stage;
ALTER TABLE leads ADD CONSTRAINT chk_leads_pipeline_stage
  CHECK (pipeline_stage IN (
    'prospect',
    'meeting_booked',
    'qualified',
    'offer_made',
    'decision_pending',
    'closed_won',
    'closed_lost'
  ));
ALTER TABLE leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();
