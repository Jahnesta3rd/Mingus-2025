"""
Comprehensive tests for IncomeComparator class
Tests demographic income analysis functionality
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml.models.income_comparator import (
    IncomeComparator, 
    IncomeComparison, 
    ComparisonGroup, 
    EducationLevel,
    IncomeAnalysisResult,
    DemographicIncomeData
)

class TestIncomeComparator(unittest.TestCase):
    """Test cases for IncomeComparator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.comparator = IncomeComparator()
        self.test_income = 65000
        self.test_location = "Atlanta"
        self.test_education = EducationLevel.BACHELORS
    
    def test_initialization(self):
        """Test IncomeComparator initialization"""
        self.assertIsNotNone(self.comparator.demographic_data)
        self.assertIsNotNone(self.comparator.metro_areas)
        self.assertIn(ComparisonGroup.NATIONAL_MEDIAN, self.comparator.demographic_data)
        self.assertIn(ComparisonGroup.AFRICAN_AMERICAN, self.comparator.demographic_data)
        self.assertIn('Atlanta', self.comparator.metro_areas)
    
    def test_analyze_income_basic(self):
        """Test basic income analysis without location/education"""
        result = self.comparator.analyze_income(self.test_income)
        
        self.assertIsInstance(result, IncomeAnalysisResult)
        self.assertEqual(result.user_income, self.test_income)
        self.assertGreater(len(result.comparisons), 0)
        self.assertIsInstance(result.overall_percentile, float)
        self.assertIsInstance(result.career_opportunity_score, float)
        self.assertIsInstance(result.motivational_summary, str)
        self.assertIsInstance(result.action_plan, list)
        self.assertIsInstance(result.next_steps, list)
    
    def test_analyze_income_complete(self):
        """Test complete income analysis with all parameters"""
        result = self.comparator.analyze_income(
            user_income=self.test_income,
            location=self.test_location,
            education_level=self.test_education
        )
        
        self.assertIsInstance(result, IncomeAnalysisResult)
        self.assertEqual(result.user_income, self.test_income)
        
        # Should have more comparisons with location and education
        self.assertGreater(len(result.comparisons), 4)
        
        # Check that we have location-based comparisons
        location_comparisons = [c for c in result.comparisons 
                              if c.comparison_group in [ComparisonGroup.METRO_AREA, ComparisonGroup.AFRICAN_AMERICAN_METRO]]
        self.assertGreater(len(location_comparisons), 0)
    
    def test_national_median_comparison(self):
        """Test national median comparison"""
        comparison = self.comparator._compare_national_median(self.test_income)
        
        self.assertIsInstance(comparison, IncomeComparison)
        self.assertEqual(comparison.comparison_group, ComparisonGroup.NATIONAL_MEDIAN)
        self.assertEqual(comparison.user_income, self.test_income)
        self.assertEqual(comparison.median_income, 74580)  # 2022 ACS data
        self.assertIsInstance(comparison.percentile_rank, float)
        self.assertIsInstance(comparison.income_gap, int)
        self.assertIsInstance(comparison.gap_percentage, float)
        self.assertIsInstance(comparison.motivational_insight, str)
        self.assertIsInstance(comparison.action_item, str)
    
    def test_african_american_comparison(self):
        """Test African American comparison"""
        comparison = self.comparator._compare_african_american(self.test_income)
        
        self.assertIsInstance(comparison, IncomeComparison)
        self.assertEqual(comparison.comparison_group, ComparisonGroup.AFRICAN_AMERICAN)
        self.assertEqual(comparison.user_income, self.test_income)
        self.assertEqual(comparison.median_income, 52000)  # 2022 ACS data
        self.assertIsInstance(comparison.percentile_rank, float)
        self.assertIsInstance(comparison.income_gap, int)
        self.assertIsInstance(comparison.gap_percentage, float)
    
    def test_age_group_comparison(self):
        """Test age group comparison"""
        comparison = self.comparator._compare_age_group(self.test_income, "25-35")
        
        self.assertIsInstance(comparison, IncomeComparison)
        self.assertEqual(comparison.comparison_group, ComparisonGroup.AGE_25_35)
        self.assertEqual(comparison.user_income, self.test_income)
        self.assertEqual(comparison.median_income, 58000)  # 2022 ACS data
        self.assertIsInstance(comparison.percentile_rank, float)
    
    def test_african_american_age_group_comparison(self):
        """Test African American age group comparison"""
        comparison = self.comparator._compare_african_american_age_group(self.test_income, "25-35")
        
        self.assertIsInstance(comparison, IncomeComparison)
        self.assertEqual(comparison.comparison_group, ComparisonGroup.AFRICAN_AMERICAN_25_35)
        self.assertEqual(comparison.user_income, self.test_income)
        self.assertEqual(comparison.median_income, 48000)  # 2022 ACS data
        self.assertIsInstance(comparison.percentile_rank, float)
    
    def test_education_comparison(self):
        """Test education level comparison"""
        comparison = self.comparator._compare_education_level(self.test_income, EducationLevel.BACHELORS)
        
        self.assertIsInstance(comparison, IncomeComparison)
        self.assertEqual(comparison.comparison_group, ComparisonGroup.COLLEGE_GRADUATE)
        self.assertEqual(comparison.user_income, self.test_income)
        self.assertEqual(comparison.median_income, 85000)  # 2022 ACS data
        self.assertIsInstance(comparison.percentile_rank, float)
    
    def test_african_american_education_comparison(self):
        """Test African American education comparison"""
        comparison = self.comparator._compare_african_american_education(self.test_income, EducationLevel.BACHELORS)
        
        self.assertIsInstance(comparison, IncomeComparison)
        self.assertEqual(comparison.comparison_group, ComparisonGroup.AFRICAN_AMERICAN_COLLEGE)
        self.assertEqual(comparison.user_income, self.test_income)
        self.assertEqual(comparison.median_income, 65000)  # 2022 ACS data
        self.assertIsInstance(comparison.percentile_rank, float)
    
    def test_location_comparison(self):
        """Test location-based comparison"""
        comparisons = self.comparator._compare_location(self.test_income, "Atlanta")
        
        self.assertIsInstance(comparisons, list)
        self.assertGreater(len(comparisons), 0)
        
        for comparison in comparisons:
            self.assertIsInstance(comparison, IncomeComparison)
            self.assertIn(comparison.comparison_group, [ComparisonGroup.METRO_AREA, ComparisonGroup.AFRICAN_AMERICAN_METRO])
            self.assertEqual(comparison.user_income, self.test_income)
            self.assertIsInstance(comparison.percentile_rank, float)
    
    def test_percentile_calculation(self):
        """Test percentile calculation"""
        data = DemographicIncomeData(
            group_name="Test Group",
            median_income=60000,
            mean_income=70000,
            percentile_25=40000,
            percentile_75=80000,
            sample_size=1000,
            year=2022,
            source="Test"
        )
        
        # Test various income levels
        test_cases = [
            (30000, 0.1),  # Very low income
            (60000, 50.0),  # Median income
            (80000, 75.0),  # 75th percentile
            (100000, 99.9)  # Very high income
        ]
        
        for income, expected_percentile in test_cases:
            percentile = self.comparator._calculate_percentile(income, data)
            self.assertIsInstance(percentile, float)
            self.assertGreaterEqual(percentile, 0.1)
            self.assertLessEqual(percentile, 99.9)
    
    def test_overall_percentile_calculation(self):
        """Test overall percentile calculation"""
        comparisons = [
            IncomeComparison(
                comparison_group=ComparisonGroup.NATIONAL_MEDIAN,
                group_name="Test",
                user_income=60000,
                median_income=60000,
                percentile_rank=50.0,
                income_gap=0,
                gap_percentage=0.0,
                context_message="Test",
                motivational_insight="Test",
                action_item="Test",
                data_source="Test",
                confidence_level=0.9
            )
        ]
        
        overall_percentile = self.comparator._calculate_overall_percentile(comparisons)
        self.assertIsInstance(overall_percentile, float)
        self.assertGreaterEqual(overall_percentile, 0.0)
        self.assertLessEqual(overall_percentile, 100.0)
    
    def test_career_opportunity_score(self):
        """Test career opportunity score calculation"""
        # Test with positive gaps (opportunities)
        positive_comparisons = [
            IncomeComparison(
                comparison_group=ComparisonGroup.NATIONAL_MEDIAN,
                group_name="Test",
                user_income=50000,
                median_income=60000,
                percentile_rank=30.0,
                income_gap=10000,
                gap_percentage=16.7,
                context_message="Test",
                motivational_insight="Test",
                action_item="Test",
                data_source="Test",
                confidence_level=0.9
            )
        ]
        
        score = self.comparator._calculate_career_opportunity_score(positive_comparisons)
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 100.0)
        
        # Test with no gaps (limited opportunity)
        no_gap_comparisons = [
            IncomeComparison(
                comparison_group=ComparisonGroup.NATIONAL_MEDIAN,
                group_name="Test",
                user_income=70000,
                median_income=60000,
                percentile_rank=70.0,
                income_gap=-10000,
                gap_percentage=-16.7,
                context_message="Test",
                motivational_insight="Test",
                action_item="Test",
                data_source="Test",
                confidence_level=0.9
            )
        ]
        
        score = self.comparator._calculate_career_opportunity_score(no_gap_comparisons)
        self.assertIsInstance(score, float)
        self.assertLessEqual(score, 50.0)
    
    def test_insight_generation(self):
        """Test motivational insight generation"""
        # Test when user income is above benchmark
        insight = self.comparator._generate_insight(70000, 60000, "test benchmark")
        self.assertIn("more than", insight)
        self.assertIn("strong career positioning", insight)
        
        # Test when user income is below benchmark
        insight = self.comparator._generate_insight(50000, 60000, "test benchmark")
        self.assertIn("opportunity gap", insight)
        self.assertIn("career advancement potential", insight)
    
    def test_action_item_generation(self):
        """Test action item generation"""
        # Test large gap
        action = self.comparator._generate_action_item(25000, "test benchmark", 60000)
        self.assertIn("Target roles", action)
        self.assertIn("$25,000", action)
        
        # Test small gap
        action = self.comparator._generate_action_item(5000, "test benchmark", 60000)
        self.assertIn("Small adjustments", action)
        self.assertIn("$5,000", action)
        
        # Test no gap (negative gap)
        action = self.comparator._generate_action_item(-10000, "test benchmark", 60000)
        self.assertIn("Leverage your strong position", action)
    
    def test_location_normalization(self):
        """Test location name normalization"""
        test_cases = [
            ("atlanta", "Atlanta"),
            ("ATLANTA", "Atlanta"),
            ("Washington DC", "Washington DC"),
            ("washington d.c.", "Washington DC"),
            ("dc", "Washington DC"),
            ("nyc", "New York City"),
            ("new york", "New York City"),
            ("philly", "Philadelphia"),
            ("unknown location", "unknown location")
        ]
        
        for input_location, expected in test_cases:
            normalized = self.comparator._normalize_location(input_location)
            self.assertEqual(normalized, expected)
    
    def test_available_locations(self):
        """Test available locations list"""
        locations = self.comparator.get_available_locations()
        self.assertIsInstance(locations, list)
        self.assertGreater(len(locations), 0)
        
        # Check that target metros are included
        target_metros = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
        for metro in target_metros:
            self.assertIn(metro, locations)
    
    def test_demographic_summary(self):
        """Test demographic summary"""
        summary = self.comparator.get_demographic_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('national_groups', summary)
        self.assertIn('metro_areas', summary)
        self.assertIn('data_year', summary)
        self.assertIn('data_source', summary)
        
        self.assertEqual(summary['data_year'], 2022)
        self.assertEqual(summary['data_source'], 'American Community Survey')
        self.assertIsInstance(summary['national_groups'], list)
        self.assertIsInstance(summary['metro_areas'], list)
    
    def test_error_handling_invalid_income(self):
        """Test error handling for invalid income values"""
        # The comparator handles negative income gracefully with fallback calculations
        result = self.comparator.analyze_income(-1000)  # Negative income
        self.assertIsInstance(result, IncomeAnalysisResult)
        self.assertEqual(result.user_income, -1000)
    
    def test_error_handling_invalid_location(self):
        """Test error handling for invalid location"""
        # Should not raise exception, just return fewer comparisons
        result = self.comparator.analyze_income(65000, location="Invalid Location")
        self.assertIsInstance(result, IncomeAnalysisResult)
        self.assertEqual(result.user_income, 65000)
    
    def test_motivational_summary_generation(self):
        """Test motivational summary generation"""
        # Create mock comparisons with a primary gap
        primary_gap = IncomeComparison(
            comparison_group=ComparisonGroup.NATIONAL_MEDIAN,
            group_name="National Median",
            user_income=50000,
            median_income=60000,
            percentile_rank=30.0,
            income_gap=10000,
            gap_percentage=16.7,
            context_message="Test",
            motivational_insight="Test",
            action_item="Test",
            data_source="Test",
            confidence_level=0.9
        )
        
        comparisons = [primary_gap]
        
        summary = self.comparator._generate_motivational_summary(comparisons, primary_gap)
        self.assertIsInstance(summary, str)
        self.assertIn("opportunity", summary)
        self.assertIn("career advancement", summary)
    
    def test_action_plan_generation(self):
        """Test action plan generation"""
        primary_gap = IncomeComparison(
            comparison_group=ComparisonGroup.NATIONAL_MEDIAN,
            group_name="National Median",
            user_income=50000,
            median_income=60000,
            percentile_rank=30.0,
            income_gap=10000,
            gap_percentage=16.7,
            context_message="Test",
            motivational_insight="Test",
            action_item="Test",
            data_source="Test",
            confidence_level=0.9
        )
        
        comparisons = [primary_gap]
        
        action_plan = self.comparator._generate_action_plan(comparisons, primary_gap)
        self.assertIsInstance(action_plan, list)
        self.assertGreater(len(action_plan), 0)
        
        for action in action_plan:
            self.assertIsInstance(action, str)
            self.assertGreater(len(action), 0)
    
    def test_next_steps_generation(self):
        """Test next steps generation"""
        primary_gap = IncomeComparison(
            comparison_group=ComparisonGroup.NATIONAL_MEDIAN,
            group_name="National Median",
            user_income=50000,
            median_income=60000,
            percentile_rank=30.0,
            income_gap=10000,
            gap_percentage=16.7,
            context_message="Test",
            motivational_insight="Test",
            action_item="Test",
            data_source="Test",
            confidence_level=0.9
        )
        
        # Test high opportunity score
        next_steps = self.comparator._generate_next_steps(primary_gap, 80.0)
        self.assertIsInstance(next_steps, list)
        self.assertGreater(len(next_steps), 0)
        
        # Test low opportunity score
        next_steps = self.comparator._generate_next_steps(primary_gap, 30.0)
        self.assertIsInstance(next_steps, list)
        self.assertGreater(len(next_steps), 0)
    
    def test_comprehensive_analysis_example(self):
        """Test comprehensive analysis with realistic example"""
        # Example: African American professional in Atlanta with bachelor's degree
        result = self.comparator.analyze_income(
            user_income=55000,
            location="Atlanta",
            education_level=EducationLevel.BACHELORS
        )
        
        # Verify all components
        self.assertIsInstance(result, IncomeAnalysisResult)
        self.assertEqual(result.user_income, 55000)
        self.assertGreater(len(result.comparisons), 4)
        self.assertIsInstance(result.overall_percentile, float)
        self.assertIsInstance(result.career_opportunity_score, float)
        self.assertIsInstance(result.motivational_summary, str)
        self.assertIsInstance(result.action_plan, list)
        self.assertIsInstance(result.next_steps, list)
        
        # Verify specific comparisons exist
        comparison_groups = [c.comparison_group for c in result.comparisons]
        self.assertIn(ComparisonGroup.NATIONAL_MEDIAN, comparison_groups)
        self.assertIn(ComparisonGroup.AFRICAN_AMERICAN, comparison_groups)
        self.assertIn(ComparisonGroup.AGE_25_35, comparison_groups)
        self.assertIn(ComparisonGroup.AFRICAN_AMERICAN_25_35, comparison_groups)
        self.assertIn(ComparisonGroup.COLLEGE_GRADUATE, comparison_groups)
        self.assertIn(ComparisonGroup.AFRICAN_AMERICAN_COLLEGE, comparison_groups)
        self.assertIn(ComparisonGroup.METRO_AREA, comparison_groups)
        self.assertIn(ComparisonGroup.AFRICAN_AMERICAN_METRO, comparison_groups)


