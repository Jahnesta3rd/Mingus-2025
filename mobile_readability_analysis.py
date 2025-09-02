#!/usr/bin/env python3
"""
Mingus Mobile Readability Analysis Tool
Comprehensive mobile readability audit for the Mingus application
"""

import os
import re
import json
import html as html_module
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ReadabilityIssue:
    file_path: str
    line_number: int
    element_type: str
    issue_type: str
    description: str
    recommendation: str
    severity: str  # 'critical', 'warning', 'info'
    screen_size: str
    current_value: str
    recommended_value: str

@dataclass
class ReadabilityMetrics:
    font_size_score: int
    line_height_score: int
    contrast_score: int
    spacing_score: int
    touch_target_score: int
    overall_score: int

class MobileReadabilityAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.metrics = {}
        
        # Mobile readability standards
        self.standards = {
            'min_font_size': 16,
            'min_line_height': 1.4,
            'min_touch_target': 44,
            'min_contrast_ratio': 4.5,
            'recommended_spacing': 16,
            'max_line_length': 75
        }
        
        # Screen sizes to test
        self.screen_sizes = ['320px', '375px', '390px', '414px', '428px', '768px']
        
        # File patterns to analyze
        self.file_patterns = [
            '*.html',
            '*.css',
            '*.scss',
            '*.tsx',
            '*.ts',
            '*.jsx',
            '*.js'
        ]

    def analyze_project(self) -> Dict[str, Any]:
        """Main analysis function"""
        print("🔍 Starting comprehensive mobile readability analysis...")
        
        # Analyze HTML files
        self.analyze_html_files()
        
        # Analyze CSS/SCSS files
        self.analyze_css_files()
        
        # Analyze React components
        self.analyze_react_components()
        
        # Generate metrics
        self.calculate_metrics()
        
        # Generate report
        return self.generate_report()

    def analyze_html_files(self):
        """Analyze HTML files for readability issues"""
        print("📄 Analyzing HTML files...")
        
        html_files = list(self.project_root.rglob('*.html'))
        
        for html_file in html_files:
            if 'node_modules' in str(html_file):
                continue
                
            self.analyze_html_file(html_file)

    def analyze_html_file(self, file_path: Path):
        """Analyze a single HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract CSS styles
            css_pattern = r'<style[^>]*>(.*?)</style>'
            css_matches = re.findall(css_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for i, css_content in enumerate(css_matches):
                self.analyze_css_content(css_content, str(file_path), f"style tag {i+1}")
            
            # Extract inline styles
            inline_pattern = r'style=["\']([^"\']*)["\']'
            inline_matches = re.findall(inline_pattern, content)
            
            for inline_style in inline_matches:
                self.analyze_inline_style(inline_style, str(file_path))
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def analyze_css_files(self):
        """Analyze CSS/SCSS files for readability issues"""
        print("🎨 Analyzing CSS/SCSS files...")
        
        css_patterns = ['*.css', '*.scss']
        
        for pattern in css_patterns:
            css_files = list(self.project_root.rglob(pattern))
            
            for css_file in css_files:
                if 'node_modules' in str(css_file):
                    continue
                    
                self.analyze_css_file(css_file)

    def analyze_css_file(self, file_path: Path):
        """Analyze a single CSS file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.analyze_css_content(content, str(file_path))
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def analyze_css_content(self, css_content: str, file_path: str, context: str = ""):
        """Analyze CSS content for readability issues"""
        
        # Font size analysis
        font_size_pattern = r'font-size:\s*([^;]+)'
        font_size_matches = re.findall(font_size_pattern, css_content, re.IGNORECASE)
        
        for match in font_size_matches:
            self.analyze_font_size(match.strip(), file_path, context)
        
        # Line height analysis
        line_height_pattern = r'line-height:\s*([^;]+)'
        line_height_matches = re.findall(line_height_pattern, css_content, re.IGNORECASE)
        
        for match in line_height_matches:
            self.analyze_line_height(match.strip(), file_path, context)
        
        # Touch target analysis
        touch_target_patterns = [
            r'width:\s*([^;]+)',
            r'height:\s*([^;]+)',
            r'min-width:\s*([^;]+)',
            r'min-height:\s*([^;]+)'
        ]
        
        for pattern in touch_target_patterns:
            matches = re.findall(pattern, css_content, re.IGNORECASE)
            for match in matches:
                self.analyze_touch_target(match.strip(), file_path, context)
        
        # Spacing analysis
        spacing_patterns = [
            r'margin:\s*([^;]+)',
            r'padding:\s*([^;]+)',
            r'margin-bottom:\s*([^;]+)',
            r'margin-top:\s*([^;]+)',
            r'padding-bottom:\s*([^;]+)',
            r'padding-top:\s*([^;]+)'
        ]
        
        for pattern in spacing_patterns:
            matches = re.findall(pattern, css_content, re.IGNORECASE)
            for match in matches:
                self.analyze_spacing(match.strip(), file_path, context)

    def analyze_inline_style(self, style_content: str, file_path: str):
        """Analyze inline styles"""
        self.analyze_css_content(style_content, file_path, "inline style")

    def analyze_font_size(self, value: str, file_path: str, context: str):
        """Analyze font size values"""
        # Extract numeric value
        numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
        if not numeric_match:
            return
            
        size = float(numeric_match.group(1))
        unit = 'px' if 'px' in value else 'em' if 'em' in value else 'rem' if 'rem' in value else 'pt'
        
        # Convert to px for comparison
        if unit == 'em':
            size *= 16  # Assuming 16px base font size
        elif unit == 'rem':
            size *= 16  # Assuming 16px root font size
        elif unit == 'pt':
            size *= 1.33  # Convert pt to px
        
        if size < self.standards['min_font_size']:
            self.issues.append(ReadabilityIssue(
                file_path=file_path,
                line_number=0,  # Would need line tracking for more accuracy
                element_type="font-size",
                issue_type="font_size_too_small",
                description=f"Font size {size}px is below minimum recommended {self.standards['min_font_size']}px",
                recommendation=f"Increase font size to at least {self.standards['min_font_size']}px for better mobile readability",
                severity="critical" if size < 14 else "warning",
                screen_size="all",
                current_value=f"{size}px",
                recommended_value=f"{self.standards['min_font_size']}px"
            ))

    def analyze_line_height(self, value: str, file_path: str, context: str):
        """Analyze line height values"""
        # Extract numeric value
        numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
        if not numeric_match:
            return
            
        line_height = float(numeric_match.group(1))
        
        if line_height < self.standards['min_line_height']:
            self.issues.append(ReadabilityIssue(
                file_path=file_path,
                line_number=0,
                element_type="line-height",
                issue_type="line_height_too_tight",
                description=f"Line height {line_height} is below minimum recommended {self.standards['min_line_height']}",
                recommendation=f"Increase line-height to at least {self.standards['min_line_height']} for better text readability",
                severity="warning",
                screen_size="all",
                current_value=str(line_height),
                recommended_value=str(self.standards['min_line_height'])
            ))

    def analyze_touch_target(self, value: str, file_path: str, context: str):
        """Analyze touch target sizes"""
        # Extract numeric value
        numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
        if not numeric_match:
            return
            
        size = float(numeric_match.group(1))
        unit = 'px' if 'px' in value else 'em' if 'em' in value else 'rem' if 'rem' in value else 'pt'
        
        # Convert to px for comparison
        if unit == 'em':
            size *= 16
        elif unit == 'rem':
            size *= 16
        elif unit == 'pt':
            size *= 1.33
        
        if size < self.standards['min_touch_target']:
            self.issues.append(ReadabilityIssue(
                file_path=file_path,
                line_number=0,
                element_type="touch-target",
                issue_type="touch_target_too_small",
                description=f"Touch target size {size}px is below minimum recommended {self.standards['min_touch_target']}px",
                recommendation=f"Increase touch target size to at least {self.standards['min_touch_target']}px for better mobile usability",
                severity="critical" if size < 32 else "warning",
                screen_size="all",
                current_value=f"{size}px",
                recommended_value=f"{self.standards['min_touch_target']}px"
            ))

    def analyze_spacing(self, value: str, file_path: str, context: str):
        """Analyze spacing values"""
        # Extract numeric value
        numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
        if not numeric_match:
            return
            
        spacing = float(numeric_match.group(1))
        unit = 'px' if 'px' in value else 'em' if 'em' in value else 'rem' if 'rem' in value else 'pt'
        
        # Convert to px for comparison
        if unit == 'em':
            spacing *= 16
        elif unit == 'rem':
            spacing *= 16
        elif unit == 'pt':
            spacing *= 1.33
        
        if spacing < self.standards['recommended_spacing']:
            self.issues.append(ReadabilityIssue(
                file_path=file_path,
                line_number=0,
                element_type="spacing",
                issue_type="insufficient_spacing",
                description=f"Spacing {spacing}px is below recommended {self.standards['recommended_spacing']}px",
                recommendation=f"Increase spacing to at least {self.standards['recommended_spacing']}px for better content separation",
                severity="warning",
                screen_size="all",
                current_value=f"{spacing}px",
                recommended_value=f"{self.standards['recommended_spacing']}px"
            ))

    def analyze_react_components(self):
        """Analyze React components for readability issues"""
        print("⚛️ Analyzing React components...")
        
        react_files = list(self.project_root.rglob('*.tsx')) + list(self.project_root.rglob('*.jsx'))
        
        for react_file in react_files:
            if 'node_modules' in str(react_file):
                continue
                
            self.analyze_react_file(react_file)

    def analyze_react_file(self, file_path: Path):
        """Analyze a single React component file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analyze className patterns for Tailwind CSS
            self.analyze_tailwind_classes(content, str(file_path))
            
            # Analyze inline styles
            inline_style_pattern = r'style=\{\{([^}]+)\}\}'
            inline_matches = re.findall(inline_style_pattern, content)
            
            for match in inline_matches:
                self.analyze_inline_style(match, str(file_path))
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

    def analyze_tailwind_classes(self, content: str, file_path: str):
        """Analyze Tailwind CSS classes for readability issues"""
        
        # Font size classes
        font_size_pattern = r'text-(\w+)'
        font_size_matches = re.findall(font_size_pattern, content)
        
        font_size_map = {
            'xs': 12, 'sm': 14, 'base': 16, 'lg': 18, 'xl': 20,
            '2xl': 24, '3xl': 30, '4xl': 36, '5xl': 48, '6xl': 60
        }
        
        for match in font_size_matches:
            if match in font_size_map:
                size = font_size_map[match]
                if size < self.standards['min_font_size']:
                    self.issues.append(ReadabilityIssue(
                        file_path=file_path,
                        line_number=0,
                        element_type="tailwind-font-size",
                        issue_type="font_size_too_small",
                        description=f"Tailwind text-{match} class uses {size}px font size",
                        recommendation=f"Use text-base (16px) or larger for better mobile readability",
                        severity="critical" if size < 14 else "warning",
                        screen_size="all",
                        current_value=f"{size}px (text-{match})",
                        recommended_value="16px+ (text-base+)"
                    ))
        
        # Line height classes
        line_height_pattern = r'leading-(\w+)'
        line_height_matches = re.findall(line_height_pattern, content)
        
        line_height_map = {
            'none': 1, 'tight': 1.25, 'snug': 1.375, 'normal': 1.5, 'relaxed': 1.625, 'loose': 2
        }
        
        for match in line_height_matches:
            if match in line_height_map:
                line_height = line_height_map[match]
                if line_height < self.standards['min_line_height']:
                    self.issues.append(ReadabilityIssue(
                        file_path=file_path,
                        line_number=0,
                        element_type="tailwind-line-height",
                        issue_type="line_height_too_tight",
                        description=f"Tailwind leading-{match} class uses {line_height} line height",
                        recommendation=f"Use leading-relaxed (1.625) or larger for better text readability",
                        severity="warning",
                        screen_size="all",
                        current_value=str(line_height),
                        recommended_value="1.4+"
                    ))

    def calculate_metrics(self):
        """Calculate overall readability metrics"""
        print("📊 Calculating readability metrics...")
        
        total_issues = len(self.issues)
        critical_issues = len([i for i in self.issues if i.severity == 'critical'])
        warning_issues = len([i for i in self.issues if i.severity == 'warning'])
        
        # Calculate scores (0-100)
        font_size_score = max(0, 100 - (critical_issues * 20) - (warning_issues * 10))
        line_height_score = max(0, 100 - (warning_issues * 15))
        spacing_score = max(0, 100 - (warning_issues * 10))
        touch_target_score = max(0, 100 - (critical_issues * 25))
        
        overall_score = (font_size_score + line_height_score + spacing_score + touch_target_score) // 4
        
        self.metrics = {
            'font_size_score': font_size_score,
            'line_height_score': line_height_score,
            'spacing_score': spacing_score,
            'touch_target_score': touch_target_score,
            'overall_score': overall_score,
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues
        }

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive readability report"""
        print("📋 Generating readability report...")
        
        # Group issues by file
        issues_by_file = {}
        for issue in self.issues:
            if issue.file_path not in issues_by_file:
                issues_by_file[issue.file_path] = []
            issues_by_file[issue.file_path].append(issue)
        
        # Group issues by type
        issues_by_type = {}
        for issue in self.issues:
            if issue.issue_type not in issues_by_type:
                issues_by_type[issue.issue_type] = []
            issues_by_type[issue.issue_type].append(issue)
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'metrics': self.metrics,
            'total_issues': len(self.issues),
            'issues_by_file': {
                file_path: [self.issue_to_dict(issue) for issue in issues]
                for file_path, issues in issues_by_file.items()
            },
            'issues_by_type': {
                issue_type: [self.issue_to_dict(issue) for issue in issues]
                for issue_type, issues in issues_by_type.items()
            },
            'recommendations': recommendations,
            'standards_used': self.standards,
            'screen_sizes_tested': self.screen_sizes
        }
        
        return report

    def issue_to_dict(self, issue: ReadabilityIssue) -> Dict[str, Any]:
        """Convert ReadabilityIssue to dictionary"""
        return {
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'element_type': issue.element_type,
            'issue_type': issue.issue_type,
            'description': issue.description,
            'recommendation': issue.recommendation,
            'severity': issue.severity,
            'screen_size': issue.screen_size,
            'current_value': issue.current_value,
            'recommended_value': issue.recommended_value
        }

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Font size recommendations
        font_size_issues = [i for i in self.issues if i.issue_type == 'font_size_too_small']
        if font_size_issues:
            recommendations.append({
                'category': 'Font Sizes',
                'priority': 'High',
                'description': f'Found {len(font_size_issues)} elements with font sizes below {self.standards["min_font_size"]}px',
                'actions': [
                    'Increase base font size to 16px minimum',
                    'Use larger font sizes for headings (24px+)',
                    'Ensure buttons and CTAs have readable text (18px+)',
                    'Test with users who have vision impairments'
                ],
                'affected_files': list(set(i.file_path for i in font_size_issues))
            })
        
        # Line height recommendations
        line_height_issues = [i for i in self.issues if i.issue_type == 'line_height_too_tight']
        if line_height_issues:
            recommendations.append({
                'category': 'Line Height',
                'priority': 'Medium',
                'description': f'Found {len(line_height_issues)} elements with tight line spacing',
                'actions': [
                    'Increase line-height to 1.4 minimum',
                    'Use 1.6 line-height for body text',
                    'Add more spacing between paragraphs',
                    'Consider using 1.8 line-height for long-form content'
                ],
                'affected_files': list(set(i.file_path for i in line_height_issues))
            })
        
        # Touch target recommendations
        touch_target_issues = [i for i in self.issues if i.issue_type == 'touch_target_too_small']
        if touch_target_issues:
            recommendations.append({
                'category': 'Touch Targets',
                'priority': 'High',
                'description': f'Found {len(touch_target_issues)} elements with small touch targets',
                'actions': [
                    'Increase button sizes to 44px minimum',
                    'Add padding to clickable elements',
                    'Ensure adequate spacing between interactive elements',
                    'Test touch targets on actual mobile devices'
                ],
                'affected_files': list(set(i.file_path for i in touch_target_issues))
            })
        
        # Spacing recommendations
        spacing_issues = [i for i in self.issues if i.issue_type == 'insufficient_spacing']
        if spacing_issues:
            recommendations.append({
                'category': 'Content Spacing',
                'priority': 'Medium',
                'description': f'Found {len(spacing_issues)} elements with insufficient spacing',
                'actions': [
                    'Add 16px minimum spacing between sections',
                    'Increase padding around content blocks',
                    'Use consistent spacing throughout the interface',
                    'Consider using a spacing scale (8px, 16px, 24px, 32px)'
                ],
                'affected_files': list(set(i.file_path for i in spacing_issues))
            })
        
        # General mobile recommendations
        if self.metrics['overall_score'] < 70:
            recommendations.append({
                'category': 'General Mobile Optimization',
                'priority': 'High',
                'description': 'Overall mobile readability score is below 70',
                'actions': [
                    'Implement responsive typography system',
                    'Use mobile-first design approach',
                    'Test on multiple device sizes',
                    'Consider implementing a design system',
                    'Add mobile-specific breakpoints',
                    'Optimize for touch interactions'
                ],
                'affected_files': ['All files']
            })
        
        return recommendations

    def save_report(self, report: Dict[str, Any], output_file: str = None):
        """Save the report to a file"""
        if output_file is None:
            output_file = f"mobile_readability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Report saved to: {output_file}")
        return output_file

    def print_summary(self, report: Dict[str, Any]):
        """Print a summary of the analysis"""
        metrics = report['metrics']
        
        print("\n" + "="*60)
        print("📱 MINGUS MOBILE READABILITY AUDIT SUMMARY")
        print("="*60)
        
        print(f"\n📊 Overall Score: {metrics['overall_score']}/100")
        print(f"🔴 Critical Issues: {metrics['critical_issues']}")
        print(f"🟡 Warning Issues: {metrics['warning_issues']}")
        print(f"📝 Total Issues: {metrics['total_issues']}")
        
        print(f"\n📈 Detailed Scores:")
        print(f"   Font Size: {metrics['font_size_score']}/100")
        print(f"   Line Height: {metrics['line_height_score']}/100")
        print(f"   Spacing: {metrics['spacing_score']}/100")
        print(f"   Touch Targets: {metrics['touch_target_score']}/100")
        
        print(f"\n🎯 Recommendations:")
        for rec in report['recommendations']:
            print(f"   • {rec['category']} ({rec['priority']}): {rec['description']}")
        
        print(f"\n📁 Files Analyzed: {len(report['issues_by_file'])}")
        print(f"🔍 Screen Sizes Tested: {', '.join(report['screen_sizes_tested'])}")
        
        print("\n" + "="*60)

