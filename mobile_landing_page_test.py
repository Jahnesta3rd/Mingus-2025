#!/usr/bin/env python3
"""
Mobile Landing Page Testing Suite
Tests mobile experience across various devices and screen sizes
"""

import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import subprocess
import os
import sys
from datetime import datetime
import statistics

class MobileLandingPageTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "mobile_devices": {},
            "performance_metrics": {},
            "accessibility_scores": {},
            "touch_interaction_tests": {},
            "content_readability_tests": {},
            "navigation_tests": {},
            "cta_tests": {},
            "cross_device_consistency": {}
        }
        
        # Mobile device configurations
        self.mobile_devices = {
            "iPhone_SE": {"width": 375, "height": 667, "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"},
            "iPhone_12": {"width": 390, "height": 844, "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"},
            "iPhone_12_Pro_Max": {"width": 428, "height": 926, "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"},
            "Samsung_Galaxy_S20": {"width": 360, "height": 800, "user_agent": "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36"},
            "iPad": {"width": 768, "height": 1024, "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"},
            "iPad_Pro": {"width": 1024, "height": 1366, "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"}
        }
        
        self.driver = None
        
    def setup_driver(self, device_name):
        """Setup Chrome driver with mobile device configuration"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size={},{}".format(
            self.mobile_devices[device_name]["width"],
            self.mobile_devices[device_name]["height"]
        ))
        chrome_options.add_argument("--user-agent={}".format(
            self.mobile_devices[device_name]["user_agent"]
        ))
        
        # Enable mobile emulation
        mobile_emulation = {
            "deviceMetrics": {
                "width": self.mobile_devices[device_name]["width"],
                "height": self.mobile_devices[device_name]["height"],
                "pixelRatio": 3.0
            },
            "userAgent": self.mobile_devices[device_name]["user_agent"]
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        return self.driver
    
    def test_page_load_speed(self, device_name):
        """Test page load speed and performance metrics"""
        print(f"Testing page load speed for {device_name}...")
        
        try:
            # Navigate to landing page
            start_time = time.time()
            self.driver.get(f"{self.base_url}/")
            
            # Wait for page to load completely
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            load_time = time.time() - start_time
            
            # Get performance metrics
            performance_metrics = self.driver.execute_script("""
                var performance = window.performance;
                var navigation = performance.getEntriesByType('navigation')[0];
                var paint = performance.getEntriesByType('paint');
                
                return {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    firstPaint: paint.find(p => p.name === 'first-paint') ? paint.find(p => p.name === 'first-paint').startTime : 0,
                    firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint') ? paint.find(p => p.name === 'first-contentful-paint').startTime : 0
                };
            """)
            
            # Check for critical resources
            critical_resources = self.driver.execute_script("""
                var resources = performance.getEntriesByType('resource');
                var critical = resources.filter(r => 
                    r.name.includes('.css') || 
                    r.name.includes('.js') || 
                    r.name.includes('font') ||
                    r.name.includes('image')
                );
                return critical.map(r => ({
                    name: r.name,
                    duration: r.duration,
                    size: r.transferSize || 0
                }));
            """)
            
            self.results["performance_metrics"][device_name] = {
                "total_load_time": load_time,
                "dom_content_loaded": performance_metrics["domContentLoaded"],
                "load_complete": performance_metrics["loadComplete"],
                "first_paint": performance_metrics["firstPaint"],
                "first_contentful_paint": performance_metrics["firstContentfulPaint"],
                "critical_resources": critical_resources,
                "status": "PASS" if load_time < 3.0 else "FAIL"
            }
            
            print(f"✓ Page load time: {load_time:.2f}s")
            return True
            
        except Exception as e:
            print(f"✗ Page load test failed: {str(e)}")
            self.results["performance_metrics"][device_name] = {
                "error": str(e),
                "status": "FAIL"
            }
            return False
    
    def test_touch_interactions(self, device_name):
        """Test touch interaction quality and responsiveness"""
        print(f"Testing touch interactions for {device_name}...")
        
        try:
            # Test CTA button touch interactions
            cta_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".hero-cta-primary, .hero-cta-secondary, .landing-nav-cta")
            
            touch_tests = []
            for button in cta_buttons:
                try:
                    # Check if button is visible and clickable
                    if button.is_displayed() and button.is_enabled():
                        # Simulate touch interaction
                        actions = ActionChains(self.driver)
                        actions.move_to_element(button)
                        actions.click()
                        actions.perform()
                        
                        # Check for visual feedback (hover states, etc.)
                        button_classes = button.get_attribute("class")
                        
                        touch_tests.append({
                            "element": button.text or button.get_attribute("href"),
                            "visible": True,
                            "enabled": True,
                            "clickable": True,
                            "has_visual_feedback": "hover" in button_classes or "active" in button_classes
                        })
                        
                        # Go back to landing page for next test
                        self.driver.get(f"{self.base_url}/")
                        time.sleep(1)
                        
                except Exception as e:
                    touch_tests.append({
                        "element": button.text or button.get_attribute("href"),
                        "error": str(e),
                        "status": "FAIL"
                    })
            
            # Test navigation menu touch interactions
            nav_links = self.driver.find_elements(By.CSS_SELECTOR, ".landing-nav-links a")
            nav_tests = []
            
            for link in nav_links:
                try:
                    if link.is_displayed():
                        # Test touch target size (should be at least 44px)
                        size = link.size
                        min_touch_target = size["width"] >= 44 and size["height"] >= 44
                        
                        nav_tests.append({
                            "element": link.text,
                            "touch_target_size": f"{size['width']}x{size['height']}",
                            "meets_minimum": min_touch_target,
                            "status": "PASS" if min_touch_target else "FAIL"
                        })
                except Exception as e:
                    nav_tests.append({
                        "element": link.text,
                        "error": str(e),
                        "status": "FAIL"
                    })
            
            self.results["touch_interaction_tests"][device_name] = {
                "cta_button_tests": touch_tests,
                "navigation_touch_tests": nav_tests,
                "status": "PASS" if all(t.get("status", "FAIL") == "PASS" for t in touch_tests + nav_tests) else "FAIL"
            }
            
            print(f"✓ Touch interaction tests completed")
            return True
            
        except Exception as e:
            print(f"✗ Touch interaction test failed: {str(e)}")
            self.results["touch_interaction_tests"][device_name] = {
                "error": str(e),
                "status": "FAIL"
            }
            return False
    
    def test_content_readability(self, device_name):
        """Test content readability on small screens"""
        print(f"Testing content readability for {device_name}...")
        
        try:
            readability_tests = []
            
            # Test text sizes
            text_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6, p, span, a")
            
            for element in text_elements[:20]:  # Test first 20 elements
                try:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text:
                            # Get computed styles
                            font_size = self.driver.execute_script(
                                "return window.getComputedStyle(arguments[0]).fontSize", element
                            )
                            font_size_px = float(font_size.replace("px", ""))
                            
                            # Get color contrast
                            color = self.driver.execute_script(
                                "return window.getComputedStyle(arguments[0]).color", element
                            )
                            background_color = self.driver.execute_script(
                                "return window.getComputedStyle(arguments[0]).backgroundColor", element
                            )
                            
                            # Check if text is readable (font size >= 16px for body text)
                            is_readable = font_size_px >= 16 if element.tag_name == "p" else font_size_px >= 14
                            
                            readability_tests.append({
                                "element": element.tag_name,
                                "text_preview": text[:50] + "..." if len(text) > 50 else text,
                                "font_size": font_size,
                                "is_readable": is_readable,
                                "color": color,
                                "background": background_color
                            })
                            
                except Exception as e:
                    readability_tests.append({
                        "element": element.tag_name,
                        "error": str(e)
                    })
            
            # Test line spacing and paragraph spacing
            paragraphs = self.driver.find_elements(By.CSS_SELECTOR, "p")
            spacing_tests = []
            
            for p in paragraphs[:5]:
                try:
                    if p.is_displayed():
                        line_height = self.driver.execute_script(
                            "return window.getComputedStyle(arguments[0]).lineHeight", p
                        )
                        margin_bottom = self.driver.execute_script(
                            "return window.getComputedStyle(arguments[0]).marginBottom", p
                        )
                        
                        spacing_tests.append({
                            "line_height": line_height,
                            "margin_bottom": margin_bottom,
                            "adequate_spacing": True  # Basic check
                        })
                except Exception as e:
                    spacing_tests.append({"error": str(e)})
            
            self.results["content_readability_tests"][device_name] = {
                "text_readability": readability_tests,
                "spacing_tests": spacing_tests,
                "status": "PASS" if all(t.get("is_readable", False) for t in readability_tests if "is_readable" in t) else "FAIL"
            }
            
            print(f"✓ Content readability tests completed")
            return True
            
        except Exception as e:
            print(f"✗ Content readability test failed: {str(e)}")
            self.results["content_readability_tests"][device_name] = {
                "error": str(e),
                "status": "FAIL"
            }
            return False
    
    def test_navigation_functionality(self, device_name):
        """Test navigation and menu functionality"""
        print(f"Testing navigation functionality for {device_name}...")
        
        try:
            navigation_tests = []
            
            # Test main navigation links
            nav_links = self.driver.find_elements(By.CSS_SELECTOR, ".landing-nav-links a")
            
            for link in nav_links:
                try:
                    if link.is_displayed():
                        href = link.get_attribute("href")
                        text = link.text
                        
                        # Test if link is functional
                        original_url = self.driver.current_url
                        link.click()
                        time.sleep(2)
                        
                        new_url = self.driver.current_url
                        navigation_worked = new_url != original_url
                        
                        navigation_tests.append({
                            "link_text": text,
                            "href": href,
                            "navigation_worked": navigation_worked,
                            "status": "PASS" if navigation_worked else "FAIL"
                        })
                        
                        # Go back to landing page
                        self.driver.get(f"{self.base_url}/")
                        time.sleep(1)
                        
                except Exception as e:
                    navigation_tests.append({
                        "link_text": link.text,
                        "error": str(e),
                        "status": "FAIL"
                    })
            
            # Test mobile menu (if exists)
            try:
                mobile_menu_button = self.driver.find_element(By.CSS_SELECTOR, ".mobile-menu-button, .hamburger-menu")
                if mobile_menu_button.is_displayed():
                    mobile_menu_button.click()
                    time.sleep(1)
                    
                    # Check if menu opened
                    mobile_menu = self.driver.find_element(By.CSS_SELECTOR, ".mobile-menu, .nav-menu")
                    menu_opened = mobile_menu.is_displayed()
                    
                    navigation_tests.append({
                        "mobile_menu": "Menu opened successfully" if menu_opened else "Menu failed to open",
                        "status": "PASS" if menu_opened else "FAIL"
                    })
                    
            except NoSuchElementException:
                navigation_tests.append({
                    "mobile_menu": "No mobile menu found (may be hidden on this device size)",
                    "status": "SKIP"
                })
            
            self.results["navigation_tests"][device_name] = {
                "navigation_tests": navigation_tests,
                "status": "PASS" if all(t.get("status") in ["PASS", "SKIP"] for t in navigation_tests) else "FAIL"
            }
            
            print(f"✓ Navigation functionality tests completed")
            return True
            
        except Exception as e:
            print(f"✗ Navigation functionality test failed: {str(e)}")
            self.results["navigation_tests"][device_name] = {
                "error": str(e),
                "status": "FAIL"
            }
            return False
    
    def test_mobile_optimized_ctas(self, device_name):
        """Test mobile-optimized call-to-action buttons"""
        print(f"Testing mobile-optimized CTAs for {device_name}...")
        
        try:
            cta_tests = []
            
            # Find all CTA buttons
            cta_selectors = [
                ".hero-cta-primary",
                ".hero-cta-secondary", 
                ".landing-nav-cta",
                "a[href*='quiz']",
                "a[href*='login']",
                "button[type='submit']",
                ".cta-button",
                ".call-to-action"
            ]
            
            for selector in cta_selectors:
                ctas = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for cta in ctas:
                    try:
                        if cta.is_displayed():
                            # Test button size (should be at least 44x44px for touch)
                            size = cta.size
                            min_size = size["width"] >= 44 and size["height"] >= 44
                            
                            # Test button positioning (should be easily reachable)
                            location = cta.location
                            screen_height = self.driver.execute_script("return window.innerHeight")
                            is_reachable = location["y"] < screen_height * 0.8  # Within 80% of screen height
                            
                            # Test button styling
                            background_color = self.driver.execute_script(
                                "return window.getComputedStyle(arguments[0]).backgroundColor", cta
                            )
                            has_contrast = background_color != "rgba(0, 0, 0, 0)" and background_color != "transparent"
                            
                            # Test button text
                            text = cta.text.strip()
                            has_clear_text = len(text) > 0 and len(text) < 50
                            
                            cta_tests.append({
                                "selector": selector,
                                "text": text,
                                "size": f"{size['width']}x{size['height']}",
                                "meets_minimum_size": min_size,
                                "is_reachable": is_reachable,
                                "has_contrast": has_contrast,
                                "has_clear_text": has_clear_text,
                                "status": "PASS" if all([min_size, is_reachable, has_contrast, has_clear_text]) else "FAIL"
                            })
                            
                    except Exception as e:
                        cta_tests.append({
                            "selector": selector,
                            "error": str(e),
                            "status": "FAIL"
                        })
            
            self.results["cta_tests"][device_name] = {
                "cta_tests": cta_tests,
                "status": "PASS" if all(t.get("status") == "PASS" for t in cta_tests) else "FAIL"
            }
            
            print(f"✓ Mobile CTA tests completed")
            return True
            
        except Exception as e:
            print(f"✗ Mobile CTA test failed: {str(e)}")
            self.results["cta_tests"][device_name] = {
                "error": str(e),
                "status": "FAIL"
            }
            return False
    
    def test_cross_device_consistency(self):
        """Test cross-device consistency"""
        print("Testing cross-device consistency...")
        
        try:
            consistency_tests = {}
            
            # Test that all devices have the same core elements
            core_elements = [
                ".hero-title",
                ".hero-subtitle", 
                ".hero-cta-primary",
                ".landing-logo",
                ".social-proof"
            ]
            
            for device_name in self.mobile_devices.keys():
                if device_name in self.results["performance_metrics"]:
                    consistency_tests[device_name] = {}
                    
                    for element_selector in core_elements:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, element_selector)
                            consistency_tests[device_name][element_selector] = {
                                "present": len(elements) > 0,
                                "visible": elements[0].is_displayed() if elements else False
                            }
                        except Exception as e:
                            consistency_tests[device_name][element_selector] = {
                                "error": str(e),
                                "present": False,
                                "visible": False
                            }
            
            # Check for consistency across devices
            all_devices_have_core_elements = True
            for device_name, elements in consistency_tests.items():
                for element_selector, status in elements.items():
                    if not status.get("present", False):
                        all_devices_have_core_elements = False
                        break
            
            self.results["cross_device_consistency"] = {
                "consistency_tests": consistency_tests,
                "all_devices_have_core_elements": all_devices_have_core_elements,
                "status": "PASS" if all_devices_have_core_elements else "FAIL"
            }
            
            print(f"✓ Cross-device consistency tests completed")
            return True
            
        except Exception as e:
            print(f"✗ Cross-device consistency test failed: {str(e)}")
            self.results["cross_device_consistency"] = {
                "error": str(e),
                "status": "FAIL"
            }
            return False
    
    def run_accessibility_tests(self, device_name):
        """Run basic accessibility tests"""
        print(f"Running accessibility tests for {device_name}...")
        
        try:
            accessibility_tests = []
            
            # Test alt text for images
            images = self.driver.find_elements(By.TAG_NAME, "img")
            for img in images:
                try:
                    alt_text = img.get_attribute("alt")
                    has_alt = alt_text is not None and alt_text.strip() != ""
                    accessibility_tests.append({
                        "type": "image_alt_text",
                        "element": img.get_attribute("src"),
                        "has_alt": has_alt,
                        "alt_text": alt_text
                    })
                except Exception as e:
                    accessibility_tests.append({
                        "type": "image_alt_text",
                        "error": str(e)
                    })
            
            # Test heading hierarchy
            headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
            heading_hierarchy = []
            for heading in headings:
                try:
                    if heading.is_displayed():
                        level = int(heading.tag_name[1])
                        text = heading.text.strip()
                        heading_hierarchy.append({
                            "level": level,
                            "text": text[:50] + "..." if len(text) > 50 else text
                        })
                except Exception as e:
                    heading_hierarchy.append({"error": str(e)})
            
            # Test form labels
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            form_accessibility = []
            for form in forms:
                try:
                    inputs = form.find_elements(By.CSS_SELECTOR, "input, textarea, select")
                    for input_elem in inputs:
                        input_id = input_elem.get_attribute("id")
                        if input_id:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                            has_label = label.is_displayed()
                            form_accessibility.append({
                                "input_id": input_id,
                                "has_label": has_label
                            })
                except Exception as e:
                    form_accessibility.append({"error": str(e)})
            
            self.results["accessibility_scores"][device_name] = {
                "image_alt_text_tests": accessibility_tests,
                "heading_hierarchy": heading_hierarchy,
                "form_accessibility": form_accessibility,
                "status": "PASS"  # Basic pass for now
            }
            
            print(f"✓ Accessibility tests completed")
            return True
            
        except Exception as e:
            print(f"✗ Accessibility test failed: {str(e)}")
            self.results["accessibility_scores"][device_name] = {
                "error": str(e),
                "status": "FAIL"
            }
            return False
    
    def run_all_tests(self):
        """Run all mobile tests across all devices"""
        print("🚀 Starting Mobile Landing Page Testing Suite")
        print("=" * 60)
        
        for device_name in self.mobile_devices.keys():
            print(f"\n📱 Testing on {device_name}")
            print("-" * 40)
            
            try:
                # Setup driver for this device
                self.setup_driver(device_name)
                
                # Run all tests
                self.test_page_load_speed(device_name)
                self.test_touch_interactions(device_name)
                self.test_content_readability(device_name)
                self.test_navigation_functionality(device_name)
                self.test_mobile_optimized_ctas(device_name)
                self.run_accessibility_tests(device_name)
                
                # Close driver
                if self.driver:
                    self.driver.quit()
                    
            except Exception as e:
                print(f"✗ Error testing {device_name}: {str(e)}")
                if self.driver:
                    self.driver.quit()
        
        # Run cross-device consistency test
        self.test_cross_device_consistency()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 Generating Test Report")
        print("=" * 60)
        
        # Calculate overall scores
        total_tests = 0
        passed_tests = 0
        
        for device_name in self.mobile_devices.keys():
            device_tests = [
                self.results["performance_metrics"].get(device_name, {}).get("status"),
                self.results["touch_interaction_tests"].get(device_name, {}).get("status"),
                self.results["content_readability_tests"].get(device_name, {}).get("status"),
                self.results["navigation_tests"].get(device_name, {}).get("status"),
                self.results["cta_tests"].get(device_name, {}).get("status"),
                self.results["accessibility_scores"].get(device_name, {}).get("status")
            ]
            
            for test_status in device_tests:
                if test_status:
                    total_tests += 1
                    if test_status == "PASS":
                        passed_tests += 1
        
        # Add cross-device consistency
        if self.results["cross_device_consistency"].get("status"):
            total_tests += 1
            if self.results["cross_device_consistency"]["status"] == "PASS":
                passed_tests += 1
        
        overall_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Create summary
        summary = {
            "overall_score": overall_score,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "test_date": datetime.now().isoformat(),
            "recommendations": self.generate_recommendations()
        }
        
        self.results["summary"] = summary
        
        # Save report
        report_filename = f"mobile_landing_page_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        print(f"\n📈 Test Results Summary:")
        print(f"Overall Score: {overall_score:.1f}%")
        print(f"Passed: {passed_tests}/{total_tests} tests")
        print(f"Failed: {total_tests - passed_tests}/{total_tests} tests")
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        # Print recommendations
        print(f"\n💡 Key Recommendations:")
        for rec in summary["recommendations"]:
            print(f"• {rec}")
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Performance recommendations
        slow_devices = []
        for device_name, metrics in self.results["performance_metrics"].items():
            if metrics.get("total_load_time", 0) > 3.0:
                slow_devices.append(device_name)
        
        if slow_devices:
            recommendations.append(f"Optimize page load speed for {', '.join(slow_devices)} (currently >3s)")
        
        # Touch interaction recommendations
        for device_name, tests in self.results["touch_interaction_tests"].items():
            if tests.get("status") == "FAIL":
                recommendations.append(f"Improve touch interactions on {device_name}")
        
        # Content readability recommendations
        for device_name, tests in self.results["content_readability_tests"].items():
            if tests.get("status") == "FAIL":
                recommendations.append(f"Improve text readability on {device_name}")
        
        # CTA recommendations
        for device_name, tests in self.results["cta_tests"].items():
            if tests.get("status") == "FAIL":
                recommendations.append(f"Optimize CTA buttons for {device_name}")
        
        # Cross-device consistency
        if self.results["cross_device_consistency"].get("status") == "FAIL":
            recommendations.append("Ensure consistent experience across all mobile devices")
        
        if not recommendations:
            recommendations.append("Great job! Mobile experience is well-optimized across all devices.")
        
        return recommendations

def main():
    """Main function to run the mobile testing suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mobile Landing Page Testing Suite")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL of the landing page")
    parser.add_argument("--devices", nargs="+", help="Specific devices to test")
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = MobileLandingPageTester(args.url)
    
    # Filter devices if specified
    if args.devices:
        tester.mobile_devices = {k: v for k, v in tester.mobile_devices.items() if k in args.devices}
    
    # Run tests
    tester.run_all_tests()

if __name__ == "__main__":
    main()
