"""
Performance Tests for Assessment System

Comprehensive performance testing including page load speed, assessment submission,
database query optimization, concurrent user load testing, memory leak detection,
and mobile performance benchmarks.
"""

import pytest
import time
import psutil
import threading
import concurrent.futures
from unittest.mock import patch, Mock, AsyncMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import json

pytestmark = pytest.mark.performance

class TestPageLoadPerformance:
    """Test page load speed optimization"""
    
    def test_landing_page_load_speed(self, chrome_driver, performance_monitor):
        """Test landing page load speed (target: <3s on 3G)"""
        performance_monitor.start_timer('landing_page_load')
        
        chrome_driver.get("http://localhost:3000")
        
        # Wait for page to fully load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "landing-page"))
        )
        
        # Wait for all resources to load
        WebDriverWait(chrome_driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        performance_monitor.end_timer('landing_page_load')
        
        load_time = performance_monitor.get_duration('landing_page_load')
        
        # Target: <3s on 3G connection
        assert load_time < 3.0, f"Landing page took {load_time}s to load, exceeds 3s target"
        
        # Verify page is fully interactive
        cta_button = chrome_driver.find_element(By.CLASS_NAME, "cta-button")
        assert cta_button.is_enabled()
    
    def test_assessment_page_load_speed(self, chrome_driver, performance_monitor):
        """Test assessment page load speed"""
        performance_monitor.start_timer('assessment_page_load')
        
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        # Wait for assessment to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Wait for all resources to load
        WebDriverWait(chrome_driver, 10).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        performance_monitor.end_timer('assessment_page_load')
        
        load_time = performance_monitor.get_duration('assessment_page_load')
        
        # Target: <2s for assessment page
        assert load_time < 2.0, f"Assessment page took {load_time}s to load, exceeds 2s target"
    
    def test_results_page_load_speed(self, chrome_driver, performance_monitor):
        """Test results page load speed after assessment completion"""
        # Complete assessment first
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Complete assessment
        self._complete_assessment_quick(chrome_driver)
        
        # Measure results page load time
        performance_monitor.start_timer('results_page_load')
        
        # Wait for results to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        performance_monitor.end_timer('results_page_load')
        
        load_time = performance_monitor.get_duration('results_page_load')
        
        # Target: <1.5s for results page
        assert load_time < 1.5, f"Results page took {load_time}s to load, exceeds 1.5s target"
    
    def test_mobile_page_load_performance(self, chrome_driver, performance_monitor):
        """Test page load performance on mobile devices"""
        # Set mobile viewport
        chrome_driver.set_window_size(375, 667)
        
        # Test landing page on mobile
        performance_monitor.start_timer('mobile_landing_page_load')
        
        chrome_driver.get("http://localhost:3000")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "landing-page"))
        )
        
        performance_monitor.end_timer('mobile_landing_page_load')
        
        load_time = performance_monitor.get_duration('mobile_landing_page_load')
        
        # Target: <4s on mobile (slower connection)
        assert load_time < 4.0, f"Mobile landing page took {load_time}s to load, exceeds 4s target"
    
    def test_resource_optimization(self, chrome_driver):
        """Test resource optimization (images, CSS, JS)"""
        chrome_driver.get("http://localhost:3000")
        
        # Wait for page to load
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "landing-page"))
        )
        
        # Check image optimization
        images = chrome_driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            # Check if images are lazy loaded
            loading_attr = img.get_attribute("loading")
            if loading_attr:
                assert loading_attr == "lazy"
            
            # Check if images have proper dimensions
            width = img.get_attribute("width")
            height = img.get_attribute("height")
            if width and height:
                assert int(width) > 0
                assert int(height) > 0
        
        # Check CSS optimization
        css_files = chrome_driver.find_elements(By.CSS_SELECTOR, "link[rel='stylesheet']")
        for css_file in css_files:
            href = css_file.get_attribute("href")
            if href and "min.css" not in href:
                # Check if CSS is minified or compressed
                pass  # This would require checking the actual file content
        
        # Check JavaScript optimization
        js_files = chrome_driver.find_elements(By.TAG_NAME, "script")
        for js_file in js_files:
            src = js_file.get_attribute("src")
            if src and "min.js" not in src:
                # Check if JS is minified or compressed
                pass  # This would require checking the actual file content