class TestIncomeComparatorIntegration(unittest.TestCase):
    """Integration tests for IncomeComparator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.comparator = IncomeComparator()
    
    def test_full_pipeline_integration(self):
        """Test full analysis pipeline integration"""
        # Test multiple scenarios
        test_scenarios = [
            {
                'income': 45000,
                'location': 'Houston',
                'education': EducationLevel.BACHELORS,
                'description': 'Entry-level professional'
            },
            {
                'income': 75000,
                'location': 'Washington DC',
                'education': EducationLevel.MASTERS,
                'description': 'Mid-career professional'
            },
            {
                'income': 95000,
                'location': 'New York City',
                'education': EducationLevel.BACHELORS,
                'description': 'Senior professional'
            }
        ]
        
        for scenario in test_scenarios:
            with self.subTest(scenario=scenario['description']):
                result = self.comparator.analyze_income(
                    user_income=scenario['income'],
                    location=scenario['location'],
                    education_level=scenario['education']
                )
                
                # Verify result structure
                self.assertIsInstance(result, IncomeAnalysisResult)
                self.assertEqual(result.user_income, scenario['income'])
                self.assertGreater(len(result.comparisons), 0)
                self.assertIsInstance(result.overall_percentile, float)
                self.assertIsInstance(result.career_opportunity_score, float)
                self.assertIsInstance(result.motivational_summary, str)
                self.assertIsInstance(result.action_plan, list)
                self.assertIsInstance(result.next_steps, list)
                
                # Verify all comparisons have required fields
                for comparison in result.comparisons:
                    self.assertIsInstance(comparison.percentile_rank, float)
                    self.assertIsInstance(comparison.income_gap, int)
                    self.assertIsInstance(comparison.gap_percentage, float)
                    self.assertIsInstance(comparison.motivational_insight, str)
                    self.assertIsInstance(comparison.action_item, str)
                    self.assertGreater(comparison.confidence_level, 0.0)
                    self.assertLessEqual(comparison.confidence_level, 1.0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 