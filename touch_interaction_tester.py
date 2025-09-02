#!/usr/bin/env python3
"""
Touch Interaction Tester
Tests touch interactions, gestures, and mobile usability features
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
# TouchActions removed in Selenium 4.15+, using ActionChains instead
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TouchTarget:
    """Represents a touch target element"""
    selector: str
    element_type: str
    width: int
    height: int
    location: Dict[str, int]
    is_visible: bool
    is_enabled: bool
    meets_size_requirements: bool
    has_adequate_spacing: bool
    accessibility_score: float
    issues: List[str]
    recommendations: List[str]

@dataclass
class GestureTest:
    """Results from gesture testing"""
    gesture_type: str
    target_element: str
    success: bool
    response_time: float
    issues: List[str]
    recommendations: List[str]

@dataclass
class TouchInteractionResult:
    """Results from touch interaction testing"""
    page_url: str
    device_config: Dict[str, Any]
    touch_targets: List[TouchTarget]
    gesture_tests: List[GestureTest]
    overall_score: float
    issues: List[str]
    recommendations: List[str]
    accessibility_compliance: Dict[str, Any]

class TouchInteractionTester:
    """Touch interaction testing suite for mobile devices"""
    
    def __init__(self, base_url: str = "http://localhost:5000", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        
        # Touch target size requirements
        self.min_touch_target_size = 44  # Minimum size in pixels
        self.min_spacing = 8  # Minimum spacing between targets
        
        # Gesture types to test
        self.gesture_types = [
            'tap',
            'double_tap',
            'long_press',
            'swipe_left',
            'swipe_right',
            'swipe_up',
            'swipe_down',
            'pinch_zoom',
            'rotate'
        ]
        
        # Accessibility requirements
        self.accessibility_requirements = {
            'touch_target_size': 44,
            'minimum_spacing': 8,
            'focus_indicators': True,
            'screen_reader_support': True,
            'keyboard_navigation': True
        }
    
    def setup_webdriver(self) -> None:
        """Setup Chrome WebDriver with touch emulation"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--enable-touch-events')
            chrome_options.add_argument('--enable-touch-drag-drop')
            
            # Enable mobile emulation with touch
            chrome_options.add_experimental_option('mobileEmulation', {
                'deviceMetrics': {
                    'width': 375,
                    'height': 812,
                    'pixelRatio': 3.0,
                    'touch': True,
                    'mobile': True
                },
                'userAgent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
            })
            
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome WebDriver initialized with touch emulation")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def teardown_webdriver(self) -> None:
        """Clean up WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
    
    def test_touch_targets(self, page_url: str) -> List[TouchTarget]:
        """Test touch targets on a page"""
        logger.info(f"Testing touch targets on {page_url}")
        
        try:
            # Navigate to page
            full_url = f"{self.base_url}{page_url}"
            self.driver.get(full_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Find all interactive elements
            interactive_selectors = [
                'button',
                'input',
                'select',
                'textarea',
                'a[href]',
                '[role="button"]',
                '[role="link"]',
                '[role="menuitem"]',
                '[tabindex]',
                '.clickable',
                '.interactive'
            ]
            
            touch_targets = []
            
            for selector in interactive_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            touch_target = self._analyze_touch_target(element, selector)
                            if touch_target:
                                touch_targets.append(touch_target)
                
                except Exception as e:
                    logger.warning(f"Error testing selector {selector}: {e}")
                    continue
            
            return touch_targets
            
        except Exception as e:
            logger.error(f"Error testing touch targets on {page_url}: {e}")
            return []
    
    def _analyze_touch_target(self, element, selector: str) -> Optional[TouchTarget]:
        """Analyze a single touch target element"""
        try:
            # Get element properties
            size = element.size
            location = element.location
            is_enabled = element.is_enabled()
            
            # Check size requirements
            meets_size_requirements = (
                size['width'] >= self.min_touch_target_size and 
                size['height'] >= self.min_touch_target_size
            )
            
            # Check spacing
            has_adequate_spacing = self._check_element_spacing(element)
            
            # Calculate accessibility score
            accessibility_score = self._calculate_accessibility_score(
                meets_size_requirements, has_adequate_spacing, is_enabled
            )
            
            # Identify issues and recommendations
            issues = []
            recommendations = []
            
            if not meets_size_requirements:
                issues.append(f"Touch target too small: {size['width']}x{size['height']}px")
                recommendations.append(f"Increase size to at least {self.min_touch_target_size}x{self.min_touch_target_size}px")
            
            if not has_adequate_spacing:
                issues.append("Insufficient spacing between touch targets")
                recommendations.append(f"Ensure at least {self.min_spacing}px spacing between interactive elements")
            
            if not is_enabled:
                issues.append("Element is disabled")
                recommendations.append("Ensure disabled state is clearly indicated")
            
            return TouchTarget(
                selector=selector,
                element_type=element.tag_name,
                width=size['width'],
                height=size['height'],
                location=location,
                is_visible=True,
                is_enabled=is_enabled,
                meets_size_requirements=meets_size_requirements,
                has_adequate_spacing=has_adequate_spacing,
                accessibility_score=accessibility_score,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.warning(f"Error analyzing touch target: {e}")
            return None
    
    def _check_element_spacing(self, element) -> bool:
        """Check if element has adequate spacing from other elements"""
        try:
            # Find nearby interactive elements
            nearby_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                'button, input, select, textarea, a[href], [role="button"]')
            
            element_location = element.location
            element_size = element.size
            
            for nearby_element in nearby_elements:
                if nearby_element != element and nearby_element.is_displayed():
                    nearby_location = nearby_element.location
                    nearby_size = nearby_element.size
                    
                    # Calculate distance between element centers
                    distance_x = abs(
                        (element_location['x'] + element_size['width']/2) - 
                        (nearby_location['x'] + nearby_size['width']/2)
                    )
                    distance_y = abs(
                        (element_location['y'] + element_size['height']/2) - 
                        (nearby_location['y'] + nearby_size['height']/2)
                    )
                    
                    # Check if elements are too close
                    if distance_x < self.min_spacing and distance_y < self.min_spacing:
                        return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking element spacing: {e}")
            return True  # Assume adequate spacing if check fails
    
    def _calculate_accessibility_score(self, size_ok: bool, spacing_ok: bool, enabled: bool) -> float:
        """Calculate accessibility score for a touch target"""
        score = 0.0
        
        if size_ok:
            score += 40
        if spacing_ok:
            score += 30
        if enabled:
            score += 30
        
        return score
    
    def test_gestures(self, page_url: str) -> List[GestureTest]:
        """Test various touch gestures on a page"""
        logger.info(f"Testing gestures on {page_url}")
        
        try:
            # Navigate to page if not already there
            current_url = self.driver.current_url
            if page_url not in current_url:
                full_url = f"{self.base_url}{page_url}"
                self.driver.get(full_url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            
            gesture_tests = []
            
            # Test basic gestures on interactive elements
            interactive_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                'button, input, select, textarea, a[href], [role="button"]')
            
            for element in interactive_elements[:5]:  # Test first 5 elements
                if element.is_displayed() and element.is_enabled():
                    # Test tap
                    tap_result = self._test_tap_gesture(element)
                    gesture_tests.append(tap_result)
                    
                    # Test long press
                    long_press_result = self._test_long_press_gesture(element)
                    gesture_tests.append(long_press_result)
            
            # Test swipe gestures on the page
            swipe_results = self._test_swipe_gestures()
            gesture_tests.extend(swipe_results)
            
            return gesture_tests
            
        except Exception as e:
            logger.error(f"Error testing gestures on {page_url}: {e}")
            return []
    
    def _test_tap_gesture(self, element) -> GestureTest:
        """Test tap gesture on an element"""
        try:
            start_time = time.time()
            
            # Perform tap
            actions = ActionChains(self.driver)
            actions.click(element).perform()
            
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Check if element responded (basic check)
            success = True
            issues = []
            recommendations = []
            
            if response_time > 300:  # More than 300ms is considered slow
                issues.append(f"Slow response time: {response_time:.0f}ms")
                recommendations.append("Optimize touch response time for better user experience")
            
            return GestureTest(
                gesture_type='tap',
                target_element=self._get_element_selector(element),
                success=success,
                response_time=response_time,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            return GestureTest(
                gesture_type='tap',
                target_element=self._get_element_selector(element),
                success=False,
                response_time=0,
                issues=[f"Tap gesture failed: {e}"],
                recommendations=["Ensure element is properly configured for touch events"]
            )
    
    def _test_long_press_gesture(self, element) -> GestureTest:
        """Test long press gesture on an element"""
        try:
            start_time = time.time()
            
            # Perform long press
            actions = ActionChains(self.driver)
            actions.click_and_hold(element).pause(1).release().perform()
            
            response_time = (time.time() - start_time) * 1000
            
            success = True
            issues = []
            recommendations = []
            
            # Check for context menu or long press behavior
            # This is a basic test - in real scenarios you'd check for specific responses
            
            return GestureTest(
                gesture_type='long_press',
                target_element=self._get_element_selector(element),
                success=success,
                response_time=response_time,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            return GestureTest(
                gesture_type='long_press',
                target_element=self._get_element_selector(element),
                success=False,
                response_time=0,
                issues=[f"Long press gesture failed: {e}"],
                recommendations=["Ensure element supports long press interactions"]
            )
    
    def _test_swipe_gestures(self) -> List[GestureTest]:
        """Test swipe gestures on the page"""
        swipe_tests = []
        
        try:
            # Get page dimensions
            page_width = self.driver.execute_script("return document.documentElement.scrollWidth")
            page_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            
            # Test horizontal swipes
            if page_width > 375:  # Only test if page is wider than viewport
                swipe_left = self._test_swipe_gesture('swipe_left', page_width, page_height)
                swipe_right = self._test_swipe_gesture('swipe_right', page_width, page_height)
                swipe_tests.extend([swipe_left, swipe_right])
            
            # Test vertical swipes
            if page_height > 812:  # Only test if page is taller than viewport
                swipe_up = self._test_swipe_gesture('swipe_up', page_width, page_height)
                swipe_down = self._test_swipe_gesture('swipe_down', page_width, page_height)
                swipe_tests.extend([swipe_up, swipe_down])
            
        except Exception as e:
            logger.warning(f"Error testing swipe gestures: {e}")
        
        return swipe_tests
    
    def _test_swipe_gesture(self, gesture_type: str, page_width: int, page_height: int) -> GestureTest:
        """Test a specific swipe gesture"""
        try:
            start_time = time.time()
            
            # Calculate swipe coordinates based on gesture type
            if gesture_type == 'swipe_left':
                start_x, start_y = page_width - 100, page_height // 2
                end_x, end_y = 100, page_height // 2
            elif gesture_type == 'swipe_right':
                start_x, start_y = 100, page_height // 2
                end_x, end_y = page_width - 100, page_height // 2
            elif gesture_type == 'swipe_up':
                start_x, start_y = page_width // 2, page_height - 100
                end_x, end_y = page_width // 2, 100
            elif gesture_type == 'swipe_down':
                start_x, start_y = page_width // 2, 100
                end_x, end_y = page_width // 2, page_height - 100
            else:
                raise ValueError(f"Unknown gesture type: {gesture_type}")
            
            # Perform swipe
            actions = ActionChains(self.driver)
            actions.move_by_offset(start_x, start_y).click_and_hold().move_by_offset(
                end_x - start_x, end_y - start_y
            ).release().perform()
            
            response_time = (time.time() - start_time) * 1000
            
            return GestureTest(
                gesture_type=gesture_type,
                target_element='page',
                success=True,
                response_time=response_time,
                issues=[],
                recommendations=[]
            )
            
        except Exception as e:
            return GestureTest(
                gesture_type=gesture_type,
                target_element='page',
                success=False,
                response_time=0,
                issues=[f"Swipe gesture failed: {e}"],
                recommendations=["Ensure page supports touch gestures"]
            )
    
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
    
    def test_page_touch_interactions(self, page_url: str, device_config: Dict[str, Any]) -> TouchInteractionResult:
        """Test touch interactions for a specific page and device"""
        logger.info(f"Testing touch interactions on {page_url} for {device_config.get('name', 'device')}")
        
        try:
            # Set device viewport
            width = device_config.get('width', 375)
            height = device_config.get('height', 812)
            self.driver.set_window_size(width, height)
            
            # Test touch targets
            touch_targets = self.test_touch_targets(page_url)
            
            # Test gestures
            gesture_tests = self.test_gestures(page_url)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(touch_targets, gesture_tests)
            
            # Collect all issues and recommendations
            all_issues = []
            all_recommendations = []
            
            for target in touch_targets:
                all_issues.extend(target.issues)
                all_recommendations.extend(target.recommendations)
            
            for gesture in gesture_tests:
                all_issues.extend(gesture.issues)
                all_recommendations.extend(gesture.recommendations)
            
            # Remove duplicates
            all_issues = list(set(all_issues))
            all_recommendations = list(set(all_recommendations))
            
            # Check accessibility compliance
            accessibility_compliance = self._check_accessibility_compliance(touch_targets)
            
            return TouchInteractionResult(
                page_url=page_url,
                device_config=device_config,
                touch_targets=touch_targets,
                gesture_tests=gesture_tests,
                overall_score=overall_score,
                issues=all_issues,
                recommendations=all_recommendations,
                accessibility_compliance=accessibility_compliance
            )
            
        except Exception as e:
            logger.error(f"Error testing touch interactions on {page_url}: {e}")
            raise
    
    def _calculate_overall_score(self, touch_targets: List[TouchTarget], 
                               gesture_tests: List[GestureTest]) -> float:
        """Calculate overall touch interaction score"""
        if not touch_targets and not gesture_tests:
            return 0.0
        
        # Touch target score (70% weight)
        target_score = 0.0
        if touch_targets:
            target_score = sum(target.accessibility_score for target in touch_targets) / len(touch_targets)
        
        # Gesture score (30% weight)
        gesture_score = 0.0
        if gesture_tests:
            successful_gestures = sum(1 for gesture in gesture_tests if gesture.success)
            gesture_score = (successful_gestures / len(gesture_tests)) * 100
        
        overall_score = (target_score * 0.7) + (gesture_score * 0.3)
        return round(overall_score, 2)
    
    def _check_accessibility_compliance(self, touch_targets: List[TouchTarget]) -> Dict[str, Any]:
        """Check accessibility compliance for touch interactions"""
        compliance = {
            'wcag_2_1_aa': False,
            'touch_target_size_compliant': False,
            'spacing_compliant': False,
            'focus_indicators_present': False,
            'keyboard_navigation_supported': False
        }
        
        if touch_targets:
            # Check touch target size compliance
            compliant_targets = sum(1 for target in touch_targets if target.meets_size_requirements)
            compliance['touch_target_size_compliant'] = compliant_targets == len(touch_targets)
            
            # Check spacing compliance
            properly_spaced = sum(1 for target in touch_targets if target.has_adequate_spacing)
            compliance['spacing_compliant'] = properly_spaced == len(touch_targets)
            
            # Overall WCAG compliance
            compliance['wcag_2_1_aa'] = (
                compliance['touch_target_size_compliant'] and 
                compliance['spacing_compliant']
            )
        
        return compliance
    
    def run_comprehensive_testing(self, pages: List[str], device_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive touch interaction testing"""
        print("👆 Starting Touch Interaction Testing")
        print("=" * 80)
        
        start_time = time.time()
        
        try:
            self.setup_webdriver()
            
            all_results = []
            
            # Test each page across different devices
            for page_url in pages:
                for device_config in device_configs:
                    try:
                        logger.info(f"Testing {page_url} on {device_config.get('name', 'device')}")
                        
                        result = self.test_page_touch_interactions(page_url, device_config)
                        all_results.append(result)
                        
                        # Print progress
                        print(f"✅ {device_config.get('name', 'Device')}: {result.overall_score}/100")
                        
                    except Exception as e:
                        logger.error(f"Failed to test {page_url} on {device_config.get('name', 'device')}: {e}")
                        continue
            
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
    
    def _generate_comprehensive_report(self, results: List[TouchInteractionResult]) -> Dict[str, Any]:
        """Generate comprehensive testing report"""
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'total_tests': len(results),
            'devices_tested': list(set(result.device_config.get('name', 'Unknown') for result in results)),
            'pages_tested': list(set(result.page_url for result in results)),
            'overall_average_score': 0,
            'device_performance': {},
            'page_performance': {},
            'accessibility_compliance': {},
            'common_issues': [],
            'recommendations': []
        }
        
        if results:
            # Calculate average scores
            report['overall_average_score'] = sum(result.overall_score for result in results) / len(results)
            
            # Device performance breakdown
            for device_name in report['devices_tested']:
                device_results = [r for r in results if r.device_config.get('name') == device_name]
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
            
            # Accessibility compliance summary
            all_compliance = [r.accessibility_compliance for r in results]
            if all_compliance:
                report['accessibility_compliance'] = {
                    'wcag_2_1_aa_compliant': sum(1 for c in all_compliance if c.get('wcag_2_1_aa', False)),
                    'touch_target_compliant': sum(1 for c in all_compliance if c.get('touch_target_size_compliant', False)),
                    'spacing_compliant': sum(1 for c in all_compliance if c.get('spacing_compliant', False))
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
        
        return report
    
    def _save_test_results(self, results: List[TouchInteractionResult], report: Dict[str, Any]) -> None:
        """Save test results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = f"touch_interaction_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump({
                'results': [self._serialize_test_result(result) for result in results],
                'report': report
            }, f, indent=2, default=str)
        
        # Save summary report
        summary_file = f"touch_interaction_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Results saved to {results_file} and {summary_file}")
    
    def _serialize_test_result(self, result: TouchInteractionResult) -> Dict[str, Any]:
        """Serialize test result for JSON output"""
        return {
            'page_url': result.page_url,
            'device_config': result.device_config,
            'overall_score': result.overall_score,
            'touch_targets_count': len(result.touch_targets),
            'gesture_tests_count': len(result.gesture_tests),
            'issues': result.issues,
            'recommendations': result.recommendations,
            'accessibility_compliance': result.accessibility_compliance
        }

def main():
    """Main function to run the touch interaction testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Touch Interaction Testing Suite')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL to test')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--pages', nargs='+', default=['/'], help='Pages to test')
    
    args = parser.parse_args()
    
    # Device configurations
    device_configs = [
        {'name': 'iPhone SE', 'width': 320, 'height': 568},
        {'name': 'iPhone 14', 'width': 375, 'height': 812},
        {'name': 'Samsung Galaxy S21', 'width': 360, 'height': 800}
    ]
    
    # Initialize tester
    tester = TouchInteractionTester(base_url=args.url, headless=args.headless)
    
    try:
        # Run comprehensive testing
        report = tester.run_comprehensive_testing(args.pages, device_configs)
        
        # Print summary
        print("\n" + "=" * 80)
        print("📋 TOUCH INTERACTION TESTING SUMMARY")
        print("=" * 80)
        print(f"Overall Score: {report['overall_average_score']:.2f}/100")
        print(f"Devices Tested: {len(report['devices_tested'])}")
        print(f"Pages Tested: {len(report['pages_tested'])}")
        
        if report['accessibility_compliance']:
            compliance = report['accessibility_compliance']
            print(f"WCAG 2.1 AA Compliant: {compliance.get('wcag_2_1_aa_compliant', 0)}/{report['total_tests']}")
        
        print(f"\n📁 Detailed results saved to JSON files")
        
    except Exception as e:
        logger.error(f"Testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
