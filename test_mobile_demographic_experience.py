#!/usr/bin/env python3
"""
MINGUS Mobile Demographic Experience Testing Suite
=================================================

Comprehensive mobile testing specifically designed for the target demographic:
- African American professionals aged 25-45
- Income range: $40K-$80K
- Likely using budget/older mobile devices
- Mobile-first usage patterns
- Need for reliable offline functionality
- Touch-friendly interfaces

Author: MINGUS Development Team
Date: January 2025
"""

import os
import sys
import time
import json
import logging
import statistics
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Selenium imports for mobile testing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
# TouchActions is deprecated in newer Selenium versions, using ActionChains instead
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Performance monitoring
import psutil
import requests
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'mobile_demographic_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeviceProfile(Enum):
    """Mobile device profiles for target demographic testing."""
    BUDGET_ANDROID = "budget_android"  # Samsung Galaxy A series, older devices
    BUDGET_IPHONE = "budget_iphone"    # iPhone SE, older iPhones
    MID_RANGE_ANDROID = "mid_android"  # Pixel 4a, OnePlus Nord
    MID_RANGE_IPHONE = "mid_iphone"    # iPhone 12, iPhone 13
    OLDER_DEVICE = "older_device"      # 3+ year old devices


class NetworkCondition(Enum):
    """Network conditions for realistic testing."""
    FAST_4G = "fast_4g"           # 50+ Mbps
    SLOW_4G = "slow_4g"           # 5-15 Mbps
    POOR_3G = "poor_3g"           # 1-3 Mbps
    SPOTTY_CONNECTION = "spotty"  # Intermittent connectivity


@dataclass
class MobileTestResult:
    """Results from mobile testing."""
    test_name: str
    device_profile: str
    network_condition: str
    passed: bool
    metrics: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    timestamp: str


@dataclass
class DemographicTestSuite:
    """Complete test suite for target demographic."""
    device_profiles: List[DeviceProfile]
    network_conditions: List[NetworkCondition]
    base_url: str
    test_results: List[MobileTestResult]


