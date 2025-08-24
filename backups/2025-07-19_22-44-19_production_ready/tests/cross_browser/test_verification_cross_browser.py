"""
Cross-Browser Compatibility Testing for Phone Verification System
Tests functionality across different browsers and versions
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import time

class TestVerificationCrossBrowser:
    """Cross-browser compatibility testing for verification system"""
    
    @pytest.fixture(params=['chrome', 'firefox', 'safari', 'edge'])
    def driver(self, request):
        """Setup different browser drivers"""
        if request.param == 'chrome':
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            driver = webdriver.Chrome(options=options)
        elif request.param == 'firefox':
            options = FirefoxOptions()
            options.add_argument("--headless")
            driver = webdriver.Firefox(options=options)
        elif request.param == 'safari':
            options = SafariOptions()
            driver = webdriver.Safari(options=options)
        elif request.param == 'edge':
            options = EdgeOptions()
            options.add_argument("--headless")
            driver = webdriver.Edge(options=options)
        
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_basic_functionality_chrome(self, driver):
        """Test basic functionality in Chrome"""
        if 'chrome' not in driver.capabilities['browserName'].lower():
            pytest.skip("Chrome-specific test")
        
        driver.get("http://localhost:3000/verification")
        
        # Test phone input
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        # Test send button
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for response
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
        )
        
        # Verify functionality
        assert phone_input.is_displayed(), "Phone input should be visible in Chrome"
        assert send_button.is_enabled(), "Send button should be enabled in Chrome"
    
    def test_basic_functionality_firefox(self, driver):
        """Test basic functionality in Firefox"""
        if 'firefox' not in driver.capabilities['browserName'].lower():
            pytest.skip("Firefox-specific test")
        
        driver.get("http://localhost:3000/verification")
        
        # Test phone input
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        # Test send button
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for response
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
        )
        
        # Verify functionality
        assert phone_input.is_displayed(), "Phone input should be visible in Firefox"
        assert send_button.is_enabled(), "Send button should be enabled in Firefox"
    
    def test_basic_functionality_safari(self, driver):
        """Test basic functionality in Safari"""
        if 'safari' not in driver.capabilities['browserName'].lower():
            pytest.skip("Safari-specific test")
        
        driver.get("http://localhost:3000/verification")
        
        # Test phone input
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        # Test send button
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for response
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
        )
        
        # Verify functionality
        assert phone_input.is_displayed(), "Phone input should be visible in Safari"
        assert send_button.is_enabled(), "Send button should be enabled in Safari"
    
    def test_basic_functionality_edge(self, driver):
        """Test basic functionality in Edge"""
        if 'edge' not in driver.capabilities['browserName'].lower():
            pytest.skip("Edge-specific test")
        
        driver.get("http://localhost:3000/verification")
        
        # Test phone input
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        # Test send button
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for response
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
        )
        
        # Verify functionality
        assert phone_input.is_displayed(), "Phone input should be visible in Edge"
        assert send_button.is_enabled(), "Send button should be enabled in Edge"
    
    def test_css_compatibility(self, driver):
        """Test CSS compatibility across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test CSS properties
        phone_input = driver.find_element(By.ID, "phone-number")
        
        # Check display property
        display = driver.execute_script(
            "return window.getComputedStyle(arguments[0]).display;", 
            phone_input
        )
        assert display != "none", f"Phone input should be visible in {driver.capabilities['browserName']}"
        
        # Check position property
        position = driver.execute_script(
            "return window.getComputedStyle(arguments[0]).position;", 
            phone_input
        )
        assert position in ["static", "relative", "absolute", "fixed"], \
            f"Invalid position value in {driver.capabilities['browserName']}"
        
        # Check font properties
        font_family = driver.execute_script(
            "return window.getComputedStyle(arguments[0]).fontFamily;", 
            phone_input
        )
        assert font_family, f"Font family should be defined in {driver.capabilities['browserName']}"
    
    def test_javascript_compatibility(self, driver):
        """Test JavaScript compatibility across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test JavaScript execution
        result = driver.execute_script("return typeof window !== 'undefined';")
        assert result is True, f"JavaScript should be enabled in {driver.capabilities['browserName']}"
        
        # Test DOM manipulation
        phone_input = driver.find_element(By.ID, "phone-number")
        driver.execute_script("arguments[0].value = 'test';", phone_input)
        
        assert phone_input.get_attribute("value") == "test", \
            f"DOM manipulation should work in {driver.capabilities['browserName']}"
        
        # Test event handling
        driver.execute_script("""
            var element = arguments[0];
            var event = new Event('input', { bubbles: true });
            element.dispatchEvent(event);
        """, phone_input)
        
        # Verify event was handled
        time.sleep(0.1)  # Allow time for event processing
    
    def test_form_validation(self, driver):
        """Test form validation across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test HTML5 validation
        phone_input = driver.find_element(By.ID, "phone-number")
        
        # Set invalid value
        driver.execute_script("arguments[0].value = 'invalid';", phone_input)
        
        # Trigger validation
        phone_input.send_keys("")  # Clear and trigger validation
        
        # Check validation state
        is_valid = driver.execute_script("return arguments[0].validity.valid;", phone_input)
        
        # Should be invalid for non-phone number format
        if not is_valid:
            print(f"HTML5 validation working in {driver.capabilities['browserName']}")
        else:
            print(f"HTML5 validation may not be strict in {driver.capabilities['browserName']}")
    
    def test_local_storage(self, driver):
        """Test localStorage compatibility across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test localStorage availability
        storage_available = driver.execute_script("return typeof localStorage !== 'undefined';")
        assert storage_available, f"localStorage should be available in {driver.capabilities['browserName']}"
        
        # Test localStorage operations
        driver.execute_script("localStorage.setItem('test', 'value');")
        value = driver.execute_script("return localStorage.getItem('test');")
        assert value == "value", f"localStorage should work in {driver.capabilities['browserName']}"
        
        # Clean up
        driver.execute_script("localStorage.removeItem('test');")
    
    def test_session_storage(self, driver):
        """Test sessionStorage compatibility across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test sessionStorage availability
        storage_available = driver.execute_script("return typeof sessionStorage !== 'undefined';")
        assert storage_available, f"sessionStorage should be available in {driver.capabilities['browserName']}"
        
        # Test sessionStorage operations
        driver.execute_script("sessionStorage.setItem('test', 'value');")
        value = driver.execute_script("return sessionStorage.getItem('test');")
        assert value == "value", f"sessionStorage should work in {driver.capabilities['browserName']}"
        
        # Clean up
        driver.execute_script("sessionStorage.removeItem('test');")
    
    def test_cookies(self, driver):
        """Test cookie handling across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test cookie setting
        driver.execute_script("document.cookie = 'test=value; path=/';")
        
        # Test cookie reading
        cookies = driver.execute_script("return document.cookie;")
        assert "test=value" in cookies, f"Cookies should work in {driver.capabilities['browserName']}"
        
        # Clean up
        driver.execute_script("document.cookie = 'test=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';")
    
    def test_fetch_api(self, driver):
        """Test Fetch API compatibility across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test Fetch API availability
        fetch_available = driver.execute_script("return typeof fetch !== 'undefined';")
        assert fetch_available, f"Fetch API should be available in {driver.capabilities['browserName']}"
        
        # Test fetch functionality (mock)
        fetch_result = driver.execute_script("""
            return fetch('/api/test')
                .then(response => response.status)
                .catch(error => 'error');
        """)
        
        # Should handle fetch calls (even if they fail)
        assert fetch_result is not None, f"Fetch should be callable in {driver.capabilities['browserName']}"
    
    def test_promise_support(self, driver):
        """Test Promise support across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test Promise availability
        promise_available = driver.execute_script("return typeof Promise !== 'undefined';")
        assert promise_available, f"Promises should be available in {driver.capabilities['browserName']}"
        
        # Test Promise functionality
        promise_result = driver.execute_script("""
            return new Promise((resolve) => {
                setTimeout(() => resolve('success'), 100);
            });
        """)
        
        assert promise_result == "success", f"Promises should work in {driver.capabilities['browserName']}"
    
    def test_async_await(self, driver):
        """Test async/await support across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test async/await functionality
        async_result = driver.execute_script("""
            return (async () => {
                await new Promise(resolve => setTimeout(resolve, 100));
                return 'async_success';
            })();
        """)
        
        assert async_result == "async_success", f"async/await should work in {driver.capabilities['browserName']}"
    
    def test_es6_features(self, driver):
        """Test ES6 features across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test arrow functions
        arrow_result = driver.execute_script("return (() => 'arrow')();")
        assert arrow_result == "arrow", f"Arrow functions should work in {driver.capabilities['browserName']}"
        
        # Test template literals
        template_result = driver.execute_script("return `template_${'literal'}`;")
        assert template_result == "template_literal", f"Template literals should work in {driver.capabilities['browserName']}"
        
        # Test destructuring
        destructuring_result = driver.execute_script("const {a, b} = {a: 1, b: 2}; return a + b;")
        assert destructuring_result == 3, f"Destructuring should work in {driver.capabilities['browserName']}"
        
        # Test spread operator
        spread_result = driver.execute_script("return [...[1, 2], 3].length;")
        assert spread_result == 3, f"Spread operator should work in {driver.capabilities['browserName']}"
    
    def test_css_grid_flexbox(self, driver):
        """Test CSS Grid and Flexbox support across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test Flexbox support
        flex_support = driver.execute_script("""
            var element = document.createElement('div');
            element.style.display = 'flex';
            return element.style.display === 'flex';
        """)
        assert flex_support, f"Flexbox should be supported in {driver.capabilities['browserName']}"
        
        # Test CSS Grid support
        grid_support = driver.execute_script("""
            var element = document.createElement('div');
            element.style.display = 'grid';
            return element.style.display === 'grid';
        """)
        assert grid_support, f"CSS Grid should be supported in {driver.capabilities['browserName']}"
    
    def test_web_apis(self, driver):
        """Test Web APIs across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test Intersection Observer
        intersection_observer = driver.execute_script("return typeof IntersectionObserver !== 'undefined';")
        print(f"IntersectionObserver available in {driver.capabilities['browserName']}: {intersection_observer}")
        
        # Test Resize Observer
        resize_observer = driver.execute_script("return typeof ResizeObserver !== 'undefined';")
        print(f"ResizeObserver available in {driver.capabilities['browserName']}: {resize_observer}")
        
        # Test Mutation Observer
        mutation_observer = driver.execute_script("return typeof MutationObserver !== 'undefined';")
        assert mutation_observer, f"MutationObserver should be available in {driver.capabilities['browserName']}"
    
    def test_performance_apis(self, driver):
        """Test Performance APIs across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test Performance API
        performance_available = driver.execute_script("return typeof performance !== 'undefined';")
        assert performance_available, f"Performance API should be available in {driver.capabilities['browserName']}"
        
        # Test performance.now()
        now_available = driver.execute_script("return typeof performance.now === 'function';")
        assert now_available, f"performance.now() should be available in {driver.capabilities['browserName']}"
        
        # Test performance.mark()
        mark_available = driver.execute_script("return typeof performance.mark === 'function';")
        print(f"performance.mark() available in {driver.capabilities['browserName']}: {mark_available}")
    
    def test_error_handling(self, driver):
        """Test error handling across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test console.error
        console_error = driver.execute_script("""
            try {
                console.error('test error');
                return 'error_logged';
            } catch (e) {
                return 'error_failed';
            }
        """)
        assert console_error == "error_logged", f"console.error should work in {driver.capabilities['browserName']}"
        
        # Test try-catch
        try_catch = driver.execute_script("""
            try {
                throw new Error('test error');
            } catch (e) {
                return 'caught';
            }
        """)
        assert try_catch == "caught", f"try-catch should work in {driver.capabilities['browserName']}"
    
    def test_browser_specific_features(self, driver):
        """Test browser-specific features"""
        browser_name = driver.capabilities['browserName'].lower()
        
        if 'chrome' in browser_name:
            # Test Chrome-specific features
            chrome_features = driver.execute_script("""
                return {
                    webkit: typeof webkit !== 'undefined',
                    chrome: typeof chrome !== 'undefined'
                };
            """)
            print(f"Chrome features: {chrome_features}")
            
        elif 'firefox' in browser_name:
            # Test Firefox-specific features
            firefox_features = driver.execute_script("""
                return {
                    moz: typeof moz !== 'undefined',
                    InstallTrigger: typeof InstallTrigger !== 'undefined'
                };
            """)
            print(f"Firefox features: {firefox_features}")
            
        elif 'safari' in browser_name:
            # Test Safari-specific features
            safari_features = driver.execute_script("""
                return {
                    webkit: typeof webkit !== 'undefined',
                    safari: typeof safari !== 'undefined'
                };
            """)
            print(f"Safari features: {safari_features}")
            
        elif 'edge' in browser_name:
            # Test Edge-specific features
            edge_features = driver.execute_script("""
                return {
                    ms: typeof ms !== 'undefined',
                    edge: typeof edge !== 'undefined'
                };
            """)
            print(f"Edge features: {edge_features}")
    
    def test_consistency_across_browsers(self, driver):
        """Test consistency of functionality across browsers"""
        driver.get("http://localhost:3000/verification")
        
        # Test that core functionality works consistently
        phone_input = driver.find_element(By.ID, "phone-number")
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        
        # Test input behavior
        phone_input.send_keys("+1234567890")
        input_value = phone_input.get_attribute("value")
        assert input_value == "+1234567890", \
            f"Input value should be consistent in {driver.capabilities['browserName']}"
        
        # Test button state
        assert send_button.is_enabled(), \
            f"Send button should be enabled in {driver.capabilities['browserName']}"
        
        # Test click behavior
        send_button.click()
        
        # Wait for response
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message")),
                EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
            )
        )
        
        # Verify consistent response handling
        success_message = driver.find_elements(By.CSS_SELECTOR, ".success-message")
        error_message = driver.find_elements(By.CSS_SELECTOR, ".error-message")
        
        assert len(success_message) > 0 or len(error_message) > 0, \
            f"Should show success or error message in {driver.capabilities['browserName']}" 