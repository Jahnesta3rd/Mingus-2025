#!/usr/bin/env python3
"""
Mingus Application - User Experience Monitoring System
====================================================

Comprehensive UX monitoring and baseline measurement system
for user interactions, accessibility, and task completion.

Author: Mingus UX Team
Date: January 2025
"""

import time
import json
import sqlite3
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import subprocess
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UXMetric:
    """User experience metric data structure"""
    timestamp: str
    metric_type: str
    metric_name: str
    value: float
    unit: str
    target: float
    status: str  # PASS, WARN, FAIL
    device_type: str
    browser: str
    metadata: Dict[str, Any]

@dataclass
class TaskCompletionMetric:
    """Task completion metric data structure"""
    task_name: str
    completion_time: float
    success: bool
    steps_taken: int
    errors_encountered: int
    device_type: str
    browser: str
    timestamp: str

@dataclass
class AccessibilityMetric:
    """Accessibility metric data structure"""
    test_type: str
    element: str
    issue_type: str
    severity: str
    description: str
    page_url: str
    timestamp: str

class UXMonitor:
    """Main UX monitoring class"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get('database_path', 'ux_metrics.db')
        self.frontend_url = config.get('frontend_url', 'http://localhost:3000')
        self.api_base_url = config.get('api_base_url', 'http://localhost:5000')
        self.selenium_config = config.get('selenium', {})
        self.accessibility_config = config.get('accessibility', {})
        
        # Initialize database
        self.init_database()
        
        # Initialize baselines
        self.baselines = self.load_ux_baselines()
    
    def init_database(self):
        """Initialize UX metrics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create UX metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ux_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                target REAL NOT NULL,
                status TEXT NOT NULL,
                device_type TEXT NOT NULL,
                browser TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create task completion table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_completion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                completion_time REAL NOT NULL,
                success BOOLEAN NOT NULL,
                steps_taken INTEGER NOT NULL,
                errors_encountered INTEGER NOT NULL,
                device_type TEXT NOT NULL,
                browser TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create accessibility metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accessibility_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_type TEXT NOT NULL,
                element TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                page_url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create UX baselines table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ux_baselines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT UNIQUE NOT NULL,
                current_baseline REAL NOT NULL,
                target REAL NOT NULL,
                unit TEXT NOT NULL,
                measurement_count INTEGER DEFAULT 0,
                last_updated TEXT NOT NULL,
                trend TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("UX monitoring database initialized")
    
    def load_ux_baselines(self) -> Dict[str, Dict[str, Any]]:
        """Load UX baselines from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM ux_baselines')
        rows = cursor.fetchall()
        
        baselines = {}
        for row in rows:
            baselines[row[1]] = {
                'current_baseline': row[2],
                'target': row[3],
                'unit': row[4],
                'measurement_count': row[5],
                'last_updated': row[6],
                'trend': row[7],
                'confidence': row[8]
            }
        
        conn.close()
        return baselines
    
    def setup_selenium_driver(self, device_type: str = 'desktop') -> webdriver.Chrome:
        """Setup Selenium WebDriver for testing"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        if device_type == 'mobile':
            chrome_options.add_argument('--window-size=375,667')
            chrome_options.add_experimental_option("mobileEmulation", {
                "deviceMetrics": {"width": 375, "height": 667, "pixelRatio": 2.0},
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            })
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    
    def measure_task_completion_times(self) -> List[TaskCompletionMetric]:
        """Measure task completion times for key user workflows"""
        tasks = []
        
        # Test different device types
        for device_type in ['desktop', 'mobile']:
            try:
                driver = self.setup_selenium_driver(device_type)
                
                # Task 1: Complete Assessment
                task1 = self.measure_assessment_completion(driver, device_type)
                if task1:
                    tasks.append(task1)
                
                # Task 2: Update User Preferences
                task2 = self.measure_preferences_update(driver, device_type)
                if task2:
                    tasks.append(task2)
                
                # Task 3: Navigate to Settings
                task3 = self.measure_settings_navigation(driver, device_type)
                if task3:
                    tasks.append(task3)
                
                # Task 4: View Dashboard
                task4 = self.measure_dashboard_view(driver, device_type)
                if task4:
                    tasks.append(task4)
                
                driver.quit()
                
            except Exception as e:
                logger.error(f"Error measuring tasks for {device_type}: {e}")
        
        return tasks
    
    def measure_assessment_completion(self, driver: webdriver.Chrome, device_type: str) -> Optional[TaskCompletionMetric]:
        """Measure assessment completion task"""
        try:
            start_time = time.time()
            steps = 0
            errors = 0
            
            # Navigate to landing page
            driver.get(self.frontend_url)
            steps += 1
            
            # Click on assessment button
            try:
                assessment_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[aria-label*='Determine Your Replacement Risk Due To AI']"))
                )
                assessment_button.click()
                steps += 1
            except TimeoutException:
                errors += 1
                return None
            
            # Fill out assessment form
            try:
                # Wait for modal to appear
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[role='dialog']"))
                )
                
                # Fill email field
                email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
                email_field.send_keys("test@example.com")
                steps += 1
                
                # Fill first name field
                first_name_field = driver.find_element(By.CSS_SELECTOR, "input[name='firstName']")
                first_name_field.send_keys("Test User")
                steps += 1
                
                # Answer assessment questions
                question_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                for i, input_elem in enumerate(question_inputs[:3]):  # Answer first 3 questions
                    if input_elem.is_displayed():
                        input_elem.click()
                        steps += 1
                        break
                
                # Submit assessment
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_button.click()
                steps += 1
                
            except (TimeoutException, NoSuchElementException) as e:
                errors += 1
                logger.error(f"Error in assessment form: {e}")
            
            end_time = time.time()
            completion_time = end_time - start_time
            
            return TaskCompletionMetric(
                task_name='complete_assessment',
                completion_time=completion_time,
                success=errors == 0,
                steps_taken=steps,
                errors_encountered=errors,
                device_type=device_type,
                browser='chrome',
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error measuring assessment completion: {e}")
            return None
    
    def measure_preferences_update(self, driver: webdriver.Chrome, device_type: str) -> Optional[TaskCompletionMetric]:
        """Measure user preferences update task"""
        try:
            start_time = time.time()
            steps = 0
            errors = 0
            
            # Navigate to settings page
            driver.get(f"{self.frontend_url}/settings")
            steps += 1
            
            # Wait for page to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                steps += 1
            except TimeoutException:
                errors += 1
                return None
            
            # Look for preference form elements
            try:
                form_elements = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
                for element in form_elements[:2]:  # Interact with first 2 form elements
                    if element.is_displayed() and element.is_enabled():
                        if element.tag_name == 'input':
                            if element.get_attribute('type') == 'text':
                                element.clear()
                                element.send_keys("Updated Value")
                            elif element.get_attribute('type') == 'checkbox':
                                element.click()
                        steps += 1
                
                # Look for save button
                save_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button:contains('Save')")
                if save_buttons:
                    save_buttons[0].click()
                    steps += 1
                
            except Exception as e:
                errors += 1
                logger.error(f"Error updating preferences: {e}")
            
            end_time = time.time()
            completion_time = end_time - start_time
            
            return TaskCompletionMetric(
                task_name='update_preferences',
                completion_time=completion_time,
                success=errors == 0,
                steps_taken=steps,
                errors_encountered=errors,
                device_type=device_type,
                browser='chrome',
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error measuring preferences update: {e}")
            return None
    
    def measure_settings_navigation(self, driver: webdriver.Chrome, device_type: str) -> Optional[TaskCompletionMetric]:
        """Measure settings navigation task"""
        try:
            start_time = time.time()
            steps = 0
            errors = 0
            
            # Start from landing page
            driver.get(self.frontend_url)
            steps += 1
            
            # Look for settings link/button
            try:
                settings_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='settings'], button:contains('Settings')")
                if settings_elements:
                    settings_elements[0].click()
                    steps += 1
                else:
                    # Try navigation menu
                    nav_elements = driver.find_elements(By.CSS_SELECTOR, "nav a, .navigation a")
                    for nav_elem in nav_elements:
                        if 'settings' in nav_elem.text.lower():
                            nav_elem.click()
                            steps += 1
                            break
                
                # Wait for settings page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                steps += 1
                
            except TimeoutException:
                errors += 1
            
            end_time = time.time()
            completion_time = end_time - start_time
            
            return TaskCompletionMetric(
                task_name='navigate_to_settings',
                completion_time=completion_time,
                success=errors == 0,
                steps_taken=steps,
                errors_encountered=errors,
                device_type=device_type,
                browser='chrome',
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error measuring settings navigation: {e}")
            return None
    
    def measure_dashboard_view(self, driver: webdriver.Chrome, device_type: str) -> Optional[TaskCompletionMetric]:
        """Measure dashboard view task"""
        try:
            start_time = time.time()
            steps = 0
            errors = 0
            
            # Navigate to dashboard
            driver.get(f"{self.frontend_url}/dashboard")
            steps += 1
            
            # Wait for dashboard to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                steps += 1
                
                # Look for dashboard content
                dashboard_elements = driver.find_elements(By.CSS_SELECTOR, ".dashboard, [data-testid='dashboard'], main")
                if dashboard_elements:
                    steps += 1
                
            except TimeoutException:
                errors += 1
            
            end_time = time.time()
            completion_time = end_time - start_time
            
            return TaskCompletionMetric(
                task_name='view_dashboard',
                completion_time=completion_time,
                success=errors == 0,
                steps_taken=steps,
                errors_encountered=errors,
                device_type=device_type,
                browser='chrome',
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error measuring dashboard view: {e}")
            return None
    
    def measure_interaction_efficiency(self) -> List[UXMetric]:
        """Measure interaction efficiency metrics"""
        metrics = []
        
        try:
            driver = self.setup_selenium_driver('desktop')
            
            # Measure clicks to complete common actions
            actions = [
                {'name': 'start_assessment', 'selector': "[aria-label*='Determine Your Replacement Risk Due To AI']"},
                {'name': 'access_settings', 'selector': "a[href*='settings'], button:contains('Settings')"},
                {'name': 'view_pricing', 'selector': "a[href*='#pricing'], button:contains('Pricing')"},
                {'name': 'toggle_faq', 'selector': "[role='button'][aria-expanded]"}
            ]
            
            for action in actions:
                try:
                    driver.get(self.frontend_url)
                    
                    # Count clicks needed
                    clicks = 0
                    elements = driver.find_elements(By.CSS_SELECTOR, action['selector'])
                    
                    if elements:
                        clicks = 1  # Single click to complete action
                    else:
                        # Try alternative selectors
                        alt_selectors = [
                            f"button:contains('{action['name'].replace('_', ' ').title()}')",
                            f"a:contains('{action['name'].replace('_', ' ').title()}')"
                        ]
                        for selector in alt_selectors:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                clicks = 1
                                break
                    
                    metric = UXMetric(
                        timestamp=datetime.now().isoformat(),
                        metric_type='interaction_efficiency',
                        metric_name=f"{action['name']}_clicks",
                        value=clicks,
                        unit='clicks',
                        target=3.0,  # Target: max 3 clicks
                        status='PASS' if clicks <= 3 else 'FAIL',
                        device_type='desktop',
                        browser='chrome',
                        metadata={'selector': action['selector']}
                    )
                    metrics.append(metric)
                    
                except Exception as e:
                    logger.error(f"Error measuring {action['name']}: {e}")
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"Error in interaction efficiency measurement: {e}")
        
        return metrics
    
    def measure_accessibility_compliance(self) -> List[AccessibilityMetric]:
        """Measure accessibility compliance using automated tools"""
        metrics = []
        
        try:
            # Run axe-core accessibility tests
            driver = self.setup_selenium_driver('desktop')
            
            pages = [
                {'name': 'landing_page', 'url': self.frontend_url},
                {'name': 'settings_page', 'url': f"{self.frontend_url}/settings"},
                {'name': 'dashboard', 'url': f"{self.frontend_url}/dashboard"}
            ]
            
            for page in pages:
                try:
                    driver.get(page['url'])
                    
                    # Inject axe-core script
                    driver.execute_script("""
                        var script = document.createElement('script');
                        script.src = 'https://cdn.jsdelivr.net/npm/axe-core@4.7.0/axe.min.js';
                        document.head.appendChild(script);
                    """)
                    
                    # Wait for axe to load
                    time.sleep(2)
                    
                    # Run accessibility tests
                    results = driver.execute_script("""
                        return new Promise(function(resolve) {
                            if (typeof axe !== 'undefined') {
                                axe.run(function(err, results) {
                                    resolve(results);
                                });
                            } else {
                                resolve({violations: []});
                            }
                        });
                    """)
                    
                    # Process results
                    if results and 'violations' in results:
                        for violation in results['violations']:
                            for node in violation['nodes']:
                                metric = AccessibilityMetric(
                                    test_type='axe_core',
                                    element=node['target'][0] if node['target'] else 'unknown',
                                    issue_type=violation['id'],
                                    severity=violation['impact'],
                                    description=violation['description'],
                                    page_url=page['url'],
                                    timestamp=datetime.now().isoformat()
                                )
                                metrics.append(metric)
                    
                except Exception as e:
                    logger.error(f"Error testing accessibility for {page['name']}: {e}")
            
            driver.quit()
            
        except Exception as e:
            logger.error(f"Error in accessibility measurement: {e}")
        
        return metrics
    
    def measure_device_usage_patterns(self) -> List[UXMetric]:
        """Measure device usage patterns and performance"""
        metrics = []
        
        device_configs = [
            {'type': 'desktop', 'width': 1920, 'height': 1080},
            {'type': 'tablet', 'width': 768, 'height': 1024},
            {'type': 'mobile', 'width': 375, 'height': 667}
        ]
        
        for config in device_configs:
            try:
                driver = self.setup_selenium_driver(config['type'])
                driver.set_window_size(config['width'], config['height'])
                
                # Measure page load time
                start_time = time.time()
                driver.get(self.frontend_url)
                end_time = time.time()
                load_time = (end_time - start_time) * 1000
                
                # Measure viewport performance
                viewport_script = """
                    return {
                        width: window.innerWidth,
                        height: window.innerHeight,
                        devicePixelRatio: window.devicePixelRatio,
                        userAgent: navigator.userAgent
                    };
                """
                viewport_info = driver.execute_script(viewport_script)
                
                # Create performance score (simplified)
                performance_score = max(0, 100 - (load_time / 100))  # Penalize slow loads
                
                metric = UXMetric(
                    timestamp=datetime.now().isoformat(),
                    metric_type='device_performance',
                    metric_name=f"{config['type']}_performance_score",
                    value=performance_score,
                    unit='score',
                    target=85.0,
                    status='PASS' if performance_score >= 85.0 else 'FAIL',
                    device_type=config['type'],
                    browser='chrome',
                    metadata={
                        'load_time': load_time,
                        'viewport': viewport_info,
                        'resolution': f"{config['width']}x{config['height']}"
                    }
                )
                metrics.append(metric)
                
                driver.quit()
                
            except Exception as e:
                logger.error(f"Error measuring {config['type']} performance: {e}")
        
        return metrics
    
    def save_ux_metrics(self, metrics: List[UXMetric]):
        """Save UX metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric in metrics:
            cursor.execute('''
                INSERT INTO ux_metrics 
                (timestamp, metric_type, metric_name, value, unit, target, status, device_type, browser, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.timestamp,
                metric.metric_type,
                metric.metric_name,
                metric.value,
                metric.unit,
                metric.target,
                metric.status,
                metric.device_type,
                metric.browser,
                json.dumps(metric.metadata)
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(metrics)} UX metrics")
    
    def save_task_completion(self, tasks: List[TaskCompletionMetric]):
        """Save task completion metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for task in tasks:
            cursor.execute('''
                INSERT INTO task_completion 
                (task_name, completion_time, success, steps_taken, errors_encountered, device_type, browser, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_name,
                task.completion_time,
                task.success,
                task.steps_taken,
                task.errors_encountered,
                task.device_type,
                task.browser,
                task.timestamp
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(tasks)} task completion metrics")
    
    def save_accessibility_metrics(self, metrics: List[AccessibilityMetric]):
        """Save accessibility metrics to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for metric in metrics:
            cursor.execute('''
                INSERT INTO accessibility_metrics 
                (test_type, element, issue_type, severity, description, page_url, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.test_type,
                metric.element,
                metric.issue_type,
                metric.severity,
                metric.description,
                metric.page_url,
                metric.timestamp
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Saved {len(metrics)} accessibility metrics")
    
    def run_comprehensive_ux_measurement(self) -> Dict[str, Any]:
        """Run comprehensive UX measurement"""
        logger.info("Starting comprehensive UX measurement")
        
        all_metrics = []
        task_metrics = []
        accessibility_metrics = []
        
        # Measure task completion times
        logger.info("Measuring task completion times...")
        task_metrics = self.measure_task_completion_times()
        
        # Measure interaction efficiency
        logger.info("Measuring interaction efficiency...")
        interaction_metrics = self.measure_interaction_efficiency()
        all_metrics.extend(interaction_metrics)
        
        # Measure accessibility compliance
        logger.info("Measuring accessibility compliance...")
        accessibility_metrics = self.measure_accessibility_compliance()
        
        # Measure device usage patterns
        logger.info("Measuring device usage patterns...")
        device_metrics = self.measure_device_usage_patterns()
        all_metrics.extend(device_metrics)
        
        # Save all metrics
        self.save_ux_metrics(all_metrics)
        self.save_task_completion(task_metrics)
        self.save_accessibility_metrics(accessibility_metrics)
        
        # Generate summary
        summary = self.generate_ux_summary(all_metrics, task_metrics, accessibility_metrics)
        
        logger.info("Comprehensive UX measurement completed")
        return summary
    
    def generate_ux_summary(self, metrics: List[UXMetric], tasks: List[TaskCompletionMetric], accessibility: List[AccessibilityMetric]) -> Dict[str, Any]:
        """Generate UX measurement summary"""
        # Calculate task completion rates
        total_tasks = len(tasks)
        successful_tasks = len([t for t in tasks if t.success])
        task_success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate average completion times by task
        task_times = {}
        for task in tasks:
            if task.task_name not in task_times:
                task_times[task.task_name] = []
            task_times[task.task_name].append(task.completion_time)
        
        avg_task_times = {}
        for task_name, times in task_times.items():
            avg_task_times[task_name] = {
                'average': statistics.mean(times),
                'median': statistics.median(times),
                'min': min(times),
                'max': max(times),
                'count': len(times)
            }
        
        # Calculate accessibility compliance
        total_accessibility_issues = len(accessibility)
        critical_issues = len([a for a in accessibility if a.severity == 'critical'])
        serious_issues = len([a for a in accessibility if a.severity == 'serious'])
        moderate_issues = len([a for a in accessibility if a.severity == 'moderate'])
        minor_issues = len([a for a in accessibility if a.severity == 'minor'])
        
        # Calculate interaction efficiency
        interaction_metrics = [m for m in metrics if m.metric_type == 'interaction_efficiency']
        avg_clicks = statistics.mean([m.value for m in interaction_metrics]) if interaction_metrics else 0
        
        # Calculate device performance
        device_metrics = [m for m in metrics if m.metric_type == 'device_performance']
        device_performance = {}
        for metric in device_metrics:
            device_performance[metric.device_type] = {
                'performance_score': metric.value,
                'status': metric.status,
                'metadata': metric.metadata
            }
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'task_completion': {
                'total_tasks': total_tasks,
                'successful_tasks': successful_tasks,
                'success_rate': task_success_rate,
                'average_times': avg_task_times
            },
            'interaction_efficiency': {
                'average_clicks': avg_clicks,
                'target_clicks': 3.0,
                'efficiency_score': max(0, 100 - (avg_clicks * 20))  # Penalize high click counts
            },
            'accessibility': {
                'total_issues': total_accessibility_issues,
                'critical_issues': critical_issues,
                'serious_issues': serious_issues,
                'moderate_issues': moderate_issues,
                'minor_issues': minor_issues,
                'compliance_score': max(0, 100 - (critical_issues * 20) - (serious_issues * 10) - (moderate_issues * 5))
            },
            'device_performance': device_performance,
            'overall_ux_score': self.calculate_overall_ux_score(task_success_rate, avg_clicks, total_accessibility_issues)
        }
        
        return summary
    
    def calculate_overall_ux_score(self, task_success_rate: float, avg_clicks: float, accessibility_issues: int) -> float:
        """Calculate overall UX score"""
        # Task completion weight: 40%
        task_score = task_success_rate * 0.4
        
        # Interaction efficiency weight: 30%
        efficiency_score = max(0, 100 - (avg_clicks * 20)) * 0.3
        
        # Accessibility weight: 30%
        accessibility_score = max(0, 100 - (accessibility_issues * 5)) * 0.3
        
        return task_score + efficiency_score + accessibility_score
    
    def export_ux_report(self, output_path: str):
        """Export UX report to file"""
        # Get recent metrics
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent UX metrics
        cursor.execute('''
            SELECT timestamp, metric_type, metric_name, value, unit, target, status, device_type, browser, metadata
            FROM ux_metrics 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        ''')
        
        recent_metrics = []
        for row in cursor.fetchall():
            recent_metrics.append({
                'timestamp': row[0],
                'metric_type': row[1],
                'metric_name': row[2],
                'value': row[3],
                'unit': row[4],
                'target': row[5],
                'status': row[6],
                'device_type': row[7],
                'browser': row[8],
                'metadata': json.loads(row[9]) if row[9] else {}
            })
        
        # Get recent task completion
        cursor.execute('''
            SELECT task_name, completion_time, success, steps_taken, errors_encountered, device_type, browser, timestamp
            FROM task_completion 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        ''')
        
        recent_tasks = []
        for row in cursor.fetchall():
            recent_tasks.append({
                'task_name': row[0],
                'completion_time': row[1],
                'success': row[2],
                'steps_taken': row[3],
                'errors_encountered': row[4],
                'device_type': row[5],
                'browser': row[6],
                'timestamp': row[7]
            })
        
        # Get recent accessibility issues
        cursor.execute('''
            SELECT test_type, element, issue_type, severity, description, page_url, timestamp
            FROM accessibility_metrics 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        ''')
        
        recent_accessibility = []
        for row in cursor.fetchall():
            recent_accessibility.append({
                'test_type': row[0],
                'element': row[1],
                'issue_type': row[2],
                'severity': row[3],
                'description': row[4],
                'page_url': row[5],
                'timestamp': row[6]
            })
        
        conn.close()
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.generate_ux_summary(
                [UXMetric(**m) for m in recent_metrics],
                [TaskCompletionMetric(**t) for t in recent_tasks],
                [AccessibilityMetric(**a) for a in recent_accessibility]
            ),
            'recent_metrics': recent_metrics,
            'recent_tasks': recent_tasks,
            'recent_accessibility': recent_accessibility,
            'baselines': self.baselines
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"UX report exported to {output_path}")

def main():
    """Main function for running UX monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mingus UX Monitor')
    parser.add_argument('--config', default='ux_monitoring_config.json', help='Configuration file path')
    parser.add_argument('--export', help='Export UX report to file')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=1800, help='Monitoring interval in seconds')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
    else:
        # Default configuration
        config = {
            'database_path': 'ux_metrics.db',
            'frontend_url': 'http://localhost:3000',
            'api_base_url': 'http://localhost:5000',
            'selenium': {
                'headless': True,
                'timeout': 10
            },
            'accessibility': {
                'axe_core_url': 'https://cdn.jsdelivr.net/npm/axe-core@4.7.0/axe.min.js'
            }
        }
    
    # Initialize monitor
    monitor = UXMonitor(config)
    
    if args.continuous:
        logger.info(f"Starting continuous UX monitoring (interval: {args.interval}s)")
        while True:
            try:
                summary = monitor.run_comprehensive_ux_measurement()
                logger.info(f"UX monitoring cycle completed - Overall score: {summary['overall_ux_score']:.1f}")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("UX monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"UX monitoring error: {e}")
                time.sleep(300)  # Wait before retrying
    else:
        # Run single measurement
        summary = monitor.run_comprehensive_ux_measurement()
        print(json.dumps(summary, indent=2))
        
        if args.export:
            monitor.export_ux_report(args.export)

if __name__ == "__main__":
    main()
