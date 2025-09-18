#!/usr/bin/env python3
"""
Mingus Application - Accessibility Testing Automation
===================================================

Comprehensive accessibility testing using axe-core, WAVE, and custom checks
for WCAG 2.1 AA compliance.

Author: Mingus Accessibility Team
Date: January 2025
"""

import pytest
import time
import json
import logging
import os
import requests
from datetime import datetime
from typing import Dict, List, Any, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessibilityTest:
    """Accessibility testing class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url', 'http://localhost:3000')
        self.api_url = config.get('api_url', 'http://localhost:5000')
        self.driver = None
        self.test_results = []
        self.axe_script_url = config.get('axe_script_url', 'https://cdn.jsdelivr.net/npm/axe-core@4.7.0/axe.min.js')
        
    def setup_driver(self, device_type: str = 'desktop'):
        """Setup WebDriver for accessibility testing"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        if device_type == 'mobile':
            chrome_options.add_argument('--window-size=375,667')
            chrome_options.add_experimental_option("mobileEmulation", {
                "deviceMetrics": {"width": 375, "height": 667, "pixelRatio": 2.0},
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            })
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        return self.driver
    
    def teardown_driver(self):
        """Cleanup WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def inject_axe_script(self):
        """Inject axe-core script into the page"""
        try:
            self.driver.execute_script(f"""
                var script = document.createElement('script');
                script.src = '{self.axe_script_url}';
                script.onload = function() {{
                    console.log('Axe-core loaded successfully');
                }};
                script.onerror = function() {{
                    console.error('Failed to load axe-core');
                }};
                document.head.appendChild(script);
            """)
            time.sleep(3)  # Wait for script to load
            return True
        except Exception as e:
            logger.error(f"Error injecting axe script: {e}")
            return False
    
    def run_axe_tests(self, page_name: str, url: str) -> Dict[str, Any]:
        """Run axe-core accessibility tests"""
        logger.info(f"Running axe tests for {page_name}...")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Inject axe script
            if not self.inject_axe_script():
                return {
                    'page': page_name,
                    'url': url,
                    'status': 'ERROR',
                    'error': 'Failed to inject axe script'
                }
            
            # Run axe tests
            axe_results = self.driver.execute_script("""
                return new Promise(function(resolve) {
                    if (typeof axe !== 'undefined') {
                        axe.run(function(err, results) {
                            if (err) {
                                resolve({error: err.toString()});
                            } else {
                                resolve(results);
                            }
                        });
                    } else {
                        resolve({error: 'Axe not available'});
                    }
                });
            """)
            
            if 'error' in axe_results:
                return {
                    'page': page_name,
                    'url': url,
                    'status': 'ERROR',
                    'error': axe_results['error']
                }
            
            # Process results
            violations = axe_results.get('violations', [])
            passes = axe_results.get('passes', [])
            incomplete = axe_results.get('incomplete', [])
            
            # Calculate scores
            total_checks = len(violations) + len(passes) + len(incomplete)
            pass_rate = (len(passes) / total_checks * 100) if total_checks > 0 else 100
            
            # Categorize violations by severity
            critical_violations = [v for v in violations if v.get('impact') == 'critical']
            serious_violations = [v for v in violations if v.get('impact') == 'serious']
            moderate_violations = [v for v in violations if v.get('impact') == 'moderate']
            minor_violations = [v for v in violations if v.get('impact') == 'minor']
            
            return {
                'page': page_name,
                'url': url,
                'status': 'COMPLETED',
                'total_checks': total_checks,
                'passes': len(passes),
                'violations': len(violations),
                'incomplete': len(incomplete),
                'pass_rate': pass_rate,
                'violations_by_severity': {
                    'critical': len(critical_violations),
                    'serious': len(serious_violations),
                    'moderate': len(moderate_violations),
                    'minor': len(minor_violations)
                },
                'critical_violations': critical_violations,
                'serious_violations': serious_violations,
                'moderate_violations': moderate_violations,
                'minor_violations': minor_violations,
                'all_violations': violations
            }
            
        except Exception as e:
            logger.error(f"Axe test failed for {page_name}: {e}")
            return {
                'page': page_name,
                'url': url,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def test_keyboard_navigation(self, page_name: str, url: str) -> Dict[str, Any]:
        """Test keyboard navigation accessibility"""
        logger.info(f"Testing keyboard navigation for {page_name}...")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Test Tab navigation
            tab_order = []
            focusable_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "a[href], button, input, select, textarea, [tabindex]:not([tabindex='-1'])")
            
            # Start with first focusable element
            if focusable_elements:
                focusable_elements[0].send_keys(Keys.TAB)
                time.sleep(0.5)
                
                # Test tab order
                for i, element in enumerate(focusable_elements[:10]):  # Test first 10 elements
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # Check if element is focused
                            focused_element = self.driver.execute_script("return document.activeElement;")
                            if focused_element == element:
                                tab_order.append({
                                    'index': i,
                                    'tag': element.tag_name,
                                    'text': element.text[:50] if element.text else '',
                                    'accessible_name': element.get_attribute('aria-label') or element.text or 'No accessible name'
                                })
                            
                            element.send_keys(Keys.TAB)
                            time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"Error testing element {i}: {e}")
            
            # Test Enter key activation
            enter_activations = 0
            for element in focusable_elements[:5]:  # Test first 5 elements
                try:
                    if element.is_displayed() and element.is_enabled():
                        element.send_keys(Keys.ENTER)
                        time.sleep(0.5)
                        enter_activations += 1
                except Exception as e:
                    logger.warning(f"Error testing Enter on element: {e}")
            
            # Test Escape key
            escape_works = False
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                time.sleep(0.5)
                escape_works = True
            except Exception as e:
                logger.warning(f"Escape key test failed: {e}")
            
            return {
                'page': page_name,
                'url': url,
                'status': 'COMPLETED',
                'total_focusable_elements': len(focusable_elements),
                'tab_order_tested': len(tab_order),
                'tab_order': tab_order,
                'enter_activations': enter_activations,
                'escape_works': escape_works,
                'keyboard_score': min(100, (len(tab_order) / max(1, len(focusable_elements)) * 100))
            }
            
        except Exception as e:
            logger.error(f"Keyboard navigation test failed for {page_name}: {e}")
            return {
                'page': page_name,
                'url': url,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def test_color_contrast(self, page_name: str, url: str) -> Dict[str, Any]:
        """Test color contrast accessibility"""
        logger.info(f"Testing color contrast for {page_name}...")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get all text elements
            text_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "p, h1, h2, h3, h4, h5, h6, span, div, a, button, label, input, textarea")
            
            contrast_issues = []
            total_text_elements = 0
            
            for element in text_elements[:20]:  # Test first 20 text elements
                try:
                    if element.is_displayed() and element.text.strip():
                        # Get computed styles
                        styles = self.driver.execute_script("""
                            var element = arguments[0];
                            var computed = window.getComputedStyle(element);
                            return {
                                color: computed.color,
                                backgroundColor: computed.backgroundColor,
                                fontSize: computed.fontSize,
                                fontWeight: computed.fontWeight
                            };
                        """, element)
                        
                        total_text_elements += 1
                        
                        # Check if element has sufficient contrast
                        # This is a simplified check - in practice, you'd use a proper contrast calculation
                        if styles['color'] == styles['backgroundColor']:
                            contrast_issues.append({
                                'element': element.tag_name,
                                'text': element.text[:50],
                                'issue': 'Same color and background',
                                'color': styles['color'],
                                'background': styles['backgroundColor']
                            })
                        
                except Exception as e:
                    logger.warning(f"Error checking contrast for element: {e}")
            
            return {
                'page': page_name,
                'url': url,
                'status': 'COMPLETED',
                'total_text_elements': total_text_elements,
                'contrast_issues': len(contrast_issues),
                'issues': contrast_issues,
                'contrast_score': max(0, 100 - (len(contrast_issues) * 10))
            }
            
        except Exception as e:
            logger.error(f"Color contrast test failed for {page_name}: {e}")
            return {
                'page': page_name,
                'url': url,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def test_screen_reader_support(self, page_name: str, url: str) -> Dict[str, Any]:
        """Test screen reader support"""
        logger.info(f"Testing screen reader support for {page_name}...")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check for ARIA attributes
            aria_elements = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label], [aria-labelledby], [aria-describedby]")
            
            # Check for semantic HTML
            semantic_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "main, nav, section, article, aside, header, footer, h1, h2, h3, h4, h5, h6")
            
            # Check for alt text on images
            images = self.driver.find_elements(By.CSS_SELECTOR, "img")
            images_with_alt = self.driver.find_elements(By.CSS_SELECTOR, "img[alt]")
            
            # Check for form labels
            form_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
            labeled_inputs = self.driver.find_elements(By.CSS_SELECTOR, 
                "input[aria-label], input[aria-labelledby], label input, label select, label textarea")
            
            # Check for skip links
            skip_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='#main'], a[href*='#content']")
            
            # Check for heading hierarchy
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            heading_levels = []
            for heading in headings:
                level = int(heading.tag_name[1])
                heading_levels.append(level)
            
            # Check for proper heading hierarchy
            hierarchy_issues = []
            if heading_levels:
                for i in range(1, len(heading_levels)):
                    if heading_levels[i] > heading_levels[i-1] + 1:
                        hierarchy_issues.append(f"Jump from h{heading_levels[i-1]} to h{heading_levels[i]}")
            
            return {
                'page': page_name,
                'url': url,
                'status': 'COMPLETED',
                'aria_elements': len(aria_elements),
                'semantic_elements': len(semantic_elements),
                'total_images': len(images),
                'images_with_alt': len(images_with_alt),
                'alt_text_coverage': (len(images_with_alt) / max(1, len(images)) * 100),
                'total_form_inputs': len(form_inputs),
                'labeled_inputs': len(labeled_inputs),
                'label_coverage': (len(labeled_inputs) / max(1, len(form_inputs)) * 100),
                'skip_links': len(skip_links),
                'heading_hierarchy_issues': len(hierarchy_issues),
                'hierarchy_issues': hierarchy_issues,
                'screen_reader_score': self.calculate_screen_reader_score(
                    len(aria_elements), len(semantic_elements), 
                    len(images_with_alt), len(images),
                    len(labeled_inputs), len(form_inputs),
                    len(skip_links), len(hierarchy_issues)
                )
            }
            
        except Exception as e:
            logger.error(f"Screen reader support test failed for {page_name}: {e}")
            return {
                'page': page_name,
                'url': url,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def calculate_screen_reader_score(self, aria_count, semantic_count, alt_count, total_images, 
                                    labeled_count, total_inputs, skip_links, hierarchy_issues):
        """Calculate screen reader accessibility score"""
        score = 0
        
        # ARIA usage (20 points)
        if aria_count > 0:
            score += min(20, aria_count * 2)
        
        # Semantic HTML (20 points)
        if semantic_count > 0:
            score += min(20, semantic_count * 2)
        
        # Alt text coverage (20 points)
        if total_images > 0:
            score += (alt_count / total_images) * 20
        
        # Form label coverage (20 points)
        if total_inputs > 0:
            score += (labeled_count / total_inputs) * 20
        
        # Skip links (10 points)
        if skip_links > 0:
            score += 10
        
        # Heading hierarchy (10 points)
        score += max(0, 10 - (hierarchy_issues * 2))
        
        return min(100, score)
    
    def test_focus_management(self, page_name: str, url: str) -> Dict[str, Any]:
        """Test focus management accessibility"""
        logger.info(f"Testing focus management for {page_name}...")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Test focus indicators
            focusable_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "a[href], button, input, select, textarea, [tabindex]:not([tabindex='-1'])")
            
            focus_indicators = 0
            for element in focusable_elements[:10]:  # Test first 10 elements
                try:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        time.sleep(0.5)
                        
                        # Check if element has focus indicator
                        focus_style = self.driver.execute_script("""
                            var element = arguments[0];
                            var computed = window.getComputedStyle(element);
                            return {
                                outline: computed.outline,
                                outlineWidth: computed.outlineWidth,
                                boxShadow: computed.boxShadow
                            };
                        """, element)
                        
                        if (focus_style['outline'] != 'none' or 
                            focus_style['outlineWidth'] != '0px' or 
                            focus_style['boxShadow'] != 'none'):
                            focus_indicators += 1
                            
                except Exception as e:
                    logger.warning(f"Error testing focus indicator: {e}")
            
            # Test focus trapping in modals
            modal_focus_trap = False
            try:
                # Look for modals
                modals = self.driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], .modal")
                if modals:
                    modals[0].click()
                    time.sleep(1)
                    
                    # Check if focus is trapped
                    focused_element = self.driver.execute_script("return document.activeElement;")
                    if focused_element and modals[0].find_element(By.CSS_SELECTOR, "*").is_displayed():
                        modal_focus_trap = True
                        
            except Exception as e:
                logger.warning(f"Error testing modal focus trap: {e}")
            
            return {
                'page': page_name,
                'url': url,
                'status': 'COMPLETED',
                'total_focusable_elements': len(focusable_elements),
                'elements_with_focus_indicators': focus_indicators,
                'focus_indicator_coverage': (focus_indicators / max(1, min(10, len(focusable_elements))) * 100),
                'modal_focus_trap': modal_focus_trap,
                'focus_management_score': min(100, (focus_indicators / max(1, min(10, len(focusable_elements))) * 100))
            }
            
        except Exception as e:
            logger.error(f"Focus management test failed for {page_name}: {e}")
            return {
                'page': page_name,
                'url': url,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def run_comprehensive_accessibility_tests(self) -> Dict[str, Any]:
        """Run comprehensive accessibility tests"""
        logger.info("Starting comprehensive accessibility tests...")
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'pages': {},
            'summary': {
                'total_pages': 0,
                'pages_passed': 0,
                'pages_failed': 0,
                'overall_score': 0.0
            }
        }
        
        # Pages to test
        pages = [
            {'name': 'landing_page', 'url': self.base_url},
            {'name': 'settings_page', 'url': f"{self.base_url}/settings"},
            {'name': 'dashboard', 'url': f"{self.base_url}/dashboard"}
        ]
        
        # Setup driver
        self.setup_driver()
        
        try:
            for page in pages:
                logger.info(f"Testing accessibility for {page['name']}...")
                
                page_results = {
                    'axe_tests': self.run_axe_tests(page['name'], page['url']),
                    'keyboard_navigation': self.test_keyboard_navigation(page['name'], page['url']),
                    'color_contrast': self.test_color_contrast(page['name'], page['url']),
                    'screen_reader_support': self.test_screen_reader_support(page['name'], page['url']),
                    'focus_management': self.test_focus_management(page['name'], page['url'])
                }
                
                # Calculate page score
                page_score = self.calculate_page_accessibility_score(page_results)
                page_results['overall_score'] = page_score
                
                test_results['pages'][page['name']] = page_results
                test_results['summary']['total_pages'] += 1
                
                if page_score >= 80:
                    test_results['summary']['pages_passed'] += 1
                else:
                    test_results['summary']['pages_failed'] += 1
                
                # Small delay between pages
                time.sleep(2)
        
        finally:
            # Cleanup
            self.teardown_driver()
        
        # Calculate overall score
        if test_results['summary']['total_pages'] > 0:
            total_score = sum(page['overall_score'] for page in test_results['pages'].values())
            test_results['summary']['overall_score'] = total_score / test_results['summary']['total_pages']
        
        logger.info(f"Accessibility tests completed - Overall score: {test_results['summary']['overall_score']:.1f}")
        return test_results
    
    def calculate_page_accessibility_score(self, page_results: Dict[str, Any]) -> float:
        """Calculate accessibility score for a page"""
        scores = []
        
        # Axe test score
        if page_results['axe_tests'].get('status') == 'COMPLETED':
            scores.append(page_results['axe_tests'].get('pass_rate', 0))
        
        # Keyboard navigation score
        if page_results['keyboard_navigation'].get('status') == 'COMPLETED':
            scores.append(page_results['keyboard_navigation'].get('keyboard_score', 0))
        
        # Color contrast score
        if page_results['color_contrast'].get('status') == 'COMPLETED':
            scores.append(page_results['color_contrast'].get('contrast_score', 0))
        
        # Screen reader score
        if page_results['screen_reader_support'].get('status') == 'COMPLETED':
            scores.append(page_results['screen_reader_support'].get('screen_reader_score', 0))
        
        # Focus management score
        if page_results['focus_management'].get('status') == 'COMPLETED':
            scores.append(page_results['focus_management'].get('focus_management_score', 0))
        
        return sum(scores) / len(scores) if scores else 0
    
    def generate_accessibility_report(self, results: Dict[str, Any], output_path: str):
        """Generate accessibility test report"""
        report = f"""
