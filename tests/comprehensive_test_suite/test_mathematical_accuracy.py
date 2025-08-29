"""
Mathematical Accuracy Tests for Assessment Scoring System

Verify exact calculation formulas match Calculator Analysis Summary
Test salary improvement score thresholds, relationship scoring, and percentile calculations.
"""

import pytest
import math
from unittest.mock import patch, Mock
from decimal import Decimal, getcontext

pytestmark = pytest.mark.mathematical

# Set precision for decimal calculations
getcontext().prec = 28

class TestSalaryImprovementScoreCalculation:
    """Test salary improvement score calculation accuracy"""
    
    def test_salary_improvement_score_45_percent_threshold(self, assessment_scoring_service, mathematical_validator):
        """Test salary improvement score at 45% threshold (should be 1.0)"""
        current_salary = 100000
        target_salary = 145000  # 45% improvement
        
        score = assessment_scoring_service._calculate_salary_improvement_score(
            current_salary, target_salary
        )
        
        assert mathematical_validator.validate_salary_improvement_score(
            current_salary, target_salary, score
        )
        assert abs(score - 1.0) < 0.01
    
    def test_salary_improvement_score_35_percent_threshold(self, assessment_scoring_service, mathematical_validator):
        """Test salary improvement score at 35% threshold (should be 0.9)"""
        current_salary = 100000
        target_salary = 135000  # 35% improvement
        
        score = assessment_scoring_service._calculate_salary_improvement_score(
            current_salary, target_salary
        )
        
        assert mathematical_validator.validate_salary_improvement_score(
            current_salary, target_salary, score
        )
        assert abs(score - 0.9) < 0.01
    
    def test_salary_improvement_score_25_percent_threshold(self, assessment_scoring_service, mathematical_validator):
        """Test salary improvement score at 25% threshold (should be 0.8)"""
        current_salary = 100000
        target_salary = 125000  # 25% improvement
        
        score = assessment_scoring_service._calculate_salary_improvement_score(
            current_salary, target_salary
        )
        
        assert mathematical_validator.validate_salary_improvement_score(
            current_salary, target_salary, score
        )
        assert abs(score - 0.8) < 0.01
    
    def test_salary_improvement_score_15_percent_threshold(self, assessment_scoring_service, mathematical_validator):
        """Test salary improvement score at 15% threshold (should be 0.7)"""
        current_salary = 100000
        target_salary = 115000  # 15% improvement
        
        score = assessment_scoring_service._calculate_salary_improvement_score(
            current_salary, target_salary
        )
        
        assert mathematical_validator.validate_salary_improvement_score(
            current_salary, target_salary, score
        )
        assert abs(score - 0.7) < 0.01
    
    def test_salary_improvement_score_5_percent_threshold(self, assessment_scoring_service, mathematical_validator):
        """Test salary improvement score at 5% threshold (should be 0.6)"""
        current_salary = 100000
        target_salary = 105000  # 5% improvement
        
        score = assessment_scoring_service._calculate_salary_improvement_score(
            current_salary, target_salary
        )
        
        assert mathematical_validator.validate_salary_improvement_score(
            current_salary, target_salary, score
        )
        assert abs(score - 0.6) < 0.01
    
    def test_salary_improvement_score_below_5_percent(self, assessment_scoring_service, mathematical_validator):
        """Test salary improvement score below 5% (should be 0.5)"""
        current_salary = 100000
        target_salary = 103000  # 3% improvement
        
        score = assessment_scoring_service._calculate_salary_improvement_score(
            current_salary, target_salary
        )
        
        assert mathematical_validator.validate_salary_improvement_score(
            current_salary, target_salary, score
        )
        assert abs(score - 0.5) < 0.01
    
    def test_salary_improvement_score_exact_boundaries(self, assessment_scoring_service):
        """Test salary improvement score at exact boundary values"""
        test_cases = [
            (100000, 145000, 1.0),   # Exactly 45%
            (100000, 134999, 0.8),   # Just below 35%
            (100000, 135000, 0.9),   # Exactly 35%
            (100000, 124999, 0.7),   # Just below 25%
            (100000, 125000, 0.8),   # Exactly 25%
            (100000, 114999, 0.6),   # Just below 15%
            (100000, 115000, 0.7),   # Exactly 15%
            (100000, 104999, 0.5),   # Just below 5%
            (100000, 105000, 0.6),   # Exactly 5%
        ]
        
        for current, target, expected in test_cases:
            score = assessment_scoring_service._calculate_salary_improvement_score(
                current, target
            )
            assert abs(score - expected) < 0.01, f"Failed for {current} -> {target}: expected {expected}, got {score}"
    
    def test_salary_improvement_score_edge_cases(self, assessment_scoring_service):
        """Test salary improvement score edge cases"""
        # Same salary (0% improvement)
        score = assessment_scoring_service._calculate_salary_improvement_score(100000, 100000)
        assert abs(score - 0.5) < 0.01
        
        # Lower target salary (negative improvement)
        score = assessment_scoring_service._calculate_salary_improvement_score(100000, 90000)
        assert abs(score - 0.5) < 0.01
        
        # Very high improvement (100%+)
        score = assessment_scoring_service._calculate_salary_improvement_score(100000, 250000)
        assert abs(score - 1.0) < 0.01


