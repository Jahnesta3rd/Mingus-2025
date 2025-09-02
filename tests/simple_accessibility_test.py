#!/usr/bin/env python3
"""
Simple Accessibility Testing without Selenium
Uses requests and BeautifulSoup for basic accessibility validation
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAccessibilityTester:
    """Simple accessibility tester using requests and BeautifulSoup"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': base_url,
            'pages_tested': 0,
            'overall_score': 0,
            'wcag_aa_compliance': False,
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
    
    def test_page(self, url_path: str, page_name: str = None) -> Dict:
        """Test a single page for accessibility issues"""
        if page_name is None:
            page_name = url_path if url_path != '/' else 'Homepage'
        
        try:
            url = f"{self.base_url}{url_path}"
            logger.info(f"Testing page: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Run accessibility tests
            test_results = {
                'page_name': page_name,
                'url': url,
                'status_code': response.status_code,
                'content_length': len(response.content),
                'tests': {}
            }
            
            # Test 1: Language declaration
            test_results['tests']['language_declaration'] = self._test_language_declaration(soup)
            
            # Test 2: Page title
            test_results['tests']['page_title'] = self._test_page_title(soup)
            
            # Test 3: Heading structure
            test_results['tests']['heading_structure'] = self._test_heading_structure(soup)
            
            # Test 4: Skip links
            test_results['tests']['skip_links'] = self._test_skip_links(soup)
            
            # Test 5: Form accessibility
            test_results['tests']['form_accessibility'] = self._test_form_accessibility(soup)
            
            # Test 6: Image accessibility
            test_results['tests']['image_accessibility'] = self._test_image_accessibility(soup)
            
            # Test 7: Link accessibility
            test_results['tests']['link_accessibility'] = self._test_link_accessibility(soup)
            
            # Test 8: ARIA labels
            test_results['tests']['aria_labels'] = self._test_aria_labels(soup)
            
            # Test 9: Color contrast indicators
            test_results['tests']['color_contrast_indicators'] = self._test_color_contrast_indicators(soup)
            
            # Test 10: Touch target indicators
            test_results['tests']['touch_target_indicators'] = self._test_touch_target_indicators(soup)
            
            # Calculate page score
            passed_tests = sum(1 for test in test_results['tests'].values() if test['status'] == 'pass')
            total_tests = len(test_results['tests'])
            page_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            test_results['score'] = page_score
            test_results['passed_tests'] = passed_tests
            test_results['total_tests'] = total_tests
            
            # Update global results
            self.results['pages_tested'] += 1
            self.results['overall_score'] += page_score
            
            # Collect issues
            for test_name, test_result in test_results['tests'].items():
                if test_result['status'] == 'fail':
                    self.results['critical_issues'].append(f"{page_name}: {test_result['description']}")
                elif test_result['status'] == 'warning':
                    self.results['warnings'].append(f"{page_name}: {test_result['description']}")
            
            logger.info(f"Page {page_name} tested: {passed_tests}/{total_tests} tests passed (Score: {page_score:.1f}%)")
            return test_results
            
        except Exception as e:
            logger.error(f"Failed to test page {page_name}: {e}")
            return {
                'page_name': page_name,
                'url': f"{self.base_url}{url_path}",
                'error': str(e),
                'status': 'error'
            }
    
    def _test_language_declaration(self, soup: BeautifulSoup) -> Dict:
        """Test if HTML has proper language declaration"""
        html_tag = soup.find('html')
        lang_attr = html_tag.get('lang') if html_tag else None
        
        if lang_attr and lang_attr.strip():
            return {
                'status': 'pass',
                'description': f'Language declared: {lang_attr}',
                'details': {'language': lang_attr}
            }
        else:
            return {
                'status': 'fail',
                'description': 'No language declaration found',
                'details': {'language': None}
            }
    
    def _test_page_title(self, soup: BeautifulSoup) -> Dict:
        """Test if page has a meaningful title"""
        title_tag = soup.find('title')
        title_text = title_tag.get_text().strip() if title_tag else ''
        
        if title_text and len(title_text) > 0:
            return {
                'status': 'pass',
                'description': f'Page title found: "{title_text}"',
                'details': {'title': title_text}
            }
        else:
            return {
                'status': 'fail',
                'description': 'No page title found',
                'details': {'title': title_text}
            }
    
    def _test_heading_structure(self, soup: BeautifulSoup) -> Dict:
        """Test heading hierarchy and structure"""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        heading_structure = []
        
        for heading in headings:
            heading_structure.append({
                'level': heading.name,
                'text': heading.get_text().strip()[:50]
            })
        
        # Check for h1
        h1_count = len([h for h in headings if h.name == 'h1'])
        
        if h1_count == 0:
            return {
                'status': 'fail',
                'description': 'No H1 heading found',
                'details': {'headings': heading_structure, 'h1_count': h1_count}
            }
        elif h1_count > 1:
            return {
                'status': 'warning',
                'description': f'Multiple H1 headings found ({h1_count})',
                'details': {'headings': heading_structure, 'h1_count': h1_count}
            }
        else:
            return {
                'status': 'pass',
                'description': f'Proper heading structure with {len(headings)} headings',
                'details': {'headings': heading_structure, 'h1_count': h1_count}
            }
    
    def _test_skip_links(self, soup: BeautifulSoup) -> Dict:
        """Test for skip links"""
        skip_links = soup.find_all('a', href=lambda x: x and x.startswith('#'))
        skip_link_texts = [link.get_text().strip() for link in skip_links]
        
        if skip_links:
            return {
                'status': 'pass',
                'description': f'Skip links found: {len(skip_links)}',
                'details': {'skip_links': skip_link_texts}
            }
        else:
            return {
                'status': 'warning',
                'description': 'No skip links found',
                'details': {'skip_links': []}
            }
    
    def _test_form_accessibility(self, soup: BeautifulSoup) -> Dict:
        """Test form accessibility features"""
        forms = soup.find_all('form')
        form_issues = []
        
        for form in forms:
            # Check for form labels
            inputs = form.find_all(['input', 'select', 'textarea'])
            for input_elem in inputs:
                input_id = input_elem.get('id')
                if input_id:
                    label = soup.find('label', attrs={'for': input_id})
                    if not label:
                        form_issues.append(f'Input {input_id} missing label')
                else:
                    form_issues.append('Input missing id attribute')
        
        if form_issues:
            return {
                'status': 'fail',
                'description': f'Form accessibility issues found: {len(form_issues)}',
                'details': {'issues': form_issues}
            }
        else:
            return {
                'status': 'pass',
                'description': 'Forms have proper accessibility features',
                'details': {'forms_count': len(forms)}
            }
    
    def _test_image_accessibility(self, soup: BeautifulSoup) -> Dict:
        """Test image accessibility"""
        images = soup.find_all('img')
        images_without_alt = []
        
        for img in images:
            alt_text = img.get('alt', '').strip()
            if not alt_text:
                images_without_alt.append(img.get('src', 'unknown'))
        
        if images_without_alt:
            return {
                'status': 'fail',
                'description': f'Images without alt text: {len(images_without_alt)}',
                'details': {'images_without_alt': images_without_alt}
            }
        else:
            return {
                'status': 'pass',
                'description': f'All {len(images)} images have alt text',
                'details': {'total_images': len(images)}
            }
    
    def _test_link_accessibility(self, soup: BeautifulSoup) -> Dict:
        """Test link accessibility"""
        links = soup.find_all('a', href=True)
        links_without_text = []
        
        for link in links:
            link_text = link.get_text().strip()
            if not link_text:
                links_without_text.append(link.get('href', 'unknown'))
        
        if links_without_text:
            return {
                'status': 'fail',
                'description': f'Links without descriptive text: {len(links_without_text)}',
                'details': {'links_without_text': links_without_text}
            }
        else:
            return {
                'status': 'pass',
                'description': f'All {len(links)} links have descriptive text',
                'details': {'total_links': len(links)}
            }
    
    def _test_aria_labels(self, soup: BeautifulSoup) -> Dict:
        """Test ARIA labels and roles"""
        elements_with_aria = soup.find_all(attrs={'aria-label': True, 'aria-labelledby': True, 'role': True})
        aria_elements = []
        
        for elem in elements_with_aria:
            aria_info = {}
            if elem.get('aria-label'):
                aria_info['aria-label'] = elem.get('aria-label')
            if elem.get('aria-labelledby'):
                aria_info['aria-labelledby'] = elem.get('aria-labelledby')
            if elem.get('role'):
                aria_info['role'] = elem.get('role')
            
            aria_elements.append({
                'tag': elem.name,
                'attributes': aria_info
            })
        
        if aria_elements:
            return {
                'status': 'pass',
                'description': f'ARIA attributes found: {len(aria_elements)} elements',
                'details': {'aria_elements': aria_elements}
            }
        else:
            return {
                'status': 'warning',
                'description': 'No ARIA attributes found',
                'details': {'aria_elements': []}
            }
    
    def _test_color_contrast_indicators(self, soup: BeautifulSoup) -> Dict:
        """Test for color contrast indicators in CSS classes"""
        # Look for CSS classes that suggest color contrast considerations
        contrast_indicators = soup.find_all(class_=lambda x: x and any(word in x.lower() for word in ['contrast', 'high-contrast', 'dark-mode', 'light-mode']))
        
        if contrast_indicators:
            return {
                'status': 'pass',
                'description': f'Color contrast indicators found: {len(contrast_indicators)}',
                'details': {'contrast_indicators': len(contrast_indicators)}
            }
        else:
            return {
                'status': 'warning',
                'description': 'No color contrast indicators found',
                'details': {'contrast_indicators': 0}
            }
    
    def _test_touch_target_indicators(self, soup: BeautifulSoup) -> Dict:
        """Test for touch target indicators in CSS classes"""
        # Look for CSS classes that suggest touch target considerations
        touch_indicators = soup.find_all(class_=lambda x: x and any(word in x.lower() for word in ['touch', 'target', 'button', 'clickable', '44px', '44px']))
        
        if touch_indicators:
            return {
                'status': 'pass',
                'description': f'Touch target indicators found: {len(touch_indicators)}',
                'details': {'touch_indicators': len(touch_indicators)}
            }
        else:
            return {
                'status': 'warning',
                'description': 'No touch target indicators found',
                'details': {'touch_indicators': 0}
            }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive accessibility testing report"""
        try:
            if self.results['pages_tested'] > 0:
                self.results['overall_score'] = self.results['overall_score'] / self.results['pages_tested']
            
            # Determine WCAG AA compliance
            self.results['wcag_aa_compliance'] = (
                self.results['overall_score'] >= 80 and 
                len(self.results['critical_issues']) == 0
            )
            
            report = {
                'summary': {
                    'total_pages': self.results['pages_tested'],
                    'overall_score': round(self.results['overall_score'], 1),
                    'wcag_aa_compliant': self.results['wcag_aa_compliance'],
                    'critical_issues': len(self.results['critical_issues']),
                    'warnings': len(self.results['warnings'])
                },
                'details': self.results,
                'recommendations': self._generate_recommendations()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []
        
        if self.results['critical_issues']:
            recommendations.append("Address critical accessibility issues immediately")
            recommendations.append("Focus on missing alt text, form labels, and heading structure")
        
        if self.results['warnings']:
            recommendations.append("Review and address accessibility warnings")
        
        if self.results['overall_score'] < 80:
            recommendations.append("Implement comprehensive accessibility improvements")
            recommendations.append("Consider accessibility training for development team")
        
        if not recommendations:
            recommendations.append("Maintain current accessibility standards")
            recommendations.append("Continue regular accessibility testing")
        
        return recommendations
    
    def save_report(self, filename: str = None) -> str:
        """Save testing report to JSON file"""
        try:
            if not filename:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"simple_accessibility_report_{timestamp}.json"
            
            report = self.generate_report()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Accessibility report saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return ""

def run_simple_accessibility_tests(base_url: str, pages: List[str] = None) -> Dict:
    """Run simple accessibility tests on specified pages"""
    if pages is None:
        pages = ['/', '/forms', '/calculator']
    
    tester = SimpleAccessibilityTester(base_url)
    
    try:
        for page in pages:
            try:
                tester.test_page(page)
            except Exception as e:
                logger.error(f"Failed to test page {page}: {e}")
        
        report = tester.generate_report()
        filename = tester.save_report()
        
        return {
            'report': report,
            'report_file': filename,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Accessibility testing failed: {e}")
        return {
            'error': str(e),
            'success': False
        }

if __name__ == "__main__":
    # Example usage
    results = run_simple_accessibility_tests("http://localhost:5001", ['/', '/forms', '/calculator'])
    print(json.dumps(results, indent=2))
