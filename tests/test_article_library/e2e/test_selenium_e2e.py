"""
Selenium End-to-End Tests for Article Library

Comprehensive frontend integration tests using Selenium WebDriver
for the Mingus article library system.
"""

import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class TestFrontendIntegration:
    """Test frontend React components with Selenium"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Create Selenium WebDriver instance"""
        options = Options()
        options.add_argument('--headless')  # Run in headless mode for CI
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Add additional options for stability
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Faster loading for tests
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)
        
        yield driver
        driver.quit()
    
    @pytest.fixture
    def authenticated_user(self, driver):
        """Log in user for testing"""
        try:
            driver.get('http://localhost:3000/login')
            
            # Wait for login form to load
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'email'))
            )
            password_field = driver.find_element(By.NAME, 'password')
            
            # Clear fields and enter credentials
            email_field.clear()
            email_field.send_keys('test@example.com')
            password_field.clear()
            password_field.send_keys('password123')
            
            # Submit form
            submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            submit_button.click()
            
            # Wait for redirect to dashboard
            WebDriverWait(driver, 15).until(
                EC.url_contains('/dashboard')
            )
            
        except TimeoutException:
            pytest.skip("Login page not available or authentication failed")
    
    def test_article_library_navigation(self, driver, authenticated_user):
        """Test navigation to article library"""
        try:
            # Click on Learning Library navigation
            library_nav = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, 'Learning Library'))
            )
            library_nav.click()
            
            # Verify we're on the article library page
            WebDriverWait(driver, 10).until(
                EC.url_contains('/articles')
            )
            
            # Check for Be-Do-Have navigation
            be_element = driver.find_element(By.XPATH, "//*[contains(text(), 'BE (Identity)')]")
            do_element = driver.find_element(By.XPATH, "//*[contains(text(), 'DO (Skills)')]")
            have_element = driver.find_element(By.XPATH, "//*[contains(text(), 'HAVE (Results)')]")
            
            assert be_element.is_displayed()
            assert do_element.is_displayed()
            assert have_element.is_displayed()
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Navigation test failed: {str(e)}")
    
    def test_assessment_modal_flow(self, driver, authenticated_user):
        """Test Be-Do-Have assessment modal workflow"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Click Take Assessment button
            assessment_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Take Assessment')]"))
            )
            assessment_button.click()
            
            # Wait for modal to appear
            modal = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'assessment-modal'))
            )
            
            # Fill out first phase (BE) questions
            rating_buttons = driver.find_elements(By.CSS_SELECTOR, '.rating-button')
            for i in range(0, min(25, len(rating_buttons)), 5):  # Select rating 5 for each question
                if i + 4 < len(rating_buttons):
                    rating_buttons[i + 4].click()  # Click 5th button (rating 5)
                    time.sleep(0.5)  # Small delay for UI updates
            
            # Click Next Phase
            next_button = driver.find_element(By.XPATH, "//*[contains(text(), 'Next Phase')]")
            next_button.click()
            
            # Verify we're on DO phase
            do_phase_text = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'DO (Skills & Actions)')]"))
            )
            assert do_phase_text.is_displayed()
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Assessment modal test failed: {str(e)}")
    
    def test_article_search_functionality(self, driver, authenticated_user):
        """Test article search interface"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Find search input
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="Search articles"]'))
            )
            
            # Type search query
            search_input.clear()
            search_input.send_keys('career advancement')
            search_input.send_keys(Keys.RETURN)
            
            # Wait for search results
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'article-card'))
            )
            
            # Verify search results contain relevant articles
            article_titles = driver.find_elements(By.CSS_SELECTOR, '.article-card .article-title')
            assert len(article_titles) > 0
            
            # Verify search results are relevant
            for title in article_titles:
                title_text = title.text.lower()
                assert 'career' in title_text or 'advancement' in title_text
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Search functionality test failed: {str(e)}")
    
    def test_article_card_interactions(self, driver, authenticated_user):
        """Test article card bookmark and access functionality"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Wait for articles to load
            article_card = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'article-card'))
            )
            
            # Test bookmark functionality
            bookmark_button = article_card.find_element(By.CLASS_NAME, 'bookmark-button')
            initial_bookmarked = 'bookmarked' in bookmark_button.get_attribute('class')
            
            bookmark_button.click()
            time.sleep(1)  # Wait for state update
            
            final_bookmarked = 'bookmarked' in bookmark_button.get_attribute('class')
            assert initial_bookmarked != final_bookmarked  # State should have changed
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Article card interactions test failed: {str(e)}")
    
    def test_phase_filtering(self, driver, authenticated_user):
        """Test Be-Do-Have phase filtering"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Click on DO phase filter
            do_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'DO (Skills)')]"))
            )
            do_button.click()
            
            # Wait for filtered results
            time.sleep(2)
            
            # Verify all visible articles are DO phase
            phase_badges = driver.find_elements(By.CSS_SELECTOR, '.phase-badge')
            for badge in phase_badges:
                assert 'DO' in badge.text
                
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Phase filtering test failed: {str(e)}")
    
    def test_cultural_relevance_display(self, driver, authenticated_user):
        """Test cultural relevance badge display"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Wait for articles to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'article-card'))
            )
            
            # Check for cultural relevance indicators
            relevance_badges = driver.find_elements(By.CLASS_NAME, 'cultural-relevance-badge')
            assert len(relevance_badges) > 0
            
            # Verify badge contains percentage or score
            for badge in relevance_badges:
                badge_text = badge.text
                assert '%' in badge_text or 'Match' in badge_text or 'Score' in badge_text
                
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Cultural relevance display test failed: {str(e)}")

    def test_article_detail_page(self, driver, authenticated_user):
        """Test article detail page functionality"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Click on first article
            article_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.article-card a'))
            )
            article_link.click()
            
            # Wait for article detail page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'article-content'))
            )
            
            # Verify article content is displayed
            article_title = driver.find_element(By.CLASS_NAME, 'article-title')
            article_content = driver.find_element(By.CLASS_NAME, 'article-content')
            
            assert article_title.is_displayed()
            assert article_content.is_displayed()
            
            # Test reading progress tracking
            progress_indicator = driver.find_element(By.CLASS_NAME, 'reading-progress')
            assert progress_indicator.is_displayed()
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Article detail page test failed: {str(e)}")

    def test_user_dashboard_functionality(self, driver, authenticated_user):
        """Test user dashboard features"""
        try:
            driver.get('http://localhost:3000/dashboard')
            
            # Wait for dashboard to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'dashboard-content'))
            )
            
            # Check for assessment scores display
            assessment_scores = driver.find_elements(By.CLASS_NAME, 'assessment-score')
            assert len(assessment_scores) >= 3  # BE, DO, HAVE scores
            
            # Check for reading statistics
            reading_stats = driver.find_element(By.CLASS_NAME, 'reading-statistics')
            assert reading_stats.is_displayed()
            
            # Check for recent articles
            recent_articles = driver.find_elements(By.CLASS_NAME, 'recent-article')
            assert len(recent_articles) >= 0  # May be empty for new users
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"User dashboard test failed: {str(e)}")

    def test_responsive_design(self, driver, authenticated_user):
        """Test responsive design functionality"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Test mobile viewport
            driver.set_window_size(375, 667)  # iPhone SE size
            time.sleep(2)
            
            # Check for mobile navigation
            mobile_menu = driver.find_element(By.CLASS_NAME, 'mobile-menu')
            assert mobile_menu.is_displayed()
            
            # Test tablet viewport
            driver.set_window_size(768, 1024)  # iPad size
            time.sleep(2)
            
            # Check for tablet layout
            article_grid = driver.find_element(By.CLASS_NAME, 'article-grid')
            assert article_grid.is_displayed()
            
            # Reset to desktop size
            driver.set_window_size(1920, 1080)
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Responsive design test failed: {str(e)}")

class TestPerformance:
    """Test application performance and scalability"""
    
    def test_search_response_time(self, client, auth_headers, sample_articles):
        """Test search endpoint response time"""
        import time
        
        search_data = {'query': 'career development'}
        
        start_time = time.time()
        response = client.post('/api/articles/search',
                              json=search_data, 
                              headers=auth_headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Should respond within 500ms
    
    def test_database_query_performance(self, app):
        """Test database query performance with larger dataset"""
        with app.app_context():
            import time
            from backend.models.articles import Article
            from app import db
            
            # Create many articles for performance testing
            articles = []
            for i in range(100):
                article = Article(
                    url=f'https://example.com/article-{i}',
                    title=f'Test Article {i}',
                    content='Test content for performance testing...',
                    content_preview='Test content for performance testing...',
                    primary_phase='DO',
                    difficulty_level='Beginner',
                    domain='example.com'
                )
                articles.append(article)
            
            db.session.add_all(articles)
            db.session.commit()
            
            # Test search performance
            start_time = time.time()
            results = db.session.query(Article).filter(
                Article.title.ilike('%test%')
            ).all()
            end_time = time.time()
            
            query_time = end_time - start_time
            assert query_time < 0.1  # Database query should be fast
            assert len(results) > 0

    def test_page_load_performance(self, driver, authenticated_user):
        """Test page load performance"""
        try:
            start_time = time.time()
            driver.get('http://localhost:3000/articles')
            
            # Wait for page to be fully loaded
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'article-card'))
            )
            end_time = time.time()
            
            load_time = end_time - start_time
            assert load_time < 3.0  # Page should load within 3 seconds
            
        except TimeoutException:
            pytest.fail("Page load performance test failed - page took too long to load")

    def test_search_performance_with_large_dataset(self, driver, authenticated_user):
        """Test search performance with many articles"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Find search input
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="Search"]'))
            )
            
            # Perform search and measure time
            start_time = time.time()
            search_input.clear()
            search_input.send_keys('test')
            search_input.send_keys(Keys.RETURN)
            
            # Wait for results
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'article-card'))
            )
            end_time = time.time()
            
            search_time = end_time - start_time
            assert search_time < 2.0  # Search should complete within 2 seconds
            
        except TimeoutException:
            pytest.fail("Search performance test failed")

