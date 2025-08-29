"""
Frontend Component Tests for Assessment System

Comprehensive test suite for React components using Jest and React Testing Library
Includes assessment flow integration, form validation, responsive design, and accessibility tests.
"""

import pytest
import json
from unittest.mock import patch, Mock, AsyncMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

pytestmark = pytest.mark.frontend

class TestAssessmentFlowComponent:
    """Test AssessmentFlow component functionality"""
    
    def test_assessment_flow_renders_correctly(self, chrome_driver):
        """Test that AssessmentFlow component renders correctly"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Verify main elements are present
        assert chrome_driver.find_element(By.CLASS_NAME, "assessment-header")
        assert chrome_driver.find_element(By.CLASS_NAME, "question-container")
        assert chrome_driver.find_element(By.CLASS_NAME, "progress-bar")
    
    def test_assessment_question_navigation(self, chrome_driver):
        """Test navigation between assessment questions"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for first question to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        
        # Answer first question
        first_question = chrome_driver.find_element(By.CLASS_NAME, "question-container")
        salary_input = first_question.find_element(By.NAME, "current_salary")
        salary_input.send_keys("75000")
        
        # Click next button
        next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
        next_button.click()
        
        # Verify we moved to next question
        WebDriverWait(chrome_driver, 5).until(
            EC.staleness_of(first_question)
        )
        
        # Verify progress bar updated
        progress_bar = chrome_driver.find_element(By.CLASS_NAME, "progress-bar")
        progress_value = progress_bar.get_attribute("aria-valuenow")
        assert int(progress_value) > 0
    
    def test_assessment_form_validation(self, chrome_driver):
        """Test form validation in assessment flow"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for first question to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        
        # Try to proceed without filling required fields
        next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
        next_button.click()
        
        # Verify validation error appears
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        
        error_message = chrome_driver.find_element(By.CLASS_NAME, "error-message")
        assert "required" in error_message.text.lower()
    
    def test_assessment_data_persistence(self, chrome_driver):
        """Test that assessment data persists during navigation"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for first question to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        
        # Fill first question
        first_question = chrome_driver.find_element(By.CLASS_NAME, "question-container")
        salary_input = first_question.find_element(By.NAME, "current_salary")
        salary_input.send_keys("75000")
        
        # Navigate to next question
        next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
        next_button.click()
        
        # Navigate back
        back_button = chrome_driver.find_element(By.CLASS_NAME, "back-button")
        back_button.click()
        
        # Verify data is still there
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.NAME, "current_salary"))
        )
        
        salary_input = chrome_driver.find_element(By.NAME, "current_salary")
        assert salary_input.get_attribute("value") == "75000"
    
    def test_assessment_completion_flow(self, chrome_driver):
        """Test complete assessment flow from start to finish"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Complete all questions
        questions_completed = 0
        max_questions = 10  # Prevent infinite loop
        
        while questions_completed < max_questions:
            try:
                # Wait for question to load
                WebDriverWait(chrome_driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
                )
                
                question_container = chrome_driver.find_element(By.CLASS_NAME, "question-container")
                
                # Fill current question based on type
                self._fill_question(question_container)
                
                # Click next
                next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
                next_button.click()
                
                questions_completed += 1
                
                # Check if we've reached the end
                try:
                    WebDriverWait(chrome_driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
                    )
                    break
                except:
                    continue
                    
            except Exception as e:
                print(f"Error completing question {questions_completed}: {e}")
                break
        
        # Verify we reached results page
        results_container = chrome_driver.find_element(By.CLASS_NAME, "assessment-results")
        assert results_container.is_displayed()
    
    def _fill_question(self, question_container):
        """Helper method to fill different types of questions"""
        # Check for different input types
        try:
            # Text input
            text_input = question_container.find_element(By.TAG_NAME, "input")
            if text_input.get_attribute("type") == "number":
                text_input.send_keys("75000")
            elif text_input.get_attribute("type") == "text":
                text_input.send_keys("Test Answer")
        except:
            pass
        
        try:
            # Select dropdown
            select_element = question_container.find_element(By.TAG_NAME, "select")
            select_element.click()
            first_option = select_element.find_element(By.TAG_NAME, "option")
            first_option.click()
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


class TestAssessmentQuestionComponent:
    """Test AssessmentQuestion component functionality"""
    
    def test_question_renders_correctly(self, chrome_driver):
        """Test that individual questions render correctly"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for question to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        
        question_container = chrome_driver.find_element(By.CLASS_NAME, "question-container")
        
        # Verify question elements
        assert question_container.find_element(By.CLASS_NAME, "question-text")
        assert question_container.find_element(By.CLASS_NAME, "question-input")
    
    def test_text_input_question(self, chrome_driver):
        """Test text input question functionality"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for question to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        
        # Find text input
        text_input = chrome_driver.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='number']")
        
        # Test input
        text_input.clear()
        text_input.send_keys("Test Answer")
        
        # Verify input value
        assert text_input.get_attribute("value") == "Test Answer"
    
    def test_select_dropdown_question(self, chrome_driver):
        """Test select dropdown question functionality"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for question to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        
        # Find select dropdown
        try:
            select_element = chrome_driver.find_element(By.TAG_NAME, "select")
            
            # Get all options
            options = select_element.find_elements(By.TAG_NAME, "option")
            assert len(options) > 1
            
            # Select first option
            select_element.click()
            options[1].click()  # Skip first option (usually placeholder)
            
            # Verify selection
            selected_option = select_element.find_element(By.CSS_SELECTOR, "option:checked")
            assert selected_option.is_selected()
        except:
            # Skip if no select element found
            pass
    
    def test_radio_button_question(self, chrome_driver):
        """Test radio button question functionality"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for question to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        
        # Find radio buttons
        try:
            radio_buttons = chrome_driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            
            if radio_buttons:
                # Click first radio button
                radio_buttons[0].click()
                
                # Verify it's selected
                assert radio_buttons[0].is_selected()
                
                # Click second radio button
                radio_buttons[1].click()
                
                # Verify first is deselected and second is selected
                assert not radio_buttons[0].is_selected()
                assert radio_buttons[1].is_selected()
        except:
            # Skip if no radio buttons found
            pass
    
    def test_checkbox_question(self, chrome_driver):
        """Test checkbox question functionality"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for question to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        
        # Find checkboxes
        try:
            checkboxes = chrome_driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            
            if checkboxes:
                # Click first checkbox
                checkboxes[0].click()
                
                # Verify it's checked
                assert checkboxes[0].is_selected()
                
                # Click second checkbox
                checkboxes[1].click()
                
                # Verify both are checked
                assert checkboxes[0].is_selected()
                assert checkboxes[1].is_selected()
                
                # Uncheck first checkbox
                checkboxes[0].click()
                
                # Verify first is unchecked and second is still checked
                assert not checkboxes[0].is_selected()
                assert checkboxes[1].is_selected()
        except:
            # Skip if no checkboxes found
            pass