class TestRelationshipScoringCalculation:
    """Test relationship scoring calculation accuracy"""
    
    def test_relationship_status_points(self, assessment_scoring_service, mathematical_validator):
        """Test relationship status point assignments"""
        test_cases = [
            ('single', 0),
            ('dating', 2),
            ('serious', 4),
            ('married', 6),
            ('complicated', 8)
        ]
        
        for status, expected_points in test_cases:
            points = assessment_scoring_service._calculate_relationship_status_points(status)
            assert points == expected_points, f"Failed for {status}: expected {expected_points}, got {points}"
    
    def test_financial_stress_frequency_points(self, assessment_scoring_service, mathematical_validator):
        """Test financial stress frequency point assignments"""
        test_cases = [
            ('never', 0),
            ('rarely', 2),
            ('sometimes', 4),
            ('often', 6),
            ('always', 8)
        ]
        
        for frequency, expected_points in test_cases:
            points = assessment_scoring_service._calculate_stress_frequency_points(frequency)
            assert points == expected_points, f"Failed for {frequency}: expected {expected_points}, got {points}"
    
    def test_emotional_triggers_points(self, assessment_scoring_service, mathematical_validator):
        """Test emotional triggers point assignments"""
        test_cases = [
            ('after_breakup', 3),
            ('after_arguments', 3),
            ('when_lonely', 2),
            ('when_jealous', 2),
            ('social_pressure', 2)
        ]
        
        for trigger, expected_points in test_cases:
            points = assessment_scoring_service._calculate_trigger_points([trigger])
            assert points == expected_points, f"Failed for {trigger}: expected {expected_points}, got {points}"
    
    def test_complete_relationship_scoring(self, assessment_scoring_service, mathematical_validator):
        """Test complete relationship scoring calculation"""
        test_cases = [
            # (status, stress_frequency, triggers, expected_total)
            ('single', 'never', [], 0),
            ('dating', 'rarely', ['when_lonely'], 4),  # 2 + 2 + 2
            ('serious', 'sometimes', ['after_arguments'], 7),  # 4 + 4 + 3
            ('married', 'often', ['when_jealous', 'social_pressure'], 12),  # 6 + 6 + 2 + 2
            ('complicated', 'always', ['after_breakup', 'after_arguments'], 19),  # 8 + 8 + 3 + 3
        ]
        
        for status, stress_frequency, triggers, expected_total in test_cases:
            total_points = assessment_scoring_service._calculate_relationship_impact_score(
                status, stress_frequency, triggers
            )
            
            assert mathematical_validator.validate_relationship_scoring(
                status, stress_frequency, triggers, total_points
            )
            assert total_points == expected_total, f"Failed for {status}/{stress_frequency}/{triggers}: expected {expected_total}, got {total_points}"


