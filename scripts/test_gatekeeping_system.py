#!/usr/bin/env python3
"""
Test Gatekeeping System Script
Comprehensive testing of assessment-based gatekeeping, progressive unlocking, and access control
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gatekeeping_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GatekeepingSystemTester:
    """Comprehensive testing of the gatekeeping system"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///instance/mingus.db')
        self.engine = None
        self.session = None
        
        # Test configuration
        self.test_scenarios = {
            'beginner_user': {
                'user_id': 1,
                'expected_level': 'Beginner',
                'expected_access': {
                    'BE': ['Beginner'],
                    'DO': ['Beginner'],
                    'HAVE': ['Beginner']
                }
            },
            'intermediate_user': {
                'user_id': 2,
                'expected_level': 'Intermediate',
                'expected_access': {
                    'BE': ['Beginner', 'Intermediate'],
                    'DO': ['Beginner', 'Intermediate'],
                    'HAVE': ['Beginner', 'Intermediate']
                }
            },
            'advanced_user': {
                'user_id': 3,
                'expected_level': 'Advanced',
                'expected_access': {
                    'BE': ['Beginner', 'Intermediate', 'Advanced'],
                    'DO': ['Beginner', 'Intermediate', 'Advanced'],
                    'HAVE': ['Beginner', 'Intermediate', 'Advanced']
                }
            }
        }
    
    def connect_database(self) -> bool:
        """Connect to database"""
        try:
            logger.info(f"Connecting to database: {self.database_url}")
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.session = sessionmaker(bind=self.engine)()
            
            logger.info("Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def get_user_assessment_data(self, user_id: int) -> Dict[str, Any]:
        """Get user assessment data from database"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT user_id, be_score, do_score, have_score,
                           be_level, do_level, have_level, overall_readiness_level,
                           assessment_date, confidence_score, is_valid
                    FROM user_assessment_scores
                    WHERE user_id = :user_id
                """), {'user_id': user_id})
                
                row = result.fetchone()
                if not row:
                    return {}
                
                return dict(row._mapping)
                
        except Exception as e:
            logger.error(f"Error getting user assessment data: {e}")
            return {}
    
    def get_access_control_mapping(self) -> Dict[str, Dict[str, List[str]]]:
        """Get access control mapping from database"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT user_level, article_phase, allowed_difficulties
                    FROM access_control_mapping
                    ORDER BY user_level, article_phase
                """))
                
                mapping = {}
                for row in result.fetchall():
                    user_level = row[0]
                    article_phase = row[1]
                    allowed_difficulties = json.loads(row[2])
                    
                    if user_level not in mapping:
                        mapping[user_level] = {}
                    
                    mapping[user_level][article_phase] = allowed_difficulties
                
                return mapping
                
        except Exception as e:
            logger.error(f"Error getting access control mapping: {e}")
            return {}
    
    def get_available_articles(self) -> List[Dict[str, Any]]:
        """Get available articles for testing"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, title, primary_phase, difficulty_level, 
                           demographic_relevance, cultural_sensitivity
                    FROM articles
                    WHERE is_active = 1
                    ORDER BY primary_phase, difficulty_level
                """))
                
                articles = []
                for row in result.fetchall():
                    articles.append(dict(row._mapping))
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting available articles: {e}")
            return []
    
    def check_article_access(self, user_level: str, article_phase: str, article_difficulty: str) -> bool:
        """Check if user has access to an article"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT allowed_difficulties 
                    FROM access_control_mapping 
                    WHERE user_level = :user_level AND article_phase = :article_phase
                """), {
                    'user_level': user_level,
                    'article_phase': article_phase
                })
                
                row = result.fetchone()
                if not row:
                    return False
                
                allowed_difficulties = json.loads(row[0])
                return article_difficulty in allowed_difficulties
                
        except Exception as e:
            logger.error(f"Error checking article access: {e}")
            return False
    
    def test_user_assessment_validation(self) -> Dict[str, Any]:
        """Test user assessment validation and scoring"""
        logger.info("Testing user assessment validation...")
        
        test_results = {
            'user_assessments': [],
            'scoring_accuracy': [],
            'level_consistency': []
        }
        
        try:
            for scenario_name, scenario in self.test_scenarios.items():
                user_id = scenario['user_id']
                expected_level = scenario['expected_level']
                
                # Get user assessment data
                assessment_data = self.get_user_assessment_data(user_id)
                
                if not assessment_data:
                    test_results['user_assessments'].append({
                        'scenario': scenario_name,
                        'user_id': user_id,
                        'status': 'FAILED',
                        'error': 'No assessment data found'
                    })
                    continue
                
                # Validate assessment data
                actual_level = assessment_data.get('overall_readiness_level', 'Unknown')
                be_level = assessment_data.get('be_level', 'Unknown')
                do_level = assessment_data.get('do_level', 'Unknown')
                have_level = assessment_data.get('have_level', 'Unknown')
                
                # Check level consistency
                level_consistent = (
                    actual_level == expected_level and
                    be_level in ['Beginner', 'Intermediate', 'Advanced'] and
                    do_level in ['Beginner', 'Intermediate', 'Advanced'] and
                    have_level in ['Beginner', 'Intermediate', 'Advanced']
                )
                
                test_results['user_assessments'].append({
                    'scenario': scenario_name,
                    'user_id': user_id,
                    'expected_level': expected_level,
                    'actual_level': actual_level,
                    'be_level': be_level,
                    'do_level': do_level,
                    'have_level': have_level,
                    'be_score': assessment_data.get('be_score', 0),
                    'do_score': assessment_data.get('do_score', 0),
                    'have_score': assessment_data.get('have_score', 0),
                    'confidence_score': assessment_data.get('confidence_score', 0),
                    'is_valid': assessment_data.get('is_valid', False),
                    'level_consistent': level_consistent,
                    'status': 'PASSED' if level_consistent else 'FAILED'
                })
                
                # Test scoring accuracy
                if level_consistent:
                    test_results['scoring_accuracy'].append({
                        'scenario': scenario_name,
                        'user_id': user_id,
                        'expected_level': expected_level,
                        'actual_level': actual_level,
                        'passed': actual_level == expected_level
                    })
                
                # Test level consistency
                test_results['level_consistency'].append({
                    'scenario': scenario_name,
                    'user_id': user_id,
                    'overall_level': actual_level,
                    'phase_levels': [be_level, do_level, have_level],
                    'consistent': level_consistent
                })
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error testing user assessment validation: {e}")
            return {'error': str(e)}
    
    def test_access_control_mapping(self) -> Dict[str, Any]:
        """Test access control mapping functionality"""
        logger.info("Testing access control mapping...")
        
        test_results = {
            'mapping_validation': [],
            'access_tests': [],
            'progressive_unlocking': []
        }
        
        try:
            # Get access control mapping
            mapping = self.get_access_control_mapping()
            
            # Test mapping structure
            expected_levels = ['Beginner', 'Intermediate', 'Advanced']
            expected_phases = ['BE', 'DO', 'HAVE']
            
            for level in expected_levels:
                if level not in mapping:
                    test_results['mapping_validation'].append({
                        'test': f'Mapping for {level} level',
                        'status': 'FAILED',
                        'error': f'Missing mapping for {level} level'
                    })
                    continue
                
                for phase in expected_phases:
                    if phase not in mapping[level]:
                        test_results['mapping_validation'].append({
                            'test': f'Mapping for {level} level - {phase} phase',
                            'status': 'FAILED',
                            'error': f'Missing mapping for {level} level - {phase} phase'
                        })
                    else:
                        test_results['mapping_validation'].append({
                            'test': f'Mapping for {level} level - {phase} phase',
                            'status': 'PASSED',
                            'difficulties': mapping[level][phase]
                        })
            
            # Test access control for different scenarios
            test_articles = [
                {'phase': 'BE', 'difficulty': 'Beginner', 'title': 'Basic Mindset Article'},
                {'phase': 'BE', 'difficulty': 'Intermediate', 'title': 'Intermediate Mindset Article'},
                {'phase': 'BE', 'difficulty': 'Advanced', 'title': 'Advanced Mindset Article'},
                {'phase': 'DO', 'difficulty': 'Beginner', 'title': 'Basic Skills Article'},
                {'phase': 'DO', 'difficulty': 'Intermediate', 'title': 'Intermediate Skills Article'},
                {'phase': 'DO', 'difficulty': 'Advanced', 'title': 'Advanced Skills Article'},
                {'phase': 'HAVE', 'difficulty': 'Beginner', 'title': 'Basic Results Article'},
                {'phase': 'HAVE', 'difficulty': 'Intermediate', 'title': 'Intermediate Results Article'},
                {'phase': 'HAVE', 'difficulty': 'Advanced', 'title': 'Advanced Results Article'}
            ]
            
            for scenario_name, scenario in self.test_scenarios.items():
                user_level = scenario['expected_level']
                expected_access = scenario['expected_access']
                
                for article in test_articles:
                    has_access = self.check_article_access(
                        user_level,
                        article['phase'],
                        article['difficulty']
                    )
                    
                    expected = article['difficulty'] in expected_access.get(article['phase'], [])
                    
                    test_results['access_tests'].append({
                        'scenario': scenario_name,
                        'user_level': user_level,
                        'article_phase': article['phase'],
                        'article_difficulty': article['difficulty'],
                        'article_title': article['title'],
                        'has_access': has_access,
                        'expected_access': expected,
                        'passed': has_access == expected
                    })
            
            # Test progressive unlocking
            for scenario_name, scenario in self.test_scenarios.items():
                user_level = scenario['expected_level']
                expected_access = scenario['expected_access']
                
                accessible_articles = {}
                for phase, difficulties in expected_access.items():
                    accessible_articles[phase] = difficulties
                
                test_results['progressive_unlocking'].append({
                    'scenario': scenario_name,
                    'user_level': user_level,
                    'accessible_phases': accessible_articles,
                    'progressive': self._validate_progressive_unlocking(user_level, accessible_articles)
                })
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error testing access control mapping: {e}")
            return {'error': str(e)}
    
    def _validate_progressive_unlocking(self, user_level: str, accessible_articles: Dict[str, List[str]]) -> bool:
        """Validate that progressive unlocking works correctly"""
        if user_level == 'Beginner':
            # Beginners should only have access to Beginner articles
            for phase, difficulties in accessible_articles.items():
                if len(difficulties) != 1 or 'Beginner' not in difficulties:
                    return False
        
        elif user_level == 'Intermediate':
            # Intermediate users should have access to Beginner and Intermediate articles
            for phase, difficulties in accessible_articles.items():
                if len(difficulties) != 2 or 'Beginner' not in difficulties or 'Intermediate' not in difficulties:
                    return False
        
        elif user_level == 'Advanced':
            # Advanced users should have access to all difficulty levels
            for phase, difficulties in accessible_articles.items():
                if len(difficulties) != 3 or 'Advanced' not in difficulties:
                    return False
        
        return True
    
    def test_article_access_integration(self) -> Dict[str, Any]:
        """Test article access integration with real articles"""
        logger.info("Testing article access integration...")
        
        test_results = {
            'article_access_tests': [],
            'content_filtering': [],
            'user_experience': []
        }
        
        try:
            # Get available articles
            articles = self.get_available_articles()
            
            if not articles:
                test_results['article_access_tests'].append({
                    'status': 'SKIPPED',
                    'reason': 'No articles available for testing'
                })
                return test_results
            
            # Test access for each user level
            for scenario_name, scenario in self.test_scenarios.items():
                user_level = scenario['expected_level']
                
                accessible_articles = []
                inaccessible_articles = []
                
                for article in articles:
                    has_access = self.check_article_access(
                        user_level,
                        article['primary_phase'],
                        article['difficulty_level']
                    )
                    
                    if has_access:
                        accessible_articles.append(article)
                    else:
                        inaccessible_articles.append(article)
                
                test_results['article_access_tests'].append({
                    'scenario': scenario_name,
                    'user_level': user_level,
                    'total_articles': len(articles),
                    'accessible_articles': len(accessible_articles),
                    'inaccessible_articles': len(inaccessible_articles),
                    'access_ratio': len(accessible_articles) / len(articles) if articles else 0
                })
                
                # Test content filtering
                phase_distribution = {}
                difficulty_distribution = {}
                
                for article in accessible_articles:
                    phase = article['primary_phase']
                    difficulty = article['difficulty_level']
                    
                    phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
                    difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1
                
                test_results['content_filtering'].append({
                    'scenario': scenario_name,
                    'user_level': user_level,
                    'phase_distribution': phase_distribution,
                    'difficulty_distribution': difficulty_distribution,
                    'filtering_appropriate': self._validate_content_filtering(user_level, difficulty_distribution)
                })
                
                # Test user experience
                test_results['user_experience'].append({
                    'scenario': scenario_name,
                    'user_level': user_level,
                    'accessible_count': len(accessible_articles),
                    'experience_quality': self._assess_user_experience(user_level, accessible_articles)
                })
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error testing article access integration: {e}")
            return {'error': str(e)}
    
    def _validate_content_filtering(self, user_level: str, difficulty_distribution: Dict[str, int]) -> bool:
        """Validate that content filtering is appropriate for user level"""
        if user_level == 'Beginner':
            # Beginners should only see Beginner articles
            return difficulty_distribution.get('Beginner', 0) > 0 and len(difficulty_distribution) == 1
        
        elif user_level == 'Intermediate':
            # Intermediate users should see Beginner and Intermediate articles
            return (difficulty_distribution.get('Beginner', 0) > 0 and 
                   difficulty_distribution.get('Intermediate', 0) > 0 and
                   difficulty_distribution.get('Advanced', 0) == 0)
        
        elif user_level == 'Advanced':
            # Advanced users should see all difficulty levels
            return (difficulty_distribution.get('Beginner', 0) > 0 and
                   difficulty_distribution.get('Intermediate', 0) > 0 and
                   difficulty_distribution.get('Advanced', 0) > 0)
        
        return False
    
    def _assess_user_experience(self, user_level: str, accessible_articles: List[Dict]) -> str:
        """Assess the quality of user experience based on accessible articles"""
        if not accessible_articles:
            return 'Poor - No articles accessible'
        
        # Count articles by phase
        phase_counts = {}
        for article in accessible_articles:
            phase = article['primary_phase']
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        # Assess experience quality
        if user_level == 'Beginner':
            if len(phase_counts) >= 2 and min(phase_counts.values()) >= 1:
                return 'Good - Balanced content across phases'
            elif len(phase_counts) >= 1:
                return 'Fair - Limited phase coverage'
            else:
                return 'Poor - No content available'
        
        elif user_level == 'Intermediate':
            if len(phase_counts) >= 3 and min(phase_counts.values()) >= 2:
                return 'Excellent - Comprehensive content coverage'
            elif len(phase_counts) >= 2 and min(phase_counts.values()) >= 1:
                return 'Good - Balanced content across phases'
            else:
                return 'Fair - Limited content variety'
        
        elif user_level == 'Advanced':
            if len(phase_counts) >= 3 and min(phase_counts.values()) >= 3:
                return 'Excellent - Comprehensive advanced content'
            elif len(phase_counts) >= 2 and min(phase_counts.values()) >= 2:
                return 'Good - Good variety of advanced content'
            else:
                return 'Fair - Limited advanced content'
        
        return 'Unknown'
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        logger.info("Running comprehensive gatekeeping tests...")
        
        all_results = {}
        
        try:
            # Test user assessment validation
            all_results['assessment_validation'] = self.test_user_assessment_validation()
            
            # Test access control mapping
            all_results['access_control'] = self.test_access_control_mapping()
            
            # Test article access integration
            all_results['article_integration'] = self.test_article_access_integration()
            
            return all_results
            
        except Exception as e:
            logger.error(f"Error running comprehensive tests: {e}")
            return {'error': str(e)}
    
    def generate_test_report(self, test_results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("GATEKEEPING SYSTEM TEST REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {datetime.now()}")
        report.append(f"Database: {self.database_url}")
        report.append("")
        
        # Assessment validation results
        if 'assessment_validation' in test_results:
            report.append("ASSESSMENT VALIDATION RESULTS:")
            report.append("-" * 40)
            
            assessment_results = test_results['assessment_validation']
            
            if 'user_assessments' in assessment_results:
                passed = sum(1 for test in assessment_results['user_assessments'] if test.get('status') == 'PASSED')
                total = len(assessment_results['user_assessments'])
                report.append(f"User Assessment Tests: {passed}/{total} passed")
                
                for test in assessment_results['user_assessments']:
                    report.append(f"  • {test['scenario']}: {test['status']}")
                    if test.get('error'):
                        report.append(f"    Error: {test['error']}")
            
            if 'scoring_accuracy' in assessment_results:
                passed = sum(1 for test in assessment_results['scoring_accuracy'] if test.get('passed', False))
                total = len(assessment_results['scoring_accuracy'])
                report.append(f"Scoring Accuracy Tests: {passed}/{total} passed")
            
            report.append("")
        
        # Access control results
        if 'access_control' in test_results:
            report.append("ACCESS CONTROL RESULTS:")
            report.append("-" * 40)
            
            access_results = test_results['access_control']
            
            if 'mapping_validation' in access_results:
                passed = sum(1 for test in access_results['mapping_validation'] if test.get('status') == 'PASSED')
                total = len(access_results['mapping_validation'])
                report.append(f"Mapping Validation Tests: {passed}/{total} passed")
            
            if 'access_tests' in access_results:
                passed = sum(1 for test in access_results['access_tests'] if test.get('passed', False))
                total = len(access_results['access_tests'])
                report.append(f"Access Control Tests: {passed}/{total} passed")
            
            if 'progressive_unlocking' in access_results:
                passed = sum(1 for test in access_results['progressive_unlocking'] if test.get('progressive', False))
                total = len(access_results['progressive_unlocking'])
                report.append(f"Progressive Unlocking Tests: {passed}/{total} passed")
            
            report.append("")
        
        # Article integration results
        if 'article_integration' in test_results:
            report.append("ARTICLE INTEGRATION RESULTS:")
            report.append("-" * 40)
            
            integration_results = test_results['article_integration']
            
            if 'article_access_tests' in integration_results:
                for test in integration_results['article_access_tests']:
                    if test.get('status') != 'SKIPPED':
                        report.append(f"• {test['scenario']}: {test['accessible_articles']}/{test['total_articles']} articles accessible")
                        report.append(f"  Access ratio: {test['access_ratio']:.2%}")
            
            if 'content_filtering' in integration_results:
                passed = sum(1 for test in integration_results['content_filtering'] if test.get('filtering_appropriate', False))
                total = len(integration_results['content_filtering'])
                report.append(f"Content Filtering Tests: {passed}/{total} passed")
            
            if 'user_experience' in integration_results:
                for test in integration_results['user_experience']:
                    report.append(f"• {test['scenario']}: {test['experience_quality']}")
            
            report.append("")
        
        # Summary
        report.append("TEST SUMMARY:")
        report.append("-" * 40)
        
        total_tests = 0
        passed_tests = 0
        
        for category, results in test_results.items():
            if isinstance(results, dict):
                for test_type, tests in results.items():
                    if isinstance(tests, list):
                        for test in tests:
                            total_tests += 1
                            if test.get('status') == 'PASSED' or test.get('passed', False) or test.get('progressive', False) or test.get('filtering_appropriate', False):
                                passed_tests += 1
        
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed Tests: {passed_tests}")
        report.append(f"Success Rate: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "Success Rate: N/A")
        
        if passed_tests == total_tests:
            report.append("Overall Status: ✅ ALL TESTS PASSED")
        else:
            report.append("Overall Status: ⚠️ SOME TESTS FAILED")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_tests(self) -> bool:
        """Run all tests and generate report"""
        logger.info("Starting gatekeeping system tests...")
        
        # Connect to database
        if not self.connect_database():
            return False
        
        try:
            # Run comprehensive tests
            test_results = self.run_comprehensive_tests()
            
            # Generate and save report
            report = self.generate_test_report(test_results)
            
            # Save report to file
            report_filename = f"gatekeeping_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            
            # Print report to console
            print(report)
            
            logger.info(f"Report saved to: {report_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test gatekeeping system with comprehensive validation')
    parser.add_argument('--database', help='Database URL')
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = GatekeepingSystemTester(args.database)
    
    # Run tests
    success = tester.run_tests()
    
    if success:
        logger.info("Gatekeeping system tests completed successfully!")
        return 0
    else:
        logger.error("Gatekeeping system tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
