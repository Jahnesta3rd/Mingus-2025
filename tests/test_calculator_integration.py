"""
Integration Tests for Calculator Systems
Tests the integration of ML calculator systems with existing MINGUS project structure
"""
import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.services.calculator_integration_service import CalculatorIntegrationService, CalculatorResult, CulturalContext
from backend.services.calculator_database_service import CalculatorDatabaseService, UserProfileData, SubscriptionData
from backend.ml.models.intelligent_job_matcher import IntelligentJobMatcher
from backend.ml.models.income_comparator_optimized import OptimizedIncomeComparator

class TestCalculatorIntegration:
    """Test calculator integration with existing MINGUS infrastructure"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock()
        session.query.return_value.filter.return_value.first.return_value = None
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration"""
        config = Mock()
        config.STRIPE_SECRET_KEY = 'test_key'
        config.SMTP_HOST = 'smtp.test.com'
        config.SMTP_PORT = 587
        config.SMTP_USERNAME = 'test@test.com'
        config.SMTP_PASSWORD = 'test_password'
        config.FROM_EMAIL = 'billing@mingus.com'
        config.TAX_SERVICE_URL = 'https://tax.test.com'
        config.TAX_SERVICE_API_KEY = 'tax_key'
        config.EXCHANGE_RATE_API_URL = 'https://exchange.test.com'
        return config
    
    @pytest.fixture
    def calculator_service(self, mock_db_session, mock_config):
        """Calculator integration service instance"""
        return CalculatorIntegrationService(mock_db_session, mock_config)
    
    @pytest.fixture
    def database_service(self, mock_db_session, mock_config):
        """Calculator database service instance"""
        return CalculatorDatabaseService(mock_db_session, mock_config)
    
    @pytest.fixture
    def sample_user_profile(self):
        """Sample user profile data"""
        return UserProfileData(
            user_id=1,
            email='test@example.com',
            full_name='Test User',
            age_range='25-35',
            location_state='GA',
            location_city='Atlanta',
            monthly_income=5000.0,
            employment_status='employed',
            primary_goal='save',
            risk_tolerance='moderate',
            investment_experience='intermediate',
            current_savings=10000.0,
            current_debt=5000.0,
            credit_score_range='good',
            household_size=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_subscription_data(self):
        """Sample subscription data"""
        return SubscriptionData(
            subscription_id=1,
            user_id=1,
            tier_name='Mid-tier ($20)',
            monthly_price=20.0,
            status='active',
            billing_cycle='monthly',
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
    
    def test_calculator_integration_service_initialization(self, calculator_service):
        """Test calculator integration service initialization"""
        assert calculator_service is not None
        assert hasattr(calculator_service, 'job_matcher')
        assert hasattr(calculator_service, 'income_comparator')
        assert hasattr(calculator_service, 'billing_features')
        assert hasattr(calculator_service, 'cultural_context')
        assert hasattr(calculator_service, 'performance_monitor')
        assert hasattr(calculator_service, '_lock')
    
    def test_database_service_initialization(self, database_service):
        """Test calculator database service initialization"""
        assert database_service is not None
        assert hasattr(database_service, 'db')
        assert hasattr(database_service, 'config')
        assert hasattr(database_service, '_lock')
        assert hasattr(database_service, '_user_profile_cache')
        assert hasattr(database_service, '_subscription_cache')
        assert hasattr(database_service, '_cache_ttl')
    
    def test_cultural_context_initialization(self):
        """Test cultural context initialization"""
        cultural_context = CulturalContext()
        
        # Test target metro areas
        assert 'Atlanta' in cultural_context.target_metro_areas
        assert cultural_context.target_metro_areas['Atlanta'] == 95000
        assert 'Houston' in cultural_context.target_metro_areas
        assert cultural_context.target_metro_areas['Houston'] == 88000
        
        # Test community challenges
        assert len(cultural_context.community_challenges) == 5
        assert 'Income instability' in cultural_context.community_challenges
        assert 'Student debt burden' in cultural_context.community_challenges
        
        # Test age-based focus
        assert '25-35' in cultural_context.age_based_focus
        assert len(cultural_context.age_based_focus['25-35']) == 5
        assert 'Career advancement opportunities' in cultural_context.age_based_focus['25-35']
    
    @patch('backend.services.calculator_integration_service.IntelligentJobMatcher')
    @patch('backend.services.calculator_integration_service.get_income_comparator')
    def test_perform_comprehensive_analysis(self, mock_get_comparator, mock_job_matcher, calculator_service):
        """Test comprehensive analysis performance"""
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.profile = Mock()
        mock_user.profile.monthly_income = 5000.0
        mock_user.profile.location_city = 'Atlanta'
        mock_user.profile.age_range = '25-35'
        mock_user.profile.employment_status = 'employed'
        
        # Mock calculator service methods
        calculator_service._get_user_with_profile = Mock(return_value=mock_user)
        calculator_service._perform_income_analysis = Mock(return_value={
            'current_income': 60000,
            'overall_percentile': 75.0,
            'career_opportunity_score': 25.0,
            'cultural_insights': {'target_demographic': 'African American professionals'},
            'recommendations': ['Focus on skill development']
        })
        calculator_service._perform_job_matching_analysis = Mock(return_value={
            'job_recommendations': [{'title': 'Senior Data Analyst', 'company': 'Test Corp'}],
            'search_statistics': {'total_jobs': 10}
        })
        calculator_service._perform_assessment_scoring = Mock(return_value={
            'score': 20,
            'segment': 'relationship-spender',
            'product_tier': 'Mid-tier ($20)',
            'challenges': ['Setting healthy boundaries'],
            'recommendations': ['Learn boundary-setting techniques']
        })
        calculator_service._perform_tax_calculation = Mock(return_value={
            'tax_liability': 5000,
            'effective_tax_rate': 0.15
        })
        calculator_service._generate_cultural_recommendations = Mock(return_value={
            'age_group': '25-35',
            'location': 'Atlanta',
            'age_based_recommendations': ['Career advancement opportunities']
        })
        calculator_service._generate_integrated_recommendations = Mock(return_value=[
            'High career advancement potential',
            'Found 10 high-quality job opportunities'
        ])
        calculator_service._log_audit_event = Mock()
        
        # Perform comprehensive analysis
        start_time = time.time()
        result = calculator_service.perform_comprehensive_analysis(1)
        calculation_time = time.time() - start_time
        
        # Verify performance requirements
        assert calculation_time < 0.5  # <500ms target
        assert isinstance(result, CalculatorResult)
        assert result.user_id == 1
        assert result.calculation_type == 'comprehensive_analysis'
        assert 'income_analysis' in result.result_data
        assert 'job_matching' in result.result_data
        assert 'assessment_scoring' in result.result_data
        assert 'tax_calculation' in result.result_data
        assert 'cultural_context' in result.result_data
        assert len(result.recommendations) > 0
    
    def test_income_analysis_performance(self, calculator_service):
        """Test income analysis performance"""
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.profile = Mock()
        mock_user.profile.monthly_income = 5000.0
        mock_user.profile.location_city = 'Atlanta'
        mock_user.profile.age_range = '25-35'
        
        # Mock income comparator
        mock_analysis = Mock()
        mock_analysis.comparisons = []
        mock_analysis.overall_percentile = 75.0
        mock_analysis.career_opportunity_score = 25.0
        mock_analysis.motivational_summary = 'You have significant growth potential'
        mock_analysis.action_plan = ['Assess your skills gap']
        
        calculator_service.income_comparator.analyze_income = Mock(return_value=mock_analysis)
        calculator_service._add_cultural_insights = Mock(return_value={
            'target_demographic': 'African American professionals'
        })
        
        # Perform income analysis
        start_time = time.time()
        result = calculator_service._perform_income_analysis(mock_user)
        calculation_time = time.time() - start_time
        
        # Verify performance requirements
        assert calculation_time < 0.2  # <200ms target
        assert 'current_income' in result
        assert 'overall_percentile' in result
        assert 'career_opportunity_score' in result
        assert 'cultural_insights' in result
    
    def test_assessment_scoring_exact_formulas(self, calculator_service):
        """Test assessment scoring with exact formulas"""
        # Test data with exact point assignments
        assessment_data = {
            'relationship_status': 'married',  # 6 points
            'spending_habits': 'joint_accounts',  # 4 points
            'financial_stress': 'sometimes',  # 4 points
            'emotional_triggers': ['after_breakup', 'social_pressure']  # 3 + 2 = 5 points
        }
        
        # Calculate expected score: 6 + 4 + 4 + 5 = 19
        expected_score = 19
        
        # Perform assessment scoring
        result = calculator_service._calculate_assessment_score(assessment_data)
        
        # Verify exact scoring
        assert result['score'] == expected_score
        assert result['segment'] == 'relationship-spender'  # 19 <= 25
        assert result['product_tier'] == 'Mid-tier ($20)'
        assert len(result['challenges']) > 0
        assert len(result['recommendations']) > 0
    
    def test_assessment_segment_classification(self, calculator_service):
        """Test exact segment classification"""
        # Test stress-free segment (score <= 16)
        stress_free_data = {
            'relationship_status': 'single',  # 0 points
            'spending_habits': 'keep_separate',  # 0 points
            'financial_stress': 'never',  # 0 points
            'emotional_triggers': ['none']  # 0 points
        }
        result = calculator_service._calculate_assessment_score(stress_free_data)
        assert result['segment'] == 'stress-free'
        assert result['product_tier'] == 'Budget ($10)'
        
        # Test crisis-mode segment (score > 35)
        crisis_data = {
            'relationship_status': 'complicated',  # 8 points
            'spending_habits': 'overspend_impress',  # 8 points
            'financial_stress': 'always',  # 8 points
            'emotional_triggers': ['after_breakup', 'after_arguments', 'when_lonely']  # 3 + 3 + 2 = 8 points
        }
        result = calculator_service._calculate_assessment_score(crisis_data)
        assert result['segment'] == 'crisis-mode'
        assert result['product_tier'] == 'Professional ($50)'
    
    def test_database_service_caching(self, database_service, sample_user_profile):
        """Test database service caching functionality"""
        # Mock database query
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = 'test@example.com'
        mock_user.full_name = 'Test User'
        mock_user.profile = Mock()
        mock_user.profile.age_range = '25-35'
        mock_user.profile.location_state = 'GA'
        mock_user.profile.location_city = 'Atlanta'
        mock_user.profile.monthly_income = 5000.0
        mock_user.profile.employment_status = 'employed'
        mock_user.profile.primary_goal = 'save'
        mock_user.profile.risk_tolerance = 'moderate'
        mock_user.profile.investment_experience = 'intermediate'
        mock_user.profile.current_savings = 10000.0
        mock_user.profile.current_debt = 5000.0
        mock_user.profile.credit_score_range = 'good'
        mock_user.profile.household_size = 2
        mock_user.profile.created_at = datetime.utcnow()
        mock_user.profile.updated_at = datetime.utcnow()
        
        database_service.db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_user
        
        # First call should query database
        result1 = database_service.get_user_profile_data(1)
        assert result1 is not None
        assert result1.user_id == 1
        
        # Second call should use cache
        result2 = database_service.get_user_profile_data(1)
        assert result2 is not None
        assert result2.user_id == 1
        
        # Verify cache was used (same object reference)
        assert result1 is result2
    
    def test_save_income_comparison_results(self, database_service):
        """Test saving income comparison results to database"""
        comparison_data = {
            'national_median': 74580,
            'current_income': 60000,
            'overall_percentile': 75.0,
            'career_opportunity_score': 25.0,
            'primary_gap': {'group_name': 'National Median', 'income_gap': -14580},
            'cultural_insights': {'target_demographic': 'African American professionals'},
            'recommendations': ['Focus on skill development']
        }
        
        # Mock database operations
        database_service.db.add = Mock()
        database_service.db.commit = Mock()
        database_service._log_audit_event = Mock()
        
        # Save results
        result = database_service.save_income_comparison_results(1, comparison_data)
        
        # Verify database operations
        assert result is True
        database_service.db.add.assert_called_once()
        database_service.db.commit.assert_called_once()
        database_service._log_audit_event.assert_called_once()
    
    def test_save_job_matching_results(self, database_service):
        """Test saving job matching results to database"""
        job_data = {
            'job_recommendations': [
                {
                    'title': 'Senior Data Analyst',
                    'company': 'Test Corp',
                    'location': 'Atlanta',
                    'salary_range': {'min': 80000, 'max': 100000, 'midpoint': 90000},
                    'overall_score': 0.85,
                    'score_breakdown': {
                        'salary_improvement': 0.9,
                        'skills_match': 0.8,
                        'career_progression': 0.7,
                        'company_quality': 0.8,
                        'location_fit': 0.9,
                        'growth_potential': 0.8
                    },
                    'recommendations': ['High salary increase potential'],
                    'risk_factors': ['Requires relocation']
                }
            ]
        }
        
        # Mock database operations
        database_service.db.add = Mock()
        database_service.db.commit = Mock()
        database_service._log_audit_event = Mock()
        
        # Save results
        result = database_service.save_job_matching_results(1, job_data)
        
        # Verify database operations
        assert result is True
        database_service.db.add.assert_called_once()
        database_service.db.commit.assert_called_once()
        database_service._log_audit_event.assert_called_once()
    
    def test_save_assessment_results(self, database_service):
        """Test saving assessment results to database"""
        assessment_data = {
            'score': 20,
            'segment': 'relationship-spender',
            'product_tier': 'Mid-tier ($20)',
            'challenges': ['Setting healthy boundaries'],
            'recommendations': ['Learn boundary-setting techniques']
        }
        
        # Mock user profile
        mock_profile = Mock()
        database_service.db.query.return_value.filter.return_value.first.return_value = mock_profile
        
        # Mock database operations
        database_service.db.commit = Mock()
        database_service._log_audit_event = Mock()
        
        # Save results
        result = database_service.save_assessment_results(1, assessment_data)
        
        # Verify database operations
        assert result is True
        database_service.db.commit.assert_called_once()
        database_service._log_audit_event.assert_called_once()
    
    def test_performance_monitoring(self, calculator_service):
        """Test performance monitoring functionality"""
        # Record performance metrics
        calculator_service._record_performance('income_analysis', 0.15)
        calculator_service._record_performance('income_analysis', 0.18)
        calculator_service._record_performance('income_analysis', 0.12)
        
        # Get average performance
        avg_performance = calculator_service._get_average_performance('income_analysis')
        
        # Verify performance monitoring
        assert avg_performance > 0
        assert avg_performance < 0.2  # Should be under 200ms target
        
        # Get performance stats
        stats = calculator_service.get_performance_stats()
        assert 'income_analysis_avg' in stats
        assert stats['income_analysis_avg'] > 0
    
    def test_cultural_personalization(self, calculator_service):
        """Test cultural personalization for target demographic"""
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.profile = Mock()
        mock_user.profile.age_range = '25-35'
        mock_user.profile.location_city = 'Atlanta'
        
        # Generate cultural recommendations
        result = calculator_service._generate_cultural_recommendations(mock_user)
        
        # Verify cultural personalization
        assert 'age_group' in result
        assert result['age_group'] == '25-35'
        assert 'location' in result
        assert result['location'] == 'Atlanta'
        assert 'age_based_recommendations' in result
        assert len(result['age_based_recommendations']) > 0
        assert 'location_opportunities' in result
        assert 'community_insights' in result
        assert 'target_metro_areas' in result
        assert 'community_challenges' in result
    
    def test_location_opportunities(self, calculator_service):
        """Test location-specific opportunities"""
        # Test Atlanta opportunities
        atlanta_opportunities = calculator_service._get_location_opportunities('Atlanta')
        assert atlanta_opportunities['target_income'] == 95000
        assert atlanta_opportunities['growth_potential'] == 118750  # 95000 * 1.25
        assert atlanta_opportunities['metro_ranking'] == 1
        assert atlanta_opportunities['opportunity_score'] == 100  # (95000/50000) * 100
        
        # Test unknown location
        unknown_opportunities = calculator_service._get_location_opportunities('Unknown City')
        assert unknown_opportunities['target_income'] == 50000
        assert unknown_opportunities['metro_ranking'] == 0
    
    def test_community_insights(self, calculator_service):
        """Test community-specific insights"""
        # Mock user data
        mock_user = Mock()
        mock_user.id = 1
        mock_user.profile = Mock()
        
        # Get community insights
        insights = calculator_service._get_community_insights(mock_user)
        
        # Verify community insights
        assert 'income_instability_risk' in insights
        assert 'student_debt_impact' in insights
        assert 'career_barriers' in insights
        assert 'homeownership_readiness' in insights
        assert 'financial_literacy_level' in insights
    
    def test_integrated_recommendations(self, calculator_service):
        """Test integrated recommendations generation"""
        income_analysis = {
            'career_opportunity_score': 25.0
        }
        job_matching = {
            'job_recommendations': [{'title': 'Test Job'}]
        }
        assessment_scoring = {
            'segment': 'crisis-mode'
        }
        tax_calculation = {
            'tax_liability': 5000
        }
        
        # Generate integrated recommendations
        recommendations = calculator_service._generate_integrated_recommendations(
            income_analysis, job_matching, assessment_scoring, tax_calculation
        )
        
        # Verify recommendations
        assert len(recommendations) > 0
        assert len(recommendations) <= 5  # Limited to top 5
        assert any('career advancement' in rec.lower() for rec in recommendations)
        assert any('job opportunities' in rec.lower() for rec in recommendations)
        assert any('professional' in rec.lower() for rec in recommendations)
        assert any('tax strategy' in rec.lower() for rec in recommendations)
    
    def test_cache_clearing(self, calculator_service, database_service):
        """Test cache clearing functionality"""
        # Clear caches
        calculator_service.clear_performance_cache()
        database_service.clear_cache()
        
        # Verify caches are cleared
        assert len(calculator_service.performance_monitor['income_analysis']) == 0
        assert len(database_service._user_profile_cache) == 0
        assert len(database_service._subscription_cache) == 0
    
    def test_database_stats(self, database_service):
        """Test database statistics functionality"""
        # Mock database queries
        database_service.db.query.return_value.count.return_value = 100
        database_service.db.query.return_value.filter.return_value.count.return_value = 80
        
        # Get database stats
        stats = database_service.get_database_stats()
        
        # Verify stats structure
        assert 'user_profiles' in stats
        assert 'subscriptions' in stats
        assert 'calculator_usage' in stats
        assert 'total_users' in stats['user_profiles']
        assert 'users_with_profiles' in stats['user_profiles']
        assert 'profile_completion_rate' in stats['user_profiles']
        assert 'active_subscriptions' in stats['subscriptions']
        assert 'total_calculator_events' in stats['calculator_usage']
    
    def test_error_handling(self, calculator_service, database_service):
        """Test error handling in calculator services"""
        # Test database service error handling
        database_service.db.query.side_effect = Exception("Database error")
        
        # Should handle error gracefully
        result = database_service.get_user_profile_data(1)
        assert result is None
        
        # Test calculator service error handling
        calculator_service._get_user_with_profile = Mock(return_value=None)
        
        # Should raise ValueError for missing user
        with pytest.raises(ValueError):
            calculator_service.perform_comprehensive_analysis(999)
    
    def test_thread_safety(self, calculator_service, database_service):
        """Test thread safety of calculator services"""
        import threading
        import time
        
        # Test performance monitoring thread safety
        def record_performance():
            for i in range(10):
                calculator_service._record_performance('test_operation', 0.1)
                time.sleep(0.01)
        
        # Create multiple threads
        threads = [threading.Thread(target=record_performance) for _ in range(5)]
        
        # Start threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify thread safety
        avg_performance = calculator_service._get_average_performance('test_operation')
        assert avg_performance > 0
        assert avg_performance <= 0.1  # Should be around 0.1
    
    def test_memory_efficiency(self, calculator_service, database_service):
        """Test memory efficiency with immutable data structures"""
        # Test that frozen dataclasses are used
        cultural_context = calculator_service.cultural_context
        assert hasattr(cultural_context, '__dataclass_params__')
        assert cultural_context.__dataclass_params__.frozen is True
        
        # Test that immutable data is returned
        user_profile = UserProfileData(
            user_id=1,
            email='test@example.com',
            full_name='Test User',
            age_range='25-35',
            location_state='GA',
            location_city='Atlanta',
            monthly_income=5000.0,
            employment_status='employed',
            primary_goal='save',
            risk_tolerance='moderate',
            investment_experience='intermediate',
            current_savings=10000.0,
            current_debt=5000.0,
            credit_score_range='good',
            household_size=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert hasattr(user_profile, '__dataclass_params__')
        assert user_profile.__dataclass_params__.frozen is True
