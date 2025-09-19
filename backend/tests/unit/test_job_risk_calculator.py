"""
Unit Tests for JobRiskCalculator

Tests include:
- JobRiskCalculator class methods
- Scoring algorithm edge cases
- Risk level calculations
- Task-based adjustments
- Industry modifiers
- Experience modifiers
- Skill modifiers
- Fuzzy string matching
- Recommendation generation
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.services.JobRiskCalculator import JobRiskCalculator, JobRiskProfile, RiskLevel, Timeframe

class TestJobRiskCalculator(unittest.TestCase):
    """Test suite for JobRiskCalculator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.calculator = JobRiskCalculator(algorithm_version="v1.0")
        self.test_form_data = {
            "job_info": {
                "title": "Software Developer",
                "industry": "technology",
                "experience": 5
            },
            "daily_tasks": {
                "coding": True,
                "meetings": True,
                "documentation": False,
                "testing": True,
                "code_review": True,
                "planning": False
            },
            "work_environment": {
                "ai_usage": "moderate",
                "remote_work": True,
                "team_size": "medium"
            },
            "skills_and_concerns": {
                "tech_skills": ["python", "javascript", "react"],
                "soft_skills": ["communication", "leadership"],
                "concerns": ["automation", "skill_gaps"]
            }
        }
    
    def test_initialization(self):
        """Test JobRiskCalculator initialization"""
        self.assertIsNotNone(self.calculator.job_titles_data)
        self.assertIsNotNone(self.calculator.industry_modifiers)
        self.assertIsNotNone(self.calculator.task_mappings)
        self.assertIsNotNone(self.calculator.recommendation_templates)
        self.assertEqual(self.calculator.algorithm_version, "v1.0")
    
    def test_find_best_job_match_exact(self):
        """Test exact job title matching"""
        title, similarity = self.calculator.find_best_job_match("software developer")
        self.assertEqual(title, "software developer")
        self.assertEqual(similarity, 1.0)
    
    def test_find_best_job_match_fuzzy(self):
        """Test fuzzy job title matching"""
        title, similarity = self.calculator.find_best_job_match("software engineer")
        self.assertIn("software", title.lower())
        self.assertGreater(similarity, 0.7)
    
    def test_find_best_job_match_unknown(self):
        """Test unknown job title handling"""
        title, similarity = self.calculator.find_best_job_match("unknown job title")
        # Should return a default job title
        self.assertIsNotNone(title)
        self.assertLess(similarity, 0.5)
    
    def test_calculate_task_risk(self):
        """Test task-based risk calculation"""
        selected_tasks = ["coding", "testing", "code_review"]
        automation_risk, augmentation_potential = self.calculator.calculate_task_risk(selected_tasks)
        
        self.assertIsInstance(automation_risk, float)
        self.assertIsInstance(augmentation_potential, float)
        self.assertGreaterEqual(automation_risk, 0)
        self.assertLessEqual(automation_risk, 100)
        self.assertGreaterEqual(augmentation_potential, 0)
        self.assertLessEqual(augmentation_potential, 100)
    
    def test_calculate_experience_modifier(self):
        """Test experience modifier calculation"""
        # Test different experience levels
        entry_modifier = self.calculator.calculate_experience_modifier(1)
        mid_modifier = self.calculator.calculate_experience_modifier(5)
        senior_modifier = self.calculator.calculate_experience_modifier(10)
        executive_modifier = self.calculator.calculate_experience_modifier(15)
        
        # Experience should reduce automation risk
        self.assertLess(entry_modifier, 1.0)
        self.assertLess(mid_modifier, 1.0)
        self.assertLess(senior_modifier, 1.0)
        self.assertLess(executive_modifier, 1.0)
        
        # More experience should provide better protection
        self.assertLess(entry_modifier, mid_modifier)
        self.assertLess(mid_modifier, senior_modifier)
    
    def test_calculate_skill_modifier(self):
        """Test skill modifier calculation"""
        # Test different skill levels
        basic_skills = ["excel", "word"]
        intermediate_skills = ["python", "javascript"]
        advanced_skills = ["machine_learning", "ai", "cloud_computing"]
        
        basic_modifier = self.calculator.calculate_skill_modifier(basic_skills, "none")
        intermediate_modifier = self.calculator.calculate_skill_modifier(intermediate_skills, "moderate")
        advanced_modifier = self.calculator.calculate_skill_modifier(advanced_skills, "extensive")
        
        # Advanced skills should provide better protection
        self.assertLess(advanced_modifier, intermediate_modifier)
        self.assertLess(intermediate_modifier, basic_modifier)
    
    def test_calculate_job_risk_basic(self):
        """Test basic job risk calculation"""
        profile = self.calculator.calculate_job_risk(self.test_form_data)
        
        self.assertIsInstance(profile, JobRiskProfile)
        self.assertIsInstance(profile.final_automation_risk, float)
        self.assertIsInstance(profile.final_augmentation_potential, float)
        self.assertIsInstance(profile.overall_risk_score, float)
        self.assertIsInstance(profile.risk_level, RiskLevel)
        self.assertIsInstance(profile.timeframe, Timeframe)
        self.assertIsInstance(profile.confidence, float)
        self.assertIsInstance(profile.recommendations, list)
        self.assertIsInstance(profile.insights, list)
    
    def test_risk_level_classification(self):
        """Test risk level classification edge cases"""
        # Test low risk
        low_risk_data = self.test_form_data.copy()
        low_risk_data["job_info"]["title"] = "executive"
        low_risk_data["job_info"]["experience"] = 15
        low_risk_data["skills_and_concerns"]["tech_skills"] = ["ai", "machine_learning", "strategy"]
        
        low_risk_profile = self.calculator.calculate_job_risk(low_risk_data)
        self.assertEqual(low_risk_profile.risk_level, RiskLevel.LOW)
        
        # Test high risk
        high_risk_data = self.test_form_data.copy()
        high_risk_data["job_info"]["title"] = "data entry clerk"
        high_risk_data["job_info"]["experience"] = 1
        high_risk_data["skills_and_concerns"]["tech_skills"] = ["excel"]
        
        high_risk_profile = self.calculator.calculate_job_risk(high_risk_data)
        self.assertIn(high_risk_profile.risk_level, [RiskLevel.HIGH, RiskLevel.CRITICAL])
    
    def test_industry_modifiers(self):
        """Test industry modifier application"""
        # Test technology industry (should have lower automation risk)
        tech_data = self.test_form_data.copy()
        tech_data["job_info"]["industry"] = "technology"
        tech_profile = self.calculator.calculate_job_risk(tech_data)
        
        # Test manufacturing industry (should have higher automation risk)
        manufacturing_data = self.test_form_data.copy()
        manufacturing_data["job_info"]["industry"] = "manufacturing"
        manufacturing_profile = self.calculator.calculate_job_risk(manufacturing_data)
        
        # Technology should have lower automation risk than manufacturing
        self.assertLess(tech_profile.final_automation_risk, manufacturing_profile.final_automation_risk)
    
    def test_edge_case_empty_data(self):
        """Test edge case with empty form data"""
        empty_data = {}
        profile = self.calculator.calculate_job_risk(empty_data)
        
        # Should handle gracefully and return a profile
        self.assertIsInstance(profile, JobRiskProfile)
        self.assertIsInstance(profile.risk_level, RiskLevel)
    
    def test_edge_case_missing_fields(self):
        """Test edge case with missing fields"""
        incomplete_data = {
            "job_info": {"title": "developer"},
            # Missing other sections
        }
        profile = self.calculator.calculate_job_risk(incomplete_data)
        
        # Should handle gracefully
        self.assertIsInstance(profile, JobRiskProfile)
    
    def test_edge_case_extreme_values(self):
        """Test edge case with extreme values"""
        extreme_data = self.test_form_data.copy()
        extreme_data["job_info"]["experience"] = 50  # Very high experience
        extreme_data["skills_and_concerns"]["tech_skills"] = ["ai", "machine_learning", "deep_learning", "neural_networks"]
        
        profile = self.calculator.calculate_job_risk(extreme_data)
        
        # Should handle extreme values gracefully
        self.assertIsInstance(profile, JobRiskProfile)
        self.assertGreaterEqual(profile.confidence, 0)
        self.assertLessEqual(profile.confidence, 1)
    
    def test_recommendation_generation(self):
        """Test recommendation generation"""
        profile = self.calculator.calculate_job_risk(self.test_form_data)
        
        self.assertIsInstance(profile.recommendations, list)
        self.assertGreater(len(profile.recommendations), 0)
        
        # Check recommendation structure
        for rec in profile.recommendations:
            self.assertIn('category', rec)
            self.assertIn('title', rec)
            self.assertIn('description', rec)
            self.assertIn('priority', rec)
            self.assertIn('timeframe', rec)
    
    def test_insight_generation(self):
        """Test insight generation"""
        profile = self.calculator.calculate_job_risk(self.test_form_data)
        
        self.assertIsInstance(profile.insights, list)
        self.assertGreater(len(profile.insights), 0)
        
        # Check that insights are strings
        for insight in profile.insights:
            self.assertIsInstance(insight, str)
            self.assertGreater(len(insight), 0)
    
    def test_confidence_calculation(self):
        """Test confidence calculation"""
        # High confidence case - complete data
        high_confidence_profile = self.calculator.calculate_job_risk(self.test_form_data)
        
        # Low confidence case - minimal data
        low_confidence_data = {"job_info": {"title": "unknown"}}
        low_confidence_profile = self.calculator.calculate_job_risk(low_confidence_data)
        
        # High confidence should be greater than low confidence
        self.assertGreater(high_confidence_profile.confidence, low_confidence_profile.confidence)
    
    def test_timeframe_assignment(self):
        """Test timeframe assignment logic"""
        # Immediate risk - high automation risk
        immediate_data = self.test_form_data.copy()
        immediate_data["job_info"]["title"] = "data entry clerk"
        immediate_profile = self.calculator.calculate_job_risk(immediate_data)
        
        # Long-term risk - low automation risk, high augmentation
        long_term_data = self.test_form_data.copy()
        long_term_data["job_info"]["title"] = "executive"
        long_term_profile = self.calculator.calculate_job_risk(long_term_data)
        
        # Should assign appropriate timeframes
        self.assertIsInstance(immediate_profile.timeframe, Timeframe)
        self.assertIsInstance(long_term_profile.timeframe, Timeframe)
    
    def test_algorithm_version_tracking(self):
        """Test algorithm version tracking"""
        v1_calculator = JobRiskCalculator("v1.0")
        v2_calculator = JobRiskCalculator("v2.0")
        
        self.assertEqual(v1_calculator.algorithm_version, "v1.0")
        self.assertEqual(v2_calculator.algorithm_version, "v2.0")
    
    def test_performance_under_load(self):
        """Test performance under load"""
        import time
        
        start_time = time.time()
        
        # Calculate risk for multiple assessments
        for i in range(100):
            test_data = self.test_form_data.copy()
            test_data["job_info"]["title"] = f"developer_{i}"
            profile = self.calculator.calculate_job_risk(test_data)
            self.assertIsInstance(profile, JobRiskProfile)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete 100 calculations in reasonable time (< 5 seconds)
        self.assertLess(execution_time, 5.0)
    
    def test_memory_usage(self):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many calculations
        for i in range(1000):
            test_data = self.test_form_data.copy()
            test_data["job_info"]["title"] = f"developer_{i}"
            profile = self.calculator.calculate_job_risk(test_data)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (< 50MB)
        self.assertLess(memory_increase, 50 * 1024 * 1024)
    
    def test_thread_safety(self):
        """Test thread safety of calculations"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def calculate_risk(thread_id):
            for i in range(10):
                test_data = self.test_form_data.copy()
                test_data["job_info"]["title"] = f"developer_thread_{thread_id}_{i}"
                profile = self.calculator.calculate_job_risk(test_data)
                results.put((thread_id, i, profile.risk_level))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=calculate_risk, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        result_count = 0
        while not results.empty():
            thread_id, iteration, risk_level = results.get()
            self.assertIsInstance(risk_level, RiskLevel)
            result_count += 1
        
        # Should have 50 results (5 threads * 10 iterations each)
        self.assertEqual(result_count, 50)

if __name__ == '__main__':
    unittest.main()
