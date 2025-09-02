#!/usr/bin/env python3
"""
Focused Mobile Readability Audit for Mingus Application
Targets main application files for specific mobile readability improvements
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MobileIssue:
    file_path: str
    element: str
    issue_type: str
    description: str
    recommendation: str
    severity: str
    current_value: str
    recommended_value: str

class FocusedMobileAuditor:
    def __init__(self):
        self.issues = []
        self.target_files = [
            'landing.html',
            'ai-job-impact-calculator.html',
            'src/components/onboarding/WelcomeStep.tsx',
            'src/components/onboarding/ProfileStep.tsx',
            'src/components/onboarding/PreferencesStep.tsx',
            'src/App.tsx'
        ]
        
        self.mobile_standards = {
            'min_font_size': 16,
            'min_line_height': 1.4,
            'min_touch_target': 44,
            'min_spacing': 16,
            'max_line_length': 75
        }

    def run_audit(self):
        """Run focused mobile readability audit"""
        print("🔍 Running focused mobile readability audit...")
        
        # Analyze landing page
        self.analyze_landing_page()
        
        # Analyze calculator page
        self.analyze_calculator_page()
        
        # Analyze React components
        self.analyze_react_components()
        
        # Generate report
        return self.generate_focused_report()

    def analyze_landing_page(self):
        """Analyze landing.html for mobile readability issues"""
        print("📄 Analyzing landing page...")
        
        try:
            with open('landing.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract CSS styles
            css_pattern = r'<style[^>]*>(.*?)</style>'
            css_matches = re.findall(css_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for css_content in css_matches:
                self.analyze_landing_css(css_content)
                
        except FileNotFoundError:
            print("⚠️ landing.html not found")
        except Exception as e:
            print(f"Error analyzing landing page: {e}")

    def analyze_landing_css(self, css_content: str):
        """Analyze landing page CSS for mobile issues"""
        
        # Check hero section font sizes
        hero_headline_match = re.search(r'\.hero-headline\s*\{[^}]*font-size:\s*([^;]+)', css_content)
        if hero_headline_match:
            font_size = self.extract_numeric_value(hero_headline_match.group(1))
            if font_size and font_size < 28:  # Should be larger on mobile
                self.issues.append(MobileIssue(
                    file_path='landing.html',
                    element='.hero-headline',
                    issue_type='font_size_too_small',
                    description=f'Hero headline font size ({font_size}px) may be too small on mobile devices',
                    recommendation='Increase hero headline font size to 32px+ for better mobile readability',
                    severity='warning',
                    current_value=f'{font_size}px',
                    recommended_value='32px+'
                ))

        # Check hero subtext
        hero_subtext_match = re.search(r'\.hero-subtext\s*\{[^}]*font-size:\s*([^;]+)', css_content)
        if hero_subtext_match:
            font_size = self.extract_numeric_value(hero_subtext_match.group(1))
            if font_size and font_size < 16:
                self.issues.append(MobileIssue(
                    file_path='landing.html',
                    element='.hero-subtext',
                    issue_type='font_size_too_small',
                    description=f'Hero subtext font size ({font_size}px) is below mobile minimum',
                    recommendation='Increase hero subtext font size to at least 16px',
                    severity='critical',
                    current_value=f'{font_size}px',
                    recommended_value='16px+'
                ))

        # Check calculator card titles
        calculator_title_match = re.search(r'\.calculator-title\s*\{[^}]*font-size:\s*([^;]+)', css_content)
        if calculator_title_match:
            font_size = self.extract_numeric_value(calculator_title_match.group(1))
            if font_size and font_size < 18:
                self.issues.append(MobileIssue(
                    file_path='landing.html',
                    element='.calculator-title',
                    issue_type='font_size_too_small',
                    description=f'Calculator title font size ({font_size}px) may be too small for mobile',
                    recommendation='Increase calculator title font size to 18px+ for better readability',
                    severity='warning',
                    current_value=f'{font_size}px',
                    recommended_value='18px+'
                ))

        # Check CTA button sizes
        cta_match = re.search(r'\.calculator-cta\s*\{[^}]*padding:\s*([^;]+)', css_content)
        if cta_match:
            padding = self.extract_numeric_value(cta_match.group(1))
            if padding and padding < 12:
                self.issues.append(MobileIssue(
                    file_path='landing.html',
                    element='.calculator-cta',
                    issue_type='touch_target_too_small',
                    description=f'CTA button padding ({padding}px) may create small touch targets',
                    recommendation='Increase CTA button padding to 16px+ for better mobile usability',
                    severity='warning',
                    current_value=f'{padding}px',
                    recommended_value='16px+'
                ))

        # Check line heights
        line_height_matches = re.findall(r'line-height:\s*([^;]+)', css_content)
        for match in line_height_matches:
            line_height = self.extract_numeric_value(match)
            if line_height and line_height < 1.4:
                self.issues.append(MobileIssue(
                    file_path='landing.html',
                    element='line-height',
                    issue_type='line_height_too_tight',
                    description=f'Line height ({line_height}) is too tight for mobile reading',
                    recommendation='Increase line-height to at least 1.4 for better mobile readability',
                    severity='warning',
                    current_value=str(line_height),
                    recommended_value='1.4+'
                ))

    def analyze_calculator_page(self):
        """Analyze ai-job-impact-calculator.html for mobile issues"""
        print("🧮 Analyzing calculator page...")
        
        try:
            with open('ai-job-impact-calculator.html', 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract CSS styles
            css_pattern = r'<style[^>]*>(.*?)</style>'
            css_matches = re.findall(css_pattern, content, re.DOTALL | re.IGNORECASE)
            
            for css_content in css_matches:
                self.analyze_calculator_css(css_content)
                
        except FileNotFoundError:
            print("⚠️ ai-job-impact-calculator.html not found")
        except Exception as e:
            print(f"Error analyzing calculator page: {e}")

    def analyze_calculator_css(self, css_content: str):
        """Analyze calculator page CSS for mobile issues"""
        
        # Check form input sizes
        input_matches = re.findall(r'input[^}]*\{[^}]*font-size:\s*([^;]+)', css_content)
        for match in input_matches:
            font_size = self.extract_numeric_value(match)
            if font_size and font_size < 16:
                self.issues.append(MobileIssue(
                    file_path='ai-job-impact-calculator.html',
                    element='input',
                    issue_type='font_size_too_small',
                    description=f'Form input font size ({font_size}px) is below mobile minimum',
                    recommendation='Increase form input font size to at least 16px to prevent zoom on iOS',
                    severity='critical',
                    current_value=f'{font_size}px',
                    recommended_value='16px+'
                ))

        # Check button sizes
        button_matches = re.findall(r'button[^}]*\{[^}]*padding:\s*([^;]+)', css_content)
        for match in button_matches:
            padding = self.extract_numeric_value(match)
            if padding and padding < 12:
                self.issues.append(MobileIssue(
                    file_path='ai-job-impact-calculator.html',
                    element='button',
                    issue_type='touch_target_too_small',
                    description=f'Button padding ({padding}px) may create small touch targets',
                    recommendation='Increase button padding to 16px+ for better mobile usability',
                    severity='warning',
                    current_value=f'{padding}px',
                    recommended_value='16px+'
                ))

    def analyze_react_components(self):
        """Analyze React components for mobile issues"""
        print("⚛️ Analyzing React components...")
        
        for file_path in self.target_files[2:]:  # Skip HTML files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.analyze_react_file(content, file_path)
                
            except FileNotFoundError:
                print(f"⚠️ {file_path} not found")
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")

    def analyze_react_file(self, content: str, file_path: str):
        """Analyze React component for mobile issues"""
        
        # Check Tailwind font size classes
        font_size_classes = re.findall(r'text-(\w+)', content)
        font_size_map = {
            'xs': 12, 'sm': 14, 'base': 16, 'lg': 18, 'xl': 20,
            '2xl': 24, '3xl': 30, '4xl': 36, '5xl': 48, '6xl': 60
        }
        
        for class_name in font_size_classes:
            if class_name in font_size_map:
                size = font_size_map[class_name]
                if size < 16:
                    self.issues.append(MobileIssue(
                        file_path=file_path,
                        element=f'text-{class_name}',
                        issue_type='font_size_too_small',
                        description=f'Tailwind text-{class_name} class uses {size}px font size',
                        recommendation='Use text-base (16px) or larger for better mobile readability',
                        severity='critical' if size < 14 else 'warning',
                        current_value=f'{size}px (text-{class_name})',
                        recommended_value='16px+ (text-base+)'
                    ))

        # Check line height classes
        line_height_classes = re.findall(r'leading-(\w+)', content)
        line_height_map = {
            'none': 1, 'tight': 1.25, 'snug': 1.375, 'normal': 1.5, 'relaxed': 1.625, 'loose': 2
        }
        
        for class_name in line_height_classes:
            if class_name in line_height_map:
                line_height = line_height_map[class_name]
                if line_height < 1.4:
                    self.issues.append(MobileIssue(
                        file_path=file_path,
                        element=f'leading-{class_name}',
                        issue_type='line_height_too_tight',
                        description=f'Tailwind leading-{class_name} class uses {line_height} line height',
                        recommendation='Use leading-relaxed (1.625) or larger for better text readability',
                        severity='warning',
                        current_value=str(line_height),
                        recommended_value='1.4+'
                    ))

        # Check spacing classes
        spacing_classes = re.findall(r'p-(\w+)|m-(\w+)', content)
        spacing_map = {
            '1': 4, '2': 8, '3': 12, '4': 16, '5': 20, '6': 24, '8': 32, '10': 40, '12': 48
        }
        
        for match in spacing_classes:
            spacing_class = match[0] or match[1]
            if spacing_class in spacing_map:
                spacing = spacing_map[spacing_class]
                if spacing < 16:
                    self.issues.append(MobileIssue(
                        file_path=file_path,
                        element=f'spacing-{spacing_class}',
                        issue_type='insufficient_spacing',
                        description=f'Spacing class uses {spacing}px which may be insufficient',
                        recommendation='Use spacing of 16px+ for better content separation on mobile',
                        severity='warning',
                        current_value=f'{spacing}px',
                        recommended_value='16px+'
                    ))

    def extract_numeric_value(self, value: str) -> float:
        """Extract numeric value from CSS value"""
        numeric_match = re.search(r'(\d+(?:\.\d+)?)', value)
        if numeric_match:
            return float(numeric_match.group(1))
        return None

    def generate_focused_report(self) -> Dict[str, Any]:
        """Generate focused mobile readability report"""
        print("📋 Generating focused report...")
        
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
        
        # Calculate metrics
        total_issues = len(self.issues)
        critical_issues = len([i for i in self.issues if i.severity == 'critical'])
        warning_issues = len([i for i in self.issues if i.severity == 'warning'])
        
        # Calculate scores
        font_size_score = max(0, 100 - (critical_issues * 15) - (warning_issues * 5))
        line_height_score = max(0, 100 - (warning_issues * 10))
        touch_target_score = max(0, 100 - (critical_issues * 20))
        overall_score = (font_size_score + line_height_score + touch_target_score) // 3
        
        metrics = {
            'overall_score': overall_score,
            'font_size_score': font_size_score,
            'line_height_score': line_height_score,
            'touch_target_score': touch_target_score,
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues
        }
        
        # Generate recommendations
        recommendations = self.generate_recommendations()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'issues_by_file': {
                file_path: [self.issue_to_dict(issue) for issue in issues]
                for file_path, issues in issues_by_file.items()
            },
            'issues_by_type': {
                issue_type: [self.issue_to_dict(issue) for issue in issues]
                for issue_type, issues in issues_by_type.items()
            },
            'recommendations': recommendations,
            'standards_used': self.mobile_standards
        }
        
        return report

    def issue_to_dict(self, issue: MobileIssue) -> Dict[str, Any]:
        """Convert MobileIssue to dictionary"""
        return {
            'file_path': issue.file_path,
            'element': issue.element,
            'issue_type': issue.issue_type,
            'description': issue.description,
            'recommendation': issue.recommendation,
            'severity': issue.severity,
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
                'description': f'Found {len(font_size_issues)} elements with font sizes below 16px',
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
        
        return recommendations

    def print_summary(self, report: Dict[str, Any]):
        """Print summary of the focused audit"""
        metrics = report['metrics']
        
        print("\n" + "="*60)
        print("📱 FOCUSED MINGUS MOBILE READABILITY AUDIT")
        print("="*60)
        
        print(f"\n📊 Overall Score: {metrics['overall_score']}/100")
        print(f"🔴 Critical Issues: {metrics['critical_issues']}")
        print(f"🟡 Warning Issues: {metrics['warning_issues']}")
        print(f"📝 Total Issues: {metrics['total_issues']}")
        
        print(f"\n📈 Detailed Scores:")
        print(f"   Font Size: {metrics['font_size_score']}/100")
        print(f"   Line Height: {metrics['line_height_score']}/100")
        print(f"   Touch Targets: {metrics['touch_target_score']}/100")
        
        print(f"\n🎯 Key Recommendations:")
        for rec in report['recommendations']:
            print(f"   • {rec['category']} ({rec['priority']}): {rec['description']}")
        
        print(f"\n📁 Files Analyzed: {len(report['issues_by_file'])}")
        print("\n" + "="*60)

def main():
    """Main function"""
    auditor = FocusedMobileAuditor()
    report = auditor.run_audit()
    
    # Print summary
    auditor.print_summary(report)
    
    # Save report
    output_file = f"focused_mobile_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Focused report saved to: {output_file}")
    print("✅ Focused audit complete!")

if __name__ == "__main__":
    main()
