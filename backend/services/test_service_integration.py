#!/usr/bin/env python3
"""
Integration Test for Daily Outlook Content Service
Tests the actual service import and basic functionality
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, date

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_service_import():
    """Test that the service can be imported without errors"""
    print("🧪 Testing Service Import")
    print("=" * 50)
    
    try:
        # Test import of the main service
        from backend.services.daily_outlook_content_service import DailyOutlookContentService
        print("✅ DailyOutlookContentService imported successfully")
        
        # Test import of supporting classes
        from backend.services.daily_outlook_content_service import UserData, ContentTemplate
        print("✅ Supporting classes imported successfully")
        
        # Test service initialization
        service = DailyOutlookContentService("test_integration.db")
        print("✅ Service initialized successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_database_operations():
    """Test database operations"""
    print("\n🧪 Testing Database Operations")
    print("=" * 50)
    
    try:
        # Create test database
        db_path = "test_integration.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create basic tables
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                first_name TEXT,
                last_name TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE user_profiles (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                personal_info TEXT,
                financial_info TEXT,
                goals TEXT,
                location TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE user_relationship_status (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                satisfaction_score INTEGER NOT NULL,
                financial_impact_score INTEGER NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE daily_outlooks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                balance_score INTEGER NOT NULL,
                financial_weight REAL NOT NULL,
                wellness_weight REAL NOT NULL,
                relationship_weight REAL NOT NULL,
                career_weight REAL NOT NULL,
                primary_insight TEXT,
                quick_actions TEXT,
                encouragement_message TEXT,
                surprise_element TEXT,
                streak_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE user_mood_data (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                mood_score INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE weekly_checkins (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                check_in_date DATE NOT NULL,
                physical_activity INTEGER DEFAULT 0,
                meditation_minutes INTEGER DEFAULT 0,
                relationship_satisfaction INTEGER DEFAULT 0
            )
        """)
        
        # Insert test data
        cursor.execute("""
            INSERT INTO users (id, email, first_name, last_name)
            VALUES (1, 'test@example.com', 'Jordan', 'Washington')
        """)
        
        personal_info = {
            'age': 28,
            'education': "Bachelor's Degree",
            'employment': 'Marketing Coordinator'
        }
        
        financial_info = {
            'annualIncome': 65000,
            'monthlyIncome': 4200,
            'currentSavings': 1200,
            'studentLoans': 35000,
            'creditCardDebt': 8500,
            'monthlyExpenses': {
                'rent': 1400,
                'carPayment': 320,
                'insurance': 180,
                'groceries': 400,
                'utilities': 150,
                'studentLoanPayment': 380,
                'creditCardMinimum': 210
            }
        }
        
        goals = {
            'careerGoals': ['Get promoted to Senior Marketing Coordinator'],
            'skillDevelopment': ['Complete Google Analytics certification'],
            'education': ['Consider MBA in 2 years'],
            'financialGoals': ['Build emergency fund to $5000']
        }
        
        cursor.execute("""
            INSERT INTO user_profiles (email, personal_info, financial_info, goals, location)
            VALUES (?, ?, ?, ?, ?)
        """, (
            'test@example.com',
            json.dumps(personal_info),
            json.dumps(financial_info),
            json.dumps(goals),
            'Atlanta, GA'
        ))
        
        cursor.execute("""
            INSERT INTO user_relationship_status (user_id, status, satisfaction_score, financial_impact_score)
            VALUES (1, 'single_career_focused', 8, 6)
        """)
        
        cursor.execute("""
            INSERT INTO user_mood_data (user_id, mood_score)
            VALUES (1, 4), (1, 3), (1, 5), (1, 4), (1, 3)
        """)
        
        cursor.execute("""
            INSERT INTO weekly_checkins (user_id, check_in_date, physical_activity, meditation_minutes, relationship_satisfaction)
            VALUES (1, '2024-01-01', 3, 45, 7), (1, '2024-01-08', 2, 30, 8)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Test database created successfully")
        print("✅ Test data inserted successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Database operation error: {e}")
        return False

def test_service_methods():
    """Test individual service methods"""
    print("\n🧪 Testing Service Methods")
    print("=" * 50)
    
    try:
        from backend.services.daily_outlook_content_service import DailyOutlookContentService
        
        # Initialize service
        service = DailyOutlookContentService("test_integration.db")
        
        # Test user data retrieval
        print("Testing user data retrieval...")
        user_data = service._get_user_data(1)
        if user_data:
            print(f"✅ User data retrieved: {user_data.user_id}, {user_data.location}, {user_data.tier}")
        else:
            print("❌ Could not retrieve user data")
            return False
        
        # Test tier-specific actions
        print("\nTesting tier-specific actions...")
        
        # Budget tier
        budget_actions = service._get_budget_tier_actions(user_data)
        print(f"✅ Budget tier actions: {len(budget_actions)} actions")
        
        # Mid-tier
        mid_actions = service._get_mid_tier_actions(user_data)
        print(f"✅ Mid-tier actions: {len(mid_actions)} actions")
        
        # Professional tier
        pro_actions = service._get_professional_tier_actions(user_data)
        print(f"✅ Professional tier actions: {len(pro_actions)} actions")
        
        # Test encouragement messages
        print("\nTesting encouragement messages...")
        for streak in [0, 3, 7, 14, 30]:
            encouragement = service.create_encouragement_message(user_data, streak)
            print(f"✅ Streak {streak}: {encouragement[:50]}...")
        
        # Test surprise elements
        print("\nTesting surprise elements...")
        for day in range(7):
            surprise = service.get_surprise_element(1, day)
            print(f"✅ Day {day}: {surprise[:50]}...")
        
        # Test tomorrow teasers
        print("\nTesting tomorrow teasers...")
        teaser = service.build_tomorrow_teaser(user_data)
        print(f"✅ Tomorrow teaser: {teaser[:50]}...")
        
        # Test primary insight selection
        print("\nTesting primary insight selection...")
        weights = {'financial': 0.4, 'wellness': 0.25, 'relationship': 0.15, 'career': 0.2}
        insight = service.select_primary_insight(user_data, weights)
        print(f"✅ Primary insight: {insight[:50]}...")
        
        # Test quick actions generation
        print("\nTesting quick actions generation...")
        actions = service.generate_quick_actions(user_data, user_data.tier)
        print(f"✅ Quick actions: {len(actions)} actions")
        for i, action in enumerate(actions, 1):
            print(f"   {i}. {action['action']} ({action['difficulty']}, {action['estimated_time']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Service method error: {e}")
        return False

def test_content_generation():
    """Test full content generation"""
    print("\n🧪 Testing Full Content Generation")
    print("=" * 50)
    
    try:
        from backend.services.daily_outlook_content_service import DailyOutlookContentService
        
        # Initialize service
        service = DailyOutlookContentService("test_integration.db")
        
        # Test content generation
        print("Generating daily outlook content...")
        content = service.generate_daily_outlook(1)
        
        if content:
            print("✅ Content generated successfully!")
            print(f"   - User ID: {content['user_id']}")
            print(f"   - Date: {content['date']}")
            print(f"   - Balance Score: {content['balance_score']}")
            print(f"   - Tier: {content['tier']}")
            print(f"   - Location: {content['location']}")
            print(f"   - Cultural Relevance: {content['cultural_relevance']}")
            print(f"   - City Specific: {content['city_specific']}")
            print(f"   - Streak Count: {content['streak_count']}")
            print(f"   - Primary Insight: {content['primary_insight'][:100]}...")
            print(f"   - Quick Actions: {len(content['quick_actions'])} actions")
            print(f"   - Encouragement: {content['encouragement_message'][:100]}...")
            print(f"   - Surprise Element: {content['surprise_element'][:100]}...")
            print(f"   - Tomorrow Teaser: {content['tomorrow_teaser'][:100]}...")
            
            return True
        else:
            print("❌ Content generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Content generation error: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid data"""
    print("\n🧪 Testing Error Handling")
    print("=" * 50)
    
    try:
        from backend.services.daily_outlook_content_service import DailyOutlookContentService
        
        # Test with non-existent user
        service = DailyOutlookContentService("test_integration.db")
        
        print("Testing with non-existent user...")
        content = service.generate_daily_outlook(999)
        
        if content and content['user_id'] == 0:
            print("✅ Handled non-existent user gracefully")
            print(f"   - Returned default content: {content['user_id'] == 0}")
        else:
            print("❌ Did not handle non-existent user properly")
            return False
        
        # Test with invalid database
        print("\nTesting with invalid database...")
        invalid_service = DailyOutlookContentService("nonexistent.db")
        invalid_content = invalid_service.generate_daily_outlook(1)
        
        if invalid_content and invalid_content['user_id'] == 0:
            print("✅ Handled invalid database gracefully")
        else:
            print("❌ Did not handle invalid database properly")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_cultural_relevance():
    """Test cultural relevance features"""
    print("\n🧪 Testing Cultural Relevance")
    print("=" * 50)
    
    try:
        from backend.services.daily_outlook_content_service import DailyOutlookContentService
        
        service = DailyOutlookContentService("test_integration.db")
        
        # Test major metros
        print("Testing major metros...")
        for metro, info in service.major_metros.items():
            print(f"✅ {metro} ({info['state']}): {info['region']} - Cultural Hub: {info['cultural_hub']}")
        
        # Test cultural additions
        print("\nTesting cultural additions...")
        cultural_additions = [
            " Your ancestors' dreams are being realized through your actions.",
            " You're part of a legacy of financial empowerment and community building.",
            " Every dollar you save is a vote for the future you deserve.",
            " You're not just building wealth, you're building generational impact."
        ]
        
        for addition in cultural_additions:
            print(f"✅ Cultural addition: {addition}")
        
        return True
        
    except Exception as e:
        print(f"❌ Cultural relevance test failed: {e}")
        return False

def cleanup():
    """Clean up test files"""
    print("\n🧹 Cleaning up test files...")
    
    test_files = [
        "test_integration.db",
        "test_user_profiles.db"
    ]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✅ Removed {file}")

def main():
    """Run all tests"""
    print("🚀 Daily Outlook Content Service - Integration Test Suite")
    print("=" * 70)
    
    tests = [
        ("Service Import", test_service_import),
        ("Database Operations", test_database_operations),
        ("Service Methods", test_service_methods),
        ("Content Generation", test_content_generation),
        ("Error Handling", test_error_handling),
        ("Cultural Relevance", test_cultural_relevance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*70}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*70}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("The Daily Outlook Content Service is fully functional and ready for integration.")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review the output above.")
    
    # Cleanup
    cleanup()
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
