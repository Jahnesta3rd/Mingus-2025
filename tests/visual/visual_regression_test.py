#!/usr/bin/env python3
"""
Mingus Application - Visual Regression Testing
============================================

Visual regression testing using Percy and custom screenshot comparison
for UI components and pages.

Author: Mingus QA Team
Date: January 2025
"""

import pytest
import time
import json
import logging
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image, ImageChops
import numpy as np
from skimage.metrics import structural_similarity as ssim
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualRegressionTest:
    """Visual regression testing class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url', 'http://localhost:3000')
        self.screenshots_dir = config.get('screenshots_dir', 'visual_test_screenshots')
        self.baseline_dir = config.get('baseline_dir', 'visual_baselines')
        self.threshold = config.get('threshold', 0.95)  # 95% similarity threshold
        self.driver = None
        self.test_results = []
        
        # Create directories
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.baseline_dir, exist_ok=True)
        os.makedirs(f"{self.screenshots_dir}/current", exist_ok=True)
        os.makedirs(f"{self.screenshots_dir}/diffs", exist_ok=True)
    
    def setup_driver(self, device_type: str = 'desktop'):
        """Setup WebDriver for visual testing"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--force-device-scale-factor=1')
        
        if device_type == 'mobile':
            chrome_options.add_argument('--window-size=375,667')
            chrome_options.add_experimental_option("mobileEmulation", {
                "deviceMetrics": {"width": 375, "height": 667, "pixelRatio": 2.0},
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            })
        elif device_type == 'tablet':
            chrome_options.add_argument('--window-size=768,1024')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        return self.driver
    
    def teardown_driver(self):
        """Cleanup WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def take_screenshot(self, name: str, device_type: str = 'desktop') -> str:
        """Take screenshot and save to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.screenshots_dir}/current/{name}_{device_type}_{timestamp}.png"
        
        # Ensure page is fully loaded
        time.sleep(2)
        
        # Take full page screenshot
        self.driver.save_screenshot(filename)
        
        # Also take viewport screenshot
        viewport_filename = f"{self.screenshots_dir}/current/{name}_{device_type}_viewport_{timestamp}.png"
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        self.driver.save_screenshot(viewport_filename)
        
        logger.info(f"Screenshot saved: {filename}")
        return filename
    
    def take_element_screenshot(self, element_selector: str, name: str, device_type: str = 'desktop') -> str:
        """Take screenshot of specific element"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, element_selector)
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Take element screenshot
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.screenshots_dir}/current/{name}_{device_type}_element_{timestamp}.png"
            element.screenshot(filename)
            
            logger.info(f"Element screenshot saved: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error taking element screenshot: {e}")
            return None
    
    def compare_images(self, current_path: str, baseline_path: str) -> Dict[str, Any]:
        """Compare two images and return similarity metrics"""
        try:
            # Load images
            current_img = Image.open(current_path)
            baseline_img = Image.open(baseline_path)
            
            # Resize images to same size if needed
            if current_img.size != baseline_img.size:
                baseline_img = baseline_img.resize(current_img.size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if current_img.mode != 'RGB':
                current_img = current_img.convert('RGB')
            if baseline_img.mode != 'RGB':
                baseline_img = baseline_img.convert('RGB')
            
            # Calculate structural similarity
            current_array = np.array(current_img)
            baseline_array = np.array(baseline_img)
            
            similarity = ssim(current_array, baseline_array, multichannel=True)
            
            # Calculate pixel difference
            diff = ImageChops.difference(current_img, baseline_img)
            diff_array = np.array(diff)
            pixel_diff = np.sum(diff_array > 0) / diff_array.size
            
            # Create diff image
            diff_filename = f"{self.screenshots_dir}/diffs/diff_{os.path.basename(current_path)}"
            diff.save(diff_filename)
            
            return {
                'similarity': similarity,
                'pixel_difference': pixel_diff,
                'is_similar': similarity >= self.threshold,
                'diff_image': diff_filename
            }
            
        except Exception as e:
            logger.error(f"Error comparing images: {e}")
            return {
                'similarity': 0.0,
                'pixel_difference': 1.0,
                'is_similar': False,
                'error': str(e)
            }
    
    def test_landing_page_visual(self):
        """Test landing page visual regression"""
        logger.info("Testing landing page visual regression...")
        
        try:
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take full page screenshot
            current_screenshot = self.take_screenshot("landing_page", "desktop")
            
            # Test different sections
            sections = [
                ("hero_section", "section[role='banner']"),
                ("pricing_section", "#pricing"),
                ("faq_section", "#faq"),
                ("features_section", "#features")
            ]
            
            for section_name, selector in sections:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        self.take_element_screenshot(selector, f"landing_{section_name}", "desktop")
                except:
                    logger.warning(f"Section {section_name} not found or not visible")
            
            # Compare with baseline
            baseline_path = f"{self.baseline_dir}/landing_page_desktop.png"
            if os.path.exists(baseline_path):
                comparison = self.compare_images(current_screenshot, baseline_path)
                return {
                    'test_name': 'landing_page_visual',
                    'status': 'PASS' if comparison['is_similar'] else 'FAIL',
                    'similarity': comparison['similarity'],
                    'threshold': self.threshold,
                    'comparison': comparison
                }
            else:
                # Save as new baseline
                os.rename(current_screenshot, baseline_path)
                return {
                    'test_name': 'landing_page_visual',
                    'status': 'BASELINE_CREATED',
                    'message': 'New baseline created'
                }
                
        except Exception as e:
            logger.error(f"Landing page visual test failed: {e}")
            return {
                'test_name': 'landing_page_visual',
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_assessment_modal_visual(self):
        """Test assessment modal visual regression"""
        logger.info("Testing assessment modal visual regression...")
        
        try:
            self.driver.get(self.base_url)
            
            # Click on assessment button
            ai_risk_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label*='Determine Your Replacement Risk Due To AI']"))
            )
            ai_risk_button.click()
            
            # Wait for modal to appear
            modal = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[role='dialog']"))
            )
            
            # Take modal screenshot
            current_screenshot = self.take_element_screenshot("[role='dialog']", "assessment_modal", "desktop")
            
            if current_screenshot:
                # Compare with baseline
                baseline_path = f"{self.baseline_dir}/assessment_modal_desktop.png"
                if os.path.exists(baseline_path):
                    comparison = self.compare_images(current_screenshot, baseline_path)
                    return {
                        'test_name': 'assessment_modal_visual',
                        'status': 'PASS' if comparison['is_similar'] else 'FAIL',
                        'similarity': comparison['similarity'],
                        'threshold': self.threshold,
                        'comparison': comparison
                    }
                else:
                    # Save as new baseline
                    os.rename(current_screenshot, baseline_path)
                    return {
                        'test_name': 'assessment_modal_visual',
                        'status': 'BASELINE_CREATED',
                        'message': 'New baseline created'
                    }
            
        except Exception as e:
            logger.error(f"Assessment modal visual test failed: {e}")
            return {
                'test_name': 'assessment_modal_visual',
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_pricing_section_visual(self):
        """Test pricing section visual regression"""
        logger.info("Testing pricing section visual regression...")
        
        try:
            self.driver.get(self.base_url)
            
            # Scroll to pricing section
            pricing_section = self.driver.find_element(By.CSS_SELECTOR, "#pricing")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", pricing_section)
            time.sleep(2)
            
            # Take pricing section screenshot
            current_screenshot = self.take_element_screenshot("#pricing", "pricing_section", "desktop")
            
            if current_screenshot:
                # Compare with baseline
                baseline_path = f"{self.baseline_dir}/pricing_section_desktop.png"
                if os.path.exists(baseline_path):
                    comparison = self.compare_images(current_screenshot, baseline_path)
                    return {
                        'test_name': 'pricing_section_visual',
                        'status': 'PASS' if comparison['is_similar'] else 'FAIL',
                        'similarity': comparison['similarity'],
                        'threshold': self.threshold,
                        'comparison': comparison
                    }
                else:
                    # Save as new baseline
                    os.rename(current_screenshot, baseline_path)
                    return {
                        'test_name': 'pricing_section_visual',
                        'status': 'BASELINE_CREATED',
                        'message': 'New baseline created'
                    }
            
        except Exception as e:
            logger.error(f"Pricing section visual test failed: {e}")
            return {
                'test_name': 'pricing_section_visual',
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_faq_accordion_visual(self):
        """Test FAQ accordion visual regression"""
        logger.info("Testing FAQ accordion visual regression...")
        
        try:
            self.driver.get(self.base_url)
            
            # Scroll to FAQ section
            faq_section = self.driver.find_element(By.CSS_SELECTOR, "#faq")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", faq_section)
            time.sleep(2)
            
            # Test closed state
            current_screenshot_closed = self.take_element_screenshot("#faq", "faq_accordion_closed", "desktop")
            
            # Click on first FAQ item
            first_faq_button = self.driver.find_element(By.CSS_SELECTOR, "#faq button[aria-expanded]")
            first_faq_button.click()
            time.sleep(1)
            
            # Test open state
            current_screenshot_open = self.take_element_screenshot("#faq", "faq_accordion_open", "desktop")
            
            results = []
            
            # Compare closed state
            if current_screenshot_closed:
                baseline_path = f"{self.baseline_dir}/faq_accordion_closed_desktop.png"
                if os.path.exists(baseline_path):
                    comparison = self.compare_images(current_screenshot_closed, baseline_path)
                    results.append({
                        'state': 'closed',
                        'status': 'PASS' if comparison['is_similar'] else 'FAIL',
                        'similarity': comparison['similarity']
                    })
                else:
                    os.rename(current_screenshot_closed, baseline_path)
                    results.append({
                        'state': 'closed',
                        'status': 'BASELINE_CREATED'
                    })
            
            # Compare open state
            if current_screenshot_open:
                baseline_path = f"{self.baseline_dir}/faq_accordion_open_desktop.png"
                if os.path.exists(baseline_path):
                    comparison = self.compare_images(current_screenshot_open, baseline_path)
                    results.append({
                        'state': 'open',
                        'status': 'PASS' if comparison['is_similar'] else 'FAIL',
                        'similarity': comparison['similarity']
                    })
                else:
                    os.rename(current_screenshot_open, baseline_path)
                    results.append({
                        'state': 'open',
                        'status': 'BASELINE_CREATED'
                    })
            
            return {
                'test_name': 'faq_accordion_visual',
                'results': results
            }
            
        except Exception as e:
            logger.error(f"FAQ accordion visual test failed: {e}")
            return {
                'test_name': 'faq_accordion_visual',
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_mobile_responsive_visual(self):
        """Test mobile responsive visual regression"""
        logger.info("Testing mobile responsive visual regression...")
        
        try:
            # Setup mobile driver
            self.teardown_driver()
            self.setup_driver('mobile')
            
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take mobile screenshot
            current_screenshot = self.take_screenshot("landing_page", "mobile")
            
            # Compare with baseline
            baseline_path = f"{self.baseline_dir}/landing_page_mobile.png"
            if os.path.exists(baseline_path):
                comparison = self.compare_images(current_screenshot, baseline_path)
                return {
                    'test_name': 'mobile_responsive_visual',
                    'status': 'PASS' if comparison['is_similar'] else 'FAIL',
                    'similarity': comparison['similarity'],
                    'threshold': self.threshold,
                    'comparison': comparison
                }
            else:
                # Save as new baseline
                os.rename(current_screenshot, baseline_path)
                return {
                    'test_name': 'mobile_responsive_visual',
                    'status': 'BASELINE_CREATED',
                    'message': 'New baseline created'
                }
                
        except Exception as e:
            logger.error(f"Mobile responsive visual test failed: {e}")
            return {
                'test_name': 'mobile_responsive_visual',
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_tablet_responsive_visual(self):
        """Test tablet responsive visual regression"""
        logger.info("Testing tablet responsive visual regression...")
        
        try:
            # Setup tablet driver
            self.teardown_driver()
            self.setup_driver('tablet')
            
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take tablet screenshot
            current_screenshot = self.take_screenshot("landing_page", "tablet")
            
            # Compare with baseline
            baseline_path = f"{self.baseline_dir}/landing_page_tablet.png"
            if os.path.exists(baseline_path):
                comparison = self.compare_images(current_screenshot, baseline_path)
                return {
                    'test_name': 'tablet_responsive_visual',
                    'status': 'PASS' if comparison['is_similar'] else 'FAIL',
                    'similarity': comparison['similarity'],
                    'threshold': self.threshold,
                    'comparison': comparison
                }
            else:
                # Save as new baseline
                os.rename(current_screenshot, baseline_path)
                return {
                    'test_name': 'tablet_responsive_visual',
                    'status': 'BASELINE_CREATED',
                    'message': 'New baseline created'
                }
                
        except Exception as e:
            logger.error(f"Tablet responsive visual test failed: {e}")
            return {
                'test_name': 'tablet_responsive_visual',
                'status': 'FAIL',
                'error': str(e)
            }
    
    def test_settings_page_visual(self):
        """Test settings page visual regression"""
        logger.info("Testing settings page visual regression...")
        
        try:
            self.driver.get(f"{self.base_url}/settings")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Take settings page screenshot
            current_screenshot = self.take_screenshot("settings_page", "desktop")
            
            # Compare with baseline
            baseline_path = f"{self.baseline_dir}/settings_page_desktop.png"
            if os.path.exists(baseline_path):
                comparison = self.compare_images(current_screenshot, baseline_path)
                return {
                    'test_name': 'settings_page_visual',
                    'status': 'PASS' if comparison['is_similar'] else 'FAIL',
                    'similarity': comparison['similarity'],
                    'threshold': self.threshold,
                    'comparison': comparison
                }
            else:
                # Save as new baseline
                os.rename(current_screenshot, baseline_path)
                return {
                    'test_name': 'settings_page_visual',
                    'status': 'BASELINE_CREATED',
                    'message': 'New baseline created'
                }
                
        except Exception as e:
            logger.error(f"Settings page visual test failed: {e}")
            return {
                'test_name': 'settings_page_visual',
                'status': 'FAIL',
                'error': str(e)
            }
    
    def run_all_visual_tests(self) -> Dict[str, Any]:
        """Run all visual regression tests"""
        logger.info("Starting visual regression tests...")
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'baseline_created': 0,
                'success_rate': 0.0
            }
        }
        
        # List of tests to run
        tests = [
            ('landing_page_visual', self.test_landing_page_visual),
            ('assessment_modal_visual', self.test_assessment_modal_visual),
            ('pricing_section_visual', self.test_pricing_section_visual),
            ('faq_accordion_visual', self.test_faq_accordion_visual),
            ('mobile_responsive_visual', self.test_mobile_responsive_visual),
            ('tablet_responsive_visual', self.test_tablet_responsive_visual),
            ('settings_page_visual', self.test_settings_page_visual)
        ]
        
        # Setup driver
        self.setup_driver()
        
        try:
            for test_name, test_func in tests:
                logger.info(f"Running visual test: {test_name}")
                
                try:
                    result = test_func()
                    test_results['tests'][test_name] = result
                    test_results['summary']['total'] += 1
                    
                    if result.get('status') == 'PASS':
                        test_results['summary']['passed'] += 1
                    elif result.get('status') == 'FAIL':
                        test_results['summary']['failed'] += 1
                    elif result.get('status') == 'BASELINE_CREATED':
                        test_results['summary']['baseline_created'] += 1
                    
                except Exception as e:
                    logger.error(f"Visual test {test_name} failed with exception: {e}")
                    test_results['tests'][test_name] = {
                        'status': 'FAIL',
                        'error': str(e)
                    }
                    test_results['summary']['total'] += 1
                    test_results['summary']['failed'] += 1
                
                # Small delay between tests
                time.sleep(2)
        
        finally:
            # Cleanup
            self.teardown_driver()
        
        # Calculate success rate
        if test_results['summary']['total'] > 0:
            test_results['summary']['success_rate'] = (
                test_results['summary']['passed'] / test_results['summary']['total'] * 100
            )
        
        logger.info(f"Visual regression tests completed - Success rate: {test_results['summary']['success_rate']:.1f}%")
        return test_results
    
    def generate_visual_report(self, results: Dict[str, Any], output_path: str):
        """Generate visual regression test report"""
        report = f"""