class TestAssessmentSubmissionPerformance:
    """Test assessment submission performance"""
    
    def test_assessment_submission_speed(self, chrome_driver, performance_monitor):
        """Test assessment submission performance (target: <2s)"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Complete assessment quickly
        self._complete_assessment_quick(chrome_driver)
        
        # Measure submission time
        performance_monitor.start_timer('assessment_submission')
        
        # Wait for submission to complete
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        performance_monitor.end_timer('assessment_submission')
        
        submission_time = performance_monitor.get_duration('assessment_submission')
        
        # Target: <2s for assessment submission
        assert submission_time < 2.0, f"Assessment submission took {submission_time}s, exceeds 2s target"
    
    def test_large_assessment_data_performance(self, chrome_driver, performance_monitor):
        """Test performance with large assessment data"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Fill assessment with large data
        self._fill_assessment_with_large_data(chrome_driver)
        
        # Measure submission time
        performance_monitor.start_timer('large_assessment_submission')
        
        # Submit assessment
        submit_button = chrome_driver.find_element(By.CLASS_NAME, "submit-assessment-button")
        submit_button.click()
        
        # Wait for results
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
        )
        
        performance_monitor.end_timer('large_assessment_submission')
        
        submission_time = performance_monitor.get_duration('large_assessment_submission')
        
        # Target: <3s for large assessment data
        assert submission_time < 3.0, f"Large assessment submission took {submission_time}s, exceeds 3s target"
    
    def test_assessment_auto_save_performance(self, chrome_driver, performance_monitor):
        """Test auto-save performance during assessment"""
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Fill first question
        question_container = chrome_driver.find_element(By.CLASS_NAME, "question-container")
        salary_input = question_container.find_element(By.NAME, "current_salary")
        salary_input.send_keys("75000")
        
        # Measure auto-save time
        performance_monitor.start_timer('auto_save')
        
        # Wait for auto-save to complete
        time.sleep(2)  # Wait for auto-save to trigger
        
        performance_monitor.end_timer('auto_save')
        
        auto_save_time = performance_monitor.get_duration('auto_save')
        
        # Target: <1s for auto-save
        assert auto_save_time < 1.0, f"Auto-save took {auto_save_time}s, exceeds 1s target"


class TestDatabaseQueryPerformance:
    """Test database query optimization"""
    
    def test_income_comparison_performance_target(self, client, auth_headers, performance_monitor):
        """Test that income comparison meets 45ms performance target"""
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        performance_monitor.start_timer('income_comparison_query')
        
        response = client.post(
            '/api/v1/assessment-scoring/calculate',
            headers=auth_headers,
            json={'assessment_data': sample_data}
        )
        
        performance_monitor.end_timer('income_comparison_query')
        
        query_time = performance_monitor.get_duration('income_comparison_query')
        query_time_ms = query_time * 1000
        
        assert response.status_code == 200
        assert query_time_ms < 45, f"Income comparison query took {query_time_ms}ms, exceeds 45ms target"
    
    def test_assessment_history_query_performance(self, client, auth_headers, performance_monitor):
        """Test assessment history query performance"""
        performance_monitor.start_timer('assessment_history_query')
        
        response = client.get(
            '/api/v1/assessment-scoring/history',
            headers=auth_headers
        )
        
        performance_monitor.end_timer('assessment_history_query')
        
        query_time = performance_monitor.get_duration('assessment_history_query')
        query_time_ms = query_time * 1000
        
        assert response.status_code == 200
        assert query_time_ms < 100, f"Assessment history query took {query_time_ms}ms, exceeds 100ms target"
    
    def test_database_connection_pool_performance(self, client, auth_headers, performance_monitor):
        """Test database connection pool performance under load"""
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        # Test multiple concurrent requests
        def make_request():
            start_time = time.time()
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_data}
            )
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Verify all requests succeeded
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        assert all(status == 200 for status in status_codes)
        
        # Verify performance is consistent
        avg_response_time = sum(response_times) / len(response_times)
        avg_response_time_ms = avg_response_time * 1000
        
        assert avg_response_time_ms < 100, f"Average response time {avg_response_time_ms}ms exceeds 100ms target"
        
        # Verify no significant outliers
        max_response_time_ms = max(response_times) * 1000
        assert max_response_time_ms < 200, f"Max response time {max_response_time_ms}ms exceeds 200ms target"
    
    def test_database_query_optimization(self, client, auth_headers, performance_monitor):
        """Test database query optimization with complex queries"""
        # Test complex assessment query
        performance_monitor.start_timer('complex_assessment_query')
        
        response = client.get(
            '/api/v1/assessment-scoring/analytics',
            headers=auth_headers
        )
        
        performance_monitor.end_timer('complex_assessment_query')
        
        query_time = performance_monitor.get_duration('complex_assessment_query')
        query_time_ms = query_time * 1000
        
        assert response.status_code == 200
        assert query_time_ms < 150, f"Complex assessment query took {query_time_ms}ms, exceeds 150ms target"


