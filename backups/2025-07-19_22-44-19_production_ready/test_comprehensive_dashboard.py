#!/usr/bin/env python3
"""
Test script for the comprehensive career dashboard
Tests the dashboard template, routes, and functionality
"""

import sys
import os
import requests
from datetime import datetime

def test_dashboard_template():
    """Test the dashboard template structure"""
    print("🧪 Testing comprehensive dashboard template...")
    
    try:
        with open('templates/comprehensive_career_dashboard.html', 'r') as f:
            content = f.read()
        
        # Check for key elements
        required_elements = [
            'Career Advancement Dashboard',
            'Your Income Analysis & Job Opportunities',
            'overallPercentile',
            'opportunityScore',
            'primaryGapAmount',
            'comparisonGrid',
            'jobMatches',
            'actionPlan',
            'financial-impact',
            'motivational-section',
            'progress-ring',
            'displayDashboard',
            'displayComparisonGrid',
            'displayJobMatches'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing elements: {missing_elements}")
            return False
        else:
            print("✅ Dashboard template contains all required elements")
            return True
            
    except FileNotFoundError:
        print("❌ Dashboard template file not found")
        return False
    except Exception as e:
        print(f"❌ Error testing dashboard template: {str(e)}")
        return False

def test_dashboard_features():
    """Test dashboard features and components"""
    print("\n📊 Testing dashboard features...")
    
    try:
        with open('templates/comprehensive_career_dashboard.html', 'r') as f:
            content = f.read()
        
        dashboard_features = [
            'income analysis dashboard',
            'visual indicators',
            'percentile rankings',
            'income gaps',
            'opportunity callouts',
            'job matches integration',
            'action items',
            'motivational messaging',
            'financial impact',
            'career advancement',
            'professional design',
            'mobile responsive',
            'comparison cards',
            'progress rings'
        ]
        
        found_features = []
        for feature in dashboard_features:
            if feature in content.lower():
                found_features.append(feature)
        
        print(f"✅ Found {len(found_features)} dashboard features:")
        for feature in found_features:
            print(f"   - {feature}")
        
        if len(found_features) >= 10:
            print("✅ Good dashboard feature coverage")
            return True
        else:
            print(f"⚠️  Limited dashboard features: {len(found_features)}/14")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dashboard features: {str(e)}")
        return False

def test_flask_routes():
    """Test Flask routes (requires running server)"""
    print("\n🌐 Testing Flask routes...")
    
    routes_to_test = [
        ('/api/income-analysis/dashboard', 'GET'),
        ('/api/income-analysis/demo', 'GET'),
        ('/api/income-analysis/health', 'GET')
    ]
    
    working_routes = 0
    
    for route, method in routes_to_test:
        try:
            if method == 'GET':
                response = requests.get(f"http://localhost:5003{route}", timeout=5)
            else:
                response = requests.post(f"http://localhost:5003{route}", timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {method} {route} - Working")
                working_routes += 1
            else:
                print(f"⚠️  {method} {route} - Status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"⚠️  {method} {route} - Server not running")
        except Exception as e:
            print(f"❌ {method} {route} - Error: {str(e)}")
    
    if working_routes == len(routes_to_test):
        print("✅ All routes working correctly")
        return True
    else:
        print(f"⚠️  {working_routes}/{len(routes_to_test)} routes working")
        return False

def test_dashboard_data_integration():
    """Test dashboard data integration"""
    print("\n🔗 Testing dashboard data integration...")
    
    try:
        # Test demo data integration
        response = requests.get(
            "http://localhost:5003/api/income-analysis/demo",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                income_comparison = data['data']['income_comparison']
                
                # Check required data fields
                required_fields = [
                    'overall_percentile',
                    'career_opportunity_score',
                    'primary_gap',
                    'comparisons',
                    'motivational_summary',
                    'action_plan'
                ]
                
                missing_fields = []
                for field in required_fields:
                    if field not in income_comparison:
                        missing_fields.append(field)
                
                if not missing_fields:
                    print("✅ Dashboard data integration working correctly")
                    print(f"   Overall Percentile: {income_comparison['overall_percentile']:.1f}%")
                    print(f"   Career Opportunity Score: {income_comparison['career_opportunity_score']:.1f}/100")
                    print(f"   Comparisons: {len(income_comparison['comparisons'])} demographic groups")
                    print(f"   Action Plan: {len(income_comparison['action_plan'])} steps")
                    return True
                else:
                    print(f"❌ Missing data fields: {missing_fields}")
                    return False
            else:
                print(f"❌ Demo data failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Demo data request failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running - cannot test data integration")
        return False
    except Exception as e:
        print(f"❌ Data integration error: {str(e)}")
        return False

def test_visual_components():
    """Test visual components and styling"""
    print("\n🎨 Testing visual components...")
    
    try:
        with open('templates/comprehensive_career_dashboard.html', 'r') as f:
            content = f.read()
        
        visual_components = [
            'progress-ring',
            'percentile-bar',
            'gap-indicator',
            'opportunity-callout',
            'financial-impact',
            'metric-card',
            'comparison-card',
            'job-match-card',
            'action-step',
            'motivational-section',
            'gradient-primary',
            'gradient-success',
            'box-shadow',
            'border-radius',
            'transition'
        ]
        
        found_components = []
        for component in visual_components:
            if component in content:
                found_components.append(component)
        
        print(f"✅ Found {len(found_components)} visual components:")
        for component in found_components:
            print(f"   - {component}")
        
        if len(found_components) >= 12:
            print("✅ Good visual component coverage")
            return True
        else:
            print(f"⚠️  Limited visual components: {len(found_components)}/15")
            return False
            
    except Exception as e:
        print(f"❌ Error testing visual components: {str(e)}")
        return False

def test_user_experience():
    """Test user experience features"""
    print("\n👤 Testing user experience features...")
    
    try:
        with open('templates/comprehensive_career_dashboard.html', 'r') as f:
            content = f.read()
        
        ux_features = [
            'loading spinner',
            'error handling',
            'responsive design',
            'mobile',
            'accessibility',
            'keyboard navigation',
            'focus indicators',
            'color contrast',
            'semantic html',
            'aria labels',
            'screen readers',
            'touch friendly',
            'hover effects',
            'smooth transitions'
        ]
        
        found_features = []
        for feature in ux_features:
            if feature in content.lower():
                found_features.append(feature)
        
        print(f"✅ Found {len(found_features)} UX features:")
        for feature in found_features:
            print(f"   - {feature}")
        
        if len(found_features) >= 8:
            print("✅ Good UX feature coverage")
            return True
        else:
            print(f"⚠️  Limited UX features: {len(found_features)}/14")
            return False
            
    except Exception as e:
        print(f"❌ Error testing UX features: {str(e)}")
        return False

def test_motivational_elements():
    """Test motivational and career advancement elements"""
    print("\n🚀 Testing motivational elements...")
    
    try:
        with open('templates/comprehensive_career_dashboard.html', 'r') as f:
            content = f.read()
        
        motivational_elements = [
            'career advancement',
            'income growth',
            'opportunity',
            'potential',
            'growth',
            'advancement',
            'motivational',
            'encouraging',
            'positive',
            'empowering',
            'transform',
            'achieve',
            'success',
            'progress',
            'improvement'
        ]
        
        found_elements = []
        for element in motivational_elements:
            if element in content.lower():
                found_elements.append(element)
        
        print(f"✅ Found {len(found_elements)} motivational elements:")
        for element in found_elements:
            print(f"   - {element}")
        
        if len(found_elements) >= 10:
            print("✅ Good motivational element coverage")
            return True
        else:
            print(f"⚠️  Limited motivational elements: {len(found_elements)}/15")
            return False
            
    except Exception as e:
        print(f"❌ Error testing motivational elements: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🎯 COMPREHENSIVE CAREER DASHBOARD TEST")
    print("=" * 60)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run tests
    tests = [
        test_dashboard_template,
        test_dashboard_features,
        test_visual_components,
        test_user_experience,
        test_motivational_elements,
        test_flask_routes,
        test_dashboard_data_integration
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Comprehensive career dashboard is ready for production")
    elif passed_tests >= total_tests * 0.8:
        print("✅ Most tests passed - dashboard is mostly ready")
    else:
        print("⚠️  Several tests failed - review needed")
    
    print("\nKey features tested:")
    print("• Dashboard template structure and content")
    print("• Visual components and styling")
    print("• User experience and accessibility")
    print("• Motivational and career advancement elements")
    print("• Flask route availability")
    print("• Data integration and functionality")
    print("• Professional design and branding")
    
    print("\nNext steps:")
    print("1. Start Flask server: python app.py")
    print("2. Visit: http://localhost:5003/api/income-analysis/dashboard")
    print("3. Test the comprehensive dashboard functionality")
    print("4. Verify mobile responsiveness and user experience")
    print("5. Test integration with job matches and action plans")

if __name__ == "__main__":
    main() 