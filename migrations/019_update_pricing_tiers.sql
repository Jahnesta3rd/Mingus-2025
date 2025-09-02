-- Migration: Update Pricing Tiers to New Structure
-- Description: Updates existing pricing tiers to reflect new $15/$35/$100 pricing model
-- Date: September 1, 2025

-- Update existing pricing tiers to new pricing structure
UPDATE pricing_tiers 
SET 
    monthly_price = 15.00,
    yearly_price = 144.00,
    name = 'Budget Tier',
    description = 'Perfect for individuals getting started with personal finance management',
    updated_at = CURRENT_TIMESTAMP
WHERE tier_type = 'budget';

UPDATE pricing_tiers 
SET 
    monthly_price = 35.00,
    yearly_price = 336.00,
    name = 'Mid-Tier',
    description = 'Ideal for serious users who want advanced financial insights and career protection',
    updated_at = CURRENT_TIMESTAMP
WHERE tier_type = 'mid_tier';

UPDATE pricing_tiers 
SET 
    monthly_price = 100.00,
    yearly_price = 960.00,
    name = 'Professional Tier',
    description = 'Comprehensive solution for professionals, teams, and businesses',
    updated_at = CURRENT_TIMESTAMP
WHERE tier_type = 'professional';

-- Insert new pricing tiers if they don't exist (SQLite compatible)
INSERT INTO pricing_tiers (
    tier_type, 
    name, 
    description, 
    monthly_price, 
    yearly_price, 
    max_health_checkins_per_month, 
    max_financial_reports_per_month, 
    max_ai_insights_per_month, 
    max_projects, 
    max_team_members, 
    max_storage_gb, 
    max_api_calls_per_month, 
    advanced_analytics, 
    priority_support, 
    custom_integrations, 
    is_active, 
    created_at, 
    updated_at
) 
SELECT 
    'budget', 'Budget Tier', 'Perfect for individuals getting started with personal finance management', 15.00, 144.00, 4, 2, 0, 1, 1, 1, 1000, 0, 0, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pricing_tiers WHERE tier_type = 'budget');

INSERT INTO pricing_tiers (
    tier_type, 
    name, 
    description, 
    monthly_price, 
    yearly_price, 
    max_health_checkins_per_month, 
    max_financial_reports_per_month, 
    max_ai_insights_per_month, 
    max_projects, 
    max_team_members, 
    max_storage_gb, 
    max_api_calls_per_month, 
    advanced_analytics, 
    priority_support, 
    custom_integrations, 
    is_active, 
    created_at, 
    updated_at
) 
SELECT 
    'mid_tier', 'Mid-Tier', 'Ideal for serious users who want advanced financial insights and career protection', 35.00, 336.00, 12, 10, 50, 3, 2, 5, 5000, 1, 1, 0, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pricing_tiers WHERE tier_type = 'mid_tier');

INSERT INTO pricing_tiers (
    tier_type, 
    name, 
    description, 
    monthly_price, 
    yearly_price, 
    max_health_checkins_per_month, 
    max_financial_reports_per_month, 
    max_ai_insights_per_month, 
    max_projects, 
    max_team_members, 
    max_storage_gb, 
    max_api_calls_per_month, 
    advanced_analytics, 
    priority_support, 
    custom_integrations, 
    is_active, 
    created_at, 
    updated_at
) 
SELECT 
    'professional', 'Professional Tier', 'Comprehensive solution for professionals, teams, and businesses', 100.00, 960.00, -1, -1, -1, -1, 10, 50, 10000, 1, 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM pricing_tiers WHERE tier_type = 'professional');

-- Update any existing subscriptions to reflect new pricing (SQLite compatible)
UPDATE subscriptions 
SET amount = (
    SELECT monthly_price 
    FROM pricing_tiers 
    WHERE pricing_tiers.id = subscriptions.pricing_tier_id
)
WHERE billing_cycle = 'monthly';

UPDATE subscriptions 
SET amount = (
    SELECT yearly_price 
    FROM pricing_tiers 
    WHERE pricing_tiers.id = subscriptions.pricing_tier_id
)
WHERE billing_cycle = 'annual';

-- Verify the update
SELECT 
    tier_type,
    name,
    monthly_price,
    yearly_price,
    ROUND((monthly_price * 12 - yearly_price) / (monthly_price * 12) * 100, 1) as annual_savings_percent
FROM pricing_tiers 
WHERE is_active = 1 
ORDER BY monthly_price ASC;
