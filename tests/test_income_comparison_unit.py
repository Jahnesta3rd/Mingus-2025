"""
Unit Tests for Income Comparison Feature
Tests IncomeComparator class methods, calculations, and edge cases
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.data.income_data_manager import IncomeDataManager, DataSource, DataQuality
from backend.ml.models.income_comparator import IncomeComparator, EducationLevel

class TestIncomeComparator(unittest.TestCase):
    """Unit tests for IncomeComparator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.comparator = IncomeComparator()
        
        # Test user profiles
        self.test_users = {
            'young_professional': {
                'income': 65000,
                'age': 28,
                'race': 'african_american',
                'education': 'bachelors',
                'location': 'Atlanta'
            },
            'mid_career': {
                'income': 85000,
                'age': 38,
                'race': 'african_american',
                'education': 'masters',
                'location': 'Washington DC'
            },
            'entry_level': {
                'income': 45000,
                'age': 25,
                'race': 'african_american',
                'education': 'high_school',
                'location': 'Houston'
            },
            'senior_professional': {
                'income': 120000,
                'age': 42,
                'race': 'african_american',
                'education': 'masters',
                'location': 'New York City'
            }
        }
    
    def test_income_comparator_initialization(self):
        """Test IncomeComparator initialization"""
        self.assertIsNotNone(self.comparator)
        self.assertIsNotNone(self.comparator.demographic_data)
        self.assertIsNotNone(self.comparator.metro_areas)
        self.assertGreater(len(self.comparator.target_metros), 0)
    
    def test_analyze_income_basic(self):
        """Test basic income analysis"""
        user = self.test_users['young_professional']
        
        result = self.comparator.analyze_income(
            user_income=user['income'],
            location=user['location'],
            education_level=EducationLevel.BACHELORS,
            age_group="25-35"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result.user_income, user['income'])
        self.assertGreater(len(result.comparisons), 0)
        self.assertGreaterEqual(result.overall_percentile, 0)
        self.assertLessEqual(result.overall_percentile, 100)
        self.assertIsNotNone(result.motivational_summary)
        self.assertGreater(len(result.action_plan), 0)
    
    def test_compare_national_median(self):
        """Test national median comparison"""
        user_income = 65000
        
        comparison = self.comparator._compare_national_median(user_income)
        
        self.assertIsNotNone(comparison)
        self.assertEqual(comparison.user_income, user_income)
        self.assertGreater(comparison.median_income, 0)
        self.assertGreaterEqual(comparison.percentile_rank, 0)
        self.assertLessEqual(comparison.percentile_rank, 100)
        self.assertIsNotNone(comparison.context_message)
        self.assertIsNotNone(comparison.motivational_insight)
    
    def test_compare_african_american(self):
        """Test African American comparison"""
        user_income = 65000
        
        comparison = self.comparator._compare_african_american(user_income)
        
        self.assertIsNotNone(comparison)
        self.assertEqual(comparison.user_income, user_income)
        self.assertGreater(comparison.median_income, 0)
        self.assertGreaterEqual(comparison.percentile_rank, 0)
        self.assertLessEqual(comparison.percentile_rank, 100)
        self.assertIsNotNone(comparison.context_message)
        self.assertIsNotNone(comparison.motivational_insight)
    
    def test_compare_age_group(self):
        """Test age group comparison"""
        user_income = 65000
        age_group = "25-35"
        
        comparison = self.comparator._compare_age_group(user_income, age_group)
        
        self.assertIsNotNone(comparison)
        self.assertEqual(comparison.user_income, user_income)
        self.assertGreater(comparison.median_income, 0)
        self.assertGreaterEqual(comparison.percentile_rank, 0)
        self.assertLessEqual(comparison.percentile_rank, 100)
    
    def test_compare_education_level(self):
        """Test education level comparison"""
        user_income = 65000
        education_level = EducationLevel.BACHELORS
        
        comparison = self.comparator._compare_education_level(user_income, education_level)
        
        self.assertIsNotNone(comparison)
        self.assertEqual(comparison.user_income, user_income)
        self.assertGreater(comparison.median_income, 0)
        self.assertGreaterEqual(comparison.percentile_rank, 0)
        self.assertLessEqual(comparison.percentile_rank, 100)
    
    def test_compare_location(self):
        """Test location comparison"""
        user_income = 65000
        location = "Atlanta"
        
        comparisons = self.comparator._compare_location(user_income, location)
        
        self.assertIsNotNone(comparisons)
        self.assertGreater(len(comparisons), 0)
        
        for comparison in comparisons:
            self.assertEqual(comparison.user_income, user_income)
            self.assertGreater(comparison.median_income, 0)
            self.assertGreaterEqual(comparison.percentile_rank, 0)
            self.assertLessEqual(comparison.percentile_rank, 100)
    
    def test_calculate_percentile(self):
        """Test percentile calculation"""
        user_income = 65000
        data = self.comparator.demographic_data['national_median']
        
        percentile = self.comparator._calculate_percentile(user_income, data)
        
        self.assertGreaterEqual(percentile, 0)
        self.assertLessEqual(percentile, 100)
        
        # Test with different income levels
        test_cases = [
            (30000, 0, 30),   # Low income
            (45000, 20, 40),  # Below median
            (74580, 45, 55),  # At median
            (100000, 60, 80), # Above median
            (150000, 80, 100) # High income
        ]
        
        for income, min_percentile, max_percentile in test_cases:
            percentile = self.comparator._calculate_percentile(income, data)
            self.assertGreaterEqual(percentile, min_percentile)
            self.assertLessEqual(percentile, max_percentile)
    
    def test_edge_case_very_high_income(self):
        """Test edge case with very high income"""
        high_income = 250000
        
        result = self.comparator.analyze_income(
            user_income=high_income,
            location="New York City",
            education_level=EducationLevel.MASTERS,
            age_group="25-35"
        )
        
        # Should handle very high income gracefully
        self.assertIsNotNone(result)
        self.assertEqual(result.user_income, high_income)
        
        # Percentile should be very high
        self.assertGreater(result.overall_percentile, 90)
    
    def test_edge_case_very_low_income(self):
        """Test edge case with very low income"""
        low_income = 25000
        
        result = self.comparator.analyze_income(
            user_income=low_income,
            location="Houston",
            education_level=EducationLevel.HIGH_SCHOOL,
            age_group="25-35"
        )
        
        # Should handle very low income gracefully
        self.assertIsNotNone(result)
        self.assertEqual(result.user_income, low_income)
        
        # Percentile should be very low
        self.assertLess(result.overall_percentile, 30)
    
    def test_missing_location_data(self):
        """Test handling of missing location data"""
        user_income = 65000
        invalid_location = "invalid_location"
        
        # Should handle gracefully
        comparisons = self.comparator._compare_location(user_income, invalid_location)
        
        # Should return empty list or handle gracefully
        self.assertIsInstance(comparisons, list)
    
    def test_motivational_messaging_quality(self):
        """Test quality of motivational messaging"""
        user_income = 65000
        
        result = self.comparator.analyze_income(
            user_income=user_income,
            location="Atlanta",
            education_level=EducationLevel.BACHELORS,
            age_group="25-35"
        )
        
        # Summary should be encouraging
        summary = result.motivational_summary
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 50)
        
        # Should not be discouraging
        discouraging_words = ['failure', 'hopeless', 'impossible', 'never', 'can\'t']
        for word in discouraging_words:
            self.assertNotIn(word, summary.lower())
        
        # Should be encouraging
        encouraging_words = ['opportunity', 'potential', 'growth', 'advancement', 'improvement']
        has_encouraging_content = any(word in summary.lower() for word in encouraging_words)
        self.assertTrue(has_encouraging_content)
    
    def test_action_plan_quality(self):
        """Test quality of action plan"""
        user_income = 65000
        
        result = self.comparator.analyze_income(
            user_income=user_income,
            location="Atlanta",
            education_level=EducationLevel.BACHELORS,
            age_group="25-35"
        )
        
        # Action plan should be actionable
        action_plan = result.action_plan
        self.assertIsInstance(action_plan, list)
        self.assertGreater(len(action_plan), 0)
        
        for action in action_plan:
            self.assertIsInstance(action, str)
            self.assertGreater(len(action), 10)
    
    def test_available_locations(self):
        """Test available locations"""
        locations = self.comparator.get_available_locations()
        
        self.assertIsInstance(locations, list)
        self.assertGreater(len(locations), 0)
        
        # Should include target metros
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

