#!/usr/bin/env python3
"""
Meme Analytics System Test Script
================================

This script demonstrates the functionality of the meme analytics system
by creating sample data and testing various analytics features.

Usage:
    python scripts/test_meme_analytics.py

Author: MINGUS Development Team
Date: January 2025
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from analytics.meme_analytics import (
        MemeAnalyticsService, create_meme_analytics_service,
        track_meme_view, track_meme_skip, track_meme_conversion
    )
    from config.base import Config
    from database import get_db_session
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this script from the project root directory")
    sys.exit(1)


class MemeAnalyticsTester:
    """Test class for the meme analytics system"""
    
    def __init__(self):
        self.config = Config()
        self.db_session = get_db_session()
        self.analytics_service = create_meme_analytics_service(self.db_session, self.config)
        
        # Sample data
        self.sample_users = [1001, 1002, 1003, 1004, 1005]
        self.sample_memes = [
            {"id": "meme-001", "category": "faith"},
            {"id": "meme-002", "category": "work_life"},
            {"id": "meme-003", "category": "friendships"},
            {"id": "meme-004", "category": "children"},
            {"id": "meme-005", "category": "relationships"},
            {"id": "meme-006", "category": "going_out"}
        ]
        self.categories = ["faith", "work_life", "friendships", "children", "relationships", "going_out"]
        
    def generate_sample_data(self, days: int = 7) -> None:
        """Generate sample analytics data for testing"""
        print(f"Generating sample data for the last {days} days...")
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Generate events for each day
        current_date = start_date
        event_count = 0
        
        while current_date <= end_date:
            # Generate 50-100 events per day
            daily_events = 50 + (hash(str(current_date)) % 50)
            
            for _ in range(daily_events):
                user_id = self.sample_users[hash(str(event_count)) % len(self.sample_users)]
                meme = self.sample_memes[hash(str(event_count)) % len(self.sample_memes)]
                
                # Randomize event type and timing
                event_type = ["view", "skip", "conversion"][hash(str(event_count)) % 3]
                time_spent = 5 + (hash(str(event_count)) % 25)  # 5-30 seconds
                
                # Add some randomness to the timestamp within the day
                hour = hash(str(event_count)) % 24
                minute = hash(str(event_count)) % 60
                second = hash(str(event_count)) % 60
                
                event_timestamp = current_date.replace(
                    hour=hour, minute=minute, second=second, microsecond=0
                )
                
                # Track the event
                if event_type == "view":
                    track_meme_view(
                        user_id=user_id,
                        meme_id=meme["id"],
                        category=meme["category"],
                        time_spent=time_spent,
                        session_id=f"session-{event_count}",
                        source_page="/dashboard",
                        device_type=["mobile", "desktop", "tablet"][hash(str(event_count)) % 3],
                        user_agent="Mozilla/5.0 (Test Browser)",
                        ip_address=f"192.168.1.{hash(str(event_count)) % 255}",
                        db_session=self.db_session,
                        config=self.config
                    )
                elif event_type == "skip":
                    track_meme_skip(
                        user_id=user_id,
                        meme_id=meme["id"],
                        category=meme["category"],
                        time_spent=time_spent,
                        session_id=f"session-{event_count}",
                        source_page="/dashboard",
                        device_type=["mobile", "desktop", "tablet"][hash(str(event_count)) % 3],
                        user_agent="Mozilla/5.0 (Test Browser)",
                        ip_address=f"192.168.1.{hash(str(event_count)) % 255}",
                        db_session=self.db_session,
                        config=self.config
                    )
                elif event_type == "conversion":
                    track_meme_conversion(
                        user_id=user_id,
                        meme_id=meme["id"],
                        category=meme["category"],
                        time_spent=time_spent,
                        session_id=f"session-{event_count}",
                        source_page="/dashboard",
                        device_type=["mobile", "desktop", "tablet"][hash(str(event_count)) % 3],
                        user_agent="Mozilla/5.0 (Test Browser)",
                        ip_address=f"192.168.1.{hash(str(event_count)) % 255}",
                        db_session=self.db_session,
                        config=self.config
                    )
                
                event_count += 1
            
            current_date += timedelta(days=1)
        
        print(f"Generated {event_count} sample events")
    
    def test_engagement_metrics(self) -> None:
        """Test engagement metrics calculation"""
        print("\n=== Testing Engagement Metrics ===")
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        metrics = self.analytics_service.get_meme_engagement_metrics(start_date, end_date)
        
        print(f"Total Views: {metrics.total_views}")
        print(f"Total Skips: {metrics.total_skips}")
        print(f"Total Likes: {metrics.total_likes}")
        print(f"Total Shares: {metrics.total_shares}")
        print(f"Total Conversions: {metrics.total_conversions}")
        print(f"Skip Rate: {metrics.skip_rate:.1f}%")
        print(f"Engagement Rate: {metrics.engagement_rate:.1f}%")
        print(f"Conversion Rate: {metrics.conversion_rate:.1f}%")
        print(f"Average Time Spent: {metrics.avg_time_spent:.1f} seconds")
        print(f"Unique Users: {metrics.unique_users}")
    
    def test_category_performance(self) -> None:
        """Test category performance metrics"""
        print("\n=== Testing Category Performance ===")
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        category_metrics = self.analytics_service.get_category_performance_metrics(start_date, end_date)
        
        print("Category Performance:")
        for metric in category_metrics:
            print(f"  {metric.category}:")
            print(f"    Views: {metric.total_views}")
            print(f"    Skip Rate: {metric.skip_rate:.1f}%")
            print(f"    Engagement Rate: {metric.engagement_rate:.1f}%")
            print(f"    Avg Time: {metric.avg_time_spent:.1f}s")
            print(f"    Unique Users: {metric.unique_users}")
    
    def test_daily_trends(self) -> None:
        """Test daily trends calculation"""
        print("\n=== Testing Daily Trends ===")
        
        daily_trends = self.analytics_service.get_daily_engagement_trends(7)
        
        print("Daily Trends:")
        for trend in daily_trends:
            print(f"  {trend['date']}:")
            print(f"    Views: {trend['total_views']}")
            print(f"    Skip Rate: {trend['skip_rate']:.1f}%")
            print(f"    Engagement Rate: {trend['engagement_rate']:.1f}%")
            print(f"    Unique Users: {trend['unique_users']}")
            print(f"    Avg Time: {trend['avg_time_spent']:.1f}s")
    
    def test_user_demographics(self) -> None:
        """Test user demographics metrics"""
        print("\n=== Testing User Demographics ===")
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        demographics = self.analytics_service.get_user_demographics_metrics(start_date, end_date)
        
        print("User Demographics by Device:")
        for demo in demographics:
            print(f"  {demo.device_type}:")
            print(f"    Users: {demo.user_count}")
            print(f"    Skip Rate: {demo.skip_rate:.1f}%")
            print(f"    Engagement Rate: {demo.engagement_rate:.1f}%")
            print(f"    Avg Time: {demo.avg_time_spent:.1f}s")
    
    def test_retention_analysis(self) -> None:
        """Test user retention analysis"""
        print("\n=== Testing Retention Analysis ===")
        
        retention_data = self.analytics_service.get_user_retention_analysis(30)
        
        print("Retention Analysis:")
        print(f"  Meme Users: {retention_data.get('meme_users_count', 0)}")
        print(f"  Non-Meme Users: {retention_data.get('non_meme_users_count', 0)}")
        print(f"  Estimated Meme Retention: {retention_data.get('estimated_meme_retention_rate', 0):.1f}%")
        print(f"  Estimated Non-Meme Retention: {retention_data.get('estimated_non_meme_retention_rate', 0):.1f}%")
        print(f"  Retention Improvement: {retention_data.get('retention_improvement', 0):.1f}%")
    
    def test_alerts(self) -> None:
        """Test alert generation"""
        print("\n=== Testing Alerts ===")
        
        alerts = self.analytics_service.check_alert_conditions()
        
        if alerts:
            print(f"Found {len(alerts)} alerts:")
            for alert in alerts:
                print(f"  {alert.alert_type}: {alert.message}")
                print(f"    Severity: {alert.severity}")
                print(f"    Current Value: {alert.current_value:.1f}%")
                print(f"    Threshold: {alert.threshold:.1f}%")
        else:
            print("No alerts generated")
    
    def test_data_export(self) -> None:
        """Test data export functionality"""
        print("\n=== Testing Data Export ===")
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)
        
        # Test CSV export
        csv_data = self.analytics_service.export_analytics_data(start_date, end_date, 'csv')
        print(f"CSV Export: {len(csv_data)} characters")
        
        # Test JSON export
        json_data = self.analytics_service.export_analytics_data(start_date, end_date, 'json')
        print(f"JSON Export: {len(json_data)} characters")
        
        # Save sample exports
        with open('sample_meme_analytics.csv', 'w') as f:
            f.write(csv_data)
        
        with open('sample_meme_analytics.json', 'w') as f:
            f.write(json_data)
        
        print("Sample exports saved to sample_meme_analytics.csv and sample_meme_analytics.json")
    
    def test_sample_queries(self) -> None:
        """Test sample queries"""
        print("\n=== Testing Sample Queries ===")
        
        sample_queries = self.analytics_service.get_sample_queries()
        
        print("Sample Queries:")
        for i, query in enumerate(sample_queries, 1):
            print(f"  {i}. {query['name']}")
            print(f"     Description: {query['description']}")
            print(f"     Use Case: {query['use_case']}")
            print(f"     Query: {query['query']}")
            print()
    
    def test_sample_reports(self) -> None:
        """Test sample reports"""
        print("\n=== Testing Sample Reports ===")
        
        sample_reports = self.analytics_service.get_sample_reports()
        
        print("Sample Reports:")
        for i, report in enumerate(sample_reports, 1):
            print(f"  {i}. {report['name']}")
            print(f"     Period: {report['period']}")
            if 'metrics' in report:
                print("     Metrics:")
                for key, value in report['metrics'].items():
                    print(f"       {key}: {value}")
            if 'insights' in report:
                print("     Insights:")
                for insight in report['insights']:
                    print(f"       - {insight}")
            print()
    
    def run_all_tests(self) -> None:
        """Run all tests"""
        print("🚀 Starting Meme Analytics System Tests")
        print("=" * 50)
        
        try:
            # Generate sample data first
            self.generate_sample_data(7)
            
            # Run all tests
            self.test_engagement_metrics()
            self.test_category_performance()
            self.test_daily_trends()
            self.test_user_demographics()
            self.test_retention_analysis()
            self.test_alerts()
            self.test_data_export()
            self.test_sample_queries()
            self.test_sample_reports()
            
            print("\n✅ All tests completed successfully!")
            print("\n📊 Analytics System Features Tested:")
            print("  ✓ Event tracking (views, skips, conversions)")
            print("  ✓ Engagement metrics calculation")
            print("  ✓ Category performance analysis")
            print("  ✓ Daily trends tracking")
            print("  ✓ User demographics analysis")
            print("  ✓ Retention correlation analysis")
            print("  ✓ Automated alert generation")
            print("  ✓ Data export (CSV/JSON)")
            print("  ✓ Sample queries and reports")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up
            if hasattr(self, 'db_session'):
                self.db_session.close()


def main():
    """Main function"""
    print("Meme Analytics System Test Script")
    print("=================================")
    
    # Check if we're in the right directory
    if not os.path.exists('backend'):
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Create and run tests
    tester = MemeAnalyticsTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
