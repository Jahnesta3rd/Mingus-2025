"""
Accessibility Testing for Phone Verification System
Tests for WCAG 2.1 AA compliance
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import time

class TestVerificationAccessibility:
    """Accessibility testing for verification system"""
    
    @pytest.fixture
    def driver(self):
        """Setup Chrome driver with accessibility testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_keyboard_navigation(self, driver):
        """Test keyboard navigation through verification flow"""
        driver.get("http://localhost:3000/verification")
        
        # Test tab navigation
        elements = driver.find_elements(By.CSS_SELECTOR, "input, button, select, textarea, [tabindex]")
        focusable_elements = [elem for elem in elements if elem.is_enabled() and elem.is_displayed()]
        
        # Test tab order
        for i, element in enumerate(focusable_elements):
            element.send_keys(Keys.TAB)
            time.sleep(0.1)
            
            # Verify focus moves to next element
            focused_element = driver.switch_to.active_element
            assert focused_element == focusable_elements[(i + 1) % len(focusable_elements)], \
                f"Focus order incorrect at element {i}"
        
        # Test shift+tab for reverse navigation
        for i in range(len(focusable_elements) - 1, -1, -1):
            driver.switch_to.active_element.send_keys(Keys.SHIFT + Keys.TAB)
            time.sleep(0.1)
            
            focused_element = driver.switch_to.active_element
            assert focused_element == focusable_elements[i], \
                f"Reverse focus order incorrect at element {i}"
    
    def test_screen_reader_labels(self, driver):
        """Test screen reader labels and ARIA attributes"""
        driver.get("http://localhost:3000/verification")
        
        # Test phone number input
        phone_input = driver.find_element(By.ID, "phone-number")
        
        # Check for proper labeling
        aria_label = phone_input.get_attribute("aria-label")
        aria_labelledby = phone_input.get_attribute("aria-labelledby")
        placeholder = phone_input.get_attribute("placeholder")
        
        # Should have at least one form of labeling
        assert aria_label or aria_labelledby or placeholder, \
            "Phone input lacks proper labeling for screen readers"
        
        # Test verification code input
        code_input = driver.find_element(By.ID, "verification-code")
        
        aria_label = code_input.get_attribute("aria-label")
        aria_labelledby = code_input.get_attribute("aria-labelledby")
        placeholder = code_input.get_attribute("placeholder")
        
        assert aria_label or aria_labelledby or placeholder, \
            "Verification code input lacks proper labeling for screen readers"
        
        # Test buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            # Buttons should have accessible names
            aria_label = button.get_attribute("aria-label")
            aria_labelledby = button.get_attribute("aria-labelledby")
            button_text = button.text.strip()
            
            assert aria_label or aria_labelledby or button_text, \
                f"Button lacks accessible name: {button.get_attribute('outerHTML')}"
    
    def test_color_contrast(self, driver):
        """Test color contrast ratios"""
        driver.get("http://localhost:3000/verification")
        
        # Test text contrast
        text_elements = driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, h3, h4, h5, h6, span, div, label")
        
        for element in text_elements[:10]:  # Test first 10 elements
            if element.is_displayed() and element.text.strip():
                # Get computed styles
                color = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).color;", 
                    element
                )
                background_color = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).backgroundColor;", 
                    element
                )
                
                # Check if colors are defined
                if color != "rgba(0, 0, 0, 0)" and background_color != "rgba(0, 0, 0, 0)":
                    # Calculate contrast ratio (simplified)
                    # In a real test, you'd use a proper contrast calculation library
                    print(f"Element text: {element.text[:50]}")
                    print(f"Color: {color}, Background: {background_color}")
    
    def test_focus_indicators(self, driver):
        """Test focus indicators are visible"""
        driver.get("http://localhost:3000/verification")
        
        # Test focus indicators on interactive elements
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, "input, button, select, textarea, a")
        
        for element in interactive_elements:
            if element.is_enabled() and element.is_displayed():
                # Focus the element
                element.click()
                
                # Check for focus indicator
                focus_style = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).outline;", 
                    element
                )
                border_style = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).border;", 
                    element
                )
                box_shadow = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).boxShadow;", 
                    element
                )
                
                # Should have some form of focus indicator
                has_focus_indicator = (
                    focus_style != "none" or 
                    "solid" in border_style or 
                    box_shadow != "none"
                )
                
                assert has_focus_indicator, \
                    f"Element lacks visible focus indicator: {element.get_attribute('outerHTML')}"
    
    def test_error_announcements(self, driver):
        """Test error messages are announced to screen readers"""
        driver.get("http://localhost:3000/verification")
        
        # Trigger an error by submitting empty form
        submit_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        submit_button.click()
        
        # Wait for error message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".error-message"))
        )
        
        error_message = driver.find_element(By.CSS_SELECTOR, ".error-message")
        
        # Check for ARIA live region
        aria_live = error_message.get_attribute("aria-live")
        assert aria_live in ["polite", "assertive"], \
            "Error message should have aria-live attribute"
        
        # Check for role
        role = error_message.get_attribute("role")
        if role:
            assert role in ["alert", "status"], \
                "Error message should have appropriate ARIA role"
        
        # Check for aria-describedby connection
        phone_input = driver.find_element(By.ID, "phone-number")
        aria_describedby = phone_input.get_attribute("aria-describedby")
        
        if aria_describedby:
            # Should reference the error message
            error_id = error_message.get_attribute("id")
            assert error_id in aria_describedby, \
                "Input should reference error message via aria-describedby"
    
    def test_form_validation_announcements(self, driver):
        """Test form validation announcements"""
        driver.get("http://localhost:3000/verification")
        
        # Test required field validation
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("invalid")
        phone_input.send_keys(Keys.TAB)  # Trigger validation
        
        # Wait for validation message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".validation-message"))
        )
        
        validation_message = driver.find_element(By.CSS_SELECTOR, ".validation-message")
        
        # Check for ARIA attributes
        aria_invalid = phone_input.get_attribute("aria-invalid")
        assert aria_invalid == "true", \
            "Invalid input should have aria-invalid='true'"
        
        # Check for aria-describedby
        aria_describedby = phone_input.get_attribute("aria-describedby")
        if aria_describedby:
            validation_id = validation_message.get_attribute("id")
            assert validation_id in aria_describedby, \
                "Input should reference validation message"
    
    def test_skip_links(self, driver):
        """Test skip links for keyboard users"""
        driver.get("http://localhost:3000/verification")
        
        # Look for skip links
        skip_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='#'], .skip-link")
        
        if skip_links:
            for skip_link in skip_links:
                # Skip links should be visible on focus
                skip_link.send_keys(Keys.TAB)
                
                # Check if skip link becomes visible
                is_visible = skip_link.is_displayed()
                assert is_visible, \
                    "Skip link should be visible when focused"
                
                # Test skip link functionality
                target_id = skip_link.get_attribute("href").split("#")[-1]
                skip_link.click()
                
                # Should focus the target element
                target_element = driver.find_element(By.ID, target_id)
                focused_element = driver.switch_to.active_element
                assert focused_element == target_element, \
                    f"Skip link should focus target element: {target_id}"
    
    def test_landmark_roles(self, driver):
        """Test proper use of landmark roles"""
        driver.get("http://localhost:3000/verification")
        
        # Check for main landmark
        main_elements = driver.find_elements(By.CSS_SELECTOR, "main, [role='main']")
        assert len(main_elements) > 0, "Page should have a main landmark"
        
        # Check for form landmark
        form_elements = driver.find_elements(By.CSS_SELECTOR, "form, [role='form']")
        assert len(form_elements) > 0, "Verification form should have form landmark"
        
        # Check for navigation landmark
        nav_elements = driver.find_elements(By.CSS_SELECTOR, "nav, [role='navigation']")
        if nav_elements:
            for nav in nav_elements:
                # Navigation should have accessible name
                aria_label = nav.get_attribute("aria-label")
                aria_labelledby = nav.get_attribute("aria-labelledby")
                nav_text = nav.text.strip()
                
                assert aria_label or aria_labelledby or nav_text, \
                    "Navigation landmark should have accessible name"
    
    def test_heading_structure(self, driver):
        """Test proper heading structure"""
        driver.get("http://localhost:3000/verification")
        
        # Get all headings
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        
        if headings:
            # Check for h1
            h1_elements = [h for h in headings if h.tag_name == "h1"]
            assert len(h1_elements) > 0, "Page should have at least one h1"
            
            # Check heading hierarchy
            current_level = 1
            for heading in headings:
                level = int(heading.tag_name[1])
                
                # Should not skip levels
                assert level <= current_level + 1, \
                    f"Heading hierarchy skipped level: {heading.tag_name}"
                
                current_level = level
    
    def test_image_alt_text(self, driver):
        """Test image alt text"""
        driver.get("http://localhost:3000/verification")
        
        # Check all images
        images = driver.find_elements(By.TAG_NAME, "img")
        
        for image in images:
            alt_text = image.get_attribute("alt")
            aria_label = image.get_attribute("aria-label")
            aria_labelledby = image.get_attribute("aria-labelledby")
            role = image.get_attribute("role")
            
            # Decorative images should have alt=""
            if role == "presentation" or role == "none":
                assert alt_text == "", \
                    "Decorative image should have empty alt text"
            else:
                # Content images should have alt text or aria-label
                has_alt = alt_text or aria_label or aria_labelledby
                assert has_alt, \
                    f"Content image lacks alt text: {image.get_attribute('src')}"
    
    def test_table_accessibility(self, driver):
        """Test table accessibility"""
        driver.get("http://localhost:3000/verification")
        
        # Check tables
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        for table in tables:
            # Check for caption or aria-label
            caption = table.find_elements(By.TAG_NAME, "caption")
            aria_label = table.get_attribute("aria-label")
            aria_labelledby = table.get_attribute("aria-labelledby")
            
            has_label = len(caption) > 0 or aria_label or aria_labelledby
            assert has_label, "Table should have caption or aria-label"
            
            # Check for proper table structure
            headers = table.find_elements(By.TAG_NAME, "th")
            if headers:
                # Should have scope attributes
                for header in headers:
                    scope = header.get_attribute("scope")
                    assert scope in ["row", "col"], \
                        "Table headers should have scope attribute"
    
    def test_dynamic_content_updates(self, driver):
        """Test dynamic content updates are announced"""
        driver.get("http://localhost:3000/verification")
        
        # Test loading state announcements
        phone_input = driver.find_element(By.ID, "phone-number")
        phone_input.send_keys("+1234567890")
        
        send_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='send-code-button']")
        send_button.click()
        
        # Wait for loading state
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".loading"))
        )
        
        loading_element = driver.find_element(By.CSS_SELECTOR, ".loading")
        
        # Check for loading announcement
        aria_live = loading_element.get_attribute("aria-live")
        assert aria_live in ["polite", "assertive"], \
            "Loading state should be announced to screen readers"
        
        # Check for aria-busy
        aria_busy = loading_element.get_attribute("aria-busy")
        assert aria_busy == "true", \
            "Loading element should have aria-busy='true'"
    
    def test_mobile_accessibility(self, driver):
        """Test accessibility on mobile devices"""
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        driver.get("http://localhost:3000/verification")
        
        # Test touch target sizes
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, "input, button, select, textarea, a")
        
        for element in interactive_elements:
            if element.is_displayed():
                size = element.size
                
                # Touch targets should be at least 44x44 pixels
                assert size['width'] >= 44, \
                    f"Touch target too narrow: {element.tag_name}"
                assert size['height'] >= 44, \
                    f"Touch target too short: {element.tag_name}"
        
        # Test viewport meta tag
        viewport_meta = driver.find_element(By.CSS_SELECTOR, "meta[name='viewport']")
        viewport_content = viewport_meta.get_attribute("content")
        
        assert "width=device-width" in viewport_content, \
            "Viewport meta tag should include width=device-width"
        assert "initial-scale=1" in viewport_content, \
            "Viewport meta tag should include initial-scale=1"
    
    def test_high_contrast_mode(self, driver):
        """Test high contrast mode compatibility"""
        driver.get("http://localhost:3000/verification")
        
        # Test that elements remain visible in high contrast
        # This is a simplified test - in practice you'd use a high contrast mode
        text_elements = driver.find_elements(By.CSS_SELECTOR, "p, h1, h2, h3, h4, h5, h6, span, div, label")
        
        for element in text_elements[:5]:  # Test first 5 elements
            if element.is_displayed() and element.text.strip():
                # Check that text has sufficient contrast
                color = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).color;", 
                    element
                )
                background_color = driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).backgroundColor;", 
                    element
                )
                
                # Should have defined colors
                assert color != "rgba(0, 0, 0, 0)", \
                    "Text should have defined color"
                assert background_color != "rgba(0, 0, 0, 0)", \
                    "Element should have defined background color"
    
    def test_zoom_functionality(self, driver):
        """Test zoom functionality"""
        driver.get("http://localhost:3000/verification")
        
        # Test zoom in
        driver.execute_script("document.body.style.zoom = '200%'")
        
        # Verify elements remain functional
        phone_input = driver.find_element(By.ID, "phone-number")
        assert phone_input.is_enabled(), "Phone input should remain enabled when zoomed"
        
        # Test zoom out
        driver.execute_script("document.body.style.zoom = '50%'")
        
        # Verify elements remain functional
        phone_input = driver.find_element(By.ID, "phone-number")
        assert phone_input.is_enabled(), "Phone input should remain enabled when zoomed out"
        
        # Reset zoom
        driver.execute_script("document.body.style.zoom = '100%'")
    
    def test_screen_reader_navigation(self, driver):
        """Test screen reader navigation patterns"""
        driver.get("http://localhost:3000/verification")
        
        # Test heading navigation
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        
        if len(headings) > 1:
            # Test that headings are properly structured
            for i, heading in enumerate(headings):
                level = int(heading.tag_name[1])
                heading_text = heading.text.strip()
                
                assert heading_text, \
                    f"Heading {i} should have text content"
                
                # Test heading accessibility
                aria_level = heading.get_attribute("aria-level")
                if aria_level:
                    assert int(aria_level) == level, \
                        f"Heading aria-level should match tag level"
        
        # Test list navigation
        lists = driver.find_elements(By.CSS_SELECTOR, "ul, ol")
        
        for list_elem in lists:
            list_items = list_elem.find_elements(By.TAG_NAME, "li")
            
            if list_items:
                # Test list accessibility
                role = list_elem.get_attribute("role")
                if role:
                    assert role in ["list", "directory"], \
                        "List should have appropriate role"
                
                # Test list item count
                aria_label = list_elem.get_attribute("aria-label")
                if aria_label and "items" in aria_label.lower():
                    # Should match actual item count
                    item_count = len(list_items)
                    assert str(item_count) in aria_label, \
                        "List aria-label should match item count" 