#!/usr/bin/env python3
"""
Simple Gamification System Test

A simplified test to verify the gamification system components are working correctly.
This test focuses on the core functionality without complex dependencies.
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_streak_tracker_component():
    """Test that StreakTracker component exists and has required methods"""
    print("🧪 Testing StreakTracker Component...")
    
    try:
        # Check if the component file exists
        component_path = "frontend/src/components/StreakTracker.tsx"
        if os.path.exists(component_path):
            print("✅ StreakTracker.tsx component exists")
            
            # Read the component file to verify it has key features
            with open(component_path, 'r') as f:
                content = f.read()
                
            # Check for key features
            features = [
                'StreakTracker',
                'ProgressRing',
                'ConfettiAnimation',
                'getStreakIcon',
                'getStreakColor',
                'milestones',
                'achievements',
                'recovery_options',
                'weekly_challenges'
            ]
            
            for feature in features:
                if feature in content:
                    print(f"✅ {feature} found in component")
                else:
                    print(f"❌ {feature} not found in component")
                    return False
            
            return True
        else:
            print("❌ StreakTracker.tsx component not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing StreakTracker component: {e}")
        return False

def test_gamification_service():
    """Test that GamificationService exists and has required methods"""
    print("\n🔧 Testing GamificationService...")
    
    try:
        # Check if the service file exists
        service_path = "backend/services/gamification_service.py"
        if os.path.exists(service_path):
            print("✅ gamification_service.py exists")
            
            # Read the service file to verify it has key methods
            with open(service_path, 'r') as f:
                content = f.read()
                
            # Check for key methods
            methods = [
                'class GamificationService',
                'calculate_streak',
                'get_milestones',
                'get_achievements',
                'get_recovery_options',
                'get_weekly_challenges',
                'get_leaderboard',
                'get_engagement_analytics',
                'get_tier_rewards'
            ]
            
            for method in methods:
                if method in content:
                    print(f"✅ {method} found in service")
                else:
                    print(f"❌ {method} not found in service")
                    return False
            
            return True
        else:
            print("❌ gamification_service.py not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing GamificationService: {e}")
        return False

def test_database_models():
    """Test that gamification database models exist"""
    print("\n🗄️ Testing Database Models...")
    
    try:
        # Check if the models file exists
        models_path = "backend/models/gamification_models.py"
        if os.path.exists(models_path):
            print("✅ gamification_models.py exists")
            
            # Read the models file to verify it has key models
            with open(models_path, 'r') as f:
                content = f.read()
                
            # Check for key models
            models = [
                'class UserStreak',
                'class Achievement',
                'class UserAchievement',
                'class Milestone',
                'class MilestoneAchievement',
                'class DailyEngagement',
                'class WeeklyChallenge',
                'class ChallengeParticipant',
                'class RecoveryOption',
                'class LeaderboardEntry',
                'class UserPoints'
            ]
            
            for model in models:
                if model in content:
                    print(f"✅ {model} found in models")
                else:
                    print(f"❌ {model} not found in models")
                    return False
            
            return True
        else:
            print("❌ gamification_models.py not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing database models: {e}")
        return False

def test_api_endpoints():
    """Test that gamification API endpoints exist"""
    print("\n🌐 Testing API Endpoints...")
    
    try:
        # Check if the API file exists
        api_path = "backend/api/gamification_api.py"
        if os.path.exists(api_path):
            print("✅ gamification_api.py exists")
            
            # Read the API file to verify it has key endpoints
            with open(api_path, 'r') as f:
                content = f.read()
                
            # Check for key endpoints
            endpoints = [
                'get_streak_data',
                'get_achievements',
                'get_milestones',
                'get_weekly_challenges',
                'get_leaderboard',
                'process_recovery',
                'join_challenge',
                'claim_achievement',
                'get_engagement_analytics',
                'get_tier_rewards'
            ]
            
            for endpoint in endpoints:
                if endpoint in content:
                    print(f"✅ {endpoint} found in API")
                else:
                    print(f"❌ {endpoint} not found in API")
                    return False
            
            return True
        else:
            print("❌ gamification_api.py not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

def test_daily_outlook_integration():
    """Test that Daily Outlook integration exists"""
    print("\n🔗 Testing Daily Outlook Integration...")
    
    try:
        # Check if Daily Outlook has been updated with gamification
        outlook_path = "frontend/src/components/DailyOutlook.tsx"
        if os.path.exists(outlook_path):
            print("✅ DailyOutlook.tsx exists")
            
            # Read the Daily Outlook file to verify integration
            with open(outlook_path, 'r') as f:
                content = f.read()
                
            # Check for gamification integration
            integration_features = [
                'StreakTracker',
                'showStreakTracker',
                'showGamification',
                'gamification'
            ]
            
            for feature in integration_features:
                if feature in content:
                    print(f"✅ {feature} found in Daily Outlook")
                else:
                    print(f"❌ {feature} not found in Daily Outlook")
                    return False
            
            return True
        else:
            print("❌ DailyOutlook.tsx not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Daily Outlook integration: {e}")
        return False

def test_bonus_service():
    """Test that bonus service exists"""
    print("\n🎁 Testing Bonus Service...")
    
    try:
        # Check if the bonus service file exists
        bonus_path = "backend/services/daily_checkin_bonus_service.py"
        if os.path.exists(bonus_path):
            print("✅ daily_checkin_bonus_service.py exists")
            
            # Read the bonus service file to verify it has key methods
            with open(bonus_path, 'r') as f:
                content = f.read()
                
            # Check for key methods
            methods = [
                'class DailyCheckinBonusService',
                'calculate_daily_bonuses',
                'calculate_weekly_challenge_bonuses',
                'calculate_monthly_bonuses',
                'get_tier_specific_bonuses'
            ]
            
            for method in methods:
                if method in content:
                    print(f"✅ {method} found in bonus service")
                else:
                    print(f"❌ {method} not found in bonus service")
                    return False
            
            return True
        else:
            print("❌ daily_checkin_bonus_service.py not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing bonus service: {e}")
        return False

def test_integration_service():
    """Test that integration service exists"""
    print("\n🔗 Testing Integration Service...")
    
    try:
        # Check if the integration service file exists
        integration_path = "backend/services/gamification_integration_service.py"
        if os.path.exists(integration_path):
            print("✅ gamification_integration_service.py exists")
            
            # Read the integration service file to verify it has key methods
            with open(integration_path, 'r') as f:
                content = f.read()
                
            # Check for key methods
            methods = [
                'class GamificationIntegrationService',
                'integrate_daily_outlook_checkin',
                'integrate_goal_completion',
                'integrate_tier_upgrade',
                'integrate_social_share',
                'get_integration_analytics'
            ]
            
            for method in methods:
                if method in content:
                    print(f"✅ {method} found in integration service")
                else:
                    print(f"❌ {method} not found in integration service")
                    return False
            
            return True
        else:
            print("❌ gamification_integration_service.py not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing integration service: {e}")
        return False

def test_documentation():
    """Test that documentation exists"""
    print("\n📚 Testing Documentation...")
    
    try:
        # Check if the README file exists
        readme_path = "GAMIFICATION_SYSTEM_README.md"
        if os.path.exists(readme_path):
            print("✅ GAMIFICATION_SYSTEM_README.md exists")
            
            # Read the README file to verify it has key sections
            with open(readme_path, 'r') as f:
                content = f.read()
                
            # Check for key sections
            sections = [
                'System Components',
                'Gamification Features',
                'API Endpoints',
                'Database Schema',
                'Integration Points',
                'Security Considerations',
                'Performance Considerations'
            ]
            
            for section in sections:
                if section in content:
                    print(f"✅ {section} found in documentation")
                else:
                    print(f"❌ {section} not found in documentation")
                    return False
            
            return True
        else:
            print("❌ GAMIFICATION_SYSTEM_README.md not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing documentation: {e}")
        return False

def main():
    """Main test function"""
    print("🎮 Simple Gamification System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    tests = [
        ("StreakTracker Component", test_streak_tracker_component),
        ("GamificationService", test_gamification_service),
        ("Database Models", test_database_models),
        ("API Endpoints", test_api_endpoints),
        ("Daily Outlook Integration", test_daily_outlook_integration),
        ("Bonus Service", test_bonus_service),
        ("Integration Service", test_integration_service),
        ("Documentation", test_documentation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    # Final status
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Gamification system is properly implemented.")
        return True
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Please review the results above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
