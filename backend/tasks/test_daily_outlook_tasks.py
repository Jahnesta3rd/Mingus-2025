#!/usr/bin/env python3
"""
Test script for Daily Outlook Celery Tasks

This script demonstrates how to use the daily outlook tasks and provides
examples for testing the system functionality.
"""

import os
import sys
from datetime import datetime, date, timedelta

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the tasks
from daily_outlook_tasks import (
    generate_daily_outlooks_batch,
    send_daily_outlook_notifications,
    optimize_content_performance,
    health_check_daily_outlook_tasks
)

def test_generate_daily_outlooks():
    """Test daily outlook generation"""
    print("🧪 Testing Daily Outlook Generation...")
    
    # Test with tomorrow's date
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    try:
        # Trigger the task
        result = generate_daily_outlooks_batch.delay(target_date=tomorrow)
        print(f"✅ Task queued with ID: {result.id}")
        
        # Wait for completion (in real usage, you'd check status asynchronously)
        print("⏳ Waiting for task completion...")
        task_result = result.get(timeout=300)  # 5 minute timeout
        
        print("📊 Task Results:")
        print(f"   Success: {task_result.get('success', False)}")
        print(f"   Target Date: {task_result.get('target_date', 'N/A')}")
        print(f"   Total Users: {task_result.get('total_users', 0)}")
        print(f"   Generated: {task_result.get('generated_count', 0)}")
        print(f"   Skipped: {task_result.get('skipped_count', 0)}")
        print(f"   Failed: {task_result.get('failed_count', 0)}")
        
        if task_result.get('errors'):
            print("❌ Errors:")
            for error in task_result['errors']:
                print(f"   - {error}")
        
        return task_result
        
    except Exception as e:
        print(f"❌ Error testing outlook generation: {e}")
        return None

def test_send_notifications():
    """Test notification sending"""
    print("\n🧪 Testing Daily Outlook Notifications...")
    
    try:
        # Trigger the task
        result = send_daily_outlook_notifications.delay()
        print(f"✅ Task queued with ID: {result.id}")
        
        # Wait for completion
        print("⏳ Waiting for task completion...")
        task_result = result.get(timeout=180)  # 3 minute timeout
        
        print("📊 Task Results:")
        print(f"   Success: {task_result.get('success', False)}")
        print(f"   Target Date: {task_result.get('target_date', 'N/A')}")
        print(f"   Total Users: {task_result.get('total_users', 0)}")
        print(f"   Notifications Sent: {task_result.get('notifications_sent', 0)}")
        print(f"   Failed: {task_result.get('failed_count', 0)}")
        
        if task_result.get('errors'):
            print("❌ Errors:")
            for error in task_result['errors']:
                print(f"   - {error}")
        
        return task_result
        
    except Exception as e:
        print(f"❌ Error testing notifications: {e}")
        return None

def test_content_optimization():
    """Test content performance optimization"""
    print("\n🧪 Testing Content Performance Optimization...")
    
    try:
        # Trigger the task with 7-day analysis period
        result = optimize_content_performance.delay(analysis_period_days=7)
        print(f"✅ Task queued with ID: {result.id}")
        
        # Wait for completion
        print("⏳ Waiting for task completion...")
        task_result = result.get(timeout=300)  # 5 minute timeout
        
        print("📊 Task Results:")
        print(f"   Success: {task_result.get('success', False)}")
        
        if task_result.get('performance_metrics'):
            metrics = task_result['performance_metrics']
            print(f"   Total Outlooks: {metrics.get('total_outlooks', 0)}")
            print(f"   View Rate: {metrics.get('view_rate', 0):.2%}")
            print(f"   Engagement Rate: {metrics.get('engagement_rate', 0):.2%}")
            print(f"   Average Rating: {metrics.get('average_rating', 0):.1f}")
            print(f"   Completion Rate: {metrics.get('completion_rate', 0):.2%}")
        
        print(f"   Low-Performing Items: {len(task_result.get('low_performing_content', []))}")
        print(f"   A/B Tests Triggered: {task_result.get('ab_tests_triggered', 0)}")
        print(f"   Templates Updated: {task_result.get('templates_updated', 0)}")
        
        return task_result
        
    except Exception as e:
        print(f"❌ Error testing content optimization: {e}")
        return None

def test_health_check():
    """Test system health check"""
    print("\n🧪 Testing System Health Check...")
    
    try:
        # Trigger the task
        result = health_check_daily_outlook_tasks.delay()
        print(f"✅ Task queued with ID: {result.id}")
        
        # Wait for completion
        print("⏳ Waiting for task completion...")
        task_result = result.get(timeout=60)  # 1 minute timeout
        
        print("📊 Health Check Results:")
        print(f"   Service Status: {task_result.get('service_status', 'Unknown')}")
        print(f"   Database Connected: {task_result.get('database_connected', False)}")
        print(f"   Recent Outlooks: {task_result.get('recent_outlooks_generated', 0)}")
        print(f"   Active Users: {task_result.get('active_users_count', 0)}")
        
        if task_result.get('error'):
            print(f"❌ Error: {task_result['error']}")
        
        return task_result
        
    except Exception as e:
        print(f"❌ Error testing health check: {e}")
        return None

def test_manual_task_triggers():
    """Test manual task triggering"""
    print("\n🧪 Testing Manual Task Triggers...")
    
    # Test with specific parameters
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    
    print("📅 Testing with specific date:", tomorrow)
    
    try:
        # Test generation with force regenerate
        result = generate_daily_outlooks_batch.delay(
            target_date=tomorrow,
            force_regenerate=True
        )
        print(f"✅ Force regeneration task queued: {result.id}")
        
        # Test optimization with extended period
        opt_result = optimize_content_performance.delay(analysis_period_days=14)
        print(f"✅ Extended optimization task queued: {opt_result.id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing manual triggers: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Daily Outlook Tasks Test Suite")
    print("=" * 50)
    
    # Check if Celery is running
    print("🔍 Checking Celery worker status...")
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery workers are running")
        else:
            print("⚠️  No Celery workers found. Please start workers first:")
            print("   celery -A backend.tasks.daily_outlook_tasks worker --loglevel=info")
            return
    except Exception as e:
        print(f"❌ Error checking Celery status: {e}")
        return
    
    # Run tests
    test_results = {}
    
    # Test 1: Health Check
    test_results['health'] = test_health_check()
    
    # Test 2: Outlook Generation
    test_results['generation'] = test_generate_daily_outlooks()
    
    # Test 3: Notifications
    test_results['notifications'] = test_send_notifications()
    
    # Test 4: Content Optimization
    test_results['optimization'] = test_content_optimization()
    
    # Test 5: Manual Triggers
    test_results['manual'] = test_manual_task_triggers()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    
    successful_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        if result:
            print(f"✅ {test_name.title()}: PASSED")
            successful_tests += 1
        else:
            print(f"❌ {test_name.title()}: FAILED")
    
    print(f"\n🎯 Results: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! Daily Outlook Tasks are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
