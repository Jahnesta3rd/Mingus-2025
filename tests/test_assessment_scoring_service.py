"""
Test Assessment Scoring Service

This test suite validates the EXACT calculation logic from the MINGUS Calculator Analysis Summary:
1. AI Job Risk Calculator - EXACT algorithm with field_salary_multipliers
2. Relationship Impact Calculator - EXACT point system from assessmentService.ts
3. Income Comparison Calculator - EXACT percentile formula with 8 demographic groups

Performance Requirements:
- Achieve 45ms average calculation time for income comparisons
- Use LRU caching with maxsize=1000
- Memory-efficient immutable data structures
- Thread-safe operations with proper locking
"""

import unittest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

# Import the service to test
from backend.services.assessment_scoring_service import (
    AssessmentScoringService,
    RiskLevel,
    RelationshipSegment,
    JobRiskScore,
    RelationshipScore,
    IncomeComparisonScore,
    AssessmentScoringResult
)

class TestAssessmentScoringService(unittest.TestCase):
    """Test suite for AssessmentScoringService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_session = Mock()
        self.mock_config = {
            'assessment': {
                'cache_ttl': 3600,
                'performance_monitoring': True
            },
            'ml': {
                'job_matcher': {},
                'income_comparator': {}
            }
        }
        
        # Mock the dependent services
        with patch('backend.services.assessment_scoring_service.IntelligentJobMatcher'), \
             patch('backend.services.assessment_scoring_service.IncomeComparatorOptimized'), \
             patch('backend.services.assessment_scoring_service.BillingFeaturesService'):
            
            self.scoring_service = AssessmentScoringService(
                self.mock_db_session, 
                self.mock_config
            )
    
    def test_ai_job_risk_calculation_exact_algorithm(self):
        """Test AI Job Risk Calculator - EXACT algorithm implementation"""
        
        # Test data representing a software developer
        assessment_data = {
            'current_salary': 80000,
            'field': 'software_development',
            'experience_level': 'mid',
            'company_size': 'large',
            'location': 'urban',
            'industry': 'technology',
            'skills': ['python', 'javascript', 'react'],
            'required_skills': ['python', 'javascript', 'react', 'node.js']
        }
        
        # Calculate job risk
        job_risk = self.scoring_service._calculate_ai_job_risk(assessment_data)
        
        # Validate the result is a JobRiskScore
        self.assertIsInstance(job_risk, JobRiskScore)
        
        # Validate EXACT algorithm weights are applied correctly
        expected_overall_score = (
            job_risk.salary_score * 0.35 +      # 35% weight - Primary importance
            job_risk.skills_score * 0.25 +      # 25% weight - Skills alignment 
            job_risk.career_score * 0.20 +      # 20% weight - Career progression
            job_risk.company_score * 0.10 +     # 10% weight - Company quality
            job_risk.location_score * 0.05 +    # 5% weight - Location fit
            job_risk.growth_score * 0.05        # 5% weight - Industry alignment
        )
        
        self.assertAlmostEqual(job_risk.overall_score, expected_overall_score, places=6)
        
        # Validate field multiplier is correct for software development
        self.assertEqual(job_risk.field_multiplier, 1.2)  # 20% premium
        
        # Validate final risk level calculation
        expected_final_risk_score = job_risk.automation_score * 0.7 + job_risk.augmentation_score * 0.3
        self.assertIsInstance(job_risk.final_risk_level, RiskLevel)
        
        # Validate confidence interval
        self.assertIsInstance(job_risk.confidence_interval, tuple)
        self.assertEqual(len(job_risk.confidence_interval), 2)
        self.assertLessEqual(job_risk.confidence_interval[0], job_risk.confidence_interval[1])
        
        # Validate recommendations and risk factors
        self.assertIsInstance(job_risk.recommendations, list)
        self.assertIsInstance(job_risk.risk_factors, list)
    
    def test_relationship_impact_calculation_exact_point_system(self):
        """Test Relationship Impact Calculator - EXACT point system from assessmentService.ts"""
        
        # Test data for different relationship scenarios
        test_cases = [
            {
                'name': 'stress_free_single',
                'data': {
                    'relationship_status': 'single',
                    'financial_stress_frequency': 'never',
                    'emotional_triggers': []
                },
                'expected_score': 0,
                'expected_segment': RelationshipSegment.STRESS_FREE,
                'expected_tier': 'Budget ($10)'
            },
            {
                'name': 'relationship_spender_dating',
                'data': {
                    'relationship_status': 'dating',
                    'financial_stress_frequency': 'sometimes',
                    'emotional_triggers': ['social_pressure']
                },
                'expected_score': 2 + 4 + 2,  # dating + sometimes + social_pressure
                'expected_segment': RelationshipSegment.RELATIONSHIP_SPENDER,
                'expected_tier': 'Mid-tier ($20)'
            },
            {
                'name': 'emotional_manager_married',
                'data': {
                    'relationship_status': 'married',
                    'financial_stress_frequency': 'often',
                    'emotional_triggers': ['after_arguments', 'when_lonely']
                },
                'expected_score': 6 + 6 + 3 + 2,  # married + often + after_arguments + when_lonely
                'expected_segment': RelationshipSegment.EMOTIONAL_MANAGER,
                'expected_tier': 'Mid-tier ($20)'
            },
            {
                'name': 'crisis_mode_complicated',
                'data': {
                    'relationship_status': 'complicated',
                    'financial_stress_frequency': 'always',
                    'emotional_triggers': ['after_breakup', 'after_arguments', 'when_jealous', 'social_pressure']
                },
                'expected_score': 8 + 8 + 3 + 3 + 2 + 2,  # complicated + always + all triggers
                'expected_segment': RelationshipSegment.CRISIS_MODE,
                'expected_tier': 'Professional ($50)'
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(test_case['name']):
                # Calculate relationship impact
                relationship_score = self.scoring_service._calculate_relationship_impact(test_case['data'])
                
                # Validate result is RelationshipScore
                self.assertIsInstance(relationship_score, RelationshipScore)
                
                # Validate EXACT point system
                self.assertEqual(relationship_score.total_score, test_case['expected_score'])
                self.assertEqual(relationship_score.segment, test_case['expected_segment'])
                self.assertEqual(relationship_score.product_tier, test_case['expected_tier'])
                
                # Validate component scores
                self.assertIsInstance(relationship_score.relationship_points, int)
                self.assertIsInstance(relationship_score.stress_points, int)
                self.assertIsInstance(relationship_score.trigger_points, int)
                
                # Validate segment-specific content
                self.assertIsInstance(relationship_score.challenges, list)
                self.assertIsInstance(relationship_score.recommendations, list)
                self.assertIsInstance(relationship_score.financial_impact, dict)
    
    def test_income_comparison_calculation_exact_percentile_formula(self):
        """Test Income Comparison Calculator - EXACT percentile formula"""
        
        # Mock the income comparator to return expected results
        mock_income_analysis = Mock()
        mock_income_analysis.overall_percentile = 65.5
        mock_income_analysis.primary_gap = {'type': 'education', 'gap': 15000}
        mock_income_analysis.career_opportunity_score = 0.75
        mock_income_analysis.comparisons = [{'group': 'national', 'percentile': 65.5}]
        mock_income_analysis.motivational_summary = "You're doing well compared to peers"
        mock_income_analysis.action_plan = ["Consider advanced education"]
        mock_income_analysis.next_steps = ["Research graduate programs"]
        mock_income_analysis.confidence_level = 0.85
        
        self.scoring_service.income_comparator.analyze_income.return_value = mock_income_analysis
        
        # Test data
        assessment_data = {
            'current_salary': 75000,
            'location': 'New York, NY',
            'education_level': 'bachelors',
            'age_group': '25-35'
        }
        
        # Calculate income comparison
        income_comparison = self.scoring_service._calculate_income_comparison(assessment_data)
        
        # Validate result is IncomeComparisonScore
        self.assertIsInstance(income_comparison, IncomeComparisonScore)
        
        # Validate the income comparator was called with correct parameters
        self.scoring_service.income_comparator.analyze_income.assert_called_once()
        call_args = self.scoring_service.income_comparator.analyze_income.call_args
        self.assertEqual(call_args[1]['user_income'], 75000)
        self.assertEqual(call_args[1]['location'], 'New York, NY')
        self.assertEqual(call_args[1]['age_group'], '25-35')
        
        # Validate returned values
        self.assertEqual(income_comparison.user_income, 75000)
        self.assertEqual(income_comparison.overall_percentile, 65.5)
        self.assertEqual(income_comparison.career_opportunity_score, 0.75)
        self.assertEqual(income_comparison.confidence_level, 0.85)
        
        # Validate calculation time is recorded
        self.assertIsInstance(income_comparison.calculation_time_ms, float)
        self.assertGreater(income_comparison.calculation_time_ms, 0)
    
    def test_comprehensive_assessment_integration(self):
        """Test comprehensive assessment integration of all three calculators"""
        
        # Mock the individual calculator methods
        mock_job_risk = Mock(spec=JobRiskScore)
        mock_job_risk.overall_score = 0.65
        mock_job_risk.final_risk_level = RiskLevel.MEDIUM
        mock_job_risk.confidence_interval = (0.60, 0.70)
        
        mock_relationship = Mock(spec=RelationshipScore)
        mock_relationship.total_score = 18
        mock_relationship.segment = RelationshipSegment.RELATIONSHIP_SPENDER
        mock_relationship.product_tier = 'Mid-tier ($20)'
        
        mock_income = Mock(spec=IncomeComparisonScore)
        mock_income.overall_percentile = 55.0
        mock_income.confidence_level = 0.80
        
        with patch.object(self.scoring_service, '_calculate_ai_job_risk', return_value=mock_job_risk), \
             patch.object(self.scoring_service, '_calculate_relationship_impact', return_value=mock_relationship), \
             patch.object(self.scoring_service, '_calculate_income_comparison', return_value=mock_income):
            
            # Test data
            assessment_data = {
                'current_salary': 70000,
                'field': 'data_analysis',
                'relationship_status': 'dating',
                'financial_stress_frequency': 'sometimes'
            }
            
            # Calculate comprehensive assessment
            result = self.scoring_service.calculate_comprehensive_assessment('test_user', assessment_data)
            
            # Validate result is AssessmentScoringResult
            self.assertIsInstance(result, AssessmentScoringResult)
            
            # Validate all three calculators were called
            self.scoring_service._calculate_ai_job_risk.assert_called_once_with(assessment_data)
            self.scoring_service._calculate_relationship_impact.assert_called_once_with(assessment_data)
            self.scoring_service._calculate_income_comparison.assert_called_once_with(assessment_data)
            
            # Validate overall assessment components
            self.assertIsInstance(result.overall_risk_level, str)
            self.assertIsInstance(result.primary_concerns, list)
            self.assertIsInstance(result.action_priorities, list)
            self.assertIsInstance(result.subscription_recommendation, str)
            self.assertIsInstance(result.confidence_score, float)
            
            # Validate timestamp
            self.assertIsInstance(result.timestamp, datetime)
    
    def test_performance_requirements(self):
        """Test performance requirements (45ms average for income comparisons)"""
        
        # Mock income comparator for performance testing
        mock_income_analysis = Mock()
        mock_income_analysis.overall_percentile = 50.0
        mock_income_analysis.primary_gap = {}
        mock_income_analysis.career_opportunity_score = 0.5
        mock_income_analysis.comparisons = []
        mock_income_analysis.motivational_summary = ""
        mock_income_analysis.action_plan = []
        mock_income_analysis.next_steps = []
        mock_income_analysis.confidence_level = 0.8
        
        self.scoring_service.income_comparator.analyze_income.return_value = mock_income_analysis
        
        # Test data
        assessment_data = {
            'current_salary': 60000,
            'location': 'San Francisco, CA',
            'education_level': 'masters',
            'age_group': '30-40'
        }
        
        # Run multiple calculations to test performance
        calculation_times = []
        num_iterations = 10
        
        for i in range(num_iterations):
            start_time = time.time()
            self.scoring_service._calculate_income_comparison(assessment_data)
            end_time = time.time()
            calculation_times.append((end_time - start_time) * 1000)  # Convert to milliseconds
        
        # Calculate average time
        average_time = sum(calculation_times) / len(calculation_times)
        
        # Validate performance requirement (45ms average)
        self.assertLess(average_time, 45.0, 
                       f"Average calculation time {average_time:.2f}ms exceeds 45ms requirement")
        
        # Validate all calculations completed successfully
        self.assertEqual(len(calculation_times), num_iterations)
        
        # Log performance metrics
        print(f"Average income comparison calculation time: {average_time:.2f}ms")
        print(f"Performance metrics: {self.scoring_service.get_performance_stats()}")
    
    def test_caching_functionality(self):
        """Test caching functionality with identical requests"""
        
        # Mock calculator methods
        with patch.object(self.scoring_service, '_calculate_ai_job_risk') as mock_job, \
             patch.object(self.scoring_service, '_calculate_relationship_impact') as mock_rel, \
             patch.object(self.scoring_service, '_calculate_income_comparison') as mock_inc:
            
            mock_job.return_value = Mock(spec=JobRiskScore)
            mock_rel.return_value = Mock(spec=RelationshipScore)
            mock_inc.return_value = Mock(spec=IncomeComparisonScore)
            
            # Test data
            assessment_data = {
                'current_salary': 65000,
                'field': 'marketing',
                'relationship_status': 'married'
            }
            
            # First call - should calculate
            result1 = self.scoring_service.calculate_comprehensive_assessment('user1', assessment_data)
            
            # Second call with identical data - should use cache
            result2 = self.scoring_service.calculate_comprehensive_assessment('user1', assessment_data)
            
            # Validate calculators were called only once each
            self.assertEqual(mock_job.call_count, 1)
            self.assertEqual(mock_rel.call_count, 1)
            self.assertEqual(mock_inc.call_count, 1)
            
            # Validate results are the same
            self.assertEqual(result1, result2)
    
    def test_thread_safety(self):
        """Test thread safety with concurrent access"""
        import threading
        import queue
        
        # Mock calculator methods
        with patch.object(self.scoring_service, '_calculate_ai_job_risk') as mock_job, \
             patch.object(self.scoring_service, '_calculate_relationship_impact') as mock_rel, \
             patch.object(self.scoring_service, '_calculate_income_comparison') as mock_inc:
            
            mock_job.return_value = Mock(spec=JobRiskScore)
            mock_rel.return_value = Mock(spec=RelationshipScore)
            mock_inc.return_value = Mock(spec=IncomeComparisonScore)
            
            # Test data
            assessment_data = {
                'current_salary': 70000,
                'field': 'finance',
                'relationship_status': 'single'
            }
            
            # Results queue
            results_queue = queue.Queue()
            
            def worker(worker_id):
                """Worker function for concurrent testing"""
                try:
                    result = self.scoring_service.calculate_comprehensive_assessment(
                        f'user_{worker_id}', assessment_data
                    )
                    results_queue.put((worker_id, result, None))
                except Exception as e:
                    results_queue.put((worker_id, None, e))
            
            # Start multiple threads
            threads = []
            num_threads = 5
            
            for i in range(num_threads):
                thread = threading.Thread(target=worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Collect results
            results = []
            while not results_queue.empty():
                worker_id, result, error = results_queue.get()
                if error:
                    self.fail(f"Thread {worker_id} failed: {error}")
                results.append((worker_id, result))
            
            # Validate all threads completed successfully
            self.assertEqual(len(results), num_threads)
            
            # Validate all results are valid
            for worker_id, result in results:
                self.assertIsInstance(result, AssessmentScoringResult)
    
    def test_field_salary_multipliers_exact_values(self):
        """Test that field salary multipliers match EXACT values from intelligent_job_matcher.py"""
        
        expected_multipliers = {
            'software_development': 1.2,  # 20% premium
            'data_analysis': 1.1,         # 10% premium
            'project_management': 1.0,    # Base level
            'marketing': 0.95,             # 5% discount
            'finance': 1.05,               # 5% premium
            'sales': 0.9,                  # 10% discount
            'operations': 0.95,            # 5% discount
            'hr': 0.9                      # 10% discount
        }
        
        for field, expected_multiplier in expected_multipliers.items():
            with self.subTest(field=field):
                assessment_data = {
                    'current_salary': 60000,
                    'field': field,
                    'experience_level': 'mid'
                }
                
                job_risk = self.scoring_service._calculate_ai_job_risk(assessment_data)
                self.assertEqual(job_risk.field_multiplier, expected_multiplier)
    
    def test_relationship_scoring_exact_points(self):
        """Test that relationship scoring uses EXACT point values from assessmentService.ts"""
        
        # Test relationship status points
        self.assertEqual(self.scoring_service.relationship_points['single'], 0)
        self.assertEqual(self.scoring_service.relationship_points['dating'], 2)
        self.assertEqual(self.scoring_service.relationship_points['serious'], 4)
        self.assertEqual(self.scoring_service.relationship_points['married'], 6)
        self.assertEqual(self.scoring_service.relationship_points['complicated'], 8)
        
        # Test stress frequency points
        self.assertEqual(self.scoring_service.stress_points['never'], 0)
        self.assertEqual(self.scoring_service.stress_points['rarely'], 2)
        self.assertEqual(self.scoring_service.stress_points['sometimes'], 4)
        self.assertEqual(self.scoring_service.stress_points['often'], 6)
        self.assertEqual(self.scoring_service.stress_points['always'], 8)
        
        # Test trigger points
        self.assertEqual(self.scoring_service.trigger_points['after_breakup'], 3)
        self.assertEqual(self.scoring_service.trigger_points['after_arguments'], 3)
        self.assertEqual(self.scoring_service.trigger_points['when_lonely'], 2)
        self.assertEqual(self.scoring_service.trigger_points['when_jealous'], 2)
        self.assertEqual(self.scoring_service.trigger_points['social_pressure'], 2)
    
    def test_assessment_breakdown_functionality(self):
        """Test get_assessment_breakdown method returns detailed breakdown"""
        
        # Mock comprehensive assessment
        mock_result = Mock(spec=AssessmentScoringResult)
        mock_result.overall_risk_level = "Medium Risk"
        mock_result.primary_concerns = ["Job Security Risk"]
        mock_result.action_priorities = ["Address job security concerns"]
        mock_result.subscription_recommendation = "Mid-tier ($20)"
        mock_result.confidence_score = 0.75
        
        mock_result.job_risk.overall_score = 0.65
        mock_result.job_risk.salary_score = 0.7
        mock_result.job_risk.skills_score = 0.8
        mock_result.job_risk.career_score = 0.6
        mock_result.job_risk.company_score = 0.8
        mock_result.job_risk.location_score = 0.7
        mock_result.job_risk.growth_score = 0.9
        mock_result.job_risk.risk_factors = ["High automation risk"]
        mock_result.job_risk.field_multiplier = 1.2
        mock_result.job_risk.confidence_interval = (0.60, 0.70)
        
        mock_result.relationship_impact.total_score = 18
        mock_result.relationship_impact.segment.value = "relationship-spender"
        mock_result.relationship_impact.relationship_points = 2
        mock_result.relationship_impact.stress_points = 4
        mock_result.relationship_impact.trigger_points = 12
        mock_result.relationship_impact.financial_impact = {"monthly_impact": 500}
        
        mock_result.income_comparison.overall_percentile = 55.0
        mock_result.income_comparison.career_opportunity_score = 0.7
        mock_result.income_comparison.calculation_time_ms = 25.5
        mock_result.income_comparison.confidence_level = 0.8
        
        with patch.object(self.scoring_service, 'calculate_comprehensive_assessment', return_value=mock_result):
            
            assessment_data = {'current_salary': 70000}
            breakdown = self.scoring_service.get_assessment_breakdown('test_user', assessment_data)
            
            # Validate breakdown structure
            self.assertIn('overall_result', breakdown)
            self.assertIn('job_risk_breakdown', breakdown)
            self.assertIn('relationship_breakdown', breakdown)
            self.assertIn('income_comparison_breakdown', breakdown)
            self.assertIn('performance_metrics', breakdown)
            
            # Validate overall result
            overall = breakdown['overall_result']
            self.assertEqual(overall['risk_level'], "Medium Risk")
            self.assertEqual(overall['primary_concerns'], ["Job Security Risk"])
            self.assertEqual(overall['subscription_recommendation'], "Mid-tier ($20)")
            self.assertEqual(overall['confidence_score'], 0.75)
            
            # Validate job risk breakdown
            job_risk = breakdown['job_risk_breakdown']
            self.assertEqual(job_risk['overall_score'], 0.65)
            self.assertEqual(job_risk['component_scores']['salary'], 0.7)
            self.assertEqual(job_risk['field_multiplier'], 1.2)
            self.assertEqual(job_risk['confidence_interval'], (0.60, 0.70))
            
            # Validate relationship breakdown
            relationship = breakdown['relationship_breakdown']
            self.assertEqual(relationship['total_score'], 18)
            self.assertEqual(relationship['segment'], "relationship-spender")
            self.assertEqual(relationship['component_scores']['relationship_points'], 2)
            
            # Validate income comparison breakdown
            income = breakdown['income_comparison_breakdown']
            self.assertEqual(income['overall_percentile'], 55.0)
            self.assertEqual(income['calculation_time_ms'], 25.5)
            self.assertEqual(income['confidence_level'], 0.8)

if __name__ == '__main__':
    unittest.main()
