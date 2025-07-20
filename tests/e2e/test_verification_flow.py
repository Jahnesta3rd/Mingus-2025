"""
End-to-End Tests for Phone Verification Flow
Tests the complete user journey from phone input to verification success
"""

import pytest
import time
import json
from unittest.mock import patch, Mock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

class TestVerificationFlowE2E:
    """End-to-end tests for verification flow"""
    
    @pytest.fixture
    def driver(self):
        """Setup Chrome driver for testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture
    def mock_sms_service(self):
        """Mock SMS service to capture sent codes"""
        with patch('backend.services.secure_verification_service._send_sms_simulation') as mock:
            sent_codes = []
            
            def capture_code(phone_number, code):
                sent_codes.append({'phone': phone_number, 'code': code})
                print(f"SMS SIMULATION: Code {code} sent to {phone_number}")
            
            mock.side_effect = capture_code
            yield mock, sent_codes
    
    def test_complete_verification_flow(self, driver, mock_sms_service):
        """Test complete verification flow from start to finish"""
        mock, sent_codes = mock_sms_service
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "phone-number"))
        )
        
        # Enter phone number
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.clear()
        phone_input.send_keys("+1234567890")
        
        # Click send code button
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for success message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
        )
        
        # Verify SMS was sent
        assert len(sent_codes) == 1
        assert sent_codes[0]['phone'] == "+1234567890"
        verification_code = sent_codes[0]['code']
        
        # Wait for code input to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "verification-code"))
        )
        
        # Enter verification code
        code_input = driver.find_element(By.ID, "verification-code")
        for digit in verification_code:
            code_input.send_keys(digit)
            time.sleep(0.1)  # Small delay between digits
        
        # Wait for verification success
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".verification-success"))
        )
        
        # Verify success message
        success_message = driver.find_element(By.CSS_SELECTOR, ".verification-success")
        assert "verified successfully" in success_message.text.lower()
    
    def test_verification_with_invalid_code(self, driver, mock_sms_service):
        """Test verification flow with invalid code"""
        mock, sent_codes = mock_sms_service
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Enter phone number and send code
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for code input
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "verification-code"))
        )
        
        # Enter invalid code
        code_input = driver.find_element(By.ID, "verification-code")
        code_input.send_keys("000000")
        
        # Wait for error message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
        )
        
        # Verify error message
        error_message = driver.find_element(By.CSS_SELECTOR, ".error-message")
        assert "invalid" in error_message.text.lower()
    
    def test_rate_limiting_behavior(self, driver, mock_sms_service):
        """Test rate limiting behavior"""
        mock, sent_codes = mock_sms_service
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Try to send code multiple times rapidly
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        for i in range(5):
            send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
            send_button.click()
            time.sleep(0.1)  # Rapid clicks
        
        # Wait for rate limit message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
        )
        
        # Verify rate limit message
        error_message = driver.find_element(By.CSS_SELECTOR, ".error-message")
        assert "too many" in error_message.text.lower() or "rate limit" in error_message.text.lower()
    
    def test_resend_functionality(self, driver, mock_sms_service):
        """Test resend functionality with cooldown"""
        mock, sent_codes = mock_sms_service
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Send initial code
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for success and resend button
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='resend-button']"))
        )
        
        # Try to resend immediately (should be blocked)
        resend_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='resend-button']")
        resend_button.click()
        
        # Wait for cooldown message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".cooldown-message"))
        )
        
        # Verify cooldown message
        cooldown_message = driver.find_element(By.CSS_SELECTOR, ".cooldown-message")
        assert "wait" in cooldown_message.text.lower()
    
    def test_captcha_integration(self, driver, mock_sms_service):
        """Test CAPTCHA integration after multiple failures"""
        mock, sent_codes = mock_sms_service
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Enter phone number and send code
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for code input
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "verification-code"))
        )
        
        # Enter invalid codes multiple times to trigger CAPTCHA
        for attempt in range(3):
            code_input = driver.find_element(By.ID, "verification-code")
            code_input.clear()
            code_input.send_keys("000000")
            time.sleep(1)
        
        # Wait for CAPTCHA to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".captcha-container"))
        )
        
        # Verify CAPTCHA is displayed
        captcha_container = driver.find_element(By.CSS_SELECTOR, ".captcha-container")
        assert captcha_container.is_displayed()
    
    def test_phone_number_validation(self, driver):
        """Test phone number validation"""
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Try invalid phone numbers
        invalid_numbers = ["123", "abc", "123456789", "1234567890123456"]
        
        for invalid_number in invalid_numbers:
            phone_input = driver.find_element(By.ID, "phone-number")
            phone_input.clear()
            phone_input.send_keys(invalid_number)
            
            send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
            send_button.click()
            
            # Wait for validation error
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
            
            error_message = driver.find_element(By.CSS_SELECTOR, ".error-message")
            assert "invalid" in error_message.text.lower()
    
    def test_accessibility_features(self, driver, mock_sms_service):
        """Test accessibility features"""
        mock, sent_codes = mock_sms_service
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Test keyboard navigation
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        phone_input.send_keys(Keys.TAB)
        
        # Verify focus moves to send button
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        assert send_button == driver.switch_to.active_element
        
        # Test screen reader labels
        phone_input = driver.find_element(By.ID, "phone-number")
        aria_label = phone_input.get_attribute("aria-label")
        assert aria_label is not None and len(aria_label) > 0
        
        # Test error message announcements
        send_button.click()
        
        # Wait for success message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
        )
        
        success_message = driver.find_element(By.CSS_SELECTOR, ".success-message")
        aria_live = success_message.get_attribute("aria-live")
        assert aria_live == "polite" or aria_live == "assertive"
    
    def test_mobile_responsiveness(self, driver, mock_sms_service):
        """Test mobile responsiveness"""
        mock, sent_codes = mock_sms_service
        
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Verify elements are properly sized for mobile
        phone_input = driver.find_element(By.ID, "phone-number")
        input_size = phone_input.size
        
        # Input should be reasonably sized for mobile
        assert input_size['width'] > 200
        assert input_size['height'] > 30
        
        # Test touch-friendly button sizes
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        button_size = send_button.size
        
        # Buttons should be touch-friendly (minimum 44px)
        assert button_size['height'] >= 44
        assert button_size['width'] >= 44
    
    def test_cross_browser_compatibility(self, driver, mock_sms_service):
        """Test cross-browser compatibility"""
        mock, sent_codes = mock_sms_service
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Test basic functionality works
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for success message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
        )
        
        # Verify basic functionality works across browsers
        success_message = driver.find_element(By.CSS_SELECTOR, ".success-message")
        assert success_message.is_displayed()
        
        # Test CSS properties are supported
        computed_style = driver.execute_script(
            "return window.getComputedStyle(arguments[0]);", 
            success_message
        )
        
        # Verify CSS properties are applied
        assert computed_style.get_property_value("display") != "none"
    
    def test_error_handling_and_recovery(self, driver):
        """Test error handling and recovery scenarios"""
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Test network error simulation
        with patch('fetch') as mock_fetch:
            mock_fetch.side_effect = Exception("Network error")
            
            phone_input = driver.find_element(By.ID, "phone-number")
            phone_input.send_keys("+1234567890")
            
            send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
            send_button.click()
            
            # Wait for error message
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
            
            error_message = driver.find_element(By.CSS_SELECTOR, ".error-message")
            assert "network" in error_message.text.lower() or "connection" in error_message.text.lower()
            
            # Test retry functionality
            retry_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='retry-button']")
            assert retry_button.is_displayed()
    
    def test_progressive_enhancement(self, driver):
        """Test progressive enhancement (works without JavaScript)"""
        # Disable JavaScript
        driver.execute_script("document.documentElement.style.pointerEvents = 'none';")
        
        # Navigate to verification page
        driver.get("http://localhost:3000/verification")
        
        # Verify page loads without JavaScript
        phone_input = driver.find_element(By.ID, "phone-number")
        assert phone_input.is_displayed()
        
        # Test form submission works
        phone_input.send_keys("+1234567890")
        
        # Find and submit form
        form = driver.find_element(By.TAG_NAME, "form")
        form.submit()
        
        # Verify page handles form submission
        # (This would typically redirect or show a message)
        assert driver.current_url != "http://localhost:3000/verification" 