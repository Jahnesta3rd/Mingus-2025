"""
Unit Tests for AssessmentScoringService

Tests include:
- AssessmentScoringService class methods
- EXACT algorithm implementation
- Component scoring calculations
- Risk level classifications
- Field salary multipliers
- Confidence interval calculations
- Edge cases and error handling
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.services.assessment_scoring_service import (
    AssessmentScoringService, 
    JobRiskScore, 
    RelationshipScore, 
    AssessmentScoringResult,
    RiskLevel,
    RelationshipSegment
)

class TestAssessmentScoringService(unittest.TestCase):
    """Test suite for AssessmentScoringService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_config = {
            'FIELD_SALARY_MULTIPLIERS': {
                'Software Development': 1.2,
                'data_analysis': 1.1,
                'project_management': 1.0,
                'marketing': 0.95,
                'finance': 1.05,
                'sales': 0.9,
                'operations': 0.95,
                'hr': 0.9
            },
            'RISK_LEVEL_THRESHOLDS': {
                'low': 0.3,
                'medium': 0.6,
                'high': 0.8,
                'critical': 1.0
            }
        }
        
        self.scoring_service = AssessmentScoringService(
            self.mock_db_session, 
            self.mock_config
        )
        
        self.test_assessment_data = {
            'current_salary': 75000,
            'field': 'Software Development',
            'experience_level': 'Mid',
            'company_size': 'large',
            'location': 'urban',
            'industry': 'technology',
            'skills': ['python', 'javascript', 'react'],
            'required_skills': ['python', 'javascript', 'react', 'node.js'],
            'daily_tasks': {
                'coding': True,
                'meetings': True,
                'documentation': False,
                'testing': True
            },
            'work_environment': {
                'ai_usage': 'moderate',
                'remote_work': True,
                'team_size': 'medium'
            },
            'skills_and_concerns': {
                'tech_skills': ['python', 'javascript'],
                'soft_skills': ['communication', 'leadership'],
                'concerns': ['automation', 'skill_gaps']
            }
        }
    
    def test_initialization(self):
        """Test AssessmentScoringService initialization"""
        self.assertIsNotNone(self.scoring_service)
        self.assertEqual(self.scoring_service.db, self.mock_db_session)
        self.assertEqual(self.scoring_service.config, self.mock_config)
    
    def test_calculate_salary_score(self):
        """Test salary score calculation"""
        # Test normal salary
        salary_score = self.scoring_service._calculate_salary_score(75000, 'Software Development')
        self.assertIsInstance(salary_score, float)
        self.assertGreaterEqual(salary_score, 0)
        self.assertLessEqual(salary_score, 1)
        
        # Test high salary
        high_salary_score = self.scoring_service._calculate_salary_score(150000, 'Software Development')
        self.assertGreater(high_salary_score, salary_score)
        
        # Test low salary
        low_salary_score = self.scoring_service._calculate_salary_score(30000, 'Software Development')
        self.assertLess(low_salary_score, salary_score)
        
        # Test edge case - zero salary
        zero_salary_score = self.scoring_service._calculate_salary_score(0, 'Software Development')
        self.assertEqual(zero_salary_score, 0)
    
    def test_calculate_skills_score(self):
        """Test skills score calculation"""
        # Test good skills match
        skills_score = self.scoring_service._calculate_skills_score(self.test_assessment_data)
        self.assertIsInstance(skills_score, float)
        self.assertGreaterEqual(skills_score, 0)
        self.assertLessEqual(skills_score, 1)
        
        # Test perfect skills match
        perfect_match_data = self.test_assessment_data.copy()
        perfect_match_data['skills'] = ['python', 'javascript', 'react', 'node.js']
        perfect_match_data['required_skills'] = ['python', 'javascript', 'react', 'node.js']
        perfect_skills_score = self.scoring_service._calculate_skills_score(perfect_match_data)
        self.assertEqual(perfect_skills_score, 1.0)
        
        # Test no skills match
        no_match_data = self.test_assessment_data.copy()
        no_match_data['skills'] = ['java', 'c++']
        no_match_data['required_skills'] = ['python', 'javascript', 'react', 'node.js']
        no_match_skills_score = self.scoring_service._calculate_skills_score(no_match_data)
        self.assertEqual(no_match_skills_score, 0.0)
        
        # Test no required skills specified
        no_required_data = self.test_assessment_data.copy()
        no_required_data['required_skills'] = []
        default_skills_score = self.scoring_service._calculate_skills_score(no_required_data)
        self.assertEqual(default_skills_score, 0.5)  # Default score
    
    def test_calculate_career_score(self):
        """Test career score calculation"""
        # Test different experience levels
        entry_score = self.scoring_service._calculate_career_score('Entry', 'Software Development')
        mid_score = self.scoring_service._calculate_career_score('Mid', 'Software Development')
        senior_score = self.scoring_service._calculate_career_score('Senior', 'Software Development')
        executive_score = self.scoring_service._calculate_career_score('Executive', 'Software Development')
        
        # Higher experience should have higher scores
        self.assertLess(entry_score, mid_score)
        self.assertLess(mid_score, senior_score)
        self.assertLess(senior_score, executive_score)
        
        # All scores should be between 0 and 1
        for score in [entry_score, mid_score, senior_score, executive_score]:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
    
    def test_calculate_company_score(self):
        """Test company score calculation"""
        # Test different company sizes
        startup_score = self.scoring_service._calculate_company_score('startup')
        small_score = self.scoring_service._calculate_company_score('small')
        medium_score = self.scoring_service._calculate_company_score('medium')
        large_score = self.scoring_service._calculate_company_score('large')
        enterprise_score = self.scoring_service._calculate_company_score('enterprise')
        
        # Larger companies should generally have higher scores (more stability)
        self.assertLess(startup_score, large_score)
        self.assertLess(small_score, enterprise_score)
        
        # All scores should be between 0 and 1
        for score in [startup_score, small_score, medium_score, large_score, enterprise_score]:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
    
    def test_calculate_location_score(self):
        """Test location score calculation"""
        # Test different location types
        national_score = self.scoring_service._calculate_location_score('national')
        urban_score = self.scoring_service._calculate_location_score('urban')
        suburban_score = self.scoring_service._calculate_location_score('suburban')
        rural_score = self.scoring_service._calculate_location_score('rural')
        
        # Urban areas should generally have higher scores (more opportunities)
        self.assertGreater(urban_score, rural_score)
        self.assertGreater(suburban_score, rural_score)
        
        # All scores should be between 0 and 1
        for score in [national_score, urban_score, suburban_score, rural_score]:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
    
    def test_calculate_growth_score(self):
        """Test growth score calculation"""
        # Test different industries
        tech_score = self.scoring_service._calculate_growth_score('technology')
        healthcare_score = self.scoring_service._calculate_growth_score('healthcare')
        finance_score = self.scoring_service._calculate_growth_score('finance')
        manufacturing_score = self.scoring_service._calculate_growth_score('manufacturing')
        
        # Technology should have higher growth potential
        self.assertGreater(tech_score, manufacturing_score)
        
        # All scores should be between 0 and 1
        for score in [tech_score, healthcare_score, finance_score, manufacturing_score]:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
    
    def test_exact_algorithm_implementation(self):
        """Test EXACT algorithm implementation with correct weights"""
        # Calculate individual component scores
        salary_score = self.scoring_service._calculate_salary_score(75000, 'Software Development')
        skills_score = self.scoring_service._calculate_skills_score(self.test_assessment_data)
        career_score = self.scoring_service._calculate_career_score('Mid', 'Software Development')
        company_score = self.scoring_service._calculate_company_score('large')
        location_score = self.scoring_service._calculate_location_score('urban')
        growth_score = self.scoring_service._calculate_growth_score('technology')
        
        # Calculate expected overall score using EXACT algorithm
        expected_overall_score = (
            salary_score * 0.35 +      # 35% weight - Primary importance
            skills_score * 0.25 +      # 25% weight - Skills alignment 
            career_score * 0.20 +      # 20% weight - Career progression
            company_score * 0.10 +     # 10% weight - Company quality
            location_score * 0.05 +    # 5% weight - Location fit
            growth_score * 0.05        # 5% weight - Industry alignment
        )
        
        # Calculate actual overall score
        job_risk = self.scoring_service._calculate_ai_job_risk(self.test_assessment_data)
        actual_overall_score = job_risk.overall_score
        
        # Should match exactly
        self.assertAlmostEqual(actual_overall_score, expected_overall_score, places=6)
        
        # Verify component scores are stored correctly
        self.assertEqual(job_risk.salary_score, salary_score)
        self.assertEqual(job_risk.skills_score, skills_score)
        self.assertEqual(job_risk.career_score, career_score)
        self.assertEqual(job_risk.company_score, company_score)
        self.assertEqual(job_risk.location_score, location_score)
        self.assertEqual(job_risk.growth_score, growth_score)
    
    def test_field_salary_multipliers(self):
        """Test field salary multipliers application"""
        # Test software development (20% premium)
        software_risk = self.scoring_service._calculate_ai_job_risk(self.test_assessment_data)
        self.assertEqual(software_risk.field_multiplier, 1.2)
        
        # Test marketing (5% discount)
        marketing_data = self.test_assessment_data.copy()
        marketing_data['field'] = 'Marketing'
        marketing_risk = self.scoring_service._calculate_ai_job_risk(marketing_data)
        self.assertEqual(marketing_risk.field_multiplier, 0.95)
        
        # Test sales (10% discount)
        sales_data = self.test_assessment_data.copy()
        sales_data['field'] = 'Sales'
        sales_risk = self.scoring_service._calculate_ai_job_risk(sales_data)
        self.assertEqual(sales_risk.field_multiplier, 0.9)
    
    def test_risk_level_classification(self):
        """Test risk level classification"""
        # Test low risk
        low_risk_data = self.test_assessment_data.copy()
        low_risk_data['current_salary'] = 150000
        low_risk_data['experience_level'] = 'Senior'
        low_risk_data['skills'] = ['ai', 'machine_learning', 'strategy']
        low_risk = self.scoring_service._calculate_ai_job_risk(low_risk_data)
        self.assertEqual(low_risk.final_risk_level, RiskLevel.LOW)
        
        # Test medium risk
        medium_risk_data = self.test_assessment_data.copy()
        medium_risk = self.scoring_service._calculate_ai_job_risk(medium_risk_data)
        self.assertEqual(medium_risk.final_risk_level, RiskLevel.MEDIUM)
        
        # Test high risk
        high_risk_data = self.test_assessment_data.copy()
        high_risk_data['current_salary'] = 30000
        high_risk_data['experience_level'] = 'Entry'
        high_risk_data['skills'] = ['excel']
        high_risk = self.scoring_service._calculate_ai_job_risk(high_risk_data)
        self.assertIn(high_risk.final_risk_level, [RiskLevel.HIGH, RiskLevel.CRITICAL])
    
    def test_confidence_interval_calculation(self):
        """Test confidence interval calculation"""
        job_risk = self.scoring_service._calculate_ai_job_risk(self.test_assessment_data)
        
        self.assertIsInstance(job_risk.confidence_interval, tuple)
        self.assertEqual(len(job_risk.confidence_interval), 2)
        
        lower_bound, upper_bound = job_risk.confidence_interval
        self.assertLess(lower_bound, upper_bound)
        self.assertGreaterEqual(lower_bound, 0)
        self.assertLessEqual(upper_bound, 1)
        
        # Overall score should be within confidence interval
        self.assertGreaterEqual(job_risk.overall_score, lower_bound)
        self.assertLessEqual(job_risk.overall_score, upper_bound)
    
    def test_recommendations_generation(self):
        """Test recommendations generation"""
        job_risk = self.scoring_service._calculate_ai_job_risk(self.test_assessment_data)
        
        self.assertIsInstance(job_risk.recommendations, list)
        self.assertGreater(len(job_risk.recommendations), 0)
        
        # Check recommendation structure
        for rec in job_risk.recommendations:
            self.assertIsInstance(rec, str)
            self.assertGreater(len(rec), 0)
    
    def test_risk_factors_identification(self):
        """Test risk factors identification"""
        job_risk = self.scoring_service._calculate_ai_job_risk(self.test_assessment_data)
        
        self.assertIsInstance(job_risk.risk_factors, list)
        
        # Check risk factors structure
        for factor in job_risk.risk_factors:
            self.assertIsInstance(factor, str)
            self.assertGreater(len(factor), 0)
    
    def test_edge_case_empty_data(self):
        """Test edge case with empty assessment data"""
        empty_data = {}
        job_risk = self.scoring_service._calculate_ai_job_risk(empty_data)
        
        # Should handle gracefully and return a valid result
        self.assertIsInstance(job_risk, JobRiskScore)
        self.assertIsInstance(job_risk.final_risk_level, RiskLevel)
        self.assertGreaterEqual(job_risk.confidence_interval[0], 0)
        self.assertLessEqual(job_risk.confidence_interval[1], 1)
    
    def test_edge_case_missing_fields(self):
        """Test edge case with missing fields"""
        incomplete_data = {
            'current_salary': 75000,
            'field': 'Software Development'
            # Missing other fields
        }
        job_risk = self.scoring_service._calculate_ai_job_risk(incomplete_data)
        
        # Should handle gracefully
        self.assertIsInstance(job_risk, JobRiskScore)
        self.assertIsInstance(job_risk.final_risk_level, RiskLevel)
    
    def test_edge_case_extreme_values(self):
        """Test edge case with extreme values"""
        extreme_data = self.test_assessment_data.copy()
        extreme_data['current_salary'] = 1000000  # Very high salary
        extreme_data['experience_level'] = 'Senior'
        extreme_data['skills'] = ['ai', 'machine_learning', 'deep_learning', 'neural_networks']
        
        job_risk = self.scoring_service._calculate_ai_job_risk(extreme_data)
        
        # Should handle extreme values gracefully
        self.assertIsInstance(job_risk, JobRiskScore)
        self.assertGreaterEqual(job_risk.confidence_interval[0], 0)
        self.assertLessEqual(job_risk.confidence_interval[1], 1)
    
    def test_performance_under_load(self):
        """Test performance under load"""
        import time
        
        start_time = time.time()
        
        # Calculate risk for multiple assessments
        for i in range(100):
            test_data = self.test_assessment_data.copy()
            test_data['current_salary'] = 50000 + (i * 1000)
            job_risk = self.scoring_service._calculate_ai_job_risk(test_data)
            self.assertIsInstance(job_risk, JobRiskScore)
        
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
            test_data = self.test_assessment_data.copy()
            test_data['current_salary'] = 50000 + (i * 100)
            job_risk = self.scoring_service._calculate_ai_job_risk(test_data)
        
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
                test_data = self.test_assessment_data.copy()
                test_data['current_salary'] = 50000 + (thread_id * 1000) + i
                job_risk = self.scoring_service._calculate_ai_job_risk(test_data)
                results.put((thread_id, i, job_risk.final_risk_level))
        
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
    
    def test_comprehensive_assessment_flow(self):
        """Test comprehensive assessment calculation"""
        user_id = "test_user_123"
        assessment_data = {
            **self.test_assessment_data,  # Spread the job risk data at the root level
            'relationship_impact': {
                'relationship_status': 'married',
                'partner_income': 60000,
                'shared_finances': True,
                'children': 2,
                'mortgage': 250000
            }
        }
        
        result = self.scoring_service.calculate_comprehensive_assessment(user_id, assessment_data)
        
        self.assertIsInstance(result, AssessmentScoringResult)
        self.assertIsInstance(result.job_risk, JobRiskScore)
        self.assertIsInstance(result.relationship_impact, RelationshipScore)
        self.assertIsInstance(result.primary_concerns, list)
        self.assertIsInstance(result.action_priorities, list)

if __name__ == '__main__':
    unittest.main()