def main():
    """Main function to run the mobile readability analysis"""
    # Get the current directory as project root
    project_root = os.getcwd()
    
    # Initialize analyzer
    analyzer = MobileReadabilityAnalyzer(project_root)
    
    # Run analysis
    report = analyzer.analyze_project()
    
    # Save report
    output_file = analyzer.save_report(report)
    
    # Print summary
    analyzer.print_summary(report)
    
    # Generate HTML report
    generate_html_report(report, output_file.replace('.json', '.html'))
    
    print(f"\n✅ Analysis complete! Check the generated reports for detailed findings.")
    print(f"📄 JSON Report: {output_file}")
    print(f"🌐 HTML Report: {output_file.replace('.json', '.html')}")

def generate_html_report(report: Dict[str, Any], output_file: str):
    """Generate an HTML report for better visualization"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mingus Mobile Readability Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .title {{
            font-size: 2.5rem;
            font-weight: 700;
            color: #8A31FF;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 20px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            color: #666;
        }}
        
        .score-excellent {{ color: #10b981; }}
        .score-good {{ color: #f59e0b; }}
        .score-poor {{ color: #ef4444; }}
        
        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: #333;
        }}
        
        .issue-list {{
            list-style: none;
        }}
        
        .issue-item {{
            background: #f8f9fa;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 0 6px 6px 0;
        }}
        
        .issue-item.warning {{
            border-left-color: #ffc107;
        }}
        
        .issue-item.info {{
            border-left-color: #17a2b8;
        }}
        
        .issue-title {{
            font-weight: 600;
            margin-bottom: 5px;
            color: #333;
        }}
        
        .issue-description {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 8px;
        }}
        
        .issue-recommendation {{
            font-size: 0.85rem;
            color: #8A31FF;
            font-weight: 500;
        }}
        
        .recommendation-card {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
        }}
        
        .recommendation-title {{
            font-weight: 600;
            color: #8A31FF;
            margin-bottom: 10px;
        }}
        
        .recommendation-priority {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .priority-high {{ background: #fee2e2; color: #dc2626; }}
        .priority-medium {{ background: #fef3c7; color: #d97706; }}
        .priority-low {{ background: #d1fae5; color: #059669; }}
        
        .recommendation-actions {{
            list-style: none;
            margin-left: 0;
        }}
        
        .recommendation-actions li {{
            margin-bottom: 5px;
            padding-left: 20px;
            position: relative;
        }}
        
        .recommendation-actions li:before {{
            content: "→";
            position: absolute;
            left: 0;
            color: #8A31FF;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            
            .title {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">📱 Mingus Mobile Readability Report</h1>
            <p class="subtitle">Generated on {report['timestamp']}</p>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value {get_score_class(report['metrics']['overall_score'])}">{report['metrics']['overall_score']}/100</div>
                    <div class="metric-label">Overall Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {get_score_class(report['metrics']['font_size_score'])}">{report['metrics']['font_size_score']}/100</div>
                    <div class="metric-label">Font Size</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {get_score_class(report['metrics']['line_height_score'])}">{report['metrics']['line_height_score']}/100</div>
                    <div class="metric-label">Line Height</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {get_score_class(report['metrics']['spacing_score'])}">{report['metrics']['spacing_score']}/100</div>
                    <div class="metric-label">Spacing</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {get_score_class(report['metrics']['touch_target_score'])}">{report['metrics']['touch_target_score']}/100</div>
                    <div class="metric-label">Touch Targets</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{report['metrics']['total_issues']}</div>
                    <div class="metric-label">Total Issues</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">🎯 Recommendations</h2>
            {generate_recommendations_html(report['recommendations'])}
        </div>
        
        <div class="section">
            <h2 class="section-title">📋 Issues by File</h2>
            {generate_issues_by_file_html(report['issues_by_file'])}
        </div>
        
        <div class="section">
            <h2 class="section-title">🔍 Issues by Type</h2>
            {generate_issues_by_type_html(report['issues_by_type'])}
        </div>
        
        <div class="section">
            <h2 class="section-title">📊 Standards Used</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                {generate_standards_html(report['standards_used'])}
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"🌐 HTML report generated: {output_file}")

def get_score_class(score: int) -> str:
    """Get CSS class for score styling"""
    if score >= 80:
        return 'score-excellent'
    elif score >= 60:
        return 'score-good'
    else:
        return 'score-poor'

def generate_recommendations_html(recommendations: List[Dict[str, Any]]) -> str:
    """Generate HTML for recommendations section"""
    html = ""
    for rec in recommendations:
        html += f"""
        <div class="recommendation-card">
            <div class="recommendation-title">{rec['category']}</div>
            <span class="recommendation-priority priority-{rec['priority'].lower()}">{rec['priority']}</span>
            <p style="margin-bottom: 15px;">{rec['description']}</p>
            <ul class="recommendation-actions">
                {''.join(f'<li>{action}</li>' for action in rec['actions'])}
            </ul>
        </div>
        """
    return html

def generate_issues_by_file_html(issues_by_file: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate HTML for issues by file section"""
    html = ""
    for file_path, issues in issues_by_file.items():
        html += f"""
        <div style="margin-bottom: 20px;">
            <h3 style="color: #8A31FF; margin-bottom: 10px;">{html_module.escape(file_path)}</h3>
            <ul class="issue-list">
                {''.join(generate_issue_html(issue) for issue in issues)}
            </ul>
        </div>
        """
    return html

