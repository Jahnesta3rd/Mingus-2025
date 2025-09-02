#!/usr/bin/env python3
"""
Mobile Application Typography Hierarchy Analysis
Analyzes typography hierarchy, font weights, line heights, and content flow for React components
"""

import re
import json
import os
from datetime import datetime
from pathlib import Path

class MobileAppTypographyAnalyzer:
    def __init__(self):
        self.issues = []
        self.typography_elements = []
        self.heading_hierarchy = []
        self.font_weights = []
        self.line_heights = []
        self.content_flow = []
        self.cta_elements = []
        self.tailwind_classes = []
        self.inline_styles = []
        
    def analyze_file(self, file_path):
        """Analyze a single React component file for typography hierarchy issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            filename = os.path.basename(file_path)
            print(f"📄 Analyzing {filename}...")
            
            # Analyze React/TSX content
            self.analyze_react_typography(content, filename)
            
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")
    
    def analyze_react_typography(self, content, filename):
        """Analyze React/TSX content for typography hierarchy issues"""
        # Find JSX heading elements
        heading_pattern = r'<h([1-6])[^>]*>([^<]+)</h[1-6]>'
        headings = re.findall(heading_pattern, content, re.IGNORECASE)
        
        for heading_level, heading_text in headings:
            self.heading_hierarchy.append({
                'level': int(heading_level),
                'text': heading_text.strip(),
                'file': filename,
                'type': 'JSX Heading'
            })
        
        # Find paragraph elements
        paragraph_pattern = r'<p[^>]*>([^<]+)</p>'
        paragraphs = re.findall(paragraph_pattern, content, re.IGNORECASE)
        
        for paragraph_text in paragraphs:
            self.analyze_paragraph(paragraph_text.strip(), filename)
        
        # Find button and CTA elements
        cta_pattern = r'<(button|a)[^>]*>([^<]+)</(button|a)>'
        cta_elements = re.findall(cta_pattern, content, re.IGNORECASE)
        
        for cta_type, cta_text, closing_tag in cta_elements:
            self.analyze_cta_element(cta_text.strip(), filename, cta_type)
        
        # Find Tailwind CSS classes
        self.analyze_tailwind_classes(content, filename)
        
        # Find inline styles
        self.analyze_inline_styles(content, filename)
        
        # Find styled-components or CSS-in-JS
        self.analyze_styled_components(content, filename)
    
    def analyze_tailwind_classes(self, content, filename):
        """Analyze Tailwind CSS classes for typography"""
        # Find className attributes with Tailwind classes
        class_pattern = r'className="([^"]*)"'
        class_matches = re.findall(class_pattern, content)
        
        for class_string in class_matches:
            classes = class_string.split()
            
            for class_name in classes:
                if class_name.startswith('text-'):
                    self.analyze_tailwind_text_class(class_name, filename)
                elif class_name.startswith('font-'):
                    self.analyze_tailwind_font_class(class_name, filename)
                elif class_name.startswith('leading-'):
                    self.analyze_tailwind_leading_class(class_name, filename)
                elif class_name.startswith('tracking-'):
                    self.analyze_tailwind_tracking_class(class_name, filename)
    
    def analyze_tailwind_text_class(self, class_name, filename):
        """Analyze Tailwind text size classes"""
        text_sizes = {
            'text-xs': 12,
            'text-sm': 14,
            'text-base': 16,
            'text-lg': 18,
            'text-xl': 20,
            'text-2xl': 24,
            'text-3xl': 30,
            'text-4xl': 36,
            'text-5xl': 48,
            'text-6xl': 60
        }
        
        if class_name in text_sizes:
            size = text_sizes[class_name]
            
            self.typography_elements.append({
                'type': 'Tailwind Text Size',
                'class': class_name,
                'size_px': size,
                'file': filename,
                'source': 'Tailwind CSS'
            })
            
            # Check for mobile readability issues
            if size < 16:
                self.issues.append({
                    'type': 'tailwind_text_too_small',
                    'severity': 'high',
                    'message': f"Tailwind class '{class_name}' ({size}px) is below mobile minimum of 16px",
                    'file': filename,
                    'class': class_name,
                    'size_px': size
                })
    
    def analyze_tailwind_font_class(self, class_name, filename):
        """Analyze Tailwind font weight classes"""
        font_weights = {
            'font-thin': 100,
            'font-extralight': 200,
            'font-light': 300,
            'font-normal': 400,
            'font-medium': 500,
            'font-semibold': 600,
            'font-bold': 700,
            'font-extrabold': 800,
            'font-black': 900
        }
        
        if class_name in font_weights:
            weight = font_weights[class_name]
            
            self.font_weights.append({
                'type': 'Tailwind Font Weight',
                'class': class_name,
                'weight': weight,
                'file': filename,
                'source': 'Tailwind CSS'
            })
            
            # Check for font weight issues
            if weight < 300:
                self.issues.append({
                    'type': 'tailwind_font_too_light',
                    'severity': 'medium',
                    'message': f"Tailwind class '{class_name}' (weight {weight}) may be too light for mobile",
                    'file': filename,
                    'class': class_name,
                    'weight': weight
                })
    
    def analyze_tailwind_leading_class(self, class_name, filename):
        """Analyze Tailwind line height classes"""
        line_heights = {
            'leading-none': 1,
            'leading-tight': 1.25,
            'leading-snug': 1.375,
            'leading-normal': 1.5,
            'leading-relaxed': 1.625,
            'leading-loose': 2
        }
        
        if class_name in line_heights:
            height = line_heights[class_name]
            
            self.line_heights.append({
                'type': 'Tailwind Line Height',
                'class': class_name,
                'height': height,
                'file': filename,
                'source': 'Tailwind CSS'
            })
            
            # Check for line height issues
            if height < 1.4:
                self.issues.append({
                    'type': 'tailwind_leading_too_tight',
                    'severity': 'high',
                    'message': f"Tailwind class '{class_name}' (line-height {height}) is too tight for mobile",
                    'file': filename,
                    'class': class_name,
                    'height': height
                })
    
    def analyze_tailwind_tracking_class(self, class_name, filename):
        """Analyze Tailwind letter spacing classes"""
        tracking_values = {
            'tracking-tighter': -0.05,
            'tracking-tight': -0.025,
            'tracking-normal': 0,
            'tracking-wide': 0.025,
            'tracking-wider': 0.05,
            'tracking-widest': 0.1
        }
        
        if class_name in tracking_values:
            tracking = tracking_values[class_name]
            
            # Check for letter spacing issues
            if tracking < -0.025:
                self.issues.append({
                    'type': 'tailwind_tracking_too_tight',
                    'severity': 'medium',
                    'message': f"Tailwind class '{class_name}' (tracking {tracking}) may be too tight for mobile",
                    'file': filename,
                    'class': class_name,
                    'tracking': tracking
                })
    
    def analyze_inline_styles(self, content, filename):
        """Analyze inline styles for typography"""
        # Find style attributes
        style_pattern = r'style="([^"]*)"'
        style_matches = re.findall(style_pattern, content)
        
        for style_string in style_matches:
            # Parse individual style properties
            style_props = style_string.split(';')
            
            for prop in style_props:
                prop = prop.strip()
                if ':' in prop:
                    key, value = prop.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == 'font-size':
                        self.analyze_inline_font_size(value, filename)
                    elif key == 'font-weight':
                        self.analyze_inline_font_weight(value, filename)
                    elif key == 'line-height':
                        self.analyze_inline_line_height(value, filename)
    
    def analyze_inline_font_size(self, value, filename):
        """Analyze inline font-size values"""
        # Parse font size
        size_info = self.parse_font_size(value)
        
        if size_info:
            size_info.update({
                'file': filename,
                'source': 'Inline Style'
            })
            
            self.typography_elements.append(size_info)
            
            # Check for mobile readability issues
            if size_info['type'] in ['fixed', 'relative'] and size_info['unit'] == 'px':
                if size_info['value'] < 16:
                    self.issues.append({
                        'type': 'inline_font_too_small',
                        'severity': 'high',
                        'message': f"Inline font-size {value} is below mobile minimum of 16px",
                        'file': filename,
                        'value': value,
                        'size_px': size_info['value']
                    })
    
    def analyze_inline_font_weight(self, value, filename):
        """Analyze inline font-weight values"""
        # Parse font weight
        weight_info = self.parse_font_weight(value)
        
        if weight_info:
            weight_info.update({
                'file': filename,
                'source': 'Inline Style'
            })
            
            self.font_weights.append(weight_info)
            
            # Check for font weight issues
            if weight_info['type'] in ['numeric', 'keyword']:
                weight_value = weight_info['value']
                
                if weight_value < 300:
                    self.issues.append({
                        'type': 'inline_font_too_light',
                        'severity': 'medium',
                        'message': f"Inline font-weight {value} may be too light for mobile",
                        'file': filename,
                        'value': value,
                        'weight': weight_value
                    })
    
    def analyze_inline_line_height(self, value, filename):
        """Analyze inline line-height values"""
        # Parse line height
        height_info = self.parse_line_height(value)
        
        if height_info:
            height_info.update({
                'file': filename,
                'source': 'Inline Style'
            })
            
            self.line_heights.append(height_info)
            
            # Check for line height issues
            if height_info['type'] in ['unitless', 'percentage']:
                height_value = height_info['value']
                
                if height_value < 1.4:
                    self.issues.append({
                        'type': 'inline_line_height_too_tight',
                        'severity': 'high',
                        'message': f"Inline line-height {value} is too tight for mobile",
                        'file': filename,
                        'value': value,
                        'height': height_value
                    })
    
    def analyze_styled_components(self, content, filename):
        """Analyze styled-components or CSS-in-JS patterns"""
        # Find styled-components patterns
        styled_pattern = r'styled\.[a-zA-Z]+\s*`([^`]+)`'
        styled_matches = re.findall(styled_pattern, content)
        
        for styled_content in styled_matches:
            self.analyze_css_content(styled_content, filename, 'Styled Component')
        
        # Find CSS-in-JS patterns
        css_js_pattern = r'css`([^`]+)`'
        css_js_matches = re.findall(css_js_pattern, content)
        
        for css_content in css_js_matches:
            self.analyze_css_content(css_content, filename, 'CSS-in-JS')
    
    def analyze_css_content(self, content, filename, source_type):
        """Analyze CSS content for typography"""
        # Find font-size declarations
        font_size_pattern = r'font-size:\s*([^;]+);'
        font_sizes = re.findall(font_size_pattern, content, re.IGNORECASE)
        
        for font_size in font_sizes:
            font_size = font_size.strip()
            self.analyze_font_size(font_size, filename, source_type)
        
        # Find font-weight declarations
        font_weight_pattern = r'font-weight:\s*([^;]+);'
        font_weights = re.findall(font_weight_pattern, content, re.IGNORECASE)
        
        for font_weight in font_weights:
            font_weight = font_weight.strip()
            self.analyze_font_weight(font_weight, filename, source_type)
        
        # Find line-height declarations
        line_height_pattern = r'line-height:\s*([^;]+);'
        line_heights = re.findall(line_height_pattern, content, re.IGNORECASE)
        
        for line_height in line_heights:
            line_height = line_height.strip()
            self.analyze_line_height(line_height, filename, source_type)
    
    def analyze_font_size(self, font_size, filename, source_type):
        """Analyze font size value"""
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
                'type': 'JSX Paragraph',
                'word_count': word_count
            })
        
        # Check for walls of text
        if word_count > 100:
            self.issues.append({
                'type': 'wall_of_text',
                'severity': 'high',
                'message': f"Paragraph has {word_count} words, creates a wall of text on mobile",
                'file': filename,
                'type': 'JSX Paragraph',
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
                'type': 'JSX CTA',
                'text': cta_text
            })
        
        if text_length > 50:
            self.issues.append({
                'type': 'cta_too_long',
                'severity': 'medium',
                'message': f"CTA text '{cta_text}' is too long for mobile buttons",
                'file': filename,
                'type': 'JSX CTA',
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
                'content_flow_elements': len(self.content_flow),
                'tailwind_classes': len(self.tailwind_classes),
                'inline_styles': len(self.inline_styles)
            },
            'issues': self.issues,
            'heading_hierarchy': self.heading_hierarchy,
            'font_weights': self.font_weights,
            'line_heights': self.line_heights,
            'cta_elements': self.cta_elements,
            'content_flow': self.content_flow,
            'typography_elements': self.typography_elements,
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
        
        # Tailwind text size issues
        if issue_types.get('tailwind_text_too_small', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'Typography',
                'title': 'Fix Tailwind Text Sizes',
                'description': f"Found {issue_types['tailwind_text_too_small']} instances of Tailwind text classes below mobile minimum.",
                'action': 'Replace text-xs and text-sm with text-base or larger for mobile readability'
            })
        
        # Line height issues
        if issue_types.get('line_height_too_tight', 0) > 0 or issue_types.get('tailwind_leading_too_tight', 0) > 0:
            total_tight = issue_types.get('line_height_too_tight', 0) + issue_types.get('tailwind_leading_too_tight', 0)
            recommendations.append({
                'priority': 'high',
                'category': 'Readability',
                'title': 'Improve Line Height for Mobile',
                'description': f"Found {total_tight} instances of line height too tight for mobile readability.",
                'action': 'Use leading-relaxed (1.625) or leading-loose (2.0) for better mobile readability'
            })
        
        # Font weight issues
        if issue_types.get('font_weight_too_light', 0) > 0 or issue_types.get('tailwind_font_too_light', 0) > 0:
            total_light = issue_types.get('font_weight_too_light', 0) + issue_types.get('tailwind_font_too_light', 0)
            recommendations.append({
                'priority': 'medium',
                'category': 'Typography',
                'title': 'Improve Font Weight Contrast',
                'description': f"Found {total_light} instances of font weight too light for mobile readability.",
                'action': 'Use font-medium (500) or font-semibold (600) for better mobile contrast'
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
                'action': 'Break long paragraphs into shorter, scannable chunks with proper spacing'
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
    print("🔍 Mobile Application Typography Hierarchy Analysis")
    print("=" * 70)
    
    analyzer = MobileAppTypographyAnalyzer()
    
    # Define directories to analyze
    directories_to_analyze = [
        'src/components/onboarding',
        'src/components/dashboard',
        'src/components/aiCalculator',
        'src/components/leadCapture',
        'src/components/common',
        'src/components/checklist',
        'src/components/tour',
        'src/components/education',
        'src/components/security',
        'src/components/questionnaires'
    ]
    
    # Collect all TSX files
    tsx_files = []
    for directory in directories_to_analyze:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.tsx') or file.endswith('.ts'):
                        tsx_files.append(os.path.join(root, file))
        else:
            print(f"⚠️  Directory not found: {directory}")
    
    print(f"📁 Found {len(tsx_files)} React component files to analyze")
    
    # Analyze each file
    for file_path in tsx_files:
        analyzer.analyze_file(file_path)
    
    # Generate report
    report = analyzer.generate_report()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 MOBILE APP TYPOGRAPHY HIERARCHY ANALYSIS SUMMARY")
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
    report_filename = f"mobile_app_typography_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    print("✅ Mobile application typography hierarchy analysis complete!")

if __name__ == "__main__":
    main()
