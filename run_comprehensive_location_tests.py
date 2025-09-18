#!/usr/bin/env python3
"""
Comprehensive Location-Based Job Recommendation Testing Suite
Main test runner that integrates all testing frameworks
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Import all test frameworks
from test_location_recommendation_framework import LocationRecommendationTestFramework
from test_user_scenario_tests import UserScenarioTestFramework
from test_performance_tests import PerformanceTestFramework
from test_edge_case_tests import EdgeCaseTestFramework

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    """
    Main test runner that orchestrates all testing frameworks
    """
    
    def __init__(self, db_path: str = "test_location_recommendations.db"):
        self.db_path = db_path
        self.test_frameworks = {
            'location_quality': LocationRecommendationTestFramework(db_path),
            'user_scenarios': UserScenarioTestFramework(db_path),
            'performance': PerformanceTestFramework(db_path),
            'edge_cases': EdgeCaseTestFramework(db_path)
        }
        
        # Test execution order
        self.execution_order = [
            'location_quality',
            'user_scenarios', 
            'performance',
            'edge_cases'
        ]
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests"""
        logger.info("🚀 Starting Comprehensive Location-Based Job Recommendation Testing Suite")
        print("=" * 80)
        print("🎯 COMPREHENSIVE LOCATION-BASED JOB RECOMMENDATION TESTING SUITE")
        print("=" * 80)
        print(f"📅 Test Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗄️  Database: {self.db_path}")
        print("=" * 80)
        
        overall_results = {
            'start_time': datetime.now(),
            'test_suites': {},
            'overall_score': 0.0,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'execution_summary': {},
            'quality_metrics': {},
            'performance_metrics': {},
            'recommendations': []
        }
        
        try:
            # Run each test suite
            for suite_name in self.execution_order:
                logger.info(f"Running {suite_name} test suite...")
                print(f"\n🔧 Running {suite_name.replace('_', ' ').title()} Tests...")
                
                start_time = time.time()
                
                try:
                    if suite_name == 'location_quality':
                        suite_results = await self.test_frameworks[suite_name].run_comprehensive_tests()
                    elif suite_name == 'user_scenarios':
                        suite_results = await self.test_frameworks[suite_name].run_user_scenario_tests()
                    elif suite_name == 'performance':
                        suite_results = await self.test_frameworks[suite_name].run_performance_tests()
                    elif suite_name == 'edge_cases':
                        suite_results = await self.test_frameworks[suite_name].run_edge_case_tests()
                    
                    end_time = time.time()
                    suite_duration = end_time - start_time
                    
                    suite_results['execution_time'] = suite_duration
                    overall_results['test_suites'][suite_name] = suite_results
                    
                    # Print suite results
                    self._print_suite_results(suite_name, suite_results)
                    
                except Exception as e:
                    logger.error(f"Error running {suite_name} test suite: {e}")
                    overall_results['test_suites'][suite_name] = {
                        'error': str(e),
                        'execution_time': 0,
                        'overall_score': 0,
                        'total_tests': 0,
                        'passed_tests': 0
                    }
                    print(f"❌ {suite_name.replace('_', ' ').title()} Tests: FAILED - {e}")
            
            # Calculate overall results
            overall_results = self._calculate_overall_results(overall_results)
            
            # Generate quality metrics
            overall_results['quality_metrics'] = self._generate_quality_metrics(overall_results)
            
            # Generate performance metrics
            overall_results['performance_metrics'] = self._generate_performance_metrics(overall_results)
            
            # Generate recommendations
            overall_results['recommendations'] = self._generate_recommendations(overall_results)
            
        except Exception as e:
            logger.error(f"Error running comprehensive tests: {e}")
            overall_results['error'] = str(e)
        
        overall_results['end_time'] = datetime.now()
        overall_results['total_duration'] = (overall_results['end_time'] - overall_results['start_time']).total_seconds()
        
        # Print final results
        self._print_final_results(overall_results)
        
        # Save results
        self._save_results(overall_results)
        
        return overall_results
    
    def _print_suite_results(self, suite_name: str, results: Dict[str, Any]):
        """Print results for a specific test suite"""
        suite_display_name = suite_name.replace('_', ' ').title()
        
        if 'error' in results:
            print(f"❌ {suite_display_name}: FAILED - {results['error']}")
            return
        
        # Extract key metrics
        overall_score = results.get('overall_score', 0)
        total_tests = results.get('total_tests', 0)
        passed_tests = results.get('passed_tests', 0)
        execution_time = results.get('execution_time', 0)
        
        # Determine status
        if overall_score >= 90:
            status = "✅ EXCELLENT"
        elif overall_score >= 80:
            status = "✅ GOOD"
        elif overall_score >= 70:
            status = "⚠️  FAIR"
        else:
            status = "❌ POOR"
        
        print(f"{status} {suite_display_name}: {overall_score:.1f}%")
        print(f"   📊 Tests: {passed_tests}/{total_tests} passed")
        print(f"   ⏱️  Duration: {execution_time:.2f}s")
        
        # Print specific metrics for each suite
        if suite_name == 'location_quality':
            self._print_location_quality_metrics(results)
        elif suite_name == 'user_scenarios':
            self._print_user_scenario_metrics(results)
        elif suite_name == 'performance':
            self._print_performance_metrics(results)
        elif suite_name == 'edge_cases':
            self._print_edge_case_metrics(results)
    
    def _print_location_quality_metrics(self, results: Dict[str, Any]):
        """Print location quality specific metrics"""
        if 'location_quality_tests' in results:
            quality_tests = results['location_quality_tests']
            print(f"   🎯 Location Quality Tests:")
            
            for test_name, test_result in quality_tests.items():
                if isinstance(test_result, dict) and 'score' in test_result:
                    status = "✅" if test_result['score'] >= 90 else "⚠️" if test_result['score'] >= 70 else "❌"
                    print(f"      {status} {test_name}: {test_result['score']:.1f}%")
    
    def _print_user_scenario_metrics(self, results: Dict[str, Any]):
        """Print user scenario specific metrics"""
        if 'demographic_tests' in results:
            demo_tests = results['demographic_tests']
            print(f"   👥 Demographic Tests:")
            
            for test_name, test_result in demo_tests.items():
                if isinstance(test_result, dict) and 'score' in test_result:
                    status = "✅" if test_result['score'] >= 85 else "⚠️" if test_result['score'] >= 70 else "❌"
                    print(f"      {status} {test_name}: {test_result['score']:.1f}%")
    
    def _print_performance_metrics(self, results: Dict[str, Any]):
        """Print performance specific metrics"""
        if 'end_to_end_tests' in results:
            perf_tests = results['end_to_end_tests']
            print(f"   ⚡ Performance Tests:")
            
            if 'processing_time_tests' in perf_tests:
                avg_time = sum(m.execution_time for m in perf_tests['processing_time_tests']) / len(perf_tests['processing_time_tests'])
                print(f"      📈 Avg Processing Time: {avg_time:.2f}s")
            
            if 'concurrent_tests' in perf_tests:
                max_concurrent = max(m.concurrent_users for m in perf_tests['concurrent_tests'])
                print(f"      👥 Max Concurrent Users: {max_concurrent}")
    
    def _print_edge_case_metrics(self, results: Dict[str, Any]):
        """Print edge case specific metrics"""
        if 'invalid_zipcode_tests' in results:
            edge_tests = results['invalid_zipcode_tests']
            print(f"   🔍 Edge Case Tests:")
            
            for test_name, test_result in edge_tests.items():
                if isinstance(test_result, dict) and 'overall_score' in test_result:
                    status = "✅" if test_result['overall_score'] >= 80 else "⚠️" if test_result['overall_score'] >= 60 else "❌"
                    print(f"      {status} {test_name}: {test_result['overall_score']:.1f}%")
    
    def _calculate_overall_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall test results"""
        total_tests = 0
        passed_tests = 0
        total_score = 0.0
        total_execution_time = 0.0
        
        for suite_name, suite_results in results['test_suites'].items():
            if 'error' not in suite_results:
                suite_tests = suite_results.get('total_tests', 0)
                suite_passed = suite_results.get('passed_tests', 0)
                suite_score = suite_results.get('overall_score', 0)
                suite_time = suite_results.get('execution_time', 0)
                
                total_tests += suite_tests
                passed_tests += suite_passed
                total_score += suite_score
                total_execution_time += suite_time
        
        overall_score = (total_score / len(results['test_suites'])) if results['test_suites'] else 0.0
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0.0
        
        results['overall_score'] = overall_score
        results['total_tests'] = total_tests
        results['passed_tests'] = passed_tests
        results['failed_tests'] = total_tests - passed_tests
        results['pass_rate'] = pass_rate
        results['total_execution_time'] = total_execution_time
        
        return results
    
    def _generate_quality_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate quality metrics summary"""
        quality_metrics = {
            'recommendation_accuracy': 0.0,
            'location_precision': 0.0,
            'user_satisfaction': 0.0,
            'error_handling': 0.0,
            'overall_quality_score': 0.0
        }
        
        # Calculate metrics from test results
        if 'location_quality' in results['test_suites']:
            location_results = results['test_suites']['location_quality']
            quality_metrics['recommendation_accuracy'] = location_results.get('overall_score', 0)
            quality_metrics['location_precision'] = location_results.get('overall_score', 0)
        
        if 'user_scenarios' in results['test_suites']:
            user_results = results['test_suites']['user_scenarios']
            quality_metrics['user_satisfaction'] = user_results.get('overall_score', 0)
        
        if 'edge_cases' in results['test_suites']:
            edge_results = results['test_suites']['edge_cases']
            quality_metrics['error_handling'] = edge_results.get('overall_score', 0)
        
        # Calculate overall quality score
        quality_metrics['overall_quality_score'] = (
            quality_metrics['recommendation_accuracy'] * 0.3 +
            quality_metrics['location_precision'] * 0.3 +
            quality_metrics['user_satisfaction'] * 0.2 +
            quality_metrics['error_handling'] * 0.2
        )
        
        return quality_metrics
    
    def _generate_performance_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance metrics summary"""
        performance_metrics = {
            'avg_processing_time': 0.0,
            'max_concurrent_users': 0,
            'memory_efficiency': 0.0,
            'api_response_time': 0.0,
            'overall_performance_score': 0.0
        }
        
        # Calculate metrics from performance test results
        if 'performance' in results['test_suites']:
            perf_results = results['test_suites']['performance']
            performance_metrics['overall_performance_score'] = perf_results.get('overall_performance_score', 0)
            
            # Extract specific metrics if available
            if 'end_to_end_tests' in perf_results:
                end_to_end = perf_results['end_to_end_tests']
                if 'processing_time_tests' in end_to_end:
                    times = [m.execution_time for m in end_to_end['processing_time_tests']]
                    performance_metrics['avg_processing_time'] = sum(times) / len(times) if times else 0
            
            if 'concurrent_user_tests' in perf_results:
                concurrent = perf_results['concurrent_user_tests']
                if 'concurrent_tests' in concurrent:
                    max_users = max(m.concurrent_users for m in concurrent['concurrent_tests'])
                    performance_metrics['max_concurrent_users'] = max_users
        
        return performance_metrics
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Overall score recommendations
        overall_score = results.get('overall_score', 0)
        if overall_score < 70:
            recommendations.append("🚨 CRITICAL: Overall system quality is below acceptable thresholds. Immediate attention required.")
        elif overall_score < 80:
            recommendations.append("⚠️  WARNING: System quality needs improvement. Address failing tests before production deployment.")
        elif overall_score < 90:
            recommendations.append("✅ GOOD: System quality is acceptable. Consider minor improvements for optimal performance.")
        else:
            recommendations.append("🎉 EXCELLENT: System quality is excellent. Ready for production deployment.")
        
        # Specific recommendations based on test results
        for suite_name, suite_results in results['test_suites'].items():
            if 'error' in suite_results:
                recommendations.append(f"🔧 {suite_name.replace('_', ' ').title()}: Fix critical errors before proceeding.")
            elif suite_results.get('overall_score', 0) < 80:
                recommendations.append(f"📈 {suite_name.replace('_', ' ').title()}: Improve test scores to meet quality standards.")
        
        # Performance recommendations
        if 'performance' in results['test_suites']:
            perf_results = results['test_suites']['performance']
            if perf_results.get('overall_performance_score', 0) < 80:
                recommendations.append("⚡ Performance: Optimize system performance for better user experience.")
        
        # Location quality recommendations
        if 'location_quality' in results['test_suites']:
            location_results = results['test_suites']['location_quality']
            if location_results.get('overall_score', 0) < 85:
                recommendations.append("🌍 Location Services: Improve location accuracy and validation.")
        
        return recommendations
    
    def _print_final_results(self, results: Dict[str, Any]):
        """Print final comprehensive results"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Overall metrics
        overall_score = results.get('overall_score', 0)
        total_tests = results.get('total_tests', 0)
        passed_tests = results.get('passed_tests', 0)
        failed_tests = results.get('failed_tests', 0)
        pass_rate = results.get('pass_rate', 0)
        total_duration = results.get('total_duration', 0)
        
        print(f"🎯 Overall Score: {overall_score:.1f}%")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
        
        # Quality metrics
        if 'quality_metrics' in results:
            quality = results['quality_metrics']
            print(f"\n🏆 QUALITY METRICS:")
            print(f"   🎯 Recommendation Accuracy: {quality.get('recommendation_accuracy', 0):.1f}%")
            print(f"   🌍 Location Precision: {quality.get('location_precision', 0):.1f}%")
            print(f"   👥 User Satisfaction: {quality.get('user_satisfaction', 0):.1f}%")
            print(f"   🛡️  Error Handling: {quality.get('error_handling', 0):.1f}%")
            print(f"   🏅 Overall Quality: {quality.get('overall_quality_score', 0):.1f}%")
        
        # Performance metrics
        if 'performance_metrics' in results:
            performance = results['performance_metrics']
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"   ⏱️  Avg Processing Time: {performance.get('avg_processing_time', 0):.2f}s")
            print(f"   👥 Max Concurrent Users: {performance.get('max_concurrent_users', 0)}")
            print(f"   💾 Memory Efficiency: {performance.get('memory_efficiency', 0):.1f}%")
            print(f"   🌐 API Response Time: {performance.get('api_response_time', 0):.2f}s")
            print(f"   🏅 Overall Performance: {performance.get('overall_performance_score', 0):.1f}%")
        
        # Recommendations
        if 'recommendations' in results and results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, recommendation in enumerate(results['recommendations'], 1):
                print(f"   {i}. {recommendation}")
        
        print("=" * 80)
        print(f"📅 Test Execution Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def _save_results(self, results: Dict[str, Any]):
        """Save results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_location_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
            print(f"\n❌ Error saving results: {e}")

async def main():
    """Main entry point for comprehensive testing"""
    print("🚀 Starting Comprehensive Location-Based Job Recommendation Testing Suite")
    
    # Initialize test runner
    test_runner = ComprehensiveTestRunner()
    
    # Run all tests
    results = await test_runner.run_all_tests()
    
    # Return exit code based on results
    overall_score = results.get('overall_score', 0)
    if overall_score >= 90:
        print("\n🎉 All tests passed with excellent scores!")
        return 0
    elif overall_score >= 80:
        print("\n✅ Tests passed with good scores!")
        return 0
    elif overall_score >= 70:
        print("\n⚠️  Tests passed with fair scores. Consider improvements.")
        return 1
    else:
        print("\n❌ Tests failed or scored poorly. Immediate attention required.")
        return 2

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
