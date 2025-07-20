"""
Realistic Demographic Scenario Tests for Income Comparison
Tests with sample user profiles representing target demographic
"""

import unittest
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.data.income_data_manager import IncomeDataManager
from backend.routes.income_analysis import IncomeComparator

class TestIncomeComparisonScenarios(unittest.TestCase):
    """Realistic demographic scenario tests"""
    
    def setUp(self):
        """Set up test fixtures with realistic user profiles"""
        self.income_manager = IncomeDataManager()
        self.comparator = IncomeComparator(self.income_manager)
        
        # Realistic African American professional profiles
        self.african_american_profiles = {
            'entry_level_graduate': {
                'name': 'Marcus Johnson',
                'income': 48000,
                'age': 24,
                'race': 'african_american',
                'education': 'bachelors',
                'location': 'Atlanta',
                'job_title': 'Marketing Coordinator',
                'years_experience': 1,
                'expected_percentile_range': (20, 40),
                'expected_gap_direction': 'negative'
            },
            'mid_level_professional': {
                'name': 'Aisha Williams',
                'income': 72000,
                'age': 31,
                'race': 'african_american',
                'education': 'bachelors',
                'location': 'Houston',
                'job_title': 'Senior Account Manager',
                'years_experience': 6,
                'expected_percentile_range': (50, 70),
                'expected_gap_direction': 'mixed'
            },
            'experienced_manager': {
                'name': 'David Thompson',
                'income': 95000,
                'age': 38,
                'race': 'african_american',
                'education': 'masters',
                'location': 'Washington DC',
                'job_title': 'Operations Director',
                'years_experience': 12,
                'expected_percentile_range': (70, 85),
                'expected_gap_direction': 'positive'
            },
            'senior_executive': {
                'name': 'Michelle Rodriguez',
                'income': 140000,
                'age': 45,
                'race': 'african_american',
                'education': 'masters',
                'location': 'New York City',
                'job_title': 'VP of Strategy',
                'years_experience': 18,
                'expected_percentile_range': (85, 95),
                'expected_gap_direction': 'positive'
            },
            'career_changer': {
                'name': 'James Wilson',
                'income': 55000,
                'age': 35,
                'race': 'african_american',
                'education': 'bachelors',
                'location': 'Chicago',
                'job_title': 'Software Developer',
                'years_experience': 2,
                'expected_percentile_range': (30, 50),
                'expected_gap_direction': 'negative'
            },
            'entrepreneur': {
                'name': 'Keisha Brown',
                'income': 85000,
                'age': 33,
                'race': 'african_american',
                'education': 'bachelors',
                'location': 'Dallas',
                'job_title': 'Business Owner',
                'years_experience': 8,
                'expected_percentile_range': (60, 80),
                'expected_gap_direction': 'positive'
            }
        }
        
        # Comparison profiles for benchmarking
        self.comparison_profiles = {
            'white_peer_same_role': {
                'name': 'Sarah Anderson',
                'income': 78000,
                'age': 31,
                'race': 'white',
                'education': 'bachelors',
                'location': 'Houston',
                'job_title': 'Senior Account Manager',
                'years_experience': 6
            },
            'hispanic_peer_same_role': {
                'name': 'Carlos Martinez',
                'income': 68000,
                'age': 31,
                'race': 'hispanic_latino',
                'education': 'bachelors',
                'location': 'Houston',
                'job_title': 'Senior Account Manager',
                'years_experience': 6
            },
            'asian_peer_same_role': {
                'name': 'Priya Patel',
                'income': 82000,
                'age': 31,
                'race': 'asian',
                'education': 'bachelors',
                'location': 'Houston',
                'job_title': 'Senior Account Manager',
                'years_experience': 6
            }
        }
    
    def test_entry_level_graduate_scenario(self):
        """Test entry-level graduate scenario"""
        user = self.african_american_profiles['entry_level_graduate']
        
        result = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        
        # Verify percentile is in expected range
        national_percentile = result['national']['percentile_rank']
        self.assertGreaterEqual(national_percentile, user['expected_percentile_range'][0])
        self.assertLessEqual(national_percentile, user['expected_percentile_range'][1])
        
        # Verify income gap direction
        national_gap = result['national']['income_gap']
        if user['expected_gap_direction'] == 'negative':
            self.assertLess(national_gap, 0)
        elif user['expected_gap_direction'] == 'positive':
            self.assertGreater(national_gap, 0)
        
        # Verify age group comparison
        age_percentile = result['age_group']['percentile_rank']
        self.assertEqual(result['age_group']['age_group'], '25-34')
        
        # Verify education comparison
        education_percentile = result['education_level']['percentile_rank']
        self.assertEqual(result['education_level']['education_level'], 'bachelors')
        
        # Verify location comparison
        location_percentile = result['location']['percentile_rank']
        self.assertEqual(result['location']['location'], 'Atlanta')
        
        # Verify summary is encouraging for entry-level
        summary = result['summary']
        encouraging_words = ['opportunity', 'growth', 'potential', 'advancement']
        has_encouraging_content = any(word in summary.lower() for word in encouraging_words)
        self.assertTrue(has_encouraging_content, f"Entry-level summary should be encouraging: {summary}")
    
    def test_mid_level_professional_scenario(self):
        """Test mid-level professional scenario"""
        user = self.african_american_profiles['mid_level_professional']
        
        result = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        
        # Verify percentile is in expected range
        national_percentile = result['national']['percentile_rank']
        self.assertGreaterEqual(national_percentile, user['expected_percentile_range'][0])
        self.assertLessEqual(national_percentile, user['expected_percentile_range'][1])
        
        # Verify all comparison types
        for comparison_type in ['national', 'age_group', 'education_level', 'location']:
            comparison = result[comparison_type]
            self.assertGreater(comparison['median_income'], 0)
            self.assertGreaterEqual(comparison['percentile_rank'], 1)
            self.assertLessEqual(comparison['percentile_rank'], 100)
        
        # Verify summary is balanced
        summary = result['summary']
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 50)  # Should have substantial content
    
    def test_experienced_manager_scenario(self):
        """Test experienced manager scenario"""
        user = self.african_american_profiles['experienced_manager']
        
        result = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        
        # Verify high percentile for experienced manager
        national_percentile = result['national']['percentile_rank']
        self.assertGreaterEqual(national_percentile, user['expected_percentile_range'][0])
        self.assertLessEqual(national_percentile, user['expected_percentile_range'][1])
        
        # Verify positive income gap
        national_gap = result['national']['income_gap']
        self.assertGreater(national_gap, 0)
        
        # Verify age group is correct
        self.assertEqual(result['age_group']['age_group'], '35-44')
        
        # Verify education level is correct
        self.assertEqual(result['education_level']['education_level'], 'masters')
        
        # Verify summary is positive for high performer
        summary = result['summary']
        positive_words = ['excellent', 'strong', 'above', 'competitive']
        has_positive_content = any(word in summary.lower() for word in positive_words)
        self.assertTrue(has_positive_content, f"Experienced manager summary should be positive: {summary}")
    
    def test_senior_executive_scenario(self):
        """Test senior executive scenario"""
        user = self.african_american_profiles['senior_executive']
        
        result = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        
        # Verify very high percentile for senior executive
        national_percentile = result['national']['percentile_rank']
        self.assertGreaterEqual(national_percentile, user['expected_percentile_range'][0])
        self.assertLessEqual(national_percentile, user['expected_percentile_range'][1])
        
        # Verify significant positive income gap
        national_gap = result['national']['income_gap']
        self.assertGreater(national_gap, 20000)  # Should be significantly above median
        
        # Verify summary is celebratory
        summary = result['summary']
        celebratory_words = ['excellent', 'outstanding', 'top', 'exceptional']
        has_celebratory_content = any(word in summary.lower() for word in celebratory_words)
        self.assertTrue(has_celebratory_content, f"Senior executive summary should be celebratory: {summary}")
    
    def test_career_changer_scenario(self):
        """Test career changer scenario"""
        user = self.african_american_profiles['career_changer']
        
        result = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        
        # Verify percentile reflects career transition
        national_percentile = result['national']['percentile_rank']
        self.assertGreaterEqual(national_percentile, user['expected_percentile_range'][0])
        self.assertLessEqual(national_percentile, user['expected_percentile_range'][1])
        
        # Verify age group is correct for career changer
        self.assertEqual(result['age_group']['age_group'], '35-44')
        
        # Verify summary addresses career transition
        summary = result['summary']
        transition_words = ['transition', 'change', 'growth', 'opportunity']
        has_transition_content = any(word in summary.lower() for word in transition_words)
        self.assertTrue(has_transition_content, f"Career changer summary should address transition: {summary}")
    
    def test_entrepreneur_scenario(self):
        """Test entrepreneur scenario"""
        user = self.african_american_profiles['entrepreneur']
        
        result = self.comparator.comprehensive_comparison(
            user['income'], user['race'], user['age'],
            user['education'], user['location']
        )
        
        # Verify percentile reflects entrepreneurial success
        national_percentile = result['national']['percentile_rank']
        self.assertGreaterEqual(national_percentile, user['expected_percentile_range'][0])
        self.assertLessEqual(national_percentile, user['expected_percentile_range'][1])
        
        # Verify positive income gap for entrepreneur
        national_gap = result['national']['income_gap']
        self.assertGreater(national_gap, 0)
        
        # Verify summary acknowledges entrepreneurial success
        summary = result['summary']
        entrepreneurial_words = ['success', 'achievement', 'accomplishment', 'leadership']
        has_entrepreneurial_content = any(word in summary.lower() for word in entrepreneurial_words)
        self.assertTrue(has_entrepreneurial_content, f"Entrepreneur summary should acknowledge success: {summary}")
    
    def test_racial_comparison_accuracy(self):
        """Test racial comparison accuracy with peer profiles"""
        african_american_user = self.african_american_profiles['mid_level_professional']
        white_peer = self.comparison_profiles['white_peer_same_role']
        hispanic_peer = self.comparison_profiles['hispanic_peer_same_role']
        asian_peer = self.comparison_profiles['asian_peer_same_role']
        
        # Compare African American professional with peers
        african_american_result = self.comparator.comprehensive_comparison(
            african_american_user['income'], african_american_user['race'],
            african_american_user['age'], african_american_user['education'],
            african_american_user['location']
        )
        
        white_peer_result = self.comparator.comprehensive_comparison(
            white_peer['income'], white_peer['race'], white_peer['age'],
            white_peer['education'], white_peer['location']
        )
        
        hispanic_peer_result = self.comparator.comprehensive_comparison(
            hispanic_peer['income'], hispanic_peer['race'], hispanic_peer['age'],
            hispanic_peer['education'], hispanic_peer['location']
        )
        
        asian_peer_result = self.comparator.comprehensive_comparison(
            asian_peer['income'], asian_peer['race'], asian_peer['age'],
            asian_peer['education'], asian_peer['location']
        )
        
        # Verify income gaps reflect known disparities
        african_american_gap = african_american_result['national']['income_gap']
        white_peer_gap = white_peer_result['national']['income_gap']
        hispanic_peer_gap = hispanic_peer_result['national']['income_gap']
        asian_peer_gap = asian_peer_result['national']['income_gap']
        
        # African American gap should be negative relative to white peers
        self.assertLess(african_american_gap, white_peer_gap)
        
        # Verify percentiles reflect income differences
        african_american_percentile = african_american_result['national']['percentile_rank']
        white_peer_percentile = white_peer_result['national']['percentile_rank']
        
        # Should reflect income disparity
        self.assertLess(african_american_percentile, white_peer_percentile)
    
    def test_geographic_variations_realistic(self):
        """Test geographic variations with realistic expectations"""
        base_user = {
            'income': 65000,
            'age': 30,
            'race': 'african_american',
            'education': 'bachelors'
        }
        
        # Test high-cost vs low-cost metro areas
        high_cost_metros = ['New York City', 'Washington DC']
        low_cost_metros = ['Houston', 'Atlanta']
        
        for metro in high_cost_metros:
            with self.subTest(metro=metro):
                result = self.comparator.compare_income_by_location(
                    base_user['income'], base_user['race'], metro
                )
                
                # In high-cost metros, same income should have lower percentile
                percentile = result['percentile_rank']
                self.assertLess(percentile, 60)  # Should be below median in high-cost areas
        
        for metro in low_cost_metros:
            with self.subTest(metro=metro):
                result = self.comparator.compare_income_by_location(
                    base_user['income'], base_user['race'], metro
                )
                
                # In low-cost metros, same income should have higher percentile
                percentile = result['percentile_rank']
                self.assertGreater(percentile, 40)  # Should be above median in low-cost areas
    
    def test_education_impact_realistic(self):
        """Test education impact with realistic expectations"""
        base_user = {
            'income': 65000,
            'age': 30,
            'race': 'african_american'
        }
        
        education_levels = ['high_school', 'bachelors', 'masters']
        
        for education in education_levels:
            with self.subTest(education=education):
                result = self.comparator.compare_income_by_education(
                    base_user['income'], base_user['race'], education
                )
                
                # Same income should have different percentiles by education level
                percentile = result['percentile_rank']
                
                if education == 'high_school':
                    # High income for high school education
                    self.assertGreater(percentile, 70)
                elif education == 'bachelors':
                    # Average income for bachelor's education
                    self.assertGreaterEqual(percentile, 40)
                    self.assertLessEqual(percentile, 70)
                elif education == 'masters':
                    # Lower income for master's education
                    self.assertLess(percentile, 60)
    
    def test_age_group_transitions_realistic(self):
        """Test age group transitions with realistic expectations"""
        base_user = {
            'income': 65000,
            'race': 'african_american',
            'education': 'bachelors'
        }
        
        # Test young professional
        young_result = self.comparator.compare_income_by_age(
            base_user['income'], base_user['race'], 28
        )
        
        # Test mid-career professional
        mid_result = self.comparator.compare_income_by_age(
            base_user['income'], base_user['race'], 38
        )
        
        # Same income should have different percentiles by age
        young_percentile = young_result['percentile_rank']
        mid_percentile = mid_result['percentile_rank']
        
        # Young professional should have higher percentile for same income
        self.assertGreater(young_percentile, mid_percentile)
    
    def test_motivational_messaging_appropriateness(self):
        """Test that motivational messaging is appropriate for all scenarios"""
        for profile_name, user in self.african_american_profiles.items():
            with self.subTest(profile=profile_name):
                result = self.comparator.comprehensive_comparison(
                    user['income'], user['race'], user['age'],
                    user['education'], user['location']
                )
                
                summary = result['summary']
                
                # Should never be discouraging
                discouraging_words = ['failure', 'hopeless', 'impossible', 'never', 'can\'t']
                for word in discouraging_words:
                    self.assertNotIn(word, summary.lower(), 
                                   f"Summary should not contain discouraging word '{word}': {summary}")
                
                # Should always be encouraging
                encouraging_words = ['opportunity', 'potential', 'growth', 'advancement', 'improvement']
                has_encouraging_content = any(word in summary.lower() for word in encouraging_words)
                self.assertTrue(has_encouraging_content, 
                              f"Summary should contain encouraging content for {profile_name}: {summary}")
                
                # Should be professional and respectful
                self.assertGreater(len(summary), 50)  # Substantial content
                self.assertLess(len(summary), 500)    # Not too verbose
    
    def test_data_consistency_across_scenarios(self):
        """Test data consistency across all scenarios"""
        all_results = {}
        
        # Collect results for all profiles
        for profile_name, user in self.african_american_profiles.items():
            result = self.comparator.comprehensive_comparison(
                user['income'], user['race'], user['age'],
                user['education'], user['location']
            )
            all_results[profile_name] = result
        
        # Verify consistency in data structure
        for profile_name, result in all_results.items():
            with self.subTest(profile=profile_name):
                # All results should have same structure
                required_keys = ['national', 'age_group', 'education_level', 'location', 'summary']
                for key in required_keys:
                    self.assertIn(key, result)
                
                # All comparisons should have same structure
                for comparison_type in ['national', 'age_group', 'education_level', 'location']:
                    comparison = result[comparison_type]
                    required_comparison_keys = ['median_income', 'percentile_rank', 'income_gap', 'income_gap_percentage']
                    for key in required_comparison_keys:
                        self.assertIn(key, comparison)
                
                # All numeric values should be reasonable
                for comparison_type in ['national', 'age_group', 'education_level', 'location']:
                    comparison = result[comparison_type]
                    self.assertGreater(comparison['median_income'], 0)
                    self.assertGreaterEqual(comparison['percentile_rank'], 1)
                    self.assertLessEqual(comparison['percentile_rank'], 100)

if __name__ == '__main__':
    unittest.main() 