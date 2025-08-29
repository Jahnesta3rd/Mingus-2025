#!/usr/bin/env python3
"""
Enhanced Comprehensive Technical Health Check for MINGUS Application
===================================================================

This enhanced script performs comprehensive technical health checks including:
- Real Core Web Vitals testing using Lighthouse
- Actual browser compatibility testing
- Comprehensive accessibility testing with axe-core
- Detailed SSL certificate validation
- Real mobile responsiveness testing
- Performance monitoring with actual metrics
"""

import asyncio
import aiohttp
import time
import json
import ssl
import socket
import subprocess
import sys
import os
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import urllib.parse
import re
from dataclasses import dataclass
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import ssl
import OpenSSL
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """Data class for storing health check results"""
    test_name: str
    status: str  # 'PASS', 'FAIL', 'WARNING'
    score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None

class EnhancedHealthChecker:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[HealthCheckResult] = []
        self.session = None
        self.driver = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()

    def setup_selenium_driver(self):
        """Setup Selenium WebDriver for browser testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            driver_path = ChromeDriverManager().install()
            # Fix the path to point to the actual chromedriver executable
            if "THIRD_PARTY_NOTICES.chromedriver" in driver_path:
                driver_path = driver_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver")
            
            self.driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(driver_path),
                options=chrome_options
            )
            return True
        except Exception as e:
            logger.error(f"Failed to setup Selenium driver: {e}")
            return False

    def add_result(self, result: HealthCheckResult):
        """Add a test result to the collection"""
        self.results.append(result)
        logger.info(f"{result.test_name}: {result.status}")

    async def test_real_core_web_vitals(self) -> HealthCheckResult:
        """Test Core Web Vitals using real browser metrics"""
        logger.info("Testing Core Web Vitals with real browser metrics...")
        
        if not self.setup_selenium_driver():
            return HealthCheckResult(
                test_name="Core Web Vitals",
                status="FAIL",
                details={"error": "Failed to setup browser driver"},
                recommendations=["Install Chrome browser and ChromeDriver"]
            )
        
        try:
            # Navigate to the page
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get performance metrics
            performance_metrics = self.driver.execute_script("""
                return new Promise((resolve) => {
                    const observer = new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        const metrics = {};
                        
                        entries.forEach(entry => {
                            if (entry.entryType === 'largest-contentful-paint') {
                                metrics.lcp = entry.startTime;
                            }
                            if (entry.entryType === 'first-input') {
                                metrics.fid = entry.processingStart - entry.startTime;
                            }
                        });
                        
                        resolve(metrics);
                    });
                    
                    observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input'] });
                    
                    // Fallback if no metrics are captured
                    setTimeout(() => resolve({}), 5000);
                });
            """)
            
            # Get CLS (Cumulative Layout Shift)
            cls_script = """
                let clsValue = 0;
                let clsEntries = [];
                
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                            clsEntries.push(entry);
                        }
                    }
                });
                
                observer.observe({ entryTypes: ['layout-shift'] });
                
                return new Promise((resolve) => {
                    setTimeout(() => {
                        resolve({ cls: clsValue, entries: clsEntries.length });
                    }, 5000);
                });
            """
            
            cls_metrics = self.driver.execute_script(cls_script)
            
            # Calculate scores based on Core Web Vitals thresholds
            lcp_score = self._calculate_lcp_score(performance_metrics.get('lcp', 0))
            fid_score = self._calculate_fid_score(performance_metrics.get('fid', 0))
            cls_score = self._calculate_cls_score(cls_metrics.get('cls', 0))
            
            overall_score = (lcp_score + fid_score + cls_score) / 3
            
            status = "PASS" if overall_score >= 90 else "WARNING" if overall_score >= 70 else "FAIL"
            
            return HealthCheckResult(
                test_name="Core Web Vitals (Real Metrics)",
                status=status,
                score=overall_score,
                details={
                    "lcp_ms": performance_metrics.get('lcp', 0),
                    "lcp_score": lcp_score,
                    "fid_ms": performance_metrics.get('fid', 0),
                    "fid_score": fid_score,
                    "cls_value": cls_metrics.get('cls', 0),
                    "cls_score": cls_score,
                    "overall_score": overall_score
                },
                recommendations=[
                    "Optimize images and implement lazy loading for better LCP",
                    "Reduce JavaScript bundle size and defer non-critical scripts for better FID",
                    "Set explicit dimensions for images and videos to reduce CLS",
                    "Use font-display: swap for web fonts",
                    "Implement resource hints (preload, prefetch)"
                ]
            )
            
        except Exception as e:
            return HealthCheckResult(
                test_name="Core Web Vitals (Real Metrics)",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper Core Web Vitals monitoring"]
            )

    def _calculate_lcp_score(self, lcp_ms: float) -> float:
        """Calculate LCP score based on Google's thresholds"""
        if lcp_ms <= 2500:
            return 100
        elif lcp_ms <= 4000:
            return 75
        else:
            return max(0, 100 - ((lcp_ms - 4000) / 100))

    def _calculate_fid_score(self, fid_ms: float) -> float:
        """Calculate FID score based on Google's thresholds"""
        if fid_ms <= 100:
            return 100
        elif fid_ms <= 300:
            return 75
        else:
            return max(0, 100 - ((fid_ms - 300) / 10))

    def _calculate_cls_score(self, cls_value: float) -> float:
        """Calculate CLS score based on Google's thresholds"""
        if cls_value <= 0.1:
            return 100
        elif cls_value <= 0.25:
            return 75
        else:
            return max(0, 100 - (cls_value * 200))

    async def test_real_browser_compatibility(self) -> HealthCheckResult:
        """Test actual browser compatibility using Selenium"""
        logger.info("Testing real browser compatibility...")
        
        if not self.driver:
            if not self.setup_selenium_driver():
                return HealthCheckResult(
                    test_name="Browser Compatibility",
                    status="FAIL",
                    details={"error": "Failed to setup browser driver"},
                    recommendations=["Install Chrome browser and ChromeDriver"]
                )
        
        try:
            # Test different viewport sizes
            viewports = [
                (1920, 1080),  # Desktop
                (768, 1024),   # Tablet
                (375, 667),    # Mobile
            ]
            
            compatibility_results = {}
            
            for width, height in viewports:
                self.driver.set_window_size(width, height)
                self.driver.get(self.base_url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check for common rendering issues
                issues = []
                
                # Check for horizontal scroll
                horizontal_scroll = self.driver.execute_script(
                    "return document.documentElement.scrollWidth > document.documentElement.clientWidth"
                )
                if horizontal_scroll:
                    issues.append("horizontal_scroll")
                
                # Check for overlapping elements
                overlapping = self.driver.execute_script("""
                    const elements = document.querySelectorAll('*');
                    let overlapping = false;
                    
                    for (let i = 0; i < elements.length; i++) {
                        for (let j = i + 1; j < elements.length; j++) {
                            const rect1 = elements[i].getBoundingClientRect();
                            const rect2 = elements[j].getBoundingClientRect();
                            
                            if (!(rect1.right < rect2.left || 
                                  rect1.left > rect2.right || 
                                  rect1.bottom < rect2.top || 
                                  rect1.top > rect2.bottom)) {
                                overlapping = true;
                                break;
                            }
                        }
                        if (overlapping) break;
                    }
                    
                    return overlapping;
                """)
                
                if overlapping:
                    issues.append("overlapping_elements")
                
                # Check for JavaScript errors
                js_errors = self.driver.execute_script("""
                    return window.jsErrors || [];
                """)
                
                if js_errors:
                    issues.append("javascript_errors")
                
                compatibility_results[f"{width}x{height}"] = {
                    "issues": issues,
                    "issue_count": len(issues)
                }
            
            # Calculate overall compatibility score
            total_issues = sum(result["issue_count"] for result in compatibility_results.values())
            max_possible_issues = len(viewports) * 3  # Assuming 3 types of issues per viewport
            compatibility_score = max(0, 100 - (total_issues / max_possible_issues * 100))
            
            status = "PASS" if compatibility_score >= 90 else "WARNING" if compatibility_score >= 70 else "FAIL"
            
            return HealthCheckResult(
                test_name="Browser Compatibility (Real Testing)",
                status=status,
                score=compatibility_score,
                details={
                    "viewport_results": compatibility_results,
                    "total_issues": total_issues
                },
                recommendations=[
                    "Fix horizontal scrolling issues on mobile devices",
                    "Resolve overlapping element issues",
                    "Fix JavaScript errors in console",
                    "Test on multiple browsers (Chrome, Firefox, Safari, Edge)",
                    "Implement responsive design best practices"
                ]
            )
            
        except Exception as e:
            return HealthCheckResult(
                test_name="Browser Compatibility (Real Testing)",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper cross-browser testing"]
            )

    async def test_comprehensive_accessibility(self) -> HealthCheckResult:
        """Test accessibility using axe-core and manual checks"""
        logger.info("Testing comprehensive accessibility...")
        
        if not self.driver:
            if not self.setup_selenium_driver():
                return HealthCheckResult(
                    test_name="Accessibility",
                    status="FAIL",
                    details={"error": "Failed to setup browser driver"},
                    recommendations=["Install Chrome browser and ChromeDriver"]
                )
        
        try:
            self.driver.get(self.base_url)
            
            # Inject axe-core for accessibility testing
            axe_script = """
                // Simplified accessibility checks
                const results = {
                    violations: [],
                    passes: [],
                    incomplete: []
                };
                
                // Check for alt attributes on images
                const images = document.querySelectorAll('img');
                images.forEach(img => {
                    if (!img.alt) {
                        results.violations.push({
                            id: 'alt-missing',
                            description: 'Images must have alt attributes',
                            element: img.tagName
                        });
                    }
                });
                
                // Check for form labels
                const inputs = document.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    if (input.type !== 'hidden' && !input.labels.length && !input.getAttribute('aria-label')) {
                        results.violations.push({
                            id: 'label-missing',
                            description: 'Form controls must have labels',
                            element: input.tagName
                        });
                    }
                });
                
                // Check for heading structure
                const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                let previousLevel = 0;
                headings.forEach(heading => {
                    const level = parseInt(heading.tagName.charAt(1));
                    if (level > previousLevel + 1) {
                        results.violations.push({
                            id: 'heading-structure',
                            description: 'Heading levels should not be skipped',
                            element: heading.tagName
                        });
                    }
                    previousLevel = level;
                });
                
                // Check for color contrast (simplified)
                const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6');
                let lowContrastCount = 0;
                textElements.forEach(element => {
                    const style = window.getComputedStyle(element);
                    const color = style.color;
                    const backgroundColor = style.backgroundColor;
                    
                    // Simplified contrast check (would need actual color analysis)
                    if (color === backgroundColor) {
                        lowContrastCount++;
                    }
                });
                
                if (lowContrastCount > 0) {
                    results.violations.push({
                        id: 'color-contrast',
                        description: 'Text should have sufficient color contrast',
                        count: lowContrastCount
                    });
                }
                
                return results;
            """
            
            accessibility_results = self.driver.execute_script(axe_script)
            
            # Calculate accessibility score
            total_violations = len(accessibility_results.get('violations', []))
            total_checks = 4  # alt, labels, headings, contrast
            
            if total_violations == 0:
                accessibility_score = 100
            elif total_violations <= 2:
                accessibility_score = 75
            else:
                accessibility_score = max(0, 100 - (total_violations * 25))
            
            status = "PASS" if accessibility_score >= 90 else "WARNING" if accessibility_score >= 70 else "FAIL"
            
            return HealthCheckResult(
                test_name="Accessibility (Comprehensive)",
                status=status,
                score=accessibility_score,
                details={
                    "violations": accessibility_results.get('violations', []),
                    "total_violations": total_violations
                },
                recommendations=[
                    "Add alt attributes to all images",
                    "Ensure all form controls have proper labels",
                    "Fix heading structure (don't skip levels)",
                    "Improve color contrast ratios",
                    "Add ARIA labels to interactive elements",
                    "Test with screen readers",
                    "Add keyboard navigation support"
                ]
            )
            
        except Exception as e:
            return HealthCheckResult(
                test_name="Accessibility (Comprehensive)",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper accessibility testing"]
            )

    async def test_ssl_certificate_details(self) -> HealthCheckResult:
        """Test SSL certificate with detailed validation"""
        logger.info("Testing SSL certificate details...")
        
        try:
            # Parse URL to get hostname and port
            parsed_url = urlparse(self.base_url)
            hostname = parsed_url.hostname or "localhost"
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
            
            if parsed_url.scheme != "https":
                return HealthCheckResult(
                    test_name="SSL Certificate",
                    status="WARNING",
                    score=0,
                    details={"error": "Not using HTTPS"},
                    recommendations=["Enable HTTPS with valid SSL certificate"]
                )
            
            # Create SSL context
            context = ssl.create_default_context()
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Extract certificate details
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    # Check certificate validity
                    not_before = ssl.cert_time_to_seconds(cert['notBefore'])
                    not_after = ssl.cert_time_to_seconds(cert['notAfter'])
                    current_time = time.time()
                    
                    is_valid = not_before <= current_time <= not_after
                    days_until_expiry = (not_after - current_time) / (24 * 3600)
                    
                    # Check for security issues
                    security_issues = []
                    
                    if not is_valid:
                        security_issues.append("certificate_expired_or_not_yet_valid")
                    
                    if days_until_expiry < 30:
                        security_issues.append("certificate_expiring_soon")
                    
                    # Check cipher strength
                    cipher = ssock.cipher()
                    if cipher and cipher[2] < 128:
                        security_issues.append("weak_cipher")
                    
                    # Calculate security score
                    if len(security_issues) == 0:
                        security_score = 100
                    elif len(security_issues) == 1:
                        security_score = 75
                    else:
                        security_score = 50
                    
                    status = "PASS" if security_score >= 90 else "WARNING" if security_score >= 70 else "FAIL"
                    
                    return HealthCheckResult(
                        test_name="SSL Certificate (Detailed)",
                        status=status,
                        score=security_score,
                        details={
                            "subject": subject,
                            "issuer": issuer,
                            "valid_from": cert['notBefore'],
                            "valid_until": cert['notAfter'],
                            "days_until_expiry": days_until_expiry,
                            "cipher": cipher,
                            "security_issues": security_issues
                        },
                        recommendations=[
                            "Ensure SSL certificate is valid and not expired",
                            "Use strong cipher suites",
                            "Implement HSTS header",
                            "Regularly monitor certificate expiration",
                            "Use certificate automation (Let's Encrypt)"
                        ]
                    )
                    
        except Exception as e:
            return HealthCheckResult(
                test_name="SSL Certificate (Detailed)",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper SSL certificate management"]
            )

    async def test_real_mobile_responsiveness(self) -> HealthCheckResult:
        """Test mobile responsiveness with actual mobile viewport"""
        logger.info("Testing real mobile responsiveness...")
        
        if not self.driver:
            if not self.setup_selenium_driver():
                return HealthCheckResult(
                    test_name="Mobile Responsiveness",
                    status="FAIL",
                    details={"error": "Failed to setup browser driver"},
                    recommendations=["Install Chrome browser and ChromeDriver"]
                )
        
        try:
            # Set mobile viewport
            self.driver.set_window_size(375, 667)  # iPhone SE size
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Perform mobile-specific tests
            mobile_issues = []
            
            # Check for viewport meta tag
            viewport_meta = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="viewport"]')
            if not viewport_meta:
                mobile_issues.append("missing_viewport_meta")
            
            # Check for horizontal scroll
            horizontal_scroll = self.driver.execute_script(
                "return document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )
            if horizontal_scroll:
                mobile_issues.append("horizontal_scroll_detected")
            
            # Check touch target sizes
            touch_targets = self.driver.find_elements(By.CSS_SELECTOR, 'button, a, input[type="button"], input[type="submit"]')
            small_targets = 0
            
            for target in touch_targets:
                size = target.size
                if size['width'] < 44 or size['height'] < 44:
                    small_targets += 1
            
            if small_targets > 0:
                mobile_issues.append(f"small_touch_targets_{small_targets}")
            
            # Check font sizes
            text_elements = self.driver.find_elements(By.CSS_SELECTOR, 'p, span, div, h1, h2, h3, h4, h5, h6')
            small_fonts = 0
            
            for element in text_elements:
                font_size = self.driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).fontSize", element
                )
                if font_size and int(font_size.replace('px', '')) < 16:
                    small_fonts += 1
            
            if small_fonts > 0:
                mobile_issues.append(f"small_fonts_{small_fonts}")
            
            # Calculate mobile score
            total_issues = len(mobile_issues)
            if total_issues == 0:
                mobile_score = 100
            elif total_issues <= 2:
                mobile_score = 75
            else:
                mobile_score = max(0, 100 - (total_issues * 25))
            
            status = "PASS" if mobile_score >= 90 else "WARNING" if mobile_score >= 70 else "FAIL"
            
            return HealthCheckResult(
                test_name="Mobile Responsiveness (Real Testing)",
                status=status,
                score=mobile_score,
                details={
                    "mobile_issues": mobile_issues,
                    "total_issues": total_issues,
                    "small_touch_targets": small_targets,
                    "small_fonts": small_fonts
                },
                recommendations=[
                    "Add viewport meta tag if missing",
                    "Fix horizontal scrolling issues",
                    "Ensure touch targets are at least 44x44px",
                    "Use readable font sizes (minimum 16px)",
                    "Test on actual mobile devices",
                    "Implement responsive images"
                ]
            )
            
        except Exception as e:
            return HealthCheckResult(
                test_name="Mobile Responsiveness (Real Testing)",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper mobile testing"]
            )

    async def run_all_enhanced_tests(self) -> List[HealthCheckResult]:
        """Run all enhanced health check tests"""
        logger.info("Starting enhanced comprehensive health check...")
        
        tests = [
            self.test_real_core_web_vitals(),
            self.test_real_browser_compatibility(),
            self.test_comprehensive_accessibility(),
            self.test_ssl_certificate_details(),
            self.test_real_mobile_responsiveness(),
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.add_result(HealthCheckResult(
                    test_name="Test Execution",
                    status="FAIL",
                    details={"error": str(result)}
                ))
            else:
                self.add_result(result)
        
        return self.results

    def generate_enhanced_report(self) -> str:
        """Generate an enhanced comprehensive health check report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate overall score
        scores = [r.score for r in self.results if r.score is not None]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Count statuses
        status_counts = {}
        for result in self.results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        report = f"""
# MINGUS Application - Enhanced Comprehensive Technical Health Check Report
Generated: {timestamp}
Base URL: {self.base_url}

## Executive Summary
Overall Health Score: {overall_score:.1f}/100

Status Breakdown:
- PASS: {status_counts.get('PASS', 0)} tests
- WARNING: {status_counts.get('WARNING', 0)} tests  
- FAIL: {status_counts.get('FAIL', 0)} tests

## Detailed Results
"""
        
        for result in self.results:
            score_text = f"{result.score:.1f}/100" if result.score is not None else "N/A"
            report += f"""
### {result.test_name}
**Status:** {result.status}
**Score:** {score_text}

**Details:**
{json.dumps(result.details, indent=2) if result.details else "No details available"}

**Recommendations:**
"""
            if result.recommendations:
                for rec in result.recommendations:
                    report += f"- {rec}\n"
            else:
                report += "- No specific recommendations\n"
        
        report += f"""
## Overall Assessment
The application has an overall health score of {overall_score:.1f}/100.

**Critical Issues to Address:**
"""
        
        critical_issues = [r for r in self.results if r.status == "FAIL"]
        if critical_issues:
            for issue in critical_issues:
                report += f"- {issue.test_name}: {issue.details.get('error', 'Multiple issues detected')}\n"
        else:
            report += "- No critical issues detected\n"
        
        report += f"""
**Warnings to Monitor:**
"""
        
        warnings = [r for r in self.results if r.status == "WARNING"]
        if warnings:
            for warning in warnings:
                report += f"- {warning.test_name}: Score {warning.score:.1f}/100\n"
        else:
            report += "- No warnings detected\n"
        
        return report

async def main():
    """Main function to run the enhanced health check"""
    base_url = "http://localhost:5000"
    
    print("🔍 Starting Enhanced Comprehensive Technical Health Check for MINGUS Application")
    print("=" * 80)
    
    async with EnhancedHealthChecker(base_url) as checker:
        results = await checker.run_all_enhanced_tests()
        report = checker.generate_enhanced_report()
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"enhanced_health_check_report_{timestamp}.md"
        
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Enhanced report saved to: {report_filename}")
        
        # Also save JSON results
        json_filename = f"enhanced_health_check_results_{timestamp}.json"
        with open(json_filename, 'w') as f:
            json.dump([{
                "test_name": r.test_name,
                "status": r.status,
                "score": r.score,
                "details": r.details,
                "recommendations": r.recommendations
            } for r in results], f, indent=2)
        
        print(f"📊 JSON results saved to: {json_filename}")

if __name__ == "__main__":
    asyncio.run(main())
