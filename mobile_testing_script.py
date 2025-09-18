#!/usr/bin/env python3
"""
MINGUS Mobile Testing Script
Comprehensive mobile testing for the MINGUS Financial Wellness Application
"""

import time
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

class MingusMobileTester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.test_results = {
            "test_start_time": datetime.now().isoformat(),
            "test_persona": {
                "profile": "African American professional, aged 28, living in Atlanta",
                "income": "$65,000/year",
                "challenges": "Student loan debt, building emergency savings",
                "test_email": "johnnie@mingus.com"
            },
            "mobile_tests": {},
            "performance_metrics": {},
            "accessibility_tests": {},
            "issues_found": [],
            "recommendations": []
        }
        
    def setup_mobile_driver(self, device_type="iPhone 12"):
        """Setup mobile Chrome driver with device emulation"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=375,812")  # iPhone 12 dimensions
        
        # Mobile device emulation
        mobile_emulation = {
            "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(375, 812)
            return driver
        except Exception as e:
            print(f"Error setting up mobile driver: {e}")
            return None
    
    def test_page_load_performance(self, driver):
        """Test page load performance on mobile"""
        print("📱 Testing Mobile Page Load Performance...")
        
        start_time = time.time()
        driver.get(self.base_url)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )
        
        load_time = time.time() - start_time
        
        # Check for console errors
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        
        self.test_results["performance_metrics"]["mobile_load_time"] = load_time
        self.test_results["performance_metrics"]["console_errors"] = len(errors)
        
        print(f"✅ Mobile load time: {load_time:.2f} seconds")
        if errors:
            print(f"⚠️  Console errors found: {len(errors)}")
            for error in errors:
                print(f"   - {error['message']}")
        
        return load_time < 3.0  # Should load in under 3 seconds
    
    def test_responsive_design(self, driver):
        """Test responsive design elements"""
        print("📱 Testing Mobile Responsive Design...")
        
        # Test viewport meta tag
        viewport = driver.execute_script("return document.querySelector('meta[name=viewport]')?.getAttribute('content')")
        viewport_correct = "width=device-width, initial-scale=1.0" in viewport if viewport else False
        
        # Test horizontal scrolling (should be none)
        body_width = driver.execute_script("return document.body.scrollWidth")
        window_width = driver.execute_script("return window.innerWidth")
        no_horizontal_scroll = body_width <= window_width
        
        # Test touch targets (minimum 44px)
        buttons = driver.find_elements(By.TAG_NAME, "button")
        touch_target_issues = []
        
        for i, button in enumerate(buttons):
            try:
                size = button.size
                if size['width'] < 44 or size['height'] < 44:
                    touch_target_issues.append(f"Button {i}: {size['width']}x{size['height']}px")
            except:
                pass
        
        self.test_results["mobile_tests"]["responsive_design"] = {
            "viewport_meta": viewport_correct,
            "no_horizontal_scroll": no_horizontal_scroll,
            "touch_target_issues": touch_target_issues
        }
        
        print(f"✅ Viewport meta tag: {'✓' if viewport_correct else '✗'}")
        print(f"✅ No horizontal scroll: {'✓' if no_horizontal_scroll else '✗'}")
        print(f"✅ Touch targets: {len(touch_target_issues)} issues found")
        
        return viewport_correct and no_horizontal_scroll and len(touch_target_issues) == 0
    
    def test_mobile_navigation(self, driver):
        """Test mobile navigation and interactions"""
        print("📱 Testing Mobile Navigation...")
        
        # Test skip links
        skip_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='#']")
        skip_links_working = len(skip_links) > 0
        
        # Test touch interactions
        try:
            # Test hero section buttons
            hero_buttons = driver.find_elements(By.CSS_SELECTOR, "button")
            touch_interactions_working = len(hero_buttons) > 0
            
            # Test button hover states (should work on touch)
            for button in hero_buttons[:2]:  # Test first 2 buttons
                try:
                    ActionChains(driver).move_to_element(button).perform()
                    time.sleep(0.5)
                except:
                    pass
                    
        except Exception as e:
            touch_interactions_working = False
            print(f"⚠️  Touch interaction test failed: {e}")
        
        self.test_results["mobile_tests"]["navigation"] = {
            "skip_links": skip_links_working,
            "touch_interactions": touch_interactions_working
        }
        
        print(f"✅ Skip links: {'✓' if skip_links_working else '✗'}")
        print(f"✅ Touch interactions: {'✓' if touch_interactions_working else '✗'}")
        
        return skip_links_working and touch_interactions_working
    
    def test_assessment_modal_mobile(self, driver):
        """Test assessment modal on mobile"""
        print("📱 Testing Assessment Modal on Mobile...")
        
        try:
            # Find and click first assessment button
            assessment_buttons = driver.find_elements(By.CSS_SELECTOR, "button")
            ai_risk_button = None
            
            for button in assessment_buttons:
                if "AI" in button.text or "Replacement" in button.text:
                    ai_risk_button = button
                    break
            
            if ai_risk_button:
                ai_risk_button.click()
                time.sleep(2)
                
                # Check if modal opened
                modal = driver.find_elements(By.CSS_SELECTOR, "[role='dialog'], .modal, [data-testid='modal']")
                modal_opened = len(modal) > 0
                
                if modal_opened:
                    # Test form elements
                    form_inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
                    form_accessible = len(form_inputs) > 0
                    
                    # Test mobile form interaction
                    if form_inputs:
                        try:
                            first_input = form_inputs[0]
                            first_input.click()
                            first_input.send_keys("test@example.com")
                            time.sleep(1)
                        except:
                            pass
                    
                    # Close modal
                    close_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='close'], button[aria-label*='Close'], .close")
                    if close_buttons:
                        close_buttons[0].click()
                        time.sleep(1)
                    
                    self.test_results["mobile_tests"]["assessment_modal"] = {
                        "modal_opened": modal_opened,
                        "form_accessible": form_accessible,
                        "form_interaction": True
                    }
                    
                    print(f"✅ Modal opened: {'✓' if modal_opened else '✗'}")
                    print(f"✅ Form accessible: {'✓' if form_accessible else '✗'}")
                    
                    return modal_opened and form_accessible
                else:
                    print("⚠️  Assessment modal did not open")
                    return False
            else:
                print("⚠️  Assessment button not found")
                return False
                
        except Exception as e:
            print(f"⚠️  Assessment modal test failed: {e}")
            return False
    
    def test_mobile_content_readability(self, driver):
        """Test content readability on mobile"""
        print("📱 Testing Mobile Content Readability...")
        
        # Test text size (should be readable without zooming)
        try:
            # Get main heading
            main_heading = driver.find_element(By.CSS_SELECTOR, "h1")
            heading_size = main_heading.size
            heading_text = main_heading.text
            
            # Test paragraph text
            paragraphs = driver.find_elements(By.CSS_SELECTOR, "p")
            readable_paragraphs = 0
            
            for p in paragraphs[:3]:  # Test first 3 paragraphs
                try:
                    p_size = p.size
                    if p_size['height'] > 20:  # Minimum readable height
                        readable_paragraphs += 1
                except:
                    pass
            
            # Test button text readability
            buttons = driver.find_elements(By.CSS_SELECTOR, "button")
            readable_buttons = 0
            
            for button in buttons[:4]:  # Test first 4 buttons
                try:
                    button_text = button.text
                    button_size = button.size
                    if len(button_text) > 0 and button_size['height'] > 30:
                        readable_buttons += 1
                except:
                    pass
            
            self.test_results["mobile_tests"]["content_readability"] = {
                "heading_size": heading_size,
                "heading_text": heading_text[:50] + "..." if len(heading_text) > 50 else heading_text,
                "readable_paragraphs": readable_paragraphs,
                "readable_buttons": readable_buttons
            }
            
            print(f"✅ Main heading: {heading_text[:30]}...")
            print(f"✅ Readable paragraphs: {readable_paragraphs}/3")
            print(f"✅ Readable buttons: {readable_buttons}/4")
            
            return readable_paragraphs >= 2 and readable_buttons >= 3
            
        except Exception as e:
            print(f"⚠️  Content readability test failed: {e}")
            return False
    
    def test_mobile_performance(self, driver):
        """Test mobile-specific performance metrics"""
        print("📱 Testing Mobile Performance...")
        
        # Test scroll performance
        start_time = time.time()
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        scroll_time = time.time() - start_time
        
        # Test touch response time
        touch_start = time.time()
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR, "button")
            if buttons:
                buttons[0].click()
                time.sleep(0.1)
        except:
            pass
        touch_response = time.time() - touch_start
        
        # Test memory usage (approximate)
        memory_info = driver.execute_script("return performance.memory ? performance.memory.usedJSHeapSize : 0")
        
        self.test_results["performance_metrics"]["mobile_scroll_time"] = scroll_time
        self.test_results["performance_metrics"]["touch_response_time"] = touch_response
        self.test_results["performance_metrics"]["memory_usage"] = memory_info
        
        print(f"✅ Scroll performance: {scroll_time:.2f}s")
        print(f"✅ Touch response: {touch_response:.2f}s")
        print(f"✅ Memory usage: {memory_info / 1024 / 1024:.1f}MB" if memory_info > 0 else "✅ Memory usage: N/A")
        
        return scroll_time < 1.0 and touch_response < 0.5
    
    def run_comprehensive_mobile_test(self):
        """Run comprehensive mobile testing"""
        print("🚀 Starting MINGUS Mobile Testing")
        print("=" * 50)
        
        driver = self.setup_mobile_driver()
        if not driver:
            print("❌ Failed to setup mobile driver")
            return False
        
        try:
            # Test 1: Page Load Performance
            load_success = self.test_page_load_performance(driver)
            
            # Test 2: Responsive Design
            responsive_success = self.test_responsive_design(driver)
            
            # Test 3: Mobile Navigation
            navigation_success = self.test_mobile_navigation(driver)
            
            # Test 4: Assessment Modal
            modal_success = self.test_assessment_modal_mobile(driver)
            
            # Test 5: Content Readability
            readability_success = self.test_mobile_content_readability(driver)
            
            # Test 6: Mobile Performance
            performance_success = self.test_mobile_performance(driver)
            
            # Calculate overall success
            total_tests = 6
            passed_tests = sum([
                load_success, responsive_success, navigation_success,
                modal_success, readability_success, performance_success
            ])
            
            self.test_results["test_end_time"] = datetime.now().isoformat()
            self.test_results["overall_success_rate"] = (passed_tests / total_tests) * 100
            self.test_results["tests_passed"] = passed_tests
            self.test_results["total_tests"] = total_tests
            
            print("\n📊 Mobile Testing Results")
            print("=" * 30)
            print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
            print(f"✅ Success Rate: {self.test_results['overall_success_rate']:.1f}%")
            
            if passed_tests == total_tests:
                print("🎉 All mobile tests passed!")
            else:
                print("⚠️  Some mobile tests failed - see details above")
            
            return passed_tests == total_tests
            
        except Exception as e:
            print(f"❌ Mobile testing failed: {e}")
            return False
        finally:
            driver.quit()
    
    def save_test_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mingus_mobile_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"📄 Test results saved to: {filename}")
        return filename

if __name__ == "__main__":
    tester = MingusMobileTester()
    success = tester.run_comprehensive_mobile_test()
    tester.save_test_results()
    
    if success:
        print("\n🎉 MINGUS Mobile Testing Complete - All Tests Passed!")
    else:
        print("\n⚠️  MINGUS Mobile Testing Complete - Some Issues Found")
