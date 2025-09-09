#!/usr/bin/env python3
"""
Mingus Personal Finance App - Test Fixtures and Mock Data
Comprehensive test data for meme splash page testing
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any

class MemeTestData:
    """Test data for meme splash page testing"""
    
    # Sample meme data for testing
    SAMPLE_MEMES = [
        {
            'id': 1,
            'image_url': 'https://example.com/faith1.jpg',
            'category': 'faith',
            'caption': 'Sunday motivation: Trust the process and keep moving forward',
            'alt_text': 'Faith meme showing trust and perseverance',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 2,
            'image_url': 'https://example.com/work1.jpg',
            'category': 'work_life',
            'caption': 'Monday mood: Coffee first, everything else second',
            'alt_text': 'Coffee and work motivation meme',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 3,
            'image_url': 'https://example.com/health1.jpg',
            'category': 'health',
            'caption': 'Tuesday workout vibes: Your future self will thank you',
            'alt_text': 'Gym motivation and fitness meme',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 4,
            'image_url': 'https://example.com/housing1.jpg',
            'category': 'housing',
            'caption': 'Wednesday house hunting: When you find the perfect place but the price...',
            'alt_text': 'Real estate and housing meme',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 5,
            'image_url': 'https://example.com/transport1.jpg',
            'category': 'transportation',
            'caption': 'Thursday commute: Gas prices be like...',
            'alt_text': 'Gas prices and transportation meme',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 6,
            'image_url': 'https://example.com/relationship1.jpg',
            'category': 'relationships',
            'caption': 'Friday date night: When you budget for dinner but forget about parking',
            'alt_text': 'Date night and relationship finance meme',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 7,
            'image_url': 'https://example.com/family1.jpg',
            'category': 'family',
            'caption': 'Saturday family time: Teaching kids about money one piggy bank at a time',
            'alt_text': 'Family finance education meme',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 8,
            'image_url': 'https://example.com/inactive.jpg',
            'category': 'faith',
            'caption': 'This meme is inactive and should not be selected',
            'alt_text': 'Inactive meme for testing',
            'is_active': 0,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        }
    ]
    
    # Sample user data for testing
    SAMPLE_USERS = [
        {
            'id': 1,
            'username': 'test_user_1',
            'email': 'test1@example.com',
            'created_at': '2024-01-01T00:00:00Z'
        },
        {
            'id': 2,
            'username': 'test_user_2',
            'email': 'test2@example.com',
            'created_at': '2024-01-02T00:00:00Z'
        },
        {
            'id': 3,
            'username': 'test_user_3',
            'email': 'test3@example.com',
            'created_at': '2024-01-03T00:00:00Z'
        }
    ]
    
    # Sample session data for testing
    SAMPLE_SESSIONS = [
        {
            'id': 'session_123',
            'user_id': 1,
            'created_at': '2024-01-15T10:00:00Z',
            'expires_at': '2024-01-15T22:00:00Z'
        },
        {
            'id': 'session_456',
            'user_id': 2,
            'created_at': '2024-01-15T11:00:00Z',
            'expires_at': '2024-01-15T23:00:00Z'
        }
    ]
    
    # Sample analytics data for testing
    SAMPLE_ANALYTICS = [
        {
            'id': 1,
            'meme_id': 1,
            'action': 'view',
            'user_id': '1',
            'session_id': 'session_123',
            'timestamp': '2024-01-15T10:30:00Z',
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla/5.0 (Test Browser)'
        },
        {
            'id': 2,
            'meme_id': 1,
            'action': 'continue',
            'user_id': '1',
            'session_id': 'session_123',
            'timestamp': '2024-01-15T10:31:00Z',
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla/5.0 (Test Browser)'
        },
        {
            'id': 3,
            'meme_id': 2,
            'action': 'view',
            'user_id': '2',
            'session_id': 'session_456',
            'timestamp': '2024-01-15T11:00:00Z',
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla/5.0 (Test Browser)'
        },
        {
            'id': 4,
            'meme_id': 2,
            'action': 'skip',
            'user_id': '2',
            'session_id': 'session_456',
            'timestamp': '2024-01-15T11:01:00Z',
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla/5.0 (Test Browser)'
        }
    ]
    
    # Sample mood data for testing
    SAMPLE_MOOD_DATA = [
        {
            'id': 1,
            'user_id': 1,
            'session_id': 'session_123',
            'meme_id': 1,
            'mood_score': 4,
            'mood_label': 'happy',
            'timestamp': '2024-01-15T10:30:00Z',
            'meme_category': 'faith',
            'spending_context': 'before_budget_check'
        },
        {
            'id': 2,
            'user_id': 1,
            'session_id': 'session_123',
            'meme_id': 2,
            'mood_score': 5,
            'mood_label': 'excited',
            'timestamp': '2024-01-16T10:30:00Z',
            'meme_category': 'work_life',
            'spending_context': 'before_budget_check'
        },
        {
            'id': 3,
            'user_id': 2,
            'session_id': 'session_456',
            'meme_id': 3,
            'mood_score': 2,
            'mood_label': 'sad',
            'timestamp': '2024-01-15T11:00:00Z',
            'meme_category': 'health',
            'spending_context': 'before_budget_check'
        },
        {
            'id': 4,
            'user_id': 1,
            'session_id': 'session_789',
            'meme_id': 4,
            'mood_score': 3,
            'mood_label': 'neutral',
            'timestamp': '2024-01-17T10:30:00Z',
            'meme_category': 'housing',
            'spending_context': 'before_budget_check'
        }
    ]
    
    # Sample user meme history for testing
    SAMPLE_USER_HISTORY = [
        {
            'id': 1,
            'user_id': 1,
            'meme_id': 1,
            'viewed_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 2,
            'user_id': 1,
            'meme_id': 2,
            'viewed_at': '2024-01-14T10:30:00Z'
        },
        {
            'id': 3,
            'user_id': 2,
            'meme_id': 3,
            'viewed_at': '2024-01-13T10:30:00Z'
        }
    ]
    
    # Edge case test data
    EDGE_CASE_MEMES = [
        {
            'id': 100,
            'image_url': 'https://example.com/very_long_url_that_might_cause_issues_with_database_storage_and_should_be_handled_properly_by_the_system.jpg',
            'category': 'faith',
            'caption': 'A' * 1000,  # Very long caption
            'alt_text': 'Alt text with special characters: !@#$%^&*()_+-=[]{}|;:,.<>?',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 101,
            'image_url': 'https://example.com/unicode_meme.jpg',
            'category': 'work_life',
            'caption': 'Unicode test: 🚀💼💰📊🎯🔥💪',
            'alt_text': 'Unicode alt text: 🎨🌈⭐️🌟✨💫',
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        },
        {
            'id': 102,
            'image_url': 'https://example.com/sql_injection_test.jpg',
            'category': 'health',
            'caption': "'; DROP TABLE memes; --",
            'alt_text': "'; DROP TABLE memes; --",
            'is_active': 1,
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-15T10:30:00Z'
        }
    ]
    
    # Performance test data
    PERFORMANCE_TEST_MEMES = []
    
    @classmethod
    def generate_performance_test_data(cls, num_memes: int = 1000):
        """Generate large dataset for performance testing"""
        categories = ['faith', 'work_life', 'health', 'housing', 'transportation', 'relationships', 'family']
        
        for i in range(num_memes):
            category = categories[i % len(categories)]
            cls.PERFORMANCE_TEST_MEMES.append({
                'id': i + 1,
                'image_url': f'https://example.com/perf_test_{category}_{i}.jpg',
                'category': category,
                'caption': f'Performance test meme {i} for {category} category',
                'alt_text': f'Alt text for performance test meme {i}',
                'is_active': 1,
                'created_at': '2024-01-15T10:30:00Z',
                'updated_at': '2024-01-15T10:30:00Z'
            })
        
        return cls.PERFORMANCE_TEST_MEMES
    
    @classmethod
    def get_meme_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """Get all memes for a specific category"""
        return [meme for meme in cls.SAMPLE_MEMES if meme['category'] == category and meme['is_active'] == 1]
    
    @classmethod
    def get_meme_by_id(cls, meme_id: int) -> Dict[str, Any]:
        """Get a specific meme by ID"""
        for meme in cls.SAMPLE_MEMES:
            if meme['id'] == meme_id:
                return meme
        return None
    
    @classmethod
    def get_active_memes(cls) -> List[Dict[str, Any]]:
        """Get all active memes"""
        return [meme for meme in cls.SAMPLE_MEMES if meme['is_active'] == 1]
    
    @classmethod
    def get_inactive_memes(cls) -> List[Dict[str, Any]]:
        """Get all inactive memes"""
        return [meme for meme in cls.SAMPLE_MEMES if meme['is_active'] == 0]


class DatabaseTestSetup:
    """Helper class for setting up test databases"""
    
    @staticmethod
    def create_test_database(db_path: str, include_performance_data: bool = False) -> str:
        """Create a test database with sample data"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_url TEXT NOT NULL,
                    category TEXT NOT NULL,
                    caption TEXT NOT NULL,
                    alt_text TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_meme_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    meme_id INTEGER NOT NULL,
                    viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, meme_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meme_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meme_id INTEGER NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('view', 'continue', 'skip', 'auto_advance')),
                    user_id TEXT,
                    session_id TEXT,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (meme_id) REFERENCES memes (id)
                )
            """)
            
            # Insert sample memes
            memes_data = [(meme['image_url'], meme['category'], meme['caption'], 
                          meme['alt_text'], meme['is_active']) for meme in MemeTestData.SAMPLE_MEMES]
            
            cursor.executemany("""
                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, memes_data)
            
            # Insert edge case memes
            edge_case_data = [(meme['image_url'], meme['category'], meme['caption'], 
                             meme['alt_text'], meme['is_active']) for meme in MemeTestData.EDGE_CASE_MEMES]
            
            cursor.executemany("""
                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, edge_case_data)
            
            # Insert performance test data if requested
            if include_performance_data:
                performance_memes = MemeTestData.generate_performance_test_data()
                perf_data = [(meme['image_url'], meme['category'], meme['caption'], 
                            meme['alt_text'], meme['is_active']) for meme in performance_memes]
                
                cursor.executemany("""
                    INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                    VALUES (?, ?, ?, ?, ?)
                """, perf_data)
            
            # Insert user history
            history_data = [(h['user_id'], h['meme_id'], h['viewed_at']) 
                           for h in MemeTestData.SAMPLE_USER_HISTORY]
            
            cursor.executemany("""
                INSERT INTO user_meme_history (user_id, meme_id, viewed_at)
                VALUES (?, ?, ?)
            """, history_data)
            
            # Insert analytics data
            analytics_data = [(a['meme_id'], a['action'], a['user_id'], a['session_id'], 
                             a['timestamp'], a['ip_address'], a['user_agent']) 
                             for a in MemeTestData.SAMPLE_ANALYTICS]
            
            cursor.executemany("""
                INSERT INTO meme_analytics (meme_id, action, user_id, session_id, timestamp, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, analytics_data)
            
            # Insert mood data
            mood_data = [(m['user_id'], m['session_id'], m['meme_id'], m['mood_score'], 
                         m['mood_label'], m['timestamp'], m['meme_category'], m['spending_context']) 
                         for m in MemeTestData.SAMPLE_MOOD_DATA]
            
            cursor.executemany("""
                INSERT INTO user_mood_data (user_id, session_id, meme_id, mood_score, mood_label, timestamp, meme_category, spending_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, mood_data)
            
            conn.commit()
        
        return db_path
    
    @staticmethod
    def create_empty_database(db_path: str) -> str:
        """Create an empty database with just the schema"""
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables only
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_url TEXT NOT NULL,
                    category TEXT NOT NULL,
                    caption TEXT NOT NULL,
                    alt_text TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_meme_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    meme_id INTEGER NOT NULL,
                    viewed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, meme_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meme_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    meme_id INTEGER NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('view', 'continue', 'skip', 'auto_advance')),
                    user_id TEXT,
                    session_id TEXT,
                    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (meme_id) REFERENCES memes (id)
                )
            """)
            
            conn.commit()
        
        return db_path


class MockAPIData:
    """Mock data for API testing"""
    
    # Mock API responses
    MOCK_MEME_RESPONSE = {
        'id': 1,
        'image_url': 'https://example.com/meme1.jpg',
        'category': 'faith',
        'caption': 'Sunday motivation: Trust the process',
        'alt_text': 'Faith meme showing trust',
        'is_active': True,
        'created_at': '2024-01-15T10:30:00Z',
        'updated_at': '2024-01-15T10:30:00Z'
    }
    
    MOCK_ANALYTICS_RESPONSE = {
        'success': True,
        'message': 'Analytics tracked successfully'
    }
    
    MOCK_STATS_RESPONSE = {
        'total_memes': 7,
        'analytics_last_7_days': [
            {
                'action': 'view',
                'count': 150,
                'unique_users': 45,
                'unique_sessions': 67
            },
            {
                'action': 'continue',
                'count': 120,
                'unique_users': 40,
                'unique_sessions': 60
            },
            {
                'action': 'skip',
                'count': 30,
                'unique_users': 15,
                'unique_sessions': 20
            }
        ],
        'popular_memes': [
            {
                'id': 1,
                'caption': 'Sunday motivation: Trust the process',
                'category': 'faith',
                'view_count': 45
            },
            {
                'id': 2,
                'caption': 'Monday mood: Coffee first',
                'category': 'work_life',
                'view_count': 38
            }
        ]
    }
    
    # Mock error responses
    MOCK_ERROR_RESPONSES = {
        'no_memes': {
            'error': 'No memes available',
            'message': 'No active memes found in the database'
        },
        'database_error': {
            'error': 'Internal server error',
            'message': 'Failed to fetch meme'
        },
        'invalid_request': {
            'error': 'Bad request',
            'message': 'Missing required field: meme_id'
        },
        'invalid_action': {
            'error': 'Bad request',
            'message': 'Invalid action. Must be one of: view, continue, skip, auto_advance'
        }
    }
    
    # Mock request headers
    MOCK_HEADERS = {
        'valid_user': {
            'X-User-ID': 'user123',
            'X-Session-ID': 'session456',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Test Browser)'
        },
        'invalid_user': {
            'X-User-ID': 'invalid_user',
            'X-Session-ID': 'invalid_session'
        },
        'no_headers': {}
    }