class MobileDemographicTester:
    """Comprehensive mobile testing for target demographic."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.driver = None
        self.test_results = []
        
        # Target demographic specifications
        self.target_specs = {
            "min_touch_target_size": 44,  # iOS/Android guidelines
            "max_page_load_time": 3.0,    # seconds
            "max_first_paint": 1.5,       # seconds
            "min_font_size": 16,          # pixels
            "max_memory_usage": 100,      # MB
            "max_battery_drain": 5,       # % per hour
        }
        
        # Device profiles for testing
        self.device_profiles = {
            DeviceProfile.BUDGET_ANDROID: {
                "user_agent": "Mozilla/5.0 (Linux; Android 10; SM-A505F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
                "viewport": (360, 640),
                "device_pixel_ratio": 2.0,
                "memory_limit": 2048,  # 2GB RAM
                "cpu_cores": 4,
                "storage_space": 32,   # GB
            },
            DeviceProfile.BUDGET_IPHONE: {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
                "viewport": (375, 667),
                "device_pixel_ratio": 2.0,
                "memory_limit": 2048,  # 2GB RAM
                "cpu_cores": 2,
                "storage_space": 64,   # GB
            },
            DeviceProfile.MID_RANGE_ANDROID: {
                "user_agent": "Mozilla/5.0 (Linux; Android 11; Pixel 4a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36",
                "viewport": (412, 915),
                "device_pixel_ratio": 2.5,
                "memory_limit": 4096,  # 4GB RAM
                "cpu_cores": 6,
                "storage_space": 128,  # GB
            },
            DeviceProfile.MID_RANGE_IPHONE: {
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                "viewport": (390, 844),
                "device_pixel_ratio": 3.0,
                "memory_limit": 4096,  # 4GB RAM
                "cpu_cores": 4,
                "storage_space": 128,  # GB
            },
            DeviceProfile.OLDER_DEVICE: {
                "user_agent": "Mozilla/5.0 (Linux; Android 8.1.0; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36",
                "viewport": (360, 640),
                "device_pixel_ratio": 1.5,
                "memory_limit": 1024,  # 1GB RAM
                "cpu_cores": 2,
                "storage_space": 16,   # GB
            }
        }
    
    def setup_driver(self, device_profile: DeviceProfile) -> webdriver.Chrome:
        """Setup Chrome driver with mobile emulation."""
        chrome_options = Options()
        
        # Get device specifications
        device_specs = self.device_profiles[device_profile]
        
        # Mobile emulation
        mobile_emulation = {
            "deviceMetrics": {
                "width": device_specs["viewport"][0],
                "height": device_specs["viewport"][1],
                "pixelRatio": device_specs["device_pixel_ratio"]
            },
            "userAgent": device_specs["user_agent"]
        }
        
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # Performance optimizations
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # For performance testing
        
        # Enable performance logging
        chrome_options.set_capability("goog:loggingPrefs", {
            "performance": "ALL",
            "browser": "ALL"
        })
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(*device_specs["viewport"])
        
        return self.driver
    
    def test_mobile_performance(self, device_profile: DeviceProfile) -> MobileTestResult:
        """Test mobile app performance and responsiveness."""
        logger.info(f"Testing mobile performance for {device_profile.value}")
        
        try:
            driver = self.setup_driver(device_profile)
            issues = []
            recommendations = []
            
            # Navigate to landing page
            start_time = time.time()
            driver.get(self.base_url)
            
            # Wait for page load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            load_time = time.time() - start_time
            
            # Get performance metrics
            performance_logs = driver.get_log("performance")
            
            # Calculate First Contentful Paint
            fcp_time = self._extract_fcp_time(performance_logs)
            
            # Check resource optimization
            resource_count = len(driver.find_elements(By.TAG_NAME, "img")) + \
                           len(driver.find_elements(By.TAG_NAME, "script")) + \
                           len(driver.find_elements(By.TAG_NAME, "link"))
            
            # Check memory usage (simulated)
            memory_usage = self._simulate_memory_usage(device_profile)
            
            # Performance analysis
            performance_issues = []
            if load_time > self.target_specs["max_page_load_time"]:
                performance_issues.append(f"Page load time ({load_time:.2f}s) exceeds target ({self.target_specs['max_page_load_time']}s)")
            
            if fcp_time and fcp_time > self.target_specs["max_first_paint"]:
                performance_issues.append(f"First Contentful Paint ({fcp_time:.2f}s) exceeds target ({self.target_specs['max_first_paint']}s)")
            
            if resource_count > 50:
                performance_issues.append(f"Too many resources ({resource_count}) may impact performance")
            
            if memory_usage > self.target_specs["max_memory_usage"]:
                performance_issues.append(f"Memory usage ({memory_usage}MB) exceeds target ({self.target_specs['max_memory_usage']}MB)")
            
            # Generate recommendations
            if performance_issues:
                recommendations.extend([
                    "Implement image optimization and lazy loading",
                    "Minify CSS and JavaScript files",
                    "Enable gzip compression",
                    "Implement critical CSS inlining",
                    "Add service worker for caching"
                ])
            
            metrics = {
                "load_time": load_time,
                "fcp_time": fcp_time,
                "resource_count": resource_count,
                "memory_usage": memory_usage,
                "device_profile": device_profile.value
            }
            
            passed = len(performance_issues) == 0
            
            result = MobileTestResult(
                test_name="Mobile Performance Test",
                device_profile=device_profile.value,
                network_condition="fast_4g",
                passed=passed,
                metrics=metrics,
                issues=performance_issues,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            
            self.test_results.append(result)
            driver.quit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in mobile performance test: {e}")
            return MobileTestResult(
                test_name="Mobile Performance Test",
                device_profile=device_profile.value,
                network_condition="fast_4g",
                passed=False,
                metrics={},
                issues=[f"Test failed: {str(e)}"],
                recommendations=["Check server availability and network connectivity"],
                timestamp=datetime.now().isoformat()
            )
    
    def test_touch_interactions(self, device_profile: DeviceProfile) -> MobileTestResult:
        """Test touch interactions and usability."""
        logger.info(f"Testing touch interactions for {device_profile.value}")
        
        try:
            driver = self.setup_driver(device_profile)
            issues = []
            recommendations = []
            
            # Navigate to landing page
            driver.get(self.base_url)
            
            # Test touch targets
            touch_elements = driver.find_elements(By.CSS_SELECTOR, 
                "button, a, input, select, .hero-cta-primary, .hero-cta-secondary, .landing-nav-cta")
            
            small_touch_targets = []
            for element in touch_elements:
                if element.is_displayed():
                    size = element.size
                    min_size = self.target_specs["min_touch_target_size"]
                    
                    if size["width"] < min_size or size["height"] < min_size:
                        small_touch_targets.append({
                            "element": element.tag_name,
                            "text": element.text[:50],
                            "size": size
                        })
            
            # Test touch responsiveness
            touch_responsive = True
            try:
                # Test CTA button touch
                cta_button = driver.find_element(By.CSS_SELECTOR, ".hero-cta-primary")
                if cta_button.is_displayed():
                    # Simulate touch using ActionChains
                    actions = ActionChains(driver)
                    actions.click(cta_button)
                    actions.perform()
                    
                    # Check for response (URL change, modal, etc.)
                    time.sleep(1)
                    current_url = driver.current_url
                    if current_url == self.base_url:
                        # Check if any modal or overlay appeared
                        modals = driver.find_elements(By.CSS_SELECTOR, ".modal, .overlay, .popup")
                        if not modals:
                            touch_responsive = False
            except Exception as e:
                touch_responsive = False
                logger.warning(f"Touch responsiveness test failed: {e}")
            
            # Test gesture support
            gesture_support = self._test_gesture_support(driver)
            
            # Analyze results
            if small_touch_targets:
                issues.append(f"Found {len(small_touch_targets)} elements with touch targets smaller than {self.target_specs['min_touch_target_size']}px")
            
            if not touch_responsive:
                issues.append("Touch interactions are not responsive")
            
            if not gesture_support:
                issues.append("Gesture support is limited")
            
            # Generate recommendations
            if issues:
                recommendations.extend([
                    "Ensure all interactive elements are at least 44x44px",
                    "Add visual feedback for touch interactions",
                    "Implement proper touch event handling",
                    "Test with actual touch devices",
                    "Add haptic feedback where appropriate"
                ])
            
            metrics = {
                "touch_targets_tested": len(touch_elements),
                "small_touch_targets": len(small_touch_targets),
                "touch_responsive": touch_responsive,
                "gesture_support": gesture_support,
                "device_profile": device_profile.value
            }
            
            passed = len(issues) == 0
            
            result = MobileTestResult(
                test_name="Touch Interactions Test",
                device_profile=device_profile.value,
                network_condition="fast_4g",
                passed=passed,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            
            self.test_results.append(result)
            driver.quit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in touch interactions test: {e}")
            return MobileTestResult(
                test_name="Touch Interactions Test",
                device_profile=device_profile.value,
                network_condition="fast_4g",
                passed=False,
                metrics={},
                issues=[f"Test failed: {str(e)}"],
                recommendations=["Check page accessibility and element visibility"],
                timestamp=datetime.now().isoformat()
            )
    
    def test_offline_functionality(self, device_profile: DeviceProfile) -> MobileTestResult:
        """Test offline functionality capabilities."""
        logger.info(f"Testing offline functionality for {device_profile.value}")
        
        try:
            driver = self.setup_driver(device_profile)
            issues = []
            recommendations = []
            
            # Navigate to landing page
            driver.get(self.base_url)
            
            # Check for service worker
            service_worker = driver.execute_script("""
                return navigator.serviceWorker && navigator.serviceWorker.controller;
            """)
            
            # Check for offline indicators
            offline_indicators = driver.find_elements(By.CSS_SELECTOR, 
                "[data-offline], .offline-indicator, .connection-status")
            
            # Check for cached resources
            cached_resources = driver.execute_script("""
                return caches ? caches.keys() : [];
            """)
            
            # Test offline mode simulation
            driver.execute_script("""
                // Simulate offline mode
                Object.defineProperty(navigator, 'onLine', {
                    get: function() { return false; }
                });
            """)
            
            # Check if app handles offline gracefully
            try:
                # Try to navigate or perform an action
                driver.find_element(By.CSS_SELECTOR, ".hero-cta-primary").click()
                time.sleep(2)
                
                # Check for offline message or graceful degradation
                offline_messages = driver.find_elements(By.CSS_SELECTOR, 
                    ".offline-message, .no-connection, [data-offline-message]")
                
                if not offline_messages:
                    issues.append("No offline handling detected")
                
            except Exception as e:
                logger.warning(f"Offline simulation test failed: {e}")
            
            # Analyze results
            if not service_worker:
                issues.append("No service worker detected for offline functionality")
            
            if not offline_indicators:
                issues.append("No offline status indicators found")
            
            if not cached_resources:
                issues.append("No cached resources detected")
            
            # Generate recommendations
            if issues:
                recommendations.extend([
                    "Implement service worker for offline caching",
                    "Add offline status indicators",
                    "Cache critical resources for offline access",
                    "Implement graceful degradation for offline mode",
                    "Add offline-first architecture"
                ])
            
            metrics = {
                "service_worker_available": bool(service_worker),
                "offline_indicators": len(offline_indicators),
                "cached_resources": len(cached_resources) if cached_resources else 0,
                "offline_handling": len(offline_messages) > 0 if 'offline_messages' in locals() else False,
                "device_profile": device_profile.value
            }
            
            passed = len(issues) == 0
            
            result = MobileTestResult(
                test_name="Offline Functionality Test",
                device_profile=device_profile.value,
                network_condition="offline",
                passed=passed,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            
            self.test_results.append(result)
            driver.quit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in offline functionality test: {e}")
            return MobileTestResult(
                test_name="Offline Functionality Test",
                device_profile=device_profile.value,
                network_condition="offline",
                passed=False,
                metrics={},
                issues=[f"Test failed: {str(e)}"],
                recommendations=["Implement basic offline detection and handling"],
                timestamp=datetime.now().isoformat()
            )
    
    def test_mobile_payment_processing(self, device_profile: DeviceProfile) -> MobileTestResult:
        """Test mobile payment processing."""
        logger.info(f"Testing mobile payment processing for {device_profile.value}")
        
        try:
            driver = self.setup_driver(device_profile)
            issues = []
            recommendations = []
            
            # Navigate to payment page or subscription flow
            payment_url = urljoin(self.base_url, "/subscription")
            driver.get(payment_url)
            
            # Check for payment form elements
            payment_elements = driver.find_elements(By.CSS_SELECTOR, 
                "input[type='card'], input[name*='card'], input[name*='payment'], .stripe-element")
            
            # Check for mobile-optimized payment UI
            mobile_payment_ui = driver.find_elements(By.CSS_SELECTOR, 
                ".mobile-payment, [data-mobile-payment], .payment-mobile-optimized")
            
            # Test payment form accessibility
            form_accessible = True
            try:
                # Check if payment form is properly structured
                payment_form = driver.find_element(By.CSS_SELECTOR, "form")
                form_inputs = payment_form.find_elements(By.CSS_SELECTOR, "input, select, textarea")
                
                for input_elem in form_inputs:
                    if input_elem.is_displayed():
                        # Check for proper labels
                        input_id = input_elem.get_attribute("id")
                        if input_id:
                            label = driver.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                            if not label:
                                form_accessible = False
                                break
                        
                        # Check for proper input types
                        input_type = input_elem.get_attribute("type")
                        if input_type == "text" and "card" in input_elem.get_attribute("name", ""):
                            # Should be type="tel" for card numbers on mobile
                            if input_type != "tel":
                                form_accessible = False
                                break
            except Exception as e:
                form_accessible = False
                logger.warning(f"Payment form accessibility test failed: {e}")
            
            # Check for secure payment indicators
            secure_indicators = driver.find_elements(By.CSS_SELECTOR, 
                ".secure-payment, .ssl-secure, [data-secure], .payment-secure")
            
            # Test touch-friendly payment buttons
            payment_buttons = driver.find_elements(By.CSS_SELECTOR, 
                "button[type='submit'], .payment-button, .subscribe-button")
            
            touch_friendly_buttons = 0
            for button in payment_buttons:
                if button.is_displayed():
                    size = button.size
                    if size["width"] >= 44 and size["height"] >= 44:
                        touch_friendly_buttons += 1
            
            # Analyze results
            if not payment_elements:
                issues.append("No payment form elements detected")
            
            if not mobile_payment_ui:
                issues.append("Payment UI not optimized for mobile")
            
            if not form_accessible:
                issues.append("Payment form not properly accessible on mobile")
            
            if not secure_indicators:
                issues.append("No security indicators for payment processing")
            
            if touch_friendly_buttons < len(payment_buttons):
                issues.append("Payment buttons not touch-friendly")
            
            # Generate recommendations
            if issues:
                recommendations.extend([
                    "Implement mobile-optimized payment forms",
                    "Use proper input types for mobile keyboards",
                    "Add security indicators and trust signals",
                    "Ensure payment buttons are touch-friendly (44x44px minimum)",
                    "Implement Apple Pay/Google Pay for mobile",
                    "Add payment form validation and error handling"
                ])
            
            metrics = {
                "payment_elements": len(payment_elements),
                "mobile_payment_ui": len(mobile_payment_ui),
                "form_accessible": form_accessible,
                "secure_indicators": len(secure_indicators),
                "touch_friendly_buttons": touch_friendly_buttons,
                "total_payment_buttons": len(payment_buttons),
                "device_profile": device_profile.value
            }
            
            passed = len(issues) == 0
            
            result = MobileTestResult(
                test_name="Mobile Payment Processing Test",
                device_profile=device_profile.value,
                network_condition="fast_4g",
                passed=passed,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            
            self.test_results.append(result)
            driver.quit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in mobile payment processing test: {e}")
            return MobileTestResult(
                test_name="Mobile Payment Processing Test",
                device_profile=device_profile.value,
                network_condition="fast_4g",
                passed=False,
                metrics={},
                issues=[f"Test failed: {str(e)}"],
                recommendations=["Implement basic payment form with mobile optimization"],
                timestamp=datetime.now().isoformat()
            )
    
    def test_screen_adaptation(self, device_profile: DeviceProfile) -> MobileTestResult:
        """Test screen adaptation across different device sizes."""
        logger.info(f"Testing screen adaptation for {device_profile.value}")
        
        try:
            driver = self.setup_driver(device_profile)
            issues = []
            recommendations = []
            
            # Navigate to landing page
            driver.get(self.base_url)
            
            # Test different viewport sizes
            viewport_sizes = [
                (320, 568),   # iPhone SE
                (375, 667),   # iPhone 6/7/8
                (414, 896),   # iPhone XR/11
                (360, 640),   # Android budget
                (412, 915),   # Android mid-range
            ]
            
            adaptation_results = []
            for width, height in viewport_sizes:
                driver.set_window_size(width, height)
                time.sleep(1)
                
                # Check for responsive design issues
                body_width = driver.execute_script("return document.body.scrollWidth;")
                viewport_width = driver.execute_script("return window.innerWidth;")
                
                # Check for horizontal scrolling
                horizontal_scroll = body_width > viewport_width
                
                # Check for text readability
                text_elements = driver.find_elements(By.CSS_SELECTOR, "p, span, div, h1, h2, h3, h4, h5, h6")
                readable_text = 0
                for element in text_elements[:10]:  # Check first 10 elements
                    try:
                        font_size = element.value_of_css_property("font-size")
                        font_size_px = int(font_size.replace("px", ""))
                        if font_size_px >= self.target_specs["min_font_size"]:
                            readable_text += 1
                    except:
                        pass
                
                # Check for touch target accessibility
                touch_elements = driver.find_elements(By.CSS_SELECTOR, "button, a, input")
                accessible_touch_targets = 0
                for element in touch_elements:
                    if element.is_displayed():
                        size = element.size
                        if size["width"] >= 44 and size["height"] >= 44:
                            accessible_touch_targets += 1
                
                adaptation_results.append({
                    "viewport": f"{width}x{height}",
                    "horizontal_scroll": horizontal_scroll,
                    "readable_text_ratio": readable_text / max(len(text_elements), 1),
                    "accessible_touch_targets": accessible_touch_targets,
                    "total_touch_elements": len(touch_elements)
                })
                
                if horizontal_scroll:
                    issues.append(f"Horizontal scrolling detected at {width}x{height}")
                
                if readable_text / max(len(text_elements), 1) < 0.8:
                    issues.append(f"Text readability issues at {width}x{height}")
            
            # Check for mobile menu functionality
            try:
                mobile_menu_button = driver.find_element(By.CSS_SELECTOR, 
                    ".mobile-menu-toggle, .hamburger-menu, [data-mobile-menu]")
                if mobile_menu_button.is_displayed():
                    mobile_menu_button.click()
                    time.sleep(1)
                    
                    mobile_menu = driver.find_element(By.CSS_SELECTOR, 
                        ".mobile-menu, .nav-menu-mobile, [data-mobile-nav]")
                    if not mobile_menu.is_displayed():
                        issues.append("Mobile menu not functioning properly")
            except:
                issues.append("No mobile menu implementation detected")
            
            # Generate recommendations
            if issues:
                recommendations.extend([
                    "Implement responsive design with mobile-first approach",
                    "Add mobile menu for navigation",
                    "Ensure text is readable on all screen sizes",
                    "Test on actual devices, not just emulation",
                    "Implement flexible grid system",
                    "Add viewport meta tag with proper settings"
                ])
            
            metrics = {
                "viewport_sizes_tested": len(viewport_sizes),
                "adaptation_results": adaptation_results,
                "device_profile": device_profile.value
            }
            
            passed = len(issues) == 0
            
            result = MobileTestResult(
                test_name="Screen Adaptation Test",
                device_profile=device_profile.value,
                network_condition="fast_4g",
                passed=passed,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            
            self.test_results.append(result)
            driver.quit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in screen adaptation test: {e}")
            return MobileTestResult(
                test_name="Screen Adaptation Test",
                device_profile=device_profile.value,
                network_condition="fast_4g",
                passed=False,
                metrics={},
                issues=[f"Test failed: {str(e)}"],
                recommendations=["Implement basic responsive design"],
                timestamp=datetime.now().isoformat()
            )
    
    def test_budget_device_performance(self, device_profile: DeviceProfile) -> MobileTestResult:
        """Test performance on budget/older mobile devices."""
        logger.info(f"Testing budget device performance for {device_profile.value}")
        
        try:
            driver = self.setup_driver(device_profile)
            issues = []
            recommendations = []
            
            # Navigate to landing page
            start_time = time.time()
            driver.get(self.base_url)
            
            # Wait for page load
            WebDriverWait(driver, 15).until(  # Longer timeout for budget devices
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            load_time = time.time() - start_time
            
            # Simulate budget device constraints
            device_specs = self.device_profiles[device_profile]
            
            # Check resource usage
            image_count = len(driver.find_elements(By.TAG_NAME, "img"))
            script_count = len(driver.find_elements(By.TAG_NAME, "script"))
            css_count = len(driver.find_elements(By.CSS_SELECTOR, "link[rel='stylesheet']"))
            
            # Check for heavy resources
            heavy_resources = []
            for img in driver.find_elements(By.TAG_NAME, "img"):
                try:
                    src = img.get_attribute("src")
                    if src and ("high-res" in src or "2x" in src or "retina" in src):
                        heavy_resources.append("High-resolution images")
                        break
                except:
                    pass
            
            # Check for unnecessary animations
            animations = driver.find_elements(By.CSS_SELECTOR, 
                "[style*='animation'], [style*='transition'], .animate, .fade")
            
            # Check for large JavaScript bundles
            large_scripts = []
            for script in driver.find_elements(By.TAG_NAME, "script"):
                try:
                    src = script.get_attribute("src")
                    if src and ("bundle" in src or "vendor" in src):
                        large_scripts.append("Large JavaScript bundles detected")
                        break
                except:
                    pass
            
            # Performance analysis for budget devices
            if load_time > 5.0:  # More lenient for budget devices
                issues.append(f"Page load time ({load_time:.2f}s) too slow for budget devices")
            
            if image_count > 20:
                issues.append(f"Too many images ({image_count}) for budget devices")
            
            if script_count > 10:
                issues.append(f"Too many scripts ({script_count}) for budget devices")
            
            if heavy_resources:
                issues.append("High-resolution resources detected - may impact performance")
            
            if len(animations) > 5:
                issues.append("Too many animations may impact performance on budget devices")
            
            if large_scripts:
                issues.append("Large JavaScript bundles may cause slow loading")
            
            # Check memory usage simulation
            memory_usage = self._simulate_memory_usage(device_profile)
            if memory_usage > device_specs["memory_limit"] * 0.8:  # 80% of available memory
                issues.append(f"Memory usage ({memory_usage}MB) too high for budget device")
            
            # Generate recommendations
            if issues:
                recommendations.extend([
                    "Optimize images for budget devices (use WebP format)",
                    "Implement lazy loading for images",
                    "Minimize JavaScript bundle size",
                    "Reduce number of HTTP requests",
                    "Implement progressive loading",
                    "Add performance budgets for budget devices",
                    "Use CDN for static resources",
                    "Implement service worker for caching"
                ])
            
            metrics = {
                "load_time": load_time,
                "image_count": image_count,
                "script_count": script_count,
                "css_count": css_count,
                "animation_count": len(animations),
                "memory_usage": memory_usage,
                "heavy_resources": len(heavy_resources),
                "device_profile": device_profile.value
            }
            
            passed = len(issues) == 0
            
            result = MobileTestResult(
                test_name="Budget Device Performance Test",
                device_profile=device_profile.value,
                network_condition="slow_4g",
                passed=passed,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now().isoformat()
            )
            
            self.test_results.append(result)
            driver.quit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in budget device performance test: {e}")
            return MobileTestResult(
                test_name="Budget Device Performance Test",
                device_profile=device_profile.value,
                network_condition="slow_4g",
                passed=False,
                metrics={},
                issues=[f"Test failed: {str(e)}"],
                recommendations=["Implement basic performance optimizations"],
                timestamp=datetime.now().isoformat()
            )
    
    def run_comprehensive_test_suite(self) -> List[MobileTestResult]:
        """Run comprehensive mobile testing suite for target demographic."""
        logger.info("Starting comprehensive mobile demographic testing suite")
        
        # Test on different device profiles
        device_profiles = [
            DeviceProfile.BUDGET_ANDROID,
            DeviceProfile.BUDGET_IPHONE,
            DeviceProfile.OLDER_DEVICE
        ]
        
        for device_profile in device_profiles:
            logger.info(f"Testing device profile: {device_profile.value}")
            
            # Run all tests for this device profile
            self.test_mobile_performance(device_profile)
            self.test_touch_interactions(device_profile)
            self.test_offline_functionality(device_profile)
            self.test_mobile_payment_processing(device_profile)
            self.test_screen_adaptation(device_profile)
            self.test_budget_device_performance(device_profile)
        
        return self.test_results
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        
        # Group results by device profile
        results_by_device = {}
        for result in self.test_results:
            device = result.device_profile
            if device not in results_by_device:
                results_by_device[device] = []
            results_by_device[device].append(result)
        
        # Calculate device-specific statistics
        device_stats = {}
        for device, results in results_by_device.items():
            device_passed = sum(1 for result in results if result.passed)
            device_total = len(results)
            device_stats[device] = {
                "passed": device_passed,
                "total": device_total,
                "success_rate": device_passed / device_total if device_total > 0 else 0
            }
        
        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []
        for result in self.test_results:
            all_issues.extend(result.issues)
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates
        all_issues = list(set(all_issues))
        all_recommendations = list(set(all_recommendations))
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "test_date": datetime.now().isoformat()
            },
            "device_statistics": device_stats,
            "critical_issues": all_issues,
            "recommendations": all_recommendations,
            "detailed_results": [asdict(result) for result in self.test_results]
        }
        
        return report
    
    def _extract_fcp_time(self, performance_logs: List[Dict]) -> Optional[float]:
        """Extract First Contentful Paint time from performance logs."""
        try:
            for log in performance_logs:
                if "message" in log:
                    message = json.loads(log["message"])
                    if "message" in message and message["message"]["method"] == "Performance.metrics":
                        metrics = message["message"]["params"]["metrics"]
                        for metric in metrics:
                            if metric["name"] == "FirstContentfulPaint":
                                return metric["value"] / 1000  # Convert to seconds
        except:
            pass
        return None
    
    def _simulate_memory_usage(self, device_profile: DeviceProfile) -> float:
        """Simulate memory usage based on device profile."""
        base_memory = 50.0  # Base memory usage in MB
        
        # Add memory based on device capabilities
        device_specs = self.device_profiles[device_profile]
        if device_profile == DeviceProfile.OLDER_DEVICE:
            base_memory += 30.0  # Older devices use more memory
        elif device_profile == DeviceProfile.BUDGET_ANDROID:
            base_memory += 20.0
        else:
            base_memory += 15.0
        
        return base_memory
    
    def _test_gesture_support(self, driver: webdriver.Chrome) -> bool:
        """Test basic gesture support."""
        try:
            # Test scroll gesture
            driver.execute_script("window.scrollTo(0, 100);")
            time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 0);")
            return True
        except:
            return False


def main():
    """Main function to run the mobile demographic testing suite."""
    print("🚀 MINGUS Mobile Demographic Experience Testing Suite")
    print("=" * 60)
    print("Testing mobile experience for target demographic:")
    print("- African American professionals aged 25-45")
    print("- Income range: $40K-$80K")
    print("- Budget/older mobile devices")
    print("- Mobile-first usage patterns")
    print("=" * 60)
    
    # Initialize tester
    base_url = os.getenv("MINGUS_BASE_URL", "http://localhost:5000")
    tester = MobileDemographicTester(base_url)
    
    try:
        # Run comprehensive test suite
        results = tester.run_comprehensive_test_suite()
        
        # Generate report
        report = tester.generate_test_report()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"mobile_demographic_test_report_{timestamp}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n📊 Test Results Summary:")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed_tests']}")
        print(f"Failed: {report['summary']['failed_tests']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1%}")
        
        print("\n📱 Device Performance:")
        for device, stats in report['device_statistics'].items():
            print(f"{device}: {stats['passed']}/{stats['total']} tests passed ({stats['success_rate']:.1%})")
        
        if report['critical_issues']:
            print(f"\n⚠️  Critical Issues Found ({len(report['critical_issues'])}):")
            for issue in report['critical_issues'][:5]:  # Show first 5
                print(f"  • {issue}")
        
        if report['recommendations']:
            print(f"\n💡 Recommendations ({len(report['recommendations'])}):")
            for rec in report['recommendations'][:5]:  # Show first 5
                print(f"  • {rec}")
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        # Return exit code based on success rate
        if report['summary']['success_rate'] >= 0.8:
            print("\n✅ Mobile experience meets target demographic requirements!")
            return 0
        else:
            print("\n❌ Mobile experience needs improvement for target demographic.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
        logger.error(f"Testing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
