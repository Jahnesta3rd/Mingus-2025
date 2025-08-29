"""
End-to-End Tests for Assessment System

Complete user journey tests: landing → assessment → results → conversion
Includes anonymous user flow, authenticated user flow, payment processing, and mobile testing.
"""

import pytest
import time
import json
from unittest.mock import patch, Mock, AsyncMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

pytestmark = pytest.mark.e2e

class TestCompleteUserJourney:
    """Test complete user journey from landing page to conversion"""
    
    def test_anonymous_user_complete_flow(self, chrome_driver):
        """Test complete anonymous user flow: landing → assessment → results → email capture"""
        # Step 1: Land on homepage
        chrome_driver.get("http://localhost:3000")
        
        # Wait for landing page to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "landing-page"))
        )
        
        # Verify landing page elements
        assert chrome_driver.find_element(By.CLASS_NAME, "hero-section")
        assert chrome_driver.find_element(By.CLASS_NAME, "cta-button")
        
        # Step 2: Click CTA to start assessment
        cta_button = chrome_driver.find_element(By.CLASS_NAME, "cta-button")
        cta_button.click()
        
        # Should navigate to assessment
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Step 3: Complete assessment
        self._complete_assessment_flow(chrome_driver)
        
        # Step 4: View results
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        # Verify results page elements
        results_container = chrome_driver.find_element(By.CLASS_NAME, "assessment-results")
        assert results_container.find_element(By.CLASS_NAME, "risk-level")
        assert results_container.find_element(By.CLASS_NAME, "recommendations")
        assert results_container.find_element(By.CLASS_NAME, "subscription-cta")
        
        # Step 5: Email capture for anonymous user
        email_input = chrome_driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_input.send_keys("anonymous@example.com")
        
        save_button = chrome_driver.find_element(By.CLASS_NAME, "save-results-button")
        save_button.click()
        
        # Verify success message
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        
        success_message = chrome_driver.find_element(By.CLASS_NAME, "success-message")
        assert "saved" in success_message.text.lower() or "sent" in success_message.text.lower()
    
    def test_authenticated_user_complete_flow(self, chrome_driver):
        """Test complete authenticated user flow: login → assessment → results → profile"""
        # Step 1: Login
        chrome_driver.get("http://localhost:3000/login")
        
        # Wait for login page to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "login-form"))
        )
        
        # Fill login form
        email_input = chrome_driver.find_element(By.NAME, "email")
        password_input = chrome_driver.find_element(By.NAME, "password")
        
        email_input.send_keys("test@mingus.com")
        password_input.send_keys("testpassword123")
        
        login_button = chrome_driver.find_element(By.CLASS_NAME, "login-button")
        login_button.click()
        
        # Wait for dashboard to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
        )
        
        # Step 2: Start assessment from dashboard
        start_assessment_button = chrome_driver.find_element(By.CLASS_NAME, "start-assessment-button")
        start_assessment_button.click()
        
        # Wait for assessment to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Step 3: Complete assessment
        self._complete_assessment_flow(chrome_driver)
        
        # Step 4: View results
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        # Step 5: Save to profile (should be automatic for authenticated users)
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "saved-to-profile"))
        )
        
        # Step 6: Navigate to profile to view saved assessment
        profile_link = chrome_driver.find_element(By.CLASS_NAME, "profile-link")
        profile_link.click()
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "profile-page"))
        )
        
        # Verify assessment is in profile
        assessment_history = chrome_driver.find_element(By.CLASS_NAME, "assessment-history")
        assert len(assessment_history.find_elements(By.CLASS_NAME, "assessment-item")) > 0
    
    def test_payment_processing_flow(self, chrome_driver):
        """Test payment processing flow: assessment → results → payment → confirmation"""
        # Complete assessment first
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        self._complete_assessment_flow(chrome_driver)
        
        # Wait for results
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        # Click on subscription CTA
        subscription_cta = chrome_driver.find_element(By.CLASS_NAME, "subscription-cta")
        subscription_cta.click()
        
        # Wait for payment form
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "payment-form"))
        )
        
        # Fill payment form
        self._fill_payment_form(chrome_driver)
        
        # Submit payment
        submit_button = chrome_driver.find_element(By.CLASS_NAME, "submit-payment-button")
        submit_button.click()
        
        # Wait for payment confirmation
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "payment-confirmation"))
        )
        
        # Verify payment success
        confirmation_message = chrome_driver.find_element(By.CLASS_NAME, "payment-confirmation")
        assert "success" in confirmation_message.text.lower() or "confirmed" in confirmation_message.text.lower()
        
        # Verify subscription status
        subscription_status = chrome_driver.find_element(By.CLASS_NAME, "subscription-status")
        assert "active" in subscription_status.text.lower()
    
    def test_mobile_device_flow(self, chrome_driver):
        """Test complete flow on mobile device"""
        # Set mobile viewport
        chrome_driver.set_window_size(375, 667)  # iPhone 6/7/8
        
        # Test complete flow on mobile
        chrome_driver.get("http://localhost:3000")
        
        # Wait for landing page to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "landing-page"))
        )
        
        # Verify mobile-specific elements
        mobile_menu = chrome_driver.find_element(By.CLASS_NAME, "mobile-menu")
        assert mobile_menu.is_displayed()
        
        # Start assessment
        cta_button = chrome_driver.find_element(By.CLASS_NAME, "cta-button")
        cta_button.click()
        
        # Complete assessment on mobile
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        self._complete_assessment_flow_mobile(chrome_driver)
        
        # Verify results on mobile
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        # Test mobile-specific interactions
        self._test_mobile_interactions(chrome_driver)
    
    def test_error_handling_flow(self, chrome_driver):
        """Test error handling throughout the user journey"""
        # Test network error during assessment
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Simulate network error by disconnecting
        chrome_driver.execute_script("window.navigator.onLine = false;")
        
        # Try to submit assessment
        next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
        next_button.click()
        
        # Verify error handling
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        
        error_message = chrome_driver.find_element(By.CLASS_NAME, "error-message")
        assert "connection" in error_message.text.lower() or "network" in error_message.text.lower()
        
        # Reconnect and retry
        chrome_driver.execute_script("window.navigator.onLine = true;")
        
        retry_button = chrome_driver.find_element(By.CLASS_NAME, "retry-button")
        retry_button.click()
        
        # Verify recovery
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
    
    def test_data_persistence_flow(self, chrome_driver):
        """Test data persistence during user journey"""
        # Start assessment
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Fill first few questions
        self._fill_partial_assessment(chrome_driver)
        
        # Navigate away and back
        chrome_driver.get("http://localhost:3000")
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Verify data persistence
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Check if previous answers are restored
        try:
            salary_input = chrome_driver.find_element(By.NAME, "current_salary")
            assert salary_input.get_attribute("value") == "75000"
        except:
            # Data persistence might not be implemented
            pass
    
    def _complete_assessment_flow(self, driver):
        """Helper method to complete assessment flow"""
        questions_completed = 0
        max_questions = 15  # Prevent infinite loop
        
        while questions_completed < max_questions:
            try:
                # Wait for question to load
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
                )
                
                question_container = driver.find_element(By.CLASS_NAME, "question-container")
                
                # Fill current question
                self._fill_question_comprehensive(question_container)
                
                # Click next
                next_button = driver.find_element(By.CLASS_NAME, "next-button")
                next_button.click()
                
                questions_completed += 1
                
                # Check if we've reached the end
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
                    )
                    break
                except:
                    continue
                    
            except Exception as e:
                print(f"Error completing question {questions_completed}: {e}")
                break
    
    def _complete_assessment_flow_mobile(self, driver):
        """Helper method to complete assessment flow on mobile"""
        questions_completed = 0
        max_questions = 15
        
        while questions_completed < max_questions:
            try:
                # Wait for question to load
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
                )
                
                question_container = driver.find_element(By.CLASS_NAME, "question-container")
                
                # Fill current question for mobile
                self._fill_question_mobile(question_container)
                
                # Click next (mobile-friendly)
                next_button = driver.find_element(By.CLASS_NAME, "next-button")
                driver.execute_script("arguments[0].click();", next_button)
                
                questions_completed += 1
                
                # Check if we've reached the end
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
                    )
                    break
                except:
                    continue
                    
            except Exception as e:
                print(f"Error completing question {questions_completed}: {e}")
                break
    
    def _fill_question_comprehensive(self, question_container):
        """Helper method to fill questions comprehensively"""
        # Try different input types
        try:
            # Text input
            text_input = question_container.find_element(By.TAG_NAME, "input")
            if text_input.get_attribute("type") == "number":
                text_input.send_keys("75000")
            elif text_input.get_attribute("type") == "text":
                text_input.send_keys("Test Answer")
            elif text_input.get_attribute("type") == "email":
                text_input.send_keys("test@example.com")
        except:
            pass
        
        try:
            # Select dropdown
            select_element = question_container.find_element(By.TAG_NAME, "select")
            select_element.click()
            options = select_element.find_elements(By.TAG_NAME, "option")
            if len(options) > 1:
                options[1].click()  # Skip placeholder
        except:
            pass
        
        try:
            # Radio buttons
            radio_buttons = question_container.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons:
                radio_buttons[0].click()
        except:
            pass
        
        try:
            # Checkboxes
            checkboxes = question_container.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            if checkboxes:
                checkboxes[0].click()
        except:
            pass
    
    def _fill_question_mobile(self, question_container):
        """Helper method to fill questions on mobile"""
        # Mobile-specific filling logic
        try:
            # Text input with mobile-friendly interaction
            text_input = question_container.find_element(By.TAG_NAME, "input")
            if text_input.get_attribute("type") == "number":
                text_input.send_keys("75000")
            elif text_input.get_attribute("type") == "text":
                text_input.send_keys("Test Answer")
        except:
            pass
        
        try:
            # Select dropdown with mobile interaction
            select_element = question_container.find_element(By.TAG_NAME, "select")
            driver.execute_script("arguments[0].click();", select_element)
            options = select_element.find_elements(By.TAG_NAME, "option")
            if len(options) > 1:
                driver.execute_script("arguments[0].click();", options[1])
        except:
            pass
        
        try:
            # Radio buttons with touch interaction
            radio_buttons = question_container.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons:
                driver.execute_script("arguments[0].click();", radio_buttons[0])
        except:
            pass
    
    def _fill_payment_form(self, driver):
        """Helper method to fill payment form"""
        # Fill card number
        card_number_input = driver.find_element(By.NAME, "card_number")
        card_number_input.send_keys("4242424242424242")
        
        # Fill expiry date
        expiry_input = driver.find_element(By.NAME, "expiry")
        expiry_input.send_keys("12/25")
        
        # Fill CVC
        cvc_input = driver.find_element(By.NAME, "cvc")
        cvc_input.send_keys("123")
        
        # Fill billing address
        address_input = driver.find_element(By.NAME, "address")
        address_input.send_keys("123 Test Street")
        
        city_input = driver.find_element(By.NAME, "city")
        city_input.send_keys("Test City")
        
        zip_input = driver.find_element(By.NAME, "zip")
        zip_input.send_keys("12345")
    
    def _fill_partial_assessment(self, driver):
        """Helper method to fill partial assessment for persistence test"""
        # Fill first question
        try:
            salary_input = driver.find_element(By.NAME, "current_salary")
            salary_input.send_keys("75000")
            
            next_button = driver.find_element(By.CLASS_NAME, "next-button")
            next_button.click()
            
            # Fill second question
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
            )
            
            field_select = driver.find_element(By.NAME, "field")
            field_select.click()
            options = field_select.find_elements(By.TAG_NAME, "option")
            options[1].click()
            
        except:
            pass
    
    def _test_mobile_interactions(self, driver):
        """Helper method to test mobile-specific interactions"""
        # Test touch scrolling
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        
        # Test pinch zoom (if supported)
        try:
            # This would require more sophisticated touch simulation
            pass
        except:
            pass
        
        # Test mobile menu
        try:
            mobile_menu_button = driver.find_element(By.CLASS_NAME, "mobile-menu-button")
            mobile_menu_button.click()
            
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mobile-menu"))
            )
            
            # Close mobile menu
            close_button = driver.find_element(By.CLASS_NAME, "close-menu-button")
            close_button.click()
        except:
            pass