class FrontendTestData:
    """Test data for frontend component testing"""
    
    # Mock meme data for React components
    MOCK_MEME_DATA = {
        'id': 1,
        'image_url': 'https://example.com/meme1.jpg',
        'category': 'faith',
        'caption': 'Sunday motivation: Trust the process and keep moving forward',
        'alt_text': 'Faith meme showing trust and perseverance',
        'is_active': True,
        'created_at': '2024-01-15T10:30:00Z',
        'updated_at': '2024-01-15T10:30:00Z'
    }
    
    # Mock user props for components
    MOCK_USER_PROPS = {
        'userId': 'user123',
        'sessionId': 'session456',
        'autoAdvanceDelay': 10000,
        'className': 'test-class'
    }
    
    # Mock callback functions
    MOCK_CALLBACKS = {
        'onContinue': lambda: print('Continue clicked'),
        'onSkip': lambda: print('Skip clicked')
    }
    
    # Mock error states
    MOCK_ERROR_STATES = {
        'network_error': 'Failed to fetch meme: 500 Internal Server Error',
        'image_load_error': 'Failed to load meme image',
        'api_error': 'Failed to load meme',
        'timeout_error': 'Request timeout'
    }
    
    # Mock loading states
    MOCK_LOADING_STATES = {
        'initial_loading': True,
        'retry_loading': True,
        'analytics_loading': True,
        'not_loading': False
    }


