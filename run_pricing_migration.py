#!/usr/bin/env python3
"""
MINGUS Pricing Tier Migration Script
Updates existing pricing tiers to new $15/$35/$100 structure
"""

import sqlite3
import os
from datetime import datetime

def run_pricing_migration():
    """Run the pricing tier migration to update to new $15/$35/$100 structure"""
    
    # Database path (adjust as needed)
    db_path = '../mingus.db'  # Main MINGUS database in root directory
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting pricing tier migration...")
        print(f"📊 Database: {db_path}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Check if pricing_tiers table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='pricing_tiers'
        """)
        
        if not cursor.fetchone():
            print("❌ Error: pricing_tiers table does not exist")
            print("   Please run the initial subscription tables migration first")
            return False
        
        # Check current pricing tiers
        print("📋 Current pricing tiers:")
        cursor.execute("""
            SELECT tier_type, name, monthly_price, yearly_price, is_active
            FROM pricing_tiers
            ORDER BY monthly_price ASC
        """)
        
        current_tiers = cursor.fetchall()
        for tier in current_tiers:
            tier_type, name, monthly, yearly, active = tier
            status = "✅ Active" if active else "❌ Inactive"
            print(f"   {tier_type}: {name} - ${monthly}/month, ${yearly}/year [{status}]")
        
        print()
        
        # Update existing pricing tiers
        print("🔄 Updating existing pricing tiers...")
        
        # Budget Tier
        cursor.execute("""
            UPDATE pricing_tiers 
            SET 
                monthly_price = 15.00,
                yearly_price = 144.00,
                name = 'Budget Tier',
                description = 'Perfect for individuals getting started with personal finance management',
                updated_at = CURRENT_TIMESTAMP
            WHERE tier_type = 'budget'
        """)
        print(f"   ✅ Budget Tier: Updated to $15/month, $144/year")
        
        # Mid-Tier
        cursor.execute("""
            UPDATE pricing_tiers 
            SET 
                monthly_price = 35.00,
                yearly_price = 336.00,
                name = 'Mid-Tier',
                description = 'Ideal for serious users who want advanced financial insights and career protection',
                updated_at = CURRENT_TIMESTAMP
            WHERE tier_type = 'mid_tier'
        """)
        print(f"   ✅ Mid-Tier: Updated to $35/month, $336/year")
        
        # Professional Tier
        cursor.execute("""
            UPDATE pricing_tiers 
            SET 
                monthly_price = 100.00,
                yearly_price = 960.00,
                name = 'Professional Tier',
                description = 'Comprehensive solution for professionals, teams, and businesses',
                updated_at = CURRENT_TIMESTAMP
            WHERE tier_type = 'professional'
        """)
        print(f"   ✅ Professional Tier: Updated to $100/month, $960/year")
        
        # Insert new pricing tiers if they don't exist
        print("➕ Inserting new pricing tiers if needed...")
        
        # Check and insert Budget Tier
        cursor.execute("SELECT COUNT(*) FROM pricing_tiers WHERE tier_type = 'budget'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO pricing_tiers (
                    tier_type, name, description, monthly_price, yearly_price,
                    max_health_checkins_per_month, max_financial_reports_per_month,
                    max_ai_insights_per_month, max_projects, max_team_members,
                    max_storage_gb, max_api_calls_per_month, advanced_analytics,
                    priority_support, custom_integrations, is_active, created_at, updated_at
                ) VALUES (
                    'budget', 'Budget Tier', 'Perfect for individuals getting started with personal finance management',
                    15.00, 144.00, 4, 2, 0, 1, 1, 1, 1000, 0, 0, 0, 1,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """)
            print("   ✅ Budget Tier: Created")
        
        # Check and insert Mid-Tier
        cursor.execute("SELECT COUNT(*) FROM pricing_tiers WHERE tier_type = 'mid_tier'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO pricing_tiers (
                    tier_type, name, description, monthly_price, yearly_price,
                    max_health_checkins_per_month, max_financial_reports_per_month,
                    max_ai_insights_per_month, max_projects, max_team_members,
                    max_storage_gb, max_api_calls_per_month, advanced_analytics,
                    priority_support, custom_integrations, is_active, created_at, updated_at
                ) VALUES (
                    'mid_tier', 'Mid-Tier', 'Ideal for serious users who want advanced financial insights and career protection',
                    35.00, 336.00, 12, 10, 50, 3, 2, 5, 5000, 1, 1, 0, 1,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """)
            print("   ✅ Mid-Tier: Created")
        
        # Check and insert Professional Tier
        cursor.execute("SELECT COUNT(*) FROM pricing_tiers WHERE tier_type = 'professional'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO pricing_tiers (
                    tier_type, name, description, monthly_price, yearly_price,
                    max_health_checkins_per_month, max_financial_reports_per_month,
                    max_ai_insights_per_month, max_projects, max_team_members,
                    max_storage_gb, max_api_calls_per_month, advanced_analytics,
                    priority_support, custom_integrations, is_active, created_at, updated_at
                ) VALUES (
                    'professional', 'Professional Tier', 'Comprehensive solution for professionals, teams, and businesses',
                    100.00, 960.00, -1, -1, -1, -1, 10, 50, 10000, 1, 1, 1, 1,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """)
            print("   ✅ Professional Tier: Created")
        
        # Update existing subscriptions if subscriptions table exists
        try:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='subscriptions'
            """)
            
            if cursor.fetchone():
                print("🔄 Updating existing subscription amounts...")
                
                # Update monthly subscriptions
                cursor.execute("""
                    UPDATE subscriptions 
                    SET amount = (
                        SELECT monthly_price 
                        FROM pricing_tiers 
                        WHERE pricing_tiers.id = subscriptions.pricing_tier_id
                    )
                    WHERE billing_cycle = 'monthly'
                """)
                
                # Update yearly subscriptions
                cursor.execute("""
                    UPDATE subscriptions 
                    SET amount = (
                        SELECT yearly_price 
                        FROM pricing_tiers 
                        WHERE pricing_tiers.id = subscriptions.pricing_tier_id
                    )
                    WHERE billing_cycle = 'annual'
                """)
                
                print("   ✅ Subscription amounts updated")
            else:
                print("   ℹ️  Subscriptions table not found, skipping subscription updates")
                
        except Exception as e:
            print(f"   ⚠️  Warning: Could not update subscriptions: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify the update
        print()
        print("🔍 Verifying updated pricing tiers:")
        cursor.execute("""
            SELECT 
                tier_type,
                name,
                monthly_price,
                yearly_price,
                ROUND((monthly_price * 12 - yearly_price) / (monthly_price * 12) * 100, 1) as annual_savings_percent
            FROM pricing_tiers 
            WHERE is_active = 1 
            ORDER BY monthly_price ASC
        """)
        
        updated_tiers = cursor.fetchall()
        for tier in updated_tiers:
            tier_type, name, monthly, yearly, savings = tier
            print(f"   {tier_type}: {name} - ${monthly}/month, ${yearly}/year (Save {savings}% annually)")
        
        print()
        print("🎉 Pricing tier migration completed successfully!")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = run_pricing_migration()
    if not success:
        exit(1)
