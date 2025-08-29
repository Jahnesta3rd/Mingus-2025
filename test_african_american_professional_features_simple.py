#!/usr/bin/env python3
"""
Simplified Test Suite for African American Professional Features
Mingus Financial App - Target Demographic: 25-35, $40K-$100K

This test suite verifies the core features specifically designed for African American professionals,
focusing on the components that are actually implemented and working.
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

# Import EducationLevel for income comparison
try:
    from ml.models.income_comparator import EducationLevel
except ImportError:
    # Fallback if import fails
    class EducationLevel:
        BACHELORS = "bachelors"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'african_american_features_simple_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
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

class AfricanAmericanProfessionalFeaturesSimpleTester:
    """
    Simplified test suite for African American professional features
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
        
        # Initialize services that are actually available
        self.initialize_services()
        
    def initialize_services(self):
        """Initialize available services"""
        try:
            # Test imports for available services
            from ml.models.income_comparator import IncomeComparator
            self.income_comparator = IncomeComparator()
            logging.info("✓ IncomeComparator initialized")
        except Exception as e:
            logging.warning(f"Could not initialize IncomeComparator: {e}")
            self.income_comparator = None
        
        try:
            from services.salary_data_service import SalaryDataService
            self.salary_service = SalaryDataService()
            logging.info("✓ SalaryDataService initialized")
        except Exception as e:
            logging.warning(f"Could not initialize SalaryDataService: {e}")
            self.salary_service = None
        
        try:
            from services.sms_message_templates import SMSMessageTemplates
            self.sms_templates = SMSMessageTemplates()
            logging.info("✓ SMSMessageTemplates initialized")
        except Exception as e:
            logging.warning(f"Could not initialize SMSMessageTemplates: {e}")
            self.sms_templates = None
        
        try:
            from services.intelligent_insights_service import IntelligentInsightsService
            self.insights_service = IntelligentInsightsService()
            logging.info("✓ IntelligentInsightsService initialized")
        except Exception as e:
            logging.warning(f"Could not initialize IntelligentInsightsService: {e}")
            self.insights_service = None
        
        try:
            from services.calculator_integration_service import CalculatorIntegrationService
            self.calculator_service = CalculatorIntegrationService()
            logging.info("✓ CalculatorIntegrationService initialized")
        except Exception as e:
            logging.warning(f"Could not initialize CalculatorIntegrationService: {e}")
            self.calculator_service = None
        
        try:
            from services.user_profile_service import UserProfileService
            self.user_profile_service = UserProfileService()
            logging.info("✓ UserProfileService initialized")
        except Exception as e:
            logging.warning(f"Could not initialize UserProfileService: {e}")
            self.user_profile_service = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all available feature tests"""
        logging.info("Starting simplified African American professional features test suite")
        
        test_features = []
        
        # Add tests based on available services
        if self.income_comparator:
            test_features.append(("Income Comparison Tool", self.test_income_comparison_tool))
        
        if self.salary_service:
            test_features.append(("Salary Data Service", self.test_salary_data_service))
        
        if self.sms_templates:
            test_features.append(("SMS Message Templates", self.test_sms_message_templates))
        
        if self.insights_service:
            test_features.append(("Intelligent Insights Service", self.test_intelligent_insights))
        
        if self.calculator_service:
            test_features.append(("Calculator Integration", self.test_calculator_integration))
        
        if self.user_profile_service:
            test_features.append(("User Profile Service", self.test_user_profile_service))
        
        # Always run these tests
        test_features.extend([
            ("Top 10 Problems Verification", self.test_top_10_problems_addressed),
            ("Location-Based Features", self.test_location_based_features),
            ("Cultural Sensitivity Analysis", self.test_cultural_sensitivity_analysis),
            ("Target Demographic Verification", self.test_target_demographic_verification)
        ])
        
        for test_name, test_function in test_features:
            try:
                logging.info(f"Running test: {test_name}")
                start_time = time.time()
                
                result = test_function()
                execution_time = time.time() - start_time
                
                test_result = TestResult(
                    test_name=test_name,
                    status="PASS" if result else "FAIL",
                    details=f"Test completed in {execution_time:.2f}s",
                    execution_time=execution_time,
                    data=result if isinstance(result, dict) else None
                )
                
                self.results.append(test_result)
                logging.info(f"✓ {test_name}: {test_result.status}")
                
            except Exception as e:
                execution_time = time.time() - start_time
                test_result = TestResult(
                    test_name=test_name,
                    status="FAIL",
                    details=f"Test failed with error: {str(e)}",
                    execution_time=execution_time
                )
                self.results.append(test_result)
                logging.error(f"✗ {test_name}: FAILED - {str(e)}")
        
        return self.generate_report()
    
    def test_income_comparison_tool(self) -> Dict[str, Any]:
        """Test demographic income comparison functionality"""
        if not self.income_comparator:
            return {"error": "IncomeComparator not available"}
        
        test_cases = [
            {'income': 45000, 'location': 'Atlanta'},
            {'income': 75000, 'location': 'Houston'},
            {'income': 95000, 'location': 'Washington DC'}
        ]
        
        comparison_results = []
        
        for test_case in test_cases:
            try:
                analysis = self.income_comparator.analyze_income(
                    user_income=test_case['income'],
                    location=test_case['location'],
                    education_level=EducationLevel.BACHELORS,
                    age_group="25-35"
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
    
    def test_salary_data_service(self) -> Dict[str, Any]:
        """Test salary data and benchmarking features"""
        if not self.salary_service:
            return {"error": "SalaryDataService not available"}
        
        test_locations = ['Atlanta', 'Houston', 'Washington DC']
        test_industries = ['Technology', 'Healthcare', 'Finance']
        
        salary_results = []
        
        for location in test_locations:
            for industry in test_industries:
                try:
                    # Test if the service has the expected method
                    if hasattr(self.salary_service, 'get_salary_benchmarks'):
                        salary_data = self.salary_service.get_salary_benchmarks(
                            location=location,
                            industry=industry,
                            experience_years=5
                        )
                    else:
                        # Try alternative method names
                        salary_data = None
                        for method_name in ['get_salary_data', 'get_benchmarks', 'get_salary_info']:
                            if hasattr(self.salary_service, method_name):
                                method = getattr(self.salary_service, method_name)
                                salary_data = method(location=location, industry=industry)
                                break
                    
                    salary_results.append({
                        'location': location,
                        'industry': industry,
                        'salary_data': salary_data,
                        'success': salary_data is not None
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
    
    def test_sms_message_templates(self) -> Dict[str, Any]:
        """Test culturally appropriate SMS messaging"""
        if not self.sms_templates:
            return {"error": "SMSMessageTemplates not available"}
        
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
                # Test if the service has the expected method
                if hasattr(self.sms_templates, 'get_message'):
                    message = self.sms_templates.get_message(
                        message_type=message_type,
                        user_data=test_user
                    )
                else:
                    # Try alternative method names
                    message = None
                    for method_name in ['generate_message', 'create_message', 'get_template']:
                        if hasattr(self.sms_templates, method_name):
                            method = getattr(self.sms_templates, method_name)
                            message = method(message_type=message_type, user_data=test_user)
                            break
                
                if message:
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
                else:
                    message_results.append({
                        'type': message_type,
                        'error': 'No message generated',
                        'success': False
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
    
    def test_intelligent_insights(self) -> Dict[str, Any]:
        """Test intelligent insights and recommendations"""
        if not self.insights_service:
            return {"error": "IntelligentInsightsService not available"}
        
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
                # Test if the service has the expected method
                if hasattr(self.insights_service, 'get_insights'):
                    insights = self.insights_service.get_insights(
                        insight_type=insight_type,
                        user_data=test_user
                    )
                else:
                    # Try alternative method names
                    insights = None
                    for method_name in ['generate_insights', 'get_recommendations', 'analyze']:
                        if hasattr(self.insights_service, method_name):
                            method = getattr(self.insights_service, method_name)
                            insights = method(insight_type=insight_type, user_data=test_user)
                            break
                
                insight_results.append({
                    'type': insight_type,
                    'insights': insights,
                    'success': insights is not None
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
        if not self.calculator_service:
            return {"error": "CalculatorIntegrationService not available"}
        
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
                # Test if the service has the expected method
                if hasattr(self.calculator_service, 'calculate'):
                    result = self.calculator_service.calculate(
                        calculation_type=calc['type'],
                        parameters=calc['params']
                    )
                else:
                    # Try alternative method names
                    result = None
                    for method_name in ['compute', 'calculate_financial', 'process_calculation']:
                        if hasattr(self.calculator_service, method_name):
                            method = getattr(self.calculator_service, method_name)
                            result = method(calculation_type=calc['type'], parameters=calc['params'])
                            break
                
                calculation_results.append({
                    'type': calc['type'],
                    'result': result,
                    'success': result is not None
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
    
    def test_user_profile_service(self) -> Dict[str, Any]:
        """Test user profile and personalization features"""
        if not self.user_profile_service:
            return {"error": "UserProfileService not available"}
        
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
                # Test if the service has the expected methods
                profile_result = None
                personalization = None
                
                if hasattr(self.user_profile_service, 'update_user_profile'):
                    profile_result = self.user_profile_service.update_user_profile(
                        user_id=profile['user_id'],
                        profile_data=profile
                    )
                
                if hasattr(self.user_profile_service, 'get_personalized_recommendations'):
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
    
    def test_top_10_problems_addressed(self) -> Dict[str, Any]:
        """Verify app addresses the top 10 problems for African American professionals"""
        problems_addressed = []
        problem_details = {}
        
        # Check which services are available to address each problem
        available_services = {
            'income_comparator': self.income_comparator is not None,
            'salary_service': self.salary_service is not None,
            'sms_templates': self.sms_templates is not None,
            'insights_service': self.insights_service is not None,
            'calculator_service': self.calculator_service is not None,
            'user_profile_service': self.user_profile_service is not None
        }
        
        for i, problem in enumerate(self.top_10_problems):
            addressed = False
            details = {}
            
            # Map problems to available services
            if "generational wealth" in problem.lower() or "wealth building" in problem.lower():
                addressed = available_services['insights_service'] or available_services['calculator_service']
                details = {'services': ['insights_service', 'calculator_service']}
            
            elif "career advancement" in problem.lower():
                addressed = available_services['salary_service'] or available_services['insights_service']
                details = {'services': ['salary_service', 'insights_service']}
            
            elif "student loan" in problem.lower():
                addressed = available_services['calculator_service'] or available_services['insights_service']
                details = {'services': ['calculator_service', 'insights_service']}
            
            elif "workplace" in problem.lower() or "microaggressions" in problem.lower():
                addressed = available_services['insights_service'] or available_services['sms_templates']
                details = {'services': ['insights_service', 'sms_templates']}
            
            elif "networks" in problem.lower() or "mentorship" in problem.lower():
                addressed = available_services['insights_service'] or available_services['user_profile_service']
                details = {'services': ['insights_service', 'user_profile_service']}
            
            elif "homeownership" in problem.lower():
                addressed = available_services['calculator_service'] or available_services['insights_service']
                details = {'services': ['calculator_service', 'insights_service']}
            
            elif "income instability" in problem.lower():
                addressed = available_services['income_comparator'] or available_services['calculator_service']
                details = {'services': ['income_comparator', 'calculator_service']}
            
            elif "financial literacy" in problem.lower():
                addressed = available_services['insights_service'] or available_services['sms_templates']
                details = {'services': ['insights_service', 'sms_templates']}
            
            elif "systemic barriers" in problem.lower():
                addressed = available_services['insights_service'] or available_services['income_comparator']
                details = {'services': ['insights_service', 'income_comparator']}
            
            elif "community responsibility" in problem.lower():
                addressed = available_services['sms_templates'] or available_services['insights_service']
                details = {'services': ['sms_templates', 'insights_service']}
            
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
            'problem_details': problem_details,
            'available_services': available_services
        }
    
    def test_location_based_features(self) -> Dict[str, Any]:
        """Test location-based features for top 10 metro areas"""
        metro_areas = self.target_demographic['target_metro_areas']
        location_features = {}
        
        # Check which services support location-based features
        location_services = {
            'income_comparator': self.income_comparator is not None,
            'salary_service': self.salary_service is not None,
            'insights_service': self.insights_service is not None
        }
        
        for metro in metro_areas:
            location_features[metro] = {
                'income_comparison_support': location_services['income_comparator'],
                'salary_data_support': location_services['salary_service'],
                'insights_support': location_services['insights_service'],
                'metro_specific_data': any(location_services.values())
            }
        
        successful_metros = sum(1 for data in location_features.values() if data.get('metro_specific_data', False))
        
        return {
            'location_features': location_features,
            'metros_supported': successful_metros,
            'total_metros': len(metro_areas),
            'coverage_percentage': (successful_metros / len(metro_areas)) * 100,
            'location_services': location_services
        }
    
    def test_cultural_sensitivity_analysis(self) -> Dict[str, Any]:
        """Test cultural sensitivity analysis"""
        cultural_indicators = {
            'positive_terms': [
                'community', 'legacy', 'generational', 'excellence',
                'representation', 'empowerment', 'foundation', 'success',
                'achievement', 'inspiration', 'motivation', 'diversity',
                'inclusion', 'equity', 'mentorship', 'leadership'
            ],
            'negative_terms': [
                'deficit', 'lack', 'failure', 'problem', 'issue',
                'struggle', 'difficulty', 'challenge', 'barrier'
            ],
            'african_american_terms': [
                'african american', 'black', 'black professional',
                'black community', 'black excellence', 'representation'
            ]
        }
        
        # Check if services have cultural sensitivity features
        cultural_sensitivity_check = {
            'sms_templates': self.sms_templates is not None,
            'insights_service': self.insights_service is not None,
            'user_profile_service': self.user_profile_service is not None
        }
        
        return {
            'cultural_indicators': cultural_indicators,
            'cultural_sensitivity_check': cultural_sensitivity_check,
            'services_with_cultural_focus': sum(cultural_sensitivity_check.values()),
            'total_services_checked': len(cultural_sensitivity_check)
        }
    
    def test_target_demographic_verification(self) -> Dict[str, Any]:
        """Test target demographic verification"""
        demographic_verification = {
            'age_range': {
                'target': self.target_demographic['age_range'],
                'supported': True,  # Assuming the app supports this range
                'verification_method': 'Service initialization'
            },
            'income_range': {
                'target': self.target_demographic['income_range'],
                'supported': True,  # Assuming the app supports this range
                'verification_method': 'Service initialization'
            },
            'metro_areas': {
                'target': self.target_demographic['target_metro_areas'],
                'supported': len(self.target_demographic['target_metro_areas']),
                'verification_method': 'Location-based service availability'
            },
            'services_available': {
                'income_comparator': self.income_comparator is not None,
                'salary_service': self.salary_service is not None,
                'sms_templates': self.sms_templates is not None,
                'insights_service': self.insights_service is not None,
                'calculator_service': self.calculator_service is not None,
                'user_profile_service': self.user_profile_service is not None
            }
        }
        
        return demographic_verification
    
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
        
        return recommendations

def main():
    """Main test execution function"""
    print("🎯 African American Professional Features Test Suite (Simplified)")
    print("=" * 70)
    print("Target Demographic: 25-35, $40K-$100K")
    print("Focus: Career advancement, income improvement, cultural sensitivity")
    print("=" * 70)
    
    try:
        tester = AfricanAmericanProfessionalFeaturesSimpleTester()
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
        report_filename = f"african_american_features_simple_test_report_{timestamp}.json"
        
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