class PerformanceTestData:
    """Test data for performance testing"""
    
    # Performance benchmarks
    BENCHMARKS = {
        'meme_selection_time': 0.1,  # seconds
        'api_response_time': 0.5,    # seconds
        'database_query_time': 0.05, # seconds
        'image_load_time': 2.0,      # seconds
        'component_render_time': 0.1 # seconds
    }
    
    # Load test scenarios
    LOAD_TEST_SCENARIOS = {
        'light_load': {
            'concurrent_users': 10,
            'requests_per_user': 5,
            'duration_minutes': 1
        },
        'medium_load': {
            'concurrent_users': 50,
            'requests_per_user': 10,
            'duration_minutes': 5
        },
        'heavy_load': {
            'concurrent_users': 100,
            'requests_per_user': 20,
            'duration_minutes': 10
        }
    }
    
    # Memory usage limits
    MEMORY_LIMITS = {
        'max_memory_increase_mb': 10,
        'max_memory_usage_mb': 100,
        'gc_threshold_mb': 50
    }


def export_test_data_to_json(output_file: str):
    """Export all test data to a JSON file for external use"""
    test_data = {
        'memes': MemeTestData.SAMPLE_MEMES,
        'users': MemeTestData.SAMPLE_USERS,
        'sessions': MemeTestData.SAMPLE_SESSIONS,
        'analytics': MemeTestData.SAMPLE_ANALYTICS,
        'user_history': MemeTestData.SAMPLE_USER_HISTORY,
        'edge_cases': MemeTestData.EDGE_CASE_MEMES,
        'mock_api_responses': MockAPIData.MOCK_MEME_RESPONSE,
        'mock_error_responses': MockAPIData.MOCK_ERROR_RESPONSES,
        'frontend_data': FrontendTestData.MOCK_MEME_DATA,
        'performance_benchmarks': PerformanceTestData.BENCHMARKS
    }
    
    with open(output_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"Test data exported to {output_file}")


if __name__ == '__main__':
    # Export test data
    export_test_data_to_json('meme_splash_test_data.json')
    
    # Generate performance test data
    performance_memes = MemeTestData.generate_performance_test_data(100)
    print(f"Generated {len(performance_memes)} performance test memes")
    
    # Print summary
    print(f"\nTest Data Summary:")
    print(f"  - Sample memes: {len(MemeTestData.SAMPLE_MEMES)}")
    print(f"  - Sample users: {len(MemeTestData.SAMPLE_USERS)}")
    print(f"  - Sample sessions: {len(MemeTestData.SAMPLE_SESSIONS)}")
    print(f"  - Sample analytics: {len(MemeTestData.SAMPLE_ANALYTICS)}")
    print(f"  - Edge case memes: {len(MemeTestData.EDGE_CASE_MEMES)}")
    print(f"  - Performance test memes: {len(performance_memes)}")
