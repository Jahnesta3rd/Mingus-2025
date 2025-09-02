#!/usr/bin/env python3
"""
Mingus Financial Services - WCAG 2.1 AA Accessibility Manager

This module provides comprehensive accessibility compliance for the Mingus financial
services application, implementing WCAG 2.1 AA standards including:

1. Alt Text and Image Accessibility
2. ARIA Labels and Landmarks Implementation  
3. Keyboard Navigation Support
4. Screen Reader Optimization

Author: Mingus Development Team
Version: 1.0.0
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AccessibilityIssue:
    """Represents an accessibility issue found during audit"""
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'alt_text', 'aria', 'keyboard', 'contrast', 'semantic'
    element: str
    description: str
    recommendation: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None

@dataclass
class AltTextTemplate:
    """Template for generating descriptive alt text"""
    context: str
    template: str
    variables: List[str]
    description: str

class AccessibilityManager:
    """
    Comprehensive accessibility manager for WCAG 2.1 AA compliance
    """
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.issues: List[AccessibilityIssue] = []
        self.alt_text_templates = self._load_alt_text_templates()
        self.aria_patterns = self._load_aria_patterns()
        self.keyboard_shortcuts = self._load_keyboard_shortcuts()
        
    def _load_alt_text_templates(self) -> Dict[str, AltTextTemplate]:
        """Load alt text templates for different types of financial content"""
        return {
            "financial_chart": AltTextTemplate(
                context="charts",
                template="Chart showing {chart_type} for {time_period}. {key_insight}",
                variables=["chart_type", "time_period", "key_insight"],
                description="Descriptive alt text for financial charts and graphs"
            ),
            "data_visualization": AltTextTemplate(
                context="visualizations", 
                template="Data visualization displaying {data_type} with {trend_direction} trend from {start_value} to {end_value}",
                variables=["data_type", "trend_direction", "start_value", "end_value"],
                description="Alt text for data visualizations and graphs"
            ),
            "decorative_image": AltTextTemplate(
                context="decorative",
                template="",
                variables=[],
                description="Empty alt text for decorative images"
            ),
            "logo": AltTextTemplate(
                context="branding",
                template="Mingus Financial Services logo",
                variables=[],
                description="Alt text for company logos"
            ),
            "profile_photo": AltTextTemplate(
                context="profiles",
                template="Profile photo of {person_name}",
                variables=["person_name"],
                description="Alt text for user profile photos"
            ),
            "financial_icon": AltTextTemplate(
                context="icons",
                template="{icon_type} icon representing {financial_concept}",
                variables=["icon_type", "financial_concept"],
                description="Alt text for financial icons and symbols"
            )
        }
    
    def _load_aria_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load ARIA patterns for different component types"""
        return {
            "form_inputs": {
                "text": 'aria-label="{label}" aria-describedby="{help_id}" aria-required="{required}"',
                "email": 'aria-label="{label}" aria-describedby="{help_id}" aria-required="{required}" aria-invalid="{invalid}"',
                "password": 'aria-label="{label}" aria-describedby="{help_id}" aria-required="{required}" aria-invalid="{invalid}"',
                "number": 'aria-label="{label}" aria-describedby="{help_id}" aria-required="{required}" aria-valuemin="{min}" aria-valuemax="{max}"',
                "select": 'aria-label="{label}" aria-describedby="{help_id}" aria-required="{required}" aria-expanded="{expanded}"',
                "checkbox": 'aria-label="{label}" aria-describedby="{help_id}" aria-checked="{checked}"',
                "radio": 'aria-label="{label}" aria-describedby="{help_id}" aria-checked="{checked}"'
            },
            "buttons": {
                "primary": 'aria-label="{label}" aria-describedby="{description_id}" aria-pressed="{pressed}"',
                "secondary": 'aria-label="{label}" aria-describedby="{description_id}"',
                "icon": 'aria-label="{label}" aria-hidden="false"',
                "close": 'aria-label="Close {context}" aria-describedby="{description_id}"',
                "submit": 'aria-label="{label}" aria-describedby="{description_id}" aria-busy="{busy}"'
            },
            "navigation": {
                "main": 'role="navigation" aria-label="Main navigation"',
                "breadcrumb": 'role="navigation" aria-label="Breadcrumb"',
                "pagination": 'role="navigation" aria-label="Pagination"',
                "menu": 'role="menu" aria-label="{label}"',
                "menuitem": 'role="menuitem" aria-current="{current}"'
            },
            "landmarks": {
                "header": 'role="banner"',
                "main": 'role="main"',
                "footer": 'role="contentinfo"',
                "aside": 'role="complementary" aria-label="{label}"',
                "section": 'role="region" aria-label="{label}"'
            },
            "tables": {
                "data": 'role="table" aria-label="{label}" aria-describedby="{description_id}"',
                "cell": 'role="cell" aria-label="{label}"',
                "header": 'role="columnheader" aria-label="{label}" scope="col"',
                "row": 'role="row" aria-label="{label}"'
            }
        }
    
    def _load_keyboard_shortcuts(self) -> Dict[str, Dict[str, str]]:
        """Load keyboard shortcuts for financial tools"""
        return {
            "navigation": {
                "dashboard": "Alt + D",
                "assessments": "Alt + A", 
                "analytics": "Alt + L",
                "profile": "Alt + P",
                "help": "F1",
                "search": "Ctrl + K"
            },
            "financial_tools": {
                "income_comparison": "Alt + I",
                "tax_calculator": "Alt + T",
                "budget_planner": "Alt + B",
                "investment_analyzer": "Alt + V",
                "debt_payoff": "Alt + E",
                "retirement_planner": "Alt + R"
            },
            "actions": {
                "save": "Ctrl + S",
                "print": "Ctrl + P",
                "export": "Ctrl + E",
                "refresh": "F5",
                "close": "Escape",
                "submit": "Enter"
            }
        }
    
    def generate_alt_text(self, image_type: str, **kwargs) -> str:
        """
        Generate appropriate alt text based on image type and context
        
        Args:
            image_type: Type of image (financial_chart, data_visualization, etc.)
            **kwargs: Variables to populate the template
            
        Returns:
            Generated alt text string
        """
        if image_type not in self.alt_text_templates:
            logger.warning(f"Unknown image type: {image_type}")
            return ""
        
        template = self.alt_text_templates[image_type]
        
        if image_type == "decorative_image":
            return ""
        
        try:
            alt_text = template.template
            for var in template.variables:
                if var in kwargs:
                    alt_text = alt_text.replace(f"{{{var}}}", str(kwargs[var]))
                else:
                    logger.warning(f"Missing variable {var} for alt text template {image_type}")
                    alt_text = alt_text.replace(f"{{{var}}}", "[missing data]")
            
            return alt_text
        except Exception as e:
            logger.error(f"Error generating alt text for {image_type}: {e}")
            return f"Image showing {image_type.replace('_', ' ')}"
    
    def generate_aria_attributes(self, element_type: str, category: str, **kwargs) -> str:
        """
        Generate ARIA attributes for different element types
        
        Args:
            element_type: Type of element (text, email, primary, etc.)
            category: Category of element (form_inputs, buttons, etc.)
            **kwargs: Variables to populate the ARIA attributes
            
        Returns:
            Generated ARIA attributes string
        """
        if category not in self.aria_patterns:
            logger.warning(f"Unknown ARIA category: {category}")
            return ""
        
        if element_type not in self.aria_patterns[category]:
            logger.warning(f"Unknown element type {element_type} in category {category}")
            return ""
        
        pattern = self.aria_patterns[category][element_type]
        
        try:
            aria_attrs = pattern
            # Extract variables from pattern using regex
            variables = re.findall(r'\{(\w+)\}', pattern)
            
            for var in variables:
                if var in kwargs:
                    aria_attrs = aria_attrs.replace(f"{{{var}}}", str(kwargs[var]))
                else:
                    # Use sensible defaults
                    defaults = {
                        "label": "Input field",
                        "help_id": "",
                        "required": "false",
                        "invalid": "false",
                        "min": "0",
                        "max": "100",
                        "expanded": "false",
                        "checked": "false",
                        "pressed": "false",
                        "description_id": "",
                        "busy": "false",
                        "current": "false",
                        "context": "dialog"
                    }
                    aria_attrs = aria_attrs.replace(f"{{{var}}}", defaults.get(var, ""))
            
            return aria_attrs
        except Exception as e:
            logger.error(f"Error generating ARIA attributes for {element_type}: {e}")
            return ""
    
    def audit_file_accessibility(self, file_path: str) -> List[AccessibilityIssue]:
        """
        Audit a single file for accessibility issues
        
        Args:
            file_path: Path to the file to audit
            
        Returns:
            List of accessibility issues found
        """
        issues = []
        file_ext = Path(file_path).suffix.lower()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            if file_ext in ['.html', '.htm']:
                issues.extend(self._audit_html_file(content, lines, file_path))
            elif file_ext in ['.tsx', '.jsx', '.js']:
                issues.extend(self._audit_react_file(content, lines, file_path))
            elif file_ext in ['.css', '.scss']:
                issues.extend(self._audit_css_file(content, lines, file_path))
                
        except Exception as e:
            logger.error(f"Error auditing file {file_path}: {e}")
            issues.append(AccessibilityIssue(
                severity="high",
                category="audit_error",
                element=file_path,
                description=f"Failed to audit file: {e}",
                recommendation="Check file permissions and encoding",
                file_path=file_path
            ))
        
        return issues
    
    def _audit_html_file(self, content: str, lines: List[str], file_path: str) -> List[AccessibilityIssue]:
        """Audit HTML file for accessibility issues"""
        issues = []
        
        # Check for missing alt attributes on images
        img_pattern = r'<img[^>]*>'
        for match in re.finditer(img_pattern, content):
            img_tag = match.group(0)
            line_num = content[:match.start()].count('\n') + 1
            
            if 'alt=' not in img_tag:
                issues.append(AccessibilityIssue(
                    severity="critical",
                    category="alt_text",
                    element="img",
                    description="Image missing alt attribute",
                    recommendation="Add descriptive alt text or alt='' for decorative images",
                    line_number=line_num,
                    file_path=file_path
                ))
        
        # Check for proper heading hierarchy
        heading_pattern = r'<(h[1-6])[^>]*>'
        headings = []
        for match in re.finditer(heading_pattern, content):
            level = int(match.group(1)[1])
            line_num = content[:match.start()].count('\n') + 1
            headings.append((level, line_num))
        
        # Check heading hierarchy
        for i, (level, line_num) in enumerate(headings):
            if i > 0 and level > headings[i-1][0] + 1:
                issues.append(AccessibilityIssue(
                    severity="high",
                    category="semantic",
                    element=f"h{level}",
                    description="Heading level skipped",
                    recommendation="Use proper heading hierarchy (h1, h2, h3, etc.)",
                    line_number=line_num,
                    file_path=file_path
                ))
        
        # Check for form labels
        input_pattern = r'<(input|textarea|select)[^>]*>'
        for match in re.finditer(input_pattern, content):
            input_tag = match.group(0)
            line_num = content[:match.start()].count('\n') + 1
            
            if 'id=' in input_tag and 'aria-label=' not in input_tag:
                # Check if there's a corresponding label
                id_match = re.search(r'id=["\']([^"\']+)["\']', input_tag)
                if id_match:
                    id_value = id_match.group(1)
                    label_pattern = rf'<label[^>]*for=["\']{id_value}["\'][^>]*>'
                    if not re.search(label_pattern, content):
                        issues.append(AccessibilityIssue(
                            severity="high",
                            category="form_labels",
                            element="input",
                            description=f"Input with id '{id_value}' missing label",
                            recommendation="Add label element or aria-label attribute",
                            line_number=line_num,
                            file_path=file_path
                        ))
        
        return issues
    
    def _audit_react_file(self, content: str, lines: List[str], file_path: str) -> List[AccessibilityIssue]:
        """Audit React/TypeScript file for accessibility issues"""
        issues = []
        
        # Check for missing alt props on img elements
        img_pattern = r'<img[^>]*>'
        for match in re.finditer(img_pattern, content):
            img_tag = match.group(0)
            line_num = content[:match.start()].count('\n') + 1
            
            if 'alt=' not in img_tag and 'alt={' not in img_tag:
                issues.append(AccessibilityIssue(
                    severity="critical",
                    category="alt_text",
                    element="img",
                    description="React image missing alt prop",
                    recommendation="Add alt prop with descriptive text or empty string",
                    line_number=line_num,
                    file_path=file_path
                ))
        
        # Check for missing aria-label on interactive elements
        interactive_pattern = r'<(button|a|input)[^>]*>'
        for match in re.finditer(interactive_pattern, content):
            element_tag = match.group(0)
            line_num = content[:match.start()].count('\n') + 1
            
            if 'aria-label=' not in element_tag and 'aria-labelledby=' not in element_tag:
                # Check if there's visible text content
                if not re.search(r'>[^<]+<', element_tag):
                    issues.append(AccessibilityIssue(
                        severity="medium",
                        category="aria",
                        element=match.group(1),
                        description="Interactive element missing accessible name",
                        recommendation="Add aria-label or aria-labelledby attribute",
                        line_number=line_num,
                        file_path=file_path
                    ))
        
        return issues
    
    def _audit_css_file(self, content: str, lines: List[str], file_path: str) -> List[AccessibilityIssue]:
        """Audit CSS file for accessibility issues"""
        issues = []
        
        # Check for focus indicators
        focus_pattern = r':focus\s*\{[^}]*\}'
        focus_rules = re.findall(focus_pattern, content)
        
        if not focus_rules:
            issues.append(AccessibilityIssue(
                severity="high",
                category="keyboard",
                element="CSS",
                description="No focus indicators defined",
                recommendation="Add visible focus indicators for keyboard navigation",
                file_path=file_path
            ))
        
        # Check for color contrast (simplified)
        color_pattern = r'color:\s*#[0-9a-fA-F]{3,6}'
        background_pattern = r'background(?:-color)?:\s*#[0-9a-fA-F]{3,6}'
        
        colors = re.findall(color_pattern, content)
        backgrounds = re.findall(background_pattern, content)
        
        if colors and not backgrounds:
            issues.append(AccessibilityIssue(
                severity="medium",
                category="contrast",
                element="CSS",
                description="Text colors defined without background colors",
                recommendation="Ensure sufficient color contrast ratios",
                file_path=file_path
            ))
        
        return issues
    
    def generate_accessibility_report(self, output_file: str = "accessibility_audit_report.json"):
        """Generate comprehensive accessibility audit report"""
        report = {
            "audit_info": {
                "timestamp": str(Path().stat().st_mtime),
                "wcag_version": "2.1 AA",
                "total_issues": len(self.issues),
                "critical_issues": len([i for i in self.issues if i.severity == "critical"]),
                "high_issues": len([i for i in self.issues if i.severity == "high"]),
                "medium_issues": len([i for i in self.issues if i.severity == "medium"]),
                "low_issues": len([i for i in self.issues if i.severity == "low"])
            },
            "issues_by_category": {},
            "issues_by_severity": {},
            "recommendations": [],
            "compliance_score": 0
        }
        
        # Group issues by category
        for issue in self.issues:
            if issue.category not in report["issues_by_category"]:
                report["issues_by_category"][issue.category] = []
            report["issues_by_category"][issue.category].append({
                "severity": issue.severity,
                "element": issue.element,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "line_number": issue.line_number,
                "file_path": issue.file_path
            })
        
        # Group issues by severity
        for issue in self.issues:
            if issue.severity not in report["issues_by_severity"]:
                report["issues_by_severity"][issue.severity] = []
            report["issues_by_severity"][issue.severity].append({
                "category": issue.category,
                "element": issue.element,
                "description": issue.description,
                "recommendation": issue.recommendation,
                "line_number": issue.line_number,
                "file_path": issue.file_path
            })
        
        # Calculate compliance score
        total_issues = len(self.issues)
        if total_issues > 0:
            critical_weight = 0.4
            high_weight = 0.3
            medium_weight = 0.2
            low_weight = 0.1
            
            critical_count = len([i for i in self.issues if i.severity == "critical"])
            high_count = len([i for i in self.issues if i.severity == "high"])
            medium_count = len([i for i in self.issues if i.severity == "medium"])
            low_count = len([i for i in self.issues if i.severity == "low"])
            
            weighted_score = (
                (critical_count * critical_weight) +
                (high_count * high_weight) +
                (medium_count * medium_weight) +
                (low_count * low_weight)
            )
            
            report["compliance_score"] = max(0, 100 - (weighted_score * 100))
        
        # Generate recommendations
        if report["issues_by_severity"].get("critical"):
            report["recommendations"].append("Fix all critical issues immediately for basic accessibility")
        
        if report["issues_by_severity"].get("high"):
            report["recommendations"].append("Address high-priority issues for WCAG AA compliance")
        
        if "alt_text" in report["issues_by_category"]:
            report["recommendations"].append("Add descriptive alt text to all images")
        
        if "form_labels" in report["issues_by_category"]:
            report["recommendations"].append("Ensure all form inputs have proper labels")
        
        if "keyboard" in report["issues_by_category"]:
            report["recommendations"].append("Implement proper keyboard navigation")
        
        # Save report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Accessibility report saved to {output_file}")
        return report
    
    def create_accessibility_enhancement_script(self, output_file: str = "accessibility_enhancements.js"):
        """Create JavaScript file with accessibility enhancements"""
        script_content = f"""
// Mingus Financial Services - Accessibility Enhancements
// WCAG 2.1 AA Compliance Implementation

(function() {{
    'use strict';
    
    // Accessibility configuration
    const ACCESSIBILITY_CONFIG = {{
        keyboardShortcuts: {json.dumps(self.keyboard_shortcuts, indent=8)},
        focusIndicatorClass: 'accessibility-focus',
        skipLinkId: 'skip-to-main',
        liveRegionId: 'accessibility-live-region',
        highContrastClass: 'high-contrast-mode',
        reducedMotionClass: 'reduced-motion'
    }};
    
    // Initialize accessibility features
    function initAccessibility() {{
        setupKeyboardNavigation();
        setupFocusIndicators();
        setupSkipLinks();
        setupLiveRegions();
        setupHighContrastToggle();
        setupReducedMotionSupport();
        setupScreenReaderAnnouncements();
        setupFormAccessibility();
        setupTableAccessibility();
        setupImageAccessibility();
    }}
    
    // Keyboard navigation setup
    function setupKeyboardNavigation() {{
        // Add keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            // Navigation shortcuts
            if (e.altKey) {{
                switch(e.key.toLowerCase()) {{
                    case 'd':
                        e.preventDefault();
                        navigateToDashboard();
                        break;
                    case 'a':
                        e.preventDefault();
                        navigateToAssessments();
                        break;
                    case 'l':
                        e.preventDefault();
                        navigateToAnalytics();
                        break;
                    case 'p':
                        e.preventDefault();
                        navigateToProfile();
                        break;
                }}
            }}
            
            // Financial tools shortcuts
            if (e.altKey) {{
                switch(e.key.toLowerCase()) {{
                    case 'i':
                        e.preventDefault();
                        openIncomeComparison();
                        break;
                    case 't':
                        e.preventDefault();
                        openTaxCalculator();
                        break;
                    case 'b':
                        e.preventDefault();
                        openBudgetPlanner();
                        break;
                    case 'v':
                        e.preventDefault();
                        openInvestmentAnalyzer();
                        break;
                }}
            }}
        }});
        
        // Ensure all interactive elements are keyboard accessible
        const interactiveElements = document.querySelectorAll('a, button, input, textarea, select, [tabindex]');
        interactiveElements.forEach(element => {{
            if (!element.hasAttribute('tabindex')) {{
                element.setAttribute('tabindex', '0');
            }}
        }});
    }}
    
    // Focus indicators
    function setupFocusIndicators() {{
        const style = document.createElement('style');
        style.textContent = `
            .accessibility-focus {
                outline: 3px solid #00d4aa !important;
                outline-offset: 2px !important;
                border-radius: 4px !important;
            }
            
            .accessibility-focus:focus {
                outline: 3px solid #00d4aa !important;
                outline-offset: 2px !important;
            }
        `;
        document.head.appendChild(style);
        
        // Add focus indicators to all focusable elements
        document.addEventListener('focusin', function(e) {{
            e.target.classList.add('accessibility-focus');
        }});
        
        document.addEventListener('focusout', function(e) {{
            e.target.classList.remove('accessibility-focus');
        }});
    }}
    
    // Skip links
    function setupSkipLinks() {{
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.id = 'skip-to-main';
        skipLink.className = 'skip-link';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: #00d4aa;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 10000;
            transition: top 0.3s;
        `;
        
        skipLink.addEventListener('focus', function() {{
            this.style.top = '6px';
        }});
        
        skipLink.addEventListener('blur', function() {{
            this.style.top = '-40px';
        }});
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }}
    
    // Live regions for screen reader announcements
    function setupLiveRegions() {{
        const liveRegion = document.createElement('div');
        liveRegion.id = 'accessibility-live-region';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(liveRegion);
    }}
    
    // High contrast mode toggle
    function setupHighContrastToggle() {{
        const toggle = document.createElement('button');
        toggle.textContent = 'Toggle High Contrast';
        toggle.setAttribute('aria-label', 'Toggle high contrast mode');
        toggle.className = 'accessibility-toggle';
        toggle.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
            padding: 8px 12px;
            background: #333;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        `;
        
        toggle.addEventListener('click', function() {{
            document.body.classList.toggle('high-contrast-mode');
            announceToScreenReader(
                document.body.classList.contains('high-contrast-mode') 
                    ? 'High contrast mode enabled' 
                    : 'High contrast mode disabled'
            );
        }});
        
        document.body.appendChild(toggle);
    }}
    
    // Reduced motion support
    function setupReducedMotionSupport() {{
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
            document.body.classList.add('reduced-motion');
        }}
        
        // Add CSS for reduced motion
        const style = document.createElement('style');
        style.textContent = `
            .reduced-motion * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        `;
        document.head.appendChild(style);
    }}
    
    // Screen reader announcements
    function setupScreenReaderAnnouncements() {{
        window.announceToScreenReader = function(message) {{
            const liveRegion = document.getElementById('accessibility-live-region');
            if (liveRegion) {{
                liveRegion.textContent = message;
                setTimeout(() => {{
                    liveRegion.textContent = '';
                }}, 1000);
            }}
        }};
    }}
    
    // Form accessibility
    function setupFormAccessibility() {{
        // Add ARIA attributes to form inputs
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {{
            if (!input.hasAttribute('aria-label') && !input.hasAttribute('aria-labelledby')) {{
                const label = input.closest('label') || document.querySelector(`label[for="${{input.id}}"]`);
                if (label) {{
                    input.setAttribute('aria-labelledby', label.id || 'label-' + Math.random().toString(36).substr(2, 9));
                }}
            }}
            
            // Add error handling
            if (input.hasAttribute('aria-invalid')) {{
                input.addEventListener('blur', function() {{
                    if (this.value && this.checkValidity()) {{
                        this.setAttribute('aria-invalid', 'false');
                    }}
                }});
            }}
        }});
    }}
    
    // Table accessibility
    function setupTableAccessibility() {{
        const tables = document.querySelectorAll('table');
        tables.forEach(table => {{
            if (!table.hasAttribute('role')) {{
                table.setAttribute('role', 'table');
            }}
            
            const headers = table.querySelectorAll('th');
            headers.forEach(header => {{
                if (!header.hasAttribute('scope')) {{
                    header.setAttribute('scope', 'col');
                }}
            }});
        }});
    }}
    
    // Image accessibility
    function setupImageAccessibility() {{
        const images = document.querySelectorAll('img');
        images.forEach(img => {{
            if (!img.hasAttribute('alt')) {{
                // Generate alt text based on context
                const context = img.closest('[data-context]')?.getAttribute('data-context') || 'image';
                img.setAttribute('alt', `${{context}} image`);
            }}
            
            // Add loading optimization
            if (!img.hasAttribute('loading')) {{
                img.setAttribute('loading', 'lazy');
            }}
        }});
    }}
    
    // Navigation functions
    function navigateToDashboard() {{
        announceToScreenReader('Navigating to dashboard');
        // Implementation for dashboard navigation
    }}
    
    function navigateToAssessments() {{
        announceToScreenReader('Navigating to assessments');
        // Implementation for assessments navigation
    }}
    
    function navigateToAnalytics() {{
        announceToScreenReader('Navigating to analytics');
        // Implementation for analytics navigation
    }}
    
    function navigateToProfile() {{
        announceToScreenReader('Navigating to profile');
        // Implementation for profile navigation
    }}
    
    // Financial tools functions
    function openIncomeComparison() {{
        announceToScreenReader('Opening income comparison tool');
        // Implementation for income comparison
    }}
    
    function openTaxCalculator() {{
        announceToScreenReader('Opening tax calculator');
        // Implementation for tax calculator
    }}
    
    function openBudgetPlanner() {{
        announceToScreenReader('Opening budget planner');
        // Implementation for budget planner
    }}
    
    function openInvestmentAnalyzer() {{
        announceToScreenReader('Opening investment analyzer');
        // Implementation for investment analyzer
    }}
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', initAccessibility);
    }} else {{
        initAccessibility();
    }}
    
    // Export for global access
    window.MingusAccessibility = {{
        init: initAccessibility,
        announce: announceToScreenReader,
        config: ACCESSIBILITY_CONFIG
    }};
    
}})();
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"Accessibility enhancement script saved to {output_file}")
        return output_file
    
    def run_full_audit(self, target_directories: List[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive accessibility audit on the codebase
        
        Args:
            target_directories: List of directories to audit (defaults to common frontend dirs)
            
        Returns:
            Audit results and recommendations
        """
        if target_directories is None:
            target_directories = [
                "frontend",
                "src",
                "components", 
                "templates",
                "static"
            ]
        
        logger.info("Starting comprehensive accessibility audit...")
        
        # Find all relevant files
        file_extensions = ['.html', '.htm', '.tsx', '.jsx', '.js', '.css', '.scss']
        files_to_audit = []
        
        for directory in target_directories:
            dir_path = self.base_path / directory
            if dir_path.exists():
                for ext in file_extensions:
                    files_to_audit.extend(dir_path.rglob(f"*{ext}"))
        
        logger.info(f"Found {len(files_to_audit)} files to audit")
        
        # Audit each file
        for file_path in files_to_audit:
            logger.info(f"Auditing {file_path}")
            issues = self.audit_file_accessibility(str(file_path))
            self.issues.extend(issues)
        
        # Generate reports
        report = self.generate_accessibility_report()
        self.create_accessibility_enhancement_script()
        
        logger.info(f"Audit complete. Found {len(self.issues)} accessibility issues.")
        logger.info(f"Compliance score: {{report['compliance_score']:.1f}}%")
        
        return report

def main():
    """Main function to run accessibility audit"""
    manager = AccessibilityManager()
    
    print("Mingus Financial Services - WCAG 2.1 AA Accessibility Audit")
    print("=" * 60)
    
    # Run full audit
    report = manager.run_full_audit()
    
    # Print summary
    print(f"\\nAudit Summary:")
    print(f"Total Issues: {{report['audit_info']['total_issues']}}")
    print(f"Critical: {{report['audit_info']['critical_issues']}}")
    print(f"High: {{report['audit_info']['high_issues']}}")
    print(f"Medium: {{report['audit_info']['medium_issues']}}")
    print(f"Low: {{report['audit_info']['low_issues']}}")
    print(f"Compliance Score: {{report['compliance_score']:.1f}}%")
    
    if report['recommendations']:
        print(f"\\nKey Recommendations:")
        for rec in report['recommendations']:
            print(f"• {{rec}}")
    
    print(f"\\nDetailed report saved to: accessibility_audit_report.json")
    print(f"Enhancement script saved to: accessibility_enhancements.js")

if __name__ == "__main__":
    main()