class TestIncomeDataManager(unittest.TestCase):
    """Unit tests for IncomeDataManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_manager = IncomeDataManager()
    
    def test_data_manager_initialization(self):
        """Test IncomeDataManager initialization"""
        self.assertIsNotNone(self.data_manager)
        self.assertIsNotNone(self.data_manager.fallback_data)
        self.assertIn('metadata', self.data_manager.fallback_data)
        self.assertIn('national_data', self.data_manager.fallback_data)
        self.assertIn('metro_areas', self.data_manager.fallback_data)
    
    def test_get_income_data_fallback(self):
        """Test fallback data retrieval"""
        # Test national data
        data = self.data_manager.get_income_data('african_american')
        self.assertIsNotNone(data)
        self.assertGreater(data.median_income, 0)
        self.assertEqual(data.source, DataSource.FALLBACK)
        
        # Test metro area data
        data = self.data_manager.get_income_data('african_american', location='Atlanta')
        self.assertIsNotNone(data)
        self.assertGreater(data.median_income, 0)
        
        # Test age group data
        data = self.data_manager.get_income_data('african_american', age_group='25-34')
        self.assertIsNotNone(data)
        self.assertGreater(data.median_income, 0)
        
        # Test education data
        data = self.data_manager.get_income_data('african_american', education_level='bachelors')
        self.assertIsNotNone(data)
        self.assertGreater(data.median_income, 0)
    
    def test_data_quality_validation(self):
        """Test data quality validation"""
        quality_report = self.data_manager.validate_data_quality()
        
        self.assertIsInstance(quality_report, dict)
        self.assertIn('overall_quality', quality_report)
        self.assertIn('issues', quality_report)
        self.assertIn('recommendations', quality_report)
        
        # Quality should be at least fair
        self.assertIn(quality_report['overall_quality'], ['excellent', 'good', 'fair'])
    
    def test_available_locations(self):
        """Test available locations retrieval"""
        locations = self.data_manager.get_available_locations()
        
        self.assertIsInstance(locations, list)
        self.assertGreater(len(locations), 0)
        
        # Should include target metro areas
        target_metros = ['Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City']
        for metro in target_metros:
            self.assertIn(metro, locations)
    
    def test_demographic_summary(self):
        """Test demographic summary"""
        summary = self.data_manager.get_demographic_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('races', summary)
        self.assertIn('age_groups', summary)
        self.assertIn('education_levels', summary)
        self.assertIn('metro_areas', summary)
        self.assertIn('data_year', summary)
        
        # Should have expected demographic groups
        expected_races = ['african_american', 'white', 'hispanic_latino', 'asian']
        for race in expected_races:
            self.assertIn(race, summary['races'])

if __name__ == '__main__':
    unittest.main() 