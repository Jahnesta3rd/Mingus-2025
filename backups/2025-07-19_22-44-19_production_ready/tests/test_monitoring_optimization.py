"""
Test script for monitoring and optimization systems
"""

import time
import random
from datetime import datetime, timedelta
from backend.monitoring.performance_monitoring import performance_monitor
from backend.monitoring.alerting import alerting_system
from backend.analytics.business_intelligence import business_intelligence
from backend.optimization.database_optimizer import database_optimizer
from backend.optimization.cache_manager import cache_manager
from backend.optimization.score_optimizer import score_optimizer
from backend.optimization.ux_optimizer import ux_optimizer

def test_performance_monitoring():
    """Test performance monitoring functionality"""
    print("Testing Performance Monitoring...")
    
    # Simulate API calls
    for i in range(10):
        with performance_monitor.api_timer('/api/users', 'GET', f'user_{i}'):
            time.sleep(random.uniform(0.1, 0.5))
    
    # Simulate database queries
    for i in range(5):
        with performance_monitor.db_timer("SELECT * FROM users WHERE id = ?", f'user_{i}'):
            time.sleep(random.uniform(0.05, 0.2))
    
    # Simulate score calculations
    for i in range(3):
        with performance_monitor.score_timer('job_security', 100, f'user_{i}'):
            time.sleep(random.uniform(0.2, 0.8))
    
    # Get performance summaries
    api_summary = performance_monitor.get_api_performance_summary(hours=1)
    db_summary = performance_monitor.get_database_performance_summary(hours=1)
    score_summary = performance_monitor.get_score_performance_summary(hours=1)
    
    print(f"API Performance: {api_summary.get('overall', {})}")
    print(f"Database Performance: {db_summary.get('overall', {})}")
    print(f"Score Performance: {score_summary.get('calculations', [])}")

def test_business_intelligence():
    """Test business intelligence functionality"""
    print("\nTesting Business Intelligence...")
    
    # Simulate user engagement
    for i in range(5):
        business_intelligence.track_user_engagement(
            f'user_{i}', 
            f'session_{i}', 
            'health_checkin', 
            usage_time=random.uniform(10, 60)
        )
        
        business_intelligence.track_feature_usage(
            f'user_{i}', 
            'job_security_dashboard', 
            usage_time=random.uniform(30, 120)
        )
        
        business_intelligence.track_user_feedback(
            f'user_{i}', 
            'satisfaction', 
            rating=random.randint(3, 5),
            comment=f"User {i} feedback"
        )
    
    # Generate insights report
    insights = business_intelligence.generate_insights_report(days=1)
    print(f"Business Insights: {insights.get('summary', {})}")

def test_alerting_system():
    """Test alerting system functionality"""
    print("\nTesting Alerting System...")
    
    # Update metrics to trigger alerts
    alerting_system.update_metric('api_response_time', 3.5)  # Should trigger alert
    alerting_system.update_metric('error_rate', 0.08)  # Should trigger alert
    alerting_system.update_metric('memory_usage', 0.95)  # Should trigger alert
    
    # Wait for alerts to be processed
    time.sleep(2)
    
    # Get alert status
    alert_summary = alerting_system.get_alert_summary()
    active_alerts = alerting_system.get_active_alerts()
    
    print(f"Alert Summary: {alert_summary}")
    print(f"Active Alerts: {len(active_alerts)}")

def test_cache_manager():
    """Test cache manager functionality"""
    print("\nTesting Cache Manager...")
    
    # Test caching
    test_data = {"user_id": "123", "name": "Test User", "score": 85.5}
    cache_manager.set('user_123', test_data, ttl=60)
    
    # Retrieve from cache
    cached_data = cache_manager.get('user_123')
    print(f"Cached Data: {cached_data}")
    
    # Test cache statistics
    stats = cache_manager.get_stats()
    print(f"Cache Stats: {stats}")