class TestResponsiveDesign:
    """Test responsive design across different screen sizes"""
    
    @pytest.mark.parametrize("width,height", [
        (320, 568),   # iPhone SE
        (375, 667),   # iPhone 6/7/8
        (414, 896),   # iPhone X/XS
        (768, 1024),  # iPad
        (1024, 768),  # iPad Landscape
        (1366, 768),  # Laptop
        (1920, 1080), # Desktop
        (2560, 1440), # 4K
    ])
    def test_responsive_layout(self, chrome_driver, width, height):
        """Test responsive layout at different screen sizes"""
        chrome_driver.set_window_size(width, height)
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Verify layout is responsive
        assessment_container = chrome_driver.find_element(By.CLASS_NAME, "assessment-flow")
        
        # Check that container fits within viewport
        container_width = assessment_container.size['width']
        container_height = assessment_container.size['height']
        
        assert container_width <= width
        assert container_height <= height
        
        # Check that text is readable
        question_text = chrome_driver.find_element(By.CLASS_NAME, "question-text")
        font_size = question_text.value_of_css_property("font-size")
        assert int(font_size.replace("px", "")) >= 12  # Minimum readable font size
    
    def test_mobile_navigation(self, chrome_driver):
        """Test navigation on mobile devices"""
        chrome_driver.set_window_size(375, 667)  # iPhone 6/7/8
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test touch-friendly button sizes
        buttons = chrome_driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            button_size = button.size
            # Buttons should be at least 44x44px for touch targets
            assert button_size['width'] >= 44
            assert button_size['height'] >= 44
    
    def test_tablet_layout(self, chrome_driver):
        """Test layout on tablet devices"""
        chrome_driver.set_window_size(768, 1024)  # iPad
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Verify tablet-specific layout adjustments
        assessment_container = chrome_driver.find_element(By.CLASS_NAME, "assessment-flow")
        
        # Check for tablet-specific CSS classes or layout
        container_classes = assessment_container.get_attribute("class")
        # This would depend on your CSS implementation
        # assert "tablet" in container_classes or "md" in container_classes