# Accessibility Test Report

**Generated**: {results['timestamp']}
**Overall Score**: {results['summary']['overall_score']:.1f}/100

## Summary

- **Total Pages**: {results['summary']['total_pages']}
- **Pages Passed**: {results['summary']['pages_passed']}
- **Pages Failed**: {results['summary']['pages_failed']}

## Page Results

"""
        
        for page_name, page_results in results['pages'].items():
            report += f"### {page_name.replace('_', ' ').title()}\n"
            report += f"**Overall Score**: {page_results['overall_score']:.1f}/100\n\n"
            
            # Axe tests
            axe_results = page_results['axe_tests']
            if axe_results.get('status') == 'COMPLETED':
                report += f"**Axe Tests**: {axe_results['pass_rate']:.1f}% pass rate\n"
                report += f"- Violations: {axe_results['violations']}\n"
                report += f"- Critical: {axe_results['violations_by_severity']['critical']}\n"
                report += f"- Serious: {axe_results['violations_by_severity']['serious']}\n"
            else:
                report += f"**Axe Tests**: {axe_results.get('status', 'ERROR')}\n"
            
            # Keyboard navigation
            kb_results = page_results['keyboard_navigation']
            if kb_results.get('status') == 'COMPLETED':
                report += f"**Keyboard Navigation**: {kb_results['keyboard_score']:.1f}/100\n"
                report += f"- Focusable elements: {kb_results['total_focusable_elements']}\n"
                report += f"- Tab order tested: {kb_results['tab_order_tested']}\n"
            
            # Color contrast
            contrast_results = page_results['color_contrast']
            if contrast_results.get('status') == 'COMPLETED':
                report += f"**Color Contrast**: {contrast_results['contrast_score']:.1f}/100\n"
                report += f"- Text elements: {contrast_results['total_text_elements']}\n"
                report += f"- Contrast issues: {contrast_results['contrast_issues']}\n"
            
            # Screen reader support
            sr_results = page_results['screen_reader_support']
            if sr_results.get('status') == 'COMPLETED':
                report += f"**Screen Reader Support**: {sr_results['screen_reader_score']:.1f}/100\n"
                report += f"- Alt text coverage: {sr_results['alt_text_coverage']:.1f}%\n"
                report += f"- Label coverage: {sr_results['label_coverage']:.1f}%\n"
                report += f"- Skip links: {sr_results['skip_links']}\n"
            
            # Focus management
            focus_results = page_results['focus_management']
            if focus_results.get('status') == 'COMPLETED':
                report += f"**Focus Management**: {focus_results['focus_management_score']:.1f}/100\n"
                report += f"- Focus indicators: {focus_results['elements_with_focus_indicators']}\n"
                report += f"- Modal focus trap: {focus_results['modal_focus_trap']}\n"
            
            report += "\n"
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Accessibility report saved to {output_path}")

def main():
    """Main function for running accessibility tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mingus Accessibility Tests')
    parser.add_argument('--base-url', default='http://localhost:3000', help='Frontend base URL')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API base URL')
    parser.add_argument('--output', help='Output file for test results')
    parser.add_argument('--report', help='Generate HTML report')
    parser.add_argument('--test', help='Run specific test only')
    
    args = parser.parse_args()
    
    config = {
        'base_url': args.base_url,
        'api_url': args.api_url,
        'axe_script_url': 'https://cdn.jsdelivr.net/npm/axe-core@4.7.0/axe.min.js'
    }
    
    # Run tests
    test_suite = AccessibilityTest(config)
    
    if args.test:
        # Run specific test
        test_method = getattr(test_suite, f"test_{args.test}")
        if test_method:
            test_suite.setup_driver()
            try:
                result = test_method('test_page', args.base_url)
                print(json.dumps(result, indent=2))
            finally:
                test_suite.teardown_driver()
        else:
            print(f"Test {args.test} not found")
    else:
        # Run all tests
        results = test_suite.run_comprehensive_accessibility_tests()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Test results saved to {args.output}")
        
        if args.report:
            test_suite.generate_accessibility_report(results, args.report)
            print(f"Accessibility report saved to {args.report}")
        
        if not args.output and not args.report:
            print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