class TestFieldSalaryMultipliers:
    """Test field salary multipliers accuracy"""
    
    def test_field_salary_multipliers_exact_values(self, assessment_scoring_service):
        """Test field salary multipliers match exact values from Calculator Analysis"""
        expected_multipliers = {
            'software_development': 1.2,  # 20% premium
            'data_analysis': 1.1,         # 10% premium
            'project_management': 1.0,    # Base level
            'marketing': 0.95,            # 5% discount
            'finance': 1.05,              # 5% premium
            'sales': 0.9,                 # 10% discount
            'operations': 0.95,           # 5% discount
            'hr': 0.9                     # 10% discount
        }
        
        for field, expected_multiplier in expected_multipliers.items():
            multiplier = assessment_scoring_service._get_field_salary_multiplier(field)
            assert abs(multiplier - expected_multiplier) < 0.001, f"Failed for {field}: expected {expected_multiplier}, got {multiplier}"
    
    def test_field_salary_calculation(self, assessment_scoring_service):
        """Test field salary calculation with multipliers"""
        base_salary = 100000
        
        test_cases = [
            ('software_development', 120000),  # 100000 * 1.2
            ('data_analysis', 110000),         # 100000 * 1.1
            ('project_management', 100000),    # 100000 * 1.0
            ('marketing', 95000),              # 100000 * 0.95
            ('finance', 105000),               # 100000 * 1.05
            ('sales', 90000),                  # 100000 * 0.9
            ('operations', 95000),             # 100000 * 0.95
            ('hr', 90000)                      # 100000 * 0.9
        ]
        
        for field, expected_salary in test_cases:
            adjusted_salary = assessment_scoring_service._calculate_field_adjusted_salary(
                base_salary, field
            )
            assert abs(adjusted_salary - expected_salary) < 0.01, f"Failed for {field}: expected {expected_salary}, got {adjusted_salary}"