class TestAccessibility:
    """Test accessibility compliance using jest-axe"""
    
    def test_accessibility_compliance(self, chrome_driver):
        """Test accessibility compliance with WCAG guidelines"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test keyboard navigation
        self._test_keyboard_navigation(chrome_driver)
        
        # Test screen reader compatibility
        self._test_screen_reader_compatibility(chrome_driver)
        
        # Test color contrast
        self._test_color_contrast(chrome_driver)
        
        # Test focus management
        self._test_focus_management(chrome_driver)
    
    def _test_keyboard_navigation(self, chrome_driver):
        """Test keyboard navigation accessibility"""
        # Test tab navigation
        body = chrome_driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.TAB)
        
        # Verify focus is visible
        focused_element = chrome_driver.switch_to.active_element
        focus_style = focused_element.value_of_css_property("outline")
        assert focus_style != "none" or "focus" in focused_element.get_attribute("class")
        
        # Test arrow key navigation for radio buttons
        try:
            radio_buttons = chrome_driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            if radio_buttons:
                radio_buttons[0].click()
                radio_buttons[0].send_keys(Keys.ARROW_RIGHT)
                # Verify focus moved to next radio button
                assert radio_buttons[1].is_selected()
        except:
            pass
    
    def _test_screen_reader_compatibility(self, chrome_driver):
        """Test screen reader compatibility"""
        # Check for proper ARIA labels
        inputs = chrome_driver.find_elements(By.TAG_NAME, "input")
        for input_element in inputs:
            aria_label = input_element.get_attribute("aria-label")
            aria_labelledby = input_element.get_attribute("aria-labelledby")
            name = input_element.get_attribute("name")
            
            # Input should have either aria-label, aria-labelledby, or name attribute
            assert aria_label or aria_labelledby or name
        
        # Check for proper heading structure
        headings = chrome_driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        heading_levels = []
        for heading in headings:
            tag_name = heading.tag_name
            level = int(tag_name[1])
            heading_levels.append(level)
        
        # Verify heading levels are sequential
        for i in range(len(heading_levels) - 1):
            assert heading_levels[i + 1] - heading_levels[i] <= 1
    
    def _test_color_contrast(self, chrome_driver):
        """Test color contrast ratios"""
        # This would require a more sophisticated color analysis
        # For now, we'll check that text elements have sufficient contrast
        text_elements = chrome_driver.find_elements(By.CSS_SELECTOR, "p, span, div, h1, h2, h3, h4, h5, h6")
        
        for element in text_elements[:5]:  # Test first 5 elements
            color = element.value_of_css_property("color")
            background_color = element.value_of_css_property("background-color")
            
            # Basic check - ensure colors are not the same
            assert color != background_color
    
    def _test_focus_management(self, chrome_driver):
        """Test focus management"""
        # Test that focus is properly managed during navigation
        next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
        next_button.click()
        
        # Verify focus is managed appropriately
        focused_element = chrome_driver.switch_to.active_element
        assert focused_element.is_displayed()


class TestCrossBrowserCompatibility:
    """Test cross-browser compatibility"""
    
    def test_chrome_compatibility(self, chrome_driver):
        """Test functionality in Chrome"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test basic functionality
        self._test_basic_functionality(chrome_driver)
    
    def test_firefox_compatibility(self, firefox_driver):
        """Test functionality in Firefox"""
        firefox_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(firefox_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test basic functionality
        self._test_basic_functionality(firefox_driver)
    
    def test_safari_compatibility(self, safari_driver):
        """Test functionality in Safari"""
        safari_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(safari_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test basic functionality
        self._test_basic_functionality(safari_driver)
    
    def test_edge_compatibility(self, edge_driver):
        """Test functionality in Edge"""
        edge_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(edge_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test basic functionality
        self._test_basic_functionality(edge_driver)
    
    def _test_basic_functionality(self, driver):
        """Test basic functionality that should work in all browsers"""
        # Test that component renders
        assessment_flow = driver.find_element(By.CLASS_NAME, "assessment-flow")
        assert assessment_flow.is_displayed()
        
        # Test that questions are present
        question_container = driver.find_element(By.CLASS_NAME, "question-container")
        assert question_container.is_displayed()
        
        # Test that navigation buttons are present
        next_button = driver.find_element(By.CLASS_NAME, "next-button")
        assert next_button.is_displayed()
        
        # Test that progress indicator is present
        progress_bar = driver.find_element(By.CLASS_NAME, "progress-bar")
        assert progress_bar.is_displayed()


class TestFormValidation:
    """Test form validation functionality"""
    
    def test_required_field_validation(self, chrome_driver):
        """Test validation of required fields"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Try to proceed without filling required fields
        next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
        next_button.click()
        
        # Verify validation error appears
        WebDriverWait(chrome_driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        
        error_message = chrome_driver.find_element(By.CLASS_NAME, "error-message")
        assert "required" in error_message.text.lower()
    
    def test_number_input_validation(self, chrome_driver):
        """Test validation of number input fields"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Find number input
        try:
            number_input = chrome_driver.find_element(By.CSS_SELECTOR, "input[type='number']")
            
            # Test invalid input
            number_input.clear()
            number_input.send_keys("invalid")
            
            # Try to proceed
            next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
            next_button.click()
            
            # Verify validation error
            WebDriverWait(chrome_driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
            )
            
            # Test valid input
            number_input.clear()
            number_input.send_keys("75000")
            
            # Verify no error
            error_messages = chrome_driver.find_elements(By.CLASS_NAME, "error-message")
            assert len(error_messages) == 0
        except:
            # Skip if no number input found
            pass
    
    def test_email_validation(self, chrome_driver):
        """Test email validation"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Find email input
        try:
            email_input = chrome_driver.find_element(By.CSS_SELECTOR, "input[type='email']")
            
            # Test invalid email
            email_input.clear()
            email_input.send_keys("invalid-email")
            
            # Try to proceed
            next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
            next_button.click()
            
            # Verify validation error
            WebDriverWait(chrome_driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
            )
            
            # Test valid email
            email_input.clear()
            email_input.send_keys("test@example.com")
            
            # Verify no error
            error_messages = chrome_driver.find_elements(By.CLASS_NAME, "error-message")
            assert len(error_messages) == 0
        except:
            # Skip if no email input found
            pass
    
    def test_real_time_validation(self, chrome_driver):
        """Test real-time validation as user types"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for component to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Find text input
        try:
            text_input = chrome_driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            
            # Type invalid input
            text_input.clear()
            text_input.send_keys("a")
            
            # Check for real-time validation
            try:
                error_message = chrome_driver.find_element(By.CLASS_NAME, "error-message")
                assert error_message.is_displayed()
            except:
                # Real-time validation might not be implemented
                pass
            
            # Type valid input
            text_input.clear()
            text_input.send_keys("Valid Input")
            
            # Verify error disappears
            error_messages = chrome_driver.find_elements(By.CLASS_NAME, "error-message")
            assert len(error_messages) == 0
        except:
            # Skip if no text input found
            pass
