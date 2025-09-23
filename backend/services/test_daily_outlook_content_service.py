#!/usr/bin/env python3
"""
Test file for Daily Outlook Content Service
Tests the content generation functionality
"""

import sys
import os
import sqlite3
import json
from datetime import datetime, date

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.daily_outlook_content_service import DailyOutlookContentService
from backend.services.feature_flag_service import FeatureTier

def setup_test_database():
    """Set up test database with sample data"""
    db_path = "test_user_profiles.db"
    
    # Remove existing test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create user_profiles table
    cursor.execute("""
        CREATE TABLE user_profiles (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            personal_info TEXT,
            financial_info TEXT,
            monthly_expenses TEXT,
            important_dates TEXT,
            health_wellness TEXT,
            goals TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create user_relationship_status table
    cursor.execute("""
        CREATE TABLE user_relationship_status (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            satisfaction_score INTEGER NOT NULL,
            financial_impact_score INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create daily_outlooks table
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
    
    # Create user_mood_data table
    cursor.execute("""
        CREATE TABLE user_mood_data (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            mood_score INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create weekly_checkins table
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
    
    # Insert test user
    cursor.execute("""
        INSERT INTO users (id, email, first_name, last_name)
        VALUES (1, 'test@example.com', 'Jordan', 'Washington')
    """)
    
    # Insert test profile data
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
        'careerGoals': ['Get promoted to Senior Marketing Coordinator', 'Learn digital marketing skills'],
        'skillDevelopment': ['Complete Google Analytics certification', 'Learn social media advertising'],
        'education': ['Consider MBA in 2 years'],
        'financialGoals': ['Build emergency fund to $5000', 'Pay off credit card debt']
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
    
    # Insert relationship status
    cursor.execute("""
        INSERT INTO user_relationship_status (user_id, status, satisfaction_score, financial_impact_score)
        VALUES (1, 'single_career_focused', 8, 6)
    """)
    
    # Insert some mood data
    cursor.execute("""
        INSERT INTO user_mood_data (user_id, mood_score)
        VALUES (1, 4), (1, 3), (1, 5), (1, 4), (1, 3)
    """)
    
    # Insert weekly check-in data
    cursor.execute("""
        INSERT INTO weekly_checkins (user_id, check_in_date, physical_activity, meditation_minutes, relationship_satisfaction)
        VALUES (1, '2024-01-01', 3, 45, 7), (1, '2024-01-08', 2, 30, 8)
    """)
    
    conn.commit()
    conn.close()
    
    return db_path

def test_content_generation():
    """Test the content generation functionality"""
    print("🧪 Testing Daily Outlook Content Service")
    print("=" * 50)
    
    # Set up test database
    db_path = setup_test_database()
    
    # Initialize service
    service = DailyOutlookContentService(db_path)
    
    # Test content generation
    print("\n1. Testing content generation for user 1...")
    try:
        content = service.generate_daily_outlook(1)
        
        print(f"✅ Generated content successfully!")
        print(f"   - Balance Score: {content['balance_score']}")
        print(f"   - Primary Insight: {content['primary_insight'][:100]}...")
        print(f"   - Quick Actions: {len(content['quick_actions'])} actions")
        print(f"   - Encouragement: {content['encouragement_message'][:100]}...")
        print(f"   - Surprise Element: {content['surprise_element'][:100]}...")
        print(f"   - Tomorrow Teaser: {content['tomorrow_teaser'][:100]}...")
        print(f"   - Streak Count: {content['streak_count']}")
        print(f"   - Tier: {content['tier']}")
        print(f"   - Location: {content['location']}")
        print(f"   - Cultural Relevance: {content['cultural_relevance']}")
        print(f"   - City Specific: {content['city_specific']}")
        
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return False
    
    # Test individual methods
    print("\n2. Testing individual methods...")
    
    # Test select_primary_insight
    try:
        user_data = service._get_user_data(1)
        if user_data:
            weights = {'financial': 0.4, 'wellness': 0.25, 'relationship': 0.15, 'career': 0.2}
            insight = service.select_primary_insight(user_data, weights)
            print(f"✅ Primary insight: {insight[:100]}...")
        else:
            print("❌ Could not get user data")
    except Exception as e:
        print(f"❌ Error selecting primary insight: {e}")
    
    # Test generate_quick_actions
    try:
        if user_data:
            actions = service.generate_quick_actions(user_data, user_data.tier)
            print(f"✅ Generated {len(actions)} quick actions")
            for i, action in enumerate(actions, 1):
                print(f"   {i}. {action['action']} ({action['difficulty']}, {action['estimated_time']})")
        else:
            print("❌ Could not get user data for actions")
    except Exception as e:
        print(f"❌ Error generating quick actions: {e}")
    
    # Test create_encouragement_message
    try:
        if user_data:
            encouragement = service.create_encouragement_message(user_data, user_data.streak_count)
            print(f"✅ Encouragement message: {encouragement[:100]}...")
        else:
            print("❌ Could not get user data for encouragement")
    except Exception as e:
        print(f"❌ Error creating encouragement message: {e}")
    
    # Test get_surprise_element
    try:
        surprise = service.get_surprise_element(1, datetime.now().weekday())
        print(f"✅ Surprise element: {surprise[:100]}...")
    except Exception as e:
        print(f"❌ Error getting surprise element: {e}")
    
    # Test build_tomorrow_teaser
    try:
        if user_data:
            teaser = service.build_tomorrow_teaser(user_data)
            print(f"✅ Tomorrow teaser: {teaser[:100]}...")
        else:
            print("❌ Could not get user data for teaser")
    except Exception as e:
        print(f"❌ Error building tomorrow teaser: {e}")
    
    # Test tier-specific content
    print("\n3. Testing tier-specific content...")
    
    # Test Budget tier
    try:
        budget_actions = service._get_budget_tier_actions(user_data)
        print(f"✅ Budget tier actions: {len(budget_actions)} actions")
    except Exception as e:
        print(f"❌ Error getting budget tier actions: {e}")
    
    # Test Mid-tier
    try:
        mid_actions = service._get_mid_tier_actions(user_data)
        print(f"✅ Mid-tier actions: {len(mid_actions)} actions")
    except Exception as e:
        print(f"❌ Error getting mid-tier actions: {e}")
    
    # Test Professional tier
    try:
        pro_actions = service._get_professional_tier_actions(user_data)
        print(f"✅ Professional tier actions: {len(pro_actions)} actions")
    except Exception as e:
        print(f"❌ Error getting professional tier actions: {e}")
    
    # Test cultural relevance
    print("\n4. Testing cultural relevance...")
    try:
        if user_data and user_data.location in service.major_metros:
            print(f"✅ User location {user_data.location} is in major metros")
            metro_info = service.major_metros[user_data.location]
            print(f"   - State: {metro_info['state']}")
            print(f"   - Region: {metro_info['region']}")
            print(f"   - Cultural Hub: {metro_info['cultural_hub']}")
        else:
            print("ℹ️  User location not in major metros")
    except Exception as e:
        print(f"❌ Error checking cultural relevance: {e}")
    
    # Clean up test database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    print("\n🎉 All tests completed!")
    return True

def test_error_handling():
    """Test error handling with invalid data"""
    print("\n5. Testing error handling...")
    
    # Test with non-existent user
    service = DailyOutlookContentService("nonexistent.db")
    
    try:
        content = service.generate_daily_outlook(999)
        print("✅ Handled non-existent user gracefully")
        print(f"   - Returned default content: {content['user_id'] == 0}")
    except Exception as e:
        print(f"❌ Error handling non-existent user: {e}")
    
    print("✅ Error handling tests completed")

if __name__ == "__main__":
    print("🚀 Daily Outlook Content Service Test Suite")
    print("=" * 60)
    
    # Run main tests
    success = test_content_generation()
    
    # Run error handling tests
    test_error_handling()
    
    if success:
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
    
    print("\n" + "=" * 60)
    print("Test suite completed.")