def test_database_optimizer():
    """Test database optimizer functionality"""
    print("\nTesting Database Optimizer...")
    
    # Simulate query analysis
    slow_query = "SELECT * FROM users WHERE email LIKE '%@example.com' AND created_at > '2025-01-01'"
    analysis = database_optimizer.analyze_query(slow_query, 2.5, 1000)
    
    print(f"Query Analysis: {analysis.suggested_optimizations}")
    print(f"Estimated Improvement: {analysis.estimated_improvement:.1%}")

def test_score_optimizer():
    """Test score optimizer functionality"""
    print("\nTesting Score Optimizer...")
    
    # Simulate score calculation
    calculation = score_optimizer.ScoreCalculation(
        calculation_type='job_security',
        input_data={'experience': 5, 'education': 'bachelor', 'industry': 'tech'},
        weights={'experience': 0.4, 'education': 0.3, 'industry': 0.3},
        algorithm='weighted_average'
    )
    
    result, optimization_result = score_optimizer.optimize_score_calculation(calculation)
    
    print(f"Score Result: {result}")
    print(f"Optimization: {optimization_result.improvement_percentage:.1f}% improvement")

def test_ux_optimizer():
    """Test UX optimizer functionality"""
    print("\nTesting UX Optimizer...")
    
    # Simulate user interactions
    for i in range(10):
        ux_optimizer.track_user_interaction(ux_optimizer.UserInteraction(
            user_id=f'user_{i}',
            session_id=f'session_{i}',
            event_type='click',
            element_id='submit_button',
            page_url='/dashboard',
            duration=random.uniform(0.1, 1.0)
        ))
    
    # Analyze user behavior
    behavior_analysis = ux_optimizer.analyze_user_behavior(days=1)
    recommendations = ux_optimizer.generate_optimization_recommendations(behavior_analysis)
    
    print(f"User Engagement: {behavior_analysis.get('engagement', {})}")
    print(f"UX Recommendations: {len(recommendations)} recommendations")

def test_integration():
    """Test integration between systems"""
    print("\nTesting System Integration...")
    
    # Simulate a complete user workflow with monitoring
    user_id = "test_user_123"
    session_id = "test_session_456"
    
    # User registration (with monitoring)
    with performance_monitor.api_timer('/api/auth/register', 'POST'):
        business_intelligence.track_user_metric(user_id, 'registration', 1.0)
        time.sleep(0.2)
    
    # Health check-in (with monitoring)
    with performance_monitor.api_timer('/api/health/checkin', 'POST', user_id):
        business_intelligence.track_user_engagement(user_id, session_id, 'health_checkin', 30.0)
        time.sleep(0.3)
    
    # Score calculation (with optimization)
    with performance_monitor.score_timer('job_security', 50, user_id):
        calculation = score_optimizer.ScoreCalculation(
            calculation_type='job_security',
            input_data={'experience': 3, 'education': 'master'},
            weights={'experience': 0.6, 'education': 0.4},
            algorithm='weighted_average'
        )
        result, _ = score_optimizer.optimize_score_calculation(calculation)
        time.sleep(0.4)
    
    # Cache the result
    cache_manager.set(f'score_{user_id}', result, ttl=3600)
    
    print(f"Integration Test Complete - Score: {result}")

def main():
    """Run all tests"""
    print("Starting Monitoring and Optimization Systems Test")
    print("=" * 50)
    
    try:
        test_performance_monitoring()
        test_business_intelligence()
        test_alerting_system()
        test_cache_manager()
        test_database_optimizer()
        test_score_optimizer()
        test_ux_optimizer()
        test_integration()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        
        # Print final statistics
        print("\nFinal Statistics:")
        print(f"Performance Monitor Stats: {performance_monitor.get_api_performance_summary(1)}")
        print(f"Cache Manager Stats: {cache_manager.get_stats()}")
        print(f"Score Optimizer Stats: {score_optimizer.get_optimization_stats()}")
        print(f"Alerting System Summary: {alerting_system.get_alert_summary()}")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 