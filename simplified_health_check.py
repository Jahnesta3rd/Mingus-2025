#!/usr/bin/env python3
"""
Simplified Comprehensive Technical Health Check for MINGUS Application
====================================================================

This simplified script performs key technical health checks including:
- Page load speed testing
- Basic Core Web Vitals simulation
- Cross-browser compatibility analysis
- Accessibility compliance checks
- Security headers validation
- Mobile-friendliness assessment
- JavaScript and CSS error detection
"""

import asyncio
import aiohttp
import time
import json
import ssl
import socket
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import urllib.parse
import re
from dataclasses import dataclass
import logging

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

class SimplifiedHealthChecker:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[HealthCheckResult] = []
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def add_result(self, result: HealthCheckResult):
        """Add a test result to the collection"""
        self.results.append(result)
        logger.info(f"{result.test_name}: {result.status}")

    async def test_page_load_speed(self) -> HealthCheckResult:
        """Test page load speed across different simulated connections"""
        logger.info("Testing page load speed...")
        
        try:
            start_time = time.time()
            async with self.session.get(f"{self.base_url}/landing.html", timeout=30) as response:
                content = await response.read()
                load_time = time.time() - start_time
                
                content_size_mb = len(content) / (1024 * 1024)
                
                # Calculate score based on load time and content size
                if load_time < 1.0 and content_size_mb < 1.0:
                    score = 100
                    status = "PASS"
                elif load_time < 2.0 and content_size_mb < 2.0:
                    score = 80
                    status = "WARNING"
                else:
                    score = max(0, 100 - (load_time * 20))
                    status = "FAIL"
                
                return HealthCheckResult(
                    test_name="Page Load Speed",
                    status=status,
                    score=score,
                    details={
                        "load_time_seconds": load_time,
                        "content_size_mb": content_size_mb,
                        "status_code": response.status
                    },
                    recommendations=[
                        "Optimize images and use WebP format",
                        "Implement lazy loading for images",
                        "Minify CSS, JavaScript, and HTML",
                        "Enable GZIP compression",
                        "Use CDN for static assets"
                    ]
                )
                
        except Exception as e:
            return HealthCheckResult(
                test_name="Page Load Speed",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Check server connectivity and configuration"]
            )

    async def test_core_web_vitals_simulation(self) -> HealthCheckResult:
        """Simulate Core Web Vitals testing based on page analysis"""
        logger.info("Testing Core Web Vitals simulation...")
        
        try:
            async with self.session.get(f"{self.base_url}/landing.html") as response:
                html_content = await response.text()
                
                # Analyze page for Core Web Vitals indicators
                analysis = {
                    "large_images": len(re.findall(r'<img[^>]*>', html_content)),
                    "external_resources": len(re.findall(r'https?://[^\s"\']+', html_content)),
                    "inline_styles": len(re.findall(r'<style[^>]*>', html_content)),
                    "external_scripts": len(re.findall(r'<script[^>]*src=', html_content)),
                    "font_imports": len(re.findall(r'@import.*font', html_content, re.IGNORECASE)),
                }
                
                # Calculate simulated scores
                lcp_score = max(0, 100 - (analysis["large_images"] * 10))
                fid_score = max(0, 100 - (analysis["external_scripts"] * 15))
                cls_score = max(0, 100 - (analysis["inline_styles"] * 5))
                
                overall_score = (lcp_score + fid_score + cls_score) / 3
                
                status = "PASS" if overall_score >= 90 else "WARNING" if overall_score >= 70 else "FAIL"
                
                return HealthCheckResult(
                    test_name="Core Web Vitals (Simulated)",
                    status=status,
                    score=overall_score,
                    details={
                        "analysis": analysis,
                        "lcp_score": lcp_score,
                        "fid_score": fid_score,
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
                test_name="Core Web Vitals (Simulated)",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper Core Web Vitals monitoring"]
            )

    async def test_cross_browser_compatibility(self) -> HealthCheckResult:
        """Test cross-browser compatibility through code analysis"""
        logger.info("Testing cross-browser compatibility...")
        
        try:
            async with self.session.get(f"{self.base_url}/landing.html") as response:
                html_content = await response.text()
                
                # Check for modern CSS features that might not be supported
                css_features = {
                    "css_grid": "display: grid" in html_content,
                    "css_flexbox": "display: flex" in html_content,
                    "css_variables": "var(--" in html_content,
                    "css_custom_properties": "var(--" in html_content,
                    "css_animations": "@keyframes" in html_content,
                }
                
                # Check for modern JavaScript features
                js_features = {
                    "es6_modules": "import " in html_content or "export " in html_content,
                    "async_await": "async" in html_content and "await" in html_content,
                    "arrow_functions": "=>" in html_content,
                    "template_literals": "`" in html_content and "${" in html_content,
                }
                
                # Calculate compatibility score
                modern_features = sum(css_features.values()) + sum(js_features.values())
                total_features = len(css_features) + len(js_features)
                compatibility_score = max(0, 100 - (modern_features * 10))
                
                status = "PASS" if compatibility_score >= 80 else "WARNING"
                
                return HealthCheckResult(
                    test_name="Cross-Browser Compatibility",
                    status=status,
                    score=compatibility_score,
                    details={
                        "css_features": css_features,
                        "js_features": js_features,
                        "modern_features_count": modern_features,
                        "compatibility_score": compatibility_score
                    },
                    recommendations=[
                        "Add polyfills for modern JavaScript features",
                        "Use CSS fallbacks for modern CSS features",
                        "Test on actual browsers: Chrome, Firefox, Safari, Edge",
                        "Consider using Babel for JavaScript transpilation",
                        "Use feature detection for progressive enhancement"
                    ]
                )
                
        except Exception as e:
            return HealthCheckResult(
                test_name="Cross-Browser Compatibility",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper cross-browser testing"]
            )

    async def test_accessibility_compliance(self) -> HealthCheckResult:
        """Test accessibility compliance through code analysis"""
        logger.info("Testing accessibility compliance...")
        
        try:
            async with self.session.get(f"{self.base_url}/landing.html") as response:
                html_content = await response.text()
                
                # Basic accessibility checks
                accessibility_checks = {
                    "has_lang_attribute": 'lang="' in html_content,
                    "has_title": "<title>" in html_content,
                    "has_meta_description": 'name="description"' in html_content,
                    "has_alt_attributes": 'alt="' in html_content,
                    "has_aria_labels": 'aria-label=' in html_content or 'aria-labelledby=' in html_content,
                    "has_semantic_html": any(tag in html_content for tag in ["<nav>", "<main>", "<section>", "<article>", "<header>", "<footer>"]),
                    "has_skip_links": "skip" in html_content.lower() or "skip to main" in html_content.lower(),
                    "has_form_labels": 'for=' in html_content and 'id=' in html_content,
                    "has_heading_structure": any(tag in html_content for tag in ["<h1>", "<h2>", "<h3>", "<h4>", "<h5>", "<h6>"]),
                }
                
                passed_checks = sum(accessibility_checks.values())
                total_checks = len(accessibility_checks)
                accessibility_score = (passed_checks / total_checks) * 100
                
                status = "PASS" if accessibility_score >= 90 else "WARNING" if accessibility_score >= 70 else "FAIL"
                
                return HealthCheckResult(
                    test_name="Accessibility Compliance",
                    status=status,
                    score=accessibility_score,
                    details={
                        "accessibility_checks": accessibility_checks,
                        "passed_checks": passed_checks,
                        "total_checks": total_checks,
                        "failed_checks": [k for k, v in accessibility_checks.items() if not v]
                    },
                    recommendations=[
                        "Add lang attribute to HTML tag",
                        "Add descriptive title and meta description",
                        "Add alt attributes to all images",
                        "Add proper ARIA labels to interactive elements",
                        "Use semantic HTML elements",
                        "Add skip navigation links",
                        "Ensure proper form labels",
                        "Maintain proper heading hierarchy",
                        "Test with screen readers",
                        "Add keyboard navigation support"
                    ]
                )
                
        except Exception as e:
            return HealthCheckResult(
                test_name="Accessibility Compliance",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper accessibility testing"]
            )

    async def test_security_headers(self) -> HealthCheckResult:
        """Test security headers and basic security measures"""
        logger.info("Testing security headers...")
        
        try:
            async with self.session.get(f"{self.base_url}/landing.html") as response:
                headers = response.headers
                
                # Check security headers
                security_headers = {
                    "content_security_policy": "Content-Security-Policy" in headers,
                    "x_frame_options": "X-Frame-Options" in headers,
                    "x_content_type_options": "X-Content-Type-Options" in headers,
                    "x_xss_protection": "X-XSS-Protection" in headers,
                    "strict_transport_security": "Strict-Transport-Security" in headers,
                    "referrer_policy": "Referrer-Policy" in headers,
                    "permissions_policy": "Permissions-Policy" in headers,
                }
                
                # Check for HTTPS
                is_https = "https://" in self.base_url
                
                passed_headers = sum(security_headers.values())
                total_headers = len(security_headers)
                security_score = (passed_headers / total_headers) * 100
                
                if not is_https:
                    security_score = max(0, security_score - 30)
                
                status = "PASS" if security_score >= 80 else "WARNING" if security_score >= 60 else "FAIL"
                
                return HealthCheckResult(
                    test_name="Security Headers",
                    status=status,
                    score=security_score,
                    details={
                        "security_headers": security_headers,
                        "is_https": is_https,
                        "passed_headers": passed_headers,
                        "total_headers": total_headers,
                        "missing_headers": [k for k, v in security_headers.items() if not v]
                    },
                    recommendations=[
                        "Enable HTTPS with valid SSL certificate",
                        "Add Content Security Policy header",
                        "Add X-Frame-Options header",
                        "Add X-Content-Type-Options header",
                        "Add Strict-Transport-Security header",
                        "Configure proper Referrer-Policy",
                        "Add Permissions-Policy header",
                        "Implement security headers in web server configuration"
                    ]
                )
                
        except Exception as e:
            return HealthCheckResult(
                test_name="Security Headers",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper security headers"]
            )

    async def test_mobile_friendliness(self) -> HealthCheckResult:
        """Test mobile-friendliness through code analysis"""
        logger.info("Testing mobile-friendliness...")
        
        try:
            async with self.session.get(f"{self.base_url}/landing.html") as response:
                html_content = await response.text()
                
                # Mobile-friendliness checks
                mobile_checks = {
                    "has_viewport_meta": 'name="viewport"' in html_content,
                    "has_responsive_design": "media=" in html_content and "max-width" in html_content,
                    "has_touch_targets": "min-height: 44px" in html_content or "min-width: 44px" in html_content,
                    "has_readable_font_size": "font-size: 16px" in html_content or "font-size: 1rem" in html_content,
                    "has_no_horizontal_scroll": "overflow-x: hidden" in html_content,
                    "has_mobile_optimized_images": "srcset=" in html_content or "sizes=" in html_content,
                    "has_touch_friendly_buttons": "padding: 10px" in html_content or "min-height: 44px" in html_content,
                }
                
                passed_checks = sum(mobile_checks.values())
                total_checks = len(mobile_checks)
                mobile_score = (passed_checks / total_checks) * 100
                
                status = "PASS" if mobile_score >= 80 else "WARNING" if mobile_score >= 60 else "FAIL"
                
                return HealthCheckResult(
                    test_name="Mobile-Friendliness",
                    status=status,
                    score=mobile_score,
                    details={
                        "mobile_checks": mobile_checks,
                        "passed_checks": passed_checks,
                        "total_checks": total_checks,
                        "failed_checks": [k for k, v in mobile_checks.items() if not v]
                    },
                    recommendations=[
                        "Add viewport meta tag",
                        "Implement responsive design with media queries",
                        "Use touch-friendly button sizes (min 44px)",
                        "Use readable font sizes (minimum 16px)",
                        "Prevent horizontal scrolling on mobile",
                        "Use responsive images with srcset and sizes",
                        "Test on actual mobile devices",
                        "Implement mobile-first design approach"
                    ]
                )
                
        except Exception as e:
            return HealthCheckResult(
                test_name="Mobile-Friendliness",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper mobile testing"]
            )

    async def test_javascript_css_errors(self) -> HealthCheckResult:
        """Test for JavaScript and CSS errors through code analysis"""
        logger.info("Testing for JavaScript and CSS errors...")
        
        try:
            async with self.session.get(f"{self.base_url}/landing.html") as response:
                html_content = await response.text()
                
                # Check for common JavaScript issues
                js_issues = {
                    "console_errors": "console.error" in html_content,
                    "console_warnings": "console.warn" in html_content,
                    "syntax_errors": "SyntaxError" in html_content,
                    "reference_errors": "ReferenceError" in html_content,
                    "type_errors": "TypeError" in html_content,
                    "eval_usage": "eval(" in html_content,
                    "innerhtml_usage": "innerHTML" in html_content,
                }
                
                # Check for common CSS issues
                css_issues = {
                    "invalid_css": "invalid" in html_content.lower() and "css" in html_content.lower(),
                    "missing_semicolons": html_content.count(";") < html_content.count(":"),
                    "unclosed_brackets": html_content.count("{") != html_content.count("}"),
                    "important_overuse": html_content.count("!important") > 10,
                }
                
                total_issues = sum(js_issues.values()) + sum(css_issues.values())
                
                if total_issues == 0:
                    status = "PASS"
                    score = 100
                elif total_issues <= 2:
                    status = "WARNING"
                    score = 75
                else:
                    status = "FAIL"
                    score = max(0, 100 - (total_issues * 20))
                
                return HealthCheckResult(
                    test_name="JavaScript and CSS Errors",
                    status=status,
                    score=score,
                    details={
                        "javascript_issues": js_issues,
                        "css_issues": css_issues,
                        "total_issues": total_issues,
                        "issue_details": {
                            "js_issues_count": sum(js_issues.values()),
                            "css_issues_count": sum(css_issues.values())
                        }
                    },
                    recommendations=[
                        "Remove console.error and console.warn statements from production",
                        "Fix any JavaScript syntax errors",
                        "Avoid using eval() for security reasons",
                        "Use textContent instead of innerHTML when possible",
                        "Validate CSS for syntax errors",
                        "Reduce use of !important declarations",
                        "Use a linter for JavaScript and CSS",
                        "Implement proper error handling"
                    ]
                )
                
        except Exception as e:
            return HealthCheckResult(
                test_name="JavaScript and CSS Errors",
                status="FAIL",
                details={"error": str(e)},
                recommendations=["Implement proper error monitoring"]
            )

    async def run_all_tests(self) -> List[HealthCheckResult]:
        """Run all health check tests"""
        logger.info("Starting simplified comprehensive health check...")
        
        tests = [
            self.test_page_load_speed(),
            self.test_core_web_vitals_simulation(),
            self.test_cross_browser_compatibility(),
            self.test_accessibility_compliance(),
            self.test_security_headers(),
            self.test_mobile_friendliness(),
            self.test_javascript_css_errors(),
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

    def generate_report(self) -> str:
        """Generate a comprehensive health check report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate overall score
        scores = [r.score for r in self.results if r.score is not None]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Count statuses
        status_counts = {}
        for result in self.results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        report = f"""
# MINGUS Application - Simplified Comprehensive Technical Health Check Report
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
    """Main function to run the health check"""
    base_url = "http://localhost:8000"
    
    print("🔍 Starting Simplified Comprehensive Technical Health Check for MINGUS Application")
    print("=" * 80)
    
    async with SimplifiedHealthChecker(base_url) as checker:
        results = await checker.run_all_tests()
        report = checker.generate_report()
        
        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"simplified_health_check_report_{timestamp}.md"
        
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Simplified report saved to: {report_filename}")
        
        # Also save JSON results
        json_filename = f"simplified_health_check_results_{timestamp}.json"
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
