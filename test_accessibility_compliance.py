#!/usr/bin/env python3
"""
WCAG 2.1 AA Accessibility Compliance Testing Script
Comprehensive testing for financial application accessibility
"""

import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import argparse
import sys
from datetime import datetime
import colorama
from colorama import Fore, Back, Style

# Initialize colorama for cross-platform colored output
colorama.init()

class AccessibilityTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "pages_tested": [],
            "overall_score": 0,
            "wcag_aa_compliance": False,
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "detailed_results": {}
        }
        
        # WCAG 2.1 AA Success Criteria
        self.wcag_criteria = {
            "1.1.1": "Non-text Content",
            "1.2.1": "Audio-only and Video-only",
            "1.2.2": "Captions",
            "1.2.3": "Audio Description",
            "1.3.1": "Info and Relationships",
            "1.3.2": "Meaningful Sequence",
            "1.3.3": "Sensory Characteristics",
            "1.4.1": "Use of Color",
            "1.4.2": "Audio Control",
            "1.4.3": "Contrast (Minimum)",
            "1.4.4": "Resize Text",
            "1.4.5": "Images of Text",
            "2.1.1": "Keyboard",
            "2.1.2": "No Keyboard Trap",
            "2.1.4": "Single Character Key Shortcuts",
            "2.2.1": "Timing Adjustable",
            "2.2.2": "Pause, Stop, Hide",
            "2.3.1": "Three Flashes or Below Threshold",
            "2.4.1": "Bypass Blocks",
            "2.4.2": "Page Titled",
            "2.4.3": "Focus Order",
            "2.4.4": "Link Purpose (In Context)",
            "2.4.5": "Multiple Ways",
            "2.4.6": "Headings and Labels",
            "2.4.7": "Focus Visible",
            "2.5.1": "Pointer Gestures",
            "2.5.2": "Pointer Cancellation",
            "2.5.3": "Label in Name",
            "2.5.4": "Motion Actuation",
            "2.5.5": "Target Size",
            "2.5.6": "Input Mechanisms",
            "2.6.1": "Character Key Shortcuts",
            "2.6.2": "Pointer Cancellation",
            "2.6.3": "Motion Actuation",
            "2.6.4": "Single Pointer",
            "2.6.5": "Target Size",
            "2.6.6": "Input Mechanisms",
            "3.1.1": "Language of Page",
            "3.1.2": "Language of Parts",
            "3.2.1": "On Focus",
            "3.2.2": "On Input",
            "3.2.3": "Consistent Navigation",
            "3.2.4": "Consistent Identification",
            "3.3.1": "Error Identification",
            "3.3.2": "Labels or Instructions",
            "3.3.3": "Error Suggestion",
            "3.3.4": "Error Prevention (Legal, Financial, Data)",
            "3.3.5": "Help",
            "3.3.6": "Error Prevention (All)",
            "3.3.7": "Authentication",
            "3.3.8": "Redundant Entry",
            "3.3.9": "Accessible Authentication",
            "4.1.1": "Parsing",
            "4.1.2": "Name, Role, Value",
            "4.1.3": "Status Messages"
        }

    def test_page(self, url_path="/"):
        """Test a single page for accessibility compliance"""
        full_url = urljoin(self.base_url, url_path)
        print(f"\n{Fore.CYAN}Testing: {full_url}{Style.RESET_ALL}")
        
        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_results = {
                "url": full_url,
                "status_code": response.status_code,
                "tests": {},
                "score": 0,
                "issues": [],
                "warnings": []
            }
            
            # Run all accessibility tests
            tests = [
                self.test_skip_links,
                self.test_heading_structure,
                self.test_aria_labels,
                self.test_keyboard_navigation,
                self.test_color_contrast,
                self.test_form_accessibility,
                self.test_image_accessibility,
                self.test_link_accessibility,
                self.test_table_accessibility,
                self.test_modal_accessibility,
                self.test_focus_management,
                self.test_screen_reader_support,
                self.test_touch_targets,
                self.test_language_declaration,
                self.test_page_title,
                self.test_landmark_roles
            ]
            
            for test_func in tests:
                test_name = test_func.__name__.replace('test_', '').replace('_', ' ')
                print(f"  {Fore.YELLOW}Running: {test_name}{Style.RESET_ALL}")
                
                try:
                    result = test_func(soup, full_url)
                    page_results["tests"][test_name] = result
                    
                    if result["status"] == "pass":
                        page_results["score"] += result["score"]
                    elif result["status"] == "fail":
                        page_results["issues"].extend(result["issues"])
                    elif result["status"] == "warning":
                        page_results["warnings"].extend(result["warnings"])
                        
                except Exception as e:
                    print(f"    {Fore.RED}Error in {test_name}: {str(e)}{Style.RESET_ALL}")
                    page_results["tests"][test_name] = {
                        "status": "error",
                        "score": 0,
                        "issues": [f"Test error: {str(e)}"],
                        "warnings": []
                    }
            
            # Calculate page score
            max_possible_score = len(tests) * 10
            page_results["score"] = min(100, (page_results["score"] / max_possible_score) * 100)
            
            self.results["pages_tested"].append(page_results)
            self.results["detailed_results"][url_path] = page_results
            
            print(f"  {Fore.GREEN}Page Score: {page_results['score']:.1f}%{Style.RESET_ALL}")
            
            return page_results
            
        except requests.RequestException as e:
            print(f"  {Fore.RED}Error accessing page: {str(e)}{Style.RESET_ALL}")
            return None

    def test_skip_links(self, soup, url):
        """Test for proper skip links"""
        skip_links = soup.find_all('a', class_='skip-link')
        
        if not skip_links:
            return {
                "status": "fail",
                "score": 0,
                "issues": ["No skip links found"],
                "warnings": []
            }
        
        issues = []
        warnings = []
        
        for link in skip_links:
            href = link.get('href')
            if not href:
                issues.append("Skip link missing href attribute")
            elif not href.startswith('#'):
                issues.append("Skip link should point to page anchor")
            
            if not link.get_text(strip=True):
                issues.append("Skip link missing text content")
        
        if issues:
            return {
                "status": "fail",
                "score": 0,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": []
        }

    def test_heading_structure(self, soup, url):
        """Test for proper heading hierarchy"""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headings:
            return {
                "status": "fail",
                "score": 0,
                "issues": ["No headings found"],
                "warnings": []
            }
        
        issues = []
        warnings = []
        
        # Check for h1
        h1_tags = soup.find_all('h1')
        if not h1_tags:
            issues.append("Page missing main heading (h1)")
        elif len(h1_tags) > 1:
            warnings.append("Multiple h1 tags found - should have only one main heading")
        
        # Check heading hierarchy
        current_level = 0
        for heading in headings:
            level = int(heading.name[1])
            
            if level - current_level > 1:
                issues.append(f"Heading level skipped: {heading.name} follows {current_level}")
            
            current_level = level
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": warnings
        }

    def test_aria_labels(self, soup, url):
        """Test for proper ARIA labels and roles"""
        issues = []
        warnings = []
        
        # Check interactive elements for ARIA labels
        interactive_elements = soup.find_all(['button', 'input', 'select', 'textarea', 'a'])
        
        for element in interactive_elements:
            # Skip hidden elements
            if element.get('type') == 'hidden' or element.get('aria-hidden') == 'true':
                continue
            
            # Check buttons
            if element.name == 'button':
                if not element.get_text(strip=True) and not element.get('aria-label'):
                    issues.append("Button missing accessible name")
            
            # Check inputs
            elif element.name == 'input':
                if not element.get('aria-label') and not element.get('aria-labelledby'):
                    # Check if there's a label
                    input_id = element.get('id')
                    if input_id:
                        label = soup.find('label', attrs={'for': input_id})
                        if not label:
                            issues.append(f"Input missing accessible name: {element.get('type', 'input')}")
                    else:
                        issues.append(f"Input missing accessible name: {element.get('type', 'input')}")
            
            # Check links
            elif element.name == 'a':
                if not element.get_text(strip=True) and not element.get('aria-label'):
                    issues.append("Link missing accessible name")
        
        # Check for proper ARIA usage
        aria_elements = soup.find_all(attrs={'aria-*': True})
        for element in aria_elements:
            aria_attrs = [attr for attr in element.attrs if attr.startswith('aria-')]
            for attr in aria_attrs:
                value = element[attr]
                if value == '' or value == 'undefined':
                    issues.append(f"Invalid ARIA attribute value: {attr}='{value}'")
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": warnings
        }

    def test_keyboard_navigation(self, soup, url):
        """Test for keyboard navigation support"""
        issues = []
        warnings = []
        
        # Check for focusable elements
        focusable_elements = soup.find_all(['a', 'button', 'input', 'select', 'textarea'])
        
        if not focusable_elements:
            issues.append("No focusable elements found")
        else:
            # Check for tabindex
            tabindex_elements = soup.find_all(attrs={'tabindex': True})
            for element in tabindex_elements:
                tabindex = element.get('tabindex')
                if tabindex == '0' or tabindex == '-1':
                    continue
                warnings.append(f"Element has non-standard tabindex: {tabindex}")
        
        # Check for keyboard event handlers
        script_tags = soup.find_all('script')
        keyboard_events = ['keydown', 'keyup', 'keypress']
        
        for script in script_tags:
            script_content = script.get_text()
            for event in keyboard_events:
                if event in script_content:
                    # Check if it's a proper keyboard handler
                    if 'addEventListener' in script_content or 'onkey' in script_content:
                        break
            else:
                warnings.append("Keyboard event handlers found but may not be properly implemented")
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": warnings
        }

    def test_color_contrast(self, soup, url):
        """Test for color contrast compliance"""
        # This is a basic test - in production, use a proper contrast checking library
        issues = []
        warnings = []
        
        # Check for CSS variables that indicate good contrast
        style_tags = soup.find_all('style')
        css_content = ' '.join([style.get_text() for style in style_tags])
        
        # Look for color contrast indicators
        if '--text-primary: #000000' in css_content or '--text-primary: #1a1a1a' in css_content:
            warnings.append("Color contrast should be verified with proper testing tools")
        else:
            warnings.append("Color contrast compliance cannot be determined from HTML alone")
        
        return {
            "status": "warning",
            "score": 5,
            "issues": issues,
            "warnings": warnings
        }

    def test_form_accessibility(self, soup, url):
        """Test for form accessibility"""
        forms = soup.find_all('form')
        
        if not forms:
            return {
                "status": "pass",
                "score": 10,
                "issues": [],
                "warnings": []
            }
        
        issues = []
        warnings = []
        
        for form in forms:
            # Check for form labels
            inputs = form.find_all(['input', 'select', 'textarea'])
            for input_elem in inputs:
                if input_elem.get('type') == 'hidden':
                    continue
                
                input_id = input_elem.get('id')
                if input_id:
                    label = soup.find('label', attrs={'for': input_id})
                    if not label:
                        issues.append(f"Input missing label: {input_elem.get('type', 'input')}")
                else:
                    issues.append(f"Input missing id: {input_elem.get('type', 'input')}")
            
            # Check for fieldset and legend
            fieldsets = form.find_all('fieldset')
            for fieldset in fieldsets:
                legend = fieldset.find('legend')
                if not legend:
                    issues.append("Fieldset missing legend")
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": warnings
        }

    def test_image_accessibility(self, soup, url):
        """Test for image accessibility"""
        images = soup.find_all('img')
        
        if not images:
            return {
                "status": "pass",
                "score": 10,
                "issues": [],
                "warnings": []
            }
        
        issues = []
        warnings = []
        
        for img in images:
            alt = img.get('alt')
            if alt is None:
                issues.append("Image missing alt attribute")
            elif alt == '':
                # Empty alt is OK for decorative images
                pass
            else:
                # Check if alt text is meaningful
                if len(alt) < 3:
                    warnings.append("Image alt text may be too short")
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": warnings
        }

    def test_link_accessibility(self, soup, url):
        """Test for link accessibility"""
        links = soup.find_all('a')
        
        if not links:
            return {
                "status": "pass",
                "score": 10,
                "issues": [],
                "warnings": []
            }
        
        issues = []
        warnings = []
        
        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            if not href:
                issues.append("Link missing href attribute")
            elif href == '#' or href == 'javascript:void(0)':
                warnings.append("Link with no meaningful destination")
            
            if not text and not link.get('aria-label'):
                issues.append("Link missing accessible text")
            
            # Check for external links
            if href and href.startswith('http') and not href.startswith(self.base_url):
                if not link.get('target') == '_blank':
                    warnings.append("External link should open in new tab")
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": []
        }

    def test_table_accessibility(self, soup, url):
        """Test for table accessibility"""
        tables = soup.find_all('table')
        
        if not tables:
            return {
                "status": "pass",
                "score": 10,
                "issues": [],
                "warnings": []
            }
        
        issues = []
        warnings = []
        
        for table in tables:
            # Check for headers
            headers = table.find_all('th')
            if not headers:
                issues.append("Table missing header cells")
            
            # Check for scope attributes
            for header in headers:
                if not header.get('scope'):
                    warnings.append("Table header missing scope attribute")
            
            # Check for caption
            caption = table.find('caption')
            if not caption:
                warnings.append("Table missing caption")
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": []
        }

    def test_modal_accessibility(self, soup, url):
        """Test for modal accessibility"""
        modals = soup.find_all(['div'], class_=['modal', 'dialog', 'popup'])
        
        if not modals:
            return {
                "status": "pass",
                "score": 10,
                "issues": [],
                "warnings": []
            }
        
        issues = []
        warnings = []
        
        for modal in modals:
            # Check for proper ARIA attributes
            if not modal.get('role') and not 'modal' in modal.get('class', []):
                warnings.append("Modal missing role attribute")
            
            if not modal.get('aria-labelledby') and not modal.get('aria-label'):
                issues.append("Modal missing accessible name")
            
            # Check for close button
            close_buttons = modal.find_all(['button', 'a'], class_=['close', 'popup-close'])
            if not close_buttons:
                warnings.append("Modal missing close button")
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": []
        }

    def test_focus_management(self, soup, url):
        """Test for focus management"""
        issues = []
        warnings = []
        
        # Check for focus-visible CSS class
        style_tags = soup.find_all('style')
        css_content = ' '.join([style.get_text() for style in style_tags])
        
        if 'focus-visible' not in css_content and ':focus' not in css_content:
            warnings.append("Focus styles may not be properly implemented")
        
        # Check for tabindex usage
        tabindex_elements = soup.find_all(attrs={'tabindex': True})
        for element in tabindex_elements:
            tabindex = element.get('tabindex')
            if tabindex == '-1':
                warnings.append("Element with tabindex='-1' should be focusable programmatically")
        
        return {
            "status": "warning",
            "score": 5,
            "issues": issues,
            "warnings": warnings
        }

    def test_screen_reader_support(self, soup, url):
        """Test for screen reader support"""
        issues = []
        warnings = []
        
        # Check for screen reader only content
        sr_elements = soup.find_all(class_=['sr-only', 'screen-reader-only'])
        if not sr_elements:
            warnings.append("No screen reader only content found")
        
        # Check for ARIA live regions
        live_regions = soup.find_all(attrs={'aria-live': True})
        if not live_regions:
            warnings.append("No ARIA live regions found for dynamic content")
        
        # Check for landmarks
        landmarks = soup.find_all(attrs={'role': ['banner', 'main', 'contentinfo', 'navigation', 'complementary']})
        if not landmarks:
            warnings.append("No landmark roles found")
        
        return {
            "status": "warning",
            "score": 5,
            "issues": issues,
            "warnings": warnings
        }

    def test_touch_targets(self, soup, url):
        """Test for touch target sizes"""
        issues = []
        warnings = []
        
        # Check for touch target classes
        touch_targets = soup.find_all(class_='touch-target')
        if not touch_targets:
            warnings.append("Touch target optimization classes not found")
        
        # Check for minimum size attributes
        style_tags = soup.find_all('style')
        css_content = ' '.join([style.get_text() for style in style_tags])
        
        if 'min-height: 44px' not in css_content and 'min-width: 44px' not in css_content:
            warnings.append("Touch target sizes may not meet minimum requirements")
        
        return {
            "status": "warning",
            "score": 5,
            "issues": issues,
            "warnings": warnings
        }

    def test_language_declaration(self, soup, url):
        """Test for language declaration"""
        html_tag = soup.find('html')
        
        if not html_tag or not html_tag.get('lang'):
            return {
                "status": "fail",
                "score": 0,
                "issues": ["HTML missing lang attribute"],
                "warnings": []
            }
        
        lang = html_tag.get('lang')
        if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', lang):
            warnings.append(f"Language attribute format may be invalid: {lang}")
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": warnings
        }

    def test_page_title(self, soup, url):
        """Test for page title"""
        title_tag = soup.find('title')
        
        if not title_tag:
            return {
                "status": "fail",
                "score": 0,
                "issues": ["Page missing title"],
                "warnings": []
            }
        
        title_text = title_tag.get_text(strip=True)
        if not title_text:
            return {
                "status": "fail",
                "score": 0,
                "issues": ["Page title is empty"],
                "warnings": []
            }
        
        if len(title_text) < 10:
            warnings.append("Page title may be too short")
        elif len(title_text) > 60:
            warnings.append("Page title may be too long")
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": warnings
        }

    def test_landmark_roles(self, soup, url):
        """Test for landmark roles"""
        landmarks = soup.find_all(attrs={'role': ['banner', 'main', 'contentinfo', 'navigation', 'complementary', 'search']})
        
        if not landmarks:
            return {
                "status": "fail",
                "score": 0,
                "issues": ["No landmark roles found"],
                "warnings": []
            }
        
        issues = []
        warnings = []
        
        # Check for main landmark
        main_landmark = soup.find(attrs={'role': 'main'})
        if not main_landmark:
            issues.append("Page missing main landmark role")
        
        # Check for navigation landmark
        nav_landmarks = soup.find_all(attrs={'role': 'navigation'})
        if not nav_landmarks:
            warnings.append("Page missing navigation landmark role")
        
        # Check for banner landmark
        banner_landmark = soup.find(attrs={'role': 'banner'})
        if not banner_landmark:
            warnings.append("Page missing banner landmark role")
        
        if issues:
            return {
                "status": "fail",
                "score": 5,
                "issues": issues,
                "warnings": warnings
            }
        
        return {
            "status": "pass",
            "score": 10,
            "issues": [],
            "warnings": warnings
        }

    def generate_report(self):
        """Generate comprehensive accessibility report"""
        print(f"\n{Fore.CYAN}=== WCAG 2.1 AA ACCESSIBILITY COMPLIANCE REPORT ==={Style.RESET_ALL}")
        print(f"Generated: {self.results['timestamp']}")
        print(f"Base URL: {self.results['base_url']}")
        print(f"Pages Tested: {len(self.results['pages_tested'])}")
        
        # Calculate overall score
        total_score = 0
        total_issues = 0
        total_warnings = 0
        
        for page in self.results['pages_tested']:
            total_score += page['score']
            total_issues += len(page['issues'])
            total_warnings += len(page['warnings'])
        
        if self.results['pages_tested']:
            self.results['overall_score'] = total_score / len(self.results['pages_tested'])
        
        print(f"\n{Fore.GREEN}Overall Score: {self.results['overall_score']:.1f}%{Style.RESET_ALL}")
        print(f"Total Issues: {total_issues}")
        print(f"Total Warnings: {total_warnings}")
        
        # Determine compliance
        if self.results['overall_score'] >= 90 and total_issues == 0:
            self.results['wcag_aa_compliance'] = True
            print(f"\n{Fore.GREEN}✓ WCAG 2.1 AA COMPLIANCE ACHIEVED{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}✗ WCAG 2.1 AA COMPLIANCE NOT ACHIEVED{Style.RESET_ALL}")
        
        # Page-by-page results
        print(f"\n{Fore.CYAN}=== DETAILED RESULTS ==={Style.RESET_ALL}")
        for page in self.results['pages_tested']:
            print(f"\n{Fore.YELLOW}Page: {page['url']}{Style.RESET_ALL}")
            print(f"  Score: {page['score']:.1f}%")
            
            if page['issues']:
                print(f"  {Fore.RED}Issues:{Style.RESET_ALL}")
                for issue in page['issues']:
                    print(f"    • {issue}")
            
            if page['warnings']:
                print(f"  {Fore.YELLOW}Warnings:{Style.RESET_ALL}")
                for warning in page['warnings']:
                    print(f"    • {warning}")
        
        # Generate recommendations
        self.generate_recommendations()
        
        return self.results

    def generate_recommendations(self):
        """Generate actionable recommendations"""
        print(f"\n{Fore.CYAN}=== RECOMMENDATIONS ==={Style.RESET_ALL}")
        
        all_issues = []
        all_warnings = []
        
        for page in self.results['pages_tested']:
            all_issues.extend(page['issues'])
            all_warnings.extend(page['warnings'])
        
        # Count issue types
        issue_counts = {}
        for issue in all_issues:
            issue_type = issue.split(':')[0] if ':' in issue else issue
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        # Generate recommendations based on common issues
        if 'No skip links found' in all_issues:
            print(f"{Fore.YELLOW}• Add skip links for keyboard navigation{Style.RESET_ALL}")
        
        if 'Page missing main heading (h1)' in all_issues:
            print(f"{Fore.YELLOW}• Ensure each page has exactly one h1 heading{Style.RESET_ALL}")
        
        if 'Image missing alt attribute' in all_issues:
            print(f"{Fore.YELLOW}• Add alt text to all images{Style.RESET_ALL}")
        
        if 'Input missing accessible name' in all_issues:
            print(f"{Fore.YELLOW}• Ensure all form inputs have proper labels{Style.RESET_ALL}")
        
        if 'Button missing accessible name' in all_issues:
            print(f"{Fore.YELLOW}• Add accessible names to all buttons{Style.RESET_ALL}")
        
        if 'Link missing accessible text' in all_issues:
            print(f"{Fore.YELLOW}• Ensure all links have descriptive text{Style.RESET_ALL}")
        
        if 'Table missing header cells' in all_issues:
            print(f"{Fore.YELLOW}• Add proper headers to data tables{Style.RESET_ALL}")
        
        if 'Modal missing accessible name' in all_issues:
            print(f"{Fore.YELLOW}• Add proper ARIA labels to modals{Style.RESET_ALL}")
        
        # General recommendations
        print(f"\n{Fore.CYAN}General Recommendations:{Style.RESET_ALL}")
        print(f"• Test with screen readers (NVDA, JAWS, VoiceOver)")
        print(f"• Test keyboard-only navigation")
        print(f"• Validate color contrast ratios")
        print(f"• Test with users who have disabilities")
        print(f"• Use automated testing tools (axe-core, WAVE)")

    def save_report(self, filename=None):
        """Save the report to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"accessibility_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{Fore.GREEN}Report saved to: {filename}{Style.RESET_ALL}")
        return filename

def main():
    parser = argparse.ArgumentParser(description='Test WCAG 2.1 AA accessibility compliance')
    parser.add_argument('--url', default='http://localhost:5000', help='Base URL to test')
    parser.add_argument('--pages', nargs='+', default=['/'], help='Pages to test')
    parser.add_argument('--output', help='Output file for the report')
    
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}WCAG 2.1 AA Accessibility Compliance Tester{Style.RESET_ALL}")
    print(f"Testing URL: {args.url}")
    print(f"Pages to test: {args.pages}")
    
    tester = AccessibilityTester(args.url)
    
    # Test each page
    for page in args.pages:
        tester.test_page(page)
    
    # Generate and display report
    results = tester.generate_report()
    
    # Save report
    if args.output:
        tester.save_report(args.output)
    else:
        tester.save_report()
    
    # Exit with appropriate code
    if results['wcag_aa_compliance']:
        print(f"\n{Fore.GREEN}✓ All tests passed!{Style.RESET_ALL}")
        sys.exit(0)
    else:
        print(f"\n{Fore.RED}✗ Some tests failed. Review the issues above.{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