class TestConcurrentUserLoadTesting:
    """Test concurrent user load handling"""
    
    def test_concurrent_user_load(self, client, auth_headers, load_test_executor, performance_monitor):
        """Test system performance under concurrent user load"""
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        def make_assessment_request():
            start_time = time.time()
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_data}
            )
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Test with 50 concurrent users
        performance_monitor.start_timer('concurrent_load_test')
        
        futures = []
        for i in range(50):
            future = load_test_executor.submit(make_assessment_request)
            futures.append(future)
        
        # Wait for all requests to complete
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append((500, 10.0))  # Error case
        
        performance_monitor.end_timer('concurrent_load_test')
        
        total_time = performance_monitor.get_duration('concurrent_load_test')
        
        # Analyze results
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        successful_requests = [r for r in status_codes if r == 200]
        failed_requests = [r for r in status_codes if r != 200]
        
        # Verify success rate
        success_rate = len(successful_requests) / len(status_codes)
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% threshold"
        
        # Verify response time performance
        avg_response_time = sum(response_times) / len(response_times)
        avg_response_time_ms = avg_response_time * 1000
        
        assert avg_response_time_ms < 200, f"Average response time {avg_response_time_ms}ms exceeds 200ms target"
        
        # Verify throughput
        throughput = len(results) / total_time
        assert throughput >= 10, f"Throughput {throughput:.1f} requests/sec below 10 req/sec target"
    
    def test_stress_testing(self, client, auth_headers, load_test_executor, performance_monitor):
        """Test system under stress conditions"""
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        def make_stress_request():
            start_time = time.time()
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_data}
            )
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Stress test with 100 concurrent users
        performance_monitor.start_timer('stress_test')
        
        futures = []
        for i in range(100):
            future = load_test_executor.submit(make_stress_request)
            futures.append(future)
        
        # Wait for all requests to complete
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append((500, 10.0))
        
        performance_monitor.end_timer('stress_test')
        
        total_time = performance_monitor.get_duration('stress_test')
        
        # Analyze stress test results
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        successful_requests = [r for r in status_codes if r == 200]
        failed_requests = [r for r in status_codes if r != 200]
        
        # Verify system doesn't completely fail under stress
        success_rate = len(successful_requests) / len(status_codes)
        assert success_rate >= 0.80, f"Stress test success rate {success_rate:.2%} below 80% threshold"
        
        # Verify response times don't degrade too much
        avg_response_time = sum(response_times) / len(response_times)
        avg_response_time_ms = avg_response_time * 1000
        
        assert avg_response_time_ms < 500, f"Stress test average response time {avg_response_time_ms}ms exceeds 500ms target"
    
    def test_gradual_load_increase(self, client, auth_headers, load_test_executor, performance_monitor):
        """Test system performance with gradual load increase"""
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        def make_request():
            start_time = time.time()
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_data}
            )
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Test with increasing load: 10, 25, 50, 75 users
        load_levels = [10, 25, 50, 75]
        results_by_level = {}
        
        for load_level in load_levels:
            performance_monitor.start_timer(f'load_level_{load_level}')
            
            futures = []
            for i in range(load_level):
                future = load_test_executor.submit(make_request)
                futures.append(future)
            
            level_results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    level_results.append(result)
                except Exception as e:
                    level_results.append((500, 10.0))
            
            performance_monitor.end_timer(f'load_level_{load_level}')
            
            results_by_level[load_level] = level_results
        
        # Analyze performance degradation
        for load_level, results in results_by_level.items():
            status_codes = [result[0] for result in results]
            response_times = [result[1] for result in results]
            
            success_rate = len([r for r in status_codes if r == 200]) / len(status_codes)
            avg_response_time = sum(response_times) / len(response_times)
            
            # Verify performance doesn't degrade too much with increased load
            if load_level <= 25:
                assert success_rate >= 0.98, f"Success rate {success_rate:.2%} below 98% for {load_level} users"
                assert avg_response_time < 0.1, f"Response time {avg_response_time}s exceeds 100ms for {load_level} users"
            elif load_level <= 50:
                assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% for {load_level} users"
                assert avg_response_time < 0.2, f"Response time {avg_response_time}s exceeds 200ms for {load_level} users"
            else:
                assert success_rate >= 0.90, f"Success rate {success_rate:.2%} below 90% for {load_level} users"
                assert avg_response_time < 0.3, f"Response time {avg_response_time}s exceeds 300ms for {load_level} users"