# Visual Regression Test Report

**Generated**: {results['timestamp']}
**Success Rate**: {results['summary']['success_rate']:.1f}%

## Summary

- **Total Tests**: {results['summary']['total']}
- **Passed**: {results['summary']['passed']}
- **Failed**: {results['summary']['failed']}
- **Baseline Created**: {results['summary']['baseline_created']}

## Test Results

"""
        
        for test_name, test_result in results['tests'].items():
            status = test_result.get('status', 'UNKNOWN')
            report += f"### {test_name}\n"
            report += f"**Status**: {status}\n"
            
            if 'similarity' in test_result:
                report += f"**Similarity**: {test_result['similarity']:.3f}\n"
                report += f"**Threshold**: {test_result.get('threshold', self.threshold)}\n"
            
            if 'error' in test_result:
                report += f"**Error**: {test_result['error']}\n"
            
            if 'comparison' in test_result and 'diff_image' in test_result['comparison']:
                report += f"**Diff Image**: {test_result['comparison']['diff_image']}\n"
            
            report += "\n"
        
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Visual regression report saved to {output_path}")

def main():
    """Main function for running visual regression tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mingus Visual Regression Tests')
    parser.add_argument('--base-url', default='http://localhost:3000', help='Frontend base URL')
    parser.add_argument('--threshold', type=float, default=0.95, help='Similarity threshold')
    parser.add_argument('--output', help='Output file for test results')
    parser.add_argument('--report', help='Generate HTML report')
    parser.add_argument('--test', help='Run specific test only')
    
    args = parser.parse_args()
    
    config = {
        'base_url': args.base_url,
        'threshold': args.threshold,
        'screenshots_dir': 'visual_test_screenshots',
        'baseline_dir': 'visual_baselines'
    }
    
    # Run tests
    test_suite = VisualRegressionTest(config)
    
    if args.test:
        # Run specific test
        test_method = getattr(test_suite, f"test_{args.test}")
        if test_method:
            test_suite.setup_driver()
            try:
                result = test_method()
                print(json.dumps(result, indent=2))
            finally:
                test_suite.teardown_driver()
        else:
            print(f"Test {args.test} not found")
    else:
        # Run all tests
        results = test_suite.run_all_visual_tests()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Test results saved to {args.output}")
        
        if args.report:
            test_suite.generate_visual_report(results, args.report)
            print(f"Visual report saved to {args.report}")
        
        if not args.output and not args.report:
            print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
