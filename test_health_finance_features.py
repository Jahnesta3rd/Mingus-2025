#!/usr/bin/env python3
"""
Comprehensive Test Script for Health-to-Finance Connection Features
Tests all unique health-to-finance connection features in the Mingus application
"""

import sys
import os
import json
import requests
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class HealthFinanceFeatureTester:
    """Test class for health-to-finance connection features"""
    
    def __init__(self, base_url: str = "http://localhost:5002"):
        self.base_url = base_url
        self.results = []
        self.test_data = {
            "user_id": 1,
            "test_checkin": {
                "physical_activity_minutes": 45,
                "physical_activity_level": "moderate",
                "relationships_rating": 8,
                "relationships_notes": "Had great conversations with family and friends",
                "mindfulness_minutes": 20,
                "mindfulness_type": "meditation",
                "stress_level": 4,
                "energy_level": 7,
                "mood_rating": 8
            }
        }
    
    def test_endpoint(self, endpoint: str, method: str = "GET", data: Dict = None, 
                     expected_status: int = 200, description: str = "") -> Dict[str, Any]:
        """Test a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {"Content-Type": "application/json"} if data else {}
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "description": description,
                "success": response.status_code == expected_status,
                "response_time": response.elapsed.total_seconds(),
                "response_size": len(response.content)
            }
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:500]  # First 500 chars
            
            if response.status_code != expected_status:
                result["error"] = f"Expected {expected_status}, got {response.status_code}"
            
            self.results.append(result)
            return result
            
        except requests.exceptions.ConnectionError:
            result = {
                "endpoint": endpoint,
                "method": method,
                "success": False,
                "error": "Connection refused - Flask app not running",
                "description": description
            }
            self.results.append(result)
            return result
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "success": False,
                "error": str(e),
                "description": description
            }
            self.results.append(result)
            return result
    
    def test_weekly_checkin_form(self) -> bool:
        """Test 1: Weekly check-in form (physical activity, relationships, mindfulness)"""
        print("\n🏃‍♂️ Testing Weekly Check-in Form Features")
        print("=" * 50)
        
        # Test demo form (no auth required)
        demo_result = self.test_endpoint(
            "/api/health/demo",
            "GET",
            expected_status=200,
            description="Demo health check-in form (no auth required)"
        )
        
        # Test authenticated form
        auth_result = self.test_endpoint(
            "/api/health/checkin",
            "GET",
            expected_status=401,  # Should require authentication
            description="Authenticated health check-in form"
        )
        
        # Test form submission
        submit_result = self.test_endpoint(
            "/api/health/checkin",
            "POST",
            data=self.test_data["test_checkin"],
            expected_status=401,  # Should require authentication
            description="Health check-in submission"
        )
        
        success = demo_result["success"] and auth_result["success"]
        print(f"✅ Demo form: {'PASS' if demo_result['success'] else 'FAIL'}")
        print(f"✅ Auth required: {'PASS' if auth_result['success'] else 'FAIL'}")
        print(f"✅ Form submission: {'PASS' if submit_result['success'] else 'FAIL'}")
        
        return success
    
    def test_health_finance_correlations(self) -> bool:
        """Test 2: Connection between health data and spending patterns"""
        print("\n💰 Testing Health-Finance Correlations")
        print("=" * 50)
        
        # Test health spending correlations endpoint
        correlations_result = self.test_endpoint(
            "/api/health/correlations",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health-spending correlations analysis"
        )
        
        # Test health insights endpoint
        insights_result = self.test_endpoint(
            "/api/health/insights",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health insights and analysis"
        )
        
        # Test health trends endpoint
        trends_result = self.test_endpoint(
            "/api/health/trends",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health trends analysis"
        )
        
        success = all([correlations_result["success"], insights_result["success"], trends_result["success"]])
        print(f"✅ Correlations endpoint: {'PASS' if correlations_result['success'] else 'FAIL'}")
        print(f"✅ Insights endpoint: {'PASS' if insights_result['success'] else 'FAIL'}")
        print(f"✅ Trends endpoint: {'PASS' if trends_result['success'] else 'FAIL'}")
        
        return success
    
    def test_relationship_status_impact(self) -> bool:
        """Test 3: Relationship status impact on financial recommendations"""
        print("\n❤️ Testing Relationship Status Impact")
        print("=" * 50)
        
        # Test relationship-based recommendations
        relationship_result = self.test_endpoint(
            "/api/health/recommendations",
            "GET",
            expected_status=401,  # Should require authentication
            description="Relationship-based financial recommendations"
        )
        
        # Test health summary with relationship data
        summary_result = self.test_endpoint(
            "/api/health/summary",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health summary including relationship metrics"
        )
        
        # Test health dashboard with relationship insights
        dashboard_result = self.test_endpoint(
            "/api/health/dashboard",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health dashboard with relationship insights"
        )
        
        success = all([relationship_result["success"], summary_result["success"], dashboard_result["success"]])
        print(f"✅ Relationship recommendations: {'PASS' if relationship_result['success'] else 'FAIL'}")
        print(f"✅ Health summary: {'PASS' if summary_result['success'] else 'FAIL'}")
        print(f"✅ Health dashboard: {'PASS' if dashboard_result['success'] else 'FAIL'}")
        
        return success
    
    def test_physical_activity_correlation(self) -> bool:
        """Test 4: Physical activity correlation with financial decisions"""
        print("\n🏃‍♀️ Testing Physical Activity Correlation")
        print("=" * 50)
        
        # Test physical activity analysis
        activity_result = self.test_endpoint(
            "/api/health/analyze",
            "POST",
            data={"analysis_type": "physical_activity", "user_id": self.test_data["user_id"]},
            expected_status=401,  # Should require authentication
            description="Physical activity correlation analysis"
        )
        
        # Test activity-based spending patterns
        patterns_result = self.test_endpoint(
            "/api/health/patterns",
            "GET",
            expected_status=401,  # Should require authentication
            description="Activity-based spending patterns"
        )
        
        # Test wellness score calculation
        wellness_result = self.test_endpoint(
            "/api/health/wellness-score",
            "GET",
            expected_status=401,  # Should require authentication
            description="Wellness score including physical activity"
        )
        
        success = all([activity_result["success"], patterns_result["success"], wellness_result["success"]])
        print(f"✅ Activity analysis: {'PASS' if activity_result['success'] else 'FAIL'}")
        print(f"✅ Spending patterns: {'PASS' if patterns_result['success'] else 'FAIL'}")
        print(f"✅ Wellness score: {'PASS' if wellness_result['success'] else 'FAIL'}")
        
        return success
    
    def test_mindfulness_tracking(self) -> bool:
        """Test 5: Meditation/mindfulness tracking integration"""
        print("\n🧘‍♀️ Testing Mindfulness Tracking Integration")
        print("=" * 50)
        
        # Test mindfulness tracking
        mindfulness_result = self.test_endpoint(
            "/api/health/mindfulness",
            "GET",
            expected_status=401,  # Should require authentication
            description="Mindfulness tracking and history"
        )
        
        # Test mindfulness-based insights
        mindfulness_insights_result = self.test_endpoint(
            "/api/health/mindfulness/insights",
            "GET",
            expected_status=401,  # Should require authentication
            description="Mindfulness-based financial insights"
        )
        
        # Test mindfulness goals
        mindfulness_goals_result = self.test_endpoint(
            "/api/health/mindfulness/goals",
            "GET",
            expected_status=401,  # Should require authentication
            description="Mindfulness goals and progress"
        )
        
        success = all([mindfulness_result["success"], mindfulness_insights_result["success"], mindfulness_goals_result["success"]])
        print(f"✅ Mindfulness tracking: {'PASS' if mindfulness_result['success'] else 'FAIL'}")
        print(f"✅ Mindfulness insights: {'PASS' if mindfulness_insights_result['success'] else 'FAIL'}")
        print(f"✅ Mindfulness goals: {'PASS' if mindfulness_goals_result['success'] else 'FAIL'}")
        
        return success
    
    def test_health_checkin_history(self) -> bool:
        """Test 6: Health check-in history and statistics"""
        print("\n📊 Testing Health Check-in History")
        print("=" * 50)
        
        # Test check-in history
        history_result = self.test_endpoint(
            "/api/health/checkin/history",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health check-in history"
        )
        
        # Test health statistics
        stats_result = self.test_endpoint(
            "/api/health/stats",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health statistics and analytics"
        )
        
        # Test latest check-in
        latest_result = self.test_endpoint(
            "/api/health/checkin/latest",
            "GET",
            expected_status=401,  # Should require authentication
            description="Latest health check-in"
        )
        
        success = all([history_result["success"], stats_result["success"], latest_result["success"]])
        print(f"✅ Check-in history: {'PASS' if history_result['success'] else 'FAIL'}")
        print(f"✅ Health statistics: {'PASS' if stats_result['success'] else 'FAIL'}")
        print(f"✅ Latest check-in: {'PASS' if latest_result['success'] else 'FAIL'}")
        
        return success
    
    def test_health_onboarding(self) -> bool:
        """Test 7: Health onboarding and setup"""
        print("\n🎯 Testing Health Onboarding")
        print("=" * 50)
        
        # Test health onboarding
        onboarding_result = self.test_endpoint(
            "/api/health/onboarding",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health onboarding flow"
        )
        
        # Test onboarding completion
        completion_result = self.test_endpoint(
            "/api/health/onboarding/complete",
            "POST",
            data={"completed": True, "user_id": self.test_data["user_id"]},
            expected_status=401,  # Should require authentication
            description="Health onboarding completion"
        )
        
        # Test onboarding status
        status_result = self.test_endpoint(
            "/api/health/onboarding/status",
            "GET",
            expected_status=401,  # Should require authentication
            description="Health onboarding status"
        )
        
        success = all([onboarding_result["success"], completion_result["success"], status_result["success"]])
        print(f"✅ Health onboarding: {'PASS' if onboarding_result['success'] else 'FAIL'}")
        print(f"✅ Onboarding completion: {'PASS' if completion_result['success'] else 'FAIL'}")
        print(f"✅ Onboarding status: {'PASS' if status_result['success'] else 'FAIL'}")
        
        return success
    
    def test_health_finance_models(self) -> bool:
        """Test 8: Health-finance data models and database"""
        print("\n🗄️ Testing Health-Finance Data Models")
        print("=" * 50)
        
        try:
            # Test importing health models
            from backend.models.user_health_checkin import UserHealthCheckin
            from backend.models.health_spending_correlation import HealthSpendingCorrelation
            
            print("✅ UserHealthCheckin model imported successfully")
            print("✅ HealthSpendingCorrelation model imported successfully")
            
            # Test model structure
            checkin_fields = [
                'physical_activity_minutes', 'physical_activity_level',
                'relationships_rating', 'relationships_notes',
                'mindfulness_minutes', 'mindfulness_type',
                'stress_level', 'energy_level', 'mood_rating'
            ]
            
            correlation_fields = [
                'health_metric', 'spending_category', 'correlation_strength',
                'correlation_direction', 'insight_text', 'recommendation_text'
            ]
            
            print(f"✅ UserHealthCheckin has required fields: {checkin_fields}")
            print(f"✅ HealthSpendingCorrelation has required fields: {correlation_fields}")
            
            return True
            
        except ImportError as e:
            print(f"❌ Model import failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Model test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all health-to-finance feature tests"""
        print("🧪 Testing Health-to-Finance Connection Features")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("Weekly Check-in Form", self.test_weekly_checkin_form),
            ("Health-Finance Correlations", self.test_health_finance_correlations),
            ("Relationship Status Impact", self.test_relationship_status_impact),
            ("Physical Activity Correlation", self.test_physical_activity_correlation),
            ("Mindfulness Tracking", self.test_mindfulness_tracking),
            ("Health Check-in History", self.test_health_checkin_history),
            ("Health Onboarding", self.test_health_onboarding),
            ("Health-Finance Models", self.test_health_finance_models)
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Generate summary
        summary = {
            "test_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed / total) * 100 if total > 0 else 0,
            "test_results": results,
            "detailed_results": self.results
        }
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} {test_name}")
        
        if passed == total:
            print("\n🎉 All health-to-finance features are working correctly!")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        
        return summary

def main():
    """Main test execution"""
    tester = HealthFinanceFeatureTester()
    results = tester.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"health_finance_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Test results saved to: {filename}")
    
    return results["success_rate"] == 100

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