class TestMemoryLeakDetection:
    """Test memory leak detection and prevention"""
    
    def test_memory_usage_optimization(self, chrome_driver, performance_monitor):
        """Test memory usage optimization during assessment flow"""
        initial_memory = performance_monitor.get_memory_usage()
        
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Complete multiple assessments to test memory usage
        for i in range(5):
            # Complete assessment
            self._complete_assessment_quick(chrome_driver)
            
            # Wait for results
            WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
            )
            
            # Navigate back to start new assessment
            chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
            
            WebDriverWait(chrome_driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
            )
        
        final_memory = performance_monitor.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100.0, f"Memory usage increased by {memory_increase}MB, exceeds 100MB limit"
    
    def test_backend_memory_usage(self, client, auth_headers, performance_monitor):
        """Test backend memory usage during multiple requests"""
        sample_data = {
            'current_salary': 75000,
            'field': 'software_development',
            'relationship_status': 'married',
            'financial_stress_frequency': 'sometimes'
        }
        
        initial_memory = performance_monitor.get_memory_usage()
        
        # Make multiple requests
        for i in range(20):
            response = client.post(
                '/api/v1/assessment-scoring/calculate',
                headers=auth_headers,
                json={'assessment_data': sample_data}
            )
            assert response.status_code == 200
        
        final_memory = performance_monitor.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (less than 50MB)
        assert memory_increase < 50.0, f"Backend memory usage increased by {memory_increase}MB, exceeds 50MB limit"
    
    def test_memory_cleanup_after_session(self, chrome_driver, performance_monitor):
        """Test memory cleanup after user session"""
        initial_memory = performance_monitor.get_memory_usage()
        
        # Complete full user session
        chrome_driver.get("http://localhost:3000")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "landing-page"))
        )
        
        # Navigate to assessment
        cta_button = chrome_driver.find_element(By.CLASS_NAME, "cta-button")
        cta_button.click()
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Complete assessment
        self._complete_assessment_quick(chrome_driver)
        
        # Navigate away
        chrome_driver.get("http://localhost:3000")
        
        # Force garbage collection
        chrome_driver.execute_script("if (window.gc) window.gc();")
        
        final_memory = performance_monitor.get_memory_usage()
        memory_increase = final_memory - initial_memory
        
        # Memory should be cleaned up (increase less than 20MB)
        assert memory_increase < 20.0, f"Memory not properly cleaned up, increase of {memory_increase}MB"