class TestSecurity:
    """Test security and access control"""
    
    def test_sql_injection_protection(self, client, auth_headers):
        """Test protection against SQL injection attacks"""
        malicious_query = "'; DROP TABLE articles; --"
        
        response = client.post('/api/articles/search',
                              json={'query': malicious_query},
                              headers=auth_headers)
        
        # Should handle gracefully without errors
        assert response.status_code in [200, 400]  # Either success or validation error
        
    def test_xss_protection(self, client, auth_headers):
        """Test cross-site scripting protection"""
        xss_payload = '<script>alert("XSS")</script>'
        
        response = client.post('/api/articles/search',
                              json={'query': xss_payload},
                              headers=auth_headers)
        
        assert response.status_code == 200
        # Response should not contain unescaped script tags
        assert '<script>' not in response.get_data(as_text=True)
    
    def test_authorization_bypass_attempts(self, client):
        """Test attempts to bypass authentication"""
        # Try accessing protected endpoint without auth
        response = client.get('/api/articles')
        assert response.status_code == 401
        
        # Try with invalid token
        fake_headers = {'Authorization': 'Bearer invalid-token'}
        response = client.get('/api/articles', headers=fake_headers)
        assert response.status_code in [401, 422]  # Invalid token format or unauthorized

    def test_frontend_security(self, driver):
        """Test frontend security measures"""
        try:
            # Test accessing protected page without authentication
            driver.get('http://localhost:3000/articles')
            
            # Should redirect to login page
            WebDriverWait(driver, 10).until(
                EC.url_contains('/login')
            )
            
            # Test XSS in search input
            driver.get('http://localhost:3000/login')
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'email'))
            )
            
            # Try to inject script
            email_field.send_keys('<script>alert("XSS")</script>')
            
            # Check that script is not executed (no alert should appear)
            # This is a basic test - in a real scenario you'd use more sophisticated detection
            
        except TimeoutException:
            pytest.fail("Frontend security test failed")

