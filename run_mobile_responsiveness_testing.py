#!/usr/bin/env python3
"""
Comprehensive Mobile Responsiveness Testing Runner
Orchestrates all testing tools and provides unified interface
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MobileResponsivenessTestRunner:
    """Comprehensive mobile responsiveness testing runner"""
    
    def __init__(self, base_url: str = "http://localhost:5000", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.test_results = {}
        self.start_time = None
        
        # Test modules
        self.test_modules = {
            'responsiveness': 'mobile_responsiveness_testing_suite.py',
            'css_validation': 'css_media_query_validator.py',
            'touch_interactions': 'touch_interaction_tester.py'
        }
        
        # Default test configuration
        self.default_config = {
            'devices': [
                {'name': 'iPhone SE', 'width': 320, 'height': 568},
                {'name': 'iPhone 14', 'width': 375, 'height': 812},
                {'name': 'iPhone 14 Plus', 'width': 428, 'height': 926},
                {'name': 'Samsung Galaxy S21', 'width': 360, 'height': 800},
                {'name': 'Google Pixel', 'width': 411, 'height': 731},
                {'name': 'iPad', 'width': 768, 'height': 1024}
            ],
            'pages': [
                '/',
                '/landing',
                '/health',
                '/budget',
                '/profile',
                '/articles',
                '/assessments',
                '/payment',
                '/subscription'
            ],
            'css_files': [
                'frontend/src/css/',
                'mobile_responsive_fixes.css',
                'enhanced_accessibility_styles.css'
            ]
        }
    
    def run_all_tests(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run all mobile responsiveness tests"""
        if config is None:
            config = self.default_config
        
        self.start_time = time.time()
        
        print("🚀 Starting Comprehensive Mobile Responsiveness Testing")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Devices: {len(config['devices'])}")
        print(f"Pages: {len(config['pages'])}")
        print(f"CSS Files: {len(config['css_files'])}")
        print("=" * 80)
        
        try:
            # 1. Run mobile responsiveness testing
            print("\n📱 Testing Mobile Responsiveness...")
            responsiveness_results = self._run_responsiveness_tests(config)
            self.test_results['responsiveness'] = responsiveness_results
            
            # 2. Run CSS media query validation
            print("\n🎨 Validating CSS Media Queries...")
            css_results = self._run_css_validation(config)
            self.test_results['css_validation'] = css_results
            
            # 3. Run touch interaction testing
            print("\n👆 Testing Touch Interactions...")
            touch_results = self._run_touch_interaction_tests(config)
            self.test_results['touch_interactions'] = touch_results
            
            # 4. Generate comprehensive report
            print("\n📊 Generating Comprehensive Report...")
            comprehensive_report = self._generate_comprehensive_report()
            
            # 5. Save all results
            self._save_all_results(comprehensive_report)
            
            # 6. Print summary
            self._print_summary(comprehensive_report)
            
            return comprehensive_report
            
        except Exception as e:
            logger.error(f"Comprehensive testing failed: {e}")
            raise
    
    def _run_responsiveness_tests(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run mobile responsiveness testing suite"""
        try:
            cmd = [
                'python3', 'mobile_responsiveness_testing_suite.py',
                '--url', self.base_url
            ]
            
            if self.headless:
                cmd.append('--headless')
            
            if config.get('pages'):
                cmd.extend(['--pages'] + config['pages'])
            
            print(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Responsiveness tests completed successfully")
                return {
                    'status': 'success',
                    'output': result.stdout,
                    'error': result.stderr
                }
            else:
                print(f"❌ Responsiveness tests failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'output': result.stdout,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("⏰ Responsiveness tests timed out")
            return {
                'status': 'timeout',
                'output': '',
                'error': 'Tests exceeded 5 minute timeout'
            }
        except Exception as e:
            print(f"❌ Responsiveness tests error: {e}")
            return {
                'status': 'error',
                'output': '',
                'error': str(e)
            }
    
    def _run_css_validation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run CSS media query validation"""
        try:
            css_results = {}
            
            for css_path in config.get('css_files', []):
                if os.path.exists(css_path):
                    print(f"Validating: {css_path}")
                    
                    cmd = [
                        'python3', 'css_media_query_validator.py',
                        css_path,
                        '--output', f'css_validation_report_{Path(css_path).stem}.txt'
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        css_results[css_path] = {
                            'status': 'success',
                            'output': result.stdout,
                            'error': result.stderr
                        }
                        print(f"✅ {css_path} validation completed")
                    else:
                        css_results[css_path] = {
                            'status': 'failed',
                            'output': result.stdout,
                            'error': result.stderr
                        }
                        print(f"❌ {css_path} validation failed")
                else:
                    print(f"⚠️ CSS file not found: {css_path}")
                    css_results[css_path] = {
                        'status': 'not_found',
                        'output': '',
                        'error': 'File not found'
                    }
            
            return css_results
            
        except Exception as e:
            logger.error(f"CSS validation error: {e}")
            return {'error': str(e)}
    
    def _run_touch_interaction_tests(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run touch interaction testing"""
        try:
            cmd = [
                'python3', 'touch_interaction_tester.py',
                '--url', self.base_url
            ]
            
            if self.headless:
                cmd.append('--headless')
            
            if config.get('pages'):
                cmd.extend(['--pages'] + config['pages'])
            
            print(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Touch interaction tests completed successfully")
                return {
                    'status': 'success',
                    'output': result.stdout,
                    'error': result.stderr
                }
            else:
                print(f"❌ Touch interaction tests failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'output': result.stdout,
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("⏰ Touch interaction tests timed out")
            return {
                'status': 'timeout',
                'output': '',
                'error': 'Tests exceeded 5 minute timeout'
            }
        except Exception as e:
            print(f"❌ Touch interaction tests error: {e}")
            return {
                'status': 'error',
                'output': '',
                'error': str(e)
            }
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive testing report"""
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        # Collect results from all test modules
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'test_duration_seconds': round(duration, 2),
            'base_url': self.base_url,
            'test_modules': {},
            'overall_status': 'unknown',
            'summary': {},
            'recommendations': []
        }
        
        # Process responsiveness test results
        if 'responsiveness' in self.test_results:
            resp_result = self.test_results['responsiveness']
            report['test_modules']['responsiveness'] = {
                'status': resp_result['status'],
                'success': resp_result['status'] == 'success'
            }
        
        # Process CSS validation results
        if 'css_validation' in self.test_results:
            css_results = self.test_results['css_validation']
            successful_css = sum(1 for result in css_results.values() if result.get('status') == 'success')
            total_css = len(css_results)
            
            report['test_modules']['css_validation'] = {
                'status': 'success' if successful_css == total_css else 'partial',
                'success': successful_css == total_css,
                'files_tested': total_css,
                'files_passed': successful_css
            }
        
        # Process touch interaction results
        if 'touch_interactions' in self.test_results:
            touch_result = self.test_results['touch_interactions']
            report['test_modules']['touch_interactions'] = {
                'status': touch_result['status'],
                'success': touch_result['status'] == 'success'
            }
        
        # Determine overall status
        successful_modules = sum(1 for module in report['test_modules'].values() if module.get('success', False))
        total_modules = len(report['test_modules'])
        
        if successful_modules == total_modules:
            report['overall_status'] = 'success'
        elif successful_modules > 0:
            report['overall_status'] = 'partial'
        else:
            report['overall_status'] = 'failed'
        
        # Generate summary
        report['summary'] = {
            'total_modules': total_modules,
            'successful_modules': successful_modules,
            'failed_modules': total_modules - successful_modules,
            'success_rate': round((successful_modules / total_modules) * 100, 2) if total_modules > 0 else 0
        }
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations()
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        # Check responsiveness test results
        if 'responsiveness' in self.test_results:
            resp_result = self.test_results['responsiveness']
            if resp_result['status'] != 'success':
                recommendations.append("Review and fix mobile responsiveness issues identified in testing")
        
        # Check CSS validation results
        if 'css_validation' in self.test_results:
            css_results = self.test_results['css_validation']
            failed_css = sum(1 for result in css_results.values() if result.get('status') == 'failed')
            if failed_css > 0:
                recommendations.append(f"Fix CSS media query issues in {failed_css} file(s)")
        
        # Check touch interaction results
        if 'touch_interactions' in self.test_results:
            touch_result = self.test_results['touch_interactions']
            if touch_result['status'] != 'success':
                recommendations.append("Improve touch interaction support and accessibility")
        
        # General recommendations
        recommendations.extend([
            "Run tests regularly during development to catch issues early",
            "Test on actual mobile devices when possible",
            "Use the React component for manual testing during development",
            "Consider implementing automated testing in CI/CD pipeline"
        ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _save_all_results(self, comprehensive_report: Dict[str, Any]) -> None:
        """Save all test results and reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save comprehensive report
        report_file = f"comprehensive_mobile_testing_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        # Save detailed test results
        results_file = f"detailed_test_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📁 Results saved to:")
        print(f"  • {report_file}")
        print(f"  • {results_file}")
    
    def _print_summary(self, report: Dict[str, Any]) -> None:
        """Print testing summary"""
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE TESTING SUMMARY")
        print("=" * 80)
        
        # Overall status
        status_emoji = {
            'success': '✅',
            'partial': '⚠️',
            'failed': '❌',
            'unknown': '❓'
        }
        
        print(f"Overall Status: {status_emoji.get(report['overall_status'], '❓')} {report['overall_status'].upper()}")
        print(f"Test Duration: {report['test_duration_seconds']} seconds")
        print(f"Success Rate: {report['summary']['success_rate']}%")
        
        # Module results
        print(f"\n📊 Module Results:")
        for module_name, module_result in report['test_modules'].items():
            status_icon = '✅' if module_result.get('success') else '❌'
            print(f"  {status_icon} {module_name.replace('_', ' ').title()}: {module_result['status']}")
        
        # Recommendations
        if report['recommendations']:
            print(f"\n💡 Top Recommendations:")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                print(f"  {i}. {rec}")
        
        print(f"\n🎯 Testing completed successfully!")
        print(f"📁 Detailed reports saved to JSON files")

def load_config(config_file: str) -> Dict[str, Any]:
    """Load test configuration from file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Config file {config_file} not found, using defaults")
        return {}
    except json.JSONDecodeError:
        print(f"⚠️ Invalid JSON in config file {config_file}, using defaults")
        return {}

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Comprehensive Mobile Responsiveness Testing Runner')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL to test')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--devices', nargs='+', help='Specific devices to test')
    parser.add_argument('--pages', nargs='+', help='Specific pages to test')
    parser.add_argument('--css-files', nargs='+', help='Specific CSS files to validate')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Initialize runner to get default config
    runner = MobileResponsivenessTestRunner(base_url=args.url, headless=args.headless)
    
    # Merge with default config if no config file provided
    if not config:
        config = runner.default_config.copy()
    
    # Override config with command line arguments
    if args.devices:
        config['devices'] = [{'name': d, 'width': 375, 'height': 812} for d in args.devices]
    if args.pages:
        config['pages'] = args.pages
    if args.css_files:
        config['css_files'] = args.css_files
    
    # Initialize runner
    runner = MobileResponsivenessTestRunner(base_url=args.url, headless=args.headless)
    
    try:
        # Run comprehensive testing
        report = runner.run_all_tests(config)
        
        # Exit with appropriate code
        if report['overall_status'] == 'success':
            sys.exit(0)
        elif report['overall_status'] == 'partial':
            sys.exit(1)
        else:
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        print(f"\n❌ Testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
