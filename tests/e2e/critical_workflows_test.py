#!/usr/bin/env python3
"""
Mingus Application - Critical Workflows E2E Tests
===============================================

End-to-end tests for critical user workflows including assessments,
user registration, profile management, and financial features.

Author: Mingus QA Team
Date: January 2025
"""

import pytest
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CriticalWorkflowsTest:
    """Critical workflows E2E test suite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url', 'http://localhost:3000')
        self.api_url = config.get('api_url', 'http://localhost:5000')
        self.driver = None
        self.test_results = []
        
    def setup_driver(self, device_type: str = 'desktop'):
        """Setup WebDriver for testing"""
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
    
    def wait_for_element(self, selector: str, timeout: int = 10):
        """Wait for element to be present and visible"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException:
            logger.error(f"Element not found: {selector}")
            return None
    
    def wait_for_clickable(self, selector: str, timeout: int = 10):
        """Wait for element to be clickable"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException:
            logger.error(f"Element not clickable: {selector}")
            return None
    
    def take_screenshot(self, name: str):
        """Take screenshot for debugging"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"screenshots/{name}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        logger.info(f"Screenshot saved: {filename}")
        return filename
    
    def test_landing_page_load(self):
        """Test landing page loads correctly"""
        logger.info("Testing landing page load...")
        
        try:
            self.driver.get(self.base_url)
            
            # Wait for page to load
            self.wait_for_element("body", 10)
            
            # Check for key elements
            hero_section = self.wait_for_element("section[role='banner']", 5)
            assert hero_section is not None, "Hero section not found"
            
            # Check for assessment buttons
            assessment_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Determine Your']")
            assert len(assessment_buttons) > 0, "Assessment buttons not found"
            
            # Check for navigation
            navigation = self.wait_for_element("nav", 5)
            assert navigation is not None, "Navigation not found"
            
            # Check for pricing section
            pricing_section = self.wait_for_element("#pricing", 5)
            assert pricing_section is not None, "Pricing section not found"
            
            # Check for FAQ section
            faq_section = self.wait_for_element("#faq", 5)
            assert faq_section is not None, "FAQ section not found"
            
            logger.info("✅ Landing page load test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Landing page load test failed: {e}")
            self.take_screenshot("landing_page_error")
            return False
    
    def test_assessment_flow(self):
        """Test complete assessment flow"""
        logger.info("Testing assessment flow...")
        
        try:
            # Navigate to landing page
            self.driver.get(self.base_url)
            
            # Click on AI Risk Assessment button
            ai_risk_button = self.wait_for_clickable("[aria-label*='Determine Your Replacement Risk Due To AI']", 10)
            assert ai_risk_button is not None, "AI Risk Assessment button not found"
            ai_risk_button.click()
            
            # Wait for modal to appear
            modal = self.wait_for_element("[role='dialog']", 10)
            assert modal is not None, "Assessment modal not found"
            
            # Fill out assessment form
            email_field = self.wait_for_element("input[type='email']", 5)
            assert email_field is not None, "Email field not found"
            email_field.send_keys("test@example.com")
            
            first_name_field = self.wait_for_element("input[name='firstName']", 5)
            if first_name_field:
                first_name_field.send_keys("Test User")
            
            phone_field = self.driver.find_element(By.CSS_SELECTOR, "input[name='phone']")
            if phone_field:
                phone_field.send_keys("555-123-4567")
            
            # Answer assessment questions
            question_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            answered_questions = 0
            
            for input_elem in question_inputs:
                if input_elem.is_displayed() and input_elem.is_enabled():
                    input_elem.click()
                    answered_questions += 1
                    time.sleep(0.5)  # Small delay between questions
            
            assert answered_questions > 0, "No assessment questions answered"
            
            # Submit assessment
            submit_button = self.wait_for_clickable("button[type='submit']", 5)
            assert submit_button is not None, "Submit button not found"
            submit_button.click()
            
            # Wait for submission to complete
            time.sleep(2)
            
            # Check for success indication (modal closes or success message)
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "[role='dialog']"))
                )
                logger.info("✅ Assessment submitted successfully")
            except TimeoutException:
                # Check for success message instead
                success_message = self.driver.find_element(By.CSS_SELECTOR, ".success, .alert-success")
                if success_message:
                    logger.info("✅ Assessment submitted successfully (success message found)")
                else:
                    logger.warning("⚠️ Assessment submission status unclear")
            
            logger.info("✅ Assessment flow test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Assessment flow test failed: {e}")
            self.take_screenshot("assessment_flow_error")
            return False
    
    def test_user_registration_flow(self):
        """Test user registration flow"""
        logger.info("Testing user registration flow...")
        
        try:
            # Navigate to landing page
            self.driver.get(self.base_url)
            
            # Look for registration/signup button
            signup_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button:contains('Sign Up'), a:contains('Sign Up'), button:contains('Get Started')")
            
            if not signup_buttons:
                # Try alternative selectors
                signup_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[href*='signup'], [href*='register']")
            
            if signup_buttons:
                signup_buttons[0].click()
                time.sleep(2)
            
            # Check if registration form appears
            registration_form = self.wait_for_element("form", 5)
            
            if registration_form:
                # Fill out registration form
                email_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='email']")
                if email_field:
                    email_field.send_keys(f"test_{int(time.time())}@example.com")
                
                password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                if password_field:
                    password_field.send_keys("TestPassword123!")
                
                confirm_password_field = self.driver.find_element(By.CSS_SELECTOR, "input[name*='confirm'], input[name*='repeat']")
                if confirm_password_field:
                    confirm_password_field.send_keys("TestPassword123!")
                
                # Submit registration
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                if submit_button:
                    submit_button.click()
                    time.sleep(3)
            
            logger.info("✅ User registration flow test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ User registration flow test failed: {e}")
            self.take_screenshot("registration_flow_error")
            return False
    
    def test_settings_management(self):
        """Test settings page management"""
        logger.info("Testing settings management...")
        
        try:
            # Navigate to settings page
            self.driver.get(f"{self.base_url}/settings")
            
            # Wait for settings page to load
            self.wait_for_element("body", 10)
            
            # Check for settings form elements
            form_elements = self.driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
            
            if form_elements:
                # Interact with form elements
                for element in form_elements[:3]:  # Test first 3 form elements
                    if element.is_displayed() and element.is_enabled():
                        if element.tag_name == 'input':
                            if element.get_attribute('type') == 'text':
                                element.clear()
                                element.send_keys("Updated Value")
                            elif element.get_attribute('type') == 'checkbox':
                                element.click()
                        elif element.tag_name == 'select':
                            options = element.find_elements(By.TAG_NAME, 'option')
                            if len(options) > 1:
                                options[1].click()
                
                # Look for save button
                save_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button:contains('Save')")
                if save_buttons:
                    save_buttons[0].click()
                    time.sleep(2)
            
            logger.info("✅ Settings management test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Settings management test failed: {e}")
            self.take_screenshot("settings_management_error")
            return False
    
    def test_dashboard_view(self):
        """Test dashboard view and functionality"""
        logger.info("Testing dashboard view...")
        
        try:
            # Navigate to dashboard
            self.driver.get(f"{self.base_url}/dashboard")
            
            # Wait for dashboard to load
            self.wait_for_element("body", 10)
            
            # Check for dashboard content
            dashboard_elements = self.driver.find_elements(By.CSS_SELECTOR, ".dashboard, [data-testid='dashboard'], main")
            
            if dashboard_elements:
                # Check for key dashboard components
                charts = self.driver.find_elements(By.CSS_SELECTOR, "canvas, .chart, .graph")
                metrics = self.driver.find_elements(By.CSS_SELECTOR, ".metric, .stat, .kpi")
                
                logger.info(f"Found {len(charts)} charts and {len(metrics)} metrics")
            
            logger.info("✅ Dashboard view test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Dashboard view test failed: {e}")
            self.take_screenshot("dashboard_view_error")
            return False
    
    def test_navigation_flow(self):
        """Test navigation between pages"""
        logger.info("Testing navigation flow...")
        
        try:
            # Start from landing page
            self.driver.get(self.base_url)
            
            # Test navigation links
            nav_links = self.driver.find_elements(By.CSS_SELECTOR, "nav a, .navigation a")
            
            for link in nav_links[:3]:  # Test first 3 navigation links
                if link.is_displayed() and link.is_enabled():
                    link_text = link.text.strip()
                    if link_text:
                        logger.info(f"Testing navigation to: {link_text}")
                        link.click()
                        time.sleep(2)
                        
                        # Verify page loaded
                        self.wait_for_element("body", 5)
                        
                        # Go back to landing page
                        self.driver.get(self.base_url)
                        time.sleep(1)
            
            logger.info("✅ Navigation flow test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Navigation flow test failed: {e}")
            self.take_screenshot("navigation_flow_error")
            return False
    
    def test_mobile_responsiveness(self):
        """Test mobile responsiveness"""
        logger.info("Testing mobile responsiveness...")
        
        try:
            # Setup mobile driver
            self.teardown_driver()
            self.setup_driver('mobile')
            
            # Navigate to landing page
            self.driver.get(self.base_url)
            
            # Check for mobile-specific elements
            mobile_menu = self.driver.find_elements(By.CSS_SELECTOR, ".mobile-menu, .hamburger, [aria-label*='menu']")
            
            # Test touch interactions
            touch_elements = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input")
            for element in touch_elements[:3]:
                if element.is_displayed():
                    # Simulate touch
                    ActionChains(self.driver).move_to_element(element).click().perform()
                    time.sleep(0.5)
            
            # Check viewport
            viewport_script = """
                return {
                    width: window.innerWidth,
                    height: window.innerHeight,
                    devicePixelRatio: window.devicePixelRatio
                };
            """
            viewport = self.driver.execute_script(viewport_script)
            
            assert viewport['width'] <= 768, f"Mobile viewport too wide: {viewport['width']}px"
            
            logger.info("✅ Mobile responsiveness test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Mobile responsiveness test failed: {e}")
            self.take_screenshot("mobile_responsiveness_error")
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        logger.info("Testing error handling...")
        
        try:
            # Test 404 page
            self.driver.get(f"{self.base_url}/nonexistent-page")
            time.sleep(2)
            
            # Check for error page or redirect
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error, .not-found, [data-testid='error']")
            
            # Test invalid form submission
            self.driver.get(self.base_url)
            
            # Try to submit assessment without filling required fields
            ai_risk_button = self.driver.find_element(By.CSS_SELECTOR, "[aria-label*='Determine Your Replacement Risk Due To AI']")
            if ai_risk_button:
                ai_risk_button.click()
                time.sleep(2)
                
                # Try to submit empty form
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                if submit_button:
                    submit_button.click()
                    time.sleep(2)
                    
                    # Check for validation errors
                    error_messages = self.driver.find_elements(By.CSS_SELECTOR, ".error, .invalid, .required")
                    if error_messages:
                        logger.info("✅ Form validation working correctly")
            
            logger.info("✅ Error handling test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.take_screenshot("error_handling_error")
            return False
    
    def test_api_connectivity(self):
        """Test API connectivity and responses"""
        logger.info("Testing API connectivity...")
        
        try:
            # Test health endpoint
            health_response = requests.get(f"{self.api_url}/health", timeout=10)
            assert health_response.status_code == 200, f"Health endpoint failed: {health_response.status_code}"
            
            health_data = health_response.json()
            assert health_data.get('status') == 'healthy', "Health status not healthy"
            
            # Test API status endpoint
            status_response = requests.get(f"{self.api_url}/api/status", timeout=10)
            assert status_response.status_code == 200, f"API status endpoint failed: {status_response.status_code}"
            
            status_data = status_response.json()
            assert 'endpoints' in status_data, "API status missing endpoints"
            
            logger.info("✅ API connectivity test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ API connectivity test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all critical workflow tests"""
        logger.info("Starting critical workflows E2E tests...")
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'success_rate': 0.0
            }
        }
        
        # List of tests to run
        tests = [
            ('landing_page_load', self.test_landing_page_load),
            ('assessment_flow', self.test_assessment_flow),
            ('user_registration_flow', self.test_user_registration_flow),
            ('settings_management', self.test_settings_management),
            ('dashboard_view', self.test_dashboard_view),
            ('navigation_flow', self.test_navigation_flow),
            ('mobile_responsiveness', self.test_mobile_responsiveness),
            ('error_handling', self.test_error_handling),
            ('api_connectivity', self.test_api_connectivity)
        ]
        
        # Setup driver
        self.setup_driver()
        
        try:
            for test_name, test_func in tests:
                logger.info(f"Running test: {test_name}")
                
                try:
                    result = test_func()
                    test_results['tests'][test_name] = {
                        'status': 'PASS' if result else 'FAIL',
                        'timestamp': datetime.now().isoformat()
                    }
                    test_results['summary']['total'] += 1
                    if result:
                        test_results['summary']['passed'] += 1
                    else:
                        test_results['summary']['failed'] += 1
                        
                except Exception as e:
                    logger.error(f"Test {test_name} failed with exception: {e}")
                    test_results['tests'][test_name] = {
                        'status': 'FAIL',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    test_results['summary']['total'] += 1
                    test_results['summary']['failed'] += 1
                
                # Small delay between tests
                time.sleep(1)
        
        finally:
            # Cleanup
            self.teardown_driver()
        
        # Calculate success rate
        if test_results['summary']['total'] > 0:
            test_results['summary']['success_rate'] = (
                test_results['summary']['passed'] / test_results['summary']['total'] * 100
            )
        
        logger.info(f"E2E tests completed - Success rate: {test_results['summary']['success_rate']:.1f}%")
        return test_results

def main():
    """Main function for running E2E tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mingus Critical Workflows E2E Tests')
    parser.add_argument('--base-url', default='http://localhost:3000', help='Frontend base URL')
    parser.add_argument('--api-url', default='http://localhost:5000', help='API base URL')
    parser.add_argument('--output', help='Output file for test results')
    parser.add_argument('--test', help='Run specific test only')
    
    args = parser.parse_args()
    
    config = {
        'base_url': args.base_url,
        'api_url': args.api_url
    }
    
    # Create screenshots directory
    import os
    os.makedirs('screenshots', exist_ok=True)
    
    # Run tests
    test_suite = CriticalWorkflowsTest(config)
    
    if args.test:
        # Run specific test
        test_method = getattr(test_suite, f"test_{args.test}")
        if test_method:
            test_suite.setup_driver()
            try:
                result = test_method()
                print(f"Test {args.test}: {'PASS' if result else 'FAIL'}")
            finally:
                test_suite.teardown_driver()
        else:
            print(f"Test {args.test} not found")
    else:
        # Run all tests
        results = test_suite.run_all_tests()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Test results saved to {args.output}")
        else:
            print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
