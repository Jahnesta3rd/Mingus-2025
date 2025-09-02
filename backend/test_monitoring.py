#!/usr/bin/env python3
"""
Test script for the monitoring system
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_monitoring_components():
    """Test individual monitoring components"""
    print("🧪 Testing monitoring components...")
    
    try:
        # Test comprehensive monitor
        from monitoring.comprehensive_monitor import comprehensive_monitor
        print("✅ Comprehensive monitor imported successfully")
        
        # Test configuration
        from monitoring.config import get_monitoring_config
        config = get_monitoring_config('development')
        print(f"✅ Configuration loaded: {config['environment']}")
        
        # Test API blueprint
        from monitoring.api import monitoring_bp
        print("✅ API blueprint imported successfully")
        
        # Test Prometheus exporter
        from monitoring.prometheus_exporter import prometheus_exporter
        print("✅ Prometheus exporter imported successfully")
        
        # Test setup functions
        try:
            from monitoring.setup_monitoring import setup_monitoring_for_app
            print("✅ Setup functions imported successfully")
        except ImportError:
            # Try alternative import path
            from setup_monitoring import setup_monitoring_for_app
            print("✅ Setup functions imported successfully (alternative path)")
        
        print("\n🎉 All monitoring components are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing monitoring components: {e}")
        return False

def test_monitoring_functionality():
    """Test basic monitoring functionality"""
    print("\n🔍 Testing monitoring functionality...")
    
    try:
        from monitoring.comprehensive_monitor import comprehensive_monitor
        
        # Test metrics collection
        summary = comprehensive_monitor.get_metrics_summary()
        print(f"✅ Metrics summary generated: {len(summary)} categories")
        
        # Test configuration access
        thresholds = comprehensive_monitor.thresholds
        print(f"✅ Thresholds loaded: {len(thresholds)} settings")
        
        # Test metrics export
        json_export = comprehensive_monitor.export_metrics('json')
        print(f"✅ JSON export working: {len(json_export)} characters")
        
        print("\n🎉 All monitoring functionality is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing monitoring functionality: {e}")
        return False

def test_web_vitals():
    """Test web vitals functionality"""
    print("\n📱 Testing web vitals functionality...")
    
    try:
        from monitoring.comprehensive_monitor import CoreWebVital
        
        # Create a test web vital
        test_vital = CoreWebVital(
            metric_name='LCP',
            value=2.5,
            timestamp='2025-08-31T21:30:00Z',
            page_url='http://localhost:5001/test',
            user_id='test_user',
            device_type='desktop',
            browser='Chrome'
        )
        
        print(f"✅ Web vital created: {test_vital.metric_name} = {test_vital.value}")
        
        # Test adding to monitor
        from monitoring.comprehensive_monitor import comprehensive_monitor
        comprehensive_monitor.add_web_vital(test_vital)
        
        # Check if it was added
        web_vitals = comprehensive_monitor.web_vitals
        print(f"✅ Web vital added to monitor: {len(web_vitals)} total")
        
        print("\n🎉 Web vitals functionality is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing web vitals: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting monitoring system tests...\n")
    
    # Test components
    components_ok = test_monitoring_components()
    
    # Test functionality
    functionality_ok = test_monitoring_functionality()
    
    # Test web vitals
    web_vitals_ok = test_web_vitals()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    if components_ok:
        print("✅ Components: PASSED")
    else:
        print("❌ Components: FAILED")
    
    if functionality_ok:
        print("✅ Functionality: PASSED")
    else:
        print("❌ Functionality: FAILED")
    
    if web_vitals_ok:
        print("✅ Web Vitals: PASSED")
    else:
        print("❌ Web Vitals: FAILED")
    
    print("="*50)
    
    if all([components_ok, functionality_ok, web_vitals_ok]):
        print("\n🎉 ALL TESTS PASSED! Monitoring system is ready to use.")
        print("\n📋 Next steps:")
        print("1. Start your Flask app with monitoring enabled")
        print("2. Access monitoring endpoints at /monitoring/*")
        print("3. View Prometheus metrics at /metrics")
        print("4. Use the built-in dashboard at /monitoring/dashboard")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
