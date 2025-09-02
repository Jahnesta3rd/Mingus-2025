#!/usr/bin/env python3
"""
Typography Hierarchy Analysis for Mingus Application
Analyzes typography hierarchy, font weights, line heights, and content flow for mobile readability
"""

import re
import json
import os
from datetime import datetime
from pathlib import Path

class TypographyHierarchyAnalyzer:
    def __init__(self):
        self.issues = []
        self.typography_elements = []
        self.heading_hierarchy = []
        self.font_weights = []
        self.line_heights = []
        self.content_flow = []
        self.cta_elements = []
        
    def analyze_file(self, file_path):
        """Analyze a single file for typography hierarchy issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = os.path.basename(file_path)
            print(f"📄 Analyzing {filename}...")
            
            # Analyze CSS/HTML content
            self.analyze_css_typography(content, filename)
            self.analyze_html_typography(content, filename)
            
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
    
    def analyze_css_typography(self, content, filename):
        """Analyze CSS content for typography hierarchy issues"""
        # Find font-weight declarations
        font_weight_pattern = r'font-weight:\s*([^;]+);'
        font_weights = re.findall(font_weight_pattern, content, re.IGNORECASE)
        
        for font_weight in font_weights:
            font_weight = font_weight.strip()
            self.analyze_font_weight(font_weight, filename, 'CSS')
        
        # Find line-height declarations
        line_height_pattern = r'line-height:\s*([^;]+);'
        line_heights = re.findall(line_height_pattern, content, re.IGNORECASE)
        
        for line_height in line_heights:
            line_height = line_height.strip()
            self.analyze_line_height(line_height, filename, 'CSS')
        
        # Find font-size declarations
        font_size_pattern = r'font-size:\s*([^;]+);'
        font_sizes = re.findall(font_size_pattern, content, re.IGNORECASE)
        
        for font_size in font_sizes:
            font_size = font_size.strip()
            self.analyze_font_size(font_size, filename, 'CSS')
        
        # Find CSS custom properties for typography
        css_var_pattern = r'--(text|font|line)-[^:]+:\s*([^;]+);'
        css_vars = re.findall(css_var_pattern, content, re.IGNORECASE)
        
        for css_var in css_vars:
            var_name, var_value = css_var
            var_value = var_value.strip()
            self.analyze_css_variable(var_name, var_value, filename)
    
    def analyze_html_typography(self, content, filename):
        """Analyze HTML content for typography hierarchy issues"""
        # Find heading elements
        heading_pattern = r'<h([1-6])[^>]*>([^<]+)</h[1-6]>'
        headings = re.findall(heading_pattern, content, re.IGNORECASE)
        
        for heading_level, heading_text in headings:
            self.heading_hierarchy.append({
                'level': int(heading_level),
                'text': heading_text.strip(),
                'file': filename,
                'type': 'HTML Heading'
            })
        
        # Find paragraph elements
        paragraph_pattern = r'<p[^>]*>([^<]+)</p>'
        paragraphs = re.findall(paragraph_pattern, content, re.IGNORECASE)
        
        for paragraph_text in paragraphs:
            self.analyze_paragraph(paragraph_text.strip(), filename)
        
        # Find button and CTA elements
        cta_pattern = r'<(button|a)[^>]*class="[^"]*(?:btn|cta|button)[^"]*"[^>]*>([^<]+)</(button|a)>'
        cta_elements = re.findall(cta_pattern, content, re.IGNORECASE)
        
        for cta_type, cta_text, closing_tag in cta_elements:
            self.analyze_cta_element(cta_text.strip(), filename, cta_type)
    
    def analyze_font_weight(self, font_weight, filename, source_type):
        """Analyze font weight value"""
        font_weight = font_weight.strip()
        
        # Parse font weight
        weight_info = self.parse_font_weight(font_weight)
        
        if weight_info:
            weight_info.update({
                'file': filename,
                'source': source_type,
                'raw_value': font_weight
            })
            
            self.font_weights.append(weight_info)
            
            # Check for issues
            self.check_font_weight_issues(weight_info)
    
    def parse_font_weight(self, font_weight):
        """Parse font weight value and return structured data"""
        # Remove quotes and extra spaces
        font_weight = font_weight.strip().strip('"\'')
        
        # Check for numeric values
        numeric_match = re.match(r'(\d+)', font_weight)
        if numeric_match:
            return {
                'value': int(numeric_match.group(1)),
                'type': 'numeric'
            }
        
        # Check for keyword values
        keywords = {
            'normal': 400,
            'bold': 700,
            'bolder': 800,
            'lighter': 300,
            'thin': 100,
            'light': 300,
            'medium': 500,
            'semibold': 600,
            'extrabold': 800,
            'black': 900
        }
        
        if font_weight.lower() in keywords:
            return {
                'value': keywords[font_weight.lower()],
                'type': 'keyword',
                'keyword': font_weight.lower()
            }
        
        # Check for CSS custom properties
        if font_weight.startswith('var(--'):
            return {
                'value': font_weight,
                'type': 'variable'
            }
        
        return None
    
    def check_font_weight_issues(self, weight_info):
        """Check for font weight issues"""
        if weight_info['type'] in ['numeric', 'keyword']:
            weight_value = weight_info['value']
            
            # Check for very light weights (hard to read on mobile)
            if weight_value < 300:
                self.issues.append({
                    'type': 'font_weight_too_light',
                    'severity': 'medium',
                    'message': f"Font weight {weight_value} may be too light for mobile readability",
                    'file': weight_info['file'],
                    'source': weight_info['source'],
                    'value': weight_value
                })
            
            # Check for very heavy weights (may cause rendering issues)
            if weight_value > 800:
                self.issues.append({
                    'type': 'font_weight_too_heavy',
                    'severity': 'low',
                    'message': f"Font weight {weight_value} may be too heavy for optimal rendering",
                    'file': weight_info['file'],
                    'source': weight_info['source'],
                    'value': weight_value
                })
    
    def analyze_line_height(self, line_height, filename, source_type):
        """Analyze line height value"""
        line_height = line_height.strip()
        
        # Parse line height
        height_info = self.parse_line_height(line_height)
        
        if height_info:
            height_info.update({
                'file': filename,
                'source': source_type,
                'raw_value': line_height
            })
            
            self.line_heights.append(height_info)
            
            # Check for issues
            self.check_line_height_issues(height_info)
    
    def parse_line_height(self, line_height):
        """Parse line height value and return structured data"""
        # Remove quotes and extra spaces
        line_height = line_height.strip().strip('"\'')
        
        # Check for numeric values (unitless)
        numeric_match = re.match(r'(\d+(?:\.\d+)?)', line_height)
        if numeric_match:
            return {
                'value': float(numeric_match.group(1)),
                'type': 'unitless'
            }
        
        # Check for percentage
        percent_match = re.match(r'(\d+(?:\.\d+)?)%', line_height)
        if percent_match:
            return {
                'value': float(percent_match.group(1)),
                'type': 'percentage'
            }
        
        # Check for em/rem
        em_match = re.match(r'(\d+(?:\.\d+)?)em', line_height)
        if em_match:
            return {
                'value': float(em_match.group(1)),
                'type': 'em'
            }
        
        rem_match = re.match(r'(\d+(?:\.\d+)?)rem', line_height)
        if rem_match:
            return {
                'value': float(rem_match.group(1)),
                'type': 'rem'
            }
        
        # Check for CSS custom properties
        if line_height.startswith('var(--'):
            return {
                'value': line_height,
                'type': 'variable'
            }
        
        return None
    
    def check_line_height_issues(self, height_info):
        """Check for line height issues"""
        if height_info['type'] in ['unitless', 'percentage']:
            height_value = height_info['value']
            
            # Check for too tight line height (hard to read on mobile)
            if height_value < 1.4:
                self.issues.append({
                    'type': 'line_height_too_tight',
                    'severity': 'high',
                    'message': f"Line height {height_value} is too tight for mobile readability",
                    'file': height_info['file'],
                    'source': height_info['source'],
                    'value': height_value
                })
            
            # Check for too loose line height (wastes space)
            if height_value > 2.0:
                self.issues.append({
                    'type': 'line_height_too_loose',
                    'severity': 'medium',
                    'message': f"Line height {height_value} may be too loose for mobile",
                    'file': height_info['file'],
                    'source': height_info['source'],
                    'value': height_value
                })
    
    def analyze_font_size(self, font_size, filename, source_type):
        """Analyze font size for hierarchy"""
        font_size = font_size.strip()
        
        # Parse font size
        size_info = self.parse_font_size(font_size)
        
        if size_info:
            size_info.update({
                'file': filename,
                'source': source_type,
                'raw_value': font_size
            })
            
            self.typography_elements.append(size_info)
    
    def parse_font_size(self, font_size):
        """Parse font size value and return structured data"""
        # Remove quotes and extra spaces
        font_size = font_size.strip().strip('"\'')
        
        # Check for pixels
        px_match = re.match(r'(\d+(?:\.\d+)?)px', font_size)
        if px_match:
            return {
                'value': float(px_match.group(1)),
                'unit': 'px',
                'type': 'fixed'
            }
        
        # Check for rem
        rem_match = re.match(r'(\d+(?:\.\d+)?)rem', font_size)
        if rem_match:
            return {
                'value': float(rem_match.group(1)),
                'unit': 'rem',
                'type': 'relative'
            }
        
        # Check for em
        em_match = re.match(r'(\d+(?:\.\d+)?)em', font_size)
        if em_match:
            return {
                'value': float(em_match.group(1)),
                'unit': 'em',
                'type': 'relative'
            }
        
        # Check for CSS custom properties
        if font_size.startswith('var(--'):
            return {
                'value': font_size,
                'unit': 'css-var',
                'type': 'variable'
            }
        
        return None
    
    def analyze_css_variable(self, var_name, var_value, filename):
        """Analyze CSS custom properties for typography"""
        if 'weight' in var_name.lower():
            self.analyze_font_weight(var_value, filename, 'CSS Variable')
        elif 'height' in var_name.lower():
            self.analyze_line_height(var_value, filename, 'CSS Variable')
        elif 'size' in var_name.lower() or 'text' in var_name.lower():
            self.analyze_font_size(var_value, filename, 'CSS Variable')
    
    def analyze_paragraph(self, paragraph_text, filename):
        """Analyze paragraph content for readability"""
        # Check paragraph length
        word_count = len(paragraph_text.split())
        
        if word_count > 50:
            self.issues.append({
                'type': 'paragraph_too_long',
                'severity': 'medium',
                'message': f"Paragraph has {word_count} words, may be too long for mobile scanning",
                'file': filename,
                'type': 'HTML Paragraph',
                'word_count': word_count
            })
        
        # Check for walls of text
        if word_count > 100:
            self.issues.append({
                'type': 'wall_of_text',
                'severity': 'high',
                'message': f"Paragraph has {word_count} words, creates a wall of text on mobile",
                'file': filename,
                'type': 'HTML Paragraph',
                'word_count': word_count
            })
        
        self.content_flow.append({
            'type': 'paragraph',
            'word_count': word_count,
            'file': filename,
            'text_preview': paragraph_text[:50] + '...' if len(paragraph_text) > 50 else paragraph_text
        })
    
    def analyze_cta_element(self, cta_text, filename, cta_type):
        """Analyze call-to-action elements"""
        # Check CTA text length
        text_length = len(cta_text)
        
        if text_length < 3:
            self.issues.append({
                'type': 'cta_too_short',
                'severity': 'medium',
                'message': f"CTA text '{cta_text}' is too short for clarity",
                'file': filename,
                'type': 'CTA Element',
                'text': cta_text
            })
        
        if text_length > 50:
            self.issues.append({
                'type': 'cta_too_long',
                'severity': 'medium',
                'message': f"CTA text '{cta_text}' is too long for mobile buttons",
                'file': filename,
                'type': 'CTA Element',
                'text': cta_text
            })
        
        self.cta_elements.append({
            'type': cta_type,
            'text': cta_text,
            'length': text_length,
            'file': filename
        })
    
    def analyze_hierarchy_issues(self):
        """Analyze heading hierarchy issues"""
        if not self.heading_hierarchy:
            return
        
        # Check for missing heading levels
        levels = [h['level'] for h in self.heading_hierarchy]
        levels.sort()
        
        # Check for skipped levels
        for i in range(len(levels) - 1):
            if levels[i + 1] - levels[i] > 1:
                self.issues.append({
                    'type': 'heading_skip_level',
                    'severity': 'medium',
                    'message': f"Heading hierarchy skips from H{levels[i]} to H{levels[i + 1]}",
                    'file': 'Multiple files',
                    'type': 'Heading Hierarchy',
                    'skipped_levels': list(range(levels[i] + 1, levels[i + 1]))
                })
        
        # Check for multiple H1 elements
        h1_count = len([h for h in self.heading_hierarchy if h['level'] == 1])
        if h1_count > 1:
            self.issues.append({
                'type': 'multiple_h1',
                'severity': 'high',
                'message': f"Found {h1_count} H1 elements, should only have one per page",
                'file': 'Multiple files',
                'type': 'Heading Hierarchy',
                'h1_count': h1_count
            })
    
    def generate_report(self):
        """Generate comprehensive typography hierarchy analysis report"""
        # Analyze hierarchy issues
        self.analyze_hierarchy_issues()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_typography_elements': len(self.typography_elements),
                'total_issues': len(self.issues),
                'heading_elements': len(self.heading_hierarchy),
                'font_weights': len(self.font_weights),
                'line_heights': len(self.line_heights),
                'cta_elements': len(self.cta_elements),
                'content_flow_elements': len(self.content_flow)
            },
            'issues': self.issues,
            'heading_hierarchy': self.heading_hierarchy,
            'font_weights': self.font_weights,
            'line_heights': self.line_heights,
            'cta_elements': self.cta_elements,
            'content_flow': self.content_flow,
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self):
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Count issues by type
        issue_types = {}
        for issue in self.issues:
            issue_type = issue['type']
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        # Line height issues
        if issue_types.get('line_height_too_tight', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'Readability',
                'title': 'Improve Line Height for Mobile',
                'description': f"Found {issue_types['line_height_too_tight']} instances of line height too tight for mobile readability. Line height should be at least 1.4 for mobile devices.",
                'action': 'Increase line height to 1.4-1.6 for better mobile readability'
            })
        
        # Font weight issues
        if issue_types.get('font_weight_too_light', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'Typography',
                'title': 'Improve Font Weight Contrast',
                'description': f"Found {issue_types['font_weight_too_light']} instances of font weight too light for mobile readability.",
                'action': 'Use font weights of 400 or higher for body text on mobile'
            })
        
        # Heading hierarchy issues
        if issue_types.get('heading_skip_level', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'Structure',
                'title': 'Fix Heading Hierarchy',
                'description': f"Found {issue_types['heading_skip_level']} instances of skipped heading levels.",
                'action': 'Ensure heading hierarchy follows H1 > H2 > H3 pattern without skipping levels'
            })
        
        # Content flow issues
        if issue_types.get('wall_of_text', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'Content',
                'title': 'Break Up Long Paragraphs',
                'description': f"Found {issue_types['wall_of_text']} instances of walls of text that are difficult to scan on mobile.",
                'action': 'Break long paragraphs into shorter, scannable chunks'
            })
        
        # CTA issues
        if issue_types.get('cta_too_long', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'Conversion',
                'title': 'Optimize CTA Text Length',
                'description': f"Found {issue_types['cta_too_long']} instances of CTA text too long for mobile buttons.",
                'action': 'Keep CTA text under 30 characters for mobile optimization'
            })
        
        return recommendations

def main():
    """Main analysis function"""
    print("🔍 Typography Hierarchy Analysis for Mingus Application")
    print("=" * 70)
    
    analyzer = TypographyHierarchyAnalyzer()
    
    # Files to analyze
    files_to_analyze = [
        'landing.html',
        'responsive_typography_system.css',
        'mobile_spacing_system.css'
    ]
    
    # Analyze each file
    for file_path in files_to_analyze:
        if os.path.exists(file_path):
            analyzer.analyze_file(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    # Generate report
    report = analyzer.generate_report()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TYPOGRAPHY HIERARCHY ANALYSIS SUMMARY")
    print("=" * 70)
    
    summary = report['summary']
    print(f"📄 Total Typography Elements: {summary['total_typography_elements']}")
    print(f"🚨 Total Issues Found: {summary['total_issues']}")
    print(f"📝 Heading Elements: {summary['heading_elements']}")
    print(f"🔤 Font Weights: {summary['font_weights']}")
    print(f"📏 Line Heights: {summary['line_heights']}")
    print(f"🎯 CTA Elements: {summary['cta_elements']}")
    print(f"📖 Content Flow Elements: {summary['content_flow_elements']}")
    
    # Print critical issues
    critical_issues = [issue for issue in report['issues'] if issue['severity'] == 'critical']
    if critical_issues:
        print(f"\n🚨 CRITICAL ISSUES ({len(critical_issues)}):")
        for issue in critical_issues:
            print(f"  • {issue['message']} ({issue['file']})")
    
    # Print high priority issues
    high_issues = [issue for issue in report['issues'] if issue['severity'] == 'high']
    if high_issues:
        print(f"\n⚠️  HIGH PRIORITY ISSUES ({len(high_issues)}):")
        for issue in high_issues[:5]:  # Show first 5
            print(f"  • {issue['message']} ({issue['file']})")
        if len(high_issues) > 5:
            print(f"  ... and {len(high_issues) - 5} more")
    
    # Print heading hierarchy
    if report['heading_hierarchy']:
        print(f"\n📝 HEADING HIERARCHY ({len(report['heading_hierarchy'])} elements):")
        for heading in report['heading_hierarchy'][:5]:  # Show first 5
            print(f"  • H{heading['level']}: {heading['text'][:50]}... ({heading['file']})")
        if len(report['heading_hierarchy']) > 5:
            print(f"  ... and {len(report['heading_hierarchy']) - 5} more")
    
    # Print recommendations
    print(f"\n💡 RECOMMENDATIONS ({len(report['recommendations'])}):")
    for rec in report['recommendations']:
        print(f"  • {rec['title']}: {rec['description']}")
    
    # Save detailed report
    report_filename = f"typography_hierarchy_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    print("✅ Typography hierarchy analysis complete!")

if __name__ == "__main__":
    main()