class TestOverallRiskScoreCalculation:
    """Test overall risk score calculation accuracy"""
    
    def test_overall_score_weighted_calculation(self, assessment_scoring_service):
        """Test overall score calculation with exact weights from Calculator Analysis"""
        # Mock individual scores
        salary_score = 0.8
        skills_score = 0.7
        career_score = 0.6
        company_score = 0.9
        location_score = 0.5
        growth_score = 0.8
        
        # Calculate expected weighted score
        expected_score = (
            salary_score * 0.35 +      # 35% weight
            skills_score * 0.25 +      # 25% weight
            career_score * 0.20 +      # 20% weight
            company_score * 0.10 +     # 10% weight
            location_score * 0.05 +    # 5% weight
            growth_score * 0.05        # 5% weight
        )
        
        # Calculate actual score
        actual_score = assessment_scoring_service._calculate_overall_risk_score(
            salary_score, skills_score, career_score, company_score, location_score, growth_score
        )
        
        assert abs(actual_score - expected_score) < 0.001
        
        # Verify weights sum to 1.0
        weights_sum = 0.35 + 0.25 + 0.20 + 0.10 + 0.05 + 0.05
        assert abs(weights_sum - 1.0) < 0.001
    
    def test_overall_score_edge_cases(self, assessment_scoring_service):
        """Test overall score calculation edge cases"""
        # All perfect scores (1.0)
        perfect_score = assessment_scoring_service._calculate_overall_risk_score(1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        assert abs(perfect_score - 1.0) < 0.001
        
        # All zero scores (0.0)
        zero_score = assessment_scoring_service._calculate_overall_risk_score(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        assert abs(zero_score - 0.0) < 0.001
        
        # Mixed scores
        mixed_score = assessment_scoring_service._calculate_overall_risk_score(0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
        assert abs(mixed_score - 0.5) < 0.001


class TestSegmentClassification:
    """Test segment classification accuracy"""
    
    def test_segment_classification_thresholds(self, assessment_scoring_service):
        """Test segment classification at exact thresholds"""
        test_cases = [
            (16, 'stress-free', 'Budget ($10)'),
            (25, 'relationship-spender', 'Mid-tier ($20)'),
            (35, 'emotional-manager', 'Mid-tier ($20)'),
            (36, 'crisis-mode', 'Professional ($50)'),
        ]
        
        for total_score, expected_segment, expected_tier in test_cases:
            segment, tier = assessment_scoring_service._classify_user_segment(total_score)
            assert segment == expected_segment, f"Failed for score {total_score}: expected {expected_segment}, got {segment}"
            assert tier == expected_tier, f"Failed for score {total_score}: expected {expected_tier}, got {tier}"
    
    def test_segment_classification_boundaries(self, assessment_scoring_service):
        """Test segment classification at boundary values"""
        # Just below stress-free threshold
        segment, tier = assessment_scoring_service._classify_user_segment(15)
        assert segment == 'stress-free'
        assert tier == 'Budget ($10)'
        
        # Just above stress-free threshold
        segment, tier = assessment_scoring_service._classify_user_segment(17)
        assert segment == 'relationship-spender'
        assert tier == 'Mid-tier ($20)'
        
        # Just below relationship-spender threshold
        segment, tier = assessment_scoring_service._classify_user_segment(24)
        assert segment == 'relationship-spender'
        assert tier == 'Mid-tier ($20)'
        
        # Just above relationship-spender threshold
        segment, tier = assessment_scoring_service._classify_user_segment(26)
        assert segment == 'emotional-manager'
        assert tier == 'Mid-tier ($20)'
        
        # Just below emotional-manager threshold
        segment, tier = assessment_scoring_service._classify_user_segment(34)
        assert segment == 'emotional-manager'
        assert tier == 'Mid-tier ($20)'
        
        # Just above emotional-manager threshold
        segment, tier = assessment_scoring_service._classify_user_segment(36)
        assert segment == 'crisis-mode'
        assert tier == 'Professional ($50)'


class TestPercentileCalculation:
    """Test percentile calculation accuracy"""
    
    def test_percentile_calculation_basic(self, assessment_scoring_service, mathematical_validator):
        """Test basic percentile calculation"""
        demographic_data = [50000, 60000, 70000, 80000, 90000, 100000, 110000, 120000, 130000, 140000]
        salary = 85000
        
        percentile = assessment_scoring_service._calculate_percentile(salary, demographic_data)
        
        assert mathematical_validator.validate_percentile_calculation(
            salary, demographic_data, percentile
        )
        # 85000 is between 80000 and 90000, so should be around 40th percentile
        assert 35 <= percentile <= 45
    
    def test_percentile_calculation_edge_cases(self, assessment_scoring_service):
        """Test percentile calculation edge cases"""
        demographic_data = [50000, 60000, 70000, 80000, 90000]
        
        # Minimum value
        percentile = assessment_scoring_service._calculate_percentile(50000, demographic_data)
        assert abs(percentile - 20.0) < 1.0  # 1st out of 5 = 20th percentile
        
        # Maximum value
        percentile = assessment_scoring_service._calculate_percentile(90000, demographic_data)
        assert abs(percentile - 100.0) < 1.0  # 5th out of 5 = 100th percentile
        
        # Below minimum
        percentile = assessment_scoring_service._calculate_percentile(40000, demographic_data)
        assert abs(percentile - 0.0) < 1.0
        
        # Above maximum
        percentile = assessment_scoring_service._calculate_percentile(100000, demographic_data)
        assert abs(percentile - 100.0) < 1.0
    
    def test_percentile_calculation_large_dataset(self, assessment_scoring_service):
        """Test percentile calculation with large dataset"""
        import random
        
        # Generate large dataset
        demographic_data = [random.randint(30000, 200000) for _ in range(1000)]
        demographic_data.sort()
        
        # Test various percentiles
        test_percentiles = [10, 25, 50, 75, 90]
        
        for target_percentile in test_percentiles:
            index = int((target_percentile / 100) * len(demographic_data))
            salary = demographic_data[index]
            
            calculated_percentile = assessment_scoring_service._calculate_percentile(salary, demographic_data)
            
            # Allow some tolerance for percentile calculation
            assert abs(calculated_percentile - target_percentile) < 5.0


class TestTaxCalculation:
    """Test tax calculation with different state rates"""
    
    def test_tax_calculation_different_states(self, assessment_scoring_service):
        """Test tax calculation with different state tax rates"""
        salary = 100000
        
        # Test different state tax rates
        state_tax_rates = {
            'CA': 0.133,  # California
            'NY': 0.1085, # New York
            'TX': 0.0,    # Texas (no state income tax)
            'FL': 0.0,    # Florida (no state income tax)
            'WA': 0.0,    # Washington (no state income tax)
        }
        
        for state, expected_rate in state_tax_rates.items():
            tax_amount = assessment_scoring_service._calculate_state_tax(salary, state)
            expected_tax = salary * expected_rate
            
            assert abs(tax_amount - expected_tax) < 0.01, f"Failed for {state}: expected {expected_tax}, got {tax_amount}"
    
    def test_tax_calculation_federal_tax(self, assessment_scoring_service):
        """Test federal tax calculation"""
        test_cases = [
            (50000, 5000),   # 10% bracket
            (100000, 15000), # 15% bracket
            (200000, 40000), # 20% bracket
        ]
        
        for salary, expected_tax in test_cases:
            tax_amount = assessment_scoring_service._calculate_federal_tax(salary)
            # Allow some tolerance for tax calculation
            assert abs(tax_amount - expected_tax) < 1000, f"Failed for {salary}: expected {expected_tax}, got {tax_amount}"
    
    def test_tax_calculation_total_tax(self, assessment_scoring_service):
        """Test total tax calculation (federal + state)"""
        salary = 100000
        state = 'CA'
        
        total_tax = assessment_scoring_service._calculate_total_tax(salary, state)
        federal_tax = assessment_scoring_service._calculate_federal_tax(salary)
        state_tax = assessment_scoring_service._calculate_state_tax(salary, state)
        
        expected_total = federal_tax + state_tax
        assert abs(total_tax - expected_total) < 0.01


class TestMathematicalPrecision:
    """Test mathematical precision and rounding"""
    
    def test_decimal_precision_calculations(self, assessment_scoring_service):
        """Test decimal precision in calculations"""
        # Use Decimal for high precision calculations
        current_salary = Decimal('100000.00')
        target_salary = Decimal('145000.00')
        
        improvement_percentage = ((target_salary - current_salary) / current_salary) * Decimal('100.00')
        expected_percentage = Decimal('45.00')
        
        assert abs(improvement_percentage - expected_percentage) < Decimal('0.01')
    
    def test_floating_point_precision(self, assessment_scoring_service):
        """Test floating point precision in calculations"""
        # Test that floating point errors don't accumulate
        weights = [0.35, 0.25, 0.20, 0.10, 0.05, 0.05]
        weights_sum = sum(weights)
        
        assert abs(weights_sum - 1.0) < 1e-10
        
        # Test weighted average calculation
        scores = [0.8, 0.7, 0.6, 0.9, 0.5, 0.8]
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        
        # Verify calculation is precise
        expected_weighted_sum = 0.8 * 0.35 + 0.7 * 0.25 + 0.6 * 0.20 + 0.9 * 0.10 + 0.5 * 0.05 + 0.8 * 0.05
        assert abs(weighted_sum - expected_weighted_sum) < 1e-10
    
    def test_rounding_consistency(self, assessment_scoring_service):
        """Test rounding consistency across calculations"""
        # Test that rounding is consistent
        test_values = [0.123456789, 0.987654321, 0.5, 0.999999999]
        
        for value in test_values:
            rounded_2 = round(value, 2)
            rounded_4 = round(value, 4)
            
            # Verify rounding behavior is consistent
            assert abs(rounded_2 - round(rounded_4, 2)) < 1e-10


class TestCalculationPerformance:
    """Test calculation performance requirements"""
    
    def test_income_comparison_performance_target(self, assessment_scoring_service, performance_monitor):
        """Test that income comparison meets 45ms performance target"""
        import random
        
        # Generate test data
        demographic_data = [random.randint(30000, 200000) for _ in range(1000)]
        salary = 75000
        
        performance_monitor.start_timer('income_comparison')
        
        percentile = assessment_scoring_service._calculate_percentile(salary, demographic_data)
        
        performance_monitor.end_timer('income_comparison')
        
        duration = performance_monitor.get_duration('income_comparison')
        
        # Convert to milliseconds
        duration_ms = duration * 1000
        
        assert duration_ms < 45, f"Income comparison took {duration_ms}ms, exceeds 45ms target"
        assert percentile >= 0 and percentile <= 100
    
    def test_assessment_calculation_performance(self, assessment_scoring_service, performance_monitor, sample_assessment_data):
        """Test overall assessment calculation performance"""
        performance_monitor.start_timer('full_assessment_calculation')
        
        result = assessment_scoring_service.calculate_assessment(sample_assessment_data)
        
        performance_monitor.end_timer('full_assessment_calculation')
        
        duration = performance_monitor.get_duration('full_assessment_calculation')
        
        # Should complete within 2 seconds
        assert duration < 2.0, f"Assessment calculation took {duration}s, exceeds 2s target"
        assert 'overall_risk_level' in result
        assert 'primary_concerns' in result
