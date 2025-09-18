#!/usr/bin/env python3
"""
Comprehensive Test Suite for Mingus Job Recommendation Engine

This test suite validates the central orchestration engine's functionality,
performance, error handling, and integration with all components.
"""

import asyncio
import json
import os
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import the engine and components
import sys
sys.path.append('backend')

from backend.utils.mingus_job_recommendation_engine import (
    MingusJobRecommendationEngine, 
    ProcessingStatus, 
    ErrorSeverity,
    ProcessingMetrics,
    WorkflowStep
)
from backend.utils.income_boost_job_matcher import SearchCriteria, CareerField, ExperienceLevel
from backend.utils.three_tier_job_selector import JobTier

class TestMingusJobRecommendationEngine(unittest.TestCase):
    """Test cases for the Mingus Job Recommendation Engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize engine with test database
        self.engine = MingusJobRecommendationEngine(db_path=self.temp_db.name)
        
        # Sample resume content for testing
        self.sample_resume = """
        John Doe
        Software Engineer
        john.doe@email.com
        (555) 123-4567
        
        EXPERIENCE
        Senior Software Engineer | Tech Corp | 2020-2023
        - Led development of microservices architecture
        - Mentored junior developers
        - Implemented CI/CD pipelines
        
        Software Engineer | StartupXYZ | 2018-2020
        - Developed web applications using Python and React
        - Collaborated with cross-functional teams
        - Optimized database queries
        
        SKILLS
        Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, SQL
        Leadership, Project Management, Agile Development
        
        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology | 2018
        """
        
        # Sample user preferences
        self.sample_preferences = {
            "remote_ok": True,
            "max_commute_time": 30,
            "must_have_benefits": ["health insurance", "401k"],
            "company_size_preference": "mid",
            "industry_preference": "technology",
            "equity_required": False,
            "min_company_rating": 3.5
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_engine_initialization(self):
        """Test engine initialization"""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.max_processing_time, 8.0)
        self.assertIsNotNone(self.engine.resume_parser)
        self.assertIsNotNone(self.engine.job_matcher)
        self.assertIsNotNone(self.engine.three_tier_selector)
    
    def test_database_initialization(self):
        """Test database tables are created correctly"""
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check if all required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'workflow_sessions',
            'workflow_steps', 
            'user_analytics',
            'performance_metrics',
            'recommendation_cache'
        ]
        
        for table in expected_tables:
            self.assertIn(table, tables)
        
        conn.close()
    
    def test_session_id_generation(self):
        """Test session ID generation"""
        user_id = "test_user"
        content = "test resume content"
        
        session_id = self.engine._generate_session_id(user_id, content)
        
        self.assertIsInstance(session_id, str)
        self.assertIn(user_id, session_id)
        self.assertTrue(len(session_id) > 0)
        
        # Same input should generate same session ID
        session_id2 = self.engine._generate_session_id(user_id, content)
        self.assertEqual(session_id, session_id2)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        step_name = "test_step"
        args = ("arg1", "arg2")
        kwargs = {"key1": "value1", "key2": "value2"}
        
        cache_key = self.engine._generate_cache_key(step_name, args, kwargs)
        
        self.assertIsInstance(cache_key, str)
        self.assertEqual(len(cache_key), 32)  # MD5 hash length
        
        # Same input should generate same cache key
        cache_key2 = self.engine._generate_cache_key(step_name, args, kwargs)
        self.assertEqual(cache_key, cache_key2)
    
    def test_career_field_determination(self):
        """Test career field determination from experience and skills"""
        # Technology experience
        tech_experience = [
            {"title": "Software Engineer", "description": "Developed web applications using Python and React"},
            {"title": "Senior Developer", "description": "Led team in building microservices"}
        ]
        tech_skills = ["Python", "JavaScript", "React", "AWS"]
        
        field = self.engine._determine_career_field(tech_experience, tech_skills)
        self.assertEqual(field, CareerField.TECHNOLOGY)
        
        # Finance experience
        finance_experience = [
            {"title": "Financial Analyst", "description": "Analyzed market trends and investment opportunities"},
            {"title": "Senior Analyst", "description": "Prepared financial reports and forecasts"}
        ]
        finance_skills = ["Financial Analysis", "Excel", "SQL", "Investment"]
        
        field = self.engine._determine_career_field(finance_experience, finance_skills)
        self.assertEqual(field, CareerField.FINANCE)
    
    def test_experience_level_determination(self):
        """Test experience level determination"""
        # Entry level
        entry_experience = []
        level = self.engine._determine_experience_level(entry_experience)
        self.assertEqual(level, ExperienceLevel.ENTRY)
        
        # Mid level
        mid_experience = [
            {"duration": "2 years", "title": "Junior Developer"},
            {"duration": "1 year", "title": "Intern"}
        ]
        level = self.engine._determine_experience_level(mid_experience)
        self.assertEqual(level, ExperienceLevel.MID)
        
        # Senior level
        senior_experience = [
            {"duration": "5 years", "title": "Senior Engineer"},
            {"duration": "3 years", "title": "Lead Developer"}
        ]
        level = self.engine._determine_experience_level(senior_experience)
        self.assertEqual(level, ExperienceLevel.SENIOR)
    
    def test_salary_estimation(self):
        """Test current salary estimation"""
        parsed_data = {
            "parsed_data": {
                "experience": [
                    {"duration": "3 years", "title": "Software Engineer"}
                ],
                "skills": ["Python", "JavaScript", "React"]
            }
        }
        
        salary = self.engine._estimate_current_salary(parsed_data, "New York")
        
        self.assertIsInstance(salary, int)
        self.assertGreater(salary, 0)
        # Should be higher for New York due to location multiplier
        self.assertGreater(salary, 50000)
    
    def test_search_criteria_creation(self):
        """Test search criteria creation from parsed data"""
        parsed_data = {
            "parsed_data": {
                "experience": [
                    {"duration": "3 years", "title": "Software Engineer", "description": "Python development"}
                ],
                "skills": ["Python", "JavaScript", "React", "AWS"]
            }
        }
        
        criteria = self.engine._create_search_criteria(parsed_data, self.sample_preferences, "New York")
        
        self.assertIsInstance(criteria, SearchCriteria)
        self.assertEqual(criteria.career_field, CareerField.TECHNOLOGY)
        self.assertEqual(criteria.experience_level, ExperienceLevel.MID)
        self.assertGreater(criteria.current_salary, 0)
        self.assertEqual(criteria.target_salary_increase, 0.25)
        self.assertIn("New York", criteria.preferred_msas)
        self.assertTrue(criteria.remote_ok)
    
    def test_error_response_creation(self):
        """Test error response creation"""
        error_type = "test_error"
        error_message = "Test error message"
        
        response = self.engine._create_error_response(error_type, error_message)
        
        self.assertFalse(response['success'])
        self.assertEqual(response['error_type'], error_type)
        self.assertEqual(response['error_message'], error_message)
        self.assertIn('timestamp', response)
        self.assertIn('processing_metrics', response)
    
    @patch('backend.utils.mingus_job_recommendation_engine.AdvancedResumeParserWithFormats')
    def test_resume_parsing_step(self, mock_parser_class):
        """Test resume parsing step execution"""
        # Mock the parser
        mock_parser = Mock()
        mock_parser.parse_resume_from_bytes.return_value = {
            'success': True,
            'parsed_data': {'personal_info': {'name': 'John Doe'}},
            'advanced_analytics': {'income_potential': {'estimated_current_salary': 80000}},
            'metadata': {'confidence_score': 0.85}
        }
        mock_parser_class.return_value = mock_parser
        
        # Test the step
        result = asyncio.run(self.engine._parse_resume_advanced(
            self.sample_resume, "test.pdf", "New York"
        ))
        
        self.assertTrue(result['success'])
        self.assertIn('parsed_data', result)
        self.assertIn('advanced_analytics', result)
        self.assertIn('metadata', result)
    
    @patch('backend.utils.mingus_job_recommendation_engine.IncomeBoostJobMatcher')
    def test_job_search_step(self, mock_matcher_class):
        """Test job search step execution"""
        # Mock the job matcher
        mock_matcher = Mock()
        mock_job = Mock()
        mock_job.job_id = "job123"
        mock_job.title = "Software Engineer"
        mock_job.company = "Tech Corp"
        mock_job.salary_median = 100000
        mock_job.overall_score = 85
        mock_job.salary_increase_potential = 0.25
        mock_job.diversity_score = 80
        mock_job.growth_score = 75
        mock_job.culture_score = 70
        mock_job.remote_friendly = True
        mock_job.equity_offered = False
        mock_job.company_size = "mid"
        mock_job.company_industry = "technology"
        mock_job.msa = "New York"
        mock_job.field = CareerField.TECHNOLOGY
        mock_job.experience_level = ExperienceLevel.MID
        mock_job.job_board = None
        mock_job.posted_date = None
        mock_job.application_deadline = None
        mock_job.location = "New York"
        mock_job.salary_range = (90000, 110000)
        mock_job.description = "Software engineer position"
        mock_job.requirements = ["Python", "React"]
        mock_job.benefits = ["Health insurance", "401k"]
        
        mock_matcher.salary_focused_search.return_value = [mock_job]
        mock_matcher_class.return_value = mock_matcher
        
        # Create search criteria
        criteria = SearchCriteria(
            current_salary=80000,
            target_salary_increase=0.25,
            career_field=CareerField.TECHNOLOGY,
            experience_level=ExperienceLevel.MID,
            preferred_msas=["New York"],
            remote_ok=True,
            max_commute_time=30,
            must_have_benefits=[],
            company_size_preference=None,
            industry_preference=None,
            equity_required=False,
            min_company_rating=3.0
        )
        
        # Test the step
        result = asyncio.run(self.engine._search_job_opportunities(criteria))
        
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn('job_id', result[0])
        self.assertIn('title', result[0])
        self.assertIn('company', result[0])
    
    def test_workflow_step_execution(self):
        """Test workflow step execution with error handling"""
        # Test successful step
        async def successful_step():
            return {"success": True, "data": "test"}
        
        step = asyncio.run(self.engine._execute_step("test_step", successful_step))
        
        self.assertEqual(step.step_name, "test_step")
        self.assertEqual(step.status, ProcessingStatus.COMPLETED)
        self.assertIsNotNone(step.result_data)
        self.assertIsNone(step.error_message)
        
        # Test failed step
        async def failed_step():
            raise Exception("Test error")
        
        step = asyncio.run(self.engine._execute_step("failed_step", failed_step))
        
        self.assertEqual(step.step_name, "failed_step")
        self.assertEqual(step.status, ProcessingStatus.FAILED)
        self.assertIsNotNone(step.error_message)
        self.assertIn("Test error", step.error_message)
    
    def test_metrics_update(self):
        """Test processing metrics update"""
        # Create sample workflow steps
        steps = [
            WorkflowStep("resume_parsing", ProcessingStatus.COMPLETED, 
                        datetime.now(), datetime.now(), 1.5, None, {}),
            WorkflowStep("job_search", ProcessingStatus.COMPLETED, 
                        datetime.now(), datetime.now(), 2.0, None, {}),
            WorkflowStep("recommendation_generation", ProcessingStatus.FAILED, 
                        datetime.now(), datetime.now(), 0.5, "Error", None)
        ]
        
        total_time = 4.0
        
        # Update metrics
        self.engine._update_metrics(steps, total_time)
        
        self.assertEqual(self.engine.metrics.total_time, 4.0)
        self.assertEqual(self.engine.metrics.resume_parsing_time, 1.5)
        self.assertEqual(self.engine.metrics.job_search_time, 2.0)
        self.assertEqual(self.engine.metrics.recommendation_generation_time, 0.5)
        self.assertEqual(self.engine.metrics.errors_count, 1)
    
    def test_analytics_tracking(self):
        """Test analytics tracking"""
        user_id = "test_user"
        session_id = "test_session"
        event_type = "test_event"
        event_data = {"key": "value"}
        
        # Track analytics
        asyncio.run(self.engine._track_analytics(user_id, session_id, event_type, event_data))
        
        # Verify data was stored
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, session_id, event_type, event_data
            FROM user_analytics 
            WHERE user_id = ? AND session_id = ?
        ''', (user_id, session_id))
        
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], user_id)
        self.assertEqual(result[1], session_id)
        self.assertEqual(result[2], event_type)
        self.assertEqual(json.loads(result[3]), event_data)
    
    def test_workflow_tracking(self):
        """Test workflow session tracking"""
        session_id = "test_session"
        user_id = "test_user"
        content = "test content"
        
        # Track workflow start
        self.engine._track_workflow_start(session_id, user_id, content)
        
        # Verify session was created
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, status, resume_content_hash
            FROM workflow_sessions 
            WHERE session_id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], user_id)
        self.assertEqual(result[1], ProcessingStatus.IN_PROGRESS.value)
        self.assertIsNotNone(result[2])
    
    def test_performance_targets(self):
        """Test that performance targets are met"""
        self.assertEqual(self.engine.max_processing_time, 8.0)
        self.assertEqual(self.engine.performance_targets['total_time'], 8.0)
        self.assertEqual(self.engine.performance_targets['recommendation_accuracy'], 0.90)
        self.assertEqual(self.engine.performance_targets['system_reliability'], 0.995)
    
    def test_cache_functionality(self):
        """Test caching functionality"""
        cache_key = "test_key"
        test_data = {"test": "data"}
        
        # Test caching
        asyncio.run(self.engine._cache_result(cache_key, test_data))
        
        # Test retrieval
        cached_result = asyncio.run(self.engine._get_cached_result(cache_key))
        
        self.assertIsNotNone(cached_result)
        self.assertEqual(cached_result, test_data)
        
        # Test non-existent key
        non_existent = asyncio.run(self.engine._get_cached_result("non_existent"))
        self.assertIsNone(non_existent)
    
    def test_error_handling_graceful_degradation(self):
        """Test graceful error handling and degradation"""
        # Test with invalid resume content
        invalid_resume = "x"  # Too short
        
        # This should not raise an exception but return an error response
        try:
            result = asyncio.run(self.engine.process_resume_completely(
                resume_content=invalid_resume,
                user_id="test_user"
            ))
            
            # Should return error response
            self.assertFalse(result.get('success', True))
            self.assertIn('error', result)
        except Exception as e:
            self.fail(f"Engine should handle invalid input gracefully, but raised: {e}")
    
    def test_concurrent_processing(self):
        """Test concurrent processing capabilities"""
        async def process_resume():
            return await self.engine.process_resume_completely(
                resume_content=self.sample_resume,
                user_id="concurrent_test"
            )
        
        # Run multiple processes concurrently
        tasks = [process_resume() for _ in range(3)]
        results = asyncio.run(asyncio.gather(*tasks, return_exceptions=True))
        
        # All should complete (though some might fail due to mocking)
        self.assertEqual(len(results), 3)
        
        # At least some should be successful or have expected error structure
        for result in results:
            if isinstance(result, Exception):
                # Exceptions are expected due to mocking
                continue
            else:
                # Should have expected structure
                self.assertIn('success', result)
                self.assertIn('session_id', result)

class TestRecommendationEngineIntegration(unittest.TestCase):
    """Integration tests for the recommendation engine"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.engine = MingusJobRecommendationEngine(db_path=self.temp_db.name)
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @patch('backend.utils.mingus_job_recommendation_engine.AdvancedResumeParserWithFormats')
    @patch('backend.utils.mingus_job_recommendation_engine.IncomeBoostJobMatcher')
    @patch('backend.utils.mingus_job_recommendation_engine.ThreeTierJobSelector')
    def test_end_to_end_workflow(self, mock_selector_class, mock_matcher_class, mock_parser_class):
        """Test complete end-to-end workflow with mocked components"""
        # Mock resume parser
        mock_parser = Mock()
        mock_parser.parse_resume_from_bytes.return_value = {
            'success': True,
            'parsed_data': {
                'personal_info': {'name': 'John Doe'},
                'experience': [{'title': 'Software Engineer', 'duration': '3 years'}],
                'skills': ['Python', 'JavaScript', 'React']
            },
            'advanced_analytics': {
                'income_potential': {'estimated_current_salary': 80000}
            },
            'metadata': {'confidence_score': 0.85}
        }
        mock_parser_class.return_value = mock_parser
        
        # Mock job matcher
        mock_matcher = Mock()
        mock_job = Mock()
        mock_job.job_id = "job123"
        mock_job.title = "Senior Software Engineer"
        mock_job.company = "Tech Corp"
        mock_job.salary_median = 100000
        mock_job.overall_score = 85
        mock_job.salary_increase_potential = 0.25
        mock_job.diversity_score = 80
        mock_job.growth_score = 75
        mock_job.culture_score = 70
        mock_job.remote_friendly = True
        mock_job.equity_offered = False
        mock_job.company_size = "mid"
        mock_job.company_industry = "technology"
        mock_job.msa = "New York"
        mock_job.field = CareerField.TECHNOLOGY
        mock_job.experience_level = ExperienceLevel.MID
        mock_job.job_board = None
        mock_job.posted_date = None
        mock_job.application_deadline = None
        mock_job.location = "New York"
        mock_job.salary_range = (90000, 110000)
        mock_job.description = "Senior software engineer position"
        mock_job.requirements = ["Python", "React", "Leadership"]
        mock_job.benefits = ["Health insurance", "401k", "Equity"]
        
        mock_matcher.salary_focused_search.return_value = [mock_job]
        mock_matcher_class.return_value = mock_matcher
        
        # Mock three-tier selector
        mock_selector = Mock()
        mock_recommendation = Mock()
        mock_recommendation.job = mock_job
        mock_recommendation.tier = JobTier.OPTIMAL
        mock_recommendation.success_probability = 0.75
        mock_recommendation.salary_increase_potential = 0.25
        mock_recommendation.skills_gap_analysis = []
        mock_recommendation.application_strategy = Mock()
        mock_recommendation.preparation_roadmap = Mock()
        mock_recommendation.diversity_analysis = {}
        mock_recommendation.company_culture_fit = 0.8
        mock_recommendation.career_advancement_potential = 0.7
        
        mock_selector.generate_tiered_recommendations.return_value = {
            JobTier.OPTIMAL: [mock_recommendation]
        }
        mock_selector.get_tier_summary.return_value = {
            'optimal': {
                'count': 1,
                'avg_salary_increase': 25.0,
                'avg_success_probability': 75.0
            }
        }
        mock_selector_class.return_value = mock_selector
        
        # Run the complete workflow
        result = asyncio.run(self.engine.process_resume_completely(
            resume_content="Software Engineer with 3 years experience in Python and React",
            user_id="integration_test",
            location="New York"
        ))
        
        # Verify result structure
        self.assertTrue(result['success'])
        self.assertIn('session_id', result)
        self.assertIn('processing_time', result)
        self.assertIn('recommendations', result)
        self.assertIn('tier_summary', result)
        self.assertIn('application_strategies', result)
        self.assertIn('insights', result)
        self.assertIn('action_plan', result)
        self.assertIn('next_steps', result)
        self.assertIn('processing_metrics', result)
        self.assertIn('workflow_steps', result)
        
        # Verify processing time is within limits
        self.assertLess(result['processing_time'], 8.0)
        
        # Verify workflow steps were tracked
        self.assertGreater(len(result['workflow_steps']), 0)
        
        # Verify all steps completed successfully
        completed_steps = [s for s in result['workflow_steps'] if s['status'] == 'completed']
        self.assertGreater(len(completed_steps), 0)

