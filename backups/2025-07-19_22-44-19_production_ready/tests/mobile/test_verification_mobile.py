"""
Mobile Responsiveness Testing for Phone Verification System
Tests mobile-specific functionality and responsive design
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time

class TestVerificationMobile:
    """Mobile responsiveness testing for verification system"""
    
    @pytest.fixture
    def mobile_driver(self):
        """Setup mobile Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_mobile_viewport_sizes(self, mobile_driver):
        """Test different mobile viewport sizes"""
        viewport_sizes = [
            (320, 568),   # iPhone 5/SE
            (375, 667),   # iPhone 6/7/8
            (414, 736),   # iPhone 6/7/8 Plus
            (375, 812),   # iPhone X/XS
            (414, 896),   # iPhone XR/XS Max
            (360, 640),   # Android small
            (412, 732),   # Android medium
            (412, 915),   # Android large
        ]
        
        for width, height in viewport_sizes:
            mobile_driver.set_window_size(width, height)
            mobile_driver.get("http://localhost:3000/verification")
            
            # Test that page loads without horizontal scroll
            body_width = mobile_driver.execute_script("return document.body.scrollWidth")
            viewport_width = mobile_driver.execute_script("return window.innerWidth")
            
            assert body_width <= viewport_width, \
                f"Page has horizontal scroll at {width}x{height}"
            
            # Test that key elements are visible
            phone_input = mobile_driver.find_element(By.ID, "phone-number")
            assert phone_input.is_displayed(), \
                f"Phone input not visible at {width}x{height}"
            
            send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
            assert send_button.is_displayed(), \
                f"Send button not visible at {width}x{height}"
    
    def test_touch_target_sizes(self, mobile_driver):
        """Test touch target sizes for mobile"""
        mobile_driver.set_window_size(375, 667)  # iPhone 6/7/8
        mobile_driver.get("http://localhost:3000/verification")
        
        # Test interactive elements have proper touch target sizes
        interactive_elements = mobile_driver.find_elements(By.CSS_SELECTOR, "input, button, select, textarea, a")
        
        for element in interactive_elements:
            if element.is_displayed():
                size = element.size
                
                # Touch targets should be at least 44x44 pixels (Apple guidelines)
                assert size['width'] >= 44, \
                    f"Touch target too narrow: {element.tag_name} ({size['width']}px)"
                assert size['height'] >= 44, \
                    f"Touch target too short: {element.tag_name} ({size['height']}px)"
                
                # Check for adequate spacing between touch targets
                location = element.location
                # This is a simplified check - in practice you'd check distance to other elements
    
    def test_mobile_keyboard_behavior(self, mobile_driver):
        """Test mobile keyboard behavior"""
        mobile_driver.set_window_size(375, 667)
        mobile_driver.get("http://localhost:3000/verification")
        
        # Test phone number input with mobile keyboard
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        phone_input.click()
        
        # Test numeric keyboard input
        phone_input.send_keys("1234567890")
        
        # Verify input works correctly
        assert phone_input.get_attribute("value") == "1234567890", \
            "Phone number input should accept numeric input"
        
        # Test verification code input
        # First send a code to trigger code input
        send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for code input to appear
        WebDriverWait(mobile_driver, 10).until(
            EC.presence_of_element_located((By.ID, "verification-code"))
        )
        
        code_input = mobile_driver.find_element(By.ID, "verification-code")
        code_input.click()
        
        # Test numeric input for verification code
        code_input.send_keys("123456")
        
        # Verify code input works
        assert code_input.get_attribute("value") == "123456", \
            "Verification code input should accept numeric input"
    
    def test_mobile_orientation_changes(self, mobile_driver):
        """Test mobile orientation changes"""
        mobile_driver.set_window_size(375, 667)  # Portrait
        mobile_driver.get("http://localhost:3000/verification")
        
        # Get initial element positions
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        initial_position = phone_input.location
        
        # Change to landscape
        mobile_driver.set_window_size(667, 375)  # Landscape
        
        # Wait for layout to adjust
        time.sleep(1)
        
        # Verify elements remain functional
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        assert phone_input.is_displayed(), "Phone input should remain visible in landscape"
        assert phone_input.is_enabled(), "Phone input should remain enabled in landscape"
        
        # Change back to portrait
        mobile_driver.set_window_size(375, 667)  # Portrait
        
        # Wait for layout to adjust
        time.sleep(1)
        
        # Verify elements remain functional
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        assert phone_input.is_displayed(), "Phone input should remain visible in portrait"
        assert phone_input.is_enabled(), "Phone input should remain enabled in portrait"
    
    def test_mobile_scroll_behavior(self, mobile_driver):
        """Test mobile scroll behavior"""
        mobile_driver.set_window_size(375, 667)
        mobile_driver.get("http://localhost:3000/verification")
        
        # Test vertical scrolling
        initial_scroll = mobile_driver.execute_script("return window.pageYOffset")
        
        # Scroll down
        mobile_driver.execute_script("window.scrollTo(0, 100)")
        time.sleep(0.5)
        
        scrolled_position = mobile_driver.execute_script("return window.pageYOffset")
        assert scrolled_position > initial_scroll, "Page should scroll vertically"
        
        # Test that form remains accessible after scroll
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        assert phone_input.is_displayed(), "Phone input should remain visible after scroll"
        
        # Test smooth scrolling back to top
        mobile_driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'})")
        time.sleep(1)
        
        final_scroll = mobile_driver.execute_script("return window.pageYOffset")
        assert final_scroll == 0, "Page should scroll back to top"
    
    def test_mobile_touch_gestures(self, mobile_driver):
        """Test mobile touch gestures"""
        mobile_driver.set_window_size(375, 667)
        mobile_driver.get("http://localhost:3000/verification")
        
        # Test tap gesture on phone input
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        mobile_driver.execute_script("arguments[0].click();", phone_input)
        
        # Verify input is focused
        assert phone_input == mobile_driver.switch_to.active_element, \
            "Phone input should be focused after tap"
        
        # Test tap gesture on send button
        send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        mobile_driver.execute_script("arguments[0].click();", send_button)
        
        # Verify button click is registered
        # This would typically show a loading state or success message
        time.sleep(1)
        
        # Test long press (should not trigger unwanted actions)
        mobile_driver.execute_script("""
            var element = arguments[0];
            var touchstart = new TouchEvent('touchstart', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            element.dispatchEvent(touchstart);
        """, phone_input)
        
        # Verify no unwanted actions occurred
        assert phone_input.get_attribute("value") == "", \
            "Long press should not trigger unwanted input"
    
    def test_mobile_network_conditions(self, mobile_driver):
        """Test mobile network conditions"""
        mobile_driver.set_window_size(375, 667)
        mobile_driver.get("http://localhost:3000/verification")
        
        # Simulate slow network
        mobile_driver.execute_cdp_cmd('Network.enable', {})
        mobile_driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': False,
            'latency': 1000,  # 1 second latency
            'downloadThroughput': 1024 * 1024,  # 1 MB/s
            'uploadThroughput': 1024 * 1024
        })
        
        # Test form submission under slow network
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for response (should be longer due to simulated latency)
        WebDriverWait(mobile_driver, 15).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
        )
        
        # Verify loading state was shown
        loading_elements = mobile_driver.find_elements(By.CSS_SELECTOR, ".loading")
        assert len(loading_elements) > 0, "Loading state should be shown under slow network"
    
    def test_mobile_battery_optimization(self, mobile_driver):
        """Test mobile battery optimization scenarios"""
        mobile_driver.set_window_size(375, 667)
        mobile_driver.get("http://localhost:3000/verification")
        
        # Simulate low battery mode
        mobile_driver.execute_cdp_cmd('Emulation.setCPUThrottlingRate', {'rate': 4})
        
        # Test form functionality under low battery
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Verify functionality remains
        WebDriverWait(mobile_driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
        )
    
    def test_mobile_accessibility_features(self, mobile_driver):
        """Test mobile accessibility features"""
        mobile_driver.set_window_size(375, 667)
        mobile_driver.get("http://localhost:3000/verification")
        
        # Test VoiceOver/Screen Reader compatibility
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        
        # Check for proper labeling
        aria_label = phone_input.get_attribute("aria-label")
        aria_labelledby = phone_input.get_attribute("aria-labelledby")
        placeholder = phone_input.get_attribute("placeholder")
        
        assert aria_label or aria_labelledby or placeholder, \
            "Phone input should have proper labeling for mobile screen readers"
        
        # Test focus management
        phone_input.click()
        assert phone_input == mobile_driver.switch_to.active_element, \
            "Phone input should be focused when tapped"
        
        # Test keyboard navigation
        phone_input.send_keys(Keys.TAB)
        send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        assert send_button == mobile_driver.switch_to.active_element, \
            "Focus should move to send button on tab"
    
    def test_mobile_error_handling(self, mobile_driver):
        """Test mobile error handling"""
        mobile_driver.set_window_size(375, 667)
        mobile_driver.get("http://localhost:3000/verification")
        
        # Test offline error handling
        mobile_driver.execute_cdp_cmd('Network.enable', {})
        mobile_driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': True,
            'latency': 0,
            'downloadThroughput': 0,
            'uploadThroughput': 0
        })
        
        # Try to submit form while offline
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for offline error message
        WebDriverWait(mobile_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
        )
        
        error_message = mobile_driver.find_element(By.CSS_SELECTOR, ".error-message")
        assert "offline" in error_message.text.lower() or "network" in error_message.text.lower(), \
            "Should show offline/network error message"
        
        # Re-enable network
        mobile_driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': False,
            'latency': 0,
            'downloadThroughput': 1024 * 1024,
            'uploadThroughput': 1024 * 1024
        })
    
    def test_mobile_performance(self, mobile_driver):
        """Test mobile performance metrics"""
        mobile_driver.set_window_size(375, 667)
        
        # Measure page load time
        start_time = time.time()
        mobile_driver.get("http://localhost:3000/verification")
        
        # Wait for page to be fully loaded
        WebDriverWait(mobile_driver, 10).until(
            EC.presence_of_element_located((By.ID, "phone-number"))
        )
        
        load_time = time.time() - start_time
        
        # Page should load within 3 seconds on mobile
        assert load_time < 3.0, f"Page load time too slow: {load_time:.2f}s"
        
        # Test form submission performance
        phone_input = mobile_driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        start_time = time.time()
        send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for response
        WebDriverWait(mobile_driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
        )
        
        submission_time = time.time() - start_time
        
        # Form submission should complete within 5 seconds
        assert submission_time < 5.0, f"Form submission too slow: {submission_time:.2f}s"
    
    def test_mobile_browser_compatibility(self, mobile_driver):
        """Test mobile browser compatibility"""
        # Test with different mobile user agents
        user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        ]
        
        for user_agent in user_agents:
            mobile_driver.execute_cdp_cmd('Network.setUserAgentOverride', {'userAgent': user_agent})
            mobile_driver.set_window_size(375, 667)
            mobile_driver.get("http://localhost:3000/verification")
            
            # Verify page loads correctly
            phone_input = mobile_driver.find_element(By.ID, "phone-number")
            assert phone_input.is_displayed(), \
                f"Phone input not visible with user agent: {user_agent}"
            
            # Test basic functionality
            phone_input.send_keys("+1234567890")
            send_button = mobile_driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
            assert send_button.is_enabled(), \
                f"Send button not enabled with user agent: {user_agent}" 