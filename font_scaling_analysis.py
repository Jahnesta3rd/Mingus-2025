#!/usr/bin/env python3
"""
Font Scaling Analysis for Mingus Application
Analyzes font sizing and scaling issues across mobile devices and zoom levels
"""

import re
import json
import os
from datetime import datetime
from pathlib import Path

class FontScalingAnalyzer:
    def __init__(self):
        self.issues = []
        self.font_sizes = []
        self.heading_sizes = []
        self.button_sizes = []
        self.navigation_sizes = []
        self.fixed_sizes = []
        self.responsive_sizes = []
        
    def analyze_file(self, file_path):
        """Analyze a single file for font sizing issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = os.path.basename(file_path)
            print(f"📄 Analyzing {filename}...")
            
            # Analyze CSS/HTML content
            self.analyze_css_content(content, filename)
            self.analyze_html_content(content, filename)
            
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
    
    def analyze_css_content(self, content, filename):
        """Analyze CSS content for font sizing issues"""
        # Find all font-size declarations
        font_size_pattern = r'font-size:\s*([^;]+);'
        font_sizes = re.findall(font_size_pattern, content, re.IGNORECASE)
        
        for font_size in font_sizes:
            font_size = font_size.strip()
            self.analyze_font_size(font_size, filename, 'CSS')
        
        # Find CSS custom properties
        css_var_pattern = r'--text-[^:]+:\s*([^;]+);'
        css_vars = re.findall(css_var_pattern, content, re.IGNORECASE)
        
        for css_var in css_vars:
            css_var = css_var.strip()
            self.analyze_font_size(css_var, filename, 'CSS Variable')
        
        # Find media queries
        media_pattern = r'@media[^{]+{([^}]+)}'
        media_queries = re.findall(media_pattern, content, re.DOTALL)
        
        for media_query in media_queries:
            self.analyze_media_query(media_query, filename)
    
    def analyze_html_content(self, content, filename):
        """Analyze HTML content for font sizing issues"""
        # Find inline styles
        inline_style_pattern = r'style="[^"]*font-size:\s*([^;"]+)[^"]*"'
        inline_styles = re.findall(inline_style_pattern, content, re.IGNORECASE)
        
        for inline_style in inline_styles:
            inline_style = inline_style.strip()
            self.analyze_font_size(inline_style, filename, 'Inline Style')
        
        # Find heading elements
        heading_pattern = r'<h([1-6])[^>]*>'
        headings = re.findall(heading_pattern, content, re.IGNORECASE)
        
        for heading_level in headings:
            self.heading_sizes.append({
                'level': f'H{heading_level}',
                'file': filename,
                'type': 'HTML Element'
            })
    
    def analyze_font_size(self, font_size, filename, source_type):
        """Analyze individual font size value"""
        font_size = font_size.strip()
        
        # Parse different font size formats
        size_info = self.parse_font_size(font_size)
        
        if size_info:
            size_info.update({
                'file': filename,
                'source': source_type,
                'raw_value': font_size
            })
            
            self.font_sizes.append(size_info)
            
            # Check for issues
            self.check_font_size_issues(size_info)
    
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
        
        # Check for percentage
        percent_match = re.match(r'(\d+(?:\.\d+)?)%', font_size)
        if percent_match:
            return {
                'value': float(percent_match.group(1)),
                'unit': '%',
                'type': 'relative'
            }
        
        # Check for viewport units
        vw_match = re.match(r'(\d+(?:\.\d+)?)vw', font_size)
        if vw_match:
            return {
                'value': float(vw_match.group(1)),
                'unit': 'vw',
                'type': 'responsive'
            }
        
        vh_match = re.match(r'(\d+(?:\.\d+)?)vh', font_size)
        if vh_match:
            return {
                'value': float(vh_match.group(1)),
                'unit': 'vh',
                'type': 'responsive'
            }
        
        # Check for CSS custom properties
        if font_size.startswith('var(--'):
            return {
                'value': font_size,
                'unit': 'css-var',
                'type': 'variable'
            }
        
        return None
    
    def check_font_size_issues(self, size_info):
        """Check for specific font sizing issues"""
        if size_info['unit'] == 'px':
            # Check for mobile minimum (16px)
            if size_info['value'] < 16:
                self.issues.append({
                    'type': 'mobile_minimum',
                    'severity': 'high',
                    'message': f"Font size {size_info['value']}px is below mobile minimum of 16px",
                    'file': size_info['file'],
                    'source': size_info['source'],
                    'value': size_info['value']
                })
            
            # Check for very small text (below 12px)
            if size_info['value'] < 12:
                self.issues.append({
                    'type': 'too_small',
                    'severity': 'critical',
                    'message': f"Font size {size_info['value']}px is too small for readability",
                    'file': size_info['file'],
                    'source': size_info['source'],
                    'value': size_info['value']
                })
            
            # Check for very large text (above 48px)
            if size_info['value'] > 48:
                self.issues.append({
                    'type': 'too_large',
                    'severity': 'medium',
                    'message': f"Font size {size_info['value']}px may be too large for mobile",
                    'file': size_info['file'],
                    'source': size_info['source'],
                    'value': size_info['value']
                })
        
        # Check for fixed sizes that don't scale
        if size_info['type'] == 'fixed':
            self.fixed_sizes.append(size_info)
            self.issues.append({
                'type': 'fixed_size',
                'severity': 'medium',
                'message': f"Fixed font size {size_info['raw_value']} may not scale properly",
                'file': size_info['file'],
                'source': size_info['source'],
                'value': size_info['raw_value']
            })
        
        # Check for responsive sizes
        if size_info['type'] == 'responsive':
            self.responsive_sizes.append(size_info)
    
    def analyze_media_query(self, media_content, filename):
        """Analyze media query content for responsive font sizing"""
        # Look for font-size declarations in media queries
        font_size_pattern = r'font-size:\s*([^;]+);'
        font_sizes = re.findall(font_size_pattern, media_content, re.IGNORECASE)
        
        for font_size in font_sizes:
            font_size = font_size.strip()
            self.analyze_font_size(font_size, filename, 'Media Query')
    
    def generate_report(self):
        """Generate comprehensive font scaling analysis report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_font_sizes': len(self.font_sizes),
                'total_issues': len(self.issues),
                'fixed_sizes': len(self.fixed_sizes),
                'responsive_sizes': len(self.responsive_sizes),
                'heading_elements': len(self.heading_sizes)
            },
            'issues': self.issues,
            'font_sizes': self.font_sizes,
            'headings': self.heading_sizes,
            'fixed_sizes': self.fixed_sizes,
            'responsive_sizes': self.responsive_sizes,
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
        
        # Mobile minimum issues
        if issue_types.get('mobile_minimum', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'Mobile Readability',
                'title': 'Increase Font Sizes Below 16px',
                'description': f"Found {issue_types['mobile_minimum']} font sizes below the mobile minimum of 16px. These should be increased to ensure readability on mobile devices.",
                'action': 'Update all font sizes below 16px to meet mobile minimum standards'
            })
        
        # Fixed size issues
        if issue_types.get('fixed_size', 0) > 0:
            recommendations.append({
                'priority': 'medium',
                'category': 'Responsive Design',
                'title': 'Replace Fixed Font Sizes',
                'description': f"Found {issue_types['fixed_size']} fixed font sizes that don't scale responsively. Consider using relative units (rem, em) or CSS custom properties.",
                'action': 'Convert fixed pixel values to relative units or CSS variables'
            })
        
        # Too small issues
        if issue_types.get('too_small', 0) > 0:
            recommendations.append({
                'priority': 'critical',
                'category': 'Accessibility',
                'title': 'Fix Extremely Small Font Sizes',
                'description': f"Found {issue_types['too_small']} font sizes below 12px. These are too small for any device and should be increased immediately.",
                'action': 'Increase all font sizes below 12px to at least 14px'
            })
        
        # Responsive design recommendations
        if len(self.responsive_sizes) < len(self.fixed_sizes):
            recommendations.append({
                'priority': 'medium',
                'category': 'Responsive Design',
                'title': 'Improve Responsive Font Scaling',
                'description': f"Only {len(self.responsive_sizes)} responsive font sizes found vs {len(self.fixed_sizes)} fixed sizes. Consider implementing a responsive typography system.",
                'action': 'Implement CSS custom properties and media queries for responsive font scaling'
            })
        
        return recommendations

def main():
    """Main analysis function"""
    print("🔍 Font Scaling Analysis for Mingus Application")
    print("=" * 60)
    
    analyzer = FontScalingAnalyzer()
    
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
    print("\n" + "=" * 60)
    print("📊 FONT SCALING ANALYSIS SUMMARY")
    print("=" * 60)
    
    summary = report['summary']
    print(f"📄 Total Font Sizes Analyzed: {summary['total_font_sizes']}")
    print(f"🚨 Total Issues Found: {summary['total_issues']}")
    print(f"📏 Fixed Sizes: {summary['fixed_sizes']}")
    print(f"📱 Responsive Sizes: {summary['responsive_sizes']}")
    print(f"📝 Heading Elements: {summary['heading_elements']}")
    
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
    
    # Print recommendations
    print(f"\n💡 RECOMMENDATIONS ({len(report['recommendations'])}):")
    for rec in report['recommendations']:
        print(f"  • {rec['title']}: {rec['description']}")
    
    # Save detailed report
    report_filename = f"font_scaling_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    print("✅ Font scaling analysis complete!")

if __name__ == "__main__":
    main()