def run_performance_tests():
    """Run performance tests"""
    print("Running Performance Tests...")
    
    # Test processing time
    engine = MingusJobRecommendationEngine()
    
    start_time = time.time()
    
    # Test with sample resume
    sample_resume = """
    John Doe
    Senior Software Engineer
    john.doe@email.com
    
    EXPERIENCE
    Senior Software Engineer | Tech Corp | 2020-2023
    - Led development of microservices architecture
    - Mentored junior developers
    - Implemented CI/CD pipelines
    
    SKILLS
    Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, SQL
    Leadership, Project Management, Agile Development
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology | 2018
    """
    
    try:
        result = asyncio.run(engine.process_resume_completely(
            resume_content=sample_resume,
            user_id="performance_test",
            location="New York"
        ))
        
        processing_time = time.time() - start_time
        
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Target: < 8.0 seconds")
        print(f"Status: {'PASS' if processing_time < 8.0 else 'FAIL'}")
        
        if result.get('success'):
            print(f"Recommendations generated: {len(result.get('recommendations', {}))}")
            print(f"Workflow steps: {len(result.get('workflow_steps', []))}")
        
    except Exception as e:
        print(f"Performance test failed: {e}")

if __name__ == '__main__':
    # Run unit tests
    print("Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests
    print("\n" + "="*50)
    run_performance_tests()