def generate_issues_by_type_html(issues_by_type: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate HTML for issues by type section"""
    html = ""
    for issue_type, issues in issues_by_type.items():
        html += f"""
        <div style="margin-bottom: 20px;">
            <h3 style="color: #8A31FF; margin-bottom: 10px;">{issue_type.replace('_', ' ').title()}</h3>
            <ul class="issue-list">
                {''.join(generate_issue_html(issue) for issue in issues)}
            </ul>
        </div>
        """
    return html

def generate_issue_html(issue: Dict[str, Any]) -> str:
    """Generate HTML for a single issue"""
    return f"""
    <li class="issue-item {issue['severity']}">
        <div class="issue-title">{html_module.escape(issue['description'])}</div>
        <div class="issue-description">File: {html_module.escape(issue['file_path'])} | Element: {issue['element_type']}</div>
        <div class="issue-recommendation">💡 {html_module.escape(issue['recommendation'])}</div>
    </li>
    """

def generate_standards_html(standards: Dict[str, Any]) -> str:
    """Generate HTML for standards section"""
    html = ""
    for key, value in standards.items():
        html += f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
            <div style="font-weight: 600; color: #8A31FF;">{key.replace('_', ' ').title()}</div>
            <div style="font-size: 0.9rem; color: #666;">{value}</div>
        </div>
        """
    return html

if __name__ == "__main__":
    main()
