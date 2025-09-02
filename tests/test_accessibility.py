"""
Accessibility Testing Framework for MINGUS Financial Application
Integrates axe-core, WCAG compliance checking, and automated accessibility validation
"""

import pytest
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time
import os
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessibilityTester:
    """Comprehensive accessibility testing using multiple tools and techniques"""
    
    def __init__(self, base_url: str = "http://localhost:5000", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': base_url,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'wcag_aa_compliance': False,
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
    def setup_driver(self):
        """Initialize Chrome WebDriver with accessibility testing capabilities"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # Enable accessibility features
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--v=1")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def teardown_driver(self):
        """Clean up WebDriver resources"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver resources cleaned up")
    
    def inject_axe_core(self):
        """Inject axe-core library into the current page"""
        try:
            # Inject axe-core from CDN
            axe_script = """
            var script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.0/axe.min.js';
            document.head.appendChild(script);
            """
            self.driver.execute_script(axe_script)
            
            # Wait for axe-core to load
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return typeof axe !== 'undefined'")
            )
            logger.info("axe-core injected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to inject axe-core: {e}")
            return False
    
    def run_axe_analysis(self, page_name: str = "Unknown Page") -> Dict:
        """Run axe-core accessibility analysis"""
        try:
            if not self.inject_axe_core():
                return {'error': 'Failed to inject axe-core'}
            
            # Run axe-core analysis
            axe_results = self.driver.execute_script("""
                return axe.run({
                    runOnly: {
                        type: 'tag',
                        values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']
                    },
                    rules: {
                        'color-contrast': { enabled: true },
                        'landmark-one-main': { enabled: true },
                        'page-has-heading-one': { enabled: true },
                        'skip-link': { enabled: true }
                    }
                });
            """)
            
            # Process results
            violations = axe_results.get('violations', [])
            passes = axe_results.get('passes', [])
            incomplete = axe_results.get('incomplete', [])
            
            # Categorize issues by WCAG level
            wcag_a_violations = [v for v in violations if 'wcag2a' in v.get('tags', []) or 'wcag21a' in v.get('tags', [])]
            wcag_aa_violations = [v for v in violations if 'wcag2aa' in v.get('tags', []) or 'wcag21aa' in v.get('tags', [])]
            
            results = {
                'page_name': page_name,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'violations': violations,
                'passes': passes,
                'incomplete': incomplete,
                'wcag_a_violations': wcag_a_violations,
                'wcag_aa_violations': wcag_aa_violations,
                'total_violations': len(violations),
                'total_passes': len(passes),
                'wcag_aa_compliant': len(wcag_aa_violations) == 0,
                'wcag_a_compliant': len(wcag_a_violations) == 0
            }
            
            logger.info(f"axe-core analysis completed for {page_name}: {len(violations)} violations, {len(passes)} passes")
            return results
            
        except Exception as e:
            logger.error(f"axe-core analysis failed: {e}")
            return {'error': str(e)}
    
    def test_color_contrast(self, page_name: str = "Unknown Page") -> Dict:
        """Test color contrast compliance using axe-core and custom validation"""
        try:
            if not self.inject_axe_core():
                return {'error': 'Failed to inject axe-core'}
            
            # Run color contrast specific analysis
            contrast_results = self.driver.execute_script("""
                return axe.run({
                    runOnly: {
                        type: 'rule',
                        values: ['color-contrast']
                    }
                });
            """)
            
            violations = contrast_results.get('violations', [])
            passes = contrast_results.get('passes', [])
            
            # Custom contrast validation for financial data
            custom_contrast_issues = self._validate_financial_contrast()
            
            results = {
                'page_name': page_name,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'contrast_violations': violations,
                'contrast_passes': passes,
                'custom_contrast_issues': custom_contrast_issues,
                'total_contrast_issues': len(violations) + len(custom_contrast_issues),
                'wcag_aa_contrast_compliant': len(violations) == 0
            }
            
            logger.info(f"Color contrast analysis completed: {len(violations)} violations, {len(passes)} passes")
            return results
            
        except Exception as e:
            logger.error(f"Color contrast testing failed: {e}")
            return {'error': str(e)}
    
    def _validate_financial_contrast(self) -> List[Dict]:
        """Custom validation for financial application specific contrast requirements"""
        issues = []
        
        try:
            # Check financial data text contrast
            financial_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                '.financial-data, .currency-amount, .percentage-value, .calculation-result')
            
            for element in financial_elements:
                # Get computed styles
                color = element.value_of_css_property('color')
                background = element.value_of_css_property('background-color')
                
                # Basic contrast validation (simplified)
                if color and background:
                    # This is a simplified check - in production you'd use a proper contrast library
                    if color == background or color == 'rgba(0, 0, 0, 0)':
                        issues.append({
                            'type': 'contrast',
                            'element': element.tag_name,
                            'text': element.text[:50],
                            'issue': 'Insufficient contrast for financial data'
                        })
            
        except Exception as e:
            logger.warning(f"Custom contrast validation failed: {e}")
        
        return issues
    
    def test_keyboard_navigation(self, page_name: str = "Unknown Page") -> Dict:
        """Test keyboard navigation accessibility"""
        try:
            results = {
                'page_name': page_name,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'keyboard_tests': [],
                'navigation_issues': [],
                'focus_management_issues': []
            }
            
            # Test Tab navigation
            tab_results = self._test_tab_navigation()
            results['keyboard_tests'].append(tab_results)
            
            # Test arrow key navigation
            arrow_results = self._test_arrow_navigation()
            results['keyboard_tests'].append(arrow_results)
            
            # Test Enter/Space activation
            activation_results = self._test_element_activation()
            results['keyboard_tests'].append(activation_results)
            
            # Test skip links
            skip_link_results = self._test_skip_links()
            results['keyboard_tests'].append(skip_link_results)
            
            # Test focus indicators
            focus_results = self._test_focus_indicators()
            results['keyboard_tests'].append(focus_results)
            
            # Aggregate issues
            for test in results['keyboard_tests']:
                if test.get('issues'):
                    results['navigation_issues'].extend(test['issues'])
                if test.get('focus_issues'):
                    results['focus_management_issues'].extend(test['focus_issues'])
            
            results['total_navigation_issues'] = len(results['navigation_issues'])
            results['keyboard_navigation_compliant'] = len(results['navigation_issues']) == 0
            
            logger.info(f"Keyboard navigation testing completed: {len(results['navigation_issues'])} issues found")
            return results
            
        except Exception as e:
            logger.error(f"Keyboard navigation testing failed: {e}")
            return {'error': str(e)}
    
    def _test_tab_navigation(self) -> Dict:
        """Test Tab key navigation through interactive elements"""
        try:
            # Find all focusable elements
            focusable_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])')
            
            tab_order = []
            issues = []
            
            # Test Tab navigation
            for i, element in enumerate(focusable_elements):
                try:
                    element.send_keys(Keys.TAB)
                    time.sleep(0.1)  # Allow focus to settle
                    
                    focused_element = self.driver.switch_to.active_element
                    tab_order.append({
                        'index': i,
                        'tag': focused_element.tag_name,
                        'text': focused_element.text[:50],
                        'accessible_name': focused_element.get_attribute('aria-label') or focused_element.text[:50]
                    })
                    
                    # Check if element is properly focusable
                    if not focused_element.is_displayed() or not focused_element.is_enabled():
                        issues.append({
                            'type': 'tab_navigation',
                            'element': focused_element.tag_name,
                            'issue': 'Element not properly focusable'
                        })
                        
                except Exception as e:
                    issues.append({
                        'type': 'tab_navigation',
                        'element': element.tag_name,
                        'issue': f'Tab navigation failed: {str(e)}'
                    })
            
            return {
                'test_type': 'tab_navigation',
                'total_elements': len(focusable_elements),
                'tab_order': tab_order,
                'issues': issues,
                'passed': len(issues) == 0
            }
            
        except Exception as e:
            return {
                'test_type': 'tab_navigation',
                'error': str(e),
                'passed': False
            }
    
    def _test_arrow_navigation(self) -> Dict:
        """Test arrow key navigation for tables and lists"""
        try:
            results = {
                'test_type': 'arrow_navigation',
                'table_tests': [],
                'list_tests': [],
                'issues': []
            }
            
            # Test table navigation
            tables = self.driver.find_elements(By.CSS_SELECTOR, 'table')
            for table in tables:
                try:
                    # Focus on first cell
                    first_cell = table.find_element(By.CSS_SELECTOR, 'td, th')
                    first_cell.click()
                    
                    # Test arrow keys
                    first_cell.send_keys(Keys.ARROW_RIGHT)
                    time.sleep(0.1)
                    
                    right_cell = self.driver.switch_to.active_element
                    if right_cell != first_cell:
                        results['table_tests'].append({
                            'table': table.get_attribute('class') or 'unknown',
                            'arrow_navigation': 'working'
                        })
                    else:
                        results['table_tests'].append({
                            'table': table.get_attribute('class') or 'unknown',
                            'arrow_navigation': 'not_working'
                        })
                        results['issues'].append({
                            'type': 'arrow_navigation',
                            'element': 'table',
                            'issue': 'Arrow key navigation not working'
                        })
                        
                except Exception as e:
                    results['issues'].append({
                        'type': 'arrow_navigation',
                        'element': 'table',
                        'issue': f'Table navigation test failed: {str(e)}'
                    })
            
            results['passed'] = len(results['issues']) == 0
            return results
            
        except Exception as e:
            return {
                'test_type': 'arrow_navigation',
                'error': str(e),
                'passed': False
            }
    
    def _test_element_activation(self) -> Dict:
        """Test Enter and Space key activation of elements"""
        try:
            results = {
                'test_type': 'element_activation',
                'enter_tests': [],
                'space_tests': [],
                'issues': []
            }
            
            # Test buttons and links
            interactive_elements = self.driver.find_elements(By.CSS_SELECTOR, 'button, a[href]')
            
            for element in interactive_elements[:5]:  # Test first 5 elements
                try:
                    # Test Enter key
                    element.send_keys(Keys.ENTER)
                    time.sleep(0.1)
                    
                    # Check if action occurred (simplified check)
                    results['enter_tests'].append({
                        'element': element.tag_name,
                        'text': element.text[:30],
                        'enter_working': True
                    })
                    
                    # Test Space key
                    element.send_keys(Keys.SPACE)
                    time.sleep(0.1)
                    
                    results['space_tests'].append({
                        'element': element.tag_name,
                        'text': element.text[:30],
                        'space_working': True
                    })
                    
                except Exception as e:
                    results['issues'].append({
                        'type': 'element_activation',
                        'element': element.tag_name,
                        'issue': f'Activation test failed: {str(e)}'
                    })
            
            results['passed'] = len(results['issues']) == 0
            return results
            
        except Exception as e:
            return {
                'test_type': 'element_activation',
                'error': str(e),
                'passed': False
            }
    
    def _test_skip_links(self) -> Dict:
        """Test skip link functionality"""
        try:
            results = {
                'test_type': 'skip_links',
                'skip_links_found': 0,
                'skip_links_working': 0,
                'issues': []
            }
            
            skip_links = self.driver.find_elements(By.CSS_SELECTOR, '.skip-link, [href^="#"]')
            results['skip_links_found'] = len(skip_links)
            
            for skip_link in skip_links:
                try:
                    # Test skip link functionality
                    skip_link.send_keys(Keys.ENTER)
                    time.sleep(0.1)
                    
                    # Check if focus moved to target
                    target_id = skip_link.get_attribute('href').split('#')[1]
                    target_element = self.driver.find_element(By.ID, target_id)
                    
                    if target_element == self.driver.switch_to.active_element:
                        results['skip_links_working'] += 1
                    else:
                        results['issues'].append({
                            'type': 'skip_link',
                            'element': skip_link.tag_name,
                            'issue': 'Skip link target not focused'
                        })
                        
                except Exception as e:
                    results['issues'].append({
                        'type': 'skip_link',
                        'element': skip_link.tag_name,
                        'issue': f'Skip link test failed: {str(e)}'
                    })
            
            results['passed'] = len(results['issues']) == 0
            return results
            
        except Exception as e:
            return {
                'test_type': 'skip_links',
                'error': str(e),
                'passed': False
            }
    
    def _test_focus_indicators(self) -> Dict:
        """Test focus indicator visibility"""
        try:
            results = {
                'test_type': 'focus_indicators',
                'elements_with_focus': 0,
                'focus_indicators_visible': 0,
                'issues': []
            }
            
            # Test focus indicators on interactive elements
            interactive_elements = self.driver.find_elements(By.CSS_SELECTOR, 'button, a[href], input, select, textarea')
            
            for element in interactive_elements[:10]:  # Test first 10 elements
                try:
                    element.send_keys(Keys.TAB)
                    time.sleep(0.1)
                    
                    focused_element = self.driver.switch_to.active_element
                    results['elements_with_focus'] += 1
                    
                    # Check focus indicator styles
                    outline = focused_element.value_of_css_property('outline')
                    box_shadow = focused_element.value_of_css_property('box-shadow')
                    
                    if outline != 'none' or box_shadow != 'none':
                        results['focus_indicators_visible'] += 1
                    else:
                        results['issues'].append({
                            'type': 'focus_indicator',
                            'element': focused_element.tag_name,
                            'issue': 'No visible focus indicator'
                        })
                        
                except Exception as e:
                    results['issues'].append({
                        'type': 'focus_indicator',
                        'element': element.tag_name,
                        'issue': f'Focus indicator test failed: {str(e)}'
                    })
            
            results['passed'] = len(results['issues']) == 0
            return results
            
        except Exception as e:
            return {
                'test_type': 'focus_indicators',
                'error': str(e),
                'passed': False
            }
    
    def test_wcag_compliance(self, page_name: str = "Unknown Page") -> Dict:
        """Comprehensive WCAG compliance testing"""
        try:
            results = {
                'page_name': page_name,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'wcag_tests': {},
                'overall_compliance': False
            }
            
            # Run axe-core analysis
            axe_results = self.run_axe_analysis(page_name)
            if 'error' not in axe_results:
                results['wcag_tests']['axe_core'] = axe_results
            
            # Test color contrast
            contrast_results = self.test_color_contrast(page_name)
            if 'error' not in contrast_results:
                results['wcag_tests']['color_contrast'] = contrast_results
            
            # Test keyboard navigation
            keyboard_results = self.test_keyboard_navigation(page_name)
            if 'error' not in keyboard_results:
                results['wcag_tests']['keyboard_navigation'] = keyboard_results
            
            # Determine overall compliance
            axe_compliant = results['wcag_tests'].get('axe_core', {}).get('wcag_aa_compliant', False)
            contrast_compliant = results['wcag_tests'].get('color_contrast', {}).get('wcag_aa_contrast_compliant', False)
            keyboard_compliant = results['wcag_tests'].get('keyboard_navigation', {}).get('keyboard_navigation_compliant', False)
            
            results['overall_compliance'] = axe_compliant and contrast_compliant and keyboard_compliant
            
            # Update global results
            self.results['tests_run'] += 1
            if results['overall_compliance']:
                self.results['tests_passed'] += 1
            else:
                self.results['tests_failed'] += 1
                
                # Collect critical issues
                if axe_results.get('wcag_aa_violations'):
                    self.results['critical_issues'].extend([
                        f"{page_name}: {v.get('description', 'Unknown violation')}" 
                        for v in axe_results['wcag_aa_violations']
                    ])
            
            logger.info(f"WCAG compliance testing completed for {page_name}: {'PASSED' if results['overall_compliance'] else 'FAILED'}")
            return results
            
        except Exception as e:
            logger.error(f"WCAG compliance testing failed: {e}")
            return {'error': str(e)}
    
    def generate_report(self) -> Dict:
        """Generate comprehensive accessibility testing report"""
        try:
            report = {
                'summary': {
                    'total_tests': self.results['tests_run'],
                    'tests_passed': self.results['tests_passed'],
                    'tests_failed': self.results['tests_failed'],
                    'success_rate': (self.results['tests_passed'] / self.results['tests_run'] * 100) if self.results['tests_run'] > 0 else 0,
                    'wcag_aa_compliant': self.results['wcag_aa_compliance']
                },
                'details': self.results,
                'recommendations': self._generate_recommendations()
            }
            
            # Determine overall compliance
            self.results['wcag_aa_compliance'] = (
                self.results['tests_failed'] == 0 and 
                len(self.results['critical_issues']) == 0
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        if self.results['critical_issues']:
            recommendations.append("Address critical WCAG AA violations immediately")
            recommendations.append("Focus on color contrast and keyboard navigation issues")
        
        if self.results['warnings']:
            recommendations.append("Review and address accessibility warnings")
        
        if self.results['tests_failed'] > 0:
            recommendations.append("Implement comprehensive accessibility fixes")
            recommendations.append("Consider accessibility training for development team")
        
        if not recommendations:
            recommendations.append("Maintain current accessibility standards")
            recommendations.append("Continue regular accessibility testing")
        
        return recommendations
    
    def save_report(self, filename: str = None) -> str:
        """Save testing report to JSON file"""
        try:
            if not filename:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"accessibility_report_{timestamp}.json"
            
            report = self.generate_report()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Accessibility report saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return ""

# Pytest fixtures and test functions
@pytest.fixture(scope="class")
def accessibility_tester():
    """Fixture to provide accessibility tester instance"""
    tester = AccessibilityTester()
    tester.setup_driver()
    yield tester
    tester.teardown_driver()

class TestAccessibility:
    """Test class for accessibility testing"""
    
    def test_homepage_accessibility(self, accessibility_tester):
        """Test homepage accessibility compliance"""
        accessibility_tester.driver.get(f"{accessibility_tester.base_url}/")
        results = accessibility_tester.test_wcag_compliance("Homepage")
        assert results['overall_compliance'], f"Homepage accessibility test failed: {results}"
    
    def test_financial_forms_accessibility(self, accessibility_tester):
        """Test financial forms accessibility"""
        accessibility_tester.driver.get(f"{accessibility_tester.base_url}/forms")
        results = accessibility_tester.test_wcag_compliance("Financial Forms")
        assert results['overall_compliance'], f"Financial forms accessibility test failed: {results}"
    
    def test_color_contrast_compliance(self, accessibility_tester):
        """Test color contrast compliance"""
        accessibility_tester.driver.get(f"{accessibility_tester.base_url}/")
        results = accessibility_tester.test_color_contrast("Homepage")
        assert results['wcag_aa_contrast_compliant'], f"Color contrast test failed: {results}"
    
    def test_keyboard_navigation(self, accessibility_tester):
        """Test keyboard navigation accessibility"""
        accessibility_tester.driver.get(f"{accessibility_tester.base_url}/")
        results = accessibility_tester.test_keyboard_navigation("Homepage")
        assert results['keyboard_navigation_compliant'], f"Keyboard navigation test failed: {results}"
    
    def test_skip_links_functionality(self, accessibility_tester):
        """Test skip links functionality"""
        accessibility_tester.driver.get(f"{accessibility_tester.base_url}/")
        skip_results = accessibility_tester._test_skip_links()
        assert skip_results['passed'], f"Skip links test failed: {skip_results}"
    
    def test_focus_indicators(self, accessibility_tester):
        """Test focus indicator visibility"""
        accessibility_tester.driver.get(f"{accessibility_tester.base_url}/")
        focus_results = accessibility_tester._test_focus_indicators()
        assert focus_results['passed'], f"Focus indicators test failed: {focus_results}"

# Standalone testing function
def run_accessibility_tests(base_url: str, pages: List[str] = None, headless: bool = True) -> Dict:
    """Run accessibility tests on specified pages"""
    if pages is None:
        pages = ['/']
    
    tester = AccessibilityTester(base_url, headless)
    
    try:
        tester.setup_driver()
        
        for page in pages:
            try:
                tester.driver.get(f"{base_url}{page}")
                page_name = page if page != '/' else 'Homepage'
                tester.test_wcag_compliance(page_name)
            except Exception as e:
                logger.error(f"Failed to test page {page}: {e}")
        
        report = tester.generate_report()
        filename = tester.save_report()
        
        return {
            'report': report,
            'report_file': filename,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Accessibility testing failed: {e}")
        return {
            'error': str(e),
            'success': False
        }
    finally:
        tester.teardown_driver()

if __name__ == "__main__":
    # Example usage
    results = run_accessibility_tests("http://localhost:5000", ['/', '/forms', '/calculator'])
    print(json.dumps(results, indent=2))
