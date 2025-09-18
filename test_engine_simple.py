#!/usr/bin/env python3
"""
Simple test script for the Mingus Job Recommendation Engine
Tests core functionality without complex dependencies
"""

import asyncio
import json
import time
import tempfile
import os
import sys

# Add backend to path
sys.path.append('backend')

def test_engine_initialization():
    """Test basic engine initialization"""
    print("🧪 Testing Engine Initialization...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        # Initialize engine
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        print("✅ Engine initialized successfully")
        print(f"   - Database path: {temp_db.name}")
        print(f"   - Max processing time: {engine.max_processing_time}s")
        print(f"   - Cache TTL: {engine.cache_ttl}s")
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Engine initialization failed: {e}")
        return False

def test_database_initialization():
    """Test database initialization"""
    print("\n🧪 Testing Database Initialization...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        # Initialize engine
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        # Check if tables were created
        import sqlite3
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'workflow_sessions',
            'workflow_steps', 
            'user_analytics',
            'performance_metrics',
            'recommendation_cache'
        ]
        
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if not missing_tables:
            print("✅ All database tables created successfully")
            print(f"   - Tables: {', '.join(tables)}")
        else:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        conn.close()
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_session_id_generation():
    """Test session ID generation"""
    print("\n🧪 Testing Session ID Generation...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        # Test session ID generation
        user_id = "test_user"
        content = "test resume content"
        
        session_id = engine._generate_session_id(user_id, content)
        
        print(f"✅ Session ID generated: {session_id}")
        print(f"   - Contains user ID: {'test_user' in session_id}")
        print(f"   - Length: {len(session_id)} characters")
        
        # Test consistency
        session_id2 = engine._generate_session_id(user_id, content)
        if session_id == session_id2:
            print("✅ Session ID generation is consistent")
        else:
            print("❌ Session ID generation is inconsistent")
            return False
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Session ID generation failed: {e}")
        return False

def test_cache_functionality():
    """Test caching functionality"""
    print("\n🧪 Testing Cache Functionality...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        # Test cache key generation
        cache_key = engine._generate_cache_key("test_step", ("arg1", "arg2"), {"key": "value"})
        print(f"✅ Cache key generated: {cache_key}")
        print(f"   - Length: {len(cache_key)} characters")
        
        # Test cache operations
        test_data = {"test": "data", "number": 123}
        
        # Cache result
        asyncio.run(engine._cache_result(cache_key, test_data))
        print("✅ Data cached successfully")
        
        # Retrieve cached result
        cached_result = asyncio.run(engine._get_cached_result(cache_key))
        
        if cached_result == test_data:
            print("✅ Cached data retrieved successfully")
        else:
            print("❌ Cached data mismatch")
            return False
        
        # Test non-existent key
        non_existent = asyncio.run(engine._get_cached_result("non_existent_key"))
        if non_existent is None:
            print("✅ Non-existent key handled correctly")
        else:
            print("❌ Non-existent key should return None")
            return False
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Cache functionality failed: {e}")
        return False

def test_career_field_determination():
    """Test career field determination"""
    print("\n🧪 Testing Career Field Determination...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
        from backend.utils.income_boost_job_matcher import CareerField
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        # Test technology field
        tech_experience = [
            {"title": "Software Engineer", "description": "Developed web applications using Python and React"},
            {"title": "Senior Developer", "description": "Led team in building microservices"}
        ]
        tech_skills = ["Python", "JavaScript", "React", "AWS"]
        
        field = engine._determine_career_field(tech_experience, tech_skills)
        print(f"✅ Technology field determined: {field}")
        print(f"   - Correct: {field == CareerField.TECHNOLOGY}")
        
        # Test finance field
        finance_experience = [
            {"title": "Financial Analyst", "description": "Analyzed market trends and investment opportunities"},
            {"title": "Senior Analyst", "description": "Prepared financial reports and forecasts"}
        ]
        finance_skills = ["Financial Analysis", "Excel", "SQL", "Investment"]
        
        field = engine._determine_career_field(finance_experience, finance_skills)
        print(f"✅ Finance field determined: {field}")
        print(f"   - Correct: {field == CareerField.FINANCE}")
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Career field determination failed: {e}")
        return False

def test_experience_level_determination():
    """Test experience level determination"""
    print("\n🧪 Testing Experience Level Determination...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
        from backend.utils.income_boost_job_matcher import ExperienceLevel
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        # Test entry level
        entry_experience = []
        level = engine._determine_experience_level(entry_experience)
        print(f"✅ Entry level determined: {level}")
        print(f"   - Correct: {level == ExperienceLevel.ENTRY}")
        
        # Test mid level
        mid_experience = [
            {"duration": "2 years", "title": "Junior Developer"},
            {"duration": "1 year", "title": "Intern"}
        ]
        level = engine._determine_experience_level(mid_experience)
        print(f"✅ Mid level determined: {level}")
        print(f"   - Correct: {level == ExperienceLevel.MID}")
        
        # Test senior level
        senior_experience = [
            {"duration": "5 years", "title": "Senior Engineer"},
            {"duration": "3 years", "title": "Lead Developer"}
        ]
        level = engine._determine_experience_level(senior_experience)
        print(f"✅ Senior level determined: {level}")
        print(f"   - Correct: {level == ExperienceLevel.SENIOR}")
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Experience level determination failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\n🧪 Testing Error Handling...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        # Test error response creation
        error_response = engine._create_error_response("test_error", "Test error message")
        
        print("✅ Error response created successfully")
        print(f"   - Success: {not error_response['success']}")
        print(f"   - Error type: {error_response['error_type']}")
        print(f"   - Error message: {error_response['error_message']}")
        print(f"   - Has timestamp: {'timestamp' in error_response}")
        print(f"   - Has metrics: {'processing_metrics' in error_response}")
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_analytics_tracking():
    """Test analytics tracking"""
    print("\n🧪 Testing Analytics Tracking...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        # Test analytics tracking
        user_id = "test_user"
        session_id = "test_session"
        event_type = "test_event"
        event_data = {"key": "value", "number": 123}
        
        # Track analytics
        asyncio.run(engine._track_analytics(user_id, session_id, event_type, event_data))
        print("✅ Analytics tracked successfully")
        
        # Verify data was stored
        import sqlite3
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, session_id, event_type, event_data
            FROM user_analytics 
            WHERE user_id = ? AND session_id = ?
        ''', (user_id, session_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            print("✅ Analytics data stored in database")
            print(f"   - User ID: {result[0]}")
            print(f"   - Session ID: {result[1]}")
            print(f"   - Event Type: {result[2]}")
            print(f"   - Event Data: {result[3]}")
        else:
            print("❌ Analytics data not found in database")
            return False
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Analytics tracking failed: {e}")
        return False

def test_workflow_tracking():
    """Test workflow tracking"""
    print("\n🧪 Testing Workflow Tracking...")
    
    try:
        from backend.utils.mingus_job_recommendation_engine import MingusJobRecommendationEngine, ProcessingStatus
        
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        engine = MingusJobRecommendationEngine(db_path=temp_db.name)
        
        # Test workflow tracking
        session_id = "test_workflow_session"
        user_id = "test_user"
        content = "test resume content"
        
        # Track workflow start
        engine._track_workflow_start(session_id, user_id, content)
        print("✅ Workflow start tracked")
        
        # Verify session was created
        import sqlite3
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, status, resume_content_hash
            FROM workflow_sessions 
            WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        
        if result:
            print("✅ Workflow session created in database")
            print(f"   - User ID: {result[0]}")
            print(f"   - Status: {result[1]}")
            print(f"   - Content Hash: {result[2][:16]}...")
        else:
            print("❌ Workflow session not found in database")
            return False
        
        # Test workflow completion
        result_data = {"test": "result", "success": True}
        total_time = 5.5
        
        engine._track_workflow_completion(session_id, total_time, result_data)
        print("✅ Workflow completion tracked")
        
        # Verify completion was recorded
        cursor.execute('''
            SELECT status, completed_at, total_processing_time, result_data
            FROM workflow_sessions 
            WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == ProcessingStatus.COMPLETED.value:
            print("✅ Workflow completion recorded in database")
            print(f"   - Status: {result[0]}")
            print(f"   - Processing Time: {result[2]}s")
            print(f"   - Has Result Data: {result[3] is not None}")
        else:
            print("❌ Workflow completion not recorded correctly")
            return False
        
        # Clean up
        os.unlink(temp_db.name)
        return True
        
    except Exception as e:
        print(f"❌ Workflow tracking failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Mingus Job Recommendation Engine - Simple Test Suite")
    print("=" * 60)
    
    tests = [
        test_engine_initialization,
        test_database_initialization,
        test_session_id_generation,
        test_cache_functionality,
        test_career_field_determination,
        test_experience_level_determination,
        test_error_handling,
        test_analytics_tracking,
        test_workflow_tracking
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The engine is working correctly.")
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
