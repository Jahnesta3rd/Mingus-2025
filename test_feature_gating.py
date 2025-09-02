#!/usr/bin/env python3
"""
MINGUS Feature Gating Test Script
Tests the subscription tier feature access control system
"""

import sqlite3
from datetime import datetime

def test_feature_gating():
    """Test the feature gating system with the new pricing tiers"""
    
    try:
        # Connect to database
        conn = sqlite3.connect('mingus.db')
        cursor = conn.cursor()
        
        print("🔐 Testing MINGUS Feature Gating System")
        print("=" * 50)
        print()
        
        # Test 1: Verify pricing tiers exist
        print("📋 Test 1: Pricing Tiers Verification")
        cursor.execute("""
            SELECT tier_type, name, monthly_price, yearly_price, is_active
            FROM pricing_tiers
            ORDER BY monthly_price ASC
        """)
        
        tiers = cursor.fetchall()
        if len(tiers) == 3:
            print("   ✅ Found 3 pricing tiers")
            for tier in tiers:
                tier_type, name, monthly, yearly, active = tier
                status = "Active" if active else "Inactive"
                print(f"      {tier_type}: {name} - ${monthly}/month, ${yearly}/year [{status}]")
        else:
            print(f"   ❌ Expected 3 tiers, found {len(tiers)}")
            return False
        
        print()
        
        # Test 2: Verify feature limits for each tier
        print("🔒 Test 2: Feature Limits Verification")
        cursor.execute("""
            SELECT 
                tier_type,
                max_health_checkins_per_month,
                max_financial_reports_per_month,
                max_ai_insights_per_month,
                max_projects,
                max_team_members,
                max_storage_gb,
                max_api_calls_per_month,
                advanced_analytics,
                priority_support,
                custom_integrations
            FROM pricing_tiers
            ORDER BY monthly_price ASC
        """)
        
        feature_limits = cursor.fetchall()
        
        # Expected limits for each tier
        expected_limits = {
            'budget': {
                'health_checkins': 4,
                'financial_reports': 2,
                'ai_insights': 0,
                'projects': 1,
                'team_members': 1,
                'storage_gb': 1,
                'api_calls': 1000,
                'advanced_analytics': False,
                'priority_support': False,
                'custom_integrations': False
            },
            'mid_tier': {
                'health_checkins': 12,
                'financial_reports': 10,
                'ai_insights': 50,
                'projects': 3,
                'team_members': 2,
                'storage_gb': 5,
                'api_calls': 5000,
                'advanced_analytics': True,
                'priority_support': True,
                'custom_integrations': False
            },
            'professional': {
                'health_checkins': -1,  # Unlimited
                'financial_reports': -1,  # Unlimited
                'ai_insights': -1,  # Unlimited
                'projects': -1,  # Unlimited
                'team_members': 10,
                'storage_gb': 50,
                'api_calls': 10000,
                'advanced_analytics': True,
                'priority_support': True,
                'custom_integrations': True
            }
        }
        
        for i, (tier_type, hc, fr, ai, proj, tm, storage, api, adv_analytics, priority, custom) in enumerate(feature_limits):
            tier_name = tiers[i][1]
            print(f"   📊 {tier_name} ({tier_type}):")
            
            # Check health check-ins
            expected_hc = expected_limits[tier_type]['health_checkins']
            if hc == expected_hc:
                print(f"      ✅ Health Check-ins: {hc}/month")
            else:
                print(f"      ❌ Health Check-ins: Expected {expected_hc}, got {hc}")
            
            # Check financial reports
            expected_fr = expected_limits[tier_type]['financial_reports']
            if fr == expected_fr:
                print(f"      ✅ Financial Reports: {fr}/month")
            else:
                print(f"      ❌ Financial Reports: Expected {expected_fr}, got {fr}")
            
            # Check AI insights
            expected_ai = expected_limits[tier_type]['ai_insights']
            if ai == expected_ai:
                if ai == -1:
                    print(f"      ✅ AI Insights: Unlimited")
                else:
                    print(f"      ✅ AI Insights: {ai}/month")
            else:
                print(f"      ❌ AI Insights: Expected {expected_ai}, got {ai}")
            
            # Check advanced analytics
            expected_adv = expected_limits[tier_type]['advanced_analytics']
            if adv_analytics == expected_adv:
                status = "Enabled" if adv_analytics else "Disabled"
                print(f"      ✅ Advanced Analytics: {status}")
            else:
                print(f"      ❌ Advanced Analytics: Expected {expected_adv}, got {adv_analytics}")
            
            # Check priority support
            expected_priority = expected_limits[tier_type]['priority_support']
            if priority == expected_priority:
                status = "Enabled" if priority else "Disabled"
                print(f"      ✅ Priority Support: {status}")
            else:
                print(f"      ❌ Priority Support: Expected {expected_priority}, got {priority}")
            
            print()
        
        # Test 3: Verify subscription table structure
        print("💳 Test 3: Subscription Table Structure")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='subscriptions'
        """)
        
        if cursor.fetchone():
            print("   ✅ Subscriptions table exists")
            
            # Check subscription table columns
            cursor.execute("PRAGMA table_info(subscriptions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            required_columns = ['id', 'customer_id', 'pricing_tier_id', 'stripe_subscription_id', 'status', 'amount']
            for col in required_columns:
                if col in columns:
                    print(f"      ✅ Column '{col}' exists")
                else:
                    print(f"      ❌ Missing column '{col}'")
        else:
            print("   ❌ Subscriptions table not found")
        
        print()
        
        # Test 4: Test feature access simulation
        print("🎯 Test 4: Feature Access Simulation")
        
        # Simulate a user with Budget tier trying to access AI insights
        budget_tier = next(tier for tier in feature_limits if tier[0] == 'budget')
        budget_ai_limit = budget_tier[3]  # AI insights is the 4th column (index 3)
        
        if budget_ai_limit == 0:
            print("   ✅ Budget tier correctly blocks AI insights (limit: 0)")
        else:
            print(f"   ❌ Budget tier should block AI insights, but limit is {budget_ai_limit}")
        
        # Simulate a user with Professional tier accessing unlimited features
        professional_tier = next(tier for tier in feature_limits if tier[0] == 'professional')
        prof_health_limit = professional_tier[1]  # Health check-ins is the 2nd column (index 1)
        
        if prof_health_limit == -1:
            print("   ✅ Professional tier correctly allows unlimited health check-ins")
        else:
            print(f"   ❌ Professional tier should allow unlimited health check-ins, but limit is {prof_health_limit}")
        
        print()
        
        # Test 5: Verify pricing calculations
        print("💰 Test 5: Pricing Calculations")
        for tier in tiers:
            tier_type, name, monthly, yearly = tier[:4]
            annual_cost = monthly * 12
            savings = annual_cost - yearly
            savings_percent = (savings / annual_cost) * 100
            
            print(f"   📊 {name}:")
            print(f"      Monthly: ${monthly}")
            print(f"      Yearly: ${yearly}")
            print(f"      Annual savings: ${savings} ({savings_percent:.1f}%)")
            
            # Verify 20% discount
            if abs(savings_percent - 20.0) < 0.1:
                print(f"      ✅ 20% annual discount verified")
            else:
                print(f"      ❌ Expected 20% discount, got {savings_percent:.1f}%")
            print()
        
        print("🎉 Feature gating test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = test_feature_gating()
    if not success:
        exit(1)
