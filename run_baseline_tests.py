#!/usr/bin/env python3
"""
Mingus Application - Baseline Testing Suite Runner
================================================

Main test runner that orchestrates all baseline measurements including
performance, UX, E2E, visual regression, and accessibility testing.

Author: Mingus QA Team
Date: January 2025
"""

import sys
import os
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import subprocess
import concurrent.futures
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('baseline_testing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaselineTestRunner:
    """Main baseline test runner"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = {}
        self.lock = Lock()
        
        # Create output directories
        self.create_directories()
        
        # Initialize test modules
        self.init_test_modules()
    
    def create_directories(self):
        """Create necessary output directories"""
        directories = [
            'test_results',
            'screenshots',
            'visual_test_screenshots',
            'visual_baselines',
            'reports',
            'logs'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def init_test_modules(self):
        """Initialize test modules"""
        self.test_modules = {
            'performance': {
                'module': 'monitoring.performance_monitor',
                'class': 'PerformanceMonitor',
                'enabled': self.config.get('performance', {}).get('enabled', True)
            },
            'ux': {
                'module': 'monitoring.ux_monitor',
                'class': 'UXMonitor',
                'enabled': self.config.get('ux', {}).get('enabled', True)
            },
            'e2e': {
                'module': 'tests.e2e.critical_workflows_test',
                'class': 'CriticalWorkflowsTest',
                'enabled': self.config.get('e2e', {}).get('enabled', True)
            },
            'visual': {
                'module': 'tests.visual.visual_regression_test',
                'class': 'VisualRegressionTest',
                'enabled': self.config.get('visual', {}).get('enabled', True)
            },
            'accessibility': {
                'module': 'tests.accessibility.accessibility_test',
                'class': 'AccessibilityTest',
                'enabled': self.config.get('accessibility', {}).get('enabled', True)
            }
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance monitoring tests"""
        logger.info("Starting performance tests...")
        
        try:
            from monitoring.performance_monitor import PerformanceMonitor
            
            config = self.config.get('performance', {})
            monitor = PerformanceMonitor(config)
            
            # Run comprehensive performance measurement
            results = monitor.run_comprehensive_measurement()
            
            # Export baseline report
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"reports/performance_baseline_{timestamp}.json"
            monitor.export_baseline_report(report_path)
            
            logger.info("Performance tests completed")
            return {
                'status': 'COMPLETED',
                'results': results,
                'report_path': report_path
            }
            
        except Exception as e:
            logger.error(f"Performance tests failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def run_ux_tests(self) -> Dict[str, Any]:
        """Run UX monitoring tests"""
        logger.info("Starting UX tests...")
        
        try:
            from monitoring.ux_monitor import UXMonitor
            
            config = self.config.get('ux', {})
            monitor = UXMonitor(config)
            
            # Run comprehensive UX measurement
            results = monitor.run_comprehensive_ux_measurement()
            
            # Export UX report
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"reports/ux_baseline_{timestamp}.json"
            monitor.export_ux_report(report_path)
            
            logger.info("UX tests completed")
            return {
                'status': 'COMPLETED',
                'results': results,
                'report_path': report_path
            }
            
        except Exception as e:
            logger.error(f"UX tests failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run E2E tests"""
        logger.info("Starting E2E tests...")
        
        try:
            from tests.e2e.critical_workflows_test import CriticalWorkflowsTest
            
            config = self.config.get('e2e', {})
            test_suite = CriticalWorkflowsTest(config)
            
            # Run all E2E tests
            results = test_suite.run_all_tests()
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"reports/e2e_baseline_{timestamp}.json"
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info("E2E tests completed")
            return {
                'status': 'COMPLETED',
                'results': results,
                'report_path': report_path
            }
            
        except Exception as e:
            logger.error(f"E2E tests failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def run_visual_tests(self) -> Dict[str, Any]:
        """Run visual regression tests"""
        logger.info("Starting visual regression tests...")
        
        try:
            from tests.visual.visual_regression_test import VisualRegressionTest
            
            config = self.config.get('visual', {})
            test_suite = VisualRegressionTest(config)
            
            # Run all visual tests
            results = test_suite.run_all_visual_tests()
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"reports/visual_baseline_{timestamp}.json"
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Generate visual report
            visual_report_path = f"reports/visual_report_{timestamp}.md"
            test_suite.generate_visual_report(results, visual_report_path)
            
            logger.info("Visual regression tests completed")
            return {
                'status': 'COMPLETED',
                'results': results,
                'report_path': report_path,
                'visual_report_path': visual_report_path
            }
            
        except Exception as e:
            logger.error(f"Visual regression tests failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def run_accessibility_tests(self) -> Dict[str, Any]:
        """Run accessibility tests"""
        logger.info("Starting accessibility tests...")
        
        try:
            from tests.accessibility.accessibility_test import AccessibilityTest
            
            config = self.config.get('accessibility', {})
            test_suite = AccessibilityTest(config)
            
            # Run comprehensive accessibility tests
            results = test_suite.run_comprehensive_accessibility_tests()
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = f"reports/accessibility_baseline_{timestamp}.json"
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Generate accessibility report
            accessibility_report_path = f"reports/accessibility_report_{timestamp}.md"
            test_suite.generate_accessibility_report(results, accessibility_report_path)
            
            logger.info("Accessibility tests completed")
            return {
                'status': 'COMPLETED',
                'results': results,
                'report_path': report_path,
                'accessibility_report_path': accessibility_report_path
            }
            
        except Exception as e:
            logger.error(f"Accessibility tests failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def run_tests_parallel(self, test_types: List[str]) -> Dict[str, Any]:
        """Run tests in parallel"""
        logger.info(f"Running tests in parallel: {test_types}")
        
        test_functions = {
            'performance': self.run_performance_tests,
            'ux': self.run_ux_tests,
            'e2e': self.run_e2e_tests,
            'visual': self.run_visual_tests,
            'accessibility': self.run_accessibility_tests
        }
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tests
            future_to_test = {
                executor.submit(test_functions[test_type]): test_type 
                for test_type in test_types 
                if test_type in test_functions and self.test_modules[test_type]['enabled']
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_test):
                test_type = future_to_test[future]
                try:
                    result = future.result()
                    results[test_type] = result
                    logger.info(f"{test_type} test completed: {result['status']}")
                except Exception as e:
                    logger.error(f"{test_type} test failed: {e}")
                    results[test_type] = {
                        'status': 'FAILED',
                        'error': str(e)
                    }
        
        return results
    
    def run_tests_sequential(self, test_types: List[str]) -> Dict[str, Any]:
        """Run tests sequentially"""
        logger.info(f"Running tests sequentially: {test_types}")
        
        test_functions = {
            'performance': self.run_performance_tests,
            'ux': self.run_ux_tests,
            'e2e': self.run_e2e_tests,
            'visual': self.run_visual_tests,
            'accessibility': self.run_accessibility_tests
        }
        
        results = {}
        
        for test_type in test_types:
            if test_type in test_functions and self.test_modules[test_type]['enabled']:
                logger.info(f"Running {test_type} tests...")
                try:
                    result = test_functions[test_type]()
                    results[test_type] = result
                    logger.info(f"{test_type} test completed: {result['status']}")
                except Exception as e:
                    logger.error(f"{test_type} test failed: {e}")
                    results[test_type] = {
                        'status': 'FAILED',
                        'error': str(e)
                    }
            else:
                logger.warning(f"Skipping {test_type} test (disabled or not found)")
        
        return results
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive baseline report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"reports/comprehensive_baseline_report_{timestamp}.md"
        
        # Calculate overall statistics
        total_tests = len(results)
        completed_tests = len([r for r in results.values() if r.get('status') == 'COMPLETED'])
        failed_tests = len([r for r in results.values() if r.get('status') == 'FAILED'])
        success_rate = (completed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Extract key metrics
        performance_score = 0
        ux_score = 0
        e2e_success_rate = 0
        visual_success_rate = 0
        accessibility_score = 0
        
        if 'performance' in results and results['performance'].get('status') == 'COMPLETED':
            perf_results = results['performance']['results']
            performance_score = perf_results.get('overall_stats', {}).get('overall_score', 0)
        
        if 'ux' in results and results['ux'].get('status') == 'COMPLETED':
            ux_results = results['ux']['results']
            ux_score = ux_results.get('overall_ux_score', 0)
        
        if 'e2e' in results and results['e2e'].get('status') == 'COMPLETED':
            e2e_results = results['e2e']['results']
            e2e_success_rate = e2e_results.get('summary', {}).get('success_rate', 0)
        
        if 'visual' in results and results['visual'].get('status') == 'COMPLETED':
            visual_results = results['visual']['results']
            visual_success_rate = visual_results.get('summary', {}).get('success_rate', 0)
        
        if 'accessibility' in results and results['accessibility'].get('status') == 'COMPLETED':
            a11y_results = results['accessibility']['results']
            accessibility_score = a11y_results.get('summary', {}).get('overall_score', 0)
        
        # Generate report
        report = f"""# Mingus Application - Comprehensive Baseline Report

**Generated**: {datetime.now().isoformat()}
**Overall Success Rate**: {success_rate:.1f}%

## Executive Summary

This comprehensive baseline report covers all aspects of the Mingus Personal Finance Application including performance, user experience, functionality, and accessibility.

### Overall Statistics

- **Total Test Suites**: {total_tests}
- **Completed Successfully**: {completed_tests}
- **Failed**: {failed_tests}
- **Success Rate**: {success_rate:.1f}%

### Key Metrics

| Metric | Score | Status |
|--------|-------|--------|
| Performance Score | {performance_score:.1f}/100 | {'✅ PASS' if performance_score >= 80 else '❌ FAIL'} |
| UX Score | {ux_score:.1f}/100 | {'✅ PASS' if ux_score >= 80 else '❌ FAIL'} |
| E2E Success Rate | {e2e_success_rate:.1f}% | {'✅ PASS' if e2e_success_rate >= 90 else '❌ FAIL'} |
| Visual Regression | {visual_success_rate:.1f}% | {'✅ PASS' if visual_success_rate >= 95 else '❌ FAIL'} |
| Accessibility Score | {accessibility_score:.1f}/100 | {'✅ PASS' if accessibility_score >= 90 else '❌ FAIL'} |

## Detailed Results

"""
        
        # Add detailed results for each test type
        for test_type, result in results.items():
            report += f"### {test_type.replace('_', ' ').title()} Tests\n\n"
            report += f"**Status**: {result.get('status', 'UNKNOWN')}\n\n"
            
            if result.get('status') == 'COMPLETED':
                if test_type == 'performance':
                    perf_results = result['results']
                    report += f"- **Overall Score**: {perf_results.get('overall_stats', {}).get('overall_score', 0):.1f}/100\n"
                    report += f"- **API Performance**: {perf_results.get('overall_stats', {}).get('api_score', 0):.1f}%\n"
                    report += f"- **Database Performance**: {perf_results.get('overall_stats', {}).get('db_score', 0):.1f}%\n"
                    report += f"- **Load Test Performance**: {perf_results.get('overall_stats', {}).get('load_score', 0):.1f}%\n"
                    report += f"- **Security Performance**: {perf_results.get('overall_stats', {}).get('security_score', 0):.1f}%\n"
                
                elif test_type == 'ux':
                    ux_results = result['results']
                    report += f"- **Overall UX Score**: {ux_results.get('overall_ux_score', 0):.1f}/100\n"
                    report += f"- **Task Success Rate**: {ux_results.get('task_completion', {}).get('success_rate', 0):.1f}%\n"
                    report += f"- **Interaction Efficiency**: {ux_results.get('interaction_efficiency', {}).get('efficiency_score', 0):.1f}/100\n"
                    report += f"- **Accessibility Compliance**: {ux_results.get('accessibility', {}).get('compliance_score', 0):.1f}/100\n"
                
                elif test_type == 'e2e':
                    e2e_results = result['results']
                    report += f"- **Success Rate**: {e2e_results.get('summary', {}).get('success_rate', 0):.1f}%\n"
                    report += f"- **Total Tests**: {e2e_results.get('summary', {}).get('total', 0)}\n"
                    report += f"- **Passed**: {e2e_results.get('summary', {}).get('passed', 0)}\n"
                    report += f"- **Failed**: {e2e_results.get('summary', {}).get('failed', 0)}\n"
                
                elif test_type == 'visual':
                    visual_results = result['results']
                    report += f"- **Success Rate**: {visual_results.get('summary', {}).get('success_rate', 0):.1f}%\n"
                    report += f"- **Total Tests**: {visual_results.get('summary', {}).get('total', 0)}\n"
                    report += f"- **Passed**: {visual_results.get('summary', {}).get('passed', 0)}\n"
                    report += f"- **Failed**: {visual_results.get('summary', {}).get('failed', 0)}\n"
                    report += f"- **Baseline Created**: {visual_results.get('summary', {}).get('baseline_created', 0)}\n"
                
                elif test_type == 'accessibility':
                    a11y_results = result['results']
                    report += f"- **Overall Score**: {a11y_results.get('summary', {}).get('overall_score', 0):.1f}/100\n"
                    report += f"- **Total Pages**: {a11y_results.get('summary', {}).get('total_pages', 0)}\n"
                    report += f"- **Pages Passed**: {a11y_results.get('summary', {}).get('pages_passed', 0)}\n"
                    report += f"- **Pages Failed**: {a11y_results.get('summary', {}).get('pages_failed', 0)}\n"
                
                if 'report_path' in result:
                    report += f"- **Detailed Report**: {result['report_path']}\n"
            
            elif result.get('status') == 'FAILED':
                report += f"- **Error**: {result.get('error', 'Unknown error')}\n"
            
            report += "\n"
        
        # Add recommendations
        report += """## Recommendations

Based on the baseline measurements, here are the key recommendations:

### Performance Optimization
- Monitor API response times and optimize slow endpoints
- Implement caching strategies for frequently accessed data
- Optimize database queries and add appropriate indexes
- Consider CDN implementation for static assets

### User Experience Enhancement
- Improve task completion rates through better UX design
- Optimize interaction efficiency by reducing required clicks
- Enhance mobile responsiveness and touch interactions
- Implement better error handling and user feedback

### Visual Consistency
- Establish visual regression testing in CI/CD pipeline
- Create comprehensive baseline images for all components
- Implement automated visual testing for all breakpoints
- Regular visual audits to maintain design consistency

### Accessibility Compliance
- Address critical and serious accessibility violations
- Implement proper ARIA labels and semantic HTML
- Ensure keyboard navigation works for all interactive elements
- Regular accessibility audits and user testing

### Continuous Monitoring
- Set up automated baseline measurements
- Implement alerting for performance degradation
- Regular testing of critical user workflows
- Continuous accessibility compliance monitoring

## Next Steps

1. **Address Critical Issues**: Fix any critical performance, UX, or accessibility issues
2. **Implement Monitoring**: Set up continuous monitoring and alerting
3. **Establish Baselines**: Use these measurements as baseline for future comparisons
4. **Regular Testing**: Schedule regular baseline measurements and testing
5. **Documentation**: Update documentation with baseline metrics and thresholds

---

*This report was generated automatically by the Mingus Baseline Testing Suite.*
"""
        
        # Save report
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Comprehensive report saved to {report_path}")
        return report_path
    
    def run_all_tests(self, parallel: bool = True) -> Dict[str, Any]:
        """Run all baseline tests"""
        logger.info("Starting comprehensive baseline testing...")
        
        start_time = time.time()
        
        # Determine which tests to run
        test_types = [test_type for test_type, config in self.test_modules.items() if config['enabled']]
        
        if not test_types:
            logger.warning("No tests enabled in configuration")
            return {'error': 'No tests enabled'}
        
        logger.info(f"Running tests: {test_types}")
        
        # Run tests
        if parallel:
            results = self.run_tests_parallel(test_types)
        else:
            results = self.run_tests_sequential(test_types)
        
        # Generate comprehensive report
        report_path = self.generate_comprehensive_report(results)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Final summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'test_types': test_types,
            'results': results,
            'comprehensive_report': report_path,
            'summary': {
                'total_tests': len(results),
                'completed': len([r for r in results.values() if r.get('status') == 'COMPLETED']),
                'failed': len([r for r in results.values() if r.get('status') == 'FAILED']),
                'success_rate': (len([r for r in results.values() if r.get('status') == 'COMPLETED']) / len(results) * 100) if results else 0
            }
        }
        
        logger.info(f"Baseline testing completed in {duration:.2f} seconds")
        logger.info(f"Success rate: {summary['summary']['success_rate']:.1f}%")
        logger.info(f"Comprehensive report: {report_path}")
        
        return summary

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file"""
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)
    else:
        # Default configuration
        return {
            'performance': {
                'enabled': True,
                'database_path': 'performance_metrics.db',
                'api_base_url': 'http://localhost:5000',
                'frontend_url': 'http://localhost:3000'
            },
            'ux': {
                'enabled': True,
                'database_path': 'ux_metrics.db',
                'frontend_url': 'http://localhost:3000',
                'api_base_url': 'http://localhost:5000'
            },
            'e2e': {
                'enabled': True,
                'base_url': 'http://localhost:3000',
                'api_url': 'http://localhost:5000'
            },
            'visual': {
                'enabled': True,
                'base_url': 'http://localhost:3000',
                'threshold': 0.95
            },
            'accessibility': {
                'enabled': True,
                'base_url': 'http://localhost:3000',
                'api_url': 'http://localhost:5000'
            }
        }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Mingus Baseline Testing Suite')
    parser.add_argument('--config', default='baseline_config.json', help='Configuration file path')
    parser.add_argument('--parallel', action='store_true', default=True, help='Run tests in parallel')
    parser.add_argument('--sequential', action='store_true', help='Run tests sequentially')
    parser.add_argument('--test-types', nargs='+', help='Specific test types to run')
    parser.add_argument('--output', help='Output file for results')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override test types if specified
    if args.test_types:
        for test_type in config:
            config[test_type]['enabled'] = test_type in args.test_types
    
    # Determine execution mode
    parallel = args.parallel and not args.sequential
    
    # Run tests
    runner = BaselineTestRunner(config)
    results = runner.run_all_tests(parallel=parallel)
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
