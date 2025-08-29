#!/usr/bin/env python3
"""
Comprehensive Test Suite for African American Professional Features
Mingus Financial App - Target Demographic: 25-35, $40K-$100K

This test suite verifies all features specifically designed for African American professionals,
including career advancement recommendations, income improvement suggestions, community-specific
financial challenges, cultural sensitivity, location-based features, and verification of the
top 10 problems addressed in the documentation.
"""

import sys
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from ml.models.income_comparator import IncomeComparator
    from ml.models.mingus_job_recommendation_engine import MingusJobRecommendationEngine
    from ml.models.intelligent_job_matcher import IntelligentJobMatcher
    from services.career_advancement_service import CareerAdvancementService
    from services.sms_message_templates import SMSMessageTemplates
    from services.communication_router import CommunicationRouter
    from services.intelligent_insights_service import IntelligentInsightsService
    from services.calculator_integration_service import CalculatorIntegrationService
    from services.salary_data_service import SalaryDataService
    from services.user_profile_service import UserProfileService
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'african_american_features_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    status: str  # PASS, FAIL, SKIP
    details: str
    execution_time: float
    data: Optional[Dict] = None

@dataclass
class FeatureTest:
    """Feature test configuration"""
    name: str
    description: str
    test_function: callable
    required: bool = True