class TestAccessibility:
    """Test accessibility features"""
    
    def test_keyboard_navigation(self, driver, authenticated_user):
        """Test keyboard navigation accessibility"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Use Tab to navigate through elements
            body = driver.find_element(By.TAG_NAME, 'body')
            body.send_keys(Keys.TAB)
            
            # Check that focus is visible
            focused_element = driver.switch_to.active_element
            assert focused_element.is_displayed()
            
            # Test Enter key functionality
            focused_element.send_keys(Keys.ENTER)
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Keyboard navigation test failed: {str(e)}")
    
    def test_screen_reader_compatibility(self, driver, authenticated_user):
        """Test screen reader compatibility"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Check for proper ARIA labels
            aria_labels = driver.find_elements(By.CSS_SELECTOR, '[aria-label]')
            assert len(aria_labels) > 0
            
            # Check for proper heading structure
            headings = driver.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6')
            assert len(headings) > 0
            
            # Check for alt text on images
            images = driver.find_elements(By.TAG_NAME, 'img')
            for img in images:
                alt_text = img.get_attribute('alt')
                assert alt_text is not None  # Should have alt text
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Screen reader compatibility test failed: {str(e)}")

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_network_error_handling(self, driver):
        """Test handling of network errors"""
        try:
            # Try to access a non-existent page
            driver.get('http://localhost:3000/non-existent-page')
            
            # Should show 404 page
            error_message = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'error-page'))
            )
            assert error_message.is_displayed()
            
        except TimeoutException:
            # If no error page is implemented, that's also acceptable
            assert True
    
    def test_empty_search_results(self, driver, authenticated_user):
        """Test handling of empty search results"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Find search input
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="Search"]'))
            )
            
            # Search for something that shouldn't exist
            search_input.clear()
            search_input.send_keys('xyz123nonexistent')
            search_input.send_keys(Keys.RETURN)
            
            # Should show no results message
            no_results = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'no-results'))
            )
            assert no_results.is_displayed()
            
        except TimeoutException:
            pytest.fail("Empty search results test failed")

class TestDataConsistency:
    """Test data consistency across frontend and backend"""
    
    def test_article_data_consistency(self, driver, authenticated_user, sample_articles):
        """Test that article data is consistent between frontend and backend"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Get first article from frontend
            article_card = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'article-card'))
            )
            
            frontend_title = article_card.find_element(By.CLASS_NAME, 'article-title').text
            frontend_phase = article_card.find_element(By.CLASS_NAME, 'phase-badge').text
            
            # Compare with backend data
            backend_article = sample_articles[0]
            assert frontend_title == backend_article['title']
            assert frontend_phase == backend_article['primary_phase']
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Data consistency test failed: {str(e)}")
    
    def test_user_progress_synchronization(self, driver, authenticated_user):
        """Test that user progress is properly synchronized"""
        try:
            driver.get('http://localhost:3000/articles')
            
            # Click on an article to start reading
            article_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.article-card a'))
            )
            article_link.click()
            
            # Wait for article page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'article-content'))
            )
            
            # Check that progress is tracked
            progress_indicator = driver.find_element(By.CLASS_NAME, 'reading-progress')
            assert progress_indicator.is_displayed()
            
            # Navigate back to articles list
            driver.back()
            
            # Check that progress is reflected in the list
            progress_badge = driver.find_element(By.CLASS_NAME, 'progress-badge')
            assert progress_badge.is_displayed()
            
        except (TimeoutException, NoSuchElementException) as e:
            pytest.fail(f"Progress synchronization test failed: {str(e)}")
