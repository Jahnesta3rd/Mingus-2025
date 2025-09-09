#!/usr/bin/env python3
"""
Test Script for Meme Analytics System

This script demonstrates the analytics system functionality with sample data
and provides a quick way to test all features.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from meme_analytics_system import MemeAnalyticsSystem, AnalyticsEvent, UserDemographics
from meme_analytics_reports import MemeAnalyticsReports

def create_sample_data(analytics, num_users=50, num_events=200):
    """Create sample data for testing"""
    print("Creating sample data...")
    
    # Sample user demographics
    age_ranges = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    genders = ['male', 'female', 'non-binary', 'prefer_not_to_say']
    income_ranges = ['under_25k', '25k-50k', '50k-75k', '75k-100k', '100k-150k', '150k+']
    education_levels = ['high_school', 'some_college', 'bachelors', 'masters', 'doctorate']
    states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
    
    # Create user demographics
    for user_id in range(1, num_users + 1):
        demographics = UserDemographics(
            user_id=user_id,
            age_range=random.choice(age_ranges),
            gender=random.choice(genders),
            income_range=random.choice(income_ranges),
            education_level=random.choice(education_levels),
            location_state=random.choice(states)
        )
        analytics.add_user_demographics(demographics)
    
    # Sample meme categories
    categories = ['faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out']
    meme_ids = list(range(1, 19))  # 18 memes (3 per category)
    
    # Create sample events over the last 30 days
    event_types = ['view', 'continue', 'skip', 'auto_advance', 'error']
    device_types = ['mobile', 'desktop', 'tablet']
    browsers = ['Chrome', 'Safari', 'Firefox', 'Edge']
    
    for _ in range(num_events):
        # Random date within last 30 days
        days_ago = random.randint(0, 30)
        event_time = datetime.now() - timedelta(days=days_ago)
        
        # Create event
        event = AnalyticsEvent(
            user_id=random.randint(1, num_users),
            session_id=f"session_{random.randint(1000, 9999)}",
            meme_id=random.choice(meme_ids),
            event_type=random.choice(event_types),
            time_spent_seconds=random.randint(3, 20) if random.random() > 0.1 else 0,
            user_agent=f"Mozilla/5.0 ({random.choice(device_types)})",
            device_type=random.choice(device_types),
            browser=random.choice(browsers),
            os="Windows" if random.random() > 0.5 else "macOS",
            screen_resolution=f"{random.randint(1200, 1920)}x{random.randint(800, 1080)}"
        )
        
        # Adjust event timestamp
        event.event_timestamp = event_time
        analytics.track_event(event)
    
    print(f"Created {num_users} users and {num_events} events")

def test_analytics_queries(analytics):
    """Test various analytics queries"""
    print("\n" + "="*50)
    print("TESTING ANALYTICS QUERIES")
    print("="*50)
    
    # Test performance metrics
    print("\n1. Performance Metrics (30 days):")
    metrics = analytics.get_performance_metrics(30)
    if metrics:
        print(f"   Total Views: {metrics.get('total_views', 0):,}")
        print(f"   Unique Users: {metrics.get('unique_users', 0):,}")
        print(f"   Skip Rate: {metrics.get('skip_rate', 0):.1f}%")
        print(f"   Continue Rate: {metrics.get('continue_rate', 0):.1f}%")
        print(f"   Avg Time Spent: {metrics.get('avg_time_spent', 0):.1f}s")
    else:
        print("   No metrics data available")
    
    # Test category performance
    print("\n2. Category Performance:")
    category_data = analytics.get_category_performance(30)
    if not category_data.empty:
        for _, row in category_data.head(3).iterrows():
            print(f"   {row['category'].title()}: {row['total_views']} views, "
                  f"{row['skip_rate']:.1f}% skip rate")
    else:
        print("   No category data available")
    
    # Test daily engagement
    print("\n3. Daily Engagement (last 7 days):")
    daily_data = analytics.get_daily_engagement_rates(7)
    if not daily_data.empty:
        print(f"   Days with data: {len(daily_data)}")
        print(f"   Avg daily views: {daily_data['total_views'].mean():.0f}")
        print(f"   Avg skip rate: {daily_data['skip_rate'].mean():.1f}%")
    else:
        print("   No daily data available")
    
    # Test user retention
    print("\n4. User Retention Analysis:")
    retention = analytics.get_user_retention_analysis(30)
    if retention:
        print(f"   Avg interactions per user: {retention.get('avg_interactions', 0):.1f}")
        print(f"   Avg active days: {retention.get('avg_active_days', 0):.1f}")
        print(f"   Total meme users: {retention.get('total_meme_users', 0)}")
    else:
        print("   No retention data available")

def test_alert_system(analytics):
    """Test the alert system"""
    print("\n" + "="*50)
    print("TESTING ALERT SYSTEM")
    print("="*50)
    
    # Check for alerts
    alerts = analytics.check_alerts()
    print(f"\nActive Alerts: {len(alerts)}")
    
    if alerts:
        for i, alert in enumerate(alerts, 1):
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(alert.get('severity', 'low'), "⚪")
            print(f"   {i}. {severity_icon} {alert.get('title', 'Unknown Alert')}")
            print(f"      {alert.get('description', 'No description')}")
    else:
        print("   ✅ No active alerts")

def test_report_generation():
    """Test report generation"""
    print("\n" + "="*50)
    print("TESTING REPORT GENERATION")
    print("="*50)
    
    reports = MemeAnalyticsReports()
    
    # Generate executive summary
    print("\n1. Executive Summary:")
    summary = reports.generate_executive_summary(30)
    print(f"   Generated {len(summary)} character report")
    print(f"   Preview: {summary[:200]}...")
    
    # Generate category analysis
    print("\n2. Category Analysis:")
    category_report = reports.generate_category_analysis(30)
    print(f"   Generated {len(category_report)} character report")
    
    # Generate user behavior report
    print("\n3. User Behavior Report:")
    behavior_report = reports.generate_user_behavior_report(30)
    print(f"   Generated {len(behavior_report)} character report")
    
    # Generate sample queries guide
    print("\n4. Sample Queries Guide:")
    queries_guide = reports.generate_sample_queries_guide()
    print(f"   Generated {len(queries_guide)} character guide")

def test_chart_generation(analytics):
    """Test chart generation"""
    print("\n" + "="*50)
    print("TESTING CHART GENERATION")
    print("="*50)
    
    try:
        success = analytics.create_dashboard_charts("test_charts")
        if success:
            print("✅ Charts generated successfully in 'test_charts/' directory")
        else:
            print("❌ Chart generation failed")
    except Exception as e:
        print(f"❌ Chart generation error: {e}")

def test_csv_export(analytics):
    """Test CSV export functionality"""
    print("\n" + "="*50)
    print("TESTING CSV EXPORT")
    print("="*50)
    
    try:
        # Export daily engagement data
        daily_data = analytics.get_daily_engagement_rates(30)
        if not daily_data.empty:
            success = analytics.export_to_csv(daily_data, "test_daily_engagement.csv")
            if success:
                print("✅ Daily engagement data exported to 'test_daily_engagement.csv'")
            else:
                print("❌ Daily engagement export failed")
        else:
            print("⚠️ No daily data to export")
        
        # Export category performance data
        category_data = analytics.get_category_performance(30)
        if not category_data.empty:
            success = analytics.export_to_csv(category_data, "test_category_performance.csv")
            if success:
                print("✅ Category performance data exported to 'test_category_performance.csv'")
            else:
                print("❌ Category performance export failed")
        else:
            print("⚠️ No category data to export")
            
    except Exception as e:
        print(f"❌ CSV export error: {e}")

def main():
    """Main test function"""
    print("🎭 Meme Analytics System Test")
    print("="*50)
    
    try:
        # Initialize analytics system
        print("Initializing analytics system...")
        analytics = MemeAnalyticsSystem()
        
        # Create sample data
        create_sample_data(analytics, num_users=30, num_events=150)
        
        # Test analytics queries
        test_analytics_queries(analytics)
        
        # Test alert system
        test_alert_system(analytics)
        
        # Test report generation
        test_report_generation()
        
        # Test chart generation
        test_chart_generation(analytics)
        
        # Test CSV export
        test_csv_export(analytics)
        
        print("\n" + "="*50)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*50)
        
        print("\nGenerated files:")
        print("- test_daily_engagement.csv")
        print("- test_category_performance.csv")
        print("- test_charts/ (directory with chart images)")
        print("- meme_analytics.log (log file)")
        
        print("\nNext steps:")
        print("1. Run 'python meme_analytics_api.py' to start the web API")
        print("2. Run 'python meme_analytics_dashboard.py' for the desktop dashboard")
        print("3. Open 'http://localhost:5001/api/analytics/dashboard' for web dashboard")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