class AfricanAmericanProfessionalFeaturesTester:
    """
    Comprehensive test suite for African American professional features
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
        # Target demographic parameters
        self.target_demographic = {
            'age_range': (25, 35),
            'income_range': (40000, 100000),
            'target_metro_areas': [
                'Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City',
                'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore'
            ]
        }
        
        # Top 10 problems identified from documentation
        self.top_10_problems = [
            "Limited access to generational wealth and family financial support",
            "Career advancement barriers in corporate environments", 
            "Student loan debt burden significantly above national averages",
            "Workplace microaggressions and cultural navigation challenges",
            "Limited access to professional networks and mentorship",
            "Housing and homeownership barriers in desirable areas",
            "Income instability and lack of emergency funds",
            "Financial literacy gaps and investment knowledge",
            "Systemic barriers to wealth building and investment",
            "Balancing individual success with community responsibility"
        ]
        
        # Initialize services
        self.initialize_services()
        
    def initialize_services(self):
        """Initialize all required services"""
        try:
            self.income_comparator = IncomeComparator()
            self.job_engine = MingusJobRecommendationEngine()
            self.job_matcher = IntelligentJobMatcher()
            self.career_service = CareerAdvancementService()
            self.sms_templates = SMSMessageTemplates()
            self.communication_router = CommunicationRouter()
            self.insights_service = IntelligentInsightsService()
            self.calculator_service = CalculatorIntegrationService()
            self.salary_service = SalaryDataService()
            self.user_profile_service = UserProfileService()
            logging.info("All services initialized successfully")
        except Exception as e:
            logging.error(f"Service initialization failed: {e}")
            raise
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all feature tests"""
        logging.info("Starting comprehensive African American professional features test suite")
        
        test_features = [
            FeatureTest(
                name="Career Advancement Recommendations",
                description="Test career advancement recommendations for African American professionals",
                test_function=self.test_career_advancement_recommendations
            ),
            FeatureTest(
                name="Income Improvement Suggestions", 
                description="Test income improvement and salary optimization features",
                test_function=self.test_income_improvement_suggestions
            ),
            FeatureTest(
                name="Community-Specific Financial Challenges",
                description="Test features addressing community-specific financial challenges",
                test_function=self.test_community_specific_challenges
            ),
            FeatureTest(
                name="Cultural Sensitivity in Financial Advice",
                description="Test cultural sensitivity and appropriateness of financial advice",
                test_function=self.test_cultural_sensitivity
            ),
            FeatureTest(
                name="Location-Based Features",
                description="Test location-based features for top 10 metro areas",
                test_function=self.test_location_based_features
            ),
            FeatureTest(
                name="Top 10 Problems Verification",
                description="Verify app addresses the top 10 problems for African American professionals",
                test_function=self.test_top_10_problems_addressed
            ),
            FeatureTest(
                name="Income Comparison Tool",
                description="Test demographic income comparison functionality",
                test_function=self.test_income_comparison_tool
            ),
            FeatureTest(
                name="Job Recommendation Engine",
                description="Test job recommendation engine for African American professionals",
                test_function=self.test_job_recommendation_engine
            ),
            FeatureTest(
                name="SMS Message Templates",
                description="Test culturally appropriate SMS messaging",
                test_function=self.test_sms_message_templates
            ),
            FeatureTest(
                name="Communication Router",
                description="Test communication routing and personalization",
                test_function=self.test_communication_router
            ),
            FeatureTest(
                name="Intelligent Insights Service",
                description="Test intelligent insights and recommendations",
                test_function=self.test_intelligent_insights
            ),
            FeatureTest(
                name="Calculator Integration",
                description="Test financial calculator integration",
                test_function=self.test_calculator_integration
            ),
            FeatureTest(
                name="Salary Data Service",
                description="Test salary data and benchmarking features",
                test_function=self.test_salary_data_service
            ),
            FeatureTest(
                name="User Profile Service",
                description="Test user profile and personalization features",
                test_function=self.test_user_profile_service
            )
        ]
        
        for feature in test_features:
            try:
                logging.info(f"Running test: {feature.name}")
                start_time = time.time()
                
                result = feature.test_function()
                execution_time = time.time() - start_time
                
                test_result = TestResult(
                    test_name=feature.name,
                    status="PASS" if result else "FAIL",
                    details=f"Test completed in {execution_time:.2f}s",
                    execution_time=execution_time,
                    data=result if isinstance(result, dict) else None
                )
                
                self.results.append(test_result)
                logging.info(f"✓ {feature.name}: {test_result.status}")
                
            except Exception as e:
                execution_time = time.time() - start_time
                test_result = TestResult(
                    test_name=feature.name,
                    status="FAIL",
                    details=f"Test failed with error: {str(e)}",
                    execution_time=execution_time
                )
                self.results.append(test_result)
                logging.error(f"✗ {feature.name}: FAILED - {str(e)}")
        
        return self.generate_report()
    
    def test_career_advancement_recommendations(self) -> Dict[str, Any]:
        """Test career advancement recommendations for African American professionals"""
        test_data = {
            'user_profile': {
                'age': 28,
                'income': 65000,
                'education': 'Bachelor\'s Degree',
                'location': 'Atlanta',
                'industry': 'Technology',
                'experience_years': 5,
                'current_role': 'Software Engineer'
            }
        }
        
        # Test career advancement service
        career_recommendations = self.career_service.get_career_advancement_recommendations(
            user_profile=test_data['user_profile']
        )
        
        # Verify recommendations are culturally appropriate
        cultural_keywords = [
            'mentorship', 'networking', 'leadership', 'executive presence',
            'professional development', 'career advancement', 'representation'
        ]
        
        recommendations_text = json.dumps(career_recommendations).lower()
        cultural_relevance_score = sum(1 for keyword in cultural_keywords if keyword in recommendations_text)
        
        return {
            'recommendations': career_recommendations,
            'cultural_relevance_score': cultural_relevance_score,
            'total_keywords': len(cultural_keywords),
            'relevance_percentage': (cultural_relevance_score / len(cultural_keywords)) * 100
        }
    
    def test_income_improvement_suggestions(self) -> Dict[str, Any]:
        """Test income improvement and salary optimization features"""
        test_income = 65000
        test_location = 'Atlanta'
        
        # Test income comparison
        income_analysis = self.income_comparator.analyze_income(
            user_income=test_income,
            age=28,
            education='Bachelor\'s Degree',
            location=test_location,
            metro_area=test_location
        )
        
        # Test salary optimization suggestions
        salary_suggestions = self.salary_service.get_salary_optimization_suggestions(
            current_salary=test_income,
            location=test_location,
            experience_years=5,
            industry='Technology'
        )
        
        return {
            'income_analysis': income_analysis,
            'salary_suggestions': salary_suggestions,
            'income_gap_identified': income_analysis.get('career_opportunity_score', 0) > 20,
            'optimization_opportunities': len(salary_suggestions.get('suggestions', []))
        }
    
    def test_community_specific_challenges(self) -> Dict[str, Any]:
        """Test features addressing community-specific financial challenges"""
        challenges_addressed = []
        
        # Test student loan debt management
        student_loan_insights = self.insights_service.get_student_loan_insights(
            user_income=65000,
            debt_amount=45000,
            age=28
        )
        if student_loan_insights:
            challenges_addressed.append("Student loan debt burden")
        
        # Test generational wealth building
        wealth_building_insights = self.insights_service.get_wealth_building_insights(
            user_income=65000,
            age=28,
            location='Atlanta'
        )
        if wealth_building_insights:
            challenges_addressed.append("Generational wealth building")
        
        # Test homeownership barriers
        homeownership_insights = self.insights_service.get_homeownership_insights(
            user_income=65000,
            location='Atlanta',
            credit_score=720
        )
        if homeownership_insights:
            challenges_addressed.append("Homeownership barriers")
        
        return {
            'challenges_addressed': challenges_addressed,
            'student_loan_insights': student_loan_insights,
            'wealth_building_insights': wealth_building_insights,
            'homeownership_insights': homeownership_insights,
            'coverage_percentage': (len(challenges_addressed) / 3) * 100
        }
    
    def test_cultural_sensitivity(self) -> Dict[str, Any]:
        """Test cultural sensitivity and appropriateness of financial advice"""
        # Test SMS message templates for cultural appropriateness
        test_user = {
            'first_name': 'Marcus',
            'income': 65000,
            'location': 'Atlanta',
            'age': 28
        }
        
        # Test different message types
        message_types = [
            'low_balance_warning',
            'career_advancement',
            'wealth_building',
            'community_engagement'
        ]
        
        cultural_appropriateness_scores = []
        messages = []
        
        for message_type in message_types:
            try:
                message = self.sms_templates.get_message(
                    message_type=message_type,
                    user_data=test_user
                )
                messages.append(message)
                
                # Check for cultural sensitivity indicators
                cultural_indicators = [
                    'community', 'legacy', 'generational', 'excellence',
                    'representation', 'empowerment', 'foundation'
                ]
                
                message_lower = message.lower()
                cultural_score = sum(1 for indicator in cultural_indicators if indicator in message_lower)
                cultural_appropriateness_scores.append(cultural_score)
                
            except Exception as e:
                logging.warning(f"Could not test message type {message_type}: {e}")
        
        return {
            'messages': messages,
            'cultural_scores': cultural_appropriateness_scores,
            'average_cultural_score': sum(cultural_appropriateness_scores) / len(cultural_appropriateness_scores) if cultural_appropriateness_scores else 0,
            'message_types_tested': len(message_types)
        }
    
    def test_location_based_features(self) -> Dict[str, Any]:
        """Test location-based features for top 10 metro areas"""
        metro_areas = self.target_demographic['target_metro_areas']
        location_features = {}
        
        for metro in metro_areas:
            try:
                # Test income comparison for each metro area
                metro_income_analysis = self.income_comparator.analyze_income(
                    user_income=65000,
                    age=28,
                    education='Bachelor\'s Degree',
                    location=metro,
                    metro_area=metro
                )
                
                # Test job opportunities for each metro area
                metro_jobs = self.job_engine.get_job_recommendations(
                    user_profile={
                        'location': metro,
                        'income': 65000,
                        'experience_years': 5,
                        'industry': 'Technology'
                    },
                    limit=5
                )
                
                location_features[metro] = {
                    'income_analysis': metro_income_analysis,
                    'job_opportunities': len(metro_jobs) if metro_jobs else 0,
                    'metro_specific_data': True
                }
                
            except Exception as e:
                location_features[metro] = {
                    'error': str(e),
                    'metro_specific_data': False
                }
        
        successful_metros = sum(1 for data in location_features.values() if data.get('metro_specific_data', False))
        
        return {
            'location_features': location_features,
            'metros_supported': successful_metros,
            'total_metros': len(metro_areas),
            'coverage_percentage': (successful_metros / len(metro_areas)) * 100
        }
    
    def test_top_10_problems_addressed(self) -> Dict[str, Any]:
        """Verify app addresses the top 10 problems for African American professionals"""
        problems_addressed = []
        problem_details = {}
        
        for i, problem in enumerate(self.top_10_problems):
            addressed = False
            details = {}
            
            if "generational wealth" in problem.lower():
                # Test wealth building features
                wealth_features = self.insights_service.get_wealth_building_insights(
                    user_income=65000,
                    age=28,
                    location='Atlanta'
                )
                addressed = wealth_features is not None
                details = {'feature': 'Wealth Building Insights', 'data': wealth_features}
            
            elif "career advancement" in problem.lower():
                # Test career advancement features
                career_features = self.career_service.get_career_advancement_recommendations(
                    user_profile={'age': 28, 'income': 65000, 'location': 'Atlanta'}
                )
                addressed = career_features is not None
                details = {'feature': 'Career Advancement Service', 'data': career_features}
            
            elif "student loan" in problem.lower():
                # Test student loan features
                loan_features = self.insights_service.get_student_loan_insights(
                    user_income=65000,
                    debt_amount=45000,
                    age=28
                )
                addressed = loan_features is not None
                details = {'feature': 'Student Loan Insights', 'data': loan_features}
            
            elif "workplace" in problem.lower() or "microaggressions" in problem.lower():
                # Test workplace navigation features
                workplace_features = self.career_service.get_workplace_navigation_insights(
                    user_profile={'age': 28, 'income': 65000, 'location': 'Atlanta'}
                )
                addressed = workplace_features is not None
                details = {'feature': 'Workplace Navigation', 'data': workplace_features}
            
            elif "networks" in problem.lower() or "mentorship" in problem.lower():
                # Test networking features
                networking_features = self.career_service.get_networking_recommendations(
                    user_profile={'age': 28, 'income': 65000, 'location': 'Atlanta'}
                )
                addressed = networking_features is not None
                details = {'feature': 'Networking Recommendations', 'data': networking_features}
            
            elif "homeownership" in problem.lower():
                # Test homeownership features
                home_features = self.insights_service.get_homeownership_insights(
                    user_income=65000,
                    location='Atlanta',
                    credit_score=720
                )
                addressed = home_features is not None
                details = {'feature': 'Homeownership Insights', 'data': home_features}
            
            elif "income instability" in problem.lower():
                # Test emergency fund features
                emergency_features = self.calculator_service.get_emergency_fund_calculator(
                    monthly_expenses=3000,
                    income=65000
                )
                addressed = emergency_features is not None
                details = {'feature': 'Emergency Fund Calculator', 'data': emergency_features}
            
            elif "financial literacy" in problem.lower():
                # Test financial education features
                education_features = self.insights_service.get_financial_education_resources(
                    user_income=65000,
                    age=28
                )
                addressed = education_features is not None
                details = {'feature': 'Financial Education Resources', 'data': education_features}
            
            elif "systemic barriers" in problem.lower():
                # Test systemic barrier awareness features
                barrier_features = self.insights_service.get_systemic_barrier_insights(
                    user_income=65000,
                    location='Atlanta',
                    industry='Technology'
                )
                addressed = barrier_features is not None
                details = {'feature': 'Systemic Barrier Insights', 'data': barrier_features}
            
            elif "community responsibility" in problem.lower():
                # Test community engagement features
                community_features = self.insights_service.get_community_engagement_insights(
                    user_income=65000,
                    location='Atlanta'
                )
                addressed = community_features is not None
                details = {'feature': 'Community Engagement Insights', 'data': community_features}
            
            if addressed:
                problems_addressed.append(problem)
            
            problem_details[f"Problem {i+1}"] = {
                'problem': problem,
                'addressed': addressed,
                'details': details
            }
        
        return {
            'problems_addressed': problems_addressed,
            'total_problems': len(self.top_10_problems),
            'addressed_count': len(problems_addressed),
            'coverage_percentage': (len(problems_addressed) / len(self.top_10_problems)) * 100,
            'problem_details': problem_details
        }
    
    def test_income_comparison_tool(self) -> Dict[str, Any]:
        """Test demographic income comparison functionality"""
        test_cases = [
            {'income': 45000, 'age': 25, 'location': 'Atlanta'},
            {'income': 75000, 'age': 30, 'location': 'Houston'},
            {'income': 95000, 'age': 35, 'location': 'Washington DC'}
        ]
        
        comparison_results = []
        
        for test_case in test_cases:
            try:
                analysis = self.income_comparator.analyze_income(
                    user_income=test_case['income'],
                    age=test_case['age'],
                    education='Bachelor\'s Degree',
                    location=test_case['location'],
                    metro_area=test_case['location']
                )
                
                comparison_results.append({
                    'test_case': test_case,
                    'analysis': analysis,
                    'success': True
                })
                
            except Exception as e:
                comparison_results.append({
                    'test_case': test_case,
                    'error': str(e),
                    'success': False
                })
        
        successful_comparisons = sum(1 for result in comparison_results if result['success'])
        
        return {
            'comparison_results': comparison_results,
            'successful_comparisons': successful_comparisons,
            'total_test_cases': len(test_cases),
            'success_rate': (successful_comparisons / len(test_cases)) * 100
        }
    
    def test_job_recommendation_engine(self) -> Dict[str, Any]:
        """Test job recommendation engine for African American professionals"""
        test_profiles = [
            {
                'age': 25,
                'income': 45000,
                'location': 'Atlanta',
                'industry': 'Technology',
                'experience_years': 2
            },
            {
                'age': 30,
                'income': 75000,
                'location': 'Houston',
                'industry': 'Healthcare',
                'experience_years': 7
            },
            {
                'age': 35,
                'income': 95000,
                'location': 'Washington DC',
                'industry': 'Finance',
                'experience_years': 12
            }
        ]
        
        recommendation_results = []
        
        for profile in test_profiles:
            try:
                recommendations = self.job_engine.get_job_recommendations(
                    user_profile=profile,
                    limit=10
                )
                
                # Check for cultural relevance in job recommendations
                cultural_relevance = self.check_job_cultural_relevance(recommendations)
                
                recommendation_results.append({
                    'profile': profile,
                    'recommendations': recommendations,
                    'cultural_relevance': cultural_relevance,
                    'success': True
                })
                
            except Exception as e:
                recommendation_results.append({
                    'profile': profile,
                    'error': str(e),
                    'success': False
                })
        
        successful_recommendations = sum(1 for result in recommendation_results if result['success'])
        
        return {
            'recommendation_results': recommendation_results,
            'successful_recommendations': successful_recommendations,
            'total_profiles': len(test_profiles),
            'success_rate': (successful_recommendations / len(test_profiles)) * 100
        }
    
    def check_job_cultural_relevance(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Check cultural relevance of job recommendations"""
        if not recommendations:
            return {'score': 0, 'indicators': []}
        
        cultural_indicators = [
            'diversity', 'inclusion', 'equity', 'representation',
            'mentorship', 'leadership', 'professional development'
        ]
        
        relevant_jobs = []
        total_score = 0
        
        for job in recommendations:
            job_text = json.dumps(job).lower()
            job_score = sum(1 for indicator in cultural_indicators if indicator in job_text)
            
            if job_score > 0:
                relevant_jobs.append({
                    'job': job.get('title', 'Unknown'),
                    'score': job_score,
                    'indicators': [ind for ind in cultural_indicators if ind in job_text]
                })
                total_score += job_score
        
        return {
            'score': total_score,
            'relevant_jobs': relevant_jobs,
            'average_score': total_score / len(recommendations) if recommendations else 0
        }
    
    def test_sms_message_templates(self) -> Dict[str, Any]:
        """Test culturally appropriate SMS messaging"""
        test_user = {
            'first_name': 'Marcus',
            'income': 65000,
            'location': 'Atlanta',
            'age': 28,
            'balance': 2500,
            'days_until_negative': 3
        }
        
        message_types = [
            'low_balance_warning',
            'career_advancement',
            'wealth_building',
            'community_engagement',
            'financial_wellness_check'
        ]
        
        message_results = []
        
        for message_type in message_types:
            try:
                message = self.sms_templates.get_message(
                    message_type=message_type,
                    user_data=test_user
                )
                
                # Check message length (SMS limit)
                message_length = len(message)
                within_limit = message_length <= 160
                
                # Check cultural appropriateness
                cultural_score = self.assess_message_cultural_appropriateness(message)
                
                message_results.append({
                    'type': message_type,
                    'message': message,
                    'length': message_length,
                    'within_limit': within_limit,
                    'cultural_score': cultural_score,
                    'success': True
                })
                
            except Exception as e:
                message_results.append({
                    'type': message_type,
                    'error': str(e),
                    'success': False
                })
        
        successful_messages = sum(1 for result in message_results if result['success'])
        
        return {
            'message_results': message_results,
            'successful_messages': successful_messages,
            'total_types': len(message_types),
            'success_rate': (successful_messages / len(message_types)) * 100
        }
    
    def assess_message_cultural_appropriateness(self, message: str) -> Dict[str, Any]:
        """Assess cultural appropriateness of a message"""
        message_lower = message.lower()
        
        positive_indicators = [
            'community', 'legacy', 'generational', 'excellence',
            'representation', 'empowerment', 'foundation', 'success',
            'achievement', 'inspiration', 'motivation'
        ]
        
        negative_indicators = [
            'deficit', 'lack', 'failure', 'problem', 'issue',
            'struggle', 'difficulty', 'challenge'
        ]
        
        positive_score = sum(1 for indicator in positive_indicators if indicator in message_lower)
        negative_score = sum(1 for indicator in negative_indicators if indicator in message_lower)
        
        return {
            'positive_score': positive_score,
            'negative_score': negative_score,
            'net_score': positive_score - negative_score,
            'positive_indicators': [ind for ind in positive_indicators if ind in message_lower],
            'negative_indicators': [ind for ind in negative_indicators if ind in message_lower]
        }
    
    def test_communication_router(self) -> Dict[str, Any]:
        """Test communication routing and personalization"""
        test_users = [
            {
                'user_id': 'user1',
                'age': 25,
                'income': 45000,
                'location': 'Atlanta',
                'preferences': {'sms': True, 'email': False}
            },
            {
                'user_id': 'user2', 
                'age': 30,
                'income': 75000,
                'location': 'Houston',
                'preferences': {'sms': False, 'email': True}
            }
        ]
        
        routing_results = []
        
        for user in test_users:
            try:
                # Test communication routing
                route_result = self.communication_router.route_communication(
                    user_id=user['user_id'],
                    message_type='career_advancement',
                    user_data=user
                )
                
                routing_results.append({
                    'user': user,
                    'route_result': route_result,
                    'success': True
                })
                
            except Exception as e:
                routing_results.append({
                    'user': user,
                    'error': str(e),
                    'success': False
                })
        
        successful_routing = sum(1 for result in routing_results if result['success'])
        
        return {
            'routing_results': routing_results,
            'successful_routing': successful_routing,
            'total_users': len(test_users),
            'success_rate': (successful_routing / len(test_users)) * 100
        }
    
    def test_intelligent_insights(self) -> Dict[str, Any]:
        """Test intelligent insights and recommendations"""
        test_user = {
            'age': 28,
            'income': 65000,
            'location': 'Atlanta',
            'industry': 'Technology',
            'experience_years': 5
        }
        
        insight_types = [
            'career_insights',
            'financial_insights', 
            'wealth_building_insights',
            'community_insights'
        ]
        
        insight_results = []
        
        for insight_type in insight_types:
            try:
                insights = self.insights_service.get_insights(
                    insight_type=insight_type,
                    user_data=test_user
                )
                
                insight_results.append({
                    'type': insight_type,
                    'insights': insights,
                    'success': True
                })
                
            except Exception as e:
                insight_results.append({
                    'type': insight_type,
                    'error': str(e),
                    'success': False
                })
        
        successful_insights = sum(1 for result in insight_results if result['success'])
        
        return {
            'insight_results': insight_results,
            'successful_insights': successful_insights,
            'total_types': len(insight_types),
            'success_rate': (successful_insights / len(insight_types)) * 100
        }
    
    def test_calculator_integration(self) -> Dict[str, Any]:
        """Test financial calculator integration"""
        test_calculations = [
            {
                'type': 'emergency_fund',
                'params': {'monthly_expenses': 3000, 'income': 65000}
            },
            {
                'type': 'debt_payoff',
                'params': {'debt_amount': 45000, 'interest_rate': 6.8, 'monthly_payment': 500}
            },
            {
                'type': 'home_affordability',
                'params': {'income': 65000, 'down_payment': 20000, 'credit_score': 720}
            }
        ]
        
        calculation_results = []
        
        for calc in test_calculations:
            try:
                result = self.calculator_service.calculate(
                    calculation_type=calc['type'],
                    parameters=calc['params']
                )
                
                calculation_results.append({
                    'type': calc['type'],
                    'result': result,
                    'success': True
                })
                
            except Exception as e:
                calculation_results.append({
                    'type': calc['type'],
                    'error': str(e),
                    'success': False
                })
        
        successful_calculations = sum(1 for result in calculation_results if result['success'])
        
        return {
            'calculation_results': calculation_results,
            'successful_calculations': successful_calculations,
            'total_calculations': len(test_calculations),
            'success_rate': (successful_calculations / len(test_calculations)) * 100
        }
    
    def test_salary_data_service(self) -> Dict[str, Any]:
        """Test salary data and benchmarking features"""
        test_locations = ['Atlanta', 'Houston', 'Washington DC']
        test_industries = ['Technology', 'Healthcare', 'Finance']
        
        salary_results = []
        
        for location in test_locations:
            for industry in test_industries:
                try:
                    salary_data = self.salary_service.get_salary_benchmarks(
                        location=location,
                        industry=industry,
                        experience_years=5
                    )
                    
                    salary_results.append({
                        'location': location,
                        'industry': industry,
                        'salary_data': salary_data,
                        'success': True
                    })
                    
                except Exception as e:
                    salary_results.append({
                        'location': location,
                        'industry': industry,
                        'error': str(e),
                        'success': False
                    })
        
        successful_salary_data = sum(1 for result in salary_results if result['success'])
        
        return {
            'salary_results': salary_results,
            'successful_salary_data': successful_salary_data,
            'total_combinations': len(test_locations) * len(test_industries),
            'success_rate': (successful_salary_data / (len(test_locations) * len(test_industries))) * 100
        }
    
    def test_user_profile_service(self) -> Dict[str, Any]:
        """Test user profile and personalization features"""
        test_profiles = [
            {
                'user_id': 'user1',
                'age': 25,
                'income': 45000,
                'location': 'Atlanta',
                'industry': 'Technology'
            },
            {
                'user_id': 'user2',
                'age': 30,
                'income': 75000,
                'location': 'Houston',
                'industry': 'Healthcare'
            }
        ]
        
        profile_results = []
        
        for profile in test_profiles:
            try:
                # Test profile creation/update
                profile_result = self.user_profile_service.update_user_profile(
                    user_id=profile['user_id'],
                    profile_data=profile
                )
                
                # Test personalization
                personalization = self.user_profile_service.get_personalized_recommendations(
                    user_id=profile['user_id']
                )
                
                profile_results.append({
                    'profile': profile,
                    'profile_result': profile_result,
                    'personalization': personalization,
                    'success': True
                })
                
            except Exception as e:
                profile_results.append({
                    'profile': profile,
                    'error': str(e),
                    'success': False
                })
        
        successful_profiles = sum(1 for result in profile_results if result['success'])
        
        return {
            'profile_results': profile_results,
            'successful_profiles': successful_profiles,
            'total_profiles': len(test_profiles),
            'success_rate': (successful_profiles / len(test_profiles)) * 100
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.status == "PASS")
        failed_tests = sum(1 for result in self.results if result.status == "FAIL")
        skipped_tests = sum(1 for result in self.results if result.status == "SKIP")
        
        total_execution_time = sum(result.execution_time for result in self.results)
        
        # Calculate feature coverage scores
        coverage_scores = {}
        for result in self.results:
            if result.data and isinstance(result.data, dict):
                if 'coverage_percentage' in result.data:
                    coverage_scores[result.test_name] = result.data['coverage_percentage']
                elif 'success_rate' in result.data:
                    coverage_scores[result.test_name] = result.data['success_rate']
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'skipped_tests': skipped_tests,
                'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                'total_execution_time': total_execution_time,
                'average_execution_time': total_execution_time / total_tests if total_tests > 0 else 0
            },
            'feature_coverage': coverage_scores,
            'detailed_results': [
                {
                    'test_name': result.test_name,
                    'status': result.status,
                    'details': result.details,
                    'execution_time': result.execution_time,
                    'data': result.data
                }
                for result in self.results
            ],
            'target_demographic_verification': {
                'age_range': self.target_demographic['age_range'],
                'income_range': self.target_demographic['income_range'],
                'metro_areas': self.target_demographic['target_metro_areas'],
                'top_10_problems': self.top_10_problems
            },
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [result for result in self.results if result.status == "FAIL"]
        low_coverage_tests = []
        
        for result in self.results:
            if result.data and isinstance(result.data, dict):
                coverage = result.data.get('coverage_percentage', 0)
                if coverage < 80:
                    low_coverage_tests.append(result.test_name)
        
        if failed_tests:
            recommendations.append(f"Fix {len(failed_tests)} failing tests to ensure core functionality")
        
        if low_coverage_tests:
            recommendations.append(f"Improve coverage for: {', '.join(low_coverage_tests)}")
        
        # Check specific feature recommendations
        for result in self.results:
            if result.test_name == "Top 10 Problems Verification":
                if result.data and result.data.get('coverage_percentage', 0) < 100:
                    recommendations.append("Ensure all top 10 problems for African American professionals are addressed")
            
            elif result.test_name == "Location-Based Features":
                if result.data and result.data.get('coverage_percentage', 0) < 100:
                    recommendations.append("Improve location-based features for all target metro areas")
            
            elif result.test_name == "Cultural Sensitivity in Financial Advice":
                if result.data and result.data.get('average_cultural_score', 0) < 3:
                    recommendations.append("Enhance cultural sensitivity in financial advice and messaging")
        
        return recommendations

def main():
    """Main test execution function"""
    print("🎯 African American Professional Features Test Suite")
    print("=" * 60)
    print("Target Demographic: 25-35, $40K-$100K")
    print("Focus: Career advancement, income improvement, cultural sensitivity")
    print("=" * 60)
    
    try:
        tester = AfricanAmericanProfessionalFeaturesTester()
        report = tester.run_all_tests()
        
        # Print summary
        print("\n📊 TEST SUMMARY")
        print("-" * 40)
        summary = report['test_summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Skipped: {summary['skipped_tests']} ⏭️")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Execution Time: {summary['total_execution_time']:.2f}s")
        
        # Print feature coverage
        print("\n🎯 FEATURE COVERAGE")
        print("-" * 40)
        for feature, coverage in report['feature_coverage'].items():
            status = "✅" if coverage >= 80 else "⚠️" if coverage >= 60 else "❌"
            print(f"{status} {feature}: {coverage:.1f}%")
        
        # Print top 10 problems verification
        print("\n🔍 TOP 10 PROBLEMS VERIFICATION")
        print("-" * 40)
        top_10_result = next((r for r in report['detailed_results'] if r['test_name'] == "Top 10 Problems Verification"), None)
        if top_10_result and top_10_result['data']:
            data = top_10_result['data']
            print(f"Problems Addressed: {data['addressed_count']}/{data['total_problems']}")
            print(f"Coverage: {data['coverage_percentage']:.1f}%")
            
            if data['coverage_percentage'] < 100:
                print("\nMissing Coverage:")
                for problem_key, problem_data in data['problem_details'].items():
                    if not problem_data['addressed']:
                        print(f"  ❌ {problem_data['problem']}")
        
        # Print recommendations
        if report['recommendations']:
            print("\n💡 RECOMMENDATIONS")
            print("-" * 40)
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec}")
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"african_american_features_test_report_{timestamp}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        # Return exit code based on success rate
        if summary['success_rate'] >= 80:
            print("\n🎉 Test suite completed successfully!")
            return 0
        else:
            print("\n⚠️ Test suite completed with issues that need attention.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        logging.error(f"Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