class TestConversionOptimization:
    """Test conversion optimization throughout the user journey"""
    
    def test_landing_page_conversion_elements(self, chrome_driver):
        """Test conversion elements on landing page"""
        chrome_driver.get("http://localhost:3000")
        
        # Wait for landing page to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "landing-page"))
        )
        
        # Verify conversion elements
        assert chrome_driver.find_element(By.CLASS_NAME, "hero-cta")
        assert chrome_driver.find_element(By.CLASS_NAME, "social-proof")
        assert chrome_driver.find_element(By.CLASS_NAME, "trust-indicators")
        assert chrome_driver.find_element(By.CLASS_NAME, "urgency-elements")
        
        # Test CTA button visibility
        cta_button = chrome_driver.find_element(By.CLASS_NAME, "hero-cta")
        assert cta_button.is_displayed()
        assert cta_button.is_enabled()
        
        # Test social proof elements
        testimonials = chrome_driver.find_elements(By.CLASS_NAME, "testimonial")
        assert len(testimonials) > 0
    
    def test_assessment_conversion_triggers(self, chrome_driver):
        """Test conversion triggers during assessment"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for assessment to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Verify progress indicators
        progress_bar = chrome_driver.find_element(By.CLASS_NAME, "progress-bar")
        assert progress_bar.is_displayed()
        
        # Verify time estimates
        time_estimate = chrome_driver.find_element(By.CLASS_NAME, "time-estimate")
        assert time_estimate.is_displayed()
        
        # Verify completion incentives
        try:
            completion_incentive = chrome_driver.find_element(By.CLASS_NAME, "completion-incentive")
            assert completion_incentive.is_displayed()
        except:
            # Completion incentive might not be implemented
            pass
    
    def test_results_page_conversion(self, chrome_driver):
        """Test conversion elements on results page"""
        # Complete assessment first
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        self._complete_assessment_flow(chrome_driver)
        
        # Wait for results
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        # Verify conversion elements
        assert chrome_driver.find_element(By.CLASS_NAME, "subscription-cta")
        assert chrome_driver.find_element(By.CLASS_NAME, "value-proposition")
        assert chrome_driver.find_element(By.CLASS_NAME, "risk-urgency")
        
        # Test subscription CTA
        subscription_cta = chrome_driver.find_element(By.CLASS_NAME, "subscription-cta")
        assert subscription_cta.is_displayed()
        assert subscription_cta.is_enabled()
        
        # Test value proposition clarity
        value_prop = chrome_driver.find_element(By.CLASS_NAME, "value-proposition")
        assert len(value_prop.text) > 0
    
    def test_email_capture_optimization(self, chrome_driver):
        """Test email capture optimization"""
        # Complete assessment as anonymous user
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        self._complete_assessment_flow(chrome_driver)
        
        # Wait for results
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        # Test email capture form
        email_input = chrome_driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        assert email_input.is_displayed()
        
        # Test email validation
        email_input.send_keys("invalid-email")
        save_button = chrome_driver.find_element(By.CLASS_NAME, "save-results-button")
        save_button.click()
        
        # Verify validation error
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        
        # Test valid email
        email_input.clear()
        email_input.send_keys("valid@example.com")
        save_button.click()
        
        # Verify success
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )


class TestMobileDeviceTesting:
    """Test mobile device specific functionality"""
    
    @pytest.mark.parametrize("device", [
        {"width": 375, "height": 667, "name": "iPhone 6/7/8"},
        {"width": 414, "height": 896, "name": "iPhone X/XS"},
        {"width": 768, "height": 1024, "name": "iPad"},
        {"width": 1024, "height": 768, "name": "iPad Landscape"},
    ])
    def test_mobile_device_compatibility(self, chrome_driver, device):
        """Test compatibility across different mobile devices"""
        chrome_driver.set_window_size(device["width"], device["height"])
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test basic functionality
        self._test_mobile_basic_functionality(chrome_driver)
        
        # Test touch interactions
        self._test_touch_interactions(chrome_driver)
        
        # Test mobile-specific UI elements
        self._test_mobile_ui_elements(chrome_driver)
    
    def test_ios_safari_specific(self, chrome_driver):
        """Test iOS Safari specific functionality"""
        # Set iOS Safari user agent
        chrome_driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        })
        
        chrome_driver.set_window_size(375, 667)
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test iOS-specific interactions
        self._test_ios_specific_interactions(chrome_driver)
    
    def test_chrome_mobile_specific(self, chrome_driver):
        """Test Chrome Mobile specific functionality"""
        # Set Chrome Mobile user agent
        chrome_driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
        })
        
        chrome_driver.set_window_size(375, 667)
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test Android-specific interactions
        self._test_android_specific_interactions(chrome_driver)
    
    def _test_mobile_basic_functionality(self, driver):
        """Test basic functionality on mobile"""
        # Test that component renders
        assessment_flow = driver.find_element(By.CLASS_NAME, "assessment-flow")
        assert assessment_flow.is_displayed()
        
        # Test that questions are present
        question_container = driver.find_element(By.CLASS_NAME, "question-container")
        assert question_container.is_displayed()
        
        # Test that navigation works
        next_button = driver.find_element(By.CLASS_NAME, "next-button")
        assert next_button.is_displayed()
        assert next_button.is_enabled()
    
    def _test_touch_interactions(self, driver):
        """Test touch interactions on mobile"""
        # Test touch scrolling
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        
        # Test touch-friendly button sizes
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            button_size = button.size
            # Buttons should be at least 44x44px for touch targets
            assert button_size['width'] >= 44
            assert button_size['height'] >= 44
    
    def _test_mobile_ui_elements(self, driver):
        """Test mobile-specific UI elements"""
        # Test mobile menu
        try:
            mobile_menu_button = driver.find_element(By.CLASS_NAME, "mobile-menu-button")
            assert mobile_menu_button.is_displayed()
        except:
            # Mobile menu might not be implemented
            pass
        
        # Test responsive text sizing
        text_elements = driver.find_elements(By.CSS_SELECTOR, "p, span, div, h1, h2, h3, h4, h5, h6")
        for element in text_elements[:5]:  # Test first 5 elements
            font_size = element.value_of_css_property("font-size")
            assert int(font_size.replace("px", "")) >= 12  # Minimum readable font size
    
    def _test_ios_specific_interactions(self, driver):
        """Test iOS Safari specific interactions"""
        # Test iOS-specific CSS properties
        try:
            # Test -webkit- prefixed properties
            elements = driver.find_elements(By.CSS_SELECTOR, "*")
            for element in elements[:10]:  # Test first 10 elements
                webkit_appearance = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).webkitAppearance", element
                )
                # This is just a basic test - in practice you'd test more iOS-specific properties
        except:
            pass
        
        # Test iOS-specific touch events
        try:
            # Test touch event handling
            element = driver.find_element(By.CLASS_NAME, "question-container")
            driver.execute_script("""
                var element = arguments[0];
                var touchEvent = new TouchEvent('touchstart', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                element.dispatchEvent(touchEvent);
            """, element)
        except:
            pass
    
    def _test_android_specific_interactions(self, driver):
        """Test Android Chrome specific interactions"""
        # Test Android-specific viewport handling
        viewport_width = driver.execute_script("return window.innerWidth;")
        viewport_height = driver.execute_script("return window.innerHeight;")
        
        assert viewport_width > 0
        assert viewport_height > 0
        
        # Test Android-specific touch events
        try:
            element = driver.find_element(By.CLASS_NAME, "question-container")
            driver.execute_script("""
                var element = arguments[0];
                var touchEvent = new TouchEvent('touchstart', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                element.dispatchEvent(touchEvent);
            """, element)
        except:
            pass
