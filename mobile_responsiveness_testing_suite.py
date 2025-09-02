#!/usr/bin/env python3
"""
MINGUS Comprehensive Mobile Responsiveness Testing Suite
Tests mobile responsiveness across multiple device sizes, CSS media queries, touch interactions, and usability
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path
import re
import cssutils
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
# TouchActions removed in Selenium 4.15+, using ActionChains instead

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DeviceConfig:
    """Device configuration for testing"""
    name: str
    width: int
    height: int
    pixel_ratio: float
    user_agent: str
    touch_enabled: bool
    category: str

@dataclass
class CSSMediaQuery:
    """CSS media query information"""
    query: str
    min_width: Optional[int]
    max_width: Optional[int]
    orientation: Optional[str]
    device_type: Optional[str]
    is_valid: bool
    issues: List[str]

@dataclass
class TouchTargetTest:
    """Touch target test results"""
    element_selector: str
    element_type: str
    width: int
    height: int
    min_size_met: bool
    spacing_adequate: bool
    issues: List[str]
    recommendations: List[str]

@dataclass
class ResponsivenessTest:
    """Responsiveness test results"""
    device: DeviceConfig
    page_url: str
    viewport_size: Tuple[int, int]
    css_breakpoints: List[CSSMediaQuery]
    touch_targets: List[TouchTargetTest]
    navigation_test: Dict[str, Any]
    form_usability: Dict[str, Any]
    overall_score: float
    issues: List[str]
    recommendations: List[str]

class MobileResponsivenessTester:
    """Comprehensive mobile responsiveness testing suite"""
    
    def __init__(self, base_url: str = "http://localhost:5000", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.test_results = []
        self.driver = None
        
        # Device configurations for comprehensive testing
        self.devices = {
            'iPhone SE': DeviceConfig(
                name='iPhone SE',
                width=320,
                height=568,
                pixel_ratio=2.0,
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                touch_enabled=True,
                category='small_mobile'
            ),
            'iPhone 14': DeviceConfig(
                name='iPhone 14',
                width=375,
                height=812,
                pixel_ratio=3.0,
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                touch_enabled=True,
                category='standard_mobile'
            ),
            'iPhone 14 Plus': DeviceConfig(
                name='iPhone 14 Plus',
                width=428,
                height=926,
                pixel_ratio=3.0,
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
                touch_enabled=True,
                category='large_mobile'
            ),
            'Samsung Galaxy S21': DeviceConfig(
                name='Samsung Galaxy S21',
                width=360,
                height=800,
                pixel_ratio=3.0,
                user_agent='Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36',
                touch_enabled=True,
                category='android_mobile'
            ),
            'Google Pixel': DeviceConfig(
                name='Google Pixel',
                width=411,
                height=731,
                pixel_ratio=2.75,
                user_agent='Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36',
                touch_enabled=True,
                category='android_mobile'
            ),
            'Budget Android': DeviceConfig(
                name='Budget Android',
                width=320,
                height=640,
                pixel_ratio=1.5,
                user_agent='Mozilla/5.0 (Linux; Android 10; SM-A505FN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36',
                touch_enabled=True,
                category='budget_mobile'
            ),
            'iPad': DeviceConfig(
                name='iPad',
                width=768,
                height=1024,
                pixel_ratio=2.0,
                user_agent='Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                touch_enabled=True,
                category='tablet'
            )
        }
        
        # Pages to test
        self.pages_to_test = [
            "/",
            "/landing",
            "/health",
            "/budget",
            "/profile",
            "/articles",
            "/assessments",
            "/payment",
            "/subscription"
        ]
        
        # CSS breakpoints to validate
        self.expected_breakpoints = {
            'mobile': 320,
            'tablet': 768,
            'desktop': 1024,
            'large_desktop': 1440
        }
    
    def setup_webdriver(self) -> None:
        """Setup Chrome WebDriver with mobile emulation capabilities"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--remote-debugging-port=9222')
            
            # Enable mobile emulation
            chrome_options.add_experimental_option('mobileEmulation', {
                'deviceMetrics': {
                    'width': 375,
                    'height': 812,
                    'pixelRatio': 3.0
                },
                'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
            })
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def teardown_webdriver(self) -> None:
        """Clean up WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def test_css_media_queries(self, css_content: str) -> List[CSSMediaQuery]:
        """Test and validate CSS media queries"""
        media_queries = []
        
        # Parse CSS content for media queries
        css_rules = cssutils.parseString(css_content)
        
        for rule in css_rules:
            if rule.type == rule.MEDIA_RULE:
                query = rule.media.mediaText
                media_query = CSSMediaQuery(
                    query=query,
                    min_width=None,
                    max_width=None,
                    orientation=None,
                    device_type=None,
                    is_valid=True,
                    issues=[]
                )
                
                # Parse media query conditions
                for condition in rule.media:
                    if condition.name == 'min-width':
                        try:
                            media_query.min_width = int(condition.value.replace('px', ''))
                        except ValueError:
                            media_query.issues.append(f"Invalid min-width value: {condition.value}")
                            media_query.is_valid = False
                    
                    elif condition.name == 'max-width':
                        try:
                            media_query.max_width = int(condition.value.replace('px', ''))
                        except ValueError:
                            media_query.issues.append(f"Invalid max-width value: {condition.value}")
                            media_query.is_valid = False
                    
                    elif condition.name == 'orientation':
                        media_query.orientation = condition.value
                    
                    elif condition.name == 'device-type':
                        media_query.device_type = condition.value
                
                # Validate breakpoint logic
                if media_query.min_width and media_query.max_width:
                    if media_query.min_width >= media_query.max_width:
                        media_query.issues.append("min-width cannot be greater than or equal to max-width")
                        media_query.is_valid = False
                
                media_queries.append(media_query)
        
        return media_queries
    
    def test_touch_targets(self, device: DeviceConfig) -> List[TouchTargetTest]:
        """Test touch target sizes and spacing"""
        touch_targets = []
        
        try:
            # Find all interactive elements
            interactive_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                'button, input, select, textarea, a[href], [role="button"], [tabindex]')
            
            for element in interactive_elements:
                try:
                    # Get element dimensions
                    size = element.size
                    location = element.location
                    
                    # Check if element is visible
                    if not element.is_displayed():
                        continue
                    
                    # Test touch target size (minimum 44x44px for mobile)
                    min_size_met = size['width'] >= 44 and size['height'] >= 44
                    
                    # Check spacing between elements (minimum 8px)
                    spacing_adequate = True
                    issues = []
                    recommendations = []
                    
                    if not min_size_met:
                        issues.append(f"Touch target too small: {size['width']}x{size['height']}px (minimum 44x44px)")
                        recommendations.append("Increase element dimensions to meet minimum touch target size")
                    
                    # Check if element is properly spaced from others
                    for other_element in interactive_elements:
                        if other_element != element and other_element.is_displayed():
                            other_location = other_element.location
                            other_size = other_element.size
                            
                            # Calculate distance between elements
                            distance_x = abs((location['x'] + size['width']/2) - (other_location['x'] + other_size['width']/2))
                            distance_y = abs((location['y'] + size['height']/2) - (other_location['y'] + other_size['height']/2))
                            
                            if distance_x < 8 and distance_y < 8:
                                spacing_adequate = False
                                issues.append(f"Insufficient spacing with element {other_element.tag_name}")
                                recommendations.append("Increase spacing between interactive elements to at least 8px")
                    
                    touch_target = TouchTargetTest(
                        element_selector=self._get_element_selector(element),
                        element_type=element.tag_name,
                        width=size['width'],
                        height=size['height'],
                        min_size_met=min_size_met,
                        spacing_adequate=spacing_adequate,
                        issues=issues,
                        recommendations=recommendations
                    )
                    
                    touch_targets.append(touch_target)
                    
                except Exception as e:
                    logger.warning(f"Error testing touch target for element: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error during touch target testing: {e}")
        
        return touch_targets
    
    def test_mobile_navigation(self, device: DeviceConfig) -> Dict[str, Any]:
        """Test mobile navigation functionality"""
        navigation_test = {
            'hamburger_menu_accessible': False,
            'navigation_items_visible': False,
            'submenu_accessible': False,
            'back_navigation_works': False,
            'breadcrumbs_visible': False,
            'search_functionality': False,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Test hamburger menu
            hamburger_menu = self.driver.find_elements(By.CSS_SELECTOR, 
                '[aria-label*="menu"], [aria-label*="Menu"], .hamburger, .menu-toggle, [data-testid*="menu"]')
            
            if hamburger_menu:
                navigation_test['hamburger_menu_accessible'] = True
                
                # Test menu interaction
                try:
                    hamburger_menu[0].click()
                    time.sleep(1)
                    
                    # Check if navigation items are visible
                    nav_items = self.driver.find_elements(By.CSS_SELECTOR, 'nav a, .nav-item, .menu-item')
                    if nav_items:
                        navigation_test['navigation_items_visible'] = True
                    
                    # Test submenu if exists
                    submenus = self.driver.find_elements(By.CSS_SELECTOR, '.submenu, .dropdown-menu')
                    if submenus:
                        navigation_test['submenu_accessible'] = True
                    
                except Exception as e:
                    navigation_test['issues'].append(f"Menu interaction failed: {e}")
            
            # Test search functionality
            search_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="search"], input[placeholder*="search"], .search-input')
            if search_inputs:
                navigation_test['search_functionality'] = True
            
            # Test breadcrumbs
            breadcrumbs = self.driver.find_elements(By.CSS_SELECTOR, '.breadcrumbs, .breadcrumb, [aria-label*="breadcrumb"]')
            if breadcrumbs:
                navigation_test['breadcrumbs_visible'] = True
            
        except Exception as e:
            navigation_test['issues'].append(f"Navigation testing error: {e}")
        
        return navigation_test
    
    def test_form_usability(self, device: DeviceConfig) -> Dict[str, Any]:
        """Test form usability on mobile devices"""
        form_test = {
            'input_sizes_adequate': False,
            'labels_visible': False,
            'error_messages_clear': False,
            'submit_button_accessible': False,
            'form_validation_works': False,
            'keyboard_navigation': False,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Find forms
            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            
            for form in forms:
                try:
                    # Test input sizes
                    inputs = form.find_elements(By.CSS_SELECTOR, 'input, textarea, select')
                    
                    for input_elem in inputs:
                        if input_elem.is_displayed():
                            size = input_elem.size
                            
                            # Check if input is large enough for mobile
                            if size['height'] >= 44:
                                form_test['input_sizes_adequate'] = True
                            else:
                                form_test['issues'].append(f"Input too small: {size['height']}px height")
                                form_test['recommendations'].append("Increase input height to at least 44px for mobile")
                    
                    # Test labels
                    labels = form.find_elements(By.TAG_NAME, 'label')
                    if labels:
                        form_test['labels_visible'] = True
                    
                    # Test submit button
                    submit_buttons = form.find_elements(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
                    if submit_buttons:
                        form_test['submit_button_accessible'] = True
                        
                        # Check submit button size
                        submit_size = submit_buttons[0].size
                        if submit_size['width'] < 44 or submit_size['height'] < 44:
                            form_test['issues'].append("Submit button too small for mobile")
                            form_test['recommendations'].append("Increase submit button size to at least 44x44px")
                    
                except Exception as e:
                    form_test['issues'].append(f"Form testing error: {e}")
            
        except Exception as e:
            form_test['issues'].append(f"Form usability testing error: {e}")
        
        return form_test
    
    def test_responsive_design(self, device: DeviceConfig, page_url: str) -> ResponsivenessTest:
        """Test responsive design for a specific device and page"""
        logger.info(f"Testing {device.name} on {page_url}")
        
        try:
            # Set device viewport
            self.driver.set_window_size(device.width, device.height)
            self.driver.execute_script(f"document.documentElement.style.setProperty('--device-width', '{device.width}px');")
            
            # Navigate to page
            full_url = f"{self.base_url}{page_url}"
            self.driver.get(full_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Test CSS media queries
            css_content = self._extract_css_content()
            css_breakpoints = self.test_css_media_queries(css_content)
            
            # Test touch targets
            touch_targets = self.test_touch_targets(device)
            
            # Test navigation
            navigation_test = self.test_mobile_navigation(device)
            
            # Test form usability
            form_usability = self.test_form_usability(device)
            
            # Calculate overall score
            overall_score = self._calculate_responsiveness_score(
                css_breakpoints, touch_targets, navigation_test, form_usability
            )
            
            # Generate issues and recommendations
            issues = []
            recommendations = []
            
            for target in touch_targets:
                issues.extend(target.issues)
                recommendations.extend(target.recommendations)
            
            issues.extend(navigation_test['issues'])
            recommendations.extend(navigation_test['recommendations'])
            
            issues.extend(form_usability['issues'])
            recommendations.extend(form_usability['recommendations'])
            
            # Remove duplicates
            issues = list(set(issues))
            recommendations = list(set(recommendations))
            
            test_result = ResponsivenessTest(
                device=device,
                page_url=page_url,
                viewport_size=(device.width, device.height),
                css_breakpoints=css_breakpoints,
                touch_targets=touch_targets,
                navigation_test=navigation_test,
                form_usability=form_usability,
                overall_score=overall_score,
                issues=issues,
                recommendations=recommendations
            )
            
            return test_result
            
        except Exception as e:
            logger.error(f"Error testing responsive design for {device.name} on {page_url}: {e}")
            raise
    
    def _extract_css_content(self) -> str:
        """Extract CSS content from the current page"""
        try:
            # Get all stylesheets
            stylesheets = self.driver.find_elements(By.TAG_NAME, 'link[rel="stylesheet"]')
            css_content = ""
            
            for stylesheet in stylesheets:
                try:
                    href = stylesheet.get_attribute('href')
                    if href and href.startswith('http'):
                        response = requests.get(href)
                        if response.status_code == 200:
                            css_content += response.text + "\n"
                except Exception as e:
                    logger.warning(f"Could not fetch stylesheet {href}: {e}")
            
            # Get inline styles
            inline_styles = self.driver.find_elements(By.TAG_NAME, 'style')
            for style in inline_styles:
                css_content += style.get_attribute('innerHTML') + "\n"
            
            return css_content
            
        except Exception as e:
            logger.error(f"Error extracting CSS content: {e}")
            return ""
    
    def _get_element_selector(self, element) -> str:
        """Generate a CSS selector for an element"""
        try:
            if element.get_attribute('id'):
                return f"#{element.get_attribute('id')}"
            elif element.get_attribute('class'):
                classes = ' '.join(element.get_attribute('class').split())
                return f".{classes}"
            else:
                return element.tag_name
        except:
            return element.tag_name
    
    def _calculate_responsiveness_score(self, css_breakpoints: List[CSSMediaQuery], 
                                     touch_targets: List[TouchTargetTest],
                                     navigation_test: Dict[str, Any],
                                     form_usability: Dict[str, Any]) -> float:
        """Calculate overall responsiveness score"""
        total_score = 0
        max_score = 100
        
        # CSS breakpoints score (25 points)
        valid_breakpoints = sum(1 for bp in css_breakpoints if bp.is_valid)
        total_breakpoints = len(css_breakpoints) if css_breakpoints else 1
        css_score = (valid_breakpoints / total_breakpoints) * 25
        total_score += css_score
        
        # Touch targets score (30 points)
        if touch_targets:
            valid_targets = sum(1 for target in touch_targets if target.min_size_met and target.spacing_adequate)
            touch_score = (valid_targets / len(touch_targets)) * 30
            total_score += touch_score
        else:
            total_score += 15  # Partial score if no touch targets found
        
        # Navigation score (25 points)
        nav_score = 0
        if navigation_test['hamburger_menu_accessible']:
            nav_score += 5
        if navigation_test['navigation_items_visible']:
            nav_score += 5
        if navigation_test['search_functionality']:
            nav_score += 5
        if navigation_test['breadcrumbs_visible']:
            nav_score += 5
        if navigation_test['submenu_accessible']:
            nav_score += 5
        
        total_score += nav_score
        
        # Form usability score (20 points)
        form_score = 0
        if form_usability['input_sizes_adequate']:
            form_score += 5
        if form_usability['labels_visible']:
            form_score += 5
        if form_usability['submit_button_accessible']:
            form_score += 5
        if form_usability['form_validation_works']:
            form_score += 5
        
        total_score += form_score
        
        return round(total_score, 2)
    
    def run_comprehensive_testing(self) -> Dict[str, Any]:
        """Run comprehensive mobile responsiveness testing"""
        print("📱 Starting MINGUS Comprehensive Mobile Responsiveness Testing")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            self.setup_webdriver()
            
            all_results = []
            
            # Test each page across different devices
            for page_url in self.pages_to_test:
                page_results = []
                
                for device_name, device_config in self.devices.items():
                    try:
                        logger.info(f"Testing {device_name} on {page_url}")
                        
                        test_result = self.test_responsive_design(device_config, page_url)
                        page_results.append(test_result)
                        
                        # Print progress
                        print(f"✅ {device_name}: {test_result.overall_score}/100")
                        
                    except Exception as e:
                        logger.error(f"Failed to test {device_name} on {page_url}: {e}")
                        continue
                
                all_results.extend(page_results)
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(all_results)
            
            # Save results
            self._save_test_results(all_results, report)
            
            print(f"\n🎯 Testing completed in {time.time() - start_time:.2f} seconds")
            print(f"📊 Total tests run: {len(all_results)}")
            print(f"📈 Average score: {report['overall_average_score']:.2f}/100")
            
            return report
            
        except Exception as e:
            logger.error(f"Comprehensive testing failed: {e}")
            raise
        finally:
            self.teardown_webdriver()
    
    def _generate_comprehensive_report(self, results: List[ResponsivenessTest]) -> Dict[str, Any]:
        """Generate comprehensive testing report"""
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'total_tests': len(results),
            'devices_tested': list(set(result.device.name for result in results)),
            'pages_tested': list(set(result.page_url for result in results)),
            'overall_average_score': 0,
            'device_performance': {},
            'page_performance': {},
            'common_issues': [],
            'critical_issues': [],
            'recommendations': []
        }
        
        if results:
            # Calculate average scores
            report['overall_average_score'] = sum(result.overall_score for result in results) / len(results)
            
            # Device performance breakdown
            for device_name in report['devices_tested']:
                device_results = [r for r in results if r.device.name == device_name]
                if device_results:
                    avg_score = sum(r.overall_score for r in device_results) / len(device_results)
                    report['device_performance'][device_name] = {
                        'average_score': round(avg_score, 2),
                        'tests_run': len(device_results)
                    }
            
            # Page performance breakdown
            for page_url in report['pages_tested']:
                page_results = [r for r in results if r.page_url == page_url]
                if page_results:
                    avg_score = sum(r.overall_score for r in page_results) / len(page_results)
                    report['page_performance'][page_url] = {
                        'average_score': round(avg_score, 2),
                        'tests_run': len(page_results)
                    }
            
            # Collect common issues and recommendations
            all_issues = []
            all_recommendations = []
            
            for result in results:
                all_issues.extend(result.issues)
                all_recommendations.extend(result.recommendations)
            
            # Count issue frequency
            from collections import Counter
            issue_counts = Counter(all_issues)
            recommendation_counts = Counter(all_recommendations)
            
            report['common_issues'] = [{'issue': issue, 'count': count} for issue, count in issue_counts.most_common(10)]
            report['recommendations'] = [{'recommendation': rec, 'count': count} for rec, count in recommendation_counts.most_common(10)]
            
            # Identify critical issues (appearing in more than 50% of tests)
            critical_threshold = len(results) * 0.5
            report['critical_issues'] = [issue for issue, count in issue_counts.items() if count > critical_threshold]
        
        return report
    
    def _save_test_results(self, results: List[ResponsivenessTest], report: Dict[str, Any]) -> None:
        """Save test results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = f"mobile_responsiveness_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'results': [self._serialize_test_result(result) for result in results],
                'report': report
            }, f, indent=2, default=str)
        
        # Save summary report
        summary_file = f"mobile_responsiveness_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Results saved to {results_file} and {summary_file}")
    
    def _serialize_test_result(self, result: ResponsivenessTest) -> Dict[str, Any]:
        """Serialize test result for JSON output"""
        return {
            'device': {
                'name': result.device.name,
                'width': result.device.width,
                'height': result.device.height,
                'category': result.device.category
            },
            'page_url': result.page_url,
            'viewport_size': result.viewport_size,
            'overall_score': result.overall_score,
            'issues': result.issues,
            'recommendations': result.recommendations,
            'touch_targets_count': len(result.touch_targets),
            'css_breakpoints_count': len(result.css_breakpoints)
        }

def main():
    """Main function to run the testing suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MINGUS Mobile Responsiveness Testing Suite')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL to test')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--pages', nargs='+', help='Specific pages to test')
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = MobileResponsivenessTester(base_url=args.url, headless=args.headless)
    
    # Override pages if specified
    if args.pages:
        tester.pages_to_test = args.pages
    
    try:
        # Run comprehensive testing
        report = tester.run_comprehensive_testing()
        
        # Print summary
        print("\n" + "=" * 80)
        print("📋 TESTING SUMMARY")
        print("=" * 80)
        print(f"Overall Score: {report['overall_average_score']:.2f}/100")
        print(f"Devices Tested: {len(report['devices_tested'])}")
        print(f"Pages Tested: {len(report['pages_tested'])}")
        
        if report['critical_issues']:
            print(f"\n🚨 Critical Issues Found: {len(report['critical_issues'])}")
            for issue in report['critical_issues'][:3]:
                print(f"  • {issue}")
        
        if report['recommendations']:
            print(f"\n💡 Top Recommendations:")
            for rec in report['recommendations'][:3]:
                print(f"  • {rec['recommendation']}")
        
        print(f"\n📁 Detailed results saved to JSON files")
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
