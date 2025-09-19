#!/usr/bin/env python3
"""
Test script for weekly check-in integration with vehicle questions
"""

import sqlite3
import json
import requests
import sys
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_USER_ID = "test_user_123"
TEST_SESSION_ID = "test_session_456"

def test_weekly_checkin_submission():
    """Test submitting a weekly check-in with vehicle questions"""
    print("🧪 Testing weekly check-in submission...")
    
    # Sample check-in data
    checkin_data = {
        "check_in_date": datetime.now().strftime("%Y-%m-%d"),
        "healthWellness": {
            "physicalActivity": 4,
            "relationshipSatisfaction": 8,
            "meditationMinutes": 60,
            "stressSpending": 120.50
        },
        "vehicleWellness": {
            "vehicleExpenses": 150.00,
            "transportationStress": 2,
            "commuteSatisfaction": 4,
            "vehicleDecisions": "Got new tires, researched insurance options, planned maintenance schedule"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/weekly-checkin",
            headers={
                "Content-Type": "application/json",
                "X-User-ID": TEST_USER_ID,
                "X-Session-ID": TEST_SESSION_ID
            },
            json=checkin_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Weekly check-in submission successful")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Weekly check-in submission failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_weekly_checkin_retrieval():
    """Test retrieving weekly check-in data"""
    print("\n🧪 Testing weekly check-in retrieval...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/weekly-checkin/latest",
            headers={
                "X-User-ID": TEST_USER_ID
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Latest check-in retrieval successful")
            print(f"   Check-in data: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Check-in retrieval failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_weekly_checkin_analytics():
    """Test retrieving weekly check-in analytics"""
    print("\n🧪 Testing weekly check-in analytics...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/weekly-checkin/analytics",
            headers={
                "X-User-ID": TEST_USER_ID
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Analytics retrieval successful")
            print(f"   Analytics: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Analytics retrieval failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_database_schema():
    """Test that the database schema is properly created"""
    print("\n🧪 Testing database schema...")
    
    try:
        conn = sqlite3.connect("mingus_memes.db")
        cursor = conn.cursor()
        
        # Check if weekly_checkins table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='weekly_checkins'
        """)
        
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ weekly_checkins table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(weekly_checkins)")
            columns = cursor.fetchall()
            
            expected_columns = [
                'user_id', 'check_in_date', 'week_start_date',
                'physical_activity', 'relationship_satisfaction', 
                'meditation_minutes', 'stress_spending',
                'vehicle_expenses', 'transportation_stress', 
                'commute_satisfaction', 'vehicle_decisions'
            ]
            
            column_names = [col[1] for col in columns]
            missing_columns = [col for col in expected_columns if col not in column_names]
            
            if not missing_columns:
                print("✅ All expected columns present")
                return True
            else:
                print(f"❌ Missing columns: {missing_columns}")
                return False
        else:
            print("❌ weekly_checkins table does not exist")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Run all tests"""
    print("🚀 Starting Weekly Check-in Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Check-in Submission", test_weekly_checkin_submission),
        ("Check-in Retrieval", test_weekly_checkin_retrieval),
        ("Analytics Retrieval", test_weekly_checkin_analytics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Weekly check-in integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
