#!/usr/bin/env python3
"""
CSS Media Query Validator
Validates CSS media queries for responsive design best practices
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MediaQuery:
    """Represents a CSS media query"""
    query: str
    line_number: int
    file_path: str
    min_width: Optional[int]
    max_width: Optional[int]
    orientation: Optional[str]
    device_type: Optional[str]
    is_valid: bool
    issues: List[str]
    recommendations: List[str]

@dataclass
class CSSFile:
    """Represents a CSS file with its media queries"""
    file_path: str
    media_queries: List[MediaQuery]
    total_queries: int
    valid_queries: int
    issues_count: int

@dataclass
class ValidationResult:
    """Results from CSS media query validation"""
    files_analyzed: int
    total_media_queries: int
    valid_queries: int
    invalid_queries: int
    common_issues: List[Dict[str, Any]]
    breakpoint_analysis: Dict[str, Any]
    recommendations: List[str]
    overall_score: float

class CSSMediaQueryValidator:
    """CSS Media Query Validator for responsive design"""
    
    def __init__(self):
        # Standard breakpoints for responsive design
        self.standard_breakpoints = {
            'mobile': 320,
            'mobile_large': 375,
            'mobile_xl': 428,
            'tablet': 768,
            'tablet_large': 1024,
            'desktop': 1440,
            'desktop_large': 1920
        }
        
        # Common media query patterns
        self.media_query_patterns = {
            'width': r'(min|max)-width:\s*(\d+(?:\.\d+)?)(px|em|rem|%)',
            'height': r'(min|max)-height:\s*(\d+(?:\.\d+)?)(px|em|rem|%)',
            'orientation': r'orientation:\s*(portrait|landscape)',
            'device_type': r'(screen|print|speech|all)',
            'aspect_ratio': r'aspect-ratio:\s*(\d+)/(\d+)',
            'resolution': r'resolution:\s*(\d+(?:\.\d+)?)(dpi|dpcm|dppx)'
        }
        
        # Best practices for media queries
        self.best_practices = {
            'mobile_first': 'Use min-width media queries for mobile-first approach',
            'logical_breakpoints': 'Use logical breakpoints that match content needs',
            'consistent_units': 'Use consistent units (px, em, rem) throughout',
            'no_overlap': 'Avoid overlapping breakpoints that can cause conflicts',
            'semantic_names': 'Use semantic names for breakpoints when possible'
        }
    
    def validate_css_file(self, file_path: str) -> CSSFile:
        """Validate a single CSS file"""
        logger.info(f"Validating CSS file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            media_queries = self._extract_media_queries(content, file_path)
            
            # Validate each media query
            for query in media_queries:
                self._validate_single_media_query(query)
            
            valid_count = sum(1 for q in media_queries if q.is_valid)
            issues_count = sum(len(q.issues) for q in media_queries)
            
            return CSSFile(
                file_path=file_path,
                media_queries=media_queries,
                total_queries=len(media_queries),
                valid_queries=valid_count,
                issues_count=issues_count
            )
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return CSSFile(
                file_path=file_path,
                media_queries=[],
                total_queries=0,
                valid_queries=0,
                issues_count=1
            )
    
    def _extract_media_queries(self, content: str, file_path: str) -> List[MediaQuery]:
        """Extract media queries from CSS content"""
        media_queries = []
        
        # Find all @media rules
        media_rule_pattern = r'@media\s+([^{]+)\s*\{'
        matches = re.finditer(media_rule_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            query_text = match.group(1).strip()
            line_number = content[:match.start()].count('\n') + 1
            
            media_query = MediaQuery(
                query=query_text,
                line_number=line_number,
                file_path=file_path,
                min_width=None,
                max_width=None,
                orientation=None,
                device_type=None,
                is_valid=True,
                issues=[],
                recommendations=[]
            )
            
            media_queries.append(media_query)
        
        return media_queries
    
    def _validate_single_media_query(self, media_query: MediaQuery) -> None:
        """Validate a single media query"""
        query = media_query.query
        
        # Parse width conditions
        width_matches = re.findall(self.media_query_patterns['width'], query)
        for match in width_matches:
            condition, value, unit = match
            try:
                numeric_value = float(value)
                if condition == 'min-width':
                    media_query.min_width = int(numeric_value) if unit == 'px' else numeric_value
                elif condition == 'max-width':
                    media_query.max_width = int(numeric_value) if unit == 'px' else numeric_value
            except ValueError:
                media_query.issues.append(f"Invalid {condition} value: {value}{unit}")
                media_query.is_valid = False
        
        # Parse orientation
        orientation_match = re.search(self.media_query_patterns['orientation'], query)
        if orientation_match:
            media_query.orientation = orientation_match.group(1)
        
        # Parse device type
        device_match = re.search(self.media_query_patterns['device_type'], query)
        if device_match:
            media_query.device_type = device_match.group(1)
        
        # Validate breakpoint logic
        self._validate_breakpoint_logic(media_query)
        
        # Check for best practices
        self._check_best_practices(media_query)
    
    def _validate_breakpoint_logic(self, media_query: MediaQuery) -> None:
        """Validate breakpoint logic and consistency"""
        # Check for conflicting min/max width
        if media_query.min_width is not None and media_query.max_width is not None:
            if media_query.min_width >= media_query.max_width:
                media_query.issues.append(
                    f"min-width ({media_query.min_width}) cannot be greater than or equal to max-width ({media_query.max_width})"
                )
                media_query.is_valid = False
        
        # Check for standard breakpoint usage
        if media_query.min_width is not None:
            self._check_breakpoint_consistency(media_query, media_query.min_width, 'min-width')
        
        if media_query.max_width is not None:
            self._check_breakpoint_consistency(media_query, media_query.max_width, 'max-width')
    
    def _check_breakpoint_consistency(self, media_query: MediaQuery, value: float, condition_type: str) -> None:
        """Check if breakpoint value follows consistent patterns"""
        # Check if value is close to standard breakpoints
        closest_standard = min(self.standard_breakpoints.values(), 
                             key=lambda x: abs(x - value))
        
        if abs(value - closest_standard) > 20:  # Allow 20px tolerance
            media_query.recommendations.append(
                f"Consider using standard breakpoint {closest_standard}px instead of {value}px for {condition_type}"
            )
    
    def _check_best_practices(self, media_query: MediaQuery) -> None:
        """Check media query against best practices"""
        query = media_query.query.lower()
        
        # Check for mobile-first approach
        if 'min-width' in query and 'max-width' not in query:
            media_query.recommendations.append(self.best_practices['mobile_first'])
        
        # Check for logical breakpoints
        if media_query.min_width is not None and media_query.max_width is not None:
            if media_query.max_width - media_query.min_width < 50:
                media_query.recommendations.append(
                    "Breakpoint range is very narrow, consider if this is necessary"
                )
        
        # Check for consistent units
        units = re.findall(r'\d+(px|em|rem|%)', media_query.query)
        if len(set(units)) > 1:
            media_query.recommendations.append(
                "Consider using consistent units throughout media queries"
            )
    
    def validate_directory(self, directory_path: str, file_pattern: str = "*.css") -> ValidationResult:
        """Validate all CSS files in a directory"""
        logger.info(f"Validating CSS files in directory: {directory_path}")
        
        css_files = []
        directory = Path(directory_path)
        
        # Find all CSS files
        for css_file in directory.rglob(file_pattern):
            if css_file.is_file():
                css_files.append(css_file)
        
        if not css_files:
            logger.warning(f"No CSS files found in {directory_path}")
            return ValidationResult(
                files_analyzed=0,
                total_media_queries=0,
                valid_queries=0,
                invalid_queries=0,
                common_issues=[],
                breakpoint_analysis={},
                recommendations=[],
                overall_score=0.0
            )
        
        # Validate each CSS file
        file_results = []
        for css_file in css_files:
            file_result = self.validate_css_file(str(css_file))
            file_results.append(file_result)
        
        # Generate comprehensive validation result
        return self._generate_validation_result(file_results)
    
    def _generate_validation_result(self, file_results: List[CSSFile]) -> ValidationResult:
        """Generate comprehensive validation result from file results"""
        total_queries = sum(f.total_queries for f in file_results)
        valid_queries = sum(f.valid_queries for f in file_results)
        invalid_queries = total_queries - valid_queries
        
        # Calculate overall score
        overall_score = (valid_queries / total_queries * 100) if total_queries > 0 else 0
        
        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []
        all_breakpoints = []
        
        for file_result in file_results:
            for query in file_result.media_queries:
                all_issues.extend(query.issues)
                all_recommendations.extend(query.recommendations)
                
                if query.min_width is not None:
                    all_breakpoints.append(('min-width', query.min_width))
                if query.max_width is not None:
                    all_breakpoints.append(('max-width', query.max_width))
        
        # Count issue frequency
        from collections import Counter
        issue_counts = Counter(all_issues)
        recommendation_counts = Counter(all_recommendations)
        
        common_issues = [{'issue': issue, 'count': count} for issue, count in issue_counts.most_common(10)]
        
        # Analyze breakpoints
        breakpoint_analysis = self._analyze_breakpoints(all_breakpoints)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            file_results, issue_counts, breakpoint_analysis
        )
        
        return ValidationResult(
            files_analyzed=len(file_results),
            total_media_queries=total_queries,
            valid_queries=valid_queries,
            invalid_queries=invalid_queries,
            common_issues=common_issues,
            breakpoint_analysis=breakpoint_analysis,
            recommendations=recommendations,
            overall_score=round(overall_score, 2)
        )
    
    def _analyze_breakpoints(self, breakpoints: List[Tuple[str, float]]) -> Dict[str, Any]:
        """Analyze breakpoint usage patterns"""
        analysis = {
            'total_breakpoints': len(breakpoints),
            'min_width_breakpoints': [],
            'max_width_breakpoints': [],
            'breakpoint_distribution': {},
            'gaps': [],
            'overlaps': []
        }
        
        min_widths = [bp[1] for bp in breakpoints if bp[0] == 'min-width']
        max_widths = [bp[1] for bp in breakpoints if bp[0] == 'max-width']
        
        analysis['min_width_breakpoints'] = sorted(min_widths)
        analysis['max_width_breakpoints'] = sorted(max_widths)
        
        # Analyze breakpoint distribution
        all_breakpoints = sorted(set(min_widths + max_widths))
        for i in range(len(all_breakpoints) - 1):
            gap = all_breakpoints[i + 1] - all_breakpoints[i]
            if gap > 100:  # Large gaps
                analysis['gaps'].append({
                    'from': all_breakpoints[i],
                    'to': all_breakpoints[i + 1],
                    'gap': gap
                })
        
        return analysis
    
    def _generate_recommendations(self, file_results: List[CSSFile], 
                                issue_counts: Counter, 
                                breakpoint_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Based on common issues
        if issue_counts:
            most_common_issue = issue_counts.most_common(1)[0][0]
            if 'min-width' in most_common_issue and 'max-width' in most_common_issue:
                recommendations.append("Review breakpoint logic to ensure min-width < max-width")
        
        # Based on breakpoint analysis
        if breakpoint_analysis['gaps']:
            recommendations.append("Consider adding breakpoints for large gaps in responsive design")
        
        # Based on file results
        files_with_issues = sum(1 for f in file_results if f.issues_count > 0)
        if files_with_issues > len(file_results) * 0.5:
            recommendations.append("Multiple files have validation issues - consider establishing CSS standards")
        
        # General best practices
        recommendations.extend([
            "Use mobile-first approach with min-width media queries",
            "Standardize breakpoint values across the project",
            "Test media queries across different devices and orientations"
        ])
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def generate_report(self, validation_result: ValidationResult, output_file: str = None) -> str:
        """Generate a detailed validation report"""
        report = []
        report.append("=" * 80)
        report.append("CSS MEDIA QUERY VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Files Analyzed: {validation_result.files_analyzed}")
        report.append(f"Total Media Queries: {validation_result.total_media_queries}")
        report.append(f"Valid Queries: {validation_result.valid_queries}")
        report.append(f"Invalid Queries: {validation_result.invalid_queries}")
        report.append(f"Overall Score: {validation_result.overall_score}/100")
        report.append("")
        
        # Breakpoint Analysis
        if validation_result.breakpoint_analysis:
            report.append("📱 BREAKPOINT ANALYSIS")
            report.append("-" * 40)
            bp_analysis = validation_result.breakpoint_analysis
            
            if bp_analysis['min_width_breakpoints']:
                report.append(f"Min-width breakpoints: {', '.join(map(str, bp_analysis['min_width_breakpoints']))}")
            
            if bp_analysis['max_width_breakpoints']:
                report.append(f"Max-width breakpoints: {', '.join(map(str, bp_analysis['max_width_breakpoints']))}")
            
            if bp_analysis['gaps']:
                report.append("Large gaps detected:")
                for gap in bp_analysis['gaps'][:3]:  # Show top 3 gaps
                    report.append(f"  • {gap['from']}px → {gap['to']}px (gap: {gap['gap']}px)")
            
            report.append("")
        
        # Common Issues
        if validation_result.common_issues:
            report.append("🚨 COMMON ISSUES")
            report.append("-" * 40)
            for issue in validation_result.common_issues[:5]:  # Show top 5 issues
                report.append(f"• {issue['issue']} (found {issue['count']} times)")
            report.append("")
        
        # Recommendations
        if validation_result.recommendations:
            report.append("💡 RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in validation_result.recommendations:
                report.append(f"• {rec}")
            report.append("")
        
        # Save report to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write('\n'.join(report))
            logger.info(f"Report saved to {output_file}")
        
        return '\n'.join(report)

def main():
    """Main function to run the CSS validator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSS Media Query Validator')
    parser.add_argument('path', help='Path to CSS file or directory to validate')
    parser.add_argument('--output', '-o', help='Output file for the report')
    parser.add_argument('--pattern', '-p', default='*.css', help='File pattern to match (default: *.css)')
    
    args = parser.parse_args()
    
    validator = CSSMediaQueryValidator()
    
    try:
        if os.path.isfile(args.path):
            # Validate single file
            file_result = validator.validate_css_file(args.path)
            validation_result = validator._generate_validation_result([file_result])
        elif os.path.isdir(args.path):
            # Validate directory
            validation_result = validator.validate_directory(args.path, args.pattern)
        else:
            print(f"Error: {args.path} is not a valid file or directory")
            sys.exit(1)
        
        # Generate and display report
        report = validator.generate_report(validation_result, args.output)
        print(report)
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