class TestMobilePerformanceBenchmarks:
    """Test mobile performance benchmarks"""
    
    def test_mobile_page_load_benchmarks(self, chrome_driver, performance_monitor):
        """Test mobile page load performance benchmarks"""
        # Set mobile viewport
        chrome_driver.set_window_size(375, 667)
        
        # Test landing page on mobile
        performance_monitor.start_timer('mobile_landing_load')
        
        chrome_driver.get("http://localhost:3000")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "landing-page"))
        )
        
        performance_monitor.end_timer('mobile_landing_load')
        
        load_time = performance_monitor.get_duration('mobile_landing_load')
        
        # Mobile benchmarks: <4s on 3G, <2s on 4G
        assert load_time < 4.0, f"Mobile landing page took {load_time}s, exceeds 4s 3G target"
    
    def test_mobile_assessment_performance(self, chrome_driver, performance_monitor):
        """Test mobile assessment performance"""
        chrome_driver.set_window_size(375, 667)
        
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Complete assessment on mobile
        performance_monitor.start_timer('mobile_assessment_completion')
        
        self._complete_assessment_mobile(chrome_driver)
        
        performance_monitor.end_timer('mobile_assessment_completion')
        
        completion_time = performance_monitor.get_duration('mobile_assessment_completion')
        
        # Mobile assessment should complete within reasonable time
        assert completion_time < 30.0, f"Mobile assessment took {completion_time}s, exceeds 30s target"
    
    def test_mobile_touch_response_time(self, chrome_driver, performance_monitor):
        """Test mobile touch response time"""
        chrome_driver.set_window_size(375, 667)
        
        chrome_driver.get("http://localhost:3000/assessment/ai-job-risk")
        
        WebDriverWait(chrome_driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "assessment-flow"))
        )
        
        # Test touch response time
        next_button = chrome_driver.find_element(By.CLASS_NAME, "next-button")
        
        performance_monitor.start_timer('touch_response')
        
        # Simulate touch
        chrome_driver.execute_script("arguments[0].click();", next_button)
        
        # Wait for response
        time.sleep(0.1)
        
        performance_monitor.end_timer('touch_response')
        
        response_time = performance_monitor.get_duration('touch_response')
        response_time_ms = response_time * 1000
        
        # Touch response should be very fast (<100ms)
        assert response_time_ms < 100, f"Touch response took {response_time_ms}ms, exceeds 100ms target"
    
    def _complete_assessment_quick(self, driver):
        """Helper method to complete assessment quickly for performance testing"""
        questions_completed = 0
        max_questions = 5  # Limit for performance testing
        
        while questions_completed < max_questions:
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
                )
                
                question_container = driver.find_element(By.CLASS_NAME, "question-container")
                
                # Quick fill
                try:
                    text_input = question_container.find_element(By.TAG_NAME, "input")
                    if text_input.get_attribute("type") == "number":
                        text_input.send_keys("75000")
                    elif text_input.get_attribute("type") == "text":
                        text_input.send_keys("Test")
                except:
                    pass
                
                try:
                    radio_buttons = question_container.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    if radio_buttons:
                        radio_buttons[0].click()
                except:
                    pass
                
                next_button = driver.find_element(By.CLASS_NAME, "next-button")
                next_button.click()
                
                questions_completed += 1
                
                try:
                    WebDriverWait(driver, 2).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
                    )
                    break
                except:
                    continue
                    
            except Exception as e:
                break
    
    def _complete_assessment_mobile(self, driver):
        """Helper method to complete assessment on mobile"""
        questions_completed = 0
        max_questions = 10
        
        while questions_completed < max_questions:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
                )
                
                question_container = driver.find_element(By.CLASS_NAME, "question-container")
                
                # Mobile-friendly filling
                try:
                    text_input = question_container.find_element(By.TAG_NAME, "input")
                    if text_input.get_attribute("type") == "number":
                        text_input.send_keys("75000")
                    elif text_input.get_attribute("type") == "text":
                        text_input.send_keys("Test")
                except:
                    pass
                
                try:
                    radio_buttons = question_container.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    if radio_buttons:
                        driver.execute_script("arguments[0].click();", radio_buttons[0])
                except:
                    pass
                
                next_button = driver.find_element(By.CLASS_NAME, "next-button")
                driver.execute_script("arguments[0].click();", next_button)
                
                questions_completed += 1
                
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
                    )
                    break
                except:
                    continue
                    
            except Exception as e:
                break
    
    def _fill_assessment_with_large_data(self, driver):
        """Helper method to fill assessment with large data for performance testing"""
        questions_completed = 0
        max_questions = 10
        
        while questions_completed < max_questions:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
                )
                
                question_container = driver.find_element(By.CLASS_NAME, "question-container")
                
                # Fill with large data
                try:
                    text_input = question_container.find_element(By.TAG_NAME, "input")
                    if text_input.get_attribute("type") == "text":
                        text_input.send_keys("x" * 1000)  # Large text input
                    elif text_input.get_attribute("type") == "number":
                        text_input.send_keys("75000")
                except:
                    pass
                
                try:
                    radio_buttons = question_container.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    if radio_buttons:
                        radio_buttons[0].click()
                except:
                    pass
                
                next_button = driver.find_element(By.CLASS_NAME, "next-button")
                next_button.click()
                
                questions_completed += 1
                
                try:
                    WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "assessment-results"))
                    )
                    break
                except:
                    continue
                    
            except Exception as e:
                break
